# AUDIT `3i` — ADVERSARIAL

> **`FINDING`** — the audit of session `3i`, written 2026-08-07 from a fresh clone at
> `2de79e5`. Method: clone, diff `eaa7604..HEAD`, read the code, run the harness, and
> apply real source-edit mutations to every arm `3i` claims to have repaired. Claims
> not reproducible from the clone are marked as such.

**Verdict in one line:** `3i` did the hard part — it fixed a real corpus defect at the
right layer, applied a rule that cost it its only passer, and reported a falsified
pre-registration without rescuing it quietly. **But the single change that moved the
blind roster is the one change with no pre-registration, and its every arm points one
way; the gate fails OPEN if the stamp↔code assertion trips; and the document half is
now the weaker half for the third consecutive session — including `CLAUDE.md`, the file
loaded before anything else.**

**Closing gate as committed:** `0 of 36 within ±20% · 0 qualified · slice 26.31%
(n=23)`. Reproduced from `predictions/gate_manifest_3e.json`, not re-run: no `.db` is
committed.

---

## §1 — What `3i` earned (short, because it is real)

* **E15 fixed at the right layer.** Verified by executing `ingest_abilities_record` on a
  synthetic record: the pet restatement lands in `pet_ability_damage`,
  `ability_performance` gets owner rows only, and `dps` is no longer
  `(total_damage + pet_damage)/dur` (`core/builds/corpus.py:434-478`, `:619-665`).
* **The P1-FALSE algebra is sound.** Independently re-derived: with
  `slice = (100+δ)/coverage`, `slice_new/slice_old = M_old/M_new` — the total-damage
  terms cancel and the 19.8% consumer-dedupe anchor genuinely was an internally
  inconsistent intermediate. The prereg (`predictions/prereg_3i_e15.md`, `1f9c05e`) is
  the direct parent of the fix and was **never retro-edited** (`git diff` is empty).
* **Predicates 4 and 5 are now computations, not `print()`s**
  (`tools/audit/parse_admissibility.py:330-339`, `:356`), and predicate 4 resolves
  *capture* timestamps — so it correctly continues to remove nobody on the 8th. The
  `3h` hardcoded-date trap is closed. `resolved_entries` now prints (`:436-448`).
* **The doc-sync parser does not fail open on a parse-zero.** Two reformat mutations of
  `ENGINE_BUGS.md` (`## E`→`### E`; `| **Check** |`→`| **Check(s)** |`) each go RED via
  set equality against a non-empty `EXPECTED_FAILURES`. M31 verified RED by a real doc
  edit. Baseline `claimed=10, registered=10`, matching the claim.
* **E1, E4, E5, E6 verified RED under real source edits.** E4: `mv predictions /tmp` now
  `FAIL [A5] (0 files)` where it previously passed vacuously. E5: a prose-`LIVE` file
  with no status line is now UNCLASSIFIED.
* **`predictions/per_ability_summary.json` is genuinely tool-produced and internally
  consistent.** Key-for-key the dict literal at `per_ability_accuracy.py:476-513`; every
  arithmetic identity closes (415 = 123 + 292; 63.9 + 24.8 + 11.3 = 100.0; per-character
  `keyed+absent` = 100 ± 0.15 on all 36). `git_sha 9311a04` is the parent of the commit
  that added it — the "clean tree, then commit" shape. **This closes the `3h` audit's
  item 2** (the headline distribution living only in gitignored `data/derived/`).
* **The phase check ran first, read-only, before any gear tier was read**, against the
  live endpoint, and the flip had not happened. STOP-POINT 0 correctly did not trigger.

---

## §2 — 🚨 TIME-CRITICAL, tonight: the flip now takes the whole cohort inadmissible

The boundary arms `2026-08-08T00:00:00Z`. `3i` wired predicate 4 into a resolver whose
**first** branch is payload-level, not capture-level:

```
core/builds/phases.py:233-234
    if refuse_reason:
        return None, refuse_reason
```

