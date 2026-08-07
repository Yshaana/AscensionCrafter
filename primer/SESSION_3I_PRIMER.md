# SESSION `3i` — fix the log side, then move the gate for reasons you can name

> **`SUPERSEDED BY primer/Session_2026-08-07_3i_gate_repair.md`** — the work order for
> session `3i`, now run. The session record holds what actually happened, including
> the departures (the P1 diagnosis in Block B, the comparator-tightening finding in
> Block D). *(Reclassified at `3i` close-out, per its own expiry condition.)*

Predecessors: `primer/Session_2026-08-07_3h_measurement.md` (the session record),
`primer/AUDIT_3H_ADVERSARIAL.md` (the audit this order implements),
`primer/ENGINE_BUGS.md` (the defect registry), `primer/PROGRESS.md` (live state).

---

## §0 — Where things stand, and what kind of session this is

**`3h` was an instrument session and it did its job.** The gate read `1 / 1 / 20.5% (n=23)`
at every one of its ten commits, no file under `core/` was touched, both measurements were
pre-registered before they ran, and P4 was reported **false**. The result: slice accuracy is
no longer inferred. The sim is **absent** for most logged damage, **zero-producing** for a
tenth, and **wrong in both directions** on the rest — 17% of producing abilities are *over*
1.25×. **A single multiplier will not fix this model.**

`3h` also found **E15**: `ability_performance` stores pet damage twice, and
`corpus.py:594-614` adds `pet_damage` to a `total_damage` that already contains it. **The
gate's own comparison target is wrong for every pet owner.**

🛑 **`3i` IS THE OPPOSITE KIND OF SESSION TO `3h`. THE GATE IS EXPECTED TO MOVE.** That
makes the discipline stricter, not looser:

> 🛑 **THE INVARIANT FOR THIS SESSION: every commit that moves the gate moves it for ONE
> reason, and that reason is PRE-REGISTERED in a commit that lands BEFORE it.** Report the
> pair on every commit as `3g` and `3h` did. A commit that moves the gate **without a
> pre-registration naming the direction** is a defect in that commit, even if the movement
> is welcome. Two gate-moving changes in one commit is the same defect.

**Opening gate:** `1 of 36 within ±20% · 1 qualified · slice accuracy 20.5% at coverage ≥20%
(n=23)`. Holdout: **0 of 5**, median slice **9.8% (n=4)**, read once at `3g` close-out and
**not to be read again this session**.

**Two gate movements are already known in outline and must land in separate commits:**

| change | known pair | source |
|---|---|---|
| E15 consumer dedupe **alone** | `1 / 1 / 20.5%` → `1 / 1 / **19.8%**` | `3h` C4 green path, run and reverted |
| Apply stamped admissibility rule | `**1** / 1 / …` → `**0** / … ` (`Boomcat` NOT ADMISSIBLE) | `CALIBRATION_TOLERANCE.md` successor #3 |

⚠ **The ingest-layer E15 fix will move the gate by MORE than the consumer dedupe**, because
it also corrects `encounter_performance.dps` and therefore every pet owner's `delta_pct`.
That number is not known in advance. **Pre-register the direction, not the magnitude.**

---

## §1 — The six things this session must produce

| | | why now |
|---|---|---|
| **A** | `PROGRESS.md`'s stale `## Current position` archived, and the `LIVE`-doc sweep | a `LIVE` file has been telling every session to "FIX E13 FIRST" for two sessions after E13 was fixed |
| **B** | **E15 fixed at ingest and at `dps`**, one commit, its own pair | the gate's own logged DPS is wrong for every pet owner |
| **C** | **`per_ability_accuracy.py`'s logged side repaired**, then re-run and re-stated | it sums duplicates in its denominator and drops them from its numerator; the shares in its own artifact do not sum to 100% |
| **D** | The stamped **admissibility rule applied**, and its unimplemented predicates implemented | predicate 4's hardcoded "predates the boundary" stopped being true on 2026-08-08 |
| **E** | The two **tautological check arms** repaired, plus three fail-open holes | `3g` G6's lesson, recurring inside the checks written to guard it |
| **F** | **One** modelling target, taken from the *repaired* distribution — **if and only if** A–E have landed | first gate-moving modelling since `3g`; it is fine for this to spill to `3j` |

