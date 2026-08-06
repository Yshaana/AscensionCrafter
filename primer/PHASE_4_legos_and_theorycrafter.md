# PHASE 4 — The Lego Box & The Theorycrafter (Layers 4 & 5) — v2

> **`LIVE`** — the next phase plan; not yet started. **Must be true today, and is citable as current truth.** If you find a claim here that the tree contradicts, that is a defect in this file. *(Classified `3f` F8c, 2026-08-07.)*

**Read `00_ARCHITECTURE.md` and Phases 1–3 first.**

> **🆕 Terminology (2e D6, owner decision 2026-08-05): "lego" is renamed
> "kit"** going forward — a **kit** is a coupling-based cluster of cards, a
> **chassis** is the shared base a kit slots into. This document keeps its
> original wording (annotate, don't rewrite); read every "lego" below as "kit".
> The planned `core/legos/` becomes `core/kits/`. The first fully-measured kit
> is **the Cleave Kit** (`builds/shared/synergy_portable-multiplier-packages.md`
> Package 4): Lightbound Cleave + Improved Cleave, portable *because* it is
> engine-inert — all eight Cleave school variants share the byte-identical
> family-4 mask `[4194304,0,0]`, so Improved Cleave's ×2.20 reaches every one.
> **Kit discovery must REDISCOVER it from data alone — it is this phase's
> regression target.**

---

# Part A — The Lego Box (Layer 4)

## What a lego is

A **set of cards that are mechanically coupled — where removing one substantially degrades the
whole — with a measured contribution.** The defining property is *coupling*, nothing else.

**Coupling, not tags.** A lego is not "all my Frost cards" *when those cards don't interact* — a bag
of same-school cards with no mechanical relationship is not a lego. But shared school is **neither
disqualifying nor required**, and it is frequently the very mechanism the coupling runs through: a
talent that reads "increases Frost damage," a proc that fires "on Frost spell cast." A cluster can be
mostly one school and be a completely valid lego.

**Worked example (from the builds repo, the kind co-occurrence mining surfaces):** a character runs
one Frost *Mage* ability, one Frost *Shaman* ability feeding it, and 2–3 talents that boost the Mage
ability's damage. Remove the talents and the payoff collapses; remove the Shaman feeder and the
engine loses its input. That is a lego — cross-class, mostly-Frost, tightly coupled. Judging it by
"it's just Frost stuff" would wrongly discard it; judging it by coupling correctly keeps it.

From this project's own history:
- Fel Infused Weapon + Shadow and Flame + Bane + fast off-hand — a no-ICD proc engine scaling with
  attack frequency
- A quadratic-CP finisher + its generators + anything guaranteeing max-CP dumps
- Reverberation + three-shock cycling → Elemental Fusion stacking via independent per-shock windows

## Schema

```sql
CREATE TABLE legos (
  lego_id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT NOT NULL,
  engine_type TEXT,          -- 'proc_engine','burst_window','sustain','cp_finisher',
                             -- 'cooldown_loop','aoe_engine','resource_engine',
                             -- 'self_sustain','mitigation','threat'
  role_fit TEXT,             -- 'dps','tank','healer','any'
  content_fit TEXT,          -- comma list of ContentProfile names it suits
  discovery_method TEXT NOT NULL,  -- 'graph_motif','co_occurrence','sim_ablation','manual',
                                    -- 'external_sighting'
  confidence TEXT NOT NULL,
  realm TEXT NOT NULL, season TEXT NOT NULL,
  verified_at_patch INTEGER NOT NULL,
  evidence_ref TEXT NOT NULL
);

CREATE TABLE lego_components (
  lego_id INTEGER NOT NULL REFERENCES legos(lego_id),
  spell_id INTEGER NOT NULL,
  role TEXT NOT NULL,        -- 'core','amplifier','enabler','optional','anti_synergy'
  min_rank INTEGER,
  criticality REAL           -- MEASURED: output lost when this component is removed
);

CREATE TABLE lego_requirements (
  lego_id INTEGER NOT NULL REFERENCES legos(lego_id),
  requirement_type TEXT NOT NULL,   -- 'path','weapon_type','stat_threshold','level',
                                     -- 'resource_pool','exclusivity_conflict'
  requirement_value TEXT NOT NULL,
  is_hard INTEGER NOT NULL          -- hard = doesn't function at all without it
);

CREATE TABLE lego_measurements (
  lego_id INTEGER NOT NULL REFERENCES legos(lego_id),
  content_profile TEXT NOT NULL,
  gear_tier TEXT NOT NULL,          -- fresh/mid/bis — §2.10; some legos only matter when geared
  metric TEXT NOT NULL,
  contribution REAL, pct_of_total REAL,
  contribution_low REAL, contribution_high REAL,   -- inherits sim uncertainty (§2.4)
  measured_via TEXT NOT NULL,       -- 'sim_ablation','real_parse'
  patch_id INTEGER NOT NULL
);
```

`lego_measurements` being keyed by **content profile AND gear tier** is the point: a lego that's 30%
of your damage in raid ST at BiS and 8% in fresh gear solo is not one number.

## Three discovery methods — build all three, they find different things

| Method | Source | Finds |
|---|---|---|
| **Graph motif mining** | Relationship graph (Phase 1 T5) | Dense clusters — including synergies **nobody plays yet**. Pass a `build_spec` so `amplifies_school` edges resolve to the build's real same-school abilities; a purely static graph misses school-scoped couplings |
| **Co-occurrence mining** | Builds repo (Phase 3 T3) | Card sets appearing together above chance — synergies **other players already found**. Cheapest, improves every crawl day. **Also the backstop for school-scoped couplings** the graph would miss: a Frost Mage ability + Frost Shaman feeder + Frost-damage talents showing up together across builds surfaces from frequency alone, no edge required |
| **Sim ablation** | Simulation (Phase 2) | **Quantifies** what the other two only suggest |

```python
# core/legos/discover.py
def discover_from_graph(min_size=2, max_size=6) -> list[LegoCandidate]
def discover_from_cooccurrence(min_support=0.05, min_lift=2.0) -> list[LegoCandidate]
def validate_by_ablation(candidate, build_context, content, gear_tier) -> LegoMeasurement
```

**Pipeline:** graph + co-occurrence propose → ablation measures → anything with a meaningful measured
contribution is promoted with evidence. **Nothing enters `legos` without an ablation measurement or a
real parse.** An unmeasured lego is a hypothesis, and the project's whole discipline is not treating
hypotheses as facts.

**Ablation must respect uncertainty.** If removing a component changes output by less than the
build's own uncertainty range, the correct verdict is **"not measurably coupled"**, not a small
criticality number.

### Design input from session `2d` (2026-08-05) — worked examples with ground truth

The owner's framing: the packages in
`builds/shared/synergy_portable-multiplier-packages.md` (Demon Package, DK
Disease Package, Kings, and the measured **Cleave Kit**) are **examples of what
this discovery process must find on its own**. They double as a regression
suite: when discovery first runs, it must rediscover the Cleave Kit from data
alone — if it can't, a signal below is missing. Signals the worked examples
prove out, each already grounded in an existing table:

1. **Amplifier reach is queryable, so graph proposal is concrete.** Improved
   Cleave + every family-4 mask member (`[4194304,0,0]` — all 8 Cleave school
   variants) is a provable candidate cluster from `EffectSpellClassMask` alone,
   no tooltip parsing. Amplifier + mask-family = the canonical 2-card kit motif.
2. **School-parameterized families collapse to ONE kit.** The six `-bound`
   Cleaves are byte-identical fingerprints differing only in school mask — the
   miner should emit one kit with a school parameter (pick the variant matching
   the host's tallest school stack), not six near-duplicate kits.
3. **Portability is measurable: low marginal-value VARIANCE across chassis.**
   The Cleave Kit travels because it is engine-inert (proc-tested: feeds no
   Hammerdin/PBL/seal riders → no host dependency). Formally: run ablation
   against *diverse* chassis; a portable kit has stable marginal value, a
   coupled engine piece has high variance. Both are valuable — they are
   different product types and should be labeled as such.
4. **Absence of coupling is evidence, record it.** The engine-inertness verdict
   came from dedicated proc isolation tests. Discovery should treat measured
   independence as a first-class kit property, not merely missing edges.
5. **Delivery channel matters for portability.** Off-GCD/next-swing delivery
   means the kit adds a damage channel without displacing the host's rotation —
   detectable from timing attributes. Conversely its cost is host-dependent
   (converted autos starve auto-keyed riders — measured: Seal of Command rides
   white swings only), which `compatible_legos` must price per host.

**Anti-synergies are legos too.** `role='anti_synergy'` records cards that fight each other —
exclusivity collisions, weapon-imbue slot conflicts, dead talents whose triggers never fire in a
given kit. Knowing what *not* to slot is as valuable, and this project has found dead slots the hard
way repeatedly (Shadow Strikes with no Shadow Bolt; Enhanced Weapon Mastery bucket-blocked; Dual
Wield Mastery non-stacking).

## Composition

```python
# core/legos/compose.py
def compatible_legos(lego_ids) -> dict:
    """Do these fit in one build? Slot budget (30 abilities / 25 talents), exclusivity conflicts,
    path requirements, weapon requirements, resource-pool conflicts."""

def build_from_legos(lego_ids, path=None, content=None, fill_strategy='sim_greedy') -> BuildSpec
```

`compatible_legos` is what makes this a box of legos rather than a list of ideas — the "do these
click together" check.

---

# Part B — Acquisition Cost (the missing constraint)

**Per the user's framing:** a build is a **core set** (without which it doesn't function — a hard
gate) plus **flex slots** where the tradeoff is DPS gain against rarity.

Without this, the optimizer will confidently propose builds you cannot reach.

## Card acquisition cost

```python
# core/theory/acquisition.py
def card_acquisition_cost(spell_id, rank, build_theme, user_id) -> dict:
    """Expected difficulty of getting this card at this rank, for this user, on this build."""
```

Inputs, all already available or coming from Phase 0 T7:

| Factor | Effect on cost | Source |
|---|---|---|
| Already owned at required rank | **Zero** | `owned_cards` |
| Owned at partial rank | **Low** — upgrade rolls are self-funding (a hit refunds the reroll) and staff-stated to be likelier when already held | Primer §2 |
| Rarity (COMMON → LEGENDARY) | Rising | Catalog `rarities` |
| On-theme vs off-theme | Off-theme is a **structural** penalty — roll affinity skews toward what the build already looks like | Primer §2 "roll affinity (verified)" |
| Single-rank vs multi-rank | Multi-rank costs more — a hit may land 1/5 and need re-fishing. **Single-rank targets weighted up: a hit is a complete hit** | Primer §2 |
| Requires Golden pool but only owned Normal | Very high — Golden guarantee slots only hold owned goldens | Primer §2 |
| Requires a guarantee slot already spent | **Infeasible** if the character is past levelling — allocation freezes and rerolls become the only lever | Primer §2 |

## Build-level feasibility

```python
def build_feasibility(build_spec, user_id) -> dict:
    """Returns:
      - hard_feasible: bool         — every CORE card is reachable
      - blocking: list              — core cards that are not, and why
      - expected_cost: float        — summed acquisition cost of everything missing
      - protect_list: list          — owned cards that must not be rerolled away
      - chase_list: list            — ordered by DPS_GAIN / ACQUISITION_COST
    """
```

**Output format is protect/chase lists**, because that's what the in-game rapid-roller consumes, and
primer §2 explicitly says advice should be delivered as two lists rather than prose. The chase list's
ordering *is* the flex-slot tradeoff the user described, made numeric.

⚠ **Core vs flex is a human designation, not an inferred one.** The build brief (Part C) declares
core abilities; ablation can *suggest* that something is core by measuring how much it's worth, but
the declaration stays with the person. Auto-classifying core would let the tool quietly redefine what
build you're making.

---

# Part C — The Theorycrafter (Layer 5)

## Being straight about what's buildable

Most of the theorycrafting judgment is a person (or Claude) working with the tools. What's *software*
is the scaffolding making that judgment fast, consistent, and evidence-backed — not an autonomous
build designer.

## Task C1 — The principles corpus

```sql
CREATE TABLE principles (
  id INTEGER PRIMARY KEY,
  principle TEXT NOT NULL,
  domain TEXT,           -- 'stat_weighting','card_acquisition','rotation','gearing',
                         -- 'test_design','scaling','resource_management','survivability'
  role_scope TEXT,       -- 'dps','tank','healer','any'
  content_scope TEXT,
  source TEXT NOT NULL,  -- 'primer','wotlk_theory','derived_from_corpus','external_guide'
  evidence_ref TEXT,
  applies_when TEXT,     -- scope conditions; a principle that always applies is rare
  confidence TEXT NOT NULL,
  realm TEXT, season TEXT
);
```

Three sources, descending trustworthiness:

1. **The primer's §5 rules**, made queryable. Hard-won and server-specific — *percentage multipliers
   are gear-proof while flat adds decay*; *check cap status before assigning any stat weight*; *count
   what actually rolls a hit check*; *never dump a quadratic CP finisher below max*; *design tests
   that don't destroy cards*.
2. **WotLK fundamentals from the web** — attack table mechanics, rating conversions, armor curves,
   haste breakpoints. ⚠ **Every one is a hypothesis on this server until validated.** Store at
   `confidence='unverified'` with an explicit note; let calibration promote or retract them. **Do not
   let borrowed retail theory enter at the same confidence as measured local facts** — that's the
   single biggest way this could quietly go wrong.
3. **Derived from the corpus** — patterns holding empirically across the builds repo. *"Top-decile
   AoE builds all run at least one uncapped ground effect"* is checkable once there's data. Generate
   candidates, verify, store with sample size.

## Task C2 — The build brief

```python
@dataclass
class BuildBrief:
    core_abilities: list[int]      # non-negotiable — the build is FOR these
    core_talents: list[int]
    role: Role
    content_priority: list[str]    # ordered ContentProfile names — a build is rarely for one thing
    path: str | None               # None = let the tools recommend
    owned_cards_only: bool
    level: int
    constraints: list[str]         # 'must dual wield','no channeled abilities',...
    max_acquisition_cost: float | None
    user_id: str
```

**`content_priority` being an ordered list, not a single value, is deliberate.** Real builds are
"mostly mythic dungeons, some raid, occasional solo." The tools should optimise a weighted objective
across that list and **report where the compromises land** — which content the build is quietly bad
at is exactly the thing a single-scenario optimiser hides.

Workflow the tools support:

1. Brief in → `spell_profile()` the core abilities, read their relationship neighbourhoods
2. Query legos containing or compatible with the core abilities, filtered by role and content
3. Query the builds repo — is anyone already running something like this, and how
4. Compose candidates → fast sim → medium sim survivors (castability) → slow sim finalists
5. Stat weights, path comparison, gear curve on the leaders
6. Feasibility and acquisition cost per candidate
7. **Present alternatives with tradeoffs**, not one answer

That last point matters. This project's value comes from falsifiable comparison, not oracle
pronouncements. Output should be *"three directions, what each costs, what each is betting on"* — the
strongest flagged, but the reasoning visible.

**Where two candidates differ by less than their uncertainty, say so** rather than ranking them.

## Task C3 — The guide generator

Locked build → complete player-facing document. **The payoff for everything upstream.**

```python
# core/theory/guide.py
def generate_guide(build_spec, brief, format='html') -> str
```

| Section | Content | Source |
|---|---|---|
| **Overview** | What it is, what it's for, how it wins, **what content it's good and bad at** | Brief + legos + content priority |
| **Card acquisition** | **Protect / chase lists**, guarantee-slot allocation, Normal vs Golden reasoning, single-rank targets weighted up | Part B |
| **Stat priority** | Weights per content profile, caps called out, **uncertainty on each weight** | Phase 2 T7 |
| **Gearing** | Stat weights exported in BisBeard's input format plus a link to the configured optimizer (§2.11) — or, on Path B, BiS by slot with drop sources grouped by where you'd farm. Either way: enchants, gems, and **how priorities shift as you gear** | Phase 3 T4 + gear curve |
| **Rotation** | Opener, priority list, cooldown usage, what never to clip | APL |
| **Mechanics you must know** | The build's load-bearing quirks — off-GCD windows, next-swing queueing, quadratic finishers, proc ICDs | Facts + mechanics |
| **Anti-patterns** | Dead cards, exclusivity conflicts, common mistakes | Anti-synergy legos |
| **Addon setup** | Trackers the build needs: proc uptimes, CP counters, next-swing state, cooldown glows | Mechanics + APL |
| **Expected performance** | Sim output per content profile and gear tier, **with ranges, not point estimates** | Phase 2 |
| **Durability outlook** | Volatility flags on load-bearing cards — *"this ability has been nerfed three times this season"* | Phase 1 T10 |
| **Provenance footer** | Patch, realm, season; what's measured vs. predicted; open questions affecting this build | Facts + verification queue |

**The provenance footer is not optional.** A guide that doesn't distinguish measured from predicted is
exactly the artifact this project exists to avoid producing — and it's what makes the guide safe to
share with other players, which is the stated long-term goal.

**Format:** HTML first (self-contained, shareable, chartable), markdown export for the repo. Keep the
generator a pure formatter over structured data (§2.7).

## Task C4 — Addon config generation (optional, cheap)

The APL the sim runs and the rotation the player executes should come from one source. Generate an
addon rotation-helper config from the build's APL.

**Note:** WeakAura custom-function triggers are sandboxed on this server, but full custom addons work
(`AscensionCrafterExport` proves it). So: an addon config, not a WeakAura import string.

---

## Execution order

```
A:  graph motif + co-occurrence → ablation validation → composition
B:  acquisition cost (independent — can start any time; depends on Phase 0 T7 for rarity data)
C1: principles (independent, any time)
C2: brief (depends on A and B)
C3: guide (depends on everything)
C4: last, optional
```

## Exit criteria

- Every lego has a measured contribution with an uncertainty range, per content profile and gear tier
- **The lego box reproduces the project's known synergies — the Fel Infused Weapon engine, quadratic
  CP finishers, the Hammerdin core — without being hand-fed them.** This is the real test of whether
  discovery works
- Acquisition cost correctly identifies at least one historically-known infeasible build
- A guide generated for the current Paladin build is complete enough to hand to another player
- Every principle is tagged with source and confidence; no retail-WotLK assumption sits at
  `confirmed` without local validation

---

## Where this points next

> 🛑 **CORRECTION 2026-08-06 (`3d` B5): `api/` DOES NOT "already exist" as a
> service boundary.** It is a 30-line docstring with **zero functions**,
> imported by nothing, while **5 of 7 `cli/` entry points import `core/`
> directly**. The sentence below overstated a *reserved directory name* as a
> *built layer*, and a future phase reading it would budget accordingly. What
> genuinely holds is the thing that makes the layer cheap to add later:
> **`core/` purity is real and enforced** (47 files, 0 violations), so no logic
> has to be extracted from a CLI first. Read the paragraph with `api/` removed
> from the list of things already done.

Once Phase 4 works locally, the web app is a thin layer: ~~`api/` already exists as the service
boundary~~, `BuildSpec` is the canonical interchange format, the guide generator already emits HTML,
per-user data is `user_id`-scoped, and roles/content types are modelled rather than assumed. The
interactive builder becomes a UI over existing functions plus **live medium-sim feedback as the
player slots cards** — which is exactly why medium sim was worth building.

Ordering when that time comes: **build `api/`** → FastAPI over it → SQLite→Postgres (already
designed for) → builder UI → accounts → sharing. **None of it requires rewriting layers 1–4**, which
is the entire point of the §2.7 constraints.

> 🆕 **SIZED, `3f` F8, because the correction above said the layer was absent without saying what
> filling it costs — and an uncosted gap in a plan's premise is still a gap.** Re-measured at `3f`
> HEAD, not inherited: **`api/` holds 0 functions, nothing in the tree imports it, and 5 of 7 `cli/`
> entry points import `core/` directly** (`crosswalk`, `mechanics`, `profile`, `relationships`,
> `sim`; the other two are `rebuild`, a subprocess runner, and `browse`, which shells out to
> Datasette).
>
> **The work is 5 thin functions plus 5 CLI re-points, and it is small for one specific reason:
> `core/` purity is real and enforced** (50 files, 0 violations at `3f`) — no logic has to be
> extracted from a CLI first, because none of it is in a CLI. Each `api/` function is the argument
> marshalling a CLI already does, minus the printing. **The honest statement is that `core/` is the
> reusable layer today and `api/` is a reserved name**; whoever first needs a served function should
> build it there and route one CLI through it, converting the reservation into a boundary.
>
> 🛑 **Do not budget Phase 4 as though this is done.** It is cheap, not free, and it is a
> precondition of everything in the ordering line above.
