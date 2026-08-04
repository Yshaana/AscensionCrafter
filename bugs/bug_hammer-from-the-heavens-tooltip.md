# Bug report — Hammer from the Heavens tooltip renders an inverted damage range

📤 **SUBMITTED 2026-08-04 → [ascension.gg/bugtracker/view/199929](https://ascension.gg/bugtracker/view/199929)**
(the tracker is auth-gated, so status and any dev reply have to be read while logged in).

## ✅ Correction filed 2026-08-04 — report is now accurate

The originally submitted diagnosis was wrong and would have pointed a dev at a fix that
breaks the currently-correct minimum. **The owner has updated the report**; the table
below records what changed, so a future session doesn't re-raise it.

**The core report was always valid** — the range really is inverted, and that is the part
a dev acts on. Only the *explanation* was wrong.

| | submitted version | correct |
|---|---|---|
| cause | description **double-applies** level scaling | scaling is applied **once**; the **maximum** term just uses the wrong rate (1/level instead of 2.4/level) |
| suggested fix | remove both `($PL-10)` terms | change the maximum's `($PL-10)*1` to `($PL-10)*2.4` |
| expected display | 74 to 97 | **194 to 217** — the minimum shown today is already correct |

**Worth a follow-up comment**, because the submitted fix would break the minimum, which
is currently right. Suggested wording:

```
Correction to my own report: the scaling is not applied twice. The macros render the
raw base points, and the description supplies the level scaling once. The minimum's
rate (2.4/level) matches the effect's actual EffectRealPointsPerLevel and is correct;
only the maximum's rate (1/level) is wrong. At level 60 the correct display is
194 to 217 - so the fix is to change the maximum's ($PL-10)*1 to ($PL-10)*2.4, not to
remove the terms. Apologies for the noise.
```

What falsified my original explanation: a client re-extraction returned `MaxLevel = 0`
for this spell (uncapped), and a double application would render `242/195` — *above* the
observed minimum of 194, which is impossible.

**Filed:** 2026-08-04 · **Realm:** Darkmoon · **Spell:** 282987 (triggered by Hour of
Judgement, 282986) · **Character:** Elric, level 60

**Watch for one specific reply.** If a dev says the tooltip text is the *intended*
damage, this stops being a display bug and becomes a **damage** bug worth ~2.3× on an
ability that is 22.1% of this build's damage — which would move the stat weights in
`build_paladin-hammerdin.md` §10. Any other outcome changes nothing for us.

Copy each block into the matching field of the in-game **Create a Bug Report** form.

---

## Category
`Spells / Abilities` — or `Tooltips` / `UI` if the dropdown offers one. *(Pick whichever
exists; I can't see the option list from the screenshot.)*

## Priority
**Low.** It appears to be a display-only fault — the damage the server deals looks
correct. Raise it to Medium **only** if a dev confirms the tooltip text reflects the
*intended* damage, because then the ability is under-performing rather than
mis-displaying.

## Report Title
⚠ **50 character limit.** This one is 46.
```
Hammer from the Heavens: inverted damage range
```
The spell id and the "194 to 147" figure are both in the Issue body, so nothing is lost
by keeping the title short.

## Issue
⚠ **This is the CORRECTED text (2026-08-04).** The originally submitted version blamed a
double-applied scaling term; that was wrong. See "If you already submitted" below.
```
The tooltip for Hammer from the Heavens displays a damage range whose minimum is
LARGER than its maximum: "A Holy hammer falls from the heavens, dealing 194 to 147
Holy damage to nearby enemies."

The cause appears to be that the maximum-damage term in the spell's description uses
the wrong per-level scaling rate. The description reads:

  min = ($PL-10)*2.4 + $m1 + ($AP*0.091) + ($SP*0.091)
  max = ($PL-10)*1   + $M1 + ($AP*0.091) + ($SP*0.091)

The effect's actual per-level scaling is 2.4 (db.ascension.gg reports Effect #1 as
"School Damage: Value: 2 to 25, plus 2.4 per level"). So the MINIMUM term, at 2.4 per
level, is correct - but the MAXIMUM term uses only 1 per level. The minimum therefore
grows 2.4x faster than the maximum and overtakes it at around level 29.

At level 60 the numbers work out exactly:
  min = (60-10)*2.4 + 2  + stat terms = 194   <- correct
  max = (60-10)*1   + 25 + stat terms = 147   <- too low; should be 217

So the displayed maximum is short by 70 at level 60, and the fix looks like changing
the maximum's "($PL-10)*1" to "($PL-10)*2.4" to match the minimum and the effect's
real scaling rate.

The underlying effect data looks fine, and the two scaling components (+9.10% spell
power, +9.10% attack power) are unaffected - this reads as a description/template
problem rather than bad spell data.
```

## Is this a Gamebreaking Issue
```
No
```

## Exact Location
```
Anywhere - the tooltip renders the same way everywhere (spellbook, action bar, and
the Hour of Judgement tooltip chain). Observed in open world and dungeons on Darkmoon.
```

## What were you doing
```
Reading the Hammer from the Heavens tooltip on a level 60 character. Hammer from the
Heavens is the spell triggered by Hour of Judgement (282986 -> 282987).
```

## Expected Outcome
```
A damage range where the minimum is lower than the maximum. At level 60 the correct
display would be "dealing 194 to 217 Holy damage" (the minimum shown today is already
correct; only the maximum is wrong).
```

## Actual Outcome
```
"A Holy hammer falls from the heavens, dealing 194 to 147 Holy damage to nearby
enemies."

The minimum (194) is higher than the maximum (147), which cannot be a valid range.
```

## Steps to Reproduce
```
Step 1: Log in on a level 60 character that has Hammer from the Heavens / Hour of Judgement.
Step 2: Hover the Hammer from the Heavens tooltip (spellbook, action bar, or via Hour of Judgement).
Step 3: Read the damage line - it shows "194 to 147", minimum greater than maximum.
Step 4 (optional): Repeat on a lower-level character. Below about level 29 the range reads
        correctly; above it the minimum overtakes the maximum and the range inverts.
```

## Public Report
Leave **checked** — the diagnosis is useful to other players and there is nothing
account-specific in it.

---

## Notes for us, not for the report

- **The undeniable part is the self-contradiction.** A minimum above a maximum is wrong
  on its face and needs no evidence beyond the screenshot. The mechanism is offered as
  help, not as the claim — keep it that way if a GM pushes back.
- **Our own evidence that the engine is fine** (deliberately left out of the report, as
  it involves parses of other players' characters): pooled across 17,972 Hammer from the
  Heavens hits from 12 characters in the 2026-08-04 crawl, implied non-crit damage is
  124–140 on the two largest samples — below the tooltip's own stated *minimum* of 194.
  So the server is not dealing the inflated number.
- **Step 4 is a prediction, not something we verified.** The crossover at ~level 29 is
  derived from the formula (`2.4x` vs `1x` per level from base level 10), not observed.
  If a dev tests it and the crossover is elsewhere, that is informative rather than
  embarrassing — but do not assert it as measured.
- **If they respond that the text is the intended damage**, that changes it from a
  display bug into a damage bug worth ~2.3× on this ability, and it would move the
  stat weights in `build_paladin-hammerdin.md` §10. Worth following up on.
