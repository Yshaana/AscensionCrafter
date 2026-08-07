"""parse_admissibility.py — the APM ratio, implemented (3h D1), and the D4
admissibility predicates computed BLIND over the frozen cohort.

    py tools/audit/parse_admissibility.py

`3c` retracted `Boomcat` as "the best clean-qualifier candidate" on an APM
ratio of 0.24 — computed chat-side. `grep -rn "apm"` returned nothing: the
whole retraction rested on a number with no implementation. This file is the
implementation.

🛑 THE RATIO IS ONLY VALID ON INSTANT-HEAVY KITS, and returns None — not a
number — outside that regime. `ability_performance.casts` under-counts
cast-time casters (`SPELL_CAST_SUCCESS` and `SPELL_CAST_START` are disjoint by
cast type — 3e preflight thread 1), and 22 of the 41 cohort boards are
cast-time casters. A bare APM ratio across the cohort would be exactly the
kind of number this project retracts.

🛑 THE D4 COMPUTATION IS BLIND: every predicate is a property of the PARSE
(action rate, window length, phase resolution, snapshot lag) and the per-
character table is computed and printed before any delta or verdict is read.
The falsifiability comparison at the end reads the committed manifest's
verdicts — AFTER the blind table — because "does the rule remove a FAILING
character" cannot be answered without them.

⚠ E15 interplay: casts are summed over `is_pet = 0` rows only. Pet rows no
longer duplicate owner rows post-3i-B (the restatement lives in
pet_ability_damage), and a pet's casts are not the player's actions in any
case.

🆕 3i D — the rule is APPLIED (owner decision, Q4: yes, taking the known hit).
`admissibility_for()` is the single implementation both this tool's own
`main()` and `calibrate_crawled.py`'s gate loop call, so the two can never
drift. Predicates 4 and 5 are now COMPUTED, not printed as inert prose (D1,
D2); `resolved_entries` and the comparator context print beside every ratio
(D3); the fail-open regime is counted and "N of 41" is reported as a LOWER
BOUND with its composition (D4); the comparator excludes trash-tainted,
short, and self-overlapping scopes, and no longer silently drops a
legitimate 0.0 APM comparator (D5); the stamped thresholds are asserted
against this module's constants (D6).
"""
import json
import re
import sqlite3
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import config  # noqa: E402
from config import BUILDS_DB_PATH, DB_PATH  # noqa: E402

import calibrate_crawled as cc  # noqa: E402
from core.builds.phases import resolve_phase  # noqa: E402
from core.db.connection import connect  # noqa: E402
from ingest.logs_gg.build_builds_db import latest_phase_context  # noqa: E402

config.ensure_utf8_stdout()

# The regime bound, stated: a board with 3+ cast-time combat entries is a
# cast-time caster (the 3e-preflight classifier), and `casts` is structurally
# blind to its main buttons. Below 3, the kit is instant-heavy and casts/min
# is a faithful action rate.
MAX_CAST_TIME_ENTRIES = 2

# Death-deflation signature, stated before the cohort table was computed
# (prereg_3h_boomcat.md P9): this parse's action rate at or below HALF the
# character's own typical rate.
APM_RATIO_BOUND = 0.5

# 🆕 3i D8 — provenance stated, not invented alongside its result: this is
# CLAUDE.md's own capture-validity rule ("flag any conclusion drawn from
# under ~60 s of data as provisional"), applied here as an admissibility
# predicate rather than a footnote. The constant predates this tool.
MIN_PARSE_SECONDS = 60.0

# Effect types excluded from the cast-time count (mechanical, not name-based):
# 28 = SPELL_EFFECT_SUMMON, 24 = SPELL_EFFECT_CREATE_ITEM (conjures).
_NON_COMBAT_EFFECTS = {24, 28}

# 🆕 3i D6 — the stamped thresholds this module's constants must equal.
# predictions/CALIBRATION_TOLERANCE.md successor #3's predicate list, as text
# fragments to locate and the constant each must match.
_STAMP_PATH = (Path(__file__).resolve().parents[2] / "predictions"
              / "CALIBRATION_TOLERANCE.md")

# 🛑 3j A3 (`AUDIT_3I_ADVERSARIAL` §5) — THE SECTION THE STAMP LIVES IN.
# The `3i` check regex-matched three numbers ANYWHERE in the file, which the
# audit demonstrated to be a false green: deleting the ENTIRE stamped
# predicate-1 block (lines 317-322) left it PASSING, because the regex then
# matched the D7 correction's own *quotation* of P9 thirty-six lines below and
# still returned 0.5. An assertion that passes on a document which no longer
# stamps the rule is not an assertion.
#
# The block is bounded by its own heading and the next `###`, so a stamp that
# is deleted, renamed or moved out of successor #3 makes the check FAIL to
# find its section rather than silently find a lookalike elsewhere.
_STAMP_SECTION_HEADING = r"^###\s*🛑\s*Stamped successor #3: parse admissibility"

