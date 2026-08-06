#!/usr/bin/env python3
"""Ingest db.ascension.gg's STATED coefficients into `spell_scaling`.

    py ingest/ascension_db/load_scraped_coefficients.py [--dry-run]

The client supplies **magnitudes**; the site supplies **coefficients**. That
division of labour is the settled model (primer v31): Ascension keeps applied
coefficients in tooltip text, so `EffectBonusCoefficient` cannot supply one and
the ~41% of crawled damage where we hold a flat and no coefficient is
structurally unreachable from the client alone.

Source: `data/source/ascension_db/spell_pages.ndjson` (2,902 committed records,
scoped by measured demand — see `tools/scrapers/scrape_ascension_db.py`).

## 🛑 Verdicts are RECOMPUTED here, never read from the file

Each record carries a `cross_check` field, but that value was computed against
the **pre-`--with-dbc`** extract. The 2026-08-06 run added 834 spells and 813
check digits, which retired 769 `unverifiable` rows. Reading the stored field
would ingest a stale verdict and, worse, would silently keep refusing spells
that are now checkable. The verdict is recomputed against whatever
`spell_effect_values` currently holds, using the same `cross_check` and the same
grouping the scraper used (`decoded_flats_by_spell`).

## The filter: agree only

* **`agree`** -> ingested. The page's stated base value reproduces the flat we
  decoded independently from the client's numeric fields, so the two sources
  are describing the same spell at the same rank.
* **`unverifiable`** -> **skipped** (audit decision, 2026-08-06). No check
  digit, so no basis for trust. They stay in the committed ndjson and are
  promoted for free by a later extract that decodes their flat — which is
  exactly what happened to 769 of them. Admitting them at "weak confidence"
  would let them feed the sim and inflate the very magnitude-coverage number
  the calibration gate reads; and `spell_scaling` has no confidence column, so
  "weak" would need its own source string anyway.
* **`disagree`** -> **refused** and listed in the report by name. Not stored
  with a caveat. The tolerance is deliberately not widened to absorb them.

## 🛑 Why this script does NOT own `source='db_ascension_gg'`

That string is already owned by `ingest/export/seed_hand_coefficients.py`, which
runs `DELETE FROM spell_scaling WHERE source='db_ascension_gg'` before inserting
Hammer from the Heavens' three-source-confirmed 9.1% SP/AP on 282987 — a
calibration anchor. Two scripts deleting by the same key is rebuild-order-
dependent data loss (the `resolve_numeric_formulas.py` bug, inverted), and it
would also flatten a three-source anchor into the same tier as 1,600 two-source
bulk rows. This script owns `db_ascension_gg_scraped` and nothing else; 282987
is skipped outright so the anchor is never shadowed.

## 🛑 Coefficients are NOT summed per term_type

151 spells state two SP coefficients and 143 state two AP — a `direct` and a
`periodic` component (Pyroblast: SP 0.575 direct, SP 0.025 periodic). Adding
them applies the DoT's coefficient to the direct hit and the nuke's to the tick.
That is "an aggregate across effect slots mixes units" (primer v30 §5), the rule
the Lightbound Cleave 62-65 case produced. Each component is stored as its own
row carrying `spell_scaling.component`, which is the binding the resolver
otherwise has to guess at (`_formula_terms` records `is_periodic=None` for
text-derived rows and `ability_model` warns when a source has both).
"""
import argparse
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import config  # noqa: E402
from config import DATA_DERIVED, DB_PATH  # noqa: E402
from core.spells.db_ascension import cross_check, decoded_flats_by_spell  # noqa: E402

config.ensure_utf8_stdout()

SOURCE = "db_ascension_gg_scraped"
SCRAPE = config.DATA_SOURCE / "ascension_db" / "spell_pages.ndjson"
REPORT = DATA_DERIVED / "scraped_coefficient_ingest.md"

# Owned by seed_hand_coefficients.py at a STRONGER tier (three-source confirmed,
# and a calibration anchor). Never duplicate it into the bulk partition.
HAND_SEEDED_SKIP = {282987}

