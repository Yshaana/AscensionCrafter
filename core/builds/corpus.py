"""The builds corpus (Phase 3 Task 1) — normalise raw crawl records into builds.db.

Pure logic: takes a connection and already-parsed record dicts. Reading the
gzipped NDJSON off disk is `ingest/logs_gg/build_builds_db.py`'s job.

Schema notes, where they deviate from PHASE_3_builds_repo.md's draft DDL —
each is a recorded deviation, not drift:

* **`capture_scopes` exists and performance rows key on `scope_id`.** The
  per-ability endpoints aggregate over whatever `encounterIds` the crawler
  passed (rows carry no encounter_id — PROGRESS plan-changes, 2026-08-04), so
  an ability row's true granularity is the SCOPE, not the encounter. A
  `boss_single` scope covers exactly one encounter and `encounter_id` is set;
  grind `boss_group:*` and `trash_bundle` scopes cover many and it stays NULL.
  Collapsing scopes onto encounters would fabricate per-encounter precision
  the source never had.
* **Avoidance lives in `ability_avoidance`, keyed by the ENEMY target.** The
  endpoint keys rows by `target_character_id` with no attacker id (Phase 0
  finding), so per-character miss/dodge columns in `ability_performance`
  cannot be honestly filled. They exist (per the phase doc) and stay NULL for
  crawled data; pooled inference joins `ability_avoidance` per spell instead.
* **No `patch_id`/`phase_id` columns — `patch_date`/`occurred_at` are stored.**
  Patch and phase ids in ascension.db are rebuild-scoped autoincrements (the
  same reason `open_questions` moved to slugs); a durable corpus must not
  reference them. Resolution happens at query time against the attached
  ascension.db by date.
* **`character_snapshots.gear_stats_json`, not `stats_json`.** The crawl's
  `stats_summary` block is GEAR-ONLY (`_gearOnly` key; a level-60 character
  shows Strength 13 — session 1x). Naming it `stats_json` invites reading it
  as a character sheet, which is exactly the trap 1x flagged.
* **Snapshots carry `capture_report_id`/`capture_encounter_id`.** An armory
  capture is taken AT an encounter, so for that encounter the build join is
  exact (lag 0) — better than nearest-in-time, which remains the fallback.
"""
import json

from . import gear

