#!/usr/bin/env python3
"""Phase 2 T9 (session 2c) — migrate pre-table predictions into the ledger.

    py ingest/export/seed_predictions.py

Same append-only discipline as `seed_confirmed.py` and `seed_epistemics.py`:
this file is the SOURCE OF TRUTH for predictions made before the `predictions`
table existed, so a rebuild reconstructs them.

🛑 **The stamps below are the ORIGINAL ones and must never be refreshed.**
`predictions/pred_2026-08-05_elric_paladin.md` was written under session 2b's
model, against the 2026-08-05 19-step rebuild, and predicted 586 / 602 / 602.
Session 2c then changed the model substantially — Holy Shock resolves, talents
are modelled, the same fixture now sims ~848. Re-deriving this row from the
current model would convert a fitted, post-hoc number into an apparently
pre-registered one, which destroys the only property the ledger has.

The outcome rows record what the 2026-08-04 parse actually showed, and are
deliberately separate from the prediction: a prediction is never edited by its
result.
"""
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import config  # noqa: E402
from config import DB_PATH  # noqa: E402

config.ensure_utf8_stdout()
from core.db.schema import create_phase1_schema  # noqa: E402
from core.sim.predictions import (  # noqa: E402
    PredictionLedgerError, record_outcome, record_prediction,
)

FIXTURE = config.REPO / "fixtures" / "build_elric_paladin.json"

# --- the 2b prediction, exactly as it was made --------------------------------
PRED_2B = {
    "slug": "pred_2026-08-05_elric_paladin_raid_boss_st",
    "character_name": "Elric",
    "user_id": "owner",
    "predicted_value": 602.0,          # medium_sim, the headline figure
    "predicted_low": 543.0,            # knowledge-uncertainty 90% CI
    "predicted_high": 589.0,
    "primary_metric": "DAMAGE_DONE",
    "sim_tier": "medium",
    "sim_version": "2b",
    "data_version": "ascension.db rebuilt 2026-08-05, 19 steps",
    "realm": "Darkmoon",
    "season": "S10",
    "created_at": "2026-08-05T00:00:00+00:00",
    "notes": (
        "Migrated from predictions/pred_2026-08-05_elric_paladin.md by "
        "seed_predictions.py (session 2c). ORIGINAL STAMPS PRESERVED — this row "
        "is NOT re-derived from the current model, which would make a post-hoc "
        "number look pre-registered. The prediction that mattered was that this "
        "is WRONG and by roughly 6x against the owner's reported ~3,600, with "
        "the causes named and ranked in the source file. fast 586 / medium 602 "
        "/ slow 602; combat-RNG 95% band 555-642."),
}

# The 2b file also carried a mythic_dungeon_st figure; logged as its own row
# because it is a different content profile and a different prediction.
PRED_2B_DUNGEON = dict(
    PRED_2B,
    slug="pred_2026-08-05_elric_paladin_mythic_dungeon_st",
    predicted_value=674.0, predicted_low=None, predicted_high=None,
    notes=("Migrated from pred_2026-08-05_elric_paladin.md (session 2c), "
           "ORIGINAL 2b STAMPS. fast 632 / medium 674 / slow 674. No "
           "knowledge-uncertainty band was computed for this profile."),
)

