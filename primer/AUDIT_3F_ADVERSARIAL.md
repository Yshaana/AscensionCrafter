# Adversarial audit — session `3f`

> **`FINDING 2026-08-07`** — point-in-time analysis, true as of its date and **not maintained
> since**. Not citable as current truth without re-checking against the tree. **Expires when
> `3g` closes**, or earlier if any file it cites moves. *(Born with a status line, per `3f` F8c.)*

> 🛑 **CORRECTION, 2026-08-07, made before the owner acted on this document.** The first issue
> of this audit was written against `b4eea78`, which I took for the session HEAD. **It was
> not** — `3f` is **ten** commits, and three landed after my clone: `3610182` (Block D
> close-out), `83f3d09` (F8c + the `PHASE_4` sizing), `9cea1e3` (record update). **§5.1 and
> §5.2 are WITHDRAWN in full**; both were artifacts of auditing a mid-session tree, and their
> subject matter is re-verified at the real HEAD in §5.0 below. **This is the error this
> project's own first rule exists to prevent** — I cloned fresh and then failed to re-check
> that the tree had stopped moving before publishing. `git fetch` before writing is now part of
> this chat's loop.
>
> **§1–§4 and §6 stand unchanged**, and I verified that mechanically rather than by reading:
> `phases.py`, `gear.py`, `check_sim_engine.py`, `check_gate_exclusion.py`,
> `calibrate_crawled.py`, `calibrate_vs_log.py`, `check_refusals.py` and `build_builds_db.py`
> are **byte-identical between `b4eea78` and HEAD**. The three late commits touched
> documentation, `CLAUDE.md`, and the manifest's regeneration stamp only.

**Auditor:** monitoring chat, 2026-08-07. **Method:** fresh clone, code read directly, `3f` =
`23b4d82^..9cea1e3` (10 commits). Two parallel deep-dives (the new/repaired checks; F4–F8b's
implementation), each **running the registered mutations against the tree** rather than reading
the registry table, then every 🔴 re-verified by hand. `check_refusals.py` was executed
end-to-end: **22 of 22 PASS at HEAD**.

**Limitation, unchanged since `3c`:** `data/derived/` is gitignored, so `check_sim_engine.py`,
`calibrate_crawled.py` and `check_gate_exclusion.py` cannot be run end-to-end. Their pure-logic
halves and 11 of the 16 registered mutations were executed; **5 (M7–M10) could not be run from
a clean clone at all** — see §2.6.

---

## 0. Verdict in six lines

1. **The two headline defects are real, and I verified both mechanisms independently.**
   `AttackTable.probabilities()` returns percentages by its own docstring
   (`combat_engine.py:214-220`) and `expected_swing` multiplies by them as fractions
   (`swings.py:159-163`) — E13. `n_ticks()` divides the *card's* 12.0 s duration by the
   *triggered* spell's 0.001 s tick (`ability_model.py:890-895`) — E14. These are the most
   valuable findings this project has produced in three sessions, and they came from the one
   thing nobody had done: multiply a sim output against a measured one. **The argument for
   ground truth, made by the ground truth**, exactly as the record says.
2. **F9's pre-registration is genuine and provable from git.** `eed2ec1` carries the fixture,
   the ±25% tolerance and its reason, and **no assertion**; the assertion lands in `7a43fe3`.
   The only delta to `gate_manifest_3e.json` in that commit is a regeneration timestamp.
3. **But three of the newly registered defect checks can never turn GREEN from their own
   fix.** E12's gates on a function that does not exist anywhere in the tree; E11's asserts
   on `self_health_pct` after calling a function that only touches `target_health_pct`; E9's
   re-implements the discriminator it is testing instead of importing it. The new standing
   rule is one-sided — it demands a mutation that turns a check **red**, and says nothing
   about the change that turns it **green**. `3g` is the session that has to fix E9–E14.
