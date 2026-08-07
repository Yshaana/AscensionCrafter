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
    # E1 CLOSED in 3e B4 — is_finisher now reads `per_combo` as well as
    # `cp_scaling` (all 4 of this board's per-combo abilities are gated, was 0),
    # finishers have their own APL tier above the fillers so a gated entry
    # actually gets a turn, and combo_points is generated and spent in
    # medium_sim. Line deleted per the registry's own rule.
    # E2 CLOSED in 3e B5 — target health decays linearly across the fight, a
    # target_health_pct_below gate works in medium_sim AND scales cast counts in
    # fast_sim, and the residual (TargetAuraState is absent from the extract, so
    # which abilities are execute-gated cannot be derived) is named in warnings
    # by both tiers. Line deleted per the registry's own rule.
    # E3 CLOSED in 3e B6 at the "explicitly named as a gap" bar — both tiers
    # detect summons mechanically (SPELL_EFFECT_SUMMON) and name each pet with
    # the measured size of the omission. ⚠ NOT modelled, and cannot be from our
    # data: creature stats live in the server's creature_template, not in any
    # client DBC. See ENGINE_BUGS E3 and open question pet_damage_not_derivable.
    # E4 CLOSED in 3e B2 — debuff_active / debuff_missing /
    # debuff_remaining_below added to the grammar and to the evaluator, with
    # target debuffs tracked separately from player buffs. Line deleted rather
    # than left as a comment-out, per the registry's own rule.
    "[dot_caster] the board's DoTs enter the rotation at all":
        "ENGINE_BUGS.md E5 PARTLY FIXED in 3e B3 — pure DoTs now enter the "
        "rotation (Corruption 0 -> 4 casts, once per its own 18s duration). The "
        "5 that still read zero are NOT this defect: two are non-damaging (Fel "
        "Armor, Dark Domination) and three are MIXED direct+periodic abilities "
        "in the spam-filler tier, which is ENGINE_BUGS.md E7",
    "[frost_mage] fast_sim allocates GCDs to more than one filler":
        "ENGINE_BUGS.md E7 — third fixture, same root. 1 of 4 fillers casts; "
        "the starved three are Blizzard (a CHANNEL, see E8), Hydricles and Ice "
        "Lance. A caster whose whole rotation is fillers is the case where one "
        "spam button absorbing the budget is most visibly wrong",
    "[dot_caster] fast_sim allocates GCDs to more than one filler":
        "ENGINE_BUGS.md E7 — 0 of 7 fillers cast. Its remaining fillers are "
        "mixed direct+periodic abilities competing in a spam tier where one "
        "button absorbs the budget. Left registered rather than rewritten: "
        "declaring a check invalid because it stopped flattering the code is "
        "what this registry exists to prevent",
    # 🚨 ADDED 3f F3, AND ITS ARRIVAL IS THE FINDING. This entry did not exist
    # because the check was measuring the WRONG SET: `_filler_ids` classified
    # on `cooldown_seconds`, the rule `fast_sim` used BEFORE 3e B1, so
    # cooldown-less bounded abilities were counted as fillers and cp_melee read
    # "3 of 7 firing" and passed. Against the partition fast_sim actually uses
    # (`_useful_cast_interval`) the same run reads **1 of 5** and fails.
    #
    # Nothing about the sim changed — this is an instrument correction
    # revealing a pre-existing state. 🛑 CONSEQUENCE: E7 affects ALL THREE
    # fixtures, not two, and `3e`'s "after B1 and B3 this PASSES on cp_melee
    # (1 of 7 -> 2 of 7)" was computed over the drifted set and is withdrawn.
    "[cp_melee] fast_sim allocates GCDs to more than one filler":
        "ENGINE_BUGS.md E7 — 1 of 5 unbounded fillers casts. Registered in 3f "
        "F3 when the drifted _filler_ids classifier was corrected; the sim was "
        "NOT changed and the gate did not move. The four starved entries "
        "(25286, 275871, 276076, 998107) are the same one-spam-button-absorbs-"
        "the-budget shape as the other two fixtures",

    # 🚨 3h C4 — E15: pet-attributable damage is stored TWICE in
    # ability_performance (an owner row and a pet row with byte-identical
    # damage — 15,551 of 20,785 owner+pet groups corpus-wide), so every SUM
    # over the table double-counts it. Found by the per-ability comparison:
    # pet-class auto ratios read 0.005-0.013 and the logged side carried both
    # copies. Registered, NOT fixed in 3h (the fix moves coverage and
    # therefore the gate — it belongs to a commit that owns its pair).
    # Green path RUN at 3h C4 and REVERTED: dedupe identical
    # (spell_id, spell_name, damage_total) owner/pet pairs inside
    # modelled_damage_share turns this green. See ENGINE_BUGS.md E15.
    "[corpus] identical owner+pet rows in ability_performance are counted "
    "ONCE in the coverage denominator":
        "ENGINE_BUGS.md E15 — modelled_damage_share sums all rows, so a "
        "duplicated pet row inflates total (and modelled, when matched) for "
        "every pet-owning character. Whether the duplication is ingest-side "
        "or endpoint-side is discriminated by the 3h D2 re-fetch",

    # 🚨 3f F9 — THE FIRST ASSERTIONS IN THIS HARNESS THAT COMPARE A MODELLED
    # MAGNITUDE TO A MEASURED ONE. Both fail, both were EXPECTED to fail, and
    # the tolerance was committed one commit BEFORE they were run (eed2ec1).
    # 🛑 DO NOT WIDEN THE TOLERANCE TO CLOSE THESE. They are the instrument.
    "[frost_mage] modelled DPS is within the PRE-REGISTERED ±25% of the "
    "measured capture":
        "ENGINE_BUGS.md E16 (3i A3 — this value cited only E13/E14, both "
        "closed, so the entry was orphaned; AUDIT_3H §8). "
        "🆕 3g — E13 AND E14 ARE BOTH FIXED, AND THIS IS STILL RED. It has "
        "moved 90,202 -> 83,610 (G1, E13) -> 457 modelled DPS against a "
        "measured 1,382: +6,427% -> +5,950% -> -66.9%. The tolerance is "
        "UNCHANGED at ±25% and was not touched at any step. What remains is "
        "the ordinary under-production family — the same direction and roughly "
        "the same size as the cohort's slice accuracy, on a single character "
        "with a verified same-session stat block. This entry is no longer "
        "about two explosions; it is now the same open problem as the "
        "per-ability entry below, and closing it is a modelling question "
        "rather than a defect hunt",
    # 🛑 3f F10 — E9..E12 REGISTERED, NOT FIXED. Each is a real defect in the
    # code 3e wrote, each would move the gate, and each therefore belongs in a
    # modelling session with a before/after pair. 3d's D3 discipline: entries
    # first, fixes second. Do NOT close one of these by weakening its check.
    "[engine] E9: medium_sim routes a DoT by the SAME discriminator apl_gen "
    "and _useful_cast_interval use":
        "ENGINE_BUGS.md E9 — a THIRD DoT discriminator exists, in the layer "
        "that decides PRIORITY. apl_gen and _useful_cast_interval both use "
        "_is_pure_periodic; medium_sim's cast path uses `dur and "
        "tick_interval_seconds`. apl_gen's own comment claims the two layers "
        "cannot drift apart, and 1c07bab's commit message asserts they use the "
        "same test. An ability with a periodic aura at EffectAmplitude 0 lands "
        "in the MAINTAINED tier at the top of the APL, is routed to st.buffs, "
        "has debuff_remaining() return 0.0 forever, and wins every priority "
        "scan — the Seal of Command 47-of-47-GCDs failure re-created",
    "[engine] E10: target health decays to ~0 by the end of the fight, as "
    "_decay_target_health's own docstring says it does":
        "ENGINE_BUGS.md E10 — the decay divides by st.fight_duration while the "
        "timeline is bounded by fight_duration x (1 - movement_pct), so target "
        "health FLOORS at 100 x movement_pct on every preset (0.05-0.20). On "
        "world_boss that is 20.0, so `target_health_pct_below: 20` is "
        "permanently false in medium_sim while fast_sim credits 20% of casts",
    "[engine] E11: the PLAYER's health moves, so a self-sustain heal gated on "
    "health_pct_below can fire":
        "ENGINE_BUGS.md E11 — self_health_pct is declared on TimelineState, "
        "READ by apl.py, and WRITTEN NOWHERE. apl_gen emits health_pct_below "
        "for every heal under a self_sustain_required preset, so those entries "
        "can never fire in medium_sim, while fast_sim's _health_gate does not "
        "match the condition at all and casts them at full rate. E2's twin on "
        "the player side, unfixed and unnamed while E2 was closed",
    "[engine] E12: slow_sim rolls a finisher at the combo points medium_sim "
    "spent on it":
        "ENGINE_BUGS.md E12 — B4 threaded combo_points through _components -> "
        "expected_hit -> expected_cast but NOT through the RNG path, so "
        "slow_sim builds its skeleton from medium_sim at 5 CP and then rolls "
        "every cast at 0 CP. Measured on the fixture: the finisher scores 197 "
        "at 0 CP and 328 at 5 CP, a 1.7x difference, so the Monte-Carlo mean "
        "and 95% band are centred BELOW the answer they claim to be the "
        "variance of",
    # 🆕 3g G3 — E13 and E14 SPLIT OUT of the shared frost_mage DPS assertion.
    # Until now both were registered against that one aggregate, so neither
    # could be closed individually and the registry's "registered + now
    # PASSING -> hard failure" rule could not tell which of the two had moved.
    # These are UNIT invariants: true of any build, any content, any weapon.
    # ✅ E13's three assertions are CLOSED in 3g G1 and are deliberately absent
    # from this registry — a check that has started passing must LEAVE it, or
    # the registry stops meaning "these are the known failures". They still run,
    # every run, and a regression turns them into ordinary hard failures.
    # ✅ E14's three assertions are CLOSED in 3g G2 and are deliberately absent
    # for the same reason as E13's.
    "[frost_mage] every well-sampled ability's modelled per-cast mean is "
    "within ±25% of its measured non-crit mean":
        "ENGINE_BUGS.md E16 (3i A3 — this string appeared in no document and "
        "named no E-number until the doc-sync parser landed; AUDIT_3H §8). "
        "The ordinary under-production, now MEASURED per ability against a "
        "real capture for the first time: Frostbolt -34%, Ray of Frost -33%, "
        "Ice Lance -60%, Frozen Orb within, Icicle (830445) not modelled at "
        "all. Same direction as the gate's slice accuracy (20.5% at >=20% "
        "coverage since 3g; the ~64% this message cited until 3h was E13's "
        "number), on a single character with a verified same-session stat "
        "block — corroboration, not restatement. NOTE the whole-character "
        "figure is 457/1,382 = 33.1% with NO coverage term, vs the cohort's "
        "20.5% — reconciling those two is 3h Block C5. This entry is the one "
        "a future modelling session should be trying to close",
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


