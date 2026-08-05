"""Phase 2 T4 — `compute_stats()`: BuildSpec + content -> CharState.

ONE implementation used by every consumer (sim, legos, builder, guides) —
path bonuses, percentage multipliers and stat conversions interact, and two
implementations would diverge (PHASE_2 T4).

What is modelled in 2a, honestly:

* **`stats_override` is the primary path** until Phase 3 lands an items table.
  Its semantics: FINAL character-sheet values (path, talents and gear already
  baked in). Path *stat* bonuses are NOT reapplied on top — only the weapon-
  clause damage multipliers attach (a sheet never shows those) plus warnings.
* **Component mode** (no override): gear item stats + path flat grants + path
  conversions + base-game stat->crit conversions. Talent stat contributions
  are NOT modelled yet — each unmodelled slot lands in `warnings`, never
  silently contributes zero without saying so.
* **Path magnitudes carry their evidence status inline** (primer §3 +
  confirmed_facts). The Duality SP amp is the measured 1.895x (controlled
  empty-spec test 2026-08-04, `duality_sp_amp_confirmed_reverses_retraction`),
  NOT the tooltip's 1.75. The Duality AP factor 0.548x is a measured ANOMALY
  contradicting the tooltip (`duality_attack_power_anomaly`, open) — it is a
  parameter, and using it always warns.
"""
from dataclasses import dataclass, field

from ..sim.combat_engine import RatingConversions

# --- base-game stat -> crit conversions (ascension_confirmed, measured) --------
# build_paladin-hammerdin §12: Agi -> melee crit ~32.4/1%, Int -> spell crit ~61/1%.
AGI_PER_MELEE_CRIT_PCT = 32.4
INT_PER_SPELL_CRIT_PCT = 61.0

# --- Duality: UNDER A BUG ADVISORY (session 2d, 2026-08-05) --------------------
# 🛑 bugs/bug_path-of-duality-broken.md — Path of Duality (129243) is broken in
# several ways, reported independently by multiple players and corroborated by
# our own captures. Modelling its TOOLTIP would fabricate damage the server does
# not deliver, so every value here models the BUGGED, MEASURED behaviour and the
# path always warns.
#
# 1. SP amp: NOT APPLYING. Measured on identical gear/board, post-relog:
#    PoS 250 SP vs PoD 271 SP, i.e. a flat +19 after the Lunar Guidance delta —
#    and an independent player reports the same "difference of 19 Spellpower".
#    ❌ The 1.895x from 2026-08-04 is RETRACTED as a Duality property: that test
#    used rapid path toggling, which cannot be separated from a stale
#    Path-of-Intelligence doubling or an ON phase of the AP cycling bug.
# INTENDED, per Ascension's own path documentation (2026-08-05): "Grants Attack
# Power equal to your highest primary stat (Strength or Agility) and boosts Spell
# Power from GEAR by 75%", cross-stat crits, and two named weapon sub-abilities —
# `Unleashed Force` (2H, +6% all damage) and `Twin Flurry` (1H, +10% haste).
# 🚨 This VINDICATES the project's v3-era in-game tooltip read of a "x1.75
# itemised SP amp", which v4 retracted on the grounds that it was not visible on
# the live sheet. Both were right about different things: v3 read the DESIGN, v4
# observed the BROKEN DELIVERY. Four document versions oscillated between them
# because the intended-vs-delivered distinction did not exist until session 2d.
# ⚠ Tier: external documentation, corroborated by our own v3 tooltip read and by
# a bug report expecting a much larger grant. An in-game tooltip would upgrade it.
DUALITY_SP_AMP_INTENDED = 1.75       # applies to GEAR spell power only
DUALITY_FLAT_SP_MEASURED = 19.0      # damage AND healing (BonusHealing 229->248)
DUALITY_FLAT_INT_MEASURED = 19.0     # PoS Int 180 vs PoD Int 199
DUALITY_AP_FACTOR_INTENDED = 1.0     # "AP = highest of Str or Agi", at 100%
DUALITY_STAT_PER_CROSS_CRIT_RATING = 3.4
# back-compat aliases (callers written before the intended/impaired split)
DUALITY_SP_AMP_MEASURED = DUALITY_SP_AMP_INTENDED
DUALITY_AP_FACTOR_MEASURED = DUALITY_AP_FACTOR_INTENDED

