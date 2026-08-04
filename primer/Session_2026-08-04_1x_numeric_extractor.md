# Session `1x` — numeric-field DBC extractor, and the rank question settled (2026-08-04)

**Scope:** the task Phase 0 discovered and the original chunking never named — resolve
the blocked hidden-formula spells from the client's **numeric** DBC fields, and settle
*"do coefficients scale with rank?"* (a `PHASE_1` T4 blocker).

**Status: complete.** `py cli/rebuild.py` runs 14 steps clean. `core/` purity: 0
violations.

**Next session is `1b`** — `spell_mechanics` (T4) + the relationship graph (T5).

**Two of this session's results contradict the brief it was given.** Both are recorded
as corrections rather than quietly worked around, and both change what `1b` should
build.

---

## Headline

| | |
|---|---|
| blocked spells resolved from numeric fields | **794 of 887** (93 carry no magnitude anywhere — debuff/immunity markers, as Phase 0 predicted) |
| `spell_effect_values` rows | 6,367 (4,863 from the spell's own record, 1,504 from hidden sub-spells) |
| catalog spells with a decoded numeric effect | 2,981 of 3,061 |
| flat-convention validation anchors | 7, all passing |
| **"do coefficients scale with rank?"** | **YES — the working hypothesis is falsified** |

---

## 1. 🚨 `EffectBonusCoefficient` is not the SP/AP coefficient

**This was the session's premise and it did not survive first contact.**
`RECON_FINDINGS.md` Task 4 reported *"311 carry a non-zero `EffectBonusCoefficient`
(SP/AP scaling)"* and ranked a numeric extractor as Phase 1's highest-value task partly
on that basis. The **count is right. The reading of the field is wrong**, and an
extractor built on it would have fabricated SP coefficients at scale — across 311
spells, silently, with tier-4 provenance attached.

The field is stock 3.3.5a's `EffectBonusMultiplier`: a multiplier on the
*cast-time-derived default* coefficient, whose neutral value is **1.0**.

Three measurements, over the full 15,769-row `spell_dbc_raw`:

1. **7,647 of the 9,211 non-zero values are exactly `1.0`** — 83% carry no information
2. the recurring non-default values are retail's cast-time formula frozen into
   constants: `0.429 = 1.5/3.5`, `0.714 = 2.5/3.5`, `0.214 = 0.75/3.5`,
   `0.571 = 2.0/3.5`, `0.143 = 0.5/3.5`
3. **calibration** — across 98 spells whose own tooltip states an explicit `$SP*x` or
   `$AP*x`, a DBC coefficient matches the stated term in **4 of 98**. Flash Heal reads
   0.807; Revenge, Intercept, Victory Rush and Heroic Throw all read exactly 1.0
   against stated AP terms of 0.19 / 0.12 / 0.45 / 0.5

For the blocked spells specifically: of the 343 whose refs carry any coefficient,
**270 carry only 1.0**. The real coefficient surface is **≤73 spells, not 311**.

**What this means generally:** Ascension keeps the coefficients its server actually
applies in the **tooltip text** (`$SP*0.2415`), not in this numeric field, which on its
own custom cards is overwhelmingly left at the default. So the numeric extractor is a
**flat-magnitude** win — which is the large one anyway (794 spells) — and never a
coefficient win.

**In code:** the column is `spell_effect_values.bonus_multiplier`, deliberately *not*
named `coefficient`, and `dbc_numeric.py` never emits it as an SP or AP term.

⚠ This does not retire the Holy Supernova observation (`0.161` at both R1 and R6). It
reframes it: that line is one where Ascension *did* write a real value into the field.
Being right about one spell is not the same as the field meaning what it looked like.

## 2. 🚨 Coefficients DO scale with rank — Phase 0's conclusion is retracted

Phase 0 answered this from a **single** line (Holy Supernova, `EffectBonusCoefficient`
identical at R1 and R6) and concluded *"reading a coefficient off the catalog's Rank-1
entry is probably safe; reading a flat is catastrophic."* The second half stands. **The
first half is falsified.**

Measured across all **1,580** multi-rank lines with 2+ members in `spell_dbc_raw`:

| evidence | constant | varies | no data |
|---|---|---|---|
| numeric `EffectBonusCoefficient` (tier 4) | 696 | **169** | 715 |
| tooltip `$SP*`/`$AP*` literals (tier 6) | 132 | **34** | 1,414 |

The variation has one consistent shape — retail's **low-rank penalty, ramping then
plateauing** (110 of the 169 varying lines fit exactly): Frost Nova 0.018 → 0.043 →
0.193; Renew 0 → 0.291 → 0.376 then flat for ranks 3–14; Immolate 0.058 → 0.125 → 0.200
then flat for ranks 3–11.

**That shape is precisely what makes it dangerous:** the catalog stores **Rank 1** for
~697 entries, which is where the penalty is deepest.

Seven catalog entries are measurably affected today — both ranks state a coefficient and
the two disagree:

| card | catalog (R1) | level-60 rank | factor |
|---|---|---|---|
| Sun Down | SP 0.4 | SP 1.3 | **3.25×** |
| Grasp of Darkness | SP 0.5 / AP 0.3 | SP 1.4 / AP 0.975 | **2.8×** |
| Spore | AP 0.08 | AP 0.13 | 1.63× |
| Fulmination | SP 0.28 / AP 0.18 | SP 0.38 / AP 0.245 | 1.36× |
| Seismic Tremor | AP 0.15 | AP 0.2 | 1.33× |
| Bone Spear | SP/AP 0.05 | SP/AP 0.04–0.1 | shape changes |
| Spirit Charge | SP 0.2 | AP 0.2 | **term type changes** |

**Seven is a floor, not a total** — 547 affected entries state no coefficient in either
rank's text, so nothing can be compared for them.

### The number that was nearly 15

A first pass reported **15** differences. Eight of those were entries where the
*level-60* record's text yields no coefficient — which is not a difference. Three
distinct causes, all confirmed by reading the actual records:

1. a **compound form the regex cannot read** — `($SP+$AP)*0.36` (Bone Arrow); a known
   `text_extraction.py` gap, still open
2. the formula **moved into a sub-spell** — `$71791m1` (Deep Freeze)
3. the rank line pulled in a **different ability of the same name** — Blood Drinker's
   rank-4 record describes a Bloodthirst heal

These are now a separate verdict (`live_text_unresolved` / `catalog_text_unresolved`)
and are excluded from the headline. Cause 3 is worth noting on its own: it is the
duplicate-name trap surviving inside `dbc_spell_rank`'s line grouping.

### Evidence-tier caveat, stated because it is load-bearing

Neither source alone carries this claim. The **numeric** column is tier 4 but is *not*
the coefficient Ascension applies (§1). The **tooltip literals** *are* that coefficient
but are tier-6 text. They are reported separately, never merged into one number, and
they agree on direction.

**Consequence: `spell_scaling` needs rank keying.** Owner decision (2026-08-04) was
**record-and-flag here, migrate in T4** — session `1b` rebuilds the table anyway.

## 3. What shipped

```
core/spells/dbc_numeric.py     pure decoder: flat range, per-level, per-combo,
                               bonus_multiplier. Reads numeric fields ONLY
core/spells/rank_scaling.py    the rank study as reusable functions, not a one-off
core/db/schema.py              + PHASE1_NUMERIC_DDL (spell_effect_values)
ingest/dbc/resolve_numeric_formulas.py
                               the ingester + report. Idempotent, owns its deletes
cli/rebuild.py                 + one step, after load_extract.py
```

`spell_effect_values` is keyed `(spell_id, source_spell_id, effect_index)` because a
card's real magnitude frequently lives in a *different* spell record: `spell_id` is the
card the value is attributed to, `source_spell_id` is the record actually decoded, and
`via` says which (`self` / `hidden_ref`). Provenance is `NOT NULL` per §2.1, and
`evidence_ref` cites the DBC row and archive it came from.

Report: `data/derived/numeric_extraction_report.md`, regenerated every run.

### The flat convention, now validated on every run

`minimum = base_points + 1`, `maximum = base_points + die_sides`, checked against seven
magnitudes established **independently of the DBC** — Improved Cleave R1/R2/R3
(39/79/119 → 40/80/120%), Avenging Wrath (19 → 20%), Divine Storm (109 → 110%), Divine
Protection (−51 → −50%), Fel Infused Weapon 2H (14 → 15%). A client patch that changes
the convention now **fails the run** rather than silently rewriting every magnitude.

Also established: `base_points = -1` with `die_sides <= 1` is the DBC's **"no value"
sentinel**. The decoder returns `None`, never `0.0` — so nothing downstream can mistake
"unset" for "measured zero".

### Deliberately not done

* **`has_hidden_formula` is not cleared.** The flag means "the *export* cannot see this
  formula", which stays true regardless of what we resolved elsewhere. Clearing it is
  also the exact shape of the idempotency bug Phase 0 found three times — a flag that
  scopes the next run's targets, mutated by this run.
* **No SP/AP rows written to `spell_scaling`.** See §1.
* **No rank re-key.** Owner decision; T4's job.

## 4. Hammer from the Heavens — ✅ RESOLVED (mid-session, from owner-supplied sources)

> **This section was first written as "narrowed, not closed". The owner then supplied a
> live tooltip screenshot and the two db.ascension.gg pages, which closed it.** The
> original analysis is kept below the verdict because the *reasoning* is what generalises.

> ⚠ **CORRECTED after a `--with-dbc` re-extraction.** This section first said 74–97, on
> the theory that level scaling capped at 40. The client returned `MaxLevel = 0`
> (uncapped), falsifying it. The real explanation is below; **the figure is 122–145.**
> Two claims made here earlier are retracted in §4a.

**At level 60: `122 to 145` Holy damage, `+9.1%` Spell Power, `+9.1%` Attack Power, per
hit.** Radius 8 yards, instant. For Elric (AP 584 / SP 533): **224–247 per non-crit hit**,
averaging ~235.

Three independent sources:

| Source | Tier | What it gave |
|---|---|---|
| client DBC numeric fields | 4 | `base_points 1`, `die_sides 24`, `per_level 2.4`, `SpellLevel 10`, **`MaxLevel 0` (uncapped)** → `2+120` to `25+120` at level 60 |
| **db.ascension.gg** page for `282987` | 3 | *"School Damage: Value: 2 to 25, plus 2.4 per level"* — matches the numeric fields exactly; plus *"Scaling #1: +9.10% of spell power"* and *"Scaling #2: +9.10% of attack power"* |
| **live in-game tooltip** | 1 | `194 to 147` — whose arithmetic independently solves to level 60 (§4a) |

## 4a. Solving the tooltip — and two retractions

`$m1`/`$M1` render the **raw base points, unscaled** (2 and 25), exactly as db shows
them. The description then supplies the level scaling itself. Treating the two displayed
numbers as simultaneous equations, with `A` the shared `0.091×(AP+SP)` term:

```
min = (L-10)*2.4 +  2 + A = 194
max = (L-10)*1   + 25 + A = 147
      subtract:  (L-10)*1.4 - 23 = 47   ->   L = 60 exactly
      back-substitute:                        A = 72  ->  AP+SP = 791
```

`A` cancels on subtraction, so **the character's level falls out of a tooltip
independently of gear** — and it lands exactly on 60. That is what makes the model
credible rather than fitted.

**The bug is narrower than first described.** Scaling is applied *once*, not twice. The
minimum's `2.4`/level **matches** the effect's real `EffectRealPointsPerLevel` and is
correct; **the maximum's `1`/level is simply wrong.** At level 60 the tooltip should read
**194 to 217**; it shows 147.

### ❌ Retraction 1 — "the description double-applies level scaling"

It does not. `$m1`/`$M1` carry no scaling. A double application would render `242/195` —
**above** the observed minimum of 194, impossible since `A` cannot be negative.

### ❌ Retraction 2 — "level scaling caps at 40, so the flat is 74–97"

Falsified by the client: `MaxLevel = 0`. The 48-point gap that motivated the cap
hypothesis is entirely explained by `A = 72`.

### ❌ Retraction 3 — the pooled-parse argument was overconfident

I cited 17,972 crawled hits as ruling out a 122–145 flat, because implied non-crit
averages were 124–140. **That treated 12 crawled characters as if all were level 60.**
The crawl records no character level (Phase 0 T2), and this ability scales 2.4/level — a
level-40 character deals 74–97 for the same spell. With levels unknown and Holy taking
partial resistance, those figures cannot discriminate flat hypotheses at all.

**Generalised into primer §5:** pooled parse data cannot settle a magnitude that varies
with anything the crawl does not record — level, rank, or gear.

### 🚨 The best proof in the project of §1's finding

**`282987`'s `EffectBonusCoefficient` is all zero** — yet the ability demonstrably
scales at 9.1% SP and 9.1% AP. A numeric-fields-only reading of *coefficients* would
have concluded this spell has **no stat scaling at all**. Numeric fields own the flats;
they do not own Ascension's coefficients.

### ⚠ Composition: the build doc's assumption revised

`build_paladin-hammerdin.md` §10 assumed **30% SP / 30% AP / 40% flat**. It was **right
that SP and AP contribute equally** — the coefficients are identical at 0.091 — but
**understated how flat-dominated the ability is.** At Elric's stats the real split is
**~21 / 23 / 57**.

That is the direction §10's own caveat anticipated (*"if it's mostly flat, SP and AP
weights drop and spell crit's dominance grows further"*), so it **reinforces** the
existing gearing order rather than disturbing it. It also means this ability's 22.1%
damage share **decays as gear scales** and should be re-derived after a tier jump.

*(An earlier draft of this section said 26/26/46, computed from the retracted 74–97
flat.)*

### `max_level` added to the extractor — and what it actually found

`spell_dbc_raw` did not store `MaxLevel`, and without it a level-scaled magnitude cannot
be computed. Added to `build_dbc_index.py`, and the owner ran `--with-dbc` the same day.

**It returned `MaxLevel = 0` for `282987` — uncapped — which falsified the cap
hypothesis** (§4a, Retraction 2). Column alignment was verified independently: Holy
Supernova R6 reads `spell_level 60`, R1 reads `14`, cooldown 40,000 ms, all matching
known values.

The column earns its place regardless: **1,653 spells carry a real cap, and 196 of the
354 level-scaled catalog spells are capped.** T4 cannot compute a correct level-60 flat
for those without it.

## 5. Unrelated pre-existing bug, not fixed

`py cli/rebuild.py` **crashes when its output is piped or redirected**:
`build_index.py` prints a `⚠` and Python selects cp1252 for a non-console stdout →
`UnicodeEncodeError`, killing the chain at step 1. It works when run in a terminal,
which is why it has not been noticed. Workaround: `PYTHONIOENCODING=utf-8`.

Left alone as out of scope for `1x` — it is a one-line fix in a file this session had no
other reason to touch. Worth doing in `1b`.

---

## For `1b`

- **`spell_scaling` needs rank keying** — this session's main schema output. T4 rebuilds
  the table anyway; key it `(spell_id, term_type, rank, …)` and use
  `core.spells.ranks.rank_for_level()` for resolution.
- **Read a coefficient off `spell_effect_values`, never `bonus_multiplier`.** The
  coefficients Ascension applies are in tooltip text; the numeric field is a default
  multiplier 83% of the time.
- **`resolve_spell_mechanics()` should consume `spell_effect_values`** for flats,
  per-level and per-combo terms — that is what it was built for.
- **The trigger-chain gap (§4) is T5's `triggers` relation** and unlocks ~519 more
  spells' magnitudes.
- `core/spells/text_extraction.py`'s **compound-form gap** (`($SP+$AP)*0.36`,
  `$SPFR*0.0096`) is now costing real coverage, not just tidiness — it is why 8 rank
  comparisons could not be made.
