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
import datetime
import json
import os
import re
import sqlite3
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from config import (  # noqa: E402
    DBC_ASCENSION_EXTRACT_JSON, DBC_EXTRACT_JSON, DB_PATH as _DB_PATH,
)
import season_config  # noqa: E402  - realm/season constants (3d A1)
from core.spells.text_extraction import SUBSPELL_REF_PAT  # noqa: E402

DB_PATH = str(_DB_PATH)  # ephemeral, gitignored

DEFAULT_DATA_PATH = r"E:\Ascension Launcher\resources\ascension-live\Data"
# Committed so the machine with the game client does not also need builds.db.
DEFAULT_SCOPE_FILE = (Path(__file__).resolve().parents[2] / "data" / "source"
                      / "dbc" / "extract_scope_observed_ids.json")
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
    # Added session 0a (Phase 0 Task 4a). Layout is stock 3.3.5a
    # (TrinityCore SkillLineAbilityEntry); Ascension has not changed the shape,
    # only the *contents* of SkillLine.dbc (see extract_skill_lines).
    'SkillLineAbility.dbc': (14, [('ID', 'u32', 1), ('SkillLine', 'u32', 1), ('Spell', 'u32', 1),
                                   ('RaceMask', 'u32', 1), ('ClassMask', 'u32', 1),
                                   ('ExcludeRace', 'u32', 1), ('ExcludeClass', 'u32', 1),
                                   ('MinSkillLineRank', 'u32', 1), ('SupercededBySpell', 'u32', 1),
                                   ('AcquireMethod', 'u32', 1), ('TrivialSkillLineRankHigh', 'u32', 1),
                                   ('TrivialSkillLineRankLow', 'u32', 1)]),
}


# ---------------------------------------------------------------------------
# CharacterAdvancement.dbc - Ascension's OWN card catalog (Phase 0 session 0a).
#
# Not a Blizzard table: no TrinityCore struct exists for it, so the layout below
# was reverse-engineered against known anchors and is recorded here rather than
# cited. Method and evidence: RECON_FINDINGS.md Task 5.
#
#   * The record ID is the `entry_id` that ascensionlogs.gg armory captures and
#     the in-game tooltip's "CharacterAdvancement ID" both use. It is NOT a
#     spellId and must never be joined to one directly.
#   * Slots 5..9 are a SpellRank[5] array: the spellId per card rank. Talents
#     fill 2/3/5 of them; ability cards fill only slot 5 (the game resolves an
#     ability's spell *rank* by character level instead - see resolve_rank_lines).
#
# Confidence: slots 0/1/2/3/5-9/16/20/24/47/64/65 are anchored on 10,231 records
# and cross-checked against 1,054 crawled entry_ids (100% resolved, 660/660 name
# agreement). The remaining int slots are stored verbatim in `raw_ints_json`
# rather than guessed at.
# ---------------------------------------------------------------------------
# Slot 121 is a packed 4-byte availability field (decoded session 0a). Byte 2
# ((v >> 8) & 0xFF) separates the currently-playable card pool from everything else.
# Evidence, four independent lines - none of them documentation, so treat this as a
# strong empirical rule rather than a certainty:
#   1. all 1,054 entry_ids observed on live Darkmoon characters have byte2 == 1;
#      not one of the 5,705 byte2==0 records has ever been seen
#   2. it keeps 3,129 records, within 3.0% of BisBeard's independently-maintained
#      S10 card count (3,226) and close to the catalog export's 3,061
#   3. semantics: the kept set contains all five Paths by name; the excluded set is
#      full of retail WotLK class abilities (Ferocious Bite, Lava Burst, Ignite,
#      Improved Fireball) that are not part of the classless card pool
#   4. it resolves the duplicate-name trap structurally - "Holy Power" and
#      "Titan's Grip" each appear three times in this table, once per byte2 group,
#      and exactly one of each is byte2 == 1
# ⚠ Do NOT read byte2 as meaning "Darkmoon" specifically. Only Darkmoon data exists
# to test against; it could equally mean current-season, or classless mode. The
# honest label is "the currently-playable pool". 97 cards of BisBeard's count are
# unaccounted for and that gap is unexplained.
CA_POOL_SLOT = 121

CA_SLOTS = {
    'ca_type': 1, 'prereq_1': 2, 'prereq_2': 3,
    'rarity_a': 16, 'rarity_b': 20, 'rarity_c': 24,
    'rarity_a_n': 17, 'rarity_b_n': 21, 'rarity_c_n': 25,
    'req_level_a': 26, 'req_level_b': 27, 'req_level_c': 28,
    'category_a': 32, 'category_b': 33,
    'name': 47, 'icon': 64, 'description': 65,
}
CA_STRING_SLOTS = {1, 16, 20, 24, 47, 64, 65}
CA_RANK_SLOTS = (5, 6, 7, 8, 9)
# Class names Ascension uses as SkillLine.dbc names (verified session 0a: the
# client's skill lines are renamed to classes, e.g. line 26 is "Warrior", not
# retail's "Arcane"). 'Conquest of Azeroth' is a real line but not a class.
CLASS_SKILL_LINES = {'Warrior', 'Paladin', 'Hunter', 'Rogue', 'Priest',
                     'Death Knight', 'Shaman', 'Mage', 'Warlock', 'Druid'}


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
# and run it through THE SAME extraction build_index.py uses on directly-visible
# tooltips. 1c: this used to duplicate a narrower private copy of the regexes;
# now it delegates to core.spells.text_extraction so the two extractors cannot
# drift (the 1c widening — compound sums, school-suffixed tokens, lowercase —
# takes effect here at the next --with-dbc client re-extraction).
# ---------------------------------------------------------------------------
from core.spells.text_extraction import extract_scaling as _extract_scaling  # noqa: E402


