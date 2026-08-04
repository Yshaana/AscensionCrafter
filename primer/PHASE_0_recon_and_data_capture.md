# PHASE 0 — Recon & Start Capturing (v3)

**Read `ARCHITECTURE.md` first.**

---

## ✅ PHASE 0 IS COMPLETE (2026-08-04). Verdicts live in `primer/RECON_FINDINGS.md`.

Read that file, not this one, for what was actually found. This document is the **brief**; it is kept
for its reasoning, and amended in place where reality contradicted it.

> ⚠ **Two numbers in here and in `RECON_FINDINGS.md` were refined by session `1a`** — the wrong-rank
> catalog count is **711, not 697** (with 25 lines genuinely ambiguous), and the fingerprint rule
> needs **two** field sets, not one. Both because the original reporter used `max()`, which silently
> takes the first of a tie. See the correction block at the top of `RECON_FINDINGS.md`.
>
> ⚠ **Paths here are pre-restructure.** `index/` no longer exists — see the v20 changelog in
> `Ascension_Context_Primer.md` for the old→new map. Task 6's crawler is now **scheduled** (at logon,
> once a day, `SCHEDULING.md`); the "manual-first" posture this doc specifies was satisfied and
> retired on 2026-08-04.

| Task | Verdict | Session |
|---|---|---|
| 1 — db.ascension.gg | CONFIRMED earlier; closed to further automated work by policy (§1a robots) | prior + 0a |
| 2 — ascensionlogs.gg endpoints | CONFIRMED map; ⚠ target count must be **inferred**; ❌ per-parse stats do **not** exist | 0b + 0a |
| 3 — changelog | CONFIRMED as change history; ❌ **not** a new-card discovery source; ❌ **not** a phase-timeline source | 0b + 0a |
| 4 — DBC re-run | CONFIRMED. 🚨 **98% of the 803 blocked spells resolve from numeric fields** | 0a |
| 4a — SkillLineAbility | CONFIRMED, via skill-line **names** not ClassMask. 13% → **58%** class coverage | 0a |
| 5 — crosswalk 🛑 | **RESOLVED — Phase 1's gate is open.** `entry_id` = CharacterAdvancement ID, never join to `spells.id` | 0a |
| 6 — crawler | ✅ built and running | 0b |
| 7 — official builder | CONFIRMED rich catalog + coefficients + essence costs — but **Area-52/Elune only, not Darkmoon** | 0a |
| 8 — doc fixes + write-up | ✅ done | 0a |
| 9 — BisBeard 🛑 | CONFIRMED integration target. **Phase 3 T4 re-scoped**, gear source still open | 0a |

### ⚠ Three claims in the body below are WRONG and are corrected inline
1. **Task 4 item 1's "274132 is absent"** — it exists, as Winds of Winter **Rank 5**.
2. **§1f's contiguous rank rule** — disproven (4,791 non-contiguous lines vs 1,908 contiguous).
3. **Task 1's "fetch ~30 spells"** — superseded by §1a's robots finding before it was ever run.

**Purpose:** answer every open question about what data is actually reachable, and in what form,
before a single table is designed — and get capture running so data starts accruing today.

**No schema design in this phase.** The only code built is a deliberately crude crawler (Task 6) and
a changelog parser (Task 3). Their output formats are allowed to be ugly — raw capture gets reshaped
later.

**Output:** `primer/RECON_FINDINGS.md`, one section per task, each ending in a definitive
**CONFIRMED / DISPROVEN / BLOCKED** verdict with evidence. Not "probably." A BLOCKED verdict with a
stated reason is a fine outcome — a question *known* to be unanswered is safe; one that's assumed is
not.

---

## Task 1 — `db.ascension.gg`: map what's reachable without a browser

**Correction to standing project belief.** This site is documented as requiring JS and therefore
unreachable from a plain fetch. **That is wrong.** A plain HTTP GET of
`https://db.ascension.gg/?spell=276076` returns a server-rendered **Spell Details** table with
school, mana cost, range, cast time, cooldown, GCD, weapon requirements, and numbered Effect entries.
Verified 2026-08-04.

Two further observations from the same check:
- `?spell=274132` **redirects to the homepage** — that ID doesn't exist in their database. A
  redirect-to-home is the "not found" signal; detect it, don't parse the homepage as a spell.
- The **Related** section is empty on a plain fetch — that part *is* JS-loaded.

**Do:**
1. Fetch ~30 spells spanning ability / talent / mystic enchant / proc types. Determine exactly which
   fields are reliably server-rendered vs. sometimes absent.
2. **Determine whether damage formulas / spell scaling appear in server-rendered output**, or only
   via JS. This is the single most valuable field and the main reason the site matters.
3. Find whether an unauthenticated JSON endpoint exists. This codebase is **Aowow** (the open-source
   Wowhead clone); Aowow conventionally exposes tooltip data under patterns like `?spell=X&power`
   and list data under `?spells&filter=...`. Test these. A JSON endpoint beats HTML parsing on every
   axis.
4. Check whether **Mystic Enchants** are their own entity type, and whether classless cards have a
   URL space distinct from spells.
5. **Check for item pages.** If items are server-rendered too, this is a canonical item database for
   Phase 3's gear optimizer — better than reconstructing one from crawled gear alone.
6. Establish the polite request rate. This will eventually be crawled at catalog scale (3,000+).

**Conflict to log, not resolve:** the site reports Fel Infused Weapon (276076) as school **Fire**;
project docs say **Shadowflame**. Record as a `conflict` for Phase 1's verification queue. Do not
"correct" either source here.

### ⚠ 1a — robots.txt disallows automated access

