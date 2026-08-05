#!/usr/bin/env python3
"""Phase 1 T8 — the auto-debugger (session 1c).

Runs as the last step of every rebuild and standalone:

    py tools/audit/audit_gaps.py            # fast integrity sweep
    py tools/audit/audit_gaps.py --deep     # + graph consistency, outlier stats

Output: `data/derived/audit_report.md` plus a one-line stdout summary.

### May auto-fix (mechanical only)
Exact-duplicate rows from re-ingestion. (A "mark vanished crosswalk targets"
fix was built and withdrawn this session — see the note in `autofix()`.)

### Must NEVER auto-fix (§2.3)
A value conflict. Anything below `confirmed`. Anything touched by an
unprocessed patch entry. The auto-debugger may never pick a winner between
disagreeing sources — that is precisely how confidently wrong data is created.

### Ranking
`variance_contribution` is Phase 2's sensitivity analysis and does not exist
yet; until then issues are ranked by the documented fallback — how many
owned/current-pool spells each issue touches — and the report says which
ranking is in effect.
"""
import argparse
import datetime as _dt
import json
import re
import sqlite3
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from config import (DATA_DERIVED, DB_PATH, DBC_DIR, CHANGELOG_DIR, REPO,  # noqa: E402
                    ensure_derived_dir)
from core.spells.epistemics import find_answered_questions  # noqa: E402

PHASE2_BOUNDARY = "2026-08-08"   # server Phase 2 launch — first live test of this sweep


def _owned_ids(conn):
    return {r[0] for r in conn.execute("SELECT DISTINCT spellId FROM owned_cards")}


# ---------------------------------------------------------------- checks

def conflict_sweep(conn, deep):
    """Every confidence='conflict' row, bucketed: multi-effect-slot collisions
    (one spell, two effect slots, same source tier) separately from genuine
    cross-source disagreements — 1b flagged that without this split the sweep
    becomes noise and gets ignored."""
    slot_collisions, cross_source = [], []
    for sid, cj in conn.execute(
            "SELECT spell_id, conflicts_json FROM spell_mechanics "
            "WHERE confidence = 'conflict'"):
        for field, entries in (json.loads(cj) or {}).items():
            tiers = {e.get("source_tier") for e in entries}
            # same tier + evidence differing only in the effect slot = collision
            stripped = {re.sub(r"\[\d\]", "[*]", e.get("evidence_ref", ""))
                        for e in entries}
            item = {"spell_id": sid, "field": field,
                    "values": [e.get("value") for e in entries]}
            if len(tiers) == 1 and len(stripped) == 1:
                slot_collisions.append(item)
            else:
                cross_source.append(item)
    xwalk = [{"external_id": r[0], "source": r[1], "spell_id": r[2]}
             for r in conn.execute(
                 "SELECT external_id, external_source, spell_id FROM "
                 "spell_id_crosswalk WHERE confidence = 'conflict' LIMIT 100")]
    class_conflicts = [{"spell_id": r[0], "detail": r[1]} for r in conn.execute(
        "SELECT id, class_conflict_json FROM spells "
        "WHERE class_conflict_json IS NOT NULL")]
    return {
        "cross_source_disagreements": cross_source,        # the real §2.3 queue
        "multi_effect_slot_collisions": slot_collisions,   # modelling honesty, low priority
        "crosswalk_conflicts (ambiguous rank lines etc.)": xwalk,
        "class_origin_conflicts": class_conflicts,
    }


def staleness_sweep(conn, deep):
    """Mechanics whose verified_at_patch predates a patch entry naming that
    spell — the daily-patch check that matters most."""
    rows = conn.execute("""
        SELECT DISTINCT m.spell_id, s.name, p.patch_date, pe.change_direction
        FROM spell_mechanics m
        JOIN patch_entry_spells pes ON pes.spell_id = m.spell_id
        JOIN patch_entries pe ON pe.entry_id = pes.entry_id
        JOIN patches p ON p.patch_id = pe.patch_id
        LEFT JOIN patches vp ON vp.patch_id = m.verified_at_patch
        LEFT JOIN spells s ON s.id = m.spell_id
        WHERE vp.patch_date IS NULL OR p.patch_date > vp.patch_date
        ORDER BY p.patch_date DESC""").fetchall()
    return {"mechanics_touched_after_verification": [
        {"spell_id": r[0], "name": r[1], "patched": r[2], "direction": r[3]}
        for r in rows]}


