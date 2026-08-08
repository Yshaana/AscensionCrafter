"""Phase 2 T2 — content profiles, roles, metrics, SimResult.

Scenario = content profile x target count x role (ARCHITECTURE §2.9). This is
what replaces the flat patchwork/cleave/aoe triple: solo at 3 targets and a
mythic dungeon at 3 targets differ in raid buffs, self-sustain, fight length
and incoming damage, and a DPS-only sim silently steers solo players wrong
(PHASE_2 T2).

Preset provenance: every preset carries a `provenance` string. Where a number
comes from real crawled data it says so; where it is an assumption it says
that instead — same no-fabricated-precision discipline as everywhere else.
"""
from dataclasses import dataclass, field, replace
from enum import Enum

from .combat_engine import TargetProfile


class Role(Enum):
    DPS = "dps"
    TANK = "tank"
    HEALER = "healer"
    HYBRID = "hybrid"


class Metric(Enum):
    DAMAGE_DONE = "damage_done"
    HEALING_DONE = "healing_done"
    ABSORB_DONE = "absorb_done"
    DAMAGE_TAKEN = "damage_taken"
    EFFECTIVE_HP = "effective_hp"
    SURVIVAL_TIME = "survival_time"
    THROUGHPUT_PER_MANA = "throughput_per_mana"
    THREAT = "threat"


PRIMARY_METRIC_BY_ROLE = {
    Role.DPS: Metric.DAMAGE_DONE,
    Role.TANK: Metric.EFFECTIVE_HP,
    Role.HEALER: Metric.HEALING_DONE,
    Role.HYBRID: Metric.DAMAGE_DONE,
}


@dataclass
class ContentProfile:
    name: str
    content_type: str            # 'raid','world_boss','dungeon_normal','dungeon_mythic','solo','pvp'
    difficulty: str | None
    target: TargetProfile
    fight_duration: float        # seconds
    raid_buffs_available: bool
    self_sustain_required: bool
    incoming_damage_dps: float
    movement_pct: float
    provenance: str = "unstated"

    def with_targets(self, count):
        """Same profile at a different target count (§2.9: target count is an
        independent axis)."""
        return replace(self, target=replace(self.target, count=count))


@dataclass
class SimResult:
    """Every computable metric, always — a pure DPS build still reports
    self-healing and damage taken, which is what makes solo evaluation possible
    without a separate code path (PHASE_2 T2)."""
    metrics: dict                    # Metric -> float
    primary_metric: Metric
    role: Role
    content: ContentProfile
    per_ability: dict = field(default_factory=dict)   # spell_id -> breakdown dict
    warnings: list = field(default_factory=list)
    # Combat-RNG spread, set by slow_sim only. Deliberately a SEPARATE field
    # from anything uncertainty.py produces: combat variance and knowledge
    # uncertainty are different quantities and must never share one error bar
    # (PHASE_2 T6).
    combat_rng: dict | None = None

    @property
    def primary_value(self):
        return self.metrics.get(self.primary_metric)


# --------------------------------------------------------------------- presets

# Target model notes:
# * Raid bosses on this realm's current content (Zul'Gurub) are treated as +3
#   (level 63) — the project's own hit-cap language is anchored to "+3 raid
#   boss" (primer §1, build doc §10). ascension_confirmed as the convention;
#   individual boss levels unverified per-boss.
# * armor 3731 / dodge 6.5 / parry 14.0 / block 5.0 for a +3 boss are
#   retail_hypothesis values (3.3.5 boss defaults, SimC enemy defaults) — NOT
#   yet validated on Ascension. The enemy-avoidance API endpoint
#   (character_damage_taken_abilities, participantType=enemies) can validate
#   dodge/parry per boss when calibration (T8) needs it.
# * Dungeon mobs modelled +2 (elevated) per the primer's ~6% spell-miss figure.

_BOSS_63 = TargetProfile(level=63, armor=3731, dodge_pct=6.5, parry_pct=14.0,
                         block_pct=5.0)
_ELITE_62 = TargetProfile(level=62, armor=3300, dodge_pct=5.0, parry_pct=12.0,
                          block_pct=5.0)
_MOB_60 = TargetProfile(level=60, armor=2800, dodge_pct=5.0, parry_pct=5.0,
                        block_pct=5.0)

