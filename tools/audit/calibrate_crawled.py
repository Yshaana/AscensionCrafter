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
   lagged snapshot is a different build wearing the same name.

   ⚠ **Corpus-size caveat, learned the hard way on 2026-08-06.** Against a
   mid-backfill corpus this filter left exactly ONE level-60 character, and
   that looked like a structural property of the data ("exact-join captures
   skew toward levelling players"). It was not — it was small-sample. After the
   backfill completed the same strict filter yields **41**. The lesson is
   general enough to keep: *a filter that starves on a partial corpus is not
   evidence that the filter is too strict.* Prefer re-running on more data over
   loosening a constraint.
3. **A character on an impaired system is reported, never silently included.**
   Path of Duality's parses are excluded from absolute calibration by the 2d
   advisory; they are counted and named, not dropped quietly.
4. **Buffs are DERIVED, never fitted** (3b pre-flight §0.3). A measured buff
   applies only when a participant in the same capture scope holds the
   granting card on a linked board (`core/builds/group_buffs.py`); every
   character is also simmed unbuffed so the layer's contribution is visible.
   The derivation is an explicit lower bound — unlinked boards and unmeasured
   buffs contribute nothing, and a remaining miss is information about the
   next missing mechanism, not a licence to scale this one.

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
from core.builds.gear import (  # noqa: E402
    gear_coverage, missing_stat_budget_bound, normalise_stats,
    slot_budget_medians)
from core.builds.group_buffs import derive_buffs  # noqa: E402
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
               ep.snapshot_lag_hours, c.level, ep.scope_id,
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
    for slot, item_id, name, stats_json, weapon_json in conn.execute(
            "SELECT slot, item_id, item_name, stats_json, weapon_json "
            "FROM snapshot_gear WHERE snapshot_id = ?", (snapshot_id,)):
        stats, _unmapped = normalise_stats(stats_json)
        slot_name = WEAPON_SLOTS.get(slot, f"slot_{slot}")
        # weapon damage lives only in the item description, and without it the
        # sim gives a crawled character no weapon at all — zeroing white swings
        # and every weapon-percent ability
        weapon = json.loads(weapon_json) if weapon_json else None
        gear[slot_name] = GearItem(item_id=item_id, name=name or f"item {item_id}",
                                   slot=slot_name, stats=stats, weapon=weapon)
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


def modelled_damage_share(conn, scope_id, character_id, sim_spell_ids):
    """Of the damage this character ACTUALLY dealt, what fraction came from
    spells the sim produced any damage for?

    This is the third leg of the miss decomposition (PLAN_3B §5.2) and the one
    that tests the revised hypothesis directly: if the sim reproduces a
    character's gear and buffs but only knows magnitudes for 15% of what they
    actually pressed, the miss is per-ability coverage, not stats.

    Pet rows are counted in the denominator — the character's logged DPS
    includes them, so excluding them here would flatter the coverage number.
    """
    rows = conn.execute(
        "SELECT spell_id, spell_name, damage_total, is_pet, spell_school "
        "FROM ability_performance "
        "WHERE scope_id = ? AND character_id = ? AND damage_total > 0",
        (scope_id, character_id)).fetchall()
    total = sum(r[2] for r in rows)
    if not total:
        return None
    has_autos = any(k in sim_spell_ids for k in ("auto_mh", "auto_oh"))

    def is_modelled(r):
        if r[0] in sim_spell_ids:
            return True
        # The log renders auto-attacks as NEGATIVE ids the sim never uses — it
        # keys its swing layer 'auto_mh'/'auto_oh'. Matching on id alone
        # therefore scored every character's white damage as unmodelled and
        # understated coverage by ~9 points.
        #
        # ⚠ Not every negative id is an ordinary swing: extra-attack procs from
        # trinkets and weapons log the same way ('Auto Attack [Hand of
        # Justice]'), and the sim does NOT model those. The discriminator is
        # taken from the row itself rather than from the id's magnitude — a
        # bracket tag that equals the row's own school is a school-flavoured
        # swing, anything else names an item.
        if r[0] >= 0 or not has_autos:
            return False
        name = r[1] or ""
        if "[" not in name:
            return True                       # plain 'Auto Attack'
        tag = name[name.index("[") + 1:].rstrip("]").strip()
        return tag.lower() == (r[4] or "").lower()

    modelled = sum(r[2] for r in rows if is_modelled(r))
    unmodelled = sorted((r for r in rows if not is_modelled(r)),
                        key=lambda r: -r[2])
    return {
        "logged_abilities": len(rows),
        "modelled_abilities": sum(1 for r in rows if is_modelled(r)),
        "modelled_damage_pct": round(100.0 * modelled / total, 1),
        "top_unmodelled": [
            {"spell_id": r[0], "name": r[1], "is_pet": bool(r[3]),
             "share_pct": round(100.0 * r[2] / total, 1)}
            for r in unmodelled[:6]],
    }


def decompose_miss(*, delta_pct, coverage, budget_bound, buff_gain_pct,
                   modelled):
    """Name what the one-directional negative delta can and cannot be.

    🛑 Deliberately produces a VERDICT PER MECHANISM, not a split that sums to
    the miss. Apportioning a multiplicative shortfall across three candidate
    causes would require knowing the answer; what is available is whether each
    cause is *capable* of explaining the size of the miss, which is enough to
    eliminate candidates. Nothing here is fitted or subtracted from a sim run.
    """
    legs = {}
    cov = coverage["coverage_pct"]
    shortfall = (budget_bound or {}).get("estimated_budget_shortfall_pct") or 0.0
    if cov is not None and cov >= 99.9:
        legs["gear_resolution"] = (
            "ELIMINATED — 100% of stat-bearing slots resolved; the sim ran on "
            "this character's whole gear set")
    elif shortfall and abs(delta_pct or 0) > 2 * shortfall:
        legs["gear_resolution"] = (
            f"INSUFFICIENT — {cov:.0f}% of slots resolved, an estimated "
            f"{shortfall:.0f}% of stat budget missing, against a "
            f"{delta_pct:+.0f}% miss. Contributes; cannot account for it")
    else:
        legs["gear_resolution"] = (
            f"CANDIDATE — only {cov:.0f}% of slots resolved (est. {shortfall:.0f}% "
            f"of stat budget missing), comparable to the {delta_pct:+.0f}% miss")
    legs["buffs"] = (
        f"MEASURED at {buff_gain_pct:+.1f}% — the derived layer's whole "
        f"contribution" + (", which cannot account for the miss"
                           if abs(buff_gain_pct) < abs(delta_pct or 0) / 2
                           else ""))
    if modelled is None:
        legs["magnitude_coverage"] = "UNKNOWN — no per-ability rows for this scope"
    elif modelled["modelled_damage_pct"] < 50:
        legs["magnitude_coverage"] = (
            f"DOMINANT — the sim has magnitudes for only "
            f"{modelled['modelled_damage_pct']:.0f}% of the damage this "
            f"character actually dealt "
            f"({modelled['modelled_abilities']}/{modelled['logged_abilities']} "
            f"abilities)")
    else:
        legs["magnitude_coverage"] = (
            f"PARTIAL — {modelled['modelled_damage_pct']:.0f}% of logged damage "
            f"comes from abilities the sim modelled")
    return legs


def _median(xs):
    xs = sorted(x for x in xs if x is not None)
    return xs[len(xs) // 2] if xs else None


def _decomposition_section(results):
    """The corpus-level answer to 'what is the miss made of', built only from
    per-character verdicts — no apportioning, no fitted scale factor."""
    if not results:
        return []
    full_gear = [r for r in results if (r["gear_coverage_pct"] or 0) >= 99.9]
    modelled = [r["modelled"]["modelled_damage_pct"] for r in results
                if r["modelled"]]
    # A character can land inside tolerance while the sim reproduces almost
    # none of what they actually pressed — the modelled fraction happens to
    # total the right number. That is compensating error, not calibration, and
    # the ±20% criterion is structurally blind to it. Reported alongside the
    # criterion, never substituted for it: moving a gate's definition after
    # seeing the result is how a gate stops meaning anything.
    passing = [r for r in results if r["within_tolerance"]]
    qualified = [r for r in passing
                 if (r["modelled"] or {}).get("modelled_damage_pct", 0) >= 50]
    lines = [
        "", "## Miss decomposition (PLAN_3B §5.2)", "",
        f"🛑 **Read the pass with its coverage.** {len(passing)} characters are "
        f"within ±{AGGREGATE_TOLERANCE_PCT:g}%, but only **{len(qualified)}** of "
        f"them are within tolerance *while the sim also reproduces ≥50% of the "
        f"damage they actually dealt*"
        + (": " + ", ".join(
            f"{r['name']} ({r['delta_pct']:+.0f}%, "
            f"{r['modelled']['modelled_damage_pct']:.0f}% modelled)"
            for r in qualified) if qualified else "")
        + ". The rest agree on the total while missing most of the kit — the "
        "modelled slice happens to sum to about the right number. The ±20% "
        "criterion cannot distinguish that from calibration, so the qualified "
        "count is reported next to it and neither replaces the other.", "",
        "The one-directional negative delta is decomposed into the three "
        "mechanisms that each produce it, so no single cause is credited "
        "wholesale. Each leg gets a **verdict on whether it is capable of "
        "explaining a miss this size** — deliberately not a split summing to "
        "the miss, which would require knowing the answer.", "",
        f"- **Gear resolution.** Median gear-stat coverage across the gate's "
        f"characters is **{_median([r['gear_coverage_pct'] for r in results]):.0f}%**, "
        f"and **{len(full_gear)} of {len(results)}** resolve **100%** of their "
        f"stat-bearing slots. Those characters were simmed on their entire real "
        f"gear set, so gear under-resolution is **eliminated** for them — and "
        f"their median delta is "
        f"**{_median([r['delta_pct'] for r in full_gear]):+.0f}%**. "
        f"⚠ Coverage is reportable but not repairable from the corpus: an "
        f"unresolved item is unresolved on every snapshot, because those ids "
        f"are absent from the upstream item database.",
        f"- **Buffs.** The derived layer moves sim DPS by a median of "
        f"**{_median([r['buff_gain_pct'] for r in results]):+.1f}%** "
        f"(max {max((r['buff_gain_pct'] for r in results), default=0):+.1f}%).",
        f"- **Magnitude coverage.** The sim produces damage for a median of "
        f"**{_median(modelled):.0f}%** of what these characters actually dealt"
        + (f" (n={len(modelled)} with per-ability rows)." if modelled else "."),
        "",
        "| leg | characters where it is the stated verdict |",
        "|---|---|",
    ]
    for leg in ("gear_resolution", "buffs", "magnitude_coverage"):
        buckets = {}
        for r in results:
            head = r["miss_decomposition"][leg].split(" —")[0]
            buckets.setdefault(head, []).append(r["name"])
        cell = "; ".join(f"**{k}** {len(v)}" for k, v in
                         sorted(buckets.items(), key=lambda kv: -len(kv[1])))
        lines.append(f"| {leg} | {cell} |")

    unmodelled = {}
    for r in results:
        for u in (r["modelled"] or {}).get("top_unmodelled", []):
            e = unmodelled.setdefault((u["spell_id"], u["name"]),
                                      {"chars": 0, "share": 0.0})
            e["chars"] += 1
            e["share"] += u["share_pct"]
    if unmodelled:
        lines += [
            "", "### Biggest unmodelled abilities across the gate", "",
            "Ranked by how much of their owners' real damage the sim produces "
            "nothing for. This is the shortlist the next magnitude work should "
            "read — it is measured demand, not a guess at what matters.", "",
            "| spell | id | characters | mean share of their damage |",
            "|---|---:|---:|---:|"]
        for (sid, name), e in sorted(unmodelled.items(),
                                     key=lambda kv: -kv[1]["share"])[:20]:
            lines.append(f"| {name} | {sid} | {e['chars']} | "
                         f"{e['share'] / e['chars']:.1f}% |")
    return lines


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

    slot_medians = slot_budget_medians(bdb)
    rows = candidates(bdb, args.limit, args.max_lag_hours)
    print(f"[candidates] {len(rows)} distinct level-60 characters pass the "
          f"completeness filter (max build staleness "
          f"{args.max_lag_hours:g}h)")

    results, excluded, seen_chars = [], [], set()
    for (cid, cname, snapshot_id, dps, path, boss, ctype, dur, enc_id,
         lag, level, scope_id, _longest) in rows:
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
        # 3b pre-flight §0.3: the buff layer, DERIVED from the group in the
        # same capture scope (never guessed, never fitted). The unbuffed sim
        # runs alongside so the layer's effect is visible per character.
        buff_keys, buff_prov = derive_buffs(bdb, scope_id, cid, snapshot_id)
        try:
            spec = build_spec_for(bdb, snapshot_id, token)
            cs0 = compute_stats(spec, content, conv, conn=asc)
            apl = generate_apl(asc, spec, content, cs0)
            res0 = fast_sim(asc, spec, content, cs0, apl=apl)
            spec.raid_buffs = buff_keys
            if buff_keys:
                cs = compute_stats(spec, content, conv, conn=asc)
                res = fast_sim(asc, spec, content, cs, apl=apl)
            else:
                cs, res = cs0, res0
        except Exception as e:                      # noqa: BLE001 — reported
            excluded.append((cid, cname, f"sim error: {type(e).__name__}: {e}"))
            continue
        seen_chars.add(cid)
        sim_dps = res.primary_value
        delta = 100 * (sim_dps / dps - 1) if dps else None
        # PLAN_3B §5.2 — decompose the miss instead of attributing it wholesale
        cov = gear_coverage(bdb, snapshot_id)
        bound = missing_stat_budget_bound(bdb, snapshot_id, coverage=cov,
                                          slot_medians=slot_medians)
        buff_gain = (100 * (sim_dps / res0.primary_value - 1)
                     if res0.primary_value else 0.0)
        modelled = modelled_damage_share(bdb, scope_id, cid,
                                         set(res.per_ability.keys()))
        results.append({
            "character_id": cid, "name": cname, "path": token, "boss": boss,
            "content_type": ctype, "sim_preset": preset,
            "duration_s": dur, "logged_dps": dps, "snapshot_lag_hours": lag,
            "sim_dps": sim_dps, "delta_pct": delta,
            "sim_dps_unbuffed": res0.primary_value,
            "buffs_applied": buff_keys,
            "buff_provenance": buff_prov,
            "within_tolerance": abs(delta) <= AGGREGATE_TOLERANCE_PCT,
            "gear_coverage_pct": cov["coverage_pct"],
            "gear_unresolved_pieces": len(cov["missing"]),
            "gear_name_matched_pieces": len(cov["name_matched"]),
            "gear_budget_shortfall_pct": bound.get("estimated_budget_shortfall_pct"),
            "buff_gain_pct": buff_gain,
            "modelled": modelled,
            "miss_decomposition": decompose_miss(
                delta_pct=delta, coverage=cov, budget_bound=bound,
                buff_gain_pct=buff_gain, modelled=modelled),
            "abilities": len(spec.abilities), "talents": len(spec.talents),
            "gear_pieces": len(spec.gear),
            "top_sim_abilities": [
                r["name"] for _sid, r in
                sorted(res.per_ability.items(), key=lambda kv: -kv[1]["damage"])[:5]],
            "warnings": sorted({w for w in res.warnings})[:8],
        })

    passing = [r for r in results if r["within_tolerance"]]
    qualified = [r for r in passing
                 if (r["modelled"] or {}).get("modelled_damage_pct", 0) >= 50]
    print(f"[gate] {len(passing)} of {len(results)} simmed characters within "
          f"±{AGGREGATE_TOLERANCE_PCT:g}%  "
          f"(criterion: ≥3)  -> {'PASS' if len(passing) >= 3 else 'NOT MET'}")
    print(f"[gate] of those, {len(qualified)} also have ≥50% of their real "
          f"damage modelled — the rest pass by compensating error")

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
        f"**Build-to-parse staleness allowed: {args.max_lag_hours:g}h** "
        + ("(strict — every snapshot below was captured AT its own encounter, "
           "so it IS the build that produced the parse)."
           if args.max_lag_hours == 0 else
           "(LOOSENED — a lagged snapshot is a different build wearing the same "
           "name; read the lag column before trusting any row)."),
        "",
        f"Directional summary: **{sum(1 for r in results if (r['delta_pct'] or 0) < 0)} "
        f"of {len(results)} deltas are negative.** A one-sided distribution is a "
        "missing multiplicative layer, not noise.",
        "",
        "Buffs are DERIVED from the group in the same capture scope — a buff "
        "applies only when a participant's linked board holds the granting "
        "card (`core/builds/group_buffs.py`). This is a lower bound: unlinked "
        "boards and unmeasured buffs contribute nothing, and nothing is fitted.",
        "",
        "| character | path | boss | build lag (h) | logged DPS | sim unbuffed | sim buffed | delta | buffs | gear cov | modelled dmg | within ±20% |",
        "|---|---|---|---:|---:|---:|---:|---:|---|---:|---:|---|",
    ]
    for r in sorted(results, key=lambda r: abs(r["delta_pct"] or 1e9)):
        md = r["modelled"]
        modelled_cell = f"{md['modelled_damage_pct']:.0f}%" if md else "n/a"
        lines.append(
            f"| {r['name']} ({r['character_id']}) | {r['path']} | {r['boss']} "
            f"| {r['snapshot_lag_hours']:.1f} "
            f"| {r['logged_dps']:,.0f} | {r['sim_dps_unbuffed']:,.0f} "
            f"| {r['sim_dps']:,.0f} "
            f"| {r['delta_pct']:+.1f}% | {len(r['buffs_applied'])} "
            f"| {r['gear_coverage_pct']:.0f}% "
            f"| {modelled_cell} "
            f"| {'yes' if r['within_tolerance'] else 'NO'} |")

    lines += _decomposition_section(results)

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
            f"({r['delta_pct']:+.1f}%; unbuffed sim {r['sim_dps_unbuffed']:,.0f})",
            f"- sim's top abilities: {', '.join(r['top_sim_abilities'])}",
            f"- gear: {r['gear_coverage_pct']:.0f}% of stat-bearing slots "
            f"resolved ({r['gear_unresolved_pieces']} unresolved"
            + (f", est. {r['gear_budget_shortfall_pct']:.0f}% of stat budget missing"
               if r['gear_budget_shortfall_pct'] else "")
            + (f"; ⚠ {r['gear_name_matched_pieces']} piece(s) matched by NAME, "
               f"which can land on the wrong difficulty variant"
               if r['gear_name_matched_pieces'] else "") + ")",
        ]
        if r["modelled"]:
            md = r["modelled"]
            lines.append(
                f"- magnitude coverage: sim produces damage for "
                f"**{md['modelled_damage_pct']:.0f}%** of this character's real "
                f"damage ({md['modelled_abilities']}/{md['logged_abilities']} "
                f"logged abilities)")
            if md["top_unmodelled"]:
                lines.append("  - biggest unmodelled: " + ", ".join(
                    f"{u['name']} ({u['spell_id']}) {u['share_pct']:.0f}%"
                    for u in md["top_unmodelled"][:4]))
        lines.append("- miss decomposition:")
        for leg, verdict in r["miss_decomposition"].items():
            lines.append(f"  - **{leg}**: {verdict}")
        prov = r.get("buff_provenance") or {}
        lines.append(
            f"- buffs derived from group: "
            f"{', '.join(r['buffs_applied']) if r['buffs_applied'] else 'none'} "
            f"({prov.get('participants_with_board', 0)} of "
            f"{prov.get('participants', 0)} scope participants have a linked "
            f"board — derivation is a lower bound)")
        for key, grant in (prov.get("applied") or {}).items():
            names = ", ".join(f"{n} (lag {lag:.0f}h)" if lag else n
                              for n, _cid, lag in grant["granted_by"][:4])
            note = f" ⚠ {grant['assumption']}" if grant.get("assumption") else ""
            lines.append(f"  - {key}: held by {names}{note}")
        if prov.get("not_derivable"):
            lines.append(
                f"  - not derivable (no visible holder): "
                f"{', '.join(prov['not_derivable'])}")
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
