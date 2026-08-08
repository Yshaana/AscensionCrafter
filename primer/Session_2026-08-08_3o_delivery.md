# Session `3o` — 2026-08-08 — the one-button capture, a constant that executed wrong, and two delivery mechanisms that refused to be modelled

> **`HISTORICAL`** — the record of session `3o`, written at its close. A past
> session; **may contain claims that are false today, and that is correct.**
> Work order it ran: `primer/SESSION_3O_PRIMER.md` (now `SUPERSEDED`). Audit it
> implemented: `primer/AUDIT_3N_ADVERSARIAL.md`. The owner answered four
> stop-points at session start; one carried its stated default.

## §0 — Commit by commit, with the gate at each

| commit | what | within/qual | slice (n) | producing (n) |
|---|---|---|---|---|
| `8a75a2e` | pre-flight: `AUDIT_3N` F2/F3/F4/F6 + a site the audit missed | — | — | — |
| `5625e4b` | **Block A baseline** | 0 / 0 | 30.150 (24) | — |
| `63f295e` | Block A per-ability baseline | 0 / 0 | 30.150 (24) | 0.2571 (123) |
| `3cafc41` | re-stamp the asserted blocks | — | — | — |
| `0157f64` | **Block B**: the `/ace` session capture addon | — | — | — |
| `d3d1177` | Block B: pairing tool generalised, F7 gap derived | — | — | — |
| `fcb1ec6` | **PREREG** — the imbue AP constant | — | — | — |
| `8d9f591` | **Block C**: `attack_power` 88.0 → 80.0 | — | — | — |
| `8a755a5` | Block C manifest | 0 / 0 | **30.150 (24)** | — |
| `6235c36`, `f13a57b` | Block C per-ability | 0 / 0 | 30.150 (24) | **0.2571 (123)** |
| `7b64cbe` | Block C: the unification + the AP-inert finding registered | — | — | — |
| `7569573` | **Block D**: the fixture blind spot closed (M73/M74) | — | — | — |
| `9e60061` | **Block E**: two delivery mechanisms measured, both refused | — | — | — |
| `b0c118b` | **Block G**: E1 registered with its trigger | — | — | — |
| `38629d6`, `610bcd0`, `518a27f` | close-out artifacts, clean tree | 0 / 0 | **30.150 (24)** | **0.2571 (123)** |

**Prereg parenthood:** `fcb1ec6` → `8d9f591`, a direct commit-parent. It is the
session's only gate-capable code change.

**THE GATE DID NOT MOVE, AND THAT IS THE CORRECT RESULT.** Slice
`30.150% → 30.150% (n=24)`, published Δ **0.0 pp** AND same-member Δ **0.0 pp**,
membership unchanged. Producing median `0.2571 (n=123) → 0.2571 (n=123)`,
published Δ **0.0** AND same-member Δ **0.0**, 0 rows dropped, 0 added — **both
pairs quoted at the same endpoints, baseline→close.** Absent share **59.0%**,
unchanged. Admissible-only **27.62% (n=21)**.

## §1 — Owner decisions

Four answered at session start; one took its stated default.

1. **Delivery scope beyond the floor** — Plague Swarm 276445 next if room. *(No
   room: the floor's own two mechanisms consumed the block, §5.)*
2. **E1** — register the trigger, do not land it. *(Registered, §7.)*
3. **The 88-vs-80 imbue delta** — the owner supplied the answer himself, §4.
4. **Addon smoke test** — training dummy, right after Block B lands. *(Pending
   the owner; the addon is committed and testable, §3.)*
5. **Holdout** — unspent (default). Not read. **Predicate 2** — UNARMED.

## §2 — Pre-flight, and a rule that paid inside its own first hour

`AUDIT_3N`'s four documentation findings, repaired. Two are worth the record:

🚨 **F4's second half is FALSE, and the truth is sharper than the finding.** The
audit said the admissible-only slice "has no emitter (the manifest has no such
key — checked)". It has had one since `3m` A2 (`7c5db49`), and the manifest the
audit itself read carries `median_slice_accuracy_pct_admissible_only = 27.619`.
**The emitted value was sitting in the artifact while the close-out typed a
different one beside it.** So the defect was never a missing emitter — it was an
emitter with **no assertion**, which is `[3j-C3]`'s lesson exactly. Fixed by
rendering it into `CALIBRATION_TOLERANCE.md`'s derived block, where `[3m-A0]`
now asserts it.