_STAMP_CHECKS = [
    ("APM ratio", r"APM ratio\s*[≤<=]+\s*([\d.]+)", APM_RATIO_BOUND),
    ("cast-time entries", r"[≤<=]+\s*(\d+)\s*cast-time combat entries",
     MAX_CAST_TIME_ENTRIES),
    ("parse window", r"Parse window\s*<\s*(\d+)\s*s", MIN_PARSE_SECONDS),
    # 🆕 3j A3 — the comparator FLOOR, which D5 changed under an unchanged
    # stamp and the 3i check was structurally blind to. Amended into the stamp
    # by owner decision 2026-08-07 (stamp-follows-code).
    ("comparator floor", r"is at least\s*\*\*(\d+)\s*s\*\*\s*long",
     MIN_PARSE_SECONDS),
    ("min comparators", r"Fewer than\s*\*\*(\d+)\*\*\s*qualifying comparators",
     2),
]

# 🆕 3j A3 — the two things D5 changed that are NOT numbers, and so cannot be
# caught by the numeric loop: the comparator DEFINITION and the comparison
# DIRECTION. Each is a fragment that must be PRESENT in the stamped section.
# `(label, pattern, why_it_matters)`.
_STAMP_PROSE_CHECKS = [
    ("comparator definition — qualifying, not all",
     r"other\s+\*\*qualifying\*\*\s+scopes",
     "D5 replaced 'the character's own other scopes' with a filtered subset "
     "and left the stamp saying 'other scopes'"),
    ("comparator definition — self-overlap excluded",
     r"shares no encounter with the scope under test",
     "a boss_group comparator containing the tested boss_single compares a "
     "parse against itself"),
    ("comparator definition — trash excluded",
     r"contains no trash encounter",
     "trash scopes are a different content type"),
    ("comparator definition — 0.0 admitted",
     r"0\.0 is admitted\*\*, not dropped",
     "`if (a := scope_apm(...))` silently dropped a legitimate 0.0"),
]

def flags_on_ratio(ratio):
    """The stamped predicate-1 comparison, in ONE place.

    🆕 `3j` A3 — extracted from `admissibility_for` so the comparison DIRECTION
    is testable. The stamp says **`≤`**, so a character sitting exactly on the
    bound is flagged; `AUDIT_3I` §5 lists the `<=` → `<` change at `:342` among
    the things the stamp assertion could not see, and a text match on the
    character "≤" would not have caught it either — the stamp is the thing
    being checked against, so it cannot also be the witness.
    """
    return ratio is not None and ratio <= APM_RATIO_BOUND


# 🆕 3j A3 — the direction, asserted BEHAVIOURALLY against the real predicate
# above rather than by re-reading the source or restating the operator. Writing
# this as `APM_RATIO_BOUND <= APM_RATIO_BOUND` would be a tautology — true of
# `<=`, `>=` and `==` alike, and green under the very mutation it names.
def _direction_is_inclusive():
    """Does a ratio EXACTLY equal to the bound flag? The stamp says it must."""
    return flags_on_ratio(APM_RATIO_BOUND) and not flags_on_ratio(
        APM_RATIO_BOUND + 1e-9)