# --- system impairments --------------------------------------------------------
# 🛑 OWNER DECISION 2026-08-05, correcting a same-session over-reach of mine that
# hardcoded the bugged values as the model. **The model stays the INTENDED
# behaviour**; what the server currently fails to deliver lives here and is
# applied only when a caller asks for `system_state='as_measured'`.
#
# Why the separation:
#   1. A fix must not require re-deriving the model — set `fixed_on` and the
#      intended model is already correct. Baking a bug into the model makes the
#      fix a landmine someone has to remember to defuse.
#   2. **Other players' parses are full of Duality**, mostly from players unaware
#      of the bug. Modelling intended behaviour is what lets a crawled character
#      read as "underperforming the design" rather than as a worse build — and it
#      turns the impairment into a DETECTOR: when Duality parses stop
#      underperforming, that is the fix landing.
#   3. **The bug is intermittent**, so neither endpoint is the truth. Real output
#      lands between "bonus never applies" and "bonus always applies"; a single
#      constant cannot express that, a range with a named unknown can.
# Policy ("do not recommend Duality") is a RECOMMENDATION-layer concern and is a
# flag here, never a change to the math.
#
# This is a THIRD kind of uncertainty, distinct from the two the sim already
# separates — combat RNG (slow_sim) and knowledge uncertainty (uncertainty.py).
# Here the formula is known and the SERVER is not honouring it.
#
# 🛑 `duty_cycle` is None on purpose. The AP bonus is reported to cycle every
# ~10-15 s, but nobody has measured what FRACTION of the time it is up, and a
# point estimate would be fabricated precision on this build's most load-bearing
# stat. `as_measured` therefore yields a RANGE. Measuring it is a 2e task and the
# data already exists: weapon-damage abilities should be BIMODAL in a Duality
# parse, so a histogram of Dawnreaver non-crit hits gives the duty cycle directly.
SYSTEM_IMPAIRMENTS = {
    "path:Duality": {
        "evidence": "bugs/bug_path-of-duality-broken.md",
        "detected_on": "2026-08-05",
        "fixed_on": None,
        "recommend": False,          # policy flag, read by the recommender
        "effects": {
            "ap_grant": {
                "intended_factor": 1.0,
                "impaired_factor_range": (0.0, 1.0),   # cycles fully on/off
                "duty_cycle": None,                    # UNMEASURED — see above
                "note": "AP bonus cycles on/off every ~10-15 s (a player watched "
                        "832<->1128 standing still; we read 174<->307)",
            },
            "sp_amp": {
                "intended_factor": 1.75,                # gear SP x 1.75
                "impaired_factor": 1.0,                 # amp absent entirely
                "impaired_flat_instead": 19.0,
                "note": "the +75% gear spell-power boost does not apply; only a "
                        "flat ~+19 arrives. At gear SP 229 that is 271 observed "
                        "against ~425 intended — a ~36% shortfall, and it is why "
                        "a bug report describes 'a difference of 19 Spellpower'",
            },
            "weapon_clause": {
                "intended": "2H +6% all damage (Unleashed Force) / "
                            "1H +10% haste (Twin Flurry)",
                "impaired_factor": 0.0,
                "note": "2H Unleashed Force reported fully non-functional; 1H "
                        "Twin Flurry reported to reach MAIN HAND only. Two "
                        "reports differ slightly on the 1H case",
            },
        },
    },
}


def impairment_for(path):
    """The OPEN impairment record for a path, or None. `fixed_on` closes it."""
    rec = SYSTEM_IMPAIRMENTS.get(f"path:{path}")
    return None if (rec is None or rec.get("fixed_on")) else rec


