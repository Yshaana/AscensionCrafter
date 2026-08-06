# Session 0a — Recon (Phase 0 Tasks 1–5, 7, 8, 9)

> **`HISTORICAL`** — the record of a past session or a completed phase. Immutable. It **may contain claims that are false today**, and that is correct rather than a defect — it records what was believed at the time. **Never citable as current truth.** *(Classified `3f` F8c, 2026-08-07.)*

**Date:** 2026-08-04 · **Session ID:** `0a` · **Status:** ✅ done
**Deliverable:** `primer/RECON_FINDINGS.md` — one verdict per task, with evidence.
**Phase 0 is complete.** Phase 1 is no longer gated.

This file is the *session* record: what was done, what shipped, what surprised me, what I'd tell the
next session. The *findings* live in `RECON_FINDINGS.md` and are not duplicated here.

---

## The six results that changed the plan

1. **Task 5's gate is open.** `entry_id` is the CharacterAdvancement ID, and `CharacterAdvancement.dbc`
   exists in the client — so the crosswalk is a real table, not an inference. 1,054/1,054 crawled
   entry_ids resolve; 0 of 1,054 equal a catalog `spells.id`.
2. **Rank resolution is solved and it is level-gated**, not contiguous-id. It reproduces the owner's
   own tooltips exactly. **≈50% of the multi-rank catalog carries the wrong rank's magnitudes.**
3. **Class resolution went 13% → 58%** — via skill-line *names*, because Ascension renamed them to
   classes. Agrees with 382/387 existing rows and 7/7 of primer §4's proof cases.
4. **98% of the 803 "blocked" hidden-formula spells resolve from numeric DBC fields.** Phase 0 asked
   for this to be flagged loudly if large. Phase 1's highest-value task.
5. **The client DBC is the earliest complete card source** — 52/52 newly-announced cards are in it,
   2/52 are in the catalog export.
6. **Phase 3 T4 re-scoped**: BisBeard takes stat weights as input and owns items/BiS; we own the
   simulator. Gear *data* source is still open.

---

## What shipped

| File | Change |
|---|---|
| `primer/RECON_FINDINGS.md` | **new** — the Phase 0 deliverable |
| `primer/PHASE_0_recon_and_data_capture.md` | v3 — completion header + three inline corrections |
| `primer/INDEX_GUIDE.md` | v8 — new tables, endpoint additions, self-contradiction fixed, v3 claim corrected |
| `index/build_dbc_index.py` | CharacterAdvancement / SkillLine / SkillLineAbility / `gt*` / rank-line extraction; rank-sibling scoping; **two idempotency bugs fixed** |
| `index/dbc-ascension-extract.json` | **new committed artifact** (~16 MB, 128,110 rows) |
| `index/seed_confirmed.py` | +14 facts (89 → 103) |
| `tools/scrapers/parse_changelog.py` | **new** — the Task 3 parser |
| `primer/PROGRESS.md` | next session set to `1a` |

### New tables in `ascension_index.db`
`dbc_character_advancement` (10,231) · `dbc_spell_rank` (42,606) · `dbc_spell_class` (10,864) ·
`dbc_gt_tables` (22,564) · `dbc_skill_line` (872) · `dbc_skilllineability` (40,973)

---

## Two bugs worth remembering

**`build_dbc_index.py` was destructively non-idempotent, in two places.** Running it twice in a row
took `spell_scaling`'s `dbc_hidden_formula` rows from **113 → 0**, and shrank `spell_dbc_raw`. Cause:
the resolver clears `has_hidden_formula` on success, and *both* the resolver's target query and the
raw-table scoping filter selected on that flag — so a second run deleted its own output and then
found nothing to re-derive. Fixed and verified: clean run and re-run now both give 84/887, 113 rows,
15,769 raw rows.

**This invalidated a documented claim** (`INDEX_GUIDE` v3: "not incremental"), and it means **any
coverage number published from this pipeline before today was only reproducible from a clean
database**. Corrected in `INDEX_GUIDE`.

**And then a third instance of the same bug class turned up in `seed_confirmed.py`** — it INSERTs
into `confirmed_facts` without clearing first, so running it twice without an intervening
`build_index.py` rebuild **doubles every fact**. Caught live (103 → 213 rows) while re-seeding. Fixed
with a `DELETE FROM confirmed_facts` — safe because `build_index.py` creates the table and nothing
else writes to it. Audited the other seven seeders at the same time: `seed_synergies` is safe
(`INSERT OR IGNORE` against a `UNIQUE` name), `seed_cp_scaling` is safe (guards on a row count), the
rest only UPDATE. Whole chain verified idempotent — two consecutive seed passes both give
`confirmed_facts=110, shared_synergies=9, spell_scaling=716`.

**Worth generalising:** three idempotency bugs in one day, all the same shape — *a script that
derives rows without owning the deletion of its own previous output*. Worth a standing check on any
new seeder/ingester in Phase 1.

