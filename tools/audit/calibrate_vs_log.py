#!/usr/bin/env python3
"""Phase 2 T8 (partial) — calibrate the sim against real combat logs.

    py tools/audit/calibrate_vs_log.py --character Elric "<log>" ["<log>" ...]
    py tools/audit/calibrate_vs_log.py --character Elric --all-logs

Compares the sim's BASE per-event value (no talent multipliers, no crit) against
the logged NON-CRIT average for the same ability, and reports the ratio. Because
talents are the one large thing 2b does not model, that ratio IS the unmodelled
talent multiplier — and PHASE_2 T8's rule is to report the delta per mechanism
rather than a pass/fail, so the output groups by school and never averages the
groups together.

🛑 **Field alignment is verified before any number is reported.** The parser in
`tools/log_parser/` is documented as unvalidated against a real Ascension log,
and an earlier ad-hoc scan in session 2b read the crit flag one field off. The
check below asserts three independently doc-confirmed facts (periodic effects at
0% crit; melee well below Holystrike) and REFUSES to report if they fail.

3.3.5 field layout, after splitting the body on ',':
  SPELL_DAMAGE  0 event 1 srcGUID 2 srcName 3 srcFlags 4 dstGUID 5 dstName
                6 dstFlags 7 spellId 8 spellName 9 spellSchool 10 amount
                11 overkill 12 school 13 resisted 14 blocked 15 absorbed
                16 CRITICAL 17 glancing 18 crushing
  SWING_DAMAGE  0 event 1 srcGUID 2 srcName 3 srcFlags 4 dstGUID 5 dstName
                6 dstFlags 7 amount 8 overkill 9 school 10 resisted 11 blocked
                12 absorbed 13 CRITICAL 14 glancing 15 crushing
"""
import argparse
import collections
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import config  # noqa: E402

# Piped/redirected stdout defaults to cp1252 on Windows and this file
# prints non-ASCII; without this it dies with UnicodeEncodeError only when
# its output is captured. See config.ensure_utf8_stdout.
config.ensure_utf8_stdout()
from core.db.connection import connect  # noqa: E402
from core.sim.ability_model import resolve_ability, AbilityResolutionError  # noqa: E402
from core.sim.content import get_preset  # noqa: E402
from core.builds.stats import CharState  # noqa: E402

DEFAULT_LOG_DIR = Path(r"E:\Ascension Launcher\resources\ascension-live\Logs")

# 🛑 Abilities are keyed on the log's OWN spellId field, never on the ability
# name (session 2c, gate G3). The name-matching this replaced produced both of
# 2b's calibration outliers, from one cause:
#
#   logged "Consecration" is 270768 and logged "Exorcism" is 270767 — out-of-
#   catalog spells summoned by Purification By Light, with no rank line, level
#   scaling of their own, and different magnitudes — while the tool resolved the
#   catalog's 26573 and 879. Different abilities that share a name, which is
#   exactly what the project's "never relate two spell IDs by name" rule exists
#   to prevent. It had simply never been applied to our own tooling.
#
# The log states the id on every damage line, so nothing has to be matched at
# all. What remains here is the small set of ids that are not directly castable
# and must be resolved through their OWNER, plus which of a multi-event ability's
# events the logged line corresponds to.

# logged spell id -> (spell id to resolve, which event). Hammer from the Heavens
# is out of catalog and reached only via a trigger, so it resolves through
# Hammerdin, whose only damage is that pulse.
ID_ROUTING = {
    282987: (282983, "attributed"),   # Hammer from the Heavens <- Hammerdin
    282984: (282984, "own"),          # Hour of Judgement's own periodic tick
}

# Doc-confirmed facts used as the field-alignment gate (primer §1). Matched on
# NAME here on purpose and only here: the gate asks "does the crit flag land in
# the right column", which any 0%-crit periodic effect answers regardless of
# which spell id it turns out to be.
ALIGNMENT_ZERO_CRIT = ("Consecration", "Righteous Vengeance", "Hour of Judgement")

# 🛑 Recorded in predictions/CALIBRATION_TOLERANCE.md BEFORE any 2c calibration
# ran, and duplicated here only so the gate is runnable. Do not edit this number
# to make a run pass — widening it needs a dated entry in that file with a
# reason, because a tolerance chosen after seeing the deltas gates nothing.
PER_ABILITY_TOLERANCE_PCT = 25.0


