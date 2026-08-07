#!/usr/bin/env python3
"""Load the committed client extracts into the database — no game client needed.

`build_dbc_index.py` reads the client's MPQ archives directly and needs the game
installed plus a built StormLib. It also **exports everything it learned** to two
committed JSON files, precisely so that every other session — a fresh clone, a
machine without the client, a future web host — can still have the `dbc_*` tables.
This script is that other path, and it is the one in the routine rebuild chain.

    py ingest/dbc/load_extract.py

Sources (both committed, both irreplaceable without the client):

  `data/source/dbc/dbc-ascension-extract.json`
      dbc_character_advancement  — **the crosswalk**, 10,231 cards
      dbc_spell_rank             — 42,606 ranked spells in 12,779 lines
      dbc_spell_class            — class per spell, from renamed skill lines
      dbc_gt_tables              — rating->percent conversions for Phase 2
      dbc_skill_line / dbc_skilllineability

  `data/source/dbc/dbc-extract.json`
      spell_dbc_raw              — the client's own spell records
      plus the support tables and the hidden-formula scaling rows

Each table is dropped and rebuilt from the JSON, so this is idempotent — the
failure mode Phase 0 found three times (a script deriving rows without owning the
deletion of its own previous output) cannot happen here.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from config import (  # noqa: E402
    DBC_ASCENSION_EXTRACT_JSON, DBC_EXTRACT_JSON, DB_PATH, ensure_derived_dir,
)
import season_config  # noqa: E402  - realm/season constants (3d A1)
from core.db.connection import connect, transaction  # noqa: E402

# columns whose values are stored as JSON/text and must not be coerced
_PK = {
    "dbc_character_advancement": "ca_id",
    "dbc_spell_rank": "spell_id",
    "dbc_spell_class": "spell_id",
    "dbc_skill_line": "id",
    "spell_dbc_raw": "id",
    "dbc_spellitemenchantment": "id",   # 3l: enchant-delivered damage route
}


def _column_type(name):
    if name.endswith("_json") or name in {
        "name", "icon", "description", "class_name", "all_classes", "rank_text",
        "ca_type", "rarity_a", "rarity_b", "rarity_c", "source_archive",
        "table_name", "name_subtext", "aura_description", "term_type",
    }:
        return "TEXT"
    if name == "value":
        return "REAL"
    return "INTEGER"


def load_table(conn, table, block):
    """Drop and recreate `table` from a `{"columns": [...], "rows": [[...]]}` block."""
    columns = block["columns"]
    pk = _PK.get(table)
    defs = []
    for col in columns:
        decl = f"{col} {_column_type(col)}"
        if col == pk:
            decl += " PRIMARY KEY"
        defs.append(decl)
    conn.execute(f"DROP TABLE IF EXISTS {table}")
    conn.execute(f"CREATE TABLE {table} ({', '.join(defs)})")
    placeholders = ",".join("?" * len(columns))
    conn.executemany(f"INSERT OR REPLACE INTO {table} VALUES ({placeholders})",
                     block["rows"])
    return len(block["rows"])


def load_ascension_extract(conn, path):
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    # Keys prefixed '_' are extract METADATA (`_extracted_at`, 2e T4), not tables.
    return {table: load_table(conn, table, block)
            for table, block in payload.items() if not table.startswith("_")}


def load_spell_extract(conn, path):
    """`dbc-extract.json` predates the columns/rows convention — it stores lists of dicts."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    loaded = {}

    raw = payload.get("spell_dbc_raw")
    if raw:
        columns = list(raw[0].keys())
        loaded["spell_dbc_raw"] = load_table(conn, "spell_dbc_raw", {
            "columns": columns, "rows": [[r.get(c) for c in columns] for r in raw]})

    for table, rows in (payload.get("support_tables") or {}).items():
        if rows:
            columns = list(rows[0].keys())
            loaded[table] = load_table(conn, table, {
                "columns": columns, "rows": [[r.get(c) for c in columns] for r in rows]})

    # hidden-formula coefficients belong in spell_scaling next to the export-derived
    # ones, distinguished by `source` rather than by living in a separate table
    scaling = payload.get("hidden_formula_scaling")
    if scaling:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(spell_scaling)")}
        if "source" not in cols:
            conn.execute("ALTER TABLE spell_scaling ADD COLUMN source TEXT")
        conn.execute("UPDATE spell_scaling SET source = 'export_tooltip' "
                     "WHERE source IS NULL")
        conn.execute("DELETE FROM spell_scaling WHERE source = 'dbc_hidden_formula'")
        # 3d C1 — provenance stated per row.
        # 🛑 source_tier is 'dbc_description_text', NOT the 'dbc_numeric_field'
        # tier 4 that spell_effect_values carries. These coefficients are
        # regex-extracted from a sub-spell's DESCRIPTION STRING, which is the
        # weakest thing the client offers, not the strongest. Labelling them
        # tier 4 would claim the authority of a numeric field for a tooltip
        # template — the Titanic Mutilate trap, in provenance form. (This does
        # not violate "never read a magnitude from a description": spell_scaling
        # holds COEFFICIENTS, and Ascension keeps applied coefficients in
        # tooltip text — that is the whole reason this route exists.)
        conn.executemany(
            "INSERT INTO spell_scaling (spell_id, term_type, coefficient, source,"
            " source_tier, evidence_ref, confidence, realm, season) "
            "VALUES (?,?,?, 'dbc_hidden_formula', 'dbc_description_text',"
            " ?, 'inferred', ?, ?)",
            # ⚠ The evidence_ref names the ROUTE, not a sub-spell id, because
            # this payload does not carry one — `hidden_formula_scaling` records
            # only {spell_id, term_type, coefficient}. Writing
            # `dbc:Spell.dbc:<spell_id>:description` would be actively WRONG:
            # the coefficient is not in that spell's own description, it is in a
            # sub-spell the tooltip references. Naming what we know and naming
            # the gap beats inventing an id that would not resolve.
            [(r["spell_id"], r["term_type"], r.get("coefficient"),
              f"dbc:Spell.dbc:<hidden sub-spell of {r['spell_id']}>:description"
              f" — resolved by build_dbc_index.py's hidden-formula pass; the"
              f" candidate ids are in spells.hidden_refs for {r['spell_id']}."
              f" The exact sub-spell id is NOT carried in the extract payload.",
              season_config.REALM, season_config.SEASON) for r in scaling])
        loaded["spell_scaling (dbc_hidden_formula)"] = len(scaling)
    return loaded


def main():
    ensure_derived_dir()
    if not DB_PATH.exists():
        print(f"no database at {DB_PATH} - run ingest/export/build_index.py first",
              file=sys.stderr)
        return 1

    conn = connect(DB_PATH)
    loaded = {}
    with transaction(conn):
        if DBC_ASCENSION_EXTRACT_JSON.exists():
            loaded.update(load_ascension_extract(conn, DBC_ASCENSION_EXTRACT_JSON))
        else:
            print(f"MISSING {DBC_ASCENSION_EXTRACT_JSON}", file=sys.stderr)
        if DBC_EXTRACT_JSON.exists():
            loaded.update(load_spell_extract(conn, DBC_EXTRACT_JSON))
        else:
            print(f"MISSING {DBC_EXTRACT_JSON}", file=sys.stderr)

    if not loaded:
        print("nothing loaded - both extracts are missing", file=sys.stderr)
        return 1
    for table, count in sorted(loaded.items()):
        print(f"{table}: {count} rows")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
