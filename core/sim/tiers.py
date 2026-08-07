"""Phase 2 T5 — the three simulation tiers.

| Tier   | Method                                   | Answers                       |
|--------|------------------------------------------|-------------------------------|
| fast   | closed form, expected value x casts/sec  | "does A beat B, roughly, now" |
| medium | one deterministic timeline, averaged RNG | "is this rotation CASTABLE?"  |
| slow   | Monte Carlo, full RNG                    | variance, CIs, proc chains    |

**Medium is the one worth having.** Fast sim assumes you cast an ability every
N seconds because its cooldown allows it, and cannot see that you are GCD-locked
or out of mana — an error class it is structurally blind to, and that slow sim
only reveals as noise. Medium answers castability directly.

All three consume the SAME `ResolvedAbility.expected_cast`, so they can differ
in how rigorously they evaluate over time but never in what an ability does
(PHASE_2 T3). Every `SimResult` carries `warnings`, and anything computed from
a NULL, conflicted or attributed field says so there.
"""
import random
from dataclasses import dataclass, field

from .ability_model import resolve_ability, AbilityResolutionError
from .apl import APL, MAX_COMBO_POINTS, entry_ready
from .content import ContentProfile, Metric, PRIMARY_METRIC_BY_ROLE, SimResult
from .pets import detect_summons, pet_gap_warning
from .swings import (
    swing_events, expected_swing, seal_procs, righteous_vengeance_damage,
    SEAL_PROC_PER_MELEE_EVENT, SEAL_PROC_RATE_EVIDENCE,
    RIGHTEOUS_VENGEANCE_SPELL_ID, RIGHTEOUS_VENGEANCE_FRACTION,
    RIGHTEOUS_VENGEANCE_CARD_SPELL_IDS,
)

# retail_hypothesis: 1.5s base GCD, floored at 1.0s, reduced by spell haste for
# spells only. Not yet validated on Ascension — a calibration candidate.
#
# 🛑 3f F2 — `PROGRESS.md` described this as "a named retail_hypothesis WITH A
# WARNING, like BASE_GCD", and BASE_GCD emitted no warning at all. Rather than
# delete the sentence, the warning now exists: it is appended once per sim run
# by both tiers. It is not per-ability on purpose — every on-GCD ability in
# every build depends on it, so a per-ability emission would be pure noise
# while saying nothing extra.
BASE_GCD = 1.5
MIN_GCD = 1.0

BASE_GCD_UNVALIDATED = (
    f"BASE_GCD = {BASE_GCD:g}s (floor {MIN_GCD:g}s) is a retail_hypothesis, NOT "
    "measured on Ascension. It sets the cast count of every on-GCD ability, so "
    "it scales this entire result linearly; a server running a different base "
    "GCD would move every number below by the same ratio. No endpoint or DBC "
    "field we hold states it — settling it needs a log with dense back-to-back "
    "instants and their timestamps.")

# retail_hypothesis (3e B4): one combo point per non-finisher damaging cast, and
# a finisher spends what its APL entry is gated on.
#
# 🛑 THIS IS A HYPOTHESIS BECAUSE THE DATA IS ABSENT, and the absence is the
# finding. `SPELL_EFFECT_ADD_COMBO_POINTS` is effect type 40, and
# `spell_effect_values` holds **ZERO rows** of it — nothing in the extract says
# which abilities generate combo points or how many. So "which buttons are
# builders" cannot be derived today, only assumed, and it is assumed HERE, once,
# under a name, with a warning emitted by any sim that relies on it. Same
# treatment as BASE_GCD above. Open question:
# `combo_point_generation_absent_from_extract`.
#
# 🛑 3f F2 — THAT SENTENCE WAS FALSE WHEN IT WAS WRITTEN, in the tier the gate
# runs on. The warning sat inside `if window < 1.0:` — the EXECUTE-WINDOW
# branch — and `_health_gate` only matches `target_health_pct_below`, which
# `apl_gen` never emits (ENGINE_BUGS E2 says so in its own entry). So for every
# auto-generated APL, i.e. every gate run and every fixture run, `window` was
# 1.0, the block never executed, and `fast_sim` scaled finisher cast counts by
# an unmeasured constant in silence while four documents stated otherwise. It
# is now emitted from `if cp > 0:` in fast_sim and from medium_sim, which
# applied the same hypothesis with no warning at all.
CP_PER_BUILDER_CAST = 1.0


def cp_hypothesis_warning(ability_name, cp, casts=None):
    """The disclosure for `CP_PER_BUILDER_CAST`, emitted wherever it is applied.

    `casts` is the CP-LIMITED count. The old text reported the count AFTER the
    execute-window multiply at `:375`, so on the rare path where it did fire it
    named a health-scaled number as the combo-point-limited one.

    Never called with `cp == 0`: the old form printed *"held to 0 combo
    points"*, which describes an ability that is not a finisher and means
    nothing.
    """
    at = f" and cast {casts:.1f}x" if casts is not None else ""
    return (f"{ability_name}: held to {cp:g} combo points{at}, assuming "
            f"{CP_PER_BUILDER_CAST:g} CP per builder cast — a "
            "retail_hypothesis, NOT measured. SPELL_EFFECT_ADD_COMBO_POINTS "
            "(effect 40) has zero rows in the extract, so which abilities "
            "generate combo points, and how many, is not derivable from our "
            "data at all. This scales the finisher's cast count directly.")