Discovered 2026-08-04: after roughly **2–3 automated requests**, `db.ascension.gg` returns a
robots-disallowed response. **Plain-HTTP fetching works technically, but the site asks not to be
crawled and rate-limits aggressively.**

**This downgrades the plan.** db.ascension.gg is *not* a bulk source. Treat it as source tier 3 for
**targeted, low-volume, manual lookups only** — the ~50 spells that actually matter for a build, not
3,000. If catalog-scale coverage is genuinely needed, ask the site operator rather than working
around the robots rule. Update §2.2's tier-3 note accordingly.

### ✅ 1c — CONFIRMED: db.ascension.gg carries damage coefficients, on catalog-compatible IDs

This was Task 1's most important open question. **Answer: yes**, as clean numeric fields in
server-rendered HTML. Verified on Holy Supernova (`?spell=270182` — the same ID the catalog uses):

```
Scaling #1   +24.15% of spell power to direct component
Scaling #2   +15.70% of attack power to direct component
Effect #1    School Damage: Value 61 to 69, plus 0.6 per level, Radius: 15 yards
Cost 20% of base mana | Cast time 2 seconds | Cooldown 40 seconds | GCD 1.5 seconds
```

**The db uses the same ID space as the catalog and the client** — `270182` and `136` both resolve
there identically. There is no separate db ID space. (An earlier draft of this task claimed a "fifth
ID space" based on `81193` also being named Holy Supernova; that was wrong — see §1d.)

Combined with the rate limit above, this makes db.ascension.gg the **best available source for the
specific spells a build depends on** — high quality, low volume. Plan around per-build lookups, not
sweeps.

**Small conflict to log:** the catalog tooltip gives Holy Supernova's AP term as `0.159`; the db
gives `15.70%`. Same ID, same rank. Record both, `confidence='conflict'`, and resolve from a live
tooltip.

### 🚨 1d — THE DUPLICATE-NAME TRAP, caught live — READ THIS BEFORE RELATING ANY TWO IDs

**Two spells on db.ascension.gg are both named "Holy Supernova." They are not the same ability and
not two ranks of one ability.**

| | `270182` (the real one) | `81193` (a different spell) | In-game `270187` |
|---|---|---|---|
| SP coefficient | 24.15% | 30.13% | — |
| AP coefficient | 15.70% | 19.58% | — |
| Base damage | 61–69 | 131–153 | 737–856 |
| **Radius** | **15 yd** | **10 yd** | **15 yd** |
| **Cooldown** | **40 s** | **50 s** | **40 s** |
| Cast time | 2.00 s | Instant | 1.61 s (haste-adjusted — see §1e) |

`270182` matches the owner's live ability on **both** radius and cooldown. `81193` matches on
neither, and differs in cast type. Same name, unrelated spells.

**This produced a real, retracted error in this very session:** an earlier draft concluded
"coefficients scale with rank" by comparing `81193`'s 30.13% against `270182`'s 24.15%, and proposed
re-keying `spell_scaling` on the strength of it. Both the conclusion and the schema change were
withdrawn. Rank-scaling of coefficients may well be true — but nothing here is evidence for it, and
it must be established from two confirmed ranks of the *same* ability line.

**🛑 HARD RULE — never relate two spell IDs by name.** Before treating two IDs as the same ability,
a variant, or two ranks, **fingerprint them on mechanics**: radius, cooldown, cast type, resource
cost, effect structure, school. A name match is evidence of nothing.

This trap has now caught confident reasoning **twice in one session** — first the `1111294` "Wildcard
variant" prefix (§1f), then this. Both times the failure mode was identical: same name + different ID
was assumed to mean "related," when the primer's standing warning (Ascension's Mental Quickness ≠
WotLK's Mental Quickness; two different "Cruelty" ranks) says the opposite is the safe default.
Encode the fingerprint check in the crosswalk resolver, not as a doc convention.

### 1e — In-game tooltips show HASTE-ADJUSTED values, not base values

Holy Supernova's base cast time is **2.00 s** (db); the owner's in-game tooltip reads **1.61 s**.
`2.00 ÷ 1.61 ≈ 1.24` — approximately 24% haste. The apparent conflict resolves cleanly and gives a
rule worth encoding:

**A tooltip read is a measurement of the character, not of the spell.** Any in-game tooltip captured
as evidence must record the character's haste (and any other relevant multipliers) alongside it, or
the number cannot be interpreted later. Applies to the capture addon (Phase 3 T5), to manual tooltip
reads feeding source tier 1, and to scouted per-rank tooltip captures.

**Corollary:** this is a plausible route to *measuring* stats — a known base value plus an observed
tooltip value yields the character's effective modifier. Worth noting as a technique; not a task yet.

🎯 **Still open: which ID space does the server actually use in combat logs?** Whatever
`ascensionlogs.gg` reports per-ability damage in is canonical. Resolve in Task 2.

### 1f — ID SPACES (revised 2026-08-04 after in-game verification)

**❌ RETRACTED: the "11 prefix / Wildcard variant" hypothesis.** An earlier draft of this task
claimed live Wildcard spells use prefixed IDs derived from max-rank base IDs (`11294 → 1111294`).
**Four in-game tooltips disprove it** — every live ID is plain:

| Ability | In-game ID | Note |
|---|---|---|
| Arcane Intellect Rank 1 | `1459` | canonical WotLK ID |
| Arcane Intellect Rank 5 | `10157` | canonical WotLK ID |
| Mend Pet Rank 1 | `136` | canonical WotLK ID |
| Holy Supernova Rank 6 | `270187` | Ascension original, plain high ID |

`1111294` is therefore **not** a Wildcard ID. Supporting evidence: base `11294` carries Elune *and*
Area52 PvP-mod blocks while `1111294` carries none — the prefixed variant most likely belongs to a
different Ascension realm (Bronzebeard / CoA). **Do not build a `wildcard_variant` crosswalk.** If
worth resolving at all, treat it as "which realm does this ID belong to," not "which variant of ours."

### The four ID spaces that DO exist

| Space | Example | Notes |
|---|---|---|
| **`spellId`** | 1459, 270187 | Catalog **and** in-game agree. **Rank-specific** — each rank has its own ID |
| **`CharacterAdvancement ID`** | 40094, 40017 | Shown in in-game tooltips. ~40000 range. **See the hypothesis below** |
| **`cardId`** | 26572, 12294, 12045 | From `Cards.txt`. **Multiple per spellId** (owned copies across Normal/Golden pools) |
| Realm-variant IDs | 1111294 | Another realm's space. Out of scope |

### 🎯 Likely resolution of a long-open question

`INDEX_GUIDE` v4 records the scouted sample's `entry_id` for Shadow Bolt as **40050** — the same
range as the verified CharacterAdvancement IDs above. Shadow Bolt's `spellId` is 686; its `cardId`s
are 26542 / 12277 / 24322 / 26543. None match.

**Hypothesis: `scouted_build_entries.entry_id` = CharacterAdvancement ID, NOT `spells.id`.**

✅ **CONFIRMED (0a), and the mapping table was found: `CharacterAdvancement.dbc` is in the client**
(10,231 records). `ca_id` = `entry_id`; slots 5–9 are `SpellRank[5]`, the spellId per card rank.
All three in-game CA IDs match crawled build entries (40094 Arcane Intellect, 40017 Mend Pet,
40050 Shadow Bolt); 1,054/1,054 crawled entry_ids resolve; 660/660 names agree; 0 of 1,054 entry_ids
equal a catalog `spells.id`. The answer to the question open since INDEX_GUIDE v4 is exactly the one
predicted here: **different spaces, never join directly.** The task's "determine whether the addon or
client can dump a mapping" is answered — the client ships it as a DBC.

**Test it (this is now the highest-priority part of Task 5):** collect CharacterAdvancement IDs for
~10 abilities from in-game tooltips, then check whether they appear as `entry_id` in the committed
scouted JSON for characters known to run those abilities. If confirmed, the answer to the
"entry_id ↔ spells.id correspondence" question open since INDEX_GUIDE v4 is **"different spaces,
never join directly"** — and the crosswalk needs a real CA↔spellId mapping, which is not currently in
any local file. Determine whether the addon or the game client can dump one.

*(Checked and rejected: CA ID is not derivable from catalog ordinal position — Mend Pet is catalog
ability #18 with CA 40017, Arcane Intellect is #108 with CA 40094. The offset grows, so the CA list
contains entries our catalog does not. A real mapping is required.)*

### Rank IDs — two apparent regimes, one confirmed, one provisional

| Regime | Example | Rule | Status |
|---|---|---|---|
| **Ascension originals** | Holy Supernova R1 `270182` → R6 `270187` | ~~**Contiguous:** `rank1_id + (rank − 1)`~~ | ❌ **DISPROVEN (0a).** 4,791 rank lines are non-contiguous vs 1,908 contiguous. Holy Supernova happens to be contiguous; **Winds of Winter is not** — R1 `274121`, then R2–R8 at `274129`–`274135` |
| **Classic WotLK spells** | Arcane Intellect R1 `1459` → R5 `10157` | **Scattered** — requires DBC rank chains | ✅ Confirmed from two in-game tooltips |

✅ **REPLACED BY A RULE THAT DOES HOLD (0a): rank is level-gated.** A character holds the highest
rank in the line whose `SpellLevel` ≤ their level. Verified against both captured in-game tooltips
(Holy Supernova → `270187` R6 at `SpellLevel` 60; Winds of Winter → `274132` R5 at 58). Extracted
into `dbc_spell_rank`, with lines grouped on (name, skill lines, mechanical fingerprint) per §1d —
never name alone. **The primer §5 "check ±1–3 of an unresolved id" heuristic is not safe in general.**

🚨 **And the consequence is large:** 697 of the 1,409 catalog entries sitting in a multi-rank line
(≈50%) are stored at a rank a level-60 character does not hold, with the correct id absent from the
catalog entirely. That is the answer to this task's "report how many catalog entries the owner
actually plays at a rank the catalog doesn't carry."

**Confirm the contiguous rule properly before relying on it**, and apply §1d's fingerprint rule when
you do: check that `270183`–`270186` are Holy Supernova **and share radius, cooldown, cast type, and
effect structure** with `270182`/`270187`. Two IDs being adjacent and same-named proves nothing —
`81193` is also named Holy Supernova and is a different ability entirely.

Note also that `81193` was labelled "Rank 3," so **that** ability has its own rank block somewhere.
Sequential IDs near a known spell may belong to a same-named but unrelated line.

This replaces the primer's §5 heuristic ("check ±1–3 of an unresolved ID") with a testable rule for
one regime and an explicit lookup requirement for the other — but only once the first is confirmed.

### 🚨 The catalog stores Rank 1 only — this is a first-order data trap

Verified: `spell-export.json` holds Arcane Intellect at `1459` (**Rank 1**) and does not contain
`10157` (Rank 5) at all. It holds Holy Supernova at `270182` (**Rank 1**) and not `270187` (Rank 6),
**an ability the project owner actively plays.**

| | Catalog (Rank 1) | In-game (Rank 5) |
|---|---|---|
| Arcane Intellect | +2 Intellect, +2 spell power | **+31 Intellect, +27 spell power** |

**A ~15× gap.** Any analysis reading magnitudes from the catalog for a max-rank card is wrong by an
order of magnitude. Catalog rank distribution overall: 1,369 `None`, 678 `Rank 1`, 438 `Rank 3`, 205
`Rank 2`, 84 `Rank 5` — so rank coverage is partial and inconsistent, not uniformly Rank 1.

**Consequences, all mandatory:**
- `(spell_id, rank)` keying on `spell_mechanics` is confirmed necessary, not defensive
- The resolver must **refuse** to serve a Rank-1 magnitude for a higher-rank query rather than
  silently returning it — enforce in code
- Per-rank tooltips from the scouted crawl and from in-game reads become a **primary** source for
  played-rank magnitudes, not a cross-check
- Report how many catalog entries the owner actually plays at a rank the catalog doesn't carry

### ⚠️ Ascension edits spells in place

Retail WotLK's Arcane Intellect grants Intellect only. Ascension's grants Intellect **and spell
power**, under the same ID `1459`.

**So: a classic-range ID means the CLASS carries over. It does not mean retail's numbers, or even
retail's effects, carry over.** Task 4a's class resolution stays valid; nothing else about the retail
spell may be inherited. Write this into the resolver as a hard rule.

**Verdict needed:** can this serve as source tier 3 at catalog scale via plain HTTP, and does it
carry damage coefficients?

---

## Task 2 — `ascensionlogs.gg`: confirm the full endpoint map

`INDEX_GUIDE.md` currently **contradicts itself**: v7's changelog documents a working per-ability
encounter endpoint, while its "Known gaps" section still lists that capability as not found. Resolve
and fix the doc.

**Confirm each works today:**

| Endpoint | Confirms |
|---|---|
| `/api/reports/{id}/character_spell_damage?scope=encounter&encounterIds=&format=flat&limit=10000&participantType=friendlies` | Per-ability hits / crits / damage per character per encounter |
| `/api/reports/{id}/character_damage_taken_abilities?...&participantType=enemies` | **Avoidance**: miss/dodge/parry/resist/resist_full/immune per player ability |
| `/api/reports/{id}/character_damage_taken_abilities?...&participantType=friendlies` | Damage the raid *took* — needed for tank/healer/solo modelling (§2.8) |
| `/api/reports/{id}/encounters?includeTrash=true` | Encounter list per report |
| `/api/armory/character/{id}` | Full gear + build + resolved stats |
| `/api/armory/character/{id}/captures?limit=` | Capture history with report ids |
| `/api/encounters/rankings/overall?...` | Leaderboard |
| `/api/characters/{name}/boss-rows?...` | Per-boss ranking rows |
| `/api/phases` | Phase list |

**Also determine:**

- ~~**Healing data.** Is there a `character_spell_healing` (or equivalent) endpoint?~~ ✅ **RESOLVED
  in session 0b (2026-08-04): yes.** `/api/reports/{id}/character_spell_healing?...&participantType=friendlies`
  returns per-character-per-spell `total_healing` / `overhealing` / `effective_healing` /
  `total_absorbs` / `casts` / `hits` / `crits`, plus `source_breakdowns` and `target_breakdowns`.
  `character_healing` (no `_spell_`) 404s. **The anticipated "healer support has no empirical
  calibration" constraint does not apply.** Captured daily by the crawler.
- **Damage-taken per character**, for tank modelling. Same reasoning. *(0b captures
  `character_damage_taken_abilities` in both directions daily; per-character shaping is still 0a's to
  characterise.)*
- ~~**Resolve the `role=healer` empty-result quirk.**~~ ✅ **RESOLVED in session 0b.** The endpoint's
  own 400 body enumerates them: `Allowed values: tank, dps, tanks-and-dps, support`. **`support` is
  the healer role.** `metric=avg_hps` is also accepted and orders differently from `avg_dps`.
- Resolve the leaderboard's apparent 25-result cap regardless of `limit`. *(0b note: not reproduced
  at `limit=100`, which returned full sets. Not chased further — revisit only if a >100 pull is ever
  needed.)*