---

## Block 0 — 🚨 the phase boundary, before anything else

`season_config.NEXT_PHASE_BOUNDARY` was `2026-08-08T00:00:00Z`. `3g` built three defences
and **nobody has ever seen one fire**. Before any other work, and before any gear tier is
read:

1. Hit `/api/phases` live. Record the raw payload in the session record — active top-level
   phase, and whether anything ships as a **child**.
2. State whether `phase_guard()` fired, whether `phase_label` went **NULL** rather than
   mis-stamping, and whether `horizon is None` failed closed.
3. **If the flip happened:** bump `EXPECTED_PHASE_NAME` and re-derive the corpus **before**
   any gear tier read. Leaderboards and armory are the only data a flip destroys; reports
   persist, so the report backfill has no deadline.
4. **If it did not happen:** say so plainly and re-check the declared boundary's own date.

> 🛑 **STOP-POINT 0.** If the flip happened *and* a gear tier was read before
> `EXPECTED_PHASE_NAME` was bumped, **stop and report**. Do not re-derive over it.

---

## Block A — the documents (no code, no gate move)

Land **first**, in **one commit that touches no `.py`**, because everything later quotes
these.

**A1. 🚨 `primer/PROGRESS.md:527-580`.** Wrap the `## Current position` / `### 🔴 FIRST
ACTIONS NEXT SESSION (3g)` block in `<details><summary>Superseded…` exactly as the `3f`
block at `:582` and the `3e` block at `:606` already are. It currently reads as live truth
and says *"Gate: 5 of 36, slice 64.3%"* and *"🚨 FIX E13 FIRST … every white swing is ~78×
over"*. Both defects were fixed at `3g`.

> 🛑 **This is not tidiness.** `PROGRESS.md`'s own header says *"if you find a claim here
> that the tree contradicts, that is a defect in this file"* — and it has carried three of
> them across two sessions, in the file every session reads first. `3h` Block A existed to
> sweep stale documents and did not look here.

**A2.** `predictions/gate_manifest_3e.json:19` ships
`successor_floor_justification: "slice accuracy is stable at ~62.6% across the
>=20/>=30/>=50 bands"` beside its own bands of **20.45 / 16.86 / 16.86**. The string is
hardcoded at `calibrate_crawled.py:1451`; the same file's `:1160` already says ~62% was
E13's inflated autos. Same shape at `:1504` (`"the >=0 band reads ~164%"` against an
artifact reading **40.25**). **Generate these from the bands or annotate them as
pre-E13 — do not leave hand-typed magnitudes inside a generated artifact.**

**A3. `primer/ENGINE_BUGS.md:3`** claims it is *"ENFORCED in both directions by
`check_sim_engine.py`"*. **Nothing in the tree parses `ENGINE_BUGS.md`** —
`resolve_generality()` (`check_sim_engine.py:248-283`) enforces `EXPECTED_FAILURES` against
runtime check *names* only. Two drifts already exist: `check_sim_engine.py:193` registers a
`"[frost_mage] … well-sampled …"` check whose string appears in **no** document and whose
registry value names no E-number; and `:131` is now owned only by E13 and E14, **both
closed**.

> 🛑 **Owner question A3 (default below).** Either write the ~30-line parser that reads the
> E-numbers and check strings out of `ENGINE_BUGS.md` and asserts the set equality, **or**
> downgrade line 3 to *"enforced one direction; the document side is a human promise."*
> **Default if unreachable: write the parser.** A promise this project has now broken twice
> is worth 30 lines.

**A4.** `primer/ENGINE_BUGS.md:17` — *"Every entry here is a FAILING CHECK"* — is false as
written; `:534` (E8) and `:670-698` (eight more) self-disclose the exemption. Amend the
invariant to state the exemption, and make the parser in A3 honour it.

