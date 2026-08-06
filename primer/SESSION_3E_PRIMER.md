# SESSION `3E` PRIMER — modelling, on a frozen cohort

**Work order for Claude Code.** Written by the monitoring chat 2026-08-06 evening,
against a fresh clone at `91d8f92`, after `3d` closed. Read this first, then
`primer/ENGINE_BUGS.md`, then `primer/FINDINGS_3e_preflight_2026-08-06.md`.

Predecessors: `primer/Session_2026-08-06_3d_hygiene_and_instrument.md` (what `3d`
did), `primer/AUDIT_3C_ADVERSARIAL.md` (still the reference for what is broken),
`primer/ADDENDUM_3D_slice_accuracy_correction.md` and
`primer/ADDENDUM_3D_to_3E_mage_capture.md` (both are `3e` input, both still
unlanded).

---

## §0 — The ordering rule, and the one thing that cannot be got wrong

`3d` was scoped so the gate could not move. **`3e` is the opposite: the gate is
supposed to move.** That makes the ordering the invariant instead of the number.

> 🛑 **Block A lands first, on its own commit, before a single modelling change.**
> Block A stamps the cohort and repairs the instrument. Every commit after it
> reports the gate **and cohort median slice accuracy above a stated coverage
> floor**, before and after, against the frozen 41. A modelling commit that does
> not carry a before/after pair is not finished.

**Owner decision, 2026-08-06 — settled, do not re-open.** The cohort is **frozen
to the 41 `character_id`s already recorded in `predictions/gate_manifest.json`**.
Not a sliding window, not `LIMIT 120`, not "whoever qualifies today". This was
chosen **before** the next gate result was seen, which is the whole point —
`CALIBRATION_TOLERANCE.md`'s closing rule.

Two consequences to write down now rather than discover later:

* The frozen cohort **goes stale**, by design. It is a fixed benchmark, not a live
  measure of the realm. When it is replaced, that is a **new manifest with a new
  name and a stated reason**, never an edit to this one — same discipline as the
  holdout slug.
* Characters that enter the corpus after today are **invisible to the gate**.
  That is acceptable while `3e` is measuring whether fixes generalise. It is not
  acceptable forever, and `PHASE_3`'s "≥3 distinct characters" exit still has to
  be met on a cohort someone can defend.

**Scope, per owner decision:** `3e` = **Block A + Block B + Block C**. Block D is
close-out. If the session runs long, **whole blocks spill to `3f`, never half a
block** — a half-fixed E1/E5 pair is worse than an untouched one, because the
masking relationship between them is what makes the failures readable.

---

## Block A — make the gate readable (no modelling, one commit)

**A1 — Freeze the cohort.**
`candidates()` (`tools/audit/calibrate_crawled.py:130`) currently ends
`ORDER BY ep.character_id LIMIT ?`, which `3d` proved is a sliding window keyed on
an arbitrary id: the population grew 157 → 180 and the gate went 5-of-41 →
4-of-38 with zero code changes.

Replace the limit with an explicit id set loaded from the manifest. Requirements:

* The cohort file is **data, not a constant in the tool** — the tool reads
  `predictions/gate_manifest.json`'s `cohort[].character_id`.
* A character in the frozen set that **no longer qualifies** (snapshot lag, gear
  rows, level) must be reported as *dropped, with the reason*, not silently
  omitted. A cohort that quietly shrinks is the same defect wearing a different
  coat.
* A character in the corpus but **not** in the frozen set is not scored at all,
  and the count of such characters is printed. Silence there would read as
  "everyone was measured".
* 🛑 The `EXCLUDED_SNAPSHOT_SOURCES` filter (`3d` F1) stays exactly as it is. It
  excludes owner-captured snapshots by `source`, which is why the incoming Mage
  fixture is excluded automatically. Do not weaken it to "except the Mage".

