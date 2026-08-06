# 🆕 THE PAIRED DUNGEON RUN — 2026-08-06 (owner-offered; NOT restart-gated)

> **`LIVE`** — the standing capture request to the owner. **Must be true today, and is citable as current truth.** If you find a claim here that the tree contradicts, that is a defect in this file. *(Classified `3f` F8c, 2026-08-07.)*

**Run this whenever convenient — it does not wait on the server restart.** It is
a *second, independent* ask from the dummy protocol below, and it is cheap: play
a dungeon you were going to play anyway, with logging on, and upload it.

## Why it is worth a run of its own

The owner has **never uploaded a log**, so his character is absent from the crawl
corpus. Every crawled character we calibrate against has inputs we *infer* — gear
resolved through BisBeard, cards resolved through the crosswalk, buffs derived
from other players' boards, stats computed rather than read. **A dungeon he logs
locally AND uploads gives the same encounter measured twice**, once by us at
ground truth and once by the site's API. That is a check digit on the entire
crawl pipeline, and nothing else available produces one.

What it settles, in rough order of value:

1. **`PLAN_3C` T2c — does the site's `casts` field mean what we think?** Blocking
   the whole log-admissibility rule. The site reports `casts=0` for proc/DoT
   damage (Immolation: 0 casts, 47 hits), so crawl casts/sec under-reads
   proc-heavy kits — Qt logs **9,310 DPS at 0.11 casts/sec**. Comparing the
   site's count against `SPELL_CAST_SUCCESS` in his own log resolves it in one
   query.
2. **A real in-content APM anchor.** His dummy parses give **57.3 / 57.1 APM**
   (two logs, 0.3% apart) — but that is a stationary dummy with no movement or
   mechanics, i.e. an *upper bound*. A dungeon number is what an admissibility
   threshold would actually need.
3. **The first crawled character with fully known inputs.** Gear, cards, stats,
   buffs and rotation all verifiable instead of inferred — so for one character
   we can measure `PLAN_3C`'s **slice accuracy** against ground truth and find
   out whether the sim's ~50–150% spread is real or an artifact of inferred
   inputs.
4. **Does `deaths` ever populate?** It is a declared column with **0 of 19,649**
   rows filled and the crawler never mentions the field. If *anyone* in the group
   dies, a report we control tells us whether the data is available at all — a
   capture bug or a genuinely absent field.
5. **End-to-end pipeline test:** snapshot matching, gear resolution, card
   resolution and buff derivation, all checkable against what he knows was true.

## ✅ NO NEW RUN NEEDED — the log we want already exists

Owner's improvement on the original ask (2026-08-06): upload an **existing**
dungeon log instead of playing a new one. Reviewing
`E:\Ascension Launcher\resources\ascension-live\Logs`, one candidate wins on
every axis.

### 🎯 Upload this one

> **`2026-08-04-20.37.12 WoWCombatLog.txt`** — Scarlet Monastery, 7.8 min

| why it wins | detail |
|---|---|
| **Path of INTELLIGENCE** | ALC's `CI` record reads `primary_stat: intellect`. ⚠ **This is the deciding factor.** The Uldaman run 30 minutes earlier (`20.07.21`) is on **`duality`**, and Duality is the broken path whose AP cycles mid-fight — the owner's own standing decision is that **PoD parses are unusable for absolute calibration**. |
| **It has player DEATHS** | Elric died **2×**, plus Spishtar, ruffyQT, Shaka, Mizmo and Aezneri. The only candidate that can test whether `deaths` populates — and it is *also* ground truth for the exact "died mid-fight" failure mode T2 needs to detect. |
| **Inputs are captured INLINE** | The `CI` record carries 18 **gear** pieces (item_id + enchant + gems + suffix), the full **`hero_build`** (entry_id + rank per card), level, race, path, and `instance: Scarlet Monastery`, snapshotted **per pull** (`captured_for_pull_id`). This is the "fully known inputs" no crawled character has. |
| **Most recent real content** | Gear closest to current. |
| **A second cross-check character** | **Spishtar** (277 casts) is already in the crawl corpus as `character_id 14773`. |
| **Clean bosses** | Mograine, Whitemane, Fairbanks. |
| **Good activity sample** | 190 Elric casts / 7.8 min = **24.3 APM**. |

