# SESSION `3h` — measure the residual instead of inferring it

> **`LIVE`** — the work order for session `3h`. **Must be true today, and is citable as
> current truth.** Reclassify **`SUPERSEDED BY primer/Session_2026-08-07_3h_*.md`** at
> close-out. *(Born with a status line and an expiry condition, per `3f` F8c.)*

Predecessors: `primer/Session_2026-08-07_3g_explosions.md` (the session record),
`primer/AUDIT_3G_ADVERSARIAL.md` (the audit this order implements),
`primer/ENGINE_BUGS.md` (the defect registry), `primer/PROGRESS.md` (live state).

---

## §0 — Where things stand, and what kind of session this is

**`3g` was correct and it made the problem bigger.** E13 (every white swing exactly 100×
over) and E14 (12,000 ticks per cast) are both fixed at the boundary, every consumer
accounted for tree-wide, and the gate went **5 → 1 within ±20%**, **slice accuracy 64.3% →
20.5%**. The audit tried to break both fixes and could not.

**The gate today:** `1 of 36 within ±20% · 1 qualified · slice accuracy 20.5% at coverage
≥20% (n=23)`. Holdout, read once at `3g` close-out: **0 of 5, −79% to −98%**, median slice
**9.8%** — *worse* than the tuning set, so 20.5% is the optimistic end.

🛑 **`3h` IS AN INSTRUMENT SESSION. IT FIXES NO ENGINE DEFECT.** `3f` fixed none and found
two errors bigger than anything `3e` touched. `3g` fixed those two and the answer moved by a
factor of five. **This project's error-finding rate is set by its instruments, not by its
effort** — and the audit found that the metric now carrying the whole project is the last
headline number that is *inferred* rather than *measured*.

> 🛑 **THE INVARIANT FOR THIS SESSION: the gate reads `1 / 1 / 20.5%` at EVERY commit.**
> Report the pair on every commit as `3g` did. **A commit that moves the gate is a defect in
> that commit**, not a result — stop and report it. The one deliberate exception is Block D,
> which *measures* a cohort effect and **does not apply it**.

**E9, E11 and E12 are NOT in scope.** They have run green paths and are ready to take one
commit and one gate pair each. They are the *next* session's work, deliberately: `3e` picked
its targets from an aggregate and had its inference retracted, and the aggregate is still
dominated by something none of those three touch. **Choose modelling targets from a
distribution, not from a median.**

---

## §1 — The four things this session must produce

| | | why now |
|---|---|---|
| **A** | The three stale `LIVE` documents corrected | `ENGINE_BUGS.md` says E13/E14 are unfixed, in the file whose status line forbids exactly that |
| **B** | Coverage split into **producing** vs **keyed-but-zero** | until this runs, nobody knows whether 20.5% is a magnitude problem or a resolution problem |
| **C** | The **direct per-ability comparison**, cohort-wide | slice accuracy is `(100+delta)/coverage` — a ratio of two aggregates, never once checked against the per-ability measurement both sides of which are already in hand |
| **D** | `Boomcat` reconciled, and a **parse-admissibility** rule stamped (not applied) | the only passing row is adjudicated by chat-side arithmetic with no implementation, against a column that has never held a value |

---

## Block A — the documents (no code, no gate move)

Full find/replace blocks are in `primer/PRIMER_PATCH_3h.md` (§5 is already applied — do not re-apply it). Land them **first**, in **one commit
that touches no `.py`**, because every later document quotes these.

**A1.** `primer/ENGINE_BUGS.md` — E13 and E14 get the `— ✅ FIXED (3g Gn)` heading suffix
and a closure box in the shape E1/E2/E4/E6 already use; `~78` becomes **exactly 100** with
the reason; the two forward-looking *"NOT FIXED IN `3f`… the first thing that session should
do"* paragraphs are retired.

> 🛑 **This is not tidiness.** The `3g` record states *"THE FACTOR IS 100, NOT ~78 …
> **Corrected in `ENGINE_BUGS`**"* and it was not — `grep -n "78" primer/ENGINE_BUGS.md`
> still returns lines 702 and 723. A correction reported as landed and not landed is the
> failure mode `3d` found three instances of. It also breaches the file's own line-17
> invariant (*"every entry here is a FAILING CHECK … registered in `EXPECTED_FAILURES`"*),
> because `3g` correctly removed both from that map.

