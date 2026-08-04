# tools/scrapers — daily capture

Built in session 0b (Phase 0 Task 6). Raw capture only: **no spell-ID resolution, no
normalisation, no analysis.** Those belong to Phase 3, and keeping capture free of them is
deliberate — resolving at capture time bakes today's interpretation into data that cannot be
re-collected. (The crosswalk has since been *resolved* and built — `spell_id_crosswalk`, Phase 1
T3 — but it is applied at rebuild time, never at capture time. That separation is the point.)

---

## Daily routine

**Nothing to do — it runs itself.** Since 2026-08-04 the daily capture is a scheduled task
(`AscensionCrafter Daily Crawl`) that fires **at logon**, 5 minutes in, at most once a day.
See **`SCHEDULING.md`** in the repo root for how to change, disable or force it.

It runs, in order:

1. `fetch_changelog.py` — changelog snapshot (also refreshes the patch-date stamp)
2. `crawl_ascensionlogs.py --max-reports 25` — the crawl, then auto-commits and pushes

**Double-clicking `run_crawler.bat` still works** and deliberately ignores the once-a-day guard —
a manual run is an explicit act. The scheduled path uses
`tools/scheduling/run_crawler_scheduled.bat` instead, which has no `pause` (Task Scheduler has
nobody to press a key) and carries the guard.

### Two launchers, on purpose

| Launcher | Cap | When |
|---|---|---|
| `run_crawler.bat` | 25 new reports | **Daily.** Bounded and predictable, ~30–60 min worst case |
| `catchup_crawler.bat` | uncapped | The historical backfill. Run when the machine can stay on for hours — overnight is ideal. 🛑 **Never schedule this one** — see below |

🛑 **Only the capped daily run is scheduled. Do not automate `catchup_crawler.bat`** — an unbounded
unattended job hammering a third-party public API is exactly what this crawler's sequential,
rate-limited design exists to avoid, and the likeliest outcome of getting it wrong is the IP being
blocked. It stays a deliberate manual action. There is no deadline on it: reports persist on
ascensionlogs after a phase flips.

The cap exists because grind reports take ~10 minutes each (report #2 has 658 encounters), so an
uncapped run can take many hours. That is fine for a deliberate backfill and wrong for a daily
double-click.

**Ctrl+C is safe in both.** `scan_log.json` is written after every report, so the next run resumes
from where the last one stopped — nothing re-fetched, nothing lost.

⚠ Both launchers **push to GitHub** at the end. Use `--no-push` if you want to inspect first.

---

## Scripts

| Script | What it does |
|---|---|
| `crawl_ascensionlogs.py` | Leaderboards, reports, per-ability damage/healing/avoidance/damage-taken, armories |
| `fetch_changelog.py` | Changelog snapshot; `--backfill` pulls all ~353 pages once |
| `baseline_phase1.py` | One-off Phase 1 baseline — leaderboards + top-N full builds |
| `archive_crawl.py` | Rolls old tier-2 bulk into monthly tarballs |
| `compress_existing_crawl.py` | One-off: gzips pre-2026-08-04 plain `.jsonl` captures |

Useful flags:

```bash
py tools/scrapers/crawl_ascensionlogs.py --max-reports 25   # watchable short run
py tools/scrapers/crawl_ascensionlogs.py --no-push          # don't commit
py tools/scrapers/crawl_ascensionlogs.py --recrawl-report 74 --recrawl-report 75
py tools/scrapers/archive_crawl.py --older-than 30 --dry-run
py tools/scrapers/archive_crawl.py --verify
```

---

## Storage model — two tiers

The volume problem and the irreplaceability problem are almost perfectly **anti-correlated**,
and the storage model exploits that.

| | Tier 1 — **committed** | Tier 2 — **local only, gitignored** |
|---|---|---|
| Files | `characters`, `leaderboards`, `phases`, `reports`, `scan_log.json`, `manifest.json` | `abilities`, `healing`, `avoidance`, `damage_taken` |
| Share of bytes | ~20% (and far less once armory dedupe kicks in) | ~80% |
| Re-fetchable? | ❌ **No** — point-in-time state | ✅ Yes, by report id |
| Why | Armory snapshots and leaderboard standings are gone the moment a phase flips or a player regears | Derived from reports, which persist on ascensionlogs.gg |

Measured on the first real run: 3 reports → 130 MB raw → **7.4 MB gzipped** (17.6×) → of which
only **1.4 MB is tier 1**.

### The manifest is what makes this safe

Every run writes a **committed** `manifest.json` per date listing *every* file — including the
gitignored ones — with record count, sha256, byte size, and the report ids covered.

So git always knows **what was captured**, even when it doesn't hold the bytes. A future session
can tell the difference between "never captured" and "captured, stored locally", and can verify
or deliberately re-fetch. That is ARCHITECTURE §2.12's intent (nothing invisible to a future
session) without the gigabytes.

