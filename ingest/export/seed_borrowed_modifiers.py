#!/usr/bin/env python3
import json, re, sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from config import DB_PATH, SPELL_EXPORT  # noqa: E402
from core.spells.wotlk_class_dictionary import (  # noqa: E402
    BASE_ABILITY_CLASS, NOT_A_CLASS_REFERENCE,
)

# Known multi-word idioms that must NOT be split on " and "
IDIOMS = ['Slice and Dice']

PAT = re.compile(r'uses ([A-Za-z\'\- ]+?) modifiers', re.I)

def split_targets(raw):
    for idiom in IDIOMS:
        if raw.strip().lower() == idiom.lower():
            return [idiom]
    return [p.strip() for p in re.split(r'\s+and\s+', raw.strip())]

def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # add columns if not present
    cur.execute("PRAGMA table_info(spells)")
    cols = {r[1] for r in cur.fetchall()}
    if 'borrows_from' not in cols:
        cur.execute("ALTER TABLE spells ADD COLUMN borrows_from TEXT")
    if 'path_fit_heuristic' not in cols:
        cur.execute("ALTER TABLE spells ADD COLUMN path_fit_heuristic TEXT")

    with open(SPELL_EXPORT) as f:
        data = json.load(f)
    spells = data['spells']

    resolved = 0
    unresolved = 0
    for s in spells:
        t = s.get('tooltip') or ''
        m = PAT.search(t)
        if not m:
            continue
        raw = m.group(1).strip()
        if raw in NOT_A_CLASS_REFERENCE:
            continue
        targets = split_targets(raw)
        cur.execute("UPDATE spells SET borrows_from=? WHERE id=?", (', '.join(targets), s['id']))

        # only set class_origin if not already set (doc-confirmed rows win)
        cur.execute("SELECT class_origin FROM spells WHERE id=?", (s['id'],))
        existing = cur.fetchone()[0]
        if existing:
            continue
        classes = {BASE_ABILITY_CLASS[tg] for tg in targets if tg in BASE_ABILITY_CLASS}
        if len(classes) == 1:
            cls = classes.pop()
            note = f"Borrows '{raw}' modifiers -> base ability is {cls} in WotLK. Class-tag rule (primer §4): CONFIRM with a dummy proc test before relying on this for engine-gating decisions."
            cur.execute("UPDATE spells SET class_origin=?, class_confidence=?, notes=COALESCE(notes,'')||? WHERE id=?",
                        (cls, 'inferred_borrowed_modifiers', note, s['id']))
            resolved += 1
        else:
            unresolved += 1

    # Path-fit heuristic from primer §3: "purely physical -> Strength/Agility;
    # anything with (SP+AP) coefficients or hybrid schools -> Duality;
    # caster-only -> Intelligence."
    cur.execute('''
        SELECT spell_id, GROUP_CONCAT(DISTINCT term_type) FROM spell_scaling GROUP BY spell_id
    ''')
    for spell_id, terms in cur.fetchall():
        term_set = set(terms.split(','))
        cur.execute("SELECT schools, mechanics FROM spells WHERE id=?", (spell_id,))
        schools, mechanics = cur.fetchone()
        is_hybrid_school = any(h in (schools or '') for h in
                                ['Holystrike','Holyfire','Shadowflame','Firestrike',
                                 'Froststrike','Shadowstrike','Spellstrike','Stormstrike'])
        has_sp = 'SP' in term_set
        has_ap = 'AP' in term_set or 'RAP' in term_set
        is_heal = 'heal' in (mechanics or '')

        if is_hybrid_school or (has_sp and has_ap):
            fit = 'Duality'
        elif has_sp and is_heal:
            fit = 'Healing'
        elif has_sp:
            fit = 'Intelligence'
        elif has_ap and not has_sp:
            fit = 'Strength/Agility'
        else:
            fit = None
        if fit:
            cur.execute("UPDATE spells SET path_fit_heuristic=? WHERE id=?", (fit, spell_id))

    conn.commit()
    print('resolved class_origin via borrowed-modifiers dictionary:', resolved)
    print('borrows_from set but class unresolved (base ability not in dictionary):', unresolved)

    cur.execute("SELECT COUNT(*) FROM spells WHERE borrows_from IS NOT NULL")
    print('total spells with a borrows_from clause recorded:', cur.fetchone()[0])
    cur.execute("SELECT COUNT(*) FROM spells WHERE class_origin IS NOT NULL")
    print('total spells with ANY class_origin now:', cur.fetchone()[0])
    cur.execute("SELECT COUNT(*) FROM spells WHERE path_fit_heuristic IS NOT NULL")
    print('total spells with path_fit_heuristic:', cur.fetchone()[0])
    conn.close()

if __name__ == '__main__':
    main()