`refuse_reason` is `phase_guard`'s verdict on the `/api/phases` **payload** — "this no
longer describes the server we think we're pointed at". `admissibility_for` passes it
straight through (`parse_admissibility.py:321, 337-339`), so on refusal **every** member
gets `flags.append("unresolved phase: …")` (`:349-350`) → `within_tolerance = None`
(`calibrate_crawled.py:947-949`).

The chain fires on the first crawl on or after the 8th with **zero code changes**:

1. `crawl_ascensionlogs.py:320-321` writes the phases payload to disk **before**
   `season_config.assert_phase(d)` raises — so the post-flip payload lands even though
   the crawl dies.
2. `build_builds_db.latest_phase_context():63-82` takes the **newest** payload.
3. `phase_guard` sees active top-level ≠ `EXPECTED_PHASE_NAME` → refuse reason.
4. Gate reads **0 of 36, all 36 NOT ADMISSIBLE, all on the identical reason.**

Benign today, verified: newest payload is `data/source/crawl/2026-08-06/phases.jsonl.gz`,
single active top-level `Phase 1 - Zul'Gurub`, boundary armed, `boundary_passed_yet:
False`.

This is the *opposite* failure from `3h`'s fail-open, but it is the same category error:
the rule answering a question about the **labelling infrastructure** as if it were a
question about the **parse** — which `CLAUDE.md`'s own "excluded for what its PARSE is"
clause forbids.

**Fix before the next gate run:** separate payload-refusal from capture-unresolvable in
`admissibility_for`, and make a cohort-wide identical flag a loud refusal (the gate
should decline to publish a number, not publish `0 of 36`).

---

## §3 — 🚨 The gate fails OPEN, and then asserts the rule was applied

```
tools/audit/calibrate_crawled.py:830-837
    if not pa.assert_stamped_thresholds():
        print("🛑 REFUSING to apply the admissibility rule — …")
        pa = None            # ← and the run continues
```

`parse_admissibility.py:384-388` returns 1 as a standalone tool. **The gate — the thing
with consequences — proceeds without the rule.** And:

```
tools/audit/calibrate_crawled.py:1581
    "parse_admissibility_rule_applied": True,     # hardcoded literal
```

`write_gate_manifest` takes no parameter reflecting whether `pa` was `None`; rows fall
back to `not_admissible: False` via `.get()` defaults (`:1841-1845`). **A stamp/code
drift therefore produces a committed manifest asserting a rule that did not run, with
every row silently admissible.**

This is exactly the defect class `3h`'s A3 assertion (`:1889-1901`) was added to
prevent — `criteria_in_force` describing criteria the result was not computed under —
reintroduced two blocks later in the same session, and not covered by that assertion,
which only checks the coverage floor key.

---

## §4 — 🚨 The comparator tightening: not pre-registered, and every arm points one way

**Commit order, verified:**

| commit | time | what |
|---|---|---|
| `2b6c615` | 11:26:39 | the D5 comparator change — **its own message already states the effect**: *"5 of 41 (now 3 of 41, see below)"* |
| `801d612` | 11:26:46 | `predictions/prereg_3i_admissibility.md`, **7 seconds later** |

The prereg's body confirms the effect was known when it was written (*"Re-run blind
table: 3 of 41 flagged… Robottikyrpa and Frediib no longer carry a confident APM ratio"*).
So the pre-registration covers the **wiring** step (P1–P4, all about `within_tolerance`).
**The roster-moving change has no pre-registration at all.**

Effect, from the committed manifest:

| character | `within_tolerance` | `not_admissible` | flag |
|---|---|---|---|
| Nodding (10456) | None | true | window 52s < 60s |
| Boomcat (16501) | None (**was true**) | true | apm_ratio 0.24 |
| Deyindra (20461) | None | true | apm_ratio 0.22 |
| **Robottikyrpa (11591)** | **false** | **false** | **[]** |
| **Frediib (40568)** | **false** | **false** | **[]** |

