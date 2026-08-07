"""Phase 3 / `3e` B6 — summoned pets: detected and named, NOT yet modelled.

ENGINE_BUGS E3: no pet model exists anywhere in `core/sim/`, while the corpus
DPS this is calibrated against **includes pet damage**. So every pet-carrying
build is guaranteed to miss low against the corpus number it is calibrated on —
**silently**, which is the part that matters.

⚠ **`3j` B4 — the FORMULA in this docstring was stale; the CONCLUSION is not.**
It read `dps = (total_damage + pet_damage) / duration`, which `3i` B3 fixed
(that expression counted pet damage twice — E15). The current expression is
`dps = total_damage / duration`. **The gap this module warns about survives the
fix**, because the endpoint merges pets into `rows[]` and `total_damage` sums
those owner rows: pet damage is in the denominator exactly once, where before
it was there twice. `pet_damage` is now a *restatement* — "of that total, this
much was pet-delivered" — and is never added back.

Recorded this way deliberately, per the primer's v25 rule: **retracting a
mechanism does not retract the conclusion it supported.** The wrong formula
would have been an easy excuse to close E3; the measurement it rests on is
unaffected.

🛑 **WHY THIS MODULE DETECTS AND WARNS RATHER THAN SIMULATING.**

The owner's scope decision (2026-08-06) was the mechanical minimum: summon -> a
pet actor with auto-attacks plus whatever damage spell its own record carries,
scaled from the owner's stats. **That scope is not reachable from this project's
data, and the reason is structural rather than a gap someone forgot to fill.**

* Summons themselves ARE derivable: `SPELL_EFFECT_SUMMON` is effect type 28 and
  `spell_effect_values` holds **395 rows across 389 spells**, each carrying the
  summoned **creature id** in `misc_value`. So "does this build summon, and
  what" is a query, and that is what this module answers.
* A pet's **damage** is not. Creature stats — attack power, damage range, attack
  speed, the pet's own spell list — live in the server's `creature_template`,
  **not in any client DBC**. There is no creature table in `ascension.db` and no
  `--with-dbc` widening would produce one, because the client does not ship it.

So the honest state is: the sim knows a pet exists, names it, and states the
size of what it is missing. Inventing a damage figure for it would be exactly
the fabrication this project refuses everywhere else — and it would be
fabrication *inside the number the calibration gate reads*.

**The route that WOULD work is logs, not DBC.** `ability_performance` already
carries an `is_pet` flag, and a combat log names pet damage directly, so a pet
damage profile can be MEASURED per pet. That belongs with PHASE_3 T6 log
ingestion (session `3f`), not here. Open question: `pet_damage_not_derivable`.

Measured scale of the gap, so nobody has to guess how much this matters:

* Owner's Frost Mage capture (Lesser Water Elemental): **5.0%** of damage
  unbuffed, **5.4%** buffed, **1.5%** in the dungeon window.
* Gate cohort: roughly **10%** of the cohort's real damage is pet damage.
"""

SUMMON_EFFECT_TYPE = 28

# Owner's 2026-08-06 Frost Mage capture — the only first-party measurement of a
# pet's share we hold. Quoted in the warning so a reader knows the magnitude of
# the omission without going to find it.
MEASURED_PET_SHARE_NOTE = (
    "measured on the owner's Frost Mage capture: 5.0% of damage unbuffed, 5.4% "
    "buffed, 1.5% in a dungeon; ~10% across the gate cohort")


def detect_summons(conn, spell_ids):
    """Which of these abilities summon something, and what creature.

    Mechanical: reads `SPELL_EFFECT_SUMMON` rows and their `misc_value`
    (the creature id). Never matched on name — 'Summon' in a spell's title is
    not evidence, and this project has two retracted conclusions from relating
    ids by name.

    🔬 The two methods were compared on the committed fixtures and they disagree
    **in both directions**, which is the rule earning its keep: on the
    combo-point board a name match returns `Summon Felguard, Summon Void Zone,
    Summon Voidwalker` while the effect query returns `Summon Void Zone` and
    **`Roll the Bones`** — a summon no name match could ever find, and two
    "Summon …" titles that carry no summon effect in our extract.

    ⚠ **This is a LOWER BOUND.** A summon whose spell has no
    `spell_effect_values` row is invisible here, exactly as it is invisible to
    every other query in the project. Absence of a row is not evidence of no
    pet, and this function never claims otherwise.
    """
    ids = [s for s in spell_ids if isinstance(s, int)]
    if not ids:
        return []
    marks = ",".join("?" * len(ids))
    rows = conn.execute(
        f"""SELECT DISTINCT v.spell_id, COALESCE(s.name, '') AS name,
                   v.misc_value
            FROM spell_effect_values v
            LEFT JOIN spells s ON s.id = v.spell_id
            WHERE v.effect_type = ? AND v.spell_id IN ({marks})
            ORDER BY v.spell_id""",
        (SUMMON_EFFECT_TYPE, *ids)).fetchall()
    return [{"spell_id": r[0], "name": r[1] or f"spell {r[0]}",
             "creature_id": r[2]} for r in rows]


def pet_gap_warning(summons):
    """The warning a sim emits when a build summons. None when it does not.

    Named per pet, because "this build has a pet" and "this build has three
    pets" are different sizes of missing damage.
    """
    if not summons:
        return None
    named = ", ".join(
        f"{s['name']} (spell {s['spell_id']}"
        + (f" -> creature {s['creature_id']}" if s["creature_id"] else "")
        + ")" for s in summons[:6])
    return (
        f"PET DAMAGE IS NOT MODELLED. This build summons {len(summons)} "
        f"pet(s): {named}"
        + (" ..." if len(summons) > 6 else "")
        + f". The corpus DPS this is calibrated against INCLUDES pet damage "
        f"(the endpoint merges pets into rows[], so corpus.py's total_damage "
        f"already contains it; 3j B4 — pet_damage is a restatement and is NOT "
        f"added on top, which 3i B3 fixed), so a "
        f"pet-carrying build misses low by roughly the pet's whole share — "
        f"{MEASURED_PET_SHARE_NOTE}. Creature stats live in the server's "
        f"creature_template, NOT in any client DBC, so no wider extract "
        f"reaches them; the route is log-derived pet profiles (PHASE_3 T6). "
        f"See open question pet_damage_not_derivable")
