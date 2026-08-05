# Pre-registered prediction — Elric (Paladin Hammerdin), 2026-08-05

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
