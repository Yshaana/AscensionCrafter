# Path of Duality is broken in multiple ways (community-reported)

**Status: 🔭 watching** — already reported by multiple other players, so **we do
not submit**. Tracked here because it invalidates data and gates a
recommendation. **Path of Duality spell id: `129243`** (from one of the reports).

**Owner decision, 2026-08-05:**
1. **Ignore Path of Duality logs** for absolute calibration until a fix lands.
2. **Do not recommend Path of Duality**, even when sheet arithmetic favours it.
3. **He plays Path of Intelligence going forward**, for consistency.
4. **We must track bug fixes** and re-open these questions when one appears.

---

## What Duality is SUPPOSED to do (Ascension path documentation, 2026-08-05)

| Clause | Intended | Delivered (measured) |
|---|---|---|
| Attack Power | = your highest primary stat (Str or Agi), 100% | ✅ correct **when it applies** — but cycles on/off |
| **Spell Power** | **gear spell power boosted by 75%** | ❌ **flat +19 only.** At gear SP 229: ~425 intended vs **271** observed — a ~36% shortfall |
| Cross-stat crits | Int → melee/ranged crit, Agi → spell crit | ✅ works, as **rating** (~3.4 stat per rating point) |
| 2H — *Unleashed Force* | +6% all damage | ❌ reported non-functional |
| 1H — *Twin Flurry* | +10% haste | ❌ reported main-hand only |

🚨 **This vindicates the project's v3-era tooltip read of a "×1.75 itemised SP
amp", which v4 retracted for not being visible on the live sheet.** Both were
right about different things — **v3 read the DESIGN, v4 observed the BROKEN
DELIVERY** — and four document versions oscillated between them because the
intended-vs-delivered distinction did not exist until this session. It also
explains the bug report's phrasing exactly: a player expecting ~+172 (75% of
229) and receiving +19 would indeed describe it as *"a difference of 19
Spellpower"*.

⚠ Source tier: external path documentation, corroborated by our own v3 in-game
tooltip read and by the community bug report's expectations. **An in-game
tooltip read of Path of Duality would upgrade this to tier 1** — worth doing
opportunistically, since the intended model is now what the sim serves.

## What the community reports say (owner read the bug DB, 2026-08-05)

| # | Reported symptom | Our own corroboration |
|---|---|---|
| 1 | **AP bonus cycles ON and OFF every ~10–15 s.** One player watched AP oscillate **832 ↔ 1128** (Δ ≈ their Strength) while standing still | ✅ **Exactly what we measured.** Elric read AP **174** then **307** on identical gear/board; 160×1.10 = 176 (bonus OFF) vs (160+121)×1.10 = 309 (bonus ON). **This is the real cause of what we filed as a "path-switch settle delay" and of the 0.548× "Duality AP anomaly"** |
| 2 | **SP bonus not applying** — *"Shifting between Path of Strength and Path of Duality is a difference of 19 Spellpower"* | ✅ **Identical to our measurement**: POS 250 → POD 271 = **+21 gross, +19 after the Lunar Guidance delta**. An independent player reports the same 19 |
| 3 | **AP is added AFTER modifiers**, so Duality AP < (base AP + total Str). One player: 730 actual vs 760 minimum | ⚠ Consistent with our fit `(160 + Str) × 1.10` working while a *pre-modifier* addition would give more |
| 4 | **The weapon-type passives do not work** — 2H +6% damage, 1H +10% haste | 🛑 **`core/builds/stats.py` was applying the 2H `all_damage 1.06` bucket.** Fixed 2026-08-05: not applied, named reason |
| 5 | **Twin Flurry's 10% melee haste affects main hand only** | not independently checked |
| 6 | **Bonus Strength/Agility does not apply**; Agility grants AP only when *lower* than Strength | ⚠ Our captures cannot separate this (Str 121 ≫ Agi 28 throughout) |

## Why this matters to the project, beyond one character

**Data invalidation.** Every one of the owner's five historical calibration logs
and all of 2026-08-05's dummy logs were recorded on Path of Duality with symptom
1 active — so **Attack Power was oscillating mid-parse**. That is a per-hit
input changing on a ~10–15 s cycle inside every window we measured, and it is a
strong candidate for part of the unexplained between-session multiplier spread
(1.41×, session 2b) and for within-window variance on weapon-damage abilities.

**What SURVIVES, and why.** Anything measured as a *ratio inside one log between
two abilities with the same input dependence* is unaffected, because a cycling
AP moves both sides together:
* HftH ÷ HoJ-tick pair ratio (both 0% weapon, both AP-scaled the same) — still valid;
* Holy Shock's SP coefficient (measured against HftH in the same log) — still valid;
* every **proc-rate** result (Hammerdin trigger set, Lightbound Cleave engine-inertness) —
  stat-independent by construction;
* crit-table verdicts and partial-resist fractions.

**What is COMPROMISED:** absolute DPS calibration, anything reading AP as a
constant, and the Duality path model itself.

## 🚨 Correction to our own earlier conclusion (2026-08-05, same day)

Earlier the same evening this project concluded *"Duality has no SP amplifier and
never did"* from the clean path trio. **That is the right measurement with the
wrong interpretation.** The correct statement is:

> Duality's SP grant is **currently bugged to a flat ~+19**, corroborated by an
> independent player reporting the identical 19. Whether the design intends an
> amplifier is **unknown and now unmeasurable** — the 2026-08-04 test that read
> 1.895× may have caught a working Duality, a stale Path-of-Intelligence state,
> or an ON phase of a cycling bug, and those cannot be separated after the fact.

Likewise **`bug_path-switch-stale-stats.md` is superseded**: its "~5–10 s settle
delay" reading was symptom 1 observed through a narrow window. A settle delay
converges once; this oscillates indefinitely.

## What to do when a fix appears

Re-open, in this order: `duality_sp_amp_and_ap_bugged` (this file's slug),
`elric_active_path_and_duality_ap_anomaly`, the Duality parameters in
`core/builds/stats.py`, and primer §3's Duality block. Then **re-capture the path
trio** (relog between each) before trusting any Duality number again.

Fix-detection mechanism (2e T-BUGWATCH): the daily changelog capture already
exists — scan it for `Duality`, `attack power`, `spell power`, `path` and surface
matches against this file's symptom list.
