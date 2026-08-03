#!/usr/bin/env python3
"""Seeds shared_synergies from external builds/engines observed outside our
own characters (dungeon groups, other players' parses/tooltips) - reference
material only, same append-only spirit as seed_confirmed.py, but for engines
we don't own rather than facts about our own build. Nothing here is guessed;
every row traces to a source (parse, tooltip, or screenshot) and a linked
build file with the full detail."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / 'ascension_index.db'  # this file lives in index/
conn = sqlite3.connect(str(DB_PATH))
cur = conn.cursor()

cur.execute('''
CREATE TABLE IF NOT EXISTS shared_synergies (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE,
    source TEXT,
    engine_desc TEXT,
    scaling_note TEXT,
    tags TEXT,
    confidence TEXT,
    linked_file TEXT,
    date_added TEXT
)
''')

# (name, source, engine_desc, scaling_note, tags, confidence, linked_file, date_added)
SYNERGIES = [
    (
        'Fel Infused Weapon (no-ICD scaling)',
        'group parse, dagger/hybrid char',
        'fires on every auto attack and melee ability, no ICD',
        'flat + AP*0.05 + SP*0.05 Shadowflame per hit',
        'no-ICD,dual-wield,attack-speed-scaling',
        'internal_test',
        'builds/shared/synergy_fel-infused-dagger.md',
        '2026-08-02',
    ),
    (
        'Winds of Winter (quadratic CP finisher)',
        'dungeon group, live parse + tooltip, 2026-08-03',
        "Rogue combo-point finisher slot, borrows Cone of Cold (Mage). Damage scales n^2 with combo points spent, not linear.",
        'flat*n + (SP_frost*0.0096)*n^2 + (AP*0.00624)*n^2, n=combo points (1-5)',
        "quadratic-scaling,combo-points,dual-AP-SP,frost,titan's-grip",
        'external_sighting',
        'builds/shared/synergy_winds-of-winter.md',
        '2026-08-03',
    ),
    (
        'Titanic Mutilate (CP generator, borrowed tag)',
        'dungeon group, live parse + tooltip, 2026-08-03',
        'borrows Mutilate (Rogue), 2 CP per cast, +20% dmg vs bleeding, feeds Winds of Winter',
        'see linked file — weapon-damage based, both hands',
        'combo-points,class-tag-borrowed,rogue',
        'external_sighting',
        'builds/shared/synergy_winds-of-winter.md',
        '2026-08-03',
    ),
    (
        'Killing Machine -> Frost crit consumption chain',
        'dungeon group, live parse, 2026-08-03',
        'DK talent: melee hit chance to guarantee next Frost spell/ability crits; Titanic Mutilate (melee) feeds it, Winds of Winter (Frost) consumes it',
        'unresolved — 9 KM procs measured against 11-12 crits observed, gap unexplained',
        'crit-chain,cross-ability-proc,frost,unresolved',
        'external_sighting',
        'builds/shared/synergy_winds-of-winter.md',
        '2026-08-03',
    ),
]

cur.executemany('''INSERT OR IGNORE INTO shared_synergies
    (name, source, engine_desc, scaling_note, tags, confidence, linked_file, date_added)
    VALUES (?,?,?,?,?,?,?,?)''', SYNERGIES)

conn.commit()
cur.execute('SELECT COUNT(*) FROM shared_synergies')
print('shared_synergies rows:', cur.fetchone()[0])
conn.close()
