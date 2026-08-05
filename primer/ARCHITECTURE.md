# AscensionCrafter — Architecture & Build Order (v2)

**Status:** supersedes `prompt_for_code_spell_infrastructure.md`,
`prompt_for_code_simulation_engine.md`, `prompt_for_code_scouted_data_pipeline.md`, and v1 of this
document. Where this and any older doc disagree, **this wins.**

**v2 changes:** uncertainty propagation replaces point-estimate output; the flat
patchwork/cleave/aoe scenario model is replaced by **content profile × target count × role**;
acquisition cost becomes a first-class build attribute; gear-scaling curves replace single-gear-state
evaluation; realm and season stamping added alongside patch stamping; a prediction ledger closes the
loop against the user's own play; the verification queue now emits executable test protocols; and
BisBeard is treated as an integration target rather than something to rebuild (§2.11).

**Audience:** Claude Code, and future-Claude picking this up cold.

---

## 1. The five layers

| # | Layer | Purpose |
|---|---|---|
| 1 | **Spell & Mechanics Database** | Everything the game does, with provenance, uncertainty, and relationships modelled as a graph |
| 2 | **Builds Repo** | What real players run and how it performs — crawled + live-captured. Also a *measurement instrument* feeding layer 1 |
| 3 | **Simulation** | Build → numbers, with honest uncertainty, across content types, target counts, roles, and gear levels |
| 4 | **Kit Box** *(renamed from "Lego Box", 2e D6 — owner decision 2026-08-05)* | Reusable, measured, evidence-backed build components that slot together. **A `kit` is a coupling-based cluster of cards; a `chassis` is the shared base a kit slots into.** Older docs say "lego" — same concept, annotate-don't-rewrite applies |
| 5 | **Theorycrafter** | Principles + tools + judgment → a designed build and a player-facing guide |

Layers 1–2 are data, 3 is computation, 4–5 are synthesis. Data quality gates everything — a wrong
coefficient in layer 1 silently corrupts every sim, lego, and guide. That's why layer 1 alone gets a
verification regime.

---

## 2. Non-negotiable principles

Schema- or code-enforced wherever possible, not discipline-enforced. The project's prose standards
already say most of this; the point of the restructure is to make violations **structurally
impossible**.

### 2.1 No value without provenance
Every mechanic value carries, `NOT NULL`: `source_tier`, `evidence_ref`, `verified_at_patch`,
`realm`, `season`, `confidence`. A number with no source cannot be inserted. Fabricating precision
becomes a constraint violation, not a lapse in judgment.

### 2.2 Source hierarchy

| Tier | Source | Notes |
|---|---|---|
| 1 | Live in-game tooltip / our own controlled parse | Ground truth — **but a tooltip is a measurement of the character, not the spell.** In-game values are haste/modifier-adjusted (Holy Supernova: 2.00s base → 1.61s displayed ≈ 24% haste). Always capture the character's stats alongside, or the number can't be interpreted later |
| 2 | Pooled combat-log measurement across many characters | Statistically strong for crit tables, hit checks, proc rates. Weak for coefficients |
| 3 | `db.ascension.gg` server-rendered spell page | Plain-HTTP fetchable, no browser needed — **but robots disallows automated access.** Targeted manual lookups only, not bulk crawling |
| 4 | Client DBC numeric fields (`EffectBasePoints`+1) | Never the `description` string — the Titanic Mutilate trap (stale "115%" vs actual 70%) |
| 5 | Changelog entries | Authoritative for *changes* and *new card existence*; often imprecise about magnitudes |
| 6 | `spell-export.json` tooltip text | Authoritative for existence, target lists, verbatim amplifier detection. Weakest for magnitudes |
| 7 | Scouted per-rank tooltip captures | Validates standard `$mN`/`$MN` fields only. **Proven blind to custom scripted terms** — silence is never confirmation |

### 2.3 Conflicts are surfaced, never auto-resolved
Two sources disagreeing → record **both**, `confidence='conflict'`, enqueue for verification. The
auto-debugger may fix *mechanical* problems (broken refs, stale derived columns, orphans,
recomputable values). It may **never** pick a winner between disagreeing sources — that's precisely
how confidently wrong data is created.

