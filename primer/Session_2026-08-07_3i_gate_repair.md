# Session `3i` — 2026-08-07 — fix the log side, then move the gate for reasons you can name

> **`HISTORICAL`** — the record of session `3i`, a completed gate-moving session.
> May contain claims that are false today, and that is correct. Live state:
> `primer/PROGRESS.md`. *(Born with a status line, per `3f` F8c.)*

Work order: `primer/SESSION_3I_PRIMER.md` (now `SUPERSEDED BY` this file).
Audit implemented: `primer/AUDIT_3H_ADVERSARIAL.md`.

---

## §0 — The invariant, and how it was kept

🛑 **Every commit that moved the gate moved it for ONE reason, pre-registered in a
commit that landed before it.** Fifteen commits, in order:

| commit | block | gate pair | pre-reg / cause |
|---|---|---|---|
| `1b0ccb7` | A0 | 1/1/20.5% → 1/1/20.5% | census paste refresh (A4 caught the drift, as designed) |
| `953eccc` | A docs | unchanged | archive stale block, annotate stamped text, no `.py` |
| `227c0ff` | A code | unchanged | doc-sync parser (`check_engine_bugs_doc_sync`), E16, phrasing fixes |
| `61d9746` | A manifest | unchanged | regen carrying only the A2 annotations |
| `1f9c05e` | **B1 prereg** | unchanged | **committed BEFORE the E15 fix** |
| `9d84e02` | **B** | **1/1/20.5% → 1/1/26.3%** | E15 fixed at ingest + `dps`; P1 FALSE, diagnosed |
| `32ff19a` | B manifest | unchanged | carries B's numbers |
| `b356cea` | C | unchanged | `per_ability_accuracy.py` repaired (C1–C5, C7) — writes no manifest |
| `9311a04` | C manifest | unchanged | C5's new key only, every existing key byte-identical |
| `133d20f` | C6 | unchanged | repaired instrument re-run, committed summary, prereg CONFIRMED |
| `2b6c615` | D1–D8 | unchanged | predicates implemented; writes no manifest |
| `801d612` | **D prereg** | unchanged | **committed BEFORE the application** |
| `0fbffd5` | **D** | **1/1/26.3% → 0/0/26.3%** | admissibility applied; P1/P2/P4 CONFIRMED |
| `87b58b3` | D manifest | unchanged | carries D's numbers |
| `69f1e34` | E | unchanged | six check repairs; verified no numeric aggregate touched |

**Closing gate: 0 of 36 within ±20% · 0 qualified · slice accuracy 26.3% at
coverage ≥20% (n=23).** Holdout: not read this session (carried forward from
`3g`'s 0 of 5, 9.8% median, per the manifest's own carry-forward mechanism).

---

## §1 — Block 0: the phase boundary, checked live before any gear tier was read

Run first, read-only, against the live `/api/phases` endpoint (headers matching
`crawl_ascensionlogs.py`'s own — the bare request 403'd, `HEADERS` succeeded):

* **Checked 2026-08-07T09:31:37Z.** Payload: Phase 0 (closed), `Phase 1 -
  Zul'Gurub` (`id=2`, active, `start_date` 2026-07-31T18:00Z), `Phase 1.1`
  (`id=3`, `phase_number=2`, a **child** of Phase 1). No Phase 2 record.
* `assert_phase()`: **PASS**, live active top-level phase equals
  `EXPECTED_PHASE_NAME`.
* `phase_guard()`: `refuse_reason=None`, boundary **ARMED** at
  `2026-08-08T00:00:00+00:00` (no window reaches it).
* `resolve_phase()` exercised live: a 2026-08-07 capture resolves to `Phase 1 -
  Zul'Gurub`; a 2026-08-08T00:00:01Z capture resolves to `None` with the
  boundary reason; `horizon=None` fails closed with its stated reason.
* **The flip had NOT happened.** `boundary_passed_yet: False` (checked at
  2026-08-07T09:31, ~14.5h before the boundary).

🛑 Per the work order: since the flip had not happened, no `EXPECTED_PHASE_NAME`
bump or corpus re-derivation was needed, and no gear tier was read before this
check ran. STOP-POINT 0 did not trigger.

---

## §2 — What each block did, and its measured outcome

### A — documents (§Block A)

