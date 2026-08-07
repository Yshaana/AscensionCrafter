"""
scrape_ascension_db.py — pull stated coefficients and trigger links from
db.ascension.gg, for the spells our own data says we are missing.

    py tools/scrapers/scrape_ascension_db.py --plan          # cost estimate, no requests
    py tools/scrapers/scrape_ascension_db.py --coverage 0.90 # the 90%-of-damage set
    py tools/scrapers/scrape_ascension_db.py --all           # every observed damaging spell
    py tools/scrapers/scrape_ascension_db.py --resume        # continue an interrupted run

## Why this exists

The sim has a key for a median 37% of what real characters deal (as measured
2026-08-06, pre-E13 — kept as this tool's historical motivation; the phrasing
"produces damage for" was retired at 3h B1 because a key is not production, and
the current figures live in predictions/gate_manifest_3e.json), and the
miss splits almost evenly between spells absent from our DBC extract (~43%) and
spells where we hold a magnitude but **no coefficient** (~41%). The client
cannot fix the second: Ascension keeps applied coefficients in **tooltip
text**, not numeric fields. db.ascension.gg states them outright, and it also
states the `EffectTriggerSpell` links that are how a card's damage can live two
hops away (Hour of Judgement -> Hammer from the Heavens is right there in the
page's own href).

## Scoping — we never enumerate the site

The site carries hundreds of thousands of entries and almost all are
irrelevant. **The request list is DERIVED FROM MEASURED DEMAND**: distinct
spell ids that actually dealt damage in the crawl corpus, ranked by how much
damage they account for, cut at a coverage target. 285 ids cover 90% of all
logged damage; 2,902 cover everything ever observed. Nothing is probed
speculatively and no id range is swept.

## Politeness

`robots.txt` (checked 2026-08-06) is `Allow: /` for all agents with **no
Crawl-delay**, and disallows only `?admin=`, `?account=`, `?compare=`,
`?filter=`, `?search=`, `?go-to-comment=` and `*&filter=` — none of which this
touches. We are stricter than required anyway: sequential, one request at a
time, a default **2.0s** delay, a descriptive User-Agent with a contact
address, and exponential backoff that STOPS the run rather than hammering on
repeated failures.

## Durability

Every record is appended to NDJSON and flushed **as it arrives**, so a network
failure loses at most the one in flight. `--resume` reads what is already on
disk and requests only the remainder, so an interrupted run is re-entrant and
costs the site nothing for work already done.
"""
import argparse
import json
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import config  # noqa: E402
from config import BUILDS_DB_PATH, DB_PATH  # noqa: E402
from core.spells.db_ascension import cross_check, parse_spell_page  # noqa: E402

config.ensure_utf8_stdout()

BASE = "https://db.ascension.gg/?spell="
USER_AGENT = ("AscensionCrafter/1.0 (personal build-theorycrafting tool; "
              "contact a.avenard@gmail.com)")
OUT_DIR = config.DATA_SOURCE / "ascension_db"
DEFAULT_DELAY = 2.0


def demand_list(bconn, coverage=None, limit=None):
    """Spell ids ranked by the damage they account for across the whole corpus.

    Measured demand, not a guess at what matters — and it is why this scraper
    never enumerates the site.
    """
    rows = bconn.execute(
        "SELECT spell_id, SUM(damage_total) d, COUNT(DISTINCT character_id) c "
        "FROM ability_performance WHERE damage_total > 0 AND spell_id > 0 "
        "GROUP BY spell_id ORDER BY d DESC").fetchall()
    total = sum(r[1] for r in rows) or 1.0
    out, run = [], 0.0
    for sid, dmg, chars in rows:
        run += dmg
        out.append({"spell_id": sid, "damage": dmg, "characters": chars,
                    "cumulative_share": run / total})
        if coverage is not None and run / total >= coverage:
            break
        if limit is not None and len(out) >= limit:
            break
    return out


def our_flats(aconn):
    """Decoded flats from the client's numeric fields — the check digits.

    ⚠ PER EFFECT SLOT, never aggregated. A MIN/MAX across slots mixes a flat
    with a weapon-percent row and invents a range belonging to no effect —
    which produced two false disagreements before it was caught.
    """
    out = {}
    for sid, lo, hi in aconn.execute(
            "SELECT spell_id, flat_min, flat_max FROM spell_effect_values "
            "WHERE flat_min IS NOT NULL"):
        out.setdefault(sid, []).append((lo, hi))
    return out


def already_done(path):
    seen = set()
    if not path.exists():
        return seen
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                seen.add(json.loads(line)["spell_id"])
            except Exception:      # noqa: BLE001 — a torn trailing line is fine
                continue
    return seen


