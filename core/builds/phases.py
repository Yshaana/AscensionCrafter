"""`3f` F8b — resolve a capture timestamp to the server phase it fell in.

**Owner decision 2026-08-06** (`ADDENDUM_3E_to_3F.md` §2.2): `gear_tier_stats`
must neither blend phases silently nor refuse. It derives `phase_label`, and a
snapshot that cannot be resolved to **exactly one** phase gets NULL and is
**excluded** from a phase-scoped query — never assigned to the nearest phase.

Why this is a join and not a new source: every snapshot already carries a
capture timestamp, and `/api/phases` carries each phase's `start_date`, which
`crawl_ascensionlogs.py` already fetches to run its own assertion. Both halves
were in hand.

🛑 **READ `progression_parent_phase_id`, NEVER `phase_number`.** The live
record whose `phase_number` is 2 is *named* "Phase 1.1" and is a **child** of
Phase 1, not the Phase 2 content launch. `PROGRESS.md` recorded that trap on
2026-08-04 and `season_config` already honours it; so does this.

🚨 **THE FIELD IS `start_date`, AND THERE IS NO PHASE 2 RECORD YET.** Measured
against the captured payloads on 2026-08-06 and re-checked live on 2026-08-07,
`/api/phases` returns exactly three records — Phase 0 (`2026-07-24T00:00Z`),
Phase 1 - Zul'Gurub (`2026-07-31T18:00Z`, active) and Phase 1.1 (a child). The
2026-08-08 Phase 2 boundary appears **nowhere in the API**; its only source in
the tree is the `user_confirmed` seed in `server_phases` and `season_config`.

🚨 **`3g` G0 — THE HORIZON RULE DEFENDED AGAINST THE WRONG THING, AND IT IS
REPLACED BY A POSITIVE ASSERTION.** The horizon is *when we fetched*, not
*what the payload knows*. The first post-flip daily crawl appends a post-flip
payload (`crawl_phases()` writes before it asserts, deliberately, for the
daily crawler), the horizon jumps past the flip, Phase 1's window is still
`open_ended`, and **every post-flip capture up to that fetch time resolves to
`Phase 1 - Zul'Gurub`** — precisely the silent mis-read F8b exists to prevent,
arriving through a door the horizon does not cover. Reproduced by the `3f`
auditor against the committed payload.

Three defences now, and they are ordered so the widest fires first:

1. **`phase_guard()` — the payload's own phase set must agree with what this
   clone expects.** If the live active top-level phase is not the expected one
   (`3k` B0: the CURRENT one — the latest-starting active top-level, since
   actives accumulate — or two windows genuinely overlap), **every** label is
   NULL with that as the
   reason. Nothing compared the two before.
2. **A DECLARED boundary that the payload has not caught up to.** The
   child-phase precedent is the reason this exists: the server published its
   last content boundary (Phase 1.1) as a **child**, which `phase_windows`
   correctly drops — so a Phase 2 published the same way would be invisible to
   the resolver while `assert_phase()` still passes, and defence 1 would not
   fire either. A capture at or after a boundary no window has reached is NULL
   **regardless of fetch time**. The boundary **self-retires**: the moment the
   payload carries a top-level window starting at or after it, the payload has
   modelled it and the guard disarms itself.
3. **The horizon, which now fails CLOSED.** `horizon is None` used to fail
   open — `resolve_phase("2027-01-01…", w, None)` returned Phase 1.

⚠ **A position this module used to hold, and no longer does.** Its previous
docstring said it *"does not read the seeded date"*. That was the right
instinct about *coupling* and the wrong answer about *safety*: refusing to
know the boundary did not make the boundary go away, it just meant the one
case the module existed for was the case it could not see. The date is now a
**parameter with no default**, supplied by the caller (`ingest/` may import
`season_config`; `core/` still may not). Purity is preserved by the layering,
not by ignorance.

Pure logic (`core/` rules): takes records and returns labels. It never fetches,
never opens a file, and never reads a constant naming a date.
"""
from datetime import datetime, timezone


