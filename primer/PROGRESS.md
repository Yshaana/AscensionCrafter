# PROGRESS

**Claude Code maintains this file. Update it at the end of every session, before writing the handoff.**

This is the pointer that lets a new session start with no memory of the last one. Keep it short —
detail belongs in `Session_*.md` handoffs, not here.

---

## Current position

**Next session: `1c` — facts/questions (T6), `spell_profile()` (T7), auto-debugger +
test protocols (T8), browsing (T9), volatility (T10).**

**✅ SESSION `1b` IS DONE (2026-08-05).** T4 (`spell_mechanics`) and T5
(`spell_relationships` + graph) built, validated, idempotent. Session record:
`primer/Session_2026-08-05_1b_mechanics_relationships.md`.

**What `1c` inherits from `1b`:**

- **`py cli/rebuild.py` is now 16 steps** (~75s): `cli/relationships.py` (T5) then
  `cli/mechanics.py` (T4) run last, in that order — the trigger-attributed
  `spell_effect_values` rows T5 writes are inputs to T4's resolver. The piped-output
  `UnicodeEncodeError` crash is FIXED (env `PYTHONIOENCODING=utf-8` in `run_step`).
- **`spell_mechanics` is live: 3,747 rows** (3,061 catalog + 686 unambiguous level-60
  rank siblings), per-field provenance/uncertainty JSON, 29 conflict rows (mostly
  multi-effect-slot collisions, surfaced not resolved), **710 rows carrying an explicit
  rank gap** — `resolve_spell_mechanics()` names the level-60 id instead of silently
  serving Rank-1 magnitudes. 25 ambiguous rank lines contribute no sibling, per §2.3.
- **`spell_relationships` is live: 5,302 edges** (4,670 triggers, 388 borrows_modifiers,
  218 amplifies, 17 shares_exclusivity_bucket, 9 amplifies_school). Graph queries in
  `core/spells/graph.py` (networkx): `neighbourhood` / `find_clusters` / `path_between` /
  `gating_requirements`, all taking optional `build_spec` for `amplifies_school`
  expansion (hybrid schools double-dip: a Fire amplifier reaches a Shadowflame ability).
- **Bounded trigger attribution ran** (owner decision 2026-08-05: depth ≤ 2, cycle-safe,
  single-path, out-of-catalog targets only, `via='trigger_hopN'`, `confidence='inferred'`):
  **724 magnitude rows across 444 cards**; 26 ambiguous targets skipped. **Hammer from
  the Heavens reproduces 122–145 end-to-end** — it is a rebuild-time validation now.
- **`spell_scaling` is rank-keyed** (+`rank` label column; 229 level-60 sibling
  coefficient rows at `source='dbc_rank_sibling_text'`, covering the 7 known-different
  lines — Sun Down SP 1.3 is a rebuild-time validation). ⚠ **Its FK to `spells` was
  dropped** (sibling ids are absent from the export by definition; `owned_cards` precedent).
- **`spells.crit_table`/`hit_table`/`rolls_hit_check`/`proc_icd_seconds` no longer exist**
  — doc-confirmed combat-table facts live in the `doc_confirmed_mechanics` staging table
  (reworked `seed_spell_flags.py`) and surface only in `spell_mechanics`. Anything still
  querying the old `spells` columns must switch.
- **243 `talent_amplifiers` rows remain 'needs manual review' and contribute NO edges** —
  a standing human-review queue T6/T8 should surface rather than let rot.
- **The compound-form extraction gap is still open** (`($SP+$AP)*x`, `$SPFR*x`) — was not
  in `1b`'s brief; do it in `1c` or log it as a T8 coverage-sweep item.
- T4/T5 deviations from the phase doc are recorded in `PHASE_1_spell_database.md`'s
  progress block (FK drop, migrate-and-demote, single-member bucket, attribution bounds).

**✅ SESSION `1x` IS DONE (2026-08-04).** 794 of 887 blocked hidden-formula spells
resolved from numeric DBC fields; the rank question settled. Session record:
`primer/Session_2026-08-04_1x_numeric_extractor.md`. Its two corrections
(`EffectBonusCoefficient` is not the SP/AP coefficient; coefficients DO scale with
rank) are now **enforced in code** — `1b` built T4/T5 on them, and both are
rebuild-time validations. The `sourcesByStat` check it also carried was closed in `1x`
itself (premise wrong — the block is gear-only).

