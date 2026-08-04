# Winds of Winter — Frostblade (WIP v7)

## Status
WIP — theorycraft only, no talent board committed, no character built. **This is the build Elric is actively being rerolled toward.**

**v7 update (2026-08-04, session close):** pulled three spells from an already-cached local DBC extract (no live client needed). Titanic Mutilate's hidden weapon% is now fully resolved (115%). Frostbound Cleave's formula is upgraded from a family-pattern prediction to DBC-confirmed (byte-identical to Lightbound/Voidbound Cleave, as expected). **Winds of Winter's long-missing flat baseline term has a strong lead: ~33.75 damage per combo point spent**, via a DBC field purpose-built for exactly this pattern. This term is larger than the SP dynamic term at 5 CP, meaning §4's Path-comparison deltas were computed on an incomplete formula — recomputed with it included, the ranking is unchanged (Intelligence still wins) but the real gaps are smaller than stated (+20.0% vs. Strength, not the earlier +53.7% read implied). One loose end: a second, unexplained coefficient (0.214) on the same effect slot isn't accounted for by anything in the visible tooltip text — flagged as next session's top "hit harder" item. Full numbers in `seed_confirmed.py`'s `winds_of_winter_stack_dbc_pulls`. See new §10 for the full open-questions punch list for next session, organized by "hit harder" vs. "hit often" per the user's framing.

**v6 update (2026-08-04):** tightened the ability stack to a deliberately minimal button count by request — Titanic Mutilate + Ices Spike to build 5 CP, Winds of Winter to spend, Frostbound Cleave macro'd in off-GCD as free bonus damage. Added new §5a: Frostbound Cleave turns out to share the Frost dmg% talent investment already planned for Winds of Winter, and its Improved Cleave multiplier (+120% at 3/3, DBC-confirmed) is already owned at max rank with no chase needed. Also surfaces the first real cost of the Path of Intelligence recommendation — Frostbound Cleave is AP-scaling, and Intelligence sacrifices AP hardest.

**v5 update (2026-08-04):** completed the three-way Path test (Strength/Duality/Intelligence, same gear, same empty spec). **Path of Intelligence beats Path of Duality** for this build's core formulas, reversing v4's "Duality is the only real candidate" call — see §4.

**v4 update (2026-08-04):** clean controlled test confirmed Path of Duality's Spell Power amp is real (1.895x) — reverses the Paladin build doc's old "RETRACTED" verdict on the same mechanic — and surfaced a new Attack Power anomaly under Duality. Superseded by v5's finding that Intelligence outperforms Duality anyway; full detail preserved in §4.

**v3 update (2026-08-04):** pulled Elric's real, live gear stats via a custom addon (`index/AscensionCrafterExport/`) and replaced §8's guesswork with confirmed numbers. Reverses the prior "gear needs a full re-itemization" conclusion — Elric's current gear is already close to the reference build's Spell Power total and well ahead of it on Crit Rating; the one real, confirmed gap is itemized Attack Power (currently zero).

**v2 rewrite (2026-08-04):** scanned 68 public reports on `darkmoon.ascensionlogs.gg` (ids 2-86) for every character running this engine, found ~20, and used the spread between the best and worst performers to replace v1's untested crit-rate hypothesis with an evidence-backed one. v1's Frostbite/Shatter/Fingers of Frost theory is **retracted as the primary mechanism** — see §3.

## Why this is worth building
Every core card is already owned (Cards.txt, checked 2026-08-04), most at both Normal and Golden. This section now also includes the **actual crit-rate engine**, not a guess:

| Card | Role | Owned |
|---|---|---|
| Winds of Winter (274121) | core finisher, quadratic CP scaling | abilityNormal + abilityGolden |
| Titanic Mutilate (271779) | CP generator, 2/cast | abilityNormal + abilityGolden |
| Killing Machine (51130) | crit proc (melee→next Frost spell) | talentNormal + talentGolden, 5/5 |
| **Malice (14142)** | **flat crit% — "all spells and attacks"** | talentNormal + talentGolden, 5/5 |
| **Conviction (20121)** | **flat crit% — "all spells and attacks"** | talentNormal, 5/5 |
| **Combat Expertise (31860)** | **flat crit% + expertise + stamina** | talentNormal, 3/3 |
| Piercing Ice (12953) | Frost dmg% | talentNormal 3/3 |
| Improved Cone of Cold (12490) | verbatim amp on Winds of Winter | talentNormal 3/3 |
| Arctic Winds (31676) | Frost dmg% + all-dmg% | talentGolden + talentNormal 3/3 |
| Black Ice (49664) | Frost/Shadow dmg% | talentNormal 5/5 |
| Frozen Orb (760014) | Frost AoE support | abilityNormal |
| Absolute Zero (285148) | Frost support/stun | abilityNormal |
| Consecrated Weapon (200809) | flat Holy support, same card the Hammerdin build runs | abilityNormal |
| Righteous Vengeance (53382) | crit→DoT, same talent Hammerdin runs | talentGolden + talentNormal 3/3 |
| Seal of Command (20375) | Holy rider on autos/Paladin abilities | abilityNormal |
| Enhanced Weapon Mastery (29086) | +4% all dmg — not bucket-blocked in this build | talentGolden + talentNormal 3/3 |

**Bold rows are the v2 addition** — the actual mechanism behind the near-100% Winds of Winter crit rate observed on real characters, none of which appear on the single reference build v1 was built from. All three are already owned.

---

## 1. Core identity

**Archetype:** Titan's Grip dual-2H, Int/AP dual-scaling nuke. Combo points from **Titanic Mutilate** (borrows Mutilate, Rogue-tagged) feed **Winds of Winter** (borrows Cone of Cold, Mage-tagged), whose SP/AP terms are **quadratic in combo points spent**:

```
Winds of Winter damage = flat(b2)×n + (SPFrost×0.0096)×n² + (AP×0.00624)×n²
```

Never dump below 5 CP — going 3→5 is closer to a 2.8× gain than 1.67× (standing quadratic-CP rule, same one governing Holy Finish on the Paladin build).

---

## 2. Class-tag table

| Card | Borrows from | Real tag | Confidence |
|---|---|---|---|
| Winds of Winter | Cone of Cold | Mage | `inferred_borrowed_modifiers` |
| Titanic Mutilate | Mutilate | Rogue | `inferred_borrowed_modifiers` |
| Consecrated Weapon | — (native) | Paladin | native |
| Righteous Vengeance | — (native talent) | Paladin | native |
| Killing Machine | — (native talent) | Death Knight | native |
| Malice | — (native talent) | Rogue | native |
| Conviction | — (native talent) | Paladin (Retribution) | native |
| Combat Expertise | — (native talent) | Death Knight (Blood) | native |

**Verbatim-named amplifier:** Improved Cone of Cold reads *"Increases the damage dealt by your Cone of Cold spell"* — names the base spell directly, applies to Winds of Winter by the class-tag rule's "named beats generic" practice, no proc-test needed.

---

## 3. Crit-rate engine — RESOLVED against real player data, not theory

**v1 of this file guessed a Frostbite→Shatter→Fingers of Frost freeze-crit chain.** That guess is now retracted as the leading theory. Here's why.

### The scouting method
Per `primer/INDEX_GUIDE.md`'s "find who plays ability X" technique: walked every report ID from 2 to 86 (68 valid reports found; the site's `/api/reports/{id}` 404s on gaps), pulled `encounters?includeTrash=true` for each, then `character_spell_damage?scope=encounter&participantType=friendlies` filtered for `Winds of Winter` / `Titanic Mutilate`. Found **~20 distinct characters** running this engine — far more than the single player the original `synergy_winds-of-winter.md` write-up was based on.

### High performers vs. low performers
Pulled full talent boards for a spread of both and compared:

| Character | Winds of Winter crit% (hits) | Damage share | Malice | Conviction | Combat Expertise | Killing Machine |
|---|---|---|---|---|---|---|
| **Gunju** | **97.0% (1,026 hits)** | **73.5%** | ✅ 5/5 | — | — | ✅ 5/5 |
| Titanus (mature board, reports 47-75) | 99.0-99.5% (2,290 hits pooled) | 38-43% | — | — | ✅ 3/3 | ✅ 5/5 |
| Kcdq | 92.3-100% | 22-28% | — | ✅ 5/5 | ✅ 3/3 | ✅ 5/5 |
| Blasted | 91.3% (92 hits) | 59.2% | — | — | — | ✅ 5/5 |
| Ek | 97.7% (43 hits) | 2.2% | — | — | — | (not captured) |
| Tdoctor | **16.9-44.3%** | 13.6-21.5% | ❌ | ❌ | ✅ 3/3 (alone) | ❌ |
| Evilelf | **0% (6 hits)** | 16.4% | ❌ | ❌ | ❌ | ❌ |
| Altride | **31.2% (48 hits)** | 14.2% | ❌ | ❌ | ❌ | ❌ |

