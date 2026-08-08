# Pre-registration — `3m` Block B: Improved Cleave, before the server changes it

> **`FINDING 2026-08-08`** — committed BEFORE the change it predicts. Every number
> below is derived from the **committed baseline** `gate_manifest_3e.json` @ `7723b1e`
> and `data/derived/calibration_crawled.json` regenerated at `ece967d`
> (instrument only — the gate reads identically at both commits); the post-change
> numbers are UNMADE at the time of writing. Verify with `git log --format='%H %p %s'`
> that the commit carrying the results is a child of this one. True as of its date,
> not maintained.

**Baseline artifact:** `predictions/gate_manifest_3e.json`, git `7723b1e`, generated
`2026-08-08T08:11:51+00:00` — `0 of 35 within ±20% · 0 qualified · slice 30.426%
(n=24) · absent 58.8% · producing median 0.3116 (n=118)`.

---

## Why this is registered at all: a server patch lands Monday

`data/source/changelog/daily/2026-08-08_page1.json`, entry `2026-08-07T21:32:22`,
`[Darkmoon] [Dawnrise]`:

> *"[Going Live Monday, 10 August] Fixed a bug where **Improved Cleave increased
> hybrid Cleaves weapon damage, rather than only their bonus damage.** Regular Cleave
> was unaffected. … Improved Cleave is now eligible for reset at Gabril Mewell."*

This project read `EffectMiscValue = 8 = SPELLMOD_ALL_EFFECTS` over the tooltip's
*"increases the **bonus** damage"* — **correctly, per its own standing rule** — and
modelled a whole-ability ×2.20. Ascension has now stated the tooltip described the
**intent** and `ALL_EFFECTS` was the broken **delivery**. Same shape as `2d`'s Path of
Duality lesson, **fired in the opposite direction: here the numeric field was the bug
and the prose was right.**

**Owner decision, 2026-08-08, taken before any code was changed: model INTENDED.**
The primer's `2d` practice — *model the intended behaviour, record the shortfall as a
dated impairment* — with the shape checked rather than assumed, because every existing
`SYSTEM_IMPAIRMENTS` record is *delivered < intended* and this is the first
*delivered > intended* case. **Owner decision 2: the frozen cohort stays pre-fix.**

`0.65·W + 2.2·(9 + AP)` replaces `2.2·(0.65·W + 9 + AP)`. The removed term is
`1.2 × 0.65 × W` — **pure weapon damage, so the nerf scales with weapon damage.**

---

## Facts measured BEFORE the change

**Six cohort members hold Improved Cleave, all at rank 3** (card `20496`,
`EffectBasePoints` 119 → **+120%**, i.e. ×2.20): character ids 461, 463, 7674, 10456,
11431, 11591. **461 and 463 are HOLDOUT members and are not read**, so the tuning-set
population is **four**.

**The ×2.20 is confirmed to be reaching these abilities**, read from
`sim_ability_damage[].applied_multipliers` rather than inferred — Nodding's Stormbound
Cleave carries a talents factor of **exactly 2.2000**, and the others carry 2.2 × their
own other talents (Blix 2.8217, Robottikyrpa 2.4926, Lootgoblin 2.6696).

⚠ **This could not be read from the committed artifact before this session.**
`res.warnings` is truncated to `sorted(...)[:8]` — **alphabetically** — so
*"Bladestorm event …"* survived and *"Lightbound Cleave event …"* did not. The
multipliers are now carried explicitly per ability.

| character | ability | talents factor | weapon base `W` | bonus base `B` | W share |
|---|---|---:|---:|---:|---:|
| 7674 Blix | Lightbound Cleave | 2.8217 | 168.0 | 62.0 | 73.0% |
| 10456 Nodding | Stormbound Cleave | 2.2000 | 168.0 | 62.0 | 73.0% |
| 11591 Robottikyrpa | Voidbound Cleave | 2.4926 | 153.7 | 62.0 | 71.3% |
| 11431 Lootgoblin | Lightbound Cleave | 2.6696 | 27.3 | 62.0 | — (0 casts) |

Other talent multipliers **cancel out of the ratio** and are not part of the
prediction: `post/pre = O·(W + 2.2B) / (2.2·O·(W + B))`.

