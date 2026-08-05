#!/usr/bin/env python3
"""Run the simulation tiers against a build fixture (Phase 2 T5/T12).

    py cli/sim.py --build fixtures/build_elric_paladin.json \
                  --apl fixtures/apl_paladin_optimal.json \
                  --content raid_boss_st --tier medium

    py cli/sim.py --build ... --compare-apl fixtures/apl_paladin_observed.json
    py cli/sim.py --build ... --weights            # T7 stat weights
    py cli/sim.py --build ... --paths              # T7 path comparison
    py cli/sim.py --build ... --uncertainty        # T6 knowledge uncertainty

No logic lives here: it loads JSON, calls `core/sim`, and formats. Anything that
decides something belongs in `core/`.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config  # noqa: E402
from core.db.connection import connect  # noqa: E402
from core.builds.spec import BuildSpec, SlottedCard, GearItem  # noqa: E402
from core.builds.stats import compute_stats  # noqa: E402
from core.sim import combat_engine as ce  # noqa: E402
from core.sim.apl import APL, APLEntry  # noqa: E402
from core.sim.content import Role, get_preset, PRESETS  # noqa: E402
from core.sim.tiers import fast_sim, medium_sim, slow_sim  # noqa: E402


def load_build(path):
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    gear = {}
    for slot, w in (d.get("weapons") or {}).items():
        gear[slot] = GearItem(item_id=0, name=f"{slot} (fixture)", slot=slot,
                              stats={}, weapon=w)
    spec = BuildSpec(
        character_level=d["character_level"], role=Role(d.get("role", "dps")),
        path=d["path"],
        abilities=[SlottedCard(a["spell_id"], a["rank"]) for a in d["abilities"]],
        talents=[SlottedCard(t["spell_id"], t["rank"]) for t in d["talents"]],
        gear=gear, stats_override=d.get("stats_override"),
        realm=d.get("realm", "Darkmoon"), season=d.get("season", "S10"),
        source=d.get("source", "user_designed"))
    return spec, d


def load_apl(path):
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    return APL(name=d["name"], provenance=d.get("provenance", "unstated"),
               entries=[APLEntry(spell_id=e["spell_id"],
                                 conditions=e.get("conditions", []),
                                 off_gcd=e.get("off_gcd", False),
                                 comment=e.get("comment", ""))
                        for e in d["entries"]])


def show(result, title, top=12):
    print(f"\n=== {title}")
    print(f"    {result.primary_metric.value}: "
          f"{result.primary_value:,.0f}   (content: {result.content.name}, "
          f"{result.content.fight_duration:g}s, "
          f"{result.content.target.count} target(s) at level "
          f"{result.content.target.level})")
    rows = sorted(result.per_ability.items(), key=lambda kv: -kv[1]["damage"])
    total = sum(r["damage"] for _, r in rows) or 1.0
    print(f"\n    {'ability':30}{'casts':>7}{'damage':>12}{'share':>8}  notes")
    for sid, r in rows[:top]:
        note = "ATTRIBUTED" if r.get("attributed") else ""
        if r.get("unresolved_events"):
            note = (note + " +UNRESOLVED-EVENTS").strip()
        print(f"    {r['name'][:29]:30}{r['casts']:>7.1f}{r['damage']:>12,.0f}"
              f"{100 * r['damage'] / total:>7.1f}%  {note}")
    if result.combat_rng:
        c = result.combat_rng
        print(f"\n    combat RNG ({c['iterations']} iterations): 95% of pulls "
              f"land {c['p2_5_dps']:,.0f}-{c['p97_5_dps']:,.0f} DPS "
              f"(sd {c['sd_dps']:,.0f})")


def show_warnings(result, limit=25):
    seen, out = set(), []
    for w in result.warnings:
        if w not in seen:
            seen.add(w)
            out.append(w)
    print(f"\n--- warnings ({len(out)} distinct)")
    for w in out[:limit]:
        print(f"  * {w}")
    if len(out) > limit:
        print(f"  ... and {len(out) - limit} more")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--build", required=True)
    ap.add_argument("--apl")
    ap.add_argument("--compare-apl")
    ap.add_argument("--content", default="raid_boss_st",
                    choices=sorted(PRESETS))
    ap.add_argument("--tier", default="medium",
                    choices=("fast", "medium", "slow", "all"))
    ap.add_argument("--iterations", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--weights", action="store_true", help="T7 stat weights")
    ap.add_argument("--paths", action="store_true", help="T7 path comparison")
    ap.add_argument("--uncertainty", action="store_true",
                    help="T6 knowledge-uncertainty propagation")
    ap.add_argument("--samples", type=int, default=300)
    ap.add_argument("--quiet-warnings", action="store_true")
    args = ap.parse_args()

    conn = connect(config.DB_PATH)
    spec, raw = load_build(args.build)
    content = get_preset(args.content)
    conv = ce.load_rating_conversions(conn, level=spec.character_level)
    cs = compute_stats(spec, content, conv)

    print(f"build: {raw.get('name', args.build)}  path={spec.path}  "
          f"level={spec.character_level}")
    for u in raw.get("unresolved", []):
        print(f"  ! UNRESOLVED: {u}")

    apl = load_apl(args.apl) if args.apl else None

    if args.weights:
        from core.sim.weights import stat_weights
        w = stat_weights(conn, spec, content, cs, apl=apl)
        print(f"\n=== stat weights ({content.name}, "
              f"normalised to {w['normalised_to']})")
        print(f"    {'stat':22}{'weight':>9}{'dps/point':>12}   note")
        for name, row in w["weights"].items():
            print(f"    {name:22}{row['weight']:>9.2f}{row['dps_per_point']:>12.3f}"
                  f"   {row.get('note', '')}")
        for note in w["warnings"]:
            print(f"  ! {note}")
        return 0

    if args.paths:
        from core.sim.weights import compare_paths
        res = compare_paths(conn, spec, content, apl=apl)
        print(f"\n=== path comparison ({content.name})")
        print(f"    {'path':16}{'dps':>10}{'vs current':>12}")
        for name, row in res["paths"].items():
            print(f"    {name:16}{row['dps']:>10,.0f}{row['delta_pct']:>11.1f}%")
        for note in res["warnings"]:
            print(f"  ! {note}")
        return 0

    if args.uncertainty:
        from core.sim.uncertainty import sim_with_uncertainty, sensitivity
        u = sim_with_uncertainty(conn, spec, content, cs, apl=apl,
                                 samples=args.samples, seed=args.seed)
        print(f"\n=== knowledge uncertainty ({u['samples']} samples, "
              f"{content.name})")
        print(f"    nominal {u['nominal']:,.0f} DPS")
        print(f"    range   {u['low']:,.0f} - {u['high']:,.0f}  "
              f"(90% CI {u['ci_low']:,.0f} - {u['ci_high']:,.0f})")
        print(f"    spread  +/-{u['spread_pct']:.1f}% of nominal")
        print("\n    THIS IS NOT COMBAT VARIANCE. It is how much the answer "
              "moves because\n    we do not know the inputs. Run --tier slow "
              "for the combat-RNG spread.")
        print("\n=== sensitivity: what is worth measuring, most valuable first")
        for row in sensitivity(conn, spec, content, cs, apl=apl,
                               samples=args.samples, seed=args.seed):
            print(f"    {row['parameter'][:46]:48}"
                  f"{row['variance_contribution_pct']:>6.1f}%  "
                  f"{row['note']}")
        return 0

    if apl is None:
        from core.sim.apl_gen import generate_apl
        apl = generate_apl(conn, spec, content, cs)
        print(f"  (no --apl given; auto-generated: {apl.provenance})")

    results = []
    if args.tier in ("fast", "all"):
        results.append((fast_sim(conn, spec, content, cs, apl=apl),
                        f"FAST  [{apl.name}]"))
    if args.tier in ("medium", "all"):
        results.append((medium_sim(conn, spec, apl, content, cs),
                        f"MEDIUM  [{apl.name}]"))
    if args.tier in ("slow", "all"):
        results.append((slow_sim(conn, spec, apl, content, cs,
                                 iterations=args.iterations, seed=args.seed),
                        f"SLOW  [{apl.name}]"))
    for res, title in results:
        show(res, title)
    if not args.quiet_warnings and results:
        show_warnings(results[-1][0])

    if args.compare_apl:
        other = load_apl(args.compare_apl)
        a = medium_sim(conn, spec, apl, content, cs)
        b = medium_sim(conn, spec, other, content, cs)
        show(b, f"MEDIUM  [{other.name}]")
        da, db = a.primary_value, b.primary_value
        print(f"\n=== APL comparison ({content.name})")
        print(f"    {apl.name:24}{da:>12,.0f}")
        print(f"    {other.name:24}{db:>12,.0f}")
        if db:
            print(f"    delta                   {da - db:>12,.0f}  "
                  f"({100 * (da / db - 1):+.1f}% for {apl.name})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
