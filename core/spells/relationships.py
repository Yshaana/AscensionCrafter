"""`spell_relationships` population — Phase 1 T5 (session `1b`).

One writer for the relationship table. Edges migrate from the existing staging
tables (`modifier_links`, `talent_amplifiers`, `exclusivity_buckets`) and from
the client's own `EffectTriggerSpell` fields; each keeps its original provenance.

⚠ Deviation from PHASE_1 T5's "migrate and retire", recorded in the session
handoff: the staging tables are KEPT as ingestion inputs (their seed scripts own
them and run earlier in the chain) — what retires is treating them as query
surfaces. `spell_relationships` is the one queryable home for relationships.

## Relation types (enumerated, never free text)

`amplifies_school` edges carry {"school": ...} in `condition_json` and NULL
`target_spell_id` — they resolve against a build at graph time (`graph.py`), and
enter at LOWER confidence than named-list edges (primer §5: named lists outrank
generic wording until proc-tested).

## Bounded trigger attribution (owner decision, 2026-08-05)

`EffectTriggerSpell` is also an attribution path for magnitudes: a card's damage
can live two hops away (Hammerdin → Hour of Judgement aura `282986` → Hammer
from the Heavens `282987`). `attribute_trigger_magnitudes()` walks trigger edges
from each catalog card, **depth ≤ 2, cycle-safe**, and attributes a reached
spell's numeric magnitudes to the card ONLY when:

* the target is reached by **exactly one path** (ambiguity → no attribution),
* the target is **not itself a catalog card** (its magnitude is its own row),
* the card does not already have that target as a magnitude source.

Rows land in `spell_effect_values` with `via='trigger_hop1'/'trigger_hop2'` and
`confidence='inferred'` — never 'confirmed', because "the engine attributes this
triggered spell's damage to the card" is a modelling decision, not a measurement.
The full chain is in `evidence_ref`. A magnitude can never reach the resolver
through an unbounded walk: depth is capped here, in code.
"""
import json

from . import dbc_numeric as dn
from .mechanics import HYBRID_SCHOOLS, SCHOOL_BITS

RELATION_TYPES = (
    "amplifies", "amplifies_school", "triggers", "resets_cooldown",
    "reduces_cooldown", "consumes", "grants_buff", "grants_charges", "enables",
    "requires", "replaces", "borrows_modifiers", "shares_exclusivity_bucket",
    "shares_cooldown_category", "converts_school", "extends_duration",
    "anti_synergy",
)

SCHOOL_NAMES = set(SCHOOL_BITS.values()) | set(HYBRID_SCHOOLS.values())

MAX_TRIGGER_DEPTH = 2   # owner decision 2026-08-05: bounded walk, never deeper

