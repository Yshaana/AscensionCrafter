# Session `3f` — repair the instruments, and what the repaired instruments found

> **`HISTORICAL`** — the record of a past session or a completed phase. Immutable. It **may contain claims that are false today**, and that is correct rather than a defect — it records what was believed at the time. **Never citable as current truth.** *(Classified `3f` F8c, 2026-08-07.)*

**2026-08-06/07, overnight, unattended.** Work order:
`primer/SESSION_3F_PRIMER.md`. Evidence it rests on:
`primer/AUDIT_3E_ADVERSARIAL.md`, `primer/ADDENDUM_3E_to_3F.md`.
Range: `c942541..HEAD`.

---

## The invariant held, at every commit

> **5 of 36 within ±20% · 2 qualified · slice accuracy 64.3% at coverage ≥20%
> (n=23)**

Reported before and after all **eight** commits, and **identical every time** —
including across a full 21-step `py cli/rebuild.py`, which is the only run that
could have moved it through the seed layer the gate reads. Two stronger checks
than the headline pair: every per-character `delta_pct` and `within_tolerance`
in the regenerated manifest is byte-equal to `3e`'s, and the holdout block is
preserved verbatim.

**`3f` changed no damage arithmetic, and the gate confirms it.**

---

## The headline is not the invariant. It is what the new instrument found.

`3f` was scoped so the gate *could not* move. That was the point — and it means
the session's value is entirely in what the repaired instruments detected.

### 🚨 Two magnitude explosions, supplying **99.6%** of the sim's total on a real capture

F9 put ground truth into the Frost Mage fixture and asserted against it. Until
that commit, **no assertion anywhere in this harness compared a modelled
magnitude to a measured one, on any of the three fixtures** — the exact
limitation `ADDENDUM_3D_to_3E_mage_capture.md:141-142` invoked to justify
preferring a real capture, which then arrived carrying inputs only.

The assertion read **90,202 modelled DPS against a measured 1,382**. Two
defects account for nearly all of it:

| | defect | size |
|---|---|---|
| **E14** | Absolute Zero scores **12,000 ticks per cast** — card duration 12.0s divided by the *triggered* spell's 0.001s tick interval | 6.24M of 6.77M total damage (**92.2%**) |
| **E13** | **every white swing is ~78× over** — `probabilities()` returns percentages (they sum to 100.0) and `expected_swing` multiplies by them as fractions | 0.50M, and see below |

Strip both and the fixture models ~373 DPS against 1,382 — **−73%**, the
ordinary under-production family.

### 🛑 E13 is live inside the calibration gate, and it changes how `3e`'s result reads

**24 of the 36 scored cohort characters carry a melee auto in their top 5 sim
abilities.** One of them is **`Ari` — delta −9.7%, `Melee auto (MH)` its single
largest modelled source, and one of the gate's TWO qualified passes.**

So at least one qualified pass is standing on a 78×-inflated auto-attack. That
is compensating error of a size this project has not previously seen, and it
means `3e`'s central conclusion —

> *"six mechanisms were repaired and the answer did not move, therefore the
> residual is not in the mechanisms"*

— **must be re-read.** The residual may be a large positive error cancelling a
large negative one. An aggregate criterion is structurally blind to exactly
that, which is why the qualified rider was invented; E13 shows the same hazard
one level deeper, *inside* a qualified pass.

🛑 **Neither defect is fixed.** Both move the gate — E13 enormously, and in the
direction of *more* under-production. They are registered with failing checks
per `3d`'s D3 discipline and belong to a modelling session with a before/after
pair. **E13 should be the first thing that session does**, because every other
calibration number in this project is measured against a total containing it.

⚠ **Neither was found by reasoning.** Both survived `3e`'s five-defect sweep,
three fixtures, and a full adversarial audit, because nothing in the repo had
ever multiplied a sim output by a measured one. That is the argument for ground
truth, made by the ground truth.

---

## Block A — the instruments

