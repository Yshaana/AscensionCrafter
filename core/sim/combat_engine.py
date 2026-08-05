"""Phase 2 T1 — the shared combat physics.

Ported SimC/WotLK math, NOT a SimC fork (PHASE_2 "The SimC decision"). Every
formula below carries a comment naming its source and its validation status
against real Ascension data. Ascension is heavily modified — a formula correct
in retail WotLK is a *hypothesis* here until Task 8 (calibration) confirms it.

Validation-status vocabulary used in comments and warnings:
    ascension_confirmed  — measured on this server (confirmed_facts / parses)
    retail_hypothesis    — retail 3.3.5 mechanic, NOT yet validated here
    open_question        — a recorded conflict/unknown; value flagged loudly

Hard rule (PHASE_2 T1): a needed-but-unknown quantity is never silently
defaulted — it either raises `EngineDataError` or lands in a `warnings` list
the caller must surface.
"""
from dataclasses import dataclass, field


class EngineDataError(Exception):
    """A value the engine needs is missing, conflicted, or failed validation."""


# ---------------------------------------------------------------- rating -> %

# gtCombatRatings row layout: 32 ratings x 100 levels, row_index = cr*100+(level-1).
# CR enum order is stock 3.3.5 (SharedDefines.h CombatRating) — Ascension ships the
# table unmodified (Phase 0 T4: "gt* tables match retail; crit = exactly 14.0 at 60,
# validating both the tables and the row-index decoding").
CR_INDEX = {
    "defense": 1,
    "dodge": 2,
    "parry": 3,
    "block": 4,
    "hit_melee": 5,
    "hit_ranged": 6,
    "hit_spell": 7,
    "crit_melee": 8,
    "crit_ranged": 9,
    "crit_spell": 10,
    "haste_melee": 17,
    "haste_ranged": 18,
    "haste_spell": 19,
    "expertise": 23,
    "armor_penetration": 24,
}

# ascension_confirmed level-60 anchors (INDEX_GUIDE v8 / confirmed_facts:
# crit_rating_conversion et al.). Loading raises if the table disagrees — that
# would mean either the extract changed or the row-index decode broke.
_LEVEL60_ANCHORS = {
    "crit_melee": 14.0, "crit_ranged": 14.0, "crit_spell": 14.0,
    "hit_melee": 10.0, "hit_spell": 8.0,
    "haste_melee": 10.0, "expertise": 2.5,
}

# open_question `armor_pen_divisor_5_vs_4_2`: site calculator says 5, client gt
# table says 4.2. We serve the client value but always attach this warning.
_ARMOR_PEN_WARNING = (
    "armor_penetration divisor is a recorded CONFLICT (open question "
    "armor_pen_divisor_5_vs_4_2): client gt table says {value:g}, the site "
    "calculator says 5 — using the client value; settle with an in-game reading"
)


@dataclass
class RatingConversions:
    """Rating-per-1% divisors at one level, sourced from dbc_gt_tables."""
    level: int
    divisors: dict            # name -> rating per 1%
    warnings: list

    def percent(self, rating_name, rating):
        """Convert a rating amount to percent at this level."""
        div = self.divisors.get(rating_name)
        if not div:
            raise EngineDataError(
                f"no {rating_name!r} divisor at level {self.level} — "
                "refusing to default (PHASE_2 T1 hard rule)")
        return rating / div


def load_rating_conversions(conn, level=60):
    """Read rating divisors from dbc_gt_tables and validate the known anchors.

    Source: client gtCombatRatings.dbc via the committed extract. Anchor check
    is ascension_confirmed for level 60 only; other levels are the same table
    but unanchored (warning attached).
    """
    divisors, warnings = {}, []
    for name, cr in CR_INDEX.items():
        row = conn.execute(
            "SELECT value FROM dbc_gt_tables WHERE table_name = 'gtCombatRatings'"
            " AND row_index = ?", (cr * 100 + (level - 1),)).fetchone()
        if row is not None and row[0]:
            divisors[name] = row[0]
    if not divisors:
        raise EngineDataError(
            "gtCombatRatings absent from dbc_gt_tables — run py cli/rebuild.py")

    if level == 60:
        for name, expected in _LEVEL60_ANCHORS.items():
            got = divisors.get(name)
            if got is None or abs(got - expected) > 0.01:
                raise EngineDataError(
                    f"gtCombatRatings anchor mismatch at level 60: {name} = "
                    f"{got!r}, doc-confirmed value is {expected} — the extract "
                    "or the row-index decode changed; do not trust conversions")
    else:
        warnings.append(
            f"rating divisors at level {level} are unanchored (only level 60 "
            "is validated against confirmed_facts)")

    if "armor_penetration" in divisors:
        warnings.append(_ARMOR_PEN_WARNING.format(value=divisors["armor_penetration"]))
    return RatingConversions(level=level, divisors=divisors, warnings=warnings)


