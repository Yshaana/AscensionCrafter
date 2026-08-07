"""parse_admissibility.py — the APM ratio, implemented (3h D1), and the D4
admissibility predicates computed BLIND over the frozen cohort.

    py tools/audit/parse_admissibility.py

`3c` retracted `Boomcat` as "the best clean-qualifier candidate" on an APM
ratio of 0.24 — computed chat-side. `grep -rn "apm"` returned nothing: the
whole retraction rested on a number with no implementation. This file is the
implementation.

🛑 THE RATIO IS ONLY VALID ON INSTANT-HEAVY KITS, and returns None — not a
number — outside that regime. `ability_performance.casts` under-counts
cast-time casters (`SPELL_CAST_SUCCESS` and `SPELL_CAST_START` are disjoint by
cast type — 3e preflight thread 1), and 22 of the 41 cohort boards are
cast-time casters. A bare APM ratio across the cohort would be exactly the
kind of number this project retracts.

🛑 THE D4 COMPUTATION IS BLIND: every predicate is a property of the PARSE
(action rate, window length, phase resolution, snapshot lag) and the per-
character table is computed and printed before any delta or verdict is read.
The falsifiability comparison at the end reads the committed manifest's
verdicts — AFTER the blind table — because "does the rule remove a FAILING
character" cannot be answered without them. Nothing here writes anything:
this tool stamps nothing and applies nothing (D4 is an owner decision).

⚠ E15 interplay: casts are summed over `is_pet = 0` rows only. Pet rows
duplicate owner rows for 15,551 groups (ENGINE_BUGS E15), and a pet's casts
are not the player's actions in any case.
"""
import json
import sqlite3
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import config  # noqa: E402
from config import BUILDS_DB_PATH, DB_PATH  # noqa: E402

import calibrate_crawled as cc  # noqa: E402
from core.db.connection import connect  # noqa: E402

config.ensure_utf8_stdout()

# The regime bound, stated: a board with 3+ cast-time combat entries is a
# cast-time caster (the 3e-preflight classifier), and `casts` is structurally
# blind to its main buttons. Below 3, the kit is instant-heavy and casts/min
# is a faithful action rate.
MAX_CAST_TIME_ENTRIES = 2

# Death-deflation signature, stated before the cohort table was computed
# (prereg_3h_boomcat.md P9): this parse's action rate at or below HALF the
# character's own typical rate.
APM_RATIO_BOUND = 0.5

# Parse-window floor: the analyze-capture rule flags conclusions from under
# ~60s of data as provisional; a scored parse below it is a data-quality
# exclusion candidate, not a modelling input.
MIN_PARSE_SECONDS = 60.0

# Effect types excluded from the cast-time count (mechanical, not name-based):
# 28 = SPELL_EFFECT_SUMMON, 24 = SPELL_EFFECT_CREATE_ITEM (conjures).
_NON_COMBAT_EFFECTS = {24, 28}


def cast_time_entries(asc, bdb, snapshot_id):
    """How many of this board's resolved entries are cast-time combat spells.

    Resolution: snapshot_cards.spell_id -> spell_dbc_raw.casting_time_index ->
    dbc_spellcasttimes.base (ms). base > 0 = cast-time. Summons and conjures
    are excluded by effect type, never by name.
    """
    rows = bdb.execute(
        "SELECT DISTINCT spell_id FROM snapshot_cards "
        "WHERE snapshot_id = ? AND spell_id IS NOT NULL",
        (snapshot_id,)).fetchall()
    n_cast, n_resolved = 0, 0
    for (sid,) in rows:
        r = asc.execute(
            "SELECT r.casting_time_index, r.effect_json "
            "FROM spell_dbc_raw r WHERE r.id = ?", (sid,)).fetchone()
        if r is None:
            continue
        n_resolved += 1
        cti, effect_json = r
        if not cti:
            continue
        base = asc.execute(
            "SELECT base FROM dbc_spellcasttimes WHERE id = ?",
            (cti,)).fetchone()
        if not base or not base[0] or base[0] <= 0:
            continue
        try:
            effects = json.loads(effect_json or "{}").get("Effect") or []
        except ValueError:
            effects = []
        if any(e in _NON_COMBAT_EFFECTS for e in effects):
            continue
        n_cast += 1
    return {"cast_time_entries": n_cast, "resolved_entries": n_resolved,
            "fraction": (n_cast / n_resolved) if n_resolved else None}


