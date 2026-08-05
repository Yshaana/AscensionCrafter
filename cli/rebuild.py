#!/usr/bin/env python3
"""Rebuild the derived database from committed source data.

One command instead of a nine-script chain the caller has to remember in order:

    py cli/rebuild.py

Order is load-bearing. `build_index.py` DROPS and recreates the database, so it
must run first; every seed after it either fills a column or derives a table from
what the previous step wrote.

The DBC step is **excluded by default** — it needs the game client plus a built
StormLib and takes minutes, while everything else runs off plain-text files that
work in any clone. Add it with `--with-dbc` after a client patch:

    py cli/rebuild.py --with-dbc

⚠ `--with-dbc` also REWRITES the two committed extracts in `data/source/dbc/`.
That is the point (they are the only way a session without the client can work),
but it means the step belongs in a commit of its own.
"""
import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from config import DB_PATH  # noqa: E402

# (path, why it is here) — order matters, see the module docstring
CHAIN = [
    ("ingest/export/build_index.py", "catalog + owned cards; DROPS and recreates the db"),
    # early, because seed_class_from_skill_line and the crosswalk both read dbc_*
    ("ingest/dbc/load_extract.py", "dbc_* tables from the committed extract (no client needed)"),
    # needs spell_dbc_raw (above) and spells.hidden_refs (build_index)
    ("ingest/dbc/resolve_numeric_formulas.py",
     "spell_effect_values - magnitudes from NUMERIC dbc fields, never description text"),
    ("ingest/export/seed_borrowed_modifiers.py", "class_origin from 'uses X modifiers' clauses"),
    # after the weaker tooltip tier above, so disagreements are detectable
    ("ingest/export/seed_class_from_skill_line.py", "class_origin from the client's skill lines"),
    ("ingest/export/seed_confirmed.py", "confirmed_facts from the docs"),
    ("ingest/export/seed_epistemics.py",
     "open_questions + retractions + fact_spell_links (T6)"),
    ("ingest/export/seed_synergies.py", "shared_synergies from builds/shared/"),
    ("ingest/export/seed_exclusivity.py", "exclusivity_buckets"),
    ("ingest/export/seed_modifier_links.py", "modifier_links from spells.borrows_from"),
    ("ingest/export/seed_talent_amplifiers.py", "talent_amplifiers"),
    ("ingest/export/seed_spell_flags.py",
     "doc_confirmed_mechanics staging (combat-table facts; surfaces in spell_mechanics)"),
    ("ingest/export/seed_cp_scaling.py", "combo-point scaling types"),
    ("ingest/changelog/ingest_changelog.py", "patches, patch_entries, seasons, server_phases"),
    ("cli/crosswalk.py", "spell_id_crosswalk - needs the dbc_* tables"),
    # T5 before T4: the trigger-attributed spell_effect_values rows written by
    # relationships.py are inputs to the mechanics resolver
    ("cli/relationships.py", "spell_relationships + bounded trigger attribution (T5)"),
    ("cli/mechanics.py", "spell_mechanics resolved truth table + spell_scaling rank keying (T4)"),
    # last, per the phase doc: the auto-debugger sweeps everything above
    ("tools/audit/audit_gaps.py", "auto-debugger integrity sweep (T8)"),
]

DBC_STEP = ("ingest/dbc/build_dbc_index.py",
            "re-extract from the CLIENT; rewrites data/source/dbc/*.json")


def run_step(script, why, extra_args=()):
    print(f"\n=== {script}\n    ({why})")
    started = time.time()
    # PYTHONIOENCODING: several steps print ⚠/✅; when stdout is piped or redirected
    # Python picks cp1252 on Windows and the chain dies at step 1 with a
    # UnicodeEncodeError (pre-existing bug logged in PROGRESS.md, fixed in 1b).
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    result = subprocess.run([sys.executable, str(REPO / script), *extra_args],
                            cwd=REPO, env=env)
    print(f"    -> exit {result.returncode} in {time.time() - started:.1f}s")
    return result.returncode


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--with-dbc", action="store_true",
                    help="also re-extract from the game client (needs client + StormLib)")
    ap.add_argument("--keep-going", action="store_true",
                    help="do not stop at the first failing step")
    args = ap.parse_args()

    chain = list(CHAIN)
    if args.with_dbc:
        # after build_index.py (it reads `spells` to scope itself), and before
        # load_extract.py so the freshly written JSON is what gets loaded
        chain.insert(1, DBC_STEP)

    failed = []
    for script, why in chain:
        if not (REPO / script).exists():
            print(f"\n=== {script}\n    SKIPPED - not present in this checkout")
            continue
        if run_step(script, why) != 0:
            failed.append(script)
            if not args.keep_going:
                print(f"\nSTOPPED at {script}. Fix it, or re-run with --keep-going.")
                return 1

    print(f"\n{'=' * 60}")
    print(f"database: {DB_PATH}")
    if failed:
        print(f"FAILED steps ({len(failed)}): {', '.join(failed)}")
        return 1
    print(f"rebuild OK - {len(chain)} steps")
    return 0


if __name__ == "__main__":
    sys.exit(main())
