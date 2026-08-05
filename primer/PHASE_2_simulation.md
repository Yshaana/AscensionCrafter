# PHASE 2 — Simulation Engine (Layer 3) — v4

**Read `00_ARCHITECTURE.md` and Phase 1 first. Hard dependency: `spell_mechanics` (Phase 1 T4) and
`spell_profile()` (Phase 1 T7). A sim built before those simulates placeholders.**

---

## Progress (session `2c`, 2026-08-05): gates G0–G4 + T4b, T8, T9, T10, T11 ✅

Full detail in `Session_2026-08-05_2c_gates_and_talents.md`. **PHASE 2 IS
COMPLETE**, with one exit criterion deliberately moved to 3a (§8.2).

New: `core/sim/{talents,predictions,cache,diff,report}.py`,
`ingest/export/seed_predictions.py` (new rebuild step),
`predictions/CALIBRATION_TOLERANCE.md`. Validation is **38 checks**.

**The headline is that four things `2b` believed were wrong, and each was found
by a gate rather than by a parse:**

1. **Holy Shock resolved to 0** and inverted the rotation conclusion — because a
   rank sibling's sub-spells were never extracted (G4). Fixed; **optimal now
   beats observed, 848 vs 823**, restoring build doc §11.
2. **The 1.31 school ratio is confounded** by a weapon input from a different
   session (G1). Demoted; replaced by weapon-free pair ratios.
3. **Consecration and Exorcism were never outliers** — the calibration tool
   matched them by NAME and resolved the wrong spells (G3). Our own
   never-match-by-name rule, unapplied to our own tooling.
4. **The type-121 double-count theory is wrong twice over** (G2): the anchors do
   not carry 121, and the resolver never counted it as a swing anyway.

**Plus a bug this session introduced and caught:** `resolve_numeric_formulas.py`
ran `DELETE FROM spell_effect_values` unscoped, destroying the trigger-attributed
rows `relationships.py` owns. Invisible in the rebuild (which runs it first) and
only visible on the standalone re-run its own docstring invites — it zeroed
Hammer from the Heavens. Now scoped to `via IN ('self','hidden_ref')`.

**T4b, talent modelling — what it does and does not explain.** Built on auras
107/108 + `EffectMiscValue` + `EffectSpellClassMask` from numeric fields, as
`2b` specified. ⚠ **`EffectSpellClassMask` had to be added to the extract** — it
was parsed and never written out, so no earlier session could have done this.

* **Improved Cleave's class mask is byte-identical to Lightbound Cleave's**
  (family 4, `[4194304,0,0]`), so its +120% `SPELLMOD_ALL_EFFECTS` reaches it —
  **×2.20**, from numeric fields alone. It reaches Cleave and Fel Cleave, and
  does **not** reach Whirling Light, Dawnreaver or Dawn Strike. The chase-list
  ranking now has a mechanical proof rather than an argument.
* 🚨 **Holy Power and Holy Specialization are CRIT talents, not damage
  multipliers** (aura 71, `+5%` crit chance with Holy each). The build doc calls
  them part of a "stacked Holy multiplier chain"; two of that chain's members do
  not multiply damage at all.
* **The modelled talent layer is only ×1.155** for Holy (Answered Prayers +10%
  all schools, Twin Disciplines +5% Holy) against a logged ~2.1×. The residual is
  **not claimed to be talents** — see §8.1.
* **Unknown auras are named, never assumed inert.** 6 talents use auras outside
  stock 3.3.5 (231, 333, 122, 136); 4 more are `SPELL_AURA_DUMMY`, i.e. a
  server-side script that no numeric field states. Both sets are listed by name
  in `warnings`, because a talent silently contributing 1.0× is indistinguishable
  from one read correctly.

---

## Progress (session `2b`, 2026-08-05): T5, T6, T7-cheap-half ✅ — plus 4 data bugs

Full detail in `Session_2026-08-05_2b_sim_tiers.md`. Validation is now **30 checks**
in `py tools/audit/check_sim_engine.py`. New: `core/sim/{apl,tiers,apl_gen,uncertainty,
weights}.py`, `cli/sim.py`, `tools/audit/calibrate_vs_log.py`, `fixtures/`,
`predictions/`.

