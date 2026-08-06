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
| **Check** | none yet — currently surfaced as a `warnings` entry from `core/sim/tiers.py :: _mixed_damage_warning` |
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
`calibrate_crawled.py:73` and called at `:465` and `:469` (⚠ this citation read
`:70,426` until `3e` A6; it had drifted) —
so it is the highest-consequence item on this page. Not registered as an expected
failure because it does not currently fail — but it needs a check that actually
bites, and writing one is part of `3e`.

</details>