| task | what was wrong | what it is now |
|---|---|---|
| **F1** | `check_gate_exclusion.py` **could not run** (`TypeError` since `3e` A1) and a signature fix would have made it pass for the wrong reason — it minted the intruder at `character_id 1`, which a frozen id set can never admit *whatever its source* | **Rewritten**, not repaired. It CONTAMINATES a character already inside the frozen cohort, so membership is not in question and `source` is the only variable |
| **F2** | `CP_PER_BUILDER_CAST`'s disclosure sat inside the execute-window branch, which `apl_gen` can never generate — so it never fired in the tier the gate runs on, while **four documents** said it did | Emitted from `if cp > 0:` before the window multiply, and from `medium_sim`, which had no warning at all. `BASE_GCD` gained the warning its docs claimed it had |
| **F3** | Three checks that could not fail: the E2 check was a constant `True` (and E2 was *closed* on it); the pet check asserted a pure function returns the same value twice; `_filler_ids` re-implemented a rule B1 changed while its docstring claimed it could not drift | Each asserts a real property: decay behaviour, summon detection **by spell id**, and the imported partition. Plus a separated vacuity guard — the old condition passed on an *empty* filler set |
| **F4** | `session_mismatch()` returned the caller's **all-clear** when the log filename had no timestamp; `_log_started_at` raised on `2026-02-30` | Returns a "cannot check" string distinguishable from silence; `_log_started_at` is total. **The check `2e` rates above all others finally has a test** |
| **F5** | The closing NOTE formatted the override *flags*, so `--stat-block`-only ended in `TypeError` before `return 0` | Reads the resolved stats. Extracted so a test can call it with every flag unset |
| **F6** | The freeze had **two exits and only one was reported** — scoring-loop losses never reached the manifest | `still_qualifying` / `scored` / `excluded_after_selection`, and **two assertions REFUSE to write a manifest whose members do not add up** |
| **F7** | Per-character slice accuracy unfloored and uncaveated; bands shipped with no `n` | **Annotated in place, not floored** (stated in the manifest), `n` and a `readable` flag per band |
| **F8** | `3e` published a sign reversal in three prose docs and **zero** retraction rows | Seeded. Plus the `PLAN_V2` rescope seeded, the band table pasted from the tool, and five docs carrying the retracted `casts` claim marked |
| **F8b** | `phase_label` written as literal `None` | Derived from `/api/phases`, with a horizon rule |

### 🚨 F5's finding, reported as the work order asked

`3e`'s C1 headline invocation **could not have completed as documented** — the
`--stat-block`-only path crashed unconditionally before `return 0`. Either C5's
re-derivation was run *with the flags as well as the block*, leaving in circuit
the hand-transcription channel C1 exists to remove, or a traceback was ignored.
The repo cannot tell which. **The pair ratios should be re-derived through the
block alone before they are cited again.**

### 🚨 F8b's two findings, neither anticipated by the task

1. **The corpus is not single-phase.** Against the API's own dates, **182 of
   412 snapshots (44.2%)** predate Phase 1's start and belong to **Phase 0**.
   Nothing is unresolvable. Every doc saying "currently all Phase 1" was reading
   the `user_confirmed` seed, whose Phase 1 has a NULL start.
   ✅ But gear tiers filter to `pieces >= 12`, and that population is **216
   Phase 1 / 7 Phase 0** — so scoping costs **3.1%**, not 44%. Quoting 44%
   about gear tiers overstates the disruption by 14×. **Stop-point 3 checked
   and not triggered**: it fires on a material share landing NULL, and zero do.
   The frozen gate cohort is 40 Phase 1 / 1 Phase 0.
2. 🛑 **`/api/phases` does not contain the 2026-08-08 boundary.** It holds
   Phase 0, Phase 1 - Zul'Gurub, and Phase 1.1 (a *child*, and the one whose
   `phase_number` is 2). The only source of 2026-08-08 in the tree is the
   `user_confirmed` seed and `season_config`. So the resolver returns **NULL
   past the payload's own fetch time** — without that horizon rule a post-flip
   capture would be silently labelled Phase 1, which is precisely the failure
   F8b exists to prevent, arriving through the back door.

---

## The deadline item (§0.5), and two more defects in the same path

`baseline_phase1.py` is scheduled **2026-08-07 20:00** against a flip due
2026-08-08, and it inherited the phase tripwire while catching nothing. It now
exits **2** with a banner saying the capture is *no longer possible* and telling
the operator **not** to "fix" it by bumping `season_config` and re-running.

Two further live defects found while testing it:

* **It never called `config.ensure_utf8_stdout()`.** Under Task Scheduler
  stdout is a pipe, Python selects cp1252, and the 🛑/🚨 banner dies on
  `UnicodeEncodeError` **part-way through printing** — exit 1 with a truncated
  message. The guard would have failed exactly where it was needed.
