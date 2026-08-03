# Fel Cleave — leveling/alt build (WIP)

## Status
WIP — theorycraft only, no talent board committed.

## Engine
- **Fel Cleave** (id 276066) — Warrior-tagged via the class-tag rule: raw client tooltip reads *"This uses Cleave modifiers"*, but that clause is entirely absent from the export tooltip — found via the DBC extraction pipeline, not a live screenshot (primer §4/§11 v11).
- **Shadowflame** school — a hybrid: physical weapon-damage half + Shadowflame magic half, double-dips modifiers from both component schools (primer §1).
- **Not part of the current Paladin kit** — flagged explicitly in `seed_confirmed.py` so it doesn't get mistaken for something already covered by `build_paladin-hammerdin.md`.

## Why this is worth a WIP file
Same shape as Lightbound Cleave (also Warrior-tagged, also Cleave-borrowing) but on the Shadowflame school instead of Holystrike — worth a look if a Shadowflame-leaning alt or leveling build ever gets picked up, since the class-tag mechanism (and therefore which talents actually buff it) is already resolved.

## Open questions
- No proc-test yet — Warrior tag is `confirmed_class_tag_rule` (stated as fact from the DBC read), not `confirmed_proc_test`. Confirm with a dummy parse before relying on it for engine-gating decisions (primer §4).
- No scaling coefficients pulled yet from `spell_dbc_raw`/`index/dbc-extract.json` — `EffectBasePoints`/`EffectBonusCoefficient` for this spell haven't been reviewed.
- No talent/gear plan — this file is a placeholder for "worth investigating," not a build.
