# Pre-registration ADDENDUM — `3l` B3b: per-snapshot weapon-slot convention detection

> **`FINDING 2026-08-08`** — committed BEFORE the fix it predicts, after the
> B3 pair (`29fbc1b` + `5bf7d98`) falsified P1/P4 and diagnosed one cause.
> This is the follow-up the diagnosis names; it is a NEW mechanism relative to
> the registered F1 and therefore gets its own registration rather than a
> rescue of the falsified predictions. True as of its date, not maintained.

## The measured cause (from the B3 pair, committed)

The corpus mixes TWO weapon-slot conventions per snapshot:

| cohort members | weapon slots | convention | under F1 (slots 15/16) |
|---:|---|---|---|
| 13 | {15} | server enum (15=MH) | ✅ gained their weapon |
| 14 | {15,16} | server enum (15=MH, 16=OH) | ✅ correct both hands |
| 7 | {16} | API style (16=MH) | ❌ LOST their weapon |
| 7 | {16,17} | API style (16=MH, 17=OH) | ❌ LOST both |

Anchors: slot-15 rows include 2H weapons (a main hand); slot-17 rows include
2H weapons (impossible for 3.3.5's ranged slot — they are Titan's Grip
off-hands under API numbering); a slot-16-ONLY weapon is self-contradictory
under the server reading (an off-hand with no main hand).

## The registered fix (B3b)

`build_spec_for` detects the convention **per snapshot, from its own weapon
rows**: if any weapon sits at slot 15 → server mapping `{15: MH, 16: OH}`
(17 = ranged, unmapped); otherwise, weapons at 16/17 → API mapping
`{16: MH, 17: OH}`. No snapshot is guessed: one with no weapon rows keeps no
weapon, and the stray slots (10–14) stay unmapped and warned as before.

## Predictions

- **P1b**: cohort members simmed with a main hand: **27 → 41 of 41** (the
  original P1, now conditioned on the measured convention split).
- **P2b**: characters with a producing `auto` key: **19 → 26–33** (13 server
  members newly joined + the 14 API members restored, minus members whose
  logs carry no negative-id rows).
- **P3b**: absent share **falls below the 59.9% pre-B3 baseline**: predicted
  **55.0–59.5%**. Quoted with the slice, always.
- **P4b**: slice at ≥20% coverage **rises or holds vs 33.5%**: predicted
  **33.5–45%**; within ±20% **0–3**; qualified **0–2**. No member's sim
  damage falls (the detector only ADDS weapons relative to `5bf7d98`).
- **P5b**: no member of the 27 currently-correct group changes AT ALL — the
  detector reproduces the server mapping exactly where slot 15 exists.

**NOT predicted:** the producing median (C2's epsilon lesson + opposing
membership forces); per-character deltas beyond the direction constraint in
P4b; everything deferred in the parent prereg.

**Falsifiers:** the stated bands; any of the 27 moving (P5b is exact); any
sim damage falling.
