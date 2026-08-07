# Calibration — 2026-08-06 `3c`, against FULLY VERIFIED inputs

> **`FINDING 2026-08-06`** — a calibration record, true as of its date and **not
> maintained**. Its numbers describe the `3c` sim and inputs; later engine fixes
> (E13/E14, `3g`) do not retro-edit this file. *(Status line added `3h` A5, when
> `3f` F8c's lifecycle was extended to `predictions/`.)*

Run after the db.ascension.gg coefficient ingest, against
`2026-08-05-22.42.20` — the unbuffed Path-of-Intelligence dummy baseline whose
site-side capture ([report 106](https://darkmoon.ascensionlogs.gg/reports/106/encounters))
reproduces the local log **to the digit** (443,505 == 443,505, 20 of 20
abilities at +0.0%).

**Inputs are read from the same-session export, not assumed:**
`AP 141 · SP 638 (all schools) · MH 543.6–646.3 @3.57 · unbuffed · no imbue ·
+3 target`.

⚠ **The tool's defaults are Duality-era and wrong for this log** (AP 584 /
SP 533). Passing them changes conclusions — HftH reads 1.26× on the defaults and
1.45× on the real block. **Always pass the stat block.**

---

## ✅ Result 1 — weapon-damage abilities are essentially exact

| ability | school | weapon share | logged / modelled |
|---|---|---:|---:|
| Lightbound Cleave (907304) | Holystrike | 86% | **1.00×** |
| Seal of Command (20424) | Holy | 100% | **1.04×** |
| Dawnreaver (903158) | Holystrike | 100% | **0.99×** |
| Dawn Strike (907901) | Holystrike | 85% | 0.79× |

This **reproduces `2e` exactly** (LC 1.00, Dawnreaver 0.99). Independent
confirmation that the weapon-damage path is right when the weapon input is real.

## ✅ Result 2 — the coefficient-bearing Holy pair is UNCHANGED by the ingest

| ability | `2e` | `3c` |
|---|---:|---:|
| Hammer from the Heavens (282987) | 1.446× | **1.45×** |
| Hour of Judgement (282984) | 1.41× | **1.41×** |

**Expected, and worth stating as a negative result:** both already carried
hand-seeded coefficients (`db_ascension_gg`, the three-source anchor), so the
bulk scrape had nothing to add. `2e`'s "~1.24 still unexplained after the talent
layer" stands untouched.

## 🆕 Result 3 — the out-of-catalog residual is a TIGHT CLUSTER

Eight abilities are excluded as "sim base is wrong". Five of them land in a
**±4% band**:

| ability | logged / **base** |
|---|---:|
| Righteous Smite (273123) | 4.67× |
| Holy Shock (25902) | 4.52× |
| Consecration — PBL (270768) | 4.46× |
| Judgement of Command (20467) | 4.35× |
| Arcing Light (954923) | 4.33× |

**Five independent out-of-catalog spells agreeing to ±4% is one mechanism, not
five bugs.** That is a much sharper target than "cause unknown", and it is the
single largest modelling gap on this character.

🛑 **NOT claimed: that this is `2e`'s 2.2× residual having doubled.** Two reasons
the comparison is invalid as it stands, and both must be closed before anyone
quotes a movement:

1. **`2e` quoted `logged/modelled` (after talents); this table is
   `logged/base`.** At the ×1.15 talent layer the same rows are ~3.9–4.1×
   vs-model — still not 2.2×, but not the same measurement either.
2. **This session changed how periodic coefficients are applied.** PBL
   Consecration's scraped coefficients are stated `periodic`, and the new
   `component` binding routes them to the periodic event instead of the direct
   one. That is *correct* for a ground DoT, but it means the modelled base for
   exactly these spells is not the number `2e` measured. **A controlled
   before/after on the same inputs is required** — comparing across two sessions
   that changed the model in between is the confound this project keeps finding.

⚠ Note the ingest **did** reach these spells: PBL Consecration now holds
SP 0.050 / AP 0.033 (periodic), Exorcism SP 0.090 / AP 0.090, Arcing Light
SP 0.120 / AP 0.078. So `2e`'s "their SP term is missing, not zero" is now
*false as a description of the data* — the coefficients exist. Whether supplying
them moved the residual is the open question above.

## 🆕 Result 4 — two exclusions are named mechanisms, not mysteries

* **Righteous Vengeance (61840): 228× — base 1 vs logged 228.** The base of 1 is
  the site's nominal `Value: 1`. This is the **conversion mechanic** with no stat
  coefficient to find, exactly as `PLAN_3C` T6 describes. The buffed/unbuffed
  pair independently measured it at **×3.18 per hit**, the largest buff response
  of any ability — because buffed crits are both bigger and more frequent and RV
  converts crit damage. **T6 is the fix; nothing here needs data.**
* **Holy Finish (904888): 12.55×** — the combo-point finisher evaluated at
  **0 CP** (`2a`'s known gap: "per-combo flat term present — combo points not yet
  parameterised"). A quadratic CP term at 0 CP is a modelling gap, not a
  measurement.
* **Siphon Health (18652): 0.09×** — over-modelled 11×; still an unattributed
  external effect.

## What this run does NOT settle

* **Auto-attacks are not modelled at all** — 99 white swings at 305 avg, listed
  as "logged but NOT resolvable".
* Six talent effects remain unmodelled (auras 333/122/231/136), and four are
  server-side `SPELL_AURA_DUMMY` scripts (Holy Specialization, Judgements of the
  Wise, Mental Quickness, **Righteous Vengeance**) that no numeric field states.
* 🛑 **Holy Shock's 4.52× must not be read as evidence about its coefficient.**
  25902 carries a **provisional 0.40 back-solved from these very parses**
  (`holy_shock_bonus_coefficient_0429`), and the scrape now states **0.214** —
  the two disagree by ~2×, and the provisional value wins by source precedence.
  Calibrating it against the log that produced it is circular.

## Next

1. **A controlled before/after** on the periodic-component change, to make
   Result 3's cluster comparable with `2e`.
2. **T6 conversion mechanics** — RV is the biggest single named gap and needs no
   data.
3. Decide the Holy Shock coefficient conflict (measured 0.40 vs scraped 0.214).
