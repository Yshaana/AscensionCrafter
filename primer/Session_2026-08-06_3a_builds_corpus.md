# Session `3a` — the builds corpus, pooled inference, gear, and the calibration gate

**2026-08-06, overnight autonomous run.** Phase 3 Tasks 1, 2, 3, 4, 8 plus the
inherited ≥3-character calibration gate and one owner-decided seed.

Owner answered four questions before bed; everything below follows from those.

| Question | Owner decision |
|---|---|
| Run the uncapped historical backfill tonight? | **Yes, Claude starts it** |
| Gear data source for T4 | **Client DBC first** (Item.dbc / ItemStat.dbc) |
| Holy Shock SP coefficient | **Seed measured ~0.40, flagged provisional** |
| Widen the crawl (re-crawl known chars + all roles)? | **Widen both** |

---

## Headline: the calibration gate is NOT MET, and the miss has a shape

`tools/audit/calibrate_crawled.py` is new and implements PHASE_2 §8.2's
inherited criterion — *the sim reproduces ≥3 real characters within ±20%
aggregate DPS*, tolerance unchanged from `predictions/CALIBRATION_TOLERANCE.md`.

**Result: 0 of 41 level-60 crawled characters within ±20%, at the STRICT
lag-0 setting.** Report: `data/derived/calibration_crawled.md`.

> ⚠ **This supersedes a mid-session figure of "2 of 25 at a stated 336h
> staleness".** The uncapped backfill finished after the first write-up (50 new
> reports, 275 armory records, 390 characters known), the corpus roughly
> doubled, and the gate was re-run. See "the corpus size caveat" below — the
> correction is in the project's favour and the numbers below are the ones to
> quote.

🚨 **The misses are one-directional: 40 of 41 deltas are negative**, ranging
−35% to −92%. A scatter would mean noise; a one-sided distribution of that size
is a missing multiplicative layer, and it is the same signature that has caught
every previous modelling gap in this project. The larger corpus also shifted
the candidate set onto **real Zul'Gurub raid bosses** (Hakkar, Bloodlord
Mandokir, Taerar, Snowgrave) rather than dungeon trash-adjacent kills — i.e.
onto exactly the content where buff stacks are largest, and that is where the
biggest misses sit. Two candidate mechanisms, both already known and neither
fitted here:

1. **Buffs are not modelled for anyone but the owner.** `core/sim/buffs.py`
   (2e) is measured for *his* buff set. Every crawled parse is a real group in
   a real dungeon carrying buffs the sim gives them none of. 2e measured the
   owner's own buffed/unbuffed gap at **1,555 → 3,650 DPS, a factor of 2.35** —
   which is the right order to explain a −55% median.
2. **Talents are modelled only where cards resolve, and the crawl's cards are
   every class's kit**, not the Paladin kit the talent layer was built against.

⚠ **Do not close this by fitting a constant.** That is 2c's demoted 1.31 and
2e's deliberately-unseeded Holy residual, one level up. The correct next step
is to model the buff layer for a crawled character (their group is in the same
report — the buff set is *derivable*, not assumed), then re-run the gate.

Two structural findings fell out of building the gate, both worth keeping:

* 🚨 **The corpus-size caveat, and it is a method lesson worth more than the
  gate number.** Against the mid-backfill corpus, the strict `--max-lag-hours 0`
  filter left **exactly one** level-60 character, and I wrote that up as a
  structural property of the data ("exact-join captures skew toward levelling
  players") and loosened the threshold to 336h to get an n at all. **That was
  wrong — it was small-sample, not structure.** After the backfill completed,
  the *same* strict filter yields **41**. Generalised, and now in the tool's own
  docstring: **a filter that starves on a partial corpus is not evidence that
  the filter is too strict.** Re-run on more data before loosening a constraint.
  The gate now runs at its strictest setting with no staleness caveat at all,
  which makes its verdict stronger than the one it replaced.
* **Level must be read, not assumed.** A first version hardcoded level 60 and
  simmed a level-49 character's parse against level-60 magnitudes — the same
  error `1x` retracted when pooled crawl data was used to "rule out" a
  level-scaled flat. `characters.level` now gates the candidate set.

---

## T1 — the corpus (`data/derived/builds.db`)

`core/builds/corpus.py` (pure logic) + `ingest/logs_gg/build_builds_db.py`
(reads the gzipped NDJSON). Gitignored, same rule as every other derived db.

After the backfill completed: **4,069 characters, 412 build snapshots, 19,684
cards, 6,896 gear rows, 5,455 encounters, 19,649 performance rows, 307,442
ability rows, 877,850 avoidance rows, 807 leaderboard entries.**

⚠ **Correction (post-3a audit, 2026-08-06): these figures are NOT
committed-reproducible.** The original text here said "rebuilt from committed
source"; that is true only for tier-1. Ability/avoidance/performance rows come
from TIER-2 crawl files, which are gitignored by design — a clean rebuild from
the committed NDJSON alone yields **390 characters and 0
ability/avoidance/performance rows** (`characters_known: 390` in the capture
manifest). Reproducing the full corpus needs the local tier-2 files or a
per-report re-fetch (`crawl_ascensionlogs.py --recrawl-report <id>`). The
committed per-report `tier2_manifest.json` in each crawl day folder
(`tools/scrapers/build_tier2_manifest.py`) makes the tier-2 inputs auditable —
row counts and checksums per report — without a re-fetch.

**Five deviations from PHASE_3 T1's draft DDL, each recorded not drifted:**

1. 🚨 **`capture_scopes` exists and performance keys on `scope_id`, not
   `encounter_id`.** The per-ability endpoints aggregate over whatever
   `encounterIds` the crawler passed and the rows carry no encounter id, so an
   ability row's true granularity is the SCOPE. `boss_single` scopes cover one
   encounter and set `encounter_id`; grind `boss_group:*` and `trash_bundle`
   scopes cover many and leave it NULL. Collapsing scopes onto encounters would
   fabricate per-encounter precision the source never had.
2. **Avoidance lives in its own table, keyed by the ENEMY.** The endpoint has no
   attacker id, so `ability_performance`'s miss/dodge/parry columns exist (per
   the phase doc) and stay NULL for crawled data; inference joins
   `ability_avoidance` per spell instead.