def check_engine_bugs_doc_sync():
    """3i A3 — ENGINE_BUGS.md's "enforced in both directions" claim, made true.

    Until 3i, `resolve_generality()` enforced EXPECTED_FAILURES against the
    check names that RAN, and nothing anywhere parsed ENGINE_BUGS.md — so the
    document's half of the promise was human-kept, and the 3h audit found it
    broken twice (a registered check whose string appeared in no document, and
    one owned only by two ✅ FIXED entries). This parses the document and
    asserts SET EQUALITY between the check names its OPEN entries claim and
    EXPECTED_FAILURES' keys.

    Parsing rules, matching the document's own stated conventions:
      * an entry is a section whose heading starts `## E<n>`;
      * a heading containing "✅ FIXED" or "NAMED, NOT MODELLED" is closed —
        its checks left the registry by the registry's own rule, and any Check
        rows below it (including historical ones kept in <details>) are record,
        not claim;
      * a `| **Check(s)** |` row containing "NONE" is the header invariant's
        stated exemption (E8): the entry explicitly discloses it has no check
        and claims nothing;
      * backticked names starting `[` are check names; the compressed
        `[a] / [b] / [c] tail` form expands to one name per bracket tag.

    Registered mutation M31 (RUN 2026-08-07): delete E16's Checks row — the
    two frost-mage keys become unclaimed and this goes RED. Green path:
    restore the row; the fix IS the document naming its checks.
    """
    import re
    path = config.PRIMER_DIR / "ENGINE_BUGS.md"
    text = path.read_text(encoding="utf-8")

    claimed = set()
    for section in re.split(r"(?m)^## ", text)[1:]:
        heading = section.splitlines()[0]
        if not re.match(r"E\d+", heading):
            continue
        if "✅ FIXED" in heading or "NAMED, NOT MODELLED" in heading:
            continue
        for m in re.finditer(r"(?m)^\|\s*\*\*Checks?\*\*\s*\|(.*)\|\s*$",
                             section):
            cell = m.group(1)
            if "NONE" in cell:
                continue        # the stated exemption — discloses, claims nothing
            for name in re.findall(r"`([^`]+)`", cell):
                name = " ".join(name.split())
                if not name.startswith("["):
                    continue    # a file path or symbol, not a check name
                comp = re.match(r"((?:\[\w+\]\s*/\s*)+\[\w+\])\s+(.*)", name)
                if comp:
                    tail = comp.group(2)
                    for tag in re.findall(r"\[\w+\]", comp.group(1)):
                        claimed.add(f"{tag} {tail}")
                else:
                    claimed.add(name)

    registered = {" ".join(k.split()) for k in EXPECTED_FAILURES}
    doc_only = sorted(claimed - registered)
    code_only = sorted(registered - claimed)
    check("ENGINE_BUGS.md open entries and EXPECTED_FAILURES claim the SAME "
          "check set — the document side of 'enforced in both directions' "
          "is parsed, not promised",
          not doc_only and not code_only,
          f"claimed={len(claimed)}, registered={len(registered)}"
          + (f"; DOC-ONLY {doc_only}" if doc_only else "")
          + (f"; CODE-ONLY {code_only}" if code_only else ""))


