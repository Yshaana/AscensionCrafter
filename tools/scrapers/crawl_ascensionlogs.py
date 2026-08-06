#!/usr/bin/env python3
"""
crawl_ascensionlogs.py — Phase 0 Task 6: crude daily crawler for darkmoon.ascensionlogs.gg.

RAW CAPTURE ONLY. No spell-ID resolution, no normalisation, no analysis — that is
Phase 3. Output is gzipped NDJSON (.jsonl.gz), one stamped record per line, under
data/source/crawl/<YYYY-MM-DD>/. Ugly is allowed; losing data is not.

Read it back with:  gzip.open(path, "rt", encoding="utf-8")

Design decisions (session 0b, 2026-08-04 — see primer/Session_2026-08-04_crawler.md):
- Report discovery is SEQUENTIAL ID PROBING. The /api/reports list endpoint
  requires an auth token (401 "No token provided"); report IDs are small
  sequential integers and a missing ID returns 404 {"error":"Report not found"}.
  We walk upward from the last known report and stop after TAIL_404_LIMIT
  consecutive 404s. 404s *followed by a live ID in the same run* are recorded as
  permanently missing; trailing 404s are re-probed next run (they may simply not
  exist yet).
- Per-ability endpoints AGGREGATE across whatever encounterIds you pass — rows
  carry no encounter_id. So boss encounters are fetched ONE ENCOUNTER PER CALL
  (per-encounter granularity is what the content-profile work needs), and trash
  encounters are fetched as a single bundled call per report. Every data record
  stores the encounter_ids it covers.
- EXCEPT for grind reports: report 2 alone has 658 encounters (368 boss
  *attempts* over an 8-hour dungeon session) — per-encounter calls would be
  ~1,500 requests for one report. Reports with more than BOSS_SINGLE_LIMIT boss
  encounters are instead grouped by boss_id: one call per boss, aggregated over
  its attempts (scope "boss_group:<boss_id>"). Per-attempt ability granularity
  is sacrificed for grind logs only; per-fight duration/kill data is still fully
  present in the encounters list, and mechanics inference pools per boss anyway.
- Roles: the rankings endpoint accepts role ∈ {tank, dps, tanks-and-dps, support}.
  "support" is the healer role — this resolves INDEX_GUIDE v7's role=healer quirk.
  All three non-redundant roles are walked (`tanks-and-dps` is a union of two we
  already take), so Phase 3 T8's "capture all roles" was already satisfied here;
  what T8 actually added is the re-verification sweep below.
- Re-verification (Phase 3 T8, 2026-08-06): discovery is incremental, so a
  character who respecs and stops parsing stays frozen at their old build. Each
  run additionally re-pulls up to REVERIFY_PER_RUN known-but-not-seen-today
  characters, oldest capture first. Content-hash dedupe makes an unchanged build
  cost one request and zero bytes.
- character_spell_healing EXISTS (resolves a Phase 0 Task 2 open question) and is
  captured, as are both directions of character_damage_taken_abilities
  (participantType=enemies → avoidance of player attacks; friendlies → damage the
  raid took).
- Every record is stamped: captured_at (UTC ISO), realm, season, patch_date.
  patch_date comes from data/source/changelog/latest_patch_date.txt (written by
  fetch_changelog.py, which the launcher runs first). If it is missing the stamp
  is null and the summary says so loudly — never silently fabricated.
- scan_log.json makes runs incremental and Ctrl+C-safe: it is rewritten after
  every report and every character batch.

Usage:
    py tools/scrapers/crawl_ascensionlogs.py
    py tools/scrapers/crawl_ascensionlogs.py --max-reports 25   (watchable first run)
    py tools/scrapers/crawl_ascensionlogs.py --no-push          (skip git commit/push)

Requires: pip install requests
"""
import argparse
import gzip
import hashlib
import json
import subprocess
import sys
import time
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
except ImportError:
    print("Requires the 'requests' package: pip install requests", file=sys.stderr)
    sys.exit(1)

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_tier2_manifest  # noqa: E402  (per-report reproducibility manifest, 3a audit §1.1b)

# --- constants -------------------------------------------------------------
BASE = "https://darkmoon.ascensionlogs.gg"
REALM = "darkmoon"
SEASON = 10

