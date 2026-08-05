# PHASE 2 — Simulation Engine (Layer 3) — v2

**Read `00_ARCHITECTURE.md` and Phase 1 first. Hard dependency: `spell_mechanics` (Phase 1 T4) and
`spell_profile()` (Phase 1 T7). A sim built before those simulates placeholders.**

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

- Calibration reproduces ≥3 real characters within stated tolerance, per content profile
- `mean(roll_hit)` ≈ `expected_hit` in test
- Stat weights stable under delta variation, or the instability is reported
- Zero silent defaults — every NULL/conflicted field surfaces in `warnings`
- `sensitivity()` output is populating `open_questions.variance_contribution`
- At least one prediction logged and reconciled end-to-end

## Out of scope

Forking SimC. A compiled engine (measure first — 10–15 abilities × 1,000 iterations should be seconds
in Python). A general APL expression language beyond the enumerated grammar. PvP modelling.
