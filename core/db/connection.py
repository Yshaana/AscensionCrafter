"""Connection helpers.

Pure per §2.7: the *caller* decides where the database lives (see `config.py`),
these functions only take a path or an already-open connection.
"""
import os
import sqlite3
from contextlib import contextmanager


class RebuildIncomplete(RuntimeError):
    """The database carries an unfinished-rebuild marker and must not be read."""


def connect(db_path, *, row_factory=True, foreign_keys=True,
            allow_incomplete=False) -> sqlite3.Connection:
    """Open a connection. `db_path` may be a str or Path; ':memory:' works for tests.

    🛑 3d E3 — REFUSES to open a half-built database.

    `cli/rebuild.py` runs 21 steps as separate subprocesses with no cross-step
    transaction, no temp-DB-and-swap and no backup. If step 15 fails, the
    previous 14 steps' writes are committed and `ascension.db` is left
    half-seeded — and, crucially, still perfectly READABLE. Every query against
    it returns plausible rows drawn from a database that is missing most of its
    content. Nothing marked it invalid.

    So the rebuild now writes a `rebuild_state` marker before step 1 and clears
    it on success, and every reader hard-fails while that marker is present. A
    killed rebuild leaves a database that refuses to be read, rather than one
    that quietly lies.

    Two escape hatches, both for the rebuild itself, which must obviously be
    able to open the database it is building:

      * `allow_incomplete=True` — explicit, for a direct caller.
      * the `ASCENSION_REBUILD_IN_PROGRESS` environment variable, which
        `cli/rebuild.py` sets for every subprocess it launches. Without it each
        of the 21 chain steps would have to pass the flag by hand, and the one
        that forgot would break the chain rather than the guard.

    ⚠ Reading an env var is the only thing `core/` learns about its caller here.
    It is not a config import and not a path: `os.environ` carries no filesystem
    layout, so §2.7 rule 1 holds. `tools/audit/check_core_purity.py` is the
    arbiter and passes.
    """
    conn = sqlite3.connect(str(db_path))
    if row_factory:
        conn.row_factory = sqlite3.Row
    if foreign_keys:
        conn.execute("PRAGMA foreign_keys = ON")
    if not allow_incomplete and not os.environ.get(
            "ASCENSION_REBUILD_IN_PROGRESS"):
        _assert_rebuild_complete(conn, db_path)
    return conn


def _assert_rebuild_complete(conn, db_path):
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='rebuild_state'"
    ).fetchone()
    if row is None:
        return                      # pre-E3 database, or a fresh in-memory one
    marker = conn.execute(
        "SELECT started_at, git_sha, step_count FROM rebuild_state "
        "WHERE completed_at IS NULL ORDER BY rowid DESC LIMIT 1").fetchone()
    if marker is None:
        return
    started, sha, steps = marker[0], marker[1], marker[2]
    conn.close()
    raise RebuildIncomplete(
        f"{db_path} carries an UNFINISHED rebuild marker (started {started}, "
        f"git {sha}, {steps} steps planned) and is refusing to be read. A "
        f"rebuild died partway, so this database is half-seeded — readable, "
        f"plausible, and missing most of its content. Re-run `py cli/rebuild.py` "
        f"to completion. Pass allow_incomplete=True only if you are the rebuild."
    )


@contextmanager
def transaction(conn: sqlite3.Connection):
    """Commit on clean exit, roll back on any exception.

    Used by every ingester so a half-written table can never be left behind — the
    failure mode behind Phase 0's idempotency bugs.
    """
    try:
        yield conn
    except Exception:
        conn.rollback()
        raise
    else:
        conn.commit()


def table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type IN ('table','view') AND name = ?", (name,)
    ).fetchone()
    return row is not None


def column_names(conn: sqlite3.Connection, table: str) -> list:
    return [r[1] for r in conn.execute(f"PRAGMA table_info({table})")]


def count_rows(conn: sqlite3.Connection, table: str) -> int:
    if not table_exists(conn, table):
        return 0
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