def assert_stamped_thresholds():
    """3i D6 / 3j A3 — this module must equal the stamped predicate text, and
    the check must be ANCHORED to the section that stamps it.

    Registered mutation M33 (RUN 2026-08-07): set APM_RATIO_BOUND = 0.4 —
    goes RED, reporting stamped 0.5 vs module 0.4. Green path: the constants
    above, matched by construction (this IS the fix; a mismatch means either
    the stamp or the code drifted and both must be reconciled by hand, never
    silently reconciled by the assertion).

    🆕 Registered mutation M34 (RUN 2026-08-07, `3j` A3): delete the stamped
    successor-#3 section from `CALIBRATION_TOLERANCE.md`. Pre-3j this stayed
    GREEN — the file-wide regex found the D7 correction's quotation of the
    same numbers 36 lines further down. Now the section lookup fails first and
    every arm reports it. Green path: the section present, which is the fix.

    🆕 Registered mutation M35 (RUN 2026-08-07, `3j` A3): revert predicate 1's
    comparator wording to the un-amended *"the character's own other scopes"*.
    The four prose arms go RED — the two things D5 changed under an unchanged
    stamp are now visible to the check.
    """
    if not _STAMP_PATH.exists():
        print(f"🛑 [D6] cannot verify — {_STAMP_PATH} does not exist")
        return False
    whole = _STAMP_PATH.read_text(encoding="utf-8")

    # --- 3j A3: cut the stamped SECTION out first -------------------------
    m = re.search(_STAMP_SECTION_HEADING, whole, re.MULTILINE)
    if not m:
        print(f"🛑 [D6] FAIL — the stamped successor-#3 section was not found "
              f"in {_STAMP_PATH.name}. The rule this module implements is not "
              f"stamped anywhere; refusing to verify against the rest of the "
              f"file, which is where the false green came from (AUDIT_3I §5).")
        return False
    nxt = re.search(r"^###\s", whole[m.end():], re.MULTILINE)
    text = whole[m.start():m.end() + (nxt.start() if nxt else len(whole))]
    print(f"PASS  [D6] stamped section located: {len(text)} chars, "
          f"anchored to its own heading (not the whole file)")

    ok = True
    for label, pattern, module_value in _STAMP_CHECKS:
        m = re.search(pattern, text)
        if not m:
            print(f"🛑 [D6] FAIL — stamped text for {label!r} not found by "
                  f"pattern {pattern!r}; cannot verify")
            ok = False
            continue
        stamped_value = float(m.group(1))
        match = abs(stamped_value - float(module_value)) < 1e-9
        tag = "PASS" if match else "FAIL"
        print(f"{tag}  [D6] {label}: stamped {stamped_value:g} == "
              f"module {float(module_value):g}")
        ok = ok and match

    for label, pattern, why in _STAMP_PROSE_CHECKS:
        present = re.search(pattern, text) is not None
        print(f"{'PASS' if present else 'FAIL'}  [D6] {label}"
              + ("" if present else f" — MISSING from the stamped section. {why}"))
        ok = ok and present

    inclusive = _direction_is_inclusive()
    print(f"{'PASS' if inclusive else 'FAIL'}  [D6] comparison direction: a "
          f"ratio exactly equal to the bound flags (stamped '≤')")
    return ok and inclusive


class AdmissibilityOutage(RuntimeError):
    """The admissibility computation cannot produce a PER-PARSE verdict.

    🛑 `3j` Block 0 (`AUDIT_3I_ADVERSARIAL` §2). Raised — never returned as a
    per-character flag — when the thing that failed is the **labelling
    infrastructure** rather than any character's parse.

    `CLAUDE.md`'s standing rule: *a character may be excluded from the gate for
    what its PARSE is, never for what its DELTA is*, and exclusion must rest on
    **input validity**. A `/api/phases` payload that no longer describes this
    server is not a statement about anybody's parse — it is an outage. Routing
    it through predicate 4 turned one infrastructure fault into 41 identical
    parse verdicts and published `0 of 36` as though it were a measurement.

    The correct response to an outage is to **decline to publish a number**.
    A gate that reports `0 of 36` because it could not resolve a phase is
    strictly worse than a gate that reports nothing, because the first is
    quotable.
    """


def assert_publishable(phase_ctx, rows=None):
    """Refuse to publish a gate number when the admissibility rule is blind.

    Two refusals, checked in this order:

    1. **Payload-level.** `phase_guard`'s `refuse_reason` is its verdict on the
       `/api/phases` payload — not on any capture. If it is set, no per-parse
       admissibility verdict is computable, so nothing may be published.
       Checked BEFORE the sim loop by the gate, so an outage costs seconds
       rather than a full cohort sim.
    2. **Cohort-level.** If every scored member carries the *same* flag string,
       that flag is describing the run, not the members. Same if every member is
       flagged at all: a rule that removes 100% of the cohort has measured
       nothing, and the number it leaves behind is an artifact of its own
       refusal.

    `rows` are `admissibility_for()` dicts; pass `None` to run check 1 only.
    A cohort of fewer than 2 scored members is exempt from check 2 — "every
    member shares a flag" is not evidence of anything at n=1.

    MUTATION THAT MAKES THIS FAIL (red): delete either `raise` below. The
    check (`check_refusals.py :: check_admissibility_outage_refuses`) then
    reports that a refused payload published a number. GREEN PATH: the raises
    as written — which IS the fix, not a stub: the gate calls this at both
    points and has no other route to a manifest.
    """
    _windows, _horizon, refuse_reason, _boundary = phase_ctx
    if refuse_reason:
        raise AdmissibilityOutage(
            f"the /api/phases payload cannot label anything: {refuse_reason}\n"
            f"This is an INFRASTRUCTURE refusal, not a parse verdict. The gate "
            f"refuses to publish a number rather than flag every cohort member "
            f"'unresolved phase' and report the residue as a measurement. Fix "
            f"the payload (re-crawl /api/phases; bump "
            f"season_config.EXPECTED_PHASE_NAME and re-derive the corpus if "
            f"the server flipped), then re-run.")
    if not rows or len(rows) < 2:
        return
    shared = set(rows[0].get("flags") or [])
    for r in rows[1:]:
        shared &= set(r.get("flags") or [])
    if shared:
        raise AdmissibilityOutage(
            f"every one of the {len(rows)} scored members carries the "
            f"identical admissibility flag(s) {sorted(shared)!r}. A flag that "
            f"is true of the whole cohort is describing the RUN, not the "
            f"parses — refusing to publish.")
    if all(r.get("not_admissible") for r in rows):
        raise AdmissibilityOutage(
            f"all {len(rows)} scored members are NOT ADMISSIBLE. The rule has "
            f"removed the entire cohort, so the gate would be reporting a "
            f"number computed over nobody — refusing to publish.")


