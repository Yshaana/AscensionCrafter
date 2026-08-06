# Audit primer — session `3c`, 2026-08-06

**For the monitoring-chat audit.** Written the way the incoming `3c` primer was:
claims first, with the commits and commands to reproduce them, and the things I
am *least* sure about flagged rather than buried.

Commits this session: `79c6568` → `a7af0fb` (8 commits, all pushed to `main`).
Rebuild 21 steps green, `core/` purity 0/47, all sim-engine checks pass.

---

## 0. 🚨 Answering the scope question first: **NO, Phase 4 was not next**

`PHASE_3_builds_repo.md`'s own execution order has two chains, and **only one of
them ran**:

```
1 (schema) → 2 (inference) → 3 (search) → 4 (gear) → 8 (crawler)   ✅ DONE
5 (addon)  → 6 (logs)      → 7 (automation)        [independent]   ❌ DEFERRED
```

Verified in the tree today: `core/builds/search.py` ✅, `core/builds/inference.py`
✅, `builds.db` ✅, gear layer ✅ — but **`ingest/logs/` does not exist** (T6) and
there is **no hooks directory** (T7). T5's addon exists only as
`addons/AscensionCrafterExport` (the stat exporter), not the capture addon the
phase doc specifies. PROGRESS records these as *"deferred, not blocked"* by an
owner scoping decision, and that deferral was never revisited.

**And the exit criteria are more than the gate.** Six are listed; the calibration
gate is one. Also outstanding or unverified:

* *"At least one default uncertainty range replaced by a measured confidence
  interval"* — inference is **staging-only** (74 proposals, nothing promoted).
* *"`ContentProfile` presets are derived from real encounter data, not
  invented"* — `core/sim/content.py` carries no marker of derivation; I could not
  confirm this is met and **flag it as unverified**, not as failed.

> **Recommendation: Phase 3 is not finishable by closing the gate alone.** The
> deferred T5→T6→T7 chain and at least two non-gate exit criteria remain.

### 🆕 And today made T6 much more valuable than when it was deferred

Everything in §2 below — aligning a combat log against the site's API, comparing
`casts` to `SPELL_CAST_SUCCESS`, correlating deaths to encounter windows — **was
done by hand this session**. T6 (*combat log ingestion*) is precisely that
capability, systematised. The new **T11** (give Elric a snapshot from his ALC
capture) is a thin slice of the same chain. The deferral looks less defensible
after today than before it.

---

## 1. What was executed from the incoming audit primer

All four ordered steps, plus a blocker the primer did not name.

| step | outcome |
|---|---|
| **STEP 0** — partition the bulk scrape | ✅ `source='db_ascension_gg_scraped'`; the hand-curated `db_ascension_gg` anchor (HftH 282987) untouched and verified surviving a clean rebuild |
| **STEP 1** — agree-only filter | ✅ `unverifiable` **out**, `disagree` refused and logged. PROGRESS's contradicting line reconciled |
| **STEP 2** — lock the rider first | ✅ ≥3 qualified at ≥50%, stamped in `CALIBRATION_TOLERANCE.md` **and** wired into the tool **before** the re-run |
| **STEP 3** — ingest + re-run | ✅ 3,446 coefficients / 1,617 spells; verdicts recomputed live (**2,692 agree / 8 disagree**, reproducing the audit exactly) |

**Blocker the primer missed — same family as its own Blocker A.** STEP 3.2 said
to reconcile the 329 trigger edges into `spell_relationships` as a separate step.
That table has **one writer whose `DELETE` is unscoped**, so a separate script
would have re-committed the `resolve_numeric_formulas.py` bug (2c). Edges are
added inside `populate_all`, after the client's own `EffectTriggerSpell` so it
wins collisions.

**Result: 0 new edges — all 329 were already carried by the client.** Not a
failure; two independent sources agreeing on the whole trigger graph.

### Gate outcome

**5 of 41 within ±20% (was 4), 2 qualified (was 1) → PHASE 3 EXIT NOT MET.**

🚨 **The median magnitude coverage did NOT move — still 37%** — against the
primer's expectation that *"this is where the median 37% should move"*. That
expectation was mis-specified: coverage is gated on **magnitudes**, the client
supplies those, and a coefficient source can only make already-modelled abilities
more accurate. Measured over the 88 demand-ranked unmodelled abilities: **83
already have a magnitude**, 51 now have a coefficient, **all 88 are
out-of-catalog**, and **57 have no card and no incoming trigger edge**. Coverage
is a **reachability** problem.

---

## 2. What the owner's four log uploads established