- ⚠ **Per-ability endpoints AGGREGATE across the `encounterIds` passed** — returned rows carry no
  `encounter_id`. Per-encounter granularity requires one call per encounter (0b, 2026-08-04).
- **Target count**: does any response carry it, or something implying it (enemy unit count, trash
  flag, encounter type)? If not, state explicitly that it must be *inferred*. **Never silently
  default to 1** — the entire scenario model depends on this being honest.
- **Content type**: can `raid` / `dungeon_normal` / `dungeon_mythic` / `world_boss` be derived from
  zone, difficulty, or bracket fields? §2.9's content profiles should be **derived from real
  encounter data**, not invented — this is where that comes from.
- **Per-parse character stats** (crit rating, SP, AP, haste). Load-bearing: Phase 3's pooled
  inference regresses observed crit% against each character's melee vs. spell crit. If stats only
  exist on the current armory snapshot and not per-parse, say so — it means approximating from the
  nearest-in-time capture, with the error that implies.
- **Date/patch/realm/season** per parse, for §2.5 stamping.
- ~~Are report IDs sequential integers, and what's the current maximum?~~ ✅ **PARTLY RESOLVED in
  session 0b.** They are small sequential integers, but **there is no unauthenticated list
  endpoint** — `/api/reports?limit=N` returns **401 `{"error":"No token provided"}`**, and
  `/api/reports/recent` / `/latest` 400 because they're parsed as `{id}`. Discovery is therefore
  **sequential ID probing**; a missing ID returns a clean 404 `{"error":"Report not found"}`. The
  crawler walks upward from a stored frontier and stops after 20 consecutive 404s. **The current
  maximum is still unknown** — it emerges from the first full run.

