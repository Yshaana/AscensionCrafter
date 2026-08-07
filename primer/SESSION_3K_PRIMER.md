# SESSION `3K` PRIMER — resolve the flip, then coverage. Modelling, pre-registered.

> **`LIVE`** — the work order for session `3k`, drafted 2026-08-07 (evening) from
> `AUDIT_3J_ADVERSARIAL.md` (§5 is the source list; this file orders and scopes it).
> **Expiry: superseded by the `3k` session record when `3k` closes** — mark it
> `SUPERSEDED BY` that file, per the established pattern. *(Born `LIVE`, inside the
> four-status vocabulary — `3j`'s work order was born `WORK ORDER` and was invisible
> to the F8c census until corrected. ⚠ Landing this file in `primer/` stales
> `CLAUDE.md`'s pasted census; refresh the paste in the same commit, or the suite
> fails at your own first commit, as it did at `18c2333`.)*

**Audit implemented:** `AUDIT_3J_ADVERSARIAL.md` (⚠ delivered via the oversight chat,
not yet in `primer/` — committing it is pre-flight).
**Previous session record:** `primer/Session_2026-08-07_3j_integrity.md`.

---

## §0 — The rules, INVERTED from `3j`

🛑 **`3k` is a MODELLING session: the gate is EXPECTED to move.** That permission is
narrow, and it is the whole discipline:

1. **No commit that can move the gate lands without a pre-registration that is its
   commit-parent.** Prediction first, run second, `git log` proves the order. `3i`'s
   7-seconds-late prereg is the counterexample; `3j` A2 (`a6e0fa2` → `77d7e17`) is
   the model — including naming what it CANNOT register.
2. **Pre-register the MODE before touching `core/`:** coverage (absent keys) or
   ratio tuning. Per the repaired distribution the answer is **coverage** — 63.9% of
   cohort logged damage has no sim key; the slice is arithmetically capped near ~36%
   until keys exist; tuning (producing median 0.273) is second and is **out of scope
   for `3k` unless the owner says otherwise** (standing decision 2).
3. **Every gate move is committed as a before/after pair** with its prereg cited.
   An unexpected move is a finding: stop, report the pair, no retroactive prereg.
4. **Refusal over fabrication, unchanged.** A key you cannot build from provenanced
   data is a named refusal, not an invented coefficient. The gate has **zero**
   passers — you are building a pass, not defending one, and a pass built on
   fabricated keys is worse than no pass.
5. **Mutation discipline continues:** every commit that changes a check includes the
   RED mutation, run, cited, registered in `ENGINE_BUGS.md`'s (parser-enforced)
   table. M50+ are yours.
6. **The holdout stays unspent.** It is annotated pre-E15 and is not read this
   session (standing decision 3). Reading it is `3l`'s call, once a tuned slice
   exists to validate.

---

## Pre-flight (one commit)

1. Commit `AUDIT_3J_ADVERSARIAL.md` into `primer/` (born `FINDING`, dated
   2026-08-07). The owner has the file from the oversight chat.
2. Overwrite `primer/CHAT_MONITORING_PRIMER.md` **in place** with the v6 content
   (owner has it; the file is versionless, the version lives in the title line —
   **never a `_v6` sibling**).
3. This file's own status line; refresh `CLAUDE.md`'s census paste (two new files in
   `primer/` = two drifts; `check_refusals.py` A4 catches both).

---

## Block 0 — Molten Core (FIRST; read-only until the shape is known)

The boundary `NEXT_PHASE_BOUNDARY = 2026-08-07T18:00:00Z` (owner hand-edit,
`efc9baa`) has **passed**. The last committed crawl (`c23b822`, captured
15:49–16:03Z) is pre-boundary and clean: ZG active, no MC record in the payload.
What the crawler did since is the diagnostic. Check `/api/phases` live (crawler
`HEADERS`; bare requests 403) and record the payload verbatim in the session record.

