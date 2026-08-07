"""Realm / season / phase constants — the ONE place these are written down.

Sibling of `config.py` (which owns filesystem layout). Same layering rule:
**`core/` may NOT import this module.** `core/` takes realm and season as
parameters with defaults; only `ingest/`, `cli/`, `tools/` and `api/` — the
layers allowed to know which server this clone is pointed at — import from here.

Why this exists (session `3d`, Block A1). These constants were hardcoded in
**five** places (`tools/scrapers/crawl_ascensionlogs.py:82`, `cli/mechanics.py:38`,
`cli/relationships.py:30`, `ingest/dbc/resolve_numeric_formulas.py:56`,
`ingest/changelog/ingest_changelog.py:52`) with nothing checking any of them
against the live server. **Phase 2 flips on 2026-08-08**, and the failure mode
of a stale constant is silent: every record captured after the flip is stamped
against a phase that has ended, and nothing says so.

---

## What this module can and cannot verify

🛑 **Read this before adding an assertion — it is the honest boundary.**

The logs API's `/api/phases` response states **phases**. It does **not** state a
realm and it does **not** state a season. So:

* **`REALM_SLUG` IS checkable** — it is the subdomain the crawler talks to, so
  the constant and the URL must agree or one of them is wrong. `assert_realm()`.
* **`EXPECTED_PHASE_NAME` IS checkable** — `assert_phase()` compares it against
  the live active top-level phase and hard-fails on a mismatch. This is what
  makes the 2026-08-08 flip **self-announcing**.
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
# 🚨 Phase 2 is scheduled for 2026-08-08. When it lands, `assert_phase()` fails
# loudly with the live name in the message. That is the intended behaviour:
# update this constant and `SEASON`/`SEASON_NUMBER` if the season also rolled,
# in ONE place, then re-run.
EXPECTED_PHASE_NAME = "Phase 1 - Zul'Gurub"

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
NEXT_PHASE_BOUNDARY = "2026-08-07T17:00:00Z"    # was 2026-08-08T00:00:00Z


class RealmSeasonMismatch(RuntimeError):
    """The clone's declared server state disagrees with the live server.

    Always fatal. Never downgrade this to a warning: the whole point is that a
    stale constant must stop the capture rather than mis-stamp a day of records.
    """


def active_phases(payload):
    """Every active phase in a `/api/phases` payload, top-level and child."""
    return [p for p in (payload or {}).get("phases", []) if p.get("is_active")]


def active_top_level_phases(payload):
    """Active phases with no progression parent — the real 'what phase is the
    server on' answer. Child phases (`progression_parent_phase_id` set) are
    content patches inside their parent, not phases in this sense."""
    return [p for p in active_phases(payload)
            if p.get("progression_parent_phase_id") in (None, 0)]


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

    Raises RealmSeasonMismatch on any of: no payload, no active top-level phase,
    more than one, or a name mismatch. Returns the matched phase dict.

    🚨 This is the 2026-08-08 tripwire. A phase flip is not an error in the
    server — it is an error in THIS CLONE'S CONSTANTS, and the message says so.
    """
    if not payload or not payload.get("phases"):
        raise RealmSeasonMismatch(
            "/api/phases returned no phases. Either the endpoint changed shape "
            "or the request failed — refusing to stamp records against an "
            "unverified phase."
        )
    tops = active_top_level_phases(payload)
    if len(tops) != 1:
        names = [p.get("name") for p in tops]
        raise RealmSeasonMismatch(
            f"expected exactly ONE active top-level phase, found {len(tops)}: "
            f"{names}. Live payload: {describe_phases(payload)}. This is either "
            f"a phase transition in progress or a schema change; resolve it by "
            f"hand before capturing."
        )
    live = tops[0]
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
