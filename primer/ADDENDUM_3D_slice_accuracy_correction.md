# Addendum — correction to `3d`'s slice-accuracy reading

> **`HISTORICAL`** — the record of a past session or a completed phase. Immutable. It **may contain claims that are false today**, and that is correct rather than a defect — it records what was believed at the time. **Never citable as current truth.** *(Classified `3f` F8c, 2026-08-07.)*

**Written by:** the monitoring chat, 2026-08-06, verifying `3d` at `de31da9`.
**Target:** `predictions/CALIBRATION_TOLERANCE.md` line ~154, and
`gate_manifest.json`'s `cohort_median_slice_accuracy_pct`.
~~**Urgency: before `3e` runs.**~~ ✅ **LANDED in `3e` A2** (marked `3f` F8): the
floor is implemented, it is in the manifest key name
(`median_slice_accuracy_pct_at_coverage_ge_20`), and the band table is emitted by
the tool. `3f` F8 added the missing `RETRACTIONS` row —
`cohort_slice_accuracy_160pct_means_the_sim_overproduces` — because the reversal had
been published in three prose documents and seeded in none.

---

## The claim

> "slice is over-produced by about 60% while only part of each kit is modelled"
> — `CALIBRATION_TOLERANCE.md:154`, from `cohort_median_slice_accuracy_pct = 159.79`.

## The correction

**That median is a low-coverage artifact, and the sign is backwards for every
character that matters.**

`slice_accuracy = (100 + delta) / coverage` has **coverage in the denominator**, so it
explodes as coverage → 0. Wynta sits at **1.3% coverage** and reports 150% slice
accuracy: a ratio computed against a hundredth of a kit is noise, not a measurement.
Computed from the committed manifest:

| Population | n | median slice accuracy |
|---|---|---|
| All | 38 | **159.8%** |
| coverage ≥ 20% | 27 | **62.6%** |
| coverage ≥ 30% | 23 | **62.6%** |
| coverage ≥ 50% | 11 | **62.6%** |

Stable at **62.6%** the moment the noise floor is excluded, and it does not move again
across three thresholds. **The sim UNDER-produces on the slice it models, by ~37%.**
It does not over-produce by 60%.

*(Cohort median `slice × coverage` is 36.4% at every band — that quantity is just
`(100+delta)/100` and is stable by construction. It is the *ratio* that destabilises,
not the product.)*

## Why it matters, concretely

At slice accuracy 62.6%, **coverage alone can never reach ±20%.** Landing `delta = 0`
needs `slice × coverage = 1.0`; at 0.626 that requires **coverage > 100%**. There is no
amount of reachability work that closes the gap while the modelled slice is 37% light.

Under the discarded 159.8% reading the conclusion inverts — it says coverage work will
*overshoot* and that the risk is sailing past the window. That is the opposite
instruction, and it would have sent `3e` to throttle exactly the work it needs.

The ~80% landmark is unaffected in its own terms (it was always stated as conditional on
slice = 100%, and `CALIBRATION_TOLERANCE.md` §"why it is NOT a floor" states that
correctly). What changes is the distance: reaching it requires slice accuracy to climb
from **62.6% to ~100%** *and* coverage from 36% to ~80%. Both roughly double. That is a
materially harder road than the 3d record implies.

## Three edits

1. **`CALIBRATION_TOLERANCE.md:154`** — replace "over-produced by about 60%" with the
   banded table above and the ≥20%-coverage figure. Keep the §"not a floor" reasoning;
   it is correct and unaffected.
2. **`calibrate_crawled.py`** — report cohort median slice accuracy **only over
   characters above a stated coverage floor**, and print the floor next to it. A ratio
   with coverage in the denominator must never be aggregated across characters whose
   coverage spans 1.3% to 69%. Emit the per-band table; it costs nothing and it is
   self-diagnosing.
3. **`gate_manifest.json`** — `cohort_median_slice_accuracy_pct` should carry its floor
   in the key name or an adjacent field. As it stands the manifest pins a number that
   two readers will interpret two ways.

## What does not change

* The §0 invariant held — verified: `edfcc61` and `de31da9` both read 5 of 41, 2
  qualified, and the manifest's `criterion_met/rider_met/exit_met` agree.
* PLAN_3C's "both must move together" was right, and is now quantified rather than
  argued. If anything it is *more* right: neither lever alone can close this.
* The cohort-drift finding stands and is the correct call (see below).

## Unrelated, and worth its own line

`3d`'s unprompted finding — `candidates()` is `ORDER BY character_id LIMIT 120` over a
population that grew 157→180 mid-session, so rebuilding `builds.db` moved the gate 5-of-41
→ 4-of-38 with **zero code changes** — is the most valuable thing in the session, and
declining to fix it inside a hygiene session was the right call. Two notes for `3e`:

* The isolation method (restore old corpus → 5 of 41 returns) is the correct proof and
  should be recorded as the technique, not just the result.
* **Whatever replaces the sliding window must be chosen before the next gate result is
  seen.** A cohort definition picked after observing which characters it admits is the
  same failure as moving a gate after seeing its number — `CALIBRATION_TOLERANCE.md`'s own
  closing rule. Pin it from the committed manifest's 41 ids, or state a rule that does not
  depend on corpus size, and stamp it *first*.
