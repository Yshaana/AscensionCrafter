# In-game check queue — owner actions (generated 2026-08-05, pre-2a)

All checks are card-safe (tooltip reads, sheet reads, dummy parses — no rerolls).
Ordered by value to the Phase 2 sim. Protocols follow `tools/audit/protocols.py`
output, refined by hand where the tool emitted a generic template. When a check
is done, resolve the matching `open_questions` slug in
`ingest/export/seed_epistemics.py` in the same session the result lands.

## 1. Active Path + Duality AP anomaly — `elric_active_path_and_duality_ap_anomaly`
**Gates the SP weight (1.00 vs ~1.77) — highest value check on this list.**
- On Elric's CURRENT talent-loaded board: character panel → note the active Path.
- Hover the **melee crit** and **spell crit** breakdown tooltips; screenshot both.
  - If Duality active: Int appears under melee crit AND Agi under spell crit.
  - If another path: base conversions only (Agi→melee, Int→spell).
- Also note sheet **Attack Power** and current Str/Agi — the 0.548× AP anomaly
  needs a second reading before it can be filed in `bugs/`.

## 2. Capped level-scaling formula — `capped_level_scaling_engine_formula`
**One tooltip settles the flat values of all 196 capped catalog spells.**
- Candidate: **Volcanic Shell** (spell 281060, in current pool). Base 500 flat,
  +40/level, SpellLevel 29, MaxLevel 34 — the widest discriminator available:
  - If engine caps as `min(level, max_level)`: tooltip shows **700**.
  - If uncapped (like Hammer from the Heavens): tooltip shows **1740**.
  - Anything else: neither hypothesis; record the number verbatim.
- Backup if Volcanic Shell can't be viewed: **Grove Shot** (278240) — capped
  ≈ 35 vs uncapped ≈ 336.

## 3. Armor pen divisor — `armor_pen_divisor_5_vs_4_2`
- Equip any gear with ArP rating; hover the Armor Penetration line on the sheet.
  - Site calculator right: pct = rating / 5.0
  - Client gt table right: pct = rating / 4.2
- One reading with a known rating value settles it (19% divisor gap).

## 4. Fel Infused Weapon per-level ×3 — `fel_infused_weapon_per_level_3x`
- Read the FIW tooltip in-game at 60; screenshot the sheet (AP + SP) in the
  same session so the AP×0.05 + SP×0.05 terms can be removed.
  - Client DBC right: flat ≈ 4 + (60−spell_level)×1.5
  - db.ascension.gg right: flat ≈ 4 + (60−spell_level)×4.5

## 5. Mental Quickness exclusivity — `mental_quickness_exclusivity`
- Read live tooltips of **Mental Quickness**, **Holy Focus** (capstone), and
  **Answered Prayers** side by side. Look for any "does not stack / only the
  highest" clause naming the others or "similar effects".
  - Clause present → shared bucket; add to `seed_exclusivity.py`.
  - No clause on any of the three → provisionally independent (tooltip tier;
    a proc/damage test would upgrade it).

## 6. Brutal Crusader — `brutal_crusader_effect`
- Read the effect text on **Light's Hope** (link it or view in dungeon journal /
  AH if not owned). If it's a Crusader-family Str proc, Str's weight changes;
  record the exact wording either way.

## 7. Nurturing Instinct healing clause — `nurturing_instinct_healing_clause`
- Read the live tooltip; check whether the Agility-healing clause names spells
  generically ("healing spells") or a list. If generic, it plausibly touches
  Holy Shock / Holy Finish heal components — still likely marginal at Agi 46,
  but record the wording before the reroll decision.

## Longer checks (need a dummy + combat log, ~10–15 min each)

## 8. Lightbound Cleave post-patch procs — `lightbound_cleave_post_patch_procs`
- On a dummy: queue ONLY Lightbound Cleave off-GCD over autos for ~5 min
  (~100 LC hits). Count Hammerdin stack gains, JotTH procs, PBL procs in the
  log (capture with ALC, parse with `tools/log_parser/parse_log.py`).
- Control window: same duration pressing Judgement/Holy Shock normally, to
  confirm the engines proc at all in the session.
  - Verdict unchanged: 0 Hammerdin procs from LC.
  - Patch changed eligibility: nonzero — §2's class-tag table needs an edit.

## 9. Titan's Grip tax on Holystrike — `titans_grip_tax_on_holystrike`
- ~100 LC non-crit hits under Titan's Grip, then ~100 with a single 2H (same
  MH weapon). Compare mean non-crit damage; use Dawnreaver as the physical
  control in both windows.
  - Tax applies to weapon half: LC shifts ~−10% like Dawnreaver.
  - Tax skips magic half: LC shifts less than Dawnreaver.

## Passive / observational (no dedicated session needed)

## 10. Reroll upgrade-chance slot scope — `reroll_upgrade_chance_slot_scope`
- During normal upgrade fishing, log every roll outcome twice: rolls landing
  in the slot holding the partial vs. any other slot. Needs ~200 rolls
  accumulated over time — a notes file is enough; no dedicated testing.
