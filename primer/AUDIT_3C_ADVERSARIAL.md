# Adversarial audit — session `3c`, and the Phase 4 readiness question

> **`FINDING 2026-08-06`** — point-in-time analysis, true as of its date and **not maintained since**. Not citable as current truth without re-checking against the tree. *(Classified `3f` F8c, 2026-08-07.)*

**Auditor:** monitoring chat, 2026-08-06. **Method:** full clone of `main` at `a36f666`,
code read directly. Six parallel deep-dives: coefficient ingest, class generality,
Phase 3 exit criteria, Phase 4 preconditions, PLAN_3C soundness, automation.
**Everything below cites `file:line` in the committed tree.**

---

## 0. Verdict in four lines

1. **`3c`'s headline conclusion is right — Phase 4 is not next — but for weaker reasons
   than it gives, and the true reasons are worse.** It undercounts the exit criteria (7,
   not 6), calls a **failed** criterion "unverified", and its T5/T6 remaining-work
   estimates are wrong in both directions.
2. **The recommended next steps are ~60% correct.** T13 and T11 are right but in the
   **wrong order**; T6\* is described as unbuilt when it is **built, dead, and
   ungated** — implementing it as written would silently inject damage into all 41
   cohort characters, not 9.
3. **The architecture has not drifted in its bones** (`core/` purity is real: 47 files,
   0 violations) **but it has drifted in its evidence discipline.** Three of the eight
   rules are violated in code while being reported as satisfied.
4. **On generality: the code is class-neutral; the *validation* is not.** One character,
   one class, one fixture. Five engine bugs sit in shared paths that a Hammerdin is
   structurally incapable of exposing.

---

## 1. Audit of `3c`'s own claims

