# PROGRESS

**Claude Code maintains this file. Update it at the end of every session, before writing the handoff.**

This is the pointer that lets a new session start with no memory of the last one. Keep it short —
detail belongs in `Session_*.md` handoffs, not here.

---

## Current position

**Next session: `0a` — recon Tasks 1–5, 7, 9.**

`0b` is ✅ done (2026-08-04) — crawler, changelog fetcher, and launcher all shipped and run. See
`primer/Session_2026-08-04_0b_crawler.md`.

**Start `0a` from that handoff's endpoint section rather than re-probing.** Healing
(`character_spell_healing` exists), the role vocabulary (`support` = healer), report discovery
(sequential probing; the list endpoint is auth-gated), and the changelog JSON API are all settled.
Task 2's remaining unknowns are target-count inference, content-type derivation, per-parse character
stats, and per-parse date/patch/realm stamping. **Task 5 still gates Phase 1 and is untouched.**

### 🔁 Standing daily action for the project owner (not a session task)

**Double-click `run_crawler.bat` once a day.** Changelog snapshot + a crawl capped at 25 new
reports, then auto-commit and push. Bounded to ~30–60 min worst case. Manual-first by design — no
scheduler until a few runs prove out.

**Separately, `catchup_crawler.bat`** is the uncapped historical backfill — run it when the machine
can stay on for hours (overnight). Grind reports take ~10 min each, so a full backfill is long.
Ctrl+C is safe in both: `scan_log.json` is saved after every report and the next run resumes.
Not urgent — reports persist on the site, so the backfill has no deadline.

### ✅ Phase 1 baseline — CAPTURED 2026-08-04, deadline met

48 characters (full gear + build + resolved stats), 12 leaderboards, 3 phase records, 0 errors, in
`data/source/crawl/baseline_phase1/` (0.70 MB, all tier 1, committed). 50 were requested; 2 of the
top-50 have no armory capture on the site (404 — not an error).

**Correction to the earlier framing of this deadline:** reports *persist* after a phase flip, so
historical parse data is **not** lost on the 8th and the report backfill is not deadline-bound. What
was genuinely unrecoverable is the **leaderboard standings and character armory snapshots as they
stand during Phase 1** — and that is now captured. Nothing else in Phase 0 is deadline-bound.

Optionally re-run closer to the 8th for a tighter "before" edge; the folder is overwritten in place.

---

## Session log

| Session | Scope | Status | Handoff | Notes |
|---|---|---|---|---|
| **0b** | Crawler + changelog fetcher (T6) | ✅ done | `Session_2026-08-04_0b_crawler.md` | Shipped 2026-08-04. Changelog backfilled (353 pages, back to 2016). Baseline script ready, **run before Aug 8** |
| **0a** | Recon T1–5, 7, 9 | ⬜ not started | — | ▶ **NEXT.** Start from 0b's endpoint findings, don't re-probe |
| 1a | Restructure, patches/realms/seasons, crosswalk | ⬜ | — | Gated on 0a Task 5 |
| 1b | `spell_mechanics` + relationship graph | ⬜ | — | |
| 1c | Facts, `spell_profile()`, auto-debugger, browsing, volatility | ⬜ | — | |
| 2a | Combat engine, content profiles, ability model, build spec | ⬜ | — | |
| 2b | Three sim tiers + uncertainty | ⬜ | — | |
| 2c | Weights, calibration, prediction ledger, cache, CLI | ⬜ | — | |
| 3a | Crawl normalisation, inference, search, gear | ⬜ | — | Gear scope gated on 0a Task 9 |
| 3b | Addon, logs, automation, crawler refinement | ⬜ | — | |
| 4 | Legos + Theorycrafter | ⬜ | — | Chunk as it goes |

Status values: ⬜ not started · 🟡 in progress · ✅ done · ⏸️ blocked

---

## Blocked on the user

Anything waiting on a 🛑 stop-point or a decision only the project owner can make. Clear entries as
they're answered.

| Item | Blocking | Asked on |
|---|---|---|
| *(nothing currently open)* | — | — |

**🎉 Both long-standing 3b blockers were resolved on 2026-08-04 — Phase 3 is no longer gated on the
owner for anything.**

