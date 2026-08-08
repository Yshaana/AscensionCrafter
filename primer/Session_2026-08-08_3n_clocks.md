# Session `3n` — 2026-08-08 — two clocks, one blocker replaced, and two vacuous checks caught

> **`HISTORICAL`** — the record of session `3n`, written at its close. A past
> session; **may contain claims that are false today, and that is correct.**
> Work order it ran: `primer/SESSION_3N_PRIMER.md` (now `SUPERSEDED`). Audit it
> implemented: `primer/AUDIT_3M_ADVERSARIAL.md`. The owner answered four
> stop-points at session start; two more carried their stated defaults.

## §0 — Commit by commit, with the gate at each

| commit | what | within/qual | slice (n) | producing (n) |
|---|---|---|---|---|
| `9669b67` | pre-flight: four audit repairs + five more siblings | — | — | — |
| `f252afa` | **Block A baseline** | 0 / 0 | 30.040 (24) | — |
| `62d9eae` | Block A per-ability baseline | 0 / 0 | 30.040 (24) | 0.3234 (117) |
| `fdf9851` | **PREREG** — the APL clock fix | — | — | — |
| `14ec3dc` | **leg 1**: the swing budget | — | — | — |
| `699f878` | leg 1 manifest | 0 / 0 | **30.040 (24)** | — |
| `260c930` | leg 1 per-ability | 0 / 0 | 30.040 (24) | **0.3133 (127)** |
| `9c96dc6` | producing same-member instrument (reporting only) | — | — | — |
| `10c52b4` | instrument seeded | 0 / 0 | 30.040 (24) | 0.3133 (127) |
| `fc9a36c` | **leg 2**: on-next-swing replaces its swing | — | — | — |
| — | leg 2 manifest | 0 / 0 | **30.150 (24)** | — |
| — | leg 2 per-ability | 0 / 0 | 30.150 (24) | **0.2571 (123)** |
| `196ac5e` | M70/M71 registered and run | — | — | — |
| — | Block C (E2), registrations, seed corrections, close-out | 0 / 0 | 30.150 (24) | 0.2571 (123) |

**Prereg parenthood:** `fdf9851` → `14ec3dc` (leg 1) and `fdf9851` → `fc9a36c`
(leg 2). Every gate-capable commit has the prereg as an ancestor with no
intervening gate-capable change.

## §1 — Owner decisions

Four answered at start; two took their stated defaults.

1. **Block D** — open only if B and C leave room. *(They did not. Deferred, §8.)*
2. **E2** — land in `3n`, not a third carry. *(Landed, §4.)*
3. **First post-Monday capture** — Monday 10 Aug or soon after.
4. **Chase-list re-rank** — yes, after B/C. *(Written, §6.)*
5. **Holdout** — unspent (default). Not read.
6. **Predicate 2 (deaths > 0)** — UNARMED (default).

⚠ Decision 3 was **amended by the owner mid-session** — see §7.

## §2 — Pre-flight: the blast radius was wider than the audit found

`AUDIT_3M`'s headline lesson is that a correction's blast radius includes its
siblings. Applying it found **five sites the audit did not name**.

The audit's four: `seed_epistemics.py:181`'s falsified aura-344 claim (F1); the
`2b` ALL_EFFECTS seed, annotated rather than deleted as **pre-2026-08-10
delivered** behaviour (F2); ENGINE_BUGS M63's wrong site (F4); the tally and
`58.83` prose (F3).

**The five it did not:**

- `voidbound_lightbound_cleave_dbc_formula` — **the root the retracted `9+AP`
  came from**, still asserting "a full 1:1 AP-scaling coefficient" as fact. Its
  own conclusion was also backwards: it claimed to correct the "LC flat 62
  assumption", and **62 is right** (Rank 5); the 9 it preferred is Rank 1.
- `voidbound_cleave_damage_share_and_parse` — "fits the formula in shape" with no
  captured stat block, i.e. **a free parameter absorbing any residual**, which is
  exactly why it could not detect that the formula was wrong.
- `winds_of_winter_stack_dbc_pulls` — upgraded a PREDICTION to "DBC-CONFIRMED"
  **using the same misreading that produced it**.
- `wip_winds-of-winter-frostblade.md` — 973/700/606 withdrawn, and the Path
  argument they fed is void: with no AP term this ability is not "where
  Intelligence costs damage".
- `synergy_portable-multiplier-packages.md` — the "≈ +200 DPS for two slots"
  package premise *was* the weapon component the fix removed.

**F3, counted from the scored tables:** `3m` was **20 predictions — 17 confirmed
/ 2 falsified / 1 split** (B 4✓·2✗·1 split · C 7/7 · D 6/6), not "13 of 15".
And **`58.83` exists in no committed output** — the emitter prints **58.8**.
⚠ Consequence stated rather than papered over: at 1 dp the artifact cannot
support an "unchanged" claim finer than ±0.05 pp.

## §3 — Block B: the APL clock fix

