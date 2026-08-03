# Scouted build: Pumprat (dual-wield Voidbound Cleave / Fel Infused Weapon hybrid)

**Source:** live in-game inspect via inspects.nie.one (spec decode) + a real combat log the player captured (Uldaman, ALC-logged), both 2026-08-03
**Raw data:** inspect fragment decoded inline this session (not saved to `index/scouted/`, no JSON export tool was used — this predates the ascensionlogs.gg scouting pipeline); combat log at `E:\Ascension Launcher\resources\ascension-live\Logs\2026-08-03-21.18.43 WoWCombatLog.txt` (player's local machine, not in this repo)
**Confidence:** `internal_test` — this is real parsed combat-log data, not a public-API sighting, but Pumprat's own character sheet (AP/SP/crit) was never captured, so any stat back-solving below is inference, not a live-tooltip read
**Path:** Not captured — no character-sheet screenshot, no `primary_stat` on the relevant ALC snapshot

## Kit
**Character:** Pumprat, NightElf, Darkmoon Season 10 Wildcard, level 60, active spec 5 of 6 saved.

**Core damage abilities (this log, % of Pumprat's own total damage):**
| Ability | Total dmg | Share | Hits | Crit% |
|---|---|---|---|---|
| Voidbound Cleave | 1,986,118 | **47.7%** | 826 | 60.65% |
| Fel Infused Attack | 538,778 | 12.9% | 1,823 | 23.86% |
| Blade Flurry | 468,002 | 11.2% | 377 | 0% |
| Gloomblade | 277,743 | 6.7% | 344 | 38.37% |
| Melee (autos) | 162,169 | 3.9% | 778 | 45.63% |
| Stampede | 140,756 | 3.4% | 63 | 49.21% |
| Hammer of the Righteous | 131,479 | 3.2% | 102 | 46.08% |
| Duskthirst | 130,710 | 3.1% | 67 | 52.24% |
| Hammer from the Heavens | 107,439 | 2.6% | 176 | 53.41% |
| Righteous Vengeance | 86,052 | 2.1% | 242 | 0% |

**Talents (active spec, from inspect decode):** Answered Prayers 5/5, Sword Specialization 5/5, Mental Quickness 5/5, Righteous Vengeance 3/3, Flurry 3/3, Shadow Mastery 3/3, Malediction 3/3, Demonic Tactics 5/5, Demonic Pact 5/5, Emberstorm 5/5, Icy Talons 5/5, Tundra Stalker 5/5, Black Ice 5/5, Endless Flurry, Combat Experience 2/2, **Improved Cleave 3/3**, Incite 3/3, Quick Reflexes 3/3, Hunting for Sport 2/2.

**Abilities:** Fel Infused Weapon, Voidbound Cleave, Hammer of the Righteous, Hour of Judgement, Judgement of The Three Hammers, Summon Felguard, Soul Link, Gloomblade, Shadow Blades, Death Mark, Stampede, Icy Touch, Ancient of War, Incarnation of Chaos, Duskthirst.

**Weapons:** Keris of Zul'Serak + Ogre Pocket Knife — both fast off-hand-shaped daggers (dual-wield).

**Notable cross-class utility/buff picks:** Summon Felguard + Soul Link + Demonic Tactics/Pact (demon package, see below — barely used this pull) alongside a Warrior Cleave-family melee core and Hammerdin-adjacent pieces (Hour of Judgement, JotTH, Hammer of the Righteous). Eclectic classless kit, not a clean archetype match to our own build.

## Performance
Not independently re-measured against a raid-boss log this session — player-reported: **~12,000 DPS** on bosses in this log's pull(s), vs. the player's own **~3,600 DPS**. Not yet cross-checked against a specific single boss fight window in this log; the 47.7%/12.9% shares above are summed across the whole log (all pulls), not one boss.

## Key insight — Voidbound Cleave scaling, resolved via DBC

Voidbound Cleave (907280) tooltip: *"A sweeping attack that does your weapon damage plus $s1 as Shadowstrike damage... This uses Cleave modifiers."* Raw DBC (`dbc-extract.json`, `spell_dbc_raw`):

```
Effect[0] (the "$s1" bonus term): EffectBasePoints=8 -> 9 (basepoints+1), EffectDieSides=1, EffectBonusCoefficient=1.0
Effect[1] (the "your weapon damage" term): EffectBasePoints=64 -> 65, EffectDieSides=1, EffectBonusCoefficient=0.0
EffectChainTargets=2 (cleave to 2 additional nearby targets, matches tooltip's "two nearest allies")
```

Read as: **bonus damage = 9 + AP×1.0** (a full 1:1 AP-scaling term — unusually strong; every other per-hit coefficient logged in this project so far is in the 0.05-0.3 range) **+ weapon damage × ~65%** (no AP/SP scaling on this half). Confidence note: the raw `Effect` type codes (58, 31) were not matched against a verified WotLK/TrinityCore `SPELL_EFFECT_*` enum table in this project — the "bonus term vs. weapon-damage term" split is inferred from which term has a nonzero `EffectBonusCoefficient` and how that pairs with the tooltip's own two-clause wording ("weapon damage **plus** $s1"), not from a named enum lookup. Treat the split as well-supported, not certain, pending a live tooltip screenshot.

**Lightbound Cleave (907300, our own Paladin build's core damage ability) has byte-identical `EffectBasePoints`/`EffectBonusCoefficient` values to Voidbound Cleave** — same formula applies. This directly corrects `build_paladin-hammerdin.md` v8 §7, which had listed Improved Cleave dead-last on the chase list assuming it "scales only LC's flat 62 — decays with gear." That estimate had no DBC or live-tooltip source found in this session's history.

**Improved Cleave's real magnitude, confirmed via all 3 ranks' raw DBC** (`EffectBasePoints[0]`, `basepoints+1` convention): R1 (12329) = 39→**40%**, R2 (12950) = 79→**80%**, R3 (20496) = 119→**120%**. Clean linear +40%/rank. Tooltip: *"Increases the bonus damage done by your Cleave ability by $s1%."* Pumprat runs this at 3/3. Applying it to the AP-scaling bonus term only (per the "bonus damage" reading above): **`(9 + AP) × (1 + 3×0.4) = (9 + AP) × 2.2`** at max rank.

**Sanity check against the actual parse:** Pumprat's Voidbound Cleave non-crit hits average 1,425 damage (n=325, range 833-2,027) and crit hits average 3,040 (n=501, ratio 2.13× — consistent with a standard physical crit multiplier, not evidence either way on crit table). No character sheet exists for Pumprat to plug in a real AP, but the shape fits: `(9+AP)×2.2` for a plausible dungeon-tier AP (several hundred) plus `weapon_dmg×0.65` lands in the observed 800-2,000 range without needing any exotic extra multiplier. **Fel Infused Attack's damage on the same character (mean 244 non-crit, known base formula `5.5 + AP×0.05 + SP×0.05`) implies an AP+SP figure (~4,775) that is implausibly high for dungeon gear if taken at face value** — meaning Pumprat is very likely also stacking broad Shadow/Fire/all-damage% amplifiers (Malediction 3/3, Shadow Mastery 3/3, Emberstorm 5/5, Demonic Pact 5/5, Answered Prayers 5/5) on top of these base formulas. Those amplifiers may or may not also touch Voidbound Cleave's Shadowstrike half — **not yet checked which of them name "Shadowstrike" or "Cleave" verbatim vs. generic school wording** (primer §5's "named lists outrank generic wording" rule applies here and hasn't been run against this specific talent list yet).

**Practical takeaway for our own build:** Improved Cleave 3/3 is very likely one of the single highest-value remaining talents for Lightbound Cleave, not the throwaway #7 slot it was ranked at. Recommend re-prioritizing the reroll queue and getting a fresh in-game parse with Improved Cleave slotted to measure Lightbound Cleave's actual total-damage share once acquired.

## Open questions / not yet checked
1. Pumprat's actual AP/SP (no character sheet capture) — would let the `(9+AP)×2.2 + weapon×0.65` formula be checked exactly instead of just shape-matched.
2. Which of Pumprat's Shadow/Fire/all-damage talents (Malediction, Shadow Mastery, Emberstorm, Demonic Pact) explicitly name "Shadowflame"/"Shadowstrike"/"Cleave" verbatim vs. generic school wording — needed to know which also amplify Voidbound Cleave itself, not just Fel Infused Attack.
3. Whether Effect[0]'s `EffectBonusCoefficient=1.0` truly maps to AP specifically (vs. some other stat, or a hybrid AP+SP split) — the DBC field is confirmed nonzero and paired correctly with the tooltip's `$s1` term, but which in-game stat it draws from at 1.0 has not been isolated.
4. Demon package (Summon Felguard/Soul Link/Demonic Tactics/Demonic Pact) is essentially untested by this log — the pet barely swung. A log where Pumprat's pet is actually active would be needed to evaluate the demon-package angle originally flagged.
5. This log's 47.7%/12.9% shares are summed across the whole log (multiple pulls, mixed trash/boss) — the specific boss pull(s) where the player reported ~12k DPS were not isolated out for a per-fight breakdown.
