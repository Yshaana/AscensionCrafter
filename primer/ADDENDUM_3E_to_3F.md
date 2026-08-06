# Addendum — `3e` → `3f`: ordering, and amendments to the standing plans

**Written by:** the monitoring chat, 2026-08-06, after auditing `3e` against a fresh
clone at `c86eb7f`. Companion to `primer/AUDIT_3E_ADVERSARIAL.md`, which carries the
`file:line` evidence for everything asserted here.

**What this is for.** `3e` closed with one open question from Code — *does `3f` (log
ingestion) run before `PLAN_3G` (self-verifying gates)?* — and left three plan documents
that no longer describe the tree. This answers the first and lists the amendments the
second requires. The work order itself is `primer/SESSION_3F_PRIMER.md`.

---

## 1. The ordering question, answered

> **Code asked:** *"Gates exist to stop bad numbers reaching a database, and `3f` builds
> a writer into one."*

**The instinct is right and the conclusion does not follow. The answer is neither: a
short instrument-repair block first, then `3f`, then `3G`.**

**Why not `3G` first.** `PLAN_3G` as written is a *framework* — a gate registry,
three-verdict semantics, `scripts/gates/`, a phase runner. It is being designed against a
picture that is already stale: `PLAN_3G:30-32` names `within_tolerance` as its fifth
fail-open instrument, and `3e` A3 fixed that in the same session the plan was written
(`calibrate_crawled.py:696-698`). Meanwhile **none of the four fail-open instruments the
audit actually found is on its list.** Building the abstraction before repairing the
specimens produces a registry whose test set is wrong.

**Why not `3f` first, unmodified.** Code's argument is stronger than Code stated it, and
in its concrete form it decides the ordering:

> 🛑 **`tools/audit/check_gate_exclusion.py` cannot run.** `3e` A1 changed
> `candidates()` from `(conn, limit, max_lag_hours)` to `(conn, cohort_ids,
> max_lag_hours)` (`calibrate_crawled.py:240`) and the guard still calls it with
> `limit=120` at `:126,140,160` — `TypeError` before any DB access. That guard is what
> proves owner-captured snapshots never enter the gate cohort. **`3f` is precisely the
> session that creates owner-derived rows in `builds.db`.**

And repairing the signature does not restore the test: `inject_privileged_character()`
mints the intruder at `character_id 1` *on purpose*, because the old `candidates()` was
`ORDER BY character_id LIMIT N`. Under a frozen id set that character can never appear
**whatever its `source`**, so the positive checks pass for an unrelated reason and the
control arm fails. It needs rewriting against the frozen-cohort design.

So the write-side guard for the exact hazard `3f` creates is dead **today**. That is a
precondition, not a framework — which is why the answer is a block, not a session.

**Ordering, with reasons:**

| # | what | why here |
|---|---|---|
| 0 | **Time-critical, by 2026-08-07 20:00** — §2 below | deadline-driven; the tripwire can block the one capture that cannot be redone |
| 1 | **Instrument repair block** (`3f` Block A) | contains `check_gate_exclusion`'s rewrite, which `3f`'s writer depends on |
| 2 | **Ground truth in the fixtures** (`3f` Block B) | no assertion anywhere in the harness compares a modelled magnitude to a measured one; the writer is about to produce magnitudes |
| 3 | **PHASE_3 T6, log ingestion** (`3f` Block C) | the largest single source of owner toil. Every log finding in this project currently survives only as prose a human typed into a seed file |
| 4 | **`PLAN_3G`** | now has four real specimens from step 1 and a real customer in step 3's writer |

🛑 **One thing to say plainly, so it is not mistaken later: `3G` does not move the
residual.** `3e`'s holdout result says the error is in magnitudes and coverage, not
mechanisms — six mechanisms were repaired and the answer did not move. `3G` is insurance
on the instruments. Worth doing; not progress on the model, and it should not be counted
as such when Phase 3's exit is re-read.

---

## 2. Time-critical — this does not wait for a session