### Optional second: `2026-08-04-20.07.21` (Uldaman, 20.4 min)

Bigger sample — 503 Elric casts, 60k events, APM 24.7 — and **zero player
deaths**, so it is the clean *control* against Scarlet Monastery's death case.
🛑 But it is on **Duality**, so use it only for the cast-count, APM and `deaths`
questions — **never for calibration.** `Neroxa` (id 10567) is already in the
crawl.

### What you do

1. Upload `2026-08-04-20.37.12 WoWCombatLog.txt` to ascensionlogs.gg.
2. **Send the report link.** That is the whole deliverable — it gives us the
   `report_id` to crawl.
3. Optionally repeat for the Uldaman log.

Nothing else. No new run, no stat export needed — ALC already captured the gear
and board inline, which is the input side `compute_stats` consumes, so this
tests the real pipeline rather than bypassing it.

### ✅ DONE — reports [104](https://darkmoon.ascensionlogs.gg/reports/104/encounters) (SM) and [105](https://darkmoon.ascensionlogs.gg/reports/105/encounters) (Uldaman)

Both uploaded and crawled 2026-08-06. Results in `PLAN_3C` §T2: the site's
> 🛑 **RETRACTED — marked in `3f` F8, not rewritten.** The claim below that the
> site's `casts` is `SPELL_CAST_SUCCESS`, and that *"crawl casts/sec is a
> faithful character-level APM measure"*, was **falsified by the 2026-08-06
> Frost Mage capture**. `SPELL_CAST_SUCCESS` and `SPELL_CAST_START` are
> **disjoint by cast type**: Elric's instants log `SUCCESS` and never `START`,
> his cast-time spells log `START` and never `SUCCESS` — **Frostbolt was cast
> 74 times and produced ZERO `SPELL_CAST_SUCCESS` events** while landing 52
> non-crit hits. The 93% / 97.3% agreement was measured on an **all-instant
> Hammerdin**, where it is correct and does not generalise: for a cast-time
> caster the site's `casts` counts only the instant portion of the rotation.
> Measured across the cohort, it fails for **22 of 41** members.
> Detail: `data/source/captures/2026-08-06_elric_mage_frost/README.md` and
> `primer/FINDINGS_mage_capture_2026-08-06.md` §1. This document is kept as the
> record of what was believed at the time.

`casts` is confirmed to be `SPELL_CAST_SUCCESS` (93% and **97.3%** agreement),
`deaths` is confirmed **unobtainable** (no death or presence key exists anywhere
in the API payload), and the Fairbanks encounter gave ground truth for the
death-deflation failure mode — dead 82% of the fight, reported as 481 DPS with
`validation_status: 'valid'`.

### 🎯 STILL WANTED — the dummy pair (owner offered 2026-08-06)

The dungeon uploads settled the *measurement* questions. They cannot settle
**slice accuracy**, because a dungeon has phases, adds, movement and deaths. A
dummy parse is a sustained single-target rotation, which is exactly what the sim
models — and two logs exist that are uniquely suited.

**1. Primary — `2026-08-05-22.42.20_WoWCombatLog.txt`** (unbuffed, 285.2s,
**1,555 DPS**)

This is *the* most valuable log in the project. Per its capture README, every
condition is **verified rather than asserted**:

* **the only log with a same-session stat block AND a non-cycling path** — SP 638
  on Path of Intelligence, so every sim input is known exactly rather than
  inferred (this is the one thing no crawled character has);
* **unbuffed, verified** — all 11 auras on Elric are self-cast, zero external
  buffs despite ~10 other players present. That removes the sim's weakest layer
  (derived buffs, ±0–11%) from the comparison entirely;
* **weapon imbue absent, verified** — Holy SP == all-school SP;
* **target level +3 (63)**, derived two independent ways (33.6% glancing; 6.0%
  miss) — the level every hit/crit/glancing constant is anchored to;