🚨 **A finding that falls out of this, recorded here because it is load-bearing for
the owner's decision and NOT for the predictions below.** `seed_confirmed.py:103`
states Lightbound Cleave's bonus term as **`9 + AP × 1.0`**, read on 2026-08-03 from
`EffectBonusCoefficient = 1.0`. **`1x` (2026-08-04) established that
`EffectBonusCoefficient` is NOT an SP/AP coefficient** — it is stock 3.3.5's
`EffectBonusMultiplier`, whose neutral value is exactly 1.0, and 7,647 of 9,211
non-zero values are 1.0. So *"a full 1:1 AP-scaling coefficient, notably stronger than
any other per-hit coefficient in this project"* was **the neutral default read as a
measurement** — which is precisely the trap `CLAUDE.md` now names as a hard rule. The
current decode says **flat 62**, no AP term, and the sim's `B = 62.0` is that flat.
**The seed's formula SHAPE is what Monday confirms; its MAGNITUDE rests on a retracted
premise.** Corrected in the same commit as the code.

---

## Predictions

🆕 **The falsifier is SYMMETRIC** (`3m` §0 rule 3). `3l`'s tuning prereg read *"every
delta moves UP; any character moving DOWN falsifies the mechanism model"*, under which
this change could not have been registered at all. Below, the **predicted direction is
stated per mechanism**, and a move in *either* direction that is not predicted
falsifies.

**P1 — the gate criterion does not move.** `within_tolerance` **0 → 0**, `qualified`
**0 → 0**. *Direction: unchanged.* Every affected character sits at −93% or worse and
is moving further from zero; none is near the ±20% band in either direction.

**P2 — the headline slice does not move, to the digit: 30.426% (n=24) → 30.426%
(n=24), same-member `delta_pp` = 0.000.** *Direction: unchanged.* The mechanism is
`3l`'s own P4b lesson used as a **predictor** rather than learned after the fact: all
four affected members sit at slice **5.87 / 3.94 / 3.17 / 14.10%**, far below the
median of 30.425, and pushing values that are already below a median further down
cannot move it. **Membership is also unchanged** — coverage is untouched, so no member
crosses the 20% floor.

**P3 — the producing median does not move: 0.3116 (n=118) → 0.3116 (n=118).**
*Direction: unchanged.* Same mechanism: the two affected producing rows are at ratios
**0.0737** (Blix LC) and **0.0242** (Nodding SC), both far below the median and both
staying below it. ⚠ Robottikyrpa's Voidbound Cleave is **not** among the 118 producing
rows, so only two rows move.

**P4 — absent share unchanged at 58.8%.** *Direction: unchanged.* No sim key is gained
or lost; only a magnitude changes.

**P5 — exactly THREE abilities change, and their per-ability changes are:**

| character | ability | predicted change |
|---|---|---:|
| 7674 Blix | Lightbound Cleave | **−39.84%** |
| 10456 Nodding | Stormbound Cleave | **−39.84%** |
| 11591 Robottikyrpa | Voidbound Cleave | **−38.87%** |

**P6 — per-character sim totals, and NOTHING ELSE MOVES:**

| character | sim change | delta now | delta predicted |
|---|---:|---:|---:|
| 7674 Blix | **−30.12%** | −96.01% | **−97.21%** |
| 10456 Nodding *(NOT ADMISSIBLE)* | **−10.51%** | −97.56% | **−97.82%** |
| 11591 Robottikyrpa | **−2.33%** | −92.99% | **−93.16%** |
| 11431 Lootgoblin | **0.00%** | −98.07% | −98.07% |
| the other 31 tuning members | **0.00%** | — | unchanged |

Lootgoblin holds both cards and moves **zero** because its Lightbound Cleave is
allocated **0 casts** by the APL — a real prediction that a broadly-applied change
would break.

**P7 — Robottikyrpa's Piercing Cleaver does NOT change**, despite the name. Its
talents factor is **1.133** with no 2.2 component, so Improved Cleave does not reach
it, and its weapon base is **0.0** — it would not move even if it did. *Direction:
unchanged.* A change here means the modifier was scoped by name rather than by class
mask.

### What falsifies this

Any of: a character outside the four moving at all; any of the three per-ability
changes landing more than **±0.5 pp** from predicted; Lootgoblin or Piercing Cleaver
moving; the headline slice, the producing median, the absent share or
`within_tolerance` moving at all; **or any member moving UP.** The prediction is that
three numbers go down by a stated amount and everything else holds — a violation in
either direction is a falsification, and it is reported, not rescued.

### What is NOT predicted

* **Anything about the holdout.** 461 and 463 hold Improved Cleave and will change;
  the holdout is unspent by owner decision and is not read.
