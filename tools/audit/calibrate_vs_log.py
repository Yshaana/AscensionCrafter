#!/usr/bin/env python3
"""Phase 2 T8 (partial) — calibrate the sim against real combat logs.

    py tools/audit/calibrate_vs_log.py --character Elric "<log>" ["<log>" ...]
    py tools/audit/calibrate_vs_log.py --character Elric --all-logs

Compares the sim's BASE per-event value (no talent multipliers, no crit) against
the logged NON-CRIT average for the same ability, and reports the ratio. Because
talents are the one large thing 2b does not model, that ratio IS the unmodelled
talent multiplier — and PHASE_2 T8's rule is to report the delta per mechanism
rather than a pass/fail, so the output groups by school and never averages the
groups together.

🛑 **Field alignment is verified before any number is reported.** The parser in
`tools/log_parser/` is documented as unvalidated against a real Ascension log,
and an earlier ad-hoc scan in session 2b read the crit flag one field off. The
check below asserts three independently doc-confirmed facts (periodic effects at
0% crit; melee well below Holystrike) and REFUSES to report if they fail.

3.3.5 field layout, after splitting the body on ',':
  SPELL_DAMAGE  0 event 1 srcGUID 2 srcName 3 srcFlags 4 dstGUID 5 dstName
                6 dstFlags 7 spellId 8 spellName 9 spellSchool 10 amount
                11 overkill 12 school 13 resisted 14 blocked 15 absorbed
                16 CRITICAL 17 glancing 18 crushing
  SWING_DAMAGE  0 event 1 srcGUID 2 srcName 3 srcFlags 4 dstGUID 5 dstName
                6 dstFlags 7 amount 8 overkill 9 school 10 resisted 11 blocked
                12 absorbed 13 CRITICAL 14 glancing 15 crushing
"""
import argparse
import collections
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import config  # noqa: E402
from core.db.connection import connect  # noqa: E402
from core.sim.ability_model import resolve_ability, AbilityResolutionError  # noqa: E402
from core.sim.content import get_preset  # noqa: E402
from core.builds.stats import CharState  # noqa: E402

DEFAULT_LOG_DIR = Path(r"E:\Ascension Launcher\resources\ascension-live\Logs")

# Logged ability name -> the spell id to resolve, where the name alone is wrong
# or ambiguous. Hammer from the Heavens is out of catalog and reached only via a
# trigger, so it is resolved through Hammerdin, whose ONLY damage is that pulse.
NAME_OVERRIDES = {
    "Hammer from the Heavens": 282983,
    "Hour of Judgement": 282984,
    "Lightbound Cleave": 907300,
    "Dawn Strike": 907894,
    "Whirling Light": 907780,
    "Dawnreaver": 903158,
    "Holy Shock": 20473,
    "Consecration": 26573,
    "Seal of Command": 20375,
    "Seal of Vengeance": 31801,
    "Holy Finish": 904880,
    "Judgement of The Three Hammers": 280210,
    "Blades of Light": 913444,
}

# Which event of a multi-event ability the logged line corresponds to.
EVENT_PICKER = {
    "Hammer from the Heavens": "attributed",   # the triggered pulse
    "Hour of Judgement": "own",                # its own periodic tick
}

# Doc-confirmed facts used as the field-alignment gate (primer §1).
ALIGNMENT_ZERO_CRIT = ("Consecration", "Righteous Vengeance", "Hour of Judgement")


def scan_log(path, character):
    """Per-ability non-crit/crit damage samples for one character."""
    dmg = collections.defaultdict(lambda: {"hit": [], "crit": []})
    casts = collections.Counter()
    quoted = f'"{character}"'
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if quoted not in line:
                continue
            parts = line.split("  ", 1)
            if len(parts) != 2:
                continue
            f = parts[1].rstrip().split(",")
            if len(f) < 9 or f[2].strip('"') != character:
                continue
            ev = f[0]
            if ev == "SPELL_CAST_SUCCESS":
                casts[f[8].strip('"')] += 1
            elif ev in ("SPELL_DAMAGE", "SPELL_PERIODIC_DAMAGE", "RANGE_DAMAGE"):
                if len(f) < 17:
                    continue
                try:
                    amt = int(f[10])
                except ValueError:
                    continue
                key = "crit" if f[16].strip().lower() in ("1", "true") else "hit"
                dmg[f[8].strip('"')][key].append(amt)
            elif ev == "SWING_DAMAGE":
                if len(f) < 14:
                    continue
                try:
                    amt = int(f[7])
                except ValueError:
                    continue
                key = "crit" if f[13].strip().lower() in ("1", "true") else "hit"
                dmg["Melee"][key].append(amt)
    return dmg, casts


