# Capture — Elric, 2026-08-05 22:42, **Path of Intelligence clean baseline** (session `2e` T3)

Tier-1, `source='user_provided'`. Supplied by the owner 2026-08-05 in response to
the `2e` capture protocol (`primer/NEXT_CAPTURE.md` §1, Window A).

**This is the first calibration-grade capture in the project's history with a
same-session stat block AND a path that is not cycling.** Every prior absolute
calibration ran on Path of Duality, whose AP bonus oscillates mid-parse
(`bugs/bug_path-of-duality-broken.md`).

## Files

| File | What |
|---|---|
| `stat_export_POI_unbuffed.txt` | AscensionCrafterExport output, Path of Intelligence, relogged |
| `2026-08-05-22.42.20_WoWCombatLog.txt` | 285.2 s window, 17,139 events |
| `2026-08-05-22.42.20_WoWCombatLog.summary.json` | `tools/log_parser/parse_log.py` output (gitignored) |

## Provenance — every protocol condition VERIFIED, not asserted

| Condition | Status | How verified |
|---|---|---|
| Path of Intelligence | ✅ | Export states it; SP 638 ≈ 2× (gear 229 + Lunar Guidance) |
| Relogged before export | ✅ | Stat block is **byte-identical** to `../2026-08-05_elric_2d/stat_export_POI_relog.txt` |
| **Same session as the log** | ✅ | Same byte-identical block ⇒ gear/spec/path provably unchanged |
| **Unbuffed** | ✅ | **All 11 aura types applied to Elric are self-cast.** Zero external buffs despite ~10 other players in the log |
| **Weapon imbue absent** | ✅ | Export shows `SpellPower_Holy == SpellPower_<all others> == 638`. An active Consecrated Weapon would add ~+172 **Holy-only** SP |
| Dummy identity recorded | ✅ | **Azeroth Execute Training Dummy** — see below |
| Single target | ✅ | 883 of 887 damage events on one dummy (4 stray on Azeroth Tank Training Dummy) |

⚠ The log also contains ~10 unrelated players hitting a **Dynamic Training
Dummy**. Elric never touched it. Filter on `sourceName == 'Elric'`; the file is a
public-area capture, not a solo one.

## 🎯 Target level = 63 (+3), derived two independent ways

The dummy is *named* "Execute" rather than "boss", but it behaves as **+3**:

1. **Glancing blows = 33.6% of landed white swings (42/125).** Glancing occurs
   *only* against higher-level targets. A +0 target produces none.
2. **Miss rate 8/133 swings = 6.0%**, plus 1.8% melee hit ⇒ ~7.8% base miss,
   against the 8.0% expected at +3 (5.0% at +0).

**This is the target level T3 wanted** — +3 is the raid-boss-equivalent the hit
caps and `melee_crit_suppression_vs_higher_level` are anchored to.

⚠ **Execute-range caveat, recorded not resolved:** the dummy is held in execute
range by design, so any execute-conditional damage bonus is permanently active
here and would not be in normal play. No such effect is currently modelled for
this build, but it must be checked before this log anchors an absolute number.

## Headline measurements (285.2 s, unbuffed, +3 target)

**Total 443,505 damage ⇒ 1,555 DPS unbuffed.**

