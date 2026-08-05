"""`spell_mechanics` resolution — Phase 1 T4 (session `1b`).

`resolve_spell_mechanics()` merges every source this database holds into one
resolved row per spell, **per field, by §2.2 tier priority**, with provenance and
uncertainty attached to every value. Rules baked into code, not convention:

* 🛑 **Never a magnitude from a `description` string.** Flats/per-level/per-combo
  come from `spell_effect_values` (numeric DBC fields, session `1x`); SP/AP
  coefficients come from `spell_scaling` (tooltip text — the only place Ascension
  states them; `EffectBonusCoefficient` is NOT a coefficient, see `dbc_numeric.py`).
* 🛑 **Never serve a lower-rank value for a higher-rank query.** When the queried
  spell is not the one a character of the requested level casts, the result carries
  an explicit `rank_gap` naming the level-appropriate id(s) — it never silently
  substitutes (Arcane Intellect R1 vs R5 is a ~15× gap).
* **Conflicts are surfaced, never resolved** (§2.3): two sources disagreeing on a
  field put BOTH values in `conflicts` and mark the row `confidence='conflict'`.
* **Level scaling**: `flat + (min(level, max_level or level) − spell_level) ×
  per_level`, where 🛑 `max_level = 0` means UNCAPPED, not "caps at zero" —
  getting that backwards produced a retracted Hammer-from-the-Heavens claim.

Structural fields (cooldown, cast time, school, GCD, next-swing, channel, radius,
periodicity) decode from `spell_dbc_raw` scalars and attribute bits. The bits used
are only the ones validated against doc-confirmed facts in session `1b`:
`ATTR0 0x4` = on-next-swing (Lightbound Cleave ✓), `ATTR0 0x40` = passive
(Improved Cleave ✓), `start_recovery_time` 1500/0 = normal/off-GCD (Divine Storm ✓,
Lightbound Cleave ✓). Unvalidated bits stay undecoded rather than guessed.

Doc-confirmed combat-table facts (crit table, proc ICD…) come from the
`doc_confirmed_mechanics` staging table (`ingest/export/seed_spell_flags.py`) —
they migrated OUT of `spells` columns in `1b` so this table is their one home.
"""
import json

from .ranks import DEFAULT_LEVEL, rank_for_level
from . import dbc_numeric as dn

REALM_DEFAULT = "Darkmoon"   # single-realm database today; parameterised for §2.5

# --- §2.2 source tiers, low ordinal = stronger ---------------------------------
TIER_ORDER = {
    "live_tooltip_or_own_parse": 1,
    "pooled_log_measurement": 2,
    "db_ascension_gg": 3,
    "dbc_numeric_field": 4,
    "changelog": 5,
    "export_tooltip": 6,
    "scouted_tooltip": 7,
}

# Default confidence → uncertainty mapping (PHASE_1 T4). 🛑 A heuristic, not a
# measurement — `basis` says so wherever it surfaces.
UNCERTAINTY_DEFAULTS = {
    "confirmed": 0.0,
    "inferred": 0.10,
    "unverified": 0.25,
}

SCHOOL_BITS = {1: "Physical", 2: "Holy", 4: "Fire", 8: "Nature",
               16: "Frost", 32: "Shadow", 64: "Arcane"}
# Ascension's named hybrid schools, keyed by exact mask (primer §1). An unnamed
# combination is rendered as its components joined with '+', never guessed a name.
HYBRID_SCHOOLS = {3: "Holystrike", 5: "Firestrike", 6: "Holyfire",
                  9: "Stormstrike", 17: "Froststrike", 33: "Shadowstrike",
                  36: "Shadowflame", 65: "Spellstrike"}

POWER_TYPES = {0: "mana", 1: "rage", 2: "focus", 3: "energy",
               5: "runes", 6: "runic"}

ATTR0_ON_NEXT_SWING = 0x4     # validated: Lightbound Cleave carries it
ATTR0_PASSIVE = 0x40          # validated: Improved Cleave carries it
ATTR_EX_CHANNELED = 0x4 | 0x40

