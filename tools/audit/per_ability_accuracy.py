"""per_ability_accuracy.py — the DIRECT per-ability comparison (3h Block C).

    py tools/audit/per_ability_accuracy.py [--char <id> ...]

Slice accuracy is `(100 + delta) / coverage` — a whole-character DPS delta over
a whole-character coverage share. It is a ratio of two aggregates and it
inherits every assumption in both. This tool replaces the inference with the
measurement both sides of which were already in hand: for every scored
character x every ability, `res.per_ability[sid]["damage"]` against
`ability_performance.damage_total`, joined on spell id — the same join
`modelled_damage_share` performs — plus the abilities the sim has NO key for,
because the set the sim never reached is as informative as the set it got
wrong.

🛑 A NEW TOOL, not a flag on calibrate_crawled.py (SESSION_3H_PRIMER Q1):
that file is ~1,700 lines and carries the gate; the measurement stays out of
the thing being measured. It REUSES the gate's own selection and sim path by
import, so the population and the builds are identical by construction.

🛑 THIS TOOL MOVES NO GATE. It never touches predictions/gate_manifest*.json.
Full rows land in data/derived/ (gitignored); 🆕 3i C7 — the SUMMARY
statistics additionally land in predictions/per_ability_summary.json, a small
COMMITTED artifact, because 3h's headline result lived only in gitignored
files and was the one number a monitoring chat could not check (AUDIT_3H §2).
Same dirty-tree discipline as the gate manifest: the committed artifact is
refused when the working tree is dirty.

Units: the sim's per-ability damage is a total over `content.fight_duration`;
the log's is a total over the encounter's `duration_seconds`. The ratio is
therefore taken over RATES:

    ratio = (sim_damage / sim_fight_s) / (logged_damage / encounter_s)

Pre-registration: predictions/prereg_3h_per_ability.md, committed BEFORE this
tool's first run.

🆕 3i Block C — the logged side is repaired: one policy for duplicated rows
(is_pet = 0 at the query, per E15's rows[]-canonical decision; residual
same-spell_id duplicates MERGED deterministically and named), the per-row
shares are asserted to sum to 100 ± ε per character (C2, mutation M32), and
the phantom-production cell (producing sim keys the log has no row for) is
reported (C4). Re-run prereg: SESSION_3I_PRIMER.md Block C6 (committed before
this run) — the absent share is predicted to move UP, the producing-ratio
median to move little.

key_state vocabulary (the work order's, plus one measured addition):
  producing            the key produced sim damage > 0
  refused:<reason>     every event refused (E14-family reasons, from the
                       refusal site's own wording)
  unresolved           no damage event resolves (ability_model.py:735-742)
  starved:zero-casts   mean > 0 but the GCD allocation gave it zero casts —
                       Block B measured ALL 90 cohort zero-keys in this state,
                       so it is named rather than folded into "refused"
  absent               the sim has no key at all (sim_damage = 0 by
                       construction)
"""
import argparse
import json
import statistics
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import config  # noqa: E402
from config import BUILDS_DB_PATH, DATA_DERIVED, DB_PATH  # noqa: E402

import calibrate_crawled as cc  # noqa: E402 — the gate's own selection + sim
import sqlite3  # noqa: E402

from core.builds.group_buffs import derive_buffs  # noqa: E402
from core.builds.stats import compute_stats  # noqa: E402
from core.db.connection import connect  # noqa: E402
from core.sim import combat_engine as ce  # noqa: E402
from core.sim.apl_gen import generate_apl  # noqa: E402
from core.sim.content import get_preset  # noqa: E402
from core.sim.tiers import fast_sim  # noqa: E402

config.ensure_utf8_stdout()

JSON_PATH = DATA_DERIVED / "per_ability_accuracy.json"
MD_PATH = DATA_DERIVED / "per_ability_accuracy.md"
SUMMARY_PATH = (Path(__file__).resolve().parents[2] / "predictions"
                / "per_ability_summary.json")

