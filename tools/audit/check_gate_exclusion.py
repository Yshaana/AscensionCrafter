#!/usr/bin/env python3
"""3d F1 / 3f F1 — prove the gate EXCLUDES privileged-input characters.

    py tools/audit/check_gate_exclusion.py

`calibrate_crawled.candidates()` filters on level, gear, cards and snapshot lag
with — until `3d` — **no source filter at all**. So the moment Elric gets a
`character_snapshots` row from his own ALC capture, he becomes a gate candidate
automatically and the cohort silently grows, with the one privileged-input
character inside it. *"He is an instrument, not a count"* existed only as a
sentence in a handoff. `3f` Block C is the session that finally creates
owner-derived rows in `builds.db`, so this is the guard that has to be alive.

🚨 **REWRITTEN in `3f` F1, not repaired.** `3e` A1 changed `candidates()` from
`(conn, limit, max_lag_hours)` to `(conn, cohort_ids, max_lag_hours)` and this
file still called it with `limit=120`, so it raised `TypeError` before touching
the database and **had not run since**. Fixing the signature would not have
restored it: the old test minted the intruder at `character_id 1` *on purpose*,
because `candidates()` was `ORDER BY character_id LIMIT N` and a low id landed
at the front of the window. Under a **frozen id set** id 1 can never appear
**whatever its `source`** — so the positive assertions would have passed for a
reason unrelated to `EXCLUDED_SNAPSHOT_SOURCES`, and the control arm ("without
the filter the SAME character DOES enter") would have failed.

**The design the frozen cohort needs is the opposite one: contaminate a
character that is ALREADY IN the frozen set.** Then membership is not in
question and `source` is the only variable, so both arms mean what they say:

* with the filter  -> the contaminated member **leaves** the cohort, and is
  reported in `dropped` **naming the source**, never silently omitted;
* without it       -> the same member **returns**, and the cohort is
  byte-identical to the baseline.

🛑 **MUTATION THAT MAKES THIS FAIL:** set
`calibrate_crawled.EXCLUDED_SNAPSHOT_SOURCES = ()`. The contaminated member
stays in the cohort and the two positive checks below go red. *(Verified 3f.)*
A second mutation: move the source filter out of `_completeness_sql`'s WHERE
clause into a post-hoc drop — the exclusion then still works but `dropped`
loses its reason, and the reason check goes red.

🛑 `EXCLUDED_SNAPSHOT_SOURCES` itself is **not touched** by `3f`. This repairs
its guard, never the filter.

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


def contaminate(conn, character_id):
    """Make EVERY qualifying snapshot of a frozen cohort member look like an
    owner capture — the shape Elric's ALC-derived snapshot has.

    This is the `3f` inversion of `3d`'s `inject_privileged_character`. Nothing
    else about the character changes: same gear, same cards, same encounter,
    same lag, same level. So if it disappears from the cohort, `source` is the
    only thing that can have removed it, and if it does NOT disappear the filter
    is dead. A synthetic row failing some unrelated completeness check would
    make this test pass for the wrong reason, which is exactly how the previous
    version would have passed.

    Returns the number of snapshots contaminated.
    """
    snaps = [r[0] for r in conn.execute(
        "SELECT DISTINCT ep.snapshot_id FROM encounter_performance ep "
        "WHERE ep.character_id = ? AND ep.snapshot_id IS NOT NULL",
        (character_id,))]
    conn.executemany(
        "UPDATE character_snapshots SET source = 'own_capture' "
        "WHERE snapshot_id = ?", [(s,) for s in snaps])
    conn.commit()
    return len(snaps)


def main():
    if not BUILDS_DB_PATH.exists():
        print(f"no builds.db at {BUILDS_DB_PATH} — build it with "
              f"`py cli/rebuild.py --with-corpus` (3d E1)", file=sys.stderr)
        return 1

    cohort_ids, spec = cc.load_frozen_cohort()
    print(f"frozen cohort: {len(cohort_ids)} ids "
          f"({spec.get('frozen_at', 'undated')})")

    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / "builds.db"
        shutil.copy(str(BUILDS_DB_PATH), copy)
        conn = sqlite3.connect(str(copy))

        rows, dropped, outside = cc.candidates(conn, cohort_ids, max_lag_hours=0)
        base_ids = [r[0] for r in rows]
        print(f"baseline: {len(base_ids)} of {len(cohort_ids)} frozen members "
              f"qualify, {len(dropped)} dropped, {len(outside)} outside")

        # 🛑 VACUITY GUARD. If no frozen member qualifies there is nothing to
        # contaminate and every assertion below would pass having tested
        # nothing — the failure shape the 3e audit found three times.
        check("there is a qualifying frozen member to contaminate at all "
              "(guards this test against passing vacuously)",
              bool(base_ids),
              f"{len(base_ids)} qualifying"
              if base_ids else "NO frozen member qualifies — test proves nothing")
        if not base_ids:
            return 1

        victim = base_ids[0]
        vname = next(r[1] for r in rows if r[0] == victim)
        n_snaps = contaminate(conn, victim)
        check("the victim is INSIDE the frozen cohort, so membership is not "
              "what is being tested — source is the only variable",
              victim in cohort_ids and n_snaps > 0,
              f"character_id {victim} ({vname}), {n_snaps} snapshot(s) "
              f"-> source='own_capture'")

        after, after_dropped, after_outside = cc.candidates(
            conn, cohort_ids, max_lag_hours=0)
        after_ids = [r[0] for r in after]

        check("a contaminated cohort member is EXCLUDED from the gate",
              victim not in after_ids,
              f"character_id {victim} "
              f"{'LEAKED IN' if victim in after_ids else 'correctly absent'}")

        reasons = {cid: reason for cid, _n, reason in
                   ((d[0], d[1], d[2]) for d in after_dropped)}
        check("...and it is reported as DROPPED, naming the source — never "
              "silently omitted",
              victim in reasons and "source=" in (reasons.get(victim) or ""),
              reasons.get(victim, "NOT IN dropped — the cohort shrank silently"))

        check("no OTHER cohort member moved — the exclusion did not disturb "
              "the rest of the frozen set",
              set(base_ids) - {victim} == set(after_ids),
              f"{len(base_ids)} -> {len(after_ids)}; "
              f"unexpectedly added {sorted(set(after_ids) - set(base_ids))}, "
              f"unexpectedly lost "
              f"{sorted(set(base_ids) - set(after_ids) - {victim})}")

        # An excluded member must not resurface in `outside` either. `outside`
        # is printed as "qualifies but was not scored", which would read as a
        # deliberate omission rather than an exclusion.
        check("the excluded member is not re-reported as 'qualifying but "
              "unscored' — an exclusion is not an omission",
              victim not in after_outside,
              f"outside grew by "
              f"{sorted(set(after_outside) - set(outside))}")

        # The converse arm. Without the filter the SAME character comes back —
        # otherwise this test could be passing because the contamination broke
        # some unrelated completeness condition rather than because the
        # exclusion works.
        saved = cc.EXCLUDED_SNAPSHOT_SOURCES
        try:
            cc.EXCLUDED_SNAPSHOT_SOURCES = ()
            unguarded = [r[0] for r in
                         cc.candidates(conn, cohort_ids, max_lag_hours=0)[0]]
        finally:
            cc.EXCLUDED_SNAPSHOT_SOURCES = saved

        check("without the filter the SAME character DOES enter — so the test "
              "exercises the exclusion, not an unrelated rejection",
              victim in unguarded,
              f"unguarded cohort "
              f"{'contains' if victim in unguarded else 'does NOT contain'} "
              f"character_id {victim}")
        check("...and without the filter the cohort is otherwise identical to "
              "the baseline",
              unguarded == base_ids,
              f"{len(base_ids)} -> {len(unguarded)}")

        conn.close()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        return 1
    print("gate exclusion holds: a privileged-input snapshot removes its "
          "character from the cohort, with a stated reason, and disturbs "
          "nothing else")
    return 0


if __name__ == "__main__":
    sys.exit(main())
