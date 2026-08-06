"""
build_builds_db.py — Phase 3 Task 1: normalise the raw crawl into builds.db.

Rebuilds data/derived/builds.db from every committed (and locally present
tier-2) .jsonl.gz under data/source/crawl/. Like every derived db it is
gitignored and safe to delete; the NDJSON is the source of truth.

    py ingest/logs_gg/build_builds_db.py

Spell-ID resolution happens HERE, at rebuild time, never at capture time —
so a crosswalk improvement re-resolves everything without re-crawling. It
needs data/derived/ascension.db to exist (run `py cli/rebuild.py` first);
without it the corpus still builds, with every card left unresolved and a
loud warning.

Safe to run while the crawler is appending: multi-member gzip streams read
transparently, and a partially-written trailing line is skipped and counted.
"""
import gzip
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import config  # noqa: E402
from config import BUILDS_DB_PATH, CRAWL_DIR, DB_PATH, ensure_derived_dir  # noqa: E402
from core.builds import corpus, gear  # noqa: E402
from core.builds.phases import phase_windows  # noqa: E402
from core.spells import crosswalk  # noqa: E402

config.ensure_utf8_stdout()


def latest_phase_windows():
    """The most recently captured `/api/phases` payload, as phase windows.

    🛑 `3f` F8b — THE BOUNDARY COMES FROM THE LIVE RESPONSE, cached with its
    fetch time, never from a date typed into a constant. `season_config.py` is
    the one place that knows the EXPECTED phase; it is deliberately not the
    place a phase timeline is read from, and neither is the `user_confirmed`
    `server_phases` seed (whose Phase 1 has a NULL start, which is why the
    corpus has been described as "all Phase 1" when 38.6% of it predates
    Phase 1's actual start).

    The newest capture wins: an older payload knows about fewer phases, and its
    fetch time becomes the horizon past which nothing can be resolved.
    """
    best = None
    for path in sorted(CRAWL_DIR.glob("*/phases.jsonl.gz")):
        try:
            with gzip.open(path, "rt", encoding="utf-8") as f:
                for line in f:
                    rec = json.loads(line)
                    at = rec.get("captured_at")
                    if at and (best is None or at > best[0]):
                        best = (at, rec.get("payload") or {})
        except (OSError, KeyError, json.JSONDecodeError):
            continue
    if best is None:
        return [], None
    return phase_windows(best[1], best[0])

# Ingestion order matters only mildly (characters before performance makes the
# character upserts richer first), but reports must precede the per-ability
# files so encounter durations exist for the DPS pass.
FILE_ORDER = ["phases", "reports", "characters", "leaderboards",
              "abilities", "healing", "avoidance", "damage_taken"]

# file stem -> the record_type its lines carry (they differ for four families)
STEM_TO_TYPE = {
    "phases": "phases_snapshot",
    "reports": "report_encounters",
    "characters": "character_armory",
    "leaderboards": "leaderboard",
    "abilities": "abilities",
    "healing": "healing",
    "avoidance": "avoidance",
    "damage_taken": "damage_taken",
}


def iter_records(path):
    """Yield (record, None) or (None, error) per line; tolerant of a
    partially-written trailing line while the crawler is running."""
    with gzip.open(path, "rt", encoding="utf-8") as f:
        while True:
            try:
                line = f.readline()
            except EOFError:
                # trailing partial gzip member (crawler mid-append)
                break
            if not line:
                break
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line), None
            except json.JSONDecodeError as e:
                yield None, str(e)


def stem_of(path):
    return path.name.split(".")[0]