Under the predicate `prereg_3h_boomcat.md` P9 actually registered: **0 failing removed,
1 passing removed, 1 not-scoreable removed.** That is verbatim the asymmetry `CLAUDE.md`
calls *"a fitting device, and the asymmetry proves it."* The full rule's falsifiability
bar survives only via `Nodding`, flagged by a different predicate D5 never touched.

**And the direction is structural, not incidental.** `:286-293` — self-overlap,
`< MIN_PARSE_SECONDS`, trash-tainted — each arm can only *remove* comparators, moving a
character toward `len(apms) < 2` → refused → admissible. Excluding trash also strips
high-APM AoE scopes, lowering the comparator median and *raising* the tested ratio →
fewer flags. **No arm of the change can add a flag. Nothing checked that.**

**The stated rationale for the third arm is inverted.** `:257-260` claims admitting a
legitimately-0.0 comparator is *"exactly the death-deflation signal this predicate exists
to detect."* The deflation signal lives on the **tested** scope. Admitting a 0.0
**comparator** drags the median toward zero, which **raises** the tested ratio and
**hides** deflation.

To `3i`'s credit, the departure is stated plainly and not buried
(`prereg_3i_admissibility.md`; `CALIBRATION_TOLERANCE.md:361-380`: *"the narrow
predicate's evidence for stamping has evaporated"*). The problem is not concealment. It
is that a measurement-then-record was recorded in the slot reserved for a prediction.

---

## §5 — The stamp↔code assertion is blind to the change that moved the roster

`assert_stamped_thresholds()` (`:95-122`) regex-matches **three numbers** anywhere in
`CALIBRATION_TOLERANCE.md` against three module constants. All three match; the named
mutation (`APM_RATIO_BOUND = 0.4`) does go RED. It cannot see:

* the comparison **direction** (`<=` → `<` at `:342`);
* the **comparator definition** — the stamp says *"half the median of the character's own
  **other scopes**"* (`CALIBRATION_TOLERANCE.md:317-318`); D5 replaced that with a
  filtered subset and left the stamped text unchanged;
* deletion of the filters at `:286-291`; `median` → `mean`; whether predicates 2/4/5
  exist at all.

**Demonstrated false-green:** deleting the *entire* stamped predicate-1 block (lines
317-322) leaves the check GREEN — the regex then matches the D7 correction's own
*quotation* of P9 thirty-six lines below and still returns `0.5`. The assertion is not
anchored to the stamped section, so it passes on a document that no longer stamps the
rule.

---

## §6 — Block C is dormant by construction, and `PROGRESS.md` implies otherwise

The repair itself is real and deterministic: one policy (`AND is_pet = 0`, `:173-178`),
residual merge at `:234-239` with `sorted()` names, `raise AssertionError` at `:286-292`
sitting outside the only `try/except`.

But after Block B, `ingest_abilities_record` writes `is_pet` as a **constant 0**, so the
filter is a no-op *by construction*; and the session record itself states there were
**zero** duplicate groups on the post-B corpus (`Session_…_3i_gate_repair.md:145-148`),
so the merge branch never executes either. **The 62.2% → 63.9% move is Block B's, not
Block C's.**

The session record discloses this honestly, three paragraphs later.
**`primer/PROGRESS.md:22-29` — the LIVE document — does not**: it packs *"REPAIRED
(C1–C7) … Re-run, prereg CONFIRMED: absent share moved UP (62.2% → 63.9%)"* into one
bullet that reads as the repair producing the move.

Related, same file:

* **ε = 0.5pp is coarse** for an invariant guarding a numerator drop that was typically
  small.
* 🚨 **`--char` silently overwrites the committed cohort artifact.** `:301-304` accepts
  the flag, `:321-327` filters, `:514-516` writes `predictions/per_ability_summary.json`
  unconditionally on a clean tree — and **nothing in the JSON records that a filter was
  applied.** A one-character debugging run replaces a cohort-wide artifact with a partial
  one that looks cohort-wide.
* The summary **prints a dirty-tree refusal and continues, exit 0** (`:518-523`), where
  the manifest **raises** (`calibrate_crawled.py:1540-1548`) — the docstring's "same
  dirty-tree discipline as the gate manifest" (`:25-26`) overstates it. It also carries
  no cohort identity, while the *gitignored* sibling does (`:528`).
* The 58.4% phantom-production cell is **measured** (`:394-397`), but it is a cohort
  **total** share weighted by absolute sim damage — characters on longer presets
  (`fight_duration` spans 12.0–300.0) dominate, which is the units problem the tool's own
  docstring insists on avoiding. No per-character split, so concentration is unverifiable.

---

## §7 — E15's residue: no migration, unguarded consumers, a fixture that cannot fail

1. **No migration, no schema version — legacy DBs still double-count.** Measured against a
   retained pre-`3i` `builds.db`: `init_schema` is `CREATE TABLE IF NOT EXISTS` only
   (`corpus.py:237`), `PRAGMA user_version` is 0 and never set, no backfill, no
   `DELETE FROM ability_performance WHERE is_pet=1`. Legacy rows survive; `pet_damage`
   silently becomes **NULL** (correlated subquery over an empty side table). These
   consumers have **no `is_pet` filter** and still double-count on a legacy DB:
   `corpus.py:670-677` `compute_damage_share` (feeds `core/builds/search.py:133-138`);
   `tools/scrapers/scrape_ascension_db.py:83` `demand_list` (ranks scraper priority);
   `tools/audit/build_extract_scope_request.py:63` (drives DBC extract requests).
   Mitigated only by `build_builds_db.py:130-131` unlinking the DB each build. The code
   has no guard.
2. **The E15 check cannot fail.** `check_e15_pet_row_double_count`
   (`check_sim_engine.py:1130-1170`) builds its own in-memory table and exercises only
   `modelled_damage_share`'s filter — green regardless of what `ingest_abilities_record`
   does. Nothing asserts "0 `is_pet=1` rows in the real corpus" or "`pet_ability_damage`
   is non-empty", and `build_builds_db.py:253-256` omits the new table from the census
   printout. A silently-broken pet ingest yields `pet_damage = NULL` everywhere and
   prints nothing. **Fail-open.**
3. **A false safety claim in a comment.** `per_ability_accuracy.py:171` says *"the C2
   assertion below makes any recurrence loud instead of silent."* It cannot: the query at
   `:174-179` filters `is_pet = 0` **before** the invariant is computed, so returning
   `is_pet=1` rows would be excluded from numerator and denominator alike and
   `share_sum` would still hit 100.0.
4. **Pet-only characters silently vanish (measured).** `compute_encounter_performance`
   selects `FROM ability_performance` (`:650`) and `_seen_character` is only called for
   `rows[]` players (`:441`) — a character present only in `pet_spell_damage_by_owner`
   now produces **0** `encounter_performance` rows and is absent from `characters`.
   Pre-fix it got a row with `dps = pet_damage/dur`, clearing the `ep.dps > 100` cohort
   filter (`calibrate_crawled.py:250`). Undocumented cohort-composition change.
5. **Latent double-count vector in both tables.** SQLite permits NULLs in rowid-table PK
   columns, so any row where `_int_or_none(spell_id)` returns `None` escapes
   `INSERT OR REPLACE`. Measured: 3 ingests of one record → 3 rows / 3000 damage in
   `ability_performance`, straight into `total_damage → dps →` the gate. **Reachable:
   5 report ids (79, 104, 105, 106, 107) appear twice across the committed crawl days**,
   and `spell_id` is a string field in the source payload. Pre-existing, not a `3i`
   regression — but live, in the very table E15 was closed on.
6. **Four documents still print the old formula as current**, one of them into a
   user-facing string: `core/sim/pets.py:103-104`; `ingest/export/seed_epistemics.py:244`
   (seeded into the epistemics DB — **and this file was edited in `3i`**);
   `check_sim_engine.py:1410-1412`; `ENGINE_BUGS.md:367`.

---

## §8 — Block E: the repairs, graded

| arm | claim | verdict |
|---|---|---|
| E1 | cross-check replaces the subtraction identity | ✅ **two-sided.** RED under `is_producing → True` (0.0 ≠ 60.0) **and** under a zero-list mutation |
| E2 | tautological arm replaced with a discriminating cross-check | 🔴 **half-earned.** Under the `3h`-registered mutation `is_producing → return True`: `[B4]` FAIL, `[E1]` FAIL, **`[E2]` PASS — `producing=60.0, zero=0.0`**, byte-identical to the output `AUDIT_3H` §6.2 condemned. The fixture's correct answer *is* the maximal-producing answer, so no over-permissive bug can move it. Falsifiable only under the narrower `autos_producing = False` edit |
| E3 | the auto-key hole in the named zero list closed | 🔴 **no check at all.** Mutating `calibrate_crawled.py:548` to `if False:` — a full revert — leaves `check_refusals.py` at **0 FAILURES**. The E1 fixture (`check_refusals.py:872-882`) contains only positive ids (92557, 111) and **no auto rows**, so it never exercises the repaired path |
| E3 | — | 🔴 **and it regressed.** `:537-538` `continue`s past `auto_mh`/`auto_oh` and `:548` re-adds only when `auto_rows_logged` is truthy, so **a zero-producing auto key whose log carried no auto row is now dropped from the named zero list entirely.** Verified both trees: `eaa7604` → `[{'spell_id': 'auto_mh', …, 'why': 'refused-sentinel'}]`; HEAD → `[]`. The comment two lines above (`:511-513`) says *"Full list, no caps — a renderer may truncate but must say what it dropped"* |
| E4 | fail-open census closed | ✅ verified |
| E5 | fail-open census closed | ✅ verified |
| E6 | `--allow-dirty` requires and records a reason | 🟡 **assertions never run on a clean tree** (both inside `if tree_dirty:`, `check_refusals.py:406, 429, 448` → 0 `[E6]` lines) and the CLI path they guard is unreachable (`calibrate_crawled.py:1434` sets `allow_dirty=bool(args.allow_dirty_reason)`, so the `SystemExit` at `:1551` guards direct API misuse only). Disclosed by the `[A7]` stated-skip line — honest, not silent |

**And the `3h` finding it was meant to close is unchanged at HEAD:**
`predictions/gate_manifest.json` still ships `git_working_tree_dirty: true` with
`dirty_tree_write_allowed_by_flag` and `…_reason` **absent**. The only reader of any
committed manifest is `parse_admissibility.py:479`, and it reads the cohort. There is no
assertion of the form *"a committed manifest with `git_working_tree_dirty: true` must
carry a reason."*

**Two structural notes:**

* **A duplicated predicate with a comment asserting it isn't.** `calibrate_crawled.py:521-523`
  claims auto rows are matched *"through the SAME `is_auto_row` predicate"*. False:
  `is_modelled` (`:476-497`) inlines its own copy; `is_auto_row` (`:524-532`) is a second
  implementation 30 lines later. Nothing asserts they agree — and the one check that
  would notice has no auto rows in its fixture. Compounds the E3 finding.
* **The doc-sync verdict cannot reach the exit code on a clean clone** — the environment
  it was explicitly written for. `check_sim_engine.py:351` runs it first, then `:357-366`
  `return 2` on a missing `data/derived/ascension.db` **without consulting `FAILURES`**
  (read only at `:723`). Baseline exit 2; with M31 applied (doc-sync FAIL) exit **2**.

---

## §9 — The document half, again the weaker half — third consecutive session

1. 🚨 **`CLAUDE.md:199` says the admissibility rule is NOT applied.** *"✅ STAMPED `3h` D4
   …, **NOT applied** … A later session applies it with its own before/after pair."* `3i`
   applied it at `0fbffd5`. The **only** `CLAUDE.md` change in the whole `3i` range was
   the census line (59 → 62 files). This file is auto-loaded before anything else, every
   session. **Highest-traffic stale live instruction in the repo.**
2. 🚨 **`primer/CHAT_MONITORING_PRIMER.md` is v4, `LIVE`, and stale by its own written
   terms.** `:3-6`: *"Supersede at v5 when `3i` closes … If you are reading this after
   `3i` has closed, it is stale."* It landed at `891eeed`, the **first** commit of the
   range, and **no `3i` commit touched it after.** Contradictions: `:60-62` `1/1/20.5%`
   vs `0/0/26.31%`; `:71` producing median 0.253 vs 0.2727; `:101-107` the
   `per_ability_accuracy` defect stated as live and *"do not pick modelling targets from
   the pre-repair distribution"*; `:115` *"5 of 41 is a lower bound"*; `:134-137` 20.5%;
   `:150-151` *"`calibrate_crawled.py:692` and `scrape_ascension_db.py:12` still carry the
   old phrasing"* — **both fixed in `3i`**. It also mislabels the blocks (calls the
   instrument repair "Block B" and admissibility "Block C"; they ran as C and D). Third
   consecutive expiry-while-`LIVE`.
