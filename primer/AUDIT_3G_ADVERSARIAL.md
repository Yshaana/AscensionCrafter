# `3g` adversarial audit — the code is right and the documents are two sessions behind

> **`FINDING 2026-08-07`** — an adversarial audit of session `3g`, true as of its date and
> not maintained. Expires when `3h` closes or refutes its items. Audited from a fresh
> `--depth 40` clone at `b5425cc`, tree-only; `data/derived/` is gitignored, so every
> number below is either read from a committed file or derived from source, never from a
> gate run.

---

## 0. Verdict in six lines

**`3g` is the strongest session in the sequence, and the engine work is correct.** I tried
to break E13 and E14 at the boundary and could not: `probabilities()` returns fractions,
the one consumer that used to divide by 100 no longer does, the multiply site is untouched
and documented as to why, and E14 reads each component's own duration through the join the
card always used. Every claim I could check about the code held.

**What did not survive is the documentation layer.** The two `LIVE` documents that a new
chat is told to cite as current truth — `primer/ENGINE_BUGS.md` and, by default,
`predictions/CALIBRATION_TOLERANCE.md` — both still describe the pre-`3g` world, and one of
them contradicts the session record's own claim that it was corrected. `3f` F8c built a
lifecycle for documents; `3g` shows the lifecycle stops one directory short of where the
gate's numbers live.

**And one measurement problem is structural, not clerical:** coverage counts abilities the
sim produced zero damage for, which means the headline `20.5%` conflates *magnitude error*
with *zero production* — two different defects with two different fixes.

| | |
|---|---|
| Engine fixes (E13, E14) | ✅ correct, verified at file:line |
| Instruments (G0, G4, G5–G9) | ✅ correct; one scope hole (A6) |
| Discipline (pre-registration, one cause per commit, holdout read once) | ✅ clean |
| `LIVE` documents | 🚨 two are stale, one demonstrably against the record's own claim |
| The headline metric itself | 🟠 derived, not measured, and its denominator is wrong |

---

## 1. 🚨 `ENGINE_BUGS.md` still says E13 and E14 are unfixed — in the file whose status line forbids exactly that

`primer/ENGINE_BUGS.md:3` classifies the file **`LIVE`**: *"Must be true today, and is
citable as current truth. If you find a claim here that the tree contradicts, that is a
defect in this file."* Line 17: *"**Every entry here is a FAILING CHECK** in
`tools/audit/check_sim_engine.py`. They are registered in that file's `EXPECTED_FAILURES`
map."*

`3g` fixed both defects and correctly removed both from `EXPECTED_FAILURES`
(`check_sim_engine.py:167-175`, with the reasoning spelled out). It then did not touch
either entry in the registry document.

| where | what it still says | what is true |
|---|---|---|
| `ENGINE_BUGS.md:702` (heading) | *"E13 — every white swing **is** ~78x over"* | fixed at `7af0195`; and the factor is **exactly 100**, not ~78 |
| `ENGINE_BUGS.md:723` | *"multiplies every white swing by ~78"* | ditto |
| `ENGINE_BUGS.md:736-741` | *"🛑 **DELIBERATELY NOT FIXED IN `3f`** … **It is the first thing that session should do**"* | it was the first thing `3g` did |
| `ENGINE_BUGS.md:746-747` | *"whether any other consumer of `probabilities()` makes the same unit assumption (`grep -rn …`)"* | done, tree-wide, in `3g` G1 |
| `ENGINE_BUGS.md:751` (heading) + `:787-790` | *"🛑 **NOT FIXED IN `3f`** … Any fix … should refuse and warn"* | fixed at `6c62309`, and by stopping the mixing rather than refusing |

🛑 **This is a falsifiable contradiction of the session record, not a tidiness complaint.**
`Session_2026-08-07_3g_explosions.md` states: *"🛑 **THE FACTOR IS 100, NOT ~78.**
`ENGINE_BUGS` and the `3f` record both said ~78× … **Corrected in `ENGINE_BUGS`.**"*
`grep -n "78" primer/ENGINE_BUGS.md` returns lines 702 and 723, unchanged. **A correction
reported as landed and not landed is the precise failure mode `3d` found three instances of
and `3f` F8c was built to prevent.**