# 3e B5 (ENGINE_BUGS E2) — target health DECAYS linearly from 100% to 0% over the
# fight, so an execute window is reachable at all. It was pinned at 100.0, which
# made `target_health_pct_below` permanently false and every execute-range
# ability dead code — while `apl_gen` emitted no health condition either, so the
# same abilities were cast as if ALWAYS available. Unmodelled in both directions
# at once, and silent about it.
#
# 🛑 WHICH ABILITIES ARE EXECUTE-GATED IS NOT DERIVABLE FROM OUR DATA. In 3.3.5
# that gate is `TargetAuraState = AURA_STATE_HEALTHLESS_20_PERCENT`, and
# `spell_dbc_raw` does not carry `TargetAuraState` at all — the extract exports
# `attributes` / `attributes_ex` and no aura-state column. So the decay below
# makes the MECHANISM work; it cannot make the sim know that Hammer of Wrath
# needs a dying target. Any sim that runs emits the gap by name rather than
# leaving an execute ability quietly over-credited. Open question:
# `execute_gating_absent_from_extract`.
EXECUTE_GATING_UNAVAILABLE = (
    "EXECUTE WINDOWS ARE NOT MODELLED PER ABILITY: 3.3.5 encodes an execute gate "
    "as TargetAuraState (AURA_STATE_HEALTHLESS_20_PERCENT) and the DBC extract "
    "carries no aura-state column, so the sim cannot tell which abilities "
    "require a low-health target. Target health itself DOES decay here, so a "
    "hand-authored target_health_pct_below condition works — but an "
    "execute-gated ability with no such condition is modelled as always "
    "available and is OVER-CREDITED")


def _gcd_for(ability, char_state):
    """GCD an ability consumes. `gcd_type='none'` means off-GCD entirely."""
    gt = ability.fields.get("gcd_type")
    if gt in ("none", "off"):
        return 0.0
    haste = (char_state.spell_haste_pct if ability.school != "Physical"
             else char_state.melee_haste_pct)
    gcd = BASE_GCD / (1.0 + max(0.0, haste) / 100.0)
    gcd *= 1.0 + char_state.gcd_modifier_pct / 100.0
    return max(MIN_GCD, gcd)


def _cast_time(ability, char_state):
    ct = ability.fields.get("cast_time_seconds") or 0.0
    if ct <= 0:
        return 0.0
    haste = (char_state.spell_haste_pct if ability.school != "Physical"
             else char_state.melee_haste_pct)
    return ct / (1.0 + max(0.0, haste) / 100.0)


def _resolve_all(conn, spell_ids, level, warnings):
    """Resolve every ability once. A refusal is reported, never swallowed —
    an ability silently dropped from a rotation changes the answer."""
    out = {}
    for sid in spell_ids:
        try:
            out[sid] = resolve_ability(conn, sid, level=level)
        except AbilityResolutionError as e:
            warnings.append(
                f"ability {sid} EXCLUDED from the sim — the resolver refused: "
                f"{e}. The result below is a build missing this ability, not "
                "the build you asked about")
    return out


def _effective_time(content: ContentProfile):
    """Seconds actually available to act. movement_pct is time spent not
    casting; treating it as free is the commonest way a sim overstates DPS."""
    return content.fight_duration * (1.0 - max(0.0, min(1.0, content.movement_pct)))


def _decay_target_health(st):
    """Target health falls linearly to 0 across the fight (3e B5).

    A boss fight ENDS when the target dies, so 100% -> 0% over
    `fight_duration` is the shape, not an assumption about pacing. It is still
    a shape: real damage is lumpy and an execute window arrives a little early
    or late. What matters here is that the window EXISTS, which it did not
    before — `target_health_pct` was pinned at 100.0 forever.
    """
    if st.fight_duration > 0:
        st.target_health_pct = max(
            0.0, 100.0 * (1.0 - st.now / st.fight_duration))


def _routes_as_debuff(ability):
    """Does `medium_sim` file this ability's duration on the TARGET? 🆕 `3g` G5.

    🛑 **A seam, like `_decay_health` above, and for the same reason.** E9 is a
    THIRD DoT discriminator: `apl_gen` and `_useful_cast_interval` both call
    `_is_pure_periodic`, while `medium_sim`'s cast path tested `dur and
    tick_interval_seconds` INLINE — and `check_sim_engine.py` tested E9 by
    **re-implementing that inline test in the check**, against a hand-built fake
    whose `tick_interval_seconds` is `None`, so the comparison was against the
    literal constant `False`. It could only ever go green on a REGRESSION in
    `_is_pure_periodic`, which is exactly the drift `F3`'s own `_filler_ids`
    repair condemns.

    Extracting it changes nothing today — this is byte-equivalent to the inline
    test — but it gives the check something real to import, and it gives E9 a
    green path: **the fix is to make this return `_is_pure_periodic(ability)`**,
    so all three layers share one discriminator.

    ⚠ Why that is not done here: it is a behaviour change that moves cast
    counts, and `3g` reports one cause per gate move. It belongs in the commit
    that owns its pair.

    The disagreement is real and reachable: an ability with a periodic aura at
    `EffectAmplitude 0` has a duration and no tick interval, so
    `_is_pure_periodic` calls it a DoT (and `apl_gen` files it in the MAINTAINED
    tier at the top of the APL, gated on `debuff_remaining_below`) while this
    routes it to `st.buffs` — where `debuff_remaining()` returns 0.0 forever,
    `0.0 < 1.5` is always true, and the entry wins EVERY priority scan. That is
    the Seal of Command 47-of-47-GCDs failure re-created at the top of the list.
    """
    return bool(ability.fields.get("tick_interval_seconds"))


