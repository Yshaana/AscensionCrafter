# PROGRESS

**Claude Code maintains this file. Update it at the end of every session, before writing the handoff.**

This is the pointer that lets a new session start with no memory of the last one. Keep it short —
detail belongs in `Session_*.md` handoffs, not here.

---

## Current position

**Next session: `2c` — talent modelling, calibration (T8), prediction ledger (T9),
cache (T10), diff/report (T11). Read `PHASE_2_simulation.md`.**

**✅ SESSION `2b` IS DONE (2026-08-05).** T5 (three tiers + APL grammar + apl_gen),
T6 (uncertainty from a sim-layer policy table), T7 cheap half (stat weights, path
comparison). The sim produces its first end-to-end number. Session record:
`primer/Session_2026-08-05_2b_sim_tiers.md`. Validation: `check_sim_engine.py` is
**30 checks** (was 16), all pass; purity 0/34; 19-step rebuild green.

**What `2c` inherits from `2b`:**

- 🛑 **FIRST ITEM: open question `rank_siblings_inherit_no_hidden_refs`.** It
  blocks the rotation question. A rank sibling inherits no `hidden_refs` (that
  column is parsed from the export, which siblings are by definition absent
  from), so a sibling whose own record is a DUMMY loses its sub-spell chain.
  **Holy Shock R4 (20930) is exactly that and resolves to 0 damage** — which makes
  `paladin_optimal` (602) score BELOW `paladin_observed` (659), inverting build doc
  §11's central conclusion. The sim names the zero-damage ability loudly and
  `check_sim_engine` asserts that it does, so it cannot be quoted as a result.
- ✅ **The sim is CALIBRATED against a real parse** (Elric's own
  `2026-08-04-20.07.21 WoWCombatLog.txt`, 60,427 events). Outcome recorded in
  `predictions/pred_2026-08-05_elric_paladin.md`, tool
  `tools/audit/calibrate_vs_log.py` (verifies field alignment against three
  doc-confirmed facts and REFUSES to report if they fail). **Within any one log a
  school's abilities agree to ~±0.03 — and since HftH and HoJ's tick are
  structurally unrelated formulas, that agreement validates BOTH base formulas.**
  **Pulse delivery confirmed a second time, independently: 259 HftH hits / 60 HoJ
  ticks = 4.32 against a predicted 4.00.**
- 🛑 **Do NOT fit one talent multiplier from pooled logs.** The absolute
  multiplier swings **1.41× between sessions** (Holy 1.76 / 1.90 / 1.99 / 2.48)
  — that is buff and gear state, not talents. **The durable quantity is the
  Holy÷Holystrike RATIO, 1.31 ± 0.03 across all four logs**, because buff state
  cancels in a ratio. That ratio is what a correct talent model must reproduce.
- ⚠ **Two calibration outliers must be settled BEFORE fitting talents**:
  **Consecration ~4×** (suspect missing component or wrong rank) and **Dawn
  Strike**, which misses its school group in ALL FOUR logs, always ~0.3 low — a
  reproducing per-ability bias meaning its sim base is **~25–30% too high**.
  Suspect effect type 121 (normalized weapon) being counted alongside type 31
  (weapon-percent); if so it affects every ability carrying type 121. Open
  questions `consecration_and_dawn_strike_calibration_outliers` and
  `dawn_strike_sim_base_is_systematically_too_high`.
- 🚨 **Talent modelling is now the single largest error source**, ahead of
  everything else combined. **Owner decision 2026-08-05: general extractor for
  coverage + hand-seed the ~24 slotted talents.** A correct model should
  *reproduce* ~1.76 and ~1.40 from the actual cards — those are targets, not
  values to hardcode. Build the extractor on
  **auras 107/108 (`ADD_FLAT_MODIFIER`/`ADD_PCT_MODIFIER`) read together with
  `EffectMiscValue` (the SpellModOp) and `EffectSpellClassMask`, from NUMERIC
  fields** — 2b showed Improved Cleave's tooltip understates its own scope
  (it names the flat; the op is `SPELLMOD_ALL_EFFECTS`), so tooltip parsing is
  the wrong foundation.
- 📅 **Owner decision 2026-08-05: re-run the Phase 1 baseline capture on
  2026-08-07**, before the 2026-08-08 phase flip, to tighten the "before" edge.
  Overwrites `data/source/crawl/baseline_phase1/` in place. The sim reads ~600 DPS against the owner's reported
  ~3,600 — pre-registered with its causes ranked in
  `predictions/pred_2026-08-05_elric_paladin.md`.
- ⚠ **Do NOT adopt the sim's stat weights.** They disagree sharply with the build
  doc's empirical ones (sim: weapon_damage 25, hit 17, crit 6.1; doc: crit 2.00
  best, AP 1.00). The disagreement is a diagnostic, not a result.
- Remaining named gaps: seals scored per cast not per swing; auto-attacks
  unmodelled; `Judgement` resolves to no current-pool card; Righteous Vengeance's
  30% crit DoT unmodelled.
- `sensitivity()` output is ready to populate `open_questions.variance_contribution`.

**✅ SESSION `2a` IS DONE (2026-08-05).** T1–T4: `core/sim/combat_engine.py` (gt-table
rating conversions, anchor-validated; attack tables; no silent defaults),
`core/sim/content.py` (8 presets, raid durations derived from scouted ZG data),
`core/sim/ability_model.py` (resolver-path-only `ResolvedAbility`, full term_type
vocabulary, outliers excluded), `core/builds/spec.py`+`stats.py` (BuildSpec ranks-
mandatory; compute_stats sheet/component modes, Duality parameterised at measured
values). Validation: `py tools/audit/check_sim_engine.py` (16 checks incl. the
mean(roll_hit×100k)≈expected_hit guard). Session record:
`primer/Session_2026-08-05_2a_sim_foundation.md`.

**What `2b` inherits from `2a`:**

- 🚨 **First item: finish `trigger_attributed_coefficients_not_in_spell_scaling`**
  (in_progress). The attribution DECISION is made (owner, 2026-08-05): coefficients
  live on the trigger TARGET — `seed_hand_coefficients.py` (new 19th rebuild step)
  seeds HftH's 9.1% SP/AP on 282987 with tier-3 provenance. **What 2b implements:**
  the ability model pulls `spell_scaling` rows per component `source_spell_id`
  (bounded, single-path, confidence=inferred when trigger-reached — 1b's walk
  rules). Until that lands the rows are queryable but a card's profile still
  serves flat-only (~45% understatement on HftH stands).
- **Trigger-hop magnitudes ARE summed into expected_hit** (flagged
  `calibration_anchor=False`, listed in `triggered_components`) — see the 2a plan-
  changes row for why the "never anchor" rule does not mean "exclude".
- `expected_hit` is per-EVENT (hit or tick): direct-vs-DoT splitting, CP
  parameterisation, hybrid-school mitigation split, AoE totals-at-N are all
  deliberate 2a gaps with warnings — T5's tiers own them.
- New open question `melee_crit_suppression_vs_higher_level` — the engine warns
  instead of modelling it; a big white-swing parse settles it.

**✅ SESSION `1c` IS DONE (2026-08-05). PHASE 1 IS COMPLETE — all exit criteria checked
and recorded in `PHASE_1_spell_database.md`.** Session record:
`primer/Session_2026-08-05_1c_epistemics_tooling.md`.

**What `2a` inherits from `1c`:**

- **`py cli/rebuild.py` is now 18 steps** (~90s): `seed_epistemics.py` (T6) runs after
  `seed_confirmed.py`, and `tools/audit/audit_gaps.py` (T8) runs LAST, writing
  `data/derived/audit_report.md` + a one-line summary every rebuild.
