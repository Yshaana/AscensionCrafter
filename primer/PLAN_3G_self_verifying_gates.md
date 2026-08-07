# PLAN `3G` — the gate contract: instruments that cannot fail open

> **`LIVE`** — a plan that has NOT run; amend per ADDENDUM_3E_to_3F §3.1 before running. **Must be true today, and is citable as current truth.** If you find a claim here that the tree contradicts, that is a defect in this file. *(Classified `3f` F8c, 2026-08-07.)*

**Candidate session, written 2026-08-06 by the monitoring chat.** Not scheduled yet —
`PROGRESS.md` decides. Owner decision 2026-08-06: **this gets its own session rather
than being folded into `3e`.**

🛑 **Ordering is an open question for the owner.** The natural slot is after `3f`
(PHASE_3 T6, log ingestion), but the argument for putting it **before** `3f` is real:
`3f` builds a writer from logs into `builds.db`, and every gate below is about
preventing a bad number from reaching a database. Building the ingest first means
retro-fitting the gates to it.

---

## Why this exists

It is not a new idea. It is the same finding, four times, in one session.

`CHAT_MONITORING_PRIMER`'s review loop asks one question above all others:
**"does this check have a regime where it returns a number it cannot support?"**
Session `3d` asked it and found **four** live instances:

| Instrument | Its fail-open regime |
|---|---|
| `check_alignment()` | passes **vacuously** off-Hammerdin |
| the extract wrapper's "game is closed" check | Unix `find` shadowed the Windows one, the check errored, and it printed *"OK - game is closed"* |
| two of `3d`'s own checks | written and passing without biting |
| slice accuracy | explodes as coverage → 0; 1,859,400% at 0.2% coverage, in the committed manifest |

And `3e`'s preflight audit found a fifth: `within_tolerance` at
`calibrate_crawled.py:494` has **no coverage floor**, so a character the sim models
nothing for can score a pass.

> ✅ **ANNOTATION (`3i` A5): the fifth specimen is CLOSED.** The 20% coverage floor
> was applied at `3g` G4 (`389c735`; `calibrate_crawled.py`, grep
> `SUCCESSOR_COVERAGE_FLOOR_PCT`) and removed nobody — the four low-coverage passes
> it was designed to catch were the same characters E13 was inflating. The four
> specimens above it remain live examples of the class. The line above is kept as
> written because this plan's argument was built on it.

**Every one of these is the same shape: a measurement returning a confident number
outside the regime where it means anything.** That is a class, and a class deserves a
mechanism rather than five separate fixes.

---

## What to build

### `scripts/gates/` — pure assertion functions, no I/O beyond what they check

Each returns `PASS` / `FAIL` / **`INSUFFICIENT_DATA`**. 🛑 **The third verdict is the
whole point.** A gate that can only say pass or fail will say "pass" when it cannot
tell, which is the defect it exists to prevent.

| Gate | Catches |
|---|---|
| `file_is_stable(path)` | size **and** mtime unchanged across an interval — the truncated 46-second window |
| `corpus_is_complete(manifest)` | expected row/file counts present before any aggregate is published — the partial-corpus retractions |
| `test_is_discriminating(result)` | both arms produce identical or vacuously-passing output — `check_alignment()` off-Hammerdin |
| `schema_columns_match(rows, expected)` | column reads **by name, never index** — `glancing` read where `critical` was wanted |
| `metric_in_supported_regime(value, denom, floor)` | a ratio aggregated where its denominator approaches zero — slice accuracy, `within_tolerance` |

⚠ **`core/` purity applies** (`tools/audit/check_core_purity.py`): if any of these lands
in `core/`, no `print()`, no `argparse`, no paths, connection passed in. `scripts/` is
the right home for anything that touches the filesystem.

### The regression set already exists, and this is the part worth doing first

`ingest/export/seed_epistemics.py` holds **`RETRACTIONS`** — every claim this project
has had to withdraw, with what falsified it. That is a ready-made, honestly-collected
test set that nobody has used as one.

🛑 **Write one regression test per historical retraction, asking: would a gate have
caught this?** Then report the answer *as measured*, including the misses. The usage
report that prompted this session asserts *"every retraction should have been caught by
one of these gates"* — **that is a hypothesis, not a specification.** If it turns out
only half are catchable, that is the finding, and inventing a gate per remaining row to
force the number to 100% would be fitting the instrument to its own test set.

### `scripts/phase_runner.py` — the enforcement layer

Wraps each analysis step; **refuses to write a finding to `primer/` or seed the DB
unless the step's gates pass.** Emits `reports/<phase>_gate_report.md` listing every
gate, its verdict, and its evidence. Any `FAIL` blocks the commit.

⚠ **Scope check before building this half.** The runner is the ambitious part and the
part most likely to be abandoned half-built. The gates plus the retraction regression
suite have standalone value *today* — a gate you call by hand still bites. **Land the
gates first; the runner is the second commit, and a legitimate `3h` if the session runs
long.**

---

## What NOT to adopt from the usage report

The report also suggested tagging every empirical claim inline as
`[VERIFIED: n=X, source]` / `[PROVISIONAL: basis]`.

**Do not.** This repo already has a richer version of exactly that, and it is
queryable rather than prose: `confirmed_facts` (with `sample_size`, `evidence_ref`,
`verified_at_patch`, `realm`, `season`), `open_questions`, `retractions`,
`spell_mechanics`' per-field `source_tier_json` / `evidence_ref_json` /
`uncertainty_json`, and the five-tier `class_confidence` vocabulary. Adding a parallel
inline scheme would create a second place a confidence claim can live — **which is the
doc-vs-tree drift this project calls its most expensive failure mode.**

The report's other large suggestion — parallel subagents writing to `staging/<source>/`
with a reconciliation pass that surfaces conflicts instead of auto-resolving them — is
**already the repo's stated discipline** (Rule 3; `cross_check()`'s
`agree`/`disagree`/`unverifiable` verdicts, where *unverifiable is not a pass*). What is
genuinely absent is the **parallelism**, not the reconciliation. Worth revisiting only
if a session is actually blocked on wall-clock, which none has been.

---

## Exit criteria

1. `scripts/gates/` exists, each gate returns three verdicts, each has a unit test that
   makes it **fail** (not just pass).
2. One regression test per `RETRACTIONS` row, with the caught/not-caught split reported
   honestly — including which gate would have caught it, and which rows nothing catches.
3. The five known fail-open instruments above are each either fixed or explicitly
   recorded as accepted, with the reason.
4. 🛑 **No gate weakens an existing check to make itself pass.**
