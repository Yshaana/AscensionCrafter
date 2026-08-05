# Pre-registered prediction — Elric (Paladin Hammerdin), 2026-08-05

> ## ✅ OUTCOME — reconciled same day against a real parse
>
> Source: `2026-08-04-20.07.21 WoWCombatLog.txt` (Elric, 60,427 events,
> 2,179,963 damage). Parsed with `tools/log_parser/parse_log.py`; field
> alignment verified against three doc-confirmed facts before use (Consecration,
> Righteous Vengeance and Hour of Judgement all parse at 0% crit, matching the
> aura-tick rule; melee 35.6% vs Holystrike 46–53%, matching the Holystrike
> spell-table verdict).
>
> **The prediction that mattered — "this is wrong, and here is why" — holds, and
> the error decomposes almost exactly as predicted.** Comparing the sim's base
> per-event value against the logged NON-CRIT average, at AP 584 / SP 533:
>
> | ability | school | sim base | logged non-crit | ratio |
> |---|---|---|---|---|
> | Hammer from the Heavens | Holy | 235 | 410 | **1.74×** |
> | Hour of Judgement (own tick) | Holy | 137 | 243 | **1.78×** |
> | Lightbound Cleave | Holystrike | 470 | 661 | **1.41×** |
> | Whirling Light | Holystrike | 408 | 576 | **1.41×** |
> | Dawnreaver | Holystrike | 314 | 436 | **1.39×** |
> | Dawn Strike | Holystrike | 476 | 528 | 1.11× ⚠ |
> | Consecration | Holy | 56 | 199 | 3.55× ⚠ |
>
> **The ratios cluster by school.** ⚠ **Superseded by the five-log run below —
> these are ONE SESSION's values, not constants.**
>
> **Why this also validates the base formulas.** Hammer from the Heavens
> (flat 122–145 + 9.1% SP + 9.1% AP) and Hour of Judgement's own tick
> (flat 81 + 5% SP + 5% AP) are structurally unrelated formulas, yet they land on
> the *same* multiplier (1.74 vs 1.78). If either base were wrong the two would
> not agree. The same holds across the three Holystrike abilities at 1.39–1.41.
>
> **Pulse delivery confirmed on the owner's own character.** 259 Hammer from the
> Heavens hits against 60 Hour of Judgement ticks = **4.32**, versus the **4.00**
> predicted from the 500 ms trigger period against the 2,000 ms tick period.
> Independent of the pooled crawl's 3.81. The mild overshoot has a candidate
> cause: Hammerdin (282983) triggers the same pulse chain, adding HftH hits with
> no corresponding HoJ tick. ⚠ Still does not settle the ABSOLUTE count — no
> `SPELL_CAST_SUCCESS` for Hour of Judgement appears in this log, so pulses-per-
> cast could not be counted directly.
>
> **Two abilities came back as outliers and are NOT explained:**
> * **Consecration 3.55×** — far outside the Holy group. Suspect a missing
>   component or a rank issue, not the talent stack.
> * **Dawn Strike 1.11×** — far below its Holystrike peers. Its effect structure
>   (121/80/31) differs from the others, so its sim base is the likely error.
>
> **Holy Shock resolves to no events at all**, as predicted — and the log shows it
> is real and material: 36 casts, 1,380 non-crit average, 3.0% of damage.
> Confirms `rank_siblings_inherit_no_hidden_refs` is worth fixing first in 2c.
>
> ⚠ **Caveat on all ratios:** the sim base uses the 2026-08-03 sheet (AP 584 /
> SP 533) and weapon damage from the older King Gordok parse. Not a same-moment
> comparison.
>
> ---
>
> ### Extended to all five logs — and it changes the conclusion
>
> `tools/audit/calibrate_vs_log.py --character Elric --all-logs`. Three separate
> results, and conflating them was my mistake above:
>
> **1. Within any one log, a school's abilities agree very tightly.** In
> `2026-08-03-20.51` the three Holystrike abilities read **1.88 / 1.87 / 1.87**;
> Hammer from the Heavens and Hour of Judgement's tick read **2.46 / 2.49**. Two
> structurally unrelated Holy formulas agreeing to 0.03 is strong evidence
> **both base formulas are correct.** Holds in every log with enough hits.
>
> **2. The absolute multiplier is NOT a constant.**
>
> | log | Holy | Holystrike | Holy÷Holystrike |
> |---|---|---|---|
> | 2026-08-03 20.51 | 2.48 | 1.87 | 1.32 |
> | 2026-08-03 21.18 | 1.99 | 1.52 | 1.31 |
> | 2026-08-04 20.07 | 1.76 | 1.40 | 1.25 |
> | 2026-08-04 20.37 | 1.90 | 1.42 | 1.34 |
>
> A **1.41× swing** between sessions. That is buff and gear state — raid buffs,
> consumables, Vengeance uptime, Avenging Wrath windows — not talents.
>
> **3. The durable quantity is the SCHOOL RATIO: 1.31 ± 0.03.** Whatever buff
> state multiplies both schools cancels in the ratio, leaving the talent
> structure. **That is the number a correct talent model must reproduce**; the
> absolute values are session-specific calibration inputs.
>
> **Dawn Strike misses its group in all four logs, always low** (1.43 / 1.17 /
> 1.11 / 1.13 against peers at 1.87 / 1.50 / 1.40 / 1.42). A bias that reproduces
> in every sample is not noise — its sim **base is ~25–30% too high**. Suspect
> effect type 121 (normalized weapon) being counted alongside type 31
> (weapon-percent). If so it affects every ability carrying type 121.
>
> **🛑 Consequence for 2c: do not fit one talent multiplier from pooled logs.**
> Fit per-log with buff state known, or model buffs explicitly and let the
> residual be talents.

