"""Phase 2 T4b (session 2c) — what a build's talents actually do.

Through 2b, talents contributed **nothing** to the sim, on a build whose whole
identity is a stacked multiplier chain. That was the single largest error source
by a wide margin. This module closes it.

## Read modifiers from numeric fields, never from the tooltip

The rule this is built on comes from the Improved Cleave case (2b): its tooltip
says *"increases the bonus damage done by your Cleave ability"* — naming one
term — while its `EffectMiscValue` is **8 = `SPELLMOD_ALL_EFFECTS`**, so it
multiplies *every* effect of the spells in its class mask. Reading the tooltip
gave +74 per hit; reading the modifier op gave +563. The project already banned
reading a *magnitude* from tooltip prose; that case extended the ban to **scope**.

So everything here decodes `EffectAura` + `EffectMiscValue` + `EffectBasePoints`
+ `EffectSpellClassMask`, and nothing here reads a description string.

⚠ `EffectSpellClassMask` had to be added to the extract in 2c — it was parsed by
`build_dbc_index.py` and never written out, which is why no earlier session could
have done this.

## Card rank is not level rank

A talent card's rank is its ROLL (1–5), not a level gate, so the level-gated
`dbc_spell_rank` path used for abilities is the wrong one. The card rank maps to
a spell id through `dbc_character_advancement.spell_rank_<n>`, which is exact.
Getting this wrong reads Rank 1 for a 5/5 card — the catalog's standing trap.

## 🛑 Unknown auras are NAMED, never assumed inert

`AURA_SEMANTICS` holds only auras whose reading can be justified. Anything else
produces an `unmodelled` modifier carrying the aura id, and the build's warnings
say which talent and which aura. A talent that silently contributes 1.0x is
indistinguishable from a talent that was read correctly and does nothing — and
this project has been burned by exactly that shape often enough to refuse it.
Ascension also ships auras beyond stock 3.3.5's range (333 appears on Sword
Specialization and Accuracy), so "unknown" here is common and expected.
"""
from dataclasses import dataclass, field

# --- school mask -> school names (stock SpellSchoolMask) -----------------------
SCHOOL_BITS = {
    1: "Physical", 2: "Holy", 4: "Fire", 8: "Nature",
    16: "Frost", 32: "Shadow", 64: "Arcane",
}
ALL_SCHOOLS_MASK = 127

# Ascension's hybrid schools are combinations of the stock bits, and the primer's
# double-dip rule says an amplifier for either component reaches the hybrid. So a
# mask is expanded to its BITS and matched bitwise, never by school name.
HYBRID_MASKS = {
    "Holystrike": 1 | 2, "Holyfire": 2 | 4, "Shadowflame": 32 | 4,
    "Firestrike": 1 | 4, "Froststrike": 1 | 16, "Shadowstrike": 1 | 32,
    "Spellstrike": 1 | 64, "Stormstrike": 1 | 8,
}


def school_to_mask(school):
    """The bitmask for a school name, hybrids included. 0 when unknown."""
    if not school:
        return 0
    if school in HYBRID_MASKS:
        return HYBRID_MASKS[school]
    for bit, name in SCHOOL_BITS.items():
        if name == school:
            return bit
    return 0


