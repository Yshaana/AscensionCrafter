"""Phase 2 T1 (session `2e`) — the swing layer: auto-attacks, seal riders, and
crit-fed damage-over-time.

Three gaps `2b` named and `2d`/`2e` measured. All three share one property that
the per-cast model structurally cannot express: **their rate is set by the swing
timer or by the build's own crit output, not by how often a button is pressed.**

    auto-attacks   — a damage source with no cast at all
    seal riders    — a proc on melee EVENTS; `2b` scored them per cast, which
                     understates them by roughly the swing count
    Righteous Vengeance — 30% of a CRIT as an 8 s DoT, so its magnitude is a
                     function of the rest of the rotation

Every constant here is either derived from the combat engine or **measured**
from a named capture. Nothing is a retail default: where retail would supply a
number we do not have, the model warns instead (PHASE_2 T1's hard rule).

⚠ Provenance note. This module holds *sim-layer policy*, following the `2b`
owner decision that put uncertainty bands in `core/sim/uncertainty.py` rather
than inventing rows in Phase 1's truth table. A number here is an argued
assumption with its evidence named, not a game fact — game facts belong in
`seed_confirmed.py`.
"""
from dataclasses import dataclass, field

from .combat_engine import (
    white_melee_table, crit_multiplier, armor_dr_fraction,
    armor_after_penetration, GLANCING_DAMAGE_PENALTY,
)


# --------------------------------------------------------------- measured data

# Seal of Command's proc rate, measured across the two `2e` Path-of-Intelligence
# windows (data/source/captures/2026-08-05_elric_2e_poi_baseline/).
#
#                     window A (unbuffed)   window B (buffed)
#   white swings            137                   154
#   melee ability landings  230                   243
#   Seal of Command hits     84                   106
#   hits / swing           0.61                  0.69
#   hits / melee event     0.23                  0.27
#   hits / minute          17.7                  21.1
#
# 🚨 This CORRECTS `2d`'s "Seal of Command riders fire on autos only". That
# reading came from a Lightbound-Cleave-only isolation window, and Lightbound
# Cleave is the one melee ability measured to feed NOTHING (`2d` §4). With a
# full rotation, only ~30% of procs land within 50 ms of a white swing while
# ~51-64% land within 50 ms of a melee ability — so the seal procs from BOTH.
#
# 🛑 The underlying proc MECHANIC is still unknown. A flat per-event chance and a
# PPM proc (which would scale with weapon speed, not event count) both fit two
# windows at one weapon speed. They are separated only by a capture at a
# materially different weapon speed or haste level, which we do not have.
# `SEAL_PROC_PER_MELEE_EVENT` is therefore a MEASURED RATE, not a derived one,
# and every consumer is warned.
SEAL_PROC_PER_MELEE_EVENT = 0.25          # 0.23 (A) / 0.27 (B)
SEAL_PROC_RATE_EVIDENCE = (
    "measured 2026-08-05, captures/2026-08-05_elric_2e_poi_baseline: "
    "84 procs / 367 melee events (unbuffed), 106 / 397 (buffed)"
)

# Righteous Vengeance: "direct critical strikes with spells and abilities make
# your target take 30% additional damage over 8 seconds as Holy damage."
# ascension_confirmed magnitude (build doc §4, four parses); the DBC carries no
# base points at all — effect 0 is aura 3 (periodic damage) at a 2000 ms period
# with the value supplied by the caster, which is exactly why it has zero
# `spell_effect_values` rows and can never be resolved from numeric fields.
RIGHTEOUS_VENGEANCE_SPELL_ID = 61840
RIGHTEOUS_VENGEANCE_FRACTION = 0.30
RIGHTEOUS_VENGEANCE_DURATION = 8.0
RIGHTEOUS_VENGEANCE_PERIOD = 2.0

# The seal selects which judgement spell a Judgement press actually damages
# with, so the pressed card is NOT the damaging spell (`2d` §5, resolving `2b`'s
# "Judgement resolves to no card" gap). Keys are pressed cards; the value is the
# id that appears in the combat log.
JUDGEMENT_BY_SEAL = {
    20375: 20467,      # Seal of Command  -> Judgement of Command
}
JUDGEMENT_PRESS_CARDS = (20271, 53408)     # Judgement of Light / of Wisdom


@dataclass
class SwingOutcome:
    """Expected damage per swing plus the table that produced it."""
    mean: float
    crit_fraction: float
    landed_fraction: float
    table: object
    warnings: list = field(default_factory=list)


def swing_interval(weapon, melee_haste_pct):
    """Seconds between swings. `None` when the weapon or its speed is unknown —
    never defaulted to a plausible 2.0."""
    if not weapon:
        return None
    speed = weapon.get("speed")
    if not speed or speed <= 0:
        return None
    return speed / (1.0 + max(0.0, melee_haste_pct) / 100.0)