def _parse_ts(text):
    """An ISO-8601 timestamp from the API or the corpus, as aware UTC.

    The API writes `2026-07-31T18:00:00.000Z`; `character_snapshots.captured_at`
    writes the same shape. A naive value is TREATED AS UTC, because every
    timestamp in this corpus is stamped UTC by the crawler — unlike combat-log
    and stat-block times, which are client LOCAL and must never be mixed with
    these (see `seed_confirmed.py:47`).
    """
    if not text:
        return None
    s = str(text).strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return None
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


def phase_windows(payload, fetched_at):
    """`[{label, phase_number, starts_at, ends_at, open_ended}]`, in order.

    Built from TOP-LEVEL phases only (`progression_parent_phase_id is None`).
    Each phase runs from its own `start_date` up to the next one's — the API
    states `end_date` but leaves it null on live phases, so the successor's
    start is the reliable edge.

    `fetched_at` is the payload's own capture time and is **load-bearing**: the
    final window is open-ended in the data but can only be trusted up to the
    moment the payload was taken. A snapshot later than that may belong to a
    phase this payload has never heard of, which is exactly the 2026-08-08
    situation. That horizon is carried on the last window as `open_ended` and
    enforced in `resolve_phase`.
    """
    tops = [p for p in (payload or {}).get("phases", [])
            if p.get("progression_parent_phase_id") is None]
    rows = []
    for p in tops:
        start = _parse_ts(p.get("start_date"))
        if start is None:
            continue        # a phase with no stated start cannot bound anything
        rows.append({"label": p.get("name"),
                     "phase_number": p.get("phase_number"),
                     "starts_at": start,
                     "ends_at": _parse_ts(p.get("end_date")),
                     "open_ended": False})
    rows.sort(key=lambda r: r["starts_at"])
    for i, r in enumerate(rows):
        nxt = rows[i + 1]["starts_at"] if i + 1 < len(rows) else None
        if nxt is not None and (r["ends_at"] is None or r["ends_at"] > nxt):
            r["ends_at"] = nxt
        if i + 1 == len(rows) and r["ends_at"] is None:
            r["open_ended"] = True
    return rows, _parse_ts(fetched_at)


def describe_horizon(horizon):
    """The horizon as a short UTC string, or `"UNKNOWN"` when it is None.

    🛑 `3g` G0 — this exists because `build_builds_db.py:192` did
    `f"(horizon {horizon:%Y-%m-%d %H:%M}Z)"` on a value that is `None` whenever
    the payload's fetch time did not parse. That raises `TypeError`, so **the
    line reporting the failure was the line that crashed** — F5's exact crash
    class, reintroduced inside F8b's own code, in the session that fixed F5.

    It lives here rather than at the call site so it can be tested without
    running a corpus rebuild. A guard that cannot run must say so; a guard that
    cannot even print must not exist.
    """
    return f"{horizon:%Y-%m-%d %H:%M}Z" if horizon is not None else "UNKNOWN"


def _active_top_level(payload):
    """Active phases with no progression parent.

    Deliberately a local re-implementation of `season_config`'s function of the
    same shape: `core/` may not import `season_config`, and this is two lines
    of field access rather than a rule that could drift. The rule that COULD
    drift — which name to expect — is a parameter.

    🚨 **`3k` B0 — this is NOT "what phase is the server on" any more.** See
    `current_top_level()`.
    """
    return [p for p in (payload or {}).get("phases", [])
            if p.get("is_active")
            and p.get("progression_parent_phase_id") in (None, 0)]


