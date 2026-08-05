# Project Ascension — Portable Multiplier Packages v1

**What this is:** NOT a single scouted character — this is a cross-character pattern found by scanning 37 total external players (25-man 404-guild roster, report 74, Hakkar; plus a top-25 ZG leaderboard cross-check and 12 fresh characters from two other guilds — Mouse and Nelf) for talent/ability frequency. Data sources: `combatants-roster` and `armory/character` API endpoints on darkmoon.ascensionlogs.gg, which return fully resolved talent/ability names and (critically) resolved `per_rank_text` tooltips with real numbers, not placeholder `$s1`-style export text.

**Purpose:** three separate portable "packages" — small, cheap, class-agnostic groups of talents/abilities that show up disproportionately often across many different players' builds regardless of their main archetype, because the wording is generic enough to apply to anyone in classless mode. None of these are yet tested on our own character. Treat as a chase-list candidate, not a confirmed personal DPS gain.

---

## Package 1: The Demon Package

**Frequency (n=37 total sampled across two sessions):** Demonic Tactics 18/25 → 30/37 combined once cross-referenced; Demonic Pact ~10/25; Master Demonologist ~9/25; Demonic Knowledge only 2/25 (rare specialist layer).

**Core three (near-universal among any character running a demon at all, n=12 demon-pet subset):**

| Talent | Frequency (n=12) | Resolved effect (live tooltip, max rank) |
|---|---|---|
| **Demonic Tactics** | 12/12 (100%) | +10% melee **and** spell crit, for you **and** your active demon — explicitly includes Enslave Demon, not just a Summoned pet |
| **Demonic Pact** | 10/12 (83%) | Flat **+10% spell damage done**, unconditional. Also: pet's spell crits proc a raid-wide spell power buff (5% of your Spell Damage, 45s, 20s CD) — **this raid-buff clause explicitly excludes Enslaved demons**, Summoned only |
| **Master Demonologist** | 8/12 (67%) | Per-pet-type bonus. For **Felguard and Enslaved Demons specifically: +5% all damage done, -5% damage taken**, flat and unconditional |

**Optional specialist layer (rare, n=2/12):**

**Demonic Knowledge** (rank 3, resolved tooltip): *"Increases your spell damage by an amount equal to 12% of the total of your active demon's Stamina plus Intellect."* Requires **Enslave Demon** (ability) to tame a wild demon NPC with a large native Stat budget, since the bonus reads the demon's own stats, not the summoned-pet baseline. Best candidate identified so far (unconfirmed, no live test yet): **level 60 Elite "Dread Lord"** (Nathrezim family, Ascension DB npc=475221) — 15,291 HP vs. 3,495 HP for the non-elite named unique of the same family/level, and a caster-flavored ability kit (Mind Blast, Shadow Shock, Sleep) implying a real Intellect budget, unlike pure-melee demon families (e.g. Doomguard). Location: Blasted Lands, Tainted Scar (canonical vanilla spawn for this family; unconfirmed on Ascension's own spawn tables).

**Requires (ability):** Enslave Demon or a Summon-type demon ability, cost varies by which tier you pursue.

**Bottom line:** the cheap core-three tier is unconditional and cross-class-portable — no pet-species hunting required, just keep any demon active. The Demonic Knowledge layer needs a real farming/testing trip and is not part of the "everyone does this" pattern.

---

## Package 2: DK Disease Multiplier Package

**Frequency:** Tundra Stalker 6/25, Rage of Rivendare 4/25 (usually paired with Tundra Stalker), self-applied via Icy Touch + Plague Strike (both DK abilities, cheap GCDs).

| Talent | Resolved effect (live tooltip, max rank 5/5) |
|---|---|
| **Tundra Stalker** | +15% all damage (spells **and** abilities) to targets infected with your Frost Fever, +5 expertise |
| **Rage of Rivendare** | +10% all damage (spells **and** abilities) to targets infected with your Blood Plague, +5 expertise |

