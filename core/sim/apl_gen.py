"""Phase 2 T5 — default APL generation.

Produces a priority list from a BuildSpec so builds can be compared without
hand-authoring a rotation for each one, and so the guide generator has a
rotation section to render (PHASE_2 T5).

Priority rules, in order:
  0. MAINTAINED DEBUFFS (a periodic effect with a duration) before cooldowns,
     each gated on its own remaining time so it is refreshed near expiry rather
     than spammed. See `3e` B3 / ENGINE_BUGS E5 — a DoT carries no cooldown, so
     it used to be filed as a *filler*, behind every cooldown ability, and on a
     real DoT-caster board with nine cooldowns the GCD budget was gone before
     the rotation reached it: **6 of 7 DoTs cast zero times.** Gating is what
     makes a high priority safe — a maintained debuff is unavailable almost all
     of the time, so it cannot monopolise the list;
  1. cooldown abilities next, longest cooldown first — a long cooldown that
     slips is unrecoverable, a filler that slips costs one GCD;
  2. then by damage per GCD;
  3. quadratic combo-point finishers gated at MAX combo points — the primer's
     "never dump below max CP" rule is structural, not a preference: going 3->5
     CP is ~2.8x, not 1.67x;
  4. self-sustain abilities gated on health when the content profile requires
     it — a solo build that never heals is not the build being evaluated;
  5. off-GCD abilities are marked as such so they are queued alongside, not
     instead of, a GCD action.

⚠ This is "good enough to compare builds", not an optimiser. It does not search
orderings, and a hand-authored APL will usually beat it.
"""
from .ability_model import resolve_ability, AbilityResolutionError
from .apl import APL, APLEntry, MAX_COMBO_POINTS
from .tiers import _is_pure_periodic, _is_next_swing

SELF_SUSTAIN_HEALTH_PCT = 50.0

# 3e B3 — how close to expiry a maintained debuff is refreshed. One GCD's worth,
# which is the smallest window that cannot clip the DoT, and it is the reason the
# ability can sit at high priority without spamming. ⚠ Named and stated rather
# than tuned: retail's "pandemic" rule refreshes at 30% of duration remaining and
# this is deliberately NOT that, because our engine has no evidence Ascension
# implements pandemic and inventing one would be fabricating a mechanic.
DEBUFF_REFRESH_WINDOW_S = 1.5