3. 🚨 **`predictions/CALIBRATION_TOLERANCE.md` — a generated table its own status line
   forbids leaving stale.** Header `:3-8`: *"MUST be regenerated whenever the run they
   describe is superseded."* Band table `:180-185`:

   | floor | doc | manifest |
   |---:|---|---|
   | ≥0% | 40.3% (n=33) | 40.25% (n=33) |
   | ≥10% | **23.4% (n=26)** | **34.96% (n=27)** |
   | ≥20% | **20.5% (n=23)** | **26.31% (n=23)** |
   | ≥30% | **16.9% (n=20)** | **17.53% (n=20)** |
   | ≥50% | **16.9% (n=8)** | **15.61% (n=9)** |

   `:186-192` is the standing warning against exactly this (*"regenerate, do not retype,
   and check this table in the same commit that moves the gate"*). `3i` moved the gate
   twice and did not touch it. Worse: `:201-202` and `:213` are annotations **`3i` itself
   wrote in Block A** citing producing-only 30.7% (n=20) as *"committed in
   `gate_manifest_3e.json`"* — the manifest reads **37.65 (n=19)**. Stale by the end of
   their own session, because Block D re-ran the gate after Block A wrote them. And
   `:302`'s heading still reads *"stamped `3h` D4, **NOT applied**"* while `:357-380`
   narrates the applying session — heading and body disagree inside one section.
4. ⚠ **The holdout in the manifest is pre-E15 and sits beside post-E15 tuning numbers.**
   `holdout.read: false`, carried from `131eeb4` (a `3g` commit). The carry-forward note
   is exemplary about *"NOT from this run"* — but neither it nor `PROGRESS.md:70-75`'s
   LIVE table says **the corpus underneath was corrected in between**. E15 moved tuning
   slice 20.5 → 26.3 purely by fixing the logged-DPS denominator; the holdout's
   −79%…−98% and median 9.8% were computed on the inflated logged side. The table invites
   a comparison that is no longer like-for-like.
5. 🚨 **The mutation registry is out of sync, and structurally invisible to the new
   parser.** `ENGINE_BUGS.md:106` ends at **M31**. **M32** (`per_ability_accuracy.py:281`)
   and **M33** (`parse_admissibility.py:98`) are called *"Registered"* in code and exist
   only in the session record. The E1/E2/E4/E5/E6 repair mutations carry no M number at
   all. `check_engine_bugs_doc_sync` parses only `| **Check(s)** |` rows — it does not
   touch the mutation table, so this drift is the exact class the new check was built for
   and does not cover. **And no check anywhere exercises the applied admissibility rule**:
   `grep -rn "admissib" tools/ core/ cli/` returns only the two files.
6. ⚠ **`ENGINE_BUGS.md` E16's prose magnitude** still reads *"~a fifth of the cohort
   slice"*; it is 26.3% — a quarter. (The −66.9% whole-character figure beside it is still
   valid.)
