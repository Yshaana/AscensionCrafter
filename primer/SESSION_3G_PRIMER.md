# SESSION `3G` PRIMER — fix the explosions, and make the gate move on purpose

> **`SUPERSEDED BY primer/Session_2026-08-07_3g_explosions.md`** — `3g` ran and closed on
> 2026-08-07, so this work order's expiry condition has fired. **Do not run it again.** Kept
> because the session record is written against its task numbering, and because three of its
> premises turned out to be wrong in ways worth reading: coverage does **not** fall with E13
> (§0), the E13 factor is **100 and not ~78** (Block A/G1), and `check_refusals.py` did
> **not** already walk `primer/` (G9). *(Born with a status line and an expiry condition,
> per `3f` F8c; retired by that condition.)*

**Work order for Claude Code.** Written by the monitoring chat 2026-08-07 against a fresh clone
at `227b033`, after `3f` closed and was audited. Read this first, then
`primer/AUDIT_3F_ADVERSARIAL.md` (the `file:line` evidence for everything below — note its own
correction header), then `primer/ENGINE_BUGS.md` E13/E14 and the check registry.

Predecessors: `primer/Session_2026-08-06_3f_instruments.md` (what `3f` did),
`primer/SESSION_3F_PRIMER.md` (`HISTORICAL`, do not run it again).

**Task naming: `G1…Gn`.** `E`-numbers are **defect ids** and `M`-numbers are **mutation ids**;
neither is ever a task id. "Fix E13" is task **G1**. Where this document means a PHASE task it
says `PHASE_3 T6` in full.

**🌙 This session runs overnight, unattended.** §0.9 says how to handle that. The owner has
already settled the three decisions that would otherwise have blocked you — §0.8. Everything
else runs on a **stated, reversible default** and lands as a row in `PROGRESS.md`'s blocked
table. **Nothing waits for an answer that cannot arrive.**

---

## §0 — The invariant, inverted

`3f` was scoped so the gate **could not** move, and the whole session was checkable against one
unchanging number. **`3g` is the opposite: the gate MUST move, and the discipline is that every
move has exactly one named cause.**

> 🛑 **Every commit reports the gate before and after, against the frozen 41. A commit that
> changes damage arithmetic states WHICH defect moved it, in which direction, and by how much.
> A commit that moves the gate for two reasons at once is a commit that must be split.**

**Baseline, carried from `3f` and unchanged across ten commits:**

> `5 of 36 within ±20% · 2 qualified · slice accuracy 64.3% at coverage ≥20% (n=23)`

🛑 **PRE-REGISTER THE DIRECTION BEFORE YOU RUN IT.** For each of G1 and G2, write into the
commit message *before* the after-number exists: which way the gate should move, why, and
roughly how far. This is the same rule as F9's tolerance, applied to a fix instead of an
assertion.

**And say the uncomfortable part out loud in advance:** E13 and E14 both remove *positive*
error. The sim already **under**-produces by about a third on what it models. So removing them
should push deltas **more negative**, and the within-±20% count should **fall, not rise** —
`Ari` in particular, whose −9.7% pass is standing on a 78× auto-attack. **A fix that makes the
gate look better is the one to be suspicious of.** If the number improves, stop and find the
second thing you changed.

⚠ **Both gate metrics move, not one.** Stripping a 78× auto-attack and a 12,000-tick DoT
removes modelled damage, so **coverage falls too** — and slice accuracy has coverage in its
denominator. Report the pair `(within_tolerance, slice_at_≥20%)` together at every step, plus
`n` for the band, and never quote a slice figure without its `n`.

---

## §0.5 — 🚨 G0, the deadline item, and it may already have fired

**The server flips to Phase 2 on 2026-08-08.** The pre-flip baseline was scheduled 2026-08-07
20:00. By the time you read this the flip may have happened, be hours away, or have happened
*mid-session*. **Handle all three; do not assume which.**

**First action of the session, before anything else:** fetch `/api/phases`, print what the
server says, and state plainly in your first output whether the flip has occurred. If it has,
check that `data/source/crawl/baseline_phase1/` is byte-identical to its committed state —
`3f` found `crawl_phases()` writes before it asserts, and did it to that file once already.