def _decay_health(st):
    """Advance every health track the timeline models. 🆕 `3g` G5.

    🛑 **This exists so E11 has a GREEN PATH, and it is deliberately a seam
    rather than a fix.** `check_sim_engine.py` used to call
    `_decay_target_health(st)` and then assert `st.self_health_pct < 100.0` —
    but that function touches only `target_health_pct` (the string
    `self_health` does not appear in it), so **no correct fix could ever turn
    that assertion green.** It was a permanent alarm, closable only by a lie.

    Today this decays the target only, so the check is still red and E11 is
    still open — nothing about the sim's behaviour changes by introducing it.
    **The fix is to decay `self_health_pct` here**, next to its sibling, and
    that single change turns the check green. `self_health_pct` is declared on
    `TimelineState` and READ by `apl.py`'s `health_pct_below` branch while being
    written nowhere in the tree, so `apl_gen`'s heals under a
    `self_sustain_required` preset can never fire in `medium_sim` while
    `fast_sim` casts them at full rate.

    ⚠ What the fix must NOT be: a plain mirror of the target's linear decay.
    The player is being healed as well as damaged, and a monotonic 100 -> 0 on
    the player would make every self-sustain heal fire in the last N% of the
    fight and never before, which is a different wrong answer. That is why this
    is left as a seam and not guessed at — see ENGINE_BUGS E11.
    """
    _decay_target_health(st)


def _cp_gate(apl, spell_id):
    """Combo points this entry is HELD TO by its own APL gate, else 0.

    3e B4 — the sim reads the rotation's own stated intent rather than
    re-deriving "is this a finisher", so the gate and the damage cannot disagree
    about how many combo points were spent. `apl_gen` holds finishers to
    MAX_COMBO_POINTS; a hand-authored APL can say something else and this
    follows it.
    """
    if not apl:
        return 0
    for e in apl.entries:
        if e.spell_id != spell_id:
            continue
        for c in (e.conditions or []):
            if c.get("type") == "combo_points_at_least":
                return int(c.get("value") or 0)
    return 0


def _health_gate(apl, spell_id):
    """Fraction of the fight an entry's target-health gate leaves it available.

    Under linear health decay an ability gated at "target below X%" is castable
    for the last X% of the fight, so `X/100` is exactly its share. Returns 1.0
    when the entry carries no health gate. 3e B5 — fast_sim has no timeline, so
    this is how a window enters a closed-form tier.
    """
    if not apl:
        return 1.0
    for e in apl.entries:
        if e.spell_id != spell_id:
            continue
        for c in (e.conditions or []):
            if c.get("type") == "target_health_pct_below":
                return max(0.0, min(1.0, float(c.get("value") or 0) / 100.0))
    return 1.0


def _is_pure_periodic(ability):
    """Is ALL of this ability's damage periodic?

    🚨 3e B3 — the distinction the first version of this got wrong, caught by
    the fixture rather than by reasoning. Corruption is a maintained debuff: all
    of its damage is ticks, so re-casting it early gains nothing. **Fireball is
    not** — it is a direct nuke that happens to leave a 4s DoT rider, and
    bounding it to one cast per 4s models a Fire mage as casting Fireball 10
    times a minute. Treating "has a periodic component" as "is a DoT" misclassed
    it and the check caught it immediately (Fireball 10 casts, Living Bomb 6,
    Pyroblast 7 in one 68s fight).

    Read from `events()`, which already splits damage into `direct` / `periodic`
    per source spell — not from the name, and not from the presence of a tick
    interval alone.
    """
    try:
        evs = ability.events()
    except Exception:                                # noqa: BLE001
        return False
    return bool(evs) and all(e.kind == "periodic" for e in evs)


def _useful_cast_interval(ability):
    """Seconds between USEFUL casts, read from the ability's own fields.

    Returns `(interval, reason)`; `interval <= 0` means nothing bounds it and it
    is a genuine spam button that may absorb whatever GCDs are left.

    🚨 3e B1 — THE DURATION TERM IS THE POINT, and leaving it out was a real
    over-count. `expected_cast` scores a periodic event as
    `duration / tick_interval` ticks **for one cast** — one Corruption cast is
    all 6 of its ticks. So a DoT treated as an unbounded filler is re-applied
    every GCD and **re-scores its entire duration each time**, which is the
    "DoTs are re-cast every GCD" defect the `3c` audit predicted. It reads clean
    on today's fixtures only because those DoTs never get any budget at all
    (ENGINE_BUGS E5) — remove that starvation without this bound and the sim
    would inflate every DoT by roughly `duration / gcd`.

    A cooldown and a duration can both apply; the binding one is the LONGER.
    Re-casting a 6s-cooldown DoT that runs for 18s refreshes it, it does not
    stack, so the useful rate is one per 18s.

    ⚠ Nothing here is invented — both numbers come from the resolved ability. An
    ability whose duration is unknown gets no duration bound, exactly as
    `expected_cast` refuses an unknown pulse count rather than defaulting it.
    """
    cd = ability.fields.get("cooldown_seconds") or 0.0
    dur = ability.fields.get("duration_seconds") or 0.0
    periodic = bool(ability.fields.get("tick_interval_seconds"))
    if periodic and dur > 0 and _is_pure_periodic(ability):
        if cd > 0:
            return (max(cd, dur),
                    f"cooldown {cd:g}s vs {dur:g}s periodic duration — the "
                    f"longer binds, a refresh does not stack")
        return dur, f"{dur:g}s periodic duration (one cast scores every tick)"
    if cd > 0:
        return cd, f"{cd:g}s cooldown"
    return 0.0, "unbounded — a spam filler"


def _mixed_damage_warning(ability):
    """A spell with BOTH a direct hit and a periodic rider is mis-modelled in
    both directions, and the sim says so rather than picking a side.

    Bound it by its DoT duration and a Fire mage casts Fireball once every 4s.
    Leave it unbounded and every cast re-scores the rider's whole duration, so
    the DoT part is over-counted by roughly `duration / gcd`. **Neither is
    right, and there is no field that resolves it** — what refreshing does to a
    partially-elapsed DoT is a server behaviour we have not measured on
    Ascension. Unbounded is the lesser error for the direct component, which
    dominates on these spells, so that is what runs; the residual is named here
    instead of being buried.
    """
    if _is_pure_periodic(ability):
        return None
    try:
        evs = ability.events()
    except Exception:                                # noqa: BLE001
        return None
    if not any(e.kind == "periodic" for e in evs):
        return None
    dur = ability.fields.get("duration_seconds") or 0.0
    if dur <= 0:
        return None
    return (f"{ability.name} ({ability.spell_id}) has BOTH a direct and a "
            f"periodic component over {dur:g}s. It is cast as a spammable "
            f"direct spell, so its periodic component's damage is RE-SCORED on "
            f"every cast and is over-counted — an upper bound on that "
            f"component, not a measurement. Refresh behaviour on a "
            f"partially-elapsed DoT is unmeasured on this server")


