"""Phase 2 T4 — `compute_stats()`: BuildSpec + content -> CharState.

ONE implementation used by every consumer (sim, legos, builder, guides) —
path bonuses, percentage multipliers and stat conversions interact, and two
implementations would diverge (PHASE_2 T4).

What is modelled in 2a, honestly:

* **`stats_override` is the primary path** until Phase 3 lands an items table.
  Its semantics: FINAL character-sheet values (path, talents and gear already
  baked in). Path *stat* bonuses are NOT reapplied on top — only the weapon-
  clause damage multipliers attach (a sheet never shows those) plus warnings.
* **Component mode** (no override): gear item stats + path flat grants + path
  conversions + base-game stat->crit conversions. Talent stat contributions
  are NOT modelled yet — each unmodelled slot lands in `warnings`, never
  silently contributes zero without saying so.
* **Path magnitudes carry their evidence status inline** (primer §3 +
  confirmed_facts). The Duality SP amp is the measured 1.895x (controlled
  empty-spec test 2026-08-04, `duality_sp_amp_confirmed_reverses_retraction`),
  NOT the tooltip's 1.75. The Duality AP factor 0.548x is a measured ANOMALY
  contradicting the tooltip (`duality_attack_power_anomaly`, open) — it is a
  parameter, and using it always warns.
"""
from dataclasses import dataclass, field

from ..sim.combat_engine import RatingConversions

# --- base-game stat -> crit conversions (ascension_confirmed, measured) --------
# build_paladin-hammerdin §12: Agi -> melee crit ~32.4/1%, Int -> spell crit ~61/1%.
AGI_PER_MELEE_CRIT_PCT = 32.4
INT_PER_SPELL_CRIT_PCT = 61.0

# --- Duality measured factors --------------------------------------------------
# confirmed_facts.duality_sp_amp_confirmed_reverses_retraction: SP 229 -> 434
# on identical gear, empty spec => 1.895x (tooltip says 1.75 — measurement wins).
DUALITY_SP_AMP_MEASURED = 1.895
# open_question elric_active_path_and_duality_ap_anomaly: AP measured at 0.548x
# the Path of Strength value, contradicting "AP = highest of Str or Agi".
DUALITY_AP_FACTOR_MEASURED = 0.548


@dataclass
class CharState:
    """Resolved character state the sim consumes. Percent fields are final
    percentages; rating fields are pre-conversion where named `_rating`."""
    level: int
    # primary stats
    strength: float = 0.0
    agility: float = 0.0
    intellect: float = 0.0
    spirit: float = 0.0
    stamina: float = 0.0
    # offense
    attack_power: float = 0.0
    ranged_attack_power: float = 0.0
    spell_power: float = 0.0
    spell_power_by_school: dict = field(default_factory=dict)  # 'Holy' -> bonus
    bonus_healing: float = 0.0
    # chances (final, post-conversion)
    melee_crit_pct: float = 0.0
    spell_crit_pct: float = 0.0
    melee_hit_pct: float = 0.0
    spell_hit_pct: float = 0.0
    melee_haste_pct: float = 0.0
    spell_haste_pct: float = 0.0
    expertise_points: float = 0.0
    armor_pen_pct: float = 0.0
    # weapons: {'min','max','speed'} or None
    main_hand: dict | None = None
    off_hand: dict | None = None
    # named multiplier buckets, e.g. 'physical_ability' -> 1.10. Consumers
    # multiply the buckets that apply to an ability; unknown buckets are ignored
    # BY NAME, never silently — ability_model surfaces which buckets it applied.
    damage_multipliers: dict = field(default_factory=dict)
    ability_crit_damage_bonus: float = 0.0   # additive on the crit multiplier
    # T4b: the build's decoded talent effects, or None when talents were not
    # modelled (no `conn` passed to compute_stats). None and "no talents" are
    # different states and the ability model reports which one it saw.
    talents: object = None
    # Resource pools and regen, for the medium sim's castability question.
    # EMPTY MEANS UNKNOWN, not zero: medium_sim refuses to model starvation
    # rather than assuming an infinite bar or an empty one.
    resource_pools: dict = field(default_factory=dict)   # 'mana' -> max value
    resource_regen: dict = field(default_factory=dict)   # 'mana' -> per second
    # Path of Agility's 1H clause reduces GCD and cost by 8%; 2a recorded it as
    # "rotation-level, medium sim (2b) owns it" and this is where it arrives.
    gcd_modifier_pct: float = 0.0            # negative = faster
    resource_cost_modifier_pct: float = 0.0  # negative = cheaper
    warnings: list = field(default_factory=list)

    def effective_spell_power(self, school):
        """Generic SP + school-specific bonus. School-scoped scaling terms
        (SPFR/SPH/...) resolve through this — treating them as generic SP
        double-counts (1c audit kickoff note #2)."""
        return self.spell_power + self.spell_power_by_school.get(school or "", 0.0)


