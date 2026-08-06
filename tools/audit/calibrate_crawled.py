"""
calibrate_crawled.py — the ≥3-real-characters calibration gate (Phase 3 exit).

    py tools/audit/calibrate_crawled.py [--limit 12]

PHASE_2 §8.2 moved this criterion to 3a because simulating a crawled character
needs gear, and gear is Phase 3 T4's `items` table. That dependency is now
satisfied: `snapshot_gear` carries resolved per-slot stat blocks, so a crawled
character can be built as a real `BuildSpec` and simmed in COMPONENT mode
(gear + path + talents), with no invented stats.

Tolerance is `predictions/CALIBRATION_TOLERANCE.md`'s, unchanged and not
re-derived here: **±20% aggregate DPS**.

🛑 Three honesty rules this tool enforces structurally, because each is a way
the gate could be passed without meaning anything:

1. **Candidates are chosen before results are seen.** Selection is by data
   completeness only — gear stats resolved, cards resolved, an exact (lag-0)
   build-to-parse join, a boss encounter with a real duration. It never ranks
   by how well the sim did.
2. **Build-to-parse staleness is an explicit, reported parameter.**
   `--max-lag-hours` defaults to **0** (the snapshot was captured AT that
   encounter, so it IS the build that produced the parse). Any looser value is
   printed in the header and the per-character lag is in the table, because a
   lagged snapshot is a different build wearing the same name. ⚠ Measured
   2026-08-06: at lag 0 the corpus yields **one** level-60 character, because
   exact-join captures skew heavily toward levelling players — so a run at a
   stated non-zero lag is the only way this gate currently has an n at all,
   and its result must be read with the lag column, not without it.
3. **A character on an impaired system is reported, never silently included.**
   Path of Duality's parses are excluded from absolute calibration by the 2d
   advisory; they are counted and named, not dropped quietly.

The output is a per-mechanism report, per the tolerance file's own rule that a
pass/fail number alone is worth very little.
"""
import argparse
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import config  # noqa: E402
from config import BUILDS_DB_PATH, DATA_DERIVED, DB_PATH  # noqa: E402
from core.builds.gear import normalise_stats  # noqa: E402
from core.builds.spec import BuildSpec, GearItem, SlottedCard  # noqa: E402
from core.builds.stats import compute_stats  # noqa: E402
from core.db.connection import connect  # noqa: E402
from core.sim import combat_engine as ce  # noqa: E402
from core.sim.apl_gen import generate_apl  # noqa: E402
from core.sim.content import Role, get_preset  # noqa: E402
from core.sim.tiers import fast_sim  # noqa: E402

config.ensure_utf8_stdout()

AGGREGATE_TOLERANCE_PCT = 20.0     # predictions/CALIBRATION_TOLERANCE.md
REPORT_PATH = DATA_DERIVED / "calibration_crawled.md"

PATH_TOKEN = {"strength": "Strength", "agility": "Agility", "duality": "Duality",
              "intellect": "Intelligence", "intelligence": "Intelligence",
              "spirit": "Healing", "healing": "Healing"}

# Slot index -> BuildSpec slot name. Only the two the sim reads by name matter;
# everything else contributes stats under its numeric slot.
WEAPON_SLOTS = {16: "main_hand", 17: "off_hand"}


def candidates(conn, limit, max_lag_hours=0.0):
    """Selection is by DATA COMPLETENESS ONLY — never by sim agreement.

    ONE row per character (the longest qualifying encounter), chosen in SQL so
    the limit spans `limit` distinct characters. Taking the limit first and
    deduping after let two chatty characters consume all 40 rows and reduced
    the gate to n=1.

    Level 60 is required, not assumed: every coefficient, rating divisor and
    rank resolution in this stack is level-60. Simming a level-40 character's
    parse against level-60 magnitudes is the pooled-crawl error from `1x`
    (a level-scaled magnitude cannot be compared across unknown levels).
    """
    return conn.execute("""
        SELECT ep.character_id, c.name, ep.snapshot_id, ep.dps, ep.path,
               e.boss_name, e.content_type, e.duration_seconds, e.encounter_id,
               ep.snapshot_lag_hours, c.level,
               MAX(e.duration_seconds) AS _longest
        FROM encounter_performance ep
        JOIN capture_scopes cs ON cs.scope_id = ep.scope_id
        JOIN encounters e ON e.encounter_id = cs.encounter_id
        JOIN characters c ON c.character_id = ep.character_id
        WHERE ep.snapshot_lag_hours IS NOT NULL
          AND ep.snapshot_lag_hours <= ?           -- rule 2, parameterised
          AND ep.dps IS NOT NULL AND ep.dps > 100
          AND e.is_trash = 0 AND e.duration_seconds >= 20
          AND c.level = 60                          -- level-60 model only
          AND EXISTS (SELECT 1 FROM snapshot_gear sg
                       WHERE sg.snapshot_id = ep.snapshot_id
                         AND sg.stats_json IS NOT NULL)
          AND EXISTS (SELECT 1 FROM snapshot_cards sc
                       WHERE sc.snapshot_id = ep.snapshot_id
                         AND sc.spell_id IS NOT NULL)
        GROUP BY ep.character_id
        ORDER BY ep.character_id
        LIMIT ?""", (max_lag_hours, limit)).fetchall()


