# Session `1a` — restructure, patch tracking, ID crosswalk (2026-08-04)

**Scope:** Phase 1 Tasks 1–3, plus `TASK_automate_daily_crawler.md` (owner-supplied
mid-session, independent of the schema work).

**Status: complete.** `py cli/rebuild.py` runs 13 steps clean in ~32s from an empty
`data/derived/`. Next session is **`1b`** — `spell_mechanics` (T4) + the relationship
graph (T5).

Two owner decisions taken at the start, not to be re-litigated:

| Question | Decision |
|---|---|
| Where do Phase 1 tables live? | **One database, `data/derived/ascension.db`.** No ATTACH between spells and crosswalk. `scouted_builds.db` stays separate until Phase 3 |
| How aggressive is the restructure? | **Full move + pure-logic split now.** Retrofitting the `core/` boundary after 1b builds on top of it is the expensive version |

---

## Task 1 — restructure

`index/` is gone. Data to `data/source/{export,dbc,scouted}`, scripts to
`ingest/{export,dbc,changelog,logs_gg,addon}`, acquisition runners to
`tools/scrapers/`, reports to `tools/audit/`, addons to `addons/`, derived `.db`
files to `data/derived/` (now gitignored wholesale).

New pure layer:

```
config.py            the ONE place a filesystem layout is written down
core/db/             connection.py, schema.py (catalog DDL + Phase 1 DDL)
core/spells/         text_extraction, ranks, fingerprint, crosswalk,
                     class_resolution, wotlk_class_dictionary
core/changelog/      parse.py
api/                 named, empty, documented — first tenant is T7's spell_profile()
cli/                 rebuild.py, crosswalk.py
tools/audit/         check_core_purity.py, tooltip_diff_report.py
```

**The purity rule is enforced, not documented.** `tools/audit/check_core_purity.py`
walks the AST of every file in `core/` and fails on `print()`, `argparse`, `sys.argv`,
imports of `config`/`cli`/`ingest`/`tools`/`api`, or a self-opened `sqlite3.connect`.
Currently **0 violations across 12 files**, with exactly one named exemption
(`core/db/connection.py`, whose job is opening connections and which still takes the
path as a parameter). Run it after touching `core/`.

Verified against the Phase 0 baseline, every number matching `RECON_FINDINGS`: 3,061
spells, 887 hidden formulas, 387 borrowed-modifier classes, 113 facts, 15,769
`spell_dbc_raw` rows, 1080/1080 hidden refs resolved, 84/887 into `spell_scaling`,
3,129 `in_current_pool`.

### Two findings the move surfaced

**1. `owned_cards` should never have had a foreign key.** Turning on the
`foreign_keys` pragma rejected **47 of the owner's own 4,465 owned-card rows** (39
distinct spellIds). They are not bad data — **all 39 resolve in
`CharacterAdvancement.dbc`** and are simply missing from `spell-export.json`. That is
Phase 0 finding #5 (*the export goes stale within days*) reproduced from his own
collection, which is a stronger demonstration than the changelog version of it. FK
dropped, count now reported on every build. Look those cards up in the CA table, never
in `spells`.

**2. `spell_dbc_raw` was missing fields the fingerprint hard rule explicitly names.**
The rule says compare *radius, **cooldown**, cast type, **resource cost**, effect
structure* — and cooldown and power type were not stored anywhere. Added 17 scalar
columns (`recovery_time`, `casting_time_index`, `power_type`, `spell_level`,
`start_recovery_time`, proc fields, …), which T4 needs regardless.

⚠ **And the extract exporter was a hardcoded column list**, so those 17 columns were
invisible to every session without the game client. Now `SELECT *`. Worth remembering:
`data/source/dbc/*.json` is the *only* channel from the client to everyone else, so a
column added to the table and forgotten in the exporter fails silently and only for
people who cannot check.

---

## Task 2 — patch, realm, season tracking

Five tables (`seasons`, `server_phases`, `patches`, `patch_entries`,
`patch_entry_spells`), classification in `core/changelog/parse.py`, ingestion in
`ingest/changelog/ingest_changelog.py`.

