"""Phase 1 T10 — volatility scoring, Darkmoon-only, REPORT-ONLY (session 1c).

An ability with four nerfs in two seasons is a poor place to spend a Golden
guarantee slot. This module computes how often a spell has been patch-touched,
in which direction, and how recently — from `patch_entry_spells` ×
`patch_entries` × `patches`.

🛑 Report-only, per the phase doc and the owner: this NEVER enters optimizer
scoring or stat weights. It surfaces as a flag in `spell_profile()` and a note
in a guide, nothing more.

⚠ Scope decision (owner, 2026-08-05): **Darkmoon-tagged entries only, strict.**
The 2016→ corpus is rich but realm tags only exist from 2026 on Darkmoon
(~159 entries at decision time), and §2.5 forbids folding cross-realm history
into one realm's score. Consequence: the score is honest but THIN — the result
dict carries `data_window_days` and `data_thin` so a caller can never mistake
"no touches in a two-week window" for "stable for a year". The signal deepens
automatically as the season accrues.

"Does it get nerfed after becoming popular" needs the builds repo's popularity
timeline (Phase 3) and is deliberately not attempted here.

🆕 2e T9 (D7): the score is DECAY-WEIGHTED —
`weight = direction_mult × 0.5^(age_days/90)`, direction priors nerf 1.5 /
rework 1.25 / buff 0.75 / unknown 1.0. **Both the half-life and the multipliers
are stated priors, not fitted values** — the Darkmoon-tagged window is far too
thin to fit anything (see `data_thin`). Bands read off the weighted score.
Still Darkmoon-strict, still report-only.
"""
from datetime import date, datetime


def _parse_date(s):
    return datetime.strptime(s[:10], "%Y-%m-%d").date()


def volatility_score(conn, spell_id, lookback_days=365, realm="Darkmoon",
                     today=None):
    """Patch-touch history for one spell. Returns a dict; never raises on an
    unknown spell (a spell with no rows is simply untouched-in-window).

    `today` is injectable for tests; defaults to the current date.
    """
    today = today or date.today()

    window = conn.execute(
        """SELECT MIN(p.patch_date), MAX(p.patch_date)
           FROM patches p WHERE p.realm = ?""", (realm,)).fetchone()
    earliest, latest = window if window else (None, None)
    data_window_days = ((today - _parse_date(earliest)).days + 1) if earliest else 0

    rows = conn.execute(
        """SELECT p.patch_date, pe.change_direction, pe.status,
                  pes.confidence, pes.matched_name,
                  substr(pe.raw_text, 1, 200)
           FROM patch_entry_spells pes
           JOIN patch_entries pe ON pe.entry_id = pes.entry_id
           JOIN patches p ON p.patch_id = pe.patch_id
           WHERE pes.spell_id = ?
             AND p.realm = ?
             AND (pe.realms IS NULL OR pe.realms = '' OR pe.realms LIKE '%' || ? || '%')
           ORDER BY p.patch_date DESC""",
        (spell_id, realm, realm)).fetchall()

    cutoff = None
    in_window = []
    for r in rows:
        d = _parse_date(r[0])
        if (today - d).days <= lookback_days:
            in_window.append(r)
        elif cutoff is None:
            cutoff = r[0]

    by_direction = {}
    by_confidence = {}
    for r in in_window:
        by_direction[r[1] or "unclassified"] = by_direction.get(r[1] or "unclassified", 0) + 1
        by_confidence[r[3]] = by_confidence.get(r[3], 0) + 1

    n = len(in_window)
    last_touch = in_window[0][0] if in_window else None
    nerfs = by_direction.get("nerf", 0)
    buffs = by_direction.get("buff", 0)

    # ------------------------------------------------------------- 2e T9 (D7)
    # Decay-weighted score: weight = direction_mult × 0.5^(age_days / 90).
    # A nerf last week matters more than a buff last season — both the 90-day
    # half-life and the direction multipliers are STATED PRIORS, not measured
    # quantities (there is nowhere near enough Darkmoon-tagged history to fit
    # them; see `data_thin`). They are arguable and are meant to be argued with.
    #   nerf 1.5   — a nerf is evidence the devs think it is too strong,
    #                and further nerfs follow more often than reversals
    #   rework 1.25 — a rework destabilises verdicts in both directions
    #   buff 0.75  — a buff invalidates less of what we measured
    #   unknown 1.0
    DIRECTION_MULT = {"nerf": 1.5, "rework": 1.25, "buff": 0.75}
    HALF_LIFE_DAYS = 90.0
    weighted = 0.0
    for r in in_window:
        age = (today - _parse_date(r[0])).days
        weighted += (DIRECTION_MULT.get(r[1], 1.0)
                     * 0.5 ** (age / HALF_LIFE_DAYS))

    # Banded on the weighted score. Thresholds are the same stated-prior
    # calibration: one fresh nerf (1.5) alone lands 'active'; three fresh
    # touches land 'hot'; anything decayed below half a fresh touch is 'stable'.
    observed_days = min(lookback_days, data_window_days) or 1
    rate_per_90d = n * 90.0 / observed_days
    if n == 0:
        band = "untouched_in_window"
    elif weighted >= 3.0:
        band = "hot"
    elif weighted >= 1.0:
        band = "active"
    else:
        band = "stable"

    return {
        "spell_id": spell_id,
        "realm": realm,
        "lookback_days": lookback_days,
        # honesty block — read this before reading the score
        "data_window_days": data_window_days,
        "data_window": [earliest, latest],
        "data_thin": data_window_days < lookback_days,
        "thinness_note": (
            f"Darkmoon-tagged patch data covers only {data_window_days} of the "
            f"requested {lookback_days} days — 'untouched' means untouched in "
            f"THAT window, not stable for a year"
            if data_window_days < lookback_days else None),
        # the actual signal
        "touches": n,
        "by_direction": by_direction,
        "by_match_confidence": by_confidence,
        "nerf_count": nerfs,
        "buff_count": buffs,
        "last_touched": last_touch,
        "days_since_last_touch": (today - _parse_date(last_touch)).days if last_touch else None,
        "touch_rate_per_90d": round(rate_per_90d, 2),
        # 2e T9: decay-weighted score (see the stated-priors comment above).
        # Bands read off this, not off the raw rate. Keep `data_thin` in view:
        # with a ~2-week tagged window nothing has meaningfully decayed yet, so
        # the honesty block stays until the window exceeds ~2 half-lives (180d).
        "weighted_score": round(weighted, 3),
        "weighting": "direction_mult x 0.5^(age_days/90); "
                     "priors nerf 1.5 / rework 1.25 / buff 0.75 / unknown 1.0 "
                     "(STATED, not fitted)",
        "band": band,
        "recent_entries": [
            {"date": r[0], "direction": r[1], "status": r[2],
             "match_confidence": r[3], "matched_name": r[4], "text": r[5]}
            for r in in_window[:10]],
        # 🛑 contract, restated where the data lands
        "report_only": True,
        "note": "Never enters optimizer scoring or stat weights (T10 hard rule).",
    }
