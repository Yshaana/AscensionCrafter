# PHASE 1 — The Spell & Mechanics Database (Layer 1) — v2

**Read `ARCHITECTURE.md` and `primer/RECON_FINDINGS.md` first. Phase 0 Task 5 has its verdict.**

---

## ✅ Progress — amended 2026-08-04 after session `1a`

| Task | Status |
|---|---|
| **T1** repo restructure + core/api/cli split | ✅ **done** (`1a`) |
| **T2** patch, realm, season tracking | ✅ **done** (`1a`) |
| **T3** the ID crosswalk | ✅ **done** (`1a`) |
| **1x** numeric-field DBC extractor | ✅ **done** (`1x`) |
| **T4** `spell_mechanics` | ⬜ session `1b`, next |
| **T5** relationship graph | ⬜ session `1b` |
| T6–T10 | ⬜ session `1c` |

**🆕 A task this doc never named was inserted and has now run: session `1x`, the numeric-field DBC
extractor**, before T4. It resolved **794 of the 887** blocked hidden-formula spells from
`EffectBasePoints`/`EffectDieSides`/`EffectRealPointsPerLevel` into the new `spell_effect_values`
table (the remaining 93 carry no magnitude anywhere — debuff/immunity markers). 🛑 **Numeric fields
only — never the `description` string** (the Titanic Mutilate trap).

⚠ **It also corrected the premise it was given.** Phase 0's *"311 carry a non-zero
`EffectBonusCoefficient` (SP/AP scaling)"* counted right and read the field wrong: it is stock
`EffectBonusMultiplier`, default 1.0, and **270 of the 343** blocked spells with any coefficient
carry only 1.0. The coefficient win was ≤73 spells, not 311 — the **flat** win was the real one all
along. Full detail in `Session_2026-08-04_1x_numeric_extractor.md`; consequences for T4 are folded
into the task text below.

### What `1a` built that T4 and T5 must reuse rather than re-derive

- **`core/spells/ranks.py :: rank_for_level()`** — T4's third resolver rule ("never serve a
  lower-rank value for a higher-rank query") is this function. Call it.
- **`core/spells/fingerprint.py`** — T4's fourth rule (🛑 fingerprint before relating two IDs) is
  **already implemented**, and it needs **two field sets**; see the amendment in T4 below.
- **`core/spells/crosswalk.py`** — `resolve_entry_id()` is the sanctioned `entry_id` → spell path.
- **`core/db/schema.py`, `core/db/connection.py`** — DDL and connections. `core/` purity is enforced
  by `tools/audit/check_core_purity.py`; **`resolve_spell_mechanics()` goes in
  `core/spells/mechanics.py` and takes a connection as a parameter.**
- **`py cli/rebuild.py`** — add new ingesters to its `CHAIN`, in dependency order.

### Amendments to the task text below

- **T3 — two sub-tasks were deliberately NOT built**, and should not be added later in the belief
  they were forgotten: a separate **`wotlk_rank`** ID space (superseded — `dbc_spell_rank` is the one
  home for rank lines; duplicating 42,606 rows creates a second home for the same fact), and the
  **`id_proximity` ±1–3 resolver** (the contiguous-rank rule was *retracted* in Phase 0 — 4,791
  non-contiguous lines vs 1,908 — so adding it back at `inferred` confidence would reintroduce a
  disproven heuristic, which is worse than not answering).
- **T3 — class resolution landed at tier `confirmed_skill_line`**, not `confirmed_wotlk_id_identity`:
  the mechanism turned out to be Ascension's *renamed skill lines*, not WotLK ID identity. Coverage
  394 → 1,794 of 3,061 (58.6%), against the doc's "potentially ~1,200+" estimate. The name-match
  guardrail passed with **0** mismatches.
- **T4's "does `spell_scaling` need rank keying?" no longer needs an in-game tooltip.** The doc says
  to settle it by reading one ability at two ranks in-game. `dbc_spell_rank` now gives confirmed
  same-line rank pairs, so it can be tested across **every** multi-rank line at once, offline —
  scheduled into `1x`.
- **T4's primary key**: measured, not assumed — **0** CA cards reuse a spell_id across rank slots and
  **0** in-pool spell_ids are shared across cards, so `spell_id` already identifies a card-rank
  uniquely in the playable pool. Key as specified anyway; just know `rank` is a label there.

The heart of the project. Everything downstream inherits its correctness. The goal is not "a database
of spells" — it's **a database that cannot quietly hold a wrong number.**

Four properties make that true:

1. **Provenance is mandatory and enforced** — no value without source, evidence, patch/realm/season stamp, confidence
2. **Uncertainty is stored, not implied** — every value has a range, and it propagates into the sim
3. **Relationships are first-class** — a graph, so "how do these interact" is one traversal
4. **The database audits itself** — and emits executable test protocols for what's still unknown

---

## Task 1 — Repo restructure and the core/api/cli split

Move to `00_ARCHITECTURE.md` §4. Mechanical, but do it **first** — retrofitting the pure-logic
boundary after modules exist is far more painful.

The rule that matters: **`core/` imports nothing from `cli/`, contains no `print()`, no `argparse`,
no hardcoded paths, and takes a connection as a parameter.** Existing `index/*.py` scripts split
along that line as they move. Keep the rebuild chain working throughout — a restructure that breaks
the pipeline for three sessions is worse than one that takes an extra day.