# ------------------------------------------------------------- path bonus data

# primer §3. Each entry lists what IS modelled; anything the primer states that
# is NOT modelled here must be warned about by name in compute_stats.
# Flat grants use the primer's stated curves; '~' values are approximations and
# say so in the warning they emit.


def _flat_grants(path, level):
    """Path flat stat grants (primer §3). Returns (stat_deltas, notes)."""
    if path == "Strength":
        return {"strength": 4 + 0.5 * level}, []
    if path == "Agility":
        return {"agility": 4 + 0.5 * level}, []
    if path in ("Intelligence", "Healing"):
        return ({"intellect": 4 + 1.25 * level, "spirit": 40.0},
                ["path spirit grant ~40 is approximate (primer §3 '~40')"])
    if path == "Duality":
        # primer §3 states no flat grant for Duality
        return {}, []
    return {}, []


def _weapon_clause(path, wielding):
    """Path weapon-clause effects -> (damage_multipliers, crit_damage_bonus,
    haste_bonus_pct(melee, spell), notes). primer §3; 'abilities' wording
    excludes auto-attacks (ascension_confirmed)."""
    mults, crit_dmg, haste_m, haste_s, notes = {}, 0.0, 0.0, 0.0, []
    gcd_mod = cost_mod = 0.0
    is_2h = wielding in ("2h", "dual_2h")
    if path == "Strength":
        if is_2h:
            mults["physical_ability"] = 1.10   # excludes autos ("abilities")
        else:
            notes.append("Strength 1H +20% ArP clause not yet modelled as "
                         "rating — flagged instead of silently dropped")
    elif path == "Agility":
        if is_2h:
            crit_dmg = 0.20                    # ability crit damage bonus
        else:
            # primer §3: damaging melee/ranged abilities' GCD and cost -8%.
            # Carried on CharState for the medium sim rather than folded into a
            # damage number — it is a castability effect, not a damage one.
            gcd_mod = cost_mod = -8.0
    elif path == "Duality":
        if is_2h:
            mults["all_damage"] = 1.06         # magic AND physical +6%
        else:
            haste_m = haste_s = 10.0
    elif path == "Intelligence":
        if is_2h:
            haste_s = 12.0
        else:
            mults["spell_damage"] = 1.05
    elif path == "Healing":
        if is_2h:
            haste_s = 10.0
            notes.append("Healing 2H +3% spell crit applied")
        else:
            notes.append("Healing 1H +5% healing clause not modelled yet")
    return mults, crit_dmg, haste_m, haste_s, gcd_mod, cost_mod, notes


# --------------------------------------------------------------- gear loading

# scouted_gear stats_json key normalisation. Conservative: unknown keys warn.
_GEAR_STAT_KEYS = {
    "strength": "strength", "agility": "agility", "intellect": "intellect",
    "spirit": "spirit", "stamina": "stamina",
    "attack_power": "attack_power", "ranged_attack_power": "ranged_attack_power",
    "spell_power": "spell_power", "healing_power": "bonus_healing",
}
_GEAR_RATING_KEYS = {
    "crit_rating": "crit", "hit_rating": "hit", "haste_rating": "haste",
    "expertise_rating": "expertise", "armor_penetration_rating": "armor_penetration",
}


