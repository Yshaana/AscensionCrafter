# AUDIT `3j` — ADVERSARIAL

> **`FINDING`** — the audit of session `3j`, written 2026-08-07 (evening) from a fresh
> clone at `c23b822`. Method: clone, read the diff `2de79e5..cba60f6` plus the three
> post-close commits, run both harnesses on the clean clone, and **independently
> re-run three of the session's registered mutations from source** (M37, M31, M45)
> rather than trusting the record's RED column. Claims not reproducible from the
> clone are marked as such.

**Verdict in one line:** `3j` survived its audit. Every claim spot-checked reproduces
from the clone — including the three revert tests this audit ran itself — and the §6
not-done list is accurate. **The findings below are forward-looking, and the loudest
one is environmental, not a session defect: the phase boundary was moved to
`2026-08-07T18:00:00Z` by two post-close owner commits, that time has now passed, and
if Molten Core lands as a CHILD phase — the server's own precedent with `Phase 1.1` —
neither tripwire fires and the boundary guard can never self-retire.**

**Closing gate as committed:** `0 of 36 within ±20% · 0 qualified · slice 26.31%
(n=23)`, 3 NOT ADMISSIBLE (Nodding, Boomcat, Deyindra). Reproduced from
`predictions/gate_manifest_3e.json` (status `LIVE`, `git_sha ed00608`, clean tree,
`parse_admissibility_rule_applied: true`), not re-run: no `.db` is committed.

---

## §1 — What `3j` earned (and what this audit re-ran itself)

The session's job was to end the class of check that cannot fail. The test of that is
not the record's mutation table — it is whether a hostile reader can re-run the
reverts and get the same reds. This audit did, on a fresh clone:

* **M37 (E3 full revert, `if has_autos and not autos_producing:` → `if False:`)** —
  re-run from source by this audit: **3 named `[3j-A4]` FAIL arms, suite exit 1**;
  restored, exit 0. The record claims 3 red arms. **Exact match.** Pre-`3j` this same
  revert left the suite at 0 FAILURES (`AUDIT_3I` §8) — the class is closed.
