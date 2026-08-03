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
  `2.s10w60.60.5....!1~...`) → run `index/decode_inspect_export.py` against it
  (needs `index/spell-export.json` alongside it). Don't hand-decode the
  hex/base36 format. The header's 4th field (`n`) is the active spec index —
  call it out rather than asking which spec was active.

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
  → run `index/scout_ascensionlogs_cli.py <name>` (or `--top "<instance>"
  --phase N --limit N` for leaderboard pulls). It's a public, unauthenticated
  JSON REST API — pure `requests`-based, no browser/scraping needed. Writes
  raw JSON to `index/scouted/scouted_<name>_<date>.json`. Rebuild the derived
  `scouted_builds.db` afterward with `index/build_scouted_builds_db.py`
  (auto-scans `index/scouted/`). The browser-console fallback
  (`index/scout_ascensionlogs.js`) only applies if driving a live browser tab
  mid-conversation — CLI is the default path. Known open gaps: `entry_id`
  correspondence to `spells.id` is unconfirmed (don't join as validated), and
  the fight-level per-ability damage-breakdown endpoint hasn't been found yet
  (`/summary /fights /table /damage-done` all 404 — `/api/reports/{id}` has
  metadata only). See `INDEX_GUIDE.md`'s scouting section for the full
  endpoint map.

## Rebuild command

Run from `index/` after any seed/schema change — full chain in primer §2a.

## Repo conventions

- Scouted-build data lives in `index/scouted_builds.db`, kept separate from
  `ascension_index.db` — never merge them.
- Analysis write-ups for scouted builds go in
  `builds/shared/scouted_<name>_<date>.md`, matching the `synergy_*.md`
  convention.
- Whenever a verdict changes (retraction, new resolution, updated stat
  weight), update `seed_confirmed.py` in the same session so the next index
  rebuild picks it up — don't just note it in prose.