def scan_log(path, character):
    """Per-ability non-crit/crit damage samples for one character.

    Keyed on the log's own `spellId`, with the name kept only for display. See
    the ID_ROUTING comment for why the name is never the key. White swings have
    no spell id and use the sentinel 0.
    """
    dmg = collections.defaultdict(
        lambda: {"hit": [], "crit": [], "name": None})
    casts = collections.Counter()
    quoted = f'"{character}"'
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if quoted not in line:
                continue
            parts = line.split("  ", 1)
            if len(parts) != 2:
                continue
            f = parts[1].rstrip().split(",")
            if len(f) < 9 or f[2].strip('"') != character:
                continue
            ev = f[0]
            if ev == "SPELL_CAST_SUCCESS":
                try:
                    casts[int(f[7])] += 1
                except ValueError:
                    pass
            elif ev in ("SPELL_DAMAGE", "SPELL_PERIODIC_DAMAGE", "RANGE_DAMAGE"):
                if len(f) < 17:
                    continue
                try:
                    amt, sid = int(f[10]), int(f[7])
                except ValueError:
                    continue
                key = "crit" if f[16].strip().lower() in ("1", "true") else "hit"
                dmg[sid][key].append(amt)
                dmg[sid]["name"] = f[8].strip('"')
            elif ev == "SWING_DAMAGE":
                if len(f) < 14:
                    continue
                try:
                    amt = int(f[7])
                except ValueError:
                    continue
                key = "crit" if f[13].strip().lower() in ("1", "true") else "hit"
                dmg[0][key].append(amt)
                dmg[0]["name"] = "Melee"
    return dmg, casts


def _by_name(dmg, name):
    """All samples logged under a display name, merged across spell ids."""
    merged = {"hit": [], "crit": []}
    for v in dmg.values():
        if v["name"] == name:
            merged["hit"].extend(v["hit"])
            merged["crit"].extend(v["crit"])
    return merged if (merged["hit"] or merged["crit"]) else None


class AlignmentUncheckable(RuntimeError):
    """The alignment gate had no anchor ability in this log and could not run."""


def check_alignment(dmg):
    """Refuse to report unless doc-confirmed facts reproduce.

    🔴 3d D2 — THIS GATE USED TO FAIL OPEN, and off-Elric it always did.
    Every anchor it checks is a paladin ability (`ALIGNMENT_ZERO_CRIT`, plus
    "Melee" and "Lightbound Cleave"). When none of them appear it `continue`d
    past each one and returned an EMPTY problem list — which the caller reads as
    *"alignment OK"*. So for a Mage log, a Rogue log, or any log that is not
    this project's one paladin, the field-alignment check **passed vacuously and
    said so out loud**, printing "alignment OK" for a check that never ran.

    That is exactly the failure mode the primer names: *a guard that cannot run
    must SAY SO — never report the condition it failed to test.* It is the same
    shape as the extract wrapper's "is the game closed?" check that errored and
    printed "OK - game is closed" (primer v31 §5), implemented here.

    Now: if no anchor is present in sufficient quantity, this RAISES
    `AlignmentUncheckable` rather than returning `[]`. "I could not check" and
    "I checked and it was fine" are different answers and must not share a
    return value.

    ⚠ The anchor set is still paladin-only. Making this gate work for other
    classes needs doc-confirmed 0%-crit periodics and plausible-crit-rate
    anchors for those kits, which do not exist yet. Refusing is the honest
    interim state — it converts a silent false pass into a visible gap.
    """
    problems = []
    anchors_checked = []
    for name in ALIGNMENT_ZERO_CRIT:
        v = _by_name(dmg, name)
        if not v or (len(v["hit"]) + len(v["crit"])) < 20:
            continue
        anchors_checked.append(f"{name} (0%-crit periodic)")
        if v["crit"]:
            problems.append(
                f"{name} shows {len(v['crit'])} crits — it is a doc-confirmed "
                "0%-crit periodic effect, so the critical-flag field is "
                "misaligned")
    for label in ("Melee", "Lightbound Cleave"):
        v = _by_name(dmg, label)
        if v and (len(v["hit"]) + len(v["crit"])) >= 30:
            anchors_checked.append(f"{label} (plausible crit rate)")
            rate = len(v["crit"]) / (len(v["hit"]) + len(v["crit"]))
            if not 0.05 < rate < 0.95:
                problems.append(
                    f"{label} crit rate {rate:.1%} is implausible — suspect "
                    "field misalignment")
    if not anchors_checked:
        present = sorted({v["name"] for v in dmg.values() if v.get("name")})
        anchor_names = sorted(ALIGNMENT_ZERO_CRIT) + ["Melee", "Lightbound Cleave"]
        # Be precise about WHY it could not run — "absent" and "present but too
        # few samples" are different problems with different fixes, and saying
        # the wrong one sends the next reader looking in the wrong place.
        thin = []
        for name in anchor_names:
            v = _by_name(dmg, name)
            if v:
                thin.append(f"{name} ({len(v['hit']) + len(v['crit'])} events)")
        reason = (f"the anchors present are all BELOW their sample thresholds "
                  f"(20 events for a 0%-crit periodic, 30 for a crit-rate "
                  f"check): {', '.join(thin)}" if thin else
                  f"NONE of the anchor abilities appears in this log at all")
        raise AlignmentUncheckable(
            f"field alignment COULD NOT BE CHECKED — {reason}. This is NOT a "
            f"pass. Anchors are {anchor_names}, all paladin; this log contains "
            f"{len(present)} ability names "
            f"({', '.join(present[:8])}{'…' if len(present) > 8 else ''}). "
            f"Refusing rather than reporting an unverified alignment as OK.")
    return problems, anchors_checked


