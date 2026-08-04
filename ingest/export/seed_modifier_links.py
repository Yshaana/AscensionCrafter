#!/usr/bin/env python3
"""Seeds modifier_links - unifies spells.borrows_from ("uses X modifiers" class-tag
clause, link_type='class_tag') with the catalog's separate sharesModifiersWith field
("talents boosting X also boost this card", link_type='talent_amp') into one
bidirectional table, so "what buffs ability X" and "what does X's damage feed into"
are both one query. borrows_from itself is NOT dropped - additive only.

IMPORTANT: sharesModifiersWith does NOT exist anywhere in the current
spell-export.json - every spell entry has exactly {id, type, name, rank, tooltip}
(verified by inspecting the union of keys across all 3061 entries). The primer/
task brief describes it as a catalog field to parse; it is not present in this
export. Per the primer's own "check the export before writing up a diff/fact"
discipline (§5, the Exorcism false-positive lesson), this script does NOT
fabricate talent_amp rows - it only populates link_type='class_tag' from the
already-verified borrows_from data. Re-check this if a future spell-export.json
pull ever adds the field."""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from config import DB_PATH  # noqa: E402  - repo-root path resolution (see config.py)
conn = sqlite3.connect(str(DB_PATH))
cur = conn.cursor()

cur.execute('''
CREATE TABLE IF NOT EXISTS modifier_links (
    spell_id INTEGER,
    target_name TEXT,
    target_spell_id INTEGER,
    link_type TEXT,
    link_confidence TEXT,
    source TEXT,
    FOREIGN KEY (spell_id) REFERENCES spells(id)
)
''')
cur.execute('DELETE FROM modifier_links')  # rebuilt fresh each run from spells.borrows_from, same idempotent pattern as the other seed scripts

# Build a name -> id lookup for target resolution. Skip ambiguous (duplicate-name-trap) names.
cur.execute('SELECT id, name FROM spells')
name_to_ids = {}
for sid, name in cur.fetchall():
    name_to_ids.setdefault(name, []).append(sid)

def resolve_target_id(target_name):
    ids = name_to_ids.get(target_name)
    if ids and len(ids) == 1:
        return ids[0]
    return None  # not found, or ambiguous (duplicate-name trap) - leave NULL rather than guess

cur.execute('SELECT id, borrows_from, class_confidence FROM spells WHERE borrows_from IS NOT NULL')
rows = cur.fetchall()

inserted = 0
for spell_id, borrows_from, class_confidence in rows:
    for target_name in [t.strip() for t in borrows_from.split(',')]:
        target_spell_id = resolve_target_id(target_name)
        cur.execute('''INSERT INTO modifier_links
            (spell_id, target_name, target_spell_id, link_type, link_confidence, source)
            VALUES (?,?,?,?,?,?)''',
            (spell_id, target_name, target_spell_id, 'class_tag', class_confidence, 'export_tooltip'))
        inserted += 1

conn.commit()
print(f'modifier_links rows inserted (class_tag, from borrows_from): {inserted}')
print("modifier_links rows inserted (talent_amp, from sharesModifiersWith): 0 "
      "- field not present in spell-export.json, see script docstring")
conn.close()
