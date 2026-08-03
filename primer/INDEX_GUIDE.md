# Ascension Spell/Card Index — Guide (v3)

**v3 changelog (2026-08-03):** Improvement batch v1 — three new tables (`exclusivity_buckets`, `modifier_links`, `talent_amplifiers`), four new `spells` columns (`crit_table`, `rolls_hit_check`, `hit_table`, `proc_icd_seconds`), one new `spell_scaling` column (`cp_scaling_type`), and a full batch pass of `build_dbc_index.py`'s hidden-formula resolver. All additive — every v2 table/column/query still works unchanged. Five things worth flagging from this batch:
- **`sharesModifiersWith` does not exist in `spell-export.json`.** Verified by inspecting the union of keys across all 3061 entries — every spell has exactly `{id, type, name, rank, tooltip}`. `modifier_links.link_type='talent_amp'` (the field this was meant to populate) is therefore **not populated** — only `link_type='class_tag'` (migrated from the existing `borrows_from` data) has rows. Re-check if a future `spell-export.json` pull ever adds the field.
- **Holy Finish had zero `spell_scaling` rows before this batch.** `build_index.py`'s SP/AP regex only matches the standalone `$SP*N` / `$AP*N` form, not Holy Finish's compound `($AP+$SP)*n*n*0.02`. `seed_cp_scaling.py` now hand-inserts its two rows (SP 0.02, AP 0.02) alongside the existing extractor output — a pre-existing gap in `build_index.py`, not fixed there since every other spell's extraction is unaffected.
- **Molten Earth's `crit_table` is left NULL on purpose**, not "unconfirmed" in the ordinary sense — it measures 40.7% crit (primer §1) but crit-capability has no structural predictor and the primer explicitly says not to force it into the melee/spell binary. A `notes` entry flags this so it reads differently from a truly-unknown spell. Confirmed with the project owner before seeding.
- **Two names from the source brief don't resolve against the current export** — "Consecrated Holy Weapon" (closest match: `Consecrated Weapon`, id 200809, not assumed identical) and "PBL ground" (no matching `spells.name` at all). Flagged in `seed_spell_flags.py`'s console output rather than guessed — same duplicate-name-trap discipline as everything else in this pipeline. Resolve manually against a live tooltip before seeding `crit_table` for either.
- **`build_dbc_index.py`'s hidden-formula batch pass: 84/887 resolved, 803 left blocked** — same split as the pre-batch reactive total, since the resolver already runs against the *full* `has_hidden_formula=1` list every time it's invoked (not incremental). The 803 blocked spells are **not** missing from `spell_dbc_raw` (hidden_refs resolve against DBC at 100%) — their raw sub-spell description text simply has no `$SP*`/`$AP*`/`$RAP*`/weapon-damage pattern to extract (utility/CC/flat-value effects, e.g. Blizzard, Power Word: Shield, Charge — coefficients for these live in numeric DBC fields like `EffectBonusCoefficient`, not description text; decoding those is out of scope for the current regex-based resolver). `tooltip_diff_report.py` re-run against the fresh pull found exactly one "uses X modifiers" line missing from an export tooltip — Fel Cleave, already on record (v11) — so **no new class-tag proof case** this batch.

**v2 changelog (2026-08-03):** Rewritten for the v12 repo reorg — new paths throughout, new `shared_synergies` table + confidence tiers, new `spell_scaling.source` column distinguishing export-tooltip coefficients from DBC-derived ones. **Confirmed correct:** `build_dbc_index.py` lives in `index/` alongside the rest of the pipeline (this matches the primer's v13 correction — an earlier primer changelog had mistakenly placed it in a separate repo; that's now fixed on both docs). Version-tagging this file going forward, matching the convention already used by the primer and build docs, so future edits are traceable instead of silent.

`ascension_index.db` (SQLite) built from `spell-export.json` (3061 spells) + `Cards.txt` (owned cards). All of this lives in `index/` as of the v12 repo reorg — the db itself is gitignored/ephemeral (rebuild each session, see primer v10/v12).

Rebuild anytime with, from `index/`:
```
python3 build_index.py && python3 seed_borrowed_modifiers.py && python3 seed_confirmed.py && python3 seed_synergies.py && python3 seed_exclusivity.py && python3 seed_modifier_links.py && python3 seed_talent_amplifiers.py && python3 seed_spell_flags.py && python3 seed_cp_scaling.py
```
if the source exports change. Add `python3 build_dbc_index.py` (needs local client access + a built StormLib) if you also need `spell_dbc_raw`/`dbc_*`/`index/dbc-extract.json` refreshed, and the hidden-formula resolver re-run against the current `has_hidden_formula=1` list — **not part of the routine per-session rebuild above**, since it depends on the local WoW client rather than plain-text project files that mount cleanly every time. Run it last if included — it reads `spells`/`hidden_refs` state produced by the steps above.

