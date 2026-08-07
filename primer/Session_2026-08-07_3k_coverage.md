# Session `3k` — the phase flip, and coverage's first honest lesson

> **`HISTORICAL`** — the record of session `3k`, 2026-08-07 (evening).
> **May contain claims that are false today, and that is correct.** Work order
> it ran: `primer/SESSION_3K_PRIMER.md` (now `SUPERSEDED BY` this file). Audit
> it implemented: `primer/AUDIT_3J_ADVERSARIAL.md`.

**In one line:** the Molten Core boundary landed in a shape with no protocol
and would have NULLed the corpus indefinitely; that is fixed and cost the gate
nothing. Coverage moved **62.9% → 59.9% absent** on one target — and the run
falsified two of its own five predictions, including the one that assumed
coverage buys accuracy.

---

## §0 — Commit by commit, with the gate at each

| commit | what | gate after |
|---|---|---|
| `b2ad6c1` | pre-flight: `AUDIT_3J_ADVERSARIAL.md`, `SESSION_3K_PRIMER.md`, v6 monitoring primer **in place**, `CLAUDE.md` census refreshed in the same commit | *(not run)* |
| `e803275` | **B0 prereg** — the live payload verbatim; P1 registered and unmeasured | *(not run)* |
| `9d29028` | **B0 code** — current phase = latest-starting active top-level; M50/M51 | 0 / 0 / 26.3% (n=23) |
| `e86cb2a` | **B0 result** — isolated pair, no move; P1 falsified as written | 0 / 0 / 26.3% (n=23) |
| `57e844f` | **Block A** — boundary line retired, Phase 3 exit fossil corrected, 7 criteria annotated | unchanged |
| `c69a46f` | **B1 prereg** — mode = coverage, target list, P1–P5, all unmeasured | *(not run)* |
| `dc8281b` | **B3 code** — `crit_damage` populated + RV ownership gate; M52/M53 | 0 of 35 / 0 / 26.3% |
| `9683e87` | **B4** — instrument regenerated, clean tree | 0 of 35 / 0 / 26.3% |

**Every gate-capable commit has a pre-registration as a commit-parent.**
`git log --format='%H %ci %s'` shows `e803275` → `9d29028` (39 s) and
`c69a46f` → `dc8281b` (5 min 53 s), prediction first in both cases.

**The gate did not move this session.** A modelling session was permitted to
move it and did not — which is the honest outcome, not a disappointment, and
§3 explains exactly why.

---

## §1 — Block 0: the flip landed in the shape nobody had written a protocol for

`/api/phases` at **2026-08-07T19:20:51Z** (crawler headers; bare `requests`
gets 403), verbatim in `predictions/prereg_3k_b0_phase_flip.md`:

| id | name | parent | active | start |
|---|---|---|---|---|
| 1 | Phase 0 | null | **false** | 2026-07-24T00:00Z |
| 2 | Phase 1 - Zul'Gurub | null | **true** | 2026-07-31T18:00Z |
| 3 | Phase 1.1 | 2 | true | 2026-08-03T18:00Z |
| 4 | **Phase 2 - Molten Core / Onyxia** | **null** | **true** | **2026-08-07T18:00Z** |

Molten Core landed **top-level** — the work order's shape A — **but Zul'Gurub
stayed active**. Two active top-level phases: the work order's STOP-POINT 0,
and neither shape A, B nor C. The owner was asked and decided:

> 🆕 **Transitions on this server are ADDITIVE: raids get added, none removed,
> so expect actives to accumulate each phase; don't treat `count == 2` as
> special.** (Owner, 2026-08-07.)

So `is_active` means *this content is live*, not *this is the current phase*.
`len(tops) != 1` — `3g` G0's predicate, in both `phase_guard()` and
`season_config.assert_phase()` — read that as *"a transition in progress or a
schema change"* and refused **every** `phase_label`. Permanently: Zul'Gurub
never stops being active, so the condition could never clear itself. **The
crawler would have died on its next run and the corpus would have gone
unlabelled from the first Molten Core crawl onward.**

