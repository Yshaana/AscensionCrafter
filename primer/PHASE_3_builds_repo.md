# PHASE 3 — The Builds Repo (Layer 2) — v2

**Read `00_ARCHITECTURE.md`, Phase 1, and Phase 2 first.**

The crude crawler has run since Phase 0; raw NDJSON has been accumulating. This phase turns that pile
into a queryable corpus and adds the live-capture path.

**The reframe that matters:** this is not just "other people's builds to copy." It's a **measurement
instrument.** Pooled across hundreds of characters it settles mechanics questions no single parse
can — which is why it feeds Layer 1, not only Layer 4.

---

## Task 1 — Normalise the crawl

`data/derived/builds.db`, built from the crawl NDJSON, never itself committed (§2.12).
⚠ *(post-3a audit, 2026-08-06)* Only **tier-1** of that NDJSON is committed; the
ability/avoidance/performance bulk is gitignored **tier-2** (re-fetchable per
report, audited via each day folder's committed `tier2_manifest.json`), so the
full corpus is **not** reproducible from a clean checkout alone.

```sql
CREATE TABLE characters (
  character_id INTEGER PRIMARY KEY,
  name TEXT, realm TEXT, guild TEXT, level INTEGER,
  primary_role TEXT,              -- 'dps','tank','healer','unknown'
  source TEXT NOT NULL,           -- 'crawled','user_provided','manual'
  first_seen_at TEXT, last_seen_at TEXT
);

CREATE TABLE character_snapshots (
  snapshot_id  INTEGER PRIMARY KEY,
  character_id INTEGER NOT NULL REFERENCES characters(character_id),
  captured_at  TEXT NOT NULL,
  patch_id     INTEGER, season TEXT, realm TEXT, phase_id INTEGER,
  path TEXT, spec_index INTEGER,
  stats_json   TEXT,              -- resolved stats at capture
  source       TEXT NOT NULL
);

CREATE TABLE snapshot_cards (
  snapshot_id INTEGER NOT NULL REFERENCES character_snapshots(snapshot_id),
  tree TEXT NOT NULL,             -- 'abilities' | 'talents'
  external_id TEXT NOT NULL,      -- raw, as captured
  spell_id INTEGER,               -- resolved via crosswalk at BUILD time, not capture time
  spell_id_confidence TEXT,
  name TEXT, rank INTEGER, max_rank INTEGER,
  per_rank_tooltip_json TEXT
);

CREATE TABLE snapshot_gear (
  snapshot_id INTEGER NOT NULL REFERENCES character_snapshots(snapshot_id),
  slot TEXT NOT NULL,
  item_id INTEGER, item_name TEXT, quality INTEGER, item_level INTEGER,
  enchant_id INTEGER, gems_json TEXT,
  stats_json TEXT, drop_source TEXT, tier TEXT
);

CREATE TABLE encounters (
  encounter_id INTEGER PRIMARY KEY,
  report_id INTEGER, external_encounter_id INTEGER,
  zone TEXT, boss_name TEXT, difficulty TEXT, is_trash INTEGER,
  content_type TEXT,              -- 'raid','world_boss','dungeon_normal','dungeon_mythic','solo'
  content_type_confidence TEXT,   -- 'api_reported','inferred','unknown'
  target_count INTEGER,           -- NULL if unknown. NEVER defaulted to 1
  target_count_confidence TEXT,
  duration_seconds REAL,
  occurred_at TEXT, patch_id INTEGER, realm TEXT, season TEXT, phase_id INTEGER
);

CREATE TABLE encounter_performance (
  encounter_id INTEGER NOT NULL REFERENCES encounters(encounter_id),
  character_id INTEGER NOT NULL,
  snapshot_id INTEGER,            -- nearest-in-time build; NULL if none close enough
  snapshot_lag_hours REAL,        -- how stale the matched build is — honesty about the join
  role TEXT,
  total_damage REAL, dps REAL,
  total_healing REAL, hps REAL,
  damage_taken REAL, deaths INTEGER,
  percentile REAL
);

CREATE TABLE ability_performance (
  encounter_id INTEGER NOT NULL,
  character_id INTEGER NOT NULL,
  spell_id INTEGER, external_id TEXT, spell_name TEXT,
  hits INTEGER, crits INTEGER,
  misses INTEGER, dodges INTEGER, parries INTEGER,
  resists_partial INTEGER, resists_full INTEGER, immunes INTEGER,
  damage_total REAL, healing_total REAL, damage_share_pct REAL
);
```

**Four things the old design got wrong:**

1. **Avoidance columns exist.** The old schema had hits and crits only. The avoidance endpoint
   returns full miss/dodge/parry/resist counts per player ability — throwing that away discards the
   ground truth for `rolls_hit_check` and `can_be_full_resisted`.
2. **`snapshot_lag_hours` is explicit.** Joining a parse to a build snapshot taken days later is a
   guess. Record how big the guess is instead of hiding it, and let analysis filter on it.
3. **`content_type` is stored, not derived at query time.** §2.9's profiles need it, and it's better
   resolved once at ingest with a confidence tag than re-inferred inconsistently everywhere.
4. **Healing and damage-taken columns exist**, per §2.8 — even if only DPS is modelled at first, the
   data cannot be backfilled later.

**Spell-ID resolution happens at rebuild time, never at capture time.** A crosswalk improvement then
re-resolves everything without re-crawling.

**Provenance:** `user_provided` is trusted over `crawled` on conflict (the user was there watching);
stale `user_provided` gets a louder staleness flag.

**Derive `ContentProfile` presets from this table** (Phase 2 T2) — real observed target counts, fight
durations, and content types beat invented ones. Report what the real distribution looks like; the
sim's 1/3/15 defaults should be checked against it, not assumed.

---

## Task 2 — Pooled mechanics inference (feeds Layer 1)

**The highest-leverage analysis in the project**, and a byproduct of data already collected.

Primer §5 says crit-rate questions need thousands of hits, and that parsing crit% per source is the
cheapest mechanics test available. It's been done one parse at a time. Pooled, it becomes a standing
automated sweep.

```python
# core/builds/inference.py
def infer_crit_table(spell_id) -> dict:
    """Regress each character's observed crit% against their melee crit rating and their spell
    crit rating. Whichever correlates is the table. Returns verdict, both correlations, total
    sample size, contributing character count, and a CONFIDENCE INTERVAL."""

def infer_hit_check(spell_id) -> dict:
    """Pooled misses/dodges/parries. Zero avoidance across a large sample against known-level
    targets => rolls_hit_check=0. The Hammer from the Heavens result (4,962 hits, 11 characters,
    0 avoided) generalised into a sweep."""

def infer_proc_rate(proc_spell_id, trigger_spell_ids) -> dict
def infer_partial_resist(spell_id) -> dict
def infer_coefficient(spell_id, term) -> dict
    """Regress observed damage against contributing stats across characters. Weak for
    multi-term formulas; report the R² honestly and refuse when the terms aren't separable."""
```

**Rules that make this trustworthy rather than a source of confident garbage:**

- **Writes to a staging table for human review. Never auto-seeds `spell_mechanics`.** It proposes
  with sample sizes and confidence; a human promotes.
- **Patch-partitioned.** Never pool hits across a patch that changed the ability. Check
  `patch_entry_spells` and split.
- **Realm- and season-partitioned** (§2.5).
- **Requires per-character stats.** Depends on Phase 0 T2's finding. If stats exist only on the
  armory snapshot and not per-parse, `snapshot_lag_hours` gates which samples are usable — say so in
  the output rather than pooling everything.
- **Reports sample size prominently and refuses below threshold.** If candidate values are within ~3
  points, the correct output is **"insufficient discriminator"**, not a number.
- **Target-level aware.** Miss rates differ ~6% vs ~17% between +2 and +3; pooling across content
  levels produces a meaningless average.
- **Emits a measured confidence interval**, which then **overrides the default uncertainty range**
  in `spell_mechanics` (Phase 1 T4) and is marked with `basis='measured'`. This is how the heuristic
  ±10%/±25% defaults get replaced by real numbers over time.

Run across the catalog periodically; feed results into the verification queue ranked by
`variance_contribution`.

---

## Task 3 — Search and analysis

```python
# core/builds/search.py
def find_builds(abilities=None, talents=None, path=None, role=None, content_type=None,
                min_dps=None, source=None, max_staleness_days=None) -> list[dict]
```

**Then the analyses the corpus makes possible:**

| Function | Answers |
|---|---|
| `co_occurrence(spell_id)` | Cards appearing alongside this one far above chance. **Market-basket analysis over hundreds of builds — how you discover synergies other players already found** |
| `ability_performance_percentiles(spell_id, content_type)` | Typical damage share and its spread. High variance = build-sensitive; tight = it does what it does |
| `meta_snapshot(patch_id)` | What's played, and how it shifted after a patch. Daily patching makes this a real moving thing |
| `outliers(metric, content_type)` | Characters far above their cohort — the highest-value scouting targets, found by query not browsing |
| `path_performance(content_type)` | Real DPS distribution per Path per content type — empirical ground truth against `compare_paths()` |
| `item_usage(slot, path, phase)` | What top performers actually wear. Feeds Task 4 |
| `role_distribution()` | How many crawled characters are tanks/healers — sizes how well non-DPS roles can be supported empirically |

---

## Task 4 — Gear data (scope depends on Phase 0 Task 9)

🛑 **Read Phase 0 Task 9's verdict before scoping this task.**

### 🚨 SUPERSEDING NOTE (2026-08-06, `PLAN_3B_UPDATE.md` + session `3b`)

**This task's original text below treats gear as native 3.3.5. It is not.**
Item stats are **rolled at drop as a function of tier** — raid difficulty
(Normal / Heroic / Mythic / Ascended) or M+ keystone level, with the M+ cap a
timeline parameter — plus post-drop upgrades (Mythic Coins). Level is constant
at 60, so level is not an axis. Three consequences that override anything
below:

1. **Scope is STAT WEIGHTS, not gear suggestions.** BisBeard owns the item
   matrix and the optimizer; we emit a weight vector the player pastes in.
   Do **not** build `optimize_gearset`, a BiS optimizer, or an ingestion of
   BisBeard's item matrix. This also **dissolves the 3a audit's circularity
   flag** — "the `items` table agreeing with BisBeard checks our weights, not
   our items" was only a problem if we claimed to be an independent item
   source, and we don't. Checking the weights *is* the job.
2. **Never map item NAME -> stats** — 476 of 1,157 names span several item_ids
   at different difficulties with different stat blocks. ✅ **But keying on
   `item_id` is lossless**: every variant carries its own id and
   `item_id -> (tier, stats)` is a function (measured: 0 ids carry two stat
   blocks). So the deduped `items` table is safe as a stat source, and
   `PLAN_3B` §3.2's "the dedup collapses real differences" is **amended** —
   the hazard is the name. Watch `snapshot_gear.stats_match_type`, which flags
   the crawl's own name-matched blocks.
3. **Report gear-stat resolution COVERAGE per character** (`gear_coverage()`).
   A character with unresolved pieces is simmed at too-low stats and produces
   the same negative delta as a missing buff — the calibration miss cannot be
   attributed until coverage is known. ⚠ Coverage is **not repairable from the
   corpus**: an unresolved item is unresolved on every snapshot.

🚨 **And the one that actually moved the gate: weapon damage is in NO stat
block.** It exists only in the rendered item description and must be parsed
with the description's own stated DPS as a check digit
(`core/builds/gear.py :: parse_weapon_damage`). Without it a crawled character
sims with no weapon at all.

🆕 **And the source that unblocks Task 2's coefficient work (2026-08-06):**
`db.ascension.gg` states applied SP/AP coefficients and `EffectTriggerSpell`
links outright — `tools/scrapers/scrape_ascension_db.py`. This is what
`infer_coefficient()` was never going to reach by regression (pooled data
cannot isolate single stats, which is why it correctly refuses): the
coefficient is *stated*, not inferred. 🛑 Only `cross_check == 'agree'` rows
may be used; `unverifiable` is not a pass.

**Still to do here:** `PLAN_3B` §4's accessible-ceiling object (open raids ×
difficulties × current M+ cap, parsed from the timeline, bounding the sim and
the weight sweep) and §6's two-vector weight emitter — the latter **only after
the sim passes the gate**, which currently rests on one qualified character.

