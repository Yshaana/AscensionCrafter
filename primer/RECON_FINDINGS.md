# RECON FINDINGS — Phase 0 (v1)

> **`FINDING 2026-08-04`** — point-in-time analysis, true as of its date and **not maintained since**. Not citable as current truth without re-checking against the tree. *(Classified `3f` F8c, 2026-08-07.)*

**Produced by session `0a`, 2026-08-04.** One section per Phase 0 task, each ending in a
**CONFIRMED / DISPROVEN / PARTIAL / BLOCKED** verdict with the evidence behind it.

Session `0b` already settled part of Task 2 (healing endpoint, role vocabulary, report discovery,
changelog API). Those verdicts are folded in here rather than repeated — `Session_2026-08-04_0b_crawler.md`
holds their original derivation.

**How to read a verdict here:** it describes what was true on 2026-08-04, on **Darkmoon**, on the
client build then installed. The server patches daily. Anything marked CONFIRMED is still subject to
§2.5 stamping — it is not permanent.

---

## ⚠ Refined by session `1a` (2026-08-04) — read before quoting a number from this file

Two figures below were **measured again in `1a` against the same data and came out different**. The
verdicts stand; the numbers were understated, both for the same reason — **the Phase 0 reporter used
`max()`, which silently returns the first of a tie.** Recorded here rather than edited in place, so
the correction is visible instead of retroactive.

| This file says | Actually | Why |
|---|---|---|
| **697** catalog entries carry the wrong rank | **711**, of which **25 are genuinely ambiguous** | Several spells can tie for the top rank available at level 60, and `max()` hid it. Real causes: a line whose members *all* read "Rank 1" (`Desolation`, 5 members); a line pulling in an other-realm 11-prefix variant (`Arcane Focus` → `912840` **and** `1212840`). Ambiguous lines are now recorded as `confidence='conflict'` and **never tie-broken** |
| the fingerprint rule, as one field set | it needs **two** | The strict set answers *"same ability?"* and is the **wrong test** for *"two ranks of one ability?"* — rank legitimately changes radius, cooldown and resource type, and higher ranks *fill* effect slots the lower rank leaves empty. Strict comparison flagged **106** rank conflicts, almost all ordinary talents; the rank-aware set leaves **8 rows on 2 cards** |

Two claims below got **stronger** with more data, not weaker:

- **"0 of 1,054 entry_ids match a catalog `spells.id`"** → at 1,487 observed entry_ids there are now
  **4** numeric collisions (`1152`, `36936`, `50029`, `50043`) and **still 0 real matches**. `1152` is
  `Path of Healing` in a crawl and `Purify` in the catalog. **Never join `entry_id` to `spells.id`.**
- **"3,061/3,061 catalog ids reachable from a CA rank slot"** — reproduced exactly.

🆕 **One finding this file does not contain:** `Necrosis` (in the current pool) **changes damage
school across its own ranks** — 0 → 32 (Shadow) → 1 (Physical). Unexplained; recorded as a conflict.

---

## Headline results

Seven things changed the plan. Everything else is detail.

| # | Finding | Consequence |
|---|---|---|
| 1 | **`entry_id` is the CharacterAdvancement ID, and `CharacterAdvancement.dbc` exists in the client** — 10,231 records, layout reverse-engineered, 1,054/1,054 crawled entry_ids resolve, 660/660 names agree | Task 5's gate is **open**. The crosswalk is a real table, not an inference |
| 2 | **A level-60 character's spell rank is deterministic** (`SpellLevel <= 60`, highest rank wins) — reproduces the owner's own tooltips exactly | Rank resolution is a query, not a guess. **697 catalog entries (≈50% of multi-rank ones) carry the wrong rank's magnitudes** |
| 3 | **Class ownership resolves from `SkillLine` names, not ClassMask** — Ascension renamed skill lines to classes. 1,789/3,061 catalog entries (58%) get a deterministic single class, vs 394 (13%) today, and it agrees with 382/387 existing rows and 7/7 of primer §4's proof cases | Task 4a delivered **4.5×** coverage. The class-tag rule becomes a fallback, not the primary method |
| 4 | **98% of the 803 "blocked" hidden-formula spells would resolve from numeric DBC fields** (311 with SP/AP coefficients, 770 with flat magnitudes) | Phase 0 Task 4 asked for this to be flagged loudly if large. **It is large.** Numeric-field extractor = Phase 1's highest-value task |
| 5 | **The client DBC is the earliest and most complete card source.** 52/52 cards announced since 2026-07-01 are already in `CharacterAdvancement.dbc`; only **2/52** are in `spell-export.json` | The catalog export goes stale within days. Existence questions go to the DBC first |
| 6 | **Three idempotency bugs** — two in `build_dbc_index.py` (running it twice silently deleted all 113 hidden-formula scaling rows and shrank `spell_dbc_raw`), one in `seed_confirmed.py` (doubled every fact, 103 → 213) | All fixed and verified. Previously-published coverage numbers were only reproducible from a clean database |
| 7 | **The CA table carries a playable-pool flag** — byte 2 of slot 121 isolates **3,129** currently-playable cards from 10,231, covering 1,054/1,054 observed and landing within 3% of BisBeard's independent count | Phase 1 ingests the playable pool, not the whole table. Also resolves the duplicate-name trap structurally. See A1 |

Two claims from earlier docs are **retracted** — see §Retractions.

---

## Task 1 — `db.ascension.gg`

**Verdict: CONFIRMED (already), and closed to further automated work by policy.**

Tasks 1c–1f were answered in a previous session and stand unchanged: the site is server-rendered,
carries damage coefficients, and uses catalog-compatible IDs. Nothing was re-fetched this session.

**No automated requests were made to db.ascension.gg in session 0a**, deliberately. §1a records that
robots disallows automated access after ~2–3 requests, and the owner's standing decision (0b) is to
stay inside robots.txt with targeted manual lookups only. Task 1's original "fetch ~30 spells"
instruction is therefore **superseded**, not skipped — it was written before §1a was discovered.