---

## Task 2 — Patch, realm, and season tracking

Daily patching plus divergent realms plus seasonal resets means these are prerequisites for every
other table, not features.

```sql
CREATE TABLE seasons (
  season_id  INTEGER PRIMARY KEY,
  label      TEXT NOT NULL,      -- 'S10'
  realm      TEXT NOT NULL,
  started_at TEXT, ended_at TEXT
);

CREATE TABLE server_phases (
  phase_id   INTEGER PRIMARY KEY,
  season_id  INTEGER NOT NULL REFERENCES seasons(season_id),
  phase_number INTEGER NOT NULL,
  label      TEXT,               -- content tier unlocked
  started_at TEXT, ended_at TEXT
);

CREATE TABLE patches (
  patch_id    INTEGER PRIMARY KEY,
  realm       TEXT NOT NULL,
  season_id   INTEGER REFERENCES seasons(season_id),
  patch_date  TEXT NOT NULL,     -- the changelog's "Changes made on" date
  fetched_at  TEXT NOT NULL,
  entry_count INTEGER
);

CREATE TABLE patch_entries (
  entry_id          INTEGER PRIMARY KEY,
  patch_id          INTEGER NOT NULL REFERENCES patches(patch_id),
  realms            TEXT,      -- parsed from [Darkmoon][Dawnrise] tags
  status            TEXT,      -- 'live','pending_restart','announced_future'
  status_note       TEXT,      -- 'Going Live Monday, 3 August'
  category          TEXT,
  change_type       TEXT,      -- 'New','Change'
  change_direction  TEXT,      -- 'buff','nerf','fix','neutral','new_card' — for volatility scoring
  raw_text          TEXT NOT NULL,
  first_seen_at     TEXT NOT NULL,
  status_changed_at TEXT
);

CREATE TABLE patch_entry_spells (
  entry_id     INTEGER NOT NULL REFERENCES patch_entries(entry_id),
  spell_id     INTEGER,
  matched_name TEXT NOT NULL,
  match_method TEXT NOT NULL,   -- 'bracketed','prose_name_match','manual'
  confidence   TEXT NOT NULL
);
```

**`server_phases` exists for §2.10** — gear tiers are derived per phase, so a phase timeline is
required. **Seed with known state (user-confirmed 2026-08-04):**

| Season | Phase | Label | Dates |
|---|---|---|---|
| S10 | 1 | Zul'Gurub | → 2026-08-08 |
| S10 | 2 | (label TBC) | 2026-08-08 → |

Backfill earlier phases and forward-fill later ones from changelog content-unlock entries (Phase 0
T3), or manually if that fails.

**Phase transitions invalidate more than a patch does.** A patch changes some abilities; a phase
change shifts the entire gear distribution, which moves stat weights, which moves BiS, which can move
build rankings — without a single ability having changed. `audit_gaps.py` (Task 8) should treat a
phase boundary as invalidating every `gear_tier`-keyed sim result and every stat weight derived under
the prior phase, and say so loudly rather than letting them quietly age. **Phase 2 on 2026-08-08 is
the first live test of this.**

**`status` matters** because a `[Pending Restart]` entry is not yet in effect. Treating it as live
invalidates facts prematurely; ignoring it misses the change when it lands. `status_changed_at`
across daily snapshots captures the transition.

**`change_direction`** feeds volatility scoring (Task 10). Classify conservatively —
increase/reduce/"fixed a bug" language is usually unambiguous; flag the rest as `neutral` rather than
guessing.

**Ingester** (`ingest/changelog/`): inserts patches and entries, resolves names, and — the
operational payoff — **enqueues every affected mechanic into the verification queue** (Task 8).

**`detect_new_cards()`:** any bracketed name in a `New` entry not resolving against the catalog is a
newly-added card, discovered before it appears in any export. Report these; they're the leading edge
of the game's content.

---

## Task 3 — The ID crosswalk

Per Phase 0 Task 5. General infrastructure, not a one-off fix.

```sql
CREATE TABLE spell_id_crosswalk (
  id              INTEGER PRIMARY KEY,
  external_source TEXT NOT NULL,   -- 'logs_gg.entry_id','db_ascension_gg','catalog_vs_live',
                                    -- 'dbc','changelog_name','official_builder'
  external_id     TEXT NOT NULL,   -- TEXT, not INTEGER — some sources key by name
  spell_id        INTEGER NOT NULL,
  rank            INTEGER,
  match_method    TEXT NOT NULL,   -- 'id_identity','name_exact','name+rank','id_proximity','manual'
  confidence      TEXT NOT NULL,
  evidence_ref    TEXT,
  notes           TEXT
);
```

Every external ID space plugs in as rows, never as new join logic. The known catalog-vs-live case
(274121 vs 274132) is just another row.

### The ID spaces (verified in-game 2026-08-04 — see Phase 0 Task 1f)

**Catalog IDs and in-game IDs are the same space.** `1459` (Arcane Intellect R1) and `136` (Mend Pet
R1) appear identically in `spell-export.json` and in live tooltips. There is **no** prefixed
"Wildcard variant" space — that hypothesis was tested and retracted.

