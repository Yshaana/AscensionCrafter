# Project Ascension — "Winds of Winter" Build Reference v1

**What this is:** NOT a live character handoff — this is a reverse-engineered profile of another player's build, met in a dungeon (2026-08-03). Data sources: 2 screenshots (ability/talent board, equipped gear) + 2 combat log parses from that player's own damage breakdown. Pair with `Ascension_Context_Primer.md` for the general rules (class-tag rule, exclusivity buckets, crit-table mechanics) this doc applies but doesn't restate.

**Purpose:** reference material — either for comparing against your own Paladin build, or as a blueprint if you ever want to build this yourself. Not something you own or are actively testing, so confidence tiers matter more than usual here: most of this is tooltip-confirmed math, but the *why does it crit so much* question is still open.

---

## 1. Build identity

**Archetype:** Titan's Grip (dual 2H) Int/AP dual-scaling nuke build. Spec name shown in-game: **"Intellect build."**

Unlike your Paladin build (which separates into an SP-lane and an AP-lane across different abilities), this build's core abilities **scale off both SP and AP simultaneously**, so investing in either stat pays into the same damage. Titan's Grip supplies AP from two 2H weapons; the gear (rings, trinkets, leather int pieces) supplies Int/SP. Both lanes feed the same finisher.

**Core loop:** generate combo points with **Titanic Mutilate** (Rogue *Mutilate*, reskinned), dump them into **Winds of Winter** (Rogue finisher slot, reskinned with Mage *Cone of Cold* modifiers) — a Frost cone nuke whose SP/AP scaling is **quadratic in combo points**, not linear. That's the entire reason this build hits as hard as it does.

---

## 2. Class-tag table (confirmed via `uses X modifiers` clause)

| Card | Borrows from | Real class origin | Confidence |
|---|---|---|---|
| Winds of Winter | Cone of Cold | **Mage** | `inferred_borrowed_modifiers` |
| Titanic Mutilate | Mutilate | **Rogue** | `inferred_borrowed_modifiers` |
| Consecrated Weapon | — (native) | Paladin (same card you run) | native |
| Righteous Vengeance | — (native talent) | Paladin (same talent you run) | native |
| Killing Machine | — (native talent) | Death Knight | native |
| Hammerdin | — (native talent) | Paladin — **you have this slotted too; it's the talent your own build's name comes from** | native |

Practical consequence of the Winds of Winter borrow: any talent that names **Cone of Cold** explicitly (not just "Frost spells" generically) is confirmed to apply. **Improved Cone of Cold** does — it's in his talent list and directly buffs the base ability by name, per the class-tag rule's "named modifiers beat generic wording" practice.

---

## 3. The core nuke — exact formula

**Winds of Winter** (id 274121, Frost school via borrowed Cone of Cold):

```
Damage per cast = flat(b2) × n + (SPFrost × 0.0096) × n² + (AP × 0.00624) × n²
```
where `n` = combo points spent (1–5).

**This is the whole story.** The SP and AP terms are multiplied by `n²`, not `n`. Going from 1 CP to 5 CP doesn't 5× the scaling term — it **25×'s** it. Dumping at 5 CP instead of, say, 3 CP roughly triples the scaling-derived damage. There is no reason this build would ever finish below 5 CP, and the two parses (11–12 casts each) are consistent with a full 5-CP-every-time rotation.

This single mechanic explains the parse dominance: 47.3–55.9% of total damage from one ability across both logs.

**Combo point generation — Titanic Mutilate** (id 271779, borrows *Mutilate*):
- Instant, both weapons, **2 combo points per cast**, +20% damage vs. bleeding targets.
- Two casts = 4 CP; needs one more point from somewhere else (Seal of Command autohit or a filler) to reach 5 before the dump. Not confirmed which — flag if you ever get his full rotation log.

---

## 4. Support layer

