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


def snapshot_fingerprint(conn, character_id):
    """Every column of this character's qualifying snapshots that could plausibly
    affect completeness, as one comparable dict. 🆕 `3g` G6.

    Exists so *"`source` is the only variable"* is a MEASURED claim rather than a
    docstring. `contaminate()`'s own docstring says nothing else changes; this
    is what checks it.
    """
    rows = conn.execute(
        "SELECT cs.snapshot_id, cs.source, cs.captured_at, cs.path, "
        "       cs.spec_role, cs.gear_stats_json IS NOT NULL, "
        "       (SELECT COUNT(*) FROM snapshot_gear g "
        "          WHERE g.snapshot_id = cs.snapshot_id), "
        "       (SELECT COUNT(*) FROM snapshot_cards c "
        "          WHERE c.snapshot_id = cs.snapshot_id) "
        "FROM character_snapshots cs "
        "WHERE cs.snapshot_id IN ("
        "  SELECT DISTINCT ep.snapshot_id FROM encounter_performance ep "
        "  WHERE ep.character_id = ? AND ep.snapshot_id IS NOT NULL) "
        "ORDER BY cs.snapshot_id", (character_id,)).fetchall()
    keys = ("snapshot_id", "source", "captured_at", "path", "spec_role",
            "has_gear_stats", "gear_rows", "card_rows")
    return {k: tuple(r[i] for r in rows) for i, k in enumerate(keys)}


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
        # 🆕 3g G6 — DE-TAUTOLOGISED. This asserted `victim in cohort_ids and
        # n_snaps > 0`, and BOTH conjuncts are guaranteed by construction:
        # `victim` is `base_ids[0]` which is drawn from the cohort, and
        # `n_snaps > 0` because `victim` was selected from
        # `encounter_performance` in the first place. It was true for every
        # value of EXCLUDED_SNAPSHOT_SOURCES, every source, every mutation.
        #
        # The real property — the one that makes `source` the ONLY variable —
        # is that `contaminate()` changed the source and changed NOTHING ELSE.
        # That is falsifiable: a contaminate() that also nulled a stat block, or
        # moved a timestamp, would make the exclusion arm below pass for the
        # wrong reason, which is precisely the confound this arm is for.
        before_row = snapshot_fingerprint(conn, victim)
        n_snaps = contaminate(conn, victim)
        after_row = snapshot_fingerprint(conn, victim)
        changed = {k for k in before_row
                   if before_row[k] != after_row.get(k)}
        check("contaminate() changed the SOURCE and nothing else — so `source` "
              "is genuinely the only variable in the arms below",
              changed == {"source"} and n_snaps > 0,
              f"character_id {victim} ({vname}), {n_snaps} snapshot(s); "
              f"fields that changed: {sorted(changed) or 'NONE'}")

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

        # 🆕 3g G6 — DE-TAUTOLOGISED. This asserted `victim not in
        # after_outside`, which is true for every value of
        # EXCLUDED_SNAPSHOT_SOURCES, every source and every mutation:
        # `outside = qualifying - cohort_ids` (calibrate_crawled.py:280) and
        # `victim in cohort_ids` by construction. ⚠ It was made unfalsifiable by
        # the F1 rewrite that moved the victim INSIDE the cohort — the fix and
        # the vacuity have the same cause, which is worth knowing about a
        # rewrite that was otherwise correct.
        #
        # The falsifiable property is that excluding a cohort member does not
        # DISTURB the outside set at all. A `candidates()` that computed
        # `outside` from the post-exclusion population, or that let an excluded
        # member fall through to it, would move this.
        check("excluding a cohort member leaves the 'qualifying but unscored' "
              "set untouched — an exclusion is not an omission, and it is not "
              "a reshuffle either",
              set(after_outside) == set(outside),
              f"outside {len(outside)} -> {len(after_outside)}; "
              f"gained {sorted(set(after_outside) - set(outside))}, "
              f"lost {sorted(set(outside) - set(after_outside))}")

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