Every other closed entry in the file carries the treatment: `## E1 … — ✅ FIXED (3e B4)`,
`## E6 … — ✅ FIXED (3e B1)`, each with a closure box saying what happened. E13 and E14 have
neither, so a reader scanning the headings sees ten entries and cannot tell which two are
history. **It also breaches line 17 directly:** two entries in the file are no longer
failing checks and are deliberately absent from `EXPECTED_FAILURES` — the same breach the
file itself flags at `:495` against an earlier row.

**Fix:** two heading suffixes and two closure boxes, in the shape E1/E2/E4/E6 already use,
plus s/~78/exactly 100/. Fifteen minutes, and it is the first thing `3h` should do because
every later document quotes this one.

---

## 2. 🚨 `CALIBRATION_TOLERANCE.md` is the project's calibration reference and it is one retraction behind

`predictions/CALIBRATION_TOLERANCE.md` is the stamped tolerance document — the file whose
whole purpose is to be the thing you cannot edit to fit a result. Its slice-accuracy section
still reads:

| line | still says | after `3g` |
|---|---|---|
| `:170` | band table `≥20% → 23 → **64.3%**` | **20.5%**, n=23 |
| `:182` | **"The sim UNDER-produces on the slice it does model, by about a third."** | by about **four fifths** |
| `:184-190` | *"At slice accuracy ~62–64% … **both levers have to roughly double**"* | at 20.5%, coverage would have to rise **~4.9×** — and above 100%, so the lever does not exist |
| `:177` | *"the bands read 159.8 / 85.4 / 62.6 / 62.6 / 62.6"* | 40.3 / 23.4 / 20.5 / 16.9 / 16.9 (`gate_manifest_3e.json`) |

🛑 **The file tells you how to keep it current and `3g` did not do it.** `:172` says:
*"Regenerate with `py tools/audit/calibrate_crawled.py` and copy
`result.slice_accuracy_by_coverage_band_pct` out of `predictions/gate_manifest_3e.json`."*
`3g` regenerated that manifest five times and copied nothing out. **The warning at `:172`
is `3f` F8's finding — *"the project's reference table for its own largest retraction did
not describe the run it named"* — and it has now happened to the same table one session
later.**

⚠ The consequence is not cosmetic. `:184-190` is the paragraph that tells the *next* session
where to spend its effort, and at 64.3% it says "both levers have to roughly double,"
which reads as a hard but ordinary programme. At 20.5% the coverage lever is arithmetically
dead: `slice × coverage = 1.0` is unreachable for any coverage ≤ 100% at any slice below
1.0, and at 0.205 the magnitude lever has to carry essentially all of it. **That is a
different instruction to the next session, and the file still gives the old one.**

---

## 3. 🟠 The current gate manifest contradicts itself about the coverage floor — the exact defect G8 removed, in the adjacent key

`gate_manifest_3e.json`, generated at `80a66e9`, ships both of these:

```
criteria_in_force.within_tolerance_coverage_floor_pct   : null
criteria_in_force.successor_floor_effective_from        : "the gate run AFTER 3e (stamped 2026-08-06)"
result.coverage_floor_pct_applied                       : 20.0
```

