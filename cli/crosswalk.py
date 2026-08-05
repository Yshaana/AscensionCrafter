#!/usr/bin/env python3
"""Build and query the ID crosswalk (Phase 1 Task 3).

    py cli/crosswalk.py                     # rebuild every source, print a summary
    py cli/crosswalk.py --resolve 40876     # what does this entry_id point at?
    py cli/crosswalk.py --spell 46917       # every external id pointing at this spell
    py cli/crosswalk.py --validate          # re-run Phase 0 Task 5's checks

Populates four external ID spaces from the client's own `CharacterAdvancement.dbc`,
`dbc_spell_rank`, `Cards.txt`, and the entry_ids actually observed on live
characters in `data/source/crawl/` + `data/derived/scouted_builds.db`.

🛑 The rule this table exists to enforce: **never join `entry_id` to `spells.id`.**
Phase 0 measured 0 of 1,054 matching, with one numeric collision (`50043`) that is
two entirely unrelated cards. Decisions live in `core/spells/crosswalk.py`.
"""
import argparse
import gzip
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import CRAWL_DIR, DB_PATH, SCOUTED_DB_PATH  # noqa: E402
import config  # noqa: E402

# Piped/redirected stdout defaults to cp1252 on Windows and this file
# prints non-ASCII; without this it dies with UnicodeEncodeError only when
# its output is captured. See config.ensure_utf8_stdout.
config.ensure_utf8_stdout()
from core.db.connection import connect, table_exists, transaction  # noqa: E402
from core.db.schema import create_phase1_schema  # noqa: E402
from core.spells import crosswalk as xw  # noqa: E402


def _walk_entry_ids(node, out):
    """Collect every `{entry_id, rank}` dict anywhere in a nested structure.

    Walks rather than indexing a known path (today:
    `payload.armory.ci_resolved.specialization.hero_build`) because the site's
    payload shape is not ours to depend on — a silent path change would look like
    "no characters run any cards" rather than an error.
    """
    if isinstance(node, dict):
        if "entry_id" in node and isinstance(node.get("entry_id"), int):
            out.append((node["entry_id"], node.get("rank"), node.get("name")))
        for value in node.values():
            _walk_entry_ids(value, out)
    elif isinstance(node, list):
        for value in node:
            _walk_entry_ids(value, out)


def observed_entry_ids():
    """`(entry_id, rank, name, evidence_ref)` from every live capture we hold."""
    seen = []
    for path in sorted(CRAWL_DIR.glob("*/characters.jsonl.gz")):
        evidence = path.relative_to(CRAWL_DIR.parent.parent).as_posix()
        try:
            with gzip.open(path, "rt", encoding="utf-8") as f:
                for line in f:
                    found = []
                    _walk_entry_ids(json.loads(line), found)
                    seen.extend((eid, rank, name, evidence)
                                for eid, rank, name in found)
        except (OSError, json.JSONDecodeError):
            continue

    if SCOUTED_DB_PATH.exists():
        scouted = sqlite3.connect(str(SCOUTED_DB_PATH))
        try:
            rows = scouted.execute(
                "SELECT entry_id, rank, name FROM scouted_build_entries").fetchall()
            seen.extend((r[0], r[1], r[2], "scouted_builds.db") for r in rows)
        except sqlite3.OperationalError:
            pass
        scouted.close()
    return seen


def build(conn):
    observations = observed_entry_ids()
    with transaction(conn):
        create_phase1_schema(conn)
        ca = xw.populate_character_advancement(conn)
        live = xw.populate_catalog_vs_live(conn)
        obs = xw.populate_observed_entry_ids(conn, observations)
        cards = xw.populate_card_ids(conn)

    print(f"character_advancement: {ca['rows']} rows from {ca['cards']} cards"
          f"  (fingerprint conflicts {ca['conflicts']}, unchecked {ca['unchecked']})")
    print(f"catalog_vs_live:       {live['gaps']} catalog entries stored at a rank a "
          f"level-60 character does NOT hold ({live['rows']} rows)")
    print(f"    of those rows, the level-60 id is absent from the catalog entirely: "
          f"{live['level_rank_absent_from_catalog']}")
    print(f"    ⚠ ambiguous (several spells tie for the top rank): {live['ambiguous']}"
          f" - recorded as conflicts, NOT tie-broken")
    print(f"    fingerprint conflicts {live['conflicts']}, unchecked {live['unchecked']}")
    print(f"logs_gg.entry_id:      {obs['resolved']} rows from {obs['observed']} "
          f"observations ({len(set(o[0] for o in observations))} distinct entry_ids)")
    if obs["unresolved"]:
        print(f"    ⚠ {len(obs['unresolved'])} entry_id(s) NOT in "
              f"CharacterAdvancement.dbc: {obs['unresolved'][:10]}")
    if obs["name_mismatch"]:
        print(f"    ⚠ {len(obs['name_mismatch'])} name mismatch(es) vs the CA table "
              f"- the rank chain is authoritative, the name is not:")
        for entry_id, crawled, ca_name in obs["name_mismatch"][:5]:
            print(f"        {entry_id}: crawl {crawled!r} vs CA {ca_name!r}")
    print(f"card_id:               {cards['rows']} rows (many-to-one with spellId)")
    return ca, live, obs, cards