# C4 — the round numbers and orders of magnitude a unit error looks like.
# E13 was exactly 100; E14 was exactly card_duration / component_tick. Integers
# 2..30 cover tick counts, target counts and rank multipliers.
ROUND_CONSTANTS = [0.01, 0.1, 0.2, 0.25, 0.33, 0.5, 2.0, 3.0, 4.0, 5.0,
                   10.0, 100.0] + [float(n) for n in range(6, 31)]
ROUND_TOLERANCE = 0.02          # within 2%, relative

HIST_EDGES = [0.0, 0.05, 0.1, 0.2, 0.3, 0.5, 0.8, 1.25, 2.0, 5.0, 10.0]


def key_state_for(entry):
    """Map a sim per-ability entry to the key_state vocabulary above."""
    if (entry.get("damage") or 0.0) > 0.0:
        return "producing"
    why = cc._keyed_zero_reason(entry)
    if why == "no-damage-event-resolves":
        return "unresolved"
    if "zero-casts-allocated" in why:
        return "starved:zero-casts"
    if why.startswith("refused-"):
        return "refused:" + why[len("refused-"):]
    return "zero:" + why


def round_flag(ratio):
    """C4 — return the constant this ratio is within 2% of, or None."""
    if ratio is None or ratio <= 0:
        return None
    for c in ROUND_CONSTANTS:
        if abs(ratio - c) / c <= ROUND_TOLERANCE:
            return c
    return None


def hist_bucket(ratio):
    if ratio == 0.0:
        return "= 0"
    for lo, hi in zip(HIST_EDGES, HIST_EDGES[1:]):
        if lo < ratio <= hi:
            return f"({lo:g}, {hi:g}]"
    return f"> {HIST_EDGES[-1]:g}"


def per_key_table(paired, total_logged_all):
    """Ranked per-key table: one row per (spell_id, key_state) over the cohort.

    3l B0 (`AUDIT_3K` §3.2): every target-pick and every audit reads exactly
    this table, and until now it existed only as pasted tool output with no
    committed source — the `3k` prereg's target list could not be re-derived
    from the tree. One row per (spell_id, state) because key_state is
    PER-CHARACTER: the same spell can be producing for one member and absent
    for another, and collapsing that to one row would average two mechanisms
    (the `3b` per-effect-slot lesson, one level up).

    Built from PAIRED rows only (logged > 0): `characters` means characters
    that LOG the key, which is what every quoted count has meant (RV "9
    characters", Devour Mind "2"). Sim-only keys are the `phantom` block's
    business — mixing them in would count characters that never logged the
    ability.

    `median_producing_ratio` is the median of per-character rate ratios where
    producing, same semantics as the headline `producing.median_ratio`.
    """
    groups = {}
    for r in paired:
        g = groups.setdefault((r["spell_id"], r["key_state"]), {
            "spell_id": r["spell_id"], "name": str(r["spell_name"]),
            "state": r["key_state"], "logged": 0.0,
            "chars": set(), "ratios": []})
        g["logged"] += r["logged_damage"]
        g["chars"].add(r["character_id"])
        if r["key_state"] == "producing" and r["ratio"] is not None:
            g["ratios"].append(r["ratio"])
    out = []
    for g in groups.values():
        out.append({
            "spell_id": g["spell_id"], "name": g["name"], "state": g["state"],
            "share_of_cohort_logged_pct": round(
                100.0 * g["logged"] / total_logged_all, 3),
            "characters": len(g["chars"]),
            "median_producing_ratio": (round(statistics.median(g["ratios"]), 4)
                                       if g["ratios"] else None),
        })
    out.sort(key=lambda row: (-row["share_of_cohort_logged_pct"],
                              str(row["spell_id"])))
    return out


