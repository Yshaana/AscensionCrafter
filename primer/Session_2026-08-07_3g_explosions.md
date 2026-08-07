# Session `3g` — the two magnitude explosions, and what they cost `3e`

> **`HISTORICAL`** — the record of session `3g`, 2026-08-07. **A past session: it
> describes what was true when it ran, and later sessions may have overturned parts of
> it.** Not citable as current truth; for that read `PROGRESS.md`, `ENGINE_BUGS.md` and
> `CLAUDE.md`. *(Born with a status line, per `3f` F8c.)*

Work order: `primer/SESSION_3G_PRIMER.md`. Predecessors: `3f`'s record and
`primer/AUDIT_3F_ADVERSARIAL.md`.

---

## The headline

**`3f` built the first instrument in this project that compared a modelled magnitude to a
measured one. `3g` fixed the two things it found, and the gate got five times worse.**

| | before `3g` | after `3g` |
|---|---:|---:|
| within ±20% (tuning set of 36) | 5 | **1** |
| qualified (≥50% coverage) | 2 | **1** |
| slice accuracy at ≥20% coverage | 64.3% (n=23) | **20.5% (n=23)** |
| criterion (≥3 within ±20%) | PASS | **NOT MET** |
| holdout, read once at close-out | 0 of 5, −45% to −98% | **0 of 5, −79% to −98%** |

**That is the session working**, and it was pre-registered. Both fixes remove *positive*
error from a sim that already under-produces, so both had to push deltas more negative and
the count down. Stop-point 2 — *"if the gate gets better, stop"* — never fired.

🚨 **The number that matters is not the count. It is that the sim's real under-production
was hidden behind a 100× error for two sessions.** Slice accuracy did not drift from 64.3%
to 20.5%; **64.3% was never true.** The sim reproduces about a **fifth** of the damage of
the abilities it models, not two thirds.

---

## Every commit, with its gate pair and its cause

| commit | what | within ±20% | qualified | slice ≥20% | cause of move |
|---|---|---:|---:|---:|---|
| `646884a` | G0 — phase flip defence | 5 → 5 | 2 → 2 | 64.3 → 64.3 | none |
| `1942a1a` | G3 pre-work — split the E13/E14 assertion | 5 → 5 | 2 → 2 | 64.3 → 64.3 | none |
| `fb54fd7` | G1 pre-registration + auto-share instrument | 5 → 5 | 2 → 2 | 64.3 → 64.3 | none |
| **`7af0195`** | **G1 — E13 fixed** | **5 → 1** | **2 → 1** | **64.3 → 20.5** | **E13, alone** |
| `5872b53` | G2 pre-registration | 1 → 1 | 1 → 1 | 20.5 → 20.5 | none |
| **`6c62309`** | **G2 — E14 fixed** | **1 → 1** | **1 → 1** | **20.5 → 20.5** | **E14 moved deltas, not counts** |
| `389c735` | G4 — the 20% coverage floor applied | 1 → 1 | 1 → 1 | 20.5 → 20.5 | none (see below) |
| `b48fb08` | G5–G8 — instruments | 1 → 1 | 1 → 1 | 20.5 → 20.5 | none |
| `55b42cb` | G9 — self-printing counts | 1 → 1 | 1 → 1 | 20.5 → 20.5 | none |
| `131eeb4` | holdout pre-registration | 1 → 1 | 1 → 1 | 20.5 → 20.5 | none |
| `80a66e9` | holdout read | 1 → 1 | 1 → 1 | 20.5 → 20.5 | none |

**One commit moved the gate for one reason, twice. No commit moved it for two.**

⚠ **The corpus grew during G0** — `builds.db` was stale against the committed NDJSON and a
rebuild took it 412 → 436 snapshots, 116 → 139 qualifying-but-not-frozen. **The gate did not
move at all.** Under `3d`'s `ORDER BY character_id LIMIT N` that alone would have moved it;
the frozen cohort is why it did not. That is `3e` A1 paying for itself unprompted.

---

## G1 / E13 — every white swing was exactly 100× over

`AttackTable.probabilities()` returned **percent** by its own docstring while
`swings.expected_swing` multiplied by it **as fractions**.