Seeded S10 Phase 1 (Zul'Gurub → 2026-08-08) and Phase 2. `server_phases` deliberately
keeps **two** numbers: `phase_number` is the server's own label, `api_phase_number` is
the logs API's field, and they disagree — the API's `phase_number=2` record is *named*
"Phase 1.1".

Current-era Darkmoon slice: **10 patches, 159 entries, 301 name links, all 301
resolving to a card.** 141 of 159 are **not yet live** — status parsing is mandatory,
not decoration.

### `change_direction` took three passes, and the failures are the useful part

The final rule is not the obvious one, so it is worth writing down why the obvious
ones fail:

1. **The new-card pattern matched nothing.** Live wording is *"A new Talent/Mystic
   Enchant is now available!"*, also *"A new Conquest of Azeroth Talent/Mystic
   Enchant…"*, also *"A new Legendary Talent and Talent Card…"*. A regex pinning the
   noun directly before "is now available" matched **0 of 52**, so every new card was
   classified `nerf` — their body text is usually "X and Y reduce Z's cooldown". Fix:
   match the *frame* (`a new … is now available`), not the noun.
2. **Inverting the comparative for cost-like quantities got 10 of 13 nerfs wrong.**
   "reduces X's cooldown … **up from** 1s" inverts *twice*. What actually holds is
   simpler: **a reduction applied to a cooldown, cost, cast time or damage taken is a
   buff**, whichever direction word sits beside it.
3. **Bare `lower` is ordinary English** ("at lower levels"), not a nerf verb. Only the
   past participle is a change verb.

Final split, with every buff and nerf hand-checked against the raw text:
**64 buff / 19 fix / 3 nerf / 52 new_card / 21 neutral.** The 52 new cards match Phase
0's independent count exactly, and **0** are unknown to the client — exactly as Phase 0
predicted, so the changelog remains a change-history source, not a discovery source.
The 21 neutrals are genuine reworks and "can now trigger X" additions; per the task's
own instruction they are left neutral rather than guessed.

---

## Task 3 — the ID crosswalk

`spell_id_crosswalk`, four external ID spaces:

| source | rows | distinct ids | conflicts |
|---|---|---|---|
| `character_advancement` | 14,661 | 10,231 | 8 |
| `catalog_vs_live` | 738 | 711 | 52 |
| `logs_gg.entry_id` | 1,719 | 1,487 | 0 |
| `card_id` | 4,465 | 4,465 | 0 |

`py cli/crosswalk.py --validate` re-runs Phase 0 Task 5's checks against live data:

- **1,487/1,487** observed entry_ids resolve through CharacterAdvancement
- **3,061/3,061** catalog ids reachable from some CA rank slot
- **4 numeric entry_id ↔ spells.id collisions, 0 real matches.** Phase 0 saw one;
  with more data there are four (`1152` is `Path of Healing` in the crawl and `Purify`
  in the catalog). **The never-join rule gets stronger with more data, not weaker.**

The 15× rank trap is now a query:

```
$ py cli/crosswalk.py --resolve 40094
entry_id 40094 rank 1 -> card spell 1459 -> level-60 spell 10157  (rank differs!)   (not in catalog)
```

**Two things deliberately NOT built**, with reasons, so a future session doesn't add
them thinking they were forgotten:

- **`wotlk_rank`** as its own space — superseded. `dbc_spell_rank` is the one home for
  rank lines; duplicating 42,606 rows into the crosswalk creates a second home for the
  same fact. `catalog_vs_live` carries the part that does work.
- **An `id_proximity` (±1–3) resolver** — the contiguous-rank rule was **retracted** in
  Phase 0 (4,791 non-contiguous lines vs 1,908). Adding it back at `inferred`
  confidence would reintroduce a disproven heuristic, which is worse than not answering.

Also seeded `class_origin` from the client's renamed skill lines:
**394 → 1,794 of 3,061 (58.6%)**, matching Phase 0's 58%. All 5 known class conflicts
surfaced in `spells.class_conflict_json`, none auto-resolved (§2.3). Note the fifth,
Fel Infused Weapon, arrives via `seed_confirmed.py` at tier `conflict` rather than
through the new resolver, because `seed_confirmed` runs later in the chain and should
win — it is the doc-sourced tier.

### Two Phase 0 numbers refined — same root cause

Both because the original reporter used `max()`, which silently returns the **first**
of a tie:

- **697 wrong-rank catalog entries is a lower bound; the real figure is 711**, of which
  **25 are genuinely ambiguous** — several spells tie for the top rank available at 60.
  Two real causes: a line whose members *all* read "Rank 1" (`Desolation`, 5 members),
  and a line pulling in an other-realm 11-prefix variant (`Arcane Focus` → `912840`
  **and** `1212840`). Recorded as conflicts, never tie-broken; `resolve_entry_id()`
  returns `level_spell_id=None` plus the candidate list.
- **The fingerprint rule needed two field sets.** The strict set answers *"same
  ability?"*. It is the wrong test for *"two ranks of one ability?"* — rank
  legitimately changes radius, cooldown and `power_type`, and higher ranks **fill
  effect slots** the lower rank leaves empty (Malice `[6,0,0]`→`[6,0,6]`→`[6,6,6]`).
  Strict comparison flagged 106 rank conflicts, almost all ordinary talents.
  `RANK_FINGERPRINT_FIELDS` (school + effect-structure compatibility) leaves **8 rows
  on 2 cards**, both `Necrosis` — whose school genuinely changes across ranks
  (0 → 32 Shadow → 1 Physical). That one is a real finding, still unexplained.

---

## Crawler automation (owner-supplied task)

**Registered:** `AscensionCrafter Daily Crawl`, created by the committed script
`tools/scheduling/register_daily_crawler.ps1`. Full documentation in `SCHEDULING.md`.

Settings as specified: `StartWhenAvailable` on, network required, 2-hour limit, no
wake, not elevated, **runs only when logged on** (owner's choice — no stored password).

**The trigger is at-logon, not a clock time.** The owner answered the "what time?"
question with *"when I turn on the computer"*, which a logon trigger expresses
directly — and it makes the missed-run requirement moot, since a PC that was off has
simply not logged on yet.

Because logging on twice a day is normal, the **once-per-day guard lives in
`tools/scheduling/run_crawler_scheduled.bat`**, not the trigger: it stamps
`data/derived/last_scheduled_crawl.txt` on **success only**, so a failed run retries at
the next logon instead of being suppressed for the day. That script also has **no
`pause`** — Task Scheduler has nobody to press a key, and a pause would hang the task
until the 2-hour limit killed it. `run_crawler.bat` keeps its pause and deliberately
ignores the guard; a manual run is an explicit act.

**Verified:** both guard paths (skip when stamped today, proceed when not); the task
registers with every required setting; `schtasks /run` launches it and it spawns the
crawler with the right working directory. Double-ingest safety was checked in the
code rather than by racing two runs — `scan_log["reports"]` skips already-captured
report ids and armory records are content-hashed and rewritten only on change.

🛑 **`catchup_crawler.bat` is deliberately not scheduled**, and there is a note saying
so next to the scheduling script and in `SCHEDULING.md`. Uncapped, multi-hour, against
someone else's public API.

---

## Open, carried into 1b

- 🚨 **The numeric-field DBC extractor** — still the highest-value unclaimed item
  (788 of 803 blocked hidden-formula spells, 98%). Cheaper now that `spell_dbc_raw`
  carries 17 more numeric columns. **Numeric fields only, never `description`.**
- **`Necrosis` changes damage school across its own ranks** (0 → Shadow → Physical),
  on a card that is in the current pool. Unexplained; recorded as a conflict.
- **25 ambiguous rank lines** need a rule or a hand resolution before anything reads a
  magnitude off them.
- **The 5 class conflicts** still need a proc test or a live tooltip each.
- **`stats_summary.sourcesByStat`** — carried over from 0b *and* 0a, still not
  inspected. Could settle the Path of Duality question from already-captured data.
- **`SEASON = 10` is hardcoded** in the crawler and cannot be derived from the API.
