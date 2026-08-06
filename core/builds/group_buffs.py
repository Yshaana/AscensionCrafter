"""Derive a crawled character's buff set from the group in the same report.

3b pre-flight §0.3 (2026-08-06). The calibration gate's one-sided miss (40 of
41 deltas negative, −35% to −92%) is a missing multiplicative layer, and the
ranked cause is that buffs were modelled for the owner only. The buff set for a
crawled parse is DERIVABLE, because the group that produced it is in the same
report: on a classless server it is the CARDS a group member carries — never
their class — that determine which buffs they can provide.

🛑 What this module does and refuses to do:

* It applies only the buffs in `core.sim.buffs.MEASURED_BUFFS` with
  `tier='ascension_measured'` — the set measured to arithmetic in the 2e
  incremental capture. It never invents a magnitude for a buff it can see but
  has not measured.
* A buff is derived ONLY when a participant in the same capture scope holds the
  granting card on their linked build snapshot (`card_spell_id` match — the
  never-resolve-by-name hard rule; names appear in provenance for humans only).
* Derivation is a LOWER BOUND and says so: participants without a linked
  snapshot cannot contribute evidence, and buffs outside the measured set
  (other stat buffs, %damage auras, consumables) are not applied at all. The
  coverage numbers ride along so the caller can report how much of the group
  was visible.
* 🛑 It never fits anything. If the gate still misses after this layer, the
  miss is information about the NEXT missing mechanism, not an invitation to
  scale this one.

Card-id resolution (2026-08-06, against ascension.db + builds.db, verified in
both directions id->name and name->id with zero collisions):

* Blessing of Kings        -> card 20217  (measured as "Greater Blessing of
  Kings" — assumed the card's group version; same card either way)
* Arcane Intellect         -> card 1459   (⚠ measured as "Arcane Brilliance";
  NO card of that name exists in catalog or CharacterAdvancement — the group
  version of the Arcane Intellect card is the only candidate source. Flagged
  as an assumption in provenance, magnitude +31 Int / +27 raw SP as measured)
* Strength of Earth Totem  -> card 8075
* Aspect of the Beast      -> card 13161  (aura scope self-vs-party unverified
  on Ascension; +14 AP measured, small either way)
* Consecrated Weapon       -> card 200809 (SELF only — a weapon imbue, not a
  raid buff; stacks per equipped weapon. The 200818 the combat log names is
  its damage spell, not the card)
"""

# buff_key (matching core.sim.buffs.MEASURED_BUFFS) -> derivation rule
BUFF_GRANTING_CARDS = {
    "blessing_of_kings": {
        "card_spell_ids": (20217,), "scope": "group",
        "assumption": "measured as 'Greater Blessing of Kings'; treated as the "
                      "group version of the Blessing of Kings card"},
    "arcane_brilliance": {
        "card_spell_ids": (1459,), "scope": "group",
        "assumption": "no 'Arcane Brilliance' card exists — derived from the "
                      "Arcane Intellect card, assumed to deliver the measured "
                      "group version"},
    "strength_of_earth_totem": {
        "card_spell_ids": (8075,), "scope": "group", "assumption": None},
    "aspect_of_the_beast": {
        "card_spell_ids": (13161,), "scope": "group",
        "assumption": "aura scope (self vs party) unverified on Ascension"},
    "consecrated_weapon": {
        "card_spell_ids": (200809,), "scope": "self",
        "assumption": "all equipped weapons assumed imbued when the card is "
                      "held (matches the owner's Titan's Grip practice)"},
}


def derive_buffs(bdb, scope_id, character_id, own_snapshot_id):
    """Derive the applicable measured-buff set for one (scope, character).

    `bdb` is a builds.db connection. Returns `(buff_keys, provenance)` where
    `provenance` is a dict:

        {"applied": {buff_key: {"granted_by": [(name, character_id,
                                                snapshot_lag_hours)],
                                "assumption": str|None}},
         "participants": N, "participants_with_board": N,
         "not_derivable": [...]}   # measured buffs whose granting card no
                                   # visible board holds — absence of evidence

    Group-scoped buffs accept any participant's linked snapshot regardless of
    its lag (a buff card on a board is far more stable than the board as a
    whole); the lag is recorded per grant so the caller can judge. Self-scoped
    buffs use the candidate's own (lag-0) snapshot only.
    """
    participants = bdb.execute(
        """SELECT ep.character_id, ep.snapshot_id, ep.snapshot_lag_hours, c.name
           FROM encounter_performance ep
           JOIN characters c ON c.character_id = ep.character_id
           WHERE ep.scope_id = ?""", (scope_id,)).fetchall()
    with_board = [(cid, sid, lag, name) for cid, sid, lag, name in participants
                  if sid is not None]

    snapshot_ids = [sid for _cid, sid, _lag, _n in with_board]
    holders_by_card = {}
    if snapshot_ids:
        marks = ",".join("?" * len(snapshot_ids))
        for sid, card_id in bdb.execute(
                f"""SELECT DISTINCT snapshot_id, card_spell_id
                    FROM snapshot_cards
                    WHERE snapshot_id IN ({marks})
                      AND card_spell_id IS NOT NULL""", snapshot_ids):
            holders_by_card.setdefault(card_id, set()).add(sid)

    snap_owner = {sid: (name, cid, lag) for cid, sid, lag, name in with_board}

    applied, not_derivable = {}, []
    for key, rule in BUFF_GRANTING_CARDS.items():
        if rule["scope"] == "self":
            eligible = {own_snapshot_id} if own_snapshot_id in snap_owner else set()
        else:
            eligible = set(snap_owner)
        granting = set()
        for card_id in rule["card_spell_ids"]:
            granting |= holders_by_card.get(card_id, set()) & eligible
        if granting:
            applied[key] = {
                "granted_by": sorted((snap_owner[sid] for sid in granting),
                                     key=lambda t: t[1]),
                "assumption": rule["assumption"],
            }
        else:
            not_derivable.append(key)

    provenance = {
        "applied": applied,
        "participants": len(participants),
        "participants_with_board": len(with_board),
        "not_derivable": not_derivable,
    }
    return list(applied), provenance
