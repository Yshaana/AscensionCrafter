# Primer patch — the three stale-document corrections `3h` Block A must land

> **`FINDING 2026-08-07`** — exact find/replace blocks for the three stale citable-as-current
> documents named in `primer/AUDIT_3G_ADVERSARIAL.md` §1–3. **This file is scaffolding:
> delete it once the edits are committed.** Expiry condition: `3h` Block A closes.

Every number below is **pasted from `predictions/gate_manifest_3e.json`** (generated
`2026-08-07T01:37:21Z` at `80a66e9`), never retyped — per `3f` F8, which exists because the
last version of the same table did not describe the run it named.

⚠ **These are documents, not code.** They can be committed by the monitoring chat or by
Code; they move no gate and touch no `.py`. If Code takes them, they are Block A1–A2 and
belong in a commit that touches nothing else.

---

## 1. `primer/ENGINE_BUGS.md` — E13

### 1.1 Replace the heading (line 702)

**FIND**

```
## E13 — every white swing is ~78x over: `probabilities()` returns PERCENTS, `expected_swing` multiplies by them as FRACTIONS 🆕🚨
```

**REPLACE**

```
## E13 — every white swing was EXACTLY 100x over: `probabilities()` returned PERCENTS, `expected_swing` multiplied by them as FRACTIONS — ✅ FIXED (`3g` G1)

> ### ✅ Closed 2026-08-07, session `3g` G1 (`7af0195`). The record below is what was found; this box is what happened.
>
> 🛑 **THE FACTOR IS EXACTLY 100, NOT ~78.** The `~78` throughout the record below is the
> *multiplier's magnitude for one particular crit rate* — the bracket evaluates to ~78
> where ~0.78 was meant. E13 is a **unit** error, so its size is a property of the units
> and is **invariant across builds, weapons and content**: exactly 100. Read every `~78`
> below as "the bracket's value on the frost-mage fixture", not as the defect's size.
>
> **Fixed at the boundary, once.** `AttackTable.probabilities()` returns FRACTIONS
> (`combat_engine.py:242-244`); `probabilities_pct()` exists for percentage points
> (`:246-249`); `segments` stays percent because `roll()` draws `uniform(0, 100)` from it.
> `swings.py:159-163` is **unchanged, deliberately** — it was always written correctly.
> Patching the multiply site was the tempting fix and the wrong one: it would have left a
> function whose name and values disagree, which is the condition that produced the defect.
> `ability_model.py:748` was the CORRECT consumer all along and its compensating `/100.0`
> is gone.
>
> **Every consumer accounted for, tree-wide** (`core/`, `tools/`, `cli/`, `ingest/`): one
> wrong caller (`swings.py:130`), one right caller (`ability_model.py:678`), and
> `SwingOutcome.crit_fraction` / `landed_fraction` with **zero readers** — write-only and
> mis-united since written.
>
> 🚨 **The exposure was far larger than `3f` reported.** `3f` said 24 of 36 scored
> characters "carry a melee auto in their top 5". Measured with the `auto_share_of_sim_pct`
> instrument: **the auto was 89–96% of TOTAL SIM DAMAGE for fourteen of them**, and 41–95%
> for **all five** passers — not `Ari` alone.
>
> **Gate pair, this fix alone:** within ±20% **5 → 1**, qualified **2 → 1**, slice accuracy
> at ≥20% coverage **64.3% → 20.5%** (n=23 both). `Ari`'s −9.7% qualified pass was a 100×
> error cancelling a large negative one, and now reads **−89.6%**. The 12 characters with
> no auto damage are unchanged **to the decimal**, which makes the attribution exact rather
> than inferred.
>
> **Assertions:** three, in `check_sim_engine.py:865-882`, and **deliberately absent from
> `EXPECTED_FAILURES`** — a check that has started passing must leave the registry, or the
> registry stops meaning *"these are the known failures"*. They run every run; a regression
> turns them into ordinary hard failures.
>
> ⚠ **Still open, carried from the record below:** whether the `block` row should reduce
> damage rather than being dropped. Not assumed, not fixed, not registered.
```

### 1.2 Correct the `~78` in the body (line ~723)

**FIND**

```
**A probability table that sums to 100 is a PERCENTAGE table.** Treating it as
fractions multiplies every white swing by ~78. `expected_swing` returns
**11,573.6** for a weapon whose average hit is 240.7.
```

**REPLACE**

