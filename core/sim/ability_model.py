"""Phase 2 T3 — `ResolvedAbility`: one ability, resolved once, used by every tier.

Built from `spell_profile(mode='fast')` — NEVER raw tables (1c audit kickoff
rule #1: rank gaps and conflicts only surface on the resolver path; raw reads
simulate placeholders). The three sim tiers may differ in how rigorously they
evaluate over time, never in what an ability does (PHASE_2 T3).

The four 2a kickoff rules, enforced here:

1. Resolver path only — `resolve_ability()` calls `spell_profile`, follows its
   `rank_gap` redirect, and refuses ambiguous rank lines.
2. `term_type` is a vocabulary: school-scoped SP terms (SPFR/SPFI/SPH/SPN/SPA/
   SPS) resolve through `CharState.effective_spell_power(school)` — treating
   them as generic SP double-counts hybrid double-dip. BH is healing-side (the
   mechanics resolver already routes it there; asserted here anyway).
3. Coefficients > OUTLIER_COEFFICIENT_CAP are EXCLUDED with a named warning
   (swallowed *N DoT-total multipliers in the committed extract — open question
   `hidden_formula_outlier_coefficients`). Exclusion, not clamping: a clamped
   3.0 is still a fabricated number.
4. `confidence='inferred'` terms (incl. `via='trigger_hopN'`) compute but are
   flagged `calibration_anchor=False` — they must never anchor calibration as
   if they were tier-1 parses. trigger_hop magnitudes ARE summed into the
   per-hit mean (for cards like Hour of Judgement the triggered spell IS the
   card's damage — excluding them would zero 444 cards); the rule is about
   calibration anchoring, not computation. They are also listed separately in
   `triggered_components` so calibration can subtract them.
"""
import json
from dataclasses import dataclass, field

from . import combat_engine as ce
from .content import ContentProfile, Metric

OUTLIER_COEFFICIENT_CAP = 3.0

# term_type -> how to read the stat off CharState. School-scoped SP terms name
# their school; None school on 'SP' means "the ability's own school".
_SCHOOL_SP_TERMS = {"SPFR": "Frost", "SPFI": "Fire", "SPH": "Holy",
                    "SPN": "Nature", "SPA": "Arcane", "SPS": "Shadow"}
_MAGIC_SCHOOLS = {"Holy", "Fire", "Nature", "Frost", "Shadow", "Arcane"}


class AbilityResolutionError(Exception):
    """The resolver refused (ambiguous rank line, missing spell) — the sim
    refuses too rather than guessing (PHASE_1 rule inherited)."""


@dataclass
class ExpectedHitResult:
    mean: float                    # expected damage per event, all rolls folded in
    variance: float
    mean_healing: float
    breakdown: dict                # p_miss/p_avoid/p_land/p_crit_given_land/...
    per_metric: dict               # Metric -> expected value per event
    components: list               # per-term contributions with provenance flags
    applied_multipliers: dict      # bucket name -> multiplier actually applied
    warnings: list


@dataclass
class HitResult:
    outcome: str                   # miss/dodge/parry/block/full_resist/hit/crit/tick
    damage: float
    healing: float = 0.0