SCHEMA = """
CREATE TABLE IF NOT EXISTS characters (
    character_id INTEGER PRIMARY KEY,
    name TEXT, realm TEXT, guild TEXT, level INTEGER,
    primary_role TEXT,              -- 'dps','tank','healer','unknown'
    source TEXT NOT NULL,           -- 'crawled','user_provided','manual'
    first_seen_at TEXT, last_seen_at TEXT
);

CREATE TABLE IF NOT EXISTS character_snapshots (
    snapshot_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id INTEGER NOT NULL REFERENCES characters(character_id),
    captured_at  TEXT NOT NULL,     -- site capture time (UTC ISO), NOT crawl time
    crawled_at   TEXT,              -- when our crawler stored it (UTC ISO)
    patch_date   TEXT, season TEXT, realm TEXT,
    path TEXT, spec_index INTEGER, spec_name TEXT, spec_role TEXT,
    capture_report_id INTEGER,      -- the encounter this capture was taken at,
    capture_encounter_id INTEGER,   --   when the site recorded one (exact join)
    captured_for_boss TEXT,
    armory_hash TEXT,
    gear_stats_json TEXT,           -- stats_summary: GEAR-ONLY (_gearOnly trap, 1x)
    source TEXT NOT NULL,
    source_file TEXT,
    UNIQUE (character_id, captured_at)
);

CREATE TABLE IF NOT EXISTS snapshot_cards (
    snapshot_id INTEGER NOT NULL REFERENCES character_snapshots(snapshot_id),
    tree TEXT NOT NULL,             -- 'abilities' | 'talents'
    external_id TEXT NOT NULL,      -- entry_id (CharacterAdvancement ID), raw
    spell_id INTEGER,               -- level-appropriate spell, resolved at BUILD time
    card_spell_id INTEGER,          -- the held card rank's own spell id
    spell_id_confidence TEXT,
    name TEXT, rank INTEGER, max_rank INTEGER,
    per_rank_tooltip_json TEXT,
    PRIMARY KEY (snapshot_id, tree, external_id)
);

CREATE TABLE IF NOT EXISTS snapshot_gear (
    snapshot_id INTEGER NOT NULL REFERENCES character_snapshots(snapshot_id),
    slot INTEGER NOT NULL,
    item_id INTEGER, item_name TEXT, quality INTEGER, item_level INTEGER,
    enchant_id INTEGER, gems_json TEXT,
    stats_json TEXT,                -- resolved_bisbeard stats when present
    drop_source TEXT, source_category TEXT, tier TEXT,
    -- resolved_bisbeard.match_type: 'direct' (matched on item_id) or
    -- 'name_fallback' (matched on NAME). The distinction is load-bearing:
    -- 476 item names in this corpus span several item_ids at different
    -- difficulties with different stat blocks, so a name match can land on
    -- the wrong variant. Kept as a column rather than dropped, so a
    -- name-matched stat block can be excluded or flagged downstream.
    stats_match_type TEXT,
    -- {min,max,speed,hand,...} for weapons, else NULL. Weapon damage is in NO
    -- stat block on this server's data (resolved_bisbeard.damage is null on
    -- every weapon in the corpus) — it is parsed from the rendered item
    -- description and self-checked against that description's stated DPS.
    -- Without it a crawled character sims with no weapon at all.
    weapon_json TEXT,
    PRIMARY KEY (snapshot_id, slot)
);

CREATE TABLE IF NOT EXISTS encounters (
    encounter_id INTEGER PRIMARY KEY,   -- the site's own global encounter id
    report_id INTEGER,
    zone TEXT, boss_name TEXT, boss_id INTEGER, difficulty TEXT,
    is_trash INTEGER,
    content_type TEXT,              -- 'raid','dungeon_normal','dungeon_mythic','unknown'
    content_type_confidence TEXT,   -- 'api_reported','inferred','unknown'
    target_count INTEGER,           -- NULL if unknown. NEVER defaulted to 1
    target_count_confidence TEXT,
    duration_seconds REAL,
    occurred_at TEXT,               -- UTC ISO (site timestamps are UTC)
    success INTEGER, wipe_percent REAL, validation_status TEXT,
    participant_count INTEGER, player_participant_count INTEGER,
    patch_date TEXT, realm TEXT, season TEXT
);

CREATE TABLE IF NOT EXISTS capture_scopes (
    scope_id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    scope TEXT NOT NULL,            -- 'boss_single' | 'boss_group:<boss_id>' | 'trash_bundle'
    encounter_ids_json TEXT NOT NULL,
    encounter_id INTEGER,           -- set iff the scope covers exactly one encounter
    captured_at TEXT,
    patch_date TEXT, realm TEXT, season TEXT,
    UNIQUE (report_id, scope, encounter_ids_json)
);

CREATE TABLE IF NOT EXISTS encounter_performance (
    scope_id INTEGER NOT NULL REFERENCES capture_scopes(scope_id),
    encounter_id INTEGER,           -- NULL for aggregated (group/trash) scopes
    character_id INTEGER NOT NULL,
    snapshot_id INTEGER,            -- nearest-in-time build; NULL if none close enough
    snapshot_lag_hours REAL,        -- how stale the matched build is
    role TEXT,
    path TEXT,                      -- character_spec from the parse (per-parse Path!)
    -- total_damage: the WHOLE logged total for this character. The endpoint's
    --   rows[] are owner-MERGED, so this already contains pet damage.
    -- pet_damage: a RESTATEMENT — "of that total, this much was pet-delivered".
    --   NEVER added to total_damage; dps = total_damage / duration (3i B3, E15).
    -- 🆕 3j B5 — pet_damage's NULL-vs-0 semantics, stated rather than left to
    --   be rediscovered: it is a correlated SUM over pet_ability_damage, and
    --   SUM over an empty set is NULL, so **NULL means "no pet rows for this
    --   (scope, character)" and 0 never occurs.** Measured on the live corpus:
    --   12,062 rows NULL, 0 rows exactly 0, 7,245 rows > 0. Consequence for
    --   callers: use `COALESCE(pet_damage, 0)` when summing, and do NOT read
    --   NULL as "unknown" — it is a positive statement that this character
    --   fielded no pet in this scope.
    total_damage REAL, pet_damage REAL, dps REAL,
    total_healing REAL, effective_healing REAL, hps REAL,
    damage_taken REAL, deaths INTEGER,
    percentile REAL,
    PRIMARY KEY (scope_id, character_id)
);

CREATE TABLE IF NOT EXISTS ability_performance (
    scope_id INTEGER NOT NULL REFERENCES capture_scopes(scope_id),
    encounter_id INTEGER,           -- NULL for aggregated scopes
    character_id INTEGER NOT NULL,
    spell_id INTEGER,               -- client Spell.dbc space (Phase 0 A2)
    spell_name TEXT, spell_school TEXT,
    is_pet INTEGER NOT NULL DEFAULT 0,
    casts INTEGER, hits INTEGER, crits INTEGER,
    misses INTEGER, dodges INTEGER, parries INTEGER,   -- NULL for crawled data:
    resists_partial INTEGER, resists_full INTEGER,     --   avoidance has no attacker id;
    immunes INTEGER,                                   --   see ability_avoidance
    damage_total REAL, healing_total REAL, overhealing REAL, absorbs REAL,
    damage_share_pct REAL,
    PRIMARY KEY (scope_id, character_id, spell_id, spell_name, is_pet)
);

-- 🆕 3i B2 (E15) — the endpoint's per-pet RESTATEMENT, kept out of the table
-- it used to double-count. `rows[]` is owner-MERGED (3h D2, report 79): it
-- already contains pet damage, and `pet_spell_damage_by_owner` restates it.
-- Ingesting both into ability_performance stored pet damage twice (E15), so:
-- ability_performance holds rows[] ONLY (is_pet is now constant 0 there; the
-- column and PK stay until the deferred schema commit, 3i Q3), and the pet
-- block lands here — the attribution layer E3's resolution route needs
-- (pet_damage_not_derivable), structurally unsummable into the canonical
-- totals by accident.
-- 🛑 NEVER add this table's damage to ability_performance sums: it is a
-- restatement ("of the owner's total, this much was pet-delivered"), not an
-- addition. ⚠ On aggregated trash_bundle/boss_group scopes the two payload
-- blocks DISAGREE (pet up to 1800× the owner-merged copy, 0 such cases in any
-- boss_single scope — scope drift between the blocks, registered in
-- ENGINE_BUGS E15's closure, unresolvable from our side), so per-pet figures
-- from aggregated scopes carry that caveat.
CREATE TABLE IF NOT EXISTS pet_ability_damage (
    scope_id INTEGER NOT NULL REFERENCES capture_scopes(scope_id),
    encounter_id INTEGER,
    character_id INTEGER NOT NULL,   -- the OWNER, as ability_performance keys it
    spell_id INTEGER, spell_name TEXT, spell_school TEXT,
    casts INTEGER, hits INTEGER, crits INTEGER,
    damage_total REAL,
    PRIMARY KEY (scope_id, character_id, spell_id, spell_name)
);

-- Avoidance ground truth: how often each PLAYER ability was avoided by each enemy.
-- Keyed by the enemy target; the endpoint carries NO attacker id (Phase 0).
CREATE TABLE IF NOT EXISTS ability_avoidance (
    scope_id INTEGER NOT NULL REFERENCES capture_scopes(scope_id),
    encounter_id INTEGER,
    target_character_id INTEGER NOT NULL,   -- the ENEMY unit
    spell_id INTEGER, spell_name TEXT, spell_school TEXT,
    damage REAL, hit_count INTEGER, casts INTEGER,
    miss_count INTEGER, dodge_count INTEGER, parry_count INTEGER,
    deflect_count INTEGER, immune_count INTEGER, reflect_count INTEGER,
    evade_count INTEGER,
    blocked REAL, block_count INTEGER, block_full_count INTEGER,
    resisted REAL, resist_count INTEGER, resist_full_count INTEGER,
    absorbs REAL, absorb_count INTEGER, absorb_full_count INTEGER,
    PRIMARY KEY (scope_id, target_character_id, spell_id, spell_name)
);

-- Damage the raid took, per player per ability (participantType=friendlies).
CREATE TABLE IF NOT EXISTS damage_taken_rows (
    scope_id INTEGER NOT NULL REFERENCES capture_scopes(scope_id),
    encounter_id INTEGER,
    target_character_id INTEGER NOT NULL,   -- the PLAYER hit
    spell_id INTEGER, spell_name TEXT, spell_school TEXT,
    damage REAL, hit_count INTEGER,
    PRIMARY KEY (scope_id, target_character_id, spell_id, spell_name)
);

CREATE TABLE IF NOT EXISTS leaderboard_entries (
    captured_at TEXT NOT NULL,
    phase INTEGER, location TEXT, difficulty TEXT, role TEXT, metric TEXT,
    character_id INTEGER, name TEXT, class TEXT, spec TEXT,
    total_points REAL, bosses_killed INTEGER, total_bosses INTEGER,
    PRIMARY KEY (captured_at, phase, location, difficulty, role, metric, character_id)
);

CREATE TABLE IF NOT EXISTS corpus_files (
    file TEXT PRIMARY KEY,
    records INTEGER, ingested INTEGER, skipped INTEGER
);

CREATE INDEX IF NOT EXISTS idx_ability_perf_spell ON ability_performance(spell_id);
CREATE INDEX IF NOT EXISTS idx_ability_avoid_spell ON ability_avoidance(spell_id);
CREATE INDEX IF NOT EXISTS idx_snapshots_char ON character_snapshots(character_id, captured_at);
CREATE INDEX IF NOT EXISTS idx_cards_spell ON snapshot_cards(spell_id);
CREATE INDEX IF NOT EXISTS idx_cards_external ON snapshot_cards(external_id);
CREATE INDEX IF NOT EXISTS idx_enc_perf_char ON encounter_performance(character_id);
CREATE INDEX IF NOT EXISTS idx_gear_item ON snapshot_gear(item_id);
"""

