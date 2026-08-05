# SCORECARD — the ten-axis build rating (spec v1, session `2e`)

**Status: SPEC ONLY.** Implementation lands with Phase 4; this document exists
now so `3a` knows what population data it must produce. Source of the design:
`PHASE_2D` T6 (owner decisions D1/D2, 2026-08-05).

**Header form a guide displays:** `74/100 · Difficulty: Hard`

---

## 1. Shape

**Ten axes × 10 points = 100.** No axis is weighted above another in the tally —
a reader who cares more about one axis reads that axis.

Two hard rules, both inherited from the project's epistemics:

1. **Performance axes are percentile-anchored, never vibes.** An axis score of
   5/10 is the population median *by construction*, computed against
   `character_scenario_dps` over the crawl. "Above average" is a measurable
   claim with a denominator.
2. **An axis with unconfirmed inputs shows a confidence marker, never a
   fabricated number.** The marker vocabulary is the project's usual one; a
   low-confidence 7 renders as `7? ` with the gating confound named in the
   axis's detail line. D4 applies on top: **no cross-school ranking is published
   from sim output until the calibration gate passes** (see §4).

## 2. The axes

| # | Axis | Score source | Anchor population |
|---|---|---|---|
| 1 | **Single-Target** | sim `patchwork` DPS → percentile | `character_scenario_dps`, same content profile |
| 2 | **Cleave** | sim `cleave` DPS → percentile | same |
| 3 | **AoE** | sim `aoe` DPS → percentile | same |
| 4 | **Burst** | medium-sim timeline windowing: best 10 s ÷ mean 10 s | sim-internal (no crawl analogue yet) |
| 5 | **Consistency** | inverse RNG dependence: combat-RNG band width + proc-chain damage share | sim-internal |
| 6 | **Survivability** | kit analysis: mitigation, self-heals, sustain (healing terms are already extracted — `BH` term type, healing block in `spell_mechanics`) | kit-structural |
| 7 | **Support** | buffs/debuffs/utility brought: relationship graph + aura categories | kit-structural |
| 8 | **Accessibility** | acquisition model: chase-card count, essence cost, RNG roll depth | Phase 4's acquisition data |
| 9 | **Gear Scaling** | DPS slope per gear tier (§2.10 curves + 3a `items`) | crawl gear brackets |
| 10 | **Volatility** | recency-weighted patch risk (`volatility_score`, T9's decay model), damage-share-weighted over the board | changelog history |

Axis 10 inverts: **low volatility scores high** (a stable build is worth more to
a reader than one balanced last week).

## 3. Complexity — OFF the tally, by design

Complexity is computed 1–10 internally (APL button count, conditional density,
procs/timers the player must track, GCD pressure) and displayed **only** as a
neutral difficulty badge:

| 1–2 | 3–4 | 5–6 | 7–8 | 9–10 |
|---|---|---|---|---|
| Very Easy | Easy | Moderate | Hard | Very Hard |

**Rationale (owner decision):** difficulty is information, not merit. Folding it
into the score would penalise a build for being demanding, which is a
preference, not a quality — the badge lets each reader apply their own sign.

## 4. Gates and confounds — stated up front, per axis

**The D4 gate:** axes 1–3 are sim-derived, and the sim is not trusted for
cross-school comparison until calibration passes the recorded tolerance
(`predictions/CALIBRATION_TOLERANCE.md`) — a gate that **moved to Phase 3a**
with the ≥3-character criterion. Until it passes, axes 1–3 publish
**within-kit** comparisons only, marked accordingly.

Confounds that gate axes 1–3 today, each shrinking as `3a` lands:

| Confound | Effect | Resolves when |
|---|---|---|
| Crawl records no character level | percentile mixes levels | 3a normalisation (or level inference) |
| Target count is inferred, never recorded | cleave/AoE percentiles noisy | 3a inference over `participant_count` |
| Buff state unnormalized | ±1.41× between sessions on the same build | T2 buff model + per-parse aura enumeration |
| Gear unbracketed | percentile conflates build and gear | 3a T4 `items` + §2.10 tiers |

**Launch posture: axes 1–3 marked low-confidence, axes 4–7 and 10 computable at
spec time, axes 8–9 blocked on Phase 4 / 3a data.** An axis that is blocked
renders as `–` with its blocker named, never as a guessed midpoint.

## 5. What `3a` must produce for this spec (the reason it lands now)

1. **`character_scenario_dps`** — per (character, content-scenario) DPS from the
   crawl, the percentile denominator for axes 1–3.
2. **Gear brackets** on crawled characters (T4 `items`), for axis 9's slope and
   axis 1–3's gear confound.
3. **Target-count inference** per parse, for the cleave/AoE split.
4. The **≥3-character calibration** result — the D4 gate's input.

## 6. Worked example (fictitious numbers, format only)

```
Hammerdin (Elric variant)                    74/100 · Difficulty: Hard
  ST  8   Cleave 7   AoE 4?   Burst 6   Consistency 9
  Surv 6  Support 5  Access 3  GearScale 7  Volatility 9
  ? = low confidence: AoE percentile gated on target-count inference (3a)
```
