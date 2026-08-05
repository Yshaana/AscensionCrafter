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
