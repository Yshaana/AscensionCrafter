# Engine bugs — defects in OUR code, found by the regression harness

> **`LIVE`** — the defect registry, ENFORCED in both directions by check_sim_engine.py. **Must be true today, and is citable as current truth.** If you find a claim here that the tree contradicts, that is a defect in this file. *(Classified `3f` F8c, 2026-08-07.)*

**Not game bugs.** `bugs/` is for Ascension's bugs, staged for submission, and its
README says so explicitly: *"These are **game** bugs, not this repo's bugs.
Problems with our own code go in `PROGRESS.md`'s plan-changes table or a session
handoff, not here."*

> ⚠ **Convention conflict, resolved and flagged for the owner.**
> `SESSION_3D_PRIMER.md` D3 says to record these as `bugs/` entries. The repo's
> own convention says the opposite. This file honours the repo — putting engine
> defects in the Ascension submission queue would pollute the thing the owner
> actually submits from. If the owner prefers them in `bugs/`, moving them is a
> `git mv` and a README edit.

**Every entry here is a FAILING CHECK in `tools/audit/check_sim_engine.py` —
with one stated exemption** (`3i` A4, writing down what `:534` and the
"Also recorded, without checks" list already self-disclosed): an entry MAY stand
without a check **only if its Check row says so explicitly** ("NONE", with the
reason) or it sits in the explicitly-labelled without-checks list. An entry that
neither carries a check nor discloses its absence is a defect in this file.
Registered entries live in `EXPECTED_FAILURES`, so they do not break
the build — but the registry is enforced in both directions:

* an **unregistered** failure fails the harness (a new regression);
* a **registered** check that starts **PASSING** also fails the harness, with a
  message telling you to close the entry here and drop it from the registry. A
  stale "known bug" list is the same doc-drift this project treats as its most
  expensive failure mode, so it is not allowed to rot quietly.

---

## 🆕 The check registry — every check, and the mutation that turns it red

**Standing rule, adopted `3f`** (`ADDENDUM_3E_to_3F.md` §4, promoted from
`PLAN_3G:111-112`): *every check carries a registered test that makes it fail.*
**If you cannot name the mutation, it is not a check.**

It was adopted because the `3e` audit found **four instruments that could not
fail**, three of which would have been caught by naming a mutation and trying
it. Two of them had defects CLOSED on their say-so.

🛑 **Naming a mutation is not enough — RUN it.** Every row below was executed
against the tree and the red checks recorded. Three of my own first attempts in
`3f` were themselves wrong or vacuous and only running them showed it: a
mutation that dropped an input id rather than an output row (left the check
green), a test case that exercised only one of two assertions (left the other's
mutation green), and an in-process `io.StringIO` stderr that accepts any
codepoint (made an encoding assertion unfalsifiable).

🆕 **`3g` G5 — AND THE RULE HAD ONLY HALF A RIGOUR.** The `3f` audit found
**three registered checks that could never turn GREEN from their own fix** —
permanently red, closable only by a lie. A check that cannot go green carries no
information either, and it will eventually be silenced rather than satisfied. So
**every row now names the change that turns it green as well, and that change
must be the FIX**. Where a defect is registered but unfixed, the **seam** the fix
lands in is created first so the green path is reachable before it is taken.

🛑 **Run the green path too, not just the red one.** `3g` named E12's as *"thread
`combo_points` through `roll_hit`/`roll_cast`"*, applied exactly that, and the
check **stayed red**: the parameter has to reach `_components`, not just the
signatures. A green path that has only been named is a guess about your own code.

⚠ **PRECONDITION column, `3g` G7.** *"Every row below was executed against the
tree"* was unreproducible for a third of the registry from a clean clone —
`data/derived/*.db` is gitignored. Each row now states what it needs, so an
auditor knows whether a row they cannot run is stale or merely gated. This is the
primer's own standing practice — *a code path only a gated run exercises can stay
broken while everything reports green* — applied to the registry itself.

