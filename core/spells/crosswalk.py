"""The ID crosswalk (Phase 1 Task 3).

Ascension exposes the same card through several unrelated ID spaces. Phase 0 Task 5
proved the two most-confused ones are genuinely different: across 1,054 distinct
`entry_id`s from 12 scouted characters and the 48-character Phase 1 baseline,
**0 resolved to the catalog `spells.id` of the same card**, and the single numeric
collision (`50043`) is `Ghostly Finish` in the crawl and `Chilblains` in the catalog.

    🛑 NEVER join `entry_id` to `spells.id`. Go through this table.

Every external space plugs in as **rows, never as new join logic** — so the next
source costs a populate function, not a rewrite of every query.

The spaces, and how each resolves:

  ``character_advancement``  CA id (== the crawl's / BisBeard's `entry_id`) → the
                             spellId of each card rank, straight out of
                             `CharacterAdvancement.dbc` slots 5–9. Talent cards fill
                             2/3/5 slots; **ability cards fill only slot 1**, because
                             an ability's *spell* rank is set by character level, not
                             by the card — chase that through `catalog_vs_live`.
  ``logs_gg.entry_id``       the subset of CA ids actually observed on a live
                             character. Same numbers, recorded separately because
                             "seen in the wild" is evidence the DBC alone isn't.
  ``catalog_vs_live``        catalog `spells.id` → the id a level-60 character
                             really casts. This is where the 697 wrong-rank entries
                             live, and the long-running 274121-vs-274132 confusion
                             is just another row here.
  ``card_id``                `Cards.txt` cardId → spellId. **Many-to-one** — Arcane
                             Intellect has four (2 Normal, 2 Golden).

Two spaces named in the original task are deliberately NOT built:

  * ``wotlk_rank`` (rank-1 id ↔ other ranks) — superseded. `dbc_spell_rank` is the
    one home for rank lines; duplicating 42,606 rows here would be a second home
    for the same fact. `catalog_vs_live` carries the part that does work.
  * ``id_proximity`` matching — **the contiguous-rank rule was retracted in Phase 0**
    (4,791 non-contiguous lines vs 1,908 contiguous). Adding a ±1–3 resolver would
    reintroduce a disproven heuristic at `inferred` confidence, which is worse than
    not answering.

Every relation that could tie two *different* spell ids together is checked with
`fingerprint.py` first, and a mismatch is recorded as `confidence='conflict'`
rather than resolved (§2.3).
"""
from . import fingerprint as fp

EXTERNAL_SOURCES = {
    "character_advancement": "CharacterAdvancement.dbc ca_id -> spellId per card rank",
    "logs_gg.entry_id": "entry_id seen on a live character (ascensionlogs armory capture)",
    "catalog_vs_live": "catalog spells.id -> the id a level-60 character actually casts",
    "card_id": "Cards.txt cardId -> spellId (many-to-one)",
    "db_ascension_gg": "db.ascension.gg spell page id (same space as the catalog)",
    "changelog_name": "a name as written in a changelog entry",
    "official_builder": "ascension.gg/v2/builder entry id (Area-52/Elune only - NOT Darkmoon)",
}

CONFIDENCE = ("confirmed", "inferred", "conflict", "unverified")

_INSERT = """
INSERT OR IGNORE INTO spell_id_crosswalk
    (external_source, external_id, spell_id, rank, match_method, confidence,
     evidence_ref, notes)
VALUES (?,?,?,?,?,?,?,?)
"""


def clear_source(conn, external_source):
    """Delete this source's own previous rows.

    Phase 0 found three bugs of exactly one shape: *a script that derives rows
    without owning the deletion of its own previous output*. Every populate
    function below calls this first, so a re-run is a replace, not an append.
    """
    conn.execute("DELETE FROM spell_id_crosswalk WHERE external_source = ?", (external_source,))


# ---------------------------------------------------------------------------
# populate
# ---------------------------------------------------------------------------

