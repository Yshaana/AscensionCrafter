# PROGRESS

**Claude Code maintains this file. Update it at the end of every session, before writing the handoff.**

This is the pointer that lets a new session start with no memory of the last one. Keep it short —
detail belongs in `Session_*.md` handoffs, not here.

---

## Current position

**Next session: `1x` — the numeric-field DBC extractor. Then `1b`.**

> **Why `1x` and not `1b`:** the a/b/c chunking in `START_HERE_FOR_CODE.md` was written
> before Phase 0 discovered this task, and renumbering would break every existing
> cross-reference — the project's own most expensive failure mode. Letters here have
> never implied order anyway: **`0b` ran before `0a`.** `1x` runs between `1a` and `1b`.

**`1x` scope (owner decision, 2026-08-04): its own session, before `1b`.** Build a
numeric-field extractor over the client DBC. It resolves **788 of the 803 (98%)**
hidden-formula spells the current text-regex resolver cannot crack — 311 carry a
non-zero `EffectBonusCoefficient`, 770 carry usable `EffectBasePoints`/`DieSides`, and
only 15 are genuinely empty (debuff/immunity markers with no magnitude to find).

- 🛑 **Numeric fields ONLY — never the `description` string.** That is the Titanic
  Mutilate trap: the description said 115%, the field said 70%, and the description
  was stale dead text. It has already cost this project one retraction.
- It goes before `1b` because `spell_mechanics` is meant to be the *resolved* truth
  table; populating it while 98% of hidden formulas are unresolved means building it
  twice.
- Cheaper than it was: `spell_dbc_raw` gained 17 numeric columns in `1a`.
- **Settle "do coefficients scale with rank?" in the same session** — no in-game work
  needed any more. `dbc_spell_rank` gives confirmed same-line rank pairs, so compare
  `EffectBonusCoefficient` across ranks of one line, at scale. Phase 0's single-line
  result (identical at R1 and R6; only flats scale) is the hypothesis to test. **This
  is a `PHASE_1` T4 blocker** — T4 says settle it before deciding whether
  `spell_scaling` needs rank keying.

**Then `1b`** — `spell_mechanics` (T4) + relationship graph (T5), the schema core.

**What `1x` and `1b` inherit, and should not re-derive:**

- **One command rebuilds everything: `py cli/rebuild.py`** (13 steps, ~32s from empty).
  Add `--with-dbc` only after a client patch. Database: `data/derived/ascension.db`.
- **`core/` is pure** — no `print()`, no `argparse`, no paths, connection passed in, and
  it may not import `config.py`. `tools/audit/check_core_purity.py` enforces it; run it
  after touching `core/`. **T4's `resolve_spell_mechanics()` goes in
  `core/spells/mechanics.py` and obeys this.**
- **The crosswalk is live.** Never join `entry_id` to `spells.id`; call
  `core.spells.crosswalk.resolve_entry_id()` or `py cli/crosswalk.py --resolve <id>`.
- **Rank resolution is a function**, `core.spells.ranks.rank_for_level()`. T4's third
  resolver rule ("never serve a lower-rank value for a higher-rank query") calls it
  rather than re-deriving it.
- **Fingerprinting is a function**, `core/spells/fingerprint.py`, with **two field
  sets** — see the plan-changes table. T4's fourth rule is already implemented.
- **`networkx` 3.6.1 is installed** (owner decision, 2026-08-04) — T5 uses it as
  ARCHITECTURE specifies rather than hand-rolling graph algorithms. See
  `requirements.txt`.
- **T4's primary key:** measured in `1a` — **0** CA cards reuse a spell_id across rank
  slots and **0** in-pool spell_ids are shared across cards, so `spell_id` already
  identifies a card-rank uniquely in the playable pool. Key as the doc specifies
  anyway (`rank = 0` means rank-independent); just know `rank` is a label there, not a
  disambiguator.
- **Do the carried-over `stats_summary.sourcesByStat` check** — deferred from `0b`
  *and* `0a`. Cheap, and it could settle the Path of Duality question from data already
  on disk.

**✅ SESSION `1a` IS DONE (2026-08-04).** Repo restructured to ARCHITECTURE §4, patch/realm/season
tracking built, ID crosswalk built. Session record:
`primer/Session_2026-08-04_1a_restructure_crosswalk.md`.