# effect ids — semantics validated in 1b against doc-confirmed facts where noted
EFFECT_SCHOOL_DAMAGE = 2
EFFECT_HEAL = 10
EFFECT_WEAPON_PCT = 31        # validated: Divine Storm effect2 = 109 -> 110%
EFFECT_WEAPON_FLAT = 58
EFFECT_TRIGGER = 64
EFFECT_NORMALIZED_WEAPON = 121
DAMAGE_EFFECTS = {EFFECT_SCHOOL_DAMAGE, EFFECT_WEAPON_PCT, EFFECT_WEAPON_FLAT,
                  EFFECT_NORMALIZED_WEAPON}
AURA_PERIODIC_DAMAGE = 3
AURA_PERIODIC_HEAL = 8
AURA_PERIODIC_LEECH = 53
AURA_PERIODIC_DAMAGE_PCT = 89
# stock 3.3.5 SPELL_AURA_PERIODIC_TRIGGER_SPELL. Load-bearing for 2b: a trigger
# hanging off THIS aura fires once per period for the aura's whole duration, so
# a trigger-reached magnitude is NOT "once per cast". Hour of Judgement is the
# live case — effect 1 is aura 23 at a 500 ms period over a 10 s duration.
AURA_PERIODIC_TRIGGER_SPELL = 23
PERIODIC_AURAS = {AURA_PERIODIC_DAMAGE, AURA_PERIODIC_HEAL,
                  AURA_PERIODIC_LEECH, AURA_PERIODIC_DAMAGE_PCT}
AURA_SCHOOL_ABSORB = 69


def scaled_flat(flat, per_level, spell_level, max_level, level):
    """Level-scaled flat value. 🛑 `max_level = 0` means UNCAPPED."""
    if flat is None:
        return None
    if not per_level:
        return flat
    effective = min(level, max_level) if max_level else level
    return flat + (effective - (spell_level or 0)) * per_level


def school_name(mask):
    if not mask:
        return None
    if mask in SCHOOL_BITS:
        return SCHOOL_BITS[mask]
    if mask in HYBRID_SCHOOLS:
        return HYBRID_SCHOOLS[mask]
    parts = [name for bit, name in sorted(SCHOOL_BITS.items()) if mask & bit]
    return "+".join(parts) if parts else None


class _FieldSet:
    """Per-field value + provenance accumulator with §2.3 conflict handling."""

    def __init__(self):
        self.values, self.tiers, self.evidence = {}, {}, {}
        self.confidence, self.uncertainty, self.conflicts = {}, {}, {}

    def set(self, field, value, tier, evidence, confidence="confirmed",
            uncertainty=None):
        if value is None:
            return
        if field in self.values and self.values[field] != value:
            # two sources disagree: keep the stronger tier's value as the display
            # value but record BOTH, and downgrade the field to conflict (§2.3)
            entry = self.conflicts.setdefault(field, [{
                "value": self.values[field], "source_tier": self.tiers[field],
                "evidence_ref": self.evidence[field],
            }])
            entry.append({"value": value, "source_tier": tier,
                          "evidence_ref": evidence})
            if TIER_ORDER.get(tier, 99) < TIER_ORDER.get(self.tiers[field], 99):
                self.values[field], self.tiers[field] = value, tier
                self.evidence[field] = evidence
            self.confidence[field] = "conflict"
            lows = [c["value"] for c in entry if isinstance(c["value"], (int, float))]
            self.uncertainty[field] = {
                "low": min(lows) if lows else None,
                "high": max(lows) if lows else None,
                "basis": "conflict — spans the disagreeing values (§2.3)",
            }
            return
        if field in self.values:
            return  # same value from a second source: keep the first provenance
        self.values[field] = value
        self.tiers[field] = tier
        self.evidence[field] = evidence
        self.confidence[field] = confidence
        if uncertainty is not None:
            self.uncertainty[field] = uncertainty
        else:
            pct = UNCERTAINTY_DEFAULTS.get(confidence, 0.25)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                self.uncertainty[field] = {
                    "low": value * (1 - pct), "high": value * (1 + pct),
                    "basis": f"default_confidence_mapping({confidence}, ±{pct:.0%}) — heuristic, not measured",
                }
            else:
                self.uncertainty[field] = {
                    "low": None, "high": None,
                    "basis": f"default_confidence_mapping({confidence}) — non-numeric",
                }

    def row_confidence(self):
        if any(c == "conflict" for c in self.confidence.values()):
            return "conflict"
        if all(c == "confirmed" for c in self.confidence.values()):
            return "confirmed"
        return "inferred"