7. ✅ **`## Current position` is fixed** — `PROGRESS.md:604` is now inside a collapsed
   `<details>`, and the live top block matches the manifest exactly. **Residual, same
   class:** two `### 🔴 FIRST ACTIONS NEXT SESSION` headings at `:865` and `:913` are
   **not** collapsed — they sit under bare `## Superseded:` H2s, and `:865` carries no
   session tag at all.

**Previously-open items, status:**

| item | status |
|---|---|
| `gear_tier_stats(phase=…)` production caller | 🔴 **still none.** Only `core/builds/gear.py:403` (the def). **Fourth** consecutive session; `3f` exit condition 10 still reads ✅ |
| `ContentProfile` presets self-declaring assumptions | 🔴 **still 6 of 8** — `core/sim/content.py:133,139,145,151,157,163`. `PHASE_3` criterion 7, untouched since `3d` |
| `calibrate_crawled.py:692` coverage phrasing | ✅ fixed (`3i` A5, now `:730`) |
| `scrape_ascension_db.py:12` | ✅ fixed |
| `gate_manifest_3e.json` misnamed | 🟡 unchanged, and **it is the only live artifact in `predictions/` with no `status`/`_status_note` key at all** — the *frozen* `gate_manifest.json` has one, and the brand-new `per_ability_summary.json` has one. `check_refusals.py`'s A5 check, whose message reads *"EVERY file in predictions/ carries a status line"*, walks `*.md` only — **all four JSONs are outside it** |

