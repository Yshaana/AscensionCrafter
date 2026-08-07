# Session `3h` — 2026-08-07 — the measurement that replaced the inference

> **`HISTORICAL`** — the record of session `3h`, a completed instrument session.
> May contain claims that are false today, and that is correct. Live state:
> `primer/PROGRESS.md`. *(Born with a status line, per `3f` F8c.)*

Work order: `primer/SESSION_3H_PRIMER.md` (now `SUPERSEDED BY` this file).
Audit implemented: `primer/AUDIT_3G_ADVERSARIAL.md`.

---

## §0 — The invariant, opening and closing

🛑 **The gate read `1 of 36 within ±20% · 1 qualified · slice accuracy 20.5%
(n=23)` at the session's open, at every one of its ten commits, and at its
close.** No engine defect was fixed; E9/E11/E12 keep their run green paths and
stay registered; the holdout was **not** read (`--read-holdout` never passed,
and `per_ability_accuracy.py` excludes holdout ids structurally).

| commit | block | gate pair | cause of no movement |
|---|---|---|---|
| `40696a2` | A docs | 1 / 1 / 20.5% | no `.py` touched |
| `d41930a` | A code | 1 / 1 / 20.5% | reporting/provenance only |
| `e06a8c3` | A manifest | 1 / 1 / 20.5% | manifest keys only, clean tree |
| `533201a` | B split | 1 / 1 / 20.5% | instrumentation; `modelled_damage_pct` expression untouched |
| `cf59da8` | B manifest | 1 / 1 / 20.5% | manifest keys only, clean tree |
| `1dd464e` | C1+C2 | 1 / 1 / 20.5% | tool + prereg added, never run |
| `acb8ec8` | C3+C4 | 1 / 1 / 20.5% | read-only measurement; E15 registered unfixed |
| `cd54716` | D3 | 1 / 1 / 20.5% | document only |
| `7fc5bc0` | D1+D2 | 1 / 1 / 20.5% | read-only tools + registry update |
| `6770405` | D4 | 1 / 1 / 20.5% | stamped, applied by nobody |

---

## §1 — What the session measured, in one block

**Slice accuracy was the last headline number in the project that was inferred
rather than measured. It is now measured, and the inference was hiding three
different things.**

1. **The distribution (C3, first run after the committed prereg `1dd464e`):**
   651 ability rows over 36 characters. Producing paired abilities: n=94,
   **median ratio 0.253**, quartiles 0.099/1.007, only **10 of 94 (11%)**
   inside [0.8, 1.25]. **25%** of paired keyed abilities sit at exactly 0.
   **Absent keys carry 62.2% of cohort logged damage.** The sim is not
   "uniformly ~5× under" — it is absent for most damage, zero-producing for a
   tenth, wrong in both directions on the rest, and the aggregates cancel.

2. **The zero mass is ALLOCATION, not refusals (B):** all **90** keyed-but-zero
   entries across the cohort are `zero-casts-allocated` — GCD starvation (E6/E7
   family). **Zero** come from E14's refusals: the `3g` audit's §4 worry that
   G2 poisoned coverage measures as absent. Producing-only slice median:
   **30.7% (n=20)** beside the headline 20.5% (n=23). Keyed-but-zero share:
   median 0.1%, **max 45.4%**, 18 of 36 characters affected.

3. **A structural ×2 on the LOG side (C4 → E15, registered, fixed nowhere):**
   pet-attributable damage is stored **twice** in `ability_performance` —
   15,551 of 20,785 owner+pet groups byte-identical. D2's re-fetch of report
   79 discriminated the layer: **the endpoint itself states pet damage twice**
   (owner-merged inside `rows[]` AND restated in `pet_spell_damage_by_owner`)
   and the ingester takes both at face value. One layer up,
   `corpus.py` computes `dps = (total_damage + pet_damage) / duration` where
   `total_damage` already contains the pet damage — **the gate's own logged
   DPS is inflated for every pet-owning character.** Green path RUN and
   REVERTED: consumer-side dedupe turns the registered check green and moves
   the gate to 1 / 1 / **19.8%** — which is why the fix belongs to a later
   commit that owns that pair (Q3).

---

## §2 — Prereg outcomes (both preregs committed before their measurements)