def generate_apl(conn, build_spec, content, char_state, name=None):
    """Build a default APL. Abilities the resolver refuses are omitted AND
    named in the APL's provenance — a silently dropped ability would change the
    rotation without saying so."""
    scored, refused = [], []
    for card in build_spec.abilities:
        try:
            ab = resolve_ability(conn, card.spell_id,
                                 level=build_spec.character_level)
        except AbilityResolutionError as e:
            refused.append(f"{card.spell_id} ({e})")
            continue
        exp = ab.expected_cast(char_state, content)
        if exp.mean <= 0 and not exp.unresolved_events:
            continue                      # no damage: not a rotational button
        cd = ab.fields.get("cooldown_seconds") or 0.0
        gt = ab.fields.get("gcd_type")
        # 🚨 3n B leg 1 — a NEXT-SWING ability costs no GCD. It replaces your
        # next white swing, so it is queued alongside a GCD action exactly like
        # a declared off-GCD ability, and it must NOT enter the filler ranking
        # below — that ranking sorts by damage per CAST, and a next-swing
        # ability's casts are bought with swings, not GCDs. Ranking the two
        # against each other compares different clocks, which is what dropped
        # Lightbound Cleave out of Blix's rotation entirely (41% of his logged
        # damage) while Plague Strike's higher per-cast damage took the budget.
        #
        # ⚠ Testing `gcd_type` alone does NOT catch these: every one of the 11
        # next-swing ids in the corpus resolves `gcd_type = None`. Hence the
        # attribute test, shared with `fast_sim` via `_is_next_swing`.
        next_swing = _is_next_swing(ab)
        off_gcd = gt in ("none", "off") or next_swing
        dur = ab.fields.get("duration_seconds") or 0.0
        scored.append({
            "ability": ab, "spell_id": ab.spell_id, "cooldown": cd,
            "off_gcd": off_gcd, "next_swing": next_swing, "mean": exp.mean,
            # 3e B3 — a MAINTAINED DEBUFF: something applied to the target that
            # ticks and falls off, and whose damage is ENTIRELY those ticks.
            # ⚠ "has a periodic component" is NOT the test, and using it was a
            # real misclassification the fixture caught: Fireball leaves a 4s
            # DoT rider but is a direct nuke, and gating it on debuff uptime
            # models a Fire mage casting Fireball 10 times a minute. Shares
            # `tiers._is_pure_periodic` so the two layers cannot drift apart.
            "debuff_duration": (
                dur if (dur > 0 and _is_pure_periodic(ab)) else 0.0),
            # 3e B4 (ENGINE_BUGS E1) — this read `cp_scaling` ALONE, and on a
            # real combo-point board that classified NONE of the four abilities
            # carrying a genuine per-combo term as finishers: Rupture, Crimson
            # Tempest, Panache and Aether Rupture all carry `per_combo` (a
            # decoded flat per combo point, EffectPointsPerCombo) while
            # `cp_scaling` is set only on COEFFICIENT terms parsed from tooltip
            # text — and is None even there on this board. So zero APL entries
            # were CP-gated and the finishers cast freely as ordinary fillers,
            # which is why a naive "does a finisher ever cast?" check would have
            # passed while both halves of E1 were live.
            "is_finisher": any(
                t.get("per_combo") or t.get("cp_scaling")
                for t in ab.damage_terms),
            "is_quadratic": any(
                t.get("cp_scaling") == "quadratic" for t in ab.damage_terms),
            "heals": exp.mean_healing > 0,
        })

    # off-GCD first (they cost nothing to queue), then MAINTAINED DEBUFFS, then
    # cooldowns longest-first, then fillers by damage.
    #
    # 3e B3 — the maintained-debuff tier is new and it is the whole E5 fix.
    # A DoT has no cooldown, so it used to land in `fillers` behind every
    # cooldown ability; on the DoT-caster fixture that is nine of them, and the
    # GCD budget ran out first. It is safe at high priority ONLY because each
    # entry is gated on its own remaining duration below — an ungated DoT at the
    # top of the list would be re-cast every GCD, which re-scores its entire
    # duration each time (`expected_cast` scores duration/tick ticks per cast).
    # That is why E4's grammar had to land first: this fix is not expressible
    # without `debuff_remaining_below`.
    # 3n B — within the off-GCD tier, next-swing abilities are ordered by damage
    # per SWING (which is their per-cast damage, since each costs exactly one
    # swing). That is a comparison inside ONE clock, which is legitimate; the
    # defect was comparing across two.
    off = sorted([s for s in scored if s["off_gcd"]],
                 key=lambda s: (not s["next_swing"], -s["mean"]))
    on_gcd = [s for s in scored if not s["off_gcd"]]
    maintained = sorted([s for s in on_gcd if s["debuff_duration"] > 0],
                        key=lambda s: -s["mean"])
    rest = [s for s in on_gcd if s["debuff_duration"] <= 0]
    # 3e B4 — FINISHERS get their own tier, ABOVE ordinary fillers.
    # Detection alone was not enough: with the finisher left among the fillers,
    # a higher-damage filler carrying `always` won every scan and the CP-gated
    # entry never got a turn, so it still cast zero times after `is_finisher`
    # was fixed. It is safe up here for the same reason a maintained debuff is —
    # it is gated, and unavailable until the combo points are actually there.
    finishers = sorted([s for s in rest if s["is_finisher"]],
                       key=lambda s: -s["mean"])
    rest = [s for s in rest if not s["is_finisher"]]
    cds = sorted([s for s in rest if s["cooldown"] > 0],
                 key=lambda s: -s["cooldown"])
    fillers = sorted([s for s in rest if not s["cooldown"]],
                     key=lambda s: -s["mean"])

    entries = []
    for s in off:
        entries.append(APLEntry(
            spell_id=s["spell_id"], conditions=[{"type": "always"}],
            off_gcd=True,
            comment=(f"{s['ability'].name}: ON-NEXT-SWING — replaces a main-hand "
                     "white swing, so it costs no GCD and is bounded by the "
                     "weapon swing timer, not the GCD budget"
                     if s["next_swing"] else
                     f"{s['ability'].name}: off-GCD, queue alongside a GCD action")))

    if content.self_sustain_required:
        for s in scored:
            if s["heals"] and not s["off_gcd"]:
                entries.append(APLEntry(
                    spell_id=s["spell_id"],
                    conditions=[{"type": "health_pct_below",
                                 "value": SELF_SUSTAIN_HEALTH_PCT}],
                    comment=f"{s['ability'].name}: self-sustain, gated on health "
                            "because this content profile requires it"))

    for s in maintained:
        # Gated on ITS OWN remaining time on the target, which is what makes a
        # high priority safe: the entry is unavailable for all but the last
        # ~1.5s of the debuff, so it refreshes without clipping and cannot
        # monopolise the priority list.
        conds = [{"type": "debuff_remaining_below",
                  "spell_id": s["spell_id"],
                  "value": DEBUFF_REFRESH_WINDOW_S}]
        # A maintained debuff can ALSO be a finisher — Rupture and Aether
        # Rupture are both. It then carries both gates, because both are true
        # of it: refresh near expiry, and only at max combo points.
        if s["is_finisher"]:
            conds.append({"type": "combo_points_at_least",
                          "value": MAX_COMBO_POINTS})
        entries.append(APLEntry(
            spell_id=s["spell_id"],
            conditions=conds,
            comment=(f"{s['ability'].name}: maintained debuff "
                     f"({s['debuff_duration']:g}s), refreshed under "
                     f"{DEBUFF_REFRESH_WINDOW_S:g}s remaining"
                     + (f"; own cooldown {s['cooldown']:g}s"
                        if s["cooldown"] else "")
                     + (f"; ALSO a finisher, held to {MAX_COMBO_POINTS} CP"
                        if s["is_finisher"] else ""))))

    for s in finishers:
        comment = (f"{s['ability'].name}: finisher held to "
                   f"{MAX_COMBO_POINTS} CP")
        if s["is_quadratic"]:
            comment += " — QUADRATIC CP scaling, never dump below max"
        entries.append(APLEntry(
            spell_id=s["spell_id"],
            conditions=[{"type": "combo_points_at_least",
                         "value": MAX_COMBO_POINTS}],
            comment=comment))

    for s in cds:
        entries.append(APLEntry(
            spell_id=s["spell_id"], conditions=[{"type": "always"}],
            comment=f"{s['ability'].name}: on cooldown ({s['cooldown']:g}s)"))

    for s in fillers:
        entries.append(APLEntry(
            spell_id=s["spell_id"], conditions=[{"type": "always"}],
            comment=f"{s['ability'].name}: filler"))

    prov = (f"auto-generated by apl_gen for content={content.name}; "
            f"{len(entries)} entries")
    if refused:
        prov += f". OMITTED (resolver refused): {'; '.join(refused)}"
    return APL(name=name or f"auto_{content.name}", entries=entries,
               provenance=prov)