**G0 — the horizon rule defends against the wrong thing.**
`core/builds/phases.py:110-114` returns NULL for a capture later than the **payload's fetch
time**. But `3f`'s own finding (session record `:115-121`) is that **`/api/phases` does not
contain the 2026-08-08 boundary at all**, and Phase 1's window is `open_ended` with
`ends_at = None` (`phases.py:85-86`). `latest_phase_windows()` takes the **newest** payload
(`build_builds_db.py:57`), and `crawl_phases()` writes before it asserts — deliberately, for
the daily crawler.

So: **the first post-flip daily crawl appends a post-flip payload, the horizon jumps past the
flip, and every post-flip capture up to that fetch time resolves to `Phase 1 - Zul'Gurub`.**
Reproduced by the auditor against the committed payload:

```
phase_windows(payload, fetched_at="2026-08-09T06:00Z")
resolve_phase("2026-08-08T12:00:00Z", w, h)  ->  ("Phase 1 - Zul'Gurub", None)
```

That is precisely the failure F8b exists to prevent, arriving through a door the horizon rule
does not cover.

**Required shape of the fix — a positive assertion, not a horizon:**

* A capture may take a phase label **only if the payload's own phase set is consistent with
  `season_config.EXPECTED_PHASE_NAME`.** Today nothing compares the two. If the payload names a
  phase `season_config` does not expect, **every** label is NULL with that as the reason.
* 🛑 **`horizon is None` must fail CLOSED.** `phases.py:110`'s `if horizon is not None and …`
  currently fails open — `resolve_phase("2027-01-01…", w, None)` returns Phase 1.
* **`build_builds_db.py:192` crashes on that same state** — `f"(horizon {horizon:%Y-%m-%d …}Z)"`
  on `None`. **This is F5's exact crash class, reintroduced inside F8b's own code.** Fix it and
  add it to the F8b test.
* ⚠ **The child-phase precedent makes this worse and must be handled:** the server published
  its last content boundary (Phase 1.1, `phase_number: 2`) as a **child**, which
  `phase_windows` correctly drops. **A Phase 2 published the same way would be invisible to the
  resolver while `assert_phase()` still passes.** Decide what the resolver does when the live
  payload's top-level set has not changed but `season_config` says it should have — and make it
  refuse, not guess.
* **`gear_tier_stats(phase=…)` has no caller anywhere in the tree** (`core/builds/gear.py:372`;
  `grep -rn gear_tier_stats` outside `gear.py` returns only `primer/*.md`). Either route one
  real read through it, or state in `PROGRESS.md` that no phase-scoped read exists yet. Exit
  condition 10 of `3f` reads ✅ on a function nothing calls.
* **One number, stated two ways:** `gear.py:402,414` say **44.2%**; `gear.py:518` and
  `build_builds_db.py:44` say **38.6%**. Have the tool print it once and paste that.

**G0 lands FIRST and on its own commit**, before any arithmetic changes, so its gate pair is
trivially identical and the modelling commits start from a clean baseline.

---

## §0.8 — Owner decisions, taken 2026-08-07, before any result was seen

Implement; do not re-open. All three were asked and answered *before* this document was
finished, which is the point.

1. ✅ **`3g` is a modelling session: E13 first, then E14, then whatever the audit's §7 list
   still justifies.** Reason stated by the owner's choice and worth repeating in the session
   record: **every calibration number in this project is currently measured against a total
   containing a 78× error**, so fixing it is a precondition of trusting anything else.
2. ✅ **The 20% coverage floor on `within_tolerance` is DEFERRED until after E13 and E14 land**,
   then applied as **its own separate commit with its own before/after pair**, last. One cause
   per gate move. It is not applied first and it is not skipped.
3. ✅ **The holdout is read ONCE, at close-out, after both fixes.** Not after E13 alone. The
   standing rule as written.

---

## §0.9 — How to run unattended, and what to ask

**Ask your questions in your FIRST output, then proceed.** Do not hold work for an answer that
cannot arrive before morning. For each question:

* state the question,
* state the **default you are running on**,
* state **why it is reversible**, and
* add a row to `PROGRESS.md`'s "Blocked on the user" table.

