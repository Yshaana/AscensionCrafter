#!/usr/bin/env python3
"""
baseline_phase1.py — one-off Phase 1 (Zul'Gurub era) baseline snapshot.

Phase 0 Task 6 explicitly asks for this before the 2026-08-08 phase flip: a
clean snapshot of the current leaderboards plus the top ~50 characters' full
builds, so a before/after pair exists for `meta_snapshot()` even if the
incremental crawl has gaps. Run ONCE (re-running overwrites the same folder —
it is a point-in-time artifact, dated inside each record).

Reuses the crawler's plumbing (api_get, NdjsonWriter, stamping).

Output: data/source/crawl/baseline_phase1/{phases,leaderboards,characters}.jsonl

Usage:  py tools/scrapers/baseline_phase1.py [--top 50]
"""
import argparse
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import crawl_ascensionlogs as crawler
from crawl_ascensionlogs import NdjsonWriter, api_get, read_patch_date, write_manifest

OUT_DIR = crawler.CRAWL_ROOT / "baseline_phase1"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--top", type=int, default=50, help="characters to snapshot (default 50)")
    args = ap.parse_args()
    # line-buffer stdout so progress is visible when output is redirected to a file
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except AttributeError:
        pass

    patch_date = read_patch_date()
    writers = {n: NdjsonWriter(OUT_DIR, n, patch_date)
               for n in ("phases", "leaderboards", "characters")}

    print(f"=== Phase 1 baseline snapshot (top {args.top} characters) ===")
    active = crawler.crawl_phases(writers)

    # rank-ordered character collection: leaderboard order is the priority order
    seen = {}  # id -> name, insertion-ordered = rank-ordered (dps first, then tank, support)
    crawler.crawl_leaderboards(writers, active, seen)

    picked = list(seen.items())[:args.top]
    print(f"[baseline] pulling full armory for {len(picked)} characters...")
    pulled = 0
    for cid, cname in picked:
        _, armory = api_get(f"/api/armory/character/{cid}")
        if armory is None:
            continue
        _, captures = api_get(f"/api/armory/character/{cid}/captures?limit=100")
        primary_stat = None
        if cname:
            _, primary_stat = api_get(
                f"/api/characters/{urllib.parse.quote(str(cname))}/primary-stat")
        writers["characters"].write(
            "character_armory",
            {"armory": armory, "captures": captures, "primary_stat": primary_stat},
            character_id=int(cid), character_name=cname,
        )
        pulled += 1
        if pulled % 10 == 0:
            print(f"  ...{pulled}/{len(picked)}")

    write_manifest(OUT_DIR, writers, crawler.load_scan_log(), patch_date, [])

    print(f"\nBASELINE SUMMARY: {pulled} characters, "
          f"{writers['leaderboards'].count} leaderboards, "
          f"{crawler.STATS['requests']} requests, {len(crawler.ERRORS)} errors")
    for path, err in crawler.ERRORS[:10]:
        print(f"  ⚠ {path} -> {err}")
    print(f"Output: {OUT_DIR}")
    print("NOTE: commit is left to the daily crawler / manual git — this script does not push.")
    return 0 if not crawler.ERRORS else 1


if __name__ == "__main__":
    sys.exit(main())