# --- aura semantics -----------------------------------------------------------
# (kind, how to read EffectMiscValue). Only auras with a defensible reading are
# here; see the module docstring on why the rest are named rather than assumed.
#
# Each entry cites what pins it. "retail 3.3.5" means the stock aura id, which is
# safe for auras Ascension inherited unchanged; where a talent's own known
# behaviour confirms the reading, that is named too, because an inherited id is a
# hypothesis on a server this heavily modified.
AURA_SEMANTICS = {
    # +% damage done, scoped by school mask. Answered Prayers (misc 127 = all
    # schools) and Twin Disciplines (misc 2 = Holy) both use it, matching their
    # documented all-damage% / Holy% behaviour.
    79: ("damage_pct_school", "school_mask"),
    # flat +damage done by school. Same scoping.
    13: ("damage_flat_school", "school_mask"),
    # +% crit CHANCE by school. Confirmed by Holy Power and Holy Specialization,
    # which retail defines as "+5% critical chance with Holy spells" at 5/5 and
    # whose rank-5 records read basepoints 4 -> 5%.
    # 🚨 Worth stating loudly because the build doc calls these part of a "Holy
    # multiplier stack": they are CRIT talents, not damage multipliers.
    71: ("crit_pct_school", "school_mask"),
    52: ("crit_pct_melee", None),
    57: ("crit_pct_spell", None),
    # +% crit DAMAGE bonus (Holy Focus).
    163: ("crit_damage_pct_school", "school_mask"),
    166: ("attack_power_pct", None),
    167: ("ranged_attack_power_pct", None),
    # MiscValue is the SCHOOL mask and MiscValueB is the stat — reading MiscValue
    # as the stat gives "stat 127", which is not a stat.
    174: ("spell_power_from_stat_pct", "school_mask_stat_b"),   # Lunar Guidance
    175: ("healing_from_stat_pct", "school_mask_stat_b"),       # Nurturing Instinct
    138: ("melee_haste_pct", None),                  # Flurry
    # SpellMod: the op lives in EffectMiscValue, the target set in the class mask.
    107: ("spellmod_flat", "spellmod_op"),
    108: ("spellmod_pct", "spellmod_op"),
}

# Auras whose meaning IS established but which deliberately do not produce a
# damage modifier here. Keeping them separate from the genuinely-unknown set
# matters: "we know what this is and it is handled elsewhere" and "we have no
# idea what this does" are different states, and collapsing them would make the
# warning list unreadable and hide the real gaps.
AURA_KNOWN_NOT_A_MODIFIER = {
    42: ("proc_trigger", "SPELL_AURA_PROC_TRIGGER_SPELL — a trigger, not a "
                         "multiplier. The chain it fires is the relationship "
                         "graph's (spell_relationships.triggers), and its damage "
                         "already reaches the sim as an attributed component"),
    4: ("server_script", "SPELL_AURA_DUMMY — the behaviour lives in a server-side "
                         "script, so no numeric field states it. Only a live "
                         "tooltip or a parse can pin these"),
}

# SpellModOp values that change DAMAGE. Everything else (cooldown, cost,
# duration, range, ...) is decoded and carried, but never multiplied into a
# damage number — a cooldown modifier applied as damage is the exact silent
# error this project keeps finding.
SPELLMOD_DAMAGE_OPS = {
    0: "SPELLMOD_DAMAGE",
    8: "SPELLMOD_ALL_EFFECTS",     # the Improved Cleave case
}

# 🚨 `3m` Block B (2026-08-08) — MODIFIERS THAT REACH THE BONUS TERM ONLY.
#
# Ascension's 2026-08-07 changelog, live Monday 10 August:
#     "Fixed a bug where Improved Cleave increased hybrid Cleaves weapon damage,
#      rather than only their bonus damage. Regular Cleave was unaffected."
#
# `2b`/`2c` read `EffectMiscValue = 8 = SPELLMOD_ALL_EFFECTS` over the tooltip's
# "increases the BONUS damage done by your Cleave ability" — correctly, per this
# project's own standing rule that a numeric field outranks tooltip prose. The
# server has now declared the tooltip to be the INTENT and `ALL_EFFECTS` to be
# the broken DELIVERY. Same shape as `2d`'s Path of Duality lesson, fired in the
# opposite direction: there the prose was aspirational and the delivery was
# broken; here the numeric field was the bug and the prose was right.
#
# Owner decision 2026-08-08: **model INTENDED.** So `0.65·W + 2.2·(9+AP)`
# replaces `2.2·(0.65·W + 9+AP)`, and the removed term is `1.2 × 0.65 × W` — a
# pure weapon term, so the nerf scales with weapon damage.
#
# 🛑 SCOPED TO IMPROVED CLEAVE BY CARD ID, NOT GENERALISED TO op 8. The evidence
# is one changelog line about one card. `SPELLMOD_ALL_EFFECTS` means all effects
# in the engine, and a weapon-percent effect IS an effect — so treating every op
# 8 modifier as bonus-only would be inventing a general rule from a specific
# statement, which is the same over-reach `2d` had to walk back. If another card
# is later declared the same way, add its id here with its own changelog line.
#
# Ranks 1/2/3 = 12329 / 12950 / 20496 (`seed_confirmed.py`
# improved_cleave_true_magnitude, +40%/+80%/+120%).
BONUS_TERM_ONLY_TALENT_IDS = {12329, 12950, 20496}
BONUS_TERM_ONLY_EVIDENCE = (
    "Ascension changelog 2026-08-07T21:32:22 [Darkmoon][Dawnrise], live "
    "2026-08-10: 'Fixed a bug where Improved Cleave increased hybrid Cleaves "
    "weapon damage, rather than only their bonus damage.'")