def main():
    # 🆕 3i A3 — the doc-sync check runs FIRST, before the db refusal below,
    # because it needs only the committed tree: a clean clone can verify the
    # registry↔document agreement even when it cannot run the engine checks.
    check_engine_bugs_doc_sync()

    # 🆕 3g G7 — A GUARD THAT CANNOT RUN MUST SAY SO. This used to die on a raw
    # `sqlite3.OperationalError` traceback when `data/derived/ascension.db` was
    # absent, where its sibling `check_gate_exclusion.py:97-100` refuses with a
    # message. `data/derived/` is gitignored, so a clean clone hits this every
    # time, and a traceback reads as "this tool is broken" rather than "this
    # tool needs a rebuild first".
    if not config.DB_PATH.exists():
        print(f"🛑 REFUSING TO RUN — {config.DB_PATH} does not exist.\n"
              f"   Every check below reads it, so running would prove nothing "
              f"about the engine.\n"
              f"   Build it first:  py cli/rebuild.py\n"
              f"   (data/derived/ is gitignored by design — the db is always "
              f"rebuildable from committed source.)")
        return 2
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
    check_e15_pet_row_double_count()
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
    """The UNBOUNDED tier — the spam buttons `fast_sim` allocates last.

    🚨 3f F3 — THIS DOCSTRING USED TO CLAIM THE CHECK "cannot drift from the
    code it tests by re-implementing the rule differently", AND THEN DID
    EXACTLY THAT. It classified on `cooldown_seconds`, which is what `tiers.py`
    used *before* `3e` B1. `fast_sim` now partitions on
    `_useful_cast_interval` into `cp_gated` / `bounded` / `unbounded` /
    `off_gcd` (`tiers.py:301-307`), and a cooldown-less **pure DoT** is
    `bounded` — allocated FIRST, not last — while this function still counted
    it as a filler. That corrupted the `EXPECTED_FAILURES` bookkeeping text,
    which quotes counts taken over the wrong set.

    The rule is now IMPORTED rather than restated: an ability is a filler iff
    `_useful_cast_interval` says nothing bounds it. If B1's partition changes
    again, this moves with it instead of silently disagreeing.

    🛑 MUTATION THAT MAKES THIS FAIL: change `_useful_cast_interval` to return
    a positive interval for everything. Every board reports zero fillers, and
    the vacuity guard in the caller goes red rather than passing on an empty
    set. *(Verified 3f.)*
    """
    from core.sim.tiers import _resolve_all, _useful_cast_interval
    off = {e.spell_id for e in apl.entries if e.off_gcd}
    ids = apl.spell_ids()
    abilities = _resolve_all(conn, ids, level, [])
    return [s for s in ids if s not in off and abilities.get(s)
            and _useful_cast_interval(abilities[s])[0] <= 0]


