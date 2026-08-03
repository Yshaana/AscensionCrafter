#!/usr/bin/env python3
"""
Usage: python3 parse_log.py <WoWCombatLog.txt> [output.json]

Combines:
  - combat_log_parser.py  : standard combat events (damage/miss/heal/etc.)
  - decode_alc.py          : ALC-embedded player builds (gear/talents/spec)

Writes a JSON summary with:
  - event_count
  - crit_rate_by_source_ability
  - avoidance_breakdown
  - builds: list of decoded CI/KEYFRAME_REF records found in the log
"""
import json
import sys
from pathlib import Path

from combat_log_parser import parse_log, crit_rate_by_source_ability, avoidance_breakdown
from decode_alc import decode_chunks


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 parse_log.py <WoWCombatLog.txt> [output.json]")
        sys.exit(1)

    log_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else log_path.with_suffix(".summary.json")

    lines = log_path.read_text(errors="ignore").splitlines()

    events = parse_log(lines)
    crit_rates = crit_rate_by_source_ability(events)
    avoidance = avoidance_breakdown(events)
    builds = decode_chunks(lines)

    summary = {
        "source_file": str(log_path),
        "event_count": len(events),
        "crit_rate_by_source_ability": {
            f"{src} :: {ability}": stats for (src, ability), stats in crit_rates.items()
        },
        "avoidance_breakdown": {
            f"{src} :: {ability}": stats for (src, ability), stats in avoidance.items()
        },
        "builds": [
            {"record_type": rtype, "data": data} for rtype, data in builds
        ],
    }

    out_path.write_text(json.dumps(summary, indent=2, default=str))
    print(f"Parsed {len(events)} combat events, {len(builds)} build record(s).")
    print(f"Summary written to {out_path}")


if __name__ == "__main__":
    main()
