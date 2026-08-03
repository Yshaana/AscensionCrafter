# Project Ascension — Titan's Grip: Staff/Polearm + Off-hand Clause v1

**What this is:** a single-tooltip finding (user-spotted, tooltip-confirmed against `spell-export.json`), not a scouted character. Filed as a synergy note because it's a generic, class-agnostic gear-slot trick, same spirit as the other portable packages.

---

## The finding

**Titan's Grip** (id 46917, single rank) has two separate clauses in one tooltip:

> *"Allows you to wield a Two-Handed Axe, Mace, or Sword in each hand. Also allows for a weapon or shield to be held in the off-hand while a Staff or Polearm is equipped. Physical damage dealt is reduced by [X]%."*

1. **Dual-2H-melee clause** — wield two 2H Axes/Maces/Swords at once. This is the clause our own Paladin/Hammerdin build already runs.
2. **Staff/Polearm + off-hand clause** — a Staff or Polearm normally occupies both weapon slots on its own. This clause frees up the off-hand slot anyway, letting a caster equip a Staff **and** a separate off-hand weapon or shield simultaneously — a free extra item's worth of stats (crit/hit/SP/whatever the off-hand piece rolls) for any caster archetype, at zero opportunity cost against the 2H-melee use case (they're different weapon categories, not competing for the same gear).

## Caveat

The tooltip's physical-damage-reduction penalty (`$S3%`, unresolved magnitude in the export — same hidden-placeholder problem the primer already tracks for other cards) is worded as a blanket reduction to "physical damage dealt," not explicitly scoped to only the dual-2H-melee configuration. For a pure caster who deals little/no physical damage, this is likely irrelevant — but if this clause is ever paired with a hybrid kit that deals real physical damage alongside spell damage (e.g. any Holystrike-adjacent hybrid), confirm the penalty doesn't clip that portion before assuming it's free.

## Status

Not tested on our own build — we currently use the dual-2H-melee clause, not this one. Filed as a reference note for any future caster-archetype build, or if our own build's weapon-slot posture ever changes.

## Assumption register

**Confirmed (tooltip, `spell-export.json`, id 46917):**
- ✅ Both clauses' exact wording as quoted above.

**Unconfirmed / open:**
- ❓ Exact magnitude of the physical damage reduction (`$S3%` unresolved in export).
- ❓ Whether the penalty applies globally whenever Titan's Grip is slotted, or only while actually using the dual-2H-melee configuration.
