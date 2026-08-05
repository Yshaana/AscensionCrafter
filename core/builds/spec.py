"""Phase 2 T4 — `BuildSpec`: the one build representation.

Used by the sim, legos, builder UI and guide generator (PHASE_2 T4: "get it
right once"). Ranks are MANDATORY — a build with 3/5 cards is a different
build (wildcard rolls land 1..5 and there is no respec).
"""
from dataclasses import dataclass, field

from ..sim.content import Role

SLOT_BUDGET_ABILITIES = 30    # per-spec slot budget (INDEX_GUIDE inspect format)
SLOT_BUDGET_TALENTS = 25

PATHS = ("Strength", "Agility", "Duality", "Intelligence", "Healing")


@dataclass
class SlottedCard:
    spell_id: int
    rank: int                  # the rank HELD, not the max rank

    def __post_init__(self):
        if not isinstance(self.rank, int) or self.rank < 1:
            raise ValueError(
                f"SlottedCard(spell_id={self.spell_id}): rank is mandatory and "
                f">= 1, got {self.rank!r} — a build with partial ranks is a "
                "different build (PHASE_2 T4)")


@dataclass
class GearItem:
    """One equipped item. `stats` is a flat {stat_name: value} dict — the same
    shape as scouted_gear.stats_json — so crawled gear loads directly. `weapon`
    is None for non-weapons, else {'min':, 'max':, 'speed':, 'hand': '1h'|'2h'}."""
    item_id: int
    name: str
    slot: str
    stats: dict = field(default_factory=dict)
    weapon: dict | None = None


@dataclass
class BuildSpec:
    character_level: int
    role: Role
    path: str
    abilities: list            # list[SlottedCard], up to 30
    talents: list              # list[SlottedCard], up to 25
    gear: dict = field(default_factory=dict)          # slot -> GearItem
    consumables: list = field(default_factory=list)   # spell ids
    raid_buffs: list = field(default_factory=list)    # ignored when content says so
    stats_override: dict | None = None                # sheet stats — see stats.py
    realm: str = "Darkmoon"
    season: str = "S10"
    source: str = "user_designed"    # 'user_designed','crawled','optimizer_generated'
    user_id: str | None = None

    def __post_init__(self):
        if self.path not in PATHS:
            raise ValueError(f"unknown path {self.path!r} — one of {PATHS}")
        if len(self.abilities) > SLOT_BUDGET_ABILITIES:
            raise ValueError(
                f"{len(self.abilities)} abilities exceeds the "
                f"{SLOT_BUDGET_ABILITIES}-slot budget")
        if len(self.talents) > SLOT_BUDGET_TALENTS:
            raise ValueError(
                f"{len(self.talents)} talents exceeds the "
                f"{SLOT_BUDGET_TALENTS}-slot budget")
        for card in list(self.abilities) + list(self.talents):
            if not isinstance(card, SlottedCard):
                raise TypeError(
                    "abilities/talents must be SlottedCard instances "
                    f"(got {card!r}) — ranks are mandatory")

    def wielding(self):
        """'2h' | '1h' | 'dual_2h' | 'dual_1h' | 'unarmed' — for path weapon
        clauses. Titan's Grip double-2H counts as 2H for path clauses and you
        never get both weapon clauses (primer §3, ascension_confirmed)."""
        weapons = [g.weapon for g in self.gear.values()
                   if g.weapon and g.slot in ("main_hand", "off_hand")]
        hands = [w.get("hand") for w in weapons]
        if not hands:
            return "unarmed"
        if len(hands) == 2:
            return "dual_2h" if all(h == "2h" for h in hands) else "dual_1h"
        return "2h" if hands[0] == "2h" else "1h"
