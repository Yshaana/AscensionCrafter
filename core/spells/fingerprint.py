"""Mechanical fingerprinting — HARD RULE, never relate two spell IDs by name.

Phase 0 Task 1d, promoted to a standing rule in `START_HERE_FOR_CODE.md` #5 and
`PHASE_1` Task 4. Same-name/different-ID was wrongly assumed to mean "related"
**twice in one session**, producing two retracted conclusions and a nearly-adopted
schema change. The concrete case: two spells named "Holy Supernova" —

    270182  radius index 18, cooldown 40s, 2s cast   (CA 36394)
     81193  radius index 13, cooldown 50s, instant   (CA  1397, and it is Rank 3
                                                      of a completely separate line)

Before treating two IDs as the same ability, a variant, or two ranks of one line,
compare **radius, cooldown, cast type, resource cost, effect structure and school**.
That is what this module does, and every crosswalk write that could relate two IDs
goes through it.
"""
import json

# Fields compared, in the order the rule names them. `effect_types` is the Effect[3]
# opcode triple — the closest thing to a structural signature the DBC carries.
FINGERPRINT_FIELDS = (
    "school_mask",
    "recovery_time",         # cooldown, ms
    "casting_time_index",
    "power_type",            # resource: mana/rage/energy/...
    "radius_index",          # EffectRadiusIndex[3]
    "effect_types",          # Effect[3]
)

# ⚠ A DIFFERENT question needs a different field set. The strict set above answers
# *"are these two IDs the same ability?"* — the hard rule's case, where a differing
# radius or cooldown is exactly what tells Holy Supernova `270182` apart from the
# unrelated `81193`.
#
# It is the wrong test for *"are these two RANKS of one ability?"*, because rank
# legitimately changes those very fields: Gravity Bomb R1 carries a radius on its
# third effect and the higher rank does not; Soul Reaper's ranks differ in
# `power_type`. Applied to rank chains the strict set produced 48 in-pool "conflicts"
# on ordinary talents (Malice R4/R5, Tactical Mastery R3) — noise that would bury the
# real ones.
#
# What genuinely must NOT change between ranks is the damage school and the effect
# structure. That is this set.
RANK_FINGERPRINT_FIELDS = ("school_mask", "effect_types")

# Some columns arrived with the Phase 1 T1 extractor widening. On an older
# spell_dbc_raw they are simply absent — a missing field is reported as
# `unknown`, never silently treated as equal (§2.3: absence is not agreement).
_SCALAR_COLUMNS = ("school_mask", "recovery_time", "casting_time_index", "power_type")


def spell_fingerprint(conn, spell_id):
    """Return the mechanical fingerprint of `spell_id`, or None if it is not in
    `spell_dbc_raw`. Values that the stored row cannot supply come back as None."""
    cols = {r[1] for r in conn.execute("PRAGMA table_info(spell_dbc_raw)")}
    if not cols:
        return None
    wanted = [c for c in _SCALAR_COLUMNS if c in cols]
    sql = f"SELECT id, name, effect_json{''.join(', ' + c for c in wanted)} " \
          f"FROM spell_dbc_raw WHERE id = ?"
    row = conn.execute(sql, (spell_id,)).fetchone()
    if row is None:
        return None

    fp = {"spell_id": row[0], "name": row[1]}
    for i, col in enumerate(wanted, start=3):
        fp[col] = row[i]
    for col in _SCALAR_COLUMNS:
        fp.setdefault(col, None)

    effects = {}
    try:
        effects = json.loads(row[2] or "{}")
    except (json.JSONDecodeError, TypeError):
        effects = {}
    fp["effect_types"] = tuple(effects.get("Effect") or ())
    fp["radius_index"] = tuple(effects.get("EffectRadiusIndex") or ())
    if fp.get("casting_time_index") is None:
        fp["casting_time_index"] = effects.get("CastingTimeIndex")
    return fp


