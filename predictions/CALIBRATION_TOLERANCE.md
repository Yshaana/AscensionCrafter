# Calibration tolerance — written BEFORE any 2c calibration run

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