The server flips to **Phase 2 on 2026-08-08**. The crawl half is genuinely fixed and was
verified by execution against a synthetic Phase 2 payload: `assert_phase()` raises
`RealmSeasonMismatch`, exits **2**, and fires *before* any record is written
(`crawl_ascensionlogs.py:315-321,844,886`). That part is good and `3e` did not disturb it.

Two exposures remain, and one has a Friday deadline.

**2.1 🚨 The tripwire can block the one capture that cannot be redone.**
`tools/scrapers/baseline_phase1.py:44` calls `crawler.crawl_phases(writers)` and therefore
inherits the assertion, but its `main()` does **not** catch `RealmSeasonMismatch` — it dies
on a raw traceback. It is scheduled **2026-08-07 20:00** (`SCHEDULING.md:128-132`). If the
API flips its active record even hours early, the guard blocks the baseline and the owner
sees a stack trace rather than the refusal banner. Leaderboards and armory are the only
data the flip destroys.

*Fix: catch it in `main()`, print the refusal banner plus an explicit "this is the
pre-flip baseline — if you are seeing this the flip already happened, capture is no longer
possible" line, and exit nonzero. Ten minutes.*

**2.2 ✅ `gear_tier_stats` — OWNER DECISION TAKEN 2026-08-06: derive `phase_label`.**
`core/builds/gear.py:128-131` writes the literal `None` into `phase_label` on every row of
the only writer. No other writer exists; `snapshot_gear` has no phase column
(`corpus.py:77-96`); `gear_tier_stats()` never selects or filters on it and returns a
hardcoded caveat string at `:409`. Its own docstring predicts the outcome at `:350-355`:
**a Phase-1 BiS will be reported as current.**

So the sequence would have been: loud, correct failure on the crawl → owner bumps
`season_config.py:69` → gear tiers silently mix Phase 1 and Phase 2 from that moment.

**Decision: populate `phase_label` by derivation, and give `gear_tier_stats()` a phase
parameter.** ⚠ **Correcting this addendum's own first draft, which implied the data was
missing — it is not.** Every snapshot already carries a capture timestamp (PHASE_3 exit
criterion 6 is MET — patch/realm/season stamping, `corpus.py:53,113,123`), and
`/api/phases` carries each phase's `started` date, which `crawl_ascensionlogs.py:315-321`
**already fetches** to run its own assertion. `phase_label` is therefore a join against
data in hand, not a new source. That makes the option that neither loses data nor lies also
the cheap one.

Rejected, with reasons recorded so they are not re-litigated: *refuse until populated* is
safe but takes gear analysis offline exactly when Phase 2 gear starts entering the corpus;
*accept the blend behind a caveat* is cheapest and is the shape of failure this project has
now found four times — a caveat that is printed and not enforced.

🛑 **Derivation rules, because this is a stamped value and stamped values are load-bearing:**
a snapshot whose capture timestamp cannot be resolved to exactly one phase window gets
`phase_label = NULL` and is **excluded** from a phase-scoped query, never assigned to the
nearest phase. `gear_tier_stats()` reports how many rows it excluded for that reason. Rule
2: unconfirmed is flagged, never defaulted.

**2.3 `3e` removed the reminder from the live docs.** `PROGRESS.md`'s only Phase-2 line is
`:194`, inside a `<details>Superseded</details>` block (`:180-247`). The live top block and
"FIRST ACTIONS NEXT SESSION" carry no mention of 2026-08-08. Put it back.

---

## 3. Amendments to the standing plans

### 3.1 `PLAN_3G_self_verifying_gates.md` — three edits, none structural

The design is sound and unusually well-guarded: the three-verdict requirement with
`INSUFFICIENT_DATA` as the point (`:44-46`) is the correct generalisation of this whole
failure class; `:66-71` explicitly refuses to fit the instrument to its test set;
`:111-112` requires every gate to have a test that makes it fail; `:117` forbids weakening
an existing check. Its pushback on the inline-tag proposal (`:87-105`) is correct for the
right reason. Keep all of it.

