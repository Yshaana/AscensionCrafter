# Pre-registration — `3g` G1, the E13 fix

> **`FINDING 2026-08-07`** — a prediction made before the measurement that tests it.
> True as of its date and **not maintained**. **Expires when `3g`'s session record
> lands** and records the outcome beside it. *(Born with a status line and an expiry
> condition, per `3f` F8c.)*

**Committed BEFORE the fix, deliberately.** This file and the
`auto_share_of_sim_pct` instrument that produced it land in one commit; the fix
lands in the next. That ordering is the whole value — it is the same construction
`3f` used for F9's tolerance (`eed2ec1` carries the number, `7a43fe3` the
assertion), and it is provable from git rather than asserted in prose.

🛑 **Not written to the `predictions` table.** That table holds pre-registered
claims about *game mechanics*, checked later against a capture. This is a
prediction about **our own code's output**, and `3g`'s stop-point 5 puts written
rows out of scope. The commit ordering carries the same guarantee at the right
weight.

---

## What changes, and by exactly how much

E13 is a **unit** error, so its size is not build-dependent and not estimated:

```python
mean = base * (p.get("hit", 0.0) + p.get("crit", 0.0) * crit_mult
               + p.get("glancing", 0.0) * glance_mult)     # swings.py:159-163
```

`probabilities()` returns percent (`combat_engine.py:216`, its own docstring).
So every white swing is inflated by **exactly 100×** — `p_hit = 50` is used where
`0.50` was meant.

⚠ **The "~78×" in `ENGINE_BUGS` E13 and the `3f` record is the MULTIPLIER'S
MAGNITUDE, not the error factor.** The bracket evaluates to ~78 where it should
evaluate to ~0.78, and both numbers describe the same defect — but the factor the
arithmetic is scaled by is 100, not 78, and every prediction below uses 100. The
78 is a property of one particular table (`hit + crit×mult + glance×0.75` for a
given crit rate); the 100 is a property of the units and is invariant.

The fix touches nothing else. The other consumer of `probabilities()`
(`ability_model.py:678-680`) already divides by 100 and simply stops doing so;
`SwingOutcome.crit_fraction` / `landed_fraction` have **zero readers tree-wide**.
So the only numeric change anywhere in the sim is **auto-attack mean ÷ 100**, and
each character's new sim total is

    scale = (1 − auto_share) + auto_share / 100

## Predicted gate, all 36 scored

| | before | **predicted after** |
|---|---:|---:|
| within ±20% | 5 of 36 | **1 of 36** |
| qualified (≥50% coverage) | 2 | **1** |
| slice accuracy at ≥20% coverage | 64.3% (n=23) | **20.5% (n=23)** |

🛑 **The gate criterion (≥3 within ±20%) is predicted to FAIL.** That is the
intended direction and must not be treated as a surprise or a regression.

**`n` for the slice band does not move** (23 either way), and neither does any
character's coverage. ⚠ **This contradicts `SESSION_3G_PRIMER.md` §0's warning
that "coverage falls too".** Coverage here is `modelled_damage_share()`
(`calibrate_crawled.py:369-424`) — the share of the character's **real logged**
damage belonging to abilities the sim produced *any* damage for, keyed on
`set(res.per_ability.keys())`. Scaling a magnitude does not remove a key, so
coverage is untouched by E13. Only the numerator of slice accuracy moves.

## The five current passers, individually

| character | auto share of sim | delta before | **delta after** | within |
|---|---:|---:|---:|---|
| `Ari` (464) | 89.3% | −9.7% | **−89.5%** | True → **False** |
| `Chastie` (16274) | 41.4% | +9.1% | **−35.6%** | True → **False** |
| `Zaczao` (20491) | 94.7% | −2.6% | **−93.9%** | True → **False** |
| `Malo` (33712) | 85.5% | −16.6% | **−87.2%** | True → **False** |
| `Xoller` (39717) | 94.8% | −11.6% | **−94.6%** | True → **False** |

**All five fall out.** The one predicted to cross *in* is `Boomcat`, from the
over-producing side.

🚨 **The exposure is far larger than the work order assumed.** `3f` reported that
24 of 36 scored characters "carry a melee auto in their top 5". Measured with the
new instrument, the auto is **89–96% of total sim damage** for fourteen of them,
and it is a passer's largest source in three of the five passes — not `Ari` alone.

## What this does to `3e`'s headline

`3e` concluded *"six mechanisms were repaired and the answer did not move,
therefore the residual is not in the mechanisms."* If the prediction above holds,
that conclusion was measured against a total in which a **100× error supplied
~90% of the sim's damage for most of the cohort**, and the four melee passes were
compensating error at a scale an aggregate criterion cannot see. The qualified
rider was invented to catch exactly this one level up; E13 is the same hazard one
level deeper, inside a qualified pass.

**Either outcome is informative, and both get recorded:**

* **Prediction holds** → `3e`'s reading needs amending and a `RETRACTIONS` row.
  The residual question re-opens on honest numbers for the first time.
* **Prediction fails** → I changed something I did not intend to, and the gap
  between predicted and actual names it. Stop-point 2 applies if the gate moves
  in the *better* direction.
