"""`3e` C1 — parse an AscensionCrafterExport stat block.

The addon writes a ~40-line block per capture. Until now **every consumer
retyped four or five numbers out of it by hand** and discarded the other ~35,
and no parser existed anywhere in the repo. That hand channel is what produced
the contamination `2e` spent a whole session undoing: a stat block from a
different session is not a degraded input, it is *the whole error* for
weapon-dominated abilities. `3d` made the flags `required=True`, which made the
transcription compulsory rather than correct.

Pure logic (`core/` rules): takes TEXT, returns a dict, raises on refusal. It
knows nothing about paths or argv.

🛑 **Refusal semantics are inherited from `3d` F2 and deliberately kept.** A
field that is not in the block comes back **absent**, never defaulted. Nothing
here invents a number, and `require()` exists so a caller can demand a field and
get a named error instead of a silent `None` flowing into a calculation.

⚠ **Two families of field are parsed but deliberately NOT converted:**

* `ManaRegen_raw` — `GetManaRegen` returns per-second while the character sheet
  shows per-5. The addon prints the raw API return for exactly that reason.
  **Establish the unit before consuming it**; guessing and being wrong plants a
  silent 5x error in a block everything downstream trusts.
* `*Haste_raw_UNVERIFIED` — the addon does not trust these (`GetMeleeHaste` read
  1.06% against the rating line) and neither does this parser. They are exposed
  under their real names so a consumer has to opt in knowingly.
"""
import re
from datetime import datetime

# `Name: value` where value may carry units, percents or parenthetical asides.
_LINE = re.compile(r"^\s*([A-Za-z][A-Za-z0-9_]*)\s*:\s*(.+?)\s*$")
_HEADER = re.compile(r"^===\s*(.+?)\s*-\s*(.+?)\s*-\s*(.+?)\s*===\s*$")
# "227.7-253.7 (speed 1.66)"
_WEAPON = re.compile(
    r"^\s*([\d.]+)\s*-\s*([\d.]+)\s*\(speed\s*([\d.]+)\s*\)")
# "36 (3.60%)" -> rating and its converted percent
_RATING = re.compile(r"^\s*(-?[\d.]+)\s*\(\s*(-?[\d.]+)\s*%\s*\)")
_NUMBER = re.compile(r"^\s*(-?[\d.]+)")

SCHOOLS = ("Holy", "Fire", "Nature", "Frost", "Shadow", "Arcane")


class StatBlockError(Exception):
    """The block is unusable, or a required field is absent. Raised rather than
    defaulted — a missing stat that becomes 0.0 is the failure mode this whole
    module exists to remove."""


def _num(text):
    m = _NUMBER.match(text)
    return float(m.group(1)) if m else None


def parse_stat_block(text):
    """Parse an export into a dict. Absent fields are ABSENT, never zero.

    Returns keys: `character`/`realm`/`season`, `level`, `exported_at`
    (a `datetime`, or None if unparseable), the primary stats, `attack_power`,
    `spell_power` (per school, plus `spell_power` = the common value when every
    school agrees), `bonus_healing`, crit percentages, ratings (both the rating
    and its stated percent), `weapon` (`{min,max,speed}` per hand), `armor`,
    `mana_max`, `power_type`, and the raw unconverted fields under their own
    names.
    """
    if not text or "===" not in text:
        raise StatBlockError(
            "this does not look like an AscensionCrafterExport stat block — no "
            "'=== <character> - <realm> - <season> ===' header line found. "
            "Refusing rather than parsing something else's file")
    out = {"raw_fields": {}, "spell_power_by_school": {},
           "spell_crit_by_school": {}, "ratings": {}, "weapon": {}}
    for line in text.splitlines():
        h = _HEADER.match(line)
        if h:
            out["character"], out["realm"], out["season"] = (
                h.group(1), h.group(2), h.group(3))
            continue
        m = _LINE.match(line)
        if not m:
            continue
        key, val = m.group(1), m.group(2)
        out["raw_fields"][key] = val

        if key.startswith("SpellPower_"):
            out["spell_power_by_school"][key.split("_", 1)[1]] = _num(val)
        elif key.startswith("SpellCrit_"):
            out["spell_crit_by_school"][key.split("_", 1)[1]] = _num(val)
        elif key.startswith("Rating_"):
            r = _RATING.match(val)
            out["ratings"][key.split("_", 1)[1]] = (
                {"rating": float(r.group(1)), "pct": float(r.group(2))}
                if r else {"rating": _num(val), "pct": None})
        elif key in ("MainHandDamage", "OffHandDamage"):
            w = _WEAPON.match(val)
            hand = "main_hand" if key.startswith("Main") else "off_hand"
            if w:
                out["weapon"][hand] = {"min": float(w.group(1)),
                                       "max": float(w.group(2)),
                                       "speed": float(w.group(3))}
            # "none (no off-hand equipped)" -> the hand is ABSENT, not zero.
            # A zero-damage weapon and no weapon are different builds.

    def take(field, dest, cast=float):
        if field in out["raw_fields"]:
            v = _num(out["raw_fields"][field])
            if v is not None:
                out[dest] = cast(v)

    take("Level", "level", int)
    take("Strength", "strength")
    take("Agility", "agility")
    take("Stamina", "stamina")
    take("Intellect", "intellect")
    take("Spirit", "spirit")
    take("AttackPower", "attack_power")
    take("RangedAttackPower", "ranged_attack_power")
    take("BonusHealing", "bonus_healing")
    take("MeleeCrit", "melee_crit_pct")
    take("RangedCrit", "ranged_crit_pct")
    take("Armor", "armor")
    take("ManaMax", "mana_max")
    take("PowerMax", "power_max")
    if "PowerType" in out["raw_fields"]:
        out["power_type"] = out["raw_fields"]["PowerType"].split()[0].lower()

    # Every school reading the same number is the normal case (a flat SP pool);
    # a school-scoped grant makes them differ, and then there is no single
    # "spell power" and the caller must ask per school.
    sp = [v for v in out["spell_power_by_school"].values() if v is not None]
    if sp and len(set(sp)) == 1:
        out["spell_power"] = sp[0]
    elif sp:
        out["spell_power_varies_by_school"] = True
    crit = [v for v in out["spell_crit_by_school"].values() if v is not None]
    if crit and len(set(crit)) == 1:
        out["spell_crit_pct"] = crit[0]

    ts = out["raw_fields"].get("ExportedAt")
    out["exported_at"] = _parse_exported_at(ts) if ts else None
    out["exported_at_text"] = ts
    return out