@dataclass
class CharState:
    """Resolved character state the sim consumes. Percent fields are final
    percentages; rating fields are pre-conversion where named `_rating`."""
    level: int
    # primary stats
    strength: float = 0.0
    agility: float = 0.0
    intellect: float = 0.0
    spirit: float = 0.0
    stamina: float = 0.0
    # offense
    attack_power: float = 0.0
    ranged_attack_power: float = 0.0
    spell_power: float = 0.0
    spell_power_by_school: dict = field(default_factory=dict)  # 'Holy' -> bonus
    bonus_healing: float = 0.0
    # chances (final, post-conversion)
    melee_crit_pct: float = 0.0
    spell_crit_pct: float = 0.0
    melee_hit_pct: float = 0.0
    spell_hit_pct: float = 0.0
    melee_haste_pct: float = 0.0
    spell_haste_pct: float = 0.0
    expertise_points: float = 0.0
    armor_pen_pct: float = 0.0
    # weapons: {'min','max','speed'} or None
    main_hand: dict | None = None
    off_hand: dict | None = None
    # named multiplier buckets, e.g. 'physical_ability' -> 1.10. Consumers
    # multiply the buckets that apply to an ability; unknown buckets are ignored
    # BY NAME, never silently — ability_model surfaces which buckets it applied.
    damage_multipliers: dict = field(default_factory=dict)
    ability_crit_damage_bonus: float = 0.0   # additive on the crit multiplier
    # T4b: the build's decoded talent effects, or None when talents were not
    # modelled (no `conn` passed to compute_stats). None and "no talents" are
    # different states and the ability model reports which one it saw.
    talents: object = None
    # Resource pools and regen, for the medium sim's castability question.
    # EMPTY MEANS UNKNOWN, not zero: medium_sim refuses to model starvation
    # rather than assuming an infinite bar or an empty one.
    resource_pools: dict = field(default_factory=dict)   # 'mana' -> max value
    resource_regen: dict = field(default_factory=dict)   # 'mana' -> per second
    # Path of Agility's 1H clause reduces GCD and cost by 8%; 2a recorded it as
    # "rotation-level, medium sim (2b) owns it" and this is where it arrives.
    gcd_modifier_pct: float = 0.0            # negative = faster
    resource_cost_modifier_pct: float = 0.0  # negative = cheaper
    # Set only when system_state='as_measured' AND the build uses a system with
    # an open, INTERMITTENT impairment. None means "no impairment applied" —
    # which is different from "impairment measured at zero".
    impairment_range: dict | None = None
    # Open SYSTEM_IMPAIRMENTS records touching this build, whatever the mode.
    # Carries the policy flag: an entry with recommend=False must not be
    # presented as a recommendation regardless of how well it sims.
    impairments: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    def effective_spell_power(self, school):
        """Generic SP + school-specific bonus. School-scoped scaling terms
        (SPFR/SPH/...) resolve through this — treating them as generic SP
        double-counts (1c audit kickoff note #2)."""
        return self.spell_power + self.spell_power_by_school.get(school or "", 0.0)


# ------------------------------------------------------------- path bonus data

# primer §3. Each entry lists what IS modelled; anything the primer states that
# is NOT modelled here must be warned about by name in compute_stats.
# Flat grants use the primer's stated curves; '~' values are approximations and
# say so in the warning they emit.


def _flat_grants(path, level):
    """Path flat stat grants (primer §3). Returns (stat_deltas, notes)."""
    if path == "Strength":
        return {"strength": 4 + 0.5 * level}, []
    if path == "Agility":
        return {"agility": 4 + 0.5 * level}, []
    if path in ("Intelligence", "Healing"):
        return ({"intellect": 4 + 1.25 * level, "spirit": 40.0},
                ["path spirit grant ~40 is approximate (primer §3 '~40')"])
    if path == "Duality":
        # primer §3 states no flat grant; MEASURED 2026-08-05 (post-relog, same
        # gear/board, PoS vs PoD): +19 Intellect and +19 Spell Power, the latter
        # applying to healing as well. Whether +19 is the design or the bugged
        # remnant of a larger grant is unknown — see bug_path-of-duality-broken.
        return ({"intellect": DUALITY_FLAT_INT_MEASURED},
                ["Duality flat grants +19 Int / +19 SP are MEASURED (2026-08-05 "
                 "path trio), not from the primer — and the path is under a bug "
                 "advisory, so they may be a broken partial application"])
    return {}, []