`predictions/prereg_3h_per_ability.md` (`1dd464e`, before the tool's first run):

| | prediction | outcome |
|---|---|---|
| P1 | producing median in [0.20, 0.45]; <15% inside [0.8, 1.25] | ✅ 0.253; 11%. ⚠ Caveat: the >1.25 tail is heavier than the prose implied (17% of producing) |
| P2 | 10–25% of paired keyed at exactly 0; absent >55% of logged | ✅ 25% (at the stated boundary); 62.2% |
| P3 | `Boomcat` SPREADS (compensation), not clustered at 1.0 | ✅ Serpent Strike (29.7% of logged) starved to 0, Poisonous Strikes (14.4%) absent, Puncture 3.51×, Venomous Fury 2.13×, autos 0.477 |
| P4 | a third sim-side unit error passing the coincidence guard | ❌ **FALSE as stated.** No round-constant hit recurs or traces to a constant (Revenge 0.2457~0.25 single char; Haunt 0.329 at 1% share; the ~0.1 auto is E15-contaminated). The scan instead surfaced an exactly-×2 error on the **log** side — E15. Right family, wrong side of the comparison |
| P5 | F9's 33.1% within 8 points of the producing-only figure | ✅ 33.1% vs 30.7% = **2.4 points** — the F9/cohort disagreement is closed by the producing/keyed split plus composition (the frost mage's five modelled abilities run −33% to −60%, no starved keys, verified inputs) |

`predictions/prereg_3h_boomcat.md` (`cd54716`, before D1 was read):

| | prediction | outcome |
|---|---|---|
| P6 | implemented APM ratio in [0.15, 0.35], inside the regime | ✅ **0.27**, regime valid (0 cast-time entries, n_others=8). `3c`'s chat-side 0.24 reproduced by an implementation for the first time |
| P7 | death-deflation supported; correcting the denominator pushes the delta negative | ✅ supported; D2 found no death field, and nothing contradicts the signature |
| P8 | if it survives, C3 already shows the pass is compensation | branch did not arise; the framing correction stands either way |
| P9 | the admissibility predicate removes ≥1 FAILING character | ✅ removes **3** (Nodding, Robottikyrpa, Frediib) + 1 passing (`Boomcat`) + 1 not-scoreable (Deyindra) |

---

## §3 — 🛑 Stop-points and owner decisions

**D4 (the only stop-point reached):** presented the five predicates, the blind
cohort effect (5 of 41), and the falsifiability result (removes 3 failing).
**Owner decision 2026-08-07: STAMP.** Stamped as successor #3 in
`predictions/CALIBRATION_TOLERANCE.md`, applied by nobody in `3h`. Known in
outline for the applying session: `Boomcat` is flagged, so application takes
`within ±20%` from 1 to 0 with `Boomcat` NOT ADMISSIBLE rather than failed —
that session records the pair.

---

## §4 — Departures from the work order, measured rather than argued

1. **B2's reason taxonomy gained `zero-casts-allocated`.** The work order named
   refused-*/no-damage-event-resolves; the corpus contained a third state (GCD
   starvation) and it turned out to be **all 90** entries. Folding it into
   "refused" would have misattributed the entire zero mass to E14.
2. **C5 did not literally run C1 on the frost-mage fixture** — the fixture has
   no `ability_performance` rows for C1's join. The equivalent per-ability
   measurement already exists (F9's fixture assertion, per-ability deltas
   committed since `3f`); the reconciliation used those numbers. P5's test was
   stated in the prereg and passed (2.4 points).
3. **`check_sim_engine.py`'s frost-mage XFAIL message** cited "the same ~64%
   slice accuracy" — E13's number, in a message string. Corrected in the Block
   A code commit as the same stale-document family Block A existed for.
4. **E15's check lives in `check_sim_engine.py`'s `EXPECTED_FAILURES`** even
   though the defect is corpus-layer — keeping `ENGINE_BUGS.md`'s line-17
   invariant (every entry is a failing check in that file's registry) true
   without a second registry.

## §5 — What `3h` hands to the next session

* **The modelling target list is now a distribution, not an aggregate.** The
  biggest single lever visible: **Elemental Blast** (0.02–0.19 across three
  characters carrying 56–69% of their logged damage; absent on a fourth at
  63.9%). Then the starved-allocation mass (E6/E7 family, 10.9% of logged
  damage), then the absent-key majority (62.2%).
* **E15's fix is one commit with a known pair** (1/1/20.5 → 1/1/19.8 on the
  consumer dedupe alone) — but the *right* fix is at ingest, and it also
  corrects `encounter_performance.dps` for pet owners, which moves deltas.
  Fix ingest and consumer in the same session, with the check leaving
  `EXPECTED_FAILURES`.
* **The stamped admissibility rule is ready to apply** — one commit, one pair,
  `Boomcat` 1 → 0 NOT ADMISSIBLE expected.
* **E9/E11/E12** keep their run green paths, untouched, ready.
* **`deaths` cannot be populated from this API** (D2, verified on a fresh
  re-fetch): no per-player death or active-time field on any payload. The
  fallback signal is the implemented APM ratio, valid-regime only.
* ⚠ **The phase boundary arms tonight** (`2026-08-08T00:00:00Z`). G0's
  defences have never fired; check on the 8th per `AUDIT_3G_ADVERSARIAL.md` §9.
