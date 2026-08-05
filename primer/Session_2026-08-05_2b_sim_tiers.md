# Session 2b — Sim Tiers, Uncertainty, Stat Weights

**Date:** 2026-08-05 · **Scope:** PHASE_2 T5, T6, T7 (cheap half) · **Status:** ✅ complete

The sim produces its first end-to-end number. Getting there surfaced **four data
bugs**, two of which had been silently zeroing large parts of the catalog, and
**one correction to a live build decision**.

---

## What was built

| Module | Task | Contents |
|---|---|---|
| `core/sim/apl.py` | T5 | APL + closed condition grammar (12 types). Refuses `target_count_at_least`/`content_type_is` **by name, with the reason** — a build's AoE rotation is a different APL, never a branch |
| `core/sim/tiers.py` | T5 | `fast_sim` (closed form), `medium_sim` (deterministic timeline: cooldowns, GCD, resources, castability), `slow_sim` (Monte Carlo over combat RNG) |
| `core/sim/apl_gen.py` | T5 | Default APL from a BuildSpec: cooldowns longest-first, then damage-per-GCD, quadratic CP finishers gated at max CP, self-sustain gated on health when the profile requires it |
| `core/sim/uncertainty.py` | T6 | `sim_with_uncertainty` + `sensitivity` over **knowledge** uncertainty, from a documented policy table |
| `core/sim/weights.py` | T7 | `stat_weights` (curve + delta-stability + hit-gating), `compare_paths` |
| `cli/sim.py` | T12 | Runs all of it; no logic |
| `fixtures/` | T5 | `build_elric_paladin.json`, `apl_paladin_optimal.json`, `apl_paladin_observed.json` |
| `predictions/pred_2026-08-05_elric_paladin.md` | T9 | Pre-registered, before the next parse |

Validation: `check_sim_engine.py` is **30 checks** (was 16), all pass;
`check_core_purity.py` 0 violations across 34 files; full 19-step rebuild green.

## The four bugs, all the same shape

Each was a value keyed to one id being read for a different id, and each failed
**silently toward zero** — which is why none surfaced until a rotation ran.

1. **Trigger-reached coefficients were never served** (the 2a open question).
   `spell_scaling` was queried by card id, but a trigger-reached component's
   coefficients live on the TARGET. Now pulled per component `source_spell_id`.
   Hammerdin reproduces the confirmed **223.6–246.6** (was flat-only 122–145).
2. **Rank siblings had no magnitudes at all.** The resolver correctly redirects
   a level-60 query to the rank the character casts — onto a spell the numeric
   extractor had never decoded, because it only ever walked catalog ids. It was
   trading a *wrong* magnitude for *no* magnitude. **686 cards affected, all
   decodable the whole time**; 676 now resolve (+1,193 effect rows). Lightbound
   Cleave, Dawn Strike, Holy Finish and Consecration all went 0 → real.
3. **Weapon-percent effects were read as flat damage.** `EFFECT_WEAPON_PCT`
   stores a *percent*; emitting it as a flat added **65 damage** to Lightbound
   Cleave instead of 65% of a ~627 swing. A units error that shrinks with gear,
   so it would have looked like a scaling problem, not a units problem.
4. **`fast_sim` let the first no-cooldown ability eat the entire GCD budget.**
   Allocation order is not priority order: cooldown abilities are rate-limited
   and must be allocated first. Symptom was a one-button rotation and every stat
   weight reading 0.00.

## 🚨 The structural finding: trigger-reached damage can be DELIVERED periodically

Hour of Judgement has two effects, and only one is what the docs describe.
Effect 0 is a persistent-area periodic damage aura at 2,000 ms (its own 81 at
60). **Effect 1 is `SPELL_AURA_PERIODIC_TRIGGER_SPELL` at 500 ms**, and that is
what fires Hammer from the Heavens. Over a 10 s duration one cast produces
**5 own ticks and 20 HftH pulses** — not one.

The distinction that matters: **282987 is not periodic at all.** It is an
ordinary direct spell. What repeats is the *delivery*, so periodicity must be
read off the **triggering effect slot**, never off the triggered spell.

**Validated against real parses with no fitting.** The model predicts exactly
4.00 HftH hits per HoJ tick. Pooled over the 2026-08-04 crawl — 170
character-report groups running both — **16,491 HftH hits / 4,332 HoJ hits =
3.81** (median 3.24, quartiles 2.80–3.95 over the 43 groups with ≥20 of each).
The mild undershoot is expected: different radii, so not identical target sets.