🛑 **The one thing that is NOT reversible is a written row.** If a question is about what gets
written into `builds.db`, `prediction_outcomes`, or a committed manifest — **do not default.
Stop and leave it undone**, per `3f`'s stop-point 4. Everything in `3g` as scoped is code and
documents, both revertible; if that stops being true, that is the boundary.

⚠ **Two counts in `PROGRESS.md` disagree with each other right now** — `:77` says **six**
questions are waiting, the blocked table has **seven** new `3f` rows, and `3f`'s closing
statement said **eight**. Reconcile them against the table, or drop the numeral. It is the
standing rule's own failure mode (*where no tool prints it, the number has no owner*) sitting
in the live block a new chat reads first.

---

## Block A — the two magnitude explosions

**This is the session's purpose.** Both were found by F9's ground-truth assertion — the first
assertion in this harness that ever compared a modelled magnitude to a measured one — and both
survived `3e`'s five-defect sweep, three fixtures and a full adversarial audit.

### G1 — E13: every white swing is ~78× over. **Do this first.**

`AttackTable.probabilities()` returns **percentages** — its own docstring says *"probabilities
in percent, summing to 100"* (`core/sim/combat_engine.py:214-220`) — and `expected_swing`
multiplies by them **as fractions** (`core/sim/swings.py:159-163`):

```python
mean = base * (p.get("hit", 0.0)
               + p.get("crit", 0.0) * crit_mult
               + p.get("glancing", 0.0) * glance_mult)
```

**Why this one is first, and it is not just size.** It is **live inside the calibration gate**:
24 of the 36 scored cohort characters carry a melee auto in their top 5 sim abilities, and
**`Ari` — delta −9.7%, `Melee auto (MH)` its single largest modelled source — is one of the
gate's TWO qualified passes.** So at least one qualified pass is standing on a 78× error, which
means `3e`'s central conclusion (*"six mechanisms were repaired and the answer did not move,
therefore the residual is not in the mechanisms"*) **may be a large positive error cancelling a
large negative one.** An aggregate criterion is structurally blind to that; the qualified rider
was invented to catch it one level up; E13 shows the same hazard one level *deeper*, inside a
qualified pass.

**Required:**

* **Fix the unit, at the boundary, once.** Decide whether `probabilities()` returns fractions
  or whether every consumer divides, and make the docstring and the type say which. Do not
  patch the multiply site alone and leave a function whose name means one thing and whose
  values mean another — that is how this defect existed at all.
* 🛑 **Check every consumer of the same object before you change it.** `SwingOutcome` also
  carries `crit_pct` and `landed`, both built from the same percentages
  (`swings.py:163-164`). The auditor found no consumer of either in `core/sim/`, **but did not
  check `tools/`** — grep the whole tree and say what you found. A half-converted unit is worse
  than a consistently wrong one.
* **Report per-character attribution, not just the aggregate.** For all 36 scored: delta before,
  delta after, and the auto-attack share of modelled damage before and after. `Ari` gets its own
  paragraph — it is the case that decides how `3e`'s headline should be read from now on.
* **Say what happens to `3e`'s conclusion**, in the session record, in one direction or the
  other. If the residual is still not in the mechanisms after E13, that is a stronger result
  than before. If it moves, `3e`'s reading needs amending and a `RETRACTIONS` row — *prose is
  not a seed*.

### G2 — E14: 12,000 ticks per cast

`ability_model.py :: n_ticks` (`:890-895`) computes `round(duration / tick)` where the duration
comes from the **card** (Absolute Zero, 12.0 s) and the tick from the **triggered spell**
(0.001 s) — 12,000 ticks for one cast, 92.2% of the Frost Mage fixture's total damage.

**The 0.001 is a decode artifact**: `EffectAmplitude` of 1 (milliseconds) becomes 0.001 s, and
that record's own `duration_seconds` is *also* 0.001 — one application, not a 12-second channel
of millisecond ticks.

🛑 **Fix the general case, not this spell.** Per rule 2, a periodic event whose tick interval is
implausibly small, or whose tick and duration come from **different spells**, must **refuse and
warn** rather than produce a number. Special-casing `285149` leaves the next one live.

**And re-check the neighbours:** `ENGINE_BUGS` notes this is almost certainly
`sim_magnitude_explosion_absolute_zero`, the open question `PLAN_3C` raised against Mutaforma's
+3,619%. Once G2 lands, re-check that question's other members against this cause and resolve
or narrow it in `seed_epistemics.py`.

