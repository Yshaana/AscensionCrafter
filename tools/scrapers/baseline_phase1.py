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

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import config  # noqa: E402
import season_config  # noqa: E402
import crawl_ascensionlogs as crawler  # noqa: E402
from crawl_ascensionlogs import (  # noqa: E402
    NdjsonWriter, api_get, read_patch_date, write_manifest)

# 3f F0 — MUST come before anything prints. This script runs under Task
# Scheduler via run_baseline_scheduled.bat, where stdout is not a console, so
# Python selects cp1252 and the refusal banner below (🛑 / 🚨) dies on
# UnicodeEncodeError PART-WAY THROUGH PRINTING — turning the exit code from 2
# into 1 and truncating the one message the operator needs. A refusal banner
# that crashes before it finishes is not a refusal banner. Same defect as
# INDEX_GUIDE v10 / `2c`'s 12 entry points; this file was never in that sweep.
config.ensure_utf8_stdout()

OUT_DIR = crawler.CRAWL_ROOT / "baseline_phase1"


def _refuse_phase_flip(exc):
    """The tripwire fired on the ONE capture that cannot be redone. (3f F0)

    `crawl_phases()` raises `RealmSeasonMismatch` before a single record is
    stamped, which is right for the daily crawler — a mis-stamped day is
    unrepairable. But this script is the **pre-flip Phase 1 baseline**, and
    leaderboards plus armory are the only data a phase flip DESTROYS: reports
    persist, standings do not. So if the guard fires here it is not "edit a
    constant and re-run" — the thing this script exists to capture is already
    gone, and the operator has to be told that rather than shown a traceback.

    Until `3f`, `main()` caught nothing and this died on a raw stack trace at
    a scheduled 2026-08-07 20:00 run, with nobody watching.
    """
    print("\n" + "=" * 62, file=sys.stderr)
    print("🛑 REFUSING TO CAPTURE — realm/season/phase assertion failed",
          file=sys.stderr)
    print("=" * 62, file=sys.stderr)
    print(str(exc), file=sys.stderr)
    print(
        "\n🚨 THIS IS THE PRE-FLIP PHASE 1 BASELINE. If you are seeing this,\n"
        "   THE FLIP HAS ALREADY HAPPENED and this capture is no longer\n"
        "   possible — leaderboard standings and armory snapshots are the only\n"
        "   data a phase flip destroys, and they are gone. Reports persist, so\n"
        "   the report backfill is unaffected and has no deadline.\n"
        "\n   Do NOT 'fix' this by editing season_config.py and re-running:\n"
        "   that would capture a POST-flip snapshot into a folder named\n"
        "   baseline_phase1, which is worse than having no baseline at all.\n"
        "   The most recent usable Phase 1 baseline is whatever already sits\n"
        "   in data/source/crawl/baseline_phase1/ from an earlier run.\n"
        "\n   If the phase name merely CHANGED without the content flipping\n"
        "   (a rename), update season_config.EXPECTED_PHASE_NAME and re-run\n"
        "   — but check the live name in the message above first.",
        file=sys.stderr)
    return 2


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--top", type=int, default=50, help="characters to snapshot (default 50)")
    args = ap.parse_args()
    # line-buffer stdout so progress is visible when output is redirected to a file
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except AttributeError:
        pass

    print(f"=== Phase 1 baseline snapshot (top {args.top} characters) ===")

    # 🛑 3f F0 — ASSERT BEFORE ANY WRITER EXISTS, and this is not belt-and-braces.
    # `crawl_phases()` writes the /api/phases snapshot and asserts AFTERWARDS
    # (crawl_ascensionlogs.py:315-321). For the daily crawler that is defensible
    # — the day's folder recording what the server actually said is a record,
    # and the run then dies before anything else is stamped. Here it is not:
    # this script OVERWRITES data/source/crawl/baseline_phase1/ in place, and
    # NdjsonWriter APPENDS to a multi-member gzip rather than truncating. So a
    # post-flip run would append the post-flip payload into the irreplaceable
    # PRE-flip artifact, and `load_api_phases()` takes last-wins — silently
    # turning the baseline into a mixture. Found by this session's own check
    # doing exactly that to the committed file (770 -> 3476 bytes).
    #
    # One extra request on a run-once script, in exchange for the guarantee
    # that a refusal leaves the baseline folder byte-identical.
    _, preflight = api_get("/api/phases")
    try:
        if preflight is None:
            raise season_config.RealmSeasonMismatch(
                "/api/phases could not be fetched. Refusing to touch the "
                "baseline folder without verifying which phase the server is "
                "on — an unverified overwrite of this artifact is unrepairable.")
        season_config.assert_phase(preflight)
    except season_config.RealmSeasonMismatch as e:
        return _refuse_phase_flip(e)

    patch_date = read_patch_date()
    writers = {n: NdjsonWriter(OUT_DIR, n, patch_date)
               for n in ("phases", "leaderboards", "characters")}

    # `crawl_phases` deliberately does not catch this, so the caller must. It
    # re-fetches and re-asserts, which is the authoritative gate; the only
    # window it now leaves is a flip landing between the two requests.
    try:
        active = crawler.crawl_phases(writers)
    except season_config.RealmSeasonMismatch as e:
        return _refuse_phase_flip(e)

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
