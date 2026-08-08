# Pre-registration — `3l` C2: ContentProfile durations become corpus-measured, and the gate is predicted NOT to move

> **`FINDING 2026-08-08`** — committed BEFORE the preset change it predicts.
> Every number under "Predictions" is UNMADE at the time of writing;
> `git log --format='%H %p %s'` proves parenthood. True as of its date, not
> maintained.

## The change being registered

The three gate-feeding `ContentProfile` presets in `core/sim/content.py` get
their `fight_duration` replaced with a corpus measurement, and their
`provenance` strings become `measured: <query>`:

| preset | duration today | becomes | source |
|---|---:|---:|---|
| `raid_boss_st` | 75.0 (scouted fastest-kill ×1.5 estimate) | **78.1** | median, n=33 |
| `raid_boss_cleave` | 75.0 (same estimate) | **78.1** | same (shares content_type `raid`) |
| `mythic_dungeon_st` | 60.0 (`assumption:`) | **39.9** | median, n=566 |

The measurement, run 2026-08-08 on `builds.db` derived from the tree at
`f7b14af` (corpus: 472 snapshots):

```sql
SELECT e.content_type, e.duration_seconds
FROM capture_scopes cs JOIN encounters e ON e.encounter_id = cs.encounter_id
WHERE e.duration_seconds IS NOT NULL
  AND e.content_type IN ('raid','dungeon_normal')
```

- `raid`: n=33, **median 78.1 s** (mean 88.5, IQR 49.3–112.1, range 24.5–235.9)
- `dungeon_normal`: n=566, **median 39.9 s** (mean 49.0, IQR 26.0–59.9, range 3.6–396.2)

Median over mean because both distributions are right-skewed (a 396 s outlier
dungeon pull; a 236 s raid wipe-length kill). Scope-joined encounters only —
these are exactly the encounters the gate's `boss_single` scopes cite, per
`CONTENT_PRESET` (`calibrate_crawled.py:368`): `raid → raid_boss_st`,
`dungeon_normal`/`dungeon_mythic → mythic_dungeon_st`.

The other five presets (`raid_aoe`, `mythic_dungeon_aoe`, `dungeon_normal_aoe`,
`world_boss`, `solo_grind`) have **no corpus measurement** — no scope the gate
uses maps to them, `dungeon_mythic` has zero corpus rows, and trash_bundle
scopes carry no encounter durations. They keep their `assumption:` strings.
Fabricating a measurement for them would be worse than the assumption.

## Predictions

**P1 — the gate does not move. Not approximately: to the digit.**
`gate_manifest_3e.json` regenerated after the change equals the committed
pre-C2 baseline (`5b1dd3d`, git_sha `f7b14afb`): **0 of 35 within ±20% ·
0 qualified · slice 26.3% (n=23)**, same per-character deltas, same
admissibility flags (Nodding / Boomcat / Deyindra), same band table.

**P2 — the instrument does not move either.** `per_ability_summary.json`
regenerated after the change equals the committed B0 baseline (`f7b14af`):
absent 59.9% / producing median 0.2573 (n=107) / phantom 53.8% / 274
per-key rows.

**The mechanism, stated before the run:** the gate runs `fast_sim`, whose
closed form is *linear in fight duration end to end* — every cast count is
`available / interval` or `budget / occupancy` with
`available = fight_duration × (1 − movement_pct)`, per-cast damage never reads
`fight_duration` (verified: `ability_model.py` touches only `content.target`),
and the reported DPS divides the total by `fight_duration` again. Duration
cancels exactly; `movement_pct` (unchanged) is the only surviving factor.
The presets' durations are load-bearing for `medium_sim`/`slow_sim` (timeline
execute windows, buff uptimes) and for honesty of provenance — not for this
gate.

**What is NOT predicted:** anything about `medium_sim`/`slow_sim` outputs
(nothing in the gate path runs them); anything about future gates that adopt
timeline tiers.

**Falsifier:** any digit of P1 or P2 changing. If the gate moves at all, the
linearity claim above is wrong about the code as it actually runs, the move is
a FINDING to diagnose (not a success), and attribution stops until it is
explained.

## Why this is C2 and not part of the tuning prereg

§0 rule 3: presets feed the sim side of the very gate the tuning pass will be
judged on. If this landed mid-tuning and the gate moved, nobody could say
which change did what. It lands first, alone, with its own pair — and the
predicted pair delta is zero.
