"""Numeric-field decoding for client Spell.dbc effect slots (session `1x`).

🛑 **This module exists so that a magnitude is never read from a `description`
string.** That is the Titanic Mutilate trap — the description said 115%, the numeric
field said 70%, and the description was stale dead text. Everything here reads
`EffectBasePoints` / `EffectDieSides` / `EffectRealPointsPerLevel` /
`EffectPointsPerCombo` and nothing else. No function in this file takes text.

## The flat-value convention

WoW stores a flat magnitude as `base_points` = *one less than* the minimum roll:

    minimum = base_points + 1
    maximum = base_points + die_sides

Validated against every flat magnitude already on record in this project, each
established independently of the DBC:

| Spell | field | decoded | doc value |
|---|---|---|---|
| Improved Cleave R1/R2/R3 | 39 / 79 / 119 | 40 / 80 / 120 % | +40%/rank (`build_paladin-hammerdin` v9) |
| Avenging Wrath | 19 | 20 % | +20% all damage (v10) |
| Divine Storm | 109 | 110 % | 110% weapon damage (v10) |
| Divine Protection | -51 | -50 % | -50% damage taken (v10) |
| Fel Infused Weapon 2H | 14 | 15 % | +15% Shadowflame (INDEX_GUIDE v6) |

`base_points == -1` with `die_sides <= 1` decodes to 0 and is the DBC's **"no
value" sentinel**, not a real zero — those slots return `None` rather than 0.0, so
a caller can never mistake "unset" for "measured zero" (§2.2's rule against
silently defaulting a NULL to a plausible number).

## 🚨 `EffectBonusCoefficient` is NOT the SP/AP coefficient

Measured in session `1x` across all 15,769 extracted spell records:

* **7,647 of 9,211** non-zero values are exactly `1.0`
* the recurring non-default values are retail's cast-time formula —
  `0.429 = 1.5/3.5`, `0.714 = 2.5/3.5`, `0.214 = 0.75/3.5`, `0.571 = 2.0/3.5`
* calibrated against 98 spells whose own tooltip states an explicit `$SP*x`/`$AP*x`,
  the field agrees with the text in **4 of 98** cases

The field is stock 3.3.5's `EffectBonusMultiplier`: a *multiplier on the
cast-time-derived default coefficient*, whose neutral value is 1.0. Ascension keeps
the real coefficients for its custom spells somewhere the stock DBC layout does not
expose — for its own cards the field is overwhelmingly left at the 1.0 default.

⚠ **Phase 0's "311 blocked spells carry a non-zero `EffectBonusCoefficient` (SP/AP
scaling)" counted correctly and interpreted wrongly.** Of the 343 blocked spells
whose refs carry any coefficient, **270 carry only 1.0**. So this module reports the
field under its real name, `bonus_multiplier`, and **never emits it as an SP or AP
term.** Deriving an SP coefficient from it would fabricate precision at scale.
"""

DEFAULT_BONUS_MULTIPLIER = 1.0

# The DBC's "this slot is unset" marker. Appears as EffectBasePoints alongside
# die_sides 1, which would otherwise decode to a perfectly plausible 0.
NO_VALUE_SENTINEL = -1

MAX_EFFECTS = 3

# Effect ids worth naming, because a caller deciding "is this a damage value or a
# duration" needs them. Deliberately partial — an unnamed id is returned as its
# integer rather than guessed at.
EFFECT_TYPES = {
    0: "none",
    2: "school_damage",
    3: "dummy",
    6: "apply_aura",
    10: "heal",
    31: "weapon_damage_noschool",
    54: "enchant_held_item",     # the weapon-imbue slot (primer §2)
    58: "weapon_damage_plus",
    64: "trigger_spell",
    77: "script_effect",
}

# Field names as they appear in `spell_dbc_raw.effect_json`, so `evidence_ref` can
# cite the actual DBC column a value came from rather than a paraphrase.
FIELD_NAMES = {
    "flat": "EffectBasePoints/EffectDieSides",
    "per_level": "EffectRealPointsPerLevel",
    "per_combo": "EffectPointsPerCombo",
    "bonus_multiplier": "EffectBonusCoefficient",
}


def _slot(effects, key, index, default=0):
    """One effect slot's value, tolerating a short or absent array."""
    values = effects.get(key) or []
    if index < len(values):
        return values[index]
    return default


