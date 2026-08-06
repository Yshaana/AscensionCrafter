#!/usr/bin/env python3
"""Build `spell_relationships` + bounded trigger attribution (Phase 1 T5).

    py cli/relationships.py

Thin wrapper over `core/spells/relationships.py`. Runs in the rebuild chain
after `cli/crosswalk.py` and BEFORE `cli/mechanics.py` — the trigger-attributed
`spell_effect_values` rows written here are inputs to the mechanics resolver.

Validations (fail loudly, never silently): the graph must reproduce the four
known exclusivity buckets and the documented Lightbound Cleave → Cleave
borrowing, and the bounded trigger walk must attribute Hammer from the Heavens
(`282987`, raw 2–25 +2.4/level) to its cards — the project's known worked
example (PHASE_1 T4/T5).
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config  # noqa: E402
import season_config  # noqa: E402
from config import DB_PATH  # noqa: E402
from core.db.connection import connect, table_exists, transaction  # noqa: E402
from core.db.schema import create_phase1_schema  # noqa: E402
from core.spells import relationships as rel  # noqa: E402

# Realm/season come from season_config.py — the ONE place they are written down
# (3d A1). Re-exported under the local names so existing call sites are unchanged.
REALM = season_config.REALM
SEASON = season_config.SEASON

SCRAPE = config.DATA_SOURCE / "ascension_db" / "spell_pages.ndjson"


def load_scraped_records():
    """The committed db.ascension.gg capture, or [] if this clone lacks it.

    Absent is not an error — the edges it adds are additive, and every other
    source still builds. `core/` cannot read this itself (it takes data, not
    paths), so the file IO lives here.
    """
    if not SCRAPE.exists():
        return []
    out = []
    with SCRAPE.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def latest_patch_id(conn):
    row = conn.execute(
        "SELECT patch_id FROM patches WHERE realm = ? ORDER BY patch_date DESC "
        "LIMIT 1", (REALM,)).fetchone()
    return row[0] if row else None


def validate(conn):
    failures = []

    # All multi-member buckets must appear as edge groups. A single-member
    # bucket (Holy Focus: "does not stack with other similar effects", other
    # members unknown) has no pairwise relationship to express — it stays in
    # the `exclusivity_buckets` staging table as the record of the clause.
    multi_member = conn.execute(
        """SELECT COUNT(*) FROM (SELECT bucket_id FROM exclusivity_buckets
           GROUP BY bucket_id HAVING COUNT(*) >= 2)""").fetchone()[0]
    distinct_buckets = conn.execute(
        """SELECT COUNT(DISTINCT json_extract(condition_json, '$.bucket_id'))
           FROM spell_relationships
           WHERE relation_type = 'shares_exclusivity_bucket'""").fetchone()[0]
    if distinct_buckets < multi_member:
        failures.append(f"exclusivity buckets in graph: {distinct_buckets}, "
                        f"expected every multi-member bucket ({multi_member})")

    lc = conn.execute(
        """SELECT COUNT(*) FROM spell_relationships r
           JOIN spells s ON s.id = r.source_spell_id
           WHERE s.name = 'Lightbound Cleave'
             AND r.relation_type = 'borrows_modifiers'
             AND r.target_name = 'Cleave'""").fetchone()[0]
    if lc == 0:
        failures.append("Lightbound Cleave -> Cleave borrows_modifiers edge "
                        "missing (documented proof case, primer §4)")

    # 282987 has two magnitude-bearing slots; the school-damage one must decode
    # to 2-25 +2.4/level (session 1x resolved formula). DBC floats are float32,
    # so per_level compares with tolerance, never equality.
    hfth = conn.execute(
        """SELECT DISTINCT spell_id FROM spell_effect_values
           WHERE source_spell_id = 282987 AND via LIKE 'trigger_hop%'
             AND effect_index = 0 AND flat_min = 2.0 AND flat_max = 25.0
             AND ABS(per_level - 2.4) < 1e-4""").fetchall()
    if not hfth:
        failures.append("Hammer from the Heavens (282987) school-damage slot "
                        "(2-25, +2.4/level) not attributed to any card")
    return failures


def main():
    if not DB_PATH.exists():
        print(f"no database at {DB_PATH} - run py cli/rebuild.py first",
              file=sys.stderr)
        return 1
    conn = connect(DB_PATH)
    for required in ("spell_dbc_raw", "spell_effect_values", "modifier_links",
                     "talent_amplifiers", "exclusivity_buckets"):
        if not table_exists(conn, required):
            print(f"{required} missing - run the earlier chain steps first",
                  file=sys.stderr)
            return 1
    create_phase1_schema(conn)

    stamp = {"realm": REALM, "season": SEASON, "patch_id": latest_patch_id(conn)}
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    scraped = load_scraped_records()
    with transaction(conn):
        stats = rel.populate_all(conn, stamp, now, scraped_records=scraped)

    total = conn.execute("SELECT COUNT(*) FROM spell_relationships").fetchone()[0]
    by_type = conn.execute(
        "SELECT relation_type, COUNT(*) FROM spell_relationships "
        "GROUP BY relation_type ORDER BY 2 DESC").fetchall()
    print(f"spell_relationships: {total} edges")
    for relation, count in by_type:
        print(f"  {relation}: {count}")
    st = stats["scraped_triggers"]
    print(f"db.ascension.gg trigger edges: {st['new']} NEW "
          f"({st['already_known']} already carried by the client's own "
          f"EffectTriggerSpell, which wins the row)")
    amp = stats["amplifiers"]
    print(f"amplifier staging rows skipped pending manual review: "
          f"{amp['skipped_review']}")
    att = stats["trigger_attribution"]
    print(f"trigger attribution (bounded depth {rel.MAX_TRIGGER_DEPTH}, "
          f"single-path only): {att['rows']} magnitude rows "
          f"({att['hop1']} 1-hop, {att['hop2']} 2-hop) across "
          f"{att['cards_with_attribution']} cards; "
          f"{att['ambiguous_skipped']} multi-path targets skipped unattributed")

    failures = validate(conn)
    if failures:
        print("VALIDATION FAILED:", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1
    print("validation OK: every multi-member exclusivity bucket + Lightbound "
          "Cleave->Cleave + Hammer from the Heavens attribution all reproduce")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