# ------------------------------------------------------------------- targets

@dataclass
class TargetProfile:
    """PHASE_2 T1 target model. +2 dungeon vs +3 raid drives miss chances."""
    level: int
    armor: int
    resistances: dict = field(default_factory=dict)   # school -> resistance
    dodge_pct: float = 0.0
    parry_pct: float = 0.0
    block_pct: float = 0.0
    count: int = 1


# ----------------------------------------------------------------- avoidance

# Base miss vs level delta, single-weapon special/spell attacks.
# melee: ascension_confirmed at +3 (primer §1: "special-attack yellow hit cap vs
# raid boss: 8%"); +0..+2 values are the retail_hypothesis 5/5.5/6 curve.
# spell: ascension_confirmed shape (primer §5: ~4/5/6/17 by delta; the +2≈6% and
# +3=17% figures are the project's own).
_MELEE_BASE_MISS = {0: 5.0, 1: 5.5, 2: 6.0, 3: 8.0}
_SPELL_BASE_MISS = {0: 4.0, 1: 5.0, 2: 6.0, 3: 17.0}
# ascension_confirmed (primer §1): dual-wield WHITE attacks carry +19% miss.
DUAL_WIELD_WHITE_MISS_PENALTY = 19.0
# retail_hypothesis: expertise reduces target dodge AND parry by 0.25% per point.
EXPERTISE_REDUCTION_PER_POINT = 0.25
# retail_hypothesis: glancing blows — white attacks only, vs higher-level targets.
# 3.3.5: chance 6% + 12% per level of skill-diff bands ≈ 24% vs +3 boss;
# damage penalty vs +3 ≈ 25% (SimC wotlk branch player_t::glance values).
GLANCING_CHANCE_VS_BOSS = 24.0
GLANCING_DAMAGE_PENALTY = 0.25


def _base_miss(table, delta, warnings, kind):
    if delta <= 0:
        return table[0]
    if delta in table:
        return table[delta]
    warnings.append(
        f"{kind} base miss for level delta +{delta} is outside the modelled "
        "0..3 range — using the +3 value; treat as unvalidated")
    return table[3]


def melee_miss_pct(attacker_level, target_level, hit_pct, dual_wield_white=False,
                   warnings=None):
    """Chance to miss with a melee swing after hit rating.

    Yellow cap 8% vs +3 is ascension_confirmed; the DW white +19% penalty is
    ascension_confirmed (primer §1 — effectively unreachable cap at low tiers).
    """
    w = warnings if warnings is not None else []
    miss = _base_miss(_MELEE_BASE_MISS, target_level - attacker_level, w, "melee")
    if dual_wield_white:
        miss += DUAL_WIELD_WHITE_MISS_PENALTY
    return max(0.0, miss - hit_pct)


def spell_miss_pct(attacker_level, target_level, spell_hit_pct, warnings=None):
    """Chance for a spell to miss. retail_hypothesis floor: miss can't go below
    1% in 3.3.5 — kept, flagged unvalidated on Ascension."""
    w = warnings if warnings is not None else []
    miss = _base_miss(_SPELL_BASE_MISS, target_level - attacker_level, w, "spell")
    return max(1.0 if miss > 1.0 else 0.0, miss - spell_hit_pct)


