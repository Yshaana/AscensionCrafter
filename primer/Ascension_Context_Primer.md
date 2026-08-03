# Project Ascension — Systems Primer v12 (Context for Claude)

This file explains how **Project Ascension** works so you can reason about build decisions. Background context, not a build — pair with a build handoff. Ascension is a heavily customized WoW private server; **treat in-game tooltip coefficients and mechanics as source of truth over retail/classic WoW assumptions**.

**v12 changelog (2026-08-03):** **Repo reorganized into three build tiers with a filename-prefix convention** (survives flat project-knowledge mounts, not just folders):
- `build_*` → `builds/my-builds/` — locked, authoritative, iterable (e.g. `build_paladin-hammerdin.md`, renamed from `Ascension_Paladin_Handoff.md`)
- `wip_*` → `builds/wip/` — theorycraft in progress, not yet a committed board
- `synergy_*` → `builds/shared/` — external engine/scaling reference extracts only, **not** full gear/talent dumps (e.g. `synergy_winds-of-winter.md`, `synergy_fel-infused-dagger.md`)

File paths changed throughout: this primer and `INDEX_GUIDE.md` now live in `primer/`; `build_index.py`, `seed_confirmed.py`, `seed_borrowed_modifiers.py`, `build_dbc_index.py`, `tooltip_diff_report.py`, `decode_inspect_export.py`, `class_dictionary.py`, `spell-export.json`, and `Cards.txt` now live in `index/`; build docs live in `builds/` per the prefix convention above. See `INDEX_GUIDE.md` for the full path/schema reference.

New `index/seed_synergies.py` adds a `shared_synergies` table — same append-only, confidence-tiered pattern as `confirmed_facts`, but for engines observed on **other players'** builds rather than facts about our own. Seeded from `builds/shared/synergy_winds-of-winter.md` (2026-08-03 dungeon encounter, another player's Titan's Grip Int/AP build): a quadratic combo-point-scaling finisher (Winds of Winter, `n²` CP term, tooltip-confirmed) fed by a borrowed-tag combo generator (Titanic Mutilate), plus an open crit-source question (Killing Machine's measured procs don't cover the observed crit rate — see the linked file §5). Logged as 4 `shared_synergies` rows. **Check `shared_synergies` (via `seed_synergies.py`) before treating an external build's engine as novel** — it may already be logged with a confidence tier and linked file.

`ascension_index.db` moves to `index/ascension_index.db` and stays gitignored/ephemeral, continuing the v10 policy below — nothing changes about *when* to rebuild it. **New wrinkle:** `spell_dbc_raw`/`dbc_*` (from `build_dbc_index.py`) can't be regenerated from `spell-export.json` alone — they require the actual client files plus a locally-built StormLib, not available in every session. `build_dbc_index.py` now also writes `index/dbc-extract.json` (spell_dbc_raw + support tables + resolved hidden-formula `spell_scaling` rows), which **does** get committed, so that data survives even in a session that can't re-run the extraction.

**v11 changelog (2026-08-03):** DBC extraction pipeline (`build_dbc_index.py`) ran a full tooltip diff of every catalog spell's raw client description against its export tooltip (3,061 spells). Surfaced the `uses X modifiers` class-tag mechanism catalog-wide (389 instances, most already visible in exports too) and one genuine miss: **Fel Cleave** (id 276066) — its raw DBC description reads *"This uses Cleave modifiers"*, but the export tooltip omits that clause entirely, same shape as the Enhanced Weapon Mastery omission (§2). Seeded to `seed_confirmed.py`: **Warrior**-tagged (`confirmed_class_tag_rule`), Shadowflame school, **not part of the current Paladin kit** — logged for a possible future leveling/alt build, see `builds/wip/wip_fel-cleave-leveling.md`. New §4 class-tag table row.

**v10 changelog (2026-08-03):** **`ascension_index.db` binary uploads are unreliable — diagnosed and worked around.** Re-uploaded copies of the `.db` repeatedly failed to open (`sqlite3.DatabaseError: file is not a database`); byte inspection showed the SQLite header's null terminator arriving as `\x10` instead of `\x00` — a null-byte mangling in the upload/mount pipeline, reproduced on a fresh re-upload, so it's not a bad export on the player's end. **Fix: stop treating the `.db` as a source to upload/maintain at all.** `build_index.py` → `seed_borrowed_modifiers.py` → `seed_confirmed.py` all read plain-text sources (`spell-export.json`, `Cards.txt`, `class_dictionary.py`, the seed scripts themselves) that mount cleanly with no corruption — running this three-step pipeline reconstructs the full index **including all seeded `confirmed_facts` and `class_origin` rows** from scratch, verified byte-for-byte equivalent (3,061 spells / 393 class_origin rows / 41 confirmed_facts, matching pre-corruption counts). §2a and §5 updated accordingly.

