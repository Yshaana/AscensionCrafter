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
import season_config  # noqa: E402
from core.builds.phases import (describe_horizon, phase_guard,  # noqa: E402
                                phase_windows)
from core.spells import crosswalk  # noqa: E402

config.ensure_utf8_stdout()


def latest_phase_context():
    """`(windows, horizon, refuse_reason, boundary)` for the newest payload.

    🛑 `3f` F8b — THE TIMELINE COMES FROM THE LIVE RESPONSE, cached with its
    fetch time, never from a date typed into a constant. `season_config.py` is
    the one place that knows the EXPECTED phase; it is deliberately not the
    place a phase timeline is read from, and neither is the `user_confirmed`
    `server_phases` seed (whose Phase 1 has a NULL start, which is why the
    corpus has been described as "all Phase 1" when nearly half of it predates
    Phase 1's actual start — the census below prints the real figure).

    The newest capture wins: an older payload knows about fewer phases, and its
    fetch time becomes the horizon past which nothing can be resolved.

    🚨 `3g` G0 — **but the newest payload is exactly what makes the horizon
    unsafe.** The first post-flip daily crawl appends a post-flip payload, so
    the horizon jumps past the flip while Phase 1's window is still open-ended,
    and every post-flip capture up to that fetch time resolves to Phase 1. So
    the timeline is now gated by `phase_guard()`: the payload's own active
    top-level phase must still be `season_config.EXPECTED_PHASE_NAME`, and a
    capture at or after `season_config.NEXT_PHASE_BOUNDARY` takes no label
    until the payload carries a window that reaches it. This function is where
    `ingest/` — which may import `season_config` — hands those two constants to
    `core/`, which may not.
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
        return [], None, ("no /api/phases capture found under "
                          "data/source/crawl/*/phases.jsonl.gz"), None
    windows, horizon = phase_windows(best[1], best[0])
    refuse, boundary = phase_guard(
        best[1], windows,
        expected_phase_name=season_config.EXPECTED_PHASE_NAME,
        unmodelled_boundary=season_config.NEXT_PHASE_BOUNDARY)
    return windows, horizon, refuse, boundary

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


def migrate_existing():
    """`py ingest/logs_gg/build_builds_db.py --migrate` — bring an existing
    `builds.db` to the current schema version WITHOUT rebuilding it.

    🆕 `3j` B1. The rebuild path already produces a current database (it drops
    and recreates), so this exists for the case the audit actually found: a
    **retained** `builds.db` that is read rather than rebuilt. `3j`'s own
    corpus was exactly that — post-`3i` in content (0 `is_pet=1` rows, 22,427
    `pet_ability_damage` rows) but written before `PRAGMA user_version` existed,
    so every consumer's new `assert_schema_current` refused it.

    Preferred over a rebuild when the gate must not move: migrating a corpus
    that already has no restatement rows changes **no data at all**, so it
    cannot shift a single number. A rebuild re-reads `data/source/crawl/` and
    may legitimately pick up a new crawl day.
    """
    if not BUILDS_DB_PATH.exists():
        print(f"{BUILDS_DB_PATH} does not exist — nothing to migrate. "
              f"Run without --migrate to build it.")
        return 1
    conn = sqlite3.connect(BUILDS_DB_PATH)
    before = conn.execute(
        "SELECT COUNT(*), COALESCE(SUM(damage_total), 0) "
        "FROM ability_performance").fetchone()
    frm, to, note = corpus.migrate_schema(conn)
    after = conn.execute(
        "SELECT COUNT(*), COALESCE(SUM(damage_total), 0) "
        "FROM ability_performance").fetchone()
    conn.close()
    print(f"[migrate] {BUILDS_DB_PATH.name}: schema v{frm} -> v{to} — {note}")
    print(f"[migrate] ability_performance rows {before[0]} -> {after[0]}, "
          f"damage_total {before[1]:.1f} -> {after[1]:.1f}"
          + ("  (UNCHANGED — this migration touched no data)"
             if before == after else "  ⚠ CHANGED — restatement rows removed"))
    return 0


def main():
    if "--migrate" in sys.argv:
        return migrate_existing()
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
    windows, horizon, phase_refuse, phase_boundary = latest_phase_context()
    # 3g G0 — the corpus still BUILDS when phase labelling refuses; it just
    # labels nothing. Refusing the whole build over a labelling inconsistency
    # would take down every read that does not depend on phase at all.
    if phase_refuse:
        print(f"  🛑 PHASE LABELLING REFUSED — every phase_label is NULL.\n"
              f"     {phase_refuse}")
    elif phase_boundary is not None:
        print(f"  ⚠ declared boundary {phase_boundary:%Y-%m-%d %H:%M}Z is ARMED "
              f"— /api/phases carries no phase reaching it, so captures at or "
              f"after it take no label (season_config.NEXT_PHASE_BOUNDARY)")
    item_stats = gear.build_items_from_gear(
        conn, phase_windows=windows, phase_horizon=horizon,
        phase_refuse_reason=phase_refuse, phase_boundary=phase_boundary)
    print(f"  {item_stats['items']} items, {item_stats['with_stats']} with resolved "
          f"stat blocks (provenance: {item_stats['provenance']})")
    if item_stats["phase_labels_derived"]:
        # 3g G0 — `horizon` is None whenever the payload's fetch time did not
        # parse, and `f"{None:%Y-%m-%d}"` raises. This is F5's exact crash
        # class, reintroduced inside F8b's own code; a guard that cannot run
        # must SAY so, not die reporting it. `describe_horizon` is in core/ so
        # it can be tested without a corpus rebuild.
        print(f"  phase_label derived from /api/phases "
              f"(horizon {describe_horizon(horizon)}): "
              + ", ".join(f"{k}={v}"
                          for k, v in item_stats["items_by_phase_label"].items()))
        for why, n in item_stats["phase_unresolved_by_reason"].items():
            print(f"    ⚠ {n} unresolved — {why}")
    else:
        print("  ⚠ phase_label left NULL on every row — no /api/phases capture "
              "found under data/source/crawl/*/phases.jsonl.gz")

    # 3g G9 — the corpus phase split, PRINTED. It shipped as two different
    # hand-typed percentages (44.2% and 38.6%); now it has an owner.
    census = gear.corpus_phase_census(
        conn, phase_windows=windows, phase_horizon=horizon,
        phase_refuse_reason=phase_refuse, phase_boundary=phase_boundary)
    print(f"  corpus phase census: {census['snapshots']} snapshots — "
          + ", ".join(f"{k}: {v} ({census['pct_by_phase_label'][k]}%)"
                      for k, v in census["by_phase_label"].items()))

    print("[post] linking performance rows to build snapshots…")
    link = corpus.link_performance_snapshots(conn)
    print(f"  exact={link['exact']} nearest-in-time={link['nearest']} "
          f"unmatched={link['unmatched']}")

    conn.commit()

    n = {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
         for t in ["characters", "character_snapshots", "snapshot_cards", "snapshot_gear",
                   "encounters", "capture_scopes", "encounter_performance",
                   "ability_performance",
                   # 🆕 3j B2 — the E15 side table, in the census. `AUDIT_3I`
                   # §7.2: it was omitted, so a silently-broken pet ingest
                   # produced `pet_damage = NULL` everywhere and PRINTED
                   # NOTHING. A table whose emptiness is invisible cannot be
                   # noticed to be empty.
                   "pet_ability_damage",
                   "ability_avoidance", "leaderboard_entries"]}
    # 🆕 3j B2 — the E15 invariant, asserted against the REAL corpus at the end
    # of every build, not against a fixture. `check_e15_pet_row_double_count`
    # builds its own in-memory table and exercises only `modelled_damage_share`'s
    # filter, so it is green regardless of what `ingest_abilities_record` does.
    n_pet_rows = conn.execute(
        "SELECT COUNT(*) FROM ability_performance WHERE is_pet = 1").fetchone()[0]
    n_unresolved = conn.execute(
        "SELECT COUNT(*) FROM ability_performance WHERE spell_id = ?",
        (corpus.UNRESOLVED_SPELL_ID,)).fetchone()[0]
    schema_v = corpus.schema_version(conn)
    conn.close()

    print(f"\nBuilt {BUILDS_DB_PATH}")
    for t, c in n.items():
        print(f"  {t:<24} {c:>8}")
    print(f"  {'PRAGMA user_version':<24} {schema_v:>8}")
    print(f"\n[E15] ability_performance rows with is_pet=1: {n_pet_rows} "
          f"(must be 0 — the endpoint's per-pet restatement belongs in "
          f"pet_ability_damage, and summing both double-counts every "
          f"pet-owner's damage)")
    print(f"[E15] pet_ability_damage rows: {n['pet_ability_damage']}")
    print(f"[3j-B3] ability_performance rows with an UNRESOLVED spell_id "
          f"({corpus.UNRESOLVED_SPELL_ID}): {n_unresolved} — these used to be "
          f"NULL, which escapes the PRIMARY KEY and re-ingests as duplicates")
    if n_pet_rows:
        print(f"🛑 E15 REGRESSION — {n_pet_rows} is_pet=1 row(s) landed in "
              f"ability_performance. Every damage total over this corpus is "
              f"inflated for pet-owning characters. Do not run the gate "
              f"against it.")
        return 1
    if not n["pet_ability_damage"]:
        print("⚠ pet_ability_damage is EMPTY. That is correct only if no "
              "captured scope had a pet-owning player in it; if the corpus "
              "has pet owners, the restatement is being dropped rather than "
              "re-homed. Check before trusting a per-pet breakdown.")
    if totals["bad_lines"]:
        print(f"  ⚠ {totals['bad_lines']} unparseable line(s) skipped "
              f"(crawler mid-append is the usual cause)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
