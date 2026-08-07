# Pre-registration — `3j` A2: the D5 comparator definition, tested in the direction nobody tested

> **`FINDING 2026-08-07`** — committed BEFORE the runs it predicts. Every
> measurement below is UNMADE at the time of writing; verify with `git log`
> that the commit carrying the results is a child of this one. True as of its
> date, not maintained.

## Why this document exists at all

`AUDIT_3I_ADVERSARIAL.md` §4, verbatim on the commit order:

| commit | time | what |
|---|---|---|
| `2b6c615` | 11:26:39 | the D5 comparator change — its own message already states the effect |
| `801d612` | 11:26:46 | `predictions/prereg_3i_admissibility.md`, **7 seconds later** |

The `3i` pre-registration covers the **wiring** of the admissibility rule into
`within_tolerance` (P1–P4). The change that actually moved the blind roster —
tightening the APM comparator set — has **no pre-registration**, and the
document that looks like one was written after its result was known. `3i` said
so plainly rather than hiding it; the problem is structural, not honesty.

🛑 **THIS DOCUMENT IS NOT A RETROACTIVE PRE-REGISTRATION OF THAT CHANGE, AND
CANNOT BE ONE.** The D5 effect (`5 of 41` → `3 of 41`; Robottikyrpa and
Frediib losing a confident ratio) is known to me, is recorded in
`prereg_3i_admissibility.md`, and no amount of ceremony makes a known result
unknown. Writing "I predict 3 of 41" here would be the same fraud one layer
further out.

What *is* still unknown, and what this document therefore registers, are three
questions the `3i` work never asked:

1. **The counterfactual roster.** Nobody has run the cohort with the D5 filters
   removed. The `5 of 41` figure comes from the `3h` stamp, computed on a
   **different corpus** — pre-E15, before pet damage was un-double-counted.
   Whether reverting the filters on TODAY's corpus reproduces exactly that
   roster is unmeasured.
2. **Whether the change set can move a character INTO a flag.** The audit
   asserts it cannot: *"each arm can only remove comparators… No arm of the
   change can add a flag."* That claim is about `len(apms) < 2` and about
   trash-stripping lowering the median. It does **not** follow for the median
   in general, and I believe it is **false as stated** — see P3.
3. **Whether the roster change touches the published gate at all.**

## The predicates, as they will be stamped (owner decision 2026-08-07)

Owner decision, taken before these runs: **stamp follows code.** Predicate 1's
comparator definition is amended to name the three filters, appended to
`CALIBRATION_TOLERANCE.md` in the `3i` D7 correction style — stamped text is
never rewritten in place. The reasoning offered and accepted: a comparator
scope that *contains the scope under test* compares a parse against itself, and
a sub-60s comparator violates the same capture-validity floor predicate 3
enforces. Those are correctness properties of the predicate, not a weakening
chosen to move a number.

Predicate 1, as amended:

> **APM ratio ≤ 0.5** — this scope's casts/min at or below half the median of
> the character's own other **qualifying** scopes, where a qualifying
> comparator scope (a) shares no encounter with the scope under test, (b) is at
> least `MIN_PARSE_SECONDS` long, and (c) contains no trash encounter. A
> comparator whose APM is legitimately `0.0` is **admitted**, not dropped.
> Fewer than 2 qualifying comparators ⇒ ratio `None` (refused), never a number.

## Registered predictions

**P1 — the counterfactual roster.** Removing all three filters (restoring
`others` as literally every other scope, i.e. the pre-D5 code) and re-running
the blind table on **today's** corpus yields a flagged roster that is a strict
**superset** of `{Nodding, Boomcat, Deyindra}`, and specifically re-admits
`Robottikyrpa` and `Frediib` to a confident ratio.
*Confirmed if the counterfactual roster ⊇ the current 3 and contains both
names. Falsified if either name still refuses, or if any of the current 3
drops out.*

**P2 — the roster change does not move the published gate.** Under the
counterfactual of P1 the gate still reads `0 within ±20% / 0 qualified /
slice 26.3% (n=23)`. Reasoning stated in advance: `Robottikyrpa` and `Frediib`
are `within_tolerance = false` today, so flagging them converts `False → None`,
which removes nothing from a count of `True`; and the slice population is
selected on coverage, not on admissibility (`3i` measured the admissibility
application as `1/1/26.3 → 0/0/26.3`, slice unmoved).
*Confirmed if all three headline figures are unchanged. Falsified by any move —
which would mean admissibility leaks into the slice population, a defect.*

**P3 — the audit's one-way claim is FALSE as stated, and I can build the
counterexample.** A filter that removes **low-APM** comparators *raises* the
comparator median, which *lowers* the tested ratio `scope_apm / median`, which
can push a character **below** `APM_RATIO_BOUND` — adding a flag. Concretely: a
character whose tested scope runs at 10 APM, with comparator scopes at 40, 45
and two sub-60s scopes at 2 and 3 APM. Unfiltered median of `[2, 3, 40, 45]` is
21.5 ⇒ ratio 0.465 ⇒ **flagged**… no — that is already flagged. The
counterexample must go the other way: tested scope at 12 APM, comparators
`[18, 20]` qualifying and `[2, 3]` sub-60s. Unfiltered median of `[2, 3, 18,
20]` = 10.5 ⇒ ratio 1.14 ⇒ **not flagged**. Filtered median of `[18, 20]` = 19
⇒ ratio 0.63 ⇒ still not flagged. Tested scope at 8 instead: unfiltered
8/10.5 = 0.76 not flagged; filtered 8/19 = 0.42 ⇒ **FLAGGED**.
*Registered claim: a fixture with tested APM 8, qualifying comparators at 18
and 20, and two sub-60s comparators at 2 and 3, is NOT flagged with the filters
removed and IS flagged with them applied. Confirmed if the fixture behaves that
way against the real `apm_ratio()`. Falsified if it does not — in which case
the audit's one-way claim stands and I record that instead.*

**P4 — the 0.0-comparator rationale in the code is inverted.** `3i` wrote at
`parse_admissibility.py:257-260` that admitting a legitimately-`0.0` comparator
is *"exactly the death-deflation signal this predicate exists to detect."* The
deflation signal lives on the **tested** scope. A `0.0` **comparator** drags the
median toward zero, which **raises** `scope_apm / median` and **hides**
deflation. *This is arithmetic, not a measurement — registered as a claim to be
corrected in the code, with the correction stating the real reason the fix is
right: a `0.0` comparator is DATA, and silently dropping it was a fail-open in
the comparator set, whatever direction it happens to push the ratio.*

## What is NOT being decided here

The `3h` P9 falsifiability question. `3i` D7 already recorded that under the
narrow predicate P9 registered, the count of removed FAILING characters is now
**0**, and that the full rule's bar survives only via `Nodding`. Nothing in
`3j` re-opens that; `3j` is an integrity session and does not move the gate.
If P1 shows the counterfactual re-admits both names, that is a fact about the
comparator definition, **not** a reason to revert to it.