- **T6 epistemics live**: `open_questions` (28 rows: 23 open / 1 in-progress / 4
  resolved-as-history, keyed by stable `slug`), `retractions` (24), `fact_spell_links`
  (410: 64 inferred id-based, 346 needs_review name-based — never auto-approved).
  `confirmed_facts` carries provenance columns (evidence_ref/realm/season stamped;
  verified_at_patch NULL for pre-tracking backfill). **Both seed files are append-only
  source of truth — resolving a question means editing `seed_epistemics.py`.**
- **T7 `spell_profile()`** (`core/spells/profile.py`, `cli/profile.py`): rank gaps and
  conflicts surfaced first; duplicate names refuse with a candidate list; out-of-catalog
  ids fall back to `dbc_only` (282987 profiles); `mode='fast'` for sim loops — **this is
  the resolver 2a's ability model should call, not raw tables.**
- **T8 auto-debugger** (12 sweeps incl. the 2026-08-08 phase boundary, which fires in
  3 days) + **test-protocol generator** (7 hand-written protocols; card-destruction
  protocols are REFUSED structurally; <3-point discriminators emit "find another test").
- **T9**: `search_spells(conn, **filters)` + `py cli/browse.py` (Datasette, 12 canned
  queries; datasette now pinned in requirements.txt). **T10**: `volatility_score()` —
  Darkmoon-only strict (owner decision 2026-08-05), report-only, carries a `data_thin`
  honesty block (12-day tagged window today).
- **The compound-form extraction gap is CLOSED**: `spell_scaling` 1,058 → 1,348 rows
  (625 → 737 spells), new term types (`SPFR`/`SPH`/…/`BH`; BH routes to the healing
  block). ⚠ 2a note: `spell_scaling.term_type` is no longer only SP/AP/RAP/WEAPON.
- **Amplifier queue pre-classified, owner-approval gated** (`reviews/amplifier_review.md`,
  243 rows: 58 verbatim / 12 check-stat / 16 school / 105 proposed-exclude / 52
  unclassified). Nothing enters the graph until the owner approves a batch there.
- **New open question**: `hidden_formula_outlier_coefficients` — 4 cached
  `dbc_hidden_formula` coefficients look like swallowed multipliers (277595 RAP/SP 6.0);
  the widened extractor fixes them at the next `--with-dbc` re-extraction.
- 1c deviations from the phase doc are in `PHASE_1_spell_database.md`'s progress block.

**✅ SESSION `1x` IS DONE (2026-08-04).** 794 of 887 blocked hidden-formula spells
resolved from numeric DBC fields; the rank question settled. Session record:
`primer/Session_2026-08-04_1x_numeric_extractor.md`. Its two corrections
(`EffectBonusCoefficient` is not the SP/AP coefficient; coefficients DO scale with
rank) are now **enforced in code** — `1b` built T4/T5 on them, and both are
rebuild-time validations. The `sourcesByStat` check it also carried was closed in `1x`
itself (premise wrong — the block is gear-only).

**✅ SESSION `1a` IS DONE (2026-08-04).** Repo restructured to ARCHITECTURE §4, patch/realm/season
tracking built, ID crosswalk built. Session record:
`primer/Session_2026-08-04_1a_restructure_crosswalk.md`.

### 🔁 Daily capture — now AUTOMATED (2026-08-04)

**Nothing to remember. The daily crawl runs itself at logon**, 5 minutes in, at most once a day.
Task: `AscensionCrafter Daily Crawl`; script:
`tools/scheduling/register_daily_crawler.ps1`; full documentation: **`SCHEDULING.md`**.
Double-clicking `run_crawler.bat` still works and deliberately bypasses the once-a-day guard.

**🛑 `catchup_crawler.bat` is deliberately NOT scheduled and must stay that way.** It is uncapped,
runs for hours against a third-party public API, and automating it risks getting the IP blocked.
Manual action, started before bed, no deadline — reports persist on ascensionlogs after a phase flip.

**Separately, `catchup_crawler.bat`** is the uncapped historical backfill — run it when the machine
can stay on for hours (overnight). Grind reports take ~10 min each, so a full backfill is long.
Ctrl+C is safe in both: `scan_log.json` is saved after every report and the next run resumes.
Not urgent — reports persist on the site, so the backfill has no deadline.

### ✅ Phase 1 baseline — CAPTURED 2026-08-04, deadline met

48 characters (full gear + build + resolved stats), 12 leaderboards, 3 phase records, 0 errors, in
`data/source/crawl/baseline_phase1/` (0.70 MB, all tier 1, committed). 50 were requested; 2 of the
top-50 have no armory capture on the site (404 — not an error).

**Correction to the earlier framing of this deadline:** reports *persist* after a phase flip, so
historical parse data is **not** lost on the 8th and the report backfill is not deadline-bound. What
was genuinely unrecoverable is the **leaderboard standings and character armory snapshots as they
stand during Phase 1** — and that is now captured. Nothing else in Phase 0 is deadline-bound.

Optionally re-run closer to the 8th for a tighter "before" edge; the folder is overwritten in place.

---

## Session log

| Session | Scope | Status | Handoff | Notes |
|---|---|---|---|---|
| **0b** | Crawler + changelog fetcher (T6) | ✅ done | `Session_2026-08-04_0b_crawler.md` | Shipped 2026-08-04. Changelog backfilled (353 pages, back to 2016). Baseline captured |
| **0a** | Recon T1–5, 7, 8, 9 | ✅ done | `Session_2026-08-04_0a_recon.md` | **Phase 0 complete.** `RECON_FINDINGS.md` written. Crosswalk resolved; class coverage 13%→58%; rank resolution solved; 2 pipeline bugs fixed |
| **1a** | Restructure, patches/realms/seasons, crosswalk | ✅ done | `Session_2026-08-04_1a_restructure_crosswalk.md` | `core/api/cli` split + purity check; `cli/rebuild.py`; 5 patch tables; `spell_id_crosswalk` (4 ID spaces); class coverage 394→1,794. Crawler scheduling automated in the same session |
| **1x** | Numeric-field DBC extractor (+ settle rank-vs-coefficient) | ✅ done | `Session_2026-08-04_1x_numeric_extractor.md` | 794/887 blocked spells resolved; `spell_effect_values` + `dbc_numeric.py` + `rank_scaling.py`. **Two Phase 0 claims corrected** — `EffectBonusCoefficient` is not the SP/AP coefficient, and coefficients DO scale with rank |
| **1b** | `spell_mechanics` (T4) + relationship graph (T5) | ✅ done | `Session_2026-08-05_1b_mechanics_relationships.md` | 3,747 mechanics rows, 5,302 edges, bounded trigger attribution (724 rows / 444 cards, HftH 122–145 reproduces end-to-end), `spell_scaling` rank-keyed (+229 sibling rows), `spells` combat-table columns → `doc_confirmed_mechanics`. Rebuild is 16 steps; piped-output crash fixed. Two stale `confirmed_facts` rows qualified SUPERSEDED (pre-`1b` prep item) |
| **1c** | Facts, `spell_profile()`, auto-debugger, browsing, volatility | ✅ done | `Session_2026-08-05_1c_epistemics_tooling.md` | **Phase 1 complete, exit criteria checked.** T6–T10 + compound-form gap closed (+290 scaling rows) + amplifier queue pre-classified (approval-gated per owner decision) + conflict sweep buckets slot collisions separately. Two more owner decisions implemented: Darkmoon-only volatility, Datasette pinned. Rebuild is 18 steps |
| **2a** | Combat engine, content profiles, ability model, build spec | ✅ done | `Session_2026-08-05_2a_sim_foundation.md` | T1–T4 + `check_sim_engine.py` (16 checks). Found the HftH coefficient queryability gap; 2 open questions filed |
| **2b** | Three sim tiers, uncertainty, stat weights | ✅ done | `Session_2026-08-05_2b_sim_tiers.md` | T5+T6+T7-cheap-half. **4 data bugs found, all silently zeroing**: trigger coefficients unserved, rank siblings had NO magnitudes (686 cards), weapon-percent read as flat, fast_sim allocation order. 🚨 Structural finding: trigger-reached damage can be delivered by a periodic-trigger aura (HoJ fires HftH 20x/cast, validated 3.81 vs predicted 4.00 over 20,823 pooled hits). 🔴 Improved Cleave reverted to bottom of the chase list |
| 2c | Talent modelling, calibration, prediction ledger, cache, diff/report | ⬜ | — | ▶ **NEXT.** Start with `rank_siblings_inherit_no_hidden_refs` — it blocks the rotation question. ⚠ The 2026-08-08 phase boundary lands in 3 days; the audit's phase-boundary sweep starts firing then |
| 3a | Crawl normalisation, inference, search, gear | ⬜ | — | Gear scope gated on 0a Task 9 |
| 3b | Addon, logs, automation, crawler refinement | ⬜ | — | |
| 4 | Legos + Theorycrafter | ⬜ | — | Chunk as it goes |

