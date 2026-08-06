# PROGRESS

> ✅ **2026-08-06 — SESSION `3d` IS DONE. Next session is `3e` (modelling).**
> Session record: `primer/Session_2026-08-06_3d_hygiene_and_instrument.md`.
> **Read `primer/ENGINE_BUGS.md` first — it is `3e`'s concrete work list.**
>
> **§0 invariant HELD: the gate reads 5 of 41, 2 qualified, opening and
> closing.** Six commits, one per block: `342b493` A · `47bd374` B · `2d3db19` C
> · `788a771` D · `a77875e` E · `69f2192` F. All seven `3d` exit criteria met
> (table in the session record).
>
> 🚨 **THE FINDING `3d` DID NOT GO LOOKING FOR: THE GATE'S COHORT MOVES ON ITS
> OWN.** Rebuilding `builds.db` took the gate from **5 of 41 to 4 of 38 with
> ZERO code changes** — isolated by restoring the old corpus, which restored
> 5 of 41. `calibrate_crawled.candidates()` is `ORDER BY character_id LIMIT 120`
> and the qualifying population grew **157 → 180** when the daily crawler fired,
> so the limit is not a cost cap but a **sliding window keyed on an arbitrary
> id**. Four characters left and four entered for no reason but their id.
> **Two gate results from different days are not comparable even with identical
> code.** 🛑 Deliberately NOT fixed — changing a gate's population is not a
> hygiene edit. **It is `3e`'s first job**, and `predictions/gate_manifest.json`
> now records the cohort by id so the comparison is checkable.
>
> ⚠ **Consequence for `3e`:** `build_builds_db.py` is in the chain but **opt-in**
> (`py cli/rebuild.py --with-corpus`), precisely so a routine rebuild does not
> silently redefine the gate. Rebuilding the corpus is a deliberate act, like
> `--with-dbc`, and invalidates comparison against any earlier gate result.
>
> 🛑 **Three owner questions, none blocking** (detail in the session record §
> "For the owner"): the cohort slide above; whether `calibrate_vs_log` should
> **substitute** the independent Holy Shock coefficient (0.2145) rather than just
> report it beside the back-solved 0.40 — `3d` reports, because substituting
> changes a calibration number; and a convention conflict where the `3d` primer
> said to file engine defects in `bugs/` while `bugs/README.md` says that folder
> is for **game** bugs only — the repo won, so they are in
> `primer/ENGINE_BUGS.md`.
>
> **What `3e` inherits, ready to use:** two non-paladin fixtures wired into
> `check_sim_engine.py` with **six real engine defects** registered as XFAILs
> (`primer/ENGINE_BUGS.md`); slice accuracy reported per character and as a
> cohort median (**160%**); a **pre-registered, outcome-blind 5-character
> holdout** (`holdout_3e_crawled_gate_validation_set` — 460, 461, 462, 463,
> 7661) that must not be tuned against; a dated successor criterion in
> `CALIBRATION_TOLERANCE.md` effective at the next gate; and
> `calibrate_vs_log.py` that refuses to run without a stated stat block.
>
> ⚠ **E1/E5 are coupled and must be fixed together**: 6 of 7 DoTs on a
> DoT-caster board are cast ZERO times, which currently MASKS the predicted
> DoT-recast bug; and `combo_points` never incrementing is masked by `apl_gen`
> not classifying any per-combo ability as a finisher in the first place.
>
> 📌 **`primer/ADDENDUM_3D_to_3E_mage_capture.md` landed mid-`3d` (commit
> `d6fa1e2`) and is `3e` input. Checked against what `3d` shipped:**
> * Its §2 supersedes F2 with a `--stat-block <path>` parser instead of four
>   hand-typed flags. **`3d` shipped F2 as written, so by the addendum's own
>   terms this is additive `3e` work, not a rework** — and the refusal semantics
>   it says to keep are exactly what shipped.
> * Its §4 replaces the *generic* synthetic caster with the incoming Frost Mage.
>   **Both `3d` fixtures still stand**: its own table keeps the combo-point melee
>   and the DoT caster as "still needed", since Frost is burst, not DoT.
> * Its §7 asks that the `candidates()` exclusion cover the Mage too.
>   **Already true** — F1 excludes by `character_snapshots.source`
>   (`'own_capture'`), not by character, so any owner-captured character is
>   excluded automatically.
> * ✅ **CLEARED in `3e` A6 — the owner action is DONE.** The updated addon
>   landed at commit `9486283`, version `2026-08-06c`, carrying all five fields.
>   ⚠ Two of them are **named differently from the addendum**:
>   `SpellHaste_raw_UNVERIFIED` / `MeleeHaste_raw_UNVERIFIED`, not `*_total` —
>   the addon read `GetMeleeHaste` at 1.06% against the rating line and
>   explicitly does not trust them (`.lua:197-209`). The addendum's §1 table is
>   corrected in place. Anything written against the old names misses the fields.
>
> ---
>
> <details><summary>Superseded: the <code>3d</code> work-order pointer</summary>
>
> 🔴 **2026-08-06 — `3c` is audited and CLOSED. Next session is `3d`.**
> **Work order: `primer/SESSION_3D_PRIMER.md`. Read it first.**
> Findings it rests on: `primer/AUDIT_3C_ADVERSARIAL.md` (adversarial audit of
> `3c`, code-verified against `a36f666`). `primer/AUDIT_3C_handoff.md` remains
> the record of what `3c` did — read it for §2's log-upload findings, but read
> the adversarial audit for what is actually true.
>
> 🛑 **`3d` MUST NOT MOVE THE GATE.** Run `calibrate_crawled.py` before and after;
> both must read **5 of 41, 2 qualified**. Any difference is stopped on and its
> cause reported — never fixed forward. That invariant is what makes `3e`
> readable. Detail: `SESSION_3D_PRIMER.md` §0.
>
> 🚨 **Deadline — the server flips to Phase 2 on 2026-08-08.** `SEASON` is
> hardcoded in **five** places and nothing asserts it against `/api/phases`.
> `SESSION_3D_PRIMER.md` Block A ships on its own commit if the session runs long.
>
> **Phase 4 is NOT next**, and the `3c` framing of why was wrong in both
> directions. Corrected: `PHASE_3` lists **seven** exit criteria, not six;
> **three** are outstanding (#2 crosswalk/string-matching, #4 measured CI,
> #7 `ContentProfile`), not two; and **#7 is FAILED, not unverified** — 6 of 8
> presets in `core/sim/content.py` carry `provenance="assumption: …"` in their
> own strings. Criterion #4's mechanism does not exist at all: no code anywhere
> sets `inference.promoted=1` and `uncertainty.py`'s `POLICY` has no `measured`
> band. ⚠ `ingest/logs/` is a **strawman path** — it appears nowhere in `PHASE_3`.
>
> **Owner decisions, 2026-08-06 — settled, do not re-open:**
> * `3d` = hygiene + instrument only, **no modelling changes**.
> * **PHASE_3 T6 (log ingestion) is REINSTATED and promoted** to its own session,
>   `3f`. It is **not** absent as `3c` claimed — parsing is done and verified
>   (`tools/log_parser/`), the correlation rule is seeded (`seed_confirmed.py:47`),
>   the glob is written (`calibrate_vs_log.py:314`). What is missing is mtime
>   windowing, UTC conversion, and **any writer from a log into `builds.db`**.
> * **PHASE_3 T5 (capture addon) is DEMOTED**, not reinstated — ALC +
>   `decode_alc.py` already decode every player build in a log.
> * **PHASE_3 T7** follows `3f` (hard dependency).
> * **Block D runs on Opus.** Not a default to be re-litigated.
>
> 🔤 **NAMING, fixed in `3d` B1.** `PLAN_3C_clean_exit.md`'s tasks are now
> **`C1`…`C13`** — they used to be `T1`…`T13` and collided with
> `PHASE_3_builds_repo.md` on **all eight** numbers (T5 meant *capture addon*,
> *pets* and *three sim tiers* depending on the file), with `PHASE_2` a third
> space. `AUDIT_3C_handoff.md` collided with itself 135 lines apart. **In this
> file every `T<n>` is a PHASE doc's task and is qualified as such; a `C<n>` is
> always PLAN_3C's.**
>
> **Session map:** `3d` hygiene + instrument → `3e` modelling + gate re-run →
> `3f` PHASE_3 T6 → PHASE_3 T7 → re-read Phase 3 exit honestly → Phase 4.
> Phase 4's hard blockers are recorded in `SESSION_3D_PRIMER.md` §11 so they are
> not rediscovered. Phase 4 Part C1 (principles corpus) is genuinely unblocked
> now and can run in parallel — it has no sim dependency.
>
> Gate: **5 of 41 within ±20%, 2 qualified → EXIT NOT MET** under the coverage
> rider stamped before the run. ⚠ The rider's "stamped before" claim is
> **plausible but unverified** — the addendum, the `QUALIFIED_COVERAGE_PCT`
> constants and the ingest all land in the same commit `79c6568`.
> ~~🔒 That gate result is **not reproducible by anyone but the owner**:
> `data/derived/` is gitignored, no `.db` is committed, and `build_builds_db.py`
> is in no chain and no `.bat`. `SESSION_3D_PRIMER.md` Block E fixes this.~~
> ✅ **Partly addressed in `3d` E1/E2** — the corpus builder is in the chain
> (opt-in) and `predictions/gate_manifest.json` is committed per run, so a gate
> result now carries its cohort, criteria, corpus counts and git SHA. ⚠ It is
> still not *rebuildable* from committed source alone: the corpus's bulk needs
> gitignored tier-2 crawl data. What an auditor gains is the ability to check
> whether a claimed result matches the manifest — not to regenerate it.
>
> </details>

**Claude Code maintains this file. Update it at the end of every session, before writing the handoff.**

This is the pointer that lets a new session start with no memory of the last one. Keep it short —
detail belongs in `Session_*.md` handoffs, not here.

---

## Current position

**✅ `3d` IS DONE (2026-08-06) — hygiene + instrument, no modelling change.**
Session record: `primer/Session_2026-08-06_3d_hygiene_and_instrument.md`.
The gate is untouched at **5 of 41, 2 qualified**, verified opening and closing.

### 🔴 FIRST ACTIONS NEXT SESSION (`3e`)

1. **Read `primer/ENGINE_BUGS.md`.** Six real engine defects, each a registered
   XFAIL in `check_sim_engine.py` with file:line. That is the work list.
   ⚠ **E1 and E5 are each MASKED by a second bug** and must be fixed in pairs —
   fixing one alone will look like it did nothing.
2. **Pin the gate cohort by id.** It currently slides as the corpus grows
   (5-of-41 → 4-of-38 with no code change; see the header). Until it is pinned,
   no two gate results are comparable, which makes every other `3e` measurement
   unreadable.
3. **Righteous Vengeance: un-break AND talent-gate.** `tiers.py:439` reads a
   `crit_damage` key written nowhere; `_add_swing_sources` is called from
   `fast_sim` with no check that 61840 is in `build_spec.talents`. Fixing the key
   without the gate lands ~30% of crit damage on **all 41** characters instead of
   the 109-of-371 boards that hold it. Measure the cohort-wide delta **before**
   accepting.
4. **Report slice accuracy before and after every coverage task.** A task that
   raises coverage while dropping slice accuracy has moved the metric, not the
   model. Cohort median today: **160%**.
5. 🛑 **Do not tune against the holdout** — `holdout_3e_crawled_gate_validation_set`
   (character ids 460, 461, 462, 463, 7661). Read it once, at the end.

### Still blocked on the owner (unchanged by `3d`)

| Item | Blocking |
|---|---|
| Tracker #200295 re-test + PBL × LC discriminator (needs in game) | Build doc §2/§11 revert |
| Consecrated Holy Weapon (200818) live tooltip | 25.1% of buffed damage, unmodelled |
| Identify Siphon Health (18652) / Swift Retribution (853484) | Passive-layer completeness |

---

## Superseded: the `3b` critical-path position

**✅ 3B's CRITICAL PATH IS DONE (2026-08-06).** `PLAN_3B_UPDATE.md` §5's
sequence — fix the gear layer, then re-run the gate with the miss
**decomposed** — ran end to end. Session record:
`primer/Session_2026-08-06_3b_gear_and_decomposition.md`. Owner scoping
decision: critical path first; **3b T5 (addon) / T6 (log ingestion) /
T7 (session automation) are deferred, not blocked**.

### 🎉 The calibration gate PASSES — 4 of 41, on one missing input

`py tools/audit/calibrate_crawled.py --limit 120 --max-lag-hours 0`
→ **4 of 41** level-60 crawled characters within ±20% (criterion ≥3).
Was 0 of 41. **Nothing was fitted**; the whole move came from finding that
**weapon damage is absent from every stat block** in the crawl
(`resolved_bisbeard.damage` is NULL on all 1,413 weapon-slot entries), so the
sim had been giving every candidate **no weapon at all** — zeroing white swings
and every weapon-percent ability. It is parsed from the rendered item
description and **self-checked against that description's own stated DPS**,
849 of 849 agreeing within 3%; a parse that fails the check returns nothing.

> ⚠ **Superseded 2026-08-06 by the audit-gated ingest session: the gate now
> reads 5 of 41, 2 qualified, and Phase 3 EXIT is NOT MET** under the coverage
> rider stamped before that run. The reading below stands as the record of why
> the rider exists.

### 🛑 But read the pass with its coverage — it is not clean

Only **one** of the four passes (Ari, −10.3%) also has ≥50% of its real damage
modelled. The other three (Chastie 5%, Zaczao 6%, Xoller 13%) agree on the
total while the sim reproduces almost none of their kit — **compensating
error**, which the ±20% aggregate criterion is structurally blind to. The
criterion was **not** redefined after the result was seen; the qualified count
is reported next to it. **Owner decision needed:** open question
`crawled_gate_passes_by_compensating_error` — should Phase 3's exit carry a
magnitude-coverage floor, and at what level?

### What the decomposition established (PLAN_3B §5.2)

- **Gear resolution: ELIMINATED** for 30 of 41 — median gear-stat coverage is
  **100%**, so they were simmed on their entire real gear set and still missed
  by a median −92% (−68% after the weapon fix). ⚠ Coverage is reportable but
  **not repairable from the corpus**: an unresolved item is unresolved on every
  snapshot (0 of 592 resolve anywhere else) because those ids are absent
  upstream. Open question `crawl_gear_coverage_is_not_repairable`.
- **Buffs: median +0.0%** (max +10.6%) — the 3b pre-flight finding holds.
  `crawled_gate_residual_after_buff_layer` is **resolved**.
- **Magnitude coverage: DOMINANT** — the sim produces damage for a median
  **37%** of what these characters actually dealt (20% before the weapon fix).
  The gate report now ends with a **ranked list of the biggest unmodelled
  abilities** — measured demand, and the shortlist the next magnitude work
  should read.

### 🆕 Gear model: the difficulty axis lives in the item_id

Same-name items really do carry different stats (**476 of 1,157** names span
several ids at different tiers) — but **each variant has its own item_id**, and
`item_id -> (tier, stats)` is a function (0 ids carry two stat blocks). So
`PLAN_3B` §3 was amended (owner, 2026-08-06): **never map item NAME to stats**
stands and is the real hazard — the crawl's own 98 `name_fallback` matches are
it, now visible as `snapshot_gear.stats_match_type` — while "the deduped
`items` table is lossy" is dropped, because keying on item_id is lossless.

### 🆕 The magnitude-coverage bottleneck has a SOURCE now — db.ascension.gg

A consolidation review classified **every** unmodelled damage row across the
gate cohort by cause: **42.9%** spells absent from our DBC extract, **41.1%**
magnitude-but-no-coefficient, 9.1% autos/extra-attack procs, **5.5%** a real
resolver/APL gap, 1.3% no decoded magnitude. **Only 5.5% is a code problem** —
the resolver and APL are fine.

🆕 **`db.ascension.gg` states applied coefficients outright** (Icy Penance:
`Value 284 · SP 29.0% · AP 7.8%`, against our decoded flat of exactly 284) and
**states `EffectTriggerSpell` links too** — HoJ → HftH comes off the page's own
href. The project had used it by hand once (`1x`, HftH) and never systematised
it. `tools/scrapers/scrape_ascension_db.py` + `core/spells/db_ascension.py`
now do, **scoped by measured demand and never by enumeration**: 285 ids cover
90% of all logged damage, 2,902 cover everything observed (~2 h at a 2s delay).

🛑 **A scraped coefficient is trusted only where the page's stated base value
reproduces the flat we decoded from the client's numeric fields**; a
disagreement REFUSES the coefficients. Full run of 2,902 records, **after the
2026-08-06 `--with-dbc`**: **2,692 agree / 202 unverifiable / 8 disagree**;
1,634 spells state a coefficient; **329 trigger edges**.

✅ **The `--with-dbc` run landed and validated the source at scale.**
`spell_dbc_raw` 16,566 → **17,400** (+834); check digits 14,100 → **14,913**.
**769 of the 971 unverifiable rows gained a verdict and 767 AGREE — 99.7% on
the newly-checkable set**, from two completely independent derivations. **The
scraped coefficients are safe to ingest.**

✅ **The widened `--with-dbc` run is DONE** (owner, 2026-08-06, via the new
double-click `run_dbc_extract.bat`). `extract_scope_missing_log_observed_ids`
is **resolved** — all five ids it named now decode (200818 → 1, 20424 → 35,
954923 → 140 +1.2/lvl, 907790 → 65, 18652 → 30). ⚠ None carries a
`spell_scaling` row: the client supplies **magnitudes, never coefficients**.
That division of labour is now the settled model — client for flats, scrape
for coefficients.

### ✅ DONE 2026-08-06 (the audit-gated ingest session) — items 1 and the gate

1. ~~**Ingest the scrape**~~ **DONE.** 3,446 coefficients across 1,617 spells at
   `source='db_ascension_gg_scraped'`, verdicts **recomputed against the live
   extract** (2,692 agree / 8 disagree, reproducing the audit exactly).
   ⚠ **Correction to this line as written:** it said `unverifiable` rows *"land
   at a weaker confidence"*, which contradicted the 3b handoff's *"unverifiable
   stays out"*. **Settled: they stay OUT.** No check digit means no basis for
   trust, and `spell_scaling` has no confidence column — the source string *is*
   the provenance. They remain in the committed ndjson and are promoted for
   free when an extract decodes their flat, which is what happened to 767.
   🚨 **And the second half of this line was wrong on its facts: the ingest was
   NEVER going to move magnitude coverage, and it did not — still a median 37%.**
   Coverage is gated on *magnitudes*, and the settled division of labour is that
   the **client** supplies those; a coefficient source can only make abilities we
   already model more accurate. It did exactly that: the gate went **4 of 41 →
   5 of 41**, qualified **1 → 2**. See the new finding below for where the
   coverage bottleneck actually is.
### 🚨 THE COVERAGE BOTTLENECK IS UNREACHABLE IDS, NOT MISSING NUMBERS

Measured immediately after the ingest, over the **88 demand-ranked unmodelled
abilities** the gate itself names:

- **83 of 88 already have a magnitude**, and **51 now have a coefficient**
  (50 of them from this ingest). **The numbers are not the bottleneck.**
- **All 88 are OUT OF CATALOG** — not one is a card the sim could press.
- **57 of 88 have no card AND no incoming trigger edge**, so no route the sim
  walks reaches them at all.

Worked case: the log reports Devour Mind damage under **287865**, while the sim
presses catalog card **285133** whose bounded walk reaches sibling **287860**.
The two siblings hold **identical decoded magnitudes and identical scraped
coefficients** (SP 0.08 / AP 0.055) — but only 287860 has a trigger edge, so
287865 scores as unmodelled. `20467` (the judgement damage spell the seal
selects) and `25902` (Holy Shock's damage sub-spell, which already carries a
seeded coefficient) are both in the unreachable 57.

**So coverage is an ATTRIBUTION/REACHABILITY problem, not a data-acquisition
one.** This generalises `2e`'s `dbc_only` finding — extracted-but-never-read
because the resolver only walked catalog routes — from magnitudes to the whole
routing layer. Open question
`unmodelled_damage_is_unreachable_ids_not_missing_numbers`.
🛑 **Do not close it by matching ids on name or by numeric proximity** — 287860
vs 287865 is exactly the shape rule 5 forbids. The join has to be mechanical.

### 🔴 FIRST ACTIONS NEXT SESSION

2. **Implement damage-CONVERSION mechanics** (Righteous Vengeance's
   30%-of-crit-damage class, 9 characters in the gate). We already hold the
   fact; the sim cannot express it. **No data needed** — pure sim work.
3. **Model pets** — owner decision 2026-08-06. 10% of the cohort's real damage,
   currently scored as zero, which quietly biases the corpus against
   pet-carrying builds.
4. **The owner's in-game capture** — `primer/NEXT_CAPTURE.md`, gated on the
   server restart. 🚨 **200818 SURVIVED the `--with-dbc` run**: the client
   decodes it to a flat of **1**, matching the site's `Value: 1`. Two
   independent sources agreeing on a nominal 1 confirms its damage is
   enchant-delivered and lives in `SpellItemEnchantment.dbc`, still
   unextracted. Its live tooltip stays the one genuine owner-only ask, and is
   still 25.1% of the owner's buffed damage.
5. ⚠ **`BEFORE_3B` §3's two "blocked" questions are already answered** — the
   `WoWCombatLog` naming convention and `ReloadUI()` availability were both
   resolved 2026-08-04 and are written up in `PHASE_3_builds_repo.md` T5/T6.
   Doc drift, not a blocker; do not re-ask the owner.

### Owner decisions, 2026-08-06 (consolidation review)

| Decision | Call |
|---|---|
| db.ascension.gg scraper | **Build it** — polite, cross-validated, demand-scoped, resumable |
| Pets in the sim | **Model them** |
| Phase 3 exit criterion | **Keep ±20%, report coverage beside it** — do not move a gate after seeing its number |

### Decisions taken 2026-08-06 (the audit-gated ingest session)

| Decision | Call |
|---|---|
| `unverifiable` rows in `spell_scaling` | **OUT**, not "weaker confidence" — settles the PROGRESS-vs-handoff contradiction |
| Bulk scrape provenance | **Its own source string** `db_ascension_gg_scraped`; the hand-curated anchor partition is untouched |
| Phase 3 exit | **±20% unchanged, plus a ≥3-qualified rider at ≥50% coverage** — stamped *before* the re-run |
| The site's 329 trigger edges | **All 329 were already carried by the client's `EffectTriggerSpell`; 0 new.** Not a failure — two independent sources agreeing on the whole trigger graph. The client wins any collision by insert order. |

---

## Superseded: the 3b pre-flight position

**✅ 3B PRE-FLIGHT IS DONE (2026-08-06, from `BEFORE_3B.md`).** §1 audit
remediations landed (reproducibility framing + per-report `tier2_manifest.json`
+ INDEX_GUIDE v17 + the lag-0 retraction row), §2 green (rebuild 20 steps,
purity 0/46, all sim-engine checks incl. 3 new buff-layer checks), and §0.3 —
the derived buff layer — is BUILT and run. Session record:
`primer/Session_2026-08-06_3b_preflight.md`. **3b proper has not started.**

### 🔴 FIRST ACTIONS NEXT SESSION (3b)

1. **The consolidated one-session dummy protocol is written and is THE ask:**
   `primer/NEXT_CAPTURE.md` (top section, 2026-08-06). Six windows + a hover
   list cover ALL owner-gated items at once — the #200295 re-test, the PBL ×
   Lightbound Cleave discriminator, the 200818 tooltip, Siphon Health/Swift
   Retribution, the log-file convention, ReloadUI, the 1.30× melee-haste
   display, seal rate-vs-PPM, and the imbue re-measure. 🛑 **Gated on the
   server restart**: checked live 2026-08-06 morning, the 08-04/08-05
   changelog entries still carry `[Pending Restart]` and the tracker is
   login-gated — the owner confirms #200295's status logged in, or waits for
   the daily crawl to show the tag flip. Build doc §2/§11 revert stays
   conditional on the re-test, not the tracker status.

### 🚨 The calibration gate is STILL NOT MET — and the buff hypothesis is now measured

> ⚠ **Superseded 2026-08-06 by the 3b session above: the gate now reads 4 of
> 41.** The buff finding below stands unchanged and was the correct call — what
> it could not see was that the sim was simming every candidate with no weapon.
> Kept as the historical record, not as the current position.

`py tools/audit/calibrate_crawled.py --limit 120 --max-lag-hours 0`
→ **0 of 41** level-60 crawled characters within ±20%
(`data/derived/calibration_crawled.md`). Criterion is ≥3. Strict lag-0.

**The buff layer is no longer the explanation.** §0.3 built it properly —
`core/builds/group_buffs.py` derives each candidate's buff set from the boards
of participants in the same capture scope (card-id match, never name; lower
bound, nothing fitted), and `compute_stats` now applies the full measured
arithmetic (Kings ×1.10 last, +31 Int/+27 raw SP, +62 Str/+62 Agi, +14 AP,
imbue per weapon, PoI doubling on buff SP). Result: 3–5 buffs derive per
candidate and move sim DPS by **+0% to +11%** — against misses of −35% to
−99%. 3a's ranked-cause #1 ("buffs, order ×2.35") is **largely falsified as a
stat-side mechanism**: the owner's own ×2.35 buffed gap routes mostly through
things the sim lacks per ability (his buffed parse is 25.1% unmodelled 200818
damage, and buffed SP feeds coefficients that out-of-catalog spells cannot
carry — 2e's missing-coefficient mechanism, which the crawl generalises to
every class's kit). Open question `crawled_gate_residual_after_buff_layer`
carries the revised candidate ranking: per-kit magnitude/coefficient coverage,
unmodelled proc/trigger/imbue damage, APL realism for unknown kits, CP
finishers at 0 CP, hybrid mitigation.

🆕 The one positive delta is its own bug: Mutaforma sims at **89,340 DPS**
(+3,619%) off an attributed Absolute Zero periodic — open question
`sim_magnitude_explosion_absolute_zero` (285148).

🛑 **Do not close this by fitting a constant.** Same rule as 2c's demoted 1.31
and 2e's deliberately-unseeded Holy residual. The buff layer was built and
measured rather than fitted, and its measured insufficiency is the finding.

🚨 **A method lesson from building this gate, worth more than its number.**
Against the mid-backfill corpus the strict lag-0 filter left **one** character,
and that was written up as structural ("exact-join captures skew toward
levellers") and worked around by loosening the threshold to 336h. It was
**small-sample, not structure** — after the backfill the same strict filter
yields **41**. Generalised: *a filter that starves on a partial corpus is not
evidence that the filter is too strict.* Re-run on more data before loosening a
constraint. ⚠ Also: **level is read, never assumed** — a first version
hardcoded 60 and simmed a level-49 parse against level-60 magnitudes, which is
`1x`'s retracted pooled-crawl error, re-committed and caught.

### What `3a` established (details in the session record)

- 🆕 **`data/derived/builds.db` exists** (gitignored, built by
  `ingest/logs_gg/build_builds_db.py`): **4,069 characters, 412
  snapshots, 19,684 cards, 6,896 gear rows, 5,455 encounters, 307,442 ability
  rows, 877,850 avoidance rows.** ⚠ **Those figures require TIER-2 crawl data
  (local or re-fetched per report via `crawl_ascensionlogs.py
  --recrawl-report <id>`) and are NOT committed-reproducible** — a clean rebuild
  from committed source alone yields 390 characters and 0
  ability/avoidance/performance rows, because tier-2 is gitignored by design.
  Auditable without a re-fetch via the committed per-report
  `tier2_manifest.json` in each `data/source/crawl/<date>/` folder
  (`tools/scrapers/build_tier2_manifest.py`, added post-3a-audit 2026-08-06).
  Card resolution runs at REBUILD time —
  3,222/3,245 (entry_id, rank) pairs resolve, 23 ambiguous left NULL.
  ✅ Reproduces HftH's zero-avoidance on **17,781** pooled hits (3.6× the
  sample behind the confirmed fact).
  (The uncapped backfill completed during `3a`: 94 min, 6,146 requests, 0
  retries, 50 new reports, 275 armory records, 390 characters known.)
- 🚨 **`ItemStat.dbc` does NOT carry item stat values** — probed and disproved
  against 1,198 ground-truth items (6 exact matches in 567 overlaps; no field
  above 9.2%). The owner's chosen "client DBC first" route is a dead end for
  stats. `items` (**2,384; 1,792 with stats**) is built from `snapshot_gear`
  instead, stamped `provenance='crawl_resolved_bisbeard'` — so agreement with
  BisBeard checks our WEIGHTS, not our ITEMS.
- 🚨 **Pooled crit-table inference cannot use the phase doc's regression**:
  per-parse stats do not exist and hit/crit are unified in GEAR, so gear rating
  cannot separate the tables even in principle. Replaced with a
  **within-character anchor comparison** (buff state and gear cancel in the
  pair). `infer_coefficient` **refuses** per spell and records the refusal.
- 🆕 **Inference is staging-only** (`inference_findings`, 74 proposals / 70
  refusals over the top-50 abilities) — nothing auto-seeds `spell_mechanics`.
  Free finding: **immunity ≠ resist roll** — 8 enemy units full-resisted every
  HftH pulse while landing zero; pooling those would fake a partial-resist rate.
- 🆕 **Crawler re-verification** (T8): 40 known-but-not-seen-today characters
  per run, oldest first, so a respec-then-stop-parsing character can no longer
  stay frozen. All-roles was already done since 0b.
- 🟡 **Holy Shock SP 0.40 seeded PROVISIONAL** on 25902 under
  `source='ascension_measured_provisional'`; the open question stays live at
  `in_progress` because 0.40 is back-solved from the parses it would be checked
  against.

### Still blocked on the owner

| Item | Blocking |
|---|---|
| Tracker #200295 re-test + PBL × LC discriminator (needs in game) | Build doc §2/§11 revert |
| Consecrated Holy Weapon (200818) live tooltip | 25.1% of buffed damage, unmodelled |
| Identify Siphon Health (18652) / Swift Retribution (853484) | Passive-layer completeness |
| *(optional)* bug-DB read access via the owner's browser session | Repeatable bug lookups |

---

## Superseded: `2e`'s position

**✅ SESSION `2e` IS DONE (2026-08-05, late night).** T1–T4 and T6–T11 complete;
T5 (bug-DB browser) and T3b's detector half deferred with recorded reasons.
Session record: `primer/Session_2026-08-05_2e_poi_calibration.md`. Calibration
report: `predictions/calib_2026-08-05_2e_poi.md`. Rebuild green (20 steps),
purity 0/41, all engine checks pass (count is run-dependent — stop quoting a
fixed N).

**Next session: post-restart re-tests, then `3a`.**

### 🔴 FIRST ACTIONS NEXT SESSION

1. **Re-test tracker #200295 after the server restart** — it was FIXED hours
   after submission (`[Pending Restart]`, owner will test 2026-08-06). Run BOTH:
   Hammerdin procs from Judgement/Holy Shock (confirms the fix) and the
   **PBL × Lightbound Cleave discriminator** (a Hammerdin-only fix and a general
   engine fix look identical if you only re-test Hammerdin). Protocol:
   `bugs/bug_hammerdin-trigger-set.md`. Build doc §2/§11 revert is conditional
   on the re-test, not the tracker status.
2. **Ask for the Consecrated Holy Weapon (200818) live tooltip** — measured at
   **25.1% of buffed damage** and absent from the DBC extract entirely; the top
   single ask in the project.

### What `2e` established (headlines — details in the session record)

- ✅ **The Holystrike residual was the weapon input**: LC 1.00× / Dawnreaver
  0.99× with the first same-session stat block in project history.
  `holy_holystrike_ratio_weapon_input_confound` demonstrated.
- 🚨 **The Holy residual is TWO mechanisms** (`holy_residual_two_mechanisms`):
  out-of-catalog spells whose coefficients CANNOT exist in our data (~2.2×) vs
  a real ~1.24× on coefficient-bearing spells — plus a component that grows with
  buffs. Never collapse into one multiplier. D4 gate stays shut.
- 🚨 **`dbc_only`**: 11,857 extracted-but-never-decoded spells now carry
  magnitudes. Still missing entirely (~38% of buffed damage): 200818, 20424,
  954923, 907790, 18652 — extract-scope fix specified in
  `extract_scope_missing_log_observed_ids`.
- 🆕 **Buff layer measured to arithmetic** (`core/sim/buffs.py`); **BonusHealing
  reads undoubled SP** — standing instrument. ❌ Retracted: `2d`'s "seal riders
  fire on autos only" (isolation-window over-generalisation; ~0.25/melee event
  measured).
- 🆕 Glancing vs +3 = **32.6% measured** (retail 24% rejected, 3.1σ); melee crit
  suppression **consistent with zero** (first constraint, not conclusive).
- ✅ **1,555 DPS unbuffed / 3,650 buffed** — the owner's ~3,600, finally
  measured against a known stat block. Calibration gate: 3 of 8 in tolerance
  (was 1 of 7), all weapon abilities within ±1%, every miss mechanism-named.

### Still blocked on the owner

| Item | Blocking |
|---|---|
| `holy_shock_bonus_coefficient_0429` — seed measured ~0.40 or hold for a stating tooltip? | Holy Shock's modelled damage |
| ~~Commit the raw combat logs?~~ ✅ **Resolved 2026-08-05: committed as reference** (owner decision). May be pruned later if unneeded for a while — if pruning, re-derive nothing from them first: T3b's duty-cycle re-test and the seal PPM question both consume the raw per-hit data | — |
| Consecrated Holy Weapon (200818) live tooltip | 25.1% of buffed damage, unmodelled |
| *(optional)* bug-DB read access via the owner's browser session (`2e` T5, deferred) | Repeatable bug-database lookups |

---

## Superseded: `2e`'s original position

**Was: next session `2e` — read `primer/PHASE_2E_buffs_and_carryover.md`.**
`3a` was deferred behind it: `2d` spent its budget on an owner-in-the-loop
testing run that produced three premise-invalidating findings, and left every
code task untouched. `2e` carried them plus what `2d` created.

**⚠ SESSION `2d` IS PARTIAL (2026-08-05).** T0 (in-game list) and T1 (capture
bundle) delivered and far exceeded; **T2–T10 not started.** Session record:
`primer/Session_2026-08-05_2d_capture_and_bugs.md`. Rebuild green (20 steps),
purity 0/39. Code changed: `core/builds/stats.py` only — a correctness fix.

### 🛑 Read before touching any calibration data: Path of Duality is broken

Community-reported (multiple independent players) and corroborated by our own
captures — `bugs/bug_path-of-duality-broken.md`, spell `129243`:

- **AP bonus cycles ON/OFF every ~10–15 s, indefinitely** (a player watched
  832↔1128; we read 174↔307). **So every historical calibration log had a
  per-hit input oscillating mid-parse** — a candidate cause of part of `2b`'s
  1.41× between-session spread.
- **SP grant reduced to a flat ~+19** (independently reported as "a difference of
  19 Spellpower"; we measured +19).
- Weapon-type passives (2H +6% damage / 1H +10% haste) **dead** — `stats.py` had
  been applying the 6%.

**Owner decisions:** ignore PoD parses for absolute calibration; **do not
recommend PoD**; he plays **Path of Intelligence** now; **track bug fixes** — the
watch list with changelog keywords is in `bugs/README.md`.
**What survives:** within-log ratios between abilities sharing input dependence
(pair ratios, the Holy Shock coefficient), all proc-rate results, crit tables.

### Three retractions `2d` forced

- ❌ **"Duality applies a 1.895× SP amp"** → **no amplifier, flat +19.** The ×2.0
  doubling belongs to **Path of Intelligence** (its tooltip says so); the project
  attributed it to the wrong path for two versions. The 2026-08-04 test used
  rapid path toggling and cannot be repaired retrospectively.
- ❌ **"Duality Str→AP at 0.548×"** → an **OFF-phase reading** of the cycling bug.
  When it applies, the tooltip's 100% is exact. *Two agreeing measurements of an
  oscillating quantity are two samples of one phase, not a rate.*
- ❌ **"Hit and crit rating are unified"** (build doc §10) → unified in **gear**
  only; Duality's cross-crit conversions grant **rating** (~3.4 stat per rating
  point) and split them (238 melee / 187 spell).

### 🚨 Hammerdin does not proc from Judgement or Holy Shock

Measured over 10 minutes on a dummy: Dawnreaver 15–17 procs / 119 casts (~20%,
consistent), **Holy Shock 1 / 78, Judgement 0 / 51** — combined 1 where ~26 is
predicted, **p < 10⁻⁹**. The −4 s cooldown reduction *does* work per proc, and
there is no ICD. Submitted as
[tracker #200295](https://ascension.gg/bugtracker/view/200295).
**Consequence: build doc §2's class-tag table and §11's rotation priority are
both wrong — Dawnreaver is the engine driver, not Judgement/Holy Shock.**
Suspected mechanism (a guess): trigger-delivered damage is proc-blind, which
would affect **every** "damaging X abilities" engine — open question
`hammerdin_trigger_set_excludes_trigger_delivered_damage`.

### Also settled in `2d`

- ✅ **Lightbound Cleave feeds NOTHING** — zero Hammerdin, zero PBL (while a
  control window proved the engine live), Seal of Command riders on autos only.
  Closes `lightbound_cleave_post_patch_procs`. **That inertness is what makes it
  portable** → the owner-proposed **Cleave Kit** (Package 4 in
  `synergy_portable-multiplier-packages.md`), now a `PHASE_4` regression target.
- ✅ **Holy Shock SP coefficient ≈ 0.40** (n=40 unbuffed, weapon-free pair) —
  still unseeded pending an owner decision.
- ✅ **First direct pulse count:** 17.9 HftH per HoJ cast vs 20–21 modelled.
- 🆕 **Dummy identity is a calibration variable** — level-scaling vs fixed-63
  dummies differ 10–18% at identical stats. Put it in capture metadata.
- 🆕 **Weapon imbues grant STATS** — Consecrated Weapon +172 Holy SP / ~+61 AP,
  school-scoped. An "unbuffed" baseline isn't clean unless the imbue is absent.
- ✅ Talent model validated exactly: Twin Disciplines' unrecorded third effect
  (+5% Holy crit) makes the stack 15 points; the sheet reads 15.00.
- ✅ The `2b` "Judgement resolves to no card" gap: the **seal** selects the
  judgement spell, so pressed card ≠ damaging id (20467).

**Capture data:** `data/source/captures/2026-08-05_elric_2d/` (unbuffed + buffed
exports, three relog-separated path captures, board ids, README with provenance).

---

## Superseded: `3a`'s original position

**⚠ It also inherits Phase 2's ≥3-character calibration criterion (see below).**

**✅ SESSION `2c` IS DONE (2026-08-05). PHASE 2 IS COMPLETE.** Gates G0–G4 plus
T4b (talents), T8 (calibration), T9 (prediction ledger), T10 (cache), T11
(diff/report). Session record:
`primer/Session_2026-08-05_2c_gates_and_talents.md`. Validation:
`check_sim_engine.py` **38 checks**, all pass; purity 0 violations; 20-step
rebuild green.

**Four things `2b` believed were wrong, and three were our own tooling:**

- ✅ **`rank_siblings_inherit_no_hidden_refs` RESOLVED.** A sibling's sub-spells
  are named in its own DBC description — but had never been EXTRACTED, because
  `spell_dbc_raw` was scoped to catalog + **export** hidden_refs + siblings.
  Needed `--with-dbc` (+797 ids). **Holy Shock R4 = 562–608.**
  🚨 **Consequence: `paladin_optimal` 848 now BEATS `paladin_observed` 823 —
  build doc §11's central rotation conclusion is restored.**
- 🛑 **The 1.31 Holy÷Holystrike ratio is CONFOUNDED and demoted — do not fit
  against it.** Holystrike is 86–100% weapon damage and Holy is 0%, so the stale
  weapon input (from a different session's parse) passes into the ratio ~1:1.
  **Replaced by WEAPON-FREE PAIR RATIOS, which need no weapon input at all:**
  HftH ÷ HoJ-tick predicted **1.718**, observed within **3.2%** across 4 logs;
  Dawnreaver ÷ Whirling Light predicted **0.769**, within **6.4%** across 3.
  Those are the targets a talent model must reproduce.
- ✅ **Consecration and Exorcism were never calibration outliers.**
  `calibrate_vs_log.py` matched by NAME; the logged spells are **270768** and
  **270767** (Purification By Light's own out-of-catalog versions), not the
  catalog's 26573/879. Our own never-match-by-name rule, never applied to our own
  tools. Fixed by keying on the log's `spellId`. **The Holy group is now n=3,
  1.97–2.15, with no outlier.**
- ✅ **The effect-type-121 double-count theory is wrong twice.** The three
  Holystrike anchors do NOT carry 121 (only Dawn Strike does), so `2b`'s
  base-formula validation **stands**; and the resolver never counted 121 as a
  swing anyway. Dawn Strike is reframed as a TALENT question — same formula as
  Lightbound Cleave, different family, 25% less damage in game.

**T4b — talents now contribute, and two build-doc claims need correcting:**

- ⚠ **`EffectSpellClassMask` had to be added to the extract** — parsed since v9
  and never written out, which is why no earlier session could model amplifiers.
- ✅ **Improved Cleave's class mask is byte-identical to Lightbound Cleave's**
  (family 4, `[4194304,0,0]`) → **×2.20**, proved from numeric fields. It does
  NOT reach Whirling Light, Dawnreaver or Dawn Strike.
- 🚨 **Holy Power and Holy Specialization are CRIT talents (aura 71, +5% Holy
  crit each), not damage multipliers.** The build doc calls them part of a
  "stacked Holy multiplier chain". The whole modelled damage layer is **×1.155**.
- **Unknown auras are named, never assumed inert:** 6 talents use auras outside
  stock 3.3.5 (231/333/122/136), 4 are server-side scripts (`SPELL_AURA_DUMMY`).

**T8 — tolerance recorded BEFORE calibrating** (`predictions/CALIBRATION_TOLERANCE.md`,
±20% aggregate / ±25% per-ability). **Reported result: 1 of 7 abilities within
tolerance.** The misses group by SCHOOL (Holy ~1.86×, Holystrike ~1.37×) — an
unmodelled school amplifier *or* an unmodelled buff. 🛑 Not to be closed by
fitting a constant.

**📅 PHASE BOUNDARY CHANGE:** T8's **"reproduces ≥3 real characters" criterion
MOVES to 3a**, because simulating a crawled character needs gear and gear is
Phase 3 T4's `items` table. Phase 2 exits without it, deliberately and on record.

**Bug introduced and caught this session:** `resolve_numeric_formulas.py` ran
`DELETE FROM spell_effect_values` unscoped, destroying the trigger rows
`relationships.py` owns — invisible in the rebuild, visible only on the
standalone re-run its docstring invites, and it zeroed Hammer from the Heavens.
Now scoped. Also fixed repo-wide: **piped/redirected stdout no longer crashes**
on Windows (`config.ensure_utf8_stdout()`, 12 entry points) — open since
INDEX_GUIDE v10.

**🔴 FIRST ACTION NEXT SESSION: ask the owner for the capture bundle he agreed
to produce — see `primer/NEXT_CAPTURE.md`.** An unbuffed stat export
(`addons/AscensionCrafterExport/`) taken in the **same session** as two dungeon
logs, plus a bounded list of live tooltips. The stat block is the binding item:
it un-confounds the absolute calibration, settles
`elric_active_path_and_duality_ap_anomaly`, and makes the two logs able to test
whether the ~1.86 Holy / ~1.37 Holystrike residual is structural or buff state.
🛑 Stats and logs must be the same session — a mismatch is exactly the King
Gordok error that forced `2c` to demote the headline ratio.

---

## Superseded: what `2c` was told to inherit from `2b`

Kept because several of these numbers are still quoted in older docs, and each
is now wrong for a reason worth knowing.

**✅ SESSION `2b` IS DONE (2026-08-05).** T5 (three tiers + APL grammar + apl_gen),
T6 (uncertainty from a sim-layer policy table), T7 cheap half (stat weights, path
comparison). The sim produces its first end-to-end number. Session record:
`primer/Session_2026-08-05_2b_sim_tiers.md`. Validation: `check_sim_engine.py` is
**30 checks** (was 16), all pass; purity 0/34; 19-step rebuild green.

**What `2c` inherited from `2b` — ⚠ four of these are now SUPERSEDED, see the
`2c` block above before using any number here:**

- 🛑 **FIRST ITEM: open question `rank_siblings_inherit_no_hidden_refs`.** It
  blocks the rotation question. A rank sibling inherits no `hidden_refs` (that
  column is parsed from the export, which siblings are by definition absent
  from), so a sibling whose own record is a DUMMY loses its sub-spell chain.
  **Holy Shock R4 (20930) is exactly that and resolves to 0 damage** — which makes
  `paladin_optimal` (602) score BELOW `paladin_observed` (659), inverting build doc
  §11's central conclusion. The sim names the zero-damage ability loudly and
  `check_sim_engine` asserts that it does, so it cannot be quoted as a result.
- ✅ **The sim is CALIBRATED against a real parse** (Elric's own
  `2026-08-04-20.07.21 WoWCombatLog.txt`, 60,427 events). Outcome recorded in
  `predictions/pred_2026-08-05_elric_paladin.md`, tool
  `tools/audit/calibrate_vs_log.py` (verifies field alignment against three
  doc-confirmed facts and REFUSES to report if they fail). **Within any one log a
  school's abilities agree to ~±0.03 — and since HftH and HoJ's tick are
  structurally unrelated formulas, that agreement validates BOTH base formulas.**
  **Pulse delivery confirmed a second time, independently: 259 HftH hits / 60 HoJ
  ticks = 4.32 against a predicted 4.00.**
- 🛑 **Do NOT fit one talent multiplier from pooled logs.** The absolute
  multiplier swings **1.41× between sessions** (Holy 1.76 / 1.90 / 1.99 / 2.48)
  — that is buff and gear state, not talents. **The durable quantity is the
  Holy÷Holystrike RATIO, 1.31 ± 0.03 across all four logs**, because buff state
  cancels in a ratio. That ratio is what a correct talent model must reproduce.
- ⚠ **Two calibration outliers must be settled BEFORE fitting talents**:
  **Consecration ~4×** (suspect missing component or wrong rank) and **Dawn
  Strike**, which misses its school group in ALL FOUR logs, always ~0.3 low — a
  reproducing per-ability bias meaning its sim base is **~25–30% too high**.
  Suspect effect type 121 (normalized weapon) being counted alongside type 31
  (weapon-percent); if so it affects every ability carrying type 121. Open
  questions `consecration_and_dawn_strike_calibration_outliers` and
  `dawn_strike_sim_base_is_systematically_too_high`.
- 🚨 **Talent modelling is now the single largest error source**, ahead of
  everything else combined. **Owner decision 2026-08-05: general extractor for
  coverage + hand-seed the ~24 slotted talents.** A correct model should
  *reproduce* ~1.76 and ~1.40 from the actual cards — those are targets, not
  values to hardcode. Build the extractor on
  **auras 107/108 (`ADD_FLAT_MODIFIER`/`ADD_PCT_MODIFIER`) read together with
  `EffectMiscValue` (the SpellModOp) and `EffectSpellClassMask`, from NUMERIC
  fields** — 2b showed Improved Cleave's tooltip understates its own scope
  (it names the flat; the op is `SPELLMOD_ALL_EFFECTS`), so tooltip parsing is
  the wrong foundation.
- ✅ **Phase 1 baseline re-capture is SCHEDULED, not a reminder** (owner decision
  2026-08-05). Task `AscensionCrafter Phase1 Baseline` fires **2026-08-07 20:00**
  with `StartWhenAvailable`, so a powered-off PC catches up at next boot instead
  of silently skipping. Registered by
  `tools/scheduling/register_phase1_baseline.ps1`; full rationale in
  `SCHEDULING.md`. It overwrites `data/source/crawl/baseline_phase1/` in place,
  then commits **that folder only** and pushes. **Remove it after the flip** with
  the script's `-Unregister` switch — it deliberately does not self-delete. The sim reads ~600 DPS against the owner's reported
  ~3,600 — pre-registered with its causes ranked in
  `predictions/pred_2026-08-05_elric_paladin.md`.
- ⚠ **Do NOT adopt the sim's stat weights.** They disagree sharply with the build
  doc's empirical ones (sim: weapon_damage 25, hit 17, crit 6.1; doc: crit 2.00
  best, AP 1.00). The disagreement is a diagnostic, not a result.
- Remaining named gaps: seals scored per cast not per swing; auto-attacks
  unmodelled; `Judgement` resolves to no current-pool card; Righteous Vengeance's
  30% crit DoT unmodelled.
- `sensitivity()` output is ready to populate `open_questions.variance_contribution`.

**✅ SESSION `2a` IS DONE (2026-08-05).** T1–T4: `core/sim/combat_engine.py` (gt-table
rating conversions, anchor-validated; attack tables; no silent defaults),
`core/sim/content.py` (8 presets, raid durations derived from scouted ZG data),
`core/sim/ability_model.py` (resolver-path-only `ResolvedAbility`, full term_type
vocabulary, outliers excluded), `core/builds/spec.py`+`stats.py` (BuildSpec ranks-
mandatory; compute_stats sheet/component modes, Duality parameterised at measured
values). Validation: `py tools/audit/check_sim_engine.py` (16 checks incl. the
mean(roll_hit×100k)≈expected_hit guard). Session record:
`primer/Session_2026-08-05_2a_sim_foundation.md`.

**What `2b` inherits from `2a`:**

- 🚨 **First item: finish `trigger_attributed_coefficients_not_in_spell_scaling`**
  (in_progress). The attribution DECISION is made (owner, 2026-08-05): coefficients
  live on the trigger TARGET — `seed_hand_coefficients.py` (new 19th rebuild step)
  seeds HftH's 9.1% SP/AP on 282987 with tier-3 provenance. **What 2b implements:**
  the ability model pulls `spell_scaling` rows per component `source_spell_id`
  (bounded, single-path, confidence=inferred when trigger-reached — 1b's walk
  rules). Until that lands the rows are queryable but a card's profile still
  serves flat-only (~45% understatement on HftH stands).
- **Trigger-hop magnitudes ARE summed into expected_hit** (flagged
  `calibration_anchor=False`, listed in `triggered_components`) — see the 2a plan-
  changes row for why the "never anchor" rule does not mean "exclude".
- `expected_hit` is per-EVENT (hit or tick): direct-vs-DoT splitting, CP
  parameterisation, hybrid-school mitigation split, AoE totals-at-N are all
  deliberate 2a gaps with warnings — T5's tiers own them.
- New open question `melee_crit_suppression_vs_higher_level` — the engine warns
  instead of modelling it; a big white-swing parse settles it.

**✅ SESSION `1c` IS DONE (2026-08-05). PHASE 1 IS COMPLETE — all exit criteria checked
and recorded in `PHASE_1_spell_database.md`.** Session record:
`primer/Session_2026-08-05_1c_epistemics_tooling.md`.

**What `2a` inherits from `1c`:**

- **`py cli/rebuild.py` is now 18 steps** (~90s): `seed_epistemics.py` (T6) runs after
  `seed_confirmed.py`, and `tools/audit/audit_gaps.py` (T8) runs LAST, writing
  `data/derived/audit_report.md` + a one-line summary every rebuild.
- **T6 epistemics live**: `open_questions` (28 rows: 23 open / 1 in-progress / 4
  resolved-as-history, keyed by stable `slug`), `retractions` (24), `fact_spell_links`
  (410: 64 inferred id-based, 346 needs_review name-based — never auto-approved).
  `confirmed_facts` carries provenance columns (evidence_ref/realm/season stamped;
  verified_at_patch NULL for pre-tracking backfill). **Both seed files are append-only
  source of truth — resolving a question means editing `seed_epistemics.py`.**
- **T7 `spell_profile()`** (`core/spells/profile.py`, `cli/profile.py`): rank gaps and
  conflicts surfaced first; duplicate names refuse with a candidate list; out-of-catalog
  ids fall back to `dbc_only` (282987 profiles); `mode='fast'` for sim loops — **this is
  the resolver 2a's ability model should call, not raw tables.**
- **T8 auto-debugger** (12 sweeps incl. the 2026-08-08 phase boundary, which fires in
  3 days) + **test-protocol generator** (7 hand-written protocols; card-destruction
  protocols are REFUSED structurally; <3-point discriminators emit "find another test").
- **T9**: `search_spells(conn, **filters)` + `py cli/browse.py` (Datasette, 12 canned
  queries; datasette now pinned in requirements.txt). **T10**: `volatility_score()` —
  Darkmoon-only strict (owner decision 2026-08-05), report-only, carries a `data_thin`
  honesty block (12-day tagged window today).
- **The compound-form extraction gap is CLOSED**: `spell_scaling` 1,058 → 1,348 rows
  (625 → 737 spells), new term types (`SPFR`/`SPH`/…/`BH`; BH routes to the healing
  block). ⚠ 2a note: `spell_scaling.term_type` is no longer only SP/AP/RAP/WEAPON.
- **Amplifier queue pre-classified, owner-approval gated** (`reviews/amplifier_review.md`,
  243 rows: 58 verbatim / 12 check-stat / 16 school / 105 proposed-exclude / 52
  unclassified). Nothing enters the graph until the owner approves a batch there.
- **New open question**: `hidden_formula_outlier_coefficients` — 4 cached
  `dbc_hidden_formula` coefficients look like swallowed multipliers (277595 RAP/SP 6.0);
  the widened extractor fixes them at the next `--with-dbc` re-extraction.
- 1c deviations from the phase doc are in `PHASE_1_spell_database.md`'s progress block.

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
| **1c** | Facts, `spell_profile()`, auto-debugger, browsing, volatility | ✅ done | `Session_2026-08-05_1c_epistemics_tooling.md` | **Phase 1 complete, exit criteria checked.** T6–T10 + compound-form gap closed (+290 scaling rows) + amplifier queue pre-classified (approval-gated per owner decision) + conflict sweep buckets slot collisions separately. Two more owner decisions implemented: Darkmoon-only volatility, Datasette pinned. Rebuild is 18 steps |
| **2a** | Combat engine, content profiles, ability model, build spec | ✅ done | `Session_2026-08-05_2a_sim_foundation.md` | T1–T4 + `check_sim_engine.py` (16 checks). Found the HftH coefficient queryability gap; 2 open questions filed |
| **2b** | Three sim tiers, uncertainty, stat weights | ✅ done | `Session_2026-08-05_2b_sim_tiers.md` | T5+T6+T7-cheap-half. **4 data bugs found, all silently zeroing**: trigger coefficients unserved, rank siblings had NO magnitudes (686 cards), weapon-percent read as flat, fast_sim allocation order. 🚨 Structural finding: trigger-reached damage can be delivered by a periodic-trigger aura (HoJ fires HftH 20x/cast, validated 3.81 vs predicted 4.00 over 20,823 pooled hits). 🔴 Improved Cleave reverted to bottom of the chase list |
| **2c** | Talent modelling, calibration, prediction ledger, cache, diff/report | ✅ done | `Session_2026-08-05_2c_gates_and_talents.md` | Phase 2 complete. Gates G0–G4 + T4b/T8–T11. Holy Shock R4 resolved; the 1.31 ratio demoted; talents modelled |
| **2d** | Capture bundle, in-game testing, bug findings | ⚠ partial | `Session_2026-08-05_2d_capture_and_bugs.md` | T0+T1 delivered and exceeded; **T2–T10 not started** → carried to `2e`. Three premise-invalidating findings (Duality broken, Hammerdin trigger set, LC engine-inert), 2 bugs filed / 1 submitted (#200295), 3 retractions, Cleave Kit written up |
| **2e** | Buff model, sim gaps, PoI recalibration, bug-fix watch, scorecard spec | ✅ done | `Session_2026-08-05_2e_poi_calibration.md` | T1–T4, T6–T11. Holystrike residual closed (weapon input); Holy residual split into 2 mechanisms; `dbc_only` +11,857 spells; buff layer measured; glancing 32.6%; watch sweeps live; kit rename; D3/D4 landed. T5 + detector deferred with reasons. **#200295 FIXED pending restart** |
| 3a | Crawl normalisation, inference, search, gear | ✅ done | `Session_2026-08-06_3a_builds_corpus.md` | T1–T4 + T8, plus the uncapped backfill (50 reports). `builds.db` built; inference is staging-only with an anchor-comparison crit method (the doc's regression is impossible — hit/crit unified in gear); `ItemStat.dbc` disproved as a stat source, items come from the crawl. 🚨 **Calibration gate NOT MET (0 of 41 at strict lag-0), 40/41 misses negative → unmodelled buffs** |
| 3b | Gear layer + decomposed calibration gate | 🟡 partial | `Session_2026-08-06_3b_gear_and_decomposition.md` | `PLAN_3B_UPDATE.md` §5's critical path only (owner scoping decision). 🎉 **Gate PASSES, 4 of 41 (was 0 of 41)** — on one missing input, **weapon damage is in no stat block**, nothing fitted. 🛑 Only 1 of the 4 also has ≥50% of its damage modelled; the rest pass by compensating error and the criterion was NOT redefined. Gear model corrected (difficulty lives in the item_id; name→stats banned). **Remaining: T5 addon, T6 log ingestion, T7 session-start hook, PLAN_3B §4 ceiling + §6 weight emitter** |
| 4 | Legos + Theorycrafter | ⬜ | — | Chunk as it goes |

Status values: ⬜ not started · 🟡 in progress · ✅ done · ⏸️ blocked

---

## Blocked on the user

Anything waiting on a 🛑 stop-point or a decision only the project owner can make. Clear entries as
they're answered.

| Item | Blocking | Asked on |
|---|---|---|
| **A Path of Intelligence capture bundle** (unbuffed export + 2 logs, relog before exporting, dummy identity + imbue state noted) | `2e` T3 — the recalibration. PoD parses are excluded by the bug advisory, so the existing bundle cannot serve absolute calibration | 2026-08-05 (`2e` T3) |
| **`holy_shock_bonus_coefficient_0429`** — seed the measured ~0.40, or wait for a tooltip that states a coefficient? | Holy Shock's modelled damage (3% of parse) | 2026-08-05 (open since `2c`) |
| Identify **Siphon Health (18652)** and **Swift Retribution (853484)** — hover in game | Completeness of the passive layer; small calibration residuals | 2026-08-05 (`2d`) |
| *(optional)* Bug-DB read access via the owner's browser session | `2e` T5 — repeatable bug-database lookups | 2026-08-05 (owner suggestion) |

**Delivered by the owner in `2d` and consumed:** the full capture bundle (stat
exports, three path captures, four dummy logs, Holy Shock R4 tooltip, 55-id
board), plus the Path-of-Duality bug-database excerpts that changed the session.

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
| 2026-08-06 (3b) | ✅ **The `--with-dbc` run landed: +834 spells, and 769 of 971 unverifiable coefficients resolved at 99.7% agreement** | Owner ran it via the new double-click `run_dbc_extract.bat`. `spell_dbc_raw` 16,566 → **17,400**; check digits 14,100 → **14,913**; the observed-id scope engaged as designed. Scrape verdicts moved **1,925 → 2,692 agree**, **971 → 202 unverifiable**, 6 → 8 disagree: of the 769 newly checkable, **767 agree**. Our client-decoded flats and db.ascension.gg's stated values come from completely independent routes, so agreement at that scale is real corroboration — **the scraped coefficients are safe to ingest**. `extract_scope_missing_log_observed_ids` **resolved**: all five named ids decode. ⚠ None carries a `spell_scaling` row — the client gives magnitudes, never coefficients, which is now the settled division of labour |
| 2026-08-06 (3b) | 🚨 **A code path only an OWNER-GATED run exercises can stay broken for sessions while everything reports green** | `export_ascension_extract_json` summed `len(v['rows'])` over every payload value including the `_extracted_at` **string** added in `2e` → `TypeError`. It fired **after** `write_text`, so both extracts were complete and valid and only the summary died — but the non-zero exit stopped the whole 20-step chain. Latent since `2e` because **nothing had run `--with-dbc` in between**, and the routine rebuild never touches that exporter, so 20/20 passing said nothing about it. **When a step is gated behind hardware, credentials or another person, its last SUCCESSFUL run is the real staleness clock — not the last commit that touched it.** Fixed by skipping `_`-prefixed keys, the convention `load_extract.py` already used |
| 2026-08-06 (3b) | ⚠ **A guard that cannot run must say so — never report the condition it failed to test** | `run_dbc_extract.bat`'s game-running check **failed OPEN**: if Git for Windows' `usrin` precedes `System32` on PATH, its Unix `find` shadows the Windows one, the check errors, and the script printed *"OK - game is closed"* without having checked. Caught in a dry run before the owner saw it; now uses absolute `System32` paths and warns explicitly when it cannot check. Same run also fixed a garbled log (`tee` does not exist in cmd; PowerShell 5.1's `Tee-Object` writes UTF-16 — precisely the file a failing user would send back) |
| 2026-08-06 (3b) | 🚨 **200818 SURVIVED the extract — the live-tooltip ask stands** | Consecrated Holy Weapon decodes to a flat of **1**, matching db.ascension.gg's `Value: 1`. Two independent sources agreeing on a nominal 1 confirms the damage is **not in its own record**: it is delivered through the weapon enchant, and `SpellItemEnchantment.dbc` is still unextracted. The run was expected to retire this ask and did the opposite. Still 25.1% of the owner's buffed damage. Separately **Ignite (12654) decodes to no flat at all**, which is what `sim_cannot_express_damage_conversion_mechanics` predicts for that family — a confirmation, not a gap |
| 2026-08-06 (3b) | 🆕 **db.ascension.gg is a systematised SOURCE now, and the widened `--with-dbc` run leaves the critical path** | A consolidation review classified every unmodelled damage row: **42.9%** absent from our extract, **41.1%** magnitude-but-no-coefficient, 9.1% autos, **5.5%** a real resolver/APL gap. The client **structurally cannot** fix the 41% — Ascension keeps applied coefficients in tooltip text, not numeric fields. The site states them (`Icy Penance: Value 284 · SP 29.0% · AP 7.8%`, against our decoded flat of exactly 284) **and** states `EffectTriggerSpell` links, so relationship discovery is a byproduct (HoJ → HftH off the page's own href; 154 edges in the first 39%). Used by hand once in `1x` and never systematised until now. **Cheaper routes checked and rejected first**: `?spell=X&power` returns a 583-byte JS object but **no `Scaling` lines**; `sitemap.xml` has no per-spell URLs. `robots.txt` is `Allow: /`, no `Crawl-delay`, disallowing only admin/account/compare/filter/search — we are stricter anyway (sequential, 2s, contact UA, stop on 403/429). **Scoped by measured demand, never enumeration.** 🛑 Coefficients trusted only where the page's base value reproduces our client-decoded flat (14,100 check digits); disagreement REFUSES them. **FINAL 2,902/2,902: 66.3% agree, 0.2% disagree (6, all diagnosed and still refused — the tolerance was NOT widened to absorb them), 1,634 coefficients, 329 trigger edges** |
| 2026-08-06 (3b) | ⚠ **An aggregate across EFFECT SLOTS is not a property of the spell — it mixes units** | The scrape's cross-check first aggregated `MIN/MAX` across slots, so Lightbound Cleave's effect 0 (flat **62**) and effect 1 (**65% weapon damage**, the `EFFECT_WEAPON_PCT` trap from INDEX_GUIDE v13) merged into "62–65" — a range belonging to no effect — and falsely contradicted the page's correct `Value: 62`. Caught because the check disagreed with a source that turned out to be right. Now compared per slot: 6 agree / 0 disagree on the pilot. **The check found a bug in our code before it found one in the data, which is the argument for having it** |
| 2026-08-06 (3b) | 🎉 **The inherited exit gate now PASSES — 4 of 41 within ±20% — and the cause was ONE missing input, not a fitted constant: weapon damage is in NO stat block** | `resolved_bisbeard.damage` is NULL on **all 1,413** weapon-slot entries and `stats` never carries it, so `build_spec_for` was constructing every crawled character with `weapon=None` — the sim gave all 41 candidates **no weapon at all**, zeroing white swings and every weapon-percent ability. Found by DECOMPOSING the miss (PLAN_3B §5.2) rather than attributing it: gear resolution **eliminated** for 30 of 41 (median 100% coverage, still −92%), buffs **median +0.0%**, leaving per-ability coverage — sim damage for a median **20%** of real damage, **37%** after the fix. Weapon numbers exist only in the rendered item description and are parsed **with the same string's stated DPS as an enforced check digit**, 849/849 within 3%; a failing parse returns nothing. 🛑 **Read the pass with its coverage: only 1 of the 4 (Ari) is inside tolerance while ≥50% of its damage is modelled** — the others agree on the total while the sim reproduces 5–13% of the kit, i.e. compensating error, which an aggregate criterion is blind to. The criterion was **not** redefined after the result was seen; the qualified count is reported beside it and the question is the owner's (`crawled_gate_passes_by_compensating_error`) |
| 2026-08-06 (3b) | 🚨 **Gear is dynamic, and `PLAN_3B` §3 was amended: the difficulty axis lives in the item_id** | Stats are rolled at drop by tier, so **476 of 1,157** resolved item names span several item_ids with different stat blocks (`Golem Shard Leggings` = Str 45 / 38 / 30 at Mythic 10 / Mythic / Heroic). **But each variant carries its own id** and `item_id → (tier, stats)` is a function — 0 of 1,792 stat-bearing ids carry two blocks or two tiers. So **"never map item NAME → stats" stands and is the real hazard** (the crawl's own 98 `name_fallback` matches are it, now visible as `snapshot_gear.stats_match_type`), while §3.2's "the deduped `items` table collapses real differences" is **dropped** — keying on the id is lossless. Owner decision 2026-08-06. ⚠ Whether base-id → variant-id forms a decodable scheme is **not established**; prefixes are inconsistent, and relating two ids by a pattern is the same error class as relating two spells by name |
| 2026-08-06 (3b) | ⚠ **Gear-stat coverage is reportable but NOT repairable from the corpus** | `gear_coverage()` reports resolved fraction of stat-bearing slots (shirt/tabard excluded as measured-statless: 0 of 209 and 0 of 87). Median across the gate is **100%**, 30 of 41 fully resolved — which is what eliminated gear as the dominant cause. The 592 unresolved item_ids resolve on **no** snapshot (0 of 592), because they are absent upstream: levelling greens and vanilla items outside BisBeard's S10 scope. Whether to enrich them from db.ascension.gg is open (`crawl_gear_coverage_is_not_repairable`) |
| 2026-08-06 (3a) | 🚨 **The client DBC is NOT a source of item stat values — Phase 0 T9's "honest default" route is a dead end, and Phase 3 T4 runs on the crawl instead** | Probed rather than assumed, and disproved against ground truth. `Item.dbc` (563,308 records, 8 fields) is stock display data. `ItemStat.dbc` (1,513,931 records, 39 fields) is a custom table whose fields 3–22 read as `(ITEM_MOD type, value)` pairs reproduce the true block **6 times in 567 overlaps** across 1,198 items the crawl already resolves, with no field matching a real stat value above 9.2% (chance). Expected in hindsight: 3.3.5 keeps item stats server-side in `item_template`. `items` is therefore assembled from `snapshot_gear` (1,680 items / 1,313 with stats at the time of this entry; 2,384 / 1,792 after the backfill completed) — Path B's own fallback. ⚠ **Provenance is stamped `crawl_resolved_bisbeard`**: those blocks are BisBeard's resolution carried through the armory capture, so cross-validating our weights against BisBeard checks the WEIGHTS and not the ITEMS. The remaining `ItemStat.dbc` layout is recorded as an open question, not guessed |
| 2026-08-06 (3a) | 🚨 **PHASE_3 T2's crit-table regression is IMPOSSIBLE as specified; replaced with a within-character anchor comparison** | The doc says regress each character's crit% against their melee and spell crit rating. Per-parse stats do not exist (Phase 0 T2) and armory stats are gear-only — **and hit/crit rating are unified in GEAR (2d)**, so a gear-rating regression cannot separate the two tables even in principle. The replacement compares the target's crit% against the same character's crit% on doc-confirmed anchors *in the same parse* (melee: Auto Attack; spell: confirmed `crit_table='spell'` ids expanded through the crosswalk), so buff state, gear and target-level suppression cancel inside the pair — the property that makes weapon-free pair ratios durable, reused. ⚠ A two-bucket version proposed five PERIODIC abilities (4 Consecration ranks, Blood Presence) as `melee`, because ~0% crit is closer to the melee anchor than the spell one; a `none` bucket now fires first. `infer_coefficient` **refuses per spell and records the refusal** — it unlocks only when per-parse stats exist (T5 self-snapshot) |
| 2026-08-06 (3a) | ⚠ **PHASE_3 T1's DDL deviates in five recorded places; the load-bearing one is `capture_scopes`** | Per-ability endpoints aggregate over whatever `encounterIds` were passed and rows carry no encounter id, so an ability row's real granularity is the SCOPE, not the encounter — performance keys on `scope_id`, and `encounter_id` is set only where the scope covers exactly one. Collapsing scopes onto encounters would fabricate precision the source never had. Also: avoidance moved to its own enemy-keyed table (no attacker id exists), no `patch_id`/`phase_id` columns (rebuild-scoped autoincrements must not be referenced durably — the `open_questions` slug lesson), `gear_stats_json` not `stats_json` (the `_gearOnly` trap), and snapshots carry `capture_report_id` so the build-to-parse join can be EXACT rather than nearest-in-time |
| 2026-08-06 (3a) | 🚨 **Phase 3's inherited exit gate is NOT MET: 0 of 41 crawled characters within ±20%, and 40 of 41 misses are NEGATIVE** | A one-sided distribution that size is a missing multiplicative layer, not noise. Ranked cause: **buffs are modelled for the owner only** — 2e measured his own unbuffed→buffed gap at ×2.35, and every crawled parse is a real group the sim buffs not at all. The post-backfill candidate set is real Zul'Gurub raid bosses (Hakkar, Bloodlord Mandokir, Taerar, Snowgrave), i.e. exactly where buff stacks are largest, and that is where the −90% misses sit. The buff set is **derivable** (the group is in the same report), so this is buildable. Second cause: talents resolve only where cards resolve, and the crawl is every class's kit. 🛑 Not to be closed by fitting a constant. ⚠ Level is read, never assumed — a first version hardcoded 60 and simmed a level-49 parse against level-60 magnitudes, `1x`'s retracted pooled-crawl error re-committed and caught |
| 2026-08-06 (3a) | ⚠ **RETRACTED, same session, mine: "the strict lag-0 build-to-parse join yields only one level-60 character, because exact-join captures skew toward levelling players"** | Measured against a MID-BACKFILL corpus and written up as a structural property of the data, which justified loosening the gate's staleness threshold to 336h to get an n at all. The backfill then completed and the *same strict filter* returned **41** characters. It was small-sample, not structure. **Generalised into the tool's own docstring: a filter that starves on a partial corpus is not evidence that the filter is too strict — re-run on more data before loosening a constraint.** The gate now runs at its strictest setting with no staleness caveat, so the correction strengthened the result rather than weakening it |
| 2026-08-06 (3a) | 🟡 **Owner decision: seed Holy Shock's measured SP 0.40 as PROVISIONAL, under its own source string** | Neither the client's 0.429 (consistently ~5% high across four logs) nor nothing (2c falsified "no SP term": 26–34% above group in every log). 0.40 goes on the damage sub-spell **25902** — the trigger TARGET, per the 2026-08-05 attribution rule — with `source='ascension_measured_provisional'`, so it is filterable and visibly weaker than a stated coefficient. `seed_hand_coefficients.py` now owns two source partitions and scopes its delete per source. 🛑 The open question stays **in_progress**, not resolved: 0.40 is back-solved from the owner's own parses and must never be used as a fit target against them (2e's rule for the unseeded Holy residual). Closes on any source that STATES a coefficient |
| 2026-08-06 (3a) | 🆕 **Crawler re-verification sweep (T8); "capture all roles" was already satisfied** | `ROLES = [dps, tank, support]` has been walked since 0b (`tanks-and-dps` is a union of two already taken) — reported rather than re-claimed. The real gap was that discovery is incremental, so a character who respecs and then stops parsing stays frozen at their old build indefinitely. Each run now re-pulls up to 40 known-but-not-seen-today characters, oldest capture first, so the sweep rolls through the population; content-hash dedupe already makes an unchanged build cost one request and zero bytes, so the cost is ~40 requests/day rather than a second crawl |
| 2026-08-05 (2e) | 🚨 **`spell_effect_values` decodes EVERY extracted spell** — new `via='dbc_only'` (+19,098 rows / 11,857 spells), attribution untouched (`spell_id == source_spell_id`) | The resolver walked only catalog routes; seal targets, judgement spells, out-of-catalog versions and talent damage spells were extracted-but-never-read. Combat logs name ids directly, so the sim resolved exactly those and got nothing. Third instance of the family "data present, query narrow" (2b's 686 siblings, 1x's 98%). The scoped delete now covers three vias — a fourth writer must scope its own |
| 2026-08-05 (2e) | ❌ **RETRACTED (2d): "Seal of Command riders fire on autos only"** — measured ~0.25 procs per melee event, autos AND abilities | Generalised from a Lightbound-Cleave-only isolation window, and LC is the one ability that feeds nothing. **An isolation window isolates its subject — it cannot ground a claim about everything outside the isolation.** LC itself still procs nothing; the Cleave Kit costing stands. Mechanism (rate vs PPM) open: two windows at one weapon speed cannot separate them |
| 2026-08-05 (2e) | ✅ **The Holystrike residual WAS the weapon input** (LC 1.00×, Dawnreaver 0.99×); 🚨 the Holy residual is TWO mechanisms and must never be averaged | First same-session stat block in project history. Missing-coefficient class (out-of-catalog spells have no tooltip to carry one — 2.2×) vs real residual on coefficient-bearing spells (~1.24× post-talent-layer), plus a buff-scaling component. Back-solved coefficients stated in the calib report and deliberately NOT seeded — a coefficient fitted to the parse it checks is not a check |
| 2026-08-05 (2e) | 🆕 **Buff layer measured to arithmetic; BonusHealing = undoubled SP is a standing instrument** | Owner's incremental capture (one export per buff). Kings ×1.10 applied LAST; imbue **+86 raw per weapon, stacking** — the 2d "+172" was the doubled presentation on a sheet that should not have doubled, flagged for re-measure. Also generalised the read-too-early trap: ANY fresh buff can be absent from an immediate export |
| 2026-08-05 (2e) | 🆕 **Glancing vs +3 = 32.6% ascension_measured** (95/291; retail 24% rejected at 3.1σ); melee crit suppression consistent with ZERO (66/261) | Both constants named in `combat_engine.py`; measured value served, retail kept for reference. Suppression stays open (3-point effects fit the error bar) but the retail assumption now has evidence against it |
| 2026-08-05 (2e) | 🆕 **Terminology (D6): "lego" → "kit"; a `chassis` is the shared base** — ARCHITECTURE layer 4, `core/legos/` → `core/kits/` (planned), PHASE_4 annotated not rewritten | Owner decision 2026-08-05. First fully-measured kit: the Cleave Kit (Package 4), now PHASE_4's discovery regression target |
| 2026-08-05 (2e) | 🆕 **Watch-sweep design: the first keyword per watch row is a required ANCHOR; generic keywords only amplify** | The naive any-keyword scan matched 299 unrelated balance entries (`proc`, `spell power`). Anchor-first cut it to exactly one true positive (the known 2026-07-28 Duality RAP fix — a validation against history). Encoded in `bugs/README.md` |
| 2026-08-05 (2d) | 🆕 **ARCHITECTURE (owner): model INTENDED behaviour; impairments are a separate, dated layer; "don't recommend" is a policy flag, never a change to the math** | Corrects a same-session over-reach of mine that hardcoded Duality's bugged values as the model. Three reasons, all the owner's: a fix would otherwise require re-deriving the model (a landmine someone must remember to defuse); **other players' parses are full of the broken system**, and only an intended model lets a crawled character read as *impaired* rather than as a *worse build*; and an intermittent bug has no true point value, so `as_measured` must return a **RANGE** with the unmeasured quantity named (`duty_cycle: None` — not guessed). Implemented as `core/builds/stats.py :: SYSTEM_IMPAIRMENTS` + `compute_stats(system_state=...)`, 4 new checks. ✅ **Free detector:** parses that systematically underperform the intended model *are* the bug — and when they stop, that is the fix landing |
| 2026-08-05 (2d) | 🚨 **Duality's INTENDED behaviour includes a +75% boost to GEAR spell power — which ends a four-version oscillation** | Ascension's own path documentation: AP = highest primary stat, **gear SP boosted 75%**, cross-stat crits, and two named sub-abilities (*Unleashed Force* 2H +6% damage, *Twin Flurry* 1H +10% haste). **This vindicates v3's "×1.75 itemised SP amp", which v4 retracted for not being visible on the sheet — both were right about different things: v3 read the DESIGN, v4 observed the BROKEN DELIVERY.** At gear SP 229, intended ≈ 425 vs 271 observed (~36% shortfall), which is exactly why a bug report says *"a difference of 19 Spellpower"*. ⚠ Scoped to **gear** SP, so the multiplier is order-dependent in `compute_stats` — it must run before Lunar Guidance and other effect SP is added |
| 2026-08-05 (2d) | 🛑 **PATH OF DUALITY IS BROKEN — its parses are excluded from absolute calibration, and it is not to be recommended** | Community-reported by multiple players and corroborated by our own captures: the AP bonus **cycles on/off every ~10–15 s** (832↔1128 for one player, 174↔307 for us), the SP grant is reduced to a flat **+19** (independently reported as 19), and the weapon-type passives are dead. Every historical calibration log therefore had AP oscillating **mid-parse** — a candidate cause of part of `2b`'s 1.41× between-session spread. `core/builds/stats.py` was applying a 6% all-damage clause the server does not grant; removed. Owner plays **Path of Intelligence** now. Fix-detection watch list in `bugs/README.md` |
| 2026-08-05 (2d) | ❌ **RETRACTED: "Duality applies a 1.895× SP amplifier"** (which had itself reversed a v4 retraction) | A relog-separated three-path capture measures **no amplifier — a flat +19**, while **Path of Intelligence** measures a real ×2.0 doubling that its own tooltip states. A Path-of-Strength capture taken *without* relogging read SP 500 = 1.995 × (items + Lunar Guidance), proving PoI's doubling persists across a switch. So the 2026-08-04 reading could have been stale PoI, an ON phase of the cycling bug, or a working Duality — indistinguishable after the fact. **Method: a measurement taken by toggling a setting is only as clean as the toggle; where a switch has settle/cycle/carry-over behaviour, a relog belongs between every reading** |
| 2026-08-05 (2d) | ❌ **RETRACTED: "Duality converts Str→AP at 0.548×"** | Not a rate — an **OFF-phase reading** of the cycling bug. 174/307 = 0.567 and 0.548 are two samples of the same phase. **Two agreeing measurements of an oscillating quantity are not a confirmation** |
| 2026-08-05 (2d) | ❌ **RETRACTED: "hit and crit rating are UNIFIED stats"** (build doc §10) | Unified in **gear**, not in the engine. The path trio shows 238 melee vs 187 spell crit rating on identical gear under Duality (179/179 under Strength and Intelligence) — the cross-crit conversions grant **rating** at ~3.4 stat per rating point. Stat weights must be per-table |
| 2026-08-05 (2d) | 🚨 **Hammerdin does NOT proc from Judgement or Holy Shock — build doc §11's rotation premise is false in game** | 10-minute dummy test: Dawnreaver 15–17 procs / 119 casts (~stated 20%), **Holy Shock 1/78, Judgement 0/51** — combined 1 where ~26 is predicted, p < 10⁻⁹. The −4 s reduction works per proc; no ICD. Submitted as [tracker #200295](https://ascension.gg/bugtracker/view/200295). **Dawnreaver is the engine driver.** Suspected cause (a guess, filed as an open question): trigger-delivered damage is proc-blind, which would affect every "damaging X abilities" engine on the server |
| 2026-08-05 (2d) | ✅ **Lightbound Cleave feeds NO engine — and that inertness is a feature** | Isolation window + same-log control: zero Hammerdin (53 LC hits + 70 swings), zero PBL (while the control produced 14 Consecrations / 2 Exorcisms), Seal of Command riders on **autos only**. PBL's "weapon-damage spells and abilities" intake is narrower than its wording. Closes `lightbound_cleave_post_patch_procs`. Owner's observation that LC + Improved Cleave is a portable **kit** is written up as Package 4 and made a `PHASE_4` discovery regression target — all 8 Cleave school variants share the byte-identical family-4 mask, so Improved Cleave's ×2.20 reaches every one |
| 2026-08-05 (2d) | 🆕 **Training-dummy identity is a calibration variable** | Two sessions an hour apart, identical unbuffed character, differed **10–18% on every ability** — one dummy scales to player level, the other is a fixed 63. Dummy NPC identity belongs in capture metadata alongside gear and buffs. Within-log ratios unaffected, which is again why the weapon-free pairs are the durable quantities |
| 2026-08-05 (2d) | 🆕 **Weapon imbues grant STATS, not just a damage rider** | Consecrated Weapon adds **+172 Holy SP and ~+61 AP** to the sheet, school-scoped — so it separates Holy from general SP. ⚠ The catalog's Rank-1 sub-spell states +11/+19; the level-60 sibling is unresolved. **An "unbuffed" baseline is not clean unless the imbue is also absent** |
| 2026-08-05 (2d) | ⚠ **A settle delay and an indefinite oscillation are indistinguishable through one before/after pair** | Mine, twice: I diagnosed the AP behaviour first as "stale until relog", then as "a ~5–10 s settle delay" after the owner watched the sheet settle. Both wrong — it oscillates forever. Repeated sampling over minutes is what separates them |
| 2026-08-05 (2b) | 🚨 **Trigger-reached damage can be DELIVERED by a periodic-trigger aura — a trigger-attributed magnitude is not "once per cast"** | Hour of Judgement effect 1 is `SPELL_AURA_PERIODIC_TRIGGER_SPELL` at a 500 ms period over a 10 s duration, so one cast fires Hammer from the Heavens **20 times**, alongside 5 ticks of its own 81. The pulse spell itself is NOT periodic — the DELIVERY is, so periodicity must be read off the triggering effect slot, never the triggered spell. Validated with no fitting: predicted ratio exactly 4.00, pooled crawl gives **16,491 HftH hits / 4,332 HoJ hits = 3.81** across 170 character-report groups. Confirms the ratio and hence the structure; does NOT confirm the absolute 20 (invariant to duration) or any magnitude (crawl records no level). 48 component rows across **34 cards** are affected; counts above 100 are refused, not clamped |
| 2026-08-05 (2b) | 🚨 **Rank siblings had NO magnitudes at all — 686 cards silently simmed as 0** | The resolver correctly redirects a level-60 query to the rank the character casts, but `resolve_numeric_formulas.py` only ever decoded CATALOG ids, so the redirect landed on a spell with zero `spell_effect_values` rows: it traded a WRONG magnitude for NO magnitude. All 686 were in `spell_dbc_raw` and decodable the whole time. Now 676 covered (+1,193 rows), 25 ambiguous lines skipped rather than tie-broken. Lightbound Cleave, Dawn Strike, Holy Finish and Consecration all went 0 → real |
| 2026-08-05 (2b) | ⚠ **`EFFECT_WEAPON_PCT` was emitted as a FLAT damage term** | The stored value is a PERCENT: Lightbound Cleave gained 65 flat damage instead of 65% of a ~627 swing. A units error that shrinks with gear, so it presents as a scaling problem rather than a units problem. Now becomes a `WEAPON` coefficient of pct/100 |
| 2026-08-05 (2b) | ⚠ **`fast_sim` allocation order is not priority order** | A no-cooldown ability first in the priority list consumed the entire GCD budget and starved every cooldown behind it — reporting a one-button rotation and **every stat weight as 0.00**. Cooldown abilities are rate-limited and must be allocated first; off-GCD entries ride along free |
| 2026-08-05 (2b) | 🆕 **Amplifier talents must be read from auras 107/108 + SpellModOp, not from tooltip prose — and this is the foundation 2c's talent modelling should use** | Improved Cleave is `EffectAura 108` (`SPELL_AURA_ADD_PCT_MODIFIER`) with `EffectMiscValue = 8` = **`SPELLMOD_ALL_EFFECTS`**, so its +120% multiplies EVERY effect of the spells in its class mask. Its tooltip says *"increases the bonus damage done by your Cleave ability"*, naming one term — **the tooltip understates its own scope**. For Lightbound Cleave that is ~470 → ~1,033 per hit, not the +74 a flat-only reading gives. The project's "never read a magnitude from tooltip prose" rule extends to **scope**, and numeric-field modifier ops are the general mechanism for talent multipliers |
| 2026-08-05 (2b) | ❌ **RETRACTED, same session, mine: "Improved Cleave is low-value because the flat is small" — it stays a TOP chase** | Having correctly retracted v9's `9 + AP × 1.0` *mechanism*, I carried the demolition straight through to the *conclusion* without re-deriving it, and treated the tooltip as authoritative about which effects the modifier touches. The owner flagged it immediately against direct in-game experience and the numeric field settled it against me (row above). **Lesson: retracting a mechanism does not retract the conclusion it supported** — v9 was right about the card for a reason it never stated. v9's formula stays retracted; there is still no AP term on Lightbound Cleave, which is excellent because it multiplies a large *weapon-damage* component |
| 2026-08-05 (2b) | 🔴 **RETRACTED: v9's Improved Cleave FORMULA (`9 + AP × 1.0`) — the card's ranking is unaffected** | v9 moved it from last to #2b on the reading that Lightbound Cleave's bonus term is `9 + AP x 1.0`. Two compounding errors, each already covered by a hard rule: 9 is the **Rank-1** value (a level-60 character casts Rank 5, where it is **62**), and `EffectBonusCoefficient = 1.0` is stock `EffectBonusMultiplier`'s neutral default, not an AP coefficient — retracted catalog-wide in `1x`. LC R5 is 65% weapon damage + flat 62; Improved Cleave 3/3 is worth **+74 per hit, not +712** (~9.6x overestimate). §10a's x1.48 ceiling loses its x1.110 factor. v9's "independent corroboration" applied the same formula to the same premises |
| 2026-08-05 (2b) | ⚠ **T6 cannot source its ranges from `spell_mechanics.uncertainty_json`; owner decision — build them in the sim layer** | Measured across all 3,747 rows: `damage_formula_terms_json` is stored `low: None, high: None, basis: non-numeric`, and every numeric field carries a `default_confidence_mapping(confirmed, ±0%)` band explicitly labelled "heuristic, not measured". Sampling that reports ±0% knowledge uncertainty — worse than none, because it looks authoritative. Bands now live in `core/sim/uncertainty.py`'s POLICY table as a stated, arguable assumption; Phase 1's truth table stays untouched rather than carrying invented ranges behind tier provenance |
| 2026-08-05 (2b) | ⚠ **Combat-table facts now follow the rank redirect; magnitudes do not** | `doc_confirmed_mechanics` is seeded against catalog ids, so Lightbound Cleave's proc-tested `crit_table='spell'` was discarded the moment the resolver redirected to the rank-5 id, falling back to a heuristic guess in place of a measurement. Crit/hit table and avoidance are rank-INVARIANT properties; magnitudes are not, so only the former are carried |
| 2026-08-05 (2b) | ⚠ **The daily patch check missed a build-relevant entry — scan by MECHANIC, not by card name** | 2a reported 2026-08-04 Darkmoon as "PvP-only reductions plus a new talent Authority". It also carried *"Fixed a bug where mechanics that are supposed to trigger from physical abilities would not trigger from the newly introduced physical + magic school abilities (Talents such as Art of War, Vengeance etc.)"* — Holystrike is such a school and is most of this build's damage, and **Vengeance is slotted at 2/3**, so its own Holystrike crits were not feeding an equipped card. The note names no slotted card except in a parenthetical, which is why a name scan missed it |
| 2026-08-05 (2a+) | 🆕 **Owner decision: trigger-reached coefficients live on the trigger TARGET, never the cards** | Closes the decision half of `trigger_attributed_coefficients_not_in_spell_scaling` (now in_progress). New append-only `seed_hand_coefficients.py` owns `spell_scaling` rows with `source='db_ascension_gg'` (rebuild is 19 steps); first rows: 282987 SP/AP 0.091. Rationale: truth stays where it is true, no per-card duplication, and 2b's per-source-spell event model composes on top. Cards-side hand-seeding was explicitly rejected (conflates the pulse event with the card's own hit — 282984 already carries its own SP/AP 0.05) |
| 2026-08-05 (2a) | 🆕 **Trigger-attributed magnitudes ARE summed into `expected_hit`**, flagged `calibration_anchor=False` | The kickoff note's "never let inferred rows anchor calibration" was first over-read as "exclude from computation" — which zeroes 444 cards (Hour of Judgement's entire damage is its trigger chain). Corrected same session: computed + warned + listed in `triggered_components` so calibration can subtract them. The rule constrains *anchoring*, not *computation* |
| 2026-08-05 (2a) | 🚨 **HftH's confirmed 9.1% SP/AP coefficients are NOT queryable** — doc prose + `confirmed_facts` only, no `spell_scaling` rows for 282987 or the cards | Found by 2a's validation: the resolver serves flat 122–145 without the stat terms (~45% understatement at AP 584/SP 533). Filed as open question `trigger_attributed_coefficients_not_in_spell_scaling` rather than rush-seeded — attributing coefficients to cards has per-event/rotation semantics, the same per-case judgment 1b's multi-path decision deferred |
| 2026-08-05 (2a) | ⚠ **Crit suppression vs higher-level targets: warned, not modelled** | No fabricated retail constant (§2 rule 2). The owner's own parse hints it exists (sheet 21.76% vs autos 16.2%, n=37 — too small). Open question `melee_crit_suppression_vs_higher_level`; combat_engine emits a warning whenever a white table is built vs a higher-level target |
| 2026-08-05 (2a) | ⚠ **Talent stat/multiplier modelling deferred to calibration** — component-mode `compute_stats` warns per unmodelled slot | PHASE_2 T4 wants full resolution; without an items table (Phase 3) and per-talent magnitudes, silent partial modelling would fabricate precision. Sheet mode (`stats_override` = FINAL sheet values) is exact today and is the calibration path. The phase doc's T4 section is amended |
| 2026-08-05 (1c) | 🆕 **`open_questions`/`retractions` key on a `slug` column** beyond T6's DDL | Autoincrement ids reset every rebuild — nothing durable can reference them. Both tables owned by `seed_epistemics.py`, append-only, same discipline as `seed_confirmed.py` |
| 2026-08-05 (1c) | ⚠ **A "mark vanished crosswalk targets" auto-fix was built and WITHDRAWN in-session** | Without history, absent-from-extract is indistinguishable from never-in-scope: 7,654 out-of-pool CA rank-slot rows matched the "vanished" predicate. Now report-only in the provenance sweep. The withdrawn version had already polluted notes on one build — a rebuild reset it |
| 2026-08-05 (1c) | ⚠ **The one "cross-source" mechanics conflict is a component collapse, not a source disagreement** | Champion's Spear (291180): weapon_damage_pct 150 (initial hit, own effect) vs 50 (per-second DoT, sub-spell 291181). Both real; one column cannot hold two components. Queued; a T4-schema follow-up (per-component formula terms) would dissolve it |
| 2026-08-05 (1c) | 🆕 **`spell_scaling.term_type` vocabulary widened** (SPFR/SPFI/SPH/SPN/SPA/SPS/BH/SPI/STA + lowercase/compound/prefix forms extract) | The 1b carry-over gap. +290 rows / +112 spells; BH routes to the healing block in `spell_mechanics`. `SP_PAT`/`AP_PAT`/`RAP_PAT` untouched so `rank_scaling`'s validated comparisons don't shift; DBC-side extractor delegates to the shared implementation (effective next `--with-dbc`) |
| 2026-08-05 (1c) | 🆕 **Protocol generator refusal scans actionable fields only** (method/setup/record), not question text | A blanket scan made the reroll-mechanics question un-protocolable — its observational protocol (log fishing outcomes, zero cards at risk) is legitimate. The refusal still raises `CardDestructionRefused` on any instructing text |
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