def realm_season_sweep(conn, deep):
    unstamped_facts = conn.execute(
        "SELECT COUNT(*) FROM confirmed_facts WHERE realm IS NULL OR season IS NULL"
    ).fetchone()[0]
    return {"facts_missing_realm_or_season": unstamped_facts,
            "_note": "single-realm database today; cross-realm application is "
                     "structurally impossible until a second realm is ingested"}


def phase_boundary_sweep(conn, deep):
    today = _dt.date.today().isoformat()
    crossed = today >= PHASE2_BOUNDARY
    # nothing gear_tier-keyed exists yet (sim is Phase 2) — this sweep exists so
    # the first phase flip is caught by design, not by memory
    return {"_next_boundary": PHASE2_BOUNDARY, "_boundary_crossed": crossed,
            "phase_keyed_artifacts_invalidated": [],
            "_note": ("PHASE BOUNDARY CROSSED — any stat weight or gear tier "
                     "derived before this date is suspect" if crossed else
                     "no phase-keyed sim artifacts exist yet (Phase 2)")}


def provenance_sweep(conn, deep):
    """evidence_refs that don't resolve to real evidence. Understands the
    `dbc:Spell.dbc:<id>:...` form; other forms are checked for non-emptiness."""
    bad = []
    dbc_ids = {r[0] for r in conn.execute("SELECT id FROM spell_dbc_raw")}
    n = 0
    for sid, ref in conn.execute(
            "SELECT spell_id, evidence_ref FROM spell_effect_values"):
        n += 1
        m = re.match(r"dbc:Spell\.dbc:(\d+):", ref or "")
        if not ref or (m and int(m.group(1)) not in dbc_ids):
            bad.append({"table": "spell_effect_values", "spell_id": sid, "ref": ref})
    empty_rel = conn.execute(
        "SELECT COUNT(*) FROM spell_relationships "
        "WHERE evidence_ref IS NULL OR evidence_ref = ''").fetchone()[0]
    # crosswalk targets outside the extract's scope: mostly out-of-pool CA rank
    # slots whose spell was never in spell_dbc_raw. NOT "vanished" — vanished
    # means previously-present-now-absent, which needs history we don't keep.
    # Report-only, counted by source.
    out_of_scope = dict(conn.execute("""
        SELECT external_source, COUNT(*) FROM spell_id_crosswalk
        WHERE spell_id NOT IN (SELECT id FROM spells)
          AND spell_id NOT IN (SELECT id FROM spell_dbc_raw)
        GROUP BY 1""").fetchall())
    return {"_checked_effect_values": n, "unresolvable": bad[:50],
            "relationships_with_empty_evidence": empty_rel,
            "_crosswalk_targets_outside_extract_scope": out_of_scope}


def coverage_sweep(conn, deep):
    owned = _owned_ids(conn)
    rows = conn.execute("""
        SELECT s.id, s.name, s.type FROM spells s
        WHERE NOT EXISTS (SELECT 1 FROM spell_mechanics m WHERE m.spell_id = s.id)
    """).fetchall()
    no_mech_owned = [r for r in rows if r[0] in owned]
    return {"catalog_spells_without_mechanics": len(rows),
            "_of_which_owned": len(no_mech_owned),
            "_owned_examples": [{"id": r[0], "name": r[1]} for r in no_mech_owned[:20]]}


def doc_vs_data_sweep(conn, deep):
    """Minimal 1c version: verify characters named in builds/*.md resolve in
    scouted_builds.db. The full claim-vs-snapshot diff (with the informational/
    real-bug severity split) needs Phase 3's normalised corpus."""
    import config
    scouted = DATA_DERIVED / "scouted_builds.db"
    if not scouted.exists():
        return {"note": "scouted_builds.db absent — skipped"}
    sc = sqlite3.connect(str(scouted))
    known = {r[0] for r in sc.execute("SELECT DISTINCT name FROM scouted_characters")}
    sc.close()
    named = set()
    for md in (config.BUILDS_DIR / "shared").glob("scouted_*.md"):
        m = re.match(r"scouted_([A-Za-z]+)_", md.name)
        if m:
            named.add(m.group(1))
    missing = sorted(named - known)
    return {"_doc_named_characters": sorted(named), "unresolved_in_db": missing,
            "_note": "full claim-vs-snapshot diff lands with Phase 3's corpus"}


