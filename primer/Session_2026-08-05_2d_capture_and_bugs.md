# Session 2d — the capture bundle, and three things the game got wrong

> **`HISTORICAL`** — the record of a past session or a completed phase. Immutable. It **may contain claims that are false today**, and that is correct rather than a defect — it records what was believed at the time. **Never citable as current truth.** *(Classified `3f` F8c, 2026-08-07.)*

**Date:** 2026-08-05 (evening) · **Scope:** `PHASE_2D` T0–T1, then wherever the
evidence led · **Status:** ⚠ partial — T1 consumed and far exceeded, **T2–T10 not
started** and carried into `PHASE_2E_buffs_and_carryover.md`.

This session is not the shape it was planned as, and the deviation was worth it.
It was meant to deliver an in-game task list, consume the capture bundle, then
spend most of its budget writing a buff model and closing sim gaps. Instead the
owner ran an unusually productive live testing loop, and **three separate
in-game findings turned out to invalidate premises the project had been building
on** — two of them premises this project had itself confirmed. Recording the
findings and their consequences was the higher-value use of the session; the
code work is carried forward intact.

**The session's own honest failure:** the code tasks were repeatedly deferred
inside the turn ("I'll start while you play") and never begun. `2e` starts with
them.

---

## 1. The capture bundle arrived, and it is the best evidence set the project has

Everything is in `data/source/captures/2026-08-05_elric_2d/` with a README
recording provenance and the traps.

* An **unbuffed stat export** in the same session as the logs — the thing
  `NEXT_CAPTURE.md` called the binding item, obtained.
* A **fully-buffed export** minutes later — so buff deltas are measurable
  directly rather than modelled (Kings **+10% on every stat**, exact; Arcane
  Brilliance **+31 Int / +27 SP**).
* **Three relog-separated path captures** (Strength / Intelligence / Duality),
  which turned into the session's biggest finding.
* **Four dummy logs**: a buffed execute-range window, a 10-minute proc test, a
  Lightbound Cleave isolation window plus control, and a baseline window.
* The **Holy Shock R4 tooltip**, matching `2c`'s sub-spell extraction byte-exactly
  (562–608 / 676–732) — a tier-1 confirmation of the whole rank-sibling fix.
* The **55-id board export**: all resolve, every talent rank matches build doc §7.

---

## 2. 🚨 Path of Duality is broken, and it invalidates our calibration inputs

The owner read the public bug database and found Duality (`129243`) reported
broken by **multiple independent players**, in ways that match measurements this
project had been treating as mysteries:

| Reported | Our corroboration |
|---|---|
| AP bonus **cycles on/off every ~10–15 s** (one player: 832 ↔ 1128, Δ = their Str) | Elric read **174 ↔ 307**; 160×1.10 = 176 (off) vs (160+121)×1.10 = 309 (on) |
| SP grant reduced to **"a difference of 19 Spellpower"** | Our trio measured **+19** exactly |
| 2H +6% damage / 1H +10% haste **do not work** | 🛑 `stats.py` was applying the 6% — removed |

**Consequence: every historical calibration log had Attack Power oscillating
mid-parse.** That is a strong candidate for part of the 1.41× between-session
multiplier spread `2b` recorded. **What survives** is anything measured as a
ratio inside one log between abilities sharing the same input dependence — the
pair ratios, the Holy Shock coefficient, every proc-rate result, crit tables.
**What is compromised** is absolute calibration and anything reading AP as a
constant.

**Owner decisions:** ignore PoD logs for absolute calibration; do not recommend
PoD even when sheet arithmetic favours it; he plays **Path of Intelligence**
going forward; and **the project must track bug fixes** — a watch list with
changelog keywords now lives in `bugs/README.md`.

### The three retractions this forced

1. ❌ **"Duality applies a 1.895× SP amp"** (confirmed 2026-08-04) — retracted.
   The clean relog-separated trio measures **no amplifier, a flat +19**. The
   ×2.0 doubling belongs to **Path of Intelligence**, whose tooltip says so; the
   project attributed it to the wrong path for two document versions. The
   2026-08-04 test used rapid toggling and cannot be repaired after the fact.
2. ❌ **"Duality converts Str→AP at 0.548×"** — retracted. Two agreeing
   measurements of an *oscillating* quantity are two samples of one phase, not a
   rate. When it applies, the tooltip's 100% is exact.
3. ❌ **"Hit and crit rating are unified stats"** (build doc §10) — retracted.
   They are unified in *gear*; Duality's cross-crit conversions grant **rating**
   (~3.4 stat per rating point) and split them: 238 melee vs 187 spell.

### And a diagnosis of my own, wrong twice

