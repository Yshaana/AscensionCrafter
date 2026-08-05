"""Hand-seeded SP/AP coefficients from tier-3 sources (db.ascension.gg).

Owner decision 2026-08-05 (session 2a follow-up, open question
`trigger_attributed_coefficients_not_in_spell_scaling`): coefficients that a
tier-3 source states for a spell the tooltip extractor cannot reach are seeded
**on the spell that carries them** — the trigger TARGET — never duplicated onto
the cards that reach it. The resolver learns to follow `source_spell_id` per
component in 2b; until then these rows are queryable truth, not yet served
through a card's profile.

Append-only, same discipline as seed_confirmed.py. This script OWNS every
spell_scaling row with source = 'db_ascension_gg' (idempotent delete+insert).

⚠ spell_scaling deliberately has no FK to `spells` (1b) — out-of-catalog ids
like 282987 are exactly why.
"""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import config  # noqa: E402

SOURCE = "db_ascension_gg"

# (spell_id, term_type, coefficient, rank, evidence note — kept here in the seed,
#  the table has no note column)
ROWS = [
    # Hammer from the Heavens (282987, out-of-catalog, reached only via
    # Hour of Judgement's trigger chain). Three-source confirmation, session 1x:
    # db.ascension.gg "Scaling #1: +9.10% of spell power" / "Scaling #2: +9.10%
    # of attack power", corroborated by the live tooltip arithmetic and the
    # client numeric fields (flat half). build_paladin-hammerdin.md §12 item 2.
    (282987, "SP", 0.091, 0),
    (282987, "AP", 0.091, 0),
]


def main():
    conn = sqlite3.connect(config.DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM spell_scaling WHERE source = ?", (SOURCE,))
    cur.executemany(
        "INSERT INTO spell_scaling (spell_id, term_type, coefficient, source, rank)"
        " VALUES (?, ?, ?, ?, ?)",
        [(sid, term, coeff, SOURCE, rank) for sid, term, coeff, rank in ROWS])
    conn.commit()
    n = cur.execute("SELECT COUNT(*) FROM spell_scaling WHERE source = ?",
                    (SOURCE,)).fetchone()[0]
    print(f"hand-seeded {SOURCE} coefficient rows: {n}")
    print("  NOTE: served through a card's resolver profile only once 2b lands "
          "the source_spell_id follow (open question "
          "trigger_attributed_coefficients_not_in_spell_scaling, in_progress)")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