The predicate was a **proxy**, and the hazard it proxied for is ambiguous
*labelling*. So the protection **moved rather than being deleted**:
`_overlapping_windows()` refuses when two top-level phases claim the same
`start_date`, which is the only shape `phase_windows` cannot normalise away.
M51 exists specifically to prove that half is real.

What worked without intervention, worth recording because it was designed to:
`NEXT_PHASE_BOUNDARY` **self-retired** the moment a top-level window started at
the boundary, exactly as its docstring promised.

⚠ **A fresh `/api/phases` capture had to be appended** to
`data/source/crawl/2026-08-07/phases.jsonl.gz` (2 records now: 15:49Z with 3
phases, 19:45Z with 4). `latest_phase_context()` reads the newest **committed**
payload, and measured directly: against the 15:49Z one the new constant refuses
all **436** snapshots. The API turns out to serve a phase record only once its
`start_date` has passed — record 4 was `created_at` 2026-08-04 and was absent
from the 15:49Z payload entirely.

**Corpus impact: none.** The latest capture anywhere is `16:02:50Z`, 1h57m
before the boundary, so zero captures fall on the new side and no gear tier is
affected yet.

---

## §2 — The falsification that was mine, not the code's

`3k` B0's **P1 predicted `0 of 36` and both sides read `0 of 35`.** Falsified as
written.

The cause is worth more than the prediction. P1's baseline came from a
`builds.db` built at **14:34**, while the daily crawl commit `c23b822` landed at
**17:03** — so the baseline corpus held **436** snapshots against the tree's
**472**. `0 of 36` was a number read off a stale database.

The pair was then re-measured properly, by checking `season_config.py`,
`core/builds/phases.py` and the phases capture back out at `b2ad6c1`,
re-deriving, and re-running:

| | tuning set | qualified | slice @≥20% |
|---|---:|---:|---:|
| before (`b2ad6c1` code, 472-snapshot corpus) | 0 of 35 | 0 | 26.3% (n=23) |
| after (`9d29028` code, same corpus) | 0 of 35 | 0 | 26.3% (n=23) |

**The phase change moved the gate by exactly nothing** — P1's substance, on
numbers P1 got wrong.

🆕 **The standing lesson, and it is `MEMORY.md`'s "the gate cohort slides with
the corpus" arriving from the other side.** That entry warns against comparing
gate results across a corpus rebuild. Here the *baseline itself* was
pre-rebuild. **A stale `builds.db` is a sliding window with no `ORDER BY` to
blame. A gate reading is only a baseline if the corpus under it was derived
from the tree you are about to change — derive first, then read the before.**

---

## §3 — Block B: coverage bought coverage and nothing else

### The distribution, registered before any target was picked

Absent keys ranked by cohort logged-damage share (`per_ability_summary.json` at
`57e844fb`, clean tree): **there is no big win.** The largest single absent key
(Devour Mind, 6.63%) affects **two** characters; the top 30 keys cover only
**69.3%** of absent mass, and 14 of them affect exactly one character. **Absent
mass is not concentrated, it is shattered.**

🆕 **And it is dominated by TRIGGER-DELIVERED damage, which the APL structurally
cannot contain.** `generate_apl()` iterates `build_spec.abilities` — *cards*.
Righteous Vengeance, Deep Wounds, Ignite, Frost Fever, Blood Plague,
Flametongue/Windfury/Fel Infused Attack, Seal of Command and the pet firebolts
are none of them cards. That is a different problem from a missing coefficient,
and it is the shape of `3l`'s work.

### The target: a derivation that had never once run

**Righteous Vengeance (61840)** — the broadest single absent key (**9
characters**), and the only one in the top 12 needing no new game data.

