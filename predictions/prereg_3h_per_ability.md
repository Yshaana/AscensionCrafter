# Pre-registration — `3h` Block C, the direct per-ability comparison

> **`FINDING 2026-08-07`** — a prediction made before the measurement that tests it.
> True as of its date and **not maintained**. **Expires when `3h`'s session record
> lands** and records the outcome beside it. *(Born with a status line and an expiry
> condition, per `3f` F8c.)*

**Committed BEFORE `tools/audit/per_ability_accuracy.py` has ever been run.** The
tool exists in the same commit as this file and has been syntax-checked only. What
IS known at time of writing, and is legitimately in these predictions' inputs:
Block B's cohort figures (producing-only median 30.7% at n=20; keyed-but-zero
median 0.1% / max 45.4%; all 90 zero entries `zero-casts-allocated`), the `3g`
fixes, and F9's frost-mage per-ability deltas (Frostbolt −34%, Ray of Frost −33%,
Ice Lance −60%, Frozen Orb within, Icicle absent — in `check_sim_engine.py` since
`3f`). What has NOT been seen: any cohort-wide per-ability ratio, `Boomcat`'s
per-ability decomposition, and any round-number scan.

---

## P1 — the shape

**Prediction: neither of the work order's two clean alternatives.** A mass at
exactly 0 (keyed-but-zero + the absent-key majority), and over **producing paired
abilities** a broad, right-skewed unimodal distribution centred noticeably below
1 — **median ratio in [0.20, 0.45]** (consistent with producing-only slice 30.7%,
which is an aggregate of exactly these numbers weighted by logged share).

Willing to be wrong about: **fewer than 15% of producing paired abilities land
within [0.8, 1.25]** — i.e. the sim getting an ability *right* is the exception.

## P2 — the zero fraction

Among **paired** abilities (sim key exists AND logged damage > 0):
**10–25% at exactly 0.** (Block B found 90 zero-cast keys; a minority carry
logged damage.)

Among all logged damage, **absent keys (no sim key at all) carry the majority:
> 55% of cohort logged damage.** Coverage median ~37% implies ~63% absent, minus
pet/auto edge cases.

## P3 — `Boomcat`

**Prediction: SPREAD, not clustered at 1.0.** Its +0.8% aggregate at 82.2%
coverage, against a sim that under-produces everywhere else, is predicted to be
**compensating error** — `Ari`'s shape on the passing side. Concretely: at least
one ability with ratio ≥ 1.5 AND at least one producing ability with ratio ≤ 0.5,
each carrying ≥ 5% of its logged damage.

**If instead every producing `Boomcat` ability with ≥ 5% logged share sits in
[0.7, 1.3], this prediction is WRONG and the conclusion flips**: `Boomcat` is a
genuine calibration anchor — the strongest single calibration point in the
project — and Block D's admissibility question becomes *more* important, not
less.

## P4 — a third unit error

**Prediction: YES, at least one exists.** At least one ability, carrying ≥ 1% of
its owner's logged damage, whose ratio is within 2% of one of
`{0.01, 0.1, 0.2, 0.25, 0.33, 0.5, 2, 3, 4, 5, 10, 100}` or of an integer in
[2, 30] — **and** either recurring across ≥ 2 characters holding the ability or
traceable to a mechanical constant (tick count, target count, rank multiplier)
on inspection. One character × one round ratio alone is coincidence-grade and
does NOT count.

Per the work order: anything found is **registered as `E15…` and fixed in no
commit of this session.**

## P5 — F9 reconciliation (C5)

The frost mage reads **33.1%** of measured DPS with no coverage term; the cohort
slice reads 20.5% (has-a-key) / 30.7% (producing-only). **Prediction: the
producing-only figure closes most of the gap** — the frost-mage whole-character
ratio will sit within **8 points** of the cohort's producing-only median, and the
remaining difference is composition (its five modelled abilities are
better-than-cohort-median modelled: −33% to −60% each, no starved keys).

**If the gap does not close** (frost-mage ratio differs from the producing-only
median by more than 8 points), that is a registered finding, not a rounding
difference — two measurements of the same quantity disagreeing.