def flat_range(base_points, die_sides):
    """`(minimum, maximum)` for a flat magnitude, or `None` when the slot is unset.

    `minimum = base_points + 1`, `maximum = base_points + die_sides` — see the
    module docstring for the five independent validations of this convention.
    """
    if base_points is None:
        return None
    if base_points == NO_VALUE_SENTINEL and (die_sides or 0) <= 1:
        return None
    if base_points == 0 and (die_sides or 0) == 0:
        return None
    low = base_points + 1
    high = base_points + die_sides if die_sides else low
    return (float(low), float(max(low, high)))


def is_default_multiplier(value):
    """True when `EffectBonusCoefficient` carries no information.

    Both the unset 0.0 and the neutral 1.0 mean "no coefficient stated here" — see
    the 🚨 section of the module docstring.
    """
    return value is None or value == 0.0 or value == DEFAULT_BONUS_MULTIPLIER


def decode_effect(effects, index):
    """Decode one effect slot of a parsed `effect_json` dict.

    Returns a dict of numeric fields only. `flat_min`/`flat_max`/`per_level`/
    `per_combo`/`bonus_multiplier` are `None` when the slot carries no value, never
    0.0-as-a-guess.
    """
    base_points = _slot(effects, "EffectBasePoints", index)
    die_sides = _slot(effects, "EffectDieSides", index)
    per_level = _slot(effects, "EffectRealPointsPerLevel", index, 0.0)
    per_combo = _slot(effects, "EffectPointsPerCombo", index, 0.0)
    multiplier = _slot(effects, "EffectBonusCoefficient", index, 0.0)
    flat = flat_range(base_points, die_sides)

    return {
        "effect_index": index,
        "effect_type": _slot(effects, "Effect", index),
        "effect_aura": _slot(effects, "EffectAura", index),
        "base_points": base_points,
        "die_sides": die_sides,
        "flat_min": flat[0] if flat else None,
        "flat_max": flat[1] if flat else None,
        "per_level": per_level or None,
        "per_combo": per_combo or None,
        # reported under its real name, never as SP/AP, and only when it is not the
        # 1.0 default that 83% of non-zero values carry
        "bonus_multiplier": None if is_default_multiplier(multiplier) else multiplier,
        "trigger_spell": _slot(effects, "EffectTriggerSpell", index) or None,
        "misc_value": _slot(effects, "EffectMiscValue", index) or None,
        "misc_value_b": _slot(effects, "EffectMiscValueB", index) or None,
        "radius_index": _slot(effects, "EffectRadiusIndex", index) or None,
        "aura_period": _slot(effects, "EffectAuraPeriod", index) or None,
        "chain_targets": _slot(effects, "EffectChainTargets", index) or None,
    }


def decode_effects(effects):
    """All three effect slots. Slots carrying nothing usable are omitted."""
    return [d for d in (decode_effect(effects, i) for i in range(MAX_EFFECTS))
            if has_usable_value(d)]


def has_usable_value(decoded):
    """Does this slot carry a magnitude worth storing?

    An empty slot (`Effect == 0` with every numeric field unset) is dropped rather
    than stored as a row of NULLs — the table is meant to answer "what is this
    spell's magnitude", and 30,000 empty rows make that query slower and no truer.
    """
    if decoded["effect_type"] == 0 and decoded["effect_aura"] == 0:
        return False
    return any(decoded[k] is not None for k in
               ("flat_min", "per_level", "per_combo", "bonus_multiplier",
                "trigger_spell", "misc_value"))


def effect_type_name(effect_type):
    """A readable name when we have one, else the raw id as a string."""
    return EFFECT_TYPES.get(effect_type, str(effect_type))


def evidence_ref(source_spell_id, effect_index, archive=None):
    """Provenance string for a decoded value (§2.1: evidence must point at evidence)."""
    base = f"dbc:Spell.dbc:{source_spell_id}:effect{effect_index}"
    return f"{base}@{archive}" if archive else base


def summarise(decoded):
    """One-line human summary of a decoded slot. Used by reports, not stored."""
    parts = [effect_type_name(decoded["effect_type"])]
    if decoded["flat_min"] is not None:
        if decoded["flat_max"] != decoded["flat_min"]:
            parts.append(f"{decoded['flat_min']:g}-{decoded['flat_max']:g}")
        else:
            parts.append(f"{decoded['flat_min']:g}")
    if decoded["per_level"]:
        parts.append(f"+{decoded['per_level']:g}/level")
    if decoded["per_combo"]:
        parts.append(f"+{decoded['per_combo']:g}/combo point")
    if decoded["bonus_multiplier"]:
        parts.append(f"bonus_multiplier={decoded['bonus_multiplier']:g}")
    return " ".join(parts)
