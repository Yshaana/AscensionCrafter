# Ascension Spell/Card Index — Guide

`ascension_index.db` (SQLite) built from `spell-export.json` (3061 spells) + `Cards.txt` (owned cards). All of this lives in `index/` as of the v12 repo reorg — the db itself is gitignored/ephemeral (rebuild each session, see primer v10/v12).

Rebuild anytime with, from `index/`:
```
python3 build_index.py && python3 seed_borrowed_modifiers.py && python3 seed_confirmed.py && python3 seed_synergies.py
```
if the source exports change. Add `python3 build_dbc_index.py` (needs local client access + a built StormLib) if you also need `spell_dbc_raw`/`dbc_*`/`index/dbc-extract.json` refreshed.

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
| notes | provenance / doc citation for any confirmed field |

**spell_scaling** — one row per detected SP/AP/RAP/WEAPON coefficient (spell_id, term_type, coefficient, source). A spell can have multiple rows (e.g. hybrid abilities have both an SP and an AP row). **This is the damage-formula comparison table** — sort/filter it directly. `source` is `export_tooltip` (from the catalog's own text, `build_index.py`) or `dbc_hidden_formula` (pulled from a `has_hidden_formula=1` spell's hidden sub-spell text in `spell_dbc_raw`, `build_dbc_index.py`) — the latter only exists for spells where the client's raw data revealed a coefficient the export never showed.

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