I filed the AP behaviour first as *"stale until relog"*, then — after the owner
watched the sheet settle — as *"a ~5–10 s settle delay"*. Both wrong: it is an
indefinite oscillation. **A settle delay and an oscillation look identical
through a single before/after pair;** distinguishing them needs repeated
sampling over minutes. `bugs/bug_path-switch-stale-stats.md` keeps both wrong
diagnoses on the record.

---

## 3. 🚨 Hammerdin does not proc from Judgement or Holy Shock

The owner asked whether the cooldown reduction was working. It is — but the
*trigger set* is not what the tooltip says. A dedicated 10-minute dummy test,
counting standalone hammers on the primary target only:

| Pressed | Procs / casts | vs 20% stated |
|---|---|---|
| Dawnreaver | 15–17 / 119 | ✓ consistent |
| **Holy Shock** | **1 / 78** | ✗ |
| **Judgement** | **0 / 51** | ✗ |

Combined 1 in 129 against ~26 expected — **p < 10⁻⁹**. The −4 s reduction itself
works (~4 s per observed proc; press gaps 69.4 s / 75.9 s against a 90.0 s base)
and there is **no internal cooldown** (procs chained 4 s apart).

**Suspected mechanism, offered as a guess:** the failing abilities are exactly
those that deliver damage through a *second* spell (Holy Shock's press is a
dummy → 25902; a Judgement press damages via the seal → 20467), while Dawnreaver
and Hammer of Wrath carry damage on the pressed spell. **If that generalises it
affects every "damaging X abilities" engine on the server** — filed as open
question `hammerdin_trigger_set_excludes_trigger_delivered_damage`.

**Build-doc consequence:** §2's class-tag table and §11's rotation priority are
both built on Judgement and Holy Shock feeding this engine. They do not.
**Dawnreaver is the engine driver.** Submitted as
[tracker #200295](https://ascension.gg/bugtracker/view/200295); the report was
rewritten in the owner's voice per house style, with the evidence kept in a
never-submitted notes section.

---

## 4. Lightbound Cleave feeds nothing — and that is what makes it portable

An isolation window (204 s, LC only, one dummy) plus a 72 s normal-rotation
control in the same log:

* **Hammerdin: zero** from 53 LC hits + 70 white swings. The pre-patch verdict
  survives the 2026-08-03 off-GCD proc fix — closes `lightbound_cleave_post_patch_procs`.
* **Purification By Light: zero**, while the control window produced 14
  Consecrations and 2 Exorcisms. **New:** LC is 65% weapon damage and PBL's
  intake reads *"weapon-damage spells and abilities"* — the intake is narrower
  than its wording.
* **Seal of Command riders: autos only** — all 7 procs at exactly 0.00 s from a
  white swing, ~3 s from any LC hit.
* **JotTH: no verdict** — never cast in either window.

The control window is what makes the zeros mean anything; without it a zero says
"the engines were quiet tonight".

**This became the session's design contribution.** The owner observed that LC +
Improved Cleave is *"a good Kit for any melee build"* — and engine-inertness is
precisely what makes a kit portable. Written up as **Package 4: The Cleave Kit**
in `builds/shared/synergy_portable-multiplier-packages.md`, including the
verified roster: **all eight Cleave school variants carry the byte-identical
family-4 mask `[4194304,0,0]`**, so Improved Cleave's ×2.20 reaches every one,
and each `-bound` variant is a true hybrid that double-dips the host's school
stack. `PHASE_4`'s discovery section now carries the kit as a **regression
target**: when kit discovery first runs, it must rediscover this from data alone.

---

## 5. Smaller results worth keeping

* **Holy Shock's SP coefficient ≈ 0.40** (n=40 unbuffed non-crits, measured
  against HftH in the same log — a weapon-free same-school pair, so the Duality
  cycling cancels). Confirms `2c`'s direction and its "0.429 reads ~5% high"
  residual with a cleaner instrument. Still not seeded — owner decision pending.
* **First direct pulse count:** 17.9 HftH per Hour of Judgement cast (143 over 8
  casts) vs 20–21 modelled. Partially settles `periodic_trigger_delivery_pulse_count`;
  a stationary repeat would remove the radius explanation.
* **Pair ratio validated twice more** (1.743, 1.68 vs 1.718 predicted) — six logs,
  and the first two with a same-session stat export.
* 🆕 **Dummy identity is a calibration variable.** Two sessions an hour apart with
  an identical character differed 10–18% across every ability: one used a
  level-scaling "Dynamic Training Dummy", the other a fixed level-63 boss dummy.
  Put the NPC identity in capture metadata. Silver lining: we now have the same
  unbuffed character against both +0 and +3 targets, and 300+ white swings vs a
  +3 boss — the parse `melee_crit_suppression_vs_higher_level` was waiting for.
