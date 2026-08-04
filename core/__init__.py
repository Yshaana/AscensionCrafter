"""Pure logic layer (ARCHITECTURE §2.7).

Rules, enforced by review and by `tools/audit/check_core_purity.py`:

  * no `print()` — return values, raise, or log via the caller
  * no `argparse` / `sys.argv` — CLIs live in `cli/`
  * no hardcoded or repo-relative paths — `config.py` is off-limits here
  * every function that touches the database takes an open `sqlite3.Connection`
    as its first parameter and never opens one itself

This is what lets a future FastAPI app call the identical functions the CLI does.
"""
