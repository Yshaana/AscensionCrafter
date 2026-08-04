"""Does a damage coefficient change between ranks of the same spell? (session `1x`)

This settles the question `PHASE_1` T4 named as a blocker on the `spell_scaling`
schema, and that `PROGRESS.md` scheduled into `1x`. It had been answered "probably
not" from a **single** rank line (Holy Supernova, `EffectBonusCoefficient` identical
at R1 and R6), with the conclusion *"reading a coefficient off the catalog's Rank-1
entry is probably safe."*

## 🚨 The verdict: coefficients DO change with rank. That conclusion is falsified.

Measured across all 1,580 multi-rank lines with two or more members in
`spell_dbc_raw`:

| Evidence | constant across ranks | varies |
|---|---|---|
| numeric `EffectBonusCoefficient` | 696 | **169** |
| tooltip `$SP*`/`$AP*` literals | 132 | **34** |

110 of the 169 varying numeric lines follow a **ramp-then-plateau** shape.

The variation has a consistent shape — retail's low-rank penalty, which **ramps up
over the early ranks and then plateaus**: Frost Nova 0.018 → 0.043 → 0.193, Renew
0 → 0.291 → 0.376 (flat for ranks 3–14), Immolate 0.058 → 0.125 → 0.200 (flat for
ranks 3–11).

**That shape is what makes it dangerous rather than academic**, because the catalog
stores Rank 1 for ~697 entries — precisely the rank where the penalty is deepest.
Seven catalog entries are measurably affected today (both ranks state a coefficient
and the two disagree):

| Card | catalog (stored rank) | level-60 rank | factor |
|---|---|---|---|
| Sun Down | SP 0.4 | SP 1.3 | **3.25×** |
| Grasp of Darkness | SP 0.5 / AP 0.3 | SP 1.4 / AP 0.975 | **2.8×** |
| Spore | AP 0.08 | AP 0.13 | 1.63× |
| Fulmination | SP 0.28 / AP 0.18 | SP 0.38 / AP 0.245 | 1.36× |
| Seismic Tremor | AP 0.15 | AP 0.2 | 1.33× |
| Bone Spear | SP/AP 0.05 | SP/AP 0.04–0.1 | shape changes |
| Spirit Charge | SP 0.2 | AP 0.2 | **term type changes** |

Seven is a floor, not a total: 547 of the affected entries state no coefficient in
either rank's text, so nothing can be compared for them.

**Consequence for the schema: `spell_scaling` needs rank keying.** Recorded here and
in `seed_confirmed.py`; the migration itself belongs to T4 in session `1b`, which
rebuilds the table anyway (owner decision, 2026-08-04).

## ⚠ On the two evidence sources, and why both are reported separately

The numeric column is the **only** one that satisfies §2.2 tier 4 — but it is also
the field session `1x` established is *not* the SP/AP coefficient Ascension actually
applies (see `dbc_numeric.py`). The tooltip literals **are** the coefficients the
server applies, and they are the source every existing `spell_scaling` row already
came from — but they are text.

So neither source alone carries the claim, and this module never merges them into
one number. It reports both, tier-labelled, and they agree on direction. Where a
value has to be *used* rather than compared, the numeric field is the citable one
and the text stays a tier-6 signal (§2.2).
"""
import json

from .ranks import DEFAULT_LEVEL, catalog_rank_gaps
from .text_extraction import AP_PAT, RAP_PAT, SP_PAT

# tolerance for calling two floats the same coefficient; well below the smallest
# real difference seen (Fulmination 0.28 vs 0.38) and above float noise
EPSILON = 1e-4


def _text_coefficients(description):
    """`{term: (values...)}` for `$SP*x` / `$AP*x` / `$RAP*x` literals in raw text.

    ⚠ Text, not a numeric field — tier 6. Used **only** to compare one rank's text
    against another's, never emitted as a stored magnitude. The hard rule this
    project enforces ("never read a magnitude from a DBC description") is about
    trusting that text as a *value*; comparing two descriptions for equality makes
    no such claim.
    """
    text = description or ""
    return {
        "SP": tuple(sorted({round(float(v), 6) for v in SP_PAT.findall(text)})),
        "AP": tuple(sorted({round(float(v), 6) for v in AP_PAT.findall(text)})),
        "RAP": tuple(sorted({round(float(v), 6) for v in RAP_PAT.findall(text)})),
    }


def _numeric_coefficients(effect_json):
    values = (json.loads(effect_json) if effect_json else {}).get("EffectBonusCoefficient") or []
    return tuple(round(float(v), 6) for v in values)


def line_members(conn, line_id):
    """Every member of a rank line that has a DBC record, lowest rank first."""
    rows = conn.execute(
        """SELECT r.spell_id, r.rank, r.spell_level, d.name, d.effect_json, d.description
           FROM dbc_spell_rank r JOIN spell_dbc_raw d ON d.id = r.spell_id
           WHERE r.line_id = ? ORDER BY r.rank""",
        (line_id,),
    ).fetchall()
    return [{
        "spell_id": r[0], "rank": r[1], "spell_level": r[2], "name": r[3],
        "numeric": _numeric_coefficients(r[4]),
        "text": _text_coefficients(r[5]),
    } for r in rows]


