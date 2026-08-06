"""DDL for the AscensionCrafter database.

Split into two blocks by origin, not by preference:

  * ``CATALOG_DDL`` — the tables `ingest/export/build_index.py` builds from
    `spell-export.json` + `Cards.txt`. Pre-existing shape, unchanged by Phase 1 T1
    so the rebuild chain keeps working (Phase 1 T4 is what reworks `spells`).
  * ``PHASE1_DDL`` — Phase 1 Task 2 (patch/realm/season) and Task 3 (crosswalk).
    Additive: it never touches a catalog table.

Other tables (`exclusivity_buckets`, `modifier_links`, `talent_amplifiers`,
`shared_synergies`, every `dbc_*` table) are still declared by the script that owns
them. That is deliberate — one writer per table is what makes the idempotency rule
checkable. They move here as Phase 1 absorbs them.

SQL is kept Postgres-portable (§2.7 rule 2): plain types, explicit FKs, no SQLite-only
syntax. `INTEGER PRIMARY KEY AUTOINCREMENT` is the one concession, and translates to
`SERIAL`/`IDENTITY` mechanically.
"""

CATALOG_DDL = """
CREATE TABLE IF NOT EXISTS spells (
    id INTEGER PRIMARY KEY,
    type TEXT,
    name TEXT,
    rank TEXT,
    tooltip TEXT,
    schools TEXT,           -- comma-joined, denormalized for quick reading
    mechanics TEXT,         -- comma-joined
    has_hidden_formula INTEGER,
    hidden_refs TEXT,       -- comma-joined spell IDs not resolvable in this export
    has_unresolved_pct INTEGER,
    class_origin TEXT,      -- ONLY confirmed values, else NULL
    class_confidence TEXT,  -- see core/spells/class_resolution.py for the tier order
    best_fit_path TEXT,     -- ONLY confirmed/derived-from-explicit-coeff, else NULL
    notes TEXT
);

-- ⚠ Rank-keyed as of session 1b (T4). `rank` is the spell's own rank label from
-- `dbc_spell_rank` (0 = not in a rank line / unknown). It is a LABEL, not a
-- disambiguator — measured in 1a: spell_id already identifies a card-rank uniquely
-- in the playable pool. It exists because coefficients DO scale with rank (1x:
-- 169 of 1,580 multi-rank lines vary, ramp-then-plateau), so a row must say which
-- rank's coefficient it carries. `source` says where the number came from:
-- 'export_tooltip' (catalog text, usually Rank 1 — the DEEPEST point of the ramp),
-- 'dbc_hidden_formula' (sub-spell text), 'dbc_rank_sibling_text' (the level-60
-- sibling's own text, added by the T4 migration), 'hand_seeded'.
-- NO foreign key on spell_id, deliberately (dropped in 1b, same precedent as
-- owned_cards): the T4 rank migration inserts rows for level-60 rank SIBLINGS,
-- and in all 697 wrong-rank cases the sibling id is absent from
-- spell-export.json entirely — an FK would reject exactly the rows that fix
-- the wrong-rank problem.
CREATE TABLE IF NOT EXISTS spell_scaling (
    spell_id INTEGER,
    term_type TEXT,    -- SP / AP / RAP / WEAPON
    coefficient REAL,  -- NULL for WEAPON (normalized, no fixed coeff in text)
    source TEXT DEFAULT 'export_tooltip',
    cp_scaling_type TEXT,   -- 'linear' | 'quadratic' | NULL (seed_cp_scaling.py)
    rank INTEGER NOT NULL DEFAULT 0,
    -- 'direct' | 'periodic' | NULL. NULL means UNKNOWN, never "direct":
    -- tooltip TEXT cannot bind a coefficient to an effect slot, which is why
    -- `_formula_terms` records is_periodic=None for every text-derived row and
    -- `ability_model` warns when it has to guess. db.ascension.gg STATES the
    -- binding ("to direct component" / "per tick"), so scraped rows can fill
    -- it in — the only source in the stack that can.
    -- 🛑 This column is why scraped coefficients are NOT summed per term_type:
    -- Pyroblast states SP 0.575 direct AND SP 0.025 periodic, and adding them
    -- would apply the DoT's coefficient to the direct hit. That is the
    -- "an aggregate across effect slots mixes units" rule (primer v30 §5),
    -- one layer up from the Lightbound Cleave 62-65 case that found it.
    component TEXT
);

-- NO foreign key on spellId, deliberately. `Cards.txt` is a CLIENT export and the
-- catalog export lags the client by days (Phase 0 finding #5). Measured 2026-08-04:
-- 47 of the owner's own 4,465 owned-card rows (39 distinct spellIds) name a card
-- absent from `spell-export.json` — and all 39 resolve in `CharacterAdvancement.dbc`.
-- They are real cards he owns, not bad data. An FK here would have to either reject
-- them or silently drop them; `build_index.py` reports the count instead.
CREATE TABLE IF NOT EXISTS owned_cards (
    cardId INTEGER,
    spellId INTEGER,
    rank INTEGER,
    pool TEXT    -- abilityNormal / abilityGolden / talentNormal / talentGolden
);

-- T6 (session 1c) widened this with provenance columns. The whole db is dropped
-- and recreated each rebuild, so the columns live in the CREATE rather than as a
-- migration. Backfilled rows carry evidence_ref = source_doc + section (that IS
-- the evidence pointer for doc-seeded facts) and NULL verified_at_patch (they
-- predate patch tracking); realm/season default to where the measurements were
-- actually made. sample_size only where the source doc states one.
CREATE TABLE IF NOT EXISTS confirmed_facts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT,
    fact TEXT,
    source_doc TEXT,
    source_section TEXT,
    verified_at_patch INTEGER,    -- REFERENCES patches(patch_id); NULL = pre-tracking
    superseded_by_patch INTEGER,  -- set when a later patch invalidates the fact
    evidence_ref TEXT,
    sample_size INTEGER,          -- hits/parses behind a measured fact, when stated
    realm TEXT,
    season TEXT
);

CREATE INDEX IF NOT EXISTS idx_spells_name ON spells(name);
CREATE INDEX IF NOT EXISTS idx_scaling_spell ON spell_scaling(spell_id);
CREATE INDEX IF NOT EXISTS idx_owned_spell ON owned_cards(spellId);
"""


