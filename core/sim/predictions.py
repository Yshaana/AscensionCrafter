"""Phase 2 T9 — the prediction ledger.

The owner generates parses constantly on a character whose build is known
exactly, which makes his own logs the best calibration source available: no
snapshot lag, known content, and it accumulates for free with no test design.
This module records what the model predicted, and later what actually happened.

## The one property that matters

**A prediction is logged BEFORE the parse that tests it, and keeps the stamps it
was made under.** Everything else here is bookkeeping around that.

`sim_version` and `data_version` are what let an old miss be re-checked against
today's model to ask whether a fix actually fixed it. Re-deriving a stored
prediction from the current model would quietly convert a fitted, post-hoc
number into an apparently pre-registered one — destroying the exact property the
ledger exists to create. So `record_prediction` REFUSES to overwrite an existing
slug: a changed prediction is a NEW row, and the old one stays.
"""
import hashlib
import json
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone


class PredictionLedgerError(Exception):
    pass


def _json(obj):
    if is_dataclass(obj):
        obj = asdict(obj)
    return json.dumps(obj, default=str, sort_keys=True)


def build_spec_hash(build_spec):
    """Stable hash of a build, so two predictions about the same board match."""
    return hashlib.sha256(_json(build_spec).encode("utf-8")).hexdigest()[:16]


def record_prediction(conn, *, slug, build_spec, content_profile,
                      predicted_value, primary_metric, sim_version,
                      data_version, predicted_low=None, predicted_high=None,
                      per_ability=None, sim_tier=None, patch_id=None,
                      realm="Darkmoon", season="S10", user_id=None,
                      character_name=None, notes=None, created_at=None):
    """Insert one prediction. Refuses to overwrite an existing slug.

    `created_at` is settable ONLY so a prediction made before this table existed
    can be migrated with its original date — never to backdate a new one.
    """
    existing = conn.execute(
        "SELECT sim_version, created_at FROM predictions WHERE slug = ?",
        (slug,)).fetchone()
    if existing:
        raise PredictionLedgerError(
            f"prediction {slug!r} already exists (sim_version {existing[0]}, "
            f"made {existing[1]}). A prediction is never rewritten — log a new "
            "slug. Overwriting one would erase the record of what was believed "
            "before the parse, which is the only thing this table is for")
    spec_json = _json(build_spec)
    conn.execute(
        "INSERT INTO predictions (slug, user_id, character_name, "
        "build_spec_json, build_spec_hash, content_profile_json, "
        "predicted_value, predicted_low, predicted_high, primary_metric, "
        "per_ability_json, sim_tier, sim_version, data_version, patch_id, "
        "realm, season, notes, created_at) "
        "VALUES (" + ",".join("?" * 19) + ")",
        (slug, user_id, character_name, spec_json,
         hashlib.sha256(spec_json.encode("utf-8")).hexdigest()[:16],
         _json(content_profile), float(predicted_value),
         predicted_low, predicted_high, primary_metric,
         _json(per_ability) if per_ability is not None else None,
         sim_tier, sim_version, data_version, patch_id, realm, season, notes,
         created_at or datetime.now(timezone.utc).isoformat(timespec="seconds")))
    return slug


def record_outcome(conn, *, prediction_slug, actual_value, source=None,
                   encounter_id=None, actual_per_ability=None, notes=None):
    """Record what actually happened. A prediction may have several outcomes —
    the same build parsed twice is two data points, not a correction."""
    row = conn.execute(
        "SELECT predicted_value, predicted_low, predicted_high FROM predictions "
        "WHERE slug = ?", (prediction_slug,)).fetchone()
    if row is None:
        raise PredictionLedgerError(
            f"no prediction {prediction_slug!r} — an outcome cannot be recorded "
            "for a prediction that was never made, which is the whole point")
    predicted, low, high = row
    delta_pct = 100.0 * (actual_value / predicted - 1.0) if predicted else None
    within = None
    if low is not None and high is not None:
        within = 1 if low <= actual_value <= high else 0
    conn.execute(
        "INSERT INTO prediction_outcomes (prediction_slug, encounter_id, "
        "source, actual_value, actual_per_ability_json, delta_pct, "
        "within_predicted_range, notes, recorded_at) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        (prediction_slug, encounter_id, source, float(actual_value),
         _json(actual_per_ability) if actual_per_ability is not None else None,
         delta_pct, within, notes,
         datetime.now(timezone.utc).isoformat(timespec="seconds")))
    return delta_pct


def reconcile(conn, user_id=None, character_name=None):
    """Match outcomes against predictions and report SYSTEMATIC bias.

    Aggregate error is the least useful thing here. What earns its keep is bias
    that reproduces per ability or per mechanism, because that names the thing to
    fix — every retraction in this project has worked that way.
    """
    where, params = [], []
    if user_id:
        where.append("p.user_id = ?")
        params.append(user_id)
    if character_name:
        where.append("p.character_name = ?")
        params.append(character_name)
    clause = ("WHERE " + " AND ".join(where)) if where else ""
    rows = conn.execute(
        f"""SELECT p.slug, p.sim_version, p.data_version, p.predicted_value,
                   p.per_ability_json, o.actual_value, o.actual_per_ability_json,
                   o.delta_pct, o.within_predicted_range, o.source
            FROM predictions p JOIN prediction_outcomes o
              ON o.prediction_slug = p.slug {clause}
            ORDER BY p.created_at""", params).fetchall()

    per_ability_bias, entries = {}, []
    for (slug, simv, datav, pred, pred_ab, actual, act_ab, delta, within,
         source) in rows:
        entries.append({
            "slug": slug, "sim_version": simv, "data_version": datav,
            "predicted": pred, "actual": actual, "delta_pct": delta,
            "within_range": within, "source": source,
        })
        if not (pred_ab and act_ab):
            continue
        pa, aa = json.loads(pred_ab), json.loads(act_ab)
        for name, p in pa.items():
            a = aa.get(name)
            if a is None or not p:
                continue
            per_ability_bias.setdefault(name, []).append(100.0 * (a / p - 1.0))

    systematic = []
    for name, deltas in sorted(per_ability_bias.items()):
        if len(deltas) < 2:
            continue
        mean = sum(deltas) / len(deltas)
        # A bias is SYSTEMATIC when every sample points the same way. One-sided
        # agreement across independent parses is the signal; a large mean with
        # mixed signs is variance, and treating it as bias would chase noise.
        one_sided = all(d > 0 for d in deltas) or all(d < 0 for d in deltas)
        if one_sided and abs(mean) >= 10.0:
            systematic.append({
                "ability": name, "n": len(deltas), "mean_delta_pct": mean,
                "deltas": deltas,
                "suggests_open_question": (
                    f"{name} is modelled "
                    f"{'too low' if mean > 0 else 'too high'} by "
                    f"{abs(mean):.0f}% in every one of {len(deltas)} parses — "
                    "a reproducing one-sided bias is a mis-modelled mechanic, "
                    "not variance"),
            })
    return {"entries": entries, "systematic_bias": systematic,
            "n_predictions": len({e["slug"] for e in entries}),
            "n_outcomes": len(entries)}
