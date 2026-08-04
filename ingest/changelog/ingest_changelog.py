#!/usr/bin/env python3
"""Changelog -> `patches` / `patch_entries` / `patch_entry_spells` (Phase 1 Task 2).

Also seeds `seasons` and `server_phases`, because §2.10 derives gear tiers per
server phase and that needs a phase timeline to exist.

Offline and re-runnable: it reads only the committed captures under
`data/source/changelog/`. Acquisition is `tools/scrapers/fetch_changelog.py`'s job.

    py ingest/changelog/ingest_changelog.py                  # current era, Darkmoon
    py ingest/changelog/ingest_changelog.py --all            # the full 2016-> corpus
    py ingest/changelog/ingest_changelog.py --new-cards      # report only

**Default scope is deliberate.** The corpus is 35,238 entries reaching back to
2016/07/23 and is *mostly not about this realm* — 27,609 entries are untagged and
the biggest tagged realms are Elune (2,875) and Area-52 (2,455) against Darkmoon's
170. Ingesting all of it by default would bury the realm we play on. `--all` exists
for history questions.

⚠ Two things this ingester will NOT do, both settled in Phase 0:
  * It does not build the phase timeline from changelog text. 93 entries match
    phase/season language and they are overwhelmingly *boss mechanic* phases
    ("Illidan starts his Phase 3"). `/api/phases` is authoritative.
  * It does not treat an unresolved new-card name as a discovery. The client DBC
    knows about a card the day it is announced; the catalog export does not.
"""
import argparse
import gzip
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from config import (  # noqa: E402
    CHANGELOG_DIR, CRAWL_DIR, DBC_ASCENSION_EXTRACT_JSON, DB_PATH, SPELL_EXPORT,
)
from core.changelog.parse import (  # noqa: E402
    LEGACY_ZONE_TOKENS, detect_new_cards, parse_entry,
)
from core.db.connection import connect, transaction  # noqa: E402
from core.db.schema import create_phase1_schema  # noqa: E402

REALM = "Darkmoon"
SEASON_LABEL = "S10"
CURRENT_ERA = "2026/07/01"   # where dense realm tagging begins (Phase 0 Task 3)

# User-confirmed 2026-08-04. The server's own "Phase N" label, which is NOT the logs
# API's `phase_number` field — that API's phase_number=2 record is *named* "Phase 1.1"
# and is a child of Phase 1. Build timelines from name + parent id, never the number.
SEED_PHASES = [
    (1, "Zul'Gurub", None, "2026-08-08"),
    (2, None, "2026-08-08", None),
]


def load_known_names():
    """Lowercased card name -> [(source, id)]. Catalog + the client's own card list."""
    names = {}
    for s in json.loads(SPELL_EXPORT.read_text(encoding="utf-8"))["spells"]:
        names.setdefault(s["name"].strip().lower(), []).append(("catalog", s["id"]))
    if DBC_ASCENSION_EXTRACT_JSON.exists():
        ca = json.loads(DBC_ASCENSION_EXTRACT_JSON.read_text(encoding="utf-8")) \
            .get("dbc_character_advancement")
        if ca:
            i_name, i_id = ca["columns"].index("name"), ca["columns"].index("ca_id")
            for row in ca["rows"]:
                nm = (row[i_name] or "").strip().lower()
                if nm:
                    names.setdefault(nm, []).append(("character_advancement", row[i_id]))
    return names


def load_zone_tokens():
    zones = set(LEGACY_ZONE_TOKENS)
    for path in CRAWL_DIR.glob("*/phases.jsonl.gz"):
        try:
            with gzip.open(path, "rt", encoding="utf-8") as f:
                for line in f:
                    for phase in json.loads(line)["payload"].get("phases") or []:
                        for loc in phase.get("locations") or []:
                            if loc.get("location"):
                                zones.add(loc["location"].strip().lower())
        except (OSError, KeyError, json.JSONDecodeError):
            continue
    return zones