### 2.4 Uncertainty propagates; the sim never emits a bare point estimate
Every mechanic value carries an uncertainty range. The sim returns a **distribution reflecting input
confidence**, separate from combat RNG variance. Two payoffs:

- `4200 DPS ±80` and `4200 DPS ±900` are different situations. The second is a build you don't yet
  understand, and the output should say so.
- **Verification priority becomes computed, not guessed.** Variance-based sensitivity analysis —
  "which unverified value most widens the DPS range" — *is* the queue. That's a better answer to
  "what should I test tonight" than any hand-assigned importance score.

⚠ The default confidence→range mapping (Phase 1 Task 4) is itself a heuristic, not a measurement. It
must be labelled as such everywhere it surfaces.

### 2.5 Everything is stamped: patch, realm, season
The realm patches **daily**, realms diverge in balance, and seasons reset the card economy.

- `patches` is a first-class entity; facts decay against it
- **`realm`** — Darkmoon and Dawnrise receive different changes; an undifferentiated fact is a wrong fact
- **`season`** — S9 data may not describe S10
- Parses cannot be pooled across a patch that changed the measured ability
- Sim cache keys include all three
- The patch ingester auto-enqueues re-verification for anything a patch touched

### 2.6 Retractions and predictions are data
`retractions` (claim, why believed, what falsified it, superseding evidence, date, patch) and
`predictions`/`prediction_outcomes` (Phase 2 Task 9). Storing epistemics as prose means a fresh
session can re-derive a dead conclusion.

### 2.7 Server-ready from day one — four cheap decisions
Eventual goal is a hosted multi-user app with an interactive builder. Not building it now, but these
cost ~nothing today and are painful migrations later:

1. **Pure logic layer.** `core/` contains no `print()`, no `argparse`, no hardcoded paths, and takes
   a connection as a parameter. CLIs are thin wrappers. A web API must call the identical function.
2. **Postgres-portable SQL.** Plain types, explicit FKs, no SQLite-only features without reason.
3. **`user_id` on all user-scoped tables from day one**, with one user. Owned cards, personal
   builds, guarantee allocations, personal test results. Shared canonical data has no `user_id`.
4. **A named service layer** (`api/`) a FastAPI app wraps 1:1.

### 2.8 Role and content are first-class, not DPS-with-exceptions
The project owner plays DPS; others will tank, heal, and play solo. Building DPS-only and
generalising later means touching the engine.

- **Role** ∈ `dps` / `tank` / `healer` / `hybrid` — determines the primary metric
- **Metric** is pluggable: damage, healing, damage taken, effective HP, survival time, throughput per mana
- **Content profile** is an axis independent of target count (§2.9)

### 2.9 Scenario = content profile × target count × role
This replaces the flat patchwork/cleave/aoe triple. Solo play at 3 targets and a mythic dungeon at 3
targets are different problems: raid buffs, self-sustain requirements, fight length, and incoming
damage all differ.

```python
@dataclass
class ContentProfile:
    content_type: str        # 'raid','world_boss','dungeon_normal','dungeon_mythic','solo','pvp'
    difficulty: str | None
    target: TargetProfile    # level, armor, resistances, avoidance, count
    fight_duration: float
    raid_buffs_available: bool
    self_sustain_required: bool     # solo: you are your own healer
    incoming_damage_dps: float      # 0 for a pure raid DPS slot; large for solo/tank
    movement_pct: float             # forced downtime / uptime loss
```

Named presets ship (`raid_boss_st`, `raid_boss_cleave`, `mythic_trash_aoe`, `solo_grind`,
`world_boss`, `dungeon_normal_aoe`, …) and **are derived from real crawled encounter data wherever
possible**, not invented. `pvp` is reserved in the enum but out of scope for now.

