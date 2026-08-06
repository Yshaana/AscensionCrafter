# PLAN 3C — reaching the Phase 3 exit *cleanly*

> **`HISTORICAL`** — the record of a past session or a completed phase. Immutable. It **may contain claims that are false today**, and that is correct rather than a defect — it records what was believed at the time. **Never citable as current truth.** *(Classified `3f` F8c, 2026-08-07.)*

**Written 2026-08-06**, immediately after the audit-gated coefficient ingest
(`79c6568`). Supersedes nothing; it is the work plan for the exit rider stamped
that day in `predictions/CALIBRATION_TOLERANCE.md`.

Current position: **5 of 41 within ±20%, 2 qualified → EXIT NOT MET.**

> 🔤 **NAMING — read this before citing a task number from this file.**
> This document's tasks are **`C1`…`C13`**, renamed in session `3d` (Block B1)
> from the old `T`-numbering. Reason: **all eight of its numbers 1–8 collided**
> with `PHASE_3_builds_repo.md`'s own task numbers, with `PHASE_2` a third space
> — so one token meant *the capture addon*, *pets*, and *three sim tiers*
> depending on which file the reader had open. `AUDIT_3C_handoff.md` collided
> with **itself**, same three tokens carrying six meanings 135 lines apart.
>
> | # | this file — `C<n>` | `PHASE_3_builds_repo.md` — `T<n>` |
> |---|---|---|
> | 1 | slice accuracy | normalise the crawl |
> | 2 | log admissibility *(closed)* | pooled mechanics inference |
> | 3 | fix over-predictions | search and analysis |
> | 4 | trigger-edge reachability | gear data |
> | 5 | pets | the capture addon |
> | 6 | conversion mechanics | combat-log ingestion |
> | 7 | class-A reachability | session-start automation |
> | 8 | re-run and report | refine the crawler |
>
> **A `T`-prefixed task number anywhere in this file is now a bug** — including
> in prose that merely quotes the old names, which is why this note does not use
> them. `grep -n "\bT[0-9]" primer/PLAN_3C_clean_exit.md` must return **nothing**;
> that is one of `3d`'s exit criteria. To refer to another document's task, name
> the document and the task in words rather than pasting its bare number here.

---

---

# 🔄 REVISION 2026-08-06 (evening) — after the paired upload and the calibration

The plan below was written before the owner uploaded four of his own logs
(reports 104–107) and before the verified-input calibration. Both landed the
same day. **Read this section first; where it differs from the original tasks,
this wins.** Session records: `Session_2026-08-06_3c_paired_upload.md`,
`predictions/calib_2026-08-06_3c_verified_inputs.md`.

## What closed

* **C2 is CLOSED as a dead end**, with a negative result worth as much as a fix:
  no admissibility filter is constructible from the crawl API. `deaths` does not
  exist in the payload at all, and four candidate discriminators were tested and
  rejected (wipes, raw DPS, absolute APM, within-character APM). **The corpus
  retains an unknown number of death-deflated parses we cannot identify.** That
  is now a stated limitation of the gate.

## ❌ What I got wrong, and it changes C3

The original C3 said over-predictions are *"unambiguous bugs — the sim asserts
damage that provably did not happen"*, and named **Boomcat (82% coverage) the
single best clean-qualifier candidate anywhere in the gate.**

**Retracted.** Report 104 established a *second* cause of over-prediction that is
not a bug at all: a **death-deflated parse**. Elric died 6.1s into the 34.0s
Fairbanks fight and the site reports 481 DPS against his 3,473 on Mograine —
a 7.2× deflation, `deaths` NULL, `validation_status: valid`. Against that
character the sim would "over-predict" by ~7×, and nothing is wrong with the sim.

**Boomcat's within-character APM ratio is 0.24** (17.1 against its own median
72.5). Elric's *known* death case sits at **0.38**. Boomcat looks like the same
signature, not a fixable bug — so it is probably **not** a qualifier candidate at
all, and C3's expected yield is materially lower than the original text claims.

✅ **Mutaforma remains a genuine bug** — APM ratio 0.99, entirely normal activity,
+3,619%. It is the one over-predictor confirmed to be ours.

