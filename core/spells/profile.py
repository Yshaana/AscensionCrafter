"""Phase 1 T7 — `spell_profile()`: one call, everything known about a spell.

Structured dict, no printing. The CLI (`cli/profile.py`), Datasette canned
queries and the future web API all call this same function (§2.7).

Design notes:

* **Name resolution honours the duplicate-name trap.** A name matching several
  catalog ids returns `{"ambiguous": True, "candidates": [...]}` and refuses to
  pick — hard rule 5, never relate by name.
* **Conflicts and rank gaps are surfaced at the top of the mechanics section**,
  not buried: `resolve_spell_mechanics()` is called live (its `rank_gap` is
  computed, not stored) so the profile can never silently serve a Rank-1
  magnitude for a level-60 question.
* **`mode='fast'`** skips graph traversal, clusters, volatility and usage joins
  — for loops (the sim resolving 15 abilities).
* **Real usage** needs the separate `scouted_builds.db`; pass its connection as
  `scouted_conn` or the section reports itself unavailable. Performance
  (pooled hits/crits) is Phase 3 and says so rather than pretending.
"""
from .graph import find_clusters, neighbourhood
from .mechanics import DEFAULT_LEVEL, resolve_spell_mechanics
from .ranks import rank_for_level
from .volatility import volatility_score

_SPELL_COLS = ("id", "type", "name", "rank", "schools", "mechanics",
               "has_hidden_formula", "hidden_refs", "has_unresolved_pct",
               "class_origin", "class_confidence", "best_fit_path", "notes")


def _resolve_name_or_id(conn, name_or_id):
    """id -> [row] | name -> all exact matches (duplicate-name trap: >1 is the
    caller's problem to disambiguate, never ours to guess)."""
    cols = ", ".join(_SPELL_COLS)
    if isinstance(name_or_id, int) or (isinstance(name_or_id, str)
                                       and name_or_id.isdigit()):
        rows = conn.execute(
            f"SELECT {cols} FROM spells WHERE id = ?", (int(name_or_id),)).fetchall()
        if not rows:
            # Out-of-catalog spells with a DBC record still profile — Hammer
            # from the Heavens (282987) is exactly this shape, and "complete for
            # every ability in the user's builds" is a T7 exit criterion.
            # Deliberately id-only: a NAME lookup must stay catalog-scoped, or
            # the 209k-row Spell.dbc floods every duplicate-name query.
            dbc = conn.execute(
                "SELECT id, name FROM spell_dbc_raw WHERE id = ?",
                (int(name_or_id),)).fetchone()
            if dbc:
                row = dict.fromkeys(_SPELL_COLS)
                row.update(id=dbc[0], name=dbc[1], type="dbc_only")
                return [row]
    else:
        rows = conn.execute(
            f"SELECT {cols} FROM spells WHERE name = ? COLLATE NOCASE",
            (name_or_id,)).fetchall()
    return [dict(zip(_SPELL_COLS, r)) for r in rows]