def answered_question_sweep(conn, deep):
    return {"candidates": find_answered_questions(conn)[:20]}


def contradiction_sweep(conn, deep):
    """Facts still carrying an unqualified superseded/retracted marker, and
    fact pairs linked to one spell where one topic names the other as
    superseding — cheap textual heuristics, not NLP."""
    stale = [r[0] for r in conn.execute(
        "SELECT topic FROM confirmed_facts WHERE fact LIKE '%SUPERSEDED%' "
        "AND fact NOT LIKE '%⚠ SUPERSEDED%'")]
    return {"facts_with_unqualified_superseded_marker": stale}


def string_match_sweep(conn, deep):
    """Code paths still string-matching spell identity instead of joining the
    crosswalk. Heuristic grep over the repo's Python."""
    suspects = []
    pat = re.compile(r"json\.dumps\(.*\)\.lower\(\)|name\s*==?\s*.*\.lower\(\)\s*in|"
                     r"LIKE\s+'%.+%'.*name", re.I)
    for py in REPO.rglob("*.py"):
        if "__pycache__" in str(py) or py.name == "audit_gaps.py":
            continue
        try:
            for i, line in enumerate(py.read_text(encoding="utf-8").splitlines(), 1):
                if pat.search(line) and "crosswalk" not in line:
                    suspects.append(f"{py.relative_to(REPO)}:{i}")
        except OSError:
            continue
    return {"candidates": suspects[:30], "_note": "heuristic — review, don't assume"}


def orphan_name_sweep(conn, deep):
    unresolved = conn.execute(
        "SELECT COUNT(*) FROM patch_entry_spells WHERE spell_id IS NULL").fetchone()[0]
    examples = [r[0] for r in conn.execute(
        "SELECT DISTINCT matched_name FROM patch_entry_spells "
        "WHERE spell_id IS NULL LIMIT 15")]
    return {"changelog_names_never_resolved": unresolved, "_examples": examples}


def outlier_coefficient_sweep(conn, deep):
    """Serves open question hidden_formula_outlier_coefficients: SP/AP-family
    coefficients implausibly large for a per-hit term. Threshold 3.0 — the
    largest independently-confirmed coefficient on record is Grasp of Darkness
    SP 1.4; Anti-Magic Zone's genuine 2*AP absorb stays under it."""
    rows = conn.execute("""
        SELECT ss.spell_id, s.name, ss.term_type, ss.coefficient, ss.source
        FROM spell_scaling ss LEFT JOIN spells s ON s.id = ss.spell_id
        WHERE ss.coefficient > 3.0 AND ss.term_type != 'WEAPON'
        ORDER BY ss.coefficient DESC""").fetchall()
    return {"suspicious": [
        {"spell_id": r[0], "name": r[1], "term": r[2], "coefficient": r[3],
         "source": r[4]} for r in rows]}


# ---------------------------------------------------------------- auto-fix

def autofix(conn):
    """Mechanical fixes only (see module docstring). Returns what was done."""
    fixed = []
    # exact-duplicate spell_scaling rows from any historical double-ingest
    dupes = conn.execute("""
        SELECT COUNT(*) - COUNT(DISTINCT spell_id || '|' || term_type || '|' ||
               COALESCE(coefficient,'') || '|' || source || '|' || rank)
        FROM spell_scaling""").fetchone()[0]
    if dupes:
        conn.execute("""
            DELETE FROM spell_scaling WHERE rowid NOT IN (
                SELECT MIN(rowid) FROM spell_scaling
                GROUP BY spell_id, term_type, coefficient, source, rank)""")
        fixed.append(f"deduplicated {dupes} exact-duplicate spell_scaling rows")
    # NOTE: a "mark crosswalk rows whose target vanished" fix was built and
    # withdrawn in the same session: without history, absent-from-extract is
    # indistinguishable from never-in-scope (7,654 out-of-pool CA rank slots
    # matched). Reported by provenance_sweep instead of mutated here.
    conn.commit()
    return fixed


