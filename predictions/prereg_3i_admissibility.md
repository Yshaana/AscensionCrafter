# Pre-registration — `3i` Block D: applying the stamped admissibility rule

> **`FINDING 2026-08-07`** — committed BEFORE the application commit it predicts
> (the wiring into `calibrate_crawled.py`'s `within_tolerance` and the gate
> re-run must be a child of this one; verify with `git log`). True as of its
> date, not maintained.

## What is known at time of writing (legitimate inputs)

The stamp (`predictions/CALIBRATION_TOLERANCE.md` successor #3, `3h` D4):
blind effect **5 of 41** (Nodding, Robottikyrpa, Boomcat, Deyindra, Frediib),
falsifiability **removes 3 FAILING characters** (Nodding, Robottikyrpa,
Frediib) + 1 passing (Boomcat) + 1 not-scoreable (Deyindra). D1–D6 implement
the predicates rather than printing prose (predicate 4 via `resolve_phase`,
predicate 5 tested, the comparator tightened per D5). **Running the repaired
tool to verify D1–D6 (required engineering — not a gate read) surfaced a
departure from the stamp, recorded here before the gate-moving commit:**

🚨 **The D5 comparator tightening (excluding trash-tainted, sub-60s, and
self-overlapping comparator scopes — each a real correctness fix, not a
weakening chosen to move a number) changes the ROSTER, not just the count.**
Re-run blind table: **3 of 41 flagged** — Nodding, Boomcat, Deyindra.
`Robottikyrpa` and `Frediib` no longer carry a confident APM ratio at all:
their comparator sets shrank below 2 qualifying scopes once the tightened
filters removed self-overlapping/short/trash-tainted scopes, so their ratio
is now `None` (refused) rather than `≤ 0.5`. Boomcat's own ratio moved
**0.27 → 0.24** — closer to `3c`'s original chat-side figure, corroboration
rather than drift.

**Consequence for the stamp's own falsifiability argument, stated precisely
rather than glossed over:** under the FULL combined rule (all five
predicates), the bar (*removes ≥1 currently-failing character*) is **still
met** — `Nodding` is still flagged, via predicate 3 (window 52s < 60s),
untouched by D5's tightening. But under the NARROWER predicate
`prereg_3h_boomcat.md` P9 actually registered (*APM ratio ≤ 0.5 within the
valid regime, or deaths > 0* — excluding the window predicate), the count of
failing characters removed is now **0**, not the 2 that survive `3i` D7's own
correction of the "3" figure (see `D7` below) — `Robottikyrpa` and `Frediib`
were the two, and neither carries a confident ratio anymore. **The narrow
predicate's evidence for stamping has evaporated under a more correct
comparator; the full rule's evidence (Nodding, via a different predicate)
has not.**

This is reported as a finding, not absorbed silently. It does not change the
Q4 default (apply the rule): the falsifiability bar under the actual stamped
rule — all five predicates combined, which is what was measured and pasted
into `CALIBRATION_TOLERANCE.md` — is still met, and D5's tightening is a
correctness fix (fail-open comparator flaws named in `AUDIT_3H_ADVERSARIAL`
§5.2/§5.3), not a fit to a wanted result. Withholding the application because
the *specific* evidence changed would be exactly the fitting-in-the-other-
direction this project's stamp-first discipline exists to prevent.

## Prediction

**Applying `admissibility_for()` inside `calibrate_crawled.py`'s per-character
loop** (overriding `within_tolerance` to `None` for any flagged character,
regardless of its prior verdict, with the original verdict preserved under a
separate key for auditability):

* **P1 — `within ±20%` count: 1 → 0.** `Boomcat` is the cohort's only passer
  and is flagged (`apm_ratio 0.24 ≤ 0.5`, in-regime); its verdict becomes
  `None` (NOT ADMISSIBLE), never `False`.
* **P2 — `qualified` count: 1 → 0** (it is the same single row).
* **P3 — no other tuning-set member's verdict changes**, because the two
  other flagged characters (Nodding, Deyindra) are already `None` or `False`
  in the current manifest (Deyindra is a `not_scoreable_below_coverage_floor`
  member per the 20% floor; Nodding fails outright) — flagging them
  NOT ADMISSIBLE instead of FAILED changes their *label*, not the count.
* **P4 — slice accuracy (median at ≥20% coverage) is UNCHANGED**, because
  `within_tolerance` does not enter that computation.

**Willing to be wrong:** if the count moves by more than the one row named
above, or a different character's verdict changes, that is a departure from
this prereg and must be reported before the manifest is committed.
