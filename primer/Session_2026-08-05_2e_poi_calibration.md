# Session 2e — the PoI calibration, the buff layer measured, and a resolver widening

> **`HISTORICAL`** — the record of a past session or a completed phase. Immutable. It **may contain claims that are false today**, and that is correct rather than a defect — it records what was believed at the time. **Never citable as current truth.** *(Classified `3f` F8c, 2026-08-07.)*

**Date:** 2026-08-05 (late night) · **Scope:** `PHASE_2E` T1–T4, T6–T11 (T5
deferred; T3b half-deferred, reasons recorded) · **Status:** ✅ complete.

The owner supplied, live during the session: the **Window A/B capture pair**
(unbuffed + buffed logs with byte-identical-to-`2d` stat exports), the
**incremental buff capture** (one export per buff added — the session's best
data), the **isolation captures** (Elixir of Agility, geared-no-talents, naked),
and the `2d` PoD logs. He also reported **tracker #200295 fixed
`[Pending Restart]`** — hours after submission.

All capture analysis lives in
`data/source/captures/2026-08-05_elric_2e_poi_baseline/README.md`; the
calibration report in `predictions/calib_2026-08-05_2e_poi.md`. This handoff
records only what they don't.

---

## 1. Headline results

1. **The Holystrike residual was the weapon input** — LC 1.00×, Dawnreaver
   0.99× with same-session stats. `holy_holystrike_ratio_weapon_input_confound`
   is demonstrated, not just diagnosed.
2. **The Holy residual is two mechanisms** (missing coefficients on
   out-of-catalog spells at ~2.2×; a real ~1.24× on coefficient-bearing ones),
   plus a third term that grows with buffs. Never one multiplier.
3. **11,417 of 16,566 extracted spells had never been decoded** — the resolver
   walked only catalog routes. New `via='dbc_only'` class: 11,857 spells gained
   magnitudes. Same failure family as `2b`'s 686 zero-magnitude siblings and
   `1x`'s 98%: data present, query narrow.
4. **The buff layer is arithmetic now** (`core/sim/buffs.py`), and
   **BonusHealing = undoubled SP** is a standing instrument.
5. **Consecrated Holy Weapon (200818) is 25.1% of buffed damage and absent from
   the extract entirely** — now the largest modelling gap and top tooltip ask.
   The extract-scope fix is specified (log-observed ids +
   `SpellItemEnchantment.dbc`).
6. Gate: **3 of 8 within tolerance** (was 1 of 7), every weapon ability within
   ±1%, every miss carrying a named mechanism.

## 2. Code shipped

| What | Where |
|---|---|
| Swing layer: autos (white table + glancing), seal riders (measured rate), RV as derived DoT, seal→judgement mapping | `core/sim/swings.py`, wired into **both** fast and medium tiers |
| Measured buff model + `BUFF_SETS` | `core/sim/buffs.py` |
| `dbc_only` fourth source class, scoped delete widened | `ingest/dbc/resolve_numeric_formulas.py` |
| Glancing 32.6% measured constant (retail 24 named, rejected) | `core/sim/combat_engine.py` |
| D3 bucket scoring: highest member only, suppressed members named | `core/sim/talents.py` (Elric board: ×1.155 unchanged — confirmation, as predicted) |
| `bugfix_watch_sweep` (anchor-keyword design) + `extract_staleness_sweep`; `_extracted_at` stamps | `tools/audit/audit_gaps.py`, `ingest/dbc/build_dbc_index.py`, `load_extract.py` |
| Volatility decay weighting (stated priors) | `core/spells/volatility.py` |
| `predictions.patch_id` backfilled (patch 10, with reasoning) | `ingest/export/seed_predictions.py` |

## 3. Session's own errors, kept on the record

1. **Copied a combat log while the game was still writing it** and analysed the
   truncated copy. The verdict happened to survive, but the method was wrong —
   check file stability before reading a live log directory.
2. **First parse attempt hand-indexed CSV columns** and read `glancing` where it
   wanted `critical` (0% crit everywhere — impossible on its face). The shipped
   parser's named fields were right all along; CLAUDE.md's stale "unverified"
   note (which invited re-derivation) is corrected.
3. **The imbue-doubling "anomaly" I flagged was my own error** — resolved within
   the session by the incremental capture (+86 raw, doubled to 172). The
   surviving question moved to `2d`'s Duality-sheet reading, flagged for
   re-measure.
4. **T3b's histogram discriminator was underpowered as designed** (cluster
   separation ≈ weapon-roll σ) — the protocol missed the intrinsic variance. The
   sharper time-series test found short-lag correlation **−0.29 where cycling
   predicts +0.26** (n=25 pairs): weak evidence the sheet oscillation was not
   expressing in combat damage. `duty_cycle` stays `None`.

## 4. Deferred, with reasons

- **T5 (bug-DB browser access):** needs the owner's live Chrome session
  mid-conversation; not available this session. The task spec stands in
  `PHASE_2E` §T5.
- **T3b's underperformance detector:** PoD parses are excluded from absolute
  calibration by owner decision, so a per-path residual mode has no valid PoD
  input until a fix lands; design recorded in `PHASE_2E` §T3b and the bug file.

## 5. What the next session starts with

1. 🔴 **Post-restart re-test of #200295** — Hammerdin from Judgement/Holy Shock
   (confirms the fix) **and the PBL × Lightbound Cleave discriminator**
   (separates a Hammerdin-only fix from a general engine fix — they look
   identical if you only re-test Hammerdin). Protocol in
   `bugs/bug_hammerdin-trigger-set.md`. If general: re-open the class-tag
   engine-intake practice; if specific: §4's practice stands.
2. **Build-doc §2/§11 revert is conditional on that re-test** — not on the
   tracker status.
3. **Live tooltip for Consecrated Holy Weapon (200818)** — 25.1% of buffed
   damage, no other route to its formula until the enchantment DBC is extracted.
4. `--with-dbc` scope widening when convenient (spec in
   `extract_scope_missing_log_observed_ids`).
5. `3a` is unblocked: `2e`'s exit criteria are met with the two recorded
   deferrals.

## 6. Owner decisions pending (unchanged from session start)

- `holy_shock_bonus_coefficient_0429` — seed the measured ~0.40 or hold for a
  stating tooltip.
- Whether the ~16 MB of raw combat logs under `data/source/captures/` get
  committed (currently staged untracked; tier-1-irreplaceable by the project's
  own storage rules, but the owner rules on repo weight).
