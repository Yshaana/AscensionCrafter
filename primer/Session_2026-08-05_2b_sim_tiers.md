# Session 2b — Sim Tiers, Uncertainty, Stat Weights

> **`HISTORICAL`** — the record of a past session or a completed phase. Immutable. It **may contain claims that are false today**, and that is correct rather than a defect — it records what was believed at the time. **Never citable as current truth.** *(Classified `3f` F8c, 2026-08-07.)*

**Date:** 2026-08-05 · **Scope:** PHASE_2 T5, T6, T7 (cheap half) · **Status:** ✅ complete

The sim produces its first end-to-end number. Getting there surfaced **four data
bugs**, two of which had been silently zeroing large parts of the catalog, plus
**one structural finding about how triggered damage is delivered** and **one
retraction of my own that the owner caught within the session**.

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

## 🧠 A retraction of my own, made and corrected within the session

I retracted v9's Improved Cleave *mechanism* (below) — correctly — and then
carried the demolition straight through to its *conclusion*, demoting the card to
the bottom of the chase list. **The owner flagged it immediately against direct
in-game experience, and the numeric field settled it against me.**

Improved Cleave is `EffectAura 108` = `SPELL_AURA_ADD_PCT_MODIFIER` with
`EffectMiscValue = 8`, and SpellModOp 8 is **`SPELLMOD_ALL_EFFECTS`**. Its +120%
multiplies *every* effect of the spells in its class mask — the 65% weapon
component as well as the flat. Lightbound Cleave goes **~470 → ~1,033 per hit**
at Elric's weapon damage, on an ability carrying over half his pressed damage.
**It stays a top-tier chase.**

Two lessons worth more than the card:

1. **Retracting a mechanism does not retract the conclusion it supported.** The
   conclusion has to be re-derived independently. v9 was right about this card
   for a reason it never stated.
2. **This project's "never read a magnitude from tooltip prose" rule extends to
   SCOPE.** The tooltip says *"increases the bonus damage done by your Cleave
   ability"* — naming one term — while the modifier op says all of them.
   Generalised: read amplifiers from auras **107/108 + `EffectMiscValue`
   (SpellModOp) + `EffectSpellClassMask`**, in numeric fields. **This is the
   foundation 2c's talent modelling should be built on**, not tooltip parsing.

## 🔴 Still retracted: v9's Improved Cleave FORMULA (the ranking is unaffected)

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
stated AP term. The card is excellent because Improved Cleave multiplies a large
*weapon-damage* component, not a large AP-scaling one — §10a's ×1.110 factor is
if anything **understated**, not removed. ⚠ v9's "independent corroboration"
against a scouted character applied the same formula to the same premises, so it
never tested them.

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

## ✅ Calibrated against five real parses — and the first read was wrong

Late addition: the owner's combat logs were sitting in
`E:\Ascension Launcher\resources\ascension-live\Logs`. New tool
`tools/audit/calibrate_vs_log.py` compares the sim's BASE per-event value
(no talents, no crit) against the logged NON-CRIT average, so the ratio *is* the
unmodelled talent layer. **It verifies field alignment against three
doc-confirmed facts first and refuses to report if they fail** — the log parser
is documented as unvalidated, and my own first ad-hoc scan had the crit flag one
field off and would have produced confident nonsense.

**I read one log, drew a conclusion, then four more logs overturned it.**

**1. Within any one log, a school's abilities agree very tightly.** In
`2026-08-03-20.51` the three Holystrike abilities read **1.88 / 1.87 / 1.87**;
Hammer from the Heavens and Hour of Judgement's own tick read **2.46 / 2.49**.
Those two Holy formulas are structurally unrelated — flat 122–145 + 9.1% SP/AP
versus flat 81 + 5% SP/AP — so agreeing to 0.03 is strong evidence that **both
base formulas are correct.** Holds in every log with enough hits.

**2. The absolute multiplier is NOT a constant.**

| log | Holy | Holystrike | Holy ÷ Holystrike |
|---|---|---|---|
| 2026-08-03 20.51 | 2.48 | 1.87 | 1.32 |
| 2026-08-03 21.18 | 1.99 | 1.52 | 1.31 |
| 2026-08-04 20.07 | 1.76 | 1.40 | 1.25 |
| 2026-08-04 20.37 | 1.90 | 1.42 | 1.34 |

A **1.41× swing** between sessions — buff and gear state, not talents. The
single-log figure I first recorded (1.76 / 1.40) is one session's value and is
marked SUPERSEDED in `confirmed_facts`.

**3. The durable quantity is the school ratio: 1.31 ± 0.03.** Buff state
multiplies both schools and cancels in a ratio, leaving talent structure —
consistent with the Holy stack applying in full to Holy damage but only to the
magic half of a hybrid, with Titan's Grip's −10% physical on the weapon half.

**Pulse delivery confirmed a third time, on the owner's own character:** 259
HftH hits / 60 HoJ ticks = **4.32** against the predicted **4.00**. Independent
of the pooled crawl's 3.81. Candidate cause of the overshoot: Hammerdin triggers
the same chain, adding pulses with no matching tick. ⚠ The **absolute** count is
still unsettled — no `SPELL_CAST_SUCCESS` for Hour of Judgement appears in any
log, so pulses-per-cast could not be counted.

**Dawn Strike misses its group in all four logs, always low** (1.43 / 1.17 /
1.11 / 1.13 vs peers at 1.87 / 1.50 / 1.40 / 1.42). A bias that reproduces in
every sample is neither noise nor buff state — its sim base is **~25–30% too
high**. Suspect effect type 121 (normalized weapon) being counted alongside type
31 (weapon-percent), which would affect **every** ability carrying type 121.

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
  everything else combined. **Owner decision: general extractor for coverage +
  hand-seed the ~24 slotted talents.** Build the extractor on **auras 107/108 +
  `EffectMiscValue` (SpellModOp) + `EffectSpellClassMask`, from numeric fields** —
  the Improved Cleave case above proves tooltip prose understates modifier scope,
  so tooltip parsing is the wrong foundation.
* 🛑 **Do NOT fit one talent multiplier from pooled logs.** It swings 1.41×
  between sessions on buff state. Fit per-log with buff state known, or model
  buffs explicitly and let the residual be talents. **Target: reproduce the
  1.31 Holy÷Holystrike ratio**, not the absolute values.
* ⚠ **Settle two calibration outliers BEFORE fitting**, or they drag the
  constants: `dawn_strike_sim_base_is_systematically_too_high` (reproduces in all
  four logs; likely a type-121/type-31 double count affecting many abilities) and
  `consecration_and_dawn_strike_calibration_outliers` (Consecration ~4×).
* 📅 **Re-run the Phase 1 baseline capture on 2026-08-07** (owner decision) before
  the phase flip on the 8th. Overwrites in place.
* Seals are scored per cast, not per swing; auto-attacks are unmodelled;
  `Judgement` resolves to no current-pool card.
* `sensitivity()` output is ready to populate `open_questions.variance_contribution`.
