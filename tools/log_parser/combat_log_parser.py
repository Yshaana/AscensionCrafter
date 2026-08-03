"""
Generic WoWCombatLog.txt line parser (WotLK 3.3.5-family log grammar).

NOTE ON CONFIDENCE: this is built from the public, stable Blizzard combat-log
format (the one WarcraftLogs/etc. have relied on for years) -- it is NOT
verified against an actual Ascension-produced log file, since Ascension's
modified client could add/reorder fields for its custom systems. Treat field
alignment as "predicted, not confirmed" until checked against a real sample
(see bottom of this file for the one-line sanity check to run on your first
real log). This is a different confidence tier than decode_alc.py, which was
validated against the addon's own real vendored libraries end-to-end.

Format per line:
    <timestamp>  <EVENT>,<sourceGUID>,"<sourceName>",<sourceFlags>,
                 <destGUID>,"<destName>",<destFlags>,<event-specific fields...>

CONFIRMED against a real 2026-08-03 Ascension log: this Ascension client's log
grammar omits sourceRaidFlags/destRaidFlags entirely (present in stock
WotLK/retail logs) -- 6 base fields, not 8. Also, the miss-type events are
SPELL_MISSED / SWING_MISSED, not SPELL_MISS / SWING_MISS. Both mismatches
silently misaligned every field after sourceFlags (spellId, amount, critical,
etc.) and zeroed out the miss-type lookups. Fixed 2026-08-03; see the git
history for this file if the field layout is ever in doubt again.
"""

import csv
import io
import re
from collections import defaultdict

TIMESTAMP_RE = re.compile(r"^(\d{1,2}/\d{1,2}\s+\d{2}:\d{2}:\d{2}\.\d{3})\s+(.*)$")

# Field layouts for the event suffixes we actually need for the current test
# queue. Base fields (event, sourceGUID, sourceName, sourceFlags,
# sourceRaidFlags, destGUID, destName, destFlags, destRaidFlags) are assumed
# common to all and split off before these.
SUFFIX_FIELDS = {
    "_DAMAGE": ["spellId", "spellName", "spellSchool", "amount", "overkill",
                "school", "resisted", "blocked", "absorbed", "critical",
                "glancing", "crushing"],
    "SWING_DAMAGE": ["amount", "overkill", "school", "resisted", "blocked",
                     "absorbed", "critical", "glancing", "crushing"],
    "_MISSED": ["spellId", "spellName", "spellSchool", "missType", "amountMissed"],
    "SWING_MISSED": ["missType", "amountMissed"],
    "_HEAL": ["spellId", "spellName", "spellSchool", "amount", "overhealing", "absorbed", "critical"],
    "_AURA_APPLIED": ["spellId", "spellName", "spellSchool", "auraType"],
    "_AURA_REMOVED": ["spellId", "spellName", "spellSchool", "auraType"],
    "_CAST_SUCCESS": ["spellId", "spellName", "spellSchool"],
    "_CAST_START": ["spellId", "spellName", "spellSchool"],
    "_INTERRUPT": ["spellId", "spellName", "spellSchool", "extraSpellId", "extraSpellName", "extraSpellSchool"],
}

BASE_FIELDS = ["sourceGUID", "sourceName", "sourceFlags",
               "destGUID", "destName", "destFlags"]


def _fields_for_event(event: str):
    if event == "SWING_DAMAGE":
        return SUFFIX_FIELDS["SWING_DAMAGE"]
    if event == "SWING_MISSED":
        return SUFFIX_FIELDS["SWING_MISSED"]
    for suffix, fields in SUFFIX_FIELDS.items():
        if suffix.startswith("_") and event.endswith(suffix):
            return fields
    return None  # unknown/unhandled event type -> caller keeps raw fields only


def _split_csv_line(rest: str):
    # WoW log lines are comma-separated with some quoted string fields
    # (player/creature names). csv module handles the quoting correctly.
    reader = csv.reader(io.StringIO(rest))
    return next(reader)


def parse_line(line: str):
    """
    Returns an event dict, or None for lines that aren't parseable combat
    log rows (headers, blank lines, or ALC's embedded-payload SPELL_CAST_FAILED
    rows -- those are handled separately by decode_alc.py).
    """
    m = TIMESTAMP_RE.match(line.strip())
    if not m:
        return None
    ts, rest = m.groups()

    # Route ALC embedded payloads away from normal parsing.
    if "ALC_F_v1_c2_" in rest:
        return None

    parts = _split_csv_line(rest)
    if len(parts) < 7:
        return None

    event = parts[0]
    base = dict(zip(["event"] + BASE_FIELDS, parts[0:7]))
    base["timestamp"] = ts

    field_names = _fields_for_event(event)
    extra = parts[7:]
    if field_names:
        for name, val in zip(field_names, extra):
            base[name] = val
    else:
        base["raw_extra"] = extra

    if "critical" in base:
        base["critical"] = base["critical"] not in ("nil", "", "0", "false")
    return base


def parse_log(path_or_lines, encoding="utf-8"):
    if isinstance(path_or_lines, (list, tuple)):
        lines = path_or_lines
    else:
        with open(path_or_lines, encoding=encoding, errors="ignore") as f:
            lines = f.readlines()
    events = []
    for line in lines:
        ev = parse_line(line)
        if ev:
            events.append(ev)
    return events


# ---------------------------------------------------------------------------
# Summary helpers aimed at the open test queue
# ---------------------------------------------------------------------------

def crit_rate_by_source_ability(events, source_name=None):
    """
    Per (sourceName, spellName or 'Melee') crit rate. Sorting this against
    known melee/spell crit % immediately reveals which table an ability
    rolls on (primer §5) -- and abilities with 0% across many hits flag
    periodic/ground effects.
    """
    counts = defaultdict(lambda: {"hits": 0, "crits": 0})
    for ev in events:
        if ev["event"] not in ("SWING_DAMAGE",) and not ev["event"].endswith("_DAMAGE"):
            continue
        if source_name and ev.get("sourceName", "").strip('"') != source_name:
            continue
        ability = "Melee" if ev["event"] == "SWING_DAMAGE" else ev.get("spellName", "?").strip('"')
        key = (ev.get("sourceName", "?").strip('"'), ability)
        counts[key]["hits"] += 1
        if ev.get("critical"):
            counts[key]["crits"] += 1
    out = {}
    for key, c in counts.items():
        out[key] = {**c, "crit_pct": round(100 * c["crits"] / c["hits"], 2) if c["hits"] else 0.0}
    return out


def avoidance_breakdown(events, source_name=None):
    """miss/dodge/parry/resist/immune counts per (sourceName, ability)."""
    counts = defaultdict(lambda: defaultdict(int))
    for ev in events:
        if not (ev["event"] == "SWING_MISSED" or ev["event"].endswith("_MISSED")):
            continue
        if source_name and ev.get("sourceName", "").strip('"') != source_name:
            continue
        ability = "Melee" if ev["event"] == "SWING_MISSED" else ev.get("spellName", "?").strip('"')
        key = (ev.get("sourceName", "?").strip('"'), ability)
        counts[key][ev.get("missType", "?")] += 1
    return {k: dict(v) for k, v in counts.items()}


if __name__ == "__main__":
    import sys
    import pprint

    events = parse_log(sys.argv[1])
    print(f"Parsed {len(events)} events")
    print("\n=== Crit rate by source/ability ===")
    pprint.pprint(crit_rate_by_source_ability(events))
    print("\n=== Avoidance breakdown ===")
    pprint.pprint(avoidance_breakdown(events))