**The scoping filter was also hiding real data.** `spell_dbc_raw` was scoped to catalog ids ±3, but
rank ids are frequently non-contiguous — so the spell a level-60 character actually casts was being
excluded. That is the entire reason 274132 was on record as "absent from the client." It never was.

---

## Method notes for the next session

- **The fingerprint rule earned its keep twice.** The one numeric `entry_id`↔`spells.id` collision
  (50043) is two unrelated cards, and the two "Holy Supernova" lines turned out to be two separate
  CA cards. Both would have produced a wrong conclusion under name matching.
- **Reverse-engineering an undocumented DBC works well with crawled anchors.** The CA layout was
  recovered by voting slot-by-slot against 1,054 known (entry_id, name) pairs rather than guessing.
  Unmapped slots went into `raw_ints_json` verbatim — decode later without re-extracting.
- **Sensitivity-check derived counts.** The "697 catalog entries at the wrong rank" figure was
  re-run under four rank-line grouping strictnesses; it moves only between 697 and 794. Reporting
  the range is more honest than the point estimate.
- **Answer from captured data before making requests.** Every Task 2 question was settled from the
  existing crawl. Zero automated requests were made to `db.ascension.gg` (robots), and BisBeard was
  read-only with probing stopped rather than host-guessing.

---

## Surprises

- **`character_spec` in per-ability rows is the PATH** (`Duality`/`Intelligence`/`Strength`/
  `Agility`/`Healing`). Per-parse Path attribution for every logged character, free, previously
  undocumented.
- **BisBeard independently keys on `entryId` and carries no spellId at all** — a separately-maintained
  tool reaching the same conclusion as Task 5.
- **The official builder embeds its whole catalog in an 11.9 MB inline script**, with explicit
  `{direct_bonus, dot_bonus, ap_bonus, ap_dot_bonus}` coefficients and per-rank resolved text — but
  only for **Area-52 and Elune**, so §2.5 forbids applying any of it to Darkmoon.
- **`ItemStat.dbc` has 1,513,931 records.** A full client-side item database exists. Not extracted
  (out of scope, layout unverified), but it means the gear database may not need a third party.

---

## What I did NOT do, deliberately

- **No automated `db.ascension.gg` requests.** §1a + the owner's standing decision. Task 1's "fetch
  ~30 spells" was superseded before it was ever run.
- **Did not resolve the 5 class conflicts.** §2.3 — recorded both sides, queued for verification.
- **Did not extract `Item.dbc`/`ItemStat.dbc`.** Out of Phase 0's scope and the layout is unverified.
- **Did not chase BisBeard's item-JSON host.** Guessing hosts is the crawling behaviour the courtesy
  note warns against.
- **Did not commit anything.** Working tree is dirty and ready — see below.

---

## 🛑 For the owner

**Nothing is blocking.**

1. **Uncommitted work.** This session's changes are in the working tree but **not committed**, since
   committing wasn't requested. Say the word and I'll commit and push.
2. ✅ **Both requested lookups were supplied and are folded in** — see `RECON_FINDINGS.md` Task 1.
   Fel Infused Weapon's school was never a real conflict (Fire *enchant* spell, Shadowflame damage
   sub-spell); Holy Supernova's AP term is a three-way split of no practical consequence. They also
   produced three unplanned results: independent confirmation of the level-gate rank rule, three-way
   agreement that **Holy Supernova is Priest-tagged** (so it does **not** feed Hammerdin), and a
   partial answer to "do coefficients scale with rank?" (they don't; only flats do).
3. **One cheap in-game read left, if you want it:** **Fel Infused Weapon's tooltip at level 60.**
   db renders its per-level term as **4.5**, the client DBC says **1.5** — exactly 3×. The in-game
   number is fully resolved and settles it. Related: the existing "flat ≈ 5.5" figure in
   `seed_confirmed` has the wrong *shape* — `EffectRealPointsPerLevel` is a per-level rate, not a
   flat add.

Also flagged, not acted on: the 2026-08-04 changelog announced **`[Authority]`** — *"Execution
Sentence's periodic damage increases…"* — which touches a chase-list ability whose magnitude
`build_paladin-hammerdin.md` §8 records as unresolved.

---

## Next session: `1a`

Repo restructure (T1) + patch/realm/season tracking (T2) + crosswalk (T3). It now starts from a
**confirmed** crosswalk rather than an open question, and `RECON_FINDINGS.md` names the primary key.

**Read first:** `RECON_FINDINGS.md` Task 5 (the join), then `PHASE_1_spell_database.md`.

⚠ **Carry into Phase 1 planning:** the numeric-field extractor (98% of 803 spells) is the single
highest-value item found in Phase 0 and is currently *not* a named Phase 1 task. It belongs in T4's
scope or immediately after it.