| spellId | ability | school | n | non-crit avg | crit avg | crit% | % dmg |
|---|---|---|---|---|---|---|---|
| 907304 | Lightbound Cleave | Holystrike | 80 | 520.6 | 1003.1 | 35.0% | 12.4% |
| 25902 | Holy Shock | Holy | 29 | 1243.2 | 2430.1 | 51.7% | 12.1% |
| — | Melee auto | Physical | 125 | 305.4 | 707.8 | 20.8% | 11.0% |
| 282987 | Hammer from the Heavens | Holy | 87 | 341.4 | 662.4 | 41.4% | 9.3% |
| 20424 | Seal of Command | Holy | 84 | 311.9 | 625.3 | 44.0% | 8.5% |
| 907901 | Dawn Strike | Holystrike | 56 | 417.5 | 878.5 | 35.7% | 7.4% |
| 61840 | Righteous Vengeance | Holy | 130 | 228.1 | — | **0.0%** | 6.7% |
| 16459 | Sword Specialization | Physical | 38 | 469.2 | 960.2 | 31.6% | 5.3% |
| 903158 | Dawnreaver | Holystrike | 46 | 339.3 | 701.2 | 41.3% | 5.1% |
| 273123 | Righteous Smite | Holy | 36 | 379.5 | 750.9 | 41.7% | 4.3% |
| 954923 | Arcing Light | Holy | 30 | 379.0 | 745.6 | 46.7% | 3.7% |
| 20467 | Judgement of Command | Holy | 16 | 776.6 | 1408.7 | 37.5% | 3.7% |
| 904888 | Holy Finish | Holystrike | 7 | 1543.8 | 3045.0 | 14.3% | 2.8% |
| 280212 | Judgement of the Three Hammers | Physical | 17 | 550.0 | 1100.0 | 23.5% | 2.6% |
| 270768 | Consecration | Holy | 47 | 162.9 | — | **0.0%** | 1.7% |
| 270767 | Exorcism | Holy | 7 | 496.8 | 1041.7 | 42.9% | 1.2% |
| 282984 | Hour of Judgement | Holy | 20 | 195.1 | — | **0.0%** | 0.9% |
| 907780 / 907790 | Whirling Light MH / OH | Holystrike | 5 / 5 | 464.7 / 373.8 | 723.5 / 619.0 | 40% / 20% | 1.1% |
| 18652 | **Siphon Health** | **Shadow** | 22 | 41.3 | — | 0.0% | 0.2% |

## ✅ What this capture validates

- **The weapon-free pair anchor reproduces best-ever.** HftH ÷ HoJ-tick =
  **1.750** against a predicted **1.718** — **+1.9%**, the tightest of seven logs
  and the first on a non-cycling path. Dawnreaver ÷ Whirling Light = 0.730 vs
  0.769 (−5.1%, inside the historical band; n=5 on Whirling Light).
- **The sheet's Holy crit is real in combat.** Sheet says 41.88%; observed HftH
  41.4% (n=87), Righteous Smite 41.7% (n=36), Exorcism 42.9%, Seal of Command
  44.0% (n=84). The +15.00 talent crit stack (Holy Power 5 + Holy Specialization
  5 + Twin Disciplines 5) is delivered, not just displayed.
- **Periodic-cannot-crit, reconfirmed:** Righteous Vengeance 0/130, Consecration
  0/47, Hour of Judgement 0/20.
- **Spell crit multiplier ≈ 2.0** (1.93–2.10 across seven abilities), consistent
  with Holy Focus lifting spell crits from the 1.5× base to 200%.
- **Rating divisors confirmed from the export**: crit 179 → 12.79% (14.0 ✓),
  melee hit 18 → 1.80% (10.0 ✓), spell hit 18 → 2.25% (8.0 ✓), expertise 32 →
  12.80% (2.5 ✓).

## ⚠ Open items this capture raises

1. **Melee autos crit 20.8% (n=125) against a 24.92% sheet** — a ~4-point
   suppression vs the +3 target. Directionally the expected
   `melee_crit_suppression_vs_higher_level` effect, but n=125 gives ~±3.9% at 1σ,
   so it does **not** discriminate 3% from 4%. Needs the 300+ swing sample.
2. **Melee auto crit multiplier is 2.318**, above the 2.0 physical base. Unexplained.
3. **Sword Specialization crits 31.6%** — above the 24.92% melee sheet, despite
   being a physical extra-attack proc. Unexplained.
4. 🆕 **Siphon Health (18652) deals SHADOW damage** — 22 ticks, 41.3 avg. First
   mechanical handle on one of the two unattributed passives
   (`siphon_health_and_swift_retribution_sources_unknown`). It is a small Shadow
   periodic, which narrows the search considerably.
5. 🚨 **Holy Shock's non-crit average (1243.2) is far above the current model.**
   At R4 base 562–608 (avg 585) and SP 638, a 0.40 coefficient predicts ~840.
   Hand-computed residual ≈ **1.48×**, while HftH's is ≈ **1.67×** — *the two Holy
   residuals do not match*, so a single Holy-school multiplier cannot explain
   both. 🛑 These are hand calculations for triage only; the sim's own resolver is
   the instrument, and running it is `2e` T3.