def check_registered_defects(conn, kind, spec, apl, f, m):
    """`3f` F10 — E9–E12, each with a check that FAILS. None is fixed here.

    `3d`'s D3 discipline: registry entries first, fixes second. Every one of
    these is a real defect in the code `3e` wrote, every one would move the
    gate, and every one therefore belongs in a modelling session with a
    before/after pair — not in an instrument session whose invariant is that
    the gate does not move.

    🛑 Each assertion is written to fail on the DEFECT, not on a symptom that
    might have another cause, so that closing the defect is what turns it
    green. Where a defect is not reachable on the three committed fixtures the
    check asserts the mechanism directly rather than pretending a fixture
    exercises it.
    """
    from core.sim import tiers as T
    from core.sim.apl import APL, APLEntry

    if kind != "cp_melee":
        return      # one board is enough to hold these; they are not per-fixture

    # ---- E9: a THIRD DoT discriminator, in the layer that decides priority --
    # apl_gen.py and tiers.py:_useful_cast_interval both use _is_pure_periodic;
    # medium_sim's buff/debuff routing uses `dur and tick_interval_seconds`.
    # apl_gen's own comment claims "the two layers cannot drift apart".
    class _FakeAb:
        name = "synthetic mixed direct+periodic, EffectAmplitude 0"
        fields = {"duration_seconds": 12.0, "tick_interval_seconds": None}

        def events(self):
            class E:
                kind = "periodic"
            return [E()]

    ab = _FakeAb()
    pure = T._is_pure_periodic(ab)
    # 🆕 3g G5 — GREEN PATH. This used to RE-IMPLEMENT the discriminator it is
    # testing (`bool(fields["duration_seconds"] and
    # fields["tick_interval_seconds"])`) against a fake whose tick interval is
    # None, so it was the literal constant False and could only go green on a
    # REGRESSION in `_is_pure_periodic`. It now IMPORTS the real routing
    # predicate that `medium_sim` calls (`tiers._routes_as_debuff`, extracted in
    # 3g G5 as a behaviour-preserving seam), so the GREEN PATH IS THE FIX:
    # make `_routes_as_debuff` return `_is_pure_periodic(ability)` and all three
    # layers share one discriminator.
    routed_as_debuff = T._routes_as_debuff(ab)
    gcheck("[engine] E9: medium_sim routes a DoT by the SAME discriminator "
          "apl_gen and _useful_cast_interval use",
          pure == routed_as_debuff,
          f"_is_pure_periodic says DoT={pure} (so apl_gen files it in the "
          f"MAINTAINED tier at the top of the APL, gated on "
          f"debuff_remaining_below); medium_sim's `dur and "
          f"tick_interval_seconds` says debuff={routed_as_debuff} (so it goes "
          f"to st.buffs, debuff_remaining() returns 0.0 forever, 0.0 < 1.5 is "
          f"always true, and the entry wins EVERY priority scan) — the Seal of "
          f"Command 47-of-47-GCDs failure re-created at the top of the list")

    # ---- E10: target-health decay is capped by movement_pct ----------------
    # _decay_target_health divides by st.fight_duration while the timeline is
    # bounded by fight_duration * (1 - movement_pct), so health FLOORS at
    # 100 * movement_pct.
    from core.sim.content import get_preset
    wb = get_preset("world_boss")
    st = T.TimelineState(fight_duration=wb.fight_duration)
    st.now = T._effective_time(wb)          # the LAST instant the loop reaches
    T._decay_target_health(st)
    # 🛑 The assertion is that health reaches ~ZERO, not that it dips under 20.
    # The first version of this check compared `< 20.0` against a floor of
    # exactly 20.0 and PASSED on floating-point luck — a knife-edge assertion
    # is not an assertion. The real property is the one _decay_target_health's
    # docstring claims: "target health falls linearly to 0 across the fight".
    # It does not; it stops at 100 * movement_pct, on EVERY preset.
    gcheck("[engine] E10: target health decays to ~0 by the end of the fight, "
          "as _decay_target_health's own docstring says it does",
          st.target_health_pct < 1.0,
          f"on world_boss (movement_pct {wb.movement_pct:g}) target health "
          f"FLOORS at {st.target_health_pct:.1f}% — the timeline is bounded by "
          f"{T._effective_time(wb):.0f}s while the decay divides by the full "
          f"{wb.fight_duration:.0f}s, so it can never fall below "
          f"100 x movement_pct. `target_health_pct_below: 20` is therefore "
          f"PERMANENTLY FALSE here in medium_sim while fast_sim credits the "
          f"ability 20% of its casts — E2's original symptom, unfixed on this "
          f"profile, and the two tiers disagree by up to 1.8x")

    # ---- E11: self_health_pct is declared, read, and written nowhere -------
    # 🆕 3g G5 — GREEN PATH. This used to call `_decay_target_health(st2)` and
    # then assert `st2.self_health_pct < 100.0`. That function touches only
    # `target_health_pct` — the string `self_health` does not appear in it — so
    # NO CORRECT FIX COULD EVER TURN THIS GREEN. It was a permanent alarm.
    # It now calls `tiers._decay_health`, the seam `medium_sim` actually invokes
    # (3g G5, currently delegating to `_decay_target_health` and nothing else),
    # so THE GREEN PATH IS THE FIX: decay `self_health_pct` there, beside its
    # sibling. ⚠ And not as a mirror of the target's linear 100 -> 0 — the
    # player is healed as well as damaged; see tiers._decay_health's docstring.
    st2 = T.TimelineState(fight_duration=100.0)
    st2.now = 50.0
    T._decay_health(st2)
    gcheck("[engine] E11: the PLAYER's health moves, so a self-sustain heal "
          "gated on health_pct_below can fire",
          st2.self_health_pct < 100.0,
          f"self_health_pct is still {st2.self_health_pct:.0f} at mid-fight — "
          f"declared on TimelineState, READ by apl.py's health_pct_below "
          f"branch, and WRITTEN NOWHERE in the tree. apl_gen emits "
          f"health_pct_below for every heal under a self_sustain_required "
          f"preset, so those entries can never fire in medium_sim, while "
          f"fast_sim's _health_gate does not match the condition at all and "
          f"casts them at FULL rate. E2's twin, on the player side")

    # ---- E12: roll_hit/roll_cast never received combo_points ---------------
    # slow_sim builds its skeleton from medium_sim (which casts at 5 CP) and
    # then rolls every cast at 0 CP, so a combo-point build's Monte-Carlo mean
    # is centred BELOW the medium-sim answer it claims to be the variance of.
    finisher = next((e.spell_id for e in apl.entries
                     if any(c.get("type") == "combo_points_at_least"
                            for c in (e.conditions or []))), None)
    if finisher is not None:
        from core.sim.ability_model import resolve_ability
        ab2 = resolve_ability(conn, finisher, level=spec.character_level)
        cs = m.content if hasattr(m, "content") else None
        at0 = ab2.expected_cast(_CS_FOR_E12[0], _CS_FOR_E12[1], combo_points=0)
        at5 = ab2.expected_cast(_CS_FOR_E12[0], _CS_FOR_E12[1], combo_points=5)
        differs = abs(at5.mean - at0.mean) > 0.01
        # 🆕 3g G5 — GREEN PATH. This used to read
        # `T._roll_uses_combo_points() if hasattr(T, ...) else False`, and
        # `grep -rn "_roll_uses_combo_points"` returned THAT LINE ONLY — the
        # function exists nowhere in the tree. So `rolled` was permanently
        # False, the assertion reduced to "the finisher's damage does not vary
        # with combo points" (which it does, by design), and THE ONLY WAY TO
        # TURN IT GREEN WAS TO ADD A STUB WITH THAT NAME. Threading combo_points
        # through roll_hit/roll_cast — the actual fix — left it red.
        #
        # It now exercises the RNG path directly: same seed, 0 CP vs 5 CP. Today
        # `roll_cast` takes no `combo_points` argument at all, so this raises
        # TypeError and `rolled` is False for a REAL reason. The fix — accepting
        # it and passing it down to `_components` — makes the two rolls differ
        # and the check green. No stub can satisfy it: it compares damage, not
        # the presence of a name.
        from random import Random
        try:
            r5 = ab2.roll_cast(_CS_FOR_E12[0], _CS_FOR_E12[1], Random(1),
                               combo_points=5)
            r0 = ab2.roll_cast(_CS_FOR_E12[0], _CS_FOR_E12[1], Random(1),
                               combo_points=0)
            rolled = abs(r5.damage - r0.damage) > 0.01
        except TypeError:
            rolled = False
        gcheck("[engine] E12: slow_sim rolls a finisher at the combo points "
              "medium_sim spent on it",
              rolled or not differs,
              f"finisher {finisher} scores {at0.mean:.0f} at 0 CP and "
              f"{at5.mean:.0f} at 5 CP (a {at5.mean / at0.mean:.1f}x "
              f"difference), and roll_hit/roll_cast call _components() with the "
              f"DEFAULT combo_points=0 — so slow_sim's mean and 95% band are "
              f"centred below the medium_sim answer they claim to be the "
              f"variance of. The docstring still asserts convergence is "
              f"'asserted by check_sim_engine.py'; that assertion runs at "
              f"combo_points=0 and passes vacuously")