**A2 — Land the slice-accuracy correction.**
`predictions/CALIBRATION_TOLERANCE.md:154` still reads *"the modelled slice is
over-produced by about 60%"*. It is **backwards** — the median is a low-coverage
artifact, and `slice_accuracy = (100 + delta) / coverage` explodes as coverage → 0
(Mutaforma: 0.2% coverage, slice accuracy 1,859,400%; that value is in the
committed manifest). Restricted to coverage ≥ 20% the median is **62.6%**, stable
across ≥20 / ≥30 / ≥50 bands. **The sim under-produces on what it models, by ~37%.**

Three edits, per `ADDENDUM_3D_slice_accuracy_correction.md`. The durable one is
the second: `calibrate_crawled.py` must report the cohort median **only above a
stated coverage floor, and print the floor beside it**, plus the per-band table.
`gate_manifest.json`'s `cohort_median_slice_accuracy_pct` needs the floor in the
key name or an adjacent field, or two readers will read it two ways.

⚠ **This inverts an instruction `3e` would otherwise follow.** Under the 159.8%
reading, coverage work overshoots and should be throttled. Under 62.6%, coverage
alone can *never* reach ±20% — landing `delta = 0` at slice 0.626 needs coverage
> 100%. Both levers have to roughly double. Land A2 before any coverage task is
prioritised.

**A3 — Give `within_tolerance` a coverage floor, or make it say it has none.**
`calibrate_crawled.py:494` is `abs(delta) <= AGGREGATE_TOLERANCE_PCT` with no
other term. Three of the five characters carrying the criterion sit at 4.6%, 5.6%
and 13.3% coverage, and three cohort members have **0.0% coverage with a non-null
delta** — the sim produced DPS mapping to none of what they logged. A character
the sim models nothing for can score a pass.

Minimum acceptable fix: `within_tolerance` reports **`None`**, not `False`, when
coverage is 0 or absent — the same treatment slice accuracy already gets at
`:535-537` — and the headline prints the coverage distribution of the passers.
🛑 **Raising the floor above zero changes the criterion, so it is an owner
decision, not a code decision.** Report; do not decide. See §"Stop-points".

**A4 — Split the holdout out of the headline.**
`HOLDOUT_IDS` (460, 461, 462, 463, 7661) exists only in
`ingest/export/seed_predictions.py:195`. `calibrate_crawled.py` has never heard of
it, so the five are counted in "n of 41" — meaning any fix that lifts them moves
the headline **and** spends the holdout in the same number. Report two lines:
tuning set (36) and holdout (5), the holdout read **once, at close-out, after all
modelling is done**. The set itself is immutable; if it must change that is a new
slug with its reason.

**A5 — Land the cast-time cohort measurement.**
Drop `primer/FINDINGS_3e_preflight_2026-08-06.md` and
`predictions/cohort_cast_time_2026-08-06.md` in as-is. They answer thread 1's
cheapest question (**Boomcat is not a cast-time caster — the retraction stands**)
and they size its blast radius (**22 of 41 cohort characters carry ≥3 cast-time
combat abilities**), which C2's admissibility filter must be designed against
rather than on the Hammerdin.

**A6 — Fix `ADDENDUM_3D_to_3E_mage_capture.md` §1's field table.** It names
`MeleeHaste_total` / `SpellHaste_total`; the shipped addon (`2026-08-06c`) calls
them `MeleeHaste_raw_UNVERIFIED` / `SpellHaste_raw_UNVERIFIED` and explicitly does
not trust them (`.lua:197-209`). Also clear `PROGRESS.md`'s "⚠ OWNER ACTION
OUTSTANDING" — the addon landed at `9486283`. And fix `ENGINE_BUGS.md`'s E6
citation (`calibrate_crawled.py:70,426` → `:73,465,469`) and
`ADDENDUM_3D_to_3E_mage_capture.md` §2's "weapon speed is hardcoded at 3.57",
which `3d` fixed. **All three are the same defect this project calls its most
expensive: a document that stopped matching the tree.**

---

## Block B — the six engine defects

All six are registered `EXPECTED_FAILURES` in `tools/audit/check_sim_engine.py`
and documented in `primer/ENGINE_BUGS.md`. The registry is enforced **both ways**:
a registered check that starts passing fails the harness until its entry is
closed. Close entries as you fix them.

