# Scouted build: Professorpp (Duality Hammerdin — direct comparison to our own build)

**Source:** darkmoon.ascensionlogs.gg, captured 2026-08-02 (Hakkar), character_id 30915
**Raw data:** `index/scouted/scouted_Professorpp_2026-08-03.json`
**Confidence:** `external_sighting` — observed via public armory/rankings data, not proc-tested by us
**Path:** Duality (matches our own build's path)

Found via the new scouting technique documented in `INDEX_GUIDE.md` v7 — searching
`character_spell_damage` across 17 reports for "Hammer from the Heavens" by name, rather than
leaderboard browsing. Professorpp is the heaviest confirmed user of that ability found on the
server (2,471 logged hits across sampled reports) — direct relevance to
`build_paladin-hammerdin.md`.

## Stats (live sheet, Hakkar capture, level 60)
| Stat | Value |
|---|---|
| Strength / Intellect / Stamina / Spirit | 152 / 32 / 152 / 13 |
| Attack Power | 567 (103 gear + 304 from Str + 160 class base) |
| Spell Power | 177 |
| Crit | 93 rating → 6.64% melee/ranged, **0% spell** |
| Hit | 82 rating → 8.2% |
| Expertise | 33 rating → 13.2 |

Note: this capture reads as an early/leveling gear snapshot (armor 4,139, low rating pools
overall) rather than a raid-BiS comparison point — 0% spell crit in particular means this
specific capture is not useful for stat-weight comparison, only for kit/talent comparison.

## Kit
**Core damage abilities (ability bar, all r1/1):** Lightbound Cleave, Righteous Execution,
Hour of Judgement, Guardian of Ancient Kings, Judgement of Light, Flurry of Light, Consecrated
Weapon, Icy Touch, Plague Strike, Pestilence, Battle Charge — plus a wide cross-class utility
spread (Trueshot Aura, Blessing of Kings, Cleanse, Avenging Wrath, Horn of Winter, Improved Icy
Talons, Death Wish, Rampage, Slice and Dice, Blade Flurry, Demonic Leap, Cloak of Shadows,
Guarding Rune, Aspect of the Beast, Mend Pet, Kick, Blood Presence, Unchained Blink).

**Talents (full/near-full rank):** Answered Prayers 5/5, Righteous Vengeance 3/3, Judgements of
the Pure 3/3, Twin Disciplines 5/5, Crusade 3/3, Vengeance 3/3, Blood Gorged 5/5, Rage of
Rivendare 5/5, Icy Talons 5/5, Improved Blood Presence 5/5, Tundra Stalker 5/5, Bloody Vengeance
3/3, Reaping Gallows 1/1, Combat Expertise 3/3, Wrecking Crew 3/3, Improved Cleave 3/3, Sudden
Death 3/3, Master Marksman 3/3, Dual Wield Mastery 5/5, Honor Among Thieves 3/3, Prey on the
Weak 3/3, Find Weakness 3/3, Demonic Tactics 5/5, Savage Fury 2/2, Flurry 3/3.

**Overlap with our own `build_paladin-hammerdin.md`:** Hour of Judgement, Guardian of Ancient
Kings, Righteous Vengeance 3/3, Answered Prayers 5/5, Consecrated Weapon, Lightbound Cleave,
Judgements of the Pure 3/3 — core Hammerdin engine matches almost exactly. Diverges into a much
wider cross-class multi-strike/DK/hunter utility spread (Icy Talons, Blood Gorged, Rage of
Rivendare, Tundra Stalker, Master Marksman, Dual Wield Mastery) that our own build doesn't carry
— **Blood Gorged and Blood Gorged-adjacent picks are notable given `cross_character_ewm_observation`'s
existing finding that a card's dead/alive status depends on full board composition**, not
whether it's present in isolation.

## Performance (Zul'Gurub, best-of, provisional ranks)
| Boss | DPS | Rank | Percentile |
|---|---|---|---|
| High Priest Venoxis | 38,122 | #10/25 | 64.0 |
| High Priestess Jeklik | 33,261 | #5/24 | 83.3 |
| High Priestess Mar'li | 28,082 | #12/24 | 54.2 |
| Edge of Madness | 35,776 | #6/25 | 80.0 |
| High Priest Thekal | 47,476 | #5/24 | 83.3 |
| Gahz'ranka | 19,562 | #7/23 | 73.9 |
| High Priestess Arlokk | 27,786 | #6/24 | 79.2 |
| Jin'do the Hexxer | 60,608 | #6/24 | 79.2 |
| Hakkar | 37,250 | #7/25 | 76.0 |

Consistently mid-to-high percentile (54–83%) across the ZG boss set on early gear — the kit
itself is carrying more than itemization here, similar to David's Warlock write-up.

## Key insight
This is the clearest available cross-character validation that our own Hammerdin core (Hour of
Judgement / Guardian of Ancient Kings / Righteous Vengeance / Answered Prayers / Lightbound
Cleave) is a real, independently-arrived-at build pattern, not an artifact of our own theorycraft
— Professorpp assembled overlapping core talents from a completely different talent-fishing
history. Also the direct source of the 2,471-hit Hammer from the Heavens sample used to close the
`hammer_from_heavens_cannot_be_avoided` avoidance-table question this session (see primer v17).

## Open questions / not yet checked
- This capture's stat sheet (0% spell crit, low overall rating) is not representative of a
  finished build — worth re-scouting once a later/higher-gear capture exists, if one shows up in
  future report scans, before drawing any stat-weight conclusions from this character.
- Whether the wide DK/Hunter multi-strike talent spread (Icy Talons, Rage of Rivendare, Blood
  Gorged, Master Marksman) contributes real damage here or is leftover from an earlier leveling
  spec — not broken out per-ability in this capture, would need a `character_spell_damage` pull
  filtered to this character specifically to check.
