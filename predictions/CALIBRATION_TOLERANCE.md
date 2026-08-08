# Calibration tolerance — written BEFORE any 2c calibration run

> **`LIVE`** — the stamped tolerance and calibration reference. **Must be true today, and
> is citable as current truth.** Tolerances in this file are stamped and may not be edited
> to fit a result; **measured tables in it are generated output and MUST be regenerated
> whenever the run they describe is superseded.** If you find a claim here that the tree
> contradicts, that is a defect in this file. *(Classified `3h` A2; `3f` F8c's lifecycle
> applied to `predictions/`, which it had not reached.)*

**Stamped 2026-08-05, session `2c`, as the first act of T8** (PHASE_2 addendum §8.1).

PHASE_2 T8's exit criterion says the sim "reproduces ≥3 real characters within
stated tolerance" and never stated one. Choosing a tolerance after seeing the
deltas is post-hoc fitting wearing a gate's clothes, so the numbers below are
recorded first and are not to be edited to fit a result. Widening them later is
allowed; doing so silently is not — a change needs its own dated entry with the
reason, in this file.

---

## The two tolerances

| Level | Tolerance | Applies to |
|---|---|---|
| **Aggregate DPS** | **±20%** | total DPS for one character on one encounter, sim vs logged |
| **Per-ability** | **±15%** on the ability's *share* of total damage, and **±25%** on its per-hit non-crit average | any ability contributing ≥5% of the character's damage |

**Why these, and not tighter.** They are set from the measured noise floor of
the evidence itself, not from ambition:

* the weapon-free pair ratios — the only quantities in this kit that are
  currently *derivable* rather than fitted — reproduce to **3.2%** (Hammer from
  the Heavens ÷ Hour of Judgement, four logs) and **6.4%** (Dawnreaver ÷
  Whirling Light, three logs). That is the best the data does when the model is
  right, so a per-ability tolerance below ~10% would fail on noise;
* buff and gear state moves the same ability's logged-vs-modelled ratio **1.41×
  between sessions** (session 2b, five logs). Until buffs are modelled, a
  same-character aggregate comparison inherits that spread, and ±20% is the
  honest floor rather than a generous one;
* n is small on several abilities (Dawnreaver 17–38 non-crit hits per log), so
  the sampling error alone is several percent.

**Why not looser.** ±20% aggregate still discriminates the failures that matter.
The 2b state — sim ~600 against a reported ~3,600 — misses by 6×. The error
classes this project keeps finding (a zero-damage ability, a units error, a wrong
rank) all produce misses far outside ±20%, so the gate catches them.

## What counts as a miss

* **Missing the tolerance is a finding to report, not a failure to hide.**
  Report the delta *per mechanism* — which ability, and which modelled quantity
  is wrong — per T8's own rule. A pass/fail number alone is worth very little.
* An ability below 5% of damage is **not** exempt from being wrong; it is exempt
  from the *gate*, because its sampling error swamps the measurement.