4. 🚨 **F8b's horizon rule defends against the wrong thing, and the flip is tomorrow.** It
   NULLs captures newer than the *payload fetch time* — but the session's own finding is that
   `/api/phases` **does not contain the 2026-08-08 boundary**. The first post-flip daily crawl
   appends a post-flip payload (`crawl_phases()` writes before it asserts, deliberately), the
   horizon jumps past the flip, Phase 1 is `open_ended`, and post-flip captures resolve to
   **`Phase 1 - Zul'Gurub`**. That is the exact failure F8b exists to prevent, arriving
   through a door the rule does not cover.
5. ~~Two exit conditions were dropped from the exit-conditions table.~~ **WITHDRAWN — I was
   reading a mid-session tree.** All 13 exit conditions are in the record's table at HEAD
   (`Session_2026-08-06_3f_instruments.md:274-288`), 12 ✅ and #8 spilled. **F8c is done, and
   done well**: 53 of 53 files carry a status line, the born-with-a-status rule is in both
   `CLAUDE.md:162-170` and `START_HERE_FOR_CODE.md`, two uncertain files are flagged in
   `PROGRESS.md`'s blocked table rather than guessed. §5.0.
6. ~~`PROGRESS.md` was not touched in `3f`.~~ **WITHDRAWN, same cause.** It is updated at HEAD
   (+144 lines): the pointer reads *"`3f` IS DONE. Next session is `3g`"*, and **2026-08-08 is
   at `:9`, inside the live block**, with the post-flip procedure stated. §5.0.

**Net:** `3f` did the hardest thing on the work order — it built the first instrument in this
project that compares a modelled magnitude to a measured one, and that instrument immediately
found two defects that survived `3e`'s sweep, three fixtures and a full adversarial audit. It
also caught four of its own vacuous checks by running them. That is the standing rule working
as designed. The failures below are of two kinds: **checks that are stuck red rather than
fail-open** (a new shape for this project), and **documentation work that was quietly dropped
from the scoreboard rather than reported as spilled**.

---

## 1. 🚨 The deadline item — F8b does not hold past 2026-08-08

**`core/builds/phases.py:110-114`, `:85-86`, `:99-103`; `ingest/logs_gg/build_builds_db.py:47-48,57,63`**

```python
if horizon is not None and ts > horizon:
    return None, (f"captured {ts:%Y-%m-%d %H:%M}Z, AFTER the phases payload ...")
```

The horizon is **when we fetched the payload**, not **what the payload knows**. Phase 1's
window is `open_ended` with `ends_at = None` (`:85-86`), so any capture at or before the
horizon matches it. `latest_phase_windows()` takes the **newest** payload
(`build_builds_db.py:57`).

The record itself supplies the precondition that breaks it (record `:115-121`): *"`/api/phases`
does not contain the 2026-08-08 boundary"*, and (record `:138-144`) `crawl_phases()` **writes
the snapshot before it asserts**, left that way on purpose for the daily crawler.

**Failure scenario, reproduced against the committed 2026-08-06 payload:**

```
phase_windows(payload, fetched_at="2026-08-09T06:00Z")
resolve_phase("2026-08-08T12:00:00Z", w, h)  ->  ("Phase 1 - Zul'Gurub", None)
```

(with the real `2026-08-06T17:23Z` fetch time the same call correctly returns `None`.)

The daily crawler runs at logon, appends a `phases` record, and *then* aborts on
`RealmSeasonMismatch`. The next `build_builds_db.py` labels every capture first seen
2026-08-08/09 as Phase 1, and `gear_tier_stats(phase="Phase 1 - Zul'Gurub")` ranks post-flip
gear as Phase 1 BiS with `snapshots_excluded: 0`.

**Nothing compares the payload's phase list against `season_config.EXPECTED_PHASE_NAME`**, and
the child-phase precedent makes it worse: the server published its last content boundary
(Phase 1.1, `phase_number: 2`) as a **child**, which `phase_windows` correctly drops — so a
Phase 2 published the same way is invisible to the resolver while `assert_phase()` still
passes. `check_refusals.py:455` only ever tests a *pre*-flip horizon.