def check_e13_e14_units(conn):
    """`3g` G3 — E13 and E14, one assertion EACH.

    🛑 They shared a single assertion until now (the frost_mage aggregate DPS
    check), so neither could be closed individually and the registry's own
    *"registered + now PASSING -> hard failure"* rule was blind between them:
    fixing either would have turned the shared check green-ish for the wrong
    reason, or left it red with no way to say which half moved. Splitting is a
    precondition of fixing, not a tidy-up.

    Both assertions are UNIT invariants, deliberately — they are true of any
    build, any content, any weapon, so they cannot be satisfied by tuning a
    fixture, and they stay meaningful after the fixture is replaced.
    """
    import core.sim.combat_engine as ce
    from core.sim.ability_model import PULSE_COUNT_SANITY_LIMIT, resolve_ability
    from core.sim.swings import expected_swing

    # ---- E13: probabilities are FRACTIONS, and a swing cannot beat a crit ---
    # RED: make AttackTable.probabilities() return percents again.
    # GREEN: the fix — probabilities() returns 0..1 and every consumer agrees.
    boss = ce.TargetProfile(level=63, armor=6200, dodge_pct=6.5, parry_pct=0.0)
    tbl = ce.white_melee_table(60, 20.0, 8.0, 5, boss, dual_wield=False)
    total = sum(tbl.probabilities().values())
    gcheck("[engine] E13: AttackTable.probabilities() returns FRACTIONS "
           "summing to 1.0, which is what every consumer multiplies by",
           abs(total - 1.0) < 1e-6,
           f"probabilities() sums to {total:.4f}; segments sum to "
           f"{sum(p for _, p in tbl.segments):.1f} (percent, which is correct "
           f"for segments — roll() draws uniform(0,100) from them). A function "
           f"named `probabilities` returning percent is the whole defect: "
           f"expected_swing multiplies by it as if it were 0..1")

    # The consequence, stated as a physical invariant rather than a unit one,
    # so it holds however the representation question is answered: the MEAN of
    # one swing cannot exceed the largest single outcome one swing can produce.
    class _CS:
        level = 60
        melee_crit_pct, melee_hit_pct, expertise_points = 20.0, 8.0, 5
        armor_pen_pct, ability_crit_damage_bonus = 0.0, 0.0
        main_hand = {"min": 100.0, "max": 200.0, "speed": 2.6}
        off_hand = None
        warnings = []

    out = expected_swing(_CS(), _CS.main_hand, boss)
    ceiling = _CS.main_hand["max"] * ce.crit_multiplier("melee", 0.0)
    gcheck("[engine] E13: one white swing's EXPECTED damage never exceeds one "
           "critical strike on the weapon's maximum roll",
           out is not None and 0.0 <= out.mean <= ceiling,
           f"mean {out.mean:.1f} vs a ceiling of {ceiling:.1f} "
           f"({out.mean / ceiling:.1f}x) — armor mitigation and every "
           f"non-crit outcome only push the mean DOWN, so a mean above the "
           f"ceiling is arithmetically impossible and can only be a unit error")
    gcheck("[engine] E13: SwingOutcome's *_fraction fields actually hold "
           "fractions, as their names say",
           out is not None and 0.0 <= out.landed_fraction <= 1.0
           and 0.0 <= out.crit_fraction <= 1.0,
           f"landed_fraction={out.landed_fraction:.4f}, "
           f"crit_fraction={out.crit_fraction:.4f}. ⚠ Tree-wide grep: these "
           f"two fields have ZERO readers anywhere — core/, tools/, cli/, "
           f"ingest/. They have been write-only and mis-united since they were "
           f"written, which is why nothing caught it")

    # ---- E14: a tick count needs ONE spell's duration and ONE spell's tick --
    # RED: drop the provenance refusal, or the count limit, in
    # occurrences_per_cast's periodic branch.
    # GREEN: the fix — both refusals present, both naming their reason.
    ab = resolve_ability(conn, 285148, level=60)      # Absolute Zero
    per = {ev.key: ab.occurrences_per_cast(ev) for ev in ab.events()}
    bad = {k: n for k, (n, _) in per.items()
           if n is not None and n > PULSE_COUNT_SANITY_LIMIT}
    gcheck("[engine] E14: no periodic component scores more occurrences per "
           "cast than the sanity limit its sibling branch already enforces",
           not bad,
           f"{ {k: n for k, (n, _) in per.items()} } against a limit of "
           f"{PULSE_COUNT_SANITY_LIMIT}. Absolute Zero's periodic event takes "
           f"its DURATION from the card (285148, 12.0s) and its TICK from the "
           f"triggered spell (285149, 0.001s) -> 12,000 ticks for one cast. "
           f"The periodic-trigger DELIVERY branch six lines above has enforced "
           f"this same limit since 2b; the plain periodic branch never did")

    # ⚠ THIS ASSERTION WAS RE-DERIVED IN 3g G2, and the reason is on the record
    # BEFORE the fix ran (predictions/prereg_3g_e14.md, committed at 5872b53).
    # Its first form asserted that Absolute Zero REFUSES and names both spells,
    # because the work order specified a refusal. Measuring first showed the
    # component's own duration is one join away (duration_index ->
    # dbc_spellduration), so the mixing can be STOPPED rather than detected —
    # and Absolute Zero then resolves correctly to ONE application instead of
    # refusing. An assertion that encodes a MECHANISM breaks when a better
    # mechanism arrives; this one now states the PROPERTY.
    ev_p = next((e for e in ab.events() if e.kind == "periodic"), None)
    n_p, _ = ab.occurrences_per_cast(ev_p) if ev_p else (None, None)
    own = ab.component_durations.get(ev_p.source_spell_id) if ev_p else None
    gcheck("[engine] E14: a periodic component's tick count comes from ONE "
           "spell's duration and that same spell's tick, never from two",
           ev_p is not None and own is not None and n_p == max(1, round(
               own / (ev_p.tick_interval_seconds or 1))),
           f"285149 states its own duration ({own}s) and its own tick "
           f"({ev_p.tick_interval_seconds if ev_p else None}s) -> n={n_p}. The "
           f"card's 12.0s is no longer consulted. ⚠ Measured across the frozen "
           f"cohort, the card's duration DISAGREES with the component's own in "
           f"11 of the 12 events built this way — Absolute Zero is only where "
           f"the disagreement is four orders of magnitude")

    # The refusal still exists, for what stays genuinely unknowable. No spell in
    # the corpus reaches it today (all 12 mixed-provenance components state a
    # duration), so it is exercised synthetically rather than left untested — an
    # untested refusal is a refusal nobody has seen refuse.
    class _Ev:
        key, source_spell_id, via, kind = "hidden_ref:999:periodic", 999, "hidden_ref", "periodic"
        tick_interval_seconds, is_attributed = 2.0, True
        fields = {"duration_seconds": 30.0}
        delivery = None

    stub = ab.__class__(**{**ab.__dict__, "component_durations": {}})
    n_s, note_s = stub.occurrences_per_cast(_Ev())
    gcheck("[engine] E14: when the component states NO duration of its own, "
           "the mix is REFUSED and both spells are named",
           n_s is None and "999" in (note_s or "")
           and str(ab.spell_id) in (note_s or ""),
           f"n={n_s}, note={(note_s or '(none)')[:120]}")


