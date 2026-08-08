# SESSION `3N` PRIMER — the APL clock fix, the first coefficients, and delivery's opening

> **`LIVE`** — the work order for session `3n`, drafted 2026-08-08 (afternoon) from
> `AUDIT_3M_ADVERSARIAL.md` (§5 is the source list). **SUPERSEDED BY
> `primer/Session_<date>_3n_*.md` when `3n` closes** — mark it in the close-out
> commit, not in a later cleanup.

**Audit implemented:** `primer/AUDIT_3M_ADVERSARIAL.md` (landed at `3n` pre-flight).
**Previous session record:** `primer/Session_2026-08-08_3m_repair.md`.
**Monitoring primer:** `primer/CHAT_MONITORING_PRIMER.md` (v9, written with the audit).

---

## §0 — The rules

🛑 **`3n` is a MODELLING session with one repair at its head.** The APL clock fix is
the largest single measured modelling error left (18% of Blix's sim, 15 of 41 members
exposed), and it is the first change in the arc whose *cohort-wide direction is not
known in advance* — which makes the symmetric-falsifier rule load-bearing, not
ceremonial.

1. **No commit that can move the gate lands without a pre-registration that is its
   commit-parent.** A falsified prediction is reported, not rescued. An unexpected
   move is a finding: stop, commit the pair with its cause, no retroactive prereg.
2. **A quoted baseline must exist as a COMMITTED artifact derived from the current
   tree.** Rebuild, regenerate, commit, *then* predict.
3. **No prereg may carry a one-sided falsifier.** State the predicted direction per
   member/mechanism; keep the falsifier symmetric.
4. **Every mechanism ships with a registered mutation — run RED and GREEN, and the
   mutation must be one someone might actually have written** (M60's isolating
   pattern; M68's crash-is-not-the-behaviour lesson). **M70+ are yours.**
5. **Publish the same-member number beside every published median.**
   `slice_delta_vs_previous_run` does this automatically now — quote the pair
   wherever either appears. It bites the producing median too (`3m` B watched it
   rise while nothing got more accurate).
6. **No coefficient is fitted to the parse it must later check.** What you cannot
   build from provenanced data is a **named refusal**.
7. **Never quote coverage as progress toward the gate.**
8. 🆕 **A CORRECTION'S BLAST RADIUS INCLUDES ITS SIBLINGS** (`AUDIT_3M` F1/F2, and it
   is the session's headline lesson). `3m` corrected the aura-344 seed in
   `seed_confirmed.py` and left the same falsified claim standing in
   `seed_epistemics.py:181` — the exact line `AUDIT_3L` F5 had named. It reconciled
   seed 103 with the code and left the `2b` ALL_EFFECTS seed twenty entries down
   asserting the opposite. **When you correct a fact, grep the tree for its siblings
   before you commit** — other seeds in the same file, the second seed file, registry
   rows, prose restatements.
9. 🆕 **A HAND TALLY IS A MAGNITUDE WITH NO OWNER** (`AUDIT_3M` F3). `3m`'s "13 of 15
   predictions confirmed" reproduces from no committed artifact (direct count over
   the three scored prereg tables: **20 predictions — 17 confirmed / 2 falsified /
   1 split**). Quote per-block counts read straight from the scored tables
   (`B 4✓·2✗·1 split — C 7/7 — D 6/6`), never a summed headline; if a single number
   is wanted, a tool prints it.
10. **The holdout stays unspent** unless the owner explicitly spends it. At 0 passers
    there is nothing for it to validate.
11. 🆕 **THE MONDAY SPLIT IS LIVE FROM 2026-08-10.** The frozen cohort stays pre-fix
    (owner decision, `3m`). Any capture or crawl parse of a hybrid-Cleave character
    taken from 10 August onward is **not comparable** to the cohort or to any pre-fix
    artifact until the date-aware handling (Block E1) lands. Check the date of every
    input before comparing.

---

## Pre-flight — cannot move the gate; one commit (plus its own for anything that
touches a check)