# Fight durations (3l C2, prereg predictions/prereg_3l_c2.md): the three
# gate-feeding presets are MEASURED from the corpus — scope-joined encounters
# only, because those are exactly the fights the calibration gate's
# boss_single scopes cite (CONTENT_PRESET in calibrate_crawled.py). Median,
# not mean: both distributions are right-skewed. The remaining presets have
# no corpus measurement (no gate scope maps to them; dungeon_mythic has zero
# corpus rows; trash bundles carry no encounter durations) and keep their
# `assumption:` strings — fabricating a measurement would be worse.
_DURATION_QUERY = ("SELECT e.content_type, e.duration_seconds FROM "
                   "capture_scopes cs JOIN encounters e ON e.encounter_id = "
                   "cs.encounter_id WHERE e.duration_seconds IS NOT NULL")
_RAID_PROVENANCE = ("fight_duration measured: median 78.1s over n=33 "
                    f"scope-joined raid encounters ({_DURATION_QUERY} AND "
                    "content_type='raid'), builds.db @ f7b14af 2026-08-08; "
                    "IQR 49.3-112.1. Supersedes the scouted fastest-kill x1.5 "
                    "estimate (75.0). Target stats retail_hypothesis")
_DUNGEON_PROVENANCE = ("fight_duration measured: median 39.9s over n=566 "
                       f"scope-joined dungeon_normal encounters "
                       f"({_DURATION_QUERY} AND content_type="
                       "'dungeon_normal'), builds.db @ f7b14af 2026-08-08; "
                       "IQR 26.0-59.9. dungeon_mythic itself is unobserved in "
                       "the corpus — this preset serves both, and the measured "
                       "side is dungeon_normal. Target stats: assumption "
                       "(+2 elevated boss, partial group buffs)")

PRESETS = {
    "raid_boss_st": ContentProfile(
        name="raid_boss_st", content_type="raid", difficulty=None,
        target=_BOSS_63, fight_duration=78.1,
        raid_buffs_available=True, self_sustain_required=False,
        incoming_damage_dps=0.0, movement_pct=0.10,
        provenance=_RAID_PROVENANCE),
    "raid_boss_cleave": ContentProfile(
        name="raid_boss_cleave", content_type="raid", difficulty=None,
        target=replace(_BOSS_63, count=3), fight_duration=78.1,
        raid_buffs_available=True, self_sustain_required=False,
        incoming_damage_dps=0.0, movement_pct=0.10,
        provenance=_RAID_PROVENANCE),
    "raid_aoe": ContentProfile(
        name="raid_aoe", content_type="raid", difficulty=None,
        target=replace(_ELITE_62, count=12), fight_duration=40.0,
        raid_buffs_available=True, self_sustain_required=False,
        incoming_damage_dps=0.0, movement_pct=0.15,
        provenance="assumption: 10-15 adds, medium burst window"),
    "mythic_dungeon_st": ContentProfile(
        name="mythic_dungeon_st", content_type="dungeon_mythic", difficulty="mythic",
        target=_ELITE_62, fight_duration=39.9,
        raid_buffs_available=False, self_sustain_required=False,
        incoming_damage_dps=150.0, movement_pct=0.10,
        provenance=_DUNGEON_PROVENANCE),
    "mythic_dungeon_aoe": ContentProfile(
        name="mythic_dungeon_aoe", content_type="dungeon_mythic", difficulty="mythic",
        target=replace(_MOB_60, level=61, count=6), fight_duration=20.0,
        raid_buffs_available=False, self_sustain_required=True,
        incoming_damage_dps=300.0, movement_pct=0.15,
        provenance="assumption: 5-8 pack pulls, short bursts, some self-sustain"),
    "dungeon_normal_aoe": ContentProfile(
        name="dungeon_normal_aoe", content_type="dungeon_normal", difficulty="normal",
        target=replace(_MOB_60, count=6), fight_duration=15.0,
        raid_buffs_available=False, self_sustain_required=False,
        incoming_damage_dps=100.0, movement_pct=0.10,
        provenance="assumption: trash packs, partial buffs"),
    "world_boss": ContentProfile(
        name="world_boss", content_type="world_boss", difficulty=None,
        target=_BOSS_63, fight_duration=300.0,
        raid_buffs_available=True, self_sustain_required=False,
        incoming_damage_dps=250.0, movement_pct=0.20,
        provenance="assumption: very long, variable buffs, high incoming damage"),
    "solo_grind": ContentProfile(
        name="solo_grind", content_type="solo", difficulty=None,
        target=replace(_MOB_60, count=2, level=60), fight_duration=12.0,
        raid_buffs_available=False, self_sustain_required=True,
        incoming_damage_dps=200.0, movement_pct=0.05,
        provenance="assumption: 1-3 mobs, no raid buffs, you are your own healer"),
}


def get_preset(name):
    if name not in PRESETS:
        raise KeyError(
            f"unknown content preset {name!r} — available: {sorted(PRESETS)}")
    return PRESETS[name]