Status values: ⬜ not started · 🟡 in progress · ✅ done · ⏸️ blocked

---

## Blocked on the user

Anything waiting on a 🛑 stop-point or a decision only the project owner can make. Clear entries as
they're answered.

| Item | Blocking | Asked on |
|---|---|---|
| *(nothing currently open)* | — | — |

**🎉 Both long-standing 3b blockers were resolved on 2026-08-04 — Phase 3 is no longer gated on the
owner for anything.**

**✅ `ReloadUI()` works** — confirmed in-game by the owner. Not sandboxed, so an addon can force a
SavedVariables flush on demand instead of waiting for logout. Makes mid-session self-snapshot capture
practical and removes the main design risk in Phase 3 T5. Seeded as
`confirmed_facts.client_reloadui_available`. Still unestablished (and not needed for the intended
out-of-combat flow): whether it's callable *in combat*.

**✅ Combat log naming, location — and the correlation rule** — owner supplied the path; verified
against 3 real logs. `<launcher>\resources\ascension-live\Logs`, filename
`YYYY-MM-DD-HH.MM.SS WoWCombatLog.txt`. **Not** retail's pattern, exactly as T6 feared — a
retail-derived glob matches nothing. Bonus: correlation is solved too. Filename timestamp = window
**start**, file mtime = window **end**, both verified exact to the second against the first/last
in-file events, so a log is placeable in time without opening it. Seeded as
`confirmed_facts.combat_log_naming_and_correlation`; full detail and three traps in `PHASE_3` T6.
⚠ Chief traps: in-file timestamps carry **no year** (filename is the only source), and everything is
**local** time while the crawler stamps **UTC**.

**Note:** `SEASON = 10` is also hardcoded in the crawler. It must be bumped when S11 starts — the
API exposes phases, not seasons, so this can't be derived. Not blocking; flagged so it isn't missed.

**Resolved:** crawler scheduling → **manual-first on Windows** (2026-08-04). No scheduler set up
initially; Windows Task Scheduler added later once the crawler is proven. `0b` is no longer blocked.

**Resolved 2026-08-04 (owner decisions, session 0b) — do not re-litigate these:**

| Question | Decision |
|---|---|
| Tier-2 bulk data is local-only on one disk — acceptable? | **Yes, accepted.** Re-fetchable by report id while ascensionlogs retains history, and the committed manifest records what existed. No off-machine sync |
| Capture Dawnrise as well as Darkmoon? | **Darkmoon only.** `REALM` stays hardcoded. Cross-realm facts are unsafe to mix anyway |
| Watchlist for own characters? | **Yes — implemented.** `tools/scrapers/watchlist.txt`, seeded with **Elric** (resolves to character_id 39772). Watched characters are captured every run with priority over `--max-armory` |
| Contact db.ascension.gg's operator / BisBeard's author? | **No outreach for now.** Stay inside robots.txt (targeted manual lookups only) and inspect BisBeard read-only in 0a Task 9 |

⚠ **`SEASON = 10` is hardcoded** in the crawler and cannot be derived (the API exposes phases, not
seasons). Bump it when S11 starts, or every record will be mis-stamped.

---

## Plan changes

When recon or implementation contradicts a phase doc, record it here **and** amend the doc itself.