# --------------------------------------------------------------------- fast

def fast_sim(conn, build_spec, content: ContentProfile, char_state,
             apl: APL = None) -> SimResult:
    """Closed form: expected damage per cast x casts allowed per fight.

    Cast counts come from cooldowns and a GCD budget, in APL priority order.
    ⚠ It does NOT model resources at all, so it cannot see mana starvation —
    that is medium sim's job and the warning says so.
    """
    warnings = list(char_state.warnings)
    ids = apl.spell_ids() if apl else [c.spell_id for c in build_spec.abilities]
    abilities = _resolve_all(conn, ids, build_spec.character_level, warnings)

    available = _effective_time(content)
    gcd_budget = available
    per_ability, total, total_heal = {}, 0.0, 0.0

    # Allocation order is NOT priority order, and getting this wrong is easy to
    # miss: an ability is rate-limited by its cooldown or by the GCD budget, and
    # the cooldown ones must be allocated FIRST. Walking the priority list in
    # order let Lightbound Cleave — first in the list, no cooldown — consume the
    # entire budget and starve every cooldown behind it, reporting a rotation of
    # one button. Off-GCD entries are free and are handled separately.
    #
    # 3e B3 — the split is on whether the ability has ANY useful cast interval,
    # not on whether it has a cooldown. A DoT has no cooldown but is bounded by
    # its own duration, so under the old test it fell in with the unbounded
    # fillers and was allocated last — behind nine cooldown abilities on the
    # DoT-caster fixture, where the budget ran out first and it received
    # nothing. An interval-bounded ability cannot monopolise the budget (it
    # takes only `available / interval` casts), so allocating it first is safe
    # in exactly the way allocating a cooldown first is.
    #
    # 3e B4 — CP-gated finishers are allocated LAST among on-GCD entries,
    # because their cast count is a function of how many builder casts happened
    # in front of them. Allocating one early would let it spend combo points
    # nothing had generated yet.
    off_gcd_ids = {e.spell_id for e in apl.entries if e.off_gcd} if apl else set()
    on_gcd = [s for s in ids if s not in off_gcd_ids and abilities.get(s)]
    cp_gated = [s for s in on_gcd if _cp_gate(apl, s) > 0]
    rest = [s for s in on_gcd if s not in cp_gated]
    bounded = [s for s in rest if _useful_cast_interval(abilities[s])[0] > 0]
    unbounded = [s for s in rest if _useful_cast_interval(abilities[s])[0] <= 0]
    ordered = (bounded + cp_gated + unbounded
               + [s for s in ids if s in off_gcd_ids])
    gcd_actions = 0.0

    for sid in ordered:
        ab = abilities.get(sid)
        if ab is None:
            continue
        cp = _cp_gate(apl, sid)
        exp = ab.expected_cast(char_state, content, combo_points=cp)
        warnings.extend(exp.warnings)
        gcd = _gcd_for(ab, char_state)
        occupancy = max(gcd, _cast_time(ab, char_state))
        interval, why = _useful_cast_interval(ab)
        mixed = _mixed_damage_warning(ab)
        if mixed:
            warnings.append(mixed)

        # 3e B1 — ONE allocation rule for every on-GCD ability, cooldown or
        # filler. It used to be two branches, and the filler branch ended
        # `gcd_budget = 0.0` — so the first filler took the whole remainder and
        # every later one got nothing, whatever its own fields said. Measured on
        # the committed fixtures before the fix: **1 of 7** fillers ever cast on
        # the combo-point board and **0 of 8** on the DoT caster.
        #
        # The rule now is the same for both: an ability is capped by its own
        # useful cast interval, capped again by the budget left in front of it,
        # and it consumes only what it uses. A filler with no interval is a spam
        # button and still absorbs the remainder — that part was always right.
        if sid in off_gcd_ids:
            # Queued alongside a GCD action, so it costs no budget; it fires
            # about as often as there are GCD actions to ride, or as its own
            # interval allows, whichever is fewer.
            casts = (gcd_actions if interval <= 0
                     else min(gcd_actions, available / interval))
        else:
            if interval > 0:
                casts = available / interval
                if casts * occupancy > gcd_budget:
                    casts = gcd_budget / occupancy if occupancy else 0.0
                    warnings.append(
                        f"{ab.name}: GCD-limited, not limited by its {why} — "
                        "the budget ran out first")
            else:
                casts = gcd_budget / occupancy if occupancy else 0.0
            if cp > 0:
                # 3e B4 — a finisher is limited by the COMBO POINTS in front of
                # it, not by the GCD budget: it can be spent once per `cp`
                # builder casts. Before this, finishers were CP-gated in the APL
                # (medium_sim) and completely ungated here, so fast_sim cast
                # them as ordinary fillers at whatever rate the budget allowed —
                # while scoring them at 0 CP.
                #
                # The cycle is `cp` builder GCDs plus the finisher's own, so out
                # of N total actions a finisher fires N / (cp + 1) times. N is
                # actions already allocated plus what the remaining budget could
                # still buy — an UPPER bound on builders, so this is an upper
                # bound on the finisher too, and it is stated as one.
                projected = gcd_actions + (gcd_budget / occupancy
                                           if occupancy else 0.0)
                allowed = projected * CP_PER_BUILDER_CAST / (cp + 1)
                if allowed < casts:
                    casts = allowed
                # 3f F2 — emitted HERE, where the hypothesis is applied, and
                # BEFORE the execute-window multiply below so the number quoted
                # is the CP-limited one. It used to live inside that branch,
                # which apl_gen can never generate.
                warnings.append(cp_hypothesis_warning(ab.name, cp, casts))
            window = _health_gate(apl, sid)
            if window < 1.0:
                # 3e B5 — an execute-gated ability is available only for the
                # last `window` of the fight. fast_sim has no clock, so the
                # window enters as a share of its cast count.
                casts *= window
                warnings.append(
                    f"{ab.name}: gated to the last {window:.0%} of the fight by "
                    f"a target-health condition; cast count scaled accordingly")
            gcd_budget = max(0.0, gcd_budget - casts * occupancy)
            gcd_actions += casts

        dmg = exp.mean * casts
        total += dmg
        total_heal += exp.mean_healing * casts
        per_ability[sid] = {
            "name": ab.name, "casts": casts, "damage": dmg,
            "mean_per_cast": exp.mean, "school": ab.school,
            "events": exp.per_event,
            "unresolved_events": exp.unresolved_events,
            "attributed": any(e["attributed"] for e in exp.per_event),
            # 3e B1 — what actually bounded this ability's cast count, so the
            # rotation can be read without re-deriving the allocation by hand.
            "rate_limit": ("off_gcd" if sid in off_gcd_ids
                           else "gcd_budget" if interval <= 0 else why),
        }

    # 3e B1 — an ability allocated ZERO casts used to be completely silent, so a
    # board whose entire filler tier never fires reported a clean rotation. The
    # sim now names them: a build modelled without its own buttons is a
    # different build, and the reader has to be told which one they got.
    starved = [r["name"] for r in per_ability.values() if r["casts"] <= 0.001]
    if starved:
        warnings.append(
            f"{len(starved)} of {len(per_ability)} APL abilities were allocated "
            f"ZERO casts — higher-priority abilities consumed the whole "
            f"{available:.0f}s GCD budget: {', '.join(starved[:8])}"
            + (" ..." if len(starved) > 8 else "")
            + ". This is a rotation the sim could not fit, not a build choice")

    if gcd_budget > 0.01:
        warnings.append(
            f"{gcd_budget:.1f}s of {available:.1f}s GCD budget went UNUSED — "
            "the rotation cannot fill the fight; either an ability is missing "
            "from the APL or the build has no filler")
    warnings.append(
        "fast_sim does not model resources — it cannot see mana/rage/energy "
        "starvation. Use medium_sim for castability")
    warnings.append(EXECUTE_GATING_UNAVAILABLE)
    warnings.append(BASE_GCD_UNVALIDATED)   # 3f F2
    _pw = pet_gap_warning(detect_summons(
        conn, [c.spell_id for c in build_spec.abilities]))
    if _pw:
        warnings.append(_pw)

    # 2e: the same swing layer medium_sim uses. Both tiers must model it or they
    # disagree by the whole auto-attack + DoT share, which is exactly what
    # `check_sim_engine`'s fast-vs-medium agreement guard caught when only
    # medium had it. The tiers may differ in HOW rigorously they evaluate over
    # time; they must never differ in WHAT an ability does (PHASE_2 T3).
    melee_ability_hits = sum(
        r["casts"] for sid, r in per_ability.items()
        if (abilities.get(sid) and abilities[sid].school in ("Physical", "Holystrike")))
    swing_damage, _ = _add_swing_sources(
        conn, char_state, content, available, per_ability, melee_ability_hits,
        warnings, build_spec=build_spec)
    total += swing_damage

    dps = total / content.fight_duration if content.fight_duration else 0.0
    return SimResult(
        metrics={Metric.DAMAGE_DONE: dps,
                 Metric.HEALING_DONE: total_heal / content.fight_duration,
                 Metric.DAMAGE_TAKEN: content.incoming_damage_dps},
        primary_metric=PRIMARY_METRIC_BY_ROLE[build_spec.role],
        role=build_spec.role, content=content, per_ability=per_ability,
        warnings=warnings)