🚨 **RULE 8 PAID IMMEDIATELY, ON THE SESSION'S FIRST GREP.** Grepping for the
**value** `9+AP` found `core/sim/talents.py:146` writing the Improved Cleave
bonus term as `2.2·(9+AP)` — a doubly-retracted magnitude **inside the module
that implements the fix**, and not one of the two sites the audit named. Prose
siblings are found reliably now; this was a **code comment**, which the
sentence-grep does not reach and the value-grep does.

Also: `[A4]` was **RED on the session's first harness run**, because the
oversight chat's own commit landed four documents without regenerating the
census. The assertion caught it in minutes. Census 78 → **81**.

## §3 — Block B: the addon, and the first one this repo can test

`/ace start` turns combat logging on and **verifies it by reading the state
back**, takes one full export, and snapshots stats at the first and last instant
of every combat. `/ace snap`, `/ace status`, `/ace stop` (one copyable blob),
`/ace resume`. Bare `/ace` and `/acexport` keep their original behaviour.

The stat emitter is **factored out and shared**, so `pair_parses_to_stats.py`
ingests a session blob unchanged. `Target:` carries the enemy GUID or the literal
`none`; `WeaponMH:`/`WeaponOH:` carry itemStrings whose second field is the
enchant id — **the imbue rank per parse**, which no stat number carries.

