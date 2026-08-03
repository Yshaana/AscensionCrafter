#!/usr/bin/env python3
"""
Ascension Spell/Card Index Builder
Parses spell-export.json (catalog) + Cards.txt (owned cards) into a single
queryable SQLite database, with automated text-derived tags:
  - damage school(s) mentioned in tooltip
  - explicit SP/AP/RAP scaling coefficients (when present in raw tooltip)
  - "hidden formula" flag (tooltip references a sub-spell ID not in this export)
  - mechanic signal tags (heal/proc/dot/aoe/cc/execute/cooldown/resource)
Class-of-origin and best-fit-Path are NOT auto-guessed from spell names —
the "duplicate-name trap" (primer §2) means name-matching is unsafe (e.g.
Ascension's Mental Quickness shares a name with a real WotLK talent but is
a completely different effect). Those fields are only ever populated from
CONFIRMED sources: proc-tests, live tooltips, or facts already established
in the project docs. Everything else is left NULL/'unverified' on purpose.
"""
import json, re, sqlite3, sys, os
from pathlib import Path

INDEX_DIR = Path(__file__).resolve().parent  # this file lives in index/
SPELL_EXPORT = str(INDEX_DIR / 'spell-export.json')
CARDS_FILE = str(INDEX_DIR / 'Cards.txt')
DB_PATH = str(INDEX_DIR / 'ascension_index.db')  # ephemeral, gitignored - rebuild each session

PURE_SCHOOLS = ['Frost','Fire','Shadow','Arcane','Nature','Holy','Physical']
HYBRID_SCHOOLS = ['Holystrike','Holyfire','Shadowflame','Firestrike','Froststrike',
                   'Shadowstrike','Spellstrike','Stormstrike']
OTHER_SCHOOL_WORDS = ['Fel','Chaos']
ALL_SCHOOLS = PURE_SCHOOLS + HYBRID_SCHOOLS + OTHER_SCHOOL_WORDS

SP_PAT = re.compile(r'\$SP\s*\*\s*([\d.]+)')
AP_PAT = re.compile(r'\$AP\s*\*\s*([\d.]+)')
RAP_PAT = re.compile(r'\$RAP\s*\*\s*([\d.]+)')
WEAPON_PAT = re.compile(r'\$(MWB|mwb|OWB|owb|mw|ow)\b|weapon damage|Normalized', re.I)
SUBSPELL_REF_PAT = re.compile(r'\$(\d{3,7})[a-zA-Z]{1,3}\d*')
PCT_PLACEHOLDER_PAT = re.compile(r'\$s\d+%?')  # unresolved $s1 / $s2 style magnitude

MECHANIC_RULES = {
    'heal':        re.compile(r'\bheal(s|ing|ed)?\b|restore(s)? .*health', re.I),
    'proc':        re.compile(r'chance to|% chance|when you|on your next|has a \$', re.I),
    'dot_hot':     re.compile(r'over \d|over \$|each \$?\d*\s*sec|per sec', re.I),
    'aoe':         re.compile(r'nearby enem|all enem|area|\byards?\b|target area', re.I),
    'cc':          re.compile(r'\bstun(s|ned)?\b|\broot(s|ed)?\b|\bsilence(s|d)?\b|\bfear(s|ed)?\b|'
                               r'\bsleep\b|polymorph|disorient|incapacitat|snare|\bslow(s|ed)?\b', re.I),
    'execute':     re.compile(r'below \d+%|at or below|health remaining', re.I),
    'cooldown_effect': re.compile(r'cooldown', re.I),
    'buff_debuff': re.compile(r'increases|decreases|reduces|grants|gains', re.I),
    'resource_mana':   re.compile(r'\bmana\b', re.I),
    'resource_rage':   re.compile(r'\brage\b', re.I),
    'resource_energy': re.compile(r'\benergy\b', re.I),
    'resource_runic':  re.compile(r'runic power', re.I),
    'resource_holypower': re.compile(r'holy power', re.I),
    'resource_combopoints': re.compile(r'combo point', re.I),
    'resource_focus': re.compile(r'\bfocus\b', re.I),
    'exclusivity_bucket': re.compile(r'does not stack with', re.I),
}

def extract_schools(tooltip):
    found = set()
    for school in ALL_SCHOOLS:
        if re.search(r'\b' + re.escape(school) + r'\b', tooltip):
            found.add(school)
    return sorted(found)