### G3 — re-run F9's ground truth, and report the number

The pre-registered ±25% assertion currently fails at **+6,427%** (90,202 modelled DPS against a
measured 1,382). After G1 and G2 the record predicts ~373 DPS against 1,382 — **−73%**, the
ordinary under-production family.

🛑 **Do NOT widen the tolerance.** It stays ±25%. If the assertion still fails — and it should —
it stays in `EXPECTED_FAILURES` **with its new number**. Record the before and after as
magnitudes, not as pass/fail.

⚠ **E13 and E14 currently share a single assertion** (`check_sim_engine.py:114-123`), so the
registry cannot tell which of the two was fixed, and its own *"registered + now PASSING → hard
failure"* rule is blind between them. **Split it before you fix either** — a per-defect
assertion each, plus the aggregate.

---

## Block B — the coverage floor, as its own move

### G4 — apply the stamped 20% floor to `within_tolerance`

Owner decision §0.8.2: **after** G1 and G2, in its own commit, with its own before/after pair.

It was stamped 2026-08-06 **before** the run that would test it, justified by slice-accuracy
stability (flat across ≥20/≥30/≥50, unstable below) rather than by a wanted number, and
`CALIBRATION_TOLERANCE.md:142` says it takes effect at the next gate. `3f` correctly neither
applied it early nor moved it. **`3g` is that gate.**

* Under it, the pre-`3g` run reads **2 of 36**. **The criterion is expected to FAIL.** That is
  the intended direction and must not be a surprise.
* 🛑 **The floor is not re-tuned in this session.** 20.0 is `SLICE_COVERAGE_FLOOR_PCT`
  (`calibrate_crawled.py:113`). Changing it after seeing G1's result is moving a gate after
  seeing its number.
* **Clear the attribution row** sitting in the blocked table: the floor is credited to the owner
  three times in `3e`'s record and is numerically identical to a constant Code chose and
  justified in its own voice. State which it was, plainly, in the session record. An
  unverifiable attribution on a gate criterion is worth two sentences now and an argument later.

---

## Block C — the instruments the audit found, and they are not cosmetic

`3f` adopted *"every check carries a registered test that makes it fail."* **That is half a
rule.** The audit found three checks that can never turn **green** — permanently red regardless
of the fix, closable only by a lie. `3g` is the session that fixes E9–E12, so this blocks the
work directly.

### G5 — give E9, E11 and E12 a green path, before fixing them

* **E12 — `check_sim_engine.py:770`** gates on
  `hasattr(T, "_roll_uses_combo_points")`. **That function exists nowhere in the tree** — grep
  returns that line only. So `rolled` is permanently `False` and the assertion reduces to *"the
  finisher's damage does not vary with combo points"*, which it does by design. Threading
  `combo_points` through `roll_hit`/`roll_cast` — **the actual fix** — leaves it red. **The only
  way to turn it green is to add a stub with that name.** Re-derive the assertion against a real
  property: roll at 5 CP and at 0 CP through `slow_sim` and compare against `medium_sim`'s
  skeleton.
* **E11 — `check_sim_engine.py:742-747`** calls `T._decay_target_health(st2)` and then asserts
  `st2.self_health_pct < 100.0`. That function touches only `target_health_pct`
  (`tiers.py:162-173`); the string `self_health` does not appear in it. Any correct fix leaves
  the assertion red forever.
* **E9 — `check_sim_engine.py:699-712`** re-implements the discriminator it is testing
  (`routed_as_debuff` computed locally from a hand-built `_FakeAb` whose
  `tick_interval_seconds` is `None`, so it is the constant `False`) instead of importing
  `tiers.py:583/635`. It only goes green on a **regression** in `_is_pure_periodic`. **This is
  the exact drift F3's own `_filler_ids` repair condemns** (`check_sim_engine.py:638-650`),
  rebuilt three functions later in the same commit.

🆕 **Amend the standing rule and write it into `CLAUDE.md` beside the current one:**

> **A defect check names BOTH mutations: the one that turns it red, and the change that turns
> it green. The green one must be the fix, not a stub.** A check that cannot go green is not a
> check — it is a permanent alarm, and it will be silenced rather than satisfied.