# --------------------------------------------------------------------------
# Phase 1 Task 2 — patch, realm and season tracking
# --------------------------------------------------------------------------
# The realm patches daily, realms diverge in balance, and seasons reset the card
# economy (§2.5). These are prerequisites for every other table, not features:
# a fact with no patch/realm/season stamp is a fact that cannot be aged out.
PHASE1_PATCH_DDL = """
CREATE TABLE IF NOT EXISTS seasons (
    season_id  INTEGER PRIMARY KEY,
    label      TEXT NOT NULL,        -- 'S10'
    realm      TEXT NOT NULL,
    started_at TEXT,
    ended_at   TEXT
);

CREATE TABLE IF NOT EXISTS server_phases (
    phase_id     INTEGER PRIMARY KEY,
    season_id    INTEGER NOT NULL REFERENCES seasons(season_id),
    phase_number INTEGER NOT NULL,   -- the SERVER's "Phase N" label, NOT the logs
                                     -- API's phase_number field (they disagree)
    label        TEXT,               -- content tier unlocked, e.g. 'Zul''Gurub'
    started_at   TEXT,
    ended_at     TEXT,
    api_phase_id INTEGER,            -- /api/phases id, when one corresponds
    api_phase_number INTEGER,        -- the API's own field, kept for joins ONLY
    parent_api_phase_id INTEGER,     -- progression_parent_phase_id
    source       TEXT NOT NULL,      -- 'user_confirmed' | 'api_phases' | 'changelog'
    notes        TEXT
);

CREATE TABLE IF NOT EXISTS patches (
    patch_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    realm       TEXT NOT NULL,
    season_id   INTEGER REFERENCES seasons(season_id),
    patch_date  TEXT NOT NULL,       -- the changelog's group_key date, YYYY-MM-DD
    fetched_at  TEXT NOT NULL,
    entry_count INTEGER,
    UNIQUE (realm, patch_date)
);

CREATE TABLE IF NOT EXISTS patch_entries (
    entry_id          INTEGER PRIMARY KEY,   -- the changelog API's own stable id
    patch_id          INTEGER NOT NULL REFERENCES patches(patch_id),
    realms            TEXT,      -- comma-joined, parsed from [Darkmoon][Dawnrise] tags.
                                 -- EMPTY means "no statement", never "all realms"
    status            TEXT,      -- 'live' | 'pending_restart' | 'announced_future'
    status_note       TEXT,      -- verbatim, e.g. 'Going Live Monday, 3 August'
    category          TEXT,
    change_type       TEXT,      -- 'New' | 'Change'
    change_direction  TEXT,      -- 'buff'|'nerf'|'fix'|'neutral'|'new_card'
    raw_text          TEXT NOT NULL,
    first_seen_at     TEXT NOT NULL,
    status_changed_at TEXT,
    source_file       TEXT
);

CREATE TABLE IF NOT EXISTS patch_entry_spells (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id     INTEGER NOT NULL REFERENCES patch_entries(entry_id),
    spell_id     INTEGER,       -- NULL when the name never resolved
    ca_id        INTEGER,       -- CharacterAdvancement id, when it resolved there
    matched_name TEXT NOT NULL,
    match_method TEXT NOT NULL, -- 'bracketed'|'prose_name_match'|'manual'
    confidence   TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_patch_entries_patch ON patch_entries(patch_id);
CREATE INDEX IF NOT EXISTS idx_patch_entry_spells_entry ON patch_entry_spells(entry_id);
CREATE INDEX IF NOT EXISTS idx_patch_entry_spells_spell ON patch_entry_spells(spell_id);
CREATE INDEX IF NOT EXISTS idx_patches_date ON patches(patch_date);
"""


