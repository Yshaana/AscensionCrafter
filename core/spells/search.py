"""Phase 1 T9 — `search_spells()`: general filtered search (session 1c).

The "easily searchable" requirement as a real function, not ad-hoc SQL in a
notebook. The CLI, Datasette users pasting into the SQL box, and the future web
API all get the same semantics.

Filters compose with AND. Everything is optional; no filters returns the whole
catalog (capped by `limit`).
"""

_VALID_FILTERS = frozenset((
    "name_like", "school", "scaling_term", "coefficient_min", "coefficient_max",
    "owned", "type", "class_origin", "mechanic", "relates_to",
    "patch_touched_since", "min_volatility_touches", "rarity", "in_current_pool",
))


def search_spells(conn, limit=100, **filters):
    """Filtered catalog search. Returns a list of dicts, name-ordered.

    Filters (all optional, AND-composed):
      name_like            substring on spells.name (case-insensitive)
      school               spells.schools contains this school (text signal)
      scaling_term         has a spell_scaling row of this term_type (SP/AP/SPFR/...)
      coefficient_min/max  bounds on that term's coefficient (needs scaling_term)
      owned                True = only cards in owned_cards, False = only unowned
      type                 'ability' | 'talent'
      class_origin         confirmed/inferred class
      mechanic             spells.mechanics contains this tag (text signal)
      relates_to           spell id — connected by any spell_relationships edge
      patch_touched_since  'YYYY-MM-DD' — named by a patch entry on/after date
      min_volatility_touches  at least N patch touches ever (report-only signal)
      rarity               dbc_character_advancement rarity_a (e.g. 'Epic')
      in_current_pool      True — CA row with in_current_pool = 1 exists
    """
    unknown = set(filters) - _VALID_FILTERS
    if unknown:
        raise ValueError(f"unknown filter(s): {sorted(unknown)} — "
                         f"valid: {sorted(_VALID_FILTERS)}")

    where, params, joins = [], [], []

    if (v := filters.get("name_like")) is not None:
        where.append("s.name LIKE ? COLLATE NOCASE")
        params.append(f"%{v}%")
    if (v := filters.get("school")) is not None:
        where.append("(',' || COALESCE(s.schools,'') || ',') LIKE ?")
        params.append(f"%,{v},%")
    if (v := filters.get("mechanic")) is not None:
        where.append("(',' || COALESCE(s.mechanics,'') || ',') LIKE ?")
        params.append(f"%,{v},%")
    if (v := filters.get("type")) is not None:
        where.append("s.type = ?")
        params.append(v)
    if (v := filters.get("class_origin")) is not None:
        where.append("s.class_origin = ?")
        params.append(v)

    if (v := filters.get("scaling_term")) is not None:
        cond = "ss.term_type = ?"
        p = [v]
        if (lo := filters.get("coefficient_min")) is not None:
            cond += " AND ss.coefficient >= ?"
            p.append(lo)
        if (hi := filters.get("coefficient_max")) is not None:
            cond += " AND ss.coefficient <= ?"
            p.append(hi)
        where.append(f"EXISTS (SELECT 1 FROM spell_scaling ss "
                     f"WHERE ss.spell_id = s.id AND {cond})")
        params.extend(p)
    elif filters.get("coefficient_min") is not None or \
            filters.get("coefficient_max") is not None:
        raise ValueError("coefficient bounds need scaling_term")

    if (v := filters.get("owned")) is not None:
        op = "EXISTS" if v else "NOT EXISTS"
        where.append(f"{op} (SELECT 1 FROM owned_cards oc WHERE oc.spellId = s.id)")

    if (v := filters.get("relates_to")) is not None:
        where.append("""EXISTS (SELECT 1 FROM spell_relationships r
            WHERE (r.source_spell_id = s.id AND r.target_spell_id = ?)
               OR (r.target_spell_id = s.id AND r.source_spell_id = ?))""")
        params.extend([v, v])

    if (v := filters.get("patch_touched_since")) is not None:
        where.append("""EXISTS (SELECT 1 FROM patch_entry_spells pes
            JOIN patch_entries pe ON pe.entry_id = pes.entry_id
            JOIN patches p ON p.patch_id = pe.patch_id
            WHERE pes.spell_id = s.id AND p.patch_date >= ?)""")
        params.append(v)

    if (v := filters.get("min_volatility_touches")) is not None:
        where.append("""(SELECT COUNT(*) FROM patch_entry_spells pes
            WHERE pes.spell_id = s.id) >= ?""")
        params.append(v)

    if (v := filters.get("rarity")) is not None:
        where.append("""EXISTS (SELECT 1 FROM dbc_character_advancement ca
            WHERE s.id IN (ca.spell_rank_1, ca.spell_rank_2, ca.spell_rank_3,
                           ca.spell_rank_4, ca.spell_rank_5)
              AND ca.rarity_a = ?)""")
        params.append(v)
    if filters.get("in_current_pool"):
        where.append("""EXISTS (SELECT 1 FROM dbc_character_advancement ca
            WHERE s.id IN (ca.spell_rank_1, ca.spell_rank_2, ca.spell_rank_3,
                           ca.spell_rank_4, ca.spell_rank_5)
              AND ca.in_current_pool = 1)""")

    sql = f"""
        SELECT s.id, s.name, s.type, s.schools, s.mechanics, s.class_origin,
               s.class_confidence,
               EXISTS (SELECT 1 FROM owned_cards oc WHERE oc.spellId = s.id) AS owned
        FROM spells s
        {"WHERE " + " AND ".join(where) if where else ""}
        ORDER BY s.name LIMIT ?"""
    params.append(limit)
    cols = ("id", "name", "type", "schools", "mechanics", "class_origin",
            "class_confidence", "owned")
    return [dict(zip(cols, r)) for r in conn.execute(sql, params)]