SPELLMOD_OP_NAMES = {
    0: "DAMAGE", 1: "DURATION", 2: "THREAT", 3: "EFFECT1", 4: "CHARGES",
    5: "RANGE", 6: "RADIUS", 7: "CRITICAL_CHANCE", 8: "ALL_EFFECTS",
    9: "NOT_LOSE_CASTING_TIME", 10: "CASTING_TIME", 11: "COOLDOWN",
    12: "EFFECT2", 14: "COST", 15: "CRIT_DAMAGE_BONUS", 21: "GLOBAL_COOLDOWN",
    22: "DOT", 23: "EFFECT3",
}


@dataclass
class TalentModifier:
    """One decoded effect slot of one slotted talent."""
    talent_spell_id: int
    talent_name: str
    card_rank: int
    resolved_spell_id: int
    effect_index: int
    kind: str
    value: float | None
    scope: dict = field(default_factory=dict)
    evidence_ref: str = ""
    note: str = ""


@dataclass
class TalentEffects:
    """Everything a build's talents do, aggregated and queryable."""
    modifiers: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    # 2e T10 (D3): talent_spell_id -> (bucket_id, bucket_name) for slotted
    # talents that share a "does not stack / only the highest applies" bucket.
    # Populated by resolve_talents from `exclusivity_buckets`.
    buckets: dict = field(default_factory=dict)

    # --- damage ---------------------------------------------------------------
    def damage_multiplier(self, school, spell_family=None, class_mask=None,
                          component="all"):
        """Multiplicative damage factor for one ability, and what produced it.

        Returns `(factor, [applied_names])`.

        🆕 `3m` B — `component` selects which half of the ability's base the
        factor is for: `"all"` (every modifier — the behaviour every caller had
        before, and still correct for any ability with no weapon term),
        `"weapon"` (the weapon-percent components) or `"bonus"` (flats and
        stat coefficients). Only modifiers in `BONUS_TERM_ONLY_TALENT_IDS`
        distinguish the two; everything else applies to both, so for the vast
        majority of abilities `weapon` and `bonus` return the same number as
        `all` and the split costs nothing.

        🛑 Calling this with `component="all"` on an ability that HAS a weapon
        term and a bonus-only modifier silently restores the pre-fix behaviour.
        `_damage_buckets` is the only production caller and asks for the split.

        2e T10 (D3): exclusivity buckets are scored **as the game scores them**
        — when several applicable modifiers share a bucket, only the HIGHEST
        member enters the math; the suppressed members are named in the applied
        list so a board carrying dead bucket-mates reads as such rather than as
        extra damage. Conflicts are allowed and warned, never rejected (the
        analysis path must be able to model someone else's conflicted board).
        """
        mask = school_to_mask(school)
        factor, applied = 1.0, []
        candidates = []          # (modifier, pct_value, label)
        for m in self.modifiers:
            if m.value is None:
                continue
            # 3m B — a bonus-only modifier does not reach the weapon component.
            if (component == "weapon"
                    and m.talent_spell_id in BONUS_TERM_ONLY_TALENT_IDS):
                continue
            if m.kind == "damage_pct_school":
                if mask and (m.scope.get("school_mask", 0) & mask):
                    candidates.append((m, m.value, f"{m.talent_name} +{m.value:g}%"))
            elif m.kind == "spellmod_pct" and m.scope.get("op") in SPELLMOD_DAMAGE_OPS:
                if _mask_hits(m.scope.get("class_mask"), class_mask,
                              m.scope.get("family"), spell_family):
                    candidates.append((
                        m, m.value,
                        f"{m.talent_name} +{m.value:g}% "
                        f"({SPELLMOD_OP_NAMES.get(m.scope['op'], m.scope['op'])})"))

        best_in_bucket = {}      # bucket_id -> highest pct among applicable members
        for m, value, _ in candidates:
            b = self.buckets.get(m.talent_spell_id)
            if b and value > best_in_bucket.get(b[0], float("-inf")):
                best_in_bucket[b[0]] = value

        for m, value, label in candidates:
            b = self.buckets.get(m.talent_spell_id)
            if b and value < best_in_bucket.get(b[0], value):
                applied.append(
                    f"[bucket-suppressed] {label} — {b[1]}: only the highest "
                    "member applies")
                continue
            factor *= 1.0 + value / 100.0
            applied.append(label)
        return factor, applied

    def flat_damage_bonus(self, school, spell_family=None, class_mask=None):
        total, applied = 0.0, []
        mask = school_to_mask(school)
        for m in self.modifiers:
            if m.value is None:
                continue
            if m.kind == "damage_flat_school" and mask and (
                    m.scope.get("school_mask", 0) & mask):
                total += m.value
                applied.append(f"{m.talent_name} +{m.value:g}")
            elif m.kind == "spellmod_flat" and m.scope.get("op") in SPELLMOD_DAMAGE_OPS:
                if _mask_hits(m.scope.get("class_mask"), class_mask,
                              m.scope.get("family"), spell_family):
                    total += m.value
                    applied.append(f"{m.talent_name} +{m.value:g} flat")
        return total, applied

    # --- stats ----------------------------------------------------------------
    def crit_bonus(self, school, table):
        """Additive crit-chance points from talents, for one school and table."""
        mask = school_to_mask(school)
        total = 0.0
        for m in self.modifiers:
            if m.value is None:
                continue
            if m.kind == "crit_pct_school" and mask and (
                    m.scope.get("school_mask", 0) & mask):
                total += m.value
            elif m.kind == "crit_pct_melee" and table == "melee":
                total += m.value
            elif m.kind == "crit_pct_spell" and table == "spell":
                total += m.value
        return total

    def crit_damage_bonus(self, school):
        mask = school_to_mask(school)
        return sum(m.value for m in self.modifiers
                   if m.kind == "crit_damage_pct_school" and m.value is not None
                   and mask and (m.scope.get("school_mask", 0) & mask))

    def scalar(self, kind):
        return sum(m.value for m in self.modifiers
                   if m.kind == kind and m.value is not None)

    def unmodelled(self):
        return [m for m in self.modifiers if m.kind.startswith("unmodelled")]


