# Adversarial audit — session `3e`

**Auditor:** monitoring chat, 2026-08-06. **Method:** fresh clone of `main` at `c86eb7f`,
code read directly, `3e` = `200f79f..c86eb7f`. Five parallel deep-dives (Block A, Block B,
Block C, fail-open instruments, standing threads), then every 🔴 finding re-verified by hand
against the tree. Every number below was recomputed from committed artifacts; every claim
cites `file:line`.

**Limitation, same as `3c`:** `data/derived/` is gitignored and no `.db` is committed, so
`check_sim_engine.py`, `calibrate_crawled.py`, `calibrate_vs_log.py` and
`check_gate_exclusion.py` cannot be run end-to-end by an auditor. Pure-logic halves were
executed. `check_core_purity.py` **was** run: `49 files checked, 0 violations`.

---

## 0. Verdict in five lines

1. **`3e`'s headline is right and it is the most valuable thing in the session.** Five
   engine defects fixed, gate unmoved, holdout unmoved at 27–69% coverage. I could not
   break that result and it reproduces from the committed manifest. The discipline around
   it — holdout redacted at `68779e7`, read once at `7c416d1` — is provable from git, not
   asserted.
2. **But `3e` shipped four instruments that cannot fail**, and closed defects on two of
   them. The E2 "execute window" check passes on a string the sim emits unconditionally;
   the pet check asserts a pure function returns the same value twice; the rule-1 exclusion
   guard **cannot run at all** — `3e`'s own A1 broke its signature; and `_filler_ids`
   re-implements a classification rule B1 changed, while its docstring claims it cannot drift.
3. **A `retail_hypothesis` is silently shaping the gate number.** `CP_PER_BUILDER_CAST`
   scales finisher cast counts in `fast_sim` — the tier the gate runs on — and its
   disclosure warning is nested inside a branch `apl_gen` can never generate. Three
   documents state that the warning fires.
4. **Block A's freeze has a second exit that is not instrumented**, and the committed
   manifest reports `still_qualifying: 41, dropped: []` from a field that counts *scored*
   characters. A sim crash on a frozen member shrinks the headline denominator silently,
   into a gitignored file.
5. **The one thing that must not go wrong this week is half-guarded.** The 2026-08-08 phase
   flip will fail the crawl loudly and correctly — and then `gear_tier_stats()` will blend
   Phase 1 and Phase 2 silently, because `phase_label` is written as literal `None`.

**Net:** `3e` is the most honest session in the project's history and the most
self-instrumented, and that is exactly why the instruments matter. `PLAN_3G` is the right
next document; it is also already stale about its own tree.

---

## 1. Audit of `3e`'s own claims

