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

# 3e A6 — this harness printed ⚠ and crashed the moment its output was piped or
# redirected: Python selects cp1252 for a non-console stdout on Windows. Same
# defect `2c` fixed across 12 entry points, and THIS file was missed — so the
# regression harness died exactly when a session tried to capture its output,
# which is the only way anyone reads it. `2c`'s own lesson, one file late.
config.ensure_utf8_stdout()

FAILURES = []
GENERALITY_RESULTS = {}     # check name -> bool, for the 3d D1 fixtures only

# 3d D3 — KNOWN engine defects, each an entry in primer/ENGINE_BUGS.md.
#
# These are failing checks that name real bugs, which is the deliverable of
# `3d` Block D. Fixing them is `3e`, so they must not break the build today —
# but a "known bug" list is exactly the kind of thing that rots into a
# permanent excuse, so the registry is enforced BOTH ways:
#
#   registered + still failing  -> reported as EXPECTED FAIL, does not exit 1
#   registered + now PASSING    -> HARD FAILURE. Close the ENGINE_BUGS.md entry
#                                  and delete the line here. A stale registry
#                                  silently lowers the bar for every later run.
#   unregistered + failing      -> ordinary failure, exit 1 (a new regression)
#
# 🛑 Do not add a line here to silence an inconvenient check. A line is a claim
# that the defect is written up, with file:line, in primer/ENGINE_BUGS.md.
EXPECTED_FAILURES = {
    "[cp_melee] an APL entry gated on combo_points_at_least can ever fire":
        "ENGINE_BUGS.md E1 — combo_points never incremented, AND is_finisher "
        "classifies none of this board's per-combo abilities",
    "[cp_melee] the execute window is modelled, or the sim says it cannot "
    "model it":
        "ENGINE_BUGS.md E2 — target_health_pct pinned at 100 (tiers.py:198-199)",
    "[cp_melee] pet damage is modelled or explicitly named as a gap":
        "ENGINE_BUGS.md E3 — no pet model, while corpus.py:614 includes pet "
        "damage in the dps this is calibrated against",
    "[dot_caster] pet damage is modelled or explicitly named as a gap":
        "ENGINE_BUGS.md E3 — same defect, second fixture",
    # E4 CLOSED in 3e B2 — debuff_active / debuff_missing /
    # debuff_remaining_below added to the grammar and to the evaluator, with
    # target debuffs tracked separately from player buffs. Line deleted rather
    # than left as a comment-out, per the registry's own rule.
    "[dot_caster] the board's DoTs enter the rotation at all":
        "ENGINE_BUGS.md E5 — DoTs are filed behind every cooldown ability and "
        "the GCD budget never reaches them (6 of 7 cast zero times)",
    "[dot_caster] fast_sim allocates GCDs to more than one filler":
        "ENGINE_BUGS.md E5 — same root, seen through the filler tier. 3e B1 "
        "fixed the allocation rule and this now PASSES on cp_melee (1 of 7 -> "
        "2 of 7); the DoT caster still reads 0 of 8 because its nine cooldown "
        "abilities consume the entire GCD budget before the filler tier is "
        "reached at all. Closes with B3, not B1",
}

# A DAMAGING ability whose magnitude is genuinely unknown, used to exercise the
# zero-damage guard rather than assume it still works.
# ⚠ Do not swap this for an ability that merely has a zero *component*: Blades of
# Light looks like a candidate and is not one — its own effect is zero but its
# trigger-reached components resolve, so the ability-level guard correctly stays
# quiet and only the per-event warning fires.
#
# 🆕 2026-08-06: was Thorns (467), and the swap is a RESULT, not a repair. The
# db.ascension.gg ingest gave Thorns SP 0.0182 / AP 0.0118, so it resolves to a
# damage event now and can no longer exercise a zero-damage guard. The fixture's
# premise was retired by the data improving underneath it. 🛑 The guard itself
# was never in question — the correct response is a still-valid fixture, never a
# weakened assertion.
#
# Execution Sentence is a durable replacement because its emptiness has a
# documented CAUSE rather than being an accident of coverage: all three of its
# `EffectBasePoints` are the DBC "no value" sentinel (-1) and its
# `EffectTriggerSpell` is empty, so its real formula lives outside the effect
# slots this extract captures — a hardcoded script trigger
# (build_paladin-hammerdin.md §8, chase item 2). No wider extract or scrape
# fills that in; only a live tooltip would.
ZERO_DAMAGE_SPELL_ID = 954817  # Execution Sentence


