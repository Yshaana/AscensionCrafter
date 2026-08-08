"""Encounter windowing from a combat log — on GUID, with the kill chosen explicitly.

🚨 `3m` Block D (`AUDIT_3L` F13) — WHY THIS EXISTS AND WHY IT IS NOT A ONE-LINER.

`3l` verified the Molten Core capture's Gehennas pull and wrote: *"GUID
`0xF130002FE3000994` … one `UNIT_DIED` at 20:02:55.246. **One pull, never two
encounters.**"* That is true of the GUID it checked, and it **invites the exact
mis-window it was written to prevent** — a reader takes "one pull" as a property
of the BOSS and windows on the boss's NAME.

Measured on that same capture:

    Lucifron      1 GUID    kill @ 19:45:41
    Magmadar      2 GUIDs   kill @ 19:40:47   (one wipe first)
    Gehennas      2 GUIDs   kill @ 20:02:55   (wipe 19:52:51-19:54:56)
    Garr          4 GUIDs   kill @ 20:41:14   (three failed pulls first)
    Baron Geddon  3 GUIDs   NO KILL

First-mention-of-the-name -> `UNIT_DIED` on Gehennas spans **603.6 s** against the
kill GUID's **379.8 s**: it folds in a 125 s wipe plus ~100 s of downtime and
deflates DPS by ~37% — on the capture whose entire value is per-parse calibration.

⚠ **A WINDOW IS NOT COVERAGE OF THAT WINDOW.** The Gehennas kill spans a client
crash (one log file ends 19:57:30, the next resumes 19:58:30), so ~60 s inside its
379.8 s carries no log at all. `logged_seconds` is reported separately from
`wall_seconds` for exactly this, and a caller dividing damage by the wrong one
gets a number that looks fine.

🛑 **AMBIGUITY REFUSES.** Two GUIDs with a `UNIT_DIED`, or none at all, returns no
window and says why — never the longest attempt, never the last one. Same rule
rank resolution already follows: an ambiguous answer is recorded as ambiguous.

Pure logic (`core/` rules): takes an iterable of log LINES and returns dicts. It
never opens a file, never takes a path, and never imports `config`.
"""
import re

# A unit GUID as the 3.3.5 client writes it, immediately followed by the unit's
# quoted name. Matching the pair together is what ties a GUID to a boss without
# ever relating two ids by name (CLAUDE.md's standing rule) — the NAME selects
# which GUIDs are candidates; the GUID is what the window is built on.
_GUID_NAME = re.compile(r'(0x[0-9A-Fa-f]{16}),"([^"]+)"')

# `MM/DD HH:MM:SS.mmm` — the client's own local-time stamp. 🛑 Combat-log times
# are client LOCAL and must never be mixed with the crawler's UTC stamps
# (`seed_confirmed.py`); this module only ever SUBTRACTS two of them, which is
# safe under any fixed offset, and returns seconds rather than instants.
_TS = re.compile(r"^(\d{1,2})/(\d{1,2}) (\d{2}):(\d{2}):(\d{2})\.(\d{3})")


def _parse_ts(line):
    """Seconds-within-year for one log line, or None. Only ever differenced."""
    m = _TS.match(line)
    if not m:
        return None
    mon, day, hh, mm, ss, ms = (int(x) for x in m.groups())
    # A day ordinal is enough: windows never span a month boundary, and if one
    # ever did, the difference would be obviously wrong rather than subtly so.
    return ((mon * 31 + day) * 86400.0 + hh * 3600.0 + mm * 60.0 + ss + ms / 1000.0)


def scan_encounters(lines, boss_name):
    """Every GUID seen carrying `boss_name`, with its own first/last/death times.

    Returns a list of dicts ordered by first appearance, each:
    `{guid, first, last, died, events}` — times in seconds-within-year, `died`
    None when that GUID never logged a `UNIT_DIED`.

    ⚠ `lines` may span SEVERAL log files (a client crash splits one pull across
    two). Pass them concatenated in time order; the GUID is what stitches them,
    which is the named limitation in `3l` §5.
    """
    seen = {}
    for line in lines:
        if boss_name not in line:
            continue
        ts = _parse_ts(line)
        if ts is None:
            continue
        for guid, name in _GUID_NAME.findall(line):
            if name != boss_name:
                continue
            rec = seen.get(guid)
            if rec is None:
                rec = seen[guid] = {"guid": guid, "first": ts, "last": ts,
                                    "died": None, "events": 0}
            rec["last"] = ts
            rec["events"] += 1
            if "UNIT_DIED" in line:
                rec["died"] = ts
    return sorted(seen.values(), key=lambda r: r["first"])


def kill_window(lines, boss_name, gaps=()):
    """The window of the ENCOUNTER THAT KILLED `boss_name`, or a refusal.

    `gaps` is an iterable of `(start, end)` second pairs during which no log
    exists — a client crash, typically. Any overlap with the window is
    subtracted from `logged_seconds` and named in `notes`.

    Returns a dict. On success: `{ok: True, guid, start, end, wall_seconds,
    logged_seconds, attempts, notes}`. On refusal: `{ok: False, reason, ...}` —
    and the reason is always specific enough to act on.

    🛑 It refuses rather than guessing in BOTH directions: no kill at all
    (Baron Geddon in the reference capture — three attempts, no death) and more
    than one kill (a boss pulled and killed twice in one log).
    """
    encounters = scan_encounters(lines, boss_name)
    if not encounters:
        return {"ok": False, "reason": f"no encounter for {boss_name!r} in these "
                                       f"lines", "attempts": 0}
    kills = [e for e in encounters if e["died"] is not None]
    if not kills:
        spans = ", ".join(f"{e['last'] - e['first']:.0f}s" for e in encounters)
        return {
            "ok": False,
            "reason": (f"{boss_name} was engaged {len(encounters)} time(s) "
                       f"({spans}) and NEVER died in these lines — there is no "
                       f"kill window. Returning the longest or the last attempt "
                       f"would be a guess wearing a measurement's clothes"),
            "attempts": len(encounters),
            "candidates": [e["guid"] for e in encounters]}
    if len(kills) > 1:
        return {
            "ok": False,
            "reason": (f"{boss_name} has {len(kills)} GUIDs carrying a UNIT_DIED "
                       f"— the boss was killed more than once in these lines and "
                       f"'the kill' is ambiguous. Pass a narrower slice, or pick "
                       f"a GUID explicitly"),
            "attempts": len(encounters),
            "candidates": [e["guid"] for e in kills]}

    k = kills[0]
    start, end = k["first"], k["died"]
    wall = end - start
    lost, notes = 0.0, []
    for g0, g1 in gaps:
        lo, hi = max(start, g0), min(end, g1)
        if hi > lo:
            lost += hi - lo
            notes.append(
                f"{hi - lo:.1f}s inside this window has NO LOG (a capture gap) — "
                f"wall-clock duration and LOGGED duration are different numbers "
                f"here, and dividing damage by the wrong one is a silent error")
    if len(encounters) > 1:
        notes.append(
            f"{len(encounters) - 1} earlier attempt(s) on {boss_name} were "
            f"EXCLUDED by GUID. Windowing on the boss NAME instead would span "
            f"{end - encounters[0]['first']:.1f}s rather than {wall:.1f}s "
            f"(AUDIT_3L F13)")
    return {"ok": True, "guid": k["guid"], "start": start, "end": end,
            "wall_seconds": wall, "logged_seconds": wall - lost,
            "attempts": len(encounters), "notes": notes}
