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
from datetime import datetime, timezone
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
    ("ingest/export/seed_hand_coefficients.py",
     "tier-3 hand-seeded coefficients on trigger TARGETS (owner decision 2026-08-05)"),
    # AFTER the hand seed, and owning a DIFFERENT source string. Both delete by
    # source before inserting, so sharing one key would make the surviving rows
    # depend on this order — and would flatten a three-source calibration anchor
    # into the bulk tier. Before cli/mechanics.py, which rank-keys spell_scaling.
    ("ingest/ascension_db/load_scraped_coefficients.py",
     "bulk db.ascension.gg coefficients, agree-verdict rows only (recomputed live)"),
    ("ingest/export/seed_predictions.py",
     "predictions ledger (T9) - migrated rows keep their ORIGINAL stamps"),
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

# 3d E1 — the crawl corpus. It targets a DIFFERENT database (builds.db), and the
# gate cohort, the scraper's demand list and pooled inference all depend on it,
# yet it was in no chain and no .bat: every headline number in this project came
# from a manual step on one machine.
#
# 🛑 OPT-IN, NOT UNCONDITIONAL — and this is a DELIBERATE DEVIATION from the task
# as written, made because running it revealed a hazard the task did not
# anticipate. Measured in `3d`:
#
#   Rebuilding builds.db MOVED THE CALIBRATION GATE from 5 of 41 to 4 of 38,
#   with ZERO code changes, purely because the daily crawler had run.
#
# Cause: `calibrate_crawled.candidates()` is `ORDER BY character_id LIMIT 120`,
# and the qualifying population grew from 157 to 180 characters. The limit was
# meant as a cost cap; what it actually does is take a SLIDING WINDOW over a
# growing corpus, keyed on an arbitrary id. Four characters left the cohort and
# four entered, for no reason but their id.
#
# So an unconditional chain step would mean every routine `py cli/rebuild.py`
# silently redefines the gate's population — the opposite of reproducibility,
# and it would have destroyed this session's own §0 invariant. It is opt-in for
# the same reason `--with-dbc` is: it rewrites an input that other results are
# quoted against, so it must be a deliberate act.
#
#     py cli/rebuild.py --with-corpus     # rebuild builds.db too
#
# ✅ FIXED IN `3e` A1, and this note is corrected in `3f` F13 — the text above
# describes the WORLD BEFORE THAT FIX and is kept only because it explains why
# the step is opt-in. `candidates()` is no longer `ORDER BY character_id LIMIT
# N`: the gate's population is the frozen id set committed in
# `predictions/cohort_frozen_3e.json`, and a member that stops qualifying is
# reported as DROPPED WITH ITS REASON, never substituted. Rebuilding the corpus
# therefore can no longer swap cohort members for one another.
#
# 🛑 IT IS STILL OPT-IN, for a narrower but real reason. A frozen member can
# still stop qualifying — its snapshot lag can change, gear can fail to resolve,
# a level can move — and that legitimately shrinks the denominator. The gate
# reports it (`dropped`, and since `3f` F6 `excluded_after_selection` too), so
# it is now visible rather than silent; but a routine rebuild should still not
# be able to change what a gate number means without someone asking for it.
#
# ⚠ WHERE LOG INGESTION SITS (`3f` F13): AFTER this step, never before. It
# writes into the same `builds.db` this step rebuilds from scratch, so a log
# ingested first is destroyed. Its rows carry an EXCLUDED `source`, so they
# cannot enter the gate cohort — `tools/audit/check_gate_exclusion.py` is what
# proves that, and it is worth re-running after any ingestion.
CORPUS_STEP = ("ingest/logs_gg/build_builds_db.py",
               "builds.db - the normalised crawl corpus. ⚠ REBUILDS FROM "
               "SCRATCH: any log-derived rows must be re-ingested AFTER it "
               "(see cli/rebuild.py CORPUS_STEP)")