3. **No `patch_id`/`phase_id` columns.** Those ids are rebuild-scoped
   autoincrements in ascension.db — the same reason `open_questions` moved to
   slugs. `patch_date`/`occurred_at` are stored and resolved at query time.
4. **`gear_stats_json`, not `stats_json`.** The crawl's `stats_summary` is
   GEAR-ONLY (`_gearOnly`; a level-60 character shows Strength 13 — session
   `1x`). Naming it `stats_json` invites reading it as a character sheet.
5. **Snapshots carry `capture_report_id`/`capture_encounter_id`**, so the
   build-to-parse join can be EXACT (lag 0) where the capture was taken at that
   encounter, with nearest-in-time as the labelled fallback.

Spell-ID resolution runs at rebuild time through the crosswalk, never at
capture time: **3,222 of 3,245 distinct (entry_id, rank) pairs resolve, 23
ambiguous and left NULL** — never tie-broken.

✅ **The corpus reproduces a known result on first build**: Hammer from the
Heavens, **17,781 pooled hits — 0 miss, 0 dodge, 0 parry**, matching
`confirmed_facts.hammer_from_heavens_cannot_be_avoided` (4,962 hits at the
time) on 3.6× the sample.

---

## T2 — pooled inference (`core/builds/inference.py`)

Staging only: findings land in `inference_findings` and **nothing auto-seeds
`spell_mechanics`**. Runner: `tools/analysis/pooled_inference.py`, report
`data/derived/inference_report.md`. Top-50 most-played abilities swept:
**74 proposals, 70 honest refusals.**

🚨 **`infer_crit_table` could not be built the way the phase doc specified, and
the reason is a hard data fact.** The doc says regress each character's crit%
against their melee crit rating and their spell crit rating. Per-parse stats do
not exist (Phase 0), armory stats are gear-only — and **hit and crit rating are
unified in GEAR** (2d), so a regression against gear rating cannot separate the
two tables even in principle. Replaced with a **within-character anchor
comparison**: the target ability's crit% is compared against the same
character's crit% on doc-confirmed anchors in the same parse (melee: Auto
Attack; spell: the confirmed `crit_table='spell'` ids expanded through the
crosswalk). Buff state, gear and target-level suppression all cancel inside the
pair — the same property that makes the weapon-free pair ratios durable.

⚠ **The first version had a two-bucket bug worth recording**: with only
`melee`/`spell` votes, five *periodic* abilities (four Consecration ranks and
Blood Presence) were proposed as `melee` — because a ~0% crit rate is closer to
the melee anchor than to the spell one. A cannot-crit ability is not a
melee-table ability. A third bucket now fires first: near-zero crit while BOTH
anchors crit normally proposes `none`, which is the correct verdict and matches
the primer's aura-tick rule.