def _load_raw(conn, spell_id):
    row = conn.execute(
        """SELECT id, name, attributes, attributes_ex, school_mask, effect_json,
                  spell_level, max_level, recovery_time, category_recovery_time,
                  casting_time_index, duration_index, power_type, mana_cost,
                  mana_cost_pct, proc_type_mask, proc_chance, proc_charges,
                  max_targets, start_recovery_time, source_archive
           FROM spell_dbc_raw WHERE id = ?""", (spell_id,)).fetchone()
    if row is None:
        return None
    keys = ("id", "name", "attributes", "attributes_ex", "school_mask",
            "effect_json", "spell_level", "max_level", "recovery_time",
            "category_recovery_time", "casting_time_index", "duration_index",
            "power_type", "mana_cost", "mana_cost_pct", "proc_type_mask",
            "proc_chance", "proc_charges", "max_targets", "start_recovery_time",
            "source_archive")
    return dict(zip(keys, row))


def _lookup(conn, table, id_col, value_col, key):
    if key is None:
        return None
    row = conn.execute(
        f"SELECT {value_col} FROM {table} WHERE {id_col} = ?", (key,)).fetchone()
    return row[0] if row else None


def _resolve_structure(conn, fs, raw, catalog_type):
    """Tier-4 structural fields from the spell's own DBC record."""
    sid = raw["id"]
    arch = raw["source_archive"]

    def ref(field_name):
        return f"dbc:Spell.dbc:{sid}:{field_name}@{arch}"

    fs.set("school", school_name(raw["school_mask"]), "dbc_numeric_field",
           ref("SchoolMask"))

    cd = max(raw["recovery_time"] or 0, raw["category_recovery_time"] or 0)
    if cd:
        fs.set("cooldown_seconds", cd / 1000.0, "dbc_numeric_field",
               ref("RecoveryTime/CategoryRecoveryTime"))

    base = _lookup(conn, "dbc_spellcasttimes", "id", "base",
                   raw["casting_time_index"])
    if base is not None:
        fs.set("cast_time_seconds", (base or 0) / 1000.0, "dbc_numeric_field",
               ref("CastingTimeIndex"))

    attr0 = raw["attributes"] or 0
    passive = bool(attr0 & ATTR0_PASSIVE)
    if bool(attr0 & ATTR0_ON_NEXT_SWING):
        fs.set("is_next_swing", 1, "dbc_numeric_field",
               ref("Attributes&0x4 (validated: Lightbound Cleave)"))
    if bool((raw["attributes_ex"] or 0) & ATTR_EX_CHANNELED):
        fs.set("is_channeled", 1, "dbc_numeric_field", ref("AttributesEx&0x44"))

    if passive:
        fs.set("gcd_type", "none", "dbc_numeric_field",
               ref("Attributes&0x40 passive (validated: Improved Cleave)"))
    elif (raw["start_recovery_time"] or 0) > 0:
        fs.set("gcd_type", "normal", "dbc_numeric_field",
               ref("StartRecoveryTime"))
    elif catalog_type == "ability":
        fs.set("gcd_type", "off_gcd", "dbc_numeric_field",
               ref("StartRecoveryTime=0 (validated: Lightbound Cleave)"))

    cost, pct = raw["mana_cost"] or 0, raw["mana_cost_pct"] or 0
    if cost or pct:
        fs.set("resource_type", POWER_TYPES.get(raw["power_type"],
                                                str(raw["power_type"])),
               "dbc_numeric_field", ref("PowerType"))
        if cost:
            fs.set("resource_cost", float(cost), "dbc_numeric_field",
                   ref("ManaCost (raw DBC units)"))
        if pct:
            fs.set("resource_cost_pct_base", pct, "dbc_numeric_field",
                   ref("ManaCostPct"))
    elif not passive and catalog_type == "ability":
        fs.set("resource_type", "none", "dbc_numeric_field", ref("ManaCost=0"))

    if raw["max_targets"]:
        fs.set("max_targets", raw["max_targets"], "dbc_numeric_field",
               ref("MaxTargets"))

    pc = raw["proc_chance"] or 0
    if 0 < pc <= 100:
        fs.set("proc_chance_pct", float(pc), "dbc_numeric_field",
               ref("ProcChance"))
    if raw["proc_type_mask"]:
        fs.set("proc_trigger_events", f"proc_type_mask=0x{raw['proc_type_mask']:x}",
               "dbc_numeric_field", ref("ProcTypeMask"))

    # per-effect structure: periodicity, radius, absorb — decoded from the raw
    # slots (not spell_effect_values, which drops magnitude-less slots)
    effects = json.loads(raw["effect_json"]) if raw["effect_json"] else {}
    duration_ms = _lookup(conn, "dbc_spellduration", "id", "duration",
                          raw["duration_index"])
    for i in range(dn.MAX_EFFECTS):
        d = dn.decode_effect(effects, i)
        if d["effect_aura"] in PERIODIC_AURAS and d["aura_period"]:
            fs.set("is_periodic", 1, "dbc_numeric_field",
                   ref(f"EffectAura[{i}]"))
            fs.set("tick_interval_seconds", d["aura_period"] / 1000.0,
                   "dbc_numeric_field", ref(f"EffectAuraPeriod[{i}]"))
        if d["radius_index"]:
            radius = _lookup(conn, "dbc_spellradius", "id", "radius",
                             d["radius_index"])
            if radius:
                fs.set("aoe_radius", float(radius), "dbc_numeric_field",
                       ref(f"EffectRadiusIndex[{i}]"))
        if d["chain_targets"]:
            fs.set("cleave_fixed_n", d["chain_targets"], "dbc_numeric_field",
                   ref(f"EffectChainTargets[{i}]"))
    if duration_ms and duration_ms > 0:
        fs.set("duration_seconds", duration_ms / 1000.0, "dbc_numeric_field",
               ref("DurationIndex"))


