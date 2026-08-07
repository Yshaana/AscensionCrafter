# SESSION `3J` PRIMER — gate integrity, then the E15 aftermath. No modelling.

> **`WORK ORDER`** — the brief for session `3j`, drafted 2026-08-08 from
> `primer/AUDIT_3I_ADVERSARIAL.md` (§10 is the source list; this file orders and
> scopes it). Becomes `SUPERSEDED BY` the `3j` session record when `3j` closes.

**Audit implemented:** `primer/AUDIT_3I_ADVERSARIAL.md`.
**Previous session record:** `primer/Session_2026-08-07_3i_gate_repair.md`.

---

## §0 — The invariant, unchanged

🛑 **The gate is expected to read `0 / 0 / 26.3% (n=23)` at EVERY commit of this
session.** `3j` is an integrity session: it repairs the machinery that produces the
number, it does not move the number. If any change moves the gate, that is a
**finding** — stop, pre-register nothing retroactively, report the pair, and put the
cause in the session record before continuing. The only sanctioned exception is
Block 0 (a phase flip forces an `EXPECTED_PHASE_NAME` bump + corpus re-derivation,
which may legitimately change `n`; if so, commit the before/after pair with the flip
evidence as its reason).

**Do not open a modelling block.** The modelling work (`3i`'s handed-over Block F) is
`3k`'s, on a gate this session makes trustworthy. If `3j` finishes early, stop early.

**Every commit that changes a check must include the mutation that turns the check
RED, run and cited.** The `3i` audit found one repaired arm (E3) whose full revert
leaves the suite green — that class is what this session exists to end.

---

## Block 0 — the phase flip (FIRST, read-only, before any crawl output is trusted)

The boundary armed `2026-08-08T00:00:00Z`. The daily crawler has likely already run
against the post-flip server.

1. Check `/api/phases` live (crawler `HEADERS`; the bare request 403s). Record the
   payload verbatim in the session record.
2. **If the flip happened:** bump `EXPECTED_PHASE_NAME`, re-derive the corpus, and
   verify `phase_label` went NULL (not mis-stamped) for any post-boundary capture
   **before any gear tier is read**. Leaderboards/armory are the only data a flip
   destroys; reports persist.
3. **Either way, fix the passthrough** (`AUDIT_3I` §2): in
   `parse_admissibility.admissibility_for`, a **payload-level** `refuse_reason` must
   not become a per-member "unresolved phase" flag. Payload refusal is an
   infrastructure outage → the gate must **refuse to publish a number**, loudly, not
   publish `0 of 36`. Add the guard: if every cohort member carries an identical
   admissibility flag, refuse.
4. Mutation: feed a synthetic refused payload; assert the gate run raises/refuses
   rather than emitting a manifest. Register it.

🛑 STOP-POINT 0: if the flip produced anything other than the two expected shapes
(clean flip caught by the defences, or no flip), stop and ask the owner before
touching the corpus.

---

## Block A — gate integrity

**A1 — close the fail-open** (`calibrate_crawled.py:830-837`, `:1581`).
`assert_stamped_thresholds()` failing must **raise**, not `pa = None` + continue.
`parse_admissibility_rule_applied` must reflect reality, not a literal. Extend the
`3h` A3 manifest assertion to cover this key. Mutation: break a stamped constant,
assert the gate refuses to write a manifest.

**A2 — re-derive the D5 comparator change as a real pre-registration.** The change is
already in; the prereg slot is empty. Write the predicate and the predicted roster
*from the stamped rule text*, commit it, then re-run and compare. If the committed
behaviour and the stamped text disagree (they do — the stamp says "other scopes",
the code says a filtered subset), **update the stamp with an owner decision or
revert the filter** — one or the other, in this session.
Also: add a fixture in which a comparator-set change moves a character **into** a
flag. The current one-way structure (every D5 arm can only remove flags) is untested
in the direction that matters. And correct or plainly re-state the inverted
0.0-comparator rationale (`parse_admissibility.py:257-260`): admitting a 0.0
comparator *raises* the tested ratio and *hides* deflation.

**A3 — anchor `assert_stamped_thresholds()` to the stamped section.** Parse the
successor-#3 block, not the whole file (the demonstrated false-green: deleting the
stamped block leaves it matching D7's quotation 36 lines down). Extend it to the
comparator definition and the comparison direction — the two things D5 changed under
an unchanged stamp.

**A4 — E3: check, restoration, dedup.** (a) Add auto rows to the E1 fixture so the
`if False:` revert goes RED. (b) Stop dropping zero-producing auto keys whose log
carried no auto row — the named zero list must be full, per its own comment.
(c) `is_modelled` and `is_auto_row` are two byte-identical inline copies of one
predicate with a comment claiming they're the same object — unify or assert
agreement.

**A5 — E2: widen the fixture** so the maximal-producing answer is not the correct
answer (add a row an over-permissive `is_producing` would misclassify), or retire the
arm and let E1 carry it. Either is fine; a green arm that cannot go red under its
named defect is not.

**A6 — doc-sync exit code on a clean clone.** `check_sim_engine.py` must consult
`FAILURES` before the `return 2` on missing db — the clean-clone environment is the
one the check was written for, and today its verdict cannot reach the exit code
there.

---

## Block B — the E15 aftermath

**B1 — migrate or refuse.** Set `PRAGMA user_version`. On an old-version DB: either
backfill (`DELETE FROM ability_performance WHERE is_pet=1`; repopulate
`pet_ability_damage`) or refuse to read it. No third path. Add `is_pet`-awareness or
an assertion to the three unguarded consumers (`compute_damage_share`,
`demand_list`, `build_extract_scope_request`).

**B2 — a real E15 check.** Against the *actual* corpus: assert zero `is_pet=1` rows
and `pet_ability_damage` non-empty (when the corpus has pet-owners); add the side
table to `build_builds_db.py`'s census printout. The current fixture-only check is
green regardless of what ingest does.

**B3 — the NULL-`spell_id` PK escape.** `_int_or_none(spell_id) → None` rows bypass
`INSERT OR REPLACE` dedupe in both tables; 5 report ids are known to re-ingest.
Reject the row loudly or coalesce to a sentinel — and count occurrences in the real
corpus first (it may already be inflating `total_damage`; if it is, that is a
pre-registered gate move for `3k`, not for this session).

**B4 — stale-formula strings** (4 sites, one user-facing, one seeded into the
epistemics DB): `core/sim/pets.py:103-104`, `ingest/export/seed_epistemics.py:244`,
`check_sim_engine.py:1410-1412`, `ENGINE_BUGS.md:367`.

**B5 — pet-only characters.** Document the cohort-composition change; query whether
any pre-`3i` cohort member was wholly pet-only. Also decide `pet_damage`'s NULL-vs-0
semantics and state it in the DDL comment.

---

## Block C — documents (fixed budget: one block, not a session; third session running)

**C1 —** `CLAUDE.md:199`: "NOT applied" → applied, `3i` D, with the pair.
**C2 —** `primer/CHAT_MONITORING_PRIMER.md` → **v5, in place.** The file is
versionless; the version lives in the title line only. Overwrite its content with the
v5 draft (delivered alongside this work order). **Do not create a `_v5` sibling** —
a versioned copy beside the live file is how v2–v4 each stayed marked `LIVE` after
expiring.
**C3 —** Regenerate `CALIBRATION_TOLERANCE.md`'s band table **from the manifest, in
one commit**, and re-derive the `3i` A5 annotations (30.7%/n=20 → the manifest's
37.65/n=19). Fix the `:302` heading ("NOT applied"). Consider making the band table
generated-and-asserted like the census paste, so it cannot silently stale again.
**C4 —** Land **M32/M33** in `ENGINE_BUGS.md`; number the E1–E6 repair mutations;
**extend `check_engine_bugs_doc_sync` to parse the mutation table** — the drift it
just missed is the class it was built for.
**C5 —** Extend the A5 status-line check to `predictions/*.json`; give
`gate_manifest_3e.json` a `status` key (rename optional, label mandatory).
**C6 —** Annotate the holdout carry-forward as **pre-E15** in the manifest note and
`PROGRESS.md`'s table (or re-read it — owner's call; re-reading spends the holdout,
so default is annotate).
**C7 —** `per_ability_summary.json`: refuse to write under `--char`/
`--max-lag-hours` (or record the filter in the artifact); add cohort identity; make
the dirty-tree refusal raise.
**C8 —** Collapse the two uncollapsed `FIRST ACTIONS NEXT SESSION` headings
(`PROGRESS.md:865`, `:913`); tag `:865`.

---

## Standing decisions needed from the owner (ask, don't guess)

1. **A2:** stamp-follows-code or code-follows-stamp for the D5 comparator definition.
2. **C6:** annotate the holdout as pre-E15, or spend a re-read.
3. **Deferred items now four+ sessions old** — `gear_tier_stats` caller (Phase 3
   exit 10) and `ContentProfile`'s 6/8 assumption presets (criterion 7): schedule
   into `3k`, or formally re-scope the Phase 3 exit. Carrying them another session
   is the one option this work order rules out.

## What `3j` hands to `3k`

A gate whose number can be trusted: fail-closed on stamp drift, phase-outage-proof,
with every repaired check owning a RED mutation. `3k` is then the modelling session —
and per the repaired distribution, it is a **coverage** session first (63.9% of
logged damage has no sim key; slice is capped near ~36% until keys exist), ratio
tuning second (producing median 0.273). `3k` pre-registers which of the two it is
doing before touching `core/`.
