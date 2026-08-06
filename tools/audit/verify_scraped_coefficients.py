"""
verify_scraped_coefficients.py — test db.ascension.gg's STATED coefficients
against what characters actually dealt (Route 2, 2026-08-06).

    py tools/audit/verify_scraped_coefficients.py [--min-hits 100] [--min-chars 3]

## What this is, and what it is NOT

🛑 This is **NOT** `infer_coefficient()`, which `3a` correctly refused. That
refuses to *estimate* a coefficient from pooled data, and it is right to: with
several unknown terms you cannot isolate one stat's contribution.

Here **every term is already stated** — flat, SP%, AP%. Nothing is being
solved for. We evaluate the stated formula on each character's own computed
stats and ask whether it predicts what that character actually dealt. That is a
**hypothesis test against a predicted value**, not an estimation, and it is a
far weaker requirement on the data.

## 🛑 THIS IS A SCREEN, NOT A VALIDATION — and that is a measured finding

The first version of this tool tried to be comparative: does the stated formula
track observed damage better than a **flat-only null model**? **That test was
degenerate and its result has been retracted.** The flat term is a *constant
per spell*, so the null model has zero variance across characters and its
correlation is undefined — on all 247 tested spells. The verdict rule read
`r_null is None or r_model > r_null`, which handed every spell an automatic
pass. It reported "183 supported, 0 contradicted" and meant nothing.

What the data actually shows, once that is removed: **cross-character
correlation cannot discriminate here.** Across 207 spells with a computable
correlation the distribution of `r(model)` is centred on zero — median
**+0.10**, only 29 above +0.5, and **83 negative**. A roughly symmetric spread
around zero is what pure noise looks like.

That is not evidence against the coefficients. It is evidence that the method
is swamped: observed per-hit damage carries each character's talent
multipliers, crit rate (a `damage/hits` average includes crits), target armor,
partial resists and content mix — all large, all unmodelled per crawled kit,
and none correlated with spell power. A real coefficient is easily buried.

**So what survives is a sanity screen**, and it is worth having on its own
terms: the *implied multiplier* (observed ÷ predicted) catches order-of-
magnitude and wrong-rank errors decisively even when it cannot confirm a
coefficient to within a factor of two. A spell implying ×1.6 is consistent with
crit inflation plus an ordinary talent stack; one implying ×29 is not, and is
a flag worth chasing.

**Conclusion: this cannot retire the `unverifiable` bucket.** Only a
client-side decoded flat can (Route 1 — the widened `--with-dbc` extract,
id list in `data/derived/dbc_extract_scope_request.json`).
"""
import argparse
import json
import sqlite3
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import config  # noqa: E402
from config import BUILDS_DB_PATH, DATA_DERIVED, DB_PATH  # noqa: E402
from core.builds.gear import normalise_stats  # noqa: E402
from core.builds.spec import BuildSpec, GearItem  # noqa: E402
from core.builds.stats import compute_stats  # noqa: E402
from core.db.connection import connect  # noqa: E402
from core.sim import combat_engine as ce  # noqa: E402
from core.sim.content import Role, get_preset  # noqa: E402

config.ensure_utf8_stdout()

SCRAPE = config.DATA_SOURCE / "ascension_db" / "spell_pages.ndjson"
REPORT = DATA_DERIVED / "scraped_coefficient_verification.md"
PATH_TOKEN = {"strength": "Strength", "agility": "Agility", "duality": "Duality",
              "intellect": "Intelligence", "intelligence": "Intelligence",
              "spirit": "Healing", "healing": "Healing"}
WEAPON_SLOTS = {16: "main_hand", 17: "off_hand"}


def load_scraped(only_unverifiable=True):
    out = {}
    for line in SCRAPE.open(encoding="utf-8"):
        r = json.loads(line)
        if not r.get("parsed_ok") or not r.get("scaling"):
            continue
        if only_unverifiable and r.get("cross_check") != "unverifiable":
            continue
        terms = {}
        for s in r["scaling"]:
            if s.get("term_type") in ("SP", "AP"):
                terms[s["term_type"]] = terms.get(s["term_type"], 0.0) + s["coefficient"]
        if terms:
            out[r["spell_id"]] = {"name": r.get("name_on_page"), "terms": terms,
                                  "value": r.get("value")}
    return out


