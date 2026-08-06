"""Phase 2 T5 — the action priority list and its condition grammar.

An APL is a structured JSON priority list with a SMALL ENUMERATED condition
grammar (PHASE_2 T5). Deliberately not an expression language: the grammar is
the thing the medium sim can reason about, and an open-ended one would turn
"is this rotation castable?" back into "run it and see".

🛑 **An APL never branches on target count or content type.** A build's AoE
rotation is a *different APL passed for that content profile*, not a conditional
inside one APL. That keeps every comparison explicit — if two content profiles
produce different results it is because the sim ran different rotations, and
the caller had to say so.
"""
import json
from dataclasses import dataclass, field

# The whole grammar. Anything not here is a hard error, not a silent skip —
# a mistyped condition that quietly evaluates True would invent a rotation.
CONDITION_TYPES = {
    "always",                 # {}
    "cooldown_ready",         # {} — this entry's own spell
    "other_cooldown_ready",   # {'spell_id': int}
    "other_cooldown_not_ready",  # {'spell_id': int} — "only while X is down"
    "buff_active",            # {'spell_id': int}   — on the PLAYER
    "buff_missing",           # {'spell_id': int}   — on the PLAYER
    # 3e B2 (ENGINE_BUGS E4) — the target side. `buff_active`/`buff_missing`
    # track the player's own auras, so before these existed a DoT could only
    # ever be given `always`, and "re-cast it when it is about to expire" was
    # not expressible in the grammar at all. A DoT caster's defining decision
    # had no way to be written down.
    "debuff_missing",         # {'spell_id': int}   — on the TARGET
    "debuff_active",          # {'spell_id': int}   — on the TARGET
    "debuff_remaining_below",  # {'spell_id': int, 'value': seconds} — pandemic
                               # refresh: re-apply just before it drops
    "resource_at_least",      # {'resource': 'mana'|'rage'|'energy'|..., 'value': n}
    "resource_pct_at_least",  # {'resource': str, 'value': 0-100}
    "combo_points_at_least",  # {'value': n}
    "health_pct_below",       # {'value': 0-100} — self-sustain gating
    "target_health_pct_below",  # {'value': 0-100} — execute windows
    "time_remaining_below",   # {'value': seconds}
}

# Conditions a caller might reach for that are REFUSED by design, with the
# reason, so the error explains the rule instead of just rejecting a name.
_REFUSED = {
    "target_count_at_least": (
        "an APL must not branch on target count — pass a different APL for the "
        "AoE content profile so the comparison stays explicit (PHASE_2 T5)"),
    "content_type_is": (
        "an APL must not branch on content type — same rule as target count"),
}


# 3e B4 — the combo-point cap lives here, in the layer BOTH `apl_gen` (which
# writes the gate) and `tiers` (which spends against it) already depend on.
# It was defined in `apl_gen` alone, and `tiers` cannot import that module —
# `apl_gen` imports `tiers`, so the arrow only points one way.
MAX_COMBO_POINTS = 5


class APLError(Exception):
    """A malformed APL. Raised, never worked around: a silently-dropped entry
    changes the rotation being simulated without saying so."""


@dataclass
class APLEntry:
    spell_id: int
    conditions: list = field(default_factory=list)
    off_gcd: bool = False       # queued alongside a GCD action (Lightbound Cleave)
    comment: str = ""

    def __post_init__(self):
        for c in self.conditions:
            t = c.get("type")
            if t in _REFUSED:
                raise APLError(f"condition {t!r} is refused: {_REFUSED[t]}")
            if t not in CONDITION_TYPES:
                raise APLError(
                    f"unknown condition type {t!r} on spell {self.spell_id} — "
                    f"the grammar is closed; known types: {sorted(CONDITION_TYPES)}")


@dataclass
class APL:
    name: str
    entries: list = field(default_factory=list)
    provenance: str = "unstated"

    def to_json(self):
        return json.dumps({
            "name": self.name, "provenance": self.provenance,
            "entries": [{"spell_id": e.spell_id, "conditions": e.conditions,
                         "off_gcd": e.off_gcd, "comment": e.comment}
                        for e in self.entries]}, indent=2)

    @classmethod
    def from_json(cls, text):
        d = json.loads(text)
        return cls(name=d["name"], provenance=d.get("provenance", "unstated"),
                   entries=[APLEntry(**e) for e in d["entries"]])

    def spell_ids(self):
        return [e.spell_id for e in self.entries]


# --------------------------------------------------------------- evaluation

def evaluate(condition, state):
    """Evaluate one condition against a `TimelineState`. Unknown types raise —
    `APLEntry` already validates, so reaching here means the grammar and the
    evaluator disagree, which is a bug worth surfacing loudly."""
    t = condition["type"]
    if t == "always":
        return True
    if t == "cooldown_ready":
        return state.cooldown_ready(condition["_spell_id"])
    if t == "other_cooldown_ready":
        return state.cooldown_ready(condition["spell_id"])
    if t == "other_cooldown_not_ready":
        # Exists for the "engine poison" case: Blades of Light is a legitimate
        # filler ONLY while Hour of Judgement is down, because its channel
        # suppresses the Paladin-tagged abilities that bring HoJ back
        # (build_paladin-hammerdin.md §2, §11).
        return not state.cooldown_ready(condition["spell_id"])
    if t == "buff_active":
        return state.buff_active(condition["spell_id"])
    if t == "buff_missing":
        return not state.buff_active(condition["spell_id"])
    # 3e B2 — the target's debuffs are a SEPARATE dict from the player's buffs.
    # Conflating them is the bug this fixes: `medium_sim` used to record every
    # duration-carrying ability in `st.buffs`, so a DoT on the boss and a seal on
    # yourself were the same object.
    if t == "debuff_active":
        return state.debuff_active(condition["spell_id"])
    if t == "debuff_missing":
        return not state.debuff_active(condition["spell_id"])
    if t == "debuff_remaining_below":
        return state.debuff_remaining(condition["spell_id"]) < condition["value"]
    if t == "resource_at_least":
        return state.resource(condition["resource"]) >= condition["value"]
    if t == "resource_pct_at_least":
        return state.resource_pct(condition["resource"]) >= condition["value"]
    if t == "combo_points_at_least":
        return state.combo_points >= condition["value"]
    if t == "health_pct_below":
        return state.self_health_pct < condition["value"]
    if t == "target_health_pct_below":
        return state.target_health_pct < condition["value"]
    if t == "time_remaining_below":
        return state.time_remaining() < condition["value"]
    raise APLError(f"evaluator has no branch for condition type {t!r}")


def entry_ready(entry: APLEntry, state):
    """All of an entry's conditions, plus its own cooldown, which is implicit —
    an APL that had to spell out 'cooldown_ready' on every line would make the
    common case noisy and the omission easy to miss."""
    if not state.cooldown_ready(entry.spell_id):
        return False
    for c in entry.conditions:
        c = dict(c)
        c["_spell_id"] = entry.spell_id
        if not evaluate(c, state):
            return False
    return True