Add the green-path column to `ENGINE_BUGS`' check registry and populate it for **every**
registered defect, not only E9/E11/E12. Where you cannot name a green path, say so in the
registry rather than leaving the column blank.

### G6 — de-tautologise three arms

* **`check_gate_exclusion.py:163-167`** — `victim not in after_outside`. `outside = qualifying −
  cohort_ids` (`calibrate_crawled.py:280`) and `victim ∈ cohort_ids` by construction, so this is
  true for every value of `EXCLUDED_SNAPSHOT_SOURCES`, every `source`, every mutation. ⚠ **It
  was made unfalsifiable by the F1 rewrite that moved the victim inside the cohort** — the fix
  and the vacuity have the same cause, which is worth a line in the registry.
* **`check_gate_exclusion.py:130-134`** — both conjuncts guaranteed.
* **`check_sim_engine.py:980-984`** — `named = any("TargetAuraState" in w …)` where
  `EXECUTE_GATING_UNAVAILABLE` is appended **unconditionally** at `tiers.py:468,687`. F3
  correctly diagnosed the old `any("health" in w.lower() …)` as a constant `True` and replaced
  it with a different constant `True`. Only `decays` is falsifiable; the detail string reports
  `named` as if it were an independent result.

🛑 **The rest of `check_gate_exclusion.py` is sound and stays.** The exclusion, the drop-reason
and the control arm are all genuinely falsifiable, verified by the auditor by running them.
Repair the two arms; do not rewrite the file again.

### G7 — repair the mutation registry

* **M3 is stale, and it was invalidated by a fix in the same session.**
  `check_refusals.py:92-95` says deleting the `except RealmSeasonMismatch` around
  `crawl_phases()` turns three assertions red. **The auditor applied exactly that mutation: all
  four F0 checks stayed PASS**, because the pre-flight `api_get` + `assert_phase` block added in
  the same commit (`baseline_phase1.py:106-113`) refuses first. Only removing **both** handlers
  turns anything red, and it turns **four** red, not three. The guard is right; the row is
  wrong.
* **M2 is platform-conditional.** Deleting `config.ensure_utf8_stdout()` turns **nothing** red
  on Linux — CPython picks UTF-8 for a pipe on POSIX regardless. The code comment scopes it to
  Windows honestly, so the *(Verified 3f.)* is plausible where you ran it. **Mark the row
  `[Windows only]`**, because the monitoring chat audits on Linux and will see it pass
  unconditionally.
* **M7–M10 (5 of 16) cannot be run from a clean clone at all** — they need gitignored
  `data/derived/*.db`. *"Every row below was executed against the tree"* is unreproducible for a
  third of the registry, on an owner-gated path. **State the precondition on each row.** This is
  the primer's own standing practice — *a code path only a gated run exercises can stay broken
  while everything reports green* — applied to the registry itself.
* **`check_sim_engine.py` dies on a raw `sqlite3.OperationalError`** when the DB is absent,
  where `check_gate_exclusion.py:97-100` refuses with a message. **A guard that cannot run must
  say so.**

### G8 — the manifest's two remaining self-contradictions

* **Two different `scored` values ship in one file**: `calibrate_crawled.py:1211` sets
  `result.scored = len(tuning)` (36); `:1279` sets `cohort_definition.scored =
  len(tuning)+len(holdout)` (41). Both are in `gate_manifest_3e.json`, neither notes the other,
  and F6's assertions reconcile only the second. An auditor reading `"scored": 36` and
  `"scored": 41` gets the contradiction F6 exists to remove, in a different coat.
* **F6's two "REFUSE to write" assertions are arithmetic identities** (`:1355`, `:1361`) — given
  `_completeness_sql`'s `GROUP BY ep.character_id` (`:235`), no data condition can trip them.
  They **are** real regression guards on the caller's wiring, and I am not asking you to remove
  them. **Correct the claim** in `ENGINE_BUGS` and the `3f` record from *"refuse a manifest
  whose members do not add up"* to what they actually do.
* **`calibrate_crawled.py:1015`** truncates the exclusion list at `excluded[:40]` and prints
  "none" only when empty. **No silent caps** — print what was dropped.