🛑 **The fix must be a positive assertion, not a horizon:** a capture may only take a phase
label if the payload's own phase set is consistent with `season_config`'s expected phase, and
a capture at or after a known-unmodelled boundary is NULL regardless of fetch time.

**Two smaller defects in the same code:**

* **`phases.py:110` fails OPEN when `horizon is None`** — `resolve_phase("2027-01-01…", w,
  None)` returns `("Phase 1 - Zul'Gurub", None)`. `horizon` is `_parse_ts(fetched_at)`
  (`:87`), which returns `None` on any non-ISO `captured_at`.
* **…and `build_builds_db.py:192` then crashes formatting the message that would report it** —
  `f"(horizon {horizon:%Y-%m-%d %H:%M}Z)"` on `None`. **This is F5's exact crash class,
  reintroduced inside F8b's own code, in the same session that fixed F5.**

**And the phase parameter has no caller.** `gear_tier_stats(phase=…)` (`core/builds/gear.py:372`)
— `grep -rn gear_tier_stats` outside `gear.py` returns only `primer/*.md`. Exit condition 10
reads ✅, but the first person to read a gear tier after the flip calls it with no `phase=`,
gets the blended answer, and the `phase_scoping["note"]` explaining that (`:493-495`) is
discarded with the return value.

**One number stated two ways.** `gear.py:402,414` say **44.2%** of snapshots predate Phase 1;
`gear.py:518` and `build_builds_db.py:44` say **38.6%**. In the session that adopted *"a
magnitude never appears in a markdown file except as generated output."*

---

## 2. The instruments

### 2.1 🔴 Three registered defect checks are stuck RED — no fix can close them

This is a new failure shape for this project. The previous four instruments were **fail-open**:
green when they should have been red. These are the mirror: **permanently red, closable only by
a lie.** The consequence is the same — the check carries no information — and it lands squarely
on `3g`, whose job is to fix E9–E14 and prove it.

* **E12 — `check_sim_engine.py:770`.**
  ```python
  rolled = T._roll_uses_combo_points() if hasattr(T, "_roll_uses_combo_points") else False
  ```
  `grep -rn "_roll_uses_combo_points"` returns **this line only**. `rolled` is permanently
  `False`, so the assertion `rolled or not differs` reduces to *"the finisher's damage does not
  vary with combo points"* — which it does, by design. Threading `combo_points` through
  `roll_hit`/`roll_cast` (the actual defect, `ability_model.py:796-797`) leaves it red. **The
  only way to turn it green is to add a stub named `_roll_uses_combo_points` returning truthy.**
  A check closable by a lying stub and not by the fix.
* **E11 — `check_sim_engine.py:742-747`.** Calls `T._decay_target_health(st2)` and then asserts
  `st2.self_health_pct < 100.0`. `_decay_target_health` (`core/sim/tiers.py:162-173`) touches
  only `st.target_health_pct`; the string `self_health` does not appear in it. The defect is
  real — `self_health_pct` is declared, read at `apl.py:147`, written nowhere — but any correct
  fix (writing it in the `medium_sim` loop, or a `_decay_self_health`) leaves this assertion
  red forever.
* **E9 — `check_sim_engine.py:699-712`.**
  ```python
  routed_as_debuff = bool(ab.fields.get("duration_seconds")
                          and ab.fields.get("tick_interval_seconds"))
  ```
  This **re-implements** `tiers.py:583/635`'s discriminator rather than importing it, against a
  hand-built `_FakeAb` whose `tick_interval_seconds` is `None` — so it is the literal constant
  `False`. Fixing `tiers.py` leaves the check red; swapping in a *different* wrong
  discriminator leaves it red for the same wrong reason. It only goes green on a regression in
  `_is_pure_periodic`. **This is the exact drift F3's own `_filler_ids` repair condemns
  (`check_sim_engine.py:638-650`), rebuilt three functions later in the same commit.**

