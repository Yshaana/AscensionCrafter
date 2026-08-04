#!/usr/bin/env python3
"""Seeds shared_synergies from external builds/engines observed outside our
own characters (dungeon groups, other players' parses/tooltips) - reference
material only, same append-only spirit as seed_confirmed.py, but for engines
we don't own rather than facts about our own build. Nothing here is guessed;
every row traces to a source (parse, tooltip, or screenshot) and a linked
build file with the full detail."""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from config import DB_PATH  # noqa: E402  - repo-root path resolution (see config.py)
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
    (
        'Demon Package core (Demonic Tactics + Demonic Pact + Master Demonologist)',
        'ZG roster crawl, 37 characters across 3 guilds (404/Mouse/Nelf), 2026-08-03',
        'Three near-universal talents among any character running a demon pet: Demonic Tactics (+10% melee+spell crit, self+pet, includes Enslave Demon), Demonic Pact (+10% flat spell damage, unconditional; separate raid-buff clause on pet crit excludes Enslaved demons), Master Demonologist (+5% all damage/-5% damage taken for Felguard or Enslaved Demon specifically).',
        'flat: Demonic Tactics +10%crit, Demonic Pact +10% spell dmg, Master Demonologist +5%dmg/-5%dmg-taken — all unconditional, no pet-species requirement',
        'cross-class,generic-wording,portable,pet,crit,flat-damage',
        'external_sighting',
        'builds/shared/synergy_portable-multiplier-packages.md',
        '2026-08-03',
    ),
    (
        'Demonic Knowledge (enslaved-demon stat siphon)',
        'ZG roster crawl, 2 of 37 characters (Malo, David), 2026-08-03',
        'Optional specialist layer on top of the Demon Package core. Requires Enslave Demon to tame a high-Stamina/Intellect demon NPC; converts a % of the demon\'s own Stam+Int into your spell damage. Rare (2/37) vs. the core package.',
        'rank 3 (max): 12% of active demon\'s (Stamina+Intellect) as spell damage. Best untested candidate: level 60 Elite "Dread Lord" (Nathrezim, Ascension DB npc=475221), 15,291 HP vs 3,495 HP for non-elite same-level/family unique, caster-flavored kit implies real Int budget.',
        'cross-class,pet,stat-siphon,unconfirmed,requires-live-test',
        'external_sighting',
        'builds/shared/synergy_portable-multiplier-packages.md',
        '2026-08-03',
    ),
    (
        'DK Disease Package (Tundra Stalker + Rage of Rivendare + Icy Touch/Plague Strike)',
        'ZG roster crawl, 6/25 (Tundra Stalker), 4/25 (Rage of Rivendare), 2026-08-03',
        'Self-apply Frost Fever (Icy Touch) and Blood Plague (Plague Strike), two cheap GCDs with long duration/near-permanent uptime. Both disease-damage talents apply to "your spells and abilities" generically, not DK-gated.',
        'flat: Tundra Stalker +15% all dmg to Frost-Fever\'d target +5 expertise (5/5); Rage of Rivendare +10% all dmg to Blood-Plague\'d target +5 expertise (5/5). Stacked = +25% all dmg + 10 expertise on target.',
        'cross-class,generic-wording,portable,dot,flat-damage,cheap-setup',
        'external_sighting',
        'builds/shared/synergy_portable-multiplier-packages.md',
        '2026-08-03',
    ),
    (
        'Blessing of Kings (+10% all stats)',
        'ZG roster crawl, 9/25 characters, 2026-08-03',
        'Self-castable Paladin blessing, single rank ability, no talent cost, 30-min duration, no proc conditions. Cheapest item found across all packages this session; adoption (36%) lower than expected given the cost.',
        'flat +10% to all 5 stats (Str/Agi/Stam/Int/Spirit combined). Does not stack with other similar effects.',
        'cheap,flat-stats,no-talent-cost,paladin-native,check-own-bar',
        'external_sighting',
        'builds/shared/synergy_portable-multiplier-packages.md',
        '2026-08-03',
    ),
    (
        "Titan's Grip Staff/Polearm + off-hand clause",
        'Tooltip read (spell-export.json id 46917), user-spotted, 2026-08-03',
        'Second, separate clause on Titan\'s Grip beyond the dual-2H-melee clause our build uses: allows a weapon or shield in the off-hand while a Staff or Polearm is equipped, freeing a normally-locked gear slot for any caster archetype.',
        'no numeric scaling — a free gear slot, not a damage formula. Unresolved: exact % of the tooltip\'s physical-damage-reduction penalty ($S3, placeholder), and whether it is scoped only to the dual-2H-melee configuration.',
        'gear-slot,caster,cross-class,unconfirmed-penalty-scope',
        'external_sighting',
        'builds/shared/synergy_titans-grip-staff-offhand.md',
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