def spell_profile(conn, name_or_id, rank=None, realm=None, season=None,
                  depth=2, mode="full", level=DEFAULT_LEVEL, scouted_conn=None):
    """Everything known about one spell, with provenance. See module docstring."""
    matches = _resolve_name_or_id(conn, name_or_id)
    if not matches:
        return {"found": False, "query": name_or_id}
    if len(matches) > 1:
        return {"found": True, "ambiguous": True, "query": name_or_id,
                "note": ("duplicate-name trap: multiple catalog entries share "
                         "this name — query by id"),
                "candidates": [{k: m[k] for k in ("id", "name", "type", "rank",
                                                  "schools", "class_origin")}
                               for m in matches]}
    spell = matches[0]
    sid = spell["id"]

    # --- identity --------------------------------------------------------
    line = rank_for_level(conn, sid, level)
    ca = conn.execute(
        """SELECT ca_id, max_rank, rarity_a, in_current_pool
           FROM dbc_character_advancement
           WHERE ? IN (spell_rank_1, spell_rank_2, spell_rank_3,
                       spell_rank_4, spell_rank_5)
           ORDER BY in_current_pool DESC""", (sid,)).fetchall()
    profile = {
        "found": True,
        "identity": {
            **spell,
            "rank_line": line,   # what a level-`level` character casts, or None
            "character_advancement": [
                {"ca_id": r[0], "max_rank": r[1], "rarity": r[2],
                 "in_current_pool": bool(r[3])} for r in ca],
        },
    }

    # --- ownership (user-scoped once user_id exists on owned_cards) ------
    owned = conn.execute(
        "SELECT cardId, rank, pool FROM owned_cards WHERE spellId = ?",
        (sid,)).fetchall()
    profile["ownership"] = {
        "owned": bool(owned),
        "cards": [{"card_id": r[0], "rank": r[1], "pool": r[2]} for r in owned],
    }

    # --- mechanics: live resolve so rank_gap/conflicts are fresh ---------
    resolved = resolve_spell_mechanics(conn, sid, rank=rank, realm=realm,
                                       season=season, level=level)
    profile["mechanics"] = {
        # surfaced FIRST, prominently, per the phase doc
        "rank_gap": resolved["rank_gap"],
        "conflicts": resolved["conflicts"],
        "confidence": resolved["confidence"],
        "fields": resolved["fields"],
        "source_tiers": resolved["tiers"],
        "uncertainty": resolved["uncertainty"],
        "evidence": resolved["evidence"],
    }

    # --- facts (linked via fact_spell_links, full text) ------------------
    profile["facts"] = [
        {"topic": r[0], "fact": r[1], "match_method": r[2], "confidence": r[3],
         "realm": r[4], "season": r[5]}
        for r in conn.execute(
            """SELECT f.topic, f.fact, l.match_method, l.confidence,
                      f.realm, f.season
               FROM fact_spell_links l
               JOIN confirmed_facts f ON f.topic = l.fact_topic
               WHERE l.spell_id = ?""", (sid,))]

    # --- patch history, newest first -------------------------------------
    profile["patch_history"] = [
        {"date": r[0], "direction": r[1], "status": r[2],
         "match_confidence": r[3], "text": r[4]}
        for r in conn.execute(
            """SELECT p.patch_date, pe.change_direction, pe.status,
                      pes.confidence, substr(pe.raw_text, 1, 300)
               FROM patch_entry_spells pes
               JOIN patch_entries pe ON pe.entry_id = pes.entry_id
               JOIN patches p ON p.patch_id = pe.patch_id
               WHERE pes.spell_id = ?
               ORDER BY p.patch_date DESC""", (sid,))]

    # --- gaps -------------------------------------------------------------
    open_qs = [
        {"slug": r[0], "question": r[1], "blocks": r[2]}
        for r in conn.execute(
            """SELECT slug, question, blocks FROM open_questions
               WHERE status IN ('open', 'in_progress')
                 AND (',' || COALESCE(affected_spell_ids, '') || ',')
                     LIKE '%,' || ? || ',%'""", (str(sid),))]
    profile["gaps"] = {
        "hidden_refs_unresolved": spell["hidden_refs"] or None,
        "has_unresolved_pct": bool(spell["has_unresolved_pct"]),
        "mechanics_conflicts": bool(resolved["conflicts"]),
        "rank_gap": bool(resolved["rank_gap"]),
        "open_questions": open_qs,
    }

    if mode == "fast":
        return profile

    # --- relationships & clusters (full mode only) ------------------------
    profile["relationships"] = neighbourhood(conn, sid, depth=depth)
    profile["clusters"] = [
        {"size": c["size"], "edges": c["edges"], "density": round(c["density"], 3),
         # very large components are noise at profile granularity — name them by size only
         "nodes": c["nodes"] if c["size"] <= 50 else None}
        for c in find_clusters(conn) if sid in c["nodes"]]

    # --- volatility (report-only — the payload restates its own contract) --
    profile["volatility"] = volatility_score(conn, sid)

    # --- real usage (needs scouted_builds.db) ------------------------------
    if scouted_conn is not None and ca:
        ca_ids = [r[0] for r in ca]
        marks = ",".join("?" * len(ca_ids))
        usage = scouted_conn.execute(
            f"""SELECT sc.name, sc.spec, sbe.rank, sbe.max_ranks, sbe.scouted_at
                FROM scouted_build_entries sbe
                JOIN scouted_characters sc
                  ON sc.character_id = sbe.character_id
                 AND sc.scouted_at = sbe.scouted_at
                WHERE sbe.entry_id IN ({marks})
                ORDER BY sbe.scouted_at DESC""", ca_ids).fetchall()
        profile["real_usage"] = [
            {"character": r[0], "spec": r[1], "rank": r[2], "max_ranks": r[3],
             "captured_at": r[4],
             "note": "snapshot — check captured_at before treating as current"}
            for r in usage]
    else:
        profile["real_usage"] = {"available": False,
                                 "note": "pass scouted_conn (scouted_builds.db)"}

    # --- performance: Phase 3 owns pooled parse data -----------------------
    profile["performance"] = {"available": False,
                              "note": "pooled hits/crits/damage-share lands in Phase 3"}
    return profile