| Claim (session record / `PROGRESS.md`) | Verdict | Evidence |
|---|---|---|
| Gate unmoved: 5 of 36, 2 qualified, slice 64.3% | ✅ **REPRODUCES EXACTLY** | recomputed from `predictions/gate_manifest_3e.json`: `within_tolerance=5`, `qualified=2`, `median…_ge_20 = 64.29871133238616`. 5 passers, 2 with coverage ≥20 (`Ari` 57.6, `Malo` 62.4) |
| Holdout 0 of 5, read once at close-out | ✅ **PROVABLE FROM GIT** | `git show 68779e7:predictions/gate_manifest_3e.json` → `holdout.read: false`, `results: "REDACTED"`. `read: true` only at `7c416d1` |
| Holdout ids named **before** the work | ✅ **CORRECT** | `ingest/export/seed_predictions.py:185-194`, landed `69f2192` (3d Block F), one commit before `3e`. The pre-registration rule is outcome-blind by construction |
| A1: `cohort_frozen_3e.json` copied verbatim from the `3d` manifest | ✅ **VERIFIED BYTE-WISE** | id lists compare **order-sensitively equal**, 41 vs 41, 0 dupes, all `name` fields identical |
| A1: `ORDER BY … LIMIT N` unreachable on every path | ✅ **CORRECT** | `calibrate_crawled.py:240` signature has no `limit`; `:216-236` SQL has no `LIMIT`; argparse `:589-598` exposes only `--cohort/--max-lag-hours/--read-holdout` |
| A1: `gate_manifest.json` is immutable | ✅ **CORRECT** | `:160` `GATE_MANIFEST_PATH = …gate_manifest_3e.json`; sole write at `:1201-1203`; no other writer in the tree |
| A1: a member that stops qualifying is **dropped with a reason, never substituted** | ⚠️ **HALF TRUE — the second exit is silent** | true for the completeness filter (`:275-333`, printed `:617`, manifest `:1163`); **false for the sim path** — `:633/:641/:645/:666` push losses into `excluded`, which never reaches `dropped`, never reaches the manifest, and lands only in gitignored `data/derived/`. See §4.1 |
| A1: "41 of 41 still qualify, 0 dropped" | ✅ reproducible / ⚠️ **vacuous** | `corpus_row_counts` is byte-identical across all 8 tables between the `3d` 18:37 run and the `3e` 21:10 run — the drop machinery ran against an unchanged corpus. Implemented, not tested |
| A1: cohort fixed **before** the next result was seen | ⚠️ **PLAUSIBLE, UNVERIFIED** | cohort file and re-run manifest land in the **same** commit `68779e7`. Three things corroborate it strongly (§2) but git does not. Same shape as `3c`'s rider finding |
| A2: `3d`'s 160% was a low-coverage artifact; the sim **under**-produces | ✅ **CORRECT, arithmetic checks** | `gate_manifest.json` all-41 median = 159.795%; `Mutaforma` `slice_accuracy_pct = 1859400.19` at 0.2% coverage, both in the committed `3d` manifest as claimed |
| A2: floor implemented, printed beside the number, band table, floor in the manifest key | ✅ **ALL FOUR** | `:113`, stdout `:780-784`, band line `:787-789`, report `:916-921`, manifest key `median_slice_accuracy_pct_at_coverage_ge_20` |
| A2: the floor applies everywhere the median is consumed | ✅ **YES — one median site** | `slice_accuracy_bands()` `:479-494` is the only median computation; every reader goes through a band |
| A2: the band table in `CALIBRATION_TOLERANCE.md` | ❌ **MISLABELLED, AND 3 OF 5 `n` ARE WRONG** | see §5.1 — recomputed independently |
| A3: `within_tolerance` is `None` at zero coverage; consumers handle it | ✅ **CORRECT** | `:696-698`; nine consumers checked (`is True` / `is None` / explicit dict at `:964`); the single truthy test at `:511` is harmless. `Huskeer`/`Jamppa`/`Xizek` serialise as `null`; `3d` had them as `False` |
| A3: the 20% successor floor exists in code, reads 2 of 36 | ✅ **CONSTANT, not prose** — ⚠️ no trip-wire | `:131-132` `SUCCESSOR_COVERAGE_FLOOR_PCT`; 2 of 5 passers survive it, reproduced. **Nothing enforces the effective-from date** — if `3f` forgets, nothing fires |
| A4: 36/5 split, holdout withheld unless `--read-holdout`, no leakage | ✅ **CLEAN** | `:743-744`, `:795-811`, `:821`, `:1185-1188`; tuning arrays contain none of 460/461/462/463/7661 |
| A6: `ensure_utf8_stdout()` added to the harness | ✅ | `tools/audit/check_sim_engine.py:35` |
| A6: five documents made true again | ⚠️ **partial — and two were falsified in-session** | `ENGINE_BUGS.md:469` cites `:73,465,469`, correct at the *parent* and wrong in the very commit that "fixed" it (A1 moved them to `:82,658,662`). `ADDENDUM_3D_to_3E:33` asserts five flags are `required=True` — true at `68779e7`, falsified 3 commits later by `3e`'s own C1. Both still wrong at HEAD |
| B/E6: the cited `gcd_budget = 0.0` was *redundant, not wrong* | ✅ **arithmetic holds** — ⚠️ one exception | `casts*occupancy == gcd_budget` exactly. **Except `occupancy == 0`**, where the old line zeroed the budget and starved everything behind it. "Redundant, not wrong" is *mostly* right |
| B/E6: one allocation rule covers every on-GCD ability | 🟡 **structurally true, input fails open** | `tiers.py:342-387`; edge cases verified clean (zero/negative duration, `None` fields, div-by-zero, negative budget, over-subscription + `starved` warning). But see §4.5 |
| B/E4: grammar expresses DoT uptime; debuffs ≠ buffs | ✅ **evaluated, not just parsed** | types `apl.py:33-36`, evaluator `:127-136`, separate dict `tiers.py:465/590`, emitted `apl_gen.py:147-149` |
| B/E5: `_is_pure_periodic` from `events()`; Fireball is a direct nuke with a rider | ✅ **the code does what the prose says** | `tiers.py:170-191`, `apl_gen.py:75`, `_mixed_damage_warning` `:231-259`. The self-correction is real and well-reasoned |
| B/E1: `is_finisher` reads `per_combo`; finishers get their own tier; CP read from the APL gate | ✅ **all three** | `apl_gen.py:86-88`, `:117-119`, `:167-175`; `_cp_gate` `tiers.py:131-149` consumed at `:316` and `:557-558` |
| B/E1: `CP_PER_BUILDER_CAST` is "assumed once, under a name, **with a warning**" | ❌ **THE WARNING IS UNREACHABLE** | `tiers.py:379-385` is nested inside `if window < 1.0:` (`:371`). See §3.3 |
| B/E2: execute windows reachable; "both tiers say what they cannot know" | 🟡 **they say it; the check that certifies it is vacuous** | `EXECUTE_GATING_UNAVAILABLE` appended **unconditionally** at `tiers.py:425,635`. See §3.2 |
| B/E3: pets detected and named, no damage injected | ✅ **CORRECT** | `core/sim/pets.py` has no damage path; `tiers.py:426-429,636-643` touch no total |
| B/E3: the rule-5 string match is gone from the whole tree | ✅ **VERIFIED** | `check_sim_engine.py:760-761` calls `detect_summons`; no `"summon" in …name` anywhere. The both-directions disagreement evidence is genuine and the finding is a good one |
| E7 / E8 registered with E1–E6 discipline | 🟡 / ❌ | E7 has two registered failing checks (`check_sim_engine.py:81-92`) but its own row says `Check │ none yet` (`ENGINE_BUGS.md:344`). **E8 has no check at all** — `grep -n channel tools/audit/check_sim_engine.py` returns comments only |
| E8: `is_channeled` genuinely unread | ✅ **CONFIRMED** | written `core/spells/mechanics.py:275`, column `core/db/schema.py:340`, **zero reads in `core/sim/`** |
| C1: `--stat-block` parses the real exports; flags demoted to overrides; refusal covers both paths | ✅ **ALL VERIFIED BY EXECUTION** | `core/builds/stat_block.py:56`; `calibrate_vs_log.py:534-556` defaults `None`, `:449-456` prints `🛑 OVERRIDE`; both refusal paths `SystemExit` |
| C1: `ManaRegen_raw` left unconverted, nothing consumes it | ✅ **CORRECT** | raw string in `raw_fields`; `grep -rn mana_regen --include=*.py` → 0 hits. The addendum's warning was honoured |
| C1: `session_mismatch()` "verified in all three states" | ❌ **FAIL-OPEN ON THE LOG SIDE** | `stat_block.py:199-200` returns `None` — the caller's "all clear" value. See §3.4 |
| C2: fixture built by the parser from a verified same-session block | ✅ **every number recomputes exactly** | against `Unbuffed Mage.txt` |
| C2: the Mage fixture carries ground truth on seven abilities | ❌ **IT CARRIES NONE** | `fixtures/build_elric_frost_mage.json` has inputs only. See §4.7 |
| C2: "Blizzard casts 0 / 0 / **305** across Windows A/B/C" | ❌ **WRONG BY ~76×, AND 27% IS AN ENEMY'S** | measured: Elric `SPELL_CAST_SUCCESS` on Blizzard = **4**. See §5.2 |
| C5: block parses to AP 141 / SP 638 / 543.6–646.3 @ 3.57, matching `3d`'s hand-typed values | ✅ **EXACT** | the transcription is now mechanically verified, which was the point |
| C5: the contaminated 1.718 / 0.769 targets | ⚠️ **HALF-CLEARED** | re-derived in **3d** at `PHASE_2_simulation.md:473-494`, but `:467-470` still headlines **1.718** as "the target a talent model must reproduce" |
| C3/C4 blocked because `calibrate_vs_log` refuses on a non-paladin log, fail-closed | ✅ **TRUE — and it was fixed in `3d`, not `3e`** | `AlignmentUncheckable` raised on the Mage log; the fail-open `check_alignment()` that `AUDIT_3C` §5 flagged was closed at `2d3db19`. Good: a prior finding actually landed |
| Exit criteria re-read: four unmet, one improved-not-met, two met | ✅ **HONEST** | `content.py:133-163` — 6 presets still `provenance="assumption: …"`, and `content.py` is **not in the `3e` diff**, so no back-filling by analogy occurred. The 🛑 was respected |
| "Your chosen pet scope was not buildable — creature stats are in no client DBC" | ✅ **plausible and correctly scoped** | not independently verifiable without the client, but the reasoning is sound and the route (logs / `ability_performance.is_pet`) is right |

---

## 2. Is the headline result trustworthy?

**Yes, and it is the strongest thing in the session.** Three independent checks:

* **Block A really was instrument-only.** Recomputing the `3d` manifest's bands with the 5
  holdout ids removed gives `164.69 / 143.99 / 64.30 / 63.45 / 63.45` — identical to
  `68779e7`'s manifest to full float precision, and `Mutaforma`'s `1859400.19` is
  unchanged. Nothing about the model moved in A.
* **`corpus_row_counts` is byte-identical across all eight tables** between the `3d` and
  `3e` runs, so no corpus movement could have been observed and then selected against.
* **The id set is order-identical**, not merely set-identical — consistent with a copy,
  not a re-derivation.