### Recovery path

```bash
py tools/scrapers/crawl_ascensionlogs.py --recrawl-report <id>
```

Fetches only that report's tier-2 data. No leaderboard walk, no armory pulls, no frontier
advance.

⚠ **The risk you are accepting:** "reports stay fetchable" is an assumption supported by
evidence (reports #2–4 from 24–25 July were still fetchable on 4 August), **not a guarantee**.
If ascensionlogs ever prunes history, un-archived tier-2 data is lost. That is precisely why
tier 1 stays committed and why archiving *defers* rather than deletes.

### Archiving

`archive_crawl.py --older-than 30` consolidates tier-2 files older than 30 days into
`data/archive/crawl_<YYYY-MM>.tar`, verifying each member's sha256 before removing the original.
Tier-1 files, manifests and `scan_log.json` are **never** touched. Run it monthly-ish; nothing
breaks if you forget.

---

## Why gzip

Measured: 3 reports = 130 MB uncompressed, and `avoidance` alone crossed the 50 MB rotation
boundary.

**Honest accounting:** git already zlib-compresses blobs with the same DEFLATE algorithm gzip
uses, so this is roughly *neutral* for `.git` size — it is **not** a 17× repo saving. The real
wins are clone/working-tree size and headroom under GitHub's 100 MB per-file limit.

Read any capture file with:

```python
import gzip, json
with gzip.open(path, "rt", encoding="utf-8") as f:
    for line in f:
        rec = json.loads(line)
```

Files are appended per-record, producing a multi-member gzip stream. That is valid and read
transparently — and it keeps the property that a Ctrl+C costs at most the record in flight.

---

## Design notes worth knowing before changing anything

- **Report discovery is sequential ID probing.** `/api/reports?limit=N` returns **401** — there
  is no unauthenticated list endpoint. A missing report is a clean 404. The crawler walks upward
  from a stored frontier and stops after 20 consecutive 404s. Trailing 404s are re-probed next
  run; 404s *below* a later live id are recorded as permanently missing.
- **Request-level failures are queued, not skipped.** They go to `scan_log.retry_reports` and are
  retried first on the next run, so a transient error never silently loses a report.
- **Per-ability endpoints aggregate over `encounterIds`** — returned rows carry no
  `encounter_id`. Per-encounter granularity therefore costs one call each.
- **Grind reports are grouped by `boss_id`.** Report #2 alone has 658 encounters / 368 boss
  attempts; per-encounter calls would be ~1,500 requests for one report. Over 40 boss encounters
  → one call per boss (scope `boss_group:<id>`). Per-attempt *ability* granularity is lost for
  grind logs only; per-fight duration/kill/wipe data survives in the encounters list.
- **Armory records are content-hash deduped** over `ci_resolved` + `stats_summary`, so unchanged
  builds aren't rewritten daily. `capture`/`captures` are excluded from the hash — they carry ids
  and timestamps that churn without the build changing.
- **`watchlist.txt` characters are always captured**, with priority over `--max-armory`. Leaderboard
  and report discovery only finds characters who parsed that day, so without this a personal
  character goes uncaptured on any day it doesn't raid — leaving holes in the gear/build timeline
  the build docs depend on. Names are resolved once and cached in `scan_log.watchlist_ids`; a name
  that doesn't resolve is reported loudly, never silently dropped. Currently: **Elric** (39772).
- **Realm is Darkmoon-only and season is hardcoded to 10** (owner decision, 2026-08-04). Dawnrise is
  deliberately not captured. ⚠ `SEASON` cannot be derived from the API — bump it when S11 starts or
  every record is mis-stamped.
- **Roles are `dps` / `tank` / `support`.** `support` is the healer role — the endpoint's own 400
  body enumerates the allowed values. `healer` is rejected.
- **Every record is stamped** with `captured_at`, `realm`, `season`, `patch_date`. `patch_date`
  comes from `data/source/changelog/latest_patch_date.txt`, which is why the launcher runs the
  changelog fetcher first. If it's missing the stamp is `null` and the summary says so — never
  fabricated.
- **⚠ `phase_number` ≠ the server's "Phase N" label.** `/api/phases` record `phase_number=2` is
  named "Phase 1.1" and is a child of Phase 1. Build phase timelines from `name` +
  `progression_parent_phase_id`.
- **Rate limiting:** single-threaded, 0.6 s between requests, 3 retries with escalating backoff
  on 429/5xx. Nothing is parallelised. Running unattended against someone else's public API —
  "don't get flagged" is a hard constraint.