def fetch(url, *, timeout=30, retries=3):
    """One page. Backs off, then gives up — never hammers."""
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", "replace"), None
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None, "404"          # the site does not carry it: a result
            last = f"HTTP {e.code}"
            if e.code in (403, 429):
                return None, last           # stop on throttle/deny, do not retry
        except Exception as e:              # noqa: BLE001
            last = f"{type(e).__name__}: {e}"
        time.sleep(2.0 * (2 ** attempt))
    return None, last


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--coverage", type=float,
                   help="fraction of all logged damage to cover (e.g. 0.90)")
    g.add_argument("--limit", type=int, help="top N spells by damage")
    g.add_argument("--all", action="store_true", help="every observed damaging spell")
    ap.add_argument("--plan", action="store_true",
                    help="print the cost estimate and exit — makes NO requests")
    ap.add_argument("--resume", action="store_true",
                    help="skip ids already in the output file")
    ap.add_argument("--delay", type=float, default=DEFAULT_DELAY,
                    help=f"seconds between requests (default {DEFAULT_DELAY})")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    if not BUILDS_DB_PATH.exists():
        print(f"{BUILDS_DB_PATH} missing — run ingest/logs_gg/build_builds_db.py")
        return 1
    bconn = sqlite3.connect(BUILDS_DB_PATH)
    aconn = sqlite3.connect(DB_PATH) if DB_PATH.exists() else None

    if args.all:
        targets = demand_list(bconn)
    elif args.limit:
        targets = demand_list(bconn, limit=args.limit)
    else:
        targets = demand_list(bconn, coverage=args.coverage or 0.90)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = args.out or (OUT_DIR / "spell_pages.ndjson")
    done = already_done(out_path) if args.resume else set()
    todo = [t for t in targets if t["spell_id"] not in done]

    secs = len(todo) * (args.delay + 0.4)      # measured: ~0.4s per 25 KB page
    print(f"[scope] {len(targets)} spells cover "
          f"{targets[-1]['cumulative_share'] * 100:.1f}% of all logged damage "
          f"in the corpus")
    if done:
        print(f"[resume] {len(done)} already captured, {len(todo)} remaining")
    print(f"[estimate] {len(todo)} requests at {args.delay:g}s delay "
          f"≈ {secs / 60:.0f} min ({secs / 3600:.1f} h), ~{len(todo) * 25 / 1024:.0f} MB")
    if args.plan:
        print("[plan] no requests made")
        return 0

    flats = our_flats(aconn) if aconn else {}
    print(f"[check] {len(flats)} spells have a decoded flat to cross-check against")

    stats = {"agree": 0, "disagree": 0, "unverifiable": 0,
             "with_coefficient": 0, "trigger_edges": 0, "missing": 0, "errors": 0}
    t0 = time.time()
    # append + flush per record: a network failure loses at most the one in flight
    with out_path.open("a", encoding="utf-8") as f:
        for i, t in enumerate(todo, 1):
            sid = t["spell_id"]
            html, err = fetch(f"{BASE}{sid}")
            if err in ("HTTP 403", "HTTP 429"):
                print(f"\n[stop] server returned {err} — stopping rather than "
                      f"retrying. Re-run with --resume later.")
                break
            rec = (parse_spell_page(html, sid) if html
                   else {"spell_id": sid, "parsed_ok": False, "reason": err})
            verdict, detail = cross_check(rec, flats.get(sid))
            rec.update({
                "cross_check": verdict, "cross_check_detail": detail,
                "corpus_damage": t["damage"], "corpus_characters": t["characters"],
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "source_url": f"{BASE}{sid}",
            })
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()

            if not rec.get("parsed_ok"):
                stats["missing" if err == "404" else "errors"] += 1
            else:
                stats[verdict] += 1
                if rec.get("scaling"):
                    stats["with_coefficient"] += 1
                stats["trigger_edges"] += len(rec.get("trigger_edges") or [])

            if i % 25 == 0 or i == len(todo):
                rate = (time.time() - t0) / i
                print(f"  {i}/{len(todo)}  agree={stats['agree']} "
                      f"disagree={stats['disagree']} unverif={stats['unverifiable']} "
                      f"coef={stats['with_coefficient']} "
                      f"triggers={stats['trigger_edges']} "
                      f"404={stats['missing']} err={stats['errors']}  "
                      f"eta {(len(todo) - i) * rate / 60:.0f}m")
            time.sleep(args.delay)

    print(f"\n[done] {out_path}")
    print(f"  cross-check: {stats['agree']} agree / {stats['disagree']} DISAGREE "
          f"(coefficients refused) / {stats['unverifiable']} unverifiable")
    print(f"  {stats['with_coefficient']} spells state a coefficient; "
          f"{stats['trigger_edges']} trigger edges found")
    if stats["disagree"]:
        print("  ⚠ a disagreement is usually a RANK mismatch — the page shows a "
              "different rank than the id we decoded. Inspect before using.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