def _trigger_delivery(conn, chain):
    """How often a trigger-reached component actually fires (2b).

    `chain` is the evidence string the bounded walk recorded, e.g.
    'trigger:282984->282986->282987;dbc:...'. We walk it hop by hop, and at each
    hop find which of the parent's effect slots names the child in
    `EffectTriggerSpell`. If that slot is a PERIODIC TRIGGER aura (23) with a
    period, the component fires once per period rather than once per cast.

    Returns {'periodic': bool, 'period_seconds': float|None, 'hop': str|None}.
    Nothing is assumed: an unparseable chain returns periodic=False, which is
    the pre-2b behaviour, and the caller says so.
    """
    out = {"periodic": False, "period_seconds": None, "hop": None}
    if not chain or "trigger:" not in chain:
        return out
    try:
        path = chain.split("trigger:", 1)[1].split(";", 1)[0]
        ids = [int(x) for x in path.split("->")]
    except (ValueError, IndexError):
        return out
    for parent, child in zip(ids, ids[1:]):
        row = conn.execute("SELECT effect_json FROM spell_dbc_raw WHERE id = ?",
                           (parent,)).fetchone()
        if not row or not row[0]:
            continue
        try:
            eff = json.loads(row[0])
        except (ValueError, TypeError):
            continue
        trig = eff.get("EffectTriggerSpell") or []
        auras = eff.get("EffectAura") or []
        periods = eff.get("EffectAuraPeriod") or []
        for i, t in enumerate(trig):
            if t != child:
                continue
            aura = auras[i] if i < len(auras) else 0
            period = periods[i] if i < len(periods) else 0
            if aura == AURA_PERIODIC_TRIGGER_SPELL and period:
                out.update(periodic=True, period_seconds=period / 1000.0,
                           hop=f"{parent}->{child}")
                return out
    return out