@dataclass
class ResolvedAbility:
    """Everything the sim tiers need about one ability. Construct via
    `resolve_ability()`, not directly."""
    spell_id: int
    name: str
    level: int
    school: str | None
    fields: dict                   # resolved mechanics fields (spell_mechanics)
    confidence: str
    damage_terms: list
    healing_terms: list
    triggered_components: list     # inferred trigger_hop magnitudes, NOT in mean
    rank_note: str | None
    resolution_warnings: list

    # ---------------------------------------------------------------- helpers

    def _crit_table(self, warnings):
        ct = self.fields.get("crit_table")
        if ct:
            return ct
        guess = "melee" if self.school == "Physical" else "spell"
        warnings.append(
            f"crit_table unconfirmed for {self.name} ({self.spell_id}) — "
            f"heuristic '{guess}' from school {self.school!r} (Holystrike "
            "precedent: hybrids crit on the spell table); verify per parse")
        return guess

    def _hit_table(self, warnings):
        ht = self.fields.get("hit_table")
        if ht:
            return ht
        guess = "melee" if self.school == "Physical" else "spell"
        warnings.append(
            f"hit_table unconfirmed for {self.name} ({self.spell_id}) — "
            f"heuristic '{guess}' from school; crit and hit tables are "
            "INDEPENDENT rolls (primer §5), never inferred from each other")
        return guess

    def _rolls_hit_check(self, warnings):
        r = self.fields.get("rolls_hit_check")
        if r is not None:
            return bool(r)
        if self.fields.get("is_periodic"):
            # ascension_confirmed: periodic effects cannot miss (primer §5)
            return False
        warnings.append(
            f"rolls_hit_check unconfirmed for {self.name} ({self.spell_id}) — "
            "assuming it rolls (the conservative direction for hit weights); "
            "procs riding a landed attack would make this False")
        return True

    def _can_crit(self, warnings):
        if self.fields.get("always_crits"):
            return True, True
        if self.fields.get("is_periodic"):
            tcc = self.fields.get("ticks_can_crit")
            if tcc is None:
                warnings.append(
                    f"{self.name} ({self.spell_id}) is periodic with "
                    "unconfirmed tick-crit: defaulting to CANNOT crit "
                    "(aura-tick rule, primer §1) — but Molten Earth proves "
                    "exceptions exist; verify from a parse, never the tooltip")
                return False, False
            return bool(tcc), False
        return True, False

    def _avoidance_table(self, char_state, content: ContentProfile, warnings):
        """First-roll table per hit_table/rolls_hit_check. Returns AttackTable
        with a single 'land' segment when nothing rolls."""
        if not self._rolls_hit_check(warnings):
            return ce.AttackTable(segments=[("land", 100.0)])
        ht = self._hit_table(warnings)
        t = content.target
        if ht == "melee":
            def flag(name, default):
                v = self.fields.get(name)
                if v is None:
                    warnings.append(
                        f"{name} unconfirmed for {self.name} — assuming "
                        f"{default} (retail default for melee specials)")
                    return default
                return bool(v)
            table = ce.special_attack_table(
                char_state.level, char_state.melee_crit_pct,
                char_state.melee_hit_pct, char_state.expertise_points, t,
                can_be_dodged=flag("can_be_dodged", True),
                can_be_parried=flag("can_be_parried", True),
                can_be_blocked=flag("can_be_blocked", False))
        else:
            cbfr = self.fields.get("can_be_full_resisted")
            if cbfr is None:
                if self.school == "Holy":
                    # ascension_confirmed: Holy has no full-resist roll
                    # (primer §1 v17; 4,962-hit HftH sample) — partials remain
                    cbfr = False
                else:
                    cbfr = True
                    warnings.append(
                        f"can_be_full_resisted unconfirmed for {self.name} — "
                        "assuming full-resist roll exists (non-Holy school)")
            table = ce.spell_table(char_state.level, char_state.spell_hit_pct,
                                   t, can_be_full_resisted=bool(cbfr))
        warnings.extend(table.warnings)
        return table

    def _components(self, char_state, warnings):
        """Per-term damage/healing contributions. Returns (damage_min,
        damage_max, healing_avg, components)."""
        dmin = dmax = heal = 0.0
        comps = []

        def stat_for(term):
            if term == "AP":
                return char_state.attack_power
            if term == "RAP":
                return char_state.ranged_attack_power
            if term == "SP":
                return char_state.effective_spell_power(self.school)
            if term in _SCHOOL_SP_TERMS:
                return char_state.effective_spell_power(_SCHOOL_SP_TERMS[term])
            if term == "SPI":
                return char_state.spirit
            if term == "STA":
                return char_state.stamina
            if term == "BH":
                return char_state.bonus_healing
            return None

        # ---- coefficient dedup: rank-sibling text is the rank-correct source
        by_term = {}
        for t in self.damage_terms:
            if t.get("term") == "FLAT":
                continue
            by_term.setdefault(t["term"], []).append(t)

        def pick_rows(rows):
            pref = [r for r in rows if r.get("source") == "dbc_rank_sibling_text"]
            chosen = pref or rows
            srcs = {r.get("source") for r in rows}
            if pref and len(srcs) > 1:
                warnings.append(
                    f"{self.name}: term {rows[0]['term']} has multiple "
                    "coefficient sources — using rank-sibling text (rank-"
                    "correct) over the catalog's stored rank")
            return chosen

        for t in self.damage_terms:
            term = t.get("term")
            if term == "FLAT":
                via = t.get("via", "self")
                lo = t.get("min")
                hi = t.get("max")
                if lo is None:
                    continue
                cp = t.get("per_combo")
                if cp:
                    warnings.append(
                        f"{self.name}: per-combo flat term present — combo "
                        "points not yet parameterised in expected_hit (2a); "
                        "term included at 0 CP")
                dmin += lo
                dmax += (hi if hi is not None else lo)
                comps.append({"kind": "flat", "min": lo, "max": hi, "via": via,
                              "confidence": t.get("confidence"),
                              "calibration_anchor":
                                  t.get("confidence") == "confirmed",
                              "evidence_ref": t.get("evidence_ref")})
        for term, rows in by_term.items():
            for t in pick_rows(rows):
                coeff = t.get("coefficient")
                if coeff is None:
                    continue
                if coeff > OUTLIER_COEFFICIENT_CAP:
                    warnings.append(
                        f"{self.name}: {term} coefficient {coeff:g} EXCLUDED — "
                        f"exceeds the {OUTLIER_COEFFICIENT_CAP:g} outlier cap "
                        "(swallowed *N DoT-total multipliers in the committed "
                        "extract; open question "
                        "hidden_formula_outlier_coefficients — fixed by the "
                        "next --with-dbc re-extraction)")
                    comps.append({"kind": "excluded_outlier", "term": term,
                                  "coefficient": coeff,
                                  "calibration_anchor": False})
                    continue
                stat = stat_for(term)
                if stat is None:
                    if term == "WEAPON":
                        w = char_state.main_hand
                        if not w:
                            warnings.append(
                                f"{self.name}: WEAPON term but no main-hand "
                                "weapon on CharState — term contributes 0, "
                                "named not silent")
                            continue
                        lo, hi = w["min"] * coeff, w["max"] * coeff
                        cp_kind = t.get("cp_scaling")
                        dmin += lo
                        dmax += hi
                        comps.append({"kind": "weapon", "coefficient": coeff,
                                      "min": lo, "max": hi,
                                      "cp_scaling": cp_kind,
                                      "confidence": t.get("confidence"),
                                      "calibration_anchor": False})
                        continue
                    warnings.append(
                        f"{self.name}: unknown scaling term {term!r} — "
                        "contributes 0, named not silent (extend the term "
                        "vocabulary here if the extractor learned a new one)")
                    continue
                if t.get("cp_scaling"):
                    warnings.append(
                        f"{self.name}: {term} carries cp_scaling="
                        f"{t['cp_scaling']} — combo points not parameterised "
                        "in 2a; coefficient applied WITHOUT the CP factor")
                contrib = stat * coeff
                dmin += contrib
                dmax += contrib
                comps.append({"kind": "coefficient", "term": term,
                              "coefficient": coeff, "value": contrib,
                              "source": t.get("source"),
                              "confidence": t.get("confidence", "inferred"),
                              "calibration_anchor": False})

        for t in self.healing_terms:
            if t.get("term") == "FLAT":
                lo, hi = t.get("min"), t.get("max")
                if lo is not None:
                    heal += (lo + (hi if hi is not None else lo)) / 2.0
            else:
                coeff = t.get("coefficient")
                stat = stat_for(t.get("term"))
                if coeff is not None and stat is not None:
                    heal += stat * coeff

        return dmin, dmax, heal, comps

    def _mitigation(self, char_state, content: ContentProfile, warnings):
        """Multiplicative mitigation factor: armor for physical, average
        partial resist for magic. Hybrids warn (component split is 2b work)."""
        t = content.target
        school = self.school
        if school == "Physical" or self.fields.get("affected_by_armor"):
            armor = ce.armor_after_penetration(t.armor, char_state.armor_pen_pct)
            return 1.0 - ce.armor_dr_fraction(armor, char_state.level)
        if school in _MAGIC_SCHOOLS:
            res = t.resistances.get(school, 0)
            return 1.0 - ce.average_resist_fraction(res, char_state.level,
                                                    warnings)
        if school:  # named hybrid or composite
            warnings.append(
                f"{self.name}: hybrid school {school!r} mitigation not split "
                "into physical/magic components yet (2a) — no mitigation "
                "applied; primer §1 says hybrids have an armor-mitigated half")
        return 1.0

    def _damage_buckets(self, char_state):
        """Which CharState.damage_multipliers buckets apply. Applied buckets
        are surfaced so nothing multiplies invisibly."""
        applied = {}
        for bucket, mult in char_state.damage_multipliers.items():
            if bucket == "all_damage":
                applied[bucket] = mult
            elif bucket == "physical_ability" and self.school == "Physical":
                applied[bucket] = mult
            elif bucket == "spell_damage" and self.school in _MAGIC_SCHOOLS:
                applied[bucket] = mult
        return applied

    # ------------------------------------------------------------- public API

    def expected_hit(self, char_state, content: ContentProfile,
                     rng=None) -> ExpectedHitResult:
        """Expected value/variance for ONE event (one direct hit or one tick).

        For periodic abilities with known duration/tick the per-cast total is
        `mean * n_ticks()` — direct-vs-DoT term splitting inside one ability
        is 2b work and warned about when both could be present.
        """
        warnings = list(self.resolution_warnings)
        table = self._avoidance_table(char_state, content, warnings)
        probs = table.probabilities()
        p_land = probs.get("land", probs.get("hit", 0.0) + probs.get("crit", 0.0)
                           + probs.get("glancing", 0.0)) / 100.0

        can_crit, always = self._can_crit(warnings)
        if can_crit and not always:
            ctable = self._crit_table(warnings)
            crit_pct = (char_state.melee_crit_pct if ctable == "melee"
                        else char_state.spell_crit_pct)
            p_crit = min(1.0, max(0.0, crit_pct / 100.0))
            mult = ce.crit_multiplier(
                ctable, self.fields.get("crit_damage_multiplier"))
        elif always:
            p_crit, mult = 1.0, ce.crit_multiplier(
                self._crit_table(warnings),
                self.fields.get("crit_damage_multiplier"))
        else:
            p_crit, mult = 0.0, 1.0
        mult += char_state.ability_crit_damage_bonus if p_crit else 0.0

        dmin, dmax, heal, comps = self._components(char_state, warnings)
        mitigation = self._mitigation(char_state, content, warnings)
        buckets = self._damage_buckets(char_state)
        bucket_mult = 1.0
        for m in buckets.values():
            bucket_mult *= m

        base_avg = (dmin + dmax) / 2.0
        scale = mitigation * bucket_mult
        e_crit_factor = 1.0 + p_crit * (mult - 1.0)
        mean = p_land * base_avg * scale * e_crit_factor

        # variance: uniform base on [dmin,dmax], mixture over outcomes
        # E[D^2] for uniform = (a^2+ab+b^2)/3
        a, b = dmin * scale, dmax * scale
        e_d2 = (a * a + a * b + b * b) / 3.0
        e2 = p_land * ((1.0 - p_crit) * e_d2 + p_crit * e_d2 * mult * mult)
        variance = max(0.0, e2 - mean * mean)

        if not comps and base_avg == 0.0:
            warnings.append(
                f"{self.name} ({self.spell_id}): no resolvable magnitude — "
                "expected damage is 0 because nothing is KNOWN, not because "
                "the ability does nothing")
        if self.confidence == "conflict":
            warnings.append(
                f"{self.name} ({self.spell_id}): mechanics row carries a "
                "source CONFLICT (§2.3) — output uses the stronger tier's "
                "value; check spell_mechanics.conflicts_json")
        if self.triggered_components:
            warnings.append(
                f"{self.name}: {len(self.triggered_components)} trigger-"
                "attributed magnitude(s) included in the mean at "
                "confidence=inferred (bounded trigger walk) — real but "
                "attributed, never a calibration anchor; see "
                "triggered_components")

        n = content.target.count
        if n > 1:
            cap = self.fields.get("max_targets") or self.fields.get("cleave_fixed_n")
            if self.fields.get("aoe_radius") or cap:
                if cap is None:
                    warnings.append(
                        f"{self.name}: AoE with no max_targets/falloff data — "
                        "per-target value reported; total at {n} targets is "
                        "UNKNOWN, not per_target*n (PHASE_2 T3: three "
                        "different split behaviours exist in the data)")
            # per-event result stays per-target; tiers own target math

        return ExpectedHitResult(
            mean=mean, variance=variance, mean_healing=heal * p_land,
            breakdown={
                "p_land": p_land, "p_crit_given_land": p_crit,
                "avoidance": {k: v / 100.0 for k, v in probs.items()
                              if k not in ("land", "hit", "crit")},
                "crit_multiplier": mult, "mitigation_factor": mitigation,
                "base_min": dmin, "base_max": dmax,
            },
            per_metric={Metric.DAMAGE_DONE: mean,
                        Metric.HEALING_DONE: heal * p_land},
            components=comps, applied_multipliers=buckets, warnings=warnings)

    def roll_hit(self, char_state, content: ContentProfile, rng) -> HitResult:
        """One RNG resolution of one event. `mean(roll_hit x N)` must converge
        on `expected_hit().mean` — asserted by tools/audit/check_sim_engine.py."""
        warnings = []
        table = self._avoidance_table(char_state, content, warnings)
        outcome = table.roll(rng)
        if outcome not in ("land", "hit", "crit", "glancing"):
            return HitResult(outcome=outcome, damage=0.0)

        dmin, dmax, heal, _ = self._components(char_state, warnings)
        mitigation = self._mitigation(char_state, content, warnings)
        bucket_mult = 1.0
        for m in self._damage_buckets(char_state).values():
            bucket_mult *= m
        dmg = rng.uniform(dmin, dmax) * mitigation * bucket_mult

        can_crit, always = self._can_crit(warnings)
        crit = False
        if can_crit:
            ctable = self._crit_table(warnings)
            crit_pct = (char_state.melee_crit_pct if ctable == "melee"
                        else char_state.spell_crit_pct)
            crit = always or rng.uniform(0.0, 100.0) < crit_pct
            if crit:
                mult = ce.crit_multiplier(
                    ctable, self.fields.get("crit_damage_multiplier"))
                dmg *= mult + char_state.ability_crit_damage_bonus
        return HitResult(outcome="crit" if crit else "hit", damage=dmg,
                         healing=heal)

    def n_ticks(self):
        """Tick count for periodic abilities, or None."""
        dur = self.fields.get("duration_seconds")
        tick = self.fields.get("tick_interval_seconds")
        if self.fields.get("is_periodic") and dur and tick:
            return max(1, round(dur / tick))
        return None