That is why "five defects fixed, nothing moved" is evidence rather than noise, and the
session is right to call it the most useful result. The conclusion that follows —
**the residual is not in the mechanisms `3e` repaired** — is sound.

⚠ **One caveat the session does not state.** B1 itself moved the gate 5 → 4 and then it
came back to 5. Seven characters moved and every one moved down; `Chastie`'s `+13.1%` pass
became `−27.9%`. So "the answer did not move" is a *net* statement over a set that did
move, and the net includes at least one pass that was restored by later blocks rather than
never lost. That is fully disclosed in `ENGINE_BUGS.md:79,300,442` — but the headline
table reads as stasis when the underlying rows churned.

⚠ **And one process gap.** B2 (`1c07bab`) shipped with no gate before/after pair, against
`SESSION_3E_PRIMER.md` §0's *"a modelling commit that does not carry a before/after pair is
not finished."* B1, B3, B4, B5+B6 all carry theirs. B2 is also the commit whose message
asserts a discriminator equivalence that §4.4 disproves.

---

## 3. 🔴 The instruments `3e` built that cannot fail

This is the section that matters. `3e` wrote `PLAN_3G_self_verifying_gates.md` — a plan
about exactly this failure class — in the same session it shipped four instances of it.

### 3.1 The rule-1 exclusion guard **cannot run**, and repairing it would not restore it

`3e` A1 changed `candidates()` from `(conn, limit, max_lag_hours)` to
`(conn, cohort_ids, max_lag_hours)` (`calibrate_crawled.py:240`). The guard that proves
`own_capture` characters never enter the gate cohort was not updated:

```
check_gate_exclusion.py:126   before    = cc.candidates(conn, limit=120, max_lag_hours=0)
check_gate_exclusion.py:140   after     = cc.candidates(conn, limit=120, max_lag_hours=0)
check_gate_exclusion.py:160   unguarded = cc.candidates(conn, limit=120, max_lag_hours=0)
```

→ `TypeError: candidates() got an unexpected keyword argument 'limit'`, before any DB
access. It also now returns a 3-tuple, so `[r[0] for r in before]` is wrong even with the
kwarg fixed. **It was not run during `3e`.**

Worse: `inject_privileged_character()` (`:74-79`) deliberately mints the intruder at
`character_id 1` — *"A LOW character_id on purpose. candidates() is ORDER BY character_id
LIMIT N"*. Under a frozen id set, id 1 can never appear **whatever its `source`**, so the
positive checks at `:143-152` would pass for a reason unrelated to
`EXCLUDED_SNAPSHOT_SOURCES`, and the control arm at `:164-168` — "without the filter the
SAME character DOES enter" — would **fail**. The test needs rewriting against the
frozen-cohort design, not repairing.

🛑 This is the guard protecting the standing rule that the owner's own characters must
never inflate the gate cohort — the rule the Mage capture is about to test for the second
time.

### 3.2 E2 was closed on a check that is a constant `True`

```python
check_sim_engine.py:658   warned = any("health" in (w or "").lower()
                                       for w in (m.warnings or []) + (f.warnings or []))
          :661   gcheck("[cp_melee] the execute window is modelled, or the sim says
                         it cannot model it", warned or bool(hp_gated), …)
```

B5 added `EXECUTE_GATING_UNAVAILABLE` (`tiers.py:65-72`) and appends it **unconditionally**
at `tiers.py:425` (fast) and `:635` (medium). Its text contains
`AURA_STATE_HEALTHLESS_20_PERCENT` and *"low-health target"* — so `"health" in w.lower()`
is satisfied for every build, every fixture, forever.

**Failure scenario:** revert `_decay_target_health` entirely, pinning target health at 100
again, and re-run the harness. The check still prints `PASS`. The E2 line was **removed
from `EXPECTED_FAILURES`** (`check_sim_engine.py:62-69`) partly on this pass.

Second, independent vacuity in the same predicate: `hp_gated` (`:653-656`) matches
`health_pct_below` as well as `target_health_pct_below`, and `apl_gen.py:137` emits
`health_pct_below` for **self-sustain heals**. Any board with a heal under a
`self_sustain_required` preset satisfies an *execute-window* check.

### 3.3 An unmeasured hypothesis silently shapes the gate number

`CP_PER_BUILDER_CAST = 1.0` (`tiers.py:48`) divides a finisher's cast count at `:367`.
Its disclosure warning sits at `:379-385` — nested inside `if window < 1.0:` (`:371`),
the *execute-window* branch, not inside `if cp > 0:` (`:352`).

`_health_gate` only matches `target_health_pct_below`, and **`apl_gen` never emits that
condition** — `ENGINE_BUGS.md`'s own E2 entry says so. So for every auto-generated APL —
i.e. every gate run and every fixture run — `window == 1.0`, the block never executes, and
`fast_sim` scales finisher casts by an unmeasured constant in silence. `medium_sim`
(`:562-563`) applies the same hypothesis with **no warning at all**.
`grep -n "retail_hypothesis" core/sim/tiers.py` → one emission site: line 381.

**The gate runs on `fast_sim`** (`calibrate_crawled.py:73,465,469`).

Three documents state the opposite:

* `tiers.py:44-46` — *"assumed HERE, once, under a name, **with a warning emitted by any sim that relies on it**"*
* `ENGINE_BUGS.md:74-76` — same wording
* `ingest/export/seed_epistemics.py:235` — *"a named retail_hypothesis **carrying a warning in every sim that relies on it**"*
* `PROGRESS.md` — *"a named `retail_hypothesis` **with a warning**, like `BASE_GCD`"* —
  and `BASE_GCD` (`tiers.py:34`) emits no warning either.

This is a **rule-2 violation** (never fabricate precision) asserted as satisfied in four
places — the exact failure mode the primer names as most expensive.

Two smaller bugs in the same block: when it *does* fire, `casts` has already been
multiplied by `window` at `:375`, so it reports the health-scaled number as the CP-limited
one; and when `cp == 0` it prints *"held to 0 combo points"*, which is meaningless.

### 3.4 `session_mismatch()` returns "all clear" when it cannot check

```python
core/builds/stat_block.py:192   exported = block.get("exported_at")
                         :193   if exported is None:  return ("… CANNOT be checked …")
                         :199   if log_started_at is None:  return None        # ← silent
```

`None` is the caller's "no problem, stay silent" value (`calibrate_vs_log.py:620-625`). The
block side is handled; the log side is not. `_log_started_at`'s own docstring
(`calibrate_vs_log.py:410-412`) says the opposite of what the code does: *"Returns None if
the name does not match, **and the caller then says it could not check rather than assuming
agreement**."*

Executed:

```
same session            -> None
33h apart               -> '🛑 STAT BLOCK AND LOG ARE 33.8 HOURS APART …'
block has no ExportedAt -> 'stat block carries no parseable ExportedAt … CANNOT be checked'
LOG has no timestamp    -> None        <-- indistinguishable from "same session"
```

Filename regimes that silently disable the check: `WoWCombatLog.txt`,
`06-08-2026-19.16.56 WoWCombatLog.txt` (EU day-first), `2026-08-06 19-16-56 …`. And
`2026-02-30-…` raises an **uncaught** `ValueError` at `calibrate_vs_log.py:420`.