**Consequence:** build evaluation is multi-objective. A solo build trading 8% DPS for self-sustain is
*better* in `solo_grind` and *worse* in `raid_boss_st`. The tooling must be able to say that rather
than declaring one build "better."

### 2.10 Builds are evaluated as curves, not points
Primer warns that flat-value abilities dominate in greens and decay with gearing, and that verdicts
must be re-derived when gear changes. Evaluating one gear state re-creates that mistake.

Every build is simmed at **three gear tiers** (fresh / mid / BiS) with **tiers derived per server
phase from the builds repo**, not hardcoded — what "BiS" means moves as content unlocks. Report the
slope. "Great now, dead later" gets caught automatically.

### 2.11 Integrate, don't duplicate
Where a maintained community tool already solves a problem well, integrate with it rather than
rebuilding it. The concrete case: **BisBeard (`s10.bisbeard.com`)** already does stat-weight-driven
BiS optimization for Ascension S10 with phase- and content-filtered gear, plus talent-driven
character-sheet auditing.

The division that follows is clean, and it's the reason stat weights were worth deriving at all:

| Capability | Owner |
|---|---|
| Item database, phase tagging, content-filtered BiS | **BisBeard** |
| **Deriving the stat weights** — requires a simulator | **This stack.** Nothing else has one |
| Simulation, uncertainty, rotation modelling | This stack |
| Relationship graph, lego discovery, mechanics inference | This stack |
| Guide generation | This stack |

We produce what nobody else can and hand off what's already solved. This also shapes the eventual UI:
complement BisBeard's planning-and-gear strengths, don't rebuild them. Where an integration proves
genuinely two-way useful, talking to the tool's author beats reverse-engineering it.

### 2.12 Derived vs. source
Source data is committed plain text/JSON; derived databases are gitignored and rebuilt. A chat
session can only see committed files via `raw.githubusercontent.com` — anything existing only as a
local `.db` is invisible to future sessions.

---

## 3. Build order

Two deviations from layer numbering, both deliberate:

- **Crawling starts in Phase 0.** Parse data accrues with wall-clock time; every day not running is
  unrecoverable.
- **The addon lands in Phase 3**, not early. Highest effort, lowest certainty (blocked on
  `ReloadUI()` availability and combat-log naming), and the crawler covers most of its value.

| Phase | Layers | Deliverable | Gate |
|---|---|---|---|
| **0 — Recon & Capture** | 1, 2 | Every assumption verified; crawler + changelog fetcher running daily | All recon questions have a verdict, none left "probably" |
| **1 — Spell Database** | 1 | Schema with provenance + uncertainty, all sources ingested, patch ingester, relationship graph, auto-debugger, test-protocol generator | Auto-debugger clean or consciously triaged |
| **2 — Simulation** | 3 | Combat engine, three sim tiers, uncertainty propagation, stat weights, gear curves, calibration, prediction ledger | Reproduces ≥3 real parses within stated tolerance |
| **3 — Builds Repo** | 2 | Normalised corpus, pooled mechanics inference, gear DB, addon + log path | Inference proposing verified-quality candidates |
| **4 — Legos & Theorycrafter** | 4, 5 | Component discovery, acquisition model, build brief, guide generator | — |

Phase 1 is the long one. Phases 2 and 3 partially overlap once Phase 1's schema is stable.

---

## 4. Repo layout

✅ **Realised 2026-08-04 in Phase 1 T1 — this is the actual layout, no longer a target.** `index/`
is gone. Directories not yet needed (`core/sim/`, `core/legos/`, `core/theory/`, `core/builds/`,
`ingest/ascension_db/`) are created by the phase that first needs them rather than sitting empty.

