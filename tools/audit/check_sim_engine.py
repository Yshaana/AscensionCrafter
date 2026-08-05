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
from core.builds.spec import BuildSpec, GearItem, SlottedCard  # noqa: E402
from core.builds.stats import compute_stats  # noqa: E402
from core.sim.content import Role  # noqa: E402

FAILURES = []

# A DAMAGING ability whose magnitude is genuinely unknown, used to exercise the
# zero-damage guard rather than assume it still works. Thorns states `$s1 Nature
# damage` in its tooltip and resolves to no events at all — the same state Holy
# Shock was in until 2c's G4 fix, and the state the guard exists to catch.
# ⚠ Do not swap this for an ability that merely has a zero *component*: Blades of
# Light looks like a candidate and is not one — its own effect is zero but its
# trigger-reached components resolve, so the ability-level guard correctly stays
# quiet and only the per-event warning fires.
ZERO_DAMAGE_SPELL_ID = 467  # Thorns


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
    # card actually pressed. Two cards reach it (Hour of Judgement 282984 and
    # Hammerdin 282983) by the bounded trigger walk at confidence=inferred.
    #
    # 2b closed the coefficient half: the confirmed +9.1% SP / +9.1% AP live on
    # the TARGET (282987) and are now pulled per component source, so Hammerdin
    # — whose only damage IS the pulse — must reproduce the independently
    # confirmed 223.6-246.6 at AP 584 / SP 533 (build doc §12 item 2).
    from core.builds.stats import CharState
    cs = CharState(level=60, attack_power=584.0, spell_power=533.0,
                   spell_crit_pct=0.0, melee_crit_pct=0.0)
    ct = get_preset("raid_boss_st")

    hammerdin = resolve_ability(conn, 282983, level=60)
    hres = hammerdin.expected_hit(cs, ct)
    check("HftH base reproduces 223.6-246.6 (flat 122-145 + 9.1% SP + 9.1% AP)",
          abs(hres.breakdown["base_min"] - 223.6) < 0.5
          and abs(hres.breakdown["base_max"] - 246.6) < 0.5,
          f"{hres.breakdown.get('base_min'):.1f}-{hres.breakdown.get('base_max'):.1f}")
    check("HftH SP+AP coefficients arrive via trigger attribution, not the card",
          sum(1 for c in hres.components
              if c.get("kind") == "coefficient" and c.get("via") == "trigger_hop2"
              and abs(c.get("coefficient", 0) - 0.091) < 1e-9) == 2,
          f"{[(c.get('term'), c.get('coefficient'), c.get('via')) for c in hres.components]}")

    hoj = resolve_ability(conn, 282984, level=60)
    evs = {e.key: e for e in hoj.events()}
    check("HoJ splits into its own periodic tick + the attributed HftH pulse",
          any(k.startswith("self:periodic") for k in evs)
          and any("282987" in k for k in evs), f"events: {sorted(evs)}")
    check("HoJ own periodic resolves to the confirmed 81 (21 + 2/level at 60)",
          any(abs((c.get("min") or 0) - 81.0) < 0.5
              for e in evs.values() if e.kind == "periodic"
              for c in hoj.expected_hit(cs, ct, event=e).components))

    # The pulse is delivered by a PERIODIC-TRIGGER aura (aura 23, 500ms) over a
    # 10s duration -> 20 pulses/cast, against 5 ticks of HoJ's own damage. The
    # 4.00 ratio this implies is validated against 20,823 pooled crawl hits
    # (observed 3.81) — see confirmed_facts.
    pulse = next(e for e in hoj.events() if e.is_attributed)
    own = next(e for e in hoj.events() if not e.is_attributed)
    n_pulse, _ = hoj.occurrences_per_cast(pulse)
    n_own, _ = hoj.occurrences_per_cast(own)
    check("HoJ pulse delivery: 20 HftH pulses vs 5 own ticks (ratio 4.00)",
          n_pulse == 20 and n_own == 5, f"{n_pulse} vs {n_own}")
    check("attributed events flagged never-anchor",
          any("never a calibration anchor" in w
              for w in hoj.expected_cast(cs, ct).warnings))

    # 4 -- MC convergence, at BOTH levels. Per-event is PHASE_2 T3's mandated
    # tier-divergence guard; per-cast additionally guards the event composition
    # and occurrence counting that 2b introduced.
    rng = random.Random(42)
    cs_crit = CharState(level=60, attack_power=584.0, spell_power=533.0,
                        spell_crit_pct=28.86, melee_crit_pct=32.46,
                        spell_hit_pct=5.7, melee_hit_pct=5.7)
    ab = resolve_ability(conn, 282984, level=60)
    for ev in ab.events():
        exp = ab.expected_hit(cs_crit, ct, event=ev)
        n = 100_000
        mc = sum(ab.roll_hit(cs_crit, ct, rng, event=ev).damage
                 for _ in range(n)) / n
        tol = 4 * (exp.variance / n) ** 0.5 + 1e-9   # 4 sigma of the MC mean
        check(f"MC mean ~= expected per event ({ev.key})",
              abs(mc - exp.mean) <= tol,
              f"mc {mc:.2f} vs exp {exp.mean:.2f}, tol {tol:.2f}")

    exp_cast = ab.expected_cast(cs_crit, ct)
    n = 20_000
    mc_cast = sum(ab.roll_cast(cs_crit, ct, rng).damage for _ in range(n)) / n
    tol = 4 * (exp_cast.variance / n) ** 0.5 + 1e-9
    check("MC mean ~= expected per CAST (event composition guard)",
          abs(mc_cast - exp_cast.mean) <= tol,
          f"mc {mc_cast:.1f} vs exp {exp_cast.mean:.1f}, tol {tol:.1f}")

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
    st2 = compute_stats(spec2, get_preset("raid_boss_st"), conv, conn=conn)
    # Session 2d replaced the "Duality AP anomaly" claim (retracted — it was an
    # OFF-phase reading of a cycling bug, not a conversion rate) with an
    # impairment layer. Three properties are asserted, because the failure this
    # guards is a build silently modelled against a system the server is not
    # honouring — and the second is the one that makes a fix cheap: the MODEL
    # must stay the intended behaviour, so only `fixed_on` has to change.
    check("an impaired path raises a SYSTEM IMPAIRMENT advisory",
          any("SYSTEM IMPAIRMENT" in w for w in st2.warnings))
    check("the impairment carries its policy flag to the recommender",
          any(i.get("recommend") is False for i in st2.impairments),
          f"impairments={[i['system'] for i in st2.impairments]}")
    check("default mode models INTENDED behaviour, not the bug",
          st2.impairment_range is None
          and any("OPTIMISTIC" in w for w in st2.warnings))
    # Needs real Strength, or Duality's AP grant is 0 and the range degenerates
    # to a single point — which would make the assertion below pass vacuously.
    spec2m = BuildSpec(character_level=60, role=Role.DPS, path="Duality",
                       abilities=[], talents=[SlottedCard(1, 1)],
                       gear={"chest": GearItem(item_id=1, name="t", slot="chest",
                                               stats={"strength": 121})})
    st2m = compute_stats(spec2m, get_preset("raid_boss_st"), conv, conn=conn,
                         system_state="as_measured")
    check("as_measured yields a RANGE for an intermittent impairment, "
          "never a fabricated duty cycle",
          st2m.impairment_range is not None
          and st2m.impairment_range.get("unmeasured") == "duty_cycle"
          and st2m.impairment_range["attack_power_low"]
          < st2m.impairment_range["attack_power_high"])
    # T4b replaces 2a's blanket "talents contribute nothing" warning with a
    # per-talent account. Two properties are asserted, because the failure this
    # guards is a talent silently contributing 1.0x — indistinguishable, without
    # a warning, from one that was read correctly and does nothing.
    check("a talent id that does not resolve is NAMED, not dropped",
          any("NOT RESOLVED" in w for w in st2.warnings),
          "spell id 1 is not a card")

    from core.sim.talents import resolve_talents
    teff = resolve_talents(conn, [SlottedCard(12815, 5)])   # Sword Specialization
    check("a talent whose auras are not understood is NAMED as a gap",
          any("UNMODELLED" in w for w in teff.warnings)
          and any(m.kind.startswith("unmodelled_aura") for m in teff.modifiers),
          "Sword Specialization uses aura 333, outside stock 3.3.5")

    # The Improved Cleave lesson in code: the scope of an amplifier comes from
    # the modifier op, never from the tooltip. 3/3 is +120% via SpellModOp 8
    # (ALL_EFFECTS), so it must multiply the WHOLE ability.
    ic = resolve_talents(conn, [SlottedCard(12329, 3)])
    ic_mods = [m for m in ic.modifiers if m.kind == "spellmod_pct"]
    check("Improved Cleave 3/3 reads as +120% SPELLMOD_ALL_EFFECTS",
          any(abs(m.value - 120.0) < 1e-6 and m.scope.get("op") == 8
              for m in ic_mods),
          f"{[(m.value, m.scope.get('op_name')) for m in ic_mods]}")

    # 7 -- T5 tiers, T6 uncertainty, T7 weights, on the committed fixture
    import json as _json
    from core.sim.apl import APL, APLEntry, APLError
    from core.sim.tiers import fast_sim, medium_sim
    from core.sim.weights import stat_weights
    from core.sim.uncertainty import sim_with_uncertainty

    root = Path(__file__).resolve().parents[2]
    bd = _json.loads((root / "fixtures/build_elric_paladin.json").read_text(
        encoding="utf-8"))
    gear = {s: GearItem(item_id=0, name=s, slot=s, stats={}, weapon=w)
            for s, w in bd["weapons"].items()}
    fspec = BuildSpec(
        character_level=bd["character_level"], role=Role(bd["role"]),
        path=bd["path"], gear=gear, stats_override=bd["stats_override"],
        abilities=[SlottedCard(a["spell_id"], a["rank"]) for a in bd["abilities"]],
        talents=[SlottedCard(t["spell_id"], t["rank"]) for t in bd["talents"]])
    fcs = compute_stats(fspec, ct, conv, conn=conn)

    apls = {}
    for nm in ("optimal", "observed"):
        d = _json.loads((root / f"fixtures/apl_paladin_{nm}.json").read_text(
            encoding="utf-8"))
        apls[nm] = APL(name=d["name"], provenance=d["provenance"],
                       entries=[APLEntry(**{k: v for k, v in e.items()
                                            if k != "name"})
                                for e in d["entries"]])
    check("both Paladin APL fixtures parse against the closed grammar", True)

    try:
        APLEntry(spell_id=1, conditions=[{"type": "target_count_at_least",
                                          "value": 3}])
        check("APL refuses target-count branching", False, "it was accepted")
    except APLError:
        check("APL refuses target-count branching", True)

    f = fast_sim(conn, fspec, ct, fcs, apl=apls["optimal"])
    m = medium_sim(conn, fspec, apls["optimal"], ct, fcs)
    check("fast and medium agree within 35% on the same APL",
          f.primary_value > 0 and m.primary_value > 0
          and abs(f.primary_value - m.primary_value) / m.primary_value < 0.35,
          f"fast {f.primary_value:.0f} vs medium {m.primary_value:.0f}")
    # The allocation-order bug this guards: a no-cooldown ability first in the
    # priority list used to eat the whole GCD budget and report a 1-button rotation.
    check("fast_sim allocates to more than one ability",
          sum(1 for r in f.per_ability.values() if r["damage"] > 0) >= 5,
          f"{sum(1 for r in f.per_ability.values() if r['damage'] > 0)} abilities")
    check("medium_sim reports GCD saturation",
          any("GCD saturation" in w for w in m.warnings))

    # ✅ UNBLOCKED in 2c by gate G4. Through 2b the optimal APL scored BELOW the
    # observed/starved one, inverting build doc §11's central conclusion — a data
    # gap, not a result: Holy Shock's level-60 rank (20930) is a DUMMY whose
    # sub-spell chain the rank sibling did not inherit, so it resolved to 0 and
    # the ~9 GCDs the optimal APL spends on it scored as waste. G4 follows the
    # sibling's own DBC description to its sub-spells (25902/25903), Holy Shock
    # resolves to 562–608, and the comparison means something again.
    #
    # Two checks, deliberately separate:
    #   1. the zero-damage GUARD still works (it is what caught this) — asserted
    #      against a rotation deliberately built around an ability with no
    #      known magnitude, so the guard is tested rather than assumed;
    #   2. the real comparison now runs, and optimal must beat observed.
    mo = medium_sim(conn, fspec, apls["observed"], ct, fcs)
    zero_apl = APL(name="zero_damage_guard",
                   entries=[APLEntry(spell_id=ZERO_DAMAGE_SPELL_ID)])
    mz = medium_sim(conn, fspec, zero_apl, ct, fcs)
    check("zero-damage ability in the rotation is named, not silently scored",
          any("ZERO damage" in w for w in mz.warnings),
          f"guard exercised against spell {ZERO_DAMAGE_SPELL_ID}")
    check("optimal APL beats the observed/starved one (build doc §11)",
          m.primary_value > mo.primary_value,
          f"optimal {m.primary_value:.0f} vs observed {mo.primary_value:.0f} "
          "- unblocked by G4 (Holy Shock resolves)")

    u = sim_with_uncertainty(conn, fspec, ct, fcs, apl=apls["optimal"],
                             samples=40, seed=1)
    check("knowledge-uncertainty band is non-degenerate",
          u["high"] > u["low"] and u["spread_pct"] > 0,
          f"{u['low']:.0f}-{u['high']:.0f} (+/-{u['spread_pct']:.1f}%)")
    check("uncertainty is reported separately from combat RNG",
          f.combat_rng is None and "policy_note" in u)

    w = stat_weights(conn, fspec, ct, fcs, apl=apls["optimal"], delta=100)
    check("stat weights are non-degenerate",
          any(r["dps_per_point"] > 0 for r in w["weights"].values()),
          f"{len(w['weights'])} stats")
    check("hit weight states its target level and gated share",
          "level-63" in (w["weights"].get("hit_rating", {}).get("note") or ""))

    # 8 -- T9 ledger, T10 cache, T11 diff. Each check targets the one property
    # that makes the module worth having, not that it runs.
    from core.sim import cache as simcache
    from core.sim.predictions import PredictionLedgerError, record_prediction

    dv, dv_warnings = simcache.data_version(conn)
    # The failure this guards is silent and total: a key that watches only
    # spell_mechanics serves a previous session's answers after a rebuild that
    # changed spell_effect_values or the talent path.
    missing = [t for t in simcache.SIM_INPUT_TABLES
               if not conn.execute(
                   "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                   (t,)).fetchone()]
    check("cache data_version covers every sim input table",
          not missing and not dv_warnings, f"{len(simcache.SIM_INPUT_TABLES)} "
          f"tables hashed -> {dv}" + (f"; MISSING {missing}" if missing else ""))
    k1 = simcache.cache_key(build_hash="x", tier="medium", content={"a": 1},
                            data_version_str=dv)
    k2 = simcache.cache_key(build_hash="x", tier="medium", content={"a": 1},
                            data_version_str=dv + "!")
    check("a changed data_version changes the cache key", k1 != k2)

    try:
        record_prediction(
            conn, slug="pred_2026-08-05_elric_paladin_raid_boss_st",
            build_spec={}, content_profile={}, predicted_value=1.0,
            primary_metric="DAMAGE_DONE", sim_version="x", data_version="x")
        check("the ledger refuses to overwrite an existing prediction", False,
              "it accepted the overwrite")
    except PredictionLedgerError:
        check("the ledger refuses to overwrite an existing prediction", True)

    # T11's central clause: a delta smaller than the uncertainty is not a result.
    from core.sim.diff import diff_builds
    d = diff_builds(conn, fspec, fspec, ct, fcs, fcs, apl_a=apls["optimal"],
                    apl_b=apls["optimal"],
                    uncertainty_a={"low": u["low"], "high": u["high"]},
                    uncertainty_b={"low": u["low"], "high": u["high"]})
    check("diff refuses to rank builds whose delta is inside the uncertainty",
          d["verdict"] == "inconclusive" and d["winner"] is None,
          f"{d['verdict']}, delta {d['delta']:.1f}")

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        return 1
    print("all sim-engine checks pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