# ------------------------------------------------------------------- medium

@dataclass
class TimelineState:
    """Mutable state the APL grammar evaluates against."""
    now: float = 0.0
    fight_duration: float = 0.0
    cooldowns: dict = field(default_factory=dict)      # spell_id -> ready_at
    buffs: dict = field(default_factory=dict)          # spell_id -> expires_at
    # 3e B2 (E4) — the TARGET's debuffs, kept separate from the player's buffs.
    # One dict for both was the conflation: a DoT on the boss and a seal on
    # yourself are not the same object, and only one of them is what a DoT
    # caster's rotation is deciding about.
    debuffs: dict = field(default_factory=dict)        # spell_id -> expires_at
    resources: dict = field(default_factory=dict)      # name -> current
    pools: dict = field(default_factory=dict)          # name -> max
    combo_points: int = 0
    self_health_pct: float = 100.0
    target_health_pct: float = 100.0

    def cooldown_ready(self, spell_id):
        return self.cooldowns.get(spell_id, 0.0) <= self.now

    def buff_active(self, spell_id):
        return self.buffs.get(spell_id, 0.0) > self.now

    def debuff_active(self, spell_id):
        return self.debuffs.get(spell_id, 0.0) > self.now

    def debuff_remaining(self, spell_id):
        return max(0.0, self.debuffs.get(spell_id, 0.0) - self.now)

    def resource(self, name):
        return self.resources.get(name, 0.0)

    def resource_pct(self, name):
        mx = self.pools.get(name)
        return 100.0 * self.resources.get(name, 0.0) / mx if mx else 100.0

    def time_remaining(self):
        return max(0.0, self.fight_duration - self.now)


