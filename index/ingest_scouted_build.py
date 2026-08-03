"""
ingest_scouted_build.py
------------------------
Loads one or more JSON files produced by scout_ascensionlogs.js
(scoutCharacter() / scoutMany() output) into ascension_index.db as new
tables. Additive — does not touch spells/spell_scaling/owned_cards/etc.

Usage:
    python3 ingest_scouted_build.py scout_David_*.json [more.json ...]

Schema created (idempotent — CREATE TABLE IF NOT EXISTS):

    scouted_characters      one row per character, latest snapshot wins
    scouted_gear             one row per (character, slot, scouted_at)
    scouted_build_entries    one row per (character, tree, entry_id, scouted_at)
                              tree is 'abilities' or 'talents'
    scouted_rankings         one row per (character, phase, zone, boss)
    scouted_capture_history  one row per past capture (report_id linkage
                              for future fight-level digging)

⚠ entry_id vs spells.id: NOT YET CONFIRMED to be the same ID space as our
own ascension_index.db `spells` table. Do not treat a join between
scouted_build_entries.entry_id and spells.id as validated until checked —
e.g. pick a known entry_id (Shadow Bolt = 40050 in the sample capture) and
confirm it resolves to the same ability in spell-export.json. If they
diverge, this script still works standalone (all tooltip text is captured
independently, per_rank_text included in scouted_build_entries.tooltip),
just the cross-reference queries in INDEX_GUIDE.md won't apply as-is.
"""

import json
import sqlite3
import sys
from pathlib import Path

DB_PATH = "ascension_index.db"

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
    tree TEXT,              -- 'abilities' or 'talents'
    entry_id INTEGER,
    name TEXT,
    icon TEXT,
    rank INTEGER,
    max_ranks INTEGER,
    tooltip TEXT,            -- tooltip text AT CURRENT RANK (per_rank_text[rank-1])
    per_rank_tooltip_json TEXT,  -- full array, all ranks, for multi-rank cards
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
        print(f"  [skip] {data.get('name')}: {data['error']} ({source_file})")
        return

    char = data.get("character", {})
    character_id = char.get("id")
    scouted_at = data.get("scouted_at")
    if character_id is None or scouted_at is None:
        print(f"  [skip] malformed record in {source_file}")
        return

    conn.execute(
        """INSERT OR REPLACE INTO scouted_characters
           (character_id, name, class, spec, race, guild_name, primary_stat_token, scouted_at, captured_for_boss)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (
            character_id, char.get("name"), char.get("class"), char.get("spec"),
            char.get("race"), char.get("guild_name"),
            (data.get("primary_stat") or {}).get("token"),
            scouted_at, data.get("captured_for_boss"),
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
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)

    for path_str in sys.argv[1:]:
        path = Path(path_str)
        if not path.exists():
            print(f"  [missing] {path}")
            continue
        payload = json.loads(path.read_text())
        # scoutMany() output is {name: record, ...}; scoutCharacter() output is a single record
        if "scouted_at" in payload:
            records = [payload]
        else:
            records = list(payload.values())
        for rec in records:
            ingest_one(conn, rec, path_str)

    conn.commit()
    conn.close()
    print("Done.")


if __name__ == "__main__":
    main()
