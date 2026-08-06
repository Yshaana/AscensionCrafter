# Engine bugs — defects in OUR code, found by the regression harness

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

**Every entry here is a FAILING CHECK in `tools/audit/check_sim_engine.py`.**
They are registered in that file's `EXPECTED_FAILURES` map, so they do not break
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

| # | mutation | red |
|---|---|---:|
| M1 | revert `session_mismatch`'s log side to `return None` | 1 |
| M2 | drop `config.ensure_utf8_stdout()` from `baseline_phase1.py` | 1 |
| M3 | remove `baseline_phase1`'s `RealmSeasonMismatch` handler | 3 |
| M4 | remove the `ValueError` guard in `_log_started_at` | 1 |
| M5 | point `closing_note` back at `args.*` instead of the resolved stats | 1 |
| M6 | remove `baseline_phase1`'s pre-flight phase assert | 1 |
| M7 | `EXCLUDED_SNAPSHOT_SOURCES = ()` | 3 |
| M8 | make `_decay_target_health` a no-op (pin target health at 100) | 1 |
| M9 | `detect_summons` returns `[]` | 3 |
| M9b | `detect_summons` returns rows with **wrong** spell ids (non-empty) | 3 |
| M10 | `_useful_cast_interval` returns a positive interval for everything | 3 |
| M11a | drop the manifest's frozen-arithmetic assertion | 2 |
| M11b | drop the manifest's scoring-loop assertion | 1 |
| M12 | drop the holdout carry-forward | 2 |
| M13 | treat CHILD phases as top-level in `phase_windows` | 2 |
| M14 | drop the horizon rule in `resolve_phase` | 2 |

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
| **Check** | ✅ **THREE registered failing checks** — `[cp_melee] / [dot_caster] / [frost_mage] fast_sim allocates GCDs to more than one filler`, all in `EXPECTED_FAILURES` (`check_sim_engine.py:78-102`). Also surfaced per ability as a `warnings` entry from `core/sim/tiers.py :: _mixed_damage_warning`. ⚠ The row read *"none yet"* until `3f` F8, contradicting this file's own line-15 invariant that every entry here IS a failing check |
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
| **Check** | 🛑 **STILL NONE — and unlike E7 that is accurate.** `grep -n channel tools/audit/check_sim_engine.py` returns comments only, so E8 is held by prose alone and breaches this file's line-15 invariant. It is NOT registered in `EXPECTED_FAILURES`, because a registry line is a claim that a check exists. **What would close it:** assert that a build containing a channelled ability (Blizzard, 10187 — the Frost Mage fixture already carries it) charges more than one GCD of occupancy for it, or that some warning names the channel. Both fail today. Deliberately not written in `3f`, which fixes no engine defects — see E9–E12, registered on the same terms |
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

## E13 — every white swing is ~78x over: `probabilities()` returns PERCENTS, `expected_swing` multiplies by them as FRACTIONS 🆕🚨

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
fractions multiplies every white swing by ~78. `expected_swing` returns
**11,573.6** for a weapon whose average hit is 240.7.

🚨 **THIS IS INSIDE THE CALIBRATION GATE, AND IT IS NOT A CORNER CASE.**
**24 of the 36 scored cohort characters carry a melee auto in their top 5 sim
abilities**, and one of them is **`Ari` (delta −9.7%, `Melee auto (MH)` its
single largest modelled source) — one of the gate's TWO qualified passes.** So
at least one qualified pass is standing on a 78x-inflated auto-attack. That is
compensating error of a size this project has not previously seen, and the
`3e` holdout result — *"the residual is not in the mechanisms"* — should be
re-read in its light: the residual may be a large positive error cancelling a
large negative one, which an aggregate criterion is structurally blind to.

🛑 **DELIBERATELY NOT FIXED IN `3f`.** The session's invariant is that no
commit moves the gate, and this fix moves it enormously — in the direction of
*more* under-production, since it removes damage from 24 of 36 characters.
It belongs in a modelling session with a before/after pair, exactly as `3d`'s
D3 discipline requires and as E9–E12 are handled below. **It is the first thing
that session should do**, because every other calibration number is measured
against a total that contains it.

⚠ Two things to check when it IS fixed, neither assumed here: whether the
`block` row should reduce damage rather than being dropped, and whether any
other consumer of `probabilities()` makes the same unit assumption
(`grep -rn "probabilities()" core/`).

---

## E14 — a periodic component with a 0.001s tick scores 12,000 ticks per cast 🆕🚨

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

🛑 **NOT FIXED IN `3f`** — same reason as E13. ⚠ Any fix must guard the general
case, not special-case this spell: a periodic event whose tick interval is
implausibly small (or whose tick and duration come from different spells)
should refuse and warn, per rule 2, rather than produce a number.

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
