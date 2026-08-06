#!/usr/bin/env python3
"""
build_tier2_manifest.py — per-report reproducibility manifest for tier-2 crawl data.

Why this exists (3a audit remediation §1.1b, 2026-08-06): the calibration gate
(`tools/audit/calibrate_crawled.py`) runs on tier-2 bulk data (abilities /
healing / avoidance / damage_taken), which is gitignored by design — a clean
checkout rebuilds `builds.db` with 390 characters and ZERO ability/avoidance/
performance rows. The gate's headline numbers (0 of 41 within tolerance, 41
strict lag-0 candidates) were therefore defined on data no reviewer or
monitoring session could see or verify. manifest.json already records per-FILE
totals and sha256; this tool adds the PER-REPORT layer, so a re-fetch
(`crawl_ascensionlogs.py --recrawl-report <id>`) can be checked report by
report without re-pulling everything, and a reviewer can audit exactly which
reports fed the gate.

Output: one committed `tier2_manifest.json` per day directory under
data/source/crawl/, shaped:

    {
      "generated_at": "...",
      "files": { "<stem>": { "files": [names], "records": N, "payload_rows": N } },
      "by_report": {
        "<report_id>": {
          "<stem>": {"records": N, "payload_rows": N, "payload_sha256": "..."}
        }
      }
    }

- `records`      = NDJSON lines (one per API call made for that report).
- `payload_rows` = sum of len(payload["rows"]) — SOURCE-side row counts.
                   avoidance maps 1:1 onto ability_avoidance (877,850 = 877,850
                   verified 2026-08-06); abilities + healing land in
                   ability_performance via an upsert MERGE plus pet rows, so
                   that table's count is post-merge, not a sum of these.
- `payload_sha256` = order-independent digest: sha256 over the sorted list of
                   sha256(canonical-JSON(payload)) per record. Detects local
                   corruption and confirms exactly what the gate ran on.

⚠ Row COUNTS are the durable audit for a re-fetch; the checksum is exact only
for the original capture. A re-fetched payload can legitimately differ byte-wise
(server-side edits, new API fields) while still carrying the same rows — a
count match with a checksum mismatch means "same shape, different bytes", which
is a prompt to diff, not an error.

Idempotent and deterministic: re-running over unchanged files produces an
identical manifest (git-diff-stable). The crawler calls build_for_dir() at the
end of every run; run standalone to backfill existing day folders:

    py tools/scrapers/build_tier2_manifest.py
"""
import gzip
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CRAWL_ROOT = REPO_ROOT / "data" / "source" / "crawl"
TIER2_STEMS = ["abilities", "healing", "avoidance", "damage_taken"]


def _canonical_payload_hash(payload):
    """sha256 of the payload serialised canonically (sorted keys, no spaces)."""
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def build_for_dir(date_dir):
    """Build (and write) tier2_manifest.json for one day directory.
    Returns the manifest dict, or None if the dir has no tier-2 files."""
    date_dir = Path(date_dir)
    file_totals = {}
    # by_report[report_id][stem] -> {"records": n, "payload_rows": n, "hashes": [...]}
    by_report = {}
    found_any = False

    for stem in TIER2_STEMS:
        paths = sorted(date_dir.glob(f"{stem}*.jsonl.gz"))
        if not paths:
            continue
        found_any = True
        totals = {"files": [p.name for p in paths], "records": 0, "payload_rows": 0}
        for path in paths:
            with gzip.open(path, "rt", encoding="utf-8") as f:
                for line in f:
                    rec = json.loads(line)
                    rid = str(rec.get("report_id"))
                    payload = rec.get("payload") or {}
                    rows = payload.get("rows") if isinstance(payload, dict) else None
                    n_rows = len(rows) if isinstance(rows, list) else 0
                    slot = by_report.setdefault(rid, {}).setdefault(
                        stem, {"records": 0, "payload_rows": 0, "hashes": []})
                    slot["records"] += 1
                    slot["payload_rows"] += n_rows
                    slot["hashes"].append(_canonical_payload_hash(payload))
                    totals["records"] += 1
                    totals["payload_rows"] += n_rows
        file_totals[stem] = totals

    if not found_any:
        return None

    # collapse per-record hashes into one order-independent digest per (report, stem)
    for rid, stems in by_report.items():
        for stem, slot in stems.items():
            combined = hashlib.sha256(
                "".join(sorted(slot.pop("hashes"))).encode("ascii")).hexdigest()
            slot["payload_sha256"] = combined

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "note": ("Per-report reproducibility manifest for gitignored tier-2 data. "
                 "Row counts are the durable audit for a re-fetch "
                 "(crawl_ascensionlogs.py --recrawl-report <id>); payload_sha256 "
                 "is exact only for the original capture. See this tool's "
                 "docstring."),
        "files": {k: file_totals[k] for k in sorted(file_totals)},
        "by_report": {
            rid: {stem: stems[stem] for stem in sorted(stems)}
            for rid, stems in sorted(by_report.items(), key=lambda kv: int(kv[0]))
        },
    }
    out = date_dir / "tier2_manifest.json"
    # stable serialisation; only generated_at changes on a no-op re-run, so
    # skip the write entirely when the data content is unchanged
    if out.exists():
        try:
            old = json.loads(out.read_text(encoding="utf-8"))
            if (old.get("files") == manifest["files"]
                    and old.get("by_report") == manifest["by_report"]):
                return old
        except (json.JSONDecodeError, OSError):
            pass
    out.write_text(json.dumps(manifest, indent=1, ensure_ascii=False),
                   encoding="utf-8")
    return manifest


def main():
    wrote = 0
    for date_dir in sorted(CRAWL_ROOT.iterdir()):
        if not date_dir.is_dir():
            continue
        manifest = build_for_dir(date_dir)
        if manifest is None:
            print(f"{date_dir.name}: no tier-2 files (skipped)")
            continue
        wrote += 1
        n_reports = len(manifest["by_report"])
        totals = ", ".join(
            f"{stem} {v['records']} rec / {v['payload_rows']} rows"
            for stem, v in manifest["files"].items())
        print(f"{date_dir.name}: {n_reports} report(s) | {totals}")
    print(f"tier2_manifest.json written/verified for {wrote} day folder(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