Reports [104](https://darkmoon.ascensionlogs.gg/reports/104/encounters)–[107](https://darkmoon.ascensionlogs.gg/reports/107/encounters) — the same combat measured locally *and* through the API.

1. **`ability_performance` is EXACT.** Report 106: site 443,505 vs log 443,505,
   **20 of 20 abilities at +0.0%**. Report 107: 1,102,221 vs 1,102,221, **zero**
   disagreements. ⚠ DPS differs 1–2% purely by **window** — compare totals.
2. **The site's `casts` IS `SPELL_CAST_SUCCESS`** — 93% and **97.3%**. An earlier
   objection of mine ("it under-reads proc builds and would bias the corpus") is
   **withdrawn**; it was wrong at character level.
3. **`deaths` is UNOBTAINABLE** — no death-like or presence-like key anywhere in
   the payload for a report we control. The column can never be filled.
4. **The failure mode it hides, with ground truth:** Elric died 6.1s into a 34.0s
   fight, dead **82%** of it; the site reports **481 DPS vs 3,473** elsewhere,
   `deaths` NULL, `validation_status: 'valid'`.
5. **The buff layer, measured per hit** (106 vs 107): a tight **~×1.45** core on
   ten abilities, **Righteous Vengeance ×3.18** (conversion compounding), and
   **Consecrated Holy Weapon 25.1% of buffed damage** — independently
   reproducing the documented 25.1% to one decimal.

---

## 3. 🛑 Three things I got wrong this session

Listed deliberately, because an audit should check these hardest.

**(a) I shipped a coefficient double-count.** The ingest left **323 (spell,term)
pairs with two sources**, and `_formula_terms` emitted every row as its own term
— which the engine **sums**. Mongoose Bite got AP 0.45 + 0.20 = **0.65**. Fixed
with explicit source precedence in `_dedupe_coefficients`. ⚠ **My first fix
didn't work**: keying on `(term, component)` failed because a legacy row's
`component` is NULL meaning *unknown*, not *a different component*. The key must
be the term, with one source winning outright.
*Gate re-run after the fix: unchanged at 5/41 — it was not inflating the gate.*

**(b) I called Boomcat the best clean-qualifier candidate. Retracted.** I framed
over-predictions as "unambiguous bugs". Report 104 proved a second cause that is
not a bug: a death-deflated parse. **Boomcat's within-character APM ratio is
0.24; Elric's known death case is 0.38.** Boomcat is likely the same signature.

**(c) I over-claimed against `casts` as a filter** before measuring it (see 2.2).

---

## 4. The revised plan — what the audit should scrutinise

Full detail in `PLAN_3C_clean_exit.md` (with a dated revision section).

### The diagnosis it rests on

The miss decomposes into **coverage** and **slice accuracy**
(`(100+delta)/coverage`), and only the first was being tracked. **Both current
qualifiers pass by over-producing on their modelled slice** (Ari 156%, Malo
131%), so fixing accuracy alone loses them — the two must move together. The
arithmetic says **~80% coverage** is where a truthful model lands inside ±20%.
🛑 That is knowledge obtained *after* the 50% rider was stamped and **must not
edit it**.

### Order

| # | task | why here |
|---|---|---|
| **T13** | fix `calibrate_vs_log.py`'s Duality-era defaults | 10 min, and it silently moves HftH 1.26× → 1.45× |
| **T6\*** | conversion mechanics (RV / Ignite / Deep Wounds) | two independent measurements; no data needed; 9 of 41 characters |
| **T11** | give Elric a snapshot from his ALC capture | first character with **zero input error by construction** |
| **T10→T9** | controlled before/after, then the ~4.5× out-of-catalog cluster | five spells within ±4% = one mechanism; may generalise to the cohort |
| T4, T5, T12, T7 | trigger-edge reachability, pets, coefficient-conflict review, class-A reachability | |

\* `T6` here is PLAN_3C's task, not PHASE_3's T6. **Naming collision — worth
renaming before it causes an error.**

### The strategic claim I most want challenged

> T2's dead end + T3's weakening ⇒ **the crawl cohort may not be able to deliver
> a clean exit on its own**, because a model error and an invalid parse are
> indistinguishable per candidate. The route through is to fix the model against
> **Elric** (verified inputs, 11 valid boss encounters, zero snapshots today),
> then let the corrected model lift the cohort.

⚠ Elric **cannot** satisfy the exit himself — §8.2 wants ≥3 distinct characters.
He is an instrument, not a count.

---

## 5. Open decisions for the owner / audit

1. **The 177 export-vs-scraped coefficient conflicts.** Precedence currently
   prefers the scrape (states the *applied* value, carries a check digit, and the
   catalog stores the wrong rank for ~half of multi-rank cards). **That is a
   judgement call now load-bearing on 177 abilities.** Mongoose Bite 0.20 vs
   0.45; Holy Wrath 0.15 vs 0.07.
2. **Holy Shock (25902)**: measured-provisional **0.40** (back-solved from the
   owner's parses) vs scraped **0.214**. ~2× apart. Provisional wins by
   precedence — and calibrating it against the parses that produced it is
   **circular**.
3. **Should Phase 3's deferred T5→T6→T7 chain be reinstated** before Phase 4,
   given §0?
4. **`ContentProfile` presets derived from real encounter data** — exit criterion
   I could not verify either way.

## 6. Reproduce

```bash
py cli/rebuild.py                                    # 21 steps
py tools/audit/check_core_purity.py                  # 0/47
py tools/audit/check_sim_engine.py                   # all pass
py tools/audit/calibrate_crawled.py --limit 120 --max-lag-hours 0
py ingest/ascension_db/load_scraped_coefficients.py --dry-run
```

⚠ The calibration below **requires the stat block**; its defaults are wrong:

```bash
py tools/audit/calibrate_vs_log.py --character Elric --ap 141 --sp 638 --weapon-min 543.6 --weapon-max 646.3 "data/source/captures/2026-08-05_elric_2e_poi_baseline/2026-08-05-22.42.20_WoWCombatLog.txt"
```