🛑 **Recommended amendment to the new standing rule, for `3g`:** *"Every check names the
mutation that turns it red"* is half a rule. A defect check must also **name the change that
turns it green**, and that change must be the fix, not a stub. Add the green-path column to the
registry and re-derive it for E9, E11, E12.

### 2.2 🟠 E13 and E14 share one assertion

`check_sim_engine.py:114-123` — both are registered against the single frost_mage aggregate DPS
check. Neither can be closed individually, and the registry's own *"registered + now PASSING →
hard failure"* rule cannot tell which of the two was fixed. Given the record's (correct)
instruction that **E13 goes first**, `3g` needs a per-defect assertion before it starts.

### 2.3 🟠 The F1 rewrite made two of its own arms tautological

`check_gate_exclusion.py`'s **core design is sound and I verified it** — the victim is genuinely
inside the frozen cohort, `contaminate()` changes only `source`, and the control arm is real
(`_completeness_sql` reads the module global at call time, `calibrate_crawled.py:207,237`, and
SQLite treats `s.source IN ()` as constant-false, so emptying `EXCLUDED_SNAPSHOT_SOURCES`
genuinely disables the filter). The exclusion, the drop-reason and the no-other-member-moved
checks are all falsifiable.

Two arms are not:

* **`:163-167`** — `check("the excluded member is not re-reported as 'qualifying but
  unscored'", victim not in after_outside)`. `outside = sorted(qualifying - set(cohort_ids))`
  (`calibrate_crawled.py:280`) and `victim ∈ cohort_ids` by construction, so this is true for
  every value of `EXCLUDED_SNAPSHOT_SOURCES`, every `source`, every mutation. **It was made
  unfalsifiable by the rewrite that moved the victim inside the cohort** — the fix and the
  vacuity have the same cause.
* **`:130-134`** — both conjuncts guaranteed: `victim in cohort_ids` as above, and `n_snaps > 0`
  because `victim` was selected from `encounter_performance` in the first place.

### 2.4 🟠 The execute-window check is still half-vacuous — F3 swapped one always-present substring for another

`check_sim_engine.py:980-984`:
```python
named = any("TargetAuraState" in (w or "") for w in (m.warnings or []) + (f.warnings or []))
gcheck("[cp_melee] the execute window is modelled, or the sim says it cannot model it",
       decays and named, ...)
```
`EXECUTE_GATING_UNAVAILABLE` (`tiers.py:110-112`, whose text contains `TargetAuraState`) is
`warnings.append`-ed **unconditionally** at `tiers.py:468` and `:687`. F3's own comment
(`:950-957`) correctly diagnoses the old `any("health" in w.lower() …)` as a constant `True` —
and replaces it with a different constant `True`. Only `decays` is falsifiable; the detail
string still reports `named` as an independent result.

### 2.5 🟠 A registered mutation invalidated by a fix in the same session — M3

`check_refusals.py:92-95` states verbatim: *"delete the `except season_config.RealmSeasonMismatch`
handler around `crawl_phases()` in `baseline_phase1.main()` … all three assertions go red.
**(Verified 3f.)**"*

**I applied exactly that mutation: all four F0 checks stayed PASS.** The pre-flight
`api_get("/api/phases")` + `assert_phase()` block added **in the same session**
(`baseline_phase1.py:106-113`) refuses at exit 2 before `crawl_phases()` is reached. Only
removing *both* handlers turns anything red (4 red, not 3). The measurement was taken before
the pre-flight existed and never re-run.

The guard itself is correct and I am not asking for it to change — the *registry row* is stale,
and a stale mutation is precisely the thing the new standing rule exists to prevent.

### 2.6 🟡 Mutations that cannot be run where an auditor runs them

* **M2 (drop `config.ensure_utf8_stdout()`) is platform-conditional.** I deleted it and re-ran:
  **0 red**. On POSIX, CPython picks UTF-8 for a pipe regardless (PEP 538/540), so
  `check_refusals.py:130-133` is unfalsifiable on Linux and in any Linux CI. The comment at
  `:106-108` names the Windows condition honestly, so the *(Verified 3f.)* is plausible where
  Code ran it — but the row needs `[Windows only]` on it, because the monitoring chat audits on
  Linux and will see it pass unconditionally.