def _mask_hits(mod_mask, target_mask, mod_family, target_family):
    """Does a SpellMod's class mask cover the target spell?

    Both sides are three u32s. A hit is any shared bit, and the families must
    match — a class mask is only meaningful inside its `SpellClassSet`, so
    comparing masks across families would produce confident nonsense.
    """
    if not mod_mask or not target_mask:
        return False
    if mod_family is not None and target_family is not None \
            and mod_family != target_family:
        return False
    return any((a or 0) & (b or 0) for a, b in zip(mod_mask, target_mask))


# --- extraction ----------------------------------------------------------------

def resolve_card_rank(conn, catalog_spell_id, card_rank):
    """Spell id for a talent CARD at a given roll rank, or `(None, reason)`.

    🛑 Card rank is a ROLL, not a level gate — `dbc_spell_rank`'s level rule is
    for abilities and is the wrong lookup here.
    """
    rows = conn.execute(
        "SELECT ca_id, name, max_rank, in_current_pool, "
        "spell_rank_1, spell_rank_2, spell_rank_3, spell_rank_4, spell_rank_5 "
        "FROM dbc_character_advancement "
        "WHERE spell_rank_1 = ?1 OR spell_rank_2 = ?1 OR spell_rank_3 = ?1 "
        "   OR spell_rank_4 = ?1 OR spell_rank_5 = ?1",
        (catalog_spell_id,)).fetchall()
    if not rows:
        return None, "no CharacterAdvancement row for this spell id"
    pool = [r for r in rows if r[3]]
    if len(pool) > 1:
        return None, (f"{len(pool)} in-current-pool CA rows share this spell id "
                      "— ambiguous, refusing to pick one")
    row = pool[0] if pool else rows[0]
    if not pool:
        return None, "no in_current_pool CA row (other realm/mode entry only)"
    if card_rank < 1 or card_rank > 5:
        return None, f"card rank {card_rank} outside 1-5"
    resolved = row[3 + card_rank]
    if not resolved:
        return None, (f"CA row has no spell for rank {card_rank} "
                      f"(max_rank {row[2]})")
    return resolved, row[1]