🚨 **`infer_coefficient` REFUSES, per spell, and is recorded refusing.** The
regression needs stats at the parse; the snapshot lags it and path grants (PoI's
×2.0, Duality's cycling) move the true stat by more than the effect being
fitted. It unlocks when per-parse stats exist — Phase 3 T5's self-snapshot.

**A finding the sweep produced for free:** the immunity/roll split. Several
Holy abilities have enemy units that full-resisted **every** pulse while
landing zero — 8 such targets for Hammer from the Heavens, 6 for Fel Infused
Attack. That is an immunity, not a resist roll, and pooling the two would
manufacture a phantom partial-resist rate on abilities the primer already calls
unresistable. They are reported separately and excluded from the rate.

---

## T3 — search and analysis (`core/builds/search.py`)

`find_builds`, `co_occurrence`, `ability_performance_percentiles`,
`meta_snapshot`, `outliers`, `path_performance`, `item_usage`,
`role_distribution`. Cards match on spell id or raw entry_id, **never by name**.

Two immediately useful readings:

* **`path_performance`, 4,033 parses**: intellect 518 avg / 5,161 max ·
  agility 414 / 3,477 · strength 413 / 3,062 · duality 381 / 3,454 ·
  spirit 125 / 1,253. Duality sitting last is consistent with the 2d bug
  advisory, though these are averages across mixed content and not a controlled
  comparison.
* **`co_occurrence` on Hammerdin** recovers the build's own shape from other
  players' boards with no input from our docs: Fanaticism, The Art of War,
  Exorcist's Slash, Crusader Strike, One With The Light, Seals of the Pure,
  Sanctity of Battle, Divine Storm — lift 17–44×. This is the market-basket
  discovery path working.

---

## T4 — gear, and the owner's chosen route turned out to be a dead end

🚨 **The client DBC does not carry item stat values. Probed and disproved, not
assumed.**

* `Item.dbc` — 563,308 records, 8 fields: stock 3.3.5 display data
  (class/subclass/display id/inventory type). No stats. Expected in hindsight:
  in 3.3.5 item stats live server-side in `item_template`.
* `ItemStat.dbc` — 1,513,931 records, 39 fields, a custom Ascension table.
  Tested against **1,198 items whose real stats the crawl already resolves**:
  reading fields 3–22 as `(ITEM_MOD type, value)` pairs reproduces the true
  block exactly **6 times out of 567 overlaps**, and no single field equals a
  real stat value above chance (best 9.2%). Decodable content is
  display/gating-shaped (f37 a 1–70 required level, f36 an 8000/12000
  delay-like constant, f23–f26 floats). Layout otherwise unresolved — recorded
  as an open question, **not guessed at**.

So `items` is built from `snapshot_gear` — Path B's own fallback, which the
recon itself called "an item database assembled as a byproduct". **2,384 items,
1,792 with resolved stat blocks** after the backfill.

⚠ **Provenance matters here and is stamped in the table**: those stat blocks
are **BisBeard's resolution** carried through the armory capture
(`provenance='crawl_resolved_bisbeard'`). Cross-validating our weights against
BisBeard is therefore a check on the **weights**, not an independent check on
the **items**. Anyone reading agreement as confirmation should read this line
first.

`gear_tier_stats()` returns fresh/mid/BiS blocks measured from real characters
at percentiles of gear stat budget. ⚠ It deliberately does **not** rank on
`item_level` — that column is NULL on most crawled rows, so an ilvl ranking
sorts by *how much metadata resolved* rather than by gear quality, and the
first version returned **empty** fresh and mid blocks, which is what caught it.

`export_stat_weights()` emits `key=value` and JSON. It does **not** invent a
`weightString` grammar — BisBeard exposes the name but not the encoding, and
Phase 0 stopped short of probing for it. `rank_items()` is a cross-validation
report, and its docstring states plainly that **weapon damage is not in
`stats_json`**, so a weapon ranking from it is a stat-stick ranking only.

**No `optimize_gearset()` was built**, per the Phase 0 T9 verdict.

---

## T8 — crawler refinement

* **All roles was already done** — `ROLES = [dps, tank, support]` has been
  walked since 0b (`tanks-and-dps` is a union of two already taken). Reported
  rather than claimed as new work.
* **Re-verification is the real gap and is now closed.** Discovery is
  incremental, so a character who respecs and stops parsing stays frozen at
  their old build forever. Each run now additionally re-pulls up to
  `REVERIFY_PER_RUN = 40` known-but-not-seen-today characters, **oldest capture
  first**, so the sweep rolls through the whole population. Content-hash dedupe
  already makes an unchanged build cost one request and write nothing, so the
  cost is ~40 requests/day, not a second crawl. `--reverify 0` disables.

---

## The Holy Shock seed (owner decision)

**Seeded 0.40 as provisional**, on the damage sub-spell **25902** (the trigger
TARGET, per the 2026-08-05 attribution rule — the pressed card is a dummy),
under its own source string `ascension_measured_provisional` in
`seed_hand_coefficients.py`. That script now owns two source partitions and
scopes its delete per source.

Evidence, unchanged from 2d/2c: ≈0.40 measured at n=40 unbuffed non-crits
against HftH in the same log (weapon-free same-school pair, so the then-current
Duality AP cycling cancels); 2c's discriminator independently falsifies "no SP
term" (26–34% above group in all four logs) and shows the client's 0.429 runs
~5% high (3–9% below group in all four).

🛑 **The open question stays live at `in_progress`, deliberately.** 0.40 is
back-solved from the owner's parses and must never become a fit target for
those same parses. What closes it: any source that *states* a coefficient.

---

## Housekeeping

* `py cli/rebuild.py` — green, 20 steps. `check_core_purity` 0/45.
  `check_sim_engine` all pass (the optimal-vs-observed margin is unchanged at
  25 points; the harness reports totals, not DPS).
* Backfill (`crawl_ascensionlogs.py`, uncapped) ran for **94 minutes, 6,146
  requests, 0 retries**: **50 new reports, 275 armory records, 390 characters
  known**, 3.6 MB tier-1 committed / 28.6 MB tier-2 local. It committed and
  pushed `data/source` itself. Every figure in this document is post-backfill.
* New derived artifacts, all gitignored: `builds.db`, `inference_report.md`,
  `calibration_crawled.md` / `.json`.