## 🚨 The strategic consequence

C2's dead end plus C3's weakening means **the crawl cohort may not be able to
deliver a clean exit on its own**: we cannot separate a model error from an
invalid parse for any given candidate. Pushing harder on the 41 does not fix
that.

**The route through it is Elric.** He is now in the corpus (`character_id
39772`) with **11 valid non-trash boss encounters**, and — uniquely — inputs we
have *verified* rather than inferred. Any residual on him is unambiguously the
model's. So:

> **Use Elric to fix the MODEL, then let the corrected model lift the cohort.**
> That is a cleaner dependency order than the original plan's, which tried to fix
> the cohort directly while its inputs were unverifiable.

⚠ **Elric cannot satisfy the exit himself** — PHASE_2 §8.2 says ≥3 real
*characters*, and 11 encounters on one character is not that. He is an
instrument, not a candidate for the count.

## Revised task list

| # | task | status / change |
|---|---|---|
| **C1** | report slice accuracy | unchanged, still pending, still approved |
| ~~C2~~ | log admissibility | **CLOSED — dead end, documented** |
| **C3** | fix over-predictions | **narrowed to Mutaforma**; the rest may be undetectable bad parses |
| **C4** | 43 abilities with a trigger edge (687 pts) | unchanged |
| **C5** | pets (440 pts) | unchanged |
| **C6** | conversion mechanics | 🔼 **PROMOTED to first** — see below |
| **C7** | 54 with magnitude, no edge (1303 pts) | unchanged, still last and still risky |
| 🆕 **C9** | the ~4.5× out-of-catalog cluster | **new, possibly the biggest lever** |
| 🆕 **C10** | controlled before/after on the periodic-component change | **new, blocks C9's interpretation** |
| 🆕 **C11** | make Elric a gate-grade instrument | **new** |
| 🆕 **C12** | review the 177 export-vs-scraped coefficient conflicts | **new** |
| 🆕 **C13** | fix `calibrate_vs_log.py`'s wrong defaults | **new, small, urgent** |

### C6 — promoted to first work item

Two independent measurements now agree it is the largest *named* gap:
* the calibration reads Righteous Vengeance at **228×** (base 1 vs logged 228) —
  base 1 is the site's nominal `Value: 1`, i.e. there is no coefficient to find;
* the buffed/unbuffed pair measures it at **×3.18 per hit**, the largest buff
  response of any ability, because buffed crits are both bigger and more frequent
  and RV converts crit damage.

It needs **no data**, it affects 9 of the 41 gate characters, and Ignite and
Deep Wounds are the same shape. Nothing else on the list has this
evidence-to-cost ratio.

### 🆕 C9 — the ~4.5× out-of-catalog cluster

Five out-of-catalog spells on Elric land within a **±4% band** against base:
Righteous Smite 4.67×, Holy Shock 4.52×, PBL Consecration 4.46×, Judgement of
Command 4.35×, Arcing Light 4.33×. Five independent spells agreeing that tightly
is **one mechanism, not five bugs**.

**Why it may be the biggest lever:** every one of the 88 demand-ranked unmodelled
abilities in the crawl cohort is **also out-of-catalog**. If a single systematic
factor explains Elric's cluster, it plausibly reaches the cohort's accuracy
problem too — the half of the miss that coverage work cannot touch.

🛑 **Blocked on C10, and do not fit it.** Candidate mechanisms to test *before*
proposing a number: a missing rank redirect (out-of-catalog spells have no rank
line), unapplied level scaling, or a school-scoped amplifier. Back-solving 4.5
and seeding it is exactly what `2e` refused to do with the Holy residual.

### 🆕 C10 — the controlled before/after (blocks C9)

This session changed how periodic coefficients route: a scraped row stating
`periodic` now attaches to the periodic event instead of the direct one. PBL
Consecration is affected. **So the cluster above cannot be compared with `2e`'s
2.2× figures** — different measurement (`logged/base` vs `logged/modelled`) *and*
a changed model in between. Re-run both configurations on identical inputs before
anyone quotes a movement.

### 🆕 C11 — make Elric a gate-grade instrument