def current_top_level(payload):
    """The active top-level phase with the LATEST `start_date` — the server's
    current phase — or `None` when the payload has no such record.

    🚨 **`3k` B0, owner decision 2026-08-07: TRANSITIONS ON THIS SERVER ARE
    ADDITIVE.** Content is added at a phase boundary and none is removed, so
    the number of *active* top-level phases grows with every phase and will
    keep growing. Measured on the live payload at `2026-08-07T19:20Z`, hours
    after the Molten Core boundary:

        id=2  "Phase 1 - Zul'Gurub"              parent=None  active=True
        id=3  "Phase 1.1"                        parent=2     active=True
        id=4  "Phase 2 - Molten Core / Onyxia"   parent=None  active=True

    Two active top-level phases, and Zul'Gurub is still `is_active` with a NULL
    `end_date` because Zul'Gurub is still open. **`is_active` means "this
    content is live", not "this is the current phase."**

    ⚠ This retires `3g` G0's `len(tops) != 1` predicate, which read exactly two
    actives as *"a phase transition in progress or a schema change"* and
    refused. That predicate was a **proxy** for the hazard, and the hazard is
    ambiguous *labelling*, not a count. The server's own modelling has now
    falsified the proxy: it would have NULLed every capture, permanently, from
    the first Molten Core crawl onward. The protection is not deleted — it
    moves to where it can still fire, on windows that genuinely overlap
    (`_overlapping_windows()` below), which is what "ambiguous" actually means.
    """
    dated = [(s, p) for p in _active_top_level(payload)
             if (s := _parse_ts(p.get("start_date"))) is not None]
    if not dated:
        return None
    return max(dated, key=lambda sp: sp[0])[1]


def _overlapping_windows(windows):
    """Pairs of top-level windows that cannot both be true, as label strings.

    This is where `len(tops) != 1` went. `phase_windows` closes each window at
    its successor's start, so the only way two windows can overlap after that
    normalisation is if two top-level phases claim the **same** `start_date` —
    which leaves the ordering between them, and therefore every label on either
    side, a guess. The `ends_at > next.starts_at` arm is belt-and-braces
    against a future change to `phase_windows`.
    """
    bad = []
    for a, b in zip(windows or [], (windows or [])[1:]):
        if a["starts_at"] == b["starts_at"] or (
                a["ends_at"] is not None and a["ends_at"] > b["starts_at"]):
            bad.append(f"{a['label']!r} vs {b['label']!r}")
    return bad


def phase_guard(payload, windows, *, expected_phase_name=None,
                unmodelled_boundary=None):
    """`(refuse_reason, armed_boundary)` — may this payload label anything?

    🛑 **`3g` G0 — this is the positive assertion the horizon rule was not.**
    It answers a question nothing in the tree asked before: *does the payload
    we are about to resolve against still describe the server this clone
    believes it is pointed at?* A payload that does not gets to label
    **nothing** — not "nothing after some date", nothing at all — because if
    the phase set has moved, we do not know which of its windows are still
    what they say they are.

    `expected_phase_name` is `season_config.EXPECTED_PHASE_NAME`, passed in.
    Passing `None` skips the check and says so by returning no reason; that is
    for the pure-logic tests, not for a caller with a real corpus.

    `unmodelled_boundary` is a DECLARED boundary date (ISO-8601) that the
    server has announced and the API does not yet carry —
    `season_config.NEXT_PHASE_BOUNDARY`. It is returned **armed** only while no
    top-level window has reached it. Once the payload carries a window starting
    at or after it, the payload has modelled the boundary and the guard
    disarms: the constant does not have to be removed by hand, and a clone that
    forgets to remove it is not punished with permanent NULLs.

    Why the boundary is needed at all, given defence 1: the server published
    its last content boundary as a **child** phase, which `phase_windows` drops
    and `assert_phase` ignores. A Phase 2 published the same way leaves the
    active top-level name unchanged — defence 1 sees nothing wrong, and without
    this the resolver would happily stretch Phase 1 across the flip.
    """
    if expected_phase_name is not None:
        if not (payload or {}).get("phases"):
            return ("the /api/phases payload carries no phases at all — "
                    "refusing to label any capture against it"), None
        clashes = _overlapping_windows(windows)
        if clashes:
            return (f"two top-level phases claim the same window "
                    f"({'; '.join(clashes)}) — the order between them, and so "
                    f"every label on either side, would be a guess. Every "
                    f"phase_label is NULL until it is resolved by hand"), None
        cur = current_top_level(payload)
        if cur is None:
            names = [p.get("name") for p in _active_top_level(payload)]
            return (f"the payload has no active top-level phase with a "
                    f"parseable start_date (active top-levels: {names}) — "
                    f"there is nothing to check the expected phase against"), None
        live = cur.get("name")
        if live != expected_phase_name:
            return (f"PHASE FLIP: the payload's active top-level phase is "
                    f"{live!r}, this clone expects "
                    f"{expected_phase_name!r}. Every phase_label is NULL until "
                    f"season_config.EXPECTED_PHASE_NAME is updated and the "
                    f"corpus re-derived — a mis-stamped phase cannot be "
                    f"repaired later"), None

    boundary = _parse_ts(unmodelled_boundary)
    if boundary is not None and any(w["starts_at"] >= boundary
                                    for w in (windows or [])):
        boundary = None         # the payload has caught up; disarm
    return None, boundary