TERM_TYPES = {"SP", "AP", "RAP", "WEAPON"}


def load_records():
    if not SCRAPE.exists():
        return None
    out = []
    with SCRAPE.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true",
                    help="recompute and report, write nothing")
    args = ap.parse_args()

    records = load_records()
    if records is None:
        print(f"no scrape at {SCRAPE} - nothing to ingest (not an error)")
        return 0

    conn = sqlite3.connect(DB_PATH)
    ours = decoded_flats_by_spell(conn)

    tally = Counter()
    committed = Counter()
    rows, disagreements, promoted, demoted = [], [], [], []

    for rec in records:
        sid = rec.get("spell_id")
        committed[rec.get("cross_check")] += 1
        if not rec.get("parsed_ok"):
            tally["not_parsed"] += 1
            continue

        verdict, detail = cross_check(rec, ours.get(sid))
        tally[verdict] += 1

        # Movement vs the committed (pre---with-dbc) verdict is itself a result:
        # it measures what the widened extract bought us.
        was = rec.get("cross_check")
        if was == "unverifiable" and verdict != "unverifiable":
            (promoted if verdict == "agree" else demoted).append(
                (sid, rec.get("name_on_page"), verdict, detail))
        elif was == "agree" and verdict != "agree":
            demoted.append((sid, rec.get("name_on_page"), verdict, detail))

        if verdict == "disagree":
            disagreements.append((sid, rec.get("name_on_page"), detail))
            continue
        if verdict != "agree":
            continue
        if sid in HAND_SEEDED_SKIP:
            tally["skipped_hand_seeded"] += 1
            continue

        rank = rec.get("rank_on_page") or 0
        for s in rec.get("scaling") or []:
            term = s.get("term_type")
            if term not in TERM_TYPES:
                # an unrecognised scaling stat is REPORTED, never coerced into
                # the known vocabulary (the parser's own rule)
                tally["unnamed_stat_skipped"] += 1
                continue
            coeff = s.get("coefficient")
            if coeff is None:
                continue
            component = s.get("component")
            if component not in ("direct", "periodic"):
                component = None
            rows.append((sid, term, float(coeff), SOURCE, rank, component))

    spells = len({r[0] for r in rows})
    print(f"[scope]     {len(records)} scraped records")
    print(f"[committed] pre---with-dbc verdicts: "
          + ", ".join(f"{v} {k}" for k, v in committed.most_common()))
    print(f"[recomputed] against the LIVE extract: "
          + ", ".join(f"{v} {k}" for k, v in tally.most_common()))
    print(f"[movement]  {len(promoted)} unverifiable -> agree "
          f"(the widened extract's payoff), {len(demoted)} regressions")
    print(f"[ingest]    {len(rows)} coefficient rows across {spells} spells "
          f"at source='{SOURCE}'")
    print(f"[refused]   {len(disagreements)} disagree - coefficients NOT stored")

    if args.dry_run:
        print("\n--dry-run: nothing written")
        conn.close()
        return 0

    cur = conn.cursor()
    # Idempotent, and scoped to the ONE source this script owns. Widening this
    # delete would clobber seed_hand_coefficients.py's anchor rows.
    cur.execute("DELETE FROM spell_scaling WHERE source = ?", (SOURCE,))
    cur.executemany(
        "INSERT INTO spell_scaling (spell_id, term_type, coefficient, source, "
        "rank, component) VALUES (?,?,?,?,?,?)", rows)
    conn.commit()

    held = cur.execute("SELECT COUNT(*) FROM spell_scaling WHERE source = ?",
                       (SOURCE,)).fetchone()[0]
    anchor = cur.execute("SELECT COUNT(*) FROM spell_scaling WHERE source = "
                         "'db_ascension_gg'").fetchone()[0]
    print(f"[verify]    {held} rows at '{SOURCE}'; "
          f"{anchor} rows still at 'db_ascension_gg' (the hand-seeded anchor)")
    if anchor == 0:
        print("  ⚠ the hand-seeded anchor partition is EMPTY - "
              "seed_hand_coefficients.py has not run yet, or its rows were "
              "deleted by something that should not own that source",
              file=sys.stderr)

    write_report(records, tally, committed, rows, spells, disagreements,
                 promoted, demoted)
    print(f"[report]    {REPORT}")
    conn.close()
    return 0


