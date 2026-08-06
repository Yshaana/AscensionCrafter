# Hammerdin never procs from Holy Shock or Judgement

**Status: ✅✅ FIXED AND VERIFIED IN GAME, 2026-08-06.** Reported fixed on
[tracker #200295](https://ascension.gg/bugtracker/view/200295) the same day it was
submitted, and **confirmed live by measurement** the following evening.

> **Re-test, 2026-08-06 21:47–21:52.** 39 Holy Shock + 25 Judgement casts, Hour of
> Judgement deliberately never pressed so every hammer is a proc rather than periodic
> delivery. **11 distinct Hammerdin procs from 64 casts = 17.2%**, against a stated 20%
> (expected 12.8 ± 3.2). Compare the pre-fix measurement: **1 proc in 129 casts, 0.8%**.
>
> Capture: `data/source/captures/2026-08-06_elric_hammerdin_proc_retest/`.
> Analysis: `primer/FINDINGS_hammerdin_fix_verification_2026-08-06.md`.
> ⚠ Per-ability (HS 4/39, Judgement 6/25) does **not** discriminate at this n.

🚨 **The discriminator was run, and the fix is SCOPED, not general.** In a same-session
Lightbound-Cleave-only window (53 casts, 49 hits, 81 white swings), **Purification By
Light produced nothing** — while PBL fired in the Hammerdin window 13 minutes later on
the same board, which is the control. **Primer §4's engine-intake practice stands.**

⚠ **The proposed MECHANISM did not survive, and it is not the same claim as the bug.**
`2d` theorised that trigger-delivered damage is proc-blind in general. Both PBL triggers
in the re-test fired on Judgement — whose damage arrives via the seal (`54158`), i.e.
trigger-delivered — so PBL plainly *can* see it. 🛑 **n = 2. Neither the mechanism nor its
negation is established.** The cheap decisive test is a **Judgement-only window**;
until it runs, `hammerdin_trigger_set_excludes_trigger_delivered_damage` closes as
*"specific bug fixed, general mechanism contradicted once and unresolved"*, never as
*"mechanism confirmed"*.

⚠ **Also unresolved and newly visible:** PBL's intake in this sample is close to the
**inverse** of its wording — nothing from 130 white swings or 49 Lightbound Cleave hits,
two triggers from 25 Judgements. `2d` established what does *not* feed it; what *does*
is still unmeasured.

<details><summary>Superseded status line (2026-08-05)</summary>

**Status: ✅ FIXED BY ASCENSION 2026-08-05 `[Pending Restart]`** — reported fixed
on [tracker #200295](https://ascension.gg/bugtracker/view/200295) the same day it
was submitted. **Not live until the restart; owner will re-test 2026-08-06.**

</details>
**Found:** 2026-08-05, session `2d`, dedicated 10-minute proc test on training
dummies + a 5.5-minute log the same evening.
(Tracker pages are auth-gated — check for dev responses while logged in.)

---

## 🚨 Fix landed — what it changes, and the one thing it does NOT yet tell us

**Turnaround was hours, not weeks.** The report was submitted and marked fixed on
2026-08-05. This is the first `fixed_on` event in the project's impairment
architecture, and it arrived through the owner reading the tracker rather than
through our changelog sweep — which is the argument *for* building the sweep
(`2e` T4), not against it.

### What re-opens when it goes live

| Re-open | Because |
|---|---|
| `builds/my-builds/build_paladin-hammerdin.md` **§11 rotation priority** | "Press Judgement and Holy Shock" becomes correct again — `2d` had demoted it |
| build doc **§2 class-tag table** | Judgement / Holy Shock return to feeding the engine |
| open question `hammerdin_trigger_set_excludes_trigger_delivered_damage` | The *general* mechanism is now testable against a working case |
| primer §4's engine-intake mapping | The "check whether it damages with the spell you press" practice may narrow to a historical note |

### 🎯 The decisive test — is the fix SPECIFIC or GENERAL?

`2d` suspected a general cause: **a "damaging X abilities" trigger is blind to
damage delivered by a *second* spell** (Holy Shock's press is a dummy → 25902;
Judgement damages through the seal → 20467). If that generalises it affects every
proc engine on the server.

**A Hammerdin-only fix and a general engine fix look identical if you only
re-test Hammerdin.** The discriminator is a *different* engine with the same
shape:

> **Purification By Light × Lightbound Cleave.** `2d` measured PBL taking **zero**
> intake from Lightbound Cleave (65% weapon damage) across an isolation window,
> while a same-session control produced 14 Consecrations. **If PBL now procs from
> Lightbound Cleave, the general mechanism was fixed. If it still does not, the
> fix was scoped to Hammerdin** and primer §4's practice stands unchanged.

Run both in one session: Hammerdin procs from Holy Shock/Judgement (confirms the
reported fix), and a Lightbound-Cleave-only window watching for Consecration
(tests the generalisation). The `2d` protocol and its control window are reusable
as-is.

⚠ **Every capture in `data/source/captures/2026-08-05_elric_2e_poi_baseline/` is
PRE-fix.** Per-hit magnitudes are unaffected (proc rates do not enter a non-crit
average), so the calibration work stands. **Rotation and APL conclusions drawn
from those logs are time-limited** and must be re-derived after the restart.

---

## Ready to paste into the in-game form

**Category:** (pick closest — Talents/Abilities)
**Priority:** Normal
**Report Title** (48 chars):

> Hammerdin doesn't proc from Holy Shock/Judgement

**Issue:**

> Hammerdin says damaging Paladin abilities have a 20% chance to summon a
> Hammer from the Heavens and cut Hour of Judgement's cooldown by 4 sec.
> Tested ~10 min on training dummies with combat logging, pressing everything
> on cooldown:
>
> - Holy Shock: 1 proc in 78 casts
> - Judgement: 0 procs in 51 casts
> - Dawnreaver: 15+ procs in 119 casts (roughly the stated 20%)
> - Hammer of Wrath: also procs normally (earlier log, 44 casts)
> - The -4 sec reduction itself works fine when a proc happens
>
> At 20%, Holy Shock + Judgement together should have given ~25 procs, not 1.
>
> Possible cause (just a guess): both broken abilities deal their damage via a
> second spell (Holy Shock's damage logs under a different spell ID, Judgement's
> comes from the seal), while Dawnreaver/Hammer of Wrath hit directly with the
> button you press. Maybe the proc check misses triggered-spell damage. If it's
> somehow intended, the tooltip shouldn't say "damaging Paladin abilities".

**Is this a Gamebreaking Issue:** No
**Exact Location:** Training dummies (open world)
**What were you doing:** Testing my talent procs on a dummy, pressing Holy
Shock, Judgement and Dawnreaver on cooldown for ~10 minutes with combat logging
on.
**Expected Outcome:** Holy Shock and Judgement proc Hammerdin about 1 time in
5, like Dawnreaver does.
**Actual Outcome:** They almost never proc it (1 proc in 129 casts combined),
while Dawnreaver and Hammer of Wrath proc at the normal rate.
**Steps to Reproduce:**

> Step 1: Take Hammerdin and Hour of Judgement, go to a training dummy.
> Step 2: Press only Holy Shock and Judgement on cooldown for ~5 minutes.
> Almost no hammers appear and the Hour of Judgement cooldown never jumps.
> Step 3: Press only Dawnreaver for ~5 minutes. Hammers appear about 1 press in
> 6 and the Hour of Judgement cooldown visibly drops 4s each time.

---

## Notes for us (never submitted)

Full evidence behind the numbers above (all single-target on the primary dummy
GUID — splash hits on the surrounding dummy cluster excluded):

| Pressed ability | Procs / casts | Rate | Expected at 20% |
|---|---|---|---|
| Dawnreaver (903158) | 15–17 / 119 | ~13–17% | 23.8 ± 4.4 ✓ |
| Holy Shock (20930) | 1 / 78 | 1.3% | 15.6 ± 3.5 ✗ |
| Judgement (of Wisdom, 53408) | 0 / 51 | 0% | 10.2 ± 2.9 ✗ |

Combined HS+Judgement: 1/129 vs ~26 expected → p < 10⁻⁹ under a working 20%.
Corroborated by the earlier 5.5-min log: 44 Hammer of Wrath casts procced at
~16% while 28 Holy Shocks + 24 Judgements gave ~0. Reduction magnitude
verified per-cycle: press gaps 69.4/75.9s on 5/4-proc cycles vs 90s base.
Proc data: 282983 proc_chance=20, reduction −4000 ms via 282985 → 282984.

- Build-doc impact: §2's class-tag table lists Judgement / Holy Shock as
  "feeds Hammerdin: Yes — underused"; §11's rotation priority presses them to
  compress Hour of Judgement. **Measured: they do not feed it; Dawnreaver (and
  Hammer of Wrath in execute) are the real engine drivers.**
- Same structural family as primer §4's trigger-vs-modifier trap, one level
  deeper: trigger-delivered damage appears to be **proc-blind** — likely
  generalises to every "damaging X abilities" engine. Check JotTH/PBL intake
  against trigger-delivered abilities too.
- Same test: Holy Shock SP coefficient measured ~0.40 (n=40 unbuffed
  non-crits); HftH ÷ HoJ-tick 1.68–1.74 vs 1.718 predicted (logs 5 and 6);
  first absolute pulse count 17.9/cast (143 over 8 casts) vs 20–21 modelled.