🆕 **`tools/audit/check_addon_lua.py` loads the addon into a real Lua 5.1 runtime
(the client's own version, via `lupa`) behind a stubbed WoW API, dispatches the
slash commands, fires the combat events and asserts on the output: 14/14.** The
addon was previously verified only by the owner installing it and playing, which
is how `2026-08-06c` shipped two real bugs.

⚠ **One of my own arms was vacuous and is fixed in the same commit.** The first
logging arm read `("...verified ON" in blob) or True` — green under every
possible mutation. Kept in the comment, because the shape is the point: an arm
ending `or True` is not a weak check, it is not a check.

⚠ **A false alarm, recorded because the reasoning was wrong even though the
outcome was fine.** I inferred from a two-field header in the committed addon
that the owner's installed copy was newer, and asked him for it. It is
**content-identical**. `GetRealmName()` returns `"Darkmoon - Season 10
Wildcard"` — a realm name with an embedded `" - "`, which is why the header
parses into three fields. **Both parsers depend on that accident.**

**F7, and the fix restores an agreement that had been silently lost.** The
crash-gap constant read whole seconds (60.0) under a comment claiming it was
measured from the log files' stamps; the stamps give **59.764 s**. Gehennas logs
**320.084 s**, not 319.848 — and `3m`/`AUDIT_3M` both published **320.1** from
the same bytes, so `3n`'s 319.8 had been disagreeing with its predecessor
without saying so. `logged_seconds` is the denominator of every per-parse
coefficient, and truncating a gap upward inflates DPS one-directionally.

## §4 — Block C: a constant that executed wrong, and a prediction that failed

`CONSECRATED_WEAPON_IMBUE.attack_power` **88.0 → 80.0**, at the one site where
it executes (`AUDIT_3N` F1). `3n` retired the +88 in both seeds and left it
running in the gate pipeline for 6 of 35 members.

🚨 **THE 88-VS-80 QUESTION IS ANSWERED, BY THE OWNER, AND IT IS REGISTERED
RATHER THAN MODELLED.** `2e`'s +88 was measured with **Blessing of Kings up**
(its steps 4→5 read AP 258→346, gear identical); the 2026-08-08 three-step was
**unbuffed**; and **80 × 1.10 = 88 exactly**. Since **1.21 = 1.10 × 1.10**, this
is almost certainly the *same* mechanism as the standing
`str_to_ap_1_21_under_buffs` question — one second ×1.10 on attack power under
buffs, seen in two places, not two puzzles. **Nothing applies that multiplier.**
The discriminator is stated before the capture: one export pair, **Kings alone
up vs unbuffed, predicting +88 against +80**.

🚨 **P2 WAS FALSIFIED, AND THE DIAGNOSIS IS A BIGGER FINDING THAN THE FIX.**
The prereg predicted all 6 holders' damage would fall; **one** moved. Probed by
raising the imbue AP to 8000/weapon and re-running the gate:

| member | probe move | verdict |
|---|---:|---|
| Xyz | **+47.170 pp** | AP-sensitive |
| Blix | **+2.520 pp** | AP-sensitive |
| Lootgoblin | **+1.190 pp** | AP-sensitive |
| Deyindra | **0.000 pp** | **AP-INERT** |
| Nodding | **0.000 pp** | **AP-INERT** |
| Xoller | **0.000 pp** | **AP-INERT** |

**Half the imbue holders are structurally attack-power independent** — fifteen
thousand AP changes their modelled damage by exactly nothing, so no AP
correction can ever reach them. Two candidate causes are recorded **without
choosing between them** (no AP term in the kit; or white swings fully replaced
after `3n` leg 2 — Nodding and Deyindra carry two next-swing abilities each).

Scored: **P1 ✓ · P2 ✗ · P3 ✓ · P4 ✓ · P5 ✓ · P6 ✓ · P7 ✓ · P8 ✓ — 7 of 8.**

⚠ **My first population count was wrong and would have been a confidently
falsifiable lie.** `snapshot_cards` carries both `spell_id` and
`card_spell_id`; `derive_buffs` matches the latter, the corpus stores this card's
`spell_id` as the rank sibling **200814** against `card_spell_id` **200809**, and
querying the wrong column returned **0 of 35**. A wrong-column zero and a real
zero are indistinguishable by eye.

## §5 — Block E: delivery opened, and both mechanisms REFUSED

Absent mass **59.0%**. It is a long tail: the largest single key is 6.63%.

**1. The imbue chain is confirmed on its sheet grants; its per-hit term is not.**
Enchant 23392 → hidden spell **200824** (rank 6) decodes aura 345 = **86** and
aura 344 = **73**, matching the measured +86 raw Holy SP and the +80 observed AP
(73 × 1.096) exactly — independent validation of the rank ladder. But the stated
per-hit form (`$/77;…m1 to $/25;…M1`) implies a **max/min ratio of 3.08**
whatever value is fed through it, and the log gives **three discrete values —
240 ×37, 270 ×13, 287 ×1 — a ratio of 1.196**. Same-session weapon speeds
(3.63 / 3.53, ratio 0.972) do not explain the 240-vs-270 split (0.889) either.

**So 200818 stays ABSENT for the 6 members holding the card, deliberately.**
Modelling from a form that does not reproduce would add phantom damage to
exactly those characters. The clue is recorded: counts of 37/13/1 look like
distinct **states**, not a roll.

**2. Devour Mind: the card hypothesis is ELIMINATED.** Pre-flight answered branch
(1) — no trigger edge reaches 287865. Branch (3), done mechanically: 18
characters log it, 12 have a board linked to the scope they logged it in, and
intersecting those 12 on `card_spell_id` gives **zero** common cards. The zero is
real, not a broken query — every board holds exactly 55 cards, pairwise overlaps
run 0–34 (mean 10), and the most widely shared card reaches 9 of 12. Remaining
candidates: a non-card source, or an incomplete board capture.

⚠ **I hand-indexed log columns on the first pass**, which `CLAUDE.md` forbids by
name because it produced `2e`'s only parsing error. The numbers agreed, but the
finding rests on the re-run through `combat_log_parser.py`'s named fields.

## §6 — Block D: both mutants the audit found green now go red

Every fixture held exactly ONE next-swing ability, so `AUDIT_3N` F5 ran two
natural mutants against `3n`'s headline fix and **both stayed green**.

New fixture from a real crawled board (snapshot 76): **two** next-swing
abilities on **two** weapons. ⚠ **The first candidate was rejected after being
measured**: snapshot 78 carries three next-swing Cleaves — a stronger *sharing*
test — but all three resolve to the **same 283 damage per swing**, so the
*ordering* arm could not discriminate any order from any other. The chosen
board's two differ genuinely (268 vs 121 per swing).

- **M73** (decrement deleted) — RED with the predicted signature, joint casts
  **38.951 = 2 × 19.475**. 🚨 **`cp_melee` still PASSES under the same mutant**,
  which demonstrates the old fixtures' blindness rather than asserting it.
- **M74** (off hand reduced too) — RED: the off-hand row disappears entirely.

🛑 **`build_nonpaladin_fixtures.py` destroys hand-added blocks**, found by
running it: regenerating dropped the `ground_truth_absent` records (`3f` F9)
from both existing fixtures, and nothing failed, because no check reads them.
Restored, carried forward, and the trap documented in the script itself.

## §7 — Block G: E1 registered with its trigger

Owner decision: register, do not land. The trigger is stated in the form that
cannot be silently skipped — **before the first post-2026-08-10 parse of a
card-holding cohort member is COMPARED to anything pre-fix**, not before the
next capture. The frozen cohort is entirely pre-fix and the owner holds the card
**0/3**, so nothing is contaminated today. Both free detectors are named.

## §8 — NOT done, explicitly

1. **Nothing was added to the model, so the absent share did not move.** Block E
   measured two mechanisms and modelled neither. That is the honest headline.
2. **The imbue per-hit term is unmodelled**, with its form unknown and its next
   step named (bucket the hits by the event they accompany).
3. **Devour Mind's source is unidentified** — narrowed by two eliminations.
4. **Seal of Command 20424 was not reached** (1.48%, 4 members). The floor's
   first two items consumed the block.
5. **Plague Swarm 276445** — the owner's answer for "if room remains". There was
   none.
6. **The ×1.141 LBC residual is still unscored** (Block F), a third session.
7. **E1 not landed** — registered with a trigger instead, by decision.
8. **The addon has not been smoke-tested in game.** It is verified against a
   stubbed Lua 5.1 client, which cannot tell whether Ascension exposes
   `LoggingCombat`/`UnitGUID` under those names or fires
   `PLAYER_REGEN_DISABLED` when this server thinks combat begins.
9. **Half the imbue holders are AP-inert** — measured, two candidate causes, not
   separated.
10. **The holdout stays unspent**; **predicate 2** UNARMED.
11. **Meritania's greedy swing budget** — still an allocation policy nobody
    stamped.

## §9 — Harnesses at close (clean tree)

| harness | result |
|---|---|
| `check_refusals.py` | exit 0 — **`[arms] check_refusals.py: 102 arms — 102 passed / 0 failed`** |
| `check_core_purity.py` | exit 0 — 52 files, 0 violations |
| `check_sim_engine.py` | exit 0 — all checks pass |
| `check_addon_lua.py` | 14/14 against a stubbed Lua 5.1 client (optional, needs `lupa`) |

⚠ **The arm count moves with the WORKING TREE'S cleanliness**, not only with
added arms: the `[A7]`/`[E6]` fixtures exercise the dirty-tree manifest refusal,
which cannot be tested on a clean tree, so a dirty tree runs four arms a clean
one does not. Cite the clean-tree line. Census regenerated in every `primer/`
commit.

## §10 — What `3o` hands to `3p`

1. **A one-button capture addon**, testable in CI-like isolation for the first
   time, waiting on one dummy run.
2. **The imbue constant correct where it executes**, and its buffed-state
   residual unified with a standing question and given a one-capture
   discriminator.
3. **`3n`'s clock fix protected** by the two mutations that previously could not
   fail.
4. **Delivery measured rather than guessed**: two mechanisms with their evidence,
   their refusal, and their named next step.
5. **A modelling gap nobody had seen** — half the imbue holders are AP-inert.
6. **E1 carried with a trigger**, not a hope.
