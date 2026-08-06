# Capture — Elric, 2026-08-06 19:15–19:56, **FROST MAGE, Path of Intelligence**

Tier-1, `source='user_provided'`. Supplied by the owner 2026-08-06, between sessions
`3d` and `3e`, against the protocol in `primer/ADDENDUM_3D_to_3E_mage_capture.md` §5.

**This is the project's first non-paladin calibration capture.** Every prior absolute
calibration — `2c`, `2d`, `2e`, and the whole `3b`/`3c` gate line — ran on the owner's
Hammerdin. The audit in `primer/AUDIT_3C_ADVERSARIAL.md` §5 named that single-character
validation surface as the largest structural risk in the project; this is the first
capture that reduces it.

**Full analysis: `primer/FINDINGS_mage_capture_2026-08-06.md`.** This file is the
provenance record.

## Files

| File | What |
|---|---|
| `Unbuffed Mage.txt` | AscensionCrafterExport, `ExportedAt 19:15:41` |
| `Buffed Mage.txt` | AscensionCrafterExport, `ExportedAt 19:21:39` |
| `2026-08-06-19.16.56 WoWCombatLog.txt` | **Window A — unbuffed dummy**, 214.2 s, 12,719 events |
| `2026-08-06-19.22.22 WoWCombatLog.txt` | **Window B — buffed dummy**, 179.9 s, 11,872 events |
| `2026-08-06-19.45.40 WoWCombatLog.txt` | **Window C — Scarlet Monastery**, 619.1 s, 22,896 events, **288 ALC build records** |