* **M7–M10 (5 of 16) cannot be run from a clean clone at all** — `check_sim_engine.py` needs
  `data/derived/ascension.db` and `check_gate_exclusion.py` needs `builds.db`, both gitignored.
  *"Every row below was executed against the tree"* is unreproducible for a third of the
  registry, on an owner-gated path. This is the primer's own standing practice — *a code path
  only a gated run exercises can stay broken while everything reports green* — applied to the
  mutation registry itself.
* Related: `check_sim_engine.py` dies on a raw `sqlite3.OperationalError` traceback when the DB
  is absent, where `check_gate_exclusion.py:97-100` refuses with a message. **A guard that
  cannot run must say so.**

---

## 3. F6 / F7 — the manifest

### 3.1 🟠 The two "REFUSE to write" assertions are arithmetic identities

`calibrate_crawled.py:1355` and `:1361`, wired at `:1087`.

`still_qualifying = len(rows)` and `dropped = [cid for cid in cohort_ids if cid not in present]`
(`:274-276`), so assertion 1 reduces to `len(rows) + (len(cohort_ids) − len(rows)) ==
len(cohort_ids)`. `_completeness_sql` ends `GROUP BY ep.character_id` (`:235`), so `rows` is one
row per character and every row lands in exactly one of `results` / `excluded` — assertion 2
reduces to `len(results) + len(excluded) == len(rows)`. The only branch that could break it, the
`seen_chars` dedup at `:666-667`, is unreachable given the `GROUP BY`.

They **are** real regression guards on the caller's wiring — reverting `:1087` to
`len(tuning)+len(holdout)` does turn them red, and `check_refusals.py:310,326` fires them by
passing hand-forged `n_qualifying`. But the record's *"two assertions REFUSE to write a manifest
whose members do not add up"* claims a runtime invariant, and no data condition can trip them.

**The data half of F6 is correct and I verified it:** all four drop reasons (`:670,678,682,703`)
reach `excluded_after_selection` at `:1282-1284`, and `still_qualifying` is `len(rows)`.

### 3.2 🟡 The manifest carries two different `scored` values

`:1211` sets `result.scored = len(tuning)` (36); `:1279` sets `cohort_definition.scored =
len(tuning)+len(holdout)` (41). **Both ship in `predictions/gate_manifest_3e.json`**, neither
notes the other, and the F6 assertions only reconcile the second. An auditor reading `"scored":
36` and `"scored": 41` in one file gets the self-contradiction F6 exists to remove, in a
different coat.

### 3.3 🟡 The committed manifest does not correspond to any committed state

`predictions/gate_manifest_3e.json` — `git_sha: 7a43fe3`, `git_working_tree_dirty: true`, while
HEAD is `b4eea78`. Self-reported, so the instrument is honest. But combined with `data/derived/`
being gitignored, **the "identical at every commit" invariant remains unauditable from the repo
alone** — unchanged from `3e`'s own least-sure item #4, and now carrying a stronger claim.

### 3.4 F7 — verified correct

`gate_manifest_3e.json` still ships Mutaforma at 1,859,400% **with `slice_accuracy_caveat` as a
sibling key in the same object** (`calibrate_crawled.py:1336-1341`), 13 of 36 annotated; the
policy is stated at `:1240-1246`; all five bands carry `n` and `readable`, computed with the
identical filter as the medians (`:490-509`). *Annotated in place, and it says so* — as the
work order allowed.

---

## 4. F4 / F5 — verified, with one caller-side gap

Both fixes are correct at the layer they touch. `session_mismatch()` returns four distinct
values (`stat_block.py:202-227`); `_log_started_at` is total (`calibrate_vs_log.py:453-456`);
`closing_note(stats)` reads the resolved dict (`:404-426`, called `:931`) and
`resolve_stat_inputs` refuses before it if any value is `None` (`:503-511`). Tests at
`check_refusals.py:163-234` and `:240-264` cover all four states plus `2026-02-30`, and I turned
each red under its mutation.

