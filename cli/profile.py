#!/usr/bin/env python3
"""Thin CLI over core/spells/profile.py :: spell_profile() (Phase 1 T7).

    py cli/profile.py "Hammer from the Heavens"
    py cli/profile.py 907300 --fast
    py cli/profile.py 907300 --json          # full structured dump

Default output is a human-readable digest; --json prints the whole dict.
Real-usage joins attach automatically when data/derived/scouted_builds.db
exists.
"""
import argparse
import json
import sqlite3
import sys
from pathlib import Path

# Windows picks cp1252 for piped/redirected stdout and dies on ⚠/🛑 — the same
# trap rebuild.py fixed in 1b (there via env for child processes).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import DB_PATH, SCOUTED_DB_PATH  # noqa: E402
from core.spells.profile import spell_profile  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("spell", help="spell name or catalog id")
    ap.add_argument("--fast", action="store_true", help="skip graph/volatility/usage")
    ap.add_argument("--json", action="store_true", help="dump the full dict as JSON")
    ap.add_argument("--depth", type=int, default=2, help="graph neighbourhood depth")
    args = ap.parse_args()

    conn = sqlite3.connect(str(DB_PATH))
    scouted = sqlite3.connect(str(SCOUTED_DB_PATH)) if SCOUTED_DB_PATH.exists() else None
    p = spell_profile(conn, args.spell, depth=args.depth,
                      mode="fast" if args.fast else "full", scouted_conn=scouted)

    if args.json:
        print(json.dumps(p, indent=2, default=str))
        return 0
    if not p.get("found"):
        print(f"not found: {args.spell}")
        return 1
    if p.get("ambiguous"):
        print(f"⚠ duplicate name — query by id:")
        for c in p["candidates"]:
            print(f"  {c['id']:8} {c['name']} ({c['type']}, {c['schools'] or 'no school'})")
        return 1

    i = p["identity"]
    print(f"{i['name']} (id {i['id']}, {i['type']})  schools: {i['schools'] or '—'}")
    if i["class_origin"]:
        print(f"  class: {i['class_origin']} [{i['class_confidence']}]")
    if i["rank_line"]:
        rl = i["rank_line"]
        print(f"  rank line: level-60 character casts {rl['spell_id']} (rank {rl['rank']})")
    own = p["ownership"]
    if own["owned"]:
        cards = ", ".join(f"{c['pool']} r{c['rank']}" for c in own["cards"])
        print(f"  owned: yes — {cards}")
    else:
        print("  owned: no")

    m = p["mechanics"]
    if m["rank_gap"]:
        print(f"  🛑 RANK GAP: {m['rank_gap']}")
    if m["conflicts"]:
        print(f"  ⚠ CONFLICTS: {json.dumps(m['conflicts'])[:300]}")
    print(f"  mechanics confidence: {m['confidence']}")
    for field in ("school", "cooldown_seconds", "cast_time_seconds", "gcd_type",
                  "resource_type", "aoe_radius", "duration_seconds"):
        if m["fields"].get(field) is not None:
            print(f"    {field}: {m['fields'][field]}  [{m['source_tiers'].get(field)}]")
    for jf in ("damage_formula_terms_json", "healing_formula_terms_json"):
        if m["fields"].get(jf):
            terms = json.loads(m["fields"][jf])
            print(f"    {jf.replace('_json','')}: {len(terms)} term(s)")
            for t in terms[:6]:
                if t.get("term") == "FLAT":
                    print(f"      FLAT {t.get('min')}–{t.get('max')} (via {t.get('via')}, {t.get('confidence')})")
                else:
                    print(f"      {t.get('term')}*{t.get('coefficient')} ({t.get('source')}, rank {t.get('rank')})")

    if p["facts"]:
        print(f"  facts ({len(p['facts'])}):")
        for f in p["facts"][:5]:
            print(f"    [{f['confidence']}] {f['topic']}")
    if p["patch_history"]:
        print(f"  patch history ({len(p['patch_history'])}):")
        for e in p["patch_history"][:5]:
            print(f"    {e['date']} {e['direction']:9} {e['text'][:90]}")
    g = p["gaps"]
    gaps = [k for k, v in g.items() if v and k != "open_questions"]
    if gaps or g["open_questions"]:
        print(f"  gaps: {', '.join(gaps) or '—'}")
        for q in g["open_questions"]:
            print(f"    open question: {q['slug']}")

    if "relationships" in p:
        r = p["relationships"]
        print(f"  graph: {len(r['nodes'])} nodes / {len(r['edges'])} edges within depth {args.depth}")
        v = p["volatility"]
        thin = " (data thin: " + str(v['data_window_days']) + "d window)" if v["data_thin"] else ""
        print(f"  volatility: {v['band']}, {v['touches']} touches{thin}")
        u = p["real_usage"]
        if isinstance(u, list):
            print(f"  real usage: {len(u)} scouted snapshot(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