## Repo layout / naming convention (v12)

| Prefix | Folder | Meaning |
|---|---|---|
| `build_*` | `builds/my-builds/` | Locked, authoritative, iterable — your own build docs |
| `wip_*` | `builds/wip/` | Theorycraft in progress, not yet a committed board |
| `synergy_*` | `builds/shared/` | External engine/scaling reference extracts only — **not** full gear/talent dumps |

Filenames carry the prefix (not just the folder) because flat project-knowledge mounts lose folder context. `primer/` holds this guide and the systems primer; `index/` holds every index-building script plus the raw exports and generated artifacts.

## Tables

**spells** — one row per catalog entry (ability or talent)
| Column | Meaning |
|---|---|
| id, type, name, rank | raw catalog fields |
| tooltip | raw tooltip text |
| schools | comma-list of damage schools *mentioned in the tooltip text* (Frost/Fire/Shadow/Arcane/Nature/Holy/Physical + hybrids: Holystrike, Holyfire, Shadowflame, Firestrike, Froststrike, Shadowstrike, Spellstrike, Stormstrike) |
| mechanics | comma-list of text-signal tags: heal, proc, dot_hot, aoe, cc, execute, cooldown_effect, buff_debuff, resource_mana/rage/energy/runic/holypower/combopoints/focus, exclusivity_bucket |
| has_hidden_formula | 1 if the tooltip references a sub-spell ID **not present in this export** — the true coefficient is hidden (primer's "hidden sub-spell" problem, e.g. Hammer from the Heavens = 282987) |
| hidden_refs | those unresolvable spell IDs, for when you get a live tooltip |
| has_unresolved_pct | 1 if the tooltip has an unresolved `$s1%`-style magnitude placeholder |
| **class_origin** | ONLY ever populated two ways — see Confidence tiers below. NULL means "unknown, don't guess" |
| class_confidence | `confirmed_proc_test` / `confirmed_native` / `confirmed_class_tag_rule` (doc-verified) vs `inferred_borrowed_modifiers` (auto, from an explicit "uses X modifiers" clause — still verify with a proc test before relying on it for engine-gating decisions) |
| best_fit_path | ONLY set from explicit doc statements |
| path_fit_heuristic | auto-computed from primer §3's own rule: SP+AP or hybrid school → Duality; SP+heal → Healing; SP only → Intelligence; AP only → Strength/Agility |
| borrows_from | the literal ability name(s) named in an explicit "uses X modifiers" tooltip clause (381 spells have this — it's the mechanical hook the class-tag rule runs on) |
| **crit_table** (v3) | `melee` / `spell` / `none` / NULL (unconfirmed). Only ever set from a doc-confirmed measurement (`seed_spell_flags.py`) — NULL means unconfirmed, not "doesn't crit". See Molten Earth exception below. |
| **rolls_hit_check** (v3) | 1/0/NULL — per primer §5's hit-weighting rule (crit table and hit table are independent rolls). Column exists; no values seeded yet — nothing in the docs states this per-ability as of v3. |
| **hit_table** (v3) | `melee` / `spell` / NULL — same idea as crit_table but for the hit roll, independently. Column exists; no values seeded yet. |
| **proc_icd_seconds** (v3) | NULL = unconfirmed; 0 = confirmed no ICD. Currently seeded only for Fel Infused Weapon (0, primer §1 v6). |
| notes | provenance / doc citation for any confirmed field. Also carries the crit_table/proc_icd_seconds seed rationale (v3) and, for Molten Earth specifically, an explicit "left NULL on purpose" flag — see the v3 changelog above. |

**spell_scaling** — one row per detected SP/AP/RAP/WEAPON coefficient (spell_id, term_type, coefficient, source, **cp_scaling_type** (v3)). A spell can have multiple rows (e.g. hybrid abilities have both an SP and an AP row). **This is the damage-formula comparison table** — sort/filter it directly. `source` is `export_tooltip` (from the catalog's own text, `build_index.py`) or `dbc_hidden_formula` (pulled from a `has_hidden_formula=1` spell's hidden sub-spell text in `spell_dbc_raw`, `build_dbc_index.py`) — the latter only exists for spells where the client's raw data revealed a coefficient the export never showed. **`cp_scaling_type`** (v3, `seed_cp_scaling.py`): `linear` / `quadratic` / NULL (not a combo-point-scaling term). Quadratic combo-point finishers (Holy Finish, Winds of Winter, Shield Strike, Elemental Immolate) put the CP term inside a squared power (`*n*n` in the raw tooltip) rather than a linear `*n` multiplier — primer §1 (v12), "never dump below max CP" rule. Detected by scanning each finisher's literal per-point tooltip formula, not inferred from mechanics alone.

**owned_cards** — from Cards.txt: cardId, spellId, rank, pool (abilityNormal/abilityGolden/talentNormal/talentGolden). Join to `spells` on spellId to answer "what do I actually own."

**confirmed_facts** — every load-bearing rule/measurement from the primer + handoff (crit conversion, path bonuses, exclusivity buckets, stat weights, the class-tag rule itself, etc.), tagged with topic + source doc + section, so it's queryable alongside the spell data instead of re-reading the whole markdown file.

**shared_synergies** (v12, `seed_synergies.py`) — engines/cards observed on **other players'** builds (dungeon groups, external parses/tooltips), not our own. Same append-only spirit as `confirmed_facts`, but every row also links to a `builds/shared/synergy_*.md` file with the full write-up.
| Column | Meaning |
|---|---|
| name | short identifier for the engine/card |
| source | where this came from (parse, tooltip, screenshot + date) |
| engine_desc | how the mechanism actually works |
| scaling_note | formula/coefficients, or a pointer to the linked file if too long for one field |
| tags | comma-list, same free-tagging spirit as `mechanics` |
| confidence | see tier legend below |
| linked_file | the `builds/shared/synergy_*.md` with full detail |
| date_added | when this was logged |

**Confidence tiers for `shared_synergies.confidence`:**
- `external_sighting` — observed on someone else's character (parse/tooltip/screenshot), not proc-tested by us
- `internal_test` — verified via our own testing, but on a card/engine we don't currently run as a core build piece
- `confirmed_proc_test` — same top tier as the `spells.class_confidence` legend below, if it's ever earned one

**Check `shared_synergies` before treating an external build's engine as novel** — it may already be logged.

**exclusivity_buckets** (v3, `seed_exclusivity.py`) — makes "does not stack / only the highest applies" rules queryable instead of living only in prose. Each row is one (bucket, spell) membership; two spells conflict if they share a `bucket_id`.
| Column | Meaning |
|---|---|
| bucket_id | groups spells that share an exclusivity bucket — join on this, not `bucket_name` |
| spell_id | the card in the bucket |
| bucket_name | short slug (`all_damage_pct`, `weapon_imbue_slot`, `spell_crit_dmg_bonus`, `dw_spec_mastery`) |
| bucket_desc | one-line human description |
| source | `tooltip` (from an in-tooltip clause) / `patch_note` (server-codified) / `doc_confirmed` (mechanical, not tooltip-stated — e.g. the weapon-imbue slot conflict) |
| notes | provenance, plus a flag on `doc_confirmed` rows that they won't surface from a text scan |

Seeded with the 4 known buckets from the primer (Enhanced Weapon Mastery/Unending Fury/Answered Prayers/Blessed Weapons; the 5 weapon imbues; Holy Focus; Dual Wield Specialization↔Mastery — note DWS has two catalog entries under the duplicate-name trap, only the Rogue r5 one, id 13852, actually carries the "does not stack with Dual Wield Mastery" clause). The seed script also scans every tooltip for "does not stack"/"only the highest"/"only the strongest" and **prints** further candidates to console rather than auto-inserting them — most of the ~160 hits are generic buff boilerplate ("does not stack with other similar effects" on unrelated stat buffs), not build-relevant buckets, so they need a human read before becoming a row.

**modifier_links** (v3, `seed_modifier_links.py`) — unifies `spells.borrows_from` with the catalog's `sharesModifiersWith` field into one bidirectional table, so "what buffs ability X" and "what does X's damage feed into" are both one query. **`sharesModifiersWith` does not exist in the current `spell-export.json`** (verified against the full key set) — only `link_type='class_tag'` (migrated from `borrows_from`, not dropped) is populated; `link_type='talent_amp'` has zero rows pending a future export that actually carries the field.
| Column | Meaning |
|---|---|
| spell_id | the ability/card in question |
| target_name | the ability/effect it links to, by name (may not resolve to an id) |
| target_spell_id | resolved `spells.id` if `target_name` matches a catalog entry unambiguously, else NULL |
| link_type | `class_tag` (uses X modifiers) — `talent_amp` (sharesModifiersWith) currently unpopulated, see above |
| link_confidence | same tier vocabulary as `spells.class_confidence` |
| source | `export_tooltip` (both current rows come from the tooltip's "uses X modifiers" clause) |

**talent_amplifiers** (v3, `seed_talent_amplifiers.py`) — operationalizes primer §5's "named lists outrank generic wording until proc-tested" rule so a new amplifier can be checked by query instead of a manual tooltip re-read.
| Column | Meaning |
|---|---|
| talent_spell_id | the talent card |
| target_effect | the amplified target(s), as extracted from the tooltip |
| match_type | `verbatim` (names a specific ability or hybrid school string, e.g. Shadowflame) vs `school_generic` (only names a base school, e.g. "Fire and Shadow spells") |
| verified | 1 if proc-tested/confirmed live, else 0 — the 3 hand-seeded primer §5 cases (Shadow and Flame, Bane = verified; Emberstorm = not) are the only `verified=1` rows currently |
| notes | classification rationale; `'needs manual review'` on ambiguous bulk-scan extractions rather than a guessed classification |

Hand-seeded with the 3 primer §5 cases, then bulk-scanned across all `type='talent'` tooltips for amplifier language (`increases ... by $sN%` patterns). The bulk pass is intentionally conservative — anything that doesn't cleanly resolve to either a known ability/hybrid-school name or a bare pure-school name gets `match_type='school_generic'` with a `'needs manual review'` note rather than a forced classification (~70% of bulk hits landed here, since the pattern also catches non-damage amplifiers like crit/dodge/block chance).

**Also see primer §5 for the daily patch-note check practice** (not duplicated here — kept in one place to avoid drift between docs).

## Confidence tiers for class_origin (read before trusting one)

1. `confirmed_proc_test` — actually verified in-game with a dummy parse (e.g. Lightbound Cleave = 0 procs from Paladin trigger)
2. `confirmed_native` — the character's own class ability, no ambiguity
3. `confirmed_class_tag_rule` — stated as fact in the docs but not explicitly proc-tested in the text
4. `inferred_borrowed_modifiers` — auto-derived: tooltip explicitly says "uses X modifiers", and X's real WotLK owning class is unambiguous. **Still a prediction, not a confirmation** — the class-tag rule (primer §4) exists precisely because flavor/name/school can mislead; always proc-test before it matters for engine-gating.
5. NULL — no class signal in this export at all. Most of the catalog (2669/3061) is here. Don't fill this in by guessing from the name — that's the duplicate-name trap (primer §2, e.g. Ascension's Mental Quickness ≠ WotLK's Mental Quickness).

## Common queries

```sql
-- Cross-class school search (the "cold caster, crazy single-target DPS" pattern)
SELECT s.id, s.name, s.type, s.class_origin, ss.term_type, ss.coefficient
FROM spells s JOIN spell_scaling ss ON s.id = ss.spell_id
WHERE s.schools LIKE '%Frost%' AND s.mechanics NOT LIKE '%aoe%'
ORDER BY ss.coefficient DESC;

-- What do I actually own that does Shadow damage?
SELECT s.name, oc.pool, oc.rank
FROM owned_cards oc JOIN spells s ON s.id = oc.spellId
WHERE s.schools LIKE '%Shadow%';

-- Highest AP-scaling single-target abilities (melee/hybrid DPS hunting)
SELECT s.name, s.schools, s.class_origin, ss.coefficient
FROM spells s JOIN spell_scaling ss ON s.id = ss.spell_id
WHERE ss.term_type='AP' ORDER BY ss.coefficient DESC LIMIT 20;

-- Everything flagged with a hidden formula (needs a live tooltip, not export-trustworthy)
SELECT id, name, hidden_refs FROM spells WHERE has_hidden_formula=1;

-- Pull a rule instead of re-reading the whole markdown doc
SELECT fact, source_doc, source_section FROM confirmed_facts WHERE topic LIKE '%crit%';

-- Everything known to feed a specific class's engine (borrowed-modifiers hits)
SELECT name, borrows_from, class_origin, class_confidence FROM spells
WHERE class_origin='Paladin' ORDER BY class_confidence;

-- Shared synergies tagged no-ICD (external builds worth checking against your own)
SELECT name, engine_desc, scaling_note, confidence, linked_file
FROM shared_synergies WHERE tags LIKE '%no-ICD%';

-- Check a chase-list for internal exclusivity conflicts (v3)
SELECT eb1.bucket_name, s1.name AS card_a, s2.name AS card_b
FROM exclusivity_buckets eb1
JOIN exclusivity_buckets eb2 ON eb1.bucket_id = eb2.bucket_id AND eb1.spell_id < eb2.spell_id
JOIN spells s1 ON s1.id = eb1.spell_id
JOIN spells s2 ON s2.id = eb2.spell_id;

-- Everything that amplifies a given ability, talent-chase surface (v3)
SELECT s.name AS amplifier, ml.link_type, ml.link_confidence
FROM modifier_links ml JOIN spells s ON s.id = ml.spell_id
WHERE ml.target_name = 'Whirlwind';

-- What does this card's damage actually feed into (v3)
SELECT target_name, link_type, link_confidence FROM modifier_links WHERE spell_id = ?;

-- Verbatim-confirmed damage amplifiers for a given effect (v3, primer §5 "named lists outrank generic")
SELECT s.name AS talent, ta.target_effect, ta.verified
FROM talent_amplifiers ta JOIN spells s ON s.id = ta.talent_spell_id
WHERE ta.target_effect LIKE '%Shadowflame%' AND ta.match_type = 'verbatim';

-- Quadratic combo-point finishers (v3, "never dump below max CP" rule)
SELECT s.name, ss.term_type, ss.coefficient
FROM spell_scaling ss JOIN spells s ON s.id = ss.spell_id
WHERE ss.cp_scaling_type = 'quadratic';
```

## What this does NOT do

- Does not know true class tags for the ~87% of the catalog with no "uses X modifiers" clause and no doc confirmation. That still requires the primer's method: predict from borrowed modifiers if stated, else proc-test.
- Does not resolve hidden sub-spell coefficients (they're simply not in this export — flagged, not fabricated).
- `schools`/`mechanics` are **text-presence signals**, not verified game mechanics — e.g. a tag with "heal" in mechanics means the word appears in the tooltip, not that it's confirmed to function that way live.

---

## External tool: decoding inspects.nie.one live character exports

A third-party site (`inspects.nie.one`) captures a live in-game inspect via WeakAura and exposes it as a URL fragment (`.../#new/<data>`). This is a **live data source, not part of the index** — it reflects whatever the target character has slotted at inspection time, for any player, not just your own characters. `index/decode_inspect_export.py` parses it into readable spec lists and gear, using `index/spell-export.json` for the name lookup.

**Format, reverse-engineered and confirmed 2026-08-02** (validated against a live in-game screenshot — decoded spec 2 matched the client's "Agility build" panel ability-for-ability and talent-for-talent):

```
<fragment> = <header> "!" <gear>

<header>  = "2" "." <season/level> "." <level> "." <n> "." <hex:name> "."
            <hex:realm> "." <hex:title> "." <unix_ts> "." <specs_blob>

<specs_blob> = <block> ("_" <block>)*        -- ONE BLOCK PER SPEC, in spec order
<block>      = <leader_token> "~" <30 base36 ability IDs, "."-joined>
                                "~" <25 base36 talent IDs, "."-joined>
  - leader_token's meaning is unidentified (doesn't resolve to a spell ID) —
    likely an internal row ID/checksum. Safe to ignore.
  - 30 abilities / 25 talents matches the fixed per-spec slot budget.

<gear>  = <item> ("_" <item>)*
<item>  = <slot_index> "~" <hex:item_string> "~" <hex:item_name> "~"
          <quality> "~" <slot_code> "~" <hex:icon_path>
  - item_string is classic itemString format: "itemID:enchant:gem1:gem2:gem3:gem4:...:lvl"
```

Two separate encodings in one payload: spec data is **base-36 spell IDs**, gear data is **hex-encoded ASCII/UTF-8**. Don't confuse the two when extending the parser.

**Usage:** `python3 decode_inspect_export.py "<fragment after #new/>"`

**Known gap:** ~11% of decoded spec IDs won't resolve against `spell-export.json` (rank-specific IDs our catalog doesn't carry a row for — same phenomenon as the rank-decoding practice in the primer §5, not a parsing bug). The live site itself always has the name; only our offline lookup is incomplete.

**Use case:** faster and more complete than manual ability-bar screenshots for capturing a live loadout — including other players' builds for comparison, and re-syncing this project's own docs against your characters' actual current state (see `builds/my-builds/build_paladin-hammerdin.md` v6 for the case study that led to writing this tool).
