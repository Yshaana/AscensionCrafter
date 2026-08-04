# Project Ascension — Systems Primer v19 (Context for Claude)

This file explains how **Project Ascension** works so you can reason about build decisions. Background context, not a build — pair with a build handoff. Ascension is a heavily customized WoW private server; **treat in-game tooltip coefficients and mechanics as source of truth over retail/classic WoW assumptions**.

> **🔧 Tool trigger — inspect links (read this before anything else in chat):** If the user pastes anything matching `inspects.nie.one/#new/...`, or a raw fragment that looks like `2.s10w...!1~...` (dot-separated header, `!` before a gear blob, `~`/`.`/`_`-delimited spec blocks), **immediately fetch and run `index/decode_inspect_export.py` against it.** Do not hand-decode the hex/base36 format manually — the decoder already exists, is fast, and won't make transcription errors. Full format spec lives in the script's own docstring and `INDEX_GUIDE.md`.

**v19 changelog (2026-08-04, Phase 0 recon session `0a`):** The client's own DBC files turned out to
answer several questions this document had been treating as open or heuristic. Full evidence in
`primer/RECON_FINDINGS.md`; index mechanics in `INDEX_GUIDE.md` v8. **Read those for detail — only the
consequences for the rules in this document are recorded here.**

- 🚨 **The catalog stores the WRONG RANK for about half of all multi-rank cards.** `spell-export.json`
  holds **697 of 1,409** multi-rank entries at a rank a level-60 character does not hold, and in **all
  697** the correct id is absent from the export entirely. Holy Supernova is the live example: the
  catalog has Rank 1 (61–69 damage), the owner casts **Rank 6 (595–714)** — a ~9.7× gap.
  **Never read a flat magnitude off a catalog entry without checking its rank first.**
  ✅ Silver lining, measured on the same line: **coefficients do *not* change with rank** (identical
  `EffectBonusCoefficient` at R1 and R6) — only flats do. So reading an SP/AP *coefficient* off a
  Rank-1 entry is probably safe; reading a flat is catastrophic. One line, not yet a law.
- ❌ **The §5 "check ±1-3 for a rank sibling" heuristic is retracted** as a general rule — 4,791 rank
  lines are non-contiguous vs 1,908 contiguous. Rank is **level-gated**: the highest rank in the line
  whose `SpellLevel` ≤ character level. Corrected inline in §5.
- 🆕 **Class resolution is now deterministic for 58% of the catalog** via `SkillLineAbility` — see the
  new note at the top of §4. The class-tag rule becomes the fallback for the rest.
- ✅ **The crit-rating conversion (§1) is confirmed from `gtCombatRatings.dbc`**, along with every
  other level-60 rating conversion. Ascension has not modified those tables.
- 🆕 **Weapon-imbue exclusivity (§2) is mechanically confirmed and now queryable** — effect type 54.
- 🆕 **New rule in §2: the school of an *applying* spell is not the school of its damage.**
- 🎯 **The `entry_id` ↔ `spells.id` question is answered: they are different ID spaces and must never
  be joined.** `entry_id` is the **CharacterAdvancement ID**; the client ships the mapping as
  `CharacterAdvancement.dbc`. This affects every "who runs ability X" query — see `INDEX_GUIDE` v8.
- 🆕 **The duplicate-name trap (§2) now has a structural explanation.** A card name can appear several
  times in the CA table — once per game-mode/realm pool — and only one is currently playable. "Titan's
  Grip" and "Holy Power" each have three entries. `in_current_pool` picks the right one.
- ⚠ **Three idempotency bugs found in this project's own scripts** (two in `build_dbc_index.py`, one
  in `seed_confirmed.py`), all the same shape: *a script that derives rows without owning the deletion
  of its own previous output*. All fixed. Worth checking on any new ingester.