def cast_time_entries(asc, bdb, snapshot_id):
    """How many of this board's resolved entries are cast-time combat spells.

    Resolution: snapshot_cards.spell_id -> spell_dbc_raw.casting_time_index ->
    dbc_spellcasttimes.base (ms). base > 0 = cast-time. Summons and conjures
    are excluded by effect type, never by name.

    ⚠ 3i D4 — FAIL-OPEN, by construction, in four places (unchanged from 3h;
    documented here rather than fixed, because the regime test's job is to
    ANSWER "is this instant-heavy", and every one of these treats an
    UNKNOWN card as instant): an unresolved snapshot_cards row never reaches
    this query; a card absent from spell_dbc_raw increments neither counter;
    a NULL/0 casting_time_index is not counted as cast-time; a card whose
    casting_time_index has no dbc_spellcasttimes row is not counted either.
    `resolved_entries` is returned so a caller can see WHEN this matters —
    resolved_entries << the card count on the snapshot means the regime
    verdict below is unverified, not confirmed instant.
    """
    rows = bdb.execute(
        "SELECT DISTINCT spell_id FROM snapshot_cards "
        "WHERE snapshot_id = ? AND spell_id IS NOT NULL",
        (snapshot_id,)).fetchall()
    n_cast, n_resolved = 0, 0
    for (sid,) in rows:
        r = asc.execute(
            "SELECT r.casting_time_index, r.effect_json "
            "FROM spell_dbc_raw r WHERE r.id = ?", (sid,)).fetchone()
        if r is None:
            continue
        n_resolved += 1
        cti, effect_json = r
        if not cti:
            continue
        base = asc.execute(
            "SELECT base FROM dbc_spellcasttimes WHERE id = ?",
            (cti,)).fetchone()
        if not base or not base[0] or base[0] <= 0:
            continue
        try:
            effects = json.loads(effect_json or "{}").get("Effect") or []
        except ValueError:
            effects = []
        if any(e in _NON_COMBAT_EFFECTS for e in effects):
            continue
        n_cast += 1
    return {"cast_time_entries": n_cast, "resolved_entries": n_resolved,
            "card_count": len(rows),
            "fraction": (n_cast / n_resolved) if n_resolved else None}


def scope_duration_seconds(bdb, scope_id):
    """Wall-clock seconds behind one capture scope (single or grouped)."""
    row = bdb.execute(
        "SELECT encounter_id, encounter_ids_json FROM capture_scopes "
        "WHERE scope_id = ?", (scope_id,)).fetchone()
    if row is None:
        return None
    enc_id, ids_json = row
    ids = [enc_id] if enc_id is not None else []
    if not ids and ids_json:
        try:
            ids = list(json.loads(ids_json) or [])
        except ValueError:
            ids = []
    if not ids:
        return None
    q = ",".join("?" * len(ids))
    tot = bdb.execute(
        f"SELECT SUM(duration_seconds) FROM encounters "
        f"WHERE encounter_id IN ({q})", ids).fetchone()[0]
    return tot


def _scope_encounter_ids(bdb, scope_id):
    row = bdb.execute(
        "SELECT encounter_id, encounter_ids_json FROM capture_scopes "
        "WHERE scope_id = ?", (scope_id,)).fetchone()
    if row is None:
        return set()
    enc_id, ids_json = row
    ids = {enc_id} if enc_id is not None else set()
    if not ids and ids_json:
        try:
            ids |= set(json.loads(ids_json) or [])
        except ValueError:
            pass
    return ids


def _scope_is_trash_free(bdb, encounter_ids):
    """3i D5 — a comparator scope is admissible only if NONE of its
    encounters are trash. Checked mechanically via `encounters.is_trash`,
    never by matching the `scope` string (the same discipline as everywhere
    else in this project: a structured flag, not a name)."""
    if not encounter_ids:
        return False
    q = ",".join("?" * len(encounter_ids))
    row = bdb.execute(
        f"SELECT SUM(COALESCE(is_trash, 0)) FROM encounters "
        f"WHERE encounter_id IN ({q})", list(encounter_ids)).fetchone()
    return bool(row and (row[0] or 0) == 0)


