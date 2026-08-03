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
- **Combat event parsing (`combat_log_parser.py`) is unverified against a real
  Ascension log** — it's built on the standard Blizzard log grammar, but
  Ascension's modified client could have field differences I can't check
  blind. First real log you send: I'll confirm field alignment and fix
  anything that's off.

## Output
`parse_log.py` writes `<logname>.summary.json` with:
- `crit_rate_by_source_ability` — per ability/source crit%
- `avoidance_breakdown` — miss/dodge/parry/resist counts per ability/source
- `builds` — every gear/talent/spec snapshot ALC captured, decoded

Just upload the raw `.txt` in chat going forward and I'll run this directly —
you don't need to run it yourself unless you want to.