**What 1b inherits, and should not re-derive:**

- **One command rebuilds everything: `py cli/rebuild.py`** (13 steps, ~32s from empty). Add
  `--with-dbc` only after a client patch. The database is now `data/derived/ascension.db`.
- **`core/` is pure** — no `print()`, no `argparse`, no paths, connection passed in, and it may not
  import `config.py`. `tools/audit/check_core_purity.py` enforces it; run it after touching `core/`.
  **T4's `resolve_spell_mechanics()` goes in `core/spells/mechanics.py` and obeys this.**
- **The crosswalk is live.** Never join `entry_id` to `spells.id`; call
  `core.spells.crosswalk.resolve_entry_id()` or `py cli/crosswalk.py --resolve <id>`.
- **Rank resolution is a function**, `core.spells.ranks.rank_for_level()`. T4's third resolver rule
  ("never serve a lower-rank value for a higher-rank query") should call it rather than re-derive it.
- **Fingerprinting is a function**, `core/spells/fingerprint.py`, with **two field sets** — see the
  plan-changes table. T4's fourth rule is already implemented; wire to it.

⚠ **Still not a named task, still the highest-value item Phase 0 found:** a **numeric-field DBC
extractor** would resolve **788 of the 803 (98%)** hidden-formula spells the text resolver can't
crack. It belongs in T4's scope or immediately after. **Numeric fields only — never the
`description` string** (the Titanic Mutilate trap). `spell_dbc_raw` now carries 17 more numeric
columns than it did, which makes this cheaper than it was.

### 🔁 Daily capture — now AUTOMATED (2026-08-04)

**Nothing to remember. The daily crawl runs itself at logon**, 5 minutes in, at most once a day.
Task: `AscensionCrafter Daily Crawl`; script:
`tools/scheduling/register_daily_crawler.ps1`; full documentation: **`SCHEDULING.md`**.
Double-clicking `run_crawler.bat` still works and deliberately bypasses the once-a-day guard.