def snapshot_stats(bconn, aconn, conv, snapshot_id, path):
    """A crawled snapshot's real SP/AP — gear + path + talents, via the same
    compute_stats the calibration gate uses. Not gear-only: `gear_stats_json`
    is the `_gearOnly` trap and would understate a caster badly."""
    token = PATH_TOKEN.get((path or "").lower())
    if token is None:
        return None
    gear = {}
    for slot, item_id, name, stats_json, weapon_json in bconn.execute(
            "SELECT slot, item_id, item_name, stats_json, weapon_json "
            "FROM snapshot_gear WHERE snapshot_id = ?", (snapshot_id,)):
        stats, _ = normalise_stats(stats_json)
        sname = WEAPON_SLOTS.get(slot, f"slot_{slot}")
        gear[sname] = GearItem(item_id=item_id, name=name or str(item_id),
                               slot=sname, stats=stats,
                               weapon=json.loads(weapon_json) if weapon_json else None)
    if not gear:
        return None
    spec = BuildSpec(character_level=60, role=Role("dps"), path=token,
                     abilities=[], talents=[], gear=gear, source="crawled")
    try:
        cs = compute_stats(spec, get_preset("raid_boss_st"), conv, conn=aconn)
    except Exception:                      # noqa: BLE001
        return None
    return {"sp": float(getattr(cs, "spell_power", 0) or 0),
            "ap": float(getattr(cs, "attack_power", 0) or 0)}


