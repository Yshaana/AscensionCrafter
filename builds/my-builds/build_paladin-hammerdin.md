# Project Ascension — Paladin Build Handoff (v10)

**Location:** `builds/my-builds/build_paladin-hammerdin.md` (renamed from `Ascension_Paladin_Handoff.md` in the v12 restructure).

**Purpose:** Continue work on my Ascension (WoW private server) Paladin character. **Classless server, Season 10, Wildcard mode.** Pair this with `primer/Ascension_Context_Primer.md` (v12) and `index/ascension_index.db` (queryable spell/card index — see primer §2a).

**Realm:** Darkmoon (classless seasonal wildcard).

**v10 changelog (2026-08-03):** Re-decoded a fresh live inspect export for Elric (active spec confirmed index 4, same Hammerdin spec as always). Full detail in §7. Summary: 21 of 23 previously-documented talents confirmed unchanged at the same ranks (five spellIDs that looked unresolved on first pass all landed on exact DBC hits at their expected v6 ranks — a decoding artifact, not a board change). Two real changes: **Accuracy confirmed Rank 5/5** (closes a v6/§12 open item), and **Glyph of Blood Strike is gone, replaced by Nurturing Instinct (Rank 2/2)** — an off-theme Druid healing talent (dead Cat Form clause, marginal Agility-scaled healing), added fresh to the reroll queue in place of the card it replaced.

**v9 changelog (2026-08-03):** Major correction to §7's Improved Cleave chase-list entry, discovered while investigating a scouted player's (Pumprat) Voidbound Cleave — a different `-bound Cleave` card sharing Lightbound Cleave's exact DBC structure.

