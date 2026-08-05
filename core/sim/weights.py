"""Phase 2 T7 (partial) — stat weights and path comparison.

Owner decision 2026-08-05: 2b takes the CHEAP half of T7. `gear_tier_presets`
and `scaling_curve` are deferred to Phase 3, which owns the `items` table —
without it they would run on hand-invented stat blocks, which is the class of
made-up input this project keeps getting burned by.

Points the phase doc insists on, implemented here:

* **Per content profile.** Raid ST and solo weights genuinely differ, and not
  only because of target count — no raid buffs changes the marginal value of
  everything.
* **Detect cap effects.** Marginal value is measured at several deltas and the
  CURVE is reported, not just the slope. An overcapped stat is worth exactly
  zero and a weight that hides that is worse than no weight.
* **Delta sensitivity is a warning, not a number.** A weight that moves with
  the step size is not a measurement of anything.
* **Hit respects `rolls_hit_check`** and states which target level it applies
  to. Weighting hit against damage that never rolls a hit check is the exact
  error that once inflated a hit weight from 0.3 to 2.0.
"""
from dataclasses import replace

from .ability_model import resolve_ability
from .tiers import fast_sim

# Stats to differentiate, and how to apply a delta to CharState.
STAT_SETTERS = {
    "attack_power": lambda cs, d: _add(cs, "attack_power", d),
    "spell_power": lambda cs, d: _add(cs, "spell_power", d),
    "strength": lambda cs, d: _add(cs, "strength", d),
    "agility": lambda cs, d: _add(cs, "agility", d),
    "intellect": lambda cs, d: _add(cs, "intellect", d),
    "crit_rating": lambda cs, d: (_add(cs, "melee_crit_pct", d / 14.0),
                                  _add(cs, "spell_crit_pct", d / 14.0)),
    "hit_rating": lambda cs, d: (_add(cs, "melee_hit_pct", d / 10.0),
                                 _add(cs, "spell_hit_pct", d / 8.0)),
    "haste_rating": lambda cs, d: (_add(cs, "melee_haste_pct", d / 10.0),
                                   _add(cs, "spell_haste_pct", d / 10.0)),
    "expertise_rating": lambda cs, d: _add(cs, "expertise_points", d / 2.5),
    "armor_pen_rating": lambda cs, d: _add(cs, "armor_pen_pct", d / 4.2),
    "weapon_damage": lambda cs, d: _weapon(cs, d),
}


def _add(cs, attr, delta):
    setattr(cs, attr, getattr(cs, attr) + delta)


def _weapon(cs, delta):
    for hand in ("main_hand", "off_hand"):
        w = getattr(cs, hand)
        if w:
            setattr(cs, hand, {**w, "min": w["min"] + delta,
                               "max": w["max"] + delta})


def _clone(cs):
    from copy import deepcopy
    return deepcopy(cs)


def _dps(conn, build_spec, content, cs, apl):
    return fast_sim(conn, build_spec, content, cs, apl=apl).primary_value or 0.0