def expected_swing(char_state, weapon, target, *, is_offhand=False,
                   attacker_level=None):
    """Expected damage of ONE white swing, through the full white table.

    White swings are the only attacks that can glance, and glancing is a large
    term against a higher-level target — `2e` measured 33.6% and 39.0% of landed
    swings glancing against a level-63 dummy. Modelling autos without it
    overstates them substantially.
    """
    warnings = []
    if not weapon:
        return None
    lo, hi = weapon.get("min"), weapon.get("max")
    if lo is None or hi is None:
        warnings.append(
            "weapon damage range is UNKNOWN — auto-attack damage cannot be "
            "computed and is omitted, not guessed")
        return SwingOutcome(0.0, 0.0, 0.0, None, warnings)

    level = attacker_level if attacker_level is not None else char_state.level
    table = white_melee_table(
        level, char_state.melee_crit_pct, char_state.melee_hit_pct,
        char_state.expertise_points, target,
        dual_wield=bool(char_state.off_hand))
    warnings.extend(table.warnings)
    p = table.probabilities()

    base = (float(lo) + float(hi)) / 2.0
    if is_offhand:
        # retail_hypothesis: off-hand swings deal 50% damage. NOT validated on
        # Ascension. It is flagged rather than silently applied, and the owner's
        # own parses put auto-attacks at ~8-11% of damage, so the exposure is
        # bounded either way.
        base *= 0.5
        warnings.append(
            "off-hand white damage uses the retail 50% penalty "
            "(retail_hypothesis, not validated on Ascension)")

    armor = armor_after_penetration(target.armor, char_state.armor_pen_pct)
    base *= (1.0 - armor_dr_fraction(armor, level))

    crit_mult = crit_multiplier("melee", char_state.ability_crit_damage_bonus)
    # retail_hypothesis: a glancing blow deals ~75% of a normal hit vs a +3
    # target. The CHANCE is now ascension_measured (see combat_engine's
    # GLANCING_CHANCE_VS_BOSS_MEASURED); the DAMAGE PENALTY is not — no capture
    # separates a glancing hit from a normal one in the log.
    glance_mult = 1.0 - GLANCING_DAMAGE_PENALTY
    if p.get("glancing"):
        warnings.append(
            "glancing DAMAGE penalty is a retail_hypothesis 25%; glancing is "
            "~33% of swing attempts vs a +3 target in the 2e captures, so this "
            "term is NOT small. The glancing CHANCE is measured, the penalty "
            "is not — a log that flags glancing per swing would settle it")

    mean = base * (p.get("hit", 0.0)
                   + p.get("crit", 0.0) * crit_mult
                   + p.get("glancing", 0.0) * glance_mult)
    landed = p.get("hit", 0.0) + p.get("crit", 0.0) + p.get("glancing", 0.0)
    return SwingOutcome(mean, p.get("crit", 0.0), landed, table, warnings)


def swing_events(char_state, duration):
    """`(main_hand_swings, off_hand_swings, warnings)` over `duration` seconds.

    Fractional by design — the medium tier averages RNG rather than rolling it,
    so a partial swing is the honest expectation, not a rounding error.
    """
    warnings = []
    mh_int = swing_interval(char_state.main_hand, char_state.melee_haste_pct)
    oh_int = swing_interval(char_state.off_hand, char_state.melee_haste_pct)
    if mh_int is None:
        warnings.append(
            "main-hand weapon speed is UNKNOWN — auto-attacks and seal riders "
            "are NOT modelled for this build")
        return 0.0, 0.0, warnings
    mh = duration / mh_int
    oh = duration / oh_int if oh_int else 0.0
    return mh, oh, warnings


def seal_procs(melee_events, rate=SEAL_PROC_PER_MELEE_EVENT):
    """Expected seal-rider procs from a count of melee events (white swings plus
    landed melee abilities). Deliberately a plain multiply — see the module
    header for why a PPM model is NOT assumed."""
    return max(0.0, melee_events) * rate


def righteous_vengeance_damage(crit_damage_total, fraction=RIGHTEOUS_VENGEANCE_FRACTION):
    """Total Righteous Vengeance damage implied by the rotation's own crit output.

    RV is a *derived* source: it has no magnitude of its own, so it cannot be
    resolved from the DBC and must be computed from what the rest of the build
    crits for. `crit_damage_total` is the summed damage of critical strikes over
    the fight.

    ⚠ It POOLS on refresh rather than clipping (build doc §4, 92-101% uptime
    measured over four parses), so the total is conserved and a per-tick average
    is not meaningful — this returns the total only.
    """
    return max(0.0, crit_damage_total) * fraction


def resolve_judgement_target(pressed_spell_id, active_seal_id):
    """The spell id a Judgement press actually damages with.

    The active SEAL selects the judgement, so the pressed card and the damaging
    spell are different ids. Returns `(spell_id, note)`; `spell_id` is None when
    the seal is unknown — this never falls back to the pressed card, because
    doing so silently attributes the press's (zero) damage to the rotation.
    """
    if pressed_spell_id not in JUDGEMENT_PRESS_CARDS:
        return pressed_spell_id, None
    target = JUDGEMENT_BY_SEAL.get(active_seal_id)
    if target is None:
        return None, (
            f"Judgement ({pressed_spell_id}) was pressed with no known active "
            f"seal (saw {active_seal_id!r}) — the seal SELECTS the judgement "
            "spell, so the damaging id cannot be resolved. Damage omitted "
            "rather than attributed to the pressed card, which deals none")
    return target, (
        f"Judgement press {pressed_spell_id} damages via {target} "
        f"(selected by the active seal {active_seal_id})")