def scope_duration_seconds(bdb, scope_id):
    """Wall-clock seconds behind one capture scope (single or grouped)."""
    row = bdb.execute(
        "SELECT encounter_id, encounter_ids_json FROM capture_scopes "
        "WHERE scope_id = ?", (scope_id,)).fetchone()
    if row is None:
        return None
    enc_id, ids_json = row
    ids = [enc_id] if enc_id is not None else []
    if not ids and ids_json:
        try:
            ids = list(json.loads(ids_json) or [])
        except ValueError:
            ids = []
    if not ids:
        return None
    q = ",".join("?" * len(ids))
    tot = bdb.execute(
        f"SELECT SUM(duration_seconds) FROM encounters "
        f"WHERE encounter_id IN ({q})", ids).fetchone()[0]
    return tot


def scope_apm(bdb, character_id, scope_id):
    """This character's casts per minute over one scope. is_pet = 0 only."""
    dur = scope_duration_seconds(bdb, scope_id)
    if not dur:
        return None
    casts = bdb.execute(
        "SELECT SUM(casts) FROM ability_performance "
        "WHERE scope_id = ? AND character_id = ? AND is_pet = 0",
        (scope_id, character_id)).fetchone()[0]
    if casts is None:
        return None
    return 60.0 * casts / dur


def apm_ratio(bdb, character_id, scope_id, *, n_cast_time_entries):
    """This scope's APM over the median of the character's OTHER scopes.

    Returns a dict whose `ratio` is None — never a number — when the kit is
    outside the instant-heavy regime or fewer than 2 other scopes exist to
    define "typical".
    """
    out = {"scope_apm": scope_apm(bdb, character_id, scope_id),
           "n_cast_time_entries": n_cast_time_entries,
           "in_regime": n_cast_time_entries <= MAX_CAST_TIME_ENTRIES,
           "other_scope_apms": [], "ratio": None, "reason": None}
    if not out["in_regime"]:
        out["reason"] = (f"{n_cast_time_entries} cast-time combat entries > "
                         f"{MAX_CAST_TIME_ENTRIES} — casts under-counts this "
                         f"kit, ratio refused")
        return out
    if out["scope_apm"] is None:
        out["reason"] = "no casts or no duration for this scope"
        return out
    others = [s for (s,) in bdb.execute(
        "SELECT DISTINCT scope_id FROM ability_performance "
        "WHERE character_id = ? AND scope_id != ? AND is_pet = 0",
        (character_id, scope_id)).fetchall()]
    apms = [a for s in others if (a := scope_apm(bdb, character_id, s))]
    out["other_scope_apms"] = sorted(round(a, 1) for a in apms)
    if len(apms) < 2:
        out["reason"] = (f"only {len(apms)} other scope(s) with an APM — no "
                         f"'typical rate' to compare against, ratio refused")
        return out
    out["ratio"] = out["scope_apm"] / statistics.median(apms)
    return out