**The mechanism, re-derived rather than inherited.** `is_next_swing` is decoded
in `mechanics.py:272` and was **read by nothing in `core/sim/`**. These abilities
also fail the off-GCD test **on a technicality** — all 11 next-swing ids resolve
`gcd_type = None`, because they are rank siblings absent from the catalog. So
they were ranked among GCD fillers by damage **per cast** and charged a GCD they
do not cost.

🚨 **A correction to `3m` §9.** It reports Lightbound Cleave as swing-limited at
*"44.52 casts"*. **That is not the swing clock** — it is what LC would get from
the GCD budget if it won the filler ranking. Blix's real swing clock is 2.9366 s,
giving **23.936**. The fix hands LC roughly **half** what `3m`'s figure implies —
a number read off the wrong clock, in the section diagnosing a wrong clock.

**Exposure:** 12 of the 35 tuning-set members (`3m`'s 15 of 41 is the whole
cohort; the 5 holdout are not read). 10 of the 12 fully starved.

**Two legs, scored separately.** Leg 1 gives next-swing abilities their own
**swing budget** (shared, because two Cleaves cannot ride one white swing). Leg 2
is the **replacement** — `schema.py:341` calls it that — reducing main-hand autos
by the next-swing casts, main hand only, clamped. Leg 1 alone would add their
damage *on top of* swings that never happen.

**Result: 9 predictions, 8 confirmed, 1 falsified.**

| | |
|---|---|
| slice | 30.040 → **30.150 (n=24)**, published **+0.11 pp** = same-member **+0.11 pp**, membership unchanged |
| producing median | 0.3234 (117) → **0.2571 (123)** |
| within / qualified | **0 / 0** throughout |
| starved allocations | 105 → 94 |

🚨 **P8 FALSIFIED on Meritania**, reported not rescued. Its precondition (the
ability out-damages the auto it replaces) held; the precondition was
**incomplete** — it silently assumed leg 1 *gains* the member casts. Meritania's
Dusk Maul was already cast at ~its swing rate (19.625 → 19.008), so leg 1 gave
her nothing and leg 2 only subtracted. **The log agrees with the direction:** her
autos still sim 33.48 against 21.66 logged, so what was removed was over-count.
The clause I needed was in probe data I already had.

🚨 **THE TWO HEADLINE INSTRUMENTS MOVED IN OPPOSITE DIRECTIONS, BOTH PAIRS
EQUAL** — so both are accuracy, not composition. Not a contradiction: the slice
is per **character** over that character's modelled abilities; the producing
median is per **ability row**, unweighted. Block B moved damage out of a row
every melee character has (autos) into rows only 12 have. First time in the arc
they have disagreed in sign with both pairs equal, and **neither is the gate.**

**Leg 1's producing move is the purest P4b instance yet:** the median fell
0.3234 → 0.3133 and **nothing became less accurate** — 11 starved abilities
returned, with a median ratio of **0.2061**, below the sitting median. They were
always this badly modelled; they were previously *invisible* because they cast
zero times. **Fixing the clock made an existing error countable.**

## §4 — Block C (E2): the blocker moved, and naming which is the point

`tools/analysis/pair_parses_to_stats.py` pairs each GUID-resolved kill window
against the stat blocks **bracketing** it, and rules before deriving anything.

| window | verdict |
|---|---|
| Lucifron | 🛑 no block BEFORE it (nearest +46 s) |
| Magmadar | 🛑 no block BEFORE it (+340 s) |
| **Gehennas** | ✅ **ADMISSIBLE** — AP 488 held, brackets −607 s/+822 s |
| Garr | 🛑 brackets DISAGREE: AP 488→471, Str 214→201, Agi 112→99, Int 359→346, crit 32.36→31.96 |
| Baron Geddon | 🛑 no kill (3 attempts) |

Garr is precisely the confound the test exists for, and **invisible with a single
stat block**: five stats move together, so the character who dealt the damage is
not the character any one block describes.

🚨 **`refused:no_per_parse_stats` is LIFTED for Gehennas** — stats at the parse
exist, verified unchanged, with **logged 319.8 s separated from wall 379.8 s**
(dividing by wall understates DPS by 15.8%). That was E2's stated blocker.

**What blocks a coefficient now is arithmetic, not data.** One admissible window
is ONE (stat, damage) point per ability, and a coefficient is a **slope**:
`damage = flat + coeff × stat` is under-determined by one point — every
coefficient fits, with the flat absorbing the difference. **The fix is a capture
protocol, not more data**: a stat block immediately before and after each pull.
Registered as `per_parse_coefficient_needs_two_stat_levels`.

## §5 — Mutations, and two vacuous drafts

M70 (the code that actually shipped `3e`→`3m`) and M71 (the plausible half-fix)
both run **RED exit 1 / GREEN exit 0**, tree clean after each.

🛑 **Two drafts of the check were vacuous, and only running the mutation found
it.** Draft 1 asserted arithmetic on literal constants and re-implemented the
clamp — `3f`'s vacuity plus `3g` G5's re-implementation. **Draft 2 is the new
one and is worth the registry entry:** it asserted `rate_limit ==
"swing_budget"`, and stayed green under M70 **because the label is computed by a
separate expression from the allocation** — the mutant left it reading
`swing_budget` beside `casts = 0.0`.