**BisBeard (`s10.bisbeard.com`) already does stat-weight-driven BiS optimization for Ascension S10,
with phase- and content-filtered gear.** Building a competing optimizer is weeks of work for a worse
result. The division of labour is clean and it's the reason stat weights were worth deriving:

| Capability | Owner |
|---|---|
| Item database, phase tagging, content filtering | **BisBeard** |
| Stat-weight-driven BiS selection | **BisBeard** |
| **Deriving the stat weights** (needs a simulator) | **Us** — nobody else has one |
| Gear→stats for the sim's three-tier scaling curve | **Us**, internally |

### Two scope paths

**Path A — BisBeard's data is reachable (preferred).** Build only what the sim needs:
- Extract item stat blocks per phase into the `items` table below
- Implement `export_stat_weights(build_spec, content)` in BisBeard's input format
- Implement build-string encode/decode if Phase 0 T9 found the format, so builds round-trip
- **Do not build `optimize_gearset()`.** Point the guide's gearing section at BisBeard instead
- Cross-check our `compute_stats()` against BisBeard's talent audit on 3–5 known builds. A
  disagreement is a finding — file it as an open question rather than assuming either side is right

**Path B — BisBeard's data is not reachable.** Build the item database from what we already have.
`snapshot_gear` captures per-slot item, enchant, gems, resolved stats, drop source, and tier —
deduped by `item_id` across hundreds of characters, that **is** an item database, assembled as a
byproduct. Enrich from db.ascension.gg's item pages (Phase 0 T1) for items nobody crawled. Then
implement `optimize_gearset()` as originally specced below.

