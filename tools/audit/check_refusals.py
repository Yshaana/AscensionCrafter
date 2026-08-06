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
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

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


def main():
    print("=== 3f: the guards that must REFUSE (F0 / F4 / F5) ===\n")
    check_baseline_phase_refusal()
    print()
    check_session_mismatch_states()
    check_log_started_at_is_total()
    print()
    check_stat_block_only_closing_note()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        return 1
    print("every refusal path refuses, and every one is distinguishable from "
          "an all-clear")
    return 0


if __name__ == "__main__":
    sys.exit(main())
