#!/usr/bin/env python3
"""Enforce the pure-logic boundary (ARCHITECTURE §2.7 rule 1) structurally.

The rule is only worth having if it is checked. `core/` must contain no `print()`,
no `argparse`/`sys.argv`, no imports from `cli/`/`ingest/`/`tools/`/`config`, and no
function that opens its own database connection — a web API has to be able to call
the identical function the CLI does, with a connection handed in.

    py tools/audit/check_core_purity.py     # exit 0 clean, 1 with violations

Runs on the AST, not on regex, so a `print` inside a string or a comment does not
trip it. This is an early piece of Phase 1 Task 8's auto-debugger; it lives here so
the boundary is enforced from the session that created it rather than the session
that finally builds the rest of the sweeps.
"""
import ast
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CORE = REPO / "core"

FORBIDDEN_IMPORTS = {"argparse", "config", "cli", "ingest", "tools", "api"}
FORBIDDEN_CALLS = {"print", "input", "exit", "quit"}
# opening a connection inside core/ means the caller cannot control the database,
# which is exactly what breaks a multi-user server later
FORBIDDEN_ATTR_CALLS = {("sqlite3", "connect")}

# The one sanctioned exception, named rather than silently tolerated: this module's
# entire job is opening a connection, and it still takes the path as a parameter -
# it never decides where the database lives. Everything else in core/ must receive
# an already-open connection.
EXEMPT = {"core/db/connection.py": {("sqlite3", "connect")}}


def check_file(path):
    exempt = EXEMPT.get(path.relative_to(REPO).as_posix(), set())
    violations = []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as exc:
        return [(getattr(exc, "lineno", 0), f"syntax error: {exc.msg}")]

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in FORBIDDEN_IMPORTS:
                    violations.append((node.lineno, f"imports '{alias.name}'"))
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if node.level == 0 and root in FORBIDDEN_IMPORTS:
                violations.append((node.lineno, f"imports from '{node.module}'"))
        elif isinstance(node, ast.Call):
            fn = node.func
            if isinstance(fn, ast.Name) and fn.id in FORBIDDEN_CALLS:
                violations.append((node.lineno, f"calls {fn.id}()"))
            elif isinstance(fn, ast.Attribute) and isinstance(fn.value, ast.Name):
                if (fn.value.id, fn.attr) in FORBIDDEN_ATTR_CALLS \
                        and (fn.value.id, fn.attr) not in exempt:
                    violations.append(
                        (node.lineno, f"calls {fn.value.id}.{fn.attr}() - core/ must "
                                      f"take an open connection as a parameter"))
        elif isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name) and node.value.id == "sys" \
                    and node.attr == "argv":
                violations.append((node.lineno, "reads sys.argv"))
    return violations


def main():
    if not CORE.exists():
        print(f"no core/ directory at {CORE}")
        return 0

    files = sorted(CORE.rglob("*.py"))
    total = 0
    for path in files:
        violations = check_file(path)
        if violations:
            rel = path.relative_to(REPO).as_posix()
            for lineno, message in violations:
                print(f"{rel}:{lineno}: {message}")
            total += len(violations)

    print(f"\ncore/ purity: {len(files)} files checked, {total} violation(s)")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