Add these `external_source` values:

- **`wotlk_rank`** — Rank 1 ID ↔ other ranks. **Two regimes, resolve differently:** Ascension
  originals are contiguous (`rank1_id + rank − 1`, e.g. Holy Supernova 270182 → 270187 at R6);
  classic WotLK spells are scattered (Arcane Intellect 1459 → 10157 at R5) and need DBC rank chains.
  Never guess by proximity — establish which regime from the ID range first
- **`character_advancement`** — the `CharacterAdvancement ID` shown in in-game tooltips (~40000
  range: 40094 Arcane Intellect R1, 40017 Mend Pet R1). **Strong hypothesis: this is what scouted
  `entry_id` actually is** (Shadow Bolt's scouted `entry_id` was 40050, while its `spellId` is 686
  and its `cardId`s are 26542/12277/24322/26543). Confirm per Phase 0 Task 5
- **`card_id`** — `Cards.txt`'s `cardId`. **Many-to-one with `spellId`** — Arcane Intellect has four
  (26572, 12294 Normal; 26573, 24339 Golden). Any join must handle multiplicity rather than assuming
  one row

🛑 **If the CharacterAdvancement hypothesis confirms, a CA↔spellId mapping does not exist in any
local file** — it's not derivable from catalog ordinal position (tested: Mend Pet is catalog ability
#18 with CA 40017; Arcane Intellect is #108 with CA 40094 — the offset grows). Determine whether the
addon or client can dump one, and stop-and-ask before building around a substitute.

### Deterministic class resolution

If Phase 0 Task 4a extracted `SkillLineAbility.dbc`, add `seed_class_from_wotlk_id.py`:

- For every catalog entry with `id < 80000`, join to the DBC record
- **Require a name match** before accepting the class — an ID collision is possible and a mismatch is
  a finding worth logging
- Write `class_origin` at a new tier `confirmed_wotlk_id_identity`, ranked above
  `inferred_borrowed_modifiers` and below `confirmed_proc_test`
- Record spells resolving to no class or multiple classes as exactly that, not as a forced single
  value

Expected coverage jump: ~392 → potentially ~1,200+ of 3,061. Report actual numbers; if the real
figure is far below that, the name-match guardrail is telling you something and should be
investigated rather than loosened.

**Then retire string matching entirely.** Anywhere doing
`if 'winds of winter' in json.dumps(build).lower()` switches to a crosswalk join. String matching
produced the Tdoctor bug; leaving both paths running recreates it.

If Phase 0 confirmed the rank hypothesis, add an `id_proximity` resolver checking ±1–3 of an
unresolved ID against known names, writing at `confidence='inferred'`.

---

## Task 4 — `spell_mechanics`: the resolved truth table

The most important schema decision in the project. Read the whole task before writing DDL.

### Key: `(spell_id, rank, realm, season)`

- **`rank`** — ranks are the core economy: rolls land 1–5, partial ranks are assets, a 3/5 card is
  numerically different from a 5/5. Convention: **`rank = 0` means rank-independent / max rank**.
  Zero rather than NULL keeps the key simple and avoids NULL-comparison bugs.
- **`realm`, `season`** — §2.5. Trivial now, a migration later.

### Schema

```sql
CREATE TABLE spell_mechanics (
  spell_id INTEGER NOT NULL,
  rank     INTEGER NOT NULL DEFAULT 0,
  realm    TEXT    NOT NULL,
  season   TEXT    NOT NULL,

  -- Resource & timing
  resource_type          TEXT,     -- 'mana','rage','energy','runic','holypower','combopoints','none'
  resource_cost          REAL,
  resource_cost_pct_base INTEGER,
  cooldown_seconds       REAL,
  cooldown_category      TEXT,     -- shared-cooldown group (seals share one — confirm)
  gcd_type               TEXT,     -- 'normal','off_gcd','none'
  cast_time_seconds      REAL,
  is_channeled           INTEGER,
  is_next_swing          INTEGER,  -- On-Next-Hit replacement (Cleave/Heroic Strike pattern)
  charges                INTEGER,
  charge_recharge_seconds REAL,

  -- Output
  effect_type            TEXT,     -- 'damage','heal','absorb','mitigation','buff','utility'
  school                 TEXT,     -- incl. hybrids: Holystrike, Shadowflame, Froststrike...
  damage_formula_text    TEXT,
  damage_formula_terms_json TEXT,  -- [{"term":"SP","coefficient":0.0096,"cp_scaling":"quadratic"}]
  healing_formula_terms_json TEXT, -- §2.8 — healer support is first-class, not bolted on later
  absorb_formula_terms_json  TEXT,
  mitigation_pct         REAL,     -- tank support
  threat_modifier        REAL,
  weapon_damage_pct      REAL,
  normalized_weapon_speed REAL,

  -- Combat table
  crit_table             TEXT,     -- 'melee','spell','none'
  hit_table              TEXT,     -- 'melee','spell','none'
  rolls_hit_check        INTEGER,
  can_be_dodged          INTEGER,
  can_be_parried         INTEGER,
  can_be_blocked         INTEGER,
  can_glance             INTEGER,
  can_be_full_resisted   INTEGER,
  affected_by_armor      INTEGER,
  crit_damage_multiplier REAL,     -- 2.0 melee / 1.5 spell baseline; overridable
  always_crits           INTEGER,  -- e.g. "Exorcism is now guaranteed to critically strike"

  -- Proc behaviour
  proc_chance_pct        REAL,
  proc_ppm               REAL,
  proc_icd_seconds       REAL,     -- 0 = confirmed no ICD; NULL = unknown
  proc_trigger_events    TEXT,
  can_proc_from_off_gcd  INTEGER,  -- see the 2026-08-03 change restricting this

  -- AoE
  max_targets            INTEGER,  -- NULL = uncapped
  damage_split_behavior  TEXT,     -- 'none','split_evenly','falloff','fixed_cleave_n'
  cleave_fixed_n         INTEGER,
  aoe_radius             REAL,
  falloff_pct_per_target REAL,
  falloff_floor_pct      REAL,

  -- Periodic
  is_periodic            INTEGER,
  tick_interval_seconds  REAL,
  duration_seconds       REAL,
  ticks_can_crit         INTEGER,
  scales_with_haste      INTEGER,
  is_ground_effect       INTEGER,

  -- Provenance & uncertainty (§2.1, §2.4)
  source_tier_json       TEXT NOT NULL,  -- per-field: which tier supplied each value
  evidence_ref_json      TEXT NOT NULL,  -- per-field: pointer to the actual evidence
  uncertainty_json       TEXT NOT NULL,  -- per-field: {"low":..,"high":..,"basis":".."}
  conflicts_json         TEXT,           -- non-null when sources disagreed; ALL values seen
  confidence             TEXT NOT NULL,
  verified_at_patch      INTEGER NOT NULL REFERENCES patches(patch_id),
  last_resolved_at       TEXT NOT NULL,

  PRIMARY KEY (spell_id, rank, realm, season)
);
```