def extract_scaling_terms(text):
    terms, _hidden, _pct = _extract_scaling(text, spell_id=-1, valid_ids=())
    return set(terms)


def ensure_spell_scaling_source_column(cur):
    cur.execute("PRAGMA table_info(spell_scaling)")
    if 'source' not in {row[1] for row in cur.fetchall()}:
        cur.execute("ALTER TABLE spell_scaling ADD COLUMN source TEXT")
        cur.execute("UPDATE spell_scaling SET source='export_tooltip' WHERE source IS NULL")


def resolve_hidden_formula_spells(cur):
    ensure_spell_scaling_source_column(cur)

    # ⚠ Idempotency (fixed session 0a). This step clears its own rows and then
    # re-derives them - but it ALSO clears has_hidden_formula on every spell it
    # resolves (below), so on a second run those spells no longer appear in the
    # `has_hidden_formula=1` target set. The delete therefore threw away all 113
    # previously-resolved rows and re-derived none: running this script twice in
    # a row silently emptied spell_scaling of every dbc_hidden_formula row.
    # (INDEX_GUIDE v3's claim that "the resolver already runs the full list every
    # invocation, not incremental" was wrong, and this is how.)
    # Fix: re-target anything that either is still flagged OR already has rows
    # from a previous run, so the delete is always followed by a re-derive.
    cur.execute("SELECT DISTINCT spell_id FROM spell_scaling WHERE source='dbc_hidden_formula'")
    previously_resolved = [r[0] for r in cur.fetchall()]
    cur.execute("DELETE FROM spell_scaling WHERE source='dbc_hidden_formula'")

    cur.execute('SELECT id, hidden_refs FROM spells WHERE has_hidden_formula=1')
    targets = cur.fetchall()
    if previously_resolved:
        ph = ','.join('?' * len(previously_resolved))
        cur.execute(f'SELECT id, hidden_refs FROM spells WHERE id IN ({ph})', previously_resolved)
        seen = {t[0] for t in targets}
        targets += [t for t in cur.fetchall() if t[0] not in seen]
        print(f'(re-targeting {len(previously_resolved)} spells resolved on a previous run '
              f'so re-running stays idempotent)')
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
                # 3d C1 — provenance stated per row. This writer DOES know the
                # sub-spell id (`rid`), unlike load_extract.py replaying the
                # exported payload, so the evidence_ref names it exactly.
                # source_tier is 'dbc_description_text', not the tier-4
                # 'dbc_numeric_field': this is regex extraction from a
                # description string, and labelling it tier 4 would borrow the
                # authority of a numeric field for a tooltip template.
                new_rows.append((
                    sid, term_type, coeff, 'dbc_hidden_formula',
                    'dbc_description_text',
                    f'dbc:Spell.dbc:{rid}:description'
                    f' (hidden sub-spell referenced by {sid}\'s tooltip)',
                    'inferred', season_config.REALM, season_config.SEASON))
            # surprise check: does an existing confirmed_facts row already
            # assert a coefficient for one of these spells that now conflicts?
            cur.execute('SELECT name FROM spells WHERE id=?', (sid,))
            name_row = cur.fetchone()
            name = name_row[0] if name_row else str(sid)
            for rid, term_type, coeff in found_terms:
                cur.execute('SELECT name FROM spell_dbc_raw WHERE id=?', (rid,))
                sub_row = cur.fetchone()
                sub_name = sub_row[0] if sub_row else str(rid)
                # ⚠ Word-boundary, not substring (tightened session 0a). A bare
                # `sub_name in fact` on a short name like "Mutilate" matched dozens
                # of unrelated facts, printing a spell x fact cross-product that
                # buried anything genuinely surprising.
                name_re = re.compile(r'\b' + re.escape(sub_name) + r'\b') if sub_name else None
                for fact in all_facts:
                    if name_re and name_re.search(fact) and ('%' in fact or 'assumed' in fact.lower()):
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

    cur.executemany(
        'INSERT INTO spell_scaling (spell_id, term_type, coefficient, source, '
        'source_tier, evidence_ref, confidence, realm, season) '
        'VALUES (?,?,?,?,?,?,?,?,?)', new_rows)

    print(f'\nhas_hidden_formula spells resolved into spell_scaling: {resolved_count} / {len(targets)}')
    print(f'left flagged (no SP/AP/RAP/weapon term found in hidden sub-spell text): {len(unresolved)}')
    if surprises:
        seen_pairs = set()
        print(f'\nSURPRISING resolutions (conflict with an existing confirmed_facts entry):')
        shown = 0
        for s in surprises:
            key = (s['spell_id'], s['hidden_ref_id'])
            if key in seen_pairs:
                continue
            seen_pairs.add(key)
            if shown >= 15:
                continue
            shown += 1
            print(f"  - spell {s['spell_id']} ({s['spell_name']}) -> hidden ref {s['hidden_ref_id']} "
                  f"({s['hidden_ref_name']}): resolved {s['resolved_term']}={s['resolved_coefficient']}")
            print(f"    existing fact: {s['conflicting_fact'][:200]}")
        if len(seen_pairs) > shown:
            print(f'  ... and {len(seen_pairs) - shown} more spell/ref pairs '
                  f'({len(surprises)} fact matches total)')
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
    # SELECT *, not a hardcoded column list. This export is the ONLY way a session
    # without the game client sees spell_dbc_raw, so a column added to the table and
    # forgotten here would be invisible everywhere except this machine - which is
    # exactly what happened to the fingerprint scalars added in Phase 1 T1.
    cur.execute('SELECT * FROM spell_dbc_raw')
    cols = [d[0] for d in cur.description]
    spell_dbc_raw = [dict(zip(cols, row)) for row in cur.fetchall()]

    support_tables = {}
    # dbc_spellitemenchantment (3l): created unconditionally by its extractor,
    # so this SELECT cannot crash even when the archive was missing — the
    # export then carries an honest empty list rather than dying.
    for table_name in ('dbc_spellduration', 'dbc_spellrange', 'dbc_spellcasttimes',
                        'dbc_spellradius', 'dbc_talent', 'dbc_talenttab',
                        'dbc_spellitemenchantment'):
        cur.execute(f'SELECT * FROM {table_name}')
        table_cols = [d[0] for d in cur.description]
        support_tables[table_name] = [dict(zip(table_cols, row)) for row in cur.fetchall()]

    cur.execute("SELECT spell_id, term_type, coefficient FROM spell_scaling WHERE source='dbc_hidden_formula'")
    hidden_formula_scaling = [{'spell_id': r[0], 'term_type': r[1], 'coefficient': r[2]} for r in cur.fetchall()]

    payload = {
        # 2e T4: the extract-staleness sweep compares this against the latest
        # Darkmoon patch date — without it the extracts carry no date at all and
        # staleness is only guessable from file mtimes, which git resets.
        '_extracted_at': datetime.datetime.now().isoformat(timespec='seconds'),
        'spell_dbc_raw': spell_dbc_raw,
        'support_tables': support_tables,
        'hidden_formula_scaling': hidden_formula_scaling,
    }
    DBC_EXTRACT_JSON.write_text(json.dumps(payload, indent=1), encoding='utf-8')
    print(f'\nExported {len(spell_dbc_raw)} spell_dbc_raw rows + '
          f'{sum(len(v) for v in support_tables.values())} support-table rows + '
          f'{len(hidden_formula_scaling)} hidden-formula scaling rows to {DBC_EXTRACT_JSON}')