**✅ `ReloadUI()` works** — confirmed in-game by the owner. Not sandboxed, so an addon can force a
SavedVariables flush on demand instead of waiting for logout. Makes mid-session self-snapshot capture
practical and removes the main design risk in Phase 3 T5. Seeded as
`confirmed_facts.client_reloadui_available`. Still unestablished (and not needed for the intended
out-of-combat flow): whether it's callable *in combat*.

**✅ Combat log naming, location — and the correlation rule** — owner supplied the path; verified
against 3 real logs. `<launcher>\resources\ascension-live\Logs`, filename
`YYYY-MM-DD-HH.MM.SS WoWCombatLog.txt`. **Not** retail's pattern, exactly as T6 feared — a
retail-derived glob matches nothing. Bonus: correlation is solved too. Filename timestamp = window
**start**, file mtime = window **end**, both verified exact to the second against the first/last
in-file events, so a log is placeable in time without opening it. Seeded as
`confirmed_facts.combat_log_naming_and_correlation`; full detail and three traps in `PHASE_3` T6.
⚠ Chief traps: in-file timestamps carry **no year** (filename is the only source), and everything is
**local** time while the crawler stamps **UTC**.

**Note:** `SEASON = 10` is also hardcoded in the crawler. It must be bumped when S11 starts — the
API exposes phases, not seasons, so this can't be derived. Not blocking; flagged so it isn't missed.

**Resolved:** crawler scheduling → **manual-first on Windows** (2026-08-04). No scheduler set up
initially; Windows Task Scheduler added later once the crawler is proven. `0b` is no longer blocked.

**Resolved 2026-08-04 (owner decisions, session 0b) — do not re-litigate these:**

| Question | Decision |
|---|---|
| Tier-2 bulk data is local-only on one disk — acceptable? | **Yes, accepted.** Re-fetchable by report id while ascensionlogs retains history, and the committed manifest records what existed. No off-machine sync |
| Capture Dawnrise as well as Darkmoon? | **Darkmoon only.** `REALM` stays hardcoded. Cross-realm facts are unsafe to mix anyway |
| Watchlist for own characters? | **Yes — implemented.** `tools/scrapers/watchlist.txt`, seeded with **Elric** (resolves to character_id 39772). Watched characters are captured every run with priority over `--max-armory` |
| Contact db.ascension.gg's operator / BisBeard's author? | **No outreach for now.** Stay inside robots.txt (targeted manual lookups only) and inspect BisBeard read-only in 0a Task 9 |

⚠ **`SEASON = 10` is hardcoded** in the crawler and cannot be derived (the API exposes phases, not
seasons). Bump it when S11 starts, or every record will be mis-stamped.

---

## Plan changes

When recon or implementation contradicts a phase doc, record it here **and** amend the doc itself.