---

## Task 3 — Changelog: confirm the parse and assess the corpus

### 🆕 AMENDED (session 0b, 2026-08-04): it's a JSON API — don't parse HTML

The changelog page embeds a real paginated JSON API, discovered while building the daily fetcher:

```
https://api.ascension.gg/api/v3/article/changelog?realm_type=1&page=N
```

Laravel-style pagination, `per_page=100`, **353 pages / 35,238 entries**. Each entry carries a stable
integer `id`, plus `label`, `category`, `realm_type`, `group_key` (the "Changes made on" date, as
`YYYY/MM/DD`), `description` (with `[Darkmoon]` / `[Dawnrise]` / `[Pending Restart]` tags inline),
`created_at`, and `updated_at`.

**The HTML-scraping description below is superseded for *acquisition*.** The parsing work (realm,
status, and ability-name extraction from `description`) is unchanged and still this task's job — it
just runs against clean JSON fields instead of markup, and gets `updated_at` for free as a
change-detection signal.

**Backfill already done by session 0b:** 353/353 pages, 0 errors, 30.2 MB in
`data/source/changelog/backfill/`. The corpus reaches back to **2016/07/23** — a decade of history,
substantially more than this task assumed. Daily snapshots of pages 1–2 land in
`data/source/changelog/daily/`. Item 2 below ("backfill all 352 pages") is therefore **complete**;
items 1, 3, 4, 5 remain open.