def effective_dodge_parry(target: TargetProfile, expertise_points,
                          attack_from_behind=False):
    """Target dodge/parry after expertise. Parry only applies from the front
    (retail_hypothesis). Expertise dodge cap 26 is ascension_confirmed
    (primer §1) and emerges naturally here: 26 x 0.25 = 6.5% ≈ boss dodge."""
    reduction = expertise_points * EXPERTISE_REDUCTION_PER_POINT
    dodge = max(0.0, target.dodge_pct - reduction)
    parry = 0.0 if attack_from_behind else max(0.0, target.parry_pct - reduction)
    return dodge, parry


# -------------------------------------------------------------- attack tables

@dataclass
class AttackTable:
    """Ordered outcome segments; probabilities in percent, summing to 100."""
    segments: list                    # [(outcome_name, pct), ...]
    warnings: list = field(default_factory=list)

    def probabilities(self):
        return {name: pct for name, pct in self.segments if pct > 0}

    def roll(self, rng):
        x = rng.uniform(0.0, 100.0)
        acc = 0.0
        for name, pct in self.segments:
            acc += pct
            if x < acc:
                return name
        return self.segments[-1][0]


def white_melee_table(attacker_level, crit_pct, hit_pct, expertise_points,
                      target: TargetProfile, dual_wield=False,
                      attack_from_behind=False):
    """Single-roll white-swing table: miss/dodge/parry/glancing/block/crit/hit.

    Structure: retail_hypothesis (3.3.5 one-roll white table, SimC
    melee_attack_t::execute ordering). Miss and DW penalty values are
    ascension_confirmed; glancing numbers are retail_hypothesis.
    """
    warnings = []
    delta = target.level - attacker_level
    miss = melee_miss_pct(attacker_level, target.level, hit_pct,
                          dual_wield_white=dual_wield, warnings=warnings)
    dodge, parry = effective_dodge_parry(target, expertise_points,
                                         attack_from_behind)
    glancing = GLANCING_CHANCE_VS_BOSS if delta >= 3 else max(0.0, delta * 6.0)
    if glancing:
        warnings.append(
            "glancing chance/penalty are retail_hypothesis values (24%/25% vs "
            "+3) — not yet validated on Ascension")
    block = max(0.0, target.block_pct)
    # retail_hypothesis: crit suppression vs higher-level targets exists but its
    # magnitude on Ascension is an OPEN QUESTION — the owner's own parse shows
    # autos at 16.2% vs a 21.76% sheet. We do NOT bake in a retail constant;
    # we warn instead (no silent defaults, and no fabricated precision either).
    if delta > 0:
        warnings.append(
            f"melee crit suppression vs +{delta} target not modelled "
            "(open question — sheet 21.76% vs parsed 16.2% autos suggests it "
            "exists on Ascension; measure before trusting white-crit output)")
    crit = max(0.0, crit_pct)
    used = miss + dodge + parry + glancing + block + crit
    if used > 100.0:
        # squeeze crit first, then block — retail table-overflow order
        overflow = used - 100.0
        crit = max(0.0, crit - overflow)
        used = miss + dodge + parry + glancing + block + crit
        if used > 100.0:
            block = max(0.0, block - (used - 100.0))
            used = miss + dodge + parry + glancing + block + crit
    return AttackTable(segments=[
        ("miss", miss), ("dodge", dodge), ("parry", parry),
        ("glancing", glancing), ("block", block), ("crit", crit),
        ("hit", max(0.0, 100.0 - used)),
    ], warnings=warnings)


def special_attack_table(attacker_level, crit_pct, hit_pct, expertise_points,
                         target: TargetProfile, can_be_dodged=True,
                         can_be_parried=True, can_be_blocked=True,
                         attack_from_behind=False):
    """Two-roll yellow attack: roll 1 avoidance (this table), roll 2 crit.

    Structure: retail_hypothesis (3.3.5 two-roll specials — no glancing).
    Returned table resolves the FIRST roll only; apply `crit_pct` to landed
    hits separately (that is what makes crit_table/hit_table independent).
    """
    warnings = []
    miss = melee_miss_pct(attacker_level, target.level, hit_pct,
                          warnings=warnings)
    dodge, parry = effective_dodge_parry(target, expertise_points,
                                         attack_from_behind)
    if not can_be_dodged:
        dodge = 0.0
    if not can_be_parried:
        parry = 0.0
    block = target.block_pct if can_be_blocked else 0.0
    used = min(100.0, miss + dodge + parry + block)
    return AttackTable(segments=[
        ("miss", miss), ("dodge", dodge), ("parry", parry), ("block", block),
        ("land", max(0.0, 100.0 - used)),
    ], warnings=warnings)