**A5.** The remaining stale-prose sweep, all one-liners:
`calibrate_crawled.py:692` and `tools/scrapers/scrape_ascension_db.py:12` still say the sim
*"produces damage for"* X% (B1 retired that phrasing everywhere else);
`ingest/export/seed_epistemics.py:252` still carries the retracted **305 casts** figure that
`ENGINE_BUGS.md:559-566` corrects to **4**; `primer/PLAN_3G_self_verifying_gates.md:32-34`
names the `within_tolerance` coverage floor as missing when `3g` G4 applied it;
`predictions/CALIBRATION_TOLERANCE.md:197-198, 203` still frame the coverage split as an
open `3h` question, and `:238` carries pre-E13 band numbers contradicting the corrected
table 55 lines above — **annotate, do not rewrite stamped text.**
`primer/PROGRESS.md:73` quotes holdout median slice `9.8%` beside "0 of 5"; the source says
**9.8% (n=4)**. Restore the `n`.

**A6.** Supersede `primer/CHAT_MONITORING_PRIMER.md` with **v4** (drafted in the oversight
chat, delivered with this order) and reclassify `primer/SESSION_3H_PRIMER.md` as
`SUPERSEDED BY primer/Session_2026-08-07_3h_measurement.md` if it is not already.

---

## Block B — E15, at the layer where it lives 🚨

**One commit. Its own gate pair. Pre-register before it.**

**B1 (pre-registration, committed first).** State: the direction of the gate move; whether
`within ±20%` count is expected to change; and which characters are expected to move most
(the pet owners named in `ENGINE_BUGS.md`: Malo, Ikkura, Onur, plus any others the
discriminator finds). **The consumer-dedupe-only pair is already known — `1 / 1 / 19.8%` —
so predict the ingest-layer pair *relative to that*, and say why it differs.**

**B2. Fix at ingest.** `core/builds/corpus.py:425-434` ingests `pet_spell_damage_by_owner`
as `is_pet=1` rows under the owner's `character_id`, while `rows[]` — already owner-**merged**
per `3h` D2's re-fetch of report 79 — is ingested as `is_pet=0`. The pet block is a
**restatement, not an addition**. Decide and state which copy is canonical.

⚠ Two traps `3h` already found and one it left open:
* the payload's `spell_id` is a **STRING** — compare with `str()` or `_int_or_none`;
* `ability_performance`'s primary key **includes `is_pet`** (`corpus.py:156`), so the two
  copies coexist by design of the schema — a fix that only dedupes on read leaves the schema
  lying;
* 🛑 **the 1,208 groups where `owner < pet` are NOT explained by the restatement** and need
  their own look. Partial windows and scope drift are the candidates. **If they resist
  explanation, register them rather than picking a rule.**

**B3. Fix `dps`.** `corpus.py:594-614` computes `dps = (total_damage + pet_damage) / dur`
where `total_damage` sums `is_pet=0` rows — which already contain the pet damage. Fix in the
same commit; it is the same defect one layer up, and it moves `delta_pct`, not just coverage.

**B4.** The registered check leaves `EXPECTED_FAILURES`; `ENGINE_BUGS.md` E15 gets its
`— ✅ FIXED (3i B)` heading and a closure box in the shape E1/E2/E4/E6/E13/E14 use, with the
**measured** before/after pair in it.

---

## Block C — repair the instrument before trusting its numbers 🚨

**No gate move — `per_ability_accuracy.py` writes no manifest. Commit separately anyway.**

The audit traced this from the schema up and it is a defect in the tool, not only inherited
from E15. Inside `rows_for_character`, the same duplicated rows are handled four ways:

| line | code | effect |
|---|---|---|
| `:154` | `total_logged = sum(r[2] for r in logged)` | **both copies counted** |
| `:204` | `logged_by_sid[r[0]] = r` | dict — **last row wins, the other silently dropped** |
| `:200` | `auto_logged += r[2]` | **both copies accumulated** |
| `:202` | `other_negative.append(r)` | **both kept as separate rows** |

**C1.** Make the numerator and the denominator agree: one policy for a duplicated
`(spell_id, spell_name)` pair, applied at all four sites.