* **M31 (delete E16's Checks row) on a clean clone** — re-run by this audit:
  `check_sim_engine.py` baseline **exit 2**, under M31 **exit 1**, restored exit 2.
  The A6 claim ("the doc-sync verdict reaches the exit code on a clean clone") is
  true in the environment it was made for.
* **M45 (disable `assert_publishable`'s payload-level raise)** — re-run by this
  audit: `[3j-0]` goes FAIL with `raised='NOTHING'`, suite exit 1; restored, clean.
  The phase-outage guard is real, not a stub — and the harness carries the
  publish-arm (the actual `3i` roster, 3 of 36 flagged for three different reasons,
  asserted to PUBLISH), so a refuse-always implementation fails.
* **The harness on a clean clone: 59 PASS, 0 FAIL, exit 0** (`check_refusals.py`).
  `check_sim_engine.py` runs its doc-sync arms green then refuses on the missing db
  with exit 2, which is now a *verdict-bearing* exit rather than an unconditional one.
* **A1 verified in source:** `assert_stamped_thresholds()` failure now raises
  `SystemExit("🛑 GATE REFUSED …")` (`calibrate_crawled.py:~860`); the two dead
  `pa is not None` branches are gone; `parse_admissibility_rule_applied` is derived
  from per-row `admissibility_computed` ground truth and asserted against it
  (`:1545`, `:2016-2035`). The honest negative in §5 of the record — the first A1
  mutation ("restore the hardcoded literal `True`") stayed GREEN because the
  assertion re-derives the fact — is the right kind of negative result to keep.
* **A2 is a genuine pre-registration.** `a6e0fa2` (14:19:41) is the parent of
  `77d7e17` (14:24:55) — registered before run, order verified by this audit with
  `git log`. More importantly the document is honest about its limits: it states in
  bold that it **cannot** retroactively pre-register D5's known effect, and registers
  only the three unasked questions. P3's counterexample (filters CAN add a flag via a
  raised median: 0.76 unfiltered → 0.42 filtered) **falsifies `AUDIT_3I` §4's one-way
  claim as stated** — this audit's own §4 was wrong of the median, and the correction
  is now stamped into the amendment text. Credit for falsifying the auditor.
* **The stamp amendment is appended in the D7 correction style** (`CALIBRATION_
  TOLERANCE.md:370+`), never rewritten in place, with the owner decision named and
  the correctness rationale (self-overlap comparators — Nodding's unfiltered set is
  371 scopes; sub-60s comparators contradicting predicate 3) stated with measured
  evidence, not vibes.
* **B1/B3 verified in source and harness:** `PRAGMA user_version` = 1 stamped at
  init, `assert_schema_current` refuses v0, `migrate_schema` is a reachable green
  path (harness proves the round trip), `UNRESOLVED_SPELL_ID = -999999` replaces the
  NULL PK escape and is counted in `build_builds_db.py`'s census. B3 was measured
  before fixing (0 of 291,320 / 0 of 22,427) so the closure is provably gate-neutral.
* **The document half held for once.** `CLAUDE.md:199` corrected; the band table is
  generated-and-asserted (`[3j-C3]` PASS, and M48 — one changed digit — is
  registered); the census is 65 files, 13 LIVE / 38 HISTORICAL / 5 SUPERSEDED /
  9 FINDING, pasted-equals-generated; `predictions/*.json` all carry status keys
  including `gate_manifest_3e.json` (`LIVE`); ENGINE_BUGS' mutation table is
  parser-enforced, contiguous, M1..M49. Document discipline was the weaker half for
  three consecutive sessions; **this session it was not.**

`3j` also stayed inside its own invariant: `0 / 0 / 26.3% (n=23)` at every commit,
verified by the manifest regens at `328e719` and `cba60f6`, and no modelling block
was opened.

---

## §2 — 🚨 TIME-CRITICAL: the boundary moved, it has PASSED, and Molten Core has a third shape nobody wrote a protocol for

**What changed after close, by hand:** two owner commits (`139170b` 16:47,
`efc9baa` 16:50 BST — manual edits, no session) moved `NEXT_PHASE_BOUNDARY` from
`2026-08-08T00:00:00Z` to **`2026-08-07T18:00:00Z` ("19:00 BST Molten Core
unlock")**. `EXPECTED_PHASE_NAME` was correctly left at `Phase 1 - Zul'Gurub` — it
must not be bumped until the flip is *observed*. As of this audit's run time the
boundary has passed: **the flip is live now, not tomorrow.**

**The last crawl is safe.** `c23b822` (17:03 BST) captured at 15:49–16:03Z,
*pre*-boundary: payload shows ZG active (`end_date: null`), child `Phase 1.1`
active, **no Molten Core record at all**. So `/api/phases` had not yet modelled the
boundary an hour before it, no poison payload is on disk, and every capture in the
corpus is cleanly pre-MC.

**The two expected shapes are both defended.** If MC lands as a new **top-level**
phase: the next crawler run dies loudly at `assert_phase` ("PHASE FLIP DETECTED"),
which is the tripwire working — bump `EXPECTED_PHASE_NAME` (+`SEASON` if rolled),
re-derive, verify post-boundary `phase_label`. If the payload lags: `phase_guard`
NULLs every capture ≥18:00Z, predicate 4 flags them per-parse, and — post-`3j`
Block 0 — a payload *refusal* makes the gate refuse to publish instead of printing
`0 of 36`. Both paths verified in source by this audit.

**🚨 The third shape: MC as a CHILD phase.** The server's only in-season precedent
is exactly this — `Phase 1.1` shipped as `phase_number: 2`, `parent: 2`, invisible
to `assert_phase` by design. `season_config.py`'s own comment block knows child
boundaries are invisible; that is *why* `NEXT_PHASE_BOUNDARY` exists. But the
guard's self-retire condition is **"a top-level phase starting at or after this
date"** — a condition a child-phase MC **never satisfies**. Consequences if MC is a
child:

1. `assert_phase` stays green forever — no alarm.
2. Every capture from 18:00Z onward is phase-NULL → "unresolved phase" →
   inadmissible, **indefinitely**, because the guard cannot disarm itself.
3. The only symptom is a quiet, growing pile of flagged captures. The corpus stops
   accumulating admissible post-MC data with no single loud failure anywhere.

There is no committed protocol for manually retiring a child-phase boundary, and no
decision on how post-MC captures get phase-labelled in that case (same ZG window?
a synthetic `MC` sub-window keyed off the boundary timestamp? — this matters the
moment gear tiers diverge). **This is `3k`'s Block 0, and it needs an owner
decision, not just code** (see §5, item 1). Until it is resolved: no gear tier read,
per the standing rule — and the daily crawler's behaviour tonight is itself the
diagnostic: *loud death = top-level flip; silent success with a ZG payload = child
shape or no flip yet. Check which, before anything else next session.*

---

## §3 — Findings against the session itself (small, and none moves a number)

1. **The v5 monitoring primer's expiry has fired and its body misdates itself.**
   Its own rule: supersede at v6 when `3j` closes — `3j` has closed. The `3j`
   addendum is honest and complete, but the v5 body says "Written 2026-08-08" and
   "Where things stand, 2026-08-08" — it was committed 2026-08-07 13:01 (`18c2333`),
   a `LIVE` document dated in its own future. Now additionally stale: its open
   thread 1 and standing-actions section describe the `2026-08-08T00:00:00Z`
   boundary, superseded by the owner commits. **v6 is due and should be written
   from the post-`3j` + post-boundary-move state** (drafted alongside this audit).
2. **`PROGRESS.md`'s top block was staled within two hours of being written** — by
   the owner's boundary move, not by `3j`: "the phase boundary arms
   `2026-08-08T00:00:00Z`" and "checked live … ~12 h before the boundary" are both
   now false (it was ~6 h). Not a session defect — the session recorded what was
   true at commit time — but the file is `LIVE` and must be corrected in `3k`'s
   first document pass, with the MC outcome, whichever shape it takes.
3. **`season_config.py`'s comment still says "🚨 Phase 2 is scheduled for
   2026-08-08"** two lines above a constant now naming 2026-08-07. One-line fix,
   same commit as the `EXPECTED_PHASE_NAME` bump when it happens.
4. **The B2 real-corpus arms are unexercisable from the clone** (printed SKIP, by
   design — no `.db` committed). Fixture arms + the migration round-trip carry the
   claim; noted as the standing reproducibility limit, not a defect.
5. **`3j`'s §6 not-done list is accurate** — verified: `gear_tier_stats(phase=…)`
   still has no production caller; `ContentProfile` is still 6 of 8
   `assumption:…`; the 1,208 owner<pet groups are located, not explained;
   `gate_manifest.json` (frozen `3d`) still carries `git_working_tree_dirty: true`
   with no reason key. All correctly scheduled or explicitly deferred. An honest
   not-done list, second session running.

---

## §4 — Reproducibility limit (unchanged, restated)

Tier-2 captures gitignored; no `.db` committed. Corpus figures (291,320 rows /
2,818,810,395.0 damage / n=23…) are unverifiable from the clone; what IS verifiable —
and was verified — is function behaviour under synthetic fixtures, manifest-internal
arithmetic, mutation reverts, and commit ordering. The committed
`per_ability_summary.json` and clean-tree `git_sha` manifests remain the honest
perimeter.

---

## §5 — The list `3k` works from

In priority order. Items 1–2 are gates on everything else.

1. **🚨 Block 0: resolve the Molten Core flip — with the child-phase protocol.**
   (a) Observe which shape landed (crawler behaviour + `/api/phases` verbatim in
   the session record). (b) Top-level shape: bump `EXPECTED_PHASE_NAME` (+season if
   rolled), re-derive the corpus, verify post-boundary stamping. (c) **Child
   shape (owner decision required):** define and implement manual boundary
   retirement — how `NEXT_PHASE_BOUNDARY` is cleared when no top-level phase will
   ever satisfy the self-retire condition, and how post-MC captures are
   phase-labelled (synthetic sub-window keyed on the boundary timestamp is the
   obvious candidate; decide, stamp, then implement). (d) Fix the stale
   `season_config.py` comment. (e) 🛑 STOP-POINT: any third-shape surprise
   (season roll, schema change, two actives) → ask, don't guess.
2. **Correct the staled `LIVE` documents in one pass:** `PROGRESS.md` top block
   (boundary + MC outcome), commit the v6 monitoring primer **in place, no `_v6`
   sibling** (draft delivered with this audit).
3. **Pre-register the modelling mode before touching `core/`** — coverage first
   (63.9% of logged damage has no sim key; slice arithmetically capped near ~36%)
   or ratio tuning (producing median 0.273). Pick targets from
   `per_ability_summary.json`, register what a pass looks like, then build.
   Zero passers: expect to build a pass, not defend one.
4. **The two owner-scheduled deliverables**, not carried again:
   `gear_tier_stats(phase=…)` production caller (Phase 3 exit 10, currently 🟡),
   and `ContentProfile` presets replaced with **corpus-measured** durations for the
   content types the gate's scopes use (criterion 7 — load-bearing: presets feed
   the sim side).
5. **The holdout stays unspent** until the tuning slice has something to validate;
   when read, it is read once, post-E15, like-for-like — the pre-E15 annotation
   already forbids citing the old pair.
6. **The 1,208 owner<pet groups** — explain or formally register as a bounded
   unknown with a measured cohort impact (currently 0 of 41 affected).
7. Housekeeping, one commit: decide the frozen `gate_manifest.json` dirty-reason
   question (annotate the FROZEN doc's status note vs. leave — owner call, then
   close the thread).

**Tone check, per the standing method:** `3j` is the first session since `3f` where
the audit's sharpest finding is about the *environment*, not the session. That is
what an integrity session is for. Say so, and then hold `3k` to the prereg-first
standard `3j` just re-armed.