def _pick_event(ab, pick):
    evs = ab.events()
    if not evs:
        return None
    if pick == "attributed":
        cand = [e for e in evs if e.is_attributed]
        return cand[0] if cand else evs[0]
    if pick == "own":
        cand = [e for e in evs if not e.is_attributed]
        return cand[0] if cand else evs[0]
    return evs[0]


def resolve_for(conn, logged_id, level=60):
    """`(ResolvedAbility, event)` for a LOGGED SPELL ID, or `(None, reason)`."""
    if logged_id == 0:
        return None, "white swing — auto-attacks are not modelled"
    sid, pick = ID_ROUTING.get(logged_id, (logged_id, None))
    try:
        ab = resolve_ability(conn, sid, level=level)
    except AbilityResolutionError as e:
        return None, f"resolver refused: {e}"
    ev = _pick_event(ab, pick)
    if ev is None:
        return None, "resolves to NO EVENTS (no known magnitude)"
    return ab, ev


# 🛑 3d C4 — the circularity guard that was DOCUMENTED AND NEVER IMPLEMENTED.
#
# `seed_epistemics.py:143` asserts, in prose, that *"Holy Shock is EXCLUDED from
# the Holy-group constant, same treatment as Consecration."* It was not. Grep
# found `ascension_measured_provisional` in exactly two files — the seeder and
# the precedence dict — and ZERO times under `tools/`. So `sim_base()` embedded
# Holy Shock's 0.40 SP coefficient, `emit()` pooled Holy Shock into the Holy
# school group, and the group median was then used to judge... the parses that
# 0.40 was back-solved from in the first place. A documented-but-absent guard is
# worse than a missing one: it reads as satisfied to the next session.
#
# Derived, not hardcoded. Any coefficient whose `source` marks it as back-solved
# from our own parses makes its spell ineligible for a group constant. Listing
# spell id 25902 literally would go stale the moment a second provisional value
# is seeded — and the seeding path for one already exists.
CIRCULAR_COEFF_SOURCES = {"ascension_measured_provisional"}


def circular_terms(ev):
    """Back-solved coefficient terms in a resolved event, if any.

    A spell carrying one cannot contribute to a school-group constant that is
    itself compared against the parses the coefficient came from. It is still
    REPORTED per ability — the number is informative — it just cannot vote.
    """
    out = []
    for t in (ev.terms or []):
        if t.get("source") in CIRCULAR_COEFF_SOURCES:
            out.append((t.get("term"), t.get("coefficient"), t.get("source")))
    return out


def independent_alternative(conn, source_spell_id, term_type):
    """The best NON-circular coefficient for this term, if any source states one.

    Reported next to a circular term so the operator can see that an independent
    check exists — Holy Shock's SP is provisional 0.40 (back-solved) but
    db.ascension.gg separately STATES 0.2145, roughly half.

    🛑 REPORTED, NOT SUBSTITUTED. Swapping the tool's arithmetic onto the
    independent value is defensible and is arguably what "then the scraped 0.214
    stands in calibration" asks for — but it changes a calibration number, and
    `3d` ships no such change (§8 scope fence). Surfacing it lets `3e` make that
    call deliberately, with both numbers in front of it, instead of inheriting a
    silent rebind from a hygiene session.
    """
    row = conn.execute(
        "SELECT coefficient, source FROM spell_scaling "
        "WHERE spell_id = ? AND term_type = ? AND source NOT IN "
        "(" + ",".join("?" * len(CIRCULAR_COEFF_SOURCES)) + ") "
        "ORDER BY coefficient DESC LIMIT 1",
        (source_spell_id, term_type, *sorted(CIRCULAR_COEFF_SOURCES))).fetchone()
    return (row[0], row[1]) if row else (None, None)


