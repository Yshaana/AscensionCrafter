# SESSION `3M` PRIMER — a deadline, four repairs, then the first real coefficients

> **`LIVE`** — the work order for session `3m`, drafted 2026-08-08 (morning) from
> `AUDIT_3L_ADVERSARIAL.md` (§5 is the source list, §5a the post-close additions).
> **SUPERSEDED BY `primer/Session_<date>_3m_*.md` when `3m` closes** — mark it in the
> close-out commit, not in a later cleanup.

**Audit implemented:** `primer/AUDIT_3L_ADVERSARIAL.md` (landed `851fc64`).
**Previous session record:** `primer/Session_2026-08-08_3l_tuning.md`.
**Monitoring primer:** `primer/CHAT_MONITORING_PRIMER.md` (v8, amended same morning).

---

## §0 — The rules

🛑 **`3m` is a REPAIR-then-MODELLING session. The gate is expected to move, and for
the first time in this arc some of it moves DOWN.** Two changes (RV rank, RV pool)
and one server patch (Improved Cleave) all *remove* modelled damage. That is the
correct direction when the previous number was wrong.

1. **No commit that can move the gate lands without a pre-registration that is its
   commit-parent.** `git log --format='%H %p %s'` proves it. A falsified prediction
   is reported, not rescued. An unexpected move is a finding: stop, commit the pair
   with its cause, no retroactive prereg.
2. **A quoted baseline must exist as a COMMITTED artifact derived from the current
   tree.** Rebuild, regenerate, commit, *then* predict.
3. 🆕 **NO PREREG MAY CARRY A ONE-SIDED FALSIFIER.** `prereg_3l_b_tuning.md:70`
   read *"Every delta moves UP (the sim only gains damage); any character moving
   DOWN falsifies the mechanism model"* — under which two of this session's three
   correctness repairs could not have been registered at all. State the predicted
   direction per mechanism and let the falsifier be symmetric.
4. 🆕 **EVERY MECHANISM SHIPS WITH A REGISTERED MUTATION — and `3l`'s four did not.**
   `git log --name-only a97b849..642f531` touches no test file; `check_sim_engine.py`
   is untouched across the whole `3l` range. **M57+ are yours.** Name the RED
   mutation *and* the change that turns it GREEN, and **run both** (`3g` G5, and
   `3g` E12's green path that only *looked* right).
5. 🆕 **A statistic over a changing population is not a fixed target — and this
   applies to the leg where `n` stays the same.** `3l` derived P4b and applied it in
   one direction; the 26.3 → 33.5 leg had n=23 on both sides and was pure membership
   swap. **Publish a same-member number beside every published median** (Block A).
6. **No coefficient is fitted to the parse it must later check.** Diagnose the
   mechanism with provenance; what you cannot build from provenanced data is a
   **named refusal**.
7. **Never quote coverage as progress toward the gate.** Absent share and slice
   accuracy are reported together, every time either appears.
8. 🆕 **When a session seeds a fact from an extract, read the sibling fields in the
   same rows.** The audit's two worst findings (RV's rank ladder, aura 344) were
   each two columns away from a number `3l` had already read correctly.
9. **The holdout stays unspent** unless the owner explicitly spends it. At 0 passers
   there is nothing for it to validate.

---

## Pre-flight — cannot move the gate; land it in one commit (plus the canary, which
gets its own)

1. **Census.** This file and nothing else is new in `primer/` at pre-flight →
   regenerate `CLAUDE.md`'s pasted census block **in the commit that adds it**, or
   `[A4]` fails at your first commit. Do not retype it: run
   `py tools/audit/check_refusals.py`, paste the `[census]` line it prints.
2. **`check_refusals.py` prints its own arm count** (`len(PASSED) + len(FAILURES)`).
   The `3l` record says 74; the tree has 77. A number in a document with no tool to
   emit it has no owner (`AUDIT_3L` F11).
