#!/usr/bin/env python3
"""`3f` — the guards that exist to REFUSE, and the mutations that make them stop.

    py tools/audit/check_refusals.py

**Standing rule, adopted 3f (`ADDENDUM_3E_to_3F.md` §4): every check carries a
registered test that makes it fail.** Three of the four fail-open instruments
the `3e` audit found survived review because nobody could name the mutation
that would turn them red — so this file states one per check, in the check's
own text, and the mutations are re-listed in `primer/ENGINE_BUGS.md`'s
check registry.

Covers the refusal paths `3f` F0 / F4 / F5 repaired. They share a shape: each
is a guard whose *silence* is indistinguishable from an all-clear, which is the
single most expensive failure mode this project has (`2e`'s stale stat block
was worth more than every other error combined).

🛑 Runs entirely in-process against synthetic inputs. It makes no network
request, opens no database, and writes nothing.
"""
import ast
import inspect
import json
import re
import sys
import tempfile
import textwrap
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import config  # noqa: E402

config.ensure_utf8_stdout()

FAILURES = []


def check(name, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail else ""))
    if not ok:
        FAILURES.append(name)


# --------------------------------------------------------------------------
# F0 — the 2026-08-07 baseline capture must REFUSE, not traceback
# --------------------------------------------------------------------------
FLIPPED_PAYLOAD = {"phases": [{
    "id": 4, "name": "Phase 2 - Ruins of Ahn Qiraj", "phase_number": 3,
    "is_active": True, "progression_parent_phase_id": None,
    "start_date": "2026-08-08T18:00:00.000Z"}]}


# 🛑 OUT_DIR IS REDIRECTED TO A TEMP DIR, and that is not merely tidiness.
# The first version of this check ran against the real OUT_DIR and APPENDED a
# synthetic "Phase 2" payload into the committed
# data/source/crawl/baseline_phase1/phases.jsonl.gz (770 -> 3476 bytes) — the
# irreplaceable artifact the guard under test exists to protect. It was caught
# by `git status` and reverted. `bp.api_get` is patched too, not just
# `bp.crawler.api_get`, because F0's pre-flight calls the name imported into
# baseline_phase1's own namespace.
_DRIVER = """
import json, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(%r).resolve()))
sys.path.insert(0, str(Path(%r).resolve()))
import baseline_phase1 as bp
payload = json.loads(%r)
bp.crawler.api_get = bp.api_get = lambda path, **kw: (200, payload)
tmp = Path(tempfile.mkdtemp(prefix="check_refusals_"))
bp.OUT_DIR = tmp
sys.argv = ["baseline_phase1.py", "--top", "1"]
try:
    rc = bp.main()
finally:
    # The refusal must leave the output folder EMPTY. Reported on stdout so the
    # parent can assert on it without trusting this process's own exit code.
    print("WROTE_FILES=" + str(sorted(p.name for p in tmp.iterdir())))
sys.exit(rc)
"""