**Deviations from this document, and why:**

1. **T6 does NOT source ranges from `spell_mechanics.uncertainty_json`** (owner
   decision). Measured across all 3,747 rows, that column cannot serve:
   `damage_formula_terms_json` is stored `low: None, high: None, basis:
   non-numeric`, and every numeric field carries a `±0%` confidence-mapping
   default labelled "heuristic, not measured". Sampling it would report ±0%
   knowledge uncertainty — worse than none, because it looks authoritative.
   Ranges live in `core/sim/uncertainty.py`'s **POLICY table** instead: a stated,
   arguable assumption, kept out of Phase 1's truth table so invented ranges
   never acquire tier provenance.
2. **`expected_hit` changed meaning.** It resolved every damage term a card could
   reach into one number under one avoidance roll and one crit roll — not a
   quantity that occurs in the game. It now resolves ONE event; `expected_cast`
   composes them. See "per-source-spell events" below.
3. **T7 is half-done by design** (owner decision): `stat_weights` and
   `compare_paths` shipped; `gear_tier_presets` and `scaling_curve` deferred to
   Phase 3, which owns the `items` table — without it they would run on
   hand-invented stat blocks.
4. **T8 calibration started early**, because the owner's combat logs were
   available. `tools/audit/calibrate_vs_log.py` is the tool; results below.

**🚨 The structural finding T5 could not have been built without:** an ability is
not one event. Hour of Judgement is three — its own periodic tick, its own direct
terms, and the Hammer from the Heavens pulse it triggers — resolving on different
tables. Worse, **trigger-reached damage can be DELIVERED periodically**: HoJ's
effect 1 is `SPELL_AURA_PERIODIC_TRIGGER_SPELL` at 500 ms over a 10 s duration, so
one cast fires the pulse **20 times**. The pulse spell itself is not periodic —
the delivery is, so periodicity must be read off the **triggering effect slot**,
never the triggered spell. 34 cards are affected.

**Calibration result, and the trap in it.** Comparing the sim's base per-event
value against logged non-crit averages across five of the owner's parses:

* within any ONE log, a school's abilities agree to ~±0.03, and since Hammer from
  the Heavens and HoJ's own tick are structurally unrelated formulas, that
  agreement **validates both base formulas**;
* the **absolute** multiplier swings **1.41× between sessions** (Holy 1.76 → 2.48)
  — that is buff and gear state, not talents;
* **the durable quantity is the Holy ÷ Holystrike ratio, 1.31 ± 0.03**, because
  buff state cancels in a ratio.

🛑 **T8 must not fit one talent multiplier from pooled logs.** Fit per-log with
buff state known, or model buffs and let the residual be talents.

---

## Progress (session `2a`, 2026-08-05): T1–T4 ✅ built as specified, with four deviations

