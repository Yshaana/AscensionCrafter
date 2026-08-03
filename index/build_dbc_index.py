#!/usr/bin/env python3
"""
DBC Spell/Talent Index Builder
Reads Spell.dbc and its supporting lookup tables straight out of the client's
own MPQ archives (via a locally-built StormLib) and stores them in
ascension_index.db, keyed by ID. This resolves spells flagged
has_hidden_formula=1 in the `spells` table (built by build_index.py from
spell-export.json, an in-game/addon-reachable scan) against the client's
full internal catalog, which also contains helper sub-spells no addon can see.

Field layouts are taken directly from TrinityCore's DBCStructure.h (3.3.5
branch) SpellEntry/TalentEntry/etc structs, including columns TrinityCore
itself comments out (e.g. Spell.dbc's raw Description text) because the
column still occupies real space in the row and we need it.

Does NOT touch or commit the client's MPQ files (Blizzard/Ascension
copyrighted assets) - only the parsed-out data ends up in the repo.

Re-run this whenever the client patches: it re-discovers which archive
currently holds each DBC file (see find_owning_archive) rather than
hardcoding a patch filename, since Ascension's patch-letter naming isn't
guaranteed stable across client updates.
"""
import argparse
import ctypes
from ctypes import wintypes
import json
import os
import re
import sqlite3
import struct
import sys
from pathlib import Path

INDEX_DIR = Path(__file__).resolve().parent  # this file lives in index/
DB_PATH = str(INDEX_DIR / 'ascension_index.db')  # ephemeral, gitignored
DBC_EXTRACT_JSON = INDEX_DIR / 'dbc-extract.json'  # committed - survives the db being gitignored

DEFAULT_DATA_PATH = r"E:\Ascension Launcher\resources\ascension-live\Data"
DEFAULT_STORMLIB_DLL = os.environ.get(
    'ASCENSION_STORMLIB_DLL',
    r"C:\Users\Yshaana\Documents\dbc-extraction-work\refs\stormlib\build\Release\StormLib.dll")

# Archives known to be stock Blizzard/locale files (not Ascension's own content).
# Anything else that turns up in the Data folder is treated as a candidate
# custom-patch override.
STOCK_ARCHIVE_NAMES = {
    'common.mpq', 'common-2.mpq', 'expansion.mpq', 'lichking.mpq',
    'patch.mpq', 'patch-2.mpq', 'patch-3.mpq', 'patch-4.mpq', 'patch-5.mpq',
    'base-enus.mpq', 'locale-enus.mpq', 'expansion-locale-enus.mpq',
    'expansion-speech-enus.mpq', 'lichking-locale-enus.mpq',
    'lichking-speech-enus.mpq', 'speech-enus.mpq', 'backup-enus.mpq',
    'patch-enus.mpq', 'patch-enus-2.mpq', 'patch-enus-3.mpq',
}


# ---------------------------------------------------------------------------
# Minimal ctypes StormLib wrapper (ANSI build - STORM_UNICODE is OFF by default)
# ---------------------------------------------------------------------------
class MpqArchive:
    _lib = None

    @classmethod
    def _load(cls, dll_path):
        if cls._lib is None:
            lib = ctypes.WinDLL(dll_path)
            lib.SFileOpenArchive.argtypes = [wintypes.LPCSTR, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE)]
            lib.SFileOpenArchive.restype = wintypes.BOOL
            lib.SFileCloseArchive.argtypes = [wintypes.HANDLE]
            lib.SFileCloseArchive.restype = wintypes.BOOL
            lib.SFileHasFile.argtypes = [wintypes.HANDLE, wintypes.LPCSTR]
            lib.SFileHasFile.restype = wintypes.BOOL
            lib.SFileOpenFileEx.argtypes = [wintypes.HANDLE, wintypes.LPCSTR, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE)]
            lib.SFileOpenFileEx.restype = wintypes.BOOL
            lib.SFileGetFileSize.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
            lib.SFileGetFileSize.restype = wintypes.DWORD
            lib.SFileReadFile.argtypes = [wintypes.HANDLE, wintypes.LPVOID, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD), wintypes.LPVOID]
            lib.SFileReadFile.restype = wintypes.BOOL
            lib.SFileCloseFile.argtypes = [wintypes.HANDLE]
            lib.SFileCloseFile.restype = wintypes.BOOL
            cls._lib = lib
        return cls._lib

    def __init__(self, path, dll_path):
        lib = self._load(dll_path)
        self.lib = lib
        self.handle = wintypes.HANDLE()
        flags = 0x00000100 | 0x00010000 | 0x00020000  # READ_ONLY | NO_LISTFILE | NO_ATTRIBUTES
        if not lib.SFileOpenArchive(str(path).encode('mbcs'), 0, flags, ctypes.byref(self.handle)):
            raise OSError(f'SFileOpenArchive failed for {path}, error {ctypes.GetLastError()}')

    def has_file(self, internal_path):
        return bool(self.lib.SFileHasFile(self.handle, internal_path.encode('ascii')))

    def read_file(self, internal_path):
        fh = wintypes.HANDLE()
        if not self.lib.SFileOpenFileEx(self.handle, internal_path.encode('ascii'), 0, ctypes.byref(fh)):
            raise OSError(f'SFileOpenFileEx failed for {internal_path}, error {ctypes.GetLastError()}')
        try:
            size = self.lib.SFileGetFileSize(fh, None)
            buf = ctypes.create_string_buffer(size)
            read = wintypes.DWORD(0)
            self.lib.SFileReadFile(fh, buf, size, ctypes.byref(read), None)
            return buf.raw[:read.value]
        finally:
            self.lib.SFileCloseFile(fh)

    def close(self):
        self.lib.SFileCloseArchive(self.handle)

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()


