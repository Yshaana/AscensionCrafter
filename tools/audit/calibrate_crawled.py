"""
calibrate_crawled.py — the ≥3-real-characters calibration gate (Phase 3 exit).

    py tools/audit/calibrate_crawled.py [--max-lag-hours 0] [--read-holdout]

PHASE_2 §8.2 moved this criterion to 3a because simulating a crawled character
needs gear, and gear is Phase 3 T4's `items` table. That dependency is now
satisfied: `snapshot_gear` carries resolved per-slot stat blocks, so a crawled
character can be built as a real `BuildSpec` and simmed in COMPONENT mode
(gear + path + talents), with no invented stats.

Tolerance is `predictions/CALIBRATION_TOLERANCE.md`'s, unchanged and not
re-derived here: **±20% aggregate DPS**.

🛑 Three honesty rules this tool enforces structurally, because each is a way
the gate could be passed without meaning anything:

1. **Candidates are chosen before results are seen.** Selection is by data
   completeness only — gear stats resolved, cards resolved, an exact (lag-0)
   build-to-parse join, a boss encounter with a real duration. It never ranks
   by how well the sim did.

   🆕 **3e A1 — and the population is FROZEN, as committed data.** The cohort is
   the id set in `predictions/cohort_frozen_3e.json`, not the top N by id.
   `3d` proved `ORDER BY character_id LIMIT N` is a sliding window rather than a
   cost cap: when the crawler grew the qualifying population 157 → 180, the gate
   read 5-of-41 → 4-of-38 with **zero code changes**. A frozen member that stops
   qualifying is reported as **dropped, with its reason**, never substituted and
   never silently omitted; characters that qualify but are not in the set are
   counted and named as unscored. Two runs are comparable only because of this.
2. **Build-to-parse staleness is an explicit, reported parameter.**
   `--max-lag-hours` defaults to **0** (the snapshot was captured AT that
   encounter, so it IS the build that produced the parse). Any looser value is
   printed in the header and the per-character lag is in the table, because a
   lagged snapshot is a different build wearing the same name.

   ⚠ **Corpus-size caveat, learned the hard way on 2026-08-06.** Against a
   mid-backfill corpus this filter left exactly ONE level-60 character, and
   that looked like a structural property of the data ("exact-join captures
   skew toward levelling players"). It was not — it was small-sample. After the
   backfill completed the same strict filter yields **41**. The lesson is
   general enough to keep: *a filter that starves on a partial corpus is not
   evidence that the filter is too strict.* Prefer re-running on more data over
   loosening a constraint.
3. **A character on an impaired system is reported, never silently included.**
   Path of Duality's parses are excluded from absolute calibration by the 2d
   advisory; they are counted and named, not dropped quietly.
4. **Buffs are DERIVED, never fitted** (3b pre-flight §0.3). A measured buff
   applies only when a participant in the same capture scope holds the
   granting card on a linked board (`core/builds/group_buffs.py`); every
   character is also simmed unbuffed so the layer's contribution is visible.
   The derivation is an explicit lower bound — unlinked boards and unmeasured
   buffs contribute nothing, and a remaining miss is information about the
   next missing mechanism, not a licence to scale this one.

The output is a per-mechanism report, per the tolerance file's own rule that a
pass/fail number alone is worth very little.
"""
import argparse
import json
import sqlite3
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import config  # noqa: E402
import season_config  # noqa: E402  - realm/season constants (3d A1)
from config import BUILDS_DB_PATH, DATA_DERIVED, DB_PATH  # noqa: E402
from core.builds.gear import (  # noqa: E402
    gear_coverage, missing_stat_budget_bound, normalise_stats,
    slot_budget_medians)
from core.builds.group_buffs import derive_buffs  # noqa: E402
from core.builds.spec import BuildSpec, GearItem, SlottedCard  # noqa: E402
from core.builds.stats import compute_stats  # noqa: E402
from core.db.connection import connect  # noqa: E402
from core.sim import combat_engine as ce  # noqa: E402
from core.sim.apl_gen import generate_apl  # noqa: E402
from core.sim.content import Role, get_preset  # noqa: E402
from core.sim.tiers import fast_sim  # noqa: E402

config.ensure_utf8_stdout()

AGGREGATE_TOLERANCE_PCT = 20.0     # predictions/CALIBRATION_TOLERANCE.md
MIN_WITHIN_TOLERANCE = 3           # the ±20% criterion, UNCHANGED (PHASE_2 §8.2)

# Phase 3 EXIT rider, stamped 2026-08-06 BEFORE the scraped-coefficient ingest
# was re-run through this gate (CALIBRATION_TOLERANCE.md addendum). It does not
# touch the ±20% pass definition; it adds a second condition on the exit.
#
# Why: of the 4 characters inside ±20%, only 1 also had ≥50% of its damage
# modelled. The other 3 agree on the TOTAL while the sim reproduces 5-13% of the
# kit — compensating error, which an aggregate criterion is structurally blind
# to. Set while coverage was a median 37% and the post-ingest number was still
# unknown, so it is a stricter bar that cannot have been fitted to a result.
QUALIFIED_COVERAGE_PCT = 50.0
MIN_QUALIFIED = 3
REPORT_PATH = DATA_DERIVED / "calibration_crawled.md"

# 3e A2/A3 — SLICE ACCURACY IS A RATIO WITH COVERAGE IN ITS DENOMINATOR, so it
# explodes as coverage -> 0 and must never be aggregated across a cohort spanning
# 0.2% to 82% coverage. The cohort median is therefore reported ONLY above a
# stated floor, with the floor printed beside it and the per-band table under it.
#
# Measured from the committed 3d manifest: the all-characters median is 159.8%,
# which reads as "the sim over-produces the slice it models by 60%". That is
# BACKWARDS and it is a low-coverage artifact — Mutaforma at 0.2% coverage
# reports 1,859,400%. Restricted to coverage >= 20% the median is 62.6% and does
# not move again at >= 30% or >= 50%. **The sim UNDER-produces on what it models,
# by ~37%.** (predictions/CALIBRATION_TOLERANCE.md; ADDENDUM_3D_slice_accuracy_correction.md)
SLICE_COVERAGE_FLOOR_PCT = 20.0
SLICE_BANDS = (0.0, 10.0, 20.0, 30.0, 50.0)

# 3e A3 — OWNER DECISION 2026-08-06, taken after seeing the coverage distribution
# of the passers and stamped BEFORE this gate run.
#
# THIS run: `within_tolerance` keeps NO coverage floor, so the criterion's
# definition is unchanged and 3e's before/after pairs stay comparable to every
# earlier run. The only change is honesty at the boundary — a character the sim
# models NOTHING for reports None, not False (see `within_tolerance` below).
#
# NEXT gate: a 20% coverage floor applies to `within_tolerance` itself.
# Justification, recorded now rather than after the fact: slice accuracy is
# stable at 62.6% across the >=20 / >=30 / >=50 bands and unstable below 20%, so
# 20% is where the metric stops being noise — a property of the measurement, not
# a level chosen to admit a wanted number. At today's numbers it would take the
# gate from 5 passing to 2, i.e. it is a STRICTER bar stamped while its own
# result is known to fail. That is the direction a criterion is allowed to move.
SUCCESSOR_COVERAGE_FLOOR_PCT = 20.0
SUCCESSOR_FLOOR_EFFECTIVE_FROM = "the gate run AFTER 3e (stamped 2026-08-06)"

# ✅ 3g G4 — THAT GATE IS THIS ONE. The floor is APPLIED, in its own commit with
# its own before/after pair, per owner decision 2026-08-07 (SESSION_3G_PRIMER
# §0.8.2). It is NOT re-tuned here: 20.0 is the value stamped on 2026-08-06 and
# changing it after seeing G1's result would be moving a gate after seeing its
# number, in either direction.
SUCCESSOR_FLOOR_APPLIED_FROM = "3g (2026-08-07)"

# 🛑 THE ATTRIBUTION, settled from git rather than from memory (3g G4; the
# AUDIT_3E §6 / AUDIT_3F question, raised because the floor is credited to the
# owner three times in 3e's record while being numerically identical to a
# constant Code chose and justified in its own voice).
#
# `git log -S` puts BOTH constants in ONE commit, 68779e7 ("3e Block A"):
# `SLICE_COVERAGE_FLOOR_PCT = 20.0` at +119 and `SUCCESSOR_COVERAGE_FLOOR_PCT =
# 20.0` at +137. So:
#
#   * The OWNER decided the POLICY — that a coverage floor should apply to
#     `within_tolerance`, that it takes effect at the NEXT gate and not the one
#     being run, and that 3e's before/after pairs therefore stay comparable.
#     That is a decision only the owner can take, and it is his.
#   * CODE chose the VALUE, in A2 of the same commit, from the band table:
#     slice accuracy is flat across >=20/>=30/>=50 and unstable below, so 20 is
#     where the metric stops being noise. It was chosen for slice REPORTING
#     first and reused for the criterion second.
#
# Neither claim was ever false; a reader could reasonably take "owner decision"
# to cover the number as well, which is what the auditor flagged. ✅ And the
# property that matters survives either reading: the value was fixed BEFORE it
# was applied to a criterion, it is strictly HARSHER (2 of 36 against 5 on the
# run that stamped it), and it was not chosen to admit a wanted result.

# 3e A4 — the pre-registered validation subset (seed_predictions.py's
# `holdout_3e_crawled_gate_validation_set`). Registered in `3d`, but
# `calibrate_crawled.py` had never heard of it, so all five were counted in
# "n of 41" — meaning any fix that lifted them moved the headline AND spent the
# holdout in the same number. The headline is now the TUNING SET only; the
# holdout is withheld from stdout and REDACTED in the manifest unless
# --read-holdout is passed, which is a Block D close-out action.
HOLDOUT_SLUG = "holdout_3e_crawled_gate_validation_set"
HOLDOUT_IDS = (460, 461, 462, 463, 7661)

# 3e A1 — THE COHORT IS FROZEN, AND IT IS DATA RATHER THAN A CONSTANT IN HERE.
# Read from a committed file so an auditor can see the population without
# reading the tool, and so the tool cannot quietly redefine it.
#
# 🛑 The file this READS and the file this WRITES are deliberately different.
# If the gate read and wrote one manifest, a member that stopped qualifying
# would vanish from the next write and the frozen set would shrink silently —
# the same defect the freeze exists to remove, wearing a different coat.
COHORT_PATH = config.REPO / "predictions" / "cohort_frozen_3e.json"

# 3d E2 — COMMITTED, unlike everything else this tool writes. Counts, ids and
# hashes only; no bulk data, so `.gitignore:10` stays exactly as it is. It lives
# under predictions/ because it is a record of what was measured, alongside the
# markdown ledgers, not a rebuildable derived artifact.
# ⚠ 3e A1: the NAME changed. `gate_manifest.json` is the immutable record of the
# `3d` run the cohort was frozen from and is never written again.
GATE_MANIFEST_PATH = config.REPO / "predictions" / "gate_manifest_3e.json"

PATH_TOKEN = {"strength": "Strength", "agility": "Agility", "duality": "Duality",
              "intellect": "Intelligence", "intelligence": "Intelligence",
              "spirit": "Healing", "healing": "Healing"}

# Slot index -> BuildSpec slot name. Only the two the sim reads by name matter;
# everything else contributes stats under its numeric slot.
WEAPON_SLOTS = {16: "main_hand", 17: "off_hand"}