---

## §10 — The list `3j` works from

Ordered by consequence, not by effort. Items 1–3 are gate-integrity; 4–6 are the
document debt; 7+ is the modelling work `3i` handed over whole.

**Block 0 (before anything else, and it may already have happened)**

1. 🚨 **The flip.** Check `/api/phases` live. Then, regardless of outcome, fix the
   `refuse_reason` passthrough (§2): a payload-level refusal must not become a
   cohort-wide parse verdict. A gate run where **all** members carry the identical
   admissibility flag should refuse to publish a number.

**Block A — gate integrity (do not run a modelling block before these land)**

2. 🚨 **Close the fail-open at `calibrate_crawled.py:830-837 / :1581`.** Either raise
   when `assert_stamped_thresholds()` fails, or make
   `parse_admissibility_rule_applied` reflect the actual `pa is not None` — and extend
   the `3h` A3 assertion to cover it. A manifest that claims a rule ran when it did not
   is the worst failure available to this project.
3. 🚨 **Re-derive the D5 comparator change as a pre-registration.** State the predicate,
   predict the roster, *then* re-apply. Separately: add a check that the comparator
   change set can move a character **into** a flag, not only out — the current one-way
   structure (§4) is untested in the direction that matters. And fix the inverted 0.0-
   comparator rationale, or state plainly that the arm raises ratios and hides deflation.