_ROLE_MAP = {"DAMAGER": "dps", "TANK": "tank", "HEALER": "healer"}


# 🆕 3j B1 (`AUDIT_3I_ADVERSARIAL` §7.1) — THE CORPUS SCHEMA VERSION.
#
#   0  pre-3i. `ability_performance` holds pet rows (`is_pet = 1`) that are a
#      RESTATEMENT of damage already merged into `rows[]`, so every SUM over it
#      double-counts pet damage, and `dps` adds `pet_damage` to a total that
#      already contains it (E15).
#   1  post-3i-B. Pet restatements live in `pet_ability_damage`;
#      `ability_performance` is owner rows only. Post-3j-B3, `spell_id` is
#      never NULL in either table (`UNRESOLVED_SPELL_ID`).
#
# `init_schema` was `CREATE TABLE IF NOT EXISTS` only, `PRAGMA user_version`
# was 0 and never set, and there was no backfill — so a retained pre-3i
# `builds.db` kept its doubled rows, silently, while `pet_damage` became NULL
# (a correlated subquery over an empty side table). Three consumers have no
# `is_pet` filter and would have gone on double-counting: `compute_damage_share`
# (feeds `core/builds/search.py`), `demand_list` (ranks scraper priority) and
# `build_extract_scope_request` (drives DBC extract requests). The only thing
# standing between that and a wrong answer was `build_builds_db.py` unlinking
# the DB on every build — a habit, not a guard.
CORPUS_SCHEMA_VERSION = 1


class CorpusSchemaTooOld(RuntimeError):
    """A `builds.db` written before the E15 fix, opened for reading.

    🛑 There is no third path here. Either migrate it (`migrate_schema`) or
    refuse to read it. Reading it "carefully" is what the three unguarded
    consumers were already doing.
    """


def init_schema(conn):
    conn.executescript(SCHEMA)
    conn.execute(f"PRAGMA user_version = {CORPUS_SCHEMA_VERSION}")


def schema_version(conn):
    return conn.execute("PRAGMA user_version").fetchone()[0]


