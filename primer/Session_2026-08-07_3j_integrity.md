# Session `3j` — gate integrity: the machinery, not the number

> **`HISTORICAL`** — the record of session `3j`, run 2026-08-07. **It describes what
> that session did and may contain claims that are false today, which is correct for a
> record.** Work order it ran: `primer/SESSION_3J_PRIMER.md` (now `SUPERSEDED BY` this
> file). Audit it implemented: `primer/AUDIT_3I_ADVERSARIAL.md`.

**One line:** an integrity session that repaired the machinery producing the gate number
and did not move it — `0 / 0 / 26.3% (n=23)` at every one of ten commits — closing the
fail-open, the phase-outage passthrough, three checks that could not fail, and the
document half that had been the weaker half for three sessions.

---

## §0 — Commit-by-commit, with the gate at each

| # | commit | what | gate |
|---|---|---|---|
| 1 | `45883c0` | pre-flight: the work order's own status line + the census it staled | `0 / 0 / 26.3%` |
| 2 | `5f97deb` | **Block 0** — a phase outage refuses to publish | `0 / 0 / 26.3%` |
| 3 | `941b8b0` | **A1** — the gate fails CLOSED on stamp drift | `0 / 0 / 26.3%` |
| 4 | `a6e0fa2` | **A2 prereg** — registered BEFORE the runs (no measurement) | `0 / 0 / 26.3%` |
| 5 | `77d7e17` | **A2+A3** — P1–P4 confirmed, stamp amended, assertion anchored | `0 / 0 / 26.3%` |
| 6 | `2e1dcac` | **A4+A5** — E3 gets a check, its regression undone, E2 can fail | `0 / 0 / 26.3%` |
| 7 | `bbc886e` | **A6** — doc-sync verdict reaches the exit code on a clean clone | untouched |
| 8 | `cb23924` | **Block B** — the E15 aftermath | `0 / 0 / 26.3%` |
| 9 | `9353f6f` | **Block C** — the document half | `0 / 0 / 26.3%` |
| 10 | `328e719` | the manifest, regenerated from a clean tree | `0 / 0 / 26.3%` |

🛑 **The invariant held at every commit.** Full reading, unchanged from `18c2333`:
`0 of 36 within ±20% · 0 qualified · slice accuracy 26.3% at coverage ≥20% (n=23)`,
3 NOT ADMISSIBLE (Nodding, Boomcat, Deyindra). **No modelling block was opened** — that
is `3k`'s, per the work order.

---

## §1 — Block 0: the flip, and the outage that was going to publish a number

**Live check first, read-only, before any corpus change.** `GET /api/phases` with the
crawler's `HEADERS`, 2026-08-07T12:04Z: HTTP 200, 3 phases, single active top-level
`Phase 1 - Zul'Gurub`, `assert_phase` passes.

🛑 **THE FLIP HAD NOT HAPPENED.** The boundary arms `2026-08-08T00:00:00Z`; the session
ran ~12 h before it. The work order's *"the daily crawler has likely already run against
the post-flip server"* was drafted for the 8th and the session opened on the 7th.
`data/source/crawl/2026-08-07/` carries no `phases.jsonl.gz` at all, so no poison payload
was on disk. Expected shape (b): **STOP-POINT 0 did not trigger**, `EXPECTED_PHASE_NAME`
was **not** bumped, the corpus was **not** re-derived.

**The fix landed anyway, because the chain fires tonight with zero code changes.**
`phase_guard`'s `refuse_reason` is a verdict on the *payload*; it was passed into
`resolve_phase`, which checks it first — so one infrastructure fault returned NULL for
every capture, flagged all 41 members *"unresolved phase"*, and the gate would have
published **`0 of 36`** as a measurement. `CLAUDE.md`'s own rule forbids it: a character
is excluded for what its **parse** is, and a payload refusal is nobody's parse.

* `admissibility_for` no longer passes `refuse_reason` down; it reports
  `phase_payload_refusal` and **suppresses predicate 4** while it is set.
* New `assert_publishable()` + `AdmissibilityOutage`, called before the sim loop (an
  outage costs seconds, not a cohort sim) and again after it.
* Cohort-level half: refuse if every member shares a flag string, and refuse if every
  member is flagged at all.

**The guard is not a refuse-always stub** — one arm feeds it the *actual* `3i` roster
(3 of 36 flagged, each for a different reason) and asserts it **publishes**. A maximally
refusing implementation passes three arms and fails that one.

---

## §2 — Block A: the gate integrity

**A1 — the fail-open.** `assert_stamped_thresholds()` failing set `pa = None` and
*continued*, then the manifest asserted `parse_admissibility_rule_applied: True` from a
hardcoded literal. It now raises; the two dead `if pa is not None` branches are gone; the
claim is derived and cross-checked against a new per-row `admissibility_computed`.

**A2 — the comparator.** Pre-registered in `predictions/prereg_3j_comparator.md`
(`a6e0fa2`), committed before the runs it predicts. All four confirmed:

