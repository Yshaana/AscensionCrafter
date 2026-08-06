# PLAN — the blind v1-vs-v2 re-derivation

**Owner decision, 2026-08-06.** `builds/my-builds/build_paladin-hammerdin.md` is frozen
as a **v1 artifact** rather than maintained. When Phase 4's theorycrafter can design a
build, it re-derives this one **blind**, and the two are compared.

🛑 **This document must be written and stamped BEFORE the theorycrafter runs.** It is the
same discipline as `3d`'s holdout and the gate's successor criterion: a comparison whose
scoring is decided after seeing the result measures nothing.

---

## ✅ AMENDED AND SEEDED — 2026-08-06, session `3f` (F8). This document may now be run.

| | |
|---|---|
| **Decision taken** | 2026-08-06, by the owner, **before v2 ran** |
| **Amendment landed** | session `3f`, 2026-08-06 |
| **Seed row** | `ingest/export/seed_epistemics.py` → `open_questions.plan_v2_blind_rederivation_scoring_rescoped` |
| **Status of the unamended version** | superseded; do not run it |

🛑 **The seed row is the pre-registration, not this heading.** A design decision
that changes what a test measures belongs in the seeds — *"Prose is not a seed"*
(`/close-session`). If the row is absent from `open_questions` after a rebuild,
the amendment has not landed and v2 does not run.

**Stamped 2026-08-06 by the monitoring chat, after the `3e` audit
(`primer/AUDIT_3E_ADVERSARIAL.md` §8), and decided by the owner the same day.**

**The blind test as written is not blind.** Step 2 makes `known_answer` the thing that
turns this from a demo into a test and fills it from the seeds; Step 3 then lists v2's
permitted inputs as *"the current capture, **the databases**, the crawl corpus, the sim."*
**The databases are the answer key.** `RETRACTIONS` names v1's graded claims verbatim and
by slug — `sword_specialization_zero_output`, `duality_sp_amp_not_applying`,
`improved_cleave_is_low_value_because_the_flat_is_small`, `art_of_war_dead_slot` — which
are exactly the ones cited below as v1's known-wrong claims. A v2 session with DB access
learns, before deriving anything, that Sword Specialization is not zero-output.

**✅ Owner decision, 2026-08-06 — rescope the scoring:**

* **The headline is v1's still-open (⬜) claims only.** They have no answer key anywhere in
  the tree, and they are scored against the 2026-08-06 Hammerdin proc-retest capture —
  tier-1 evidence rather than a seeded verdict.
* **The retracted claims become a labelled sanity check**, reported after the headline and
  reported *as leaked*: "v2 avoided these; it could also have looked them up."
* **No DB blinding and no pre-v1 rebuild.** Blinding by exclusion list is an honour system
  unless a filtered view is built, and this project does not need another guard that is
  documented rather than implemented. A pre-v1 rebuild would be a real blind but hands v2
  less knowledge than the current toolkit, so a v2 miss could not be separated from "v2 had
  less to work with".
* **Step 4's flagship outcome is RETIRED** — *"v2 reproduces a retracted v1 claim → the
  single most valuable outcome the test can produce"*. It was never available; the leak had
  already suppressed it.
* **Unchanged and still the best guard in this document:** scoring v2's *silence* as an
  improvement, "or the test rewards overconfidence". That works on open claims.

⚠ **Also wrong below and corrected here: `retractions` holds 32 rows, not 24.** It held 32
before `3e` started. The count is load-bearing — it is this document's argument for why v1
is a good evaluation set, and `PLAN_3G:113` sizes its regression suite from it.

✅ **Both landed in `3f` (F8), 2026-08-06:** the body of this plan below is amended in
place (Step 4's flagship outcome struck through and replaced, the row count corrected),
and the rescope is seeded as
`open_questions.plan_v2_blind_rederivation_scoring_rescoped`. A decision that changes
what a test measures is not a prose note — *"Prose is not a seed."*

---

## Why v1 is an unusually good evaluation set

Not sentiment. Three properties, none of which a synthetic benchmark would have:

1. **It is a complete, committed, dated artifact** — one document, ~20 explicit claims,
   produced by a named method (live tooltips, hand parses, inference; no spell database,
   no simulator, no calibration gate).
2. **It has already been partially graded.** `retractions` holds **32** rows (⚠ this line
   read "24" until `3f` F8; the tree held 32 before `3e` started, and the count is
   load-bearing — it is this section's argument for why v1 is a good evaluation set, and
   `PLAN_3G:113` sizes its regression suite from it) and several are
   v1's own claims — the Improved Cleave `9 + AP × 1.0` formula, the Duality SP-amp
   reversal, *"Sword Specialization produces zero output"*, the hit/expertise
   overstatement. **Those have known answers** — ⚠ and that is exactly why they are now a
   labelled SANITY CHECK rather than the headline (see the amendment above): the key is in
   the repo, and v2 can read it. *"A v2 that reproduces a retracted v1 claim has failed a
   test whose key is already in the repo"* was this document's original framing and it is
   retired; the converse — v2 avoiding them — proves nothing, because it could simply have
   looked them up.
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
* ~~**v2 reproduces a *retracted* v1 claim** → 🚨 a regression with a known key. This is the
  single most valuable outcome the test can produce and it should be treated as a
  finding, not a footnote.~~
  🛑 **RETIRED 2026-08-06 (owner decision; landed `3f` F8). This outcome was never
  available.** The leak had already suppressed it: v2 can look the retracted claims up
  in `retractions` by slug, so it will avoid them — and that avoidance would have been
  scored as v2 having improved. Counting it is assumption-laundering, *"v2 read the
  answer"* recorded as *"v2 measured the answer"*. The retracted claims are now a
  **labelled sanity check**, run and reported AFTER the headline and reported *as
  leaked*: "v2 avoided these; it could also have looked them up." A sanity check that
  says so is worth having; a headline that does not is not.
* **The headline is v1's still-OPEN (⬜) claims**, which have no answer key anywhere in
  the tree, scored against the 2026-08-06 Hammerdin proc-retest capture — tier-1
  evidence rather than a seeded verdict.
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