1. **Land the cycle documents**: `primer/AUDIT_3M_ADVERSARIAL.md` (born `FINDING`),
   the v9 monitoring primer (in place — never a versioned sibling), and this file —
   **regenerate `CLAUDE.md`'s census in the same commit** (`py
   tools/audit/check_refusals.py`, paste the `[census]` line), or `[A4]` fails at
   your first commit.
2. **`AUDIT_3M` F1 — finish C3's blast radius.** `seed_epistemics.py:181` still says
   aura 344 *"is the per-hit damage parameter … underived"*. One sentence: aura 344 =
   flat attack power (+73/weapon at rank 6, `3m` C3); the per-hit term is effect 0
   with divisors 77/25, *stated*; keep the delivery-question half of the entry open —
   that part is real and is Block D's.
3. **`AUDIT_3M` F2 — annotate, don't delete.** `seed_confirmed.py`'s
   `improved_cleave_modifies_all_effects_not_just_the_flat` correctly describes the
   **pre-2026-08-10 delivered** behaviour; stamp it as exactly that (dated), pointing
   at `improved_cleave_true_magnitude` for current truth. Fix
   `frostbound_cleave_identified_for_winds_of_winter_stack`'s formula citation — it
   still carries `(9+AP)*2.2` and predicted hits derived from the retracted
   magnitude.
4. **`AUDIT_3M` F4** — ENGINE_BUGS M63's site is wrong: `WEAPON_SLOTS` lives in
   `tools/audit/calibrate_crawled.py:207`, not `core/sim/tiers.py`. One line.
   (Measured: the registered edit applied to `tiers.py` is a no-op and the harness
   stays green — exactly the false comfort the table exists to prevent.)
5. **`AUDIT_3M` F3** — append the tally correction to the `3m` record (it is
   `HISTORICAL`; append, don't rewrite) and correct `PROGRESS.md`'s top block to the
   per-block counts. Same pass: "58.83%" has no committed emitter — either quote the
   artifact's 58.8 or make `per_ability_accuracy.py` emit 2 dp and quote that.

---

## Block A — baseline (short: the instruments already exist)

Rebuild `builds.db` from the current tree, regenerate `gate_manifest_3e.json` and
`per_ability_summary.json`, commit. Every later prereg cites this artifact. Cite the
`[arms]` line, clean tree. Expected unchanged from `3m`'s close:
`0 / 0 / 30.040 (n=24)`, absent 58.8, producing 0.3234 (n=117) — **if anything moved,
stop: that is a finding, not a baseline.**

---

## Block B — 🚨 THE APL CLOCK FIX (the headline; own prereg pair)

**The mechanism, measured in `3m` §9:** `apl_gen` ranks cooldown-less fillers by
expected damage **per cast** across abilities whose cast **rates are governed by
different clocks** — `is_next_swing = 1` abilities (the Cleave family, Heroic Strike,
Light Maul, Shadow Slash — 11 of the cohort's 530 ability ids) are rate-limited by the
weapon swing timer, while ordinary fillers are GCD-limited. `fast_sim` then gives the
top-ranked filler the entire remaining GCD budget. On Blix that misranking dropped
Lightbound Cleave from the rotation entirely (−100% instead of the predicted −39.84%)
and cost **18%** of his simmed damage. ⚠ `3m`'s first diagnosis (per-cast vs
per-GCD-second) was **wrong** — a cohort sweep found 0 disagreements because
`_gcd_for` returns one GCD per character. Do not re-inherit it; the units mismatch is
the mechanism.

**B1 — prereg first.** Cohort: the 15 of 41 members holding both a next-swing ability
and GCD fillers. Predict per-member direction (not every member moves the same way —
a next-swing ability re-entering the rotation can displace a filler). Predict the
producing median and slice move, **published and same-member**. Symmetric falsifier.
State what is NOT predicted (per-member magnitudes beyond Blix's measured case are
estimates, say so).

**B2 — the fix.** Design constraint rather than prescription: a next-swing ability's
casts are bounded by the swing timer, not the GCD budget, so it must not compete for
GCD allocation on per-cast damage — and its expected damage must be scored on the
clock that actually limits it. Acceptance: Blix's Lightbound Cleave returns to his
rotation; no next-swing ability consumes GCD budget; the cohort sweep that caught the
wrong diagnosis re-run as a check.

**B3 — mutations (M70+).** RED: restore per-cast ranking across clocks (the exact
code `3l`/`3e` wrote — a mutation someone did write). GREEN: the fix. Run both.

**B4 — pair commit, scored.** If the gate moves in a direction the prereg did not
name, that is a finding — stop and commit the pair with its cause.

---

## Block C — E2: `infer_coefficient` on real per-parse stats (THIRD carry — land it
or it needs a fresh owner stamp)

The windowing is landed (`core/logs/encounters.py` — kill GUID explicit, ambiguity
refuses, wall vs logged both reported). All six Elric MC stat blocks are
phase-resolvable. This is the T5 unblock for `refused:no_per_parse_stats`
(`core/builds/inference.py:350`), gating **Phase 3 criteria 3-full and 4**.

**C1 — own prereg**: which refusals may convert to verdicts; falsifiable
expectations; what is NOT predicted. 🛑 Divide damage by **logged** seconds, never
wall (Gehennas: 320.1 logged inside a 379.8 wall — the crash gap is real).

**C2 — seed discipline.** The owner's `3m` scope decision stands as precedent:
**no seeding in a session's tail.** Derive early; anything derived late is written as
a finding for `3o` to seed at its head. Whatever verdicts land, update
`seed_confirmed.py` **and grep for siblings in the same pass** (§0 rule 8).

---

## Block D — delivery modelling's opening (owner decision: in `3n` if B and C leave
room, else `3o` whole)

Absent mass is **58.8%** and dominated by trigger-delivered damage. If pulled in,
own prereg, and start with the two items whose formulas are *stated by the client*
rather than underived:

1. **Imbue per-hit** — effect 0, divisors 77/25, rank from
   `snapshot_gear.enchant_id`; and model the **+73 raw AP per weapon** grant (seeded
   `3m` C3, unmodelled). The ×1.21 residual against `2e`'s observed +88 stays a named
   finding — do not fit it.
2. **Seal per-proc (20424)** — 35% weapon, Holy, delivery-blocked not
   extraction-blocked; proc rate measured `2e` (~0.25/melee event).

Carried behind those: Plague Swarm 276445 (146× gap), school-variant and extra-attack
autos, Deep Wounds / Ignite / diseases.

**Devour Mind 287865 (6.63%, the largest single absent key) is at its FOURTH
deferral.** This session it gets a registered `open_questions` row with a named
blocking reason, or it gets modelled — a fourth bare "carried, unchanged" line is not
an option.

## Block E — the Monday split, date-aware

**E1** — the B-prereg-named refinement, deferred under the deadline: apply the
Improved Cleave whole-ability impairment only to parses dated **before 2026-08-10**
(the `SYSTEM_IMPAIRMENTS`-style record from `3m` B1 carries the `fixed_on` date).
Required before any post-Monday capture or crawl parse of a hybrid-Cleave character
can be compared to anything pre-fix. If the owner takes a post-Monday capture this
session, E1 lands **first**.

---

## Standing decisions needed from the owner — ask at session START

1. **Delivery modelling: opened in `3n` (Block D as scoped) or deferred whole to
   `3o`?**
2. **E2 runs in `3n`** — if it is to be carried a third time instead, that carry
   needs its own stamp.
3. **Holdout:** unspent by default.
4. **Predicate 2 (deaths > 0):** stays UNARMED by name unless stamped.
5. **Post-Monday captures:** none compared to pre-fix artifacts until E1 lands. When
   is the first post-fix capture planned? (It is also the free detector for the
   server fix actually landing as stated.)
6. **Improved Cleave reset:** the toolkit's verdict stands (74.4/hit at 3/3 on The
   Light's Hope) — does the owner want a chase-list re-rank written up once B/C land?

---

## Close-out (its own commit, per the established pattern)

Session record `primer/Session_<date>_3n_*.md` (born `HISTORICAL`) with the §0
commit-by-commit gate table and the prereg→code parent pairs; per-block prediction
counts quoted **from the scored tables** (§0 rule 9); `PROGRESS.md` top block
replaced, `3m` block collapsed; **this file marked `SUPERSEDED BY` the record**;
final gate manifest from a clean tree; all three harnesses run and exit codes cited
(the **clean-tree** arm count is the citable one); census regenerated in every commit
that touches `primer/`; the published + same-member pair quoted together wherever
either appears; the honest NOT-done list.

## What `3n` should hand to `3o`

An APL that ranks on the right clocks, with a mutation behind it; the project's first
per-parse coefficients (or a stamped, named refusal per blocked input); a gate whose
remaining error is demonstrably delivery; Devour Mind registered or modelled; the
Monday split handled by date rather than by memory; and zero seeds asserting a
falsified fact — checked by grep, not by recollection.