3. **The additive-transition warrant** (`AUDIT_3L` F16). Zul'Gurub and Phase 1.1 went
   `is_active: False` overnight; the two-active overlap lasted under ~12 h. **The
   rule stands, the reason does not.** Correct `CLAUDE.md`, `PROGRESS.md`,
   `season_config.py`'s docstring and `core/builds/phases.py`; **annotate**
   `predictions/prereg_3k_b0_phase_flip.md` rather than rewriting it — it records
   what was decided on the day and is a `FINDING`.
4. **`CALIBRATION_TOLERANCE.md`'s derived prose** (`AUDIT_3L` F11). `3l` regenerated
   the asserted band table and nothing around it: `:246` "At **26.3%**…", `:249`
   "a **3.8×** rise", `:204` "roughly **ONE QUARTER**", and the `3i` A5 annotation's
   "37.6% (n=19) / 26.3% (n=23)". Either regenerate those sentences from the tool or
   move them into generated output. **Third time this file has gone stale inside its
   own assertion's blind spot.**
5. **The `3l` record's slot-17 sentence** (`AUDIT_3L` F10) says the detector maps
   neither slot-17-only nor stray rows. It maps the 36 slot-17-only rows to
   `off_hand`, silently. Append the correction (the record is `HISTORICAL`; append,
   don't rewrite).
6. **THE CANARY, its own commit** (`AUDIT_3L` F17). `canary_check` normalises by run
   count; leaderboard volume is driven by **active phases × locations × difficulties
   × roles**. ZG going inactive dropped it 12.0 → 2.0 rec/run (−83%, threshold 50%),
   so the daily job now fails at **every logon** and cannot be satisfied. Normalise
   by active-phase count (or attempted-vs-written queries); **keep the absolute
   zero-floor arm unchanged**. 🛑 **Do not raise `CANARY_DROP_RATIO`** — that is
   redefining a check after seeing its result. Ships with its RED mutation. Precedent
   for the hand-commits in the meantime: `7f28c4e`.

---

## Block A — instrument BEFORE anything gate-capable, then commit the baseline

Everything in Blocks B–D moves a number. None of it is readable until the instrument
can say what moved. This is `3l`'s B0 discipline applied one level up.

**A1 — the same-member slice** (`AUDIT_3L` F1, the headline finding). Add to
`gate_manifest_3e.json` a `slice_delta_vs_previous_run` block: the previous run's
band membership, this run's value over that fixed membership, and both `n`s. Measured
for `3l`: published **26.308 → 30.426 (+4.12 pp)**; same 22 members **30.635 →
30.425 (−0.21 pp)**. 🛑 **Quote the pair everywhere either number appears.** Then
append the correction to `PROGRESS.md`'s `3l` block.

**A2 — `not_scoreable_below_coverage_floor` is a lie by name** (F8). At `642f531` its
13 = 10 below-floor + **3 NOT ADMISSIBLE**, one of which (Boomcat, 82.2%) has the
cohort's *highest* coverage. `calibrate_crawled.py:1094`'s console line already
excludes them and calls the alternative "actively MISLEADING"; the JSON contradicts
the console the same function prints. Split it by reason, or carry a reason field —
a third `None` cause arrived in `3i` and the survivor key absorbed it, so a fourth
will too. **Also publish the admissible-only slice beside the headline**: measured
26.31 (n=21) → 30.43 (n=20) → 27.40 (n=21).

**A3 — the four soft check arms** (F9), one line each, all four verified
comment-satisfiable or fixture-blind by the audit:

| arm | site | fix |
|---|---|---|
| `[3k-B3]` 4 | `check_refusals.py:976` | 🚨 pure `inspect.getsource` substring — call the function with `build_spec=None`, `crit_damage > 0`, assert the string is in the returned `warnings` |
| `[3l-B0]` 2 | `:1040` | fixture's only producing group has two ratios so median == mean — add a third row |
| `[3l-D2]` 1 | `:1191` | all `amounts_max` fixture values non-negative — make one negative |
| `[3l-C1]` 2 | `:1120` | add `rc == 2 and "REFUSED" in text` to the conjunction |

**A4 — commit the baseline.** Rebuild `builds.db` from the current tree, regenerate
`gate_manifest_3e.json` and `per_ability_summary.json` with A1/A2 in them, commit.
Every later prereg cites this artifact. **Nothing after this point is registered
against an uncommitted number.**

---

## Block B — 🛑 DEADLINE: MONDAY 10 AUGUST. Improved Cleave.

Changelog `2026-08-07T21:32:22`, `[Darkmoon] [Dawnrise]`: *"[Going Live Monday, 10
August] Fixed a bug where **Improved Cleave increased hybrid Cleaves weapon damage,
rather than only their bonus damage.** Regular Cleave was unaffected. … eligible for
reset at Gabril Mewell."*