# ---------------------------------------------------------------------------
# Generic WDBC container
# ---------------------------------------------------------------------------
WDBC_HEADER = struct.Struct('<4s4I')


def load_dbc(data):
    magic, record_count, field_count, record_size, string_block_size = WDBC_HEADER.unpack_from(data, 0)
    if magic != b'WDBC':
        raise ValueError(f'bad magic {magic!r}')
    header_size = WDBC_HEADER.size
    records_size = record_count * record_size
    records_blob = data[header_size:header_size + records_size]
    string_block = data[header_size + records_size:header_size + records_size + string_block_size]
    records = [records_blob[i * record_size:(i + 1) * record_size] for i in range(record_count)]
    return {
        'record_count': record_count, 'field_count': field_count,
        'record_size': record_size, 'string_block_size': string_block_size,
        'records': records, 'string_block': string_block,
    }


def read_cstr(string_block, offset):
    if offset == 0 or offset >= len(string_block):
        return ''
    end = string_block.index(b'\x00', offset)
    return string_block[offset:end].decode('utf-8', errors='replace')


# NOTE on text that looks corrupted but isn't: raw descriptions frequently
# contain "$<spellID>donds" (e.g. "over $61840donds as Holy damage") with no
# space. This is not a read bug - verified byte-for-byte against the raw MPQ
# data and confirmed as a standard, long-standing WoW tooltip convention that
# recurs 400+ times across this file: the "$<id>d" macro renders as a bare
# unit ("8 sec"/"8 min") at tooltip time, and authors glue on the remaining
# letters ("onds"/"utes") to spell out the full word without a space, since
# the client's renderer already inserted one. Leave these as-is; they are
# meant to stay unresolved raw text same as any other $s1/$m1-style macro.


def find_owning_archive(mpq_paths, internal_path, dll_path):
    """Every archive that contains internal_path. Caller decides how to pick
    among them; in practice (checked 2026-08) each target DBC file is present
    in exactly one non-stock archive, so there is nothing to disambiguate."""
    hits = []
    for path in mpq_paths:
        try:
            with MpqArchive(path, dll_path) as mpq:
                if mpq.has_file(internal_path):
                    hits.append(path)
        except OSError:
            continue
    return hits


def pick_final_archive(hits, internal_path):
    non_stock = [h for h in hits if os.path.basename(h).lower() not in STOCK_ARCHIVE_NAMES]
    if len(non_stock) == 1:
        return non_stock[0]
    if len(non_stock) > 1:
        print(f'WARNING: {internal_path} present in multiple custom archives {non_stock} '
              f'- patch order can not be inferred automatically, picking last by name', file=sys.stderr)
        return sorted(non_stock)[-1]
    if hits:
        print(f'NOTE: {internal_path} only found in stock archives, using last: {hits[-1]}', file=sys.stderr)
        return hits[-1]
    return None


def list_all_mpqs(data_path):
    base = [os.path.join(data_path, f) for f in os.listdir(data_path) if f.lower().endswith('.mpq')]
    enus_dir = os.path.join(data_path, 'enUS')
    enus = [os.path.join(enus_dir, f) for f in os.listdir(enus_dir) if f.lower().endswith('.mpq')] if os.path.isdir(enus_dir) else []
    return base + enus


# ---------------------------------------------------------------------------
# Spell.dbc field layout (234 x 4-byte slots / 936-byte record, 3.3.5a),
# from TrinityCore src/server/shared/DataStores/DBCStructure.h SpellEntry.
# ---------------------------------------------------------------------------
MAX_SPELL_EFFECTS = 3
MAX_SPELL_REAGENTS = 8