def sim_base(conn, logged_id, cs, content, level=60, talents=None):
    """`(value, school)` for one logged event, or `(None, reason)`.

    Returns the sim's BASE (pre-crit) value. When `talents` is supplied the
    build's talent multiplier for that event's school and class mask is applied,
    which is what the T8 gate compares against; without it the value is the raw
    base, which is the diagnostic 2b used to size the unmodelled talent layer.
    Both are reported side by side because they answer different questions.
    """
    ab, ev = resolve_for(conn, logged_id, level=level)
    if ab is None:
        return None, ev
    r = ab.expected_hit(cs, content, event=ev)
    base = (r.breakdown["base_min"] + r.breakdown["base_max"]) / 2.0
    if base <= 0:
        return None, "base resolves to 0"
    if talents is not None:
        factor, _ = talents.damage_multiplier(
            ev.school, spell_family=ab.spell_family,
            class_mask=ab.spell_class_mask)
        base *= factor
    return base, ev.school


def weapon_fraction(cs, ev):
    """What share of this event's base value comes from WEAPON terms?

    0.0 = no weapon term at all; 1.0 = pure weapon percent with no flat. Only
    those two extremes give a weapon-FREE pair ratio (see `pair_ratios`).
    """
    weapon = flat = 0.0
    mh = cs.main_hand or {}
    swing = ((mh.get("min", 0.0) + mh.get("max", 0.0)) / 2.0)
    for t in (ev.terms or []):
        if t.get("term") == "WEAPON" and t.get("coefficient"):
            weapon += t["coefficient"] * swing
        elif t.get("min") is not None:
            flat += (t["min"] + (t.get("max") or t["min"])) / 2.0
    total = weapon + flat
    return (weapon / total) if total else 0.0