def check_alignment(dmg):
    """Refuse to report unless doc-confirmed facts reproduce."""
    problems = []
    for name in ALIGNMENT_ZERO_CRIT:
        v = dmg.get(name)
        if not v or (len(v["hit"]) + len(v["crit"])) < 20:
            continue
        if v["crit"]:
            problems.append(
                f"{name} shows {len(v['crit'])} crits — it is a doc-confirmed "
                "0%-crit periodic effect, so the critical-flag field is "
                "misaligned")
    melee, holystrike = dmg.get("Melee"), dmg.get("Lightbound Cleave")
    for v, label in ((melee, "Melee"), (holystrike, "Lightbound Cleave")):
        if v and (len(v["hit"]) + len(v["crit"])) >= 30:
            rate = len(v["crit"]) / (len(v["hit"]) + len(v["crit"]))
            if not 0.05 < rate < 0.95:
                problems.append(
                    f"{label} crit rate {rate:.1%} is implausible — suspect "
                    "field misalignment")
    return problems


def sim_base(conn, name, cs, content, level=60):
    """The sim's base (pre-talent, pre-crit) value for one logged event."""
    sid = NAME_OVERRIDES.get(name)
    if sid is None:
        rows = conn.execute("SELECT id FROM spells WHERE name = ?",
                            (name,)).fetchall()
        if len(rows) != 1:
            return None, "not in NAME_OVERRIDES and name is absent/ambiguous"
        sid = rows[0][0]
    try:
        ab = resolve_ability(conn, sid, level=level)
    except AbilityResolutionError as e:
        return None, f"resolver refused: {e}"
    evs = ab.events()
    if not evs:
        return None, "resolves to NO EVENTS (no known magnitude)"
    pick = EVENT_PICKER.get(name)
    ev = evs[0]
    if pick == "attributed":
        cand = [e for e in evs if e.is_attributed]
        ev = cand[0] if cand else evs[0]
    elif pick == "own":
        cand = [e for e in evs if not e.is_attributed]
        ev = cand[0] if cand else evs[0]
    r = ab.expected_hit(cs, content, event=ev)
    base = (r.breakdown["base_min"] + r.breakdown["base_max"]) / 2.0
    return (base, ev.school) if base > 0 else (None, "base resolves to 0")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("logs", nargs="*")
    ap.add_argument("--character", default="Elric")
    ap.add_argument("--all-logs", action="store_true")
    ap.add_argument("--log-dir", default=str(DEFAULT_LOG_DIR))
    ap.add_argument("--ap", type=float, default=584.0)
    ap.add_argument("--sp", type=float, default=533.0)
    ap.add_argument("--weapon-min", type=float, default=585.0)
    ap.add_argument("--weapon-max", type=float, default=669.0)
    ap.add_argument("--min-hits", type=int, default=15)
    args = ap.parse_args()

    paths = [Path(p) for p in args.logs]
    if args.all_logs:
        paths = sorted(Path(args.log_dir).glob("* WoWCombatLog.txt"))
    if not paths:
        print("no logs given; pass paths or --all-logs")
        return 1

    conn = connect(config.DB_PATH)
    content = get_preset("raid_boss_st")
    cs = CharState(level=60, attack_power=args.ap, spell_power=args.sp,
                   spell_crit_pct=0.0, melee_crit_pct=0.0,
                   main_hand={"min": args.weapon_min, "max": args.weapon_max,
                              "speed": 3.57})

    pooled = collections.defaultdict(lambda: {"hit": [], "crit": []})
    per_log = []
    for p in paths:
        if not p.exists():
            print(f"! missing: {p}")
            continue
        dmg, casts = scan_log(p, args.character)
        if not dmg:
            print(f"  {p.name}: no {args.character} damage events, skipped")
            continue
        problems = check_alignment(dmg)
        if problems:
            print(f"🛑 {p.name}: FIELD ALIGNMENT FAILED, refusing to report")
            for pr in problems:
                print(f"     {pr}")
            continue
        per_log.append((p.name, dmg))
        for k, v in dmg.items():
            pooled[k]["hit"].extend(v["hit"])
            pooled[k]["crit"].extend(v["crit"])
        n = sum(len(v["hit"]) + len(v["crit"]) for v in dmg.values())
        print(f"  {p.name}: {n:,} damage events, alignment OK")

    if not per_log:
        print("nothing usable")
        return 1

    # A ratio far outside any plausible talent stack is not a multiplier, it is
    # a broken sim base. Reporting those alongside real multipliers would invite
    # averaging them in, so they are separated by name and with a likely cause.
    BROKEN_ABOVE = 3.0
    KNOWN_BROKEN = {
        "Righteous Vengeance": "sim base ~1: it is 30% of a CRIT's damage as a "
                               "DoT, and the sim has no source-damage input for it",
        "Holy Finish": "combo points are not parameterised (2a gap) so the base "
                       "is computed at 0 CP — and its CP term is QUADRATIC",
        "Seal of Command": "seals are per-swing riders; the sim scores them "
                           "per cast",
        "Seal of Vengeance": "seals are per-swing riders; the sim scores them "
                             "per cast",
    }

    def emit(label, dmg_map, show_broken=True):
        print(f"\n{'=' * 78}\n{label}\n{'=' * 78}")
        print(f"{'ability':30}{'school':12}{'n':>6}{'sim base':>10}"
              f"{'logged':>9}{'ratio':>8}")
        by_school, broken, unresolved = collections.defaultdict(list), [], []
        for name, v in sorted(dmg_map.items(),
                              key=lambda kv: -len(kv[1]["hit"])):
            if len(v["hit"]) < args.min_hits:
                continue
            base, school = sim_base(conn, name, cs, content)
            logged = statistics.mean(v["hit"])
            if base is None:
                unresolved.append((name, school, len(v["hit"]), logged))
                continue
            ratio = logged / base
            if ratio > BROKEN_ABOVE or ratio < 0.5:
                broken.append((name, ratio, base, logged, len(v["hit"])))
                continue
            print(f"{name[:29]:30}{str(school)[:11]:12}{len(v['hit']):>6}"
                  f"{base:>10,.0f}{logged:>9,.0f}{ratio:>7.2f}x")
            by_school[school].append((name, ratio, len(v["hit"])))

        print("\n--- by school (groups are never averaged together) ---")
        for school, rows in sorted(by_school.items(),
                                   key=lambda kv: -sum(r[2] for r in kv[1])):
            rs = [r[1] for r in rows]
            if len(rows) < 2:
                print(f"  {school:12} single sample: {rows[0][0]} "
                      f"{rows[0][1]:.2f}x - no group estimate")
                continue
            spread = max(rs) - min(rs)
            flag = "  << WIDE, not one multiplier" if spread > 0.35 else ""
            print(f"  {school:12} n={len(rows)}  median "
                  f"{statistics.median(rs):.2f}x  range "
                  f"{min(rs):.2f}-{max(rs):.2f}{flag}")
            for nm, r, n in sorted(rows, key=lambda x: -x[2]):
                print(f"      {nm[:34]:36}{r:>6.2f}x  ({n} hits)")

        if show_broken and broken:
            print("\n--- EXCLUDED: sim base is wrong, not a talent multiplier ---")
            for nm, r, base, logged, n in sorted(broken, key=lambda x: -x[1]):
                why = KNOWN_BROKEN.get(nm, "cause unknown - investigate")
                print(f"  {nm[:28]:30}{r:>8.2f}x  base {base:,.0f} vs "
                      f"{logged:,.0f}\n      {why}")
        if show_broken and unresolved:
            print("\n--- logged but NOT resolvable by the sim ---")
            for nm, why, n, logged in unresolved:
                print(f"  {nm[:28]:30}{logged:>9,.0f} avg / {n:>4} hits   {why}")
        return by_school

    emit(f"POOLED across {len(per_log)} log(s) - sim BASE vs logged NON-CRIT avg",
         pooled)

    if len(per_log) > 1:
        print(f"\n\n{'#' * 78}\nPER-LOG - does the multiplier hold session to "
              f"session?\n{'#' * 78}")
        for nm, dmg in per_log:
            groups = emit(f"{nm}", dmg, show_broken=False)
            del groups

    print(f"\nNOTE Ratios assume the stats passed (AP {args.ap:g} / SP "
          f"{args.sp:g} / weapon {args.weapon_min:g}-{args.weapon_max:g}).\n"
          "  A multiplier that MOVES between logs is buff/gear state, not a "
          "talent constant - trust the\n  within-school AGREEMENT (do the "
          "abilities of one school track each other?) over the absolute value.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