# --------------------------------------------------------------------------
# Phase 1 Task 3 — the ID crosswalk
# --------------------------------------------------------------------------
# Every external ID space plugs in as rows, never as new join logic. Phase 0 Task 5
# proved `entry_id` and `spells.id` are different spaces (0 of 1,054 match), so the
# crosswalk is the ONLY sanctioned way to cross between them.
PHASE1_CROSSWALK_DDL = """
CREATE TABLE IF NOT EXISTS spell_id_crosswalk (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    external_source TEXT NOT NULL,   -- see core/spells/crosswalk.py :: EXTERNAL_SOURCES
    external_id     TEXT NOT NULL,   -- TEXT, not INTEGER — some sources key by name
    spell_id        INTEGER NOT NULL,
    rank            INTEGER,         -- card rank (CA) or spell rank (rank lines)
    match_method    TEXT NOT NULL,   -- 'id_identity'|'name_exact'|'name+rank'|'dbc_rank_slot'
                                     -- |'dbc_rank_line'|'level_gate'|'manual'
    confidence      TEXT NOT NULL,   -- 'confirmed'|'inferred'|'conflict'|'unverified'
    evidence_ref    TEXT,
    notes           TEXT,
    UNIQUE (external_source, external_id, rank, spell_id)
);

CREATE INDEX IF NOT EXISTS idx_crosswalk_lookup
    ON spell_id_crosswalk(external_source, external_id);
CREATE INDEX IF NOT EXISTS idx_crosswalk_spell
    ON spell_id_crosswalk(spell_id);
"""

