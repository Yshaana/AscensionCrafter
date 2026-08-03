#!/usr/bin/env python3
"""Adds spell_scaling.cp_scaling_type and seeds it. Quadratic combo-point
finishers (Holy Finish, Winds of Winter - primer §1 v12) put the CP term
inside a squared power rather than a linear multiplier; this column sorts
any future finisher automatically instead of requiring a manual tooltip read.

Detection: Ascension's per-combo-point tooltips spell out each point tier's
literal formula (e.g. Holy Finish: "...+($AP+$SP)*2*2*0.02..." for the 2-point
tier). A tier's SP/AP coefficient is quadratic in the point count N iff the
formula contains the point count multiplied by itself (`*N*N`) next to the
SP/AP term; if the coefficient instead is scaled by a single `*N`, it's
linear. Classification only applies to spells with an actual SP/AP/RAP
coefficient AND a "per combo point" tiered tooltip - spells that merely award
or spend combo points without a scaling formula (Mutilate, Fulmination's
target-count-only scaling, Kingsbane) get NULL (not CP-scaling in this sense),
same "don't guess" discipline as the rest of the pipeline."""
import re
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / 'ascension_index.db'  # this file lives in index/
conn = sqlite3.connect(str(DB_PATH))
cur = conn.cursor()

cur.execute("PRAGMA table_info(spell_scaling)")
cols = {r[1] for r in cur.fetchall()}
if 'cp_scaling_type' not in cols:
    cur.execute('ALTER TABLE spell_scaling ADD COLUMN cp_scaling_type TEXT')

QUAD_PAT = re.compile(r'\*(\d)\*\1\b')  # e.g. "*2*2" - point count multiplied by itself
TIER_PAT = re.compile(r'\d\s*points?\s*:', re.I)  # "1 point  :" / "2 points:" tier markers

def spell_id_unique(name):
    cur.execute('SELECT id FROM spells WHERE name=?', (name,))
    rows = cur.fetchall()
    return rows[0][0] if len(rows) == 1 else None

set_count = 0

# --- Known case: Holy Finish (primer §1/§11 handoff, hand-confirmed) ---
# build_index.py's SP/AP extraction regex only matches "$SP*N" / "$AP*N" as
# standalone terms - it does NOT match Holy Finish's compound "($AP+$SP)*n*n*0.02"
# form, so Holy Finish has NO spell_scaling rows at all (verified: pre-existing
# gap in the automated extractor, out of scope to fix here). Hand-inserting the
# two rows here, same discipline as seed_confirmed.py hand-seeding facts the
# automated pass misses.
holy_finish_id = spell_id_unique('Holy Finish')
if holy_finish_id is not None:
    cur.execute('SELECT COUNT(*) FROM spell_scaling WHERE spell_id=?', (holy_finish_id,))
    if cur.fetchone()[0] == 0:
        cur.executemany('INSERT INTO spell_scaling (spell_id, term_type, coefficient, cp_scaling_type) VALUES (?,?,?,?)',
                         [(holy_finish_id, 'SP', 0.02, 'quadratic'),
                          (holy_finish_id, 'AP', 0.02, 'quadratic')])
        print(f"Holy Finish (id {holy_finish_id}): NOT found in spell_scaling (extractor gap, compound (AP+SP) form) - "
              "hand-inserted 2 rows (SP 0.02, AP 0.02, cp_scaling_type='quadratic'). "
              "Formula (AP+SP) x CP^2 x 0.02, primer §1/handoff §11.")
        set_count += 2
    else:
        cur.execute("UPDATE spell_scaling SET cp_scaling_type='quadratic' WHERE spell_id=? AND term_type IN ('SP','AP')",
                    (holy_finish_id,))
        set_count += cur.rowcount
        print(f"Holy Finish (id {holy_finish_id}): cp_scaling_type='quadratic' set on {cur.rowcount} existing spell_scaling row(s).")

# --- Bulk scan: any other finisher with a per-combo-point SP/AP/RAP formula ---
cur.execute('''
    SELECT DISTINCT s.id, s.name, s.tooltip
    FROM spells s JOIN spell_scaling ss ON ss.spell_id = s.id
    WHERE ss.term_type IN ('SP','AP','RAP')
      AND s.tooltip LIKE '%combo point%'
      AND s.id != COALESCE(?, -1)
''', (holy_finish_id,))
candidates = cur.fetchall()

quad_found = []
linear_found = []
for sid, name, tt in candidates:
    tt = tt or ''
    if not TIER_PAT.search(tt):
        continue  # awards/spends combo points but has no per-point scaling tiers - not applicable
    if QUAD_PAT.search(tt):
        cur.execute("UPDATE spell_scaling SET cp_scaling_type='quadratic' WHERE spell_id=? AND term_type IN ('SP','AP','RAP')", (sid,))
        set_count += cur.rowcount
        quad_found.append(name)
    else:
        cur.execute("UPDATE spell_scaling SET cp_scaling_type='linear' WHERE spell_id=? AND term_type IN ('SP','AP','RAP')", (sid,))
        set_count += cur.rowcount
        linear_found.append(name)

conn.commit()
print(f"Bulk scan - quadratic CP finishers found: {sorted(quad_found)}")
print(f"Bulk scan - linear CP finishers found: {len(linear_found)} spells")
print(f"spell_scaling.cp_scaling_type total rows set: {set_count}")
cur.execute("SELECT COUNT(*) FROM spell_scaling WHERE cp_scaling_type IS NOT NULL")
print('spell_scaling.cp_scaling_type non-NULL:', cur.fetchone()[0])
conn.close()
