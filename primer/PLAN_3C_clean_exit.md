# PLAN 3C — reaching the Phase 3 exit *cleanly*

**Written 2026-08-06**, immediately after the audit-gated coefficient ingest
(`79c6568`). Supersedes nothing; it is the work plan for the exit rider stamped
that day in `predictions/CALIBRATION_TOLERANCE.md`.

Current position: **5 of 41 within ±20%, 2 qualified → EXIT NOT MET.**

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
5. **Candidates are never excluded because they failed.** T2 touches candidate
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
| out-of-catalog, **no edge**, has a magnitude | 54 | 1303 | T7 |
| out-of-catalog, **has an edge**, still unmodelled | 43 | 687 | T4 |
| pets | 14 | 440 | T5 |
| no edge **and** no magnitude | 5 | 112 | — genuinely missing data |

**Only 112 share-points is a data-acquisition problem.** The rest is routing,
and it is our code. This is why the coefficient ingest moved accuracy but not
coverage, and it is the standing correction to the expectation that it would.

---

## 2. Tasks

Each task states what would **falsify** it, so a task that turns out to be
solving a non-problem gets abandoned rather than completed.

### T1 — Report slice accuracy as a diagnostic *(owner approved 2026-08-06)*

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

### T2 — Log admissibility: which parses are valid calibration candidates?

**Owner question, 2026-08-06:** *should we identify and dismiss certain logs — bad
captures, a player present for only part of the fight, deaths, disconnects?*
**Yes, and today we have almost no rule at all.** Here is what was measured.

#### T2a — What the corpus can and cannot currently detect

| failure case | detectable today? |
|---|---|
| wipe / kill | ✅ `encounters.success` (3,527 wipes / 1,928 kills) |
| fight duration | ✅ `encounters.duration_seconds` |
| cast activity | 🟡 `ability_performance.casts` — **but see T2c, it undercounts** |
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

#### T2b — Wipes are NOT a disqualifier (hypothesis tested and rejected)

The obvious rule — "drop the wipes" — is wrong. Wipes are **more** common among
the well-predicted characters (**20 of 33**) than among the over-predictors
(**2 of 8**). Do not filter on `success`.

#### T2c — APM: anchored against the owner's own parses

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
with `sim_magnitude_explosion_absolute_zero` and belongs to T3.

#### ✅ T2 RESOLVED 2026-08-06 by the paired upload (reports 104 + 105)

The owner uploaded two of his own logs, giving the same encounters measured
twice — locally at ground truth and through the API. Four results, and they
change T2's conclusions in both directions.

**1. ✅ The site's `casts` IS `SPELL_CAST_SUCCESS`. T2c's worry is RETRACTED.**

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

> **T2 verdict: no reliable admissibility filter is constructible from the crawl
> API.** The one signal that would work is not exposed. Four candidates have now
> been tested and rejected — wipes, raw DPS, absolute APM, within-character APM.
> **Nothing is filtered.** The corpus contains an unknown number of
> death-deflated parses we cannot identify, and that is a stated limitation of
> the gate rather than something to paper over.

**5. ✅ Mutaforma is confirmed a genuine sim bug**, not a bad parse — normal
activity (APM ratio 0.99) with a +3,619% delta. It belongs entirely to T3.

**Follow-ups this opens (not blocking):**
* `damage_taken_rows` may permit *inferring* a death from a killing blow — the
  only remaining route to presence, worth one session's check.
* The owner can upload logs, and logs **do** carry `UNIT_DIED`. That is ground
  truth for any character we hold a log for, but it does not scale to 4,000
  crawled characters.

#### T2d — What to actually do

1. **Report** wipe status, duration, casts/sec and T1's slice accuracy per
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
comparison is free and would settle T2c's measurement-mismatch question.

---

### T3 — Fix the over-predictions that survive T2

**Do:** for each character still over-predicting after T2, name the mechanism.
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

### T4 — Reachability, class B: 43 abilities that *have* a trigger edge (687 pts)

**Do:** instrument `attribute_trigger_magnitudes` to record, per rejected target,
*which* rule rejected it. The rules are: depth > 2, multi-path
(`ambiguous_skipped`), target is itself a catalog card, or the card already has
that magnitude source. Then decide per reason — several are conservative
defaults from `1b` that were never revisited against measured demand.

**Why before T7:** these already have an edge, so the graph knows the
relationship. Nothing new has to be *inferred* — our own bounded-walk rule is
declining to use what we hold. Cheapest structural coverage available, and it is
entirely our code.

**Verify:** `ambiguous_skipped` falls; coverage rises on named characters; the
`282987` Hammer-from-the-Heavens validation in `cli/relationships.py` still
passes (it is the regression guard for this walk).

**Falsified if:** the rejections turn out to be correct — i.e. attributing them
would double-count. Then record that and move the 687 points to T7's problem.

---

### T5 — Model pets (440 pts) *(owner decision 2026-08-06)*

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

### T6 — Damage-conversion mechanics (≈150+ pts, no data needed)

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

### T7 — Reachability, class A: 54 with a magnitude but no edge (1303 pts)

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

### T8 — Re-run, report, and read it against the rider

**Do:** `py tools/audit/calibrate_crawled.py --limit 120 --max-lag-hours 0`.
Report within-±20%, qualified, and the T1 slice accuracy together.

---

## 3. Sequencing and the expected trajectory

```
T1 ─┐
T2 ─┴─> T3 ──┐
T4 ──────────┼──> T8 (re-run)
T5 ──────────┤
T6 ──────────┘
T7 ─────────────> T8 (likely a later session)
```

T1/T2 are pure instrumentation and gate nothing. T3 depends on T2's answer. T4,
T5 and T6 are independent of each other and can land in any order.

### 🛑 Expect the pass count to DROP before it rises

Chastie, Zaczao and Xoller pass only because a 5–13% modelled slice massively
over-produces. T3 removes exactly that, and T4/T5/T6 add the damage that made
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
| Boomcat | 82% | 888% | 482 | T2 verdict first, then T3 |

**Billyeye is the single cleanest target in the cohort** and is not currently
visible as such, which is the argument for T1 on its own.

---

## 4. What could make this fail

* **T2 goes the wrong way.** If activity does not separate the over-predictors,
  the criterion stays untouched and T3 grows. That is a fine outcome; it is
  written as a falsification precisely so it cannot quietly become an excuse to
  drop candidates.
* **T7 finds no mechanical join.** 1303 share-points stay unmodelled and the
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

* **T2's filter, if activity separates cleanly.** Introducing a candidate-quality
  threshold changes what the gate is measured *over*, and that is your call, not
  mine. I will bring the measured separation and a proposed principle-based
  threshold; the decision to apply it is yours, and it gets written into
  `CALIBRATION_TOLERANCE.md` before any re-run that it affects.

Everything else in T1 and T3–T8 is ordinary work needing no decision.