def _formula_terms(conn, fs, spell_id, level):
    """Magnitude terms: flats from `spell_effect_values`, coefficients from
    `spell_scaling`. Sorted into damage / heal / absorb JSON blocks.

    Coefficients are keyed by the spell that OWNS them, which is not always the
    card. Owner decision 2026-08-05: a trigger-reached component's coefficients
    live on the trigger TARGET, never duplicated onto the cards that reach it —
    truth stays where it is true. So the pull is per COMPONENT SOURCE, not just
    per card: Hour of Judgement (282984) and Hammerdin (282983) both receive
    Hammer from the Heavens' flat via `trigger_hop2`, and its 9.1% SP/AP rows
    live on 282987. Keying only on the card served flat-only magnitudes and
    understated HftH by ~45% (open question
    `trigger_attributed_coefficients_not_in_spell_scaling`).

    The walk is inherited, not re-done: component sources come from the rows
    `spell_effect_values` already holds, so 1b's bounds (depth <= 2, cycle-safe,
    single-path, out-of-catalog targets only) apply unchanged. `hidden_ref`
    sources are deliberately NOT followed — their coefficients already land on
    the card's own id as `source='dbc_hidden_formula'`, and following them too
    would double-count.
    """
    damage, heal, absorb = [], [], []

    rows = conn.execute(
        """SELECT v.source_spell_id, v.effect_index, v.via, v.effect_type,
                  v.effect_aura, v.flat_min, v.flat_max, v.per_level, v.per_combo,
                  v.evidence_ref, v.confidence, v.aura_period,
                  d.spell_level, d.max_level, d.school_mask
           FROM spell_effect_values v
           LEFT JOIN spell_dbc_raw d ON d.id = v.source_spell_id
           WHERE v.spell_id = ?
           ORDER BY v.via, v.source_spell_id, v.effect_index""",
        (spell_id,)).fetchall()
    trigger_sources = {}     # source_spell_id -> (via, evidence_ref)
    delivery_memo = {}

    def delivery_for(via, chain):
        if not str(via or "").startswith("trigger_hop"):
            return None
        if chain not in delivery_memo:
            delivery_memo[chain] = _trigger_delivery(conn, chain)
        return delivery_memo[chain]

    for (src, idx, via, etype, aura, fmin, fmax, per_level, per_combo,
         evidence, confidence, period, sl, ml, smask) in rows:
        if str(via or "").startswith("trigger_hop") and src is not None:
            trigger_sources.setdefault(src, (via, evidence))
        if fmin is None and not per_combo:
            continue
        # A term's own periodicity and school belong to the SPELL THAT CARRIES
        # IT, which is not always the card (2b): Hour of Judgement's own tick,
        # its own direct hit and the Hammer from the Heavens pulse it triggers
        # are three different events that resolve on their own tables. Recorded
        # per term so the ability model can split them (PHASE_2 T5).
        term = {
            "term": "FLAT",
            "min": scaled_flat(fmin, per_level, sl, ml, level),
            "max": scaled_flat(fmax, per_level, sl, ml, level),
            "raw_min": fmin, "raw_max": fmax,
            "per_level": per_level, "spell_level": sl,
            "max_level": ml,   # 0 = UNCAPPED
            "scaled_at_level": level if per_level else None,
            "per_combo": per_combo,
            "via": via, "source_spell_id": src, "effect_index": idx,
            "is_periodic": aura in PERIODIC_AURAS,
            "tick_interval_seconds": (period / 1000.0) if period else None,
            "source_school": school_name(smask) if smask is not None else None,
            "trigger_delivery": delivery_for(via, evidence),
            "evidence_ref": evidence, "confidence": confidence,
        }
        if etype == EFFECT_HEAL or aura == AURA_PERIODIC_HEAL:
            heal.append(term)
        elif aura == AURA_SCHOOL_ABSORB:
            absorb.append(term)
        elif etype in DAMAGE_EFFECTS or aura in (AURA_PERIODIC_DAMAGE,
                                                 AURA_PERIODIC_LEECH):
            if etype == EFFECT_WEAPON_PCT and fmin is not None:
                fs.set("weapon_damage_pct", fmin, "dbc_numeric_field", evidence,
                       confidence="confirmed" if confidence == "confirmed"
                       else "inferred")
                # 🛑 A weapon-percent effect's stored value is a PERCENT, not a
                # damage number. Emitting it as a flat added 65 damage to
                # Lightbound Cleave instead of 65% of a ~627 swing — an error
                # that shrinks with gear and so would have looked like a
                # scaling problem rather than a units problem. It becomes a
                # WEAPON coefficient, which is the term type that multiplies
                # weapon damage.
                term = dict(term, term="WEAPON", coefficient=fmin / 100.0,
                            weapon_pct=fmin, min=None, max=None)
            damage.append(term)

    # SP/AP/RAP coefficients live in tooltip TEXT (tier 6) — the only place
    # Ascension states them. Rank-ramp risk documented per row via source/rank.
    # Pull the card's own coefficients, then each trigger-reached component's
    # from the spell that owns them (see the docstring for why).
    coeff_sources = [(spell_id, "self", None)]
    for src in sorted(trigger_sources):
        via, evidence = trigger_sources[src]
        coeff_sources.append((src, via, evidence))

    for src, via, chain in coeff_sources:
        srow = conn.execute("SELECT school_mask FROM spell_dbc_raw WHERE id = ?",
                            (src,)).fetchone()
        src_school = school_name(srow[0]) if srow and srow[0] is not None else None
        for term_type, coeff, source, cp, rank in conn.execute(
                "SELECT term_type, coefficient, source, cp_scaling_type, rank "
                "FROM spell_scaling WHERE spell_id = ?", (src,)):
            entry = {"term": term_type, "coefficient": coeff,
                     "cp_scaling": cp, "source": source, "rank": rank,
                     "via": via, "source_spell_id": src,
                     "source_school": src_school,
                     "trigger_delivery": delivery_for(via, chain),
                     # Coefficients come from tooltip TEXT, which cannot bind a
                     # term to an effect slot — so a coefficient's direct-vs-
                     # periodic binding is genuinely unknown, not merely
                     # unrecorded. The ability model attaches it to the source's
                     # direct event when one exists and warns when both exist.
                     "is_periodic": None,
                     "confidence": "inferred",
                     "note": ("tier-6 tooltip text; coefficients can ramp with "
                              "rank (1x: 169/1,580 lines vary) — check rank "
                              "before trusting")}
            if via != "self":
                # Attributed, not stated on this card: the coefficient belongs
                # to the trigger target and is reached by the bounded walk.
                entry["evidence_ref"] = chain
                entry["note"] += (
                    f"; ATTRIBUTED from trigger target {src} via {via} — real "
                    "but inferred, never a calibration anchor")
            # BH (bonus healing) is a healing coefficient by definition — the 1c
            # extraction widening added it, and it must not masquerade as damage.
            # Every other term (incl. SPI/STA) stays in the damage block with its
            # term label visible; text alone cannot bind a term to an effect slot.
            (heal if term_type == "BH" else damage).append(entry)

    if damage:
        fs.set("damage_formula_terms_json", json.dumps(damage),
               "dbc_numeric_field" if any(t.get("term") == "FLAT" for t in damage)
               else "export_tooltip",
               f"spell_effect_values+spell_scaling for spell {spell_id}",
               confidence="inferred")
        fs.set("effect_type", "damage", "dbc_numeric_field",
               f"effect structure of spell {spell_id}", confidence="inferred")
    if heal:
        fs.set("healing_formula_terms_json", json.dumps(heal),
               "dbc_numeric_field",
               f"spell_effect_values for spell {spell_id}", confidence="inferred")
        if "effect_type" not in fs.values:
            fs.set("effect_type", "heal", "dbc_numeric_field",
                   f"effect structure of spell {spell_id}", confidence="inferred")
    if absorb:
        fs.set("absorb_formula_terms_json", json.dumps(absorb),
               "dbc_numeric_field",
               f"spell_effect_values for spell {spell_id}", confidence="inferred")

    parts = []
    for t in damage:
        if t["term"] == "FLAT" and t["min"] is not None:
            parts.append(f"{t['min']:g}-{t['max']:g}"
                         if t["max"] != t["min"] else f"{t['min']:g}")
        elif t.get("coefficient") is not None:
            parts.append(f"{t['term']}*{t['coefficient']:g}")
    if parts:
        fs.set("damage_formula_text", " + ".join(parts), "dbc_numeric_field",
               f"assembled from terms of spell {spell_id}", confidence="inferred")