REPO_ROOT = Path(__file__).resolve().parents[2]
CRAWL_ROOT = REPO_ROOT / "data" / "source" / "crawl"
SCAN_LOG_PATH = CRAWL_ROOT / "scan_log.json"
PATCH_DATE_FILE = REPO_ROOT / "data" / "source" / "changelog" / "latest_patch_date.txt"
WATCHLIST_PATH = Path(__file__).resolve().parent / "watchlist.txt"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Referer": f"{BASE}/",
    "Accept": "application/json",
}

# --- storage tiers (session 0b, 2026-08-04) --------------------------------
# TIER 1 (committed): small and IRREPLACEABLE — point-in-time state that cannot be
#   re-fetched once it changes. Armory snapshots and leaderboard standings are gone
#   the moment a phase flips or a player regears.
# TIER 2 (local only, gitignored): bulk and RE-FETCHABLE — derived from reports,
#   which persist on ascensionlogs.gg and can be re-pulled by report id. ~99% of the
#   bytes, ~0% of the irreplaceability.
# Every run writes a COMMITTED manifest.json describing tier-2 files (record counts,
# sha256, sizes, report ids) so git always knows what was captured even when it does
# not hold the bytes — ARCHITECTURE §2.12's intent without the gigabytes.
TIER1_WRITERS = ["phases", "leaderboards", "reports", "characters"]
TIER2_WRITERS = ["abilities", "healing", "avoidance", "damage_taken"]

DIFFICULTIES = ["ascended", "normal"]
ROLES = ["dps", "tank", "support"]          # support = healers (verified 2026-08-04)
TAIL_404_LIMIT = 20                          # consecutive missing report IDs before stopping
BOSS_SINGLE_LIMIT = 40                       # >this many boss encounters -> group by boss_id
RESCOUT_HOURS = 20                           # re-pull a character's armory if older than this

# Phase 3 T8 re-verification (owner approved 2026-08-06). Discovery is
# incremental: a character is re-pulled only when they turn up in that day's
# leaderboards or reports. Someone who respecs and then stops parsing is
# therefore frozen in the corpus at their old build forever — the exact
# "incremental-only misses changes to characters already seen" gap T8 names.
# So: a slow rolling sweep of KNOWN characters who did not appear this run,
# oldest-capture-first, hard-capped per run. Content-hash dedupe already means
# an unchanged build costs one request and writes nothing, so the cost is
# REVERIFY_PER_RUN requests/day, not a second full crawl.
REVERIFY_AFTER_DAYS = 7                      # a known character is stale after this
REVERIFY_PER_RUN = 40                        # hard cap on extra armory pulls per run
ROTATE_BYTES = 40 * 1024 * 1024              # rotate a .jsonl.gz at 40 MB (GitHub 100 MB blob cap)

# --- module state ----------------------------------------------------------
STATS = {"requests": 0, "errors": 0, "retries": 0}
ERRORS = []          # (context, detail) tuples for the end-of-run summary
DELAY = 0.6          # seconds between requests; overridable via --delay


def api_get(path, ok_statuses=(200,)):
    """GET with rate limit + retry/backoff. Returns (status, parsed_json_or_None).

    Statuses outside ok_statuses+404 are retried up to 3 times, then recorded as
    errors. 404 is returned as-is (it is a meaningful signal for report probing).
    """
    url = f"{BASE}{path}"
    for attempt in range(3):
        time.sleep(DELAY)
        STATS["requests"] += 1
        try:
            r = requests.get(url, timeout=30, headers=HEADERS)
        except requests.RequestException as e:
            STATS["retries"] += 1
            time.sleep(10 * (attempt + 1))
            last_err = str(e)
            continue
        if r.status_code in ok_statuses:
            try:
                return r.status_code, r.json()
            except ValueError:
                last_err = f"non-JSON body ({len(r.text)} bytes)"
                break
        if r.status_code == 404:
            return 404, None
        if r.status_code in (429, 500, 502, 503, 504):
            STATS["retries"] += 1
            time.sleep(30 * (attempt + 1))
            last_err = f"HTTP {r.status_code}"
            continue
        last_err = f"HTTP {r.status_code}: {r.text[:200]}"
        break
    STATS["errors"] += 1
    ERRORS.append((path, last_err))
    return None, None


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def read_patch_date():
    if PATCH_DATE_FILE.exists():
        val = PATCH_DATE_FILE.read_text(encoding="utf-8").strip()
        return val or None
    return None