**Failure scenario:** the owner copies a log out under a friendlier name, pairs it with
yesterday's block, and the tool prints its numbers with no warning — reproducing the `2e`
contamination that the session record calls *"the single error worth more than all the
others combined"*. `stat_block.py` has **no test anywhere in the tree**.

### 3.5 The pet check asserts that a pure function is deterministic

`check_sim_engine.py:760-778` computes `detect_summons(conn, [a["spell_id"] for a in
bd["abilities"]])` and then asserts a warning containing `"pet"` exists.
`tiers.py:426/636` compute `pet_gap_warning(detect_summons(conn, [c.spell_id for c in
build_spec.abilities]))`, and `_load_fixture:549` builds `spec.abilities` 1:1 from
`bd["abilities"]`. Same pure function, same ids, both sides. Given the vacuity guard
passes, `pet_warned` is **necessarily** true.

B6 correctly added a vacuity guard and then wrote an assertion the guard makes
unfalsifiable.

### 3.6 `_filler_ids` re-implements a rule B1 changed, while claiming it cannot drift

Docstring (`check_sim_engine.py:555-565`): *"Classified the same way `tiers.py` does, from
the resolved ability's own `cooldown_seconds`, **so the check cannot drift from the code it
tests by re-implementing the rule differently**."*

`fast_sim` no longer classifies on `cooldown_seconds` (`tiers.py:301-307`): it partitions
into `cp_gated` / `bounded` / `unbounded` / `off_gcd`. A cooldown-less pure DoT is
`bounded` and allocated **first**; `_filler_ids` counts it as a filler. This corrupts the
`EXPECTED_FAILURES` bookkeeping text at `:80-93` ("reads 1 of 8 because…"), a count taken
over the wrong set.

Additional vacuous pass: the condition is `len(fillers) < 2 or len(firing) >= 2`. If
`_resolve_all` fails or the field is renamed, `fillers` empties and the check **passes**.
For `cp_melee` that entry is not in `EXPECTED_FAILURES`, so the vacuous pass is silent.

---

## 4. New defects in the code `3e` wrote

Ranked by what they cost.

### 4.1 🔴 The freeze has two exits and only one is reported

`candidates()` answers "does this frozen member still pass the *completeness* filter", and
instruments it well (`drop_reason()` `:285-333` names the mechanism).

The second exit is the scoring loop at `:626-668`: a member is dropped for a `content_type`
with no preset (`:633`), an unresolvable `path` (`:641`), Path of Duality (`:645`), or
**any sim exception** (`:666`). Those land in `excluded`, which is **not** merged into
`dropped`, does **not** appear in `gate_manifest_3e.json`, and is written only to
`data/derived/` (`:977-981`, `:1039`) — gitignored, structurally unauditable.

Meanwhile `:1162` sets `"still_qualifying": len(tuning) + len(holdout)` — the count of
*scored* characters. So two sim errors produce a committed manifest reading
`frozen_size: 41, still_qualifying: 39, dropped: []`, an internally contradictory record,
while stdout `:616` still prints `41 of 41` and the headline denominator quietly becomes 34.

**This was live.** Block B rewrote `tiers.py`, `apl.py` and `apl_gen.py` across five
commits; any one raising on one crawled build would have moved the `3e` before/after pair
by shrinking its denominator, and the only artifact that could catch it is gitignored. It
happened not to bite — the denominator is 36 in both `68779e7` and `7c416d1`. That is luck.

**Fix:** fold `excluded` into the manifest, and compute `still_qualifying` from `len(rows)`.

### 4.2 🔴 The 1,859,400% number is in the newly committed manifest

A2 put the floor on the **aggregate** only. Per-character slice accuracy has no floor
(`calibrate_crawled.py:737-739`) and is written per row at `:1196-1197`:

```
Mutaforma  0.2% coverage  1859400.19
Chastie    4.6%              2371.44
Zaczao     5.6%              1739.20
```

The session record and `PROGRESS.md` both cite *"Mutaforma reports 1,859,400% … and that
value is in the committed manifest"* **as the defect**. It is in the new manifest at the
same magnitude. `PLAN_3G` exit criterion 3 requires every known fail-open instrument to be
fixed **or explicitly recorded as accepted with the reason**; this one is half-fixed and no
doc says so.

Related: `slice_accuracy_by_coverage_band_pct[">=0"] = 163.73` ships in the manifest with
**no `n` and no caveat** — `3d`'s exact error, one key away from the good number. The
generated report carries `n` (`:917-921`); the artifact an auditor actually gets does not.
`>=50` is a median of **8**.

### 4.3 🔴 The `--stat-block`-only path crashes at the end

`calibrate_vs_log.py:888-889` formats the closing NOTE from `args.ap / args.sp /
args.weapon_min / args.weapon_max` — the **flags**, not the resolved `stats` dict used
correctly 275 lines earlier at `:611-614`. On the `--stat-block`-only path those are all
`None`:

```
resolved: {'ap': 30.0, 'sp': 780.0, 'weapon_min': 227.7, 'weapon_max': 253.7, …}
reproducing line 888-889 -> TypeError: unsupported format string passed to NoneType.__format__
```

`:888` is unconditional before `return 0`. So either C5's re-derivation was run **with the
flags as well as the block** — defeating C1's entire point — or a traceback was ignored.
Either way C1's headline invocation does not complete.

### 4.4 🔴 A third DoT discriminator, in the layer that decides priority

Three tests for "is this a DoT" now exist:

| site | test |
|---|---|
| `apl_gen.py:75` | `dur > 0 and _is_pure_periodic(ab)` — decides top-tier placement + gate |
| `tiers.py:220` | `periodic and dur > 0 and _is_pure_periodic(ab)` — the fast_sim bound |
| `tiers.py:583` | `dur and tick_interval_seconds` — decides `st.debuffs` vs `st.buffs` |

`apl_gen.py:73` claims *"Shares `tiers._is_pure_periodic` so the two layers cannot drift
apart"*, and `1c07bab`'s message asserts `:583` uses *"the same mechanical discriminator
`_useful_cast_interval` uses"*. It does not — and it stopped being true the moment B3
added `_is_pure_periodic` to `_useful_cast_interval`.

**Failure scenario:** an ability with a periodic aura whose `EffectAmplitude` is 0 gets
`term["is_periodic"]=True, tick=None` (`mechanics.py:584-585`) while the ability-level
fields get neither (`:320-324`). `_is_pure_periodic` → `True`, `tick_interval_seconds` →
`None`. `apl_gen` files it in the **maintained tier at the top of the APL** gated on
`debuff_remaining_below 1.5`; `:583` routes it to `st.buffs`; `debuff_remaining()` returns
`0.0` forever (`:498-499`); `0.0 < 1.5` is always true; the entry wins **every** priority
scan and consumes the whole rotation. This is the Seal-of-Command 47-of-47-GCDs failure
re-created at the top of the list.

### 4.5 🟠 `_is_pure_periodic` fails open into the over-count, silently