# --------------------------------------------------------------------------
# Session 1x — decoded numeric effect values
# --------------------------------------------------------------------------
# The client's Spell.dbc carries every magnitude as a numeric field, and 853 of the
# 887 spells whose export tooltip hides its formula behind a sub-spell reference
# have one. Until now the only resolver was a regex over the sub-spell's
# *description text*, which found a coefficient in 84 of them and nothing in 803.
#
# 🛑 Numeric fields only. Never the `description` string — the Titanic Mutilate trap
# (text said 115%, field said 70%, text was stale). Decoding lives in
# `core/spells/dbc_numeric.py`; this table is where it lands.
#
# Keyed on (spell_id, source_spell_id, effect_index) because a catalog spell's real
# magnitude frequently lives in a *different* spell record: `spell_id` is the card
# the value is attributed to, `source_spell_id` is the DBC record actually read, and
# `via` says which. Keeping both means a value can always be traced back to the row
# it was decoded from rather than to "the DBC" in general.
PHASE1_NUMERIC_DDL = """
CREATE TABLE IF NOT EXISTS spell_effect_values (
    spell_id         INTEGER NOT NULL,  -- catalog card this value is attributed to
    source_spell_id  INTEGER NOT NULL,  -- the Spell.dbc record actually decoded
    effect_index     INTEGER NOT NULL,  -- 0..2
    via              TEXT NOT NULL,     -- 'self' | 'hidden_ref'

    effect_type      INTEGER,
    effect_aura      INTEGER,
    base_points      INTEGER,           -- raw field, kept so decoding is auditable
    die_sides        INTEGER,
    flat_min         REAL,              -- base_points + 1
    flat_max         REAL,              -- base_points + die_sides
    per_level        REAL,              -- EffectRealPointsPerLevel
    per_combo        REAL,              -- EffectPointsPerCombo
    -- ⚠ NOT an SP/AP coefficient. Stock 3.3.5 EffectBonusMultiplier, default 1.0
    -- (7,647 of 9,211 non-zero values). NULL here means "default or unset", and
    -- the column is deliberately not named `coefficient` so nothing downstream
    -- mistakes it for one. See core/spells/dbc_numeric.py.
    bonus_multiplier REAL,
    trigger_spell    INTEGER,
    misc_value       INTEGER,
    misc_value_b     INTEGER,
    radius_index     INTEGER,
    aura_period      INTEGER,
    chain_targets    INTEGER,

    -- provenance (§2.1) — no value without a source
    source_tier      TEXT NOT NULL,     -- always 'dbc_numeric_field' (tier 4)
    evidence_ref     TEXT NOT NULL,     -- dbc:Spell.dbc:<id>:effect<N>@<archive>
    confidence       TEXT NOT NULL,
    realm            TEXT NOT NULL,
    season           TEXT NOT NULL,
    verified_at_patch INTEGER,
    extracted_at     TEXT NOT NULL,

    PRIMARY KEY (spell_id, source_spell_id, effect_index)
);

CREATE INDEX IF NOT EXISTS idx_effect_values_spell ON spell_effect_values(spell_id);
CREATE INDEX IF NOT EXISTS idx_effect_values_source ON spell_effect_values(source_spell_id);
"""

# --------------------------------------------------------------------------
# Phase 1 Task 4 — spell_mechanics: the resolved truth table (session 1b)
# --------------------------------------------------------------------------
# One row per (spell_id, rank, realm, season). `rank = 0` means rank-independent /
# the spell's own identity (1a measured that spell_id already identifies a
# card-rank uniquely in the playable pool, so rank is a label here, not a
# disambiguator). Populated by core/spells/mechanics.py via cli/mechanics.py.
#
# Provenance is PER FIELD: source_tier_json / evidence_ref_json / uncertainty_json
# are {field_name: ...} maps covering every non-NULL mechanic field in the row —
# §2.1 enforced at the row level (NOT NULL) and audited at the field level (T8).
# Two sources disagreeing on a field → both values into conflicts_json and
# confidence='conflict'; the resolver never picks a winner (§2.3).
PHASE1_MECHANICS_DDL = """
CREATE TABLE IF NOT EXISTS spell_mechanics (
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

CREATE INDEX IF NOT EXISTS idx_mechanics_school ON spell_mechanics(school);
CREATE INDEX IF NOT EXISTS idx_mechanics_effect ON spell_mechanics(effect_type);
"""

# --------------------------------------------------------------------------
# Phase 1 Task 5 — the relationship graph (session 1b)
# --------------------------------------------------------------------------
# `relation_type` is enumerated in core/spells/relationships.py :: RELATION_TYPES,
# never free text. `amplifies_school` edges carry {"school": ...} in condition_json
# and a NULL target_spell_id — they resolve against a build at graph-build time
# (core/spells/graph.py), which makes part of the graph build-dependent by design.
PHASE1_RELATIONSHIPS_DDL = """
CREATE TABLE IF NOT EXISTS spell_relationships (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
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
  verified_at_patch INTEGER NOT NULL REFERENCES patches(patch_id),
  UNIQUE (source_spell_id, target_spell_id, target_name, relation_type)
);

CREATE INDEX IF NOT EXISTS idx_rel_source ON spell_relationships(source_spell_id);
CREATE INDEX IF NOT EXISTS idx_rel_target ON spell_relationships(target_spell_id);
CREATE INDEX IF NOT EXISTS idx_rel_type   ON spell_relationships(relation_type);
"""