SPELL_FIELDS = [
    ('ID', 'u32', 1), ('Category', 'u32', 1), ('DispelType', 'u32', 1), ('Mechanic', 'u32', 1),
    ('Attributes', 'u32', 1), ('AttributesEx', 'u32', 1), ('AttributesExB', 'u32', 1),
    ('AttributesExC', 'u32', 1), ('AttributesExD', 'u32', 1), ('AttributesExE', 'u32', 1),
    ('AttributesExF', 'u32', 1), ('AttributesExG', 'u32', 1),
    ('ShapeshiftMask', 'u32', 2), ('ShapeshiftExclude', 'u32', 2),
    ('Targets', 'u32', 1), ('TargetCreatureType', 'u32', 1), ('RequiresSpellFocus', 'u32', 1),
    ('FacingCasterFlags', 'u32', 1), ('CasterAuraState', 'u32', 1), ('TargetAuraState', 'u32', 1),
    ('ExcludeCasterAuraState', 'u32', 1), ('ExcludeTargetAuraState', 'u32', 1),
    ('CasterAuraSpell', 'u32', 1), ('TargetAuraSpell', 'u32', 1),
    ('ExcludeCasterAuraSpell', 'u32', 1), ('ExcludeTargetAuraSpell', 'u32', 1),
    ('CastingTimeIndex', 'u32', 1), ('RecoveryTime', 'u32', 1), ('CategoryRecoveryTime', 'u32', 1),
    ('InterruptFlags', 'u32', 1), ('AuraInterruptFlags', 'u32', 1), ('ChannelInterruptFlags', 'u32', 1),
    ('ProcTypeMask', 'u32', 1), ('ProcChance', 'u32', 1), ('ProcCharges', 'u32', 1),
    ('MaxLevel', 'u32', 1), ('BaseLevel', 'u32', 1), ('SpellLevel', 'u32', 1),
    ('DurationIndex', 'u32', 1), ('PowerType', 'u32', 1), ('ManaCost', 'u32', 1),
    ('ManaCostPerLevel', 'u32', 1), ('ManaPerSecond', 'u32', 1), ('ManaPerSecondPerLevel', 'u32', 1),
    ('RangeIndex', 'u32', 1), ('Speed', 'f32', 1), ('ModalNextSpell', 'u32', 1), ('CumulativeAura', 'u32', 1),
    ('Totem', 'u32', 2), ('Reagent', 'i32', MAX_SPELL_REAGENTS), ('ReagentCount', 'u32', MAX_SPELL_REAGENTS),
    ('EquippedItemClass', 'i32', 1), ('EquippedItemSubclass', 'i32', 1), ('EquippedItemInvTypes', 'i32', 1),
    ('Effect', 'u32', MAX_SPELL_EFFECTS), ('EffectDieSides', 'i32', MAX_SPELL_EFFECTS),
    ('EffectRealPointsPerLevel', 'f32', MAX_SPELL_EFFECTS), ('EffectBasePoints', 'i32', MAX_SPELL_EFFECTS),
    ('EffectMechanic', 'u32', MAX_SPELL_EFFECTS), ('EffectImplicitTargetA', 'u32', MAX_SPELL_EFFECTS),
    ('EffectImplicitTargetB', 'u32', MAX_SPELL_EFFECTS), ('EffectRadiusIndex', 'u32', MAX_SPELL_EFFECTS),
    ('EffectAura', 'u32', MAX_SPELL_EFFECTS), ('EffectAuraPeriod', 'u32', MAX_SPELL_EFFECTS),
    ('EffectAmplitude', 'f32', MAX_SPELL_EFFECTS), ('EffectChainTargets', 'u32', MAX_SPELL_EFFECTS),
    ('EffectItemType', 'u32', MAX_SPELL_EFFECTS), ('EffectMiscValue', 'i32', MAX_SPELL_EFFECTS),
    ('EffectMiscValueB', 'i32', MAX_SPELL_EFFECTS), ('EffectTriggerSpell', 'u32', MAX_SPELL_EFFECTS),
    ('EffectPointsPerCombo', 'f32', MAX_SPELL_EFFECTS),
    ('EffectSpellClassMask', 'u32', MAX_SPELL_EFFECTS * 3),
    ('SpellVisualID', 'u32', 2), ('SpellIconID', 'u32', 1), ('ActiveIconID', 'u32', 1), ('SpellPriority', 'u32', 1),
    ('Name', 'strblock', 1), ('NameSubtext', 'strblock', 1), ('Description', 'strblock', 1), ('AuraDescription', 'strblock', 1),
    ('ManaCostPct', 'u32', 1), ('StartRecoveryCategory', 'u32', 1), ('StartRecoveryTime', 'u32', 1),
    ('MaxTargetLevel', 'u32', 1), ('SpellClassSet', 'u32', 1), ('SpellClassMask', 'u32', 3),
    ('MaxTargets', 'u32', 1), ('DefenseType', 'u32', 1), ('PreventionType', 'u32', 1), ('StanceBarOrder', 'u32', 1),
    ('EffectChainAmplitude', 'f32', MAX_SPELL_EFFECTS),
    ('MinFactionID', 'u32', 1), ('MinReputation', 'u32', 1), ('RequiredAuraVision', 'u32', 1),
    ('RequiredTotemCategoryID', 'u32', 2), ('RequiredAreasID', 'i32', 1), ('SchoolMask', 'u32', 1),
    ('RuneCostID', 'u32', 1), ('SpellMissileID', 'u32', 1), ('PowerDisplayID', 'u32', 1),
    ('EffectBonusCoefficient', 'f32', MAX_SPELL_EFFECTS),
    ('DescriptionVariablesID', 'u32', 1), ('Difficulty', 'u32', 1),
]
SPELL_TOTAL_SLOTS = sum(17 * c if k == 'strblock' else c for _, k, c in SPELL_FIELDS)
assert SPELL_TOTAL_SLOTS == 234