6. **The `2c` Holy residual moved** — ~1.86× on Duality logs, ~1.67× for HftH
   here. Movement points at buff/path state as *part* of the cause, but it is far
   from 1.0, so something structural remains. Per `NEXT_CAPTURE.md` §1 this is the
   A/B discriminator's first arm; **Window B (buffed) is still outstanding.**

---

# Window B (buffed) — 2026-08-05 22:54

Files: `stat_export_POI_buffed.txt`, `2026-08-05-22.54.21_WoWCombatLog.txt`.

**Owner-stated buffs:** Aspect of the Beast, Arcane Brilliance, Greater Blessing
of Kings, **2× Consecrated Weapons**, Strength of the Earth Totem.

## 🛑 The LOG is unusable as the discriminator arm — the EXPORT is excellent

**The combat window is 46 seconds (22:54:21 → 22:55:07) containing 19 Elric
damage events.** Window A has 887. This is a warm-up, not a measurement: single
digits per ability, `Lightbound Cleave` has one event (a crit), `Seal of Command`
one, `Melee auto` two. **No residual may be computed from it.**

⚠ Righteous Vengeance reads *lower* here (154 avg) than unbuffed (228.1) — not a
paradox and not usable: RV pools on refresh and needs ~30 s+ to reach steady
state, so a cold 46 s window samples the ramp.

⚠ The external buffs were applied **before** logging started, so the log carries
no `SPELL_AURA_APPLIED` for them. Buff state here is documented by the **export
plus the owner's statement**, not self-evidenced by the log — unlike Window A,
whose unbuffed state the log proves independently.

**Window B must be re-run at ~5 minutes to settle structural-vs-buff.**

## ✅ What the buffed EXPORT settles anyway — the buff model is now MEASURED

`2e` T2 was scoped as a modelling exercise. This pair turns most of it into
arithmetic. **Blessing of Kings applies LAST, multiplicatively, to all five
stats**; everything else is additive underneath it:

| Stat | Model | Predicted | Observed |
|---|---|---|---|
| Intellect | (259 + **31** Arcane Brilliance) × 1.10 | 319.00 | **319** ✓ |
| Stamina | 264 × 1.10 | 290.40 | **290** ✓ |
| Spirit | 77 × 1.10 | 84.70 | **84** ✓ |
| Strength | (121 + **62**) × 1.10 | 201.30 | **201** ✓ |
| Agility | (28 + **62**) × 1.10 | 99.00 | **99** ✓ |

**General spell power**, +68 observed, predicted **+68.4**:
`Arcane Brilliance +27 × 2.0 (PoI doubling) = +54`, plus
`Lunar Guidance 12% × ΔInt 60 = +7.2, ×2.0 = +14.4`.
This simultaneously confirms Arcane Brilliance's +27 SP, **Lunar Guidance = 12%
of Intellect**, and that PoI's doubling reaches *effect* SP and the Lunar
Guidance knock-on.

## 🆕 Consecrated Weapon stacks once PER WEAPON

`SpellPower_Holy − SpellPower_<other>` = **1050 − 706 = 344 = 2 × 172**.

Under Titan's Grip both weapons carry the imbue and **both Holy SP grants apply**.
This confirms `2d`'s +172 figure and is the first evidence it stacks.

⚠ **Anomaly, recorded not resolved:** `2d` measured +172 on a **Duality** sheet
(which has no SP doubling) and this PoI capture — *with* a ×2.0 doubling on
item/effect SP — also gives **172 each**, not 344 each. So **PoI's doubling
appears NOT to reach weapon-imbue Holy SP**, which its "SP from items and
effects DOUBLED" wording would predict. Either the imbue is excluded from the
doubling, or the grant is +86 doubled to 172 and `2d`'s Duality reading needs
re-examination. **One capture cannot separate these** — resolve with a
single-imbue export (see below).

## Weapon damage is a pure flat add

Range width is **identical** (102.7) in both windows; both ends move +177.1.
`ΔAP/14 × speed = 287/14 × 3.57 = 73.2`, leaving **+103.9** attributable to the
imbues' flat weapon-damage rider.

## ⚠ Attack Power is NOT decomposable from this pair

