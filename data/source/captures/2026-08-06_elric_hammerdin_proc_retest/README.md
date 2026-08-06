# Capture — Elric, 2026-08-06 21:34–21:52, **HAMMERDIN PROC RE-TEST**

Tier-1, `source='user_provided'`. Supplied by the owner 2026-08-06, between sessions
`3d` and `3e`, against the protocol in `bugs/bug_hammerdin-trigger-set.md`.

**Purpose: re-test tracker [#200295](https://ascension.gg/bugtracker/view/200295) after
the fix went live, and run the PBL × Lightbound Cleave discriminator alongside it** —
because a Hammerdin-only fix and a general engine fix are indistinguishable if only
Hammerdin is re-tested.

**Full analysis: `primer/FINDINGS_hammerdin_fix_verification_2026-08-06.md`.** This file
is the provenance record.

⚠ **This is the last clean capture before the Phase 2 flip on 2026-08-08.** It is the
reference state for Elric as of Phase 1.

## Files

| File | Bytes | What |
|---|---:|---|
| `stat_export_21.47.06.txt` | 11,307 | AscensionCrafterExport, **before** window A |
| `stat_export_21.52.16.txt` | 11,306 | AscensionCrafterExport, **after** window A (combat end) |
| `2026-08-06-21.34.18 WoWCombatLog.txt` | 2,848,214 | **Window B — Lightbound Cleave isolation**, 235.2 s, 17,902 events |
| `2026-08-06-21.47.49 WoWCombatLog.txt` | 2,215,684 | **Window A — Holy Shock + Judgement**, 258.5 s, 14,263 events |

⚠ **Both logs are shared training-dummy areas** — several other players are logging in the
same file. Every figure in this record and in the findings doc is filtered to
`sourceName = "Elric"`. The raw event counts above are the whole file, not Elric's share
(Elric contributes 1,074 and 1,389 events respectively).

*Byte counts are a check digit: the analysed copies matched these exactly.*

⚠ **Window B has no stat block of its own.** It ran 13 minutes before the 21:47:06
export, on the same gear and the same unbuffed state (its self-auras are a strict subset
of window A's). Treat the 21:47:06 block as applying to it **with that caveat stated**,
not as a same-session pairing.

## Provenance — VERIFIED from the artifacts

| Condition | Status | How verified |
|---|---|---|
| Same-session stat block ↔ log pairing (window A) | ✅ | `ExportedAt 21:47:06` → log `21.47.49`; closing block `21:52:16` → log ends `21:52:13` |
| Not a read-too-early export | ✅ | Blocks differ: MH speed 3.63→3.16, MH damage 526.1–627.7→586.5–705.1, mana 5006→925 |
| Same dummy across both windows | ✅ | `Azeroth Execute Training Dummy` is the primary target in both, read from the logs |
| Single target, window B | ✅ | 164 damage events, one `destName` |
| Path of Intelligence | ✅ | `Path of Intelligence` (84866) in the spellbook capture |
| Pet | ✅ | **none** — `Pet: none` in both blocks, no pet rows in either log |
| Hour of Judgement **not** cast | ✅ | 0 events for `282984`/`282986` from Elric in window A — so **every Hammer from the Heavens is a proc, not periodic delivery** |
| Buffs | ✅ | **Unbuffed, no group.** Self-auras only; no external source in either log |
| Weapon imbue | ✅ | **Absent.** No `Consecrated Weapon` cast, no `200818` from Elric (other players in the zone show theirs, so the log captures the event class fine) |
| Seal | ⚠ | **Window B: none.** Window A: a seal is up (Judgement damages via `54158`) |

## ⚠ Caveats — recorded, not resolved

1. **The two windows are not the same character state.** Window A has a seal up and
   window B does not. That is intended — B is an isolation window — but it means the two
   are **not** a controlled pair for anything except the presence/absence of PBL output.
2. **Mana ended at 925 of 5017** in window A (18%). Not out, but low enough that nothing
   about sustain should be read from this log.
3. **The target is an *Execute* training dummy.** `core/sim/tiers.py:198-199` pins
   `target_health_pct` at 100, so any execute-conditional effect is permanently active
   here and unrepresentable in the sim. Same caveat the `2e` and Mage captures carry.
4. **Window A is not a rotation.** Only Holy Shock and Judgement were pressed, by design.
   Its DPS is not a build measurement.
5. **`Physical Quickness` (840822) applied 81 times** in window A and appears in no
   project doc. It is in the DBC extract. Unmodelled and frequent.

## Headline numbers

| Window | Duration | Total damage | DPS | Casts |
|---|---|---|---|---|
| B — Lightbound Cleave only | 235.2 s | 61,841 | 263 | 53 LC |
| A — Holy Shock + Judgement | 258.5 s | 146,101 | 565 | 39 HS, 25 Judgement |

**Window B damage split:** Lightbound Cleave 43.5% · white swings 42.5% ·
Sword Specialization 12.8% · Siphon Health 1.2%.

**Window A damage split:** white 40.5% · Holy Shock 33.1% · Judgement 7.7% ·
Sword Specialization 5.7% · Righteous Vengeance 4.7% · **Hammer from the Heavens 3.5%** ·
Righteous Smite 1.9% · Consecration 1.7% · Exorcism 0.7% · Siphon Health 0.5%.

## 🚨 What this capture establishes

**Tracker #200295 is fixed, measured.** 11 distinct Hammerdin procs from 64 casts
(**17.2%**) against a stated 20%, versus `2d`'s 1 proc in 129 casts (0.8%).

**The fix did NOT generalise.** Purification By Light fired in window A and **not once**
in window B's 49 Lightbound Cleave hits and 81 white swings.

**Judgements of the Pure is +15% haste, and no haste field can see it.** Both stat
blocks bracket the fight: Frostbolt cast time 1708→1485 ms and main-hand speed
3.63→3.16 are both ratio **1.15**, while `Rating_HasteSpell` is unchanged at 15 and
`GetMeleeHaste` reads 1.02%→1.17%. First live confirmation that the addon's
`GetSpellInfo` cast-time probe (added `2026-08-06c`) is the only working instrument for
buff haste.