def parse_spell_record(record_bytes, string_block):
    slots_u = struct.unpack_from(f'<{SPELL_TOTAL_SLOTS}I', record_bytes, 0)
    slots_f = struct.unpack_from(f'<{SPELL_TOTAL_SLOTS}f', record_bytes, 0)
    slots_i = struct.unpack_from(f'<{SPELL_TOTAL_SLOTS}i', record_bytes, 0)
    out, pos = {}, 0
    for name, kind, count in SPELL_FIELDS:
        if kind == 'strblock':
            offsets = slots_u[pos:pos + 16]
            texts = [read_cstr(string_block, o) for o in offsets]
            out[name] = next((t for t in texts if t), '')
            pos += 17
        elif kind == 'u32':
            vals = slots_u[pos:pos + count]
            out[name] = vals[0] if count == 1 else list(vals)
            pos += count
        elif kind == 'i32':
            vals = slots_i[pos:pos + count]
            out[name] = vals[0] if count == 1 else list(vals)
            pos += count
        elif kind == 'f32':
            vals = slots_f[pos:pos + count]
            out[name] = vals[0] if count == 1 else list(vals)
            pos += count
    return out


# Small supporting-table layouts (TrinityCore DBCStructure.h). Verified at
# runtime against the file's own field_count before use - if a client update
# changes the schema, extraction for that table is skipped with a warning
# rather than silently misreading bytes.
SUPPORT_TABLES = {
    'SpellDuration.dbc': (4, [('ID', 'u32', 1), ('Duration', 'i32', 1), ('DurationPerLevel', 'i32', 1), ('MaxDuration', 'i32', 1)]),
    'SpellRange.dbc': (6, [('ID', 'u32', 1), ('RangeMinHostile', 'f32', 1), ('RangeMinFriendly', 'f32', 1),
                            ('RangeMaxHostile', 'f32', 1), ('RangeMaxFriendly', 'f32', 1), ('Flags', 'u32', 1)]),
    'SpellCastTimes.dbc': (2, [('ID', 'u32', 1), ('Base', 'i32', 1)]),
    'SpellRadius.dbc': (4, [('ID', 'u32', 1), ('Radius', 'f32', 1), ('RadiusPerLevel', 'f32', 1), ('RadiusMax', 'f32', 1)]),
    'Talent.dbc': (14, [('ID', 'u32', 1), ('TabID', 'u32', 1), ('TierID', 'u32', 1), ('ColumnIndex', 'u32', 1),
                         ('SpellRank', 'u32', 5), ('PrereqTalent', 'u32', 1), ('PrereqRank', 'u32', 1)]),
    'TalentTab.dbc': (23, [('ID', 'u32', 1), ('ClassMask', 'u32', 1), ('PetTalentMask', 'u32', 1), ('OrderIndex', 'u32', 1)]),
}


def parse_simple_record(record_bytes, string_block, fields, expected_slots, actual_field_count):
    """fields need not cover every slot (trailing/interior columns can be
    skipped); only the leading columns up to the last named field are read."""
    slots_u = struct.unpack_from(f'<{actual_field_count}I', record_bytes, 0)
    slots_f = struct.unpack_from(f'<{actual_field_count}f', record_bytes, 0)
    slots_i = struct.unpack_from(f'<{actual_field_count}i', record_bytes, 0)
    out, pos = {}, 0
    for name, kind, count in fields:
        if kind == 'u32':
            vals = slots_u[pos:pos + count]
        elif kind == 'i32':
            vals = slots_i[pos:pos + count]
        elif kind == 'f32':
            vals = slots_f[pos:pos + count]
        else:
            raise ValueError(kind)
        out[name] = vals[0] if count == 1 else list(vals)
        pos += count
    return out