* An ability whose sim base is **known** broken (documented in
  `calibrate_vs_log.py`'s `KNOWN_BROKEN`) is excluded from the gate **by id**,
  and every exclusion is listed in the calibration output. An exclusion is a
  debt, not a pass.

## Scope decision: how many characters, and when (addendum §8.2)

The addendum asked this to be resolved explicitly rather than discovered at the
exit gate. **Decision, session 2c:**

> **`2c` calibrates against the owner's character only. The "≥3 real characters"
> criterion MOVES to Phase 3a, and this is a recorded phase-boundary change.**

The reason is a hard dependency, not a shortage of effort. Simulating a crawled
character needs their **gear**, and gear lives in Phase 3 T4's `items` table,
which does not exist — the same dependency that already deferred T7's
`gear_tier_presets` and `scaling_curve`. The crawl records per-ability damage and
a build, but no stat block; without one, a crawled character could only be simmed
against invented stats, and "reproduces 3 characters" would then be measuring our
own assumptions three times.

What `2c` delivers instead, and it is the stronger evidence of the two:

* **one character, five logs, four sessions** — so the model is tested against
  *session variation*, which a single parse of three characters would not show;
* **weapon-free pair ratios**, which are predictions the model makes with no
  fitted input at all, checked per log.

⚠ Anyone reading Phase 2's exit criteria should read this decision alongside
them. Phase 2 exits without the ≥3-character check; 3a owns it.

---

## Addendum 2026-08-06 — the Phase 3 exit gains a coverage rider

**Stamped BEFORE the scraped-coefficient ingest was re-run through the gate.**
That timing is the whole point: the rider is a *stricter* bar than what
currently passes, set while the number it will judge is still unknown.

### The ±20% pass definition is UNCHANGED

`≥3 characters within ±20% aggregate DPS` still means exactly what it meant. It
is not re-derived, not widened, not tightened. Everything above this line
stands.

### What is added: a qualified-coverage rider on the EXIT

> **Phase 3 exits only when ≥3 characters are within ±20% AND at least 3 of
> those also have ≥50% of their real damage modelled.**

At the time of writing: **4 pass, 1 qualified → exit NOT met.**

### Why

`3b` measured the problem the aggregate criterion cannot see. Of the four
characters inside ±20%, **one** (Ari, −10.3%) also has ≥50% of its damage
modelled; the other three (Chastie 5%, Zaczao 6%, Xoller 13%) agree on the total
while the sim reproduces almost none of their kit. That is **compensating
error** — a modelled slice that happens to sum to about the right number — and
an aggregate criterion is structurally blind to it.

The honest fix is not to move the gate. It is to say out loud that agreeing on a
total while modelling 6% of a kit is not calibration, and to make the exit
depend on that. The qualified count was already computed and reported next to
the criterion (`3b`); this promotes it from a companion metric to a rider with
teeth.

### Why 50%, and why now

* **Now**, because coverage sits at a median 37% and the ingest is expected to
  move it. Setting the floor after seeing the post-ingest number would be
  choosing a threshold to fit a result — the exact failure this file exists to
  prevent. Set while the number is unknown, it cannot be gamed in either
  direction.
* **50%**, because below half the kit modelled, the unmodelled remainder is
  large enough to absorb an arbitrary error in the modelled part, which is the
  compensating-error case. It is a floor on *interpretability*, not a target
  fitted to any character's coverage.

⚠ Same standing rule as the rest of this file: changing this rider later is
allowed, doing it silently is not. A change needs its own dated entry here with
its reason — and, given what it gates, a reason that does not reduce to "the
current number did not clear it".

---

## Addendum 2026-08-06 (session `3d`, F4) — a SUCCESSOR criterion, recorded early

**This entry changes nothing that is currently in force.** The ±20% pass
definition and the ≥3-qualified-at-≥50% rider both stand exactly as written
above. It is recorded now, before `3e` does the modelling work that will be
judged against it, so that it can never be mistaken for a threshold chosen after
seeing a result — the same reason the 50% rider was stamped before its own run.

🛑 **It takes effect AT THE NEXT GATE, NOT THIS ONE.**

### The successor: report slice accuracy, and read coverage against it

> From `3e` onward, every gate run reports **slice accuracy** per character and
> as a cohort median, alongside coverage — and **every coverage task reports it
> before and after.** A task that raises coverage while dropping slice accuracy
> has moved the metric, not the model.

Implemented in `3d` (`tools/audit/calibrate_crawled.py`, F3) as pure
instrumentation: it changes no verdict, and the gate was byte-identical with it
in place.

🚨 **CORRECTED TWICE. Read both corrections — the second is larger than the first.**

**Correction 1 (`3e` A2): the sign.** `3d`'s figure was *"cohort median 160% — the modelled
slice is over-produced by about 60%"*. That median is a **low-coverage artifact**: slice
accuracy has **coverage in its denominator**, so it explodes as coverage → 0. Mutaforma, at
**0.2%** coverage, reports **1,859,400%** — and that value is in the committed `3d`
manifest. A median across a cohort spanning 0.2% to 82% coverage is not a measurement of
anything. **The sim under-produces on what it models.**

🚨 **Correction 2 (`3g` G1): the size, and it is four times worse than correction 1 left
it.** The `64.3%` this section carried until `3h` was **never true** — it was measured on a
sim in which `AttackTable.probabilities()` returned percentages that `expected_swing`
multiplied as fractions, making every white swing **exactly 100× over** (`ENGINE_BUGS.md`
E13). The auto was **89–96% of total sim damage for fourteen of 36 characters and 41–95%
for all five passers.** Slice accuracy did not *drift* from 64.3% to 20.5%; the earlier
figure was measuring a defect.

| coverage floor | n | median slice accuracy | readable? |
|---:|---:|---:|:--|
| ≥0% | 34 | 41.0% | **no** — below the floor |
| ≥10% | 27 | 32.7% | **no** — below the floor |
| ≥20% | **24** | **30.1%** | yes |
| ≥30% | 20 | 24.4% | yes |
| ≥50% | 10 | 10.2% | yes |

⚠ **Table PASTED FROM THE TOOL, never retyped (`3f` F8).** 🆕 **`3j` C3 — it is now
GENERATED AND ASSERTED, because the warning alone failed twice.**
`py tools/audit/render_band_table.py` renders it from
`predictions/gate_manifest_3e.json`'s `result.slice_accuracy_by_coverage_band_pct`, and
`check_refusals.py` asserts the paste matches — the same treatment `3h` A4 gave
`CLAUDE.md`'s census line, for the same reason: *generation only helps if something
asserts the paste.*

🛑 **The two failures, because they are the argument for the assertion.** `3f`'s table
survived `3g`, a session that regenerated the manifest **five times**; `3h` A2 regenerated
it and wrote the standing warning above. Then `3i` **moved the gate twice** (E15, then
admissibility) and did not touch this table — the warning was ignored by the session that
had just written it. `AUDIT_3I` §9.3 measured the drift: doc `≥10% 23.4% (n=26)` against
manifest `34.96% (n=27)`, doc `≥20% 20.5%` against manifest `26.31%`.

🆕 **`3m` pre-flight (`AUDIT_3L` F11) — the figures the prose below is built from are
GENERATED AND ASSERTED, exactly like the table above.** Row *"stated as a fraction of
reality"* is the sentence that used to live here in words:

<!-- GENERATED derived-figures (render_band_table.py) — DO NOT RETYPE -->

| derived figure | value | derived from |
|---|---:|---|
| headline slice accuracy (≥20% coverage floor) | **30.1% (n=24)** | `median_slice_accuracy_pct_at_coverage_ge_20` |
| …stated as a fraction of reality | **roughly ONE THIRD** | the same figure, rendered in words |
| multiple the slice must rise by at the 100% coverage CEILING | **3.3×** | `100 / headline` |
| best coverage anywhere in the cohort | **Boomcat 82.2%** — **NOT ADMISSIBLE** | `max(cohort[].modelled_damage_pct)` |
| …slice accuracy that coverage would require for `delta = 0` | **121.7%** | `100 / (best coverage / 100)` |
| producing-only slice median (≥20%) | **32.7% (n=23)** | `median_slice_accuracy_pct_producing_only_at_coverage_ge_20` |
| …paired over the SAME members (no selection bias) | **30.15% headline / 36.27% producing-only (n=24)** | `paired_medians_same_members_at_headline_floor` |
| …admissible-only slice median (≥20%) | **27.62% (n=21)** | `median_slice_accuracy_pct_admissible_only` |

*(from `gate_manifest_3e.json`, generated 2026-08-08T17:08:58+00:00, git `b0c118b`.)*

<!-- /GENERATED derived-figures -->

**The sim reproduces the fraction named in that block's second row, of the damage of the
abilities it has a key for.**
⚠ *(History, kept because it is the argument for generating the word: this sentence read
"ONE FIFTH" — true of the pre-E15 20.5% — then "ONE QUARTER" at 26.3%, and was stale
again at 30.4% inside the session that regenerated the table above it. It states no
number now. `AUDIT_3I` §9.6 flagged the same wording on `ENGINE_BUGS` E16.)*
⚠ *"has a key for"* is deliberate and is not the same as *"models"* — see
`AUDIT_3G_ADVERSARIAL.md` §4 and `3h` Block B. Until that split is measured, this figure
conflates magnitude error with zero production.

> ✅ **ANNOTATION (`3i` A5, ⚠ CORRECTED `3j` C3, ⚠ DE-NUMBERED `3m` pre-flight): the
> split IS measured now** (`3h` Block B, committed in `gate_manifest_3e.json`) — the
> producing-only median and the headline are the last two rows of the generated block
> above, and **this annotation no longer restates either.** ⚠ The two medians are over
> **different populations**: the producing-only figure is upward-biased by selection
> (the dropped members are the worst cases), which is why the block's final row carries
> the **paired** medians over the same members (a `3i` C5 output). The paragraph above
> is kept as stamped.
>
> 🛑 **This annotation has now gone stale twice, in two different sessions, and that is
> why its numbers were removed rather than corrected a third time.** `3i` wrote it in
> Block A citing *"30.7% (n=20)"*, then re-ran the gate in Block D — by its own close
> the manifest read 37.65 (n=19) and the annotation cited a figure the file it named no
> longer contained. `3j` C3 corrected it to 37.6/26.3; `3l` moved the gate again and it
> was wrong on both halves within the day. **Two corrections of the same sentence is
> the signal to change its owner, not to correct it better.** The lesson otherwise
> stands: an annotation written in Block A and a gate re-run in Block D belong to the
> same session and must be reconciled before it closes.

*(Corroboration, independent of coverage: `3f` F9's frost-mage assertion compares modelled
DPS to a measured capture with a same-session verified stat block and no coverage term. It
reads **457 against 1,382 — −66.9%**, i.e. the sim produces ~33% of one real character's
total output. That it is not ~20% is itself informative and is a `3h` Block C question.)*

> ✅ **ANNOTATION (`3i` A5, ⚠ CORRECTED `3j` C3): the `3h` Block C question is
> answered** — `3h` P5 reconciled F9's 33.1% against the producing-only figure; the
> gap to the headline is the keyed-but-zero mass plus composition. ⚠ **The `3h`
> reconciliation was computed on the PRE-E15 corpus** (producing-only 30.7%,
> headline 20.5%), where the two figures sat 2.4 points apart. Post-E15 the
> producing-only figure is **37.6%** against F9's 33.1% — still close, now with F9
> the *lower* of the two, and F9 itself is a single character on a same-session stat
> block with no coverage term, so it did not move with the corpus fix. The
> reconciliation stands in kind; its arithmetic is restated here rather than left
> reading as current. It also inherits the selection bias noted above
> (`AUDIT_3H` §7.1).

🛑 **Why this matters more than a bigger number.** At slice accuracy ~62–64% the previous
text said *"both levers have to roughly double"*, which reads as a hard but ordinary
programme. **At the headline slice the coverage lever is arithmetically dead.** Landing
`delta = 0` requires `slice × coverage = 1.0`, and the generated block above states both
consequences:

* at the **ceiling** of 100% coverage, slice must reach **100%** — the block's
  *"multiple the slice must rise by"* row;
* at the **best coverage anywhere in the cohort**, slice must exceed **100%**, which is
  impossible by construction — the block's *"slice accuracy that coverage would require"*
  row;
* no attainable coverage substitutes for **any** of it.

⚠ *(History: this passage stated "At 20.5%" and "a **4.9×** rise", was corrected by
`3j` C3 to 26.3% / 3.8×, and was stale again at 30.4% before `3m` de-numbered it. **The
conclusion has survived every correction and each one made it no easier** — the required
multiple is still far beyond what coverage work can substitute for, and the
best-coverage row exceeds 100% under every value the headline has ever taken. That the
argument is invariant to the number is the reason it can safely stop quoting one.)*

**The magnitude lever has to carry essentially all of the gap.** Coverage work is now
support work, not the programme. Under the discarded 160% reading the conclusion inverted
entirely — it said coverage work would *overshoot* — and under the 64.3% reading it said
the two levers could share the load. Neither is true.

**Reporting rule, in force from `3e`:** the cohort median is reported **only
above a stated coverage floor, with the floor printed beside it** and the band
table under it, and the manifest key carries the floor in its name
(`median_slice_accuracy_pct_at_coverage_ge_20`). A bare
`cohort_median_slice_accuracy_pct` pins a number two readers will read two ways.

### 🛑 Stamped successor #2: a 20% coverage floor on `within_tolerance` itself

**Owner decision 2026-08-06, effective at the gate run AFTER `3e`.** Stamped
here before `3e`'s own result was known, and it is a **stricter** bar — the
direction a criterion is allowed to move.

`within_tolerance` is `abs(delta) <= 20` **and nothing else**. Three of the five
characters carrying the ≥3 criterion sit at **4.6%, 5.6% and 13.3%** coverage, so
the criterion can be carried by characters whose kit the sim barely models. From
the next gate, a character must also have **≥20% of its real damage modelled** to
count as within tolerance.

**Why 20%, and why this is not a number chosen to admit a wanted result:** slice
accuracy is stable at ~63% across the ≥20 / ≥30 / ≥50 bands and unstable below
20% (144% at ≥10%, 165% at ≥0%). 20% is where the metric stops being noise — a
property of the measurement itself. At today's numbers the floor takes the gate
from **5 passing to 2**, i.e. it fails on the run that stamped it.

> ⚠ **ANNOTATION (`3i` A5): every band figure in the stamped paragraph above was
> measured on E13-inflated autos** (the same caveat `calibrate_crawled.py` carries at
> its `~62%` reference). Post-E13 the bands read 20.5 / 16.9 / 16.9 at ≥20/≥30/≥50 and
> 23.4 / 40.3 at ≥10/≥0 — see the regenerated table above. The floor's *justification
> shape* (stable above 20%, denominator-dominated below) survives; the stable level
> does not. Stamped text left as written, per the standing rule.

**What lands in `3e` instead:** `within_tolerance` returns **`None`, not
`False`, at zero coverage** — three cohort members (Huskeer, Jamppa, Xizek) have
0.0% coverage with a non-null delta, and the sim has no opinion about them.
Slice accuracy already refused to report there; the criterion now does too.

---

#### ✅ APPLIED 2026-08-07 (`3g` G4) — and it cost nothing, for a reason worth reading

**That gate is `3g`.** The floor is in force, in its own commit with its own
before/after pair (owner decision 2026-08-07). Below it the verdict is
**NOT SCOREABLE** (`None`), not `False` — the same treatment zero coverage
already had, because *"we have no opinion"* is a different statement from
*"it failed"*. **The value was not re-tuned**: 20.0 is what was stamped on
2026-08-06, and changing it after seeing `3g`'s result would be moving a gate
after seeing its number, in either direction.

🔬 **It removed nobody, and the reason is the session's best corroboration of
its own justification.** When this was stamped it would have cut the gate from
**5 passing to 2**. By the time it was applied, `3g` G1 had fixed **E13** — a
percent-vs-fraction unit error making every white swing exactly 100× over — and
the only surviving passer sits at **82.2%** coverage, far above the floor. The
four low-coverage passes the floor was designed to catch (4.6%, 5.6%, 13.3% and
one at 57.6%) were **the same characters E13 was inflating**: their passes were
compensating error, and two independent instruments — a coverage floor stamped
on the shape of the metric, and a unit fix in the engine — identified the same
rows from opposite directions. Ten characters are now NOT SCOREABLE under the
floor; none of them was passing.

**Attribution, settled from git** (`3g` G4, answering `AUDIT_3E` §6): `git log
-S` puts `SLICE_COVERAGE_FLOOR_PCT` and `SUCCESSOR_COVERAGE_FLOOR_PCT` in **one
commit**, `68779e7`. The **owner decided the policy** — that a floor applies,
at the next gate and not the one being run. **Code chose the value**, in A2 of
that same commit, from the band table. Neither claim was ever false, and a
reader could reasonably take *"owner decision"* to cover the number as well —
which is what the auditor flagged. The property that matters survives either
reading: the value was fixed **before** it was applied to a criterion, and it is
strictly harsher than what it replaced.

### 🛑 Stamped successor #3: parse admissibility (stamped `3h` D4, APPLIED `3i` D)

**Owner decision 2026-08-07, effective at a LATER session's gate run with its
own before/after pair — nothing in `3h` applies it, and the `3h` gate reads
`1 / 1 / 20.5%` unmoved.** Same discipline as successor #2: stamp first, apply
in a commit that owns its pair.

> ✅ **APPLIED, `3i` D (`0fbffd5`), with its pair: `1 / 1 / 26.3%` → `0 / 0 / 26.3%
> (n=23)`.** `Boomcat` — the cohort's only passer — became NOT ADMISSIBLE at APM ratio
> 0.24, exactly as this stamp predicted. *(Heading corrected `3j` C3: it read
> *"NOT applied"* while the body four paragraphs down already narrated the applying
> session — heading and body disagreeing inside one section, `AUDIT_3I` §9.3. The
> paragraph above is kept verbatim as stamped text; it describes `3h`, and `3h` is
> when it was true.)*

**The rule: a character may be excluded for what its PARSE is, never for what
its DELTA is.** Every predicate is a property of the parse, computable blind
over the whole cohort — tuning set and holdout identically — before any delta
is read. Verdict is **NOT ADMISSIBLE (`None`)**, never `False`.
Implementation: `tools/audit/parse_admissibility.py` (`3h` D1).

**The predicates:**

1. **APM ratio ≤ 0.5** — this scope's casts/min at or below half the median of
   the character's own other scopes. 🛑 **Valid only on instant-heavy boards
   (≤ 2 cast-time combat entries, resolved via `casting_time_index` →
   `dbc_spellcasttimes`); outside that regime the ratio is `None`, never a
   number** — `ability_performance.casts` under-counts cast-time casters, and
   22 of the 41 cohort boards are cast-time casters.
2. **deaths > 0** — inert until data exists: the `3h` D2 re-fetch verified the
   API exposes **no per-player death or active-time field**, so this arms only
   if a future source carries it.
3. **Parse window < 60 s** — the analyze-capture provisional-data floor.
4. **The capture resolves to no phase** (G0's post-boundary state).
5. **Snapshot lag > 0 h** — already enforced at selection; removes nobody by
   construction, stated so the list is complete.

> 🆕 **AMENDMENT (`3j` A2, owner decision 2026-08-07) — predicate 1's
> comparator definition, stated. Appended, never rewritten in place.**
>
> The stamped text above says *"the character's own other scopes"*. The
> implementation (`3i` D5) restricts that to **qualifying** scopes, and the
> `3i` audit correctly flagged the two as disagreeing under an unchanged
> stamp. **Owner decision: stamp follows code.** Predicate 1 reads, in full:
>
> > **APM ratio ≤ 0.5** — this scope's casts/min at or below half the median of
> > the character's own other **qualifying** scopes, where a qualifying
> > comparator scope (a) shares no encounter with the scope under test,
> > (b) is at least **60 s** long, and (c) contains no trash encounter. A
> > comparator whose APM is legitimately **0.0 is admitted**, not dropped.
> > Fewer than **2** qualifying comparators ⇒ ratio `None` (refused), never a
> > number.
>
> **Why the code and not the stamp moved.** These are correctness properties of
> the predicate, not a weakening chosen to move a number: (a) a `boss_group`
> comparator that *contains* the `boss_single` scope under test compares a
> parse against itself — measured under the `3j` P1 counterfactual, `Nodding`'s
> unfiltered comparator set is **371 scopes** and `Robottikyrpa`'s contains
> visible duplicate pairs (`41.3, 41.4, 42.3, 42.3, 47.0, 47.0 …`), the
> self-overlap signature; (b) a sub-60 s comparator violates the same
> capture-validity floor **predicate 3 already enforces on the tested scope**,
> so admitting it as "typical" contradicts the neighbouring predicate; (c)
> trash scopes are a different content type, not a different day.
>
> 🔬 **And the change set is NOT one-way, contrary to `AUDIT_3I` §4.** That the
> filters can only *remove* comparators is true of the `< 2` escape hatch and
> **false of the median**: removing LOW-APM comparators raises the median and
> lowers the tested ratio, adding a flag. Registered in advance
> (`predictions/prereg_3j_comparator.md` P3) and run —
> `check_refusals.py :: check_comparator_can_add_a_flag`, tested 8 APM against
> qualifying comparators 18/20 with sub-60 s comparators at 2/3: **0.762
> admissible unfiltered, 0.421 flagged filtered.** On the live cohort the same
> effect is visible small: D5 moved `Boomcat` 0.27 → **0.24**, *toward* the
> bound.
>
> ⚠ **The counterfactual roster is measured, so this amendment is not a
> free choice made in the dark** (`3j` P1/P2, both CONFIRMED). With all three
> filters removed on today's corpus the roster is **5 of 41** — Nodding,
> Robottikyrpa (0.24), Boomcat (0.27), Deyindra (0.22), Frediib (0.14) — and
> the published gate is **identical either way: `0 / 0 / 26.3% (n=23)`**. So
> the amendment changes who is named as inadmissible and changes **no headline
> figure**. It is adopted on the correctness argument alone, which is the only
> ground it could honestly be adopted on.
>
> 🛑 **What this does NOT re-open:** the `3h` P9 falsifiability question. Under
> the narrow predicate P9 registered, the count of removed FAILING characters
> is **0** with the filters and **2** without (Robottikyrpa, Frediib) — the D7
> correction below states this already. The full rule's bar still holds via
> `Nodding` (predicate 3). Choosing the definition that scores *worse* on the
> narrow bar is the direction that rules out fitting.

**Measured blind effect on all 41, computed before any verdict was consulted
(pasted from `parse_admissibility.py`, run 2026-08-07 at `7fc5bc0`):**

```
[blind] cohort effect: 5 of 41 members flagged NOT ADMISSIBLE (None, never False):
        Nodding (window 52s), Robottikyrpa (0.24), Boomcat (0.27),
        Deyindra (0.22), Frediib (0.14)
[falsifiability]
  removes FAILING characters: 3 (Nodding, Robottikyrpa, Frediib)
  removes PASSING characters: 1 (Boomcat)
  removes NOT-SCOREABLE characters: 1 (Deyindra)
```

🔬 **The falsifiability bar is met and is the reason this was stampable at
all**: the rule removes three characters that currently FAIL. A rule that only
ever removes passers is a fitting device, and the asymmetry proves it — that
check ran before stamping, per the rule's own text in `CLAUDE.md`.

⚠ **What applying it will do is already known in outline and must be recorded
by the applying session as its own before/after pair**: `Boomcat` — the only
passing row — is flagged at APM ratio 0.27 (the implemented confirmation of
`3c`'s chat-side 0.24), so applying the rule takes the gate's `within ±20%`
count from 1 to 0 with `Boomcat` NOT ADMISSIBLE rather than failed.
Pre-registered direction and interpretation: `predictions/prereg_3h_boomcat.md`
(P7 supported; P8's it-survives branch did not arise).

> ✅ **CORRECTION (`3i` D7): the "3" above is the FULL-RULE falsifiability
> count, not the count `prereg_3h_boomcat.md` P9 actually registered.** P9
> registered *"the death-deflation predicate (an APM ratio ≤ 0.5 within the
> valid regime, or deaths > 0)"* — two predicates, not five. Of the three
> names in "removes FAILING characters: 3", `Nodding` was flagged by
> predicate 3 (the 52s window), not by APM ratio or deaths. **On the
> predicate P9 actually registered, the count is 2** (Robottikyrpa, Frediib).
> The bar (≥1) was met either way and the stop-rule did not trigger — the
> DECISION does not change, only the number attached to it. Pasted block
> above kept verbatim, per this project's rule against rewriting stamped
> text.
>
> ⚠ **FURTHER CORRECTION (`3i` D5, applying session): the tightened
> comparator moves the roster, not just this count.** D5 fixed three
> fail-open comparator flaws (a comparator scope could overlap the scope
> under test, be shorter than the parse-validity floor, or contain trash) —
> real correctness fixes, found in `AUDIT_3H_ADVERSARIAL.md` §5.2/§5.3, not
> a fit to any wanted result. Re-run: **`Robottikyrpa` and `Frediib` no
> longer carry a confident APM ratio at all** — their comparator sets shrank
> below 2 qualifying scopes once self-overlapping/short/trash-tainted
> comparators were excluded, so `ratio` is `None` (refused), not `≤ 0.5`.
> **Under the P9-registered predicate alone, the count is now 0.** The
> FULL rule's falsifiability bar is still met, because `Nodding` (predicate
> 3, untouched by D5) is unaffected — see `predictions/prereg_3i_admissibility.md`
> for the full account and why this does not change the decision to apply.

### The ~80% coverage figure, and why it is NOT a floor

The decomposition is algebraically exact:

```
slice_accuracy = (100 + delta) / coverage
```

Set slice accuracy = 100 ⇒ `delta = coverage − 100` ⇒ `|delta| ≤ 20 ⇒ coverage ≥ 80`.
So ~80% coverage is where a *truthful* model lands inside ±20%, and the figure
reproduces independently. **It is nonetheless neither necessary nor sufficient,
and must not be adopted as a threshold:**

* **Not necessary.** 110% slice accuracy at 73% coverage gives −19.7% — a pass,
  below 80.
* **Not sufficient.** 80% coverage at 60% slice accuracy gives −52% — a fail, at
  80.
* It is **one point on a 2-D curve**, valid only at *exactly* 100% slice
  accuracy, which `PLAN_3C` §4 says will not happen.

### And the trajectory assumption behind it is unsafe

The formula assumes the unmodelled slice is predicted at **zero** — true today
by construction. The risky step is assuming damage *added* by the reachability
tasks arrives at ~100% fidelity. Our own data refutes that: the out-of-catalog
cluster reads **4.3–4.7× logged/base**, i.e. ~22% fidelity. Covering the residual
42% at 22% fidelity buys roughly **9 delta points, not 42**.

Worse, **coverage is a MEMBERSHIP TEST** (`modelled_damage_share`,
`calibrate_crawled.py:171-224`), so a spell modelled at 4.5×-under counts as
*fully covered*. Coverage work therefore **mechanically raises coverage while
depressing slice accuracy**, and a currently-passing character can be LOST by
pure coverage work with no accuracy change at all — Ari (156%) and Malo (131%)
are both over-producers today and are the ones at risk.

**Therefore: 80% is a diagnostic landmark, not a bar.** Nothing may fail a gate
for being below it, and nothing may pass for being above it.

### 🚨 A separate finding that this criterion cannot fix, recorded here because it changes what any of these numbers mean

Measured in `3d`: rebuilding `builds.db` after the daily crawler ran moved the
gate from **5 of 41 to 4 of 38 with zero code changes**.
`calibrate_crawled.candidates()` is `ORDER BY character_id LIMIT 120` over a
population that grew from **157 to 180** qualifying characters, so the limit —
written as a cost cap — is really a **sliding window keyed on an arbitrary id**.
Four characters left the cohort and four entered for no reason but their id.

**Consequence: two gate results are comparable only if their cohorts match.**
`predictions/gate_manifest.json` (`3d` E2) now records the cohort by character id
on every run, which is what makes the comparison checkable — and what makes the
holdout set below pinnable. **Fixing the sliding window is `3e` work**; `3d`
ships no change to the gate's population, deliberately.