### G9 — the two hand-typed counts, and make them self-printing

**Both are already wrong, within a day of being written, and neither is anyone's mistake — it
is what happens to a number typed into prose.** This is the standing rule's own failure mode,
sitting in the two documents a new session reads first.

* **`CLAUDE.md:166` says the `primer/` census is `13 / 32 / 0 / 6`.** Measured at `a87a140`
  it is **`14 LIVE / 34 HISTORICAL / 0 SUPERSEDED / 7 FINDING`** across **55** files, all of
  which carry a status line. Two documents landed — the `3f` audit and this work order — and
  the count went stale the same day.
* **`PROGRESS.md:77` says SIX questions are waiting**, the blocked table has **seven** new `3f`
  rows, and `3f`'s closing statement said **eight**. (Also named in §0.9 and Block D; fix it
  once, here.)

🛑 **Do not just retype them correctly — that buys one day.** `check_refusals.py` already walks
`primer/` for the F8c test, so it is the natural place to **emit the census**, and the blocked
table is countable from its own rows. Have a tool print both, paste the output, and say in each
document that the figure is generated. Where a count cannot be generated, **drop the numeral
and name the source** — *"the questions in the blocked table below"* is true forever.

⚠ **Then check for the third.** `grep` `CLAUDE.md`, `PROGRESS.md` and
`START_HERE_FOR_CODE.md` for any other bare count of something the tree contains. A number
whose only owner is a sentence is a number nobody is watching.

---

## Block D — close-out

Session record, `PROGRESS.md` pointer (**and reconcile that question count, §0.9**),
`ENGINE_BUGS.md` updated with green paths, final gate manifest, `RETRACTIONS` rows for anything
`3g` overturns.

**Report the gate pair for every commit, with its cause.** The headline is the size and
direction of the move and what it says about where the residual is — not the count itself.

### 🛑 Read the holdout ONCE, at close-out, after both fixes

Owner decision §0.8.3. Members `460, 461, 462, 463, 7661`, pre-registered, last read at `3e`'s
close-out (0 of 5, −45% to −98%, three carrying 27–69% coverage).

* Read it **after** G1, G2, G3 and G4 have all landed. Not between them.
* 🛑 **Pre-register what you expect before reading**, in the commit that precedes the read. The
  holdout's value is entirely that nothing was tuned against it; a prediction written afterwards
  is worth nothing.
* Record the result **unsoftened**, whichever way it goes. `3f` carried `3e`'s reading forward
  verbatim and stamped it with the commit that took it (`c7d2892`) rather than erasing it —
  keep that pattern, and stamp the new one the same way.

---

## Stop-points — ask, do not decide

1. 🛑 **Any change to the gate's definition beyond G4's stamped floor** — a cohort edit, a
   tolerance change, a second criterion. G4 is pre-approved; nothing else is.
2. 🛑 **If E13's fix moves the gate in the "better" direction** — more characters inside ±20%.
   Stop. That is the opposite of the pre-registered prediction and means something else changed.
   Report it before proceeding.
3. 🛑 **If G0's phase work would touch anything already written into a committed artifact** —
   the baseline folder above all. Refuse and report; that file is unrepairable.
4. 🛑 **If a fix in Block A requires changing a `ContentProfile` preset or a
   `retail_hypothesis` constant to make a number work.** That is fitting, not fixing.
5. 🛑 **Anything that would write a row into `builds.db` or `prediction_outcomes`.** Out of
   scope this session; a written row is the one irreversible thing here.

---

## Exit conditions

`3g` is done when all of these hold:

1. Every commit reports the gate before and after **with the cause of any move named**, and no
   commit moves it for two reasons.
2. **G0**: phase labelling asserts positively against `season_config`, `horizon=None` fails
   closed, `build_builds_db.py:192`'s `None`-format crash is gone and tested, and the
   child-phase case is handled or explicitly refused.
3. **E13 is fixed at the boundary**, every consumer of `AttackTable.probabilities()` and
   `SwingOutcome` is accounted for tree-wide, and the per-character attribution — including
   `Ari` — is recorded.
4. **E14 is fixed in the general case**, with a refusal-and-warning for implausible tick
   intervals and for tick/duration coming from different spells.