# ---------------------------------------------------------------------------
# Validation: a small fixed set of spells with exact-wording facts already on
# record (confirmed_facts / handoff docs), checked against freshly-extracted
# spell_dbc_raw.description on every run. Substrings are chosen to be things
# that appear in the RAW (unresolved-macro) text verbatim - not the rendered
# English a player would see - so this doesn't false-positive on ordinary
# $s1/$m1/$61840d-style placeholders that are supposed to stay unresolved.
# If the client patches and any of these stop matching, something about the
# extraction (or the spell itself) genuinely changed and needs a look.
# ---------------------------------------------------------------------------
VALIDATION_SPELLS = [
    (907300, 'Lightbound Cleave', ['uses Cleave modifiers']),
    (907894, 'Dawn Strike', ['uses Sinister Strike modifiers']),
    (903158, 'Dawnreaver', ['uses Crusader Strike modifiers']),
    (913444, 'Blades of Light', ['uses Bladestorm modifiers']),
    (907780, 'Whirling Light', ['uses Whirlwind modifiers']),
    (280210, 'Judgement of The Three Hammers', ['SP*0.325', 'AP*0.278']),
    (276076, 'Fel Infused Weapon', ['AP*0.05', 'SP*0.05']),
    (272624, 'Molten Earth', ['uses Fire Nova modifiers']),
    (853486, 'The Art of War', ['Judgement, Crusader Strike, Execution Sentence and Divine Storm']),
    (53382, 'Righteous Vengeance', ['$s1% additional damage', '$61840d']),
]


def validate_known_spells(cur):
    cur.execute('SELECT id, description FROM spell_dbc_raw WHERE id IN ({})'.format(
        ','.join(str(sid) for sid, _, _ in VALIDATION_SPELLS)))
    by_id = dict(cur.fetchall())
    failures = []
    for sid, name, expected_substrings in VALIDATION_SPELLS:
        desc = by_id.get(sid)
        if desc is None:
            failures.append(f'{sid} ({name}): not present in spell_dbc_raw at all')
            continue
        for expected in expected_substrings:
            if expected not in desc:
                failures.append(
                    f'{sid} ({name}): expected substring {expected!r} not found.\n'
                    f'    actual description: {desc!r}')
    if failures:
        print('\nVALIDATION FAILED - extraction regressed against known-good spells:', file=sys.stderr)
        for f in failures:
            print(f'  - {f}', file=sys.stderr)
        sys.exit(1)
    print(f'\nValidation OK: {len(VALIDATION_SPELLS)} known spells match expected raw text.')


# ---------------------------------------------------------------------------
# Resolve has_hidden_formula=1 spells: pull each hidden_ref's raw description
# from spell_dbc_raw and run it through the exact same SP/AP/RAP/weapon regex
# build_index.py uses on directly-visible tooltips, since the coefficients in
# these hidden sub-spells are written the same way ("$AP*0.091", "$SP*0.325").
# ---------------------------------------------------------------------------
SP_PAT = re.compile(r'\$SP\s*\*\s*([\d.]+)')
AP_PAT = re.compile(r'\$AP\s*\*\s*([\d.]+)')
RAP_PAT = re.compile(r'\$RAP\s*\*\s*([\d.]+)')
WEAPON_PAT = re.compile(r'\$(MWB|mwb|OWB|owb|mw|ow)\b|weapon damage|Normalized', re.I)


def extract_scaling_terms(text):
    terms = set()
    for m in SP_PAT.finditer(text):
        terms.add(('SP', float(m.group(1))))
    for m in AP_PAT.finditer(text):
        terms.add(('AP', float(m.group(1))))
    for m in RAP_PAT.finditer(text):
        terms.add(('RAP', float(m.group(1))))
    if WEAPON_PAT.search(text):
        terms.add(('WEAPON', None))
    return terms


def ensure_spell_scaling_source_column(cur):
    cur.execute("PRAGMA table_info(spell_scaling)")
    if 'source' not in {row[1] for row in cur.fetchall()}:
        cur.execute("ALTER TABLE spell_scaling ADD COLUMN source TEXT")
        cur.execute("UPDATE spell_scaling SET source='export_tooltip' WHERE source IS NULL")