`tiers.py:181-184`: `except Exception: return False`, and `bool(evs) and all(…)`. "I could
not tell" and "I have no events" both return the same value as "definitely not a DoT" —
routing the ability into the **unbounded spam** tier, with `_mixed_damage_warning` also
returning `None` on the exception path (`:246-247`). The safe default here is the bounded
one; the code picked the over-counting one and says nothing. Rule 2 again.

### 4.6 🟠 Target-health decay is capped by `movement_pct`; the two tiers disagree by up to 1.8×

`_decay_target_health` divides by `st.fight_duration` (`tiers.py:117-129`) while the
timeline loop is bounded by `available = fight_duration × (1 − movement_pct)` (`:114`,
`:521`, `:529`). Target health therefore **floors at `100 × movement_pct`**. Every preset
sets `movement_pct` 0.05–0.20 (`content.py:120-162`).

On `world_boss` (0.20) `target_health_pct` never goes below 20.0, so
`target_health_pct_below: 20` is **permanently false in `medium_sim`** — E2's original
symptom, unfixed on that profile — while `fast_sim` credits the ability 20% of its casts.
The fast-vs-medium agreement guard (`check_sim_engine.py:420`, 35% tolerance) runs on the
Paladin fixture only.

### 4.7 🟠 `self_health_pct` is still pinned at 100 — E2's twin, unfixed and unnamed

```
core/sim/tiers.py:471   self_health_pct: float = 100.0
core/sim/apl.py:147     return state.self_health_pct < condition["value"]
```

No writer anywhere in the tree. `apl_gen.py:132-139` emits `health_pct_below` for every
healing ability when `content.self_sustain_required` (`mythic_dungeon_aoe`, `solo_grind`).
Those entries can **never** fire in `medium_sim`; in `fast_sim`, `_health_gate` doesn't
match `health_pct_below` at all, so the same heal is cast at the **full** rate.
*"Unmodelled in both directions at once, and silent about it"* — E2's own words, on the
player side, while E2's registry line was deleted. `content.incoming_damage_dps` (150–300
on those presets) sits unused.

### 4.8 🟠 The Mage fixture has no ground truth — the one thing that justified preferring it

`ADDENDUM_3D_to_3E_mage_capture.md:141-142`: *"A fixture with a verified stat block, a
paired buffed/unbuffed log and a real parse is worth more than a plausible-looking
synthetic one, **because a synthetic fixture can only catch a crash — it has no ground
truth to be wrong against.**"*

`fixtures/build_elric_frost_mage.json` carries `stats_override`, `weapons`, `abilities`,
`talents`, `unresolved` — and **no expected DPS, no per-ability non-crit averages, no pet
share**. All of it exists and is already tabulated in the capture README (Window A:
296,031 player / 15,453 pet / 214.2 s; Frostbolt ×1.027 … Frost Fever ×1.080). None was
carried across. `check_nonpaladin_fixtures()` only `gcheck`s structural properties.

So the Mage arrived as a **third structural fixture**, not as a ground-truth anchor —
exactly the limitation the addendum invoked to justify preferring it. The combo-point
fixture is likewise still assertion-free on magnitudes. **No assertion anywhere in the
harness compares a modelled magnitude to a measured one, on any of the three fixtures.**

### 4.9 🟠 `roll_hit` never got `combo_points`; the stated convergence contract is now false

B4 threaded `combo_points` through `_components → expected_hit → expected_cast` but not
through the RNG path: `ability_model.py:796-797` calls `_components(...)` with the default
`combo_points=0`. `slow_sim` builds its skeleton from `medium_sim` (casts at 5 CP) then
rolls every cast at 0 CP (`tiers.py:809-810`), so a combo-point build's Monte-Carlo mean
and 95% band are centred **below** the medium-sim answer they claim to be the variance of.
The docstring at `:784-785` still asserts convergence *"asserted by check_sim_engine.py"*;
the assertion (`:253-269`) runs at `combo_points=0` and passes vacuously.

### 4.10 🟠 The commit hook measures the working-tree file, not the staged blob

`.claude/hooks/block_large_staged_files.ps1:35-36`:

```powershell
if (-not (Test-Path -LiteralPath $path)) { continue }   # deletion or rename
$item = Get-Item -LiteralPath $path
```

`git diff --cached --name-only` lists staged **paths**; the size read is on-disk.
**Failure:** `git add data/derived/ascension.db` (194 MB), then delete or rebuild it before
committing — `Test-Path` false, `continue`, exit 0, the 194 MB blob is committed. Correct
read is `git cat-file -s :"$path"`.

`.claude/README.md` now says **"✅ THE HOOK IS VERIFIED"**. The owner's test
(`fsutil file createnew` → `git add` → run) exercises only the present-on-disk case, and
the README's honest caveat block names the *other* two gaps but not this one. The script
itself still carries `🛑 UNVERIFIED as written` at `:3-5` — doc drift inside A6.

### 4.11 🟡 Smaller, verified

* **`tiers.py:636-643`** — the pet warning block is duplicated verbatim in `medium_sim`,
  including the DB round-trip. Deduped downstream, so cosmetic.
* **`tiers.py:408-415`** — the `starved` warning asserts *"higher-priority abilities
  consumed the whole GCD budget"* without checking; zero casts also come from
  `occupancy == 0`, `window == 0.0`, or the CP cap. Nine lines later the same run can print
  *"Xs of GCD budget went UNUSED"* (`:417-421`) — two contradictory claims in one output.
* **`tiers.py:139-149`, `:159-167`** — `_cp_gate`/`_health_gate` are first-match-wins on
  duplicate spell entries. `Rupture at 5 CP` **and** `Rupture at 1 CP when falling off` —
  the natural way to write a real rotation — scores every cast at whichever is listed
  first, charges the budget twice (`:386`), and warns about neither.
* **`apl.py:73-79`** — no validation that `combo_points_at_least.value ≤ MAX_COMBO_POINTS`.
  A hand-authored `50` gives `medium_sim` zero casts (fail-closed) and `fast_sim`
  `cp_scaling × 2500` (`ability_model.py:494-499` squares it). The two do not cancel.
* **`ability_model.py:487-499`** — the quadratic CP multiplier (**25× at 5 CP**) is applied
  silently; the warning fires only in the branch where it is **not** applied.
* **`tiers.py:561-563`** — the CP grant sits before `if not entry.off_gcd:` (`:604`), so
  off-GCD entries grant a combo point on **every** scan pass, including idle passes
  (`:613-617`). An `always` off-GCD entry saturates CP within two scans.
* **`core/builds/stat_block.py:74-103`** — a file containing two concatenated blocks is
  silently merged **last-wins** (verified: unbuffed+buffed → `AP 30 / SP 840 / ExportedAt
  19:21:39`, no warning). That is the contamination shape the module exists to prevent.
* **`core/builds/stat_block.py:162-175`** — `require()` has **zero call sites** tree-wide;
  the refusal actually in force is hand-rolled at `calibrate_vs_log.py:474-481`.