| # | Claim in `AUDIT_3C_handoff.md` | Verdict | Evidence |
|---|---|---|---|
| §0 | "Phase 4 is NOT next" | ✅ **CORRECT** | `calibrate_crawled.py:75-87` — `MIN_WITHIN_TOLERANCE=3`, `MIN_QUALIFIED=3`; run gives 2 qualified. Criterion 1 fails on its own; T5–T7 aren't even needed for the conclusion |
| §0 | "Six exit criteria are listed" | ❌ **WRONG — there are seven** | `PHASE_3_builds_repo.md` exit block |
| §0 | "Two non-gate criteria outstanding/unverified" | ❌ **UNDERSTATED — three** (#2, #4, #7) | see §3 |
| §0 | "`ContentProfile` presets — flag as unverified, not failed" | ❌ **It is FAILED** | `core/sim/content.py` — **6 of 8 presets carry `provenance="assumption: …"` in their own string**; all target counts invented; every target stat `retail_hypothesis` (`:93-97`). Only `fight_duration` on 2 presets derives from real data (`:107-113`). No derivation tool exists anywhere in `tools/` or `ingest/` |
| §0 | "`ingest/logs/` does not exist (T6)" | ⚠️ **STRAWMAN** | `ingest/logs/` never appears in `PHASE_3`. The real T6 test is a *writer from a log into `builds.db`* |
| §0 | "T6 (log ingestion) does not exist" | ⚠️ **OVERSTATED** | Parsing is done and Ascension-verified (`tools/log_parser/combat_log_parser.py`, `decode_alc.py`); the correlation rule is fully specified and seeded (`seed_confirmed.py:47`); the `* WoWCombatLog.txt` glob is implemented at `calibrate_vs_log.py:314`. Missing: mtime windowing (**zero** `st_mtime` uses in the tree), UTC conversion, and the DB writer. Correct wording: *"T6 exists as verified manual tools, unsystematised."* Small-to-medium, not a phase |
| §0 | "T5 exists only as the stat exporter" | ✅ **SUBSTANTIVELY RIGHT, but the priority call is wrong** | `.toc` declares **no `## SavedVariables:`**; no inspect hook, no talents/ranks/timestamp. ~70% remaining. **But** ALC + `decode_alc.py` already decode *every player build in a log* (625 records from one file, byte-verified) — so T5's purpose is largely served through T6's channel. **T5 should be demoted, not reinstated** |
| §0 | "no hooks directory (T7)" | ✅ **CORRECT test** | T7's spec is literally a `SessionStart` hook + `tools/session_hooks/`. Neither exists. `SCHEDULING.md` / `run_crawler.bat` are **T8** (crawler), orthogonal. ~100% remaining, and it hard-depends on T6 |
| §1 STEP 2 | "rider stamped **before** the re-run ✅" | ⚠️ **PLAUSIBLE, UNVERIFIED — not ✅** | `git log --follow predictions/CALIBRATION_TOLERANCE.md` → the addendum, the `QUALIFIED_COVERAGE_PCT` constants **and** `load_scraped_coefficients.py` all land in the *same commit* `79c6568`. Nothing contradicts the claim; nothing corroborates it either. Also: the file is in `predictions/`, not `primer/` as §6 implies |
| §1 | Gate = 5 of 41, 2 qualified; median coverage 37%; 323/177 conflicts; 74 proposals | 🔒 **UNVERIFIABLE BY ANY AUDITOR** | `.gitignore:10` excludes `data/derived/`; **no `.db` is committed**. The 323/177 figures exist only as a prose comment at `core/spells/mechanics.py:342-343` — no tool measures them, no test asserts them. See §4.F |
> 🛑 **RETRACTED — marked in `3f` F8, not rewritten.** The claim below that the
> site's `casts` is `SPELL_CAST_SUCCESS`, and that *"crawl casts/sec is a
> faithful character-level APM measure"*, was **falsified by the 2026-08-06
> Frost Mage capture**. `SPELL_CAST_SUCCESS` and `SPELL_CAST_START` are
> **disjoint by cast type**: Elric's instants log `SUCCESS` and never `START`,
> his cast-time spells log `START` and never `SUCCESS` — **Frostbolt was cast
> 74 times and produced ZERO `SPELL_CAST_SUCCESS` events** while landing 52
> non-crit hits. The 93% / 97.3% agreement was measured on an **all-instant
> Hammerdin**, where it is correct and does not generalise: for a cast-time
> caster the site's `casts` counts only the instant portion of the rotation.
> Measured across the cohort, it fails for **22 of 41** members.
> Detail: `data/source/captures/2026-08-06_elric_mage_frost/README.md` and
> `primer/FINDINGS_mage_capture_2026-08-06.md` §1. This document is kept as the
> record of what was believed at the time.

| §2 | Four log-upload findings (exactness, `casts`=`SPELL_CAST_SUCCESS`, `deaths` unobtainable, buff layer ×1.45) | ✅ **SOUND, and the best work in the session** | Independent reproduction of the 25.1% figure to one decimal is a genuine check digit |
| §3a | Coefficient double-count fixed | ⚠️ **PARTIAL** — see §4.B |
| §3b | Boomcat retracted (APM ratio 0.24 vs Elric's 0.38) | ✅ **CORRECT and correctly retracted** | Rule 7 honoured |
| §3c | Over-claimed against `casts` | ✅ correctly retracted | |
| §4 | "T6\* — conversion mechanics… no data needed" | 🔴 **DANGEROUSLY WRONG** — see §4.A |
| §4 fn | "`T6` naming collision — worth renaming" | ❌ **MASSIVELY UNDERSTATED — all eight numbers collide** | see §4.G |

---

## 2. The fourth thing `3c` got wrong (it listed three)

**It reported Righteous Vengeance as unbuilt work. It is built, it has never once run, and
turning it on as specified would corrupt the gate.**

```
core/sim/tiers.py:439      if ev.get("crit_damage"):
core/sim/ability_model.py:826-836   per_event.append({ "event_key", "kind", "school",
                           "source_spell_id", "via", "attributed", "occurrences",
                           "mean_each", "mean_total", "p_land", "p_crit" })
```

`grep -rn "crit_damage"` across the whole tree: the key `crit_damage` is **read in exactly
one place and written in none.** Every sim run since `2e` has therefore taken the `else`
branch at `tiers.py:453` and emitted *"Righteous Vengeance NOT modelled"* — a warning that
was printed on every gate run and never read.

Two consequences the plan does not see:

* **Blast radius is 41, not 9.** `_add_swing_sources` is called from `fast_sim`
  (`tiers.py:171`) — the tier `calibrate_crawled.py:70,426` uses — with **no check that
  61840 is in `build_spec.talents`**. Fix the key without adding a talent gate and ~30% of
  crit damage lands on **every** cohort character. Only 109 of 371 crawled level-60 boards
  hold RV. Ari (−10.3%) plausibly flips to over-prediction; the 8 existing over-predictors
  get worse.
* **The "two independent measurements" framing is loose.** ×3.18 measures the *game's*
  buff response; 228× measures *our model gap*. They are not two readings of one quantity.

> **Action:** T6\* is not "implement conversion mechanics". It is **"fix a dead code path
> and add the talent gate it never had, then measure the cohort-wide delta shift before
> accepting it."** Different task, different risk, different review.

---

## 3. Phase 3 exit criteria — true status

| # | Criterion | Status | Evidence |
|---|---|---|---|
| 1 | ≥3 real characters within tolerance, **per content profile** | ❌ **NOT MET** | 5 pass / 2 qualified vs `MIN_QUALIFIED=3`. The *"per content profile"* sub-clause is **separately unverified** — `calibrate_crawled.py:137` maps `content_type`→preset but the gate never partitions by it |
| 2 | Every crawled record resolves via crosswalk; **zero string matching** | ❌ **NOT MET** | `corpus.py:555-582` writes `spell_id_confidence='unresolved'` on misses, so "every" isn't structurally guaranteed. And "zero string matching" is literally false — `snapshot_gear.stats_match_type='name_fallback'` (98 rows) is item-name matching, **retained by design** |
| 3 | Inference proposes crit-table verdicts for top ~50 abilities | 🔒 **UNVERIFIABLE** | Tool exists (`inference.py:77-190`, Wilson intervals). Output is gitignored |
| 4 | ≥1 default uncertainty range replaced by a **measured** CI | ❌ **NOT MET — worse than reported** | `core/sim/uncertainty.py:44-80` `POLICY` has **no `measured` band at all**. `inference.py:48` `promoted` flag exists; **no code anywhere sets `promoted=1`**; nothing writes `basis='measured'`. The mechanism the criterion needs *does not exist* |
| 5 | `find_builds()` answers the multi-ability queries | ✅ **MET** | `core/builds/search.py:24` + seven T3 analyses |
| 6 | Every parse/snapshot patch/realm/season stamped | ✅ **MET** | `corpus.py:53,113,123` |
| 7 | `ContentProfile` presets derived from real encounter data | ❌ **FAILED** (reported as "unverified") | `content.py` — 6/8 presets self-declare `"assumption: …"` |

**Net: 2 met, 4 not met, 1 unverifiable.** The handoff's framing ("the gate plus two
loose ends") is optimistic by a factor of two.

---

## 4. New defects the handoff did not surface

Ranked by what they cost.

### A. 🔴 Righteous Vengeance — dead + ungated
Covered in §2. `tiers.py:439`, `tiers.py:171`.

### B. 🔴 The dedupe fix reopens its own bug on an unknown source
`core/spells/mechanics.py:398-402` selects on `_COEFF_SOURCE_RANK.get(source, 99)`.
Any source string **absent from the hardcoded dict ranks 99**. Two unknown sources tie,
both survive as `winners`, and if their `component` differs (or one is NULL) **both are
emitted and summed — the original Mongoose Bite bug, reachable again.** There is no
validation that every `source` in `spell_scaling` appears in the rank table; add a
better source and forget the dict and it silently ranks *last*, behind `export_tooltip`.
(`core/sim/cache.py:84-87` does warn for the analogous omission — the pattern exists, it
just wasn't applied here.)

**Related:** same-source duplicate terms are **silently destroyed, not conflicted**
(`:404-409`). `migrate_spell_scaling_ranks` (`:790-796`) demonstrably produces them via
`rank_scaling.py:81-85`. That is exactly the direct+periodic pair the schema comment
(`core/db/schema.py:66-70`) says must never be collapsed.

### C. 🔴 Rule 1 violated: `spell_scaling` has **no provenance columns at all**
`core/db/schema.py:53-72` — no `evidence_ref`, no `confidence`, no `verified_at_patch`,
no `realm`, no `season`. `source TEXT DEFAULT 'export_tooltip'` is nullable with a
default, so a row that omits it **fabricates tier-6 provenance**. That happens today:
`ingest/export/seed_cp_scaling.py:53` hand-inserts Holy Finish SP/AP 0.02 without
`source`. Contrast `spell_effect_values` (`:260-263`) and `spell_mechanics` (`:355-363`),
which do enforce NOT NULL. The coefficient table — the one now load-bearing on 177
judgement calls — is the *least* provenance-enforced table in the schema.

### D. 🔴 Rule 3 half-violated, and the operator-facing count is wrong
Both conflicting rows **do persist** (each writer deletes only its own source partition:
`load_scraped_coefficients.py:183`, `seed_hand_coefficients.py:70`) — so "record both" is
satisfied. But "flag, queue" is not: coefficient conflicts never enter `FieldSet.conflicts`
(`mechanics.py:118-146`), `conflicts_json` is NULL for all 177, and
`stats["with_conflict"]` (`:753`) counts only `fs.conflicts`. So
**`cli/mechanics.py:133` prints "rows with a source conflict (surfaced not resolved)" and
that number is wrong by ~177.** The disagreement is visible only to someone parsing a
JSON blob. No `open_questions` row exists for them.

### E. 🔴 The Holy Shock circularity guard is **prose that was never implemented**
`ingest/export/seed_epistemics.py:143` asserts *"Holy Shock is EXCLUDED from the
Holy-group constant."* Grep: `ascension_measured_provisional` appears in exactly two
files — the seeder (`seed_hand_coefficients.py:30,62`) and the precedence dict — and
**zero times in `tools/`**. `calibrate_vs_log.py:400` calls `sim_base()` (which now
embeds 0.40) and pools Holy Shock into the Holy school group at `:414` with no source
filter; `KNOWN_BROKEN` (`:377-384`) does not list 25902. The circularity is real,
unguarded, and *documented as guarded*. That last part is the dangerous bit.
(Mitigating: exactly **one** back-solved value exists. Not a class.)

### F. 🟠 The project's headline numbers are not reproducible by anyone but the owner
`.gitignore:10` excludes `data/derived/`; `builds.db` is gitignored **and** its builder
(`ingest/logs_gg/build_builds_db.py`) is **not in `rebuild.py`'s `CHAIN` and not in any
`.bat`**. So the gate cohort, the 37% coverage, the 74 proposals and the 323/177 conflict
counts exist only on one machine, produced by a manual step. Every claim in this project
is a *trust me* to an auditor. Cheap fix: append `build_builds_db.py` to the chain, and
commit a small `gate_manifest.json` (counts + hashes, not bulk) per gate run.

### G. 🟠 Eight T-number collisions across three documents, not one
`AUDIT_3C_handoff.md` footnotes only T6. In fact **every number 1–8 collides**:

| # | PHASE_3 | PLAN_3C |
|---|---|---|
| T1 | Normalise the crawl | report slice accuracy |
| T2 | Pooled mechanics inference | log admissibility |
| T3 | Search and analysis | fix over-predictions |
| T4 | Gear data | trigger-edge reachability (687 pts) |
| T5 | The capture addon | pets (440 pts) |
| T6 | Combat log ingestion | conversion mechanics |
| T7 | Session-start automation | class-A reachability (1303 pts) |
| T8 | Refine the crawler | re-run and report |

PHASE_2 is a third space (its T8 is *Calibration*). Worse, **the handoff collides with
itself**: §0 line 18 says "T5(addon) → T6(logs) → T7(automation) deferred"; §4 line 154
says "T4, T5, T12, T7 — trigger-edge reachability, pets, coefficient-conflict review,
class-A reachability". Same three tokens, six meanings, 135 lines apart.
**Rename PLAN_3C's to `C1…C13` before any work starts.** 5 minutes; prevents a
session-costing error.

### H. 🟠 Contaminated regression targets from a wrong-defaults run
`predictions/pred_2026-08-05_elric_paladin.md:62` records a `calibrate_vs_log.py` run with
**no stat flags** — i.e. the stale defaults (`:302-305`, AP 584 / SP 533 / 585–669 from
the 2026-08-03 build doc). The 1.31 school ratio downstream is already demoted, but the
**pair ratios are not**: `PHASE_2_simulation.md:470` states predicted **1.718** and
**0.769** and calls them *"the targets a talent model must reproduce."* `pair_ratios()`
(`:461`) takes the char-state built from `args.ap/args.sp/args.weapon_*`, and both sides
carry flat + SP/AP terms in different proportions — **so those targets are a function of
the wrong stat block.** T13 must re-derive them at AP 141 / SP 638, not just fix flags.

### I. 🟠 `--all-logs` defaults should be a refusal, not a correction
T13 as written swaps stale numbers for fresh ones. Rule 2 says *unconfirmed = flagged,
never silently defaulted.* Make the stat block `required=True`. The alternative in
PLAN_3C — "read it from a named capture" — is worse: it silently rebinds to whatever that
folder holds later.

### J. 🟠 Engine bugs a Hammerdin cannot expose
All in shared paths, all invisible on an all-instant single-filler melee build:

* **`tiers.py:137-141`** — in `fast_sim`, the **first filler consumes the entire GCD
  budget** (`gcd_budget = 0.0`); every later filler gets 0 casts. The comment two lines
  up says "fillers split whatever budget the cooldowns left, in priority order." The code
  does not. **This is the tier the calibration gate runs on.**
* **`tiers.py:197`, `apl.py:118`** — `combo_points` is **never incremented anywhere**, so
  `combo_points_at_least` (which `apl_gen.py:91` emits for every finisher) can never be
  true. Finishers are never cast in `medium_sim`; `ability_model.py:420-425` scores CP
  terms at 0 CP in `fast_sim`.
* **`apl.py:19-32`** — no target-debuff/DoT-uptime condition exists; `apl_gen` gives
  fillers `always`. **A DoT is re-cast every GCD with its entire duration's damage
  re-scored each time.**
* **`tiers.py:198-199`** — `self_health_pct`/`target_health_pct` fixed at 100. Execute
  windows and the solo self-sustain branch are dead code.
* **`apl_gen.py:62-63`** — fillers sorted by damage *per cast*, not per GCD/cast-time
  (docstring line 10 claims otherwise). Penalises any mixed-cast-time caster.
* **`ingest/logs_gg` / `corpus.py:614`** computes `dps = (total_damage + pet_damage)/dur`
  while **no pet model exists in `core/sim`** — pet classes are guaranteed to miss.
* **`core/sim/mechanics`** resolves `is_channeled` (`spells/mechanics.py:232`) and the sim
  **never reads it** — a channel costs one GCD and delivers all ticks.

### K. 🟡 Automation defects
* **`crawl_ascensionlogs.py:783`** — only *request-level* `ERRORS` gate exit. A 200 with
  changed HTML yields 0 phases → 0 leaderboards → **exit 0, day stamped success, empty
  capture auto-committed.** No row-count or delta canary anywhere.
* **`crawl_ascensionlogs.py:645`** — unattended `git add data/source` is **unscoped**: any
  working-tree change under `data/source` (half-edited scouted JSON, a capture folder
  mid-copy) gets swept into an auto-pushed commit. The baseline task got this right
  (`run_baseline_scheduled.bat:58` scopes to one folder); the daily one did not.
* **`run_crawler_scheduled.bat:34-35`** — changelog failure prints `[WARN]` and the exit
  code is ignored, so a day of records can be stamped `patch_date: null` silently.
* **`SEASON` is hardcoded in five places** (`crawl_ascensionlogs.py:82`, `cli/mechanics.py:38`,
  `cli/relationships.py:30`, `resolve_numeric_formulas.py:56`, +realm). **Phase 2 flips
  2026-08-08** — that is two days out and needs five hand edits, with nothing asserting the
  constant against `/api/phases`, which the crawler already fetches.
* **`rebuild.py` partial failure is unsafe**: 21 steps as separate subprocesses (`:86`),
  no cross-step transaction, no temp-DB-and-swap, no backup. Step 15 failing leaves
  `ascension.db` half-seeded and *readable*, with nothing marking it invalid. (A
  *complete* run is idempotent — `build_index.py:86` unlinks first.)
* Docs say 20 steps (`Session_2026-08-06_3b_preflight.md:13`); the chain has 21.

### L. 🟡 `api/` is a 12-line empty `__init__.py`
`ARCHITECTURE.md` §2.7 rule 4 states the layering `cli → api → core`. Seven CLIs call
`core/` directly; `api/` has **zero functions**. `PHASE_4` then says *"the web app is a
thin layer: `api/` already exists"* — that is false comfort baked into a future phase's
premise.

---

## 5. "Does it work for any DPS class, or just my Hammerdin?"

**Short answer: the code is class-neutral; the evidence base is not. That asymmetry is the
single biggest structural risk in the project right now.**

**What is genuinely generic** (and this is real, not lip service): `combat_engine.py`,
`content.py` (keyed on content, not class), the talent decoder (`talents.py:52-56` knows
all eight hybrid schools), `builds/corpus.py`, `inference.py`, `search.py`, and the APL
condition grammar — which already has mana/rage/energy/combo-point/execute types defined.
The corpus is **not** paladin-skewed either: 371 level-60 decoded boards split intellect
79 / strength 50 / spirit 48 / duality 40 / agility 38; **Hammerdin appears on 9 boards.**

**Where the Hammerdin has leaked into logic:**

| Where | What |
|---|---|
| `tiers.py:432-457` | RV applied to every build, ungated by talent (§2) |
| `tiers.py:415-430`, `swings.py:57,185` | Seal-rider proc block runs unconditionally — a Mage sim result carries a Seal-of-Command warning. Damage is 0, so noise not error, but it's paladin logic in a shared path |
| `tiers.py:168-170, 323-325` | `melee_ability_hits` counts only schools `("Physical","Holystrike")` — Shadowflame/Froststrike/Shadowstrike melee builds are **not counted as melee** |
| `swings.py:69-81` | `RIGHTEOUS_VENGEANCE_SPELL_ID=61840`, `JUDGEMENT_BY_SEAL`, `JUDGEMENT_PRESS_CARDS` — paladin spell IDs hardcoded in `core/`, not in a seed table |
| `buffs.py:78-90,138-151` | `consecrated_weapon` (a paladin imbue) sits in the `party`/`raid` presets. No caster-side buffs (Curse of Elements, Totem of Wrath, Demonic Pact) exist even as named gaps |
| `calibrate_vs_log.py:299-340` | Defaults are Elric; weapon `speed: 3.57` hardcoded with **no CLI flag**; no `--spell-crit`, `--haste`, `--ranged-ap`, or resource flag. **A caster must pass a fake weapon to run the tool at all** |
| `fixtures/`, `check_sim_engine.py:270-297` | The **only** committed fixtures are `build_elric_paladin.json` + `apl_paladin_{observed,optimal}.json`. The engine's whole regression harness is one paladin |

**🔴 The one that matters most — the guard fails open off-Hammerdin.**
`calibrate_vs_log.py:380-386`: `check_alignment()` `continue`s when none of the paladin
abilities in `ID_ROUTING` / `ALIGNMENT_ZERO_CRIT` appear. So **for a Mage log the field-
alignment gate passes vacuously and never says it could not run.** That is precisely the
failure mode primer v31 §5 warns about, implemented.

**Archetype readiness:**

| Archetype | Blocking gaps |
|---|---|
| Caster DoT (Warlock/Shadow) | DoT re-scored every GCD, single-filler bug, no mana derivation, no caster buffs |
| Caster burst (Mage) | Cast-time-blind filler ordering, channels unmodelled, calibration needs a fake weapon |
| Melee physical (Rogue/Warrior) | Combo points never increment → finishers never fire; no execute window; no energy/rage |
| Pet class (Hunter/Lock/DK) | No pet model at all, while gate DPS **includes** pet damage; no ranged attack table |
| Hybrid caster/melee | Hybrid school misclassification, melee/spell haste move together (`weights.py:28-42`) |

> **The fix is cheap and it is the highest-leverage thing on this list.** Add **two**
> non-paladin fixtures — one combo-point melee, one DoT caster — to `check_sim_engine.py`.
> That single change converts every item in the table above from an unknown-unknown into
> a failing test, and it costs a session. Do it *before* adding any mechanics.

---

## 6. Architecture: robust, or drifted?

**Held (verified, not taken on trust):**
* `core/` purity — ran it: **47 files checked, 0 violations.** This is a real, enforced
  invariant and it is the thing that will let a web app reuse the logic later.
* Refuse-rather-than-default discipline is genuinely pervasive — the weapon-damage parser
  self-checks against the description's stated DPS and returns nothing on failure;
  `scrape_ascension_db.py` hard-stops on 403/429 rather than retrying; the scraped
  coefficients refuse on a base-value disagreement. This is the project's best feature.
* Patch/realm/season stamping on parses and snapshots.
* Retractions are explicit and recorded (Rule 7 is being honoured well).

**Drifted:**
* **Rule 1** — `spell_scaling` has no provenance columns (§4.C).
* **Rule 3** — conflicts recorded but not flagged/queued, and the count reported to the
  operator is wrong (§4.D).
* **Rule 2** — a documented exclusion that isn't implemented (§4.E) is a *worse* failure
  than a missing one, because it reads as satisfied.
* **`cli → api → core`** never exercised; `api/` empty (§4.L).
* **Built but absent from `ARCHITECTURE.md` §4's layout**: `tools/analysis/pooled_inference.py`,
  `core/builds/group_buffs.py`, `core/spells/db_ascension.py` plus a whole third-party
  scrape source, `predictions/` markdown ledgers alongside the `predictions` table,
  `reviews/` human-approval gates, `bugs/`. None of these are *wrong* — but the
  architecture doc no longer describes the tree, and doc/reality drift is the failure mode
  the monitoring primer itself names as most expensive.
* **§2.4 inverted**: uncertainty ranges moved *out* of Phase 1's truth table into a sim-layer
  policy table because `spell_mechanics.uncertainty_json` is a ±0% heuristic. Phase 4's
  `contribution_low/high` "inherits sim uncertainty (§2.4)" — it would inherit a stated
  assumption, not a measurement.

**Verdict: the skeleton is sound and worth keeping. The connective tissue between "we have
a rule" and "the code enforces the rule" is where the rot is.** Every one of the three rule
violations is a ~1-hour fix. None requires a redesign.

---

## 7. Update pipelines — how automatable are they today?

| Source | Rating | Owner toil | Failure detection |
|---|---|---|---|
| ascensionlogs.gg crawl | ✅ **FULLY AUTOMATED** — Task Scheduler at-logon+5min, once/day guard, registered by a *committed* PowerShell script | none in steady state | 🔴 **none that matters** (§4.K) |
| api.ascension.gg changelog | ✅ automated (same task) | none | 🔴 exit code swallowed |
| Historical backfill | 🟡 manual by design, correctly so | start before bed | resumable, Ctrl+C safe |
| db.ascension.gg scrape | 🟡 fully manual, **correctly** — never referenced by any `.bat`/`.ps1` | run after corpus growth | per-row cross-check verdict; hard stop on 403/429 |
| Game client DBC | 🟠 double-click `.bat`, then tell Claude | close game, wait, report | 🔴 none — **its exporter was broken from `2e` to 2026-08-06 while every routine rebuild reported green** |
| spell-export.json / Cards.txt | 🔴 fully manual, per-patch | re-export from client | none |
| Combat logs | 🔴 **fully manual and it terminates** | capture, upload, ask Claude | n/a |
| `ascension.db` rebuild | 🟢 one command, no prompts | after seed changes | `audit_gaps.py` as step 21 |
| `builds.db` | 🔴 **not in the chain, not in any `.bat`** | manual, every time | none |

**Rate-limit/ban risk: low and well-handled.** Nothing scheduled touches db.ascension.gg.
The crawler is sequential, 0.6s delay, 3-try backoff, 30s on 429/5xx, capped at 25 reports,
2h task limit. This was done right.

**The combat-log path is the honest answer to your question.** Trace it: ALC → 
`WoWCombatLog.txt` → `parse_log.py` → `*.summary.json` → **`.gitignore:4` excludes it** →
nothing reads it. `calibrate_vs_log.py` prints to stdout. `prediction_outcomes` is only
ever populated from hand-written `seed_predictions.py`. **Every log finding in this project
survives solely as prose a human typed into a seed file.** That is the toil, and it is
exactly PHASE_3 T6.

**Six cheap wins, in order of value per hour:**

1. **Row-count canary in the crawler** (~20 lines): compare per-writer counts against the
   previous date's manifest; exit nonzero if leaderboards/phases drop >50% or hit zero.
   Turns the top silent failure into a non-stamped, self-retrying run.
2. **Scope the auto-commit** to `data/source/crawl` + `data/source/changelog` (mirror
   `run_baseline_scheduled.bat:58`). One line. Kills the "unattended job commits my WIP" class.
3. **Assert `SEASON`/phase against the live `/api/phases` response** already in hand.
   **Do this before 2026-08-08.** Makes the phase flip self-announcing instead of silently
   mis-stamping every record.
4. **Propagate the changelog exit code** — a null `patch_date` should fail the day, not warn.
5. **Append `build_builds_db.py` to `rebuild.py`'s chain** — removes a manual step
   everything analytical depends on, and makes the gate reproducible.
6. **Wire T6's log path**: glob `* WoWCombatLog.txt`, correlate by filename-start/mtime-end,
   write into `builds.db` + `prediction_outcomes`. **Owner input afterwards would be zero** —
   the logs are already on disk in a known directory.

Items 1–5 are roughly one session combined. That is the "minor user input" state you asked
about — you are about 80% of the way there, and the missing 20% is concentrated in one place.

---

## 8. Phase 4 readiness

Phase 4 is Parts A (kit discovery: graph motif → co-occurrence → **sim ablation** →
composition), B (acquisition cost, `build_feasibility`), C (principles, `BuildBrief`,
guide generator, addon config).

**Hard blockers — do not start Phase 4 without these:**

1. **Ablation runs on a sim that models a median 37% of a character's damage.** Concretely:
   Consecrated Holy Weapon is 25.1% of your own buffed damage and has **no modelled
   magnitude**. Ablate a kit and you measure its share of the *modelled 37%*, then report
   it as `pct_of_total`. **A kit whose members happen to be modelled reads as ~3× more
   critical than one whose members don't — so the chase list is ordered by modelling
   coverage, not by value.** And `criticality` ships as a NOT-NULL number with an
   `evidence_ref` attached. This is the single worst thing that could happen to this project.
   *Minimum mitigation even if you start early:* a **coverage guard on ablation** — refuse
   to emit a `lego_measurement` for any build below a stated modelled-damage threshold.
   Cheap, and it makes Part A safe to start incrementally.
2. **"Not measurably coupled" is decided by a policy table, not by data.** Ablation must
   beat the build's uncertainty band; that band is `uncertainty.py`'s documented guess.
   Loose → everything decouples; tight → noise reads as coupling. Exit criterion 4 (a
   measured CI) is the fix, and its mechanism doesn't exist yet.
3. **Part B has no Darkmoon-legal data foundation.** The only source with essence costs is
   the Area-52/Elune builder, which `seed_confirmed.py:146` explicitly says **may not be
   applied to Darkmoon**. Guarantee-slot state is entirely unmodelled (`grep -i guarantee`
   → prose only). So `build_feasibility` would return `hard_feasible` from rarity +
   `owned_cards` alone — meaning **it cannot detect the one thing Phase 4's exit criteria
   grade it on** (a historically-known infeasible build). Either get Darkmoon acquisition
   data or descope Part B to rarity + ownership and label it. Do not ship `expected_cost`.
4. **243 of 243 amplifier rows are unapproved** in `reviews/amplifier_review.md` — zero
   `[x]`. Motif mining runs on a graph missing most amplifier reach (218 `amplifies`, **9**
   `amplifies_school`). The Cleave Kit regression target would be rediscovered via the one
   hand-seeded row, not from data. Approve or explicitly reject them; discovery quality is
   bounded by this.

**Also missing but not blocking:** `core/kits/` and `core/theory/` don't exist;
`character_scenario_dps` (SCORECARD axes 1–3) has no code; `Metric.EFFECTIVE_HP` /
`SURVIVAL_TIME` / `THREAT` / `THROUGHPUT_PER_MANA` are enum members that are **never
computed anywhere** (so tank/healer kit ranking is impossible today); `owned_cards` has no
`user_id`; `gear_tier_stats` has `phase_label` NULL everywhere and **Phase 2 flips
2026-08-08**.

**Can run in parallel with Phase 3 cleanup, genuinely unblocked:** Part C1 (principles
corpus) — it has no sim dependency and `confirmed_facts`/`open_questions`/`retractions`
already carry most of it.

---

## 9. The corrected plan

Folding `3c`'s recommendations into the greater plan, with the ordering fixed.

**Step 0 — hygiene, ~1 session, do all of it before any modelling work**

| | task | why |
|---|---|---|
| 0.1 | Rename PLAN_3C `T1…T13` → `C1…C13` | §4.G. 5 minutes, prevents a session-costing error |
| 0.2 | Add 2 non-paladin fixtures (CP melee + DoT caster) to `check_sim_engine.py` | §5. Converts 6 unknown-unknowns into failing tests. **Highest leverage item in this document** |
| 0.3 | `spell_scaling` provenance columns NOT NULL; validate every `source` against `_COEFF_SOURCE_RANK` and hard-fail on an unknown | §4.B, §4.C |
| 0.4 | Route coefficient conflicts into `FieldSet.conflicts` + an `open_questions` row | §4.D — fixes a wrong operator-facing number |
| 0.5 | Implement the Holy Shock exclusion that `seed_epistemics.py:143` claims | §4.E |
| 0.6 | Crawler canary + scoped auto-commit + changelog exit code + `SEASON` assertion + `build_builds_db.py` into the chain | §7. **The `SEASON` one is time-critical: Phase 2 flips 2026-08-08** |

**Step 1 — the instrument, before anything is measured with it**

| | task | change from `3c`'s order |
|---|---|---|
| 1.1 | **C11 (Elric snapshot from ALC)** — **and an explicit exclusion in `candidates()`** | 🔺 **Moved to first.** `calibrate_crawled.py:99-134` filters on level/gear/cards/lag with **no source filter** — giving Elric a `character_snapshots` row makes him a gate candidate automatically and the cohort silently becomes 42 with the one privileged-input character in it. "Instrument, not a count" currently exists only in prose |
| 1.2 | **C13** — make the stat block `required=True` (not "fix the defaults"), **and re-derive the 1.718 / 0.769 pair targets** at AP 141 / SP 638 | §4.H, §4.I. Falls out of 1.1; the stale regression targets in `PHASE_2_simulation.md:470` are live contamination |
| 1.3 | **C1 (slice accuracy)** + append the ~80% derivation to `CALIBRATION_TOLERANCE.md` as a **dated successor criterion**, effective next gate | see below |

**Step 2 — modelling, each with a before/after slice-accuracy reading**

| | task | change |
|---|---|---|
| 2.1 | **C6** — fix `crit_damage` emission **and add the talent gate**, measure cohort-wide delta shift **before accepting** | 🔺 Reframed from "implement" to "un-break and gate" (§2) |
| 2.2 | **C10 → C9** — but require a **second Holy character** before claiming "one mechanism" | Five spells, all Holy, all one character, all one stat block, three summoned by one talent = **one measurement with five readings**, not five |
| 2.3 | C4, C5, C12, C7 | unchanged, but pre-register expected coverage/slice movement in `predictions` first |
| 2.4 | Fix the `fast_sim` filler bug (`tiers.py:137-141`) | 🆕 It's in the tier the gate uses |

**Step 3 — reinstate the deferred chain, re-scoped**

* **PHASE_3 T6 (log ingestion): reinstate, and promote.** Everything §2 of the handoff did
  by hand *is* T6. It's small (parser done, correlation rule seeded, glob written) and it
  removes the largest single source of owner toil.
* **PHASE_3 T5 (capture addon): demote, don't reinstate.** ALC + `decode_alc.py` already
  decode every player build in a log. T5's value case is much weaker than when it was
  deferred.
* **PHASE_3 T7 (session automation): keep deferred** until T6 lands (hard dependency), but
  the patch-check half is independent and cheap.

**Two standing rules to adopt now:**
* **Hold out ≥5 of the 41 from all tuning as a named validation set, named before the
  work.** There is currently no overfitting control anywhere in PLAN_3C — T8 is a post-hoc
  read of the same cohort the fixes were tuned to lift. The mechanism to do it right is
  already built and unused: `predictions`/`prediction_outcomes` refuses to overwrite a slug,
  which is exactly pre-registration.
* **Every coverage task reports slice accuracy before and after.** A task that raises
  coverage while dropping slice accuracy has moved the metric, not the model.

### On the ~80% arithmetic

The decomposition `slice_accuracy = (100+delta)/coverage` is **algebraically exact** ✓, and
~80% reproduces independently ✓ (set slice accuracy = 100 ⇒ `delta = coverage − 100` ⇒
`|delta| ≤ 20 ⇒ coverage ≥ 80`).

**But it is neither necessary nor sufficient.** 110% accuracy at 73% coverage gives −19.7%
and passes below 80. 80% coverage at 60% accuracy gives −52% and fails at 80. It's one
point on a 2-D curve, valid only at *exactly* 100% slice accuracy — which PLAN_3C's own §4
says won't happen.

**And the trajectory assumption is unsafe in a way the plan doesn't flag.** The formula
assumes the unmodelled slice is predicted at zero — true today by construction. The risky
assumption is that damage *added* by C4/C5/C7 arrives at ~100% fidelity. Your own data
refutes it: the out-of-catalog cluster reads **4.3–4.7× logged/base**, i.e. ~22% fidelity.
Covering the residual 42% at 22% fidelity buys **~9 delta points, not 42**. Worse,
**coverage is binary** (`modelled_damage_share`, `calibrate_crawled.py:171-224`, is a
membership test) — a spell modelled at 4.5×-under counts as *fully covered*. So coverage
work **mechanically raises coverage while depressing slice accuracy**, and Ari (156%) /
Malo (131%) can be lost by pure coverage work with no accuracy change at all.

**Keeping the 50% rider for this gate is the right call** — `CALIBRATION_TOLERANCE.md`'s
own closing rule ("a reason that does not reduce to 'the current number did not clear it'")
is exactly what an 80% edit would violate, and 80 > 50 means the rider is loose, not wrong.
Record the successor criterion, dated, **now** — before T8 re-runs — so it can never be
mistaken for post-hoc. **And record that 80% is conditional on slice accuracy = 100%**, or
it will be misread as a hard floor.

---

## 10. Open decisions for you

1. **The 177 coefficient conflicts.** Preferring the scrape is defensible (states the
   *applied* value, carries a check digit, catalog stores the wrong rank for ~half of
   multi-rank cards). The problem isn't the choice — it's that the choice is **invisible**
   (§4.D). Approve the precedence *and* require the queue.
2. **Holy Shock 0.40 vs 0.214.** Two clean options: (a) implement the exclusion that's
   already documented and let the scrape's 0.214 stand in calibration; (b) get one more
   independent Holy Shock measurement from a *different* character. I'd do (a) now and (b)
   when convenient — the current state, where the guard is documented but absent, is the
   worst of the three.
3. **T5/T6/T7:** my recommendation is **T6 yes (promote), T5 no (demote), T7 after T6**.
   Not a straight reinstatement of the chain.
4. **`ContentProfile` presets:** this is a *failed* exit criterion, not an unverified one.
   Either derive the 6 assumption-presets from the `encounters` table T1 built, or amend the
   criterion honestly. Do it **before** they become `lego_measurements` keys in Phase 4.
5. **The two non-paladin fixtures.** This is the one I'd push hardest on. Everything else on
   this list is a known problem with a known fix; the fixtures are what stop the *next* six
   unknown problems.

---

*Not verifiable from the repo (tier-2 data is gitignored and no `.db` is committed): the
5/41 gate result, 2 qualified, 37% median coverage, 74 inference proposals, 323/177
coefficient-conflict counts, the exact 41-character cohort, and 9-of-41 for Righteous
Vengeance. These are asserted in prose and reproducible only on the owner's machine. See
§4.F.*
