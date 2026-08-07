# AscensionCrafter — Claude Code Instructions

Always read these before any theorycrafting/analysis/scouting task — they change
most sessions, so re-read even if the topic feels familiar from earlier context:

@primer/Ascension_Context_Primer.md
@primer/INDEX_GUIDE.md

🧊 **`builds/my-builds/build_paladin-hammerdin.md` is NO LONGER auto-loaded, on purpose
(owner decision 2026-08-06).** It is a **frozen v1 artifact** describing a character
state that no longer exists — its §10 stat weights carry Attack Power at 1.00 for a
character now at AP **134**, and its §6 gear state predates Path of Intelligence and The
Light's Hope. Auto-loading it fed stale weights into every session as if current.

Read it **only** when you need the history, and read its own header first. The current
character state is
`data/source/captures/2026-08-06_elric_hammerdin_proc_retest/`. 🛑 **Do not read it at
all if you are re-deriving this build** — see `primer/PLAN_V2_BLIND_REDERIVATION.md`;
the comparison it sets up is void if the answer is in your context.

## 🖥 The owner's machine — read before emitting a single command

**Windows, PowerShell, and the owner is not a coder.** Every command you print is
something a human copy-pastes verbatim, so it has to run as written.

- **No bash-only syntax.** `&&`, `||`, heredocs (`<<EOF`), `export VAR=`, backtick
  line-continuation and `$(...)` all fail or behave differently. Use `;` to sequence,
  `$env:VAR = "..."` to set, and here-strings (`@"…"@`) if you truly need one.
- **Prefer one command per Bash call** over a chain. A chain that fails halfway leaves
  the owner guessing which half ran.
- **Never hand over a command you have not made copy-pasteable** — no `<fill this in>`
  placeholders in the middle of a line, no assumed working directory. State the `cd`.
- Scripts meant to run on his machine (crawler, extract wrapper, session hooks) target
  Windows: no cron (Task Scheduler), no POSIX tools assumed on PATH. ⚠ Git for Windows
  ships a Unix `find` that **shadows** the Windows one — `3b` lost a guard to exactly
  this. Use absolute paths in `.bat` wrappers.