def compute_stats(build_spec, content, conversions: RatingConversions,
                  duality_sp_amp=DUALITY_SP_AMP_MEASURED,
                  duality_ap_factor=DUALITY_AP_FACTOR_MEASURED,
                  conn=None):
    """Resolve a BuildSpec into a CharState for `content`.

    Pass `conn` to model talents (session 2c, T4b). Without it the 2a behaviour
    is preserved — talents contribute nothing and say so.

    🛑 **Sheet mode and talents interact, and getting it wrong double-counts.**
    `stats_override` means the values are FINAL character-sheet readings, and a
    sheet already includes every talent's contribution to crit, AP, SP and
    haste. So in sheet mode only the talents' DAMAGE MULTIPLIERS are applied —
    a sheet never displays those — and their stat contributions are deliberately
    dropped. In component mode both halves apply.
    """
    warnings = list(conversions.warnings)
    level = build_spec.character_level
    wielding = build_spec.wielding()

    cs = CharState(level=level)

    # ----- weapons come from gear either way ------------------------------
    for slot_name, attr in (("main_hand", "main_hand"), ("off_hand", "off_hand")):
        g = build_spec.gear.get(slot_name)
        if g and g.weapon:
            setattr(cs, attr, {k: g.weapon[k] for k in ("min", "max", "speed")
                               if k in g.weapon})

    if build_spec.stats_override:
        # ----- sheet mode: values are FINAL; do not reapply path stats -----
        for k, v in build_spec.stats_override.items():
            if hasattr(cs, k) and not isinstance(getattr(cs, k), (dict, list)):
                setattr(cs, k, v)
            elif k == "spell_power_by_school":
                cs.spell_power_by_school = dict(v)
            elif k in ("resource_pools", "resource_regen", "damage_multipliers"):
                setattr(cs, k, dict(v))
            elif k in ("hit_rating", "crit_rating", "haste_rating",
                       "expertise_rating", "armor_pen_rating"):
                # ratings supplied raw: convert here so sheet users can paste
                # the sheet's rating numbers directly
                if k == "hit_rating":
                    cs.melee_hit_pct = conversions.percent("hit_melee", v)
                    cs.spell_hit_pct = conversions.percent("hit_spell", v)
                elif k == "crit_rating":
                    cs.melee_crit_pct += conversions.percent("crit_melee", v)
                    cs.spell_crit_pct += conversions.percent("crit_spell", v)
                elif k == "haste_rating":
                    cs.melee_haste_pct = conversions.percent("haste_melee", v)
                    cs.spell_haste_pct = conversions.percent("haste_spell", v)
                elif k == "expertise_rating":
                    cs.expertise_points = v / conversions.divisors["expertise"] \
                        if conversions.divisors.get("expertise") else 0.0
                elif k == "armor_pen_rating":
                    cs.armor_pen_pct = conversions.percent("armor_penetration", v)
            else:
                warnings.append(f"stats_override key {k!r} not recognised — "
                                "ignored (named, not silent)")
        warnings.append(
            "stats_override in use: sheet values treated as FINAL (path stats, "
            "talents, gear assumed already included) — only weapon-clause "
            "multipliers were added on top")
    else:
        # ----- component mode: gear + path, talents NOT yet modelled -------
        for g in build_spec.gear.values():
            for k, v in (g.stats or {}).items():
                key = k.lower()
                if key in _GEAR_STAT_KEYS:
                    setattr(cs, _GEAR_STAT_KEYS[key],
                            getattr(cs, _GEAR_STAT_KEYS[key]) + v)
                elif key in _GEAR_RATING_KEYS:
                    r = _GEAR_RATING_KEYS[key]
                    if r == "crit":
                        cs.melee_crit_pct += conversions.percent("crit_melee", v)
                        cs.spell_crit_pct += conversions.percent("crit_spell", v)
                    elif r == "hit":
                        cs.melee_hit_pct += conversions.percent("hit_melee", v)
                        cs.spell_hit_pct += conversions.percent("hit_spell", v)
                    elif r == "haste":
                        cs.melee_haste_pct += conversions.percent("haste_melee", v)
                        cs.spell_haste_pct += conversions.percent("haste_spell", v)
                    elif r == "expertise":
                        cs.expertise_points += v / conversions.divisors["expertise"]
                    elif r == "armor_penetration":
                        cs.armor_pen_pct += conversions.percent(
                            "armor_penetration", v)
                else:
                    warnings.append(
                        f"gear stat key {k!r} on {g.name} not recognised — "
                        "ignored (named, not silent)")

        grants, notes = _flat_grants(build_spec.path, level)
        warnings.extend(notes)
        for stat, delta in grants.items():
            setattr(cs, stat, getattr(cs, stat) + delta)

        # path AP conversions (primer §3)
        if build_spec.path == "Strength":
            cs.attack_power += cs.strength          # AP = 100% of Strength
            warnings.append("Strength->parry conversion not modelled")
        elif build_spec.path == "Agility":
            cs.attack_power += cs.agility
            warnings.append("Agility path crit-DAMAGE-from-Agi clause not "
                            "modelled (magnitude unmeasured)")
        elif build_spec.path == "Duality":
            # tooltip: AP = highest of Str or Agi. MEASURED: 0.548x the PoS
            # value on the same character (open question
            # elric_active_path_and_duality_ap_anomaly). Parameterised.
            cs.attack_power += max(cs.strength, cs.agility) * duality_ap_factor
            warnings.append(
                f"Duality AP factor {duality_ap_factor} is a measured ANOMALY "
                "contradicting the tooltip's 'highest of Str/Agi' — open "
                "question elric_active_path_and_duality_ap_anomaly; pass "
                "duality_ap_factor=1.0 to model the tooltip instead")
        if build_spec.path == "Duality":
            cs.spell_power *= duality_sp_amp
            warnings.append(
                f"Duality SP amp {duality_sp_amp}x applied (measured 2026-08-04, "
                "controlled empty-spec test; tooltip claims 1.75)")
            warnings.append(
                "Duality Int->melee-crit / Agi->spell-crit conversions are "
                "confirmed REAL but their rates are unmeasured — NOT applied; "
                "sheet-mode (stats_override) captures them exactly")
        elif build_spec.path == "Intelligence":
            cs.spell_power *= 2.0    # "SP from items and effects DOUBLED"

        # base-game stat->crit (ascension_confirmed measured rates)
        cs.melee_crit_pct += cs.agility / AGI_PER_MELEE_CRIT_PCT
        cs.spell_crit_pct += cs.intellect / INT_PER_SPELL_CRIT_PCT

        n_talents = len(build_spec.talents)
        if n_talents and conn is None:
            warnings.append(
                f"{n_talents} slotted talents contribute NO stats/multipliers — "
                "compute_stats was called without a `conn`, so T4b's talent "
                "model could not run; output underestimates")

    # ----- talents (T4b, session 2c) ---------------------------------------
    if conn is not None and build_spec.talents:
        from ..sim.talents import resolve_talents
        cs.talents = resolve_talents(conn, build_spec.talents)
        warnings.extend(cs.talents.warnings)
        if build_spec.stats_override:
            warnings.append(
                "talents: DAMAGE MULTIPLIERS applied; their crit/AP/SP/haste "
                "contributions deliberately NOT applied, because sheet mode "
                "means those are already in the numbers you supplied. Applying "
                "both would double-count them")
        else:
            cs.attack_power *= 1.0 + cs.talents.scalar("attack_power_pct") / 100.0
            cs.ranged_attack_power *= \
                1.0 + cs.talents.scalar("ranged_attack_power_pct") / 100.0
            cs.melee_haste_pct += cs.talents.scalar("melee_haste_pct")
            for m in cs.talents.modifiers:
                if m.kind == "spell_power_from_stat_pct" and m.value:
                    stat = (m.scope.get("stat") or "").lower()
                    src = getattr(cs, stat, 0.0) if stat else 0.0
                    cs.spell_power += src * m.value / 100.0
                elif m.kind == "healing_from_stat_pct" and m.value:
                    stat = (m.scope.get("stat") or "").lower()
                    cs.bonus_healing += getattr(cs, stat, 0.0) * m.value / 100.0
            # crit talents are school- and table-scoped, so they cannot collapse
            # into the two scalar crit fields without losing that scoping. They
            # are applied per event by the ability model instead.
            warnings.append(
                "talent crit bonuses are school/table-scoped and are applied "
                "PER EVENT by the ability model, not folded into "
                "melee_crit_pct/spell_crit_pct here")

    # ----- weapon clauses apply in both modes ------------------------------
    mults, crit_dmg, haste_m, haste_s, gcd_mod, cost_mod, notes = _weapon_clause(
        build_spec.path, wielding)
    warnings.extend(notes)
    for bucket, m in mults.items():
        cs.damage_multipliers[bucket] = cs.damage_multipliers.get(bucket, 1.0) * m
    cs.ability_crit_damage_bonus += crit_dmg
    cs.melee_haste_pct += haste_m
    cs.spell_haste_pct += haste_s
    cs.gcd_modifier_pct += gcd_mod
    cs.resource_cost_modifier_pct += cost_mod
    if build_spec.path == "Healing" and wielding in ("2h", "dual_2h"):
        cs.spell_crit_pct += 3.0

    # ascension_confirmed (primer §3): Titan's Grip -10% physical is a CARD
    # magnitude, not a path clause — it belongs to talent/ability modelling,
    # so dual_2h wielding warns rather than silently applying it here.
    if wielding == "dual_2h":
        warnings.append(
            "Titan's Grip -10% physical (card magnitude) not applied by "
            "compute_stats — belongs to ability/talent modelling")

    if build_spec.consumables:
        warnings.append(f"{len(build_spec.consumables)} consumables not modelled")
    if build_spec.raid_buffs and content.raid_buffs_available:
        warnings.append(f"{len(build_spec.raid_buffs)} raid buffs not modelled")
    elif build_spec.raid_buffs and not content.raid_buffs_available:
        warnings.append(
            "raid_buffs ignored: content profile has raid_buffs_available=False")

    cs.warnings = warnings
    return cs