_CS_FOR_E12 = (None, None)      # filled by check_nonpaladin_fixtures


def check_ground_truth(kind, bd, f, m):
    """`3f` F9 — compare a MODELLED magnitude to a MEASURED one.

    🚨 Until this existed, **no assertion anywhere in the harness compared a
    modelled magnitude to a measured one, on any of the three fixtures.** They
    could catch a crash and a structural property and nothing else — which is
    the exact limitation `ADDENDUM_3D_to_3E_mage_capture.md:141-142` invoked to
    justify preferring a real capture, and then the real capture arrived
    carrying inputs only.

    🛑 **THE TOLERANCE IS PRE-REGISTERED IN THE FIXTURE AND IS NOT READ FROM
    HERE.** It was committed one commit before this assertion ran (`eed2ec1`),
    for a reason stated in the fixture, and it is expected to FAIL. Do not
    widen it to make this green: that is the failure this project has spent
    three sessions building machinery against. If it is ever widened, the
    widening is dated and reasoned in the fixture, in its own commit.

    A fixture with no `ground_truth` is SKIPPED, not passed — the two crawled
    boards carry `ground_truth_absent` explaining why no measured magnitude
    exists for them, and a silent pass there would be the vacuity this session
    is about.

    MUTATION THAT MAKES THIS FAIL DIFFERENTLY: scale `fast_sim`'s total by 2.
    The DPS assertion's delta moves by +100 points. It is already red, so the
    proof that it BINDS is that its reported delta tracks the model rather than
    being a constant — which is why the number is printed, not just a verdict.
    """
    gt = bd.get("ground_truth")
    if not gt:
        if bd.get("ground_truth_absent"):
            print(f"SKIP  [{kind}] ground truth: "
                  f"{bd['ground_truth_absent']['status']} — "
                  f"{bd['ground_truth_absent']['_what_would_close_it'][:88]}...")
        return

    tol = gt["tolerance_pct"]
    measured = gt["player_dps"]
    # The sim models the PLAYER only — pets are a named, unmodelled gap (E3),
    # so comparing against the pet-inclusive figure would score a known
    # omission twice.
    modelled = f.primary_value
    delta = 100.0 * (modelled / measured - 1) if measured else None
    gcheck(f"[{kind}] modelled DPS is within the PRE-REGISTERED ±{tol:g}% of "
          f"the measured capture",
          delta is not None and abs(delta) <= tol,
          f"modelled {modelled:.0f} vs measured {measured:.0f} DPS "
          f"({delta:+.1f}%, tolerance ±{tol:g}% registered at {gt['_evidence_ref']}); "
          f"pet excluded from both sides ({gt['pet_share_pct']:.1f}% of the "
          f"capture, an unmodelled gap by E3)")

    rows = [r for r in gt["per_ability_noncrit_mean"]
            if r["n"] >= gt["_per_ability_min_n"]]
    hit, miss, absent = [], [], []
    for r in rows:
        rec = f.per_ability.get(r["spell_id"]) or f.per_ability.get(r["card_spell_id"])
        if not rec or not rec.get("mean_per_cast"):
            absent.append(f"{r['name']}({r['spell_id']})")
            continue
        d = 100.0 * (rec["mean_per_cast"] / r["mean"] - 1)
        (hit if abs(d) <= tol else miss).append(f"{r['name']} {d:+.0f}%")
    gcheck(f"[{kind}] every well-sampled ability's modelled per-cast mean is "
          f"within ±{tol:g}% of its measured non-crit mean",
          bool(rows) and not miss and not absent,
          f"{len(hit)} within, {len(miss)} outside, {len(absent)} not modelled "
          f"at all. outside: {miss or '-'}; unmodelled: {absent or '-'}")