# 🛑 3d F1 — snapshot sources that may NEVER enter the gate cohort.
#
# The gate measures whether the sim reproduces characters whose inputs it had to
# INFER from a public crawl. A character whose stat block, board and weapon we
# captured ourselves — Elric, from his own ALC export — is a different kind of
# object: an INSTRUMENT with privileged inputs, useful precisely because its
# error is not input error. Scoring it alongside 41 crawled strangers would
# inflate the gate with the one case that was never in question.
#
# "He is an instrument, not a count" existed only in prose. `candidates()`
# filters on level, gear, cards and lag with NO source filter, so the moment
# Elric gets a `character_snapshots` row he becomes a candidate automatically and
# the cohort silently becomes 42 — with the privileged-input character inside it.
#
# ⚠ APPLIED IN SQL, BEFORE THE LIMIT, not as a post-hoc drop. `candidates()` is
# `ORDER BY character_id LIMIT N`, so a filtered-out character that is still
# SELECTed would consume a slot and push a real one out of the window — turning
# an exclusion into a silent cohort change. Filtering in the WHERE clause means
# an excluded character is invisible to the window entirely.
EXCLUDED_SNAPSHOT_SOURCES = ("own_capture",)


def load_frozen_cohort(path=COHORT_PATH):
    """The gate's population, as committed data rather than a tool constant."""
    if not path.exists():
        raise SystemExit(
            f"{path} missing — the gate cohort is FROZEN data (3e A1) and the "
            f"tool will not invent one. Restore it from git.")
    spec = json.loads(path.read_text(encoding="utf-8"))
    ids = [int(i) for i in spec["character_ids"]]
    if len(set(ids)) != len(ids):
        raise SystemExit(f"{path}: duplicate character_ids in the frozen cohort")
    return ids, spec


def _completeness_sql(max_lag_hours, extra_where, params):
    excl = ",".join("?" * len(EXCLUDED_SNAPSHOT_SOURCES))
    return (f"""
        SELECT ep.character_id, c.name, ep.snapshot_id, ep.dps, ep.path,
               e.boss_name, e.content_type, e.duration_seconds, e.encounter_id,
               ep.snapshot_lag_hours, c.level, ep.scope_id,
               MAX(e.duration_seconds) AS _longest
        FROM encounter_performance ep
        JOIN capture_scopes cs ON cs.scope_id = ep.scope_id
        JOIN encounters e ON e.encounter_id = cs.encounter_id
        JOIN characters c ON c.character_id = ep.character_id
        WHERE ep.snapshot_lag_hours IS NOT NULL
          AND ep.snapshot_lag_hours <= ?           -- rule 2, parameterised
          AND ep.dps IS NOT NULL AND ep.dps > 100
          AND e.is_trash = 0 AND e.duration_seconds >= 20
          AND c.level = 60                          -- level-60 model only
          -- 3d F1: privileged-input characters are INSTRUMENTS, not cohort
          -- members. Filtered in the WHERE clause, never as a post-hoc drop.
          -- See EXCLUDED_SNAPSHOT_SOURCES.
          AND NOT EXISTS (SELECT 1 FROM character_snapshots s
                           WHERE s.snapshot_id = ep.snapshot_id
                             AND s.source IN ({excl}))
          AND EXISTS (SELECT 1 FROM snapshot_gear sg
                       WHERE sg.snapshot_id = ep.snapshot_id
                         AND sg.stats_json IS NOT NULL)
          AND EXISTS (SELECT 1 FROM snapshot_cards sc
                       WHERE sc.snapshot_id = ep.snapshot_id
                         AND sc.spell_id IS NOT NULL)
          {extra_where}
        GROUP BY ep.character_id
        ORDER BY ep.character_id""",
            (max_lag_hours, *EXCLUDED_SNAPSHOT_SOURCES, *params))


def candidates(conn, cohort_ids, max_lag_hours=0.0):
    """Selection is by DATA COMPLETENESS ONLY — never by sim agreement.

    ONE row per character (the longest qualifying encounter), chosen in SQL so
    the cohort spans distinct characters. Taking a limit first and deduping
    after let two chatty characters consume all 40 rows and reduced the gate to
    n=1.

    Level 60 is required, not assumed: every coefficient, rating divisor and
    rank resolution in this stack is level-60. Simming a level-40 character's
    parse against level-60 magnitudes is the pooled-crawl error from `1x`
    (a level-scaled magnitude cannot be compared across unknown levels).

    🛑 3e A1 — THE POPULATION IS AN EXPLICIT FROZEN ID SET, NOT A WINDOW.
    This used to end `ORDER BY ep.character_id LIMIT ?`. `3d` proved that is a
    SLIDING WINDOW keyed on an arbitrary id, not a cost cap: when the daily
    crawler grew the qualifying population from 157 to 180, four characters left
    and four entered, and the gate read 5-of-41 -> 4-of-38 with **zero code
    changes**. Two gate results from different days were not comparable even
    with identical code, which makes every 3e before/after pair unreadable.

    Returns `(rows, dropped, outside)`:
      * `rows`     — the frozen members that still qualify
      * `dropped`  — frozen members that no longer qualify, WITH THE REASON.
                     A cohort that quietly shrinks is the same defect.
      * `outside`  — how many corpus characters qualify but are not frozen in.
                     Printed, because silence there reads as "everyone was
                     measured".
    """
    placeholders = ",".join("?" * len(cohort_ids))
    sql, params = _completeness_sql(
        max_lag_hours, f"AND ep.character_id IN ({placeholders})", cohort_ids)
    rows = conn.execute(sql, params).fetchall()

    present = {r[0] for r in rows}
    dropped = [(cid, *drop_reason(conn, cid, max_lag_hours))
               for cid in cohort_ids if cid not in present]

    all_sql, all_params = _completeness_sql(max_lag_hours, "", ())
    qualifying = {r[0] for r in conn.execute(all_sql, all_params).fetchall()}
    outside = sorted(qualifying - set(cohort_ids))
    return rows, dropped, outside


def drop_reason(conn, cid, max_lag_hours):
    """Why did a FROZEN cohort member stop qualifying?

    Checked condition by condition against the same completeness filter, so the
    report names the mechanism instead of saying 'gone'. A frozen member is
    never silently omitted and is never substituted.
    """
    name = (conn.execute("SELECT name FROM characters WHERE character_id = ?",
                         (cid,)).fetchone() or [f"id {cid}"])[0]
    if not conn.execute("SELECT 1 FROM characters WHERE character_id = ?",
                        (cid,)).fetchone():
        return name, "character no longer in the corpus at all"
    lvl = conn.execute("SELECT level FROM characters WHERE character_id = ?",
                       (cid,)).fetchone()[0]
    if lvl != 60:
        return name, f"level is now {lvl}, not 60"
    perf = conn.execute(
        "SELECT COUNT(*), MIN(COALESCE(ep.snapshot_lag_hours, 1e9)) "
        "FROM encounter_performance ep "
        "JOIN capture_scopes cs ON cs.scope_id = ep.scope_id "
        "JOIN encounters e ON e.encounter_id = cs.encounter_id "
        "WHERE ep.character_id = ? AND e.is_trash = 0 "
        "  AND e.duration_seconds >= 20 AND ep.dps > 100", (cid,)).fetchone()
    if not perf[0]:
        return name, "no non-trash encounter >=20s with DPS > 100 in the corpus"
    if perf[1] > max_lag_hours:
        return name, (f"best snapshot lag is {perf[1]:.1f}h, above the "
                      f"{max_lag_hours:g}h limit")
    gear = conn.execute(
        "SELECT COUNT(*) FROM snapshot_gear sg JOIN encounter_performance ep "
        "ON ep.snapshot_id = sg.snapshot_id WHERE ep.character_id = ? "
        "AND sg.stats_json IS NOT NULL", (cid,)).fetchone()[0]
    if not gear:
        return name, "no snapshot_gear rows with resolved stats"
    cards = conn.execute(
        "SELECT COUNT(*) FROM snapshot_cards sc JOIN encounter_performance ep "
        "ON ep.snapshot_id = sc.snapshot_id WHERE ep.character_id = ? "
        "AND sc.spell_id IS NOT NULL", (cid,)).fetchone()[0]
    if not cards:
        return name, "no snapshot_cards resolved to spell ids"
    src = conn.execute(
        "SELECT DISTINCT s.source FROM character_snapshots s "
        "JOIN encounter_performance ep ON ep.snapshot_id = s.snapshot_id "
        "WHERE ep.character_id = ?", (cid,)).fetchall()
    if src and all(s[0] in EXCLUDED_SNAPSHOT_SOURCES for s in src):
        return name, (f"every snapshot is source={src[0][0]!r}, which "
                      f"EXCLUDED_SNAPSHOT_SOURCES bars from the cohort")
    return name, ("no single condition isolates it — the completeness filter "
                  "rejects it on a combination; inspect by hand")


# content_type -> the sim preset that matches it. Simming a dungeon parse
# against a raid-boss preset compares two different fights.
CONTENT_PRESET = {
    "raid": "raid_boss_st",
    "dungeon_normal": "mythic_dungeon_st",   # nearest single-target dungeon preset
    "dungeon_mythic": "mythic_dungeon_st",
}


def build_spec_for(conn, snapshot_id, path_token):
    gear = {}
    for slot, item_id, name, stats_json, weapon_json in conn.execute(
            "SELECT slot, item_id, item_name, stats_json, weapon_json "
            "FROM snapshot_gear WHERE snapshot_id = ?", (snapshot_id,)):
        stats, _unmapped = normalise_stats(stats_json)
        slot_name = WEAPON_SLOTS.get(slot, f"slot_{slot}")
        # weapon damage lives only in the item description, and without it the
        # sim gives a crawled character no weapon at all — zeroing white swings
        # and every weapon-percent ability
        weapon = json.loads(weapon_json) if weapon_json else None
        gear[slot_name] = GearItem(item_id=item_id, name=name or f"item {item_id}",
                                   slot=slot_name, stats=stats, weapon=weapon)
    abilities, talents = [], []
    for tree, spell_id, rank in conn.execute(
            "SELECT tree, spell_id, rank FROM snapshot_cards "
            "WHERE snapshot_id = ? AND spell_id IS NOT NULL", (snapshot_id,)):
        card = SlottedCard(spell_id, max(1, rank or 1))
        (abilities if tree == "abilities" else talents).append(card)
    return BuildSpec(
        character_level=60, role=Role("dps"), path=path_token,
        abilities=abilities[:30], talents=talents[:25],
        gear=gear, source="crawled")


def _keyed_zero_reason(entry):
    """3h B2 — WHY a sim-keyed ability produced zero damage, from the sim's own
    per-ability record. The vocabulary matches the refusal messages in
    `ability_model.py` so the reason traces to the exact refusal site."""
    reasons = set()
    for u in entry.get("unresolved_events") or []:
        r = u.get("reason") or ""
        if "states no duration of its own" in r:
            reasons.add("refused-no-duration")
        elif "non-positive duration" in r:
            reasons.add("refused-sentinel")
        elif "sanity limit" in r:
            reasons.add("refused-sanity")
        else:
            reasons.add("refused-other")
    if not (entry.get("events") or []) and not reasons:
        # ability_model.py:735-742 — "0 because nothing is KNOWN"
        reasons.add("no-damage-event-resolves")
    if (entry.get("casts") or 0.0) <= 0.001 and (entry.get("mean_per_cast")
                                                 or 0.0) > 0:
        # tiers.py — the GCD budget starved it: a rotation problem, not a
        # resolution one. Observed in the corpus, so named rather than folded
        # into "refused" (a measured departure from the work order's taxonomy).
        reasons.add("zero-casts-allocated")
    return "+".join(sorted(reasons)) or "zero-mean-unexplained"