**Either path needs the `items` table**, because the sim's gear tiers read from it.

```sql
CREATE TABLE items (
  item_id INTEGER PRIMARY KEY,
  name TEXT, quality INTEGER, slot TEXT, item_level INTEGER,
  stats_json TEXT, sockets_json TEXT,
  drop_source TEXT, source_category TEXT, tier TEXT,
  phase_id INTEGER,               -- which server phase this becomes available
  first_seen_at TEXT, seen_count INTEGER   -- popularity signal
);
```

```python
# core/builds/gear.py  — BOTH PATHS
def gear_tier_stats(phase_id, path, role) -> dict[str, StatBlock]:
    """Fresh / mid / BiS stat blocks for a given server phase. Feeds Phase 2 T7's scaling curve.
    This is the minimum the sim needs and is required on both paths."""

def export_stat_weights(build_spec, content, target='bisbeard') -> str:
    """Emit our derived weights in an external optimizer's input format."""

# PATH B ONLY — skip entirely if BisBeard handles optimization
def rank_items(slot, stat_weights, filters=None) -> list[dict]
def optimize_gearset(build_spec, stat_weights, phase=None, available_only=False) -> dict:
    """Best item per slot subject to constraints, with a shopping list BY DROP SOURCE."""
```

`phase_id` supports §2.10: BiS for phase 1 is not BiS for phase 3. **S10 is on Phase 1 (Zul'Gurub);
Phase 2 starts 2026-08-08** — so `gear_tier_stats()` must be phase-parameterised from the start, not
retrofitted. A hardcoded "current BiS" would be wrong within days of being written.

**Cross-validate against `item_usage()` on either path.** If the recommended gear disagrees with what
every top performer actually wears, that's a signal the weights or item data are wrong — worth
investigating, not dismissing. This check is *more* valuable on Path A, not less: it's the only
independent test of whether our stat weights are any good once an external tool is consuming them.

---

## Task 5 — The capture addon

Sequenced here deliberately: highest effort, lowest certainty, and the crawler covers most of its
value.

**Scope: active spec only.** Inactive specs are frequently stale — not rerolled to current owned
cards, gear from a different playstyle, or parked. Capturing them manufactures exactly the failure
mode the auto-debugger exists to catch.

**Confirmed: gear is per-spec, not character-global.** There's no single "the character's gear," only
"this spec's gear right now."

Extends `AscensionCrafterExport` (proof full custom addons are permitted even though WeakAura
custom-function triggers are sandboxed).

### 🆕 REQUIREMENT — self-snapshot goes FIRST in every capture list

**Owner request, 2026-08-04. Deliberately deferred to this phase rather than hacked in early —
"we can wait and do it properly."**

**The requirement:** whenever the addon captures inspected players, it **first appends a snapshot of
the owner's own character** — active spec's gear, talents/abilities with ranks, and resolved stats —
at the **top of the pending list**, before any inspected player. Every capture batch is therefore
self-stamped: "here is what *I* looked like when I met these people."

The owner is in the logs he collects. That single fact is what makes this cheap and valuable at the
same time — no extra play session, no separate workflow, just an entry the addon writes anyway.

**Why — do not lose this reasoning, it is the whole justification:**

1. **It closes an open risk this plan already named.** Phase 0 Task 2 flags *per-parse character
   stats* as load-bearing: if stats exist only on an armory snapshot and not per parse, Task 2's
   pooled inference (regressing observed crit% against each character's real crit rating) must
   approximate from the nearest-in-time capture. For other players we are stuck with that
   approximation. For the owner, self-capture makes it **exact** — stats as they were at the moment
   of the fight.
2. **§2.2's tier-1 rule demands it regardless.** *"A tooltip is a measurement of the character, not
   the spell … always capture the character's stats alongside, or the number can't be interpreted
   later."* This is that rule automated instead of remembered. Holy Supernova's 2.00s base reading
   as 1.61s in-game is the standing example of what goes wrong without it.
3. **It is the only source of *measured* gear-scaling curves.** §2.10 requires builds be evaluated as
   curves across gear tiers "derived per server phase from the builds repo, not hardcoded." A
   season-long series of self-snapshots is the same build observed at many gear levels — real
   scaling, not a model. Nothing else in this stack produces it, and it is what catches
   "great now, dead later."
4. **It makes the owner the calibration anchor for Phase 2's gate** ("reproduces ≥3 real parses
   within stated tolerance"). His are the only parses where exact stats, the complete log, *and*
   control over what he does all coexist — tier-1 and tier-2 evidence on one subject.

**Consequence for sequencing:** the two 🛑 stop-points below (`ReloadUI()` availability, combat-log
naming) become **more** important, not less. A self-snapshot is worthless if the write never flushes,
or if it can't be correlated to a specific log file. Both are cheap for the owner to answer in-game
and both sit in `PROGRESS.md`'s blocked table.

**Precedent that this is feasible:** `AscensionCrafterExport`'s manual `/acexport` already gathers
exactly these fields — stats, per-slot gear, crit by school — and produced the Path of Duality
three-way test (`wip_winds-of-winter-frostblade.md` §4). The addon work is automating *when* it
fires and *where* it writes, not inventing the capture itself.

- On inspect: active spec's talents/abilities with ranks, full per-slot gear with enchants and gems,
  resolved stats, spec index, zone/instance, timestamp
- **Appends to a growing SavedVariables list, never overwrites.** Six players met in one raid = six
  pending entries. The ingestion pipeline clears them, not the addon
- ~~Exports an encoded blob to a copyable in-game frame~~ — **dropped, see the delivery model below**
- **SavedVariables only flush on logout or `/reload`** — a Lua addon has no other write path

### 🆕 DELIVERY MODEL — settled 2026-08-04 (owner's design)

**No `ReloadUI()` call. The addon never forces a flush.** Data lands on disk when the owner quits
the game normally, which is the natural end of a play session anyway. Claude Code then reads the
file directly at the start of the next working session, alongside the combat logs. Simpler addon, no
disruption to play, and the in-combat/taint questions become moot.

**Verified paths on the owner's machine (2026-08-04):**

```
SavedVariables:  <launcher>\resources\ascension-live\WTF\Account\Yshaana\SavedVariables\<Addon>.lua
Combat logs:     <launcher>\resources\ascension-live\Logs\YYYY-MM-DD-HH.MM.SS WoWCombatLog.txt
Darkmoon S10 characters: Elric, Testouille, Yshaana
```

Precedent that this works on this client: `AscensionLogsCompanion.lua` already writes into that exact
folder. WoW also keeps one previous generation as `<Addon>.lua.bak` — a free recovery net if a flush
is ever interrupted.

⚠ **Correction to the "1 file per session" assumption — this shapes the implementation.**
SavedVariables is **one file per addon, rewritten wholesale on every flush**. An addon cannot choose
its filename or emit a new file per session; the name is fixed by the addon name. So "one file per
session" is not achievable and shouldn't be designed toward.

**What delivers the same outcome:** the addon loads its saved table at login, **appends** this
session's entries, and saves at logout — producing **one file containing a growing list, with one
self-snapshot entry per session**. That is already what this task specifies ("appends to a growing
SavedVariables list, never overwrites; the ingestion pipeline clears them, not the addon"), so the
owner's intent and the existing design agree — only the mechanism differs from how it was pictured.
Each entry must stamp **character + realm + timestamp**, since the file is account-level and covers
Elric/Testouille/Yshaana together.

**Two simplifications this unlocks — real complexity removed, not deferred:**

1. **No encoding, no copyable in-game frame.** Both existed only to get data through a *chat* window
   by copy-paste. Claude Code reads the file off disk, so the addon can write plain, readable Lua
   tables — far easier to parse, diff and debug. Chat-only sessions are still served, because the
   ingestion pipeline commits a normalised extract to the repo (§2.12).
2. **`## SavedVariables:` must be added to the `.toc`** — the current `AscensionCrafterExport.toc`
   declares none, which is precisely why it is copy-paste-only today. Use account-level
   `## SavedVariables:` (not `SavedVariablesPerCharacter`) so one file covers every character.

**The one real tradeoff, stated plainly:** without a forced flush, a client **crash** loses that
session's in-memory captures — the data was never written. WoW does crash. This is accepted as the
cost of a simpler addon. `ReloadUI()` is **confirmed working** (see below) and therefore remains a
known escape hatch if crash-loss ever proves painful — but it is **not being implemented now**, and
no toggle should be built speculatively.

**Session-start workflow for Claude Code:** read the SavedVariables `.lua`, read the `Logs`
directory, correlate entries to logs by the `[start, end]` window rule in Task 6, then normalise and
commit. Requires a small Lua-table parser — the file is a plain `AscensionCrafterExportDB = { … }`
assignment, not JSON.

✅ **RESOLVED 2026-08-04 — `ReloadUI()` works on this server.** Confirmed in-game by the project
owner (tier-1 evidence). The stop-point that stood here is closed: a Lua addon **can** force a
SavedVariables flush on demand rather than waiting for logout, which is what makes self-snapshot
capture practical *mid-session* (capture → optional reload → data on disk) instead of only at the
end of a play session.

Consistent with what was already known: the sandboxing this project hit before was specific to
**WeakAuras' custom-code editor**, not addons generally — which is why `AscensionCrafterExport` works
as a full custom addon. The "don't assume, this server sandboxes things" caution was right to make;
the answer just came back favourable.

*Not established, and not needed for the intended use:* whether `ReloadUI()` is callable **during
combat**, or whether protected-function taint applies. The intended flow is post-inspect and
out-of-combat. Establish before relying on an in-combat reload.

Decoder: extend `decode_inspect_export.py` with the new format, versioned so existing
`inspects.nie.one` fragments still decode.

---

## Task 6 — Combat log ingestion

`tools/log_parser/` already parses `WoWCombatLog.txt` via `AscensionLogsCompanion` into structured
events — **but nothing confirms its output reaches the database.** Close that gap.

**Confirmed: one log file per dungeon/raid run**, not one continuous file. Correlation is matching a
capture to *a specific file*, not slicing a window from a giant log.

**Correlation is many-to-one.** Captures accumulate across a session, so several players met in the
same run fall inside the same file. Group by matched file, parse each **once**, extract every matched
character from that pass.

### ✅ RESOLVED 2026-08-04 — naming, location, AND the correlation rule

Owner supplied the path; verified directly against 3 real logs on his machine. The caution above was
justified — **it is not retail's pattern.**

```
Directory: <launcher>\resources\ascension-live\Logs
           (owner's machine: E:\Ascension Launcher\resources\ascension-live\Logs)
Filename:  YYYY-MM-DD-HH.MM.SS WoWCombatLog.txt
Example:   2026-08-03-21.18.43 WoWCombatLog.txt
```

Note the differences from retail (`WoWCombatLog-<date>_<time>.txt`): the timestamp is a **prefix**
not a suffix, time uses **dots** not colons, and there is a **space** before `WoWCombatLog.txt`.
A pattern guessed from retail would have matched nothing.

**The correlation rule falls straight out, and it's better than expected — no need to open a file to
place it in time:**

| Boundary | Source | Verified |
|---|---|---|
| Window **start** | the filename timestamp | `2026-08-03-21.18.43` ↔ first event `8/3 21:18:43.238` — exact to the second |
| Window **end** | the file's mtime | mtime `21:31:49` ↔ last event `8/3 21:31:49.838` — exact to the second |

So: a capture at local time *T* belongs to the log whose `[start, end]` window contains *T*. The
three observed windows (20:41:34–20:43:55, 20:51:45–21:08:17, 21:18:43–21:31:49) are
**non-overlapping with gaps**, independently confirming "one file per run" and making the match
unambiguous.

⚠ **Three traps to encode, not discover later:**

1. **In-file timestamps carry NO YEAR** — the format is `M/D HH:MM:SS.mmm` (e.g. `8/3 21:18:43.238`).
   The **filename is the only source of the year.** A parser reading timestamps from file contents
   alone cannot date a log, and will mis-order anything spanning a year boundary.
2. **Everything here is LOCAL time** — filename, in-file timestamps, and mtime all agree with each
   other and with local wall-clock. **The crawler stamps UTC** (`captured_at`). Any correlation
   between log data and crawl data must convert; comparing them raw silently mismatches by the
   UTC offset.
3. **The directory is shared with unrelated client logs** (`Trace.txt`, `gx.log`, `Error.txt`,
   `FrameXML.log`, …), and `tools/log_parser/` drops `<logname>.summary.json` beside its input.
   Glob on `* WoWCombatLog.txt` specifically — and make sure it does not also match
   `* WoWCombatLog.summary.json`.

**mtime caveat, stated honestly:** mtime is a *cheap proxy* for the window end and matched the last
event exactly in all observed cases, but it is filesystem metadata — a backup tool, sync client, or
file copy can rewrite it. The authoritative end is the last event timestamp inside the file. Use
mtime to shortlist candidate logs, then confirm from contents before committing a correlation.

*(Incidental observation, n=1, do NOT generalise: the first log line carries spell id `9931032`
("PvE Mode"), far outside the four known ID spaces, while the ascensionlogs API reports
catalog-range ids like `287865` / `907284`. This is a lead for PROGRESS's open "which ID space do
combat logs use?" question — it is not an answer, and per the standing rule two IDs are never
related without fingerprinting.)*

**What logs give that the API doesn't:** full per-second detail — proc timing (ICD detection), buff
uptime, exact sequence ordering, resource flow. That makes logs the strongest source for Task 2's
proc-rate inference specifically.

**Also: this is the ingest path for the prediction ledger** (Phase 2 T9). The user's own logs are the
outcome half of every prediction — wire `prediction_outcomes` population in here.

---

## Task 7 — Session-start automation

Claude Code's `SessionStart` hook (`.claude/settings.json`, project-scoped).

```
tools/session_hooks/check_session_state.sh
  - FAST existence/diff checks only:
      * new addon captures pending?
      * new patches since last session, and do any touch abilities in the user's builds?
      * unreconciled predictions with matching new parses?
  - stdout: a short summary, or nothing
  - KEEP FAST — heavy work doesn't belong in a hook that runs every session

tools/session_hooks/ingest_new_data.py   (what the hook prompts Claude to run)
  - Reads pending captures, groups by matched log file, parses each once
  - Links build + performance into the same encounter row, tags source='user_provided'
  - Reconciles any matched predictions
  - Writes an ingest log entry so nothing is reprocessed
```

**The patch check is the one that matters most day to day.** *"3 patches landed since your last
session; 2 touch abilities in your builds"* is exactly what should greet a new session on a
daily-patching server, and it's a cheap query against Phase 1's tables.

**Fail open.** If the WoW folder isn't found, exit cleanly with no output. Never block a session over
a nice-to-have check.

---

## Task 8 — Refine the crawler

- Broad walk: all zones × phases × difficulties, plus sequential report IDs
- Full historical backfill, once, as a separate job from the daily incremental
- **Re-crawl known characters periodically** to catch respecs — incremental-only misses changes to
  characters already seen. Quick-vs-deep applied to crawling: daily incremental, weekly
  re-verification
- **Capture all roles** — depends on Phase 0 T2 resolving the `role=healer` quirk
- Politeness and rate limiting per Phase 0 findings

---

## Execution order

```
1 (schema)
  → 2 (inference) ─┐
  → 3 (search)    ─┤ independent
  → 4 (gear)      ─┘  (4 needs Phase 2 T7's stat weights)
  → 8 (crawler refinement)
5 (addon) → 6 (logs) → 7 (automation)     [independent chain]
```

## Exit criteria

- 🆕 **INHERITED FROM PHASE 2 (recorded boundary change, PHASE_2 §8.2 / 2e T6):
  the sim reproduces ≥3 real characters within the stated tolerance
  (`predictions/CALIBRATION_TOLERANCE.md`), per content profile.** It lands here
  because simulating a crawled character needs gear (T4's `items` table). Until
  this passes, the sim is not trusted on hypothetical builds — that gate moved
  with the criterion.
  ⚠ **Status 2026-08-06: MET as written (4 of 41), but only 1 of the 4 passes
  with ≥50% of its real damage modelled** — the rest agree on the total while
  the sim reproduces almost none of the kit. The criterion is structurally
  blind to that and was **not** redefined after the result was seen; whether it
  should carry a magnitude-coverage floor is open
  (`crawled_gate_passes_by_compensating_error`) and is an owner decision.
- Every crawled record resolves via the crosswalk; zero string matching remains
- Inference proposes crit-table verdicts with sample sizes for the top ~50 most-played abilities
- At least one default uncertainty range replaced by a measured confidence interval
- `find_builds()` answers the multi-ability queries previously done by hand
- Every parse and snapshot is patch/realm/season stamped
- `ContentProfile` presets are derived from real encounter data, not invented

## Out of scope

Hosted/remote crawling. Real-time scraping. Capturing inactive specs (cut deliberately, not
deferred).