def check_e15_pet_row_double_count():
    """3h C4 / E15 — a pet-attributable row stored twice must be counted once.

    RED (current state): `modelled_damage_share` sums every ability_performance
    row, so an owner row and a byte-identical pet row for the same spell both
    enter the coverage denominator (and the numerator, when the spell is
    keyed). Measured corpus-wide at 3h C4: 15,551 of 20,785 owner+pet groups
    are byte-identical.

    GREEN PATH (run at 3h C4 and reverted — it moves coverage and therefore
    the gate, so it belongs to a later session's own commit): dedupe rows
    whose (spell_id, spell_name, damage_total) appears with both is_pet=0 and
    is_pet=1 inside the same scope+character, keeping the owner copy.

    Fixture: spell 555 logged 1000 twice (owner + identical pet row), spell
    666 logged 1000 once, spell 555 keyed and producing. Counted once, the
    share is 50.0%; the current double-count reads 66.7%.
    """
    import sqlite3 as _sq
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import calibrate_crawled as cc

    conn = _sq.connect(":memory:")
    conn.execute(
        "CREATE TABLE ability_performance (scope_id INT, character_id INT, "
        "spell_id INT, spell_name TEXT, damage_total REAL, is_pet INT, "
        "spell_school TEXT)")
    conn.executemany(
        "INSERT INTO ability_performance VALUES (?,?,?,?,?,?,?)",
        [(1, 7, 555, "Pet Spell", 1000.0, 0, "shadow"),
         (1, 7, 555, "Pet Spell", 1000.0, 1, "shadow"),   # byte-identical dup
         (1, 7, 666, "Own Spell", 1000.0, 0, "fire")])
    per_ability = {555: {"name": "Pet Spell", "casts": 2.0, "damage": 500.0,
                         "mean_per_cast": 250.0, "events": [{"kind": "direct"}],
                         "attributed": True, "unresolved_events": []}}
    out = cc.modelled_damage_share(conn, 1, 7, per_ability)
    gcheck("[corpus] identical owner+pet rows in ability_performance are "
           "counted ONCE in the coverage denominator",
           out is not None and out["modelled_damage_pct"] == 50.0,
           f"modelled_damage_pct={out and out['modelled_damage_pct']} "
           f"(counted once it is 50.0; the double-count reads 66.7)")


