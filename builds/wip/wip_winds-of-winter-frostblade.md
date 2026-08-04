# Winds of Winter — Frostblade (WIP v10)

## Status
WIP — theorycraft only, no talent board committed, no character built. **This is the build Elric is actively being rerolled toward.**

**v10 update (2026-08-04, session continued):** Two follow-ups per user request, plus a consolidation. (1) Checked whether any scouted Winds of Winter player actually combines a Frost Fever source with Tundra Stalker (the "Package 2" synergy from `synergy_portable-multiplier-packages.md`) — **nobody has**: Gunju runs the source (Glacial Spike) without the amplifier, Kcdq runs the amplifier (Tundra Stalker 5/5) with no source at all (likely dead on his own board). Real, tooltip-grounded mechanic, not an observed pattern — downgraded accordingly. (2) Checked Seal Fate's adoption: only 1/5 scouted characters run it (Blasted, 1/3) — weak evidence, not a validated pick. (3) **New §11 below consolidates every talent/ability surfaced across this whole investigation into one master candidate pool**, tiered Core (never swap) / Strong-Flexible (owned, likely include) / Conditional-Tradeoff (real but costs something or thin evidence) — for sim-based refinement once a core is set, per the user's request. All prior scattered mentions across §4/§5/§6/§10 still stand; §11 is the consolidated reference going forward.

