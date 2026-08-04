"""Connection helpers.

Pure per §2.7: the *caller* decides where the database lives (see `config.py`),
these functions only take a path or an already-open connection.
"""
import sqlite3
from contextlib import contextmanager


def connect(db_path, *, row_factory=True, foreign_keys=True) -> sqlite3.Connection:
    """Open a connection. `db_path` may be a str or Path; ':memory:' works for tests."""
    conn = sqlite3.connect(str(db_path))
    if row_factory:
        conn.row_factory = sqlite3.Row
    if foreign_keys:
        conn.execute("PRAGMA foreign_keys = ON")
    return conn


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
