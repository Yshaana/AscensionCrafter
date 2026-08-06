# SESSION `3F` PRIMER — repair the instruments, then build the writer

> **`HISTORICAL`** — the record of a past session or a completed phase. Immutable. It **may contain claims that are false today**, and that is correct rather than a defect — it records what was believed at the time. **Never citable as current truth.** *(Classified `3f` F8c, 2026-08-07.)*

**Work order for Claude Code.** Written by the monitoring chat 2026-08-06, against a fresh
clone at `c86eb7f`, after `3e` closed and was audited. Read this first, then
`primer/AUDIT_3E_ADVERSARIAL.md` (the `file:line` evidence for everything below), then
`primer/ADDENDUM_3E_to_3F.md` (the ordering argument and the plan amendments).

Predecessors: `primer/Session_2026-08-06_3e_modelling.md` (what `3e` did),
`primer/ENGINE_BUGS.md` (the defect registry), `primer/PLAN_3G_self_verifying_gates.md`
(deferred — see §0).

**Task naming: `F1…Fn`.** Never a bare `C2` or `T6` again — `3e` reintroduced exactly that
collision one session after `3d` renamed `T1…T13 → C1…C13` to fix it
(`ADDENDUM_3E_to_3F.md` §3.6). Where this document means a PHASE task it says
`PHASE_3 T6` in full.

---

## §0 — The ordering rule, and the invariant

`3e` was scoped so the gate was *supposed* to move, and it did not. **`3f` is scoped so
the gate cannot move.** Blocks A and C change no damage arithmetic; Block B adds
assertions, not model changes. So the invariant is the number:

> 🛑 **Every commit in `3f` reports the gate before and after, against the frozen 41, and
> the pair must be IDENTICAL: 5 of 36 within ±20%, 2 qualified, median slice accuracy
> 64.3% at coverage ≥20%.** A `3f` commit that moves the gate has changed the model by
> accident. Stop, do not proceed, and report which commit moved it.

**Why this session exists, and why `PLAN_3G` is not it.** Code's open question was whether
`3f` (log ingestion) precedes `PLAN_3G` (self-verifying gates). The answer is neither, and
the reason is concrete rather than architectural:

> **`tools/audit/check_gate_exclusion.py` cannot run.** `3e` A1 changed `candidates()` to
> `(conn, cohort_ids, max_lag_hours)` (`calibrate_crawled.py:240`); the guard still calls
> it with `limit=120` at `:126,140,160` → `TypeError` before any DB access. That guard is
> what proves owner-captured snapshots never enter the gate cohort — **and PHASE_3 T6 is
> precisely the work that creates owner-derived rows.**

So the instrument repair is a *precondition* of the writer, not a framework to be built
first. `PLAN_3G` follows `3f`, by which point it has four real specimens to formalise
instead of the stale one it currently names. See `ADDENDUM_3E_to_3F.md` §1.

**Scope: Block A + Block B + Block C.** Block D is close-out. If the session runs long,
**whole blocks spill to `3g`, never half a block.** If something must spill it is Block C —
and A+B are exactly C's preconditions, so a spill costs nothing already spent.

**One thing to hold in mind all session.** `3e` fixed six engine mechanisms and the answer
did not move; three holdout members sit at 27–69% coverage and still miss by 45–85%. **The
residual is not in the mechanisms.** Nothing in `3f` is expected to move it either. `3f`
buys the ability to *detect* that it has moved, which is not the same thing and should not
be reported as the same thing.

---

## §0.5 — Before the session, or in its first ten minutes

These are deadline items, not tasks. The server flips to **Phase 2 on 2026-08-08**.

**🚨 `tools/scrapers/baseline_phase1.py` must catch `RealmSeasonMismatch` — by
2026-08-07 20:00.** It calls `crawler.crawl_phases(writers)` at `:44` and inherits the
phase assertion, but `main()` does not catch it, so it dies on a raw traceback. It is
scheduled for Friday 20:00 (`SCHEDULING.md:128-132`). If the API flips its active record
even hours early, the guard blocks **the one capture that cannot be redone** — leaderboards
and armory are the only data the flip destroys — and the owner sees a stack trace instead
of a refusal banner.

Catch it, print the refusal banner plus an explicit *"this is the pre-flip baseline; if you
are seeing this the flip already happened and this capture is no longer possible"*, exit
nonzero. Ten minutes, and it is the highest-consequence ten minutes this week.

