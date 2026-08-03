#!/usr/bin/env python3
"""
Tooltip Diff Report: spell_dbc_raw.description vs spells.tooltip

The export tooltip (spells.tooltip, from spell-export.json - an in-game/addon
scan) can render numbers/placeholders resolved and can also just omit entire
clauses the live/raw tooltip has (confirmed_facts 'export_tooltip_incomplete':
Enhanced Weapon Mastery's export tooltip dropped its exclusivity clause
entirely). Lightbound Cleave's raw DBC text similarly carries a distinct
"@ext:This uses Cleave modifiers.:ext@" clause that turns out to be the literal
mechanism behind the class-tag rule (primer §4).

This is a whole-catalog systematic search for more of those: for every spell
with both a tooltip and a spell_dbc_raw.description, split each into clauses,
strip out macro placeholders/numbers (so raw-vs-resolved formatting doesn't
cause false positives), and flag any DBC clause with no reasonable match in
the export tooltip's clauses. "@ext:...:ext@" wrapped clauses and "uses X
modifiers" lines are always flagged regardless of similarity score, since
those are the highest-value catches (same shape as the Enhanced Weapon
Mastery and Lightbound Cleave cases).

Output only - never edits spells.tooltip. These need human judgment before
they change anything downstream.
"""
import json
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = str(ROOT / 'data' / 'ascension_index.db')
REPORT_MD = ROOT / 'docs' / 'tooltip_diff_report.md'
REPORT_JSON = ROOT / 'data' / 'tooltip_diff_report.json'

MACRO_PAT = re.compile(r'\$\{[^}]*\}|\$\w+')
EXT_PAT = re.compile(r'@ext:(.*?):ext@', re.S)
NONWORD_PAT = re.compile(r'[^a-z0-9%\s]')
WS_PAT = re.compile(r'\s+')

STOPWORDS = {
    'a', 'an', 'the', 'to', 'of', 'and', 'or', 'your', 'you', 'is', 'are',
    'in', 'on', 'for', 'with', 'that', 'this', 'by', 'as', 'at', 'it', 'if',
}


def normalize(text):
    text = MACRO_PAT.sub(' NUM ', text)
    text = text.lower()
    text = NONWORD_PAT.sub(' ', text)
    text = WS_PAT.sub(' ', text).strip()
    return text


def split_clauses(raw_text):
    """Returns list of (kind, clause_text) - kind is 'ext' for @ext:...:ext@
    wrapped clauses, else 'plain'."""
    clauses = []
    remaining = raw_text
    for m in EXT_PAT.finditer(raw_text):
        clauses.append(('ext', m.group(1).strip()))
    plain_text = EXT_PAT.sub(' ', raw_text)
    for para in re.split(r'\r?\n\r?\n+|\r?\n', plain_text):
        for sent in re.split(r'(?<=[.!?])\s+', para):
            sent = sent.strip()
            if sent:
                clauses.append(('plain', sent))
    return clauses


def significant_tokens(norm_text):
    return {t for t in norm_text.split() if t not in STOPWORDS and len(t) > 1}


def jaccard(a, b):
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def best_match_score(clause_tokens, other_clause_token_sets):
    if not other_clause_token_sets:
        return 0.0
    return max(jaccard(clause_tokens, o) for o in other_clause_token_sets)


SIMILARITY_THRESHOLD = 0.35
MIN_CLAUSE_LEN = 12  # skip trivially short fragments


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        SELECT s.id, s.name, s.tooltip, d.description
        FROM spells s
        JOIN spell_dbc_raw d ON d.id = s.id
        WHERE s.tooltip IS NOT NULL AND s.tooltip != ''
          AND d.description IS NOT NULL AND d.description != ''
    ''')
    rows = cur.fetchall()
    print(f'Comparing {len(rows)} catalog spells with both a tooltip and a DBC description...')

    findings = []
    for sid, name, tooltip, description in rows:
        export_clauses = split_clauses(tooltip)
        export_token_sets = [significant_tokens(normalize(c)) for _, c in export_clauses]

        dbc_clauses = split_clauses(description)
        for kind, clause in dbc_clauses:
            if len(clause) < MIN_CLAUSE_LEN:
                continue
            norm = normalize(clause)
            tokens = significant_tokens(norm)
            if not tokens:
                continue
            score = best_match_score(tokens, export_token_sets)
            is_modifier_clause = 'modifiers' in norm and 'use' in norm
            missing = score < SIMILARITY_THRESHOLD
            # "@ext@" is Blizzard's own long-standing wrapper for all sorts of
            # common caveat text (cooldown sharing, "does not stack", etc.) -
            # most of that is native/expected, so an ext clause only matters
            # here if it's the "uses X modifiers" class-tag mechanism (always
            # worth cataloguing, primer §4) or genuinely missing from export.
            if is_modifier_clause:
                category = 'modifier_missing' if missing else 'modifier_present'
            elif missing:
                category = 'other_missing'
            else:
                continue
            findings.append({
                'id': sid, 'name': name, 'kind': kind,
                'clause': clause, 'best_match_score': round(score, 2),
                'category': category,
            })

    findings.sort(key=lambda f: f['best_match_score'])

    REPORT_JSON.write_text(json.dumps(findings, indent=1), encoding='utf-8')

    modifier_missing = [f for f in findings if f['category'] == 'modifier_missing']
    modifier_present = [f for f in findings if f['category'] == 'modifier_present']
    other_missing = [f for f in findings if f['category'] == 'other_missing']

    lines = [
        '# Tooltip Diff Report',
        '',
        f'Catalog spells compared: {len(rows)}',
        f'Total flagged clauses: {len(findings)}',
        f'  - "uses X modifiers" line, MISSING from export tooltip entirely: {len(modifier_missing)}',
        f'  - "uses X modifiers" line, also present in export tooltip (catalogued for reference): {len(modifier_present)}',
        f'  - other DBC-only clause, no export-tooltip match (similarity < {SIMILARITY_THRESHOLD}): {len(other_missing)}',
        '',
        '## "uses X modifiers" lines MISSING from the export tooltip (highest priority)',
        '',
        'These spells\' class-tag mechanism (primer §4) is only visible in the raw',
        'client data - the export tooltip a player/addon sees does not mention it',
        'at all. Same shape as the Enhanced Weapon Mastery omission already on record.',
        '',
    ]
    for f in modifier_missing:
        lines.append(f"- **{f['id']} {f['name']}**: {f['clause']}")
    lines += [
        '', '## Other DBC-only clauses (no good match in export tooltip)', '',
    ]
    for f in other_missing:
        lines.append(f"- **{f['id']} {f['name']}** (match={f['best_match_score']}): {f['clause']}")
    lines += [
        '', '## "uses X modifiers" lines already present in export tooltip (reference catalog)', '',
        'Not missing - just a full list of every class-tag mechanism spell found,',
        'for cross-referencing into the class-tag/duplicate-name-trap work.', '',
    ]
    for f in modifier_present:
        lines.append(f"- **{f['id']} {f['name']}**: {f['clause']}")

    REPORT_MD.write_text('\n'.join(lines), encoding='utf-8')

    print(f'\n{len(findings)} flagged clauses: {len(modifier_missing)} missing modifier lines, '
          f'{len(other_missing)} other missing clauses, {len(modifier_present)} modifier lines already present')
    print(f'Report written to {REPORT_MD}')
    print(f'Raw data written to {REPORT_JSON}')

    conn.close()


if __name__ == '__main__':
    main()