def spell_slot_index(field_name):
    """Slot offset of a named Spell.dbc field, derived from SPELL_FIELDS itself so
    it can't drift out of sync with parse_spell_record."""
    pos = 0
    for name, kind, count in SPELL_FIELDS:
        if name == field_name:
            return pos
        pos += 17 if kind == 'strblock' else count
    raise KeyError(field_name)


def scan_spell_rank_index(dbc):
    """Cheap pre-pass over the FULL Spell.dbc (209k records): just the fields needed
    to group rank lines. Avoids parse_spell_record's full 234-slot unpack per row."""
    i_id = spell_slot_index('ID')
    i_name = spell_slot_index('Name')
    i_sub = spell_slot_index('NameSubtext')
    i_level = spell_slot_index('SpellLevel')
    i_school = spell_slot_index('SchoolMask')
    i_cd = spell_slot_index('RecoveryTime')
    i_cast = spell_slot_index('CastingTimeIndex')
    i_radius = spell_slot_index('EffectRadiusIndex')
    i_effect = spell_slot_index('Effect')
    sb = dbc['string_block']
    out = {}
    n = dbc['record_size'] // 4
    for rec in dbc['records']:
        u = struct.unpack_from(f'<{n}I', rec, 0)
        sub = read_cstr(sb, u[i_sub])
        rank = None
        if sub.startswith('Rank '):
            tail = sub.split()[-1]
            rank = int(tail) if tail.isdigit() else None
        out[u[i_id]] = {
            'name': read_cstr(sb, u[i_name]),
            'rank_text': sub,
            'rank': rank,
            'spell_level': u[i_level],
            # mechanical fingerprint - PHASE_0 1d's hard rule: never relate two
            # ids by name alone.
            'fingerprint': (u[i_school], u[i_cd], u[i_radius], u[i_cast],
                            u[i_effect], u[i_effect + 1], u[i_effect + 2]),
        }
    return out


def build_rank_lines(rank_index, skill_of):
    """Group rank-numbered spells into lines keyed by (name, skill lines, fingerprint).

    Returns {line_key: [spell_id, ...]}. A line with one member is still a line.
    """
    lines = {}
    for sid, info in rank_index.items():
        if info['rank'] is None or not info['name']:
            continue
        key = (info['name'], tuple(sorted(skill_of.get(sid, ()))), info['fingerprint'])
        lines.setdefault(key, []).append(sid)
    return lines


def load_skill_line_map(mpqs, dll_path):
    """{spell_id: {skill_line_id, ...}} straight from SkillLineAbility.dbc.

    Read directly (rather than from the dbc_skilllineability table) because rank
    grouping has to happen before spell_dbc_raw is scoped, which is before the
    support tables are written.
    """
    internal = 'DBFilesClient\\SkillLineAbility.dbc'
    archive = pick_final_archive(find_owning_archive(mpqs, internal, dll_path),
                                'SkillLineAbility.dbc')
    if archive is None:
        print('SkillLineAbility.dbc: not found; rank lines will group on name alone',
              file=sys.stderr)
        return {}
    with MpqArchive(archive, dll_path) as mpq:
        dbc = load_dbc(mpq.read_file(internal))
    n = dbc['record_size'] // 4
    out = {}
    for rec in dbc['records']:
        u = struct.unpack_from(f'<{n}I', rec, 0)
        out.setdefault(u[2], set()).add(u[1])
    return out