**✅ SESSION `1a` IS DONE (2026-08-04).** Repo restructured to ARCHITECTURE §4, patch/realm/season
tracking built, ID crosswalk built. Session record:
`primer/Session_2026-08-04_1a_restructure_crosswalk.md`.

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
| **1x** | Numeric-field DBC extractor (+ settle rank-vs-coefficient) | ✅ done | `Session_2026-08-04_1x_numeric_extractor.md` | 794/887 blocked spells resolved; `spell_effect_values` + `dbc_numeric.py` + `rank_scaling.py`. **Two Phase 0 claims corrected** — `EffectBonusCoefficient` is not the SP/AP coefficient, and coefficients DO scale with rank |
| **1b** | `spell_mechanics` (T4) + relationship graph (T5) | ✅ done | `Session_2026-08-05_1b_mechanics_relationships.md` | 3,747 mechanics rows, 5,302 edges, bounded trigger attribution (724 rows / 444 cards, HftH 122–145 reproduces end-to-end), `spell_scaling` rank-keyed (+229 sibling rows), `spells` combat-table columns → `doc_confirmed_mechanics`. Rebuild is 16 steps; piped-output crash fixed. Two stale `confirmed_facts` rows qualified SUPERSEDED (pre-`1b` prep item) |
| 1c | Facts, `spell_profile()`, auto-debugger, browsing, volatility | ⬜ | — | ▶ **NEXT.** T6–T10; also: compound-form extraction gap, the 243 manual-review amplifier rows, and T8 bucketing multi-effect-slot "conflicts" separately from cross-source ones. **Owner decisions 2026-08-05:** (1) amplifier queue → **pre-classify with evidence into a review file, NOTHING enters the graph until owner approves a batch**; (2) **Datasette approved as a dependency** — pin in `requirements.txt` like networkx |
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
| 2026-08-05 (1b) | ⚠ **`spell_scaling` lost its FK to `spells`, deliberately** | The T4 rank migration inserts rows for level-60 rank siblings, and in all 697 wrong-rank cases the sibling id is absent from `spell-export.json` — an FK rejects exactly the rows that fix the wrong-rank problem. Same precedent as `owned_cards` (1a) |
| 2026-08-05 (1b) | 🆕 **Trigger attribution semantics decided (owner, 2026-08-05): bounded walk, flagged** | Depth ≤ 2, cycle-safe, single-path targets only, out-of-catalog targets only, `via='trigger_hopN'`, `confidence='inferred'`, chain in `evidence_ref`. 724 rows / 444 cards; 26 multi-path targets deliberately unattributed. In-catalog targets are never double-attributed — their magnitude is their own row |
| 2026-08-05 (1b) | ⚠ **T5's "migrate and retire" became "migrate and demote"; `exclusivity_buckets` stays a TABLE, not a view** | Staging tables are kept as ingestion inputs (their seeds own them, run earlier in the chain); `spell_relationships` is the one query surface. A view could not round-trip bucket 3 (Holy Focus) — a single-member bucket has no pairwise edge to reconstruct from. Every multi-member bucket is validated as an edge group each rebuild |
| 2026-08-05 (1b) | 🆕 **`spells.crit_table`/`hit_table`/`rolls_hit_check`/`proc_icd_seconds` removed** | T4's "one home per fact": doc-confirmed combat-table values seed `doc_confirmed_mechanics` (reworked `seed_spell_flags.py`) and surface only in `spell_mechanics` |
| 2026-08-05 (1b) | ⚠ **Most `spell_mechanics` conflict rows are multi-effect-slot collisions, not cross-source disagreements** | 29 rows carry `confidence='conflict'`; sampled cases are one spell whose two effect slots have different radii or chain counts feeding a single column (e.g. 276884 radius 8 vs 5). Honest per §2.3, but T8's conflict sweep should bucket them separately from genuine source disagreements or they become noise |
| 2026-08-04 (1x) | ❌ **RETRACTED: "reading a coefficient off the catalog's Rank-1 entry is probably safe."** Coefficients DO scale with rank; **`spell_scaling` needs rank keying** | Phase 0 derived it from **one** line (Holy Supernova, identical at R1 and R6). Measured across all **1,580** multi-rank lines with 2+ DBC members: numeric coefficient constant 696 / **varies 169**; tooltip literals constant 132 / **varies 34**. The shape is retail's low-rank penalty — ramp then plateau, 110 of the 169 — and the catalog stores **Rank 1**, the deepest point of the penalty. Seven catalog entries measurably affected (Sun Down SP 0.4→1.3 = 3.25×; Grasp of Darkness 0.5→1.4 = 2.8×; Spirit Charge changes term type SP→AP). Seven is a **floor**: 547 more state no coefficient in either rank's text. Migration deferred to T4 by owner decision |
| 2026-08-04 (1x) | 🚨 **CORRECTED: `EffectBonusCoefficient` is NOT the SP/AP coefficient** — it is `EffectBonusMultiplier`, default 1.0 | Phase 0's *"311 blocked spells carry a non-zero `EffectBonusCoefficient` (SP/AP scaling)"* counted right and read the field wrong. **7,647 of 9,211** non-zero values are exactly 1.0; the recurring non-defaults are retail's cast-time formula (`0.429 = 1.5/3.5`, `0.714 = 2.5/3.5`); calibrated against 98 spells stating their own `$SP*x`/`$AP*x` it agrees **4 times**. Of the 343 blocked spells with any coefficient, **270 carry only 1.0** → the real surface is **≤73, not 311**. Building the extractor on it would have fabricated SP coefficients across 311 spells *with tier-4 provenance attached*. Ascension keeps applied coefficients in **tooltip text**; the field is stored as `bonus_multiplier` and never emitted as SP/AP |
| 2026-08-04 (1x) | 🚨 **A live tooltip can render an arithmetically impossible range — and solving it pins values no single source states** | Hammer from the Heavens displays *"194 to 147"* in-game (owner screenshot, tier 1). The description hand-rolls level scaling at **two different rates** — `($PL-10)*2.4` on the min, `($PL-10)*1` on the max — while `$m1`/`$M1` render the raw base unscaled. The min's rate matches the effect's real 2.4/level and is **correct**; the max's 1/level is **wrong**, so the min overtakes it above ~level 29. At 60 it should read **194 to 217**. Treating the two numbers as simultaneous equations cancels the unknown stat term and yields **`L = 60` exactly** — the character's level falls out of a tooltip |
| 2026-08-04 (1x) | ❌ **RETRACTED, twice, on Hammer from the Heavens: "double-applies scaling" and "caps at level 40 → flat 74–97"** | Both were mine, both wrong, both caught the same day. A double application would render 242/195 — *above* the observed minimum, impossible. And a `--with-dbc` re-extraction returned **`MaxLevel = 0`** (uncapped). The 48-point gap that motivated the cap is fully explained by the stat term `A = 72`. **The flat is 122–145 at level 60**, and §10's assumed 30/30/40 split becomes **~21/23/57** — right that SP and AP are equal, wrong about how flat-dominated it is |
| 2026-08-04 (1x) | ❌ **RETRACTED: pooled crawl data "ruled out" the higher flat** — it cannot settle a level-scaled magnitude at all | 17,972 hits were cited as decisive, treating 12 crawled characters as if all were level 60. **The crawl records no character level** (Phase 0 T2) and this ability scales 2.4/level — a level-40 character deals 74–97 for the same spell. With Holy partial resistance on top, the figures discriminate nothing. **Generalised into primer §5:** never cite pooled damage about a magnitude that varies with something the crawl does not record |
| 2026-08-04 (1x) | 🆕 **`max_level` added to `spell_dbc_raw`, and the owner re-extracted the same day** | Without it a level-scaled magnitude cannot be computed. **1,653 spells carry a real cap; 196 of the 354 level-scaled catalog spells are capped**, so T4 needs it. Column alignment verified independently (Holy Supernova R6 `spell_level 60`, R1 `14`, cooldown 40,000 ms). ✅ **No longer a T4 blocker — it is populated** |
| 2026-08-04 (1x) | 🆕 **Magnitudes are also reached by `EffectTriggerSpell`, not only by tooltip `hidden_refs`** — ~519 spells still unattributed | Found while checking **Hammer from the Heavens** (`282987`), the owner's largest stat-weight unknown: it is triggered by Hour of Judgement (`282986`), two hops from any card, so `1x`'s hidden_ref-based extractor never saw it. **529 catalog → out-of-catalog trigger links across 519 distinct targets.** Deliberately not built here — multi-hop chains need cycle handling and an attribution decision, and **T5 already owns the `triggers` relation** |
| 2026-08-04 (1x) | ⚠ **The "15 rank differences" number was nearly published; the honest figure is 7** | Eight entries had a coefficient at one rank and none at the other — **not** a difference. Three confirmed causes: a compound form the regex cannot read (`($SP+$AP)*0.36`, Bone Arrow), a formula moved into a sub-spell (`$71791m1`, Deep Freeze), and a rank line that pulled in a **different ability of the same name** (Blood Drinker) — the duplicate-name trap surviving inside `dbc_spell_rank`'s grouping. Now a separate verdict, excluded from the headline |
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