**v9 changelog (2026-08-02, late night):** Formalized `decode_inspect_export.py` and its format spec into `INDEX_GUIDE.md` — a third-party site (inspects.nie.one) exposes a live in-game inspect as a URL fragment (base-36 spec data + hex-encoded gear), now fully decodable for any character, not just your own. Full format spec, known gaps, and usage live in `INDEX_GUIDE.md`; this is a live external data source, separate from the offline `ascension_index.db`.

**v8 changelog (2026-08-02, late night):** New §5 practice from cross-referencing a live in-game inspect/WeakAura export (55 spell IDs) against the catalog for the Paladin build: unresolved IDs are very likely different ranks of known cards, not missing content — resolved 5/5 unmatched IDs this way, each landing exactly on a card already known to be held at partial rank (see `Ascension_Paladin_Handoff.md` v6 for the full case study).

**v7 changelog (2026-08-02, later night):** Live in-game tooltip resolved Molten Earth's hidden formula (`60 + (SP+AP)×0.12` Fire dmg/tick, 8 ticks, uses **Fire Nova** modifiers) and its full modifier list. Two consequences: **(1) class-tag rule proof case #2** — Molten Earth is Lava-Lash-*triggered* but Fire-Nova-*modified*, meaning talents that buff Lava Lash (Elemental Fusion, Lava Flows) do **NOT** buff Molten Earth, exactly the same trap as Lightbound Cleave/Cleave in §4. A same-session recommendation was made and then retracted on this basis — logged as a case study in §4. **(2) periodic-crit rule downgraded further** — Molten Earth is a confirmed textbook aura-tick DoT (not the "instant-pulse ground object" the v6 theory guessed at) and still crits, while Righteous Vengeance (same DoT structure) doesn't. No structural predictor found; crit-capability appears to be flagged per-spell server-side. New §1 note: **AP+SP dual scaling is not exclusive to named hybrid `-strike` schools** — pure-school spells (Molten Earth, Cataclysmic Sundering) can carry both coefficients too. New §2 **weapon-imbue exclusivity** entry. New §5 practice: prefer talents that name an effect **verbatim** over ones matched by generic school wording.

**v6 changelog (2026-08-02, night):** Two additions from group-parse observation (unrelated dagger/hybrid character, third-party parse). **Periodic-no-crit rule scoped**: Molten Earth (Shaman ground pulse) parsed 40.7% crit over 575 hits, contradicting a blanket "ground effects can't crit" reading — rule now scoped to aura-tick DoTs specifically, with Molten Earth flagged as a likely repeating-instant-pulse exception pending a live-tooltip mechanism check. **New fact**: no-ICD per-hit procs (confirmed: Fel Infused Weapon) scale directly with attack frequency rather than weapon damage, reported up to ~30% of total DPS for hyper-fast dual-wield attackers — a concrete reason to prioritize weapon speed over weapon DPS in builds carrying this kind of card.

**v5 changelog (2026-08-02, evening):** Both exports are now indexed in a queryable SQLite database, `ascension_index.db` (see §2a). It's a **derived cache, not a new source of truth** — this doc and the handoff remain authoritative. New rule in §5: check the index before re-parsing raw JSON, and keep `confirmed_facts` in sync whenever a verdict here changes.

**v4 changelog (2026-08-02, evening):** **Hybrid crit-table question RESOLVED** — Holystrike crits on the **spell** table and takes Holy modifiers; the under-review flag is removed and the method that settled it is written up as a reusable practice (§5). **Duality's measured claims downgraded** — neither the SP amp nor the cross-crit conversions were visible on a live sheet; v3's Int→melee crit measurement retracted as contaminated. New sections on **exclusivity buckets**, **channelled lockout abilities as engine poison**, and **engine intake tags**. New practice: **export tooltips can be incomplete — live reads outrank them.**

---

## 1. What Project Ascension is