| Ability | Formula / effect | Parse share (log1 / log2) |
|---|---|---|
| **Consecrated Weapon** | Flat Holy SP + AP buff, plus per-swing Holy proc scaled to **weapon speed** (slower = more per hit) — same card you run. Titan's Grip's slow 2H weapons synergize well with this. | 13.3% / 10.0% |
| **Righteous Vengeance** | Same talent you run: crits seed a 30%-of-crit-damage Holy DoT. Feeds heavily off Winds of Winter's near-100% crit rate. | 11.8% / 14.0%, 87.7–89.5% uptime |
| **Frozen Orb** | `flat + SP×0.0714 + AP×0.0464` Frost, ticking, AoE, applies a slow. Same dual-scaling logic as the finisher. | 4.7% / 3.0% |
| **Absolute Zero** | `(playerLevel×3 + flat) + AP×0.0085 + SP×0.013` Frost, stacks 5×, stuns at max stacks. Borrows Frost Nova. | 2.6–3.2% / — |
| **Seal of Command** | Standard seal — main hand autos + Paladin melee abilities get a Holy rider, judge deals `0.19×weapon + 0.08×AP + 0.13×SPH`. | minor, folded into melee/unlisted |

---

## 5. Crit rate — confirmed sources, and the open gap

**Confirmed crit contributors:**
- **Killing Machine** (DK talent, in his board): melee abilities have a chance to guarantee the *next Frost spell/ability* crits. Titanic Mutilate is melee → feeds this → Winds of Winter is Frost-tagged → consumes it.
- **Piercing Ice, Arctic Winds, Black Ice, Improved Cone of Cold**: all Frost **damage%** boosts, not crit%. They inflate the number, not the crit rate.

**Ruled out (checked and absent from his talent board):**
- **Shatter** (bonus crit vs. frozen targets) — not slotted.
- **Frostbite / Fingers of Frost** (the classic WotLK freeze→guaranteed-crit chain) — neither is slotted.
- No other talent on his board grants flat crit%.

**⚠ Open gap, not yet resolved:** you pulled the Killing Machine buff data from his log — **9 activations, 60% uptime.** Winds of Winter landed 11 hits (100% crit) in one fight and 12 hits (91.7% crit, i.e. 11 crits) in the other. **9 procs cannot cover 11 crits in either fight, let alone both.** Killing Machine is a real contributor but not the full explanation.

**Leading hypothesis (unconfirmed):** his two trinkets — **Smolderweb's Eye** and **Heart of Wyrmthalak** — are both classic stacking-proc crit-rating trinkets (spell crit on cast / melee crit on hit). Items aren't in the spell export, so this can't be verified from data on hand. **If you want to actually close this:** pull the **Auras** tab from his log and check trinket-proc uptime alongside Killing Machine's — that separates "high baseline crit rating, KM just tops it off" from "something else entirely."

---

## 6. Full observed loadout (as-screenshotted, 2026-08-03)

**Abilities (30/30 slots):**
Trueshot Aura · Heroic Strike · Titan's Grip · Sweeping Strikes · Adrenaline Rush · Frozen Orb · Ice Lance · Deep Freeze · Cold Snap · Ice Block · Arcane Power · Tether Elemental · Stormstrike · Call of the Elements · Shamanistic Rage · Windfury Totem · Seal of Command · Avenging Wrath · Mind Freeze · Icy Touch · Blood Presence · Ray of Frost · Burst of Thorns · Lava Sweep · Malediction · **Titanic Mutilate** · **Absolute Zero** · **Winds of Winter** · **Consecrated Weapon** · Frost Wyrm

**Talents (25/25 slots):**
Combat Potency · Vitality · Relentless Strikes · Focused Attacks · Spell Power · Spell Impact · Ice Floes · Arcane Concentration · **Piercing Ice** · **Improved Cone of Cold** · **Arctic Winds** · Demonic Pact · Elemental Weapons · Enhanced Weapon Mastery · Enhancing Totems · **Righteous Vengeance** · **Black Ice** · Icy Talons · **Killing Machine** · Improved Blood Presence · Blood Gorged · Tundra Stalker · Power Overwhelming · Lava Freeze · Focused Hunt

(Bold = directly load-bearing for the Winds of Winter engine, per §2–5 above. Everything else is either filler, utility, or feeding a rotation piece not captured in the parse — e.g. the Shaman totems, Hunter aura, and DK presence look like leftover multi-class utility rather than core damage.)