def extract_scaling(tooltip, spell_id, valid_ids):
    # dedupe identical (type, coeff) pairs - per-combo-point / per-rank tables
    # repeat the same unit coefficient once per point/rank in the raw text
    terms = set()
    for m in SP_PAT.finditer(tooltip):
        terms.add(('SP', float(m.group(1))))
    for m in AP_PAT.finditer(tooltip):
        terms.add(('AP', float(m.group(1))))
    for m in RAP_PAT.finditer(tooltip):
        terms.add(('RAP', float(m.group(1))))
    if WEAPON_PAT.search(tooltip):
        terms.add(('WEAPON', None))
    terms = list(terms)
    # hidden sub-spell references (formula lives in a spell NOT in this export)
    hidden_refs = set()
    for m in SUBSPELL_REF_PAT.finditer(tooltip):
        rid = int(m.group(1))
        if rid != spell_id and rid not in valid_ids:
            hidden_refs.add(rid)
    unresolved_pct = bool(PCT_PLACEHOLDER_PAT.search(tooltip))
    return terms, sorted(hidden_refs), unresolved_pct

def extract_mechanics(tooltip):
    return sorted(tag for tag, pat in MECHANIC_RULES.items() if pat.search(tooltip))

def main():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.executescript('''
    CREATE TABLE spells (
        id INTEGER PRIMARY KEY,
        type TEXT,
        name TEXT,
        rank TEXT,
        tooltip TEXT,
        schools TEXT,           -- comma-joined, denormalized for quick reading
        mechanics TEXT,         -- comma-joined
        has_hidden_formula INTEGER,
        hidden_refs TEXT,       -- comma-joined spell IDs not resolvable in this export
        has_unresolved_pct INTEGER,
        class_origin TEXT,      -- ONLY confirmed values, else NULL
        class_confidence TEXT,  -- 'confirmed_proc_test' | 'confirmed_native' | NULL
        best_fit_path TEXT,     -- ONLY confirmed/derived-from-explicit-coeff, else NULL
        notes TEXT
    );

    CREATE TABLE spell_scaling (
        spell_id INTEGER,
        term_type TEXT,    -- SP / AP / RAP / WEAPON
        coefficient REAL,  -- NULL for WEAPON (normalized, no fixed coeff in text)
        FOREIGN KEY(spell_id) REFERENCES spells(id)
    );

    CREATE TABLE owned_cards (
        cardId INTEGER,
        spellId INTEGER,
        rank INTEGER,
        pool TEXT,   -- abilityNormal / abilityGolden / talentNormal / talentGolden
        FOREIGN KEY(spellId) REFERENCES spells(id)
    );

    CREATE TABLE confirmed_facts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic TEXT,
        fact TEXT,
        source_doc TEXT,
        source_section TEXT
    );

    CREATE INDEX idx_spells_name ON spells(name);
    CREATE INDEX idx_scaling_spell ON spell_scaling(spell_id);
    CREATE INDEX idx_owned_spell ON owned_cards(spellId);
    ''')

    with open(SPELL_EXPORT) as f:
        data = json.load(f)
    spells = data['spells']
    valid_ids = {s['id'] for s in spells}

    scaling_rows = []
    for s in spells:
        tooltip = s.get('tooltip') or ''
        schools = extract_schools(tooltip)
        terms, hidden_refs, unresolved_pct = extract_scaling(tooltip, s['id'], valid_ids)
        mechanics = extract_mechanics(tooltip)

        cur.execute('''INSERT INTO spells
            (id, type, name, rank, tooltip, schools, mechanics, has_hidden_formula,
             hidden_refs, has_unresolved_pct, class_origin, class_confidence,
             best_fit_path, notes)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (s['id'], s['type'], s['name'], s.get('rank'), tooltip,
             ','.join(schools), ','.join(mechanics),
             1 if hidden_refs else 0, ','.join(map(str, hidden_refs)),
             1 if unresolved_pct else 0,
             None, None, None, None))

        for term_type, coeff in terms:
            scaling_rows.append((s['id'], term_type, coeff))

    cur.executemany('INSERT INTO spell_scaling VALUES (?,?,?)', scaling_rows)

    # Owned cards
    with open(CARDS_FILE) as f:
        cards = json.load(f)
    owned_rows = []
    for pool, entries in cards.items():
        for e in entries:
            owned_rows.append((e['cardId'], e['spellId'], e['rank'], pool))
    cur.executemany('INSERT INTO owned_cards VALUES (?,?,?,?)', owned_rows)

    conn.commit()

    # sanity report
    cur.execute('SELECT COUNT(*) FROM spells')
    print('spells indexed:', cur.fetchone()[0])
    cur.execute('SELECT COUNT(*) FROM spells WHERE schools != ""')
    print('spells with a detected school:', cur.fetchone()[0])
    cur.execute('SELECT COUNT(DISTINCT spell_id) FROM spell_scaling')
    print('spells with explicit SP/AP/RAP/weapon term:', cur.fetchone()[0])
    cur.execute('SELECT COUNT(*) FROM spells WHERE has_hidden_formula=1')
    print('spells with a hidden (unresolvable) sub-spell formula:', cur.fetchone()[0])
    cur.execute('SELECT COUNT(*) FROM owned_cards')
    print('owned card rows:', cur.fetchone()[0])

    conn.close()

if __name__ == '__main__':
    main()