def medium_sim(conn, build_spec, apl: APL, content: ContentProfile,
               char_state) -> SimResult:
    """One deterministic timeline. Real cooldowns, GCD and resources; crits and
    procs AVERAGED rather than rolled, so the answer is reproducible.

    This is the tier that answers **"is this rotation physically castable?"** —
    it reports GCD saturation, resource starvation and abilities the priority
    list never actually reached.
    """
    warnings = list(char_state.warnings)
    abilities = _resolve_all(conn, apl.spell_ids(), build_spec.character_level,
                             warnings)

    model_resources = bool(char_state.resource_pools)
    if not model_resources:
        warnings.append(
            "resource pools are UNKNOWN on this CharState — starvation is NOT "
            "modelled and castability answers cooldowns and GCD only. Supply "
            "resource_pools/resource_regen (e.g. mana) for the full answer")

    st = TimelineState(fight_duration=content.fight_duration,
                       pools=dict(char_state.resource_pools),
                       resources=dict(char_state.resource_pools))

    available = _effective_time(content)
    per_ability, total, total_heal = {}, 0.0, 0.0
    gcd_used = idle = 0.0
    starved = {}
    maintenance_assumed = set()
    never_cast = set(apl.spell_ids())
    cp_disclosed = set()        # 3f F2 — one CP_PER_BUILDER_CAST note per spell
    last = -1.0

    while st.now < available:
        if st.now <= last:          # no progress guard
            st.now += 0.1
            continue
        last = st.now
        acted = False
        for entry in apl.entries:
            ab = abilities.get(entry.spell_id)
            if ab is None or not entry_ready(entry, st):
                continue

            # resource gate
            cost = ab.fields.get("resource_cost") or 0.0
            rtype = ab.fields.get("resource_type")
            if cost and rtype and model_resources:
                cost *= 1.0 + char_state.resource_cost_modifier_pct / 100.0
                if st.resources.get(rtype, 0.0) < cost:
                    starved[rtype] = starved.get(rtype, 0) + 1
                    continue
                st.resources[rtype] -= cost

            # 3e B4 (ENGINE_BUGS E1) — the combo-point economy, finally
            # reachable. `combo_points` was declared on TimelineState and
            # incremented NOWHERE in the tree, so `combo_points_at_least` could
            # never be true and any finisher gated on it never cast. Fixing that
            # alone would have done nothing, because `is_finisher` also
            # classified none of a real board's per-combo abilities — detection
            # had to be fixed first (apl_gen), and only then does this bite.
            cp_cost = _cp_gate(apl, entry.spell_id)
            exp = ab.expected_cast(char_state, content, combo_points=cp_cost)
            if cp_cost:
                st.combo_points = max(0, st.combo_points - cp_cost)
                # 3f F2 — medium_sim applied CP_PER_BUILDER_CAST with NO
                # warning at all, while three documents asserted every sim
                # relying on it emits one. Deduped by spell so a 300s fight
                # does not repeat it per cast.
                if entry.spell_id not in cp_disclosed:
                    cp_disclosed.add(entry.spell_id)
                    warnings.append(cp_hypothesis_warning(ab.name, cp_cost))
            elif exp.mean > 0:
                st.combo_points = min(MAX_COMBO_POINTS,
                                      st.combo_points + CP_PER_BUILDER_CAST)
            if entry.spell_id in never_cast:
                warnings.extend(exp.warnings)
                never_cast.discard(entry.spell_id)
            total += exp.mean
            total_heal += exp.mean_healing

            rec = per_ability.setdefault(entry.spell_id, {
                "name": ab.name, "casts": 0, "damage": 0.0,
                "mean_per_cast": exp.mean, "school": ab.school,
                "events": exp.per_event,
                "unresolved_events": exp.unresolved_events,
                "attributed": any(e["attributed"] for e in exp.per_event)})
            rec["casts"] += 1
            rec["damage"] += exp.mean

            cd = ab.fields.get("cooldown_seconds") or 0.0
            if cd:
                st.cooldowns[entry.spell_id] = st.now + cd
            dur = ab.fields.get("duration_seconds")
            if dur and _routes_as_debuff(ab):
                # 3e B2 — a periodic damage effect lands on the TARGET.
                # Everything with a duration used to be filed under st.buffs
                # regardless, so `debuff_missing` would have read the player.
                st.debuffs[entry.spell_id] = st.now + dur
            elif dur:
                st.buffs[entry.spell_id] = st.now + dur
            elif any(c.get("type") == "buff_missing"
                     and c.get("spell_id") == entry.spell_id
                     for c in entry.conditions):
                # A maintenance buff with no known duration. Left untracked it
                # is re-cast every GCD and monopolises the entire rotation —
                # which is how Seal of Command came to eat 47 of 47 GCDs. Held
                # for the rest of the fight instead, which is what a seal
                # actually does, and warned about because it IS an assumption.
                st.buffs[entry.spell_id] = st.fight_duration
                maintenance_assumed.add(entry.spell_id)

            if not entry.off_gcd:
                step = max(_gcd_for(ab, char_state), _cast_time(ab, char_state))
                gcd_used += step
                _regen(st, char_state, step)
                st.now += step
                _decay_health(st)
                acted = True
                break
            # off-GCD entries cost no time; keep scanning the priority list

        if not acted:
            idle += 0.1
            _regen(st, char_state, 0.1)
            st.now += 0.1
            _decay_health(st)

    # ------------------------------------------------------- 2e: the swing layer
    # Auto-attacks, seal riders and Righteous Vengeance are rate-driven by the
    # swing timer or by the rotation's own crit output, so none of them can be
    # expressed as "damage per cast". They are added here, after the timeline,
    # each as its own `per_ability` row so nothing is hidden inside a total.
    melee_ability_hits = sum(
        r["casts"] for sid, r in per_ability.items()
        if (abilities.get(sid) and abilities[sid].school in ("Physical", "Holystrike")))
    swing_damage, seal_note = _add_swing_sources(
        conn, char_state, content, available, per_ability, melee_ability_hits,
        warnings, build_spec=build_spec)
    total += swing_damage

    dps = total / content.fight_duration if content.fight_duration else 0.0
    saturation = gcd_used / available if available else 0.0
    warnings.append(EXECUTE_GATING_UNAVAILABLE)
    warnings.append(BASE_GCD_UNVALIDATED)   # 3f F2
    _pw = pet_gap_warning(detect_summons(
        conn, [c.spell_id for c in build_spec.abilities]))
    if _pw:
        warnings.append(_pw)
    _pw = pet_gap_warning(detect_summons(
        conn, [c.spell_id for c in build_spec.abilities]))
    if _pw:
        warnings.append(_pw)
    warnings.append(
        f"GCD saturation {saturation:.0%} ({gcd_used:.0f}s of {available:.0f}s "
        f"actable); {idle:.0f}s idle")
    if saturation > 0.99:
        warnings.append(
            "rotation is GCD-SATURATED — lower-priority abilities are being "
            "squeezed out; adding damage to a filler will not increase DPS")
    if idle > available * 0.10:
        warnings.append(
            f"{idle:.0f}s ({idle / available:.0%}) IDLE — the priority list "
            "cannot fill the fight; the build is missing a filler or "
            "everything is on cooldown")
    for rtype, n in starved.items():
        warnings.append(
            f"resource STARVATION: {n} decision points where a {rtype} cost "
            "could not be paid — this is the error class fast_sim cannot see")
    for sid in never_cast:
        nm = abilities[sid].name if sid in abilities else sid
        warnings.append(
            f"{nm} ({sid}) is in the APL but was NEVER CAST — its conditions "
            "never came true, or higher priorities always won")
    zero_damage = [sid for sid, r in per_ability.items()
                   if r["casts"] > 0 and r["damage"] <= 0]
    for sid in zero_damage:
        nm = abilities[sid].name if sid in abilities else sid
        warnings.append(
            f"🛑 {nm} ({sid}) was cast {per_ability[sid]['casts']} times for "
            "ZERO damage — it resolves to no known magnitude, which is NOT the "
            "same as doing nothing. Every GCD it takes is scored as wasted, so "
            "ANY APL comparison that moves this ability is measuring the data "
            "gap, not the rotation. Do not rank rotations against this build "
            "until it resolves")
    for sid in maintenance_assumed:
        nm = abilities[sid].name if sid in abilities else sid
        warnings.append(
            f"{nm} ({sid}) has NO KNOWN DURATION and is treated as a "
            "maintenance buff held for the whole fight — an ASSUMPTION, made "
            "because the alternative (recast every GCD) monopolises the "
            "rotation. ⚠ Its damage is also attributed PER CAST, but a seal's "
            "damage is a per-swing rider: cast once, its contribution here is "
            "understated by roughly the swing count. Do not read its damage "
            "share as meaningful")

    return SimResult(
        metrics={Metric.DAMAGE_DONE: dps,
                 Metric.HEALING_DONE: total_heal / content.fight_duration,
                 Metric.DAMAGE_TAKEN: content.incoming_damage_dps},
        primary_metric=PRIMARY_METRIC_BY_ROLE[build_spec.role],
        role=build_spec.role, content=content, per_ability=per_ability,
        warnings=warnings)