def migrate_schema(conn):
    """Bring a pre-`3i` corpus to `CORPUS_SCHEMA_VERSION`, or say it cannot.

    Returns `(from_version, to_version, notes)`. Idempotent: on an
    already-current DB it changes nothing and reports so.

    🛑 **The v0 → v1 migration DELETES rather than moves.** The `is_pet = 1`
    rows in `ability_performance` are a restatement of damage already present
    in the owner rows, so they are pure duplication — there is nothing in them
    to preserve. `pet_ability_damage` cannot be reconstructed from them either,
    because the per-pet attribution the endpoint carried was never stored. A
    migrated v0 database therefore has **correct totals and an empty pet side
    table**, which is a different state from a freshly built v1 and is reported
    as such rather than papered over. The honest fix for a v0 DB is a rebuild;
    this exists so that a DB which is *read* rather than rebuilt cannot be read
    wrong.
    """
    v = schema_version(conn)
    if v >= CORPUS_SCHEMA_VERSION:
        return v, v, "already current — nothing to migrate"
    conn.executescript(SCHEMA)
    n_pet = conn.execute(
        "SELECT COUNT(*) FROM ability_performance WHERE is_pet = 1").fetchone()[0]
    conn.execute("DELETE FROM ability_performance WHERE is_pet = 1")
    n_side = conn.execute(
        "SELECT COUNT(*) FROM pet_ability_damage").fetchone()[0]
    conn.execute(f"PRAGMA user_version = {CORPUS_SCHEMA_VERSION}")
    conn.commit()
    note = (f"deleted {n_pet} is_pet=1 restatement row(s) from "
            f"ability_performance (E15). pet_ability_damage holds {n_side} "
            f"row(s)")
    if not n_side:
        note += (" — EMPTY, and it cannot be reconstructed from the deleted "
                 "rows: the per-pet attribution was never stored. Totals are "
                 "now correct; per-pet breakdowns need a rebuild")
    return v, CORPUS_SCHEMA_VERSION, note


def assert_schema_current(conn, *, what="this tool"):
    """Refuse to read a corpus written before the E15 fix.

    MUTATION THAT MAKES THIS FAIL (red): delete the `raise`. A v0 database then
    reads clean through `compute_damage_share` / `demand_list` /
    `build_extract_scope_request`, every one of which sums
    `ability_performance` with no `is_pet` filter and would double-count pet
    damage exactly as it did before `3i`. GREEN PATH: the raise as written,
    plus `migrate_schema()` for a caller that wants to repair rather than
    refuse — both reachable, neither a stub.
    """
    v = schema_version(conn)
    if v < CORPUS_SCHEMA_VERSION:
        raise CorpusSchemaTooOld(
            f"{what} refuses to read this builds.db: PRAGMA user_version is "
            f"{v}, this code expects {CORPUS_SCHEMA_VERSION}.\n"
            f"A v0 corpus stores pet damage TWICE in ability_performance "
            f"(E15), so every SUM over it — damage share, scraper demand, DBC "
            f"extract scope — is inflated for every pet-owning character.\n"
            f"Fix it by rebuilding (py ingest/logs_gg/build_builds_db.py), or "
            f"call core.builds.corpus.migrate_schema(conn) to delete the "
            f"restatement rows in place.")
    return v


# ---------------------------------------------------------------------------
# per-record ingestion
# ---------------------------------------------------------------------------

def _seen_character(conn, character_id, name, realm, captured_at, *,
                    guild=None, level=None, role=None, source="crawled"):
    conn.execute(
        """INSERT INTO characters (character_id, name, realm, guild, level,
                                   primary_role, source, first_seen_at, last_seen_at)
           VALUES (?,?,?,?,?,?,?,?,?)
           ON CONFLICT(character_id) DO UPDATE SET
             name = COALESCE(excluded.name, name),
             guild = COALESCE(excluded.guild, guild),
             level = COALESCE(excluded.level, level),
             primary_role = COALESCE(excluded.primary_role, primary_role),
             first_seen_at = MIN(COALESCE(first_seen_at, excluded.first_seen_at),
                                 COALESCE(excluded.first_seen_at, first_seen_at)),
             last_seen_at = MAX(COALESCE(last_seen_at, excluded.last_seen_at),
                                COALESCE(excluded.last_seen_at, last_seen_at))""",
        (character_id, name, realm, guild, level, role, source,
         captured_at, captured_at),
    )