*Source: the 2026-08-06 usage report — bash `&&` chains and heredoc escaping recurred
across multiple sessions as the top environment friction.*

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
  (decoded, verified byte-exact against ALC's own source).
  `combat_log_parser.py`'s event parsing **is verified against real Ascension
  logs** (2026-08-03: two field-layout bugs found and fixed — 6 base fields,
  `SPELL_MISSED`/`SWING_MISSED` names; details in `tools/log_parser/README.md`).
  ⚠ Use its **named fields**, never hand-indexed columns — the 2e session's one
  parsing error came from a throwaway script hand-counting columns and reading
  `glancing` where it wanted `critical`. Re-verify only if Ascension changes the
  client's log grammar.

  🛑 **A log the game is still writing to is not a capture.** Before parsing anything
  under `data/source/captures/`: confirm the file's size and mtime are unchanged across
  a short interval, then report **line count, first and last timestamp, and window
  duration** before any number is derived from it. A 2026-08-05 session analysed a
  truncated 46-second window this way and had to redo the work. ⚠ **A guard that
  cannot run must say so** — `3b` found the owner-facing "is the game closed?" check
  printing *"OK - game is closed"* after erroring. Never report a condition you failed
  to test.
  ⚠ **Flag any conclusion drawn from under ~60 s of data as provisional**, in the
  output, not just in your head.

- **Need a spell's APPLIED SP/AP coefficient, or its trigger links** → run
  `tools/scrapers/scrape_ascension_db.py`. `db.ascension.gg` states coefficients
  outright (`Scaling #1: +29.00% of spell power`), which the client **cannot** —
  Ascension keeps applied coefficients in tooltip text, not numeric fields. It also
  states `EffectTriggerSpell` links (HoJ → HftH, from the page's own `href`).
  🛑 Trust a scraped coefficient only on a `cross_check` verdict of **`agree`** —
  the page's base value must reproduce our client-decoded flat; `unverifiable` is
  not a pass. **Scope by measured demand, never enumeration** (`--plan` first;
  `--coverage 0.90` = 285 ids). Don't hand-fetch spell pages one at a time.

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

⚠ **`--with-dbc` is OWNER-GATED, and a path only it exercises can stay broken
for sessions while every routine rebuild reports green** (measured: its exporter
crashed from `2e` to 2026-08-06 undetected). Its last **successful** run is the
staleness clock, not its last commit. The owner runs it by double-clicking
`run_dbc_extract.bat`; its scope now includes
`data/source/dbc/extract_scope_observed_ids.json` (log-observed ids — every
other scope rule starts from the catalog and misses what players actually cast).

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
  ⚠ Scope, sharpened 2026-08-06: this targets **DBC** descriptions, which are tooltip
  *templates* with `$` variables and hand-rolled scaling. An **already-rendered**
  third-party string (the crawl's item text) is admissible **only when it carries its
  own check digit and the check is enforced** — weapon damage is parsed that way and
  validated against the same string's stated DPS, 849/849 (`core/builds/gear.py`).
- **Never map an item NAME to stats.** Gear stats are rolled at drop by tier, so 476 of
  1,157 names in the corpus span several item_ids with different stat blocks. Key on
  `item_id`, which encodes the difficulty and is lossless; treat
  `snapshot_gear.stats_match_type = 'name_fallback'` as suspect.
- **A stat block is not a character's inputs — weapon damage is in no stat block.**
  Building a character from stat blocks alone gives it no weapon, zeroing white swings
  and every weapon-percent ability. Read `snapshot_gear.weapon_json`.
- **Never read an SP/AP coefficient from `EffectBonusCoefficient`.** It is stock 3.3.5's
  `EffectBonusMultiplier` — a multiplier on the default, whose neutral value is **1.0**.
  7,647 of 9,211 non-zero values are exactly 1.0, and it matches a spell's own stated
  `$SP*x`/`$AP*x` in 4 of 98 cases. **Ascension keeps applied coefficients in tooltip
  text.** Use `spell_effect_values` for flats; the column there is `bonus_multiplier`.
- **Coefficients scale with rank, so check the rank before trusting one too** — not just
  flats. Catalog entries are stored at Rank 1, which is where retail's low-rank penalty
  is deepest (Sun Down SP 0.4 vs 1.3 at level 60).
- **Check the rank before trusting a magnitude.** The catalog stores the wrong rank for ~half of all
  multi-rank cards (697 of 1,409), usually Rank 1 — up to a 10× error on flat values. Rank is
  level-gated: highest rank in the line with `SpellLevel` ≤ character level. Use `dbc_spell_rank`.
- **Scope card queries to `dbc_character_advancement.in_current_pool = 1`** (3,129 of 10,231). The
  rest are other realms'/modes' entries and are the main source of duplicate-name confusion.
- **Never read a flat magnitude off a catalog entry without checking the rank.** Use
  `core.spells.ranks.rank_for_level()` or the `catalog_vs_live` crosswalk rows.

## Repo conventions

- 🆕 **Every file in `primer/` carries a STATUS LINE, and only `LIVE` documents may be
  cited as current truth** (`3f` F8c, 2026-08-07). `LIVE` = must be true today ·
  `HISTORICAL` = a past session or completed phase, **may contain claims that are false
  today, and that is correct** · `SUPERSEDED BY <path>` · `FINDING <date>` = true as of its
  date, not maintained. 🆕 **The census is GENERATED — do not retype it here.**
  `py tools/audit/check_refusals.py` prints it and asserts that no file is unclassified;
  as generated 2026-08-07:

  ```
  [census] primer/ status lines: 59 files — 14 LIVE / 35 HISTORICAL / 2 SUPERSEDED / 8 FINDING
  ```

  ⚠ This line previously read `13 / 32 / 0 / 6`, typed by hand, and was **wrong within a day
  of being written** — two documents landed and nothing recounted. It is the standing rule's
  own failure mode sitting in the file every session reads first. Two files are still flagged
  uncertain in `PROGRESS.md`'s blocked table. **A new document is born with a status line and
  with its expiry condition stated** — *"superseded when X lands"* — in the commit that
  creates it. Status acquired
  in a later cleanup is status nobody trusted in between. Full rule in
  `primer/START_HERE_FOR_CODE.md`.
- 🆕 **A magnitude never appears in a markdown file except as generated output, pasted with
  its provenance.** Every numeric error the `3e` audit found in a document was
  hand-transcribed — **four for four, and zero errors in numbers a tool emitted**. If a
  number belongs in a document, have the tool print it and paste that. Where no tool prints
  it, the number has no owner.
- 🆕 **Every check carries a registered test that makes it fail** — name the mutation, and
  **run it**. `3f` found four of its own checks vacuous only by running the mutation.
  Registry: `primer/ENGINE_BUGS.md`. If you cannot name one, it is not a check.
- 🆕 **A defect check names BOTH mutations: the one that turns it RED, and the change that
  turns it GREEN — and the green one must be the FIX, not a stub** (`3g` G5, 2026-08-07).
  The red half alone is half a rule. The `3f` audit found **three registered checks that
  could never turn green from their own fix**: one gated on `hasattr(T,
  "_roll_uses_combo_points")` for a function that exists nowhere in the tree, so the only
  way to close it was to add a stub with that name; one asserted on `self_health_pct` after
  calling a function that touches only `target_health_pct`; one re-implemented the
  discriminator it was testing instead of importing it, so it could only go green on a
  *regression*. **A check that cannot go green is not a check — it is a permanent alarm, and
  it will be silenced rather than satisfied.** Where a defect is registered but not yet
  fixed, create the **seam** the fix lands in and point the check at it, so the green path is
  reachable before it is taken.
  🛑 **Run the green path too.** `3g` named E12's as *"thread `combo_points` through
  `roll_hit`/`roll_cast`"*, applied exactly that, and the check **stayed red** — the
  parameter has to reach `_components`, not just the signatures. A green path that has only
  been named is a guess about your own code.
- **Layout** (Phase 1 T1, 2026-08-04): `core/` is pure logic — no `print()`, no
  `argparse`, no paths, takes a connection as a parameter. Only `config.py` knows
  where files live, and `core/` may not import it. `tools/audit/check_core_purity.py`
  enforces this; run it after touching `core/`.
- `data/source/` is committed and irreplaceable; `data/derived/` is gitignored and
  always rebuildable. Never commit a `.db`.
- **Before every commit: `git status --short`, and check for any staged file over 5 MB.**
  Never commit a built database or a raw DBC dump — they belong in `.gitignore` or the
  two-tier manifest model. One commit took the repo to 194 MB and needed an amend.
  Write the commit message **at commit time**; a message staged during an earlier
  attempt describes work that has since changed.
- Scouted-build data lives in `data/derived/scouted_builds.db`, kept separate from
  `ascension.db` — never merge them.
- Analysis write-ups for scouted builds go in
  `builds/shared/scouted_<name>_<date>.md`, matching the `synergy_*.md`
  convention.
- Whenever a verdict changes (retraction, new resolution, updated stat
  weight), update `seed_confirmed.py` in the same session so the next index
  rebuild picks it up — don't just note it in prose.
- **Spotted a game bug or a tooltip-vs-log discrepancy? Log it in `bugs/`.** The owner
  submits these to Ascension when he has time, so they must survive the session. Add a
  row to `bugs/README.md`; write the full field-by-field report only once the evidence
  holds, otherwise file it `needs verification` and name the missing check. ⚠ **The
  in-game form's title field caps at 50 characters** — put spell ids and figures in the
  Issue body. House style and the full form spec are in `bugs/README.md`.
