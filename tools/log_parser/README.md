# Ascension log parser

Turns a `WoWCombatLog.txt` (with ALC installed) into structured JSON: combat
events (crit%, avoidance) plus every player build ALC captured in that log.

## Files
- `parse_log.py` — run this one. `python3 parse_log.py WoWCombatLog.txt`
- `combat_log_parser.py` — standard combat event parsing (damage/miss/etc.)
- `decode_alc.py` — decodes ALC's embedded `[[ALC_F_v1_c2_...]]` build payloads
- `d1_dict.bin` — required by `decode_alc.py`, keep it in the same folder

No installs needed — pure Python 3 standard library (`zlib`, `csv`, `re`, `json`).

## Confidence
- **Build decoding (`decode_alc.py`) is verified**, not guessed: built directly
  from ALC's own source and tested by round-tripping real payloads produced
  by the addon's own vendored libraries (base64 alphabet, dictionary-deflate,
  frame format, AceSerializer — all confirmed byte-exact, including special
  characters, floats, multi-chunk splits, and multi-record frames).
  **Also fixed 2026-08-03**: the chunk-reassembly regex was capturing the CSV
  field's closing `"` as part of the base64 payload (every `SPELL_CAST_FAILED`
  line quotes the fail-reason field), throwing off the base64 group-of-4
  length on nearly every frame. `decode_chunks` now strips it. Confirmed fix
  against a real log: 0 build records decoded before, 625 after.
- **Combat event parsing (`combat_log_parser.py`) — verified against a real
  Ascension log 2026-08-03, two field-layout bugs found and fixed:**
  1. This Ascension client's log grammar has only **6 base fields**
     (sourceGUID, sourceName, sourceFlags, destGUID, destName, destFlags) —
     it omits `sourceRaidFlags`/`destRaidFlags` entirely, unlike stock
     WotLK/retail logs. The old 8-field assumption silently shifted every
     field after sourceFlags by 2, producing garbage spellIds and a flatlined
     0% crit rate everywhere.
  2. The miss-type events are `SPELL_MISSED`/`SWING_MISSED` in this log, not
     `SPELL_MISS`/`SWING_MISS` — the old suffix/equality checks never matched,
     so `avoidance_breakdown` silently returned nothing for spell misses.
  Both confirmed by diffing raw log lines against parsed output; re-run
  produced real spellIds, non-zero crit rates matching expected melee/spell
  crit-table splits, and populated avoidance data. Treat this parser as
  confirmed for this log format going forward — re-verify only if Ascension
  changes their client's log grammar.

## Output
`parse_log.py` writes `<logname>.summary.json` with:
- `crit_rate_by_source_ability` — per ability/source crit%
- `avoidance_breakdown` — miss/dodge/parry/resist counts per ability/source
- `builds` — every gear/talent/spec snapshot ALC captured, decoded

Just upload the raw `.txt` in chat going forward and I'll run this directly —
you don't need to run it yourself unless you want to.
