#!/usr/bin/env python3
"""
scout_ascensionlogs_cli.py
----------------------------
Pure-Python port of scout_ascensionlogs.js — NO BROWSER REQUIRED.

darkmoon.ascensionlogs.gg's armory/ranking data is a public, unauthenticated
JSON REST API (confirmed via network trace in-session). This script hits it
directly with `requests`, the same way the browser version does with
`fetch`, and writes raw JSON straight into index/scouted/ — no console
paste, no download, no manual chat upload.

Run this locally (e.g. via Claude Code, which has normal outbound internet
access) or directly by hand. It's the primary path for routine/bulk
scouting going forward; the browser console version
(scout_ascensionlogs.js) remains useful as a fallback for interactive
mid-conversation scouting when Claude is driving a live browser tab.

Usage:
    python3 scout_ascensionlogs_cli.py David
    python3 scout_ascensionlogs_cli.py David Mcflurry Zyzz
    python3 scout_ascensionlogs_cli.py --top "Zul'Gurub" --phase 1 --limit 10
    python3 scout_ascensionlogs_cli.py --top "Zul'Gurub" --phase 1 --limit 10 --delay 1.0

Output:
    index/scouted/scouted_<name>_<YYYY-MM-DD>.json  (one per character)

Requires:
    pip install requests
"""
import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
except ImportError:
    print("Requires the 'requests' package: pip install requests", file=sys.stderr)
    sys.exit(1)

BASE = "https://darkmoon.ascensionlogs.gg"
OUT_DIR = Path(__file__).parent / "scouted"


def fetch_json(path):
    url = f"{BASE}{path}"
    try:
        r = requests.get(url, timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
            "Referer": f"{BASE}/",
            "Accept": "application/json",
        })
    except requests.RequestException as e:
        return {"__error": True, "exception": str(e), "url": url}
    if not r.ok:
        return {"__error": True, "status": r.status_code, "url": url}
    return r.json()


def scout_character(name):
    result = {"scouted_at": datetime.now(timezone.utc).isoformat(), "name": name}

    by_name = fetch_json(f"/api/armory/by-name/{name}")
    if not by_name.get("success") or not by_name.get("has_armory"):
        result["error"] = "No armory data (not inspected/logged, or name mismatch)."
        return result

    char_id = by_name["character"]["id"]
    result["character"] = by_name["character"]

    capture = fetch_json(f"/api/armory/character/{char_id}")
    ci = capture.get("ci_resolved", {}) or {}
    result["captured_for_boss"] = (capture.get("capture") or {}).get("captured_for_boss")

    result["gear"] = []
    for slot, item in (ci.get("gear") or {}).items():
        resolved_item = item.get("resolved_item") or {}
        bis = item.get("resolved_bisbeard") or {}
        result["gear"].append({
            "slot": item.get("slot", int(slot)),
            "item_id": item.get("item_id"),
            "name": resolved_item.get("name"),
            "quality": resolved_item.get("quality"),
            "enchant_id": item.get("enchant"),
            "enchant_name": (item.get("resolved_enchant") or {}).get("name"),
            "gems": item.get("gems"),
            "stats": bis.get("stats"),
            "damage": bis.get("damage"),
            "source": bis.get("source"),
            "source_category": bis.get("source_category"),
            "tier": resolved_item.get("mythic_tier"),
        })

    trees = ((ci.get("specialization") or {}).get("talents") or {}).get("trees") or {}
    result["build"] = {}
    for slug, tree in trees.items():
        result["build"][slug] = [
            {
                "entry_id": t.get("entry_id"),
                "name": t.get("name"),
                "icon": t.get("icon"),
                "rank": t.get("rank"),
                "max_ranks": t.get("max_ranks"),
                "per_rank_text": t.get("per_rank_text"),
            }
            for t in (tree.get("talents") or [])
        ]

    result["primary_stat"] = ci.get("primary_stat")

    phases_resp = fetch_json("/api/phases")
    phases = phases_resp if isinstance(phases_resp, list) else phases_resp.get("phases", [])
    result["rankings"] = []
    for phase in phases:
        phase_num = phase.get("phase_number", phase.get("number", phase.get("id")))
        if phase_num is None:
            continue
        zs = fetch_json(
            f"/api/characters/{name}/zone-summaries?phase={phase_num}&difficulty=ascended&bracket=all&metric=avg_dps"
        )
        for tile in zs.get("tiles", []):
            if not tile.get("bosses_killed"):
                continue
            location = tile["location"]
            br = fetch_json(
                f"/api/characters/{name}/boss-rows?phase={phase_num}&difficulty=ascended"
                f"&bracket=all&metric=avg_dps&location={location}"
            )
            result["rankings"].append({
                "phase": phase_num,
                "zone": location,
                "zone_summary": tile,
                "boss_rows": [r for r in br.get("rows", []) if r.get("kills", 0) > 0],
            })

    caps = fetch_json(f"/api/armory/character/{char_id}/captures?limit=100")
    result["capture_history"] = [
        {
            "capture_id": c.get("capture_id"),
            "captured_at": c.get("captured_at"),
            "boss_name": (c.get("encounter") or {}).get("boss_name"),
            "report_id": (c.get("encounter") or {}).get("report_id"),
            "location": (c.get("encounter") or {}).get("location"),
            "success": (c.get("encounter") or {}).get("success"),
        }
        for c in caps.get("captures", [])
    ]
    return result


def find_top_characters(zone, phase, limit=10):
    """Auto-discover outliers via the site's own leaderboard endpoint.
    Ranked by total All-Star points across the whole zone, NOT single-boss
    DPS — see README caveat on this distinction."""
    url = (
        f"/api/encounters/rankings/overall?location={zone}&difficulty=ascended"
        f"&phase={phase}&metric=avg_dps&page=1&limit={limit}&role=dps&cohort=global"
    )
    r = fetch_json(url)
    rankings = r.get("rankings", {})
    zone_data = rankings.get(zone, {})
    for key in ("ascended", "normal"):
        if key in zone_data:
            return zone_data[key]
    return next(iter(zone_data.values()), [])


def save(data, name):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = OUT_DIR / f"scouted_{name}_{date}.json"
    path.write_text(json.dumps(data, indent=2))
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("names", nargs="*", help="Character names to scout")
    parser.add_argument("--top", metavar="ZONE", help="Auto-discover top characters in this zone via the leaderboard")
    parser.add_argument("--phase", type=int, default=1)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--delay", type=float, default=0.5, help="Seconds between characters (politeness, default 0.5)")
    args = parser.parse_args()

    names = list(args.names)
    if args.top:
        top = find_top_characters(args.top, args.phase, args.limit)
        discovered = [c["name"] for c in top]
        names.extend(n for n in discovered if n not in names)
        print(f"Discovered {len(discovered)} in {args.top} phase {args.phase}: {discovered}")

    if not names:
        parser.error("Provide character names and/or --top ZONE")

    for i, name in enumerate(names):
        print(f"Scouting {name}...")
        data = scout_character(name)
        if data.get("error"):
            print(f"  [skip] {name}: {data['error']}")
            continue
        path = save(data, name)
        print(f"  [ok] saved {path} ({len(json.dumps(data))} bytes, "
              f"{len(data.get('gear', []))} gear, "
              f"{sum(len(v) for v in data.get('build', {}).values())} build entries)")
        if i < len(names) - 1:
            time.sleep(args.delay)


if __name__ == "__main__":
    main()
