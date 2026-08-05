"""Phase 2 T6 — knowledge-uncertainty propagation.

**The change that makes sim output honest**: instead of one confident number,
report how much the answer moves because we do not know the inputs, and say
which unknowns drive the spread.

🛑 **This is not combat variance.** `slow_sim` answers "this build rolls between
3,900 and 4,500 on any given pull". This module answers "we don't know this
coefficient, so the true mean is somewhere in 3,800-4,600". They are different
quantities and are NEVER merged into one error bar — merging them hides the one
you can actually do something about (PHASE_2 T6).

## Where the ranges come from, and why not from `uncertainty_json`

PHASE_2 T6 specifies sampling each mechanic from its `spell_mechanics.
uncertainty_json` range. Session 2b checked what is actually in that column
across all 3,747 rows and it cannot serve:

* `damage_formula_terms_json` — the field that drives DPS — is stored with
  `low: None, high: None, basis: 'non-numeric'`;
* every numeric field carries a `default_confidence_mapping(confirmed, ±0%)`
  band, explicitly labelled "heuristic, not measured".

Sampling that would report ±0% knowledge uncertainty, which is worse than
reporting none at all because it looks authoritative. **Owner decision
2026-08-05: build the ranges here, in the sim layer, as a documented policy
table, and leave Phase 1's truth table untouched** — writing invented ranges
into `spell_mechanics` would put fabricated precision behind tier provenance,
which is the exact failure `EffectBonusCoefficient` already caused once.

The policy below is a **stated assumption, not a measurement**. It is written
down in one place so it can be argued with, and every band names its reason.
"""
import random
from dataclasses import dataclass

from .ability_model import resolve_ability
from .tiers import fast_sim


@dataclass
class Band:
    """A multiplicative uncertainty band on one input, with its reason."""
    low: float
    high: float
    reason: str


# --- the policy table ---------------------------------------------------------
# Keyed by the evidence a term carries. Bands are multiplicative on the term's
# value. Ordering matters: the FIRST matching rule wins, most specific first.
#
# The numbers are judgements, deliberately round, and chosen to be wide enough
# that resolving a question visibly narrows the answer. They are not derived
# from a distribution — there is no distribution to derive them from, which is
# the honest reason to keep them here rather than in the database.

POLICY = [
    ("excluded_outlier", Band(0.0, 0.0,
        "coefficient exceeded the outlier cap and was excluded entirely — it "
        "contributes nothing and no band can make it contribute")),
    ("trigger_attributed", Band(0.85, 1.15,
        "magnitude reached by the bounded trigger walk (confidence=inferred): "
        "the chain is single-path and cycle-safe, but the attribution itself "
        "has never been confirmed against a parse")),
    ("db_ascension_gg", Band(0.95, 1.05,
        "tier-3 third-party render; agreed exactly with the client on Holy "
        "Supernova, so tight — but it is still not the server")),
    ("dbc_rank_sibling_text", Band(0.90, 1.10,
        "coefficient read from the rank-correct sibling's tooltip text: right "
        "rank, but still tier-6 text")),
    ("export_tooltip", Band(0.75, 1.25,
        "tier-6 export tooltip. Widest band of the text sources for two "
        "measured reasons: the export omits whole clauses, and coefficients "
        "ramp with rank on 169 of 1,580 multi-rank lines while the catalog "
        "stores Rank 1, the deepest point of the ramp")),
    ("dbc_hidden_formula", Band(0.70, 1.30,
        "regex-extracted from a sub-spell's description text; the open "
        "question hidden_formula_outlier_coefficients shows this source has "
        "swallowed DoT-total multipliers before")),
    ("dbc_numeric_field", Band(0.98, 1.02,
        "tier-4 client numeric field, validated against 7 independently known "
        "magnitudes every rebuild — near-certain, but level scaling and rank "
        "selection still sit on top of it")),
]