def modelled_damage_share(conn, scope_id, character_id, per_ability):
    """Of the damage this character ACTUALLY dealt, what fraction came from
    spells the sim HAS A KEY FOR — split into the share from keys that
    PRODUCED damage and the share from keys that produced ZERO.

    🛑 3h B1 — this docstring used to claim *"spells the sim produced any
    damage for"*, and that was FALSE: `core/sim/tiers.py` writes a
    `per_ability` entry unconditionally, including when every event was
    REFUSED or nothing resolved, so a key means *the sim iterated this
    ability*. Since `slice = (100 + delta) / coverage`, a keyed-but-zero
    ability raises the denominator and lowers the numerator — it pushes slice
    accuracy down twice. The split below is what separates magnitude error
    from zero production; `modelled_damage_pct` remains the SUM of the two so
    no existing verdict moves.

    `per_ability` is the sim result's per-ability mapping (3h B1 — this took a
    bare id set before, which is exactly how the producing/zero distinction
    was invisible).

    This is the third leg of the miss decomposition (PLAN_3B §5.2) and the one
    that tests the revised hypothesis directly: if the sim reproduces a
    character's gear and buffs but only knows magnitudes for 15% of what they
    actually pressed, the miss is per-ability coverage, not stats.

    Pet rows are counted in the denominator — the character's logged DPS
    includes them, so excluding them here would flatter the coverage number.
    """
    sim_spell_ids = set(per_ability.keys())
    producing_ids = {sid for sid, v in per_ability.items()
                     if (v.get("damage") or 0.0) > 0.0}
    rows = conn.execute(
        "SELECT spell_id, spell_name, damage_total, is_pet, spell_school "
        "FROM ability_performance "
        "WHERE scope_id = ? AND character_id = ? AND damage_total > 0",
        (scope_id, character_id)).fetchall()
    total = sum(r[2] for r in rows)
    if not total:
        return None
    has_autos = any(k in sim_spell_ids for k in ("auto_mh", "auto_oh"))
    autos_producing = any(k in producing_ids for k in ("auto_mh", "auto_oh"))

    def is_modelled(r):
        if r[0] in sim_spell_ids:
            return True
        # The log renders auto-attacks as NEGATIVE ids the sim never uses — it
        # keys its swing layer 'auto_mh'/'auto_oh'. Matching on id alone
        # therefore scored every character's white damage as unmodelled and
        # understated coverage by ~9 points.
        #
        # ⚠ Not every negative id is an ordinary swing: extra-attack procs from
        # trinkets and weapons log the same way ('Auto Attack [Hand of
        # Justice]'), and the sim does NOT model those. The discriminator is
        # taken from the row itself rather than from the id's magnitude — a
        # bracket tag that equals the row's own school is a school-flavoured
        # swing, anything else names an item.
        if r[0] >= 0 or not has_autos:
            return False
        name = r[1] or ""
        if "[" not in name:
            return True                       # plain 'Auto Attack'
        tag = name[name.index("[") + 1:].rstrip("]").strip()
        return tag.lower() == (r[4] or "").lower()

    def is_producing(r):
        """A matched row's key produced sim damage. Negative-id auto rows are
        matched through the swing keys, so they take the autos' state."""
        if r[0] in sim_spell_ids:
            return r[0] in producing_ids
        return autos_producing          # matched via the negative-id auto path

    modelled = sum(r[2] for r in rows if is_modelled(r))
    producing = sum(r[2] for r in rows if is_modelled(r) and is_producing(r))
    keyed_zero = modelled - producing
    unmodelled = sorted((r for r in rows if not is_modelled(r)),
                        key=lambda r: -r[2])
    # 3h B2 — the NAMED zero list: every sim key with zero damage, its logged
    # share (0.0 when the log never saw it), and why. Full list, no caps — a
    # renderer may truncate but must say what it dropped.
    logged_by_sid = {r[0]: r for r in rows}
    zero_list = []
    for sid, entry in per_ability.items():
        if sid in producing_ids:
            continue
        lr = logged_by_sid.get(sid)
        zero_list.append({
            "spell_id": sid, "name": entry.get("name"),
            "logged_share_pct": (round(100.0 * lr[2] / total, 1)
                                 if lr else 0.0),
            "why": _keyed_zero_reason(entry),
        })
    zero_list.sort(key=lambda z: -z["logged_share_pct"])
    return {
        "logged_abilities": len(rows),
        "modelled_abilities": sum(1 for r in rows if is_modelled(r)),
        # UNCHANGED expression — the sum of the two splits below, so no
        # existing verdict (floor, qualified, slice bands) moves. (3h B1)
        "modelled_damage_pct": round(100.0 * modelled / total, 1),
        "modelled_and_producing_pct": round(100.0 * producing / total, 1),
        "keyed_but_zero_pct": round(100.0 * keyed_zero / total, 1),
        "keyed_but_zero": zero_list,
        "top_unmodelled": [
            {"spell_id": r[0], "name": r[1], "is_pet": bool(r[3]),
             "share_pct": round(100.0 * r[2] / total, 1)}
            for r in unmodelled[:6]],
    }


def decompose_miss(*, delta_pct, coverage, budget_bound, buff_gain_pct,
                   modelled):
    """Name what the one-directional negative delta can and cannot be.

    🛑 Deliberately produces a VERDICT PER MECHANISM, not a split that sums to
    the miss. Apportioning a multiplicative shortfall across three candidate
    causes would require knowing the answer; what is available is whether each
    cause is *capable* of explaining the size of the miss, which is enough to
    eliminate candidates. Nothing here is fitted or subtracted from a sim run.
    """
    legs = {}
    cov = coverage["coverage_pct"]
    shortfall = (budget_bound or {}).get("estimated_budget_shortfall_pct") or 0.0
    if cov is not None and cov >= 99.9:
        legs["gear_resolution"] = (
            "ELIMINATED — 100% of stat-bearing slots resolved; the sim ran on "
            "this character's whole gear set")
    elif shortfall and abs(delta_pct or 0) > 2 * shortfall:
        legs["gear_resolution"] = (
            f"INSUFFICIENT — {cov:.0f}% of slots resolved, an estimated "
            f"{shortfall:.0f}% of stat budget missing, against a "
            f"{delta_pct:+.0f}% miss. Contributes; cannot account for it")
    else:
        legs["gear_resolution"] = (
            f"CANDIDATE — only {cov:.0f}% of slots resolved (est. {shortfall:.0f}% "
            f"of stat budget missing), comparable to the {delta_pct:+.0f}% miss")
    legs["buffs"] = (
        f"MEASURED at {buff_gain_pct:+.1f}% — the derived layer's whole "
        f"contribution" + (", which cannot account for the miss"
                           if abs(buff_gain_pct) < abs(delta_pct or 0) / 2
                           else ""))
    if modelled is None:
        legs["magnitude_coverage"] = "UNKNOWN — no per-ability rows for this scope"
    elif modelled["modelled_damage_pct"] < 50:
        legs["magnitude_coverage"] = (
            f"DOMINANT — the sim has magnitudes for only "
            f"{modelled['modelled_damage_pct']:.0f}% of the damage this "
            f"character actually dealt "
            f"({modelled['modelled_abilities']}/{modelled['logged_abilities']} "
            f"abilities)")
    else:
        legs["magnitude_coverage"] = (
            f"PARTIAL — {modelled['modelled_damage_pct']:.0f}% of logged damage "
            f"comes from abilities the sim modelled")
    return legs


