"""Phase 2 T2 (session `2e`) — the buff/aura state model.

Same discipline as `talents.py`: a buff is a named record with a magnitude, a
provenance tier, and an explicit statement of what is NOT known about it.

**Almost everything here is MEASURED, not modelled.** On 2026-08-05 the owner
ran an incremental capture — an AscensionCrafterExport after each buff was added
one at a time — which turns what `PHASE_2D` T2 scoped as a modelling exercise
into arithmetic. The captures are in
`data/source/captures/2026-08-05_elric_2e_poi_baseline/stat_exports_incremental_buffs.txt`.

Two structural results came out of it and both are load-bearing:

1. **Blessing of Kings applies LAST**, multiplicatively, to all five primary
   stats. Everything else is additive underneath it. Order matters: applying
   Kings before a flat stat buff overstates that buff by 10%.
2. **Bonus Healing tracks UNDOUBLED spell power.** Observed 229 / 256 / 342 / 428
   across the chain = `gear 229 + Arcane Brilliance 27 + 86 per weapon imbue`,
   with no Path-of-Intelligence doubling, no Lunar Guidance and no path flat.
   That makes Bonus Healing a **free instrument**: it reads an effect's raw SP
   grant directly, which is how the imbue's +86 was separated from the +172 that
   appears in the Holy spell-power field.

⚠ Provenance. `tier` is this project's usual vocabulary. `ascension_measured`
means measured on this server from a named capture; `retail_hypothesis` means a
retail value we have NOT validated and which therefore warns on use.
"""
from dataclasses import dataclass, field


CAPTURE = ("2026-08-05 incremental buff capture, "
           "data/source/captures/2026-08-05_elric_2e_poi_baseline/")

# 🚨 `3o` Block C — the capture that RETIRED the +88 imbue AP figure.
#
# ⚠ THE TWO CAPTURES DISAGREE ON THE AP HALF AND AGREE EXACTLY ON THE SP HALF,
# and the owner supplied the discriminator: the `2e` +88 was measured with
# BLESSING OF KINGS UP (its steps 4->5 read AP 258->346 with gear identical),
# while this one is UNBUFFED — and 80 x 1.10 = 88 exactly. That unifies it with
# the open question `str_to_ap_1_21_under_buffs` (1.21 = 1.10 x 1.10): one
# mechanism seen twice, not two puzzles.
#
# 🛑 REGISTERED, NOT MODELLED. Nothing in this module multiplies the imbue by a
# second 1.10 under Kings. `Buff.attack_power` is the POST-DEADLINESS OBSERVED
# grant and `apply_buffs` adds it without the Kings multiplier, so the value
# belongs to the unbuffed state this capture measures. Applying an unexplained
# multiplier because it makes a number come out right is fitting; the buffed
# case is a named residual with a stated discriminator (one export pair, Kings
# alone vs unbuffed, predicting +88 vs +80).
CAPTURE_2026_08_08 = (
    "2026-08-08 LBC baseline + imbue test, "
    "data/source/captures/2026-08-08_elric_lbc_baseline_imbue_test/")


@dataclass(frozen=True)
class Buff:
    """One buff. `flat_stats` are added BEFORE any multiplicative buff.

    `raw_spell_power` is the UNDOUBLED grant — the value Bonus Healing reports.
    Path multipliers (Path of Intelligence's x2.0) are applied by
    `core.builds.stats`, not here, so a buff's record never bakes in a path.
    """
    name: str
    flat_stats: dict = field(default_factory=dict)      # 'strength' -> +62
    stat_multiplier: float = 1.0                        # 1.10 = Kings
    raw_spell_power: float = 0.0                        # undoubled, all schools
    raw_spell_power_by_school: dict = field(default_factory=dict)
    attack_power: float = 0.0                           # post-Deadliness observed
    ranged_attack_power: float = 0.0
    stacks_per_weapon: bool = False
    tier: str = "ascension_measured"
    evidence: str = CAPTURE
    notes: str = ""


# --------------------------------------------------------------- the measured set

BLESSING_OF_KINGS = Buff(
    name="Greater Blessing of Kings",
    stat_multiplier=1.10,
    evidence=CAPTURE + " (step 3->4: every one of Str/Agi/Sta/Int/Spi x1.10)",
    notes="Applies LAST, after every flat stat buff. Verified against all five "
          "stats simultaneously: (121+62)x1.10=201.3 obs 201, (28+62)x1.10=99.0 "
          "obs 99, 264x1.10=290.4 obs 290, (259+31)x1.10=319 obs 319, "
          "77x1.10=84.7 obs 84.",
)

ARCANE_BRILLIANCE = Buff(
    name="Arcane Brilliance",
    flat_stats={"intellect": 31.0},
    raw_spell_power=27.0,
    evidence=CAPTURE + " (step 1->2: Int +31, BonusHealing +27)",
    notes="The +27 is the RAW grant, read directly off Bonus Healing. Under "
          "Path of Intelligence it presents as +54 in the spell-power field, "
          "plus a Lunar Guidance knock-on from the +31 Int.",
)

CONSECRATED_WEAPON_IMBUE = Buff(
    name="Consecrated Weapon (imbue)",
    raw_spell_power_by_school={"Holy": 86.0},
    attack_power=80.0,
    ranged_attack_power=80.0,
    stacks_per_weapon=True,
    evidence=CAPTURE_2026_08_08 + " (three-step imbue: AP 141 -> 221 -> 301, "
             "i.e. +80 and +80 on a settled sheet, UNBUFFED)",
    notes="🆕 STACKS ONCE PER WEAPON — under Titan's Grip both weapons carry it "
          "and both grants apply (Holy SP premium 1050-706 = 344 = 2 x 172). "
          "School-scoped, so it separates Holy from general spell power and "
          "silently breaks any accounting that assumes they move together. "
          "⚠ The RAW grant is 86 (Bonus Healing +86 per imbue); the 172 seen in "
          "the Holy field is after Path of Intelligence's x2.0. `2d` recorded "
          "+172 as the raw grant from a DUALITY sheet, which has no doubling — "
          "that reading is FLAGGED FOR RE-CHECK, not carried here.",
)

