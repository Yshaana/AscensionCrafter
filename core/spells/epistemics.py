"""Fact ↔ spell linking and the answered-question check (Phase 1 T6, session 1c).

Two functions, both pure (connection as a parameter, no I/O side effects beyond
the tables they own):

* ``link_facts_to_spells`` derives ``fact_spell_links`` from ``confirmed_facts``
  text. It owns the table (delete-then-insert, idempotent).
* ``find_answered_questions`` flags ``open_questions`` rows whose text overlaps a
  ``confirmed_facts`` row — the *"you already answered this"* check that would
  have caught the INDEX_GUIDE v7 self-contradiction. Report-only: it returns
  candidates, it never resolves a question.

⚠ Matching discipline (hard rule 5: never relate two IDs by name — this module
skirts that rule on purpose, and compensates with confidence tiers):

* A 6-digit-or-longer number that is a catalog id → ``id_regex``, `inferred`.
  The Ascension custom range (≥100000) doesn't collide with ratings, dates or
  percentages in fact prose.
* A shorter number that is a catalog id counts ONLY when the spell's *name* also
  appears in the same fact (``id_plus_name``) — "393 rating" must never link to
  a spell that happens to have id 393.
* A bare name match is ``name_exact`` at `needs_review`, **never auto-approved**,
  and duplicate names link every candidate (the duplicate-name trap is the
  reader's problem to resolve, not this module's to guess at).
"""
import re

STOPWORDS = frozenset("""
    the and for with from that this have been does not are was were will would
    into over under between against about which where when whose their there
    each every never always also only both more most less than then them they
""".split())

# words that appear in nearly every fact/question in this project and carry no
# discriminating signal for the overlap check
DOMAIN_NOISE = frozenset("""
    spell spells ability abilities damage tooltip tooltips rank ranks card cards
    catalog level character owner darkmoon season patch confirmed resolved
    source evidence measured question phase session
""".split())

_NUM_PAT = re.compile(r"\b(\d{3,7})\b")


def _distinctive_tokens(text):
    words = re.findall(r"[a-z]{5,}", (text or "").lower())
    return {w for w in words if w not in STOPWORDS and w not in DOMAIN_NOISE}


def link_facts_to_spells(conn):
    """Rebuild ``fact_spell_links`` from ``confirmed_facts``. Returns counts."""
    spell_names = {}   # id -> name
    ids_by_name = {}   # name -> [ids]  (duplicate names are real, keep all)
    for sid, name in conn.execute("SELECT id, name FROM spells WHERE name IS NOT NULL"):
        spell_names[sid] = name
        ids_by_name.setdefault(name, []).append(sid)
    valid_ids = set(spell_names)

    # longest-first so 'Righteous Vengeance' masks its span before 'Vengeance'
    # gets a chance to fire inside it
    names_longest_first = sorted(
        (n for n in ids_by_name if len(n) >= 4), key=len, reverse=True)
    name_pats = {n: re.compile(r"\b" + re.escape(n) + r"\b") for n in names_longest_first}

    conn.execute("DELETE FROM fact_spell_links")
    counts = {"id_regex": 0, "id_plus_name": 0, "name_exact": 0}
    rows = []
    for topic, fact in conn.execute("SELECT topic, fact FROM confirmed_facts"):
        text = fact or ""
        linked = set()

        for m in _NUM_PAT.finditer(text):
            num = int(m.group(1))
            if num not in valid_ids or num in linked:
                continue
            if num >= 100000:
                rows.append((topic, num, "id_regex", "inferred"))
                counts["id_regex"] += 1
                linked.add(num)
            elif name_pats.get(spell_names[num]) and \
                    name_pats[spell_names[num]].search(text):
                # short id corroborated by the spell's own name in the same fact
                rows.append((topic, num, "id_plus_name", "inferred"))
                counts["id_plus_name"] += 1
                linked.add(num)
            # a bare short number with no name corroboration is NOT a link

        masked = text
        for name in names_longest_first:
            pat = name_pats[name]
            if not pat.search(masked):
                continue
            masked = pat.sub(" " * len(name), masked)
            for sid in ids_by_name[name]:
                if sid not in linked:
                    rows.append((topic, sid, "name_exact", "needs_review"))
                    counts["name_exact"] += 1
                    linked.add(sid)

    conn.executemany(
        "INSERT INTO fact_spell_links (fact_topic, spell_id, match_method, confidence)"
        " VALUES (?,?,?,?)", rows)
    counts["total"] = len(rows)
    return counts


def find_answered_questions(conn, min_shared_tokens=6):
    """Candidate (question, fact) pairs whose texts overlap enough to suggest the
    question is already answered. Returns a list of dicts, best match first.
    Report-only — resolving a question is a human edit to the seed script."""
    facts = [(topic, _distinctive_tokens(f"{topic} {fact}"))
             for topic, fact in conn.execute(
                 "SELECT topic, fact FROM confirmed_facts")]
    out = []
    for slug, question in conn.execute(
            "SELECT slug, question FROM open_questions WHERE status = 'open'"):
        q_tokens = _distinctive_tokens(question)
        if not q_tokens:
            continue
        for topic, f_tokens in facts:
            shared = q_tokens & f_tokens
            if len(shared) >= min_shared_tokens:
                out.append({"question_slug": slug, "fact_topic": topic,
                            "shared_tokens": sorted(shared),
                            "score": len(shared)})
    out.sort(key=lambda r: -r["score"])
    return out