# content_type -> the sim preset that matches it. Simming a dungeon parse
# against a raid-boss preset compares two different fights.
CONTENT_PRESET = {
    "raid": "raid_boss_st",
    "dungeon_normal": "mythic_dungeon_st",   # nearest single-target dungeon preset
    "dungeon_mythic": "mythic_dungeon_st",
}


def build_spec_for(conn, snapshot_id, path_token):
    gear = {}
    for slot, item_id, name, stats_json in conn.execute(
            "SELECT slot, item_id, item_name, stats_json FROM snapshot_gear "
            "WHERE snapshot_id = ?", (snapshot_id,)):
        stats, _unmapped = normalise_stats(stats_json)
        slot_name = WEAPON_SLOTS.get(slot, f"slot_{slot}")
        gear[slot_name] = GearItem(item_id=item_id, name=name or f"item {item_id}",
                                   slot=slot_name, stats=stats, weapon=None)
    abilities, talents = [], []
    for tree, spell_id, rank in conn.execute(
            "SELECT tree, spell_id, rank FROM snapshot_cards "
            "WHERE snapshot_id = ? AND spell_id IS NOT NULL", (snapshot_id,)):
        card = SlottedCard(spell_id, max(1, rank or 1))
        (abilities if tree == "abilities" else talents).append(card)
    return BuildSpec(
        character_level=60, role=Role("dps"), path=path_token,
        abilities=abilities[:30], talents=talents[:25],
        gear=gear, source="crawled")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--limit", type=int, default=40,
                    help="candidate rows to consider (pre-filtered by completeness)")
    ap.add_argument("--max-lag-hours", type=float, default=0.0,
                    help="max build-snapshot staleness vs the parse (default 0 = "
                         "the snapshot was captured AT that encounter). Any other "
                         "value is reported in the output, never applied silently")
    args = ap.parse_args()

    if not BUILDS_DB_PATH.exists():
        print(f"{BUILDS_DB_PATH} missing — run ingest/logs_gg/build_builds_db.py")
        return 1
    bdb = sqlite3.connect(BUILDS_DB_PATH)
    asc = connect(DB_PATH)
    conv = ce.load_rating_conversions(asc, level=60)

    rows = candidates(bdb, args.limit, args.max_lag_hours)
    print(f"[candidates] {len(rows)} distinct level-60 characters pass the "
          f"completeness filter (max build staleness "
          f"{args.max_lag_hours:g}h)")

    results, excluded, seen_chars = [], [], set()
    for (cid, cname, snapshot_id, dps, path, boss, ctype, dur, enc_id,
         lag, level, _longest) in rows:
        if cid in seen_chars:
            continue          # one encounter per character — no double counting
        preset = CONTENT_PRESET.get(ctype)
        if preset is None:
            excluded.append((cid, cname,
                             f"content_type {ctype!r} has no matching sim preset "
                             f"— simming it against a raid profile would compare "
                             f"two different fights"))
            continue
        content = get_preset(preset)
        token = PATH_TOKEN.get((path or "").lower())
        if token is None:
            excluded.append((cid, cname, f"path {path!r} not resolvable"))
            continue
        if token == "Duality":
            # rule 3: named, not silently dropped
            excluded.append((cid, cname,
                             "Path of Duality — parses excluded from absolute "
                             "calibration by the 2d bug advisory (AP cycles "
                             "mid-parse)"))
            continue
        try:
            spec = build_spec_for(bdb, snapshot_id, token)
            cs = compute_stats(spec, content, conv, conn=asc)
            apl = generate_apl(asc, spec, content, cs)
            res = fast_sim(asc, spec, content, cs, apl=apl)
        except Exception as e:                      # noqa: BLE001 — reported
            excluded.append((cid, cname, f"sim error: {type(e).__name__}: {e}"))
            continue
        seen_chars.add(cid)
        sim_dps = res.primary_value
        delta = 100 * (sim_dps / dps - 1) if dps else None
        results.append({
            "character_id": cid, "name": cname, "path": token, "boss": boss,
            "content_type": ctype, "sim_preset": preset,
            "duration_s": dur, "logged_dps": dps, "snapshot_lag_hours": lag,
            "sim_dps": sim_dps, "delta_pct": delta,
            "within_tolerance": abs(delta) <= AGGREGATE_TOLERANCE_PCT,
            "abilities": len(spec.abilities), "talents": len(spec.talents),
            "gear_pieces": len(spec.gear),
            "top_sim_abilities": [
                r["name"] for _sid, r in
                sorted(res.per_ability.items(), key=lambda kv: -kv[1]["damage"])[:5]],
            "warnings": sorted({w for w in res.warnings})[:8],
        })

    passing = [r for r in results if r["within_tolerance"]]
    print(f"[gate] {len(passing)} of {len(results)} simmed characters within "
          f"±{AGGREGATE_TOLERANCE_PCT:g}%  "
          f"(criterion: ≥3)  -> {'PASS' if len(passing) >= 3 else 'NOT MET'}")

    lines = [
        "# Calibration gate — crawled characters",
        "",
        "Inherited from PHASE_2 §8.2: *the sim reproduces ≥3 real characters "
        f"within ±{AGGREGATE_TOLERANCE_PCT:g}% aggregate DPS* "
        "(`predictions/CALIBRATION_TOLERANCE.md`, unchanged).",
        "",
        f"**Result: {len(passing)} of {len(results)} within tolerance — "
        f"{'PASS' if len(passing) >= 3 else 'NOT MET'}.**",
        "",
        "Candidates were selected by data completeness only (level 60, resolved "
        "gear stats, resolved cards, a non-trash encounter ≥20s), never by how "
        "well the sim did.",
        "",
        f"**Build-to-parse staleness allowed: {args.max_lag_hours:g}h.** At the "
        "strict setting (0h — the snapshot was captured at that very encounter) "
        "this corpus yields exactly ONE level-60 character, because exact-join "
        "captures skew toward levelling players. Read the lag column.",
        "",
        "| character | path | boss | build lag (h) | logged DPS | sim DPS | delta | within ±20% |",
        "|---|---|---|---:|---:|---:|---:|---|",
    ]
    for r in sorted(results, key=lambda r: abs(r["delta_pct"] or 1e9)):
        lines.append(
            f"| {r['name']} ({r['character_id']}) | {r['path']} | {r['boss']} "
            f"| {r['snapshot_lag_hours']:.1f} "
            f"| {r['logged_dps']:,.0f} | {r['sim_dps']:,.0f} "
            f"| {r['delta_pct']:+.1f}% | {'yes' if r['within_tolerance'] else 'NO'} |")

    lines += ["", "## Excluded, and why", ""]
    for cid, cname, why in excluded[:40]:
        lines.append(f"- {cname} ({cid}): {why}")
    if not excluded:
        lines.append("- none")

    lines += ["", "## Per-character detail (mechanism, not just a delta)", ""]
    for r in results:
        lines += [
            f"### {r['name']} ({r['character_id']}) — {r['path']}",
            f"- {r['boss']}, {r['content_type']} (sim preset {r['sim_preset']}), "
            f"{r['duration_s']:.0f}s; "
            f"{r['abilities']} abilities / {r['talents']} talents / "
            f"{r['gear_pieces']} gear pieces resolved",
            f"- logged {r['logged_dps']:,.0f} vs sim {r['sim_dps']:,.0f} "
            f"({r['delta_pct']:+.1f}%)",
            f"- sim's top abilities: {', '.join(r['top_sim_abilities'])}",
        ]
        for w in r["warnings"]:
            lines.append(f"  - ⚠ {w}")
        lines.append("")
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"[report] {REPORT_PATH}")

    (DATA_DERIVED / "calibration_crawled.json").write_text(
        json.dumps({"results": results, "excluded": excluded,
                    "tolerance_pct": AGGREGATE_TOLERANCE_PCT,
                    "passing": len(passing)}, indent=1, default=str),
        encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
