# Capture list for the next session — agreed 2026-08-05, end of `2c`

**Claude: ask about this FIRST THING next session.** The owner committed to
producing this bundle when he next gets home.

Three items, in strict priority order. **Item 1 is worth more than 2 and 3
combined**, and item 2 is worth much less without item 1.

---

## 1. 🔴 A stat block taken in the SAME session as the logs

This is the single highest-value piece of evidence the project can obtain, and
it is the one thing that cannot be recovered afterwards.

**Use `addons/AscensionCrafterExport/`**, not screenshots — it produced the
controlled Path-of-Strength-vs-Duality comparison on 2026-08-04, and a parseable
export beats a picture we have to transcribe.

**Capture, at minimum:**

| | why |
|---|---|
| **Weapon damage (min–max) and speed, both hands** | 🔴 the whole reason. Holystrike abilities are **86–100% weapon damage** and Holy abilities are **0%**, so a wrong weapon number corrupts every cross-school comparison at ~1:1 |
| AP, SP, Bonus Healing | the coefficient half of every formula |
| Melee crit %, spell crit %, hit, haste, expertise, ArP | crit is the build's best stat and the sim currently takes it from a 2026-08-03 sheet |
| Str / Agi / Int / Sta / Spi | needed to check the Duality conversions |
| **The active Path**, stated explicitly | still an open question on this character |
| Full talent list **with ranks**, full ability bar | a 3/5 card is a different build |

### 🛑 The one rule that makes or breaks this

**The stat block and the logs must be the same session — same gear, same spec,
nothing changed between them.** If gear changes, capture again.

That is not pedantry: the sim's current weapon input comes from an older King
Gordok parse, and that single mismatch is what forced session `2c` to demote the
project's headline calibration number (`holy_holystrike_ratio_weapon_input_confound`).
Repeating it would waste the logs.

### "Unbuffed" — what actually matters

**Known** buff state, not zero buff state. Passive talent auras are fine: they
are constant and are part of the character. What must not happen is an unrecorded
raid buff or consumable inflating the sheet.

Simplest reliable procedure: **take the export standing in a city or at the
dungeon entrance, before any group buffs, then zone in and start logging.** If
you self-buff (seals, aura, anything you keep up), that is fine — just say so.

---

## 2. Two dungeon logs, recorded right after the capture

With item 1 in hand these become far more informative than the existing five.

**What they settle:**

* **The falsifiable half of `2c`'s logged prediction.** The sim currently misses
  by ~1.86× on Holy and ~1.37× on Holystrike, and the misses group by school.
  Two readings remain: an unmodelled school-scoped amplifier (structural), or
  buff state (session-specific). **If the residual reproduces at the same values
  against a known stat block, it is structural.** If it moves, it was buffs.
* **Buff extrapolation from the other players — yes, this works, and it is a good
  idea.** A 3.3.5 log records `SPELL_AURA_APPLIED` for every buff on you,
  including who cast it, so the group's contribution can be enumerated rather
  than guessed. That is exactly the "model buffs explicitly and let the residual
  be talents" path the phase doc asks for.
* **Two logs rather than one** so a difference between them can be attributed.

**Useful but optional:** if one of the two runs is mostly single-target, it also
settles `periodic_trigger_delivery_pulse_count` — the absolute Hammer from the
Heavens pulse count per Hour of Judgement cast, which no log so far has been able
to answer because none contains a `SPELL_CAST_SUCCESS` line for HoJ.

---

## 3. Live tooltips — a bounded list, highest value first

"All the missing tooltip info" is unbounded, so here is the actual list, ordered
by how much damage the sim currently cannot see. **Anything from group A is worth
more than all of group C.**

### A. Damage sources the sim cannot resolve at all

Sorted by hit count in the owner's own logs. Each is real damage with no
modelled magnitude:

| Ability | logged id | hits | avg | why it is unresolved |
|---|---|---|---|---|
| **Righteous Vengeance** | 61840 | 1,259 | 259 | 30% of a crit as a DoT; the sim has no source-damage input for it |
| **Consecration** | 270768 | 1,247 | 228 | Purification By Light's own version, out of catalog |
| **Consecrated Holy Weapon** | 200818 | 1,223 | 445 | ⚠ **NOT** the catalog's `Consecrated Weapon` (200809) — confirmed different |
| **Arcing Light** | 954923 | 312 | 564 | not in the catalog at all |
| **Seal of Command** | 20424 | 208 | 454 | the logged id differs from the catalog's 20375 |
| **Blades of Light** | 913445 / 913446 | 375 | 629–677 | main and off-hand both unresolved |
| **Sword Specialization** | 16459 | 158 | 702 | the extra-attack proc |
| **Whirling Light (Off-hand)** | 907790 | 148 | 579 | off-hand variant absent |
| **Righteous Smite** | 273123 | 125 | 477 | no known magnitude |
| **Judgement of Command** | 20467 | 21 | 1,300 | hits hard, rarely pressed |

### B. Two tooltips that would settle a named open question outright

* 🎯 **Holy Shock, rank 4** — settles `holy_shock_bonus_coefficient_0429`. The
  measurement says there *is* an SP term and that 0.429 is close but ~5% too
  large. **A tooltip stating the coefficient closes it immediately**, and I will
  not seed a number without it.
* 🎯 **Lightbound Cleave, rank 5** — this is the *stated overturn condition* for
  the "no AP term" claim (build doc v12). If the live tooltip shows an `$AP` or
  `$SP` term, that claim is retracted. If it shows only weapon % + flat, it is
  confirmed from tier 1 instead of tier 4.

### C. The six talents whose auras are not understood

These use auras outside stock 3.3.5, so no numeric field explains them, and they
currently contribute **nothing** to the model:

**Sword Specialization** and **Accuracy** (aura 333) · **Wrecking Crew** and
**Spellblade** (aura 231) · **Dual Wield Specialization** (aura 122) · **Twin
Disciplines**' second effect (aura 136).

And four whose effect is a **server-side script** (`SPELL_AURA_DUMMY`), where a
tooltip is the *only* possible source: **Holy Specialization**, **Judgements of
the Wise**, **Mental Quickness**, **Righteous Vengeance**.

> Value beyond this build: decoding aura 231 and 333 generalises to every card
> that uses them, not just these four.

### D. Nice to have

* **"Brutal Crusader"** on Light's Hope — open since v5, and it changes Strength's
  weight if it is a Crusader-family proc.
* **Dawn Strike, rank 8** — its formula matches Lightbound Cleave's in our data
  but the game pays it 25% less; a tooltip may name the difference.

---

## What NOT to spend effort on

* Screenshots of stats the addon already exports.
* Tooltips for abilities the sim already resolves correctly (Hammer from the
  Heavens, Hour of Judgement, Whirling Light main-hand, Dawnreaver) — those are
  validated to within 3.2% by the weapon-free pair ratios and need nothing.
* A long fight specifically for sample size. Two ordinary dungeon runs are
  plenty; the binding constraint is the **stat block**, not the hit count.