**Resolved in session `1x` (2026-08-04):**
~~Does `stats_summary.sourcesByStat` itemise per-source stat contributions?~~ ✅ **Answered
and CLOSED after four deferrals — and its recorded justification was wrong.** It itemises
**item sources only** (`gear` / `enchant` / `set`), never talents or path grants, so it
could never have settled the Path of Duality question `PROGRESS` claimed for it. ⚠ **The
whole `stats_summary` block is gear-only** (explicit `_gearOnly` key; a level-60 character
shows Strength 13) — a real trap for Phase 3, which must not read it as a character sheet.
✅ Genuine value instead: a clean gear-only stat vector for 48 characters, exactly what
§2.10's gear tiers need — plus independent confirmation of 8 of 9 level-60 rating
divisors, with **armor penetration the lone conflict** (below). ·
~~Do damage coefficients scale with rank?~~ ✅ **YES** — 169 of 865 lines with numeric
data vary, 34 of 166 with text data vary, in a ramp-then-plateau shape. `spell_scaling`
needs rank keying; see the plan-changes table. ·
~~What are Hammer from the Heavens' coefficients?~~ ✅ **RESOLVED mid-session** from an
owner-supplied live tooltip + the db.ascension.gg pages + a `--with-dbc` re-extraction:
**122–145 Holy, +9.1% SP, +9.1% AP** at level 60 (level scaling **uncapped**). This was
the largest single unknown in the Paladin build's stat weights, open since v5. §10's
assumed 30/30/40 split becomes **~21/23/57** — right that SP and AP are equal, wrong
about how flat-dominated it is, which *reinforces* the existing spell-crit-first gearing
order. ⚠ Two intermediate answers were retracted along the way; see the plan-changes table.