AP 141 → 428 (+287) and RAP 60 → 299 (+239), against Str +80. With five buffs
applied simultaneously and at least two granting AP (Consecrated Weapon ~+61
each per `2d`, plus Aspect of the Beast), the system is **under-determined**. The
Str/Agi +62 likewise cannot be split between Aspect of the Beast and Strength of
the Earth Totem.

🎯 **Cheap fix, no combat required: an incremental buff capture.** Export once
with no buffs, then once after each buff is added, one at a time. Five exports
give every per-buff delta exactly, with zero modelling — and it resolves the
imbue-doubling anomaly above as a side effect (export with **one** imbue, then
two).

## Window B attempt 2 — `2026-08-05-23.03.10`: NO COMBAT AT ALL

Log spans 23:03:10 → 23:05:40 (150 s, 14,647 events). **Elric appears in 20 of
them — 15 `SPELL_AURA_REMOVED` and 5 mana ticks. Zero attacks.** The rest is
unrelated players at the Dynamic Training Dummy.

Buffs were *decaying* through this window, not merely the totem:

| Time | Event |
|---|---|
| 23:04:56 | **Greater Blessing of Kings** removed |
| 23:04:57 | **Arcane Brilliance** removed |
| 23:05:40.977 | Everything removed at once — `PvE Mode`, `Aura of Experience`, `Primary Stat: Intellect`, `Aspect of the Beast` — the logout/zone-out signature |

**Reconstructed timeline:** Window A 22:42–22:47 (887 events ✅) · attempt 1
22:54:21–22:54:33 (19 events) · **gap 22:58–23:03 with no log file at all** ·
attempt 2 23:03–23:05 (0 attacks). The buffed combat was most likely fought in
the unlogged gap.

🛑 **Window B remains uncaptured. Three files, no usable buffed combat.**

## 🆕 Swift Retribution is an EXTERNAL aura from another player

`23.03.10` line: `SPELL_AURA_REMOVED  Virginity -> Elric  Swift Retribution`.

**It is cast by another player (`Virginity`), not by Elric.** This resolves half
of `siphon_health_and_swift_retribution_sources_unknown`: Swift Retribution is
not one of Elric's talents and needs no tooltip hover — it is a passing
Retribution-Paladin raid aura. ⚠ It also means the `2d` "unbuffed" capture,
whose README records buff state as *"Swift Retribution only"*, was carrying a
stranger's aura.

**Does this contaminate Window A?** No external aura is evidenced there —
`APPLIED`, `REFRESH` and `REMOVED` all show only self-cast sources. Absence is
not quite proof (an aura applied before the log and never removed inside it
would be invisible), but the exposure is bounded and harmless: **Swift
Retribution is a haste aura, and haste does not change per-hit damage.** Every
Window A number this capture reports is a **per-hit non-crit average**, so the
calibration inputs stand regardless. Only DPS totals and swing counts could
shift.

---

# Incremental buff capture — 2026-08-05, `stat_exports_incremental_buffs.txt`

Six exports, one buff added at a time. **This makes the buff layer measured
arithmetic rather than a model, and it resolves two anomalies flagged above.**

## Per-buff deltas (isolated)

| Step | Buff added | Measured effect |
|---|---|---|
| 1 | **Aspect of the Beast** | **+14 AP.** Nothing else — no RAP, no stats |
| 2 | **Arcane Brilliance** | **+31 Int, +27 raw SP** (→ +60 displayed after PoI doubling and the Lunar Guidance knock-on) |
| 3 | **Blessing of Kings** | ⚠ **NO CHANGE — the export is STALE** (see below) |
| 4 | **Consecrated Weapon, MH** | **+86 raw SP → +172 Holy SP**, **+88 AP**, **+80 RAP**. Kings' ×1.10 also lands here |
| 5 | **Consecrated Weapon, OH** | identical: **+86 raw / +172 Holy SP, +88 AP, +80 RAP** |
| 6 | **Strength of Earth Totem** | **+62 raw Str AND +62 raw Agi** (displayed +68/+69 after Kings) |

**Blessing of Kings is ×1.10 to all five stats**, confirmed by the step 3→4
delta (Str 121→133, Agi 28→30, Sta 264→290, Int 290→319, Spi 77→84 — every one
exactly ×1.10 with floor rounding).