* **That the sim gets closer to reality.** It does not, and this is the sharp point:
  **every parse in the corpus is PRE-fix**, so modelling the intended behaviour makes
  the sim reproduce something the logged data does not contain. The four characters
  get *worse* against their own parses, and that is the correct direction when the
  previous number was right about the wrong server.
* **The date-aware refinement**, named and deferred rather than done under a deadline:
  applying the impairment only to parses dated before `2026-08-10` would let the
  intended model be compared against pre-fix parses without this bias. It requires
  threading a parse date into the talent layer and is registered for `3n`.
* **Whether Regular Cleave was affected.** The changelog says it was not; nothing here
  tests it.

---

## 🆕 RESULTS — appended in the pair commit, `3m` B (2026-08-08)

Run from the clean tree at `9267660`, the commit-child of this prereg.
**Nothing above this line has been edited.**

| # | prediction | outcome |
|---|---|---|
| **P1** | `within_tolerance` 0 → 0, `qualified` 0 → 0 | ✅ **CONFIRMED** — `0 / 0` |
| **P2** | headline slice 30.426% (n=24) → 30.426%, same-member `delta_pp` 0.000 | ✅ **CONFIRMED to the digit** — 30.426 (n=24), same-member **+0.001 pp**, membership unchanged |
| **P3** | producing median 0.3116 (n=118) → 0.3116 | ❌ **FALSIFIED** — **0.3234 (n=117)**, +0.0118 |
| **P4** | absent share unchanged at 58.8% | ✅ **CONFIRMED** — 58.83% |
| **P5** | three abilities move by −39.84 / −39.84 / −38.87% | ❌ **FALSIFIED** — two went to **−100%** (dropped from the rotation), one moved −1.4% |
| **P6** | four characters move by −30.12 / −10.51 / −2.33 / 0.00%, and no other member moves | ⚠ **SPLIT: the tail CONFIRMED EXACTLY, the magnitudes FALSIFIED.** Exactly **3 of 35** moved, Lootgoblin exactly **0.00%** — but Blix moved **+14.71%**, not −30.12% |
| **P7** | Piercing Cleaver does not move | ✅ **CONFIRMED exactly** — 2,683.1 before and after, talents factor 1.133 both times |

### The diagnosis, and it is one mechanism

**The APL is endogenous to ability magnitudes, and every falsified prediction here
assumed a fixed rotation.**

`apl_gen` ranks cooldown-less fillers by **expected damage per cast**
(`fillers = sorted(rest, key=lambda s: -s["mean"])`), and `fast_sim` gives the top
filler the entire remaining GCD budget. On Blix:

| | per cast | casts | total |
|---|---:|---:|---:|
| Lightbound Cleave, before | **596.4** | 44.52 | 26,554 |
| Plague Strike, before | 591.7 | *(unallocated)* | — |
| Plague Strike, after | 591.7 | **54.99** | **32,540** |

Lightbound Cleave led by **0.8% per cast**, so it took the whole budget. The
bonus-only fix cut it ~40%, Plague Strike took the lead, and Lightbound Cleave left
the rotation **entirely** — hence −100% rather than −39.84%, and hence P3's `n`
falling 118 → 117 as its 0.0737 ratio left the producing population. **P3 is `3l`'s
P4b lesson a third time: the producing median ROSE because a low ratio was removed,
with no ability becoming more accurate.**

**Blix's sim rose 14.71% because the pre-change rotation was worse by the sim's own
accounting.** Plague Strike delivers 23.5% more casts at 0.8% less damage each —
strictly more damage — and the APL preferred Lightbound Cleave anyway.

### 🚨 A defect this falsification exposed, registered NOT fixed

**`apl_gen` ranks fillers by damage per CAST while the budget allocates by TIME, so
it can pick the lower-throughput button.** 596.4 × 44.52 = 26,554 against
591.7 × 54.99 = 32,540 — the sim chose the option worth 18% less. The correct key is
damage per GCD-second, not per cast.

This is **not** fixed here: it is a separate mechanism, it moves the gate for every
filler-limited character in the cohort rather than the four in this prereg's scope,
and changing it inside a falsified prereg's own results commit would be rescuing.
Registered for `3n` with this measurement as its evidence.

### What was NOT rescued

The prereg is not edited. P5 and P6's magnitudes are wrong because they were computed
under a fixed-rotation assumption that this session's own instrument
(`sim_ability_damage`, added two commits earlier) was sufficient to have tested and
did not. **P2 and P7 were exact, P1 and P4 held, and P6's tail — the hard part, that
*nothing else moves* — held exactly.** The mechanism scoping was right; the
throughput model underneath it was not.