**Put 2026-08-08 back in `PROGRESS.md`'s live block.** Its only Phase-2 line is `:194`,
inside a `<details>Superseded</details>` block (`:180-247`). The live top block and "FIRST
ACTIONS NEXT SESSION" carry no mention of it.

**`gear_tier_stats` — the owner has decided; the task is F8b in Block A.**
`core/builds/gear.py:128-131` writes literal `None` into `phase_label`, so gear tiers would
silently blend Phase 1 and Phase 2 the moment `season_config.py:69` is bumped — its own
docstring predicts it at `:350-355`. **Owner decision 2026-08-06: derive `phase_label`, do
not blend and do not refuse.** Full reasoning in `ADDENDUM_3E_to_3F.md` §2.2. It does not
have to land before Saturday — the crawl refuses correctly on its own — but it has to land
before anyone reads a gear tier after the flip.

---

## Block A — repair the instruments (one commit, before anything writes)

Everything here is a guard, a warning, or a manifest field. **No damage arithmetic
changes.** The gate must read identically before and after this commit.

**F1 — Rewrite `check_gate_exclusion.py` against the frozen cohort. Do not repair the
signature.**
`:126,140,160` pass `limit=120` to a function that no longer takes it, and `candidates()`
now returns a 3-tuple, so `[r[0] for r in before]` is wrong even with the kwarg fixed. More
importantly `inject_privileged_character()` mints the intruder at `character_id 1` **on
purpose** (`:74-79`), because the old `candidates()` was `ORDER BY character_id LIMIT N`.
Under a frozen id set that character can never appear **whatever its `source`** — so the
positive assertions at `:143-152` would pass for a reason unrelated to
`EXCLUDED_SNAPSHOT_SOURCES`, and the control arm at `:164-168` ("without the filter the
SAME character DOES enter") would fail.

The rewrite injects the privileged character **at an id that is inside
`cohort_frozen_3e.json`**, so that `source` is the only thing that can exclude it. Then
both arms mean what they say. State in the test's own docstring what mutation makes it
fail — reverting `EXCLUDED_SNAPSHOT_SOURCES` to empty must turn it red.

🛑 `EXCLUDED_SNAPSHOT_SOURCES` itself (`calibrate_crawled.py:191`) **is not touched**. `3f`
repairs its guard, never the filter.

**F2 — Move the `CP_PER_BUILDER_CAST` disclosure out of the health branch, and emit it from
`medium_sim` too.**
`tiers.py:379-385` is nested inside `if window < 1.0:` (`:371`), the execute-window branch.
`_health_gate` only matches `target_health_pct_below`, and **`apl_gen` never emits that
condition** — `ENGINE_BUGS`' own E2 entry says so. So for every auto-generated APL, i.e.
every gate run and every fixture run, the warning never fires while the constant scales
finisher cast counts at `:367`. **The gate runs on `fast_sim`**
(`calibrate_crawled.py:73,658,662`).

Move it under `if cp > 0:` (`:352`), before the `window` multiply so it reports the
CP-limited count rather than the health-scaled one, and add the equivalent emission in
`medium_sim` at `:562-563`, which currently applies the same hypothesis with no warning at
all. Drop the `cp == 0` case, which prints "held to 0 combo points" and means nothing.

This is a **rule-2 violation** currently asserted as satisfied in four places —
`tiers.py:44-46`, `ENGINE_BUGS.md:74-76`, `seed_epistemics.py:235`, `PROGRESS.md`. Fix the
code, then make those four sentences true rather than deleting them. Note in passing that
`BASE_GCD` (`tiers.py:34`) emits no warning either, and the docs claim it does; decide
whether that is a second fix or a doc correction, and say which.

**F3 — Make three harness checks falsifiable.**
* `check_sim_engine.py:658` — `warned = any("health" in w.lower() …)` is a **constant
  `True`**: B5 appends `EXECUTE_GATING_UNAVAILABLE` unconditionally (`tiers.py:425,635`)
  and its text contains `AURA_STATE_HEALTHLESS_20_PERCENT`. Revert `_decay_target_health`
  entirely and the check still passes — and E2 was removed from `EXPECTED_FAILURES`
  (`:62-69`) partly on that pass. Assert on the *decay behaviour* (target health at
  `t = fight_duration/2` is not 100), not on a substring. Also narrow `hp_gated`
  (`:653-656`), which currently accepts `health_pct_below` — a self-sustain heal condition
  — as evidence of an execute window.
* `check_sim_engine.py:760-778` — both sides call `detect_summons` on the same ids, so
  `pet_warned` is *necessarily* true given the vacuity guard. Assert that the **detector**
  finds the fixture's known summon by spell id, which is a real property.
* `check_sim_engine.py:555-565` — `_filler_ids` classifies on `cooldown_seconds` while
  `fast_sim` now partitions into `cp_gated` / `bounded` / `unbounded` / `off_gcd`
  (`tiers.py:301-307`), so a cooldown-less pure DoT is allocated first and still counted as
  a filler. The docstring claims the check "cannot drift by re-implementing the rule
  differently"; it now does. Import the partition from `tiers` or delete the claim. Also
  guard the vacuous pass: `len(fillers) < 2 or len(firing) >= 2` passes when `fillers` is
  empty.

**F4 — `session_mismatch()` must say it cannot check on the log side.**
`core/builds/stat_block.py:199-200` returns `None` — the caller's all-clear value
(`calibrate_vs_log.py:620-625`) — when the log filename carries no parseable timestamp. The
block side is handled correctly at `:193-198`; the log side is not, and
`_log_started_at`'s own docstring (`calibrate_vs_log.py:410-412`) states the opposite of
what the code does. Regimes that silently disable it today: `WoWCombatLog.txt`,
`06-08-2026-19.16.56 WoWCombatLog.txt` (day-first), `2026-08-06 19-16-56 …`. And
`2026-02-30-…` raises an **uncaught** `ValueError` at `calibrate_vs_log.py:420`.

Return a "cannot check" string, catch the `ValueError`, and — since `stat_block.py` has no
test anywhere in the tree — add one covering all four states. This is the check the `3e`
record calls *worth more than all the others combined*; it should not be the only one with
no test.

**F5 — Fix the `--stat-block`-only crash.**
`calibrate_vs_log.py:888-889` formats the closing NOTE from `args.ap / args.sp /
args.weapon_min / args.weapon_max` — the flags, not the resolved `stats` dict used
correctly at `:611-614`. On the `--stat-block`-only path those are all `None`:
`TypeError: unsupported format string passed to NoneType.__format__`, unconditional before
`return 0`. So C1's own headline invocation does not complete. **Report in the commit
message whether `3e`'s C5 re-derivation was therefore run with the flags as well as the
block** — if it was, the transcription channel C1 exists to remove was still in circuit for
that measurement, and that is worth knowing before the pair ratios are cited again.

**F6 — The frozen cohort has two exits; instrument the second.**
`candidates()` reports drops from the completeness filter well (`:275-333`). The scoring
loop at `:626-668` drops members for a missing preset (`:633`), an unresolvable path
(`:641`), Path of Duality (`:645`) or **any sim exception** (`:666`) into `excluded`, which
never reaches `dropped`, never reaches the manifest, and lands only in gitignored
`data/derived/` (`:977-981`, `:1039`). Meanwhile `:1162` sets
`"still_qualifying": len(tuning) + len(holdout)` — the count of *scored* characters.

Two sim errors therefore produce a committed manifest reading `frozen_size: 41,
still_qualifying: 39, dropped: []`, while stdout `:616` still prints `41 of 41` and the
headline denominator quietly becomes 34. **This was live during `3e`** — Block B rewrote
three sim modules across five commits and any one raising on one crawled build would have
shrunk the denominator invisibly. It happened not to bite.

Fold `excluded` into the manifest (as `dropped` or a sibling `excluded_after_selection`),
and compute `still_qualifying` from `len(rows)`.

**F7 — Per-character slice accuracy has no floor, and the manifest bands have no `n`.**
A2 floored the aggregate only. `:737-739` writes an unfloored per-character value, and
`predictions/gate_manifest_3e.json` ships `Mutaforma` at **1,859,400%** at 0.2% coverage —
the exact value `3e`'s own record cites *as the defect*. `slice_accuracy_by_coverage_band_pct[">=0"]`
ships at 163.7% with no `n` and no caveat, one key away from the good number, and `>=50` is
a median of **8**. The generated report carries `n` (`:917-921`); the artifact an auditor
gets does not.

Either floor the per-character value or annotate it in place, put `n` beside every band in
the manifest, and say in the manifest which you did.

**F8 — Provenance and doc corrections.**
* **One `RETRACTIONS` row for the slice-accuracy sign reversal.** `3e` published the
  reversal in three prose docs and added **zero** retraction rows (`git diff` adds 6
  `QUESTIONS`, 0 retractions; the table holds 32). `/close-session`'s own rule: *"Prose is
  not a seed."* This is load-bearing beyond bookkeeping — `PLAN_3G:113` designates
  `RETRACTIONS` as the ready-made regression set for `3g`.
* **Regenerate `CALIBRATION_TOLERANCE.md`'s band table from the tool.** The committed table
  at `:166-172` is headed "n (3e tuning set)" but its medians are `3d`'s and three of its
  five `n` values match no computation (`ADDENDUM_3E_to_3F.md` §3.4). Paste the tool's
  output; never retype it. Keep the `:174-177` parenthetical, which reproduces exactly.
* **The doc-drift list in `ADDENDUM_3E_to_3F.md` §3.5** — including two documents `3e`
  falsified in-session, and five older docs still asserting the retracted `casts` claim
  unmarked. Also `cli/rebuild.py`'s `--with-corpus` warning still says the cohort is
  `ORDER BY character_id LIMIT N`, which `3e` A1 ended.
* **Amend `PLAN_V2_BLIND_REDERIVATION.md` per the owner's decision** — rescope the scoring
  to v1's open claims, demote the retracted ones to a labelled sanity check, and **retire
  Step 4's flagship outcome** (`:83-85`), which the leak had already suppressed. Keep
  `:86-88` unchanged. Fix `:20`'s "24 rows" → **32**. Add a dated decision header so the
  plan cannot be run in its unamended form. 🛑 **And seed it**: a design decision that
  changes what a test measures goes into `seed_epistemics.py`, not only into a plan
  document — `/close-session`'s own rule, *"Prose is not a seed."*
* 🚨 **`PHASE_4_legos_and_theorycrafter.md` rests on a false claim about the tree** — it
  states *"the web app is a thin layer: `api/` already exists"*, and `api/` is a 12-line
  empty `__init__.py` with zero functions (`AUDIT_3C_ADVERSARIAL.md` §4.L, still true at
  HEAD). This is not doc tidiness: it is a future phase's premise resting on something that
  is not there, and Phase 4 is the phase after this one. Correct the premise. If the
  layering `cli → api → core` is still wanted, say that `api/` must be **built**, and size
  it — do not let "already exists" survive into planning.
* **`ENGINE_BUGS.md` corrections** (`ADDENDUM_3E_to_3F.md` §3.3): Blizzard `305 → 4` casts
  — measured, Elric's `SPELL_CAST_SUCCESS` on Blizzard in Window C is 4, delivering 9.4% of
  that window's damage; the 305 is a raw grep line-count and 83 of those lines are a
  Scarlet Sorcerer's. Plus E7's contradictory `Check │ none yet` row, and E8, which has
  genuinely no check.

**F8b — Derive `phase_label`, and give `gear_tier_stats()` a phase parameter.**
*Lettered because it was added to Block A after the block was numbered, and because it is
the only item here with an external deadline.* ✅ **Owner decision 2026-08-06**
(`ADDENDUM_3E_to_3F.md` §2.2) — this is settled; implement it, do not re-open it.

The data is already in hand and this addendum's first draft was wrong to imply otherwise:
every snapshot carries a capture timestamp (PHASE_3 exit criterion 6 is MET —
`corpus.py:53,113,123`), and `/api/phases` carries each phase's `started` date, which
`crawl_ascensionlogs.py:315-321` **already fetches** to run its own assertion. So
`phase_label` is a join, not a new source.

🛑 **Derivation rules, because a stamped value is load-bearing:**
* A snapshot whose capture timestamp resolves to **exactly one** phase window gets that
  label. Anything else — ambiguous, out of range, missing timestamp — gets **NULL** and is
  **excluded** from a phase-scoped query. Never assigned to the nearest phase. Rule 2.
* `gear_tier_stats()` reports how many rows it excluded and why. A phase-scoped BiS built
  from a silently reduced population is the mixed-phase failure wearing a different coat.
* Delete the hardcoded caveat string at `gear.py:409` once the function can actually
  partition. A printed caveat that is no longer true is worse than none, and this project
  has now found four caveats that were printed and not enforced.
* The phase boundary comes from the **live `/api/phases` response**, cached with its fetch
  time, not from a literal date typed into a constant. `season_config.py` is the one place
  that knows the expected phase; it is not the place to hardcode 2026-08-08.

**F8c — Classify every document in `primer/`. Additive only; delete nothing.**
*Also lettered because it was appended after the block was numbered.*

**The defect is not that `primer/` holds 48 files. It is that nothing on a file tells you
which kind of file it is.** Live reference, historical record, superseded, and
point-in-time finding all sit in one namespace with identical formatting, so a session
reading `PLAN_3C_clean_exit.md:363` today gets *"The site's `casts` IS
`SPELL_CAST_SUCCESS`"* as a settled conclusion. The information loss a destructive cleanup
was feared to cause **is already happening**, and it is caused by the absence of labels
rather than the presence of files.

Add one status line at the top of every file in `primer/`, from this set:

| status | meaning |
|---|---|
| `LIVE` | describes the current tree and **must be true today**. Citable as current truth |
| `HISTORICAL` | describes a past state, immutable, **may contain claims that are false today** — and that is correct, not a defect. Never citable as current truth |
| `SUPERSEDED BY <path>` | pointer only; read the successor |
| `FINDING <date>` | point-in-time analysis; true as of its date, not maintained |

Rules for the pass:

* 🛑 **Additive only.** No deletions, no moves, no subfolders, no path changes, no rewriting
  of historical content. Git history and every existing citation stay intact. The owner's
  concern — that a cleanup could lose something load-bearing — is well founded against a
  destructive pass and does not apply to this one. Keep it that way.
* 🛑 **A file whose status you cannot determine is flagged, not guessed.** Put it in
  `PROGRESS.md`'s blocked table with your best reading and why you are unsure. Rule 6. A
  document mislabelled `HISTORICAL` becomes invisible; one mislabelled `LIVE` becomes a
  trap. Both are worse than an open question.
* **`HISTORICAL` files keep their wrong claims** — do not rewrite them. But a claim that
  also appears in the **retracted-claims list** gets an inline marker *at the claim*,
  pointing at the retraction. That is the same sweep as `ADDENDUM_3E_to_3F.md` §3.5, so do
  the two together.
* **Only `LIVE` documents may be cited as current truth.** Write that rule into
  `primer/START_HERE_FOR_CODE.md` and `CLAUDE.md`, so a document is *born* with a status
  rather than acquiring one in a later cleanup.
* **Every new document declares its expiry condition at birth** — "superseded when X
  lands". `ADDENDUM_3D_slice_accuracy_correction.md` carried a natural expiry (*"before
  `3e` runs"*) that nobody closed, because nothing was watching for one.

**Why before Phase 4 rather than during it.** Phase 4 is the first phase whose output
*leaves* the project — guides and briefs a player reads. A stale claim stops being an
internal cost at that boundary. And Phase 4's own premise is already contaminated: see the
`PHASE_4` bullet in F8.

**Block A acceptance:** the gate reads `5 / 2 / 64.3%` before and after; `check_core_purity.py`
is clean; `check_gate_exclusion.py` **runs** and its stated failure-mutation turns it red;
`check_sim_engine.py`'s three repaired checks each turn red under their stated mutation.

---

## Block B — give the harness teeth (one or two commits)

**F9 — Ground truth in the Frost Mage fixture.**
`ADDENDUM_3D_to_3E_mage_capture.md:141-142` justified preferring a real capture over a
synthetic fixture *"because a synthetic fixture can only catch a crash — it has no ground
truth to be wrong against."* `fixtures/build_elric_frost_mage.json` carries inputs only. So
the Mage arrived as a **third structural fixture**, and **no assertion anywhere in the
harness compares a modelled magnitude to a measured one, on any of the three.**

The numbers already exist in `data/source/captures/2026-08-06_elric_mage_frost/README.md`:
Window A 296,031 player damage / 15,453 pet / 214.2 s, plus per-hit non-crit averages for
seven abilities. Add a `ground_truth` block to the fixture, sourced from the capture with
its `evidence_ref`, and assert against it.

🛑 **Pre-register the tolerance before you see the result.** Write the tolerance and the
reason for it into the fixture in one commit, run the assertion in the next. A tolerance
chosen after seeing the miss is the same failure as moving a gate after seeing its number,
and it is the failure this project has spent three sessions building machinery against.
Expect it to fail — the sim under-produces by roughly a third on what it models, so a
tolerance that passes today would have to be very loose. **A failing ground-truth
assertion, registered, is the correct outcome.** Record it in `EXPECTED_FAILURES` with the
number, not as a pass.

Then do the same for the combo-point fixture if — and only if — a measured magnitude exists
for it. It does not today (`ADDENDUM_3D_to_3E:144` still says so), so the honest outcome is
a named gap, not an invented target.

**F10 — Register four new engine defects. Do NOT fix them.**
`3d`'s D3 discipline: `bugs/` entries first, fixes second. Each of these is a real defect
found in the code `3e` wrote, each would move the gate, and each therefore belongs in a
modelling session with a before/after pair — not here. Register with a check that **fails**:

| id | defect | evidence |
|---|---|---|
| **E9** | `medium_sim` uses a **third** DoT discriminator — `dur and tick_interval_seconds` (`tiers.py:583`) — while `apl_gen.py:75` and `tiers.py:220` use `_is_pure_periodic`. `apl_gen.py:73` claims "the two layers cannot drift apart" and `1c07bab`'s message asserts `:583` uses the same test. It does not. An ability with a periodic aura at `EffectAmplitude 0` lands in the **maintained tier at the top of the APL**, is routed to `st.buffs`, has `debuff_remaining()` return `0.0` forever, and wins every priority scan — the Seal-of-Command 47-of-47-GCDs failure re-created | `tiers.py:583`, `apl_gen.py:73-75`, `mechanics.py:320-324,584-585` |
| **E10** | Target-health decay divides by `st.fight_duration` while the timeline is bounded by `available = fight_duration × (1 − movement_pct)`, so target health **floors at `100 × movement_pct`**. On `world_boss` (0.20) `target_health_pct_below: 20` is permanently false in `medium_sim` — E2's original symptom, unfixed on that profile — while `fast_sim` credits 20% of casts | `tiers.py:117-129` vs `:114,521,529`; `content.py:120-162` |
| **E11** | `self_health_pct` is declared (`tiers.py:471`), read (`apl.py:147`) and **written nowhere**. `apl_gen.py:132-139` emits `health_pct_below` for every heal under `self_sustain_required`, so those entries can never fire in `medium_sim`, while `fast_sim`'s `_health_gate` does not match the condition at all and casts them at full rate. E2's twin, on the player side, unfixed and unnamed while E2 was closed | `tiers.py:471`, `apl.py:147`, `apl_gen.py:132-139`, `content.py:143,161` |
| **E12** | `roll_hit`/`roll_cast` never received `combo_points` (`ability_model.py:796-797`), so `slow_sim` builds its skeleton from `medium_sim` at 5 CP and rolls every cast at 0 CP (`tiers.py:809-810`). The docstring at `:784-785` still asserts convergence "asserted by check_sim_engine.py"; that assertion (`:253-269`) runs at `combo_points=0` and passes vacuously | as cited |

Also worth a line each in the registry, without checks: `_is_pure_periodic` returning
`False` on an empty or raising `events()` (`tiers.py:181-184`) — the fail-open default is
the *over-counting* one; the `starved` warning asserting a cause it did not check
(`:408-415`), which can print alongside its own contradiction nine lines later; the
first-match-wins `_cp_gate`/`_health_gate` on duplicate spell entries; the unvalidated
`combo_points_at_least` value; the silent quadratic CP multiplier (**25× at 5 CP**,
`ability_model.py:487-499`) whose warning fires only when it is *not* applied; combo points
granted from idle scans and off-GCD entries (`tiers.py:561-563` before `:604`); the
duplicated pet warning (`:636-643`); and `stat_block.py`'s last-wins silent merge of two
concatenated blocks (`:74-103`) — which is the contamination shape that module exists to
prevent.

---

## Block C — PHASE_3 T6, log ingestion

**This is the session's purpose and the largest single source of owner toil.** Trace it
today: ALC → `WoWCombatLog.txt` → `parse_log.py` → `*.summary.json` → **`.gitignore`
excludes it** → nothing reads it. `calibrate_vs_log.py` prints to stdout.
`prediction_outcomes` is populated only from hand-written `seed_predictions.py`. **Every
log finding in this project survives solely as prose a human typed into a seed file.**

Most of it already exists. `AUDIT_3C` overstated the gap and `3e`'s record corrected it:
the parser is Ascension-verified, the correlation rule is fully specified and seeded, and
the glob is implemented.

**F11 — mtime windowing and UTC conversion.**
`grep -rn "st_mtime\|getmtime" --include=*.py` returns **zero** hits tree-wide. The rule is
already seeded verbatim at `seed_confirmed.py:47` and is unusually complete — read it
before writing a line:
* window start = filename timestamp, verified exact against the first in-file event;
* window end = file mtime, verified exact against the last in-file event;
* a capture at local time `T` belongs to the log whose `[start, end]` contains `T`;
* 🛑 **in-file timestamps carry no year** — the filename is the only year source;
* 🛑 **all log times are LOCAL while the crawler stamps UTC** — convert before comparing;
* 🛑 **mtime is filesystem metadata and can be rewritten by backup/sync tools** — use it to
  shortlist, then **confirm from the last in-file event** before committing a correlation.
  A correlation that could not be confirmed must say so, not fall back to mtime alone.

And from `seed_confirmed.py:164`: **the log is comma-separated and Ascension spell names
contain commas** — *"Earth, Wind, and Fire"* was truncated to *"Earth"* by a naive split.
Quote-aware CSV only. `combat_log_parser.py` already does this; anything new must not
reintroduce it.

**F12 — The writer.**
Into `builds.db` and `prediction_outcomes`. Requirements, all of them non-negotiable
because this is the first automated writer of tier-1 evidence:
* Every row carries provenance: `evidence_ref` pointing at the capture folder, patch,
  realm, season — the `spell_scaling` provenance failure (`AUDIT_3C` §4.C) is the
  cautionary case and it took two sessions to unwind.
* 🛑 **Every row the writer creates gets a `source` that `EXCLUDED_SNAPSHOT_SOURCES`
  excludes.** The Mage needs the same exclusion Elric got — `FINDINGS_mage_capture`'s
  closing 🛑 says so, and it is easier to forget the second time. F1's rewritten guard is
  the thing that will catch a mistake here; run it after the writer lands, not before.
* A correlation the rule could not confirm is **written as unconfirmed or not written**.
  Never defaulted. Rule 2.
* The writer is idempotent on re-run over the same capture folder, and says what it skipped.

**F13 — Wire it into the chain.**
`build_builds_db.py` reached the chain in `3d` as `--with-corpus` (`cli/rebuild.py:108`),
which is good — but its printed warning still describes the cohort as `ORDER BY
character_id LIMIT N`, ended by `3e` A1. Correct that text, and state where the log
ingestion step sits relative to it.

---

## Block D — close-out

Session record, `PROGRESS.md` pointer, `ENGINE_BUGS.md` updated, final gate manifest.
Report the gate pair for **every** commit, and state plainly that `3f` was not expected to
move it. If it moved, that is the session's headline and everything else is secondary.

**Do not read the holdout.** `3f` makes no modelling change, so there is nothing for it to
validate; reading it spends a pre-registered resource for no information. The holdout is
read again when a modelling session closes.

---

## Settled owner decisions — implement, do not re-open

Both were taken 2026-08-06, **before either was tested against a result**, which is the
whole point. Reasoning is in `ADDENDUM_3E_to_3F.md` §2.2 and §3.2.

1. ✅ **`gear_tier_stats` → derive `phase_label`.** Not a blend, not a refusal. Task F8b.
2. ✅ **`PLAN_V2` → rescope the scoring** to v1's open claims; retracted claims become a
   labelled sanity check; Step 4's flagship outcome is retired. Task F8. **v2 does not run
   until the amendment and its seed row are committed.**

---

## Stop-points — ask, do not decide

1. 🛑 **F9's ground-truth tolerance**, if the pre-registered value has to be looser than
   ±50% to be meaningful. At that width, say what the assertion is still able to catch
   before adopting it.
2. 🛑 **Anything that changes the gate's definition** — a coverage floor on
   `within_tolerance`, a cohort edit, a tolerance change. The 20% successor floor is
   already stamped for a *future* gate and takes effect on its stated date; `3f` neither
   applies it early nor moves it.
3. 🛑 **If F8b's phase derivation is ambiguous for a material share of snapshots** — say,
   more than a few percent land NULL — stop and report the share before proceeding. A
   phase-scoped gear tier built on a quietly halved population is the failure the decision
   was taken to avoid.
4. 🛑 **If Block C cannot land whole**, say so and stop at Block B's close-out. A
   half-built writer that has already written rows is worse than none, because the rows
   are indistinguishable from correct ones.

---

## Exit conditions

`3f` is done when all of these hold:

1. The gate reads `5 of 36 / 2 qualified / 64.3% at ≥20%` at every commit, unchanged.
2. `check_gate_exclusion.py` runs, tests what it claims to test, and turns red under a
   stated mutation.
3. The three repaired harness checks each turn red under a stated mutation, and each
   mutation is written down in the registry.
4. `session_mismatch()` has a test covering all four states, and the log-side "cannot
   check" path is one of them.
5. The committed gate manifest cannot report a cohort it did not score.
6. The Mage fixture carries ground truth with a pre-registered tolerance, and its result —
   pass or fail — is recorded as a number.
7. E9–E12 are registered with failing checks and **are not fixed**.
8. A log lands in `builds.db` and `prediction_outcomes` through code, with provenance, an
   excluded `source`, and a confirmed correlation — or Block C is declared spilled, whole,
   with its reason.
9. One `RETRACTIONS` row exists for the slice-accuracy sign reversal.
10. `phase_label` is derived, unresolvable snapshots are NULL and excluded with a reported
    count, `gear_tier_stats()` takes a phase, and `gear.py:409`'s stale caveat is gone.
11. `PLAN_V2` is amended per the owner's decision, carries a dated decision header, says
    32 not 24, and the rescope exists as a seed row rather than only as prose.
12. Every file in `primer/` carries a status line; nothing was deleted or moved; any file
    whose status was unclear is in `PROGRESS.md`'s blocked table rather than guessed at;
    and `START_HERE_FOR_CODE.md` + `CLAUDE.md` carry the born-with-a-status rule.
13. `PHASE_4`'s *"`api/` already exists"* premise is corrected.

---

## Explicitly out of scope

* **Any fix to E9–E12, or to the smaller defects listed under F10.** They move the gate.
  They belong in a modelling session with a before/after pair.
* **`PLAN_3G` itself.** It follows `3f`. When it is written, amend it first per
  `ADDENDUM_3E_to_3F.md` §3.1 — its current specimen list names one instrument that is
  already fixed and none of the ones that are not.
* **Back-filling the six `ContentProfile` presets.** They stay declared as assumptions.
  `3e` correctly declined when C4 did not land; `3f` does not get to either.
* **Touching `EXCLUDED_SNAPSHOT_SOURCES`, the frozen cohort, or the holdout slug.**
* **The caster buff layer (`3e` C3) and the dungeon `ContentProfile` (`3e` C4).** Both are
  blocked on `calibrate_vs_log` running on a non-paladin log, which is `PLAN_3G`'s
  territory. Its refusal is fail-closed and correct; do not weaken it to unblock them.

---

## Standing rules — in force, and one new

* **Every coverage task reports slice accuracy before and after.** (`3d`)
* **The holdout is named before the work, not after.** (`3d`)
* 🆕 **Every check carries a registered test that makes it fail.** Already `PLAN_3G:111-112`;
  promoted to standing now because it is the single rule that would have caught three of
  the four fail-open instruments the `3e` audit found, and adopting it early gives `3g` a
  populated registry to formalise instead of an empty one. When you add or repair a
  `gcheck`, name the mutation that turns it red. **If you cannot name one, it is not a
  check.**
* 🆕 **A magnitude never appears in a markdown file except as generated output, pasted
  with its provenance.** Evidence: *every* numeric error the `3e` audit found in a document
  was hand-transcribed — the `1.718` pair target, `CALIBRATION_TOLERANCE.md`'s `n` column,
  "Blizzard 305 casts", `PLAN_V2`'s "24 rows". **Four for four. Zero errors in numbers a
  tool emitted.** This is the same defect class as `3e`'s C1: four hand-typed stat flags
  were the transcription channel that contaminated a calibration, and C1 fixed
  transcription **into the simulator** while leaving transcription **into the
  documentation** unguarded. If a number belongs in a document, have the tool print it and
  paste the tool's output — as F8 already requires for the band table, now generalised.