**v9 update (2026-08-04, session continued):** User supplied the authoritative live source for this build's core ability: [db.ascension.gg's spell browser](https://db.ascension.gg/?spell=274132), confirming **274132, not 274121, is the Winds of Winter actually cast on Darkmoon.** This closes §7 item 8 (the multi-spell-ID question flagged in v2/v7) — and it's a much bigger deal than a rank/instance split. Cross-referenced the whole ability stack (Titanic Mutilate, Ices Spike, Frostbound Cleave, and both Winds of Winter IDs) on the same site.

- 🔴 **Winds of Winter has its OWN 5-second cooldown, independent of the GCD and independent of combo points.** This was not knowable from any source used so far (not in the local DBC cache, not on Gunju's per-rank tooltip capture) — db.ascension.gg is the only source that's surfaced it. **This fundamentally changes the rotation model.** The build was previously framed as "generate to 5 CP, dump, repeat" with the assumption that cast frequency was bounded only by CP generation speed. It's actually bounded by whichever is slower: CP generation, or this flat 5s gate. See §4 and §10 "hit often" for the reworked framing.
- 🔴 **Winds of Winter costs Mana — "25% of base mana" per cast — not Energy.** Resolves §10 "hit often" item 1 outright, but not the way that item assumed: it's not that these abilities are pure-GCD/no-resource, it's that **the kit runs on three separate resource pools at once**, one per class the ability borrows modifiers from (a new, previously-unrecognized instance of the class-tag rule extending to resource type, not just damage modifiers):

  | Ability | Resource cost | Borrows from | Resource matches the borrowed class |
  |---|---|---|---|
  | Titanic Mutilate | 50 Energy | Mutilate (Rogue) | ✅ Energy |
  | Ices Spike | 35 Energy | Hemorrhage (Rogue) | ✅ Energy |
  | Winds of Winter | 25% of base Mana, **5s cooldown** | Cone of Cold (Mage) | ✅ Mana |
  | Frostbound Cleave | 20 Rage | Cleave (Warrior) | ✅ Rage |

  **Consequence: the existing §5 "Energy sustain stack" (Vitality/Focused Attacks/Relentless Strikes/Combat Potency/Natural Energy/Slaughter from the Shadows) is still correct and still needed** — it covers Titanic Mutilate + Ices Spike, the two Energy-costed CP generators — **but it does nothing for Winds of Winter's Mana cost or Frostbound Cleave's Rage cost.** Neither of those has ANY sustain plan yet. Given the finisher is 60%+ of total damage, Mana sustain for it specifically is now a real, previously-invisible gap — see new §10 item.
- ✅ **Cross-validation of last session's DBC reads: Ices Spike (65% weapon dmg) and Frostbound Cleave (9 flat / 65% weapon dmg) both match db.ascension.gg exactly**, digit for digit. Good news for the DBC-reading methodology in general — the Titanic Mutilate 115%→70% miss last session was a hardcoded-stale-text trap specific to that one field, not a sign the whole approach is unreliable.
- ⚠ **The Winds of Winter base damage roll is 32-97 on 274132, not 2-23** (2-23 was 274121's range, confirmed correct for that ID but apparently the wrong ID for Darkmoon). **This means the `EffectPointsPerCombo=33.75` flat-per-CP term and the unexplained `EffectBonusCoefficient=0.214`, both read from 274121's DBC data last session, are UNCONFIRMED for the actual live spell (274132) and should not be assumed to carry over.** 274132 isn't in the locally cached `dbc-extract.json` at all (checked — only 274118 and 274121 exist there), so there's no local way to re-derive its real per-CP/SP/AP coefficients right now. Given the base roll is roughly 14-16x larger on 274132 than on 274121, it's plausible the other terms scale similarly, but that's a guess, not a read — do not use it for damage math. Needs either a fresh DBC pull that actually includes 274132, or a live in-game tooltip.
- db.ascension.gg's "Spell Scaling and PvP Mods may not always be accurate or present" disclaimer is worth remembering — it did NOT show the `$b2`/`$SPFR`/`$AP` scaling terms for Winds of Winter at all (same gap as Gunju's per-rank capture), only the flat School Damage base roll, cooldown, and resource cost. Good for mechanics (cooldown/cost/resource type), not sufficient alone for the scaling formula.

**Practical rotation impact, pending real regen numbers (§10):** 2× Titanic Mutilate (100 Energy) + 1× Ices Spike (35 Energy) = 135 Energy to reach 5 CP, against Winds of Winter's hard 5s gate. Whether Energy regen or the 5s cooldown is the actual binding constraint on cast frequency is now the single biggest open "hit often" question — previously the framing didn't even know the cooldown existed.

**v8 update (2026-08-04, session continued):** Follow-up DBC dig, still no live client needed — cross-validated against Gunju's own scouted live-tooltip capture (`index/scouted/scouted_Gunju_2026-08-03.json`), which caught a real methodology error.

- ❌ **RETRACTION: Titanic Mutilate is NOT 115% weapon damage.** v7 read that number off spell 271781's hardcoded description *string* — but that string is stale flavor text, not the field the game engine actually substitutes into 271779's `$271781s2%` template. The template pulls `EffectBasePoints[1]` (the numeric field), which is **69 → 70 under the project's standard "+1" convention** — and Gunju's own live-resolved tooltip capture confirms it directly: *"Instantly attacks with both weapons for 70% weapon damage."* Checked the off-hand trigger (271782) too — its `EffectBasePoints[1]` is also 69→70, so this reads as a clean **70%/70% split, both hands**, not the asymmetric 115%/70% v7 implied. Same "check the field the engine actually uses, not the nearest-looking text" discipline as every other correction in this doc's history (Improved Cleave's true magnitude, the Frostbound/Lightbound Cleave `+1` convention) — this is that exact trap, just caught this time instead of missed. **Practical impact: low** — Titanic Mutilate's magnitude was never load-bearing for the DPS-share estimates (Winds of Winter dominates at 60%+), but any future "how much does Titanic Mutilate itself hit for" question should use 70%, not 115%.
- ✅ **Ices Spike's weapon% resolved: 65% base**, `EffectBasePoints[1]` = 64→65 on its own effect slot (a proper `$s2%` template reference, not a stale hardcoded string — same field type that correctly resolved Improved Cleave and the Cleave family, no reason to distrust it here). Per its own tooltip's dagger/two-hander multipliers, **under Titan's Grip (counts as two-hander) that's 65% × 0.85 = 55.25% weapon damage as Froststrike** — the actual number for this build's gear, not the generic 65%.
- ✅ **Titan's Grip's `$S3%` placeholder is now DBC-confirmed: exactly −10%** (`EffectBasePoints[2]` = -11→-10 on spell 46917's third effect slot). Closes §10 "hit harder" item 5 below. This matches the figure `build_paladin-hammerdin.md` already carries from a live tooltip on a different character — same number, second independent method, no surprise, but it's now confirmed from this build's own source data rather than borrowed from the Paladin doc.
- **Frostbound Cleave's DBC-confirmed status (claimed in v7) is real** — re-verified this session: its `effect_json` is byte-identical to Lightbound Cleave (907300) and Voidbound Cleave (907280), field for field. §5a's text calling this a "prediction, not independently DBC-verified" was stale from before that check landed; corrected below.
- **Methodology note, not a resolution:** Gunju's scouted Winds of Winter capture shows the *same* "2-23 damage" range at all 5 combo-point levels — i.e., the site's per-rank tooltip preview doesn't appear to evaluate the custom `$b2*n` / `$SPFR*n*n` / `$AP*n*n` terms at all, only the standard `$m2`/`$M2` fields. This means Gunju's capture can't be used to cross-check the 33.75/CP or 0.214-coefficient findings one way or the other — it's silent on them, not contradicting them. Worth knowing before treating an ascensionlogs.gg per-rank tooltip as authoritative for any custom-scripted formula term.

Full detail (including the corrected Titanic Mutilate figure) added to `seed_confirmed.py` this session. See updated §5, §5a, and §10 below.

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
| Winds of Winter (274121 catalog/card ID; **274132 is the live Darkmoon spell ID**, v9) | core finisher, quadratic CP scaling, 5s own cooldown + 25% base Mana cost (v9) | abilityNormal + abilityGolden |
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

**⚠ v9: the coefficients above (`b2`≈33.75, plus an unexplained 0.214 term) were read from spell 274121's DBC data. The user has confirmed 274132, not 274121, is the ID actually cast on Darkmoon — its base damage roll (32-97) is ~14-16x larger than 274121's (2-23), and its `b2`/SP/AP coefficients are unconfirmed pending a fresh DBC pull or live tooltip.** The *shape* of the formula (flat term + quadratic SP + quadratic AP, both scaling by n²) is still trusted — that's a structural fact about the spell template, not a magnitude — but do not use the specific 33.75/0.0096/0.00624 numbers for damage math until 274132 is independently confirmed. **Also new in v9: Winds of Winter has its own 5-second cooldown and costs 25% of base Mana per cast** (not previously known) — see the v9 changelog above and §4/§10.

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

**Core rotation — v6 framing (2026-08-04), REVISED v9 for Winds of Winter's own 5s cooldown:**
1. **Titanic Mutilate** ×2 → 4 CP, 100 Energy (confirmed 2 CP/cast, both weapons)
2. **Ices Spike** ×1 → 5th CP, 35 Energy (see §5 — recommended pick)
3. **Winds of Winter** @ 5 CP, **only when its own 5s cooldown is also up** — this is the 60%+ ability, everything else is in service of it, but it's now a two-condition gate (CP=5 AND cooldown ready), not just a CP threshold
4. **Frostbound Cleave** — macro'd in, off-GCD, 20 Rage, doesn't touch the combo-point economy at all. See new §5a.
5. Frozen Orb / Absolute Zero on cooldown as AoE/support filler between dumps, if button budget allows

**v9 change: this is no longer cleanly a "2-button generate-and-dump loop."** With Winds of Winter capped to once per 5s regardless of CP, the practical rotation now depends on which is slower — building 135 Energy worth of CP generators, or waiting out the 5s gate. If Energy regen comfortably outpaces 5s, there will be idle GCD windows between reaching 5 CP and the cooldown coming back up — in which case Frostbound Cleave (off-GCD already) and Frozen Orb/Absolute Zero stop being "filler if button budget allows" and start being genuinely necessary to not waste GCDs. If Energy regen is the slower of the two, the 5s cooldown never actually matters and the original framing holds. **Which case this actually is depends on real Energy regen numbers, not yet gathered — top "hit often" open item, §10.**

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

### Energy sustain stack (all owned, all rank-3+) — ⚠ v9: only covers HALF the kit's resource needs

**v9 confirms this section's premise is correct but incomplete.** Titanic Mutilate (50 Energy) and Ices Spike (35 Energy) are both genuinely Energy-costed, confirmed via db.ascension.gg — this stack is real and needed. **But Winds of Winter costs 25% of base Mana per cast (not Energy) and Frostbound Cleave costs 20 Rage (not Energy)** — neither has any sustain plan below or anywhere else in this doc. At a hard cap of one Winds of Winter cast per 5s, 25% base mana per cast implies the character would burn through its entire base Mana pool in ~20 seconds of uninterrupted casting with zero regen — a real, unaddressed gap given the ability is 60%+ of total damage. Frostbound Cleave's Rage, being off-GCD/no-cooldown, is bounded only by however fast Rage generates for a non-Warrior-resource character (likely melee-swing-driven, unverified) — it may end up firing far less often than "macro it and forget it" implies if Rage trickles in slowly. Both are new, unscoped open items — see §10.

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
- **Ices Spike** (913312) — 1 CP, Froststrike hybrid, **35 Energy, no cooldown (v9, db.ascension.gg-confirmed)**. Recommended: double-dips the same Frost dmg% talents (Piercing Ice/Arctic Winds/Black Ice) already planned for Winds of Winter and Frostbound Cleave, so it's not a "wasted" filler slot the way a plain physical hit would be — same talent investment, one more ability boosted. **Weapon% resolved (v8, cross-confirmed v9): 65% base, ×0.85 under a two-hander (Titan's Grip counts) = 55.25% weapon damage as Froststrike** — matches db.ascension.gg exactly. (Being an *ability* not a *spell*, it likely doesn't feed Fingers of Frost even if that talent were ever slotted — doesn't matter for the current recommended board, which doesn't run Fingers of Frost.)
- Hemorrhage (16511) — 1 CP, Physical, simple filler, no particular synergy with the rest of the kit. Fallback if Ices Spike turns out to have an issue (e.g. an unexpected cooldown).
- Death Mark (283169) — *"instantly awards N combo points"*, magnitude (`$s1`) and cooldown unresolved (needs a live tooltip). Deprioritized: unresolved magnitude is a worse bet than a known quantity when the goal is a small, reliable button set.

---

## 5a. Frostbound Cleave — off-GCD weave, zero extra button cost

**Added v6 (2026-08-04),** in response to wanting a tight, low-button rotation: since Winds of Winter is 60%+ of total damage in every real parse found (§3), the right design is to put everything else in service of that ability rather than spreading investment thin — and Frostbound Cleave (907340) turns out to fit that exactly, at no extra cost.

**What it is:** *"A sweeping attack that does your weapon damage plus $s1 as Froststrike damage to the target and his two nearest allies. Uses Cleave modifiers."* Same "-bound Cleave" family as Lightbound Cleave (Warrior-tagged, `confirmed_proc_test`) and Voidbound Cleave (Warrior-tagged, `confirmed_class_tag_rule`) — differs only in damage school. **Owned** (abilityNormal). **Costs 20 Rage, no cooldown, 0 GCD (v9, db.ascension.gg-confirmed)** — the Rage cost is new information; matches the Warrior tag (Cleave modifiers) exactly like Titanic Mutilate/Ices Spike's Energy cost matches their Rogue tags. Rage generation for a character not built around a Warrior resource loop is unverified — see §10.

**Why it's a near-zero-cost addition:**
- **Froststrike is a hybrid school** (physical weapon-damage half + Frost magic half) — per the standing hybrid-school rule, it double-dips modifiers from *both* component schools. Its Frost half benefits from the exact same Piercing Ice/Arctic Winds/Black Ice stack already planned for Winds of Winter. Zero additional talent investment required.
- **It's off-GCD.** Same family as Lightbound Cleave, which `build_paladin-hammerdin.md` §11 documents as *"queued off-GCD at all times — macro onto fillers."* It doesn't compete with the Titanic Mutilate → Ices Spike → Winds of Winter loop for button-presses — macro it in once and forget it.
- **Doesn't touch the combo-point economy at all** — pure bonus damage layered on top, independent of the generate/spend cycle.
- **Improved Cleave (20496) is already owned at what appears to be max rank (3/3)** — no reroll chase needed. This is the DBC-confirmed +40%/rank (`improved_cleave_true_magnitude`), giving +120% at 3/3 on the Cleave family's AP-scaling bonus term.

**Formula (v8: DBC-confirmed directly, not just extended by family pattern)** — Frostbound Cleave's own `effect_json` (spell 907340) is byte-identical to Lightbound Cleave (907300) and Voidbound Cleave (907280), field for field: `weapon_dmg × 0.65 + (9 + AP) × 2.2` at Improved Cleave 3/3.

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
8. ~~Multiple `Winds of Winter` spell IDs were seen in Titanus's own log data (274121 in the catalog export vs. 274132 in live parse rows)~~ — **RESOLVED v9**: user-confirmed, 274132 is the live Darkmoon spell ID. Not a simple rank/instance split as guessed — 274132's base damage roll (32-97) is far larger than 274121's (2-23), and its actual `b2`/SP/AP coefficients are now a fresh open question (§1, §10) since the local DBC cache never had 274132 to begin with.

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

1. **What are 274132's real b2/SP/AP coefficients (top priority, superseded from the old "0.214 mystery" item).** v9: confirmed 274132, not 274121, is the live Darkmoon spell — its base damage roll (32-97) is far larger than 274121's (2-23), and 274132 isn't in the local `dbc-extract.json` cache at all, so none of last session's coefficient reads (`b2`=33.75/CP, the unexplained 0.214 term, or even whether the 0.0096/0.00624 SP/AP multipliers themselves carry over) can be assumed correct for the actual spell. This supersedes rather than just extends the old mystery — the question is no longer "what does one extra term on 274121 mean," it's "what is 274132's whole formula." Needs either a DBC pull that includes 274132 specifically, or a live in-game tooltip showing real computed min/max damage at a known CP count and known SP/AP. Gunju's live capture and db.ascension.gg's own page both stop short of showing this (neither evaluates the custom scaling terms, both show only the flat base roll).
2. **Does the `SPFR` term actually read Frost-school-specific SP, or just general SP on this server?** Still an open extractor gap (`build_index.py`'s regex doesn't match `$SPFR*`, noted since primer v14) — doesn't block anything since our current stat weight treatment already assumes general SP, but worth confirming rather than assuming.
3. **Gunju's full ability bar isn't fully explained** — Crimson Tempest, Roll the Bones, Ice Shock all present but roles unconfirmed. Ice Shock in particular is a linear (not quadratic) Frost CP finisher — worth checking whether it's ever worth casting over banking toward Winds of Winter, or if it's dead weight in his rotation.
4. **Frostbite/Shatter/Fingers of Frost as a possible addition** once Malice/Conviction/Combat Expertise are maxed and slots remain — still untested by any scanned character, not disproven, just never observed in the wild (§3).
5. ~~**Titan's Grip's physical-penalty placeholder (`$S3%`)**~~ — **RESOLVED v8**, DBC-confirmed exactly −10% (`EffectBasePoints[2]` = -11→-10 on spell 46917). Matters more than originally noted, now that it's a real number: Frostbound Cleave and Ices Spike both have real weapon-damage components, not just Winds of Winter's stat-pure nuke, so this tax applies to a larger share of the kit than it did on the Paladin build.
6. **Exact Path amp tooltip wording.** Duality measured 1.895x (not the folklore "1.75x"), Intelligence measured 2.515x (not a clean "doubled") — both real, neither matches its documented paraphrase. A live tooltip screenshot on each passive would pin the exact designed numbers down.
7. **The Path of Duality Attack Power anomaly** (0.548x of the Strength-path baseline despite the tooltip claiming `AP = highest of Str or Agi`) — lower priority now that Intelligence, not Duality, is the lead path candidate, but still an unresolved, reportable discrepancy.

### Tracked for later — portable packages found via scouting, not yet applied to the core board

Per the user's 2026-08-04 request to check the Demon Package (`synergy_portable-multiplier-packages.md`) against Winds of Winter performers and look for Shadow/Frost synergy. Checked the 5 locally-scouted characters with saved JSON (Gunju, Titanus, Kcdq, Blasted, Tdoctor) rather than re-hitting the live API. Held here rather than folded into §4's recommended board, per the user's "pivot — tally for once we've set a core" framing.

- **Demon Package is NOT the Winds-of-Winter discriminator.** 4/4 high performers checked run at least one member (Titanus: Demonic Pact 5/5 + Demonic Tactics 5/5; Blasted: Master Demonologist 5/5 + Demonic Pact 5/5 + Demonic Knowledge 3/3, the deepest investment seen; Kcdq: Demonic Tactics 5/5; Gunju: Master Demonologist 3/5 + Demonic Tactics 3/5, partial) — **but so does the one low performer checked, Tdoctor (Demonic Tactics 5/5).** Consistent with `synergy_portable-multiplier-packages.md`'s own framing: it's a broadly-popular pick across classless "Hero" builds generally, not something specific to this engine. The actual discriminator remains Malice/Conviction/Combat Expertise + Killing Machine (§3), unchanged by this check.
- **Still worth adding, though — two of the four package members are pure free upside.** Pulled full tooltip text: **Demonic Tactics** ("Increases critical strike chance for **you**, your tamed pet, and your Wild Imps") and **Demonic Pact** ("Increases **your** spell damage done by X%") both have self-buff clauses that are *unconditional* — no pet required at all. At 5/5 each that's +10% crit (any table) and +10% flat spell damage, zero rotation/pet-management cost. **Elric already owns both at 5/5** (Cards.txt: Demonic Tactics 30248, Demonic Pact 47240) — zero reroll chase. The other two, Master Demonologist and Demonic Knowledge, are fully pet-conditional ("as long as that demon is active" / "your active demon's Stamina plus Intellect") and would require committing to real Felguard/Enslaved-demon upkeep — a bigger design decision, also already owned at/near max rank (23825 5/5, 35693 3/3) if it's ever wanted.
- **No Shadow synergy found or worth chasing.** None of the 4 high performers run any Shadow-specific damage talent. The contrast case (Tdoctor, the low performer) is the one saturated with Shadow talents (Shadow Power, Misery, Twisted Faith, Shadow Embrace, etc.) — none of which touch Frost at all, reinforcing the existing §3 read that his board is a mismatched, non-synergistic pile rather than a competing theory worth testing.
- 🔴 **Real Frost lead found, high-value: Ice Floes may reduce Winds of Winter's own cooldown.** Ice Floes (owned, 3/3, id 55094) reads *"Reduces the cooldown of your Frost Nova, Cone of Cold, Ice Block and Icy Veins spells by 33%"* — names **Cone of Cold verbatim**, satisfying the same "named beats generic, no proc-test needed" rule already used for Improved Cone of Cold's damage amp. Since Winds of Winter is class-tag-confirmed to borrow Cone of Cold modifiers, this could cut the newly-discovered 5s cooldown (v9 above) down to ~3.35s — directly bearing on the still-open "does Energy or the cooldown bind cast frequency" question. **Not proc-tested, same confidence tier as any borrowed-modifier prediction** — but if it holds, it's probably the single best lever on the entire "hit often" side of the ledger, and it's free (already owned, all 3 high-performers checked run it at 3/3).
- **One more untracked Frost dmg% amplifier: Concussion** (owned 5/5, id 16108) — *"Increases your Frost, Fire, and Nature damage done by 5%"*, flat, no conditions. Currently not in §4's Frost-dmg% list (which only has Piercing Ice/Arctic Winds/Black Ice/Improved Cone of Cold) — a free 5th one.
- Two more seen but likely dead as-is: **Tundra Stalker** (conditional on a Frost Fever debuff this kit has no source for) and **Elemental Weapons** (buffs specific weapon *imbues* — Windfury/Flametongue/Frostbrand/Earthliving — none currently planned; weapon-imbue-exclusivity rule applies if one ever is).

**If/when we set the core:** Demonic Tactics 5/5, Demonic Pact 5/5, Concussion 5/5, and Ice Floes 3/3 are all already-owned, zero-chase, no-downside additions — the main open decision is whether to also commit to Felguard/Enslaved-demon pet upkeep for Master Demonologist + Demonic Knowledge, which is a real rotation/complexity tradeoff, not a free pickup.

**Follow-up scan (2026-08-04, same session): checked all 5 characters for every OTHER Frost/Cold talent, and specifically anything else naming Cone of Cold verbatim.** Found five more, all owned:

- 🔴 **Glacial Spike (284177, owned, abilityNormal 1/1) — a whole new ability candidate, not previously known to this build.** Real tooltip: `${$m1+($SP*0.129)+($AP*0.0838)}` Frost damage, slows enemies, and **applies Frost Fever** — "uses Cone of Cold modifiers," same borrowed-class family as Winds of Winter. Two things stack on top of each other here: it's a genuine linear SP+AP Frost nuke in its own right (benefits from Improved Cone of Cold and Spell Impact below the same way Winds of Winter does), **and it's the missing enabler for Tundra Stalker** — Tundra Stalker's "+15% damage to Frost Fever targets" clause is worded globally ("your spells and abilities"), not restricted to the Cone of Cold family, so keeping Frost Fever up via Glacial Spike would buff Winds of Winter, Ices Spike, Frostbound Cleave, *and* Titanic Mutilate all at once. Tundra Stalker (owned 5/5) was flagged dead last message specifically because nothing in the kit applied Frost Fever — this closes that gap, at the cost of one more button, which cuts against the stated minimal-button goal. **v10 downgrade: this is `synergy_portable-multiplier-packages.md`'s pre-existing "Package 2" synergy, and checking all 5 scouted Winds of Winter characters shows NOBODY has actually assembled it** — Gunju runs Glacial Spike without Tundra Stalker, Kcdq runs Tundra Stalker with no Frost Fever source at all (likely dead on his own board, same failure mode this would have hit us without Glacial Spike). Real, tooltip-grounded mechanic — not an observed pattern. Treat as an unproven prediction, same tier as any other class-tag inference, not a validated "top players do this" pick.
- ✅ **Spell Impact (12469, owned 3/3) verbatim-names Cone of Cold**: *"Increases the damage of your Arcane Explosion, [...], Ice Lance and Cone of Cold spells by X%."* Gunju runs it at 2/3 for a resolved 6% — implies 3%/rank, so Elric's already-owned 3/3 = **9%**. Same confidence tier as Improved Cone of Cold's existing 45% (named-list rule, no proc-test needed). Free damage amp, not yet tracked.
- 🔴 **Elemental Focus (16164, owned 1/1) — the strongest Mana-sustain lead found for the newly-discovered 25% base Mana cost.** *"After landing a critical strike with a Fire, Frost, or Nature spell or ability, chance to enter Clearcasting — reduces the resource cost of your next [N] Magic spells/abilities by [X]%."* Given these same characters' ~99-100% Frost crit rates, this would fire close to every cast if it triggers off Frost crits (it does — Frost is explicitly listed). Exact proc chance and reduction magnitude are still templated/unresolved even in the live capture — directionally excellent, not yet quantified.
- **Seal Fate (14193, owned 3/3)** — not actually a Frost talent (matched on its capstone mentioning "Cold Blood," a Rogue ability name, not Frost damage) but relevant anyway: *"Your critical strikes from Rogue abilities that add combo points have a chance to add an additional combo point."* Titanic Mutilate is Rogue-tagged and adds combo points — this could be a real lead on the still-open 5th-combo-point-source question (§5/§10). **v10: adoption checked, weak — only 1/5 scouted characters (Blasted) runs it, and only at 1/3.** Not a validated pattern like Ice Floes/Improved Cone of Cold (3-4/5+). Mechanically sound, thin evidence.
- **Arctic Reach (16758, owned 2/2)** — verbatim-names Cone of Cold but is range/radius only, not damage (*"increases the radius of your Frost Nova and Cone of Cold spells by 20%"*). Useful for AoE/trash cone width, not single-target damage. Carries an unchecked "does not stack with other similar effects" exclusivity clause.

**Updated free-and-owned tally:** Demonic Tactics 5/5, Demonic Pact 5/5, Concussion 5/5, Ice Floes 3/3, Spell Impact 3/3 — five zero-chase, no-downside adds. Elemental Focus 1/1 is a strong Mana-sustain candidate pending exact numbers. Glacial Spike is the one real button/complexity decision in the pile (new ability, but unlocks Tundra Stalker for the whole kit). Seal Fate is a lead on the CP-source question, unrelated to Frost itself.

### Hit often

1. ~~Does Titanic Mutilate / Ices Spike / Winds of Winter actually cost Energy at all on this server?~~ — **RESOLVED v9**, and more interesting than the item assumed: **all three run on different resource pools.** Titanic Mutilate 50 Energy, Ices Spike 35 Energy, Winds of Winter 25% base Mana (plus its own 5s cooldown), Frostbound Cleave 20 Rage — confirmed via db.ascension.gg. See the v9 changelog table above. Replaced by two new, sharper items below.
2. **🔴 NEW (v9, top priority): does Energy regen or Winds of Winter's 5s cooldown actually bind cast frequency?** 2×Titanic Mutilate + 1×Ices Spike = 135 Energy per 5-CP cycle. If baseline (or talent-boosted) Energy regen comfortably produces 135 Energy inside 5 seconds, the cooldown is irrelevant and the original "spam to 5 CP" framing holds. If it's slower, Energy is the real bottleneck and the cooldown never binds. Either way this determines whether Frostbound Cleave/Frozen Orb/Absolute Zero need to fill real idle GCD gaps (§4) — currently unknown, needs either known Energy regen rate + Energy-talent math, or a parse.
3. **🔴 NEW (v9): Winds of Winter has no Mana sustain plan at all.** 25% of base Mana per cast, uncapped by anything in the current recommended board (the Energy-sustain stack in §5 doesn't touch Mana). At the 5s cast cap this could exhaust base Mana in as little as ~20s of continuous casting with zero regen accounted for. Needs either a Mana-return talent search (parallel to the existing Energy-sustain stack — likely in the Mage/Intelligence-Path space given the ability's Cone of Cold heritage) or confirmation that base regen/Spirit alone is sufficient at this build's Int/Spirit levels.
4. **NEW (v9): does Frostbound Cleave's Rage actually generate fast enough to matter?** It's off-GCD/no-cooldown, so in principle free — but 20 Rage per cast on a character not built around a Warrior Rage-generation loop (no stated Rage-gen talents in the current board) might trickle in far slower than "macro it and forget it" implies. Unverified either way; would need in-game observation of the Rage bar.
5. **The 5th combo-point source, still not fully closed.** Ices Spike is recommended (now confirmed 35 Energy, no cooldown), Honor Among Thieves helps passively, but neither is proc-tested.
6. **Does Haste actually shorten Winds of Winter's cast, or reduce the GCD, or interact with its 5s cooldown at all?** Deprioritized in every stat-weight discussion so far by inheritance from the Paladin build's own reasoning, never independently checked for this build specifically — now sharper given the newly-discovered fixed cooldown (a 5s cooldown is a very different target for Haste to shrink than "GCD length" was).
7. **Killing Machine's real proc rate against this specific rotation** (Titanic Mutilate ×2 + Ices Spike) — established as load-bearing for the crit-rate mechanism (§3) but never measured against this exact ability mix.
8. **Honor Among Thieves' exact proc chance** — still an unresolved `$s1%` placeholder. Directly determines how reliably the passive 5th-CP assist actually fires.
9. **Titan's Grip's dual-2H weapon speed vs. auto-attack-triggered procs** (Combat Potency specifically, which needs actual off-hand swings) — slow 2H weapons swing less often than fast weapons; whether this meaningfully throttles Combat Potency's Energy contribution has been examined.
10. **The gold-standard confirmation, still outstanding across every open item above:** a real dummy parse under the recommended board. Sheet-math, DBC reads, and now a live spell-browser cross-check have gotten this build a long way, but nothing here has been measured in an actual fight yet.

---

## 11. Master talent/ability candidate pool (v10) — consolidated, for sim-based refinement

Everything surfaced across this investigation, in one place, tiered by confidence. This is bigger than any realistic slot budget on purpose — the point is to have the full candidate set assembled before trimming, not to hand-pick a final board here. All items are already owned unless flagged otherwise.

### Core — never swap, foundational to the archetype

| Item | Why it's core |
|---|---|
| **Winds of Winter** (274132 live) | The entire reason this build exists — 60%+ of damage in every real parse found (§3) |
| **Titanic Mutilate** | Primary CP generator, 2/cast confirmed, 70% weapon dmg both hands (v8/v9-confirmed) |
| **Killing Machine 5/5** | Confirmed crit-rate discriminator — every high performer runs it (§3) |
| **Malice 5/5** | Confirmed crit-rate discriminator — flat crit%, all spells/attacks (§3) |
| **Conviction 5/5** | Confirmed crit-rate discriminator — flat crit%, all spells/attacks (§3) |
| **Combat Expertise 3/3** | Confirmed crit-rate discriminator — flat crit% + expertise + stamina (§3) |
| **Improved Cone of Cold 3/3** | Largest confirmed Cone of Cold/Winds of Winter damage amp, 45%, verbatim-named |
| **Path of Intelligence** | Confirmed best stat lane — wins both the Winds of Winter and Seal of Command formulas (§4) |

### Strong / flexible — owned, mechanically confirmed or broadly adopted, likely-include pending sims

| Item | Rank | Role | Adoption evidence |
|---|---|---|---|
| Ices Spike | 1 CP | 5th-CP filler, 55.25% weapon dmg under Titan's Grip (confirmed) | Recommended pick, not independently adoption-checked |
| Frostbound Cleave | — | Off-GCD bonus dmg, DBC-confirmed formula | Family-standard (Lightbound/Voidbound) |
| Piercing Ice 3/3 | Frost dmg% (+6%) | — |
| Arctic Winds 3/3 | Frost dmg% + all-dmg% | — |
| Black Ice 5/5 | Frost/Shadow dmg% (+10%/+5%) | — |
| Concussion 5/5 | Frost/Fire/Nature dmg% (+5%) | Kcdq (high performer) |
| Spell Impact 3/3 | Verbatim Cone of Cold dmg amp (~9% at 3/3) | Gunju (highest single performer, 2/3) |
| Demonic Tactics 5/5 | +10% crit, **unconditional, no pet needed** | 4/5 characters (Gunju/Titanus/Kcdq/Tdoctor — but see §10 tally, not the WoW discriminator) |
| Demonic Pact 5/5 | +10% spell dmg, **unconditional, no pet needed** | Titanus, Blasted (both 5/5) |
| Ice Floes 3/3 | −33% CD on Cone of Cold — **predicted to cut Winds of Winter's 5s CD to ~3.35s** | 4/5 characters (Gunju/Titanus/Kcdq/Blasted) — broadest adoption of anything found this session |
| Righteous Vengeance 3/3 | Crit→DoT, near-permanent uptime at this crit rate | Shared w/ Hammerdin build |
| Consecrated Weapon | Flat Holy support | Shared w/ Hammerdin build |
| Seal of Command | Holy rider on autos/Paladin abilities | Shared w/ Hammerdin build |
| Enhanced Weapon Mastery 3/3 | Free +4% all dmg, not bucket-blocked here | — |

### Conditional / tradeoff — real mechanics, but cost something or have thin evidence; sim candidates, not auto-includes

| Item | The tradeoff |
|---|---|
| **Glacial Spike + Tundra Stalker combo** | Mechanically sound (Glacial Spike applies Frost Fever, Tundra Stalker reads it globally) but **nobody scouted has actually combined them** (§10 v10 downgrade) — costs an extra button for an unproven payoff |
| **Master Demonologist 5/5 + Demonic Knowledge 3/3** | Fully dead without committing to real Felguard/Enslaved-demon pet upkeep — a rotation/complexity decision, not a free pickup |
| **Seal Fate 3/3** | Mechanically sound (Titanic Mutilate crits → chance at bonus CP) but only 1/5 scouted characters run it, at 1/3 — weak adoption evidence |
| **Elemental Focus 1/1** | Best Mana-sustain theory found (Frost-crit-triggered Clearcasting) but exact proc chance/magnitude unresolved even in live captures |
| **Honor Among Thieves 3/3** | Passive CP source, but group-only (inert solo) and chance-gated with a 3s ICD — can't be the sole 5th-CP source |
| **Arctic Reach 2/2** | Cone-radius only (AoE/trash utility), not single-target damage; unchecked exclusivity clause |
| **Energy sustain stack** (Vitality 3/3, Focused Attacks 3/3, Relentless Strikes 3/3, Combat Potency 3/3, Natural Energy 1/1, Slaughter from the Shadows 3/3) | Only covers Titanic Mutilate/Ices Spike's Energy cost — does nothing for Winds of Winter's Mana or Frostbound Cleave's Rage (v9 gap, still open) |

**Still missing from this pool, deliberately:** a Mana-sustain answer beyond the unquantified Elemental Focus lead, and confirmation of whether Ice Floes' cooldown reduction actually applies to Winds of Winter (both top open items, §10). Add to this table as new leads surface — don't let individual mentions scatter back across §4-§10 once §11 exists.