* **`calibrate_vs_log.py:441-449`** — the "no ExportedAt" note is gated on
  `exported_at_text`, not `exported_at`, so a present-but-unparseable timestamp prints as
  if it succeeded while `session_mismatch` simultaneously reports it cannot check.
* **`calibrate_vs_log.py:186-220`** — the alignment gate is correctly fail-closed with **no**
  anchors (3d's fix survives), but returns "OK" when only the `Melee` crit anchor clears,
  and that anchor accepts anything in `0.05 < rate < 0.95`. The `2e` glancing-vs-critical
  bug lands comfortably inside that band. `anchors_checked` is printed, so it is disclosed.
* **`calibrate_crawled.py:474-476`** — `_median` returns the *upper* median for even n while
  `slice_accuracy_bands:493` uses `statistics.median`. Every decomposition figure uses a
  different estimator than the headline. And `_median` returns `None` on an empty list,
  formatted directly at `:541` → `TypeError` if no character reaches ≥99.9% gear coverage.

---

## 5. Docs vs tree

### 5.1 The `CALIBRATION_TOLERANCE.md` band table is mislabelled and three of five `n` are wrong

The committed table (`:166-172`) is headed **"n (3e tuning set)"**:

| floor | doc `n` | doc median | **recomputed from `gate_manifest_3e.json`** |
|---|---:|---:|---|
| ≥0% | 33 | 164.7% | 33 · **163.7%** |
| ≥10% | **27** | 144.0% | **26** · **141.2%** |
| ≥20% | 23 | 64.3% | 23 · 64.3% ✅ |
| ≥30% | **21** | 63.4% | **20** · 63.4% |
| ≥50% | **10** | 63.4% | **8** · 63.4% |

My recompute matches the manifest's own `slice_accuracy_by_coverage_band_pct` exactly, so
the tool is right and the table was hand-typed. Running the same computation over the **3d**
manifest minus the holdout gives `33 / 26 / 23 / 20 / 8` at `164.7 / 144.0 / 64.3 / 63.5 /
63.5` — so **the doc's medians are the 3d numbers wearing a 3e label**, and its `n` column
matches neither. Nothing material changes (the conclusion is robust), but the project's
reference table for its biggest retraction does not describe the run it names.

*(The parenthetical at `:174-177` — "computed from the committed 3d manifest, 159.8 / 85.4 /
62.6 ×3 over 38" — reproduces **exactly**. That part is right.)*

Also unresolved: `calibrate_crawled.py:110` and the manifest's own
`successor_floor_justification` both say **62.6%** where the headline says 64.3%. Both are
honest readings of different populations, but they sit unlabelled next to each other.

### 5.2 "Blizzard casts 0 / 0 / 305" is a grep line-count, and 27% of it is an enemy's

`ENGINE_BUGS.md:398` records a column headed **"Blizzard casts" = 305** for Window C;
`Session_2026-08-06_3e_modelling.md:196,217` repeats it and uses it to justify C4's spill.
Measured from the log:

```
Blizzard lines in Window C: 305   →   Elric 222, Scarlet Sorcerer 83
Elric only:  SPELL_CAST_SUCCESS 4 · SPELL_DAMAGE 134 · AURA_APPLIED 31 · REFRESH 20 · FAILED 2
Elric Blizzard = 4 casts; 88,132 of 940,460 spell damage = 9.4%
```

**Elric cast Blizzard 4 times.** The conclusion survives — Window C *is* E8-exposed and
A→B is not — but a number that is wrong by 76× sits in the durable bug registry as the
sizing of an engine gap. Worth a correction line, not a rewrite.

### 5.3 Stale citations, including two that `3e` falsified in-session

* `ENGINE_BUGS.md:469` cites `calibrate_crawled.py:73,465,469` — correct at `200f79f`,
  wrong at `68779e7` (the commit that "fixed" it moved them to `:82,658,662`). Still wrong.
* `ADDENDUM_3D_to_3E_mage_capture.md:33` asserts five flags are `required=True` — true when
  A6 wrote it, falsified three commits later by `3e`'s own C1.
* `PHASE_2_simulation.md:467-471` still headlines **1.718** as *"the target a talent model
  must reproduce"*; the corrected 1.704 appears only inside a blockquote at `:488`. Same at
  `PHASE_2D_residuals_and_scorecard.md:10,158`.
* `PHASE_2_simulation.md:496-503` now describes a tool that no longer exists — *"it refuses
  to run without `--ap --sp --weapon-min --weapon-max --weapon-speed`"* with a repro command
  using them. `git log 200f79f..c86eb7f -- primer/PHASE_2_simulation.md` is **empty**.
* `check_sim_engine.py:621,647` cite `tiers.py:197`, `:198-199`, `apl.py:118`. Those live at
  `tiers.py:469-472` and `apl.py:144` now — new stale citations added by A6's own session.
* `seed_predictions.py:221,223` and `cli/rebuild.py:91` still name `--limit 120` and
  *"`candidates()` is `ORDER BY character_id LIMIT 120`"*. (The `seed_predictions` row is a
  pre-registration ledger and arguably must **not** be edited — but then it needs a
  superseded-by note.)
* **Five older docs still assert the retracted `casts` claim**, unmarked:
  `PLAN_3C_clean_exit.md:363`, `AUDIT_3C_handoff.md:141-143`,
  `Session_2026-08-06_3c_paired_upload.md:34-45` (*"crawl casts/sec is a faithful
  character-level APM measure"* — falsified for 22 of 41 cohort members),
  `NEXT_CAPTURE.md:83-84`, `AUDIT_3C_ADVERSARIAL.md:43`. Two of those are live reference
  docs named by the monitoring primer.
* `ADDENDUM_3D_slice_accuracy_correction.md:1-7` still reads *"Urgency: before `3e` runs"* —
  it landed; the doc does not say so.
* `Session_2026-08-06_3d_hygiene_and_instrument.md:31,204` still carry the 160% reading with
  no pointer to the correction.

### 5.4 Capture protocol — 5 of 7 items unrecorded

`ADDENDUM_3D_to_3E_mage_capture.md:153-187` vs the capture README:

| §5 item | |
|---|---|
| Same dummy runs 1 & 2, recorded which | ✅ README:38, verified from logs |
| **Stat export INSIDE the dungeon, buffs up, start and end** | ❌ not done, not noted — last export 19:21:39, Window C starts 19:45:40 |
| Note any death, roughly when | ❌ unrecorded (recoverable: 0 `UNIT_DIED.*Elric` in all three) |
| Note OOM, roughly when | ❌ unrecorded |
| Note whether any channel was in the rotation | ❌ unrecorded — Blizzard was found later, from the log |
| Note Shatter / freeze-dependent crit | ❌ unrecorded, and material: Ice Age, Absolute Zero, Deep Freeze against a CC-immune dummy |
| Mark which pulls were bosses | ❌ declared unmet, README:52-53 |

The missing in-dungeon export is load-bearing beyond bookkeeping: the addendum sells pair
2→3 as *"same character, same buffs, same block; the only variable is content."* With the
last export 24 minutes before Window C, **"same buffs" is an assumption, not a
measurement** — and `session_mismatch`'s 6-hour tolerance would wave that pairing through.

---

## 6. The eight rules, and retractions

| # | Rule | Status after `3e` | Evidence |
|---|---|---|---|
| 1 | No value without provenance | ✅ **still fixed** | `core/db/schema.py:68,85-104` all `NOT NULL`; `3e` did not touch `core/spells/` or `core/db/` |
| 2 | Never fabricate precision | 🔴 **new violation** | `CP_PER_BUILDER_CAST` (§3.3) + `_is_pure_periodic` failing open (§4.5). Four docs claim the warning fires |
| 3 | Conflicts surfaced, never auto-resolved | ✅ **still fixed** | `core/spells/mechanics.py:176-184,417-448,853-861`, untouched |
| 4 | Never read a DBC description for a magnitude | ✅ **no regression** | `stat_block.py` parses an addon export, the admissible class per `CLAUDE.md:131-136`. ⚠ It carries **no check digit**, unlike the weapon-damage precedent that rule cites — inside the letter, outside the spirit |
| 5 | Never string-match to identify a spell | ✅ **improved** | B6's `detect_summons` is a real fix and the both-directions evidence is genuine. Residual (pre-existing): `calibrate_crawled.py:406-411` parses the ability name for the auto-attack tag, but self-checks against `spell_school` |
| 6 | Stop and ask rather than guess | ✅ | the three data gaps (effect 40, `TargetAuraState`, `creature_template`) are each named with a resolution route, not filled |
| 7 | Retract explicitly, with the reason recorded | 🟠 **partial regression** | the 160%→64% sign reversal is in three prose docs and **zero `RETRACTIONS` rows** — `git diff` adds 6 `QUESTIONS`, 0 retractions; the table holds 32 and none mentions slice accuracy. `/close-session`'s own rule: *"Prose is not a seed."* This matters because `PLAN_3G:113` designates `RETRACTIONS` as the regression set for `3g` |
| 8 | Pure logic layer | ✅ **verified by running it** | `check_core_purity.py` → **49 files, 0 violations**. New `pets.py`/`stat_block.py` clean; `apl_gen → tiers` adds no cycle |

**Retracted-claims regression sweep: clean in `3e`'s own docs.** All seven primer-v2
retractions are either absent or quoted-to-retract in `PROGRESS.md`,
`Session_..._3e_modelling.md`, `ENGINE_BUGS.md`, `SESSION_3E_PRIMER.md`, `PLAN_3G`,
`PLAN_V2`. The only survivals are in older docs (§5.3).

**🛑 stop-points: substantively respected, none logged as asked.** Ten markers; all ten
outcomes are consistent with the constraint (Holy Shock untouched — `git diff … | grep
"0.2145"` returns nothing; `bugs/` unmoved; no pet damage model; the six presets left as
assumptions). But `PROGRESS.md`'s "Blocked on the user" table was **not modified by `3e` at
all**, against `START_HERE_FOR_CODE.md:104` step 4. The one worth naming: the 20% successor
floor is attributed to the owner three times, and it is numerically identical to
`SLICE_COVERAGE_FLOOR_PCT = 20.0`, the constant Code itself chose in A2, justified in
Code's own voice at `calibrate_crawled.py:125-131`. Probably fine; unverifiable from the
repo.

**Also: a `C2` naming collision, one session after `B1` renamed `T1…T13 → C1…C13` to fix
exactly this.** `SESSION_3E_PRIMER.md:120` and `FINDINGS_3e_preflight:66` point the
`casts`-provenance finding at *"C2's admissibility filter"* — which is `PLAN_3C`'s C2, and
`PLAN_3C_clean_exit.md:100,402-407` **closed it as a dead end in `3c`**. `SESSION_3E_PRIMER.md:234`
uses `C2` for the Frost Mage fixture. Same token, two meanings, 114 lines apart.

---

## 7. 🚨 Time-critical — the 2026-08-08 phase flip

**The crawl half is genuinely fixed and I verified it by execution.** One definition
(`season_config.py:51-58,69`); all five `AUDIT_3C` §4.K hardcode sites now import it. Fed a
synthetic Phase 2 payload:

```
RAISED: RealmSeasonMismatch
PHASE FLIP DETECTED. … the server's active top-level phase is
'Phase 2 - Ruins of Ahn Qiraj' … Records are NOT being captured until that is done
--- transition state (both phases active) ---
RAISED: expected exactly ONE active top-level phase, found 2
```

It fires **before** any record is written (`crawl_ascensionlogs.py:315-321,844,886`), exits
**2**, and `run_crawler_scheduled.bat:57-65` has a dedicated exit-2 message. `3e` did not
touch any of it — `git diff --stat 200f79f~1 c86eb7f -- season_config.py tools/scrapers/
core/builds/gear.py tools/scheduling/` is **empty**.

**Two exposures remain.**

1. **`gear_tier_stats` will silently blend phases.** `core/builds/gear.py:128-131` writes
   the literal `None` into `phase_label` on every row of the only writer. No other writer
   exists; the source table has no phase column (`corpus.py:77-96`); `gear_tier_stats()`
   (`:335`) never selects or filters on it and returns a hardcoded caveat string at `:409`.
   Its own docstring predicts the outcome at `:350-355`: **a Phase-1 BiS will be reported as
   current.** So: loud failure on the crawl, then a silent mis-read on gear from the moment
   the constant is bumped.
2. **The irreplaceable baseline is the thing the tripwire can block.**
   `tools/scrapers/baseline_phase1.py:44` calls `crawler.crawl_phases(writers)` and
   inherits the assertion, but `main()` does **not** catch `RealmSeasonMismatch` — it dies
   on a raw traceback. It is scheduled 2026-08-07 20:00 (`SCHEDULING.md:128-132`). If the
   API flips its active record even hours early, the guard blocks the one capture that
   cannot be redone, and the owner sees a stack trace rather than the refusal banner.

**And `3e` dropped the reminder from the live docs.** `PROGRESS.md`'s only Phase-2 line is
`:194`, inside a `<details>Superseded</details>` block (`:180-247`). The live top block and
"FIRST ACTIONS NEXT SESSION" carry **no** mention of 2026-08-08.

---

## 8. The two new plan documents

### `PLAN_3G_self_verifying_gates.md` — ⚠ sound, and already stale about its own tree

The design is right, and unusually well-guarded: the three-verdict requirement
(`:44-46`, `INSUFFICIENT_DATA` as the point) is the correct generalisation of this whole
failure class; `:66-71` explicitly refuses to fit the instrument to its test set; `:111-112`
requires every gate to have a test that makes it **fail**; `:117` forbids weakening an
existing check. Its pushback on the inline-tag proposal (`:87-105`) is correct for the right
reason.

Two defects:

* **`:30-32` states a fixed defect in the present tense.** *"`within_tolerance` at
  `calibrate_crawled.py:494` has no coverage floor, so a character the sim models nothing
  for can score a pass."* The line reference is dead (the code is at `:696-698`) and `3e`
  A3 fixed the consequence **in the same session this doc was written**. So exit criterion
  3 ships pointing at an instrument already closed — while §4.2 above shows a *different*
  half of the same instrument is still open and is not on the list.
* **`:42,73` propose `scripts/gates/` and `scripts/phase_runner.py`.** `scripts/` appears
  nowhere in `ARCHITECTURE.md:225-260`, `CLAUDE.md` or `INDEX_GUIDE.md`. `tools/audit/` is
  the established home for exactly this. `:56-58` states the convention as if it existed.

### `PLAN_V2_BLIND_REDERIVATION.md` — ❌ the blind test is not blind

**The scoring key is inside the permitted input set.** Step 2 (`:57,60-62`) makes the
`known_answer` column the thing that turns this from a demo into a test and says it "must be
filled from the seeds". Step 3 (`:73`) then lists v2's permitted inputs as *"the current
capture, **the databases**, the crawl corpus, the sim"*, excluding only the frozen doc and
session records that quote it.

But the databases **are** the answer key. `RETRACTIONS` names v1's graded claims verbatim
and by slug — `sword_specialization_zero_output`, `duality_sp_amp_not_applying`,
`improved_cleave_is_low_value_because_the_flat_is_small`, `art_of_war_dead_slot`, … —
precisely the ones cited at `:21-23` as v1's known-wrong claims. A v2 session with DB access
learns, before deriving anything, that Sword Specialization is not zero-output. Step 4's
flagship outcome (`:83-85`, *"v2 reproduces a retracted v1 claim → the single most valuable
outcome the test can produce"*) is the cell the leak most directly suppresses: v2 will avoid
retracted claims because it can look them up, and that will read as v2 having improved.

**Fix, cheap, and it must be stamped before v2 runs:** either (a) exclude v1-derived
`retractions`/`confirmed_facts` slugs from v2's DB view and list them by slug in the
pre-registration, or (b) accept the leak explicitly and score only the open claims,
downgrading the retracted ones to a sanity check. The doc does neither and does not
acknowledge the tension.

**Also `:20` — "`retractions` holds 24 rows"** is wrong; the tree holds **32**, and held 32
before `3e` started. It is load-bearing: the count is the doc's argument for why v1 is a
good evaluation set, and it feeds `PLAN_3G:113`'s "one regression test per `RETRACTIONS` row".

**Otherwise sound.** `:86-88` (scoring v2's *silence* as an improvement, "or the test
rewards overconfidence") is a genuinely good guard, and the `record_prediction`-refuses-to-
overwrite-a-slug mechanism is the right pre-registration primitive. `CLAUDE.md`'s 49-line
diff was checked: it **removes** the stale Hammerdin build doc from auto-load and changes no
rule — the hard-rules block `:124-158` is byte-identical to `200f79f`.

---

## 9. The corrected plan for `3f`

**Step 0 — repair the instruments, before any of them is trusted again (~half a session)**

| | task | why |
|---|---|---|
| 0.1 | **Rewrite `check_gate_exclusion.py` against the frozen-cohort design** — not repair the signature | §3.1. It cannot run, and a signature fix would make it pass for the wrong reason |
| 0.2 | **Move the `CP_PER_BUILDER_CAST` warning out of the health branch** into `if cp > 0:`, and emit it from `medium_sim` too | §3.3. Rule-2 violation currently shaping the gate number |
| 0.3 | **Make the E2 and pet checks falsifiable** — assert on the *decay behaviour* and the *summon detection*, not on a substring of an unconditional warning | §3.2, §3.5. Both closed defects rest on them |
| 0.4 | **`session_mismatch()`: return a "cannot check" string when the log has no timestamp**, and catch the `ValueError` at `calibrate_vs_log.py:420` | §3.4. Fail-open on the one check the project rates highest |
| 0.5 | **Fix `calibrate_vs_log.py:888-889`** to read the resolved `stats` dict | §4.3. C1's headline invocation crashes |
| 0.6 | **Fold `excluded` into the manifest; compute `still_qualifying` from `len(rows)`** | §4.1. A committed artifact can currently contradict itself |
| 0.7 | **Floor or annotate per-character slice accuracy**, and put `n` beside every band in the manifest | §4.2. The number `3e` exists to retract ships in the manifest that retracts it |
| 0.8 | **One `RETRACTIONS` row for the slice-accuracy sign reversal** | rule 7, and `3g`'s regression set depends on it |

**Step 1 — the phase flip, this week**

| | task |
|---|---|
| 1.1 | 🚨 **Wrap `baseline_phase1.py`'s `main()` in a `RealmSeasonMismatch` handler** that prints the refusal banner and a clear "run me before the flip" instruction — **before 2026-08-07 20:00** |
| 1.2 | Decide what `gear_tier_stats()` does after the flip: a `phase` parameter, or a hard refusal. Silent blending is the current behaviour and its own docstring predicts the failure |
| 1.3 | Put the 2026-08-08 line back in `PROGRESS.md`'s **live** block |

**Step 2 — give the fixtures something to be wrong against**

The single highest-leverage item, and it is the same one `AUDIT_3C` §5 named: **no assertion
in the harness compares a modelled magnitude to a measured one.** The Mage capture's Window A
totals and seven per-hit ratios are already tabulated in the capture README. Put them in
`fixtures/build_elric_frost_mage.json` as a `ground_truth` block and assert against it, even
loosely. Until that exists the three fixtures can only catch crashes, and `3e`'s own §4.4,
§4.6 and §4.9 are exactly the class of defect a magnitude assertion catches and a structural
one does not.

**Step 3 — then `3f` (PHASE_3 T6) or `PLAN_3G`**

`PLAN_3G` first is defensible **only if Step 0 is folded into it**, since Step 0 is 80% of
`3g`'s stated scope discovered concretely. Then log ingestion.

---

## 10. Open decisions for the owner

1. **`PLAN_V2`'s leak.** It must be stamped before v2 runs, and only you can choose between
   blinding the DB view and rescoping the scoring. Doing neither converts "v2 read the
   answer" into "v2 measured the answer" — the exact laundering the plan exists to detect.
2. **`gear_tier_stats` after Saturday.** Blend silently (current), take a `phase` argument,
   or refuse. This is a two-day decision.
3. **The 20% successor floor.** The mechanics are right and the direction is right. If the
   attribution in the session record is accurate, log it in `PROGRESS.md`'s blocked table
   retroactively so the next auditor does not have to raise it again.
4. **Ground truth in fixtures.** You are the only source of it, and the Mage capture already
   contains it. My recommendation: this before any further modelling work.
5. **The `casts` retraction sweep.** Five older docs still assert the falsified claim, two of
   them live reference docs. Cheap to fix, and `3c`'s handoff is one of them.

---

*Not verifiable from the repo (gitignored `data/derived/`, no `.db` committed): the gate's
underlying corpus, the fixture pass/fail matrix, whether `check_gate_exclusion.py` fails
**only** on the `TypeError`, and the creature-stats claim. The committed
`gate_manifest_3e.json` is a real improvement — every headline number `3e` states in prose
reproduces from it, and the only arithmetic error I found anywhere in the session is the
hand-typed band table at `CALIBRATION_TOLERANCE.md:166-172`.*