def spell_table(attacker_level, spell_hit_pct, target: TargetProfile,
                can_be_full_resisted=True, binary=False):
    """Spell resolution roll 1: miss / full_resist / land.

    Structure: retail_hypothesis. `can_be_full_resisted=False` (e.g. Holy) means
    NO full-resist roll but partial resistance still applies downstream —
    ascension_confirmed distinction (primer §1 v17, 4,962-hit HftH sample).
    """
    warnings = []
    miss = spell_miss_pct(attacker_level, target.level, spell_hit_pct,
                          warnings=warnings)
    full_resist = 0.0
    if can_be_full_resisted and binary:
        warnings.append(
            "binary-spell full-resist chance from target resistance is not "
            "modelled yet (needs a resistance model validated on Ascension)")
    return AttackTable(segments=[
        ("miss", miss), ("full_resist", full_resist),
        ("land", max(0.0, 100.0 - miss - full_resist)),
    ], warnings=warnings)


# ------------------------------------------------------------------ mitigation

def armor_dr_fraction(target_armor, attacker_level):
    """Physical damage reduction from armor.

    retail_hypothesis: 3.3.5 formula (SimC wotlk `armor_mitigation::ratio`):
        DR = armor / (armor + 400 + 85*L)            for attacker L <= 59
        DR = armor / (armor + 400 + 85*(L + 4.5*(L-59)))  for L >= 60
    Not yet validated against an Ascension parse.
    """
    if target_armor <= 0:
        return 0.0
    lvl = attacker_level
    denom_const = 400 + 85 * (lvl + 4.5 * (lvl - 59)) if lvl >= 60 else 400 + 85 * lvl
    return target_armor / (target_armor + denom_const)


def armor_after_penetration(target_armor, arp_pct):
    """retail_hypothesis: ArP reduces effective armor by its percentage.

    3.3.5 also caps the armor ArP can act on (armor-cap constant); at level-60
    armor values (~4k) the cap is not binding, so it is deliberately not
    modelled — revisit if content armor exceeds ~8k.
    """
    return target_armor * max(0.0, 1.0 - min(arp_pct, 100.0) / 100.0)


def average_resist_fraction(resistance, attacker_level, warnings=None):
    """Average partial-resist fraction for a NON-binary spell school.

    retail_hypothesis: average resist ≈ 0.75 * R / (5 * attacker_level), capped
    at 75% (3.3.5 resistance-segment model collapsed to its mean; SimC wotlk
    `spell_resistance`). Ascension confirms partial resists exist even on Holy
    ("unresistable" = no full-resist roll only, primer §1 v17) but the CURVE is
    unvalidated here.
    """
    if resistance <= 0:
        return 0.0
    if warnings is not None:
        warnings.append(
            "partial-resist curve is retail_hypothesis (0.75*R/(5*level), "
            "cap 75%) — Ascension confirms partials exist, curve unvalidated")
    return min(0.75, 0.75 * resistance / (5.0 * attacker_level))


# ------------------------------------------------------------------ crit math

# ascension_confirmed defaults: spells crit for 150% in 3.3.5; melee for 200%.
# Ascension talent cards modify these per school (e.g. Holy Focus "spell crits
# deal 200%") — that belongs to compute_stats/talent modelling, not here.
CRIT_MULT_SPELL_DEFAULT = 1.5
CRIT_MULT_MELEE_DEFAULT = 2.0


def crit_multiplier(crit_table, override=None):
    """Base crit damage multiplier by table. `override` comes from
    spell_mechanics.crit_damage_multiplier (doc-confirmed) when present."""
    if override:
        return override
    if crit_table == "melee":
        return CRIT_MULT_MELEE_DEFAULT
    if crit_table == "spell":
        return CRIT_MULT_SPELL_DEFAULT
    raise EngineDataError(
        f"crit_table {crit_table!r} has no default multiplier — pass an "
        "explicit override")
