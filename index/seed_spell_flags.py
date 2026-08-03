#!/usr/bin/env python3
"""Adds and seeds four new nullable spells columns (crit_table, rolls_hit_check,
hit_table, proc_icd_seconds) - closes the gap between "known per-ability from a
specific build session" and "queryable across the whole catalog". Nothing here
is guessed: only values already confirmed in the primer/handoff are seeded,
everything else stays NULL ("unconfirmed", not "no")."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / 'ascension_index.db'  # this file lives in index/
conn = sqlite3.connect(str(DB_PATH))
cur = conn.cursor()

cur.execute("PRAGMA table_info(spells)")
cols = {r[1] for r in cur.fetchall()}
for col, coltype in [('crit_table', 'TEXT'), ('rolls_hit_check', 'BOOLEAN'),
                      ('hit_table', 'TEXT'), ('proc_icd_seconds', 'REAL')]:
    if col not in cols:
        cur.execute(f'ALTER TABLE spells ADD COLUMN {col} {coltype}')

def spell_id(name):
    cur.execute('SELECT id, name FROM spells WHERE name=?', (name,))
    rows = cur.fetchall()
    if len(rows) != 1:
        print(f'  ! WARNING: {name!r} not found or ambiguous in this export, skipping: {rows}')
        return None
    return rows[0][0]

# --- crit_table ---
CRIT_TABLE = [
    ('Lightbound Cleave', 'spell', "Holystrike crit-table resolution, primer §1. Measured 38.1% crit against Consecrated Holy Weapon (Holy, 39.0%) - tracks the Holy source, not the physical melee source (16.2%-20.0%)."),
    ('Dawn Strike', 'spell', "Holystrike crit-table resolution, primer §1. Measured 33.3% crit, same Holy-table pattern as Lightbound Cleave."),
    ('Sword Specialization', 'melee', "Physical, measured 20.0% crit alongside melee autos (16.2%) in the same Holystrike-resolution sheet, primer §1."),
    ('Righteous Vengeance', 'none', "Confirmed-no-crit periodic effect - 0% across 4 parses, primer §1 / seed_confirmed.py 'periodic_no_crit'."),
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

crit_set = 0
for name, val, note in CRIT_TABLE:
    sid = spell_id(name)
    if sid is None:
        continue
    cur.execute('UPDATE spells SET crit_table=?, notes=COALESCE(notes,"")||? WHERE id=?',
                (val, f' | CRIT_TABLE: {note}', sid))
    crit_set += 1

# Molten Earth: per explicit user decision (2026-08-03) - leave crit_table NULL
# (measured 40.7% crit but primer §1 explicitly says crit-capability has no structural
# predictor and should not be forced into the melee/spell binary) but flag it in notes
# so it's distinguishable from a truly-unknown spell on inspection.
molten_id = spell_id('Molten Earth')
if molten_id is not None:
    cur.execute('''UPDATE spells SET notes=COALESCE(notes,"")||? WHERE id=?''',
                (' | CRIT_TABLE: left NULL on purpose (not "unconfirmed" in the ordinary sense) - '
                 'measured 40.7% crit over 575 hits (primer §1, v6/v7) but crit-capability has no '
                 'structural predictor and the primer explicitly says not to force this into the '
                 'melee/spell binary. Decision confirmed with the project owner 2026-08-03.',
                 molten_id))
    print(f'  Molten Earth (id {molten_id}): crit_table left NULL with notes flag, per confirmed decision.')

# --- proc_icd_seconds ---
felinf_id = spell_id('Fel Infused Weapon')
if felinf_id is not None:
    cur.execute('UPDATE spells SET proc_icd_seconds=0, notes=COALESCE(notes,"")||? WHERE id=?',
                (' | PROC_ICD: confirmed no-ICD, fires on every auto attack and melee ability. Primer §1 (v6).', felinf_id))

conn.commit()
print(f'crit_table set on {crit_set} spells (+ Molten Earth notes-only flag)')
cur.execute('SELECT COUNT(*) FROM spells WHERE crit_table IS NOT NULL')
print('spells.crit_table non-NULL:', cur.fetchone()[0])
cur.execute('SELECT COUNT(*) FROM spells WHERE proc_icd_seconds IS NOT NULL')
print('spells.proc_icd_seconds non-NULL:', cur.fetchone()[0])
conn.close()