def _median(xs):
    xs = sorted(x for x in xs if x is not None)
    return xs[len(xs) // 2] if xs else None


def slice_accuracy_bands(results, bands=SLICE_BANDS):
    """Median slice accuracy per coverage band — the self-diagnosing form.

    `slice_accuracy = (100 + delta) / coverage` has coverage in its denominator,
    so a single cohort-wide median is dominated by whichever characters the sim
    happens to model least. The band table costs nothing and shows directly
    where the metric stops being noise: on the `3d` cohort it reads 159.8% over
    everyone and a flat 62.6% at every band from >=20% upward.
    """
    out = {}
    for b in bands:
        xs = [r["slice_accuracy_pct"] for r in results
              if r["slice_accuracy_pct"] is not None
              and (r["modelled"] or {}).get("modelled_damage_pct", 0) >= b]
        out[b] = statistics.median(xs) if xs else None
    return out


def slice_accuracy_band_n(results, bands=SLICE_BANDS):
    """How many characters each band's median was taken over. (`3f` F7)

    🛑 A MEDIAN WITHOUT ITS `n` IS THE DEFECT, NOT A PRESENTATION DETAIL. The
    generated report carried `n` and the committed manifest did not, so the
    artifact an auditor actually reads shipped `">=0": 163.7` — a number this
    project has formally retracted — with no sample size and no caveat, one key
    away from the good number. `>=50` is a median of 8.
    """
    return {b: sum(1 for r in results
                   if r["slice_accuracy_pct"] is not None
                   and (r["modelled"] or {}).get("modelled_damage_pct", 0) >= b)
            for b in bands}


def slice_accuracy_caveat(coverage_pct, floor=SLICE_COVERAGE_FLOOR_PCT):
    """Why a per-character slice accuracy below the floor must not be read.

    🛑 3f F7 — OWNER-VISIBLE DECISION, STATED IN THE MANIFEST: the
    per-character value is **annotated in place, NOT floored**. Flooring would
    delete it, and the extreme values ARE the evidence for `3e`'s retraction —
    `Mutaforma` at 1,859,400% on 0.2% coverage is exactly what "this ratio
    explodes as coverage -> 0" looks like, and a reader who cannot see it has
    to take the retraction on trust. What was wrong was never that the number
    existed; it was that it shipped bare, indistinguishable from a measurement.

    Returns None when the value is above the floor and can be read as-is.
    """
    if coverage_pct is None or coverage_pct >= floor:
        return None
    return (f"NOT A MEASUREMENT — coverage is {coverage_pct:.1f}%, below the "
            f"{floor:g}% floor. slice_accuracy = (100 + delta) / coverage has "
            f"coverage in its denominator, so it explodes as coverage -> 0. "
            f"This value is a diagnostic of low coverage, not of accuracy, and "
            f"must never enter an aggregate.")


def _decomposition_section(results):
    """The corpus-level answer to 'what is the miss made of', built only from
    per-character verdicts — no apportioning, no fitted scale factor."""
    if not results:
        return []
    full_gear = [r for r in results if (r["gear_coverage_pct"] or 0) >= 99.9]
    modelled = [r["modelled"]["modelled_damage_pct"] for r in results
                if r["modelled"]]
    # A character can land inside tolerance while the sim reproduces almost
    # none of what they actually pressed — the modelled fraction happens to
    # total the right number. That is compensating error, not calibration, and
    # the ±20% criterion is structurally blind to it. Reported alongside the
    # criterion, never substituted for it: moving a gate's definition after
    # seeing the result is how a gate stops meaning anything.
    passing = [r for r in results if r["within_tolerance"]]
    qualified = [r for r in passing
                 if (r["modelled"] or {}).get("modelled_damage_pct", 0)
                 >= QUALIFIED_COVERAGE_PCT]
    lines = [
        "", "## Miss decomposition (PLAN_3B §5.2)", "",
        f"🛑 **Read the pass with its coverage.** {len(passing)} characters are "
        f"within ±{AGGREGATE_TOLERANCE_PCT:g}%, but only **{len(qualified)}** of "
        f"them are within tolerance *while the sim also reproduces "
        f"≥{QUALIFIED_COVERAGE_PCT:g}% of the damage they actually dealt*"
        + (": " + ", ".join(
            f"{r['name']} ({r['delta_pct']:+.0f}%, "
            f"{r['modelled']['modelled_damage_pct']:.0f}% modelled)"
            for r in qualified) if qualified else "")
        + ". The rest agree on the total while missing most of the kit — the "
        "modelled slice happens to sum to about the right number. The ±20% "
        "criterion cannot distinguish that from calibration, which is why the "
        "qualified count is now a **Phase 3 exit rider** (stamped 2026-08-06, "
        "before this run) rather than only a reported companion.", "",
        "The one-directional negative delta is decomposed into the three "
        "mechanisms that each produce it, so no single cause is credited "
        "wholesale. Each leg gets a **verdict on whether it is capable of "
        "explaining a miss this size** — deliberately not a split summing to "
        "the miss, which would require knowing the answer.", "",
        f"- **Gear resolution.** Median gear-stat coverage across the gate's "
        f"characters is **{_median([r['gear_coverage_pct'] for r in results]):.0f}%**, "
        f"and **{len(full_gear)} of {len(results)}** resolve **100%** of their "
        f"stat-bearing slots. Those characters were simmed on their entire real "
        f"gear set, so gear under-resolution is **eliminated** for them — and "
        f"their median delta is "
        f"**{_median([r['delta_pct'] for r in full_gear]):+.0f}%**. "
        f"⚠ Coverage is reportable but not repairable from the corpus: an "
        f"unresolved item is unresolved on every snapshot, because those ids "
        f"are absent from the upstream item database.",
        f"- **Buffs.** The derived layer moves sim DPS by a median of "
        f"**{_median([r['buff_gain_pct'] for r in results]):+.1f}%** "
        f"(max {max((r['buff_gain_pct'] for r in results), default=0):+.1f}%).",
        # 3i A5 — "has a key for", not "produces damage for": the phrasing 3h
        # B1 retired everywhere else in this file survived here (a rendered
        # line in the cohort summary).
        f"- **Magnitude coverage.** The sim has a key for a median of "
        f"**{_median(modelled):.0f}%** of what these characters actually dealt"
        + (f" (n={len(modelled)} with per-ability rows)." if modelled else "."),
        "",
        "| leg | characters where it is the stated verdict |",
        "|---|---|",
    ]
    for leg in ("gear_resolution", "buffs", "magnitude_coverage"):
        buckets = {}
        for r in results:
            head = r["miss_decomposition"][leg].split(" —")[0]
            buckets.setdefault(head, []).append(r["name"])
        cell = "; ".join(f"**{k}** {len(v)}" for k, v in
                         sorted(buckets.items(), key=lambda kv: -len(kv[1])))
        lines.append(f"| {leg} | {cell} |")

    unmodelled = {}
    for r in results:
        for u in (r["modelled"] or {}).get("top_unmodelled", []):
            e = unmodelled.setdefault((u["spell_id"], u["name"]),
                                      {"chars": 0, "share": 0.0})
            e["chars"] += 1
            e["share"] += u["share_pct"]
    if unmodelled:
        lines += [
            "", "### Biggest unmodelled abilities across the gate", "",
            "Ranked by how much of their owners' real damage the sim produces "
            "nothing for. This is the shortlist the next magnitude work should "
            "read — it is measured demand, not a guess at what matters.", "",
            "| spell | id | characters | mean share of their damage |",
            "|---|---:|---:|---:|"]
        for (sid, name), e in sorted(unmodelled.items(),
                                     key=lambda kv: -kv[1]["share"])[:20]:
            lines.append(f"| {name} | {sid} | {e['chars']} | "
                         f"{e['share'] / e['chars']:.1f}% |")
    return lines


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cohort", type=Path, default=COHORT_PATH,
                    help="frozen cohort file (3e A1). The population is DATA, "
                         "not a constant in this tool, and it is not a window")
    ap.add_argument("--max-lag-hours", type=float, default=0.0,
                    help="max build-snapshot staleness vs the parse (default 0 = "
                         "the snapshot was captured AT that encounter). Any other "
                         "value is reported in the output, never applied silently")
    ap.add_argument("--read-holdout", action="store_true",
                    help="reveal the pre-registered holdout's results "
                         f"({HOLDOUT_SLUG}). Withheld by default: reading it is a "
                         "close-out action, and a holdout read every run is not a "
                         "holdout. Never tune against it")
    ap.add_argument("--allow-dirty", action="store_true",
                    help="3h A7 — permit writing the committed manifest from a "
                         "DIRTY working tree. Refused by default: both prior "
                         "manifests shipped git_working_tree_dirty=true, so their "
                         "git_sha did not identify the code that produced the "
                         "numbers. The flag is recorded in the manifest")
    args = ap.parse_args()

    if not BUILDS_DB_PATH.exists():
        print(f"{BUILDS_DB_PATH} missing — run ingest/logs_gg/build_builds_db.py")
        return 1
    bdb = sqlite3.connect(BUILDS_DB_PATH)
    asc = connect(DB_PATH)
    conv = ce.load_rating_conversions(asc, level=60)

    cohort_ids, cohort_spec = load_frozen_cohort(args.cohort)
    slot_medians = slot_budget_medians(bdb)
    rows, dropped, outside = candidates(bdb, cohort_ids, args.max_lag_hours)
    print(f"[cohort] FROZEN at {len(cohort_ids)} character ids "
          f"({args.cohort.name}, frozen {cohort_spec.get('frozen_at')}) — "
          f"not a sliding window")
    print(f"[candidates] {len(rows)} of {len(cohort_ids)} frozen members still "
          f"pass the completeness filter (max build staleness "
          f"{args.max_lag_hours:g}h)")
    for cid, cname, why in dropped:
        print(f"[dropped] {cname} ({cid}) — {why}")
    print(f"[outside] {len(outside)} corpus characters qualify but are NOT in "
          f"the frozen cohort, so they are not scored"
          + (f": {', '.join(str(i) for i in outside[:12])}"
             + (" ..." if len(outside) > 12 else "") if outside else ""))

    results, excluded, seen_chars = [], [], set()
    for (cid, cname, snapshot_id, dps, path, boss, ctype, dur, enc_id,
         lag, level, scope_id, _longest) in rows:
        if cid in seen_chars:
            continue          # one encounter per character — no double counting
        preset = CONTENT_PRESET.get(ctype)
        if preset is None:
            excluded.append((cid, cname,
                             f"content_type {ctype!r} has no matching sim preset "
                             f"— simming it against a raid profile would compare "
                             f"two different fights"))
            continue
        content = get_preset(preset)
        token = PATH_TOKEN.get((path or "").lower())
        if token is None:
            excluded.append((cid, cname, f"path {path!r} not resolvable"))
            continue
        if token == "Duality":
            # rule 3: named, not silently dropped
            excluded.append((cid, cname,
                             "Path of Duality — parses excluded from absolute "
                             "calibration by the 2d bug advisory (AP cycles "
                             "mid-parse)"))
            continue
        # 3b pre-flight §0.3: the buff layer, DERIVED from the group in the
        # same capture scope (never guessed, never fitted). The unbuffed sim
        # runs alongside so the layer's effect is visible per character.
        buff_keys, buff_prov = derive_buffs(bdb, scope_id, cid, snapshot_id)
        try:
            spec = build_spec_for(bdb, snapshot_id, token)
            cs0 = compute_stats(spec, content, conv, conn=asc)
            apl = generate_apl(asc, spec, content, cs0)
            res0 = fast_sim(asc, spec, content, cs0, apl=apl)
            spec.raid_buffs = buff_keys
            if buff_keys:
                cs = compute_stats(spec, content, conv, conn=asc)
                res = fast_sim(asc, spec, content, cs, apl=apl)
            else:
                cs, res = cs0, res0
        except Exception as e:                      # noqa: BLE001 — reported
            excluded.append((cid, cname, f"sim error: {type(e).__name__}: {e}"))
            continue
        seen_chars.add(cid)
        sim_dps = res.primary_value
        delta = 100 * (sim_dps / dps - 1) if dps else None
        # PLAN_3B §5.2 — decompose the miss instead of attributing it wholesale
        cov = gear_coverage(bdb, snapshot_id)
        bound = missing_stat_budget_bound(bdb, snapshot_id, coverage=cov,
                                          slot_medians=slot_medians)
        buff_gain = (100 * (sim_dps / res0.primary_value - 1)
                     if res0.primary_value else 0.0)
        # 3h B1 — passes the full per-ability mapping, not a bare key set, so
        # the share can be split into producing vs keyed-but-zero.
        modelled = modelled_damage_share(bdb, scope_id, cid, res.per_ability)
        # 🆕 3g G1 — the auto-attack's share of SIM damage, so E13's before/after
        # attribution is printed rather than reasoned about. `3f` found that 24
        # of 36 scored characters carry a melee auto in their top 5 and that one
        # of the gate's two qualified passes (`Ari`) has it as its LARGEST
        # modelled source — with every white swing ~78x over. A per-character
        # exposure number is the only way to say which deltas that touches.
        sim_by_ability = {k: v["damage"] for k, v in (res.per_ability or {}).items()}
        sim_total = sum(sim_by_ability.values())
        auto_dmg = sum(v for k, v in sim_by_ability.items()
                       if k in ("auto_mh", "auto_oh"))
        results.append({
            "character_id": cid, "name": cname, "path": token, "boss": boss,
            "content_type": ctype, "sim_preset": preset,
            "duration_s": dur, "logged_dps": dps, "snapshot_lag_hours": lag,
            "sim_dps": sim_dps, "delta_pct": delta,
            "sim_dps_unbuffed": res0.primary_value,
            "buffs_applied": buff_keys,
            "buff_provenance": buff_prov,
            # 3e A3 — None, not False, when the sim modelled NOTHING for this
            # character. `abs(delta) <= tol` with no other term let a character
            # whose modelled damage maps to none of what they logged score a
            # verdict either way; three cohort members sit at 0.0% coverage with
            # a non-null delta. Slice accuracy already refuses to report at zero
            # coverage (below); this is the same treatment for the criterion.
            # 🛑 A floor ABOVE zero changes the criterion and is an owner
            # decision — taken 2026-08-06 and stamped for the NEXT gate, not
            # this one. See SUCCESSOR_COVERAGE_FLOOR_PCT.
            # ✅ 3g G4 — THE STAMPED FLOOR IS NOW APPLIED. Below it the verdict
            # is None (NOT SCOREABLE), not False, for the same reason zero
            # coverage returns None: the sim has too little of this character
            # modelled for `abs(delta) <= tol` to mean anything, and "we have no
            # opinion" is a different statement from "it failed". A character at
            # 4.6% coverage landing inside ±20% is arithmetic about 4.6% of a
            # kit, not a calibration.
            "within_tolerance": (
                None if ((modelled or {}).get("modelled_damage_pct") or 0.0)
                < SUCCESSOR_COVERAGE_FLOOR_PCT
                else abs(delta) <= AGGREGATE_TOLERANCE_PCT),
            "gear_coverage_pct": cov["coverage_pct"],
            "gear_unresolved_pieces": len(cov["missing"]),
            "gear_name_matched_pieces": len(cov["name_matched"]),
            "gear_budget_shortfall_pct": bound.get("estimated_budget_shortfall_pct"),
            "buff_gain_pct": buff_gain,
            "modelled": modelled,
            "miss_decomposition": decompose_miss(
                delta_pct=delta, coverage=cov, budget_bound=bound,
                buff_gain_pct=buff_gain, modelled=modelled),
            "abilities": len(spec.abilities), "talents": len(spec.talents),
            "gear_pieces": len(spec.gear),
            "top_sim_abilities": [
                r["name"] for _sid, r in
                sorted(res.per_ability.items(), key=lambda kv: -kv[1]["damage"])[:5]],
            "auto_share_of_sim_pct": (round(100.0 * auto_dmg / sim_total, 1)
                                      if sim_total else None),
            "warnings": sorted({w for w in res.warnings})[:8],
        })

    # 3d F3 — SLICE ACCURACY, per character and as a cohort median.
    #
    #     slice_accuracy = (100 + delta) / coverage
    #
    # Algebraically exact, and it separates the two things `delta` alone cannot:
    # how MUCH of the kit is modelled (coverage) from how WELL the modelled part
    # is modelled (accuracy). Before this, only coverage was tracked.
    #
    # 🛑 PURE INSTRUMENTATION. It changes no verdict — `within_tolerance`,
    # `passing`, `qualified`, `crit_met` and `rider_met` are computed exactly as
    # before, and none of them reads this field.
    #
    # Why it matters for `3e`: coverage is a MEMBERSHIP TEST, so a spell modelled
    # at 4.5x-under counts as fully covered. Coverage work therefore mechanically
    # raises coverage while depressing slice accuracy, and a character can be
    # LOST from the gate by pure coverage work with no accuracy change at all.
    # Standing rule from `3e` on: every coverage task reports this before and
    # after. A task that raises coverage while dropping slice accuracy has moved
    # the metric, not the model.
    for r in results:
        cov_pct = (r["modelled"] or {}).get("modelled_damage_pct")
        r["slice_accuracy_pct"] = (
            (100.0 + r["delta_pct"]) / cov_pct * 100.0
            if cov_pct and r["delta_pct"] is not None and cov_pct > 0 else None)
        # 3h B3 — the same ratio over PRODUCING coverage only. Reported BESIDE
        # the existing figure, never in place of it: the criterion's definition
        # does not change in this session (SESSION_3H_PRIMER Q2).
        prod_pct = (r["modelled"] or {}).get("modelled_and_producing_pct")
        r["slice_accuracy_producing_pct"] = (
            (100.0 + r["delta_pct"]) / prod_pct * 100.0
            if prod_pct and r["delta_pct"] is not None and prod_pct > 0
            else None)

    # 3e A4 — the holdout is SPLIT OUT OF THE HEADLINE. Everything the gate
    # reports is the tuning set unless --read-holdout is passed.
    holdout = [r for r in results if r["character_id"] in HOLDOUT_IDS]
    tuning = [r for r in results if r["character_id"] not in HOLDOUT_IDS]

    slice_bands = slice_accuracy_bands(tuning)
    slice_median = slice_bands.get(SLICE_COVERAGE_FLOOR_PCT)

    passing = [r for r in tuning if r["within_tolerance"] is True]
    unscoreable = [r for r in tuning if r["within_tolerance"] is None]
    qualified = [r for r in passing
                 if (r["modelled"] or {}).get("modelled_damage_pct", 0)
                 >= QUALIFIED_COVERAGE_PCT]
    crit_met = len(passing) >= MIN_WITHIN_TOLERANCE
    rider_met = len(qualified) >= MIN_QUALIFIED
    print(f"[gate] TUNING SET: {len(passing)} of {len(tuning)} simmed "
          f"characters within ±{AGGREGATE_TOLERANCE_PCT:g}%  "
          f"(criterion: ≥{MIN_WITHIN_TOLERANCE})  "
          f"-> {'PASS' if crit_met else 'NOT MET'}")
    print(f"[gate] of those, {len(qualified)} also have "
          f"≥{QUALIFIED_COVERAGE_PCT:g}% of their real damage modelled "
          f"(rider: ≥{MIN_QUALIFIED}) -> {'PASS' if rider_met else 'NOT MET'}")
    if unscoreable:
        # 3g G4 — the two reasons are separated, because "the sim modelled
        # nothing" and "the sim modelled too little to judge" are different
        # amounts of information, and the second is a criterion change this
        # session made deliberately.
        zero = [r for r in unscoreable
                if not (r["modelled"] or {}).get("modelled_damage_pct")]
        under = [r for r in unscoreable if r not in zero]
        if zero:
            print(f"[gate] {len(zero)} character(s) are NOT SCOREABLE — the "
                  f"sim modelled 0% of their damage, so within_tolerance is "
                  f"None rather than False: "
                  + ", ".join(f"{r['name']} ({r['delta_pct']:+.0f}%)"
                              for r in zero))
        if under:
            print(f"[gate] {len(under)} character(s) are NOT SCOREABLE under "
                  f"the {SUCCESSOR_COVERAGE_FLOOR_PCT:g}% COVERAGE FLOOR "
                  f"applied from {SUCCESSOR_FLOOR_APPLIED_FROM} — too little "
                  f"of their kit is modelled for ±{AGGREGATE_TOLERANCE_PCT:g}% "
                  f"to mean anything: "
                  + ", ".join(
                      f"{r['name']} ({r['delta_pct']:+.0f}% on "
                      f"{(r['modelled'] or {}).get('modelled_damage_pct', 0):.1f}% "
                      f"coverage)" for r in under))
    # A character can clear ±20% on 4.6% coverage. The criterion cannot see
    # that; printing the passers' coverage is what makes it visible.
    if passing:
        print("[gate] coverage of the passers: "
              + ", ".join(
                  f"{r['name']} {(r['modelled'] or {}).get('modelled_damage_pct', 0):.1f}%"
                  for r in sorted(passing, key=lambda r: (r["modelled"] or {})
                                  .get("modelled_damage_pct", 0))))
    # 3d F3 / 3e A2 — reported next to coverage, never in place of a verdict,
    # and NEVER aggregated across a cohort spanning 0.2% to 82% coverage.
    if slice_median is not None:
        print(f"[slice] median slice accuracy {slice_median:.1f}% "
              f"AT COVERAGE ≥{SLICE_COVERAGE_FLOOR_PCT:g}% "
              f"(n={sum(1 for r in tuning if (r['modelled'] or {}).get('modelled_damage_pct', 0) >= SLICE_COVERAGE_FLOOR_PCT and r['slice_accuracy_pct'] is not None)})"
              f" — <100% means the sim UNDER-produces on what it does model")
    else:
        print(f"[slice] median slice accuracy: n/a at coverage "
              f"≥{SLICE_COVERAGE_FLOOR_PCT:g}%")
    print("[slice] bands: " + "  ".join(
        f"≥{b:g}%: {'n/a' if v is None else f'{v:.1f}%'}"
        for b, v in sorted(slice_bands.items())))
    # 3h B3 — the SAME median over PRODUCING coverage only, beside the
    # existing figure. Instrumentation: the headline and every verdict still
    # read modelled_damage_pct (Q2 — changing the headline is a criterion
    # change and belongs in a stamped successor).
    prod_xs = [r.get("slice_accuracy_producing_pct") for r in tuning
               if r.get("slice_accuracy_producing_pct") is not None
               and (r["modelled"] or {}).get("modelled_and_producing_pct", 0)
               >= SLICE_COVERAGE_FLOOR_PCT]
    prod_median = statistics.median(prod_xs) if prod_xs else None
    print(f"[slice] producing-only: median "
          + (f"{prod_median:.1f}%" if prod_median is not None else "n/a")
          + f" AT PRODUCING COVERAGE ≥{SLICE_COVERAGE_FLOOR_PCT:g}% "
          f"(n={len(prod_xs)}) — same ratio with keyed-but-zero keys removed "
          f"from the denominator (3h B)")
    # 3h B — what coverage was actually counting: the cohort's keyed-but-zero
    # exposure, so §4 of the 3g audit is a measured quantity from this line on.
    kbz = [((r["modelled"] or {}).get("keyed_but_zero_pct") or 0.0)
           for r in tuning if r["modelled"]]
    n_kbz = sum(1 for v in kbz if v > 0)
    if kbz:
        print(f"[coverage] keyed-but-zero share of logged damage: median "
              f"{statistics.median(kbz):.1f}%, max {max(kbz):.1f}%")
    print(f"[coverage] {n_kbz} of {len(kbz)} characters carry any "
          f"keyed-but-zero logged damage; the per-character zero lists are in "
          f"the JSON/markdown artifacts (full lists, uncapped)")
    print(f"[floor] the {SUCCESSOR_COVERAGE_FLOOR_PCT:g}% coverage floor on "
          f"within_tolerance — stamped {SUCCESSOR_FLOOR_EFFECTIVE_FROM}, "
          f"APPLIED from {SUCCESSOR_FLOOR_APPLIED_FROM} — is IN FORCE in the "
          f"numbers above. Not re-tuned this session: changing it after seeing "
          f"a result is moving a gate after seeing its number")
    if args.read_holdout:
        h_pass = [r for r in holdout if r["within_tolerance"] is True]
        print(f"[HOLDOUT] READ — {HOLDOUT_SLUG}. {len(h_pass)} of "
              f"{len(holdout)} within ±{AGGREGATE_TOLERANCE_PCT:g}%. This is a "
              f"validation reading, NOT part of the criterion.")
        for r in sorted(holdout, key=lambda r: r["character_id"]):
            print(f"[HOLDOUT]   {r['name']} ({r['character_id']}): "
                  f"{r['delta_pct']:+.1f}%, "
                  f"{(r['modelled'] or {}).get('modelled_damage_pct', 0):.1f}% "
                  f"modelled, slice "
                  + (f"{r['slice_accuracy_pct']:.1f}%"
                     if r["slice_accuracy_pct"] is not None else "n/a"))
    else:
        print(f"[holdout] {len(holdout)} member(s) WITHHELD from the headline "
              f"({HOLDOUT_SLUG}) — pass --read-holdout to read. A holdout read "
              f"every run is not a holdout.")
    print(f"[exit] PHASE 3 EXIT: "
          f"{'MET' if (crit_met and rider_met) else 'NOT MET'} — needs both. "
          "Rider stamped 2026-08-06 BEFORE this run "
          "(predictions/CALIBRATION_TOLERANCE.md addendum); a character passing "
          "±20% while the sim reproduces a fraction of its kit is compensating "
          "error, not calibration.")

    # 3e A4 — the report is the TUNING SET unless the holdout was deliberately
    # read. Writing holdout deltas into a file this session then reads is the
    # same leak as printing them.
    report_results = tuning + (holdout if args.read_holdout else [])

    lines = [
        "# Calibration gate — crawled characters",
        "",
        "Inherited from PHASE_2 §8.2: *the sim reproduces ≥3 real characters "
        f"within ±{AGGREGATE_TOLERANCE_PCT:g}% aggregate DPS* "
        "(`predictions/CALIBRATION_TOLERANCE.md`, unchanged).",
        "",
        f"**Result: {len(passing)} of {len(tuning)} within tolerance — "
        f"{'PASS' if crit_met else 'NOT MET'}.** "
        f"(tuning set; {len(holdout)} holdout member(s) "
        + ("READ — see below" if args.read_holdout else "withheld") + ")",
        "",
        "## Cohort — FROZEN, not a window (3e A1)",
        "",
        f"The population is the **{len(cohort_ids)} character ids committed in "
        f"`{args.cohort.name}`**, frozen {cohort_spec.get('frozen_at')} from the "
        f"`3d` close-out manifest. It is not `ORDER BY character_id LIMIT N`, "
        f"which `3d` proved is a sliding window: the gate moved 5-of-41 to "
        f"4-of-38 with **zero code changes** when the crawler grew the "
        f"qualifying population 157 to 180.",
        "",
        f"- **{len(rows)} of {len(cohort_ids)}** frozen members still pass the "
        f"completeness filter.",
        f"- **{len(dropped)} dropped**, each with its reason — a frozen member "
        f"is never silently omitted and never substituted"
        + (":" if dropped else "."),
    ]
    for cid, cname, why in dropped:
        lines.append(f"  - **{cname}** ({cid}): {why}")
    lines += [
        f"- **{len(outside)}** corpus characters qualify but are **not** in the "
        f"frozen cohort, so they were not scored. The frozen cohort goes stale "
        f"by design; replacing it means a new file with a new slug and a stated "
        f"reason, never an edit to this one.",
        "",
        f"⚠ **The holdout ({HOLDOUT_SLUG}) is split out of the headline.** Its "
        f"{len(holdout)} members were previously counted in \"n of 41\", so any "
        f"fix that lifted them moved the headline **and** spent the holdout in "
        f"the same number. They are "
        + ("**READ** in this run — a close-out action."
           if args.read_holdout else "withheld from this report."),
        "",
        "## Phase 3 exit criterion",
        "",
        "🛑 **The ±20% pass definition above is unchanged.** A rider was added "
        "to the *exit* on **2026-08-06, before the scraped-coefficient ingest "
        "was re-run through this gate** — a stricter bar than what passed at "
        "the time, stamped while the number it judges was still unknown "
        "(`predictions/CALIBRATION_TOLERANCE.md` addendum).",
        "",
        f"> Phase 3 exits only when **≥{MIN_WITHIN_TOLERANCE} characters are "
        f"within ±{AGGREGATE_TOLERANCE_PCT:g}%** AND **≥{MIN_QUALIFIED} of "
        f"those also have ≥{QUALIFIED_COVERAGE_PCT:g}% of their real damage "
        "modelled**.",
        "",
        f"| condition | required | actual | |", "|---|---:|---:|---|",
        f"| within ±{AGGREGATE_TOLERANCE_PCT:g}% | ≥{MIN_WITHIN_TOLERANCE} | "
        f"{len(passing)} | {'✅' if crit_met else '❌'} |",
        f"| of those, ≥{QUALIFIED_COVERAGE_PCT:g}% damage modelled | "
        f"≥{MIN_QUALIFIED} | {len(qualified)} | {'✅' if rider_met else '❌'} |",
        "",
        f"**PHASE 3 EXIT: {'MET' if (crit_met and rider_met) else 'NOT MET'}.** "
        "The rider exists because an aggregate criterion cannot distinguish "
        "calibration from a modelled slice that happens to sum to about the "
        "right number.",
        "",
        "Candidates were selected by data completeness only (level 60, resolved "
        "gear stats, resolved cards, a non-trash encounter ≥20s), never by how "
        "well the sim did.",
        "",
        f"**Build-to-parse staleness allowed: {args.max_lag_hours:g}h** "
        + ("(strict — every snapshot below was captured AT its own encounter, "
           "so it IS the build that produced the parse)."
           if args.max_lag_hours == 0 else
           "(LOOSENED — a lagged snapshot is a different build wearing the same "
           "name; read the lag column before trusting any row)."),
        "",
        f"Directional summary: **{sum(1 for r in report_results if (r['delta_pct'] or 0) < 0)} "
        f"of {len(report_results)} deltas are negative.** A one-sided distribution is a "
        "missing multiplicative layer, not noise.",
        "",
        "## Slice accuracy, by coverage band (3e A2)",
        "",
        "`slice_accuracy = (100 + delta) / coverage` has **coverage in its "
        "denominator**, so it explodes as coverage → 0 and must never be "
        "aggregated across a cohort spanning single-digit to 80%+ coverage. "
        "`3d`'s all-characters median of 159.8% read as *\"the sim "
        "over-produces the slice it models by 60%\"*. That is **backwards** — "
        "it is a low-coverage artifact. The readable bands are below; the "
        "sim UNDER-produces on what it has a key for. ⚠ *\"has a key for\"*, "
        "not *\"models\"* — see the producing/keyed-but-zero split (3h B).",
        "",
        "| coverage floor | n | median slice accuracy |", "|---:|---:|---:|",
    ]
    for b, v in sorted(slice_bands.items()):
        n = sum(1 for r in tuning if r["slice_accuracy_pct"] is not None
                and (r["modelled"] or {}).get("modelled_damage_pct", 0) >= b)
        lines.append(f"| ≥{b:g}% | {n} | "
                     + (f"{v:.1f}%" if v is not None else "n/a") + " |")
    lines += [
        "",
        f"**Headline figure: {slice_median:.1f}% at coverage "
        f"≥{SLICE_COVERAGE_FLOOR_PCT:g}%**"
        if slice_median is not None else
        f"**Headline figure: n/a at coverage ≥{SLICE_COVERAGE_FLOOR_PCT:g}%**",
        "",
        # 3h B3 — beside, never instead (Q2).
        f"**Producing-only companion (3h B): median "
        + (f"{prod_median:.1f}%" if prod_median is not None else "n/a")
        + f" at PRODUCING coverage ≥{SLICE_COVERAGE_FLOOR_PCT:g}% "
        f"(n={len(prod_xs)})** — the same ratio with keyed-but-zero keys "
        f"removed from the denominator. The headline and every verdict still "
        f"read the has-a-key figure; changing that is a criterion change and "
        f"belongs in a stamped successor.",
        "",
        "🚨 **Consequence, corrected at `3h` A2 (the ~62% this paragraph "
        "cited until then was measured on E13's 100×-inflated autos).** "
        "Landing `delta = 0` needs `slice × coverage = 1.0`, so at the "
        "current slice accuracy the coverage lever is arithmetically dead — "
        "no attainable coverage substitutes for magnitude. See "
        "`predictions/CALIBRATION_TOLERANCE.md` for the lever arithmetic.",
        "",
        f"✅ **APPLIED, from {SUCCESSOR_FLOOR_APPLIED_FROM}:** a "
        f"**{SUCCESSOR_COVERAGE_FLOOR_PCT:g}% coverage floor on "
        f"`within_tolerance` itself**, stamped "
        f"{SUCCESSOR_FLOOR_EFFECTIVE_FROM} and in force in every number in this "
        f"report. Below the floor the verdict is **NOT SCOREABLE** (None), not "
        f"False — the same treatment zero coverage already had, for the same "
        f"reason: *\"we have no opinion\"* is a different statement from "
        f"*\"it failed\"*.",
        "",
        f"**Attribution, settled from git in `3g` G4** rather than from memory, "
        f"because the floor is credited to the owner three times in `3e`'s "
        f"record while being numerically identical to a constant Code chose in "
        f"its own voice. `git log -S` puts both in ONE commit (`68779e7`): the "
        f"**owner decided the policy** — that a floor applies, at the NEXT gate "
        f"and not the one being run — and **Code chose the value**, in A2 of "
        f"the same commit, from the band table. Neither claim was false; a "
        f"reader could take *\"owner decision\"* to cover the number too. The "
        f"property that matters survives either reading: the value was fixed "
        f"**before** it was applied to a criterion, and it is strictly harsher.",
        "",
        f"🛑 **Not re-tuned in `3g`.** Changing 20.0 after seeing this "
        f"session's result would be moving a gate after seeing its number, in "
        f"either direction.",
        "",
        "Buffs are DERIVED from the group in the same capture scope — a buff "
        "applies only when a participant's linked board holds the granting "
        "card (`core/builds/group_buffs.py`). This is a lower bound: unlinked "
        "boards and unmeasured buffs contribute nothing, and nothing is fitted.",
        "",
        "| character | path | boss | build lag (h) | logged DPS | sim unbuffed | sim buffed | delta | buffs | gear cov | modelled dmg | within ±20% |",
        "|---|---|---|---:|---:|---:|---:|---:|---|---:|---:|---|",
    ]
    for r in sorted(report_results, key=lambda r: abs(r["delta_pct"] or 1e9)):
        md = r["modelled"]
        modelled_cell = f"{md['modelled_damage_pct']:.0f}%" if md else "n/a"
        # 3e A3: None is not False. 'n/a' means the sim modelled nothing for
        # this character, so the criterion has no opinion — reporting NO there
        # would claim a measurement that was never made.
        verdict = {True: "yes", False: "NO", None: "n/a (0% modelled)"}[
            r["within_tolerance"]]
        lines.append(
            f"| {r['name']} ({r['character_id']}) | {r['path']} | {r['boss']} "
            f"| {r['snapshot_lag_hours']:.1f} "
            f"| {r['logged_dps']:,.0f} | {r['sim_dps_unbuffed']:,.0f} "
            f"| {r['sim_dps']:,.0f} "
            f"| {r['delta_pct']:+.1f}% | {len(r['buffs_applied'])} "
            f"| {r['gear_coverage_pct']:.0f}% "
            f"| {modelled_cell} "
            f"| {verdict} |")

    lines += _decomposition_section(report_results)

    lines += ["", "## Excluded, and why", ""]
    # 🆕 3g G8 — NO SILENT CAP. This truncated at `excluded[:40]` and printed
    # "none" only when the list was empty, so 41 losses would have printed 40
    # and said nothing about the 41st. The manifest always carried them all;
    # the report is what a person reads.
    for cid, cname, why in excluded:
        lines.append(f"- {cname} ({cid}): {why}")
    if not excluded:
        lines.append("- none")

    lines += ["", "## Per-character detail (mechanism, not just a delta)", ""]
    for r in report_results:
        lines += [
            f"### {r['name']} ({r['character_id']}) — {r['path']}",
            f"- {r['boss']}, {r['content_type']} (sim preset {r['sim_preset']}), "
            f"{r['duration_s']:.0f}s; "
            f"{r['abilities']} abilities / {r['talents']} talents / "
            f"{r['gear_pieces']} gear pieces resolved",
            f"- logged {r['logged_dps']:,.0f} vs sim {r['sim_dps']:,.0f} "
            f"({r['delta_pct']:+.1f}%; unbuffed sim {r['sim_dps_unbuffed']:,.0f})",
            f"- sim's top abilities: {', '.join(r['top_sim_abilities'])}",
            f"- gear: {r['gear_coverage_pct']:.0f}% of stat-bearing slots "
            f"resolved ({r['gear_unresolved_pieces']} unresolved"
            + (f", est. {r['gear_budget_shortfall_pct']:.0f}% of stat budget missing"
               if r['gear_budget_shortfall_pct'] else "")
            + (f"; ⚠ {r['gear_name_matched_pieces']} piece(s) matched by NAME, "
               f"which can land on the wrong difficulty variant"
               if r['gear_name_matched_pieces'] else "") + ")",
        ]
        if r["modelled"]:
            md = r["modelled"]
            # 3h B1 — "has a key for", not "produces damage for": the old
            # wording was the docstring's false claim, rendered.
            lines.append(
                f"- magnitude coverage: sim has a key for "
                f"**{md['modelled_damage_pct']:.0f}%** of this character's real "
                f"damage ({md['modelled_abilities']}/{md['logged_abilities']} "
                f"logged abilities) — "
                f"**{md.get('modelled_and_producing_pct', 0):.0f}% producing / "
                f"{md.get('keyed_but_zero_pct', 0):.0f}% keyed-but-zero**")
            # 3h B2 — the FULL zero list, uncapped. A keyed-but-zero ability
            # depresses slice accuracy twice (denominator up, numerator down),
            # so every one is named with its reason.
            for z in md.get("keyed_but_zero") or []:
                lines.append(
                    f"  - keyed-but-zero: {z['name']} ({z['spell_id']}) — "
                    f"{z['logged_share_pct']:.1f}% of logged damage — "
                    f"{z['why']}")
            if md["top_unmodelled"]:
                lines.append("  - biggest unmodelled: " + ", ".join(
                    f"{u['name']} ({u['spell_id']}) {u['share_pct']:.0f}%"
                    for u in md["top_unmodelled"][:4]))
        lines.append("- miss decomposition:")
        for leg, verdict in r["miss_decomposition"].items():
            lines.append(f"  - **{leg}**: {verdict}")
        prov = r.get("buff_provenance") or {}
        lines.append(
            f"- buffs derived from group: "
            f"{', '.join(r['buffs_applied']) if r['buffs_applied'] else 'none'} "
            f"({prov.get('participants_with_board', 0)} of "
            f"{prov.get('participants', 0)} scope participants have a linked "
            f"board — derivation is a lower bound)")
        for key, grant in (prov.get("applied") or {}).items():
            names = ", ".join(f"{n} (lag {lag:.0f}h)" if lag else n
                              for n, _cid, lag in grant["granted_by"][:4])
            note = f" ⚠ {grant['assumption']}" if grant.get("assumption") else ""
            lines.append(f"  - {key}: held by {names}{note}")
        if prov.get("not_derivable"):
            lines.append(
                f"  - not derivable (no visible holder): "
                f"{', '.join(prov['not_derivable'])}")
        for w in r["warnings"]:
            lines.append(f"  - ⚠ {w}")
        lines.append("")
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"[report] {REPORT_PATH}")

    (DATA_DERIVED / "calibration_crawled.json").write_text(
        json.dumps({"results": report_results, "excluded": excluded,
                    "tolerance_pct": AGGREGATE_TOLERANCE_PCT,
                    "holdout_withheld": not args.read_holdout,
                    "holdout_ids": list(HOLDOUT_IDS),
                    "passing": len(passing)}, indent=1, default=str),
        encoding="utf-8")

    write_gate_manifest(tuning, holdout, passing, qualified, crit_met,
                        rider_met, slice_bands, corpus_totals(bdb),
                        cohort_ids, dropped, outside, cohort_spec,
                        read_holdout=args.read_holdout,
                        n_qualifying=len(rows), excluded=excluded,
                        band_n=slice_accuracy_band_n(tuning),
                        allow_dirty=args.allow_dirty)
    return 0