class NdjsonWriter:
    """Appends stamped records to <date_dir>/<name>.jsonl.gz, rotating at ROTATE_BYTES.

    GZIPPED ON PURPOSE (session 0b, 2026-08-04). Measured: 3 reports produced
    116 MB uncompressed, and `avoidance` crossed the 50 MB rotation boundary on
    its own — a full historical walk would be multiple GB in the working tree and
    would keep colliding with GitHub's 100 MB per-file limit.

    Note the honest accounting: git already zlib-compresses blobs, so this is
    roughly neutral for `.git` size. The wins are (a) clone/working-tree size,
    (b) headroom under the 100 MB per-file ceiling. ARCHITECTURE §2.12's
    "committed files are readable by a chat session" concern does not apply at
    this scale — a 50 MB JSONL is unreadable through raw.githubusercontent.com
    either way. Everything a human or chat session actually reads (docs, seed
    scripts, index/scouted/*.json) stays plain text.

    Appending reopens the file per record, producing a multi-member gzip stream.
    That is valid and read transparently by gzip.open()/zcat — and it keeps the
    crash-safety property that a Ctrl+C costs at most the record in flight.
    """

    def __init__(self, date_dir, name, patch_date):
        self.dir = date_dir
        self.name = name
        self.patch_date = patch_date
        self.part = 0
        self.count = 0
        self._resolve_part()

    def _path(self):
        suffix = f".{self.part}" if self.part else ""
        return self.dir / f"{self.name}{suffix}.jsonl.gz"

    def _resolve_part(self):
        # If today's file already exists near the cap (resumed run), move to the next part.
        while self._path().exists() and self._path().stat().st_size >= ROTATE_BYTES:
            self.part += 1

    def write(self, record_type, payload, **extra):
        record = {
            "record_type": record_type,
            "captured_at": now_iso(),
            "realm": REALM,
            "season": SEASON,
            "patch_date": self.patch_date,
            **extra,
            "payload": payload,
        }
        path = self._path()
        self.dir.mkdir(parents=True, exist_ok=True)
        with gzip.open(path, "at", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        self.count += 1
        if path.stat().st_size >= ROTATE_BYTES:
            self.part += 1


def load_scan_log():
    if SCAN_LOG_PATH.exists():
        return json.loads(SCAN_LOG_PATH.read_text(encoding="utf-8"))
    return {
        "next_report_id": 1,
        "reports": {},          # id -> {crawled_at, encounters, bosses}
        "missing_reports": [],  # ids 404ing *below* a later live id — permanently absent
        "characters": {},       # id -> {name, last_armory_at}
        "pending_characters": {},  # id -> name, seen but deferred by --max-armory
        "retry_reports": [],    # ids that failed at request level — retried before the frontier
    }


def save_scan_log(log):
    SCAN_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    SCAN_LOG_PATH.write_text(json.dumps(log, indent=1), encoding="utf-8")


# --- crawl stages ----------------------------------------------------------

def crawl_watchlist(seen_characters, scan_log):
    """Resolve watchlist.txt names to character ids and force them into this run's
    capture set. Leaderboard/report discovery only finds characters who parsed that
    day, so without this a personal character goes uncaptured on any day it doesn't
    raid — leaving holes in exactly the gear/build timeline the build docs rely on.

    Resolved ids are cached in scan_log so a later run doesn't re-resolve, and an
    unresolvable name is reported loudly rather than silently dropped."""
    if not WATCHLIST_PATH.exists():
        return 0
    names = [ln.strip() for ln in WATCHLIST_PATH.read_text(encoding="utf-8").splitlines()]
    names = [n for n in names if n and not n.startswith("#")]
    if not names:
        return 0

    cache = scan_log.setdefault("watchlist_ids", {})
    added = 0
    for name in names:
        cid = cache.get(name)
        if cid is None:
            _, d = api_get(f"/api/armory/by-name/{urllib.parse.quote(name)}")
            if not d or not d.get("success") or not (d.get("character") or {}).get("id"):
                msg = (f"watchlist name '{name}' did not resolve "
                       f"(no armory record, or name mismatch)")
                print(f"[watchlist] ⚠ {msg}")
                ERRORS.append(("watchlist", msg))
                continue
            cid = d["character"]["id"]
            cache[name] = cid
        seen_characters[str(cid)] = name
        added += 1
    print(f"[watchlist] {added}/{len(names)} watched character(s) queued for capture")
    return added


def crawl_phases(writers):
    """Snapshot /api/phases daily — phase timeline + active flags are load-bearing
    for §2.10's per-phase gear tiers, and cheap to capture."""
    _, d = api_get("/api/phases")
    if d is None:
        return []
    writers["phases"].write("phases_snapshot", d)
    active = [p for p in d.get("phases", []) if p.get("is_active")]
    print(f"[phases] {len(d.get('phases', []))} phases, active: "
          f"{[p.get('phase_number') for p in active]}")
    return active


def crawl_leaderboards(writers, active_phases, seen_characters):
    """Walk zones x difficulties x roles for every active phase. Raw responses are
    kept whole; character ids/names are collected for the armory stage."""
    n = 0
    for phase in active_phases:
        phase_num = phase.get("phase_number")
        locations = [loc.get("location") for loc in phase.get("locations", [])]
        for location in locations:
            if not location:
                continue
            loc_q = urllib.parse.quote(location)
            for difficulty in DIFFICULTIES:
                for role in ROLES:
                    metrics = ["avg_dps"] if role != "support" else ["avg_dps", "avg_hps"]
                    for metric in metrics:
                        path = (f"/api/encounters/rankings/overall?location={loc_q}"
                                f"&difficulty={difficulty}&phase={phase_num}&metric={metric}"
                                f"&page=1&limit=100&role={role}&cohort=global")
                        status, d = api_get(path, ok_statuses=(200, 400))
                        if d is None or status == 400 or not d.get("success", True):
                            continue
                        zone_data = (d.get("rankings") or {}).get(location) or {}
                        rows = [e for entries in zone_data.values() for e in entries]
                        if not rows:
                            continue
                        writers["leaderboards"].write(
                            "leaderboard", d,
                            query={"location": location, "difficulty": difficulty,
                                   "phase": phase_num, "role": role, "metric": metric},
                        )
                        n += 1
                        for e in rows:
                            cid, cname = e.get("character_id"), e.get("name")
                            if cid:
                                seen_characters[str(cid)] = cname
        print(f"[leaderboards] phase {phase_num}: cumulative non-empty boards={n}, "
              f"characters seen={len(seen_characters)}")
    return n


def fetch_encounter_data(writers, report_id, encounter_ids, scope_note, seen_characters):
    """The four per-ability endpoints for one encounter-id set. Player rows are
    also mined for character ids so report participants get armory pulls even
    when they never appear on a leaderboard."""
    ids_q = ",".join(str(i) for i in encounter_ids)
    common = f"?scope=encounter&encounterIds={ids_q}&format=flat&limit=10000"
    calls = [
        ("abilities", f"/api/reports/{report_id}/character_spell_damage{common}&participantType=friendlies"),
        ("healing", f"/api/reports/{report_id}/character_spell_healing{common}&participantType=friendlies"),
        ("avoidance", f"/api/reports/{report_id}/character_damage_taken_abilities{common}&participantType=enemies"),
        ("damage_taken", f"/api/reports/{report_id}/character_damage_taken_abilities{common}&participantType=friendlies"),
    ]
    for writer_name, path in calls:
        _, d = api_get(path)
        if d is None:
            continue
        writers[writer_name].write(
            writer_name, d,
            report_id=report_id, encounter_ids=list(encounter_ids), scope=scope_note,
        )
        for row in d.get("rows", []) or []:
            cid = row.get("character_id")
            if cid and row.get("character_type") == "player":
                seen_characters.setdefault(str(cid), row.get("character_name"))


def crawl_reports(writers, scan_log, seen_characters, max_reports=None):
    """Report-ID walk: first any ids that failed at request level on an earlier run,
    then sequentially from the frontier. Stops after TAIL_404_LIMIT consecutive 404s
    or max_reports crawled reports."""
    consecutive_404 = 0
    pending_404 = []
    crawled = 0
    missing = set(scan_log.get("missing_reports", []))
    retry = list(scan_log.get("retry_reports", []))
    if retry:
        print(f"[reports] retrying {len(retry)} previously-failed report(s): {retry[:10]}")

    def id_stream():
        """Retry ids first (snapshotted, so the loop body may mutate `retry` freely),
        then the frontier walked upward forever."""
        for rid in tuple(retry):
            yield rid, True
        rid = scan_log["next_report_id"]
        while True:
            yield rid, False
            rid += 1

    ids = id_stream()

    while consecutive_404 < TAIL_404_LIMIT:
        if max_reports is not None and crawled >= max_reports:
            print(f"[reports] --max-reports {max_reports} reached")
            break
        report_id, in_retry_phase = next(ids)
        if str(report_id) in scan_log["reports"] or report_id in missing:
            continue

        status, d = api_get(f"/api/reports/{report_id}/encounters?includeTrash=true")
        if status == 404:
            if in_retry_phase:
                # a retry id that is now a confirmed 404 is genuinely absent
                missing.add(report_id)
                if report_id in retry:
                    retry.remove(report_id)
                scan_log["retry_reports"] = retry
                scan_log["missing_reports"] = sorted(missing)
                continue
            consecutive_404 += 1
            pending_404.append(report_id)
            continue
        if d is None:
            # request-level failure, NOT a 404 — never mark missing, and never let the
            # frontier advance past it silently. Queue it for the next run.
            if report_id not in retry:
                retry.append(report_id)
            scan_log["retry_reports"] = sorted(retry)
            scan_log["next_report_id"] = max(scan_log["next_report_id"], report_id + 1)
            save_scan_log(scan_log)
            continue

        # a live report: everything 404ing before it is genuinely absent
        missing.update(pending_404)
        pending_404 = []
        consecutive_404 = 0
        if report_id in retry:
            retry.remove(report_id)
            scan_log["retry_reports"] = retry

        encounters = d.get("encounters", [])
        writers["reports"].write("report_encounters", d, report_id=report_id)

        bosses = [e for e in encounters if e.get("is_boss_encounter")]
        trash = [e for e in encounters if not e.get("is_boss_encounter")]
        if len(bosses) <= BOSS_SINGLE_LIMIT:
            for enc in bosses:
                fetch_encounter_data(writers, report_id, [enc["id"]], "boss_single",
                                     seen_characters)
        else:
            groups = {}
            for enc in bosses:
                groups.setdefault(enc.get("boss_id"), []).append(enc["id"])
            print(f"[reports] #{report_id}: grind report ({len(bosses)} boss attempts) "
                  f"-> {len(groups)} boss_id groups")
            for boss_id, enc_ids in groups.items():
                fetch_encounter_data(writers, report_id, enc_ids, f"boss_group:{boss_id}",
                                     seen_characters)
        if trash:
            fetch_encounter_data(writers, report_id, [e["id"] for e in trash], "trash_bundle",
                                 seen_characters)

        scan_log["reports"][str(report_id)] = {
            "crawled_at": now_iso(), "encounters": len(encounters), "bosses": len(bosses),
        }
        scan_log["missing_reports"] = sorted(missing)
        scan_log["next_report_id"] = max(scan_log["next_report_id"], report_id + 1)
        save_scan_log(scan_log)
        crawled += 1
        print(f"[reports] #{report_id}: {len(encounters)} encounters ({len(bosses)} bosses) "
              f"[{crawled} crawled this run]")

    # trailing 404s are NOT marked missing — they may exist tomorrow
    scan_log["retry_reports"] = sorted(retry)
    scan_log["missing_reports"] = sorted(missing)
    save_scan_log(scan_log)
    print(f"[reports] {crawled} new reports; frontier at {scan_log['next_report_id']}, "
          f"tail of {consecutive_404} consecutive 404s"
          + (f", {len(retry)} queued for retry" if retry else ""))
    return crawled


def queue_reverification(scan_log, seen_characters, limit=REVERIFY_PER_RUN,
                         after_days=REVERIFY_AFTER_DAYS):
    """Add stale KNOWN characters (not seen this run) to the capture queue.

    Oldest capture first, so the sweep rolls through the whole population
    rather than re-checking the same few. Returns the number queued.
    """
    now = datetime.now(timezone.utc)
    candidates = []
    for cid, info in (scan_log.get("characters") or {}).items():
        if cid in seen_characters:
            continue
        last = info.get("last_armory_at")
        if not last:
            candidates.append((None, cid, info.get("name")))
            continue
        try:
            age_days = (now - datetime.fromisoformat(last)).total_seconds() / 86400
        except ValueError:
            continue
        if age_days >= after_days:
            candidates.append((last, cid, info.get("name")))
    # None-sorts-first: never-captured characters go before merely stale ones
    candidates.sort(key=lambda c: (c[0] is not None, c[0] or ""))
    for _last, cid, name in candidates[:limit]:
        seen_characters[cid] = name
    if candidates:
        print(f"[reverify] {min(len(candidates), limit)} of {len(candidates)} stale "
              f"known character(s) queued (>= {after_days}d since last capture)")
    return min(len(candidates), limit)


def crawl_characters(writers, scan_log, seen_characters, max_armory):
    """Armory + capture history + primary-stat for new/stale characters seen this run
    (plus anything deferred by --max-armory on a previous run)."""
    queue = dict(scan_log.get("pending_characters", {}))
    queue.update(seen_characters)
    # Watched characters go first so --max-armory can never starve them.
    watched = {str(cid): name
               for name, cid in (scan_log.get("watchlist_ids") or {}).items()}
    queue = {**watched, **{k: v for k, v in queue.items() if k not in watched}}
    pulled = 0
    unchanged = 0
    deferred = {}
    for cid, cname in queue.items():
        if pulled >= max_armory:
            deferred[cid] = cname
            continue
        known = scan_log["characters"].get(cid)
        if known and known.get("last_armory_at"):
            age_h = (datetime.now(timezone.utc)
                     - datetime.fromisoformat(known["last_armory_at"])).total_seconds() / 3600
            if age_h < RESCOUT_HOURS:
                continue

        _, armory = api_get(f"/api/armory/character/{cid}")
        if armory is None:
            continue

        # Content-hash dedupe: gear/build/stats change rarely, but a full armory
        # record is ~90 KB. Re-writing every character every day would be tens of MB
        # of near-identical data. Storing only on change collapses that AND yields
        # exactly the gear/build timeline INDEX_GUIDE wants.
        # Hashed over ci_resolved + stats_summary only — `capture` and `captures`
        # carry ids/timestamps that churn without the build actually changing.
        fingerprint = hashlib.sha256(json.dumps(
            {"ci": armory.get("ci_resolved"), "stats": armory.get("stats_summary")},
            sort_keys=True, ensure_ascii=False, default=str,
        ).encode("utf-8")).hexdigest()

        if known and known.get("armory_hash") == fingerprint:
            scan_log["characters"][cid] = {
                **known, "name": cname, "last_armory_at": now_iso(),
            }
            unchanged += 1
            continue

        _, captures = api_get(f"/api/armory/character/{cid}/captures?limit=100")
        primary_stat = None
        if cname:
            _, primary_stat = api_get(f"/api/characters/{urllib.parse.quote(str(cname))}/primary-stat")

        writers["characters"].write(
            "character_armory",
            {"armory": armory, "captures": captures, "primary_stat": primary_stat},
            character_id=int(cid), character_name=cname,
            previous_hash=(known or {}).get("armory_hash"), armory_hash=fingerprint,
        )
        # capture history links characters to reports we may not have discovered yet
        for cap in (captures or {}).get("captures", []):
            rep = (cap.get("encounter") or {}).get("report_id")
            if rep and str(rep) not in scan_log["reports"]:
                pass  # sequential walk will reach it; noted here for visibility only

        scan_log["characters"][cid] = {
            "name": cname, "last_armory_at": now_iso(), "armory_hash": fingerprint,
        }
        scan_log.get("pending_characters", {}).pop(cid, None)
        pulled += 1
        if pulled % 10 == 0:
            save_scan_log(scan_log)
            print(f"[characters] {pulled} changed armories written "
                  f"({unchanged} unchanged, skipped)...")
    if deferred:
        print(f"[characters] --max-armory {max_armory} reached; "
              f"{len(deferred)} queued for next run")
    scan_log.setdefault("pending_characters", {}).update(deferred)
    save_scan_log(scan_log)
    print(f"[characters] {pulled} armory records written, {unchanged} unchanged/skipped "
          f"({len(scan_log['characters'])} characters known)")
    return pulled


def write_manifest(date_dir, writers, scan_log, patch_date, new_report_ids):
    """Write a COMMITTED manifest describing every capture file, including the
    gitignored tier-2 bulk. This is what keeps ARCHITECTURE §2.12 honest: git may
    not hold the bytes, but it always records that they existed, how many records,
    their sha256, and which report ids they cover — so a future session can tell
    the difference between "never captured" and "captured, stored locally", and can
    verify or re-fetch deliberately."""
    files = []
    for path in sorted(date_dir.glob("*.jsonl.gz")):
        stem = path.name.split(".")[0]
        h = hashlib.sha256()
        records = 0
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        with gzip.open(path, "rt", encoding="utf-8") as f:
            for _ in f:
                records += 1
        files.append({
            "file": path.name,
            "tier": 1 if stem in TIER1_WRITERS else 2,
            "committed": stem in TIER1_WRITERS,
            "records": records,
            "bytes_gz": path.stat().st_size,
            "sha256": h.hexdigest(),
        })

    manifest = {
        "date": date_dir.name,
        "captured_at": now_iso(),
        "realm": REALM,
        "season": SEASON,
        "patch_date": patch_date,
        "new_report_ids": sorted(new_report_ids),
        "reports_known": len(scan_log.get("reports", {})),
        "characters_known": len(scan_log.get("characters", {})),
        "tier2_note": ("tier-2 files are gitignored; re-fetchable from "
                       "darkmoon.ascensionlogs.gg by report id — see "
                       "tools/scrapers/README.md"),
        "files": files,
    }
    (date_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=1), encoding="utf-8")
    return manifest