def _pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    sx = sum((x - mx) ** 2 for x in xs) ** 0.5
    sy = sum((y - my) ** 2 for y in ys) ** 0.5
    if sx == 0 or sy == 0:
        return None
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (sx * sy)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--min-hits", type=int, default=100)
    ap.add_argument("--min-chars", type=int, default=3)
    ap.add_argument("--all-verdicts", action="store_true",
                    help="also test rows that already cross-checked 'agree'")
    args = ap.parse_args()

    scraped = load_scraped(only_unverifiable=not args.all_verdicts)
    print(f"[scope] {len(scraped)} scraped spells state an SP/AP coefficient")

    bconn = sqlite3.connect(BUILDS_DB_PATH)
    aconn = connect(DB_PATH)
    conv = ce.load_rating_conversions(aconn, level=60)

    stat_cache = {}
    results = []
    for sid, rec in scraped.items():
        rows = bconn.execute(
            """SELECT ap.character_id, ap.scope_id, ap.damage_total, ap.hits,
                      ap.crits, ep.snapshot_id, ep.path
               FROM ability_performance ap
               JOIN encounter_performance ep
                 ON ep.scope_id = ap.scope_id AND ep.character_id = ap.character_id
               WHERE ap.spell_id = ? AND ap.damage_total > 0 AND ap.hits > 0
                 AND ap.is_pet = 0 AND ep.snapshot_id IS NOT NULL""", (sid,)).fetchall()
        obs = []
        for cid, scope, dmg, hits, crits, snap, path in rows:
            key = (snap, path)
            if key not in stat_cache:
                stat_cache[key] = snapshot_stats(bconn, aconn, conv, snap, path)
            st = stat_cache[key]
            if not st:
                continue
            flat = 0.0
            v = rec.get("value") or {}
            if v:
                flat = (float(v["min"]) + float(v["max"])) / 2
            pred = (flat
                    + st["sp"] * rec["terms"].get("SP", 0.0)
                    + st["ap"] * rec["terms"].get("AP", 0.0))
            if pred <= 0:
                continue
            obs.append({"character_id": cid, "sp": st["sp"], "ap": st["ap"],
                        "predicted": pred, "flat_only": flat or 1.0,
                        "observed": dmg / hits, "hits": hits})
        if len(obs) < args.min_chars or sum(o["hits"] for o in obs) < args.min_hits:
            continue

        preds = [o["predicted"] for o in obs]
        flats = [o["flat_only"] for o in obs]
        actual = [o["observed"] for o in obs]
        r_model = _pearson(preds, actual)
        r_null = _pearson(flats, actual)
        spread = (max(preds) / min(preds)) if min(preds) > 0 else 1.0
        implied = statistics.median(a / p for a, p in zip(actual, preds))

        # 🛑 The verdict is a SANITY SCREEN on the implied multiplier, NOT a
        # confirmation of the coefficient. Correlation is reported alongside
        # but is deliberately not the verdict — see this module's header for
        # why the comparative version of this test was degenerate.
        if not (0.2 <= implied <= 5.0):
            verdict = "screen_FLAG"        # order-of-magnitude / wrong-rank smell
        elif spread < 1.15:
            verdict = "screen_pass_no_spread"
        else:
            verdict = "screen_pass"
        results.append({
            "spell_id": sid, "name": rec["name"], "terms": rec["terms"],
            "characters": len(obs), "hits": sum(o["hits"] for o in obs),
            "r_model": r_model, "r_null": r_null, "predicted_spread": spread,
            "implied_multiplier": implied, "verdict": verdict,
        })

    results.sort(key=lambda r: -r["hits"])
    tally = {}
    for r in results:
        tally[r["verdict"]] = tally.get(r["verdict"], 0) + 1
    print(f"[tested] {len(results)} spells with enough observation")
    for k, v in sorted(tally.items(), key=lambda kv: -kv[1]):
        print(f"   {v:4}  {k}")

    plaus = [r for r in results if 0.2 <= r["implied_multiplier"] <= 5.0]
    print(f"[screen] {len(plaus)} of {len(results)} have an implied multiplier "
          f"in 0.2-5.0 (no order-of-magnitude error)")
    rs = [r["r_model"] for r in results if r["r_model"] is not None]
    if rs:
        rs_sorted = sorted(rs)
        print(f"[correlation] median r(model) "
              f"{rs_sorted[len(rs_sorted)//2]:+.2f}, "
              f"{sum(1 for x in rs if x > 0.5)} above +0.5, "
              f"{sum(1 for x in rs if x < 0)} NEGATIVE of {len(rs)}")
        print("[correlation] centred on zero => this method cannot discriminate; "
              "per-character multipliers swamp the stat signal. SCREEN ONLY.")

    lines = [
        "# Verifying scraped coefficients against real damage", "",
        "Route 2 (2026-08-06): db.ascension.gg **states** each coefficient, so "
        "nothing is estimated here — the stated formula is evaluated on each "
        "character's own computed stats and tested against what they actually "
        "dealt. 🛑 This is not `infer_coefficient()`, which refuses to *derive* "
        "a coefficient from pooled data and is right to.", "",
        "🛑 **This is a SCREEN, not a validation.** An earlier comparative "
        "version of this test — stated formula vs a flat-only null model — was "
        "DEGENERATE and its result is retracted: the flat term is constant per "
        "spell, so the null has zero variance and undefined correlation on all "
        "247 spells, and the verdict rule handed every one an automatic pass. "
        "With that removed, cross-character correlation is centred on zero "
        "(median r +0.10, 83 of 207 NEGATIVE) — the shape of pure noise. That "
        "is not evidence against the coefficients; it is evidence the method is "
        "swamped by talent multipliers, crit inflation, target armor and "
        "content mix, none modelled per crawled kit. What survives is the "
        "implied multiplier, which still catches order-of-magnitude and "
        "wrong-rank errors decisively.", "",
        "**This cannot retire the `unverifiable` bucket** — only a client-side "
        "decoded flat can (Route 1, `data/derived/dbc_extract_scope_request.json`).", "",
        f"**{len(results)} spells tested** "
        f"({sum(r['hits'] for r in results):,} pooled hits).", "",
        "| verdict | spells |", "|---|---:|",
    ]
    for k, v in sorted(tally.items(), key=lambda kv: -kv[1]):
        lines.append(f"| {k} | {v} |")
    lines += [
        "", f"**{len(plaus)} of {len(results)}** have an implied multiplier "
        f"between 0.2 and 5.0 — no order-of-magnitude or wrong-rank error.", "",
        "| spell | id | chars | hits | terms | r(model) | r(null) | implied × | verdict |",
        "|---|---:|---:|---:|---|---:|---:|---:|---|",
    ]
    for r in results[:60]:
        terms = " ".join(f"{k} {v:.3f}" for k, v in sorted(r["terms"].items()))
        rm = f"{r['r_model']:+.2f}" if r["r_model"] is not None else "n/a"
        rn = f"{r['r_null']:+.2f}" if r["r_null"] is not None else "n/a"
        lines.append(f"| {r['name']} | {r['spell_id']} | {r['characters']} | "
                     f"{r['hits']:,} | {terms} | {rm} | {rn} | "
                     f"{r['implied_multiplier']:.2f} | {r['verdict']} |")
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"[report] {REPORT}")
    (DATA_DERIVED / "scraped_coefficient_verification.json").write_text(
        json.dumps(results, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