def write_report(records, tally, committed, rows, spells, disagreements,
                 promoted, demoted):
    by_component = Counter(r[5] or "unknown" for r in rows)
    by_term = Counter(r[1] for r in rows)
    lines = [
        "# Scraped coefficient ingest — db.ascension.gg",
        "",
        f"`source='{SOURCE}'`. Written by "
        "`ingest/ascension_db/load_scraped_coefficients.py`.",
        "",
        "## The filter",
        "",
        "**`agree` only.** `unverifiable` is skipped (no check digit, so no "
        "basis for trust — admitting it would feed the sim and inflate the "
        "magnitude-coverage number the calibration gate reads). `disagree` is "
        "refused and listed below by name, with the tolerance deliberately not "
        "widened to absorb it.",
        "",
        "## Verdicts",
        "",
        "Recomputed against the **live** extract, never read from the file's "
        "stored field — that field predates the 2026-08-06 `--with-dbc` run.",
        "",
        "| verdict | committed (pre-DBC) | recomputed (live) |",
        "|---|---:|---:|",
    ]
    for key in ("agree", "unverifiable", "disagree"):
        lines.append(f"| {key} | {committed.get(key, 0)} | {tally.get(key, 0)} |")
    lines += [
        "",
        f"**{len(promoted)} spells moved `unverifiable` -> `agree`** on the "
        "widened extract — that is what the `--with-dbc` run bought, measured "
        f"rather than asserted. {len(demoted)} moved the other way.",
        "",
        "## What was ingested",
        "",
        f"**{len(rows)} coefficient rows across {spells} spells.**",
        "",
        "| term | rows |", "|---|---:|",
    ]
    for term, n in by_term.most_common():
        lines.append(f"| {term} | {n} |")
    lines += [
        "",
        "### Component binding",
        "",
        "🛑 Coefficients are **not summed per term_type**. A spell stating "
        "SP 0.575 `direct` and SP 0.025 `periodic` (Pyroblast) keeps two rows; "
        "adding them would apply the DoT's coefficient to the direct hit — "
        "\"an aggregate across effect slots mixes units\" (primer v30 §5). "
        "`spell_scaling.component` carries the binding, which is information "
        "no other source in the stack has: text-derived rows record "
        "`is_periodic=None` because tooltip text cannot bind a term to a slot.",
        "",
        "| component | rows |", "|---|---:|",
    ]
    for comp, n in by_component.most_common():
        lines.append(f"| {comp} | {n} |")

    lines += ["", "## Refused (`disagree`)", ""]
    if disagreements:
        lines += ["| spell | id | detail |", "|---|---:|---|"]
        for sid, name, detail in disagreements:
            lines.append(f"| {name or '?'} | {sid} | {detail} |")
    else:
        lines.append("_none_")

    if demoted:
        lines += ["", "## Regressions vs the committed verdict", "",
                  "| spell | id | now | detail |", "|---|---:|---|---|"]
        for sid, name, verdict, detail in demoted[:40]:
            lines.append(f"| {name or '?'} | {sid} | {verdict} | {detail} |")

    lines += [
        "", "## Provenance split", "",
        "| source | meaning |", "|---|---|",
        "| `db_ascension_gg` | **hand-curated anchor.** Hammer from the "
        "Heavens (282987), three-source confirmed, a calibration anchor. Owned "
        "by `seed_hand_coefficients.py`. |",
        f"| `{SOURCE}` | **bulk scrape.** Two sources (page + our decoded "
        "flat). Real, cross-checked, and explicitly *not* a calibration "
        "anchor. Owned by this script. |",
        "",
        "Separate strings because each script deletes by source before "
        "inserting: sharing one key makes the surviving rows depend on rebuild "
        "order, and would flatten a three-source anchor into the bulk tier.",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