STRENGTH_OF_EARTH_TOTEM = Buff(
    name="Strength of Earth Totem",
    flat_stats={"strength": 62.0, "agility": 62.0},
    evidence=CAPTURE + " (step 6: Str +68 and Agi +69 observed, i.e. 62 x1.10 Kings)",
    notes="Grants BOTH Strength and Agility. The +62/+62 was previously "
          "unattributable between this and Aspect of the Beast; the incremental "
          "capture assigns all of it here.",
)

ASPECT_OF_THE_BEAST = Buff(
    name="Aspect of the Beast",
    attack_power=14.0,
    evidence=CAPTURE + " (step 0->1: AP 141->155, nothing else moved)",
    notes="+14 Attack Power and nothing else — no ranged AP, no stats. "
          "Measured in isolation.",
)

ELIXIR_OF_AGILITY = Buff(
    name="Elixir of Agility",
    flat_stats={"agility": 15.0},
    evidence=CAPTURE + " (Agi 28->43, AP unchanged at 141)",
    notes="🎯 The capture that proved **Agility grants ZERO Attack Power** on "
          "this build — AP did not move at all. That killed the hypothesis that "
          "the ~1.21 Strength->AP ratio seen under buffs was an Agility term.",
)

SWIFT_RETRIBUTION = Buff(
    name="Swift Retribution",
    tier="retail_hypothesis",
    evidence="observed as an EXTERNAL aura cast by another player ('Virginity') "
             "in 2026-08-05-23.03.10 WoWCombatLog.txt",
    notes="⚠ NOT one of this character's talents — `2d` recorded it as an "
          "unidentified self-buff and it is not. It is a raid aura from a "
          "passing player, which is why it appeared 'always on, even naked'. "
          "Retail value is +3% haste; UNVALIDATED here, and the stat export's "
          "haste percentages are rating-derived only so they never show it. "
          "Haste does not change per-hit damage, so no calibration input is "
          "affected — only swing counts and DPS totals.",
)

MEASURED_BUFFS = {
    "blessing_of_kings": BLESSING_OF_KINGS,
    "arcane_brilliance": ARCANE_BRILLIANCE,
    "consecrated_weapon": CONSECRATED_WEAPON_IMBUE,
    "strength_of_earth_totem": STRENGTH_OF_EARTH_TOTEM,
    "aspect_of_the_beast": ASPECT_OF_THE_BEAST,
    "elixir_of_agility": ELIXIR_OF_AGILITY,
    "swift_retribution": SWIFT_RETRIBUTION,
}

# `raid_buffs_available` on a ContentProfile maps to a concrete set, so a sim
# that says "raid buffed" states exactly which buffs it means.
BUFF_SETS = {
    "none": (),
    "self_only": ("consecrated_weapon",),
    "party": ("blessing_of_kings", "arcane_brilliance", "consecrated_weapon"),
    "raid": ("blessing_of_kings", "arcane_brilliance", "consecrated_weapon",
             "strength_of_earth_totem", "aspect_of_the_beast"),
}


def apply_buffs(base_stats, buff_keys, *, weapons=1, warnings=None):
    """Apply a set of buffs to a primary-stat dict, in the measured ORDER.

    `base_stats` maps 'strength'/'agility'/'stamina'/'intellect'/'spirit' to
    unbuffed values. Returns `(stats, extras)` where `extras` carries the raw
    spell-power and attack-power grants for `compute_stats` to fold in at the
    right point in ITS order (path multipliers must run after the raw SP is
    summed — see `core.builds.stats`).

    🛑 Order is not cosmetic. Flat stat grants are summed first and the
    multiplicative buff applied last, because that is what the capture measured.
    Applying Kings first would overstate every flat buff by 10%.
    """
    warnings = warnings if warnings is not None else []
    stats = dict(base_stats)
    extras = {"raw_spell_power": 0.0, "raw_spell_power_by_school": {},
              "attack_power": 0.0, "ranged_attack_power": 0.0}
    multiplier = 1.0

    for key in buff_keys:
        buff = MEASURED_BUFFS.get(key)
        if buff is None:
            warnings.append(
                f"buff {key!r} is not in MEASURED_BUFFS — it is NOT applied. "
                "Unknown buffs are named, never silently skipped or guessed")
            continue
        if buff.tier != "ascension_measured":
            warnings.append(
                f"{buff.name}: tier={buff.tier} — {buff.notes.splitlines()[0]}")
        for stat, value in buff.flat_stats.items():
            stats[stat] = stats.get(stat, 0.0) + value
        multiplier *= buff.stat_multiplier
        count = weapons if buff.stacks_per_weapon else 1
        extras["raw_spell_power"] += buff.raw_spell_power * count
        for school, value in buff.raw_spell_power_by_school.items():
            extras["raw_spell_power_by_school"][school] = (
                extras["raw_spell_power_by_school"].get(school, 0.0) + value * count)
        extras["attack_power"] += buff.attack_power * count
        extras["ranged_attack_power"] += buff.ranged_attack_power * count

    if multiplier != 1.0:
        for stat in stats:
            stats[stat] *= multiplier
    extras["stat_multiplier"] = multiplier
    return stats, extras
