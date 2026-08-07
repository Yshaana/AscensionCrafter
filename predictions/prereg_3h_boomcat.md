# Pre-registration — `3h` Block D, the `Boomcat` reconciliation

> **`FINDING 2026-08-07`** — a prediction made before the measurement that tests it.
> True as of its date and **not maintained**. **Expires when `3h`'s session record
> lands** and records the outcome beside it. *(Born with a status line and an expiry
> condition, per `3f` F8c.)*

**Committed BEFORE the implemented APM ratio (D1) has been read for any cohort
character, and before the D2 re-fetch has run.** On the record already and
legitimately in these predictions' inputs: `3c`'s chat-side APM ratio of **0.24**
for `Boomcat` (no implementation existed — this session builds one); `3e`
preflight's finding that `Boomcat` is instant-heavy (54 of 55 board entries at
0 ms), so the cast-time confound does NOT apply to it; `corpus.py`'s
denominator being wall-clock encounter duration; `encounter_performance.deaths`
being declared and all-NULL; and Block C3's per-ability decomposition of
`Boomcat` (P3 confirmed: the +0.8% aggregate is compensation).

---

## P6 — the implemented APM ratio

**Prediction: the implemented ratio lands near `3c`'s chat-side 0.24 — in
[0.15, 0.35]** — and `Boomcat` remains inside the valid (instant-heavy) regime
the ratio is restricted to. If the implemented number disagrees with 0.24 by
more than that band, the chat-side computation was wrong and the `3c`
retraction's evidentiary basis needs restating either way.

## P7 — the direction, stated before it is read

**If `Boomcat`'s parse is death-deflated, correcting the denominator RAISES its
logged DPS and pushes its delta NEGATIVE — it falls out of ±20% with everything
else.** A parse with ~0.24 of the character's own typical action rate over an
80.5s window is most consistent with the character being dead or absent for a
large fraction of the window; its logged DPS is then deflated by construction,
and the sim's ~5× under-production lands "inside tolerance" against it.

**Prediction: the evidence will support death-deflation** (the APM ratio stays
≤ 0.35 under the implemented computation, and the D2 re-fetch either exposes a
death/active-time field consistent with it or exposes nothing that contradicts
it).

## P8 — what is concluded if it SURVIVES

If the implemented ratio comes back ≥ ~0.7 (i.e. the chat-side 0.24 was wrong
and the parse shows a normal action rate), then the parse is admissible and
`Boomcat` stays in the gate. 🛑 **But C3 has already shown what kind of pass it
is**: Serpent Strike (29.7% of logged) starved to zero and Poisonous Strikes
(14.4%) absent, against Puncture at 3.51× and Venomous Fury at 2.13×. So even
surviving, `Boomcat` is **not** "the strongest single calibration point" the
work order's earlier framing allowed — it is an admissible parse whose
aggregate agreement is per-ability compensation, `Ari`'s shape on the passing
side. The work order predates C3's measurement here; this pre-registration
supersedes that framing and says so before the D1 number is read.

## P9 — the admissibility rule's falsifiability check (D4)

**Prediction: at least one currently-FAILING character is removed by the
death-deflation predicate** (an APM ratio ≤ 0.5 within the valid regime, or
deaths > 0 once populated). The cohort's deltas are almost all deeply negative;
if death-deflation exists in the corpus it should not correlate with passing.
**If the rule removes only `Boomcat`, D4 says: do not stamp — report and
stop.**