### Why the combat-table block exists

The old design had resource/cooldown/damage/AoE and stopped. That's a **first-order error**:

- Without `crit_table`, the sim can't know whether to apply melee or spell crit. Where those diverge,
  every number is wrong by a multiplier.
- Primer §5 carries an explicit ⚠ that crit table and hit table are **independent rolls**, and that
  conflating them once inflated a hit weight from ~0.3 to 2.0.
- Primer §5's buckets must be modelled separately: periodic effects can't miss; procs riding a landed
  attack don't re-roll; melee abilities use melee hit regardless of crit table.
- Primer §1 (v17): Holy has no full-resist roll but **does** take partial resistance.
- `is_next_swing` + `can_proc_from_off_gcd` exist because the 2026-08-03 patch specifically changed
  proc eligibility for off-GCD On-Next-Hit abilities.

`spells.crit_table`/`hit_table`/`rolls_hit_check`/`proc_icd_seconds` already exist, mostly unseeded.
**Migrate their values here and drop them from `spells`.** One home per fact.

### Uncertainty defaults

`uncertainty_json` is populated per field. Default mapping when nothing better exists:

| Confidence | Default range | Basis |
|---|---|---|
| `confirmed` | ±0% | Measured directly |
| `inferred` | ±10% | Derived from a rule, not observed |
| `conflict` | spans the conflicting values | The actual disagreement |
| `unverified` | ±25% | Placeholder — sim must warn on any build depending on one |

🛑 **These percentages are a heuristic, not a measurement.** Store `basis` per field so a genuinely
measured uncertainty (e.g. a confidence interval from pooled parses in Phase 3) overrides the default
and is visibly distinguishable from it. Anywhere an uncertainty surfaces to the user, its basis
surfaces with it.

### Resolver

`core/spells/mechanics.py :: resolve_spell_mechanics(conn, spell_id, rank, realm, season)`, merging
by §2.2 priority per field. Two rules baked into the function, not documented as convention:

- **Never read a DBC `description` string for a magnitude.** Numeric fields only — the Titanic
  Mutilate trap written into code.
- **Two sources disagreeing → both into `conflicts_json`, `confidence='conflict'`, enqueue.** Never
  silently pick the higher tier (§2.3).