def scope_apm(bdb, character_id, scope_id):
    """This character's casts per minute over one scope. is_pet = 0 only."""
    dur = scope_duration_seconds(bdb, scope_id)
    if not dur:
        return None
    casts = bdb.execute(
        "SELECT SUM(casts) FROM ability_performance "
        "WHERE scope_id = ? AND character_id = ? AND is_pet = 0",
        (scope_id, character_id)).fetchone()[0]
    if casts is None:
        return None
    return 60.0 * casts / dur


def apm_ratio(bdb, character_id, scope_id, *, n_cast_time_entries):
    """This scope's APM over the median of the character's OTHER scopes.

    Returns a dict whose `ratio` is None — never a number — when the kit is
    outside the instant-heavy regime or fewer than 2 other scopes exist to
    define "typical".

    🆕 3i D5 — the comparator set is TIGHTENED, four ways:
      * excludes any scope with a trash encounter in it (`is_trash`, checked
        mechanically);
      * excludes any scope shorter than MIN_PARSE_SECONDS — a comparator
        drawn from noisy data is not "typical";
      * excludes any scope whose encounter set OVERLAPS the scope under
        test — a `boss_group` comparator that CONTAINS the tested
        `boss_single` encounter would compare a scope against itself;
      * no longer drops a comparator scope whose APM is legitimately 0.0 —
        the previous `if (a := scope_apm(...))` treated 0.0 as falsy and
        silently excluded it. Fixed to `is not None`.

    🛑 **3j A2 / P4 — the stated rationale for that last arm was INVERTED, and
    is corrected here rather than quietly reworded.** `3i` wrote that admitting
    a legitimately-0.0 comparator is *"exactly the death-deflation signal this
    predicate exists to detect."* It is not. **The deflation signal lives on the
    TESTED scope.** A 0.0 *comparator* drags the median toward zero, which
    RAISES `scope_apm / comparator_median` and therefore **hides** deflation —
    the opposite of what the sentence claimed.

    The fix is still right, for a reason that has nothing to do with which way
    it pushes the ratio: **a 0.0 APM comparator is DATA.** `if (a := ...)`
    could not distinguish "this scope has no casts" from "this scope has no
    duration", and silently dropping the first was a fail-open in the comparator
    set. Whether admitting it raises or lowers a given character's ratio is a
    property of that character, not an argument for the rule. Measured on the
    live cohort while `3j` ran the P1 counterfactual: 0.0 comparators are
    present and common (`Frediib`'s set contains `[0.0, 0.0, 0.1, 0.4, …]`,
    `Boomcat`'s `[0.0, 4.1, …]`), so this arm is load-bearing in both
    directions.

    ⚠ **And the filters are NOT one-way.** `AUDIT_3I` §4 argued each arm can
    only remove comparators and so can only remove flags. That holds for the
    `len(apms) < 2` escape hatch; it is **false of the median**. Removing
    LOW-APM comparators raises the median and lowers the tested ratio, which
    can add a flag. Counterexample registered in advance
    (`predictions/prereg_3j_comparator.md` P3) and RUN as
    `check_refusals.py :: check_comparator_can_add_a_flag`: tested 8 APM,
    qualifying comparators 18/20, sub-60s comparators 2/3 — 0.762 admissible
    unfiltered, **0.421 flagged filtered**. The live cohort shows the same
    thing at smaller scale: D5 moved `Boomcat`'s ratio 0.27 → 0.24, i.e.
    *toward* the bound, not away from it.
    """
    out = {"scope_apm": scope_apm(bdb, character_id, scope_id),
           "n_cast_time_entries": n_cast_time_entries,
           "in_regime": n_cast_time_entries <= MAX_CAST_TIME_ENTRIES,
           "other_scope_apms": [], "comparator_median": None,
           "n_comparator_scopes_seen": 0, "n_comparator_scopes_excluded": 0,
           "ratio": None, "reason": None}
    if not out["in_regime"]:
        out["reason"] = (f"{n_cast_time_entries} cast-time combat entries > "
                         f"{MAX_CAST_TIME_ENTRIES} — casts under-counts this "
                         f"kit, ratio refused")
        return out
    if out["scope_apm"] is None:
        out["reason"] = "no casts or no duration for this scope"
        return out
    target_encs = _scope_encounter_ids(bdb, scope_id)
    others = [s for (s,) in bdb.execute(
        "SELECT DISTINCT scope_id FROM ability_performance "
        "WHERE character_id = ? AND scope_id != ? AND is_pet = 0",
        (character_id, scope_id)).fetchall()]
    out["n_comparator_scopes_seen"] = len(others)
    apms = []
    for s in others:
        encs = _scope_encounter_ids(bdb, s)
        dur = scope_duration_seconds(bdb, s)
        if encs & target_encs:
            continue                        # self-overlap
        if not dur or dur < MIN_PARSE_SECONDS:
            continue                        # too short to be "typical"
        if not _scope_is_trash_free(bdb, encs):
            continue                        # trash-tainted
        a = scope_apm(bdb, character_id, s)
        if a is not None:                   # 🛑 NOT `if a:` — 0.0 is data
            apms.append(a)
    out["n_comparator_scopes_excluded"] = len(others) - len(apms)
    out["other_scope_apms"] = sorted(round(a, 1) for a in apms)
    if len(apms) < 2:
        out["reason"] = (f"only {len(apms)} qualifying other scope(s) (of "
                         f"{len(others)} seen) — no 'typical rate' to "
                         f"compare against, ratio refused")
        return out
    out["comparator_median"] = statistics.median(apms)
    out["ratio"] = out["scope_apm"] / out["comparator_median"]
    return out


