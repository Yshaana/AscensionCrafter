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

CREATE TABLE IF NOT EXISTS spell_scaling (
    spell_id INTEGER,
    term_type TEXT,    -- SP / AP / RAP / WEAPON
    coefficient REAL,  -- NULL for WEAPON (normalized, no fixed coeff in text)
    FOREIGN KEY(spell_id) REFERENCES spells(id)
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

CREATE TABLE IF NOT EXISTS confirmed_facts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT,
    fact TEXT,
    source_doc TEXT,
    source_section TEXT
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

PHASE1_DDL = PHASE1_PATCH_DDL + PHASE1_CROSSWALK_DDL + PHASE1_NUMERIC_DDL


def create_catalog_schema(conn) -> None:
    conn.executescript(CATALOG_DDL)


def create_phase1_schema(conn) -> None:
    """Additive and idempotent — safe to call on an existing database."""
    conn.executescript(PHASE1_DDL)


def create_all(conn) -> None:
    create_catalog_schema(conn)
    create_phase1_schema(conn)