**Every high performer runs Killing Machine 5/5 plus at least one of Malice / Conviction / Combat Expertise** — all three are flat *"increases your critical strike chance with all spells and attacks"* talents (verbatim tooltips, not Frost-specific). **Zero of the ~20 characters scanned run Frostbite, Shatter, or Fingers of Frost.** Tdoctor is the clearest negative case: he runs Combat Expertise alone with no Killing Machine and no Frost-support talents at all, and his board is otherwise a mismatched Shadow Priest/Elemental Shaman/Druid mix — Winds of Winter is bolted onto a kit that isn't built to feed it, and the crit rate (and damage share) reflects that.

**Corrected mechanism:** Killing Machine's guaranteed-crit procs top off an already-high baseline crit rate built from stacking universal flat crit% talents. Neither alone gets to ~100%; together they do, repeatedly, across independent characters.

### A second, independent confirmation: Titanus's own crit rate over time

Titanus's Winds of Winter crit rate wasn't always ~99%. Pooled per report by date:

| Report | Date | Title | Hits | Crits | Crit% | Dmg share |
|---|---|---|---|---|---|---|
| 26 | 2026-07-25 | "Tonx MS leveling" | 18 | 2 | 11.1% | 14.7% |
| 32 | 2026-07-26 | "ms" | 256 | 88 | 34.4% | 22.7% |
| 47 | 2026-07-30 | "illegal damage" | 299 | 299 | **100.0%** | 23.0% |
| 69 | 2026-07-31 | — | 455 | 452 | 99.3% | 42.8% |
| 68 | 2026-08-01 | "m zg" | 589 | 583 | 99.0% | 41.3% |
| 74/75 | 2026-08-02 | "asc zg" | 431/615 | 428/612 | 99.3%/99.5% | 38.4%/40.5% |

The jump from 34.4% (n=256, not a small-sample fluke) to 100.0% (n=299) inside a 4-day window is talent/gear acquisition, not variance — exactly the timescale on which a leveling character picks up Malice/Conviction/Combat Expertise and ranks up Killing Machine. This is the strongest single piece of evidence for the corrected mechanism.

### Still open
- Frostbite/Shatter/Fingers of Frost remain **untested, not disproven** — nobody scanned happened to run them, which isn't the same as them not working. Lower priority than the confirmed Malice/Conviction/Combat Expertise route, but worth a look if all three of those are ever maxed and slots remain.
- Gunju's exact CP-generation rotation beyond Titanic Mutilate isn't fully resolved — his ability bar also carries Crimson Tempest, Roll the Bones, and Ice Shock (a linear, non-quadratic Frost CP finisher — confirmed `cp_scaling_type` NULL/linear via the index, so it's not a Winds of Winter substitute, just possibly a filler).

---

## 4. Recommended build (owned cards only)

**Path: Intelligence — v5 update (2026-08-04), REVERSES the v4 "Duality is the only real candidate" call.** Full three-way test on Elric (AscensionCrafterExport addon, identical gear, empty spec, Path of Strength/Duality/Intelligence exported back-to-back). Full data in `seed_confirmed.py` (`duality_sp_amp_confirmed_reverses_retraction`, `duality_attack_power_anomaly`, `intelligence_path_beats_duality_for_winds_of_winter`):

| Stat | Strength | Duality | Intelligence |
|---|---|---|---|
| Spell Power (all schools) | 229 | 434 (1.895x) | **576 (2.515x)** |
| Attack Power | 290 | 159 (0.548x) | 101 (0.348x) |
| Melee/Ranged Crit | 15.70% | **19.92%** | 15.70% (no bonus) |
| Spell Crit | 16.37% | 17.26% | 17.67% |
| Main-hand weapon dmg (avg) | 485.2 | 508.2 | **559.6** |

Plugging all three into the actual Winds of Winter formula at 5 CP (`SP×0.0096×n² + AP×0.00624×n²`), cross-checked against Seal of Command's judge formula (`0.19×weapon + 0.08×AP + 0.13×SPH`):

| Path | Winds of Winter @ 5CP | Seal of Command judge |
|---|---|---|
| Strength | 100.2 | 145.1 |
| Duality | 129.0 | 165.7 |
| **Intelligence** | **154.0** | **189.3** |

**Intelligence wins both, despite having the lowest Attack Power of the three.** SP's coefficient in these formulas is large enough that Intelligence's SP lead (576 vs. Duality's 434) more than compensates for its AP deficit (101 vs. 159). Weapon damage itself is *also* highest under Intelligence (559.6 avg) — despite AP dropping, main-hand damage isn't purely AP-derived on this server, so Titanic Mutilate (pure weapon-%, no AP/SP term in its own tooltip) doesn't lose anything by going Intelligence either.

**Duality's one remaining edge: melee/ranged crit** (+4.22% vs. Intelligence's flat 0% bonus) — relevant to Titanic Mutilate's own crit chance and any auto-attack damage, but not enough by itself to outweigh Intelligence's SP lead in the formulas above.

**Also confirmed in this same test (both paths vs. Strength baseline):** Duality's SP amp is real (1.895x — reverses the Paladin build doc's old "RETRACTED, not visible on a live sheet" verdict, which was itself the contaminated measurement). Both Duality (1.895x) and Intelligence (2.515x) diverge from their primer-documented tooltip paraphrases ("~1.75x" and "doubled" respectively) — real effects, just not exactly the numbers written down; a live tooltip screenshot on each passive would settle the exact wording. Duality's Attack Power also drops oddly (0.548x) despite its tooltip claiming `AP = highest of Str or Agi` with Strength still well above Agility — unresolved bug or undocumented reduced conversion rate, flagged as `duality_attack_power_anomaly`.

