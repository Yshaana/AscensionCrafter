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

**At level 60: `74 to 97` Holy damage, `+9.1%` Spell Power, `+9.1%` Attack Power, per
hit.** Radius 8 yards, instant. For Elric (AP 584 / SP 533): **176–199 per non-crit hit.**

Three independent sources:

| Source | Tier | What it gave |
|---|---|---|
| client DBC numeric fields | 4 | `base_points 1`, `die_sides 24`, `per_level 2.4`, `base_level 10` → unscaled 2–25 plus 2.4/level |
| **db.ascension.gg** page for `282987` | 3 | *"School Damage: Value: 2 to 25, plus 2.4 per level"* — matches the numeric fields exactly; plus *"Scaling #1: +9.10% of spell power"* and *"Scaling #2: +9.10% of attack power"* |
| **live in-game tooltip** | 1 | `194 to 147` — which pins the level cap (below) |

**The level scaling caps at level 40.** db renders `$m1`/`$M1` **unscaled** (literally
`+2` and `+25` in its tooltip text); the client renders them **scaled**; the gap is
exactly **72 = (40−10)×2.4** on both ends. So the level-60 roll is `2+72` to `25+72`,
not the uncapped 122–145.

### 🚨 The best proof in the project of §1's finding

**`282987`'s `EffectBonusCoefficient` is all zero** — yet the ability demonstrably
scales at 9.1% SP and 9.1% AP. A numeric-fields-only reading of *coefficients* would
have concluded this spell has **no stat scaling at all**. Numeric fields own the flats;
they do not own Ascension's coefficients.

### ✅ Correction to a claim made earlier in this same session

An earlier draft said the build doc's assumed **30% SP / 30% AP / 40% flat** composition
was *"wrong in shape."* **It is not.** That assumption already had SP and AP equal, which
is exactly what the two Scaling rows confirm. At Elric's stats the real split is
**26 / 26 / 46** — close, and now confirmed rather than overturned. The §10 stat weights
resting on it stand.

### Why the tooltip is inverted — the generalisable part

The description **double-applies level scaling**: once inside `$m1`/`$M1`, then again as
explicit `($PL-10)*2.4` on the minimum and `($PL-10)*1` on the maximum. **The rates
differ**, so the minimum grows 2.4× faster than the maximum and overtakes it above
roughly level 29.

The engine does **not** evaluate those text terms. Confirmed against **17,972 pooled
hits** from 12 characters in the 2026-08-04 crawl: implied non-crit damage is 124–140 on
the two largest samples (Zyzz 4,310 hits, Kieceblower 2,860), which is **below the
tooltip's own stated minimum of 194** — and below the uncapped flat term before any
spell power at all, which would require negative SP.

**Rule worth carrying: a rendered tooltip number can be arithmetically impossible.**
Treat the displayed range as text, not as a measurement.

### `max_level` added to the extractor

`spell_dbc_raw` did not store `MaxLevel`, and without it a level-scaled magnitude cannot
be computed — this spell is why. The column is added to `build_dbc_index.py`; it stays
**NULL until the next `--with-dbc` run**, since only the client has it.

---

### Original analysis, kept for the reasoning

`build_paladin-hammerdin.md` §12 item 2 calls sub-spell `282987` *"the largest
uncertainty in the stat weights"* (22.1% of damage). It **is** in `spell_dbc_raw`:

```
SchoolMask 2 (Holy) · Effect[0] = 2 (school damage)
EffectBasePoints [1, 0, -1] · EffectDieSides [24, 1, 1]
EffectRealPointsPerLevel [2.4, 0, 0] · EffectBonusCoefficient ALL ZERO
```

So the flat term is a numeric-field fact (`$m1 = 2`, `$M1 = 25`, 2.4/level) while the
SP/AP coefficients exist **only as text** — `$AP*0.091` and `$SP*0.091`, equal to each
other. Another instance of §1.

🛑 **The flat term is NOT settled and no number should be published from it.** The
description's own formula is `${(($PL-10)*2.4+$m1)+…}` to `${(($PL-10)*1+$M1)+…}`, which
evaluated literally at level 60 gives a **minimum of 122 and a maximum of 75** — an
inverted range. Either the macro semantics differ from the literal reading (likely:
`$m1`/`$M1` may already include per-level scaling) or the text is stale. **Needs a
tier-1 in-game tooltip read at level 60.**

What *did* change: the build doc's assumed **30% SP / 30% AP / 40% flat** composition is
wrong in shape — the SP and AP coefficients are **equal**, at 0.091 each.

### Attribution gap found in the same check

`282987` is reached from a card by **`EffectTriggerSpell`** (Hour of Judgement `282986`
triggers it), **not** by a tooltip `hidden_ref` — so this session's extractor never
attributed it to a catalog card. **529 such catalog → out-of-catalog trigger links
exist, across 519 distinct targets.**

Following them is `PHASE_1` **T5's `triggers` relation**, and it was deliberately not
built here: multi-hop chains need cycle handling and an attribution semantics decision,
and T5 already owns the relation type. **`1b` should pick this up** — it is the next
sizeable block of unresolved magnitudes after this session's 794.

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