def check(name, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail else ""))
    if not ok:
        FAILURES.append(name)


def gcheck(name, ok, detail=""):
    """A generality check on the 3d D1 fixtures. Verdict is deferred to
    `resolve_generality()`, because whether a failure is acceptable depends on
    the EXPECTED_FAILURES registry, and whether a PASS is acceptable does too."""
    GENERALITY_RESULTS[name] = ok
    known = name in EXPECTED_FAILURES
    if ok:
        tag = "PASS!" if known else "PASS "
    else:
        tag = "XFAIL" if known else "FAIL "
    print(f"{tag} {name}" + (f"  ({detail})" if detail else ""))


def resolve_generality():
    """Enforce the registry in both directions. See EXPECTED_FAILURES."""
    unexpected_fail = [n for n, ok in GENERALITY_RESULTS.items()
                       if not ok and n not in EXPECTED_FAILURES]
    unexpected_pass = [n for n, ok in GENERALITY_RESULTS.items()
                       if ok and n in EXPECTED_FAILURES]
    stale = [n for n in EXPECTED_FAILURES if n not in GENERALITY_RESULTS]

    xfails = [n for n, ok in GENERALITY_RESULTS.items()
              if not ok and n in EXPECTED_FAILURES]
    if xfails:
        print(f"\n{len(xfails)} EXPECTED failure(s) — known engine defects, "
              f"written up in primer/ENGINE_BUGS.md, scheduled for 3e:")
        for n in xfails:
            print(f"    XFAIL  {n}\n           -> {EXPECTED_FAILURES[n]}")

    for n in unexpected_fail:
        print(f"\n🛑 NEW generality failure, not in EXPECTED_FAILURES: {n}")
        print("   Either it is a real regression, or it is a new engine defect "
              "that must be written up in primer/ENGINE_BUGS.md and registered.")
        FAILURES.append(n)
    for n in unexpected_pass:
        print(f"\n🎉 {n}\n   is registered as an EXPECTED FAILURE but now PASSES.")
        print("   If the defect is fixed: close its primer/ENGINE_BUGS.md entry "
              "and delete its line from EXPECTED_FAILURES.")
        print("   If it is not fixed, the check has been weakened and that is "
              "worse. Either way this is a hard failure — a stale known-bug "
              "registry lowers the bar for every later run.")
        FAILURES.append(f"stale EXPECTED_FAILURES entry: {n}")
    for n in stale:
        print(f"\n🛑 EXPECTED_FAILURES names a check that did not run: {n}")
        print("   The check was renamed or removed without updating the "
              "registry. Fix the registry.")
        FAILURES.append(f"EXPECTED_FAILURES entry with no matching check: {n}")


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
    # 6b -- measured buff layer (3b pre-flight §0.3). Three properties from the
    # 2e incremental capture, asserted against component mode: Kings multiplies
    # LAST (flats sum first), PoI doubles buff raw SP ("items and effects"),
    # and sheet mode refuses to double-count buffs a sheet already includes.
    gear_b = {"chest": GearItem(item_id=1, name="t", slot="chest",
                                stats={"intellect": 100.0, "spell_power": 100.0})}
    spec_u = BuildSpec(character_level=60, role=Role.DPS, path="Intelligence",
                       abilities=[], talents=[], gear=gear_b)
    spec_b = BuildSpec(character_level=60, role=Role.DPS, path="Intelligence",
                       abilities=[], talents=[], gear=gear_b,
                       raid_buffs=["blessing_of_kings", "arcane_brilliance"])
    st_u = compute_stats(spec_u, get_preset("raid_boss_st"), conv)
    st_b = compute_stats(spec_b, get_preset("raid_boss_st"), conv)
    check("buffs: Kings multiplies LAST over summed flats",
          abs(st_b.intellect - (st_u.intellect + 31.0) * 1.10) < 1e-6,
          f"unbuffed Int {st_u.intellect:.1f} -> buffed {st_b.intellect:.1f}")
    check("buffs: PoI doubles buff raw SP (items AND effects)",
          abs((st_b.spell_power - st_u.spell_power) - 27.0 * 2.0) < 1e-6,
          f"SP delta {st_b.spell_power - st_u.spell_power:.1f} (raw 27 x2)")
    spec_sheet_b = BuildSpec(character_level=60, role=Role.DPS, path="Intelligence",
                             abilities=[], talents=[],
                             raid_buffs=["blessing_of_kings"],
                             stats_override={"spell_power": 500})
    st_sb = compute_stats(spec_sheet_b, get_preset("raid_boss_st"), conv)
    check("buffs: sheet mode refuses to double-count them",
          abs(st_sb.spell_power - 500.0) < 1e-6
          and any("double-count" in w for w in st_sb.warnings))

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

    # 9 -- 3d D1: THE TWO NON-PALADIN FIXTURES.
    #
    # Everything above this line runs on one character. Six real engine bugs sit
    # in shared code paths that an all-instant, single-filler, no-combo-point,
    # no-pet melee build is structurally incapable of exposing — so nothing in
    # this harness would fail if a Rogue or a Warlock produced nonsense.
    #
    # 🛑 THESE CHECKS ARE EXPECTED TO FAIL, AND THAT IS THE DELIVERABLE (D3).
    # Each failure is filed in bugs/ with its file:line. FIXING THEM IS 3e.
    # Do not "repair" a failure here by weakening the assertion — the assertions
    # state what the engine claims about itself in its own comments and
    # docstrings, and a failing one means the code does not do what it says.
    check_nonpaladin_fixtures(conn, ct, conv)
    resolve_generality()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        return 1
    print("all sim-engine checks pass")
    return 0