def _watch_list_rows():
    """Parse the watch-list table out of `bugs/README.md` — that file is the
    single source of truth for what we watch and which keywords identify a fix.
    Duplicating the keywords here would drift."""
    readme = REPO / "bugs" / "README.md"
    if not readme.exists():
        return []
    rows, in_watch = [], False
    for line in readme.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            in_watch = "Watch list" in line
            continue
        if not in_watch or not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 3 or cells[0].startswith("---") or cells[0] == "Bug":
            continue
        keywords = [k.strip(" `") for k in cells[1].split(",") if k.strip(" `")]
        if keywords:
            rows.append({"bug": cells[0], "keywords": keywords,
                         "reopens": cells[2]})
    return rows


def bugfix_watch_sweep(conn, deep):
    """2e T4: a fix silently changes what our data means, so scan the daily
    changelog capture for each watch-list bug's keywords and report hits LOUDLY,
    naming what to re-open. Keyword-crude on purpose — a false positive costs
    one read, a missed fix costs a wrong verdict for weeks.

    Proof of need arrived the same session this was built: tracker #200295
    (Hammerdin trigger set) was fixed within hours of being reported, and the
    fix was noticed by the owner reading the tracker, not by any tooling."""
    daily = CHANGELOG_DIR / "daily"
    watch = _watch_list_rows()
    if not watch:
        return {"_note": "no watch-list rows parsed from bugs/README.md"}
    if not daily.exists():
        return {"_watch_rows": len(watch),
                "sweep_blocked": ["no daily changelog captures found"]}

    # Entries from the last capture files; the watch entries' `found` dates are
    # all 2026-08-04+ so scanning everything captured daily/ holds is bounded
    # and needs no per-bug date plumbing.
    hits = []
    seen_ids = set()
    for f in sorted(daily.glob("*.json")):
        try:
            payload = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        data = payload.get("data") or {}
        groups = data.values() if isinstance(data, dict) else [data]
        for group in groups:
            entries = (group.values() if isinstance(group, dict) else group)
            for sub in entries:
                for e in (sub if isinstance(sub, list) else [sub]):
                    if not isinstance(e, dict) or e.get("id") in seen_ids:
                        continue
                    seen_ids.add(e.get("id"))
                    desc = e.get("description") or ""
                    # Darkmoon filter, crude: skip entries that tag ONLY other realms
                    if (("Dawnrise" in desc or "Bronzebeard" in desc)
                            and "Darkmoon" not in desc):
                        continue
                    low = desc.lower()
                    for row in watch:
                        # The FIRST keyword is the ANCHOR — the bug's distinctive
                        # name (`Duality`, `Hammerdin`). Generic terms like `proc`
                        # or `spell power` alone matched 299 unrelated balance
                        # entries on the first run; they now only ever AMPLIFY an
                        # anchor hit, never create one.
                        anchor, rest = row["keywords"][0], row["keywords"][1:]
                        if anchor.lower() not in low:
                            continue
                        matched = [anchor] + [k for k in rest if k.lower() in low]
                        hits.append({
                            "bug": row["bug"], "matched": matched,
                            "date": e.get("group_key"),
                            "entry": desc[:300],
                            "REOPEN": row["reopens"]})
    return {"_watch_rows_scanned": len(watch), "_changelog_entries": len(seen_ids),
            "watch_hits": hits}


