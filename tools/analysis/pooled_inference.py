"""
pooled_inference.py — Phase 3 Task 2 runner: the crawl corpus as a standing sweep.

    py tools/analysis/pooled_inference.py [--limit 50]

Reads data/derived/builds.db (built by ingest/logs_gg/build_builds_db.py) plus
ascension.db read-only (anchors, crosswalk, patch history). Writes:

  * `inference_findings` staging rows in builds.db — proposals with sample
    sizes and intervals. 🛑 NOTHING here auto-seeds `spell_mechanics`; a human
    promotes a finding by seeding it (seed_spell_flags.py / seed_confirmed.py)
    and marking the row promoted.
  * data/derived/inference_report.md — the human-readable review queue.

Crit-table anchors come from `doc_confirmed_mechanics` (crit_table='spell'),
expanded through the crosswalk to the level-60 sibling ids that combat logs
actually name. The melee anchor is Auto Attack (spell_id -1 in log space).
"""
import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import config  # noqa: E402
from config import BUILDS_DB_PATH, DATA_DERIVED, DB_PATH  # noqa: E402
from core.builds import inference  # noqa: E402

config.ensure_utf8_stdout()

REPORT_PATH = DATA_DERIVED / "inference_report.md"


def spell_anchor_ids(asc):
    """Doc-confirmed spell-table ids, expanded to their level-60 siblings."""
    base = [r[0] for r in asc.execute(
        "SELECT spell_id FROM doc_confirmed_mechanics "
        "WHERE field = 'crit_table' AND value_text = 'spell' AND confidence = 'confirmed'")]
    expanded = set(base)
    for sid in base:
        for (live,) in asc.execute(
                "SELECT spell_id FROM spell_id_crosswalk "
                "WHERE external_source = 'catalog_vs_live' AND external_id = ? "
                "AND confidence != 'conflict'", (str(sid),)):
            expanded.add(live)
    return expanded


def patch_touched_fn(asc):
    """spell_id -> tuple of patch dates whose entries matched that spell.
    Name-matched (low-confidence) links are still worth a split flag — a wrong
    split costs sample size, an unsplit real change poisons the pool."""
    rows = asc.execute("""
        SELECT pes.spell_id, p.patch_date
        FROM patch_entry_spells pes
        JOIN patch_entries pe ON pe.entry_id = pes.entry_id
        JOIN patches p ON p.patch_id = pe.patch_id
        WHERE pes.spell_id IS NOT NULL
    """).fetchall()
    by_spell = {}
    for sid, date in rows:
        by_spell.setdefault(sid, set()).add(date)

    def fn(spell_id):
        return tuple(sorted(by_spell.get(spell_id, ())))
    return fn


def write_report(conn, results, anchors, path):
    lines = [
        "# Pooled mechanics inference — review queue",
        "",
        f"Generated {datetime.now(timezone.utc).isoformat()} by "
        "`tools/analysis/pooled_inference.py`. **Staging only — a human promotes.**",
        "",
        f"Spell-table anchors used: {sorted(anchors)}; melee anchor: Auto Attack (-1).",
        "",
        "| spell_id | name | pooled hits | chars | crit_table | hit_check | partial_resist |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in results:
        lines.append(f"| {r['spell_id']} | {r['spell_name']} | {r['pooled_hits']} "
                     f"| {r['characters']} | {r['crit_table']} | {r['hit_check']} "
                     f"| {r['partial_resist']} |")

    lines += ["", "## Proposals (promotable)", ""]
    props = conn.execute(
        "SELECT question, spell_id, spell_name, verdict, sample_size, character_count, "
        "ci_low, ci_high FROM inference_findings WHERE verdict LIKE 'propose:%' "
        "ORDER BY sample_size DESC").fetchall()
    for q, sid, name, verdict, n, chars, lo, hi in props:
        ci = f", 95% CI [{lo:.4f}, {hi:.4f}]" if lo is not None else ""
        lines.append(f"- **{name or sid}** ({sid}) — {q}: `{verdict}` "
                     f"(n={n}{', chars=' + str(chars) if chars else ''}{ci})")
    lines += ["",
              "## Immune-like targets (all-or-nothing full resists — immunity, not a roll)",
              ""]
    for (sid, name, detail) in conn.execute(
            "SELECT spell_id, spell_name, detail_json FROM inference_findings "
            "WHERE question = 'rolls_hit_check'"):
        d = json.loads(detail or "{}")
        if d.get("immune_like_target_count"):
            lines.append(f"- {name or sid} ({sid}): {d['immune_like_target_count']} "
                         f"enemy unit(s) full-resisted every pulse while landing zero")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=50)
    args = ap.parse_args()

    if not BUILDS_DB_PATH.exists():
        print(f"{BUILDS_DB_PATH} missing — run ingest/logs_gg/build_builds_db.py first")
        return 1
    if not DB_PATH.exists():
        print(f"{DB_PATH} missing — run py cli/rebuild.py first")
        return 1

    conn = sqlite3.connect(BUILDS_DB_PATH)
    asc = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    inference.init_staging(conn)

    anchors = spell_anchor_ids(asc)
    print(f"[anchors] {len(anchors)} spell-table anchor ids: {sorted(anchors)}")

    results = inference.run_sweep(conn, anchors, limit=args.limit,
                                  patch_touched=patch_touched_fn(asc))
    conn.commit()

    n_prop = sum(1 for r in results
                 for v in (r["crit_table"], r["hit_check"], r["partial_resist"])
                 if str(v).startswith("propose:"))
    n_refuse = sum(1 for r in results
                   for v in (r["crit_table"], r["hit_check"], r["partial_resist"])
                   if str(v).startswith("insufficient"))
    write_report(conn, results, anchors, REPORT_PATH)
    print(f"[sweep] {len(results)} abilities: {n_prop} proposals, "
          f"{n_refuse} honest refusals -> {REPORT_PATH}")
    conn.close()
    asc.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
