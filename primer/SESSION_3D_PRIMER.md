# Session `3d` primer — harden the harness, then build the instrument

**Written by:** the monitoring chat, 2026-08-06, after an adversarial audit of `3c`
against a full clone of `main` at `a36f666`. Findings doc: `primer/AUDIT_3C_ADVERSARIAL.md`.
**Read that file when a task below says "see §x" — do not re-derive its findings.**

**Owner decisions taken 2026-08-06 (both are settled — do not re-open):**
* `3d` = **hygiene + instrument only. No modelling changes.** Modelling and the gate re-run
  are `3e`. PHASE_3 T6 (log ingestion) is **reinstated and promoted** to its own session, `3f`.
* PHASE_3 **T5 (capture addon) is demoted**, not reinstated. PHASE_3 **T7** follows `3f`.

---

## 0. The one property that defines this session

> **🛑 `3d` must not move the calibration gate.**

Run the gate **before you touch anything** and again at the end. Both must read
**5 of 41 within ±20%, 2 qualified**.

```bash
py tools/audit/calibrate_crawled.py --limit 120 --max-lag-hours 0   # BEFORE — record verbatim
```

Every task in this session is either a correctness guard, a doc fix, a reporting addition,
or an instrument. **None of them should change a predicted number.** If the closing run
differs from the opening run by so much as one character:

**STOP. Do not proceed. Do not "fix forward". Bisect which task moved it and report the
exact cause to the owner before continuing.** A hygiene session that silently moves the
gate has destroyed the attribution that makes `3e` readable — which is the entire reason
the owner split these sessions.

The three tasks most likely to trip this legitimately are **C1**, **C2** and **C4**. If one
of them moves the gate, that is a *finding worth having*, not a failure — but it must be
reported, not absorbed.

---

## 1. Why this session exists

`3c` was good work with three honest retractions. The audit found a fourth error it missed,
three project-rule violations that are reported as satisfied, and one structural problem
that dwarfs all of them.

**The structural problem: the entire validation surface of this project is one character.**
Every fixture, the whole `check_sim_engine.py` regression harness, and `calibrate_vs_log.py`'s
defaults are Elric — a Paladin/Hammerdin. Six real engine bugs sit in shared code paths that
an all-instant, single-filler, no-combo-point, no-pet melee build is **structurally incapable
of exposing**. Nothing in the repo would fail if a Rogue or a Warlock produced nonsense.

Block D is the answer to that and it is the highest-value work in this session. Everything
else is cheaper.

**Second structural problem: no auditor can reproduce a single headline number.**
`.gitignore:10` excludes `data/derived/`, no `.db` is committed, and `build_builds_db.py`
is not in `rebuild.py`'s `CHAIN` or in any `.bat`. So 5/41, 37% coverage, 74 proposals and
the 323/177 conflict counts exist only on the owner's machine. Block E fixes that cheaply.

---

## 2. 🚨 Block A — time-critical, do this first, today

**The server flips to Phase 2 on 2026-08-08. That is two days out.**

| # | Task | Acceptance |
|---|---|---|
| **A1** | `SEASON`/realm are hardcoded in **five** places: `tools/scrapers/crawl_ascensionlogs.py:82`, `cli/mechanics.py:38`, `cli/relationships.py:30`, `ingest/.../resolve_numeric_formulas.py:56`, plus the realm constants. Centralise them into one module, and **assert the value against the live `/api/phases` response the crawler already fetches**. Mismatch = loud error, not a warning. | A deliberately wrong `SEASON` constant causes a hard failure on the next crawl, not a mis-stamped record. Remember `phase_number` is not the phase label — read `name` + `progression_parent_phase_id` (START_HERE §Current state) |
| **A2** | `crawl_ascensionlogs.py:645` does an **unscoped** `git add data/source` in an unattended job. Any working-tree change under `data/source` — a half-edited scouted JSON, a capture folder mid-copy — gets auto-committed and pushed. Scope it to `data/source/crawl` + `data/source/changelog`. `run_baseline_scheduled.bat:58` already does this correctly; copy that. | One line. Verify by leaving a dirty file under `data/source/captures` and confirming the crawl does not commit it |
| **A3** | **Row-count canary.** `crawl_ascensionlogs.py:783` gates exit only on request-level `ERRORS`. A 200 response with changed HTML yields 0 phases → 0 leaderboards → **exit 0, day stamped success, empty capture committed.** Compare each writer's count against the previous date's manifest; exit nonzero if any drops >50% or hits zero. | Simulate by pointing a selector at a nonexistent element; the run must fail and must not stamp the day |
| **A4** | `run_crawler_scheduled.bat:34-35` prints `[WARN]` on changelog failure and **ignores the exit code**, so a day of records can be stamped `patch_date: null` silently. Propagate it. | A failed changelog fetch fails the day |