def _doc_confirmed(conn, fs, spell_id):
    """Overlay doc-confirmed combat-table facts (staging table, tier 1/2)."""
    try:
        rows = conn.execute(
            """SELECT field, value_text, value_real, source_tier, evidence_ref,
                      confidence
               FROM doc_confirmed_mechanics WHERE spell_id = ?""",
            (spell_id,)).fetchall()
    except Exception:
        return  # staging table absent (partial rebuild) — nothing to overlay
    for field, vtext, vreal, tier, evidence, confidence in rows:
        fs.set(field, vtext if vtext is not None else vreal, tier, evidence,
               confidence=confidence)


def resolve_spell_mechanics(conn, spell_id, rank=None, realm=None, season=None,
                            level=DEFAULT_LEVEL):
    """Resolve one spell's mechanics from every source, per field, by tier.

    Returns a dict: `fields` / `tiers` / `evidence` / `uncertainty` /
    `conflicts` / `confidence`, plus `rank_gap` — 🛑 when the queried spell is not
    what a character of `level` casts, `rank_gap` names the level-appropriate
    id(s) (or reports ambiguity) and the caller must NOT read this row's
    magnitudes as that character's values. `realm`/`season` are accepted for API
    stability (§2.5); the database is single-realm today.
    """
    fs = _FieldSet()
    raw = _load_raw(conn, spell_id)
    catalog = conn.execute("SELECT type FROM spells WHERE id = ?",
                           (spell_id,)).fetchone()
    catalog_type = catalog[0] if catalog else None

    if raw is not None:
        _resolve_structure(conn, fs, raw, catalog_type)
    _formula_terms(conn, fs, spell_id, level)
    _doc_confirmed(conn, fs, spell_id)

    # 🛑 rule 3: never serve a lower-rank value for a higher-rank query
    rank_gap = None
    resolved_rank = 0
    line = rank_for_level(conn, spell_id, level)
    if line is not None:
        resolved_rank = next(
            (r[0] for r in conn.execute(
                "SELECT rank FROM dbc_spell_rank WHERE spell_id = ?",
                (spell_id,))), 0)
        if line["spell_id"] is None:
            rank_gap = {"kind": "no_rank_at_level", "detail": line}
        elif line["spell_id"] != spell_id:
            rank_gap = {
                "kind": "different_rank_at_level",
                "level_spell_id": line["spell_id"],
                "level_rank": line["rank"],
                "queried_rank": resolved_rank,
                "note": ("magnitudes on this row belong to the QUERIED id; the "
                         f"level-{level} character casts {line['spell_id']} "
                         f"(rank {line['rank']}) — resolve that id instead"),
            }

    return {
        "spell_id": spell_id,
        "rank": resolved_rank,
        "name": raw["name"] if raw else None,
        "fields": fs.values,
        "tiers": fs.tiers,
        "evidence": fs.evidence,
        "uncertainty": fs.uncertainty,
        "conflicts": fs.conflicts,
        "confidence": fs.row_confidence(),
        "rank_gap": rank_gap,
    }