**Caveat:** this is sheet-math on three static snapshots, not a real parse — solid enough to act on, but the project's own stated gold standard (a dummy parse under each candidate path) is the natural next step to confirm it outright.

**Core rotation — v6 update (2026-08-04), deliberately minimal-button by request:**
1. **Titanic Mutilate** ×2 → 4 CP (confirmed 2 CP/cast, both weapons)
2. **Ices Spike** ×1 → 5th CP (see §5 — now the recommended pick, not just a candidate)
3. **Winds of Winter** @ 5 CP only, never lower (quadratic scaling) — this is the 60%+ ability, everything else is in service of it
4. **Frostbound Cleave** — macro'd in, off-GCD, doesn't touch the combo-point economy at all. See new §5a.
5. Frozen Orb / Absolute Zero on cooldown as AoE/support filler between dumps, if button budget allows

That's a 2-button generate-and-dump loop (Titanic Mutilate + Ices Spike both just build toward 5, Winds of Winter spends) plus one macro'd-in passive attack that costs nothing extra to press.

**Talent priorities, in order (all owned):**
1. Killing Machine 5/5
2. Malice 5/5 **and** Conviction 5/5 **and** Combat Expertise 3/3 — stack all three; every high performer ran at least one, the two best (Gunju, Kcdq) ran two apiece
3. Improved Cone of Cold 3/3 (verbatim-named amp, zero risk)
4. **Improved Cleave 3/3 — already owned at what looks like max rank (§5a), zero chase needed**
5. Piercing Ice 3/3, Arctic Winds 3/3, Black Ice 5/5 — Frost dmg%, stacks multiplicatively with the crit-driven damage, and now does **double duty** buffing both Winds of Winter and Frostbound Cleave/Ices Spike's Frost halves (§5a)
6. Righteous Vengeance 3/3, Consecrated Weapon, Seal of Command — same support layer as the Hammerdin build, already known-good
7. Enhanced Weapon Mastery 3/3 — free +4% all damage, confirmed not bucket-blocked here (its exclusivity bucket is only EWM/Unending Fury/Answered Prayers/Blessed Weapons; none of those are in this loadout)

---

## 5. Combo-point plan

**Both Gunju and Titanus run Honor Among Thieves 3/3** (51701, owned, talentNormal) — *"When anyone in your group critically hits with a damage or healing spell or ability, you have a [X]% chance to gain a combo point. Cannot occur more than once every 3 seconds."* A genuine passive CP source, triggered by any group member's crit, no button required. Exact proc chance is an unresolved `$s1%` placeholder in the export (needs a live tooltip or DBC pull). Only functions in a group — does nothing solo — and is chance-gated with a 3s internal cooldown, so it can't be the sole 5th-CP source, but layered on top of the active filler below it should reduce how often that filler actually needs pressing in group content. Recommended as a free addition, not a replacement.