Full detail in `Session_2026-08-05_2a_sim_foundation.md`; validation is
`py tools/audit/check_sim_engine.py` (includes T3's mandated
`mean(roll_hit × 100k) ≈ expected_hit` assertion — a standalone script per the
repo's no-test-framework precedent, not pytest).

1. **T3 addition:** trigger-attributed magnitudes (`via='trigger_hopN'`,
   confidence=inferred) ARE summed into `expected_hit`, flagged
   `calibration_anchor=False` and listed in `triggered_components`. Excluding
   them zeroes 444 cards.
2. **T1 deviation:** crit suppression vs higher-level targets is *warned about,
   not modelled* — open question `melee_crit_suppression_vs_higher_level`
   (owner's parse hints it exists; no retail constant fabricated).
3. **T4 deviation:** talent stat/multiplier resolution is deferred to
   calibration — component mode warns per unmodelled slot; sheet mode
   (`stats_override` = FINAL sheet values) is the exact path today. Duality is
   parameterised at the *measured* values (SP amp 1.895, AP factor 0.548
   anomaly) with warnings, never the tooltip's.
4. **Known 2a scope cuts owned by T5/T6:** `expected_hit` is per-event
   (direct-vs-DoT term split undone, `n_ticks()` exposed), CP terms
   unparameterised, hybrid mitigation unsplit, AoE totals refuse when
   falloff/split data is NULL.

🚨 **T5 must start by finishing `trigger_attributed_coefficients_not_in_spell_scaling`**
(in_progress). The decision is MADE (owner, 2026-08-05): coefficients live on the
trigger TARGET — `seed_hand_coefficients.py` seeds HftH's 9.1% SP/AP on 282987
(tier-3 `db_ascension_gg`). T5 implements the serving half: the ability model
pulls `spell_scaling` rows per component `source_spell_id` (bounded, single-path,
`confidence='inferred'` when trigger-reached). Until then a card's profile is
flat-only on trigger-reached damage (~45% HftH understatement stands).

---

## The SimC decision, stated once

**Port SimC's combat math into Python. Do not fork SimC.**

| What SimC has | Reusable? |
|---|---|
| Two-roll melee attack table, glancing blows, dual-wield miss penalty, armor DR curve, partial-resist model, haste/GCD handling, rating conversions | **Yes — port the math.** Decades of accumulated correctness, and the genuinely hard part |
| Event-queue architecture | Yes, as a design pattern |
| Class modules, APL grammar, spell data | **No.** All assume a fixed class owns a fixed ability list — the architectural root that fights a classless system |

Forking means C++, a build toolchain, and a new C++ module per Ascension ability: slow to iterate and
effectively closed to a non-coding project owner.

**Requirement:** every ported formula carries a comment naming its source (SimC file/function, or the
WotLK mechanic) **and** whether it's been validated against real Ascension parses. Ascension is
heavily modified — a formula correct in retail WotLK is a *hypothesis* here, and Task 8 is what tests
it.

---

## Task 1 — `core/sim/combat_engine.py`

The shared physics.

**Rating conversions (level 60):** crit, hit, haste, expertise, armor pen. Source from the client's
`gtChanceToMeleeCrit`/`gtCombatRatings` DBC tables (Phase 0 T4), **not** hardcoded retail constants —
Ascension may have changed them, and that's exactly the silent assumption that corrupts everything
downstream. If unextractable, hardcode with a loud comment and file an open question.

**Attack table resolution.** Given attacker state, `TargetProfile`, and a mechanics row:
- Melee: miss → dodge → parry → glancing → block → crit → hit (two-roll)
- Spell: miss → resist → crit → hit
- Table selection comes from `crit_table`/`hit_table`/`rolls_hit_check` **independently** — an
  ability can crit on the spell table while rolling melee hit. Primer §5 is explicit, and this has
  bitten the project before
- `rolls_hit_check = 0` → no avoidance roll at all (periodic effects, procs riding a landed attack)
- `can_be_full_resisted = 0` → no full-resist roll, but **partial resistance still applies**
  (primer §1 v17: "unresistable" ≠ "resistance-proof")

**Mitigation:** armor DR (level-scaled), partial resist by school and resistance, level-based
miss/crit suppression against +2 vs +3.

**Target profile:**

```python
@dataclass
class TargetProfile:
    level: int              # +2 dungeon vs +3 raid: spell miss ~6% vs ~17%
    armor: int
    resistances: dict
    dodge_pct: float
    parry_pct: float
    block_pct: float
    count: int = 1
```

**Hard rule:** if a needed field is NULL or `confidence='conflict'`, the engine raises or emits a
loud warning — **never a silent default.**

---

## Task 2 — Content profiles and roles (§2.8, §2.9)

The scenario model. This replaces the flat patchwork/cleave/aoe triple.

```python
@dataclass
class ContentProfile:
    name: str
    content_type: str       # 'raid','world_boss','dungeon_normal','dungeon_mythic','solo','pvp'
    difficulty: str | None
    target: TargetProfile
    fight_duration: float
    raid_buffs_available: bool
    self_sustain_required: bool
    incoming_damage_dps: float
    movement_pct: float
```

**Ship presets, derived from real crawled encounter data wherever possible** (Phase 0 T2 determines
what's derivable):

| Preset | Shape |
|---|---|
| `raid_boss_st` | 1 target, +3, long, full raid buffs, no self-sustain |
| `raid_boss_cleave` | 3 targets, +3, long, full buffs |
| `raid_aoe` | 10–15, +3, medium |
| `mythic_dungeon_st` | 1, +2 elevated, medium, partial buffs |
| `mythic_dungeon_aoe` | 5–8, +2 elevated, short bursts, **some self-sustain** |
| `dungeon_normal_aoe` | 5–8, +2, short, partial buffs |
| `world_boss` | 1, +3, very long, variable buffs, high incoming damage |
| `solo_grind` | 1–3, +0/+1, short, **no raid buffs, self-sustain required, high incoming damage** |

**Why this matters more than it looks:** a solo build trading 8% DPS for self-sustain is *better* in
`solo_grind` and *worse* in `raid_boss_st`. A DPS-only, buff-assuming sim reports it as strictly
worse and would steer a solo player wrong. Same for `raid_buffs_available=False` — a build leaning on
external mana return or a raid crit buff collapses solo, and nothing else in the stack would catch
that.

**Roles and metrics:**

```python
class Role(Enum): DPS; TANK; HEALER; HYBRID

class Metric(Enum):
    DAMAGE_DONE; HEALING_DONE; ABSORB_DONE; DAMAGE_TAKEN
    EFFECTIVE_HP; SURVIVAL_TIME; THROUGHPUT_PER_MANA; THREAT
```

`SimResult` carries **all computable metrics**, with `primary_metric` set by role. Even a pure DPS
build reports self-healing and damage taken — which is exactly what makes solo evaluation possible
without a separate code path.

---

## Task 3 — `core/sim/ability_model.py`

```python
class ResolvedAbility:
    """Built once from spell_profile(). All three tiers use this — they may differ in how
    rigorously they evaluate over time, never in what an ability does."""
    def expected_hit(self, char_state, content: ContentProfile) -> ExpectedHitResult: ...
    def roll_hit(self, char_state, content: ContentProfile, rng) -> HitResult: ...
```

`ExpectedHitResult` carries mean, variance, the hit/crit/avoid breakdown, per-metric output, and
`warnings`. **A test must assert `mean(roll_hit × 100k) ≈ expected_hit`** — that's the guard against
the tiers silently diverging.

AoE per `damage_split_behavior`/`max_targets`/`falloff_*`, not one generic rule — the project's own
data shows three different behaviours.

---

## Task 4 — `BuildSpec`

Used by the sim, legos, builder UI, and guide generator. Get it right once.

```python
@dataclass
class BuildSpec:
    character_level: int
    role: Role
    path: str
    abilities: list[SlottedCard]     # spell_id + rank, up to 30
    talents: list[SlottedCard]       # spell_id + rank, up to 25
    gear: dict[str, GearItem]
    consumables: list[int]
    raid_buffs: list[int]            # ignored when content.raid_buffs_available is False
    stats_override: dict | None
    realm: str
    season: str
    source: str                      # 'user_designed','crawled','optimizer_generated'
    user_id: str | None
```

**Ranks are mandatory.** A build with 3/5 cards is a different build.

`core/builds/stats.py :: compute_stats(build_spec, content)` resolves gear + buffs + talents + path
bonuses into `char_state`. Real work — path bonuses, percentage multipliers, and stat conversions
(Int→SP, Int→crit) interact — and it must be **one implementation** used by every consumer.

---

## Task 5 — Three sim tiers

| Tier | Method | Cost | Answers |
|---|---|---|---|
| **Fast** | Closed-form. Expected value × constrained casts/sec | ms | "Does A beat B, roughly, now" |
| **Medium** | One deterministic timeline. Real cooldowns/GCD/resources, **averaged** crits and procs, no RNG | ~0.1s | **"Is this rotation physically castable?"** Resource starvation, cooldown collision, GCD saturation |
| **Slow** | Monte Carlo, N iterations, full RNG | seconds | Variance, CIs, proc chains, uptime distributions |

**Medium is worth building.** Fast sim assumes you cast an ability every N seconds because its
cooldown allows it, and silently misses that you're GCD-locked or out of mana — an error class fast
sim can't see and slow sim only reveals through noise. Medium is also the right default for the
eventual interactive builder: fast enough to feel live, honest enough to catch castability problems.

```python
def fast_sim(build_spec, content: ContentProfile) -> SimResult
def medium_sim(build_spec, apl, content: ContentProfile) -> SimResult
def slow_sim(build_spec, apl, content: ContentProfile, iterations=1000, seed=None) -> SimResult
```

**Every `SimResult` carries `warnings`** for any ability whose contribution used a NULL or conflicted
field. An AoE ability with unknown falloff at 15 targets appears there, never silently computed.

**APL:** structured JSON priority list, small enumerated condition grammar (resource thresholds,
cooldown-ready, buff active, combo points, health thresholds for self-sustain abilities). **The APL
does not branch on target count or content type internally** — a build's AoE rotation is a *different
APL passed for that content profile*, keeping comparisons explicit.

`core/sim/apl_gen.py` produces a default APL from a build (priority by damage-per-resource and
per-GCD, finishers at max CP, cooldowns on cooldown, **self-sustain abilities gated on health when
`self_sustain_required`**). Good enough to compare builds without hand-authoring, and it becomes the
guide's rotation section.

---

## Task 6 — Uncertainty propagation (§2.4)

**The change that makes sim output honest.**

```python
# core/sim/uncertainty.py
def sim_with_uncertainty(build_spec, content, tier='fast', samples=500) -> UncertainResult:
    """Monte Carlo over INPUT UNCERTAINTY (not combat RNG). Each sample draws every uncertain
    mechanic value from its uncertainty_json range, runs the sim, and collects the distribution.
    Cheap because fast_sim is milliseconds."""
```

`UncertainResult` reports: nominal DPS, the range, the confidence interval, **and which inputs drove
the spread.**

```python
def sensitivity(build_spec, content) -> list[dict]:
    """For each uncertain parameter: how much would the DPS range narrow if it were resolved?
    Sorted descending. THIS IS THE VERIFICATION QUEUE."""
```

Feed the output back into `open_questions.variance_contribution` (Phase 1 T6). That closes the loop:
the sim tells the database what's worth measuring, the database tells the sim what it can trust.

**Present both uncertainties separately and never merge them.** Combat RNG variance ("this build
rolls between 3900 and 4500 on any given pull") and knowledge uncertainty ("we don't know this
coefficient, so the true mean is somewhere in 3800–4600") are different things. Merging them into one
error bar hides the one you can actually do something about.

---

## Task 7 — Stat weights, path comparison, gear curves

### Stat weights

```python
def stat_weights(build_spec, content, method='fast', delta=100) -> dict:
    """Finite difference: re-sim at stat+delta per stat, normalize. Returns weight, per-stat
    DPS delta, uncertainty on each weight, and warnings."""
```

~8 extra sims per call, trivial with caching. Points to get right:

- **Per content profile.** Raid ST and solo weights genuinely differ, and not only because of target
  count — no raid buffs changes the marginal value of everything
- **Detect cap effects.** If marginal value collapses at higher deltas, a cap is near. Primer §5: an
  overcapped stat is worth exactly zero. Report the curve, not just the slope
- **Test delta sensitivity.** A weight that moves with `delta` is a warning sign, not a number
- **Hit weight must respect `rolls_hit_check`** — weight hit only against the confirmed gated damage
  share, and **state which target level it applies to.** This is the exact error that once inflated a
  hit weight from 0.3 to 2.0
- **Weights inherit uncertainty.** A weight derived from an unverified coefficient is itself
  uncertain; report the range

### Path comparison

```python
def compare_paths(build_spec, content, paths=None) -> dict
```

Re-sim under each Path's bonuses. Direct answer to "which Path."

### Gear-scaling curves (§2.10)

```python
def gear_tier_presets(season, phase, path, role) -> dict[str, StatBlock]:
    """Fresh / mid / BiS stat blocks for that server phase — NOT hardcoded. Sourced, in order:
    (1) BisBeard's phase-tagged item data if Phase 0 T9 found it reachable,
    (2) the builds repo — what real characters at that phase actually wear,
    (3) db.ascension.gg item pages.
    Reads from Phase 3 T4's `items` table either way."""

def scaling_curve(build_spec, content) -> dict:
    """Sim at each gear tier. Report DPS and the slope."""
```

Catches "great now, dead later" automatically — the exact mistake the primer warns about, where
flat-value abilities dominate in greens and decay with gearing. As the server advances phases, the
tiers move with it.

---

## Calibration gates (added by the `2c` addendum, 2026-08-05) — ALL CLOSED

These were gates on T8 and on talent modelling, not new tasks. Every one is now
closed; kept here because each closed by overturning something, and the
overturned version is still quoted in older docs.

| Gate | Question | Outcome |
|---|---|---|
| **G4** | `rank_siblings_inherit_no_hidden_refs` — Holy Shock R4 sims as 0 | ✅ **RESOLVED.** Two halves: the sibling's own DBC *description* names its sub-spells (25902/25903), and those ids had never been EXTRACTED — `build_dbc_index.py` scoped `spell_dbc_raw` to catalog + **export** hidden_refs + siblings, so a sibling's own refs were never in scope. +797 ids, Holy Shock R4 = **562–608**. 🛑 Consequence: **the optimal-vs-observed APL comparison inverts back — optimal 848 vs observed 823 — restoring build doc §11** |
| **G0** | four numbers disagreeing with themselves | ✅ done, see below |
| **G1** | is the Holy÷Holystrike ratio confounded by a stale weapon input? | ✅ **YES, and 1.31 is DEMOTED — do not fit against it.** Measured composition: Holystrike is 86–100% weapon damage, Holy is 0%, so a weapon-input error passes into the ratio ~1:1. Replaced by **weapon-free pair ratios** |
| **G2** | do the Holystrike anchors carry effect type 121? | ✅ **NO.** Lightbound Cleave `[58,31]`, Whirling Light `[31,64]`, Dawnreaver `[31]`; only Dawn Strike carries 121, at every rank. **2b's base-formula validation STANDS** — three independent confirmations, not one shared bias |
| **G3** | Consecration ~3.55×, blocking the Holy-group constant | ✅ **RESOLVED, and it was our own tooling.** `calibrate_vs_log.py` matched by NAME; logged "Consecration" is **270768** and logged "Exorcism" is **270767** — Purification By Light's own out-of-catalog spells, not the catalog's 26573/879. Fixed by keying on the log's own `spellId`. The Holy group is now tight at n=3, **1.97–2.15**, with no outlier |

### G0 — the four reconciled numbers

Recorded as errata rather than silent edits (Rule 7 applies to handoffs too).

| Was | Is |
|---|---|
| "five real parses" vs a 4-row table vs "all four logs" | **5 logs scan and pass alignment; 4 contribute rows.** The fifth, `2026-08-03-20.41.34`, is a **53-event fragment** — below the 15-hit minimum on every ability. A dropped sample is a finding, so it is named |
| Holystrike `1.52` vs `1.50` for `2026-08-03 21.18` | **Moot** — every ratio was re-derived after G3 and G4 changed which spells resolve. Current per-log Holystrike for that log: LC 1.50 / Dawn Strike 1.17 / Whirling Light 1.58 / Dawnreaver 1.48 |
| `1.31 ± 0.03` when the values span 1.25–1.34 | **Withdrawn entirely by G1** (the quantity is confounded). Rule 2 applies to our own derived numbers: the band was narrower than the data |
| `check_sim_engine.py` "30 checks" | **32 checks** in `2b`'s state (31 executed). Now **38**, all pass |

### What replaces 1.31 — the weapon-free pair ratios

A same-school pair cancels weapon damage only at the extremes: both sides
carrying **no** weapon term, or both **pure** weapon-percent with no flat.
Anything between (a flat plus a weapon term — most of this kit) does not cancel,
because the flat does not scale with weapon damage. Same school means the
school's whole talent stack cancels too, leaving the ratio of the two **base
formulas** — a claim about our data that a parse checks directly, with no fitted
input at all.

| Pair | Predicted | Observed | Worst delta |
|---|---|---|---|
| Hammer from the Heavens ÷ Hour of Judgement's own tick | **1.718** | 1.697 / 1.773 / 1.685 / 1.771 | **3.2%** over 4 logs |
| Dawnreaver ÷ Whirling Light | **0.769** | 0.768 / 0.720 / 0.757 | **6.4%** over 3 logs |

**These are the targets a talent model must reproduce.** `calibrate_vs_log.py`
computes them as a first-class report and labels each pair REPRODUCES / MISSES.

⚠ **To un-confound the ABSOLUTE numbers later, and it is free:** capture a
character-sheet screenshot (weapon damage, AP, SP) at the start of the next
logged session, so one parse finally has a same-moment stat block.

---

## Task 8 — Calibration

```python
def calibrate(character_name, encounter_id=None) -> dict:
    """Pull a crawled character's real build via the crosswalk (never string matching), sim it
    against a ContentProfile matching that encounter, diff against their actual logged DPS,
    per-ability damage share, crit rates, and avoidance."""
```

**Report the delta per mechanism, not pass/fail.** A discrepancy names which mechanic is
mis-modelled. That's how every retraction in this project has worked, and it's the most valuable
output of the sim before trusting it on hypotheticals.

- **Patch-aware:** never calibrate against a parse from a patch that changed the measured ability.
  `patch_entry_spells` makes this checkable
- **Per content profile:** does the raid-ST prediction match real single-target raid encounters,
  separately from mythic AoE? Strictly more informative than one aggregate number
- **Gate:** the sim isn't trusted on hypothetical builds until it reproduces ≥3 real characters
  within a stated tolerance. Write the tolerance down; treat missing it as a finding

### 8.1 — The tolerance, written down BEFORE calibrating (`2c`)

**`predictions/CALIBRATION_TOLERANCE.md`, stamped 2026-08-05 as the first act of
T8.** Aggregate DPS **±20%**; per-ability **±25%** on the non-crit average and
±15% on damage share, for abilities ≥5% of damage. Set from the measured noise
floor (the weapon-free pairs reproduce to 3.2% and 6.4%; buff state moves the
same ability 1.41× between sessions), not chosen after seeing the deltas.
Widening it needs a dated entry in that file with a reason.

**Result, reported rather than hidden: 1 of 7 abilities within tolerance.** The
six misses group by SCHOOL — Holy 1.71–1.87×, Holystrike 1.34–1.38× — which is
what an unmodelled school-scoped amplifier *or* an unmodelled buff looks like.
🛑 Not closed by fitting a constant.

### 8.1b — D4: the calibration gate before ANY cross-school ranking (2e T10)

Owner decision D4 (2026-08-05), recorded here as the standing rule: **no phase
emits a cross-school build ranking until the school residual is explained** —
either modelled (buff / Path / enchant, with the mechanism named) or per-school
calibration lands inside `CALIBRATION_TOLERANCE.md`'s recorded thresholds.
Within-school comparisons are fine before that; ranking Holy against Frost off
a sim carrying an unexplained ~1.4× Holy-side residual is not. The Phase 4 doc
carries a forward reference to this section; `SCORECARD.md` §4 applies it to
axes 1–3. *(2e status: the Holystrike residual is closed — it was the weapon
input — and the Holy residual is split into two named mechanisms; the gate
stays shut until those land inside tolerance.)*

### 8.2 — The ≥3-character criterion MOVES to Phase 3a

Recorded phase-boundary change, `2c`. Simulating a crawled character needs their
**gear**, and gear is Phase 3 T4's `items` table — the same dependency that
already deferred T7's `gear_tier_presets` and `scaling_curve`. The crawl records
per-ability damage and a build but no stat block, so "reproduces 3 characters"
would be measuring our own invented stats three times.

**Phase 2 exits without it.** What `2c` delivers instead is arguably stronger:
one character across **five logs and four sessions**, so the model is tested
against session variation — plus the weapon-free pair ratios, which are
predictions with no fitted input at all.

---

## Task 9 — The prediction ledger

**The user is a tier-1 evidence source who generates parses constantly. Capture that.**

```sql
CREATE TABLE predictions (
  id INTEGER PRIMARY KEY,
  user_id TEXT,
  build_spec_json TEXT NOT NULL, build_spec_hash TEXT NOT NULL,
  content_profile_json TEXT NOT NULL,
  predicted_value REAL NOT NULL, predicted_low REAL, predicted_high REAL,
  primary_metric TEXT NOT NULL,
  per_ability_json TEXT,          -- predicted damage share per ability
  sim_tier TEXT, sim_version TEXT, data_version TEXT,
  patch_id INTEGER, realm TEXT, season TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE prediction_outcomes (
  prediction_id INTEGER NOT NULL REFERENCES predictions(id),
  encounter_id INTEGER,
  actual_value REAL NOT NULL, actual_per_ability_json TEXT,
  delta_pct REAL, within_predicted_range INTEGER,
  notes TEXT, recorded_at TEXT NOT NULL
);
```

```python
def reconcile(user_id=None) -> dict:
    """Match the user's own parses against outstanding predictions. Report systematic bias
    per ability and per mechanism — not just aggregate error."""
```

**Why this is the best calibration source available:** it's the user's own character, so the build is
known exactly (no `snapshot_lag`), the content is known exactly, and it accumulates for free with no
test design required. Over a season it becomes a systematic record of where the model is wrong.

**Discipline:** predictions are logged **before** the parse, never fitted afterwards. The
`sim_version`/`data_version` stamps mean an old miss can be re-checked against the current model to
see whether a fix actually fixed it.

A systematic per-ability bias in `reconcile()` output should **auto-open an `open_question`** naming
the suspect mechanic. That's the loop closing on itself.

---

## Task 10 — Cache

`data/derived/sim_cache.db`, exact-match keyed on
`hash(build_spec, tier, content_profile, apl, iterations, data_version, patch_id, realm, season)`.

**`data_version` must hash every input the sim depends on** — mechanics, relationships, rating
conversions, uncertainty ranges. Hashing only `spell_mechanics` (the old design) leaves stale results
alive when a relationship or patch changes.

Design for, don't build: iteration top-up (run the delta, merge statistically) and component-level
caching of per-ability results (letting ~90%-shared board variants reuse each other's work). Keep
`ResolvedAbility` cleanly separable so neither needs a rewrite.

---

## Task 11 — Comparison and presentation

```python
def diff_builds(a: BuildSpec, b: BuildSpec, content) -> dict:
    """Ability/talent/gear/stat diff plus DPS delta with PER-ABILITY ATTRIBUTION of where the
    delta comes from — and whether the delta exceeds the uncertainty on either build."""
```

That last clause matters: a 2% difference between two builds whose uncertainty is ±10% is **not a
result**, and the tool should say so rather than ranking them.

`core/sim/report.py` renders any result, weight set, curve, or diff as (a) a structured dict, (b) a
terminal table, (c) a self-contained HTML report with charts. The HTML path seeds the eventual web
UI — keep it a pure formatter with **no logic in the renderer.**

---

## Task 12 — API and CLI

`api/sim.py` — thin service functions a FastAPI app wraps 1:1 (§2.7). `cli/sim.py` wraps those. No
logic in either.

---

## Execution order

```
1 (engine) → 2 (content/roles) → 3 (ability model) → 4 (build spec)
  → 5 (three tiers)
    → 6 (uncertainty)  → 7 (weights/paths/curves)
    → 8 (calibration)  → 9 (prediction ledger)
    → 10 (cache) → 11 (diff/report) → 12 (api/cli)
```

## Exit criteria

- ~~Calibration reproduces ≥3 real characters within stated tolerance, per content profile~~
  **→ MOVED to Phase 3a** (recorded phase-boundary change, §8.2 — simulating a
  crawled character needs gear, which is Phase 3 T4's `items` table). Phase 2
  exited without it, deliberately and on record; `PHASE_3_builds_repo.md` now
  carries the gate. *(2e T6 — the exit list and §8.2 previously disagreed.)*
- `mean(roll_hit)` ≈ `expected_hit` in test
- Stat weights stable under delta variation, or the instability is reported
- Zero silent defaults — every NULL/conflicted field surfaces in `warnings`
- `sensitivity()` output is populating `open_questions.variance_contribution`
- At least one prediction logged and reconciled end-to-end

## Out of scope

Forking SimC. A compiled engine (measure first — 10–15 abilities × 1,000 iterations should be seconds
in Python). A general APL expression language beyond the enumerated grammar. PvP modelling.