# Non-term inputs the engine itself flags as unvalidated on Ascension. These
# move the whole result, not one ability, and each names its open question.
ENGINE_BANDS = {
    "pulse_count": Band(0.5, 1.0,
        "periodic-trigger pulse count rides on the DBC duration and is not "
        "calibrated (open question periodic_trigger_delivery_pulse_count). "
        "Asymmetric DOWNWARD: if the duration is shorter than the client says, "
        "the count falls; it cannot exceed the client value"),
    "glancing_and_crit_suppression": Band(0.92, 1.0,
        "glancing chance/penalty are retail_hypothesis values and melee crit "
        "suppression vs higher-level targets is warned-not-modelled (open "
        "question melee_crit_suppression_vs_higher_level) — both would only "
        "REDUCE output, hence the one-sided band"),
    "partial_resist_curve": Band(0.95, 1.0,
        "the partial-resist curve is retail_hypothesis; Ascension confirms "
        "partials exist on Holy but the curve is unvalidated"),
}


def band_for(component):
    """The band that applies to one resolved damage component."""
    if component.get("kind") == "excluded_outlier":
        return POLICY[0][1]
    if str(component.get("via", "")).startswith("trigger_hop"):
        return dict(POLICY)["trigger_attributed"]
    src = component.get("source")
    for key, band in POLICY:
        if key == src:
            return band
    if component.get("kind") == "flat":
        return dict(POLICY)["dbc_numeric_field"]
    return dict(POLICY)["export_tooltip"]


def _uncertain_inputs(conn, build_spec, content, char_state, apl):
    """Every uncertain input this build's damage actually depends on, with its
    band. Returns [{'parameter', 'band', 'scope'}]."""
    out = []
    ids = apl.spell_ids() if apl else [c.spell_id for c in build_spec.abilities]
    seen = set()
    for sid in ids:
        try:
            ab = resolve_ability(conn, sid, level=build_spec.character_level)
        except Exception:
            continue
        for ev in ab.events():
            res = ab.expected_hit(char_state, content, event=ev)
            for c in res.components:
                b = band_for(c)
                if b.low == b.high:
                    continue
                label = (f"{ab.name}: {c.get('term') or c.get('kind')} "
                         f"({c.get('source') or c.get('via') or 'numeric'})")
                if label in seen:
                    continue
                seen.add(label)
                out.append({"parameter": label, "band": b, "scope": "component",
                            "spell_id": ab.spell_id, "event": ev.key})
            n, _ = ab.occurrences_per_cast(ev)
            if (ev.delivery or {}).get("periodic") and n:
                label = f"{ab.name}: pulse count ({n} per cast)"
                if label not in seen:
                    seen.add(label)
                    out.append({"parameter": label,
                                "band": ENGINE_BANDS["pulse_count"],
                                "scope": "occurrences", "spell_id": ab.spell_id,
                                "event": ev.key})
    for key in ("glancing_and_crit_suppression", "partial_resist_curve"):
        out.append({"parameter": f"engine: {key}", "band": ENGINE_BANDS[key],
                    "scope": "global", "spell_id": None, "event": None})
    return out


def _sample_dps(conn, build_spec, content, char_state, apl, factors):
    """Run fast_sim with a multiplicative factor applied per ability.

    Component-level factors are collapsed to an ability-level factor: the sim's
    closed form is linear in each component, so scaling the components of one
    ability by their sampled factors and scaling that ability's damage by the
    mean of those factors agree to first order. Stated because it IS an
    approximation — the alternative is re-resolving every ability per sample,
    which would make 500 samples cost what 500 medium sims cost.
    """
    res = fast_sim(conn, build_spec, content, char_state, apl=apl)
    total = 0.0
    for sid, rec in res.per_ability.items():
        total += rec["damage"] * factors.get(sid, 1.0)
    return total / content.fight_duration if content.fight_duration else 0.0