def fingerprint_index(conn, spell_ids=None):
    """Bulk-load fingerprints as `{spell_id: fingerprint}`.

    Same values as `spell_fingerprint`, one table scan instead of one query per id —
    for callers checking thousands of pairs (the crosswalk builder does ~2,400).
    `spell_ids=None` loads every row in `spell_dbc_raw`.
    """
    cols = {r[1] for r in conn.execute("PRAGMA table_info(spell_dbc_raw)")}
    if not cols:
        return {}
    wanted = [c for c in _SCALAR_COLUMNS if c in cols]
    sql = f"SELECT id, name, effect_json{''.join(', ' + c for c in wanted)} FROM spell_dbc_raw"
    wanted_ids = set(spell_ids) if spell_ids is not None else None

    out = {}
    for row in conn.execute(sql):
        if wanted_ids is not None and row[0] not in wanted_ids:
            continue
        fp = {"spell_id": row[0], "name": row[1]}
        for i, col in enumerate(wanted, start=3):
            fp[col] = row[i]
        for col in _SCALAR_COLUMNS:
            fp.setdefault(col, None)
        try:
            effects = json.loads(row[2] or "{}")
        except (json.JSONDecodeError, TypeError):
            effects = {}
        fp["effect_types"] = tuple(effects.get("Effect") or ())
        fp["radius_index"] = tuple(effects.get("EffectRadiusIndex") or ())
        if fp.get("casting_time_index") is None:
            fp["casting_time_index"] = effects.get("CastingTimeIndex")
        out[row[0]] = fp
    return out


def verdict_from_fingerprints(fp_a, fp_b, fields=FINGERPRINT_FIELDS):
    """`same_ability`'s decision, on two already-loaded fingerprints.

    Pass `fields=RANK_FINGERPRINT_FIELDS` when the question is "two ranks of one
    ability" rather than "the same ability".
    """
    if fp_a is None or fp_b is None:
        return "unknown", {"reason": "one or both ids absent from spell_dbc_raw"}
    cmp = compare_fingerprints(fp_a, fp_b, fields,
                               effects_subset_ok=(fields is RANK_FINGERPRINT_FIELDS))
    detail = {"comparison": cmp}
    if cmp["differ"]:
        return "mismatch", detail
    if "school_mask" in cmp["unknown"] or "effect_types" in cmp["unknown"]:
        return "unknown", detail
    return "match", detail


def effects_compatible(a, b):
    """Do two `Effect[3]` triples describe the same ability at different ranks?

    Effect opcode `0` is `SPELL_EFFECT_NONE` — an **empty slot**, not a different
    effect. Higher ranks routinely fill slots the lower rank leaves empty:

        Malice R1-R3 [6,0,0]  ->  R4 [6,0,6]  ->  R5 [6,6,6]

    Requiring exact equality called all 45 in-pool cards of that shape a conflict.
    So: compare only the positions where both sides are non-zero, and require those
    to agree. A slot filled on one side and empty on the other is absence.
    """
    for x, y in zip(a, b):
        if x and y and x != y:
            return False
    return True


def compare_fingerprints(fp_a, fp_b, fields=FINGERPRINT_FIELDS, *, effects_subset_ok=False):
    """Field-by-field comparison of two fingerprints.

    Returns `{"agree": [...], "differ": [...], "unknown": [...]}`. A field lands in
    `unknown` when either side could not supply it — deliberately NOT counted as
    agreement, so a thin fingerprint can never manufacture a match.

    `effects_subset_ok` switches `effect_types` to the rank-aware comparison above.
    """
    agree, differ, unknown = [], [], []
    for field in fields:
        a, b = fp_a.get(field), fp_b.get(field)
        if a is None or b is None:
            unknown.append(field)
        elif field == "effect_types" and effects_subset_ok:
            (agree if effects_compatible(a, b) else differ).append(field)
        elif a == b:
            agree.append(field)
        else:
            differ.append(field)
    return {"agree": agree, "differ": differ, "unknown": unknown}


def same_ability(conn, spell_id_a, spell_id_b):
    """Can these two IDs be treated as the same ability (e.g. two ranks of one line)?

    Returns `(verdict, detail)` where verdict is one of:

      * ``'match'``      — every comparable field agrees and at least school +
                           effect structure were actually comparable
      * ``'mismatch'``   — at least one field differs. **Do not relate them.**
      * ``'unknown'``    — too little data to judge. Also do not relate them; the
                           rule is opt-in evidence, not opt-out doubt.

    `detail` carries both fingerprints and the per-field comparison, so a caller
    can write the reason into `evidence_ref`/`notes` rather than asserting bare.
    """
    fp_a = spell_fingerprint(conn, spell_id_a)
    fp_b = spell_fingerprint(conn, spell_id_b)
    if fp_a is None or fp_b is None:
        return "unknown", {"reason": "one or both ids absent from spell_dbc_raw",
                           "a": fp_a, "b": fp_b}
    cmp = compare_fingerprints(fp_a, fp_b)
    detail = {"a": fp_a, "b": fp_b, "comparison": cmp}
    if cmp["differ"]:
        return "mismatch", detail
    # require the two load-bearing fields to have been genuinely comparable
    if "school_mask" in cmp["unknown"] or "effect_types" in cmp["unknown"]:
        return "unknown", detail
    return "match", detail