```
**A probability table that sums to 100 is a PERCENTAGE table.** Treating it as
fractions multiplies every white swing by **exactly 100** — the bracket below
evaluates to ~78 at *this* fixture's crit rate, which is where the `~78x` in
this entry's original heading came from, but the defect is a unit error and its
size is 100 for every build. `expected_swing` returns **11,573.6** for a weapon
whose average hit is 240.7.
```

### 1.3 Retire the two forward-looking paragraphs (lines ~736–748)

**FIND**

```
🛑 **DELIBERATELY NOT FIXED IN `3f`.** The session's invariant is that no
commit moves the gate, and this fix moves it enormously — in the direction of
*more* under-production, since it removes damage from 24 of 36 characters.
It belongs in a modelling session with a before/after pair, exactly as `3d`'s
D3 discipline requires and as E9–E12 are handled below. **It is the first thing
that session should do**, because every other calibration number is measured
against a total that contains it.

⚠ Two things to check when it IS fixed, neither assumed here: whether the
`block` row should reduce damage rather than being dropped, and whether any
other consumer of `probabilities()` makes the same unit assumption
(`grep -rn "probabilities()" core/`).
```

**REPLACE**

```
🛑 **DELIBERATELY NOT FIXED IN `3f`** — *and it was the first thing `3g` did.* The
paragraph that stood here said this belonged in a modelling session with a
before/after pair; `3g` G1 gave it exactly that, and the pair is in the closure
box at the top of this entry. The prediction it makes — *"in the direction of
more under-production"* — was correct, and understated: the gate went from 5
passing to 1.

⚠ Both of the "check when it IS fixed" items were taken up. The consumer sweep
(`grep -rn "probabilities()"` across `core/`, `tools/`, `cli/`, `ingest/`) was
run tree-wide and found no third caller. **The `block`-row question is still
open** and is the one thing in this entry that is not closed.
```

---

## 2. `primer/ENGINE_BUGS.md` — E14

### 2.1 Replace the heading (line 751)

**FIND**

```
## E14 — a periodic component with a 0.001s tick scores 12,000 ticks per cast 🆕🚨
```

**REPLACE**

```
## E14 — a periodic component with a 0.001s tick scored 12,000 ticks per cast — ✅ FIXED (`3g` G2)

> ### ✅ Closed 2026-08-07, session `3g` G2 (`6c62309`). The record below is what was found; this box is what happened.
>
> 🛑 **IT WAS NEVER A ONE-SPELL DEFECT, AND THAT IS THE PART WORTH CARRYING.** Scanned
> across all 1,055 distinct spell ids in the frozen cohort: **12 periodic events are built
> from two different spells' timing, and the card's duration DISAGREES with the component's
> own in ELEVEN of the twelve.** Absolute Zero is only where the disagreement is four
> orders of magnitude instead of one tick — which is why it is the one anybody noticed.
>
> **Fixed by stopping the mixing, not by detecting it — a deliberate departure from the
> work order, pre-registered at `5872b53` before the fix ran.** The component's own
> duration is one join away (`spell_dbc_raw.duration_index` → `dbc_spellduration`, which
> `core/spells/mechanics.py:317,335` already performed for the card and had never performed
> for a component). Refusing would have fixed the loud case by discarding eleven working
> numbers.
>
> ⚠ **THE SANITY LIMIT ALREADY EXISTED AND WAS NOT APPLIED TO ITS OWN SIBLING.** The
> periodic-**trigger-delivery** branch twenty lines above has refused above
> `PULSE_COUNT_SANITY_LIMIT = 100` since `2b`. **E14 is an unapplied guard, not a missing
> one** — which is a different and more worrying class than a guard nobody wrote.
>
> **The refusal is kept for what stays genuinely unknowable** — no own duration, a
> non-positive DBC sentinel (92557 reads −0.001s), and any count still over the sanity
> limit — and it names both spells. No spell in the corpus reaches the first of those
> today, so it is exercised **synthetically** (`check_sim_engine.py:958-972`): an untested
> refusal is a refusal nobody has seen refuse.
>
> **Gate pair, this fix alone:** within ±20% **1 → 1**, qualified **1 → 1**, slice accuracy
> **20.5% → 20.5%**. E14 moved deltas, not counts. `Mutaforma` (33642) moved **+3,618.8% →
> −88.3%** on this change alone, and `Boomcat` survived at −2.0% → +0.8% (it holds two
> affected cards pulling opposite ways; the pre-registration stated that direction as
> genuinely uncertain rather than guessing it).
>
> ✅ **Open question `sim_magnitude_explosion_absolute_zero` RESOLVED** (`seed_epistemics.py`).
> `3e` guessed the family right and the layer wrong: not a magnitude error, not a
> trigger-walk error — the attributed magnitude and the bounded walk were both fine.
>
> **Assertions:** three, in `check_sim_engine.py:915-972`, deliberately absent from
> `EXPECTED_FAILURES` for the same reason as E13's. ⚠ The second was **re-derived** during
> the fix: its first form asserted the *mechanism* the work order specified (Absolute Zero
> refuses), and now states the *property* (a tick count comes from one spell's duration and
> that same spell's tick). An assertion that encodes a mechanism breaks when a better
> mechanism arrives.
>
> 🚨 **What this fix hands to `3h`:** every new refusal converts a previously-producing
> component into a **zero that still holds a `per_ability` key**, and coverage counts keys.
> See `AUDIT_3G_ADVERSARIAL.md` §4 — the fix is correct and its interaction with the
> coverage instrument is not yet measured.
```