**A2.** `predictions/CALIBRATION_TOLERANCE.md` — gets a **status line** (it had none), the
band table regenerated **from the manifest, not retyped**, *"under-produces by about a
third"* corrected, and the *"both levers have to roughly double"* paragraph replaced with
the real arithmetic: at 20.5%, slice must rise **~4.9×** and coverage substitutes for none
of it.

**A3.** `tools/audit/calibrate_crawled.py` — the manifest contradicts itself:
`criteria_in_force.within_tolerance_coverage_floor_pct: None` (`:1282`) beside
`result.coverage_floor_pct_applied: 20.0` (`:1320`), with the floor **in force** at
`:781-784`. Set the key, emit `SUCCESSOR_FLOOR_APPLIED_FROM` (which exists at `:139` and
reaches stdout and the markdown but never the manifest), and **extend F6's consistency block
(`:1477-1491`) with a third assertion**: `criteria_in_force.within_tolerance_coverage_floor_pct
== result.coverage_floor_pct_applied`. F6 is named *"the manifest must not be able to
contradict itself"* and today asserts only cohort arithmetic.
**Red mutation:** revert `:1282` to `None`. **Green path:** the fix. Run both.

**A4.** `CLAUDE.md` — add the admissibility rule (text in the patch, and see D4), and make
`check_primer_status_census()` **assert that `CLAUDE.md`'s pasted census equals what it
prints**. Red: change one digit. ⚠ The census moved **twice inside `3g`** (55 → 56 files);
generated-then-pasted buys one day.

**A5.** Extend that census walk to `predictions/*.md`. Four files there carry no status line,
including `CALIBRATION_TOLERANCE.md`. **F8c's lifecycle stops one directory short of where
the gate's numbers live.**

**A6.** `predictions/gate_manifest.json` — the frozen `3d` record, and the filename a reader
reaches for first — still ships `criterion_met: true`, `within_tolerance: 5` and
`cohort_median_slice_accuracy_pct: 159.79`, the **formally retracted** number, bare, with no
`n`, no band, no caveat and no status field. Add a `"status"` key naming it frozen and
naming its successor. 🛑 **Do not edit its numbers** — it is an immutable record and its
value is that it is one.

**A7.** Both manifests report `git_working_tree_dirty: true`, so the `git_sha` does not
identify the code that produced any gate number (`3f` audit §3.3, unaddressed). **Refuse to
write a manifest from a dirty tree unless `--allow-dirty` is passed, and record the flag in
the manifest.** This is what makes *"one commit moved the gate for one reason"* checkable
from the repo rather than only from the record.

---

## Block B — what `coverage` actually counts

**The chain, verified at file:line by the audit:**

1. `calibrate_crawled.py:745-746` — `modelled_damage_share(…, set(res.per_ability.keys()))`
2. its docstring `:400-402` — *"what fraction came from spells **the sim produced any damage for**"*
3. `core/sim/tiers.py:496` — `per_ability[sid] = {...}` written **unconditionally**
4. `ability_model.py:918-924` — a refused event is excluded; `expected_cast().mean` can be `0.0`
5. `ability_model.py:735-742` — an ability with no resolving damage event returns `0.0`

**So step 2 is false.** A key means *the sim iterated this ability*, not *produced damage for
it*. And since `slice = (100 + delta) / coverage`, a keyed-but-zero ability **raises the
denominator and lowers the numerator — it pushes slice accuracy down twice.**

🚨 **`3g` G2 added refusals into this bucket**: `ability_model.py:669-679` (no own duration),
`:685-691` (non-positive DBC sentinel — 92557 hits it today), plus the sanity limit newly
applied to the plain periodic branch.

**B1.** Split `modelled_damage_share`'s return into `modelled_and_producing_pct` and
`keyed_but_zero_pct`, keeping `modelled_damage_pct` as their sum so **no existing verdict
moves**. Correct the docstring — it is a claim, and it is currently wrong.

**B2.** Emit the **named list** of keyed-but-zero abilities per character (spell id, name,
logged damage share, and *why*: refused-no-duration / refused-sentinel / refused-sanity /
no-damage-event-resolves). 🛑 **No silent caps** — if you truncate the list, print what was
dropped.

