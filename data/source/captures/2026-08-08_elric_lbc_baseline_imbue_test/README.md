# Capture — 2026-08-08 Elric: LBC unbuffed baseline (IC 0/3) + Consecrated Weapon 3-step imbue test

> **`FINDING 2026-08-08`** — owner-run test capture, protocol set by the oversight chat
> the same day. True as of its date, not maintained.

## Contents

| file | what |
|---|---|
| `stat_export_12.50.10_unbuffed.txt` | same-session stat export, unbuffed, NO imbue — pairs with the combat log |
| `stat_export_consecrated_weapon_3step.txt` | three exports in one file: unbuffed (13:05:01) → MH imbued (13:06:20) → both imbued (13:07:13), sheet allowed to settle between readings |
| `2026080812.50.42 WoWCombatLog.txt` | 37,932 events, 12:50:42 → 13:00:31 local (~9.8 min). Combat ended before the imbue test began (13:05+), so every logged hit is imbue-free |

**Integrity:** file complete (last line is an ordinary event at 13:00:31); window,
line count and timestamps stated above per the capture rule. Target identity captured
in the log itself: **Azeroth Execute Training Dummy** (⚠ dummy level not established —
see crit-rate note below).

## 🛑 Load-bearing context

- **The owner holds Improved Cleave 0/3 — he NEVER rolled the card** (stated
  2026-08-08, correcting an assumption in `3m`'s work-order framing). Consequences:
  1. **This log cannot discriminate the 2026-08-10 Improved Cleave fix** — with no
     talent held, pre-fix and post-fix predictions are identical.
  2. **Monday's patch changes this character's damage by exactly ZERO.** It changes
     the card's *chase value* only (see `prereg_3m_b_improved_cleave.md` B5: the card
     adds ~578/hit pre-fix, ~74/hit post-fix on this weapon).
  3. **The fix-shipped detector cannot come from the owner's own captures.** It must
     come from post-Monday parses of cohort members who DO hold the card (e.g. Blix)
     — this amends `SESSION_3N_PRIMER.md` E1's detector note.
- Path of Intelligence; unbuffed; no seal active assumed for the dummy window (verify
  from the log's aura events before relying on it).

## Measured (oversight chat's independent parse — re-derive before seeding)

**Lightbound Cleave (907304), IC 0/3, no imbue:** n=143 hits — 96 non-crit avg
**523.8**, 47 crit avg 1,024.5 (crit ratio **1.956**). Sheet MH 559.5–662.2
(avg 610.85, speed 3.63).

- Decode-only base `0.65×W + 62` = **459.05** → observed/base = **×1.141**.
  Candidate: the board's Holy-chain multiplier double-dipping on the Holystrike
  hybrid. NOT seeded — `3n` should compute the sim's talent layer for this exact
  board and score the residual properly.
- Crit rates run ~2σ LOW of sheet on both tables (LBC 32.9% vs 42.24%, z=−2.27;
  autos 19.7% vs 24.85%, z=−1.68) — both in the same direction, consistent with a
  higher-level dummy (crit suppression). **Provisional** (small n, dummy level
  unknown) — flagged per the <60s/thin-data rule.
- Sword Specialization (16459): n=41, non-crit avg 462.5. Autos: 198 swings.

**Consecrated Weapon rank 6, three-step (per weapon, both steps linear):**

| quantity | per imbued weapon | note |
|---|---:|---|
| Holy SP (sheet) | **+172** | = 2 × 86, PoI ×2.0 doubling exact |
| Bonus Healing | **+86** | the undoubled instrument — aura 345's +86 raw, re-confirmed |
| Attack Power | **+80** | raw aura-344 grant is 73 → **×1.096 ≈ one ×1.10 (Deadliness-shaped)** |
| Ranged AP | **+80/81** | same grant reaches RAP |

- 🚨 **The `2e` "+88 AP per imbue" does NOT reproduce — today it is +80.** The ×1.21
  residual is RETIRED as a current fact; the open question is now the 88-vs-80 delta
  between 2026-08-05 and 2026-08-08 (board change? second ×1.10 active then?).
  Update the `consecrated_weapon_grants_and_stacking` seed accordingly — and its
  siblings, per the blast-radius rule.
- ⚠ **Unexplained instrument finding:** each imbue step raised the sheet's
  weapon-damage line on **both** weapons by a flat amount (+56.0 MH, +54.3 OH, both
  ends of the range, per step) — equivalent to the weapon-damage formula seeing
  ~+216 attack power per step against the displayed +80. Speed-proportional
  (56.0/3.63 ≈ 54.3/3.53 ≈ 15.4). Nothing currently models the sheet's
  weapon-damage line this way. Recorded, not derived.

## Open questions this capture feeds

1. The ×1.141 LBC residual vs the board's computed talent layer (`3n`).
2. The 88-vs-80 imbue AP delta vs `2e`.
3. The sheet weapon-damage +15.4×speed-per-step anomaly.
4. Azeroth Execute Training Dummy's level/identity (crit suppression hint).
5. Optional control: an identical post-Monday LBC capture should show **no change**
   (owner holds no IC; "Regular Cleave was unaffected") — a cheap confirmation the
   patch touched only what it claimed.