1. **`:30-32` states a fixed defect in the present tense.** *"`within_tolerance` at
   `calibrate_crawled.py:494` has no coverage floor"* — the line reference is dead (the
   code is at `:696-698`) and `3e` A3 fixed the consequence in the same session. Delete
   it, and note in its place that a *different* half of the same instrument is still open:
   per-character slice accuracy has no floor (`:737-739`) and
   `predictions/gate_manifest_3e.json` ships `Mutaforma` at **1,859,400%**, the exact value
   `3e` cites as the defect.
2. **Replace the specimen list.** Exit criterion 3 requires each known fail-open
   instrument to be *"either fixed or explicitly recorded as accepted, with the reason."*
   The real list, from `AUDIT_3E_ADVERSARIAL.md` §3–§4:

   | instrument | regime |
   |---|---|
   | `check_sim_engine.py:658` E2 check | `warned` is a constant `True` — `EXECUTE_GATING_UNAVAILABLE` is appended unconditionally and contains "health" |
   | `check_sim_engine.py:760-778` pet check | both sides call the same pure function on the same ids; the assertion cannot fail |
   | `check_sim_engine.py:555-565` `_filler_ids` | re-implements a classification rule B1 changed, while its docstring claims it cannot drift; empty `fillers` ⇒ pass |
   | `check_gate_exclusion.py:126,140,160` | cannot run at all; and cannot be repaired by signature alone |
   | `stat_block.py:199-200` `session_mismatch` | returns the caller's all-clear value when the log filename has no timestamp |
   | `calibrate_crawled.py:737-739` + manifest | per-character slice accuracy, unfloored, uncaveated, committed |
   | `calibrate_crawled.py:1162` `still_qualifying` | counts *scored* characters; sim-path drops never reach `dropped` |
   | `.claude/hooks/block_large_staged_files.ps1:35-36` | measures the working-tree file, not the staged blob |
3. **`:42,73` propose `scripts/gates/` and `scripts/phase_runner.py`.** `scripts/` appears
   nowhere in `ARCHITECTURE.md:225-260`, `CLAUDE.md` or `INDEX_GUIDE.md`. `tools/audit/`
   is the established home for exactly this, and `:56-58` states the new convention as if
   it already existed. Use `tools/audit/`.

### 3.2 `PLAN_V2_BLIND_REDERIVATION.md` — the blind test is not blind ✅ RESOLVED 2026-08-06

Step 2 (`:57,60-62`) makes the `known_answer` column the thing that turns this from a demo
into a test, and says it must be filled from the seeds. Step 3 (`:73`) then lists v2's
permitted inputs as *"the current capture, **the databases**, the crawl corpus, the sim"*,
excluding only the frozen doc and session records quoting it.

**The databases are the answer key.** `RETRACTIONS` names v1's graded claims verbatim and
by slug — `sword_specialization_zero_output`, `duality_sp_amp_not_applying`,
`improved_cleave_is_low_value_because_the_flat_is_small`, `art_of_war_dead_slot` — which
are precisely the ones cited at `:21-23` as v1's known-wrong claims. A v2 session with DB
access learns, before deriving anything, that Sword Specialization is not zero-output.

Step 4's flagship outcome (`:83-85`, *"v2 reproduces a retracted v1 claim → the single most
valuable outcome the test can produce"*) is the cell the leak most directly suppresses: v2
will avoid retracted claims because it can look them up, and that will read as v2 having
improved. **That is assumption-laundering — "v2 read the answer" scored as "v2 measured the
answer".**

**✅ OWNER DECISION, 2026-08-06, taken before v2 runs: rescope the scoring.**

* **The headline is scored on v1's still-open (⬜) claims only.** Those have no answer key
  anywhere in the tree — no `RETRACTIONS` row, no `confirmed_facts` row — so v2's
  performance on them is genuinely blind, and it is scored against the **2026-08-06
  Hammerdin proc-retest capture**, which is tier-1 evidence rather than a seeded verdict.
* **The retracted claims are demoted to a labelled sanity check**, run and reported after
  the headline, and reported *as leaked*: "v2 avoided these; it could also have looked them
  up." A sanity check that says so is worth having. A headline that does not is not.