4. ⚠ **Anchor `assert_stamped_thresholds()` to the stamped section** (parse the block,
   not the file), and extend it to the comparator *definition* and the comparison
   direction — the two things D5 changed under an unchanged stamp (§5).
5. ⚠ **E3: give the repair a check, and restore the dropped rows.** Add auto rows to the
   E1 fixture; make the `if False:` revert go RED; and stop dropping zero-producing auto
   keys with no logged auto row. Then de-duplicate `is_modelled`/`is_auto_row` or assert
   they agree.
6. ⚠ **E2: widen the fixture** so the maximal-producing answer is not the correct answer,
   or retire the arm and rely on E1.
7. ⚠ **Make `check_sim_engine.py` return the doc-sync verdict on a clean clone** —
   consult `FAILURES` before the `return 2` on missing db (§8).

**Block B — the E15 aftermath**

8. 🚨 **Migrate or refuse.** Set `PRAGMA user_version`; on an old DB either backfill
   (`DELETE FROM ability_performance WHERE is_pet=1`, repopulate `pet_ability_damage`) or
   **refuse to read it**. Add `is_pet`-awareness or an assertion to the three unguarded
   consumers (§7.1).
9. 🚨 **Give E15 a check that can fail.** Assert against the *real* corpus: zero
   `is_pet=1` rows, `pet_ability_damage` non-empty, and add it to the
   `build_builds_db.py` census printout.