---

*(Original task text, retained — its acquisition claims are superseded above, its analysis goals are not.)*

**Confirmed 2026-08-04:** `https://ascension.gg/en/changelog/1` is fully server-rendered plain text,
no JS, paginated `?page=N` with **352 pages**. Entries group under `Changes made on: YYYY/MM/DD` and
category headers (`General`, `Talents & Abilities`), tagged `New` or `Change`, frequently carrying:

- **Realm tags**: `[Darkmoon]`, `[Dawnrise]`, `[Classless - Dawnrise]` — a Dawnrise-only change must
  not invalidate a Darkmoon fact (§2.5)
- **Status tags**: `[Pending Restart]`, `[Going Live Monday, 3 August]` — an entry may describe a
  change **not yet in effect**. Parse status; never assume every entry is live
- **Bracketed ability names**: `[Divine Concord]`, `[Righteous Opportunity]` — high confidence
- Inline prose names without brackets — lower confidence, needs catalog name-matching

**Do:**
1. Write the parser. Extract date, realm(s), status, category, change type, raw text, and every
   detectable ability name with a confidence tag by detection method.
2. Backfill all 352 pages into `data/source/changelog/`. This produces a **per-ability change history
   going back seasons** — a genuinely new capability here.
3. Report what fraction of entries resolve to a known spell/card, and characterise the rest.
4. **Assess as a new-card discovery source.** Today's page announces ~10 new Mystic Enchants by name.
   If they're absent from `spell-export.json`, the changelog is the *earliest* signal a card exists.
   Quantify how often this happens.
5. **Assess whether server phase transitions are detectable** from changelog text (content unlocks,
   season starts). §2.10's per-phase gear tiers need a phase timeline, and this is the likeliest
   source.

**Flag for the user, don't act on:** today's changelog touches abilities in his live builds — proc
effects no longer triggering from off-GCD On-Next-Hit abilities such as Cleave; a Path of Duality
ranged-attack-power bug fix; Holy *abilities* (not just Holy *spells*) now triggering Holy Shatter;
and new Paladin-adjacent enchants (`[Righteous Opportunity]`, `[Vengeful Plague]`,
`[Judged Infection]`). Surface them; the analysis is a separate conversation.

---

## Task 4 — Re-run the DBC extractor and assess coverage

```
python3 index/build_dbc_index.py
```

1. ~~Confirm whether spell **274132** is now present. It wasn't previously; it also doesn't exist on
   db.ascension.gg (Task 1). Two independent absences is meaningful.~~
   ❌ **RETRACTED (0a): the premise was wrong. 274132 is in the client — it is Winds of Winter
   Rank 5 (`SpellLevel` 58), and 274121 is Rank 1 of the same line.** It only looked absent because
   `spell_dbc_raw` was scoped to catalog ids ±3, and rank ids are frequently **non-contiguous**
   (R1 `274121` → R2 `274129`) — so the filter was excluding the exact spell a level-60 character
   casts. Fixed: rank siblings are now pulled into scope (+7,639 ids). This also settles the
   long-running 274121-vs-274132 question: same line, different ranks, Rank 5 is the level-60 one.
2. Report totals: records, catalog entries resolved, `has_hidden_formula=1` spells resolved.
3. **Assess the 803 blocked spells.** They're present in DBC but blocked because the resolver is a
   *text regex* over description strings, while their coefficients live in **numeric fields**
   (`EffectBonusCoefficient`, `EffectBasePoints`, `EffectRealPointsPerLevel`, `EffectDieSides`,
   `EffectAmplitude`, `EffectChainTargets`, `EffectRadiusIndex`). Determine how many would resolve
   from numeric fields. **If that number is large, say so loudly — it likely makes a numeric-field
   extractor Phase 1's single highest-value task.**
4. Determine which other DBC tables are available and worth extracting: `SpellDuration`,
   `SpellRadius`, `SpellCastTimes`, `SpellRange`, `SpellCategory`, `SpellProcsPerMinute`,
   `Item-sparse`/`ItemStat`, and — critically — **`gtChanceToMeleeCrit` / `gtCombatRatings` and
   friends**, the combat-rating conversion tables Phase 2's engine needs for rating→percent at
   level 60. Ascension may have modified these; assuming retail values is exactly the kind of silent
   error that corrupts everything downstream.