def stat_weights(conn, build_spec, content, char_state, apl=None, delta=100,
                 normalise_to="attack_power"):
    """Finite-difference stat weights for one content profile.

    Each stat is measured at `delta`, `2*delta` and `delta/2`. If the per-point
    value is not stable across those, a cap or a threshold is nearby and the
    row says so instead of reporting a slope that only holds at one step size.
    """
    warnings = []
    base = _dps(conn, build_spec, content, char_state, apl)
    if base <= 0:
        return {"weights": {}, "normalised_to": normalise_to, "base_dps": base,
                "warnings": ["base DPS is 0 — no weights are meaningful; the "
                             "build resolved no damage at all"]}

    raw = {}
    for name, setter in STAT_SETTERS.items():
        per_point = {}
        for step in (delta / 2.0, delta, delta * 2.0):
            cs = _clone(char_state)
            setter(cs, step)
            per_point[step] = (_dps(conn, build_spec, content, cs, apl) - base) / step
        vals = list(per_point.values())
        mid = per_point[delta]
        spread = (max(vals) - min(vals)) / abs(mid) if mid else 0.0
        note = ""
        if mid == 0:
            note = "zero marginal value — either capped or nothing uses it"
        elif spread > 0.15:
            note = (f"UNSTABLE across step size ({spread:.0%} spread over "
                    f"{delta/2:g}/{delta:g}/{delta*2:g}) — a cap or threshold "
                    "is near; read the curve, not this number")
        raw[name] = {"dps_per_point": mid, "curve": per_point, "note": note}

    # hit needs its own honesty pass, per PHASE_2 T7 and build doc §10's walkback
    gated, ungated = _hit_gated_share(conn, build_spec, content, char_state, apl)
    if raw.get("hit_rating"):
        total = gated + ungated
        share = gated / total if total else 0.0
        raw["hit_rating"]["note"] = (
            (raw["hit_rating"]["note"] + " | ") if raw["hit_rating"]["note"] else ""
        ) + (f"only {share:.0%} of modelled damage rolls a hit check, and this "
             f"weight applies ONLY vs a level-{content.target.level} target "
             f"(+{content.target.level - build_spec.character_level})")
        warnings.append(
            f"hit weight is scoped: {share:.0%} of this build's modelled damage "
            f"rolls a hit check at all, against a level-{content.target.level} "
            "target. Quoting it for other content is the error that once "
            "inflated a hit weight from 0.3 to 2.0 (build doc §10)")

    ref = raw.get(normalise_to, {}).get("dps_per_point") or 0.0
    weights = {}
    for name, row in sorted(raw.items(), key=lambda kv: -abs(kv[1]["dps_per_point"])):
        weights[name] = {
            "weight": (row["dps_per_point"] / ref) if ref else 0.0,
            "dps_per_point": row["dps_per_point"],
            "curve": row["curve"], "note": row["note"]}

    warnings.append(
        "weights are computed from fast_sim, which does not model resources — "
        "a stat that only matters when mana-starved will read as worthless")
    warnings.append(
        "talent multipliers are NOT modelled (2a limitation), so any stat whose "
        "value comes mostly through a talent is understated")
    return {"weights": weights, "normalised_to": normalise_to,
            "base_dps": base, "content": content.name, "delta": delta,
            "warnings": warnings}


def _hit_gated_share(conn, build_spec, content, char_state, apl):
    """(damage that rolls a hit check, damage that does not). The split the
    build doc's §10 walkback had to be done by hand."""
    gated = ungated = 0.0
    res = fast_sim(conn, build_spec, content, char_state, apl=apl)
    for sid, rec in res.per_ability.items():
        try:
            ab = resolve_ability(conn, sid, level=build_spec.character_level)
        except Exception:
            continue
        for ev in ab.events():
            hit = ab.expected_hit(char_state, content, event=ev)
            n, _ = ab.occurrences_per_cast(ev)
            share = hit.mean * (n or 0) * rec["casts"]
            if hit.breakdown.get("p_land", 1.0) >= 1.0:
                ungated += share
            else:
                gated += share
    return gated, ungated


def compare_paths(conn, build_spec, content, apl=None, paths=None):
    """Re-sim under each Path's bonuses. Direct answer to "which Path".

    ⚠ Only meaningful in COMPONENT mode. With `stats_override` the sheet values
    already contain the current path's effects, so swapping the path label
    changes the weapon clause and nothing else — the comparison would be
    mostly a no-op wearing a number. Said out loud rather than silently
    producing four near-identical rows.
    """
    from ..builds.stats import compute_stats
    from . import combat_engine as ce
    from ..builds.spec import PATHS

    warnings = []
    if build_spec.stats_override:
        warnings.append(
            "this build uses stats_override (sheet mode), so path STAT effects "
            "are already baked into the numbers and are NOT re-applied — only "
            "weapon-clause differences show here. For a real path comparison "
            "the build needs component-mode gear, which lands with Phase 3's "
            "items table")

    conv = ce.load_rating_conversions(conn, level=build_spec.character_level)
    out, current = {}, None
    for path in (paths or PATHS):
        spec = replace(build_spec, path=path)
        cs = compute_stats(spec, content, conv)
        dps = _dps(conn, spec, content, cs, apl)
        out[path] = {"dps": dps}
        if path == build_spec.path:
            current = dps
    for path, row in out.items():
        row["delta_pct"] = (100.0 * (row["dps"] / current - 1)) if current else 0.0
    return {"paths": out, "current": build_spec.path, "content": content.name,
            "warnings": warnings}