10. ⚠ **Fix the NULL-`spell_id` PK escape** (`COALESCE` to a sentinel, or reject the row
    loudly). It is a live double-count route with a reachable trigger.
11. ⚠ **Correct the four stale-formula strings**, one of which ships to users
    (`core/sim/pets.py:103-104`) and one of which is seeded into the epistemics DB.
12. ⚠ **Document the pet-only-character cohort change**, and check whether any cohort
    member was affected.

**Block C — documents (budget real time; this is the third session it has slipped)**

13. 🚨 `CLAUDE.md:199` → applied, with the pair.
14. 🚨 **Update `primer/CHAT_MONITORING_PRIMER.md` in place to v5.** v4 is stale by its
    own terms and has been since the moment `3i` closed. The file is versionless — the
    version belongs in the title line only; committing a `_v5` sibling would leave v4
    on disk marked `LIVE`, which is the exact three-session failure mode being fixed.
15. 🚨 **Regenerate `CALIBRATION_TOLERANCE.md`'s band table and the `3i` A5 annotations**,
    in the same commit, from the manifest. Fix the `:302` heading.
16. ⚠ **Land M32 and M33 in `ENGINE_BUGS.md`**, give the E1–E6 repair mutations numbers,
    and **extend `check_engine_bugs_doc_sync` to parse the mutation table** — otherwise
    the next drift is identical and equally invisible.
17. ⚠ **Extend the A5 status-line check to `predictions/*.json`**, and give
    `gate_manifest_3e.json` a `status` key (renaming it is optional; labelling it is not).
18. ⚠ **Annotate the holdout carry-forward** as pre-E15, or re-read it. As it stands the
    LIVE table invites an unlike comparison.
19. ⚠ **`per_ability_summary.json`: refuse to write under `--char`/`--max-lag-hours`**, or
    record the filter in the artifact. Add cohort identity. Make the dirty-tree refusal
    raise, matching its own docstring.
20. ⚠ Collapse the two uncollapsed `FIRST ACTIONS NEXT SESSION` headings; tag `:865`.

**Block D — the modelling work `3i` handed over (STOP-POINT F)**

21. Re-confirm the levers against the **repaired** distribution before picking a target:
    the absent-key majority (63.9%), the starved-allocation mass (11.3%), Elemental Blast.
    **Note that a 63.9%-absent distribution says the first lever is coverage of keys that
    do not exist, not accuracy of keys that do** — which is a different kind of work from
    tuning a multiplier.
22. **The gate has zero passers.** A modelling session should expect to *build* a pass,
    not defend one — and should pre-register what a pass would look like before it runs.

---

## §11 — Reproducibility limit (unchanged, and worth restating)

Tier-2 ability captures are gitignored (`.gitignore:27-30`); `data/derived/` is not in the
clone. Rebuilding `builds.db` from committed source yields `ability_performance` = **0
rows**, `capture_scopes` = **0**. Every corpus figure in the `3i` record — 15,551 /
22,427 / 530.5M / 1,208 / 20.5% → 26.3% / n=23 — is **unverifiable from this repository**.
The confirmations in §1 come from synthetic fixtures exercising the real functions, and
from the committed manifests' internal arithmetic.

`predictions/per_ability_summary.json` genuinely improved this. `gate_manifest_3e.json`'s
`git_sha` on a clean tree genuinely improved this. Neither makes the **inputs**
checkable. That remains the standing structural limit on this chat's reach.