**🛑 `catchup_crawler.bat` is deliberately NOT scheduled and must stay that way.** It is uncapped,
runs for hours against a third-party public API, and automating it risks getting the IP blocked.
Manual action, started before bed, no deadline — reports persist on ascensionlogs after a phase flip.

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
| **0b** | Crawler + changelog fetcher (T6) | ✅ done | `Session_2026-08-04_0b_crawler.md` | Shipped 2026-08-04. Changelog backfilled (353 pages, back to 2016). Baseline captured |
| **0a** | Recon T1–5, 7, 8, 9 | ✅ done | `Session_2026-08-04_0a_recon.md` | **Phase 0 complete.** `RECON_FINDINGS.md` written. Crosswalk resolved; class coverage 13%→58%; rank resolution solved; 2 pipeline bugs fixed |
| **1a** | Restructure, patches/realms/seasons, crosswalk | ✅ done | `Session_2026-08-04_1a_restructure_crosswalk.md` | `core/api/cli` split + purity check; `cli/rebuild.py`; 5 patch tables; `spell_id_crosswalk` (4 ID spaces); class coverage 394→1,794. Crawler scheduling automated in the same session |
| **1x** | Numeric-field DBC extractor (+ settle rank-vs-coefficient) | ⬜ | — | ▶ **NEXT.** Inserted 2026-08-04 by owner decision; not in the original chunking. 788/803 blocked spells. 🛑 numeric fields only |
| 1b | `spell_mechanics` + relationship graph | ⬜ | — | After `1x`. Read `PHASE_1_spell_database.md` T4+T5. Put the resolver in `core/spells/mechanics.py`; reuse `ranks.py`, `fingerprint.py`, `crosswalk.py` rather than re-deriving them |
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
| 2026-08-04 (1a) | 🔬 **REFINED: "697 wrong-rank catalog entries" is a LOWER BOUND. The real figure is 711, and 25 of them are genuinely AMBIGUOUS** | Phase 0's reporter used `max()`, which silently returns the first of a tie. Two real causes of ties: a rank line whose members *all* read "Rank 1" (`Desolation`, 5 members), and a line pulling in an other-realm 11-prefix variant (`Arcane Focus` → 912840 **and** 1212840). Now recorded as `confidence='conflict'` in `spell_id_crosswalk`, never tie-broken. `resolve_entry_id()` returns `level_spell_id=None` plus a candidate list when ambiguous |
| 2026-08-04 (1a) | 🆕 **The fingerprint rule needs TWO field sets, not one** | The strict set (school, cooldown, cast, power type, radius, effects) answers *"are these the same ability?"* — the hard rule's case. It is the **wrong test** for *"are these two ranks of one ability?"*: rank legitimately changes radius, cooldown and `power_type`, and higher ranks **fill effect slots** the lower rank leaves empty (Malice `[6,0,0]`→`[6,0,6]`→`[6,6,6]`). Strict comparison flagged 106 rank "conflicts", almost all ordinary talents. `RANK_FINGERPRINT_FIELDS` = school + effect-structure compatibility leaves **8 rows on 2 cards**, both `Necrosis`, whose school genuinely changes across ranks (0 → 32 Shadow → 1 Physical). That one is real |
| 2026-08-04 (1a) | ⚠ **`owned_cards` must NOT have a foreign key to `spells`** | Turning on the `foreign_keys` pragma rejected **47 of the owner's own 4,465 owned-card rows** (39 distinct spellIds). Not bad data: **all 39 resolve in `CharacterAdvancement.dbc`** and are simply absent from `spell-export.json`. Phase 0 finding #5 (the export goes stale within days) reproduced from his own collection. FK dropped; `build_index.py` reports the count every run |
| 2026-08-04 (1a) | 🆕 **The `entry_id` never-join rule got STRONGER with more data** | Phase 0 saw 1 numeric collision in 1,054 entry_ids. With 1,487 observed there are **4** (`1152`, `36936`, `50029`, `50043`) and **still 0 real matches** — e.g. `1152` is `Path of Healing` in the crawl and `Purify` in the catalog. 1,487/1,487 resolve through CharacterAdvancement; 3,061/3,061 catalog ids are reachable from a CA rank slot |
| 2026-08-04 (1a) | ⚠ **`build_dbc_index.py`'s extract exporter was a hardcoded column list** | It is the **only** way a session without the game client sees `spell_dbc_raw`, so the 17 fingerprint columns added this session were invisible everywhere except this machine. Now `SELECT *`. Any column added to that table and forgotten in the exporter has the same failure mode — silent, and only visible to whoever has the client |
| 2026-08-04 (1a) | ✅ **Daily crawler is AUTOMATED; catchup stays manual** | The manual-first condition from Phase 0 T6 is satisfied. Trigger is **at logon** (owner's stated pattern is "when I turn on the computer"), not a clock time — which also makes missed-run catch-up moot. Once-per-day guard lives in `run_crawler_scheduled.bat`, not the trigger, since logging on twice a day is normal. Registered by a committed script, documented in `SCHEDULING.md`. **`catchup_crawler.bat` is deliberately never scheduled** |
| 2026-08-04 | 🎯 **RESOLVED (was the Phase 1 gate): `entry_id` = CharacterAdvancement ID, and `CharacterAdvancement.dbc` is extractable** | 0 of 1,054 crawled entry_ids equal a catalog `spells.id`; the one numeric collision is two unrelated cards. `entry_id` is rank-independent, `spellId` is rank-specific. The client ships the mapping as a DBC (10,231 rows; slots 5–9 = `SpellRank[5]`). 1,054/1,054 resolve, 660/660 names agree. Corroborated independently by BisBeard, which keys on `entryId` and carries no spellId at all |
| 2026-08-04 | ❌ **RETRACTED: the contiguous rank rule** — replaced by a level gate | 4,791 non-contiguous rank lines vs 1,908 contiguous. Winds of Winter R1 `274121` → R2 `274129`. The rule that *does* hold: highest rank with `SpellLevel <= level`, verified against both captured in-game tooltips. **Primer §5's "check ±1–3" heuristic is unsafe in general** |
| 2026-08-04 | 🚨 **≈50% of the multi-rank catalog carries the wrong rank's magnitudes** | 697 of 1,409 catalog entries in a rank line are stored at a rank a level-60 character doesn't hold, and in all 697 the correct id is absent from the export entirely. Sensitivity-checked: 697–794 across four grouping strictnesses |
| 2026-08-04 | ❌ **RETRACTED: "spell 274132 is absent from the client"** | It is **Winds of Winter Rank 5**. The absence was an artifact of `spell_dbc_raw`'s catalog±3 scoping, which excluded non-contiguous rank siblings. Fixed (+7,639 ids). Settles the long-running 274121-vs-274132 confusion |
| 2026-08-04 | 🆕 **Class resolves from SkillLine NAMES, not ClassMask — coverage 13% → 58%** | Ascension renamed skill lines to class names; ClassMask is 512 ("Hero") on ~10k rows and useless. 1,789/3,061 catalog entries get one deterministic class, agreeing with 382/387 existing rows and 7/7 of primer §4's proof cases. **5 conflicts recorded, not resolved** (§2.3) |
| 2026-08-04 | 🚨 **98% of the 803 blocked hidden-formula spells resolve from NUMERIC fields** | 311 carry a non-zero `EffectBonusCoefficient`, 770 carry usable `EffectBasePoints`/`DieSides`; only 15 are genuinely empty. Highest-value Phase 1 task, and it is not currently a named one. ⚠ Numeric fields only — never the `description` string |
| 2026-08-04 | ❌ **RETRACTED (`INDEX_GUIDE` v3): "the resolver is not incremental"** | It was incremental **and destructive** — two consecutive runs took `spell_scaling`'s `dbc_hidden_formula` rows from 113 to 0, and shrank `spell_dbc_raw`. Both bugs fixed and verified idempotent. Any coverage number published from this pipeline before today was only reproducible from a clean DB |
| 2026-08-04 | 🆕 **The client DBC is the earliest complete card source** | 52/52 cards announced since 2026-07-01 are in `CharacterAdvancement.dbc`; **2/52** are in `spell-export.json`. The export goes stale within days. ⚠ Don't over-read it: CA's 10,231 records include other realms'/modes' entries — BisBeard's S10 set is 3,226 |
| 2026-08-04 | ❌ **Changelog is NOT a new-card discovery source, and NOT a phase-timeline source** | Every announced card is already in the client. Its 93 "phase" mentions are boss-mechanic phases, not content phases — `/api/phases` stays authoritative. It remains valuable for change history, prose magnitudes, and realm/status |
| 2026-08-04 | ⚠ **Target count: no endpoint carries it; per-parse character stats do NOT exist** | `participant_count − player_participant_count` counts every non-player unit (boss encounters median 12), not concurrent targets — must be inferred, never defaulted to 1. Ability rows carry no crit/SP/AP/haste, confirming the anticipated constraint and reinforcing Phase 3 T5's self-snapshot. **But `character_spec` carries the PATH per parse**, which is new and useful |
| 2026-08-04 | 🛑 **Phase 3 T4 re-scoped: don't build a gear optimizer; gear DATA source still open** | BisBeard takes stat weights as a first-class input (`weightString`, `configStatWeights`) and owns items/phase-tagging/BiS. Its item JSON path is phase-tagged but the serving host is unresolved. Alternative: the client's own `Item.dbc` + `ItemStat.dbc` (1,513,931 records, confirmed present, layout unverified) |
| 2026-08-04 | ⛔ **The official builder is Area-52/Elune only — NOT usable as a Darkmoon source** | It embeds a full catalog with explicit SP/AP coefficients, rarity and **essence costs** (Phase 4 acquisition inputs), but `/v2/builder/darkmoon` redirects to the homepage and those realms are max level 70. §2.5 forbids applying it cross-realm |
| 2026-08-04 | 🆕 **Phase 3 T5 delivery model settled: no `ReloadUI()`, flush on quit, Claude Code reads the file off disk** | Owner's design. Data lands at normal logout; next session I read SavedVariables + `Logs\` directly and correlate. Drops the encoded blob **and** the copyable in-game frame (both existed only for chat copy-paste) → addon writes plain readable Lua. ⚠ Corrects a misconception worth keeping straight: SavedVariables is **one file per addon, rewritten wholesale** — "one file per session" is impossible; the equivalent is one file holding a growing list, one entry per session (which is what T5 already specified). `## SavedVariables:` must be added to the `.toc` — it currently declares none, which is why the addon is copy-paste-only today. Accepted tradeoff: a client crash loses that session's captures; `ReloadUI()` stays a known-working escape hatch but is deliberately **not** implemented |
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

**Resolved in session 0a (2026-08-04)** — full evidence in `RECON_FINDINGS.md`:
~~Is scouted `entry_id` the CharacterAdvancement ID?~~ ✅ **yes** ·
~~Can the client dump a CA↔spellId mapping?~~ ✅ **yes, `CharacterAdvancement.dbc`** ·
~~Is the contiguous rank rule real?~~ ❌ **no — rank is level-gated** ·
~~Does any endpoint carry target count?~~ ❌ **no, must be inferred** ·
~~Can content type be derived?~~ ⚠ **partially** ·
~~Are per-parse character stats available?~~ ❌ **no (but Path is)** ·
~~Which ID space do `ascensionlogs.gg` payloads use?~~ ✅ **catalog/client space**

**Also resolved 2026-08-04 (pre-Phase-1 follow-ups, `RECON_FINDINGS.md` §A1–A3):**
~~Is there a playable-pool discriminator in the CA table?~~ ✅ **yes — slot 121 byte 2, now
`dbc_character_advancement.in_current_pool`; 3,129 of 10,231, covers 1,054/1,054 observed** ·
~~Which ID space does the client's `WoWCombatLog.txt` use?~~ ✅ **plain client `Spell.dbc`, 809/809 —
no fifth space** · ~~Do the `gt*` tables match retail?~~ ✅ **yes, unmodified; crit = exactly 14.0 at
level 60, validating both the tables and the row-index decoding**

**Also resolved 2026-08-04 from the two owner-supplied db.ascension.gg pages:**
~~Fel Infused Weapon school (Fire vs Shadowflame)?~~ ✅ **both right — `276076` is a Fire *enchant*
spell that deals no damage; the damage is `276075`, SchoolMask 36 = Shadowflame** ·
~~Holy Supernova AP term?~~ ✅ **three-way (0.159 / 0.157 / 0.161) and immaterial — treat as ~0.16 ± 0.002** ·
🆕 **Do coefficients scale with rank?** — partially answered: within the Holy Supernova line
`EffectBonusCoefficient` is *identical* at R1 and R6; only the flat term scales (60 → 594)

| Question | Blocks | How to settle |
|---|---|---|
| Does `stats_summary.sourcesByStat` itemise per-source stat contributions? | Could settle the Path of Duality question (`build_paladin-hammerdin.md` §4) from already-captured data, for any scouted character, with zero in-game work | Inspect the field in `data/source/crawl/baseline_phase1/characters.jsonl.gz`. Primer §5 calls crit-source breakdowns the gold-standard method. **Carried over from 0b — still not done** |
| What is the current maximum report ID? | Sizes the historical backfill | Emerges from a full crawler run (no list endpoint exists to ask directly) |
| Do damage coefficients scale with rank? | `spell_scaling` schema | Now cheap: `dbc_spell_rank` gives confirmed same-line rank pairs, so compare `EffectBonusCoefficient` across two ranks of one line — no in-game work needed |
| ⚠ **NEW:** the 97-card gap between `in_current_pool` (3,129) and BisBeard's S10 count (3,226) | Exactness of the card-pool scope | Intersect BisBeard's `entryId` list against `in_current_pool=1` and inspect the difference |
| Which of the 5 `class_origin` conflicts is right? | `class_origin` correctness | Proc test or live tooltip per spell. Note Fel Infused Weapon's existing value ("Duality") is a Path, not a class |

| Where is BisBeard's item JSON actually served from? | Phase 3 T4 gear source | Read the base-URL construction in its `itemDatabaseSync` chunk, or ask the author |
| Are `Item.dbc`/`ItemStat.dbc` layouts stable enough to extract? | A gear database with no third-party dependency | Extract a handful of known items, compare against in-game tooltips |

| What do CA slots 14/15/17/21/25/29–41 mean? | Acquisition / prerequisite modelling | Correlate `raw_ints_json` against known card properties — no re-extraction needed |
| ⚠ **NEW:** Fel Infused Weapon per-level term — db renders **4.5**/level, client DBC says **1.5** (exactly 3×) | The card's flat damage component, which the docs currently have in the wrong *shape* too (`ppl` is a per-level rate, not a flat add) | **In-game tooltip read at level 60** — fully resolved there, tier 1, beats both. db was byte-faithful on Holy Supernova, so suspect a rank/variant (`276069` vs `276076`) or a stale snapshot |