def resolve_talents(conn, talents):
    """`TalentEffects` for a list of `SlottedCard`-like (spell_id, rank) items."""
    import json

    eff = TalentEffects()
    for card in talents:
        sid = getattr(card, "spell_id", None) or card["spell_id"]
        rank = getattr(card, "rank", None) or card.get("rank", 1)
        resolved, label = resolve_card_rank(conn, sid, rank)
        if resolved is None:
            eff.warnings.append(
                f"talent {sid} rank {rank}: NOT RESOLVED — {label}. It "
                "contributes nothing, and that is a data gap, not a measurement")
            continue
        row = conn.execute(
            "SELECT name, effect_json, source_archive FROM spell_dbc_raw "
            "WHERE id = ?", (resolved,)).fetchone()
        if row is None:
            eff.warnings.append(
                f"talent {label} ({sid}) rank {rank} resolves to {resolved}, "
                "which is absent from spell_dbc_raw — contributes nothing")
            continue
        name, effect_json, archive = row
        e = json.loads(effect_json)
        family = e.get("SpellClassSet")
        found = False
        for i in range(3):
            etype = _at(e, "Effect", i)
            aura = _at(e, "EffectAura", i)
            if etype == 0 and aura == 0:
                continue
            bp = _at(e, "EffectBasePoints", i)
            misc = _at(e, "EffectMiscValue", i)
            misc_b = _at(e, "EffectMiscValueB", i)
            cmask = (e.get("EffectSpellClassMask") or [0] * 9)[i * 3:i * 3 + 3]
            evidence = f"dbc:Spell.dbc:{resolved}:effect{i}@{archive}"
            if aura in AURA_KNOWN_NOT_A_MODIFIER:
                tag, why = AURA_KNOWN_NOT_A_MODIFIER[aura]
                eff.modifiers.append(TalentModifier(
                    sid, name, rank, resolved, i, f"known_{tag}", None,
                    {"aura": aura, "effect_type": etype, "misc": misc},
                    evidence, why))
                found = True
                continue
            if aura not in AURA_SEMANTICS:
                eff.modifiers.append(TalentModifier(
                    sid, name, rank, resolved, i, f"unmodelled_aura_{aura}",
                    None, {"aura": aura, "effect_type": etype, "misc": misc},
                    evidence,
                    "aura not in AURA_SEMANTICS - its meaning is not established"))
                continue
            kind, misc_kind = AURA_SEMANTICS[aura]
            # flat-value convention: base_points + 1 (core/spells/dbc_numeric)
            value = float(bp + 1)
            scope = {"aura": aura}
            if misc_kind == "school_mask":
                scope["school_mask"] = misc
                scope["schools"] = [n for b, n in SCHOOL_BITS.items() if misc & b]
            elif misc_kind == "school_mask_stat_b":
                scope["school_mask"] = misc
                scope["schools"] = [n for b, n in SCHOOL_BITS.items() if misc & b]
                scope["stat_index"] = misc_b
                scope["stat"] = {0: "Strength", 1: "Agility", 2: "Stamina",
                                 3: "Intellect", 4: "Spirit"}.get(misc_b, str(misc_b))
            elif misc_kind == "spellmod_op":
                scope["op"] = misc
                scope["op_name"] = SPELLMOD_OP_NAMES.get(misc, str(misc))
                scope["class_mask"] = cmask
                scope["family"] = family
                if misc not in SPELLMOD_DAMAGE_OPS:
                    scope["affects_damage"] = False
            eff.modifiers.append(TalentModifier(
                sid, name, rank, resolved, i, kind, value, scope, evidence))
            found = True
        if not found:
            eff.warnings.append(
                f"talent {name} ({sid}) rank {rank}: no modelled effect - every "
                "slot used an aura whose meaning is not established")

    unknown = eff.unmodelled()
    if unknown:
        by_talent = {}
        for m in unknown:
            by_talent.setdefault(m.talent_name, set()).add(m.scope["aura"])
        eff.warnings.append(
            "UNMODELLED talent effects (contributing nothing, which is a GAP "
            "and not a measured zero): "
            + "; ".join(f"{n} aura {sorted(a)}" for n, a in sorted(by_talent.items())))
    scripted = [m for m in eff.modifiers if m.kind == "known_server_script"]
    if scripted:
        eff.warnings.append(
            "talents whose effect is a server-side script (SPELL_AURA_DUMMY), so "
            "no numeric field states it and it cannot be modelled from the "
            "client: "
            + ", ".join(sorted({m.talent_name for m in scripted})))
    non_damage = [m for m in eff.modifiers
                  if m.kind.startswith("spellmod") and not m.scope.get("affects_damage", True)]
    if non_damage:
        eff.warnings.append(
            "SpellMod effects decoded but NOT applied to damage (they modify "
            "cooldown/cost/duration/crit, which the damage path must not touch): "
            + ", ".join(f"{m.talent_name} {m.scope['op_name']}" for m in non_damage))
    # 2e T10 (D3): load bucket membership for the slotted talents, so
    # damage_multiplier can score conflicts as the game does (highest member
    # only). Allowed + warned, never rejected — the analysis path must be able
    # to model someone else's conflicted board.
    slotted = {m.talent_spell_id for m in eff.modifiers}
    if slotted:
        placeholders = ",".join("?" * len(slotted))
        rows = conn.execute(
            f"SELECT spell_id, bucket_id, bucket_name FROM exclusivity_buckets "
            f"WHERE spell_id IN ({placeholders})", tuple(slotted)).fetchall()
        eff.buckets = {r[0]: (r[1], r[2]) for r in rows}
        by_bucket = {}
        for sid_, (bid, bname) in eff.buckets.items():
            by_bucket.setdefault((bid, bname), []).append(sid_)
        for (bid, bname), members in by_bucket.items():
            if len(members) > 1:
                names = sorted({m.talent_name for m in eff.modifiers
                                if m.talent_spell_id in members})
                eff.warnings.append(
                    f"exclusivity bucket '{bname}' has {len(members)} slotted "
                    f"members ({', '.join(names)}) — only the highest applies "
                    "per evaluation; the rest are dead weight on this board "
                    "(allowed and scored as the game scores it, per D3)")
    return eff


def _at(effects, key, index, default=0):
    values = effects.get(key) or []
    return values[index] if index < len(values) else default
