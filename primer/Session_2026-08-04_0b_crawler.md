# Session 0b — Crawler + Changelog Fetcher (Phase 0 Task 6)

**Date:** 2026-08-04 · **Session ID:** `0b` · **Status:** ✅ done
**Scope:** Phase 0 Task 6 (crawler, changelog fetcher, Phase 1 baseline), plus the slice of
Task 2 that Task 6 depends on.

---

## What shipped

| File | Purpose |
|---|---|
| `tools/scrapers/crawl_ascensionlogs.py` | Daily crawler — leaderboards, reports, per-ability damage/healing/avoidance/damage-taken, armories |
| `tools/scrapers/fetch_changelog.py` | Changelog snapshot (daily) + full backfill (one-time) |
| `tools/scrapers/baseline_phase1.py` | One-off Phase 1 baseline: leaderboards + top-N full builds |
| `run_crawler.bat` | Double-clickable Windows launcher, runs both daily jobs, prints a summary |
| `tools/scrapers/archive_crawl.py` | Rolls tier-2 bulk older than N days into monthly tarballs |
| `tools/scrapers/compress_existing_crawl.py` | One-off: gzips pre-switch plain `.jsonl` captures |
| `tools/scrapers/README.md` | The storage model and design notes, for whoever touches this next |

Plus `tools/scrapers/compress_existing_crawl.py`, a one-off converter for captures written before
the gzip switch (see below).

Output lands in `data/source/changelog/` (plain JSON) and `data/source/crawl/<date>/` (gzipped
NDJSON). Raw capture only — **no spell-ID resolution at capture time**, per the phase doc.

### 🆕 Deviation: crawl output is gzipped (`.jsonl.gz`)

The phase doc says "Writes NDJSON"; it now writes gzipped NDJSON. Measured on the first real run:
**3 reports produced 116 MB**, and `avoidance` alone crossed the 50 MB rotation boundary (~370 KB per
record — the enemy-side breakdown is fat). A full historical walk would be multiple GB in the working
tree and would fight GitHub's 100 MB per-file limit continuously.

**Honest accounting, because the obvious argument is partly wrong:** git already zlib-compresses
blobs with the same DEFLATE algorithm gzip uses, so this is roughly **neutral for `.git` size** — it
is *not* a 10× repo saving. The real wins are (a) clone / working-tree size, (b) headroom under the
per-file ceiling. ARCHITECTURE §2.12's "committed files are readable by a chat session via
`raw.githubusercontent.com`" concern does **not** bind here: a 50 MB JSONL exceeds any context window
compressed or not. Everything that principle actually protects — docs, seed scripts,
`index/scouted/*.json` — stays plain text.

Read back with `gzip.open(path, "rt", encoding="utf-8")`. The data already captured was converted
in place with a byte-verified round trip rather than re-fetched, to avoid hammering someone else's
API for data already held. **Measured: 130.3 MB → 7.4 MB, 17.6×**, 990 records, 0 malformed.

### 🆕 Storage tiers — committed vs local, and why

Owner-approved this session. The key observation: **volume and irreplaceability are almost perfectly
anti-correlated**, so the split is nearly free.

| | Tier 1 — **committed** | Tier 2 — **gitignored, local** |
|---|---|---|
| Files | `characters`, `leaderboards`, `phases`, `reports`, `scan_log.json`, `manifest.json` | `abilities`, `healing`, `avoidance`, `damage_taken` |
| Measured (3 reports) | **1.4 MB** | **6.0 MB** |
| Re-fetchable? | ❌ point-in-time state — gone once a phase flips or a player regears | ✅ by report id |

**The manifest is what makes this safe.** Every run writes a *committed* `manifest.json` listing
**every** file including the gitignored ones — record count, sha256, bytes, covered report ids. Git
therefore always knows *what was captured* even when it doesn't hold the bytes, so a future session
can distinguish "never captured" from "captured, stored locally" and re-fetch deliberately. That
satisfies §2.12's intent (nothing invisible to a future session) without the gigabytes.

**Recovery path, and it's real, not aspirational:**
`py tools/scrapers/crawl_ascensionlogs.py --recrawl-report <id>` — fetches only that report's tier-2
data, no leaderboard walk, no armory pulls, no frontier advance.