**C2.** **Assert it.** The per-row `coverage_share_of_logged` values must sum to `100 ± ε`
per character. Today they do not, for any character with a duplicated ability, and nothing
notices. Register the assertion with a red mutation.

**C3.** 🆕 **Remove the nondeterminism.** `logged_by_sid[r[0]] = r` has **no `ORDER BY`**, so
for the 5,234 groups whose copies *differ*, the tool keeps whichever row SQLite returned
last. **Two runs against the same database can produce different per-ability ratios.** After
B, most of these collapse — the ones that do not must refuse or be named, not silently
picked.

**C4. Report the missing cell.** `:207-212` emits every sim key that the log has no row for
(`logged_damage = 0.0`); `:287` then filters them out and **no statistic covers them**. Sim
damage landing on abilities the character never used **inflates the aggregate delta while
earning zero coverage credit** — the exact class of thing Block C was built to expose. The
rows are already in the JSON; add a count and a share-of-sim-damage line.

**C5. Report the paired median.** `30.7% (n=20)` and `20.5% (n=23)` are medians over
**different populations** — selected on `modelled_and_producing_pct ≥ 20` and
`modelled_damage_pct ≥ 20` respectively (`calibrate_crawled.py:988-995` vs `:906-917`). The
three dropped members are by construction the ones with the most keyed-but-zero mass, so the
producing-only figure is **upward-biased by selection**, and `3h` P5's reconciliation with
F9's 33.1% inherits that. Print the **paired** median over the same members, both metrics.

**C6. Re-run and re-state.** After B and C1–C5: re-run the tool and re-state `0.253 / 11% /
25% / 62.2%` in `PROGRESS.md` and the session record.

> 🔬 **Pre-register this before running it.** The audit's expectation, stated so it can be
> falsified: **the absent share moves UP, not down.** If the duplicated mass is mostly
> positive-id unmatched pet spells — which is what `ENGINE_BUGS.md:923-931` concluded — the
> duplicate was leaving the numerator (collapsed by the dict) and staying in the denominator
> (summed), so `62.2%` was **understated**. The producing-ratio median should move
> **little**, because positive-id ratios were already computed against a single copy; the
> visible exception is the auto row. **If the absent share moves DOWN, the audit's model of
> the defect is wrong — say so and register it.**

**C7. Commit a small summary artifact** — the distribution's summary statistics and the
per-character coverage split, **not** 651 rows — into `predictions/`. `3h`'s headline result
lives only in gitignored `data/derived/` and is the single number a monitoring chat cannot
check. `3h` A7 made the gate manifest self-identifying; do the same for the number that
replaced it as the interesting one.

---

## Block D — apply the stamped rule, and implement the half of it that is prose

**One commit. Its own gate pair. Expected `within ±20%`: 1 → 0**, with `Boomcat` **NOT
ADMISSIBLE** rather than failed. Pre-register the pair before applying.

**D1. Implement predicate 4.** `parse_admissibility.py:198-199` prints *"every corpus
capture predates the 2026-08-08 boundary, so this removes nobody today."* That sentence
became false at the boundary and it is a string, not a test. The seam is three lines:
`core.builds.phases.resolve_phase(captured_at, …)`, already used at `core/builds/gear.py:121-125`.

**D2. Implement predicate 5** rather than asserting it. `lag` is already collected into the
table (`:229`) and never tested. `CLAUDE.md`: *a guard that cannot run must say so — never
report a condition you failed to test.*

**D3. Make the regime legible.** `resolved_entries` is computed (`:102`) and stored (`:231`)
and **never printed** (`:239-246`), so *"regime valid, 0 cast-time entries"* is
indistinguishable from *"nothing resolved."* Print `resolved_entries`, the comparator
median, and the per-scope APM list beside every ratio. Without them the stamped evidence
line cannot be checked by anyone.