He has 11 valid boss encounters and **zero snapshots** — no gear, no cards,
`snapshot_id` NULL — so the gate cannot sim him. But his ALC `CI` record carries
**18 gear pieces (item_id + enchant + gems) and the full `hero_build`
(entry_id + rank)** inline, plus a same-session stat export.

Build a `character_snapshots` row from the ALC capture, tagged with its own
provenance (`source='alc_capture'`, never mixed with `crawl_resolved_bisbeard`).
That yields the project's first character where **input error is zero by
construction**, so every residual is model error — which is the instrument the
whole calibration effort has been missing.

### 🆕 C12 — review the coefficient conflicts

177 spells now have `export_tooltip` and the scrape stating **different**
coefficients (Mongoose Bite 0.20 vs 0.45; Holy Wrath 0.15 vs 0.07). Precedence
currently prefers the scrape, on the grounds that it states the *applied* value,
carries an enforced check digit, and the catalog stores the wrong rank for ~half
of multi-rank cards. **That is a judgement call, and it is now load-bearing on
177 abilities.** Sample and check some against a third source.
⚠ Includes the live conflict on Holy Shock (25902): measured-provisional **0.40**
vs scraped **0.214**, ~2× apart, currently won by the provisional.

### 🆕 C13 — fix the calibration tool's defaults (do this first, it is 10 minutes)

`calibrate_vs_log.py` defaults to **AP 584 / SP 533 / weapon 585–669** — the
Duality-era block from the 2026-08-03 build doc. Those are wrong for every
Path-of-Intelligence log, and they change conclusions silently: Hammer from the
Heavens reads **1.26×** on the defaults and **1.45×** on the real block. Either
require the stat block explicitly or read it from a named capture; never default
to a stale one.

---

## 0. What is fixed and must not move

These are the constraints the plan is written *inside*. Every one of them exists
because this project has previously been burned by the alternative.

1. **The ±20% pass definition does not change.** Not widened, not tightened.
2. **The ≥50% coverage rider does not change.** It was stamped before the run it
   judges. §1 below derives that ~80% coverage is what a *truthful* model needs
   to land inside ±20% — that is knowledge obtained **after** the rider was set,
   and it must not be allowed to edit it. It is a floor, not the target.
3. **Nothing is closed by fitting a constant.** Every layer so far (buffs,
   coefficients) was built-and-measured, and its measured insufficiency was the
   finding. That stays true.
4. **No id is related to another by name or by numeric proximity.** `287860` vs
   `287865` is the live temptation and it is exactly what rule 5 forbids.
5. **Candidates are never excluded because they failed.** C2 touches candidate
   quality, and it is the single most dangerous task here; its guard rails are
   written into the task itself.

---

## 1. The diagnosis this plan is built on

The miss decomposes into **two** independent quantities, and the project has
only been tracking one.

* **coverage** — the share of a character's real damage the sim can model at all
* **slice accuracy** — whether the abilities it *does* model produce the right
  number: `(100 + delta_pct) / coverage_pct`

| char | coverage | delta | if slice were perfect | slice accuracy |
|---|---:|---:|---:|---:|
| Boomcat | 82% | +630% | −18% | **888%** |
| Qtgamora | 69% | −55% | −31% | 64% |
| Ryno | 69% | −68% | −31% | 47% |
| **Malo** ✅ | 62% | −18% | −38% | **131%** |
| Nodding | 58% | −64% | −42% | 63% |
| Ikkura | 58% | −76% | −42% | 41% |
| **Ari** ✅ | 58% | −10% | −42% | **156%** |
| Shana | 56% | −79% | −44% | 38% |
| Blix | 53% | −73% | −47% | 51% |
| Iwannakissms | 52% | −87% | −48% | 24% |
| Billyeye | 51% | −46% | −49% | **107%** |

### Three consequences, and they set the whole plan

**(a) Both current qualifiers pass by over-production.** Ari models 58% of its
damage and produces 156% of what that slice should; the excess cancels the
missing 42%. Malo is the same at 131%. The rider caught the worst compensating
error (Chastie 5%, Zaczao 6%, Xoller 13%) but not this milder form.