4a. 🎯 **`SkillLineAbility.dbc` — extract this first, it may be the highest-value single item in
   Phase 0.**

   `SkillLineAbility` maps spell → skill line → class. Joined against the catalog, it resolves
   **class ownership deterministically for every entry that is a real WotLK spell** — no tooltip
   parsing, no class-tag rule, no proc test.

   **Measured against the current catalog (2026-08-04): 1,224 of 3,061 entries (40%) fall in the
   classic WotLK ID range** (`id < 80000`; 560 abilities, 664 talents). `class_origin` is currently
   populated for ~392 (13%). This route plausibly **triples deterministic class coverage**, and it
   closes the gap the primer describes as "requires the primer's method: predict from borrowed
   modifiers if stated, else proc-test."

   **Guardrails — an ID in the classic range is not proof on its own:**
   - **Verify the catalog entry's name matches the DBC record's name.** Ascension could reuse a low
     ID for something unrelated. A mismatch is a finding, not a rounding error
   - Some WotLK spells are class-agnostic (racials, professions, item effects) or appear on multiple
     skill lines — those resolve to no class or several. Record that honestly rather than forcing one
   - Seed at a new confidence tier, e.g. `confirmed_wotlk_id_identity`, distinct from
     `inferred_borrowed_modifiers`. It's stronger than tooltip inference but it is still an
     identity claim about the *base* spell, and Ascension may have re-tagged a reworked variant
   - **This resolves class origin only. It says nothing about coefficients** — see Tasks 1d and 1f
5. **How is this triggered?** It needs local client access, and the client updates daily. Determine
   whether extraction can run on client update (file-watch on the data directory), and how long a
   full run takes.

---

## Task 5 — Verify the `entry_id ↔ spells.id` crosswalk

Open since INDEX_GUIDE v4. Everything in layers 2–4 that says "which characters run ability X"
depends on it.