def _add_swing_sources(conn, char_state, content, available, per_ability,
                       melee_ability_hits, warnings, build_spec=None):
    """Auto-attacks, seal riders and Righteous Vengeance (session `2e`, T1).

    Returns the damage added. Every source that cannot be computed is WARNED and
    contributes zero — never estimated, never fitted from the parse it is meant
    to be checked against.

    🚨 `3k` B3 — `build_spec` is what gates Righteous Vengeance on actually
    HOLDING the card. It was not needed while the derivation was dead code
    (`ev["crit_damage"]` was a key nothing wrote, so the value was always 0);
    the moment that key is populated, an ungated derivation gives all 35 cohort
    characters a Righteous Vengeance row and only 9 of them log one. That is
    phantom production, which is as wrong as a missing key. Passing `None`
    keeps the old ungated behaviour for callers that have no spec, and **says
    so in a warning** rather than silently assuming ownership.
    """
    added = 0.0
    mh, oh, w = swing_events(char_state, available)
    warnings.extend(w)
    if mh <= 0:
        return 0.0, None

    # --- auto-attacks -------------------------------------------------------
    for weapon, count, label, off in ((char_state.main_hand, mh, "Melee auto (MH)", False),
                                      (char_state.off_hand, oh, "Melee auto (OH)", True)):
        if not weapon or count <= 0:
            continue
        out = expected_swing(char_state, weapon, content.target, is_offhand=off)
        if out is None:
            continue
        warnings.extend(out.warnings)
        dmg = out.mean * count
        added += dmg
        per_ability[f"auto_{'oh' if off else 'mh'}"] = {
            "name": label, "casts": round(count, 1), "damage": dmg,
            "mean_per_cast": out.mean, "school": "Physical",
            "events": [], "unresolved_events": [], "attributed": False}

    # --- seal riders --------------------------------------------------------
    # The RATE is measured; the per-proc MAGNITUDE is not available, because the
    # damage spell (20424) is absent from `spell_dbc_raw` entirely — it is
    # reached only as an EffectTriggerSpell of the seal, a route the extract does
    # not currently follow. Procs are reported; damage is NOT invented.
    melee_events = mh + oh + melee_ability_hits
    procs = seal_procs(melee_events)
    seal_note = (
        f"seal riders: ~{procs:.0f} procs expected over the fight "
        f"({melee_events:.0f} melee events x {SEAL_PROC_PER_MELEE_EVENT:.2f}); "
        f"rate is {SEAL_PROC_RATE_EVIDENCE}. 🛑 Per-proc DAMAGE is UNMODELLED — "
        "the seal's damage spell (20424) has no record in spell_dbc_raw, so it "
        "is reached by no extraction route. Seal damage is therefore MISSING "
        "from this total, not zero; it measured 8.5% of unbuffed and 6.5% of "
        "buffed damage in the 2e captures")
    warnings.append(seal_note)

    # --- Righteous Vengeance ------------------------------------------------
    # A derived source: 30% of the rotation's own crit damage as an 8 s Holy DoT.
    # It has no magnitude of its own in the DBC (aura 3, periodic, value supplied
    # by the caster), so this is the only way it can ever be modelled.
    crit_damage = 0.0
    for sid, rec in list(per_ability.items()):
        for ev in rec.get("events") or ():
            if ev.get("crit_damage"):
                crit_damage += ev["crit_damage"] * rec["casts"]

    # `3k` B3 — does this character actually HOLD Righteous Vengeance? The
    # talent card resolves to one of three rank ids. A build_spec of None means
    # the caller could not say, and that is warned rather than assumed.
    holds_rv = None
    if build_spec is not None:
        holds_rv = any(c.spell_id in RIGHTEOUS_VENGEANCE_CARD_SPELL_IDS
                       for c in (build_spec.talents or ()))
    if crit_damage > 0 and holds_rv is False:
        warnings.append(
            f"Righteous Vengeance NOT modelled — this build does not slot the "
            f"card ({crit_damage:,.0f} crit damage would otherwise have "
            f"derived {righteous_vengeance_damage(crit_damage):,.0f}). "
            "Deriving it from crit damage alone would credit every critting "
            "build with a talent it does not have")
    elif crit_damage > 0 and holds_rv is None:
        warnings.append(
            "Righteous Vengeance derived WITHOUT a card-ownership check — the "
            "caller passed no build_spec, so whether this build slots the "
            "talent is unknown. Treat the RV row as an upper bound")
    if crit_damage > 0 and holds_rv is not False:
        rv = righteous_vengeance_damage(crit_damage)
        added += rv
        per_ability[RIGHTEOUS_VENGEANCE_SPELL_ID] = {
            "name": "Righteous Vengeance", "casts": 0, "damage": rv,
            "mean_per_cast": 0.0, "school": "Holy",
            "events": [], "unresolved_events": [], "attributed": True}
        warnings.append(
            f"Righteous Vengeance is DERIVED: {RIGHTEOUS_VENGEANCE_FRACTION:.0%} "
            f"of {crit_damage:,.0f} crit damage = {rv:,.0f}. It pools on refresh "
            "(92-101% uptime over four parses) so the total is conserved; a "
            "per-tick figure would be meaningless. Cannot crit (0/130 ticks in 2e)")
    else:
        warnings.append(
            "Righteous Vengeance NOT modelled — no per-event crit damage was "
            "reported by the ability model, so its 30% cannot be derived. It "
            "measured 6.7-9.9% of damage in the 2e captures")
    return added, seal_note