* **single target** — 883 of 887 damage events on one dummy;
* no deaths, no movement, no phases, no adds.

**2. Second — `2026-08-05-23.10.44_WoWCombatLog.txt`** (buffed, 302s,
**3,650 DPS**)

Window B: same character, same gear, same rotation, same dummy, buffed. Together
the pair is a **direct A/B test of `core/sim/buffs.py` through the crawl
pipeline** — and we already know both answers locally, so any disagreement is
ours.

⚠ **Expected risk, worth finding out either way:** the site may not classify a
dummy session as a boss encounter (report 104 contained a `Combat Segment` row).
If so it will not auto-qualify as a gate candidate — but the `ability_performance`
rows are still captured, which is most of the value.

### 🆕 What the logs already told us before uploading anything

**Real in-content APM is ~21–25, not 57.** Measured across all four of the
owner's real runs: Stratholme 20.9, Uldaman 24.1, Uldaman 24.7, Scarlet
Monastery 24.3 — tight, and **less than half** the 57.3/57.1 measured at the
dummy. The dummy figure is a stationary upper bound, exactly as suspected.

🚨 **And this substantially weakens the "low activity = invalid parse"
hypothesis.** The crawl cohort's median is ~0.6 casts/sec = **36 APM**, *higher*
than the owner's real dungeon play. Several over-predictors sit inside his
normal range (Striker 24.6, Boomcat 17.4). **An APM floor drawn from real play
would not cleanly separate them** — which is another reason `PLAN_3C` T2 does not
filter yet, and why the paired upload matters: it is the only way to learn
whether the site's `casts` and a log's `SPELL_CAST_SUCCESS` are even the same
measurement.

---

# ONE-SESSION DUMMY PROTOCOL — 2026-08-06 (3b pre-flight; supersedes the list below as the active ask)

**Designed to answer every owner-gated item in one visit: six windows,
~25 minutes at the dummy, plus a hover list.** Everything below this section is
kept for reference; its still-open items are folded in here.

## Gate 0 — do NOT run this until the patch is live

Checked live 2026-08-06 (morning): the 2026-08-04/05 changelog entries **still
carry `[Pending Restart]`** on ascension.gg, there are no 2026-08-06 entries,
and **the #200295 fix has no changelog entry at all** (tracker fixes aren't
changelogged). The tracker page is login-gated, so the only definitive read is
yours, logged in.

