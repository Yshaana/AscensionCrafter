"""Corpus search and analysis (Phase 3 Task 3).

All functions take a builds.db connection. Cards are matched by SPELL ID
(resolved at rebuild time through the crosswalk) or raw entry_id — never by
name (hard rule; two spells named alike are unrelated abilities).

Cohort honesty: performance rows aggregate per capture SCOPE (see corpus.py) —
`content_type` filters through the scope's single encounter where one exists,
and grouped scopes carry NULL content_type rather than a guess.
"""
from datetime import datetime, timezone


def _latest_snapshots(conn):
    """One snapshot per character: the most recent."""
    return """
        SELECT cs.* FROM character_snapshots cs
        JOIN (SELECT character_id, MAX(captured_at) AS m
              FROM character_snapshots GROUP BY character_id) latest
          ON latest.character_id = cs.character_id AND latest.m = cs.captured_at
    """


def find_builds(conn, abilities=None, talents=None, path=None, role=None,
                content_type=None, min_dps=None, source=None,
                max_staleness_days=None):
    """Snapshots carrying ALL the requested cards, with best observed DPS.

    `abilities` / `talents`: iterables of spell ids (level or card spell id
    both match) or raw entry_id strings/ints.
    """
    wanted = []
    for tree, ids in (("abilities", abilities), ("talents", talents)):
        for x in ids or []:
            wanted.append((tree, str(x)))

    sql = f"WITH latest AS ({_latest_snapshots(conn)}) SELECT latest.* FROM latest WHERE 1=1"
    params = []
    for tree, x in wanted:
        sql += """ AND EXISTS (
            SELECT 1 FROM snapshot_cards sc
            WHERE sc.snapshot_id = latest.snapshot_id AND sc.tree = ?
              AND (CAST(sc.spell_id AS TEXT) = ? OR CAST(sc.card_spell_id AS TEXT) = ?
                   OR sc.external_id = ?))"""
        params += [tree, x, x, x]
    if path:
        sql += " AND lower(latest.path) = lower(?)"
        params.append(path)
    if role:
        sql += " AND lower(COALESCE(latest.spec_role,'')) LIKE lower(?)"
        params.append(f"%{role}%")
    if source:
        sql += " AND latest.source = ?"
        params.append(source)
    if max_staleness_days is not None:
        cutoff = datetime.now(timezone.utc).timestamp() - max_staleness_days * 86400
        cutoff_iso = datetime.fromtimestamp(cutoff, timezone.utc).isoformat()
        sql += " AND latest.captured_at >= ?"
        params.append(cutoff_iso)

    cols = [d[0] for d in conn.execute("SELECT * FROM character_snapshots LIMIT 0").description]
    out = []
    for row in conn.execute(sql, params):
        snap = dict(zip(cols, row))
        perf = conn.execute("""
            SELECT MAX(ep.dps), MAX(ep.hps) FROM encounter_performance ep
            LEFT JOIN capture_scopes cs ON cs.scope_id = ep.scope_id
            LEFT JOIN encounters e ON e.encounter_id = cs.encounter_id
            WHERE ep.character_id = ? AND (? IS NULL OR e.content_type = ?)
        """, (snap["character_id"], content_type, content_type)).fetchone()
        snap["best_dps"], snap["best_hps"] = perf
        snap.pop("gear_stats_json", None)
        if min_dps is None or (snap["best_dps"] or 0) >= min_dps:
            out.append(snap)
    out.sort(key=lambda s: s.get("best_dps") or 0, reverse=True)
    return out