Source: `calibrate_crawled.py:1282` (hardcoded `None`) and `:1320`. The floor **is** in
force — `:781-784` applies `SUCCESSOR_COVERAGE_FLOOR_PCT` inside `within_tolerance` — and
the generated markdown says so in bold (`:1042` *"APPLIED … in force in every number in this
report"*). Only the machine-readable artifact, which is the one an auditor and any future
gate comparison reads, says the criteria in force carry no floor and that the floor belongs
to some later run.

🛑 **G8's entire premise was that a manifest must not contradict itself** — it shipped one
`scored` for exactly this reason, and the reasoning is written out at `:1294-1302`. The same
session then extended the same dict with `coverage_floor_pct_applied` and left the stale
`null` two keys above it. **`SUCCESSOR_FLOOR_APPLIED_FROM` exists at `:139` and is emitted
into stdout and the markdown (`:868, :898, :1042`) but never into the manifest.**

⚠ **And F6's guard cannot catch it.** The consistency block at `:1477-1491` asserts only
cohort arithmetic (`still_qualifying + dropped == frozen_size`, `scored + excluded ==
still_qualifying`). Nothing asserts that `criteria_in_force` describes the criteria that
produced `result`. That is the assertion F6 is named for and does not make.

**Fix:** `"within_tolerance_coverage_floor_pct": SUCCESSOR_COVERAGE_FLOOR_PCT`, add
`"floor_applied_from": SUCCESSOR_FLOOR_APPLIED_FROM`, and add one line to the F6 block
asserting `criteria_in_force.within_tolerance_coverage_floor_pct ==
result.coverage_floor_pct_applied`. Red mutation: revert `:1282` to `None`.

---

## 4. 🟠 Coverage counts abilities the sim produced ZERO damage for — so `20.5%` measures two different things at once

This is the finding I would not have expected and it is the one that matters most for `3h`.

**The chain, at file:line:**

1. `calibrate_crawled.py:745-746` — `modelled_damage_share(bdb, scope_id, cid, set(res.per_ability.keys()))`.
2. `modelled_damage_share`'s docstring, `:400-402` — *"what fraction came from spells **the sim produced any damage for**"*.
3. `core/sim/tiers.py:496` — `per_ability[sid] = {...}` is written **unconditionally**, for every ability in the loop, regardless of `dmg`.
4. `ability_model.py:918-924` — when `occurrences_per_cast` returns `None` the event is **excluded** from the total and the ability's `expected_cast().mean` can be `0.0`, with the warning *"the number below is a LOWER BOUND, not the ability's output"*.
5. `ability_model.py:735-742` — an ability with no resolving damage event returns `mean=0.0` with *"0 because nothing is KNOWN, not because it does nothing"*.

**So step 2's claim is false.** A key in `per_ability` means *the sim iterated this
ability*, not *the sim produced damage for it*. Every refused and every unresolved ability
is counted as **covered**.

**Why it bites, and in which direction:**

* `slice_accuracy = (100 + delta) / coverage` (`calibrate_crawled.py:806, :825`). Coverage
  is the **denominator**.
* A refused ability adds its full logged damage to coverage and **nothing** to the sim
  total. It therefore raises the denominator and lowers `delta` — it pushes slice accuracy
  down twice.
* 🛑 **`3g` G2 ADDED refusals to this bucket.** E14's fix introduces two new refusal paths
  (`ability_model.py:669-679` no own duration; `:685-691` non-positive DBC sentinel — 92557
  hits it today), plus the sanity limit now applied to the plain periodic branch. Each one
  converts a previously-producing component into a zero while leaving the ability's key in
  place.

**The consequence for the headline.** *"The sim reproduces about a fifth of the damage of
the abilities it models"* is not what `20.5%` measures. It measures the damage of the
abilities the sim **has a key for**, some of which it explicitly refused to model. Those
are two defect families with two different work programmes:

| if the residual is mostly… | the fix is | the evidence would look like |
|---|---|---|
| magnitude error on abilities that DID produce | coefficients, scaling, multiplier stack | per-ability ratios clustered around ~0.2 with few zeros |
| zero production on abilities that were refused/unresolved | resolution, DBC joins, trigger walks | a bimodal split: a mass at 0 and a mass near 1.0 |

**Nothing in the tree distinguishes them, and one query does.** Both sides are already in
hand: `res.per_ability[sid]["damage"]` and `ability_performance.damage_total` are joined on
the same spell id in `modelled_damage_share` today.

**Minimum fix, cheap:** split `modelled_damage_pct` into `modelled_and_producing_pct` and
`keyed_but_zero_pct`, and print the zero list. That alone tells `3h` which programme it is
in, before any modelling work is chosen.

---

## 5. 🟠 Slice accuracy is the last headline number in this project that is INFERRED rather than measured

`3g`'s own closing line: *"every defect worth finding in the last three sessions came from
putting a measured magnitude on the other side of an equals sign, and nothing came from more
careful reasoning about the code."*

Slice accuracy is on the wrong side of that line. It is `(100 + delta) / coverage` — a
whole-character DPS delta divided by a whole-character coverage share. It is **not** a
comparison of per-ability sim damage against per-ability logged damage. It is a ratio of two
aggregates, and it inherits every assumption in both: that the unmodelled remainder
contributes nothing to `delta`, that coverage means what §4 shows it does not, and that the
character's logged DPS window and the sim's fight model describe the same fight.

🛑 **The direct measurement is one function away** and it is the same move that found E13
and E14. For each scored character: join `res.per_ability` to `ability_performance` on spell
id, and emit `sim_damage / logged_damage` **per ability**. Then:

* the cohort's real per-ability accuracy distribution, not a derived median;
* the zero/non-zero split from §4 falls out for free;
* every ability whose ratio is a round number or an order of magnitude is a unit error of
  the E13 family, and E13 was found by exactly this shape of comparison on one fixture;
* the aggregate blindness that hid E13 inside `Ari`'s qualified pass is removed by
  construction.

**This is my single recommendation for `3h`.** It is instrument work, not modelling work,
and this project's measured error-finding rate is set by its instruments.

---

## 6. 🟡 F8c's document lifecycle stops at `primer/`, and the gate's numbers live in `predictions/`

`check_refusals.py :: check_primer_status_census` globs `Path(...)/"primer"/"*.md"` and
asserts no file is unclassified. It is a good check, it is correctly written (earliest-match
bucketing, delimiter required, census printed not typed), and I re-derived its output
independently: **56 files — 13 LIVE / 35 HISTORICAL / 2 SUPERSEDED / 6 FINDING.** Correct.

But `predictions/` is outside it:

| file | status line |
|---|---|
| `predictions/CALIBRATION_TOLERANCE.md` | ❌ none — and it is §2 above |
| `predictions/calib_2026-08-05_2e_poi.md` | ❌ none |
| `predictions/calib_2026-08-06_3c_verified_inputs.md` | ❌ none |
| `predictions/pred_2026-08-05_elric_paladin.md` | ❌ none |
| `predictions/prereg_3g_*.md` (3) | ✅ `FINDING 2026-08-07` — `3g`'s own, correct |

⚠ **And the JSON artifacts have no lifecycle at all.** `predictions/gate_manifest.json` — the
obvious filename, the one `seed_predictions.py:221` names as `cohort_source` — is the frozen
`3d` record and still ships:

```
result.within_tolerance                        : 5
result.criterion_met                           : true
result.cohort_median_slice_accuracy_pct        : 159.79435842518353
```

That median is the project's **formally retracted** number, shipped bare with no `n`, no
band, no caveat and no status field, under the name a reader reaches for first. The
truth lives in `gate_manifest_3e.json` — named after `3e`, holding `3g`'s numbers.
`calibrate_crawled.py:189-191` explains the naming, which is fine as an argument and poor as
a filename.

**Fix:** extend the census walk to `predictions/*.md`; add a `"status"` /
`"superseded_by"` key to both manifests; consider renaming to `gate_manifest_current.json`
with the frozen ones dated.

---

## 7. 🟡 Smaller items

* **Both manifests report `git_working_tree_dirty: true`.** `gate_manifest_3e.json` carries
  `git_sha: 80a66e9` with `dirty: true`, so the sha does not identify the code that produced
  the numbers. The `3f` audit raised this as §3.3 and `3g` did not address it. It undercuts
  the session's best structural property — *"one commit moved the gate for one reason"* —
  because the pairs are not sha-anchored from the repo alone. **Cheap fix:** refuse to write
  a manifest from a dirty tree unless `--allow-dirty` is passed, and record the reason.
* **`CLAUDE.md`'s census is generated-then-pasted** (`CLAUDE.md:171`). It is correct today —
  I re-derived it — but nothing asserts the pasted line equals the printed one, so it is one
  document-landing away from being wrong for the third time. **Fix:** have
  `check_primer_status_census()` also read `CLAUDE.md` and assert the pasted line matches.
  Red mutation: change one digit.
* **`probabilities_pct()` has zero callers** (`combat_engine.py:246`). Correct to add — it
  is what makes the boundary fix a boundary fix rather than a rename — but an untested
  sibling of the function that just produced a 100× error deserves an assertion that the two
  differ by exactly 100. `check_sim_engine.py:874` asserts `probabilities()` sums to 1.0 and
  `segments` to 100; one more line closes the pair.
* **`ContentProfile` presets remain failed, not unverified** — 6 of 8 self-declare
  `provenance="assumption: …"`. Untouched since `3d` named it; still `PHASE_3` exit
  criterion 7. Not a `3g` regression, but it is now the oldest unaddressed exit criterion.
* **`gear_tier_stats(phase=…)` still has no caller**, so `3f` exit condition 10 reads ✅ on a
  function nothing calls. `3g` stated this in the blocked table rather than fixing it, which
  was the right call for a session that had to keep every gate move attributable — but it is
  the second session it has survived.

---

## 8. What is genuinely good, and should not be lost in the above

Stated plainly because the audit above is long and the code is not the problem.

* **E13 is fixed in the only place it could correctly be fixed.** `probabilities()` returns
  fractions (`combat_engine.py:242-244`); `probabilities_pct()` carries the percent case;
  `swings.py:159-163` is untouched with the reason written at the site; `ability_model.py:748`
  dropped its compensating `/100.0`. I grepped `core/`, `tools/`, `cli/`, `ingest/` for every
  consumer of both `probabilities()` and `.segments` and found no fourth caller and no
  remaining unit disagreement. `crit_fraction`/`landed_fraction` genuinely have zero readers.
* **E14 is fixed better than the work order asked, and the departure is argued rather than
  taken.** `ability_model.py:1049-1062` performs the `duration_index → dbc_spellduration`
  join for components; `:660-679` prefers the component's own duration and refuses only when
  it is genuinely absent, naming both spells; `:685-691` refuses the non-positive sentinel;
  `:693-700` applies the sanity limit its sibling branch has enforced since `2b`. The
  reasoning for not implementing the specified refusal was pre-registered at `5872b53`,
  before the fix ran.
* **The E14 assertion states a property, not a mechanism** (`check_sim_engine.py:930-953`),
  and says so — after its first form encoded the refusal the work order specified and would
  have broken when a better mechanism arrived. That is a rare piece of test design.
* **The refusal nobody's corpus reaches is exercised synthetically** (`:958-972`) rather than
  left untested.
* **G0 is the best-built thing in the session.** `phase_guard()` (`phases.py:154-208`) makes
  a positive assertion the horizon rule could not, the declared boundary self-retires, the
  child-phase case is handled and explained, `horizon is None` fails closed, and
  `describe_horizon()` exists specifically so the `None`-format crash is testable without a
  corpus rebuild. `check_refusals.py:498-580` exercises all of it. The production caller
  passes `EXPECTED_PHASE_NAME` (`build_builds_db.py:78-81`) — I checked, because a guard with
  an opt-out parameter is a guard someone will opt out of.
* **G5's insight is the one to keep.** A permanently-red check carries no information *and*
  gets silenced rather than satisfied — a worse outcome than fail-open. And the discovery
  that E12's named green path needed three edits rather than the two the work order
  specified is the strongest argument in the repo for the rule that now sits in `CLAUDE.md`:
  a green path that has only been named is a guess about your own code.
* **The pre-registrations are real.** `prereg_3g_e13.md` at `fb54fd7` predicted 1 of 36,
  qualified 1, slice 20.5% at n=23, all five passers out and `Boomcat` crossing in — one
  commit before the fix. Predicting *which character survives* is not a hedge.
* **The holdout was read once, at close-out, against a prediction committed one commit
  earlier**, and it came back worse than the tuning set. The pre-registration named the
  dangerous direction correctly beforehand.
* **G6's replacement arms are falsifiable**, and the fingerprint approach
  (`check_gate_exclusion.py:71-96, :166-220`) tests what the arms were *for* rather than
  restating them.
* **`EXPECTED_FAILURES` is impeccable.** E13's and E14's assertions were removed on closure
  with the reasoning written at `check_sim_engine.py:167-175` — *"a check that has started
  passing must LEAVE it, or the registry stops meaning 'these are the known failures'."*
  This is precisely what §1 says the *document* failed to do, and it makes §1 a documentation
  defect rather than a discipline one.

---

## 9. What `3h` should do, in order

| # | | why now |
|---|---|---|
| 1 | 🚨 **Land the three document corrections** — `ENGINE_BUGS` E13/E14 closure boxes + `~78 → exactly 100`; `CALIBRATION_TOLERANCE` bands, the "by about a third" line and the "both levers double" paragraph; the manifest's `within_tolerance_coverage_floor_pct`. | §1–3. Sub-hour, zero gate risk, and every subsequent document quotes these. A `LIVE` file the tree contradicts is the failure mode this project spends the most effort on. |
| 2 | 🚨 **Split coverage into producing / keyed-but-zero, and print the zero list.** | §4. Until this runs, nobody knows whether `20.5%` is a magnitude problem or a resolution problem, and those are different sessions. It is a reporting change: no verdict moves, so it can land before any modelling. |
| 3 | 🚨 **Build the direct per-ability comparison** — `res.per_ability[sid]["damage"]` vs `ability_performance.damage_total`, per character, per ability, over the frozen cohort. Pre-register nothing; just measure and look at the distribution. | §5. This is the instrument move that found E13 and E14 both times, applied to the last inferred number in the project. Expect it to find a third unit error; the shape to look for is a ratio that is a round number or an order of magnitude. |
| 4 | **Then, and only then, pick a modelling target** — E9/E11/E12 (green paths run and ready, one commit and one gate pair each) or the residual. | The whole point of 2–3 is that the choice between them should be made from a distribution, not from an aggregate. `3e` chose from an aggregate and the inference was retracted. |
| 5 | **Manifest provenance**: refuse to write from a dirty tree; assert `criteria_in_force` matches `result`; extend the status census to `predictions/`. | §3, §6, §7. Each is a few lines and each closes a hole an auditor found rather than a hole someone imagined. |
| 6 | **`ContentProfile` presets** (`PHASE_3` exit criterion 7, failed since `3d`) and **`gear_tier_stats(phase=…)`'s missing caller** (`3f` exit 10). | Oldest outstanding items. Both are now surviving on being restated rather than closed. |

🚨 **Time-critical, independent of the above:** `season_config.NEXT_PHASE_BOUNDARY` is
`2026-08-08T00:00:00Z` — **tonight**. From that instant `phase_guard()` arms and every
capture at or past the boundary takes no label until the payload models it. That is correct
and intended, but it is the first time the defence fires and **nobody has seen it fire.**
Check on the 8th that: the boundary armed; `phase_label` goes NULL rather than
mis-stamping; and if the flip really happened, `EXPECTED_PHASE_NAME` is bumped and the
corpus re-derived **before** any gear tier is read. The pre-flip baseline capture was
scheduled for 2026-08-07 20:00.

---

## 10. Things I could not check, stated as gaps rather than passed over

1. **Every gate number in this audit is read from a committed manifest, not reproduced.**
   `data/derived/` is gitignored and no `.db` is committed, so 1-of-36, 20.5% at n=23 and the
   holdout's five members are checkable only on the owner's machine. `gate_manifest_3e.json`
   pins them; the corpus behind them remains unauditable from the repo alone. This is `3e`'s
   least-sure item #4, unchanged for four sessions, and it is now the limiting factor on what
   a monitoring chat can verify.
2. **§4's magnitude is unquantified.** I have shown the mechanism at file:line and shown that
   `3g` added refusals into it; I have **not** shown how many cohort abilities are keyed with
   zero damage today, because that needs a gate run. It could be three abilities or a third
   of the corpus, and which one it is changes recommendation 3's expected payoff a great deal.
   Recommendation 2 exists to answer exactly this and is deliberately ordered first.
3. **I did not audit the `3g` mutation registry by running it.** M7–M10 and M20–M27 carry a
   stated `ascension.db` / `builds.db` precondition — `3g` G7's own correction, and it is
   honest — but it means a third of the registry is unreproducible from a clean clone. I
   checked the rows' *claims* against the source and found them consistent; I did not observe
   any mutation turn a check red.
4. **The `Boomcat` result deserves a second look and I could not give it one.** It moved
   `+641.5% → −2.0%` at 82.2% coverage, the highest in the cohort, and then `−2.0% → +0.8%`
   on E14. That is the only row where a fix produced agreement rather than removing false
   agreement, and it is now the entire basis for `1 of 36`. **A single passer at high coverage
   is exactly the shape that E13 taught this project to distrust** — `Ari` was also a
   qualified pass, and it was a 100× error cancelling a large negative one. Recommendation 3
   would settle it per ability; until then `1 of 36` should be read as "one character we have
   not yet decomposed," not as one character the sim gets right.