| # | mutation (turns it RED) | red | GREEN PATH — the change that closes it | needs |
|---|---|---:|---|---|
| M1 | revert `session_mismatch`'s log side to `return None` | 1 | ✅ already green — F4 is fixed | — |
| M2 | drop `config.ensure_utf8_stdout()` from `baseline_phase1.py` | 1 **[Windows only]** | ✅ already green | **Windows** |
| M3 | remove **BOTH** the pre-flight `api_get`+`assert_phase` block **and** the `RealmSeasonMismatch` handler | **4** | ✅ already green | — |
| M4 | remove the `ValueError` guard in `_log_started_at` | 1 | ✅ already green | — |
| M5 | point `closing_note` back at `args.*` instead of the resolved stats | 1 | ✅ already green | — |
| M6 | remove `baseline_phase1`'s pre-flight phase assert | 1 | ✅ already green | — |
| M7 | `EXCLUDED_SNAPSHOT_SOURCES = ()` | 3 | ✅ already green | **`builds.db`** |
| M8 | make `_decay_target_health` a no-op (pin target health at 100) | 1 | ✅ already green | **`ascension.db`** |
| M9 | `detect_summons` returns `[]` | 3 | ✅ already green | **`ascension.db`** |
| M9b | `detect_summons` returns rows with **wrong** spell ids (non-empty) | 3 | ✅ already green | **`ascension.db`** |
| M10 | `_useful_cast_interval` returns a positive interval for everything | 3 | ✅ already green | **`ascension.db`** |
| M11a | drop the manifest's frozen-arithmetic assertion | 2 | ✅ already green | — |
| M11b | drop the manifest's scoring-loop assertion | 1 | ✅ already green | — |
| M12 | drop the holdout carry-forward | 2 | ✅ already green | — |
| M13 | treat CHILD phases as top-level in `phase_windows` | 2 | ✅ already green | — |
| M14 | drop the horizon rule in `resolve_phase` | 2 | ✅ already green | — |
| M15 🆕 | drop the `expected_phase_name` branch in `phase_guard()` | 2 | ✅ green at `646884a` (G0) | — |
| M16 🆕 | drop the declared-boundary branch in `resolve_phase()` | 1 | ✅ green at `646884a` (G0) | — |
| M17 🆕 | restore the fail-**open** horizon (`horizon is not None and ts > horizon`) | 1 | ✅ green at `646884a` (G0) | — |
| M18 🆕 | revert `describe_horizon()` to a bare f-string | 1 | ✅ green at `646884a` (G0) | — |
| M19 🆕 | drop the boundary's self-retirement, so it never disarms | 2 | ✅ green at `646884a` (G0) | — |
| M20 🆕 | **E13** — make `AttackTable.probabilities()` return percent again | 3 | ✅ green at `7af0195` (G1): return fractions at the boundary and drop the consumer's `/100.0` | **`ascension.db`** |
| M21 🆕 | **E14** — drop the component's own duration, or the sanity limit, in `occurrences_per_cast` | 3 | ✅ green at `6c62309` (G2): read `duration_index` → `dbc_spellduration` per component | **`ascension.db`** |
| M22 🆕 | **E9** — n/a, it is still red | — | 🛑 **`tiers._routes_as_debuff` returns `_is_pure_periodic(ability)`.** RUN 2026-08-07: turns it green. Seam created in G5 so the check imports the real predicate instead of re-implementing it | **`ascension.db`** |
| M23 🆕 | **E11** — n/a, it is still red | — | 🛑 **decay `self_health_pct` inside `tiers._decay_health`.** RUN 2026-08-07 (with a 100→40 non-linear track): turns it green. ⚠ Not a mirror of the target's linear 100→0 — the player is healed as well as damaged | **`ascension.db`** |
| M24 🆕 | **E12** — n/a, it is still red | — | 🛑 **thread `combo_points` through `roll_cast` → `roll_hit` → `_components`.** RUN 2026-08-07. ⚠ **Signatures alone left it RED** — the value must reach `_components`. Three edits, not two | **`ascension.db`** |
| M25 🆕 | **E10** — n/a, it is still red | — | 🟡 **no green path named.** `_decay_target_health` divides by `st.fight_duration` while the timeline is bounded by `fight_duration × (1 − movement_pct)`; whether the fix is to divide by the effective time or to extend the timeline **changes what a fight IS**, and picking one is a modelling decision, not a repair. Stated rather than left blank | **`ascension.db`** |
| M26 🆕 | **E5 / E7 / E8** — n/a, still red | — | 🟡 **no green path named**, same discipline: each is a rotation-model change whose correct shape is not settled (E7's filler budget, E8's channel model, E5's mixed direct+periodic entries) | **`ascension.db`** |
| M27 🆕 | **F9's two ground-truth entries** — n/a, still red | — | 🟡 **no green path named, and this one is the point.** They close when the sim stops under-producing by ~5×. That is the project's open problem, not a defect with a fix | **`ascension.db`** |
| M28 🆕 | `contaminate()` also nulls `gear_stats_json` — i.e. changes more than `source` | 1 | ✅ already green (`3g` G6) | **`builds.db`** |
| M29 🆕 | `contaminate()` also hits a NON-cohort character, perturbing `outside` | 1 | ✅ already green (`3g` G6) | **`builds.db`** |
| M30 🆕 | delete the status line from any file in `primer/` | 1 | ✅ restore it — which IS the fix, because an unlabelled document cannot be cited at all (`3g` G9) | — |

⚠ **M30's FIRST DRAFT WAS TOO WEAK, and it is M17's lesson a second time.**
Mutating `` `LIVE` `` → `LIVE-ish` still matches the marker regex (`-` is a word
boundary), so it returned **0 red** — which a harness counting `FAIL` lines
would have scored as *vacuous*, condemning a check that was fine. The mutation
has to **delete** the status line, not deform it. **Two of `3g`'s mutations were
wrong on first attempt and both were caught only by running them** — which is
the entire argument for the run-it half of the rule.

🆕 **M28/M29 replace two arms of `check_gate_exclusion.py` that were
TAUTOLOGICAL** (`3g` G6, confirming the `3f` audit §2.3). `victim in cohort_ids
and n_snaps > 0` and `victim not in after_outside` were each true for every value
of `EXCLUDED_SNAPSHOT_SOURCES`, every `source` and every mutation — `victim` is
drawn from the cohort and `outside = qualifying − cohort_ids`. ⚠ **The second was
made unfalsifiable by the F1 rewrite that moved the victim inside the cohort:
the fix and the vacuity have the same cause.** The replacements assert what the
arms were *for* — that `contaminate()` changes `source` and nothing else, and
that excluding a member leaves the outside set untouched — and both turn red
under a mutation, run 2026-08-07. 🛑 **The rest of that file is sound and was not
rewritten**; the exclusion, drop-reason and control arms are genuinely
falsifiable and the auditor verified them by running them.

🆕 **A third tautology was REMOVED rather than replaced** —
`check_sim_engine.py`'s `named = any("TargetAuraState" in w …)`.
`EXECUTE_GATING_UNAVAILABLE` is appended **unconditionally**, so it is the
literal constant `True`; `F3` diagnosed the previous form
(`any("health" in w.lower() …)`) as a constant `True` and replaced it with a
different constant `True` three functions later in the same commit. Only
`decays` is falsifiable (M8), so only `decays` is asserted. `named` is still
computed and printed — a reader wants to see the disclosure is present — but the
detail string now labels it unconditional so it cannot be read as a result.

*(A duplicate five-row fragment of M15–M19 stood here — an editing artifact,
removed `3i` A5; the rows live in the main table above.)*

**M15–M19 are `3g` G0's**, all in `core/builds/phases.py`, all red-counted by
running `tools/audit/check_refusals.py` under each mutation and restoring —
harness output pasted into the `3g` session record. ⚠ **M17's first draft was
malformed and is worth recording**: replacing only the `horizon is None` branch
with `if False:` left the following `ts > horizon` comparing against `None`, so
the check **crashed with a traceback instead of going red** — 0 red, which a
harness counting FAIL lines would have scored as *vacuous*. The mutation has to
restore the real prior code (one branch guarded by `horizon is not None`), not
merely disable the new one. **A mutation that changes the failure MODE is not
the mutation you meant to run.**

🛑 **M3 WAS STALE, AND IT WAS INVALIDATED BY A FIX IN ITS OWN SESSION** (`3g` G7,
confirming the `3f` audit §2.5). The row read *"delete the `except
RealmSeasonMismatch` handler around `crawl_phases()` … all three assertions go
red. (Verified 3f.)"* The auditor applied exactly that and **all four F0 checks
stayed PASS**: the pre-flight `api_get` + `assert_phase` block added in the *same
commit* (`baseline_phase1.py:106-113`) refuses at exit 2 before `crawl_phases()`
is reached. Only removing **both** turns anything red, and it turns **four** red,
not three. The measurement was taken before the pre-flight existed and never
re-run. **The guard is right; the row was wrong** — corrected above. A registered
mutation is a claim about the tree and ages exactly like any other claim.

⚠ **M2 IS PLATFORM-CONDITIONAL and is now labelled.** Deleting
`config.ensure_utf8_stdout()` turns **nothing** red on Linux — CPython selects
UTF-8 for a pipe on POSIX regardless (PEP 538/540) — so the assertion is
unfalsifiable there and in any Linux CI. The code comment scopes it to Windows
honestly, so *(Verified 3f.)* is plausible where it was run. The monitoring chat
audits on Linux and would see it pass unconditionally.

⚠ **M7–M10 and M20–M27 cannot be run from a clean clone**, because
`data/derived/*.db` is gitignored. That is not a defect in them; it is a fact an
auditor needs, and it is now in the table.

Checks live in `tools/audit/check_sim_engine.py` (the engine harness),
`tools/audit/check_gate_exclusion.py` (cohort integrity) and
`tools/audit/check_refusals.py` (guards that must not fail open — new in `3f`).
Each check's own docstring names its mutation; this table is the index.

---

## Why these were invisible until now

Every fixture, the whole regression harness, and `calibrate_vs_log.py`'s defaults
were **one character** — Elric, a Paladin/Hammerdin. These six defects sit in
**shared** code paths that an all-instant, single-filler, no-combo-point, no-pet
melee build is structurally incapable of exposing. Nothing in the repo would have
failed if a Rogue or a Warlock produced nonsense.

Session `3d` (Block D) added two fixtures built from **real crawled boards** —
`fixtures/build_crawled_cp_melee.json` (snapshot 462) and
`fixtures/build_crawled_dot_caster.json` (snapshot 218) — and every entry below
fell out immediately.

🛑 **Fixing these is `3e`.** `3d` was scoped to ship failing tests that name real
bugs, not green tests. Do not "repair" a failure by weakening its assertion.

---

## E1 — `combo_points` is never incremented, and `is_finisher` never fires either — ✅ FIXED (`3e` B4)

> ### ✅ Closed 2026-08-06, session `3e` Block B4. Fixed in the order this entry demanded, and each step was necessary.
>
> **1. Detection.** `is_finisher` read `t.get("cp_scaling")` alone. Every real
> per-combo term on this board carries **`per_combo`** instead —
> `EffectPointsPerCombo`, a decoded flat per combo point — while `cp_scaling` is
> set only on **coefficient** terms parsed from tooltip text, and is `None` even
> there. Reading both takes the board from **0 CP-gated entries to 4**
> (Rupture 11275, Panache 277038, Aether Rupture 904965, Crimson Tempest 954886).
>
> **2. Placement — necessary, and not predicted by this entry.** With detection
> fixed the finisher still cast **zero** times: it sat among the *fillers*, and a
> higher-damage filler carrying `always` won every priority scan, so the gated
> entry never got a turn. Finishers now have their own APL tier **above** the
> fillers. It is safe there for the same reason a maintained debuff is — it is
> gated, and unavailable until the combo points exist.
>
> **3. The economy.** `combo_points` is generated and spent in `medium_sim`, and
> `fast_sim` limits a finisher to `N / (cp + 1)` casts (the cycle is `cp` builder
> GCDs plus the finisher's own). `expected_hit`/`expected_cast` now take
> **`combo_points`**, read from the APL's own gate rather than re-derived, so the
> gate and the damage cannot disagree about what was spent. Before this a
> finisher's `per_combo` flat and its `cp_scaling` coefficient were **both scored
> at 0 CP** — a finisher's entire reason for existing contributed nothing.
>
> 🛑 **The generation rate is a `retail_hypothesis`, because the data is absent —
> and the absence is itself a finding.** `SPELL_EFFECT_ADD_COMBO_POINTS` is
> effect type 40 and `spell_effect_values` holds **zero rows** of it. Nothing in
> the extract says which abilities generate combo points or how many. So
> `CP_PER_BUILDER_CAST = 1.0` is assumed **once, under a name, with a warning
> emitted by any sim that relies on it** — the same treatment `BASE_GCD` gets.
> Open question: `combo_point_generation_absent_from_extract`.
>
> **Gate impact (B3 → B4): unchanged at 5 of 36, qualified 2, slice 64.3%.**
> 7 of 36 characters moved, none across the boundary — finishers now fire less
> often but each one is worth its combo points, and on this cohort the two
> roughly cancel.

<details><summary>The original E1 entry, as written by <code>3d</code></summary>

| | |
|---|---|
| **Check** | `[cp_melee] an APL entry gated on combo_points_at_least can ever fire` |
| **Where** | `core/sim/tiers.py:197` (`SimState.combo_points = 0`), `core/sim/apl.py:118` (the condition reads it), `core/sim/apl_gen.py:91` (emits it for every finisher) |
| **Predicted by** | the `3c` adversarial audit, §4.J |

`combo_points` is declared on `SimState` and **incremented nowhere in the tree**,
so `combo_points_at_least` can never be true and any finisher gated on it never
casts in `medium_sim`. `ability_model.py:420-425` separately scores combo-point
terms at 0 CP.

🚨 **NEW — this is worse than the audit predicted, and the audit's version is
currently MASKED.** On a real combo-point board, `apl_gen` classified **none** of
the four abilities carrying a genuine per-combo term (Rupture 11275, Crimson
Tempest 954886, Panache 277038, Aether Rupture 904965) as finishers — so **zero**
APL entries are CP-gated. The finishers cast freely as ordinary fillers.

Two consequences for `3e`: incrementing `combo_points` alone fixes nothing, and
a naive check ("does a finisher ever cast?") would have PASSED while both bugs
were live. `is_finisher` detection has to be fixed first, and then the CP economy
becomes reachable — at which point the *original* bug starts biting.

</details>

---

## E2 — execute windows are dead code, and nothing says so — ✅ FIXED (`3e` B5)

> ### ✅ Closed 2026-08-06, session `3e` Block B5.
>
> **The mechanism works now.** `target_health_pct` decayed nowhere — it was
> pinned at `100.0` for the whole fight, so `target_health_pct_below` was
> permanently false and every execute-range ability was unreachable, *while*
> `apl_gen` emitted no health condition either, so the same abilities cast as if
> always available. Unmodelled in both directions at once. Target health now
> falls linearly from 100% to 0% across the fight — a boss fight **ends** when
> the target dies, so that is the shape, not a pacing assumption — and a
> `target_health_pct_below` gate is honoured in `medium_sim`. `fast_sim` has no
> clock, so the same gate enters as a **share of cast count**: under linear decay
> an ability gated at "target below X%" is available for exactly the last `X/100`
> of the fight.
>
> 🛑 **What is NOT fixed, because the data does not exist: which abilities carry
> an execute gate.** In 3.3.5 that is
> `TargetAuraState = AURA_STATE_HEALTHLESS_20_PERCENT`, and `spell_dbc_raw`
> carries **no aura-state column at all** — the extract exports `attributes` /
> `attributes_ex` and nothing else of that family. So Hammer of Wrath is still
> modelled as always available and is still over-credited. **Both tiers now emit
> that by name** (`EXECUTE_GATING_UNAVAILABLE`) rather than leaving it silent,
> which is precisely what this entry asked for: *"the failure is not 'it never
> casts', it is that the window is unmodelled in either direction and the sim
> does not say so."* Open question: `execute_gating_absent_from_extract`.
>
> ⚠ Same shape as B4's combo-point finding, in a different field: the mechanism
> was repairable in an afternoon, and the **data gap behind it needs a wider
> `--with-dbc` extract**, which is owner-gated.

<details><summary>The original E2 entry, as written by <code>3d</code></summary>

| | |
|---|---|
| **Check** | `[cp_melee] the execute window is modelled, or the sim says it cannot model it` |
| **Where** | `core/sim/tiers.py:198-199` — `self_health_pct` / `target_health_pct` fixed at `100.0` |
| **Predicted by** | §4.J |

Target health never moves, so `target_health_pct_below` is never true and every
execute-range ability is unreachable — while the solo self-sustain branch
(`apl_gen.py:72-80`) is dead for the same reason.

Measured on the fixture: Hammer of Wrath (24239) is execute-gated in game and the
sim **cast it 9 times** at a pinned 100% target health, with **0** APL entries
carrying a health condition and no warning mentioning health. So the ability is
not merely missing — it is modelled as *always available*, which over-credits it.

**The failure is not "it never casts". It is that the window is unmodelled in
either direction and the sim does not say so.**

</details>

---

## E3 — no pet model, while the corpus DPS being calibrated against includes pets — 🟡 NAMED, NOT MODELLED (`3e` B6)

> ### 🟡 Closed at the "explicitly named as a gap" bar, 2026-08-06. The owner's chosen scope turned out to be UNREACHABLE, and that is the finding.
>
> **Owner decision 2026-08-06 was the mechanical minimum:** summon → a pet actor
> with auto-attacks plus whatever damage spell its own record carries, scaled
> from the owner's stats. **That is not buildable from this project's data, for a
> structural reason rather than a gap someone forgot to fill.**
>
> * **Summons ARE derivable.** `SPELL_EFFECT_SUMMON` is effect type 28 and
>   `spell_effect_values` holds **395 rows across 389 spells**, each carrying the
>   summoned **creature id** in `misc_value`. `core/sim/pets.py :: detect_summons`
>   answers "does this build summon, and what", and both tiers now call it.
> * **A pet's DAMAGE is not.** Creature stats — attack power, damage range,
>   attack speed, the pet's own spells — live in the server's
>   `creature_template`, **not in any client DBC**. There is no creature table in
>   `ascension.db`, and **no `--with-dbc` widening would produce one, because the
>   client does not ship it.** This is the one data gap in `3e` that an
>   owner-gated extract cannot close.
>
> So the sim names each pet and states the measured size of what it is missing —
> **5.0% unbuffed / 5.4% buffed / 1.5% dungeon** on the owner's Frost Mage
> capture, ~10% across the gate cohort. Inventing a damage figure would be
> fabrication *inside the number the calibration gate reads*.
>
> ✅ **The route that works is LOGS, not DBC.** `ability_performance` already
> carries `is_pet`, and a combat log names pet damage directly, so a pet damage
> profile can be **measured** per pet. That belongs with PHASE_3 T6 log ingestion
> (session `3f`). Open question: `pet_damage_not_derivable`.
>
> 🔬 **A rule-5 finding fell out of this.** The harness had been identifying pets
> by **string-matching "summon" in the ability name** — the exact thing rule 5
> forbids, inside the harness that polices the rest of the engine. Against the
> mechanical detector the two disagree **in both directions**: on the combo-point
> board the name match returns `Summon Felguard, Summon Void Zone, Summon
> Voidwalker`, the effect query returns `Summon Void Zone` and **`Roll the
> Bones`** — a summon no name match could find, plus two "Summon …" titles
> carrying no summon effect at all. The check now uses the detector, with a
> vacuity guard.

<details><summary>The original E3 entry, as written by <code>3d</code></summary>

| | |
|---|---|
| **Checks** | `[cp_melee] pet damage is modelled or explicitly named as a gap`, and the same for `[dot_caster]` |
| **Where** | no pet model anywhere in `core/sim/`; `core/builds/corpus.py:614` computes `dps = (total_damage + pet_damage) / duration` |
| **Predicted by** | §4.J; owner decision 2026-08-06 was already "model pets" |

Both fixtures summon (`Summon Felguard`, `Summon Voidwalker`, `Summon Void Zone`;
`Summon Imp`) and **no warning anywhere mentions pets**. Pet-carrying builds are
guaranteed to miss low against a corpus number that includes pet damage — and
silently, which is the part that matters. Roughly 10% of the cohort's real damage.

Naming it as a gap is the minimum; modelling it is the owner's decision and is
`3e` work.

</details>

---

## E4 — the APL grammar cannot express DoT uptime — ✅ FIXED (`3e` B2)

> ### ✅ Closed 2026-08-06, session `3e` Block B2.
>
> Added to `core/sim/apl.py`: **`debuff_active`**, **`debuff_missing`** and
> **`debuff_remaining_below`** (`{spell_id, value}` — the pandemic refresh, "the
> DoT has under N seconds left"), with evaluator branches for each.
>
> 🚨 **The grammar was only half of it. `medium_sim` filed EVERY
> duration-carrying ability in `st.buffs`**, so a DoT on the boss and a seal on
> yourself were the same object and a target-debuff condition would have read the
> player. `TimelineState` now carries a separate **`debuffs`** dict, and the cast
> path routes by the same mechanical discriminator `_useful_cast_interval` uses:
> **a duration plus a tick interval is a DoT; a duration alone is a self-buff.**
>
> ⚠ **The check was STRENGTHENED, not satisfied.** Its original form asked only
> whether a condition *name* containing `"dot"` or `"debuff"` existed in
> `CONDITION_TYPES` — satisfiable by adding a string to a set, which is exactly
> the way a green test can mean nothing. It now exercises the evaluator against a
> state carrying a real target debuff and asserts the buff/debuff separation
> holds.

<details><summary>The original E4 entry, as written by <code>3d</code></summary>

| | |
|---|---|
| **Check** | `[dot_caster] the APL grammar can express DoT uptime` |
| **Where** | `core/sim/apl.py:19-32` — the closed `CONDITION_TYPES` set |
| **Predicted by** | §4.J |

The full grammar is `always`, `buff_active`, `buff_missing`,
`combo_points_at_least`, `cooldown_ready`, `health_pct_below`,
`other_cooldown_not_ready`, `other_cooldown_ready`, `resource_at_least`,
`resource_pct_at_least`, `target_health_pct_below`, `time_remaining_below`.

**There is no target-debuff or DoT-uptime condition at all.** `buff_active` /
`buff_missing` track the *player's* buffs, not a debuff on the target. So a DoT
can only ever be given `always`, and the intended fix ("re-cast when the DoT is
about to expire") is not expressible.

</details>

---

## E5 — 6 of 7 DoTs on a DoT-caster board never enter the rotation — 🟡 PARTLY FIXED (`3e` B3)

> ### 🟡 Pure DoTs fixed 2026-08-06 (`3e` B3). Mixed direct+DoT abilities are a DIFFERENT defect — see **E7**.
>
> **What landed.** `apl_gen` gained a **maintained-debuff tier** placed *before*
> cooldowns, each entry gated on `debuff_remaining_below` (1.5s, one GCD — stated,
> not tuned, and deliberately **not** retail's 30% "pandemic" rule, which we have
> no evidence Ascension implements). Gating is what makes a high priority safe: a
> maintained debuff is unavailable for all but the last moment of its duration, so
> it cannot monopolise the list. `fast_sim`'s allocation order was changed to split
> on **whether an ability has any useful cast interval**, not on whether it has a
> cooldown — a DoT has no cooldown but is bounded by its own duration, and under
> the old test it fell in with the unbounded fillers and was allocated last.
>
> **Corruption goes 0 → 4 casts in 68 s, i.e. once per its own 18 s duration.**
> That is the defect fixed.
>
> 🚨 **The masked re-cast bug appeared on schedule, and then a SECOND
> misclassification appeared under it.** With DoTs entering the rotation, the
> re-cast check immediately failed — Fireball 10 casts, Living Bomb 6, Pyroblast 7
> in one fight — exactly as this entry predicted. But the cause was **my own
> discriminator**, not the APL: I had treated *"has a periodic component"* as
> *"is a DoT"*. **Fireball is a direct nuke that leaves a 4 s rider**, and bounding
> it to one cast per 4 s models a Fire mage casting Fireball ten times a minute.
> The test is now `_is_pure_periodic` — read from `events()`, which already splits
> damage into `direct`/`periodic` per source spell. **The fixture caught this;
> reasoning did not.**
>
> **Gate impact (B1 → B3):** 4 of 36 → **5 of 36**, qualified unchanged at 2,
> slice accuracy at ≥20% coverage 62.6% → **64.3%**. 10 of 36 characters moved, in
> both directions. ⚠ Chastie returns to passing (−27.9% → +9.1%) **on the mixed-
> ability over-count named in E7**, at 4.6% coverage — the same compensating-error
> pass B1 removed. It is reported, not celebrated.
>
> **Still XFAIL, for a reason that is no longer this one:** 5 of 7 periodic
> abilities on the fixture still cast zero times. Two (Fel Armor, Dark Domination)
> are non-damaging; three (Fireball, Immolate, Living Bomb) are mixed abilities
> competing in the spam-filler tier, where one button correctly absorbs the budget.
> **The check is deliberately left registered rather than rewritten** — declaring a
> check invalid because it no longer flatters the code is the failure mode this
> registry exists to prevent.

<details><summary>The original E5 entry, as written by <code>3d</code></summary>

| | |
|---|---|
| **Check** | `[dot_caster] the board's DoTs enter the rotation at all` |
| **Where** | `core/sim/apl_gen.py:59-63` — priority is off-GCD, then cooldowns longest-first, then fillers by damage per cast |
| **Predicted by** | 🚨 **NOBODY. This is new.** |

Measured in `medium_sim` over a 75s fight: Corruption (11671), Immolate (25309),
Living Bomb (44523), Fireball (133), Fel Armor (28189) and Dark Domination
(285158) are cast **zero** times. Only Pyroblast (18809) fires, 5 times.

Cause: a DoT with no cooldown is filed as a *filler*, behind **every** cooldown
ability, and this board has nine of those. The GCD budget is exhausted before the
rotation reaches the DoTs — so the defining abilities of a DoT caster contribute
nothing at all.

⚠ **And it hid E6's sibling.** The audit predicted DoTs would be *re-cast every
GCD*; the check for that currently reads clean **only because they are never cast
at all**. Fixing E5 will very likely make the re-cast bug appear. The two must be
fixed together, and the re-cast check must not be read as green in the meantime —
it carries that caveat in its own failure text.

</details>

---

## E7 — a mixed direct+periodic ability is mis-modelled in both directions 🆕

| | |
|---|---|
| **Check** | ✅ **THREE registered failing checks** — `[cp_melee] / [dot_caster] / [frost_mage] fast_sim allocates GCDs to more than one filler`, all in `EXPECTED_FAILURES` (`grep -n "more than one filler" tools/audit/check_sim_engine.py` — a line range stood here and drifted, `3i` A5). Also surfaced per ability as a `warnings` entry from `core/sim/tiers.py :: _mixed_damage_warning`. ⚠ The row read *"none yet"* until `3f` F8, contradicting this file's own every-entry-is-a-failing-check invariant (the header block above the registry; it read "line-15" here and that line number drifted too) |
| **Where** | `core/sim/ability_model.py :: expected_cast` returns ONE mean for an ability whose events are part direct, part periodic |
| **Found by** | `3e` B3, while fixing E5 |

An ability with **both** a direct hit and a periodic rider — Fireball, Immolate,
Living Bomb, and on the melee side Aether Rupture — has no correct single cast
rate:

* **Bound it by the DoT's duration** and the direct component is starved: a Fire
  mage casts Fireball once every 4 seconds.
* **Leave it unbounded** and every cast re-scores the rider's entire duration, so
  the periodic component is over-counted by roughly `duration / gcd`.

**Neither is right, and no field resolves it.** What a refresh does to a
partially-elapsed DoT is a server behaviour nobody has measured on Ascension.

Unbounded is what runs, because the direct component dominates on these spells
and is the larger error to get wrong — and the residual is **named in
`warnings`** per ability rather than buried. That is the floor, not the fix.

**The real fix is per-EVENT cast allocation**: score the direct component at the
cast rate and the periodic component at its own refresh rate. That is a change to
the ability model, not to the APL, which is why it is its own entry rather than
part of E5.

⚠ **It is load-bearing for the gate.** Chastie passes at +9.1% partly on this
over-count, at 4.6% coverage.

🆕 **Third fixture, `3e` C2:** the Frost Mage casts **1 of 4** fillers. A caster
whose entire rotation *is* fillers is the case where one spam button absorbing
the whole budget is most visibly wrong — the starved three are Blizzard (a
channel, see E8), Hydricles and Ice Lance.

---

## E8 — the sim never reads `is_channeled` 🆕

| | |
|---|---|
| **Check** | 🛑 **STILL NONE — and unlike E7 that is accurate.** `grep -n channel tools/audit/check_sim_engine.py` returns comments only, so E8 is held by prose alone under the header invariant's stated exemption (it read "breaches this file's line-15 invariant" until `3i` A4 wrote the exemption down; the breach was real and self-disclosed, which is exactly what the exemption now requires). It is NOT registered in `EXPECTED_FAILURES`, because a registry line is a claim that a check exists. **What would close it:** assert that a build containing a channelled ability (Blizzard, 10187 — the Frost Mage fixture already carries it) charges more than one GCD of occupancy for it, or that some warning names the channel. Both fail today. Deliberately not written in `3f`, which fixes no engine defects — see E9–E12, registered on the same terms |
| **Where** | resolved into the DB at `core/spells/mechanics.py:275` (column at `core/db/schema.py:340`); `grep -rn is_channeled core/sim/` returns **nothing** |
| **Found by** | `3e` C2, verified 2026-08-06 rather than inherited |

A channel occupies the caster for its full duration while delivering damage in
ticks. The sim charges it **one GCD** and credits **every tick**, so a channelled
ability is over-credited by roughly `channel_duration / gcd`.

🔬 **Whether this bites depends on the window, and the Mage capture settles it
for each:**

| window | Blizzard casts (Elric) | channel gap |
|---|---:|---|
| A — unbuffed dummy | **0** | inert |
| B — buffed dummy | **0** | inert |
| C — Scarlet Monastery | **4** | **live** |

🛑 **CORRECTED in `3f` F8. Window C read `305` and that figure was wrong by
~76×.** 305 is a raw grep LINE COUNT over every Blizzard-mentioning line, and
it is not even all Elric's. Re-measured through `combat_log_parser.py`'s named
fields rather than by grep: **283 parsed Blizzard events — Elric 200, a Scarlet
Sorcerer 83** (29% of them an enemy's), and Elric's decompose as
`SPELL_CAST_SUCCESS 4 · SPELL_DAMAGE 134 · SPELL_AURA_APPLIED 31 ·
SPELL_AURA_REMOVED 31`. **He cast Blizzard four times**, delivering **88,132 of
940,460** spell damage — **9.4%** of the window.

*(Counted independently in `3f` rather than taken from the audit that flagged
it. The headline — 4 casts, 9.4% — reproduces exactly; the event decomposition
differs slightly from the audit's, and the numbers above are the ones actually
measured here.)*

**The conclusion survives and the entry is not rewritten**: Window C *is*
E8-exposed and A→B is not, and 9.4% of a window is well worth modelling. But a
number wrong by 76× was sitting in the durable registry as the SIZING of an
engine gap, and it was quoted onward into `Session_2026-08-06_3e_modelling.md`
and `PROGRESS.md` to justify C4's spill. ⚠ **The lesson is the counting method,
not the number: a line count is not an event count, and a log line naming an
ability does not say who cast it.** Count `SPELL_CAST_SUCCESS` filtered by
`sourceName`, through `combat_log_parser.py`'s named fields — the same rule
CLAUDE.md already states about hand-indexed columns, one level up.

So every A→B comparison in this capture is safe from it, and **anything derived
from Window C is not** — which is a second reason C4's dungeon `ContentProfile`
needs care beyond its segmentation problem.

⚠ Channels are also **indistinguishable from instants in the client API** —
`GetSpellInfo` position 7 reads 0 for Blizzard exactly as it does for Ice Lance
(capture README). `attributes_ex & 0x44` in the DBC is the only route, which is
why `is_channeled` is resolved in the mechanics layer in the first place. The
data is there; the sim simply never asks for it.

---

## E9–E12 — four defects in the code `3e` wrote. REGISTERED IN `3f`, NOT FIXED 🆕

🛑 **Each would move the gate, so each belongs in a modelling session with a
before/after pair** — `3d`'s D3 discipline, and `3f`'s invariant is that no
commit moves the gate. All four now carry a check that FAILS
(`check_sim_engine.py`, `EXPECTED_FAILURES`). Do not close one by weakening its
assertion.

### E9 — a THIRD DoT discriminator, in the layer that decides priority

| | |
|---|---|
| **Check** | `[engine] E9: medium_sim routes a DoT by the SAME discriminator apl_gen and _useful_cast_interval use` |
| **Where** | `core/sim/tiers.py` medium_sim's cast path (`dur and tick_interval_seconds`) vs `core/sim/apl_gen.py` and `tiers._useful_cast_interval` (both `_is_pure_periodic`) |

`apl_gen.py` states *"Shares `tiers._is_pure_periodic` so the two layers cannot
drift apart"*, and `1c07bab`'s commit message asserts the routing uses *"the
same mechanical discriminator `_useful_cast_interval` uses"*. **It does not**,
and it stopped being true the moment B3 added `_is_pure_periodic` to
`_useful_cast_interval`.

**Failure scenario, asserted directly by the check:** an ability with a
periodic aura whose `EffectAmplitude` is 0 gets `is_periodic=True, tick=None`.
`_is_pure_periodic` → `True`, so `apl_gen` files it in the **maintained tier at
the top of the APL** gated on `debuff_remaining_below 1.5`; the routing test
→ `False`, so it lands in `st.buffs`; `debuff_remaining()` then returns `0.0`
forever; `0.0 < 1.5` is always true; **the entry wins every priority scan and
consumes the whole rotation.** That is the Seal-of-Command 47-of-47-GCDs
failure, re-created at the top of the list.

### E10 — target-health decay is capped by `movement_pct`

| | |
|---|---|
| **Check** | `[engine] E10: target health decays to ~0 by the end of the fight, as _decay_target_health's own docstring says it does` |
| **Where** | `core/sim/tiers.py :: _decay_target_health` vs `_effective_time` |

The decay divides by `st.fight_duration` while the timeline loop is bounded by
`fight_duration × (1 − movement_pct)`, so **target health floors at
`100 × movement_pct`** — and every preset sets `movement_pct` 0.05–0.20.
Measured on `world_boss` (0.20): the floor is exactly **20.0%**, so
`target_health_pct_below: 20` is **permanently false in `medium_sim`** — E2's
original symptom, unfixed on that profile — while `fast_sim` credits the
ability 20% of its casts. The two tiers disagree by up to 1.8×, and the
fast-vs-medium agreement guard runs on the Paladin fixture only.

⚠ **The check's own first version passed on floating-point luck** (`< 20.0`
against a floor of exactly 20.0) and was rewritten to assert the property the
docstring actually claims — that health reaches ~0. A knife-edge assertion is
not an assertion.

### E11 — `self_health_pct` is declared, read, and written nowhere

| | |
|---|---|
| **Check** | `[engine] E11: the PLAYER's health moves, so a self-sustain heal gated on health_pct_below can fire` |
| **Where** | `core/sim/tiers.py` (declared), `core/sim/apl.py` (read), **no writer anywhere in the tree** |

`apl_gen` emits `health_pct_below` for every healing ability when
`content.self_sustain_required` (`mythic_dungeon_aoe`, `solo_grind`), so those
entries can **never** fire in `medium_sim`; in `fast_sim`, `_health_gate` does
not match `health_pct_below` at all, so the same heal is cast at the **full**
rate. *"Unmodelled in both directions at once, and silent about it"* — E2's own
words, on the player side, while E2's registry line was being deleted.
`content.incoming_damage_dps` (150–300 on those presets) sits unused.

### E12 — `roll_hit` / `roll_cast` never received `combo_points`

| | |
|---|---|
| **Check** | `[engine] E12: slow_sim rolls a finisher at the combo points medium_sim spent on it` |
| **Where** | `core/sim/ability_model.py` (the RNG path calls `_components()` with the default `combo_points=0`), consumed by `slow_sim` |

B4 threaded `combo_points` through `_components → expected_hit →
expected_cast` but not through the RNG path. `slow_sim` builds its skeleton
from `medium_sim` — which casts at 5 CP — and then rolls **every cast at 0
CP**. **Measured on the combo-point fixture: the finisher (904965) scores 197
at 0 CP and 328 at 5 CP, a 1.7× difference**, so a combo-point build's
Monte-Carlo mean and 95% band are centred *below* the medium-sim answer they
claim to be the variance of. The docstring still asserts convergence is
*"asserted by check_sim_engine.py"*; that assertion runs at `combo_points=0`
and passes vacuously.

### Also recorded, without checks — smaller, verified, and each a real defect

* **`_is_pure_periodic` fails OPEN into the over-count.** `except Exception:
  return False`, and `bool(evs) and all(...)` — so *"I could not tell"* and
  *"I have no events"* both return the same value as *"definitely not a DoT"*,
  routing the ability into the **unbounded spam** tier. The safe default is the
  bounded one; the code picked the over-counting one and says nothing. Rule 2.
* **The `starved` warning asserts a cause it did not check** — *"higher-priority
  abilities consumed the whole GCD budget"* — when zero casts also come from
  `occupancy == 0`, `window == 0.0` or the CP cap. Nine lines later the same run
  can print *"Xs of GCD budget went UNUSED"*: two contradictory claims in one
  output.
* **`_cp_gate` / `_health_gate` are first-match-wins on duplicate spell
  entries.** *Rupture at 5 CP* **and** *Rupture at 1 CP when falling off* — the
  natural way to write a real rotation — scores every cast at whichever is
  listed first and charges the budget twice, warning about neither.
* **`combo_points_at_least.value` is unvalidated** against `MAX_COMBO_POINTS`.
  A hand-authored `50` gives `medium_sim` zero casts (fail-closed) and
  `fast_sim` a `cp_scaling × 2500` (it squares it). The two do not cancel.
* **The quadratic CP multiplier (25× at 5 CP) is applied silently**; its warning
  fires only in the branch where it is *not* applied.
* **Combo points are granted from idle scans and off-GCD entries** — the grant
  sits before the `if not entry.off_gcd:` guard, so an `always` off-GCD entry
  saturates CP within two scans.
* **The pet warning block is duplicated verbatim** in `medium_sim`, DB round-trip
  included. Deduped downstream, so cosmetic.
* **`stat_block.py` silently merges two concatenated blocks last-wins**
  (verified: unbuffed+buffed → AP 30 / SP 840 / the later `ExportedAt`, no
  warning). That is the contamination shape the module exists to prevent.

---

## E13 — every white swing was EXACTLY 100x over: `probabilities()` returned PERCENTS, `expected_swing` multiplied by them as FRACTIONS — ✅ FIXED (`3g` G1)

> ### ✅ Closed 2026-08-07, session `3g` G1 (`7af0195`). The record below is what was found; this box is what happened.
>
> 🛑 **THE FACTOR IS EXACTLY 100, NOT ~78.** The `~78` throughout the record below is the
> *multiplier's magnitude for one particular crit rate* — the bracket evaluates to ~78
> where ~0.78 was meant. E13 is a **unit** error, so its size is a property of the units
> and is **invariant across builds, weapons and content**: exactly 100. Read every `~78`
> below as "the bracket's value on the frost-mage fixture", not as the defect's size.
>
> **Fixed at the boundary, once.** `AttackTable.probabilities()` returns FRACTIONS
> (`combat_engine.py:242-244`); `probabilities_pct()` exists for percentage points
> (`:246-249`); `segments` stays percent because `roll()` draws `uniform(0, 100)` from it.
> `swings.py:159-163` is **unchanged, deliberately** — it was always written correctly.
> Patching the multiply site was the tempting fix and the wrong one: it would have left a
> function whose name and values disagree, which is the condition that produced the defect.
> `ability_model.py:748` was the CORRECT consumer all along and its compensating `/100.0`
> is gone.
>
> **Every consumer accounted for, tree-wide** (`core/`, `tools/`, `cli/`, `ingest/`): one
> wrong caller (`swings.py:130`), one right caller (`ability_model.py:678`), and
> `SwingOutcome.crit_fraction` / `landed_fraction` with **zero readers** — write-only and
> mis-united since written.
>
> 🚨 **The exposure was far larger than `3f` reported.** `3f` said 24 of 36 scored
> characters "carry a melee auto in their top 5". Measured with the `auto_share_of_sim_pct`
> instrument: **the auto was 89–96% of TOTAL SIM DAMAGE for fourteen of them**, and 41–95%
> for **all five** passers — not `Ari` alone.
>
> **Gate pair, this fix alone:** within ±20% **5 → 1**, qualified **2 → 1**, slice accuracy
> at ≥20% coverage **64.3% → 20.5%** (n=23 both). `Ari`'s −9.7% qualified pass was a 100×
> error cancelling a large negative one, and now reads **−89.6%**. The 12 characters with
> no auto damage are unchanged **to the decimal**, which makes the attribution exact rather
> than inferred.
>
> **Assertions:** three, in `check_sim_engine.py:865-882`, and **deliberately absent from
> `EXPECTED_FAILURES`** — a check that has started passing must leave the registry, or the
> registry stops meaning *"these are the known failures"*. They run every run; a regression
> turns them into ordinary hard failures.
>
> ⚠ **Still open, carried from the record below:** whether the `block` row should reduce
> damage rather than being dropped. Not assumed, not fixed, not registered.

| | |
|---|---|
| **Check** | `[frost_mage] modelled DPS is within the PRE-REGISTERED ±25% of the measured capture` (registered XFAIL) |
| **Where** | `core/sim/swings.py :: expected_swing` — `mean = base * (p["hit"] + p["crit"]*crit_mult + p["glancing"]*glance_mult)`, against `core/sim/combat_engine.py :: white_melee_table(...).probabilities()` |
| **Found by** | `3f` F9, by the first assertion in this project's history that compared a modelled magnitude to a measured one |

**Measured, on the Frost Mage fixture:**

```
weapon 227.7-253.7            -> base (min+max)/2   =    240.7
armor 3731 @ level 60         -> x 0.6119           =    147.3
probabilities() returns         {miss 4.4, dodge 6.5, parry 14.0,
                                 glancing 32.6, block 5.0,
                                 crit 16.63, hit 20.87}   SUM = 100.0
expected_swing computes         147.3 x (20.87 + 16.63x2 + 32.6x0.75)
                              -> 11,573.6 per swing
```

**A probability table that sums to 100 is a PERCENTAGE table.** Treating it as
fractions multiplies every white swing by **exactly 100** — the bracket below
evaluates to ~78 at *this* fixture's crit rate, which is where the `~78x` in
this entry's original heading came from, but the defect is a unit error and its
size is 100 for every build. `expected_swing` returns **11,573.6** for a weapon
whose average hit is 240.7.

🚨 **THIS IS INSIDE THE CALIBRATION GATE, AND IT IS NOT A CORNER CASE.**
**24 of the 36 scored cohort characters carry a melee auto in their top 5 sim
abilities**, and one of them is **`Ari` (delta −9.7%, `Melee auto (MH)` its
single largest modelled source) — one of the gate's TWO qualified passes.** So
at least one qualified pass is standing on a 78x-inflated auto-attack. That is
compensating error of a size this project has not previously seen, and the
`3e` holdout result — *"the residual is not in the mechanisms"* — should be
re-read in its light: the residual may be a large positive error cancelling a
large negative one, which an aggregate criterion is structurally blind to.

🛑 **DELIBERATELY NOT FIXED IN `3f`** — *and it was the first thing `3g` did.* The
paragraph that stood here said this belonged in a modelling session with a
before/after pair; `3g` G1 gave it exactly that, and the pair is in the closure
box at the top of this entry. The prediction it makes — *"in the direction of
more under-production"* — was correct, and understated: the gate went from 5
passing to 1.

⚠ Both of the "check when it IS fixed" items were taken up. The consumer sweep
(`grep -rn "probabilities()"` across `core/`, `tools/`, `cli/`, `ingest/`) was
run tree-wide and found no third caller. **The `block`-row question is still
open** and is the one thing in this entry that is not closed.

---

## E14 — a periodic component with a 0.001s tick scored 12,000 ticks per cast — ✅ FIXED (`3g` G2)

> ### ✅ Closed 2026-08-07, session `3g` G2 (`6c62309`). The record below is what was found; this box is what happened.
>
> 🛑 **IT WAS NEVER A ONE-SPELL DEFECT, AND THAT IS THE PART WORTH CARRYING.** Scanned
> across all 1,055 distinct spell ids in the frozen cohort: **12 periodic events are built
> from two different spells' timing, and the card's duration DISAGREES with the component's
> own in ELEVEN of the twelve.** Absolute Zero is only where the disagreement is four
> orders of magnitude instead of one tick — which is why it is the one anybody noticed.
>
> **Fixed by stopping the mixing, not by detecting it — a deliberate departure from the
> work order, pre-registered at `5872b53` before the fix ran.** The component's own
> duration is one join away (`spell_dbc_raw.duration_index` → `dbc_spellduration`, which
> `core/spells/mechanics.py:317,335` already performed for the card and had never performed
> for a component). Refusing would have fixed the loud case by discarding eleven working
> numbers.
>
> ⚠ **THE SANITY LIMIT ALREADY EXISTED AND WAS NOT APPLIED TO ITS OWN SIBLING.** The
> periodic-**trigger-delivery** branch twenty lines above has refused above
> `PULSE_COUNT_SANITY_LIMIT = 100` since `2b`. **E14 is an unapplied guard, not a missing
> one** — which is a different and more worrying class than a guard nobody wrote.
>
> **The refusal is kept for what stays genuinely unknowable** — no own duration, a
> non-positive DBC sentinel (92557 reads −0.001s), and any count still over the sanity
> limit — and it names both spells. No spell in the corpus reaches the first of those
> today, so it is exercised **synthetically** (`check_sim_engine.py:958-972`): an untested
> refusal is a refusal nobody has seen refuse.
>
> **Gate pair, this fix alone:** within ±20% **1 → 1**, qualified **1 → 1**, slice accuracy
> **20.5% → 20.5%**. E14 moved deltas, not counts. `Mutaforma` (33642) moved **+3,618.8% →
> −88.3%** on this change alone, and `Boomcat` survived at −2.0% → +0.8% (it holds two
> affected cards pulling opposite ways; the pre-registration stated that direction as
> genuinely uncertain rather than guessing it).
>
> ✅ **Open question `sim_magnitude_explosion_absolute_zero` RESOLVED** (`seed_epistemics.py`).
> `3e` guessed the family right and the layer wrong: not a magnitude error, not a
> trigger-walk error — the attributed magnitude and the bounded walk were both fine.
>
> **Assertions:** three, in `check_sim_engine.py:915-972`, deliberately absent from
> `EXPECTED_FAILURES` for the same reason as E13's. ⚠ The second was **re-derived** during
> the fix: its first form asserted the *mechanism* the work order specified (Absolute Zero
> refuses), and now states the *property* (a tick count comes from one spell's duration and
> that same spell's tick). An assertion that encodes a mechanism breaks when a better
> mechanism arrives.
>
> 🚨 **What this fix hands to `3h`:** every new refusal converts a previously-producing
> component into a **zero that still holds a `per_ability` key**, and coverage counts keys.
> See `AUDIT_3G_ADVERSARIAL.md` §4 — the fix is correct and its interaction with the
> coverage instrument is not yet measured.

| | |
|---|---|
| **Check** | `[frost_mage] modelled DPS is within the PRE-REGISTERED ±25% of the measured capture` (registered XFAIL, shared with E13) |
| **Where** | `core/sim/ability_model.py :: expected_cast` — a periodic event is scored as `duration / tick_interval` ticks, with the duration taken from the CARD and the tick from the TRIGGERED spell |
| **Found by** | `3f` F9 |

**Measured, on the Frost Mage fixture:**

```
285148 Absolute Zero   duration_seconds = 12.0    (the card)
285149 Absolute Zero   tick_interval_seconds = 0.001, duration_seconds = 0.001
                       (the triggered spell the periodic event resolves through)
-> 12.0 / 0.001 = 12,000 ticks scored for ONE cast
-> 2,217,786 damage per cast; 2.8 casts = 6,237,523 of the fixture's
   6,765,160 total damage (92.2%)
```

Measured ground truth for the same ability: **270.5 per non-crit hit** (n=6).

**The 0.001 is a decode artifact, not a game value.** `EffectAmplitude` of 1
(milliseconds) becomes 0.001 s, and the record's own `duration_seconds` is
*also* 0.001 — i.e. one application, not a 12-second channel of millisecond
ticks. The bug is combining a duration from one spell with a tick interval
from another and dividing.

🔬 **This is almost certainly `sim_magnitude_explosion_absolute_zero`**, the
open question `PLAN_3C` raised against Mutaforma's +3,619%, now with a
mechanism and a number rather than a symptom. Worth re-checking that question's
other members against this cause when it is fixed.

🛑 **NOT FIXED IN `3f`** — same reason as E13, *and fixed in `3g` G2*. ⚠ The requirement
stated here — *"guard the general case, not special-case this spell … should refuse and
warn"* — was **met and then improved on**: measuring first showed the component's own
duration is available, so the general case is fixed by removing the mixing rather than by
refusing it, and the refusal survives only where the duration is genuinely unknowable. The
reasoning for that departure is in `predictions/prereg_3g_e14.md`, committed **before** the
fix. See the closure box at the top of this entry.

---

## E15 — pet-attributable damage is stored TWICE in `ability_performance`, so every SUM over the table double-counts it 🆕🚨

| | |
|---|---|
| **Check** | `[corpus] identical owner+pet rows in ability_performance are counted ONCE in the coverage denominator` (registered XFAIL, `check_sim_engine.py`) |
| **Where** | the corpus layer: `ability_performance` holds, for a pet-attributable ability, an **owner row (`is_pet=0`) and a pet row (`is_pet=1`) with byte-identical damage**. Consumer bitten: `calibrate_crawled.py :: modelled_damage_share` sums every row, so both copies enter the coverage denominator (and the numerator when the spell is keyed) |
| **Found by** | `3h` C4 — the per-ability comparison: pet-class auto ratios read 0.005–0.013 (Malo, Ikkura, Onur) and inspection of the logged side found each swing stream twice |

**Measured, corpus-wide (2026-08-07):**

```
(scope, character, spell) groups with damage > 0:
  owner-only ................ 140,854
  owner + pet, IDENTICAL .... 15,551   <- the duplication (75% of owner+pet groups)
  owner + pet, different ....  5,234   (owner >= pet in 4,026; owner < pet in 1,208)
  pet-only ..................  1,642   (e.g. Firebolt (Wild Imp))
```

✅ **DISCRIMINATED at `3h` D2 (report 79 re-fetched 2026-08-07): the
duplication is ENDPOINT-SIDE SEMANTICS, faithfully double-ingested.** The
`character_spell_damage` payload states pet damage **twice**: merged into the
owner inside `rows[]` (`character_id` = the owner, `character_type:
"player"` — the Wild Imp's Firebolt 33,035 appears there under character
2310) **and** restated per-pet in `pet_spell_damage_by_owner` (same 33,035,
`is_pet: true`). `corpus.py :: ingest_abilities_record` ingests `rows[]` as
`is_pet=0` and the by-owner block as `is_pet=1`, both at face value — so
**`rows[]` is owner-MERGED, not owner-only, and the pet block is a
restatement, not an addition.** ⚠ Caught by a string/int trap on the way: the
payload's `spell_id` is a STRING, so an int-compare scan of `rows[]` reports
the pet spell absent — check with `str()` or `_int_or_none` when auditing
payloads. ⚠ The 1,208 owner < pet groups are NOT explained by this and need
their own look in the fixing session (partial windows or scope drift are the
candidates). 🚨 **Consequence one layer up:** `corpus.py:598-614` computes
`dps = (total_damage + pet_damage) / duration` where `total_damage` sums
`is_pet=0` rows — which already CONTAIN the pet damage — so **every
pet-owning character's logged DPS denominator is inflated by its pet's
damage counted twice.** That is the gate's own `logged_dps`, so the fix
moves deltas as well as coverage.

**Direction of bite, stated from the measurement rather than derived:** the
duplicated damage sits in both the matched and unmatched parts of the
denominator, so the sign of the coverage error is per-character. Removing the
duplicates **raised** cohort coverage on net (the dedupe run moved slice
accuracy *down*, 20.5% → 19.8%, and slice has coverage in its denominator),
i.e. the duplicated mass is mostly **unmatched pet spells** deflating
coverage today. The per-ability auto ratios for pet classes are roughly
**halved** by the duplication — and the rest of their deficit is E3 (pets
unmodelled), a different, named gap.

🛑 **DELIBERATELY NOT FIXED IN `3h`** (instrument session; Q3). **Green path
RUN at `3h` C4 and REVERTED**: deduping rows whose
`(spell_id, spell_name, damage_total)` appears with both `is_pet` values in
the same scope+character turns the check green (50.0), the harness then
correctly demands the registry entry leave `EXPECTED_FAILURES`, and the gate
under the candidate reads **1 / 1 / slice 19.8%** (from 20.5%, n=23 both,
counts unchanged) — the fix moves the gate, which is exactly why it belongs
to a commit that owns that pair. ⚠ The candidate keeps the owner copy; the
fixing session should first run D2's discriminator and fix at the **ingest**
layer if that is where the duplication lives, with the consumer dedupe as the
fallback seam.

---

## E6 — `fast_sim`'s first filler consumes the entire GCD budget — ✅ FIXED (`3e` B1)

> ### ✅ Closed 2026-08-06, session `3e` Block B1. The record below is what was found; this box is what happened.
>
> **The check was rewritten to bite first, and it failed as predicted.** The old
> form counted abilities that did *any* damage and passed at 11 acting abilities
> on the DoT caster **while zero of that board's eight fillers cast even once**.
> Re-stated about fillers specifically, it read **1 of 7** (cp_melee) and
> **0 of 8** (dot_caster).
>
> **What was actually wrong was bigger than the line cited.** `gcd_budget = 0.0`
> is arithmetically identical to `gcd_budget - casts * occupancy` for an
> unbounded filler, so that statement alone was redundant rather than wrong. The
> real defect is that **nothing bounded a filler's useful cast rate**:
> `expected_cast` scores a periodic event as `duration / tick` ticks **for one
> cast**, so a DoT treated as an unbounded filler is re-applied every GCD and
> **re-scores its whole duration each time**. That is the audit's predicted
> "DoTs re-cast every GCD" bug, live in `fast_sim`, masked only because those
> DoTs were getting no budget at all.
>
> **Fix:** one allocation rule for every on-GCD ability
> (`core/sim/tiers.py :: _useful_cast_interval`) — capped by its own useful cast
> interval (cooldown, periodic duration, or the **longer** of the two, since a
> refresh does not stack), capped again by the budget in front of it, consuming
> only what it uses. Both numbers come from the resolved ability; nothing is
> invented. Plus: an ability allocated **zero** casts is now **named in
> `warnings`** — it used to be completely silent, which is how a board whose
> entire filler tier never fires reported a clean rotation.
>
> **Gate impact, the honest version.** 5 of 36 → **4 of 36** within ±20%;
> qualified unchanged at 2; slice accuracy at the ≥20% floor 64.3% → **62.6%**.
> Only **7 of 36** characters moved and **every one moved down**. Chastie's
> `+13.1%` pass became `−27.9%`: it was passing *on the over-count*, at 4.6%
> coverage. **A criterion count went down because the model got more truthful** —
> the fake damage was removed and nothing was put back. Coverage did not move at
> all, because coverage is a membership test.
>
> ⚠ **It did NOT fix the DoT caster.** That board still allocates 0 of 8 fillers,
> because its nine cooldown abilities consume the entire GCD budget before the
> filler tier is reached. That is **E5**, and the strengthened check is
> registered against E5 for the `dot_caster` fixture until B3 closes it.

<details><summary>The original E6 entry, as written by <code>3d</code></summary>

| | |
|---|---|
| **Check** | `[cp_melee] / [dot_caster] fast_sim allocates GCDs to more than one filler` — **currently PASSING on both fixtures** |
| **Where** | `core/sim/tiers.py:137-141` — `gcd_budget = 0.0` after the first filler |
| **Predicted by** | §4.J |

Listed for `3e` even though the check passes, because the check is weak: it counts
abilities that did **any** damage, and both boards have enough cooldown abilities
to clear the threshold regardless of how the filler budget is split. The comment
two lines above the code says *"fillers split whatever budget the cooldowns left,
in priority order"* and the code does not do that.

🛑 **This is the tier the calibration gate runs on** — `fast_sim` is imported at
`calibrate_crawled.py` and called twice in its scoring loop (⚠ LINE NUMBERS REMOVED
IN `3f` F8: this citation has now drifted twice — it read `:70,426` until `3e` A6
'fixed' it to `:73,465,469`, which `3e`'s OWN A1 falsified in the same commit by
moving them to `:82,658,662`. A line number that has been wrong in two consecutive
corrections is not worth a third; `grep -n fast_sim tools/audit/calibrate_crawled.py`
answers it and cannot rot. The original drift note follows:) (⚠ this citation read
`:70,426` until `3e` A6; it had drifted) —
so it is the highest-consequence item on this page. Not registered as an expected
failure because it does not currently fail — but it needs a check that actually
bites, and writing one is part of `3e`.

</details>