def _load_fixture(conn, ct, conv, filename):
    """A committed fixture -> (BuildSpec, CharState). Same path as the paladin."""
    import json as _json
    root = Path(__file__).resolve().parents[2]
    bd = _json.loads((root / "fixtures" / filename).read_text(encoding="utf-8"))
    gear = {s: GearItem(item_id=0, name=w.get("item_name", s), slot=s,
                        stats={}, weapon={k: v for k, v in w.items()
                                          if k != "item_name"})
            for s, w in bd["weapons"].items()}
    spec = BuildSpec(
        character_level=bd["character_level"], role=Role(bd["role"]),
        path=bd["path"], gear=gear, stats_override=bd["stats_override"],
        source=bd.get("source", "crawled"),
        abilities=[SlottedCard(a["spell_id"], a["rank"]) for a in bd["abilities"]],
        talents=[SlottedCard(t["spell_id"], t["rank"]) for t in bd["talents"]])
    return bd, spec, compute_stats(spec, ct, conv, conn=conn)


def _filler_ids(conn, apl, level):
    """On-GCD APL entries with no cooldown — the 'filler' tier fast_sim
    allocates last. Classified the same way `tiers.py` does, from the resolved
    ability's own `cooldown_seconds`, so the check cannot drift from the code
    it tests by re-implementing the rule differently."""
    from core.sim.tiers import _resolve_all
    off = {e.spell_id for e in apl.entries if e.off_gcd}
    ids = apl.spell_ids()
    abilities = _resolve_all(conn, ids, level, [])
    return [s for s in ids if s not in off and abilities.get(s)
            and not (abilities[s].fields.get("cooldown_seconds") or 0)]