def mark_rebuild(step_count, *, started):
    """Write or clear the `rebuild_state` marker (3d E3).

    Uses raw sqlite3 rather than `core.db.connection.connect()` for the obvious
    reason: that function now REFUSES to open a database carrying this marker,
    and the rebuild is the one caller that must be able to.
    """
    import sqlite3
    if not DB_PATH.exists():
        return
    sha = None
    try:
        sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO,
                             capture_output=True, text=True,
                             timeout=30).stdout.strip() or None
    except Exception:                                # noqa: BLE001
        pass
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS rebuild_state (
            started_at   TEXT NOT NULL,
            completed_at TEXT,
            git_sha      TEXT,
            step_count   INTEGER
        )""")
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if started:
        conn.execute("DELETE FROM rebuild_state")
        conn.execute("INSERT INTO rebuild_state (started_at, completed_at, "
                     "git_sha, step_count) VALUES (?, NULL, ?, ?)",
                     (now, sha, step_count))
    else:
        conn.execute("UPDATE rebuild_state SET completed_at = ? "
                     "WHERE completed_at IS NULL", (now,))
    conn.commit()
    conn.close()


def run_step(script, why, extra_args=()):
    print(f"\n=== {script}\n    ({why})")
    started = time.time()
    # PYTHONIOENCODING: several steps print ⚠/✅; when stdout is piped or redirected
    # Python picks cp1252 on Windows and the chain dies at step 1 with a
    # UnicodeEncodeError (pre-existing bug logged in PROGRESS.md, fixed in 1b).
    # ASCENSION_REBUILD_IN_PROGRESS: 3d E3. `core.db.connection.connect()`
    # refuses to open a database carrying an uncleared rebuild marker — and the
    # rebuild's own 21 steps are exactly the callers that must be allowed to.
    # Setting it here beats passing allow_incomplete=True in fifteen files, and
    # means a new chain step cannot forget.
    env = {**os.environ, "PYTHONIOENCODING": "utf-8",
           "ASCENSION_REBUILD_IN_PROGRESS": "1"}
    result = subprocess.run([sys.executable, str(REPO / script), *extra_args],
                            cwd=REPO, env=env)
    print(f"    -> exit {result.returncode} in {time.time() - started:.1f}s")
    return result.returncode


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--with-dbc", action="store_true",
                    help="also re-extract from the game client (needs client + StormLib)")
    ap.add_argument("--with-corpus", action="store_true",
                    help="also rebuild builds.db from data/source/crawl/. ⚠ This "
                         "REDEFINES the calibration gate's cohort — see "
                         "CORPUS_STEP in this file. Deliberate act, like --with-dbc")
    ap.add_argument("--keep-going", action="store_true",
                    help="do not stop at the first failing step")
    args = ap.parse_args()

    chain = list(CHAIN)
    if args.with_dbc:
        # after build_index.py (it reads `spells` to scope itself), and before
        # load_extract.py so the freshly written JSON is what gets loaded
        chain.insert(1, DBC_STEP)
    if args.with_corpus:
        # LAST: it targets a different database and reads nothing this chain
        # writes, so its position is free — and putting it last keeps the
        # ascension.db chain's timing and failure modes unchanged.
        chain.append(CORPUS_STEP)
        print("⚠ --with-corpus: builds.db will be rebuilt from data/source/crawl/.")
        print("  The gate's cohort is FROZEN by id "
              "(predictions/cohort_frozen_3e.json), so members can no longer "
              "be swapped for one another by a corpus rebuild — but a frozen "
              "member can still stop QUALIFYING, which shrinks the "
              "denominator. Re-run the gate and re-emit its manifest, and "
              "read `dropped` / `excluded_after_selection` before comparing "
              "the result to an earlier one.")
        print("  ⚠ This rebuilds builds.db FROM SCRATCH. Any log-derived rows "
              "must be re-ingested afterwards.")

    failed = []
    for i, (script, why) in enumerate(chain):
        if not (REPO / script).exists():
            print(f"\n=== {script}\n    SKIPPED - not present in this checkout")
            continue
        rc = run_step(script, why)
        # 3d E3 — mark the database MID-REBUILD as soon as one exists, and clear
        # the mark only on a clean finish. `core.db.connection.connect()` refuses
        # to open a database carrying an uncleared marker.
        #
        # Written AFTER the first step, not before it: `build_index.py` DROPS
        # and recreates the database (it unlinks first), so a marker written
        # earlier would simply be deleted. A failure IN step 1 therefore leaves
        # no marker — and no half-seeded database either, which is the state
        # this guard exists to catch.
        if i == 0 and rc == 0:
            mark_rebuild(len(chain), started=True)
        if rc != 0:
            failed.append(script)
            if not args.keep_going:
                print(f"\nSTOPPED at {script}. Fix it, or re-run with --keep-going.")
                print(f"🛑 {DB_PATH.name} is left MARKED INCOMPLETE and will "
                      f"refuse to be read until a rebuild finishes cleanly. "
                      f"That is deliberate: a half-seeded database is readable "
                      f"and plausible, which is worse than one that errors.")
                return 1

    print(f"\n{'=' * 60}")
    print(f"database: {DB_PATH}")
    if failed:
        print(f"FAILED steps ({len(failed)}): {', '.join(failed)}")
        print(f"🛑 {DB_PATH.name} stays MARKED INCOMPLETE.")
        return 1
    mark_rebuild(len(chain), started=False)
    print(f"rebuild OK - {len(chain)} steps")
    return 0


if __name__ == "__main__":
    sys.exit(main())