**Two sub-questions Task 1 asked that are now answered from other sources**, at no cost to the
robots budget:

- *"Report how many catalog entries the owner actually plays at a rank the catalog doesn't carry."*
  **697 of the 1,409 catalog entries that sit in a multi-rank line** (≈50%). In **all 697** cases the
  level-60 spell id is absent from the catalog entirely. Sensitivity-checked across four rank-line
  grouping strictnesses: the count moves only between **697 and 794**, and both anchor lines stay
  intact under every variant. See Task 4's rank section for the method.
- *"Which ID space do combat logs use?"* — `ascensionlogs.gg` per-ability rows carry `spell_id` in
  the **catalog/client space** (e.g. `8400` Fireball). ✅ **Now also answered for the client's own
  `WoWCombatLog.txt`: the same plain `Spell.dbc` space, 809/809 — see A2 below.** 0b's `9931032` lead
  turned out to be an ordinary high client id, not a fifth space.

### ✅ Both logged conflicts CLOSED — owner supplied the two pages, 2026-08-04

**Fel Infused Weapon's school: both sources were right about different spells.**
`276076` is the **imbue-application** spell — `SchoolMask` 4 (**Fire**), and its only effect is type
54 (`ENCHANT_HELD_ITEM`, MiscValue 952, BasePoints 1799→**1800**, reproducing the page's
"Enchant Item Temporary: #952, Value: 1800" exactly). **It deals no damage at all.** The damage comes
from a *separate* spell, `276075` "Fel Infused Attack", `SchoolMask` **36 = 32 (Shadow) + 4 (Fire) =
Shadowflame**, effect type 2 (`SCHOOL_DAMAGE`). So the db page is right about the spell it renders and
the docs are right about the damage.