## ⚠ A stale export, caught in a controlled setting

**Step 3's export is byte-identical to step 2's** — Blessing of Kings had been
cast but had not yet reached the character sheet. Its effect appears in step 4.

This is the same read-too-early failure `2d` first mis-diagnosed as a
"path-switch settle delay". It is **not** Duality-specific and **not**
path-specific: *any* freshly applied buff can be missing from an export taken
immediately after. **Protocol: wait for the buff to appear on the character
sheet before exporting**, and treat a zero-delta step as suspect rather than as
a measurement of zero.

## ✅ The full spell-power model closes to ≤1.6 across five states

```
SP = 2.0 × (gear SP + effect SP + 0.12 × Int) + 118
```

| State | Predicted | Observed |
|---|---|---|
| baseline | 638.2 | **638** |
| + Arcane Brilliance | 699.6 | **698** |
| + imbue MH (Holy) | 878.6 | **878** |
| + imbue OH (Holy) | 1050.6 | **1050** |
| general (non-Holy), imbues excluded | 706.6 | **706** |

Components: **gear SP 229** (sum of items), **PoI doubling ×2.0**, **Lunar
Guidance = 12% of Intellect**, and a **+118 PoI flat that is damage-only**
(it never appears in Bonus Healing). ⚠ Whether that 118 is a post-doubling flat
or a pre-doubling +59 is still under-determined.

## 🆕 BonusHealing is UNDOUBLED spell power — a free instrument

Observed chain **229 / 256 / 256 / 342 / 428 / 428** is exactly
`gear 229 + Arcane Brilliance 27 + 86 per imbue`. No doubling, no Lunar
Guidance, no PoI flat.

**So Bonus Healing reads the raw SP contribution directly.** Any future "what
does this effect actually grant?" question can be answered by reading Bonus
Healing instead of unpicking the doubling.

## ✅ RESOLVED: the imbue-doubling anomaly (my error, corrected)

Earlier in this file I flagged that PoI's doubling appeared *not* to reach the
weapon imbue, because both `2d` (Duality) and the buffed export read **+172**.

**That was wrong, and the incremental capture shows why.** The imbue grants
**+86 raw**, which Bonus Healing reports directly, and PoI doubles it to the
**+172** seen in the Holy SP field. **PoI's doubling does reach weapon imbues.**

⚠ **Consequence for `2d`:** its +172 was read on a *Duality* sheet, which has no
doubling and should therefore have shown **+86**. Either that capture was in a
carried-over PoI-doubled state — a bug `2d` itself documented — or the figure
needs re-measuring. **Flagged for re-check; do not carry +172 as the raw grant.**

## Rating conversions independently reconfirmed

| Conversion | Measured here | Project value |
|---|---|---|
| Agi → melee crit | 69 Agi → +2.12% ⇒ **32.5 per 1%** | ~32.4 ✓ |
| Int → spell crit | 31 Int → +0.51% ⇒ **60.8 per 1%** | ~61 ✓ |
| Agi → armor | 69 Agi → +138 ⇒ **2.0 per Agi** | — |
| Agi → RAP | 69 Agi → +76 ⇒ **×1.10** (Deadliness) | ✓ |

## ⚠ Attack Power is the one term that does NOT close

Str → AP measures **~1.21**, not the expected 1.10 (Str 1:1 × Deadliness +10%):

