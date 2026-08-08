# PREREG — `3o` Block C: the imbue's attack-power constant, 88.0 → 80.0

> **`FINDING 2026-08-08`** — a pre-registration, written and committed BEFORE the
> code change it scores. Frozen on landing: a prereg corrected after its result is
> known is not a prereg. Scored in the `3o` session record.

**Change under test.** `core/sim/buffs.py :: CONSECRATED_WEAPON_IMBUE.attack_power`
**88.0 → 80.0**, one constant, nothing else.

**Why.** `3n` retired the "+88 AP per imbue" figure in both seeds from the
2026-08-08 three-step capture (`data/source/captures/2026-08-08_elric_lbc_baseline_imbue_test/`:
AP 141 → 221 → 301, i.e. **+80 and +80**, both steps linear on a settled sheet).
Its commit said "and its blast radius" and did not reach the one site where the
number is **code** (`AUDIT_3N` F1). This is that repair.

⚠ **The field's semantics decide the value.** `Buff.attack_power` is documented
*"post-Deadliness observed"*, and `apply_buffs` adds it to `extras` **without**
applying the Kings `stat_multiplier` (that multiplier touches `stats` only). So
the constant must be the observed AP delta in an **unbuffed** state, which is
exactly what the 2026-08-08 capture measures. 80.0 it is — not the raw decoded 73
(which the sim would then have to multiply by a Deadliness term it does not model
here), and not 88.

## 🚨 The 88-vs-80 question is ANSWERED, and it is not fitted

Owner, 2026-08-08, unprompted by any of our numbers: the `2e` **+88 was measured
with Blessing of Kings up** (`stat_exports_incremental_buffs.txt` steps 4→5, AP
258 → 346, gear identical throughout); the 2026-08-08 **+80 was unbuffed**. And
**80 × 1.10 = 88 exactly**.

That unifies it with the standing open question
**`str_to_ap_1_21_under_buffs`** — where buffed states show ~1.21 AP per Strength
against an unbuffed 1.10, and **1.21 = 1.10 × 1.10**. One mechanism, appearing in
two places, not two questions.

🛑 **It is registered, NOT modelled.** Nothing here multiplies the imbue by a
second 1.10 under Kings. The mechanism is unexplained, and modelling an
unexplained multiplier because it makes a number come out right is fitting.
**The discriminator, stated in advance:** one export pair on the same board, imbue
delta with **Kings alone** up versus with **no buffs**, predicting **+88 against
+80**. Until that is captured, 80.0 is the value measured in the state the field
is defined in, and the buffed case is a **named residual**.

⚠ **Consequence, stated before the run:** for a cohort member who has Kings AND
the imbue, this change may make the sim *less* right, if the owner's unification
holds for them too. That is accepted deliberately — the alternative is keeping a
constant that is wrong in the state the field documents, because it is
accidentally right in a state the field does not model.

## The affected population, measured BLIND (before the change, from the baseline)

Derivation is `core/builds/group_buffs.py`: `consecrated_weapon`, scope **self**,
card **200809**, matched on `snapshot_cards.card_spell_id`. It reaches the gate
via `derive_buffs` → `calibrate_crawled.py:1042`, and it **stacks per weapon**.

⚠ Counted on `card_spell_id`. The first count this session used `spell_id` and
returned **0 of 35** — the corpus stores Consecrated Weapon's `spell_id` as
**200814** (a rank sibling) and its `card_spell_id` as 200809. A wrong-column
zero and a real zero are indistinguishable by eye, which is this project's own
id-space rule biting inside its own analysis.

**6 of 35 tuning-set members hold the card:**

| member | baseline delta % | coverage % | baseline slice % | admissible | in the ≥20% slice band |
|---|---:|---:|---:|:--|:--|
| Blix | −94.82 | 68.0 | 7.62 | yes | yes |
| Deyindra | −53.87 | 26.6 | 173.43 | **NO** | yes |
| Lootgoblin | −97.35 | 60.8 | 4.35 | yes | yes |
| Nodding | −97.22 | 61.8 | 4.51 | **NO** | yes |
| Xoller | −93.85 | 18.0 | 34.19 | yes | no (below floor) |
| Xyz | −93.59 | 54.2 | 11.83 | yes | yes |

Baseline (committed, `63f295e`): **0 within ±20% / 0 qualified**, slice
**30.150% (n=24)**, producing **0.2571 (n=123)**, absent **59.0%**.

## Predictions

Each carries what would falsify it. **No prediction here is one-sided.**

| # | prediction | falsified by |
|---|---|---|
| **P1** | Exactly **6** members derive `consecrated_weapon`, and they are Blix, Deyindra, Lootgoblin, Nodding, Xoller, Xyz | any other count, or any other member moving |
| **P2** | **All 6 move in the same direction: sim damage FALLS**, so `delta_pct` becomes more negative for each | any holder's `delta_pct` rising, or landing exactly on its baseline |
| **P3** | The other **29 members do not move AT ALL** — `delta_pct` byte-identical to baseline | any non-holder's `delta_pct` differing in any digit |
| **P4** | The move is **small**: every holder's `delta_pct` changes by **< 1.0 pp** in magnitude | any holder moving ≥ 1.0 pp |
| **P5** | `within_tolerance` stays **0** and `qualified` stays **0** | either becoming non-zero |
| **P6** | The headline slice moves **< 0.5 pp**, and **published Δ = same-member Δ** (membership unchanged, since no member crosses the 20% coverage floor on a ≤1 pp damage move) | a move ≥ 0.5 pp, or the two deltas differing |
| **P7** | The **producing median** moves by **< 0.02**, because it is a per-ability-row statistic and only 6 of 35 members' rows shift slightly | a move ≥ 0.02 |
| **P8** | The **absent share stays 59.0%** — this change moves no damage into or out of a sim key | any change in the absent share |

🔬 **P2 is the one that could genuinely surprise.** Lowering AP lowers damage only
if these characters' modelled damage actually depends on AP; if a holder's kit is
entirely flat-and-SP, its delta will not move and **P2 is falsified, not excused**.

## Mutation

**M72** — restore `attack_power=88.0`. Red against an arm that asserts the buff's
**magnitude** against the capture-measured value (not against a label, and not by
re-implementing the lookup — `3g` G5). Green on the repair.

## What this prereg does NOT claim

It does not claim the gate improves. It does not claim 80 is right for a
Kings-buffed character — the owner's unification says it probably is not, and that
residual is registered rather than modelled. It claims only that the constant now
matches the state the field documents, and that the cohort effect is the one
predicted above.
