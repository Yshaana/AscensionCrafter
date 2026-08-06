"""
build_extract_scope_request.py — the log-observed spell ids the DBC extract
should cover (session 3b).

    py tools/audit/build_extract_scope_request.py

## Why

Every existing scope rule in `ingest/dbc/build_dbc_index.py` starts from the
CATALOG — catalog ids, their hidden refs, their rank siblings. A spell that
real characters cast but no catalog card names is therefore invisible to the
extract. That is not a corner case: it is **42.9% of the crawled cohort's real
damage**, and it is why 790 coefficients scraped from db.ascension.gg have no
client-side flat to check against.

The fix is the cheapest robust rule available — **seed the scope from spell ids
actually observed dealing damage**. This script writes that list.

## Why the output is COMMITTED

`data/source/dbc/extract_scope_observed_ids.json` is committed deliberately, so
the machine holding the game client does not also need `builds.db` (which is
gitignored, needs tier-2 crawl data, and takes a rebuild). A `--with-dbc` run
then works from a clean checkout plus the client.

Ordered by corpus damage so the head of the list is the part that matters, and
so a truncated scope still covers the important spells.
"""
import argparse
import json
import sqlite3
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import config  # noqa: E402
from config import BUILDS_DB_PATH, DB_PATH  # noqa: E402

config.ensure_utf8_stdout()

OUT = config.DATA_SOURCE / "dbc" / "extract_scope_observed_ids.json"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--min-damage", type=float, default=0.0,
                    help="drop ids below this pooled corpus damage")
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()

    if not BUILDS_DB_PATH.exists():
        print(f"{BUILDS_DB_PATH} missing — run ingest/logs_gg/build_builds_db.py")
        return 1
    b = sqlite3.connect(BUILDS_DB_PATH)
    a = sqlite3.connect(DB_PATH) if DB_PATH.exists() else None

    rows = b.execute(
        "SELECT spell_id, SUM(damage_total) d, SUM(hits) h, "
        "       COUNT(DISTINCT character_id) c "
        "FROM ability_performance WHERE damage_total > 0 AND spell_id > 0 "
        "GROUP BY spell_id ORDER BY d DESC").fetchall()

    already = set()
    if a:
        already = {r[0] for r in a.execute("SELECT id FROM spell_dbc_raw")}

    detail, ids = [], []
    for sid, dmg, hits, chars in rows:
        if dmg < args.min_damage:
            continue
        ids.append(sid)
        detail.append({"spell_id": sid, "corpus_damage": dmg, "hits": hits,
                       "characters": chars,
                       "already_in_extract": sid in already})
    missing = [d for d in detail if not d["already_in_extract"]]

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({
        "generated_on": date.today().isoformat(),
        "purpose": "spell ids observed dealing damage in the crawl corpus, to be "
                   "added to the DBC extract scope so out-of-catalog spells get "
                   "a client-decoded magnitude (session 3b)",
        "count": len(ids),
        "not_currently_in_extract": len(missing),
        "ordered_by": "pooled corpus damage, descending",
        "ids": ids,
        "detail": detail,
    }, indent=1), encoding="utf-8")

    print(f"[out] {args.out}")
    print(f"  {len(ids)} observed damaging spell ids")
    print(f"  {len(missing)} of them are NOT in the current extract "
          f"— these are what the run recovers")
    if missing:
        print("  biggest by corpus damage:")
        for d in missing[:8]:
            print(f"    {d['spell_id']:>8}  hits={d['hits']:>8,}  "
                  f"chars={d['characters']:>3}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