def classify_line(members):
    """How does this line's coefficient behave across its ranks?

    Returns a dict with a verdict for each evidence source:
    `constant` · `varies` · `no_data`, plus `ramps_then_plateaus` when the numeric
    series only ever increases and settles — retail's low-rank penalty shape.
    """
    numeric = [m["numeric"] for m in members]
    text = [m["text"] for m in members]

    if all(all(v == 0 for v in n) for n in numeric):
        numeric_verdict = "no_data"
    elif len(set(numeric)) == 1:
        numeric_verdict = "constant"
    else:
        numeric_verdict = "varies"

    if all(all(len(v) == 0 for v in t.values()) for t in text):
        text_verdict = "no_data"
    elif len({tuple(sorted(t.items())) for t in text}) == 1:
        text_verdict = "constant"
    else:
        text_verdict = "varies"

    # a ramp: first-effect coefficient never decreases with rank, and the last two
    # ranks are equal (it has settled)
    firsts = [n[0] if n else 0.0 for n in numeric]
    ramps = (numeric_verdict == "varies" and len(firsts) > 2
             and all(b >= a - EPSILON for a, b in zip(firsts, firsts[1:]))
             and abs(firsts[-1] - firsts[-2]) < EPSILON)

    return {
        "numeric": numeric_verdict,
        "text": text_verdict,
        "ramps_then_plateaus": ramps,
        "member_count": len(members),
    }


def scan_rank_lines(conn, min_members=2):
    """Yield `(line_id, name, members, classification)` for every multi-rank line.

    Only lines with at least `min_members` records present in `spell_dbc_raw` are
    scanned — a line whose siblings were never extracted cannot answer the question,
    and counting it as "constant" would quietly inflate the reassuring number.
    """
    line_ids = [r[0] for r in conn.execute(
        """SELECT r.line_id FROM dbc_spell_rank r
           JOIN spell_dbc_raw d ON d.id = r.spell_id
           WHERE r.line_size > 1
           GROUP BY r.line_id HAVING COUNT(*) >= ?""", (min_members,))]
    for line_id in line_ids:
        members = line_members(conn, line_id)
        if len(members) < min_members:
            continue
        yield line_id, members[0]["name"], members, classify_line(members)


def catalog_coefficient_gaps(conn, level=DEFAULT_LEVEL):
    """Catalog entries whose stored coefficient differs from the one they cast.

    Built on `ranks.catalog_rank_gaps()` rather than re-deriving rank resolution, so
    the **ambiguous** lines it surfaces stay ambiguous here: an entry with more than
    one level-appropriate candidate is yielded with `ambiguous=True` and no verdict,
    never tie-broken (§2.3).

    ⚠ **Only `verdict == 'differs'` is evidence.** An entry where one rank states a
    coefficient and the other does not is `*_text_unresolved`, NOT a difference —
    measured causes, all three seen in real data:

      1. the higher rank writes a **compound form the regex cannot read**
         (`($SP+$AP)*0.36` on Bone Arrow) — a known `text_extraction` gap
      2. the formula moved into a **sub-spell** (`$71791m1` on Deep Freeze)
      3. the "line" pulled in a **different ability of the same name** (Blood
         Drinker's rank-4 record describes a Bloodthirst heal)

    Folding those into the headline would have turned 7 real differences into 15.
    """
    for gap in catalog_rank_gaps(conn, level):
        catalog_id = gap["catalog_spell_id"]
        if gap["ambiguous"]:
            yield {**gap, "verdict": "ambiguous", "catalog_text": None,
                   "live_text": None, "live_spell_id": None}
            continue

        live_id = gap["candidates"][0]["spell_id"]
        rows = {r[0]: r for r in conn.execute(
            "SELECT id, effect_json, description FROM spell_dbc_raw WHERE id IN (?,?)",
            (catalog_id, live_id))}
        if catalog_id not in rows or live_id not in rows:
            yield {**gap, "verdict": "not_extracted", "catalog_text": None,
                   "live_text": None, "live_spell_id": live_id}
            continue

        catalog_text = _text_coefficients(rows[catalog_id][2])
        live_text = _text_coefficients(rows[live_id][2])
        catalog_numeric = _numeric_coefficients(rows[catalog_id][1])
        live_numeric = _numeric_coefficients(rows[live_id][1])

        catalog_has = any(len(v) for v in catalog_text.values())
        live_has = any(len(v) for v in live_text.values())
        if not catalog_has and not live_has:
            verdict = "no_text_coefficient"
        elif catalog_text == live_text:
            verdict = "same"
        elif catalog_has and live_has:
            # both ranks state a coefficient and they disagree — the only case that
            # is actual evidence the coefficient changed with rank
            verdict = "differs"
        elif catalog_has:
            verdict = "live_text_unresolved"
        else:
            verdict = "catalog_text_unresolved"

        yield {**gap, "verdict": verdict, "live_spell_id": live_id,
               "catalog_text": catalog_text, "live_text": live_text,
               "numeric_differs": catalog_numeric != live_numeric}


def owned_spell_ids(conn):
    """The project owner's own card spellIds — for ranking a finding by whether it
    actually touches his build (§2.4's spirit: relevance over raw count)."""
    return {r[0] for r in conn.execute("SELECT DISTINCT spellId FROM owned_cards")}