def extract_skill_lines(cur, mpqs, dll_path):
    """SkillLine.dbc -> dbc_skill_line, and the derived per-spell class resolution.

    ⚠ Ascension has RENAMED the skill lines to class names (line 26 is "Warrior",
    not retail's "Arcane"), and sets ClassMask to 512 (its own classless "Hero"
    class) on ~10k rows, which makes ClassMask useless for this. The skill line's
    NAME is what carries the class. Verified session 0a against 387 existing
    class_origin rows (382 agree) and 7/7 of primer §4's proof cases.
    """
    internal = 'DBFilesClient\\SkillLine.dbc'
    archive = pick_final_archive(find_owning_archive(mpqs, internal, dll_path), 'SkillLine.dbc')
    if archive is None:
        print('SkillLine.dbc: not found in any archive, skipping', file=sys.stderr)
        return {}
    with MpqArchive(archive, dll_path) as mpq:
        dbc = load_dbc(mpq.read_file(internal))
    sb = dbc['string_block']
    n = dbc['record_size'] // 4
    names, cats = {}, {}
    for rec in dbc['records']:
        u = struct.unpack_from(f'<{n}I', rec, 0)
        cats[u[0]] = u[1]
        # The name is the first slot after the category that reads back as a
        # printable string; the display-name column moves between builds, so it
        # is discovered rather than hardcoded.
        for idx in range(2, n):
            s = read_cstr(sb, u[idx])
            if s and len(s) > 1 and s.isprintable():
                names[u[0]] = s
                break
    cur.execute('DROP TABLE IF EXISTS dbc_skill_line')
    cur.execute('CREATE TABLE dbc_skill_line (id INTEGER PRIMARY KEY, name TEXT, '
                'category INTEGER, is_class_line INTEGER, source_archive TEXT)')
    cur.executemany('INSERT INTO dbc_skill_line VALUES (?,?,?,?,?)',
                    [(k, names.get(k), cats.get(k),
                      1 if names.get(k) in CLASS_SKILL_LINES else 0,
                      os.path.basename(archive)) for k in cats])
    print(f'dbc_skill_line: {len(cats)} rows from {os.path.basename(archive)} '
          f'({sum(1 for k in cats if names.get(k) in CLASS_SKILL_LINES)} class lines)')
    return names


def extract_spell_class(cur, skill_names):
    """Derive dbc_spell_class from dbc_skilllineability x dbc_skill_line."""
    cur.execute('SELECT spell, skillline FROM dbc_skilllineability')
    per_spell = {}
    for spell, line in cur.fetchall():
        nm = skill_names.get(line)
        if nm in CLASS_SKILL_LINES:
            per_spell.setdefault(spell, set()).add(nm)
    cur.execute('DROP TABLE IF EXISTS dbc_spell_class')
    cur.execute('CREATE TABLE dbc_spell_class (spell_id INTEGER PRIMARY KEY, class_name TEXT, '
                'ambiguous INTEGER, all_classes TEXT)')
    rows = [(sid, sorted(c)[0] if len(c) == 1 else None, 0 if len(c) == 1 else 1,
             ','.join(sorted(c))) for sid, c in per_spell.items()]
    cur.executemany('INSERT INTO dbc_spell_class VALUES (?,?,?,?)', rows)
    single = sum(1 for r in rows if not r[2])
    cur.execute('SELECT count(*) FROM spells s JOIN dbc_spell_class c ON c.spell_id=s.id '
                'WHERE c.ambiguous=0')
    print(f'dbc_spell_class: {len(rows)} spells ({single} unambiguous); '
          f'{cur.fetchone()[0]} of them are catalog entries')


def extract_character_advancement(cur, mpqs, dll_path):
    """CharacterAdvancement.dbc -> dbc_character_advancement. See CA_SLOTS above."""
    internal = 'DBFilesClient\\CharacterAdvancement.dbc'
    archive = pick_final_archive(find_owning_archive(mpqs, internal, dll_path),
                                'CharacterAdvancement.dbc')
    if archive is None:
        print('CharacterAdvancement.dbc: not found in any archive, skipping', file=sys.stderr)
        return
    with MpqArchive(archive, dll_path) as mpq:
        dbc = load_dbc(mpq.read_file(internal))
    sb = dbc['string_block']
    n = dbc['record_size'] // 4
    cur.execute('DROP TABLE IF EXISTS dbc_character_advancement')
    cols = ', '.join(f'{k} TEXT' if v in CA_STRING_SLOTS else f'{k} INTEGER'
                     for k, v in CA_SLOTS.items())
    cur.execute(f'CREATE TABLE dbc_character_advancement (ca_id INTEGER PRIMARY KEY, {cols}, '
                'spell_rank_1 INTEGER, spell_rank_2 INTEGER, spell_rank_3 INTEGER, '
                'spell_rank_4 INTEGER, spell_rank_5 INTEGER, max_rank INTEGER, '
                'pool_flags_raw INTEGER, in_current_pool INTEGER, '
                'raw_ints_json TEXT, source_archive TEXT)')
    rows = []
    for rec in dbc['records']:
        u = struct.unpack_from(f'<{n}I', rec, 0)
        vals = [u[0]]
        for _k, slot in CA_SLOTS.items():
            vals.append(read_cstr(sb, u[slot]) if slot in CA_STRING_SLOTS else u[slot])
        ranks = [u[s] for s in CA_RANK_SLOTS]
        vals.extend(ranks)
        vals.append(sum(1 for r in ranks if r))
        pool_raw = u[CA_POOL_SLOT]
        vals.append(pool_raw)
        vals.append(1 if ((pool_raw >> 8) & 0xFF) == 1 else 0)
        # every remaining non-zero int slot, so nothing is lost to a wrong guess
        known = set(CA_SLOTS.values()) | set(CA_RANK_SLOTS) | {0, CA_POOL_SLOT}
        vals.append(json.dumps({str(i): u[i] for i in range(n)
                                if i not in known and u[i] not in (0, 0xFFFFFFFF)}))
        vals.append(os.path.basename(archive))
        rows.append(tuple(vals))
    ph = ','.join('?' * len(rows[0]))
    cur.executemany(f'INSERT INTO dbc_character_advancement VALUES ({ph})', rows)
    cur.execute('SELECT count(*) FROM dbc_character_advancement WHERE spell_rank_1 IN '
                '(SELECT id FROM spells)')
    in_cat = cur.fetchone()[0]
    cur.execute('SELECT count(*) FROM dbc_character_advancement WHERE in_current_pool=1')
    print(f'dbc_character_advancement: {len(rows)} rows from {os.path.basename(archive)} '
          f'({in_cat} whose rank-1 spell is a catalog entry; '
          f'{cur.fetchone()[0]} flagged in_current_pool)')