```
config.py        ← the ONE place a filesystem layout is written down. core/ may NOT import it
primer/          Ascension_Context_Primer.md, INDEX_GUIDE.md, ARCHITECTURE.md, RECON_FINDINGS.md,
                 START_HERE_FOR_CODE.md, PROGRESS.md, PHASE_*.md, Session_*.md handoffs
core/            ← pure logic. No I/O side effects, no CLI, no hardcoded paths
  db/            schema, migrations, connection management
  spells/        text extraction, ranks, fingerprint, crosswalk, class resolution
                 (+ mechanics, profile, graph as Phase 1 adds them)
  changelog/     patch-entry parsing and classification
  builds/        build spec, stats, repo queries, inference, gear
  sim/           combat_engine, fast/medium/slow, uncertainty, weights, calibration
  kits/          discovery, validation, composition   (was `legos/` — renamed 2e D6, dir not yet created)
  theory/        principles, brief, acquisition, guide
api/             ← service layer; thin functions a web API wraps 1:1
cli/             ← thin CLI wrappers. rebuild.py runs the whole ingest chain
ingest/          dbc/  ascension_db/  changelog/  logs_gg/  addon/  export/
tools/
  scrapers/      acquisition runners (crawler, changelog fetcher, scouting)
  scheduling/    Task Scheduler registration — see SCHEDULING.md
  audit/         auto-debugger + test protocol generator + check_core_purity.py
  log_parser/    WoWCombatLog.txt parsing
addons/          in-game Lua addons
data/
  source/        committed raw captures — source of truth. export/ dbc/ scouted/ changelog/ crawl/
  derived/       gitignored .db files and reports — always rebuildable
builds/          my-builds/  wip/  shared/
```

**§2.7 rule 1 is enforced, not just documented.** `tools/audit/check_core_purity.py` walks the AST of
every file in `core/` and fails on `print()`, `argparse`, `sys.argv`, a self-opened connection, or an
import of `config`/`cli`/`ingest`/`tools`/`api`. One named exemption:
`core/db/connection.py`, whose job is opening connections and which still takes the path as a
parameter. Run it after touching `core/`.

---

## 5. Where the old prompts went

| Old | New home |
|---|---|
| Infra T0 (DBC re-run) | Phase 0 T4 |
| Infra T1 (crosswalk) | Phase 0 T5 (verify) + Phase 1 T3 (build) |
| Infra T2 (`spell_mechanics`) | Phase 1 T4 — expanded: combat table, rank keying, uncertainty, realm/season |
| Infra T3 (`spell_profile()`) | Phase 1 T7 |
| Infra T4 (fact links) | Phase 1 T6 |
| Infra T5 (`audit_gaps.py`) | Phase 1 T8 — promoted to auto-debugger + test generator |
| Infra T6 (Datasette) | Phase 1 T9 |
| Sim T1 (AoE columns) | Phase 1 T4 |
| Sim T2–7 | Phase 2, restructured around a ported combat engine |
| Pipeline T1 (endpoints) | Phase 0 T2 |
| Pipeline T2–3 (provenance, scraper) | Phase 0 T6 (MVP) + Phase 3 T1/T8 |
| Pipeline T4 (addon) | Phase 3 T5 |
| Pipeline T5 (log parser) | Phase 3 T6 |
| Pipeline T6 (`find_builds()`) | Phase 3 T3 |
| Pipeline T7–8 (calibration, hook) | Phase 2 T8 + Phase 3 T7 |

**New, in no old prompt:** changelog/patch ingester, relationship graph, pooled statistical
inference, verification queue with executable test protocols, uncertainty propagation, stat-weight
derivation, gear optimizer, gear-scaling curves, acquisition-cost model, volatility scoring,
prediction ledger, lego box, guide generator, role/content modelling.

---

## 6. Standing rules for execution

- **Read `PHASE_0` in full before writing any schema.** Later phases assume answers Phase 0 produces.
- **Stop and ask rather than guess.** 🛑 marks stop-points. This project has been burned repeatedly
  (274121 vs 274132; Titanic Mutilate 115% vs 70%; "db.ascension.gg needs JS", disproven in Phase 0).
- **Amend the doc in the same session** when reality differs from it, noting what changed and why.
  Drift between these docs and reality is the most expensive failure mode here.
- **Never auto-design a whole build end-to-end.** The tools narrow and quantify; a human stays in the
  composition loop. A tool that hides the judgment behind "here's your build" makes the stack less
  trustworthy, not more.