def co_occurrence(conn, spell_id, tree=None, min_carriers=5, limit=30):
    """Cards appearing alongside `spell_id` far above their base rate.

    Market-basket lift over latest snapshots: lift = P(other | target) /
    P(other). High lift = players who run the target disproportionately also
    run the other card — discovered synergy, subject to review.
    """
    x = str(spell_id)
    base = conn.execute(
        f"WITH latest AS ({_latest_snapshots(conn)}) SELECT COUNT(*) FROM latest").fetchone()[0]
    carriers = conn.execute(f"""
        WITH latest AS ({_latest_snapshots(conn)})
        SELECT COUNT(DISTINCT latest.snapshot_id) FROM latest
        JOIN snapshot_cards sc ON sc.snapshot_id = latest.snapshot_id
        WHERE CAST(sc.spell_id AS TEXT) = ? OR CAST(sc.card_spell_id AS TEXT) = ?
              OR sc.external_id = ?""", (x, x, x)).fetchone()[0]
    if carriers < min_carriers or not base:
        return {"spell_id": spell_id, "carriers": carriers,
                "verdict": "insufficient_sample", "rows": []}

    rows = conn.execute(f"""
        WITH latest AS ({_latest_snapshots(conn)}),
        target AS (
            SELECT DISTINCT latest.snapshot_id FROM latest
            JOIN snapshot_cards sc ON sc.snapshot_id = latest.snapshot_id
            WHERE CAST(sc.spell_id AS TEXT) = ? OR CAST(sc.card_spell_id AS TEXT) = ?
                  OR sc.external_id = ?),
        counts AS (
            SELECT sc.external_id, MIN(sc.name) AS name, MIN(sc.tree) AS tree,
                   COUNT(DISTINCT sc.snapshot_id) AS everywhere,
                   COUNT(DISTINCT CASE WHEN sc.snapshot_id IN (SELECT snapshot_id FROM target)
                                       THEN sc.snapshot_id END) AS with_target
            FROM snapshot_cards sc
            WHERE sc.snapshot_id IN (SELECT snapshot_id FROM latest)
              AND (? IS NULL OR sc.tree = ?)
            GROUP BY sc.external_id)
        SELECT external_id, name, tree, with_target, everywhere,
               (1.0 * with_target / ?) / (1.0 * everywhere / ?) AS lift
        FROM counts
        WHERE with_target >= 3 AND everywhere < ?    -- drop universal staples
        ORDER BY lift DESC, with_target DESC LIMIT ?
    """, (x, x, x, tree, tree, carriers, base, base, limit)).fetchall()
    return {"spell_id": spell_id, "carriers": carriers, "population": base,
            "verdict": "ok",
            "rows": [{"external_id": r[0], "name": r[1], "tree": r[2],
                      "with_target": r[3], "everywhere": r[4],
                      "lift": round(r[5], 2)} for r in rows]}


def ability_performance_percentiles(conn, spell_id, content_type=None):
    """Damage-share distribution for one ability across characters.

    Tight spread = the ability does what it does; wide = build-sensitive."""
    shares = [r[0] for r in conn.execute("""
        SELECT ap.damage_share_pct FROM ability_performance ap
        LEFT JOIN capture_scopes cs ON cs.scope_id = ap.scope_id
        LEFT JOIN encounters e ON e.encounter_id = cs.encounter_id
        WHERE ap.spell_id = ? AND ap.damage_share_pct IS NOT NULL
          AND (? IS NULL OR e.content_type = ?)
        ORDER BY ap.damage_share_pct""", (spell_id, content_type, content_type))]
    if len(shares) < 10:
        return {"spell_id": spell_id, "n": len(shares), "verdict": "insufficient_sample"}

    def pct(p):
        return round(shares[min(len(shares) - 1, int(len(shares) * p))], 2)
    return {"spell_id": spell_id, "n": len(shares), "verdict": "ok",
            "p10": pct(.10), "p25": pct(.25), "p50": pct(.50),
            "p75": pct(.75), "p90": pct(.90),
            "spread_p90_p10": round(pct(.90) - pct(.10), 2)}


def meta_snapshot(conn, tree=None, limit=40):
    """What is played right now: card carry-rates over latest snapshots."""
    base = conn.execute(
        f"WITH latest AS ({_latest_snapshots(conn)}) SELECT COUNT(*) FROM latest").fetchone()[0]
    rows = conn.execute(f"""
        WITH latest AS ({_latest_snapshots(conn)})
        SELECT sc.external_id, MIN(sc.name), MIN(sc.tree),
               COUNT(DISTINCT sc.snapshot_id) AS carriers
        FROM snapshot_cards sc
        WHERE sc.snapshot_id IN (SELECT snapshot_id FROM latest)
          AND (? IS NULL OR sc.tree = ?)
        GROUP BY sc.external_id ORDER BY carriers DESC LIMIT ?""",
        (tree, tree, limit)).fetchall()
    return {"population": base,
            "rows": [{"external_id": r[0], "name": r[1], "tree": r[2],
                      "carriers": r[3],
                      "carry_rate_pct": round(100 * r[3] / base, 1) if base else None}
                     for r in rows]}