def ingest_armory_record(conn, rec):
    """One `character_armory` record -> characters + snapshot + cards + gear.

    Returns 'ingested' | 'skipped:<reason>'. spell_id resolution is a separate
    post-pass (`resolve_snapshot_cards`) so a crosswalk improvement re-resolves
    without re-reading the crawl.
    """
    payload = rec.get("payload") or {}
    armory = payload.get("armory") or {}
    ci = armory.get("ci_resolved") or {}
    if not ci:
        return "skipped:no_ci_resolved"

    character_id = rec.get("character_id")
    if character_id is None:
        return "skipped:no_character_id"

    capture = armory.get("capture") or {}
    captured_at = capture.get("captured_at") or rec.get("captured_at")
    player = ci.get("player") or {}
    spec = ci.get("specialization") or {}
    guild = (ci.get("guild") or {}).get("name") or player.get("guild")
    role = _ROLE_MAP.get(spec.get("active_spec_role"), None)
    path = ((ci.get("primary_stat") or {}).get("token")
            or ((payload.get("primary_stat") or {}).get("current") or {}).get("stat"))

    _seen_character(conn, character_id, rec.get("character_name") or player.get("name"),
                    rec.get("realm"), captured_at,
                    guild=guild, level=player.get("level"), role=role)

    enc = capture.get("encounter") or {}
    stats_summary = armory.get("stats_summary")
    conn.execute(
        """INSERT INTO character_snapshots
             (character_id, captured_at, crawled_at, patch_date, season, realm,
              path, spec_index, spec_name, spec_role,
              capture_report_id, capture_encounter_id, captured_for_boss,
              armory_hash, gear_stats_json, source, source_file)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
           ON CONFLICT(character_id, captured_at) DO UPDATE SET
             armory_hash = excluded.armory_hash,
             gear_stats_json = excluded.gear_stats_json,
             crawled_at = excluded.crawled_at""",
        (character_id, captured_at, rec.get("captured_at"), rec.get("patch_date"),
         str(rec.get("season")), rec.get("realm"),
         path, spec.get("active_spec_idx"), spec.get("active_spec_name"),
         spec.get("active_spec_role"),
         enc.get("report_id"), enc.get("id"), capture.get("captured_for_boss"),
         rec.get("armory_hash"),
         json.dumps(stats_summary) if stats_summary else None,
         "crawled", rec.get("_source_file")),
    )
    snapshot_id = conn.execute(
        "SELECT snapshot_id FROM character_snapshots "
        "WHERE character_id = ? AND captured_at = ?",
        (character_id, captured_at)).fetchone()[0]

    # cards: active spec only is what the capture carries (T5 scope decision)
    trees = ((spec.get("talents") or {}).get("trees") or {})
    card_rows = []
    for tree_slug, tree in trees.items():
        for t in (tree or {}).get("talents") or []:
            card_rows.append((
                snapshot_id, tree_slug, str(t.get("entry_id")),
                t.get("name"), t.get("rank"), t.get("max_ranks"),
                json.dumps(t.get("per_rank_text")) if t.get("per_rank_text") else None,
            ))
    conn.executemany(
        """INSERT OR REPLACE INTO snapshot_cards
             (snapshot_id, tree, external_id, name, rank, max_rank, per_rank_tooltip_json)
           VALUES (?,?,?,?,?,?,?)""", card_rows)

    gear_rows = []
    for slot_key, item in (ci.get("gear") or {}).items():
        if not isinstance(item, dict) or not item.get("item_id"):
            continue
        resolved = item.get("resolved_item") or {}
        bis = item.get("resolved_bisbeard") or {}
        gear_rows.append((
            snapshot_id, int(slot_key), item.get("item_id"), resolved.get("name"),
            resolved.get("quality"), resolved.get("item_level"),
            item.get("enchant") or None,
            json.dumps(item.get("gems")) if item.get("gems") else None,
            json.dumps(bis.get("stats")) if bis.get("stats") else None,
            bis.get("source"), bis.get("source_category"),
            bis.get("version") or resolved.get("mythic_tier"),
            bis.get("match_type"),
            json.dumps(_weapon) if (_weapon := gear.parse_weapon_damage(
                bis.get("description"), resolved.get("inventory_type"))) else None,
        ))
    conn.executemany(
        """INSERT OR REPLACE INTO snapshot_gear
             (snapshot_id, slot, item_id, item_name, quality, item_level,
              enchant_id, gems_json, stats_json, drop_source, source_category, tier,
              stats_match_type, weapon_json)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", gear_rows)
    return "ingested"


def _content_type(difficulty, trial_level, zone_instance_type=None):
    """Content type with an honest confidence tag. 'ascended' is the raid
    difficulty on S10; mythic dungeons carry a trial/mythic marker."""
    if zone_instance_type == "raid":
        return "raid", "api_reported"
    if difficulty == "ascended":
        return "raid", "inferred"
    if trial_level:
        return "dungeon_mythic", "inferred"
    if difficulty == "normal":
        return "dungeon_normal", "inferred"
    return "unknown", "unknown"


def ingest_report_record(conn, rec):
    payload = rec.get("payload") or {}
    report_id = rec.get("report_id")
    encounters = payload.get("encounters") or []
    rows = []
    for e in encounters:
        ct, ct_conf = _content_type(e.get("difficulty"), e.get("trial_level"))
        dur = e.get("duration_seconds")
        rows.append((
            e.get("id"), report_id, e.get("zone"), e.get("name"), e.get("boss_id"),
            e.get("difficulty"), 0 if e.get("is_boss_encounter") else 1,
            ct, ct_conf,
            None, "unknown",                       # target_count: NEVER defaulted
            float(dur) if dur is not None else None,
            e.get("start_time"),
            1 if e.get("success") else 0, e.get("wipe_percent"),
            e.get("validation_status"),
            int(e["participant_count"]) if e.get("participant_count") is not None else None,
            int(e["player_participant_count"]) if e.get("player_participant_count") is not None else None,
            rec.get("patch_date"), rec.get("realm"), str(rec.get("season")),
        ))
    conn.executemany(
        """INSERT OR REPLACE INTO encounters
             (encounter_id, report_id, zone, boss_name, boss_id, difficulty, is_trash,
              content_type, content_type_confidence, target_count, target_count_confidence,
              duration_seconds, occurred_at, success, wipe_percent, validation_status,
              participant_count, player_participant_count, patch_date, realm, season)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", rows)
    return "ingested" if rows else "skipped:no_encounters"


def _scope_id(conn, rec):
    report_id = rec.get("report_id")
    scope = rec.get("scope")
    enc_ids = rec.get("encounter_ids") or []
    enc_json = json.dumps(sorted(enc_ids))
    single = enc_ids[0] if len(enc_ids) == 1 else None
    conn.execute(
        """INSERT OR IGNORE INTO capture_scopes
             (report_id, scope, encounter_ids_json, encounter_id, captured_at,
              patch_date, realm, season)
           VALUES (?,?,?,?,?,?,?,?)""",
        (report_id, scope, enc_json, single, rec.get("captured_at"),
         rec.get("patch_date"), rec.get("realm"), str(rec.get("season"))))
    row = conn.execute(
        "SELECT scope_id, encounter_id FROM capture_scopes "
        "WHERE report_id = ? AND scope = ? AND encounter_ids_json = ?",
        (report_id, scope, enc_json)).fetchone()
    return row[0], row[1]


# 🆕 3j B3 (`AUDIT_3I_ADVERSARIAL` §7.5) — the sentinel a NULL `spell_id`
# becomes. SQLite permits NULLs in a rowid table's PRIMARY KEY columns, so a
# row whose `spell_id` decodes to None escapes `INSERT OR REPLACE` dedupe
# entirely: the auditor measured 3 ingests of one record producing 3 rows and
# 3000 damage in `ability_performance`, straight into `total_damage -> dps ->`
# the gate. Reachable — `spell_id` is a string field in the source payload and
# 5 report ids (79, 104, 105, 106, 107) appear twice across the committed crawl
# days.
#
# ⚠ MEASURED BEFORE FIXING, per the work order: the real corpus carries
# **0 of 291,320** NULL-`spell_id` rows in `ability_performance` and **0 of
# 22,427** in `pet_ability_damage`. So this is a latent route, not a live
# inflation, and closing it CANNOT move the gate — there is nothing to
# de-duplicate. Had the count been non-zero it would have been a finding and a
# pre-registered gate move for a later session, not a fix here.
#
# The sentinel is negative and far outside both the client's Spell.dbc space
# and the log's auto-attack ids (-1, -22..-26), so it can never collide with a
# real key, and it is VISIBLE: a query can find these rows and count them,
# which `NULL` made impossible.
UNRESOLVED_SPELL_ID = -999999


def _int_or_none(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _spell_key(v):
    """`spell_id` as a PRIMARY-KEY-safe value — never NULL.

    🛑 `3j` B3. `_int_or_none` is still the right decoder (a `spell_id` we
    cannot read is not a spell id), but its `None` must not reach a PK column.
    Rows keep their unresolved status explicitly, as `UNRESOLVED_SPELL_ID`,
    where dedupe can see them and a reader can count them.
    """
    sid = _int_or_none(v)
    return UNRESOLVED_SPELL_ID if sid is None else sid


def ingest_abilities_record(conn, rec):
    payload = rec.get("payload") or {}
    rows = payload.get("rows") or []
    scope_id, enc_id = _scope_id(conn, rec)
    out = []
    for r in rows:
        if r.get("character_type") != "player":
            continue
        _seen_character(conn, r.get("character_id"), r.get("character_name"),
                        rec.get("realm"), rec.get("captured_at"))
        out.append((
            scope_id, enc_id, r.get("character_id"),
            _spell_key(r.get("spell_id")), r.get("spell_name"), r.get("spell_school"),
            0, r.get("casts"), r.get("hits"), r.get("crits"),
            r.get("total_damage"), None, None, None,
        ))
    # 🛑 3i B2 (E15) — the pet block is a RESTATEMENT of damage already merged
    # into rows[] (3h D2), so it must not land in ability_performance, where
    # every SUM was counting it twice. rows[] is canonical there; the per-pet
    # attribution goes to its own table (see the pet_ability_damage DDL).
    pets = []
    for owner_id, pet_rows in (payload.get("pet_spell_damage_by_owner") or {}).items():
        for r in pet_rows or []:
            if not r.get("is_pet"):
                continue
            pets.append((
                scope_id, enc_id, _int_or_none(owner_id),
                _spell_key(r.get("spell_id")), r.get("spell_name"), r.get("spell_school"),
                r.get("casts"), r.get("hits"), r.get("crits"),
                r.get("total_damage"),
            ))
    conn.executemany(
        """INSERT OR REPLACE INTO ability_performance
             (scope_id, encounter_id, character_id, spell_id, spell_name, spell_school,
              is_pet, casts, hits, crits, damage_total, healing_total, overhealing, absorbs)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", out)
    conn.executemany(
        """INSERT OR REPLACE INTO pet_ability_damage
             (scope_id, encounter_id, character_id, spell_id, spell_name, spell_school,
              casts, hits, crits, damage_total)
           VALUES (?,?,?,?,?,?,?,?,?,?)""", pets)
    return "ingested" if out or pets else "skipped:no_player_rows"


def ingest_healing_record(conn, rec):
    payload = rec.get("payload") or {}
    rows = payload.get("rows") or []
    scope_id, enc_id = _scope_id(conn, rec)
    out = []
    for r in rows:
        if r.get("character_type") != "player":
            continue
        out.append((
            scope_id, enc_id, r.get("character_id"),
            _spell_key(r.get("spell_id")), r.get("spell_name"), r.get("spell_school"),
            0, r.get("casts"), r.get("hits"), r.get("crits"),
            None, r.get("total_healing"), r.get("overhealing"), r.get("total_absorbs"),
        ))
    conn.executemany(
        """INSERT INTO ability_performance
             (scope_id, encounter_id, character_id, spell_id, spell_name, spell_school,
              is_pet, casts, hits, crits, damage_total, healing_total, overhealing, absorbs)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
           ON CONFLICT(scope_id, character_id, spell_id, spell_name, is_pet)
           DO UPDATE SET healing_total = excluded.healing_total,
                         overhealing = excluded.overhealing,
                         absorbs = excluded.absorbs""", out)
    return "ingested" if out else "skipped:no_player_rows"


def ingest_avoidance_record(conn, rec):
    payload = rec.get("payload") or {}
    rows = payload.get("rows") or []
    scope_id, enc_id = _scope_id(conn, rec)
    out = [(
        scope_id, enc_id, r.get("target_character_id"),
        _spell_key(r.get("spell_id")), r.get("spell_name"), r.get("spell_school"),
        r.get("damage"), r.get("hit_count"), r.get("casts"),
        r.get("miss_count"), r.get("dodge_count"), r.get("parry_count"),
        r.get("deflect_count"), r.get("immune_count"), r.get("reflect_count"),
        r.get("evade_count"),
        r.get("blocked"), r.get("block_count"), r.get("block_full_count"),
        r.get("resisted"), r.get("resist_count"), r.get("resist_full_count"),
        r.get("absorbs"), r.get("absorb_count"), r.get("absorb_full_count"),
    ) for r in rows]
    conn.executemany(
        """INSERT OR REPLACE INTO ability_avoidance
             (scope_id, encounter_id, target_character_id, spell_id, spell_name,
              spell_school, damage, hit_count, casts,
              miss_count, dodge_count, parry_count, deflect_count, immune_count,
              reflect_count, evade_count,
              blocked, block_count, block_full_count,
              resisted, resist_count, resist_full_count,
              absorbs, absorb_count, absorb_full_count)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", out)
    return "ingested" if out else "skipped:no_rows"


def ingest_damage_taken_record(conn, rec):
    payload = rec.get("payload") or {}
    rows = payload.get("rows") or []
    scope_id, enc_id = _scope_id(conn, rec)
    out = [(
        scope_id, enc_id, r.get("target_character_id"),
        _spell_key(r.get("spell_id")), r.get("spell_name"), r.get("spell_school"),
        r.get("damage"), r.get("hit_count"),
    ) for r in rows]
    conn.executemany(
        """INSERT OR REPLACE INTO damage_taken_rows
             (scope_id, encounter_id, target_character_id, spell_id, spell_name,
              spell_school, damage, hit_count)
           VALUES (?,?,?,?,?,?,?,?)""", out)
    return "ingested" if out else "skipped:no_rows"


def ingest_leaderboard_record(conn, rec):
    payload = rec.get("payload") or {}
    q = rec.get("query") or {}
    out = []
    for zone_data in (payload.get("rankings") or {}).values():
        for entries in (zone_data or {}).values():
            for e in entries or []:
                out.append((
                    rec.get("captured_at"), q.get("phase"), q.get("location"),
                    q.get("difficulty"), q.get("role"), q.get("metric"),
                    e.get("character_id"), e.get("name"), e.get("class"), e.get("spec"),
                    e.get("total_points"), e.get("bosses_killed"), e.get("total_bosses"),
                ))
    conn.executemany(
        """INSERT OR REPLACE INTO leaderboard_entries
             (captured_at, phase, location, difficulty, role, metric,
              character_id, name, class, spec, total_points, bosses_killed, total_bosses)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""", out)
    return "ingested" if out else "skipped:no_rows"


INGESTERS = {
    "character_armory": ingest_armory_record,
    "report_encounters": ingest_report_record,
    "abilities": ingest_abilities_record,
    "healing": ingest_healing_record,
    "avoidance": ingest_avoidance_record,
    "damage_taken": ingest_damage_taken_record,
    "leaderboard": ingest_leaderboard_record,
    "phases_snapshot": None,   # phase timeline lives in ascension.db (server_phases)
}


# ---------------------------------------------------------------------------
# post-passes
# ---------------------------------------------------------------------------

def resolve_snapshot_cards(conn, resolver):
    """Resolve every snapshot card's entry_id -> spell ids.

    `resolver(entry_id, rank)` returns a dict with `card_spell_id`,
    `level_spell_id` (None when the rank line is ambiguous) and `confidence`,
    or None when the entry_id has no crosswalk row. The caller builds it from
    ascension.db (`core.spells.crosswalk.resolve_entry_id`) — this module never
    sees that database. Never resolves by name (hard rule).
    """
    rows = conn.execute(
        "SELECT DISTINCT external_id, rank FROM snapshot_cards").fetchall()
    stats = {"pairs": len(rows), "resolved": 0, "ambiguous": 0, "unresolved": 0}
    for external_id, rank in rows:
        hit = resolver(external_id, rank)
        if hit is None:
            stats["unresolved"] += 1
            conn.execute(
                "UPDATE snapshot_cards SET spell_id = NULL, card_spell_id = NULL, "
                "spell_id_confidence = 'unresolved' WHERE external_id = ? AND rank IS ?",
                (external_id, rank))
            continue
        if hit.get("level_rank_ambiguous"):
            stats["ambiguous"] += 1
        else:
            stats["resolved"] += 1
        conn.execute(
            "UPDATE snapshot_cards SET spell_id = ?, card_spell_id = ?, "
            "spell_id_confidence = ? WHERE external_id = ? AND rank IS ?",
            (hit.get("level_spell_id"), hit.get("card_spell_id"),
             hit.get("confidence"), external_id, rank))
    return stats


def compute_encounter_performance(conn):
    """Aggregate ability rows into per-(scope, character) performance.

    DPS uses the summed duration of the scope's encounters — exact for
    boss_single, an aggregate mean for grouped scopes (which is all the
    endpoint ever offered for them).

    🆕 **`3j` B5 — the cohort-composition change `3i` B made, measured and
    named** (`AUDIT_3I_ADVERSARIAL` §7.4). This selects `FROM
    ability_performance`, so a character present ONLY in
    `pet_spell_damage_by_owner` now produces **no** `encounter_performance`
    row. Before the E15 fix its pet rows lived in `ability_performance`, so it
    got a row with `dps = pet_damage/dur`, which cleared
    `calibrate_crawled.py`'s `ep.dps > 100` cohort filter.

    **Measured on the live corpus, 2026-08-07:**

    * **695** distinct owner ids appear in `pet_ability_damage` with no owner
      row anywhere in `ability_performance`;
    * **0 of those 695 are in `characters`** — `_seen_character` runs only for
      `rows[]` entries with `character_type == "player"`, so every one of them
      is a non-player owner the corpus never tracked as a character. They are
      not players who vanished; they are rows that should never have produced a
      character-shaped record, and pre-fix they did;
    * **0 of the 41 frozen cohort members are affected** — all 41 have owner
      rows and all 41 have `encounter_performance` rows.

    So the change is real, is in the correct direction, and touches nothing the
    gate reads. Recorded because "it happens not to matter here" and "it does
    not happen" are different statements, and only one of them stays true.
    """
    conn.execute("DELETE FROM encounter_performance")
    # 🛑 3i B3 (E15) — total_damage is the whole logged total: rows[] is
    # owner-MERGED, so it already contains pet damage. `pet_damage` is the
    # restatement from pet_ability_damage — "of the total, this much was
    # pet-delivered" — kept for attribution and NEVER added back. dps used to
    # read (total_damage + pet_damage) / dur, which counted every pet's
    # damage twice in the gate's own logged denominator.
    conn.execute("""
        INSERT INTO encounter_performance
          (scope_id, encounter_id, character_id, total_damage, pet_damage,
           total_healing, effective_healing, dps, hps, damage_taken, path)
        SELECT ap.scope_id, cs.encounter_id, ap.character_id,
               SUM(CASE WHEN ap.is_pet = 0 THEN COALESCE(ap.damage_total, 0) ELSE 0 END),
               (SELECT SUM(COALESCE(p.damage_total, 0)) FROM pet_ability_damage p
                 WHERE p.scope_id = ap.scope_id
                   AND p.character_id = ap.character_id),
               SUM(COALESCE(ap.healing_total, 0)),
               SUM(COALESCE(ap.healing_total, 0) - COALESCE(ap.overhealing, 0)),
               NULL, NULL,
               (SELECT SUM(dt.damage) FROM damage_taken_rows dt
                 WHERE dt.scope_id = ap.scope_id
                   AND dt.target_character_id = ap.character_id),
               NULL
        FROM ability_performance ap
        JOIN capture_scopes cs ON cs.scope_id = ap.scope_id
        GROUP BY ap.scope_id, ap.character_id
    """)
    # duration per scope = sum of its encounters' durations
    conn.execute("""
        UPDATE encounter_performance AS ep
        SET dps = CASE WHEN d.dur > 0 THEN ep.total_damage / d.dur END,
            hps = CASE WHEN d.dur > 0 THEN ep.effective_healing / d.dur END
        FROM (SELECT cs.scope_id,
                     (SELECT SUM(e.duration_seconds) FROM encounters e
                       WHERE e.encounter_id IN (
                         SELECT value FROM json_each(cs.encounter_ids_json))) AS dur
              FROM capture_scopes cs) AS d
        WHERE d.scope_id = ep.scope_id
    """)
    # per-parse Path from the abilities rows' character_spec is not stored per
    # row; leaderboard/spec data fills `path` opportunistically in link pass.
    return conn.execute("SELECT COUNT(*) FROM encounter_performance").fetchone()[0]


def compute_damage_share(conn):
    # 🛑 3j B1 — one of the three consumers `AUDIT_3I` §7.1 found summing
    # `ability_performance` with NO `is_pet` filter. On a v0 corpus the
    # denominator counts pet damage twice for every pet-owning character, so
    # every share here is wrong. Refuse rather than compute.
    assert_schema_current(conn, what="compute_damage_share")
    conn.execute("""
        UPDATE ability_performance AS ap
        SET damage_share_pct = 100.0 * ap.damage_total / t.total
        FROM (SELECT scope_id, character_id,
                     SUM(COALESCE(damage_total, 0)) AS total
              FROM ability_performance
              WHERE is_pet = 0
              GROUP BY scope_id, character_id) AS t
        WHERE t.scope_id = ap.scope_id AND t.character_id = ap.character_id
          AND t.total > 0 AND ap.damage_total IS NOT NULL
    """)


def link_performance_snapshots(conn, max_lag_hours=24 * 14):
    """Attach each performance row to a build snapshot, honestly.

    Exact join first: a snapshot captured AT one of the scope's encounters
    (capture_report_id matches) gets lag 0. Fallback: nearest-in-time snapshot
    within `max_lag_hours`, lag recorded. Beyond that, NULL — a guess too big
    to hide.
    """
    perf = conn.execute("""
        SELECT ep.scope_id, ep.character_id, cs.report_id,
               (SELECT MIN(e.occurred_at) FROM encounters e
                 WHERE e.encounter_id IN (SELECT value FROM json_each(cs.encounter_ids_json)))
        FROM encounter_performance ep
        JOIN capture_scopes cs ON cs.scope_id = ep.scope_id
    """).fetchall()
    snaps = {}
    for sid, cid, cap_rep, cap_at, path, role in conn.execute(
            "SELECT snapshot_id, character_id, capture_report_id, captured_at, "
            "path, spec_role FROM character_snapshots"):
        snaps.setdefault(cid, []).append((sid, cap_rep, cap_at, path, role))

    from datetime import datetime

    def parse_ts(ts):
        if not ts:
            return None
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except ValueError:
            return None

    stats = {"exact": 0, "nearest": 0, "unmatched": 0}
    for scope_id, character_id, report_id, occurred_at in perf:
        candidates = snaps.get(character_id) or []
        chosen, lag = None, None
        for sid, cap_rep, cap_at, _path, _role in candidates:
            if cap_rep is not None and cap_rep == report_id:
                chosen, lag = sid, 0.0
                stats["exact"] += 1
                break
        if chosen is None:
            t0 = parse_ts(occurred_at)
            best = None
            if t0 is not None:
                for sid, _cap_rep, cap_at, _path, _role in candidates:
                    t1 = parse_ts(cap_at)
                    if t1 is None:
                        continue
                    h = abs((t1 - t0).total_seconds()) / 3600
                    if best is None or h < best[1]:
                        best = (sid, h)
            if best is not None and best[1] <= max_lag_hours:
                chosen, lag = best
                stats["nearest"] += 1
            else:
                stats["unmatched"] += 1
        row = next((c for c in candidates if c[0] == chosen), None)
        conn.execute(
            "UPDATE encounter_performance SET snapshot_id = ?, snapshot_lag_hours = ?, "
            "path = COALESCE(path, ?), role = COALESCE(role, ?) "
            "WHERE scope_id = ? AND character_id = ?",
            (chosen, lag,
             row[3] if row else None,
             _ROLE_MAP.get(row[4]) if row and row[4] else None,
             scope_id, character_id))
    return stats