5. **E13 and E14 have separate assertions**, and F9's ±25% ground truth is re-run and recorded
   as a number, tolerance unchanged.
6. **The 20% coverage floor is applied in its own commit**, with its own pair, and the
   attribution question is answered.
7. **E9, E11 and E12 each have a named green path that is the fix**, the registry has a
   green-path column populated for every registered defect, and the amended standing rule is in
   `CLAUDE.md`.
8. **The three tautological arms are falsifiable**, and M3 / M2 / M7–M10 rows are corrected with
   their preconditions stated.
9. **The manifest ships one `scored`**, F6's assertions are described as what they are, and no
   list truncates silently.
10. **The holdout is read once, at close-out, against a prediction written beforehand.**
11. **Both hand-typed counts are generated rather than retyped** — `CLAUDE.md`'s `primer/`
    census and `PROGRESS.md`'s question count — each pasted from a tool with its provenance, or
    replaced by a phrase that cannot go stale. Any third one found by grep is listed.
12. Every new document carries a status line and an expiry condition at birth.

---

## Explicitly out of scope

* **Block C / `PHASE_3 T6`, the log-ingestion writer.** It stays spilled. Its remaining
  precondition is real — `parse_log.py` produces crit rates and avoidance and **no per-ability
  damage totals at all** — and it would write tier-1 rows measured against a sim that is being
  corrected in this very session. It goes after `3g`, not into it.
* **`PLAN_3G_self_verifying_gates.md`.** ⚠ **Name collision: that document is not this
  session.** It is still `LIVE` and unrun. Do not start it, and do not renumber it — amend its
  specimen list per `ADDENDUM_3E_to_3F.md` §3.1 only if you touch it at all. It now has four
  real specimens to formalise, which is an argument for running it soon, not now.
* **Back-filling the six `ContentProfile` presets.** They stay declared as assumptions. Third
  session running.
* **Touching `EXCLUDED_SNAPSHOT_SOURCES`, the frozen cohort, or the holdout slug.**
* **The caster buff layer (`3e` C3) and the dungeon `ContentProfile` (`3e` C4)** — both blocked
  on `calibrate_vs_log` running on a non-paladin log. Its refusal is fail-closed and correct;
  **do not weaken it to unblock them.**
* **E5's residual, E7, E8, E10** — registered, real, and each would move the gate. They belong
  to the session after this one unless E13/E14 land early and cleanly, in which case take them
  **one commit per defect** with the same pre-registration discipline, in the order
  `E10 → E7 → E8`. Never two in one commit.

---

## Standing rules — in force

* **Every coverage task reports slice accuracy before and after.** (`3d`)
* **The holdout is named before the work, not after.** (`3d`)
* **Every check carries a registered test that makes it fail — name the mutation, and RUN it.**
  (`3f`) 🆕 **Now extended by G5: it must also name the change that turns it green, and that
  change must be the fix.**
* **A magnitude never appears in a markdown file except as generated output, pasted with its
  provenance.** (`3f`) ⚠ `3f` broke this **three** times — 44.2% vs 38.6%, the
  six/seven/eight question count, and `CLAUDE.md`'s `primer/` census, which was stale within a
  day of being typed. **Every instance so far has been a count or a percentage a tool could
  have printed.** G9.
* **Every file in `primer/` carries a status line, and only `LIVE` documents are citable as
  current truth. A new document is born with one, and with its expiry condition stated.** (`3f`
  F8c, now in `CLAUDE.md`)
* 🆕 **Re-check that the tree has stopped moving before publishing a judgement about it.** The
  `3f` audit's own §5 was written against a mid-session HEAD and had to withdraw two findings.
  It applies to Code too: a session record written before the last commit describes a tree that
  no longer exists.

---

## One thing to hold in mind all session

`3e` fixed six mechanisms and the answer did not move. `3f` fixed no mechanisms and found two
errors bigger than anything `3e` touched — **because it built the first instrument that
compared a modelled number to a measured one.** The lesson is not that the sim is bad. It is
that **this project's error-finding rate is set by its instruments, not by its effort**, and the
one instrument that paid was the one that put a measured magnitude on the other side of an
equals sign.

So when G1 and G2 land and the gate gets **worse**, that is the session working. The number to
protect is not the count inside ±20% — it is the honesty of the pair that produced it.