def check_baseline_phase_refusal():
    """`tools/scrapers/baseline_phase1.py` — the one capture that cannot be redone.

    🛑 RUN AS A SUBPROCESS WITH ITS OUTPUT PIPED, ON PURPOSE. The first version
    of this check swapped `sys.stderr` for an `io.StringIO` in-process, and a
    `StringIO` accepts any codepoint — so the encoding assertion below could
    not fail and dropping `ensure_utf8_stdout()` from the script left the check
    green. That is the same vacuity the `3e` audit found in three places, built
    fresh in the file written to stop building it. A pipe is what Task
    Scheduler actually gives the script, so a pipe is what the check has to use.

    MUTATION THAT MAKES THIS FAIL: delete the `except
    season_config.RealmSeasonMismatch` handler around `crawl_phases()` in
    `baseline_phase1.main()`. The exception escapes as a raw traceback, the
    exit code becomes 1, and all three assertions go red. *(Verified 3f.)*

    SECOND MUTATION: remove `config.ensure_utf8_stdout()` from the top of
    `baseline_phase1.py`. Python then selects cp1252 for the piped stderr and
    the 🛑/🚨 banner dies on UnicodeEncodeError PART-WAY THROUGH printing —
    exit 1, truncated message. The banner assertions go red. *(Verified 3f.)*
    """
    import json
    import subprocess

    root = Path(__file__).resolve().parents[2]
    driver = _DRIVER % (str(root), str(root / "tools" / "scrapers"),
                        json.dumps(FLIPPED_PAYLOAD))
    # capture_output gives the child a PIPE, not a console — the exact
    # condition under which Python picks the locale codepage on Windows.
    # `errors="replace"` on OUR side so a mangled child stream still decodes
    # and the check reports a truncated banner rather than raising itself.
    proc = subprocess.run([sys.executable, "-c", driver], cwd=str(root),
                          capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    rc, banner = proc.returncode, proc.stderr
    # 2 is the refusal code the daily crawler already uses and
    # run_crawler_scheduled.bat has a dedicated message for. An UNCAUGHT
    # RealmSeasonMismatch exits 1, so a refusal and a crash are distinguishable
    # from the exit code alone — which is all the .bat can see.
    check("[F0] the pre-flip baseline REFUSES on a phase flip instead of "
          "dying on a traceback",
          rc == 2,
          f"exit {rc}"
          + (" — TRACEBACK, not a refusal" if "Traceback" in banner else ""))
    check("[F0] the refusal says THIS CAPTURE IS NO LONGER POSSIBLE, not "
          "'edit a constant and re-run'",
          "ALREADY HAPPENED" in banner and "no longer" in banner,
          f"{len(banner)} chars of banner; "
          f"names the live phase: {'Ruins of Ahn Qiraj' in banner}")
    check("[F0] the banner survives a NON-CONSOLE stderr (Task Scheduler "
          "redirects; cp1252 would truncate it mid-print)",
          "🛑" in banner and "🚨" in banner,
          "emoji present, so the stream was reconfigured to UTF-8")

    # 🛑 The one that matters most, and the one nobody had. `crawl_phases()`
    # writes the /api/phases snapshot BEFORE it asserts, and `NdjsonWriter`
    # APPENDS — so before F0's pre-flight assert, a post-flip run appended
    # post-flip data into the pre-flip baseline it is named after.
    #
    # MUTATION THAT MAKES THIS FAIL: delete the pre-flight `api_get` +
    # `assert_phase` block in `baseline_phase1.main()` and let `crawl_phases`
    # be the only gate. `phases.jsonl.gz` appears in the temp folder and this
    # goes red. *(Verified 3f.)*
    wrote = [ln for ln in proc.stdout.splitlines() if ln.startswith("WROTE_FILES=")]
    files = wrote[-1].split("=", 1)[1] if wrote else "<driver never reported>"
    check("[F0] the refusal leaves the baseline folder UNTOUCHED — nothing is "
          "written before the phase is verified",
          files == "[]",
          f"files written before refusing: {files}")


# --------------------------------------------------------------------------
# F4 — session_mismatch must never return the all-clear when it cannot check
# --------------------------------------------------------------------------
def _block(exported_at_line):
    """A minimal but REAL AscensionCrafterExport block."""
    return (f"=== Elric - Darkmoon - S10 ===\n"
            f"Level: 60\n"
            f"AttackPower: 134\n"
            f"{exported_at_line}")


def check_session_mismatch_states():
    """`core/builds/stat_block.py :: session_mismatch` — four states, one value.

    `None` is the caller's "stay silent" value (`calibrate_vs_log.py:620-625`).
    Before `3f` F4, a log filename with no parseable timestamp returned `None`
    — INDISTINGUISHABLE from "same session, all clear" — while the function's
    own docstring at `calibrate_vs_log.py:410-412` claimed the opposite.

    MUTATION THAT MAKES THIS FAIL: change the log-side branch back to
    `if log_started_at is None: return None`. The "cannot check" case below
    goes red immediately.
    """
    from core.builds.stat_block import parse_stat_block, session_mismatch

    same = parse_stat_block(_block("ExportedAt: 2026-08-06 19:15:41"))
    log_t = datetime(2026, 8, 6, 19, 16, 56)

    r_same = session_mismatch(same, log_t)
    check("[F4] same session -> silent (None)", r_same is None, repr(r_same))

    r_apart = session_mismatch(same, datetime(2026, 8, 5, 9, 0, 0))
    check("[F4] 34h apart -> a loud mismatch",
          isinstance(r_apart, str) and "HOURS APART" in r_apart,
          (r_apart or "")[:60])

    noblock = parse_stat_block(_block("Spirit: 77"))
    r_noblock = session_mismatch(noblock, log_t)
    check("[F4] block has no ExportedAt -> says it CANNOT be checked",
          isinstance(r_noblock, str) and "CANNOT be checked" in r_noblock,
          (r_noblock or "")[:60])

    # 🛑 THE ONE THAT WAS FAIL-OPEN. `WoWCombatLog.txt`,
    # `06-08-2026-19.16.56 …` (EU day-first) and `2026-08-06 19-16-56 …` all
    # produce log_started_at=None, and every one of them silently disabled the
    # check `2e` proved is worth more than all the others combined.
    r_nolog = session_mismatch(same, None)
    check("[F4] LOG has no parseable timestamp -> says it CANNOT be checked, "
          "and is DISTINGUISHABLE from 'same session'",
          isinstance(r_nolog, str) and r_nolog != r_same,
          (r_nolog or "None — FAIL-OPEN, indistinguishable from all-clear")[:70])


def check_log_started_at_is_total():
    """`calibrate_vs_log.py :: _log_started_at` must not raise on a bad date.

    MUTATION THAT MAKES THIS FAIL: remove the try/except around the `datetime`
    construction. `2026-02-30-19.16.56 WoWCombatLog.txt` matches the regex and
    then raises an UNCAUGHT `ValueError: day is out of range for month`,
    killing the whole calibration run over a filename.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "audit"))
    from calibrate_vs_log import _log_started_at

    cases = [
        ("2026-08-06-19.16.56 WoWCombatLog.txt", datetime(2026, 8, 6, 19, 16, 56)),
        ("2026-08-05-22.42.20_WoWCombatLog.txt", datetime(2026, 8, 5, 22, 42, 20)),
        ("WoWCombatLog.txt", None),
        ("06-08-2026-19.16.56 WoWCombatLog.txt", None),   # EU day-first
        ("2026-02-30-19.16.56 WoWCombatLog.txt", None),   # matches, then invalid
    ]
    ok, detail = True, []
    for name, want in cases:
        try:
            got = _log_started_at(Path(name))
        except Exception as e:                            # noqa: BLE001
            got, ok = f"RAISED {type(e).__name__}", False
        if got != want:
            ok = False
        detail.append(f"{name.split(' ')[0][:22]}->{got}")
    check("[F4] _log_started_at returns None for every unparseable name and "
          "NEVER raises (an impossible date is a filename, not a crash)",
          ok, "; ".join(detail))


# --------------------------------------------------------------------------
# F5 — the --stat-block-only path must reach its own closing note
# --------------------------------------------------------------------------
def check_stat_block_only_closing_note():
    """`calibrate_vs_log.py` closing NOTE — formatted from the RESOLVED stats.

    It used to format `args.ap / args.sp / args.weapon_min / args.weapon_max`,
    which are all `None` on the `--stat-block`-only path, so C1's own headline
    invocation ended in `TypeError: unsupported format string passed to
    NoneType.__format__` — unconditionally, before `return 0`.

    MUTATION THAT MAKES THIS FAIL: point the NOTE back at `args.*`. This check
    passes `stats` with the flags left `None` and the format raises again.
    """
    from calibrate_vs_log import closing_note

    stats = {"ap": 30.0, "sp": 780.0, "weapon_min": 227.7,
             "weapon_max": 253.7, "weapon_speed": 1.66, "notes": []}
    try:
        note = closing_note(stats)
        raised = None
    except Exception as e:                                # noqa: BLE001
        note, raised = "", e
    check("[F5] the closing NOTE renders from the resolved stat block with "
          "every override flag unset",
          raised is None and "780" in note and "227.7" in note,
          f"raised {type(raised).__name__}: {raised}" if raised
          else note.splitlines()[0][:70])


# --------------------------------------------------------------------------
# F6 / F7 — the committed manifest must not contradict itself, or erase a
#           reading it did not take
# --------------------------------------------------------------------------
def _fake_result(cid, name, cov, delta):
    return {"character_id": cid, "name": name, "path": "Intelligence",
            "boss": "b", "delta_pct": delta, "slice_accuracy_pct": 100.0,
            "within_tolerance": True, "modelled": {"modelled_damage_pct": cov}}


def check_manifest_cannot_contradict_itself():
    """`write_gate_manifest` — every frozen member has exactly one fate.

    The defect this replaces was a committed artifact reading `frozen_size: 41,
    still_qualifying: 39, dropped: []` — a cohort reporting a size it did not
    score, with nothing checking the arithmetic, in a file that is the
    project's only auditable record of a gate run.

    MUTATION THAT MAKES THIS FAIL: delete either `raise SystemExit` in
    `write_gate_manifest`'s consistency block. The inconsistent manifest is
    written instead of refused and this goes red. *(Verified 3f.)*
    """
    import calibrate_crawled as cc

    tmp = Path(tempfile.mkdtemp(prefix="check_manifest_")) / "m.json"
    saved = cc.GATE_MANIFEST_PATH
    try:
        cc.GATE_MANIFEST_PATH = tmp
        rows = [_fake_result(1, "A", 60.0, 5.0)]
        # ⚠ 3h A7 — `allow_dirty=True` here is DELIBERATE: this harness runs
        # from whatever tree state the developer has, and these cases test the
        # cohort arithmetic, not provenance. The dirty-tree refusal gets its
        # own case below, where allow_dirty is NOT passed.
        kw = dict(slice_bands={20.0: 64.3}, corpus={}, cohort_ids=[1, 2, 3],
                  dropped=[], outside=[], cohort_spec={}, read_holdout=False,
                  allow_dirty=True,
                  allow_dirty_reason="check_refusals.py test fixture — "
                  "3i E6, a reason is now required alongside the bool")
        # 🛑 BOTH assertions get their own case. The first version of this
        # check only exercised the scoring-loop one, so disabling the
        # completeness-filter assertion left it green — the same
        # one-arm-untested shape as everything else in this file.
        #
        # Case A, the COMPLETENESS filter, constructed so the SECOND assertion
        # is SATISFIED and only the first can fire — otherwise disabling the
        # first leaves this green on the second's back, which is what the first
        # draft of this case did. 3 frozen; 2 still qualifying (1 scored + 1
        # excluded, so assertion 2 balances); 0 dropped. 2 + 0 != 3 — one
        # frozen member has vanished with no fate recorded at all.
        try:
            cc.write_gate_manifest(rows, [], rows, rows, True, True,
                                   n_qualifying=2,
                                   excluded=[(2, "B", "sim error")], **kw)
            refused_a = False
        except SystemExit:
            refused_a = True
        check("[F6] a manifest whose frozen members do not add up "
              "(still_qualifying + dropped != frozen_size) is REFUSED",
              refused_a and not tmp.exists(),
              f"refused={refused_a}, file written={tmp.exists()}")

        # Case B, the SCORING loop: 3 frozen, 1 scored, 0 dropped, 0 excluded
        # -> 2 members vanished between selection and scoring. This is the
        # exact shape of the live defect: `frozen_size: 41, still_qualifying:
        # 39, dropped: []`.
        try:
            cc.write_gate_manifest(rows, [], rows, rows, True, True,
                                   n_qualifying=3, excluded=(), **kw)
            refused = False
        except SystemExit:
            refused = True
        check("[F6] a manifest that scored fewer members than it selected, "
              "without naming the losses, is REFUSED, not written",
              refused and not tmp.exists(),
              f"refused={refused}, file written={tmp.exists()}")

        # And the honest version writes: 3 frozen, 1 scored, 2 named as
        # excluded after selection.
        try:
            cc.write_gate_manifest(
                rows, [], rows, rows, True, True, n_qualifying=3,
                excluded=[(2, "B", "sim error"), (3, "C", "no preset")], **kw)
            wrote, err = tmp.exists(), None
        except SystemExit as e:
            wrote, err = False, e
        check("[F6] ...and the same run WITH the two losses named writes fine "
              "— the assertion tests the arithmetic, not the loss",
              wrote, f"written={wrote}" + (f", refused: {err}" if err else ""))

        # 🆕 3h A3 — the THIRD assertion: criteria_in_force must describe the
        # criteria that produced result. RED MUTATION (run at 3h A3): revert
        # calibrate_crawled.py's `within_tolerance_coverage_floor_pct` to the
        # hardcoded None — this case goes red because the manifest then ships
        # a floor the result block contradicts. GREEN PATH: the key reads
        # SUCCESSOR_COVERAGE_FLOOR_PCT, same constant as
        # `coverage_floor_pct_applied`. Both were run.
        #
        # Both sides read the same module constant, so a live disagreement can
        # only come from one side being hardcoded — which is exactly what the
        # red mutation restores. From here, assert the INVARIANT on the honest
        # run's written artifact: the two keys carry equal values.
        try:
            written = json.loads(tmp.read_text(encoding="utf-8")) if tmp.exists() else None
        except (OSError, ValueError):
            written = None
        if written is None:
            try:
                cc.write_gate_manifest(
                    rows, [], rows, rows, True, True, n_qualifying=3,
                    excluded=[(2, "B", "sim error"), (3, "C", "no preset")], **kw)
                written = json.loads(tmp.read_text(encoding="utf-8"))
            except SystemExit as e:
                # Under the red mutation the writer refuses this write too —
                # report that as the failure rather than dying mid-suite.
                check("[A3] the written manifest's criteria_in_force floor "
                      "EQUALS result.coverage_floor_pct_applied — the manifest "
                      "cannot ship the 3g-audit §3 self-contradiction",
                      False, f"writer refused the honest run: {e}")
                written = None
        if written is not None:
            check("[A3] the written manifest's criteria_in_force floor EQUALS "
                  "result.coverage_floor_pct_applied — the manifest cannot ship "
                  "the 3g-audit §3 self-contradiction",
                  written["criteria_in_force"]["within_tolerance_coverage_floor_pct"]
                  == written["result"]["coverage_floor_pct_applied"],
                  f"criteria={written['criteria_in_force']['within_tolerance_coverage_floor_pct']}, "
                  f"result={written['result']['coverage_floor_pct_applied']}, "
                  f"floor_applied_from={written['criteria_in_force'].get('floor_applied_from')!r}")

        # 🆕 3j A1 — the FOURTH assertion (`AUDIT_3I_ADVERSARIAL` §3): the
        # manifest may not CLAIM the admissibility rule ran when the scoring
        # loop did not run it. `parse_admissibility_rule_applied` was a
        # hardcoded literal `True` with no parameter behind it, so a stamp↔code
        # drift shipped a committed manifest asserting a rule that did not run,
        # with every row silently `not_admissible: False` via `.get()`
        # defaults. Two arms, because a one-way assertion is half a rule.
        #
        # RED MUTATION (RUN 2026-08-07): disable the assertion itself —
        # `if ci["parse_admissibility_rule_applied"] != _rule_ran_on_every_row:`
        # → `if False:`. Arm 1 then reports `refused=False`: the false claim is
        # written. GREEN PATH: the assertion as it stands.
        #
        # 🛑 A NAMED MUTATION THAT DID NOT GO RED, recorded rather than quietly
        # swapped (`3g` G5: *a green path that has only been named is a guess
        # about your own code* — and so is a red one). The first mutation
        # registered here was "restore `parse_admissibility_rule_applied: True`
        # as a literal". It was RUN and both arms stayed **PASS**, because the
        # assertion compares the criteria key against `_rule_ran_on_every_row`,
        # which the writer re-derives from the rows — so it catches a hardcoded
        # literal just as well as a wrong parameter. That is the guard working,
        # and it means the literal is not the load-bearing part of the fix: the
        # ASSERTION is. The `admissibility_applied` parameter remains because
        # the caller stating its own belief is what gives the assertion two
        # independent sides to compare, but it is not what makes this red.
        rows_no_admiss = [_fake_result(1, "A", 60.0, 5.0)]
        for r in rows_no_admiss:
            r.pop("admissibility_computed", None)
        try:
            cc.write_gate_manifest(
                rows_no_admiss, [], rows_no_admiss, rows_no_admiss, True, True,
                n_qualifying=3,
                excluded=[(2, "B", "sim error"), (3, "C", "no preset")],
                admissibility_applied=True, **kw)
            refused_claim = False
        except SystemExit:
            refused_claim = True
        check("[3j-A1] a manifest CLAIMING parse_admissibility_rule_applied "
              "while the scoring loop computed it for 0 rows is REFUSED — "
              "`not_admissible: False` does not distinguish 'the rule cleared "
              "this parse' from 'the rule never ran'",
              refused_claim, f"refused={refused_claim}")

        # ...and the honest pairing writes. This is the arm that stops the
        # assertion being satisfiable by refusing everything.
        rows_with_admiss = [_fake_result(1, "A", 60.0, 5.0)]
        for r in rows_with_admiss:
            r["admissibility_computed"] = True
        try:
            cc.write_gate_manifest(
                rows_with_admiss, [], rows_with_admiss, rows_with_admiss,
                True, True, n_qualifying=3,
                excluded=[(2, "B", "sim error"), (3, "C", "no preset")],
                admissibility_applied=True, **kw)
            wrote_honest = tmp.exists()
            claim = json.loads(tmp.read_text(encoding="utf-8"))[
                "criteria_in_force"]["parse_admissibility_rule_applied"]
        except SystemExit as e:
            wrote_honest, claim = False, f"refused: {e}"
        check("[3j-A1] ...and a run where the loop DID compute it writes, "
              "with the key True — the assertion tests agreement, not the "
              "claim, so it cannot be satisfied by refusing everything",
              wrote_honest and claim is True,
              f"written={wrote_honest}, key={claim!r}")

        # 🆕 3h A7 — a dirty tree REFUSES without --allow-dirty. This harness
        # itself runs from a dirty tree during development; when the tree is
        # actually clean the refusal cannot fire, so the case is skipped with
        # a printed reason rather than reported as exercised.
        import subprocess as sp
        repo = Path(__file__).resolve().parents[2]
        tree_dirty = bool(sp.run(["git", "status", "--porcelain"], cwd=repo,
                                 capture_output=True, text=True,
                                 timeout=30).stdout.strip())
        if tree_dirty:
            tmp.unlink(missing_ok=True)
            kw_no_allow = {**kw, "allow_dirty": False}
            try:
                cc.write_gate_manifest(
                    rows, [], rows, rows, True, True, n_qualifying=3,
                    excluded=[(2, "B", "sim error"), (3, "C", "no preset")],
                    **kw_no_allow)
                refused_dirty = False
            except SystemExit:
                refused_dirty = True
            check("[A7] a DIRTY tree refuses to write the manifest unless "
                  "--allow-dirty is passed — a sha that does not identify the "
                  "code is worse than no record",
                  refused_dirty and not tmp.exists(),
                  f"refused={refused_dirty}, file written={tmp.exists()}")
            check("[A7] ...and the SAME call with allow_dirty records the flag "
                  "in the manifest",
                  bool(written and written.get("dirty_tree_write_allowed_by_flag")),
                  f"dirty_tree_write_allowed_by_flag="
                  f"{written.get('dirty_tree_write_allowed_by_flag') if written else 'no manifest written'}")
            # 🆕 3i E6 (AUDIT_3G / AUDIT_3H) — the REASON, not just the bool,
            # is in the committed record.
            check("[E6] ...and the STATED REASON is recorded verbatim, not "
                  "just the boolean AUDIT_3G/AUDIT_3H flagged as insufficient",
                  bool(written and written.get("dirty_tree_write_allowed_reason")
                       == kw["allow_dirty_reason"]),
                  f"dirty_tree_write_allowed_reason="
                  f"{written.get('dirty_tree_write_allowed_reason') if written else 'no manifest written'!r}")
            # 🆕 3i E6 — allow_dirty=True with NO reason must ALSO refuse.
            # Registered mutation: pass allow_dirty=True, allow_dirty_reason=
            # None — must raise SystemExit rather than silently writing a
            # dirty-tree manifest with no explanation.
            tmp.unlink(missing_ok=True)
            try:
                cc.write_gate_manifest(
                    rows, [], rows, rows, True, True, n_qualifying=3,
                    excluded=[(2, "B", "sim error"), (3, "C", "no preset")],
                    **{**kw, "allow_dirty": True, "allow_dirty_reason": None})
                refused_no_reason = False
            except SystemExit:
                refused_no_reason = True
            check("[E6] allow_dirty=True with NO REASON also refuses — a "
                  "bool alone is not a reason",
                  refused_no_reason and not tmp.exists(),
                  f"refused={refused_no_reason}, file written={tmp.exists()}")
        else:
            print("  [A7] tree is CLEAN — the dirty-tree refusal cannot fire "
                  "from here; exercised only when the harness runs dirty "
                  "(stated, not silently skipped)")
    finally:
        cc.GATE_MANIFEST_PATH = saved


def check_holdout_reading_is_not_erased():
    """A run that does not read the holdout must not destroy the run that did.

    Before `3f`, every gate run without `--read-holdout` rewrote the committed
    manifest's holdout results to "REDACTED" — so `3f`'s own per-commit gate
    reporting would have deleted `3e`'s close-out reading on its first run.

    MUTATION THAT MAKES THIS FAIL: delete the `carried`/`carried_from`
    pre-read block in `write_gate_manifest`. The second write below reports
    REDACTED and this goes red. *(Verified 3f.)*
    """
    import calibrate_crawled as cc

    tmp = Path(tempfile.mkdtemp(prefix="check_holdout_")) / "m.json"
    saved = cc.GATE_MANIFEST_PATH
    try:
        cc.GATE_MANIFEST_PATH = tmp
        rows = [_fake_result(1, "A", 60.0, 5.0)]
        hold = [_fake_result(9, "H", 30.0, -50.0)]
        # ⚠ 3h A7 — allow_dirty=True: these cases test holdout carry-forward,
        # not provenance; the dirty-tree refusal has its own case in
        # check_manifest_cannot_contradict_itself.
        kw = dict(slice_bands={20.0: 64.3}, corpus={}, cohort_ids=[1, 9],
                  dropped=[], outside=[], cohort_spec={}, n_qualifying=2,
                  excluded=(), allow_dirty=True,
                  allow_dirty_reason="check_refusals.py test fixture — "
                  "holdout carry-forward, not provenance")
        cc.write_gate_manifest(rows, hold, rows, rows, True, True,
                               read_holdout=True, **kw)
        first = json.loads(tmp.read_text(encoding="utf-8"))["holdout"]
        check("[F7] a --read-holdout run writes the holdout results",
              isinstance(first.get("results"), list) and first["read"],
              f"{len(first['results'])} result(s)"
              if isinstance(first.get("results"), list) else str(first.get("results")))

        cc.write_gate_manifest(rows, hold, rows, rows, True, True,
                               read_holdout=False, **kw)
        second = json.loads(tmp.read_text(encoding="utf-8"))["holdout"]
        check("[F7] a later run that does NOT read the holdout carries the "
              "reading forward instead of erasing it",
              isinstance(second.get("results"), list)
              and second["results"] == first["results"],
              f"results now: "
              f"{second.get('results') if not isinstance(second.get('results'), list) else str(len(second['results'])) + ' preserved'}")
        check("[F7] ...and the carried-forward reading is STAMPED with the run "
              "it came from, never presented as current",
              bool(second.get("results_carried_forward_from"))
              and second["read"] is False,
              f"read(this run)={second.get('read')}, "
              f"from={(second.get('results_carried_forward_from') or {}).get('git_sha')}")

        # 🛑 IT MUST CHAIN. The first implementation carried forward only from
        # a block with `read: true`, so the reading survived exactly ONE run
        # and the SECOND unread run redacted it after all. Under 3f's
        # per-commit gate reporting that is two runs — the record would have
        # been destroyed the same evening. Caught here, not in review.
        cc.write_gate_manifest(rows, hold, rows, rows, True, True,
                               read_holdout=False, **kw)
        third = json.loads(tmp.read_text(encoding="utf-8"))["holdout"]
        check("[F7] ...and it survives a THIRD run, keeping the ORIGINAL "
              "stamp rather than drifting forward one commit at a time",
              isinstance(third.get("results"), list)
              and third["results"] == first["results"]
              and (third.get("results_carried_forward_from")
                   == second.get("results_carried_forward_from")),
              f"results: "
              f"{'preserved' if third.get('results') == first['results'] else third.get('results')}; "
              f"stamp stable: "
              f"{third.get('results_carried_forward_from') == second.get('results_carried_forward_from')}")
    finally:
        cc.GATE_MANIFEST_PATH = saved


# --------------------------------------------------------------------------
# F8b — a capture resolves to exactly one phase, or to none
# --------------------------------------------------------------------------
# `is_active` mirrors the live payload, re-fetched 2026-08-07: Phase 0 closed,
# Phase 1 and its child both active. `3g` G0's guard reads it, so a fixture
# without it models a payload shape the server does not send.
_PHASES = {"phases": [
    {"id": 1, "name": "Phase 0", "phase_number": 0, "is_active": False,
     "progression_parent_phase_id": None,
     "start_date": "2026-07-24T00:00:00.000Z"},
    {"id": 2, "name": "Phase 1 - Zul'Gurub", "phase_number": 1,
     "is_active": True, "progression_parent_phase_id": None,
     "start_date": "2026-07-31T18:00:00.000Z"},
    # 🛑 phase_number 2, named "Phase 1.1", CHILD of Phase 1. Reading
    # phase_number instead of the parent id says the server is on Phase 2,
    # which is false — PROGRESS.md recorded this trap on 2026-08-04.
    {"id": 3, "name": "Phase 1.1", "phase_number": 2, "is_active": True,
     "progression_parent_phase_id": 2,
     "start_date": "2026-08-03T18:00:00.000Z"},
]}


def check_phase_resolution():
    """`core/builds/phases.py` — derive, or return NULL and say why.

    MUTATION THAT MAKES THIS FAIL: drop `phase_windows`' filter on
    `progression_parent_phase_id`, so child phases become top-level windows.
    "Phase 1.1" splits Phase 1 in two and the 2026-08-04 timestamp below
    resolves to the wrong label. *(Verified 3f.)*

    SECOND MUTATION: drop the `horizon` branch in `resolve_phase`. A capture
    taken after the payload was fetched resolves to the last known phase
    instead of NULL — which is exactly how a POST-2026-08-08 snapshot would
    get silently labelled Phase 1, the failure F8b exists to prevent. The
    horizon case goes red. *(Verified 3f.)*
    """
    from core.builds.phases import phase_windows, resolve_phase

    wins, horizon = phase_windows(_PHASES, "2026-08-06T06:40:10+00:00")
    check("[F8b] only TOP-LEVEL phases become windows — 'Phase 1.1' is a "
          "child and must not split Phase 1",
          [w["label"] for w in wins] == ["Phase 0", "Phase 1 - Zul'Gurub"],
          str([w["label"] for w in wins]))

    cases = [
        ("2026-07-26T12:00:00Z", "Phase 0", "inside the first window"),
        ("2026-07-31T17:59:59Z", "Phase 0", "one second before the boundary"),
        ("2026-07-31T18:00:00Z", "Phase 1 - Zul'Gurub", "on the boundary"),
        ("2026-08-04T09:00:00Z", "Phase 1 - Zul'Gurub",
         "after the CHILD phase started — still Phase 1"),
        ("2026-07-01T00:00:00Z", None, "before any known phase"),
        ("2026-08-09T00:00:00Z", None,
         "AFTER the payload was fetched — the horizon rule"),
        (None, None, "no timestamp at all"),
    ]
    ok, detail = True, []
    for ts, want, why in cases:
        got, reason = resolve_phase(ts, wins, horizon)
        if got != want:
            ok = False
            detail.append(f"{why}: got {got!r}, wanted {want!r}")
        if got is None and not reason:
            ok = False
            detail.append(f"{why}: NULL with no stated reason")
    check("[F8b] every capture resolves to exactly one phase or to NULL WITH "
          "A REASON — never to the nearest phase",
          ok, "; ".join(detail) if detail else f"{len(cases)} cases")

    # The one that matters this week, called out separately because it is the
    # 2026-08-08 case and it is easy to regress into "just use the last phase".
    got, reason = resolve_phase("2026-08-09T00:00:00Z", wins, horizon)
    check("[F8b] a capture LATER than the phases payload is NULL, not "
          "silently labelled with the newest phase the payload knew",
          got is None and "cannot know" in (reason or ""),
          f"{got!r} — {(reason or '')[:70]}")


def check_phase_guard():
    """`3g` G0 — the positive assertion the horizon rule was not.

    RED: delete the `expected_phase_name` branch in `phase_guard()`, or the
    `boundary` branch in `resolve_phase()`, or restore `horizon is not None
    and ts > horizon`. Each turns its own assertion below red.

    GREEN: these go green on the FIX and only on the fix — a payload whose
    active top-level phase matches, with a boundary the payload has reached,
    resolves normally (the last two assertions), so a guard that simply
    refused everything would fail them.
    """
    from core.builds.phases import phase_guard, phase_windows, resolve_phase

    wins, horizon = phase_windows(_PHASES, "2026-08-06T06:40:10+00:00")

    # --- 1. the payload still describes the server this clone expects -------
    refuse, boundary = phase_guard(_PHASES, wins,
                                   expected_phase_name="Phase 1 - Zul'Gurub",
                                   unmodelled_boundary="2026-08-08T00:00:00Z")
    check("[G0] a payload whose active top-level phase is the expected one "
          "does NOT refuse", refuse is None, f"refuse={refuse!r}")

    # The flip, as a top-level record. `assert_phase` catches this one too.
    flipped = {"phases": [dict(p) for p in _PHASES["phases"]]}
    flipped["phases"][1]["name"] = "Phase 2 - Ruins of Ahn'Qiraj"
    refuse_flip, _ = phase_guard(flipped, wins,
                                 expected_phase_name="Phase 1 - Zul'Gurub")
    check("[G0] a payload naming a phase season_config does not expect refuses "
          "EVERY label, not just post-flip ones",
          refuse_flip is not None and "PHASE FLIP" in refuse_flip,
          (refuse_flip or "(no refusal)")[:80])
    got, why = resolve_phase("2026-08-01T00:00:00Z", wins, horizon,
                             refuse_reason=refuse_flip)
    check("[G0] …and the refusal reaches resolve_phase — a capture safely "
          "inside Phase 1 is still NULL while the payload is inconsistent",
          got is None and why == refuse_flip, f"{got!r}")

    # --- 2. the CHILD-phase case: nothing about the payload changes ---------
    # This is the one defence 1 cannot make. The server published its last
    # boundary as a child, which phase_windows drops and assert_phase ignores.
    check("[G0] the declared boundary is ARMED while no window reaches it "
          "(the child-phase case: the payload looks completely normal)",
          boundary is not None and boundary.year == 2026
          and (boundary.month, boundary.day) == (8, 8), repr(boundary))
    got, why = resolve_phase("2026-08-08T12:00:00Z", wins, horizon,
                             boundary=boundary)
    check("[G0] a capture at or after the declared boundary is NULL even "
          "though the payload is consistent and the horizon is far later",
          got is None and "declared phase boundary" in (why or ""),
          f"{got!r} — {(why or '')[:70]}")

    # …and it SELF-RETIRES once the payload catches up.
    caught_up = {"phases": _PHASES["phases"] + [
        {"id": 4, "name": "Phase 2 - Ruins of Ahn'Qiraj", "phase_number": 3,
         "progression_parent_phase_id": None, "is_active": True,
         "start_date": "2026-08-08T00:00:00.000Z"}]}
    wins2, horizon2 = phase_windows(caught_up, "2026-08-09T06:00:00+00:00")
    _, boundary2 = phase_guard(caught_up, wins2,
                               unmodelled_boundary="2026-08-08T00:00:00Z")
    check("[G0] the boundary DISARMS itself once /api/phases carries a window "
          "reaching it — a stale constant costs nothing",
          boundary2 is None, repr(boundary2))
    got, _ = resolve_phase("2026-08-08T12:00:00Z", wins2, horizon2,
                           boundary=boundary2)
    check("[G0] …and the same capture then resolves to the NEW phase, so the "
          "guard cannot be satisfied by refusing everything",
          got == "Phase 2 - Ruins of Ahn'Qiraj", repr(got))

    # --- 3. horizon is None must fail CLOSED --------------------------------
    got, why = resolve_phase("2027-01-01T00:00:00Z", wins, None)
    check("[G0] horizon=None FAILS CLOSED — it used to return Phase 1 for a "
          "timestamp years past anything the payload knew",
          got is None and "no horizon" in (why or "").replace("there is no ",
                                                              "no "),
          f"{got!r} — {(why or '')[:70]}")

    # --- 4. …and reporting that state must not crash (F5's crash class) ----
    # `f"(horizon {None:%Y-%m-%d})"` raises TypeError. build_builds_db.py:192
    # did exactly that, inside F8b's own code, in the session that fixed F5.
    # RED: revert `describe_horizon` to a bare f-string.
    from core.builds.phases import describe_horizon
    try:
        none_desc, real_desc = describe_horizon(None), describe_horizon(horizon)
        raised = False
    except TypeError:
        none_desc = real_desc = None
        raised = True
    check("[G0] describing a None horizon does not raise — the guard that "
          "reports the failure must not be the thing that crashes",
          not raised and none_desc == "UNKNOWN"
          and real_desc.startswith("2026-08-06"),
          f"None->{none_desc!r}, real->{real_desc!r}")


# The live payload shape at 2026-08-07T19:20Z, hours after the Molten Core
# boundary — recorded verbatim from `/api/phases` (locations stripped, nothing
# else changed). TWO active top-level phases, because Zul'Gurub is still open.
_PHASES_MC = {"phases": _PHASES["phases"] + [
    {"id": 4, "name": "Phase 2 - Molten Core / Onyxia", "phase_number": 3,
     "is_active": True, "progression_parent_phase_id": None,
     "start_date": "2026-08-07T18:00:00.000Z"},
]}


def check_phase_additive():
    """`3k` B0 — ACTIVE TOP-LEVEL PHASES ACCUMULATE, and a count is not the
    answer to "what phase is the server on".

    This retires `3g` G0's `len(tops) != 1` predicate. That predicate read the
    real Molten Core payload as *"a phase transition in progress or a schema
    change"* and refused **every** label — permanently, because Zul'Gurub never
    stops being active. Owner decision 2026-08-07: transitions on this server
    are ADDITIVE (raids get added, none removed), so the current phase is the
    latest-STARTING active top-level.

    RED — M50: restore `len(tops) != 1` as a refusal arm in `phase_guard()`
    (and/or in `season_config.assert_phase()`); arms 1, 2 and 4 go red.
    RED — M51: delete the `clashes`/`_overlapping_windows` arm in
    `phase_guard()`; arm 3 goes red. This is the half that proves the
    protection MOVED rather than being deleted.

    GREEN is the fix and only the fix: arm 2 asserts a post-boundary capture
    takes the NEW label, so a guard that shrugged and refused nothing — or one
    that refused everything — fails.
    """
    import season_config as _sc
    from core.builds.phases import (current_top_level, phase_guard,
                                    phase_windows, resolve_phase)

    wins, horizon = phase_windows(_PHASES_MC, "2026-08-07T19:20:51+00:00")
    n_tops = len([p for p in _PHASES_MC["phases"]
                  if p["is_active"] and p["progression_parent_phase_id"] is None])
    refuse, boundary = phase_guard(
        _PHASES_MC, wins,
        expected_phase_name="Phase 2 - Molten Core / Onyxia",
        unmodelled_boundary="2026-08-07T18:00:00Z")

    # --- 1. two actives is NORMAL, and the newest one is the current phase --
    check("[3k-B0] a payload with TWO active top-level phases does NOT refuse "
          "— transitions are additive on this server, so the count grows every "
          "phase and can never mean 'transition in progress'",
          refuse is None and n_tops == 2
          and (current_top_level(_PHASES_MC) or {}).get("name")
          == "Phase 2 - Molten Core / Onyxia",
          f"active top-levels={n_tops}, refuse={refuse!r}, "
          f"current={(current_top_level(_PHASES_MC) or {}).get('name')!r}")

    # --- 2. the green path is the FIX: labels, not silence ------------------
    before, _ = resolve_phase("2026-08-07T16:02:50+00:00", wins, horizon,
                              refuse_reason=refuse, boundary=boundary)
    after, why = resolve_phase("2026-08-07T18:30:00+00:00", wins, horizon,
                               refuse_reason=refuse, boundary=boundary)
    check("[3k-B0] …and the boundary is CROSSED, not straddled: a capture "
          "before 18:00Z is still Zul'Gurub and one after it is Molten Core, "
          "so neither refusing everything nor labelling everything passes",
          before == "Phase 1 - Zul'Gurub"
          and after == "Phase 2 - Molten Core / Onyxia" and boundary is None,
          f"16:02Z->{before!r}, 18:30Z->{after!r} ({(why or '')[:40]}), "
          f"declared boundary self-retired={boundary is None}")

    # --- 3. the protection MOVED — genuine ambiguity still refuses ----------
    # Two top-level phases claiming the SAME start_date. This is what
    # "ambiguous" actually means, and it is the only shape `phase_windows`
    # cannot normalise away.
    tie = {"phases": _PHASES_MC["phases"] + [
        {"id": 5, "name": "Phase 2 - Blackwing Lair", "phase_number": 4,
         "is_active": True, "progression_parent_phase_id": None,
         "start_date": "2026-08-07T18:00:00.000Z"}]}
    tie_wins, _ = phase_windows(tie, "2026-08-07T19:20:51+00:00")
    tie_refuse, _ = phase_guard(
        tie, tie_wins, expected_phase_name="Phase 2 - Molten Core / Onyxia")
    check("[3k-B0] two top-level phases claiming the SAME start_date STILL "
          "refuse every label — the ambiguity protection moved out of the "
          "count and onto the windows, where it can still fire",
          tie_refuse is not None and "same window" in tie_refuse,
          (tie_refuse or "(no refusal)")[:90])

    # --- 4. the crawler-side twin agrees ------------------------------------
    # `season_config.assert_phase` is the tripwire that halts a capture. It
    # died on the SAME arm, so fixing only `core/` would leave the crawler
    # unable to run at all.
    try:
        live_name = _sc.assert_phase(_PHASES_MC).get("name")
        blew_up = None
    except _sc.RealmSeasonMismatch as exc:
        live_name, blew_up = None, str(exc)[:70]
    check("[3k-B0] season_config.assert_phase accepts the same payload and "
          "names Molten Core — the crawler halts on this function, so a fix "
          "in core/ alone leaves the capture dead",
          live_name == "Phase 2 - Molten Core / Onyxia"
          and live_name == _sc.EXPECTED_PHASE_NAME,
          f"assert_phase->{live_name!r}, EXPECTED_PHASE_NAME="
          f"{_sc.EXPECTED_PHASE_NAME!r}" + (f", raised: {blew_up}" if blew_up
                                            else ""))


def check_righteous_vengeance_wiring():
    """`3k` B3 — the derivation that read a key nothing wrote.

    `tiers._add_swing_sources` derives Righteous Vengeance as 30% of the
    rotation's crit damage via `ev.get("crit_damage")`. **No code in the tree
    wrote that key**, so the sum was always 0.0 and RV was modelled as zero for
    every character since `2e` — measured before the fix: 0 sim rows for 61840
    across the whole 35-character cohort, against 9 characters logging it.

    RED — M52: delete the `"crit_damage"` entry from `per_event` in
    `ability_model.expected_cast` (or the `crit_damage_each` breakdown key).
    Arm 1 goes red — it is the exact pre-fix state.
    RED — M53: drop the `holds_rv` gate in `_add_swing_sources`. Arm 2 goes
    red. This is the half that keeps the fix from becoming phantom
    production: populating the key without the gate gives all 35 cohort
    characters an RV row when only 9 log one.

    GREEN is the fix and only the fix: arm 1 needs a NON-ZERO crit damage from
    a real resolved ability, so a stub returning a constant fails arm 2, and a
    gate that refuses everything fails arm 1.
    """
    from core.sim.ability_model import ResolvedAbility

    # A crit-capable event with p_crit > 0 must report crit damage strictly
    # between zero and its own mean-with-crit — that bracket is what makes the
    # arm impossible to satisfy with a constant.
    # 🛑 Read as an AST, not as text. The FIRST draft of this arm substring-
    # matched `'"crit_damage"'` against the source — and passed under its own
    # mutation M52, because the COMMENT introducing the fix quotes the key. A
    # check a comment can satisfy is not a check (M30's lesson, on a new face).
    # The parser sees dict keys and never sees comments.
    def _dict_keys(func):
        tree = ast.parse(textwrap.dedent(inspect.getsource(func)))
        return {k.value for node in ast.walk(tree)
                if isinstance(node, ast.Dict)
                for k in node.keys
                if isinstance(k, ast.Constant) and isinstance(k.value, str)}

    cast_keys = _dict_keys(ResolvedAbility.expected_cast)
    hit_keys = _dict_keys(ResolvedAbility.expected_hit)
    check("[3k-B3] `expected_cast` WRITES the `crit_damage` key that "
          "`tiers.py` has always read — the derivation of Righteous Vengeance "
          "was dead code for every character because nothing produced it",
          "crit_damage" in cast_keys and "crit_damage_each" in hit_keys,
          f"per_event dict keys include crit_damage={'crit_damage' in cast_keys}, "
          f"expected_hit breakdown includes crit_damage_each="
          f"{'crit_damage_each' in hit_keys}")

    # The arithmetic, on the identity the fix is derived from:
    #   mean       = p_land * base * scale * (1 + p_crit*(mult-1))
    #   crit_dmg   = p_land * base * scale *      p_crit*mult
    # so 0 < crit_dmg < mean*mult, and crit_dmg == 0 exactly when p_crit == 0.
    p_land, base, scale, mult = 0.9, 100.0, 1.0, 2.0
    ok, detail = True, []
    for p_crit in (0.0, 0.25, 1.0):
        mean = p_land * base * scale * (1.0 + p_crit * (mult - 1.0))
        crit = p_land * base * scale * p_crit * mult
        if p_crit == 0.0 and crit != 0.0:
            ok, _ = False, detail.append("p_crit=0 gave non-zero crit damage")
        if p_crit > 0.0 and not (0.0 < crit <= mean * mult):
            ok, _ = False, detail.append(f"p_crit={p_crit}: {crit} vs {mean}")
    check("[3k-B3] …and the quantity is the damage dealt BY crits, not the "
          "expected damage of a hit that might crit — zero exactly when "
          "p_crit is zero, and never exceeding mean x crit multiplier",
          ok, "; ".join(detail) if detail else "3 crit rates checked")

    # --- the ownership gate ------------------------------------------------
    # 🛑 Structural, for the same reason as arm 1 — and this one was caught the
    # same way. Substring-matching `"RIGHTEOUS_VENGEANCE_CARD_SPELL_IDS"` and
    # `"holds_rv"` passed under M53, because stubbing `holds_rv = True` leaves
    # the import and the name in place. What has to be true is that the flag is
    # DERIVED, not asserted: at least one assignment to it must come from a
    # real comparison rather than a constant.
    from core.sim import tiers as _tiers
    gate_tree = ast.parse(textwrap.dedent(
        inspect.getsource(_tiers._add_swing_sources)))
    derived, constant = [], []
    for node in ast.walk(gate_tree):
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "holds_rv"
                for t in node.targets):
            # `holds_rv = None` is the legitimate "caller could not say"
            # initialiser and is not a stub; `holds_rv = True` is.
            if isinstance(node.value, ast.Constant):
                if node.value.value is not None:
                    constant.append(repr(node.value.value))
            else:
                derived.append(type(node.value).__name__)
    guards = [n for n in ast.walk(gate_tree)
              if isinstance(n, ast.If)
              and any(isinstance(x, ast.Name) and x.id == "holds_rv"
                      for x in ast.walk(n.test))]
    check("[3k-B3] Righteous Vengeance is GATED on holding the card, and the "
          "flag is DERIVED rather than asserted — populating crit_damage "
          "without a real gate gives all 35 cohort characters an RV row when "
          "only 9 log one, which is phantom production",
          bool(derived) and not constant and len(guards) >= 1,
          f"holds_rv derived from {derived or 'NOTHING'}, "
          f"constant assignments={constant or 'none'}, "
          f"branches gated on it={len(guards)}")

    # …and a caller that CANNOT say must be told so, not assumed to hold it.
    check("[3k-B3] …and a caller passing no build_spec gets a stated UPPER "
          "BOUND, not a silent assumption of ownership",
          "WITHOUT a card-ownership check" in inspect.getsource(
              _tiers._add_swing_sources),
          "unknown-ownership warning present")


_STATUSES = ("LIVE", "HISTORICAL", "SUPERSEDED", "FINDING")


# --------------------------------------------------------------------------
# 3l D2 — the SpellItemEnchantment parse must decode synthetic records exactly
# --------------------------------------------------------------------------
def _enchant_blob(field_count, records, string_block=b"\x00"):
    """A minimal WDBC container: header + fixed-size records + string block."""
    import struct as _s
    record_size = field_count * 4
    packed = b"".join(r.ljust(record_size, b"\x00")[:record_size] for r in records)
    head = _s.pack("<4s4I", b"WDBC", len(records), field_count, record_size,
                   len(string_block))
    return head + packed + string_block


def check_enchant_record_parse():
    """[3l-D2] parse_enchant_record decodes a synthetic client record exactly.

    This is owner-gated-path insurance (`3b`: the extract exporter was broken
    from `2e` to `3b` and nothing noticed, because only the --with-dbc run
    exercises it). The parse core is pure (bytes in, dict out), so it is
    testable on every clone with no client and no StormLib.

    MUTATION THAT MAKES THIS FAIL (red, M54): in `parse_enchant_record`, read
    `amounts_min` from the unsigned slots — `slots[5:8]` instead of
    `slots_i[5:8]`. The fixture's EffectPointsMin is negative (real enchants
    carry negative points, e.g. -armor curses), so a sign regression decodes
    -5 as 4294967291 and the exact-match assertion goes red.
    """
    import struct as _s
    try:
        from ingest.dbc.build_dbc_index import (
            ENCHANT_FIELD_COUNT, load_dbc, parse_enchant_record)
    except Exception as e:                                    # noqa: BLE001
        check("[3l-D2] enchant parse importable without the client", False,
              f"import failed: {e}")
        return

    sb = b"\x00Test Enchant\x00"
    rec = _s.pack("<2I", 23387, 0)                        # id, charges
    rec += _s.pack("<3I", 1, 3, 0)                        # effect types
    rec += _s.pack("<3i", -5, 10, 0)                      # points min (SIGNED)
    rec += _s.pack("<3i", 6, 10, 0)                       # points max
    rec += _s.pack("<3I", 200818, 99999, 0)               # effect args
    rec += _s.pack("<16I", 1, *([0] * 15))                # name locs (enUS=1)
    rec += _s.pack("<I", 0)                               # name flags
    rec += _s.pack("<7I", 0, 1, 0, 0, 0, 0, 60)           # visual..min_level
    dbc = load_dbc(_enchant_blob(ENCHANT_FIELD_COUNT, [rec], sb))
    p = parse_enchant_record(dbc["records"][0], dbc["string_block"],
                             dbc["field_count"])
    got = (p["id"], p["effect_types"], p["amounts_min"], p["amounts_max"],
           p["effect_args"], p["description"], p["min_level"])
    want = (23387, [1, 3, 0], [-5, 10, 0], [6, 10, 0], [200818, 99999, 0],
            "Test Enchant", 60)
    check("[3l-D2] synthetic 38-slot enchant record decodes exactly "
          "(incl. a NEGATIVE points-min)", got == want,
          f"got {got}" if got != want else "")

    # The honest boundary: a non-stock field_count must trust the numeric
    # prefix only — string offsets are layout-dependent and a junk offset must
    # come back as None, never as garbage text read from a wrong slot.
    rec20 = rec[:14 * 4] + _s.pack("<6I", *([7] * 6))     # junk where strings were
    dbc20 = load_dbc(_enchant_blob(20, [rec20], sb))
    p20 = parse_enchant_record(dbc20["records"][0], dbc20["string_block"], 20)
    ok20 = (p20 is not None and p20["amounts_min"] == [-5, 10, 0]
            and p20["description"] is None and p20["min_level"] is None)
    check("[3l-D2] non-stock field_count: numeric prefix decodes, strings and "
          "trailing scalars refuse as None", ok20,
          "" if ok20 else f"desc={p20 and p20['description']!r} "
                          f"min_level={p20 and p20['min_level']!r}")

    p10 = parse_enchant_record(b"\x00" * 40, b"\x00", 10)
    check("[3l-D2] field_count below the numeric prefix returns None, not a "
          "partial guess", p10 is None)


def _status_census(root):
    """Count status lines over one directory's `*.md`. Shared by the `primer/`
    and `predictions/` walks (`3h` A5) so the two cannot drift apart in how
    they classify."""
    files = sorted(p for p in root.glob("*.md"))
    counts = {s: 0 for s in _STATUSES}
    unclassified = []
    for p in files:
        head = p.read_text(encoding="utf-8", errors="replace")[:1200]
        # 🛑 3i E5 (AUDIT_3H §6.4) — the ORIGINAL matcher scanned for the
        # status word ANYWHERE a backtick/bold delimiter touched it in the
        # first 1200 chars, so a line like "see the `LIVE` gate numbers"
        # classified the WHOLE document as `LIVE` — the comment at the old
        # `:687-691` claimed the delimiter prevented this; it only prevented
        # the BARE word, not the word appearing mid-sentence with its own
        # delimiters. Fixed: match a LINE (after stripping a leading `>`
        # blockquote marker) that STARTS with `**`STATUS`` — the convention
        # every status line in this repo actually follows
        # (`> **`LIVE`** — ...`). A status word named in prose, however
        # delimited, no longer counts.
        hit = None
        for ln in head.splitlines():
            s = ln.strip()
            if s.startswith(">"):
                s = s[1:].strip()
            m = re.match(r"\*\*`(" + "|".join(_STATUSES) + r")\b", s)
            if m:
                hit = m.group(1)
                break
        if hit:
            counts[hit] += 1
        else:
            unclassified.append(p.name)
    return files, counts, unclassified


def check_primer_status_census():
    """`3f` F8c + `3g` G9 + `3h` A4/A5 — every `primer/` AND `predictions/`
    file carries a status line, the census is PRINTED rather than typed into a
    document, and `CLAUDE.md`'s pasted copy is ASSERTED against the print.

    MUTATION THAT MAKES THIS FAIL (red): delete the status line from any file in
    `primer/` or `predictions/`, or change one digit of `CLAUDE.md`'s pasted
    census line. GREEN PATH: restore it — which is the fix, because the rule is
    that a document without a status line cannot be cited at all, and a pasted
    census that disagrees with the generated one is the hand-typed-figure
    failure wearing a paste's clothes.

    🛑 **Why this prints a census as well as asserting.** `CLAUDE.md` carried the
    figure `13 / 32 / 0 / 6` typed by hand, and it was wrong within a day of
    being written — two documents landed and nothing recounted. That is the
    standing rule's own failure mode (*a magnitude never appears in a markdown
    file except as generated output*) sitting in the file every session reads
    first. The number now has an owner. ⚠ And generated-then-pasted only bought
    one more day: the census moved TWICE inside `3g` itself (55 → 56 files), so
    `3h` A4 added the assertion that the paste matches the print.

    `3h` A5 — the walk covers `predictions/` too. Four files there carried no
    status line, including `CALIBRATION_TOLERANCE.md`, the file the gate's
    numbers live in. F8c's lifecycle stopped one directory short of the gate.
    """
    repo = Path(__file__).resolve().parents[2]
    files, counts, unclassified = _status_census(repo / "primer")
    census = " / ".join(f"{counts[s]} {s}" for s in _STATUSES)
    census_line = (f"[census] primer/ status lines: {len(files)} files — "
                   f"{census}")
    print(census_line)
    # 🆕 3i E4 (AUDIT_3H §6.4) — `not unclassified` PASSES on an empty
    # directory (an empty list has no unclassified members). Verified:
    # renaming `primer/` yielded `0 files — 0/0/0/0 — PASS`. `len(files) > 0`
    # closes it; `primer/` is never expected to be empty, so this is a
    # tripwire against the directory itself going missing, not a live case.
    check("[F8c] EVERY file in primer/ carries a status line — a document "
          "without one cannot be cited as current truth, so an unclassified "
          "file is invisible rather than merely undocumented",
          len(files) > 0 and not unclassified,
          f"{len(files)} files, {census}"
          + (f"; UNCLASSIFIED: {unclassified}" if unclassified else ""))

    # 3h A5 — the same rule, one directory over, where the gate's numbers live.
    pfiles, pcounts, punclassified = _status_census(repo / "predictions")
    pcensus = " / ".join(f"{pcounts[s]} {s}" for s in _STATUSES)
    print(f"[census] predictions/ status lines: {len(pfiles)} files — "
          f"{pcensus}")
    # 🆕 3i E4 — the SAME fail-open closed here. Verified: renaming
    # `predictions/` yielded `0 files — 0 LIVE / 0 HISTORICAL / 0 SUPERSEDED
    # / 0 FINDING` and PASS, with no anchor comparable to `primer/`'s
    # CLAUDE.md paste to catch it.
    check("[A5] EVERY file in predictions/ carries a status line — F8c's "
          "lifecycle extended to the directory the gate's numbers live in",
          len(pfiles) > 0 and not punclassified,
          f"{len(pfiles)} files, {pcensus}"
          + (f"; UNCLASSIFIED: {punclassified}" if punclassified else ""))

    # 3h A4 — the pasted census in CLAUDE.md must EQUAL the generated one.
    claude_md = (repo / "CLAUDE.md").read_text(encoding="utf-8",
                                               errors="replace")
    pasted = [ln.strip() for ln in claude_md.splitlines()
              if ln.strip().startswith("[census] primer/ status lines:")]
    check("[A4] CLAUDE.md's pasted census line EQUALS the generated one — "
          "generated-once-and-pasted is one document-landing from wrong",
          len(pasted) == 1 and pasted[0] == census_line,
          (f"pasted {pasted[0]!r} vs generated {census_line!r}" if pasted
           else "no pasted census line found in CLAUDE.md"))
    return counts, len(files)


def check_coverage_split_producing_vs_zero():
    """3h B4, repaired 3i E1/E2 — a character whose EVERY sim-keyed ability
    refuses must report `modelled_and_producing_pct == 0.0` and a NON-EMPTY
    named zero list.

    🛑 AUDIT_3H §6.1 — the ORIGINAL "sum" arm asserted
    `producing_pct + keyed_zero_pct == modelled_damage_pct`, and in
    `modelled_damage_share` `keyed_zero = modelled - producing` BY
    SUBTRACTION — so that sum is true of ANY two-way partition, by
    arithmetic, regardless of what `is_producing` computes. Verified: under
    the registered mutation (`is_producing` → `return True`), only 1 of 4
    cases went red and the sum case printed `60.0 + 0.0 vs 60.0` PASS. A
    complementary-partition sum cannot be made falsifiable by tightening it —
    it has to test something ELSE.
    ✅ 3i E1's replacement: `modelled_damage_share`'s `zero_list` (built by
    iterating `per_ability` and filtering on `producing_ids` — REAL per-
    ability sim damage, untouched by `is_producing`) must sum to the SAME
    total as `keyed_but_zero_pct` (built from `rows` via `is_modelled` /
    `is_producing`). These are two INDEPENDENT code paths over the same
    data; a bug in either can make them disagree. Registered mutation
    (RUN 2026-08-07, verified against a live source edit setting
    `is_producing` to `return True` unconditionally): `keyed_but_zero_pct`
    collapses to 0.0 (the mutation touches it) while `zero_list`'s sum still
    reports the real keyed-but-zero share (`producing_ids` does not go
    through `is_producing`) — **RED**, `0.0 != 60.0`. Restored.

    🛑 AUDIT_3H §6.2 — the ORIGINAL "SAME key flips to producing" case used a
    POSITIVE spell id. For a positive id, `is_producing(r)` is DEFINED as
    `r[0] in producing_ids` — literally the same membership test the fixture
    asserts against, so the case cannot discriminate: whatever `is_producing`
    does to a positive-id row, it can only ever restate `producing_ids`.
    Verified: under `is_producing` → `return True`, the case still read
    `60.0 / 0.0` and PASSED — identically the excluded defect's own output.
    ✅ 3i E2's replacement uses a NEGATIVE-id AUTO row instead, which goes
    through `is_producing`'s OTHER branch (`return autos_producing`) — code
    the positive-id path never exercises, and genuinely capable of
    disagreeing with `producing_ids`. Registered mutation (RUN 2026-08-07,
    verified against a live source edit): `autos_producing` forced `False`
    unconditionally — the auto row's real damage (6000, in `producing_ids`
    via `per_ability['auto_mh']['damage'] > 0`) now reads as keyed-but-zero
    instead of producing — **RED**, `producing 0.0 != 60.0`. Restored.

    ⚠ The all-refused character is SYNTHETIC, stated per the work order:
    measured at 3h B over the frozen cohort, all 90 keyed-but-zero entries are
    `zero-casts-allocated` (GCD starvation) and NO cohort character has every
    ability refused. The fixture's refused ability is REAL: 92557 (Void Zone)
    is the corpus's live non-positive-duration sentinel refusal (E14 closure
    box), and its reason string below is the refusal site's own wording.
    """
    import sqlite3
    import calibrate_crawled as cc

    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE ability_performance (scope_id INT, character_id INT, "
        "spell_id INT, spell_name TEXT, damage_total REAL, is_pet INT, "
        "spell_school TEXT)")
    conn.executemany(
        "INSERT INTO ability_performance VALUES (?,?,?,?,?,?,?)",
        [(1, 7, 92557, "Void Zone", 6000.0, 0, "shadow"),
         (1, 7, 111, "Unkeyed Filler", 4000.0, 0, "physical")])
    per_ability = {92557: {
        "name": "Void Zone", "casts": 3.0, "damage": 0.0,
        "mean_per_cast": 0.0, "events": [],
        "unresolved_events": [{
            "event_key": "e0",
            "reason": "Void Zone event e0: REFUSED — spell 92557 states a "
                      "non-positive duration (-0.001s), which is the DBC's "
                      "'no value' sentinel rather than a measurement"}],
    }}
    out = cc.modelled_damage_share(conn, 1, 7, per_ability)
    check("[B4] every-ability-refused -> modelled_and_producing_pct == 0.0",
          out is not None and out["modelled_and_producing_pct"] == 0.0,
          f"producing={out and out['modelled_and_producing_pct']}")
    check("[B4] ...with a NON-EMPTY named zero list carrying the refusal "
          "reason from the refusal site's own wording",
          bool(out and out["keyed_but_zero"]
               and out["keyed_but_zero"][0]["why"] == "refused-sentinel"
               and out["keyed_but_zero"][0]["spell_id"] == 92557),
          f"zero list={out and out['keyed_but_zero']}")
    # 🆕 3i E1 — the NON-tautological cross-check: zero_list (per_ability +
    # producing_ids path) sums to the SAME share as keyed_but_zero_pct
    # (rows + is_modelled/is_producing path). Two independent computations,
    # not one derived from the other by subtraction.
    zero_list_sum = round(sum(z["logged_share_pct"]
                              for z in (out.get("keyed_but_zero") or [])), 1)
    check("[E1] the NAMED zero list's own summed share EQUALS "
          "keyed_but_zero_pct — two INDEPENDENT computations over the same "
          "data, not a subtraction that can't disagree with itself",
          out is not None and abs(zero_list_sum - out["keyed_but_zero_pct"])
          < 0.5,
          f"zero_list sum={zero_list_sum} vs keyed_but_zero_pct="
          f"{out and out['keyed_but_zero_pct']}")

    # 🆕 3i E2 — the AUTO-row producing case: an auto row with real damage
    # must read as producing via `autos_producing` (the branch a positive-id
    # row never exercises), not via `producing_ids` restating itself.
    conn2 = sqlite3.connect(":memory:")
    conn2.execute(
        "CREATE TABLE ability_performance (scope_id INT, character_id INT, "
        "spell_id INT, spell_name TEXT, damage_total REAL, is_pet INT, "
        "spell_school TEXT)")
    # 🆕 3j A5 (`AUDIT_3I_ADVERSARIAL` §8) — THE FIXTURE IS WIDENED so the
    # maximal-producing answer is no longer the correct answer. `3i` E2 fixed
    # the §6.2 defect (a positive-id row can only restate `producing_ids`) by
    # switching to a negative-id auto row, but left a fixture whose ONLY keyed
    # ability produced damage — so `producing` was already at its ceiling and
    # an over-permissive `is_producing` had nowhere to move it. Verified by the
    # auditor: under the 3h-registered mutation `is_producing -> return True`,
    # this arm printed `producing=60.0, zero=0.0` and PASSED, byte-identical to
    # the output AUDIT_3H §6.2 condemned.
    #
    # The added row (333, 2000 damage logged, 0.0 sim damage) is a KEYED
    # ability an over-permissive `is_producing` misclassifies: it belongs in
    # keyed-but-zero, and only a correct predicate puts it there.
    #
    #   correct:              producing 6000/12000 = 50.0%, zero 2000 = 16.7%
    #   is_producing -> True: producing 8000/12000 = 66.7%, zero 0.0%   RED
    #   autos_producing False: producing 0.0%, zero 66.7%               RED
    conn2.executemany(
        "INSERT INTO ability_performance VALUES (?,?,?,?,?,?,?)",
        [(1, 7, -1, "Auto Attack", 6000.0, 0, "physical"),
         (1, 7, 222, "Other", 4000.0, 0, "shadow"),
         (1, 7, 333, "Keyed But Zero", 2000.0, 0, "fire")])
    per_ability_auto = {
        "auto_mh": {
            "name": "Auto attacks", "casts": 3.0, "damage": 6000.0,
            "mean_per_cast": 2000.0, "events": [{"kind": "swing"}],
            "attributed": True, "unresolved_events": []},
        333: {
            "name": "Keyed But Zero", "casts": 0.0, "damage": 0.0,
            "mean_per_cast": 0.0, "events": [], "unresolved_events": []},
    }
    out2 = cc.modelled_damage_share(conn2, 1, 7, per_ability_auto)
    check("[E2] a real-damage AUTO row reads as producing via "
          "autos_producing — the branch a positive-id row cannot exercise, "
          "unlike the ORIGINAL fixture (AUDIT_3H §6.2)",
          out2 is not None and out2["modelled_and_producing_pct"] == 50.0,
          f"producing={out2 and out2['modelled_and_producing_pct']}, "
          f"zero={out2 and out2['keyed_but_zero_pct']}")
    check("[3j-A5] ...and the SAME fixture carries a keyed-but-zero ability, "
          "so the correct answer is NOT the maximal-producing answer — an "
          "over-permissive is_producing now has somewhere wrong to go "
          "(AUDIT_3I §8: the 3i arm was green under its own named mutation)",
          out2 is not None
          and abs(out2["keyed_but_zero_pct"] - 16.7) < 0.05
          and out2["modelled_damage_pct"] == round(
              out2["modelled_and_producing_pct"]
              + out2["keyed_but_zero_pct"], 1),
          f"producing={out2 and out2['modelled_and_producing_pct']}, "
          f"zero={out2 and out2['keyed_but_zero_pct']}, "
          f"modelled={out2 and out2['modelled_damage_pct']}")

    # 🆕 3j A4 (`AUDIT_3I_ADVERSARIAL` §8) — THE AUTO ROWS THE E1 FIXTURE
    # NEVER HAD. `3i` E3 repaired the auto-key hole in the named zero list and
    # the auditor showed the repair had NO CHECK: mutating the repaired line to
    # `if False:` — a full revert — left `check_refusals.py` at 0 FAILURES,
    # because the E1 fixture above contains only positive ids (92557, 111) and
    # no auto row, so it never reaches the repaired path.
    #
    # Case 1: the sim keys autos, produces ZERO on them, and the log DID carry
    # an auto row. The combined 'auto' entry must appear with its REAL logged
    # share — the AUDIT_3H §6.3 defect was reporting 0.0% of exactly the mass
    # it had just counted as keyed-but-zero.
    conn3 = sqlite3.connect(":memory:")
    conn3.execute(
        "CREATE TABLE ability_performance (scope_id INT, character_id INT, "
        "spell_id INT, spell_name TEXT, damage_total REAL, is_pet INT, "
        "spell_school TEXT)")
    conn3.executemany(
        "INSERT INTO ability_performance VALUES (?,?,?,?,?,?,?)",
        [(1, 7, -1, "Auto Attack", 3000.0, 0, "physical"),
         (1, 7, 222, "Other", 7000.0, 0, "shadow")])
    per_ability_zero_auto = {"auto_mh": {
        "name": "Auto attacks", "casts": 0.0, "damage": 0.0,
        "mean_per_cast": 0.0, "events": [], "unresolved_events": []}}
    out3 = cc.modelled_damage_share(conn3, 1, 7, per_ability_zero_auto)
    auto_entries = [z for z in (out3 or {}).get("keyed_but_zero") or []
                    if str(z["spell_id"]).startswith("auto")]
    check("[3j-A4] a zero-producing AUTO key WITH a logged auto row appears "
          "in the named zero list carrying its REAL logged share (30.0%), not "
          "0.0% of the mass it was just counted in",
          len(auto_entries) == 1
          and abs(auto_entries[0]["logged_share_pct"] - 30.0) < 0.05,
          f"auto entries={auto_entries}")
    zero_sum3 = round(sum(z["logged_share_pct"]
                          for z in (out3 or {}).get("keyed_but_zero") or []), 1)
    check("[3j-A4] ...and the E1 cross-check still closes over an AUTO row — "
          "the zero list's own sum equals keyed_but_zero_pct on the negative-id "
          "path too, not just the positive-id one",
          out3 is not None
          and abs(zero_sum3 - out3["keyed_but_zero_pct"]) < 0.5,
          f"zero_list sum={zero_sum3} vs keyed_but_zero_pct="
          f"{out3 and out3['keyed_but_zero_pct']}")

    # Case 2: THE REGRESSION `3i` E3 introduced. Sim keys autos, produces zero,
    # and the log carried NO auto row at all. `3i` guarded the combined entry
    # on `auto_rows_logged` being truthy, so this entry vanished — verified by
    # the auditor across both trees (`eaa7604` -> one entry, HEAD -> `[]`).
    # A 0.0% logged share is a FACT about the entry, not grounds for silence.
    conn4 = sqlite3.connect(":memory:")
    conn4.execute(
        "CREATE TABLE ability_performance (scope_id INT, character_id INT, "
        "spell_id INT, spell_name TEXT, damage_total REAL, is_pet INT, "
        "spell_school TEXT)")
    conn4.executemany(
        "INSERT INTO ability_performance VALUES (?,?,?,?,?,?,?)",
        [(1, 7, 222, "Other", 10000.0, 0, "shadow")])
    out4 = cc.modelled_damage_share(conn4, 1, 7, per_ability_zero_auto)
    auto_entries4 = [z for z in (out4 or {}).get("keyed_but_zero") or []
                     if str(z["spell_id"]).startswith("auto")]
    check("[3j-A4] a zero-producing AUTO key with NO logged auto row is STILL "
          "named, at 0.0% — the 3i E3 repair dropped it entirely, against its "
          "own 'full list, no caps' comment 40 lines above",
          len(auto_entries4) == 1
          and auto_entries4[0]["logged_share_pct"] == 0.0,
          f"auto entries={auto_entries4}")

    # 🆕 3j A4 — the two inline copies of the auto predicate are now ONE.
    # `AUDIT_3I` §8: `is_modelled` inlined its own copy while `is_auto_row`
    # was a second implementation 30 lines later, under a comment asserting
    # they were the same object. Asserted structurally: the source of
    # `modelled_damage_share` must define `is_auto_row` exactly once.
    import inspect
    src = inspect.getsource(cc.modelled_damage_share)
    check("[3j-A4] `is_auto_row` is defined ONCE in modelled_damage_share — "
          "the comment claiming the coverage sums and the zero list share one "
          "predicate is now true, rather than describing two byte-identical "
          "copies 30 lines apart",
          src.count("def is_auto_row(") == 1
          and "is_auto_row(r)" in src.split("def is_modelled(")[1][:200],
          f"definitions={src.count('def is_auto_row(')}, "
          f"is_modelled delegates="
          f"{'is_auto_row(r)' in src.split('def is_modelled(')[1][:200]}")


def check_admissibility_outage_refuses():
    """`3j` Block 0 (`AUDIT_3I_ADVERSARIAL` §2) — an INFRASTRUCTURE fault must
    make the gate refuse to publish, not become 41 identical parse verdicts.

    The chain the audit found, which would have fired on the first crawl on or
    after 2026-08-08 with zero code changes: `phase_guard` refuses the
    `/api/phases` payload → `admissibility_for` passed that straight into
    `resolve_phase` → every member flagged `unresolved phase: …` →
    `within_tolerance = None` for all of them → the gate publishes
    **`0 of 36`**. `CLAUDE.md`'s own rule forbids exactly this: a character may
    be excluded for what its PARSE is, and a payload refusal is not a property
    of anybody's parse.

    MUTATION THAT MAKES THIS FAIL (red): delete either `raise
    AdmissibilityOutage` in `parse_admissibility.assert_publishable`, or
    restore the old passthrough (`refuse_reason=refuse_reason` in
    `admissibility_for`'s `resolve_phase` call). GREEN PATH: the guard as
    written — the gate calls `assert_publishable` before the sim loop and
    again after it, and has no other route to a manifest.

    🛑 The third and fourth arms are the ones that stop this being a guard
    that refuses everything. A refuse-always `assert_publishable` would pass
    arms 1 and 2 and fail 3 and 4, so the correct answer is not the maximally-
    refusing answer — the defect `AUDIT_3H` §6.2 named on the E2 fixture.
    """
    import parse_admissibility as pa

    # Windows/horizon are REAL aware datetimes, so arm 5 exercises
    # `resolve_phase`'s ordinary path rather than tripping over the fixture.
    _tz = timezone.utc
    _windows = [{"label": "Phase 1 - Zul'Gurub",
                 "phase_number": 1,
                 "starts_at": datetime(2026, 7, 31, 18, tzinfo=_tz),
                 "ends_at": None, "open_ended": True}]
    ok_ctx = (_windows, datetime(2026, 8, 6, 6, 40, tzinfo=_tz), None, None)
    bad_ctx = (ok_ctx[0], ok_ctx[1],
               "PHASE FLIP: the payload's active top-level phase is "
               "\"Phase 2 - Ruins of Ahn'Qiraj\", this clone expects "
               "\"Phase 1 - Zul'Gurub\"", None)

    # arm 1 — a refused payload refuses BEFORE any member is looked at
    raised = None
    try:
        pa.assert_publishable(bad_ctx)
    except pa.AdmissibilityOutage as e:
        raised = str(e)
    check("[3j-0] a payload-level phase refusal makes the gate REFUSE to "
          "publish, rather than flagging every member 'unresolved phase' and "
          "reporting the residue as a measurement",
          raised is not None and "INFRASTRUCTURE refusal" in raised,
          f"raised={(raised or 'NOTHING')[:60]!r}")

    # arm 2 — a flag carried by EVERY member is describing the run
    all_same = [{"name": "A", "flags": ["unresolved phase: x"],
                 "not_admissible": True},
                {"name": "B", "flags": ["unresolved phase: x"],
                 "not_admissible": True},
                {"name": "C", "flags": ["unresolved phase: x"],
                 "not_admissible": True}]
    raised2 = None
    try:
        pa.assert_publishable(ok_ctx, all_same)
    except pa.AdmissibilityOutage as e:
        raised2 = str(e)
    check("[3j-0] a cohort in which EVERY member carries the identical "
          "admissibility flag refuses too — the second door into the same "
          "failure, reachable without a payload refusal",
          raised2 is not None and "identical admissibility flag" in raised2,
          f"raised={(raised2 or 'NOTHING')[:60]!r}")

    # arm 3 — the real 3i roster must NOT refuse (3 flagged of 36, all for
    # DIFFERENT reasons). This is the discriminator: a guard that always
    # refuses passes arms 1-2 and fails here.
    real_ish = ([{"name": "Nodding", "flags": ["window 52s < 60s"],
                  "not_admissible": True},
                 {"name": "Boomcat", "flags": ["apm_ratio 0.24 <= 0.5"],
                  "not_admissible": True},
                 {"name": "Deyindra", "flags": ["apm_ratio 0.22 <= 0.5"],
                  "not_admissible": True}]
                + [{"name": f"ok{i}", "flags": [], "not_admissible": False}
                   for i in range(33)])
    refused3 = False
    try:
        pa.assert_publishable(ok_ctx, real_ish)
    except pa.AdmissibilityOutage:
        refused3 = True
    check("[3j-0] ...and the ACTUAL 3i roster (3 of 36 flagged, each for a "
          "different reason) does NOT refuse — the guard discriminates an "
          "outage from a rule doing its job",
          not refused3, "published, as it must")

    # arm 4 — every member flagged, but for DIFFERENT reasons, still refuses:
    # a rule that removes 100% of the cohort has measured nothing.
    all_flagged_differently = [
        {"name": "A", "flags": ["window 52s < 60s"], "not_admissible": True},
        {"name": "B", "flags": ["apm_ratio 0.24 <= 0.5"],
         "not_admissible": True}]
    raised4 = None
    try:
        pa.assert_publishable(ok_ctx, all_flagged_differently)
    except pa.AdmissibilityOutage as e:
        raised4 = str(e)
    check("[3j-0] a cohort where every member is flagged for a DIFFERENT "
          "reason still refuses — no shared flag, but the number would be "
          "computed over nobody",
          raised4 is not None and "removed the entire cohort" in raised4,
          f"raised={(raised4 or 'NOTHING')[:60]!r}")

    # arm 5 — predicate 4 is SUPPRESSED under a payload refusal, so the flag
    # never reaches a member in the first place. Exercised through the real
    # `admissibility_for` against synthetic tables (no corpus is opened).
    import sqlite3
    bdb = sqlite3.connect(":memory:")
    bdb.executescript(
        "CREATE TABLE snapshot_cards (snapshot_id INT, spell_id INT);"
        "CREATE TABLE ability_performance (scope_id INT, character_id INT, "
        "  casts REAL, is_pet INT);"
        "CREATE TABLE capture_scopes (scope_id INT, encounter_id INT, "
        "  encounter_ids_json TEXT);"
        "CREATE TABLE encounters (encounter_id INT, duration_seconds REAL, "
        "  is_trash INT);"
        "CREATE TABLE encounter_performance (character_id INT, scope_id INT, "
        "  deaths INT);"
        "CREATE TABLE character_snapshots (snapshot_id INT, captured_at TEXT);"
        "INSERT INTO character_snapshots VALUES (1, '2026-08-05T00:00:00Z');"
        "INSERT INTO capture_scopes VALUES (1, 10, NULL);"
        "INSERT INTO encounters VALUES (10, 300.0, 0);")
    asc = sqlite3.connect(":memory:")
    asc.executescript(
        "CREATE TABLE spell_dbc_raw (id INT, casting_time_index INT, "
        "  effect_json TEXT);"
        "CREATE TABLE dbc_spellcasttimes (id INT, base INT);")
    row = pa.admissibility_for(
        bdb, asc, bad_ctx, character_id=7, character_name="X",
        snapshot_id=1, scope_id=1, window_s=300.0, snapshot_lag_hours=0.0)
    check("[3j-0] under a refused payload, `admissibility_for` reports the "
          "refusal as `phase_payload_refusal` and adds NO 'unresolved phase' "
          "flag — the passthrough that turned one outage into 41 parse "
          "verdicts is gone",
          row["phase_payload_refusal"] is not None
          and not any("unresolved phase" in f for f in row["flags"]),
          f"payload_refusal set={row['phase_payload_refusal'] is not None}, "
          f"flags={row['flags']}")


def check_comparator_can_add_a_flag():
    """`3j` A2 (`AUDIT_3I_ADVERSARIAL` §4) — the D5 comparator filters tested in
    the direction nobody tested: can they move a character **INTO** a flag?

    The audit's structural objection: *"each arm can only remove comparators,
    moving a character toward `len(apms) < 2` → refused → admissible… No arm of
    the change can add a flag. Nothing checked that."* The first half is true of
    the escape hatch. **The claim is false of the median**, and this fixture is
    the counterexample, worked out and registered in
    `predictions/prereg_3j_comparator.md` P3 BEFORE it was run.

    Removing **low-APM** comparators RAISES the comparator median, which LOWERS
    the tested ratio `scope_apm / median`, which can push a character BELOW
    `APM_RATIO_BOUND`. Registered numbers: tested scope 8 APM; qualifying
    comparators 18 and 20 APM; two sub-60s comparators at 2 and 3 APM.

        unfiltered  median([2, 3, 18, 20]) = 10.5  ->  8/10.5 = 0.76  admissible
        filtered    median([18, 20])       = 19.0  ->  8/19.0 = 0.42  FLAGGED

    So the filters are not one-way, and the gate's one-way structure was an
    artifact of the cohort, not of the rule.

    MUTATION THAT MAKES THIS FAIL (red): delete the `dur < MIN_PARSE_SECONDS`
    filter from `apm_ratio()` — the two 30s comparators re-enter, the median
    falls back to 10.5, the ratio returns to 0.76 and the "filtered" arm reads
    admissible. GREEN PATH: the filter as written. Both run.

    🛑 The second arm is the one that stops this being satisfiable by a filter
    that removes everything: with the sub-60s scopes gone the character must
    still have ≥ 2 qualifying comparators and a real ratio, not `None`.
    """
    import sqlite3
    import parse_admissibility as pa

    # scope 1 = under test (8 APM over 120s = 16 casts)
    # scopes 2,3 = qualifying comparators, 120s, 18 and 20 APM
    # scopes 4,5 = sub-60s comparators, 30s, 2 and 3 APM  <- the low-APM pair
    bdb = sqlite3.connect(":memory:")
    bdb.executescript(
        "CREATE TABLE ability_performance (scope_id INT, character_id INT, "
        "  casts REAL, is_pet INT);"
        "CREATE TABLE capture_scopes (scope_id INT, encounter_id INT, "
        "  encounter_ids_json TEXT);"
        "CREATE TABLE encounters (encounter_id INT, duration_seconds REAL, "
        "  is_trash INT);")
    for scope, enc, dur, apm in ((1, 101, 120.0, 8.0), (2, 102, 120.0, 18.0),
                                 (3, 103, 120.0, 20.0), (4, 104, 30.0, 2.0),
                                 (5, 105, 30.0, 3.0)):
        bdb.execute("INSERT INTO capture_scopes VALUES (?,?,NULL)", (scope, enc))
        bdb.execute("INSERT INTO encounters VALUES (?,?,0)", (enc, dur))
        bdb.execute("INSERT INTO ability_performance VALUES (?,?,?,0)",
                    (scope, 7, apm * dur / 60.0))
    bdb.commit()

    filtered = pa.apm_ratio(bdb, 7, 1, n_cast_time_entries=0)
    check("[3j-A2] the D5 comparator filters can move a character INTO a "
          "flag, not only out — removing LOW-APM comparators raises the "
          "median and lowers the tested ratio (AUDIT_3I §4's 'no arm of the "
          "change can add a flag' is false of the median)",
          filtered["ratio"] is not None
          and abs(filtered["ratio"] - 8.0 / 19.0) < 0.01
          and filtered["ratio"] <= pa.APM_RATIO_BOUND,
          f"filtered ratio={filtered['ratio'] and round(filtered['ratio'], 3)} "
          f"vs bound {pa.APM_RATIO_BOUND}, comparators="
          f"{filtered['other_scope_apms']}")

    check("[3j-A2] ...and it does so with a REAL ratio, not by refusing — the "
          "filters left 2 qualifying comparators, so this is the median moving, "
          "not the < 2-comparator escape hatch",
          len(filtered["other_scope_apms"]) == 2
          and filtered["comparator_median"] is not None,
          f"n_qualifying={len(filtered['other_scope_apms'])}, "
          f"median={filtered['comparator_median']}, "
          f"excluded={filtered['n_comparator_scopes_excluded']}")


def check_null_spell_id_cannot_escape_dedupe():
    """`3j` B3 (`AUDIT_3I_ADVERSARIAL` §7.5) — a row whose `spell_id` will not
    decode must not escape `INSERT OR REPLACE`.

    SQLite permits NULLs in a rowid table's PRIMARY KEY columns, so
    `_int_or_none(spell_id) -> None` made a row un-deduplicatable: re-ingesting
    the same record appended it again, straight into `total_damage -> dps ->`
    the gate. Reachable — `spell_id` is a string field in the source payload
    and 5 report ids (79, 104, 105, 106, 107) appear twice across the committed
    crawl days.

    ⚠ MEASURED BEFORE FIXING, per the work order's own instruction: the real
    corpus carries **0 of 291,320** such rows in `ability_performance` and
    **0 of 22,427** in `pet_ability_damage`. So this closes a latent route
    rather than correcting a live inflation, and it CANNOT move the gate —
    there is nothing to de-duplicate. Had the count been non-zero, the work
    order says it would have been a finding and a pre-registered gate move for
    a later session, not a fix here.

    MUTATION THAT MAKES THIS FAIL (red, RUN 2026-08-07): point `_spell_key` at
    `_int_or_none`, restoring the NULL. Three ingests of one record then
    produce 3 rows and 3000 damage — the auditor's measurement, reproduced.
    GREEN PATH: `_spell_key` as written, 1 row and 1000 damage.
    """
    import sqlite3
    from core.builds import corpus

    rec = {"realm": "Darkmoon", "season": "S10",
           "captured_at": "2026-08-01T00:00:00Z", "report_id": 79,
           "scope": "boss_single", "encounter_ids": [1],
           "payload": {"rows": [{"character_type": "player",
                                 "character_id": 7, "character_name": "X",
                                 "spell_id": "not-an-int",
                                 "spell_name": "Mystery",
                                 "total_damage": 1000.0}]}}
    conn = sqlite3.connect(":memory:")
    corpus.init_schema(conn)
    for _ in range(3):
        corpus.ingest_abilities_record(conn, dict(rec))
    n, dmg = conn.execute(
        "SELECT COUNT(*), COALESCE(SUM(damage_total), 0) "
        "FROM ability_performance").fetchone()
    sids = [r[0] for r in conn.execute(
        "SELECT DISTINCT spell_id FROM ability_performance")]
    check("[3j-B3] three ingests of ONE record with an undecodable spell_id "
          "produce ONE row, not three — a NULL in a rowid table's PRIMARY KEY "
          "escapes INSERT OR REPLACE and re-ingests as a duplicate",
          n == 1 and abs(dmg - 1000.0) < 0.01,
          f"rows={n}, damage={dmg:.0f} (the NULL route gives 3 / 3000)")
    check("[3j-B3] ...and the row is VISIBLE as unresolved rather than NULL, "
          "so it can be counted — the sentinel is outside both Spell.dbc space "
          "and the log's auto-attack ids, so it cannot collide",
          sids == [corpus.UNRESOLVED_SPELL_ID],
          f"spell_ids={sids}, sentinel={corpus.UNRESOLVED_SPELL_ID}")


def check_corpus_schema_gate():
    """`3j` B1 (`AUDIT_3I_ADVERSARIAL` §7.1) — a pre-`3i` corpus is migrated or
    refused, never quietly read.

    `init_schema` was `CREATE TABLE IF NOT EXISTS` only, `PRAGMA user_version`
    was 0 and never set, and no backfill existed — so a retained pre-`3i`
    `builds.db` kept its doubled `is_pet=1` rows while `pet_damage` silently
    became NULL. Three consumers summed it with no `is_pet` filter
    (`compute_damage_share`, `demand_list`, `build_extract_scope_request`).
    The only thing preventing a wrong answer was `build_builds_db.py` unlinking
    the DB on every build — a habit, not a guard.

    MUTATION THAT MAKES THIS FAIL (red, RUN 2026-08-07): replace the `raise` in
    `assert_schema_current` with `if False:`. A v0 database is then accepted by
    every consumer. GREEN PATH: the raise, plus `migrate_schema()` for callers
    that want repair instead of refusal — both reachable, neither a stub.
    """
    import sqlite3
    from core.builds import corpus

    fresh = sqlite3.connect(":memory:")
    corpus.init_schema(fresh)
    check("[3j-B1] a freshly initialised corpus declares its schema version — "
          "`init_schema` used to be CREATE-TABLE-only, leaving user_version 0 "
          "and every DB indistinguishable from a pre-E15 one",
          corpus.schema_version(fresh) == corpus.CORPUS_SCHEMA_VERSION,
          f"user_version={corpus.schema_version(fresh)}, expected "
          f"{corpus.CORPUS_SCHEMA_VERSION}")

    legacy = sqlite3.connect(":memory:")
    corpus.init_schema(legacy)
    legacy.execute("PRAGMA user_version = 0")
    refused = None
    try:
        corpus.assert_schema_current(legacy, what="check fixture")
    except corpus.CorpusSchemaTooOld as e:
        refused = str(e)
    check("[3j-B1] a v0 (pre-E15) corpus is REFUSED, not read — every SUM over "
          "its ability_performance double-counts pet damage",
          refused is not None and "user_version is 0" in refused,
          f"refused={(refused or 'NOTHING').splitlines()[0][:70]!r}")

    # ...and the migration is a real path, not a stub: it deletes the
    # restatement rows and stamps the version, and a migrated DB then passes.
    legacy.execute(
        "INSERT INTO capture_scopes (scope_id, report_id, scope, "
        "encounter_ids_json) VALUES (1, 79, 'boss_single', '[1]')")
    legacy.executemany(
        "INSERT INTO ability_performance (scope_id, character_id, spell_id, "
        "spell_name, is_pet, damage_total) VALUES (?,?,?,?,?,?)",
        [(1, 7, 555, "Pet Spell", 0, 1000.0),
         (1, 7, 555, "Pet Spell", 1, 1000.0)])
    legacy.execute("PRAGMA user_version = 0")
    frm, to, note = corpus.migrate_schema(legacy)
    remaining = legacy.execute(
        "SELECT COUNT(*) FROM ability_performance").fetchone()[0]
    passed_after = True
    try:
        corpus.assert_schema_current(legacy, what="check fixture")
    except corpus.CorpusSchemaTooOld:
        passed_after = False
    check("[3j-B1] ...and `migrate_schema` is a REACHABLE green path, not a "
          "stub: it deletes the is_pet=1 restatement, stamps the version, and "
          "the same DB then passes the guard",
          frm == 0 and to == corpus.CORPUS_SCHEMA_VERSION
          and remaining == 1 and passed_after,
          f"v{frm}->v{to}, rows left={remaining} (was 2), passes after="
          f"{passed_after}; {note}")


def check_band_table_matches_manifest():
    """`3j` C3 — `CALIBRATION_TOLERANCE.md`'s band table EQUALS the one
    generated from the committed manifest.

    The table carries its own standing warning — *"regenerate, do not retype,
    and check this table in the same commit that moves the gate"* — and it has
    gone stale **twice**, the second time in the very session that wrote the
    warning. `3i` moved the gate twice and did not touch it; `AUDIT_3I` §9.3
    measured `≥10% 23.4% (n=26)` in the doc against `34.96% (n=27)` in the
    manifest.

    `3h` A4 already established the principle on `CLAUDE.md`'s census line:
    **generation only helps if something asserts the paste.** This is that
    assertion, for the other generated table.

    MUTATION THAT MAKES THIS FAIL (red, RUN 2026-08-07): change one digit of
    the band table in `predictions/CALIBRATION_TOLERANCE.md`. GREEN PATH:
    `py tools/audit/render_band_table.py` and paste — which IS the fix.
    """
    import render_band_table as rbt

    try:
        table, m = rbt.render()
    except (OSError, ValueError, KeyError) as e:
        check("[3j-C3] CALIBRATION_TOLERANCE.md's band table EQUALS the one "
              "generated from gate_manifest_3e.json", False,
              f"could not render from the manifest: {e}")
        return
    doc = rbt.extract_from_doc()
    check("[3j-C3] CALIBRATION_TOLERANCE.md's band table EQUALS the one "
          "generated from gate_manifest_3e.json — the paste is ASSERTED, not "
          "merely warned about; the warning alone was ignored twice",
          doc is not None and rbt._norm(doc) == rbt._norm(table),
          f"manifest generated {m['generated_at']}, git {m['git_sha'][:7]}"
          + ("" if doc is not None and rbt._norm(doc) == rbt._norm(table)
             else f"\n--- document ---\n{doc}\n--- manifest ---\n{table}"))


def check_predictions_json_status():
    """`3j` C5 (`AUDIT_3I_ADVERSARIAL` §9, table) — the `predictions/` status
    rule reaches the JSON, not only the markdown.

    `3h` A5's check message reads *"EVERY file in predictions/ carries a status
    line"*, and it walks `*.md` only — so all four JSONs sat outside it.
    `gate_manifest_3e.json` was the one live artifact in the directory with no
    `status`/`_status_note` key at all, while the *frozen* `gate_manifest.json`
    had one and the brand-new `per_ability_summary.json` had one. The file most
    likely to be cited was the one with no label saying whether it is current.

    JSON has no comment syntax, so the convention is a top-level `status` (or
    `_status_note`) key — the same four-word vocabulary as the markdown status
    lines, in the shape JSON allows.

    MUTATION THAT MAKES THIS FAIL (red, RUN 2026-08-07): delete the `status`
    key from any `predictions/*.json`. GREEN PATH: add it back.
    """
    root = Path(__file__).resolve().parents[2] / "predictions"
    files = sorted(root.glob("*.json"))
    missing = []
    labelled = {}
    for p in files:
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            missing.append(f"{p.name} (unreadable)")
            continue
        val = None
        if isinstance(d, dict):
            val = d.get("status") or d.get("_status") or d.get("_status_note")
        if val:
            labelled[p.name] = str(val).split(" ")[0].strip("`*")
        else:
            missing.append(p.name)
    print(f"[census] predictions/ JSON status keys: {len(files)} files — "
          + (", ".join(f"{k}={v}" for k, v in sorted(labelled.items()))
             or "none"))
    check("[3j-C5] EVERY file in predictions/ carries a status — extended from "
          "*.md to *.json, where gate_manifest_3e.json (the artifact most "
          "likely to be cited) had no label at all",
          not missing, f"{len(files)} files, {len(labelled)} labelled"
          + (f"; UNLABELLED: {missing}" if missing else ""))


def check_blocked_question_count():
    """`3g` G9 — the "Blocked on the user" table counts ITSELF.

    MUTATION (red): change the header row's column count, or remove the table.
    GREEN PATH: restore it.

    `PROGRESS.md:77` said SIX questions were waiting while the table held SEVEN
    `3f` rows and `3f`'s closing statement said EIGHT — three numbers for one
    countable thing, in the live block a new chat reads first. The numeral is
    gone from the prose (a phrase pointing at the table cannot go stale); this
    prints the real figure so a session that WANTS a number has one with an
    owner.
    """
    p = Path(__file__).resolve().parents[2] / "primer" / "PROGRESS.md"
    lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    try:
        start = next(i for i, ln in enumerate(lines)
                     if ln.strip().startswith("## Blocked on the user"))
    except StopIteration:
        check("[G9] PROGRESS.md has a 'Blocked on the user' table to count",
              False, "section heading not found")
        return 0
    rows, seen_header = 0, False
    for ln in lines[start:]:
        s = ln.strip()
        if s.startswith("|---") or s.startswith("|:--"):
            seen_header = True
            continue
        if seen_header and s.startswith("|"):
            rows += 1
        elif seen_header and not s.startswith("|") and s:
            break
    print(f"[census] PROGRESS.md 'Blocked on the user': {rows} open row(s)")
    check("[G9] the blocked-on-the-user table is COUNTABLE from its own rows, "
          "so no document has to carry the numeral",
          rows > 0, f"{rows} rows parsed")
    return rows


def main():
    print("=== 3f: the guards that must not fail open "
          "(F0 / F4 / F5 / F6 / F7 / F8b) ===\n")
    check_baseline_phase_refusal()
    print()
    check_session_mismatch_states()
    check_log_started_at_is_total()
    print()
    check_stat_block_only_closing_note()
    print()
    check_manifest_cannot_contradict_itself()
    check_holdout_reading_is_not_erased()
    print()
    check_phase_resolution()
    check_phase_guard()
    check_phase_additive()
    check_righteous_vengeance_wiring()
    check_admissibility_outage_refuses()
    check_comparator_can_add_a_flag()
    print()
    check_null_spell_id_cannot_escape_dedupe()
    check_corpus_schema_gate()
    check_enchant_record_parse()
    print()
    check_primer_status_census()
    check_predictions_json_status()
    check_band_table_matches_manifest()
    check_blocked_question_count()
    print()
    check_coverage_split_producing_vs_zero()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        return 1
    print("every refusal path refuses, and every one is distinguishable from "
          "an all-clear")
    return 0


if __name__ == "__main__":
    sys.exit(main())