def resolve_hidden_formula_spells(cur):
    ensure_spell_scaling_source_column(cur)
    # idempotent: only this step's own rows get cleared/re-derived on re-run
    cur.execute("DELETE FROM spell_scaling WHERE source='dbc_hidden_formula'")

    cur.execute('SELECT id, hidden_refs FROM spells WHERE has_hidden_formula=1')
    targets = cur.fetchall()
    cur.execute('SELECT id, description, effect_json FROM spell_dbc_raw')
    dbc_rows = {r[0]: (r[1], r[2]) for r in cur.fetchall()}

    resolved_count = 0
    unresolved = []
    new_rows = []
    surprises = []

    cur.execute("SELECT fact FROM confirmed_facts")
    all_facts = [f[0] for f in cur.fetchall()]

    for sid, hidden_refs in targets:
        ref_ids = [int(x) for x in hidden_refs.split(',') if x.strip()]
        found_terms = []
        detail = []
        for rid in ref_ids:
            row = dbc_rows.get(rid)
            if row is None:
                detail.append(f'{rid}: not in spell_dbc_raw scope')
                continue
            desc, effect_json = row
            terms = extract_scaling_terms(desc)
            if terms:
                found_terms.extend((rid, t, c) for t, c in terms)
            else:
                detail.append(f'{rid}: no SP/AP/RAP/weapon term in raw text '
                               f'(effect_json={effect_json})')

        if found_terms:
            resolved_count += 1
            for rid, term_type, coeff in found_terms:
                new_rows.append((sid, term_type, coeff, 'dbc_hidden_formula'))
            # surprise check: does an existing confirmed_facts row already
            # assert a coefficient for one of these spells that now conflicts?
            cur.execute('SELECT name FROM spells WHERE id=?', (sid,))
            name_row = cur.fetchone()
            name = name_row[0] if name_row else str(sid)
            for rid, term_type, coeff in found_terms:
                cur.execute('SELECT name FROM spell_dbc_raw WHERE id=?', (rid,))
                sub_row = cur.fetchone()
                sub_name = sub_row[0] if sub_row else str(rid)
                for fact in all_facts:
                    if sub_name and sub_name in fact and ('%' in fact or 'assumed' in fact.lower()):
                        surprises.append({
                            'spell_id': sid, 'spell_name': name,
                            'hidden_ref_id': rid, 'hidden_ref_name': sub_name,
                            'resolved_term': term_type, 'resolved_coefficient': coeff,
                            'conflicting_fact': fact,
                        })
            cur.execute('UPDATE spells SET has_hidden_formula=0 WHERE id=?', (sid,))
        else:
            unresolved.append((sid, '; '.join(detail)))
            note = ' | DBC lookup: ' + '; '.join(detail)
            cur.execute('UPDATE spells SET notes=COALESCE(notes,"")||? WHERE id=?', (note, sid))

    cur.executemany('INSERT INTO spell_scaling (spell_id, term_type, coefficient, source) VALUES (?,?,?,?)',
                     new_rows)

    print(f'\nhas_hidden_formula spells resolved into spell_scaling: {resolved_count} / {len(targets)}')
    print(f'left flagged (no SP/AP/RAP/weapon term found in hidden sub-spell text): {len(unresolved)}')
    if surprises:
        print(f'\nSURPRISING resolutions (conflict with an existing confirmed_facts entry):')
        for s in surprises:
            print(f"  - spell {s['spell_id']} ({s['spell_name']}) -> hidden ref {s['hidden_ref_id']} "
                  f"({s['hidden_ref_name']}): resolved {s['resolved_term']}={s['resolved_coefficient']}")
            print(f"    existing fact: {s['conflicting_fact'][:300]}")
    return resolved_count, unresolved, surprises