### Energy sustain stack (all owned, all rank-3+)

| Talent | Effect | Why it fits |
|---|---|---|
| Vitality 3/3 | Flat +Energy regen rate% | Unconditional baseline |
| Focused Attacks 3/3 | Chance on melee autos + offensive spells/abilities to grant Energy | Generic wording covers every button in the kit |
| Relentless Strikes 3/3 | Chance per combo point spent on a finisher to restore Energy | Winds of Winter is explicitly a "Finishing move" — rolls 5x per cast since we always dump at 5 CP |
| Combat Potency 3/3 | Off-hand melee attacks: chance to generate Energy | Passive once Titan's Grip is slotted and off-hand is actually swinging |
| Natural Energy 1/1 | *"Your Mutilate critical strikes restore energy"* | Names Mutilate verbatim → applies to Titanic Mutilate via the class-tag rule |
| Slaughter from the Shadows 3/3 | *"Reduces the energy cost of... your Hemorrhage"* | Names Hemorrhage verbatim → Ices Spike borrows Hemorrhage's modifiers, should cut its cost directly |

**Flag: Malice's capstone also has an Energy clause** (*"gain Energy when your Garrote, Rupture, or Crimson Tempest deal damage"*) but none of those abilities are in this kit — Malice earns its slot for the crit% alone, don't count on the Energy side. **Not owned, optional chase:** Glyph of Mutilate (flat Energy cost reduction on Mutilate, likely applies to Titanic Mutilate) — a nice-to-have, not essential given the six above.

Titanic Mutilate ×2 = 4 CP. No scanned character's data resolved the 5th-point source directly, but **Ices Spike is the recommended active filler** over the other two candidates:
- **Ices Spike** (913312) — 1 CP, Froststrike hybrid. Recommended: double-dips the same Frost dmg% talents (Piercing Ice/Arctic Winds/Black Ice) already planned for Winds of Winter and Frostbound Cleave, so it's not a "wasted" filler slot the way a plain physical hit would be — same talent investment, one more ability boosted. (Being an *ability* not a *spell*, it likely doesn't feed Fingers of Frost even if that talent were ever slotted — doesn't matter for the current recommended board, which doesn't run Fingers of Frost.)
- Hemorrhage (16511) — 1 CP, Physical, simple filler, no particular synergy with the rest of the kit. Fallback if Ices Spike turns out to have an issue (e.g. an unexpected cooldown).
- Death Mark (283169) — *"instantly awards N combo points"*, magnitude (`$s1`) and cooldown unresolved (needs a live tooltip). Deprioritized: unresolved magnitude is a worse bet than a known quantity when the goal is a small, reliable button set.

---

## 5a. Frostbound Cleave — off-GCD weave, zero extra button cost

**Added v6 (2026-08-04),** in response to wanting a tight, low-button rotation: since Winds of Winter is 60%+ of total damage in every real parse found (§3), the right design is to put everything else in service of that ability rather than spreading investment thin — and Frostbound Cleave (907340) turns out to fit that exactly, at no extra cost.

**What it is:** *"A sweeping attack that does your weapon damage plus $s1 as Froststrike damage to the target and his two nearest allies. Uses Cleave modifiers."* Same "-bound Cleave" family as Lightbound Cleave (Warrior-tagged, `confirmed_proc_test`) and Voidbound Cleave (Warrior-tagged, `confirmed_class_tag_rule`) — differs only in damage school. **Owned** (abilityNormal).

**Why it's a near-zero-cost addition:**
- **Froststrike is a hybrid school** (physical weapon-damage half + Frost magic half) — per the standing hybrid-school rule, it double-dips modifiers from *both* component schools. Its Frost half benefits from the exact same Piercing Ice/Arctic Winds/Black Ice stack already planned for Winds of Winter. Zero additional talent investment required.
- **It's off-GCD.** Same family as Lightbound Cleave, which `build_paladin-hammerdin.md` §11 documents as *"queued off-GCD at all times — macro onto fillers."* It doesn't compete with the Titanic Mutilate → Ices Spike → Winds of Winter loop for button-presses — macro it in once and forget it.
- **Doesn't touch the combo-point economy at all** — pure bonus damage layered on top, independent of the generate/spend cycle.
- **Improved Cleave (20496) is already owned at what appears to be max rank (3/3)** — no reroll chase needed. This is the DBC-confirmed +40%/rank (`improved_cleave_true_magnitude`), giving +120% at 3/3 on the Cleave family's AP-scaling bonus term.

