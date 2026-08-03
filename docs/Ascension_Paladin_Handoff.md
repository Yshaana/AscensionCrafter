# Project Ascension — Paladin Build Handoff (v7)

**Purpose:** Continue work on my Ascension (WoW private server) Paladin character. **Classless server, Season 10, Wildcard mode.** Pair this with `Ascension_Context_Primer.md` (v9) and `ascension_index.db` (queryable spell/card index — see primer §2a).

**Realm:** Darkmoon (classless seasonal wildcard).

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
| Lightbound Cleave | Cleave | Warrior | **No — confirmed** |
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

**Action:** confirm the active Path in-game. Path switching is free and instant, so this may simply be the wrong path selected. If Duality *is* active and neither clause fires, it's a bug worth reporting.

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

This is why spell crit dominates the weights — every crit seeds a DoT on top.

### ✅ Confirmed magnitudes (live tooltips)

| Card | Magnitude |
|---|---|
| Titan's Grip | **Physical damage dealt −10%** |
| Vengeance (Paladin r3) | **3% per stack, 3 stacks, 30s** → 9% Physical + Holy |
| Blood Gorged | **+10% damage above 75% health, +10% armour ignore** |
| Deadliness r5 | **+10% attack power** |
| Enhanced Weapon Mastery | +4% all damage — **⚠ does not stack with Answered Prayers, Unending Fury or Blessed Weapons; highest only** |
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

**⚠ Titan's Grip is closer than "premise card" implies.** It costs −10% physical *and* +19% white miss. Its wins are Whirling Light (only ability using both weapons) and roughly 1.6× the CHW proc rate. Dropping it would free an ability guarantee slot and re-enable Sword Spec's +40% single-2H rider. Worth an actual A/B parse.

---

## 7. FINAL TALENT BOARD (v6 — confirmed live via inspect export, 2026-08-02)

### Slotted
```
Answered Prayers 5/5        Holy Focus 5/5              Holy Power 5/5
Holy Specialization 5/5     Twin Disciplines 5/5        Sword Specialization 5/5
Dual Wield Specialization 5/5   Deadliness 5/5          Lunar Guidance 3/3
Judgements of the Wise 3/3  Judgements of the Pure 3/3  Righteous Vengeance 3/3
Wrecking Crew 3/3 (locked)  Vengeance 2/3                Flurry 2/3
Mental Quickness 4/5        Fanaticism 1/3               Spellblade 1/3
Hammerdin 1/1                Purification By Light 1/1   Righteous Zealot 1/1
Twist of Faith 1/1           Accuracy ?/?
```
**Plus two glyph-type cards occupying the same board:** Glyph of Seal of Command (deliberate, temporary), Glyph of Blood Strike (filler, unevaluated).

**Since v5:** Shadow Strikes, Enhanced Weapon Mastery, and Seals of the Pure are all confirmed gone — replaced by Accuracy and the two glyphs above. Rank on Accuracy not yet read live; flag for confirmation next parse.

### 🔴 Reroll targets (current)
1. **Glyph of Blood Strike** — confirmed filler, "whatever I ended up with when I ran out of rerolls." No analysis needed, straightforward reroll-first.
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
| 7 | Improved Cleave 3/3 | scales only LC's flat 62 — decays with gear | partial |

**Total gap ≈ 40% damage**, concentrated in six cards. The two 1/1s are the cheapest acquisitions (a hit is a complete hit). None of these six appear in the v6 live export — chase list is unchanged, still fully outstanding.

### ⚡ Execution Sentence cluster — status update
v5 noted three slotted talents supporting Execution Sentence: Seals of the Pure, Judgements of the Pure, and Fanaticism. **Seals of the Pure is now gone**, dropping this to two. Judgements of the Pure and Fanaticism still support it. Re-evaluate whether an Execution Sentence ability slot is still worth it with one fewer multiplier behind it.

---

## 8. ABILITY tags

### Protect
Titan's Grip · Consecrated Weapon · Hour of Judgement · Judgement of the Three Hammers · Lightbound Cleave · Dawnreaver · Dawn Strike · **Judgement** · **Holy Shock** · Whirling Light · **Seal of Command** · **Seal of Vengeance** · Consecration

