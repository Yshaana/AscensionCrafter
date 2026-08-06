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
against the captured payloads on 2026-08-06, `/api/phases` returns exactly
three records — Phase 0 (`2026-07-24T00:00Z`), Phase 1 - Zul'Gurub
(`2026-07-31T18:00Z`, active) and Phase 1.1 (a child). The 2026-08-08 Phase 2
boundary appears **nowhere in the API**; its only source in the tree is the
`user_confirmed` seed in `server_phases` and `season_config`. So this module
resolves what the API actually states and returns NULL past the edge of what
the payload could know — see `resolve_phase`'s horizon rule. It does not
invent the flip, and it does not read the seeded date.

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


def resolve_phase(captured_at, windows, horizon):
    """`(label, reason)` — the phase this timestamp fell in, or `(None, why)`.

    🛑 **EXACTLY ONE WINDOW, OR NOTHING.** Rule 2: unconfirmed is flagged, never
    defaulted, and never assigned to the nearest phase. The four ways to get
    NULL are each named, because "excluded" and "excluded for THIS reason" are
    different amounts of information when a phase-scoped query reports how much
    of its population it dropped.

    The horizon rule is the one that matters this week: a timestamp AFTER the
    phases payload was fetched cannot be resolved by that payload, even though
    the last window looks open-ended. Resolving it would silently label
    post-flip captures as Phase 1 — the exact silent mis-read this task exists
    to prevent, arriving through the back door.
    """
    ts = _parse_ts(captured_at)
    if ts is None:
        return None, "no parseable capture timestamp"
    if not windows:
        return None, "no phase windows could be built from the payload"
    if horizon is not None and ts > horizon:
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
