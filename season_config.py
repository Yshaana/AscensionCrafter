"""Realm / season / phase constants — the ONE place these are written down.

Sibling of `config.py` (which owns filesystem layout). Same layering rule:
**`core/` may NOT import this module.** `core/` takes realm and season as
parameters with defaults; only `ingest/`, `cli/`, `tools/` and `api/` — the
layers allowed to know which server this clone is pointed at — import from here.

Why this exists (session `3d`, Block A1). These constants were hardcoded in
**five** places (`tools/scrapers/crawl_ascensionlogs.py:82`, `cli/mechanics.py:38`,
`cli/relationships.py:30`, `ingest/dbc/resolve_numeric_formulas.py:56`,
`ingest/changelog/ingest_changelog.py:52`) with nothing checking any of them
against the live server. **Phase 2 landed 2026-08-07T18:00:00Z** (announced for
the 8th, arrived a day early — additively; see `EXPECTED_PHASE_NAME`'s note),
and the failure mode of a stale constant is silent: every record captured after
a flip is stamped against a phase that has ended, and nothing says so.

---

## What this module can and cannot verify

🛑 **Read this before adding an assertion — it is the honest boundary.**

The logs API's `/api/phases` response states **phases**. It does **not** state a
realm and it does **not** state a season. So:

* **`REALM_SLUG` IS checkable** — it is the subdomain the crawler talks to, so
  the constant and the URL must agree or one of them is wrong. `assert_realm()`.
* **`EXPECTED_PHASE_NAME` IS checkable** — `assert_phase()` compares it against
  the live active top-level phase and hard-fails on a mismatch. This is what
  makes a phase flip **self-announcing** — it fired for real on the 2026-08-07
  Molten Core boundary (`3k` B0), on the wrong arm; see `assert_phase`'s note.
* **`SEASON` IS NOT CHECKABLE from this endpoint.** Nothing in the payload
  names a season. It is a **declared** value, anchored only indirectly: the
  expected phase belongs to S10, so a phase mismatch is also the signal that the
  season constant needs re-examining. Do not write an assertion that appears to
  verify the season against data that does not carry it.

## `phase_number` is NOT the phase label

Measured on the live payload, 2026-08-06:

    id=2  phase_number=1  name="Phase 1 - Zul'Gurub"  parent=None   is_active=True
    id=3  phase_number=2  name="Phase 1.1"            parent=2      is_active=True

The record whose `phase_number` is 2 is named *"Phase 1.1"* and is a **child of
Phase 1**. Reading `phase_number` alone says the server is on Phase 2 today,
which is false. Always read `name` + `progression_parent_phase_id`
(START_HERE_FOR_CODE §Current state).
"""

from datetime import datetime

# --- realm -----------------------------------------------------------------
REALM_SLUG = "darkmoon"      # subdomain / API form:  darkmoon.ascensionlogs.gg
REALM = "Darkmoon"           # display + DB-stamp form (`patches.realm`, etc.)

# --- season ----------------------------------------------------------------
# ⚠ DECLARED, not verified — no endpoint we fetch states a season. See module
# docstring. Both forms exist because the crawler stamps an int and the Phase 1
# schema stamps a label; they must describe the same season.
SEASON_NUMBER = 10           # crawler record stamp
SEASON = "S10"               # `seasons.label` / DB-stamp form