def extract_gt_tables(cur, mpqs, dll_path):
    """The gt* combat-rating conversion tables Phase 2's engine needs.

    These have no ID column - the ROW INDEX is the key (class-major, level-minor
    for the per-class tables). Stored raw; interpretation belongs to Phase 2.
    """
    gt_files = ['gtCombatRatings.dbc', 'gtChanceToMeleeCrit.dbc', 'gtChanceToMeleeCritBase.dbc',
                'gtChanceToSpellCrit.dbc', 'gtChanceToSpellCritBase.dbc',
                'gtRegenMPPerSpt.dbc', 'gtRegenHPPerSpt.dbc', 'gtOCTRegenMP.dbc',
                'gtOCTRegenHP.dbc', 'gtNPCManaCostScaler.dbc']
    cur.execute('DROP TABLE IF EXISTS dbc_gt_tables')
    cur.execute('CREATE TABLE dbc_gt_tables (table_name TEXT, row_index INTEGER, '
                'value REAL, source_archive TEXT, PRIMARY KEY (table_name, row_index))')
    total = 0
    for filename in gt_files:
        internal = f'DBFilesClient\\{filename}'
        archive = pick_final_archive(find_owning_archive(mpqs, internal, dll_path), filename)
        if archive is None:
            print(f'{filename}: not found, skipping', file=sys.stderr)
            continue
        with MpqArchive(archive, dll_path) as mpq:
            dbc = load_dbc(mpq.read_file(internal))
        name = filename[:-4]
        rows = []
        for idx, rec in enumerate(dbc['records']):
            # single-column float tables; some builds carry a leading id column
            vals = struct.unpack_from(f'<{dbc["record_size"] // 4}f', rec, 0)
            rows.append((name, idx, vals[-1], os.path.basename(archive)))
        cur.executemany('INSERT INTO dbc_gt_tables VALUES (?,?,?,?)', rows)
        total += len(rows)
    print(f'dbc_gt_tables: {total} rows across {len(gt_files)} tables')


# ---------------------------------------------------------------------------
# SpellItemEnchantment.dbc (session 3l, D2). The route to enchant-DELIVERED
# damage: Consecrated Holy Weapon (200818) decodes a nominal flat of 1 in its
# own Spell.dbc record and db.ascension.gg independently states `Value: 1` —
# two sources agreeing on a nominal 1 prove the magnitude is NOT in the spell's
# own record (primer v31 §2). The enchant record is where the delivery link
# lives: `effect_args` carries the proc-spell ids an enchant fires.
#
# Stock 3.3.5a layout (TrinityCore DBCStructure.h SpellItemEnchantmentEntry /
# wowdev WDBC docs), 38 slots:
#   0 ID | 1 Charges | 2-4 Effect[3] | 5-7 EffectPointsMin[3]
#   8-10 EffectPointsMax[3] | 11-13 EffectArg[3] | 14-29 Name_lang[16]
#   30 NameFlags | 31 ItemVisual | 32 Flags | 33 SrcItemID | 34 ConditionID
#   35 RequiredSkillID | 36 RequiredSkillRank | 37 MinLevel
# ---------------------------------------------------------------------------
ENCHANT_FIELD_COUNT = 38
ENCHANT_NUMERIC_PREFIX = 14      # slots 0-13: everything load-bearing is here


def parse_enchant_record(record_bytes, string_block, field_count):
    """One SpellItemEnchantment record -> dict, or None if unparseable.

    Kept as a pure function (bytes in, dict out) so the client-less harness can
    exercise it on synthetic records — this is exactly the class of owner-gated
    code the 3b lesson is about: a path only the --with-dbc run executes can
    stay broken for sessions while every routine rebuild reports green.

    Honest boundary: if the client's field_count is not the stock 38, only the
    numeric prefix (slots 0-13) is trusted — the string offsets and trailing
    scalars are layout-dependent and are returned as None rather than guessed.
    """
    if field_count < ENCHANT_NUMERIC_PREFIX:
        return None
    slots = struct.unpack_from(f'<{field_count}I', record_bytes, 0)
    slots_i = struct.unpack_from(f'<{field_count}i', record_bytes, 0)
    out = {
        'id': slots[0],
        'charges': slots[1],
        'effect_types': list(slots[2:5]),
        # EffectPointsMin can legitimately be negative (i32); max/arg likewise.
        'amounts_min': list(slots_i[5:8]),
        'amounts_max': list(slots_i[8:11]),
        'effect_args': list(slots[11:14]),
        'description': None, 'item_visual': None, 'flags': None,
        'src_item_id': None, 'condition_id': None, 'required_skill_id': None,
        'required_skill_rank': None, 'min_level': None,
    }
    if field_count == ENCHANT_FIELD_COUNT:
        # Loc block: enUS is slot 14; fall back to the first non-empty locale.
        desc = read_cstr(string_block, slots[14])
        if not desc:
            for loc in range(15, 30):
                desc = read_cstr(string_block, slots[loc])
                if desc:
                    break
        out.update({
            'description': desc or None,
            'item_visual': slots[31], 'flags': slots[32],
            'src_item_id': slots[33], 'condition_id': slots[34],
            'required_skill_id': slots[35], 'required_skill_rank': slots[36],
            'min_level': slots[37],
        })
    return out