# ------------------------------------------------------------------ population

COLUMNS = (
    "spell_id", "rank", "realm", "season",
    "resource_type", "resource_cost", "resource_cost_pct_base",
    "cooldown_seconds", "cooldown_category", "gcd_type", "cast_time_seconds",
    "is_channeled", "is_next_swing", "charges", "charge_recharge_seconds",
    "effect_type", "school", "damage_formula_text", "damage_formula_terms_json",
    "healing_formula_terms_json", "absorb_formula_terms_json", "mitigation_pct",
    "threat_modifier", "weapon_damage_pct", "normalized_weapon_speed",
    "crit_table", "hit_table", "rolls_hit_check", "can_be_dodged",
    "can_be_parried", "can_be_blocked", "can_glance", "can_be_full_resisted",
    "affected_by_armor", "crit_damage_multiplier", "always_crits",
    "proc_chance_pct", "proc_ppm", "proc_icd_seconds", "proc_trigger_events",
    "can_proc_from_off_gcd", "max_targets", "damage_split_behavior",
    "cleave_fixed_n", "aoe_radius", "falloff_pct_per_target",
    "falloff_floor_pct", "is_periodic", "tick_interval_seconds",
    "duration_seconds", "ticks_can_crit", "scales_with_haste",
    "is_ground_effect", "source_tier_json", "evidence_ref_json",
    "uncertainty_json", "conflicts_json", "confidence", "verified_at_patch",
    "last_resolved_at",
)
_MECHANIC_FIELDS = COLUMNS[4:-7]  # the per-field-provenance mechanic columns


