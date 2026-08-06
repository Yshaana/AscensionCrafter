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

## E1 — `combo_points` is never incremented, and `is_finisher` never fires either

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

---

## E2 — execute windows are dead code, and nothing says so

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

---

## E3 — no pet model, while the corpus DPS being calibrated against includes pets

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

---

## E4 — the APL grammar cannot express DoT uptime

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

---

## E5 — 6 of 7 DoTs on a DoT-caster board never enter the rotation

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

---

## E6 — `fast_sim`'s first filler consumes the entire GCD budget

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
