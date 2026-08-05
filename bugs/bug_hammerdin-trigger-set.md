# Hammerdin never procs from Holy Shock or Judgement

**Status: 📤 submitted 2026-08-05 — [tracker #200295](https://ascension.gg/bugtracker/view/200295)**
**Found:** 2026-08-05, session `2d`, dedicated 10-minute proc test on training
dummies + a 5.5-minute log the same evening.
(Tracker pages are auth-gated — check for dev responses while logged in.)

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