# --- phase -----------------------------------------------------------------
# The active TOP-LEVEL phase this clone expects. Child phases (parent is not
# NULL, e.g. "Phase 1.1") are content patches within it and are allowed to come
# and go without touching this.
#
# 🚨 `3k` B0, 2026-08-07 — PHASE 2 HAS LANDED, and it landed additively.
# Molten Core / Onyxia opened at 2026-08-07T18:00:00Z as a TOP-LEVEL phase
# (id=4, parent=None) while `Phase 1 - Zul'Gurub` stayed `is_active` with a
# NULL `end_date`, because Zul'Gurub is still open. `is_active` on this server
# means "this content is live", NOT "this is the current phase" — see
# `core.builds.phases.current_top_level`. Owner decision 2026-08-07: the current
# phase is the **latest-STARTING active top-level**, and a COUNT is never the
# answer.
#
# ⚠ `3m` pre-flight, 2026-08-08 (`AUDIT_3L` F16) — THE RULE STANDS, THE STATED
# WARRANT DOES NOT. This note used to read *"transitions here are additive,
# raids get added and none removed, so the count will keep growing"*. **Zul'Gurub
# and Phase 1.1 both went `is_active: False` overnight** (`/api/phases` at
# `2026-08-08T06:05:56Z`, committed `7f28c4e`): the two-active overlap lasted
# **under ~12 hours**, not forever. So a count of 2 *does* mean a transition is
# in progress, and it *does* clear itself within about a day.
#
# Why the decision survives its own warrant: latest-starting-active-top-level
# returns Molten Core under BOTH regimes — during the overlap and after the
# removal — while `len(tops) != 1` would have NULLed every label for the whole
# overlap window. The predicate was retired for being unsatisfiable-in-the-
# moment, which is true regardless of whether the overlap is permanent. **Do not
# use "actives accumulate forever" to predict the next boundary's shape.**
#
# When the NEXT phase lands, `assert_phase()` still fails loudly with the live
# name in the message. Update this constant — and `SEASON`/`SEASON_NUMBER` if
# the season also rolled — in ONE place, then re-run.
EXPECTED_PHASE_NAME = "Phase 2 - Molten Core / Onyxia"

# The next content boundary the server has ANNOUNCED but `/api/phases` does not
# yet carry a phase record for. ISO-8601 UTC, or None when there is no such
# boundary outstanding.
#
# 🛑 DECLARED, not verified — same tier as SEASON. Nothing we fetch states it.
# It exists because `assert_phase()` and the phase resolver both read the
# payload, and the payload is exactly what a boundary published as a CHILD
# phase does not change: the server shipped its last content boundary
# ("Phase 1.1", `phase_number` 2) as a child of Phase 1, invisible to both.
# `core.builds.phases.phase_guard()` takes this as a parameter and NULLs every
# capture at or after it, regardless of when the payload was fetched.
#
# ✅ It SELF-RETIRES: once `/api/phases` carries a top-level phase starting at
# or after this date, the payload has modelled the boundary and the guard
# disarms itself. Leaving a stale value here costs nothing. Setting it to None
# when a boundary is outstanding costs a mis-stamped day.
NEXT_PHASE_BOUNDARY = "2026-08-07T18:00:00Z"    # 19:00 BST Molten Core unlock


class RealmSeasonMismatch(RuntimeError):
    """The clone's declared server state disagrees with the live server.

    Always fatal. Never downgrade this to a warning: the whole point is that a
    stale constant must stop the capture rather than mis-stamp a day of records.
    """


def active_phases(payload):
    """Every active phase in a `/api/phases` payload, top-level and child."""
    return [p for p in (payload or {}).get("phases", []) if p.get("is_active")]


def active_top_level_phases(payload):
    """Active phases with no progression parent. Child phases
    (`progression_parent_phase_id` set) are content patches inside their
    parent, not phases in this sense.

    ⚠ `3k` B0 — this is NOT 'what phase is the server on'; it returns a growing
    list. Use `current_top_level_phase()`."""
    return [p for p in active_phases(payload)
            if p.get("progression_parent_phase_id") in (None, 0)]


def current_top_level_phase(payload):
    """The active top-level phase with the LATEST `start_date`, or None.

    `3k` B0 — the crawler-side twin of `core.builds.phases.current_top_level`,
    duplicated for the same reason the other pair is: `core/` may not import
    this module. Both are three lines of field access over the same payload.
    Owner decision 2026-08-07: the current phase is the newest active top-level,
    never 'the only one'. ⚠ The *warrant* that decision was stated with
    ("transitions are additive, none removed") was falsified on 2026-08-08 —
    Zul'Gurub went inactive within ~12 h. The rule is unaffected: newest-active
    returns Molten Core both during the overlap and after. See the
    `EXPECTED_PHASE_NAME` note and `AUDIT_3L` F16.
    """
    dated = []
    for p in active_top_level_phases(payload):
        raw = str(p.get("start_date") or "").strip().replace("Z", "+00:00")
        try:
            dated.append((datetime.fromisoformat(raw), p))
        except ValueError:
            continue
    return max(dated, key=lambda sp: sp[0])[1] if dated else None