⚠ **The accepted risk, stated plainly:** "reports stay fetchable" is an *assumption* supported by
evidence (reports #2–4 from 24–25 July were still fetchable on 4 August), not a guarantee. If
ascensionlogs prunes history, un-archived tier-2 data is lost. That is exactly why tier 1 stays
committed and why `archive_crawl.py` **defers rather than deletes**.

### 🆕 Armory content-hash dedupe

The crawler previously rewrote a full ~90 KB armory record for every character every run. At 400
characters that is ~37 MB/day of near-identical data. Records are now written **only when the build
actually changes**, hashed over `ci_resolved` + `stats_summary` (excluding `capture`/`captures`,
whose ids and timestamps churn without the build changing). This both collapses the volume and
produces exactly the gear/build timeline `INDEX_GUIDE` describes wanting.

### ❌ Considered and rejected: delete raw after normalising

Proposed during the session, argued against and dropped. Normalisation encodes *today's*
interpretation, and the crosswalk it depends on is still unresolved (Task 5 gates Phase 1). The phase
doc already forbids the adjacent version of this — "do not resolve spell IDs at capture time … so a
crosswalk fix never requires re-crawling." Deleting raw after normalising with crosswalk v1 makes a
v2 correction unrecoverable. Derived databases are the disposable layer here; raw capture is not.

---

## Endpoint findings (Task 2 slice — feed these into `RECON_FINDINGS.md` in 0a)

Verified live 2026-08-04 against `darkmoon.ascensionlogs.gg`.

### ✅ CONFIRMED — `character_spell_healing` exists

`/api/reports/{id}/character_spell_healing?scope=encounter&encounterIds=&format=flat&limit=&participantType=friendlies`

Returns `rows` (per character per spell: `total_healing`, `overhealing`, `effective_healing`,
`total_absorbs`, `casts`, `hits`, `crits`) plus `source_breakdowns` and `target_breakdowns` keyed by
spell id. **This removes the constraint the phase doc anticipated** — healer support is not limited to
an uncalibrated sim. `character_healing` (without `spell`) 404s; the `_spell_` form is the one.

### ✅ RESOLVED — the `role=healer` quirk (open since INDEX_GUIDE v7)

The rankings endpoint's allowed values are, verbatim from its own 400 body:

```
Invalid role parameter. Allowed values: tank, dps, tanks-and-dps, support
```

**`support` is the healer role.** `healer`/`heal`/`hps`/`healing`/`all` all 400. Independently,
`metric=avg_hps` is accepted and returns a different ranking order than `avg_dps`, so healer
leaderboards are reachable via `role=support` and/or `metric=avg_hps`. The crawler walks
`dps`/`tank`/`support`, and additionally pulls `avg_hps` for `support`.

### ✅ CONFIRMED — report discovery is sequential ID probing, and the list endpoint is gated

- `/api/reports?limit=N` → **401 `{"error":"No token provided"}`**. There is no unauthenticated
  report-list endpoint. `/api/reports/recent` and `/latest` 400 with "Report ID must be a positive
  integer" — they're being parsed as `{id}`, not routes.
- A missing report is a clean **404 `{"error":"Report not found"}`** — a usable probe signal.
- So: walk integers upward from the frontier, stop after `TAIL_404_LIMIT` (20) consecutive 404s.
  Trailing 404s are re-probed next run; 404s *below* a later live ID are recorded as permanently
  missing in `scan_log.json`.

### ⚠ Per-ability endpoints AGGREGATE — rows carry no `encounter_id`

Passing multiple `encounterIds` returns one merged row set. Per-encounter granularity therefore
requires one call per encounter. This drives the grind-report handling below.

### 🚨 `phase_number` ≠ the server's "Phase N" label — a real mis-bucketing trap

`/api/phases` returns three records today:

| record id | `phase_number` | `name` | start | active | parent |
|---|---|---|---|---|---|
| 1 | 0 | Phase 0 | 2026-07-24 | false | — |
| 2 | **1** | **Phase 1 - Zul'Gurub** | 2026-07-31 | true | — |
| 3 | **2** | **Phase 1.1** | 2026-08-03 | true | **2** |

The record whose `phase_number` is **2** is named **"Phase 1.1"** and is a *child* of Phase 1
(`progression_parent_phase_id: 2`). It is **not** the Phase 2 content launch expected on 2026-08-08.
Two consequences:

1. **The Aug 8 deadline is unaffected.** Phase 1 is still the current content phase.
2. **Anything keying per-phase gear tiers (ARCHITECTURE §2.10) off `phase_number` will silently
   mis-bucket.** Use `name` + `progression_parent_phase_id` to build the real phase timeline, and
   treat `phase_number` as an opaque record ordinal. Both are captured daily in `phases.jsonl`.

*(An earlier read of this session flagged "Phase 2 is already active" as a contradiction. The full
records resolve it — noted here so the same alarm isn't re-raised next session.)*

### Other

- `/api/phases` `locations` lists ~25 zones per phase — this is the crawler's zone list, no hardcoding.
- Leaderboard `limit=100` is accepted (INDEX_GUIDE v7's "capped at 25" was not reproduced at
  `limit=100`; not investigated further since 100 is sufficient).
- Ability rows carry `character_type: 'player'` and pet attribution under
  `pet_contributions_by_character` / `pet_spell_damage_by_owner` — pets are separable, not silently
  merged.

---

## Changelog: a JSON API, not HTML

The changelog page embeds a real paginated JSON API:

```
https://api.ascension.gg/api/v3/article/changelog?realm_type=1&page=N
```

Laravel pagination, `per_page=100`, **353 pages / 35,238 entries**. Each entry:
`id`, `label`, `category`, `realm_type`, `group_key` (the "Changes made on" date, `YYYY/MM/DD`),
`description` (with `[Darkmoon]` / `[Dawnrise]` / `[Pending Restart]` tags inline), `created_at`,
`updated_at`.

**This supersedes the phase doc's HTML-scraping plan for Task 3** — the parser now has clean JSON
input and never needs to touch markup. Task 3's *parsing* work (realm/status/ability-name extraction)
is unchanged and still belongs to 0a.

**Backfill complete: 353/353 pages, 0 errors, 30.2 MB**, in `data/source/changelog/backfill/`.
Corpus reaches back to **2016/07/23** — a decade of patch history, which is a materially bigger
per-ability change-history capability than the phase doc anticipated.

Daily mode snapshots pages 1–2 into `data/source/changelog/daily/<date>_pageN.json`. Rationale for
snapshotting rather than only backfilling once: `[Pending Restart]` entries change state (and
`description`, via `updated_at`) between fetches, and that transition is unreconstructable later.

`fetch_changelog.py` also writes `data/source/changelog/latest_patch_date.txt`, which the crawler
reads to stamp `patch_date` on every record (§2.5). If that file is missing the stamp is **null and
the run summary says so loudly** — never fabricated. This is why the launcher runs the changelog
fetcher *first*.

---

## Crawler design notes

- **Grind reports.** Report #2 alone has **658 encounters (368 boss attempts)** from an 8-hour
  dungeon session. Per-encounter calls would be ~1,500 requests for one report. Reports exceeding
  `BOSS_SINGLE_LIMIT` (40) boss encounters are instead **grouped by `boss_id`** — one call per boss,
  aggregated across its attempts, scope `boss_group:<boss_id>`. Normal raid reports keep
  per-encounter granularity (`boss_single`). Trash is always one bundled call (`trash_bundle`).
  Per-attempt *ability* granularity is lost for grind logs only; per-fight duration/kill/wipe data
  survives intact in the encounters list, and pooled inference works per boss anyway.
- **Character discovery has two sources**: leaderboards, and player rows inside every per-ability
  response. The second matters — most raiders in a report never appear on a leaderboard.
- **`--max-armory` (default 400)** caps armory pulls per run; the overflow is persisted to
  `scan_log.pending_characters` and drained first on the next run, so nothing is silently dropped.
- **Re-scout window:** a character's armory is re-pulled if older than `RESCOUT_HOURS` (20), so daily
  runs track gear/build drift across the season.
- **Crash-safety:** `scan_log.json` is rewritten after every report and every 10 armory pulls, so
  Ctrl+C or a crash costs at most one report.
- **Rate limiting:** single-threaded, 0.6 s between requests (`--delay`), 3 retries with escalating
  backoff on 429/5xx. Nothing is parallelised.
- **File rotation** at 50 MB per `.jsonl` (GitHub's 100 MB blob cap).
- **Auto-commit + push** of `data/source` at end of run; `--no-push` to skip.

---

## Phase 1 baseline — captured, deadline met

`baseline_phase1.py --top 50` run 2026-08-04: **48 characters** (full gear + build + resolved
stats), 12 leaderboards, 3 phase records, **547 requests, 0 errors**, 0.70 MB in
`data/source/crawl/baseline_phase1/` — all tier 1, committed. 50 were requested; 2 of the top-50
have no armory capture on the site (a 404, not an error).

Spot-checked: 18 gear slots, 30 abilities + 25 talents (matching the documented per-spec slot
budget), `primary_stat`, and a full `stats_summary`.

🎯 **Lead worth following up in 0a/Phase 3:** `stats_summary` contains a **`sourcesByStat`** key. The
primer names crit-source breakdown tooltips as the *gold-standard* method for settling the Path of
Duality question (`build_paladin-hammerdin.md` §4, open item #1) — "free, instant, and unambiguous,"
preferred over differential measurement. If `sourcesByStat` itemises per-source stat contributions,
that test may be runnable against **any scouted character** from already-captured data, with no
in-game work. Not pursued this session; flagged, not assumed.

---

## Open items / carried forward

| Item | Note |
|---|---|
| Report backfill is long | Reports are large; a full historical walk is many hours. Reports **persist** after a phase flip, so this is *not* deadline-bound — let it grind over successive daily runs |
| Leaderboard 25-cap (INDEX_GUIDE v7) | Not reproduced at `limit=100`; not chased further. Re-check if a >100 pull is ever needed |
| Windows Task Scheduler | Deliberately **not** set up — manual-first, per the resolved decision. ~10-min follow-up once a few manual runs prove out |
| `INDEX_GUIDE.md` self-contradiction (Task 2) | **Not fixed this session** — belongs to Task 8, and 0a will have more endpoint verdicts to fold in at the same time |
| `RECON_FINDINGS.md` | Not created — it's 0a's deliverable. This file holds 0b's endpoint verdicts until then |

---

## What the next session needs to know

`0a` (recon Tasks 1–5, 7, 9) is next. It should **start from this file's endpoint section** rather
than re-probing — healing, roles, report discovery, and the changelog API are settled. Task 2's
remaining unknowns are target-count inference, content-type derivation, per-parse character stats,
and date/patch/realm stamping per parse.

Task 5 (the `entry_id ↔ spells.id` crosswalk) still gates Phase 1 and is untouched.