**This is `2b`/`2c`'s finding declared a bug by the server.** The project read
`EffectMiscValue = 8 = SPELLMOD_ALL_EFFECTS` over the tooltip's *"increases the
**bonus** damage"* — correctly, per its own standing rule — and modelled ×2.20 on the
whole ability (`talents.py:187`; `damage_multiplier` is whole-ability). Ascension now
says the tooltip was the **intent** and `ALL_EFFECTS` was the broken delivery. Same
family as `2d`'s Duality lesson, **fired in the opposite direction: here the numeric
field was the bug and the prose was right.**

`0.65·W + 2.2·(9 + AP)` replaces `2.2·(0.65·W + 9 + AP)`. The delta is
`1.2 × 0.65 × W` — **a pure weapon term, so the nerf scales with weapon damage.**

**B1 — 🛑 owner decision, then a stamp.** Does the sim model **intended** or
**delivered**? The primer's own `2d` practice says: *model the intended behaviour,
record the shortfall as a dated impairment.* ⚠ But every existing
`SYSTEM_IMPAIRMENTS` record (`core/builds/stats.py:97`) is *delivered < intended*,
and this is the first *delivered > intended* case — **check the record shape, don't
assume it.** Whatever is decided is stamped before it is coded.

**B2 — reconcile the seed and the code.** `seed_confirmed.py:103`
(`improved_cleave_true_magnitude`) already states the **fixed** formula
(*"applied to the AP-scaling bonus term only … `(9+AP)*2.2`"*) while `talents.py`
applies `ALL_EFFECTS`. They have disagreed since `2b` and nobody noticed, because
both readings produce a defensible number and only one is executed. Monday makes the
seed right.

**B3 — prereg, and this is the cleanest one the project will get.** The direction is
known *in advance*, which almost never happens. Register: which cohort members hold a
hybrid Cleave; the predicted per-member delta from their own weapon and AP; the
predicted slice/absent/producing-median move, **published and same-member**; and what
is NOT predicted.

**B4 — the corpus split, and it is the sharp one.** Every parse in the tree is
**pre-fix**. The cohort was frozen 2026-08-06, so it stays internally consistent —
but **no capture taken from Monday onward is comparable to it** for a hybrid-Cleave
character. Decide and write down: does the frozen cohort stay pre-fix (and the sim
therefore model delivered-as-of-freeze), or does it get re-read post-fix? 🛑 This is
a stamp change with the `3h` D4 rules in full if it touches admissibility.

**B5 — the owner's own build.** He runs Lightbound Cleave on a Hammerdin with The
Light's Hope, so this is his largest single nerf of the season, and Improved Cleave
is resettable at Gabril Mewell from Monday. Once B3's numbers exist, say plainly
whether the card is still worth its slot — that is what the toolkit is for.

---

## Block C — the four correctness repairs. Own preregs; two move the gate DOWN.

**C1 — Righteous Vengeance's rank** (`AUDIT_3L` F3). `swings.py:79` is
`RIGHTEOUS_VENGEANCE_FRACTION = 0.30`, flat, while the three card ids decode
`EffectBasePoints` 9 / 19 / 29 → **10% / 20% / 30%** (re-derived from
`data/source/dbc/dbc-extract.json` by the audit). `tiers.py:894` is a **membership**
test that throws away the rank the id encodes; `snapshot_cards.rank` is never read.
A rank-1 holder is credited **3×**. Direct hit on the standing rank rule. Map card id
→ fraction; register the flatten-to-0.30 mutation.