### 2.2 Retire the forward-looking paragraph (lines ~787–790)

**FIND**

```
🛑 **NOT FIXED IN `3f`** — same reason as E13. ⚠ Any fix must guard the general
case, not special-case this spell: a periodic event whose tick interval is
implausibly small (or whose tick and duration come from different spells)
should refuse and warn, per rule 2, rather than produce a number.
```

**REPLACE**

```
🛑 **NOT FIXED IN `3f`** — same reason as E13, *and fixed in `3g` G2*. ⚠ The requirement
stated here — *"guard the general case, not special-case this spell … should refuse and
warn"* — was **met and then improved on**: measuring first showed the component's own
duration is available, so the general case is fixed by removing the mixing rather than by
refusing it, and the refusal survives only where the duration is genuinely unknowable. The
reasoning for that departure is in `predictions/prereg_3g_e14.md`, committed **before** the
fix. See the closure box at the top of this entry.
```

---

## 3. `predictions/CALIBRATION_TOLERANCE.md`

### 3.1 Give the file a status line

**INSERT** immediately after line 1 (`# Calibration tolerance — written BEFORE any 2c calibration run`):

```

> **`LIVE`** — the stamped tolerance and calibration reference. **Must be true today, and
> is citable as current truth.** Tolerances in this file are stamped and may not be edited
> to fit a result; **measured tables in it are generated output and MUST be regenerated
> whenever the run they describe is superseded.** If you find a claim here that the tree
> contradicts, that is a defect in this file. *(Classified `3h` A2; `3f` F8c's lifecycle
> applied to `predictions/`, which it had not reached.)*
```

### 3.2 Replace the whole slice-accuracy block (lines ~154–190)

**FIND** — the block beginning `🚨 **CORRECTED IN 3e A2` and ending `…would have sent 3e to
throttle exactly the work it needs.`

**REPLACE**

