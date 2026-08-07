# Pre-registration — `3i` Block B: the E15 ingest-layer fix

> **`FINDING 2026-08-07`** — committed BEFORE the fix it predicts (the fix commit
> must be a child of this one; verify with `git log`). True as of its date, not
> maintained. *(Born with a status line and an expiry condition, per `3f` F8c —
> superseded in effect once the fix commit records the measured pair.)*

Opening gate: **1 of 36 within ±20% · 1 qualified · slice 20.5% (n=23)**.
Known sibling pair, measured at `3h` C4 and reverted: the consumer dedupe
**alone** moves slice to **19.8%** (counts unchanged). This prereg predicts the
**ingest-layer** fix relative to that.

## The decision being applied (Q2/Q3 defaults, stated as a decision)

The endpoint states pet damage twice: owner-merged inside `rows[]` and restated
per-pet in `pet_spell_damage_by_owner` (discriminated at `3h` D2, report 79).

* **`rows[]` is canonical.** `ability_performance` will hold only `rows[]`
  content; the per-pet restatement is **dropped from that table** at ingest.
* **Pet attribution is preserved separately** in a new additive side table
  (`pet_ability_damage`) — it is the resolution route E3 names
  (`pet_damage_not_derivable`) and must not be lost; it must also never be
  summable into the canonical totals by accident, which is what a separate
  table gives that an `is_pet` flag in the same table did not.
* **The `is_pet` column and primary key are untouched** (Q3: the schema change
  is its own later commit; after this fix the column is constant 0).
* `encounter_performance.dps` becomes `total_damage / duration` — the
  `+ pet_damage` term was adding a restatement (B3). `pet_damage` stays
  populated, from the side table, as the informational "of the total, this
  much was pet-delivered" figure.
* `calibrate_crawled.modelled_damage_share` additionally reads `is_pet = 0`
  only — defensive for any legacy `builds.db`; a no-op on a rebuilt corpus.

## Input measurements taken before this prereg (corpus data, not gate results)

Corpus-wide (2026-08-07, pre-fix `builds.db`), (scope, character, spell)
groups with damage > 0 — reproduces `3h`'s E15 taxonomy exactly:

```
identical     15,551   own 403.2M  pet 403.2M   (the restatement)
owner_gt_pet   4,026   own  79.8M  pet  27.4M   (merge + owner's own casts)
owner_lt_pet   1,208   own  10.5M  pet  80.3M   (excess 69.7M)
owner_only   140,854   own 2325.3M
pet_only       1,642                pet  19.6M
```

🆕 **The 1,208 owner < pet groups are located, not explained:** **0 of them
occur in any `boss_single` scope**; they concentrate in `trash_bundle`
(512 direct + the aggregated `boss_group` scatter), with pet/owner damage
ratios of 5–1800× and pet casts ≫ owner casts (e.g. Firebolt (Wild Imp)
4,067 pet casts vs 143 owner-merged). Consistent with **scope drift between
the payload's two blocks on aggregated scopes** — the pet block covering a
wider window than the `rows[]` merge. Unprovable from our side without
re-fetching trash bundles; **registered in the E15 closure rather than
resolved**. Consequence of the rows[]-canonical rule: the 69.7M excess +
19.6M pet-only (~3.2% of corpus owner-side damage) is **excluded from
canonical totals** and preserved in the side table with this caveat.

Cohort pet exposure (tuning set, SUM(is_pet=1) as % of SUM(is_pet=0), the
fix's per-character lever): Malo 121%, Onur 118%, David 107%, Ikkura 77%,
Chastie 63%, Jamppa 42%, Ari 18%, Meritania 10%, … Boomcat 3.4%.
(Holdout members carry pet rows too; their gate results are not read.)

## Predictions

* **P1 — slice accuracy moves DOWN from 20.5%**, landing in the vicinity of
  the known 19.8% consumer-dedupe pair. The ingest fix contains that dedupe's
  coverage effect; the `dps` correction additionally RAISES pet owners'
  `delta_pct` (logged denominator shrinks, sim unchanged, deltas negative →
  toward zero), which pushes their slice numerators UP — so the final median
  may sit slightly above 19.8, but below 20.5.
* **P2 — `within ±20%` count UNCHANGED at 1, qualified UNCHANGED at 1.**
  `Boomcat` (the passer) has 3.4% pet exposure; no failing tuning member is
  close enough for a ≤2× pet-share correction to cross ±20%.
* **P3 — the biggest `delta_pct` movers are the biggest pet-exposure members**:
  Malo, David, Onur, Ikkura, Chastie, Jamppa (ENGINE_BUGS' named trio Malo /
  Ikkura / Onur all among them), every one moving UP (toward zero).
* **P4 — coverage (`modelled_damage_pct`) moves UP on net** (the direction the
  dedupe run measured).

**Willing to be wrong:** if slice moves UP from 20.5%, or either count
changes, the model of this fix is wrong — stop, report, and investigate
before any further block runs.