**(b) Fixing accuracy alone LOSES both qualifiers.** Ari at an honest 100% slice
accuracy and 58% coverage lands at −42% — outside tolerance. **Coverage and
accuracy have to move together**, which is why this plan refuses to sequence all
of one before the other.

**(c) The arithmetic sets the real target.** To sit inside ±20% with a truthful
model you need **~80% coverage**. One character is there today (Boomcat, 82%) and
it is an over-prediction bug. ⚠ This is a *description of what clean looks like*,
**not** a new criterion — see constraint 0.2.

### Where the unmodelled damage actually is

Classified by *why the sim cannot reach it*, summed share-points across the
cohort:

| class | abilities | share-pts | owner |
|---|---:|---:|---|
| out-of-catalog, **no edge**, has a magnitude | 54 | 1303 | C7 |
| out-of-catalog, **has an edge**, still unmodelled | 43 | 687 | C4 |
| pets | 14 | 440 | C5 |
| no edge **and** no magnitude | 5 | 112 | — genuinely missing data |

**Only 112 share-points is a data-acquisition problem.** The rest is routing,
and it is our code. This is why the coefficient ingest moved accuracy but not
coverage, and it is the standing correction to the expectation that it would.

---

## 2. Tasks

Each task states what would **falsify** it, so a task that turns out to be
solving a non-problem gets abandoned rather than completed.

### C1 — Report slice accuracy as a diagnostic *(owner approved 2026-08-06)*

**Do:** compute `slice_accuracy = (100 + delta_pct) / coverage_pct * 100` per
character; emit in `calibration_crawled.md` and `.json` beside delta and
coverage.

**Why:** it is the metric that distinguishes *converging* from *cancelling*.
Billyeye (107%, 51% coverage) is the most honest model in the cohort and
currently reads as a plain failure; Ari (156%) reads as a pass.

🛑 **A DIAGNOSTIC, NOT A GATE CONDITION.** Do not add it to the exit. The exit is
±20% + the ≥50% rider, full stop.

**Verify:** Ari 156%, Malo 131%, Billyeye 107%, Boomcat 888% reproduce.

---

### C2 — Log admissibility: which parses are valid calibration candidates?

**Owner question, 2026-08-06:** *should we identify and dismiss certain logs — bad
captures, a player present for only part of the fight, deaths, disconnects?*
**Yes, and today we have almost no rule at all.** Here is what was measured.

#### C2a — What the corpus can and cannot currently detect

| failure case | detectable today? |
|---|---|
| wipe / kill | ✅ `encounters.success` (3,527 wipes / 1,928 kills) |
| fight duration | ✅ `encounters.duration_seconds` |
| cast activity | 🟡 `ability_performance.casts` — **but see C2c, it undercounts** |
| site's own validation | 🟡 `validation_status` — NULL on **3,655 of 5,455** |
| **character died** | ❌ `encounter_performance.deaths` — **0 of 19,649 populated** |
| **ranking context** | ❌ `percentile` — 0 of 19,649 populated |
| **partial presence / active span** | ❌ not captured in any form |
| **disconnect / late join** | ❌ not captured in any form |

🚨 **`deaths` is a declared column that nothing ever writes**, and the crawler
does not mention the field anywhere. A column that looks like data and is
uniformly empty is the same silent-gap class this project keeps finding. The
per-ability endpoints are **aggregated with no timestamps**, so a character's
active span cannot be reconstructed from what we hold — **this is a capture fix,
not an analysis fix.**

#### C2b — Wipes are NOT a disqualifier (hypothesis tested and rejected)

The obvious rule — "drop the wipes" — is wrong. Wipes are **more** common among
the well-predicted characters (**20 of 33**) than among the over-predictors
(**2 of 8**). Do not filter on `success`.

#### C2c — APM: anchored against the owner's own parses

The owner's dummy logs give a ground-truth anchor for a *known-active* player,
measured with `tools/log_parser` named fields:

| log | casts | span | **APM** |
|---|---:|---:|---:|
| `2026-08-05-22.42.20` | 263 | 276s | **57.3** |
| `2026-08-05-23.10.44` | 281 | 295s | **57.1** |

