# Session `1c` — 2026-08-05 — T6–T10: epistemics, profile, audit, browsing, volatility

> **`HISTORICAL`** — the record of a past session or a completed phase. Immutable. It **may contain claims that are false today**, and that is correct rather than a defect — it records what was believed at the time. **Never citable as current truth.** *(Classified `3f` F8c, 2026-08-07.)*

**Phase 1 is complete.** All five remaining tasks landed, plus the four carry-overs from
`1b`. No game-mechanic verdict changed — this was a tooling session. Rebuild is **18
steps (~90s)**; every exit criterion in `PHASE_1_spell_database.md` is checked and
annotated there.

Owner decisions taken this session (asked at session start):
- **T10 volatility: Darkmoon-only, strict** — the cross-realm 2016→ corpus is not folded
  in, even labelled. The score carries an explicit thin-data block instead.
- **Full 1c scope in one session** (T6–T10 + carry-overs), commit per task.

---

## What was built, in order

### 1. Compound-form extraction gap — CLOSED (carry-over from 1b, open since primer v14)

`core/spells/text_extraction.py :: extract_scaling()` now matches, verified against the
full 3,061-entry export with a token survey first:

| Form | Example | Previously |
|---|---|---|
| compound sum, factors either side | `($AP+$SP)*4*4*0.02` (Eviscerate), `0.0128*($AP+$SP)*1` (Rip) | missed |
| school-suffixed SP tokens | `$SPFR*0.0096` (Winds of Winter), `$spfi*.31` | missed |
| coefficient-before-token | `(0.0066*$SPH+0.0125*$AP)*6` (Seal of Vengeance) | missed |
| lowercase | `$sp*0.69` (Soul Fire) | **silently missed** |
| BH / SPI / STA | `$BH*0.158964` (Flash Heal), `$STA*2` (Rock Barrier) | missed |

Guards verified against real false positives: `/100*$AP` (division context, Concussion
Blow), `$m2*$AP` (the digit belongs to `$m2`, Rune Strike), and factor chains of bare
1–5 integers (CP-count ambiguity → **skipped, not guessed**). Anti-Magic Zone's genuine
`2*$AP` survives.

**Result: `spell_scaling` 1,058 → 1,348 rows, 625 → 737 spells.** Holy Finish (SP/AP
0.02 quadratic) and Winds of Winter's Frost term (SPFR 0.0096 quadratic) auto-extract —
their hand-seeds in `seed_cp_scaling.py` became no-op guards. BH terms route to
`healing_formula_terms_json` in the mechanics resolver. `$PL` is deliberately excluded
(level scaling belongs to `spell_effect_values.per_level`, tier 4 — a text "PL
coefficient" would be a second, weaker home for the same fact).

Deliberately untouched: `SP_PAT`/`AP_PAT`/`RAP_PAT`, which `rank_scaling.py` imports for
rank-text comparison — widening them would shift the validated `1x` rank-ramp verdicts.
`ingest/dbc/build_dbc_index.py :: extract_scaling_terms` now delegates to the shared
implementation (effective at the next `--with-dbc` run).

### 2. T6 — epistemics layer

- `confirmed_facts` + provenance columns (in the CREATE — the db is dropped each rebuild,
  ALTERs would be theatre). Backfill stamps `Darkmoon`/`S10`/`doc :: section`.
- `open_questions` (28: 23 open, 1 in-progress, 4 resolved-kept-as-history) and
  `retractions` (24) hand-curated from PROGRESS plan-changes, the primer's retraction
  history, and the build doc's assumption register. **Deviation from the phase doc's DDL:
  both tables key on a `slug` column** — autoincrement ids reset each rebuild.
- `fact_spell_links` derived per rebuild (`core/spells/epistemics.py`): ids ≥ 100000 link
  at `inferred`; smaller ids only with name corroboration in the same fact ("393 rating"
  can never link to spell 393); bare names at `needs_review`, never auto-approved;
  duplicate names link every candidate. 37 + 27 + 346 rows.
- `find_answered_questions()` (token-overlap check) runs in the seed and in the audit.
  Current top candidates are all questions deliberately citing their partial-answer facts
  — no forgotten answers, as expected from a same-day curation.

### 3. T10 — volatility (owner: Darkmoon-only strict, report-only)

`core/spells/volatility.py :: volatility_score(conn, spell_id, ...)`. Darkmoon-tagged
patch entries only; realm tags exist only from 2026, so today's window is ~12 days and
the payload says so (`data_thin`, `thinness_note`, band computed over the observed window
only — "untouched" can never read as "stable for a year"). Report-only contract restated
inside the payload. Sanity case: Mongoose Bite = 6 touches/12 days → `hot`.

### 4. T7 — `spell_profile()` + `cli/profile.py`

Rank gaps and conflicts surface FIRST (live `resolve_spell_mechanics()` call — rank_gap
is computed, not stored). Duplicate names refuse with a candidate list (hard rule 5).
Out-of-catalog ids with a DBC record profile as `type='dbc_only'` — **282987 profiles**,
and Hour of Judgement's profile shows the trigger-attributed 122–145 flat end-to-end.
`mode='fast'` for sim loops. Real usage joins `scouted_builds.db` when passed.

Exit-criterion check: 19/20 protect-list names resolve. The miss is bare **"Judgement"**
— the build doc's shorthand; no in-pool card carries that exact name (two CA rows named
`Judgement`, 7665/30448, both `in_current_pool=0`). Not a profile bug; noted here so the
next session doesn't chase it.