Site reports: [110](https://darkmoon.ascensionlogs.gg/reports/110/encounters) ·
[111](https://darkmoon.ascensionlogs.gg/reports/111/encounters) ·
[112](https://darkmoon.ascensionlogs.gg/reports/112/encounters)

## Provenance — VERIFIED from the artifacts, not asserted

| Condition | Status | How verified |
|---|---|---|
| **Same-session stat block ↔ log pairing** | ✅ | `ExportedAt 19:15:41` → log `19.16.56`; `19:21:39` → log `19.22.22`. **The `ExportedAt` field was added to the addon this same afternoon precisely so this is checkable rather than assumed** (`2e`: a stale stat block is not a degraded input, it is the whole error) |
| **Not a read-too-early export** (`2d`/`2e` trap) | ✅ | Blocks differ: Int 321→352, SP 780→840, ManaMax 6097→6562, BonusHealing 306→333. A zero-delta pair would be suspect |
| **Same dummy both windows** (`2d`: dummy identity is a calibration variable, 10–18%) | ✅ | `Azeroth Execute Training Dummy` is the **sole** damage target in both A and B — read from the logs, not from memory |
| Single target, windows A/B | ✅ | 222 / 227 damage events, one destName each |
| Path of Intelligence | ✅ | `Path of Intelligence` (84866) present in the addon's spellbook capture |
| Pet present and identified | ✅ | `Lesser Water Elemental`, level 60, AP 460, 97.6–104.8 @ 1.80 |
| Buff applied | ✅ | **Arcane Intellect only.** Int +31 reproduces `2e`'s measured Arcane Brilliance grant exactly |

## ⚠ Caveats — recorded, not resolved

1. **Windows A and B are not equal length** (214.2 s vs 179.9 s) **and are not the same
   rotation.** Casts/min differ (Ice Lance 3.4 → 5.0; Innervate and Cold Snap appear only
   in B). 🛑 **The DPS ratio between them is therefore NOT a buff measurement** — see
   FINDINGS §2. The per-hit non-crit averages are the durable quantity.
2. **The buffed export was taken mid-combat** — `PowerMax: 6562 (current 4466)`, 68% mana.
   Stats are unaffected; note it before reading anything from the mana figure.
3. **The target is an *Execute* training dummy.** `core/sim/tiers.py:198-199` fixes
   `target_health_pct` at 100, so any execute-conditional effect is permanently active
   here and unrepresentable in the sim. Same caveat the `2e` capture carries.
4. **Window C is unsegmented.** Boss and trash pulls are mixed; `capture_scopes`
   distinguishes `boss_single` from `trash_bundle` and this log needs splitting before
   any per-encounter number is read from it.
5. **The rotation is self-described by the owner as sub-par** — 175 `SPELL_CAST_FAILED`
   against 75 starts in Window A. This does not invalidate the capture (the sim is scored
   against the rotation actually run, and every *input* is clean) and it usefully stresses
   the idle-GCD path a tight all-instant rotation never reaches.

## Headline numbers

| Window | Player | Pet | Pet share | Duration | DPS (incl. pet) |
|---|---|---|---|---|---|
| A — unbuffed dummy | 296,031 | 15,453 | **5.0%** | 214.2 s | 1,454 |
| B — buffed dummy | 345,712 | 19,578 | **5.4%** | 179.9 s | 2,030 |
| C — Scarlet Monastery | 940,460 | 14,385 | **1.5%** | 619.1 s | — (unsegmented) |

**Per-hit non-crit averages, A → B** (the durable quantity):
Frostbolt ×1.027 · Icicle ×1.003 · Ray of Frost ×0.940 · Waterbolt ×0.994 ·
Frozen Orb ×1.070 · Frost Fever ×1.080. **The buff barely moves per-hit damage**, against
the paladin's ×1.45 — consistent with Arcane Intellect alone being applied.

Window C targets, by Elric+pet damage events: Scarlet Centurion 149 · Scarlet Champion 142
· Scarlet Monk 109 · **Scarlet Commander Mograine 75** · Scarlet Myrmidon 71 · Scarlet
Abbot 58 · Scarlet Wizard 57 · Scarlet Chaplain 42 · Scarlet Defender 35 ·
**High Inquisitor Whitemane 34** · **High Inquisitor Fairbanks 23** · Scarlet Sorcerer 19.

## 🚨 What this capture overturns

**`SPELL_CAST_SUCCESS` and `SPELL_CAST_START` are disjoint by cast type.** In Window A,
Elric's instants log `SUCCESS` and never `START` (Ice Lance 12, Ray of Frost 5, Frozen Orb
3, …); his cast-time spells log `START` and never `SUCCESS` (**Frostbolt 74**, Hydricles 1).
Frostbolt was cast 74 times and produced **zero** `SPELL_CAST_SUCCESS` events while landing
52 non-crit hits.

`3c` established *"the site's `casts` IS `SPELL_CAST_SUCCESS` — 93% and 97.3%"* and on that
basis **withdrew** its own objection that `casts` under-reads and would bias the corpus,
filing it *"wrong at character level."* That measurement was taken on an **all-instant
Hammerdin**. It is correct there and does not generalise: for a cast-time caster the site's
`casts` counts only the instant portion of the rotation.

🛑 **Consequence for `PLAN_3C` C2 (log admissibility):** its APM ratios — Boomcat 0.24
against Elric's known death case at 0.38 — make every cast-time caster read as artificially
low-APM, i.e. look like a death-deflated parse. Check `casts` provenance, and whether
Boomcat is a caster, **before** C2 ships. Detail in FINDINGS §1.

## Also settled here

* **Cast time: the DBC base is not what is cast.** Frostbolt R11 — DBC base **2000 ms**
  (`casting_time_index` 5), client `GetSpellInfo` position 7 **1404 ms**, log back-to-back
  `SPELL_CAST_START` floor **1273 ms**. A sim reading the DBC would model it ~42% slow.
* **`GetSpellInfo` uses the 4.x+ signature on this client** — position 4 is mana cost,
  **position 7 is cast time**, identified by contrast against an instant (Ice Lance reads 0)
  and confirmed against a channel (Blizzard also reads 0 — channels are indistinguishable
  from instants in the client API; `attributes_ex & 0x44` in the DBC is the only route).
* **Pet contribution is small and separable for free** — the pet is its own `sourceName`.
  1.5–5.4% bounds the unmodelled-pet gap for `PLAN_3C` C5.