def describe_phases(payload):
    """One-line human summary, for the crawler's header. Never raises."""
    tops = active_top_level_phases(payload)
    kids = [p for p in active_phases(payload)
            if p.get("progression_parent_phase_id") not in (None, 0)]
    top_s = ", ".join(repr(p.get("name")) for p in tops) or "NONE"
    kid_s = ", ".join(repr(p.get("name")) for p in kids)
    return f"active top-level: {top_s}" + (f"; child: {kid_s}" if kid_s else "")


def assert_realm(base_url):
    """The realm constant must match the host actually being crawled.

    Raises RealmSeasonMismatch. Cheap, and it catches the copy-paste error of
    pointing a Dawnrise URL at a Darkmoon-stamped capture — which would produce
    records that are wrong in a way no downstream check could detect, since
    realm is the one axis balance changes diverge on (§2.5).
    """
    host = base_url.split("://", 1)[-1].split("/", 1)[0]
    if not host.startswith(f"{REALM_SLUG}."):
        raise RealmSeasonMismatch(
            f"REALM_SLUG={REALM_SLUG!r} does not match the crawl host {host!r}. "
            f"Every record this run would be stamped realm={REALM!r}. "
            f"Fix season_config.py or the URL — do not proceed."
        )


def assert_phase(payload):
    """The live server must still be on `EXPECTED_PHASE_NAME`.

    "Still on" means the CURRENT top-level phase — the active one with the
    latest `start_date` (`3k` B0: a COUNT is not the answer). Raises
    RealmSeasonMismatch on any of: no payload, no active top-level phase with a
    parseable start, or a name mismatch. Returns the matched phase dict.

    🚨 This is the phase-flip tripwire. It fired for real on the Molten Core
    boundary — though on the wrong arm: the old `len(tops) != 1` check caught
    the flip as "a transition in progress" and refused every label while the
    overlap lasted. ⚠ `3m` pre-flight correction (`AUDIT_3L` F16): the `3k`
    record said it "would have gone on refusing FOREVER, because Zul'Gurub never
    stopped being active" — Zul'Gurub **did** stop, ~12 h later. The refusal
    would have been temporary, not permanent. Retiring the arm was still right
    (it NULLs a live day's captures for no gain), but the reason is
    "unsatisfiable while it lasts", not "unsatisfiable forever". A phase flip is
    not an error in the server — it is an error in THIS CLONE'S CONSTANTS, and
    the message says so.
    """
    if not payload or not payload.get("phases"):
        raise RealmSeasonMismatch(
            "/api/phases returned no phases. Either the endpoint changed shape "
            "or the request failed — refusing to stamp records against an "
            "unverified phase."
        )
    live = current_top_level_phase(payload)
    if live is None:
        names = [p.get("name") for p in active_top_level_phases(payload)]
        raise RealmSeasonMismatch(
            f"no active top-level phase with a parseable start_date "
            f"(active top-levels: {names}). Live payload: "
            f"{describe_phases(payload)}. Resolve by hand before capturing."
        )
    if live.get("name") != EXPECTED_PHASE_NAME:
        raise RealmSeasonMismatch(
            f"PHASE FLIP DETECTED. season_config.EXPECTED_PHASE_NAME is "
            f"{EXPECTED_PHASE_NAME!r}; the server's active top-level phase is "
            f"{live.get('name')!r} (id={live.get('id')}, "
            f"phase_number={live.get('phase_number')}, "
            f"started {live.get('start_date')}). "
            f"Update season_config.py — EXPECTED_PHASE_NAME, and SEASON/"
            f"SEASON_NUMBER too if the season rolled — then re-run. Records are "
            f"NOT being captured until that is done, deliberately: a "
            f"mis-stamped day cannot be repaired later."
        )
    return live