Both diseases self-applied via **Icy Touch** (Frost Fever) and **Plague Strike** (Blood Plague) — two cheap off-rotation GCDs, long disease duration, near-permanent uptime on a boss-length fight. Stacking both = **+25% all damage + 10 expertise** on the diseased target for two talent investments (10 points total) and two throwaway button presses. Neither talent is DK-gated in its wording — "your spells and abilities" applies to your full kit, same generic-wording pattern as Package 1.

**Not yet tested on our own build.**

**Update (2026-08-04, from `wip_winds-of-winter-frostblade.md` v9 session):** found a build-specific route to the Frost Fever half that doesn't require Icy Touch — **Glacial Spike** (284177, owned) applies Frost Fever itself while also being a real SP+AP-scaling Frost nuke in the Cone of Cold family (same borrowed-modifier class as Winds of Winter). Checked whether any of the 5 scouted Winds of Winter players (Gunju/Titanus/Kcdq/Blasted/Tdoctor) had actually combined a Frost Fever source with Tundra Stalker: **nobody has.** Gunju runs Glacial Spike but not Tundra Stalker; Kcdq runs Tundra Stalker but no Frost Fever source at all (likely dead weight on his own board). This package remains a real, tooltip-grounded prediction, not an empirically-observed pattern — see `seed_confirmed.py`'s `frost_fever_synergy_not_actually_combined_by_anyone`.

---

## Package 3: Blessing of Kings

**Frequency:** 9/25 (36%) — lower adoption than expected given how cheap it is.

**Resolved tooltip (live API, single-rank ability):** *"Places a Blessing on the friendly target, increasing total stats by 10% for 30 min."*

Flat **+10% to all five stats** (Str/Agi/Stam/Int/Spirit combined). One ability slot, no talent investment, no proc conditions, 30-min duration (easily maintained). This is the cheapest item on the whole list. Worth checking whether it's currently on our own ability bar — it isn't listed among the tagged abilities in the current build handoff, and if genuinely absent, this is likely the single easiest win of the three packages.

---

## Package 4: The Cleave Kit (owner-proposed 2026-08-05, session `2d`)

**Two slots: any `-bound Cleave` ability + Improved Cleave 3/3.** Proposed by the
owner after the `2d` isolation tests; unlike Packages 1–3 this one carries
same-day measurements on our own character.