def rows_for_character(bdb, asc, conv, cand):
    """Every paired ability row for one candidate tuple from cc.candidates().

    Returns (rows, note) — note is a skip reason when the character cannot be
    simmed, mirroring the gate's own exclusions so the populations match.
    """
    (cid, cname, snapshot_id, dps, path, boss, ctype, dur, enc_id,
     lag, level, scope_id, _longest) = cand
    preset = cc.CONTENT_PRESET.get(ctype)
    if preset is None:
        return None, f"content_type {ctype!r} has no sim preset"
    content = get_preset(preset)
    token = cc.PATH_TOKEN.get((path or "").lower())
    if token is None:
        return None, f"path {path!r} not resolvable"
    if token == "Duality":
        return None, "Path of Duality (2d bug advisory)"
    buff_keys, _prov = derive_buffs(bdb, scope_id, cid, snapshot_id)
    try:
        spec = cc.build_spec_for(bdb, snapshot_id, token)
        cs = compute_stats(spec, content, conv, conn=asc)
        apl = generate_apl(asc, spec, content, cs)
        res = fast_sim(asc, spec, content, cs, apl=apl)
        if buff_keys:
            spec.raid_buffs = buff_keys
            cs = compute_stats(spec, content, conv, conn=asc)
            res = fast_sim(asc, spec, content, cs, apl=apl)
    except Exception as e:                          # noqa: BLE001 — reported
        return None, f"sim error: {type(e).__name__}: {e}"

    sim_fight_s = content.fight_duration or 1.0
    per_ability = res.per_ability or {}

    # 🛑 3i C1 — is_pet = 0 ONLY: the rows[]-canonical policy (E15). Before
    # this, the same duplicated rows were handled FOUR ways inside this
    # function (summed at total_logged, last-wins-dropped in logged_by_sid,
    # accumulated in auto_logged, kept as rows in other_negative), so the
    # numerator and denominator disagreed and the per-row shares did not sum
    # to 100 (AUDIT_3H §4.2). On the post-B corpus the filter is a no-op —
    # 0 is_pet=1 rows exist — and the C2 assertion below makes any recurrence
    # loud instead of silent.
    logged = bdb.execute(
        "SELECT spell_id, spell_name, damage_total, is_pet, spell_school "
        "FROM ability_performance "
        "WHERE scope_id = ? AND character_id = ? AND damage_total > 0 "
        "AND is_pet = 0",
        (scope_id, cid)).fetchall()
    total_logged = sum(r[2] for r in logged)
    if not total_logged or not dur:
        return None, "no logged damage or no encounter duration"

    has_autos = any(k in per_ability for k in ("auto_mh", "auto_oh"))

    def is_auto_row(r):
        """cc.modelled_damage_share's negative-id discriminator, verbatim."""
        if r[0] >= 0 or not has_autos:
            return False
        name = r[1] or ""
        if "[" not in name:
            return True
        tag = name[name.index("[") + 1:].rstrip("]").strip()
        return tag.lower() == (r[4] or "").lower()

    out = []

    def emit(spell_id, name, sim_damage, logged_damage, entry, is_pet=False):
        sim_rate = sim_damage / sim_fight_s
        logged_rate = logged_damage / dur
        ratio = (sim_rate / logged_rate) if logged_rate > 0 else None
        state = key_state_for(entry) if entry is not None else "absent"
        out.append({
            "character_id": cid, "character_name": cname,
            "spell_id": spell_id, "spell_name": name,
            "sim_damage": round(sim_damage, 1),
            "logged_damage": round(logged_damage, 1),
            "sim_rate": round(sim_rate, 3), "logged_rate": round(logged_rate, 3),
            "ratio": round(ratio, 4) if ratio is not None else None,
            "coverage_share_of_logged": round(
                100.0 * logged_damage / total_logged, 2),
            "key_state": state,
            "attributed": bool(entry.get("attributed")) if entry else None,
            "event_kinds": (sorted({e.get("kind") for e in
                                    (entry.get("events") or [])})
                            if entry else []),
            "is_pet": bool(is_pet),
            "round_flag": round_flag(ratio),
        })

    # 🛑 3i C3 — `logged_by_sid[r[0]] = r` was last-wins with no ORDER BY:
    # for a duplicated spell_id, WHICH copy survived was up to SQLite's row
    # order, so two runs against the same database could differ. Duplicates
    # are now MERGED deterministically (damage summed, names joined) and the
    # merge is counted and printed — named, never silently picked.
    logged_by_sid = {}
    merged_sids = []
    auto_logged = 0.0
    other_negative = []                 # extra-attack procs etc. — absent keys
    for r in logged:
        if is_auto_row(r):
            auto_logged += r[2]
        elif r[0] < 0:
            other_negative.append(r)
        elif r[0] in logged_by_sid:
            prev = logged_by_sid[r[0]]
            names = sorted({prev[1] or "", r[1] or ""} - {""})
            logged_by_sid[r[0]] = (r[0], " + ".join(names),
                                   prev[2] + r[2], prev[3] or r[3], prev[4])
            merged_sids.append(r[0])
        else:
            logged_by_sid[r[0]] = r
    if merged_sids:
        print(f"[merged] {cname} ({cid}): {len(merged_sids)} duplicated "
              f"spell_id group(s) merged deterministically: "
              f"{sorted(set(merged_sids))}")

    # 1. every sim key, paired to its logged row (0.0 when the log has none)
    for sid, entry in per_ability.items():
        if sid in ("auto_mh", "auto_oh"):
            continue                    # handled as one paired row below
        lr = logged_by_sid.pop(sid, None)
        emit(sid, entry.get("name") or (lr[1] if lr else str(sid)),
             entry.get("damage") or 0.0, lr[2] if lr else 0.0, entry)

    # 2. the auto pair, sim MH+OH against the matched negative-id swing rows
    if has_autos:
        auto_sim = sum((per_ability.get(k) or {}).get("damage") or 0.0
                       for k in ("auto_mh", "auto_oh"))
        auto_entry = {"damage": auto_sim,
                      "events": [{"kind": "swing"}], "attributed": True,
                      "casts": 1.0, "mean_per_cast": auto_sim,
                      "unresolved_events": []}
        emit("auto", "Auto attacks (MH+OH vs negative-id swings)",
             auto_sim, auto_logged, auto_entry)
    elif auto_logged:
        emit("auto", "Auto attacks (negative-id swings, sim has no swing keys)",
             0.0, auto_logged, None)

    # 3. 🛑 the ABSENT set — logged abilities the sim never reached. Excluding
    # these is how coverage came to mean two things.
    for sid, r in logged_by_sid.items():
        emit(sid, r[1], 0.0, r[2], None, is_pet=r[3])
    for r in other_negative:
        emit(r[0], r[1], 0.0, r[2], None, is_pet=r[3])

    # 🛑 3i C2 — THE INVARIANT THE 3h AUDIT FOUND VIOLATED, now asserted:
    # every logged row lands in exactly one emitted row, so the per-row
    # coverage_share_of_logged values MUST sum to 100 ± ε per character.
    # Before C1/C3 they did not, for any character with a duplicated ability,
    # and nothing noticed. A violation is a defect in THIS TOOL — crash loud,
    # never skip quietly. Registered mutation M32 (RUN 2026-08-07): scale
    # total_logged by 1.01 — every character's shares sum to ~99 and this
    # raises (verified: Boomcat, 99.02). Green path: the C1/C3 single-policy
    # accounting above, which IS the fix.
    share_sum = sum(r["coverage_share_of_logged"] for r in out)
    if abs(share_sum - 100.0) > 0.5:
        raise AssertionError(
            f"C2 invariant violated for {cname} ({cid}): per-row "
            f"coverage_share_of_logged sums to {share_sum:.2f}, not 100 — "
            f"the numerator and denominator of the logged side disagree "
            f"(the AUDIT_3H §4.2 defect class). Refusing to report numbers "
            f"from an inconsistent accounting.")

    return out, None


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--char", type=int, action="append",
                    help="restrict to these character ids (repeatable). "
                         "Default: the whole frozen TUNING set. The holdout "
                         "is NEVER included, with or without this flag")
    ap.add_argument("--max-lag-hours", type=float, default=0.0)
    args = ap.parse_args()

    if not BUILDS_DB_PATH.exists():
        print(f"{BUILDS_DB_PATH} missing — run ingest/logs_gg/build_builds_db.py")
        return 1
    bdb = sqlite3.connect(BUILDS_DB_PATH)
    asc = connect(DB_PATH)
    conv = ce.load_rating_conversions(asc, level=60)

    cohort_ids, cohort_spec = cc.load_frozen_cohort(cc.COHORT_PATH)
    cands, dropped, _outside = cc.candidates(bdb, cohort_ids,
                                             args.max_lag_hours)
    # 🛑 E3 — the holdout is not read by this tool, ever. Per-ability rows for
    # holdout members would BE a read.
    cands = [c for c in cands if c[0] not in cc.HOLDOUT_IDS]
    if args.char:
        want = set(args.char)
        skipped_by_filter = [c[0] for c in cands if c[0] not in want]
        cands = [c for c in cands if c[0] in want]
        print(f"[filter] --char restricted to {sorted(want)}; "
              f"{len(skipped_by_filter)} tuning members skipped by the flag "
              f"(stated, not silent)")

    all_rows, skipped, seen = [], [], set()
    for cand in cands:
        if cand[0] in seen:
            continue                    # one encounter per character
        seen.add(cand[0])
        rows, note = rows_for_character(bdb, asc, conv, cand)
        if rows is None:
            skipped.append((cand[0], cand[1], note))
            continue
        all_rows.extend(rows)

    print(f"[population] {len(seen) - len(skipped)} characters paired "
          f"({len(skipped)} skipped, mirroring the gate's own exclusions), "
          f"{len(all_rows)} ability rows")
    for cid, cname, note in skipped:
        print(f"[skipped] {cname} ({cid}): {note}")

    paired = [r for r in all_rows if r["logged_damage"] > 0]
    keyed = [r for r in paired if r["key_state"] != "absent"]
    absent = [r for r in paired if r["key_state"] == "absent"]

    # ---- the distribution, reported as a distribution (C3) ----------------
    print("\n[histogram] ratio over PAIRED KEYED abilities "
          "(sim key exists AND logged damage > 0):")
    hist = Counter(hist_bucket(r["ratio"] if r["ratio"] is not None else 0.0)
                   for r in keyed)
    order = ["= 0"] + [f"({lo:g}, {hi:g}]" for lo, hi in
                       zip(HIST_EDGES, HIST_EDGES[1:])] + [f"> {HIST_EDGES[-1]:g}"]
    for b in order:
        n = hist.get(b, 0)
        if n or b == "= 0":
            print(f"  {b:>12}: {'#' * min(n, 60)} {n}")

    print("\n[key_state] paired rows by state "
          "(logged-damage-weighted share of cohort logged damage):")
    total_logged_all = sum(r["logged_damage"] for r in paired) or 1.0
    for state, n in Counter(r["key_state"] for r in paired).most_common():
        share = 100.0 * sum(r["logged_damage"] for r in paired
                            if r["key_state"] == state) / total_logged_all
        print(f"  {state:>22}: {n:4d} rows, {share:5.1f}% of logged damage")

    prod = [r["ratio"] for r in keyed
            if r["key_state"] == "producing" and r["ratio"] is not None]
    if prod:
        qs = statistics.quantiles(prod, n=4) if len(prod) >= 4 else []
        near1 = sum(1 for x in prod if 0.8 <= x <= 1.25)
        print(f"\n[producing] n={len(prod)}, median "
              f"{statistics.median(prod):.3f}"
              + (f", quartiles {qs[0]:.3f}/{qs[2]:.3f}" if qs else "")
              + f", in [0.8, 1.25]: {near1} ({100 * near1 / len(prod):.0f}%)")
    zero_paired = sum(1 for r in keyed
                      if (r["ratio"] or 0.0) == 0.0)
    print(f"[zeros] paired keyed abilities at exactly 0: {zero_paired} of "
          f"{len(keyed)} ({100 * zero_paired / len(keyed):.0f}%)"
          if keyed else "[zeros] no paired keyed abilities")
    absent_share = 100.0 * sum(r["logged_damage"] for r in absent) / total_logged_all
    print(f"[absent] {len(absent)} paired rows with NO sim key, carrying "
          f"{absent_share:.1f}% of cohort logged damage")

    # 🛑 3i C4 — the fourth cell of the 2×2, measured and never reported
    # until now (AUDIT_3H §7.2): sim keys the LOG has no row for. Sim damage
    # landing on abilities the character never used inflates the aggregate
    # delta while earning zero coverage credit — a mechanism that makes the
    # aggregate look better than the per-ability truth. The rows were always
    # in the JSON; this is the statistic that covers them.
    phantom = [r for r in all_rows
               if r["logged_damage"] == 0 and r["key_state"] == "producing"]
    total_sim_all = sum(r["sim_damage"] for r in all_rows) or 1.0
    phantom_sim = sum(r["sim_damage"] for r in phantom)
    print(f"[phantom] {len(phantom)} producing sim keys with NO logged row — "
          f"{100.0 * phantom_sim / total_sim_all:.1f}% of cohort sim damage "
          f"lands on abilities the log never saw "
          f"({sum(1 for r in all_rows if r['logged_damage'] == 0)} sim-only "
          f"rows in all, incl. non-producing)")

    # ---- C4 — the unit-error hunt -----------------------------------------
    flagged = [r for r in paired if r["round_flag"] is not None
               and r["coverage_share_of_logged"] >= 1.0]
    print(f"\n[round] {len(flagged)} paired rows within {ROUND_TOLERANCE:.0%} "
          f"of a round constant AND carrying ≥1% of their owner's logged "
          f"damage (every one listed — no caps):")
    for r in sorted(flagged, key=lambda r: -r["coverage_share_of_logged"]):
        print(f"  {r['character_name']:>12} {str(r['spell_name'])[:32]:32} "
              f"({r['spell_id']}) ratio {r['ratio']:.4f} ~ "
              f"{r['round_flag']:g} [{r['key_state']}] "
              f"{r['coverage_share_of_logged']:.1f}% of logged")

    # ---- per-character view, five highest-coverage members (C3) -----------
    by_char = {}
    for r in paired:
        by_char.setdefault((r["character_id"], r["character_name"]),
                           []).append(r)
    cov_rank = sorted(
        by_char.items(),
        key=lambda kv: -sum(x["logged_damage"] for x in kv[1]
                            if x["key_state"] != "absent")
        / (sum(x["logged_damage"] for x in kv[1]) or 1.0))
    print("\n[characters] five highest-coverage members, per ability:")
    for (cid, cname), rows in cov_rank[:5]:
        tot = sum(x["logged_damage"] for x in rows) or 1.0
        cov = 100.0 * sum(x["logged_damage"] for x in rows
                          if x["key_state"] != "absent") / tot
        print(f"  {cname} ({cid}) — keyed coverage {cov:.1f}%:")
        for x in sorted(rows, key=lambda x: -x["logged_damage"])[:10]:
            rat = f"{x['ratio']:.3f}" if x["ratio"] is not None else "n/a"
            print(f"    {str(x['spell_name'])[:34]:34} "
                  f"{x['coverage_share_of_logged']:5.1f}% of logged, "
                  f"ratio {rat:>8} [{x['key_state']}]"
                  + (f" ~{x['round_flag']:g}" if x["round_flag"] else ""))
        if len(rows) > 10:
            print(f"    ... {len(rows) - 10} more rows in the JSON artifact "
                  f"(stated, not silent)")

    # ---- 3i C7 — the committed summary artifact ---------------------------
    # 3h's headline result (0.253 / 11% / 25% / 62.2%) lived only in
    # gitignored data/derived/ and was "the single number a monitoring chat
    # cannot check" (AUDIT_3H §2). The summary statistics — never the row
    # dump — land in predictions/, self-identifying like the gate manifest,
    # and refused on a dirty tree for the same reason the manifest is.
    import subprocess
    repo_root = Path(__file__).resolve().parents[2]
    try:
        sha = subprocess.run(["git", "rev-parse", "HEAD"],
                             capture_output=True, text=True, cwd=repo_root,
                             check=True).stdout.strip()
        dirty = bool(subprocess.run(["git", "status", "--porcelain"],
                                    capture_output=True, text=True,
                                    cwd=repo_root, check=True).stdout.strip())
    except Exception:                                   # noqa: BLE001
        sha, dirty = None, None

    per_char_split = []
    for (ccid, ccname), rows in sorted(by_char.items(),
                                       key=lambda kv: kv[0][1].lower()):
        tot = sum(x["logged_damage"] for x in rows) or 1.0
        per_char_split.append({
            "character_id": ccid, "name": ccname,
            "keyed_pct": round(100.0 * sum(
                x["logged_damage"] for x in rows
                if x["key_state"] != "absent") / tot, 1),
            "producing_pct": round(100.0 * sum(
                x["logged_damage"] for x in rows
                if x["key_state"] == "producing") / tot, 1),
            "absent_pct": round(100.0 * sum(
                x["logged_damage"] for x in rows
                if x["key_state"] == "absent") / tot, 1),
        })
    summary = {
        "status": "FINDING",
        "_status_note": "FINDING — regenerated by every run of "
                        "tools/audit/per_ability_accuracy.py on a clean tree; "
                        "true as of generated_at, at git_sha",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_sha": sha,
        "git_working_tree_dirty": dirty,
        "tool": "tools/audit/per_ability_accuracy.py (3h C1, repaired 3i C)",
        # 🆕 3j C7 (`AUDIT_3I_ADVERSARIAL` §6) — COHORT IDENTITY, and the
        # filters that were applied. The gitignored sibling carried the cohort
        # slug and this committed artifact did not; and nothing here recorded
        # that `--char` or a non-zero `--max-lag-hours` had narrowed the
        # population, so a one-character debugging run produced a file that
        # LOOKED cohort-wide. (The write itself is now refused under a filter —
        # see below — so these fields describe an unfiltered run by
        # construction. They are recorded anyway: a reader should not have to
        # infer scope from the absence of a warning.)
        "cohort": cohort_spec.get("slug"),
        "cohort_frozen_at": cohort_spec.get("frozen_at"),
        "cohort_size": len(cohort_ids),
        "holdout_excluded": True,
        "filters": {"char_ids": sorted(args.char) if args.char else None,
                    "max_lag_hours": args.max_lag_hours},
        "prereg": ["predictions/prereg_3h_per_ability.md (first run)",
                   "primer/SESSION_3I_PRIMER.md Block C6 (3i re-run)"],
        "population": {"characters": len(seen) - len(skipped),
                       "ability_rows": len(all_rows)},
        "histogram_paired_keyed_ratio": {
            b: hist.get(b, 0) for b in order if hist.get(b, 0) or b == "= 0"},
        "key_state_share_of_cohort_logged_pct": {
            state: round(100.0 * sum(r["logged_damage"] for r in paired
                                     if r["key_state"] == state)
                         / total_logged_all, 1)
            for state, _ in Counter(r["key_state"] for r in paired).most_common()},
        "producing": ({
            "n": len(prod),
            "median_ratio": round(statistics.median(prod), 4),
            "quartiles": ([round(q, 4) for q in
                           statistics.quantiles(prod, n=4)]
                          if len(prod) >= 4 else None),
            "in_band_0.8_1.25": sum(1 for x in prod if 0.8 <= x <= 1.25),
        } if prod else None),
        "zeros": {"paired_keyed_at_exactly_zero": zero_paired,
                  "paired_keyed_total": len(keyed)},
        "absent": {"rows": len(absent),
                   "share_of_cohort_logged_pct": round(absent_share, 1)},
        "phantom": {"producing_sim_only_keys": len(phantom),
                    "share_of_cohort_sim_damage_pct": round(
                        100.0 * phantom_sim / total_sim_all, 1),
                    "sim_only_rows_total": sum(
                        1 for r in all_rows if r["logged_damage"] == 0)},
        # 3l B0 — the ranked per-key table, committed. Full list, no caps.
        "per_key_table": per_key_table(paired, total_logged_all),
        "per_character_coverage_split": per_char_split,
    }
    # 🛑 3j C7 (`AUDIT_3I_ADVERSARIAL` §6) — REFUSE TO WRITE THE COMMITTED
    # ARTIFACT UNDER A FILTER. `--char` was accepted, applied, and written out
    # unconditionally on a clean tree, with nothing in the JSON recording that
    # a filter had been used: one debugging run on one character silently
    # replaced a cohort-wide committed artifact with a partial one that looked
    # cohort-wide. The `data/derived/` artifacts below are still produced, so
    # the debugging use is not blocked — only the *committed* claim is.
    #
    # 🛑 The refusal is COMPUTED here and RAISED at the very end of `main()`,
    # after the `data/derived` artifacts are written — because the message says
    # they still are, and a guard whose own message is false is worse than no
    # guard. Debugging use is not blocked; only the *committed* claim is.
    summary_refusal = None
    if bool(args.char) or args.max_lag_hours != 0.0:
        summary_refusal = (
            f"🛑 REFUSED to write {SUMMARY_PATH.name}: this run is FILTERED "
            f"(--char {sorted(args.char) if args.char else None}, "
            f"--max-lag-hours {args.max_lag_hours:g}), so it does not describe "
            f"the cohort its readers will assume. Re-run without filters to "
            f"refresh the committed summary.")
    elif dirty is not False:
        # 🛑 3j C7 — this RAISES now, matching the docstring's claim of "the
        # same dirty-tree discipline as the gate manifest". It printed and
        # continued with exit 0 while `calibrate_crawled.py` raised, so the
        # docstring overstated it and a caller checking the exit code saw
        # success where the manifest would have failed the build.
        summary_refusal = (
            f"🛑 REFUSED to write {SUMMARY_PATH}: the working tree is "
            f"{'DIRTY' if dirty else 'in an UNKNOWN git state'}, so git_sha "
            f"would not identify the code that produced it — the same rule as "
            f"the gate manifest. Commit first and re-run.")
    if summary_refusal is None:
        SUMMARY_PATH.write_text(json.dumps(summary, indent=1) + "\n",
                                encoding="utf-8")
        print(f"\n[summary] {SUMMARY_PATH} (committed artifact, git {sha[:8]})")
    else:
        print(f"\n{summary_refusal}")

    # ---- artifacts --------------------------------------------------------
    JSON_PATH.write_text(json.dumps({
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "cohort": cohort_spec.get("slug"),
        "tool": "per_ability_accuracy.py (3h C1)",
        "prereg": "predictions/prereg_3h_per_ability.md",
        "note": "ratio = (sim_damage/sim_fight_s) / (logged_damage/encounter_s); "
                "key_state 'absent' rows have sim_damage 0 by construction",
        "rows": all_rows,
    }, indent=1), encoding="utf-8")
    md = ["# Per-ability accuracy — 3h Block C", "",
          f"Generated {datetime.now(timezone.utc).isoformat(timespec='seconds')} "
          f"over the frozen tuning set. Full rows in "
          f"`per_ability_accuracy.json`. Pre-registration: "
          f"`predictions/prereg_3h_per_ability.md` (committed before first run).",
          "", "| character | spell | id | share of logged | ratio | state |",
          "|---|---|---:|---:|---:|---|"]
    for r in sorted(paired, key=lambda r: (r["character_name"],
                                           -r["logged_damage"])):
        rat = f"{r['ratio']:.3f}" if r["ratio"] is not None else "n/a"
        md.append(f"| {r['character_name']} | {r['spell_name']} "
                  f"| {r['spell_id']} | {r['coverage_share_of_logged']:.1f}% "
                  f"| {rat} | {r['key_state']}"
                  + (f" ~{r['round_flag']:g}" if r["round_flag"] else "") + " |")
    MD_PATH.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"\n[artifacts] {JSON_PATH}\n            {MD_PATH}")
    # 🛑 3j C7 — raised LAST, so the derived artifacts the refusal message
    # promises are genuinely on disk before the process exits non-zero.
    if summary_refusal is not None:
        raise SystemExit(summary_refusal + " (The data/derived artifacts above "
                                           "WERE written — use those.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