**C2 — Righteous Vengeance's white-crit pool** (F4). `3l` added white-swing crits to
the pool (`tiers.py:883`). RV's own client text reads *"**Direct** critical strikes
with **spells and abilities**"*, and `core/builds/stats.py:234` asserts that exact
wording **excludes autos** — three files away. Measured on the committed logs (68
player-rows logging 61840, periodic crits excluded): widening the pool makes the
prediction worse in **49 of 49** rows carrying white crit; OLS through the origin
gives the white-crit coefficient **−1.25**, not +0.30. **Default: RETRACT.** If it
is kept, it needs an `open_questions` slug and a `warnings` line — it currently
enters the gate silently.

**C3 — aura 344 is flat ATTACK POWER** (F5). `seed_confirmed.py:361` and
`seed_epistemics.py:181` call it the per-hit speed-scaled damage parameter and defer
it to `3m` as the delivery block. Spell 200809's own template says otherwise:

```
"...increasing Holy Spell power by $200819s2 and your attack power by $200819s3
 Each auto attack and melee ability causes $/77;200819m1 to $/25;200819M1
 additional Holy damage, based on the speed of the weapon."
```

`$s2` = effect 1 = aura 345 = Holy SP ✅. `$s3` = effect 2 = **aura 344 = attack
power**. The per-hit speed-scaled term is effect **0** (DUMMY, base 410…6627,
`RealPointsPerLevel` 19.0), divided by 77 and 25 — *stated by the client, not
underived*. Corroboration: aura 344 has 42 effects in the same extract,
`EffectMiscValue = 0` on all 42, and the 33 non-Consecrated ones are without
exception attack-power modifiers. ⚠ This string is already quoted verbatim in
`seed_confirmed.py:278` — **two confirmed facts in one file disagree.**
Consequences: rank 6 grants **+73 raw AP per weapon** (~+146 dual-wield), unmodelled
and unseeded; and `2e` measured "+88 AP per imbue (post-Deadliness)" against a raw 73
→ a ~×1.21 residual that is itself a finding, and asymmetric against aura 345's exact
86-vs-86.

**C4 — `rank_for_level` disagrees with the seeded +86** (F6).
`rank_for_level(conn, 200824, 60)` returns **rank 5 → +40**, because rank 6's
`SpellLevel` is 64. For an *enchant* line the gate is
`SpellItemEnchantment.min_level` (rank 6 = 55, rank 7 = 63), not `SpellLevel`. The
measurement settles which gate is right; nothing records that they disagree, so the
next caller through the canonical resolver gets 40 and no warning. Fix or warn — do
not leave it silent.

**C5 — register the four missing mutations** (F2, and §0 rule 4). `WEAPON_SLOTS` →
`{16,17}`; delete the AP term; restore `if mh <= 0: return`; force the slot detector
to one branch. **And repair E13** (`check_sim_engine.py:1046`): its `_CS` fixture has
no `attack_power`, so `getattr(..., 0.0)` runs `3l`'s AP branch **off**; with
realistic AP its own ceiling breaks at ~3,342 (1H) / ~4,828 (2H) and it reports a
unit error that does not exist.

**C6 — while you are in there** (F10): key the stray weapon-slot check on the slot
**index**, not the mapped name, so a slot-17-only snapshot cannot silently become an
off-hand.

---

## Block D — E2: the first per-parse coefficients the project has ever had

✅ **Unblocked.** The 2026-08-08 crawl advanced the payload horizon to
`2026-08-08T07:05:29Z` (committed `7f28c4e`), past the MC log's end at 20:03Z on
08-07. **All six Elric stat blocks are phase-resolvable.**