🚨 **Third rule, from in-game verification (Phase 0 Task 1f): never serve a lower-rank value for a
higher-rank query.** `spell-export.json` stores Rank 1 for most entries; the owner plays max rank.
Arcane Intellect is +2 Intellect / +2 spell power at Rank 1 and **+31 / +27 at Rank 5** — a ~15× gap.
The resolver must **raise or return an explicit gap**, never fall back to a lower rank. Same rule for
classic-range IDs and their retail equivalents: Ascension edits spells in place (its Arcane Intellect
grants spell power; retail's does not, under the same ID `1459`), so **class inherits from a WotLK ID,
mechanics never do.**

🛑 **Fourth rule — fingerprint before relating two IDs (Phase 0 Task 1d).** Never treat two spell IDs
as the same ability, a variant, or two ranks on the strength of a name match. Compare radius,
cooldown, cast type, resource cost, effect structure, and school first. Two spells named "Holy
Supernova" (`270182` and `81193`) differ in radius, cooldown, and cast type and are unrelated —
assuming otherwise produced a retracted conclusion and a nearly-adopted schema change in a single
session. Implement the fingerprint check inside the crosswalk resolver.

> ✅ **Done in `1a` — `core/spells/fingerprint.py`. But it needed TWO field sets, and this doc's
> single-set framing is what made the first attempt wrong.** The strict set above answers *"are these
> the same ability?"*. It is the **wrong test** for *"are these two ranks of one ability?"*, because
> rank legitimately changes radius, cooldown and resource type, and higher ranks **fill effect slots
> the lower rank leaves empty** (Malice `[6,0,0]`→`[6,0,6]`→`[6,6,6]`). Applied to rank chains, the
> strict set flagged **106 conflicts, almost all ordinary talents**. `RANK_FINGERPRINT_FIELDS`
> (school + effect-structure compatibility) leaves **8 rows on 2 cards**, both `Necrosis` — whose
> damage school genuinely changes across its own ranks. Use the right set for the question being
> asked.

### Does `spell_scaling` need rank keying? — ✅ **YES. Settled in session `1x`.**

> **The history matters, because this has now been answered wrongly twice.** An early draft
> asserted coefficients scale with rank — **withdrawn**, because the evidence compared two
> different abilities sharing a name (Phase 0 Task 1d). Phase 0 then answered "probably not"
> from a **single** line and concluded *"reading a coefficient off the catalog's Rank-1 entry
> is probably safe"* — **also retracted**, in `1x`: one line is not a law, and that line
> happened to be one of the constant ones.

Measured across all **1,580** multi-rank lines with 2+ members in `spell_dbc_raw`:

| evidence | constant | varies | no data |
|---|---|---|---|
| numeric `EffectBonusCoefficient` (tier 4) | 696 | **169** | 715 |
| tooltip `$SP*`/`$AP*` literals (tier 6) | 132 | **34** | 1,414 |

The variation is retail's **low-rank penalty — ramps then plateaus** (110 of the 169), and the
catalog stores **Rank 1**, the deepest point of that penalty. Seven catalog entries are
measurably wrong today; worst are **Sun Down SP 0.4 → 1.3 (3.25×)** and **Grasp of Darkness
SP 0.5 → 1.4 (2.8×)**, and **Spirit Charge changes term type** (SP → AP). Seven is a **floor** —
547 more state no coefficient in either rank's text, so nothing can be compared for them.

**So: key `spell_scaling` as `(spell_id, term_type, rank, ...)`.** Owner decision 2026-08-04:
`1x` records and flags, **T4 performs the migration**, since this task rebuilds the table
anyway. Resolve with `core.spells.ranks.rank_for_level()`; the study is reusable in
`core/spells/rank_scaling.py`.

🛑 **Do not read the coefficient from `EffectBonusCoefficient`.** Session `1x` established it
is stock `EffectBonusMultiplier` — default 1.0, with **7,647 of 9,211** non-zero values exactly
1.0, and agreement with a spell's own stated `$SP*x`/`$AP*x` in **4 of 98** calibration cases.
Ascension keeps the coefficients it applies in **tooltip text**. The field is stored as
`spell_effect_values.bonus_multiplier` and must never be emitted as an SP or AP term.

Standing caveat, unchanged: **every coefficient currently in the index was extracted from a
Rank 1 catalog tooltip**, so those rows are lower bounds wherever the line ramps.

### ✅ Level scaling: `max_level` is populated, and T4 must apply it

`spell_effect_values` stores flats **unscaled**. The level-N value is:

```
flat + (min(level, max_level or level) - spell_level) * per_level
```

`max_level` was added to `spell_dbc_raw` in `1x` and the owner re-extracted the same day, so the
field is live. **354 catalog spells carry a per-level term** (342 of them cards he owns), and
**1,653 spells have a real cap, 196 of them among those 354** — so T4 cannot simply assume
uncapped scaling.

🛑 **`max_level = 0` means UNCAPPED, not "caps at zero".** 12,532 spells read 0. Getting this
backwards is not hypothetical — it is what produced this session's own retracted claim that Hammer
from the Heavens caps at level 40.

Worked example, `282987`: `base 2..25`, `per_level 2.4`, `spell_level 10`, `max_level 0` →
at level 60, `2 + (60-10)*2.4 = 122` to `25 + 120 = 145`. Verified against the live tooltip and
db.ascension.gg.

### 🆕 T4 consumes `spell_effect_values` (built in `1x`)

Flat, per-level and per-combo terms are already decoded from numeric fields for 2,981 catalog
spells — **794 of the 887 blocked hidden-formula spells included**. Keyed
`(spell_id, source_spell_id, effect_index)`, with `via` distinguishing a value read from the
card's own record from one read through a hidden sub-spell. `resolve_spell_mechanics()` should
read that table rather than re-deriving from `effect_json`.

Convention (validated against 7 independently-established magnitudes, re-checked every run):
`min = base_points + 1`, `max = base_points + die_sides`. `base_points = -1` with
`die_sides <= 1` is the **"no value" sentinel** and decodes to `None`, never `0.0`.

---

## Task 5 — The relationship graph

What makes the database answer *"how do these interact"* rather than just *"what is this."*

```sql
CREATE TABLE spell_relationships (
  id              INTEGER PRIMARY KEY,
  source_spell_id INTEGER NOT NULL,
  target_spell_id INTEGER,
  target_name     TEXT,          -- when the target doesn't resolve
  relation_type   TEXT NOT NULL,
  magnitude       REAL,
  magnitude_unit  TEXT,          -- 'pct','flat','seconds','stacks','charges'
  condition_json  TEXT,          -- gating: required talents, buffs, stacks, weapon type
  direction       TEXT NOT NULL, -- 'source_affects_target' | 'source_requires_target'
  source_tier     TEXT NOT NULL,
  evidence_ref    TEXT NOT NULL,
  confidence      TEXT NOT NULL,
  realm TEXT NOT NULL, season TEXT NOT NULL,
  verified_at_patch INTEGER NOT NULL REFERENCES patches(patch_id)
);
```

**Relation types** — enumerated, not free text:

`amplifies` · `amplifies_school` · `triggers` · `resets_cooldown` · `reduces_cooldown` · `consumes` ·
`grants_buff` · `grants_charges` · `enables` · `requires` · `replaces` · `borrows_modifiers` ·
`shares_exclusivity_bucket` · `shares_cooldown_category` · `converts_school` · `extends_duration` ·
`anti_synergy`

**`amplifies_school` is a distinct relation type for a reason.** A talent reading "increases Frost
damage by X%" boosts abilities it never names — it targets a *school*, not a spell. If that only
existed as a generic `amplifies` edge with a floating `target_name`, it would never connect to the
actual Frost abilities in a build, and any lego built around a school-scoped amplifier (a real,
common pattern — see Phase 4's Frost Mage + Frost Shaman example) would be invisible to graph
discovery. So:

- `amplifies_school` edges carry the school in `condition_json` (`{"school": "Frost"}`) and have a
  NULL `target_spell_id` — they don't point at one spell
- They **resolve against a build**: at graph-build time for a specific `BuildSpec`, an
  `amplifies_school` edge expands into concrete `amplifies` edges to every ability of that school the
  build actually runs. This makes part of the graph **build-dependent, not fully static** — a design
  point that ripples into `neighbourhood()` and `find_clusters()` needing an optional `build_spec`
  argument
- They enter at **lower confidence** and flagged for proc-testing. Primer §5: *named lists outrank
  generic wording until proc-tested.* A school-scoped amplifier is generic wording by definition —
  real, but a prediction until confirmed, exactly like the existing `school_generic` tier in
  `talent_amplifiers`

**The user's example maps to:**
```
B --amplifies--> A       condition: {requires_talent: X}
Y --resets_cooldown--> B
```

### 🆕 `triggers` has a second job, found in `1x`: it unlocks ~519 spells' magnitudes

`EffectTriggerSpell` is not just a relationship — it is an **attribution path for
numeric values**. Session `1x` resolved magnitudes for spells reachable from a card by
tooltip `hidden_refs`, but a card also reaches spells by *triggering* them, and those
were never attributed: **529 catalog → out-of-catalog trigger links across 519 distinct
targets**, every one of them a spell whose numeric fields are already extracted and
sitting unused in `spell_dbc_raw`.

The case that surfaced it is the owner's own biggest unknown. **Hammer from the
Heavens** (`282987`, 22.1% of his damage, `build_paladin-hammerdin.md` §12 item 2) has a
complete DBC record — and is reached only as *Hour of Judgement* (`282986`) → `282987`,
**two hops** from any card, via `EffectTriggerSpell` rather than a tooltip reference.

Two decisions this needs before it becomes a resolver input, which is exactly why `1x`
left it alone rather than half-building it:

- **multi-hop attribution semantics** — is a 2-hop triggered spell's magnitude "the
  card's damage"? For Hammer from the Heavens, yes. It will not always be
- **cycle handling** — trigger graphs contain loops; a naive walk does not terminate

Build the edges first, then decide attribution. Do not let a magnitude reach
`spell_mechanics` through an unbounded trigger walk.

**Migrate and retire.** `modifier_links`, `talent_amplifiers`, `borrows_from`, and
`exclusivity_buckets` become rows here. Exclusivity buckets are N-way clusters — represent as
`shares_exclusivity_bucket` edges among all members with the bucket slug in `condition_json`, and
keep `exclusivity_buckets` as a **view** so existing queries don't break.

### Cluster detection

`core/spells/graph.py` using **networkx** — no graph database; at a few thousand nodes this is
trivially in-memory and a graph DB adds an operational dependency for no gain.

- `neighbourhood(spell_id, depth=2, build_spec=None)` — everything within N hops, both directions.
  With a `build_spec`, `amplifies_school` edges expand to the build's actual same-school abilities
- `find_clusters(min_size=3, build_spec=None)` — densely-interconnected subgraphs. **Lego
  candidates** (Phase 4). School-scoped amplifiers only form clusters once resolved against a build,
  so a build context surfaces couplings the static graph can't
- `path_between(a, b)` — how two abilities connect, if at all
- `gating_requirements(cluster)` — union of all `condition_json` across a cluster's edges, i.e.
  **what you must own for this cluster to work.** This is what turns the graph into build advice

### Populating

1. Migrate existing tables
2. Parse tooltips conservatively — verbatim ability-name matches are high confidence and become
   `amplifies` edges; **school-scoped wording** ("increases Frost damage") becomes an
   `amplifies_school` edge, flagged for proc-testing. **Primer §5: named lists outrank generic
   wording until proc-tested** — so the two never enter at the same confidence
3. **Changelog mining** — new-card text is near-structured prose. *"Mongoose Bite and Counterattack
   increase the damage of your next Divine Storm by 20% per stack, up to 5 stacks"* is two
   `amplifies` edges with magnitude and stack condition. Rich source; extract conservatively, flag
   for review
4. **Co-occurrence from the builds repo** (Phase 3) suggests edges the text never states —
   candidates only, never auto-inserted

---

## Task 6 — Facts, retractions, open questions

```sql
ALTER TABLE confirmed_facts ADD COLUMN verified_at_patch INTEGER;
ALTER TABLE confirmed_facts ADD COLUMN superseded_by_patch INTEGER;
ALTER TABLE confirmed_facts ADD COLUMN evidence_ref TEXT;
ALTER TABLE confirmed_facts ADD COLUMN sample_size INTEGER;
ALTER TABLE confirmed_facts ADD COLUMN realm TEXT;
ALTER TABLE confirmed_facts ADD COLUMN season TEXT;

CREATE TABLE fact_spell_links (
  fact_topic TEXT NOT NULL, spell_id INTEGER NOT NULL,
  match_method TEXT NOT NULL, confidence TEXT NOT NULL
);

CREATE TABLE open_questions (
  id INTEGER PRIMARY KEY,
  question TEXT NOT NULL,
  blocks TEXT,                    -- what decision waits on this
  status TEXT NOT NULL,           -- 'open','in_progress','resolved','abandoned'
  resolved_by_fact_topic TEXT,
  variance_contribution REAL,     -- computed (Phase 2): how much DPS uncertainty this causes
  affected_spell_ids TEXT,
  opened_at TEXT NOT NULL, opened_at_patch INTEGER
);

CREATE TABLE retractions (
  id INTEGER PRIMARY KEY,
  claim TEXT NOT NULL, why_believed TEXT NOT NULL, what_falsified_it TEXT NOT NULL,
  superseding_fact_topic TEXT, retracted_at TEXT NOT NULL, retracted_at_patch INTEGER
);
```

**`variance_contribution` replaces the hand-assigned "blast radius" from v1.** Per §2.4, it's
computed by sensitivity analysis in Phase 2 — an unknown that barely moves any build's DPS range is
genuinely low priority, and an unknown that dominates it is genuinely urgent. Until Phase 2 exists,
leave NULL and fall back to a simple dependent-count.

**Backfill:** scan the ~90 `confirmed_facts` for explicit spell IDs (regex first — higher confidence)
and exact name matches (flagged `needs_review`, never auto-approved). Seed `open_questions` from the
primer's assumption register and build docs; `retractions` from the primer's retraction history plus
Phase 0's two disproven beliefs.

**Going forward**, every new fact carries its spell IDs at write time.

**The check justifying all of this:** flag any `open_questions` row whose text overlaps a
`confirmed_facts` row — *"you already answered this."* That would have caught the INDEX_GUIDE
contradiction where v7 documented the answer to a gap the same file still listed as open.

---

## Task 7 — `spell_profile()`

```python
# core/spells/profile.py
def spell_profile(conn, name_or_id, rank=None, realm=None, season=None,
                  depth=2, mode='full') -> dict:
    """Structured dict. No printing. CLI, Datasette, and the future web API all call this.
    mode='fast' skips graph traversal and usage joins — for loops (e.g. the sim resolving 15
    abilities)."""
```

| Section | Contents |
|---|---|
| **Identity** | id, name, ranks, type, school(s), class origin + confidence, path fit |
| **Ownership** | `owned_cards` (user-scoped — takes `user_id`), rarity, pool |
| **Mechanics** | resolved row per rank, **with uncertainty ranges and `conflicts_json` surfaced prominently, not buried** |
| **Relationships** | graph neighbourhood to `depth`, both directions, conditions rendered readably |
| **Clusters / legos** | which detected components this belongs to |
| **Facts** | linked `confirmed_facts`, full text |
| **Patch history** | every `patch_entry` touching this spell, newest first, with `change_direction` — *"has this been changed recently, and which way?"* becomes a first-class question |
| **Volatility** | nerf-risk score (Task 10) |
| **Real usage** | which crawled characters run it, at what rank, **with capture dates and patch stamps** so a stale snapshot is never treated as current |
| **Performance** | pooled hits/crits/damage-share/avoidance from the builds repo (Phase 3) |
| **Gaps** | unresolved template refs, NULL fields, unverified relationships, staleness age, open questions touching this spell |

---

## Task 8 — The auto-debugger and the test-protocol generator

`tools/audit/` — last step of every rebuild, and standalone on demand.

### May auto-fix (mechanical only)
Orphaned rows, broken FKs, stale derived columns, duplicate rows from re-ingestion, crosswalk entries
pointing at vanished spells (mark, don't delete), recomputing scores.

### Must NEVER auto-fix (§2.3)
A value conflict. Anything below `confirmed`. Anything touched by an unprocessed patch entry.

### Checks

| Check | Finds |
|---|---|
| **Conflict sweep** | every `confidence='conflict'` row |
| **Staleness sweep** | mechanics whose `verified_at_patch` predates a patch entry naming that spell — *the daily-patch check that matters most* |
| **Realm/season sweep** | facts applied across realms or seasons without evidence they hold in both |
| **Phase-boundary sweep** | stat weights, gear tiers, and sim results derived under a prior server phase. A phase change moves the gear distribution → moves weights → moves BiS, with no ability having changed. **Next boundary: 2026-08-08** |
| **Provenance sweep** | rows whose `evidence_ref` doesn't resolve to real evidence |
| **Coverage sweep** | ability/talent-tier spells with no mechanics, facts, or relationships |
| **Doc-vs-data sweep** | for every character named in `builds/*.md`, verify the doc's claims match their snapshot. **Split severity**: "build changed *after* the doc was written" = informational; "never matched any snapshot" = real bug. Without that split this fires constantly once daily crawling runs, becomes noise, and gets ignored — exactly how the original Tdoctor bug survived |
| **Answered-question sweep** | open questions overlapping a confirmed fact |
| **Contradiction sweep** | two facts asserting incompatible things about one spell |
| **String-match sweep** | code paths still string-matching instead of joining the crosswalk |
| **Orphan-name sweep** | changelog names, DBC entries, crawled `entry_id`s that never resolved |

### Output

`data/derived/audit_report.md` plus a one-line stdout summary. **Issues ranked by
`variance_contribution`**, not count — one unverified coefficient that widens your main build's DPS
range by 400 outranks 200 unresolved utility spells nobody uses.

### Test-protocol generator

The queue's real output isn't "these values are unverified." It's *what to actually do tonight at a
target dummy.*

```python
# tools/audit/protocols.py
def generate_test_protocol(open_question_id) -> dict:
    """Returns: ability, method, exact setup, minimum sample size, what to record,
    and the expected result under each competing hypothesis."""
```

**Encode the primer's test-design constraints as hard rules:**

- **⚠ Never propose rerolling a card to test it.** Multi-rank cards may return at lower rank and
  there's no respec. The generator must *refuse* to emit a card-destroying protocol, not merely
  deprioritise it.
- Prefer, in order: character-sheet breakdown tooltips → gear swaps → consumables → buff-state
  filtering → two-target comparisons → bar toggles.
- **Compute minimum sample size properly** from the discriminating power needed. Primer §5:
  crit-rate questions need thousands of hits, multiplier questions ~100; if candidate values are
  within ~3 points, the correct output is **"insufficient discriminator, find another test"** — not
  a number.
- **State target level.** Miss rates differ ~6% (+2) vs ~17% (+3); a protocol that doesn't specify
  content produces uninterpretable data.
- **Name the expected outcome under each hypothesis** before the test is run. A test whose outcomes
  don't distinguish the hypotheses isn't a test.

### Quick vs. deep
Fast integrity sweep every rebuild; deep sweep (full graph consistency, cross-source re-resolution,
statistical outlier detection on coefficients) weekly or on demand.

---

## Task 9 — Browsing and search

`datasette data/derived/*.db` with canned queries. Narrow scope: browsing convenience, explicitly
**not** the builder app.

`core/spells/search.py :: search_spells(conn, **filters)` — general filtered search (school, scaling
term, coefficient range, ownership, rarity, relation to another spell, role fit, patch-touched-since,
volatility). This is the "easily searchable" requirement, and it must be a real function, not ad-hoc
SQL in a notebook.

---

## Task 10 — Volatility scoring (report-only)

```python
# core/spells/volatility.py
def volatility_score(spell_id, lookback_days=365) -> dict:
    """From patch_entry_spells + change_direction: how often has this been touched,
    which direction, how recently, and does it get nerfed after becoming popular?"""
```

An ability with four nerfs in two seasons is a poor place to spend a Golden guarantee slot. Nobody
else can compute this — it needs the historical changelog corpus.

🛑 **Report-only. This never enters optimizer scoring or stat weights.** It appears as a flag in
`spell_profile()` and a note in the final guide, nothing more. Per the user: worth knowing, shouldn't
weigh heavily.

---

## Execution order

```
✅ 1 (restructure) → ✅ 2 (patches/realms/seasons) → ✅ 3 (crosswalk)        [session 1a, done]
  → ✅ 1x (numeric-field DBC extractor + rank-vs-coefficient SETTLED)      [session 1x, done]
    → 4 (mechanics)                                                        [session 1b, NEXT]
      → 5 (relationships) ─┐                                               [session 1b]
      → 6 (facts)         ─┤ independent of each other                     [session 1c]
      → 10 (volatility)   ─┤
        → 7 (spell_profile) ←┘
          → 8 (auto-debugger + protocols) → 9 (browsing)
```

**`1x` is not in the numbered task list above** — Phase 0 discovered it after this doc was written.
It sits between 3 and 4 because T4 is the *resolved* truth table and 803 spells currently have no
coefficient at all. See the progress block at the top of this file.

## Exit criteria

- Auto-debugger clean, or every remaining issue consciously triaged
- `spell_profile()` complete for every ability in the user's current builds
- Zero mechanics rows without provenance **and** uncertainty
- Every conflict resolved or queued — none silently resolved
- The graph reproduces the four known exclusivity buckets and every documented class-tag borrowing
- The protocol generator produces a runnable test for at least the top 5 open questions

## Out of scope

Hosted DB, graph database, builder UI, the sim. Postgres portability is *designed for*, not
*migrated to*.
