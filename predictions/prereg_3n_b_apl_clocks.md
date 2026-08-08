# PREREG `3n` Block B — the APL clock fix

> **`FINDING 2026-08-08`** — pre-registration, written **before** the code it scores.
> Its commit is the commit-parent of the change. Scored in place at the end; a
> falsified prediction is reported, never rescued.

**Baseline** — the committed artifacts at `62d9eae` (Block A, this session):

| | |
|---|---:|
| within ±20% (tuning set of 35) | **0** |
| qualified (≥50% coverage) | **0** |
| slice accuracy at ≥20% coverage | **30.040% (n=24)** |
| admissible-only slice | **27.4% (n=21)** |
| producing-only slice | **36.268% (n=22)** |
| absent share of cohort logged damage | **58.8%** |
| producing median ratio | **0.3234 (n=117)** |

---

## §1 — The mechanism, re-measured this session

`3m` §9 named it and I re-derived it from the tree rather than inheriting it.
Three facts, each read from code or from a probe of the real gate path:

1. **`is_next_swing` reaches no allocation decision anywhere.** The field is set
   from `Attributes & 0x4` (`core/spells/mechanics.py:272`) and is read by
   **nothing** in `core/sim/`. `_useful_cast_interval` has no branch for it, so a
   next-swing ability with no cooldown returns `(0.0, "unbounded — a spam
   filler")`.