# --- git -------------------------------------------------------------------

def git_commit_push(date_str):
    """Commit data/source and push. Returns human-readable status string."""
    def run(*args):
        return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True,
                              text=True, timeout=300)

    run("add", "data/source")
    diff = run("diff", "--cached", "--stat")
    if not diff.stdout.strip():
        return "nothing new to commit"
    c = run("commit", "-m",
            f"crawl: {date_str} daily capture (ascensionlogs + changelog)\n\n"
            f"Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>")
    if c.returncode != 0:
        return f"COMMIT FAILED: {c.stderr.strip()[:300]}"
    p = run("push")
    if p.returncode != 0:
        return f"committed locally, PUSH FAILED: {p.stderr.strip()[:300]}"
    return "committed and pushed"


# --- main ------------------------------------------------------------------

def main():
    global DELAY
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--max-reports", type=int, default=None,
                    help="cap new reports this run (useful for a watchable first run)")
    ap.add_argument("--max-armory", type=int, default=400,
                    help="cap armory pulls this run (default 400)")
    ap.add_argument("--delay", type=float, default=DELAY,
                    help=f"seconds between requests (default {DELAY})")
    ap.add_argument("--reverify", type=int, nargs="?", const=REVERIFY_PER_RUN,
                    default=REVERIFY_PER_RUN, metavar="N",
                    help=f"re-check up to N known characters not seen this run, "
                         f"oldest capture first, to catch respecs "
                         f"(default {REVERIFY_PER_RUN}; 0 disables)")
    ap.add_argument("--no-push", action="store_true", help="skip git commit/push")
    ap.add_argument("--recrawl-report", type=int, metavar="ID", action="append",
                    help="re-fetch one report's tier-2 data (repeatable). This is the "
                         "documented recovery path for gitignored bulk capture")
    args = ap.parse_args()
    DELAY = args.delay
    # line-buffer stdout so progress is visible when output is redirected
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except AttributeError:
        pass

    started = time.time()
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    date_dir = CRAWL_ROOT / date_str
    patch_date = read_patch_date()

    writer_names = ["phases", "leaderboards", "reports", "abilities", "healing",
                    "avoidance", "damage_taken", "characters"]
    writers = {n: NdjsonWriter(date_dir, n, patch_date) for n in writer_names}

    scan_log = load_scan_log()
    seen_characters = {}

    print(f"=== crawl_ascensionlogs {date_str} (realm={REALM}, season={SEASON}, "
          f"patch_date={patch_date or 'UNKNOWN'}) ===")

    if args.recrawl_report:
        # Recovery path for gitignored tier-2 data. Fetches only the named reports
        # and exits — no leaderboard walk, no armory pulls, no frontier advance.
        print(f"[recrawl] re-fetching {len(args.recrawl_report)} report(s): "
              f"{args.recrawl_report}")
        for rid in args.recrawl_report:
            status, d = api_get(f"/api/reports/{rid}/encounters?includeTrash=true")
            if d is None:
                print(f"[recrawl] #{rid}: {'not found' if status == 404 else 'fetch failed'}")
                continue
            encounters = d.get("encounters", [])
            writers["reports"].write("report_encounters", d, report_id=rid)
            bosses = [e for e in encounters if e.get("is_boss_encounter")]
            trash = [e for e in encounters if not e.get("is_boss_encounter")]
            if len(bosses) <= BOSS_SINGLE_LIMIT:
                for enc in bosses:
                    fetch_encounter_data(writers, rid, [enc["id"]], "boss_single",
                                         seen_characters)
            else:
                groups = {}
                for enc in bosses:
                    groups.setdefault(enc.get("boss_id"), []).append(enc["id"])
                for boss_id, enc_ids in groups.items():
                    fetch_encounter_data(writers, rid, enc_ids, f"boss_group:{boss_id}",
                                         seen_characters)
            if trash:
                fetch_encounter_data(writers, rid, [e["id"] for e in trash],
                                     "trash_bundle", seen_characters)
            print(f"[recrawl] #{rid}: {len(encounters)} encounters re-fetched")
        write_manifest(date_dir, writers, scan_log, patch_date, args.recrawl_report)
        build_tier2_manifest.build_for_dir(date_dir)
        print(f"\nRecrawl complete. {STATS['requests']} requests, {len(ERRORS)} errors.")
        return 0 if not ERRORS else 1

    active_phases = crawl_phases(writers)
    crawl_watchlist(seen_characters, scan_log)
    crawl_leaderboards(writers, active_phases, seen_characters)
    reports_before = set(scan_log.get("reports", {}))
    new_reports = crawl_reports(writers, scan_log, seen_characters, args.max_reports)
    reverified = 0
    if args.reverify:
        reverified = queue_reverification(scan_log, seen_characters,
                                          limit=args.reverify)
    armory_pulls = crawl_characters(writers, scan_log, seen_characters, args.max_armory)

    new_report_ids = [int(r) for r in set(scan_log.get("reports", {})) - reports_before]
    manifest = write_manifest(date_dir, writers, scan_log, patch_date, new_report_ids)
    build_tier2_manifest.build_for_dir(date_dir)
    t1 = sum(f["bytes_gz"] for f in manifest["files"] if f["tier"] == 1)
    t2 = sum(f["bytes_gz"] for f in manifest["files"] if f["tier"] == 2)

    total_bytes = sum(f.stat().st_size for f in date_dir.glob("*.jsonl.gz")) if date_dir.exists() else 0
    commit_status = "skipped (--no-push)"
    if not args.no_push:
        commit_status = git_commit_push(date_str)

    elapsed = time.time() - started
    print("\n" + "=" * 62)
    print(f"RUN SUMMARY — {date_str}")
    print(f"  elapsed:          {elapsed/60:.1f} min")
    print(f"  HTTP requests:    {STATS['requests']} ({STATS['retries']} retries)")
    print(f"  new reports:      {new_reports}")
    print(f"  armory records:   {armory_pulls} written (changed only — unchanged builds skipped)")
    print(f"  re-verified:      {reverified} stale known character(s) queued "
          f"(respec sweep)" if reverified else
          "  re-verified:      0 (nothing stale, or --reverify 0)")
    print(f"  records written:  " + ", ".join(f"{n}={w.count}" for n, w in writers.items() if w.count))
    print(f"  output size:      {total_bytes/1e6:.1f} MB in {date_dir}")
    print(f"    tier 1 (committed):  {t1/1e6:.1f} MB")
    print(f"    tier 2 (local only): {t2/1e6:.1f} MB  — re-fetchable by report id")
    print(f"  patch_date stamp: {patch_date or '⚠ NULL — run fetch_changelog.py first'}")
    print(f"  git:              {commit_status}")
    if ERRORS:
        print(f"  ⚠ ERRORS ({len(ERRORS)}):")
        for path, err in ERRORS[:10]:
            print(f"    {path} -> {err}")
        if len(ERRORS) > 10:
            print(f"    ... and {len(ERRORS) - 10} more")
    ok = not ERRORS and "FAILED" not in commit_status
    print(f"  RESULT:           {'OK' if ok else 'COMPLETED WITH ERRORS'}")
    print("=" * 62)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
