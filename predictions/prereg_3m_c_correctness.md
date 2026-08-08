# Pre-registration — `3m` Block C: four correctness repairs, two of which move the gate DOWN

> **`FINDING 2026-08-08`** — committed BEFORE the run it predicts. The gate has
> **not** been read since any Block C change was made; every number below comes from
> the post-Block-B artifact. Verify with `git log --format='%H %p %s'` that the commit
> carrying the results is a child of this one. True as of its date, not maintained.

**Baseline:** `gate_manifest_3e.json` @ `9267660` — `0 of 35 · 0 qualified · slice
30.426% (n=24) · absent 58.83% · producing median 0.3234 (n=117)`.

🆕 **The falsifier is SYMMETRIC.** Direction is stated per mechanism; a move in
either direction that is not predicted falsifies.

---

## The four repairs, and what each can touch

**C1 — Righteous Vengeance's rank** (`AUDIT_3L` F3). `RIGHTEOUS_VENGEANCE_FRACTION`
was a flat `0.30` while the three card ids decode `EffectBasePoints` 9 / 19 / 29 →
**10% / 20% / 30%**, and `tiers.py` used the ids as a *membership* test. A rank-1
holder was credited 3×. Re-derived from `spell_dbc_raw` this session.

**Cohort blast radius, measured: 12 members hold the card, and exactly TWO hold a
rank below 3** — `32037 Shana` and `32124 Striker`, both card `53381` (20%). The
other ten hold `53382` (30%) and are **unaffected by C1**.

