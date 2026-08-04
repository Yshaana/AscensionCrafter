# AscensionCrafter — Claude Code Instructions

Always read these before any theorycrafting/analysis/scouting task — they change
most sessions, so re-read even if the topic feels familiar from earlier context:

@primer/Ascension_Context_Primer.md
@primer/INDEX_GUIDE.md
@builds/my-builds/build_paladin-hammerdin.md

## Tool triggers

Check this list before hand-parsing, hand-decoding, or guessing at anything below
— a purpose-built tool already exists for each of these.

- **Inspect link** (`inspects.nie.one/#new/...` or a raw fragment like
  `2.s10w60.60.5....!1~...`) → run `ingest/addon/decode_inspect_export.py` against
  it. Don't hand-decode the hex/base36 format. The header's 4th field (`n`) is the
  active spec index — call it out rather than asking which spec was active.

- **Combat log** (`WoWCombatLog.txt`, captured with the ALC/AscensionLogsCompanion
  addon) → run `tools/log_parser/parse_log.py <file>` (needs `combat_log_parser.py`,
  `decode_alc.py`, and `d1_dict.bin` alongside it in the same folder). Outputs
  `<logname>.summary.json` with `crit_rate_by_source_ability`,
  `avoidance_breakdown`, and every player build ALC captured in the log
  (decoded, verified byte-exact against ALC's own source). Note:
  `combat_log_parser.py`'s event parsing is *unverified* against a real
  Ascension log as of this writing — confirm field alignment against the
  first real log in a session and fix anything that's off; don't assume it's
  already validated. Full detail in `tools/log_parser/README.md`.

- **Scouting another player's build/rankings** on `darkmoon.ascensionlogs.gg`
  → run `tools/scrapers/scout_ascensionlogs_cli.py <name>` (or `--top "<instance>"
  --phase N --limit N` for leaderboard pulls). It's a public, unauthenticated
  JSON REST API — pure `requests`-based, no browser/scraping needed. Writes
  raw JSON to `data/source/scouted/scouted_<name>_<date>.json`. Rebuild the derived
  `scouted_builds.db` afterward with `ingest/logs_gg/build_scouted_builds_db.py`
  (auto-scans `data/source/scouted/`). The browser-console fallback
  (`tools/scrapers/scout_ascensionlogs.js`) only applies if driving a live browser
  tab mid-conversation — CLI is the default path. ✅ Both of this section's former
  open gaps are now CLOSED — `entry_id` is the CharacterAdvancement ID (never join
  it to `spells.id`; go through `spell_id_crosswalk`), and the fight-level
  per-ability endpoint exists (`/api/reports/{id}/character_spell_damage`). See
  `INDEX_GUIDE.md`'s scouting section for the full endpoint map.

## Rebuild command

```bash
py cli/rebuild.py
```

One command for the whole chain, into `data/derived/ascension.db`. Run it after any
seed/schema change.

Add `--with-dbc` **only** after a client patch: that step needs the game client plus
a built StormLib, and it rewrites the two committed extracts in `data/source/dbc/`.
It is what produces the client-derived tables — `dbc_character_advancement` (the
crosswalk), `dbc_spell_rank`, `dbc_spell_class`, `dbc_gt_tables` — so a session
without client access can still use them via `ingest/dbc/load_extract.py`.
Schema in `INDEX_GUIDE.md`.

## 🛑 Hard rules (Phase 0, 2026-08-04 — these have each cost a session)

- **Never join `entry_id` to `spells.id`.** They are different ID spaces — 0 of 1,054 match.
  `entry_id` (scouted builds, armory captures, BisBeard) is the **CharacterAdvancement ID**. Join
  through `dbc_character_advancement.ca_id` → `spell_rank_<N>` → `spells.id`.
- **Never relate two spell IDs by name.** Fingerprint on mechanics (school, cooldown, radius, cast
  type, effect structure) first. Two spells named "Holy Supernova" are unrelated abilities.
- **Never read a magnitude from a DBC `description` string** — numeric fields only.
- **Check the rank before trusting a magnitude.** The catalog stores the wrong rank for ~half of all
  multi-rank cards (697 of 1,409), usually Rank 1 — up to a 10× error on flat values. Rank is
  level-gated: highest rank in the line with `SpellLevel` ≤ character level. Use `dbc_spell_rank`.
- **Scope card queries to `dbc_character_advancement.in_current_pool = 1`** (3,129 of 10,231). The
  rest are other realms'/modes' entries and are the main source of duplicate-name confusion.
- **Never read a flat magnitude off a catalog entry without checking the rank.** Use
  `core.spells.ranks.rank_for_level()` or the `catalog_vs_live` crosswalk rows.

## Repo conventions

- **Layout** (Phase 1 T1, 2026-08-04): `core/` is pure logic — no `print()`, no
  `argparse`, no paths, takes a connection as a parameter. Only `config.py` knows
  where files live, and `core/` may not import it. `tools/audit/check_core_purity.py`
  enforces this; run it after touching `core/`.
- `data/source/` is committed and irreplaceable; `data/derived/` is gitignored and
  always rebuildable. Never commit a `.db`.
- Scouted-build data lives in `data/derived/scouted_builds.db`, kept separate from
  `ascension.db` — never merge them.
- Analysis write-ups for scouted builds go in
  `builds/shared/scouted_<name>_<date>.md`, matching the `synergy_*.md`
  convention.
- Whenever a verdict changes (retraction, new resolution, updated stat
  weight), update `seed_confirmed.py` in the same session so the next index
  rebuild picks it up — don't just note it in prose.