**Gear (17 items, item level ~61–64):** Bad Mojo Mask, Animated Chain Necklace, Deadwalker Mantle, Wildheart Vest, Satyrmane Sash, Senior Designer's Pantaloons, Bloodmail Boots, Gallant's Wristguards, Ironweave Gloves, Murmuring Ring, Lavishly Jeweled Ring, **Smolderweb's Eye**, **Heart of Wyrmthalak**, Amy's Blanket, **Hammer of Divine Might** (MH, 2H), **Force of Magma** (OH, 2H), Thoughtblighter (ranged).

Both trinkets are the flagged crit-stacking hypothesis from §5.

---

## 7. Parse data (both fights, player's own damage breakdown)

| Source | Log 1 (%, crit%, hits) | Log 2 (%, crit%, hits) |
|---|---|---|
| Winds of Winter | 47.3%, 100.0%, 11 | 55.9%, 91.7%, 12 |
| Consecrated Holy Weapon | 13.3%, 12.3%, 65 | 10.0%, 21.3%, 47 |
| Righteous Vengeance | 11.8%, 0.0%, 89.5% uptime | 14.0%, 0.0%, 87.7% uptime |
| Frozen Orb | 4.7%, 78.9%, 19 | 3.0%, 52.9%, 17 |
| Heroic Strike | 3.9% | 3.2% |
| Absolute Zero | 3.2%, 18.8%, 16 | 2.6%, 11.1%, 18 |
| Titanic Mutilate (MH) | 2.8%, 0.0%, 21 | 2.5%, 7.7%, 13 |
| Melee (autos) | 2.6%, 18.8%, 16 | 1.5%, — , 11 |
| Titanic Mutilate (OH) | 2.1%, 5.9%, 17 | 2.1%, 23.1%, 13 |
| Lava Sweep | 1.4% | 0.9% |
| Sweeping Strike | 1.2% | — |
| Flame Lash | 1.2%, — , 7 | 1.1%, 33.3%, 6 |
| Firebolt | 0.9% | 0.4% |
| Seal of Command | — | 0.5%, 33.3%, 3 |

---

## 8. Test queue (if you ever chase this build)

1. **Trinket proc identification** — read live tooltips on Smolderweb's Eye / Heart of Wyrmthalak. Settles §5's open gap.
2. **Auras tab pull** — Killing Machine uptime vs. trinket-proc uptime, same fight. Cheapest way to close the crit-source question without new tooltips.
3. **Third CP generator** — what fills 4→5 combo points before the Winds of Winter dump. Seal of Command autohit is the obvious guess but unconfirmed.
4. **Does Winds of Winter split damage across >3 targets?** Some Cone-of-Cold-borrowing entries carry that clause, this tooltip pull didn't show it explicitly — don't assume either way without a multi-target parse.
5. **Titan's Grip physical penalty (`$S3%`)** — unresolved placeholder in the export, same hidden-magnitude problem your own primer already tracks for other cards. Doesn't matter much here since the core nuke doesn't scale off weapon damage, but worth knowing if you ever price Titanic Mutilate's contribution.

---

## 9. Assumption register

**Confirmed (tooltip-sourced):**
- ✅ Winds of Winter's quadratic CP scaling formula, exact coefficients
- ✅ Titanic Mutilate = 2 CP/cast, borrows Mutilate (Rogue)
- ✅ Killing Machine's mechanic (melee → guaranteed next Frost crit)
- ✅ Shatter and Frostbite/Fingers of Frost are **not** on his talent board — ruled out as crit explanations
- ✅ Improved Cone of Cold buffs Winds of Winter by name (class-tag rule, named modifier)

**Unconfirmed / open:**
- ❓ Full explanation for 91.7–100% Winds of Winter crit rate — Killing Machine's 9 procs don't cover it alone
- ❓ Trinket proc mechanics (Smolderweb's Eye, Heart of Wyrmthalak) — items not in spell export, needs live tooltip
- ❓ Whether Winds of Winter splits damage past 3 targets
- ❓ 5th combo point source

**Not applicable to your own build:** this is a different stat posture entirely (dual AP+SP scaling vs. your SP-primary lane separation) — noted for comparison, not as a suggested pivot. The two overlapping pieces (Consecrated Weapon, Righteous Vengeance, and the Hammerdin talent itself) are already core to what you're running.