**B3.** Report the cohort figure both ways in the manifest and the markdown:
`median_slice_accuracy_pct_at_coverage_ge_20` as today, and beside it the same median
computed over **producing coverage only**. **Do not replace the existing key** — this is
instrumentation, and the criterion's definition does not change in this session.

**B4.** Assertion, with red and green paths **both run**: a character whose every ability
refuses must report `modelled_and_producing_pct == 0.0` and a non-empty zero list. Red:
revert B1's split. ⚠ Name a real ability from the cohort if one exists; if none does, say so
and use a synthetic — an untested split is a split nobody has seen split.

> 🔬 **What B answers.** If `keyed_but_zero_pct` is ~0 across the cohort, §4 of the audit is
> a latent trap and 20.5% means what it says. If it is material, **the headline is
> conflating two defect families** and Block C's distribution is the only thing that can
> separate them. **Report the number before drawing either conclusion.**

---

## Block C — the measurement that replaces the inference 🚨

**This is the session's headline and the reason it exists.**

Slice accuracy is `(100 + delta) / coverage` — a whole-character DPS delta over a
whole-character coverage share. It is **not** a comparison of per-ability sim damage against
per-ability logged damage, and it inherits every assumption in both aggregates. Both sides
are already joined on spell id inside `modelled_damage_share`:
`res.per_ability[sid]["damage"]` and `ability_performance.damage_total`.

**C1.** Build the paired per-ability comparison over the **frozen cohort**, as a new tool
(`tools/audit/per_ability_accuracy.py` or a flag on `calibrate_crawled.py` — your call,
stated). For every scored character × every ability the sim has a key for, emit:

```
character_id, spell_id, spell_name, sim_damage, logged_damage, ratio,
coverage_share_of_logged, key_state (producing | refused:<reason> | unresolved),
attributed (bool), event_kinds
```

🛑 **Include the abilities the sim has NO key for**, with `sim_damage = 0` and
`key_state = absent`. The set the sim never reached is as informative as the set it got
wrong, and excluding it is how coverage came to mean two things.

**C2. PRE-REGISTER, in `predictions/prereg_3h_per_ability.md`, committed BEFORE C3 runs.**
State, in numbers you are willing to be wrong about:

* the expected **shape** — unimodal around ~0.2, or bimodal (a mass at 0 and a mass near 1);
* the expected **fraction of paired abilities at exactly 0**;
* whether you expect **`Boomcat`'s** ratios to cluster near 1.0 or to spread high and low;
* whether you expect to find **a third unit error**, and what magnitude would count as one.

**C3.** Run it. Report the distribution, not a median: histogram of `ratio` over paired
abilities, the same split by `key_state`, and the per-character view for the five highest
coverage members.

**C4. Hunt the unit errors explicitly.** 🔬 **The shape to look for is a ratio that is a
round number or an order of magnitude** — E13 was exactly 100 and E14 was exactly
`card_duration / component_tick`. Flag every ability whose ratio is within 2% of
`{0.01, 0.1, 0.2, 0.25, 0.33, 0.5, 2, 3, 4, 5, 10, 100}`, or within 2% of a plausible
mechanical constant (tick counts, target counts, rank multipliers). **Register what you find
as `E15…` with a failing check; fix none of it in this session.**

**C5.** Reconcile against F9. The frost-mage assertion is the only under-production
measurement in the project with **no coverage term** — a direct DPS comparison against a
same-session verified stat block — and it reads **457 vs 1,382 = 33.1%**, not ~20%. Run C1
on the frost-mage fixture and state whether the per-ability distribution explains the gap.
🛑 **If it does not, say so and register it.** Two measurements of the same quantity
disagreeing by 1.6× is a finding, not a rounding difference.

---

## Block D — `Boomcat`, and the shape of a legitimate failsafe

**`Boomcat` (16501) is the only row in the gate that passes**, at 82.2% coverage — the
highest in the cohort — having moved `+641.5% → −2.0% → +0.8%` across `3g`'s two fixes. It
is either the project's best calibration anchor or `Ari`'s failure one layer over.