- totem step: ΔStr 68 → ΔAP 82 ⇒ **1.206**
- Kings step: ΔStr 12 → ΔAP ~15 (after subtracting the imbue's 88) ⇒ **~1.21**

Consistent across two independent steps, so it is real, not noise. `1.10 × 1.10
= 1.21` suggests **a second +10% AP multiplier** stacking with Deadliness, but
the totem moved Str *and* Agi together so an Agi→AP term (~0.10) fits equally
well. **A single-stat change settles it** — one export after any Str-only or
Agi-only source. Also unresolved: the absolute base (AP 141 at Str 121 with
+27 gear AP does not reduce cleanly).

---

# ✅ WINDOW B CAPTURED — `2026-08-05-23.10.44`, 302 s, 1,448 Elric damage events

Same **Azeroth Execute Training Dummy**, buffed, imbues up (Consecrated Holy
Weapon fires 405 times). Larger sample than Window A.

**Stat stability verified, not assumed.** Per-60 s non-crit means are flat across
the whole window — Hammer from the Heavens 492 / 489 / 490 / 472 / 486, and
Lightbound Cleave (65% weapon damage, so Strength-sensitive) 754 / 740 / 803 /
744 / 755. **The Earth Totem did not drop during this log.** Buff state matches
`stat_export_POI_buffed.txt`.

## 🎯 3,650 DPS buffed — the owner's long-reported ~3,600, measured and attributed

Window A was 1,555 unbuffed. **This is the first time the project has a
fully-attributed DPS figure with a known stat block**, and it lands on the number
the build doc has quoted from memory since v5. The sim reads **848**.

## 🚨 THE DISCRIMINATOR RESOLVES: the school residual is STRUCTURAL

| | Window A (unbuffed) | Window B (buffed) |
|---|---|---|
| Hammer from the Heavens residual | **1.446** | **1.577** |
| Holy Shock residual | **1.281** | **1.361** |

*(hand model: flat + 0.091 SP/AP coefficients, Holy Shock 585 + 0.40 SP, × the
1.155 talent layer. **Triage only — the sim's resolver is the instrument, T3.**)*

**The residual is present at ~1.45 in a window with zero buffs and every input
measured.** Per `NEXT_CAPTURE.md` §1's own decision table that is the
**structural** outcome: there was no buff state in Window A for it to hide in.
`2c`'s ~1.86 was therefore *partly* Duality/buff contamination and *substantially*
a genuine missing multiplier.

### Secondary, and new: the residual GROWS with buffs

| Ability | model-predicted B/A | observed B/A | excess |
|---|---|---|---|
| Hammer from the Heavens | 1.311 | 1.429 | **+9.0%** |
| Holy Shock | 1.196 | 1.271 | **+6.3%** |

The stat model under-predicts the buffed jump, so **something multiplicative
scales with buff state** on top of the constant structural gap. Two separate
defects, not one.

## 🚨 Consecrated Holy Weapon is 25.1% of buffed damage and is UNMODELLED

| Ability | hits | damage | share |
|---|---|---|---|
| **Consecrated Holy Weapon** (200818) | 405 | 276,301 | **25.1%** |
| Righteous Vengeance | 151 | 109,550 | 9.9% |
| Melee auto | 136 | 87,676 | 8.0% |
| Lightbound Cleave | 81 | 86,527 | 7.9% |
| Holy Shock | 32 | 82,374 | 7.5% |
| Seal of Command | 106 | 71,557 | 6.5% |
| Hammer from the Heavens | 89 | 62,204 | 5.6% |

**A quarter of buffed damage comes from a source the sim has no magnitude for**
(§4A lists it unresolved; it is **not** the catalog's `Consecrated Weapon`
200809). It is absent from Window A entirely because the imbue was off — which is
also why the unbuffed baseline is the cleaner calibration arm. **This is now the
single largest modelling gap, ahead of the school residual.**

## ✅ `melee_crit_suppression_vs_higher_level` — no suppression detected

Pooled white swings across both windows against the **+3** dummy:

| | crits/swings | observed | sheet |
|---|---|---|---|
| Window A | 26/125 | 20.8% | 24.92% |
| Window B | 40/136 | 29.4% | 27.10% |
| **Pooled** | **66/261** | **25.29%** | **26.06%** (sheet-weighted) |

**Difference −0.77 points, 1σ = 2.69 → consistent with zero suppression.** Not
conclusive (a 3-point effect is inside the error bar), but it is the first real
constraint, and it points *against* the retail assumption. Glancing blows ran
33.6% / 39.0%, confirming the +3 target level in both windows.

---

# Isolation captures — `stat_exports_isolation_tests.txt`

Three further owner captures: **+Elixir of Agility** (an Agility-only change),
**geared with no talents/abilities**, and **naked with no talents/abilities**.

## ✅ Agility → Attack Power is EXACTLY ZERO

Elixir of Agility moves **Agi 28 → 43** and nothing else. **AP stays at 141.**

**This settles the open AP question.** The Str→AP ≈ 1.21 seen in the buffed steps
is **not** an Agility term — the alternative hypothesis is dead. Same capture
reconfirms three conversions at a clean +15 Agi: melee crit **32.6** per 1%,
armor **2.0** per Agi, RAP **×1.10** (Deadliness).

## ✅ The Attack Power base formula, solved

Naked (Str 50, AP 30) and geared-no-talents (Str 121, AP 101, offhand absent):
**ΔStr 71 → ΔAP 71 — exactly 1:1.** Both rows fit `AP = Str − 20`.

Adding the offhand's +27 gear AP and Deadliness's +10%:

```
AP = (Str − 20 + gear AP) × 1.10
   = (121 − 20 + 27) × 1.10 = 140.8      observed 141   ✅
```

⚠ The buffed states still read ~1.21 per Strength rather than 1.10, so **a buff
is granting AP beyond its Strength** (Strength of Earth Totem is the candidate)
or a second multiplier appears only under buffs. The unbuffed formula is exact;
the buffed excess is now the narrow remaining question.

## ✅ Talent vs item attribution — the offhand was doing the work

The no-talent states also **unequip the offhand** (no Titan's Grip), so its stats
leave at the same time. Barovian Family Sword carries crit 17, expertise 6,
ArP 14, AP 27, Sta 17 — and every one of those deltas is fully explained by the
item:

| | talents on | talents off | delta | offhand item | talents contribute |
|---|---|---|---|---|---|
| Crit rating | 179 | 162 | 17 | 17 | **0** |
| Expertise | 32 | 26 | 6 | 6 | **0** |
| Armor pen | 14 | 0 | 14 | 14 | **0** |
| Stamina | 264 | 247 | 17 | 17 | **0** |

**The Holy crit stack is confirmed a third way:** `SpellCrit_Holy −
SpellCrit_other` is **15.00** with talents and **0.00** without.

## 🛑 UNRESOLVED: the two no-talent spell-power readings contradict each other

| State | gear SP | observed SP | Bonus Healing |
|---|---|---|---|
| naked, no talents | 0 | **118** | 0 |
| geared, no talents | 229 | **288** | 229 |
| geared, with talents | 229 | **638** | 229 |

No single `(flat, multiplier)` pair fits both no-talent rows:

- Solving the naked row gives **flat = 118** → the geared row should read
  `229 + 118 = 347`, but it reads **288** (−59).
- Assuming **flat = 59** fits the geared row (`229 + 59 = 288`) → the naked row
  should read **59**, but it reads **118** (+59).

The discrepancy is exactly **59 in both directions**, which is too clean to be
rounding. 🛑 **Not modelled, not fitted, recorded as a conflict** per §2.3.

**What would settle it, in one question to the owner:** was the **Path still
Intelligence** in *both* captures, and did "no abilities" also remove anything
that grants spell power (a self-cast aura — `Brilliance Aura` is cast by Elric in
the Window A log)? The earlier `SP = 2.0 × (gear + 59 + effects + 0.12×Int)`
model fits every *talented* state to ≤1.6, so whatever differs lives in the
stripped states, not in the working model.

## ⚠ Haste: two separate oddities, neither resolved

1. **The owner reports a persistent ~3% haste buff, "even naked".** The export
   shows `0.00%` on all three haste fields when naked, so **the export's haste
   percentages are rating-derived only** and cannot show a buff-sourced haste at
   all. His buff bar is seeing something the export does not capture.
   🎯 **Most likely source: `Swift Retribution`** — proven earlier in this file to
   be an **external aura cast by another player (`Virginity`)**, and a +3% haste
   raid aura in stock WotLK. That matches "always on" if the caster is parked in
   the dummy area.
2. **Melee haste reads 1.30× ranged/spell haste at identical rating** (3.77% vs
   2.90% at 29 rating) in every geared state, with and without talents, and 0.00%
   naked. A permanent ×1.30 melee-haste multiplier that talents do not supply.
   Unexplained; recorded.

## Still needed

1. The **Path/aura question** above, to close the spell-power contradiction.
2. A live tooltip for **Consecrated Holy Weapon (200818)** — the highest-value
   single tooltip in the project, at **25% of buffed damage**.