def _weapon_clause(path, wielding):
    """Path weapon-clause effects -> (damage_multipliers, crit_damage_bonus,
    haste_bonus_pct(melee, spell), notes). primer §3; 'abilities' wording
    excludes auto-attacks (ascension_confirmed)."""
    mults, crit_dmg, haste_m, haste_s, notes = {}, 0.0, 0.0, 0.0, []
    gcd_mod = cost_mod = 0.0
    is_2h = wielding in ("2h", "dual_2h")
    if path == "Strength":
        if is_2h:
            mults["physical_ability"] = 1.10   # excludes autos ("abilities")
        else:
            notes.append("Strength 1H +20% ArP clause not yet modelled as "
                         "rating — flagged instead of silently dropped")
    elif path == "Agility":
        if is_2h:
            crit_dmg = 0.20                    # ability crit damage bonus
        else:
            # primer §3: damaging melee/ranged abilities' GCD and cost -8%.
            # Carried on CharState for the medium sim rather than folded into a
            # damage number — it is a castability effect, not a damage one.
            gcd_mod = cost_mod = -8.0
    elif path == "Duality":
        # INTENDED behaviour. Both clauses are reported non-functional in game
        # (bug_path-of-duality-broken.md symptoms 4-5), but that belongs to the
        # impairment layer, applied only for system_state='as_measured'.
        if is_2h:
            mults["all_damage"] = 1.06         # magic AND physical +6%
        else:
            haste_m = haste_s = 10.0
    elif path == "Intelligence":
        if is_2h:
            haste_s = 12.0
        else:
            mults["spell_damage"] = 1.05
    elif path == "Healing":
        if is_2h:
            haste_s = 10.0
            notes.append("Healing 2H +3% spell crit applied")
        else:
            notes.append("Healing 1H +5% healing clause not modelled yet")
    return mults, crit_dmg, haste_m, haste_s, gcd_mod, cost_mod, notes


# --------------------------------------------------------------- gear loading

# scouted_gear stats_json key normalisation. Conservative: unknown keys warn.
_GEAR_STAT_KEYS = {
    "strength": "strength", "agility": "agility", "intellect": "intellect",
    "spirit": "spirit", "stamina": "stamina",
    "attack_power": "attack_power", "ranged_attack_power": "ranged_attack_power",
    "spell_power": "spell_power", "healing_power": "bonus_healing",
}
_GEAR_RATING_KEYS = {
    "crit_rating": "crit", "hit_rating": "hit", "haste_rating": "haste",
    "expertise_rating": "expertise", "armor_penetration_rating": "armor_penetration",
}