- A **WoW private server** on a **3.3.5 (WotLK) client base**; content/itemization/level caps vary by season.
- **Classless mode:** kits are assembled from **skill cards** (abilities) and **talent cards** drawn from every class plus custom Ascension-only and **Conquest of Azeroth (CoA)** cards (spells from Ascension's custom-class project — e.g. Primalist, Sun Cleric, Felsworn — obtainable as regular cards).
- Real constraints: **weapon/armor proficiency, resource type, form/stance requirements, card availability** — not class.
- Combat engine stays 3.3.5-based regardless of content era.

### Combat-engine defaults (3.3.5 base, verify per season)
- **Crit rating conversion: 14.0 rating per 1%** — *measured, identical for melee and spell* (393 rating → 28.07%; 164 → 11.71%).
- Special-attack (yellow) hit cap vs raid boss: **8%**. Dual-wield **white** attacks carry an additional **+19% miss** — the DW white cap is effectively unreachable at low tiers, so **auto-attacks in a dual-wield build may be near-worthless** (measured: 4.2% of damage, 37 landed swings in 309s).
- Expertise dodge cap: **26**.
- **Ground/periodic effects generally cannot crit** — *confirmed repeatedly for aura-tick DoTs* (PBL ground 0%/32 ticks; Righteous Vengeance 0% over 4 parses).
  **⚠ Confirmed exception, mechanism theory RETRACTED (v7):** Molten Earth's live tooltip reads *"Burns enemies in the area, dealing 60 + (SP+AP)×0.12 Fire damage every second for 8 sec. Uses Fire Nova modifiers."* That's a textbook aura-tick DoT — structurally identical to Righteous Vengeance's *"30% crit damage over 8s as Holy DoT."* Yet Molten Earth parses 40.7% crit over 575 hits while Righteous Vengeance parses 0% over 4 parses. **The v6 "aura-tick vs. instant-pulse ground object" theory does not survive this — Molten Earth is a real aura tick and still crits.** No structural predictor identified yet; crit-capability looks like a **per-spell server-side flag**, not something derivable from whether an effect is periodic/ground/aura. **Practice going forward: verify crit-capability per ability from a parse, never infer it from the tooltip's structure.**
- **⚠ No-ICD per-hit procs scale with attack frequency, not weapon damage (v6).** Fel Infused Weapon's tooltip has no internal cooldown: *"each auto attack and melee ability causes [flat + AP×0.05 + SP×0.05] Shadowflame damage."* That's a guaranteed trigger on every landed hit, not a proc chance. Reported in group parses at up to **~30% of total DPS** for hyper-fast dual-wield attackers (fastest daggers in the game, doubled swing count vs. a single slower weapon). **Practical consequence:** when a build carries a card like this, weapon *speed* can outweigh weapon *DPS* — always check whether a per-hit effect has an ICD before assuming more frequent smaller hits dilute rather than compound it.
- **Holy is unresistable** — Spell Penetration worthless against it.
- Base-game stat→crit conversions (Agi→melee, Int→spell) are live. **Do not assume Path grants stack on top without verifying on the character sheet** (see §3).

### Hybrid damage schools
Custom hybrid schools exist (Holystrike, Holyfire, Shadowflame, Firestrike, Froststrike, Shadowstrike, Spellstrike, Stormstrike-as-school). Rules:

- Hybrid abilities have **two damage components with separate scaling**: a physical weapon-damage half (armor-mitigated, physical modifiers) and a magic school half (flat/SP-scaled, school modifiers). They **double-dip modifiers from both component schools**.
- Hybrid abilities are **NOT classified as Spells** — "requires a Holy Spell" triggers/gates do NOT fire from Holystrike. *(This is separate from the school question below: Holystrike takes Holy* modifiers *but is not a* Spell *for gating purposes.)*
- Pure-school direct spells use the **spell crit table** — *confirmed*.
- ✅ **RESOLVED (was under review in v2/v3): hybrid strikes crit on the SPELL table, not the melee table.** Measured against a sheet showing melee 21.76% / spell 18.95% plus a large Holy-specific crit stack:

  | Source | School | Observed crit |
  |---|---|---|
  | Consecrated Holy Weapon | Holy | 39.0% |
  | Lightbound Cleave | **Holystrike** | **38.1%** |
  | Dawn Strike | **Holystrike** | **33.3%** |
  | Sword Specialization | Physical | 20.0% |
  | Melee autos | Physical | 16.2% |

  Holystrike tracks the Holy sources, not the physical ones. **Practical consequence: in a hybrid build, spell crit rating can be worth several times melee crit rating** — check the exposure split before writing stat weights.

- **Crit table and hit table are separate questions.** Holystrike critting on the spell table does not establish that it uses spell hit. Verify independently.
- **⚠ AP+SP dual scaling is NOT exclusive to the named hybrid `-strike` schools (v7).** Molten Earth (`60 + (SP+AP)×0.12`/tick) is a **pure Fire** spell, not Firestrike — yet mixes both coefficients same as the named hybrids. Cataclysmic Sundering does the same on a pure-Fire ground patch. **Don't use "is this a `-strike` school" as a proxy for "does this scale off both AP and SP" — check the raw tooltip coefficients directly, every time.**

---

## 2. The Card system

Everything slottable is a **card**. Axes: rarity tier, grade (Normal/Golden), rank, family, class/school tags.

### Exports (both obtainable — always request them)
- **Catalog export** (all in-game cards): per card — `name, rank (max), description (real tooltip with coefficients), rarities (COMMON→LEGENDARY), grades (every card exists in BOTH Normal and Golden), families (DEFAULT / LUCKY / TALENT), class + tab, tags (class/school/role), sharesModifiersWith, requiresEquip, requiredLevel`.
- **Owned-cards export**: four pools — `abilityNormal, abilityGolden, talentNormal, talentGolden` — entries `{cardId, spellId, rank}`. Match to catalog by spellId (names collide — see duplicate-name trap).

> ⚠ **Export tooltips can be INCOMPLETE, not merely unresolved.** Beyond the known `$s1` magnitude problem, exports have been observed **omitting entire clauses**. Enhanced Weapon Mastery's export text reads only *"Increases all damage done by $s1%"*; the live tooltip adds *"does not stack with Enhanced Weapon Mastery, Unending Fury, Answered Prayers or Blessed Weapons. Only the highest increase applies."* — which changes the card from a top-tier multiplier to a dead slot. **Before committing to any card verdict, ask for a live tooltip screenshot.**

### 2a. The index (`ascension_index.db`)

Both exports are parsed into a queryable SQLite database — check it before re-parsing raw JSON. Full schema and query cheat-sheet in `INDEX_GUIDE.md`, uploaded alongside it.

**⚠ v10: the `.db` is rebuilt from source each session, not uploaded as a binary.** Uploaded binary copies were repeatedly arriving corrupted (mount-pipeline null-byte mangling — see v10 changelog). The `.db` is now purely an **ephemeral local artifact**: at the start of any session that needs it, run (from `index/`) `build_index.py` → `seed_borrowed_modifiers.py` → `seed_confirmed.py` → `seed_synergies.py` in sequence against the plain-text project mounts. This reconstructs the identical database, seeded facts included, with no corruption risk since every input file is text. **Do not re-upload the `.db` to project knowledge — it's redundant and the upload path is the thing that's broken.** The real source of truth for confirmed facts is `seed_confirmed.py` itself (append-only, plain text); keep that file current and the index follows automatically. **(v12)** DBC-derived tables (`spell_dbc_raw`, `dbc_*`) additionally need `build_dbc_index.py`, which requires local client access — if that's unavailable, load `index/dbc-extract.json` instead of skipping that data entirely.

**Related but separate:** `INDEX_GUIDE.md` also documents `decode_inspect_export.py`, which decodes a **live** in-game inspect (via the third-party site inspects.nie.one) into readable spec/gear data for any character. This is a live external capture, not part of the offline index — useful for pulling another player's build for comparison, or re-syncing this project's own docs against a character's actual current state (see the Paladin handoff v6 case study).

- **schools / mechanics / scaling coefficients** are auto-extracted from tooltip text at build time — treat these the same as any export field: fast, comprehensive, but subject to the incompleteness warning above.
- **`class_origin` is populated for ~392/3061 entries only** — either doc-confirmed (proc-tested) or auto-derived from a tooltip's explicit `"uses X modifiers"` clause resolved against the base ability's real WotLK class. **NULL means unknown, not "not this class."** Never treat a NULL as a negative result, and never treat an `inferred_borrowed_modifiers` row as settled — it's still a prediction per the class-tag rule (§4) until proc-tested.
- **It is a derived cache, not a source of truth.** This doc and the build handoff stay authoritative. If a verdict here changes, add the fact to `seed_confirmed.py` in the same session (§5) — the next rebuild picks it up automatically.

### Normal vs Golden
- **Golden guarantee slots can only hold goldens the player owns. Normal guarantee slots can reach essentially any card** (ownership not required). Never waste a Normal slot on something coverable by an owned golden, and never plan a Golden slot around a card only owned as Normal.
- Duplicates feed the golden economy.

### Ranks — and why partial ranks are ASSETS
- **A card guarantees the MAX RANK of a talent — that is the reason to slot one.** RNG rolls land anywhere from **1 to 5**.
- The `X/Y` shown in the UI is the **roll result**, NOT spent talent points. **There is no respec lever.**
- ⚠ **Do NOT reroll away a partial-rank card the player wants:**
  1. Rolling an upgrade on a held partial-rank card **refunds the reroll** if it hits — the fishing is self-funding.
  2. Staff have stated that partial-rank talents have a **higher chance of rolling** their own upgrades if the player already holds the talent.
- **Corollary for chase lists:** a **1/1 single-rank card is a cheaper acquisition than a 5-rank card of similar value**, because a hit is a complete hit. Multi-rank chases can land at 1/5 and need re-fishing. Weight single-rank targets up.
- *Open question:* whether the elevated upgrade chance applies to rerolls of **any** slot, or only the slot currently holding the card.

### Rapid reroll
The game provides an auto-roller: tag **likes** and **dislikes**, and it rerolls repeatedly until it hits the targets or the budget runs out. Practical consequence: build advice should be delivered as **two explicit lists** (protect / chase), not prose. **Watch for protect tags failing** — cards on a protect list have gone missing between sessions.

### Guarantee logic: rarity × criticality × rank × affinity
- Lock: rare + build-defining; high-impact multi-rank (esp. Legendary r5); single-rank **keystones** that are catastrophic-if-missing; **off-theme or classless** cards affinity won't deliver.
- Roll: common, on-theme, replaceable, single-rank non-keystones.
- Guarantee slots are set per character. Once a character is finished levelling, **guarantee allocation is frozen and rerolls become the only tuning tool.**

### Roll affinity (verified)
Random rolls **skew toward what the build already looks like** (class/school themes — almost certainly the catalog `tags` field). On-theme rares roll reliably across pack volume; **off-theme and classless legendaries are the structural roll risk**.

### LUCKY family flag — ⚠ THEORY FALSIFIED
**"No-LUCKY cards cannot appear in random rolls" is WRONG.** Divine Steed (no-LUCKY) has been rolled multiple times.

**Current best hypothesis:** a remnant of a previous Season that featured actual "Lucky Cards". Secondary possibility: mild rarity weighting. **Do not build guarantee-slot or reroll strategy around the LUCKY flag.** Working roll model is **rarity × affinity** only.

### Duplicate-name trap
Distinct cards can share a name across classes (e.g. Vengeance: Paladin r3 stacking-damage vs Druid r5 spell-crit-damage; Dual Wield Specialization: Rogue r5 crit/off-hand vs Shaman r3 hit/elemental). Also watch for cards sharing a **name with a retail/classic talent but with completely different mechanics** — Ascension's **Mental Quickness** is a physical↔magic ping-pong damage buff, *not* the WotLK AP→SP converter. **Always read the actual tooltip.**

### ⚠ Exclusivity buckets
Some effects share a **"does not stack / only the highest applies"** bucket, and the exclusion list is often **only in the live tooltip**. Known bucket: **Enhanced Weapon Mastery ↔ Unending Fury ↔ Answered Prayers ↔ Blessed Weapons** (all-damage %). Similar wording appears on **Holy Focus** ("spell crits deal 200%, does not stack with other similar effects") and **Dual Wield Specialization ↔ Dual Wield Mastery** (fully redundant — one of them is always a dead slot).

**Practice:** when two slotted cards buff the same thing in the same way, assume a shared bucket until proven otherwise, and check the live tooltips of both.

### ⚠ Weapon-imbue exclusivity (v7)
Weapon-imbue-type ability cards (Windfury Weapon, Flametongue Weapon, Fel Infused Weapon, Rockbiter Weapon, Frostbrand Weapon, etc.) share a **weapon-enchant slot** — only one can be active at a time. This is a **different bucket from the talent all-damage% exclusivity above** — it's a mechanical slot conflict, not a stated "does not stack" tooltip clause, so it won't surface from a text scan the way §2's other exclusivity examples do. **Before recommending any weapon-imbue card alongside another, ask "is this an imbue?" first** — the same reflex as checking for a shared talent bucket, just without a tooltip to search for.

### Prestige / farming
Prestige laps (1→60 resets) yield ~160 packs × ~5 cards + rerolls; dupes feed golden economy. "Not guaranteed ≠ not in the build" — roll/fish for it.

---

## 3. Paths (five total)

**Path switching is free and instant** — "test both and compare" is always viable. ⚠ **This also means a character may not be on the path you assume. Verify before reasoning from path grants.**

### Path of Strength
Bonus Str (flat 4 + 0.5/level ≈ 34 @60); **AP = 100% of Strength**; Str → Parry. 1H: +20% ArP. 2H: melee/ranged **physical abilities** +10%.

### Path of Agility
Bonus Agi (same flat curve); **AP = 100% of Agility**; Agi → crit chance AND crit damage. 1H: damaging melee/ranged abilities' GCD and cost −8%. 2H: melee/ranged **ability** crit damage bonus +20%.

### Path of Duality
**Tooltip claims:** AP = highest of Str or Agi. **Int → melee/ranged crit; Agi → spell crit.** Casting no longer resets swing timer. 2H: magic AND physical damage +6%. 1H: +10% haste.

**⚠ MEASUREMENT STATUS DOWNGRADED (v4).** Earlier readings claimed an exact ×1.75 itemised SP amp and confirmed cross-crit conversions. A later live character sheet showed **neither**:
- **Bonus Damage 400 vs Bonus Healing 379** — a 5.5% gap, consistent with an Int→SP conversion talent alone and *no* amp. An active ×1.75 would put Bonus Damage near 660.
- **Crit source breakdowns listed Agility under melee crit and Intellect under spell crit** — the base-game conversions — with **both tables summing exactly**, leaving no room for a hidden cross-conversion term.

**The v3 "Int → melee crit ≈ 38 Int per 1% CONFIRMED" is RETRACTED** — it rested on a single +11 Int swing yielding +0.29% crit, about 4 crit rating, well inside contamination range from a second stat on the test item.

**Lesson:** a single small-magnitude stat swap is not a confirmation. Prefer **crit-source breakdown tooltips** (which itemise every contributor and sum exactly) over differential measurement — they're free, instant, and unambiguous.

**Note:** the talent card **Mental Dexterity** (r3: +hit from Int; capstone: Int→melee crit rating, Agi→spell crit rating) independently implements the same cross-stat conversion Duality's tooltip claims. A build can get this conversion reliably from the talent card without depending on whether the path passive is actually live — worth using as the primary lever until Duality's own claims are re-confirmed on a live sheet.

### Path of Intelligence
Bonus SP/Int/Spirit (flat Int 4 + 1.25/level ≈ 79 @60; Spirit ~40); **SP from items and effects DOUBLED**. 2H: +12% spell haste. 1H: +5% spell damage.

### Path of Healing
Enables the Healer role; Healing Power exists as a distinct gated stat — **off-path healing works only for emergency top-offs**. Flat Int/Spirit grants like Intelligence. 2H: +10% spell haste, +3% spell crit. 1H: +5% healing.

### Path rules
- "**Abilities**" wording in path bonuses **excludes auto-attacks** (yellow damage only). "Damage done" wording includes autos.
- Titan's Grip / double-2H setups count as 2H for path clauses; you never get both weapon clauses.
- Choosing: purely physical → Strength/Agility; anything with (SP+AP) coefficients or hybrid schools → **Duality**; caster-only → Intelligence.

---

## 4. ⚠ The class-tag rule (predictive heuristic)

**A card's `uses X modifiers` line predicts its class tag — not its flavour, name, or damage school.**

Proof case: **Lightbound Cleave** is Holy-flavoured, deals Holystrike, reads like a Paladin ability — and produced **zero** procs from a "damaging Paladin abilities" trigger. It borrows **Cleave** modifiers, so it is **Warrior**-tagged.

| Card | Borrows from | Predicted tag | Feeds a Paladin-gated proc? |
|---|---|---|---|
| Dawnreaver | Crusader Strike | Paladin | Yes |
| Dawn Strike | Sinister Strike | Rogue | No |
| Holy Finish | Eviscerate | Rogue | No |
| Lightbound Cleave | Cleave | Warrior | **No — confirmed** |
| Whirling Light | Whirlwind | Warrior | No |
| Blades of Light | Bladestorm | Warrior | No |
| Fel Cleave | Cleave | Warrior | No — Shadowflame school, not in current Paladin kit (v11) |

**Use it to predict, then confirm with a dummy proc count.** `sharesModifiersWith` separately means "talents boosting X also boost this card" — which opens whole **cross-class talent chase surfaces** (e.g. a build using Eviscerate and Whirlwind modifiers should be shopping Rogue and Warrior talent trees).

### ⚠ Proof case #2: trigger source ≠ modifier source (v7)
The rule applies just as hard to **what triggers an effect** as to what an effect looks like. **Molten Earth** is spawned by casting **Lava Lash** (Shaman), reads like a Lava Lash spinoff, and was initially assumed to inherit Lava Lash's damage talents (Elemental Fusion, Lava Flows) — a recommendation made and then **retracted in the same session** once the live tooltip showed Molten Earth actually **"uses Fire Nova modifiers."** Elemental Fusion and Lava Flows still buff Lava Lash's own weapon-damage hit; they do nothing for Molten Earth. Same shape as Lightbound Cleave above, one level removed: there it was flavour vs. modifier source, here it's **trigger** vs. modifier source. **Corollary: never assume a spawned/triggered secondary effect shares its trigger's modifier bucket — check its own `uses X modifiers` line independently.**

### Engine intake tags
Proc engines differ in what they accept, and the difference drives rotation design:
- **Narrow intake** (e.g. "damaging **Paladin** abilities") — only same-class-tagged buttons feed it. A build whose top damage comes from borrowed-tag cards can **starve its own engine** without noticing.
- **Wide intake** (e.g. "dealing direct damage with spells and abilities") — everything feeds it.

**Always map each engine's intake against the actual rotation before valuing it.**

### ⚠ Channelled lockout abilities are engine poison
Abilities worded *"while under this effect you cannot perform any other abilities"* (Bladestorm-family) do more than occupy time — they **suppress every proc engine with a narrow intake** for the whole channel. A parse can show such an ability as a top damage source while it is net-negative, because the engine it starved doesn't appear in the log at all. **Compare total damage across rotations, never per-ability shares.**

---

## 5. How to help the player reason

- **Rebuild `ascension_index.db` from source at the start of any session that needs it** (from `index/`: `build_index.py` → `seed_borrowed_modifiers.py` → `seed_confirmed.py` → `seed_synergies.py`, §2a) — don't rely on a re-uploaded binary. Use the rebuilt index for cross-referencing and formula comparisons; fall back to raw `spell-export.json` only for something it doesn't capture.
- **Keep `seed_confirmed.py` in sync with this doc.** Whenever a verdict here or in the handoff changes (a retraction, a new resolution, an updated stat weight), add the matching fact to `seed_confirmed.py` in the same session — the next rebuild picks it up automatically. This replaces directly editing `confirmed_facts` rows in a persisted `.db`.
- **Check `shared_synergies` before treating an external build's engine as novel (v12)** — another player's card/engine may already be logged with a confidence tier and a linked `builds/shared/synergy_*.md` file from a past encounter.
- **Cross-reference against the exports** — but treat exports as *incomplete*, not authoritative. Request live tooltip screenshots before final verdicts.
- **Coefficients over intuition** — pull real tooltip scaling; when magnitudes are unresolved (`$s1`) or sub-spells are hidden, say so and name the test.
- **Apply the class-tag rule (§4)**, then verify.
- **⚠ Design tests that don't destroy cards.** Rerolling a card to measure it is **not acceptable** — multi-rank cards may return lower and there's no respec. Prefer: **character-sheet breakdown tooltips → gear swaps → consumables → buff-state filtering → two-target comparisons → bar toggles.**
- **✅ Parse crit% per source to identify crit tables — this is the cheapest mechanics test available.** A single combat log gives every ability's crit rate at once; sorting them against the sheet's melee and spell crit values immediately reveals which table each uses, and abilities with 0% crit reveal periodic effects. This settled a question that had been "under review" for two document versions. **Correction (v7):** a nonzero crit% on a periodic/ground effect is NOT reliable evidence that it's structurally different from a normal aura tick — Molten Earth is a confirmed aura-tick DoT that still crits (§1). Use crit% to sort spell-vs-melee table, not to infer an effect's underlying implementation.
- **Check sample size before proposing a proportion test.** Crit-rate questions need thousands of hits; damage-multiplier questions need ~100. If candidate values are within ~3 points, find a different discriminator.
- **Watch for flat vs scaling damage in low gear.** Flat-value abilities dominate the meter in leveling greens and shrink as a share with gearing. Don't build a gearing plan around a source that doesn't scale — and **re-derive old verdicts when gear changes**, since "measured dead" at low gear often means "measured against a small stat pool."
- **Percentage multipliers are gear-proof; flat adds decay.** When forecasting to endgame, rank cards by scaling class first.
- **Check cap status before assigning any stat weight.** An overcapped stat is worth exactly zero, and hit/expertise caps move with build choices (dual-wield white hit is a separate, usually unreachable cap).
- **⚠ Before weighting hit, count what actually rolls a hit check.** Establishing that an ability *crits* on the spell table says nothing about whether it *rolls against spell hit* — these are independent rolls, and assuming otherwise once inflated a hit weight from ~0.3 to 2.0. In a proc-heavy hybrid kit most damage makes no hit check at all: **periodic effects cannot miss**, **procs riding an already-landed attack** (seal riders, weapon-imbue procs, extra-attack procs) don't re-roll, and **melee abilities use melee hit** regardless of which table they crit on. Whether **summoned procs** roll is server-specific and must be measured. Sort the parse into these buckets and weight hit against the *confirmed* gated share only.
- **Anchor miss/hit caps to the content actually being run.** Spell miss vs a +3 raid boss (~17%) is roughly triple the +2 dungeon value (~6%). An addon's "57/96" display is usually quoting the raid cap, so a player seeing zero misses in dungeons is not contradicting the display — both are correct. State which content a hit weight applies to.
- **Absence of observed misses is evidence, but check the sample.** Three casts of a spell cannot disconfirm a 17% miss rate. Ask for the parser's per-ability **Miss / Dodge / Parry / Resist** breakdown on the *highest-hit-count* sources rather than reasoning from the damage-share table alone.
- **Flag dead/conditional talents** — verify triggers actually fire for the kit. Cards granting buffs that modify abilities the player doesn't own (e.g. a proc granting a Shadow Bolt buff to a Paladin) are pure dead weight.
- **Count resource pools separately.** Mana, rage and energy are independent bars.
- **Prefer cards that cover multiple buckets** — an "all spells and attacks" card can be worth more than several narrower ones.
- **Maintain an explicit assumption register** — every best guess written down as falsifiable, with the test that settles it.
- **Elite players' builds are evidence**, but weaker than a parse.
- **Separate loadout goals:** dungeon-trash AoE and boss single-target are different loadouts, not one compromise.
- **Watch the changelog and mind realm tags.** Balance changes and even ability *schools* change per patch and realm.
- **Be willing to walk back your own recommendations** when a measurement contradicts them, and say so plainly. Several v2/v3/v4 conclusions were overturned by single logs or single tooltips — including recommendations made earlier in the same session.
- **Check for ICDs before dismissing a per-hit proc as diluted by fast weapons.** A per-hit effect with no stated internal cooldown (Fel Infused Weapon, v6) scales UP with attack frequency rather than down — the opposite of the usual "more, smaller hits average out" intuition. Confirm ICD presence/absence from the live tooltip before valuing these against weapon speed.
- **When hunting multipliers for a specific effect, prefer talents that name it verbatim over talents matched by generic school wording (v7).** Shadow and Flame and Bane both list "Shadowflame" explicitly in their tooltips — ground truth, no test needed. Emberstorm only says "Fire and Shadow spells" — a prediction under the hybrid double-dip rule, not a confirmed hit, even though it reads like it should apply. Named lists outrank generic wording until proc-tested. This is the same discipline as the class-tag rule (§4) applied to damage-multiplier talents instead of proc-engine tags — and proof case #2 above (Elemental Fusion/Lava Flows vs. Molten Earth) is what happens when it's skipped: a spawned effect was assumed to inherit its trigger's modifiers by proximity, without checking its own `uses X modifiers` line first.
- **When decoding a live in-game spell ID export (WeakAura, inspect addon, etc.) against the catalog, an unresolved ID is very likely a different rank of a known card, not missing content (v7).** Multi-rank talents appear to get a distinct spellID per rank in-game, while the catalog export only stores one canonical ID per card. Check ±1-3 of the unresolved ID for a known card name before concluding it's absent — this resolved 5/5 unmatched IDs in one live cross-check, each landing exactly on a card already known to be held at partial rank.
