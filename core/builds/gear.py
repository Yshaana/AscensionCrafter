"""Gear data for the sim (Phase 3 Task 4).

🛑 **No `optimize_gearset()`.** Phase 0 Task 9 confirmed BisBeard owns items,
phase tagging and BiS selection, and takes stat weights as a first-class input
(`weightString`). Building a competing optimizer is weeks of work for a worse
result. What this module owns is the half nobody else can produce: the stat
blocks the sim's gear-tier scaling curve needs, and the export that hands our
derived weights to BisBeard.

## Where the item data comes from — and why it is NOT the client's DBCs

Owner decision 2026-08-06 was "client DBC first, it needs nobody's permission."
That route was probed and it **does not carry item stat values**:

* `Item.dbc` (563,308 records, 8 fields) is stock 3.3.5 display data —
  class/subclass/display id/inventory type/sheath. No stats. Expected: in
  3.3.5 item stats live server-side in `item_template`, not in the client.
* `ItemStat.dbc` (1,513,931 records, 39 fields) is a **custom Ascension table
  and it is not a stat block.** Tested against 1,198 items whose real stats
  the crawl already resolves: reading fields 3–22 as `(ITEM_MOD type, value)`
  pairs reproduces the true block exactly **6 times out of 567 overlaps**, and
  no single field equals a real stat value above chance (best 9.2%). Its
  decodable content is display/gating-shaped — f37 is a 1–70 required level,
  f36 an 8000/12000 delay-like constant, f23–f26 floats. Layout otherwise
  unresolved and recorded as an open question rather than guessed at.

So the items table is assembled from `snapshot_gear` — Path B's own fallback,
and the one the recon called "an item database assembled as a byproduct."
Provenance is honest: these stat blocks are **BisBeard's resolution**, carried
through the ascensionlogs armory capture, tier `crawl_resolved_bisbeard`. That
makes cross-validating our weights against BisBeard a check on the *weights*,
not an independent check on the *items* — worth stating before anyone reads
agreement as confirmation.
"""
import json
from collections import defaultdict