`tiers.py:861` has derived it as 30% of the rotation's crit damage since `2e`,
via `ev.get("crit_damage")`. **Nothing in the tree ever wrote that key.**
`per_event` carried `p_land` and `p_crit` and no crit damage, so the sum was
always `0.0`, the `if crit_damage > 0` branch never fired, and RV was modelled
as **zero for every character for four sessions**. Measured before the fix: **0
sim rows for 61840 across the whole 35-character cohort**, and the derivation's
own warning appearing **0 times** in the calibration report.

🚨 **The fix needed a second half, and shipping the first alone would have been
a regression.** `_add_swing_sources` added RV to *any* character with crit
damage — harmless only because the value was always zero. Populating the key
without a gate gives all 35 cohort characters an RV row when 9 log one. So the
change is: populate the key **and** gate on holding the talent card (rank ids
`53380/53381/53382`, measured from `snapshot_cards`; all 9 logging characters
hold one).

### The five predictions, scored

| # | prediction | result |
|---:|---|---|
| **P1** | absent share `62.9%` → `59.0–60.0%` | ✅ **CONFIRMED** — `59.9%` |
| **P2** | non-zero RV sim for **≥8 of 9**, and zero non-holders | ❌ **FALSIFIED** — **7 of 9**. Deyindra and Shana produce 0. The non-holder half held: exactly 9 RV rows, no others |
| **P3** | phantom production does not rise above `59.4%` | ✅ **CONFIRMED** — it *fell*, `58.4%` → **`53.8%`** |
| **P4** | slice accuracy at ≥20% coverage rises from `26.3%` into `27–34%` | ❌ **FALSIFIED** — **unchanged at `26.3%`** |
| **P5** | gate headline stays `0 of 35`, 0 qualified | ✅ **CONFIRMED** |

### 🚨 P4 is the finding of the session: COVERAGE IS NOT ACCURACY

The reasoning behind P4 was that the sim under-produces, so restoring a real
damage source must raise the modelled/logged ratio. **It does not, and the
measured reason is sharp.** RV's sim output is `645` against `151,415` logged
(Blix), `857` against `242,543` (Lootgoblin) — ratios of **0.004–0.005**. The
ability moved from `absent` straight into `producing at ~0.5% of reality`.

So the coverage statistic improved by 3 points while the slice did not move at
all, and the **producing median fell** `0.2727` → `0.2573` — because the
denominator gained nine of the worst-performing rows in the cohort.

**Moving an ability from "absent" to "producing at ratio 0.005" is a real gain
in honesty and no gain in accuracy.** A session that judged itself on absent
share alone would have called this a success. `3l` should read the two
statistics together and never quote coverage as progress toward the gate.

### Named refusals — targets NOT built, with reasons

| spell_id | name | % / chars | refusal |
|---:|---|---|---|
| 200818 | Consecrated Holy Weapon | 2.61% / 6 | **Enchant-delivered; the magnitude is not in its own record.** The client decodes a flat of `1` and db.ascension.gg independently states `Value: 1` — two independent sources agreeing on a nominal 1 *prove* it lives elsewhere. `SpellItemEnchantment.dbc` is unextracted. Unblocked by an owner-gated `--with-dbc` run scoped to include it |
| 20424 | Seal of Command | 1.47% / 4 | **No record in `spell_dbc_raw`** — reached by no extraction route. Same unblock |
| 287865 | Devour Mind | 6.63% / 2 | **Deferred, not refused** — largest by mass, 2 characters; `3k` spent its budget on breadth. `3l`'s largest single target |

---

## §4 — Mutations: two registered, and BOTH first drafts were vacuous

| # | mutation | red |
|---|---|---:|
| M50 | restore `len(tops) != 1` in `phase_guard` **and** `assert_phase` | 3 |
| M51 | delete the `_overlapping_windows` arm | 1 |
| M52 | delete the `per_event` `crit_damage` entry | 1 |
| M53 | stub the ownership gate to `holds_rv = True` | 1 |