def admissibility_for(bdb, asc, phase_ctx, *, character_id, character_name,
                      snapshot_id, scope_id, window_s, snapshot_lag_hours):
    """3i — the single admissibility computation. Called by THIS tool's own
    `main()` and by `calibrate_crawled.py`'s gate loop, so the two can never
    disagree about which characters are flagged.

    `phase_ctx` is `(windows, horizon, refuse_reason, boundary)` from
    `ingest.logs_gg.build_builds_db.latest_phase_context()` — computed ONCE
    by the caller and passed in, so a per-character loop does not re-read
    the crawl files per row.

    Returns a dict with `not_admissible: bool`, `flags: [str]` (empty if
    admissible) and every diagnostic field D3 asks to be printed.
    """
    windows, horizon, refuse_reason, boundary = phase_ctx
    ct = cast_time_entries(asc, bdb, snapshot_id)
    ar = apm_ratio(bdb, character_id, scope_id,
                   n_cast_time_entries=ct["cast_time_entries"])
    deaths = bdb.execute(
        "SELECT MAX(deaths) FROM encounter_performance "
        "WHERE character_id = ? AND scope_id = ?",
        (character_id, scope_id)).fetchone()[0]

    # 🆕 3i D1 — predicate 4, COMPUTED via core.builds.phases.resolve_phase,
    # not printed as a sentence that becomes false at the 2026-08-08
    # boundary. Uses the snapshot's own captured_at.
    #
    # 🛑 3j Block 0 (`AUDIT_3I_ADVERSARIAL` §2) — `refuse_reason` is NO LONGER
    # passed down here. It is `phase_guard`'s verdict on the /api/phases
    # PAYLOAD ("this no longer describes the server we think we're pointed
    # at"), and `resolve_phase` checks it first, so passing it in made a
    # single infrastructure fault return NULL for every capture — every cohort
    # member flagged "unresolved phase", `within_tolerance` None for all 41,
    # and the gate publishing `0 of 36` as if it had measured something.
    #
    # A payload refusal is not a property of anybody's parse, so it is not a
    # predicate-4 input. It is surfaced as `phase_payload_refusal` and enforced
    # by `assert_publishable()`, which makes the RUN refuse. Predicate 4 keeps
    # exactly the capture-level reasons it was stamped for: no parseable
    # timestamp, past the declared boundary, past the payload's horizon,
    # before the first phase, or ambiguous across overlapping windows.
    captured_at = bdb.execute(
        "SELECT captured_at FROM character_snapshots WHERE snapshot_id = ?",
        (snapshot_id,)).fetchone()
    captured_at = captured_at[0] if captured_at else None
    phase_label, phase_reason = resolve_phase(
        captured_at, windows, horizon,
        refuse_reason=None, boundary=boundary)

    flags = []
    # 3j A3 — through `flags_on_ratio`, the single home of the stamped
    # comparison, so the direction is asserted rather than restated.
    if flags_on_ratio(ar["ratio"]):
        flags.append(f"apm_ratio {ar['ratio']:.2f} <= {APM_RATIO_BOUND:g}")
    if deaths and deaths > 0:
        flags.append(f"deaths {deaths}")
    if window_s is not None and window_s < MIN_PARSE_SECONDS:
        flags.append(f"window {window_s:.0f}s < {MIN_PARSE_SECONDS:g}s")
    # 🆕 3i D1 — predicate 4, now live. 🛑 3j Block 0: suppressed entirely
    # while the payload itself is refused — under an outage the honest per-
    # character answer is "not computed", not "this parse is inadmissible".
    # `assert_publishable()` stops the run before any of these rows is read.
    if refuse_reason is None and phase_label is None:
        flags.append(f"unresolved phase: {phase_reason}")
    # 🆕 3i D2 — predicate 5, TESTED rather than asserted inert. Stated as
    # inert-by-construction in the stamp (lag 0 is enforced at selection);
    # this makes that a checked fact, not an assumption, so a future
    # candidates() change that loosens --max-lag-hours cannot silently
    # smuggle a stale build past this predicate.
    if snapshot_lag_hours is not None and snapshot_lag_hours > 0:
        flags.append(f"snapshot lag {snapshot_lag_hours:.1f}h > 0h")

    return {
        "character_id": character_id, "name": character_name,
        "window_s": window_s, "snapshot_lag_h": snapshot_lag_hours,
        "cast_time_entries": ct["cast_time_entries"],
        "resolved_entries": ct["resolved_entries"],
        "card_count": ct["card_count"],
        "apm": ar["scope_apm"], "apm_ratio": ar["ratio"],
        "apm_reason": ar["reason"], "in_regime": ar["in_regime"],
        "comparator_median": ar["comparator_median"],
        "other_scope_apms": ar["other_scope_apms"],
        "n_comparator_scopes_seen": ar["n_comparator_scopes_seen"],
        "n_comparator_scopes_excluded": ar["n_comparator_scopes_excluded"],
        "deaths": deaths,
        "phase_label": phase_label, "phase_reason": phase_reason,
        # 🆕 3j Block 0 — the payload-level refusal, reported ALONGSIDE the
        # per-parse verdict and never folded into it. Non-None means no row in
        # this table is a measurement; `assert_publishable()` raises on it.
        "phase_payload_refusal": refuse_reason,
        "not_admissible": bool(flags), "flags": flags,
    }


