# Session Primer — 2026-08-03: DBC Extraction Pipeline + Repo Restructure

**What this is:** a handoff for the *next* session, covering everything built today. Pair with `Ascension_Context_Primer.md` (v12) for the general systems rules and `INDEX_GUIDE.md` for the schema/query reference — this doc is the "what happened and why" for one long session, not standing background.

**Commits, in order:** `be2abc2` (initial project layout) → `e0438fb` (DBC pipeline) → `52598c7` (pipeline follow-up) → `4fa6b20` (Fel Cleave seed) → `15f1de7` (repo restructure, current HEAD).

---

## 1. The big picture

Two independent pieces of work happened today:

1. **Built a from-scratch pipeline to read Ascension's actual game client** (MPQ archives → Spell.dbc → parsed spell data) and cross-reference it against the existing spell-export.json-derived catalog. This is a fundamentally different, more complete data source than anything used before.
2. **Restructured the whole repo** into a tiered build system (`builds/my-builds` / `builds/wip` / `builds/shared`) with a filename-prefix convention, plus moved all index tooling into `index/`.

Both are done and committed. Nothing is half-finished, but there are real open threads (see §6).

---

## 2. The DBC extraction pipeline (`index/build_dbc_index.py`)

### Why this exists
`spell-export.json` (the in-game/addon-reachable catalog) is incomplete — 887 spells reference sub-spell IDs that aren't in it at all (`has_hidden_formula=1`), because it only captures what a player can inspect, not internal helper sub-spells. The client's own `Spell.dbc` is the complete catalog, including those hidden references.

### What had to be built (all one-time environment setup, now done)
- Installed Python 3.12, CMake, and Visual Studio Build Tools (none were present on this machine).
- Cloned and built **StormLib** (ladislav-zezula/StormLib) from source, using its bundled zlib/bzip2/lzma option to avoid extra dependencies. Built as an ANSI DLL (`STORM_UNICODE` is OFF by default) — this matters for the ctypes wrapper (`LPCSTR`/`mbcs`-encoded paths, not wide strings).
- Cloned TrinityCore's 3.3.5 branch (sparse-checkout, just `DBCStructure.h`) as the authoritative field-layout reference for `Spell.dbc` — including columns TrinityCore itself comments out (like `Description`) because the column still occupies real space in the row and we need the raw tooltip text.
- The StormLib build lives at `C:\Users\Yshaana\Documents\dbc-extraction-work\refs\stormlib\build\Release\StormLib.dll`. `build_dbc_index.py` looks for it via the `ASCENSION_STORMLIB_DLL` env var, falling back to that hardcoded path.

### The patch-chain shortcut
Ascension's client has ~60 custom patch MPQs (`patch-A` through `patch-CZZ`, `patch-M`, `patch-S`, `patch-T`, etc.) beyond stock Blizzard naming. Determining their true load order looked like it'd be a real problem — but empirically, **each target DBC file is present in exactly one non-stock archive**:
- `Spell.dbc` → `patch-T.MPQ` (209,077 records — the real, complete custom catalog, vs. ~50k in any stock/locale version)
- `SpellDuration/SpellRange/SpellCastTimes/SpellRadius/SpellIcon.dbc` → `patch-S.MPQ`
- `Talent/TalentTab.dbc` → `patch-M.MPQ`

Since no other custom archive touches the same path, whichever one has the file *is* the final version, regardless of the broader chain order. `build_dbc_index.py`'s `find_owning_archive`/`pick_final_archive` implement this by scanning every archive rather than hardcoding filenames, so a future client patch that moves the data to a different archive name still gets found automatically (with a printed warning if it ever becomes ambiguous — i.e. two non-stock archives both claiming the same file).

### Validation
`validate_known_spells()` runs on every invocation: checks 10 known-confirmed spells' raw-stable substrings (e.g. Judgement of the Three Hammers' `SP*0.325`/`AP*0.278`, Lightbound Cleave's `uses Cleave modifiers`) against the fresh extraction and **exits non-zero with a printed diff on any mismatch**. This is what catches a regression automatically if the client patches and the schema shifts.

