#!/usr/bin/env python3
"""Seeds exclusivity_buckets - "does not stack / only the highest applies" rules
that currently live only in prose (primer §2, confirmed_facts) - so chase-list /
build-planning queries can auto-detect conflicts. Append-only, mirrors
seed_confirmed.py's pattern: known buckets are hand-seeded from doc-confirmed
sources; a tooltip scan surfaces further candidates but does NOT auto-insert them
(generic "does not stack with other similar effects" boilerplate appears on ~150+
unrelated buffs - see primer's export-tooltip-incomplete lesson, same discipline
applies to over-eager auto-detection)."""
import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from config import DB_PATH  # noqa: E402  - repo-root path resolution (see config.py)
conn = sqlite3.connect(str(DB_PATH))
cur = conn.cursor()

cur.execute('''
CREATE TABLE IF NOT EXISTS exclusivity_buckets (
    bucket_id INTEGER,
    spell_id INTEGER,
    bucket_name TEXT,
    bucket_desc TEXT,
    source TEXT,
    notes TEXT,
    FOREIGN KEY (spell_id) REFERENCES spells(id)
)
''')
cur.execute('DELETE FROM exclusivity_buckets')  # append-only across sessions, but this script's own rows are idempotent per rebuild

def spell_id(name):
    cur.execute('SELECT id FROM spells WHERE name=?', (name,))
    rows = cur.fetchall()
    if not rows:
        print(f'  ! WARNING: spell not found: {name}')
        return None
    if len(rows) > 1:
        print(f'  ! WARNING: ambiguous name (duplicate-name trap), skipping: {name} -> {rows}')
        return None
    return rows[0][0]

# (bucket_id, bucket_name, bucket_desc, source, [(spell_name, notes)])
BUCKETS = [
    (1, 'all_damage_pct', 'All-damage% "only the highest applies" bucket', 'patch_note',
     [('Enhanced Weapon Mastery', 'Codified 2026-08-03 Darkmoon patch note - was tooltip-only before (primer §2/v12 changelog).'),
      ('Unending Fury', None),
      ('Answered Prayers', None),
      ('Blessed Weapons', None)]),
    (2, 'weapon_imbue_slot', 'Weapon-imbue ability cards share one weapon-enchant slot', 'doc_confirmed',
     [('Windfury Weapon', 'slot conflict, not a tooltip-stated exclusion - will not surface via text scan'),
      ('Flametongue Weapon', 'slot conflict, not a tooltip-stated exclusion - will not surface via text scan'),
      ('Fel Infused Weapon', 'slot conflict, not a tooltip-stated exclusion - will not surface via text scan'),
      ('Rockbiter Weapon', 'slot conflict, not a tooltip-stated exclusion - will not surface via text scan'),
      ('Frostbrand Weapon', 'slot conflict, not a tooltip-stated exclusion - will not surface via text scan')]),
    (3, 'spell_crit_dmg_bonus', '"Does not stack with other similar effects" spell-crit-damage bucket', 'tooltip',
     [('Holy Focus', 'Tooltip: "spell crits deal 200%, does not stack with other similar effects" (primer §2).')]),
    (4, 'dw_spec_mastery', 'Dual Wield Specialization <-> Dual Wield Mastery, fully redundant', 'doc_confirmed',
     [('Dual Wield Specialization', 'id 13852 (Rogue r5) - tooltip carries the explicit "@ext:Does not stack with Dual Wield Mastery:ext@" clause. NOT id 30819 (Shaman r3 hit/elemental variant) - that tooltip has no such clause, duplicate-name trap (primer §2).'),
      ('Dual Wield Mastery', None)]),
]

inserted = 0
for bucket_id, bucket_name, bucket_desc, source, members in BUCKETS:
    for name, notes in members:
        # Dual Wield Specialization needs the specific id, handled by explicit id below
        if bucket_id == 4 and name == 'Dual Wield Specialization':
            sid = 13852
        else:
            sid = spell_id(name)
        if sid is None:
            continue
        cur.execute('INSERT INTO exclusivity_buckets (bucket_id, spell_id, bucket_name, bucket_desc, source, notes) VALUES (?,?,?,?,?,?)',
                     (bucket_id, sid, bucket_name, bucket_desc, source, notes))
        inserted += 1

conn.commit()
print(f'exclusivity_buckets rows inserted: {inserted}')

# --- Candidate scan: print only, do not auto-insert (avoid false positives from generic wording) ---
already_flagged_ids = {row[0] for row in cur.execute('SELECT DISTINCT spell_id FROM exclusivity_buckets')}
PATS = [re.compile(p, re.I) for p in [r'does not stack', r'only the highest', r'only the strongest']]
cur.execute('SELECT id, name, tooltip FROM spells')
candidates = []
for sid, name, tt in cur.fetchall():
    tt = tt or ''
    if sid in already_flagged_ids:
        continue
    for p in PATS:
        if p.search(tt):
            candidates.append((sid, name, p.pattern))
            break

print(f'\nCandidate exclusivity hits NOT already in a known bucket: {len(candidates)}')
print('(manual review only - most are generic "does not stack with other similar effects" buff boilerplate, not build-relevant buckets)')
for sid, name, pat in candidates[:15]:
    print(f'  {sid}\t{name}\t[{pat}]')
if len(candidates) > 15:
    print(f'  ... and {len(candidates) - 15} more (see full tooltip scan if needed)')

conn.close()
