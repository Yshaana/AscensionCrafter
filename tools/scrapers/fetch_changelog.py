#!/usr/bin/env python3
"""
fetch_changelog.py — Phase 0 Task 6 second daily job: snapshot the Ascension changelog.

Discovery (session 0b, 2026-08-04): the changelog page embeds a real JSON API —

    https://api.ascension.gg/api/v3/article/changelog?realm_type=1&page=N

Laravel-style pagination: per_page=100, ~353 pages, ~35,238 entries as of today.
Entries carry stable integer `id`, `label`, `category`, `realm_type`,
`group_key` (the "Changes made on" date, e.g. "2026/08/04"), `description`
(with [Darkmoon]/[Dawnrise]/[Pending Restart] tags inline), created_at and
updated_at. This beats HTML scraping on every axis — RAW JSON is what we store.

Why daily snapshots and not just a one-time backfill: the [Pending Restart] tag
means an entry can change state (and description, via updated_at) between
fetches. A daily snapshot of the newest pages captures those transitions —
impossible to reconstruct later.

This script is RAW CAPTURE ONLY. The parser (realm/status/ability-name
extraction) is Phase 0 Task 3 / session 0a, not here. The single exception is a
minimal read of the newest entry date, written to latest_patch_date.txt so the
crawler can stamp records with the patch date (ARCHITECTURE §2.5).

Output:
    data/source/changelog/daily/<YYYY-MM-DD>_page<N>.json   (daily mode: pages 1-2)
    data/source/changelog/backfill/page_<NNN>.json          (--backfill, one-time)
    data/source/changelog/latest_patch_date.txt             (YYYY-MM-DD)

Usage:
    py tools/scrapers/fetch_changelog.py              (daily snapshot)
    py tools/scrapers/fetch_changelog.py --backfill   (all pages, run once)

Requires: pip install requests
"""
import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
except ImportError:
    print("Requires the 'requests' package: pip install requests", file=sys.stderr)
    sys.exit(1)

API = "https://api.ascension.gg/api/v3/article/changelog"
REALM_TYPE = 1  # the classless realms' changelog (Darkmoon + Dawnrise entries, tagged inline)

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_ROOT = REPO_ROOT / "data" / "source" / "changelog"
PATCH_DATE_FILE = OUT_ROOT / "latest_patch_date.txt"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "application/json",
}
DELAY = 0.8


def fetch_page(page):
    time.sleep(DELAY)
    r = requests.get(API, params={"realm_type": REALM_TYPE, "page": page},
                     timeout=30, headers=HEADERS)
    r.raise_for_status()
    return r.json()


def newest_entry_date(page_json):
    """Newest 'Changes made on' date on a page. data is keyed by 'YYYY/MM/DD'."""
    dates = []
    for key in (page_json.get("data") or {}):
        m = re.fullmatch(r"(\d{4})/(\d{2})/(\d{2})", key)
        if m:
            dates.append(f"{m.group(1)}-{m.group(2)}-{m.group(3)}")
    return max(dates) if dates else None


def save(page_json, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(page_json, ensure_ascii=False, indent=1), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--backfill", action="store_true",
                    help="fetch ALL pages into backfill/ (one-time, ~5 min)")
    ap.add_argument("--daily-pages", type=int, default=2,
                    help="pages to snapshot in daily mode (default 2 = ~200 newest entries)")
    args = ap.parse_args()
    # line-buffer stdout so progress is visible when output is redirected
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except AttributeError:
        pass

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    errors = []
    saved = 0

    try:
        first = fetch_page(1)
    except Exception as e:
        print(f"FATAL: cannot fetch changelog page 1: {e}", file=sys.stderr)
        return 1

    last_page = first.get("last_page", 1)
    total = first.get("total")
    latest = newest_entry_date(first)
    if latest:
        PATCH_DATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        PATCH_DATE_FILE.write_text(latest + "\n", encoding="utf-8")

    if args.backfill:
        print(f"=== changelog BACKFILL: {last_page} pages, {total} entries ===")
        save(first, OUT_ROOT / "backfill" / "page_001.json")
        saved += 1
        for page in range(2, last_page + 1):
            try:
                save(fetch_page(page), OUT_ROOT / "backfill" / f"page_{page:03d}.json")
                saved += 1
            except Exception as e:
                errors.append((page, str(e)))
            if page % 25 == 0:
                print(f"  ...page {page}/{last_page} ({len(errors)} errors)")
    else:
        print(f"=== changelog daily snapshot: pages 1-{args.daily_pages} of {last_page} ===")
        save(first, OUT_ROOT / "daily" / f"{date_str}_page1.json")
        saved += 1
        for page in range(2, args.daily_pages + 1):
            try:
                save(fetch_page(page), OUT_ROOT / "daily" / f"{date_str}_page{page}.json")
                saved += 1
            except Exception as e:
                errors.append((page, str(e)))

    print(f"  pages saved:       {saved}")
    print(f"  latest patch date: {latest or '⚠ NOT FOUND'}")
    if errors:
        print(f"  ⚠ ERRORS ({len(errors)}): " + "; ".join(f"p{p}: {e[:80]}" for p, e in errors[:5]))
    print(f"  RESULT: {'OK' if not errors and latest else 'COMPLETED WITH ERRORS'}")
    return 0 if not errors and latest else 1


if __name__ == "__main__":
    sys.exit(main())
