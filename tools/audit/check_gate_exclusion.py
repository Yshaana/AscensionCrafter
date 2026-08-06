#!/usr/bin/env python3
"""3d F1 — prove the gate EXCLUDES privileged-input characters. Not prose, a test.

    py tools/audit/check_gate_exclusion.py

`calibrate_crawled.candidates()` filters on level, gear, cards and snapshot lag
with — until `3d` — **no source filter at all**. So the moment Elric gets a
`character_snapshots` row from his own ALC capture, he becomes a gate candidate
automatically and the cohort silently becomes 42, with the one
privileged-input character inside it. *"He is an instrument, not a count"*
existed only as a sentence in a handoff.

This test injects exactly that situation into a COPY of the corpus and asserts
the cohort does not move. It is the acceptance test for F1 and is meant to fail
loudly if anyone removes the filter.

🛑 Runs against a temp copy of `builds.db` and never writes to the real one.
"""
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import config  # noqa: E402
from config import BUILDS_DB_PATH  # noqa: E402

config.ensure_utf8_stdout()

sys.path.insert(0, str(Path(__file__).resolve().parent))
import calibrate_crawled as cc  # noqa: E402

FAILURES = []


def check(name, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail else ""))
    if not ok:
        FAILURES.append(name)


def inject_privileged_character(conn):
    """Clone a real cohort member into a NEW character whose snapshot is
    `source='own_capture'` — the shape Elric's ALC-derived snapshot will have.

    Cloning a real member rather than synthesising one matters: it guarantees the
    row passes every OTHER filter (level 60, gear with stats, resolved cards,
    lag 0, a long non-trash encounter), so if it is still absent from the cohort
    the ONLY thing that can have excluded it is the source filter. A synthetic
    row that failed some unrelated check would make this test pass for the wrong
    reason.
    """
    row = conn.execute("""
        SELECT ep.character_id, ep.snapshot_id, ep.scope_id
        FROM encounter_performance ep
        JOIN capture_scopes cs ON cs.scope_id = ep.scope_id
        JOIN encounters e ON e.encounter_id = cs.encounter_id
        JOIN characters c ON c.character_id = ep.character_id
        WHERE ep.snapshot_lag_hours IS NOT NULL AND ep.snapshot_lag_hours <= 0
          AND ep.dps > 100 AND e.is_trash = 0 AND e.duration_seconds >= 20
          AND c.level = 60
          AND EXISTS (SELECT 1 FROM snapshot_gear sg
                      WHERE sg.snapshot_id = ep.snapshot_id
                        AND sg.stats_json IS NOT NULL)
          AND EXISTS (SELECT 1 FROM snapshot_cards sc
                      WHERE sc.snapshot_id = ep.snapshot_id
                        AND sc.spell_id IS NOT NULL)
        ORDER BY ep.character_id LIMIT 1""").fetchone()
    if row is None:
        return None
    src_cid, src_snap, src_scope = row

    # A LOW character_id on purpose. candidates() is ORDER BY character_id
    # LIMIT N, so id 1 lands at the very front of the window — if the exclusion
    # were applied after the SELECT instead of inside it, this row would consume
    # a slot and push a real character out, and the cohort would change size
    # even though the intruder itself never appeared. That is the failure mode
    # this id is chosen to catch.
    new_cid, new_snap = 1, 999999
    conn.execute("INSERT OR REPLACE INTO characters "
                 "(character_id, name, realm, guild, level, primary_role, source,"
                 " first_seen_at, last_seen_at) "
                 "SELECT ?, 'Elric (injected instrument)', realm, guild, level,"
                 " primary_role, 'own_capture', first_seen_at, last_seen_at "
                 "FROM characters WHERE character_id = ?", (new_cid, src_cid))
    cols = [r[1] for r in conn.execute("PRAGMA table_info(character_snapshots)")]
    sel = ", ".join(
        "?" if c in ("snapshot_id", "character_id", "source") else c
        for c in cols)
    conn.execute(
        f"INSERT INTO character_snapshots ({', '.join(cols)}) "
        f"SELECT {sel} FROM character_snapshots WHERE snapshot_id = ?",
        (new_snap, new_cid, "own_capture", src_snap))
    for table, key in (("snapshot_cards", "snapshot_id"),
                       ("snapshot_gear", "snapshot_id")):
        tcols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})")]
        tsel = ", ".join("?" if c == key else c for c in tcols)
        conn.execute(f"INSERT INTO {table} ({', '.join(tcols)}) "
                     f"SELECT {tsel} FROM {table} WHERE {key} = ?",
                     (new_snap, src_snap))
    ecols = [r[1] for r in conn.execute("PRAGMA table_info(encounter_performance)")]
    esel = ", ".join(
        "?" if c in ("character_id", "snapshot_id") else c for c in ecols)
    conn.execute(
        f"INSERT INTO encounter_performance ({', '.join(ecols)}) "
        f"SELECT {esel} FROM encounter_performance "
        f"WHERE character_id = ? AND snapshot_id = ? AND scope_id = ?",
        (new_cid, new_snap, src_cid, src_snap, src_scope))
    conn.commit()
    return new_cid


def main():
    if not BUILDS_DB_PATH.exists():
        print(f"no builds.db at {BUILDS_DB_PATH} — build it with "
              f"`py cli/rebuild.py --with-corpus` (3d E1)", file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / "builds.db"
        shutil.copy(str(BUILDS_DB_PATH), copy)
        conn = sqlite3.connect(str(copy))

        before = cc.candidates(conn, limit=120, max_lag_hours=0)
        before_ids = [r[0] for r in before]
        print(f"baseline cohort: {len(before_ids)} characters")

        injected = inject_privileged_character(conn)
        check("a privileged-input character could be injected at all "
              "(guards this test against passing vacuously)",
              injected is not None,
              "no cohort member to clone — the test proves nothing"
              if injected is None else f"character_id {injected}, "
              f"source='own_capture'")
        if injected is None:
            return 1

        after = cc.candidates(conn, limit=120, max_lag_hours=0)
        after_ids = [r[0] for r in after]

        check("the injected own_capture character is NOT in the cohort",
              injected not in after_ids,
              f"character_id {injected} "
              f"{'LEAKED IN' if injected in after_ids else 'correctly absent'}")
        check("the cohort is byte-identical — the exclusion did not consume a "
              "window slot and displace a real character",
              after_ids == before_ids,
              f"{len(before_ids)} -> {len(after_ids)}; "
              f"added {sorted(set(after_ids) - set(before_ids))}, "
              f"lost {sorted(set(before_ids) - set(after_ids))}")

        # And the converse: without the filter it WOULD have got in. Otherwise
        # this test could pass because the injection was ineffective, not
        # because the exclusion works.
        saved = cc.EXCLUDED_SNAPSHOT_SOURCES
        try:
            cc.EXCLUDED_SNAPSHOT_SOURCES = ()
            unguarded = [r[0] for r in cc.candidates(conn, limit=120,
                                                     max_lag_hours=0)]
        finally:
            cc.EXCLUDED_SNAPSHOT_SOURCES = saved
        check("without the filter the SAME character DOES enter — so the test "
              "is exercising the exclusion, not an unrelated rejection",
              injected in unguarded,
              f"unguarded cohort {'contains' if injected in unguarded else 'does NOT contain'} "
              f"character_id {injected}")

        conn.close()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        return 1
    print("gate exclusion holds: a privileged-input character cannot become a "
          "cohort member, and cannot displace one either")
    return 0


if __name__ == "__main__":
    sys.exit(main())