**v18 changelog (2026-08-03):** Two `decode_inspect_export.py` fixes from this session's inspect-decoding work:
- **Active-spec index (`n`) was parsed but silently dropped.** The header's 4th field (`fields[0:4]`) was already unpacked as `n` but never printed or used — confirmed this session against a live `Pumprat` export where `n=5` matched the spec the user identified as active. Now printed in the header (`Active spec: 5`) and the matching spec block is tagged `(ACTIVE)` in its own header line. Format-spec docstring updated to explain `<n>` instead of leaving it unglossed.
- **Tool discoverability gap closed.** This session, Claude was handed a raw inspect fragment and hand-decoded it manually before the user pointed out the decoder already existed — the tool was documented (`INDEX_GUIDE.md`, primer v8/v9 changelogs, §2a's "related but separate" aside) but buried in prose a top-to-bottom read wouldn't connect to a pasted URL fragment. Added the pinned trigger note above, right after the title, before the changelog wall.

**v17 changelog (2026-08-03):** Scouting-session mechanical findings (Titanus/Zavulon armory pulls + an 11-character, 17-report Hammer from the Heavens hunt). Closes a long-standing open question from `build_paladin-hammerdin.md`'s hit/expertise walkback section and refines the "Holy is unresistable" combat-engine default:

- **✅ CLOSED: "Can Holy spells (particularly Hammer from the Heavens) miss?"** — No. 4,962 pooled hits across 11 characters and 17 reports: 0 miss, 0 dodge, 0 parry, 0 full resist. See `confirmed_facts.hammer_from_heavens_cannot_be_avoided`; detail edit in `build_paladin-hammerdin.md`'s hit/expertise walkback section.
- **§1 refinement: "Holy is unresistable" specifically means no full-resist roll**, not immunity to ordinary partial/chip magic resistance. Confirmed on both Lightbound Cleave (356 hits, our own build) and Hammer from the Heavens (4,962 hits) — both show 0 full resists but nonzero partial resist. Forecasting off Holy damage should still account for target resistance stat's partial mitigation; "unresistable" is not "resistance-stat-proof."
- **§1 refinement: Molten Earth's crit rate is not a fixed/flagged value** — three independent character measurements (40.7%/575, 46.6%/116, 64.8%/54) spread over 24 points. Reframe from "no structural predictor, per-spell flag" to "a normal crit-capable spell that scales with each character's own crit rating, like any other spell" — same conclusion in practice (verify per parse, don't infer from tooltip structure) but a cleaner mechanism.
- **Righteous Vengeance's 0%-crit verdict now spans 9 characters / 4 Paths / 303 hits**, up from a handful of parses. Effectively settled.
- New scouting methodology discovered this session, worth keeping in mind for future test design: **searching combat logs directly for an ability name across many reports finds who's actually playing a build far more reliably than browsing leaderboards or individual talent trees** — see `INDEX_GUIDE.md`'s scouting section (v7) for the technique. This is how the 11 Hammer-from-the-Heavens players were found after leaderboard-browsing and random-profile-clicking both came up empty.

**v16 changelog (2026-08-03):** Amendment to v15's scouting tooling — scouted-build data split out of `ascension_index.db` into its own `index/scouted_builds.db` (separate, optional, rebuildable), and the primary scouting path is now the browser-free `index/scout_ascensionlogs_cli.py` rather than the browser-console script (which stays as a fallback). Detail in `INDEX_GUIDE.md` v5, not duplicated here — same "this file points to INDEX_GUIDE.md for index mechanics" pattern as v15.

**v15 changelog (2026-08-03):** New outlier-build scouting tooling added to `index/` (`scout_ascensionlogs.js` + `ingest_scouted_build.py`), pulling opponent/top-player builds from `darkmoon.ascensionlogs.gg`'s live REST API into five new `scouted_*` tables (characters, gear, build entries, rankings, capture history) — purely additive, no existing table touched. Full endpoint map, workflow, and open items (entry_id↔`spells.id` correspondence unconfirmed; fight-level damage-breakdown endpoint not yet found) live in `INDEX_GUIDE.md` v4, not duplicated here — same "this file points to INDEX_GUIDE.md for index mechanics" pattern as every prior index change.

**v14 changelog (2026-08-03):** Index improvement batch v1 — landed three new queryable tables and two new column sets, closing gaps between prose-only rules and the database. Full schema/query detail lives in `INDEX_GUIDE.md` v3; only the build-fact-relevant findings are noted here:
- **`exclusivity_buckets`, `modifier_links`, `talent_amplifiers` tables added.** The first operationalizes §2's "does not stack" buckets (auto-detects chase-list conflicts by query instead of manual cross-checking); the third operationalizes §5's "named lists outrank generic wording" rule the same way. `modifier_links` was meant to also ingest the catalog's `sharesModifiersWith` field (§2's cross-class talent-chase surface) but **that field does not exist anywhere in the current `spell-export.json`** — verified against the full key set (every entry is just `{id, type, name, rank, tooltip}`). Only the existing `borrows_from` class-tag data is in the table for now; re-check if a future export pull adds the field.
- **New `spells` columns** (`crit_table`, `rolls_hit_check`, `hit_table`, `proc_icd_seconds`) seeded only from already-confirmed measurements (Lightbound Cleave/Dawn Strike/Sword Specialization/Righteous Vengeance crit tables, Fel Infused Weapon's no-ICD). **Molten Earth's `crit_table` is deliberately left NULL** rather than forced into the melee/spell binary — its 40.7% measured crit rate has no structural predictor per §1, same reasoning as always, now just also reflected (via a notes flag, not a value) in the index. Two names from the seed brief — "Consecrated Holy Weapon" and "PBL ground" — don't resolve against any current `spells.name` and were left unseeded rather than guessed; if either of those is meant to be a specific catalog card, it needs a live-tooltip/spell-ID check before the index can carry it.
- **New `spell_scaling.cp_scaling_type` column**, confirming Holy Finish (already known quadratic) and additionally auto-detecting **Shield Strike and Elemental Immolate** as quadratic CP finishers alongside Winds of Winter — same "never dump below max CP" consequence applies to both, not previously flagged in this doc. Also surfaced a pre-existing extraction gap: Holy Finish had **zero** `spell_scaling` rows before this batch (the compound `(AP+SP)*n*n` tooltip form isn't matched by the standard `$SP*`/`$AP*` regex) and Winds of Winter's frost-SP term (`$SPFR*0.0096`) still doesn't extract for the same reason (the regex expects literal `$SP*`, not a school-suffixed variant like `$SPFR*`) — noted for a future pass, not fixed in this batch since it's an extractor issue outside this batch's scope.
- **`build_dbc_index.py` batch-run against the full `has_hidden_formula=1` list**: 84/887 resolved, 803 blocked — same split as before, since the resolver already runs the full list every invocation (not incremental, despite the task brief's framing). The 803 aren't missing from `spell_dbc_raw` (100% of hidden_refs resolve against DBC) — their raw description text just has no SP/AP/RAP/weapon-damage pattern to extract; these are largely flat/utility/CC effects (Blizzard, Power Word: Shield, Charge) whose real coefficients live in numeric DBC fields (`EffectBonusCoefficient`) that the current text-regex resolver doesn't decode. Re-ran `tooltip_diff_report.py` against the fresh pull specifically to check for a new class-tag proof case (§4) — found exactly one "uses X modifiers" line missing from an export tooltip, and it's Fel Cleave, already on record since v11. **No new class-tag proof case this batch.**
- **Full per-session rebuild command updated** (5 new scripts added to the chain, `build_dbc_index.py` still separate/optional — see §2a and `INDEX_GUIDE.md` v3 for the current command).

**v13 changelog (2026-08-03):** **Correction to v11: `build_dbc_index.py` lives in `index/`, not a separate `AscensionCrafter` repo.** v11 documented it as external tooling in a standalone repo; that was wrong (or has since changed) — it's part of this project's own `index/` folder alongside `build_index.py` and the seed scripts, per the v12 file-layout block below. Both v11 references corrected in place (§v11 changelog above, §2a). No build-fact changes — `spell_dbc_raw`, the Fel Cleave proof case, and the tooltip-diff methodology lesson from v11 all stand; only the pipeline's *location* was wrong. Full rebuild command, run from `index/`:
```
python3 build_index.py && python3 seed_borrowed_modifiers.py && python3 seed_confirmed.py && python3 seed_synergies.py && python3 seed_exclusivity.py && python3 seed_modifier_links.py && python3 seed_talent_amplifiers.py && python3 seed_spell_flags.py && python3 seed_cp_scaling.py
```
(v14: five scripts added to the chain — `seed_exclusivity.py`, `seed_modifier_links.py`, `seed_talent_amplifiers.py`, `seed_spell_flags.py`, `seed_cp_scaling.py` — see v14 changelog below and `INDEX_GUIDE.md` v3.) Add `python3 build_dbc_index.py` (needs local client access + a built StormLib) only when `spell_dbc_raw`/`dbc_*` need refreshing — it's not part of the routine per-session rebuild, since it depends on the local WoW client rather than plain-text project files.

**v12 changelog (2026-08-03):** Repo reorganized into a tiered build structure, plus two new standing practices.

- **Three build tiers, each with a filename prefix** (the prefix is load-bearing, not cosmetic — project-knowledge mounts are flat, so folder location alone doesn't survive a re-upload; the prefix does):

  | Prefix | Folder | Meaning |
  |---|---|---|
  | `build_*` | `builds/my-builds/` | Locked, authoritative, iterable — e.g. `build_paladin-hammerdin.md` (was `Ascension_Paladin_Handoff.md`) |
  | `wip_*` | `builds/wip/` | Theorycraft in progress, no talent board committed — e.g. `wip_fel-cleave-leveling.md` |
  | `synergy_*` | `builds/shared/` | External engine/scaling extracts only — **not** full gear/talent dumps — e.g. `synergy_winds-of-winter.md`, `synergy_fel-infused-dagger.md` |

  A `wip_` build gets renamed and promoted to `build_*` in `my-builds/` once guarantee slots are spent and prestige rerolls are done — the same "locked" threshold already used for the Paladin build. A `synergy_*` file never gets promoted; it's reference material for someone else's build, kept only for the engine/scaling pattern.

- **File layout** (paths referenced throughout this doc and `INDEX_GUIDE.md` now assume this root):
  ```
  primer/    → this file + INDEX_GUIDE.md
  index/     → build_index.py, seed_confirmed.py, seed_borrowed_modifiers.py,
               seed_synergies.py, build_dbc_index.py, spell-export.json, Cards.txt
               (ascension_index.db is NOT stored here — see §2a, rebuilt each session)
  builds/
    my-builds/  → build_paladin-hammerdin.md
    wip/        → wip_fel-cleave-leveling.md
    shared/     → synergy_winds-of-winter.md, synergy_fel-infused-dagger.md
  ```

- **New `index/seed_synergies.py`** adds a `shared_synergies` table to the index — same append-only, confidence-tiered pattern as `confirmed_facts` (§2a, `INDEX_GUIDE.md`). It's the queryable counterpart to the `builds/shared/synergy_*.md` files: one row per external engine/mechanic, tagged and linked back to its source file. Query it before treating an external build's mechanic as a new discovery — it may already be logged.

- **First populated `shared_synergies` entries (2026-08-03):**
  - **Winds of Winter** (`synergy_winds-of-winter.md`) — a dungeon-encountered Titan's Grip Int/AP dual-scaling nuke build. Core finisher scales `n²` with combo points spent (`flat×n + SP×0.0096×n² + AP×0.00624×n²`), which is the entire reason it dominates its own parse (47–56% of total damage from one ability). **Worth flagging against our own kit:** Holy Finish already uses the same quadratic-CP shape (`(AP+SP) × CP² × 0.02`, handoff §11) — same mechanic, different card. Also carries an **open, unresolved question**: observed Winds of Winter crit rate (91.7–100%) isn't fully explained by the one confirmed crit source (Killing Machine, 9 procs measured against 11–12 crits) — logged as `external_sighting`, not confirmed, pending a trinket-proc check the player would have to do themselves if they ever chase this build. Not a suggested pivot for our own SP-lane build — different stat posture entirely, kept for comparison only.
  - **Fel Infused Weapon** (`synergy_fel-infused-dagger.md`) — no-ICD per-hit Shadowflame proc, scales with attack frequency not weapon DPS. Already referenced in §1's v6 note; now has a dedicated file + index row instead of living only in this doc's changelog history.

- **New §5 practice: daily patch-note check.** Added below — check `ascension.gg/en/changelog/1` (Darkmoon realm) at the start of any session that touches build theorycrafting, before relying on an existing verdict.

- **§5 also gains a `shared_synergies` lookup practice** — see the bulleted list below.

**v11 changelog (2026-08-03):** Claude Code built a client-side DBC extraction pipeline (`index/build_dbc_index.py`, StormLib against the local client's MPQ archives — *location corrected in v13; originally documented as a separate `AscensionCrafter` repo, which was wrong*). Two results worth recording:
- **New class-tag proof case: Fel Cleave.** Same shape as Lightbound Cleave (§4) — export tooltip omits the class-tag clause entirely; the raw client tooltip reveals `"This uses Cleave modifiers."` → **Warrior**-tagged, same pattern as Enhanced Weapon Mastery's missing exclusivity clause (§2). Added to §4's table.
- **Methodology lesson, not a build fact:** the pipeline's automated tooltip-diff report flagged Exorcism's stun as "DBC-only, no export-tooltip match" — checked before writing it up, and it was a **false positive**: the export tooltip already has the same fact, just reworded (*"Using Exorcism on an Undead or Demon will stun the target..."* vs. the DBC's *"It also stuns them for..."*). A fuzzy-match diff can flag reworded-but-known facts as new. **New practice, §5: always check the export tooltip directly before writing up a diff-report hit — the report finds candidates, it doesn't confirm novelty.**

**v10 changelog (2026-08-03):** **`ascension_index.db` binary uploads are unreliable — diagnosed and worked around.** Re-uploaded copies of the `.db` repeatedly failed to open (`sqlite3.DatabaseError: file is not a database`); byte inspection showed the SQLite header's null terminator arriving as `\x10` instead of `\x00` — a null-byte mangling in the upload/mount pipeline, reproduced on a fresh re-upload, so it's not a bad export on the player's end. **Fix: stop treating the `.db` as a source to upload/maintain at all.** `build_index.py` → `seed_borrowed_modifiers.py` → `seed_confirmed.py` all read plain-text sources (`spell-export.json`, `Cards.txt`, `class_dictionary.py`, the seed scripts themselves) that mount cleanly with no corruption — running this pipeline reconstructs the full index **including all seeded `confirmed_facts` and `class_origin` rows** from scratch, verified byte-for-byte equivalent (3,061 spells / 393 class_origin rows / 41 confirmed_facts, matching pre-corruption counts). §2a and §5 updated accordingly. **(v12 note: this pipeline now runs from `index/`, not the repo root — see the v12 changelog file-layout block above.)**

**v9 changelog (2026-08-02, late night):** Formalized `decode_inspect_export.py` and its format spec into `INDEX_GUIDE.md` — a third-party site (inspects.nie.one) exposes a live in-game inspect as a URL fragment (base-36 spec data + hex-encoded gear), now fully decodable for any character, not just your own. Full format spec, known gaps, and usage live in `INDEX_GUIDE.md`; this is a live external data source, separate from the offline `ascension_index.db`.

**v8 changelog (2026-08-02, late night):** New §5 practice from cross-referencing a live in-game inspect/WeakAura export (55 spell IDs) against the catalog for the Paladin build: unresolved IDs are very likely different ranks of known cards, not missing content — resolved 5/5 unmatched IDs this way, each landing exactly on a card already known to be held at partial rank (see `build_paladin-hammerdin.md` v6 for the full case study).

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
- **Crit rating conversion: 14.0 rating per 1%** — *measured, identical for melee and spell* (393 rating → 28.07%; 164 → 11.71%). ✅ **Confirmed from the client's own `gtCombatRatings.dbc` (v19): exactly 14.0000 at level 60 for melee, ranged AND spell — the same number in the same table, which is why they're identical.** Ascension has **not** modified these tables; the level curve matches retail (70 = 22.0769, 80 = 45.9060). Other level-60 conversions now available without measuring: hit melee/ranged 10.0, hit spell 8.0, haste 10.0, expertise 2.5, armor pen 4.2, dodge/parry 13.8. See `dbc_gt_tables`.
- Special-attack (yellow) hit cap vs raid boss: **8%**. Dual-wield **white** attacks carry an additional **+19% miss** — the DW white cap is effectively unreachable at low tiers, so **auto-attacks in a dual-wield build may be near-worthless** (measured: 4.2% of damage, 37 landed swings in 309s).
- Expertise dodge cap: **26**.
- **Ground/periodic effects generally cannot crit** — *confirmed repeatedly for aura-tick DoTs* (PBL ground 0%/32 ticks; Righteous Vengeance 0% over 4 parses).
  **⚠ Confirmed exception, mechanism theory RETRACTED (v7):** Molten Earth's live tooltip reads *"Burns enemies in the area, dealing 60 + (SP+AP)×0.12 Fire damage every second for 8 sec. Uses Fire Nova modifiers."* That's a textbook aura-tick DoT — structurally identical to Righteous Vengeance's *"30% crit damage over 8s as Holy DoT."* Yet Molten Earth parses 40.7% crit over 575 hits while Righteous Vengeance parses 0% over 4 parses. **The v6 "aura-tick vs. instant-pulse ground object" theory does not survive this — Molten Earth is a real aura tick and still crits.** No structural predictor identified yet; crit-capability looks like a **per-spell server-side flag**, not something derivable from whether an effect is periodic/ground/aura. **Practice going forward: verify crit-capability per ability from a parse, never infer it from the tooltip's structure.**
- **⚠ No-ICD per-hit procs scale with attack frequency, not weapon damage (v6).** Fel Infused Weapon's tooltip has no internal cooldown: *"each auto attack and melee ability causes [flat + AP×0.05 + SP×0.05] Shadowflame damage."* That's a guaranteed trigger on every landed hit, not a proc chance. Reported in group parses at up to **~30% of total DPS** for hyper-fast dual-wield attackers (fastest daggers in the game, doubled swing count vs. a single slower weapon). **Practical consequence:** when a build carries a card like this, weapon *speed* can outweigh weapon *DPS* — always check whether a per-hit effect has an ICD before assuming more frequent smaller hits dilute rather than compound it. See `builds/shared/synergy_fel-infused-dagger.md` for the dedicated writeup.
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
- **⚠ Quadratic combo-point scaling is a real, distinct pattern from linear AP/SP scaling (v12).** Both our own Holy Finish (`(AP+SP) × CP² × 0.02`) and the externally-sighted Winds of Winter (`flat×n + SP×0.0096×n² + AP×0.00624×n²`) put combo points spent inside a squared term rather than a linear multiplier. Practical consequence carries over from Holy Finish's existing rule: **never dump below max CP** in a build using a quadratic finisher — going from 3→5 CP is not a 1.67× gain, it's closer to 2.8×.

---

## 2. The Card system

Everything slottable is a **card**. Axes: rarity tier, grade (Normal/Golden), rank, family, class/school tags.

### Exports (both obtainable — always request them)
- **Catalog export** (all in-game cards): per card — `name, rank (max), description (real tooltip with coefficients), rarities (COMMON→LEGENDARY), grades (every card exists in BOTH Normal and Golden), families (DEFAULT / LUCKY / TALENT), class + tab, tags (class/school/role), sharesModifiersWith, requiresEquip, requiredLevel`.
- **Owned-cards export**: four pools — `abilityNormal, abilityGolden, talentNormal, talentGolden` — entries `{cardId, spellId, rank}`. Match to catalog by spellId (names collide — see duplicate-name trap).

> ⚠ **Export tooltips can be INCOMPLETE, not merely unresolved.** Beyond the known `$s1` magnitude problem, exports have been observed **omitting entire clauses**. Enhanced Weapon Mastery's export text reads only *"Increases all damage done by $s1%"*; the live tooltip adds *"does not stack with Enhanced Weapon Mastery, Unending Fury, Answered Prayers or Blessed Weapons. Only the highest increase applies."* — which changes the card from a top-tier multiplier to a dead slot. **As of the 2026-08-03 Darkmoon patch this exclusivity is now a codified server rule, not just a live-tooltip clause** (see the daily-changelog practice in §5) — the underlying verdict doesn't change, but it's worth noting the source moved from "tooltip-only" to "patch-note-confirmed." **Before committing to any card verdict, ask for a live tooltip screenshot.**

### 2a. The index (`ascension_index.db`)

Both exports are parsed into a queryable SQLite database — check it before re-parsing raw JSON. Full schema and query cheat-sheet in `primer/INDEX_GUIDE.md`.

**⚠ v10: the `.db` is rebuilt from source each session, not uploaded as a binary.** Uploaded binary copies were repeatedly arriving corrupted (mount-pipeline null-byte mangling — see v10 changelog). The `.db` is now purely an **ephemeral local artifact**: at the start of any session that needs it, run `build_index.py` → `seed_borrowed_modifiers.py` → `seed_confirmed.py` → `seed_synergies.py` in sequence from `index/`, against the plain-text project mounts. This reconstructs the identical database, seeded facts included, with no corruption risk since every input file is text. **Do not re-upload the `.db` to project knowledge — it's redundant and the upload path is the thing that's broken.** The real sources of truth are `seed_confirmed.py` (build facts) and `seed_synergies.py` (external engine references) — both append-only, plain text; keep them current and the index follows automatically.

**Related but separate:** `primer/INDEX_GUIDE.md` also documents `decode_inspect_export.py`, which decodes a **live** in-game inspect (via the third-party site inspects.nie.one) into readable spec/gear data for any character. This is a live external capture, not part of the offline index — useful for pulling another player's build for comparison, or re-syncing this project's own docs against a character's actual current state (see `build_paladin-hammerdin.md` v6 case study).

**`spell_dbc_raw` + support tables (v11).** A separate pipeline (`index/build_dbc_index.py` — *corrected in v13, see above*) pulls `Spell.dbc` and friends directly from the client's own MPQ archives via StormLib — the complete internal catalog, not just addon-reachable spells. This is what `spell-export.json` was missing: 887 spells were flagged `has_hidden_formula=1` because they reference sub-spell IDs no addon-based export ever saw. As of v11, 84 of those 887 have real `spell_scaling` rows now, computed from the DBC data. **Still authoritative-over-derived, same rule as everything else in this section** — a DBC read beats a stale export, but a `confirmed_*` proc-test still beats a DBC read if they ever disagree (tooltip text describes intent; a proc test describes what the server actually does).

**`shared_synergies` (v12).** New table, populated by `seed_synergies.py`, mirroring `builds/shared/synergy_*.md` files one row per external engine/mechanic (name, source, engine description, scaling formula, tags, confidence tier, link back to the source file). Same confidence-tier discipline as `class_origin`: `external_sighting` (observed via someone else's parse/tooltip, not tested by us) is the default and weakest tier here, `internal_test` if we've verified it ourselves, `confirmed_proc_test` if fully proc-tested. Full schema in `INDEX_GUIDE.md`.

- **schools / mechanics / scaling coefficients** are auto-extracted from tooltip text at build time — treat these the same as any export field: fast, comprehensive, but subject to the incompleteness warning above.
- **`class_origin` is populated for ~392/3061 entries only** — either doc-confirmed (proc-tested) or auto-derived from a tooltip's explicit `"uses X modifiers"` clause resolved against the base ability's real WotLK class. **NULL means unknown, not "not this class."** Never treat a NULL as a negative result, and never treat an `inferred_borrowed_modifiers` row as settled — it's still a prediction per the class-tag rule (§4) until proc-tested.
- **It is a derived cache, not a source of truth.** This doc and the build handoffs stay authoritative. If a verdict here changes, add the fact to `seed_confirmed.py` (or the engine to `seed_synergies.py`) in the same session (§5) — the next rebuild picks it up automatically.

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

🆕 **v19 — one major source of this now has a structural explanation and a fix.** A card name can
appear several times in `CharacterAdvancement.dbc`, **once per game-mode/realm pool**, with only one
currently playable. "Titan's Grip" has three entries and "Holy Power" three; the non-playable ones
point at other-realm spell ids (e.g. `1146917`, in the "11-prefix" space). The
`dbc_character_advancement.in_current_pool` flag isolates the **3,129** playable cards from 10,231
and picks the right entry every time — validated against all 1,054 cards seen on live characters.
**This does not retire the trap** (genuinely different cards still share names *within* the playable
pool — Vengeance and Dual Wield Specialization above are real), but it removes the largest and most
confusing source of it.

### ⚠ Exclusivity buckets
Some effects share a **"does not stack / only the highest applies"** bucket, and the exclusion list is often **only in the live tooltip**. Known bucket: **Enhanced Weapon Mastery ↔ Unending Fury ↔ Answered Prayers ↔ Blessed Weapons** (all-damage %) — **as of the 2026-08-03 Darkmoon patch, this is now an explicit patch-noted server rule** (previously tooltip-only), see §5's daily-changelog practice. Similar wording appears on **Holy Focus** ("spell crits deal 200%, does not stack with other similar effects") and **Dual Wield Specialization ↔ Dual Wield Mastery** (fully redundant — one of them is always a dead slot).

**Practice:** when two slotted cards buff the same thing in the same way, assume a shared bucket until proven otherwise, and check the live tooltips of both.

### ⚠ Weapon-imbue exclusivity (v7)
Weapon-imbue-type ability cards (Windfury Weapon, Flametongue Weapon, Fel Infused Weapon, Rockbiter Weapon, Frostbrand Weapon, etc.) share a **weapon-enchant slot** — only one can be active at a time. This is a **different bucket from the talent all-damage% exclusivity above** — it's a mechanical slot conflict, not a stated "does not stack" tooltip clause, so it won't surface from a text scan the way §2's other exclusivity examples do. **Before recommending any weapon-imbue card alongside another, ask "is this an imbue?" first** — the same reflex as checking for a shared talent bucket, just without a tooltip to search for.

✅ **MECHANICALLY CONFIRMED (v19), and it's now detectable by query rather than by reflex.** Fel
Infused Weapon (276076) has exactly one effect: **type 54, `SPELL_EFFECT_ENCHANT_HELD_ITEM`**, with
`MiscValue` 952. That *is* the temporary-weapon-enchant slot — so the conflict is a real engine slot,
not a convention. **Any card whose effect list contains type 54 is an imbue and belongs in this
bucket**; find them with a query against `spell_dbc_raw.effect_json` instead of asking the question
by hand.

### 🆕 The school of an *applying* spell is not the school of its damage (v19)
Fel Infused Weapon reads school **Fire** on db.ascension.gg while every project doc calls it
**Shadowflame**, and **both are correct** — they describe different spells. `276076` is the
enchant-application spell (`SchoolMask` 4 = Fire) and **deals no damage at all**; the damage comes
from `276075` "Fel Infused Attack" (`SchoolMask` 36 = Shadow|Fire = **Shadowflame**, effect type 2
`SCHOOL_DAMAGE`).

**This is §4's trigger-vs-modifier trap in a new guise.** Before reading a school off the card you
press, check whether that card actually carries a damage effect — if it only applies an enchant, aura
or proc, follow the effect chain to the spell that carries `SCHOOL_DAMAGE` and read the school
there.

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

**Note (2026-07-28 patch):** a Darkmoon-wide fix corrected "Path of Duality was not increasing your Ranged Attack Power." This addresses a different clause than the SP amp / cross-crit conversion question above — it does not resolve §4's open item in the Paladin handoff, just noted for completeness since it's the same Path.

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

> 🆕 **v19 — this rule is now a FALLBACK, not the primary method, for most of the catalog.** The
> client's `SkillLineAbility.dbc` resolves class **deterministically for 1,789 of 3,061 catalog
> entries (58%)**, up from 394 (13%) — see `dbc_spell_class`. The mechanism is not what you'd expect:
> **Ascension renamed the skill lines themselves to class names** (line 26 is "Warrior", not retail's
> "Arcane"), so the *skill line's name* carries the class. `ClassMask` is useless — it is `512`
> (Ascension's own classless "Hero" class) on ~10k rows, which is exactly what db.ascension.gg reports
> as "Class: Hero" on every card.
>
> It **agrees with 382/387** existing doc-confirmed rows and **7/7** of the proof cases below that
> appear in the table — including the proc-tested Lightbound Cleave. Where a spell isn't in
> `SkillLineAbility` (36% of the catalog, e.g. Molten Earth), the rule below is still how you predict.
> **Neither method replaces a proc test when engine-gating is on the line.**

Proof case: **Lightbound Cleave** is Holy-flavoured, deals Holystrike, reads like a Paladin ability — and produced **zero** procs from a "damaging Paladin abilities" trigger. It borrows **Cleave** modifiers, so it is **Warrior**-tagged.

| Card | Borrows from | Predicted tag | Feeds a Paladin-gated proc? |
|---|---|---|---|
| Dawnreaver | Crusader Strike | Paladin | Yes |
| Dawn Strike | Sinister Strike | Rogue | No |
| Holy Finish | Eviscerate | Rogue | No |
| Lightbound Cleave | Cleave | Warrior | **No — confirmed** |
| Whirling Light | Whirlwind | Warrior | No |
| Blades of Light | Bladestorm | Warrior | No |
| Fel Cleave | Cleave | Warrior | No *(v11, DBC-only — see below)* |
| Winds of Winter | Cone of Cold | Mage | No *(external sighting — see `builds/shared/synergy_winds-of-winter.md`)* |
| Titanic Mutilate | Mutilate | Rogue | No *(external sighting — same file)* |

**Fel Cleave (v11):** same proof shape as Lightbound Cleave, found via the client-side DBC pipeline rather than a live tooltip screenshot. Export tooltip: *"A sweeping attack that deals X% weapon damage as Shadowflame to your target and up to 4 nearby enemies."* — no class-tag clause at all. Raw client tooltip adds *"This uses Cleave modifiers."* Not part of the current Paladin kit (Shadowflame school, not Holy/Holystrike) — relevant if the dual-wield/Shadowflame build thread ever considers it. Currently theorycrafted in `builds/wip/wip_fel-cleave-leveling.md`.

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

- **Check the daily patch notes at the start of any build-theorycrafting session (v12).** Source: `https://ascension.gg/en/changelog/1`, filtered mentally for **Darkmoon** (the player's realm — ignore Dawnrise/Bronzebeard-only entries unless they reveal a shared-engine mechanic change). Flag anything that: (a) touches a card/talent/ability already in a `build_*` or `wip_*` file, (b) changes an exclusivity bucket, proc-trigger mechanic, or scaling coefficient already recorded in `seed_confirmed.py`, or (c) suggests the spell export itself is stale (new abilities, reworked tooltips) and needs a fresh `spell-export.json`/`Cards.txt` pull before the next index rebuild. Report findings even when nothing is actionable — a patch that merely confirms an existing verdict (e.g. codifying a tooltip-only exclusivity rule) is still worth one line, since it upgrades the fact's confidence tier.
- **Check `shared_synergies` before treating an external build's mechanic as novel (v12).** Query `index/seed_synergies.py`'s table (or `builds/shared/synergy_*.md` directly) — a pattern like "no-ICD scaling with attack speed" or "quadratic combo-point finisher" may already be logged from a previous encounter, with a confidence tier and a linked file, rather than something to re-derive from scratch.
- **Rebuild `ascension_index.db` from source at the start of any session that needs it** (`build_index.py` → `seed_borrowed_modifiers.py` → `seed_confirmed.py` → `seed_synergies.py` → `seed_exclusivity.py` → `seed_modifier_links.py` → `seed_talent_amplifiers.py` → `seed_spell_flags.py` → `seed_cp_scaling.py`, run from `index/`, §2a, v14) — don't rely on a re-uploaded binary. Use the rebuilt index for cross-referencing and formula comparisons; fall back to raw `spell-export.json` only for something it doesn't capture.
- **Keep `seed_confirmed.py` and `seed_synergies.py` in sync with this doc and the build files.** Whenever a verdict here or in a `build_*`/`wip_*` file changes (a retraction, a new resolution, an updated stat weight), add the matching fact to `seed_confirmed.py` in the same session — the next rebuild picks it up automatically. Whenever a new external engine gets written up in `builds/shared/`, add its row to `seed_synergies.py` the same way. This replaces directly editing rows in a persisted `.db`.
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
- **Elite players' builds are evidence**, but weaker than a parse — this is the whole reason `builds/shared/synergy_*.md` files default to `external_sighting` confidence rather than anything stronger.
- **Separate loadout goals:** dungeon-trash AoE and boss single-target are different loadouts, not one compromise.
- **Watch the changelog and mind realm tags.** Balance changes and even ability *schools* change per patch and realm — see the daily-check practice above.
- **Be willing to walk back your own recommendations** when a measurement contradicts them, and say so plainly. Several v2/v3/v4 conclusions were overturned by single logs or single tooltips — including recommendations made earlier in the same session.
- **Check for ICDs before dismissing a per-hit proc as diluted by fast weapons.** A per-hit effect with no stated internal cooldown (Fel Infused Weapon, v6) scales UP with attack frequency rather than down — the opposite of the usual "more, smaller hits average out" intuition. Confirm ICD presence/absence from the live tooltip before valuing these against weapon speed.
- **When hunting multipliers for a specific effect, prefer talents that name it verbatim over talents matched by generic school wording (v7).** Shadow and Flame and Bane both list "Shadowflame" explicitly in their tooltips — ground truth, no test needed. Emberstorm only says "Fire and Shadow spells" — a prediction under the hybrid double-dip rule, not a confirmed hit, even though it reads like it should apply. Named lists outrank generic wording until proc-tested. This is the same discipline as the class-tag rule (§4) applied to damage-multiplier talents instead of proc-engine tags — and proof case #2 above (Elemental Fusion/Lava Flows vs. Molten Earth) is what happens when it's skipped: a spawned effect was assumed to inherit its trigger's modifiers by proximity, without checking its own `uses X modifiers` line first.
- **When decoding a live in-game spell ID export (WeakAura, inspect addon, etc.) against the catalog, an unresolved ID is very likely a different rank of a known card, not missing content (v7).** Multi-rank talents get a distinct spellID per rank in-game, while the catalog export only stores one canonical ID per card. ❌ **The "check ±1-3 of the unresolved ID" half of this practice is RETRACTED as a general rule (v19).** Measured across the client's full `Spell.dbc`: only **1,908** rank lines are id-contiguous while **4,791 are not** — Winds of Winter runs R1 `274121` then R2–R8 at `274129`–`274135`. The 5/5 hit rate that justified it came from lines that happen to be contiguous. **Use `dbc_spell_rank` instead** (`INDEX_GUIDE` v8): it groups rank lines on name + skill line + mechanical fingerprint, and the rank a character holds is the highest in the line whose `SpellLevel` ≤ their level. The *conclusion* the practice reached is still right — an unresolved ID is usually a rank sibling, not missing content — only the ±1-3 search method is unsafe.
- **A tooltip-diff report finds candidates, it doesn't confirm novelty (v11).** The DBC-vs-export tooltip diff flagged Exorcism's stun as DBC-only; the export tooltip had the same fact in different words, and a fuzzy-match similarity score missed it. Same discipline as everything else in this doc: **check the actual export tooltip yourself before writing a diff hit into `seed_confirmed.py`** — the tool surfaces what to look at, not a confirmed fact.