It confirms the **ratio**, hence the relative periods, hence the structure. It
does **not** confirm the absolute 20 — the ratio is invariant to duration — and
it does **not** confirm magnitude, since the crawl records no character level.
Filed as `periodic_trigger_delivery_pulse_count`.

**Scope: 48 component rows across 34 cards** use periodic-trigger delivery.
Periods run 0.01 s–18 s; 0.01 s over 10 s would imply 1,000 pulses, so any count
above **100 is refused** — not applied, not clamped.

## 🔴 Build decision reversed: Improved Cleave goes back to the bottom

build_paladin-hammerdin v9 moved **Improved Cleave from last to #2b** on the
chase list, on the reading that Lightbound Cleave's bonus term is `9 + AP × 1.0`,
so +120% takes it from 593 → 1,305 at AP 584. **Both halves are wrong**, each
already covered by an existing hard rule:

* **wrong rank** — 9 is the Rank-1 value (SpellLevel 16); a level-60 character
  casts Rank 5, where the same slot reads **62**;
* **`EffectBonusCoefficient = 1.0` is not an AP coefficient** — it is stock
  `EffectBonusMultiplier`, whose neutral default is exactly 1.0. Session `1x`
  had already retracted this catalog-wide.

Lightbound Cleave R5 is **65% weapon damage + a flat 62 Holystrike**, with no
stated AP term. Improved Cleave 3/3 is therefore worth **+74 per hit, not +712**
— roughly a **9.6× overestimate**. §10a's ×1.48 ceiling needs its ×1.110 factor
removed. ⚠ v9's "independent corroboration" against a scouted character applied
the same formula to the same premises, so it never tested them.

**What would overturn this:** a live Rank-5 tooltip showing an `$AP`/`$SP` term.
The claim is that *no source states a coefficient* — not that one is proven
absent.

## Daily patch check — and 2a missed one

**2026-08-04 Darkmoon/Dawnrise:** *"Fixed a bug where mechanics that are supposed
to trigger from physical abilities would not trigger from the newly introduced
physical + magic school abilities. (Talents such as Art of War, Vengeance etc.)"*

Holystrike is such a school, and it is most of this build's pressed damage.
**Vengeance (20057) is slotted at 2/3** and triggers on direct crits — so the
build's own Holystrike crits were not feeding a card it already had equipped.
Straight buff, no action needed. **The Art of War** is named explicitly and sits
on the chase list; its trigger reliability improved.

Session 2a's check the same day reported these entries as "PvP-only reductions
plus a new talent Authority" and missed this. **Scan by affected mechanic, not
by card name** — this note names no slotted card except in a parenthetical.

## First numbers, and the honest headline

| Content | fast | medium | slow | combat RNG 95% | knowledge 90% CI |
|---|---|---|---|---|---|
| `raid_boss_st` | 586 | 602 | 602 | 555–642 | 543–589 (±5.2%) |
| `mythic_dungeon_st` | 632 | 674 | 674 | — | — |

**The owner reports ~3,600. The sim is low by ~6×, and that is the pre-registered
prediction** (`predictions/pred_2026-08-05_elric_paladin.md`). Causes are named
and ranked there; the dominant one is that **talent multipliers are not modelled
at all**, on a build whose identity is a stacked Holy multiplier chain.

⚠ **The stat weights this produces disagree sharply with the build doc's
empirical ones** (sim: weapon_damage 25, hit 17, haste 14, crit 6.1; doc: crit
2.00 best, AP 1.00 baseline). **Do not adopt the sim's weights.** The
disagreement is a diagnostic, not a result.

## What 2c inherits

* 🛑 **The optimal-vs-observed APL comparison is BLOCKED**, and the sim says so.
  `paladin_optimal` scores 602 against `paladin_observed`'s 659 — inverting §11's
  central conclusion — purely because Holy Shock resolves to 0 and the optimal
  APL spends ~9 GCDs on it. `medium_sim` names any zero-damage ability loudly and
  `check_sim_engine` asserts that it does.
* **Open question `rank_siblings_inherit_no_hidden_refs`** — a sibling inherits
  no `hidden_refs` (that column is parsed from the export, which siblings are
  absent from), so a sibling whose own record is a DUMMY loses its sub-spell
  chain. Holy Shock R4 is exactly that. **Fix this first in 2c** — it blocks the
  rotation question.
* **Talent modelling** is now the single largest error source, ahead of
  everything else combined.
* Seals are scored per cast, not per swing; auto-attacks are unmodelled;
  `Judgement` resolves to no current-pool card.
* `sensitivity()` output is ready to populate `open_questions.variance_contribution`.