def sim_with_uncertainty(conn, build_spec, content, char_state, apl=None,
                         samples=300, seed=None):
    """Monte Carlo over INPUT uncertainty (never combat RNG).

    Cheap because fast_sim is milliseconds: each sample draws every uncertain
    input from its band and re-evaluates.
    """
    rng = random.Random(seed)
    inputs = _uncertain_inputs(conn, build_spec, content, char_state, apl)
    nominal = _sample_dps(conn, build_spec, content, char_state, apl, {})

    draws = []
    for _ in range(samples):
        per_ability = {}
        global_factor = 1.0
        for item in inputs:
            b = item["band"]
            f = rng.uniform(b.low, b.high)
            if item["scope"] == "global":
                global_factor *= f
            else:
                sid = item["spell_id"]
                acc = per_ability.setdefault(sid, [])
                acc.append(f)
        factors = {sid: (sum(v) / len(v)) * global_factor
                   for sid, v in per_ability.items()}
        draws.append(_sample_dps(conn, build_spec, content, char_state, apl,
                                 factors))

    draws.sort()
    n = len(draws) or 1
    return {
        "nominal": nominal, "samples": samples,
        "low": draws[0] if draws else nominal,
        "high": draws[-1] if draws else nominal,
        "ci_low": draws[int(0.05 * n)] if draws else nominal,
        "ci_high": draws[min(n - 1, int(0.95 * n))] if draws else nominal,
        "spread_pct": (100.0 * (draws[-1] - draws[0]) / (2 * nominal)
                       if draws and nominal else 0.0),
        "inputs": len(inputs),
        "policy_note": (
            "bands come from core/sim/uncertainty.py's POLICY table — a stated "
            "assumption, not a measurement; spell_mechanics.uncertainty_json "
            "cannot serve this (2b finding)"),
    }


def sensitivity(conn, build_spec, content, char_state, apl=None, samples=200,
                seed=None):
    """How much would the DPS range narrow if each unknown were resolved?

    **This is the verification queue.** Sorted descending, it says what to
    measure next — and its output is what should populate
    `open_questions.variance_contribution`.
    """
    inputs = _uncertain_inputs(conn, build_spec, content, char_state, apl)
    base = sim_with_uncertainty(conn, build_spec, content, char_state, apl,
                                samples=samples, seed=seed)
    # Spread is measured as the 5-95 CI width, NOT max-min. The full range is a
    # two-sample statistic and at a few hundred samples it is dominated by which
    # extreme draws happened to occur, which made almost every input report a
    # 0.0% contribution — noise swamping the signal it was supposed to rank.
    base_spread = base["ci_high"] - base["ci_low"]
    if base_spread <= 0:
        return []

    rows = []
    for i, item in enumerate(inputs):
        # resolve THIS input (collapse its band to nominal), leave the rest
        rng = random.Random(seed)
        draws = []
        for _ in range(samples):
            per_ability, global_factor = {}, 1.0
            for j, other in enumerate(inputs):
                b = other["band"]
                f = 1.0 if j == i else rng.uniform(b.low, b.high)
                if other["scope"] == "global":
                    global_factor *= f
                else:
                    per_ability.setdefault(other["spell_id"], []).append(f)
            factors = {sid: (sum(v) / len(v)) * global_factor
                       for sid, v in per_ability.items()}
            draws.append(_sample_dps(conn, build_spec, content, char_state,
                                     apl, factors))
        draws.sort()
        m = len(draws) or 1
        narrowed = (draws[min(m - 1, int(0.95 * m))] - draws[int(0.05 * m)])
        contribution = max(0.0, 100.0 * (base_spread - narrowed) / base_spread)
        rows.append({
            "parameter": item["parameter"],
            "variance_contribution_pct": contribution,
            "band": (item["band"].low, item["band"].high),
            "note": item["band"].reason[:90],
        })
    rows.sort(key=lambda r: -r["variance_contribution_pct"])
    return rows