**The history:** `3c` retracted it as *"the best clean-qualifier candidate"* on a suspected
**death-deflated parse** (within-character APM ratio **0.24**, against Elric's known death
case at 0.38). `3e` preflight then ruled out the cast-time-caster explanation — 54 of 55
board entries resolve to 0 ms, it is a feral/agility physical kit — so the hypothesis stands
and is unexplained.

🚨 **Two facts make it decisive now, and neither is a modelling problem.**

1. **Death-deflation is structural in your denominator.** `core/builds/corpus.py:614` —
   `dps = (total_damage + pet_damage) / SUM(encounters.duration_seconds)`. That is
   **wall-clock encounter duration, not the player's active time.** A character who dies 40%
   in has real damage divided by the full window: their logged DPS is deflated **by
   construction**. Against a sim that under-produces ~5×, a deflated denominator **flatters
   the delta toward zero.** That is `Ari`'s shape — a compensating error an aggregate
   criterion is structurally blind to — on the **log** side instead of the sim side.
2. **The column that detects it has never held a value.** `grep -rn "deaths" --include=*.py .`
   returns **exactly one line**: `core/builds/corpus.py:137`, the `CREATE TABLE`. Declared,
   never written, never read. **That is E11's shape** (`self_health_pct`: declared, read by
   `apl.py`, written nowhere) sitting in the corpus layer. And the APM ratio the whole
   retraction rests on has no implementation either — `3e` preflight recorded that
   `grep -rn "apm"` returns nothing.

**D1.** Implement the APM ratio in code. `ability_performance.casts` and
`encounters.duration_seconds` are committed and populated; this is a query.
⚠ **Guard it with thread 1**: `casts` under-counts cast-time casters (`SPELL_CAST_SUCCESS`
and `SPELL_CAST_START` are disjoint by cast type), so the ratio is only valid on
instant-heavy kits. Restrict it to boards whose cast-time entries are under a stated
fraction of the kit, **report the fraction per character**, and return `None` — not a
number — outside that regime. `3e` preflight already proved `Boomcat` qualifies (54/55 at
0 ms). 🛑 **22 of the 41 cohort boards are cast-time casters**; a bare APM ratio across the
cohort would be exactly the kind of number this project retracts.

**D2.** Populate `deaths`, or record that it cannot be. Tier-1 does not carry it — the
report payload's `encounters[]` has `wipe_percent`, `duration_seconds` and
`validation_status`, and no per-player death field. Re-fetch one report
(`crawl_ascensionlogs.py --recrawl-report <id>`) and check whether the per-player endpoint
exposes deaths or an active-time figure. **If it does, wire the column. If it does not,
state that in `PROGRESS.md` and say what the fallback signal is** — do not leave a declared
column unexplained for a third session.

**D3. PRE-REGISTER the direction before looking**, in `predictions/prereg_3h_boomcat.md`:
if `Boomcat` is death-deflated, correcting the denominator **raises** its logged DPS and
pushes its delta **negative** — it falls out of ±20% with everything else. State that, and
state what you would conclude if it **survives**. 🛑 **If it survives at 82.2% coverage it
is not pollution — it is the strongest single calibration point in the project**, and that
would be the most important result of the session.

**D4. Stamp the admissibility rule. DO NOT APPLY IT.** Same discipline as the 20% coverage
floor: `3e` stamped, `3g` applied. Write it into `CLAUDE.md` and
`predictions/CALIBRATION_TOLERANCE.md` with:

* the predicates, stated purely as **properties of the parse** — deaths > 0, active-time
  gap, `phase_label IS NULL`, snapshot lag above a stated bound, parse duration below a
  stated floor;
* verdict **NOT ADMISSIBLE (`None`)**, never `False`;
* the **measured effect on all 41**, computed **blind — before any delta is consulted** —
  and published in full;
* 🔬 **the falsifiability check, run and reported: the rule must remove at least one
  character that currently FAILS.** A rule that only ever removes passers is a fitting
  device and the asymmetry proves it. **If it only removes `Boomcat`, do not stamp it —
  report that and stop.**

> 🛑 **STOP-POINT D4.** Whether to stamp is an **owner decision**, exactly as the coverage
> floor was. Present the predicates, the blind cohort effect and the falsifiability result;
> **do not stamp without an answer.** Default if unreachable: compute and report everything,
> stamp nothing.

---

## Block E — close-out