🛑 **Do not repair a failure by weakening its assertion.** `3d` shipped failing
tests that name real bugs; turning them green by softening them destroys the only
instrument that found them.

**B1 — E6 first, and alone on its commit.** `core/sim/tiers.py:140` sets
`gcd_budget = 0.0` after the first filler, while the comment at `:138` says
*"fillers split whatever budget the cooldowns left, in priority order"*. The code
does not do that. **This is the tier the calibration gate runs on** — `fast_sim`
is imported at `calibrate_crawled.py:73` and called at `:465` and `:469`
(⚠ `ENGINE_BUGS.md`'s own citation of `:70,426` has drifted; fix it in A6) — so
fixing it moves every character at once. Put
it on its own commit with the full before/after so the movement is attributable.
Its current check passes and is too weak to bite (it counts abilities that did
*any* damage); write one that fails on the real behaviour first, watch it fail,
then fix.

**B2 — E4 next, because E5's proper fix is not expressible without it.**
`core/sim/apl.py:19-32` is a closed `CONDITION_TYPES` set with **no target-debuff
or DoT-uptime condition at all** — `buff_active` / `buff_missing` track the
*player's* buffs. Add a target-debuff condition (`debuff_missing` /
`debuff_remaining_below` or equivalent) so "re-cast when the DoT is about to
expire" can be written down.

**B3 — E5, and expect E6's sibling to appear.** `core/sim/apl_gen.py:59-63`
prioritises off-GCD, then cooldowns longest-first, then fillers by damage per
cast — so a DoT with no cooldown is filed behind **every** cooldown ability. On
the DoT-caster fixture, 6 of 7 DoTs cast **zero** times over 75 s. Fixing this
will very likely surface the predicted re-cast-every-GCD bug, which currently
reads clean **only because the DoTs never cast**. The re-cast check must not be
read as green until E5 is fixed; it carries that caveat in its own failure text.

**B4 — E1, in two steps and in this order.** `is_finisher` at
`core/sim/apl_gen.py:50-51` is `any(t.get("cp_scaling") for t in ab.damage_terms)`
— and on a real combo-point board it classified **none** of the four abilities
carrying a genuine per-combo term as finishers, so zero APL entries are CP-gated
and the finishers cast freely as ordinary fillers. Fix detection **first**. Only
then does `combo_points` (`core/sim/tiers.py:197`, incremented nowhere in the
tree) become reachable — at which point the *original* audit bug starts biting.
Incrementing combo points alone fixes nothing, and a naive "does a finisher ever
cast?" check would have passed while both bugs were live.

**B5 — E2.** `core/sim/tiers.py:198-199` pins `self_health_pct` and
`target_health_pct` at 100.0. Execute-gated abilities are therefore modelled as
**always available** — Hammer of Wrath cast 9 times at a pinned 100% target
health, with zero APL entries carrying a health condition and no warning
mentioning health. The failure is not "it never casts", it is that the window is
unmodelled **in either direction and the sim does not say so**. Naming it in
`warnings` is the floor; modelling target-health decay is the fix.
⚠ Note for the Mage fixture: the capture's dummy is an **Execute** training dummy,
so it carries this caveat too (capture README caveat 3).

**B6 — E3.** No pet model exists anywhere in `core/sim/`, while
`core/builds/corpus.py:614` computes `dps = (total_damage + pet_damage) / duration`.
Pet-carrying builds miss low against a number that includes pets, silently. The
Mage capture measures the real share directly: **5.0% unbuffed, 5.4% buffed, 1.5%
in the dungeon** (Lesser Water Elemental) — use those as the sanity check on
whatever model lands. Owner decision 2026-08-06 was already "model pets".

---

## Block C — the Mage

**C1 — Land `--stat-block`, and land it before anything derives a number.**
⚠ **Correct the addendum's premise first.** §2 says weapon speed is hardcoded at
3.57 with no flag — `3d` fixed that: `calibrate_vs_log.py:429-442` now exposes
`--ap --sp --weapon-min --weapon-max --weapon-speed`, all `required=True`. So
F2 shipped as written and this is **additive work, not a rework**.