def outliers(conn, metric="dps", content_type=None, min_cohort=8, limit=20):
    """Characters far above their (boss, content) cohort — scouting targets."""
    col = {"dps": "ep.dps", "hps": "ep.hps"}[metric]
    rows = conn.execute(f"""
        SELECT e.boss_name, e.content_type, ep.character_id, c.name, {col} AS v,
               ep.path
        FROM encounter_performance ep
        JOIN capture_scopes cs ON cs.scope_id = ep.scope_id
        JOIN encounters e ON e.encounter_id = cs.encounter_id
        LEFT JOIN characters c ON c.character_id = ep.character_id
        WHERE {col} IS NOT NULL AND e.is_trash = 0
          AND (? IS NULL OR e.content_type = ?)""",
        (content_type, content_type)).fetchall()
    cohorts = {}
    for boss, ct, cid, name, v, path in rows:
        cohorts.setdefault((boss, ct), []).append((cid, name, v, path))
    out = []
    for (boss, ct), members in cohorts.items():
        if len(members) < min_cohort:
            continue
        vals = [m[2] for m in members]
        mean = sum(vals) / len(vals)
        var = sum((x - mean) ** 2 for x in vals) / max(1, len(vals) - 1)
        sd = var ** 0.5
        if not sd:
            continue
        for cid, name, v, path in members:
            z = (v - mean) / sd
            if z >= 2.0:
                out.append({"boss": boss, "content_type": ct, "character_id": cid,
                            "name": name, metric: round(v, 1), "path": path,
                            "cohort_n": len(members), "cohort_mean": round(mean, 1),
                            "z": round(z, 2)})
    out.sort(key=lambda r: r["z"], reverse=True)
    return out[:limit]


def path_performance(conn, content_type=None):
    """Real DPS distribution per Path — empirical check on compare_paths()."""
    rows = conn.execute("""
        SELECT ep.path, COUNT(*), AVG(ep.dps), MAX(ep.dps)
        FROM encounter_performance ep
        LEFT JOIN capture_scopes cs ON cs.scope_id = ep.scope_id
        LEFT JOIN encounters e ON e.encounter_id = cs.encounter_id
        WHERE ep.dps IS NOT NULL AND ep.path IS NOT NULL
          AND (? IS NULL OR e.content_type = ?)
        GROUP BY ep.path ORDER BY 3 DESC""", (content_type, content_type)).fetchall()
    return [{"path": r[0], "samples": r[1], "avg_dps": round(r[2], 1),
             "max_dps": round(r[3], 1)} for r in rows]


def item_usage(conn, slot=None, path=None, limit=20):
    """What top performers actually wear. Feeds Task 4's cross-validation."""
    rows = conn.execute(f"""
        WITH latest AS ({_latest_snapshots(conn)})
        SELECT sg.slot, sg.item_id, MIN(sg.item_name), COUNT(DISTINCT sg.snapshot_id) AS n
        FROM snapshot_gear sg
        JOIN latest ON latest.snapshot_id = sg.snapshot_id
        WHERE (? IS NULL OR sg.slot = ?) AND (? IS NULL OR lower(latest.path) = lower(?))
        GROUP BY sg.slot, sg.item_id ORDER BY n DESC LIMIT ?""",
        (slot, slot, path, path, limit)).fetchall()
    return [{"slot": r[0], "item_id": r[1], "item_name": r[2], "wearers": r[3]}
            for r in rows]


def role_distribution(conn):
    """How many crawled characters are tanks/healers — sizes non-DPS support."""
    rows = conn.execute(f"""
        WITH latest AS ({_latest_snapshots(conn)})
        SELECT COALESCE(spec_role, 'unknown'), COUNT(*) FROM latest GROUP BY 1
        ORDER BY 2 DESC""").fetchall()
    return [{"spec_role": r[0], "characters": r[1]} for r in rows]