def main():
    ensure_derived_dir()
    if BUILDS_DB_PATH.exists():
        BUILDS_DB_PATH.unlink()
        print(f"Removed stale {BUILDS_DB_PATH.name} — rebuilding fresh from crawl NDJSON.")

    conn = sqlite3.connect(BUILDS_DB_PATH)
    corpus.init_schema(conn)

    files = sorted(CRAWL_DIR.glob("*/*.jsonl.gz"),
                   key=lambda p: (p.parent.name, FILE_ORDER.index(stem_of(p))
                                  if stem_of(p) in FILE_ORDER else 99, p.name))
    if not files:
        print(f"No crawl files under {CRAWL_DIR} — nothing to build.")
        return 1

    totals = {"ingested": 0, "skipped": 0, "bad_lines": 0}
    for path in files:
        stem = stem_of(path)
        record_type = STEM_TO_TYPE.get(stem)
        if record_type is None:
            print(f"  [warn] {path.parent.name}/{path.name}: unknown record family, skipped")
            continue
        ingester = corpus.INGESTERS.get(record_type)
        counted = {"records": 0, "ingested": 0, "skipped": 0}
        if ingester is None:
            continue  # deliberately not ingested (phases -> ascension.db)
        for rec, err in iter_records(path):
            if err is not None:
                totals["bad_lines"] += 1
                continue
            counted["records"] += 1
            rec["_source_file"] = f"{path.parent.name}/{path.name}"
            outcome = ingester(conn, rec)
            if outcome == "ingested":
                counted["ingested"] += 1
            else:
                counted["skipped"] += 1
        conn.execute(
            "INSERT OR REPLACE INTO corpus_files (file, records, ingested, skipped) "
            "VALUES (?,?,?,?)",
            (f"{path.parent.name}/{path.name}", counted["records"],
             counted["ingested"], counted["skipped"]))
        totals["ingested"] += counted["ingested"]
        totals["skipped"] += counted["skipped"]
        print(f"  {path.parent.name}/{path.name}: {counted['ingested']}/{counted['records']} records")

    # --- post-passes -------------------------------------------------------
    print("\n[post] aggregating encounter performance…")
    perf_rows = corpus.compute_encounter_performance(conn)
    corpus.compute_damage_share(conn)
    print(f"  {perf_rows} (scope, character) performance rows")

    print("[post] resolving snapshot cards via the crosswalk…")
    if DB_PATH.exists():
        asc = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)

        cache = {}

        def resolver(entry_id, rank):
            key = (entry_id, rank)
            if key not in cache:
                hits = crosswalk.resolve_entry_id(asc, entry_id, card_rank=rank)
                cache[key] = hits[0] if hits else None
            return cache[key]

        stats = corpus.resolve_snapshot_cards(conn, resolver)
        asc.close()
        print(f"  {stats['resolved']} resolved, {stats['ambiguous']} ambiguous "
              f"(left NULL, never tie-broken), {stats['unresolved']} unresolved "
              f"of {stats['pairs']} distinct (entry_id, rank) pairs")
    else:
        print(f"  ⚠ {DB_PATH.name} missing — run `py cli/rebuild.py` first; "
              f"every card left spell_id NULL / 'unresolved'")

    print("[post] deduping gear into the items table…")
    windows, horizon = latest_phase_windows()
    item_stats = gear.build_items_from_gear(
        conn, phase_windows=windows, phase_horizon=horizon)
    print(f"  {item_stats['items']} items, {item_stats['with_stats']} with resolved "
          f"stat blocks (provenance: {item_stats['provenance']})")
    if item_stats["phase_labels_derived"]:
        print(f"  phase_label derived from /api/phases "
              f"(horizon {horizon:%Y-%m-%d %H:%M}Z): "
              + ", ".join(f"{k}={v}"
                          for k, v in item_stats["items_by_phase_label"].items()))
        for why, n in item_stats["phase_unresolved_by_reason"].items():
            print(f"    ⚠ {n} unresolved — {why}")
    else:
        print("  ⚠ phase_label left NULL on every row — no /api/phases capture "
              "found under data/source/crawl/*/phases.jsonl.gz")

    print("[post] linking performance rows to build snapshots…")
    link = corpus.link_performance_snapshots(conn)
    print(f"  exact={link['exact']} nearest-in-time={link['nearest']} "
          f"unmatched={link['unmatched']}")

    conn.commit()

    n = {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
         for t in ["characters", "character_snapshots", "snapshot_cards", "snapshot_gear",
                   "encounters", "capture_scopes", "encounter_performance",
                   "ability_performance", "ability_avoidance", "leaderboard_entries"]}
    conn.close()

    print(f"\nBuilt {BUILDS_DB_PATH}")
    for t, c in n.items():
        print(f"  {t:<24} {c:>8}")
    if totals["bad_lines"]:
        print(f"  ⚠ {totals['bad_lines']} unparseable line(s) skipped "
              f"(crawler mid-append is the usual cause)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