### Chase
1. **Divine Storm** — the outstanding **Paladin-tagged** weapon-damage GCD; directly compresses Hour of Judgement. *(External sighting, v7: another player's Paladin/Hammerdin spec runs this live — supporting evidence it's playable, not a substitute for our own parse.)*
2. **Execution Sentence** — two talents now support it (Judgements of the Pure + Fanaticism; Seals of the Pure dropped off, §7). *(External sighting, v7: another player's Paladin/Hammerdin spec runs this live alongside the same two supporting talents.)*
3. **Avenging Wrath AND Guardian of Ancient Kings — both, independently. (Corrected v7, see retraction in §12.)** They aren't redundant: Guardian of Ancient Kings resets/discounts Hammer of the Righteous, Divine Storm, and Holy Shock plus a Holy damage buff; Avenging Wrath is a flat all-damage/healing cooldown on a separate timer. Even under a worst-case reading of their "does not stack with similar effects" clauses, that only blocks simultaneous *buff* uptime, not sequential use on two independent cooldowns — alternating them still nets more total burst-window uptime across a fight than picking one.
4. **Twisted Mind** — SP still good, but its hit rider is now worthless (melee capped)
5. Divine Protection · Bloodlust

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
| **Hammer from the Heavens, JotTH** | **~29%** | ❓ **summoned procs — UNRESOLVED** |

**Confirmed spell-hit-gated damage: ~5.4%.** Even at full raid tier with zero spell hit that's `17% × 5.4% ≈ 0.9%` of damage.

**Second reason it doesn't apply:** the 96 figure is the cap vs a **+3-level raid boss**. Spell miss is ~4% vs equal level, ~5% at +1, ~6% at +2, and only jumps to 17% at +3. At 57 rating the player is **already effectively capped for all dungeon content** — which is exactly why the parses show no misses.

**Expertise, same error.** Dodge does apply to melee abilities regardless of crit table, but the 0.80 figure assumed a large dodge-exposed share. It has not been verified that Lightbound Cleave is actually being dodged. Held provisionally at 0.30 pending the check below.

**The one unknown that could reverse this:** **Hammer from the Heavens is 22.1% of damage** and it is not known whether summoned procs roll a hit check. If they do, raid-tier Hit Rating rises to ~1.2. If they don't, it stays near zero permanently.

**Test (one click, Details! → click spell name → Miss/Dodge/Parry/Resist breakdown):**
1. **Hammer from the Heavens** (78 hits) — any Miss count? *Decides the whole question.*
2. **Consecrated Holy Weapon** (82 hits) — same question, second-largest source
3. **Judgement of the Three Hammers** (23 hits) — do summoned hammers roll?
4. **Lightbound Cleave** (21 hits) — check **Dodge/Parry**, validates the expertise weight independently

**Off-hand hit rating is worth 0 regardless** — 57/220 is unreachable at this tier; treat off-hand white swings as nonexistent.

**Two caveats:**
- **Hammer from the Heavens is 22.1% of damage with unknown coefficients** (hidden sub-spell). Its composition is assumed 30% SP / 30% AP / 40% flat. If it's mostly flat, SP and AP weights drop and spell crit's dominance grows further.
- **SP ≈ AP at 1.01 vs 1.00 only because the ×1.75 amp isn't applying.** Restore it and SP becomes the clear best non-crit stat.

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

**Retracted:**
- ❌ "Int → melee crit ≈ 38/1% CONFIRMED" — contaminated single-item reading
- ❌ "Sword Specialization produces ZERO output"
- ❌ "The Art of War is dead" — cut on the wrong tooltip clause
- ❌ "Consecration is not worth a slot"
- ❌ "Enhanced Weapon Mastery is a protect card" — bucket-blocked by Answered Prayers
- ❌ **(v7) "Avenging Wrath / Guardian of Ancient Kings are substitutes, take the first"** — wrong framing. They're independent cooldowns on separate systems (flat all-damage buff vs. Holy-specific reset-and-buff), not the same functional slot. Even if mutually buff-exclusive (unconfirmed either way), sequential use on two separate cooldowns still beats picking one. Both moved to the chase list (§8).

**Cross-character observation (v7, not a measurement — treat as evidence, not confirmation):**
- Enhanced Weapon Mastery is **live** on another player's comparable Paladin/Hammerdin spec, since his board carries none of the all-damage% exclusivity bucket's other members (no Answered Prayers, Unending Fury, Blessed Weapons, Blood Gorged, or Improved Blood Presence). Same card, opposite verdict from ours purely because of board composition — a clean illustration that "is this card dead" has no fixed answer independent of the rest of the board (primer §2, exclusivity buckets).

**Still open:**
1. **Is Path of Duality actually active?** *(highest priority)*
2. Hammer from the Heavens' coefficients (hidden sub-spell 282987) — 22.1% of damage
3. Whether the Titan's Grip tax applies to Holystrike's weapon half
4. ~~Answered Prayers' all-damage % (decides Enhanced Weapon Mastery)~~ — **moot as of v6**, Enhanced Weapon Mastery is no longer slotted
5. "Brutal Crusader" on Light's Hope
6. Mental Quickness exclusivity bucket
7. Dark Justicar consume-vs-hold once acquired
8. **(v6) Accuracy's exact rank** — not yet read from a live tooltip

---

## 13. NEXT SESSION WANTS

- Path verification result folded into the weights
- Post-rotation-fix parse — target Hour of Judgement above 27% uptime
- Gear targets rebuilt around **spell hit → expertise → spell crit**
- Continued chase-list rolling as scrolls accumulate (Combat Expertise, Blood Gorged, Conviction, Dark Justicar, Inevitable Vengeance)
- Dungeon-AoE loadout variant, where Blades of Light and Light's Hammer become correct
