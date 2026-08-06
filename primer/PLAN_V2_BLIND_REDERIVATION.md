# PLAN — the blind v1-vs-v2 re-derivation

**Owner decision, 2026-08-06.** `builds/my-builds/build_paladin-hammerdin.md` is frozen
as a **v1 artifact** rather than maintained. When Phase 4's theorycrafter can design a
build, it re-derives this one **blind**, and the two are compared.

🛑 **This document must be written and stamped BEFORE the theorycrafter runs.** It is the
same discipline as `3d`'s holdout and the gate's successor criterion: a comparison whose
scoring is decided after seeing the result measures nothing.

---

## Why v1 is an unusually good evaluation set

Not sentiment. Three properties, none of which a synthetic benchmark would have:

1. **It is a complete, committed, dated artifact** — one document, ~20 explicit claims,
   produced by a named method (live tooltips, hand parses, inference; no spell database,
   no simulator, no calibration gate).
2. **It has already been partially graded.** `retractions` holds 24 rows and several are
   v1's own claims — the Improved Cleave `9 + AP × 1.0` formula, the Duality SP-amp
   reversal, *"Sword Specialization produces zero output"*, the hit/expertise
   overstatement. **Those have known answers.** A v2 that reproduces a retracted v1 claim
   has failed a test whose key is already in the repo.
3. **It records its own uncertainty.** §12 is an assumption register split into resolved,
   retracted and open. That is a scoring rubric someone else already wrote.

---

## The protocol

### Step 1 — Freeze the inputs, not just the output ✅ done 2026-08-06

A v2 disagreement is only interpretable if you can tell *"v2 is right"* from *"different
character"*. Both are now recorded:

* **v1's assumed state** — AP 546–584, SP 400–533, Str 134, Path of Duality, pre-Light's
  Hope. In the frozen document's own §6.
* **The current state** —
  `data/source/captures/2026-08-06_elric_hammerdin_proc_retest/`: two stat blocks, two
  logs, Path of Intelligence, AP 134 / SP 612, The Light's Hope equipped.
  ⚠ **Last clean capture before the Phase 2 flip on 2026-08-08.**

### Step 2 — Pre-register the claim list 🛑 DO THIS BEFORE V2 RUNS

Extract every falsifiable claim from the frozen v1 document into a scored table:
stat weights (§10), the chase-list ranking (§7), the rotation priority (§11), the
class-tag verdicts (§2), the Titan's Grip A/B question (§6), the hit and expertise
walkback (§10), the ~48% talent-stack ceiling (§10a).

For each, record **before v2 runs**:

| Field | Meaning |
|---|---|
| `claim` | as v1 stated it |
| `v1_confidence` | what v1 said about its own certainty |
| `known_answer` | ✅ confirmed / ❌ retracted / ⬜ open — from `confirmed_facts` and `retractions` |
| `scoring` | what a v2 agreement, disagreement or silence would each mean |

🛑 **The `known_answer` column is the part that makes this a test rather than a demo**,
and it must be filled from the seeds, not from judgement at comparison time.

Register the whole table through `ingest/export/seed_predictions.py` under its own slug.
`record_prediction` refuses to overwrite a slug, and **that refusal is the
pre-registration** — the same mechanism that pins the `3e` holdout.

### Step 3 — Run v2 blind

🛑 **The frozen document must not be in the session's context.** Removed from
`CLAUDE.md`'s auto-load 2026-08-06 for exactly this reason; its own header repeats the
instruction. A session that reads it and then "derives" a build is measuring anchoring.

Inputs v2 is allowed: the current capture, the databases, the crawl corpus, the sim.
Inputs v2 is not allowed: the frozen doc, and any session record that quotes its
conclusions.

### Step 4 — Score, and read the disagreements first

Agreements are the least informative cell — two methods can share an error. The
interesting cells:

* **v2 disagrees, and the answer is known** → decisive, in whichever direction.
* **v2 reproduces a *retracted* v1 claim** → 🚨 a regression with a known key. This is the
  single most valuable outcome the test can produce and it should be treated as a
  finding, not a footnote.
* **v2 is silent where v1 was confident** → often correct behaviour. v1 asserted things
  it could not support; refusing to answer is an improvement, not a gap. **Score it as
  such, or the test rewards overconfidence.**
* **v2 is confident where v1 was silent** → check the provenance chain before crediting it.

---

## Proposed Phase 4 exit criterion

`PHASE_4_legos_and_theorycrafter.md` currently has no test with a known key. This is one:

> **The theorycrafter re-derives `build_paladin-hammerdin` blind from the 2026-08-06
> capture, and every disagreement with the frozen v1 document is accounted for by a
> recorded finding — a `confirmed_facts` row, a `retractions` row, or a stated change in
> character state. No disagreement is left as "the model says so".**

That is checkable, it has a scoring key that already exists, and it cannot be satisfied
by a model that is merely confident.

---

## What this plan does NOT claim

* It does **not** assume v2 will be better. A v2 that agrees with v1 everywhere has
  learned nothing from three phases of data, and that result must be reportable.
* It is **not** a benchmark for the toolkit in general — it is one build, one character,
  one owner. ⚠ The same single-character-validation risk `AUDIT_3C_ADVERSARIAL.md` §5
  named as the project's largest structural weakness applies here too.
* It does **not** replace the calibration gate. The gate measures whether the sim
  reproduces reality; this measures whether the *advice layer* improved. Different claims.