def compute_stats(build_spec, content, conversions: RatingConversions,
                  duality_sp_amp=DUALITY_SP_AMP_INTENDED,
                  duality_ap_factor=DUALITY_AP_FACTOR_INTENDED,
                  conn=None, system_state="intended"):
    """Resolve a BuildSpec into a CharState for `content`.

    Pass `conn` to model talents (session 2c, T4b). Without it the 2a behaviour
    is preserved — talents contribute nothing and say so.

    `system_state` selects which reality to model (session 2d):

    * `'intended'` (default) — what the system is DESIGNED to do. Use for
      theorycrafting, build comparison and recommendations, and for reading a
      crawled character against the design.
    * `'as_measured'` — apply `SYSTEM_IMPAIRMENTS`, i.e. what the server
      currently delivers. Use when reproducing a real parse (calibration).
      🛑 For an INTERMITTENT impairment this is a RANGE, not a point: the result
      carries `cs.impairment_range` with the low/high CharState-affecting factor
      and a warning naming the unmeasured duty cycle. Never collapse it silently.

    Either way, if the build's path (or any other system it uses) has an open
    impairment, a loud advisory lands in `warnings` — including the policy flag
    for whether it should currently be recommended at all.

    🛑 **Sheet mode and talents interact, and getting it wrong double-counts.**
    `stats_override` means the values are FINAL character-sheet readings, and a
    sheet already includes every talent's contribution to crit, AP, SP and
    haste. So in sheet mode only the talents' DAMAGE MULTIPLIERS are applied —
    a sheet never displays those — and their stat contributions are deliberately
    dropped. In component mode both halves apply.
    """
    warnings = list(conversions.warnings)
    level = build_spec.character_level
    wielding = build_spec.wielding()

    cs = CharState(level=level)

    # ----- weapons come from gear either way ------------------------------
    for slot_name, attr in (("main_hand", "main_hand"), ("off_hand", "off_hand")):
        g = build_spec.gear.get(slot_name)
        if g and g.weapon:
            setattr(cs, attr, {k: g.weapon[k] for k in ("min", "max", "speed")
                               if k in g.weapon})

    if build_spec.stats_override:
        # ----- sheet mode: values are FINAL; do not reapply path stats -----
        for k, v in build_spec.stats_override.items():
            if hasattr(cs, k) and not isinstance(getattr(cs, k), (dict, list)):
                setattr(cs, k, v)
            elif k == "spell_power_by_school":
                cs.spell_power_by_school = dict(v)
            elif k in ("resource_pools", "resource_regen", "damage_multipliers"):
                setattr(cs, k, dict(v))
            elif k in ("hit_rating", "crit_rating", "haste_rating",
                       "expertise_rating", "armor_pen_rating"):
                # ratings supplied raw: convert here so sheet users can paste
                # the sheet's rating numbers directly
                if k == "hit_rating":
                    cs.melee_hit_pct = conversions.percent("hit_melee", v)
                    cs.spell_hit_pct = conversions.percent("hit_spell", v)
                elif k == "crit_rating":
                    cs.melee_crit_pct += conversions.percent("crit_melee", v)
                    cs.spell_crit_pct += conversions.percent("crit_spell", v)
                elif k == "haste_rating":
                    cs.melee_haste_pct = conversions.percent("haste_melee", v)
                    cs.spell_haste_pct = conversions.percent("haste_spell", v)
                elif k == "expertise_rating":
                    cs.expertise_points = v / conversions.divisors["expertise"] \
                        if conversions.divisors.get("expertise") else 0.0
                elif k == "armor_pen_rating":
                    cs.armor_pen_pct = conversions.percent("armor_penetration", v)
            else:
                warnings.append(f"stats_override key {k!r} not recognised — "
                                "ignored (named, not silent)")
        warnings.append(
            "stats_override in use: sheet values treated as FINAL (path stats, "
            "talents, gear assumed already included) — only weapon-clause "
            "multipliers were added on top")
    else:
        # ----- component mode: gear + path, talents NOT yet modelled -------
        for g in build_spec.gear.values():
            for k, v in (g.stats or {}).items():
                key = k.lower()
                if key in _GEAR_STAT_KEYS:
                    setattr(cs, _GEAR_STAT_KEYS[key],
                            getattr(cs, _GEAR_STAT_KEYS[key]) + v)
                elif key in _GEAR_RATING_KEYS:
                    r = _GEAR_RATING_KEYS[key]
                    if r == "crit":
                        cs.melee_crit_pct += conversions.percent("crit_melee", v)
                        cs.spell_crit_pct += conversions.percent("crit_spell", v)
                    elif r == "hit":
                        cs.melee_hit_pct += conversions.percent("hit_melee", v)
                        cs.spell_hit_pct += conversions.percent("hit_spell", v)
                    elif r == "haste":
                        cs.melee_haste_pct += conversions.percent("haste_melee", v)
                        cs.spell_haste_pct += conversions.percent("haste_spell", v)
                    elif r == "expertise":
                        cs.expertise_points += v / conversions.divisors["expertise"]
                    elif r == "armor_penetration":
                        cs.armor_pen_pct += conversions.percent(
                            "armor_penetration", v)
                else:
                    warnings.append(
                        f"gear stat key {k!r} on {g.name} not recognised — "
                        "ignored (named, not silent)")

        grants, notes = _flat_grants(build_spec.path, level)
        warnings.extend(notes)
        for stat, delta in grants.items():
            setattr(cs, stat, getattr(cs, stat) + delta)

        # path AP conversions (primer §3)
        if build_spec.path == "Strength":
            cs.attack_power += cs.strength          # AP = 100% of Strength
            warnings.append("Strength->parry conversion not modelled")
        elif build_spec.path == "Agility":
            cs.attack_power += cs.agility
            warnings.append("Agility path crit-DAMAGE-from-Agi clause not "
                            "modelled (magnitude unmeasured)")
        elif build_spec.path == "Duality":
            # INTENDED: AP = highest of Str or Agi at 100%. Validated when the
            # bonus IS applying: (160 + Str 121) x 1.10 Deadliness = 309 against
            # an observed 307. The impairment layer handles the cycling.
            ap_grant = max(cs.strength, cs.agility) * duality_ap_factor
            cs.attack_power += ap_grant
            imp = impairment_for("Duality")
            if imp and system_state == "as_measured":
                lo, hi = imp["effects"]["ap_grant"]["impaired_factor_range"]
                cs.impairment_range = {
                    "attack_power_low": cs.attack_power - ap_grant * (1.0 - lo),
                    "attack_power_high": cs.attack_power - ap_grant * (1.0 - hi),
                    "unmeasured": "duty_cycle",
                }
                warnings.append(
                    "🛑 as_measured: Duality's AP grant is INTERMITTENT, so this "
                    f"is a RANGE, not a value — attack power is between "
                    f"{cs.impairment_range['attack_power_low']:.0f} and "
                    f"{cs.impairment_range['attack_power_high']:.0f}. The duty "
                    "cycle is UNMEASURED and deliberately not guessed; measure "
                    "it from the bimodality of weapon-damage hits in a Duality "
                    "parse before collapsing this to a point estimate")
        if build_spec.path == "Duality":
            # 🛑 ORDER-DEPENDENT and load-bearing: the documented clause boosts
            # spell power "from GEAR" by 75%, so this must run while
            # cs.spell_power still holds gear SP only — before Lunar Guidance and
            # any other effect SP is added (talents are applied further down).
            # Moving this line changes what it multiplies.
            amp = duality_sp_amp if system_state == "intended" else 1.0
            cs.spell_power *= amp
            cs.spell_power += DUALITY_FLAT_SP_MEASURED
            cs.bonus_healing += DUALITY_FLAT_SP_MEASURED
            if system_state == "intended":
                warnings.append(
                    f"Duality SP: gear spell power x{amp} (INTENDED, per "
                    "Ascension's path documentation) plus a measured flat +19. "
                    "🛑 The amp does NOT currently apply in game — at gear SP "
                    "229 the sheet reads 271 against ~425 intended. Pass "
                    "system_state='as_measured' to model the delivered value")
            else:
                warnings.append(
                    "Duality SP as_measured: amp NOT applied (it is broken in "
                    "game), only the flat +19 — matching the bug report's "
                    "'difference of 19 Spellpower' and our own PoS 250 vs "
                    "PoD 271. ❌ The 1.895x from 2026-08-04 is retracted as a "
                    "Duality property: that is Path of INTELLIGENCE's doubling, "
                    "which persists across a switch and contaminated the test")
            # Cross-crit conversions are REAL and grant RATING (measured 2026-08-05).
            per = DUALITY_STAT_PER_CROSS_CRIT_RATING
            cs.melee_crit_pct += conversions.percent("crit_melee", cs.intellect / per)
            cs.spell_crit_pct += conversions.percent("crit_spell", cs.agility / per)
            warnings.append(
                f"Duality cross-crit conversions applied as RATING at ~{per} "
                "stat per rating point (measured: Int 199 -> +59 melee crit "
                "rating, Agi 28 -> +8 spell crit rating; n=2, approximate)")
        elif build_spec.path == "Intelligence":
            cs.spell_power *= 2.0    # "SP from items and effects DOUBLED"

        # base-game stat->crit (ascension_confirmed measured rates)
        cs.melee_crit_pct += cs.agility / AGI_PER_MELEE_CRIT_PCT
        cs.spell_crit_pct += cs.intellect / INT_PER_SPELL_CRIT_PCT

        n_talents = len(build_spec.talents)
        if n_talents and conn is None:
            warnings.append(
                f"{n_talents} slotted talents contribute NO stats/multipliers — "
                "compute_stats was called without a `conn`, so T4b's talent "
                "model could not run; output underestimates")

    # ----- talents (T4b, session 2c) ---------------------------------------
    if conn is not None and build_spec.talents:
        from ..sim.talents import resolve_talents
        cs.talents = resolve_talents(conn, build_spec.talents)
        warnings.extend(cs.talents.warnings)
        if build_spec.stats_override:
            warnings.append(
                "talents: DAMAGE MULTIPLIERS applied; their crit/AP/SP/haste "
                "contributions deliberately NOT applied, because sheet mode "
                "means those are already in the numbers you supplied. Applying "
                "both would double-count them")
        else:
            cs.attack_power *= 1.0 + cs.talents.scalar("attack_power_pct") / 100.0
            cs.ranged_attack_power *= \
                1.0 + cs.talents.scalar("ranged_attack_power_pct") / 100.0
            cs.melee_haste_pct += cs.talents.scalar("melee_haste_pct")
            for m in cs.talents.modifiers:
                if m.kind == "spell_power_from_stat_pct" and m.value:
                    stat = (m.scope.get("stat") or "").lower()
                    src = getattr(cs, stat, 0.0) if stat else 0.0
                    cs.spell_power += src * m.value / 100.0
                elif m.kind == "healing_from_stat_pct" and m.value:
                    stat = (m.scope.get("stat") or "").lower()
                    cs.bonus_healing += getattr(cs, stat, 0.0) * m.value / 100.0
            # crit talents are school- and table-scoped, so they cannot collapse
            # into the two scalar crit fields without losing that scoping. They
            # are applied per event by the ability model instead.
            warnings.append(
                "talent crit bonuses are school/table-scoped and are applied "
                "PER EVENT by the ability model, not folded into "
                "melee_crit_pct/spell_crit_pct here")

    # ----- weapon clauses apply in both modes ------------------------------
    mults, crit_dmg, haste_m, haste_s, gcd_mod, cost_mod, notes = _weapon_clause(
        build_spec.path, wielding)
    warnings.extend(notes)
    for bucket, m in mults.items():
        cs.damage_multipliers[bucket] = cs.damage_multipliers.get(bucket, 1.0) * m
    cs.ability_crit_damage_bonus += crit_dmg
    cs.melee_haste_pct += haste_m
    cs.spell_haste_pct += haste_s
    cs.gcd_modifier_pct += gcd_mod
    cs.resource_cost_modifier_pct += cost_mod
    if build_spec.path == "Healing" and wielding in ("2h", "dual_2h"):
        cs.spell_crit_pct += 3.0

    # ascension_confirmed (primer §3): Titan's Grip -10% physical is a CARD
    # magnitude, not a path clause — it belongs to talent/ability modelling,
    # so dual_2h wielding warns rather than silently applying it here.
    if wielding == "dual_2h":
        warnings.append(
            "Titan's Grip -10% physical (card magnitude) not applied by "
            "compute_stats — belongs to ability/talent modelling")

    if build_spec.consumables:
        warnings.append(f"{len(build_spec.consumables)} consumables not modelled")
    if build_spec.raid_buffs and content.raid_buffs_available:
        warnings.append(f"{len(build_spec.raid_buffs)} raid buffs not modelled")
    elif build_spec.raid_buffs and not content.raid_buffs_available:
        warnings.append(
            "raid_buffs ignored: content profile has raid_buffs_available=False")

    # ----- system impairments: advisory in BOTH modes -----------------------
    # A build using an impaired system must say so whichever reality it models —
    # in 'intended' mode because the number is optimistic, in 'as_measured' mode
    # because it is a range. The policy flag rides along so the recommendation
    # layer never has to re-derive it.
    imp = impairment_for(build_spec.path)
    if imp:
        cs.impairments.append({"system": f"path:{build_spec.path}", **imp})
        detail = "; ".join(f"{k}: {v.get('note', '')}"
                           for k, v in imp["effects"].items() if v.get("note"))
        warnings.append(
            f"🛑 SYSTEM IMPAIRMENT — Path of {build_spec.path} is currently "
            f"BROKEN in game (detected {imp['detected_on']}, evidence "
            f"{imp['evidence']}). {detail}. Modelled as "
            f"{'INTENDED behaviour, so this output is OPTIMISTIC' if system_state == 'intended' else 'AS MEASURED'}"
            + ("" if imp.get("recommend", True) else
               ". ⛔ POLICY: do NOT recommend this path while the impairment is "
               "open, regardless of how well it sims, and treat its parses as "
               "unusable for absolute calibration")
            + ". When a fix ships, set fixed_on in SYSTEM_IMPAIRMENTS — the "
              "intended model needs no other change")

    cs.warnings = warnings
    return cs