🟡 **But the caller does not act on the distinction F4 created.** `calibrate_vs_log.py:669-672`:
```python
_mismatch = session_mismatch(block, _log_started_at(_p))
if _mismatch:
    print(f"  {_mismatch}\n    (log: {_p.name})"); break
```
A real mismatch and a *"cannot check"* are handled **identically**, and both differ from
`AlignmentUncheckable` twelve lines later (`:694-699`), which `continue`s and refuses to report
that log — the project's own *"could not check is its own outcome, not a pass."* And the `break`
stops at the first log producing any string, so under `--all-logs` a later log's 34-hour
mismatch is never printed once an earlier one reports "cannot check".

---

## 5. Exit conditions and the record

### 5.0 Re-verified at the real HEAD (`9cea1e3`) — the close-out is sound

Everything §5.1 and §5.2 alleged was an artifact of auditing `b4eea78` mid-session. Checked
against the tree, not against the closing statement:

| claimed | verified |
|---|---|
| F8c classified all 53 `primer/` files | ✅ **53 of 53** carry a status line; `13 LIVE / 32 HISTORICAL / 0 SUPERSEDED / 6 FINDING`, 2 flagged. Additive — no deletions, no moves |
| the born-with-a-status rule landed | ✅ `CLAUDE.md:162-170` **and** `START_HERE_FOR_CODE.md` (+40), both carrying the expiry-at-birth clause |
| `PROGRESS.md` pointer | ✅ `:5` — *"`3f` IS DONE. Next session is `3g`"*; the `3e` block correctly collapsed into `<details>` |
| 2026-08-08 in the live block | ✅ `:9`, with the post-flip procedure (bump `EXPECTED_PHASE_NAME`, re-crawl `/api/phases` **before** reading a gear tier) |
| all 13 exit conditions in the table | ✅ `Session_..._3f_instruments.md:274-288`, 12 ✅ + #8 spilled |
| `PHASE_4` premise | ✅ and **better than asked**. `3d` had already corrected *"`api/` already exists"* (`47bd374`); the outstanding half was my work order's *"say it must be built, and size it"*, and `3f` sized it against the tree: 0 functions in `api/`, 5 of 7 `cli/` entry points import `core/` directly, so the cost is 5 thin functions + 5 re-points **because `core/` purity is real**. The conclusion — *"`core/` is the reusable layer today and `api/` is a reserved name"* — is the honest statement my work order asked for |
| gate reported at every commit | ✅ including the three late ones (`3610182`, `83f3d09`); manifest delta across them is the regeneration stamp only |

**Two things I still hold against the close-out, both small and both new:**

* 🟡 **The live block's own count is wrong, in the session that made hand-transcribed magnitudes
  a standing rule.** `PROGRESS.md:77` says **SIX** questions are waiting; the blocked table has
  **seven** new `3f` rows (F8c's two documents, Q1–Q4, the successor-floor attribution, the
  pair-ratio question) among 12 total; the closing statement to the owner says **eight**. Three
  numbers for one countable thing, in the live block a new chat reads first. It is exactly the
  class the new rule names: *"where no tool prints it, the number has no owner."* Have
  `PROGRESS.md` print the row count or drop the numeral.
* 🟠 **`CHAT_MONITORING_PRIMER.md` is labelled `LIVE`, and it is two sessions stale — which is
  the trap F8c was written to prevent, and it is mine, not Code's.** Under the rule now in
  `CLAUDE.md`, `LIVE` means *must be true today* and *a claim the tree contradicts is a defect
  in the file*. That file still says the session map is *"`3e` modelling → `3f` PHASE_3 T6"*,
  the gate is *"5 of 41"* (it is 5 of 36), the slice correction is *"written and not landed"*
  (landed in `3e` A2), and thread 3's cohort fix is *"`3e`'s first job"* (done). The
  classification is defensible — it *is* the current primer — but the contents are not. **v3 of
  that file is this chat's job before the next monitoring session, not `3g`'s.**