def main():
    if not BUILDS_DB_PATH.exists():
        print(f"{BUILDS_DB_PATH} missing — run ingest/logs_gg/build_builds_db.py")
        return 1
    bdb = sqlite3.connect(BUILDS_DB_PATH)
    asc = connect(DB_PATH)

    cohort_ids, _spec = cc.load_frozen_cohort(cc.COHORT_PATH)
    cands, dropped, _outside = cc.candidates(bdb, cohort_ids, 0.0)

    # ---- the BLIND table: parse properties only, no delta touched ---------
    print(f"[blind] predicates over all {len(cohort_ids)} frozen members "
          f"(tuning AND holdout — the rule must apply identically), computed "
          f"before any delta or verdict is read:")
    print(f"[blind] predicate 1: APM ratio <= {APM_RATIO_BOUND:g} inside the "
          f"instant-heavy regime (<= {MAX_CAST_TIME_ENTRIES} cast-time "
          f"combat entries)")
    print(f"[blind] predicate 2: deaths > 0 — encounter_performance.deaths is "
          f"ALL NULL today (declared, never written), so this predicate "
          f"removes nobody until D2 lands data")
    print(f"[blind] predicate 3: parse window < {MIN_PARSE_SECONDS:g}s")
    print(f"[blind] predicate 4: capture resolves to no phase — every corpus "
          f"capture predates the 2026-08-08 boundary, so this removes nobody "
          f"today (G0 arms at the boundary)")
    print(f"[blind] predicate 5: snapshot lag > 0h — the gate already "
          f"enforces lag 0 at selection, so this removes nobody by "
          f"construction\n")

    seen = set()
    table = []
    for cand in cands:
        (cid, cname, snapshot_id, _dps, _path, _boss, _ctype, dur, _enc,
         lag, _lvl, scope_id, _lg) = cand
        if cid in seen:
            continue
        seen.add(cid)
        ct = cast_time_entries(asc, bdb, snapshot_id)
        ar = apm_ratio(bdb, cid, scope_id,
                       n_cast_time_entries=ct["cast_time_entries"])
        deaths = bdb.execute(
            "SELECT MAX(deaths) FROM encounter_performance "
            "WHERE character_id = ? AND scope_id = ?",
            (cid, scope_id)).fetchone()[0]
        flags = []
        if ar["ratio"] is not None and ar["ratio"] <= APM_RATIO_BOUND:
            flags.append(f"apm_ratio {ar['ratio']:.2f} <= {APM_RATIO_BOUND:g}")
        if deaths and deaths > 0:
            flags.append(f"deaths {deaths}")
        if dur is not None and dur < MIN_PARSE_SECONDS:
            flags.append(f"window {dur:.0f}s < {MIN_PARSE_SECONDS:g}s")
        table.append({
            "character_id": cid, "name": cname,
            "holdout": cid in cc.HOLDOUT_IDS,
            "window_s": dur, "snapshot_lag_h": lag,
            "cast_time_entries": ct["cast_time_entries"],
            "resolved_entries": ct["resolved_entries"],
            "apm": ar["scope_apm"], "apm_ratio": ar["ratio"],
            "apm_reason": ar["reason"],
            "n_other_scopes": len(ar["other_scope_apms"]),
            "deaths": deaths,
            "not_admissible": bool(flags), "flags": flags,
        })
        rat = f"{ar['ratio']:.2f}" if ar["ratio"] is not None else "None"
        print(f"  {cname:>14} ({cid}): window {dur:6.1f}s, "
              f"cast-time entries {ct['cast_time_entries']:2d}, "
              f"APM {ar['scope_apm'] and round(ar['scope_apm'], 1)!s:>6}, "
              f"ratio {rat:>5} "
              f"({'REGIME' if ar['in_regime'] else 'refused'}"
              + (f", n_others={len(ar['other_scope_apms'])}" if ar["in_regime"] else "")
              + ")"
              + (f"  🛑 NOT ADMISSIBLE: {'; '.join(flags)}" if flags else ""))

    flagged = [t for t in table if t["not_admissible"]]
    print(f"\n[blind] cohort effect: {len(flagged)} of {len(table)} members "
          f"flagged NOT ADMISSIBLE (None, never False): "
          + (", ".join(t["name"] for t in flagged) if flagged else "none"))

    # ---- falsifiability — reads the committed manifest's verdicts, AFTER --
    print("\n[falsifiability] comparing against the committed manifest's "
          "verdicts (read only now, after the blind table above):")
    manifest = json.loads(
        cc.GATE_MANIFEST_PATH.read_text(encoding="utf-8"))
    verdicts = {r["character_id"]: r["within_tolerance"]
                for r in manifest.get("cohort", [])}
    removes_fail = [t for t in flagged
                    if verdicts.get(t["character_id"]) is False]
    removes_pass = [t for t in flagged
                    if verdicts.get(t["character_id"]) is True]
    removes_none = [t for t in flagged
                    if verdicts.get(t["character_id"]) is None]
    print(f"  removes FAILING characters: {len(removes_fail)} "
          f"({', '.join(t['name'] for t in removes_fail) or '-'})")
    print(f"  removes PASSING characters: {len(removes_pass)} "
          f"({', '.join(t['name'] for t in removes_pass) or '-'})")
    print(f"  removes NOT-SCOREABLE characters: {len(removes_none)} "
          f"({', '.join(t['name'] for t in removes_none) or '-'})")
    if removes_fail:
        print("  -> the rule is CAPABLE of removing a failing character "
              "(the D4 falsifiability bar).")
    elif flagged and not removes_fail:
        print("  🛑 the rule removes NO failing character — under D4 that is "
              "the fitting asymmetry: DO NOT STAMP; report and stop.")
    else:
        print("  -> the rule removes nobody at all on today's corpus.")
    print("\n[stamp] NOTHING STAMPED, NOTHING APPLIED — D4 is an owner "
          "decision; this tool only measures.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
