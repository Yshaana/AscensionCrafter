#!/usr/bin/env python3
"""
Decode an inspects.nie.one export URL fragment into readable spec (ability +
talent) lists and equipped gear, cross-referenced against spell-export.json.

FORMAT (reverse-engineered + confirmed 2026-08-02 against a live in-game
inspect on player "Soytard" - spec 2 "Agility build" matched exactly,
including the one spell ID our catalog doesn't cover):

  <fragment> = <header> "!" <gear>

  <header> = "2" "." <season/level> "." <level> "." <n> "." <hex:name> "."
             <hex:realm> "." <hex:title> "." <unix_ts> "." <specs_blob>
    - <n> = active spec index (1-based, matches spec block order in
      <specs_blob> below) - i.e. which of the character's spec blocks is
      currently equipped/active in-game.

  <specs_blob> = <block> ("_" <block>)*     -- one block PER SPEC, in order

  <block> = <leader_token> "~" <30 base36 ability IDs, "."-joined>
                            "~" <25 base36 talent IDs, "."-joined>
    - leader_token's purpose is not yet identified (does not resolve to a
      spell ID) - possibly an internal spec row ID/checksum. Harmless to
      ignore for decoding purposes.
    - ability/talent counts (30 / 25) match the fixed slot budget per spec.

  <gear> = <item> ("_" <item>)*
  <item> = <slot_index> "~" <hex:item_string> "~" <hex:item_name> "~"
           <quality> "~" <slot_code> "~" <hex:icon_path>
    - item_string is classic-format "itemID:enchant:gem1:gem2:gem3:gem4:...:lvl"

Usage:
  python3 decode_inspect_export.py "<fragment after #new/>"
  (or edit RAW below and run with no args)
"""
import sys, json, re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from config import SPELL_EXPORT as SPELL_EXPORT_PATH  # noqa: E402

def load_spells():
    with open(SPELL_EXPORT_PATH) as f:
        data = json.load(f)
    return {s['id']: s for s in data['spells']}

def hexdec(s):
    try:
        return bytes.fromhex(s).decode('utf-8', errors='replace')
    except Exception:
        return f"<undecodable hex: {s}>"

def b36dec(s):
    try:
        return int(s, 36)
    except Exception:
        return None

def decode(raw, spells):
    header, gear_part = raw.strip().split('!', 1)
    fields = header.split('.', 8)
    version, season_level, level, n = fields[0:4]
    name = hexdec(fields[4])
    realm = hexdec(fields[5])
    title = hexdec(fields[6])
    ts = fields[7]
    specs_blob = fields[8]

    print(f"=== {name} ===")
    print(f"Realm: {realm}  |  Title/tag: {title}  |  Level: {level}  |  Export ts: {ts}")
    print(f"Active spec: {n}")
    print()

    # ---- Specs ----
    active_spec = int(n) if n.isdigit() else None
    blocks = specs_blob.split('_')
    for i, block in enumerate(blocks, start=1):
        parts = block.split('~')
        if len(parts) < 3:
            continue
        _leader, abil_str, tal_str = parts[0], parts[1], parts[2]
        abilities = [b36dec(t) for t in abil_str.split('.') if t]
        talents = [b36dec(t) for t in tal_str.split('.') if t]

        active_tag = ' (ACTIVE)' if i == active_spec else ''
        print(f"--- Spec {i}{active_tag} ({len(abilities)} abilities, {len(talents)} talents) ---")
        print("Abilities:")
        for v in abilities:
            s = spells.get(v)
            print(f"   #{v:<8} {s['name'] if s else '?'}" + (f" ({s['rank']})" if s and s.get('rank') else ""))
        print("Talents:")
        for v in talents:
            s = spells.get(v)
            print(f"   #{v:<8} {s['name'] if s else '?'}" + (f" ({s['rank']})" if s and s.get('rank') else ""))
        print()

    # ---- Gear ----
    items = [it for it in gear_part.split('_') if it]
    print(f"--- Gear ({len(items)} items) ---")
    for item in items:
        p = item.split('~')
        if len(p) < 6:
            continue
        slot_idx, item_str_hex, name_hex, quality, slot_code, icon_hex = p[:6]
        item_string = hexdec(item_str_hex)
        item_name = hexdec(name_hex)
        item_id = item_string.split(':')[0]
        print(f"   [{slot_idx}] {item_name}  (item #{item_id}, quality {quality}, slot {slot_code})")

if __name__ == '__main__':
    spells = load_spells()
    if len(sys.argv) > 1:
        raw = sys.argv[1]
    else:
        print(__doc__.strip().splitlines()[0])
        print('\nUsage: py ingest/addon/decode_inspect_export.py "<fragment after #new/>"')
        sys.exit(2)
    decode(raw, spells)
