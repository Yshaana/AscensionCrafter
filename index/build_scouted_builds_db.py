"""
build_scouted_builds_db.py
----------------------------
Builds index/scouted_builds.db from every JSON file in index/scouted/.

DELIBERATELY SEPARATE from ascension_index.db. Scouted external builds are
reference data that grows every time you scout a new outlier — mixing that
into your own core spell/card index would bloat it and pollute queries
that have nothing to do with scouting. Keep them apart:

    ascension_index.db     <- your own build's spells/cards/talents/facts
    scouted_builds.db      <- other players' captured builds, rebuilt from
                               index/scouted/*.json, same "derived cache,
                               not source of truth" rule as the main index

Like ascension_index.db itself, this is a rebuildable artifact — the real
source of truth is the committed JSON in index/scouted/. Safe to delete
scouted_builds.db and regenerate anytime:

    python3 build_scouted_builds_db.py

No file arguments needed — it scans index/scouted/*.json automatically
(unlike the old per-file ingest_scouted_build.py, which this replaces).
"""
import json
import sqlite3
from pathlib import Path

SCOUTED_DIR = Path(__file__).parent / "scouted"
DB_PATH = Path(__file__).parent / "scouted_builds.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS scouted_characters (
    character_id INTEGER,
    name TEXT,
    class TEXT,
    spec TEXT,
    race TEXT,
    guild_name TEXT,
    primary_stat_token TEXT,
    scouted_at TEXT,
    captured_for_boss TEXT,
    source_file TEXT,
    PRIMARY KEY (character_id, scouted_at)
);

CREATE TABLE IF NOT EXISTS scouted_gear (
    character_id INTEGER,
    scouted_at TEXT,
    slot INTEGER,
    item_id INTEGER,
    item_name TEXT,
    quality INTEGER,
    enchant_id INTEGER,
    enchant_name TEXT,
    gem1 INTEGER, gem2 INTEGER, gem3 INTEGER, gem4 INTEGER,
    stats_json TEXT,
    damage_json TEXT,
    drop_source TEXT,
    source_category TEXT,
    tier TEXT,
    PRIMARY KEY (character_id, scouted_at, slot)
);

CREATE TABLE IF NOT EXISTS scouted_build_entries (
    character_id INTEGER,
    scouted_at TEXT,
    tree TEXT,
    entry_id INTEGER,
    name TEXT,
    icon TEXT,
    rank INTEGER,
    max_ranks INTEGER,
    tooltip TEXT,
    per_rank_tooltip_json TEXT,
    PRIMARY KEY (character_id, scouted_at, tree, entry_id)
);

CREATE TABLE IF NOT EXISTS scouted_rankings (
    character_id INTEGER,
    scouted_at TEXT,
    phase INTEGER,
    zone TEXT,
    boss_name TEXT,
    spec TEXT,
    best_dps REAL,
    best_rank_dps INTEGER,
    best_rank_dps_total INTEGER,
    best_rank_dps_percentile REAL,
    fastest_duration_ms INTEGER,
    kills INTEGER,
    PRIMARY KEY (character_id, scouted_at, phase, zone, boss_name)
);