**Two independent logs agreeing to 0.3%** — a solid anchor. Composition confirms
build doc §11: Lightbound Cleave leads at 16.5/min, the median inter-cast gap is
**1.09s** — *below* the 1.5s GCD — and 113 of 280 gaps are under 1s, because LC
is queued off-GCD. A pure-GCD rotation would cap near 40 APM; this kit exceeds it
legitimately.

⚠ **Two reasons this anchor cannot simply become the threshold:**

1. **It is an upper bound, not a typical value.** A stationary dummy parse has no
   movement, no mechanics, no target swaps. Real raid APM is lower for the same
   player and the same build.
2. 🚨 **The crawl's `casts` is not the same measurement, and the difference is
   BUILD-CORRELATED.** The site reports `casts = 0` for proc- and DoT-delivered
   damage (worked case: Immolation, `casts=0` with `hits=47`). So crawl
   casts/sec is a **lower bound on true APM, and it under-reads proc-heavy kits
   specifically.** The live counter-example is **Qt: 0.11 casts/sec while logging
   9,310 DPS** — plainly not an inactive player.

   **Therefore a casts/sec filter would systematically discard proc/DoT builds** —
   the same corpus-biasing failure as not modelling pets
   (`sim_models_no_pets_10pct_of_damage`), which is a thing this project has
   already decided is unacceptable. **Do not filter on crawl casts/sec.**

For reference, on that (biased) measure the cohort median is ~0.6 casts/sec and
7 of the 8 over-predictors sit at 0.11–0.41. **Mutaforma is the exception at
1.11 — high activity, so its +3,619% is a genuine sim bug**, which is consistent
with `sim_magnitude_explosion_absolute_zero` and belongs to C3.

> 🛑 **THE SECTION BELOW IS RETRACTED — marked in `3f` F8, not rewritten. And
> the section ABOVE it, which it withdrew, was RIGHT.**
>
> `3c` measured the site's `casts` against `SPELL_CAST_SUCCESS` at 93% and
> 97.3% and on that basis withdrew its own objection that `casts` under-reads
> proc-heavy kits. **Both measurements were taken on an all-instant Hammerdin,
> where they are correct and do not generalise.** The 2026-08-06 Frost Mage
> capture falsifies the generalisation: `SPELL_CAST_SUCCESS` and
> `SPELL_CAST_START` are **disjoint by cast type** — instants log `SUCCESS` and
> never `START`, cast-time spells log `START` and never `SUCCESS`. **Frostbolt
> was cast 74 times and produced ZERO `SPELL_CAST_SUCCESS` events** while
> landing 52 non-crit hits. Measured across the cohort it fails for **22 of
> 41** members.
>
> ⚠ So *"crawl `casts`/sec is a lower bound on true APM, and it under-reads"*
> — the paragraph immediately above, which this section retracted — **stands**,
> for a second and independent reason: not only proc/DoT delivery, but every
> cast-time spell in the rotation. **Do not filter on crawl casts/sec** is
> still the operative instruction, and it is now better supported than when it
> was written.
>
> Detail: `data/source/captures/2026-08-06_elric_mage_frost/README.md` and
> `primer/FINDINGS_mage_capture_2026-08-06.md` §1. Kept as the record of what
> was believed at the time.

#### ✅ C2 RESOLVED 2026-08-06 by the paired upload (reports 104 + 105)

The owner uploaded two of his own logs, giving the same encounters measured
twice — locally at ground truth and through the API. Four results, and they
change C2's conclusions in both directions.

**1. ✅ The site's `casts` IS `SPELL_CAST_SUCCESS`. C2c's worry is RETRACTED.**

| report | content | site casts | log casts | agreement |
|---|---|---:|---:|---:|
| 104 | Scarlet Monastery, Whitemane | 54 | 58 | 93% |
| 105 | Uldaman, 7 bosses | 257 | 250 | **97.3%** |

Per-ability on Whitemane it matches **exactly** on Dawn Strike (12), Dawnreaver
(9), Holy Finish (2), Judgement of Wisdom (5), Light's Hammer (1), Lightbound
Cleave (22) and Whirling Light (2). On Uldaman the site reads consistently +1 per
encounter (a pull-boundary cast). **Crawl casts/sec is a faithful APM measure at
the character level** — the `casts=0` proc rows are real (those are not casts)
and do not corrupt the total. The earlier "it would bias against proc builds"
objection was wrong at this level and is withdrawn.

