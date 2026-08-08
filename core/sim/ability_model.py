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

# A periodic-trigger aura's pulse count multiplies a component's whole per-cast
# contribution, so an unvalidated reading of the period field is dangerous in a
# way a wrong flat is not. Across the 48 periodic-delivery component rows in the
# catalog the periods run from 0.01s to 18s; a 0.01s period over a 10s duration
# would mean 1,000 pulses, which is not a reading anything corroborates. Above
# this limit the count is REFUSED (n=None) rather than applied or clamped —
# clamping would be a fabricated number, and applying it would silently inflate
# the ability by orders of magnitude. Hour of Judgement's 20 is well inside it.
PULSE_COUNT_SANITY_LIMIT = 100

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
class AbilityEvent:
    """One damage-producing event of an ability (2b).

    An ability is NOT one event. Hour of Judgement is three: its own periodic
    tick (81 Holy every 2s), its own direct terms (SP/AP 0.05), and the Hammer
    from the Heavens pulse it triggers (122-145 + 9.1% SP/AP on spell 282987).
    2a summed all of them into a single mean resolved under a single avoidance
    roll and a single crit roll, which is wrong in both directions: the DoT tick
    cannot be dodged and (usually) cannot crit, while the pulse is a separate
    spell with its own confirmed no-avoidance profile.

    Each event resolves on ITS OWN tables, using the combat-table facts of the
    spell that carries it — `fields` here is the component's own doc-confirmed
    overlay where one exists, falling back to the card's with a warning.
    """
    key: str                       # 'self:direct', 'trigger_hop2:282987:direct'
    source_spell_id: int | None
    via: str
    kind: str                      # 'direct' | 'periodic'
    school: str | None
    terms: list
    fields: dict                   # combat-table fields for THIS event's spell
    tick_interval_seconds: float | None
    delivery: dict | None          # how a trigger-reached event is DELIVERED
    is_attributed: bool            # reached by trigger walk -> never an anchor
    notes: list