# ---------------------------------------------------------------------------
# ascension_index.db is a rebuilt-each-session derived cache (primer v10/v12)
# and is gitignored - but spell_dbc_raw/dbc_* and the hidden-formula-derived
# spell_scaling rows can only be regenerated on a machine with the Ascension
# client + a built StormLib.dll, unlike the rest of the index. Export them to
# a plain JSON file that DOES get committed, so a session without client
# access can still load these results instead of re-running this whole
# pipeline from scratch.
# ---------------------------------------------------------------------------
def export_dbc_extract_json(cur):
    cur.execute('SELECT id, name, name_subtext, description, aura_description, '
                'attributes, attributes_ex, school_mask, effect_json, source_archive '
                'FROM spell_dbc_raw')
    cols = ['id', 'name', 'name_subtext', 'description', 'aura_description',
            'attributes', 'attributes_ex', 'school_mask', 'effect_json', 'source_archive']
    spell_dbc_raw = [dict(zip(cols, row)) for row in cur.fetchall()]

    support_tables = {}
    for table_name in ('dbc_spellduration', 'dbc_spellrange', 'dbc_spellcasttimes',
                        'dbc_spellradius', 'dbc_talent', 'dbc_talenttab'):
        cur.execute(f'SELECT * FROM {table_name}')
        table_cols = [d[0] for d in cur.description]
        support_tables[table_name] = [dict(zip(table_cols, row)) for row in cur.fetchall()]

    cur.execute("SELECT spell_id, term_type, coefficient FROM spell_scaling WHERE source='dbc_hidden_formula'")
    hidden_formula_scaling = [{'spell_id': r[0], 'term_type': r[1], 'coefficient': r[2]} for r in cur.fetchall()]

    payload = {
        'spell_dbc_raw': spell_dbc_raw,
        'support_tables': support_tables,
        'hidden_formula_scaling': hidden_formula_scaling,
    }
    DBC_EXTRACT_JSON.write_text(json.dumps(payload, indent=1), encoding='utf-8')
    print(f'\nExported {len(spell_dbc_raw)} spell_dbc_raw rows + '
          f'{sum(len(v) for v in support_tables.values())} support-table rows + '
          f'{len(hidden_formula_scaling)} hidden-formula scaling rows to {DBC_EXTRACT_JSON}')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--data-path', default=DEFAULT_DATA_PATH, help='Client Data folder')
    ap.add_argument('--stormlib-dll', default=DEFAULT_STORMLIB_DLL, help='Path to a built StormLib.dll')
    ap.add_argument('--db', default=DB_PATH)
    args = ap.parse_args()

    if not os.path.isdir(args.data_path):
        print(f'ERROR: data path not found: {args.data_path}', file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(args.stormlib_dll):
        print(f'ERROR: StormLib.dll not found: {args.stormlib_dll}\n'
              f'Build it first (see refs/stormlib in the DBC extraction work dir).', file=sys.stderr)
        sys.exit(1)

    mpqs = list_all_mpqs(args.data_path)
    print(f'Scanning {len(mpqs)} MPQ archives under {args.data_path} ...')

    conn = sqlite3.connect(args.db)
    cur = conn.cursor()

    # --- Spell.dbc ---------------------------------------------------------
    hits = find_owning_archive(mpqs, 'DBFilesClient\\Spell.dbc', args.stormlib_dll)
    spell_archive = pick_final_archive(hits, 'Spell.dbc')
    if spell_archive is None:
        print('ERROR: Spell.dbc not found in any archive', file=sys.stderr)
        sys.exit(1)
    print(f'Spell.dbc -> {spell_archive}')

    with MpqArchive(spell_archive, args.stormlib_dll) as mpq:
        raw = mpq.read_file('DBFilesClient\\Spell.dbc')
    dbc = load_dbc(raw)
    if dbc['field_count'] != SPELL_TOTAL_SLOTS:
        print(f'WARNING: Spell.dbc field_count={dbc["field_count"]} does not match the '
              f'expected TrinityCore 3.3.5a layout ({SPELL_TOTAL_SLOTS}) - schema may have '
              f'changed; parsed values below could be wrong.', file=sys.stderr)

    cur.executescript('''
    DROP TABLE IF EXISTS spell_dbc_raw;
    CREATE TABLE spell_dbc_raw (
        id INTEGER PRIMARY KEY,
        name TEXT,
        name_subtext TEXT,
        description TEXT,
        aura_description TEXT,
        attributes INTEGER, attributes_ex INTEGER,
        school_mask INTEGER,
        effect_json TEXT,      -- Effect[3] + all Effect* arrays, as JSON
        source_archive TEXT
    );
    ''')

    # The client ships ~209k spells total (its full internal catalog, incl.
    # unused/dev content); this project's own catalog (spell-export.json,
    # the `spells` table) only covers ~3k. Committing all 209k blows the
    # repo up to ~190MB, past GitHub's push limit. Scope spell_dbc_raw down
    # to what's actually useful here: every catalog spell, every hidden_refs
    # target (the whole point of this pipeline), and a small ID-neighborhood
    # buffer per seed_confirmed.py's own "check +/-1-3 for a rank sibling"
    # heuristic. Re-run with a wider filter (or none) if a future need
    # requires an arbitrary spell ID outside this set - full re-derivation
    # from the client is always one script run away.
    cur.execute('SELECT id FROM spells')
    catalog_ids = {r[0] for r in cur.fetchall()}
    cur.execute("SELECT hidden_refs FROM spells WHERE has_hidden_formula=1")
    hidden_ref_ids = set()
    for (refs,) in cur.fetchall():
        hidden_ref_ids.update(int(x) for x in refs.split(',') if x.strip())
    neighbor_ids = set()
    for sid in catalog_ids:
        neighbor_ids.update(range(sid - 3, sid + 4))
    relevant_ids = catalog_ids | hidden_ref_ids | neighbor_ids
    print(f'Scoping spell_dbc_raw to {len(relevant_ids)} relevant IDs '
          f'({len(catalog_ids)} catalog + {len(hidden_ref_ids)} hidden_refs + neighbor buffer)')

    spell_rows = []
    id_struct = struct.Struct('<I')
    for rec in dbc['records']:
        if id_struct.unpack_from(rec, 0)[0] not in relevant_ids:
            continue
        p = parse_spell_record(rec, dbc['string_block'])
        effect_json = json.dumps({
            'Effect': p['Effect'], 'EffectBasePoints': p['EffectBasePoints'],
            'EffectDieSides': p['EffectDieSides'], 'EffectRealPointsPerLevel': p['EffectRealPointsPerLevel'],
            'EffectMechanic': p['EffectMechanic'], 'EffectImplicitTargetA': p['EffectImplicitTargetA'],
            'EffectImplicitTargetB': p['EffectImplicitTargetB'], 'EffectRadiusIndex': p['EffectRadiusIndex'],
            'EffectAura': p['EffectAura'], 'EffectAuraPeriod': p['EffectAuraPeriod'],
            'EffectAmplitude': p['EffectAmplitude'], 'EffectChainTargets': p['EffectChainTargets'],
            'EffectItemType': p['EffectItemType'], 'EffectMiscValue': p['EffectMiscValue'],
            'EffectMiscValueB': p['EffectMiscValueB'], 'EffectTriggerSpell': p['EffectTriggerSpell'],
            'EffectPointsPerCombo': p['EffectPointsPerCombo'], 'EffectBonusCoefficient': p['EffectBonusCoefficient'],
            'DurationIndex': p['DurationIndex'], 'RangeIndex': p['RangeIndex'], 'CastingTimeIndex': p['CastingTimeIndex'],
        })
        spell_rows.append((p['ID'], p['Name'], p['NameSubtext'], p['Description'], p['AuraDescription'],
                            p['Attributes'], p['AttributesEx'], p['SchoolMask'], effect_json,
                            os.path.basename(spell_archive)))
    cur.executemany('INSERT OR REPLACE INTO spell_dbc_raw VALUES (?,?,?,?,?,?,?,?,?,?)', spell_rows)
    print(f'spell_dbc_raw: {len(spell_rows)} rows (of {dbc["record_count"]} total in the client) '
          f'from {os.path.basename(spell_archive)}')

    # --- supporting tables ---------------------------------------------------
    for filename, (expected_fields, fields) in SUPPORT_TABLES.items():
        internal = f'DBFilesClient\\{filename}'
        hits = find_owning_archive(mpqs, internal, args.stormlib_dll)
        archive = pick_final_archive(hits, filename)
        table_name = 'dbc_' + filename[:-4].lower()
        cur.execute(f'DROP TABLE IF EXISTS {table_name}')
        if archive is None:
            print(f'{filename}: not found in any archive, skipping', file=sys.stderr)
            continue
        with MpqArchive(archive, args.stormlib_dll) as mpq:
            raw = mpq.read_file(internal)
        tdbc = load_dbc(raw)
        if tdbc['field_count'] < expected_fields:
            print(f'WARNING: {filename} field_count={tdbc["field_count"]} < expected {expected_fields}, '
                  f'skipping (schema mismatch, needs review)', file=sys.stderr)
            continue
        cols = ', '.join(f'{name.lower()} TEXT' if count > 1 else f'{name.lower()} INTEGER' for name, _, count in fields[1:])
        cur.execute(f'CREATE TABLE {table_name} (id INTEGER PRIMARY KEY, {cols}, source_archive TEXT)')
        rows = []
        for rec in tdbc['records']:
            p = parse_simple_record(rec, tdbc['string_block'], fields, expected_fields, tdbc['field_count'])
            vals = [p['ID']]
            for name, _, count in fields[1:]:
                v = p[name]
                vals.append(json.dumps(v) if isinstance(v, list) else v)
            vals.append(os.path.basename(archive))
            rows.append(tuple(vals))
        placeholders = ','.join('?' * (len(fields) + 1))
        cur.executemany(f'INSERT INTO {table_name} VALUES ({placeholders})', rows)
        print(f'{table_name}: {len(rows)} rows from {os.path.basename(archive)}')

    conn.commit()

    # --- validate before trusting any of the above further -------------------
    validate_known_spells(cur)

    # --- cross-reference has_hidden_formula (raw resolution rate) ------------
    cur.execute('SELECT id, hidden_refs FROM spells WHERE has_hidden_formula=1')
    rows = cur.fetchall()
    cur.execute('SELECT id FROM spell_dbc_raw')
    dbc_ids = {r[0] for r in cur.fetchall()}
    total_refs = resolved_refs = 0
    for _sid, hidden_refs in rows:
        for ref in hidden_refs.split(','):
            if not ref.strip():
                continue
            total_refs += 1
            if int(ref) in dbc_ids:
                resolved_refs += 1
    print(f'\nhas_hidden_formula=1 spells: {len(rows)}')
    print(f'hidden_refs total: {total_refs}, resolved against DBC: {resolved_refs} '
          f'({resolved_refs / total_refs * 100:.1f}%)' if total_refs else '(none)')

    # --- turn that resolution into actual spell_scaling rows -----------------
    resolve_hidden_formula_spells(cur)
    conn.commit()

    export_dbc_extract_json(cur)

    conn.close()


if __name__ == '__main__':
    main()