Take ~20 unambiguous spells appearing on many characters (Titan's Grip 46917 is canonical) and check
whether each crawled `entry_id` equals the catalog `spells.id`.

- **Consistent across a large, diverse sample** → confirmed; ID-identity join is safe
- **Inconsistent** → record *why* per mismatch (rank-specific IDs, duplicate names, season
  differences). This project has hit duplicate-name traps before (Ascension's Mental Quickness ≠
  WotLK's; two "Cruelty" ranks) — a name match alone isn't sufficient; check rank and description too

**Also test the rank hypothesis:** primer §5 states unresolved live IDs are usually a *different
rank* of a known card, and that checking ±1–3 resolved 5/5 in one cross-check. Confirm or disprove at
larger scale.

🛑 **This determines Phase 1's `spell_mechanics` primary key.** Do not start Phase 1 Task 4 without a
verdict.

---

## Task 6 — Stand up a crude daily crawler and start it TODAY

🚨 **Hard deadline: Phase 2 launches August 8th, 2026.** The server is currently on Phase 1
(Zul'Gurub). A phase transition is a **one-time, unrecoverable measurement** — the gear distribution,
the meta, and the DPS ceiling all shift, and the "before" side of that comparison exists only until
the 8th. Every day of Phase 1 data not captured is gone permanently.

This makes the crawler the single most time-sensitive item in the entire plan. **If anything in
Phase 0 gets deferred, it is not this.** A crude crawler collecting messy NDJSON before the 8th is
worth far more than a clean one started after.

**Also worth doing before the 8th, cheaply:** a one-off snapshot of the current leaderboard and the
top ~50 characters' full builds, so there's a clean Phase 1 baseline even if the incremental crawl
has gaps. Phase 3's `meta_snapshot(patch_id)` becomes genuinely informative with a real before/after
pair, and this is the only chance to create one this season.

**Sequenced here for the general reason too: parse data accrues with calendar time.** Every day not
running is a day of parses that cannot be retroactively collected.

**Minimal scope:**
- Standalone, on the user's machine, not through a chat session
- Walks zones × phases × difficulties via the leaderboard, plus sequential report IDs
- Per new character: full armory pull. Per new report/encounter: encounter list, per-ability damage,
  **avoidance**, and — if Task 2 finds them — healing and damage-taken
- Writes NDJSON to `data/source/crawl/<date>/{characters,encounters,abilities,avoidance}.jsonl`
  — ⚠ **amended to `.jsonl.gz` in session 0b**, see the deviations note at the end of this task
- **Stamps every record with capture timestamp, patch date, realm, and season** (§2.5)
- Keeps a `scan_log` so day 2 onward is incremental
- Rate-limits per Task 1/2 findings. Running unattended daily against someone else's public API —
  treat "don't get flagged" as a hard constraint
- Auto-commits and pushes the NDJSON at end of run

**Deferred to Phase 3:** normalisation, spell-ID resolution, provenance model, analysis. Raw capture
only. **Do not resolve spell IDs at capture time** — store raw `entry_id` and name; resolve at
rebuild, so a crosswalk fix never requires re-crawling.

**Capture all roles, not just DPS.** Even if DPS is the only role modelled initially, healer and tank
parses cost nothing extra to store now and cannot be backfilled later. This depends on Task 2
resolving the `role=healer` quirk.

**✅ RESOLVED (2026-08-04): manual-first on Windows.** The user runs Windows, and has chosen to run
the crawler **manually** for the first week or two rather than scheduling it immediately. Rationale:
the first runs should be watched so a silent 3am failure can't accumulate a week of empty captures
before anyone notices, and the Aug 8 baseline needs the crawler *run*, not *scheduled*.

- **Ship a one-command / double-clickable launcher** (a `.bat` wrapping the Python call is fine) so a
  manual run is one action, not a remembered incantation
- **Print a clear success/failure summary at the end of each run** — records captured, errors, commit
  status. Manual-first only works if the user can see whether it worked
- **Do NOT set up Windows Task Scheduler yet.** Add it once the crawler has proven itself over a few
  manual runs — it's a ~10-minute follow-up, not a redesign. When that time comes, generate a Task
  Scheduler config (the user is on Windows; cron is not relevant here)
- Everything else about the crawler (incremental `scan_log`, rate limiting, auto-commit) still
  applies to manual runs unchanged

**Second daily job:** the changelog fetcher from Task 3. The `[Pending Restart]` tag means entries
change state between fetches; a daily snapshot captures the transition. Cheap to run, impossible to
reconstruct later.

---

### ✅ BUILT — session 0b, 2026-08-04

| File | Role |
|---|---|
| `tools/scrapers/crawl_ascensionlogs.py` | the daily crawler |
| `tools/scrapers/fetch_changelog.py` | changelog daily snapshot + `--backfill` |
| `tools/scrapers/baseline_phase1.py` | the one-off pre-Aug-8 baseline described above |
| `run_crawler.bat` | double-clickable launcher, runs both daily jobs, prints a summary |

Full write-up: `primer/Session_2026-08-04_0b_crawler.md`. Deviations from the scope above, all
deliberate:

- **Report discovery is sequential ID probing, not a list walk** — the list endpoint requires auth
  (401). See Task 2's amended note.
- **Grind reports are grouped by `boss_id` instead of per-encounter.** Report #2 alone holds 658
  encounters / 368 boss attempts from an 8-hour session; per-encounter calls would be ~1,500 requests
  for one report. Reports over 40 boss encounters get one call per `boss_id` (scope
  `boss_group:<id>`); normal raid reports keep per-encounter granularity. Per-attempt *ability*
  granularity is lost for grind logs only — per-fight duration/kill/wipe data survives in the
  encounters list.
- **Healing is captured** (Task 2 found the endpoint), as is damage-taken in both directions.
- **All three roles are captured** via `role` ∈ `dps`/`tank`/`support`.
- **`patch_date` comes from the changelog fetcher's `latest_patch_date.txt`**, which is why the
  launcher runs it first. If absent, the stamp is `null` and the summary says so — never fabricated.
- **⚠ `phase_number` ≠ the server's "Phase N" label.** `/api/phases` record `phase_number=2` is named
  **"Phase 1.1"** and is a child of Phase 1 (`progression_parent_phase_id`), *not* the Aug 8 Phase 2
  launch. Build the phase timeline from `name` + parent id; treat `phase_number` as an opaque
  ordinal. §2.10's per-phase gear tiers would silently mis-bucket otherwise.
- **Not deadline-bound after all: the report backfill.** Reports persist after a phase flip, so
  historical reports can be collected later. What is genuinely unrecoverable is the *leaderboard
  standings* and *character armory snapshots* as they stand during Phase 1 — which is exactly what
  `baseline_phase1.py` captures. Run the baseline before Aug 8; let the report walk grind.
- 🆕 **Output is gzipped (`.jsonl.gz`), amending this task's "Writes NDJSON" line.** Measured on the
  first real run: **3 reports produced 116 MB**, and `avoidance` alone crossed the 50 MB rotation
  boundary (~370 KB per record — the enemy-side breakdown is large). A full historical walk would be
  multiple GB in the working tree and would keep colliding with GitHub's 100 MB per-file limit.
  **Honest accounting:** git already zlib-compresses blobs, so this is roughly *neutral* for `.git`
  size — the wins are clone/working-tree size and per-file headroom, not repo size. §2.12's
  "committed files are readable by a chat session" concern doesn't bind here: a 50 MB JSONL is
  unreadable through `raw.githubusercontent.com` compressed or not, and everything a human or chat
  session actually reads (docs, seed scripts, `index/scouted/*.json`) stays plain text. Read back
  with `gzip.open(path, "rt", encoding="utf-8")`. Pre-switch captures were converted in place by
  `tools/scrapers/compress_existing_crawl.py` (byte-verified round trip) rather than re-fetched.
  Measured: **130.3 MB → 7.4 MB (17.6×)**, 990 records, 0 malformed.
- 🆕 **Two storage tiers, owner-approved.** Volume and irreplaceability turn out to be
  anti-correlated, so the split is nearly free:
  **Tier 1 — committed** (`characters`, `leaderboards`, `phases`, `reports`, `scan_log.json`,
  `manifest.json`; 1.4 MB of the measured run): point-in-time state that is *gone* once a phase
  flips or a player regears.
  **Tier 2 — gitignored, local** (`abilities`, `healing`, `avoidance`, `damage_taken`; 6.0 MB):
  re-fetchable by report id, since reports persist on ascensionlogs.gg.
  **Every run writes a committed `manifest.json` describing *all* files including the gitignored
  ones** — record count, sha256, bytes, covered report ids — so git always knows what was captured
  even without the bytes, and a future session can distinguish "never captured" from "captured,
  stored locally." Recovery path: `crawl_ascensionlogs.py --recrawl-report <id>`.
  ⚠ Accepted risk: "reports stay fetchable" is evidenced (reports #2–4 from 24–25 July still
  fetchable on 4 Aug), **not guaranteed**. Hence tier 1 stays committed and `archive_crawl.py`
  defers rather than deletes. Full model in `tools/scrapers/README.md`.
- 🆕 **Armory records are content-hash deduped** over `ci_resolved`+`stats_summary` — written only
  when a build actually changes, instead of ~90 KB per character per run.
- ❌ **Rejected: deleting raw capture once normalised.** Normalisation encodes today's
  interpretation, and the crosswalk it depends on is unresolved (Task 5 gates Phase 1) — this task
  already forbids the adjacent version of the idea ("resolve at rebuild, so a crosswalk fix never
  requires re-crawling"). Derived databases are the disposable layer; raw capture is not.

---

## Task 7 — Recon the official builder

`https://ascension.gg/v2/builder/area-52/` is linked from db.ascension.gg as "The Official Ascension
Build Calculator." A build calculator must load the complete card catalog — ranks, costs,
prerequisites, rarities — from somewhere.

Find it. If it's an unauthenticated JSON endpoint, it's potentially the **cleanest canonical card
catalog in existence**, maintained by the people who make the game. Short task, large potential
payoff.

**Specifically look for:** card **rarity** (COMMON→LEGENDARY), **pool** (normal/golden), **tags**
(class/school/role), and **max rank**. These are the inputs to Phase 4's acquisition-cost model and
are only partially present in the current export.

Also check whether it encodes/decodes build strings. If so, that's a bidirectional interchange format
worth supporting — it would let the eventual builder UI export something players can open in the
official tool.

---

## Task 9 — Recon BisBeard (`s10.bisbeard.com`) — do NOT skip, it may cut a whole task

**An existing, actively-maintained tool already does much of what Phase 3 Task 4 was going to build.**
Its own description: a level 60 Classless Hero planner for Ascension Season 10 with 30 free-pick
ability slots, 25 max-rank talent slots, **audited talent-driven character-sheet stats**, five Hero
specializations, **Phase 0 gear**, and **Best in Slot optimization**. It's one of a family
(`s10.` classless, `coa.`, `classic.`, plus Bronzebeard), so it's maintained across realms, and it
carries Mystic Enchant support.

**It is a client-rendered SPA** — a plain fetch returns only the shell. This task needs a real
browser session or network-trace capture.

**Find, in priority order:**

1. **The item dataset.** An SPA doing BiS optimization must load items with stats, slots, sources,
   and **phase tagging** from somewhere — a JSON bundle, an API, or a static asset. This is the
   single most valuable thing here: it would replace reconstructing an item database from crawled
   gear, and it already carries the per-phase tagging §2.10 needs.
2. **The build string / share encoding.** BisBeard shares builds, so an encoding exists. If it can be
   read *and written*, the loop closes: sim a build in our stack → export to BisBeard → get gear →
   import back. Document the format the same way `decode_inspect_export.py` documents its own.
3. **Whether stat weights can be supplied programmatically.** If BiS optimization takes weights as
   input, our sim's output (Phase 2 T7) feeds it directly. Determine the input format.
4. **The talent→character-sheet audit data.** "Audited talent-driven character-sheet stats" means
   they've modelled how talents affect the sheet. Our `compute_stats()` (Phase 2 T4) is a real
   correctness risk — path bonuses, Int→SP conversions, multiplier stacking order all interact — and
   an independent implementation to cross-check against is worth a lot. Even if not extractable,
   spot-checking a few builds by hand against it is cheap and valuable.
5. **What content/phase criteria its BiS filtering exposes** — dungeon types, raids, phases. These
   are empirical `ContentProfile` categories from someone who already thought about the problem;
   compare against the presets derived in Task 2 rather than inventing a second taxonomy.
6. **Whether S10 phases beyond Phase 0 are enumerated anywhere** — seeds `server_phases` (Phase 1 T2).

**Server phase state (user-confirmed 2026-08-04):** S10 is at **Phase 1 — Zul'Gurub**. **Phase 2
starts August 8th, 2026.**

⚠ **BisBeard's own page metadata says "Phase 0 gear" — that is stale.** Recorded here as a source
lesson, not a criticism of the tool: a maintained tool's marketing copy is a source like any other
and belongs low in the §2.2 hierarchy. This was caught only because the user corrected it. Treat
BisBeard's *data* as valuable and its *page description* as unversioned prose. Any phase or content
label extracted from it needs a date check before use.

🛑 **Report before Phase 3 Task 4 is scoped.** If the item dataset and weight input are both
reachable, Phase 3 T4 collapses from "build a gear optimizer" to "extract items for the sim's gear
tiers, and hand off optimization." **Integrate, don't duplicate** — building a competing optimizer is
weeks of work for a worse result.

**Also note for later:** BisBeard is the closest thing to a competitor for the eventual builder UI.
It appears to do planning and gear well, and **not** simulation, stat-weight derivation, relationship
graphs, or component discovery. That gap is where this stack's value sits — worth keeping in view so
the eventual UI complements rather than duplicates.

**Courtesy:** this is a community tool run by someone else. Rate-limit any extraction, don't
redistribute their dataset, and prefer a documented API over asset scraping if one exists. If the
integration turns out to be genuinely useful in both directions, contacting the author is likely to
be more productive than reverse-engineering.

---

## Task 8 — Fix the docs, then write up

1. Fix `INDEX_GUIDE.md`'s self-contradiction (Task 2) and add every confirmed endpoint to the
   canonical endpoint map — v7's changelog documents endpoints the map itself lacks.
2. Correct the "db.ascension.gg requires JS" claim wherever it appears (Task 1).
3. Write `primer/RECON_FINDINGS.md`, one verdict per task.
4. **Open a `retractions` entry for each disproven belief.** Two already qualify: the JS-required
   claim, and the "fight-level per-ability endpoint not found" gap. Per §2.6, retractions are data —
   these are the first rows.

---

## Execution order

Tasks 1, 2, 3, 4, 7, 9 are independent. Task 5 gates Phase 1. Task 9 gates Phase 3 Task 4's scope.
Task 6 depends on Task 2. Task 8 last.

Most of this is fetching and reading, not building. The only real code is Task 6's crawler and Task
3's parser. **If Task 1, 7, or 9 finds a JSON endpoint or extractable dataset, flag it loudly** —
each is a large simplification downstream, and Task 9's may remove a whole task.
