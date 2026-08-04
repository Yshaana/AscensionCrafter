"""Rank resolution — which spell rank does a character of level N actually cast?

**The rule (Phase 0, CONFIRMED):** the highest rank in the line whose `SpellLevel`
is ≤ the character's level. Reproduces all three in-game tooltips captured by the
owner (Holy Supernova R6, Winds of Winter R5, Arcane Intellect R5).

❌ **The contiguous-id rule is DISPROVEN and must not be reintroduced** — 4,791 rank
lines are non-contiguous versus 1,908 contiguous (Winds of Winter runs R1 `274121`
then R2–R8 at `274129`–`274135`). The primer §5 "check ±1–3 of an unresolved id"
heuristic worked only on the lines it happened to be tried on.

🚨 **Why this matters more than it looks:** 697 of the 1,409 catalog entries that sit
in a rank line are stored at a rank a level-60 character does not hold, and in all
697 the correct id is absent from `spell-export.json` entirely. Reading a flat
magnitude off such an entry is wrong by up to ~15×. Coefficients look safer —
`EffectBonusCoefficient` was identical at R1 and R6 on the one line measured — but
that is one line, not a law.

Lines come from `dbc_spell_rank`, grouped on (name, skill lines, mechanical
fingerprint) — never name alone.
"""

DEFAULT_LEVEL = 60  # Darkmoon's cap this season


def line_of(conn, spell_id):
    """The rank line a spell belongs to, or None if it carries no rank text."""
    row = conn.execute(
        "SELECT line_id, name, rank, spell_level, line_size FROM dbc_spell_rank WHERE spell_id = ?",
        (spell_id,),
    ).fetchone()
    if row is None:
        return None
    return {"line_id": row[0], "name": row[1], "rank": row[2],
            "spell_level": row[3], "line_size": row[4]}


def line_members(conn, line_id):
    """Every spell in a rank line, lowest rank first."""
    rows = conn.execute(
        "SELECT spell_id, rank, rank_text, spell_level, name FROM dbc_spell_rank "
        "WHERE line_id = ? ORDER BY rank",
        (line_id,),
    ).fetchall()
    return [{"spell_id": r[0], "rank": r[1], "rank_text": r[2],
             "spell_level": r[3], "name": r[4]} for r in rows]


def rank_for_level(conn, spell_id, level=DEFAULT_LEVEL):
    """The spell a character of `level` actually casts, given any id in the line.

    Returns a dict with the resolved member plus the id that was asked about, or
    None when the spell is not in a rank line at all (a single-rank ability — in
    which case the id you have IS the id you cast).
    """
    line = line_of(conn, spell_id)
    if line is None:
        return None
    row = conn.execute(
        "SELECT spell_id, rank, rank_text, spell_level FROM dbc_spell_rank "
        "WHERE line_id = ? AND spell_level <= ? ORDER BY rank DESC LIMIT 1",
        (line["line_id"], level),
    ).fetchone()
    if row is None:
        # every rank in the line gates above this level — the character holds none
        return {"queried_spell_id": spell_id, "line_id": line["line_id"],
                "name": line["name"], "spell_id": None, "rank": None,
                "rank_text": None, "spell_level": None,
                "gap": "no rank of this line is available at this level"}
    return {"queried_spell_id": spell_id, "line_id": line["line_id"], "name": line["name"],
            "spell_id": row[0], "rank": row[1], "rank_text": row[2], "spell_level": row[3],
            "gap": None}


def catalog_rank_gaps(conn, level=DEFAULT_LEVEL):
    """Catalog entries stored at a rank the character does not hold.

    Yields one dict per affected `spells.id`, carrying **every** level-appropriate
    candidate and whether that id is present in the catalog at all. This is the query
    behind the "≈50% of the multi-rank catalog carries the wrong magnitudes" finding —
    a function rather than a one-off script, because it must be re-run every time the
    export is refreshed.

    ⚠ **`ambiguous` is why this returns a list.** Some lines contain more than one
    spell at the same top rank available at this level, so "the level-60 id" is not
    unique. Two causes seen in real data: a line whose members all read "Rank 1"
    (`Desolation`, 5 members), and a line that pulls in an **other-realm variant**
    from the 11-prefix id space (`Arcane Focus` -> 912840 *and* 1212840). Phase 0's
    own reporter used `max()`, which silently returns the first of a tie and hides
    both cases; the counts it published (697) are therefore a lower bound. Surfacing
    the tie is §2.3's rule applied to rank resolution — an ambiguous answer is
    recorded as ambiguous, never resolved by list order.
    """
    sql = """
    SELECT s.id, s.name, sr.line_id, sr.rank, sr.spell_level, live.spell_id, live.rank,
           live.spell_level, (SELECT 1 FROM spells s2 WHERE s2.id = live.spell_id)
    FROM spells s
    JOIN dbc_spell_rank sr ON sr.spell_id = s.id
    JOIN (
        SELECT line_id, spell_id, rank, spell_level FROM dbc_spell_rank d
        WHERE d.spell_level <= :level
          AND d.rank = (SELECT MAX(rank) FROM dbc_spell_rank d2
                        WHERE d2.line_id = d.line_id AND d2.spell_level <= :level)
    ) live ON live.line_id = sr.line_id
    WHERE sr.line_size > 1 AND live.spell_id != s.id
    ORDER BY s.id, live.spell_id
    """
    grouped = {}
    for r in conn.execute(sql, {"level": level}):
        entry = grouped.setdefault(r[0], {
            "catalog_spell_id": r[0], "name": r[1], "line_id": r[2],
            "catalog_rank": r[3], "catalog_spell_level": r[4], "candidates": [],
        })
        entry["candidates"].append({
            "spell_id": r[5], "rank": r[6], "spell_level": r[7],
            "in_catalog": bool(r[8]),
        })
    for entry in grouped.values():
        entry["ambiguous"] = len(entry["candidates"]) > 1
        yield entry
