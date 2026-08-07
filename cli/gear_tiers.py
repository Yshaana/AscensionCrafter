#!/usr/bin/env python3
"""Fresh / mid / BiS gear-tier stat blocks, phase-scoped — the production caller.

    py cli/gear_tiers.py                                  # current phase (season_config)
    py cli/gear_tiers.py --phase "Phase 1 - Zul'Gurub"    # any labelled phase
    py cli/gear_tiers.py --no-phase                       # whole corpus, and says so
    py cli/gear_tiers.py --path Intelligence --role dps --json

Owner-scheduled deliverable, carried from `3j` and `3k`, landed `3l` (C1).
`core.builds.gear.gear_tier_stats` has been phase-parameterised since `3f` F8b;
this is the first production path that calls it, so gear tiers are finally
readable without writing an ad-hoc script.

🛑 REFUSAL SEMANTICS (the reason this file exists as more than plumbing): a
phase window with zero snapshots — the live Molten Core case, open since
2026-08-07T18:00Z with the corpus entirely pre-boundary — must REFUSE with a
named reason, never report an empty tier as a measurement. An empty dict
printed as "the Phase 2 BiS" would be the mixed-phase failure wearing yet
another coat.

Exit codes, matching `check_sim_engine.py`'s convention:
    0  tiers reported
    2  verdict-bearing refusal (named reason, no tiers)
    1  error (missing database, bad arguments)
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config  # noqa: E402
import season_config  # noqa: E402
from core.builds.gear import gear_tier_stats  # noqa: E402

config.ensure_utf8_stdout()


def _fmt_stats(stats, top_n=None):
    items = sorted(stats.items(), key=lambda kv: -abs(kv[1]))
    if top_n:
        items = items[:top_n]
    return ", ".join(f"{k}={v:g}" for k, v in items)


def run(conn, *, phase, path=None, role=None, phase_windows=None,
        phase_horizon=None, phase_refuse_reason=None, phase_boundary=None,
        as_json=False, out=print):
    """The caller's whole decision tree, injectable for the refusal harness.

    `phase=None` means the caller was explicitly asked to pool every phase
    (`--no-phase`); the scoping note from `gear_tier_stats` is printed, not
    swallowed.
    """
    # A payload-level phase refusal poisons every downstream label; surface it
    # as THE result rather than scoping against a timeline known to be broken.
    if phase is not None and phase_refuse_reason:
        out(f"REFUSED: phase timeline unusable — {phase_refuse_reason}")
        out("No tier is reported. Fix the phase capture, then re-run.")
        return 2

    result = gear_tier_stats(
        conn, path=path, role=role, phase=phase,
        phase_windows=phase_windows, phase_horizon=phase_horizon,
        phase_refuse_reason=phase_refuse_reason, phase_boundary=phase_boundary)

    scoping = result["phase_scoping"]

    # 🛑 C1's named case: the window exists and holds NOTHING. Distinct from
    # "thin sample" because the diagnosis differs — the corpus has not caught
    # up with the phase, and no amount of filter-loosening changes that.
    if phase is not None and scoping["snapshots_kept"] == 0:
        out(f"REFUSED: phase window empty: 0 snapshots in {phase!r}")
        out(f"  population considered: {result['population'] + scoping['snapshots_excluded']}"
            f" snapshots with >=12 resolved-stat pieces")
        for reason, n in scoping["excluded_by_reason"].items():
            out(f"  excluded {n}: {reason}")
        out("No tier is reported — an empty phase window is not a measurement.")
        return 2

    if result["verdict"] == "insufficient_sample":
        where = f" in {phase!r}" if phase is not None else " in the corpus"
        out(f"REFUSED: insufficient sample: {result['population']} usable "
            f"snapshots{where} (need >= 8)")
        for reason, n in scoping["excluded_by_reason"].items():
            out(f"  excluded {n}: {reason}")
        out("No tier is reported.")
        return 2

    if as_json:
        out(json.dumps(result, indent=1, default=str))
        return 0

    out(f"gear tiers — phase: {phase if phase is not None else 'ALL (pooled)'}"
        + (f", path: {path}" if path else "")
        + (f", role: {role}" if role else ""))
    out(f"  population: {result['population']} snapshots "
        f"(kept {scoping['snapshots_kept']}, "
        f"excluded {scoping['snapshots_excluded']})")
    for reason, n in scoping["excluded_by_reason"].items():
        out(f"    excluded {n}: {reason}")
    if phase is None:
        out(f"  NOTE: {scoping['note']}")
    for label, tier in result["tiers"].items():
        out(f"  {label:>5} (p{int(tier['percentile'] * 100):02d}): "
            f"budget {tier['gear_stat_budget']:g}, {tier['pieces']} pieces, "
            f"char {tier['character_id']} [{tier['path'] or '?'}]")
        out(f"         {_fmt_stats(tier['stats'], top_n=10)}")
    if result["unmapped_stat_keys"]:
        out(f"  ⚠ unmapped stat keys (excluded from budgets): "
            f"{', '.join(result['unmapped_stat_keys'])}")
    out(f"  provenance: {result['provenance']} — stat blocks are BisBeard's "
        f"resolution of crawled gear (INDEX_GUIDE v16)")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Fresh/mid/BiS gear-tier stat blocks from the crawl corpus, "
                    "phase-scoped.")
    ap.add_argument("--phase", default=season_config.EXPECTED_PHASE_NAME,
                    help="phase label as /api/phases names it "
                         "(default: the current phase, "
                         f"{season_config.EXPECTED_PHASE_NAME!r})")
    ap.add_argument("--no-phase", action="store_true",
                    help="pool every phase in the corpus (the scoping note is "
                         "printed; mixing phases mixes gear tiers)")
    ap.add_argument("--path", help="filter to one Path (e.g. Intelligence)")
    ap.add_argument("--role", help="filter spec_role (substring match)")
    ap.add_argument("--json", action="store_true", dest="as_json",
                    help="emit the full result as JSON")
    args = ap.parse_args(argv)

    if not config.BUILDS_DB_PATH.exists():
        print(f"ERROR: {config.BUILDS_DB_PATH} not found — build it with "
              f"py ingest/logs_gg/build_builds_db.py", file=sys.stderr)
        return 1

    # The phase timeline comes from the committed crawl captures (3f F8b),
    # never from a constant. latest_phase_context wraps phase_guard, so a
    # flipped or ambiguous payload arrives here as refuse_reason.
    from ingest.logs_gg.build_builds_db import latest_phase_context
    windows, horizon, refuse_reason, boundary = latest_phase_context()

    import sqlite3
    conn = sqlite3.connect(config.BUILDS_DB_PATH)
    try:
        return run(conn,
                   phase=None if args.no_phase else args.phase,
                   path=args.path, role=args.role,
                   phase_windows=windows, phase_horizon=horizon,
                   phase_refuse_reason=refuse_reason, phase_boundary=boundary,
                   as_json=args.as_json)
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