```
🚨 **CORRECTED TWICE. Read both corrections — the second is larger than the first.**

**Correction 1 (`3e` A2): the sign.** `3d`'s figure was *"cohort median 160% — the modelled
slice is over-produced by about 60%"*. That median is a **low-coverage artifact**: slice
accuracy has **coverage in its denominator**, so it explodes as coverage → 0. Mutaforma, at
**0.2%** coverage, reports **1,859,400%** — and that value is in the committed `3d`
manifest. A median across a cohort spanning 0.2% to 82% coverage is not a measurement of
anything. **The sim under-produces on what it models.**

🚨 **Correction 2 (`3g` G1): the size, and it is four times worse than correction 1 left
it.** The `64.3%` this section carried until `3h` was **never true** — it was measured on a
sim in which `AttackTable.probabilities()` returned percentages that `expected_swing`
multiplied as fractions, making every white swing **exactly 100× over** (`ENGINE_BUGS.md`
E13). The auto was **89–96% of total sim damage for fourteen of 36 characters and 41–95%
for all five passers.** Slice accuracy did not *drift* from 64.3% to 20.5%; the earlier
figure was measuring a defect.

| coverage floor | n | median slice accuracy | readable? |
|---:|---:|---:|:--|
| ≥0% | 33 | 40.3% | **no** — below the floor |
| ≥10% | 26 | 23.4% | **no** — below the floor |
| ≥20% | **23** | **20.5%** | yes |
| ≥30% | 20 | 16.9% | yes |
| ≥50% | 8 | 16.9% | yes |

⚠ **Table PASTED FROM THE TOOL, never retyped (`3f` F8), and regenerated at `3h` A2 from
`predictions/gate_manifest_3e.json`** (generated `2026-08-07T01:37:21Z`, `80a66e9`),
`result.slice_accuracy_by_coverage_band_pct`. 🛑 **The version that stood here through `3g`
was `3f`'s, and it survived a session that regenerated the manifest five times** — the same
failure this warning was written to prevent, one session later, on the same table. Whoever
moves this number next: regenerate, do not retype, and check this table in the same commit
that moves the gate.

**The sim reproduces roughly ONE FIFTH of the damage of the abilities it has a key for.**
⚠ *"has a key for"* is deliberate and is not the same as *"models"* — see
`AUDIT_3G_ADVERSARIAL.md` §4 and `3h` Block B. Until that split is measured, this figure
conflates magnitude error with zero production.

*(Corroboration, independent of coverage: `3f` F9's frost-mage assertion compares modelled
DPS to a measured capture with a same-session verified stat block and no coverage term. It
reads **457 against 1,382 — −66.9%**, i.e. the sim produces ~33% of one real character's
total output. That it is not ~20% is itself informative and is a `3h` Block C question.)*

🛑 **Why this matters more than a bigger number.** At slice accuracy ~62–64% the previous
text said *"both levers have to roughly double"*, which reads as a hard but ordinary
programme. **At 20.5% the coverage lever is arithmetically dead.** Landing `delta = 0`
requires `slice × coverage = 1.0`:

* at the **ceiling** of 100% coverage, slice must reach **100%** — a **4.9×** rise;
* at the **best coverage in the cohort** (`Boomcat`, 82.2%), slice must reach **121.7%**;
* no attainable coverage substitutes for **any** of it.

**The magnitude lever has to carry essentially all of the gap.** Coverage work is now
support work, not the programme. Under the discarded 160% reading the conclusion inverted
entirely — it said coverage work would *overshoot* — and under the 64.3% reading it said
the two levers could share the load. Neither is true.
```

---

## 4. `CLAUDE.md` — two additions

### 4.1 The admissibility rule (new bullet under *Repo conventions*)

```
- 🆕 **A character may be excluded from the gate for what its PARSE is, never for what its
  DELTA is** (`3h` D4). Exclusion on **input validity** — a death-deflated window, a
  truncated parse, a NULL phase label, a snapshot too stale — is a data-quality gate and is
  legitimate. Exclusion on **output disagreement** is fitting wearing a gate's clothes.
  **The test: can the rule be stated and applied blind, to the whole cohort, before any
  delta is read?** If it needs the delta, it is not a rule. Three further requirements:
  it is **pre-registered with its measured cohort effect** before the gate is re-read; it
  applies **identically to tuning set and holdout**; and 🔬 **it must be capable of removing
  a character that currently FAILS.** A rule that only ever removes passers is a fitting
  device, and the asymmetry proves it. Verdict is **NOT ADMISSIBLE (`None`)**, never
  `False` — the same treatment the coverage floor gives a below-floor character.
```

### 4.2 Make the pasted census self-checking

**FIND**

```
  ⚠ This line previously read `13 / 32 / 0 / 6`, typed by hand, and was **wrong within a day
```

**REPLACE**

```
  🆕 **`3h` A4 — `check_refusals.py` now asserts that the block above matches what it
  prints**, so "generated" no longer means "generated once and pasted". The census moved
  **twice inside `3g` itself** (55 → 56 files) — G9 regenerated it, and Block D's own
  commits changed it again eight commits later. That is the proof that generation was the
  right call and that pasting output without an assertion only buys one more day.

  ⚠ This line previously read `13 / 32 / 0 / 6`, typed by hand, and was **wrong within a day
```

---

## 5. ~~`primer/PROGRESS.md`~~ — ✅ APPLIED 2026-08-07, before `3h` started

The `3h` pointer block is **already committed** at the top of `PROGRESS.md`, with the `3g`
block folded under `<details>` in the file's own convention. **Do not re-apply it.** It went
in ahead of Block A rather than at close-out because `PROGRESS.md` is the pointer that tells
a session where to look — including this one.