**D1 — own prereg**, separate from everything above: what the stats feed, which
refusals may convert to verdicts, falsifiable expectations, what is NOT predicted.
This is the T5 unblock for `infer_coefficient`'s `refused:no_per_parse_stats`
(`core/builds/inference.py:350`), which gates **Phase 3 criteria 3-full and 4**.

**D2 — 🛑 window on GUID, and pick the kill GUID explicitly** (`AUDIT_3L` F13).
`3l`'s *"one pull, never two encounters"* is true of the GUID it checked and **invites
the mis-window it was written to prevent**. Measured from the bytes:

| boss | GUIDs | note |
|---|---|---|
| Gehennas | 2 (`…000058` wipe 19:52:51–19:54:56, `…000994` the kill) | 100 s apart, both in half 1 |
| Magmadar | 2 | wipe, then kill |
| Garr | **4** | three failed pulls before the kill |
| Baron Geddon | 3 | no kill |

First-mention → `UNIT_DIED` on Gehennas spans **604 s**, folding in a 100 s wipe and
160 s of downtime — deflating DPS on the capture whose entire value is per-parse
calibration.

**D3 — predicate 2 (deaths > 0) stays UNARMED** unless the owner stamps it. Arming it
from log-sourced deaths is a stamp change with the `3h` D4 rules in full, not a
drive-by.

---

## Block E — delivery modelling. Default: DEFERRED WHOLE to `3n`.

Absent mass is 58.8% and dominated by trigger-delivered damage — it is the
load-bearing problem and it is *not* what this session is for. Blocks A–D are a full
session on their own, and B has a hard deadline. **If the owner pulls it in, it gets
its own prereg.** With C3 applied the block is: seal per-proc (20424 — 35% weapon,
Holy, **delivery**-blocked not extraction-blocked, corrected `3l`); imbue per-hit
(effect 0, divisors 77/25, *stated*); Plague Swarm 276445 (5.96%, resolution
complete, **146×** gap); school-variant and extra-attack autos; Deep Wounds / Ignite /
diseases.

**Carried, named, not chased:** Devour Mind 287865 (6.63%, largest single absent key
— **third deferral**, register or explain); Elemental Blast 954892 (mechanism
unpinned); the AP term's `retail_hypothesis` warning cannot reach the gate artifacts
(`[:8]` truncation, no warnings field in the manifest, no `ENGINE_BANDS` entry);
`WEAPON_SLOTS` exists in three conventions across three tools; raid duration 78.1 s
is quoted to 0.1 s against SE(median) ≈ 10.2 s.

---

## Standing decisions needed from the owner — ask at session START

1. **Improved Cleave: model INTENDED or DELIVERED?** (Work-order lean: intended, with
   a dated `SYSTEM_IMPAIRMENTS`-style record for the pre-Monday state — but the record
   shape is untested in this direction, so it is a real decision.)
2. **The frozen cohort across the Monday split:** stays pre-fix, or re-read after?
3. **Delivery modelling in `3m` or `3n`?** (Default: `3n`.)
4. **Holdout:** unspent by default. At 0 passers there is nothing to validate.
5. **Predicate 2 arming:** stays unarmed by name unless stamped.

---

## Close-out (its own commit, per the established pattern)

Session record `primer/Session_<date>_3m_*.md` (born `HISTORICAL`) with the §0
commit-by-commit gate table and the prereg→code parent pairs; `PROGRESS.md` top block
replaced, `3l` block collapsed; **this file marked `SUPERSEDED BY` the record**; final
gate manifest from a clean tree; all three harnesses run and exit codes cited; census
regenerated in every commit that touches `primer/`; the honest NOT-done list; and the
**published + same-member slice pair** quoted together wherever either appears.

## What `3m` should hand to `3n`

A gate whose remaining error is delivery rather than arithmetic; an instrument that
reports composition alongside every median; four mechanisms with mutations behind
them; the Improved Cleave question answered before the patch rather than after; and
`infer_coefficient` producing verdicts from real per-parse stats instead of refusing.
