"""Phase 2 T10 — the sim result cache.

Exact-match only. A sim result is cached under a key covering every input that
can change the answer, and anything not in the key is a stale-result bug waiting
to happen.

## 🛑 `data_version` must hash EVERY input the sim depends on

The obvious design hashes `spell_mechanics` and stops. That is wrong, and this
session is the proof: 2c changed `spell_effect_values` (rank-sibling sub-spell
chains), `spell_relationships` (unchanged rows, new inputs), the talent path
(`EffectSpellClassMask`, which lives in `spell_dbc_raw`), and the rating
conversions' source table. A key that watched only `spell_mechanics` would have
served 2b's answers for 2c's model — and the failure is silent, which is the
worst kind: the number looks like a sim result and is a memory of a different
model.

So `data_version()` hashes a row count and a content digest for every table the
sim reads. Adding a new input table means adding it to `SIM_INPUT_TABLES`, and
forgetting to is the one way to reintroduce the bug — hence the deliberate
`sim_inputs_unhashed` warning when a table named there is missing entirely.

## Not built, but designed for

* **iteration top-up** — running 500 more Monte Carlo iterations and merging
  statistically rather than re-running 1,500. `n_iterations` is a key field
  today, so a top-up implementation would relax it to a range rather than
  restructure the table.
* **component-level caching** — two builds sharing ~90% of a board reuse each
  other's per-ability results. `ResolvedAbility` is already cleanly separable,
  so this needs a second table, not a rewrite.
"""
import hashlib
import json
from datetime import datetime, timezone

# Every table the sim reads. Adding a sim input without adding it here is how
# stale results come back.
SIM_INPUT_TABLES = (
    "spells", "spell_scaling", "spell_mechanics", "spell_effect_values",
    "spell_relationships", "spell_dbc_raw", "dbc_gt_tables",
    "dbc_character_advancement", "dbc_spell_rank", "doc_confirmed_mechanics",
)

CACHE_DDL = """
CREATE TABLE IF NOT EXISTS sim_results (
    cache_key     TEXT PRIMARY KEY,
    build_hash    TEXT NOT NULL,
    tier          TEXT NOT NULL,
    content_name  TEXT,
    apl_name      TEXT,
    n_iterations  INTEGER,
    data_version  TEXT NOT NULL,
    patch_id      INTEGER,
    realm         TEXT,
    season        TEXT,
    result_json   TEXT NOT NULL,
    created_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sim_results_build ON sim_results(build_hash);
CREATE INDEX IF NOT EXISTS idx_sim_results_dv ON sim_results(data_version);
"""


def _digest(obj):
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def data_version(conn):
    """`(version, warnings)` — a digest over every table the sim reads.

    Cheap enough to compute per call: it is a `COUNT(*)` plus a digest of the
    table's own schema text, not a scan of the rows. A schema change or a row
    count change both invalidate, which covers every rebuild this project does
    (every ingester replaces its rows wholesale rather than editing in place).
    """
    parts, warnings = {}, []
    for table in SIM_INPUT_TABLES:
        row = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
            (table,)).fetchone()
        if row is None:
            warnings.append(
                f"sim input table {table!r} is MISSING — the cache key cannot "
                "cover it, so a result computed now could be served after that "
                "table appears and changes the answer")
            parts[table] = None
            continue
        n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        parts[table] = [n, hashlib.sha256(
            (row[0] or "").encode("utf-8")).hexdigest()[:12]]
    return _digest(parts)[:16], warnings


def cache_key(*, build_hash, tier, content, apl=None, n_iterations=None,
              data_version_str, patch_id=None, realm=None, season=None):
    """The exact-match key. Every argument is part of the answer."""
    return _digest({
        "build": build_hash, "tier": tier,
        "content": _digest(content),
        "apl": _digest(apl) if apl is not None else None,
        "iterations": n_iterations,
        "data_version": data_version_str,
        "patch": patch_id, "realm": realm, "season": season,
    })


def create_cache_schema(cache_conn):
    """Idempotent. The CALLER opens the connection — `core/` never picks a path
    or opens a database (repo convention, enforced by check_core_purity)."""
    cache_conn.executescript(CACHE_DDL)
    return cache_conn


def get(cache_conn, key):
    row = cache_conn.execute(
        "SELECT result_json FROM sim_results WHERE cache_key = ?",
        (key,)).fetchone()
    return json.loads(row[0]) if row else None


def put(cache_conn, key, result, *, build_hash, tier, data_version_str,
        content_name=None, apl_name=None, n_iterations=None, patch_id=None,
        realm=None, season=None):
    cache_conn.execute(
        "INSERT OR REPLACE INTO sim_results (cache_key, build_hash, tier, "
        "content_name, apl_name, n_iterations, data_version, patch_id, realm, "
        "season, result_json, created_at) VALUES (" + ",".join("?" * 12) + ")",
        (key, build_hash, tier, content_name, apl_name, n_iterations,
         data_version_str, patch_id, realm, season,
         json.dumps(result, default=str),
         datetime.now(timezone.utc).isoformat(timespec="seconds")))
    cache_conn.commit()
    return key


def purge_stale(cache_conn, current_data_version):
    """Drop everything computed against a different data_version.

    Not required for correctness — the key already prevents a stale hit — but it
    keeps the file from accumulating one generation of results per rebuild, and
    a stale row is never useful again: the model that produced it is gone.
    """
    cur = cache_conn.execute(
        "DELETE FROM sim_results WHERE data_version != ?",
        (current_data_version,))
    cache_conn.commit()
    return cur.rowcount