| Question | Blocks | How to settle |
|---|---|---|
| ⚠ **NEW (1x):** is armor penetration 5 or 4.2 rating per 1% at level 60? | Physical-build stat weights only | **Conflict, recorded not resolved (§2.3).** The site's own calculator says **5**, the client's `gtCombatRatings` says **4.2**. Every other level-60 divisor agrees exactly across both sources (crit 14, hit 10, haste 10, expertise 2.5, dodge/parry 13.8, defense 1.5, block 5). Settle with a level-60 in-game armor-pen reading |
| What is the current maximum report ID? | Sizes the historical backfill | Emerges from a full crawler run (no list endpoint exists to ask directly) |
| ⚠ **NEW (1x):** does a level-scaled flat ever need a cap the crawl/tooltip can't reveal? | Nothing — recorded for completeness | ✅ Largely answered: `max_level` is extracted and populated. **1,653 spells carry a real cap; 196 of the 354 level-scaled catalog spells are capped.** What remains unverified is whether the engine applies the cap the way `min(level, max_level)` assumes — Hammer from the Heavens couldn't test it (`max_level = 0`). Settle opportunistically by checking one *capped* level-scaled spell's in-game tooltip against the computed value |
| ~~⚠ (1x): should `EffectTriggerSpell` chains be followed for magnitude attribution?~~ | — | ✅ **RESOLVED in `1b` (owner decision 2026-08-05):** yes, bounded — depth ≤ 2, cycle-safe, single-path, out-of-catalog targets, `confidence='inferred'`. 724 magnitude rows attributed; 26 ambiguous targets deliberately left unattributed (their attribution question is real but needs per-case judgment, not a looser walk) |
| ⚠ **NEW (1b):** 243 `talent_amplifiers` rows are flagged 'needs manual review' and contribute no graph edges | Amplifier coverage of the relationship graph | Human read of the staging rows (bulk-extracted target lists that didn't cleanly resolve). T6 should carry this as a standing open question; a few (e.g. Improved Cleave, now hand-seeded) are high-value |
| ⚠ **NEW:** the 97-card gap between `in_current_pool` (3,129) and BisBeard's S10 count (3,226) | Exactness of the card-pool scope | Intersect BisBeard's `entryId` list against `in_current_pool=1` and inspect the difference |
| Which of the 5 `class_origin` conflicts is right? | `class_origin` correctness | Proc test or live tooltip per spell. Note Fel Infused Weapon's existing value ("Duality") is a Path, not a class |

| Where is BisBeard's item JSON actually served from? | Phase 3 T4 gear source | Read the base-URL construction in its `itemDatabaseSync` chunk, or ask the author |
| Are `Item.dbc`/`ItemStat.dbc` layouts stable enough to extract? | A gear database with no third-party dependency | Extract a handful of known items, compare against in-game tooltips |

| What do CA slots 14/15/17/21/25/29–41 mean? | Acquisition / prerequisite modelling | Correlate `raw_ints_json` against known card properties — no re-extraction needed |
| ⚠ **NEW:** Fel Infused Weapon per-level term — db renders **4.5**/level, client DBC says **1.5** (exactly 3×) | The card's flat damage component, which the docs currently have in the wrong *shape* too (`ppl` is a per-level rate, not a flat add) | **In-game tooltip read at level 60** — fully resolved there, tier 1, beats both. db was byte-faithful on Holy Supernova, so suspect a rank/variant (`276069` vs `276076`) or a stale snapshot |