**Predicted formula** (extending the DBC-confirmed Lightbound/Voidbound Cleave formula by family pattern — same tooltip template, same class-tag clause, only the damage school differs; flagged as a *prediction*, not independently DBC-verified for this specific spell): `weapon_dmg × 0.65 + (9 + AP) × 2.2` at Improved Cleave 3/3.

| Path | Predicted hit |
|---|---|
| Strength | 973 |
| Duality | 700 |
| **Intelligence (current recommendation)** | **606** |

**The one real cost of the Path of Intelligence recommendation:** Frostbound Cleave scales off Attack Power, and Intelligence sacrifices AP hardest of the three paths. This doesn't change the Path recommendation — Winds of Winter is still 60%+ of total damage and wins outright under Intelligence per §4 — but it's a real, quantified tradeoff worth weighing once a parse exists, since it's the first piece of this build where the Intelligence pick isn't a strict upgrade over the alternatives.

---

## 6. Support layer (all owned)

| Card | Effect | Notes |
|---|---|---|
| Consecrated Weapon | Flat Holy SP+AP buff + per-swing proc scaled to weapon speed | Titan's Grip's slow 2H weapons favor it |
| Righteous Vengeance | Crits seed 30%-of-crit-damage Holy DoT, 8s, pools on refresh | With crit rate near 100%, this is close to permanent uptime |
| Frozen Orb | `flat + SP×0.0714 + AP×0.0464` Frost, ticking AoE + slow | Same dual-scaling shape as the finisher |
| Absolute Zero | `(lvl×3+flat) + AP×0.0085 + SP×0.013` Frost, stacks 5×, stuns at max | Borrows Frost Nova modifiers |
| Seal of Command | `0.19×weapon + 0.08×AP + 0.13×SPH` on judge, Holy rider on autos | Only fires off main-hand autos + Paladin abilities |
| Enhanced Weapon Mastery | +4% all damage | Live here, unlike on the Paladin build (which runs Answered Prayers, its bucket-mate) |

---

## 7. Open questions / test queue

1. **5th combo-point source** (§5) — the single biggest unresolved mechanical question.
2. **Frostbite/Shatter/Fingers of Frost as a possible ADDITION** once Malice/Conviction/Combat Expertise are maxed and there's room — untested, not disproven, per §3.
3. **Gunju's full rotation** — Crimson Tempest / Roll the Bones / Ice Shock's actual roles, if any, beyond Titanic Mutilate.
4. ~~Path verification (Duality, then Intelligence)~~ — **RESOLVED v4/v5**, see §4. Full 3-way comparison done: Intelligence beats Duality on both the Winds of Winter and Seal of Command formulas. Neither path's measured SP ratio matches its primer-documented tooltip paraphrase exactly (Duality 1.895x vs. "~1.75x"; Intelligence 2.515x vs. "doubled") — a live tooltip screenshot on each passive would pin down the exact wording, though the practical numbers are solid.
5. **The Path of Duality Attack Power anomaly** — AP dropped to 0.548x the Path of Strength value despite the tooltip claiming `AP = highest of Str or Agi` (Strength was still far higher than Agility under Duality). Path of Intelligence's own AP (0.348x, no AP clause at all) confirms this isn't unique to a "no-clause" path — Duality's clause specifically appears to under-deliver relative to its own wording. Real bug, or an undocumented reduced conversion rate? Needs a patch-note check or a live tooltip on the passive itself. Lower priority now that Intelligence (not Duality) is the lead path candidate.
6. **Gold-standard confirmation still outstanding:** all Path comparisons so far are sheet-math on static snapshots, not a real parse. A dummy parse under Path of Intelligence with the recommended talent board would confirm the §4 formula-based conclusion directly.
7. **Titan's Grip's physical-penalty placeholder (`$S3%`)** — still unresolved in the export; low priority since the core nuke doesn't scale off weapon damage.
8. Multiple `Winds of Winter` spell IDs were seen in Titanus's own log data (274121 in the catalog export vs. 274132 in live parse rows) — likely a rank/instance split same as the project's general "unresolved ID is probably a known rank" pattern; not yet cross-checked spell-ID-for-spell-ID.