**2. 🛑 `deaths` is NOT OBTAINABLE. This is a dead end, not a crawler bug.**
Searched the full API payload for a report we control: **no death-like key and
no presence/active-time key exists anywhere.** So `encounter_performance.deaths`
(0 of 19,649) can never be filled from this source. ⚠ A permanently-NULL column
that looks fillable is the trap this project keeps finding — it should be
documented as unavailable rather than left looking like a capture gap.

**3. 🚨 The death failure mode is REAL, LARGE, and INVISIBLE — now with ground
truth.** Elric died **6.1s into the 34.0s Fairbanks encounter** and was dead for
**82%** of it (log 20:42:05.525 local; site window 19:41:59.392–19:42:33.391Z,
aligned to 99ms at UTC+1). The site reports him at **481 DPS against 3,473 on
Mograine — a 7.2× deflation — with `deaths` NULL and `validation_status:
'valid'`.** A character in that state entering the gate presents as a massive sim
**over-prediction**, which is precisely the Boomcat / Jamppa / Frediib signature.

**4. ❌ But APM cannot be the filter.** It *does* catch this case — Elric's
Fairbanks APM is 14.1 against 37–43 elsewhere (ratio **0.38**). Applied across
the cohort as a within-character rule (gate-encounter APM < 50% of that
character's own median over other timed encounters), it flags **13 of 41** —
and the 13 include **Malo, one of only two qualified characters**, plus Chastie.
Meanwhile it **misses** Mutaforma (ratio 0.99), Jamppa (0.90), Candle (1.05) and
Striker (0.55). Catching 4 of 8 over-predictors at the cost of a qualifier is not
a discriminator.

> **C2 verdict: no reliable admissibility filter is constructible from the crawl
> API.** The one signal that would work is not exposed. Four candidates have now
> been tested and rejected — wipes, raw DPS, absolute APM, within-character APM.
> **Nothing is filtered.** The corpus contains an unknown number of
> death-deflated parses we cannot identify, and that is a stated limitation of
> the gate rather than something to paper over.

**5. ✅ Mutaforma is confirmed a genuine sim bug**, not a bad parse — normal
activity (APM ratio 0.99) with a +3,619% delta. It belongs entirely to C3.

**Follow-ups this opens (not blocking):**
* `damage_taken_rows` may permit *inferring* a death from a killing blow — the
  only remaining route to presence, worth one session's check.
* The owner can upload logs, and logs **do** carry `UNIT_DIED`. That is ground
  truth for any character we hold a log for, but it does not scale to 4,000
  crawled characters.

#### C2d — What to actually do

1. **Report** wipe status, duration, casts/sec and C1's slice accuracy per
   candidate. Filter on none of them yet.
2. **Fix the capture gap** — the highest-value item here. Populate `deaths`, and
   check the armory/report endpoints for an active-time or presence field. This
   is the one signal that cleanly separates "died 20s into a 90s fight" (a
   capture artifact, legitimately dismissible) from "played badly" (a real parse
   that must stay in).
3. **Only then** propose an admissibility rule, on **presence**, never on
   performance.

🛑 **THE DANGEROUS TASK — guard rails.** Excluding candidates because they failed
is gate-gaming. A rule is admissible **only** if all four hold:
* it keys on **presence/validity** (died, disconnected, partial capture), never
  on how well the sim did or on raw DPS;
* it is applied to the **whole cohort**, including current passers — expect it to
  remove some;
* it is written into `CALIBRATION_TOLERANCE.md` with its date and reason
  **before** the re-run it affects;
* removed candidates are **listed by name**. An exclusion is a debt, not a pass —
  the rule `calibrate_vs_log.py`'s `KNOWN_BROKEN` already follows.

**Open check:** the owner's character is **not in the crawl** (dummy parses are
not uploaded as reports), so the site's `casts` field has never been validated
against log ground truth. If he ever parses a real logged encounter, that
comparison is free and would settle C2c's measurement-mismatch question.