def extract_spell_item_enchantment(cur, mpqs, dll_path):
    """SpellItemEnchantment.dbc -> dbc_spellitemenchantment (all rows, unscoped
    — the table is a few thousand records, and enchant ids arrive from item
    strings and buff captures, not from any catalog scope rule).

    The table is created UNCONDITIONALLY so export_dbc_extract_json can always
    SELECT from it: a missing archive leaves an empty table plus a loud warning
    (a guard that cannot run must say so), never a crash at export time.
    """
    cur.execute('DROP TABLE IF EXISTS dbc_spellitemenchantment')
    cur.execute('''CREATE TABLE dbc_spellitemenchantment (
        id INTEGER PRIMARY KEY, charges INTEGER,
        effect_types_json TEXT, amounts_min_json TEXT, amounts_max_json TEXT,
        effect_args_json TEXT, description TEXT,
        item_visual INTEGER, flags INTEGER, src_item_id INTEGER,
        condition_id INTEGER, required_skill_id INTEGER,
        required_skill_rank INTEGER, min_level INTEGER, source_archive TEXT)''')
    internal = 'DBFilesClient\\SpellItemEnchantment.dbc'
    archive = pick_final_archive(find_owning_archive(mpqs, internal, dll_path),
                                 'SpellItemEnchantment.dbc')
    if archive is None:
        print('⚠ SpellItemEnchantment.dbc: NOT FOUND in any archive — '
              'dbc_spellitemenchantment is EMPTY and the enchant-delivered '
              'damage ask (200818) stays blocked', file=sys.stderr)
        return
    with MpqArchive(archive, dll_path) as mpq:
        dbc = load_dbc(mpq.read_file(internal))
    if dbc['field_count'] != ENCHANT_FIELD_COUNT:
        print(f'⚠ SpellItemEnchantment.dbc field_count={dbc["field_count"]} != '
              f'stock 3.3.5a {ENCHANT_FIELD_COUNT}: trusting the numeric prefix '
              f'(slots 0-13) only; description/trailing scalars stored as NULL',
              file=sys.stderr)
    rows, weird_types = [], 0
    for rec in dbc['records']:
        p = parse_enchant_record(rec, dbc['string_block'], dbc['field_count'])
        if p is None:
            continue
        # Layout smoke check: stock enchant effect types are 0..8. A slot
        # misalignment would land spell ids / amounts here, so a large share
        # of out-of-range values means the parse is reading the wrong slots.
        weird_types += sum(1 for t in p['effect_types'] if t > 16)
        rows.append((p['id'], p['charges'],
                     json.dumps(p['effect_types']), json.dumps(p['amounts_min']),
                     json.dumps(p['amounts_max']), json.dumps(p['effect_args']),
                     p['description'], p['item_visual'], p['flags'],
                     p['src_item_id'], p['condition_id'],
                     p['required_skill_id'], p['required_skill_rank'],
                     p['min_level'], os.path.basename(archive)))
    cur.executemany('INSERT OR REPLACE INTO dbc_spellitemenchantment VALUES '
                    '(' + ','.join('?' * 15) + ')', rows)
    total_type_slots = max(1, 3 * len(rows))
    weird_pct = 100.0 * weird_types / total_type_slots
    print(f'dbc_spellitemenchantment: {len(rows)} rows from '
          f'{os.path.basename(archive)} (field_count={dbc["field_count"]}, '
          f'effect-type slots >16: {weird_pct:.1f}% — near 0% expected; '
          f'a large value means the layout guess is WRONG, do not trust)')
    # The ask that drove this extraction, surfaced in the run output so the
    # owner's pasted console is itself the proof it landed (or did not).
    for probe in (23387,):
        row = cur.execute('SELECT effect_types_json, amounts_min_json, '
                          'amounts_max_json, effect_args_json, description '
                          'FROM dbc_spellitemenchantment WHERE id=?',
                          (probe,)).fetchone()
        if row:
            print(f'  enchant {probe}: types={row[0]} min={row[1]} max={row[2]} '
                  f'args={row[3]} desc={(row[4] or "")[:80]!r}')
        else:
            print(f'  ⚠ enchant {probe} (Consecrated Weapon, calib 2e) NOT in '
                  f'the client table — the 200818 ask needs a different route')


def extract_rank_lines(cur, rank_index, rank_lines):
    """dbc_spell_rank: which spell ids form a rank line, and each one's level gate.

    This is what makes "which rank does a level-60 character actually cast" a query
    instead of a guess: the answer is the highest rank in the line whose spell_level
    is <= the character's level.
    """
    cur.execute('DROP TABLE IF EXISTS dbc_spell_rank')
    cur.execute('CREATE TABLE dbc_spell_rank (spell_id INTEGER PRIMARY KEY, line_id INTEGER, '
                'name TEXT, rank INTEGER, rank_text TEXT, spell_level INTEGER, line_size INTEGER)')
    rows = []
    for line_id, (key, ids) in enumerate(sorted(rank_lines.items(), key=lambda kv: kv[0][0])):
        for sid in ids:
            info = rank_index[sid]
            rows.append((sid, line_id, info['name'], info['rank'], info['rank_text'],
                         info['spell_level'], len(ids)))
    cur.executemany('INSERT INTO dbc_spell_rank VALUES (?,?,?,?,?,?,?)', rows)
    multi = sum(1 for k, v in rank_lines.items() if len(v) > 1)
    print(f'dbc_spell_rank: {len(rows)} ranked spells in {len(rank_lines)} lines '
          f'({multi} multi-rank)')


