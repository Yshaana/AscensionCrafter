#!/usr/bin/env python3
"""Seed doc-confirmed combat-table facts into `doc_confirmed_mechanics`.

⚠ Reworked in session `1b` (Phase 1 T4). This script previously ALTERed four
columns onto `spells` (crit_table / rolls_hit_check / hit_table /
proc_icd_seconds). T4's rule is **one home per fact**: those values now live in
`spell_mechanics`, resolved from this staging table by
`core/spells/mechanics.py`. The `spells` columns are gone — anything still
querying `spells.crit_table` should query `spell_mechanics.crit_table` instead.

Nothing here is guessed: only values already confirmed in the primer/handoff are
seeded, everything else stays absent ("unconfirmed", not "no").
"""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from config import DB_PATH  # noqa: E402  - repo-root path resolution (see config.py)

conn = sqlite3.connect(str(DB_PATH))
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS doc_confirmed_mechanics (
    spell_id    INTEGER NOT NULL,
    field       TEXT NOT NULL,      -- a spell_mechanics column name
    value_text  TEXT,               -- exactly one of value_text/value_real is set
    value_real  REAL,
    source_tier TEXT NOT NULL,      -- §2.2 tier name
    evidence_ref TEXT NOT NULL,
    confidence  TEXT NOT NULL,
    notes       TEXT,
    PRIMARY KEY (spell_id, field)
)""")
cur.execute("DELETE FROM doc_confirmed_mechanics")  # owns its own output


def spell_id(name):
    cur.execute('SELECT id, name FROM spells WHERE name=?', (name,))
    rows = cur.fetchall()
    if len(rows) != 1:
        print(f'  ! WARNING: {name!r} not found or ambiguous in this export, skipping: {rows}')
        return None
    return rows[0][0]


# --- crit_table (measured, primer §1 / seed_confirmed.py) ---
CRIT_TABLE = [
    ('Lightbound Cleave', 'spell', "Holystrike crit-table resolution, primer §1. Measured 38.1% crit against Consecrated Holy Weapon (Holy, 39.0%) - tracks the Holy source, not the physical melee source (16.2%-20.0%)."),
    ('Dawn Strike', 'spell', "Holystrike crit-table resolution, primer §1. Measured 33.3% crit, same Holy-table pattern as Lightbound Cleave."),
    ('Sword Specialization', 'melee', "Physical, measured 20.0% crit alongside melee autos (16.2%) in the same Holystrike-resolution sheet, primer §1."),
    ('Righteous Vengeance', 'none', "Confirmed-no-crit periodic effect - 0% across 4 parses (later 303 hits / 9 characters / 4 Paths), primer §1 / seed_confirmed.py."),
]
# NOTE: "Consecrated Holy Weapon" (build_paladin-hammerdin.md §9, 39.0% crit Holy source)
# and "PBL ground" (primer §1's periodic_no_crit fact, 0%/32 ticks) do NOT match any
# spells.name in the current spell-export.json - flagged, not guessed (duplicate-name-trap
# discipline). Closest catalog match for the former is "Consecrated Weapon" (id 200809),
# but the name doesn't match exactly and this script will not assume they're the same
# spell. Resolve manually against a live tooltip/spell ID before seeding these two.
print("  ! UNRESOLVED (not guessed): 'Consecrated Holy Weapon' (build_paladin-hammerdin.md §9) "
      "has no exact spells.name match - closest is 'Consecrated Weapon' (id 200809), not assumed identical.")
print("  ! UNRESOLVED (not guessed): 'PBL ground' (primer §1 periodic_no_crit fact) - abbreviation "
      "does not resolve to any spells.name in this export.")

rows = 0
for name, val, note in CRIT_TABLE:
    sid = spell_id(name)
    if sid is None:
        continue
    cur.execute(
        "INSERT INTO doc_confirmed_mechanics VALUES (?,?,?,?,?,?,?,?)",
        (sid, 'crit_table', val, None, 'pooled_log_measurement',
         'primer §1 crit-table resolution (King Gordok parse + follow-ups)',
         'confirmed', note))
    rows += 1

# Righteous Vengeance is also the confirmed pooling no-crit periodic
rv_id = spell_id('Righteous Vengeance')
if rv_id is not None:
    cur.execute(
        "INSERT INTO doc_confirmed_mechanics VALUES (?,?,?,?,?,?,?,?)",
        (rv_id, 'ticks_can_crit', None, 0.0, 'pooled_log_measurement',
         'primer §1: 0% crit over 303 hits / 9 characters / 4 Paths',
         'confirmed', 'Periodic, cannot crit — effectively settled (v17).'))
    rows += 1

# Molten Earth: per explicit user decision (2026-08-03) - crit_table deliberately
# NOT seeded (measured 40.7% crit but primer §1 says crit-capability has no
# structural predictor and must not be forced into the melee/spell binary).
# A notes-only row records the decision so it reads differently from truly-unknown.
molten_id = spell_id('Molten Earth')
if molten_id is not None:
    cur.execute(
        "INSERT INTO doc_confirmed_mechanics VALUES (?,?,?,?,?,?,?,?)",
        (molten_id, 'ticks_can_crit', None, 1.0, 'pooled_log_measurement',
         'primer §1 v6/v7: 40.7% crit over 575 hits (plus 46.6%/64.8% samples)',
         'confirmed',
         'crit_table left unseeded ON PURPOSE — measured critting aura-tick DoT, '
         'but the primer forbids forcing it into the melee/spell binary. '
         'Decision confirmed with the project owner 2026-08-03.'))
    rows += 1
    print(f'  Molten Earth (id {molten_id}): ticks_can_crit=1 seeded; crit_table left unseeded per confirmed decision.')

# --- proc_icd_seconds ---
felinf_id = spell_id('Fel Infused Weapon')
if felinf_id is not None:
    cur.execute(
        "INSERT INTO doc_confirmed_mechanics VALUES (?,?,?,?,?,?,?,?)",
        (felinf_id, 'proc_icd_seconds', None, 0.0, 'live_tooltip_or_own_parse',
         'primer §1 (v6): tooltip states per-hit trigger, no ICD clause',
         'confirmed', 'Confirmed no-ICD, fires on every auto attack and melee ability.'))
    rows += 1

conn.commit()
print(f'doc_confirmed_mechanics rows seeded: {rows}')
conn.close()