def main():
    if not BUILDS_DB_PATH.exists():
        print(f"{BUILDS_DB_PATH} missing — run ingest/logs_gg/build_builds_db.py")
        return 1
    bdb = sqlite3.connect(BUILDS_DB_PATH)
    asc = connect(DB_PATH)

    if not assert_stamped_thresholds():
        print("\n🛑 REFUSING to compute admissibility — this module's "
              "constants disagree with the stamped predicate text in "
              f"{_STAMP_PATH}. Reconcile before trusting any number below.")
        return 1
    print()

    cohort_ids, _spec = cc.load_frozen_cohort(cc.COHORT_PATH)
    cands, dropped, _outside = cc.candidates(bdb, cohort_ids, 0.0)
    phase_ctx = latest_phase_context()
    windows, horizon, refuse_reason, boundary = phase_ctx
    print(f"[phase] {len(windows)} window(s), horizon "
          f"{horizon.isoformat() if horizon else 'UNKNOWN'}, "
          f"guard reason: {refuse_reason or '(none — payload consistent)'}, "
          f"boundary armed: {boundary.isoformat() if boundary else 'no'}")
    # 🛑 3j Block 0 — the same refusal the gate takes, so this tool and the
    # gate cannot disagree about whether the payload is fit to reason from.
    assert_publishable(phase_ctx)

    # ---- the BLIND table: parse properties only, no delta touched ---------
    print(f"\n[blind] predicates over all {len(cohort_ids)} frozen members "
          f"(tuning AND holdout — the rule must apply identically), computed "
          f"before any delta or verdict is read:")
    print(f"[blind] predicate 1: APM ratio <= {APM_RATIO_BOUND:g} inside the "
          f"instant-heavy regime (<= {MAX_CAST_TIME_ENTRIES} cast-time "
          f"combat entries)")
    print(f"[blind] predicate 2: deaths > 0 — encounter_performance.deaths is "
          f"ALL NULL today (declared, never written), so this predicate "
          f"removes nobody until D2 lands data")
    print(f"[blind] predicate 3: parse window < {MIN_PARSE_SECONDS:g}s "
          f"(CLAUDE.md's provisional-data floor)")
    print(f"[blind] predicate 4: capture resolves to no phase — COMPUTED via "
          f"core.builds.phases.resolve_phase (3i D1)")
    print(f"[blind] predicate 5: snapshot lag > 0h — TESTED, not assumed "
          f"(3i D2); the gate already enforces lag 0 at selection, so this "
          f"is expected to remove nobody by construction, and now checks "
          f"that rather than asserting it\n")

    seen = set()
    table = []
    for cand in cands:
        (cid, cname, snapshot_id, _dps, _path, _boss, _ctype, dur, _enc,
         lag, _lvl, scope_id, _lg) = cand
        if cid in seen:
            continue
        seen.add(cid)
        t = admissibility_for(bdb, asc, phase_ctx, character_id=cid,
                              character_name=cname, snapshot_id=snapshot_id,
                              scope_id=scope_id, window_s=dur,
                              snapshot_lag_hours=lag)
        t["holdout"] = cid in cc.HOLDOUT_IDS
        table.append(t)
        rat = f"{t['apm_ratio']:.2f}" if t["apm_ratio"] is not None else "None"
        cm = (f"{t['comparator_median']:.1f}"
              if t["comparator_median"] is not None else "n/a")
        print(f"  {cname:>14} ({cid}): window {dur:6.1f}s, "
              f"cast-time {t['cast_time_entries']:2d}/"
              f"{t['resolved_entries']:2d} resolved, "
              f"APM {t['apm'] and round(t['apm'], 1)!s:>6}, "
              f"comparator_median {cm:>6}, ratio {rat:>5} "
              f"({'REGIME' if t['in_regime'] else 'refused'}"
              + (f", n_others={len(t['other_scope_apms'])} "
                 f"(of {t['n_comparator_scopes_seen']} seen, "
                 f"{t['n_comparator_scopes_excluded']} excluded)"
                 if t["in_regime"] else "")
              + f", other_apms={t['other_scope_apms']})"
              + (f"  🛑 NOT ADMISSIBLE: {'; '.join(t['flags'])}"
                 if t["flags"] else ""))

    # ---- 3i D4 — the fail-open regime, counted and reported as a lower
    # bound rather than left implicit -----------------------------------
    out_of_regime = [t for t in table if not t["in_regime"]]
    escape_hatch = [t for t in table
                   if t["in_regime"] and t["apm_ratio"] is None
                   and t["apm_reason"] and "qualifying other scope" in t["apm_reason"]]
    unresolved_regime = [t for t in table
                         if t["resolved_entries"] < max(1, t["card_count"] // 2)]
    flagged = [t for t in table if t["not_admissible"]]
    print(f"\n[regime] {len(out_of_regime)} of {len(table)} boards are "
          f"OUT-OF-REGIME (predicate 1 structurally cannot flag them); "
          f"{len(escape_hatch)} are in-regime but hit the "
          f"< 2-comparator-scopes escape hatch (not in the stamped text); "
          f"{len(unresolved_regime)} have fewer than half their cards "
          f"resolved to a cast-time verdict (regime unverified, not "
          f"confirmed instant)")
    print(f"[blind] cohort effect: {len(flagged)} of {len(table)} members "
          f"flagged NOT ADMISSIBLE (None, never False): "
          + (", ".join(t["name"] for t in flagged) if flagged else "none"))
    assert_publishable(phase_ctx, table)     # 3j Block 0 — cohort-wide half
    print(f"🛑 [blind] {len(flagged)} of {len(table)} is a LOWER BOUND on "
          f"what the rule would flag with perfect information — it is a "
          f"measurement of how much the corpus is inadmissible ONLY where "
          f"predicate 1 can see the kit at all "
          f"({len(table) - len(out_of_regime)} of {len(table)} boards).")

    # ---- falsifiability — reads the committed manifest's verdicts, AFTER --
    print("\n[falsifiability] comparing against the committed manifest's "
          "verdicts (read only now, after the blind table above):")
    manifest = json.loads(
        cc.GATE_MANIFEST_PATH.read_text(encoding="utf-8"))
    verdicts = {r["character_id"]: r["within_tolerance"]
                for r in manifest.get("cohort", [])}
    removes_fail = [t for t in flagged
                    if verdicts.get(t["character_id"]) is False]
    removes_pass = [t for t in flagged
                    if verdicts.get(t["character_id"]) is True]
    removes_none = [t for t in flagged
                    if verdicts.get(t["character_id"]) is None]
    print(f"  removes FAILING characters: {len(removes_fail)} "
          f"({', '.join(t['name'] for t in removes_fail) or '-'})")
    print(f"  removes PASSING characters: {len(removes_pass)} "
          f"({', '.join(t['name'] for t in removes_pass) or '-'})")
    print(f"  removes NOT-SCOREABLE characters: {len(removes_none)} "
          f"({', '.join(t['name'] for t in removes_none) or '-'})")
    if removes_fail:
        print("  -> the rule is CAPABLE of removing a failing character "
              "(the D4 falsifiability bar).")
    elif flagged and not removes_fail:
        print("  🛑 the rule removes NO failing character — under D4 that is "
              "the fitting asymmetry: DO NOT STAMP; report and stop.")
    else:
        print("  -> the rule removes nobody at all on today's corpus.")
    print("\n[stamp] measurement only from this tool — APPLYING the rule to "
          "the gate itself happens in calibrate_crawled.py (3i D), which "
          "calls admissibility_for() directly.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