`PROGRESS.md:527-580` (the stale "3e IS DONE" / "FIX E13 FIRST" block that had
stood as live instruction for two sessions after both defects were fixed —
`AUDIT_3H`'s highest-severity finding) archived into the same
`<details><summary>Superseded` pattern as its siblings. `PROGRESS.md:73`'s
holdout median corrected to `9.8% (n=4)`. `ENGINE_BUGS.md`'s "enforced in both
directions" claim made TRUE: `check_engine_bugs_doc_sync()` parses the
document's open entries and asserts set equality against `EXPECTED_FAILURES`
— GREEN at 11=11 (later 10=10 once E15 closed), registered mutation M31 (delete
E16's Checks row) verified RED via a real source edit, restored. The header
invariant now states its own exemption (E8 and the without-checks list already
disclosed it; the rule now matches the practice). `CALIBRATION_TOLERANCE.md`
and `PLAN_3G`'s stale band figures annotated (kept verbatim, per the standing
rule against rewriting stamped text) with the post-E13 numbers. Three
hand-typed magnitudes replaced with generated ones in
`gate_manifest_3e.json`'s justification strings. A6 verified already done
(`CHAT_MONITORING_PRIMER` at v4, `SESSION_3H_PRIMER` already `SUPERSEDED`).

### B — E15 fixed at ingest + `dps`

**Pre-registered** (`predictions/prereg_3i_e15.md`, before the fix): the
rows[]-canonical decision (Q2 default — the owner-merged `rows[]` copy is
canonical, the per-pet restatement is dropped from `ability_performance` and
preserved separately), predicted the ingest fix would move slice DOWN toward
19.8% (the known consumer-dedupe-only pair), with the biggest movers being the
named pet-exposure characters.

**Fixed:** `core/builds/corpus.py` — the endpoint's per-pet restatement no
longer enters `ability_performance` (E15's actual defect: an owner-merged copy
in `rows[]` and a restatement in `pet_spell_damage_by_owner`, both ingested);
it lands in a new `pet_ability_damage` side table, the attribution route E3
names as unbuildable from DBC. `encounter_performance.dps` is
`total_damage / duration` (the `+ pet_damage` term was adding the restatement
to a total that already contained it). `is_pet` column/PK left untouched (Q3 —
the schema change is deferred to its own commit).

**Measured: `1/1/20.5%` → `1/1/26.3%`.** P2 (counts unchanged), P3 (movers =
the named pet-exposure list, 21 up / 0 down) and P4 (coverage +0.44 mean)
confirmed. **P1 was FALSE — slice moved UP, not toward 19.8%.** Diagnosed: the
19.8% anchor was `3h`'s consumer-dedupe-only candidate, which corrected
coverage while leaving `dps` uncorrected — an internally inconsistent
intermediate state. In the full fix the logged-total correction cancels inside
`slice = (100+delta)/coverage`, and the **matched-mass** dedupe (halved
pet-class auto ratios) dominates, raising slice per pet owner. Chastie moved to
−4.3% (would now pass ±20%); the 20% coverage floor correctly holds her NOT
SCOREABLE at 6.8% coverage — the floor doing exactly the job it was stamped
for.

The 1,208 owner<pet groups: **located, not explained** — 0 occur in any
`boss_single` scope, concentrated in `trash_bundle`/`boss_group` at 5–1,800×
ratios with pet casts ≫ owner casts. Consistent with scope drift between the
payload's two blocks on aggregated scopes; registered in the E15 closure box
rather than resolved.

`check_e15_pet_row_double_count` left `EXPECTED_FAILURES` and runs as a hard
regression guard (PASS, 50.0).

### C — `per_ability_accuracy.py` repaired

C1: one policy for a duplicated `(spell_id, spell_name)` pair at all four
sites (query now `is_pet = 0`; residual same-id duplicates merged
deterministically). C2: the per-row `coverage_share_of_logged` sum-to-100
invariant is **asserted** (raises `AssertionError` on violation); mutation
M32 (scale `total_logged` by 1.01) verified RED (99.02), restored. C3: the
nondeterministic `logged_by_sid[r[0]] = r` last-wins dict replaced with a
deterministic merge, counted and printed. C4: the phantom-production cell
reported (170 producing sim keys with no logged row, 58.4% of cohort sim
damage). C5: paired medians over the same members added (removes the
selection bias between the headline and producing-only figures).

**C6 re-run, prereg CONFIRMED both ways**: absent share moved UP (62.2% →
63.9%), producing-ratio median moved little (0.253 → 0.273). Zero-count and
in-band percentages unchanged (25%, 11%). C7: `predictions/per_ability_summary.json`
committed — the distribution's summary stats, no longer the least verifiable
number in the project.

On the post-B corpus there were **zero** same-`(spell_id, spell_name)`
duplicate groups, so C1/C3's dedupe policy is currently dormant but
load-bearing against any future duplication class.

### D — the stamped admissibility rule, applied

**Pre-registered** (`predictions/prereg_3i_admissibility.md`, before wiring):
predicted `within ±20%` 1→0 (Boomcat flagged), qualified 1→0, no other count
change, slice unchanged.

**D1–D8 implemented** (own commit, no gate move): predicate 4 computed via
`core.builds.phases.resolve_phase` against the live `/api/phases` window
(replacing the hardcoded sentence that would have started lying tonight);
predicate 5 tested against the real lag value; `resolved_entries` and the
comparator context print beside every ratio; the fail-open regime counted and
reported as a lower bound; the comparator tightened (excludes
self-overlapping, sub-60s, and trash-tainted scopes; fixed a real bug where a
legitimate 0.0 APM comparator was silently dropped by a truthiness check);
`assert_stamped_thresholds()` verifies this module's constants against the
stamped text (GREEN 0.5/2/60; mutation M33 verified RED via a real source
edit, restored).

🚨 **Verifying D1–D6 surfaced a departure from the stamp, recorded before the
gate-moving commit**: the tightened comparator changed the blind roster from
the stamped 5-of-41 to **3 of 41** (Nodding, Boomcat, Deyindra) — Robottikyrpa
and Frediib no longer carry a confident APM ratio (their comparator sets
shrank below 2 qualifying scopes once the tightened filters removed
self-overlapping/short/trash comparators). Boomcat's own ratio moved
0.27→0.24, closer to `3c`'s original chat-side figure. The full-rule
falsifiability bar remained met via Nodding (predicate 3, untouched by the
tightening); under the narrower predicate `prereg_3h_boomcat.md` P9 actually
registered, the count is now 0. Reported in both prereg documents and
annotated into `CALIBRATION_TOLERANCE.md` (stamped text kept verbatim). This
did not change the Q4 default to apply — the tightening is a correctness fix,
not a fit to a wanted result.

**Applied** (own commit): `admissibility_for()` wired into
`calibrate_crawled.py`'s per-character loop, computed blind before the row's
verdict is finalised, overriding `within_tolerance` to `None` with the
pre-override verdict preserved under a separate key for auditability.

**Measured: `1/1/26.3%` → `0/0/26.3%`.** P1/P2/P4 CONFIRMED exactly. P3
confirmed with the caveat the prereg itself named (Nodding's verdict moves
False→None, a labelling change the prereg described as expected). A reporting
overlap this wiring introduced — a not-admissible character above the
coverage floor (Nodding, 58.2%) printing under BOTH the not-admissible line
and the misleading "below coverage floor" line — was found and fixed in the
same commit.

### E — the tautological/fail-open checks repaired

E1: the "split sums to `modelled_damage_pct`" arm was tautological by
construction (`keyed_zero = modelled - producing`, true of any two-way
partition regardless of the predicate). Replaced with a genuine cross-check
— the named zero list (built from `per_ability` + `producing_ids`) must sum
to the same share as `keyed_but_zero_pct` (built from `rows` +
`is_modelled`/`is_producing`) — two independent code paths. Mutation
(`is_producing → True`) verified RED via real source edit, restored.

E2: the "SAME key flips to producing" case used a positive spell id, for
which `is_producing` is *defined* as `producing_ids` membership — it could
never discriminate. Replaced with an auto-row fixture exercising
`is_producing`'s other branch (`autos_producing`), which a positive-id row
never reaches. Its own mutation (`autos_producing = False`) verified RED via
real source edit, restored.

E3 (found while fixing E1/E2): `auto_mh`/`auto_oh` are string keys in
`per_ability`; `logged_by_sid` is keyed on integer `spell_id`, so a
zero-producing auto's zero-list entry always misreported `logged_share_pct:
0.0` and sorted last — naming 0.0% of exactly the mass `keyed_but_zero_pct`
had just credited to it. Fixed via the same `is_auto_row` predicate the
numeric sums use; purely informational (no numeric aggregate changed —
verified the gate stayed at 0/0/26.3%, all bands identical).

E4: the `predictions/`/`primer/` status censuses passed vacuously on an
empty/missing directory. `len(files) > 0` added to both; verified the old
form passed on a nonexistent directory.

E5: `_status_census` matched any backticked/bolded status word anywhere in
the first 1200 characters, so prose mentioning a status word mid-sentence
misclassified the whole document. Fixed to match only a line (after
stripping a leading `>`) that *starts* with the marker — the actual
convention every status line follows. Verified against a synthetic
mid-sentence mention: old matcher said LIVE, new says unclassified. Full
census re-run unchanged (61 primer/ files).

E6: `--allow-dirty` recorded a bare boolean nothing read. Replaced with
`--allow-dirty-reason <string>`; `write_gate_manifest` records the reason
verbatim and refuses `allow_dirty=True` with no reason. Three existing test
fixtures updated; two new checks added and verified PASS.

Full `check_refusals.py` run: exit 0, all checks including six
new/rewritten ones PASS. Full `check_sim_engine.py` and
`check_gate_exclusion.py` runs: exit 0.

---

## §3 — STOP-POINT F invoked

Blocks A–E consumed the session. Per the work order: *"That is a good outcome,
not a failure."* **Block F (modelling) is handed to `3j`.** The repaired
distribution (`predictions/per_ability_summary.json`, `3i` C6) is the input a
`3j` modelling session should re-confirm targets against — not the pre-repair
one `3h` handed forward.

Visible levers, **not re-confirmed this session** (that re-confirmation is
`3j`'s first job, per the work order):

* **Elemental Blast** — still the largest single lever by inspection of the
  C6 per-character output (0.02–0.06 range across characters carrying 63–72%
  of their logged damage each).
* **The starved-allocation mass** — `zero-casts-allocated`, 11.3% of cohort
  logged damage in the C6 run (was 10.9% pre-repair).
* **The absent-key majority** — now measured at **63.9%** (was 62.2%), per
  C6's confirmed prereg outcome.

E9, E11, E12 keep their run green paths, untouched, ready.

---

## §4 — Exit conditions (work order §3)

| # | condition | met? |
|---:|---|---|
| 1 | Block 0 checked live, before any gear tier read | ✅ §1 above |
| 2 | `PROGRESS.md:527-580` archived; no un-collapsed "FIX E13 FIRST" outside a collapsed block or HISTORICAL doc | ✅ `953eccc` |
| 3 | E15 fixed at ingest + `dps`, one commit, pre-registered pair reported, closure box with measured numbers | ✅ `9d84e02`, `ENGINE_BUGS.md` E15 closure box |
| 4 | `per_ability_accuracy.py` repaired: shares sum to 100±ε and asserted; no nondeterministic drop; phantom cell reported; paired median printed | ✅ `b356cea` |
| 5 | Distribution re-run and re-stated, C6 prereg outcome recorded including direction | ✅ `133d20f`, both predictions confirmed |
| 6 | Summary artifact committed under `predictions/` | ✅ `predictions/per_ability_summary.json` |
| 7 | Admissibility rule applied; predicates 4/5 computed; `resolved_entries` printed; stamp↔code assertion registered | ✅ `2b6c615`, `0fbffd5` |
| 8 | E1–E6 landed; registered mutations verified to turn their arms red | ✅ §2 E block, all six verified via real source edits |
| 9 | Gate pair reported at every commit; every gate-moving commit preceded by its own pre-registration | ✅ §0 table |
| 10 | Holdout not read | ✅ carried forward from `3g`'s reading, never touched |

All ten met.

---

## §5 — Q1–Q5, defaults taken

| | question | taken |
|---|---|---|
| Q1 | A3: parser or downgrade? | **Parser** (the default) — `check_engine_bugs_doc_sync()` |
| Q2 | B2: which pet-damage copy is canonical? | **`rows[]`** (the default) — stated as a decision in the prereg |
| Q3 | B: schema change this session? | **No** (the default) — ingest only; `is_pet` column/PK deferred |
| Q4 | D: apply the admissibility rule despite the known hit? | **Yes** (the default) — applied in `0fbffd5` |
| Q5 | C7: which stats in the committed artifact? | **The printed summary block** (the default), per-character split included |

The owner was not reached during the session (autonomous run); every default
was taken as stated above, per the work order's own instruction.

---

## §6 — What `3i` hands to `3j`

* **Block F, whole**, per STOP-POINT F — re-confirm the levers listed in §3
  against the repaired distribution before picking a modelling target.
* **The gate reads `0 of 36 within ±20% · 0 qualified · slice accuracy
  26.3% (n=23)`.** The admissibility rule removed the cohort's only passer.
  This is the correct, intended-direction outcome of a stamp-first rule
  whose falsifiability bar was met before its result was known — not a
  regression to chase.
* **The comparator-tightening finding** (§2 D, `predictions/prereg_3i_admissibility.md`):
  worth the owner's attention as a standing question about how much of the
  original 5-of-41 stamp's falsifiability evidence survives a more correct
  implementation. Not blocking — the full-rule bar is still met.
* **The 1,208 owner<pet E15 groups**, still unexplained (scope drift between
  the payload's two blocks on aggregated scopes) — registered, not resolved.
* ⚠ **The phase boundary arms at `2026-08-08T00:00:00Z`**, ~14 hours after
  this session's Block 0 check. `3j` (or whichever session runs after the
  8th) must re-check `/api/phases` live before any gear tier read, per the
  same three defences exercised in §1.
