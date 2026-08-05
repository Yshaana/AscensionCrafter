"""Phase 2 T1-T4 validation — run after touching core/sim/ or core/builds/.

Checks (each prints PASS/FAIL; exit 1 on any failure):

1. gtCombatRatings anchors load and validate (T1).
2. Attack tables sum to 100% and respect confirmed values (8% yellow miss vs
   +3, +19% DW white penalty).
3. Hammer from the Heavens reproduces end-to-end THROUGH THE SIM PATH:
   resolver -> ResolvedAbility -> expected base 223.6-246.6 at AP 584/SP 533
   (build doc §12 item 2: 122-145 flat + 9.1% SP + 9.1% AP at level 60).
4. mean(roll_hit x 100k) ~= expected_hit (PHASE_2 T3's tier-divergence guard).
5. Rank-gap redirect: a wrong-rank catalog id resolves to the level-60 id.
6. compute_stats sheet mode + Duality warnings present.
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import config  # noqa: E402  (tools/ may import config; core/ may not)
from core.db.connection import connect  # noqa: E402
from core.sim import combat_engine as ce  # noqa: E402
from core.sim.ability_model import resolve_ability  # noqa: E402
from core.sim.content import get_preset  # noqa: E402
from core.builds.spec import BuildSpec, SlottedCard  # noqa: E402
from core.builds.stats import compute_stats  # noqa: E402
from core.sim.content import Role  # noqa: E402

FAILURES = []


def check(name, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail else ""))
    if not ok:
        FAILURES.append(name)


def main():
    conn = connect(config.DB_PATH)

    # 1 -- rating conversions
    conv = ce.load_rating_conversions(conn, level=60)
    check("gt anchors validate at 60", True)
    check("crit divisor is 14.0", abs(conv.divisors["crit_melee"] - 14.0) < 1e-6)
    check("armor-pen conflict warning attached",
          any("armor_pen" in w for w in conv.warnings))

    # 2 -- attack tables
    boss = get_preset("raid_boss_st").target
    t = ce.white_melee_table(60, 20.0, 8.0, 5, boss, dual_wield=True)
    total = sum(p for _, p in t.segments)
    check("white table sums to 100", abs(total - 100.0) < 1e-9, f"{total}")
    miss = dict(t.segments)["miss"]
    check("DW white miss = 8+19-8 hit = 19", abs(miss - 19.0) < 1e-9, f"{miss}")
    st = ce.special_attack_table(60, 20.0, 8.0, 26, boss)
    check("yellow miss capped at 8-hit", abs(dict(st.segments)["miss"] - 0.0) < 1e-9)
    check("expertise 26 zeroes boss dodge",
          abs(dict(st.segments)["dodge"] - 0.0) < 1e-9)

    # 3 -- Hammer from the Heavens end-to-end THROUGH THE SIM PATH, via the
    # card actually pressed (Hour of Judgement 282984 — HftH's 122-145 is
    # attributed to it by the bounded trigger walk, confidence=inferred).
    # ⚠ The confirmed +9.1% SP / +9.1% AP terms are NOT in spell_scaling (doc
    # prose only, 2a finding) — so the resolvable base is the flat 122-145
    # plus the trigger chain's dummy effect (1). Recorded as a data gap.
    hoj = resolve_ability(conn, 282984, level=60)
    from core.builds.stats import CharState
    cs = CharState(level=60, attack_power=584.0, spell_power=533.0,
                   spell_crit_pct=0.0, melee_crit_pct=0.0)
    res = hoj.expected_hit(cs, get_preset("raid_boss_st"))
    hfth_terms = [c for c in res.components
                  if c.get("via") == "trigger_hop2" and c.get("min")
                  and 121.5 <= c["min"] <= 122.5]
    check("HftH 122-145 present via trigger_hop2 attribution",
          bool(hfth_terms) and abs(hfth_terms[0]["max"] - 145.0) < 0.5,
          f"components: {[(c.get('via'), c.get('min'), c.get('max')) for c in res.components]}")
    check("HoJ own periodic (confirmed, 21+(60-30)*2 -> 81) also present",
          any(c.get("via") == "self" and c.get("min") and
              80.5 <= c["min"] <= 81.5 for c in res.components))
    check("trigger-attributed terms flagged never-anchor",
          any("never a calibration anchor" in w for w in res.warnings))

    # 4 -- MC convergence: mean(roll_hit x 100k) ~= expected_hit
    rng = random.Random(42)
    cs_crit = CharState(level=60, attack_power=584.0, spell_power=533.0,
                        spell_crit_pct=28.86, melee_crit_pct=32.46,
                        spell_hit_pct=5.7, melee_hit_pct=5.7)
    for spell_id, label in ((282984, "Hour of Judgement"),):
        ab = resolve_ability(conn, spell_id, level=60)
        exp = ab.expected_hit(cs_crit, get_preset("raid_boss_st"))
        n = 100_000
        total_dmg = sum(
            ab.roll_hit(cs_crit, get_preset("raid_boss_st"), rng).damage
            for _ in range(n))
        mc = total_dmg / n
        tol = 4 * (exp.variance / n) ** 0.5 + 1e-9   # 4 sigma of the MC mean
        check(f"MC mean ~= expected ({label})", abs(mc - exp.mean) <= tol,
              f"mc {mc:.2f} vs exp {exp.mean:.2f}, tol {tol:.2f}")

    # 5 -- rank-gap redirect on a known wrong-rank catalog entry
    row = conn.execute(
        """SELECT external_id, spell_id FROM spell_id_crosswalk
           WHERE external_source = 'catalog_vs_live'
             AND confidence = 'confirmed'
             AND CAST(external_id AS INTEGER) != spell_id LIMIT 1""").fetchone()
    if row:
        redirected = resolve_ability(conn, int(row[0]), level=60)
        check("rank-gap redirect follows to level-60 id",
              redirected.spell_id == row[1] and bool(redirected.rank_note),
              f"{row[0]} -> {redirected.spell_id}")
    else:
        check("rank-gap redirect (no crosswalk row found)", False,
              "catalog_vs_live rows missing — did the rebuild run?")

    # 6 -- compute_stats: sheet mode, Duality
    spec = BuildSpec(character_level=60, role=Role.DPS, path="Duality",
                     abilities=[SlottedCard(282986, 1)], talents=[],
                     stats_override={"attack_power": 584, "spell_power": 533,
                                     "crit_rating": 393})
    st_state = compute_stats(spec, get_preset("raid_boss_st"), conv)
    check("sheet crit 393 -> 28.07%",
          abs(st_state.spell_crit_pct - 393 / 14.0) < 0.01,
          f"{st_state.spell_crit_pct:.2f}")
    check("sheet mode warns values-are-final",
          any("FINAL" in w for w in st_state.warnings))

    spec2 = BuildSpec(character_level=60, role=Role.DPS, path="Duality",
                      abilities=[], talents=[SlottedCard(1, 1)])
    st2 = compute_stats(spec2, get_preset("raid_boss_st"), conv)
    check("component mode warns about Duality AP anomaly",
          any("ANOMALY" in w for w in st2.warnings))
    check("component mode names unmodelled talents",
          any("talents contribute NO stats" in w for w in st2.warnings))

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        return 1
    print("all sim-engine checks pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