🆕 **Generalisable rule — this is the trigger-vs-modifier trap (primer §4 case #2) in a new guise:
the school of an *applying* spell is not the school of the damage it causes.** Follow the effect
chain to the spell carrying `SCHOOL_DAMAGE` before reading a school off a card you press.
*Bonus:* effect 54 mechanically confirms this card occupies the temporary-enchant slot — the
primer's weapon-imbue exclusivity bucket is a real slot conflict, not a tooltip convention. And
`276082` BasePoints 14→**15%** matches the existing two-hander fact exactly.

**Holy Supernova's AP term: now a three-way split, and immaterial.**
`0.159` (catalog literal, *and* the literal inside db's own rendered tooltip) vs `0.157`
(db's "Scaling #2: +15.70%") vs `0.161` (client DBC `EffectBonusCoefficient`, identical at R1 and R6).
The **SP** term has no such problem — literal `0.2415` and "Scaling #1: +24.15%" agree exactly.
⚠ Do **not** apply "numeric field beats text" mechanically here: db exposes **two** scaling rows while
the stock DBC carries **one** `EffectBonusCoefficient`, so these are different data structures and
Ascension evidently maintains its own scaling table for custom spells. Practical impact: the spread is
≈2.5% of the AP term, itself the minority contributor next to SP. **Treat it as ~0.16 ± 0.002 and
spend verification effort elsewhere.**

### 🎯 Three unplanned results from those same two pages

1. **The level-gate rank rule is confirmed by an independent source.** The Rank 6 page reads
   *"Requires Level 60"*; `dbc_spell_rank` independently gives `270187` `SpellLevel` 60. The whole
   line resolves 270182–270190 = Ranks 1–9 at levels 14/28/36/44/52/**60**/68/75/80.
   It is also a **live instance of the wrong-rank problem**: the catalog holds only Rank 1
   (61–69 damage) while the played Rank 6 deals **595–714** — a ~9.7× gap — and `270187` has **zero**
   `spell_scaling` rows because the catalog does not contain it.
2. **Holy Supernova is Priest-tagged, and three independent sources now agree** — the page states
   *"This uses Holy Nova modifiers"*, the index already inferred Priest from `borrows_from`, and
   session 0a's SkillLineAbility resolution returns Priest via a completely different mechanism.
   **Consequence for the Paladin build:** it would **not** feed Hammerdin (which gates on *Paladin*
   abilities) — the same trap as Lightbound Cleave. It does feed wide-intake engines like JotTH.
3. **A partial answer to "do coefficients scale with rank?"** — within this one fingerprint-confirmed
   line, `EffectBonusCoefficient` is **identical** at R1 and R6 (0.161); only the flat term scales
   (BasePoints 60→594). One line is not a law, but the asymmetry is the useful part: **reading a
   coefficient off the catalog's Rank-1 entry is probably safe; reading a flat magnitude off it is
   catastrophically wrong.** (The earlier attempt at this question was retracted for comparing two
   different abilities sharing a name — this comparison is within one confirmed line.)

⚠ **One new conflict opened by the Fel Infused Weapon page**: db renders *"4.5 Points Per Level"*
where the client DBC field says **1.5** — exactly 3×. db was byte-faithful on Holy Supernova
(3.6 vs 3.5999999), so it is not systematically wrong; likeliest causes are a different rank/variant
(two spells are named "Fel Infused Weapon", `276069` and `276076`, neither rank-numbered) or a
snapshot older than the installed client. **Settle it with an in-game tooltip read at level 60**,
where the value is fully resolved — a tier-1 source that beats both.

Separately, this clarified a mechanic the docs had the wrong shape for: **`EffectRealPointsPerLevel`
is a per-level *rate* above the spell's own base level, not a flat one-off add.** The existing
"Fel Infused Weapon flat component ≈ 5.5" reading treats it as a flat +1.5 and is wrong in form.

---

## Task 2 — `ascensionlogs.gg` endpoint map

**Verdict: CONFIRMED for the endpoint map; PARTIAL on target count; DISPROVEN on per-parse stats.**

Settled in 0b and unchanged: `character_spell_healing` exists; `support` is the healer role;
report discovery is sequential ID probing (list endpoint is 401); per-ability endpoints aggregate
across `encounterIds`; `phase_number` ≠ the server's "Phase N" label.

Answered this session, entirely from **already-captured data** — no new requests:

### ✅ §2.5 stamping — CONFIRMED complete
Every crawl record carries `realm`, `season`, `patch_date`, `captured_at`. Zero records missing
`patch_date` across the sampled files. The stamping requirement is satisfied at capture time.

### ⚠ Target count — must be INFERRED. No field carries it.
Encounters expose `participant_count` and `player_participant_count`. Their difference is **not** a
target count:

- Across 974 encounters the difference runs **0..135, median 13**
- **Boss encounters median 12** non-player participants (range 1..100) — a single-target boss fight
  would be 1

It counts every non-player unit that appeared in the window (adds, pets, totems, summons), not
concurrent targets. The better inference route is distinct enemy units in the avoidance payload
(`target_character_id`), which is exactly 1 for a clean single-boss capture — but it is contaminated
by the `boss_group` scope aggregation 0b introduced for grind reports.

**Consequence for §2.9:** target count is an inference with real error bars, and per Phase 0's own
instruction it must **never silently default to 1**.

### ⚠ Content type — PARTIAL
Derivable signals exist but are incomplete:
- `/api/phases` `locations[]` carries **`is_world_boss`** and `is_main` per zone — world-boss content
  is cleanly separable, from real data rather than an invented taxonomy
- Encounters carry `difficulty` (`normal`/null), `is_boss_encounter`, `trial_level`, `zone`
- Reports carry `keystones`, `is_speed_run`, `difficulty`, `zone`

But `difficulty` is **null on 578/974** encounters and report `zone` was `"Unknown"` on all three
reports held. **Raid vs dungeon is not directly flagged** — it needs a zone→content-type mapping
built from the phases `locations` list plus judgment. Enough to build §2.9's presets from real data;
not enough to auto-classify every encounter.

### ❌ Per-parse character stats — DISPROVEN (they do not exist)
Ability rows carry only: `character_id`, `character_name`, `character_class`, `character_spec`,
`character_type`, `is_boss`, `spell_*`, `total_damage`, `casts`, `hits`, `crits`. **No crit rating,
spell power, attack power, or haste.**

The constraint Phase 0 Task 2 anticipated **holds**: per-parse stats must be approximated from the
nearest-in-time armory capture, with the error that implies. This is direct support for the Phase 3
T5 self-snapshot requirement — it is the only route to exact per-parse stats for any character.

### 🎯 …but `character_spec` carries the PATH, per parse
Observed values: `Duality` (4,022 rows), `Intelligence` (3,402), `Strength` (4,541), `Agility`
(1,440), `Healing` (366), plus `Hero`/`Hero Tank` and role-suffixed variants. `character_class` is
always `Hero`.

**This is per-parse Path attribution for every logged character** — not in any doc so far, and
directly useful to Phase 3's pooled inference (Path determines stat conversions) and to the Path of
Duality question.

### ⚠ Avoidance rows have no attacker id
`character_damage_taken_abilities?participantType=enemies` rows are keyed by
`target_character_id` (the enemy) × ability name. There is **no attacking-character id**. Avoidance
therefore pools across every player using that ability in the window and **cannot be attributed to
one character**. Consistent with how the primer's Hammer-from-the-Heavens result was derived; worth
knowing before designing a per-character hit-table test.

---

## Task 3 — Changelog

**Verdict: CONFIRMED as a change-history source; DISPROVEN as a new-card discovery source;
DISPROVEN as a phase-timeline source.**

Parser shipped: **`ingest/changelog/parse_changelog.py`** (offline, re-runnable over the committed
corpus; ✅ moved here from `tools/scrapers/` in the Phase 1 T1 restructure as predicted, and its
classification logic now lives in `core/changelog/parse.py` with `ingest/changelog/ingest_changelog.py`
writing the `patches` tables). It extracts date, realm(s), live-status, category, change type, raw
text, and ability-name candidates tagged by detection method.

### Corpus shape — the important caveat
35,238 entries back to 2016/07/23, but **it is mostly not about this realm**:

| Realm tag | Entries |
|---|---|
| *(untagged)* | 27,609 |
| Elune | 2,875 |
| Area-52 (3 spellings) | 2,455 |
| **Darkmoon** | **170** |
| Dawnrise | 151 |

Bracket tokens are dominated by historic realms and instance names, not abilities. **Filter by realm
or date before concluding anything**, and treat untagged as *unknown*, not *all realms*.

### Current-era slice (251 entries since 2026-07-01) — this is the usable part
- **Realm tagging is dense now**: only 22/251 untagged (vs 78% untagged corpus-wide)
- **84.9% carry a not-yet-live status tag** (`[Pending Restart]`, `[Going Live …]`). Status parsing
  is mandatory — you cannot assume an entry is in effect
- **86.9% name at least one ability candidate; 78.5% resolve to a known card**

### ❌ New-card discovery — the changelog is NOT the earliest signal
There **is** a clean machine-detectable announcement pattern:
`"A new Talent/Mystic Enchant is now available! [Name]: …"` — 52 matches since 2026-07-01.

But every one of them was **already in the client**:

| | in `CharacterAdvancement.dbc` | in `spell-export.json` |
|---|---|---|
| 52 newly-announced cards | **52 / 52** | **2 / 52** |

**The client DBC knows about a card by the day it is announced; the catalog export does not.** So the
changelog's value is *change history, magnitudes-in-prose, realm and status* — not existence. For
existence, extract the DBC.

*(Flagged for the owner, not acted on: `[Authority]` — "Execution Sentence's periodic damage
increases…" — was announced 2026-08-04 and touches a chase-list ability whose magnitude
`build_paladin-hammerdin.md` §8 records as unresolved.)*

### ❌ Phase transitions — not detectable from changelog text
93 entries match phase/season language, but they are overwhelmingly **boss mechanic** phases
("Illidan starts his Phase 3…"), not server content phases. `/api/phases` is the authoritative
source and is already captured daily. Do not build the phase timeline from changelog text.

### Data artifact, not a parser bug
Two entries contain malformed nested brackets (`[Darkmoon [Dawnrise]`). Left as-is and reported.

---

## Task 4 — DBC extraction

**Verdict: CONFIRMED, and materially larger than the task anticipated.**

Re-ran `index/build_dbc_index.py` against the live client. `Spell.dbc` holds **209,111** spells;
`spell_dbc_raw` is scoped to **15,769** relevant ids (up from 11,714 — see the rank-sibling fix).

### 1. Spell 274132 — the "two independent absences" premise was WRONG
274132 **is** in the client: it is **Winds of Winter Rank 5, `SpellLevel` 58**. 274121 is **Rank 1**.

It appeared absent only because `spell_dbc_raw` was scoped to catalog ids ±3, and rank ids are
frequently **non-contiguous** (R1 `274121` → R2 `274129`). The scoping filter was cutting out the
exact spell a level-60 character casts.

**This resolves the long-running 274121-vs-274132 confusion**: same ability line, different ranks,
and **Rank 5 is what a level-60 character holds** — matching the owner's own statement. Fingerprint
check passes: identical name, school (16/Frost), and effect structure across the line.

**Fixed:** rank siblings of every catalog spell are now pulled into scope (+7,639 ids).

### 2. Coverage
| Metric | Value |
|---|---|
| `spell_dbc_raw` rows | 15,769 |
| catalog entries resolved against DBC | 3,061 / 3,061 (100%) |
| `has_hidden_formula=1` | 887 |
| hidden_refs resolving against DBC | 1,080 / 1,080 (100%) |
| resolved into `spell_scaling` by the text resolver | 84 (113 rows) |
| left blocked | 803 |

### 3. 🚨 The 803 blocked spells — 98% are resolvable from numeric fields
Phase 0 asked for this to be flagged loudly if the number was large:

| | count |
|---|---|
| hidden refs carrying a non-zero `EffectBonusCoefficient` (SP/AP scaling) | **311** |
| hidden refs carrying usable `EffectBasePoints`/`EffectDieSides` (flat magnitude) | **770** |
| **either → a numeric extractor produces a value** | **788 / 803 (98%)** |
| genuinely empty | 15 |

The 15 are correctly empty — they reference debuff/immunity markers (Power Word: Shield → Weakened
Soul, Hammer of Justice → the diminishing-returns marker 32747), which have no magnitude to find.

**A numeric-field extractor is Phase 1's single highest-value task.** It converts the largest
remaining "unknown coefficient" bucket in the project into data, and the current text-regex resolver
is leaving 98% of it on the table. ⚠ It must read **numeric fields only** — never the `description`
string (§2.2 tier 4, the Titanic Mutilate trap).

### 4. Other DBC tables — all present, all extracted
Probed 36 candidates. Newly extracted this session:

| Table | Records | Why it matters |
|---|---|---|
| `CharacterAdvancement.dbc` | 10,231 | **The crosswalk** — see Task 5 |
| `SkillLineAbility.dbc` | 40,973 | Class resolution — see Task 4a |
| `SkillLine.dbc` | 872 | Renamed to class names by Ascension |
| `gtCombatRatings` + 9 more `gt*` | 22,564 rows | **Phase 2's rating→percent conversion.** Ascension may have modified these; assuming retail values was exactly the silent-error risk Task 4 named |
| `Item.dbc` / `ItemStat.dbc` | 563,308 / **1,513,931** | A full client-side item database exists. Relevant to Phase 3 T4 / Task 9 — **not extracted this session** (out of scope, and the layout is unverified) |

Absent: `SpellProcsPerMinute.dbc`, `Item-sparse.db2`, `CharacterAdvancementSpell.dbc`.

### 5. Trigger / runtime
Full run is a few minutes on the owner's machine and requires the client plus a built StormLib. It
re-discovers which archive owns each DBC every run, so a client patch does not break it. Still **not**
part of the routine per-session rebuild. A file-watch trigger was not implemented — manual re-run
after a client patch is adequate and matches the crawler's manual-first posture.

### 🐛 Two idempotency bugs found and fixed
Both silently destroyed data on a second run:

1. **`resolve_hidden_formula_spells` deleted its own rows, then couldn't re-derive them** — it clears
   `has_hidden_formula` on every spell it resolves, so on re-run those spells were no longer in the
   target set. Two consecutive runs took `spell_scaling`'s `dbc_hidden_formula` rows from 113 → 0.
2. **The `spell_dbc_raw` scoping filter keyed off the same cleared flag**, so already-resolved
   spells' sub-spells dropped out of scope, shrinking the table run-on-run.

Now verified stable: clean run and re-run both produce **84/887 resolved, 113 rows, 15,769 raw rows**.

⚠ **This invalidates a documented claim.** `INDEX_GUIDE` v3 states the resolver "already runs the
full list every invocation (not incremental, despite the task brief's framing)". That was wrong — it
was incremental *and* destructive. Corrected in `INDEX_GUIDE.md`.

Also tightened: the "surprising resolution" check matched fact text by bare substring, so a short
name like "Mutilate" matched dozens of unrelated facts and printed a spell × fact cross-product that
buried real signal. Now word-boundary matched and deduped.

---

## Task 4a — `SkillLineAbility.dbc` class resolution

**Verdict: CONFIRMED — and by a different mechanism than the task predicted.**

The task expected class to come from WotLK ID identity for the 1,224 classic-range catalog entries.
**What actually works is better:** Ascension has **renamed the skill lines themselves to class
names**. Skill line 26 is `"Warrior"` (retail: "Arcane"), 50 is `"Hunter"`, 134 is `"Druid"`.

`ClassMask` is useless here — it is `512` on 9,889 rows (Ascension's own classless "Hero" class) and
`0` on 26,776 more. **The skill line's name is what carries the class.**

| Metric | Value |
|---|---|
| catalog entries in `SkillLineAbility` | 1,954 / 3,061 (64%) |
| **resolving to exactly one class line** | **1,789 / 3,061 (58%)** |
| resolving to several class lines | 0 |
| in SLA but on a non-class line | 165 (`Conquest of Azeroth` 163, Lockpicking 1, Bushcraft 1) |
| `class_origin` populated today | 394 (13%) |

**4.5× the current deterministic coverage.** Even class balance: Warrior 240, Druid 232, Hunter 202,
Rogue 198, Mage 166, Shaman 165, Warlock 160, Paladin 145, Death Knight 143, Priest 138.

### Guardrails — both passed
1. **Name identity:** 0 mismatches between catalog name and `Spell.dbc` name across all 1,789.
2. **Agreement with existing doc-confirmed rows:** **382 of 387 agree.**
3. **primer §4's proof cases:** **7/7 agree** where present — including the flagship proc-tested case
   **Lightbound Cleave → Warrior**, plus Dawn Strike → Rogue, Dawnreaver → Paladin, Blades of
   Light → Warrior, Whirling Light → Warrior, Winds of Winter → Mage, Titan's Grip → Warrior.
   (Molten Earth is not in `SkillLineAbility` at all — SLA covers 64% of the catalog, not all of it,
   so the class-tag rule remains the fallback for the rest.)

### ⚠ 5 conflicts — surfaced, NOT resolved (§2.3)
| Spell | Existing `class_origin` | Its tier | `SkillLineAbility` says |
|---|---|---|---|
| 276076 Fel Infused Weapon | `Duality` | `confirmed_native` | Warrior |
| 276115 Ground Slam | Warrior | `inferred_borrowed_modifiers` | Shaman |
| 276204 Carnage Rend | Warrior | `inferred_borrowed_modifiers` | Druid |
| 276811 Shadow Shot | Hunter | `inferred_borrowed_modifiers` | Warlock |
| 288847 Seal of Ebon Vengeance | Paladin | `inferred_borrowed_modifiers` | Death Knight |

Four of the five are the **weakest** existing tier (`inferred_borrowed_modifiers`, an unverified
prediction), so SLA is probably right — but that is a judgment, not a measurement, and auto-picking a
winner is precisely what §2.3 forbids. **Fel Infused Weapon's row is separately suspect**: `Duality`
is a *Path*, not a class, so that row looks like a data-entry error regardless of who is right.

**Seed at a new tier** (`confirmed_wotlk_id_identity` or better `confirmed_skill_line`) — stronger
than tooltip inference, still an identity claim about the base spell. **It resolves class only** and
says nothing about coefficients.

---

## Task 5 — the `entry_id ↔ spells.id` crosswalk 🛑

**Verdict: DISPROVEN that they are the same ID space — and the real mapping was FOUND.
Phase 1's gate is open.**

### They are not the same space, and it is not close
Across **3,300 build entries / 1,054 distinct `entry_id`s** from 12 scouted characters and the
48-character Phase 1 baseline:

| Test | Result |
|---|---|
| `entry_id` present as a catalog `spells.id` | **1 / 1,054** |
| …and that one agrees on name | **0** — id `50043` is `Ghostly Finish` in the crawl and `Chilblains` in the catalog |
| crawled name found in the catalog | 1,053 / 1,054 |
| …with catalog id **equal** to `entry_id` | **0** |

The single numeric collision is a false friend — exactly the trap 1d's hard rule exists for. **Never
join `entry_id` to `spells.id`.**

They are structurally different: **`entry_id` is rank-independent** (83 ids observed at more than one
rank; one id spans ranks 1–3, with rank carried in a separate field), while `spellId` is
**rank-specific**. One is a card; the other is a spell rank.

### ✅ The mapping is `CharacterAdvancement.dbc`, and it is now extracted
Directly confirmed against the three CA IDs read from in-game tooltips in an earlier session:

| CA / `entry_id` | Expected | Observed in crawled builds |
|---|---|---|
| 40094 | Arcane Intellect | Arcane Intellect ✓ |
| 40017 | Mend Pet | Mend Pet ✓ |
| 40050 | Shadow Bolt | Shadow Bolt ✓ (the `INDEX_GUIDE` v4 sample) |

**The 1f hypothesis is confirmed.** Layout, reverse-engineered against those anchors:

| Slot | Meaning |
|---|---|
| 0 | CA id — **this is the crawl's `entry_id`** |
| 1 | type (`Talent` 6,169 / `TalentAbility` 399 / empty) |
| 2, 3 | prerequisite CA ids |
| **5–9** | **`SpellRank[5]` — the spellId per card rank** |
| 16/20/24 (+17/21/25) | **rarity** ×3 — Poor/Normal/Uncommon/Rare/Epic/Legendary/Artifact |
| 26/27/28 | required levels | 
| 47 / 64 / 65 | name / icon / description |

Every other non-zero int slot is stored verbatim in `raw_ints_json` rather than guessed at.

### Validation
| Check | Result |
|---|---|
| crawled `entry_id`s resolving in `CharacterAdvancement.dbc` | **1,054 / 1,054** |
| scouted entry names agreeing with the CA `name` field | **660 / 660** |
| CA records whose slot-5 spell is a real `Spell.dbc` id | **10,231 / 10,231** |
| multi-rank arrays where all ranks share one `Spell.dbc` name | 2,379 (**2** mixed) |
| multi-rank arrays reading Rank 1,2,3… in order | 2,361 of 2,381 |
| catalog ids reachable from some CA rank slot | **3,061 / 3,061** |

The 2 mixed arrays are genuine renames, not errors, and are a useful warning: **the rank chain is
authoritative, the name is not.** (`Improved Spell Reflection` R3 is named `Shield Cover`; `Focus` R2
is named `Primal Focus`.)

### The join, stated plainly
```
crawl.entry_id  ->  dbc_character_advancement.ca_id
                ->  .spell_rank_<N>          (N = the card rank the character holds)
                ->  spells.id / spell_dbc_raw.id
```
**Talent cards** fill 2/3/5 rank slots (max_rank distribution: 1→7,850, 2→883, 3→1,222, 4→1, 5→275).
**Ability cards fill only slot 5** — an ability's *spell* rank is resolved by character level instead,
not by the card. See the rank section below.

### 🛑 What this means for Phase 1 Task 4's primary key
`spell_mechanics` should be keyed **`(spell_id, rank)`** as already planned, and the builds repo
should key on **`ca_id`** and join through `dbc_character_advancement` — never by name, never by
assuming id identity.

### 🎯 Bonus: crawled `per_rank_text` resolves magnitudes the catalog leaves as `$placeholders`
Of the 1,054 entries held, 931 have a catalog tooltip containing `$s1`-style placeholders. The
crawl's `per_rank_text` **fully resolves 838 of them (90%)** — and for talents it does so **at every
rank**, not just the held one.

```
Improved Cleave  R1 "…by 40%."   R2 "…by 80%."   R3 "…by 120%."
Catalog:            "…by $s1%."
```
That independently corroborates the +40%/rank Improved Cleave figure `build_paladin-hammerdin.md` v9
derived from raw DBC — two sources, same answer.

Residual unresolved even in crawl text: `$h` (proc chance), `$i` (chain targets), `$<id>d`
(cross-spell duration). Notably **`$i` is target count** — the same quantity Task 2 could not find.

⚠ **For abilities the crawl gives Rank-1 text only** (Arcane Intellect shows "+2 Intellect", the
Rank 1 value, not Rank 5's "+31"). Armory captures do **not** reveal which spell rank a character
casts. Only the level rule below does.

---

## Rank resolution (cross-cutting — Tasks 1, 4, 5)

**Verdict: CONFIRMED. The contiguous-id rule is DISPROVEN.**

### ✅ Level determines the rank
A character holds the **highest rank in the line whose `SpellLevel` ≤ character level**. Reproduces
both in-game tooltips previously captured:

| Line | Level-60 answer | Matches the owner's tooltip? |
|---|---|---|
| Holy Supernova | `270187` **Rank 6**, `SpellLevel` 60 | ✅ yes |
| Winds of Winter | `274132` **Rank 5**, `SpellLevel` 58 | ✅ yes |
| Arcane Intellect | `10157` **Rank 5**, `SpellLevel` 56 (R6 is level 70) | ✅ yes |

Extracted into **`dbc_spell_rank`** (42,606 ranked spells in 12,779 lines, 6,699 multi-rank), so this
is a query rather than a judgment call.

Rank lines are grouped on **(name, skill lines, mechanical fingerprint)** — school, cooldown, radius,
cast-time index, effect structure — never on name alone, per 1d.

### ❌ The contiguous-id rank rule does not hold
| | lines |
|---|---|
| contiguous ids | 1,908 |
| **non-contiguous** | **4,791** |

Winds of Winter is the clean counterexample: R1 `274121`, then R2–R8 at `274129`–`274135`. The
provisional rule in `PHASE_0` §1f must be **dropped**, and the primer §5 heuristic ("check ±1–3 of an
unresolved id") is unsafe as a general rule — it worked on the lines it was tried on. Use
`dbc_spell_rank`.

### 🚨 Consequence: ≈50% of the multi-rank catalog carries the wrong magnitudes
**697 of 1,409** catalog entries in a rank line are stored at a rank a level-60 character does not
hold, and in **all 697** the correct id is absent from the catalog. Examples: Blizzard (catalog R1,
level-60 R6), Power Word: Shield (R1 → R10), Mend Pet (R1 → R7), Cone of Cold (R1 → R6).

Sensitivity across four grouping strictnesses: **697–794**. The conclusion is robust to the method.

### 1d's duplicate-name trap — mechanism now explained
The two "Holy Supernova" lines are two separate CA cards: CA 36394 → `270182`… (cd 40s, radius index
18) and CA 1397 → `81191`… (cd 50s, radius index 13). `81193` is **Rank 3 of the second line**.
Same name, unrelated cards — the fingerprint rule was right, and now there is a structural reason.

Likewise the retracted "11 prefix" ID space is real but is a **parallel skill-line family**: Mend Pet
`136` sits on skill line 50; `1100136` sits on skill line **11050**. Consistent with 1f's conclusion
that these belong to another realm/mode. **Still out of scope — do not build a crosswalk for them.**

---

## Task 7 — the official builder

**Verdict: CONFIRMED that a complete, coefficient-carrying catalog exists — but it is
realm-scoped to Area-52 and Elune, NOT Darkmoon.**

`https://ascension.gg/en/v2/builder/area-52` is a Next.js app that embeds its **entire catalog** in
the server-rendered payload — an **11.9 MB inline script**. No separate API call, no auth. Every
field Task 7 hoped for is present:

```json
{"id":599,"name":"Brambles","required_level":20,"quality":1,
 "quality_essence_cost":1,"ability_essence_cost":0,"talent_essence_cost":1,
 "row":2,"column":1,"ranks":3,
 "spells":[{"id":16836,"description":"<fully resolved, per rank>",
            "search_description":"<raw $s1 template>",
            "recovery_time":0,"cast_time":0,"duration":0,"range":0,
            "power_type":0,"mana_cost":0,"mana_cost_percentage":0,
            "bonus_data":null,"rarity":1}, …]}
```
- **`bonus_data` = `{direct_bonus, dot_bonus, ap_bonus, ap_dot_bonus}`** — explicit SP/AP
  coefficients, direct and DoT, on 622 entries
- **`rarity`** on 5,736 entries; `quality`; `required_level`
- **`ability_essence_cost` / `talent_essence_cost` / `quality_essence_cost`** on 3,259 entries —
  a real **acquisition-cost model input** for Phase 4, from the game's own authors
- **`spells[].id` is a real spellId per rank**, and `description` is resolved per rank while
  `search_description` keeps the raw template — both sides of the magnitude problem in one record
- `enchants` (Mystic Enchants), `worldforged`, `condition`, `max_stack`, `schema_version`

### ⛔ But: only two realms exist in it
`{"id":2,"slug":"area-52",…,"max_level":70}` and `{"id":18,"slug":"elune",…}`. `/v2/builder/darkmoon`
**redirects to the homepage**. Darkmoon's `max_level` is 60; these are 70.

**Per §2.5, this data may not be applied to Darkmoon.** Its value is (a) proof of what the server
holds and in what shape, (b) an independent cross-check on coefficient *modelling*, (c) the essence-cost
concept. It is **not** a Darkmoon card source.

### Build string
`localStorage.ascension_last_build` = `{"loaded_uuid":"","data":"::","realm":"area-52"}` — a
**colon-delimited id encoding**, not an opaque blob, so it is readable and writable. Full field
spec needs one populated build; not worth more clicks until a Darkmoon builder exists.

---

## Task 9 — BisBeard 🛑

**Verdict: CONFIRMED as an integration target. Phase 3 T4 should be re-scoped, not cancelled.**

`s10.bisbeard.com` is a Vite/React SPA that never rendered past "Loading…" in the automated pane, so
findings come from its **code chunks**, read-only. No dataset was copied into this repo; only counts
and identifiers were measured.

Its chunk names are self-documenting:

| Chunk | Bytes | What it is |
|---|---|---|
| `realmDataS10-*.js` | 1,547,157 | **The S10 card dataset** |
| `App-*.js` | 976,165 | The app |
| `itemDatabaseSync-*.js` | 95,150 | Item sync — references `wotlkdb.com` and `db.ascension.gg` |
| `s10Calculation-*.js` | 76,568 | **The talent→character-sheet audit engine** |
| `LootBrowser-*.js` | 36,868 | Loot UI; references `sr.bisbeard.com` |

### 1. 🎯 It keys on `entryId` — independent corroboration of Task 5
`realmDataS10` contains **3,226 `entryId`s** with fields `kind`, `class`, `quality`, `name`,
`iconName`, `tooltip`, `isPassive`, `requiredLevel`, `maxRank`, `abilityEssenceCost`,
`talentEssenceCost`, `primaryStatRequirement`, `requiredSpecializations`, `sourceOrder`.

**No `spellId` anywhere.** A separately-maintained community tool independently concluded that the
CharacterAdvancement ID is the canonical S10 card key. Its id range (5..138346) and bucket
distribution match our `CharacterAdvancement.dbc` extract, **max id identical at 138346**.

**Useful bound:** BisBeard's S10 set is **3,226** vs our CA table's 10,231 and the catalog's 3,061.
So the CA table's extra ~7,000 records are **not** all playable S10 cards — they include other
realms'/modes' entries. ⚠ This tempers any "the client has 3.7× more cards" reading. The exact
S10-playable subset is a cheap follow-up: intersect BisBeard's id list with our CA ids.

### 2. ✅ Stat weights are a first-class, supplied input
`configStatWeights`, `defaultWeights`, `normalizedWeights`, **`weightString`**, `includeWeights`,
`allowWeights`, `isWeightModalOpen`. A `weightString` implies a parseable, shareable weight encoding.

**This closes ARCHITECTURE §2.11's integration loop**: our sim derives stat weights (nothing else
has a simulator), and BisBeard consumes weights to do BiS. The handoff is real, not aspirational.

### 3. ✅ An independent `compute_stats()` to cross-check against
`s10Calculation` opens with the five Paths verbatim —
`["Duality","Intelligence","Strength","Agility","Healing"]`, class `"Hero"` — and carries `formula`,
`operation`, `ruleId`, `severity`, `stat`, and per-stat handling for intellect/agility/strength/spirit.
Exactly the "audited talent-driven character-sheet stats" the task hoped for, and precisely the
correctness risk Phase 2 T4 carries. Spot-checking a few builds by hand against it is cheap.

### 4. ⚠ The item dataset — path found, host not resolved
`itemDatabaseSync` references **`/data/wotlk/items/phase-1-items.json`** — a plain JSON path, and
**phase-tagged in the filename**, which is exactly what §2.10's per-phase gear tiers need. That path
returns the SPA shell on `s10.bisbeard.com`, `bisbeard.com` and `sr.bisbeard.com`.

**Probing stopped there deliberately** — hunting for the right host by guesswork is precisely the
crawling behaviour the courtesy note warns against. Two better routes: read the fetch call's base-URL
construction in the chunk, or ask the author.

### 🛑 Phase 3 Task 4 re-scope
The pieces line up, but one is unresolved, so:
- **Do NOT build a competing gear optimizer.** Confirmed: BisBeard does items, phase tagging and BiS,
  and takes stat weights as input
- **Do build the stat-weight derivation** (Phase 2 T7) — it is the input nobody else can produce
- **Gear data for the sim's three gear tiers (§2.10) is not yet sourced.** Two candidates: BisBeard's
  item JSON (host unresolved), or the client's own `Item.dbc` + `ItemStat.dbc` (**1.5M records,
  confirmed present, layout unverified**). The client route needs no one's permission and is probably
  the honest default

---

## Pre-Phase-1 follow-ups (resolved 2026-08-04, after the main pass)

Three questions were judged cheap, local, and schema-shaping enough to answer before closing
Phase 0 rather than carrying into 1a. All three came back clean.

### ✅ A1 — the CA table DOES carry a playable-pool discriminator

**This decides whether Phase 1 ingests ~3.1k cards or all 10,231.** Slot 121 is a packed 4-byte
field; **byte 2 (`(v >> 8) & 0xFF`) separates the currently-playable pool from everything else.**
Now materialised as `dbc_character_advancement.in_current_pool` (+ `pool_flags_raw`).

| byte 2 | records | ever seen on a live Darkmoon character |
|---|---|---|
| **1** | **3,129** | **1,054** |
| 0 | 5,705 | 0 |
| *(field absent)* | 1,397 | 0 |

Four independent lines of evidence, none of them documentation:

1. **All 1,054** observed entry_ids have byte2 == 1. Not one of the 5,705 byte2==0 records has ever
   been seen on a real character.
2. **Size agrees with an independent source**: 3,129 vs BisBeard's separately-maintained S10 count of
   **3,226** — a 3.0% gap — and the catalog export's 3,061.
3. **Semantics**: the kept set contains **all five Paths** by name; the excluded set is full of
   retail WotLK class abilities (Ferocious Bite, Lava Burst, Ignite, Improved Fireball, Mind Sear).
4. **It resolves the duplicate-name trap structurally.** "Holy Power" and "Titan's Grip" each appear
   **three times** in the CA table — once per byte2 group — and exactly one of each is in the pool:

   | CA id | name | `pool_flags_raw` | in pool | → spell |
   |---|---|---|---|---|
   | **40876** | Titan's Grip | `0x01010101` | **1** | 46917 ← *the id the crawl actually uses* |
   | 3622 | Titan's Grip | 0 | 0 | 46917 |
   | 12455 | Titan's Grip | `0x01010000` | 0 | **1146917** |

   That third row lands in the **"11-prefix" realm-variant ID space** — independently tying §1f's
   retraction ("those belong to another realm") to this flag.

⚠ **Do not read byte2 as meaning "Darkmoon" specifically.** Only Darkmoon data exists to test
against; it could equally mean current-season or classless-mode. The honest label is *the currently
playable pool*. And **97 cards of BisBeard's count are unaccounted for** — that gap is unexplained.

### ✅ A2 — combat logs use the plain client `Spell.dbc` ID space. There is no fifth space.

Parsed **5 real logs** from the owner's machine (~130k spell events): **809 distinct
`(spellId, name)` pairs, and 809/809 ids are present in the full `Spell.dbc`**, with **808/809 names
agreeing exactly**.

The single "mismatch" is **my parser's fault, not the data's**: the log is comma-separated and the
spell name *"Earth, Wind, and Fire"* contains commas, so a naive `split(',')` truncated it to
"Earth". 🆕 **Trap for the Phase 3 T6 log parser: Ascension spell names contain commas — the log must
be read with a quote-aware CSV parser, never a plain split.**

**0b's `9931032` lead is resolved**: "PvE Mode" *is* in `Spell.dbc`. It only looked alien because the
client's id space runs to **13,977,920** — 9.9M is unremarkable. The four known ID spaces stand; no
fifth one exists.

⚠ **Scoping fact for Phase 3**: only **114 of the 809** logged ids are catalog `spells.id` — the
catalog covers ~14% of what actually appears in combat logs.

### ✅ A3 — the `gt*` tables are unmodified retail values, and the extraction is validated

`gtCombatRatings` at level 60 gives **CRIT_MELEE = CRIT_RANGED = CRIT_SPELL = exactly 14.0000** —
matching the primer's independently *measured* 14.0 rating per 1% crit, and matching its "identical
for melee and spell" claim literally (they are the same numbers in the table).

The level curve reproduces canonical retail exactly — level 70 = **22.0769**, level 80 = **45.9060** —
which also **validates the row-index decoding** (`ratingType × 100 + level − 1`), since it reproduces
both a measured in-game value and the known retail constants.

**Phase 2 can use these directly rather than assuming.** Ready-made level-60 conversions:

| Rating | per 1% | | Rating | per 1% |
|---|---|---|---|---|
| Crit (melee/ranged/spell) | **14.0** | | Haste (all) | 10.0 |
| Hit — melee/ranged | 10.0 | | Expertise | 2.5 |
| Hit — spell | 8.0 | | Armor penetration | 4.2 |
| Dodge / Parry | 13.8 | | Resilience (melee) | 85.0 |

---

## Retractions (§2.6 — these are data)

| Retracted claim | Where it lived | What falsified it |
|---|---|---|
| **"Spell 274132 is absent from the client DBC"** (and the framing of it as "two independent absences" alongside db.ascension.gg) | `PHASE_0` Task 4 item 1 | It is present as **Winds of Winter Rank 5**. The absence was an artifact of `spell_dbc_raw`'s ±3 id scoping, which excluded non-contiguous rank siblings |
| **"The contiguous rank rule" (`rank1_id + (rank-1)`)** — provisional | `PHASE_0` §1f | 4,791 non-contiguous rank lines vs 1,908 contiguous. Winds of Winter R1 `274121` → R2 `274129` |
| **"The hidden-formula resolver runs the full list every invocation, not incremental"** | `INDEX_GUIDE` v3 | It was incremental *and* destructive — a second run deleted all 113 rows and re-derived none. Fixed |
| **"db.ascension.gg requires JS"** | pre-Phase-0 belief | Already retracted in Phase 0; recorded here as the first `retractions` row per Task 8 |
| **"The fight-level per-ability endpoint does not exist"** | `INDEX_GUIDE` v4 "Known gaps" | Contradicted by v7's own changelog; the endpoint works. `INDEX_GUIDE` self-contradiction fixed this session |

---

## Open questions carried into Phase 1

Seed these into `open_questions` (Phase 1 Task 6).

| Question | Blocks | How to settle |
|---|---|---|
| ~~Which ID space does the client's own `WoWCombatLog.txt` use?~~ | — | ✅ **ANSWERED** — plain client `Spell.dbc` space, 809/809. See A2 |
| ~~Exact S10-playable subset of the 10,231 CA records~~ | — | ✅ **ANSWERED** — `in_current_pool` flag, 3,129 records. See A1. Residual: the 97-card gap vs BisBeard's 3,226 |
| Where is BisBeard's item JSON actually served from? | Phase 3 T4 gear source | Read the base-URL construction in `itemDatabaseSync`, or ask the author |
| Are `Item.dbc`/`ItemStat.dbc` layouts stable enough to extract? | Gear database without third-party dependency | Extract a handful of known items and compare against in-game tooltips |
| Which of the 5 class conflicts is right? | `class_origin` correctness | Proc-test, or a live tooltip read on each |
| ~~Do the `gt*` tables match retail values at level 60?~~ | — | ✅ **ANSWERED** — unmodified retail; crit = exactly 14.0 at level 60. See A3 |
| What do CA slots 14/15/17/21/25/29–41 mean? | Acquisition/prerequisite modelling | Correlate `raw_ints_json` against known card properties |
| Does `stats_summary.sourcesByStat` itemise per-source contributions? | Could settle Path of Duality from captured data | Inspect the field in `baseline_phase1/characters.jsonl.gz` — **carried over from 0b, still not done** |
| What is the current maximum report ID? | Sizes the backfill | Emerges from a full crawler run |