### Investigated-and-ruled-out: the "$61840donds" text
Some descriptions read like corrupted text (e.g. *"over $61840donds as Holy damage"* instead of "...8 seconds..."). Verified via raw-byte inspection (no embedded nulls, no encoding issues) that this is **not a bug** — it's Ascension/Blizzard's own tooltip macro convention: `$<spellID>d` renders as a bare unit (`"8 sec"`) at tooltip time, and authors glue the rest of the word on with no space (`onds`→seconds, `utes`→minutes, `ond`→second — confirmed recurring 400+ times across the catalog). Documented directly above `read_cstr()` in the code so it doesn't get "fixed" by a future session.

### What it produces
- `spell_dbc_raw` table — scoped to the 3,061 catalog spells + 1,080 hidden_refs targets + a small ID-neighborhood buffer (not the full 209k; that blew the committed db to 194MB, past GitHub's limit). Columns: name, name_subtext, description, aura_description, attributes, school_mask, effect_json (all Effect* arrays as JSON), source_archive.
- `dbc_spellduration` / `dbc_spellrange` / `dbc_spellcasttimes` / `dbc_spellradius` / `dbc_talent` / `dbc_talenttab` — the supporting lookup tables, same scoping logic per-file.
- **`resolve_hidden_formula_spells()`**: runs the exact same SP/AP/RAP/weapon regex `build_index.py` uses on export tooltips, but against each `has_hidden_formula=1` spell's hidden sub-spell text in `spell_dbc_raw`. Inserts real `spell_scaling` rows (tagged `source='dbc_hidden_formula'` vs. `'export_tooltip'`) and clears the flag where resolved. **84 of 887 resolved this way** — the rest are mostly flat-value effects with no literal `$SP*`/`$AP*`/`$RAP*` macro, which this regex approach was never going to catch (same limitation the original tooltip-regex approach already has).
- **`index/dbc-extract.json`** (new today, in the restructure): a committed JSON export of `spell_dbc_raw` + support tables + the resolved `dbc_hidden_formula` scaling rows. This exists because `ascension_index.db` is gitignored/ephemeral (see §5), but the DBC data can't be regenerated without local client access + a built StormLib — so this file is the fallback for a session that doesn't have that.

### `index/tooltip_diff_report.py` (also new today)
Clause-level diff of every catalog spell's `spell_dbc_raw.description` against its `spells.tooltip`, normalizing out `$`-macros/numbers so raw-vs-resolved formatting doesn't cause false positives. Splits on sentences and on `@ext:...:ext@` wrapper clauses specifically. Output: `index/tooltip_diff_report.md` (human-readable) + `.json` (raw data).

Findings (3,061 spells compared):
- **389** "uses X modifiers" class-tag lines catalogued (most already visible in the export tooltip too — useful reference, not new bugs).
- **1 genuinely missing**: **Fel Cleave (276066)** — "This uses Cleave modifiers" is entirely absent from its export tooltip, same shape as the already-documented Enhanced Weapon Mastery omission (primer §2). This is now seeded into `seed_confirmed.py` as Warrior-tagged, Shadowflame school, **not part of the current Paladin kit** — see `builds/wip/wip_fel-cleave-leveling.md`.
- **20 other DBC-only clauses**, notably **Exorcism (879)**: an undocumented stun (`"It also stuns them for $900879d"`) and "always critically strikes Undead and Demon targets" — neither in the export tooltip. Worth a look next session if Exorcism ever becomes relevant.

### A resolved-vs-assumed discrepancy worth knowing about
`seed_confirmed.py`'s `hidden_subspell_hoth` fact says Hammer from the Heavens (282987)'s composition was *"UNCONFIRMED, currently assumed 30% SP / 30% AP / 40% flat."* The actual DBC tooltip is `(($PL-10)*2.4+$m1) + AP*0.091 + SP*0.091` — 9.1% AP/SP each plus a level-scaling flat term, **not** the assumed 30/30/40 split. **This was not auto-corrected anywhere** (per instruction: flag, don't silently overwrite a placeholder assumption) — if this matters for a build decision, update the primer/handoff explicitly rather than trusting the old assumed split.

Also worth noting: this spell (282987) isn't actually referenced in any catalog spell's `hidden_refs` column, so it sits outside the "887 resolved" count entirely — it was found by manually cross-checking IDs mentioned in `seed_confirmed.py`, not by the automated hidden-formula resolution.

---

## 3. Repo restructure

New layout, with a filename-prefix convention (so folder context isn't lost if this project ever gets mounted flat somewhere):

| Prefix | Folder | Meaning |
|---|---|---|
| `build_*` | `builds/my-builds/` | Locked, authoritative, iterable — e.g. `build_paladin-hammerdin.md` |
| `wip_*` | `builds/wip/` | Theorycraft in progress, not yet a committed board |
| `synergy_*` | `builds/shared/` | External engine/scaling reference extracts only — not full gear/talent dumps |

`primer/` holds this doc, `Ascension_Context_Primer.md`, and `INDEX_GUIDE.md`. `index/` holds every index-building script, the raw exports (`spell-export.json`, `Cards.txt`), generated reports, `dbc-extract.json`, and the gitignored `ascension_index.db`. `tools/log_parser/` (the separate ALC combat-log tool) was untouched.

**`ascension_index.db` is now gitignored** — continuing a policy the primer already stated at v10 (rebuild-each-session derived cache, never a committed source of truth), just actually applied to this git repo now rather than left as a stale intention.

New this session: `builds/shared/synergy_winds-of-winter.md` (another player's Titan's Grip Int/AP build, met in a dungeon — quadratic combo-point-scaling finisher, open crit-source question) and `synergy_fel-infused-dagger.md`, plus `index/seed_synergies.py` populating a new `shared_synergies` table (4 rows) — same append-only, confidence-tiered pattern as `confirmed_facts`, but for engines observed on *other* players' builds. Check it before treating an external build's engine as novel.

**A gap got fixed along the way:** `seed_confirmed.py` already cited "Primer §4 (v11)" for the Fel Cleave finding from a prior step in this session, but that v11 changelog entry had never actually been written into the primer. Added it retroactively, then added v12 for the restructure itself.

---

## 4. Rebuilding everything (from a clean session)

```bash
cd index
python build_index.py            # spells, spell_scaling, owned_cards tables from spell-export.json/Cards.txt
python seed_borrowed_modifiers.py
python seed_confirmed.py
python seed_synergies.py
python build_dbc_index.py        # needs local client (E:\Ascension Launcher\...) + StormLib.dll; writes dbc-extract.json
python tooltip_diff_report.py    # needs spell_dbc_raw already populated
```

Expected counts after the first four: **3,061 spells / 394 class_origin rows / 41 confirmed_facts / 4 shared_synergies rows**. (394, not 393 — that's 393 + the Fel Cleave row added this session, not a discrepancy.)

If `build_dbc_index.py` can't run (no client access on this machine), `index/dbc-extract.json` has the last-extracted `spell_dbc_raw`/support-table/hidden-formula-scaling data — load it directly rather than skipping that data entirely.

---

## 5. Open items for next time

- **803 of 887 `has_hidden_formula=1` spells are still flagged** — their hidden sub-spell text has no literal `$SP*`/`$AP*`/`$RAP*` macro for the regex to catch. A future pass could try reading `EffectBasePoints`/`EffectBonusCoefficient` numerically from `effect_json` instead of relying on tooltip text, for the ones that are flat-value-only.
- **Hammer from the Heavens (282987)** — real coefficients now known (§2 above); the primer/handoff still state the old assumed 30/30/40 split. Worth reconciling explicitly if this ability matters for the current Paladin build.
- **Fel Cleave (`builds/wip/wip_fel-cleave-leveling.md`)** — Warrior tag is `confirmed_class_tag_rule` (from the DBC read), not yet proc-tested. Still just a placeholder file, no actual build.
- **Exorcism's undocumented stun and Undead/Demon crit clause** — flagged in the tooltip diff report, not yet folded into any build doc.
- **The other 19 "other missing clause" hits** in `index/tooltip_diff_report.md` haven't been individually reviewed (Duelist's Glove equipment notes, Raging Blow charge mechanics, etc.) — worth a skim if any of those cards come up.
- **This session's local commits are not pushed** — `git log` shows HEAD 5 commits ahead of what was checked at the last push point; push when ready.