**C2 — Righteous Vengeance's white-crit pool** (F4). `3l` added `auto_crit_damage` to
the pool. RV's own client text says *"**Direct** critical strikes with **spells and
abilities**"*, and `core/builds/stats.py` reads that exact wording as excluding autos.
Measured against the widening two independent ways: `AUDIT_3L` on the committed logs
(worse in **49 of 49** rows carrying white crit; OLS white-crit coefficient −1.25) and
`3m` over the whole crawl corpus (worse in **1,416 of 1,852**; implied fraction
**0.2004** ability-only against 0.1789 with white included — ability-only landing on
rank 2's 20% almost exactly, which corroborates C1 from the other direction).
**Retracted.** Affects every RV holder that has white crits.

**C3 — aura 344 is flat attack power** (F5). Seed text only this session; the +73/weapon
AP grant is **named and NOT yet modelled**. No code path changes.

**C4 — `rank_for_level` on an enchant line** (F6). Now gated by
`SpellItemEnchantment.min_level` when the line is enchant-delivered, with `gate`
naming which rule answered. 818 rank lines are enchant-delivered; **exactly ONE card
spell id in the whole corpus sits on such a line** (`17933 Improved Shadowburn`, held
by 2 corpus characters), and a talent card's rank comes from the card roll, not from
this resolver.

**C6 — the stray weapon-slot check keyed on the slot INDEX** (F10). Adds a warning
only. No cohort member is slot-17-only.

---

## Predictions

**P1 — C3 and C6 do not move the gate at all.** *Direction: unchanged.* C3 edits a
seed string; C6 appends a warning. Neither touches a magnitude.

**P2 — C4 does not move the gate.** *Direction: unchanged.* One corpus card sits on
an enchant-delivered line and its rank does not come from this resolver.

**P3 — C1 moves exactly TWO members, by exactly one third of their RV row:**

| character | card | RV now | RV predicted | RV share of sim | predicted sim change |
|---|---|---:|---:|---:|---:|
| 32037 Shana | 53381 (20%) | 1,587 | **1,058** | 6.78% | **−2.26%** |
| 32124 Striker | 53381 (20%) | 1,642 | **1,095** | 5.63% | **−1.88%** |

**No other member changes from C1.** *Direction: down for these two, unchanged for the
other ten holders.*

**P4 — C2 moves every RV holder that has white-swing crits, always DOWN, never up.**
*Direction: down or unchanged, never up.* 🛑 **The per-member magnitude is NOT
predicted**, and the reason is stated rather than hidden: `auto_crit_damage` has never
been exposed in any artifact, so the white share of each character's crit pool is not
knowable from committed data. What IS predicted is the **sign and the bound**: RV can
only fall, so each holder's sim total can only fall, and a holder whose RV rises
falsifies this outright.

**P5 — no member that holds no Righteous Vengeance card moves at all.** *Direction:
unchanged.* This is the hard half and the one a sloppy implementation breaks.

**P6 — the headline slice does not RISE, and membership does not change.**
*Direction: down or unchanged.* Coverage is untouched by every repair here, so no
member crosses the 20% floor and the band membership is fixed; and
`slice = (100 + delta) / coverage` with `delta` only falling means every affected
member's slice only falls. **A rise in the headline slice falsifies.** 🛑 The
magnitude is not predicted — `3l`'s P4b lesson has now bitten twice in this session
(B's P3 among them), and predicting a median over a population whose values are all
moving is exactly what that lesson says not to do.

**P7 — `within_tolerance` stays 0 and `qualified` stays 0.** *Direction: unchanged.*
Every affected member is at −93% or worse and moving further from zero.

### What falsifies this

Any member outside the 12 RV holders moving; Shana or Striker moving by more than
±0.3 pp from P3; any member's RV row **rising**; the headline slice rising; the
membership of the ≥20% band changing; `within_tolerance` or `qualified` changing;
or C3/C4/C6 producing any gate move.

### What is NOT predicted

* **The magnitude of C2's move**, per member or in aggregate — see P4.
* **The producing median.** It is a median over a membership these repairs can shift
  (an RV row falling far enough could leave the producing set, as Blix's Lightbound
  Cleave did in Block B). Direction not predicted; it is reported with its `n`.
* **Anything about the holdout** (unspent).
* **That the sim gets closer to reality.** C1 and C2 both REMOVE modelled damage from
  a sim that already under-produces by ~70%, so the gate is expected to get slightly
  worse. That is the correct direction when the previous number was wrong.

---

## 🆕 RESULTS — appended in the pair commit (2026-08-08)

Run from the clean tree at the commit-child of this prereg. **Nothing above this line
has been edited.** 🆕 The published and same-member slice numbers are **identical
here** — reported as a pair regardless, per the standing rule.

| # | prediction | outcome |
|---|---|---|
| **P1** | C3 and C6 move nothing | ✅ **CONFIRMED** — every mover is an RV holder |
| **P2** | C4 moves nothing | ✅ **CONFIRMED** — same evidence |
| **P3** | Shana −2.26%, Striker −1.88% (±0.3 pp) | ✅ **CONFIRMED** — **−2.31%** and **−1.94%** |
| **P4** | every RV holder with white crits falls, none rises | ✅ **CONFIRMED** — 9 movers, RV **−1.5% to −43.1%**, **zero** rose |
| **P5** | no non-holder moves at all | ✅ **CONFIRMED** — 9 of 9 movers hold the card |
| **P6** | the headline slice does not RISE; membership unchanged | ✅ **CONFIRMED** — **30.426 → 30.040**, published **−0.385 pp**, same-member **−0.385 pp**, membership unchanged (n=24, none dropped or added) |
| **P7** | `within_tolerance` 0, `qualified` 0 | ✅ **CONFIRMED** |

**Seven of seven confirmed. Nothing falsified, nothing rescued.**

### The gate, before → after

| | before (`9267660`) | after |
|---|---:|---:|
| within ±20% / qualified | 0 / 0 | **0 / 0** |
| headline slice (n=24) | 30.426% | **30.040%** |
| same-member Δ | — | **−0.385 pp** |
| admissible-only (n=21) | 27.40% | **27.40%** |
| absent share | 58.83% | **58.83%** |
| producing median | 0.3234 (n=117) | **0.3234 (n=117)** |

**The gate got slightly worse, and that is the correct outcome.** C1 and C2 both
*remove* modelled damage from a sim that already under-produces; the previous number
was larger because it was wrong, not because it was better.

### Why P3 landed just outside its own centre, and it is not a miss

Shana's RV fell **34.1%**, not the 33.3% C1 alone implies, and Striker's **34.5%** —
because **C1 and C2 both apply to the same two characters.** The prereg predicted C1's
contribution and tolerated ±0.3 pp for exactly this; both landed inside it (−2.31 vs
−2.26; −1.94 vs −1.88). The two mechanisms are separable in principle and were not
separated here.

### The instrument earning its keep

`slice_delta_vs_previous_run` reports **published −0.385 pp and same-member −0.385 pp**
over an unchanged membership. That equality is the *evidence* the move is accuracy and
not composition — which is precisely the distinction `3l` could not make about its own
headline, and it is the first run where the block has had a real move to describe.