- **Your check (definitive):** open
  [tracker #200295](https://ascension.gg/bugtracker/view/200295) logged in — is
  it still `[Pending Restart]`, or deployed?
- **Our automatic check:** the daily 07:46 crawl captures the changelog; the
  morning after a restart, the `[Pending Restart]` tags flip and the ingest
  records `status_changed_at`. Any session can confirm with one query.
- **In-session belt-and-braces:** the window order below (positive control
  first) distinguishes "engine dead tonight" from "fix not live" from "fix
  live" on its own.

⚠ If you run before the restart anyway: W1, W3, W4, W5 and every hover are
still valid (none depend on the fix); only W2's confirmation and W6's rotation
conclusions need the patch.

## Setup, once (2 minutes)

1. **Fixed level-63 boss dummy** — same dummy for every window (the 2d
   10–18% dummy-identity lesson). Write down its exact name. Level 63 = +3,
   which is what the hit/crit/glancing constants are anchored to.
2. Combat logging on (ALC). 📎 **Note the combat-log file's exact name and
   folder** — that answers 3b's log-convention question by observation.
3. Type **`/reload` out of combat** once and note whether it works
   (3b's ReloadUI question). At the very END of the last window, try it once
   **in combat** (`reloadui_in_combat`) — last, in case it misbehaves.
4. **Stat export (AscensionCrafterExport) immediately before W1.** Unbuffed,
   🛑 **no weapon imbue** (let Consecrated Weapon expire).
5. **Alone at the dummy, scan your own buff/aura bar:** is **Siphon Health**
   present with no other player nearby? Is **Swift Retribution**? Hover and
   screenshot anything unexplained
   (`siphon_health_and_swift_retribution_sources_unknown`).

## The six windows

No gear/spec/reroll changes except where stated. Rest between windows is fine;
staying on the same dummy is not optional.

| # | Do | Time | Answers |
|---|---|---|---|
| **W1** | **Dawnreaver only**, on cooldown | ~2.5 min (~35 casts) | Positive control: Hammerdin ~20% (expect ~7 procs — proves the engine is live tonight) AND the PBL control (Consecration 270768 / Exorcism 270767 should appear, making W3's zero meaningful) |
| **W2** | **Judgement + Holy Shock only**, on cooldown. 🛑 Do NOT press Hour of Judgement — then every hammer that appears IS a proc; also watch the HoJ cooldown for −4 s jumps | ~4 min (~25 J + ~40 HS) | **The #200295 re-test.** Fix live → ~13 procs (20% of ~65 casts); not live/not working → ~0–1 (pre-fix: 1/129). Separation is decisive either way. Bonus: ~40 fresh unbuffed Holy Shock non-crits with a same-session export |
| **W3** | **Lightbound Cleave only** (autos + queued LC) | ~3.5 min | **The general-vs-specific discriminator:** any PBL output (270768/270767) → the trigger-delivery mechanism was fixed engine-wide; zero (with W1's control positive) → the fix is Hammerdin-scoped and primer §4's practice stands. Bonus: riders on LC should stay zero |
| **W4** | **Autos only**, Seal of Command up, both weapons | ~3 min | (a) `melee_haste_displays_1_30x`: white-swing timestamps vs the sheet's displayed speeds; (b) seal rider rate per event, arm 1; (c) free glancing + crit-suppression sample vs +3 |
| **W5** | **Autos only, main hand ONLY** (unequip off-hand; re-equip after) | ~3 min | `seal_proc_mechanic_rate_vs_ppm`: halving events/min discriminates per-event ~0.25 (procs/min ~halve) from PPM (procs/min constant). Bonus: single-2H white averages (Titan's-Grip-tax data point, confound flagged) |
| **W6** | **Full rotation incl. Hour of Judgement, imbue ON.** Apply Consecrated Weapon to both weapons, take **export #2**, then play ~6 min normally | ~7 min | Post-fix rotation baseline (build doc §13: HoJ uptime with J/HS feeding restored), HftH pulse-count replication, a fresh fully-attributed calibration log — and export #2's Bonus Healing re-measures the imbue's raw +86/weapon (the flagged 2d "+172" re-check) |

## Hover list (any time, ~10 screenshots)

1. 🔴 **Consecrated Holy Weapon (200818), three hovers:** the Consecrated
   Weapon card tooltip, the weapon-enchant line on each weapon, and the active
   buff aura's tooltip. This is the project's top single ask — 25.1% of buffed
   damage with no modelled magnitude and no DBC route.
2. 🎯 **Lightbound Cleave rank 5** — the stated overturn condition for the "no
   AP term" claim.
3. The **unknown-aura talents** (nothing else can source these): Sword
   Specialization, Accuracy, Wrecking Crew, Spellblade, Dual Wield
   Specialization, Twin Disciplines — plus the four server-side-script ones:
   Holy Specialization, Judgements of the Wise, Mental Quickness, Righteous
   Vengeance. **Add Holy Focus** (its capstone's "does not stack" clause +
   Mental Quickness's covers `mental_quickness_exclusivity`).
4. **"Brutal Crusader"** on Light's Hope — only if you own it.

## Send back

The raw `WoWCombatLog` file(s), both exports, the screenshots, the dummy's
name, and — still outstanding — **2d's four logs if they're on disk**
(`<launcher>\resources\ascension-live\Logs`, dated 2026-08-05).

*(Not askable this session: `holy_shock_bonus_coefficient_0429` needs a source
that STATES a coefficient — the R4 tooltip doesn't render one; 0.40 is already
seeded provisional. W2 simply adds a cleaner measurement sample.)*

---

# Capture list — ⚠ LARGELY CONSUMED 2026-08-05 (session `2e`, same evening)

**Status:** the owner delivered Windows A and B, the incremental buff capture,
the isolation captures AND the `2d` PoD logs, all analysed in
`data/source/captures/2026-08-05_elric_2e_poi_baseline/README.md`. **What
remains open, in priority order:**

1. 🔴 **Post-restart re-test of tracker #200295** (Hammerdin fix) + the
   **PBL × Lightbound Cleave discriminator** — protocol in
   `bugs/bug_hammerdin-trigger-set.md`.
2. 🔴 **Consecrated Holy Weapon (200818) live tooltip** — 25.1% of buffed
   damage, unmodelled, no DBC route.
3. §4's tooltip list below (Lightbound Cleave R5, the aura-231/333 talents,
   "Brutal Crusader") — still valid, now behind items 1–2.
4. One export after adding **Strength of Earth Totem ALONE** to an unbuffed
   state (settles `str_to_ap_1_21_under_buffs`).
5. The Path/aura question on the two no-talent captures
   (`sp_no_talent_capture_contradiction_59`).

The protocol below is kept for reuse — it worked.

---

# Capture list for session `2e` — agreed 2026-08-05, owner-proposed dummy protocol

**Supersedes the `2c`-era list**, most of which `2d` consumed. What `2d` did NOT
deliver is carried forward in §4 unchanged.

**Owner proposal, 2026-08-05:** run the calibration capture against the **fixed
level-63 boss dummy** rather than two dungeon runs. **Accepted, and it is the
better instrument** — see §0 for why. `PHASE_2E` T3 asks for "2 logs", not two
dungeon logs; the dungeon framing was inherited from the `2d`-era ask.

---

## 0. Why a dummy beats dungeon runs for this specific capture

T3's live question is whether the sim's school residual (**~1.86× Holy,
~1.37× Holystrike**) is **structural** — an unmodelled school-scoped amplifier —
or **buff state**. That is an A/B discriminator: it needs one arm with the buffs
**off** and everything else held constant.

**A dungeon cannot supply the off arm.** You get whatever the group brings, and
you cannot repeat it. A dummy can, and the fixed level-63 dummy is **+3**, which
is the target level the hit caps and `melee_crit_suppression_vs_higher_level`
are already anchored to.

🛑 **The one thing that makes or breaks it: use the SAME dummy for both windows.**
`2d` measured two sessions an hour apart with an identical unbuffed character
differing **10–18% on every ability**, purely from dummy identity (a level-scaling
"Dynamic Training Dummy" vs the fixed level-63 boss dummy). The A/B comparison is
only valid if the target is held constant. Name the dummy in the notes.

---

## 1. 🔴 The two-window protocol (Path of Intelligence)

One session. **No gear change, no spec change, no reroll between windows.**
If anything changes, re-export and say so.

### Window A — clean baseline

| | |
|---|---|
| Path | **Intelligence**, switched and **relogged** before exporting |
| Buffs | none — no group buffs, no consumables, no flask/food |
| **Weapon imbue** | 🛑 **absent.** Let Consecrated Weapon expire and do not reapply |
| Target | fixed **level-63 boss dummy** |
| Rotation | ordinary single-target priority, played normally |
| Length | **~6 minutes** (see §2 on sample size) |
| Export | AscensionCrafterExport **immediately before** starting the log |

### Window B — played state

Identical to A in every respect **except**: full buffs as you would normally
raid/dungeon with, **and the weapon imbue up**. Fresh export immediately before.

**Why the imbue is separated out:** it is not just a damage rider. Consecrated
Weapon adds **+172 Holy SP and ~+61 AP**, school-scoped — so it moves Holy and
general spell power apart and silently breaks any accounting that assumes they
track together. An "unbuffed" baseline is not clean unless the imbue is absent.
Window A's job is cleanliness, not representativeness; Window B covers the state
you actually play.

### What each window settles

| Outcome | Reading |
|---|---|
| Residual reproduces at the **same** values in A and B | **Structural** — an unmodelled school amplifier. The sim has a missing multiplier, and T3 hunts it |
| Residual appears in B but not A | **Buff state** — T2's buff model absorbs it, no structural gap |
| Residual differs in both, in different directions | Something target- or path-scoped; recorded as a conflict, not fitted |

---

## 2. Sample size — what's binding

Damage-multiplier questions need ~100 hits per ability (primer §5). At `2d`'s
observed rates, **~6 minutes per window** clears that for every anchor:

- **Holy group** — Hammer from the Heavens (accumulates fastest, ~17.9 per Hour
  of Judgement cast), Holy Shock, Consecration (**270768**), Exorcism (**270767**).
  ⚠ The last two are Purification By Light's own out-of-catalog spells — *not*
  the catalog's 26573/879. Never match these by name.
- **Holystrike group** — Lightbound Cleave, Dawn Strike, Whirling Light, Dawnreaver.

**Don't extend the fight for sample size.** The binding constraint is the stat
export pairing, not hit count.

---

## 3. What to record alongside (short, but none of it is optional)

1. **Dummy NPC identity** — exact name, and level if the tooltip shows it.
2. **Imbue state** per window, stated explicitly.
3. **Buff list** for window B — naming them beats inferring from aura lines.
4. **Whether the pending restart has landed.** The 2026-08-05 balance pass (73
   Darkmoon entries, mostly talent buffs) was tagged `[Pending Restart]`. If it
   goes live between the export and a log, or between the two windows, the
   balance state differs from the database and from itself. Two entries touch
   this build, both **chase**-list rather than slotted, so nothing equipped
   changes: **Divine Ferocity** (+50%/stack to next Divine Storm, up from +20%)
   and **In Sword We Trust** (reworked to +25% damage *and* crit to next Crusader
   Strike — reaches **Dawnreaver**, which uses Crusader Strike modifiers).

### 🆕 Send the raw logs, and send `2d`'s too

**No combat log is retained anywhere in this repo** — `data/source/` holds none,
and `*.summary.json` is gitignored. `2d`'s four dummy logs were read in chat and
only the summary numbers survived. That makes them irreproducible: a log records
one specific gear/spec/buff/target state that can never be recreated, which is
exactly the tier-1 "irreplaceable point-in-time state" category the project
already defined for crawl data and never applied to logs.

**Two consequences, both cheap to fix:**

- Send the **new** logs as files, not summaries.
- 🔴 **Re-send `2d`'s four logs if they're still on disk** — they should be in
  `<launcher>\resources\ascension-live\Logs`, dated **2026-08-05**. They are the
  only Path-of-Duality parses the project holds, and two carried-forward tasks
  are blocked without them:
  - **T3b's Duality duty-cycle measurement** — it histograms Dawnreaver (100%
    weapon damage) non-crit hits looking for bimodality. It cannot run at all
    from summary numbers.
  - **T1's validation targets** — seals-per-swing (168 non-crit Seal of Command
    hits vs 103 white swings), the auto-attack averages (286.7 / 347.5), and
    Righteous Vengeance's 247 ticks.

  🛑 This is a request for **files you already have**, not for more Path of
  Duality play. `PHASE_2E` is explicit that PoD modelling beyond the advisory is
  wasted effort until a fix ships.

---

## 4. Live tooltips — carried forward from the `2c` list, unconsumed

`2d` delivered the Holy Shock R4 tooltip. It matched `2c`'s extraction
byte-exactly (562–608 / 676–732) — which confirmed the whole rank-sibling fix,
but **did not settle the coefficient question**, because the tooltip renders
sub-spell base values *unscaled* (no stat term at SP 271). Everything below is
still outstanding.

### A. Damage sources the sim cannot resolve at all

Sorted by hit count in the owner's own logs. Each is real damage with no
modelled magnitude:

| Ability | logged id | hits | avg | why it is unresolved |
|---|---|---|---|---|
| **Righteous Vengeance** | 61840 | 1,259 | 259 | 30% of a crit as a DoT; the sim has no source-damage input for it |
| **Consecration** | 270768 | 1,247 | 228 | Purification By Light's own version, out of catalog |
| **Consecrated Holy Weapon** | 200818 | 1,223 | 445 | ⚠ **NOT** the catalog's `Consecrated Weapon` (200809) — confirmed different |
| **Arcing Light** | 954923 | 312 | 564 | not in the catalog at all |
| **Seal of Command** | 20424 | 208 | 454 | the logged id differs from the catalog's 20375 |
| **Blades of Light** | 913445 / 913446 | 375 | 629–677 | main and off-hand both unresolved |
| **Sword Specialization** | 16459 | 158 | 702 | the extra-attack proc |
| **Whirling Light (Off-hand)** | 907790 | 148 | 579 | off-hand variant absent |
| **Righteous Smite** | 273123 | 125 | 477 | no known magnitude |
| **Judgement of Command** | 20467 | 21 | 1,300 | hits hard, rarely pressed |

### B. Tooltips that would settle a named open question outright

* 🎯 **Lightbound Cleave, rank 5** — the *stated overturn condition* for the "no
  AP term" claim (build doc v12). An `$AP`/`$SP` term retracts it; weapon % +
  flat only confirms it from tier 1 instead of tier 4.
* 🎯 **Holy Shock** — still open. `holy_shock_bonus_coefficient_0429` needs a
  tooltip that *states a coefficient*, which R4's does not. Measurement says
  ≈0.40 and that the client's 0.429 reads ~5% high. **Owner decision pending:
  seed the measured 0.40, or hold for a stating tooltip.**

### C. The talents whose auras are not understood

Outside stock 3.3.5, so no numeric field explains them; they currently contribute
**nothing** to the model:

**Sword Specialization** and **Accuracy** (aura 333) · **Wrecking Crew** and
**Spellblade** (aura 231) · **Dual Wield Specialization** (aura 122) · **Twin
Disciplines**' second effect (aura 136).

And four whose effect is a **server-side script** (`SPELL_AURA_DUMMY`), where a
tooltip is the *only* possible source: **Holy Specialization**, **Judgements of
the Wise**, **Mental Quickness**, **Righteous Vengeance**.

> Value beyond this build: decoding auras 231 and 333 generalises to every card
> that uses them.

### D. Two unattributed passives — a hover each

**Siphon Health (18652)** and **Swift Retribution (853484)** appear in the logs
with no known source. Open question
`siphon_health_and_swift_retribution_sources_unknown`.

### E. Nice to have

* **"Brutal Crusader"** on Light's Hope — open since v5; changes Strength's
  weight if it is a Crusader-family proc.
* **Dawn Strike, rank 8** — its formula matches Lightbound Cleave's in our data
  but the game pays it 25% less; a tooltip may name the difference.

---

## 5. Known limits of a dummy capture — named, not absorbed

Recorded so neither becomes a silently fitted constant.

- ⚠ **The dummy's armor is unknown**, so the weapon-damage half carries an
  unmodelled mitigation term. **The Holy group is unaffected** (0% weapon damage),
  so the Holy calibration is clean; the **Holystrike** group inherits the unknown.
  Partial bound available for free: white-swing non-crit average against the
  sheet's weapon damage range gives effective mitigation directly.
- ⚠ **`2d`'s dummy-identity effect is observed but not explained.** The level-63
  boss dummy read *higher* per-ability damage (auto 347.5) than the level-60
  dynamic dummy (286.7). That is backwards for an armor/level story, which would
  predict less damage against the higher-level target. Do not build on the
  dummy-identity finding beyond "record it" until something explains the sign.

## 6. What NOT to spend effort on

* Screenshots of stats the addon already exports.
* Tooltips for abilities the sim already resolves correctly (Hammer from the
  Heavens, Hour of Judgement, Whirling Light main-hand, Dawnreaver) — validated
  to within 3.2% by the weapon-free pair ratios.
* Extending either window for sample size (see §2).
* **Any new Path of Duality play.** §3's PoD request is for files already on disk.