def corpus_totals(bdb):
    """Row counts for the corpus tables the cohort is drawn from.

    Counts and hashes only — no bulk data. `.gitignore:10` stays as it is; the
    point is that an auditor with only the repo can tell whether a claimed gate
    result was produced against the same corpus they hold.
    """
    out = {}
    for t in ("characters", "character_snapshots", "snapshot_cards",
              "snapshot_gear", "encounters", "capture_scopes",
              "encounter_performance", "ability_performance"):
        try:
            out[t] = bdb.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        except Exception:                            # noqa: BLE001
            out[t] = None
    return out


def write_gate_manifest(tuning, holdout, passing, qualified, crit_met,
                        rider_met, slice_bands, corpus, cohort_ids, dropped,
                        outside, cohort_spec, read_holdout=False,
                        n_qualifying=None, excluded=(), band_n=None,
                        allow_dirty=False):
    """3d E2 — a small COMMITTED record of what a gate run actually measured.

    Until now the gate's headline numbers were reproducible only on the owner's
    machine: `data/derived/` is gitignored, no `.db` is committed, and the corpus
    builder was in no chain. Every figure in this project was a *trust me*.

    🚨 AND THE COHORT USED TO MOVE ON ITS OWN.
    Measured in `3d`: rebuilding `builds.db` after the daily crawler ran took the
    gate from **5 of 41 to 4 of 38 with zero code changes**, because
    `candidates()` was `ORDER BY character_id LIMIT N` over a population that
    grew from 157 to 180 — a SLIDING WINDOW keyed on an arbitrary id, not a cost
    cap. Four characters left and four entered for no reason but their id.

    ✅ **Fixed in 3e A1**: the population is now the frozen id set committed in
    `predictions/cohort_frozen_3e.json`, and this manifest records which of them
    still qualified, which dropped and why, and how many qualifying characters
    were deliberately not scored. It is small, deterministic and committed.

    ⚠ Writes `gate_manifest_3e.json` — a NEW name. `gate_manifest.json` is the
    immutable record of the `3d` run the cohort was frozen from.
    """
    band_n = band_n or {}

    # 🛑 3f F7/Q1 — A RUN THAT DOES NOT READ THE HOLDOUT MUST NOT ERASE THE
    # RUN THAT DID. Before this, any gate run without --read-holdout rewrote
    # the committed manifest's holdout block to "REDACTED", deleting `3e`'s
    # close-out reading. That put every later session in a false dilemma:
    # report the gate per commit (and destroy the holdout record) or preserve
    # the record (and never re-run the gate). `3f`'s whole invariant is
    # per-commit gate reporting, so the dilemma was live and immediate.
    #
    # A holdout is spent ONCE. Re-emitting a reading that has already been
    # taken is not a second read — but it IS a different run, so it is stamped
    # with the run it came from rather than presented as current.
    # ⚠ IT HAS TO CHAIN, and the first version did not. Carrying forward only
    # from a block with `read: true` meant the reading survived exactly ONE
    # subsequent run: the second run saw the carried block's `read: false` and
    # redacted it after all. Under 3f's per-commit gate reporting that is two
    # runs, so the bug would have destroyed the record the same evening.
    #
    # A results LIST is the signal, whatever produced it — and the STAMP is
    # inherited, never re-derived, so the record keeps pointing at the run that
    # actually read the holdout rather than drifting forward one commit at a
    # time until it claims to be current.
    carried = carried_from = None
    if not read_holdout and GATE_MANIFEST_PATH.exists():
        try:
            prev = json.loads(GATE_MANIFEST_PATH.read_text(encoding="utf-8"))
            ph = prev.get("holdout") or {}
            if isinstance(ph.get("results"), list):
                carried = ph["results"]
                carried_from = ph.get("results_carried_forward_from") or {
                    "git_sha": prev.get("git_sha"),
                    "generated_at": prev.get("generated_at"),
                    "slug": ph.get("slug"),
                }
        except (OSError, ValueError):
            carried = carried_from = None

    import subprocess
    try:
        sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=config.REPO,
                             capture_output=True, text=True,
                             timeout=30).stdout.strip() or None
        dirty = bool(subprocess.run(["git", "status", "--porcelain"],
                                    cwd=config.REPO, capture_output=True,
                                    text=True, timeout=30).stdout.strip())
    except Exception:                                # noqa: BLE001
        sha, dirty = None, None

    # 🛑 3h A7 — A MANIFEST FROM A DIRTY TREE CARRIES A SHA THAT DOES NOT
    # IDENTIFY THE CODE THAT PRODUCED IT. Both prior manifests shipped
    # `git_working_tree_dirty: true` (3f audit §3.3, 3g audit §7), which
    # undercuts the whole point of stamping the sha: "one commit moved the gate
    # for one reason" was checkable only from the session record, not from the
    # repo. Refused rather than warned, because a committed record with an
    # unverifiable provenance is worse than no record. `dirty is None` (git
    # itself failed) also refuses: an UNKNOWN tree state is not a clean one.
    if dirty is not False and not allow_dirty:
        raise SystemExit(
            f"🛑 REFUSING to write {GATE_MANIFEST_PATH.name}: the working tree "
            f"is {'DIRTY' if dirty else 'in an UNKNOWN git state'}, so git_sha "
            f"{sha[:8] if sha else '?'} would not identify the code that "
            f"produced these numbers. Commit first, or pass --allow-dirty to "
            f"record the mismatch explicitly. (stdout and the markdown report "
            f"above were still produced — only the committed manifest refused)")

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_sha": sha,
        "git_working_tree_dirty": dirty,
        # 3h A7 — recorded so a dirty-tree manifest names itself as one.
        "dirty_tree_write_allowed_by_flag": bool(allow_dirty),
        "realm": season_config.REALM,
        "season": season_config.SEASON,
        "criteria_in_force": {
            "aggregate_tolerance_pct": AGGREGATE_TOLERANCE_PCT,
            "min_within_tolerance": MIN_WITHIN_TOLERANCE,
            "qualified_coverage_pct": QUALIFIED_COVERAGE_PCT,
            "min_qualified": MIN_QUALIFIED,
            "note": "the ±20% pass definition is PHASE_2 §8.2, unchanged; the "
                    "qualified rider was stamped 2026-08-06 before the run it "
                    "judges (predictions/CALIBRATION_TOLERANCE.md addendum)",
            # 🆕 3h A3 — this key was a hardcoded None while the floor was IN
            # FORCE at the within_tolerance site, beside a `result` block whose
            # `coverage_floor_pct_applied` said 20.0 — the exact
            # self-contradiction G8 removed from `scored`, in the adjacent key
            # (AUDIT_3G_ADVERSARIAL §3). The F6 block below now asserts the two
            # agree, so the manifest cannot ship this contradiction again.
            "within_tolerance_coverage_floor_pct": SUCCESSOR_COVERAGE_FLOOR_PCT,
            "floor_applied_from": SUCCESSOR_FLOOR_APPLIED_FROM,
            "within_tolerance_zero_coverage": "reports None, never False (3e A3)",
            "successor_coverage_floor_pct": SUCCESSOR_COVERAGE_FLOOR_PCT,
            "successor_floor_effective_from": SUCCESSOR_FLOOR_EFFECTIVE_FROM,
            # 🛑 3i A2 — the stamped sentence quoted "~62.6%" beside a result
            # block whose own bands read 20.45/16.86/16.86: the stability
            # figure was measured on E13-inflated autos (see the ~62% note at
            # the successor-floor site below) and shipped as if current. The
            # stamped text is kept verbatim (it is an owner decision) and the
            # annotation carries the live bands, GENERATED from this run.
            "successor_floor_justification":
                "slice accuracy is stable at ~62.6% across the >=20/>=30/>=50 "
                "coverage bands and unstable below 20%, so 20% is where the "
                "metric stops being noise — a property of the measurement, not "
                "a level chosen to admit a wanted number. Owner decision "
                "2026-08-06, stamped before this run's result; STRICTER than "
                "what is in force, which is the direction a criterion may move",
            "successor_floor_justification_annotation":
                "3i A2: the ~62.6% in the stamped justification was measured "
                "on E13-inflated autos (pre-3g). This run's bands: "
                + ", ".join(f">={b:g}: {v:.1f}%"
                            for b, v in sorted(slice_bands.items())
                            if v is not None)
                + ". The floor's justification SHAPE (stable above 20%, "
                  "denominator-dominated below) survives; the stable level "
                  "does not. Stamped text kept verbatim above.",
        },
        "result": {
            # 🆕 3g G8 — `scored` IS GONE FROM THIS BLOCK. It shipped here as
            # len(tuning) (36) while `cohort_definition.scored` shipped as
            # len(tuning)+len(holdout) (41), both in the same file, neither
            # noting the other — so an auditor reading `"scored": 36` and
            # `"scored": 41` got exactly the self-contradiction F6 exists to
            # remove, in a different coat. ONE `scored` ships now, in
            # `cohort_definition`, and it means what F6's assertions reconcile:
            # every member the cohort selected, holdout included. This block
            # keeps `tuning_set_size`, which is unambiguous and was always the
            # number this key actually held.
            "tuning_set_size": len(tuning),
            "within_tolerance": len(passing),
            # 🆕 3g G4/G8 — SPLIT. This was one key named
            # `not_scoreable_zero_coverage` counting every `within_tolerance is
            # None`. Once G4's floor landed, that key silently started counting
            # below-floor characters too, and its NAME would have been a lie in
            # the same file that just removed a duplicate `scored`. Two reasons,
            # two keys, and the old name keeps its old meaning.
            "not_scoreable_zero_coverage": sum(
                1 for r in tuning
                if not (r["modelled"] or {}).get("modelled_damage_pct")),
            "not_scoreable_below_coverage_floor": sum(
                1 for r in tuning
                if r["within_tolerance"] is None
                and (r["modelled"] or {}).get("modelled_damage_pct")),
            "coverage_floor_pct_applied": SUCCESSOR_COVERAGE_FLOOR_PCT,
            "qualified": len(qualified),
            "criterion_met": crit_met,
            "rider_met": rider_met,
            "exit_met": bool(crit_met and rider_met),
            # 3e A2 — the floor is IN THE KEY NAME. The old
            # `cohort_median_slice_accuracy_pct` pinned a number two readers
            # would read two ways, because a median of a coverage-denominated
            # ratio is meaningless without the coverage band it was taken over.
            f"median_slice_accuracy_pct_at_coverage_ge_{SLICE_COVERAGE_FLOOR_PCT:g}":
                slice_bands.get(SLICE_COVERAGE_FLOOR_PCT),
            "slice_accuracy_coverage_floor_pct": SLICE_COVERAGE_FLOOR_PCT,
            # 3f F7 — `n` BESIDE EVERY BAND, and the caveat in the artifact
            # rather than only in the generated report. `>=0` is a number this
            # project has retracted; it must not ship bare next to the good one.
            "slice_accuracy_by_coverage_band_pct": {
                f">={b:g}": {"median_pct": v, "n": band_n.get(b, 0),
                             "readable": b >= SLICE_COVERAGE_FLOOR_PCT}
                for b, v in sorted(slice_bands.items())},
            # 3i A2 — this note hardcoded "~164%", the PRE-E13 >=0 band, while
            # the artifact beside it read 40.25. The number is now read from
            # this run's own bands; the caveat's logic is unchanged.
            "slice_accuracy_band_note":
                f"Only bands at or above the {SLICE_COVERAGE_FLOOR_PCT:g}% "
                f"floor are readable as accuracy. Below it the ratio is "
                f"dominated by its own denominator — this run's >=0 band reads "
                + (f"{slice_bands.get(0.0):.1f}%"
                   if slice_bands.get(0.0) is not None else "EMPTY")
                + f" (the same artifact class 3e retracted at ~164%), not a "
                f"finding about over- or under-production.",
            # 🆕 3h B3 — the SAME median over PRODUCING coverage only, BESIDE
            # the existing key, never replacing it (Q2: which number is the
            # headline is a criterion question and belongs in a stamped
            # successor). And the cohort's keyed-but-zero exposure, so the 3g
            # audit's §4 is a measured quantity in the committed artifact.
            f"median_slice_accuracy_pct_producing_only_at_coverage_ge_{SLICE_COVERAGE_FLOOR_PCT:g}": (
                statistics.median(xs) if (xs := [
                    r.get("slice_accuracy_producing_pct") for r in tuning
                    if r.get("slice_accuracy_producing_pct") is not None
                    and (r["modelled"] or {}).get(
                        "modelled_and_producing_pct", 0)
                    >= SLICE_COVERAGE_FLOOR_PCT]) else None),
            "producing_only_n": len([
                r for r in tuning
                if r.get("slice_accuracy_producing_pct") is not None
                and (r["modelled"] or {}).get("modelled_and_producing_pct", 0)
                >= SLICE_COVERAGE_FLOOR_PCT]),
            "keyed_but_zero_pct_median": (
                round(statistics.median(ys), 2) if (ys := [
                    ((r["modelled"] or {}).get("keyed_but_zero_pct") or 0.0)
                    for r in tuning if r["modelled"]]) else None),
            "keyed_but_zero_pct_max": (
                round(max(ys), 2) if (ys := [
                    ((r["modelled"] or {}).get("keyed_but_zero_pct") or 0.0)
                    for r in tuning if r["modelled"]]) else None),
            "per_character_slice_accuracy_policy":
                "ANNOTATED IN PLACE, NOT FLOORED (3f F7). A per-character value "
                "below the coverage floor keeps its raw number and carries a "
                "sibling `slice_accuracy_caveat` saying it is not a "
                "measurement. Flooring would delete the evidence for 3e's own "
                "retraction — Mutaforma's 1,859,400% at 0.2% coverage IS what "
                "'this ratio explodes as coverage -> 0' looks like.",
            "passer_coverage_pct": {
                r["name"]: round(
                    (r["modelled"] or {}).get("modelled_damage_pct") or 0.0, 1)
                for r in passing},
        },
        "corpus_row_counts": corpus,
        "cohort_definition": {
            "source_file": str(COHORT_PATH.relative_to(config.REPO)).replace("\\", "/"),
            "slug": cohort_spec.get("slug"),
            "frozen_at": cohort_spec.get("frozen_at"),
            "frozen_size": len(cohort_ids),
            # 🚨 3f F6 — THE FREEZE HAS TWO EXITS AND ONLY ONE WAS REPORTED.
            # This used to be `len(tuning) + len(holdout)` — the count of
            # SCORED characters — while `dropped` held only the completeness
            # filter's losses. A member lost in the SCORING loop (no preset,
            # unresolvable path, Path of Duality, or ANY sim exception) landed
            # in `excluded`, which never reached `dropped`, never reached this
            # file, and was written only to gitignored data/derived/. So two
            # sim errors produced a committed manifest reading
            # `frozen_size: 41, still_qualifying: 39, dropped: []` — internally
            # contradictory — while stdout still printed "41 of 41" and the
            # headline denominator quietly became 34.
            #
            # This was LIVE during 3e: Block B rewrote three sim modules across
            # five commits and any one raising on one crawled build would have
            # shrunk the denominator invisibly. It happened not to bite.
            #
            # `still_qualifying` is now the completeness filter's answer, and
            # `scored` is what actually reached the tables. The two are equal
            # only when nothing was excluded after selection.
            "still_qualifying": (len(cohort_ids) - len(dropped)
                                 if n_qualifying is None else n_qualifying),
            "scored": len(tuning) + len(holdout),
            "dropped": [{"character_id": cid, "name": nm, "reason": why}
                        for cid, nm, why in dropped],
            "excluded_after_selection": [
                {"character_id": cid, "name": nm, "reason": why}
                for cid, nm, why in excluded],
            "qualifying_but_not_frozen_in": len(outside),
            "note": "FROZEN id set, not ORDER BY character_id LIMIT N. A frozen "
                    "member that stops qualifying is reported as dropped with "
                    "its reason and is never substituted; a cohort that quietly "
                    "shrinks is the sliding-window defect in a different coat. "
                    "TWO exits: `dropped` is the completeness filter, "
                    "`excluded_after_selection` is the scoring loop. "
                    "frozen_size == still_qualifying + len(dropped), and "
                    "still_qualifying == scored + len(excluded_after_selection).",
        },
        "holdout": {
            "slug": HOLDOUT_SLUG,
            "character_ids": list(HOLDOUT_IDS),
            "members_scored": len(holdout),
            "read": bool(read_holdout),
            "note": "split out of the headline in 3e A4. Previously counted in "
                    "'n of 41', so any fix that lifted these five moved the "
                    "headline AND spent the holdout in the same number. `read` "
                    "is whether THIS run read it. A run that did not read it "
                    "carries the previous reading forward under "
                    "`results_carried_forward_from` rather than erasing it, and "
                    "reports REDACTED only when there is no previous reading.",
            "results": (sorted(
                ({"character_id": r["character_id"], "name": r["name"],
                  "delta_pct": round(r["delta_pct"], 2)
                               if r["delta_pct"] is not None else None,
                  "modelled_damage_pct": round(
                      (r["modelled"] or {}).get("modelled_damage_pct") or 0.0, 2),
                  "within_tolerance": r["within_tolerance"]}
                 for r in holdout), key=lambda d: d["character_id"])
                if read_holdout else (carried or "REDACTED — not read in this run")),
            **({} if read_holdout or not carried else {
                "results_carried_forward_from": carried_from,
                "results_carried_forward_note":
                    "🛑 THESE NUMBERS ARE NOT FROM THIS RUN. They were read at "
                    "the run stamped above and are carried forward verbatim "
                    "because this run did not pass --read-holdout. Re-writing "
                    "them as REDACTED would DESTROY a committed result to "
                    "record that it was not re-read, which is a worse trade: a "
                    "holdout is spent once and the record of that reading is "
                    "the thing worth keeping. Compare git_sha above against "
                    "results_carried_forward_from before citing them — if they "
                    "differ, the model may have moved since they were read.",
            }),
        },
        "cohort": sorted(
            ({"character_id": r["character_id"], "name": r["name"],
              "path": r["path"], "boss": r["boss"],
              "delta_pct": round(r["delta_pct"], 2) if r["delta_pct"] is not None else None,
              "modelled_damage_pct": round(
                  (r["modelled"] or {}).get("modelled_damage_pct") or 0.0, 2),
              # 3h B1 — the split, in the committed record. Sums to
              # modelled_damage_pct (up to the two roundings).
              "modelled_and_producing_pct": round(
                  (r["modelled"] or {}).get("modelled_and_producing_pct")
                  or 0.0, 2),
              "keyed_but_zero_pct": round(
                  (r["modelled"] or {}).get("keyed_but_zero_pct") or 0.0, 2),
              "slice_accuracy_pct": round(r["slice_accuracy_pct"], 2)
                                    if r["slice_accuracy_pct"] is not None else None,
              "slice_accuracy_producing_pct": (
                  round(r["slice_accuracy_producing_pct"], 2)
                  if r.get("slice_accuracy_producing_pct") is not None
                  else None),
              # 3f F7 — the annotation travels WITH the number, in the same
              # object, so it cannot be read without it.
              "slice_accuracy_caveat": slice_accuracy_caveat(
                  (r["modelled"] or {}).get("modelled_damage_pct")),
              "within_tolerance": r["within_tolerance"]}
             for r in tuning), key=lambda d: d["character_id"]),
    }
    # 🛑 3f F6 — THE MANIFEST MUST NOT BE ABLE TO CONTRADICT ITSELF. Every
    # frozen member has exactly one fate: it still qualifies or it is dropped;
    # if it qualifies it is either scored or excluded after selection. Asserted
    # rather than trusted, because the defect this replaces was precisely a
    # committed artifact whose own numbers did not add up (`frozen_size: 41,
    # still_qualifying: 39, dropped: []`) with nothing checking them.
    #
    # RAISES rather than warns: a manifest is a committed record, and one that
    # is wrong is worse than one that is missing.
    #
    # ⚠ 3g G8 — WHAT THESE TWO ASSERTIONS ACTUALLY ARE, corrected. `3f`'s record
    # and ENGINE_BUGS described them as *"two assertions REFUSE to write a
    # manifest whose members do not add up"*, which claims a RUNTIME invariant
    # over the data. They are not that. Given `still_qualifying = len(rows)` and
    # `dropped = [cid for cid in cohort_ids if cid not in present]`, the first
    # reduces to `len(rows) + (len(cohort_ids) - len(rows)) == len(cohort_ids)`;
    # and `_completeness_sql` ends `GROUP BY ep.character_id`, so `rows` is one
    # row per character and every row lands in exactly one of `results` /
    # `excluded`, making the second `len(results) + len(excluded) == len(rows)`.
    # **No data condition can trip either.**
    #
    # They ARE real REGRESSION GUARDS ON THE CALLER'S WIRING, which is worth
    # having and is why they stay: reverting `:1087` to `len(tuning)+len(holdout)`
    # turns them red, and `check_refusals.py:310,326` fires both by passing
    # hand-forged counts. The claim is corrected, not the code — describing a
    # wiring guard as a data invariant is the kind of overstatement that makes a
    # later auditor distrust the things that ARE true.
    cd = manifest["cohort_definition"]
    if cd["still_qualifying"] + len(cd["dropped"]) != cd["frozen_size"]:
        raise SystemExit(
            f"🛑 GATE MANIFEST IS INTERNALLY INCONSISTENT and was NOT written: "
            f"still_qualifying {cd['still_qualifying']} + dropped "
            f"{len(cd['dropped'])} != frozen_size {cd['frozen_size']}. Every "
            f"frozen member must have exactly one fate.")
    if cd["scored"] + len(cd["excluded_after_selection"]) != cd["still_qualifying"]:
        raise SystemExit(
            f"🛑 GATE MANIFEST IS INTERNALLY INCONSISTENT and was NOT written: "
            f"scored {cd['scored']} + excluded_after_selection "
            f"{len(cd['excluded_after_selection'])} != still_qualifying "
            f"{cd['still_qualifying']}. A member lost in the scoring loop must "
            f"be named, not silently removed from the denominator.")
    # 🆕 3h A3 — the assertion F6 is NAMED for and did not make: the criteria
    # the manifest CLAIMS were in force must be the criteria the result was
    # COMPUTED under. The 3g audit found `criteria_in_force` shipping a None
    # floor beside a `result` floor of 20.0 — a manifest contradicting itself
    # about which rules produced its own numbers, which the two wiring guards
    # above are structurally blind to. Red mutation: revert the
    # `within_tolerance_coverage_floor_pct` key to None.
    ci = manifest["criteria_in_force"]
    if ci["within_tolerance_coverage_floor_pct"] != \
            manifest["result"]["coverage_floor_pct_applied"]:
        raise SystemExit(
            f"🛑 GATE MANIFEST IS INTERNALLY INCONSISTENT and was NOT written: "
            f"criteria_in_force.within_tolerance_coverage_floor_pct "
            f"{ci['within_tolerance_coverage_floor_pct']} != "
            f"result.coverage_floor_pct_applied "
            f"{manifest['result']['coverage_floor_pct_applied']}. The criteria "
            f"block must describe the criteria that produced the result.")

    GATE_MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    GATE_MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
    print(f"[manifest] {GATE_MANIFEST_PATH} "
          f"(tuning set of {len(tuning)}, {len(holdout)} holdout "
          f"{'READ' if read_holdout else 'redacted'}, "
          f"git {sha[:8] if sha else '?'}"
          f"{', DIRTY tree' if dirty else ''})")


if __name__ == "__main__":
    sys.exit(main())