---

### 5.1 ~~🚨 Two exit conditions were dropped from the table~~ — WITHDRAWN

**Withdrawn 2026-08-07: this section audited `b4eea78`, three commits before the session HEAD.
It is kept rather than deleted so the correction is legible.** See §5.0 for what the tree
actually says. The original text follows.

The work order (`SESSION_3F_PRIMER.md:462-486`) lists **13**. The session record's table
(`:243-255`) lists **11** and concludes *"10 of 11."*

| dropped | what it required | state at HEAD |
|---|---|---|
| **#12** | every file in `primer/` carries a status line (`LIVE`/`HISTORICAL`/`SUPERSEDED`/`FINDING`); unclear files in `PROGRESS.md`'s blocked table; the born-with-a-status rule in `START_HERE_FOR_CODE.md` + `CLAUDE.md` | **not done. 0 of 53 files** carry a status line; neither doc carries the rule |
| **#13** | correct `PHASE_4`'s *"`api/` already exists"* premise | **already done by `3d`** (`47bd374`, `PHASE_4:370-380`) — the work order was **wrong** to list it |

F8c's five-file `casts`-retraction sweep **was** done (`AUDIT_3C_ADVERSARIAL`, `AUDIT_3C_handoff`,
`NEXT_CAPTURE`, `PLAN_3C_clean_exit`, `Session_3c_paired_upload`, +15/+25 lines each) — that is
the §3.5 half of F8, not F8c.

**Honest score is 10 of 13, with one work-order error.** #13 is my mistake and I am recording it
as such: `AUDIT_3C §4.L` was cited as *"still true at HEAD"* and it was not. **But a work-order
item that turns out to be already satisfied is reported as satisfied-by-`3d`, not deleted from
the scoreboard**, and F8c was not satisfied by anything. Dropping both rows turns 10-of-13 into
10-of-11, and the shortfall reads as one deliberate spill rather than one spill plus one silent
omission.

### 5.2 ~~🚨 `PROGRESS.md` was not touched in `3f`~~ — WITHDRAWN

**Withdrawn 2026-08-07, same cause as §5.1.** `PROGRESS.md` gained 144 lines in `3610182`. The
original text follows.

`git log -- primer/PROGRESS.md` stops at `7c416d1` (`3e` close-out). Three separate requirements
land on it:

* **Block D** — the session pointer. A fresh chat cloning today reads *"✅ 2026-08-06 — SESSION
  `3e` IS DONE. Next session is `3f`"* and would redo the session. Everything in §0 above is
  invisible to it.
* **§0.5** — *"Put 2026-08-08 back in `PROGRESS.md`'s live block."* Its only Phase-2 line is
  still `:194`, inside the `<details>Superseded</details>` block. **The flip is tomorrow**, and
  the one document a new chat reads first still hides it in a collapsed section.
* **F8c** — the blocked table for files whose status could not be determined.

### 5.3 🟡 Smaller record and hygiene items

* **Three new rotted line citations, in the session that deleted two for *"a grep does not
  rot"***: `stat_block.py:194` and `check_refusals.py:166` cite `calibrate_vs_log.py:620-625` as
  the caller (that is now the `--all-logs` glob; the caller is `:667-672`); `check_refusals.py:169`
  cites `:410-412` for `_log_started_at`'s docstring (that is now `closing_note`'s; the function
  starts at `:429`).
* `check_sim_engine.py:230` still prints *"scheduled for 3e"*.
* `calibrate_crawled.py:1015` truncates the exclusion list at `excluded[:40]` and prints "none"
  only when empty — 41 losses would print 40 silently. Report-only; the manifest carries all.
* Dead code: `check_sim_engine.py:766` (`cs = m.content …`, immediately shadowed by
  `_CS_FOR_E12`); unused import at `:681`.

