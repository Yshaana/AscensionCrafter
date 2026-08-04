#!/usr/bin/env python3
"""Seeds talent_amplifiers - operationalizes the primer §5 rule "named lists
outrank generic wording until proc-tested" so a new amplifier can be checked
by query instead of a manual tooltip re-read every time.

match_type classification:
  'verbatim'       - the amplified target list names a specific ability
                      (matches a spells.name exactly) or a hybrid school
                      (Holystrike/Shadowflame/etc, primer's HYBRID_SCHOOLS) -
                      ground truth, no test needed.
  'school_generic' - the target list only names a base/pure school
                      (Fire/Frost/Shadow/Arcane/Nature/Holy/Physical) - a
                      prediction under the hybrid double-dip rule, unconfirmed
                      for hybrid-school abilities until proc-tested.
Ambiguous extractions (neither cleanly verbatim nor cleanly generic) are
flagged 'needs manual review' rather than guessed, same discipline as
seed_exclusivity.py's candidate scan."""
import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from config import DB_PATH  # noqa: E402  - repo-root path resolution (see config.py)
conn = sqlite3.connect(str(DB_PATH))
cur = conn.cursor()

cur.execute('''
CREATE TABLE IF NOT EXISTS talent_amplifiers (
    talent_spell_id INTEGER,
    target_effect TEXT,
    match_type TEXT,
    verified BOOLEAN DEFAULT 0,
    notes TEXT,
    FOREIGN KEY (talent_spell_id) REFERENCES spells(id)
)
''')
cur.execute('DELETE FROM talent_amplifiers')  # rebuilt fresh each run, same idempotent pattern as the other seed scripts

def spell_id(name):
    cur.execute('SELECT id FROM spells WHERE name=?', (name,))
    rows = cur.fetchall()
    if len(rows) != 1:
        print(f'  ! WARNING: {name} not found or ambiguous: {rows}')
        return None
    return rows[0][0]

# --- 1. Known cases from primer §5 (hand-seeded, doc-confirmed) ---
KNOWN = [
    ('Shadow and Flame', 'Shadowflame', 'verbatim', 1,
     'Tooltip names Shadowflame explicitly alongside Shadow Bolt, Shadowburn, Chaos Bolt, Shadowfury, Soul Fire, Hand of Gul\'dan, Incinerate. Primer §5 (v7).'),
    ('Bane', 'Shadowflame', 'verbatim', 1,
     'Tooltip names Shadowflame explicitly alongside Shadow Bolt, Chaos Bolt, Immolate, Hand of Gul\'dan, Soul Fire. Primer §5 (v7).'),
    ('Emberstorm', 'Fire and Shadow spells', 'school_generic', 0,
     'Tooltip only says "Fire and Shadow spells" - does not name Shadowflame or any specific hybrid ability. Explicitly flagged in primer as unconfirmed for hybrid double-dip (§5, v7).'),
]
inserted = 0
for talent_name, target_effect, match_type, verified, notes in KNOWN:
    sid = spell_id(talent_name)
    if sid is None:
        continue
    cur.execute('''INSERT INTO talent_amplifiers
        (talent_spell_id, target_effect, match_type, verified, notes)
        VALUES (?,?,?,?,?)''', (sid, target_effect, match_type, verified, notes))
    inserted += 1
print(f'talent_amplifiers rows inserted (known/hand-seeded): {inserted}')

# --- 2. Bulk scan: damage-school / named-effect amplifier language ---
PURE_SCHOOLS = ['Frost', 'Fire', 'Shadow', 'Arcane', 'Nature', 'Holy', 'Physical']
HYBRID_SCHOOLS = ['Holystrike', 'Holyfire', 'Shadowflame', 'Firestrike', 'Froststrike',
                  'Shadowstrike', 'Spellstrike', 'Stormstrike']

cur.execute('SELECT name FROM spells')
ALL_NAMES = {row[0] for row in cur.fetchall()}

AMP_PAT = re.compile(
    r'increases[^.$]{0,150}?(?:of (?:your )?|by your |your )'
    r'([A-Za-z0-9\'\-,\s]+?)\s*(?:spells and abilities|spells|abilities)?\s*by \$s\d+%',
    re.I)

def split_targets(raw):
    parts = re.split(r',|\band\b', raw)
    return [p.strip().rstrip('.') for p in parts if p.strip()]

already_seeded_talents = {row[0] for row in cur.execute('SELECT DISTINCT talent_spell_id FROM talent_amplifiers')}

cur.execute("SELECT id, name, tooltip FROM spells WHERE type='talent'")
talents = cur.fetchall()

bulk_verbatim = 0
bulk_generic = 0
bulk_review = 0
for sid, name, tt in talents:
    if sid in already_seeded_talents:
        continue
    tt = tt or ''
    m = AMP_PAT.search(tt)
    if not m:
        continue
    raw_targets = split_targets(m.group(1))
    if not raw_targets:
        continue

    named_hits = [t for t in raw_targets if t in ALL_NAMES or t in HYBRID_SCHOOLS]
    school_hits = [t for t in raw_targets if t in PURE_SCHOOLS]
    other = [t for t in raw_targets if t not in ALL_NAMES and t not in HYBRID_SCHOOLS and t not in PURE_SCHOOLS]

    target_effect = ', '.join(raw_targets)

    if named_hits and not other:
        match_type, verified, notes = 'verbatim', 0, 'Auto-classified: target list resolves to known ability name(s)/hybrid school(s) in the catalog. Not yet proc-tested (verified=0) unlike the hand-seeded primer §5 cases.'
        bulk_verbatim += 1
    elif school_hits and not other and not named_hits:
        match_type, verified, notes = 'school_generic', 0, 'Auto-classified: target list only names base school(s), no specific ability or hybrid-school string. Unconfirmed for hybrid double-dip until proc-tested (primer §5).'
        bulk_generic += 1
    else:
        match_type, verified, notes = 'school_generic', 0, 'needs manual review - target list extraction did not cleanly resolve to a known ability/hybrid school or a pure base school.'
        bulk_review += 1

    cur.execute('''INSERT INTO talent_amplifiers
        (talent_spell_id, target_effect, match_type, verified, notes)
        VALUES (?,?,?,?,?)''', (sid, target_effect, match_type, verified, notes))

conn.commit()
print(f'talent_amplifiers rows inserted (bulk scan, verbatim): {bulk_verbatim}')
print(f'talent_amplifiers rows inserted (bulk scan, school_generic): {bulk_generic}')
print(f'talent_amplifiers rows inserted (bulk scan, needs manual review): {bulk_review}')
cur.execute('SELECT COUNT(*) FROM talent_amplifiers')
print('talent_amplifiers total rows:', cur.fetchone()[0])
conn.close()