| | prediction | result |
|---|---|---|
| P1 | filters removed ⇒ roster ⊇ the current 3, re-admitting Robottikyrpa and Frediib | ✅ **5 of 41**; Robottikyrpa 0.24, Frediib 0.14 |
| P2 | the roster change does not move the gate | ✅ `0 / 0 / 26.3% (n=23)` either way |
| P3 | the audit's *"no arm can add a flag"* is FALSE of the median | ✅ **0.762 admissible unfiltered → 0.421 flagged filtered** |
| P4 | the 0.0-comparator rationale is inverted | ✅ arithmetic; corrected in place |

The document says plainly what it is **not**: the D5 effect was already known, and no
ceremony unknows it. What it registers are the three questions `3i` never asked.

**Owner decision 2026-08-07: stamp follows code.** Predicate 1 amended to name the three
filters, appended in the `3i` D7 correction style. The counterfactual was *measured
first*, so the amendment is not a free choice made in the dark — and it scores **worse**
on the narrow `3h` P9 falsifiability bar (0 failing removed, vs 2 without the filters),
which is the direction that rules out fitting.

**A3 — the anchor.** The assertion regex-matched three numbers anywhere in the file;
`AUDIT_3I` §5 demonstrated the false green (delete the whole stamped block, the regex
finds D7's *quotation* 36 lines below, PASS). It now cuts the successor-#3 section out by
its heading and checks 5 numbers + 4 prose fragments + the comparison direction.

🛑 **The direction arm was first written as a tautology** — `APM_RATIO_BOUND <=
APM_RATIO_BOUND`, true of `<=`, `>=` and `==` alike and green under the very mutation it
named. Caught before commit; the comparison is now extracted into `flags_on_ratio()` and
the arm exercises it at the bound and just above.

**A4/A5 — the checks that could not fail.** E3's repair had *no check* (the full revert
left the suite at 0 FAILURES), and E3 had also **regressed** the list it repaired.
E2's correct answer *was* the maximal-producing answer. Both fixed, both two-sided.

**A6 — the exit code.** `check_sim_engine.py`'s doc-sync verdict could not reach the exit
code on a clean clone, the environment it was written for. **Verified in the actual
condition** — a fresh `git clone` to a temp dir with no `data/derived/`: baseline exit 2,
with M31 applied exit **1**.

---

## §3 — Block B: the E15 aftermath

**B3 measured before fixing**, per the work order, because the count decides whether it is
a fix or a finding: **0 of 291,320** NULL-`spell_id` rows in `ability_performance`, **0 of
22,427** in `pet_ability_damage`. Latent route, not live inflation ⇒ closing it **cannot
move the gate**. `UNRESOLVED_SPELL_ID` (−999999) replaces the NULL — outside both
Spell.dbc space and the log's auto ids, and countable where NULL was not.

**B1** — `PRAGMA user_version`, `assert_schema_current` (refuse) and `migrate_schema`
(repair). The three consumers `AUDIT_3I` §7.1 named gained both the guard and an
`is_pet = 0` filter.

🛑 **This session's own corpus was v0 and the new check caught it.** Repaired by
**migration, not rebuild** — deliberately: a rebuild re-reads `data/source/crawl/` and
could legitimately pick up the 2026-08-07 crawl day, which is a corpus move an integrity
session must not make. The migration **touched no data** (291,320 rows and
2,818,810,395.0 damage before and after), so it is provably gate-neutral.

**B2** — three arms that read the *real* `builds.db`, skipped with a printed reason on a
clean clone; `build_builds_db.py` prints `pet_ability_damage` + `user_version` and returns
1 on any `is_pet=1` row.

**B4 — a conclusion that survives its own mechanism.** Four sites read
`dps = (total_damage + pet_damage)/duration`, which `3i` B3 fixed. **E3 is not closed by
this**: the endpoint merges pets into `rows[]`, so `total_damage` still contains pet
damage — once now, twice before. The stale formula would have been an easy excuse to close
a live gap; primer v25's rule is why it did not.

**B5** — 695 owner ids appear in `pet_ability_damage` with no owner row anywhere, and
**0 of those 695 are in `characters`** (every one a non-player owner). **0 of the 41
cohort members affected.** `pet_damage` NULL-vs-0 semantics stated in the DDL: NULL means
"no pet rows for this (scope, character)", 0 never occurs — 12,062 / 0 / 7,245 measured.

---

## §4 — Block C: the document half

`CLAUDE.md:199` corrected. **Phase 3 exit condition 10's ✅ corrected to 🟡** (owner
decision: the checkmark is a `3j`-class defect independent of scheduling).
`CHAT_MONITORING_PRIMER.md` was **already v5 in place** — landed by the work-order commit,
versionless, no `_v5` sibling — so C2 was satisfied before the session began.

**The band table is now generated and asserted**, because the warning failed twice: `3f`'s
table survived `3g` (which regenerated the manifest five times), and `3i` moved the gate
**twice** without touching it, one session after `3h` wrote the warning.
`tools/audit/render_band_table.py` + a `check_refusals` arm, the same treatment `3h` A4
gave `CLAUDE.md`'s census.