**🛑 A1 is the only item in this primer with an external deadline. If the session runs long,
A1–A4 ship on their own commit and the rest waits.**

---

## 3. Block B — naming and doc truth

Cheap, and B1 prevents a session-costing error.

| # | Task | Acceptance |
|---|---|---|
| **B1** | **All eight T-numbers collide** between `PHASE_3_builds_repo.md` (T1 normalise / T2 inference / T3 search / T4 gear / T5 addon / T6 log ingestion / T7 automation / T8 crawler) and `PLAN_3C_clean_exit.md` (T1 slice accuracy / T2 admissibility / T3 over-predictions / T4 trigger edges / T5 pets / T6 conversion / T7 class-A / T8 re-run). PHASE_2 is a third space. **Rename PLAN_3C's `T1…T13` → `C1…C13`** everywhere they appear | `grep -n "\bT[0-9]" primer/PLAN_3C_clean_exit.md` returns nothing. All references in `PROGRESS.md` and `AUDIT_3C_handoff.md` updated |
| **B2** | `AUDIT_3C_handoff.md` **contradicts itself**: §0 line 18 says "T5(addon)→T6(logs)→T7(automation) deferred"; §4 line 154 says "T4, T5, T12, T7 — trigger-edge reachability, pets, coefficient-conflict review, class-A reachability". Same three tokens, six meanings, 135 lines apart. Fix under B1's naming | No token in either doc has two meanings |
| **B3** | Correct the exit-criteria record in `PROGRESS.md` and the handoff: there are **seven** criteria, not six; **three** are outstanding (#2, #4, #7), not two; and **#7 (`ContentProfile` presets) is FAILED, not unverified** — `core/sim/content.py` has 6 of 8 presets carrying `provenance="assumption: …"` in their own strings, all target counts invented, every target stat `retail_hypothesis` (`:93-97`) | The doc matches the file |
| **B4** | `ARCHITECTURE.md` §4's layout block no longer describes the tree. Built and undocumented: `tools/analysis/pooled_inference.py`, `core/builds/group_buffs.py`, `core/spells/db_ascension.py` + the whole db.ascension.gg source, `predictions/` markdown ledgers, `reviews/`, `bugs/`. Also record that §2.4 is **inverted in practice** — uncertainty ranges live in a sim-layer policy table, not Phase 1's truth table | The layout block matches `find . -type d` |
| **B5** | `api/` is a 12-line empty `__init__.py`, but `ARCHITECTURE.md` §2.7 rule 4 states `cli → api → core` and **`PHASE_4` says "the web app is a thin layer: `api/` already exists."** Seven CLIs call `core/` directly. Either put one real function in `api/` or amend both docs to say the boundary is aspirational | No doc claims a layer that has zero functions |
| **B6** | `Session_2026-08-06_3b_preflight.md:13` says the rebuild is 20 steps. `cli/rebuild.py:35-73` has 21 | — |

---

## 4. Block C — the three rule violations

These are reported as satisfied and are not. **A documented-but-absent guard is worse than a
missing one**, because it reads as compliant to the next session and to the owner.

| # | Task | Detail |
|---|---|---|
| **C1** | **Rule 1 violated.** `core/db/schema.py:53-72` — `spell_scaling` has **no** `evidence_ref`, `confidence`, `verified_at_patch`, `realm` or `season` column at all, and `source TEXT DEFAULT 'export_tooltip'` is nullable *with a default*, so a row that omits `source` **fabricates tier-6 provenance**. That happens today at `ingest/export/seed_cp_scaling.py:53` (Holy Finish SP/AP 0.02). Compare `spell_effect_values:260-263` and `spell_mechanics:355-363`, which do enforce NOT NULL. **Add the columns, make them NOT NULL, backfill every existing writer, and give `seed_cp_scaling.py:53` an explicit source.** | 🛑 Backfilling provenance means **stating what each existing row's real evidence is** — not defaulting it. If a writer's provenance is genuinely unknown, that is a stop-point, not a blank |
| **C2** | **The dedupe fix reopens its own bug.** `core/spells/mechanics.py:398-402` ranks on `_COEFF_SOURCE_RANK.get(source, 99)`. Any source absent from that hardcoded dict ranks 99; two unknown sources **tie**, both survive as `winners`, and if their `component` differs (or one is NULL) **both are emitted and summed — the original Mongoose Bite double-count, reachable again.** Add validation: every distinct `source` in `spell_scaling` must appear in `_COEFF_SOURCE_RANK` or the build **hard-fails**. `core/sim/cache.py:84-87` already does exactly this for the analogous case — copy the pattern. **Also:** same-source duplicate terms are silently destroyed at `:404-409` (`seen` filter), and `migrate_spell_scaling_ranks:790-796` via `rank_scaling.py:81-85` demonstrably produces them. That is precisely the direct+periodic pair `schema.py:66-70` says must never be collapsed. Record them as conflicts; do not drop them | |
| **C3** | **Rule 3 half-violated, and the operator sees a wrong number.** Both conflicting rows *do* persist (each writer deletes only its own source partition — `load_scraped_coefficients.py:183`, `seed_hand_coefficients.py:70`), so "record both" is satisfied. But coefficient conflicts never enter `FieldSet.conflicts` (`mechanics.py:118-146`), `conflicts_json` is NULL for all 177, and `stats["with_conflict"]:753` counts only `fs.conflicts` — so **`cli/mechanics.py:133` prints "rows with a source conflict (surfaced not resolved)" and that number is wrong by ~177.** Route them in, and open an `open_questions` row for the precedence decision | 🛑 **Do not change any precedence value.** The owner has approved preferring the scrape. The task is to make the choice *visible*, not to re-make it |
| **C4** | **A guard that is documented and not implemented.** `ingest/export/seed_epistemics.py:143` asserts *"Holy Shock is EXCLUDED from the Holy-group constant."* Grep: `ascension_measured_provisional` appears in the seeder (`seed_hand_coefficients.py:30,62`) and the precedence dict, and **zero times in `tools/`**. `calibrate_vs_log.py:400` calls `sim_base()` — which embeds the back-solved 0.40 — and pools Holy Shock into the Holy group at `:414` with no source filter; `KNOWN_BROKEN:377-384` does not list 25902. **Implement the exclusion.** Then the scraped 0.214 stands in calibration and the circularity is broken | Exactly **one** back-solved value exists project-wide, so this is a bounded fix, not a class of problem |

---

## 5. ⭐ Block D — two fixtures. The highest-leverage work in this session.

**Everything the audit found in the engine was found by reading, not by a failing test.
Fix that.**

| # | Task |
|---|---|
| **D1** | Add **two non-paladin fixtures** and wire them into `check_sim_engine.py` alongside `build_elric_paladin.json`: (a) a **combo-point melee** build (Rogue-ish: builder + finisher, energy, an execute-range ability), (b) a **DoT caster** (Warlock/Shadow-ish: 2+ DoTs of different durations, a filler with a cast time, mana). Take real card sets from the crawled corpus so they are plausible builds, not synthetic ones — the corpus is not paladin-skewed (371 level-60 boards: intellect 79 / strength 50 / spirit 48 / duality 40 / agility 38; Hammerdin on **9**) |
| **D2** | 🔴 **`calibrate_vs_log.py:380-386` fails OPEN.** `check_alignment()` `continue`s when none of the paladin abilities in `ID_ROUTING` / `ALIGNMENT_ZERO_CRIT` appear — so **for a Mage log the field-alignment gate passes vacuously and never says it could not run.** That is the exact failure mode primer v31 §5 warns about. Make it **refuse and say so** when it has no anchor ability for the log it was given |
| **D3** | 🛑 **Expect the new fixtures to fail, and DO NOT FIX THE FAILURES.** Record each as a `bugs/` entry with the file:line and a one-line failure description, then move on. Fixing them is `3e`. The deliverable of D1–D3 is *failing tests that name real bugs*, not green tests |

**What the audit already predicts they will expose** — use this as a checklist, and flag
anything they expose that is **not** on it, because that is the point of the exercise:

* `tiers.py:137-141` — in `fast_sim`, the **first filler consumes the entire GCD budget**
  (`gcd_budget = 0.0`); every later filler gets 0 casts. The comment two lines above says
  "fillers split whatever budget the cooldowns left, in priority order." The code does not.
  **This is the tier the calibration gate runs on.**
* `tiers.py:197` / `apl.py:118` — `combo_points` is **never incremented anywhere**, so
  `combo_points_at_least` (which `apl_gen.py:91` emits for every finisher) can never be true.
  Finishers never fire in `medium_sim`; `ability_model.py:420-425` scores CP terms at 0 CP.
* `apl.py:19-32` — no target-debuff / DoT-uptime condition exists, and `apl_gen` gives
  fillers `always`. **A DoT is re-cast every GCD with its entire duration's damage re-scored
  each time.**
* `tiers.py:198-199` — `self_health_pct` / `target_health_pct` fixed at 100. Execute windows
  and the solo self-sustain branch (`apl_gen.py:72-80`) are dead code.
* `apl_gen.py:62-63` — fillers sorted by damage *per cast*, not per GCD/cast-time, contra its
  own docstring line 10. Penalises any mixed-cast-time caster.
* `spells/mechanics.py:232` resolves `is_channeled` and the sim **never reads it** — a channel
  costs one GCD and delivers all ticks.
* No pet model exists in `core/sim`, while `corpus.py:614` computes
  `dps = (total_damage + pet_damage)/dur`. Pet classes are guaranteed to miss.
* `tiers.py:168-170,323-325` — `melee_ability_hits` counts only schools
  `("Physical","Holystrike")`, so Shadowflame/Froststrike/Shadowstrike melee builds are not
  counted as melee. `talents.py:52-56` already knows all eight hybrids.
* `weights.py:28-42` — no ranged AP, no spirit/mp5, no weapon-speed axis; melee and spell
  haste move together; divisors hardcoded (14/10/8/2.5/4.2) instead of the `gt` table the
  engine otherwise insists on.

**Also in scope, cheap:** `swings.py:69-81` holds `RIGHTEOUS_VENGEANCE_SPELL_ID=61840`,
`JUDGEMENT_BY_SEAL`, `JUDGEMENT_PRESS_CARDS` — paladin spell IDs hardcoded in `core/`.
Move them to a seed table. `buffs.py:78-90,138-151` puts `consecrated_weapon` (a paladin
imbue) in the `party`/`raid` presets, and no caster-side buffs (Curse of Elements, Totem of
Wrath, Demonic Pact) exist even as named gaps — **name them as gaps**, don't invent values.

---

## 6. Block E — make the numbers reproducible

| # | Task | Acceptance |
|---|---|---|
| **E1** | `ingest/logs_gg/build_builds_db.py` is **not in `rebuild.py`'s `CHAIN` and not in any `.bat`**, yet the gate cohort, the scraper's demand list and pooled inference all depend on it. Add it to the chain | A clean machine reproduces `builds.db` with one command |
| **E2** | Emit and **commit** a small `gate_manifest.json` per gate run: cohort size, the 41 character ids, per-character delta and coverage, the rider constants in force, and the git SHA. Counts and hashes only — not bulk data, `.gitignore:10` stays as it is | An auditor with only the repo can check that a claimed gate result matches the manifest |
| **E3** | `rebuild.py` partial failure is unsafe: 21 steps as separate subprocesses (`:86`), no cross-step transaction, no temp-DB-and-swap, no backup. Step 15 failing leaves `ascension.db` half-seeded and *readable*, with nothing marking it invalid. **Minimum fix:** write a `rebuild_state` row at start and clear it on success; every reader hard-fails on a stale marker | A killed rebuild leaves a DB that refuses to be read, not one that lies |

---

## 7. Block F — the instrument

`3c` proposed T13 → T6\* → T11. **The order is wrong.** T11 produces the verified stat block
that everything else must be validated against, and T13 falls out of it as a one-liner.

| # | Task (new `C` numbering) | Detail |
|---|---|---|
| **F1** | **C11 — give Elric a snapshot from his ALC capture** | 🛑 **Ship it with an explicit exclusion in `candidates()`.** `calibrate_crawled.py:99-134` filters on level 60 + gear stats + cards + `snapshot_lag_hours` with **no source filter** — so giving Elric a `character_snapshots` row makes him a gate candidate automatically and the cohort silently becomes **42, with the one privileged-input character inside it**. "He is an instrument, not a count" currently exists only in prose. This exclusion is **non-optional** and is the acceptance test for F1 |
| **F2** | **C13 — the stat block becomes `required=True`** | `calibrate_vs_log.py:302-305` defaults to AP 584 / SP 533 / 585–669 (from the 2026-08-03 build doc); the verified block is AP 141 / SP 638 / 543.6–646.3 (`predictions/calib_2026-08-05_2e_poi.md:9-13`). **Do not swap the defaults — delete them.** Rule 2: unconfirmed = flagged, never silently defaulted. PLAN_3C's alternative ("read it from a named capture") is worse — it silently rebinds to whatever that folder holds later. Also add `--weapon-speed` (currently hardcoded `3.57` with no flag) and named gaps for `--haste`, `--spell-crit`, `--ranged-ap` |
| **F2b** | **Decontaminate the pair ratios** | `predictions/pred_2026-08-05_elric_paladin.md:62` records a `--all-logs` run with **no stat flags** — a stale-defaults run. The 1.31 school ratio is already demoted, but **`PHASE_2_simulation.md:470` states predicted 1.718 and 0.769 and calls them "the targets a talent model must reproduce."** `pair_ratios()` (`:461`) takes the char-state built from `args.ap/args.sp/args.weapon_*`, and both sides carry flat **plus** SP/AP terms in different proportions — **those targets are a function of the wrong stat block.** Re-derive at AP 141 / SP 638 and restate them with the stat block recorded inline |
| **F3** | **C1 — report slice accuracy** | `slice_accuracy = (100 + delta) / coverage`. Currently `grep slice tools/audit/calibrate_crawled.py` returns two prose comments and no code. Report it per character and as a cohort median, next to coverage. **Pure instrumentation — it must not change any verdict** |
| **F4** | **Record the successor criterion** | Append a **dated** entry to `predictions/CALIBRATION_TOLERANCE.md`: the ~80% coverage derivation, its date, that it takes effect **at the next gate and not this one**, and — critically — **that 80% is conditional on slice accuracy = 100% and is not a hard floor.** See §9 below for why. 🛑 **Do not edit the 50% rider.** Its own closing rule ("a reason that does not reduce to 'the current number did not clear it'") is exactly what an 80% edit would violate |
| **F5** | **Name a holdout set** | There is currently **no overfitting control anywhere in PLAN_3C** — C8 is a post-hoc read of the same 41 the fixes were tuned to lift. Name **≥5 of the 41** as a validation set, excluded from all tuning, **before** `3e` starts. The mechanism is already built and unused: `predictions`/`prediction_outcomes` (`seed_predictions.py`) refuses to overwrite a slug — that is pre-registration |

---

## 8. 🚫 Explicitly out of scope for `3d`

Do not do these. They are `3e`, and doing them here destroys §0's attribution.

* **Righteous Vengeance.** `tiers.py:439` reads `ev["crit_damage"]`; `grep -rn "crit_damage"`
  confirms that key is **written nowhere in the tree** (`ability_model.py:826-836` emits
  `event_key, kind, school, source_spell_id, via, attributed, occurrences, mean_each,
  mean_total, p_land, p_crit`). Every run since `2e` has emitted *"Righteous Vengeance NOT
  modelled"* and nobody read it. **And `_add_swing_sources` is called from `fast_sim`
  (`tiers.py:171`) with no check that 61840 is in `build_spec.talents`** — only 109 of 371
  boards hold it. Fix the key without adding the talent gate and ~30% of crit damage lands on
  **all 41 characters, not 9.** `3c` describes this as unbuilt work; it is a dead code path
  that must be un-broken *and gated*, then measured cohort-wide before acceptance. **`3e`.**
* The out-of-catalog ~4.5× cluster (C10 → C9). **`3e`** — and when it runs, a **second Holy
  character** is required before "five spells within ±4% = one mechanism" is claimed. Five
  readings, all Holy, all one character, all one stat block, three summoned by a single
  talent, is **one measurement with five readings**.
* C4/C5/C12/C7 reachability and pets. **`3e`**, each pre-registering its expected coverage
  *and* slice-accuracy movement first.
* PHASE_3 T6 (combat-log ingestion). **`3f`** — see §10.
* Fixing anything Block D's new fixtures expose (D3).

---

## 9. Context you need for F4 — why 80% is not a floor

The decomposition `slice_accuracy = (100+delta)/coverage` is **algebraically exact**, and the
~80% figure reproduces independently: set slice accuracy = 100 ⇒ `delta = coverage − 100` ⇒
`|delta| ≤ 20 ⇒ coverage ≥ 80`.

**But it is neither necessary nor sufficient.** 110% accuracy at 73% coverage gives −19.7% and
passes below 80. 80% coverage at 60% accuracy gives −52% and fails at 80. It is one point on a
2-D curve, valid only at *exactly* 100% slice accuracy — which PLAN_3C's own §4 says will not
happen.

**And the trajectory assumption is unsafe.** The formula assumes the unmodelled slice is
predicted at zero — true today by construction. The risky part is assuming damage *added* by
the reachability tasks arrives at ~100% fidelity. Elric's own data refutes it: the
out-of-catalog cluster reads **4.3–4.7× logged/base**, i.e. ~22% fidelity. Covering the residual
42% at 22% fidelity buys **~9 delta points, not 42**.

**Worse, coverage is binary.** `modelled_damage_share` (`calibrate_crawled.py:171-224`) is a
membership test, so a spell modelled at 4.5×-under counts as *fully covered*. Coverage work
therefore **mechanically raises coverage while depressing slice accuracy** — and Ari (156%) /
Malo (131%) can be lost by pure coverage work with no accuracy change at all.

**Standing rule to adopt from `3e` onward:** every coverage task reports slice accuracy
**before and after**. A task that raises coverage while dropping slice accuracy has moved the
metric, not the model.

---

## 10. What comes after

| Session | Content |
|---|---|
| **`3e`** | Modelling. RV un-broken + talent-gated + cohort delta measured before acceptance; the `fast_sim` filler bug; C10→C9 with a second Holy character; C4/C5/C12/C7 pre-registered; gate re-run read against the rider **and** against slice accuracy |
| **`3f`** | **PHASE_3 T6 — combat-log ingestion, reinstated and promoted.** Everything `3c` §2 did by hand *is* T6. Most of it exists: parsing is done and Ascension-verified (`tools/log_parser/`), the correlation rule is fully specified and seeded (`seed_confirmed.py:47`), and the `* WoWCombatLog.txt` glob is written at `calibrate_vs_log.py:314`. Missing: mtime windowing (**zero** `st_mtime` uses in the tree), year/local↔UTC conversion, many-to-one grouping, and **any writer from a log into `builds.db`** — today the path terminates at a `.summary.json` that `.gitignore:4` excludes and nothing reads, so every log finding survives only as prose a human types into a seed file. Once wired, **owner input afterwards is zero** — the logs are already on his disk in a known directory |
| **then** | PHASE_3 T7 (session automation) — hard-depends on T6, though its patch-check half is independent and cheap. **PHASE_3 T5 (capture addon) stays demoted**: ALC + `decode_alc.py` already decode every player build in a log (625 records from one file, byte-verified), so T5's value case is much weaker than when it was deferred |
| **then** | Re-read Phase 3's exit criteria honestly, then Phase 4 — see §11 |

---

## 11. Phase 4 hard blockers, recorded here so they are not rediscovered

Do not start Phase 4 without these. Full reasoning in `AUDIT_3C_ADVERSARIAL.md` §8.

1. **Ablation on a 37%-coverage sim produces a chase list ordered by modelling coverage, not
   by value.** Consecrated Holy Weapon is 25.1% of the owner's buffed damage with **no
   modelled magnitude**. A kit whose members happen to be modelled reads ~3× more critical
   than one whose members don't — and `criticality` ships as a NOT-NULL number with an
   `evidence_ref`. **Minimum mitigation even if Part A starts early: a coverage guard that
   refuses to emit a `lego_measurement` below a stated modelled-damage threshold.**
2. **"Not measurably coupled" is decided by a policy table, not data.** `uncertainty.py:44-80`
   `POLICY` has **no `measured` band at all**; `inference.py:48`'s `promoted` flag is set by
   **no code anywhere**; nothing writes `basis='measured'`. Phase 3 exit criterion #4 is not
   merely unmet — its mechanism does not exist.
3. **Part B has no Darkmoon-legal data.** The only source with essence costs is the
   Area-52/Elune builder, which `seed_confirmed.py:146` says **may not be applied to
   Darkmoon**. Guarantee-slot state is unmodelled entirely. So `build_feasibility` cannot
   detect the one thing its exit criteria grade it on. Get the data or descope Part B to
   rarity + ownership and label it — **do not ship `expected_cost`**.
4. **243 of 243 amplifier rows are unapproved** in `reviews/amplifier_review.md` — zero `[x]`.
   Motif mining runs on a graph missing most amplifier reach (218 `amplifies`, **9**
   `amplifies_school`). The Cleave Kit regression target would be rediscovered via the one
   hand-seeded row, not from data.
5. **`ContentProfile` presets (exit criterion #7) are a FAILED criterion**, and they become
   `lego_measurements` keys in Phase 4. Derive them from the `encounters` table T1 built, or
   amend the criterion honestly — before Phase 4, not during.

**Genuinely unblocked and parallelisable now:** Phase 4 Part C1 (principles corpus). No sim
dependency; `confirmed_facts` / `open_questions` / `retractions` already carry most of it.

---

## 12. Model guidance

Per the project's own rule — match the model to blast radius, not difficulty.

* **Opus** — Blocks **C**, **D**, **F**. C is schema + epistemics + a rule the docs claim is
  enforced; F is the instrument, the successor criterion and the holdout design. Getting C1's
  provenance backfill or F4's wording wrong is expensive and quiet.
* **Sonnet** — Blocks **A**, **B**, **E**. Well-specified and mechanical.

🛑 **Block D runs on Opus. Owner decision, 2026-08-06 — not a default to be re-litigated.**
D1 looks mechanical enough for a cheaper model, and that is the trap: **D3's discipline
(record the failures, do not fix them) is what erodes first under a weaker model.** A session
that quietly fixes six engine bugs while reporting itself as hygiene has destroyed §0's
attribution and the `3d`/`3e` split along with it.

---

## 13. Exit criteria for `3d`

All seven must hold.

1. **The gate reads exactly 5 of 41, 2 qualified** — identical to the opening run (§0). Any
   difference is reported with its cause, not absorbed.
2. `py cli/rebuild.py` green at 21 steps; `check_core_purity.py` 0/47; `check_sim_engine.py`
   passes **for the paladin fixture** — the two new fixtures are expected to fail and their
   failures are recorded as `bugs/` entries.
3. A deliberately wrong `SEASON` constant hard-fails the crawl. A simulated schema break
   fails the crawl and does not stamp the day.
4. `grep -n "\bT[0-9]" primer/PLAN_3C_clean_exit.md` returns nothing; no token in the planning
   docs carries two meanings.
5. Every distinct `source` in `spell_scaling` is in `_COEFF_SOURCE_RANK` (enforced, not
   asserted in prose); `spell_scaling` provenance columns are NOT NULL; `cli/mechanics.py`'s
   conflict count includes the coefficient conflicts; the Holy Shock exclusion is implemented
   and its absence would fail a test.
6. `calibrate_vs_log.py` **refuses to run** without an explicit stat block, and **refuses to
   report alignment** when it has no anchor ability for the log it was given.
7. Elric has a snapshot **and** is provably excluded from `candidates()` — cohort size is 41,
   demonstrated by a test, not by prose.

**Then:** update `PROGRESS.md`, write `primer/Session_2026-08-XX_3d_hygiene_and_instrument.md`,
and hand off to `3e`.