# --- the 2c prediction, logged BEFORE the next parse --------------------------
# Same discipline, and this one is genuinely pre-registered rather than migrated:
# it is recorded here before any parse taken after 2c's changes exists.
PRED_2C = {
    "slug": "pred_2026-08-05_2c_elric_paladin_raid_boss_st",
    "character_name": "Elric",
    "user_id": "owner",
    "predicted_value": 848.0,
    "predicted_low": 798.0,            # knowledge-uncertainty 90% CI
    "predicted_high": 863.0,
    "primary_metric": "DAMAGE_DONE",
    "sim_tier": "medium",
    "sim_version": "2c",
    "data_version": "ascension.db rebuilt 2026-08-05 with --with-dbc, 20 steps "
                    "(EffectSpellClassMask + rank-sibling sub-spell refs added)",
    "realm": "Darkmoon",
    "season": "S10",
    "created_at": "2026-08-05T23:00:00+00:00",
    "notes": (
        "602 -> 848 against 2b, from three changes: Holy Shock resolves (G4), "
        "talents contribute a x1.155 school multiplier (T4b), and the "
        "optimal-vs-observed APL comparison is unblocked. STILL LOW by ~4x "
        "against the owner's reported ~3,600, and the residual is NOT claimed "
        "to be talents: the per-ability gate shows logged/modelled at 1.86x for "
        "Holy and 1.34-1.38x for Holystrike, grouping by SCHOOL, which is what "
        "an unmodelled school amplifier OR an unmodelled buff looks like - and "
        "buff state is known to move 1.41x between the owner's own sessions. "
        "The falsifiable part: if the next parse's per-ability residual is "
        "again school-grouped and again near 1.86 / 1.37, the missing factor is "
        "structural rather than session buff state."),
}

CONTENT = {
    "pred_2026-08-05_elric_paladin_raid_boss_st": {
        "name": "raid_boss_st", "targets": 1, "target_level_delta": 3,
        "fight_duration": 75.0},
    "pred_2026-08-05_elric_paladin_mythic_dungeon_st": {
        "name": "mythic_dungeon_st", "targets": 1, "target_level_delta": 2,
        "fight_duration": 60.0},
    "pred_2026-08-05_2c_elric_paladin_raid_boss_st": {
        "name": "raid_boss_st", "targets": 1, "target_level_delta": 3,
        "fight_duration": 75.0},
}

# --- what actually happened ---------------------------------------------------
# ⚠ The owner's ~3,600 is a REPORTED figure, not a parsed one, so it is recorded
# with its provenance rather than presented as a measurement. The per-ability
# numbers below are parsed and exact.
OUTCOMES = [
    {
        "prediction_slug": "pred_2026-08-05_elric_paladin_raid_boss_st",
        "actual_value": 3600.0,
        "source": "owner-reported DPS, 2026-08-05 (NOT a parsed total)",
        "notes": (
            "Reported by the owner, not computed from a log — recorded so the "
            "6x gap is in the ledger, but it is tier-1 hearsay rather than a "
            "measurement and should be replaced by a parsed total when one "
            "exists. The parsed evidence for the same period is per-ability "
            "and is in the per-ability comparison instead."),
    },
]


def main():
    conn = sqlite3.connect(str(DB_PATH))
    create_phase1_schema(conn)
    spec = json.loads(FIXTURE.read_text(encoding="utf-8"))

    made = skipped = 0
    for pred in (PRED_2B, PRED_2B_DUNGEON, PRED_2C):
        try:
            record_prediction(conn, build_spec=spec,
                              content_profile=CONTENT[pred["slug"]], **pred)
            made += 1
        except PredictionLedgerError:
            # Already present: correct behaviour on a re-run. The ledger
            # refuses to rewrite a prediction, which is what makes it a ledger.
            skipped += 1

    outcomes = 0
    for oc in OUTCOMES:
        already = conn.execute(
            "SELECT 1 FROM prediction_outcomes WHERE prediction_slug = ? "
            "AND source = ?", (oc["prediction_slug"], oc["source"])).fetchone()
        if already:
            continue
        record_outcome(conn, **oc)
        outcomes += 1

    conn.commit()
    n = conn.execute("SELECT COUNT(*) FROM predictions").fetchone()[0]
    m = conn.execute("SELECT COUNT(*) FROM prediction_outcomes").fetchone()[0]
    print(f"predictions: {n} rows ({made} inserted, {skipped} already present "
          f"and NOT rewritten)")
    print(f"prediction_outcomes: {m} rows ({outcomes} inserted)")
    for slug, sv, dv, pv in conn.execute(
            "SELECT slug, sim_version, data_version, predicted_value "
            "FROM predictions ORDER BY created_at"):
        print(f"  {slug:52} {sv:>4}  {pv:>8,.0f}  [{dv}]")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