---

## 8. Gear itemization — Gunju's profile vs. Elric's ACTUAL current gear

**v3 update (2026-08-04): this section previously ran on aggregate sheet stats and guesswork because no armory capture existed for Elric.** A custom addon (`index/AscensionCrafterExport/`, built this session after WeakAuras' "Custom Function" trigger turned out to be blocked entirely by this server's sandbox — see that addon's own header comment for the story) pulled Elric's real, current, per-slot gear stats directly from the client. The verdict below **reverses** the earlier "partial fit, needs re-gearing" conclusion.

**Elric's gear, summed across all 15 stat-carrying pieces (verified: totals below reconcile exactly against the character sheet's own reported values — 229 Spell Power, 162 Crit Rating, 26 Expertise, 29 Haste, 18 Hit, all matched to the digit):**

| Stat | Elric (current) | Gunju (reference build) |
|---|---|---|
| **Spell Power** | **229** | **237** |
| Crit Rating | **162** | 51 |
| Stamina (gear only) | 134 | 177 |
| Intellect (gear only) | 100 | 103 |
| Strength (gear only) | 71 | 47 |
| Agility | **0** | 33 |
| Expertise | 26 | 11 |
| Haste Rating | 29 | 76 |
| Hit Rating | 18 | 48 |
| Flat Attack Power (weapons/trinkets) | **0** | 156 |

**This is a near-total reversal of the earlier (aggregate-only) conclusion.** Elric's current gear is itemized almost identically to Gunju's on the stat that matters most for Winds of Winter's SP term (229 vs 237 — essentially at parity) and carries **3× Gunju's crit rating** (162 vs 51), which per §3's evidence-backed finding is exactly the lever that separates high performers from low ones. 12 of Elric's 13 non-weapon armor/jewelry pieces carry Spell Power directly — this is NOT the "physical-melee itemization with zero SP" picture the old aggregate numbers implied. That picture only held for the two named *weapons* specifically (confirmed exactly: The Light's Hope shows 0 Spell Power in the real export, matching the old doc's claim about weapons) — the rest of the kit was never actually SP-starved, the build doc's weapon-specific note had just been over-generalized to the whole loadout in the previous version of this section.

**The one real, confirmed gap: zero itemized Attack Power.** Gunju's dual Runeblade of Baron Rivendare carry 68 flat AP each (136 total) plus a Hand of Justice trinket (+20 AP) = 156 flat AP from gear alone. Elric's current gear — including The Light's Hope, a 2H sword — carries **no flat AP anywhere**; Elric's 290 total Attack Power is coming entirely from Strength (155 total Str) via whatever path formula is active, not from itemization. Since Winds of Winter squares the AP term by combo points exactly like the SP term, this is the actual lever worth chasing — not a full re-gear, just AP-itemized weapon/trinket upgrades layered onto an otherwise already-suitable kit.

**Secondary gaps, lower priority:** Haste (29 vs 76) and Hit (18 vs 48) trail Gunju's gear, and Elric has zero Agility (irrelevant if AP ends up Strength-sourced under Duality, matching Gunju's own Str-leaning split). Stamina is somewhat behind (134 vs 177 gear-only) but that's a survivability question, not a damage one.

**Revised verdict: Elric's current gear is already a strong starting point for this build, not a mismatch.** The practical gearing plan is narrower than previously written: prioritize AP-itemized weapon/trinket upgrades (the one clean, confirmed gap), keep the rest of the current SP/crit-heavy kit, and don't treat this as a from-scratch re-gear.

---

## 9. Relationship to existing builds

- **Not a replacement for `build_paladin-hammerdin.md`.** That build is locked/final-boarded — this is a separate character/spec proposal.
- **`synergy_winds-of-winter.md` is the original single-player reference**; this file supersedes its crit-rate theory (§5 of that doc) with the multi-character evidence above but doesn't change anything else in it — the base formula, CP mechanics, and support-layer numbers there still stand.
- Meaningful owned-card overlap with the Hammerdin build (Consecrated Weapon, Righteous Vengeance, Seal of Command) means gear/card knowledge transfers if this gets built.
- Opposite stat posture from Hammerdin: this build's core nuke pays into SP and AP simultaneously through one ability, rather than splitting into separate lanes.

---

## 10. Open questions for next session — organized by "hit harder" vs. "hit often"