---

### C3 — Fix the over-predictions that survive C2

**Do:** for each character still over-predicting after C2, name the mechanism.
Known starting point: **Mutaforma +3,619%**, driven by Absolute Zero (`285148`)
whose periodic component is *attributed* from trigger target `285149` at
`confidence=inferred` — open question `sim_magnitude_explosion_absolute_zero`.
One attributed magnitude producing ~30× a real parse is a resolution error
(wrong rank, wrong per-level scaling, or a periodic tick misread as
per-tick-per-target).

**Also do:** add a **sanity warning** (not a silent cap) when an attributed
magnitude implies a per-event value wildly out of line with its own source
spell's decoded flat. The bounded walk already refuses ambiguity; it does not yet
refuse absurdity.

**Why first among the fixes:** an over-prediction is an unambiguous bug — the sim
asserts damage that provably did not occur — and needs no new data. Boomcat is
the **highest-coverage character in the cohort (82%)** and therefore the single
best clean-qualifier candidate anywhere in the gate.

**Verify:** no character over-predicts by >100% without a named, recorded
mechanism.

---

### C4 — Reachability, class B: 43 abilities that *have* a trigger edge (687 pts)

**Do:** instrument `attribute_trigger_magnitudes` to record, per rejected target,
*which* rule rejected it. The rules are: depth > 2, multi-path
(`ambiguous_skipped`), target is itself a catalog card, or the card already has
that magnitude source. Then decide per reason — several are conservative
defaults from `1b` that were never revisited against measured demand.

**Why before C7:** these already have an edge, so the graph knows the
relationship. Nothing new has to be *inferred* — our own bounded-walk rule is
declining to use what we hold. Cheapest structural coverage available, and it is
entirely our code.

**Verify:** `ambiguous_skipped` falls; coverage rises on named characters; the
`282987` Hammer-from-the-Heavens validation in `cli/relationships.py` still
passes (it is the regression guard for this walk).

**Falsified if:** the rejections turn out to be correct — i.e. attributing them
would double-count. Then record that and move the 687 points to C7's problem.

---

### C5 — Model pets (440 pts) *(owner decision 2026-08-06)*

**Do:** `ability_performance.is_pet` already separates the damage; pet abilities
resolve like any other spell. The open work is the **APL/uptime model for a pet**,
not the magnitudes.

**Why it matters beyond the points:** pets are 10% of cohort damage scored as
zero, which does not merely understate pet builds — it **biases the corpus**, so
such a character can never pass honestly and the gate quietly selects for petless
kits. Open question `sim_models_no_pets_10pct_of_damage`.

**Verify:** Firebolt (`11763`, 101 pts) and Firebolt/Wild Imp (`413112`, 65 pts)
produce damage; the pet-carrying characters' coverage rises.

---

### C6 — Damage-conversion mechanics (≈150+ pts, no data needed)

**Do:** express "X% of another event's damage, redelivered as a periodic".
Righteous Vengeance (`61840`, 88 pts, 9 characters), Ignite (`12654`, 61 pts),
Deep Wounds (`12721`).

**Why it is not a coefficient problem:** we have held the RV mechanic as a
confirmed fact since build doc v5 (30% of a crit's damage as an 8s Holy DoT,
pools on refresh, cannot crit). db.ascension.gg confirms there is nothing to
scrape — the page states a nominal `Value: 1` with no Scaling lines, because the
magnitude is a **conversion**, not a function of a stat. Ignite decoding to
no-flat *confirms* the diagnosis; it is expected, not a bug.

**Verify:** RV appears as modelled damage for the 9 gate characters carrying it,
at ~30% of their own crit damage — a prediction the model makes with no fitted
input, checkable per character.

---

### C7 — Reachability, class A: 54 with a magnitude but no edge (1303 pts)

**The largest single block, and the riskiest.** Sequence it last; it likely needs
its own session.

**The worked case:** the log reports Devour Mind damage under `287865`; the sim
presses catalog card `285133`, whose walk reaches sibling `287860`. The two hold
**identical decoded magnitudes and identical scraped coefficients**
(SP 0.08 / AP 0.055). Only `287860` has a trigger edge.