2. **These abilities also fail the off-GCD test, on a technicality.** `apl_gen`
   computes `off_gcd = gt in ("none", "off")`, and every one of the 11 next-swing
   ids resolves `gcd_type = None` (they are rank siblings, absent from the
   catalog, so `mechanics.py`'s `catalog_type == "ability"` branch never fires).
   So they are treated as **on-GCD** and `_gcd_for` charges them a full GCD.
3. **Consequence:** a next-swing ability is ranked among GCD fillers by damage
   **per cast** (`sorted(fillers, key=lambda s: -s["mean"])`) and then, in
   `fast_sim`, competes for a **GCD budget it does not actually cost**. Whichever
   unbounded filler ranks first absorbs the remainder; the rest get zero.

**Blix, the measured case:** Lightbound Cleave 358.8 per cast vs Plague Strike
588.5 per cast, so Plague Strike wins the ranking and takes all 54.99 casts of
the 70.29 s budget. Lightbound Cleave gets **0**, while it is **41.0% of Blix's
logged damage**.

⚠ **A correction to `3m` §9 that this measurement forces.** That section reports
Lightbound Cleave as *"rate-limited by the weapon swing timer (44.52 casts)"*.
**44.52 is not the swing-clock count** — it is what LC would get from the GCD
budget if it won the filler ranking (44.52 × 1.4691 s ≈ the budget). Blix's real
swing clock is 3.703 s base ÷ 1.261 haste = **2.9366 s**, giving **23.936** swings
in the window. The fix therefore hands LC **roughly half** the casts `3m`'s
figure implies. Same family as the error `3m` itself caught: a number read off
the wrong clock.

### Exposure, measured over the tuning set

**11 distinct next-swing ability ids** across the corpus: Cleave (20569), Heroic
Strike (25286), Dusk Maul (904386), Light Maul (904406), Mystic Talon (904607),
Shadow Slash (907168), and the five `-bound` Cleaves (907284/907304/907324/
907344/907364).

**12 of the 35 tuning-set members hold both a next-swing ability and unbounded
GCD fillers.** (`3m` cites **15 of 41** over the whole cohort; the difference is
the 5 holdout members, which are not read here. The two figures are consistent
and neither is being restated as the other.)

| member | next-swing ability | % of its logged damage | state today |
|---|---|---:|---|
| Blix | Lightbound Cleave | 41.0% | starved: zero casts |
| Robottikyrpa | Frostbound Cleave (+2 more) | 44.0% | starved |
| Lootgoblin | Lightbound Cleave | 39.1% | starved |
| Meritania | Dusk Maul, Mystic Talon | 31.0% | **producing** |
| Nodding | Stormbound Cleave, Heroic Strike | 26.5% | starved |
| Dads | Light Maul | 18.8% | **producing** |
| Fana | Heroic Strike | 18.6% | starved |
| Deyindra | Heroic Strike, Cleave | 10.9% | starved |
| Ari | Shadow Slash | 10.5% | starved |
| Huskeer | Flamebound Cleave | 7.9% | starved |
| Frediib | Stormbound Cleave | 4.5% | starved |
| Alicion | Lightbound Cleave | 2.1% | starved |

**10 of the 12 are fully starved; 2 are producing at a GCD-derived rate.**

🔬 **None of the 11 members currently outside the slice band is exposed** — the
10 below the 20% coverage floor (Me, Pedroporro, Trace, Chastie, Zaczao, David,
Prithika, Mutaforma, Xizek, Xoller) and the one zero-coverage member (Jamppa)
hold no next-swing ability. All 12 exposed members are already **inside** the
n=24 band. This is what makes the membership prediction below falsifiable rather
than hopeful.

---

## §2 — The fix, in two legs, scored separately

`3g`'s rule is one cause per gate move, and these are two causes. **Leg 1 alone
is knowingly incomplete** — it would add a next-swing ability's damage on top of
white swings it actually replaces. Landing it alone and publishing its gate move
as a win would be publishing a number I already know is inflated. So both land,
each scored against the one before it.

**Leg 1 — the clock.** A next-swing ability is bounded by a **swing budget**
(`window ÷ main-hand swing interval`), consumes **no GCD budget**, and is removed
from the GCD-filler ranking entirely. Several next-swing abilities share one
swing budget, highest damage-per-swing first — they compete for the same swing
slots, exactly as GCD abilities compete for the GCD budget. An own cooldown still
caps it (Mystic Talon's 6 s).

**Leg 2 — the replacement.** An on-next-swing ability *replaces* the main-hand
white swing it rides (`schema.py:341` calls it exactly that, from
`Attributes & 0x4`). Main-hand autos are reduced by the number of next-swing
casts. Off-hand is untouched — the attribute replaces the main-hand swing only.

**Refusal, named:** where the main-hand swing interval is unknown, the swing
budget is unknown, and a next-swing ability is allocated **zero casts with a
named warning** rather than falling back to the GCD budget. A character with no
resolvable weapon cannot swing, so it cannot land an on-next-swing ability
either; that is the mechanically correct answer, not a punt.

---

## §3 — Predictions

### Leg 1 (clock only)

| | prediction |
|---|---|
| **P1** | All **12** exposed members' sim damage **RISES**. Every starved next-swing ability returns; the 2 producing ones free GCD budget for their other fillers. |
| **P2** | The **23** unexposed members do not move **at all** — identical sim DPS to the digit. |
| **P3** | Slice-band **membership is unchanged, n=24**, so **published Δ == same-member Δ** on the slice. Coverage can only rise, and no member outside the band is exposed. |
| **P4** | The **producing-row population GROWS** from n=117 (starved rows become producing). So the published producing median and the same-member producing median **must be quoted as a pair** and are **not expected to be equal** — this is `3l` P4b's trap, and it is being walked into deliberately with the instrument watching. |
| **P5** | Blix's Lightbound Cleave returns at **23.9 casts** (not 44.5), adding ≈ **8,590** damage ≈ **+122 DPS** on a 511.8 DPS baseline. |
| **P6** | `within_tolerance` and `qualified` **stay 0 / 0**. A +24% move on one member does not close a −60%-and-worse gap on three. |

### Leg 2 (replacement, scored against leg 1)

| | prediction |
|---|---|
| **P7** | All **12** exposed members' sim damage **FALLS relative to leg 1** — main-hand autos are removed in proportion to next-swing casts. |
| **P8** | All **12** nonetheless remain **ABOVE the Block A baseline**. Measured precondition: on every one of the 12, the next-swing ability's per-cast damage **exceeds** its main-hand auto's per-swing damage (checked, 12 of 12 — narrowest is Cleave 59.1 vs auto 53.6; widest Shadow Slash 245.7 vs 60.6). Each replaced swing is worth less than the thing replacing it. |
| **P9** | The **23** unexposed members still do not move at all. |

### Not predicted, stated as such

- **Per-member slice direction.** A returning ability changes the slice's
  numerator *and* its denominator: a starved ability is keyed-but-zero and enters
  the modelled set carrying its own logged damage. Whether a member's slice rises
  depends on whether the returning ability's own ratio is above or below that
  member's sitting slice, which I have not computed. **No per-member slice
  direction is claimed.**
- **The slice median's direction.** I expect it to rise — the sim under-produces
  at 0.32 and this restores damage that was missing — but 12 of the 24 band
  members change value at once and a median over that is not something I can
  predict from the parts. **Stated as an expectation, not a prediction, and it
  scores nothing.**
- **Per-member magnitudes** beyond Blix (P5), which is computed from measured
  inputs. Everything else in the tables above is a **direction**.
- **`medium_sim`.** Leg 1 changes `apl_gen`, which medium reads, so medium stops
  spending GCDs on these abilities — but medium's timeline does not model a swing
  clock. If the fast-vs-medium agreement guard trips, that is a finding and gets
  written down, not silenced.

### Symmetric falsifier

Each of these falsifies, in **either** direction:

- any exposed member that **falls** under leg 1, or fails to move at all (P1);
- any unexposed member that **moves at all**, in either direction (P2, P9);
- slice-band membership **changing**, in either direction — a member added *or*
  dropped (P3);
- published slice Δ **≠** same-member slice Δ (P3);
- the producing population **not** growing, or growing while the published and
  same-member medians come out **equal** (P4 — equality here would mean the new
  rows landed exactly on the sitting median, which would itself need explaining);
- Blix's Lightbound Cleave returning at a count **outside 23.9 ± 0.5**, including
  at 44.5 — which would mean the swing clock is not what bounds it (P5);
- `within_tolerance` or `qualified` **moving off 0**, up or down (P6);
- any exposed member that **rises** under leg 2, rather than falling back (P7);
- any exposed member that ends **below** the Block A baseline after both legs
  (P8) — this is the one that fires if replacement is the wrong model, and it is
  the reason P8 carries its own measured precondition.

🛑 **If the gate moves in a direction no prediction above names, that is a
finding: stop, commit the pair with its cause, and write no retroactive prereg.**

---

## §4 — Registered mutations

**M70 — RED: rank next-swing abilities among GCD fillers by damage per cast
again.** This is not an invented mutation: it is the code that actually shipped
from `3e` through `3m`. Restoring `off_gcd = gt in ("none", "off")` without the
next-swing clause, and dropping the swing-budget branch, puts Lightbound Cleave
back in the GCD-filler ranking. **GREEN: the fix** — the swing budget, and
next-swing abilities out of the GCD ranking. Both run.

**M71 — RED: let next-swing casts ride the swing clock but leave main-hand autos
unreduced.** The plausible half-fix — someone who fixed the clock and did not
notice the word *replacement* in the schema comment. This is leg 1 exactly, so
it is a mutation somebody demonstrably might write; the check must see that
autos and their replacements are being counted twice. **GREEN: leg 2.**

Both mutations must be ones someone might actually have written (`3m` M60/M68),
and neither may be so broad that it reds the arm for the wrong reason.

---

## §5 — Scoring

*Filled in after the run. Nothing above is edited.*
