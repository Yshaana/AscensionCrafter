#!/usr/bin/env python3
"""Build `spell_mechanics` — the resolved truth table (Phase 1 T4).

    py cli/mechanics.py

Thin wrapper over `core/spells/mechanics.py`. Runs LAST in the rebuild chain:
it consumes `spell_effect_values` (including the trigger-attributed rows
`cli/relationships.py` writes), `spell_scaling`, `doc_confirmed_mechanics` and
the `dbc_*` structural tables.

Also performs the T4 `spell_scaling` rank migration (rank labels + level-60
sibling coefficient rows), since this task owns that table's rebuild.

Validations pin the resolver to doc-confirmed facts: Divine Storm = 110% weapon
damage, Lightbound Cleave = off-GCD next-swing spell-crit-table, Hammerdin's
attributed Hammer from the Heavens flat = 122–145 at level 60, and Sun Down's
level-60 rank carrying SP 1.3 (the worst of the seven wrong-rank coefficients).
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import DB_PATH  # noqa: E402
import config  # noqa: E402

# Piped/redirected stdout defaults to cp1252 on Windows and this file
# prints non-ASCII; without this it dies with UnicodeEncodeError only when
# its output is captured. See config.ensure_utf8_stdout.
config.ensure_utf8_stdout()
from core.db.connection import connect, table_exists, transaction  # noqa: E402
from core.db.schema import create_phase1_schema  # noqa: E402
from core.spells import mechanics as mech  # noqa: E402

REALM = "Darkmoon"
SEASON = "S10"


def latest_patch_id(conn):
    row = conn.execute(
        "SELECT patch_id FROM patches WHERE realm = ? ORDER BY patch_date DESC "
        "LIMIT 1", (REALM,)).fetchone()
    return row[0] if row else None


def validate(conn):
    failures = []

    def one(sql, *args):
        row = conn.execute(sql, args).fetchone()
        return row[0] if row else None

    # Divine Storm: 110% weapon damage (doc-confirmed v10, DBC effect 31)
    ds = one("SELECT weapon_damage_pct FROM spell_mechanics WHERE spell_id=53385")
    if ds != 110.0:
        failures.append(f"Divine Storm weapon_damage_pct = {ds}, expected 110.0")

    # Lightbound Cleave: off-GCD, next-swing, spell crit table (doc-confirmed)
    lc = conn.execute(
        """SELECT gcd_type, is_next_swing, crit_table FROM spell_mechanics m
           JOIN spells s ON s.id = m.spell_id
           WHERE s.name = 'Lightbound Cleave'""").fetchone()
    if lc is None:
        failures.append("Lightbound Cleave has no spell_mechanics row")
    elif tuple(lc) != ("off_gcd", 1, "spell"):
        failures.append(f"Lightbound Cleave (gcd, next_swing, crit) = {lc}, "
                        "expected ('off_gcd', 1, 'spell')")

    # Hammerdin card: attributed Hammer from the Heavens flat, level-60 scaled.
    # Session 1x's resolved formula: 122-145 Holy (+9.1% SP/AP in tooltip text).
    row = conn.execute(
        "SELECT damage_formula_terms_json FROM spell_mechanics "
        "WHERE spell_id = 282983").fetchone()
    if row is None or not row[0]:
        failures.append("Hammerdin (282983) has no damage terms")
    else:
        # DBC per_level is float32 (2.4000000953...), so 122/145 with tolerance
        terms = [t for t in json.loads(row[0])
                 if t.get("source_spell_id") == 282987
                 and t.get("min") is not None
                 and abs(t["min"] - 122.0) < 0.01
                 and abs(t["max"] - 145.0) < 0.01]
        if not terms:
            failures.append("Hammerdin (282983) missing attributed 282987 term "
                            "scaling to 122-145 at level 60 — level-scaling "
                            "regression (max_level=0 is UNCAPPED)")

    # Sun Down: the level-60 sibling must carry SP 1.3 (1x: catalog says 0.4)
    sun = conn.execute(
        """SELECT ss.coefficient FROM spell_scaling ss
           WHERE ss.source = 'dbc_rank_sibling_text' AND ss.term_type = 'SP'
             AND ss.spell_id IN (
                 SELECT r2.spell_id FROM dbc_spell_rank r2
                 WHERE r2.line_id = (SELECT r.line_id FROM dbc_spell_rank r
                                     JOIN spells s ON s.id = r.spell_id
                                     WHERE s.name = 'Sun Down'))""").fetchall()
    if not any(c[0] == 1.3 for c in sun):
        failures.append(f"Sun Down level-60 sibling SP coefficient rows = "
                        f"{[c[0] for c in sun]}, expected to include 1.3")
    return failures


def main():
    if not DB_PATH.exists():
        print(f"no database at {DB_PATH} - run py cli/rebuild.py first",
              file=sys.stderr)
        return 1
    conn = connect(DB_PATH)
    for required in ("spell_dbc_raw", "spell_effect_values", "spell_scaling",
                     "dbc_spell_rank", "doc_confirmed_mechanics"):
        if not table_exists(conn, required):
            print(f"{required} missing - run the earlier chain steps first",
                  file=sys.stderr)
            return 1
    create_phase1_schema(conn)

    patch_id = latest_patch_id(conn)
    if patch_id is None:
        print("no patches row for Darkmoon - run the changelog ingester first "
              "(spell_mechanics.verified_at_patch is NOT NULL by design)",
              file=sys.stderr)
        return 1
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    with transaction(conn):
        migration = mech.migrate_spell_scaling_ranks(conn)
        stats = mech.populate(conn, REALM, SEASON, patch_id, now)

    print(f"spell_scaling rank migration: {migration['sibling_rows']} level-60 "
          f"sibling coefficient rows added "
          f"({migration['differing_lines']} lines where the catalog's stored "
          "coefficient differs from the one cast)")
    print(f"spell_mechanics: {stats['rows']} rows resolved "
          f"({stats['empty']} population targets had no resolvable field)")
    print(f"  rows with a source conflict (§2.3, surfaced not resolved): "
          f"{stats['with_conflict']}")
    print(f"  rows whose spell is not what a level-60 character casts "
          f"(explicit rank gap): {stats['with_rank_gap']}")
    print(f"  ambiguous rank lines contributing no sibling row: "
          f"{stats['ambiguous_lines_skipped']}")

    failures = validate(conn)
    if failures:
        print("VALIDATION FAILED:", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1
    print("validation OK: Divine Storm 110%, Lightbound Cleave off-GCD/"
          "next-swing/spell-crit, Hammer from the Heavens 122-145, "
          "Sun Down SP 1.3 all reproduce")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