@dataclass
class ExpectedCastResult:
    """One full activation of an ability: every event, at its own occurrence
    count. This is what the sim tiers consume; `expected_hit` stays per-event."""
    mean: float
    variance: float
    mean_healing: float
    per_event: list                # [{event_key, occurrences, mean_each, ...}]
    unresolved_events: list        # events whose occurrence count is UNKNOWN
    warnings: list


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
    component_fields: dict = field(default_factory=dict)   # source_spell_id -> fields
    # 🆕 3g G2 / E14 — source_spell_id -> that spell's OWN duration in seconds,
    # from its own `duration_index` -> `dbc_spellduration`. Kept separate from
    # `component_fields` on purpose: that dict holds doc-confirmed combat-table
    # facts, and `_fields_for` uses its emptiness to decide whether to warn that
    # a component fell back to the card's fields. Folding a duration into it
    # would silence that warning for every attributed component.
    component_durations: dict = field(default_factory=dict)
    # SpellFamilyName / SpellClassMask — what a talent SpellMod's class mask is
    # matched against (T4b). None means the client record was unavailable, which
    # is NOT the same as "no talent reaches this ability"; the talent path warns.
    spell_family: int | None = None
    spell_class_mask: list | None = None
    _events_cache: list | None = None

    # ----------------------------------------------------------------- events

    def events(self):
        """Decompose this ability into its damage events (2b).

        Grouping is (source_spell_id, direct|periodic) — the two things that
        decide which tables an event resolves on. Coefficient terms carry no
        effect binding (they come from tooltip TEXT, which cannot say which
        effect slot it describes), so they attach to their source's DIRECT
        event where one exists, and the ambiguity is warned about by name when
        a source has both a direct and a periodic component.
        """
        if self._events_cache is not None:
            return self._events_cache

        groups, notes_by_key = {}, {}

        def key_for(src, kind, via):
            return f"{via}:{src}:{kind}" if via != "self" else f"self:{kind}"

        # pass 1: flats — these know their own periodicity and school
        for t in self.damage_terms:
            if t.get("term") != "FLAT":
                continue
            src = t.get("source_spell_id")
            via = t.get("via") or "self"
            kind = "periodic" if t.get("is_periodic") else "direct"
            k = key_for(src, kind, via)
            groups.setdefault(k, {"src": src, "via": via, "kind": kind,
                                  "school": t.get("source_school"),
                                  "tick": t.get("tick_interval_seconds"),
                                  "delivery": t.get("trigger_delivery"),
                                  "terms": []})["terms"].append(t)

        # pass 2: coefficients — unbound, attach to the source's direct event
        for t in self.damage_terms:
            if t.get("term") == "FLAT":
                continue
            src = t.get("source_spell_id")
            via = t.get("via") or "self"
            direct_k = key_for(src, "direct", via)
            periodic_k = key_for(src, "periodic", via)
            # A STATED binding beats the guess. Only db.ascension.gg-sourced
            # rows carry one ("to direct component" / "per tick"); text-derived
            # rows leave it None because tooltip text cannot bind a term to an
            # effect slot. This is what stops a DoT's coefficient from being
            # applied to the direct hit on the 294 spells that state both.
            stated = t.get("component")
            stated_k = key_for(src, stated, via) if stated in ("direct", "periodic") else None
            if stated_k is not None and stated_k in groups:
                k = stated_k
            elif direct_k in groups:
                k = direct_k
                if periodic_k in groups:
                    notes_by_key.setdefault(k, []).append(
                        f"coefficient term {t.get('term')} attached to the "
                        f"DIRECT component of spell {src}, but that spell also "
                        "has a periodic component — tooltip text cannot bind a "
                        "coefficient to an effect slot, so this split is an "
                        "assumption, not a reading")
                if stated == "periodic":
                    # 🛑 Do NOT invent a periodic event here. `kind='periodic'`
                    # asserts cannot-miss and (by default) cannot-crit, so
                    # synthesising one from a coefficient with no decoded
                    # periodic flat would manufacture mechanics from nothing.
                    notes_by_key.setdefault(k, []).append(
                        f"coefficient term {t.get('term')} is STATED as the "
                        f"periodic component of spell {src}, but no periodic "
                        "flat was decoded for it — attached to the direct event "
                        "rather than inventing a periodic one. Real gap: the "
                        "tick this scales is not in our data")
            elif periodic_k in groups:
                k = periodic_k
            else:
                # coefficient with no flat anywhere: its own direct event
                k = direct_k
                groups.setdefault(k, {"src": src, "via": via, "kind": "direct",
                                      "school": t.get("source_school"),
                                      "tick": None,
                                      "delivery": t.get("trigger_delivery"),
                                      "terms": []})
            groups[k]["terms"].append(t)

        out = []
        for k, g in groups.items():
            attributed = g["via"] != "self"
            fields, fnotes = self._fields_for(g["src"], attributed)
            out.append(AbilityEvent(
                key=k, source_spell_id=g["src"], via=g["via"], kind=g["kind"],
                school=g["school"] or self.school, terms=g["terms"],
                fields=fields, tick_interval_seconds=g["tick"],
                delivery=g.get("delivery"), is_attributed=attributed,
                notes=notes_by_key.get(k, []) + fnotes))
        # deterministic order: own events first, then attributed
        out.sort(key=lambda e: (e.is_attributed, e.kind != "direct", e.key))
        self._events_cache = out
        return out

    def _fields_for(self, src, attributed):
        """Combat-table fields for the spell that carries an event.

        For the card's own events that is the card's resolved mechanics. For an
        attributed component it is that component's own doc-confirmed overlay —
        Hammer from the Heavens' 4,962-hit "cannot be avoided" is a fact about
        282987, not about the cards that trigger it. Where a component has no
        facts of its own we fall back to the card's and SAY SO, because those
        fields describe a different spell.
        """
        if not attributed:
            return self.fields, []
        own = self.component_fields.get(src)
        if own:
            merged = dict(self.fields)
            merged.update(own)
            merged["is_periodic"] = None   # the card's periodicity is not its own
            return merged, []
        return dict(self.fields), [
            f"attributed component (spell {src}) has no combat-table facts of "
            f"its own — falling back to {self.name}'s, which describe a "
            "DIFFERENT spell (crit table, hit table and avoidance may differ)"]

    # ---------------------------------------------------------------- helpers

    def _primary_event(self):
        evs = self.events()
        if not evs:
            return None
        return evs[0]

    def _crit_table(self, ev, warnings):
        ct = ev.fields.get("crit_table")
        if ct:
            return ct
        guess = "melee" if ev.school == "Physical" else "spell"
        warnings.append(
            f"crit_table unconfirmed for {self.name} ({self.spell_id}) event "
            f"{ev.key} — heuristic '{guess}' from school {ev.school!r} "
            "(Holystrike precedent: hybrids crit on the spell table); "
            "verify per parse")
        return guess

    def _hit_table(self, ev, warnings):
        ht = ev.fields.get("hit_table")
        if ht:
            return ht
        guess = "melee" if ev.school == "Physical" else "spell"
        warnings.append(
            f"hit_table unconfirmed for {self.name} ({self.spell_id}) event "
            f"{ev.key} — heuristic '{guess}' from school; crit and hit tables "
            "are INDEPENDENT rolls (primer §5), never inferred from each other")
        return guess

    def _rolls_hit_check(self, ev, warnings):
        r = ev.fields.get("rolls_hit_check")
        if r is not None:
            return bool(r)
        if ev.kind == "periodic":
            # ascension_confirmed: periodic effects cannot miss (primer §5)
            return False
        warnings.append(
            f"rolls_hit_check unconfirmed for {self.name} ({self.spell_id}) "
            f"event {ev.key} — assuming it rolls (the conservative direction "
            "for hit weights); procs riding a landed attack would make this "
            "False")
        return True

    def _can_crit(self, ev, warnings):
        if ev.fields.get("always_crits"):
            return True, True
        if ev.kind == "periodic":
            tcc = ev.fields.get("ticks_can_crit")
            if tcc is None:
                warnings.append(
                    f"{self.name} ({self.spell_id}) event {ev.key} is periodic "
                    "with unconfirmed tick-crit: defaulting to CANNOT crit "
                    "(aura-tick rule, primer §1) — but Molten Earth proves "
                    "exceptions exist; verify from a parse, never the tooltip")
                return False, False
            return bool(tcc), False
        return True, False

    def _avoidance_table(self, ev, char_state, content: ContentProfile, warnings):
        """First-roll table per hit_table/rolls_hit_check, FOR ONE EVENT.
        Returns an AttackTable with a single 'land' segment when nothing rolls."""
        if not self._rolls_hit_check(ev, warnings):
            return ce.AttackTable(segments=[("land", 100.0)])
        ht = self._hit_table(ev, warnings)
        t = content.target
        if ht == "melee":
            def flag(name, default):
                v = ev.fields.get(name)
                if v is None:
                    warnings.append(
                        f"{name} unconfirmed for {self.name} event {ev.key} — "
                        f"assuming {default} (retail default for melee specials)")
                    return default
                return bool(v)
            table = ce.special_attack_table(
                char_state.level, char_state.melee_crit_pct,
                char_state.melee_hit_pct, char_state.expertise_points, t,
                can_be_dodged=flag("can_be_dodged", True),
                can_be_parried=flag("can_be_parried", True),
                can_be_blocked=flag("can_be_blocked", False))
        else:
            cbfr = ev.fields.get("can_be_full_resisted")
            if cbfr is None:
                if ev.school == "Holy":
                    # ascension_confirmed: Holy has no full-resist roll
                    # (primer §1 v17; 4,962-hit HftH sample) — partials remain
                    cbfr = False
                else:
                    cbfr = True
                    warnings.append(
                        f"can_be_full_resisted unconfirmed for {self.name} "
                        f"event {ev.key} — assuming a full-resist roll exists "
                        "(non-Holy school)")
            table = ce.spell_table(char_state.level, char_state.spell_hit_pct,
                                   t, can_be_full_resisted=bool(cbfr))
        warnings.extend(table.warnings)
        return table

    def _components(self, ev, char_state, warnings, include_healing=False,
                    combo_points=0):
        """Per-term damage/healing contributions FOR ONE EVENT. Returns
        (damage_min, damage_max, healing_avg, components).

        Healing terms are ability-level (they carry no event binding), so they
        are counted once, on the primary event only — `include_healing`.
        """
        dmin = dmax = heal = 0.0
        comps = []

        def stat_for(term):
            if term == "AP":
                return char_state.attack_power
            if term == "RAP":
                return char_state.ranged_attack_power
            if term == "SP":
                return char_state.effective_spell_power(ev.school)
            if term in _SCHOOL_SP_TERMS:
                return char_state.effective_spell_power(_SCHOOL_SP_TERMS[term])
            if term == "SPI":
                return char_state.spirit
            if term == "STA":
                return char_state.stamina
            if term == "BH":
                return char_state.bonus_healing
            return None

        # ---- coefficient dedup: rank-sibling text is the rank-correct source.
        # Keyed on (source_spell_id, term), NOT term alone: a card can carry its
        # own SP term AND a trigger-reached component's SP term (Hour of
        # Judgement's own 0.05 vs Hammer from the Heavens' 0.091), and those are
        # different events on different spells — deduping them together would
        # silently drop one.
        by_term = {}
        for t in ev.terms:
            if t.get("term") == "FLAT":
                continue
            by_term.setdefault((t.get("source_spell_id"), t["term"]), []).append(t)

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

        for t in ev.terms:
            term = t.get("term")
            if term == "FLAT":
                via = t.get("via", "self")
                lo = t.get("min")
                hi = t.get("max")
                if lo is None:
                    continue
                cp = t.get("per_combo")
                if cp:
                    # 3e B4 — parameterised. `per_combo` is EffectPointsPerCombo,
                    # a decoded flat added per combo point spent, so the term is
                    # `flat + per_combo * cp`. Before this it was scored at 0 CP
                    # unconditionally: a finisher contributed its base and
                    # nothing else, which is most of a combo-point build's
                    # damage missing.
                    lo = lo + cp * combo_points
                    if hi is not None:
                        hi = hi + cp * combo_points
                    if not combo_points:
                        warnings.append(
                            f"{self.name}: per-combo flat term ({cp:g} per CP) "
                            "scored at 0 COMBO POINTS — this activation was not "
                            "told what CP it was spent at, so the finisher's "
                            "own scaling contributes nothing")
                dmin += lo
                dmax += (hi if hi is not None else lo)
                comps.append({"kind": "flat", "min": lo, "max": hi, "via": via,
                              "confidence": t.get("confidence"),
                              "calibration_anchor":
                                  t.get("confidence") == "confirmed",
                              "evidence_ref": t.get("evidence_ref")})
        for (_src, term), rows in by_term.items():
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
                cps = t.get("cp_scaling")
                if cps and not combo_points:
                    warnings.append(
                        f"{self.name}: {term} carries cp_scaling={cps} and this "
                        "activation was scored at 0 COMBO POINTS — the "
                        "coefficient is applied WITHOUT its CP factor")
                contrib = stat * coeff
                if cps and combo_points:
                    # 3e B4 — the primer's rule is structural, not a preference:
                    # a QUADRATIC finisher goes ~2.8x from 3 CP to 5 CP, not
                    # 1.67x, which is why "never dump below max CP" is a rule.
                    contrib *= (combo_points ** 2 if cps == "quadratic"
                                else combo_points)
                dmin += contrib
                dmax += contrib
                comps.append({"kind": "coefficient", "term": term,
                              "coefficient": coeff, "value": contrib,
                              "source": t.get("source"),
                              "via": t.get("via", "self"),
                              "source_spell_id": t.get("source_spell_id"),
                              "confidence": t.get("confidence", "inferred"),
                              "calibration_anchor": False})

        if include_healing:
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

    def _mitigation(self, ev, char_state, content: ContentProfile, warnings):
        """Multiplicative mitigation factor for ONE EVENT: armor for physical,
        average partial resist for magic. Hybrids still warn — splitting a
        hybrid's own physical/magic halves is a separate problem from splitting
        an ability into events, and is not solved here."""
        t = content.target
        school = ev.school
        if school == "Physical" or ev.fields.get("affected_by_armor"):
            armor = ce.armor_after_penetration(t.armor, char_state.armor_pen_pct)
            return 1.0 - ce.armor_dr_fraction(armor, char_state.level)
        if school in _MAGIC_SCHOOLS:
            res = t.resistances.get(school, 0)
            return 1.0 - ce.average_resist_fraction(res, char_state.level,
                                                    warnings)
        if school:  # named hybrid or composite
            warnings.append(
                f"{self.name} event {ev.key}: hybrid school {school!r} "
                "mitigation not split into physical/magic components — no "
                "mitigation applied; primer §1 says hybrids have an "
                "armor-mitigated half")
        return 1.0

    def _damage_buckets(self, ev, char_state, warnings=None):
        """Which multipliers apply to ONE EVENT, talents included (T4b).

        Applied buckets are surfaced so nothing multiplies invisibly — that is
        the whole point of returning them rather than a single number.
        """
        applied = {}
        for bucket, mult in char_state.damage_multipliers.items():
            if bucket == "all_damage":
                applied[bucket] = mult
            elif bucket == "physical_ability" and ev.school == "Physical":
                applied[bucket] = mult
            elif bucket == "spell_damage" and ev.school in _MAGIC_SCHOOLS:
                applied[bucket] = mult

        talents = getattr(char_state, "talents", None)
        if talents is None:
            if warnings is not None:
                warnings.append(
                    f"{self.name} event {ev.key}: talents NOT modelled on this "
                    "CharState (compute_stats was called without a `conn`) — "
                    "damage is understated by the build's whole multiplier stack")
            return applied
        factor, names = talents.damage_multiplier(
            ev.school, spell_family=self.spell_family,
            class_mask=self.spell_class_mask)
        if factor != 1.0:
            applied["talents"] = factor
            if warnings is not None:
                warnings.append(
                    f"{self.name} event {ev.key}: talent multiplier "
                    f"x{factor:.4f} from {', '.join(names)}")
        if self.spell_class_mask is None and warnings is not None:
            warnings.append(
                f"{self.name} ({self.spell_id}): no SpellClassMask in the "
                "client record, so per-spell talent modifiers (auras 107/108) "
                "could not be matched against it — school-wide amplifiers still "
                "applied. This is a data gap, not a finding that none apply")
        return applied

    def occurrences_per_cast(self, ev):
        """How many times one event fires per activation. Returns (n, note).

        Two different things can make an event repeat, and conflating them was
        the 2a bug:

        * the event is itself a PERIODIC EFFECT (a DoT tick) — repeat count is
          duration / tick interval;
        * the event is a one-shot spell DELIVERED BY a periodic-trigger aura.
          Hammer from the Heavens is not periodic at all: 282987 is an ordinary
          direct spell. What repeats is Hour of Judgement's effect 1, a
          `SPELL_AURA_PERIODIC_TRIGGER_SPELL` at a 500 ms period, which fires
          the pulse over and over for the aura's duration. Counting it once per
          cast understates the ability by its entire pulse count.

        `n is None` means UNKNOWN — refused rather than defaulted to 1, the same
        discipline as the AoE totals refusal.
        """
        dur = ev.fields.get("duration_seconds")

        deliv = ev.delivery or {}
        if deliv.get("periodic"):
            period = deliv.get("period_seconds")
            if period and dur:
                n = max(1, int(dur / period))
                if n > PULSE_COUNT_SANITY_LIMIT:
                    return None, (
                        f"{self.name} event {ev.key}: periodic-trigger delivery "
                        f"computes {n} pulses per cast ({period:g}s period over "
                        f"{dur:g}s), above the {PULSE_COUNT_SANITY_LIMIT} sanity "
                        "limit — REFUSED, not applied and not clamped. Either "
                        "the period field means something else for this spell "
                        "or the duration is wrong; verify before trusting any "
                        "number for this component")
                return n, (
                    f"{self.name} event {ev.key}: delivered by a periodic-"
                    f"trigger aura ({deliv.get('hop')}) at {period:g}s over a "
                    f"{dur:g}s duration -> {n} pulses per cast. The pulse spell "
                    "itself is NOT periodic; the DELIVERY is. Structure is "
                    "corroborated (pooled crawl: 16,491 HftH hits / 4,332 HoJ "
                    "hits = 3.81 vs the 4.00 this model predicts), but the "
                    "ABSOLUTE count rides on the DBC duration and is not itself "
                    "calibrated — see periodic_trigger_delivery_pulse_count")
            return None, (
                f"{self.name} event {ev.key}: delivered by a periodic-trigger "
                f"aura but {'duration' if not dur else 'period'} is unknown — "
                "pulse count REFUSED, not defaulted to 1")

        if ev.kind != "periodic":
            return 1, None
        tick = ev.tick_interval_seconds or ev.fields.get("tick_interval_seconds")

        # 🚨 3g G2 / E14 — A DURATION AND A PERIOD FROM TWO DIFFERENT SPELLS
        # DESCRIBE NO SINGLE AURA. For a trigger-reached component `tick` is the
        # COMPONENT's, while `dur` came from `ev.fields`, which `_fields_for`
        # fills from the CARD whenever the component has no doc-confirmed facts
        # of its own. Absolute Zero divided the card's 12.0s by the triggered
        # spell's 0.001s tick and scored 12,000 ticks for one cast — 92% of the
        # frost-mage fixture's damage.
        #
        # 🛑 Measured across the frozen cohort (1,055 spell ids): 12 events are
        # built this way and the two durations DISAGREE IN ELEVEN OF THEM. So
        # this was never a one-spell defect; Absolute Zero is only where the
        # disagreement is four orders of magnitude rather than one tick.
        #
        # The fix STOPS THE MIXING rather than detecting it, because the
        # component's own duration is one join away (`duration_index` ->
        # `dbc_spellduration`, which the card has always used). Refusing would
        # have fixed the loud case by throwing away eleven working numbers.
        dur_owner = self.spell_id
        if ev.is_attributed and ev.source_spell_id is not None:
            own = self.component_durations.get(ev.source_spell_id)
            if own is not None:
                dur, dur_owner = own, ev.source_spell_id
            elif tick and dur:
                # Genuinely unknowable: the component states a period but no
                # duration of its own, so the only duration available belongs to
                # a different spell. THIS is where the work order's refusal
                # belongs, and it names both spells.
                return None, (
                    f"{self.name} event {ev.key}: REFUSED — the tick interval "
                    f"({tick:g}s) is spell {ev.source_spell_id}'s and the only "
                    f"duration available ({dur:g}s) is spell {self.spell_id}'s. "
                    "A duration and a period from two different spells describe "
                    "no single aura, and spell "
                    f"{ev.source_spell_id} states no duration of its own. Not "
                    "defaulted, not clamped")

        if tick and dur:
            # A non-positive duration is the DBC's sentinel, not a measurement
            # (92557 reads -0.001s). Refused rather than floored to one tick,
            # which would look like a reading.
            if dur <= 0:
                return None, (
                    f"{self.name} event {ev.key}: REFUSED — spell {dur_owner} "
                    f"states a non-positive duration ({dur:g}s), which is the "
                    "DBC's 'no value' sentinel rather than a measurement")
            n = max(1, round(dur / tick))
            # The SAME limit the periodic-TRIGGER-DELIVERY branch above has
            # enforced since 2b. It was never applied to its sibling — E14 is an
            # unapplied guard, not a missing one.
            if n > PULSE_COUNT_SANITY_LIMIT:
                return None, (
                    f"{self.name} event {ev.key}: {n} ticks per cast "
                    f"({tick:g}s tick over a {dur:g}s duration, both from spell "
                    f"{dur_owner}), above the {PULSE_COUNT_SANITY_LIMIT} sanity "
                    "limit — REFUSED, not applied and not clamped. Either the "
                    "period field means something else for this spell or the "
                    "duration is wrong; verify before trusting any number for "
                    "this component")
            return n, None
        return None, (
            f"{self.name} event {ev.key}: periodic with "
            f"{'no duration' if not dur else 'no tick interval'} — tick count "
            "per cast is UNKNOWN and is REFUSED, not defaulted to 1; the "
            "per-cast total excludes it and lists it in unresolved_events")

    # ------------------------------------------------------------- public API

    def expected_hit(self, char_state, content: ContentProfile,
                     rng=None, event=None, combo_points=0) -> ExpectedHitResult:
        """Expected value/variance for ONE OCCURRENCE of ONE event.

        `combo_points` (3e B4) is the CP the activation is spent at. It defaults
        to **0**, which is what every caller did implicitly before — a finisher's
        `per_combo` flat and its `cp_scaling` coefficient were both scored as if
        the ability were pressed at zero combo points, i.e. a finisher's entire
        reason for existing contributed nothing. The value comes from the APL's
        own gate, not from a guess: `apl_gen` holds finishers to
        `MAX_COMBO_POINTS`, so that is what they are scored at.

        ⚠ 2b changed what this means. In 2a it summed every damage term the
        card could reach — its own direct hit, its own DoT tick and any
        trigger-reached pulse — into a single number resolved under a single
        avoidance roll and a single crit roll. Those are different events on
        different spells with different tables, so the sum was not a quantity
        that occurs in the game. It now resolves ONE event (defaulting to the
        primary one); `expected_cast` composes them into a per-activation total.
        """
        ev = event or self._primary_event()
        if ev is None:
            return ExpectedHitResult(
                mean=0.0, variance=0.0, mean_healing=0.0, breakdown={},
                per_metric={}, components=[], applied_multipliers={},
                warnings=list(self.resolution_warnings) + [
                    f"{self.name} ({self.spell_id}): no damage events resolve — "
                    "0 because nothing is KNOWN, not because it does nothing"])

        warnings = list(self.resolution_warnings) + list(ev.notes)
        table = self._avoidance_table(ev, char_state, content, warnings)
        # 3g G1 / E13 — `probabilities()` returns FRACTIONS now, so the `/100.0`
        # this line used to carry is gone. This consumer was the CORRECT one all
        # along: it divided, `swings.expected_swing` did not, and the two had
        # disagreed about the unit of the same function's return value since
        # both were written.
        probs = table.probabilities()
        p_land = probs.get("land", probs.get("hit", 0.0) + probs.get("crit", 0.0)
                           + probs.get("glancing", 0.0))

        can_crit, always = self._can_crit(ev, warnings)
        talents = getattr(char_state, "talents", None)
        # 🛑 In sheet mode the supplied crit is FINAL and already contains every
        # talent's contribution, so adding the talent crit bonus on top would
        # double-count it. compute_stats records which mode produced this state.
        sheet_mode = any("treated as FINAL" in w for w in char_state.warnings)
        talent_crit = 0.0
        if talents is not None and not sheet_mode:
            talent_crit = talents.crit_bonus(
                ev.school, self._crit_table(ev, []) if can_crit else "spell")
        if can_crit and not always:
            ctable = self._crit_table(ev, warnings)
            crit_pct = (char_state.melee_crit_pct if ctable == "melee"
                        else char_state.spell_crit_pct) + talent_crit
            p_crit = min(1.0, max(0.0, crit_pct / 100.0))
            mult = ce.crit_multiplier(
                ctable, ev.fields.get("crit_damage_multiplier"))
        elif always:
            p_crit, mult = 1.0, ce.crit_multiplier(
                self._crit_table(ev, warnings),
                ev.fields.get("crit_damage_multiplier"))
        else:
            p_crit, mult = 0.0, 1.0
        crit_dmg_bonus = char_state.ability_crit_damage_bonus
        if talents is not None:
            crit_dmg_bonus += talents.crit_damage_bonus(ev.school) / 100.0
        mult += crit_dmg_bonus if p_crit else 0.0
        if talent_crit:
            warnings.append(
                f"{self.name} event {ev.key}: talent crit +{talent_crit:g} "
                "points (school/table-scoped, applied here rather than folded "
                "into CharState)")

        primary = self._primary_event()
        dmin, dmax, heal, comps = self._components(
            ev, char_state, warnings, include_healing=(ev is primary),
            combo_points=combo_points)
        mitigation = self._mitigation(ev, char_state, content, warnings)
        buckets = self._damage_buckets(ev, char_state, warnings)
        bucket_mult = 1.0
        for m in buckets.values():
            bucket_mult *= m

        base_avg = (dmin + dmax) / 2.0
        # The weapon-percent share of the base, kept separately because a
        # talent modifier can reach one half and not the other (3m Block B).
        # A "weapon" comp always carries min/max (the weapon roll x coefficient);
        # every other kind carries a single `value` or a flat min/max pair.
        base_weapon_avg = sum(((c["min"] + c["max"]) / 2.0)
                              for c in comps if c.get("kind") == "weapon")
        scale = mitigation * bucket_mult
        e_crit_factor = 1.0 + p_crit * (mult - 1.0)
        mean = p_land * base_avg * scale * e_crit_factor
        # `3k` B3 — the damage dealt BY critical strikes, as opposed to the
        # expected damage of a hit that might crit. Both factors are already in
        # hand; computing it here rather than in the caller keeps the crit model
        # in one place. Righteous Vengeance is 30% OF A CRIT, so it needs this
        # and not `mean`.
        crit_damage_each = p_land * base_avg * scale * p_crit * mult

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
        if ev.is_attributed:
            warnings.append(
                f"{self.name} event {ev.key}: magnitude ATTRIBUTED from trigger "
                f"target {ev.source_spell_id} at confidence=inferred (bounded "
                "walk) — real, but never a calibration anchor")

        n = content.target.count
        if n > 1:
            cap = ev.fields.get("max_targets") or ev.fields.get("cleave_fixed_n")
            if ev.fields.get("aoe_radius") or cap:
                if cap is None:
                    warnings.append(
                        f"{self.name} event {ev.key}: AoE with no "
                        f"max_targets/falloff data — per-target value reported; "
                        f"total at {n} targets is UNKNOWN, not per_target*n "
                        "(PHASE_2 T3: three different split behaviours exist)")
            # per-event result stays per-target; tiers own target math

        return ExpectedHitResult(
            mean=mean, variance=variance, mean_healing=heal * p_land,
            breakdown={
                "event_key": ev.key, "event_kind": ev.kind,
                "event_school": ev.school,
                "source_spell_id": ev.source_spell_id,
                "p_land": p_land, "p_crit_given_land": p_crit,
                "avoidance": {k: v / 100.0 for k, v in probs.items()
                              if k not in ("land", "hit", "crit")},
                "crit_multiplier": mult, "crit_damage_each": crit_damage_each,
                "mitigation_factor": mitigation,
                "base_min": dmin, "base_max": dmax,
                # 🆕 3m B — the base split by COMPONENT KIND. A weapon-percent
                # component and a flat/coefficient component are different
                # quantities that a talent modifier may reach separately: the
                # 2026-08-10 server fix makes Improved Cleave multiply the
                # BONUS term only, leaving the weapon term alone. Carried in the
                # breakdown so the split is auditable per event rather than
                # re-derived, and so the delta can be predicted before the
                # change lands.
                "base_weapon_avg": base_weapon_avg,
                "base_bonus_avg": base_avg - base_weapon_avg,
            },
            per_metric={Metric.DAMAGE_DONE: mean,
                        Metric.HEALING_DONE: heal * p_land},
            components=comps, applied_multipliers=buckets, warnings=warnings)

    def roll_hit(self, char_state, content: ContentProfile, rng,
                 event=None) -> HitResult:
        """One RNG resolution of ONE OCCURRENCE of one event.
        `mean(roll_hit x N)` must converge on `expected_hit().mean` for the
        same event — asserted by tools/audit/check_sim_engine.py."""
        ev = event or self._primary_event()
        if ev is None:
            return HitResult(outcome="none", damage=0.0)
        warnings = []
        table = self._avoidance_table(ev, char_state, content, warnings)
        outcome = table.roll(rng)
        if outcome not in ("land", "hit", "crit", "glancing"):
            return HitResult(outcome=outcome, damage=0.0)

        primary = self._primary_event()
        dmin, dmax, heal, _ = self._components(
            ev, char_state, warnings, include_healing=(ev is primary))
        mitigation = self._mitigation(ev, char_state, content, warnings)
        bucket_mult = 1.0
        for m in self._damage_buckets(ev, char_state).values():
            bucket_mult *= m
        dmg = rng.uniform(dmin, dmax) * mitigation * bucket_mult

        can_crit, always = self._can_crit(ev, warnings)
        # Talent crit and crit-damage must be read the SAME way here as in
        # expected_hit, or the two tiers silently diverge — which is precisely
        # what the mean(roll_hit x N) ~= expected_hit assertion exists to catch.
        talents = getattr(char_state, "talents", None)
        sheet_mode = any("treated as FINAL" in w for w in char_state.warnings)
        crit = False
        if can_crit:
            ctable = self._crit_table(ev, warnings)
            crit_pct = (char_state.melee_crit_pct if ctable == "melee"
                        else char_state.spell_crit_pct)
            if talents is not None and not sheet_mode:
                crit_pct += talents.crit_bonus(ev.school, ctable)
            crit = always or rng.uniform(0.0, 100.0) < crit_pct
            if crit:
                mult = ce.crit_multiplier(
                    ctable, ev.fields.get("crit_damage_multiplier"))
                bonus = char_state.ability_crit_damage_bonus
                if talents is not None:
                    bonus += talents.crit_damage_bonus(ev.school) / 100.0
                dmg *= mult + bonus
        return HitResult(outcome="crit" if crit else "hit", damage=dmg,
                         healing=heal)

    # ------------------------------------------------------- per-cast totals

    def expected_cast(self, char_state, content: ContentProfile,
                      combo_points=0) -> ExpectedCastResult:
        """One full activation: every event at its own occurrence count.

        Variance sums across events under an INDEPENDENCE assumption (each
        event rolls its own avoidance and crit). That is right for a DoT tick
        vs a direct hit; it would understate variance if two events shared a
        roll, which nothing in the current data does.

        `combo_points` (3e B4) is passed through to every event — see
        `expected_hit`. Default 0 preserves every existing caller's behaviour.
        """
        total = var = heal = 0.0
        per_event, unresolved, warnings = [], [], []
        for ev in self.events():
            res = self.expected_hit(char_state, content, event=ev,
                                    combo_points=combo_points)
            warnings.extend(res.warnings)
            n, note = self.occurrences_per_cast(ev)
            if note:
                warnings.append(note)
            if n is None:
                unresolved.append({"event_key": ev.key, "reason": note,
                                   "mean_each": res.mean})
                continue
            total += res.mean * n
            var += res.variance * n
            heal += res.mean_healing * n
            per_event.append({
                "event_key": ev.key, "kind": ev.kind, "school": ev.school,
                "source_spell_id": ev.source_spell_id,
                "via": ev.via, "attributed": ev.is_attributed,
                "occurrences": n, "mean_each": res.mean,
                "mean_total": res.mean * n,
                "p_land": res.breakdown.get("p_land"),
                "p_crit": res.breakdown.get("p_crit_given_land"),
                # 3m B — the weapon/bonus base split, carried per event.
                "base_weapon_avg": res.breakdown.get("base_weapon_avg"),
                "base_bonus_avg": res.breakdown.get("base_bonus_avg"),
                # ...and WHICH multipliers were applied to it. This was only
                # ever reachable through `res.warnings`, which the gate artifact
                # truncates to 8 entries ALPHABETICALLY — so "Bladestorm event
                # ..." survived and "Lightbound Cleave event ..." did not, and
                # the question "is Improved Cleave actually reaching this
                # ability" could not be answered from the committed artifact.
                "applied_multipliers": dict(res.applied_multipliers or {}),
                # 🚨 `3k` B3 — THE KEY `tiers.py` HAS ALWAYS READ AND NOTHING
                # HAS EVER WRITTEN. `_add_swing_sources` derives Righteous
                # Vengeance as 30% of the rotation's crit damage via
                # `ev.get("crit_damage")`; that returned None on every event of
                # every ability, so the sum was always 0.0, the
                # `if crit_damage > 0` branch never fired, and RV was modelled
                # as zero for every character since `2e`. Measured before the
                # fix: 0 sim rows for 61840 across the whole cohort, against 9
                # cohort characters logging it.
                # Not a new quantity — `expected_hit` already computes both
                # factors; this only stops discarding them.
                "crit_damage": res.breakdown.get("crit_damage_each", 0.0) * n,
                "crit_multiplier": res.breakdown.get("crit_multiplier"),
            })
        if unresolved:
            warnings.append(
                f"{self.name}: per-cast total EXCLUDES {len(unresolved)} event(s) "
                "whose occurrence count is unknown — the number below is a "
                "LOWER BOUND, not the ability's output")
        return ExpectedCastResult(
            mean=total, variance=var, mean_healing=heal, per_event=per_event,
            unresolved_events=unresolved, warnings=warnings)

    def roll_cast(self, char_state, content: ContentProfile, rng):
        """One RNG activation: rolls every event its own number of times.
        `mean(roll_cast x N)` must converge on `expected_cast().mean`."""
        total = heal = 0.0
        for ev in self.events():
            n, _ = self.occurrences_per_cast(ev)
            if n is None:
                continue
            for _ in range(n):
                r = self.roll_hit(char_state, content, rng, event=ev)
                total += r.damage
                heal += r.healing if r.outcome in ("hit", "crit") else 0.0
        return HitResult(outcome="cast", damage=total, healing=heal)

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
            # Combat-table facts are RANK-INVARIANT properties of an ability —
            # a spell does not start critting on a different table at rank 5 —
            # but they are seeded against the CATALOG id, which is the rank the
            # character does not cast. Without this carry-over, Lightbound
            # Cleave's proc-tested crit_table='spell' was seeded on 907300 and
            # then thrown away the moment the resolver redirected to 907304,
            # falling back to a heuristic guess in place of a measurement.
            carried = {f: (vt if vt is not None else vr) for f, vt, vr in
                       conn.execute("SELECT field, value_text, value_real FROM "
                                    "doc_confirmed_mechanics WHERE spell_id = ?",
                                    (int(spell_id),)).fetchall()}
            if carried:
                for f, v in carried.items():
                    ability.fields.setdefault(f, v)
                ability.resolution_warnings.append(
                    f"doc-confirmed {sorted(carried)} carried from the catalog "
                    f"id {spell_id} to the rank-{gap['level_rank']} id {target} "
                    "— combat-table facts are rank-invariant, magnitudes are not")
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

    # Combat-table facts for spells this card only REACHES. They belong to the
    # component, not the card: Hammer from the Heavens' 4,962-hit "cannot be
    # avoided" is a fact about 282987, and without this the sim would fall back
    # to "assume it rolls" for a spell we have 4,962 hits of evidence about —
    # inflating the modelled hit weight exactly the way build doc §10 warns.
    component_fields = {}
    sources = {t.get("source_spell_id") for t in damage_terms
               if t.get("via") and t["via"] != "self"}
    for src in sorted(s for s in sources if s):
        rows = conn.execute(
            "SELECT field, value_text, value_real FROM doc_confirmed_mechanics "
            "WHERE spell_id = ?", (src,)).fetchall()
        if rows:
            component_fields[src] = {
                f: (vt if vt is not None else vr) for f, vt, vr in rows}

    # 🆕 3g G2 / E14 — each reached component's OWN duration, so a periodic
    # component's tick count is never `card duration / component tick`. The join
    # is the one `core/spells/mechanics.py:317,335` already performs for the
    # card; it had simply never been performed for a component. Stored raw —
    # including the DBC's non-positive sentinel — so `occurrences_per_cast` can
    # refuse on it by name rather than receive a silently absent key.
    component_durations = {}
    for src in sorted(s for s in sources if s):
        row = conn.execute(
            "SELECT d.duration FROM spell_dbc_raw r "
            "JOIN dbc_spellduration d ON d.id = r.duration_index "
            "WHERE r.id = ?", (src,)).fetchone()
        if row and row[0] is not None:
            component_durations[src] = row[0] / 1000.0

    identity = prof["identity"]

    # SpellFamilyName + SpellClassMask: what a talent's SpellMod class mask is
    # matched against (T4b). Read here so the per-event path needs no db access.
    family, class_mask = None, None
    raw = conn.execute("SELECT effect_json FROM spell_dbc_raw WHERE id = ?",
                       (identity["id"],)).fetchone()
    if raw:
        e = json.loads(raw[0])
        family, class_mask = e.get("SpellClassSet"), e.get("SpellClassMask")

    return ResolvedAbility(
        spell_id=identity["id"], name=identity.get("name") or str(spell_id),
        level=level, school=fields.get("school"), fields=fields,
        confidence=mech.get("confidence", "inferred"),
        damage_terms=damage_terms, healing_terms=healing_terms,
        triggered_components=triggered, rank_note=rank_note,
        resolution_warnings=warnings, component_fields=component_fields,
        component_durations=component_durations,
        spell_family=family, spell_class_mask=class_mask)