🛑 **M52 and M53 each returned ZERO RED on the first attempt, and only running
them revealed it.** Arm 1 substring-matched `'"crit_damage"'` against the source
— and the **comment introducing the fix quotes the key**, so the check passed on
its own documentation. Arm 3 matched `"holds_rv"`, and stubbing the value leaves
the name and the import in place. Both now read the **AST**: dict keys for arm
1, and for arm 3 that `holds_rv` is *derived* (a non-`Constant` assignment)
rather than asserted, with `holds_rv = None` explicitly allowed as the
legitimate "caller could not say" initialiser.

That is M30's lesson twice more, on two new faces, and it is the whole argument
for the run-it half of the rule. **A check its own comment can satisfy is not a
check.**

---

## §5 — Harnesses at close

| harness | exit |
|---|---:|
| `py tools/audit/check_refusals.py` | **0** |
| `py tools/audit/check_sim_engine.py` | **0** |
| `py tools/audit/check_core_purity.py` | **0 violations**, 50 files |

`predictions/gate_manifest_3e.json` regenerated from a **clean tree**,
`git_sha 9683e87`. `CALIBRATION_TOLERANCE.md`'s band table regenerated with
`render_band_table.py` twice (it moved with the corpus, then with the change) —
generated, never retyped.

---

## §6 — NOT done, explicitly

Short and honest beats a padded ✅ column.

* **Block C entirely.** Both owner-scheduled deliverables are **still owed** and
  this is the second session they have been carried:
  * **C1** — the `gear_tier_stats(phase=…)` production caller. Now *more*
    tractable than when it was scheduled: phase resolution is working and a
    Molten Core window exists with zero snapshots in it, so the "refuse with a
    named reason" behaviour has a real case to refuse.
  * **C2** — `ContentProfile` presets from corpus-measured durations. ⚠ It
    feeds the sim side and needs its **own** prereg pair.
* **B5** — keyed-but-starved (12.9%, GCD allocation). Not registered in B1, so
  deliberately untouched.
* **Block D** — neither item. **D1**, the 1,208 owner<pet groups, is unexplained
  and unregistered. **D2** was answered by the owner (*annotate the FROZEN
  status note*) and **the annotation was not written** — it is the smallest
  outstanding item in the tree.
* **Ratio tuning** — out of scope by owner decision, deferred whole to `3l`.
* **The holdout** — unspent, still annotated pre-E15.
* **Coverage beyond one target.** One key of the top twelve was built. Absent
  mass is **59.9%**, and §3 says plainly that closing it is not the same as
  closing the gate.

---

## §7 — What `3k` hands to `3l`

1. **The P4 result is `3l`'s brief.** Coverage and slice accuracy are
   independent, and this session measured that rather than assuming it. Absent
   mass at 59.9% is real, but the producing median is **0.2573** and *fell*
   when coverage rose. **Tuning is now the load-bearing problem**, and it was
   already `3l`'s registered scope.
2. **The trigger-delivery gap is the structural half of coverage.** The APL is
   built from cards; most absent mass is not a card. Righteous Vengeance was
   the case where the machinery already existed and was merely unwired — Deep
   Wounds, Ignite, the diseases and the weapon-imbue procs each need the
   delivery modelled, not just a coefficient.
3. **Two named refusals need one owner-gated `--with-dbc` run** scoped to
   include `SpellItemEnchantment.dbc` — that single run unblocks Consecrated
   Holy Weapon (2.61%, 6 characters) and Seal of Command (1.47%, 4).
4. **Block C is owed and should go first**, before it is carried a third time.
5. **Phase 3 exit, honestly: 2 of 7 criteria met** — the per-criterion table is
   now in `primer/PHASE_3_builds_repo.md` rather than needing re-derivation.
6. **Why 7 of 9 and not 9 of 9 on RV** (P2) is open: Deyindra and Shana hold the
   card, log the DoT, and their rotations report no crit damage at all. That is
   a small, well-bounded thread with an obvious first question — do their
   resolved abilities carry `p_crit > 0`?