| Date | What changed | Why |
|---|---|---|
| 2026-08-04 | 🆕 **Phase 3 T5 addon must self-snapshot FIRST, at the top of every capture list** | Owner is in the logs he collects, so it's near-free. Closes Phase 0 T2's flagged *per-parse character stats* risk for at least one character (exact, not approximated from nearest capture); satisfies §2.2's tier-1 "capture stats alongside" rule automatically; is the **only** source of *measured* gear-scaling curves for §2.10; makes him Phase 2's calibration anchor. **Deferred deliberately** — no interim script, do it properly in Phase 3. Full reasoning in `PHASE_3_builds_repo.md` T5 — don't re-derive it, and don't drop it |
| 2026-08-04 | 🆕 **Two-tier crawl storage: tier 1 committed, tier 2 gitignored + local** | Volume and irreplaceability are anti-correlated. Armory/leaderboard state (1.4 MB) can never be re-fetched; per-ability bulk (6.0 MB) is re-fetchable by report id. A **committed `manifest.json`** lists every file incl. gitignored ones (records, sha256, report ids), so git knows what exists without holding it. Recovery: `--recrawl-report <id>`. Risk accepted: "reports stay fetchable" is evidenced, not guaranteed |
| 2026-08-04 | 🆕 **Armory records deduped by content hash** | Was rewriting ~90 KB per character per run (~37 MB/day at 400 chars). Now written only on change, hashed over `ci_resolved`+`stats_summary`. Also yields the gear/build timeline INDEX_GUIDE wants |
| 2026-08-04 | ❌ **REJECTED: delete raw data after normalising** | Normalisation encodes today's interpretation and the crosswalk is still unresolved (T5 gates Phase 1). Phase 0 T6 already forbids the adjacent version ("resolve at rebuild, so a crosswalk fix never requires re-crawling"). Derived DBs are the disposable layer; raw capture is not |
| 2026-08-04 | 🆕 **Crawl output gzipped (`.jsonl.gz`)**, amending Phase 0 T6's "Writes NDJSON" | 3 reports = 116 MB uncompressed; `avoidance` alone crossed the 50 MB rotation cap. Multiple GB working tree + GitHub's 100 MB per-file limit. Note: git already zlib-compresses, so `.git` size is ~neutral — the win is clone size and per-file headroom. §2.12 unaffected: docs/seeds/`index/scouted/*.json` stay plain text |
| 2026-08-04 | 🚨 **`phase_number` ≠ the server's "Phase N" label** | `/api/phases` record with `phase_number=2` is *named* "Phase 1.1" and is a child of Phase 1 (`progression_parent_phase_id`), not the Aug 8 Phase 2 launch. Build phase timelines from `name` + parent id; §2.10's gear tiers would mis-bucket off `phase_number` |
| 2026-08-04 | ⚠ **Aug 8 deadline re-scoped: baseline, not backfill** | Reports persist after a phase flip, so historical parses aren't lost. Only leaderboard standings + armory snapshots are unrecoverable → `baseline_phase1.py` is the deadline item; the report walk can grind |
| 2026-08-04 | ✅ **Changelog is a JSON API, not HTML** (`api.ascension.gg/api/v3/article/changelog`) | 353 pages / 35,238 entries with stable ids, `group_key` dates, `updated_at`. Task 3's parser never needs to touch markup. Backfill done; corpus reaches back to 2016/07/23 |
| 2026-08-04 | ✅ **`character_spell_healing` exists** | Healer support is NOT limited to an uncalibrated sim, contrary to Phase 0 Task 2's anticipated constraint |
| 2026-08-04 | ✅ **`role=healer` quirk resolved: the value is `support`** | Endpoint's own 400 body: `Allowed values: tank, dps, tanks-and-dps, support`. Open since INDEX_GUIDE v7 |
| 2026-08-04 | ⚠ **Report list endpoint is auth-gated (401)** | Discovery is sequential ID probing with a 404 "not found" signal, not a list walk |
| 2026-08-04 | ⚠ **Per-ability endpoints aggregate over `encounterIds`** | Rows carry no `encounter_id`, so per-encounter granularity costs one call each. Drove the grind-report `boss_id` grouping compromise |
| 2026-08-04 | Lego definition corrected: coupling-based, not "not a school" | A mostly-Frost cross-class cluster (Frost Mage ability + Frost Shaman feeder + Frost-damage talents) is a valid lego. Shared school is common evidence of coupling, not a disqualifier |
| 2026-08-04 | New `amplifies_school` relation type; graph is partly build-dependent | "Increases Frost damage" boosts unnamed abilities. Without a school-scoped edge that resolves against a build, school-amplifier legos are invisible to graph discovery. Enters at lower confidence per §5 |
| 2026-08-04 | ❌ **RETRACTED: "coefficients scale with rank"** and the `spell_scaling` re-key that depended on it | Derived by comparing `81193` to `270182` — two *different* abilities sharing the name "Holy Supernova" (radius 10 vs 15, cooldown 50 vs 40, instant vs 2s cast). Still plausible, now an open question |
| 2026-08-04 | ❌ **RETRACTED: "db.ascension.gg is a fifth ID space"** | `270182` resolves there normally. The db uses catalog-compatible IDs; `81193` is just another spell |
| 2026-08-04 | 🛑 **NEW HARD RULE: fingerprint before relating two IDs** | Same-name/different-ID was wrongly assumed to mean "related" **twice in one session** (`1111294` prefix, then `81193`). Compare radius/cooldown/cast/cost/effects first |
| 2026-08-04 | 🆕 In-game tooltips are **haste-adjusted** | Holy Supernova 2.00s base → 1.61s displayed ≈ 24% haste. A tooltip measures the character, not the spell — capture stats alongside every tooltip read |
| 2026-08-04 | ✅ **CONFIRMED: db.ascension.gg carries damage coefficients** on catalog-compatible IDs | `270182` → SP 24.15%, AP 15.70%, explicit Scaling fields, server-rendered. Best per-build source; rate-limited to ~2–3 automated requests |
| 2026-08-04 | ⚠ Contiguous rank rule downgraded to provisional | `270182`→`270187` is one pair; `270183`–`270186` unchecked. Must pass the fingerprint test |
| 2026-08-04 | ❌ **RETRACTED: "11 prefix / Wildcard variant" ID space.** No `wildcard_variant` crosswalk | Four in-game tooltips show plain IDs (1459, 10157, 136, 270187). `1111294` belongs to another realm, not Wildcard |
| 2026-08-04 | ✅ Catalog IDs = in-game IDs = db IDs, confirmed | 1459, 136, 270182 identical across all three. Task 4a class resolution stands |
| 2026-08-04 | 🚨 **Catalog stores Rank 1; owner plays max rank** | Arcane Intellect R1 = +2/+2, R5 = +31/+27 (~15×). Resolver must refuse rank fallback. `(spell_id, rank)` keying confirmed necessary |
| 2026-08-04 | 🆕 Fourth ID space: `CharacterAdvancement ID` (~40000) | Likely equals scouted `entry_id` (Shadow Bolt entry_id 40050 vs spellId 686). Would answer the v4 open question as "different spaces, never join" |
| 2026-08-04 | ⚠️ Ascension edits spells in place | Its Arcane Intellect grants spell power; retail's does not, same ID 1459. Class inherits from a WotLK ID; mechanics never do |
| 2026-08-04 | `db.ascension.gg` downgraded to "targeted manual lookups only" | robots.txt disallows automated access after ~2–3 requests |
| 2026-08-04 | New Phase 0 Task 4a — `SkillLineAbility.dbc` | 1,224/3,061 catalog entries (40%) are real WotLK IDs → deterministic class resolution, vs 392 (13%) today |
| 2026-08-04 | Server phase corrected to Phase 1 (Zul'Gurub); Phase 2 on 2026-08-08 | BisBeard's page metadata said "Phase 0" and was stale |

---

## Open questions raised during planning

Seed these into `open_questions` (Phase 1 Task 6) rather than losing them here.

| Question | Blocks | How to settle |
|---|---|---|
| Does `stats_summary.sourcesByStat` itemise per-source stat contributions? | Could settle the Path of Duality question (`build_paladin-hammerdin.md` §4) from already-captured data, for any scouted character, with zero in-game work | Inspect the field in `data/source/crawl/baseline_phase1/characters.jsonl.gz`. Primer §5 calls crit-source breakdowns the gold-standard method |
| What is the current maximum report ID? | Sizes the historical backfill | Emerges from the first full crawler run (no list endpoint exists to ask directly) |
| Does any endpoint carry **target count**? | The whole scenario model (§2.9) | 0a Task 2. **Never silently default to 1** |
| Can content type (`raid`/`dungeon_*`/`world_boss`) be derived from zone/difficulty/bracket? | §2.9 content profiles derived from real data | 0a Task 2 |
| Are per-parse **character stats** available, or only the current armory snapshot? | Phase 3 pooled inference regresses crit% against per-character crit | 0a Task 2 |
| Do damage coefficients scale with rank? | `spell_scaling` schema | Read one ability's in-game tooltip at two confirmed ranks of the **same** line; compare SP/AP terms |
| Is scouted `entry_id` the CharacterAdvancement ID? | Crosswalk, all "who runs X" queries | Collect ~10 CA IDs in-game, check against committed scouted JSON |
| Can the client dump a CA↔spellId mapping? | Crosswalk (if above confirms) | Addon API, debug command, or export |
| Which ID space do combat logs use? | Canonical ID choice project-wide | Inspect `ascensionlogs.gg` per-ability damage payloads |
| Is the contiguous rank rule real? | Rank resolution for Ascension originals | Fingerprint `270183`–`270186` against `270182` |
| Holy Supernova AP term: catalog `0.159` vs db `15.70%` | Coefficient accuracy | Live tooltip read |
| Fel Infused Weapon school: db says Fire, docs say Shadowflame | Ability classification | Live tooltip read |