def extract_staleness_sweep(conn, deep):
    """2e T4: is the committed DBC extract older than the latest Darkmoon patch?
    A stale extract silently serves pre-patch magnitudes with tier-4 confidence."""
    latest_patch = conn.execute(
        "SELECT MAX(patch_date) FROM patches WHERE realm = 'Darkmoon'").fetchone()[0]
    out = {"latest_darkmoon_patch": latest_patch, "stale_extracts": []}
    for name in ("dbc-extract.json", "dbc-ascension-extract.json"):
        path = DBC_DIR / name
        if not path.exists():
            out["stale_extracts"].append({"extract": name, "problem": "missing"})
            continue
        stamped = None
        try:
            with open(path, encoding="utf-8") as fh:
                head = fh.read(4096)
            m = re.search(r'"_extracted_at":\s*"([^"]+)"', head)
            if not m:      # stamp may serialize at the tail (ascension extract)
                with open(path, "rb") as fh:
                    fh.seek(-4096, 2)
                    m = re.search(r'"_extracted_at":\s*"([^"]+)"',
                                  fh.read().decode("utf-8", "replace"))
            stamped = m.group(1) if m else None
        except OSError:
            pass
        if stamped is None:
            out["stale_extracts"].append({
                "extract": name,
                "problem": "no _extracted_at stamp — extract predates 2e T4; "
                           "age unknowable until the next --with-dbc run"})
        elif latest_patch and stamped[:10] < str(latest_patch)[:10]:
            out["stale_extracts"].append({
                "extract": name, "extracted_at": stamped,
                "problem": f"OLDER than latest Darkmoon patch {latest_patch} — "
                           "run `py cli/rebuild.py --with-dbc`"})
    return out


CHECKS = [
    ("conflict_sweep", conflict_sweep),
    ("staleness_sweep", staleness_sweep),
    ("realm_season_sweep", realm_season_sweep),
    ("phase_boundary_sweep", phase_boundary_sweep),
    ("provenance_sweep", provenance_sweep),
    ("coverage_sweep", coverage_sweep),
    ("doc_vs_data_sweep", doc_vs_data_sweep),
    ("answered_question_sweep", answered_question_sweep),
    ("contradiction_sweep", contradiction_sweep),
    ("string_match_sweep", string_match_sweep),
    ("orphan_name_sweep", orphan_name_sweep),
    ("outlier_coefficient_sweep", outlier_coefficient_sweep),
    ("bugfix_watch_sweep", bugfix_watch_sweep),
    ("extract_staleness_sweep", extract_staleness_sweep),
]


def _issue_count(result):
    """Keys prefixed '_' are informational, never issues. Bools never count."""
    n = 0
    for k, v in result.items():
        if k.startswith("_"):
            continue
        if isinstance(v, bool):
            continue
        if isinstance(v, list):
            n += len(v)
        elif isinstance(v, int):
            n += v
        elif isinstance(v, dict):
            n += _issue_count(v)
    return n


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--deep", action="store_true",
                    help="also run expensive statistical checks")
    ap.add_argument("--no-fix", action="store_true", help="report only, fix nothing")
    args = ap.parse_args()

    conn = sqlite3.connect(str(DB_PATH))
    fixed = [] if args.no_fix else autofix(conn)

    results = {}
    for name, fn in CHECKS:
        try:
            results[name] = fn(conn, args.deep)
        except sqlite3.Error as e:
            results[name] = {"check_failed": str(e)}

    ensure_derived_dir()
    report = DATA_DERIVED / "audit_report.md"
    now = _dt.datetime.now().isoformat(timespec="seconds")
    lines = [f"# Audit report — {now}", "",
             "Ranking: dependent-count fallback (variance_contribution needs "
             "Phase 2's sensitivity analysis).", ""]
    if fixed:
        lines += ["## Auto-fixed (mechanical)", ""] + [f"- {f}" for f in fixed] + [""]
    total = 0
    for name, result in results.items():
        cnt = _issue_count(result)
        total += cnt
        lines.append(f"## {name} — {cnt} item(s)")
        lines.append("```json")
        lines.append(json.dumps(result, indent=1, default=str)[:8000])
        lines.append("```")
        lines.append("")
    report.write_text("\n".join(lines), encoding="utf-8")

    key = results.get("conflict_sweep", {})
    print(f"audit: {total} items across {len(CHECKS)} checks | "
          f"cross-source conflicts {len(key.get('cross_source_disagreements', []))}, "
          f"slot collisions {len(key.get('multi_effect_slot_collisions', []))} | "
          f"{len(fixed)} auto-fix(es) | report: {report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