**Do:** find a **mechanical** basis for the join. Candidate routes, in order of
defensibility:
1. `dbc_spell_rank` line membership — the two ids may be rank siblings, which is
   an existing, validated relation;
2. mechanical fingerprint — `SpellClassSet` + `SpellClassMask` + effect structure
   (the strict fingerprint set, `1a`);
3. an explicit mapping for known engine indirections — the **seal → judgement**
   case is already understood (`20467`, `2d`: the seal selects the judgement
   spell, so pressed card ≠ damaging id) and `25902` (Holy Shock's damage
   sub-spell) is in the same bucket and already carries a seeded coefficient.

🛑 **Never by name. Never by numeric proximity.** `287860`/`287865` differ by 5
and that is not evidence of anything. If no mechanical basis is found, the
correct outcome is to **record that and leave the damage unmodelled** — an
honest coverage gap beats a fabricated join.

**Verify:** each new route reproduces a case we already know independently
(seal→judgement on the owner's own logs is the natural regression test).

---

### C8 — Re-run, report, and read it against the rider

**Do:** `py tools/audit/calibrate_crawled.py --limit 120 --max-lag-hours 0`.
Report within-±20%, qualified, and the C1 slice accuracy together.

---

## 3. Sequencing and the expected trajectory

```
C1 ─┐
C2 ─┴─> C3 ──┐
C4 ──────────┼──> C8 (re-run)
C5 ──────────┤
C6 ──────────┘
C7 ─────────────> C8 (likely a later session)
```

C1/C2 are pure instrumentation and gate nothing. C3 depends on C2's answer. C4,
C5 and C6 are independent of each other and can land in any order.

### 🛑 Expect the pass count to DROP before it rises

Chastie, Zaczao and Xoller pass only because a 5–13% modelled slice massively
over-produces. C3 removes exactly that, and C4/C5/C6 add the damage that made
their over-production look correct. **Losing them is the rider working, not a
regression** — and it should be reported that way rather than as a setback.

The pool is there: **11 characters already have ≥50% coverage.** The exit needs 3
of them inside ±20%; 2 are. The best clean-qualifier candidates are the ones with
high coverage *and* a high logged DPS (i.e. a real DPS attempt):

| candidate | coverage | slice accuracy | logged DPS | what it needs |
|---|---:|---:|---:|---|
| Billyeye | 51% | **107%** | 3,795 | coverage only — the model is already honest |
| Qtgamora | 69% | 64% | 7,006 | modest coverage + accuracy |
| Ryno | 69% | 47% | 11,948 | accuracy on the modelled slice |
| Boomcat | 82% | 888% | 482 | C2 verdict first, then C3 |

**Billyeye is the single cleanest target in the cohort** and is not currently
visible as such, which is the argument for C1 on its own.

---

## 4. What could make this fail

* **C2 goes the wrong way.** If activity does not separate the over-predictors,
  the criterion stays untouched and C3 grows. That is a fine outcome; it is
  written as a falsification precisely so it cannot quietly become an excuse to
  drop candidates.
* **C7 finds no mechanical join.** 1303 share-points stay unmodelled and the
  ~80% coverage that a truthful pass needs may be unreachable for most of the
  cohort. If that happens, the honest report is *"the exit is not currently
  reachable and here is why"* — **not** a relaxed rider.
* **Slice accuracy converges on something ≠ 100% across the board.** If the
  well-covered characters all settle at, say, 60%, that is a systematic
  under-production — a missing global multiplier — and it must be *found*, not
  fitted. Same rule as `2c`'s demoted 1.31 and `2e`'s deliberately-unseeded Holy
  residual.

---

## 5. Owner asks in this plan

Only one, and it is not blocking:

* **C2's filter, if activity separates cleanly.** Introducing a candidate-quality
  threshold changes what the gate is measured *over*, and that is your call, not
  mine. I will bring the measured separation and a proposed principle-based
  threshold; the decision to apply it is yours, and it gets written into
  `CALIBRATION_TOLERANCE.md` before any re-run that it affects.

Everything else in C1 and C3–C8 is ordinary work needing no decision.
