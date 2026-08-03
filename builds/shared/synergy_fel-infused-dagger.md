# Fel Infused Weapon — engine reference
**Source:** group parse, dagger/hybrid character
**Status:** internal test — no ICD confirmed via tooltip

## Engine
- Trigger: every auto attack and melee ability (no ICD)
- Effect: flat Shadowflame damage per hit
- Class tag: no "uses X modifiers" clause in its own tooltip (this is a native craft-your-own weapon-imbue card, not a borrowed-modifier proc). Recorded in `seed_confirmed.py` as `class_origin='Duality'` / `confirmed_native` (Primer §1 v6) — that's a **Path** fit, not a WotLK class; no class-tag ambiguity applies here the way it does for borrowed-modifier cards.

## Scaling
- Formula: flat + AP*0.05 + SP*0.05 Shadowflame per hit
- Confirmed multipliers: Primer §1 (v6) — no internal cooldown stated in the tooltip; fires on every landed auto attack *and* melee ability, not a proc chance.

## Synergy tags
no-ICD, dual-wield, attack-speed-scaling

## Relevance to our builds
Reported up to ~30% of total DPS for hyper-fast dual-wield attackers.
Weapon speed can outweigh weapon DPS when a build carries a no-ICD
per-hit card like this — check ICD presence before assuming fast weapons
dilute per-hit effects.
