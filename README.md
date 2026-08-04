# AscensionCrafter

Theorycrafting toolkit for **Project Ascension** (Season 10, Wildcard, realm Darkmoon) —
a spell/mechanics database with provenance, a corpus of real player builds, and the
persistent context docs Claude uses across sessions.

**Start here:** [`primer/START_HERE_FOR_CODE.md`](primer/START_HERE_FOR_CODE.md), then
[`primer/PROGRESS.md`](primer/PROGRESS.md) for what's next. Architecture and the
non-negotiable data rules live in [`primer/ARCHITECTURE.md`](primer/ARCHITECTURE.md).

## Structure

```
primer/     The docs. START_HERE + PROGRESS + ARCHITECTURE + phase docs + session handoffs.
core/       Pure logic. No print(), no argparse, no paths; takes a connection as a parameter.
              db/        schema, connections
              spells/    text extraction, rank resolution, ID crosswalk, fingerprinting
              changelog/ patch-entry parsing and classification
api/        Service layer a web API would wrap 1:1. Empty until Phase 1 T7.
cli/        Thin command-line wrappers. `rebuild.py` runs the whole ingest chain.
ingest/     Source data -> the derived database.
              dbc/ export/ changelog/ logs_gg/ addon/
tools/      scrapers/ (acquisition runners), audit/ (integrity checks), log_parser/
addons/     In-game Lua addons.
data/
  source/   Committed, irreplaceable raw captures: export/ dbc/ scouted/ changelog/ crawl/
  derived/  Gitignored .db files and reports. Always rebuildable.
builds/     my-builds/ (locked)  wip/ (theorycraft)  shared/ (scouted + synergy write-ups)
```

The split that matters: **`data/source/` is committed and can never be regenerated;
`data/derived/` is disposable.** And `core/` never learns where a file lives — only
`config.py` knows that (ARCHITECTURE §2.7).

## Rebuilding the database

```bash
py cli/rebuild.py
```

Runs the full chain into `data/derived/ascension.db` from committed plain-text
sources. Takes seconds and works in any clone.

After a **client patch**, add the DBC extraction step — it reads the game client's
own MPQ archives and rewrites the two committed extracts in `data/source/dbc/`:

```bash
py cli/rebuild.py --with-dbc
```

That step needs the client installed plus a locally built StormLib
(`ASCENSION_STORMLIB_DLL` overrides the DLL path). Nothing else does.

## Daily data capture

```bash
run_crawler.bat
```

Snapshots the changelog and crawls `darkmoon.ascensionlogs.gg`, capped at 25 new
reports. Also runs automatically at logon — see [`SCHEDULING.md`](SCHEDULING.md).
`catchup_crawler.bat` is the uncapped historical backfill and stays **deliberately
manual**; don't schedule it.

## Parsing a combat log

```bash
py tools/log_parser/parse_log.py "<path>/WoWCombatLog.txt"
```

Pure stdlib. See `tools/log_parser/README.md` for the confidence breakdown —
build-decoding is verified against ALC's real source; standard combat-event parsing
is still unverified against a real Ascension log.
