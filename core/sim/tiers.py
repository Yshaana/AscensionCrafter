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
from .apl import APL, entry_ready
from .content import ContentProfile, Metric, PRIMARY_METRIC_BY_ROLE, SimResult
from .swings import (
    swing_events, expected_swing, seal_procs, righteous_vengeance_damage,
    SEAL_PROC_PER_MELEE_EVENT, SEAL_PROC_RATE_EVIDENCE,
    RIGHTEOUS_VENGEANCE_SPELL_ID, RIGHTEOUS_VENGEANCE_FRACTION,
)

# retail_hypothesis: 1.5s base GCD, floored at 1.0s, reduced by spell haste for
# spells only. Not yet validated on Ascension — a calibration candidate.
BASE_GCD = 1.5
MIN_GCD = 1.0


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
    off_gcd_ids = {e.spell_id for e in apl.entries if e.off_gcd} if apl else set()
    on_gcd = [s for s in ids if s not in off_gcd_ids]
    ordered = ([s for s in on_gcd if (abilities.get(s) and
                                      (abilities[s].fields.get("cooldown_seconds") or 0) > 0)]
               + [s for s in on_gcd if (abilities.get(s) and
                                        not (abilities[s].fields.get("cooldown_seconds") or 0))]
               + [s for s in ids if s in off_gcd_ids])
    gcd_actions = 0.0

    for sid in ordered:
        ab = abilities.get(sid)
        if ab is None:
            continue
        exp = ab.expected_cast(char_state, content)
        warnings.extend(exp.warnings)
        gcd = _gcd_for(ab, char_state)
        occupancy = max(gcd, _cast_time(ab, char_state))
        cd = ab.fields.get("cooldown_seconds") or 0.0

        if sid in off_gcd_ids:
            # Queued alongside a GCD action, so it costs no budget; it fires
            # about as often as there are GCD actions to ride, or as its own
            # cooldown allows, whichever is fewer.
            casts = gcd_actions if cd <= 0 else min(gcd_actions, available / cd)
        elif cd > 0:
            casts = available / cd
            need = casts * occupancy
            if need > gcd_budget:
                casts = gcd_budget / occupancy if occupancy else 0.0
                warnings.append(
                    f"{ab.name}: GCD-limited, not cooldown-limited — the "
                    "budget ran out before its cooldown did")
            gcd_budget = max(0.0, gcd_budget - casts * occupancy)
            gcd_actions += casts
        else:
            # fillers split whatever budget the cooldowns left, in priority order
            casts = gcd_budget / occupancy if occupancy else 0.0
            gcd_budget = 0.0
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
        }

    if gcd_budget > 0.01:
        warnings.append(
            f"{gcd_budget:.1f}s of {available:.1f}s GCD budget went UNUSED — "
            "the rotation cannot fill the fight; either an ability is missing "
            "from the APL or the build has no filler")
    warnings.append(
        "fast_sim does not model resources — it cannot see mana/rage/energy "
        "starvation. Use medium_sim for castability")

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
        warnings)
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
    resources: dict = field(default_factory=dict)      # name -> current
    pools: dict = field(default_factory=dict)          # name -> max
    combo_points: int = 0
    self_health_pct: float = 100.0
    target_health_pct: float = 100.0

    def cooldown_ready(self, spell_id):
        return self.cooldowns.get(spell_id, 0.0) <= self.now

    def buff_active(self, spell_id):
        return self.buffs.get(spell_id, 0.0) > self.now

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

            exp = ab.expected_cast(char_state, content)
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
            if dur:
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
                acted = True
                break
            # off-GCD entries cost no time; keep scanning the priority list

        if not acted:
            idle += 0.1
            _regen(st, char_state, 0.1)
            st.now += 0.1

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
        warnings)
    total += swing_damage

    dps = total / content.fight_duration if content.fight_duration else 0.0
    saturation = gcd_used / available if available else 0.0
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
                       melee_ability_hits, warnings):
    """Auto-attacks, seal riders and Righteous Vengeance (session `2e`, T1).

    Returns the damage added. Every source that cannot be computed is WARNED and
    contributes zero — never estimated, never fitted from the parse it is meant
    to be checked against.
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
    if crit_damage > 0:
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
