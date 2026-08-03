# AscensionCrafter

Theorycrafting tooling for Project Ascension (Season 10, Wildcard, Darkmoon) —
spell/card index, combat log parsing, and the persistent context docs Claude
uses across sessions.

## Structure

```
docs/     Ascension_Context_Primer.md, Ascension_Paladin_Handoff.md, INDEX_GUIDE.md
          Persistent theorycrafting context. Version-bumped on edit.
data/     spell-export.json, Cards.txt, ascension_index.db
          Source data + the built SQLite index (regenerate via scripts/, see below).
scripts/  build_index.py, seed_confirmed.py, seed_borrowed_modifiers.py,
          class_dictionary.py, decode_inspect_export.py
          Index build/seed pipeline + inspects.nie.one export decoder.
tools/log_parser/
          parse_log.py + friends. Parses WoWCombatLog.txt (with the
          AscensionLogsCompanion addon installed) into structured JSON:
          combat events (crit%, avoidance) and decoded player builds.
          See tools/log_parser/README.md for details + confidence notes.
```

## Rebuilding the index

Run in order from `scripts/`:

```
python3 build_index.py              # rebuilds data/ascension_index.db from data/spell-export.json + data/Cards.txt
python3 seed_borrowed_modifiers.py  # resolves class_origin via "uses X modifiers" tooltip clauses
python3 seed_confirmed.py           # seeds confirmed_facts from docs/ statements
```

All paths are relative to repo root (resolved via each script's own location),
so this works from any clone — no environment-specific paths.

## Parsing a combat log

```
cd tools/log_parser
python3 parse_log.py /path/to/WoWCombatLog.txt
```

Pure stdlib, no installs needed. See `tools/log_parser/README.md` for the
confidence breakdown (build-decoding is verified against ALC's real source;
standard combat-event parsing is unverified against a real Ascension log).