**E1.** Session record `primer/Session_2026-08-07_3h_*.md`, born `HISTORICAL` with a status
line, per-commit gate pairs with the cause named, and every departure from this order
measured rather than argued.

**E2.** `PROGRESS.md` top block updated; this file reclassified `SUPERSEDED BY <record>`.

**E3. 🛑 DO NOT READ THE HOLDOUT.** It was read at `3g` close-out and nothing in this
session changes the model. Reading it again spends it for no measurement.
`--read-holdout` is not passed in `3h`.

**E4.** Anything Block C registers ships as `E15…` in `ENGINE_BUGS.md` **with a failing
check and a named green path that has been RUN** — `3g` G5 proved that a green path which
has only been *named* is a guess about your own code (E12's needed three edits, not the two
the work order specified).

---

## §2 — Questions, with the default if I am not reachable

| | question | default |
|---|---|---|
| **Q1** | Block C as a new tool or a flag on `calibrate_crawled.py`? | **new tool** — `calibrate_crawled.py` is 1,500 lines and carries the gate; keep the measurement out of the thing being measured |
| **Q2** | Should Block B's producing-only median become the headline? | **no.** Report both; changing which number is the headline is a criterion change and belongs in a stamped successor |
| **Q3** | If C4 finds a unit error, fix it? | **no.** Register it with a failing check. It moves the gate and belongs in a commit that owns its pair — the rule that made `3g` readable |
| **Q4** | If D2 finds the endpoint carries no death data, chase it further? | **no.** Record the gap, fall back to D1's APM ratio, and say plainly that the `Boomcat` question is bounded by data availability rather than by effort |
| **Q5** | If the clock runs out, what is dropped? | **D before C, C4 before C1–C3, and A never.** A is an hour and unblocks every later document; C is the session's reason for existing |

---

## §3 — Exit conditions

| # | condition |
|---|---|
| 1 | The gate reads `1 / 1 / 20.5%` at **every** commit, reported as a pair with its cause; Block D applies nothing |
| 2 | `ENGINE_BUGS.md` E13/E14 carry `✅ FIXED` headings and closure boxes; no `~78` survives; no entry claims to be a failing check that is not in `EXPECTED_FAILURES` |
| 3 | `CALIBRATION_TOLERANCE.md` has a status line, a band table **regenerated from the manifest**, and the corrected lever arithmetic |
| 4 | The manifest cannot contradict itself about the floor — key set, `APPLIED_FROM` emitted, F6 extended, red and green **both run** |
| 5 | `CLAUDE.md`'s census is **asserted** against the printed one; the census walk covers `predictions/` |
| 6 | Manifests refuse to write from a dirty tree without `--allow-dirty`, and record it |
| 7 | Coverage split into producing / keyed-but-zero, docstring corrected, **no verdict moved**, zero list named per character with no silent truncation |
| 8 | The per-ability comparison exists, covers the frozen cohort including `key_state = absent`, and its **pre-registration was committed before it ran** |
| 9 | The distribution is reported as a distribution; round-number and order-of-magnitude ratios are flagged; anything found is registered as `E15…` with a **run** green path and fixed in no commit |
| 10 | F9's 33.1% is reconciled against the cohort's 20.5%, or the disagreement is registered |
| 11 | The APM ratio has an implementation, a stated cast-time regime, and returns `None` outside it |
| 12 | `deaths` is populated or its impossibility is recorded in `PROGRESS.md` with the fallback named |
| 13 | `Boomcat`'s direction was pre-registered before it was read |
| 14 | The admissibility rule is stamped **or** explicitly not stamped, with the blind cohort effect and the falsifiability result both published |
| 15 | The holdout was **not** read |
| 16 | Every new document born with a status line and an expiry condition |

---

## §4 — The one thing to carry into this session

**`3e` fixed six mechanisms and the answer did not move. `3f` fixed none and found two errors
bigger than anything `3e` touched. `3g` fixed those two and the answer moved by a factor of
five — in the direction that makes the problem larger.**

The pattern is now three sessions deep and it does not favour effort. **Every defect worth
finding came from putting a measured magnitude on the other side of an equals sign, and
nothing came from more careful reasoning about the code.**

Slice accuracy is the last headline number in this project on the wrong side of that line.
**Measure it.**