def _regen(st: TimelineState, char_state, seconds):
    for name, rate in (char_state.resource_regen or {}).items():
        mx = st.pools.get(name)
        cur = st.resources.get(name, 0.0) + rate * seconds
        st.resources[name] = min(cur, mx) if mx else cur


# --------------------------------------------------------------------- slow

def slow_sim(conn, build_spec, apl: APL, content: ContentProfile, char_state,
             iterations=1000, seed=None) -> SimResult:
    """Monte Carlo over COMBAT RNG (crits, avoidance, damage rolls).

    🛑 This is not the same thing as `core/sim/uncertainty.py`, which samples
    KNOWLEDGE uncertainty. Combat variance ("this build rolls 3,900-4,500 on any
    given pull") and knowledge uncertainty ("we don't know this coefficient, so
    the true mean is somewhere in 3,800-4,600") are different quantities and are
    never merged — merging them hides the one you can act on (PHASE_2 T6).
    """
    warnings = list(char_state.warnings)
    abilities = _resolve_all(conn, apl.spell_ids(), build_spec.character_level,
                             warnings)
    rng = random.Random(seed)

    # The timeline itself is deterministic (same rotation every iteration); what
    # varies is how each cast rolls. That isolates combat variance from rotation
    # variance, which would otherwise be confounded in one number.
    skeleton = medium_sim(conn, build_spec, apl, content, char_state)
    warnings.extend(skeleton.warnings)

    totals = []
    for _ in range(iterations):
        run = 0.0
        for sid, rec in skeleton.per_ability.items():
            ab = abilities.get(sid)
            if ab is None:
                continue
            for _ in range(int(rec["casts"])):
                run += ab.roll_cast(char_state, content, rng).damage
        totals.append(run)

    totals.sort()
    n = len(totals)
    mean = sum(totals) / n if n else 0.0
    dur = content.fight_duration or 1.0
    lo = totals[int(0.025 * n)] if n else 0.0
    hi = totals[min(n - 1, int(0.975 * n))] if n else 0.0
    var = sum((t - mean) ** 2 for t in totals) / n if n else 0.0

    warnings.append(
        f"combat RNG only: {iterations} iterations, 95% of pulls land between "
        f"{lo / dur:.0f} and {hi / dur:.0f} DPS (sd {var ** 0.5 / dur:.0f}). "
        "This is NOT knowledge uncertainty — see sim_with_uncertainty()")

    res = SimResult(
        metrics={Metric.DAMAGE_DONE: mean / dur,
                 Metric.HEALING_DONE: skeleton.metrics.get(Metric.HEALING_DONE, 0.0),
                 Metric.DAMAGE_TAKEN: content.incoming_damage_dps},
        primary_metric=PRIMARY_METRIC_BY_ROLE[build_spec.role],
        role=build_spec.role, content=content,
        per_ability=skeleton.per_ability, warnings=warnings)
    res.combat_rng = {"iterations": iterations, "mean_dps": mean / dur,
                      "p2_5_dps": lo / dur, "p97_5_dps": hi / dur,
                      "sd_dps": var ** 0.5 / dur}
    return res