def populate_character_advancement(conn, *, pool_only=False):
    """CA id -> spellId, one row per populated rank slot.

    `pool_only=True` restricts to `in_current_pool = 1` (3,129 of 10,231 — the
    currently-playable cards). Default is False: the excluded records are other
    realms'/modes' entries, but they are real mappings and dropping them would
    make an unresolvable id look like a bug rather than an out-of-pool card. The
    pool flag is carried in `notes` so callers can filter without re-extracting.
    """
    clear_source(conn, "character_advancement")
    rows = conn.execute(
        "SELECT ca_id, name, max_rank, in_current_pool, "
        "       spell_rank_1, spell_rank_2, spell_rank_3, spell_rank_4, spell_rank_5 "
        "FROM dbc_character_advancement"
        + (" WHERE in_current_pool = 1" if pool_only else "")
    ).fetchall()

    # fingerprint the multi-rank arrays: the client asserts these are one card's
    # ranks, and Phase 0 found 2 genuine mid-chain renames, so the rank chain is
    # authoritative and the NAME is not. A structural mismatch is worth recording.
    rank_ids = set()
    for r in rows:
        rank_ids.update(x for x in r[4:9] if x)
    fps = fp.fingerprint_index(conn, rank_ids)

    out, stats = [], {"cards": 0, "rows": 0, "conflicts": 0, "unchecked": 0}
    for ca_id, name, max_rank, in_pool, *ranks in rows:
        populated = [(i + 1, sid) for i, sid in enumerate(ranks) if sid]
        if not populated:
            continue
        stats["cards"] += 1
        base_fp = fps.get(populated[0][1])
        note = f"in_current_pool={in_pool}; max_rank={max_rank}; name={name!r}"
        for rank, sid in populated:
            confidence, extra = "confirmed", ""
            if len(populated) > 1 and rank != populated[0][0]:
                verdict, _detail = fp.verdict_from_fingerprints(
                    base_fp, fps.get(sid), fp.RANK_FINGERPRINT_FIELDS)
                if verdict == "mismatch":
                    confidence = "conflict"
                    extra = "; FINGERPRINT MISMATCH vs rank-1 spell of the same CA row"
                    stats["conflicts"] += 1
                elif verdict == "unknown":
                    extra = "; fingerprint not comparable (id absent from spell_dbc_raw)"
                    stats["unchecked"] += 1
            out.append(("character_advancement", str(ca_id), sid, rank, "dbc_rank_slot",
                        confidence, "CharacterAdvancement.dbc slot 5-9", note + extra))
    conn.executemany(_INSERT, out)
    stats["rows"] = len(out)
    return stats


def populate_observed_entry_ids(conn, observations):
    """Record `entry_id`s actually seen on a live character.

    `observations` is an iterable of `(entry_id, rank, name, evidence_ref)` — the
    caller supplies them, because reading crawl files is `ingest/`'s job, not
    `core/`'s. Rows resolve through the CA mapping; an entry_id with no CA row is
    still recorded (`spell_id` cannot be NULL, so it is skipped and counted) because
    an unresolvable observed id is a finding, not a no-op.
    """
    clear_source(conn, "logs_gg.entry_id")
    ca = {r[0]: r[1:] for r in conn.execute(
        "SELECT ca_id, spell_rank_1, spell_rank_2, spell_rank_3, spell_rank_4, "
        "spell_rank_5, name FROM dbc_character_advancement")}

    out, stats = [], {"observed": 0, "resolved": 0, "unresolved": [], "name_mismatch": []}
    seen = set()
    for entry_id, rank, name, evidence in observations:
        stats["observed"] += 1
        row = ca.get(entry_id)
        if row is None:
            if entry_id not in stats["unresolved"]:
                stats["unresolved"].append(entry_id)
            continue
        slots, ca_name = row[:5], row[5]
        rank = rank or 1
        sid = slots[rank - 1] if 1 <= rank <= 5 else None
        sid = sid or next((s for s in slots if s), None)   # ability cards: slot 1 only
        if not sid:
            continue
        if name and ca_name and name.strip().lower() != ca_name.strip().lower():
            pair = (entry_id, name, ca_name)
            if pair not in stats["name_mismatch"]:
                stats["name_mismatch"].append(pair)
        key = (entry_id, rank, sid)
        if key in seen:
            continue
        seen.add(key)
        out.append(("logs_gg.entry_id", str(entry_id), sid, rank, "id_identity", "confirmed",
                    evidence, f"entry_id == CharacterAdvancement ca_id; card={ca_name!r}"))
    conn.executemany(_INSERT, out)
    stats["resolved"] = len(out)
    return stats


def populate_catalog_vs_live(conn, level=60):
    """Catalog `spells.id` -> the id a character of `level` actually casts.

    Only rows where the two differ are written — an entry already stored at the
    right rank needs no crosswalk. Each pair is fingerprint-checked even though the
    rank line was already grouped on a fingerprint upstream: a second, independent
    check is cheap and this is the exact place a wrong relation would do damage.
    """
    from .ranks import catalog_rank_gaps

    clear_source(conn, "catalog_vs_live")
    gaps = list(catalog_rank_gaps(conn, level))
    ids = {g["catalog_spell_id"] for g in gaps}
    ids.update(c["spell_id"] for g in gaps for c in g["candidates"])
    fps = fp.fingerprint_index(conn, ids)

    out = []
    stats = {"gaps": len(gaps), "rows": 0, "conflicts": 0, "unchecked": 0,
             "ambiguous": 0, "level_rank_absent_from_catalog": 0}
    for g in gaps:
        if g["ambiguous"]:
            stats["ambiguous"] += 1
        for cand in g["candidates"]:
            verdict, _detail = fp.verdict_from_fingerprints(
                fps.get(g["catalog_spell_id"]), fps.get(cand["spell_id"]),
                fp.RANK_FINGERPRINT_FIELDS)
            confidence = "confirmed"
            note = (f"catalog holds rank {g['catalog_rank']} "
                    f"(SpellLevel {g['catalog_spell_level']}); a level-{level} character "
                    f"casts rank {cand['rank']} (SpellLevel {cand['spell_level']}); "
                    f"level-rank id in catalog: {cand['in_catalog']}")
            if g["ambiguous"]:
                confidence = "conflict"
                note += (f"; AMBIGUOUS - {len(g['candidates'])} spells share the top "
                         f"rank available at level {level}: "
                         f"{[c['spell_id'] for c in g['candidates']]}")
            if verdict == "mismatch":
                confidence = "conflict"
                note += "; FINGERPRINT MISMATCH - do not treat as the same ability"
                stats["conflicts"] += 1
            elif verdict == "unknown":
                note += "; fingerprint not comparable"
                stats["unchecked"] += 1
            if not cand["in_catalog"]:
                stats["level_rank_absent_from_catalog"] += 1
            out.append(("catalog_vs_live", str(g["catalog_spell_id"]), cand["spell_id"],
                        cand["rank"], "level_gate", confidence,
                        f"dbc_spell_rank line {g['line_id']}", note))
    conn.executemany(_INSERT, out)
    stats["rows"] = len(out)
    return stats