def validate(conn):
    """Re-run the checks behind Phase 0 Task 5's verdict, against current data."""
    print("Phase 0 Task 5 checks, re-run against the live database:\n")

    observed = {e for e, _r, _n, _v in observed_entry_ids()}
    catalog = {r[0] for r in conn.execute("SELECT id FROM spells")}
    collisions = observed & catalog
    print(f"  distinct entry_ids observed on live characters : {len(observed)}")
    print(f"  ...that are also a catalog spells.id           : {len(collisions)} "
          f"{sorted(collisions) if collisions else ''}")
    for entry_id in sorted(collisions):
        crawl_name = conn.execute(
            "SELECT notes FROM spell_id_crosswalk WHERE external_source='logs_gg.entry_id' "
            "AND external_id=? LIMIT 1", (str(entry_id),)).fetchone()
        cat_name = conn.execute("SELECT name FROM spells WHERE id=?", (entry_id,)).fetchone()
        print(f"      {entry_id}: catalog says {cat_name[0]!r}; "
              f"crosswalk says {crawl_name[0] if crawl_name else '(unresolved)'}")
        print("      ^ a numeric collision is NOT a match - this is the false friend "
              "the never-join rule exists for")

    resolved = conn.execute(
        "SELECT COUNT(DISTINCT external_id) FROM spell_id_crosswalk "
        "WHERE external_source='logs_gg.entry_id'").fetchone()[0]
    print(f"\n  entry_ids resolving through CharacterAdvancement: {resolved}/{len(observed)}")

    reachable = conn.execute("""
        SELECT COUNT(*) FROM spells s WHERE EXISTS (
            SELECT 1 FROM spell_id_crosswalk x
            WHERE x.external_source='character_advancement' AND x.spell_id = s.id)
    """).fetchone()[0]
    total = conn.execute("SELECT COUNT(*) FROM spells").fetchone()[0]
    print(f"  catalog ids reachable from some CA rank slot   : {reachable}/{total}")

    conflicts = conn.execute(
        "SELECT external_source, COUNT(*) FROM spell_id_crosswalk "
        "WHERE confidence='conflict' GROUP BY 1").fetchall()
    print(f"\n  rows at confidence='conflict' (surfaced, NOT resolved): "
          f"{dict(conflicts) if conflicts else 'none'}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--resolve", type=int, metavar="ENTRY_ID",
                    help="resolve an entry_id through to the spell a level-60 casts")
    ap.add_argument("--rank", type=int, help="card rank held, with --resolve")
    ap.add_argument("--spell", type=int, metavar="SPELL_ID",
                    help="every external id pointing at this spell")
    ap.add_argument("--validate", action="store_true",
                    help="re-run Phase 0 Task 5's checks instead of rebuilding")
    args = ap.parse_args()

    if not DB_PATH.exists():
        print(f"no database at {DB_PATH} - run py cli/rebuild.py", file=sys.stderr)
        return 1
    conn = connect(DB_PATH)

    if args.resolve is not None:
        hits = xw.resolve_entry_id(conn, args.resolve, args.rank)
        if not hits:
            print(f"entry_id {args.resolve}: no mapping - is it in "
                  f"CharacterAdvancement.dbc?")
            return 1
        for hit in hits:
            if hit["level_rank_ambiguous"]:
                print(f"entry_id {hit['entry_id']} rank {hit['card_rank']}"
                      f" -> card spell {hit['card_spell_id']}"
                      f" -> level-60 spell AMBIGUOUS, candidates "
                      f"{hit['level_spell_candidates']} - resolve by hand, do not pick one")
                continue
            name = conn.execute("SELECT name FROM spells WHERE id=?",
                                (hit["level_spell_id"],)).fetchone()
            print(f"entry_id {hit['entry_id']} rank {hit['card_rank']}"
                  f" -> card spell {hit['card_spell_id']}"
                  f" -> level-60 spell {hit['level_spell_id']}"
                  f"{'  (rank differs!)' if hit['level_rank_differs'] else ''}"
                  f"   {name[0] if name else '(not in catalog)'}")
            print(f"    {hit['notes']}")
        return 0

    if args.spell is not None:
        for row in xw.external_ids_for(conn, args.spell):
            print(f"{row['external_source']:24s} {row['external_id']:>10s} "
                  f"rank={row['rank']}  {row['confidence']}")
        return 0

    if args.validate:
        validate(conn)
        return 0

    if not table_exists(conn, "dbc_character_advancement"):
        print("dbc_character_advancement missing - run ingest/dbc/load_extract.py first",
              file=sys.stderr)
        return 1

    build(conn)
    print("\nby source:")
    for row in xw.summary(conn):
        print(f"  {row['external_source']:24s} {row['rows']:>7} rows, "
              f"{row['distinct_external_ids']:>6} distinct ids, "
              f"{row['conflicts']} conflict(s)")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
