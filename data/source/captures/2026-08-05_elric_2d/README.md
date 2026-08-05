# Capture — Elric, 2026-08-05 (session 2d, T1 partial)

Tier-1, `source='user_provided'`, supplied in chat by the owner on 2026-08-05.

- `stat_export_unbuffed.txt` — AscensionCrafterExport addon output. Owner-stated
  context: **active Path = Duality**; buff state = **Swift Retribution only**
  (source unidentified — not the catalog talent 53648, which is not slotted);
  no group buffs, no consumables.
- `board_spell_ids.txt` — 55 spell ids (30 abilities + 25 talents), addon-read.
  All 55 resolve; talent ranks match build doc §7 exactly. Ability ids are
  card-canonical (Rank-1/catalog ids), not the level-60 cast ids.
- Holy Shock R4 tooltip (owner screenshot, in chat): **562–608 damage /
  676–732 healing, 281 mana, 6 s cooldown, id 20930** — byte-exact match with
  the 2c G4 extraction (sub-spells 25902/25903). Confirms the tooltip renders
  sub-spell base values UNSCALED (no stat term at SP 271), so it does NOT
  settle `holy_shock_bonus_coefficient_0429`.

⚠ Known addon gaps found with this capture: **enchants are not exported**
(suspected source of the ~+18 SP accounting residual), and per-item damage is
DPS-only (character-level min–max IS present, which is what the sim needs).

🛑 Same-session rule: combat logs calibrated against this export must be
recorded with this gear/spec unchanged. Dummy logs were requested in the same
chat session; if gear changed first, re-export.

## Path-trio captures (added later the same session)

- `stat_export_POD_relog_clean.txt` — **the calibration state** (owner confirmed
  Path of Duality → quit → relog → export). Identical to the earlier post-relog
  capture. SP 271 = gear 229 + Duality flat ~19 + Lunar Guidance 12%×199;
  AP 307 ≈ (160 + Str 121) × 1.10 Deadliness. All crit values close exactly via
  Δrating/14 + ΔInt/61 against the other captures.
- `stat_export_POI_relog.txt` — Path of Intelligence. Flat grants match primer
  §3 exactly (+79 Int, +40 Spirit). SP 638 ≈ 2×(items 229 + LG 31) + an
  unquantified PoI flat-SP grant (~118 outside the double, or ~59 inside it —
  under-determined from one capture).
- `stat_export_POS_contaminated.txt` — ⚠ **do not use for stat truth.** SP 500
  on a path with no SP clause = 1.995 × (items + LG): PoI's doubling still
  active (the path-switch staleness bug, second demonstration — see
  `bugs/bug_path-switch-stale-stats.md`). Owner confirmed no relog preceded it.
  Flat Str curve (+34) and PoS AP formula applied correctly in the same
  capture. Valuable as bug evidence and for the flat-grant/AP data points only.
- `stat_export_POS_relog_clean.txt` — the corrected Path of Strength capture
  (relog done). **SP 250 = items 229 + LG 12%×180 = 250.6 exactly** — no
  doubling, no Duality flats; exactly half the contaminated reading. Confirms
  the Duality flat-SP grant by difference too: POD 271 − POS 250 − ΔLG 2.3 ≈
  +19. ⚠ One residual: weapon-damage display deltas between paths do not reduce
  to ΔAP/14×speed alone (PoS MH reads +36 over POD where ΔAP predicts +10) — a
  path-scoped %-modifier (candidate: PoS 2H "+10% physical") appears in the
  sheet display. Recorded, not resolved.
- `stat_export_unbuffed.txt` — the FIRST capture of the day, pre-relog after a
  PoI→PoD switch: AP 174 stale (correct value 307). Keep for bug evidence;
  superseded by `stat_export_POD_relog_clean.txt` for calibration.

**⚠ Correction, later the same session:** the "stale until relog" mechanism is
withdrawn — path grants apply with a **~5–10 s settle delay** after a switch
(owner observed the sheet updating). Every capture below labelled
"contaminated" was exported inside that window; all post-relog captures are
settled and stand unchanged. **Protocol going forward: switch → wait ~15 s →
read/export.** A third mid-settle flavor was captured at 21:08 (weapon speeds
×1.202 fast with AP/SP already correct) — kept as
`stat_export_POD_midsettle_weaponspeed.txt` if needed.

**Measured path facts from this trio (all post-relog unless noted):**
Duality = NO SP amplifier (accounting closes ±1 with none); Duality converts
Int→melee crit RATING (199 Int → +59 rating) and Agi→spell crit RATING
(28 Agi → +8 rating), ~3.4 stat per rating point; Duality grants ~+19 Int and
~+19 flat SP (damage AND healing); PoI's clause is the item+effect SP doubling
(×2.0 measured); pathless-baseline AP = 141 at Str 121 (PoI capture).
The 2026-08-04 "Duality SP amp 1.895×" attribution is superseded — that test
used rapid path toggling, the exact state the staleness bug corrupts.