def populate_card_ids(conn):
    """`Cards.txt` cardId -> spellId. Many-to-one; every row is kept."""
    clear_source(conn, "card_id")
    rows = conn.execute(
        "SELECT DISTINCT cardId, spellId, rank, pool FROM owned_cards WHERE spellId IS NOT NULL"
    ).fetchall()
    out = [("card_id", str(card_id), spell_id, rank, "id_identity", "confirmed",
            "Cards.txt owned-cards export", f"pool={pool}")
           for card_id, spell_id, rank, pool in rows]
    conn.executemany(_INSERT, out)
    return {"rows": len(out)}


# ---------------------------------------------------------------------------
# resolve
# ---------------------------------------------------------------------------

def resolve(conn, external_source, external_id, rank=None):
    """Every spell id an external id maps to. Returns a list — never assume one."""
    sql = ("SELECT spell_id, rank, match_method, confidence, evidence_ref, notes "
           "FROM spell_id_crosswalk WHERE external_source = ? AND external_id = ?")
    params = [external_source, str(external_id)]
    if rank is not None:
        sql += " AND rank = ?"
        params.append(rank)
    sql += " ORDER BY rank"
    return [{"spell_id": r[0], "rank": r[1], "match_method": r[2], "confidence": r[3],
             "evidence_ref": r[4], "notes": r[5]} for r in conn.execute(sql, params)]


def resolve_entry_id(conn, entry_id, card_rank=None, level=60):
    """The sanctioned `entry_id` -> spell resolution, in one call.

    Two hops, because they answer different questions:
      1. `entry_id` -> the spellId of the card rank held (CharacterAdvancement)
      2. that spellId -> the rank a level-`level` character casts (`catalog_vs_live`)

    Step 2 matters for **ability** cards: the card only ever fills rank slot 1, so
    hop 1 alone returns the Rank-1 spell — the exact mistake that makes a catalog
    magnitude read ~15× low.
    """
    hits = resolve(conn, "character_advancement", entry_id, rank=card_rank)
    if not hits and card_rank is not None:
        hits = resolve(conn, "character_advancement", entry_id)
    out = []
    for hit in hits:
        live = resolve(conn, "catalog_vs_live", hit["spell_id"])
        # An ambiguous rank line has several level-appropriate candidates. Returning
        # the first would be exactly the silent tie-break §2.3 forbids, so the caller
        # gets them all plus a flag, and `level_spell_id` stays None.
        ambiguous = len(live) > 1
        out.append({
            "entry_id": int(entry_id),
            "card_rank": hit["rank"],
            "card_spell_id": hit["spell_id"],
            "level_spell_id": (None if ambiguous
                               else (live[0]["spell_id"] if live else hit["spell_id"])),
            "level_spell_candidates": [row["spell_id"] for row in live],
            "level_rank_ambiguous": ambiguous,
            "level_rank_differs": bool(live),
            "confidence": "conflict" if ambiguous else hit["confidence"],
            "notes": hit["notes"],
        })
    return out


def external_ids_for(conn, spell_id):
    """Reverse lookup: every external id known to point at this spell."""
    rows = conn.execute(
        "SELECT external_source, external_id, rank, confidence, notes "
        "FROM spell_id_crosswalk WHERE spell_id = ? ORDER BY external_source, rank",
        (spell_id,),
    ).fetchall()
    return [{"external_source": r[0], "external_id": r[1], "rank": r[2],
             "confidence": r[3], "notes": r[4]} for r in rows]


def summary(conn):
    """Row counts and conflict counts per source — the crosswalk's own health check."""
    rows = conn.execute(
        "SELECT external_source, COUNT(*), COUNT(DISTINCT external_id), "
        "       SUM(CASE WHEN confidence = 'conflict' THEN 1 ELSE 0 END) "
        "FROM spell_id_crosswalk GROUP BY external_source ORDER BY external_source"
    ).fetchall()
    return [{"external_source": r[0], "rows": r[1], "distinct_external_ids": r[2],
             "conflicts": r[3]} for r in rows]
