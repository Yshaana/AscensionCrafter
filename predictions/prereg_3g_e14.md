# Pre-registration — `3g` G2, the E14 fix

> **`FINDING 2026-08-07`** — a prediction made before the measurement that tests it.
> True as of its date and **not maintained**. **Expires when `3g`'s session record
> lands** and records the outcome beside it. *(Born with a status line and an expiry
> condition, per `3f` F8c.)*

**Committed BEFORE the fix**, same construction as `prereg_3g_e13.md`: this file
lands in one commit, the fix in the next, and the ordering is provable from git.

---

## The defect is bigger than one spell, and the fix is a derivation rather than a refusal

`occurrences_per_cast`'s periodic branch (`ability_model.py:634-643`) computes
`round(dur / tick)` where — for a **trigger-reached component** — `dur` comes
from the **card** and `tick` from the **component**. `_fields_for()` falls back
to the card's fields for any attributed component with no doc-confirmed facts of
its own, and says so in a warning; nothing downstream acts on that warning.

**Measured across the frozen cohort: 1,055 distinct spell ids, 12 periodic events
built from two different spells' timing.** Only one explodes:

| card | component | card duration | component's OWN duration | tick | n today | n from own duration |
|---|---|---:|---:|---:|---:|---:|
| 285148 Absolute Zero | 285149 | 12.0 | **0.001** | 0.001 | **12000** | **1** |
| 275739 Goldrinn's Fury | 275740 | 20.0 | 6.0 | 2.0 | 10 | 3 |
| 901025 Bloodbath | 901021 | 8.0 | 5.0 | 1.0 | 8 | 5 |
| 901025 Bloodbath | 954815 | 8.0 | 5.0 | 1.0 | 8 | 5 |
| 282977 Summon Void Zone | 92557 | 10.0 | **−0.001** | 2.0 | 5 | *sentinel* |
| 281210 Grove Guardian | 281211 | 15.0 | 20.0 | 5.0 | 3 | 4 |
| 281103 Mycelial Ring | 681554 | 3.0 | 10.0 | 1.0 | 3 | 10 |
| 982331 Shadow Waste Bolt | 284505 | 6.0 | 6.0 | 2.0 | 3 | 3 |
| 760158 Meteor | 760170 | 5.0 | 6.0 | 2.0 | 2 | 3 |
| 285133 Devour Mind | 287860 | 5.0 | 8.0 | 2.0 | 2 | 4 |
| 760158 Meteor | 760042 | 5.0 | 6.0 | 2.0 | 2 | 3 |
| 290255 Feral Frenzy | 290248 | 1.5 | 10.0 | 2.0 | 1 | 5 |

🚨 **The card's duration disagrees with the component's own in ELEVEN of the
twelve.** So the mixed pairing is not "wrong for Absolute Zero" — it is wrong
almost everywhere, and Absolute Zero is merely the case where the disagreement is
four orders of magnitude instead of one tick.

✅ **And every component's own duration is derivable.** `spell_dbc_raw.duration_index`
→ `dbc_spellduration`, which `core/spells/mechanics.py:317,335` already uses for
the card. It was never read for a component.

🛑 **So the general fix is NOT the refusal the work order specified.** `SESSION_3G_PRIMER`
Block A/G2 asks that a tick whose duration and period come from different spells
"refuse and warn". Refusing is the right instinct and would have been right if the
component's duration were unknowable — but it is one join away, so **the mixing can
be stopped rather than detected**, which fixes eleven silently-wrong components as
well as the loud one. The refusal is kept for the cases that remain genuinely
unknowable: no own duration, a non-positive sentinel duration (92557 reads
**−0.001**), and any count still above `PULSE_COUNT_SANITY_LIMIT`.

⚠ **That limit already existed and was not applied to its own sibling.** The
periodic-**trigger-delivery** branch twenty lines above has refused above
`PULSE_COUNT_SANITY_LIMIT = 100` since `2b`. E14 is an unapplied guard, not a
missing one.

## Predicted

**Frost mage ground truth** (`F9`, tolerance unchanged at ±25%):
83,610 modelled DPS → **roughly 500–600**, against a measured 1,382. Absolute
Zero's periodic component is ~99% of the post-E13 fixture total and drops by a
factor of 12,000. The assertion **stays red**, and lands in the ordinary
under-production family (≈ −55% to −65%) rather than +5,950%.

**Gate** — ten of the twelve cards are held by cohort members, so this is not
frost-mage-only. Two rows decide it:

* 🎯 **`Mutaforma` (33642)** holds Absolute Zero and is the cohort's
  **+3,618.8%** outlier at 0.2% coverage. Predicted to fall **below +100%**.
  This is the open question `sim_magnitude_explosion_absolute_zero` (`PLAN_3C`),
  and G2 should resolve it outright.
* ⚠ **`Boomcat` (16501)** is the **only** character currently inside ±20%
  (−2.0%, 82.2% coverage) and holds **two** affected cards pulling in opposite
  directions: Goldrinn's Fury 10 → 3 ticks (down) and Feral Frenzy 1 → 5 ticks
  (up). **Direction genuinely uncertain**, and it is stated as uncertain rather
  than guessed.

| | before | **predicted after** |
|---|---:|---:|
| within ±20% | 1 of 36 | **0 or 1** — entirely `Boomcat` |
| qualified (≥50% coverage) | 1 | **0 or 1**, same row |
| slice accuracy at ≥20% | 20.5% (n=23) | **small move**; the other affected characters sit at −35% to −98% and a few ticks cannot bring them in |

**Coverage may move this time, unlike E13.** A component that refuses can take an
ability's damage to zero, and a zero-damage ability that drops out of
`per_ability` would leave the modelled set. Predicted small; reported either way.