def check_nonpaladin_fixtures(conn, ct, conv):
    """Generality checks. See §9 above — these are MEANT to fail today."""
    from core.sim.apl_gen import generate_apl
    from core.sim.tiers import fast_sim, medium_sim

    print("\n--- 3d D1: non-paladin fixtures — XFAIL = a known engine defect "
          "written up in primer/ENGINE_BUGS.md, scheduled for 3e ---")

    # 3g G3 — run ONCE, not once per fixture: these are unit invariants of the
    # engine, not properties of a board.
    check_e13_e14_units(conn)

    # 3e C2 — the Frost Mage joins the two 3d fixtures rather than replacing
    # either: it is BURST, not DoT, and has no combo points, so it cannot
    # exercise what they exercise. What it reaches that a Hammerdin structurally
    # cannot: cast-time filler ordering, mana as a binding constraint, and
    # channels. It is also the only fixture built from a VERIFIED same-session
    # stat block (parsed, not transcribed) with a paired log.
    for filename, kind in (("build_crawled_cp_melee.json", "cp_melee"),
                           ("build_crawled_dot_caster.json", "dot_caster"),
                           ("build_elric_frost_mage.json", "frost_mage")):
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

        # 🛑 3f F3 — VACUITY GUARD, separated out. The condition below was
        # `len(fillers) < 2 or len(firing) >= 2`, which PASSES when `fillers` is
        # empty — so a renamed field or a failing `_resolve_all` would have
        # emptied the set and turned this green. On `cp_melee` that entry is not
        # in EXPECTED_FAILURES, so the vacuous pass would have been silent.
        # Every one of these three fixtures is known to carry ≥2 fillers.
        gcheck(f"[{kind}] the board has fillers to allocate at all (guards the "
              f"allocation check against passing vacuously)",
              len(fillers) >= 2,
              f"{len(fillers)} unbounded on-GCD entries"
              if len(fillers) >= 2 else
              f"only {len(fillers)} — the allocation check below would pass "
              f"having tested nothing")
        gcheck(f"[{kind}] fast_sim allocates GCDs to more than one filler",
              len(fillers) >= 2 and len(firing) >= 2,
              f"{len(firing)} of {len(fillers)} on-GCD fillers received any "
              f"casts ({len(acting)} abilities did damage overall, which is why "
              f"the old form of this check passed). Fillers that never cast: "
              f"{sorted(str(s) for s in fillers if s not in firing)[:8]}")

        if kind == "cp_melee":
            # `TimelineState.combo_points` / `apl.py`'s `combo_points_at_least`
            # branch (line numbers deliberately dropped in 3f F8 — the ones
            # here were stale, and A6 introduced fresh stale ones while
            # fixing older stale ones) — `combo_points` is never
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

            # 🚨 3f F3 — THIS CHECK WAS A CONSTANT `True` AND E2 WAS CLOSED ON
            # IT. The old form was `warned = any("health" in w.lower() ...)`,
            # and `3e` B5 appends `EXECUTE_GATING_UNAVAILABLE` UNCONDITIONALLY
            # from both tiers (`tiers.py:468,686`) with the substring
            # `AURA_STATE_HEALTHLESS_20_PERCENT` in it. So the predicate was
            # satisfied for every build, every fixture, forever — revert
            # `_decay_target_health` entirely, pinning target health back at
            # 100, and the check still printed PASS.
            #
            # It now asserts the DECAY BEHAVIOUR, which is a real property of
            # the mechanism E2 was closed on: target health at the fight's
            # midpoint must not still be 100.
            #
            # 🛑 MUTATION THAT MAKES THIS FAIL: make `_decay_target_health` a
            # no-op (or restore `target_health_pct = 100.0`). *(Verified 3f.)*
            from core.sim.tiers import TimelineState, _decay_target_health
            _probe = TimelineState(fight_duration=100.0)
            _probe.now = 50.0
            _decay_target_health(_probe)
            decays = _probe.target_health_pct < 99.0

            # `hp_gated` is narrowed to `target_health_pct_below` ONLY.
            # It used to accept `health_pct_below` as well, which `apl_gen.py`
            # emits for SELF-SUSTAIN HEALS under solo/dungeon presets — so any
            # board with a heal satisfied an EXECUTE-WINDOW check. Different
            # actor, different mechanism.
            hp_gated = {e.spell_id for e in apl.entries
                        if any(c.get("type") == "target_health_pct_below"
                               for c in (e.conditions or []))}
            hw_casts = m.per_ability.get(24239, {}).get("casts", 0)
            # 🆕 3g G6 — `named` IS A CONSTANT AND IS NO LONGER ASSERTED ON.
            # EXECUTE_GATING_UNAVAILABLE (whose text contains "TargetAuraState")
            # is `warnings.append`-ed UNCONDITIONALLY at tiers.py:468 and :687,
            # so `any("TargetAuraState" in w ...)` is the literal constant True.
            # F3 correctly diagnosed the OLD form — `any("health" in w.lower())`
            # — as a constant True and replaced it with a different constant
            # True, three functions after condemning exactly this drift.
            #
            # Only `decays` is falsifiable (M8 turns it red), so only `decays`
            # is asserted. `named` is still COMPUTED and still PRINTED, because
            # a reader wants to see the disclosure is there — but it is labelled
            # as unconditional so nobody reads it as an independent result.
            named = any("TargetAuraState" in (w or "")
                        for w in (m.warnings or []) + (f.warnings or []))
            gcheck("[cp_melee] the execute window is modelled, or the sim says "
                  "it cannot model it",
                  decays,
                  f"target health at mid-fight = {_probe.target_health_pct:.0f}% "
                  f"(decays: {decays} — THE ONLY FALSIFIABLE ARM). The "
                  f"TargetAuraState disclosure is present: {named}, but that "
                  f"warning is appended UNCONDITIONALLY, so it is reported and "
                  f"NOT asserted on (3g G6). Hammer of Wrath (24239) is "
                  f"execute-gated in game and the sim cast it {hw_casts}x with "
                  f"{len(hp_gated)} target-health-gated APL entries — which is "
                  f"the part that is NOT fixed and is not claimed to be: "
                  f"TargetAuraState is absent from the extract, so WHICH "
                  f"abilities are execute-gated is not derivable")

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
        #
        # ⚠ 3e B6 — this used to find pets by STRING-MATCHING "summon" in the
        # ability's name, which is the thing rule 5 forbids, inside the harness
        # that polices the rest of the engine. It now asks the same mechanical
        # detector the sim uses (SPELL_EFFECT_SUMMON + its creature id), so the
        # check and the code cannot disagree about what a pet is.
        from core.sim.pets import detect_summons
        summons = detect_summons(conn, [a["spell_id"] for a in bd["abilities"]])
        # 🛑 Same vacuity guard as the DoT check: if the detector found nothing
        # this check must not report "the gap is named" having tested nothing.
        gcheck(f"[{kind}] the fixture's summons are detectable at all "
              f"(guards the pet check against passing vacuously)",
              bool(summons),
              f"{len(summons)} summon effect(s) on the board: "
              f"{[s['name'] for s in summons]}")
        if summons:
            # 🚨 3f F3 — THE OLD FORM COULD NOT FAIL. It computed
            # `detect_summons(conn, [a["spell_id"] for a in bd["abilities"]])`
            # and then asserted a warning containing "pet" exists — but
            # `tiers.py` computes `pet_gap_warning(detect_summons(conn, [c.spell_id
            # for c in build_spec.abilities]))`, and `_load_fixture` builds
            # `spec.abilities` 1:1 from `bd["abilities"]`. Same pure function,
            # same ids, both sides. Given the vacuity guard above passes,
            # `pet_warned` was NECESSARILY true. B6 added a correct vacuity
            # guard and then wrote an assertion the guard made unfalsifiable.
            #
            # The real property is that the DETECTOR finds this fixture's known
            # summon BY SPELL ID — which is what rule 5 is about, and what the
            # name-matching version got wrong in both directions. The id is
            # named here rather than derived, so a detector that silently
            # stopped resolving SPELL_EFFECT_SUMMON goes red instead of
            # agreeing with itself.
            #
            # 🛑 MUTATION THAT MAKES THIS FAIL: have `detect_summons` return
            # rows carrying the WRONG spell_id — non-empty, so the vacuity
            # guard still passes, but no longer the board's known summon. That
            # is precisely the case the old check could not see: both sides
            # would have agreed on the wrong answer together. The three id
            # assertions go red. *(Verified 3f; returning [] also works, but it
            # trips the vacuity guard first and so tests less.)*
            # Read off each fixture once (2026-08-06) and PINNED here, so the
            # assertion is against a stated fact rather than against whatever
            # the detector happens to return today. Each is a
            # SPELL_EFFECT_SUMMON row carrying a creature id:
            #   282977 Summon Void Zone -> creature 80624   (cp_melee)
            #   954611 Hand of Gul'dan  -> creature 855350  (dot_caster)
            #   31687  Summon Water Elemental -> creature 510 (frost_mage,
            #          and the pet whose 5.0% damage share the capture measures)
            known = {"cp_melee": 282977, "dot_caster": 954611,
                     "frost_mage": 31687}.get(kind)
            found_ids = {s.get("spell_id") for s in summons}
            pet_warned = any("pet" in (w or "").lower()
                             for w in (f.warnings or []) + (m.warnings or []))
            gcheck(f"[{kind}] the summon detector finds this board's KNOWN "
                  f"summon by spell id, not by agreeing with itself",
                  known in found_ids,
                  f"expected spell {known} among detected {sorted(found_ids)}")
            gcheck(f"[{kind}] pet damage is modelled or explicitly named as a gap",
                  pet_warned,
                  f"board summons {[s['name'] for s in summons]}; a warning "
                  f"names each pet and the measured size of the gap: "
                  f"{pet_warned}. The corpus dps this is calibrated against "
                  f"INCLUDES pet damage, and pet damage is NOT modelled — "
                  f"creature stats are not in any client DBC")

        check_ground_truth(kind, bd, f, m)
        global _CS_FOR_E12
        _CS_FOR_E12 = (cs, ct)
        check_registered_defects(conn, kind, spec, apl, f, m)


if __name__ == "__main__":
    sys.exit(main())