* **No DB blinding, and no pre-v1 rebuild.** Blinding by exclusion list is an honour system
  unless a filtered view is actually built, and this project does not need another guard
  that is documented rather than implemented. A pre-v1 rebuild would be a real blind but
  hands v2 less knowledge than the current toolkit, so a v2 miss could not be separated
  from "v2 had less to work with" — it trades one uninterpretable result for another.

**Consequence to write into the plan, not just here:** Step 4's flagship outcome
(`:83-85`) — *"v2 reproduces a retracted v1 claim → the single most valuable outcome the
test can produce"* — **is retired.** It was never available; the leak had already suppressed
it. Replace it with the open-claim scoring as the headline, and keep `:86-88` (scoring v2's
*silence* as an improvement) unchanged — that guard works on open claims and is the best
thing in the document.

**Also `:20`** — *"`retractions` holds 24 rows"* is wrong; the tree holds **32**, and held
32 before `3e` started. It is load-bearing: the count is the doc's argument for why v1 is a
good evaluation set, and `PLAN_3G:113` sizes its regression suite from it.

**Otherwise sound.** `:86-88` — scoring v2's *silence* as an improvement, "or the test
rewards overconfidence" — is a genuinely good guard and should survive whichever
resolution is taken.

### 3.3 `ENGINE_BUGS.md` — one wrong magnitude, two incomplete registrations

* **`:398` "Blizzard casts 0 / 0 / 305"** is a raw grep line-count, and **27% of it is an
  enemy's**. Measured from the Window C log: 305 lines total → Elric 222, Scarlet Sorcerer
  83; Elric's `SPELL_CAST_SUCCESS` on Blizzard = **4**, delivering 88,132 of 940,460 spell
  damage (**9.4%**). The conclusion survives — Window C *is* E8-exposed, A→B is not — but
  a figure wrong by ~76× is sitting in the durable registry as the sizing of an engine gap.
  Correct it; do not rewrite the entry.
* **E7 `:344` says `Check │ none yet`** while two registered failing checks exist at
  `check_sim_engine.py:81-92`. Contradicts the file's own line-15 invariant.
* **E8 `:383` says `Check │ none yet` and there is genuinely no check** —
  `grep -n "channel" tools/audit/check_sim_engine.py` returns comments only. E8 is
  currently held by prose alone.
* **`:469`** cites `calibrate_crawled.py:73,465,469`. Those were correct at `200f79f` and
  were moved to `:82,658,662` by A1 — **in the same commit that "fixed" the citation.**

### 3.4 `CALIBRATION_TOLERANCE.md` — regenerate the band table, do not retype it

The committed table at `:166-172` is headed **"n (3e tuning set)"**:

| floor | doc `n` | doc median | recomputed from `gate_manifest_3e.json` |
|---|---:|---:|---|
| ≥0% | 33 | 164.7% | 33 · **163.7%** |
| ≥10% | **27** | 144.0% | **26** · **141.2%** |
| ≥20% | 23 | 64.3% | 23 · 64.3% ✅ |
| ≥30% | **21** | 63.4% | **20** · 63.4% |
| ≥50% | **10** | 63.4% | **8** · 63.4% |

The recompute matches the manifest's own `slice_accuracy_by_coverage_band_pct` exactly, so
the tool is right and the table was hand-typed. Running the same computation over the
**`3d`** manifest minus the holdout gives `33 / 26 / 23 / 20 / 8` at
`164.7 / 144.0 / 64.3 / 63.5 / 63.5` — **the doc's medians are `3d`'s numbers wearing a
`3e` label**, and its `n` column matches neither.

Nothing material changes; the conclusion is robust across every version of the table. But
the project's reference document for its own largest retraction does not describe the run
it names. The durable fix is to have `calibrate_crawled.py` emit the table and paste the
tool's output, never a retyped one — the tool already computes `n` correctly at `:917-921`.

*(The parenthetical at `:174-177` — 159.8 / 85.4 / 62.6 ×3 over 38 from the `3d` manifest —
reproduces exactly. That part is right and should be kept.)*

### 3.5 Docs that stopped matching the tree

Two of these were falsified **in-session**, by `3e` itself, which is why A6-class work needs
to run at the *end* of a session and not the start.