ITEMS_SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    item_id INTEGER PRIMARY KEY,
    name TEXT, quality INTEGER, slot INTEGER, item_level INTEGER,
    stats_json TEXT, sockets_json TEXT,
    drop_source TEXT, source_category TEXT, tier TEXT,
    phase_label TEXT,               -- server phase this becomes available, when known
    provenance TEXT NOT NULL,       -- 'crawl_resolved_bisbeard' | 'client_dbc' | 'manual'
    first_seen_at TEXT, seen_count INTEGER
);
CREATE INDEX IF NOT EXISTS idx_items_slot ON items(slot);
"""

# crawl stat key -> the sim's CharState vocabulary (core/sim/weights.py STAT_SETTERS)
STAT_KEY_MAP = {
    "strength": "strength", "agility": "agility", "intellect": "intellect",
    "stamina": "stamina", "spirit": "spirit",
    "spellPower": "spell_power", "attackPower": "attack_power",
    "feralAttackPower": "feral_attack_power",
    "critRating": "crit_rating", "hitRating": "hit_rating",
    "hasteRating": "haste_rating", "expertise": "expertise_rating",
    "armorPenetration": "armor_pen_rating", "resilienceRating": "resilience_rating",
    "mp5": "mp5", "hp5": "hp5", "armor": "armor",
    "defense": "defense_rating", "dodge": "dodge_rating", "parry": "parry_rating",
    "block": "block_rating", "blockValue": "block_value",
    "shieldBlockValue": "block_value",
    "healingPower": "healing_power", "spellPenetration": "spell_penetration",
    "shadowSpellPower": "shadow_spell_power",
    "fireResist": "fire_resist", "frostResist": "frost_resist",
    "shadowResist": "shadow_resist", "natureResist": "nature_resist",
    "arcaneResist": "arcane_resist",
}


def init_items_schema(conn):
    conn.executescript(ITEMS_SCHEMA)


def build_items_from_gear(conn):
    """Dedupe `snapshot_gear` by item_id into `items`. Owns its own deletion."""
    init_items_schema(conn)
    conn.execute("DELETE FROM items WHERE provenance = 'crawl_resolved_bisbeard'")
    rows = conn.execute("""
        SELECT sg.item_id, MIN(sg.item_name), MIN(sg.quality), MIN(sg.slot),
               MIN(sg.item_level), MIN(sg.stats_json), MIN(sg.gems_json),
               MIN(sg.drop_source), MIN(sg.source_category), MIN(sg.tier),
               MIN(cs.captured_at), COUNT(DISTINCT sg.snapshot_id)
        FROM snapshot_gear sg
        JOIN character_snapshots cs ON cs.snapshot_id = sg.snapshot_id
        WHERE sg.item_id IS NOT NULL
        GROUP BY sg.item_id
    """).fetchall()
    conn.executemany(
        """INSERT OR REPLACE INTO items
             (item_id, name, quality, slot, item_level, stats_json, sockets_json,
              drop_source, source_category, tier, phase_label, provenance,
              first_seen_at, seen_count)
           VALUES (?,?,?,?,?,?,?,?,?,?,?, 'crawl_resolved_bisbeard', ?,?)""",
        [(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9],
          None, r[10], r[11]) for r in rows])
    return {"items": len(rows),
            "with_stats": sum(1 for r in rows if r[5]),
            "provenance": "crawl_resolved_bisbeard"}


def normalise_stats(stats_json):
    """Crawl stat block -> the sim's vocabulary. Unknown keys are RETURNED in
    `unmapped`, never dropped silently — a stat we cannot name is a finding."""
    if not stats_json:
        return {}, []
    raw = json.loads(stats_json) if isinstance(stats_json, str) else stats_json
    out, unmapped = {}, []
    for k, v in raw.items():
        key = STAT_KEY_MAP.get(k)
        if key is None:
            unmapped.append(k)
            continue
        out[key] = out.get(key, 0) + v
    return out, unmapped


def gear_tier_stats(conn, *, path=None, role=None, tiers=(("fresh", 0.25),
                                                          ("mid", 0.50),
                                                          ("bis", 0.90))):
    """Fresh / mid / BiS stat blocks, MEASURED from what characters wear.

    Not a hand-invented curve: characters are ranked by the **total stat budget
    their gear actually carries**, and each tier is the stat block of the
    character at that percentile. That keeps the three tiers internally
    consistent (a real person wore all of it) instead of summing per-slot
    bests, which produces a set nobody has.

    ⚠ Ranking deliberately does NOT use `item_level`: it is NULL on most
    crawled rows, so an ilvl ranking sorts by *how much metadata resolved*
    rather than by gear quality — the fresh and mid tiers came back with EMPTY
    stat blocks, which is what caught it.

    ⚠ Phase parameterisation: the corpus is currently all Phase 1, so
    `phase_label` is NULL everywhere and this function does not filter on it.
    S10 Phase 2 starts 2026-08-08; once snapshots straddle the flip, tiers MUST
    be computed per phase or a Phase-1 BiS will be reported as current.
    """
    sql = """
        SELECT cs.snapshot_id, cs.character_id, cs.path,
               COUNT(sg.item_id) AS pieces
        FROM character_snapshots cs
        JOIN snapshot_gear sg ON sg.snapshot_id = cs.snapshot_id
        WHERE sg.stats_json IS NOT NULL
    """
    params = []
    if path:
        sql += " AND lower(cs.path) = lower(?)"
        params.append(path)
    if role:
        sql += " AND lower(COALESCE(cs.spec_role,'')) LIKE lower(?)"
        params.append(f"%{role}%")
    sql += " GROUP BY cs.snapshot_id HAVING pieces >= 12"

    all_unmapped = set()
    scored = []
    for snapshot_id, character_id, snap_path, pieces in conn.execute(sql, params):
        block = defaultdict(float)
        for (stats_json,) in conn.execute(
                "SELECT stats_json FROM snapshot_gear WHERE snapshot_id = ?",
                (snapshot_id,)):
            mapped, unmapped = normalise_stats(stats_json)
            all_unmapped.update(unmapped)
            for k, v in mapped.items():
                block[k] += v
        # budget = the stats a build actually converts into throughput; armor,
        # resistances and health regen are excluded so a tank's plate does not
        # outrank a caster's whole set.
        budget = sum(v for k, v in block.items()
                     if k not in {"armor", "hp5", "fire_resist", "frost_resist",
                                  "shadow_resist", "nature_resist", "arcane_resist"})
        scored.append((budget, snapshot_id, character_id, snap_path, pieces, block))
    scored.sort(key=lambda r: r[0])

    if len(scored) < 8:
        return {"verdict": "insufficient_sample", "population": len(scored),
                "tiers": {}}

    out = {}
    for label, pct in tiers:
        budget, snapshot_id, character_id, snap_path, pieces, block = \
            scored[min(len(scored) - 1, int(len(scored) * pct))]
        out[label] = {
            "percentile": pct, "snapshot_id": snapshot_id,
            "character_id": character_id, "path": snap_path,
            "gear_stat_budget": round(budget, 1), "pieces": pieces,
            "stats": {k: round(v, 1) for k, v in sorted(block.items())},
        }
    return {"verdict": "ok", "population": len(scored), "tiers": out,
            "unmapped_stat_keys": sorted(all_unmapped),
            "provenance": "crawl_resolved_bisbeard",
            "caveat": "single-phase corpus; re-derive per phase after 2026-08-08"}


def export_stat_weights(weights, *, target="bisbeard", normalise_to=None):
    """Emit derived weights in an external optimizer's input format.

    BisBeard's chunk exposes `weightString`, `configStatWeights`,
    `normalizedWeights` — the encoding itself is NOT documented anywhere we can
    read, and Phase 0 stopped short of probing for it. So this emits the two
    forms that are unambiguous: a `key=value` string and JSON. If the real
    `weightString` grammar is ever learned, add it as another target rather
    than guessing at it now.
    """
    if normalise_to and normalise_to in weights and weights[normalise_to]:
        base = weights[normalise_to]
        weights = {k: v / base for k, v in weights.items()}
    ordered = sorted(weights.items(), key=lambda kv: -abs(kv[1]))
    if target == "json":
        return json.dumps({k: round(v, 4) for k, v in ordered}, indent=1)
    if target == "bisbeard":
        return ",".join(f"{k}={v:.4f}" for k, v in ordered if v)
    raise ValueError(f"unknown target {target!r} — add it rather than guessing "
                     f"at an undocumented encoding")


def rank_items(conn, slot, stat_weights, *, limit=20, min_seen=1):
    """Items in a slot scored by our own weights. A REPORT, not an optimizer —
    it exists to cross-validate weights against `item_usage()` (Task 3): if the
    weight-ranked list disagrees with what every top performer wears, the
    weights or the item data are wrong, and that is a finding either way.

    ⚠ **Weapon damage is not in `stats_json`**, so for weapon slots this score
    omits the single largest term (the build doc weights it 2.6). A weapon
    ranking from this function is a stat-stick ranking and must not be read as
    a weapon ranking — which is exactly why it disagrees with `item_usage` on
    slot 16."""
    out = []
    for item_id, name, stats_json, ilvl, seen, tier in conn.execute(
            "SELECT item_id, name, stats_json, item_level, seen_count, tier "
            "FROM items WHERE slot = ? AND stats_json IS NOT NULL AND seen_count >= ?",
            (slot, min_seen)):
        stats, _unmapped = normalise_stats(stats_json)
        score = sum(stat_weights.get(k, 0.0) * v for k, v in stats.items())
        out.append({"item_id": item_id, "name": name, "item_level": ilvl,
                    "tier": tier, "wearers": seen, "score": round(score, 1),
                    "stats": stats})
    out.sort(key=lambda r: r["score"], reverse=True)
    return out[:limit]