def _parse_exported_at(text):
    """`ExportedAt: 2026-08-06 19:15:41 (client local time)` -> datetime.

    ⚠ CLIENT LOCAL TIME, with no zone. It is comparable to a combat log's
    timestamps (same clock, same machine) and to nothing else.
    """
    m = re.match(r"\s*(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2}:\d{2})", text or "")
    if not m:
        return None
    try:
        return datetime.strptime(f"{m.group(1)} {m.group(2)}",
                                 "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def require(block, *fields):
    """Fetch fields, raising a NAMED error for any that is absent.

    The point of the whole module: a consumer says what it needs, and an absent
    field stops the run instead of becoming a zero halfway down a formula.
    """
    missing = [f for f in fields if block.get(f) is None]
    if missing:
        raise StatBlockError(
            f"stat block is missing required field(s): {', '.join(missing)}. "
            f"Present: {sorted(k for k, v in block.items() if v is not None and k != 'raw_fields')}. "
            f"Refusing rather than defaulting — a missing stat that becomes 0.0 "
            f"is the error this parser exists to prevent")
    return tuple(block[f] for f in fields)


def session_mismatch(block, log_started_at, tolerance_hours=6.0):
    """Is this block from a different session than the log? (`3e` C1)

    Returns a warning string, or None. **This is the single check `2e` proved is
    worth more than all the others combined**: a stale stat block is not a
    degraded input, it is the entire error for weapon-dominated abilities — the
    ~1.37x "Holystrike calibration residual" that a planned session was built
    around turned out to be exactly this, and with a same-session export the
    same abilities calibrate at 1.00x and 0.99x.

    Neither timestamp carries a zone; both are client local time on one machine,
    which is what makes the comparison meaningful and also what makes it useless
    against anything else.

    🛑 **THREE OUTCOMES, AND ONLY ONE OF THEM IS SILENCE.** `None` means
    "checked, and they agree" — it is the caller's stay-silent value
    (`calibrate_vs_log.py:620-625`). Every case where the check could not RUN
    returns a string saying so. Until `3f` F4 the log side returned `None`,
    i.e. the all-clear, whenever the log's filename carried no parseable
    timestamp — and `WoWCombatLog.txt`, `06-08-2026-19.16.56 …` (EU day-first)
    and `2026-08-06 19-16-56 …` all do. A guard that reports "fine" when it
    failed to test is worse than no guard, because it manufactures confidence
    (primer §5, `3b`'s "is the game closed?" check).
    """
    exported = block.get("exported_at")
    if exported is None:
        return ("stat block carries no parseable ExportedAt, so it CANNOT be "
                "checked against the log's session. `2d` found a post-cast "
                "export byte-identical to the pre-cast one, and `2e` found a "
                "stale block was the whole calibration residual — neither is "
                "detectable on an untimestamped block")
    if log_started_at is None:
        return (f"⚠ THE LOG'S SESSION CANNOT BE DETERMINED, so this block "
                f"(exported {exported:%Y-%m-%d %H:%M}) CANNOT be checked "
                f"against it. The client writes "
                f"`YYYY-MM-DD-HH.MM.SS WoWCombatLog.txt` and only the FILENAME "
                f"carries a year — in-file timestamps are month/day. A renamed "
                f"or copied log therefore disables this check silently unless "
                f"it says so, which is what this line is. Treat the pairing as "
                f"UNVERIFIED: `2e` found a stale block was the entire "
                f"calibration residual for weapon-dominated abilities")
    delta = abs((exported - log_started_at).total_seconds()) / 3600.0
    if delta > tolerance_hours:
        return (f"🛑 STAT BLOCK AND LOG ARE {delta:.1f} HOURS APART "
                f"(block {exported:%Y-%m-%d %H:%M}, log "
                f"{log_started_at:%Y-%m-%d %H:%M}). These are probably "
                f"different sessions, and a stat block from a different session "
                f"is not a degraded input — for weapon-dominated abilities it "
                f"is the WHOLE error (`2e`)")
    return None
