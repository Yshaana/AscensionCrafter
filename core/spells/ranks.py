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

    🚨 `3m` C4 (`AUDIT_3L` F6) — AN ENCHANT-DELIVERED LINE IS GATED BY THE
    ENCHANT, NOT BY `SpellLevel`, and the two disagree in real data.

    `rank_for_level(conn, 200824, 60)` returned **rank 5 (+40)** because rank 6's
    `SpellLevel` is 64 — while `3l` seeded, from two independent routes, that the
    owner holds **rank 6 (+86)**. Both were right about different gates: these
    spells are never *cast*, they are applied by `SpellItemEnchantment` rows
    (23387–23395), and it is `SpellItemEnchantment.min_level` that decides which
    one a character can have. Rank 6's enchant gates at **55**, rank 7's at 63 —
    so a level-60 character holds exactly rank 6, which is what was measured.

    Nothing recorded that the two gates disagreed, so the next caller through the
    canonical resolver got 40 and no warning. Now the enchant gate is used when
    the line is enchant-delivered, and `gate` names which rule answered — never
    silent either way.
    """
    line = line_of(conn, spell_id)
    if line is None:
        return None
    gate = "spell_level"
    row = None
    try:
        # Is this line delivered by an item enchant? `effect_args_json` holds the
        # hidden spell id an enchant applies. A line is enchant-delivered when
        # its members appear there; the join is on the ID, never on the name.
        row = conn.execute(
            "SELECT r.spell_id, r.rank, r.rank_text, r.spell_level "
            "FROM dbc_spell_rank r "
            "JOIN dbc_spellitemenchantment e "
            "  ON json_extract(e.effect_args_json, '$[0]') = r.spell_id "
            "WHERE r.line_id = ? AND e.min_level <= ? "
            "ORDER BY r.rank DESC LIMIT 1",
            (line["line_id"], level),
        ).fetchone()
        if row is not None:
            gate = "spellitemenchantment.min_level"
    except Exception:                                     # noqa: BLE001
        # No enchant table in this clone (a DB built without the 3l extract).
        # Fall through to the SpellLevel gate rather than refusing — but the
        # `gate` field still says which rule produced the answer.
        row = None
    if row is None:
        row = conn.execute(
            "SELECT spell_id, rank, rank_text, spell_level FROM dbc_spell_rank "
            "WHERE line_id = ? AND spell_level <= ? ORDER BY rank DESC LIMIT 1",
            (line["line_id"], level),
        ).fetchone()
    if row is None:
        # every rank in the line gates above this level — the character holds none
        return {"queried_spell_id": spell_id, "line_id": line["line_id"],
                "name": line["name"], "spell_id": None, "rank": None,
                "rank_text": None, "spell_level": None, "gate": gate,
                "gap": "no rank of this line is available at this level"}
    gap = None
    if gate == "spellitemenchantment.min_level" and row[3] is not None             and row[3] > level:
        # Named, not silent: the answer is the enchant gate's, and it disagrees
        # with SpellLevel. This is the 200824 case (rank 6, SpellLevel 64,
        # enchant min_level 55) and it is CORRECT — the measurement says +86.
        gap = (f"resolved by the ENCHANT gate (min_level) to rank {row[1]}, "
               f"whose SpellLevel is {row[3]} > {level}. These spells are "
               f"applied by SpellItemEnchantment, never cast, so SpellLevel is "
               f"the wrong gate here (3m C4 / AUDIT_3L F6)")
    return {"queried_spell_id": spell_id, "line_id": line["line_id"], "name": line["name"],
            "spell_id": row[0], "rank": row[1], "rank_text": row[2], "spell_level": row[3],
            "gate": gate, "gap": gap}


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