# --------------------------------------------------------------------------
# Phase 1 Task 6 — epistemics: fact links, open questions, retractions (1c)
# --------------------------------------------------------------------------
# §2.6: storing epistemics as prose means a fresh session can re-derive a dead
# conclusion. `retractions` makes being-wrong queryable; `open_questions` is the
# verification queue's input; `fact_spell_links` is what lets spell_profile()
# answer "which confirmed facts touch this spell" without string matching.
#
# Ownership: ingest/export/seed_epistemics.py owns open_questions + retractions
# (hand-curated, append-only source file — resolving a question means editing the
# seed, same discipline as seed_confirmed.py). fact_spell_links is derived by
# core/spells/epistemics.py :: link_facts_to_spells() each rebuild.
PHASE1_EPISTEMICS_DDL = """
CREATE TABLE IF NOT EXISTS fact_spell_links (
    fact_topic   TEXT NOT NULL,
    spell_id     INTEGER NOT NULL,
    match_method TEXT NOT NULL,   -- 'id_regex' | 'id_plus_name' | 'name_exact' | 'manual'
    confidence   TEXT NOT NULL    -- name-only matches are 'needs_review', never auto-approved
);

CREATE TABLE IF NOT EXISTS open_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE,      -- stable handle; the autoincrement id is not stable across rebuilds
    question TEXT NOT NULL,
    blocks TEXT,                    -- what decision waits on this
    status TEXT NOT NULL,           -- 'open' | 'in_progress' | 'resolved' | 'abandoned'
    resolved_by_fact_topic TEXT,
    variance_contribution REAL,     -- computed by Phase 2 sensitivity analysis; NULL until then
    affected_spell_ids TEXT,        -- comma-joined
    opened_at TEXT NOT NULL,
    opened_at_patch INTEGER
);

CREATE TABLE IF NOT EXISTS retractions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE,
    claim TEXT NOT NULL,
    why_believed TEXT NOT NULL,
    what_falsified_it TEXT NOT NULL,
    superseding_fact_topic TEXT,
    retracted_at TEXT NOT NULL,
    retracted_at_patch INTEGER
);

CREATE INDEX IF NOT EXISTS idx_fact_links_spell ON fact_spell_links(spell_id);
CREATE INDEX IF NOT EXISTS idx_fact_links_topic ON fact_spell_links(fact_topic);
CREATE INDEX IF NOT EXISTS idx_open_questions_status ON open_questions(status);
"""

# --- Phase 2 T9: the prediction ledger ----------------------------------------
# The point of this table is a property that is easy to destroy by accident: a
# prediction must be logged BEFORE the parse that tests it, and must keep the
# stamps it was made under. `sim_version` / `data_version` are what let an old
# miss be re-checked against the current model to ask whether a fix actually
# fixed it — re-deriving a stored prediction from today's model silently turns a
# fitted number into an apparently pre-registered one, which is the exact
# property the ledger exists to create.
PHASE2_PREDICTIONS_DDL = """
CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE,        -- stable handle; the autoincrement id is not
    user_id TEXT,
    character_name TEXT,
    build_spec_json TEXT NOT NULL,
    build_spec_hash TEXT NOT NULL,
    content_profile_json TEXT NOT NULL,
    predicted_value REAL NOT NULL,
    predicted_low REAL,
    predicted_high REAL,
    primary_metric TEXT NOT NULL,
    per_ability_json TEXT,            -- predicted damage share per ability
    sim_tier TEXT,
    sim_version TEXT,                 -- the session that made it, e.g. '2b'
    data_version TEXT,                -- which rebuild produced the inputs
    patch_id INTEGER,
    realm TEXT,
    season TEXT,
    notes TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS prediction_outcomes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prediction_slug TEXT NOT NULL REFERENCES predictions(slug),
    encounter_id INTEGER,
    source TEXT,                      -- log filename / report id the actual came from
    actual_value REAL NOT NULL,
    actual_per_ability_json TEXT,
    delta_pct REAL,
    within_predicted_range INTEGER,
    notes TEXT,
    recorded_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_pred_outcomes_slug
    ON prediction_outcomes(prediction_slug);
"""

PHASE1_DDL = (PHASE1_PATCH_DDL + PHASE1_CROSSWALK_DDL + PHASE1_NUMERIC_DDL
              + PHASE1_MECHANICS_DDL + PHASE1_RELATIONSHIPS_DDL
              + PHASE1_EPISTEMICS_DDL + PHASE2_PREDICTIONS_DDL)


def create_catalog_schema(conn) -> None:
    conn.executescript(CATALOG_DDL)


def create_phase1_schema(conn) -> None:
    """Additive and idempotent — safe to call on an existing database."""
    conn.executescript(PHASE1_DDL)


def create_all(conn) -> None:
    create_catalog_schema(conn)
    create_phase1_schema(conn)
