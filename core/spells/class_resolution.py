"""Which class does a card belong to?

Ascension is classless, but engine gating is not: a proc that fires on "damaging
**Paladin** abilities" cares about a hidden class tag, and the primer's flagship
proof case (Lightbound Cleave — Holy-flavoured, Holystrike-school, reads like a
Paladin button, produced **zero** procs from a Paladin trigger) is what that costs
when you guess from flavour.

Two methods, in strength order:

  1. **Skill line** (Phase 0 Task 4a, CONFIRMED). Ascension **renamed the skill
     lines themselves to class names** — line 26 is `"Warrior"`, not retail's
     "Arcane". `ClassMask` is useless: it is `512` (Ascension's own classless
     "Hero" class) on ~10k rows, which is exactly why db.ascension.gg reports
     "Class: Hero" on every card. Deterministic for **1,789 of 3,061** catalog
     entries (58%), agrees with 382/387 existing doc-confirmed rows and 7/7 of
     primer §4's proof cases.
  2. **The class-tag rule** — a card's `uses X modifiers` clause names a base
     ability whose real WotLK owner is the tag. Now the **fallback**, for the 36%
     of the catalog `SkillLineAbility` never mentions (Molten Earth among them).

Neither replaces a proc test when engine gating is on the line, and **class says
nothing about coefficients** — Ascension edits spells in place, so a WotLK id
inherits its class but never its mechanics.
"""
import json

# Strongest first. `confirmed_skill_line` slots below the doc-confirmed tiers
# (those rest on an observation of this server) and above tooltip inference
# (which is an unverified prediction by construction).
CLASS_CONFIDENCE_ORDER = (
    "confirmed_proc_test",
    "confirmed_native",
    "confirmed_class_tag_rule",
    "confirmed_skill_line",
    "inferred_borrowed_modifiers",
)


def tier_rank(tier):
    """Lower is stronger. Unknown/NULL tiers sort last."""
    try:
        return CLASS_CONFIDENCE_ORDER.index(tier)
    except (ValueError, TypeError):
        return len(CLASS_CONFIDENCE_ORDER)


def resolve_from_skill_line(conn, *, require_name_match=True):
    """Plan the `class_origin` writes implied by `dbc_spell_class`.

    Returns `(writes, conflicts, skipped)` and touches nothing — the caller applies
    it. Separating the decision from the write is what makes the conflict rule
    testable instead of aspirational.

    * `writes`     — spells with no class today, and one unambiguous skill-line class
    * `conflicts`  — an existing class that DISAGREES. Recorded, never overwritten
                     (§2.3: auto-picking a winner is how confidently wrong data gets
                     created — even when the existing tier is the weakest one)
    * `skipped`    — ambiguous, name-mismatched, or already agreeing

    `require_name_match` is the guardrail Task 3 asks for: an ID collision between
    the catalog and `Spell.dbc` is possible, and a mismatch is a finding worth
    logging rather than a row worth writing. Phase 0 measured 0 mismatches across
    all 1,789 — if that number ever moves, the guardrail is telling you something.
    """
    rows = conn.execute("""
        SELECT s.id, s.name, s.class_origin, s.class_confidence,
               c.class_name, c.ambiguous, c.all_classes, r.name
        FROM spells s
        JOIN dbc_spell_class c ON c.spell_id = s.id
        LEFT JOIN spell_dbc_raw r ON r.id = s.id
    """).fetchall()

    writes, conflicts, skipped = [], [], {"ambiguous": 0, "name_mismatch": 0,
                                          "already_agrees": 0, "no_class": 0}
    for sid, name, existing, existing_tier, cls, ambiguous, all_classes, dbc_name in rows:
        if ambiguous or not cls:
            skipped["ambiguous" if ambiguous else "no_class"] += 1
            continue
        if require_name_match and dbc_name and name and dbc_name.strip() != name.strip():
            skipped["name_mismatch"] += 1
            conflicts.append({"spell_id": sid, "kind": "name_mismatch",
                              "catalog_name": name, "dbc_name": dbc_name,
                              "skill_line_class": cls})
            continue
        if existing is None:
            writes.append({"spell_id": sid, "name": name, "class_name": cls,
                           "confidence": "confirmed_skill_line",
                           "all_classes": all_classes})
        elif existing.strip().lower() == cls.strip().lower():
            skipped["already_agrees"] += 1
        else:
            conflicts.append({"spell_id": sid, "kind": "class_disagreement",
                              "name": name, "existing": existing,
                              "existing_tier": existing_tier,
                              "skill_line_class": cls,
                              "all_classes": all_classes})
    return writes, conflicts, skipped


def apply_skill_line_writes(conn, writes):
    """Write the planned `class_origin` values. Idempotent."""
    conn.executemany(
        "UPDATE spells SET class_origin = ?, class_confidence = ? WHERE id = ?",
        [(w["class_name"], w["confidence"], w["spell_id"]) for w in writes],
    )
    return len(writes)


def record_conflicts(conn, conflicts):
    """Store disagreements in `spells.class_conflict_json`, keeping BOTH values.

    The existing `class_origin` / `class_confidence` are left exactly as they were.
    This column is the flag; Phase 1 Task 4 folds it into `spell_mechanics.
    conflicts_json` and Task 6 enqueues each one as an open question.
    """
    cols = {r[1] for r in conn.execute("PRAGMA table_info(spells)")}
    if "class_conflict_json" not in cols:
        conn.execute("ALTER TABLE spells ADD COLUMN class_conflict_json TEXT")
    # own the deletion of our own previous output
    conn.execute("UPDATE spells SET class_conflict_json = NULL "
                 "WHERE class_conflict_json IS NOT NULL")
    conn.executemany(
        "UPDATE spells SET class_conflict_json = ? WHERE id = ?",
        [(json.dumps(c, ensure_ascii=False), c["spell_id"]) for c in conflicts],
    )
    return len(conflicts)


def coverage(conn):
    """How much of the catalog has a class, by tier."""
    total = conn.execute("SELECT COUNT(*) FROM spells").fetchone()[0]
    by_tier = conn.execute(
        "SELECT COALESCE(class_confidence, '(none)'), COUNT(*) FROM spells "
        "WHERE class_origin IS NOT NULL GROUP BY 1 ORDER BY 2 DESC"
    ).fetchall()
    resolved = sum(n for _t, n in by_tier)
    return {"catalog_total": total, "with_class": resolved,
            "pct": round(100.0 * resolved / total, 1) if total else 0.0,
            "by_tier": [{"tier": t, "count": n} for t, n in by_tier]}