### 5. T8 — auto-debugger + protocol generator

`tools/audit/audit_gaps.py` — 12 sweeps, rebuild step 18 + standalone (~0.2s), writes
`data/derived/audit_report.md`. Current standing: **183 items, all triaged**:

- **Conflict sweep buckets multi-effect-slot collisions (28) separately from
  cross-source disagreements (1)** — the 1b requirement. The one "cross-source" hit,
  Champion's Spear (291180) weapon_damage_pct 150 vs 50, is actually an
  initial-hit-vs-DoT **component collapse**: both values are real, one column can't hold
  two components. Queued; a per-component formula-terms refinement would dissolve it.
- Staleness 0 (mechanics re-verified at rebuild), coverage 0, realm/season 0.
- Phase-boundary sweep wired to **2026-08-08** — fires in 3 days; no phase-keyed
  artifacts exist yet, so it will start by flagging nothing but exists by design.
- Outlier-coefficient sweep (new, serves the new open question): 277595 RAP/SP 6.0,
  984513 SP 5.0, 273458 SP 3.5 — cached `dbc_hidden_formula` rows from the old narrow
  extractor; re-extract at next `--with-dbc`.
- 78 unresolved changelog prose names (expected for `prose_name_match` at `low`).

**Auto-fix withdrawal worth recording:** a "mark crosswalk rows whose target vanished"
fix matched **7,654 rows** — all out-of-pool CA rank slots that were never in
`spell_dbc_raw`'s scope. Absent-from-extract ≠ vanished; without history the two are
indistinguishable. Withdrawn same-session, replaced by a report-only count in the
provenance sweep. (The polluted notes were reset by the next rebuild.)

`tools/audit/protocols.py` — the primer's test-design rules as code: card-destroying
protocols raise `CardDestructionRefused` (the scan covers method/setup/record only, so
the reroll-mechanics question keeps its observational protocol — a blanket scan had made
it un-protocolable); <3-point discriminators emit "insufficient discriminator" instead of
a sample size; target level and per-hypothesis outcomes are mandatory and structurally
checked (identical outcomes rejected). **7 hand-written protocols** (exit criterion: 5),
24 total.

### 6. T9 — search + browsing

`core/spells/search.py :: search_spells(conn, **filters)` — 13 AND-composed filters;
unknown filters and orphaned coefficient bounds raise. `cli/browse.py` launches Datasette
(smoke-tested serving the canned open-questions query) with
`tools/browse/datasette_metadata.json` — 12 canned queries, `spell_mechanics` /
`spell_relationships` first. **Datasette pinned in requirements.txt** (owner decision).

### 7. Amplifier review queue (owner decision: approval-gated)

`tools/audit/build_amplifier_review.py` → **`reviews/amplifier_review.md`** (committed).
All 243 needs-manual-review `talent_amplifiers` rows, pre-classified with tooltip
evidence inline:

| Group | n | Proposal |
|---|---|---|
| `verbatim_ability` | 58 | `amplifies` edge(s) — misfiled by the v3 bulk scan; high-confidence tier |
| `verbatim_ability_check_stat` | 12 | named ability + stat wording — check WHICH thing is amplified |
| `school_amplifier` | 16 | `amplifies_school`, low confidence, proc-test flagged |
| `stat_or_defense` | 105 | EXCLUDE from graph — Phase 2 stat modelling owns these |
| `unclassified` | 52 | real human read needed |

Approval contract: `[x]` approves the proposed action, `[!]` rejects with a note. **The
approval ingester is deliberately not built until a first batch exists.** Question
`talent_amplifier_review_queue` is `in_progress`.

---

## Doc changes

- `PHASE_1_spell_database.md`: progress table complete, 1c deviations block, exit
  criteria annotated ✅.
- `PROGRESS.md`: pointer → `2a`, session log row, 5 plan-change rows.
- Primer → v23 (title fixed from a stale v20), §5 rebuild bullet updated (18 steps,
  profile-first practice).
- `INDEX_GUIDE.md` → v12.
- No new `confirmed_facts` — nothing game-mechanical was measured. No `bugs/` entries —
  no tooltip-vs-log discrepancy surfaced (the 291180 collapse is our modelling
  granularity, not a game bug).

## Post-close addendum (same day)

The two 1b-audit feedback items were checked after close: the Datasette pin had landed
in T9 as recorded; the stale `rebuild.py` step label for `seed_spell_flags.py`
("crit_table / proc_icd_seconds", columns retired in 1b) had been missed and is now
fixed (commit `401e649`).

## For session `2a`

- **Call `spell_profile(mode='fast')` (or `resolve_spell_mechanics`) from the ability
  model — not raw tables.** Rank gaps and conflicts are only surfaced on that path.
- `spell_scaling.term_type` is no longer just SP/AP/RAP/WEAPON — the combat engine's term
  handling must know SPFR/SPH/…/BH (school-scoped SP terms matter for hybrid double-dip).
- The **2026-08-08 phase boundary** lands during/near 2a; the audit's phase-boundary
  sweep begins flagging pre-boundary stat weights the day it flips. `SEASON = 10` stays
  hardcoded in the crawler (bump at S11).
- Open questions worth an in-game minute when convenient (protocols exist for each):
  armor-pen divisor (one sheet hover), Fel Infused Weapon per-level (one tooltip read),
  Elric's active path + AP anomaly (one sheet read).
