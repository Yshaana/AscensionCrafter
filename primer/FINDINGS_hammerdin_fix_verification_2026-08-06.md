# Findings — tracker #200295 verified, and what it did NOT fix

> **`FINDING 2026-08-06`** — point-in-time analysis, true as of its date and **not maintained since**. Not citable as current truth without re-checking against the tree. *(Classified `3f` F8c, 2026-08-07.)*

**Written by:** the monitoring chat, 2026-08-06 late evening, from the owner's paired
capture. Bundle and provenance:
`data/source/captures/2026-08-06_elric_hammerdin_proc_retest/README.md`.

Three results. The reported bug is **fixed and measured**. The generalisation the `2d`
session predicted **did not happen**. And a third thing nobody was testing for turned up
in the stat blocks.

⚠ **Method note.** The first pass at this analysis hand-indexed the combat-log columns
and read `glancing` where it wanted `critical` — **the identical defect `2e` hit**, in a
chat that had written the rule against it into `CLAUDE.md` earlier the same evening. It
was caught only because crits came out smaller than non-crits, which is impossible. Every
number below is from `tools/log_parser/parse_log.py` or from indices that tool confirmed.
**The rule is not enough on its own; the arithmetic sanity check is what caught it.**

---

## 1. ✅ Tracker #200295 is FIXED — 0.8% → 17.2%

Window A, 258.5 s: 39 Holy Shock casts, 25 Judgement of Wisdom casts.

🛑 **Hour of Judgement was never cast** (0 events for `282984`/`282986`). That matters:
HoJ delivers Hammer from the Heavens periodically at a 500 ms period, ~20 pulses per
cast. With HoJ absent, **every HftH event in this window is a Hammerdin proc.**

13 HftH damage events → **11 distinct procs**. Two events land at a zero time gap on a
second target (`Azeroth Tank Training Dummy`), which is the ability's 8-yard splash, not
two procs.

| | `2d` — 2026-08-05 | this capture |
|---|---|---|
| Holy Shock | 1 / 78 (1.3%) | 4 / 39 (10.3%) |
| Judgement | 0 / 51 (0%) | 6 / 25 (24.0%) |
| unattributed (>1.5 s from either cast) | — | 1 |
| **Combined** | **1 / 129 — 0.8%** | **11 / 64 — 17.2%** |

Stated proc chance is 20% (`282983`, `proc_chance=20`). Expected at n=64 is
**12.8 ± 3.2**; observed 11 sits inside one standard deviation. Under `2d`'s measured
rate, 11 procs in 64 casts has probability far below any usable threshold.

⚠ **Do not read the per-ability split.** Holy Shock 10.3% against Judgement 24.0% looks
like a difference and is not one at n=39 / n=25.

### What this re-opens

| Re-open | Now correct again |
|---|---|
| `build_paladin-hammerdin.md` §11 rotation priority | "Press Judgement and Holy Shock" — `2d` had demoted both |
| build doc §2 class-tag table | Judgement / Holy Shock return as Hammerdin feeders |
| open question `hammerdin_trigger_set_excludes_trigger_delivered_damage` | **Close it** — but see §3, the mechanism did not survive |

⚠ These revert *as claims about the engine*. They do **not** rehabilitate the rest of the
build doc, which is stale on gear, path and stat weights — see
`primer/PLAN_V2_BLIND_REDERIVATION.md`.

---

## 2. ❌ The fix did NOT generalise — the discriminator answers cleanly

`2d` suspected a general cause: a *"damaging X abilities"* trigger being blind to damage
delivered by a **second** spell. If that generalised it would affect every proc engine on
the server. **A Hammerdin-only fix and a general engine fix are indistinguishable if only
Hammerdin is re-tested**, so the bug file specified a second engine with the same shape:
Purification By Light × Lightbound Cleave.

**Window B — Lightbound Cleave isolation, 235.2 s, 53 casts, 49 hits, 81 white swings:**

> **Zero Purification By Light output.** No Consecration (`270768`), no Exorcism
> (`270767`), from any spell id, from Elric, anywhere in the log.

**Window A is the control**, and it is a better one than `2d`'s because it is the same
session, the same board, 13 minutes later: **PBL fired there.** So PBL is alive, and
window B's zero is a real negative rather than an absent talent.

**Verdict: the fix was scoped to Hammerdin.** Primer §4's engine-intake practice — check
whether an ability damages with the spell you press, and never assume an engine's stated
intake — stands unchanged.

---

## 3. 🚨 NEW, and it damages the mechanism BOTH sessions assumed

Every PBL trigger in window A fires on the **same log timestamp as a Judgement**:

```
SPELL_CAST_SUCCESS   53408  Judgement of Wisdom
SPELL_DAMAGE         54158  Judgement            <- damage arrives via the SEAL
SPELL_DAMAGE        270767  Exorcism             <- PBL
SPELL_AURA_APPLIED  270768  Consecration         <- PBL
```

Both triggers attribute to Judgement. **Nothing else in either window produced one** —
not 130 white swings across the two logs, not 49 Lightbound Cleave hits.

**Two things follow, and they point in opposite directions.**

**(a) PBL's intake looks close to the inverse of its wording.** The card reads
*"weapon-damage spells and abilities"*. White swings are weapon damage and fed it
nothing. Lightbound Cleave is 65% weapon damage and fed it nothing. Judgement is **not**
weapon damage — it damages through the seal — and is the only thing that fed it.
`2d` established that LC feeds PBL zero; **nobody had established what does.**

**(b) It falsifies the `2d` mechanism as a general law.** The hypothesis was that
trigger-delivered damage is proc-blind. Judgement's damage *is* trigger-delivered
(`53408` pressed, `54158` logged). If the hypothesis held, PBL could not see it. PBL
sees it.

🛑 **n = 2. This is a hypothesis, not a finding, and it must not be written into a doc as
one.** Two PBL triggers from 25 Judgements is 8%, which is also not a rate — it is two
events. **The cheap decisive test is a Judgement-only window**, the same shape as the two
already run: press only Judgement for ~4 minutes and count Exorcism/Consecration against
casts. If PBL tracks Judgement at a stable rate and still ignores autos, (a) is real.

⚠ Until that runs, `hammerdin_trigger_set_excludes_trigger_delivered_damage` should be
closed as **"the specific bug is fixed; the proposed general mechanism is contradicted by
one observation and is not established either way"** — not as "the mechanism was right".

---

## 4. 🆕 Judgements of the Pure is +15% haste, and every haste field is blind to it

The two stat blocks bracket window A. The only fields that moved:

| | 21:47:06 (before) | 21:52:16 (after) | ratio |
|---|---|---|---|
| Frostbolt R11 cast time (`GetSpellInfo` probe) | 1708 ms | 1485 ms | **1.150** |
| Main-hand speed | 3.63 | 3.16 | **1.149** |
| `Rating_HasteSpell` | 15 | 15 | — |
| `MeleeHaste_raw_UNVERIFIED` | 1.02% | 1.17% | — |

Two independent fields agree on **+15%**. `Judgements of the Pure` (`53657`) was applied
25 times — once per Judgement cast — and is 3/3 on the board.

**This is the first live confirmation that the addon's `GetSpellInfo` cast-time probe
works as intended.** It was added in `2026-08-06c` specifically because the
`Rating_Haste*` lines are rating-derived and per primer v28 are *structurally unable to
see buff or talent haste* — the gap that made an external Swift Retribution aura read as
a permanent unexplained 3%. Here the rating line is flat, `GetMeleeHaste` is flat, and
only the probe moves.

⚠ **Displayed weapon damage also rose 11.5%** (526.1–627.7 → 586.5–705.1), which haste
alone does not explain — `Enrage` (`57520`) was applied 36 times. **Observed, not
diagnosed.** Do not derive a weapon input from the closing block.

---

## 5. Free calibration result — the cleanest Lightbound Cleave sample the project has

Window B is unbuffed, **no seal, no weapon imbue**, single target, one ability pressed.
Nothing to contaminate it.

| | |
|---|---|
| LC non-crit mean | **445.8** (n=37) |
| LC crit mean | 865.2 (n=12), crit multiple **1.94×** |
| Model: 65% weapon + flat 62, at MH avg 576.9 | **437** |
| **measured ÷ predicted** | **1.020** |

The formula reproduces within **2%**. This is independent confirmation of `2b`/`2c`'s
retraction — Lightbound Cleave R5 is 65% weapon damage plus a flat 62, **with no AP
term** — and it is a stronger test than the original, because attack power here is
**134** rather than 546. Any real AP coefficient would have produced a large miss at this
AP and did not.

⚠ LC crit rate 24.5% (12/49) does **not** discriminate the melee table (20.77%) from the
Holy spell table (37.58%) at this n. Do not read it.

---

## 6. Loose ends worth a line each

- **`Physical Quickness` (`840822`)** — 81 applications in 258 s. In the DBC extract, in
  **no** project doc. A very frequent proc on a build nobody has modelled it into.
- **`Siphon Health` (`18652`)** appears in both windows, 0% crit, still unattributed —
  same open item as `2e`.
- **`Righteous Smite` (`273123`)** fired 6 times in window A; it is one of the
  out-of-catalog spells `2e` flagged as carrying no coefficient.
- **Window A DPS is not a build number** (565 over a two-button window). Recorded so
  nobody quotes it as one.