def check_nonpaladin_fixtures(conn, ct, conv):
    """Generality checks. See §9 above — these are MEANT to fail today."""
    from core.sim.apl_gen import generate_apl
    from core.sim.tiers import fast_sim, medium_sim

    print("\n--- 3d D1: non-paladin fixtures — XFAIL = a known engine defect "
          "written up in primer/ENGINE_BUGS.md, scheduled for 3e ---")

    for filename, kind in (("build_crawled_cp_melee.json", "cp_melee"),
                           ("build_crawled_dot_caster.json", "dot_caster")):
        try:
            bd, spec, cs = _load_fixture(conn, ct, conv, filename)
        except Exception as e:                      # noqa: BLE001
            gcheck(f"[{kind}] fixture loads and computes stats", False, repr(e))
            continue
        gcheck(f"[{kind}] fixture loads and computes stats", True,
              f"{len(spec.abilities)} abilities, {len(spec.talents)} talents")

        apl = generate_apl(conn, spec, ct, cs)
        f = fast_sim(conn, spec, ct, cs, apl=apl)
        m = medium_sim(conn, spec, apl, ct, cs)

        # --- the generic property every build must satisfy --------------------
        # `tiers.py:137-141` — in fast_sim the FIRST filler is given the entire
        # remaining GCD budget (`gcd_budget = 0.0` after it), so every later
        # filler gets 0 casts. The comment two lines above says "fillers split
        # whatever budget the cooldowns left, in priority order." This is the
        # tier the calibration gate runs on.
        #
        # ⚠ 3e B1 — THE ORIGINAL CHECK WAS TOO WEAK TO BITE AND SAID SO. It
        # counted abilities that did *any* damage, and both boards carry enough
        # COOLDOWN abilities to clear the threshold no matter how the FILLER
        # budget is split. Measured: it passed at 11 acting abilities on the DoT
        # caster while **zero of that board's eight fillers cast even once**.
        # The claim is now made about fillers specifically.
        acting = [k for k, r in f.per_ability.items() if r["damage"] > 0]
        fillers = _filler_ids(conn, apl, spec.character_level)
        firing = [s for s in fillers if f.per_ability.get(s, {}).get("casts", 0) > 0.001]
        gcheck(f"[{kind}] fast_sim allocates GCDs to more than one filler",
              len(fillers) < 2 or len(firing) >= 2,
              f"{len(firing)} of {len(fillers)} on-GCD fillers received any "
              f"casts ({len(acting)} abilities did damage overall, which is why "
              f"the old form of this check passed). Fillers that never cast: "
              f"{sorted(str(s) for s in fillers if s not in firing)[:8]}")

        if kind == "cp_melee":
            # `tiers.py:197` / `apl.py:118` — `combo_points` is never
            # incremented anywhere in the tree, so `combo_points_at_least`
            # (which apl_gen.py:91 emits for EVERY finisher) can never be true
            # and those finishers never fire in medium_sim.
            #
            # ⚠ Test the CONDITION, not merely "did a finisher cast". A finisher
            # apl_gen did not recognise as one gets `always` and casts freely,
            # which would pass a naive check while the actual bug is untouched.
            # The precise claim is: an entry GATED on combo_points_at_least never
            # becomes true.
            cp_gated = {e.spell_id for e in apl.entries
                        if any(c.get("type") == "combo_points_at_least"
                               for c in (e.conditions or []))}
            fired = {sid for sid in cp_gated
                     if m.per_ability.get(sid, {}).get("casts", 0) > 0}
            gcheck("[cp_melee] an APL entry gated on combo_points_at_least can "
                  "ever fire",
                  bool(cp_gated) and bool(fired),
                  f"{len(cp_gated)} CP-gated entries "
                  f"({sorted(cp_gated)}), {len(fired)} ever cast — "
                  f"combo_points is never incremented anywhere in core/sim"
                  if cp_gated else
                  "NO entry is CP-gated: apl_gen did not classify any of this "
                  "board's per-combo abilities as finishers, so this check "
                  "could not exercise the bug at all")

            # `tiers.py:198-199` — self_health_pct/target_health_pct are pinned
            # at 100. 🛑 The failure is NOT "the execute ability never casts" —
            # it is the opposite: with target health pinned at 100 the window is
            # unmodelled, so an execute-gated ability is either cast freely (as
            # if always available) or silently dropped. Either way the sim must
            # SAY it cannot model the window. Casting it is not a pass.
            hp_gated = {e.spell_id for e in apl.entries
                        if any(c.get("type") in ("target_health_pct_below",
                                                 "health_pct_below")
                               for c in (e.conditions or []))}
            hw_casts = m.per_ability.get(24239, {}).get("casts", 0)
            warned = any("health" in (w or "").lower()
                         for w in (m.warnings or []) + (f.warnings or []))
            gcheck("[cp_melee] the execute window is modelled, or the sim says "
                  "it cannot model it",
                  warned or bool(hp_gated),
                  f"Hammer of Wrath (24239) is execute-gated in game and the "
                  f"sim cast it {hw_casts}x with target_health_pct pinned at "
                  f"100.0; {len(hp_gated)} APL entries carry a health "
                  f"condition and no warning mentions health")

        if kind == "dot_caster":
            # `apl.py:19-32` — no target-debuff / DoT-uptime condition type
            # exists in the grammar, and apl_gen gives fillers `always`. So a
            # DoT is re-cast every GCD with its entire duration's damage
            # re-scored each time.
            #
            # ⚠ 3e B2 — STRENGTHENED. The original form asked only whether a
            # condition NAME containing "dot"/"debuff" existed, which is
            # satisfiable by adding a string to a set. It now exercises the
            # evaluator against a state carrying a target debuff, and checks the
            # debuff is tracked SEPARATELY from the player's buffs — the
            # conflation was the actual defect.
            from core.sim.apl import CONDITION_TYPES, evaluate
            from core.sim.tiers import TimelineState
            named = sorted(t for t in CONDITION_TYPES if "debuff" in t or "dot" in t)
            works = False
            if named:
                stt = TimelineState(now=10.0, fight_duration=100.0)
                stt.debuffs[999] = 13.0        # 3s left on the target
                try:
                    works = (
                        evaluate({"type": "debuff_missing", "spell_id": 999}, stt) is False
                        and evaluate({"type": "debuff_missing", "spell_id": 998}, stt) is True
                        and evaluate({"type": "debuff_remaining_below",
                                      "spell_id": 999, "value": 5}, stt) is True
                        and evaluate({"type": "debuff_remaining_below",
                                      "spell_id": 999, "value": 2}, stt) is False
                        # the separation itself: a target debuff must NOT read
                        # as a player buff
                        and stt.buff_active(999) is False)
                except Exception:                       # noqa: BLE001
                    works = False
            gcheck("[dot_caster] the APL grammar can express DoT uptime",
                  bool(named) and works,
                  f"debuff/DoT condition types present: {named or 'NONE'}; "
                  f"evaluator exercises them correctly and keeps target "
                  f"debuffs separate from player buffs: {works}. "
                  f"full grammar: {sorted(CONDITION_TYPES)}")

            # `apl_gen.py:62-63` — fillers are sorted by damage PER CAST, not
            # per GCD/cast-time, contradicting apl_gen's own docstring line 10.
            # On this board that penalises 1.5s fillers against a 5s Pyroblast.
            board = {a["spell_id"] for a in bd["abilities"]}
            marks = ",".join("?" * len(board))
            periodic = {r[0] for r in conn.execute(
                f"SELECT spell_id FROM spell_mechanics WHERE is_periodic = 1 "
                f"AND spell_id IN ({marks})", tuple(board))}
            # 🛑 A vacuous pass here is worse than a failure: if `periodic` came
            # back empty the check would report "DoTs are not re-cast" while
            # having tested nothing. Assert the fixture actually has DoTs first.
            gcheck("[dot_caster] the fixture's DoTs are identifiable at all "
                  "(guards this check against passing vacuously)",
                  len(periodic) >= 2,
                  f"{len(periodic)} periodic abilities on the board: "
                  f"{sorted(periodic)}")
            casts = {sid: m.per_ability.get(sid, {}).get("casts", 0)
                     for sid in periodic}
            never = {sid for sid, n in casts.items() if n == 0}
            # 🚨 NOT ON THE AUDIT'S PREDICTED LIST — found by this fixture.
            # Before asking whether DoTs are re-cast too often, ask whether they
            # are cast at all. On this board 6 of 7 are cast ZERO times: they
            # carry no cooldown, so apl_gen files them last behind every
            # cooldown ability, and the GCD budget is gone before the rotation
            # reaches them. A DoT caster whose DoTs never enter the rotation is
            # a bigger error than one that refreshes them too eagerly — and it
            # would have made the next check pass for the wrong reason.
            gcheck("[dot_caster] the board's DoTs enter the rotation at all",
                  not never,
                  f"{len(never)} of {len(periodic)} periodic abilities are cast "
                  f"ZERO times: {sorted(never)}; casts = {casts}")
            recast = {sid: n for sid, n in casts.items() if n > 5}
            gcheck("[dot_caster] DoTs that DO cast are not re-cast every GCD",
                  not recast,
                  f"re-cast >5x in one fight: {recast} — no DoT-uptime "
                  f"condition exists, so apl_gen gives them 'always' and each "
                  f"recast re-scores the whole duration's damage. ⚠ Reads clean "
                  f"today only because {len(never)} of {len(periodic)} never "
                  f"cast at all — see the check above.")

        # No pet model exists in core/sim while corpus.py:614 computes
        # dps = (total_damage + pet_damage)/duration, so any pet class is
        # guaranteed to miss low against the corpus it is calibrated on.
        pets = [a["name"] for a in bd["abilities"]
                if "summon" in (a["name"] or "").lower()]
        if pets:
            gcheck(f"[{kind}] pet damage is modelled or explicitly named as a gap",
                  any("pet" in (w or "").lower() for w in (f.warnings or [])
                      + (m.warnings or [])),
                  f"board summons {pets} and no warning mentions pets — the "
                  f"corpus dps this is calibrated against INCLUDES pet damage")


if __name__ == "__main__":
    sys.exit(main())