**Shape A — top-level flip** (crawler died at `assert_phase`, "PHASE FLIP
DETECTED", or the live payload shows a new active top-level phase):
1. Bump `EXPECTED_PHASE_NAME`; `SEASON`/`SEASON_NUMBER` only if the season actually
   rolled. Fix the stale comment two lines up ("Phase 2 is scheduled for
   2026-08-08") in the same edit.
2. Confirm `NEXT_PHASE_BOUNDARY` self-retires (payload carries a top-level phase
   starting ≥ the boundary). If yes, leave it — stale values cost nothing.
3. Re-derive the corpus. Verify every capture in `[18:00Z, flip-modelled)` got
   `phase_label` NULL, not mis-stamped, **before any gear tier is read**.
4. If `n` changes, commit the before/after gate pair with the flip evidence as its
   reason — the one sanctioned unpredicted move.

**Shape B — payload lag / no flip visible yet:** captures ≥18:00Z are NULLed by the
boundary guard and flagged per-parse; that is correct. Proceed with Blocks A–C; do
not read gear tiers; leave a dated note in the record that the flip is pending.

**Shape C — child phase** (crawler ran CLEAN but the payload shows MC as a child,
`progression_parent_phase_id` set — the `Phase 1.1` precedent): 🛑 **STOP-POINT.
This is the shape with no protocol.** `assert_phase` will never fire and the
boundary guard **can never self-retire** (its disarm condition requires a top-level
phase). Every capture from 18:00Z onward is inadmissible indefinitely. Present the
owner the options — do not pick one:
   (a) manual retirement: a dated owner-decision constant (e.g.
   `BOUNDARY_RETIRED_AT`) that disarms the guard, plus a synthetic sub-window so
   post-MC captures are labelled (e.g. `"Phase 1 - Zul'Gurub / MC"` keyed off the
   boundary timestamp) and distinguishable the moment gear tiers diverge;
   (b) keep NULLing until the server models it top-level (cost: every day of
   post-MC data is inadmissible);
   (c) something else the owner prefers.
   Whatever lands: it is new guard code → it ships with its RED mutation.

🛑 **STOP-POINT 0:** any other surprise (season roll, two active top-levels, schema
change) → ask before touching the corpus.

---

## Block A — documents (fixed budget, one block)

**A1 —** `PROGRESS.md` top block: the boundary line ("arms `2026-08-08T00:00:00Z`")
is stale; correct it with the Block 0 outcome, whichever shape it took.
**A2 —** `primer/PHASE_3_builds_repo.md` exit criterion 1: "⚠ Status 2026-08-06:
MET as written (4 of 41)" is three gate-repairs stale — current truth `0 of 36, NOT
met`. Append the correction in the D7 style (stamped/`LIVE` text is corrected by
appending, never rewritten in place).
**A3 —** While in that file: the exit-criteria list has no per-criterion status.
Optional, cheap, and it serves the "re-read Phase 3 exit honestly" step: annotate
each criterion with its audited status (`AUDIT_3J` §5 / the oversight chat's
re-derivation: 2 of 7 met — `find_builds` ✅, stamping ✅, crit-table 🟡, gate ❌,
string-matching ❌, measured-CI ❌, ContentProfile ❌).

---

## Block B — coverage (the modelling core)

**B1 — pre-register the mode and the pass, before touching `core/`.** One document
in `predictions/`, committed before any key is built, containing: (a) mode =
coverage; (b) the target list (B2) with each ability's absent logged-damage share,
read from `per_ability_summary.json`; (c) what success looks like, as numbers —
e.g. "absent mass 63.9% → below X%; slice expected to move toward the ~36% cap;
within-±20% count expected unchanged until tuning" — with each prediction
falsifiable; (d) what is explicitly NOT predicted (per-ability ratios — that is
tuning).
**B2 — pick targets from the committed artifact,** not from memory: rank the absent
keys by logged-damage share, take the largest until the registered mass target is
covered. Enumerate them by spell_id + name in the prereg.
**B3 — build the keys, provenance-enforced.** Each key's mechanics come from the
spell DB with provenance; where the data does not exist, the key is a **named
refusal** (the E14-family pattern), not a guess. Phantom production (58.4% of sim
damage on abilities the log never saw) is the warning: a key that produces damage
the log doesn't show is as wrong as a missing one.
**B4 — re-run the instrument and the gate; commit pairs.** `per_ability_summary.json`
regenerated (its own dirty-tree and filter guards apply); gate manifest from a clean
tree; before/after cited against B1's predictions, confirmed or falsified — a
falsified prediction is reported, not rescued (`3i` B set the precedent).
**B5 — keyed-but-starved (11.3%, GCD allocation)** — only if B1 registered it;
otherwise it is `3l`'s, named in the handoff.

---

## Block C — the two owner-scheduled deliverables (decision 2026-08-07; not carried again)

**C1 — `gear_tier_stats(phase=…)` production caller.** Phase 3 exit-list item,
🟡 since `3g`. A real read surface (CLI or report path) that passes the resolved
phase — and **refuses** with a named reason while phase handling is unresolved
post-boundary (Block 0 gates this). "Implemented, tested, uncalled" ends here.
**C2 — `ContentProfile` presets → corpus-measured durations** for the content types
the gate's scopes actually use. The corpus holds thousands of real encounter
durations; this is measurement, not re-verification. Provenance strings become
`measured: …` with the query stated. ⚠ **Presets feed the gate's sim side, so this
CAN move the gate → it needs its own prereg pair (§0 rule 1), separate from
Block B's.** The 2 already-measured presets are the template.

---

## Block D — only if time remains (else: named in the handoff, not carried silently)

**D1 —** the 1,208 owner<pet groups: explain, or register as a bounded unknown with
the measured cohort impact (currently 0 of 41) and a named unblock condition.
**D2 —** the frozen `gate_manifest.json` dirty-tree reason: owner call (standing
decision 4) — annotate the FROZEN status note, or close the thread as a record.

---

## Standing decisions needed from the owner (ask, don't guess)

1. **Block 0 shape C:** the child-phase protocol — option (a), (b), or other.
   Only fires if that shape is what happened.
2. **Scope:** is ratio tuning in `3k` if coverage lands early, or deferred whole to
   `3l`? Default written into this order: **defer** — coverage results decide `3l`'s
   shape, and a session that does both under one prereg muddies attribution.
3. **Holdout:** stays unspent (default, carried from `3j` C6). Only revisit if the
   owner explicitly spends it.
4. **D2:** the frozen manifest's dirty-reason — annotate or close.

---

## What `3k` hands to `3l`

A gate with real coverage under it and an honest absent-mass figure; measured
content profiles under the sim side; a phase-labelled post-MC corpus (or a stamped
owner decision on why not); and the tuning problem — producing median 0.273,
keyed-but-starved 11.3% — as `3l`'s single pre-registered concern. If coverage
alone lifts any character into ±20%, that is a finding for the record, predicted or
not — the criterion needs ≥3 with the ≥50%-coverage rider, so expect `3l` (tuning)
and then the honest Phase 3 exit re-read: 2 of 7 criteria met today, and criteria
2 (string matching), 3-full/4 (blocked on T5 per-parse stats) are still open behind
the gate.