* **`crawl_phases()` writes the snapshot BEFORE it asserts, and `NdjsonWriter`
  appends.** A post-flip run would have appended post-flip data into the
  irreplaceable *pre*-flip baseline, which `load_api_phases()` reads last-wins.
  Found the hard way: this session's own first check did it to the committed
  file (770 → 3476 bytes). Reverted; `main()` now asserts before any writer
  exists. `crawl_ascensionlogs.py` is **not** changed — for the daily crawler,
  recording what the server said that day is defensible.

---

## The new standing rule, and what enforcing it cost

> **Every check carries a registered test that makes it fail. If you cannot
> name the mutation, it is not a check.**

**16 mutations named AND RUN** (`ENGINE_BUGS.md`'s new check registry has the
table). Naming was not enough — **four of my own checks were vacuous on first
writing, and only running the mutation showed it**:

* an in-process `io.StringIO` stderr accepts any codepoint, so the encoding
  assertion could not fail → rewritten to run the script as a **subprocess with
  a piped stderr**, the condition Task Scheduler actually creates;
* a mutation that dropped an *input* id rather than an *output* row left the
  summon check green → rewritten to return rows with **wrong** ids, the case
  the old check structurally could not see;
* a manifest test case exercised only one of two assertions, so the other's
  mutation stayed green → a second case built so the first assertion is the
  only one that can fire;
* E10's check compared `< 20.0` against a floor of **exactly** 20.0 and passed
  on floating-point luck → rewritten to assert the property the docstring
  claims.

And one live bug in a `3f` fix, caught the same way: the holdout carry-forward
**survived exactly one run** before redacting after all — under per-commit gate
reporting it would have destroyed `3e`'s reading the same evening.

---

## Block C — SPILLED WHOLE to `3g`, per stop-point 4

**Nothing was written and no writer was left half-built.** Stop-point 4 is
explicit: *"A half-built writer that has already written rows is worse than
none, because the rows are indistinguishable from correct ones."* The session
reached Block B's close-out with Block C unstarted, which is the outcome the
work order specifies over a partial one.

**What `3g` inherits, all of it Block C's stated preconditions, now met:**

* `check_gate_exclusion.py` **runs**, and proves the exact hazard the writer
  creates — an owner-derived snapshot removes its character from the cohort,
  with a stated reason.
* `session_mismatch()` no longer reports an all-clear it did not test, and has
  a test covering all four states.
* `--all-logs` globbed `"* WoWCombatLog.txt"` (space) while the `2e` folder uses
  `_WoWCombatLog.txt` — **fixed**, it matched nothing there.
* `cli/rebuild.py` now states **where log ingestion sits: AFTER `--with-corpus`,
  never before**, because that step rebuilds `builds.db` from scratch.

**What `3g` still has to do first, and it is not in the work order:**
`parse_log.py`'s summary carries `crit_rate_by_source_ability`,
`avoidance_breakdown` and decoded builds — **no per-ability damage totals**.
`combat_log_parser.py` exposes `parse_log`, `crit_rate_by_source_ability` and
`avoidance_breakdown` only. The writer needs a new aggregation over the parsed
events before it has anything to write.

⚠ **And a trap this session hit, which the writer will hit harder:** Window A of
the Mage capture contains **other players** — a Paladin and a Shaman hitting
nearby dummies, ~2.1M damage between them. Summing "everything that is not the
owner" as pet damage reads **10,463 DPS against a true 1,382**. Any ingestion
must filter by `sourceName` against the character and its named pet, and the
pet's real `sourceName` is `Water Elemental`, not the README's creature name
"Lesser Water Elemental".

---

## F8c — documents get the lifecycle the claims already have

Added to the work order mid-session. **Every artifact in this project has a
lifecycle except documents:** claims get retracted, predictions get outcomes,
bugs get closed with checks, cohorts get superseded — and `primer/` had never
lost or labelled a file.

**53 files now carry a status line: 13 `LIVE` · 32 `HISTORICAL` · 6
`FINDING <date>` · 2 flagged uncertain.** Verified programmatically: zero
files without one. **Additive only** — nothing deleted, nothing moved, no
historical content rewritten; 188 insertions against 5 deletions, and the 5 are
one struck-through sentence.

**Two flagged rather than guessed at** (rule 6 — a file mislabelled
`HISTORICAL` becomes invisible, one mislabelled `LIVE` becomes a trap, and both
are worse than an open question): `PHASE_2_simulation.md` and
`ADDENDUM_3E_to_3F.md`. Both are in `PROGRESS.md`'s blocked table with the
reading taken and why it is uncertain.