_INSERT = """INSERT OR IGNORE INTO spell_relationships
    (source_spell_id, target_spell_id, target_name, relation_type, magnitude,
     magnitude_unit, condition_json, direction, source_tier, evidence_ref,
     confidence, realm, season, verified_at_patch)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""


def _edge(conn, stamp, source_id, relation, *, target_id=None, target_name=None,
          magnitude=None, magnitude_unit=None, condition=None,
          direction="source_affects_target", source_tier, evidence_ref,
          confidence):
    assert relation in RELATION_TYPES, relation
    conn.execute(_INSERT, (
        source_id, target_id, target_name, relation, magnitude, magnitude_unit,
        json.dumps(condition) if condition else None, direction, source_tier,
        evidence_ref, confidence, stamp["realm"], stamp["season"],
        stamp["patch_id"]))


def populate_borrows(conn, stamp):
    """`modifier_links` (uses-X-modifiers clauses) → `borrows_modifiers` edges.

    Direction is `source_requires_target`: the card's modifier bucket depends on
    the target base ability — talents amplifying the target also amplify the card.
    """
    n = 0
    for spell_id, target_name, target_spell_id, confidence in conn.execute(
            "SELECT spell_id, target_name, target_spell_id, link_confidence "
            "FROM modifier_links WHERE link_type = 'class_tag'"):
        _edge(conn, stamp, spell_id, "borrows_modifiers",
              target_id=target_spell_id, target_name=target_name,
              direction="source_requires_target", source_tier="export_tooltip",
              evidence_ref=f"modifier_links: tooltip 'uses {target_name} modifiers'",
              confidence="confirmed" if confidence.startswith("confirmed")
              else "inferred")
        n += 1
    return n


def _school_tokens(target_effect):
    """If a target string names only schools, return them; else None.

    Handles both a bare school ('Shadowflame') and the 'Fire and Shadow spells'
    generic form. Anything not purely school names returns None.
    """
    text = target_effect.strip()
    for suffix in (" spells", " damage", " spells and abilities"):
        if text.lower().endswith(suffix):
            text = text[: -len(suffix)]
            break
    parts = [p.strip() for chunk in text.split(",") for p in chunk.split(" and ")]
    parts = [p for p in parts if p]
    if parts and all(p in SCHOOL_NAMES for p in parts):
        return parts
    return None


def populate_amplifiers(conn, stamp):
    """`talent_amplifiers` → `amplifies` / `amplifies_school` edges.

    Rows flagged 'needs manual review' contribute NO edges — they stay in the
    staging table awaiting a human read (243 of 347 today). Verbatim
    school-name targets (Shadow and Flame → 'Shadowflame') become
    `amplifies_school` at the row's own confidence; generic school wording
    becomes `amplifies_school` at `inferred` (primer §5). Ability-name targets
    resolve to a spell id only when the name is UNIQUE in the catalog — the
    duplicate-name trap forbids anything looser.
    """
    stats = {"amplifies": 0, "amplifies_school": 0, "skipped_review": 0,
             "unresolved_names": 0}
    name_counts = {}
    for name, count in conn.execute(
            "SELECT name, COUNT(*) FROM spells GROUP BY name"):
        name_counts[name] = count
    ids_by_name = {name: sid for sid, name in
                   conn.execute("SELECT id, name FROM spells")
                   if name_counts.get(name) == 1}

    for talent_id, target_effect, match_type, verified, notes in conn.execute(
            "SELECT talent_spell_id, target_effect, match_type, verified, notes "
            "FROM talent_amplifiers"):
        if notes and "manual review" in notes:
            stats["skipped_review"] += 1
            continue
        confidence = "confirmed" if verified else "inferred"
        schools = _school_tokens(target_effect or "")
        if schools:
            for school in schools:
                _edge(conn, stamp, talent_id, "amplifies_school",
                      condition={"school": school, "match_type": match_type},
                      source_tier="export_tooltip",
                      evidence_ref=f"talent_amplifiers: '{target_effect}'",
                      # generic school wording never enters above inferred
                      confidence=confidence if match_type == "verbatim"
                      else "inferred")
                stats["amplifies_school"] += 1
            continue
        for token in (t.strip() for t in (target_effect or "").split(",")):
            if not token:
                continue
            target_id = ids_by_name.get(token)
            if target_id is None:
                stats["unresolved_names"] += 1
            _edge(conn, stamp, talent_id, "amplifies", target_id=target_id,
                  target_name=token, source_tier="export_tooltip",
                  evidence_ref=f"talent_amplifiers: '{target_effect}'",
                  confidence=confidence)
            stats["amplifies"] += 1
    return stats


# Doc-confirmed edges the automated extraction cannot reach — same hand-seed
# discipline as seed_cp_scaling.py. Each entry cites its evidence; nothing here
# is guessed. (Improved Cleave's tooltip extraction lands in manual-review as
# 'Cleave ability', but the magnitude is DBC-confirmed in the build handoff.)
HAND_SEEDED_EDGES = [
    # (source_id, relation, target_id, target_name, magnitude, unit, condition,
    #  evidence, confidence)
    (12329, "amplifies", 845, "Cleave", 40.0, "pct",
     {"rank": 1, "scope": "Cleave's bonus-damage term only, not weapon damage"},
     "build_paladin-hammerdin.md v9: EffectBasePoints R1=39->40%, DBC-confirmed",
     "confirmed"),
    (12950, "amplifies", 845, "Cleave", 80.0, "pct",
     {"rank": 2, "scope": "Cleave's bonus-damage term only, not weapon damage"},
     "build_paladin-hammerdin.md v9: EffectBasePoints R2=79->80%, DBC-confirmed",
     "confirmed"),
    (20496, "amplifies", 845, "Cleave", 120.0, "pct",
     {"rank": 3, "scope": "Cleave's bonus-damage term only, not weapon damage"},
     "build_paladin-hammerdin.md v9: EffectBasePoints R3=119->120%, DBC-confirmed",
     "confirmed"),
]


def populate_hand_seeded(conn, stamp):
    for (src, relation, target_id, target_name, magnitude, unit, condition,
         evidence, confidence) in HAND_SEEDED_EDGES:
        _edge(conn, stamp, src, relation, target_id=target_id,
              target_name=target_name, magnitude=magnitude,
              magnitude_unit=unit, condition=condition,
              source_tier="dbc_numeric_field", evidence_ref=evidence,
              confidence=confidence)
    return len(HAND_SEEDED_EDGES)


def populate_exclusivity(conn, stamp):
    """`exclusivity_buckets` → pairwise `shares_exclusivity_bucket` edges.

    N-way buckets become edges among all members (source_id < target_id, one
    edge per unordered pair) with the bucket identity in `condition_json`.
    """
    buckets = {}
    for bucket_id, spell_id, name, desc, source in conn.execute(
            "SELECT bucket_id, spell_id, bucket_name, bucket_desc, source "
            "FROM exclusivity_buckets"):
        buckets.setdefault(bucket_id, {"name": name, "desc": desc,
                                       "source": source, "members": []})
        buckets[bucket_id]["members"].append(spell_id)

    n = 0
    for bucket_id, b in buckets.items():
        members = sorted(b["members"])
        for i, a in enumerate(members):
            for c in members[i + 1:]:
                _edge(conn, stamp, a, "shares_exclusivity_bucket", target_id=c,
                      condition={"bucket_id": bucket_id,
                                 "bucket_name": b["name"]},
                      source_tier={"patch_note": "changelog",
                                   "tooltip": "export_tooltip",
                                   "doc_confirmed": "live_tooltip_or_own_parse",
                                   }.get(b["source"], "export_tooltip"),
                      evidence_ref=f"exclusivity_buckets #{bucket_id} "
                                   f"({b['name']}): {b['desc'] or ''}"[:200],
                      confidence="confirmed")
                n += 1
    return {"edges": n, "buckets": len(buckets)}


def populate_triggers(conn, stamp):
    """`EffectTriggerSpell` (every extracted DBC record) → `triggers` edges.

    Built from ALL of `spell_dbc_raw`, not only catalog spells — multi-hop
    chains (card → aura → damage spell) need the intermediate spells' edges.
    """
    n = 0
    for spell_id, effect_json, archive in conn.execute(
            "SELECT id, effect_json, source_archive FROM spell_dbc_raw "
            "WHERE effect_json LIKE '%EffectTriggerSpell%'"):
        effects = json.loads(effect_json)
        triggers = effects.get("EffectTriggerSpell") or []
        for i, target in enumerate(triggers):
            if not target or target == spell_id:
                continue
            _edge(conn, stamp, spell_id, "triggers", target_id=target,
                  condition={"effect_index": i},
                  source_tier="dbc_numeric_field",
                  evidence_ref=dn.evidence_ref(spell_id, i, archive)
                  + ":EffectTriggerSpell",
                  confidence="confirmed")
            n += 1
    return n


# ------------------------------------------------- bounded trigger attribution

def trigger_chains(conn, card_id, max_depth=MAX_TRIGGER_DEPTH):
    """All acyclic trigger paths from a card, depth-capped. Returns
    {target_id: [path, ...]} where each path is (card_id, ..., target_id)."""
    edges = {}
    for src, dst in conn.execute(
            "SELECT source_spell_id, target_spell_id FROM spell_relationships "
            "WHERE relation_type = 'triggers' AND target_spell_id IS NOT NULL"):
        edges.setdefault(src, []).append(dst)

    reached = {}
    frontier = [(card_id,)]
    for _depth in range(max_depth):
        next_frontier = []
        for path in frontier:
            for dst in edges.get(path[-1], ()):
                if dst in path:
                    continue  # cycle — never walked through
                new_path = path + (dst,)
                reached.setdefault(dst, []).append(new_path)
                next_frontier.append(new_path)
        frontier = next_frontier
    return reached


def attribute_trigger_magnitudes(conn, stamp, now):
    """Attribute triggered spells' magnitudes to their cards (bounded, flagged).

    Owns its own output: deletes `via LIKE 'trigger_hop%'` rows first.
    """
    conn.execute("DELETE FROM spell_effect_values WHERE via LIKE 'trigger_hop%'")

    catalog_ids = {r[0] for r in conn.execute("SELECT id FROM spells")}
    raw = {r[0]: (r[1], r[2]) for r in conn.execute(
        "SELECT id, effect_json, source_archive FROM spell_dbc_raw")}
    existing = {}
    for spell_id, source_id in conn.execute(
            "SELECT spell_id, source_spell_id FROM spell_effect_values"):
        existing.setdefault(spell_id, set()).add(source_id)

    stats = {"cards_with_attribution": 0, "rows": 0, "ambiguous_skipped": 0,
             "hop1": 0, "hop2": 0}
    insert = ("INSERT OR IGNORE INTO spell_effect_values VALUES ("
              + ",".join("?" * 26) + ")")

    for card_id in sorted(catalog_ids):
        reached = trigger_chains(conn, card_id)
        wrote = False
        for target, paths in reached.items():
            if target in catalog_ids:
                continue  # its magnitude is its own row, never double-attributed
            if len(paths) > 1:
                stats["ambiguous_skipped"] += 1
                continue
            if target in existing.get(card_id, ()):
                continue
            entry = raw.get(target)
            if entry is None:
                continue
            effect_json, archive = entry
            path = paths[0]
            depth = len(path) - 1
            chain = "->".join(str(p) for p in path)
            for d in dn.decode_effects(json.loads(effect_json)):
                if d["flat_min"] is None and not d["per_combo"] \
                        and not d["per_level"]:
                    continue
                conn.execute(insert, (
                    card_id, target, d["effect_index"], f"trigger_hop{depth}",
                    d["effect_type"], d["effect_aura"], d["base_points"],
                    d["die_sides"], d["flat_min"], d["flat_max"],
                    d["per_level"], d["per_combo"], d["bonus_multiplier"],
                    d["trigger_spell"], d["misc_value"], d["misc_value_b"],
                    d["radius_index"], d["aura_period"], d["chain_targets"],
                    "dbc_numeric_field",
                    f"trigger:{chain};"
                    + dn.evidence_ref(target, d["effect_index"], archive),
                    "inferred", stamp["realm"], stamp["season"],
                    stamp["patch_id"], now,
                ))
                stats["rows"] += 1
                stats[f"hop{depth}"] += 1
                wrote = True
        stats["cards_with_attribution"] += wrote
    return stats


def populate_all(conn, stamp, now):
    """Full relationship build. Owns deletion of the whole table (one writer)."""
    conn.execute("DELETE FROM spell_relationships")
    stats = {
        "borrows_modifiers": populate_borrows(conn, stamp),
        "amplifiers": populate_amplifiers(conn, stamp),
        "exclusivity": populate_exclusivity(conn, stamp),
        "triggers": populate_triggers(conn, stamp),
        "hand_seeded": populate_hand_seeded(conn, stamp),
    }
    stats["trigger_attribution"] = attribute_trigger_magnitudes(conn, stamp, now)
    return stats
