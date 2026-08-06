# Session 2a — Sim Foundation: Combat Engine, Content Profiles, Ability Model, BuildSpec

> **`HISTORICAL`** — the record of a past session or a completed phase. Immutable. It **may contain claims that are false today**, and that is correct rather than a defect — it records what was believed at the time. **Never citable as current truth.** *(Classified `3f` F8c, 2026-08-07.)*

**Date:** 2026-08-05 · **Scope:** PHASE_2 T1–T4 · **Status:** ✅ complete

Phase 2 begins. Four new modules land the simulation foundation; no game-mechanic
verdict changed, two new open questions filed, one data gap discovered.

---

## What was built

| Module | Task | Contents |
|---|---|---|
| `core/sim/combat_engine.py` | T1 | Rating conversions **from `dbc_gt_tables`** (anchor-validated at level 60, raises on mismatch — never hardcoded retail), white/special/spell attack tables, expertise/dodge/parry, armor DR, partial resist, crit multipliers. `EngineDataError` on missing data — no silent defaults |
| `core/sim/content.py` | T2 | `ContentProfile` + 8 presets, `Role`/`Metric` enums, `SimResult` (all metrics always computed). Raid preset durations **derived from scouted Zul'Gurub fastest-kill data** (mean 48s, n=50, bias stated); everything invented says `assumption` in its provenance string |
| `core/sim/ability_model.py` | T3 | `ResolvedAbility` built **only** via `spell_profile(mode='fast')` — follows rank-gap redirects, refuses ambiguous rank lines. `expected_hit`/`roll_hit` with per-component provenance. Full `term_type` vocabulary (school-scoped SP resolves through `effective_spell_power(school)`; BH routes to healing). Outlier coefficients >3.0 **excluded** (not clamped), named warning citing the open question |
| `core/builds/spec.py` + `stats.py` | T4 | `BuildSpec` (ranks mandatory, slot budgets enforced, `wielding()` for path clauses), `CharState`, `compute_stats()` — sheet mode (stats_override = FINAL values) vs component mode (gear + path grants + measured conversions; unmodelled talents warn by name) |
| `tools/audit/check_sim_engine.py` | — | 16 checks incl. the PHASE_2-mandated `mean(roll_hit × 100k) ≈ expected_hit` guard (passes at 4σ: 270.38 vs 270.35) and an end-to-end HftH attribution reproduction |

Validation: `py tools/audit/check_sim_engine.py` (all pass), `check_core_purity.py`
(0 violations), full `py cli/rebuild.py` green.

## Decisions made (and why)

1. **Trigger-attributed magnitudes ARE summed into `expected_hit`**, flagged
   `calibration_anchor=False`. The kickoff note said "don't let them anchor
   calibration" — the first implementation over-read that as "exclude from
   computation", which zeroes 444 cards (Hour of Judgement's entire damage is its
   trigger chain). Corrected mid-session: computed, warned, never an anchor, and
   listed separately in `triggered_components` so calibration can subtract them.
2. **Outliers excluded, not clamped** — a clamped 3.0 is still a fabricated number.
3. **Crit suppression is warned about, not modelled** — no fabricated retail
   constant. Filed as `melee_crit_suppression_vs_higher_level` (the owner's own
   parse hints it exists: sheet 21.76% vs autos 16.2%, but n=37).
4. **Talent stat/multiplier modelling deferred to calibration (2b/2c)** —
   component-mode `compute_stats` names every unmodelled talent in warnings
   rather than silently contributing zero. Sheet mode (stats_override) is exact
   today and is the calibration-anchor path.
5. **Duality is parameterised, not assumed**: SP amp defaults to the measured
   1.895 (not the tooltip's 1.75), AP factor defaults to the measured 0.548
   anomaly — both overridable, the anomaly always warns, citing the open question.

## Found along the way

- 🚨 **HftH's confirmed +9.1% SP / +9.1% AP coefficients are not queryable.**
  They live in doc prose and `confirmed_facts` only — `spell_scaling` has no rows
  for 282987 or the cards. The resolver-served formula is flat-only 122–145
  (~45% understatement at the owner's stats). Filed as
  `trigger_attributed_coefficients_not_in_spell_scaling` — needs the same
  per-case judgment as 1b's multi-path attribution decision, so not rushed at
  session close. **First item for 2b.**
- **Hour of Judgement carries its own confirmed periodic effect** (21 + 2/level
  → 81 at 60, `dbc:Spell.dbc:282984:effect0`) on top of the attributed HftH flat
  and its own SP/AP 0.05 tooltip terms. The sim surfaces all four components
  with per-term provenance.
- **Daily patch check (2026-08-05):** Sun Cleric/Venomancer (CoA) rework, all
  realms — nothing touching our builds or seeds. 2026-08-04 Darkmoon: PvP-only
  reductions (Consecrated Weapon −20% *in PvP*; no PvE impact), plus a new
  talent "Authority" (Execution Sentence synergy on Shield of Righteousness) —
  mildly relevant to build doc §8's Execution Sentence chase note, not acted on.

## Known 2a limitations (2b picks these up)

- `expected_hit` models ONE event (one direct hit or one tick); direct-vs-DoT
  term splitting inside a single ability is not done (`n_ticks()` exposed).
  Hybrid-school mitigation (physical/magic halves) not split either — warned.
- Combo-point terms present but not parameterised (warned, applied at 0 CP).
- AoE reports per-target values; total-at-N-targets deliberately refuses when
  `damage_split_behavior`/falloff is NULL.
- `spell_hit_pct` floor (1% retail rule) and glancing values are
  retail_hypothesis — flagged in output, candidates for calibration.

## Addendum (same day, post-audit): the attribution decision is MADE

Reviewing the 2a audit's kickoff brief with the owner, the Priority-0 decision
was taken immediately instead of waiting for 2b:

- **Owner decision (2026-08-05): trigger-reached coefficients live on the
  trigger TARGET, never duplicated onto cards.** Rationale: truth stays where it
  is true; no per-card duplication; and 2b's per-source-spell event model (which
  must split HoJ's own tick / HftH pulse / own direct terms into separate
  events) composes only on this shape. Cards-side seeding was rejected — it
  conflates the pulse event with the card's own hit (282984 already carries its
  own SP/AP 0.05 terms).
- **Implemented today (seed half only):** `ingest/export/seed_hand_coefficients.py`
  — append-only, owns `spell_scaling` rows with `source='db_ascension_gg'`
  (tier 3); first rows are 282987 SP 0.091 / AP 0.091. Rebuild is **19 steps**.
- **Deliberately NOT implemented today:** the resolver/ability-model follow
  (pull `spell_scaling` per component `source_spell_id`, bounded/single-path,
  `confidence='inferred'` when trigger-reached). That belongs with 2b's
  per-event component rework, which touches the same code. The open question is
  `in_progress`, and **the ~45% HftH understatement in sim output STANDS until
  2b lands the follow.**

## Next session: `2b` — three sim tiers (T5) + uncertainty propagation (T6)

Start by finishing `trigger_attributed_coefficients_not_in_spell_scaling` (the
serving half) — fast_sim on the Paladin build is wrong by ~45% on its top
ability until then.