**Two rules written into `START_HERE_FOR_CODE.md` and `CLAUDE.md`** so a
document is *born* with a status: it carries one in the commit that creates it,
and it declares its **expiry condition** at birth. Plus the owner's second new
standing rule — *a magnitude never appears in a markdown file except as
generated output* — whose evidence is four-for-four: every numeric error the
`3e` audit found in a document was hand-transcribed, and **zero** were in
numbers a tool emitted.

---

## Corrections to the record

* **Blizzard's Window C cast count: 305 → 4.** The 305 was a raw grep
  line-count and 29% of it was an enemy's. Re-measured here through the
  parser's named fields rather than copied from the audit that flagged it: 283
  parsed events, Elric 200 / Scarlet Sorcerer 83, and Elric's
  `SPELL_CAST_SUCCESS` is **4**, delivering 88,132 of 940,460 spell damage
  (**9.4%**). The conclusion survives — Window C *is* E8-exposed, A→B is not.
* **E7 affects all three fixtures, not two.** `3e`'s *"after B1 and B3 this
  PASSES on cp_melee (1 of 7 → 2 of 7)"* was computed over the drifted
  `_filler_ids` set. Against the partition `fast_sim` actually uses it reads
  **1 of 5** and fails. Withdrawn.
* **`CALIBRATION_TOLERANCE.md`'s band table** was headed "n (3e tuning set)"
  and carried `3d`'s medians; **3 of its 5 sample sizes were wrong**. Pasted
  from the tool, which now emits `n` and a `readable` flag per band.
* **Four of the Mage board's abilities damage through a different spell id than
  the card pressed** — Ray of Frost 984513→984514, Frozen Orb 760021→760028,
  Absolute Zero 285148→285149, Deep Freeze 44666→71791. The seal→judgement trap
  (primer v28), now shown on a caster. Ground truth is keyed on the **logged**
  id with the card id beside it.
* **Two line-number citations were deleted rather than corrected.** Both had
  drifted twice — `ENGINE_BUGS`' `calibrate_crawled` cite read `:70,426`, was
  "fixed" to `:73,465,469`, and was falsified by `3e`'s own A1 *in the commit
  that fixed it*. A line number wrong in two consecutive corrections does not
  earn a third; a grep does not rot.

---

## Exit conditions

| # | condition | |
|---|---|---|
| 1 | Gate reads `5 / 2 / 64.3%` at every commit | ✅ six commits, plus a full rebuild |
| 2 | `check_gate_exclusion.py` runs and turns red under a stated mutation | ✅ M7 → 3 red |
| 3 | Three repaired harness checks turn red under stated mutations | ✅ M8, M9b, M10, all in the registry |
| 4 | `session_mismatch()` tested in all four states | ✅ incl. the log-side "cannot check" |
| 5 | The manifest cannot report a cohort it did not score | ✅ two assertions, both falsifiable (M11a/M11b) |
| 6 | Mage fixture carries ground truth, result recorded as a number | ✅ pre-registered ±25% in its own commit; **failed at +6,427%**, recorded |
| 7 | E9–E12 registered with failing checks, **not fixed** | ✅ and E13/E14 besides |
| 8 | A log lands in `builds.db` and `prediction_outcomes` — **or Block C declared spilled, whole, with its reason** | ⬜ **SPILLED WHOLE** |
| 9 | One `RETRACTIONS` row for the slice-accuracy sign reversal | ✅ |
| 10 | `phase_label` derived, exclusions counted, `gear.py:409`'s caveat gone | ✅ |
| 11 | `PLAN_V2` amended, dated, says 32, rescope seeded | ✅ |
| 12 | Every file in `primer/` carries a status line; nothing deleted or moved; unclear files in the blocked table; born-with-a-status rule in `START_HERE_FOR_CODE.md` + `CLAUDE.md` | ✅ **53 files: 13 LIVE / 32 HISTORICAL / 6 FINDING / 2 flagged** |
| 13 | `PHASE_4`'s *"`api/` already exists"* premise corrected | ✅ and **sized** — 5 thin functions + 5 CLI re-points |

**12 of 13. The one outstanding is Block C, spilled whole and deliberately.**

⚠ Exit conditions 12 and 13 were **added to the work order by the owner at
00:30 on 2026-08-07** (`b4eea78`), mid-session, along with two new standing
rules. Both are done, in `83f3d09`.

---

## Do not read the holdout

Not read. `3f` made no modelling change, so there was nothing for it to
validate. The committed manifest's holdout block is `3e`'s reading, **carried
forward verbatim and stamped with the commit that took it (`c7d2892`)** rather
than being erased — see the commit for `Block A (instruments)` and open
question **Q1** below.