CREATE TABLE IF NOT EXISTS scouted_capture_history (
    character_id INTEGER,
    capture_id TEXT,
    captured_at TEXT,
    boss_name TEXT,
    report_id INTEGER,
    location TEXT,
    success INTEGER,
    PRIMARY KEY (character_id, capture_id)
);
"""


def ingest_one(conn, data, source_file):
    if data.get("error"):
        print(f"  [skip] {data.get('name')}: {data['error']} ({source_file.name})")
        return

    char = data.get("character", {})
    character_id = char.get("id")
    scouted_at = data.get("scouted_at")
    if character_id is None or scouted_at is None:
        print(f"  [skip] malformed record in {source_file.name}")
        return

    conn.execute(
        """INSERT OR REPLACE INTO scouted_characters
           (character_id, name, class, spec, race, guild_name, primary_stat_token,
            scouted_at, captured_for_boss, source_file)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (
            character_id, char.get("name"), char.get("class"), char.get("spec"),
            char.get("race"), char.get("guild_name"),
            (data.get("primary_stat") or {}).get("token"),
            scouted_at, data.get("captured_for_boss"), source_file.name,
        ),
    )

    for item in data.get("gear", []):
        gems = item.get("gems") or {}
        conn.execute(
            """INSERT OR REPLACE INTO scouted_gear
               (character_id, scouted_at, slot, item_id, item_name, quality, enchant_id, enchant_name,
                gem1, gem2, gem3, gem4, stats_json, damage_json, drop_source, source_category, tier)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                character_id, scouted_at, item.get("slot"), item.get("item_id"), item.get("name"),
                item.get("quality"), item.get("enchant_id"), item.get("enchant_name"),
                gems.get("1"), gems.get("2"), gems.get("3"), gems.get("4"),
                json.dumps(item.get("stats")) if item.get("stats") else None,
                json.dumps(item.get("damage")) if item.get("damage") else None,
                item.get("source"), item.get("source_category"), item.get("tier"),
            ),
        )

    for tree_slug, entries in (data.get("build") or {}).items():
        for t in entries:
            per_rank = t.get("per_rank_text") or []
            rank = t.get("rank") or 1
            current_tooltip = per_rank[rank - 1] if 0 < rank <= len(per_rank) else (per_rank[0] if per_rank else None)
            conn.execute(
                """INSERT OR REPLACE INTO scouted_build_entries
                   (character_id, scouted_at, tree, entry_id, name, icon, rank, max_ranks, tooltip, per_rank_tooltip_json)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (
                    character_id, scouted_at, tree_slug, t.get("entry_id"), t.get("name"), t.get("icon"),
                    rank, t.get("max_ranks"), current_tooltip, json.dumps(per_rank) if per_rank else None,
                ),
            )

    for r in data.get("rankings", []):
        zone = r.get("zone")
        phase = r.get("phase")
        for row in r.get("boss_rows", []):
            conn.execute(
                """INSERT OR REPLACE INTO scouted_rankings
                   (character_id, scouted_at, phase, zone, boss_name, spec, best_dps,
                    best_rank_dps, best_rank_dps_total, best_rank_dps_percentile, fastest_duration_ms, kills)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    character_id, scouted_at, phase, zone, row.get("boss_name"), row.get("spec"),
                    row.get("best_dps"), row.get("best_rank_dps"), row.get("best_rank_dps_total"),
                    row.get("best_rank_dps_percentile"), row.get("fastest_duration_ms"), row.get("kills"),
                ),
            )

    for c in data.get("capture_history", []):
        conn.execute(
            """INSERT OR REPLACE INTO scouted_capture_history
               (character_id, capture_id, captured_at, boss_name, report_id, location, success)
               VALUES (?,?,?,?,?,?,?)""",
            (
                character_id, c.get("capture_id"), c.get("captured_at"), c.get("boss_name"),
                c.get("report_id"), c.get("location"), 1 if c.get("success") else 0,
            ),
        )

    print(f"  [ok] {char.get('name')} (id={character_id}): "
          f"{len(data.get('gear', []))} gear, "
          f"{sum(len(v) for v in (data.get('build') or {}).values())} build entries, "
          f"{sum(len(r.get('boss_rows', [])) for r in data.get('rankings', []))} ranking rows")


def main():
    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"Removed stale {DB_PATH.name} — rebuilding fresh from source JSON.")

    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)

    json_files = sorted(SCOUTED_DIR.glob("scouted_*.json"))
    if not json_files:
        print(f"No scout JSON found in {SCOUTED_DIR}/ — nothing to build.")
        return

    for path in json_files:
        payload = json.loads(path.read_text())
        records = [payload] if "scouted_at" in payload else list(payload.values())
        for rec in records:
            ingest_one(conn, rec, path)

    conn.commit()
    conn.close()
    print(f"\nBuilt {DB_PATH} from {len(json_files)} source file(s).")


if __name__ == "__main__":
    main()