* 🆕 **Weapon imbues grant STATS.** Consecrated Weapon adds **+172 Holy SP and
  ~+61 AP** — school-scoped, so it moves Holy and general SP apart. ⚠ The
  catalog's Rank-1 sub-spell says +11/+19; the level-60 sibling is unresolved.
  **An "unbuffed" baseline is not clean unless the imbue is absent.**
* **Talent model validated exactly:** Twin Disciplines carries an unrecorded
  third effect (+5% Holy crit, aura 71), making the modelled Holy crit stack
  5+5+5 = 15 — and the sheet reads 41.47 − 26.47 = **15.00**.
* **The `2b` "Judgement resolves to no card" gap is explained**: the pressed card
  (Judgement of Light / of Wisdom) and the damaging spell (Judgement of Command
  20467) are different ids because the active *seal* selects the judgement.
* Passive layer named from the logs (Physical Quickness, Vengeance, Flurry,
  Enrage, Judgements of the Pure, Glyph of SoC, Spellblade, Witching Hourglass).
  Two remain unattributed: **Siphon Health (18652)** and **Swift Retribution
  (853484)**.

---

## 6. The architecture the owner corrected, and a four-version tangle resolved

My first response to the Duality finding was to **hardcode the bugged values as
the model**. The owner pushed back with three reasons, all correct:

1. **A fix would then require re-deriving the model** — baking a bug into the
   math makes the fix a landmine someone must remember to defuse, on a project
   whose named worst failure mode is drift between docs and reality.
2. **Other players' parses are full of the broken system** (he was unaware of the
   bug himself until he read the database). With the bug in the model, a crawled
   Duality character reads as a *worse build* rather than a working build being
   denied its stats — and that crawl is the population Phase 4 percentiles
   against.
3. **The bug is intermittent**, so neither endpoint is the truth. A single
   constant cannot express "somewhere between".

**Implemented as a three-layer separation** in `core/builds/stats.py`:
**model** = intended behaviour (default); **`SYSTEM_IMPAIRMENTS`** = a dated,
evidence-linked registry of what the server fails to deliver, applied only under
`system_state='as_measured'`; **policy** (`recommend: False`) = a flag the
recommender reads, never a change to the math. For an intermittent impairment
`as_measured` returns a **range** with `duty_cycle: None` — deliberately not
guessed, and measurable in `2e` from the bimodality of weapon-damage hits.

✅ **A detector falls out for free, and it is the owner's sharpest point:** if
parses on an impaired system systematically underperform the *intended* model,
that is the bug — and **when they stop underperforming, that is the fix landing**,
a better signal than keyword-scanning the changelog.

### The 75% clause, and four document versions reconciled

Ascension's path documentation states Duality's spell-power clause as **"boosts
Spell Power from GEAR by 75%"**, plus two named sub-abilities (*Unleashed Force*,
*Twin Flurry*). **That vindicates v3's "×1.75 itemised SP amp"**, which v4
retracted for not being visible on the live sheet.

| Version | Claim | Verdict |
|---|---|---|
| v3 | ×1.75 itemised SP amp (from the in-game tooltip) | ✅ read the **design** |
| v4 | no amp on the live sheet | ✅ observed the **broken delivery** |
| v20 | ×1.895 confirmed by a path-toggle test | ❌ contaminated toggle |
| 2d | no amp, flat +19 | ✅ observed the broken delivery again |

All four observations were correct; they described different things. The
intended-vs-delivered distinction that dissolves the tangle did not exist in this
project until the owner proposed it today. At gear SP 229 the shortfall is
~425 intended vs **271** observed — ~36%, and precisely why a bug report phrases
it as *"a difference of 19 Spellpower"*.

**Validation:** `check_sim_engine.py` is **43 checks** (was 40), all pass —
including four new ones asserting that the default mode models intended
behaviour, that the advisory and policy flag propagate, and that `as_measured`
yields a range rather than a fabricated duty cycle. Purity 39/0; 20-step rebuild
green.

## 7. What `2e` inherits

Read `primer/PHASE_2E_buffs_and_carryover.md`. In short: **all of `2d`'s code
tasks, plus four new ones** — a bug-fix watch sweep, bug-database read access via
the owner's browser (his suggestion, and the Duality finding justifies it), a
recalibration that must happen **on Path of Intelligence**, and the passive layer
this session named.

🛑 **The single most important carry-over:** do not spend effort modelling Path
of Duality until a fix ships, and exclude its parses from absolute calibration
by name.