**Nothing detected it because a function called `probabilities` returning `{"hit": 50.0}`
reads correctly at every call site.** The name says 0..1, the value says 0..100, and only
multiplying the two together reveals which one the caller believed.

🛑 **THE FACTOR IS 100, NOT ~78.** `ENGINE_BUGS` and the `3f` record both said ~78×. That is
the *multiplier's magnitude* for one particular crit rate — the bracket evaluates to ~78
where ~0.78 was meant. E13 is a **unit** error, so its size is a property of the units and is
invariant across builds: **exactly 100**. Corrected in `ENGINE_BUGS`.

### Fixed at the boundary, once

`probabilities()` returns fractions; `probabilities_pct()` exists for percentage points;
`segments` stays percent because `roll()` draws `uniform(0, 100)` from it.
**`swings.py:159-163` is unchanged, deliberately** — it was always written correctly.
Patching the multiply site was the tempting fix and the wrong one: it would have left a
function whose name and values disagree, which is the condition that produced the defect.

**Every consumer accounted for, tree-wide** (closing the `3f` audit's *"did not check
`tools/`"*):

| object | consumers | state |
|---|---|---|
| `probabilities()` | `swings.py:130` | was **wrong** |
| | `ability_model.py:678` | was **right** — it divided by 100; that divide is now gone |
| `segments` | `probabilities`/`probabilities_pct`, `roll()`, `check_sim_engine.py:266-274` | all percent, all correct, untouched |
| `SwingOutcome.crit_fraction` / `landed_fraction` | **ZERO readers** in `core/`, `tools/`, `cli/`, `ingest/` | write-only and mis-united since written |

### The exposure was far larger than `3f` reported

`3f` said 24 of 36 scored characters "carry a melee auto in their top 5". Measured with the
new `auto_share_of_sim_pct` instrument: **the auto is 89–96% of TOTAL SIM DAMAGE for
fourteen of them**, and it is 41–95% for **all five** passers — not `Ari` alone.

### Per-character attribution, all 36

**The control is exact rather than inferred: the 12 characters with no auto damage are
unchanged TO THE DECIMAL.** Coverage is identical for all 36.

| character | auto% before | auto% after | delta before | delta after | cov% | within |
|---|---:|---:|---:|---:|---:|---|
| Jamppa (33686) | 96.5 | 21.7 | +707.7 | −64.0 | 0.0 | None→None |
| Robottikyrpa (11591) | 96.1 | 19.7 | +21.0 | −94.1 | 48.9 | False |
| Onur (468) | 95.4 | 17.2 | −75.2 | −98.6 | 47.6 | False |
| Candle (33407) | 95.4 | 17.3 | +129.4 | −87.3 | 31.5 | False |
| Me (7650) | 95.2 | 16.4 | −71.2 | −98.3 | 17.7 | False |
| Nodding (10456) | 95.0 | 15.9 | −63.6 | −97.8 | 58.2 | False |
| **Xoller (39717)** | 94.8 | 15.4 | −11.6 | **−94.5** | 13.3 | **True→False** |
| **Zaczao (20491)** | 94.7 | 15.2 | −2.6 | **−93.9** | 5.6 | **True→False** |
| Frediib (40568) | 93.7 | 13.0 | +439.9 | −61.0 | 49.9 | False |
| Fana (1291) | 92.7 | 11.3 | −21.6 | −93.5 | 47.9 | False |
| Blix (7674) | 92.0 | 10.3 | −73.0 | −97.6 | 53.4 | False |
| Alicion (2855) | 91.4 | 9.6 | +68.1 | −84.0 | 28.3 | False |
| Lootgoblin (11431) | 90.8 | 9.0 | −85.7 | −98.5 | 46.2 | False |
| **Ari (464)** | 89.3 | 7.7 | −9.7 | **−89.6** | 57.6 | **True→False** |
| Ikkura (24659) | 88.1 | 6.9 | −76.2 | −97.0 | 57.8 | False |
| **Boomcat (16501)** | 87.7 | 6.6 | +641.5 | **−2.0** | 82.2 | **False→True** |
| Trace (11407) | 86.0 | 5.8 | −72.0 | −95.8 | 9.9 | False |
| **Malo (33712)** | 85.5 | 5.6 | −16.6 | **−87.2** | 62.4 | **True→False** |
| Microplastic (38900) | 82.1 | 4.4 | −50.9 | −90.8 | 22.3 | False |
| David (22640) | 81.5 | 4.2 | −63.1 | −92.9 | 4.2 | False |
| Xyz (17884) | 78.1 | 3.4 | −75.5 | −94.4 | 44.5 | False |
| Qtgamora (24695) | 76.5 | 3.2 | −55.4 | −89.2 | 69.3 | False |
| Striker (32124) | 71.6 | 2.5 | +146.4 | −28.1 | 32.4 | False |
| **Chastie (16274)** | 41.4 | 0.7 | +9.1 | **−35.6** | 4.6 | **True→False** |
| *(12 with no auto damage)* | 0.0 | 0.0 | *unchanged* | *unchanged* | — | unchanged |

### `Ari`, which the work order asked for by name

`Ari` (464) was **one of the gate's two qualified passes** at −9.7% with 57.6% coverage, and
`Melee auto (MH)` was its single largest modelled source. Measured: **the auto was 89.3% of
its sim damage.** With E13 fixed it reads **−89.6%**.

**Its −9.7% pass was a 100× error cancelling a large negative one.** That is now measured,
not suspected. The qualified rider was invented to catch compensating error one level up;
E13 was the same hazard one level deeper, *inside* a qualified pass, where an aggregate
criterion is structurally blind to it.

### `Boomcat`, the one that crossed in, and it is the most interesting row

**+641.5% → −2.0% at 82.2% coverage — the highest coverage in the cohort.** The character
with the most of its kit modelled now agrees within 2%. It is the only row where fixing E13
produced agreement rather than removing false agreement, and it is the single most
encouraging number in the session.

### The prediction, met to the decimal

`predictions/prereg_3g_e13.md` was committed at `fb54fd7`, one commit **before** the fix, and
predicted **1 of 36**, qualified **1**, slice **20.5% at n=23**, all five passers out, and
**`Boomcat`** as the one crossing in. Every figure met, including which character survives.

⚠ **Two of the work order's own premises were wrong, and I measured rather than assumed:**

1. **`SESSION_3G_PRIMER` §0 says coverage falls too. It does not** — for any of the 36.
   `modelled_damage_share()` measures the share of a character's **real logged** damage
   belonging to abilities the sim produced *any* damage for, keyed on
   `set(res.per_ability.keys())`. **Scaling a magnitude does not remove a key.** Only slice
   accuracy's numerator moves; `n` stays 23.
2. The ~78× figure, above.

---

## G2 / E14 — 12,000 ticks per cast, and it was never a one-spell defect

`occurrences_per_cast`'s periodic branch computed `round(dur / tick)` where, for a
trigger-reached component, **`dur` came from the CARD and `tick` from the COMPONENT**.
Absolute Zero divided the card's 12.0 s by the triggered spell's 0.001 s tick.

**Scanned all 1,055 distinct spell ids across the frozen cohort: 12 periodic events are built
from two different spells' timing, and the card's duration DISAGREES with the component's own
in ELEVEN of the twelve.** Absolute Zero is only where the disagreement is four orders of
magnitude instead of one tick — which is why it is the one anybody noticed.

🛑 **So I did not implement the refusal the work order specified, and this is the one place
`3g` departs from it.** Block A/G2 asks that a tick whose duration and period come from
different spells *"refuse and warn"*. That is right when the component's duration is
unknowable — **it is one join away**: `spell_dbc_raw.duration_index` → `dbc_spellduration`,
which `core/spells/mechanics.py:317,335` already performs for the card and had never
performed for a component. **Stopping the mixing fixes eleven silently-wrong components as
well as the loud one; refusing would have fixed the loud one by discarding eleven working
numbers to catch it.** Recorded in `prereg_3g_e14.md` *before* the fix ran.

| card | component | card dur | component's own | tick | n before | n after |
|---|---|---:|---:|---:|---:|---:|
| 285148 Absolute Zero | 285149 | 12.0 | **0.001** | 0.001 | **12000** | **1** |
| 275739 Goldrinn's Fury | 275740 | 20.0 | 6.0 | 2.0 | 10 | 3 |
| 901025 Bloodbath | 901021 | 8.0 | 5.0 | 1.0 | 8 | 5 |
| 901025 Bloodbath | 954815 | 8.0 | 5.0 | 1.0 | 8 | 5 |
| 282977 Summon Void Zone | 92557 | 10.0 | **−0.001** | 2.0 | 5 | **REFUSED** |
| 281210 Grove Guardian | 281211 | 15.0 | 20.0 | 5.0 | 3 | 4 |
| 281103 Mycelial Ring | 681554 | 3.0 | 10.0 | 1.0 | 3 | 10 |
| 982331 Shadow Waste Bolt | 284505 | 6.0 | 6.0 | 2.0 | 3 | 3 |
| 760158 Meteor | 760170 | 5.0 | 6.0 | 2.0 | 2 | 3 |
| 760158 Meteor | 760042 | 5.0 | 6.0 | 2.0 | 2 | 3 |
| 285133 Devour Mind | 287860 | 5.0 | 8.0 | 2.0 | 2 | 4 |
| 290255 Feral Frenzy | 290248 | 1.5 | 10.0 | 2.0 | 1 | 5 |

**The refusal is kept for what stays genuinely unknowable** — no own duration, a non-positive
DBC sentinel, and any count still over `PULSE_COUNT_SANITY_LIMIT` — and it names both spells.

⚠ **THE SANITY LIMIT ALREADY EXISTED AND WAS NOT APPLIED TO ITS OWN SIBLING.** The
periodic-**trigger-delivery** branch twenty lines above has refused above
`PULSE_COUNT_SANITY_LIMIT = 100` since `2b`. **E14 is an unapplied guard, not a missing one.**

✅ **Open question `sim_magnitude_explosion_absolute_zero` RESOLVED**
(`seed_epistemics.py`). `3e` guessed the family right and the layer wrong: not a magnitude
error, not a trigger-walk error — the attributed magnitude and the bounded walk were both
fine. **`Mutaforma` (33642) moved +3,618.8% → −88.3%** on this change alone.

⚠ **`Boomcat` survived** (−2.0% → +0.8%): it holds two affected cards pulling opposite ways
(Goldrinn's Fury 10 → 3, Feral Frenzy 1 → 5) and they netted slightly positive. The
pre-registration stated that direction as **genuinely uncertain** rather than guessing it.

---

## G3 — F9's ground truth, tolerance untouched at every step

| | modelled DPS | vs measured 1,382 |
|---|---:|---:|
| `3f`, as found | 90,202 | **+6,427%** |
| after G1 (E13) | 83,610 | **+5,950%** |
| after G2 (E14) | **457** | **−66.9%** |

🛑 **The ±25% tolerance was not widened at any point.** The assertion **stays registered as
failing**, with its new number. What remains is the ordinary under-production family — the
same direction and roughly the same size as the cohort's slice accuracy — so the entry is now
the same open modelling problem as the per-ability one, not a defect hunt.

My pre-registered range was ~500–600 DPS; actual 457. **My estimate was ~10% high and `3f`'s
own ~373 was ~20% low**; the truth sits between them.

**E13 and E14 now have separate assertions** (five of them, all unit invariants, added at
`1942a1a` *before* either was fixed) — without the split, neither could be closed
individually and the registry's *"registered + now PASSING → hard failure"* rule was blind
between them.

---

## What this does to `3e`'s headline

`3e` concluded *"six mechanisms were repaired and the answer did not move, therefore the
residual is not in the mechanisms."*

**The INFERENCE is retracted; the MEASUREMENT is not.** Seeded as
`retractions.residual_is_not_in_the_mechanisms` — prose is not a seed.

`3e`'s six repairs really did leave the gate byte-identical, and that fact is unchanged. What
cannot be concluded from it is anything about *where the residual lives*, because the metric
it was read from was dominated by a defect none of the six touched. A 100× positive error
supplying ~90% of the sim's damage for most of the cohort was cancelling a large negative
one, and an aggregate criterion is structurally blind to that.

**The residual question is re-opened, and is being asked of honest numbers for the first
time.**

---

## G0 — the phase flip, defended before it happened

**Checked live at `2026-08-07T00:35Z`: the flip had NOT happened.** `/api/phases` returned
the same three records as on 2026-08-06 — Phase 0 (closed), `Phase 1 - Zul'Gurub` (active,
`end_date` null) and `Phase 1.1` (`phase_number` 2, a **child**). `assert_phase()` passes.
`data/source/crawl/baseline_phase1/` byte-identical to its committed state.

⚠ `phases.jsonl.gz` in that folder had an mtime of Aug 6 23:38 while its siblings were Aug 4
— something re-ran `crawl_phases()` and it **wrote the file**, producing identical bytes. The
write-before-assert path is live and got away with it.

**The horizon rule defended against the wrong thing.** It NULLs captures newer than the
*payload fetch time*, but the first post-flip daily crawl appends a post-flip payload, the
horizon jumps past the flip, Phase 1's window is still `open_ended`, and every post-flip
capture up to that fetch time resolves to `Phase 1 - Zul'Gurub`.

**Three defences now**, widest first:

1. **`phase_guard()`** — the payload's active top-level phase must equal
   `season_config.EXPECTED_PHASE_NAME`, or **every** label is NULL with that as the reason.
   Nothing compared the two before.
2. **A declared boundary** (`season_config.NEXT_PHASE_BOUNDARY`) the payload has not reached.
   This is the case defence 1 **cannot** make: the server shipped its last content boundary
   as a **child** phase, which `phase_windows` drops and `assert_phase` ignores, so a Phase 2
   shipped the same way leaves the active top-level name unchanged. **The boundary
   self-retires** once a window reaches it, so a stale constant costs nothing.
3. **`horizon is None` fails CLOSED.** It used to return Phase 1 for a 2027 timestamp.

`build_builds_db.py:192`'s `f"(horizon {None:%Y-%m-%d})"` `TypeError` is gone — **F5's exact
crash class, reintroduced inside F8b's own code, in the session that fixed F5.** Extracted as
`core.builds.phases.describe_horizon()` so it is **testable without a corpus rebuild**,
rather than asserted with a source grep.

⚠ **Left undone on purpose:** `gear_tier_stats(phase=…)` still has **no production caller**,
so `3f` exit condition 10 reads ✅ on a function nothing calls. Stated in `PROGRESS.md`'s
blocked table rather than fixed — inventing a read surface is scope creep on a session that
must keep every gate move attributable.

---

## G4 — the floor removed nobody, and that is the corroboration

The stamped 20% coverage floor is **applied**, in its own commit, and **not re-tuned**.
Below it the verdict is **NOT SCOREABLE** (`None`), not `False` — *"we have no opinion"* is a
different statement from *"it failed"*.

🔬 **When it was stamped it would have cut the gate from 5 passing to 2. By the time it was
applied it cut nobody**, because the only surviving passer sits at 82.2% coverage. **The four
low-coverage passes it was designed to catch were the same characters E13 was inflating.**
Two independent instruments — a coverage floor stamped on the shape of the metric, and a unit
fix in the engine — identified the same rows from opposite directions. The floor was right
about which passes were not calibration, before anyone knew why.

**The attribution question is answered, from git.** `git log -S` puts both constants in ONE
commit (`68779e7`): the **owner decided the policy** (a floor applies, at the next gate, not
the one being run); **Code chose the value**, in A2 of that same commit, from the band table.
Neither claim was ever false, and a reader could reasonably take *"owner decision"* to cover
the number too. The property that matters survives either reading: **the value was fixed
before it was applied to a criterion, and it is strictly harsher.**

---

## Block C — the instruments

### G5 — three checks that could never turn GREEN

A new failure shape: the previous four instruments were fail-**open**; these were permanently
**red**, closable only by a lie. The consequence is the same — the check carries no
information — and the outcome is worse, because **a permanent alarm gets silenced rather than
satisfied.**

| defect | why it could not go green | green path, **run** |
|---|---|---|
| **E12** | gated on `hasattr(T, "_roll_uses_combo_points")` for a function existing **nowhere in the tree** — closable only by a stub with that name | thread `combo_points` `roll_cast` → `roll_hit` → `_components` ✅ |
| **E11** | asserted on `self_health_pct` after calling a function touching only `target_health_pct` | decay `self_health_pct` inside `tiers._decay_health` ✅ |
| **E9** | **re-implemented** the discriminator it was testing, against a fake whose tick interval is `None` — the constant `False`, green only on a *regression* | `_routes_as_debuff` → `_is_pure_periodic(ability)` ✅ |

**Two behaviour-preserving seams were created so the green path is reachable before it is
taken** — `tiers._decay_health` and `tiers._routes_as_debuff`, both byte-equivalent to the
inline code they replace, so nothing moved.

🛑 **And running the green paths is the half of the rule that paid.** E12's needed **three**
edits, not two: adding `combo_points` to the two signatures — **exactly what the work order
names as the fix** — left the check RED, because the value must reach `_components`. **A
green path that has only been named is a guess about your own code.** Now in `CLAUDE.md`.

### G6 — three tautological arms

* `check_gate_exclusion.py`'s `victim in cohort_ids and n_snaps > 0` and `victim not in
  after_outside` were true for **every** value of `EXCLUDED_SNAPSHOT_SOURCES`, every source,
  every mutation. Replaced by what they were *for*: `contaminate()` changes `source` **and
  nothing else** (measured against a snapshot fingerprint), and excluding a member leaves
  `outside` **untouched**. Both turn red under M28/M29, run.
  ⚠ The second was made unfalsifiable by the **F1 rewrite that moved the victim inside the
  cohort** — the fix and the vacuity share a cause.
* `check_sim_engine.py`'s `named` is **removed** from its assertion rather than replaced.
  `EXECUTE_GATING_UNAVAILABLE` is appended unconditionally, so it is a constant `True`; F3
  diagnosed the previous constant-`True` and substituted a different one three functions
  later in the same commit. Only `decays` is falsifiable, so only `decays` is asserted.
* 🛑 **The rest of `check_gate_exclusion.py` is sound and was NOT rewritten again.**

### G7 — the mutation registry

* **M3 was stale and was invalidated by a fix in its own session.** Removing the
  `RealmSeasonMismatch` handler turns **nothing** red — the pre-flight
  `api_get` + `assert_phase` added in the *same commit* refuses first. Removing **both**
  turns **four** red, not three. **The guard is right; the row was wrong.**
* **M2 marked `[Windows only]`** — unfalsifiable on the Linux the monitoring chat audits.
* **M7–M10 and M20–M27 carry a stated precondition** (`ascension.db` / `builds.db`, both
  gitignored). *"Every row was executed against the tree"* was unreproducible for a third of
  the registry from a clean clone.
* `check_sim_engine.py` **refuses with a message** when the db is absent instead of dying on
  a raw `sqlite3.OperationalError`, matching its sibling. A guard that cannot run must say so.
* **Green-path column populated for every registered defect** — including four rows (E10,
  E5/E7/E8, F9's ground truth) where I state that **no green path can be named**, and why,
  rather than leaving the column blank.

### G8 — the manifest

* **One `scored` ships now.** It was `len(tuning)` = 36 in `result` and
  `len(tuning)+len(holdout)` = 41 in `cohort_definition`, in the same file, neither noting the
  other — the self-contradiction F6 exists to remove, in a different coat.
* **F6's two "REFUSE to write" assertions are described correctly**: regression guards on the
  **caller's wiring**, not runtime data invariants. Given `_completeness_sql`'s `GROUP BY`
  both reduce to arithmetic identities and no data condition can trip them. **The code stays;
  the claim was the overstatement.**
* **No silent caps** — the exclusion list truncated at `excluded[:40]`.
* `not_scoreable_zero_coverage` **split**, because G4's floor had silently started adding
  below-floor characters to a key whose name says zero coverage.

### G9 — the hand-typed counts

**Both were already wrong, and the grep found a third.**

| where | said | is |
|---|---|---|
| `CLAUDE.md` | `13 / 32 / 0 / 6` | **55 files — 14 LIVE / 34 HISTORICAL / 0 SUPERSEDED / 7 FINDING** |
| `PROGRESS.md:77` | SIX questions (table held seven; `3f`'s closing said eight) | numeral **removed**; the table counts itself |
| `START_HERE_FOR_CODE.md:44` 🆕 | "53 files sat in one namespace" | **55** |

Fixed by **generation**, not retyping — retyping buys one day.
`check_refusals.py` gained `check_primer_status_census()`, which **asserts that no `primer/`
file is unclassified** and prints the census, and `check_blocked_question_count()`, which
parses the blocked table's own rows.

⚠ **The work order says *"`check_refusals.py` already walks `primer/` for the F8c test"*. It
does not — there was no F8c test anywhere in `tools/`.** The walk had to be written.

---

## The holdout, read once, at close-out

Pre-registered at `131eeb4`, the commit immediately before the read.

| member | delta | modelled | slice |
|---|---:|---:|---:|
| Qt (460) | −97.3% | 27.9% | 9.7% |
| Ryno (461) | −96.9% | 69.1% | 4.4% |
| Billyeye (462) | −95.0% | 51.0% | 9.8% |
| Wynta (463) | −98.0% | 1.3% | *150.0% — below the floor, a low-coverage diagnostic* |
| Iwannakissms (7661) | −79.4% | 52.5% | 39.2% |

**0 of 5**, as predicted. `3e`'s reading was 0 of 5 at −45% to −98%; **the best member moved
−45% → −79.4%**, which is E13 removing inflated auto damage from the member that had most of
it.

🎯 **The answer to the question a holdout exists to ask:**

| | median slice accuracy at ≥20% coverage |
|---|---:|
| holdout | **9.8%** (n=4) |
| tuning set | **20.5%** (n=23) |

**The holdout is WORSE than the tuning set, by roughly half.** The pre-registration named the
dangerous direction as the holdout looking materially *better*, which would have meant the
tuning set's numbers were selection-shaped rather than model-shaped. It went the other way.
**So 20.5% is not flattered by having been looked at — if anything it is the optimistic end.**

---

## Exit conditions

| # | condition | |
|---|---|---|
| 1 | every commit reports the gate with the cause named; no commit moves it for two reasons | ✅ |
| 2 | G0: positive assertion, `horizon=None` fails closed, `None`-format crash gone and tested, child-phase handled | ✅ |
| 3 | E13 fixed at the boundary, every consumer accounted for tree-wide, per-character attribution incl. `Ari` | ✅ |
| 4 | E14 fixed in the general case, with refusal + warning | ✅ — **and better than asked**: the mixing is stopped, not merely detected |
| 5 | E13/E14 separate assertions; F9 re-run and recorded as a number, tolerance unchanged | ✅ |
| 6 | 20% floor applied in its own commit with its own pair; attribution answered | ✅ |
| 7 | E9/E11/E12 green paths that are the fix; green-path column for every defect; rule in `CLAUDE.md` | ✅ — **all three run** |
| 8 | three tautological arms falsifiable; M3/M2/M7–M10 corrected with preconditions | ✅ |
| 9 | manifest ships one `scored`; F6's assertions described as what they are; no silent truncation | ✅ |
| 10 | holdout read once at close-out against a prediction written beforehand | ✅ |
| 11 | both hand-typed counts generated; any third one found by grep listed | ✅ — **a third was found** |
| 12 | every new document carries a status line and an expiry condition at birth | ✅ |

**12 of 12.**

---

## What `3g` did NOT do

* **E9, E11, E12 are NOT fixed** — only given green paths, as exit condition 7 asks. Each
  moves the gate and belongs in a commit that owns its pair.
* **E10, E7, E8, E5's residual** — untouched. `3g` Q5's default was to take them only if the
  clock allowed; it did not, and closing the stated scope well beat half-opening four more.
* **`PHASE_3 T6`, the log-ingestion writer** — still spilled, per the work order.
* **`gear_tier_stats(phase=…)` still has no caller** — stated, not fixed.

## The one thing to carry forward

**`3e` fixed six mechanisms and the answer did not move. `3f` fixed none and found two errors
bigger than anything `3e` touched. `3g` fixed those two and the answer moved by a factor of
five — in the direction that makes the project's problem larger.**

The lesson is unchanged and now has a second data point: **this project's error-finding rate
is set by its instruments, not by its effort.** Every defect worth finding in the last three
sessions came from putting a measured magnitude on the other side of an equals sign, and
nothing came from more careful reasoning about the code.

**The honest number today: the sim reproduces about one fifth of the damage of the abilities
it models, and the holdout says one tenth.** That is the problem. It is no longer hidden
behind a 100× error.