| Date | What changed | Why |
|---|---|---|
| 2026-08-05 (2b) | 🚨 **Trigger-reached damage can be DELIVERED by a periodic-trigger aura — a trigger-attributed magnitude is not "once per cast"** | Hour of Judgement effect 1 is `SPELL_AURA_PERIODIC_TRIGGER_SPELL` at a 500 ms period over a 10 s duration, so one cast fires Hammer from the Heavens **20 times**, alongside 5 ticks of its own 81. The pulse spell itself is NOT periodic — the DELIVERY is, so periodicity must be read off the triggering effect slot, never the triggered spell. Validated with no fitting: predicted ratio exactly 4.00, pooled crawl gives **16,491 HftH hits / 4,332 HoJ hits = 3.81** across 170 character-report groups. Confirms the ratio and hence the structure; does NOT confirm the absolute 20 (invariant to duration) or any magnitude (crawl records no level). 48 component rows across **34 cards** are affected; counts above 100 are refused, not clamped |
| 2026-08-05 (2b) | 🚨 **Rank siblings had NO magnitudes at all — 686 cards silently simmed as 0** | The resolver correctly redirects a level-60 query to the rank the character casts, but `resolve_numeric_formulas.py` only ever decoded CATALOG ids, so the redirect landed on a spell with zero `spell_effect_values` rows: it traded a WRONG magnitude for NO magnitude. All 686 were in `spell_dbc_raw` and decodable the whole time. Now 676 covered (+1,193 rows), 25 ambiguous lines skipped rather than tie-broken. Lightbound Cleave, Dawn Strike, Holy Finish and Consecration all went 0 → real |
| 2026-08-05 (2b) | ⚠ **`EFFECT_WEAPON_PCT` was emitted as a FLAT damage term** | The stored value is a PERCENT: Lightbound Cleave gained 65 flat damage instead of 65% of a ~627 swing. A units error that shrinks with gear, so it presents as a scaling problem rather than a units problem. Now becomes a `WEAPON` coefficient of pct/100 |
| 2026-08-05 (2b) | ⚠ **`fast_sim` allocation order is not priority order** | A no-cooldown ability first in the priority list consumed the entire GCD budget and starved every cooldown behind it — reporting a one-button rotation and **every stat weight as 0.00**. Cooldown abilities are rate-limited and must be allocated first; off-GCD entries ride along free |
| 2026-08-05 (2b) | 🆕 **Amplifier talents must be read from auras 107/108 + SpellModOp, not from tooltip prose — and this is the foundation 2c's talent modelling should use** | Improved Cleave is `EffectAura 108` (`SPELL_AURA_ADD_PCT_MODIFIER`) with `EffectMiscValue = 8` = **`SPELLMOD_ALL_EFFECTS`**, so its +120% multiplies EVERY effect of the spells in its class mask. Its tooltip says *"increases the bonus damage done by your Cleave ability"*, naming one term — **the tooltip understates its own scope**. For Lightbound Cleave that is ~470 → ~1,033 per hit, not the +74 a flat-only reading gives. The project's "never read a magnitude from tooltip prose" rule extends to **scope**, and numeric-field modifier ops are the general mechanism for talent multipliers |
| 2026-08-05 (2b) | ❌ **RETRACTED, same session, mine: "Improved Cleave is low-value because the flat is small" — it stays a TOP chase** | Having correctly retracted v9's `9 + AP × 1.0` *mechanism*, I carried the demolition straight through to the *conclusion* without re-deriving it, and treated the tooltip as authoritative about which effects the modifier touches. The owner flagged it immediately against direct in-game experience and the numeric field settled it against me (row above). **Lesson: retracting a mechanism does not retract the conclusion it supported** — v9 was right about the card for a reason it never stated. v9's formula stays retracted; there is still no AP term on Lightbound Cleave, which is excellent because it multiplies a large *weapon-damage* component |
| 2026-08-05 (2b) | 🔴 **RETRACTED: v9's Improved Cleave FORMULA (`9 + AP × 1.0`) — the card's ranking is unaffected** | v9 moved it from last to #2b on the reading that Lightbound Cleave's bonus term is `9 + AP x 1.0`. Two compounding errors, each already covered by a hard rule: 9 is the **Rank-1** value (a level-60 character casts Rank 5, where it is **62**), and `EffectBonusCoefficient = 1.0` is stock `EffectBonusMultiplier`'s neutral default, not an AP coefficient — retracted catalog-wide in `1x`. LC R5 is 65% weapon damage + flat 62; Improved Cleave 3/3 is worth **+74 per hit, not +712** (~9.6x overestimate). §10a's x1.48 ceiling loses its x1.110 factor. v9's "independent corroboration" applied the same formula to the same premises |
| 2026-08-05 (2b) | ⚠ **T6 cannot source its ranges from `spell_mechanics.uncertainty_json`; owner decision — build them in the sim layer** | Measured across all 3,747 rows: `damage_formula_terms_json` is stored `low: None, high: None, basis: non-numeric`, and every numeric field carries a `default_confidence_mapping(confirmed, ±0%)` band explicitly labelled "heuristic, not measured". Sampling that reports ±0% knowledge uncertainty — worse than none, because it looks authoritative. Bands now live in `core/sim/uncertainty.py`'s POLICY table as a stated, arguable assumption; Phase 1's truth table stays untouched rather than carrying invented ranges behind tier provenance |
| 2026-08-05 (2b) | ⚠ **Combat-table facts now follow the rank redirect; magnitudes do not** | `doc_confirmed_mechanics` is seeded against catalog ids, so Lightbound Cleave's proc-tested `crit_table='spell'` was discarded the moment the resolver redirected to the rank-5 id, falling back to a heuristic guess in place of a measurement. Crit/hit table and avoidance are rank-INVARIANT properties; magnitudes are not, so only the former are carried |
| 2026-08-05 (2b) | ⚠ **The daily patch check missed a build-relevant entry — scan by MECHANIC, not by card name** | 2a reported 2026-08-04 Darkmoon as "PvP-only reductions plus a new talent Authority". It also carried *"Fixed a bug where mechanics that are supposed to trigger from physical abilities would not trigger from the newly introduced physical + magic school abilities (Talents such as Art of War, Vengeance etc.)"* — Holystrike is such a school and is most of this build's damage, and **Vengeance is slotted at 2/3**, so its own Holystrike crits were not feeding an equipped card. The note names no slotted card except in a parenthetical, which is why a name scan missed it |
| 2026-08-05 (2a+) | 🆕 **Owner decision: trigger-reached coefficients live on the trigger TARGET, never the cards** | Closes the decision half of `trigger_attributed_coefficients_not_in_spell_scaling` (now in_progress). New append-only `seed_hand_coefficients.py` owns `spell_scaling` rows with `source='db_ascension_gg'` (rebuild is 19 steps); first rows: 282987 SP/AP 0.091. Rationale: truth stays where it is true, no per-card duplication, and 2b's per-source-spell event model composes on top. Cards-side hand-seeding was explicitly rejected (conflates the pulse event with the card's own hit — 282984 already carries its own SP/AP 0.05) |
| 2026-08-05 (2a) | 🆕 **Trigger-attributed magnitudes ARE summed into `expected_hit`**, flagged `calibration_anchor=False` | The kickoff note's "never let inferred rows anchor calibration" was first over-read as "exclude from computation" — which zeroes 444 cards (Hour of Judgement's entire damage is its trigger chain). Corrected same session: computed + warned + listed in `triggered_components` so calibration can subtract them. The rule constrains *anchoring*, not *computation* |
| 2026-08-05 (2a) | 🚨 **HftH's confirmed 9.1% SP/AP coefficients are NOT queryable** — doc prose + `confirmed_facts` only, no `spell_scaling` rows for 282987 or the cards | Found by 2a's validation: the resolver serves flat 122–145 without the stat terms (~45% understatement at AP 584/SP 533). Filed as open question `trigger_attributed_coefficients_not_in_spell_scaling` rather than rush-seeded — attributing coefficients to cards has per-event/rotation semantics, the same per-case judgment 1b's multi-path decision deferred |
| 2026-08-05 (2a) | ⚠ **Crit suppression vs higher-level targets: warned, not modelled** | No fabricated retail constant (§2 rule 2). The owner's own parse hints it exists (sheet 21.76% vs autos 16.2%, n=37 — too small). Open question `melee_crit_suppression_vs_higher_level`; combat_engine emits a warning whenever a white table is built vs a higher-level target |
| 2026-08-05 (2a) | ⚠ **Talent stat/multiplier modelling deferred to calibration** — component-mode `compute_stats` warns per unmodelled slot | PHASE_2 T4 wants full resolution; without an items table (Phase 3) and per-talent magnitudes, silent partial modelling would fabricate precision. Sheet mode (`stats_override` = FINAL sheet values) is exact today and is the calibration path. The phase doc's T4 section is amended |
| 2026-08-05 (1c) | 🆕 **`open_questions`/`retractions` key on a `slug` column** beyond T6's DDL | Autoincrement ids reset every rebuild — nothing durable can reference them. Both tables owned by `seed_epistemics.py`, append-only, same discipline as `seed_confirmed.py` |
| 2026-08-05 (1c) | ⚠ **A "mark vanished crosswalk targets" auto-fix was built and WITHDRAWN in-session** | Without history, absent-from-extract is indistinguishable from never-in-scope: 7,654 out-of-pool CA rank-slot rows matched the "vanished" predicate. Now report-only in the provenance sweep. The withdrawn version had already polluted notes on one build — a rebuild reset it |
| 2026-08-05 (1c) | ⚠ **The one "cross-source" mechanics conflict is a component collapse, not a source disagreement** | Champion's Spear (291180): weapon_damage_pct 150 (initial hit, own effect) vs 50 (per-second DoT, sub-spell 291181). Both real; one column cannot hold two components. Queued; a T4-schema follow-up (per-component formula terms) would dissolve it |
| 2026-08-05 (1c) | 🆕 **`spell_scaling.term_type` vocabulary widened** (SPFR/SPFI/SPH/SPN/SPA/SPS/BH/SPI/STA + lowercase/compound/prefix forms extract) | The 1b carry-over gap. +290 rows / +112 spells; BH routes to the healing block in `spell_mechanics`. `SP_PAT`/`AP_PAT`/`RAP_PAT` untouched so `rank_scaling`'s validated comparisons don't shift; DBC-side extractor delegates to the shared implementation (effective next `--with-dbc`) |
| 2026-08-05 (1c) | 🆕 **Protocol generator refusal scans actionable fields only** (method/setup/record), not question text | A blanket scan made the reroll-mechanics question un-protocolable — its observational protocol (log fishing outcomes, zero cards at risk) is legitimate. The refusal still raises `CardDestructionRefused` on any instructing text |
| 2026-08-05 (1b) | ⚠ **`spell_scaling` lost its FK to `spells`, deliberately** | The T4 rank migration inserts rows for level-60 rank siblings, and in all 697 wrong-rank cases the sibling id is absent from `spell-export.json` — an FK rejects exactly the rows that fix the wrong-rank problem. Same precedent as `owned_cards` (1a) |
| 2026-08-05 (1b) | 🆕 **Trigger attribution semantics decided (owner, 2026-08-05): bounded walk, flagged** | Depth ≤ 2, cycle-safe, single-path targets only, out-of-catalog targets only, `via='trigger_hopN'`, `confidence='inferred'`, chain in `evidence_ref`. 724 rows / 444 cards; 26 multi-path targets deliberately unattributed. In-catalog targets are never double-attributed — their magnitude is their own row |
| 2026-08-05 (1b) | ⚠ **T5's "migrate and retire" became "migrate and demote"; `exclusivity_buckets` stays a TABLE, not a view** | Staging tables are kept as ingestion inputs (their seeds own them, run earlier in the chain); `spell_relationships` is the one query surface. A view could not round-trip bucket 3 (Holy Focus) — a single-member bucket has no pairwise edge to reconstruct from. Every multi-member bucket is validated as an edge group each rebuild |
| 2026-08-05 (1b) | 🆕 **`spells.crit_table`/`hit_table`/`rolls_hit_check`/`proc_icd_seconds` removed** | T4's "one home per fact": doc-confirmed combat-table values seed `doc_confirmed_mechanics` (reworked `seed_spell_flags.py`) and surface only in `spell_mechanics` |
| 2026-08-05 (1b) | ⚠ **Most `spell_mechanics` conflict rows are multi-effect-slot collisions, not cross-source disagreements** | 29 rows carry `confidence='conflict'`; sampled cases are one spell whose two effect slots have different radii or chain counts feeding a single column (e.g. 276884 radius 8 vs 5). Honest per §2.3, but T8's conflict sweep should bucket them separately from genuine source disagreements or they become noise |
| 2026-08-04 (1x) | ❌ **RETRACTED: "reading a coefficient off the catalog's Rank-1 entry is probably safe."** Coefficients DO scale with rank; **`spell_scaling` needs rank keying** | Phase 0 derived it from **one** line (Holy Supernova, identical at R1 and R6). Measured across all **1,580** multi-rank lines with 2+ DBC members: numeric coefficient constant 696 / **varies 169**; tooltip literals constant 132 / **varies 34**. The shape is retail's low-rank penalty — ramp then plateau, 110 of the 169 — and the catalog stores **Rank 1**, the deepest point of the penalty. Seven catalog entries measurably affected (Sun Down SP 0.4→1.3 = 3.25×; Grasp of Darkness 0.5→1.4 = 2.8×; Spirit Charge changes term type SP→AP). Seven is a **floor**: 547 more state no coefficient in either rank's text. Migration deferred to T4 by owner decision |
| 2026-08-04 (1x) | 🚨 **CORRECTED: `EffectBonusCoefficient` is NOT the SP/AP coefficient** — it is `EffectBonusMultiplier`, default 1.0 | Phase 0's *"311 blocked spells carry a non-zero `EffectBonusCoefficient` (SP/AP scaling)"* counted right and read the field wrong. **7,647 of 9,211** non-zero values are exactly 1.0; the recurring non-defaults are retail's cast-time formula (`0.429 = 1.5/3.5`, `0.714 = 2.5/3.5`); calibrated against 98 spells stating their own `$SP*x`/`$AP*x` it agrees **4 times**. Of the 343 blocked spells with any coefficient, **270 carry only 1.0** → the real surface is **≤73, not 311**. Building the extractor on it would have fabricated SP coefficients across 311 spells *with tier-4 provenance attached*. Ascension keeps applied coefficients in **tooltip text**; the field is stored as `bonus_multiplier` and never emitted as SP/AP |
| 2026-08-04 (1x) | 🚨 **A live tooltip can render an arithmetically impossible range — and solving it pins values no single source states** | Hammer from the Heavens displays *"194 to 147"* in-game (owner screenshot, tier 1). The description hand-rolls level scaling at **two different rates** — `($PL-10)*2.4` on the min, `($PL-10)*1` on the max — while `$m1`/`$M1` render the raw base unscaled. The min's rate matches the effect's real 2.4/level and is **correct**; the max's 1/level is **wrong**, so the min overtakes it above ~level 29. At 60 it should read **194 to 217**. Treating the two numbers as simultaneous equations cancels the unknown stat term and yields **`L = 60` exactly** — the character's level falls out of a tooltip |
| 2026-08-04 (1x) | ❌ **RETRACTED, twice, on Hammer from the Heavens: "double-applies scaling" and "caps at level 40 → flat 74–97"** | Both were mine, both wrong, both caught the same day. A double application would render 242/195 — *above* the observed minimum, impossible. And a `--with-dbc` re-extraction returned **`MaxLevel = 0`** (uncapped). The 48-point gap that motivated the cap is fully explained by the stat term `A = 72`. **The flat is 122–145 at level 60**, and §10's assumed 30/30/40 split becomes **~21/23/57** — right that SP and AP are equal, wrong about how flat-dominated it is |
| 2026-08-04 (1x) | ❌ **RETRACTED: pooled crawl data "ruled out" the higher flat** — it cannot settle a level-scaled magnitude at all | 17,972 hits were cited as decisive, treating 12 crawled characters as if all were level 60. **The crawl records no character level** (Phase 0 T2) and this ability scales 2.4/level — a level-40 character deals 74–97 for the same spell. With Holy partial resistance on top, the figures discriminate nothing. **Generalised into primer §5:** never cite pooled damage about a magnitude that varies with something the crawl does not record |
| 2026-08-04 (1x) | 🆕 **`max_level` added to `spell_dbc_raw`, and the owner re-extracted the same day** | Without it a level-scaled magnitude cannot be computed. **1,653 spells carry a real cap; 196 of the 354 level-scaled catalog spells are capped**, so T4 needs it. Column alignment verified independently (Holy Supernova R6 `spell_level 60`, R1 `14`, cooldown 40,000 ms). ✅ **No longer a T4 blocker — it is populated** |
| 2026-08-04 (1x) | 🆕 **Magnitudes are also reached by `EffectTriggerSpell`, not only by tooltip `hidden_refs`** — ~519 spells still unattributed | Found while checking **Hammer from the Heavens** (`282987`), the owner's largest stat-weight unknown: it is triggered by Hour of Judgement (`282986`), two hops from any card, so `1x`'s hidden_ref-based extractor never saw it. **529 catalog → out-of-catalog trigger links across 519 distinct targets.** Deliberately not built here — multi-hop chains need cycle handling and an attribution decision, and **T5 already owns the `triggers` relation** |
| 2026-08-04 (1x) | ⚠ **The "15 rank differences" number was nearly published; the honest figure is 7** | Eight entries had a coefficient at one rank and none at the other — **not** a difference. Three confirmed causes: a compound form the regex cannot read (`($SP+$AP)*0.36`, Bone Arrow), a formula moved into a sub-spell (`$71791m1`, Deep Freeze), and a rank line that pulled in a **different ability of the same name** (Blood Drinker) — the duplicate-name trap surviving inside `dbc_spell_rank`'s grouping. Now a separate verdict, excluded from the headline |
| 2026-08-04 (1a) | 🔬 **REFINED: "697 wrong-rank catalog entries" is a LOWER BOUND. The real figure is 711, and 25 of them are genuinely AMBIGUOUS** | Phase 0's reporter used `max()`, which silently returns the first of a tie. Two real causes of ties: a rank line whose members *all* read "Rank 1" (`Desolation`, 5 members), and a line pulling in an other-realm 11-prefix variant (`Arcane Focus` → 912840 **and** 1212840). Now recorded as `confidence='conflict'` in `spell_id_crosswalk`, never tie-broken. `resolve_entry_id()` returns `level_spell_id=None` plus a candidate list when ambiguous |
| 2026-08-04 (1a) | 🆕 **The fingerprint rule needs TWO field sets, not one** | The strict set (school, cooldown, cast, power type, radius, effects) answers *"are these the same ability?"* — the hard rule's case. It is the **wrong test** for *"are these two ranks of one ability?"*: rank legitimately changes radius, cooldown and `power_type`, and higher ranks **fill effect slots** the lower rank leaves empty (Malice `[6,0,0]`→`[6,0,6]`→`[6,6,6]`). Strict comparison flagged 106 rank "conflicts", almost all ordinary talents. `RANK_FINGERPRINT_FIELDS` = school + effect-structure compatibility leaves **8 rows on 2 cards**, both `Necrosis`, whose school genuinely changes across ranks (0 → 32 Shadow → 1 Physical). That one is real |
| 2026-08-04 (1a) | ⚠ **`owned_cards` must NOT have a foreign key to `spells`** | Turning on the `foreign_keys` pragma rejected **47 of the owner's own 4,465 owned-card rows** (39 distinct spellIds). Not bad data: **all 39 resolve in `CharacterAdvancement.dbc`** and are simply absent from `spell-export.json`. Phase 0 finding #5 (the export goes stale within days) reproduced from his own collection. FK dropped; `build_index.py` reports the count every run |
| 2026-08-04 (1a) | 🆕 **The `entry_id` never-join rule got STRONGER with more data** | Phase 0 saw 1 numeric collision in 1,054 entry_ids. With 1,487 observed there are **4** (`1152`, `36936`, `50029`, `50043`) and **still 0 real matches** — e.g. `1152` is `Path of Healing` in the crawl and `Purify` in the catalog. 1,487/1,487 resolve through CharacterAdvancement; 3,061/3,061 catalog ids are reachable from a CA rank slot |
| 2026-08-04 (1a) | ⚠ **`build_dbc_index.py`'s extract exporter was a hardcoded column list** | It is the **only** way a session without the game client sees `spell_dbc_raw`, so the 17 fingerprint columns added this session were invisible everywhere except this machine. Now `SELECT *`. Any column added to that table and forgotten in the exporter has the same failure mode — silent, and only visible to whoever has the client |
| 2026-08-04 (1a) | ✅ **Daily crawler is AUTOMATED; catchup stays manual** | The manual-first condition from Phase 0 T6 is satisfied. Trigger is **at logon** (owner's stated pattern is "when I turn on the computer"), not a clock time — which also makes missed-run catch-up moot. Once-per-day guard lives in `run_crawler_scheduled.bat`, not the trigger, since logging on twice a day is normal. Registered by a committed script, documented in `SCHEDULING.md`. **`catchup_crawler.bat` is deliberately never scheduled** |
| 2026-08-04 | 🎯 **RESOLVED (was the Phase 1 gate): `entry_id` = CharacterAdvancement ID, and `CharacterAdvancement.dbc` is extractable** | 0 of 1,054 crawled entry_ids equal a catalog `spells.id`; the one numeric collision is two unrelated cards. `entry_id` is rank-independent, `spellId` is rank-specific. The client ships the mapping as a DBC (10,231 rows; slots 5–9 = `SpellRank[5]`). 1,054/1,054 resolve, 660/660 names agree. Corroborated independently by BisBeard, which keys on `entryId` and carries no spellId at all |
| 2026-08-04 | ❌ **RETRACTED: the contiguous rank rule** — replaced by a level gate | 4,791 non-contiguous rank lines vs 1,908 contiguous. Winds of Winter R1 `274121` → R2 `274129`. The rule that *does* hold: highest rank with `SpellLevel <= level`, verified against both captured in-game tooltips. **Primer §5's "check ±1–3" heuristic is unsafe in general** |
| 2026-08-04 | 🚨 **≈50% of the multi-rank catalog carries the wrong rank's magnitudes** | 697 of 1,409 catalog entries in a rank line are stored at a rank a level-60 character doesn't hold, and in all 697 the correct id is absent from the export entirely. Sensitivity-checked: 697–794 across four grouping strictnesses |
| 2026-08-04 | ❌ **RETRACTED: "spell 274132 is absent from the client"** | It is **Winds of Winter Rank 5**. The absence was an artifact of `spell_dbc_raw`'s catalog±3 scoping, which excluded non-contiguous rank siblings. Fixed (+7,639 ids). Settles the long-running 274121-vs-274132 confusion |
| 2026-08-04 | 🆕 **Class resolves from SkillLine NAMES, not ClassMask — coverage 13% → 58%** | Ascension renamed skill lines to class names; ClassMask is 512 ("Hero") on ~10k rows and useless. 1,789/3,061 catalog entries get one deterministic class, agreeing with 382/387 existing rows and 7/7 of primer §4's proof cases. **5 conflicts recorded, not resolved** (§2.3) |
| 2026-08-04 | 🚨 **98% of the 803 blocked hidden-formula spells resolve from NUMERIC fields** | 311 carry a non-zero `EffectBonusCoefficient`, 770 carry usable `EffectBasePoints`/`DieSides`; only 15 are genuinely empty. Highest-value Phase 1 task, and it is not currently a named one. ⚠ Numeric fields only — never the `description` string |
| 2026-08-04 | ❌ **RETRACTED (`INDEX_GUIDE` v3): "the resolver is not incremental"** | It was incremental **and destructive** — two consecutive runs took `spell_scaling`'s `dbc_hidden_formula` rows from 113 to 0, and shrank `spell_dbc_raw`. Both bugs fixed and verified idempotent. Any coverage number published from this pipeline before today was only reproducible from a clean DB |
| 2026-08-04 | 🆕 **The client DBC is the earliest complete card source** | 52/52 cards announced since 2026-07-01 are in `CharacterAdvancement.dbc`; **2/52** are in `spell-export.json`. The export goes stale within days. ⚠ Don't over-read it: CA's 10,231 records include other realms'/modes' entries — BisBeard's S10 set is 3,226 |
| 2026-08-04 | ❌ **Changelog is NOT a new-card discovery source, and NOT a phase-timeline source** | Every announced card is already in the client. Its 93 "phase" mentions are boss-mechanic phases, not content phases — `/api/phases` stays authoritative. It remains valuable for change history, prose magnitudes, and realm/status |
| 2026-08-04 | ⚠ **Target count: no endpoint carries it; per-parse character stats do NOT exist** | `participant_count − player_participant_count` counts every non-player unit (boss encounters median 12), not concurrent targets — must be inferred, never defaulted to 1. Ability rows carry no crit/SP/AP/haste, confirming the anticipated constraint and reinforcing Phase 3 T5's self-snapshot. **But `character_spec` carries the PATH per parse**, which is new and useful |
| 2026-08-04 | 🛑 **Phase 3 T4 re-scoped: don't build a gear optimizer; gear DATA source still open** | BisBeard takes stat weights as a first-class input (`weightString`, `configStatWeights`) and owns items/phase-tagging/BiS. Its item JSON path is phase-tagged but the serving host is unresolved. Alternative: the client's own `Item.dbc` + `ItemStat.dbc` (1,513,931 records, confirmed present, layout unverified) |
| 2026-08-04 | ⛔ **The official builder is Area-52/Elune only — NOT usable as a Darkmoon source** | It embeds a full catalog with explicit SP/AP coefficients, rarity and **essence costs** (Phase 4 acquisition inputs), but `/v2/builder/darkmoon` redirects to the homepage and those realms are max level 70. §2.5 forbids applying it cross-realm |
| 2026-08-04 | 🆕 **Phase 3 T5 delivery model settled: no `ReloadUI()`, flush on quit, Claude Code reads the file off disk** | Owner's design. Data lands at normal logout; next session I read SavedVariables + `Logs\` directly and correlate. Drops the encoded blob **and** the copyable in-game frame (both existed only for chat copy-paste) → addon writes plain readable Lua. ⚠ Corrects a misconception worth keeping straight: SavedVariables is **one file per addon, rewritten wholesale** — "one file per session" is impossible; the equivalent is one file holding a growing list, one entry per session (which is what T5 already specified). `## SavedVariables:` must be added to the `.toc` — it currently declares none, which is why the addon is copy-paste-only today. Accepted tradeoff: a client crash loses that session's captures; `ReloadUI()` stays a known-working escape hatch but is deliberately **not** implemented |
| 2026-08-04 | 🆕 **Phase 3 T5 addon must self-snapshot FIRST, at the top of every capture list** | Owner is in the logs he collects, so it's near-free. Closes Phase 0 T2's flagged *per-parse character stats* risk for at least one character (exact, not approximated from nearest capture); satisfies §2.2's tier-1 "capture stats alongside" rule automatically; is the **only** source of *measured* gear-scaling curves for §2.10; makes him Phase 2's calibration anchor. **Deferred deliberately** — no interim script, do it properly in Phase 3. Full reasoning in `PHASE_3_builds_repo.md` T5 — don't re-derive it, and don't drop it |
| 2026-08-04 | 🆕 **Two-tier crawl storage: tier 1 committed, tier 2 gitignored + local** | Volume and irreplaceability are anti-correlated. Armory/leaderboard state (1.4 MB) can never be re-fetched; per-ability bulk (6.0 MB) is re-fetchable by report id. A **committed `manifest.json`** lists every file incl. gitignored ones (records, sha256, report ids), so git knows what exists without holding it. Recovery: `--recrawl-report <id>`. Risk accepted: "reports stay fetchable" is evidenced, not guaranteed |
| 2026-08-04 | 🆕 **Armory records deduped by content hash** | Was rewriting ~90 KB per character per run (~37 MB/day at 400 chars). Now written only on change, hashed over `ci_resolved`+`stats_summary`. Also yields the gear/build timeline INDEX_GUIDE wants |
| 2026-08-04 | ❌ **REJECTED: delete raw data after normalising** | Normalisation encodes today's interpretation and the crosswalk is still unresolved (T5 gates Phase 1). Phase 0 T6 already forbids the adjacent version ("resolve at rebuild, so a crosswalk fix never requires re-crawling"). Derived DBs are the disposable layer; raw capture is not |
| 2026-08-04 | 🆕 **Crawl output gzipped (`.jsonl.gz`)**, amending Phase 0 T6's "Writes NDJSON" | 3 reports = 116 MB uncompressed; `avoidance` alone crossed the 50 MB rotation cap. Multiple GB working tree + GitHub's 100 MB per-file limit. Note: git already zlib-compresses, so `.git` size is ~neutral — the win is clone size and per-file headroom. §2.12 unaffected: docs/seeds/`index/scouted/*.json` stay plain text |
| 2026-08-04 | 🚨 **`phase_number` ≠ the server's "Phase N" label** | `/api/phases` record with `phase_number=2` is *named* "Phase 1.1" and is a child of Phase 1 (`progression_parent_phase_id`), not the Aug 8 Phase 2 launch. Build phase timelines from `name` + parent id; §2.10's gear tiers would mis-bucket off `phase_number` |
| 2026-08-04 | ⚠ **Aug 8 deadline re-scoped: baseline, not backfill** | Reports persist after a phase flip, so historical parses aren't lost. Only leaderboard standings + armory snapshots are unrecoverable → `baseline_phase1.py` is the deadline item; the report walk can grind |
| 2026-08-04 | ✅ **Changelog is a JSON API, not HTML** (`api.ascension.gg/api/v3/article/changelog`) | 353 pages / 35,238 entries with stable ids, `group_key` dates, `updated_at`. Task 3's parser never needs to touch markup. Backfill done; corpus reaches back to 2016/07/23 |
| 2026-08-04 | ✅ **`character_spell_healing` exists** | Healer support is NOT limited to an uncalibrated sim, contrary to Phase 0 Task 2's anticipated constraint |
| 2026-08-04 | ✅ **`role=healer` quirk resolved: the value is `support`** | Endpoint's own 400 body: `Allowed values: tank, dps, tanks-and-dps, support`. Open since INDEX_GUIDE v7 |
| 2026-08-04 | ⚠ **Report list endpoint is auth-gated (401)** | Discovery is sequential ID probing with a 404 "not found" signal, not a list walk |
| 2026-08-04 | ⚠ **Per-ability endpoints aggregate over `encounterIds`** | Rows carry no `encounter_id`, so per-encounter granularity costs one call each. Drove the grind-report `boss_id` grouping compromise |
| 2026-08-04 | Lego definition corrected: coupling-based, not "not a school" | A mostly-Frost cross-class cluster (Frost Mage ability + Frost Shaman feeder + Frost-damage talents) is a valid lego. Shared school is common evidence of coupling, not a disqualifier |
| 2026-08-04 | New `amplifies_school` relation type; graph is partly build-dependent | "Increases Frost damage" boosts unnamed abilities. Without a school-scoped edge that resolves against a build, school-amplifier legos are invisible to graph discovery. Enters at lower confidence per §5 |
| 2026-08-04 | ❌ **RETRACTED: "coefficients scale with rank"** and the `spell_scaling` re-key that depended on it | Derived by comparing `81193` to `270182` — two *different* abilities sharing the name "Holy Supernova" (radius 10 vs 15, cooldown 50 vs 40, instant vs 2s cast). Still plausible, now an open question |
| 2026-08-04 | ❌ **RETRACTED: "db.ascension.gg is a fifth ID space"** | `270182` resolves there normally. The db uses catalog-compatible IDs; `81193` is just another spell |
| 2026-08-04 | 🛑 **NEW HARD RULE: fingerprint before relating two IDs** | Same-name/different-ID was wrongly assumed to mean "related" **twice in one session** (`1111294` prefix, then `81193`). Compare radius/cooldown/cast/cost/effects first |
| 2026-08-04 | 🆕 In-game tooltips are **haste-adjusted** | Holy Supernova 2.00s base → 1.61s displayed ≈ 24% haste. A tooltip measures the character, not the spell — capture stats alongside every tooltip read |
| 2026-08-04 | ✅ **CONFIRMED: db.ascension.gg carries damage coefficients** on catalog-compatible IDs | `270182` → SP 24.15%, AP 15.70%, explicit Scaling fields, server-rendered. Best per-build source; rate-limited to ~2–3 automated requests |
| 2026-08-04 | ⚠ Contiguous rank rule downgraded to provisional | `270182`→`270187` is one pair; `270183`–`270186` unchecked. Must pass the fingerprint test |
| 2026-08-04 | ❌ **RETRACTED: "11 prefix / Wildcard variant" ID space.** No `wildcard_variant` crosswalk | Four in-game tooltips show plain IDs (1459, 10157, 136, 270187). `1111294` belongs to another realm, not Wildcard |
| 2026-08-04 | ✅ Catalog IDs = in-game IDs = db IDs, confirmed | 1459, 136, 270182 identical across all three. Task 4a class resolution stands |
| 2026-08-04 | 🚨 **Catalog stores Rank 1; owner plays max rank** | Arcane Intellect R1 = +2/+2, R5 = +31/+27 (~15×). Resolver must refuse rank fallback. `(spell_id, rank)` keying confirmed necessary |
| 2026-08-04 | 🆕 Fourth ID space: `CharacterAdvancement ID` (~40000) | Likely equals scouted `entry_id` (Shadow Bolt entry_id 40050 vs spellId 686). Would answer the v4 open question as "different spaces, never join" |
| 2026-08-04 | ⚠️ Ascension edits spells in place | Its Arcane Intellect grants spell power; retail's does not, same ID 1459. Class inherits from a WotLK ID; mechanics never do |
| 2026-08-04 | `db.ascension.gg` downgraded to "targeted manual lookups only" | robots.txt disallows automated access after ~2–3 requests |
| 2026-08-04 | New Phase 0 Task 4a — `SkillLineAbility.dbc` | 1,224/3,061 catalog entries (40%) are real WotLK IDs → deterministic class resolution, vs 392 (13%) today |
| 2026-08-04 | Server phase corrected to Phase 1 (Zul'Gurub); Phase 2 on 2026-08-08 | BisBeard's page metadata said "Phase 0" and was stale |

---

## Open questions raised during planning

Seed these into `open_questions` (Phase 1 Task 6) rather than losing them here.

**Resolved in session 0a (2026-08-04)** — full evidence in `RECON_FINDINGS.md`:
~~Is scouted `entry_id` the CharacterAdvancement ID?~~ ✅ **yes** ·
~~Can the client dump a CA↔spellId mapping?~~ ✅ **yes, `CharacterAdvancement.dbc`** ·
~~Is the contiguous rank rule real?~~ ❌ **no — rank is level-gated** ·
~~Does any endpoint carry target count?~~ ❌ **no, must be inferred** ·
~~Can content type be derived?~~ ⚠ **partially** ·
~~Are per-parse character stats available?~~ ❌ **no (but Path is)** ·
~~Which ID space do `ascensionlogs.gg` payloads use?~~ ✅ **catalog/client space**

**Also resolved 2026-08-04 (pre-Phase-1 follow-ups, `RECON_FINDINGS.md` §A1–A3):**
~~Is there a playable-pool discriminator in the CA table?~~ ✅ **yes — slot 121 byte 2, now
`dbc_character_advancement.in_current_pool`; 3,129 of 10,231, covers 1,054/1,054 observed** ·
~~Which ID space does the client's `WoWCombatLog.txt` use?~~ ✅ **plain client `Spell.dbc`, 809/809 —
no fifth space** · ~~Do the `gt*` tables match retail?~~ ✅ **yes, unmodified; crit = exactly 14.0 at
level 60, validating both the tables and the row-index decoding**

**Also resolved 2026-08-04 from the two owner-supplied db.ascension.gg pages:**
~~Fel Infused Weapon school (Fire vs Shadowflame)?~~ ✅ **both right — `276076` is a Fire *enchant*
spell that deals no damage; the damage is `276075`, SchoolMask 36 = Shadowflame** ·
~~Holy Supernova AP term?~~ ✅ **three-way (0.159 / 0.157 / 0.161) and immaterial — treat as ~0.16 ± 0.002** ·
🆕 **Do coefficients scale with rank?** — partially answered: within the Holy Supernova line
`EffectBonusCoefficient` is *identical* at R1 and R6; only the flat term scales (60 → 594)

**Resolved in session `1x` (2026-08-04):**
~~Does `stats_summary.sourcesByStat` itemise per-source stat contributions?~~ ✅ **Answered
and CLOSED after four deferrals — and its recorded justification was wrong.** It itemises
**item sources only** (`gear` / `enchant` / `set`), never talents or path grants, so it
could never have settled the Path of Duality question `PROGRESS` claimed for it. ⚠ **The
whole `stats_summary` block is gear-only** (explicit `_gearOnly` key; a level-60 character
shows Strength 13) — a real trap for Phase 3, which must not read it as a character sheet.
✅ Genuine value instead: a clean gear-only stat vector for 48 characters, exactly what
§2.10's gear tiers need — plus independent confirmation of 8 of 9 level-60 rating
divisors, with **armor penetration the lone conflict** (below). ·
~~Do damage coefficients scale with rank?~~ ✅ **YES** — 169 of 865 lines with numeric
data vary, 34 of 166 with text data vary, in a ramp-then-plateau shape. `spell_scaling`
needs rank keying; see the plan-changes table. ·
~~What are Hammer from the Heavens' coefficients?~~ ✅ **RESOLVED mid-session** from an
owner-supplied live tooltip + the db.ascension.gg pages + a `--with-dbc` re-extraction:
**122–145 Holy, +9.1% SP, +9.1% AP** at level 60 (level scaling **uncapped**). This was
the largest single unknown in the Paladin build's stat weights, open since v5. §10's
assumed 30/30/40 split becomes **~21/23/57** — right that SP and AP are equal, wrong
about how flat-dominated it is, which *reinforces* the existing spell-crit-first gearing
order. ⚠ Two intermediate answers were retracted along the way; see the plan-changes table.

| Question | Blocks | How to settle |
|---|---|---|
| ⚠ **NEW (1x):** is armor penetration 5 or 4.2 rating per 1% at level 60? | Physical-build stat weights only | **Conflict, recorded not resolved (§2.3).** The site's own calculator says **5**, the client's `gtCombatRatings` says **4.2**. Every other level-60 divisor agrees exactly across both sources (crit 14, hit 10, haste 10, expertise 2.5, dodge/parry 13.8, defense 1.5, block 5). Settle with a level-60 in-game armor-pen reading |
| What is the current maximum report ID? | Sizes the historical backfill | Emerges from a full crawler run (no list endpoint exists to ask directly) |
| ⚠ **NEW (1x):** does a level-scaled flat ever need a cap the crawl/tooltip can't reveal? | Nothing — recorded for completeness | ✅ Largely answered: `max_level` is extracted and populated. **1,653 spells carry a real cap; 196 of the 354 level-scaled catalog spells are capped.** What remains unverified is whether the engine applies the cap the way `min(level, max_level)` assumes — Hammer from the Heavens couldn't test it (`max_level = 0`). Settle opportunistically by checking one *capped* level-scaled spell's in-game tooltip against the computed value |
| ~~⚠ (1x): should `EffectTriggerSpell` chains be followed for magnitude attribution?~~ | — | ✅ **RESOLVED in `1b` (owner decision 2026-08-05):** yes, bounded — depth ≤ 2, cycle-safe, single-path, out-of-catalog targets, `confidence='inferred'`. 724 magnitude rows attributed; 26 ambiguous targets deliberately left unattributed (their attribution question is real but needs per-case judgment, not a looser walk) |
| ⚠ **NEW (1b):** 243 `talent_amplifiers` rows are flagged 'needs manual review' and contribute no graph edges | Amplifier coverage of the relationship graph | Human read of the staging rows (bulk-extracted target lists that didn't cleanly resolve). T6 should carry this as a standing open question; a few (e.g. Improved Cleave, now hand-seeded) are high-value |
| ⚠ **NEW:** the 97-card gap between `in_current_pool` (3,129) and BisBeard's S10 count (3,226) | Exactness of the card-pool scope | Intersect BisBeard's `entryId` list against `in_current_pool=1` and inspect the difference |
| Which of the 5 `class_origin` conflicts is right? | `class_origin` correctness | Proc test or live tooltip per spell. Note Fel Infused Weapon's existing value ("Duality") is a Path, not a class |

| Where is BisBeard's item JSON actually served from? | Phase 3 T4 gear source | Read the base-URL construction in its `itemDatabaseSync` chunk, or ask the author |
| Are `Item.dbc`/`ItemStat.dbc` layouts stable enough to extract? | A gear database with no third-party dependency | Extract a handful of known items, compare against in-game tooltips |

| What do CA slots 14/15/17/21/25/29–41 mean? | Acquisition / prerequisite modelling | Correlate `raw_ints_json` against known card properties — no re-extraction needed |
| ⚠ **NEW:** Fel Infused Weapon per-level term — db renders **4.5**/level, client DBC says **1.5** (exactly 3×) | The card's flat damage component, which the docs currently have in the wrong *shape* too (`ppl` is a per-level rate, not a flat add) | **In-game tooltip read at level 60** — fully resolved there, tier 1, beats both. db was byte-faithful on Holy Supernova, so suspect a rank/variant (`276069` vs `276076`) or a stale snapshot |
