#!/usr/bin/env python3
"""Deterministic class resolution from the client's own skill lines (Phase 1 T3).

Ascension renamed `SkillLine.dbc`'s lines to **class names** — line 26 is "Warrior",
not retail's "Arcane" — so the skill line a spell sits on names its class. This is
why `ClassMask` is useless here: it is `512` (Ascension's classless "Hero") on ~10k
rows, which is what db.ascension.gg reports as "Class: Hero" on every card.

Coverage jumps roughly **4.5x**, from 394 doc-confirmed rows to ~1,789 of 3,061.

Run after `seed_borrowed_modifiers.py` (so the weaker tooltip-inferred tier is
already in place and disagreements can be detected) and after the `dbc_*` tables
exist. Decisions live in `core/spells/class_resolution.py`; this file only supplies
paths, prints, and the commit.

⚠ Class only. It says nothing about coefficients — Ascension edits spells in place,
so a WotLK id inherits its class but never its mechanics. And neither method
replaces a proc test when engine gating is on the line.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from config import DB_PATH  # noqa: E402
import config  # noqa: E402

# Piped/redirected stdout defaults to cp1252 on Windows and this file
# prints non-ASCII; without this it dies with UnicodeEncodeError only when
# its output is captured. See config.ensure_utf8_stdout.
config.ensure_utf8_stdout()
from core.db.connection import connect, table_exists, transaction  # noqa: E402
from core.spells.class_resolution import (  # noqa: E402
    apply_skill_line_writes, coverage, record_conflicts, resolve_from_skill_line,
)


def main():
    conn = connect(DB_PATH)
    if not table_exists(conn, "dbc_spell_class"):
        print("dbc_spell_class missing - run ingest/dbc/load_extract.py first",
              file=sys.stderr)
        return 1

    before = coverage(conn)
    writes, conflicts, skipped = resolve_from_skill_line(conn)
    with transaction(conn):
        applied = apply_skill_line_writes(conn, writes)
        recorded = record_conflicts(conn, conflicts)
    after = coverage(conn)

    print(f"class_origin written from skill lines: {applied}")
    print(f"already agreed with an existing value:  {skipped['already_agrees']}")
    print(f"ambiguous / no class line:              "
          f"{skipped['ambiguous'] + skipped['no_class']}")
    print(f"catalog/DBC name mismatch (guardrail):  {skipped['name_mismatch']}")
    print(f"coverage: {before['with_class']} -> {after['with_class']} of "
          f"{after['catalog_total']} ({after['pct']}%)")
    for tier in after["by_tier"]:
        print(f"    {tier['tier']}: {tier['count']}")

    disagreements = [c for c in conflicts if c["kind"] == "class_disagreement"]
    print(f"\n⚠ {recorded} conflict(s) recorded in spells.class_conflict_json, "
          f"NOT resolved (ARCHITECTURE §2.3):")
    for c in disagreements:
        print(f"    {c['spell_id']} {c['name']}: existing {c['existing']!r} "
              f"({c['existing_tier']}) vs skill line {c['skill_line_class']!r}")
    if any(c["kind"] == "name_mismatch" for c in conflicts):
        print("    ...plus name mismatches; a mismatch is a finding, not a row to write")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