**M32–M49 landed**, and `check_engine_bugs_doc_sync` now **parses the mutation table** —
the drift class it was built for, in the half it did not read. Its contiguity arm found a
real gap on its first run (`MISSING [11]`) against a table that has `M11a`/`M11b`: a real
split-row convention the regex did not know. **The check was fixed, not the document.**

The `predictions/` status rule reaches `*.json`. The holdout is annotated **pre-E15 with
the direction stated** (owner rider): 9.8% *under*-states it, so it must not be read as a
current floor. `per_ability_summary.json` refuses to write under a filter and its
dirty-tree refusal raises — after the derived artifacts are written, because its own
message says they are.

---

## §5 — Mutations run this session

Every one **run**, not merely named. M34–M49 in `primer/ENGINE_BUGS.md`.

| mutation | red arms |
|---|---|
| restore the `refuse_reason` passthrough (M46) | 1 |
| disable all three `assert_publishable` raises (M45) | 3 |
| M33 `APM_RATIO_BOUND = 0.4`, against the **gate** | gate refuses, no manifest written |
| disable the `parse_admissibility_rule_applied` assertion (M44) | 1 |
| M34 delete the stamped successor-#3 section | all `[D6]`, and the gate refuses |
| M35 revert predicate 1's wording | 1 |
| M36 `flags_on_ratio` `<=` → `<` | 1 |
| M37 E3's repair → `if False:` (the full revert) | 3 |
| M38 restore `3i`'s `and auto_rows_logged` guard | 1 |
| M39 re-inline the duplicate auto predicate | 1 |
| M40 `is_producing → return True` | 5 |
| M41 `autos_producing = False` | 2 |
| M42 delete `assert_schema_current`'s raise | v0 DB accepted |
| M43 `_spell_key → _int_or_none` | 3 rows / 3000 damage |
| M47 remove the `MIN_PARSE_SECONDS` comparator filter | 2 |
| M48 change one digit of the band table | 1 |
| M49 delete a `status` key from `predictions/*.json` | 1 |
| M31 on a clean clone (A6) | exit 2 → **1** |
| delete an M row / cite an unregistered M99 (C4) | 1 each |

🛑 **A NAMED MUTATION THAT DID NOT GO RED, kept rather than swapped.** The mutation first
registered for the A1 arm was *"restore the hardcoded literal `True`"*. It was **run** and
both arms stayed PASS — the assertion re-derives the fact from the rows, so it catches a
literal as readily as a wrong parameter. **The assertion is the fix, not the parameter.**
The comment now says so and names the mutation that does go red (M44). `3g` G5 says a
named green path is a guess about your own code; a named red path is too.

---

## §6 — What was NOT done

An honest short list beats a padded ✅ column.

1. **`gear_tier_stats(phase=…)` still has no production caller.** Exit condition 10's ✅
   is corrected to 🟡 and the *deliverable* is scheduled into `3k` (owner decision), not
   done here.
2. **`ContentProfile` presets are still 6 of 8 self-declaring** (`core/sim/content.py`).
   Scheduled into `3k` as measurement work — see §7.
3. **The holdout was not re-read.** Annotated instead (owner decision); it stays unspent.
4. **`CHAT_MONITORING_PRIMER.md` is v5 and its own expiry says supersede at v6 when `3j`
   closes.** A `3j` addendum is appended rather than a full v6 rewrite: the gate did not
   move, so v5's substance is intact. **A `3k` reader should still treat a v6 rewrite as
   due.**
5. **`gate_manifest.json`'s missing dirty-tree reason** (`AUDIT_3I` §8's closing note) is
   untouched — it is the **frozen `3d`** artifact, and rewriting it would alter a record
   rather than fix a live claim. No assertion of the form *"a committed manifest with
   `git_working_tree_dirty: true` must carry a reason"* was added.
6. **The 1,208 owner < pet groups** registered by `3i` remain unexplained.
7. **No modelling.** Block F/D-type work is `3k`'s, per the work order's own instruction
   to stop early rather than open it.

---

## §7 — What `3j` hands to `3k`

A gate whose number can be trusted: fail-closed on stamp drift, phase-outage-proof, with
every repaired check owning a **run** RED mutation, and a corpus that refuses to be read
at the wrong schema version.

**`3k` is a modelling session, and per the repaired distribution it is a COVERAGE session
first** (63.9% of logged damage has no sim key, so the slice is capped near ~36% until
keys exist), ratio tuning second (producing median 0.273). **Pre-register which of the two
it is doing before touching `core/`.** The gate has **zero** passers — expect to *build* a
pass, not defend one, and pre-register what a pass looks like before running.

**Two named deliverables, scheduled by owner decision 2026-08-07:**

1. **`gear_tier_stats(phase=…)` production caller** (Phase 3 exit condition 10).
2. **`ContentProfile` presets — replace assumption durations/params with
   corpus-measured values** for the content types the gate's scopes actually use. The
   corpus holds thousands of real encounter durations, so **this is measurement work, not
   re-verification of guesses.** ⚠ Presets feed the gate's *sim* side, so criterion 7 is
   **load-bearing, not speculative**.