**D4. Close the fail-open paths, or state them.** Every refusal currently lands on
*admissible*: out-of-regime kits (**22 of 41 boards** — predicate 1 is structurally incapable
of removing a cast-time caster), `< 2` other scopes (`:168-171`, **an escape hatch not in the
stamped text**), NULL `SUM(casts)`, missing scope duration. The regime test itself fails open
four ways (`:76-78, :84-85, :88-89, :93-94`): anything unresolved is counted as *instant*.
**Report `5 of 41` as a lower bound**, not the rule's reach.

**D5. Tighten the comparator.** `:162-166` takes **every** distinct scope with an
`ability_performance` row — no `is_trash = 0`, no `duration_seconds >= 20`, no level or
snapshot filter, no exclusion of grouped scopes that may *contain* the scope under test, and
no re-check that the comparator scopes are themselves in the instant-heavy regime. The
walrus at `:166` also silently drops any comparator scope whose APM is exactly `0.0` — which
is the death-deflation signature the predicate exists to detect.

**D6. Add the stamp↔code assertion.** `3h` A3 built exactly this for the manifest
(`criteria_in_force` must equal what produced `result`) and did not build it here. Assert
`APM_RATIO_BOUND`, `MAX_CAST_TIME_ENTRIES` and `MIN_PARSE_SECONDS` equal the thresholds
stamped in `CALIBRATION_TOLERANCE.md` successor #3. Register a red mutation.

**D7. Record the correction to `3h`'s P9.** The prereg registered *"the death-deflation
predicate (an APM ratio ≤ 0.5 within the valid regime, or deaths > 0)"*; the record reports
*"removes 3"*, but `Nodding` was removed by the **52 s window** predicate. On the registered
predicate the count is **2**. The bar (≥1) was met and the stop-rule did not trigger — the
number needs correcting, not the decision.

**D8.** `MIN_PARSE_SECONDS = 60` arrived in the same commit as its own result. State its
provenance or stamp it.

---

## Block E — the checks that cannot go red

**One commit, no gate move.**

**E1.** `check_refusals.py:821` — the *"split sums to `modelled_damage_pct`"* arm is
tautological: `keyed_zero = modelled - producing` by construction
(`calibrate_crawled.py:496`). Verified: under the docstring's own registered mutation
(`is_producing → return True`), **1 of 4 cases went red** and the sum case printed
`60.0 + 0.0 vs 60.0` **PASS**. Either give it a red path or delete it and correct the
docstring's claim about its mutation.

**E2.** `check_refusals.py:836` — the *"SAME key flips to producing"* case asserts
`60.0 / 0.0`, which is **identically what the excluded defect produces**. Rewrite so the two
states differ.

**E3.** `calibrate_crawled.py:505-518` — `logged_by_sid` is keyed by **integer** `spell_id`,
but `per_ability` also carries the **string** keys `auto_mh` / `auto_oh`, which reach the
keyed-zero *mass* through the negative-id path (`:490`). A zero-producing auto contributes to
`keyed_but_zero_pct`, reports `logged_share_pct: 0.0`, and sorts **last** (`:517`) — so the
renderer prints *"70% keyed-but-zero"* and then names 0.0% of it.

**E4.** `check_refusals.py:750` — the new `predictions/` census **fails open on an empty or
missing directory** (verified: renaming `predictions/` yields `0 files … PASS`). Add
`len(files) > 0`. `primer/`'s equivalent is protected indirectly by the `CLAUDE.md` paste
comparison; `predictions/` has no anchor.

**E5.** `check_refusals.py:701` — `_status_census` classifies on any **backticked status
word** in the first 1200 characters, not on a status *line*. Match the line, not the word.

**E6.** `calibrate_crawled.py:1429` — `--allow-dirty` records a boolean **nothing reads**.
Either assert `git_working_tree_dirty == false` on any committed manifest, or take a
`--allow-dirty-reason` string and record it. `AUDIT_3G` asked for the reason; a bool is not
one. `predictions/gate_manifest.json` still ships `git_working_tree_dirty: true` unflagged.

---

## Block F — modelling, only if A–E have landed