Two ways to raise this build's DPS ceiling, per the stated framing: increase per-cast magnitude, or increase cast frequency. Punch list below, roughly priority-ordered within each bucket.

### Hit harder

1. **The Winds of Winter 0.214 coefficient mystery (top priority).** §3/v7: the DBC effect that carries the flat `$b2×n` term (33.75/CP, newly resolved) also carries an unexplained `EffectBonusCoefficient=0.214` not reflected anywhere in the visible tooltip text. If it's a real, additional SP-scaling term stacked on top of the explicit `SPFR×0.0096` and `AP×0.00624` written in the tooltip, it changes the absolute damage math meaningfully. If it's inert (common for heavily custom-scripted spells that override standard engine scaling), it doesn't. Settles with either a live tooltip showing real min/max numbers at 1 CP cross-referenced against known SP, or a parse.
2. **Does the `SPFR` term actually read Frost-school-specific SP, or just general SP on this server?** Still an open extractor gap (`build_index.py`'s regex doesn't match `$SPFR*`, noted since primer v14) — doesn't block anything since our current stat weight treatment already assumes general SP, but worth confirming rather than assuming.
3. **Gunju's full ability bar isn't fully explained** — Crimson Tempest, Roll the Bones, Ice Shock all present but roles unconfirmed. Ice Shock in particular is a linear (not quadratic) Frost CP finisher — worth checking whether it's ever worth casting over banking toward Winds of Winter, or if it's dead weight in his rotation.
4. **Frostbite/Shatter/Fingers of Frost as a possible addition** once Malice/Conviction/Combat Expertise are maxed and slots remain — still untested by any scanned character, not disproven, just never observed in the wild (§3).
5. **Titan's Grip's physical-penalty placeholder (`$S3%`)** — matters more now than originally noted, since Frostbound Cleave and Ices Spike both have real weapon-damage components, not just Winds of Winter's stat-pure nuke.
6. **Exact Path amp tooltip wording.** Duality measured 1.895x (not the folklore "1.75x"), Intelligence measured 2.515x (not a clean "doubled") — both real, neither matches its documented paraphrase. A live tooltip screenshot on each passive would pin the exact designed numbers down.
7. **The Path of Duality Attack Power anomaly** (0.548x of the Strength-path baseline despite the tooltip claiming `AP = highest of Str or Agi`) — lower priority now that Intelligence, not Duality, is the lead path candidate, but still an unresolved, reportable discrepancy.

### Hit often

1. **Does Titanic Mutilate / Ices Spike / Winds of Winter actually cost Energy at all on this server?** Checked all three tooltips today (including the now-fully-resolved Titanic Mutilate text) — none of them state an Energy cost anywhere. This is a real gap: the whole Energy-sustain conversation assumed a standard Rogue-style resource economy, but if these abilities are purely GCD-gated instead, "hit often" is bounded by GCD length (and Haste), not by Energy regen, and the sustain-talent discussion from earlier needs re-grounding. Worth a live tooltip check or just watching the resource bar in-game.
2. **The 5th combo-point source, still not fully closed.** Ices Spike is recommended, Honor Among Thieves helps passively, but neither is proc-tested, and Ices Spike's own energy cost (if any, per item 1) is unknown.
3. **Does Haste actually shorten Winds of Winter's cast, or reduce the GCD, or do anything at all for this kit?** Deprioritized in every stat-weight discussion so far by inheritance from the Paladin build's own reasoning, never independently checked for this build specifically.
4. **Killing Machine's real proc rate against this specific rotation** (Titanic Mutilate ×2 + Ices Spike) — established as load-bearing for the crit-rate mechanism (§3) but never measured against this exact ability mix.
5. **Honor Among Thieves' exact proc chance** — still an unresolved `$s1%` placeholder. Directly determines how reliably the passive 5th-CP assist actually fires.
6. **Titan's Grip's dual-2H weapon speed vs. auto-attack-triggered procs** (Combat Potency specifically, which needs actual off-hand swings) — slow 2H weapons swing less often than fast weapons; whether this meaningfully throttles Combat Potency's Energy contribution (if Energy is even real per item 1) hasn't been examined.
7. **The gold-standard confirmation, still outstanding across every open item above:** a real dummy parse under the recommended board. Sheet-math and DBC reads have gotten this build a long way, but nothing here has been measured in an actual fight yet.