# ------------------------------------------------------------------- factory

def resolve_ability(conn, spell_id, level=60, _redirected=False) -> ResolvedAbility:
    """Build a ResolvedAbility through the resolver path (spell_profile).

    Follows a `different_rank_at_level` rank gap to the id the character
    actually casts (noted, never silent). Refuses ambiguous rank lines.
    """
    from ..spells.profile import spell_profile

    prof = spell_profile(conn, int(spell_id), mode="fast", level=level)
    if not prof.get("found"):
        raise AbilityResolutionError(f"spell {spell_id} not found by resolver")
    if prof.get("ambiguous"):
        raise AbilityResolutionError(
            f"spell {spell_id}: ambiguous — {prof.get('candidates')}")

    mech = prof["mechanics"]
    rank_note = None
    gap = mech.get("rank_gap")
    if gap and not _redirected:
        if gap.get("kind") == "different_rank_at_level":
            target = gap["level_spell_id"]
            ability = resolve_ability(conn, target, level=level, _redirected=True)
            ability.rank_note = (
                f"queried id {spell_id} redirected to {target} (rank "
                f"{gap['level_rank']}) — the id a level-{level} character "
                "casts; magnitudes are that rank's (resolver rule 3)")
            return ability
        if gap.get("kind") == "no_rank_at_level":
            raise AbilityResolutionError(
                f"spell {spell_id}: ambiguous rank line at level {level} — "
                f"the crosswalk refuses to tie-break ({gap.get('detail')}); "
                "resolve manually before simming this ability")

    fields = mech["fields"]
    warnings = []
    damage_terms = json.loads(fields.get("damage_formula_terms_json") or "[]")
    healing_terms = json.loads(fields.get("healing_formula_terms_json") or "[]")
    triggered = [t for t in damage_terms
                 if str(t.get("via", "")).startswith("trigger_hop")]
    for t in damage_terms:
        if t.get("term") == "BH":   # kickoff rule 2: BH is healing, full stop
            healing_terms.append(t)
    damage_terms = [t for t in damage_terms if t.get("term") != "BH"]

    identity = prof["identity"]
    return ResolvedAbility(
        spell_id=identity["id"], name=identity.get("name") or str(spell_id),
        level=level, school=fields.get("school"), fields=fields,
        confidence=mech.get("confidence", "inferred"),
        damage_terms=damage_terms, healing_terms=healing_terms,
        triggered_components=triggered, rank_note=rank_note,
        resolution_warnings=warnings)