def resolve_phase(captured_at, windows, horizon, *,
                  refuse_reason=None, boundary=None):
    """`(label, reason)` — the phase this timestamp fell in, or `(None, why)`.

    🛑 **EXACTLY ONE WINDOW, OR NOTHING.** Rule 2: unconfirmed is flagged, never
    defaulted, and never assigned to the nearest phase. The four ways to get
    NULL are each named, because "excluded" and "excluded for THIS reason" are
    different amounts of information when a phase-scoped query reports how much
    of its population it dropped.

    `refuse_reason` and `boundary` come from `phase_guard()` and are checked
    FIRST and SECOND, before any window is consulted. Their order is the point:
    a payload that no longer describes this server may label nothing, and a
    capture past a boundary the payload has not modelled may take no label even
    though the payload is otherwise fine.

    🛑 **`horizon is None` FAILS CLOSED** (`3g` G0). It used to fail open, so
    `resolve_phase("2027-01-01…", w, None)` returned Phase 1. `horizon` is
    `_parse_ts(fetched_at)`, which returns `None` for any unparseable fetch
    time — meaning the one input that says how far this payload can be trusted
    was missing, and the resolver answered anyway.
    """
    if refuse_reason:
        return None, refuse_reason
    ts = _parse_ts(captured_at)
    if ts is None:
        return None, "no parseable capture timestamp"
    if not windows:
        return None, "no phase windows could be built from the payload"
    if boundary is not None and ts >= boundary:
        return None, (f"captured {ts:%Y-%m-%d %H:%M}Z, at or after the declared "
                      f"phase boundary {boundary:%Y-%m-%d %H:%M}Z, which this "
                      f"/api/phases payload does not carry a phase for. The "
                      f"boundary may have been published as a CHILD phase, "
                      f"which is invisible to the resolver. Re-crawl "
                      f"/api/phases; if it now names the new phase, update "
                      f"season_config and re-derive")
    if horizon is None:
        return None, ("the phases payload has no parseable fetch time, so "
                      "there is no horizon past which it stops being "
                      "trustworthy — refusing to resolve rather than trusting "
                      "an open-ended window forever")
    if ts > horizon:
        return None, (f"captured {ts:%Y-%m-%d %H:%M}Z, AFTER the phases payload "
                      f"was fetched ({horizon:%Y-%m-%d %H:%M}Z) — that payload "
                      f"cannot know which phase this fell in. Re-crawl "
                      f"/api/phases and re-derive")
    hits = [w for w in windows
            if w["starts_at"] <= ts and (w["ends_at"] is None
                                         or ts < w["ends_at"])]
    if len(hits) == 1:
        return hits[0]["label"], None
    if not hits:
        return None, (f"captured {ts:%Y-%m-%d %H:%M}Z, before the first known "
                      f"phase started ({windows[0]['starts_at']:%Y-%m-%d %H:%M}Z)")
    return None, (f"captured {ts:%Y-%m-%d %H:%M}Z falls in {len(hits)} "
                  f"overlapping phase windows "
                  f"({', '.join(str(w['label']) for w in hits)}) — ambiguous, "
                  f"and picking one would be a guess")