---

## 6. What is genuinely good, and should not be lost in the above

* **The ground-truth assertion is the right instrument and it worked on first contact.** Two
  defects, one of them supplying 92% of a fixture's damage, survived `3e`'s five-defect sweep,
  three structural fixtures and a full adversarial audit — and fell to the first assertion that
  multiplied a modelled magnitude against a measured one. Both mechanisms verified here
  independently of the record's arithmetic.
* **E13's live consequence is read correctly and not softened.** 24 of 36 scored characters
  carry a melee auto in their top 5; `Ari` is one of the gate's **two** qualified passes with
  `Melee auto (MH)` as its largest modelled source and a −9.7% delta. Concluding that `3e`'s
  *"the residual is not in the mechanisms"* **must be re-read** — rather than defending the
  prior session's headline — is the correct call, and it is the kind of call this project exists
  to make.
* **Both defects were registered and neither was fixed**, per `3d`'s D3 discipline, with the
  right ordering stated (E13 first, because every other calibration number is measured against a
  total containing it).
* **F9's pre-registration is provable from git**, not asserted: tolerance and reason in
  `eed2ec1`, assertion in `7a43fe3`, and the tolerance is justified structurally (zero talents)
  rather than by the size of the miss it had to accommodate.
* **Four vacuous checks were caught by running the mutations rather than naming them**, and the
  record says so plainly. That is the new standing rule paying for itself in the session that
  adopted it — and it is why §2.5's stale row is a lapse rather than the norm.
* **Block C spilled WHOLE**, per stop-point 4, with nothing half-written. The preconditions
  listed for `3g` are real, and the two additional findings handed forward (`parse_log.py` has
  no per-ability damage totals; Window A contains two other players and a pet whose real
  `sourceName` is `Water Elemental`) are exactly what a writer would have got wrong.
* **F6's data half, F4, F5, F7 and F8b's non-horizon parts verified sound.** All 22
  `check_refusals.py` assertions pass at HEAD and every runnable one turns red under its
  mutation. `check_refusals.py`'s F6 construction is the best-built check in the tree: case A
  (`:309-319`) is built so only assertion 1 can fire and case B the reverse, and the mutation
  counts confirm the arms are genuinely isolated.
* **Two line-number citations deleted rather than corrected a third time** — right call, and the
  reasoning (*a line number wrong in two consecutive corrections does not earn a third*) should
  become standing.

---

## 7. What `3g` should do, in order

1. 🚨 **Phase labelling, before or immediately after the flip.** Replace the fetch-time horizon
   with a positive consistency assertion against `season_config`; make `horizon=None` fail
   closed; fix `build_builds_db.py:192`'s `None` format; give `gear_tier_stats(phase=…)` a
   caller or state in `PROGRESS.md` that no phase-scoped read exists yet. §1.
2. **Fix E13 first, then E14**, with a before/after gate pair — as the record says. Split their
   shared assertion first (§2.2).
3. **Give E9, E11 and E12 a green path** before fixing them, and amend the standing rule to
   require one. §2.1.
4. **Re-derive the mutation registry**: M3 is stale, M2 needs `[Windows only]`, M7–M10 need a
   stated "cannot run without `data/derived/`" so a clean-clone auditor is not misled. §2.5–2.6.
5. **De-tautologise** `check_gate_exclusion.py:130-134,163-167` and the `named` half of
   `check_sim_engine.py:980-984`. §2.3–2.4.
6. **Reconcile `PROGRESS.md:77`'s question count against its own table** (six vs seven vs the
   eight in the closing statement), or drop the numeral. §5.0.

~~5. `PROGRESS.md` — the `3f` pointer…~~ ~~6. F8c, un-dropped…~~ **Both withdrawn — done at
HEAD, and my clone was stale. §5.0.**

**And one item that is this chat's, not `3g`'s:** `CHAT_MONITORING_PRIMER.md` is classified
`LIVE` and is two sessions stale. v3 before the next monitoring session. §5.0.