| file:line | what |
|---|---|
| `PHASE_2_simulation.md:467-471` | still headlines the contaminated **1.718** as *"the target a talent model must reproduce"*; the corrected 1.704 appears only in a blockquote at `:488`. Same at `PHASE_2D_residuals_and_scorecard.md:10,158` |
| `PHASE_2_simulation.md:496-503` | describes a tool that no longer exists — *"it refuses to run without `--ap --sp --weapon-min --weapon-max --weapon-speed`"*, with a repro command using them. `3e` C1 demoted all five to overrides and did not touch the doc |
| `ADDENDUM_3D_to_3E_mage_capture.md:33` | asserts the five flags are `required=True` — true when A6 wrote it, falsified three commits later by `3e`'s own C1 |
| `check_sim_engine.py:621,647` | cite `tiers.py:197`, `:198-199`, `apl.py:118`; they live at `tiers.py:469-472` and `apl.py:144`. New stale citations, added by A6's own session |
| `seed_predictions.py:221,223`, `cli/rebuild.py:91` | still name `--limit 120` / *"`candidates()` is `ORDER BY character_id LIMIT 120`"*. The `seed_predictions` row is a pre-registration ledger and arguably must **not** be edited — then it needs a superseded-by note, not silence |
| `PLAN_3C_clean_exit.md:363`, `AUDIT_3C_handoff.md:141-143`, `Session_2026-08-06_3c_paired_upload.md:34-45`, `NEXT_CAPTURE.md:83-84`, `AUDIT_3C_ADVERSARIAL.md:43` | **five docs still assert the retracted `casts` claim**, unmarked. The worst is `3c_paired_upload.md:43`, *"crawl casts/sec is a faithful character-level APM measure"* — falsified for 22 of 41 cohort characters. Two of these are live reference docs named by the monitoring primer |
| `ADDENDUM_3D_slice_accuracy_correction.md:1-7` | still reads *"Urgency: before `3e` runs"*. It landed; the doc does not say so |
| `Session_2026-08-06_3d_hygiene_and_instrument.md:31,204` | carry the 160% reading with no pointer to the correction |

### 3.6 The `C2` collision, one session after `B1` renamed `T1…T13 → C1…C13` to fix exactly this

`SESSION_3E_PRIMER.md:120` and `FINDINGS_3e_preflight:66` point the `casts`-provenance
finding at *"C2's admissibility filter"* — that is `PLAN_3C`'s C2, which
`PLAN_3C_clean_exit.md:100,402-407` **closed as a dead end in `3c`**.
`SESSION_3E_PRIMER.md:234` uses `C2` for the Frost Mage fixture. Same token, two meanings,
114 lines apart. Namespace future session tasks by session (`F1…Fn` for `3f`) and never
reuse a bare letter-number across documents.

---

### 3.7 The folder only grows, and that is a lifecycle gap rather than a tidiness one

**Every artifact in this project has a lifecycle except documents.** Claims get retracted.
Predictions get outcomes. Bugs get closed with checks. Cohorts get superseded by new slugs.
Documents alone are immortal — `primer/` holds 48 files and has never lost one. That is an
inconsistency in an otherwise unusually consistent system, and stating it that way makes
the fix obvious: give documents the same lifecycle the claims already have.

**The risk is not where it looks.** A destructive cleanup could lose something load-bearing,
and that concern is correct — which is exactly why the pass in `SESSION_3F_PRIMER.md` F8c
deletes nothing and moves nothing. The information loss is **already happening**, and it
comes from the absence of labels rather than the presence of files: a session reading
`PLAN_3C_clean_exit.md:363` today gets a retracted claim stated as settled, because nothing
on that file says it is history.

**And the numeric half of the problem has a clean diagnosis.** Every numeric error this
audit found in a document was hand-transcribed:

| doc | wrong number | source |
|---|---|---|
| `PHASE_2_simulation.md:467-471` | `1.718` pair target | hand-typed, from a contaminated run |
| `CALIBRATION_TOLERANCE.md:166-172` | 3 of 5 `n` values | hand-typed beside correct tool output |
| `ENGINE_BUGS.md:398` | "Blizzard 305 casts" | hand-typed from a grep line-count |
| `PLAN_V2:20` | "24 rows" | hand-typed count of a table holding 32 |

