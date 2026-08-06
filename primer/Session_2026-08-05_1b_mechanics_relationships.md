# Session `1b` — `spell_mechanics` (T4) + relationship graph (T5) — 2026-08-05

> **`HISTORICAL`** — the record of a past session or a completed phase. Immutable. It **may contain claims that are false today**, and that is correct rather than a defect — it records what was believed at the time. **Never citable as current truth.** *(Classified `3f` F8c, 2026-08-07.)*

Overnight autonomous session (owner asleep; two decisions taken before bed, below).
Phase 1 T4 and T5 are **done**: the resolved truth table, the relationship graph, the
bounded trigger attribution, the `spell_scaling` rank migration, and the pre-`1b`
`confirmed_facts` supersession fix from the owner's prep primer. Rebuild is 16 steps,
idempotent (two consecutive full runs produce identical counts), `core/` purity 0.

## Owner decisions taken at session start (2026-08-05, pre-sleep)

1. **Trigger attribution: bounded walk, flagged.** Build all trigger edges, then
   attribute magnitudes through chains up to **depth 2**, cycle-safe, **only when the
   chain is unambiguous** (single path), stored at `confidence='inferred'` with the
   full chain in `evidence_ref`, never overriding a higher-tier value.
2. **On an unforeseen 🛑 while the owner sleeps: log it in PROGRESS' blocked table,
   skip only the dependent piece, continue.** (None arose — the three judgment calls
   below were all resolvable inside existing precedent and are recorded as plan
   changes, not blockers.)

## Pre-`1b` prep (owner's `PRIMER_1b_prep.md`)

Both stale `confirmed_facts` rows qualified **in place** (preferred option):
`hidden_subspell_hoth` and `coefficients_do_not_scale_with_rank_holy_supernova` now
lead with `⚠ SUPERSEDED by <key>` pointers and retain their original text for history.
Verified post-rebuild that a `%Hammer%` / rank-coefficient query surfaces the pointer.
The structural `superseded_by` column deliberately waits for T6 (session `1c`), which
migrates `confirmed_facts` anyway.

## What was built

### T4 — `spell_mechanics` (3,747 rows)

- **Schema** per PHASE_1 T4, verbatim, in `core/db/schema.py` (`PHASE1_MECHANICS_DDL`).
  Key `(spell_id, rank, realm, season)`; `rank` is a label (1a: spell_id already
  identifies a card-rank uniquely).
- **Resolver** `core/spells/mechanics.py :: resolve_spell_mechanics()` — pure, per-field
  §2.2 tier merge, per-field provenance/uncertainty JSON, §2.3 conflicts surfaced never
  resolved, and the four T4 rules in code:
  - magnitudes only from numeric fields (`spell_effect_values`), never description text;
  - `EffectBonusCoefficient` never read as a coefficient;
  - **no rank fallback**: 710 rows carry an explicit `rank_gap` naming the level-60 id;
  - fingerprint/crosswalk/rank helpers reused from `1a`, not re-derived.
- **Level scaling** `flat + (min(level, max_level or level) − spell_level) × per_level`
  with `max_level = 0` = UNCAPPED, in `mechanics.scaled_flat()`.
- **Structural decode from validated bits only**: `ATTR0 0x4` next-swing (validated on
  Lightbound Cleave), `ATTR0 0x40` passive (Improved Cleave), `StartRecoveryTime`
  1500/0 (Divine Storm / LC), effect 31 = weapon-percent-damage (Divine Storm 109→110
  reproduces the doc-confirmed 110%). Unvalidated bits left undecoded.
- **Population**: 3,061 catalog spells + 686 unambiguous level-60 rank siblings (the
  25 ambiguous lines contribute nothing, per §2.3). 29 rows `confidence='conflict'` —
  sampled, **mostly multi-effect-slot collisions** (one spell, two effects, different
  radii/chain counts feeding one column), not cross-source disagreements. T8 should
  bucket these separately.
- **`spell_scaling` rank migration**: `rank` label column stamped; 229 level-60 sibling
  coefficient rows inserted at `source='dbc_rank_sibling_text'` from
  `rank_scaling.catalog_coefficient_gaps()` — exactly **7** differing lines, matching
  `1x`. ⚠ **FK to `spells` dropped** (sibling ids are absent from the export in all 697
  wrong-rank cases; `owned_cards` precedent).
- **`spells` combat-table columns removed** (`crit_table`, `hit_table`,
  `rolls_hit_check`, `proc_icd_seconds`): `seed_spell_flags.py` reworked to seed the
  new `doc_confirmed_mechanics` staging table (7 rows, each with tier + evidence);
  values surface only in `spell_mechanics`. One home per fact, as T4 specifies.

