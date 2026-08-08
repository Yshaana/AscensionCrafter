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

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
import season_config  # noqa: E402  (realm/season/phase constants + live assertions, 3d A1)

# --- constants -------------------------------------------------------------
# Realm and season come from season_config.py — the ONE place they are written
# down (3d A1). They used to be hardcoded here and in four other files with
# nothing checking any of them against the live server; `assert_realm()` and
# `assert_phase()` below close that.
BASE = f"https://{season_config.REALM_SLUG}.ascensionlogs.gg"
REALM = season_config.REALM_SLUG
SEASON = season_config.SEASON_NUMBER
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
    for §2.10's per-phase gear tiers, and cheap to capture.

    ALSO the assertion point for this clone's declared server state (3d A1).
    `season_config.assert_phase()` raises `RealmSeasonMismatch` — deliberately
    NOT caught here — if the server has moved to a phase this clone does not
    expect. The whole run dies before a single record is stamped, because a
    day captured against a stale phase constant cannot be repaired afterwards.

    ⚠ The check reads `name` + `progression_parent_phase_id`, never
    `phase_number`: the live record whose `phase_number` is 2 is named
    "Phase 1.1" and is a CHILD of Phase 1.
    """
    _, d = api_get("/api/phases")
    if d is None:
        raise season_config.RealmSeasonMismatch(
            "/api/phases could not be fetched. Refusing to capture a day of "
            "records without verifying which phase the server is on.")
    writers["phases"].write("phases_snapshot", d)
    live = season_config.assert_phase(d)
    active = season_config.active_phases(d)
    print(f"[phases] {len(d.get('phases', []))} phases; "
          f"{season_config.describe_phases(d)}")
    print(f"[phases] ✅ phase assertion passed: server is on {live['name']!r}, "
          f"matching season_config.EXPECTED_PHASE_NAME")
    return active


def crawl_leaderboards(writers, active_phases, seen_characters):
    """Walk zones x difficulties x roles for every active phase. Raw responses are
    kept whole; character ids/names are collected for the armory stage.

    Returns `(written, attempted)`.

    🆕 `3m` pre-flight (`AUDIT_3L` F17) — `attempted` is new and it is what makes
    the canary satisfiable. This function's output volume is
    `active phases × locations × difficulties × roles × metrics`, so it moves
    with legitimate SERVER state: when Zul'Gurub and Phase 1.1 went inactive on
    2026-08-08 the boards fell 12 → 2 and the canary, normalising by run count,
    read that as an 83% shape break and refused the commit at every logon.
    Recording the denominator turns the comparison into a YIELD, which is the
    thing the threshold was always meant to test — a changed payload shape drops
    written while attempted stays put.
    """
    n = 0
    attempted = 0
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
                        attempted += 1
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
        print(f"[leaderboards] phase {phase_num}: cumulative non-empty boards={n}"
              f"/{attempted} attempted, characters seen={len(seen_characters)}")
    return n, attempted


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


def write_manifest(date_dir, writers, scan_log, patch_date, new_report_ids,
                   leaderboard_queries_attempted=None, active_phase_count=None):
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
        # 🆕 3m (AUDIT_3L F17) — the leaderboard canary's DENOMINATOR. Board
        # volume is `active phases x locations x difficulties x roles x metrics`,
        # so it moves with legitimate server state; without the attempt count the
        # canary can only compare raw yield-per-run and a completed phase
        # transition trips it permanently. NULL on a recrawl (which walks no
        # leaderboards) and on every manifest written before 2026-08-08 — the
        # canary says so explicitly rather than comparing against a missing
        # denominator.
        "leaderboard_queries_attempted": leaderboard_queries_attempted,
        "active_phase_count": active_phase_count,
        "tier2_note": ("tier-2 files are gitignored; re-fetchable from "
                       "darkmoon.ascensionlogs.gg by report id — see "
                       "tools/scrapers/README.md"),
        "files": files,
    }
    (date_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=1), encoding="utf-8")
    return manifest


# --- canary ----------------------------------------------------------------
# 3d A3. The exit code used to be gated ONLY on request-level ERRORS, so a 200
# response with changed JSON shape yields 0 phases -> 0 leaderboards -> exit 0,
# day stamped success, empty capture committed. Nothing anywhere compared a
# run's output volume against anything.
#
# 🛑 SCOPE, and it is deliberate: this canary covers the writers whose volume is
# STRUCTURALLY STABLE run-to-run, not all eight. Measured across the committed
# manifests:
#
#     2026-08-04  leaderboards=28  reports=28  abilities=827  characters=218
#     2026-08-05  leaderboards=12  reports=50  abilities=702  characters=275
#     2026-08-06  leaderboards=24  reports=4   abilities=15   characters=0
#
# `reports`/`abilities`/`healing`/`avoidance`/`damage_taken` are driven by how
# many NEW reports exist that day, and `characters` by how many builds actually
# CHANGED (content-hash dedupe writes nothing for an unchanged build). All of
# them legitimately hit zero or drop >50%. Canarying them would produce a daily
# false alarm, and an alarm that cries wolf is worse than none — the operator
# learns to ignore the one signal that matters.
#
# `phases` and `leaderboards` are different: the server always has an active
# phase and always has populated boards, so zero means the SHAPE changed. Those
# two are exactly the failure the audit named ("0 phases -> 0 leaderboards").
CANARY_WRITERS = ["phases", "leaderboards"]
CANARY_DROP_RATIO = 0.5      # fail if a writer falls below half the previous day's rate


def leaderboard_query_keys(day_dir):
    """`(attempted, written)` sets of leaderboard query keys for one day folder.

    A key is `(location, difficulty, phase_number, role, metric)` — the exact
    tuple `crawl_leaderboards` walks. **Both sets are derived from COMMITTED
    tier-1 captures**, so this is auditable after the fact and needs no extra
    stored state: `attempted` is rebuilt from that day's `/api/phases` snapshots
    (the walk is a deterministic function of the active phases and their
    `locations`), `written` is read from the `query` field the leaderboard
    writer already records on every row.

    🛑 `phase_number` is part of the key ON PURPOSE. Zul'Gurub appears in the
    `locations` array of Phase 2 as well as Phase 1, but a ZG board queried
    under phase 3 is a different leaderboard from the same board under phase 1 —
    collapsing them would let a retired phase's populated boards masquerade as
    the new phase's.
    """
    attempted, written = set(), set()
    ph_path = day_dir / "phases.jsonl.gz"
    if ph_path.exists():
        try:
            with gzip.open(ph_path, "rt", encoding="utf-8") as f:
                for line in f:
                    rec = json.loads(line)
                    payload = rec.get("payload") or rec
                    for phase in (payload.get("phases") or []):
                        if not phase.get("is_active"):
                            continue
                        pnum = phase.get("phase_number")
                        for loc in (phase.get("locations") or []):
                            location = loc.get("location")
                            if not location:
                                continue
                            for difficulty in DIFFICULTIES:
                                for role in ROLES:
                                    metrics = (["avg_dps", "avg_hps"]
                                               if role == "support" else ["avg_dps"])
                                    for metric in metrics:
                                        attempted.add((location, difficulty, pnum,
                                                       role, metric))
        except (OSError, ValueError):
            return set(), set()
    lb_path = day_dir / "leaderboards.jsonl.gz"
    if lb_path.exists():
        try:
            with gzip.open(lb_path, "rt", encoding="utf-8") as f:
                for line in f:
                    q = (json.loads(line).get("query") or {})
                    written.add((q.get("location"), q.get("difficulty"),
                                 q.get("phase"), q.get("role"), q.get("metric")))
        except (OSError, ValueError):
            return attempted, set()
    return attempted, written


def previous_manifest(date_dir):
    """The most recent prior day's manifest.json, or None on the first ever run.

    Deliberately skips the `baseline_phase1` folder — it is a one-shot artifact
    with its own cadence, not a daily capture, so it is not a baseline for
    "did today look like yesterday".

    Returns `(manifest, day_dir)` — the folder too, because the canary now reads
    the previous day's committed leaderboard capture, not only its record count.
    """
    if not CRAWL_ROOT.exists():
        return None, None
    days = sorted(p for p in CRAWL_ROOT.iterdir()
                  if p.is_dir() and p.name < date_dir.name
                  and (p / "manifest.json").exists()
                  and p.name[:4].isdigit())
    if not days:
        return None, None
    try:
        return json.loads(
            (days[-1] / "manifest.json").read_text(encoding="utf-8")), days[-1]
    except (OSError, ValueError):
        return None, None


def canary_check(manifest, prev, date_dir=None, prev_dir=None):
    """Compare this run's per-writer volume against the previous day's.

    Returns `(failures, notes)` — both lists of human-readable strings. A
    non-empty `failures` blocks the commit; `notes` are printed and block
    nothing.

    🚨 `3m` pre-flight (`AUDIT_3L` F17) — THE LEADERBOARD ARM IS A CARRY-OVER
    TEST NOW, AND THE ROUTE THERE IS WORTH RECORDING BECAUSE TWO OBVIOUS FIXES
    ARE WRONG.

    The failure: `canary_check` divided by the RUN count, and leaderboard volume
    is not run-driven. On 2026-08-08 Zul'Gurub and Phase 1.1 went inactive,
    boards fell 12 → 2/run, the canary read −83% against a 50% threshold and
    refused the commit. It was right to refuse an unexplained drop — but it had
    **no way to ever be satisfied**: failures are deliberately not stamped, so
    the scheduled task retried and failed identically at every logon. A guard
    that cannot be satisfied gets switched off, and that costs the real signal.

    🛑 `CANARY_DROP_RATIO` IS NOT RAISED. Loosening a threshold after watching it
    fire is redefining a check by its result.

    ⚠ **`AUDIT_3L` F17 proposed normalising by active-phase count, and MEASURED
    ON THE COMMITTED CAPTURES THAT DOES NOT WORK.** Nor does normalising by
    attempted queries, which was this fix's first draft:

        day         written  attempted  yield   boards/run  active phases
        2026-08-06       36       1200   3.00%        12.0   2
        2026-08-07       12        400   3.00%        12.0   2
        2026-08-08        4        400   1.00%         2.0   1

    Every structural denominator still shows a ~67% drop, because **the thing
    that collapsed is not query structure, it is content population**: Molten
    Core was ~13 h old and returned rows for **2 of 200** queries. All 200 were
    attempted and 198 legitimately came back empty. No denominator built from
    the shape of the walk can see that, so no such denominator makes the guard
    satisfiable.

    What IS invariant: **a query that was populated yesterday and is still being
    attempted today should still return rows.** So the arm compares only the
    carry-over set — `prev_written ∩ today_attempted`:

    * a retired phase's boards leave the ATTEMPTED set, so they leave the
      denominator, and a phase transition is invisible to this arm (correct: it
      is not a shape break);
    * a new phase's empty boards were never in `prev_written`, so they never
      enter the numerator (correct: an unparsed raid is not a shape break);
    * a payload-shape change leaves the same queries being attempted and stops
      them returning rows — the carry-over yield goes to zero and it FIRES.

    When the carry-over set is empty (exactly what a phase transition produces)
    the arm **cannot run, and says so** rather than passing silently — the `3b`
    lesson from the extract wrapper that printed "OK - game is closed" without
    having checked. It self-clears the following day.

    Rates are still right for anything the run count DOES drive, and `phases`
    writes one record per run (the owner may log on twice in a day), so the run
    normalisation stays where it belongs.
    """
    def counts(m):
        out = {}
        for f in (m or {}).get("files", []):
            out[f["file"].split(".")[0]] = out.get(f["file"].split(".")[0], 0) + f["records"]
        return out

    now, before = counts(manifest), counts(prev)
    failures, notes = [], []

    # --- arm 1: the absolute floor. UNCHANGED, deliberately. ----------------
    # This is the arm that catches "200 response, changed shape, zero records",
    # and it needs no denominator at all. The work order says keep it as-is.
    for w in CANARY_WRITERS:
        if now.get(w, 0) == 0:
            failures.append(
                f"{w}: 0 records written. This writer cannot legitimately be "
                f"empty — the server always has an active phase and populated "
                f"leaderboards. A 200 response with a changed payload shape "
                f"looks exactly like this.")

    if not prev:
        return failures, notes

    # --- arm 2: leaderboard CARRY-OVER, not volume ---------------------------
    if date_dir is None or prev_dir is None:
        notes.append(
            "leaderboards: carry-over NOT CHECKED — the capture folders were "
            "not supplied to canary_check(). The zero-floor arm above still "
            "applied.")
    else:
        att_now, written_now = leaderboard_query_keys(date_dir)
        _att_prev, written_prev = leaderboard_query_keys(prev_dir)
        carry = written_prev & att_now
        if not carry:
            # A guard that cannot run must SAY SO. This is the phase-transition
            # case by construction, and it clears itself the next day.
            notes.append(
                f"leaderboards: carry-over NOT CHECKED — none of "
                f"{prev.get('date')}'s {len(written_prev)} populated boards is "
                f"still being queried today ({len(att_now)} queries attempted "
                f"across {manifest.get('active_phase_count')} active phase(s)). "
                f"That is what a completed phase transition looks like, and it "
                f"is NOT evidence of a healthy capture — only an absence of "
                f"comparable evidence. The zero-floor arm above still applied.")
        else:
            kept = carry & written_now
            ratio = len(kept) / len(carry)
            if ratio < CANARY_DROP_RATIO:
                failures.append(
                    f"leaderboards: only {len(kept)} of {len(carry)} boards "
                    f"that were populated on {prev.get('date')} AND are still "
                    f"being queried today returned rows ({100 * ratio:.0f}%, "
                    f"past the {100 * (1 - CANARY_DROP_RATIO):.0f}% threshold). "
                    f"Phase changes are normalised out of this comparison by "
                    f"construction, so this is NOT a content transition — check "
                    f"the endpoint's payload shape before trusting this capture. "
                    f"Missing: {sorted(carry - written_now)[:5]}")
            else:
                notes.append(
                    f"leaderboards: {len(kept)}/{len(carry)} carried-over boards "
                    f"still populated ({100 * ratio:.0f}%); "
                    f"{len(written_now)} written of {len(att_now)} attempted "
                    f"across {manifest.get('active_phase_count')} active "
                    f"phase(s).")

    # --- arm 3: rate-normalised volume for the rest --------------------------
    runs_now = max(1, now.get("phases", 1))
    runs_prev = max(1, before.get("phases", 1))
    for w in CANARY_WRITERS:
        if w in ("phases", "leaderboards"):
            # `phases` IS the run counter — rate-normalising it is circular.
            # `leaderboards` is handled by arm 2 on its own denominator.
            continue
        if not before.get(w):
            continue
        rate_now = now.get(w, 0) / runs_now
        rate_prev = before[w] / runs_prev
        if rate_now < rate_prev * CANARY_DROP_RATIO:
            failures.append(
                f"{w}: {rate_now:.1f} records/run vs {rate_prev:.1f} on "
                f"{prev.get('date')} — a drop of "
                f"{100 * (1 - rate_now / rate_prev):.0f}%, past the "
                f"{100 * (1 - CANARY_DROP_RATIO):.0f}% threshold. Check the "
                f"endpoint's payload shape before trusting this capture.")
    return failures, notes


# --- git -------------------------------------------------------------------

# Scoped so an UNATTENDED job can never sweep up unrelated working-tree changes
# (3d A2). This used to be a bare `git add data/source`, which would auto-commit
# and push a half-edited scouted JSON or a capture folder mid-copy. The baseline
# task already got this right — `tools/scheduling/run_baseline_scheduled.bat:58`
# scopes to one folder — and this mirrors it. These are the only two paths this
# crawler writes: if a writer is ever added outside them, add it here too.
COMMIT_PATHS = ["data/source/crawl", "data/source/changelog"]


def git_commit_push(date_str):
    """Commit this crawler's OWN output paths and push. Returns a status string."""
    def run(*args):
        return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True,
                              text=True, timeout=300)

    run("add", "--", *COMMIT_PATHS)
    # Scope the diff check to the same paths: an unrelated file the OWNER staged
    # by hand before the task fired must not make this look like "we have
    # something to commit", and must not ride along in the commit either — hence
    # the pathspec on `commit` too, which commits only those paths regardless of
    # what else sits in the index.
    diff = run("diff", "--cached", "--stat", "--", *COMMIT_PATHS)
    if not diff.stdout.strip():
        return "nothing new to commit"
    c = run("commit", "-m",
            f"crawl: {date_str} daily capture (ascensionlogs + changelog)\n\n"
            f"Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>",
            "--", *COMMIT_PATHS)
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

    # 3d A1 — the realm constant must match the host we are about to crawl.
    # Free, and it is the only one of the three constants this check can settle
    # locally (the season is not stated by any endpoint; the phase needs the
    # /api/phases response, asserted in crawl_phases()).
    season_config.assert_realm(BASE)

    print(f"=== crawl_ascensionlogs {date_str} (realm={REALM}, season={SEASON}, "
          f"expect_phase={season_config.EXPECTED_PHASE_NAME!r}, "
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

    prev_manifest, prev_dir = previous_manifest(date_dir)  # read BEFORE we write today's

    active_phases = crawl_phases(writers)
    crawl_watchlist(seen_characters, scan_log)
    _boards, boards_attempted = crawl_leaderboards(
        writers, active_phases, seen_characters)
    reports_before = set(scan_log.get("reports", {}))
    new_reports = crawl_reports(writers, scan_log, seen_characters, args.max_reports)
    reverified = 0
    if args.reverify:
        reverified = queue_reverification(scan_log, seen_characters,
                                          limit=args.reverify)
    armory_pulls = crawl_characters(writers, scan_log, seen_characters, args.max_armory)

    new_report_ids = [int(r) for r in set(scan_log.get("reports", {})) - reports_before]
    manifest = write_manifest(date_dir, writers, scan_log, patch_date, new_report_ids,
                              leaderboard_queries_attempted=boards_attempted,
                              active_phase_count=len(active_phases))
    build_tier2_manifest.build_for_dir(date_dir)
    t1 = sum(f["bytes_gz"] for f in manifest["files"] if f["tier"] == 1)
    t2 = sum(f["bytes_gz"] for f in manifest["files"] if f["tier"] == 2)

    # 3d A3 — canary BEFORE the commit. An empty or shape-broken capture must
    # not be committed, must not be pushed, and must not stamp the day as done.
    canary_failures, canary_notes = canary_check(manifest, prev_manifest,
                                                date_dir, prev_dir)
    for _note in canary_notes:
        print(f"  [canary] {_note}")

    total_bytes = sum(f.stat().st_size for f in date_dir.glob("*.jsonl.gz")) if date_dir.exists() else 0
    commit_status = "skipped (--no-push)"
    if canary_failures:
        commit_status = "SKIPPED — canary failed (see below)"
    elif not args.no_push:
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
    if canary_failures:
        print(f"  🛑 CANARY FAILED ({len(canary_failures)}) — this capture is NOT trustworthy:")
        for f in canary_failures:
            print(f"    - {f}")
        print("    Nothing was committed and the day is NOT stamped; the next "
              "run will retry. Files on disk are left in place for inspection.")
    ok = not ERRORS and not canary_failures and "FAILED" not in commit_status
    print(f"  RESULT:           {'OK' if ok else 'COMPLETED WITH ERRORS'}")
    print("=" * 62)
    return 0 if ok else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except season_config.RealmSeasonMismatch as e:
        # 3d A1. Not a crash — a refusal. The clone's declared server state
        # disagrees with the live server, so capturing would mis-stamp records
        # in a way that cannot be repaired after the fact.
        print("\n" + "=" * 62, file=sys.stderr)
        print("🛑 REFUSING TO CAPTURE — realm/season/phase assertion failed",
              file=sys.stderr)
        print("=" * 62, file=sys.stderr)
        print(str(e), file=sys.stderr)
        print("\nEdit season_config.py, then re-run. No day is stamped.",
              file=sys.stderr)
        sys.exit(2)
