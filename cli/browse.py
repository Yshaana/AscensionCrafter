#!/usr/bin/env python3
"""Phase 1 T9 — launch Datasette over the derived databases.

    py cli/browse.py            # http://localhost:8001, canned queries included

Browsing convenience only — explicitly NOT the builder app. Datasette is an
approved, pinned dependency (owner decision 2026-08-05); install with
`pip install -r requirements.txt`.
"""
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from config import DATA_DERIVED, DB_PATH, SCOUTED_DB_PATH  # noqa: E402
import config  # noqa: E402

# Piped/redirected stdout defaults to cp1252 on Windows and this file
# prints non-ASCII; without this it dies with UnicodeEncodeError only when
# its output is captured. See config.ensure_utf8_stdout.
config.ensure_utf8_stdout()

METADATA = REPO / "tools" / "browse" / "datasette_metadata.json"


def main():
    if not DB_PATH.exists():
        print("data/derived/ascension.db missing — run: py cli/rebuild.py")
        return 1
    dbs = [str(DB_PATH)]
    if SCOUTED_DB_PATH.exists():
        dbs.append(str(SCOUTED_DB_PATH))
    cmd = [sys.executable, "-m", "datasette", *dbs,
           "--metadata", str(METADATA), "--port", "8001"]
    print("launching:", " ".join(cmd))
    try:
        return subprocess.call(cmd, cwd=str(DATA_DERIVED))
    except FileNotFoundError:
        print("datasette not installed — pip install -r requirements.txt")
        return 1


if __name__ == "__main__":
    sys.exit(main())