| Piece | What it does | Evidence |
|---|---|---|
| Lightbound Cleave (R5 at 60) | 62 flat + 65% MH weapon damage, Holystrike, **off-GCD next-swing queue** — stacks on top of any GCD rotation | 53 isolated single-target hits, 2026-08-05: avg 493 pre-resist unbuffed (MH 415–518 @ 3.57) |
| Improved Cleave 3/3 | +120% to **all** effects (`SPELLMOD_ALL_EFFECTS`, class mask byte-identical to LC's, family 4) → **×2.20** | numeric-field proof, session `2c`; not yet parse-verified on our board (card not owned) |

**Rough value at our unbuffed stats:** LC nets ~+133 per MH swing over the auto
it replaces (auto avg 360); with Improved Cleave ×2.20 → ~1,085 per LC, net
**~+725 per swing ≈ +200 DPS single-target for two slots**, scaling with weapon
damage and crit (percentage-based, gear-proof).

**Why it travels (measured 2026-08-05, the key property):** LC is
**engine-inert** — proc-tested feeding **zero** Hammerdin, zero Purification By
Light, zero Seal of Command riders. It needs nothing from the host build and
takes nothing from it: no class-tag dependency, no intake conflict.

**The school roster (owner's point, 2026-08-05, verified from numeric fields):**
Ascension ships a Cleave in every magic school, all in the current pool, all
with the same rank ladder (level-60 rank = SpellLevel 56), and **all eight carry
the byte-identical family-4 class mask `[4194304,0,0]` — Improved Cleave's
×2.20 provably reaches every one:**

| Variant | School | Card id (R5 id) |
|---|---|---|
| Cleave | Physical | 845 |
| Lightbound Cleave | Holystrike | 907300 (907304) |
| Voidbound Cleave | Shadowstrike | 907280 (907284) |
| Flamebound Cleave | Firestrike | 907320 (907324) |
| Frostbound Cleave | Froststrike | 907340 (907344) |
| Stormbound Cleave | Stormstrike | 907360 (907364) |
| Spellbound Cleave | Spellstrike | 907260 (907264) |
| Fel Cleave | Shadowflame | 276066 (276087) |

Each `-bound` variant is a true hybrid (school mask = Physical + its school), so
per the primer's hybrid rules it **double-dips the host's Physical AND
school-specific modifier stacks and crits on the spell table** (measured for
Holystrike; assumed for siblings pending a parse). That is the kit's third
scaling lever after weapon damage and Improved Cleave: a host with a big school
stack (as with our Holy pile) or heavy spell crit gets substantially more than
the baseline +200 DPS estimate — pick the variant matching the tallest stack.

**Costs and fit conditions:**
1. **Consumes the next MH swing** — hosts whose autos carry rider economies
   (seal riders keyed to "main hand auto attacks", auto-keyed imbue procs) lose
   those procs on converted swings. Measured 2026-08-05: SoC riders fired on
   white swings only, never on LC swings.
2. Occupies *the* next-swing queue slot — mutually exclusive with the Heroic
   Strike family.
3. The 65% weapon half is Physical: armor-mitigated, and pays Titan's Grip's
   −10% where the host runs TG. Favors one hard-hitting 2H.
4. Improved Cleave is a 3-rank talent (+40%/rank linear) — a partial roll still
   pays ×1.4/×1.8. The Cleave ability itself is a single-rank ability card
   (spell rank is level-set — no rank risk).
5. Mana per queued swing.

**Confidence:** `internal_test` for LC's behavior and formula;
`confirmed` (numeric fields) for the mask reach; the ×2.20 multiplier itself is
unverified on our own board until Improved Cleave is acquired — §7 chase #1=.

---

## Assumption register

**Confirmed (live resolved tooltip text, not export placeholders):**
- ✅ All percentage/effect values above, pulled directly from `per_rank_text` on the armory API — same ground-truth tier as an in-game tooltip screenshot.
- ✅ Frequency counts, pulled from `combatants-roster` full raid data plus individual `armory/character` calls, n=37 total unique characters across 3 guilds (404, Mouse, Nelf).

**Unconfirmed / open:**
- ❓ Whether any of these three packages actually apply to, or stack cleanly with, our own Hammerdin talent board (bucket-exclusivity checks not yet run).
- ❓ Demonic Knowledge's real payoff — needs an actual Enslave Demon + character-sheet-before/after test, no shortcut from external data.
- ❓ Whether Demonic Knowledge specifically works on Enslaved (not just Summoned) demons — inferred likely-yes from Demonic Tactics/Master Demonologist explicitly listing Enslave Demon while Demonic Pact explicitly excludes it, but Demonic Knowledge's own tooltip is silent on the distinction. Named-lists-beat-generic-wording rule (primer §5) says don't assume — verify live.

**Retracted this session:** an apparent contradiction (4 characters with both Enhanced Weapon Mastery and Answered Prayers/Unending Fury simultaneously, seemingly violating primer's documented exclusivity-bucket rule) was investigated and closed — all 4 captures predate the Aug 3 patch that introduced the exclusivity rule. Not a data error, not a primer error, just a stale pre-patch snapshot. No confirmed_facts change needed.

**Not applicable without further work:** none of these three packages have been priced against our own board's existing bucket exclusivities (Answered Prayers etc.) — do that check before treating any as a slot-in recommendation.