def iter_raw_entries(directories):
    """Yield `(source_file, entry)` from every captured page."""
    for directory in directories:
        for path in sorted(Path(directory).glob("*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
            data = payload.get("data")
            if not isinstance(data, dict):
                continue
            for by_category in data.values():
                if isinstance(by_category, dict):
                    for entries in by_category.values():
                        for entry in entries or []:
                            yield path.name, entry


def reset_tables(conn):
    """Clear everything this ingester owns, in foreign-key-safe order.

    Children first — `patches.season_id` and `server_phases.season_id` both point at
    `seasons`, so deleting seasons first fails the FK check. (It failed loudly rather
    than silently, which is the whole reason the pragma is on.)
    """
    for table in ("patch_entry_spells", "patch_entries", "patches",
                  "server_phases", "seasons"):
        conn.execute(f"DELETE FROM {table}")


def seed_seasons_and_phases(conn):
    """Season + server-phase timeline. Call `reset_tables` first."""
    cur = conn.execute("INSERT INTO seasons (label, realm, started_at, ended_at) "
                       "VALUES (?,?,?,?)", (SEASON_LABEL, REALM, None, None))
    season_id = cur.lastrowid

    api_phases = load_api_phases()
    for number, label, started, ended in SEED_PHASES:
        match = api_phases.get(number)
        conn.execute(
            "INSERT INTO server_phases (season_id, phase_number, label, started_at, "
            "ended_at, api_phase_id, api_phase_number, parent_api_phase_id, source, notes) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (season_id, number, label or (match or {}).get("name"), started, ended,
             (match or {}).get("id"), (match or {}).get("phase_number"),
             (match or {}).get("progression_parent_phase_id"),
             "user_confirmed",
             "phase_number here is the SERVER's label; api_phase_number is the logs "
             "API's own field and the two disagree - see Phase 0 Task 2"))
    return season_id


def load_api_phases():
    """`/api/phases` records the crawler captured, keyed by the API's own number.

    Kept strictly as *supplementary* — the seeded timeline is user-confirmed, and
    the API's numbering is known not to match the server's labels.
    """
    out = {}
    for path in sorted(CRAWL_DIR.glob("*/phases.jsonl.gz")):
        try:
            with gzip.open(path, "rt", encoding="utf-8") as f:
                for line in f:
                    for phase in json.loads(line)["payload"].get("phases") or []:
                        num = phase.get("phase_number")
                        if num is not None and phase.get("progression_parent_phase_id") is None:
                            out[num] = phase
        except (OSError, KeyError, json.JSONDecodeError):
            continue
    return out


def ingest(conn, records, season_id, *, fetched_at):
    """Write patches, entries and name links. `reset_tables` has already run."""
    by_date = {}
    for rec in records:
        date = (rec["date"] or "").replace("/", "-")
        if date:
            by_date.setdefault(date, []).append(rec)

    stats = {"patches": 0, "entries": 0, "name_links": 0, "resolved_links": 0,
             "by_direction": {}, "by_status": {}}
    for date, recs in sorted(by_date.items()):
        cur = conn.execute(
            "INSERT INTO patches (realm, season_id, patch_date, fetched_at, entry_count) "
            "VALUES (?,?,?,?,?)", (REALM, season_id, date, fetched_at, len(recs)))
        patch_id = cur.lastrowid
        stats["patches"] += 1

        for rec in recs:
            if rec["id"] is None:
                continue
            conn.execute(
                "INSERT OR REPLACE INTO patch_entries (entry_id, patch_id, realms, status, "
                "status_note, category, change_type, change_direction, raw_text, "
                "first_seen_at, status_changed_at, source_file) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (rec["id"], patch_id, ",".join(rec["realms"]), rec["status_class"],
                 "; ".join(rec["status"]) or None, str(rec["category"]),
                 rec["change_type"], rec["change_direction"], rec["description"],
                 rec["created_at"] or fetched_at, rec["updated_at"], rec.get("source_file")))
            stats["entries"] += 1
            stats["by_direction"][rec["change_direction"]] = \
                stats["by_direction"].get(rec["change_direction"], 0) + 1
            stats["by_status"][rec["status_class"]] = \
                stats["by_status"].get(rec["status_class"], 0) + 1

            for ability in rec["abilities"]:
                spell_id = next((i for src, i in ability["refs"] if src == "catalog"), None)
                ca_id = next((i for src, i in ability["refs"]
                              if src == "character_advancement"), None)
                method = ("bracketed" if ability["detection"].startswith("bracketed")
                          else "prose_name_match")
                conn.execute(
                    "INSERT INTO patch_entry_spells (entry_id, spell_id, ca_id, "
                    "matched_name, match_method, confidence) VALUES (?,?,?,?,?,?)",
                    (rec["id"], spell_id, ca_id, ability["name"], method,
                     ability["confidence"]))
                stats["name_links"] += 1
                if spell_id or ca_id:
                    stats["resolved_links"] += 1
    return stats


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--all", action="store_true",
                    help="ingest the full 2016-> corpus instead of the current era")
    ap.add_argument("--since", default=CURRENT_ERA, help="earliest group_key, YYYY/MM/DD")
    ap.add_argument("--realm", default=REALM,
                    help="only ingest entries tagged with this realm ('' for no filter)")
    ap.add_argument("--new-cards", action="store_true",
                    help="report unresolved new-card names and exit without writing")
    args = ap.parse_args()

    known = load_known_names()
    zones = load_zone_tokens()
    since = None if args.all else args.since
    realm_filter = args.realm.strip().lower() if args.realm else None

    records, skipped_realm = [], 0
    for source_file, entry in iter_raw_entries(
            [CHANGELOG_DIR / "backfill", CHANGELOG_DIR / "daily"]):
        rec = parse_entry(entry, known, zones)
        if since and (rec["date"] or "") < since:
            continue
        if realm_filter and realm_filter not in {r.lower() for r in rec["realms"]}:
            skipped_realm += 1
            continue
        rec["source_file"] = source_file
        records.append(rec)

    # the same entry id appears on both a backfill page and a daily page
    deduped = {}
    for rec in records:
        deduped.setdefault(rec["id"], rec)
    records = list(deduped.values())

    print(f"known card names: {len(known)}   zone tokens: {len(zones)}")
    print(f"entries in scope: {len(records)}"
          f"  (skipped {skipped_realm} not tagged {args.realm!r};"
          f" since={since or 'ALL'})")

    if args.new_cards:
        new_cards = detect_new_cards(records, known)
        print(f"\nnew-card announcements with an unresolved name: {len(new_cards)}")
        for card in new_cards:
            print(f"  {card['date']}  {card['name']!r}")
        if not new_cards:
            print("  (none - consistent with Phase 0: every announced card is already "
                  "in CharacterAdvancement.dbc)")
        return 0

    fetched_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    conn = connect(DB_PATH)
    with transaction(conn):
        create_phase1_schema(conn)
        reset_tables(conn)
        season_id = seed_seasons_and_phases(conn)
        stats = ingest(conn, records, season_id, fetched_at=fetched_at)

    phases = conn.execute("SELECT phase_number, label, started_at, ended_at "
                          "FROM server_phases ORDER BY phase_number").fetchall()
    print(f"\nseasons: 1 ({SEASON_LABEL}/{REALM})   server_phases: {len(phases)}")
    for p in phases:
        print(f"  Phase {p[0]}: {p[1] or '(label TBC)'}  {p[2] or '?'} -> {p[3] or 'open'}")
    print(f"\npatches: {stats['patches']}   patch_entries: {stats['entries']}")
    print(f"patch_entry_spells: {stats['name_links']} "
          f"({stats['resolved_links']} resolved to a card)")
    print(f"by direction: {dict(sorted(stats['by_direction'].items()))}")
    print(f"by status:    {dict(sorted(stats['by_status'].items()))}")

    pending = conn.execute(
        "SELECT COUNT(*) FROM patch_entries WHERE status != 'live'").fetchone()[0]
    print(f"\n⚠ {pending} of {stats['entries']} entries are NOT yet live - do not age a "
          f"fact against one of these until its status changes")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