> **A STRING DESCRIBING WHAT THE CODE MEANT IS NOT EVIDENCE OF WHAT IT DID.**
> Assert the magnitude the mechanism produces, recomputed from the same inputs
> the sim used — never a label the code assigns to itself.

Sharper than `3f`'s soft source-text arms: this label is not a comment, it is a
real emitted field in a committed artifact, and it was **wrong in the mutant
while the check reading it was green.**

A third fix was coverage, not vacuity: the auto row is **omitted** when every
swing is replaced, which is the commonest case on these fixtures — so an arm
firing only when the row exists would not run in the situation M71 produces.

## §6 — The mid-session capture, and the chase-list re-rank

The owner landed `2026-08-08_elric_lbc_baseline_imbue_test/` during the session.
Three consequences, all handled:

1. 🚨 **`2e`'s "+88 AP per imbue" DOES NOT REPRODUCE** — the three-step re-measure
   reads **+80**, i.e. **×1.096** against the decoded 73: **one** ordinary ×1.10,
   not two. **The ×1.21 is retired**, in both seeds that carried it. ⚠ Note which
   half moved: Holy SP is +172 = 2×86 and Bonus Healing +86 **exactly, in both
   captures**. The SP half reproduces across three days; the AP half does not.
2. 🚨 **The owner holds Improved Cleave 0/3 and never rolled it**, correcting an
   assumption in `3m`'s framing. **Monday's patch changes his damage by exactly
   zero** — it changes the card's chase value only.
3. **Chase-list re-rank written**
   (`builds/my-builds/chase_improved-cleave_rerank_2026-08-08.md`): don't chase
   it; slot it if it rolls; the reset question does not arise at 0/3. The
   inverted-scaling point is the one worth keeping — **the better the main hand,
   the less the card is worth**, because it is now a multiplier on a flat.

## §7 — E1's detector note is AMENDED by the owner

`SESSION_3N_PRIMER` E1 said the first post-Monday capture "doubles as the free
detector that the server fix shipped as stated." **That is not available from the
owner's captures** — he holds no Improved Cleave, so pre- and post-fix
predictions for him are identical. The detector must come from **post-Monday
parses of cohort members who hold the card** (Blix, Lootgoblin, Robottikyrpa,
Nodding all run a hybrid Cleave).

🔬 One cheap control remains: an identical post-Monday Lightbound Cleave dummy
capture should show **no change at all**.

## §8 — NOT done, explicitly

1. **E1 — the date-aware Improved Cleave impairment did NOT land.** ⚠ Its
   urgency is **lower than the work order assumed**, for the reason in §7: the
   frozen cohort is entirely pre-fix, and the owner's own captures cannot be
   contaminated by the fix because he holds no card. It is still required before
   any post-Monday parse of a **card-holding cohort member** is compared to
   anything pre-fix. **`3o` must land it before that comparison, not before the
   capture.**
2. **Block D — delivery modelling NOT opened.** B and C did not leave room
   (owner's stated condition). Absent mass **59.0%**. Devour Mind is
   **registered** rather than carried a fourth time.
3. **The imbue's +73 AP grant is still UNMODELLED** in the sim — `3m` C3
   identified it, `3n` re-measured its sheet value, neither put it in the model.
4. **The ×1.141 Lightbound Cleave residual is NOT scored.** The new capture
   measures LBC at IC 0/3, no imbue: n=143, non-crit **523.8** against a
   decode-only base of **459.05**. Computing the sim's talent layer for that
   exact board and scoring the residual is the obvious next measurement and was
   not done.
5. **The holdout stays unspent** (0 passers).
6. **`verify_scraped_coefficients.py`'s third slot convention** — still carried,
   still named by an arm.
7. **Meritania's swing budget is greedy** — Dusk Maul takes every swing and
   starves Mystic Talon, which was previously producing. Defensible (Mystic Talon
   logs 0.00 too) but it is an allocation policy nobody stamped.

## §9 — Harnesses at close (clean tree)

| harness | result |
|---|---|
| `check_refusals.py` | exit 0 — **cite the `[arms]` line the tool prints on a clean tree** |
| `check_core_purity.py` | exit 0 — 52 files, 0 violations |
| `check_sim_engine.py` | exit 0 — all checks pass, including the fast-vs-medium agreement guard |

Census regenerated in every commit touching `primer/`.

## §10 — What `3n` hands to `3o`

1. **An APL that ranks on the right clocks**, with two mutations behind it and a
   registered lesson about what a check may assert.
2. **E2's blocker replaced and named** — with a capture protocol that fixes it in
   one line.
3. **E1, unlanded but correctly scoped** — needed before a card-holder's
   post-Monday parse, not before the owner's next capture.
4. **Devour Mind registered** with an ordered plan, after four deferrals.
5. **A producing same-member instrument**, live from its second run.
6. **Three fresh measurements nobody has scored**: the ×1.141 LBC residual, the
   88-vs-80 imbue AP delta, and the sheet weapon-damage +15.4×speed anomaly.