def mechanics_row(resolved, realm, season, patch_id, now):
    """Flatten a `resolve_spell_mechanics()` result into an INSERT tuple."""
    f = resolved["fields"]
    values = [resolved["spell_id"], resolved["rank"], realm, season]
    values += [f.get(c) for c in _MECHANIC_FIELDS]
    values += [
        json.dumps(resolved["tiers"]),
        json.dumps(resolved["evidence"]),
        json.dumps(resolved["uncertainty"]),
        json.dumps(resolved["conflicts"]) if resolved["conflicts"] else None,
        resolved["confidence"], patch_id, now,
    ]
    return tuple(values)


def population_targets(conn, level=DEFAULT_LEVEL):
    """Catalog spells plus the UNAMBIGUOUS level-N rank siblings they resolve to.

    Siblings matter because of rule 3: a query about what a level-60 character
    casts is redirected to the sibling id, so the sibling needs a mechanics row.
    Ambiguous lines (1a: 25 of them) contribute no sibling — never tie-broken.
    """
    targets = {r[0] for r in conn.execute("SELECT id FROM spells")}
    from .ranks import catalog_rank_gaps
    ambiguous = 0
    for gap in catalog_rank_gaps(conn, level):
        if gap["ambiguous"]:
            ambiguous += 1
            continue
        targets.add(gap["candidates"][0]["spell_id"])
    return targets, ambiguous


def populate(conn, realm, season, patch_id, now, level=DEFAULT_LEVEL):
    """Resolve and store every population target. Owns the deletion of its own
    output (idempotent re-run)."""
    targets, ambiguous = population_targets(conn, level)
    conn.execute("DELETE FROM spell_mechanics WHERE realm = ? AND season = ?",
                 (realm, season))
    placeholders = ",".join("?" * len(COLUMNS))
    sql = f"INSERT INTO spell_mechanics ({','.join(COLUMNS)}) VALUES ({placeholders})"

    stats = {"rows": 0, "with_conflict": 0, "with_rank_gap": 0,
             "ambiguous_lines_skipped": ambiguous, "empty": 0}
    for spell_id in sorted(targets):
        resolved = resolve_spell_mechanics(conn, spell_id, level=level)
        if not resolved["fields"]:
            stats["empty"] += 1
            continue
        conn.execute(sql, mechanics_row(resolved, realm, season, patch_id, now))
        stats["rows"] += 1
        stats["with_conflict"] += bool(resolved["conflicts"])
        stats["with_rank_gap"] += bool(resolved["rank_gap"])
    return stats


# ------------------------------------------- spell_scaling rank migration (T4)

def migrate_spell_scaling_ranks(conn, level=DEFAULT_LEVEL):
    """Rank-key `spell_scaling` (1x verdict: coefficients DO scale with rank).

    1. Stamp every existing row with its spell's own rank label from
       `dbc_spell_rank` (0 when the spell is not in a rank line).
    2. Insert the level-N sibling's own text coefficients as new rows
       (`source='dbc_rank_sibling_text'`), so a query for the spell a level-60
       character actually casts finds that rank's coefficient — including the
       seven catalog entries measured wrong today (Sun Down 0.4 → 1.3 …).

    ⚠ Reads sibling coefficients from rank-sibling *description text* — the same
    tier-6 source every existing `spell_scaling` row already came from. Flats
    are never read from text (the hard rule is about magnitudes; `spell_scaling`
    holds only coefficients).
    """
    from .rank_scaling import catalog_coefficient_gaps

    conn.execute("""
        UPDATE spell_scaling SET rank = COALESCE(
            (SELECT r.rank FROM dbc_spell_rank r
             WHERE r.spell_id = spell_scaling.spell_id), 0)""")

    conn.execute("DELETE FROM spell_scaling WHERE source = 'dbc_rank_sibling_text'")
    inserted, differing = 0, 0
    for gap in catalog_coefficient_gaps(conn, level):
        if gap["verdict"] not in ("differs", "same"):
            continue
        live_id = gap["live_spell_id"]
        live_rank = gap["candidates"][0]["rank"]
        if gap["verdict"] == "differs":
            differing += 1
        for term_type, coeffs in (gap["live_text"] or {}).items():
            for coeff in coeffs:
                conn.execute(
                    "INSERT INTO spell_scaling (spell_id, term_type, coefficient,"
                    " source, rank) VALUES (?,?,?,?,?)",
                    (live_id, term_type, coeff, "dbc_rank_sibling_text",
                     live_rank))
                inserted += 1
    return {"sibling_rows": inserted, "differing_lines": differing}