def pair_ratios(conn, names, cs, content, level=60):
    """Same-school ability pairs whose ratio is INDEPENDENT of weapon damage.

    🚨 Why this exists (session 2c, gate G1). 2b's headline calibration quantity
    was the Holy ÷ Holystrike ratio, on the reasoning that buff state multiplies
    both schools and cancels. It does — but a ratio only cancels factors applied
    to BOTH sides, and these two sides are not symmetric: the Holystrike
    abilities are ~87% weapon damage while the Holy ones carry no weapon term at
    all. The sim's weapon input came from an older King Gordok parse, not the
    same session as any log, so an error in it moves the denominator alone and
    passes into the ratio at very nearly 1:1.

    A pair is weapon-free only at the extremes: both abilities carry no weapon
    term (so W never enters), or both are pure weapon-percent with no flat (so W
    factors out of numerator and denominator alike). Anything in between — a
    flat plus a weapon term, which is most of this kit — does NOT cancel, because
    the flat does not scale with W.

    Same school is required as well, so the school's whole talent stack cancels
    too and what is left is the ratio of the two BASE FORMULAS. That is a
    statement about our data alone, and a real parse can check it directly.
    """
    resolved = {}
    for sid, label in names.items():
        ab, ev = resolve_for(conn, sid, level=level)
        if ab is None:
            continue
        r = ab.expected_hit(cs, content, event=ev)
        base = (r.breakdown["base_min"] + r.breakdown["base_max"]) / 2.0
        if base <= 0:
            continue
        resolved[sid] = {"base": base, "school": ev.school, "label": label,
                         "wfrac": weapon_fraction(cs, ev)}

    out = []
    ordered = sorted(resolved, key=lambda s: resolved[s]["label"])
    for i, a in enumerate(ordered):
        for b in ordered[i + 1:]:
            ra, rb = resolved[a], resolved[b]
            if ra["school"] != rb["school"]:
                continue
            both_flat = ra["wfrac"] < 0.02 and rb["wfrac"] < 0.02
            both_weapon = ra["wfrac"] > 0.98 and rb["wfrac"] > 0.98
            if not (both_flat or both_weapon):
                continue
            out.append({
                "a": a, "b": b, "school": ra["school"],
                "label_a": ra["label"], "label_b": rb["label"],
                "predicted": ra["base"] / rb["base"],
                "kind": "no weapon term either side" if both_flat
                        else "pure weapon-percent both sides",
            })
    return out, resolved


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("logs", nargs="*")
    ap.add_argument("--character", default="Elric")
    ap.add_argument("--all-logs", action="store_true")
    ap.add_argument("--log-dir", default=str(DEFAULT_LOG_DIR))
    # 🛑 3d F2 — THE STAT BLOCK IS REQUIRED. The defaults are DELETED, not
    # corrected.
    #
    # These carried AP 584 / SP 533 / weapon 585-669 from the 2026-08-03 build
    # doc — a Path-of-Duality-era, mixed-date sheet. The verified block from the
    # same-session capture is AP 141 / SP 638 / 543.6-646.3
    # (predictions/calib_2026-08-05_2e_poi.md:9-13). AP was out by a factor of
    # four, and any run that omitted the flags silently used the wrong numbers
    # while printing results that looked exactly like the right ones. That
    # happened: pred_2026-08-05_elric_paladin.md:62 records a --all-logs run with
    # no stat flags at all.
    #
    # Swapping in the correct defaults was the obvious fix and is the wrong one.
    # Rule 2 is *unconfirmed = flagged, never silently defaulted* — and a default
    # is a claim about a character's stats at a moment in time, which is exactly
    # the kind of thing that goes stale without anyone noticing. PLAN_3C's
    # alternative ("read it from a named capture folder") is worse still: it
    # silently rebinds to whatever that folder holds later.
    #
    # So: no defaults. State the block or get a refusal.
    ap.add_argument("--ap", type=float, required=True,
                    help="attack power. REQUIRED — no default, deliberately")
    ap.add_argument("--sp", type=float, required=True,
                    help="spell power. REQUIRED — no default, deliberately")
    ap.add_argument("--weapon-min", type=float, required=True,
                    help="main-hand min damage. REQUIRED")
    ap.add_argument("--weapon-max", type=float, required=True,
                    help="main-hand max damage. REQUIRED")
    # Was hardcoded at 3.57 inside main() with no flag at all — so a caster or
    # anyone with a different weapon could not state their own speed even if
    # they knew it.
    ap.add_argument("--weapon-speed", type=float, required=True,
                    help="main-hand speed in seconds. REQUIRED (was hardcoded "
                         "at 3.57 with no flag)")
    # ⚠ NAMED GAPS, not silent zeros. These three are real inputs the tool does
    # not take, and the CharState below is constructed with crit at 0.0 — which
    # is fine for a NON-CRIT-average comparison (the whole tool compares against
    # non-crit means) but would be wrong for anything else. Naming them here is
    # cheaper than rediscovering them.
    ap.add_argument("--haste", type=float, default=None,
                    help="NOT MODELLED YET — accepted and reported as a gap. "
                         "Haste changes cast/swing counts, not the per-hit base "
                         "this tool compares, so it is safe to omit here and "
                         "wrong to omit in a DPS comparison")
    ap.add_argument("--spell-crit", type=float, default=None,
                    help="NOT MODELLED YET — this tool compares NON-CRIT means, "
                         "so crit does not enter. Reported as a gap")
    ap.add_argument("--ranged-ap", type=float, default=None,
                    help="NOT MODELLED YET — no ranged attack table exists "
                         "(weights.py:28-42). Reported as a gap")
    ap.add_argument("--min-hits", type=int, default=15)
    ap.add_argument("--build", default="fixtures/build_elric_paladin.json",
                    help="build whose TALENTS are modelled on top of the base "
                         "value; pass '' to compare bases only")
    args = ap.parse_args()

    paths = [Path(p) for p in args.logs]
    if args.all_logs:
        paths = sorted(Path(args.log_dir).glob("* WoWCombatLog.txt"))
    if not paths:
        print("no logs given; pass paths or --all-logs")
        return 1

    conn = connect(config.DB_PATH)
    content = get_preset("raid_boss_st")

    # The talent layer (T4b). Reported as a SECOND column beside the raw base
    # rather than replacing it: base-vs-logged sizes the whole unmodelled layer
    # (2b's diagnostic), modelled-vs-logged is what the T8 gate judges.
    talents = None
    if args.build:
        import json
        from core.sim.talents import resolve_talents
        bd = json.loads((Path(config.REPO) / args.build).read_text(encoding="utf-8"))
        talents = resolve_talents(conn, bd["talents"])
        print(f"talents modelled from {args.build}: "
              f"{sum(1 for m in talents.modifiers if m.value is not None)} "
              f"decoded effects, "
              f"{len(talents.unmodelled())} unmodelled")
        for w in talents.warnings:
            print(f"  ! {w}")
    cs = CharState(level=60, attack_power=args.ap, spell_power=args.sp,
                   spell_crit_pct=0.0, melee_crit_pct=0.0,
                   main_hand={"min": args.weapon_min, "max": args.weapon_max,
                              "speed": args.weapon_speed})
    # 3d F2 — echo the block back. Every number below is a function of these
    # five, and a run whose stat block is not visible in its own output is a run
    # nobody can check later. This is what pred_2026-08-05_elric_paladin.md:62
    # was missing.
    print(f"\nSTAT BLOCK (stated, not defaulted): AP {args.ap:g} · "
          f"SP {args.sp:g} · weapon {args.weapon_min:g}-{args.weapon_max:g} "
          f"@ {args.weapon_speed:g}s")
    _gaps = [n for n, v in (("--haste", args.haste),
                            ("--spell-crit", args.spell_crit),
                            ("--ranged-ap", args.ranged_ap)) if v is not None]
    if _gaps:
        print(f"  ⚠ {', '.join(_gaps)} accepted but NOT MODELLED — this tool "
              f"compares non-crit per-hit bases, where none of them enter. "
              f"Stated so the value is not silently discarded.")

    pooled = collections.defaultdict(
        lambda: {"hit": [], "crit": [], "name": None})
    per_log = []
    for p in paths:
        if not p.exists():
            print(f"! missing: {p}")
            continue
        dmg, casts = scan_log(p, args.character)
        if not dmg:
            print(f"  {p.name}: no {args.character} damage events, skipped")
            continue
        try:
            problems, anchors = check_alignment(dmg)
        except AlignmentUncheckable as e:
            # 3d D2 — "could not check" is its own outcome, not a pass.
            print(f"🛑 {p.name}: FIELD ALIGNMENT COULD NOT BE CHECKED, "
                  f"refusing to report")
            print(f"     {e}")
            continue
        if problems:
            print(f"🛑 {p.name}: FIELD ALIGNMENT FAILED, refusing to report")
            for pr in problems:
                print(f"     {pr}")
            continue
        per_log.append((p.name, dmg))
        for k, v in dmg.items():
            pooled[k]["hit"].extend(v["hit"])
            pooled[k]["crit"].extend(v["crit"])
            pooled[k]["name"] = v["name"]
        n = sum(len(v["hit"]) + len(v["crit"]) for v in dmg.values())
        print(f"  {p.name}: {n:,} damage events, alignment OK "
              f"(anchors checked: {', '.join(anchors)})")

    if not per_log:
        print("nothing usable")
        return 1

    # A ratio far outside any plausible talent stack is not a multiplier, it is
    # a broken sim base. Reporting those alongside real multipliers would invite
    # averaging them in, so they are separated out with a likely cause. Keyed by
    # SPELL ID — the reason this whole tool stopped keying on names is that two
    # of these entries used to catch the wrong spell.
    BROKEN_ABOVE = 3.0
    KNOWN_BROKEN = {
        904881: "sim base ~1: Righteous Vengeance is 30% of a CRIT's damage as "
                "a DoT, and the sim has no source-damage input for it",
        904880: "Holy Finish: combo points are not parameterised (2a gap) so "
                "the base is computed at 0 CP — and its CP term is QUADRATIC",
        20375: "seals are per-swing riders; the sim scores them per cast",
        31801: "seals are per-swing riders; the sim scores them per cast",
        # 3d C4: named here because the audit found it absent. It no longer
        # reaches this bucket (the circular check runs first), but if the
        # circularity is ever resolved and the exclusion lifted, the ratio is
        # still ~5x and the cause below is what to look at.
        25902: "Holy Shock: resolves to a base far below its own rank-4 flat "
               "(562-608 per the captured tooltip) — a resolver/rank issue, "
               "separate from the SP-coefficient circularity. 3e.",
    }

    def label_of(sid, v):
        nm = v.get("name") or str(sid)
        return f"{nm} [{sid}]"

    def emit(label, dmg_map, show_broken=True):
        print(f"\n{'=' * 78}\n{label}\n{'=' * 78}")
        print(f"{'ability [spell id]':38}{'school':12}{'n':>6}{'base':>8}"
              f"{'+talents':>9}{'logged':>9}{'vs base':>9}{'vs model':>9}")
        by_school, broken, unresolved = collections.defaultdict(list), [], []
        circular = []
        for sid, v in sorted(dmg_map.items(),
                             key=lambda kv: -len(kv[1]["hit"])):
            if len(v["hit"]) < args.min_hits:
                continue
            lab = label_of(sid, v)
            base, school = sim_base(conn, sid, cs, content)
            logged = statistics.mean(v["hit"])
            if base is None:
                unresolved.append((lab, school, len(v["hit"]), logged))
                continue
            modelled, _ = sim_base(conn, sid, cs, content, talents=talents)
            ratio = logged / base
            model_ratio = logged / modelled if modelled else ratio
            # 3d C4 — a spell whose coefficient was back-solved from these very
            # parses is REPORTED but may not vote in its school's constant.
            _, ev_c = resolve_for(conn, sid)
            circ = circular_terms(ev_c) if ev_c is not None and hasattr(
                ev_c, "terms") else []
            if circ:
                # Checked BEFORE the broken filter on purpose. A circular
                # coefficient is the more important fact about the row, and
                # burying it under "sim base is wrong, cause unknown" is how it
                # stayed invisible in the first place. Either way it does not
                # vote — this just makes the reason visible.
                circular.append((lab, school, ratio, len(v["hit"]), circ,
                                 getattr(ev_c, "source_spell_id", sid)))
                continue
            if ratio > BROKEN_ABOVE or ratio < 0.5:
                broken.append((sid, lab, ratio, base, logged, len(v["hit"])))
                continue
            mark = ""
            print(f"{lab[:37]:38}{str(school)[:11]:12}{len(v['hit']):>6}"
                  f"{base:>8,.0f}{modelled:>9,.0f}{logged:>9,.0f}"
                  f"{ratio:>8.2f}x{model_ratio:>8.2f}x{mark}")
            by_school[school].append((sid, lab, ratio, len(v["hit"]),
                                      model_ratio))

        if circular:
            print("\n--- ⊘ EXCLUDED from every school group: CIRCULAR "
                  "coefficient (3d C4) ---")
            for lab, school, r, n, terms, src_sid in circular:
                print(f"  {lab[:34]:36}{r:>8.2f}x  ({n} hits, {school})")
                for t, coeff, s in terms:
                    alt, alt_src = independent_alternative(conn, src_sid, t)
                    print(f"      {t} {coeff:g} via '{s}' — BACK-SOLVED from "
                          f"this project's own parses. Pooling it into a group "
                          f"constant that is then checked against those same "
                          f"parses is circular, so it is reported and never "
                          f"averaged in.")
                    if alt is not None:
                        print(f"      ↳ an INDEPENDENT source states {t} "
                              f"{alt:g} ('{alt_src}'), {alt / coeff:.2f}x the "
                              f"back-solved value. Reported, NOT substituted — "
                              f"swapping the tool onto it changes a calibration "
                              f"number, which is a 3e decision, not a hygiene "
                              f"session's.")
                    else:
                        print(f"      ↳ NO independent source states {t} — the "
                              f"back-solved value is the only one there is, so "
                              f"this ability cannot check anything today.")

        print("\n--- by school (groups are never averaged together) ---")
        for school, rows in sorted(by_school.items(),
                                   key=lambda kv: -sum(r[3] for r in kv[1])):
            rs = [r[2] for r in rows]
            if len(rows) < 2:
                print(f"  {school:12} single sample: {rows[0][1]} "
                      f"{rows[0][2]:.2f}x - no group estimate")
                continue
            spread = max(rs) - min(rs)
            flag = "  << WIDE, not one multiplier" if spread > 0.35 else ""
            print(f"  {school:12} n={len(rows)}  median "
                  f"{statistics.median(rs):.2f}x  range "
                  f"{min(rs):.2f}-{max(rs):.2f}{flag}")
            for _sid, lab, r, n, _mr in sorted(rows, key=lambda x: -x[3]):
                print(f"      {lab[:40]:42}{r:>6.2f}x  ({n} hits)")

        if show_broken and broken:
            print("\n--- EXCLUDED: sim base is wrong, not a talent multiplier ---")
            for sid, lab, r, base, logged, n in sorted(broken, key=lambda x: -x[2]):
                why = KNOWN_BROKEN.get(sid, "cause unknown - investigate")
                print(f"  {lab[:34]:36}{r:>8.2f}x  base {base:,.0f} vs "
                      f"{logged:,.0f}\n      {why}")
        if show_broken and unresolved:
            print("\n--- logged but NOT resolvable by the sim ---")
            for lab, why, n, logged in unresolved:
                print(f"  {lab[:34]:36}{logged:>9,.0f} avg / {n:>4} hits   {why}")
        return by_school

    pooled_groups = emit(
        f"POOLED across {len(per_log)} log(s) - sim BASE vs logged NON-CRIT avg",
        pooled)

    if len(per_log) > 1:
        print(f"\n\n{'#' * 78}\nPER-LOG - does the multiplier hold session to "
              f"session?\n{'#' * 78}")
        for nm, dmg in per_log:
            groups = emit(f"{nm}", dmg, show_broken=False)
            del groups

    # --- the weapon-free view (2c G1) -----------------------------------------
    # Only abilities that survived the main table are eligible. An ability whose
    # sim base is already known-broken (Righteous Vengeance has no source-damage
    # input, seals are scored per cast, Holy Finish is computed at 0 CP) would
    # otherwise generate pairs with predicted ratios like 596.0, burying the real
    # ones in noise — and worse, inviting someone to read one.
    names = {sid: lab for rows in pooled_groups.values()
             for sid, lab, _r, _n, _mr in rows}
    pairs, resolved = pair_ratios(conn, names, cs, content)
    print(f"\n\n{'#' * 78}\nWEAPON-FREE PAIR RATIOS - the quantities that survive "
          f"a wrong weapon input\n{'#' * 78}")
    print("A cross-school ratio does NOT cancel a weapon-damage error: the "
          "Holystrike side is\n~87% weapon damage and the Holy side is 0%, so a "
          "d% error in weapon damage moves the\nHoly/Holystrike ratio by about "
          "the same d%. These pairs do cancel it.\n")
    if not pairs:
        print("  no weapon-free pair available in this sample")
    for pr in pairs:
        deltas = []
        rows = []
        for nm, dmg in per_log:
            va, vb = dmg.get(pr["a"]), dmg.get(pr["b"])
            if (not va or not vb or len(va["hit"]) < args.min_hits
                    or len(vb["hit"]) < args.min_hits):
                continue
            obs = statistics.mean(va["hit"]) / statistics.mean(vb["hit"])
            d = 100 * (obs / pr["predicted"] - 1)
            deltas.append(d)
            rows.append(f"    {nm[:24]:26} observed {obs:.3f}  "
                        f"delta {d:+6.1f}%  "
                        f"(n {len(va['hit'])}/{len(vb['hit'])})")
        if not rows:
            continue
        worst = max(abs(d) for d in deltas)
        # ASCII on purpose: this script's output is routinely piped, and Python
        # picks cp1252 for a non-console stdout on Windows (INDEX_GUIDE v10).
        verdict = ("[REPRODUCES]  " if worst <= 10 and len(rows) >= 3
                   else "[thin sample] " if len(rows) < 3 and worst <= 10
                   else "[MISSES]      ")
        print(f"  {verdict}  {pr['label_a']} / {pr['label_b']}   "
              f"[{pr['school']}, {pr['kind']}]")
        print(f"    predicted from the base formulas: {pr['predicted']:.3f}  "
              f"(worst delta {worst:.1f}% over {len(rows)} log(s))")
        for r in rows:
            print(r)
    print("\n  Composition of each resolved ability's base (weapon share):")
    for sid in sorted(resolved, key=lambda s: -resolved[s]["wfrac"]):
        r = resolved[sid]
        print(f"    {r['label'][:38]:40}{r['school'] or '?':12}"
              f"{r['wfrac']:>6.0%} weapon")

    # --- the T8 gate, against tolerances recorded BEFORE this ran -------------
    print(f"\n\n{'#' * 78}\nT8 GATE - against predictions/CALIBRATION_TOLERANCE.md"
          f"\n{'#' * 78}")
    print(f"  per-ability tolerance on the non-crit average: "
          f"+/-{PER_ABILITY_TOLERANCE_PCT:g}%")
    print("  (aggregate-DPS tolerance is checked by cli/sim.py against a full "
          "rotation, not here)\n")
    passed, missed = [], []
    for rows in pooled_groups.values():
        for _sid, lab, _ratio, n, model_ratio in rows:
            # Gated on the MODELLED value (base x the build's talent layer),
            # never on a fitted residual — fitting the residual and then
            # gating against it would make the gate unfalsifiable.
            delta = 100 * (model_ratio - 1.0)
            (passed if abs(delta) <= PER_ABILITY_TOLERANCE_PCT
             else missed).append((lab, model_ratio, n))
    for lab, ratio, n in sorted(missed, key=lambda x: -x[1]):
        print(f"  [MISS] {lab[:38]:40} logged/modelled {ratio:.2f}x  "
              f"({100 * (ratio - 1):+.0f}%, n={n})")
    for lab, ratio, n in passed:
        print(f"  [ OK ] {lab[:38]:40} logged/modelled {ratio:.2f}x  (n={n})")
    print(f"\n  {len(passed)} within tolerance, {len(missed)} outside.")
    if missed:
        print("  🛑 MISSING THE TOLERANCE IS A FINDING, and the finding is that "
              "an unmodelled\n     multiplier remains. Note the misses group by "
              "SCHOOL, which is what an\n     unmodelled school-scoped amplifier "
              "or an unmodelled buff looks like - and\n     buff state is known "
              "to move 1.41x between these sessions. Do NOT close this\n     by "
              "fitting a constant; see holy_holystrike_ratio_weapon_input_confound.")

    print(f"\nNOTE Ratios assume the stats passed (AP {args.ap:g} / SP "
          f"{args.sp:g} / weapon {args.weapon_min:g}-{args.weapon_max:g}).\n"
          "  A multiplier that MOVES between logs is buff/gear state, not a "
          "talent constant - trust the\n  within-school AGREEMENT (do the "
          "abilities of one school track each other?) over the absolute value.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
