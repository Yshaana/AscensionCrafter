"""Phase 2 T11 — build comparison with per-ability attribution.

The clause that matters most here is the one about significance:

> a 2% difference between two builds whose uncertainty is ±10% is **not a
> result**, and the tool should say so rather than ranking them.

So `diff_builds` returns a `verdict` before it returns a winner, and when the
delta sits inside the combined uncertainty the verdict is `inconclusive` and
`winner` is None. Ranking two builds that the model cannot distinguish is the
most likely way for this whole stack to give confidently wrong advice, because
the output looks exactly like a real answer.
"""
from ..builds.spec import SlottedCard  # noqa: F401  (documents the input shape)


def _card_map(cards):
    return {c.spell_id: c.rank for c in cards}


def _diff_cards(a, b):
    ma, mb = _card_map(a), _card_map(b)
    added = [{"spell_id": s, "rank": mb[s]} for s in mb if s not in ma]
    removed = [{"spell_id": s, "rank": ma[s]} for s in ma if s not in mb]
    # A rank change is a real build change — PHASE_2 T4: "a build with 3/5 cards
    # is a different build" — so it is reported, never folded into "unchanged".
    ranked = [{"spell_id": s, "from": ma[s], "to": mb[s]}
              for s in ma if s in mb and ma[s] != mb[s]]
    return {"added": added, "removed": removed, "rank_changed": ranked,
            "unchanged": [s for s in ma if s in mb and ma[s] == mb[s]]}


def diff_builds(conn, a, b, content, char_state_a, char_state_b, *,
                apl_a=None, apl_b=None, tier="medium",
                uncertainty_a=None, uncertainty_b=None):
    """Compare two builds, attributing the DPS delta per ability.

    `uncertainty_a` / `uncertainty_b` are `sim_with_uncertainty` results (or any
    dict with `low`/`high`). Supply them: without them the significance verdict
    degrades to `unknown`, which is honest but much less useful.
    """
    from .tiers import fast_sim, medium_sim

    def run(spec, cs, apl):
        if tier == "fast":
            return fast_sim(conn, spec, content, cs, apl=apl)
        return medium_sim(conn, spec, apl, content, cs)

    ra, rb = run(a, char_state_a, apl_a), run(b, char_state_b, apl_b)
    delta = rb.primary_value - ra.primary_value
    pct = (100.0 * delta / ra.primary_value) if ra.primary_value else None

    # --- per-ability attribution ---------------------------------------------
    names = {}
    for res in (ra, rb):
        for sid, row in res.per_ability.items():
            names[sid] = row.get("name") or str(sid)
    attribution = []
    for sid, name in names.items():
        da = ra.per_ability.get(sid, {}).get("damage", 0.0)
        db = rb.per_ability.get(sid, {}).get("damage", 0.0)
        if da == db:
            continue
        attribution.append({
            "spell_id": sid, "name": name, "damage_a": da, "damage_b": db,
            "delta": db - da,
            "share_of_delta_pct": (100.0 * (db - da) / delta) if delta else None,
        })
    attribution.sort(key=lambda r: -abs(r["delta"]))

    # --- is the delta bigger than what we do not know? -----------------------
    def band(u, res):
        if u and u.get("low") is not None and u.get("high") is not None:
            return u["high"] - u["low"]
        return None

    ba, bb = band(uncertainty_a, ra), band(uncertainty_b, rb)
    if ba is None or bb is None:
        verdict, winner = "unknown", None
        reason = ("no uncertainty supplied for one or both builds, so it is not "
                  "known whether this delta exceeds what the model does not "
                  "know. Pass sim_with_uncertainty results to get a verdict")
    else:
        # Combined half-width, treating the two bands as independent.
        combined = ((ba / 2.0) ** 2 + (bb / 2.0) ** 2) ** 0.5
        if abs(delta) <= combined:
            verdict, winner = "inconclusive", None
            reason = (
                f"the {abs(delta):.0f} DPS delta is INSIDE the combined "
                f"knowledge uncertainty (+/-{combined:.0f}). These two builds "
                "are not distinguishable by this model — reporting a winner "
                "would be reporting noise")
        else:
            verdict = "significant"
            winner = "b" if delta > 0 else "a"
            reason = (f"the {abs(delta):.0f} DPS delta exceeds the combined "
                      f"knowledge uncertainty (+/-{combined:.0f})")

    return {
        "tier": tier,
        "dps_a": ra.primary_value, "dps_b": rb.primary_value,
        "delta": delta, "delta_pct": pct,
        "verdict": verdict, "winner": winner, "significance_reason": reason,
        "abilities": _diff_cards(a.abilities, b.abilities),
        "talents": _diff_cards(a.talents, b.talents),
        "gear_changed": sorted(
            set(a.gear) ^ set(b.gear)
            | {s for s in set(a.gear) & set(b.gear)
               if a.gear[s].item_id != b.gear[s].item_id}),
        "attribution": attribution,
        # Both builds' warnings, kept separate: a warning that fires on only one
        # side is itself a reason to distrust the comparison.
        "warnings_a": ra.warnings, "warnings_b": rb.warnings,
        "warnings_only_on_one_side": sorted(
            set(ra.warnings) ^ set(rb.warnings)),
    }