**Four for four. Zero errors in numbers a tool emitted.** This is the same defect class as
`3e`'s C1 — four hand-typed stat flags were the transcription channel that contaminated a
calibration — and **the project fixed transcription into the simulator while leaving
transcription into the documentation completely unguarded.** Hence the second standing rule
below.

---

## 4. Two new standing rules, to adopt now rather than at `3G`

> **Every check must carry a registered test that makes it fail.**

It is already `PLAN_3G:111-112`. It is also the single rule that would have caught three of
this audit's four fail-open findings, it costs nothing to adopt today, and adopting it
early gives `3G` a populated registry to formalise instead of an empty one.

Operationally, for `3f` and after: when you add or repair a `gcheck`, add a line to
`ENGINE_BUGS.md`'s check registry naming **the mutation that makes it fail** — "revert
`_decay_target_health` and this check must go red". If you cannot name one, the check is
not a check.

> **A magnitude never appears in a markdown file except as generated output, pasted with
> its provenance.**

Justified by §3.7's four-for-four record, and it costs nothing: `calibrate_crawled.py`
already computes the band table's `n` correctly at `:917-921`, and the committed table was
retyped beside it. Where a number belongs in a document, have the tool print it and paste
the tool's output. Where no tool prints it, that is a signal the number has no owner.

The two standing rules from `3d`/`3e` remain in force and are **not** superseded: every
coverage task reports slice accuracy before and after, and the holdout is named before the
work, not after.

---

## 5. What this addendum does not change

* **`3e`'s headline stands and it is the best result in the project's history.** Five
  engine defects fixed, gate and holdout unmoved, recorded unsoftened. I attacked it and
  could not break it: Block A was verifiably instrument-only (recomputing the `3d` manifest
  minus the holdout reproduces `3e`'s bands to full float precision), `corpus_row_counts`
  is byte-identical between the two runs, and the holdout redaction is provable from git
  rather than asserted. **The residual is not in the mechanisms `3e` repaired.** That
  conclusion is sound and should drive `3f` onward.
* **The frozen cohort, the holdout slug, and the 20% successor floor** are settled owner
  decisions. Nothing here reopens them.
* **`EXCLUDED_SNAPSHOT_SOURCES` stays exactly as it is.** `3f` repairs its *guard*, never
  the filter.
* **The six `ContentProfile` presets stay declared as assumptions.** `3e` correctly
  declined to back-fill by analogy when C4 did not land; `3f` does not get to either.

---

## 6. Owner decisions — two taken, two open

**✅ Taken 2026-08-06, before either was tested against a result:**

1. **`PLAN_V2`'s leak → rescope the scoring** to v1's open claims; retracted claims become
   a labelled sanity check; the flagship outcome is retired. §3.2.
2. **`gear_tier_stats` after Saturday → derive `phase_label`** from the snapshot capture
   timestamp against `/api/phases`, and give the function a phase parameter. Unresolvable
   snapshots get NULL and are excluded, never assigned to the nearest phase. §2.2.

Both are recorded here **and** in `primer/SESSION_3F_PRIMER.md` as tasks, so neither
survives only as prose. Per rule 7 and `/close-session`, whichever session lands them puts
the `PLAN_V2` rescope in `seed_epistemics.py` as well — a design decision that changes what
a test measures belongs in the seeds, not just in a plan document.

**Still open:**

3. **Ground truth in the fixtures.** You are the only source of it and the Mage capture
   already contains it (Window A: 296,031 player / 15,453 pet / 214.2 s, plus seven
   per-hit ratios). My recommendation is that this precedes any further modelling work,
   and it is scoped as `3f` Block B on that basis. Say if you disagree and it moves.
4. **The 20% successor floor** — if the session record's attribution is accurate, log it
   in `PROGRESS.md`'s blocked table retroactively. `3e` modified no row of that table,
   and the floor is numerically identical to a constant Code chose in A2 and justified in
   its own voice. Probably fine; currently unverifiable from the repo, and the next
   auditor will raise it again.
