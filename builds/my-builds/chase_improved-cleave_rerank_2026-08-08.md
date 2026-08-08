# Improved Cleave — chase-list re-rank after the 2026-08-10 fix

> **`FINDING 2026-08-08`** — written at `3n`'s close at the owner's request. True as of
> its date, not maintained. Supersede when a post-Monday parse of a card-holder lands.

## The one-line answer

**Improved Cleave drops from a top chase to a marginal one, and it gets *worse* the
better your main hand gets.** You hold it **0/3**, so **Monday's patch changes your
current damage by exactly zero** — this is purely a decision about whether to spend
rerolls chasing it.

## What changed

Ascension declared Improved Cleave's whole-ability multiplier a **bug** and fixed it
live **2026-08-10**: it now multiplies only the *bonus* term, not the weapon component.

On your own stat block (The Light's Hope), from `prereg_3m_b_improved_cleave.md` B5:

| | pre-fix | post-fix |
|---|---:|---:|
| Improved Cleave 3/3 adds, per Lightbound Cleave hit | **578.1** | **74.4** |
| …as a change in the card's worth | — | **−87.1%** |
| Lightbound Cleave's own per-hit damage with the card | — | **−47.5%** |

## The part that inverts the usual reasoning

The removed term is `1.2 × 0.65 × weapon_damage` — **pure weapon**. Your weapon is
**87.1%** of Lightbound Cleave's base, which is why the card loses almost all its
value. And because the surviving term is the **flat 62**:

🚨 **The better your main hand gets, the LESS this card is worth** — in absolute
damage, not just relatively. That is the opposite of the standing "percentage
multipliers are gear-proof, flat adds decay" rule, and the reason is that the card is
now a multiplier *on a flat*, which behaves like a flat.

## Verdict

| | |
|---|---|
| **Chase it?** | **No — not with a guarantee slot, and not with targeted rerolls.** |
| **If it rolls anyway?** | Slot it. 74.4/hit on an off-GCD ability you queue at all times is still free damage. |
| **Reset at Gabril Mewell?** | **Not applicable — you hold it 0/3.** The reset question only arises for a holder. |
| **What it displaces** | Nothing now. Anything previously ranked below it on the strength of the ~578 figure should move back above it. |

⚠ **`build_paladin-hammerdin.md` v9/v12 still rank this card a top chase** on the
pre-fix arithmetic (§7 and the §12 chase table). That document is a **frozen v1
artifact** by owner decision and is not being rewritten; read this note against it.

## What would change this verdict

A **post-Monday parse of a cohort member who holds the card** — Blix, Lootgoblin,
Robottikyrpa and Nodding all run a hybrid Cleave. Their pre/post-fix Cleave damage is
the only clean check that the patch shipped as described, and it **cannot** come from
your own captures, because you hold no Improved Cleave and pre- and post-fix
predictions for you are identical (`2026-08-08_elric_lbc_baseline_imbue_test/README.md`).

🔬 One cheap control you *can* run: an identical Lightbound Cleave dummy capture after
Monday should show **no change at all** — the changelog says *"Regular Cleave was
unaffected"*, and you hold no IC. If it moves, something else changed in the patch.
