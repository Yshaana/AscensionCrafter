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
import season_config  # noqa: E402  - realm/season constants (3d A1)

SOURCE = "db_ascension_gg"

# A SECOND source owned by this script (2026-08-06, session 3a): a coefficient
# measured off the owner's own parses rather than read from a stating source.
# Kept under its own `source` string so it is filterable and so this script's
# delete stays scoped per source — one writer, two owned partitions.
MEASURED_SOURCE = "ascension_measured_provisional"

# 3d C1: the table now HAS provenance columns, so the evidence notes that used to
# live only in these comments are written into `evidence_ref` as well. The comment
# stays as the long-form reasoning; the column carries the pointer.
#
# (spell_id, term_type, coefficient, rank, evidence_ref)
ROWS = [
    # Hammer from the Heavens (282987, out-of-catalog, reached only via
    # Hour of Judgement's trigger chain). Three-source confirmation, session 1x:
    # db.ascension.gg "Scaling #1: +9.10% of spell power" / "Scaling #2: +9.10%
    # of attack power", corroborated by the live tooltip arithmetic and the
    # client numeric fields (flat half). build_paladin-hammerdin.md §12 item 2.
    (282987, "SP", 0.091, 0,
     "https://db.ascension.gg/?spell=282987 'Scaling #1: +9.10% of spell power'"
     " — corroborated by the live in-game tooltip's own arithmetic and by the"
     " client's numeric fields for the flat half (3 independent sources,"
     " session 1x; build_paladin-hammerdin.md §12 item 2)"),
    (282987, "AP", 0.091, 0,
     "https://db.ascension.gg/?spell=282987 'Scaling #2: +9.10% of attack power'"
     " — corroborated by the live in-game tooltip's own arithmetic and by the"
     " client's numeric fields for the flat half (3 independent sources,"
     " session 1x; build_paladin-hammerdin.md §12 item 2)"),
]

MEASURED_ROWS = [
    # Holy Shock's damage sub-spell (25902 — the trigger TARGET, per the owner's
    # 2026-08-05 attribution rule; the pressed card 20473/20930 is a dummy).
    #
    # 🟡 PROVISIONAL, owner decision 2026-08-06. The measurement is 2d's
    # ≈0.40 (n=40 unbuffed non-crits, read against HftH in the SAME log so the
    # then-current Path-of-Duality AP cycling cancels — a weapon-free same-school
    # pair). 2c's independent discriminator agrees in direction and magnitude:
    # "no SP term" is FALSIFIED (it puts Holy Shock 26-34% above its own Holy
    # group in all four logs), and the client's 0.429 is consistently ~5% too
    # large (3-9% below group in all four). 0.40 sits between them and reproduces.
    #
    # 🛑 Why it stays provisional rather than becoming a confirmed coefficient:
    # no source STATES 0.40. It is back-solved from parses, so it must never
    # become a fit target for the same parses — the standing rule from 2e's
    # deliberately-unseeded Holy residual. The open question
    # `holy_shock_bonus_coefficient_0429` stays live and names the check that
    # would close it (a live tooltip stating a coefficient).
    (25902, "SP", 0.40, 0,
     "own_parse:2026-08-05 session 2d — n=40 unbuffed non-crit Holy Shock hits"
     " read against Hammer from the Heavens in the SAME log (weapon-free"
     " same-school pair, so buff state / talent stack / Duality AP cycling all"
     " cancel). BACK-SOLVED, not stated by any source: never use as a fit target"
     " against those same parses. Open question"
     " holy_shock_bonus_coefficient_0429 stays live."),
]


# 3d C1. The two partitions differ in KIND, not just in name, and the provenance
# columns now say so rather than leaving it to a source string a reader has to
# know the history of:
#   db_ascension_gg                — a tier-3 page STATES the number. 'confirmed'.
#   ascension_measured_provisional — back-solved from our own parses; no source
#                                    states it. 'provisional', and the word is
#                                    load-bearing (rule 2).
PROVENANCE = {
    SOURCE: ("db_ascension_gg", "confirmed"),
    MEASURED_SOURCE: ("own_parse_measurement", "provisional"),
}


def main():
    conn = sqlite3.connect(config.DB_PATH)
    cur = conn.cursor()
    for source, rows in ((SOURCE, ROWS), (MEASURED_SOURCE, MEASURED_ROWS)):
        tier, confidence = PROVENANCE[source]
        cur.execute("DELETE FROM spell_scaling WHERE source = ?", (source,))
        cur.executemany(
            "INSERT INTO spell_scaling (spell_id, term_type, coefficient, source,"
            " rank, source_tier, evidence_ref, confidence, realm, season)"
            " VALUES (?,?,?,?,?,?,?,?,?,?)",
            [(sid, term, coeff, source, rank, tier, evidence, confidence,
              season_config.REALM, season_config.SEASON)
             for sid, term, coeff, rank, evidence in rows])
    conn.commit()
    n = cur.execute("SELECT COUNT(*) FROM spell_scaling WHERE source = ?",
                    (SOURCE,)).fetchone()[0]
    m = cur.execute("SELECT COUNT(*) FROM spell_scaling WHERE source = ?",
                    (MEASURED_SOURCE,)).fetchone()[0]
    print(f"hand-seeded {SOURCE} coefficient rows: {n}")
    print(f"hand-seeded {MEASURED_SOURCE} coefficient rows: {m}")
    print("  🟡 PROVISIONAL rows are back-solved from the owner's own parses — "
          "never fit them against those same parses (open question "
          "holy_shock_bonus_coefficient_0429 stays live)")
    print("  NOTE: served through a card's resolver profile only once 2b lands "
          "the source_spell_id follow (open question "
          "trigger_attributed_coefficients_not_in_spell_scaling, in_progress)")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