---


**Logged BEFORE the next parse, never fitted afterwards** (PHASE_2 T9's discipline).
The `predictions` table itself is session `2c`; until it exists this file is the
ledger, and it carries the same stamps a row would.

| Stamp | Value |
|---|---|
| build | `fixtures/build_elric_paladin.json` (build_paladin-hammerdin.md v11) |
| APL | `fixtures/apl_paladin_optimal.json` |
| sim_version | `2b` (session 2026-08-05) |
| data_version | `ascension.db` rebuilt 2026-08-05, 19 steps |
| realm / season | Darkmoon / S10 |
| patch | Darkmoon 2026-08-04 |

## The prediction

| Content | fast | medium | slow (mean) | combat-RNG 95% band | knowledge-uncertainty 90% CI |
|---|---|---|---|---|---|
| `raid_boss_st` (1 target, +3, 75s) | 586 | **602** | 602 | 555 – 642 | 543 – 589 (±5.2%) |
| `mythic_dungeon_st` (1 target, +2, 60s) | 632 | **674** | 674 | — | — |

The two uncertainty numbers are deliberately reported separately and must not be
merged: the combat-RNG band is how much one pull differs from another, the
knowledge band is how much the answer moves because we do not know the inputs.

## 🛑 The prediction that actually matters is that this is WRONG, and by how much

The owner's own reported figure is **~3,600 DPS**. The sim says ~600. **It is
low by roughly 6×, and that gap is the point of logging this.** Every known
cause is named below; if the real error decomposes differently, the model is
wrong somewhere we have not looked, which is exactly what calibration (2c) is
for.

Named causes, largest first:

1. **No talent modelling at all** (2a limitation, carried). The entire Holy
   multiplier stack — Holy Power 5/5, Holy Specialization 5/5, Twin Disciplines
   5/5, Answered Prayers 5/5, Holy Focus 5/5, Vengeance, Deadliness, Wrecking
   Crew — contributes exactly nothing. On a build whose identity *is* stacked
   Holy multipliers this alone plausibly accounts for most of the 6×.
2. **Holy Shock resolves to 0 damage** (open question
   `rank_siblings_inherit_no_hidden_refs`). It is cast 9 times and scores
   nothing.
3. **Seals are modelled per CAST, not per swing.** Seal of Command and Seal of
   Vengeance are cast once and score ~130 and ~290; in reality they ride every
   landed melee swing.
4. **Auto-attacks are not in the model.** Only 4.2% of damage per the build doc,
   so small — but not zero.
5. **`Judgement` is missing entirely** — no card in the current pool resolves to
   that name, so a rotation priority is simply absent.
6. **Righteous Vengeance's 30% crit-damage DoT is not modelled**, and the build
   doc measures it at 6.4–9.0% of total damage.

## Secondary prediction, and why it is currently untestable

`apl_paladin_optimal` scores **602** and `apl_paladin_observed` scores **659** —
i.e. the model currently says the *starved* rotation is better, inverting build
doc §11's central conclusion. **This is a data artifact, not a result.** Holy
Shock resolves to 0, the optimal APL spends ~9 GCDs on it, so those GCDs are
scored as wasted. `medium_sim` names the zero-damage ability in its warnings and
`check_sim_engine.py` asserts that it does, precisely so this cannot be quoted
as a finding. **Re-run this comparison once Holy Shock resolves.**

## How to settle it

`tools/log_parser/parse_log.py` on any existing combat log gives, for free:

* **Hammer from the Heavens hits per Hour of Judgement cast in a SINGLE-TARGET
  fight** — settles `periodic_trigger_delivery_pulse_count`, the largest
  structural unknown (predicted: 20).
* **Per-non-crit HftH damage** — predicted 224–247 at AP 584 / SP 533.
* **Lightbound Cleave non-crit average** — predicted base 446 before talent
  multipliers; the build doc measured 703, and the ratio is a direct read on how
  much the unmodelled talent stack is worth.