> 🛑 **STOP-POINT F.** If A–E consumed the session, **stop and hand F to `3j`.** That is a
> good outcome, not a failure: `3e` picked its targets from an aggregate and had its
> inference retracted, and the whole point of C is that the current target list is not yet
> trustworthy. **Do not start F on the pre-repair distribution.**

If there is budget: **one** target, one commit, one pre-registered pair. The visible levers
as of `3h`, **to be re-confirmed against the repaired distribution first**:

* **Elemental Blast** — ratio 0.02–0.19 across three characters carrying **56–69%** of their
  logged damage each, and absent on a fourth at 63.9%. The largest single lever visible.
* **The starved-allocation mass** — all 90 keyed-but-zero entries are `zero-casts-allocated`
  (the E6/E7 GCD family), **10.9% of logged damage**. A rotation problem, not a resolution one.
* **The absent-key majority** — 62.2% before C's repair, and expected to be **larger** after.

**E9, E11 and E12 keep their run green paths and remain ready** — one commit and one gate
pair each, whenever a session takes them.

---

## §2 — Questions, with the default if I am not reachable

| | question | default |
|---|---|---|
| **Q1** | A3: write the `ENGINE_BUGS.md` parser, or downgrade the "both directions" claim? | **Write the parser.** |
| **Q2** | B2: which copy of a duplicated row is canonical — the owner-merged `rows[]` entry or the per-pet restatement? | **Keep the owner-merged `rows[]` copy**, drop the restatement, and record `is_pet` provenance separately. State it as a decision, not a discovery. |
| **Q3** | B: should the schema change (drop `is_pet` from the primary key) or only the ingest? | **Ingest only this session.** A schema change is its own commit with its own rebuild, and mixing it with a gate move breaks the one-reason rule. |
| **Q4** | D: apply the admissibility rule in this session at all, given it takes the gate to **0 of 36**? | **Yes, apply it.** It was stamped with its falsifiability check passed and its effect known in outline; deferring it because the number gets worse is exactly the fitting behaviour the stamp-first discipline exists to prevent. |
| **Q5** | C7: which summary statistics go in the committed artifact? | **The printed summary block, verbatim** — histogram counts, producing n/median/quartiles/in-band, zero count, absent share, per-character coverage split. Not the 651 rows. |

---

## §3 — Exit conditions

1. Block 0's phase-boundary check run **live** and its raw payload recorded, before any gear
   tier read.
2. `PROGRESS.md:527-580` archived; `grep -n "FIX E13 FIRST" primer/` returns nothing outside
   a collapsed `<details>` or a `HISTORICAL` document.
3. E15 fixed at **ingest** and at **`dps`**, in one commit, with its pre-registered pair
   reported and its `ENGINE_BUGS.md` closure box carrying the measured numbers.
4. `per_ability_accuracy.py` repaired: shares sum to 100 ± ε **and that is asserted**; no
   nondeterministic row drop; the phantom-production cell reported; the paired median printed.
5. The distribution **re-run and re-stated** in `PROGRESS.md`, with C6's pre-registration
   outcome recorded — including if the absent share moved the *other* way.
6. A summary artifact committed under `predictions/`, so `3i`'s headline is checkable from
   the tree.
7. The admissibility rule **applied**, with predicates 4 and 5 computed rather than printed,
   `resolved_entries` printed, and the stamp↔constants assertion registered.
8. E1–E6 landed; `check_refusals.py`'s registered mutations verified to actually turn their
   arms red.
9. The gate pair reported at **every** commit, and every gate-moving commit preceded by its
   own pre-registration.
10. The holdout **not read**. `3g` read it once at close-out; nothing this session earns
    another read.

---

## §4 — The one thing to carry into this session

**`3h` proved the aggregates were cancelling. `3i`'s job is to stop the log side from
cancelling too.**

Every number this project has retracted was derived from two other numbers. The `3h` audit
found the newest one derived from a table where the same rows are counted once in one place
and twice in another — and the tool that found the defect is itself a consumer of it. So:

> 🛑 **Fix the measurement before you trust what it points at.** Blocks B and C are not
> housekeeping ahead of the real work; they are the reason the real work would otherwise be
> aimed at a number nobody can currently sign.