What has *not* changed is the reason to do it: **five hand-typed numbers is still
a hand transcription of a ~40-line export, and the other ~35 fields are still
discarded.** No stat-block parser exists anywhere in the repo. That channel is
what produced the contamination `2e` spent a session undoing; making the flags
mandatory made the transcription compulsory, not correct. Per
`ADDENDUM_3D_to_3E_mage_capture.md` §2:

```
py tools/audit/calibrate_vs_log.py --stat-block <path/to/stat_export_*.txt> <log>
```

* Parse the export directly. Keep `3d` F2's refusal semantics — refuse to run
  without a block, never default silently. Do not introduce fresh defaults.
* Demote `--ap`/`--sp`/`--weapon-*` from required inputs to explicit **overrides**
  for what-if runs, and print loudly when an override disagrees with the block.
* Free wins: weapon speed stops being hardcoded; per-school SP and crit replace
  one blended `--sp`; `ExportedAt` lets the tool **warn when the block and the log
  are from different sessions** — the single error `2e` proved is worth more than
  all the others combined.
* ⚠ `ManaRegen_raw` is deliberately unconverted (`GetManaRegen` is per-second, the
  character sheet is per-5). **Establish the unit before consuming it.** Same for
  the `*_raw_UNVERIFIED` haste fields — the addon does not trust them and neither
  should the parser.

**C2 — Add the Mage fixture, run `check_sim_engine.py`, record what fails.**
Frost Mage, Path of Intelligence, verified stat blocks, paired logs, real parses:
it exercises cast-time filler ordering, mana as a binding constraint, and channels
— three gaps a Hammerdin structurally cannot reach. Expect new failures; register
them, do not fix them in the same commit.
⚠ **`is_channeled` is resolved into the DB at `core/spells/mechanics.py:275`
(column at `core/db/schema.py:340`) and `grep -rn is_channeled core/sim/` returns
nothing** — so the sim never reads it, and a channel costs one GCD while
delivering all its ticks. Verified 2026-08-06, not inherited. Check
whether the captured rotation contained one before reading anything from it.
Both `3d` fixtures stay: Frost is burst, not DoT, and has no combo points.

**C3 — Measure the caster buff layer, per ability, from the durable quantity.**
🛑 **Not from the A→B DPS ratio.** Windows A and B are unequal length (214.2 s vs
179.9 s) and are not the same rotation (Ice Lance 3.4 → 5.0 casts/min; Innervate
and Cold Snap appear only in B). The capture README names the durable quantity
itself: **per-hit non-crit averages**, A→B — Frostbolt ×1.027, Icicle ×1.003, Ray
of Frost ×0.940, Waterbolt ×0.994, Frozen Orb ×1.070, Frost Fever ×1.080.

The buff barely moves per-hit damage, against the paladin's ×1.45 — consistent
with **Arcane Intellect alone** being applied. That is a finding, not a
disappointment: it is direct evidence against a blended constant, on a second
kit. Per-ability, never a single number — `2e`'s Righteous Vengeance at ×3.18
against a ×1.45 core is what proved that.

**C4 — Derive the dungeon `ContentProfile`, with the confound marked.**
Owner decision 2026-08-06: derive it now rather than wait for a re-capture.

The buff confound I originally raised is **resolved, not merely accepted** —
`FINDINGS_3e_preflight_2026-08-06.md` §3 shows from the log itself that every
external buff in Window C is armour, healing, mana regen or attack power, that
Arcane Intellect was already present in Window B, and that the only pre-existing
auras were Arcane Brilliance (same grant as AI, does not stack) and Commanding
Shout (stamina). **No buff present in C and absent in B raises Elric's spell
damage.** The stat block therefore applies.

🛑 **The blocker that remains is segmentation, and it is hard.** Window C mixes
boss and trash pulls (capture README caveat 4), and **target count and fight
duration are exactly what a `ContentProfile` encodes**. Split C into
`boss_single` / `trash_bundle` scopes first. Deriving from the unsegmented window
produces an average of two different fight shapes wearing the word "derived".

Then, and this is the part that matters:

* Stamp its provenance **`derived`, with the evidence ref**, and record the
  segmentation basis in the same string.
* Mark it **not promotable** until a second dungeon capture reproduces it — one
  run of one dungeon by one character is a measurement, not a distribution.
* 🛑 **Leave the other six presets declared as assumptions.** Criterion 7 is
  *failed* rather than merely unverified precisely because invented values were
  carried as if they weren't. Do not back-fill by analogy.
* ⚠ This makes the Mage a valid second verified character **for its own content
  profile**. It is not a raid boss, and the gate cohort is not dungeon content —
  so it is not a third of the raid-side exit.

**C5 — F2b, still the urgent half.** `PHASE_2_simulation.md:470` states 1.718 and
0.769 as *"the targets a talent model must reproduce"*, and **both were computed
from the wrong stat block**. Re-derive them through C1's parser. Anything built on
those two numbers inherits the contamination.

---

## Block D — close-out

1. Gate run against the frozen 41, with the coverage-floored slice median, tuning
   set and holdout reported separately.
2. **Read the holdout once**, now, and record the reading whatever it says. If the
   fixes generalised, some of 460/461/462/463/7661 improved without ever being
   looked at. If they did not, that is the most informative result of the session
   and must not be softened.
3. Session record in `primer/`, `PROGRESS.md` pointer, new gate manifest under a
   new name (the frozen one is immutable).
4. Re-read `PHASE_3`'s seven exit criteria **honestly**, one line each, and say
   which moved. Four were unmet, one unverifiable, two met.
5. Add a `PROGRESS.md` pointer to **`primer/PLAN_3G_self_verifying_gates.md`** — a
   candidate session written 2026-08-06 that generalises the fail-open-instrument class
   (`check_alignment()` vacuous off-Hammerdin, the extract wrapper's "game is closed"
   check, slice accuracy at 1% coverage, `within_tolerance` with no coverage floor).
   🛑 Its position relative to `3f` is an **open owner question**, stated in the doc:
   `3f` builds a writer from logs into `builds.db`, and gates exist to stop bad numbers
   reaching a database — so there is a real argument for gates first.

---

## 🛑 Stop-points — ask, do not guess

1. **A3's coverage floor.** Adding a floor to `within_tolerance` changes the
   criterion. Report the distribution; let the owner set the number — after
   seeing the distribution but stamped before the next gate run.
2. **The Holy Shock coefficient.** `3d` left open whether `calibrate_vs_log`
   should **substitute** the independent 0.2145 rather than report it beside the
   back-solved 0.40. Substituting changes a calibration number. `3d` reported.
   Unchanged unless the owner says otherwise.
3. **`bugs/` vs `primer/ENGINE_BUGS.md`.** `SESSION_3D_PRIMER` D3 said file engine
   defects in `bugs/`; `bugs/README.md` says that folder is game bugs only. The
   repo won. Moving them is a `git mv` and a README edit if the owner prefers.
4. **Any pet model beyond "name the gap"** is a modelling decision with a ~5%
   (dummy) to ~10% (cohort) magnitude. Propose, then land.

## What `3e` must not do

* Must not touch the frozen cohort's membership. If a member stops qualifying,
  report it; do not substitute.
* Must not tune against 460, 461, 462, 463, 7661, or read them before Block D.
* Must not fix E1 or E5 halfway — the masking relationships are the instrument.
* Must not turn a failing check green by weakening it.
* Must not carry a derived-from-one-run `ContentProfile` as if it were a
  distribution, and must not back-fill the other six presets by analogy.
* Must not report a gate number without the coverage floor beside the slice
  median. A ratio with coverage in its denominator, aggregated across characters
  spanning 0.2% to 82% coverage, is not a measurement.

## 🚨 Time-critical, independent of everything above

**The server flips to Phase 2 on 2026-08-08.** `3d` centralised the season/realm
constants and made the crawl hard-fail on a stale phase, **but nobody has seen it
fire.** On the 8th, check that the flip was detected and that
`gear_tier_stats.phase_label` stops being NULL. If `3e` is running on the 8th,
this takes precedence over whatever block is open.