def report_level_rank_gap(cur, rank_index, rank_lines, level=60):
    """How many catalog entries are stored at a rank a level-`level` character does
    not hold? (PHASE_0 Task 1's "report how many" ask.)"""
    line_of = {sid: key for key, ids in rank_lines.items() for sid in ids}
    cur.execute('SELECT id FROM spells')
    cat_ids = [r[0] for r in cur.fetchall()]
    cat_set = set(cat_ids)
    same = wrong = wrong_absent = 0
    for sid in cat_ids:
        key = line_of.get(sid)
        if key is None:
            continue
        sibs = [i for i in rank_lines[key] if rank_index[i]['spell_level'] <= level]
        if not sibs:
            continue
        best = max(sibs, key=lambda i: rank_index[i]['rank'])
        if best == sid:
            same += 1
        else:
            wrong += 1
            if best not in cat_set:
                wrong_absent += 1
    print(f'\nlevel-{level} rank check: {same + wrong} catalog entries sit in a rank line; '
          f'{same} are already the level-{level} id, {wrong} are NOT '
          f'({wrong_absent} of those level-{level} ids are absent from the catalog entirely)')


def export_ascension_extract_json(cur):
    """Ascension-specific DBC tables -> their own committed JSON.

    Separate from dbc-extract.json on purpose: that file is already ~14 MB and is
    rewritten wholesale each run, and these tables answer a different question
    (crosswalk / class / rank / rating conversion rather than raw spell text).
    Committed because they cannot be reproduced without the game client, which a
    future session may not have - same reasoning as the crawler's tier-1 split.
    """
    payload = {}
    for table in ('dbc_character_advancement', 'dbc_skill_line', 'dbc_skilllineability',
                  'dbc_spell_class', 'dbc_spell_rank', 'dbc_gt_tables'):
        try:
            cur.execute(f'SELECT * FROM {table}')
        except sqlite3.OperationalError:
            print(f'  (skipping {table}: not built this run)', file=sys.stderr)
            continue
        cols = [d[0] for d in cur.description]
        payload[table] = {'columns': cols, 'rows': cur.fetchall()}
    payload['_extracted_at'] = datetime.datetime.now().isoformat(timespec='seconds')
    path = DBC_ASCENSION_EXTRACT_JSON
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding='utf-8')
    # ⚠ Skip the `_`-prefixed metadata keys. `_extracted_at` is a STRING, and
    # summing len(v['rows']) across every value crashed on it with "string
    # indices must be integers" — after the file had already been written, so
    # the export succeeded and only the summary died, taking the whole rebuild
    # chain down with it. Latent since the stamp was added in 2e: nothing had
    # run --with-dbc between then and 2026-08-06. Same `_`-prefix convention
    # load_extract.py already uses on the reading side.
    tables = {k: v for k, v in payload.items() if not k.startswith('_')}
    total = sum(len(v['rows']) for v in tables.values())
    print(f'Exported {total} rows across {len(tables)} Ascension tables to {path} '
          f'({path.stat().st_size / 1e6:.1f} MB)')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--data-path', default=DEFAULT_DATA_PATH, help='Client Data folder')
    ap.add_argument('--stormlib-dll', default=DEFAULT_STORMLIB_DLL, help='Path to a built StormLib.dll')
    ap.add_argument('--db', default=DB_PATH)
    ap.add_argument('--observed-ids', default=None,
                    help='JSON file with an "ids" list of log-observed spell ids '
                         'to add to the extract scope (session 3b). Defaults to '
                         f'{DEFAULT_SCOPE_FILE.name} in data/derived/ if present.')
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
        -- Scalars added in Phase 1 T1 for core/spells/fingerprint.py. The hard rule
        -- ("never relate two ids by name - compare radius, COOLDOWN, cast type,
        -- RESOURCE COST and effect structure first") names fields that were only
        -- reachable inside effect_json or not stored at all. Cheap columns, and
        -- Phase 1 T4's spell_mechanics needs every one of them anyway.
        spell_level INTEGER,
        base_level INTEGER,
        -- Added session 1x. A flat magnitude scales as
        --   base_points + (min(level, max_level) - base_level) * per_level
        -- so WITHOUT max_level a level-scaled magnitude cannot be computed at all.
        -- Found the hard way on Hammer from the Heavens (282987): its live tooltip
        -- renders an INVERTED range (194 to 147), and that range is reproduced
        -- exactly only when the level bonus stops at 40 rather than 60.
        max_level INTEGER,
        recovery_time INTEGER,           -- cooldown, ms
        category_recovery_time INTEGER,  -- shared-category cooldown, ms
        casting_time_index INTEGER,
        duration_index INTEGER,
        range_index INTEGER,
        power_type INTEGER,              -- mana / rage / energy / runic / ...
        mana_cost INTEGER,
        mana_cost_pct INTEGER,
        proc_type_mask INTEGER,
        proc_chance INTEGER,
        proc_charges INTEGER,
        max_targets INTEGER,
        speed REAL,
        start_recovery_time INTEGER,     -- GCD, ms (0 = off-GCD)
        start_recovery_category INTEGER,
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
    # NB: keyed on hidden_refs being present, NOT on has_hidden_formula=1. The
    # flag is cleared once a spell resolves, so filtering on it dropped every
    # already-resolved spell's sub-spells out of scope on the next run - which
    # then un-resolved them. Same idempotency bug as resolve_hidden_formula_spells.
    cur.execute("SELECT hidden_refs FROM spells WHERE hidden_refs IS NOT NULL AND hidden_refs != ''")
    hidden_ref_ids = set()
    for (refs,) in cur.fetchall():
        hidden_ref_ids.update(int(x) for x in refs.split(',') if x.strip())
    neighbor_ids = set()
    for sid in catalog_ids:
        neighbor_ids.update(range(sid - 3, sid + 4))

    # Rank siblings (session 0a). The +/-3 neighbour buffer above is NOT enough:
    # rank ids are frequently non-contiguous (Winds of Winter R1 274121 -> R2
    # 274129), so the spell a level-60 character actually casts was being scoped
    # out of spell_dbc_raw entirely. That is how 274132 came to be recorded as
    # "absent from the client" - it never was.
    rank_index = scan_spell_rank_index(dbc)
    skill_of = load_skill_line_map(mpqs, args.stormlib_dll)
    rank_lines = build_rank_lines(rank_index, skill_of)
    sibling_ids = set()
    for ids in rank_lines.values():
        if catalog_ids.intersection(ids):
            sibling_ids.update(ids)

    # A rank sibling's OWN sub-spell refs (session 2c, gate G4). `hidden_ref_ids`
    # above comes from `spells.hidden_refs`, which is parsed from the EXPORT's
    # tooltip - and a sibling is by definition absent from the export, so it
    # contributes none. When the sibling's own record is a DUMMY that keeps its
    # magnitude in a sub-spell, that sub-spell was therefore never in scope and
    # the ability resolved to zero damage. Holy Shock is the live case: catalog
    # R1 (20473) points at 25912/25914, but the R4 a level-60 character casts
    # (20930) points at 25902/25903, and neither was ever extracted.
    #
    # 🛑 This reads a POINTER out of the description string, never a magnitude.
    # The magnitude still comes from the referenced spell's numeric fields. The
    # ban is on trusting description *numbers* (the Titanic Mutilate trap); a
    # `$25902s1` token is an id, and it is the only place the link is recorded.
    sibling_ref_ids = set()
    id_struct_scan = struct.Struct('<I')
    for rec in dbc['records']:
        if id_struct_scan.unpack_from(rec, 0)[0] not in sibling_ids:
            continue
        desc = parse_spell_record(rec, dbc['string_block']).get('Description') or ''
        for m in SUBSPELL_REF_PAT.finditer(desc):
            sibling_ref_ids.add(int(m.group(1)))
    sibling_ref_ids -= (catalog_ids | hidden_ref_ids | neighbor_ids | sibling_ids)

    # OBSERVED ids (session 3b). Every scope rule above starts from the
    # CATALOG, so a spell that real characters cast but no catalog card names
    # is invisible to this extract — which is exactly the 43% of crawled damage
    # the sim cannot model, and the reason 790 scraped coefficients have no
    # client-side check digit. The fix is the cheapest robust rule available:
    # seed the scope from spell ids that were actually OBSERVED dealing damage.
    #
    # The list is a committed artifact rather than a live DB query, so this
    # step does not require builds.db to exist on the machine holding the game
    # client. Regenerate it with tools/audit/build_extract_scope_request.py.
    observed_ids = set()
    scope_file = Path(args.observed_ids) if args.observed_ids else DEFAULT_SCOPE_FILE
    if scope_file.exists():
        try:
            observed_ids = {int(x) for x in
                            json.loads(scope_file.read_text(encoding='utf-8'))['ids']}
            print(f'Observed-id scope: {len(observed_ids)} ids from {scope_file.name}')
        except Exception as e:                       # noqa: BLE001
            print(f'⚠ could not read {scope_file}: {e} — continuing without it')
    else:
        print(f'⚠ {scope_file} not found — extract will NOT cover log-observed '
              f'ids (see session 3b; run tools/audit/build_extract_scope_request.py)')

    relevant_ids = (catalog_ids | hidden_ref_ids | neighbor_ids | sibling_ids
                    | sibling_ref_ids | observed_ids)
    print(f'Scoping spell_dbc_raw to {len(relevant_ids)} relevant IDs '
          f'({len(catalog_ids)} catalog + {len(hidden_ref_ids)} hidden_refs + '
          f'{len(sibling_ids)} rank siblings + {len(sibling_ref_ids)} rank-sibling '
          f'sub-spell refs + {len(observed_ids)} observed + neighbor buffer)')

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
            # Session 2c (T4b): the modifier fields. `EffectSpellClassMask` was
            # already PARSED here and simply never written out — the same shape
            # as v9's hardcoded-column-list gap, and it hid the one field that
            # says WHICH spells an amplifier talent reaches. 9 u32s, three per
            # effect slot; `SpellClassSet` (SpellFamilyName) below scopes them,
            # since a class mask only means anything within its family.
            'EffectSpellClassMask': p['EffectSpellClassMask'],
            'SpellClassSet': p['SpellClassSet'], 'SpellClassMask': p['SpellClassMask'],
        })
        spell_rows.append((p['ID'], p['Name'], p['NameSubtext'], p['Description'], p['AuraDescription'],
                            p['Attributes'], p['AttributesEx'], p['SchoolMask'], effect_json,
                            p['SpellLevel'], p['BaseLevel'], p['MaxLevel'], p['RecoveryTime'],
                            p['CategoryRecoveryTime'], p['CastingTimeIndex'], p['DurationIndex'],
                            p['RangeIndex'], p['PowerType'], p['ManaCost'], p['ManaCostPct'],
                            p['ProcTypeMask'], p['ProcChance'], p['ProcCharges'],
                            p['MaxTargets'], p['Speed'], p['StartRecoveryTime'],
                            p['StartRecoveryCategory'],
                            os.path.basename(spell_archive)))
    cur.executemany('INSERT OR REPLACE INTO spell_dbc_raw VALUES '
                    '(' + ','.join('?' * 28) + ')', spell_rows)
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

    # --- Ascension-specific tables (session 0a, Phase 0 Tasks 4a + 5) --------
    skill_names = extract_skill_lines(cur, mpqs, args.stormlib_dll)
    if skill_names:
        extract_spell_class(cur, skill_names)
    extract_character_advancement(cur, mpqs, args.stormlib_dll)
    extract_gt_tables(cur, mpqs, args.stormlib_dll)
    extract_spell_item_enchantment(cur, mpqs, args.stormlib_dll)
    extract_rank_lines(cur, rank_index, rank_lines)
    report_level_rank_gap(cur, rank_index, rank_lines)
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
    export_ascension_extract_json(cur)

    conn.close()


if __name__ == '__main__':
    main()