- **Improved Cleave's true magnitude is +40%/rank, linear, confirmed clean across all 3 ranks via raw DBC** (`EffectBasePoints[0]`: R1=39→40%, R2=79→80%, R3=119→120%, `basepoints+1` convention). At 3/3 this is **+120% to "the bonus damage done by your Cleave ability"** — not the small flat-62-and-decaying value §7 previously assumed. The old estimate had no DBC or live-tooltip backing found in this session's history; treat it as superseded.
- **Lightbound Cleave (907300) and Voidbound Cleave (907280) share byte-identical DBC coefficients**: Effect[0] (the `$s1` "bonus damage" term referenced by Cleave's own tooltip phrasing "weapon damage **plus** $s1") = flat 9 with `EffectBonusCoefficient=1.0` — a full 1:1 AP-scaling term, unusually strong for a per-hit coefficient in this project's data so far. Effect[1] = flat 65 with `EffectBonusCoefficient=0.0`, read as a ~65% weapon-damage component (no AP/SP scaling) corresponding to the tooltip's "your weapon damage" phrase. **"Bonus damage" in Improved Cleave's tooltip almost certainly means Effect[0] specifically** (the "plus $s1" term), not the weapon-damage half — consistent with Cleave's own tooltip pairing the two terms as separate clauses.
- **Practical formula implied for Lightbound Cleave (and any Cleave-modifier-bucket card)**: per-hit ≈ `(weapon_damage × 0.65) + (9 + AP × 1.0) × (1 + Improved_Cleave_rank × 0.4)`. At 3/3 Improved Cleave that bonus term becomes `(9 + AP) × 2.2`. This is independently corroborated: applying this exact formula to a scouted character's own AP-plus-bonus estimate (back-solved from a separately-known formula on a different ability in the same log) landed within range of that character's actual observed Voidbound Cleave damage — see `builds/shared/scouted_Pumprat_2026-08-03.md` for the full derivation.
- **Consequence: Improved Cleave should NOT be ranked last on the §7 chase list.** Moved up pending a fresh in-game parse to quantify Lightbound Cleave's actual total-damage share at our own build's AP (not yet re-measured this session) — see the reprioritized `2b` row below. The "Total gap ≈ 40% damage" figure at the bottom of §7 predates this correction and should be treated as stale until Lightbound Cleave is re-measured with the corrected formula.
- **This does NOT change the Cleave class-tag verdict** (Lightbound Cleave / Voidbound Cleave both still confirmed Warrior-tagged, still feed zero Hammerdin procs, primer §4) — Improved Cleave lives in the same Warrior/Cleave modifier bucket, so it amplifying these cards is consistent with, not a contradiction of, that rule.

**v8 changelog (2026-08-03):** Daily patch-note check (new standing practice, primer §5) against `https://ascension.gg/en/changelog/1`, Darkmoon-filtered. Two entries relevant to this build, both going live 2026-08-03:

- **Enhanced Weapon Mastery / Answered Prayers / Unending Fury / Blessed Weapons exclusivity is now a codified server rule**, not just a live-tooltip clause. No verdict change — §7 already has EWM correctly flagged as bucket-blocked and rerolled away — but this raises the fact's confidence tier from "live-tooltip-confirmed" to "patch-note-confirmed." No action needed.
- **⚠ New open item: proc-trigger fix for off-GCD / On-Next-Hit replacement abilities** ("certain proc effects could be triggered by abilities that are not on the global cooldown, including... Cleave, Raptor Strike, Maul and Heroic Strike... restores intended proc behaviour"). **Lightbound Cleave is exactly this ability shape** — Cleave-tagged, off-GCD, next-swing-queued (§0, §11). If LC's proc interactions were affected by the bug this patch fixes, its behavior may have shifted today. **Added to §9 test queue** — needs a fresh dummy check on what LC does and doesn't feed post-patch, since §2's confirmed "Lightbound Cleave = 0 Hammerdin procs" verdict predates this fix and should be re-verified rather than assumed to still hold unchanged.

Also noted, not directly actionable: a 2026-07-28 Darkmoon-wide fix corrected Path of Duality not granting Ranged Attack Power — a different clause than the SP-amp/cross-crit-conversion question in §4/§9 item 1, doesn't resolve it.

**v7 changelog (2026-08-02, late night):** Decoded another player's ("Sling") full 6-spec loadout via `decode_inspect_export.py` and compared his Paladin/Hammerdin spec against this build (§8). **Two external data points added to the chase list**: he's running both Divine Storm and Execution Sentence, both currently on our own chase list — evidence they're live and playable, not a substitute for our own parse. **Retraction**: §8's *"Avenging Wrath / Guardian of Ancient Kings — substitutes, take the first"* was wrong — they're independent cooldowns on separate systems (flat all-damage buff vs. Holy-specific cooldown-reset-and-buff), not redundant picks; both belong on the chase list. Also observed: Sling runs Enhanced Weapon Mastery live (undisputed, since he carries none of its exclusivity-bucket mates) — a clean real-world illustration that the same card's dead/alive status depends entirely on the rest of the board, not the card itself.

**v6 changelog (2026-08-02, late night):** Cross-referenced a live in-game inspect/WeakAura export (55 spell IDs) against the catalog, confirming the current real loadout for the first time since v5's talent rolls finished. **22 of the original 25-slot board are unchanged.** Three dead slots identified in v5 are now confirmed gone (**Shadow Strikes, Enhanced Weapon Mastery, Seals of the Pure** — all rerolled away since v5), replaced by **Accuracy**, **Glyph of Seal of Command** (deliberate temporary mana fix, pending Spellblade reaching 3/3), and **Glyph of Blood Strike** (unevaluated filler, next reroll target). Fanaticism and Spellblade remain at their v5 ranks (1/3 each), unchanged. **Lunar Guidance's presence is independently confirmed** as the likely source of the residual Bonus Damage/Healing gap noted in §4 — matches the v5 hypothesis exactly. Three ability-bar entries (**Berserker Stance, Ghost Wolf, Frostfall**) turned up in the export with no prior documentation — confirmed as low-priority leftovers, not core rotation, not worth analysis time. New reusable practice (now in the primer, §5): when a live-exported spell ID doesn't resolve against the catalog, check ±1-3 for a known card — multi-rank talents appear to get a distinct spellID per rank, and the catalog only stores one canonical ID per card.

**v5 changelog (2026-08-02, evening):** **Talent rolls are finished — the board is final** (§7). Four real dungeon parses recorded, including one full boss fight with cooldowns. Major resolutions: **Holystrike crits on the SPELL table — §9 test #5 ANSWERED**, which makes spell crit worth **5× melee crit** and reweights the entire gearing plan. **Duality's SP amp and cross-crit conversions are both absent from the live sheet** — the single most urgent open item. **Righteous Vengeance measured at 30% and confirmed pooling.** Three v4 verdicts formally overturned: **Sword Specialization works** (both clauses), **Consecration earns its slot**, **Art of War was cut on the wrong tooltip clause**. New stat weights in §10 derived empirically from the parse rather than from a model — including a **walkback on hit and expertise**, which an earlier draft of this document overstated (crit table and hit table are independent rolls; only ~5.4% of damage is confirmed spell-hit-gated).

---

## 0. Session state (start here)

- **Level 60, class fixed, guarantee slots spent.** Rerolls are the only tuning lever.
- **Talent rerolls: ongoing.** Board has moved since v5 — 3 slots turned over (§7). Chase list unchanged, still fully outstanding.
- **Gear is mid-upgrade.** Zul'Gurub is now accessible; chase weapons identified (§6).
- **Immediate next actions, in order:**
  1. **Verify which Path is actually active** (§4 — two independent signals say Duality isn't applying)
  2. **Fix the rotation** — Judgement and Holy Shock are being cast ~3 times per 5-minute fight (§11). Largest free gain available.
  3. **Run the Miss/Dodge breakdown on Hammer from the Heavens** (§10) — settles whether hit and expertise are worth anything at all
  4. **Gear for crit** — it is the best stat by a distance and nothing else is close
  5. **(v8, new)** Re-check Lightbound Cleave's proc interactions post-2026-08-03-patch — see v8 changelog above and §9 item 10

---

## 1. Build identity

- **Path:** Path of Duality — **⚠ but see §4; neither the SP amp nor the cross-crit conversions are visible on the live sheet.**
- **Weapons:** Titan's Grip. Currently MH 3.57 / OH 2.60. Chase pair identified: **Light's Hope** (69.9 DPS, 3.70) + **Zin'rokh** (64.1 DPS, 3.80), both 2H swords.
- **Archetype:** **Holy-dominant hybrid melee.** ~70% of damage resolves on the spell crit table. Three proc engines:
  1. **Hammerdin** ← **Paladin-tagged** damaging abilities → Hammer from the Heavens + **Hour of Judgement cooldown reduction**
  2. **Judgement of the Three Hammers** ← **any** direct damage → 3 Physical hammers
  3. **Purification By Light** ← weapon-damage spells/abilities → Exorcism hit + Consecration ground
- **Stat posture:** **Spell-crit-first.** Spell crit rating is worth 5× melee crit rating. SP and AP are currently at parity (~1.00) *because the Duality amp isn't applying* — if it comes back, SP jumps to ~1.77 and the posture becomes decisively SP-lean.

---

## 2. THE CLASS-TAG RULE (confirmed, load-bearing)

**A card's `uses X modifiers` line predicts its class tag — not its flavour, name, or damage school.**

| Card | Borrows from | Tag | Feeds Hammerdin? |
|---|---|---|---|
| Dawnreaver | Crusader Strike | Paladin | Yes |
| Light's Hammer | — (native) | Paladin | Yes |
| Judgement / Holy Shock | — (native) | Paladin | **Yes — underused, see §11** |
| Dawn Strike | Sinister Strike | Rogue | No |
| Holy Finish | Eviscerate | Rogue | No |
| Lightbound Cleave | Cleave | Warrior | **No — confirmed pre-2026-08-03 patch; re-verify, see §9 item 10** |
| Whirling Light | Whirlwind | Warrior | No |
| **Blades of Light** | **Bladestorm** | **Warrior** | **No — and it blocks everything else** |

**⚠ Blades of Light is a trap button.** *"While under the effects of Blades of Light, you can move but cannot perform any other abilities."* It is Warrior-tagged (no Hammerdin proc) **and** it locks you out of casting the Paladin abilities that would reduce Hour of Judgement's cooldown. Every second of channel actively suppresses your best engine. It does feed **JotTH** (any direct damage), so it is a legitimate filler *only* while Hour of Judgement is genuinely unavailable.

---

## 3. LUCKY FLAG — THEORY RETIRED

Falsified in v4 and unchanged. Divine Steed (no-LUCKY) rolls repeatedly. Working roll model is **rarity × affinity only**. Do not build guarantee-slot or reroll strategy around the LUCKY flag.

---

## 4. MEASUREMENTS

### 🔴 URGENT — Path of Duality may not be active

Two independent signals, both from the live sheet:

| Expected under Duality | Observed |
|---|---|
| Itemised SP ×1.75 → Bonus Damage ≈ 660 | **Bonus Damage 400 vs Bonus Healing 379** (5.5% gap — consistent with Lunar Guidance alone, unamped) |
| Int → melee crit, Agi → spell crit | Melee crit sources list **Agility**; spell crit sources list **Intellect** — the base-game conversions, with both tables summing exactly and no room for a hidden term |

**The v4 "Int → melee crit ≈ 38/1% CONFIRMED" measurement is retracted.** It rested on a single +11 Int swing producing +0.29% melee crit — about 4 crit rating at the now-known conversion, well inside contamination range. At Int 289 the sheet showed **no Intellect line in the melee crit table at all**.

**Consequence:** Int no longer widens the melee-over-spell crit lead. It narrows it (spell-side only). The v4 claim that "no gear allocation can push spell crit above melee crit" was directionally backwards — though the practical conclusion is moot now that spell crit is the priority anyway.

**Action:** confirm the active Path in-game. Path switching is free and instant, so this may simply be the wrong path selected. If Duality *is* active and neither clause fires, it's a bug worth reporting. *(Note: a 2026-07-28 Darkmoon patch fixed Duality not granting Ranged Attack Power — a different clause, doesn't resolve this.)*

### ✅ Holystrike crits on the SPELL table — §9 #5 RESOLVED

From the King Gordok parse, crit rates sorted by school against sheet values (**melee 21.76% / spell 18.95%**):

| Source | School | Observed crit |
|---|---|---|
| Consecrated Holy Weapon | Holy | 39.0% |
| **Lightbound Cleave** | **Holystrike** | **38.1%** |
| Hammer from the Heavens | Holy | 35.9% |
| **Dawn Strike** | **Holystrike** | **33.3%** |
| Sword Specialization | Physical | 20.0% |
| Judgement of the Three Hammers | Physical | 17.4% |
| Melee autos | Physical | 16.2% |

Holystrike abilities crit at ~2× the melee sheet rate and land alongside pure-Holy sources. **Holystrike receives Holy modifiers**, so Holy Power 5/5, Holy Specialization 5/5 and Twin Disciplines 5/5 are covering Lightbound Cleave, Dawn Strike, Whirling Light, Holy Finish and Blades of Light — far more of the kit than v4 assumed.

**Crit-table exposure:**
```
Spell table   70.2%   (HftH, CHW, LC, Dawn Strike, Holy Shock, Judgement, SoV, most unlisted)
Melee table   14.3%   (autos, Sword Spec procs, JotTH)
Cannot crit   15.3%   (Righteous Vengeance, Holy Vengeance DoT, Hour of Judgement, Consecration)
```

### ✅ Righteous Vengeance — 30%, pools, cannot crit

> Direct critical strikes with spells and abilities make your target take **30% additional damage over 8 seconds** as Holy damage.

- **0% crit across four parses** → periodic, confirms the ground/DoT rule
- **92–101% uptime** with damage-per-tick ranging 135→536 → **pools on refresh** (Ignite/Deep Wounds style), does not clip
- Measured contribution **6.4–9.0%** of total damage
- **Raises the marginal value of a crit by 40%**: a crit is now worth 2.6× a normal hit instead of 2.0×

This is why spell crit dominates the weights — every crit seeds a DoT on top. *(Also relevant for comparison: `builds/shared/synergy_winds-of-winter.md` runs the same talent and reports 87.7–89.5% uptime feeding off a near-100% crit rate — consistent with the pooling mechanic here.)*

### ✅ Confirmed magnitudes (live tooltips)

| Card | Magnitude |
|---|---|
| Titan's Grip | **Physical damage dealt −10%** |
| Vengeance (Paladin r3) | **3% per stack, 3 stacks, 30s** → 9% Physical + Holy |
| Blood Gorged | **+10% damage above 75% health, +10% armour ignore** |
| Deadliness r5 | **+10% attack power** |
| Enhanced Weapon Mastery | +4% all damage — **⚠ does not stack with Answered Prayers, Unending Fury or Blessed Weapons; highest only. As of 2026-08-03, this is a codified Darkmoon server rule, not just a tooltip clause (v8).** |
| Righteous Vengeance | 30% of crit damage as an 8s Holy DoT |
| Crit rating conversion | **exactly 14.0 rating per 1%**, identical on both schools |

### ✅ Other resolutions

- **Sword Specialization works — both clauses.** The hit clause (`spells and abilities`, no weapon requirement) was carrying melee hit to cap on a polearm; the extra-attack clause logs **6.8K / 3.1% / 10 procs**. The v4 "producing ZERO output" verdict is overturned. Note the `+40% while wielding a single Two-Handed Weapon` rider does **not** apply under Titan's Grip.
- **Consecrated Weapon is flat.** `m1/77 to M1/25 based on weapon speed`, no SP or AP term. Still 17.8–22.4% of damage, but its share will decay as gear scales. Do not gear around it.
- **Judgement of the Three Hammers has the largest coefficient in the kit:** `3 × (m1 + SP×0.325 + AP×0.278)` ≈ 0.975 SP + 0.834 AP per proc. **SP-weighted over AP.** Physical school, so it pays the Titan's Grip tax.
- **Seals of the Pure excludes Seal of Fervor.** It lists Righteousness, Vengeance, Command and Execution Sentence only. Combined with SoF being Fire-school (missing Twin Disciplines 5/5, Answered Prayers' Holy rider, Holy Spec, Holy Power 5/5, Holy Focus), **the seal parse resolves to SoC + SoV via Twist of Faith.** SoF is dead.
- **Consecration earns its slot** — 2.2–7.6% at 30–79% uptime across parses. The v4 cut is overturned.
- **The Art of War was cut on the wrong clause.** Its first line is *"Increases the damage of your Judgement, Crusader Strike, Execution Sentence and Divine Storm abilities by X%"* — always-on, and Dawnreaver uses Crusader Strike modifiers. Back on the chase list.
- **Autos are irrelevant.** 37 landed swings in ~309 seconds (4.2% of damage) with off-hand hit at **57/220** — unreachable. Weapon damage matters only through ability coefficients.

---

## 5. Wildcard / reroll mechanics

Unchanged from v4:
- **Cards guarantee MAX RANK; RNG rolls land 1–5.** The `X/Y` display is the roll result, not spent points. No respec.
- **Partial ranks are assets** — upgrades are self-funding (refund on hit) and staff have said held partials roll their own upgrades more often. Never reroll away a partial you want.
- Auto-roller: tag likes/dislikes, it rerolls until targets hit or budget ends.
- **Open question:** does the elevated upgrade chance apply to *any* slot or only the holding slot?

---

## 6. Gear state

**Live stats (King Gordok parse):**
```
Str 134 · Agi 46 · Int 189 · Sta 270 · Spi 29
Melee:  585–669 dmg · 3.57 / 2.60 speed · AP 546 · crit 21.76%
        hit 57/30 (CAPPED) · off-hand hit 57/220 · ArP 0 · expertise 5/26
Spell:  Bonus Damage 400 · Bonus Healing 379 · hit 57/96 · haste 29 · crit 18.95%
```

**Cap status — mostly a non-issue, see the §10 walkback:**

| Stat | Have | Need | Verdict |
|---|---|---|---|
| Melee hit | 57 | 30 | Overcapped, but unified with spell hit so not separately fixable |
| Spell hit | 57 | 96 | ⚠ **96 is the +3 RAID cap.** Effectively capped for dungeon content (~6% miss at +2). Only ~5.4% of damage is confirmed spell-hit-gated. |
| Expertise | 5 | 26 | ⚠ Provisional — dodge exposure unverified. Do not chase over crit. |
| Off-hand hit | 57 | 220 | ⛔ unreachable — treat as nonexistent |

**No mis-itemisation to fix here.** Clean parses at 57 hit are expected, not surprising. Gear for crit.

**Chase weapons (Zul'Gurub tier):**
- **Light's Hope** — 2H sword, 206–311, 3.70, 69.9 DPS, +16 Str, +20 Sta, 15 crit, 9 haste, "Brutal Crusader" *(effect unidentified — read it)*
- **Zin'rokh, Destroyer of Worlds** — 2H sword, 202–285, 3.80, 64.1 DPS, +28 Sta, 17 crit, +60 AP

**Main hand assignment matters:** all three seals key off **main hand autos and Paladin melee abilities only**. Higher-DPS weapon (Light's Hope) goes MH.

**⚠ Neither weapon itemises SP or Int.** With the SP amp currently absent this is moot, but if Duality comes back online, look for an SP/Int 2H sword before committing.

**⚠ Titan's Grip is closer than "premise card" implies.** It costs −10% physical *and* +19% white miss. Its wins are Whirling Light (only ability using both weapons) and roughly 1.6× the CHW proc rate. Dropping it would free an ability guarantee slot and re-enable Sword Spec's +40% single-2H rider. Worth an actual A/B parse. *(Comparison note: `builds/shared/synergy_winds-of-winter.md` also runs Titan's Grip, but on a build where the core nuke doesn't scale off weapon damage at all — its −10% physical tax matters even less there than it does for us, since JotTH and Consecrated Weapon both pay it here.)*

---

## 7. FINAL TALENT BOARD (v10 — confirmed live via inspect export, 2026-08-03)

### Slotted
```
Answered Prayers 5/5        Holy Focus 5/5              Holy Power 5/5
Holy Specialization 5/5     Twin Disciplines 5/5        Sword Specialization 5/5
Dual Wield Specialization 5/5   Deadliness 5/5          Lunar Guidance 3/3
Judgements of the Wise 3/3  Judgements of the Pure 3/3  Righteous Vengeance 3/3
Wrecking Crew 3/3 (locked)  Vengeance 2/3                Flurry 2/3
Mental Quickness 4/5        Fanaticism 1/3               Spellblade 1/3
Hammerdin 1/1                Purification By Light 1/1   Righteous Zealot 1/1
Twist of Faith 1/1           Accuracy 5/5                Nurturing Instinct 2/2 (NEW, see below)
```
**Plus one glyph-type card:** Glyph of Seal of Command (deliberate, temporary — see reroll targets).

**Since v6 (v10, 2026-08-03):** Re-decoded live inspect export. Every v6 talent confirmed still present at the same rank (Vengeance/Flurry/Fanaticism/Spellblade/Mental Quickness all initially looked unresolved against the catalog on this pass but each resolved to an exact spellID hit in the DBC extract, same ranks as v6 — no actual change, just different spellIDs than the ones previously seen at those ranks). Two real changes:
- **Accuracy confirmed Rank 5/5** — closes the open item from v6/§12. Tooltip: "Increases your chance to hit with all spells and attacks by X%." Given the hit walkback (§10 — spell hit only matters for ~5.4% of damage, melee hit already overcapped for dungeon content), this is likely a low-marginal-value slot, but not worth rerolling away since there's nothing better to put a "chance to hit" card toward at 5/5 already sunk.
- **Glyph of Blood Strike is gone, replaced by Nurturing Instinct (Rank 2/2).** The v6 reroll-first recommendation for Blood Strike was evidently actioned. Nurturing Instinct's tooltip: *"Increases your healing spells by up to $s1% of your Agility, and increases healing done to you by $s1% while in Cat form."* This is a Druid Restoration talent — the Cat Form clause is fully dead (no shapeshifting in this kit), and the Agility-scaled healing clause is marginal at best (Agility is a 0.15-weight stat per §10, and this build isn't healing-postured). **Reads as another off-theme/low-value reroll landing, not an improvement over Blood Strike.** Added to reroll targets below.

### 🔴 Reroll targets (current)
1. **Nurturing Instinct 2/2 (NEW, v10)** — off-theme Druid healing talent (Cat Form clause fully dead, Agility-scaled healing marginal for a DPS-postured build). Same "filler landed off-theme" shape as the Blood Strike slot it replaced. Reroll-first candidate.
2. **Fanaticism 1/3** — unchanged from v5: Judgement crit only, unless Execution Sentence gets slotted.
3. **Glyph of Seal of Command** — **not a mistake, don't touch yet.** Deliberately held as a mana-sustain stopgap until Spellblade reaches 3/3, at which point Judgements of the Wise + maxed Spellblade should cover mana and this can be rerolled freely. Log this as a *known temporary state*, not a dead slot.

### Protect (never reroll)
Hammerdin · Purification By Light · Righteous Zealot · **Twist of Faith** (enables the SoC + SoV pairing) · Righteous Vengeance 3/3 (locked) · Wrecking Crew 3/3 (locked) · Holy Power 5/5 · Holy Specialization 5/5 · Twin Disciplines 5/5 · Holy Focus 5/5 · Answered Prayers 5/5 · Sword Specialization 5/5 · Deadliness 5/5 · Dual Wield Specialization 5/5 · Judgements of the Wise 3/3

**Seals of the Pure removed from protect** — confirmed intentionally rerolled away since v5; player rated it "not terrible" but not a priority to protect. Consistent, not a gap to fix.

### Upgrade magnets (partial — keep and fish)
**Vengeance 2/3** (last rank ≈ +3% total damage) · **Flurry 2/3** · **Mental Quickness 4/5** · **Spellblade 1/3** (target 3/3, unlocks the Glyph of Seal of Command swap)

### 🎯 Chase list — still missing, priority order

| # | Talent | Value | Rank risk |
|---|---|---|---|
| 1 | **Combat Expertise 3/3** | +6% crit **both tables** → **+6.3%** | partial |
| 2 | **Blood Gorged 5/5** | +10% all damage, +10% ArP → **+10%** (⚠ conditional on >75% health — primer §1) | partial |
| 3 | **Conviction 5/5** | +5% crit **both tables** → **+5.3%** | partial |
| 4 | **Dark Justicar 0/1** | SoV to 10 stacks; Judgement consumes for `0.58 × (SP+AP)` → **+8.4%** | **none — 1/1** |
| 5 | **Inevitable Vengeance 0/1** | SoV DoT crits + hastes; **1% Phys/Holy damage-taken per stack → 10%** | **none — 1/1** |
| 6 | **The Art of War 3/3** | +% Judgement, Crusader Strike (→ Dawnreaver), Divine Storm | partial |
| 2b | **⚠ Improved Cleave 3/3 (REPRIORITIZED, see v9)** | **+120% to LC's AP-scaling bonus component** (not a flat 62 — see v9 changelog). Was ranked #7/last; likely belongs much higher. | partial |

**Total gap ≈ 40% damage**, concentrated in six cards (pre-v9 estimate — does not yet reflect Improved Cleave's corrected magnitude, see v9). The two 1/1s are the cheapest acquisitions (a hit is a complete hit). None of these six appear in the v6 live export — chase list is unchanged, still fully outstanding.

### ⚡ Execution Sentence cluster — status update
v5 noted three slotted talents supporting Execution Sentence: Seals of the Pure, Judgements of the Pure, and Fanaticism. **Seals of the Pure is now gone**, dropping this to two. Judgements of the Pure and Fanaticism still support it. Re-evaluate whether an Execution Sentence ability slot is still worth it with one fewer multiplier behind it.

---

## 8. ABILITY tags

### Protect
Titan's Grip · Consecrated Weapon · Hour of Judgement · Judgement of the Three Hammers · Lightbound Cleave · Dawnreaver · Dawn Strike · **Judgement** · **Holy Shock** · Whirling Light · **Seal of Command** · **Seal of Vengeance** · Consecration

### Chase
1. **Divine Storm** — the outstanding **Paladin-tagged** weapon-damage GCD; directly compresses Hour of Judgement. **Magnitude confirmed via DBC (v10):** 110% weapon damage to multiple enemies (`EffectBasePoints=109->110`), heals up to 3 party/raid members for a % of damage caused. Sanity-checked against Elric's own Dawn Strike average (812/hit in the 2026-08-03 log) — at self-buffed weapon damage ~723 avg, 110% lands at ~795/hit, same order of magnitude as an existing similar-shaped GCD ability. *(External sighting, v7: another player's Paladin/Hammerdin spec runs this live.)*
2. **Execution Sentence** — two talents now support it (Judgements of the Pure + Fanaticism; Seals of the Pure dropped off, §7). **Magnitude UNRESOLVED even via DBC (v10):** all three EffectBasePoints are the DBC "no value" sentinel (-1) and EffectTriggerSpell is empty — the real formula lives entirely outside the effect slots this extract captures (likely a hardcoded script trigger). Cannot be quantified without a live tooltip screenshot showing the resolved number.
3. **Avenging Wrath AND Guardian of Ancient Kings — both, independently. (Corrected v7, see retraction in §12.)** Magnitudes confirmed via DBC (v10): Avenging Wrath = **+20% all damage/healing, 20s duration** (`EffectBasePoints=19->20`, `DurationIndex=18`→20,000ms — duration is DBC-confirmed, cooldown is NOT in this extract, treat any uptime % as an assumption). Guardian of Ancient Kings = **+15% Holy damage, 12s duration** (`EffectBasePoints[1]=14->15`, `DurationIndex=29`→12,000ms, same cooldown caveat) plus the HotR/Divine Storm/Holy Shock cooldown resets, which compound Hour of Judgement uptime in a way this simple % can't capture. They aren't redundant: even under a worst-case reading of their "does not stack with similar effects" clauses, that only blocks simultaneous *buff* uptime, not sequential use on two independent cooldowns.
4. **Twisted Mind** — SP still good, but its hit rider is now worthless (melee capped). **Magnitude confirmed via DBC (v10):** flat **+60 Spell Power** (`$PL*1` = player level × 1 = 60 at level 60, not a percentage), **+3% hit** (worthless, melee capped / spell hit barely matters), and a healing/absorb reduction whose own magnitude is *itself* hidden behind a second sub-spell (978705) not in this extract. Also a bar-changing/stance-type ability — check it doesn't conflict with anything else on the bar before slotting.
5. **Divine Protection** — **defensive, not a DPS card.** Magnitude confirmed: **-50% damage taken, 12s duration** (`EffectBasePoints[1]=-51->-50`, `DurationIndex=29`→12,000ms). Shares a cooldown-exclusion with Avenging Wrath (can't use either within a window of the other). Kept on the chase list for survivability, not counted in any DPS estimate.
6. **Bloodlust** — **magnitude confirmed via DBC (v10):** +30% melee/ranged attack speed, +20% casting speed (`EffectBasePoints`: index2=29->30 = $s3 attack speed, index0=19->20 = $s1 cast speed), **40s duration** (`DurationIndex=64`→40,000ms). No cooldown in this extract — in most WotLK-family servers this class of raid cooldown runs on a long timer (~10min class), which would cap its average-fight contribution in the low single digits; treat that framing as an assumption pending confirmation, not a measured value.

### Cut
**Seal of Fervor** (Fire school, excluded from Seals of the Pure) · Exorcist's Slash · Judgement of Light / Justice · **Blades of Light for single-target** (Warrior tag + ability lockout starves Hammerdin; AoE/filler only)

### Leftover / not evaluated (v6)
Confirmed present in the v6 live export but **not core rotation** — player-confirmed as low-priority filler, not worth analysis time unless reroll scrolls free up: **Berserker Stance** (Warrior stance, leftover, "not terrible" so not a priority reroll), **Ghost Wolf**, **Frostfall** (both untouched due to reroll-scroll scarcity, not a deliberate kit choice).

---

## 9. TEST QUEUE

**Resolved this session:** #5 Holystrike modifiers ✅ · #6 partially (Holystrike is spell-table) ✅ · #7 Agility reading ✅ (Agi → melee crit only, ~32.4/1%) · #3 seal parse ✅ (SoC + SoV win; SoF dead) · #11 Divine Strength ✅ (cut)

**Remaining, priority order:**

1. **🔴 Confirm the active Path.** Two signals say Duality's SP amp and cross-crit conversions aren't applying. This gates the entire SP-vs-AP question.
2. **Rotation fix parse.** Judgement and Holy Shock on cooldown vs current. Target: Hour of Judgement uptime from 13.6% → 27%+.
3. **Titan's Grip A/B.** Dual 2H vs single 2H, same content. Costs −10% physical and +19% white miss against Whirling Light's second weapon and 1.6× CHW procs.
4. **Answered Prayers' all-damage %** — live tooltip read. Decides whether Enhanced Weapon Mastery is completely dead.
5. **"Brutal Crusader" on Light's Hope** — identify the effect. If it's a Crusader-family Str proc it changes Str's weight.
6. **Hammer from the Heavens coefficients** (sub-spell 282987, hidden). 22.1% of damage with unknown scaling — the largest uncertainty in the stat weights.
7. **Dark Justicar consume-vs-hold** once acquired: Judgement eats 10 SoV stacks for burst but drops Inevitable Vengeance's debuff to zero.
8. **Mental Quickness exclusivity** — does it pool with Holy Focus's capstone or Answered Prayers?
9. **Reroll mechanic** — does the partial-rank upgrade bonus apply to any slot or only the holding slot?
10. **🆕 (v8) Re-verify Lightbound Cleave's proc behavior post-2026-08-03 patch.** The patch note "fixed an issue where certain proc effects could be triggered by abilities that are not on the global cooldown, including... Cleave... restores intended proc behaviour" directly targets LC's ability shape (off-GCD, Cleave-tagged, next-swing-queued). §2's "0 Hammerdin procs" verdict was measured before this fix — confirm it still holds, and check whether LC's interaction with any other proc engine (JotTH, PBL) changed too.

---

## 10. STAT WEIGHTS (v5 — derived empirically from the King Gordok parse)

**⚠ Hit Rating and Crit Rating are UNIFIED stats on this server** — the sheet shows melee and spell values that move together (hit 57/57). You cannot buy the spell half without the melee half, so weights below are the **combined per-rating-point value**, entered directly into the in-game stat-weight tool.

| Field | Weight | Note |
|---|---|---|
| **Crit Rating** | **2.00** | spell half **1.65** + melee half **0.33**. 70.2% of damage on the spell table, ×1.4 from Righteous Vengeance. **Clear best stat, not close.** |
| Weapon DPS | 2.6 | `0.72 per avg damage × 3.57 speed`; ability coefficients only — autos are 4.2% |
| Attack Power | **1.00** | baseline |
| Strength | 1.00 | 1:1 AP — no premium |
| Spell Power | 1.00 | **→ 1.77 if the Duality ×1.75 amp is restored** |
| Holy Spell Power | 0.95 | **→ 1.68** with the amp; ~95% of general SP since nearly all magic damage is Holy |
| Intellect | 0.50 | spell crit **0.38** (~61/1%) + Lunar Guidance SP **0.12** |
| Haste Rating | 0.50 | swing-rate sources only; raise toward 0.8 if spell haste reduces the GCD |
| **Hit Rating** | **0.30** | ⚠ raid only — **0.00 for dungeon content.** See the walkback below. |
| **Expertise** | **0.30** | ⚠ provisional — see below. Was overstated at 0.80. |
| Armor Pen | 0.18 | melee-table physical sources only |
| Agility | 0.15 | melee crit only (~32.4/1%) |
| Stamina | 0.15 | survivability; no Blood Gorged yet |
| Mana per 5 | 0.10 | JotW covers it |
| Spirit / Spell Pen / Resilience | 0.00 | Holy is unresistable |

**Gearing order:** *crit → weapon DPS → SP ≈ AP ≈ Str → Int → haste → rest.* Do not pass over a crit or weapon upgrade for hit or expertise.

### ⚠ Hit and expertise — walkback (important)

An earlier v5 draft told the player to cap spell hit and expertise first. **That was wrong on both counts**, and the error is instructive enough to record.

**The mistake:** having established that Holystrike *crits* on the spell table, I assumed it also *rolls against spell hit*. **Crit table and hit table are independent rolls.** Sorting the parse by what actually makes a hit check:

| Category | Share | Rolls spell hit? |
|---|---|---|
| Holy Shock + Judgement | **5.4%** | ✅ yes — real spells |
| Lightbound Cleave, Dawn Strike, autos, Sword Spec | ~22% | ❌ melee hit — **already capped at 57/30** |
| Righteous Vengeance, Holy Vengeance, Consecration, Hour of Judgement | ~15% | ❌ periodic — cannot miss |
| CHW, Seal of Vengeance | ~21% | ❌ ride an attack that already landed |
| **Hammer from the Heavens, JotTH** | **~29%** | ✅ **RESOLVED (2026-08-03) — cannot be avoided, see below** |

**Confirmed spell-hit-gated damage: ~5.4%.** Even at full raid tier with zero spell hit that's `17% × 5.4% ≈ 0.9%` of damage.

**Second reason it doesn't apply:** the 96 figure is the cap vs a **+3-level raid boss**. Spell miss is ~4% vs equal level, ~5% at +1, ~6% at +2, and only jumps to 17% at +3. At 57 rating the player is **already effectively capped for all dungeon content** — which is exactly why the parses show no misses.

**Expertise, same error.** Dodge does apply to melee abilities regardless of crit table, but the 0.80 figure assumed a large dodge-exposed share. It has not been verified that Lightbound Cleave is actually being dodged. Held provisionally at 0.30 pending the check below.

**✅ RESOLVED (2026-08-03 scouting session) — was: "The one unknown that could reverse this."** Hammer from the Heavens is 22.1% of damage, and it was not known whether summoned procs roll a hit check (if they do, raid-tier Hit Rating rises to ~1.2; if they don't, it stays near zero permanently). Now settled: **they do not roll an avoidable hit check.** 4,962 pooled Hammer from the Heavens hits across 11 characters (Professorpp 2471, Geniusdex 988, Phantomx 774, Germarona 239, and 7 others) and 17 reports show 0 miss/dodge/parry/full-resist. See `confirmed_facts.hammer_from_heavens_cannot_be_avoided` and primer v17. **Raid-tier Hit Rating stays near zero — the walkback's provisional weight (0.30) stands, does not reverse to ~1.2.** This is an avoidance/hit-table finding, not a crit-table one — Hammer from the Heavens' crit table was already separately confirmed via Holystrike (primer §1 v4). Its damage composition (30/30/40 SP/AP/flat split, second caveat below) remains unconfirmed.

**New scouting lead, not yet acted on:** Professorpp (Duality, 2,471 logged Hammer from the Heavens hits across sampled reports) is the heaviest confirmed user of this build's core ability found on the server — worth scouting as a comparison build. Also worth a look: Geniusdex (988 hits), Phantomx (774 hits).

**Off-hand hit rating is worth 0 regardless** — 57/220 is unreachable at this tier; treat off-hand white swings as nonexistent.

**Two caveats:**
- **Hammer from the Heavens is 22.1% of damage with unknown coefficients** (hidden sub-spell). Its composition is assumed 30% SP / 30% AP / 40% flat. If it's mostly flat, SP and AP weights drop and spell crit's dominance grows further.
- **SP ≈ AP at 1.01 vs 1.00 only because the ×1.75 amp isn't applying.** Restore it and SP becomes the clear best non-crit stat.

### 10a. Extrapolated ceiling from the remaining chase list (v10, 2026-08-03 snapshot)

Speculative, not measured — a projection from current stats + confirmed talent/ability magnitudes, not a fresh parse. Re-derive if AP/gear shifts meaningfully; the **method** is the reusable part, not the specific numbers.

**Inputs used:** self-buffed character sheet, 2026-08-03 — AP 584, Bonus Damage (SP) 533, melee crit 32.46%, spell crit 28.86%. Lightbound Cleave baseline from the same day's Uldaman log: 150 hits, non-crit avg 703 (n=94), crit avg 1,407 (n=56), 10.8% of total damage (144,922 / 1,336,753).

**Talent stack (multiplicative, not additive — corrects the older "~40%" additive estimate in §7):**

| Card | Multiplier |
|---|---|
| Combat Expertise 3/3 | ×1.063 |
| Blood Gorged 5/5 (⚠ only above 75% HP) | ×1.10 |
| Conviction 5/5 | ×1.053 |
| Dark Justicar 0/1 | ×1.084 |
| **Improved Cleave 3/3** — bonus term `9+AP×1.0` goes 593→1,305 at AP 584; propagated through LC's own crit ratio (2.00×) and hit/crit split from the log | ×1.110 |

**Combined: ×1.48 → roughly +48% DPS**, projecting the reported **3,600 → ~5,330 DPS** baseline, *if* everything lands at max rank and the Blood Gorged health condition holds. Two things keep this a ceiling: **Dark Justicar and Inevitable Vengeance partially conflict** (Dark Justicar's Judgement burst consumes all 10 SoV stacks, zeroing Inevitable Vengeance's stacking debuff — can't fully bank both on the same GCD), and **The Art of War 3/3 isn't included at all** (still no pinned magnitude), so the real ceiling is higher than 48%, just unquantified past that point.

**Buff/ability layer on top (lower confidence — durations are DBC-confirmed, cooldowns are NOT, so these assume typical WotLK-family cooldown lengths rather than measuring them):**

| Ability | Confirmed magnitude | Rough DPS estimate |
|---|---|---|
| Divine Storm | 110% weapon dmg AoE + heal (sanity-checked against Elric's own Dawn Strike avg, 812/hit — same order of magnitude) | ~4-6%, based on Dawn Strike's own 5.1% share |
| Avenging Wrath | +20% all dmg/heal, 20s duration (confirmed) | ~2% (assumes ~3min CD, unconfirmed) |
| Guardian of Ancient Kings | +15% Holy dmg, 12s duration (confirmed) + resets HotR/Divine Storm/Holy Shock CDs | Not cleanly quantifiable — the CD-reset effect (compounds Hour of Judgement uptime, currently only 13.6% per §11) likely matters more than the flat 15% |
| Bloodlust | +30%/+20% attack/cast speed, 40s duration (confirmed) | ~1-2% (assumes a long ~10min-class CD, unconfirmed) |
| Twisted Mind | Flat +60 SP (not a %), +3% hit (near-worthless), hidden healing penalty | Low single digits |
| Execution Sentence | Magnitude fully unresolved (DBC has no data for it) | Unquantifiable |

**Net picture:** the reliable talent-stack ceiling (~48%) plus a rough **+5-10%** more from Divine Storm/buffs, landing somewhere in the **~55-60%** range as a working estimate — with Execution Sentence and The Art of War as unquantified upside beyond that.

---

## 11. ROTATION (v5)

**🔴 The biggest free gain available: press Judgement and Holy Shock.**

In a ~309-second boss fight the parse logged **3 Judgements and 3 Holy Shocks**. Expected: ~38 and ~50.

This matters because Hammerdin keys on **Paladin-tagged** abilities and its cooldown reduction is what brings Hour of Judgement back. Your top damage buttons — Lightbound Cleave (Warrior), Dawn Strike (Rogue), Whirling Light (Warrior) — feed it nothing. **Hour of Judgement sat at 13.6% uptime while generating 22.1% of total damage.** Doubling that uptime roughly doubles Hammer from the Heavens.

**Priority:**
1. **Seal of Command up wire-to-wire**; **Seal of Vengeance** paired via Twist of Faith
2. **Hour of Judgement** on cooldown — the only burst window
3. **Judgement on cooldown** ← *currently the single largest error*
4. **Holy Shock on cooldown** ← *ditto*
5. **Dawnreaver** on its 4s cooldown (Paladin-tagged)
6. **Whirling Light** on its 10s cooldown
7. Dawn Strike filler → Holy Finish at **5 CP only** (the CP term is quadratic: `(AP+SP) × CP² × 0.02`)
8. **Lightbound Cleave queued off-GCD at all times** — macro onto fillers
9. **Blades of Light only while Hour of Judgement is unavailable** — never during, never when it's close

---

## 12. ASSUMPTION REGISTER

**Resolved:**
- ✅ Holystrike crits on the **spell** table and takes Holy modifiers
- ✅ Righteous Vengeance = 30%, pools on refresh, cannot crit
- ✅ Consecrated Weapon is flat (no SP/AP coefficient)
- ✅ Crit rating = 14.0 per 1%, both schools
- ✅ Sword Specialization works — both clauses
- ✅ Seal parse: SoC + SoV; SoF dead (Fire + excluded from Seals of the Pure)
- ✅ Agi → melee crit only (~32.4/1%); Int → spell crit only (~61/1%)
- ✅ Class tag follows the borrowed-modifier ability
- ✅ Periodic effects cannot crit
- ✅ Blades of Light locks out other abilities and starves Hammerdin
- ✅ **(v6) Lunar Guidance independently confirmed slotted** — matches the v5 hypothesis that it alone (unamped) explains the 5.5% Bonus Damage/Healing gap in §4
- ✅ **(v6) Shadow Strikes, Enhanced Weapon Mastery, Seals of the Pure confirmed rerolled away** since v5, replaced by Accuracy + Glyph of Seal of Command + Glyph of Blood Strike
- ✅ **(v8) Enhanced Weapon Mastery's exclusivity bucket is now a codified Darkmoon server rule** (2026-08-03 patch), upgrading its confidence from tooltip-only to patch-note-confirmed. No verdict change.

**Retracted:**
- ❌ "Int → melee crit ≈ 38/1% CONFIRMED" — contaminated single-item reading
- ❌ "Sword Specialization produces ZERO output"
- ❌ "The Art of War is dead" — cut on the wrong tooltip clause
- ❌ "Consecration is not worth a slot"
- ❌ "Enhanced Weapon Mastery is a protect card" — bucket-blocked by Answered Prayers
- ❌ **(v7) "Avenging Wrath / Guardian of Ancient Kings are substitutes, take the first"** — wrong framing. They're independent cooldowns on separate systems (flat all-damage buff vs. Holy-specific reset-and-buff), not the same functional slot. Even if mutually buff-exclusive (unconfirmed either way), sequential use on two separate cooldowns still beats picking one. Both moved to the chase list (§8).

**Cross-character observation (v7, not a measurement — treat as evidence, not confirmation):**
- Enhanced Weapon Mastery is **live** on another player's comparable Paladin/Hammerdin spec, since his board carries none of the all-damage% exclusivity bucket's other members (no Answered Prayers, Unending Fury, Blessed Weapons, Blood Gorged, or Improved Blood Presence). Same card, opposite verdict from ours purely because of board composition — a clean illustration that "is this card dead" has no fixed answer independent of the rest of the board (primer §2, exclusivity buckets).

**Related external reference (v12, not part of this build):** `builds/shared/synergy_winds-of-winter.md` documents a different player's Titan's Grip Int/AP dual-scaling build encountered 2026-08-03. Two overlapping pieces worth noting for comparison: it runs the same Righteous Vengeance talent (87.7–89.5% uptime, consistent with our own pooling measurement above) and the same Hammerdin talent this build's name comes from. Its core finisher's quadratic-combo-point scaling is the same shape as our own Holy Finish — see primer §1/v12 for the cross-reference. Not a suggested pivot; different stat posture (dual AP+SP vs. our SP-lane separation).

**Still open:**
1. **Is Path of Duality actually active?** *(highest priority)* — **new data point, v10, not a resolution:** a fresh character-panel screenshot shows Bonus Damage 474 vs Bonus Healing 248, a 1.91x gap — much larger than v5's 400/379 (1.06x) and closer to the retracted v3 "x1.75 amp" figure than the "no amp" reading v4 settled on. Could mean the amp is now live (gear/patch change since v5?), or could just mean new gear itemises more flat SP than Int this time. **Still needs the gold-standard test** (crit-source breakdown tooltip, §5 method) before treating this as anything but a prompt to re-check.
2. Hammer from the Heavens' coefficients (hidden sub-spell 282987) — 22.1% of damage
3. Whether the Titan's Grip tax applies to Holystrike's weapon half
4. ~~Answered Prayers' all-damage % (decides Enhanced Weapon Mastery)~~ — **moot as of v6**, Enhanced Weapon Mastery is no longer slotted
5. "Brutal Crusader" on Light's Hope
6. Mental Quickness exclusivity bucket
7. Dark Justicar consume-vs-hold once acquired
8. ~~Accuracy's exact rank~~ — **RESOLVED v10**, confirmed Rank 5/5 via fresh inspect export
9. **(v8, new) Lightbound Cleave proc behavior post-2026-08-03 patch** — see §9 item 10
10. **(v9, new) Lightbound Cleave's total-damage share needs re-measuring once Improved Cleave is acquired** — the corrected `(9+AP)×2.2` formula (v9) predicts a large gain but hasn't been checked against a fresh parse
11. **(v10, new) Is Nurturing Instinct's Agility-scaled healing clause touching anything in this kit at all** (Holy Shock/Holy Finish healing components)? Assumed dead/marginal on tooltip reading alone; not proc-tested.

---

## 13. NEXT SESSION WANTS

- Path verification result folded into the weights
- Post-rotation-fix parse — target Hour of Judgement above 27% uptime
- Gear targets rebuilt around **spell hit → expertise → spell crit**
- Continued chase-list rolling as scrolls accumulate (Combat Expertise, Blood Gorged, Conviction, Dark Justicar, Inevitable Vengeance)
- Dungeon-AoE loadout variant, where Blades of Light and Light's Hammer become correct
- **(v8) Lightbound Cleave dummy re-check** — first item, cheap and directly patch-motivated
