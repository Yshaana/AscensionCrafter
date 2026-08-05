#!/usr/bin/env python3
"""Catalog ingester — `spell-export.json` + `Cards.txt` -> the `spells` tables.

Thin by design (Phase 1 T1): every extraction rule lives in
`core/spells/text_extraction.py` and every table definition in `core/db/schema.py`.
This file owns only the three things `core/` is not allowed to know — where the
files are, what gets printed, and when to commit.

Class-of-origin and best-fit-Path are NOT auto-guessed from spell names. The
duplicate-name trap (primer §2) makes name matching unsafe — Ascension's Mental
Quickness shares a name with a real WotLK talent and is a completely different
effect. Those fields are populated only by `seed_class_from_skill_line.py` (from
the client's own skill lines) and the confirmed-fact seeds. Everything else stays
NULL on purpose.

⚠ This script REBUILDS the database from scratch. It is the first step of the
rebuild chain — see `cli/rebuild.py`.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from config import CARDS_FILE, DB_PATH, SPELL_EXPORT, ensure_derived_dir  # noqa: E402
import config  # noqa: E402

# Piped/redirected stdout defaults to cp1252 on Windows and this file
# prints non-ASCII; without this it dies with UnicodeEncodeError only when
# its output is captured. See config.ensure_utf8_stdout.
config.ensure_utf8_stdout()
from core.db.connection import connect, transaction  # noqa: E402
from core.db.schema import create_all  # noqa: E402
from core.spells.text_extraction import (  # noqa: E402
    extract_mechanics, extract_scaling, extract_schools,
)


def build(conn, spell_export_path, cards_path):
    """Populate the catalog tables. Returns a stats dict; prints nothing."""
    with open(spell_export_path, encoding="utf-8") as f:
        spells = json.load(f)["spells"]
    valid_ids = {s["id"] for s in spells}

    spell_rows, scaling_rows = [], []
    for s in spells:
        tooltip = s.get("tooltip") or ""
        terms, hidden_refs, unresolved_pct = extract_scaling(tooltip, s["id"], valid_ids)
        spell_rows.append((
            s["id"], s["type"], s["name"], s.get("rank"), tooltip,
            ",".join(extract_schools(tooltip)), ",".join(extract_mechanics(tooltip)),
            1 if hidden_refs else 0, ",".join(map(str, hidden_refs)),
            1 if unresolved_pct else 0, None, None, None, None,
        ))
        scaling_rows.extend((s["id"], term_type, coeff) for term_type, coeff in terms)

    conn.executemany(
        "INSERT INTO spells (id, type, name, rank, tooltip, schools, mechanics, "
        "has_hidden_formula, hidden_refs, has_unresolved_pct, class_origin, "
        "class_confidence, best_fit_path, notes) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        spell_rows)
    conn.executemany("INSERT INTO spell_scaling (spell_id, term_type, coefficient) "
                     "VALUES (?,?,?)", scaling_rows)

    with open(cards_path, encoding="utf-8") as f:
        cards = json.load(f)
    owned_rows = [(e["cardId"], e["spellId"], e["rank"], pool)
                  for pool, entries in cards.items() for e in entries]
    conn.executemany("INSERT INTO owned_cards (cardId, spellId, rank, pool) "
                     "VALUES (?,?,?,?)", owned_rows)

    # Cards the owner holds that the catalog export cannot describe. Not an error:
    # the export lags the client (Phase 0 finding #5), so these are the leading edge
    # of the game's content showing up in his collection before spell-export.json
    # is refreshed. Reported, never dropped.
    orphans = [r for r in owned_rows if r[1] not in valid_ids]

    return {"spells": len(spell_rows), "scaling_rows": len(scaling_rows),
            "owned_cards": len(owned_rows), "owned_cards_not_in_catalog": len(orphans),
            "orphan_spell_ids": sorted({r[1] for r in orphans})}


def main():
    ensure_derived_dir()
    if DB_PATH.exists():
        DB_PATH.unlink()   # full rebuild: this script owns the whole file
    conn = connect(DB_PATH)
    with transaction(conn):
        create_all(conn)
        stats = build(conn, SPELL_EXPORT, CARDS_FILE)

    print(f"spells indexed: {stats['spells']}")
    for label, sql in (
        ("spells with a detected school", "SELECT COUNT(*) FROM spells WHERE schools != ''"),
        ("spells with explicit SP/AP/RAP/weapon term",
         "SELECT COUNT(DISTINCT spell_id) FROM spell_scaling"),
        ("spells with a hidden (unresolvable) sub-spell formula",
         "SELECT COUNT(*) FROM spells WHERE has_hidden_formula=1"),
        ("owned card rows", "SELECT COUNT(*) FROM owned_cards"),
    ):
        print(f"{label}: {conn.execute(sql).fetchone()[0]}")
    if stats["owned_cards_not_in_catalog"]:
        print(f"⚠ owned cards NOT in the catalog export: "
              f"{stats['owned_cards_not_in_catalog']} rows / "
              f"{len(stats['orphan_spell_ids'])} distinct spellIds - the export lags "
              f"the client; look these up in dbc_character_advancement, not here")
    print(f"database: {DB_PATH}")
    conn.close()


if __name__ == "__main__":
    main()