### T5 — `spell_relationships` (5,302 edges) + `core/spells/graph.py`

- Edges: `triggers` 4,670 (from `EffectTriggerSpell` across all extracted DBC records —
  intermediates included so multi-hop chains resolve), `borrows_modifiers` 388 (from
  `modifier_links`), `amplifies` 218 (verbatim amplifier targets, unique-name
  resolution only — duplicate-name trap), `shares_exclusivity_bucket` 17 (pairwise
  within buckets), `amplifies_school` 9 (school in `condition_json`, NULL target).
- **Hand-seeded**: Improved Cleave R1–R3 → Cleave (845) at +40/80/120% — its automated
  extraction landed in manual-review as "Cleave ability", but the magnitude is
  DBC-confirmed in the build handoff (v9). Same discipline as `seed_cp_scaling.py`.
- **Graph queries** (networkx): `neighbourhood` / `find_clusters` / `path_between` /
  `gating_requirements`, all with optional `build_spec`. `amplifies_school` expansion
  honours hybrid double-dipping (Shadowflame ← Fire amplifier) and enters expanded
  edges at `inferred` (primer §5: predictions until proc-tested). `find_clusters`
  excludes trigger edges (the trigger web would merge everything into one component)
  and is deliberately simple — Phase 4 refines it. `path_between(907300, 20496)` now
  answers: Lightbound Cleave —borrows_modifiers→ Cleave ←amplifies— Improved Cleave.
- **Bounded trigger attribution**: **724 magnitude rows across 444 cards** (619 1-hop,
  105 2-hop), 26 multi-path targets skipped unattributed, in-catalog targets never
  attributed (their magnitude is their own row — no double counting). Rows live in
  `spell_effect_values` with `via='trigger_hopN'`, `confidence='inferred'`, chain in
  `evidence_ref`.

### Rebuild-time validations added (fail the chain, not a report)

| Step | Validation |
|---|---|
| `cli/relationships.py` | every multi-member exclusivity bucket appears as an edge group; Lightbound Cleave→Cleave edge exists; 282987's school-damage slot (2–25, +2.4/level) attributed |
| `cli/mechanics.py` | Divine Storm `weapon_damage_pct` = 110; Lightbound Cleave = off-GCD / next-swing / spell-crit; Hammerdin's attributed 282987 term scales to **122–145** at 60; Sun Down's level-60 rank carries **SP 1.3** |

The Hammer from the Heavens check is the session-`1x` resolved formula reproducing
**end-to-end through the new machinery** — trigger walk → numeric decode → level
scaling — with no hand-placed number in the path.

### Freebie

`py cli/rebuild.py` no longer crashes with piped/redirected output —
`run_step()` sets `PYTHONIOENCODING=utf-8` for every child. Verified by running the
full chain redirected to a file.

## Judgment calls made overnight (recorded, not blockers)

1. **`spell_scaling` FK drop** — forced by the FK rejecting sibling rows; resolved by
   the repo's own `owned_cards` precedent (identical cause: export lags client).
2. **"Migrate and retire" → "migrate and demote"** — the staging tables' seed scripts
   own them and run earlier in the chain; retiring the tables meant restructuring five
   seeds mid-session. Demoted to staging inputs instead; `spell_relationships` is the
   query surface. Revisit in `1c` if the duplication bothers.
3. **`exclusivity_buckets` stays a table, not a view** — bucket 3 (Holy Focus) has one
   member; a pairwise-edge view cannot reconstruct a single-member bucket. The doc's
   intent (existing queries keep working) is preserved by keeping the table itself.

## Numbers that should reproduce on any future rebuild

| Metric | Value |
|---|---|
| rebuild steps / status | 16, all exit 0, idempotent |
| `spell_mechanics` rows | 3,747 (29 conflict, 710 rank-gap) |
| `spell_relationships` edges | 5,302 |
| trigger-attributed magnitude rows | 724 (444 cards; 26 ambiguous skipped) |
| `spell_scaling` sibling rows / differing lines | 229 / 7 |
| `doc_confirmed_mechanics` rows | 7 |
| `core/` purity | 18 files, 0 violations |

## Left open for `1c`

- **Compound-form extraction gap** (`($SP+$AP)*x`, `$SPFR*x`) — still open, was not in
  `1b`'s brief.
- **243 manual-review amplifier rows** contribute no edges — standing human-review
  queue for T6.
- **T8 should bucket multi-effect-slot conflicts separately** from cross-source ones.
- The 26 ambiguous trigger targets: each needs a per-case attribution judgment, not a
  looser walk.
