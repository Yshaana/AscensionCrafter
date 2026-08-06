# Session 2026-08-06 — 3b: the gear layer, and the decomposed calibration gate

Phase 3b proper, driving `PLAN_3B_UPDATE.md`'s critical path (§5): fix the gear
/ stats layer, then re-run the calibration gate with the miss **decomposed**
rather than attributed wholesale. Owner scoping decision at session start:
critical path first, addon/logs/automation (T5–T7) deferred to a later session.

**Headline: the crawled calibration gate moved from 0 of 41 to 4 of 41 within
±20% — and it moved on one missing input, not a fitted constant.** Read the
pass with its coverage caveat below; it is not a clean pass.

---

## 1. Gear: the difficulty axis lives in the item_id

`PLAN_3B_UPDATE.md` §1 says stats are rolled at drop as a function of tier, so
two items with the same name can carry different stats. **Confirmed** — 476 of
1,157 resolved item names span several item_ids at different tiers.
`Golem Shard Leggings` is the clean case:

| item_id | tier | Strength | armor |
|---|---|---:|---:|
| 13074 | Mythic 10 | 45 | 703 |
| 1663074 | Mythic | 38 | 633 |
| 1563074 | Heroic | 30 | 606 |

**But each variant carries its own item_id**, which makes `item_id -> (tier,
stats)` a *function*: across 3,919 stat-bearing rows, **0 item_ids carry more
than one distinct stat block, and 0 span more than one tier.**

So §3's discipline splits in two, and the owner amended it accordingly
(decision 2026-08-06):

- ✅ **Kept, and it is the real hazard: never map item NAME -> stats.** The
  crawl's own `match_type='name_fallback'` rows are exactly this failure, and
  they are now carried through as **`snapshot_gear.stats_match_type`** (98 in
  the corpus) instead of being dropped, so a name-matched block can be flagged
  or excluded downstream.
- ❌ **Dropped: "the deduped `items` table is wrong for per-character stats."**
  The dedup keys on item_id, which already encodes difficulty, so it is
  lossless. Reading instances remains right (it is what carries slot, enchant
  and gems) — but the dedup was never the hazard.

⚠ **Not established, deliberately:** whether the numeric relation between a
base id and its variants (`13074` -> `1563074` / `1663074`) is a decodable
scheme. The prefixes are inconsistent across the corpus, and relating two ids
by a pattern is the same error class as relating two spells by name. Variants
are grouped by **name + tier as an observation**, never derived arithmetically.

## 2. Coverage — reportable, and not repairable

`gear_coverage()` reports the fraction of **stat-bearing** slots whose stats
resolved. Shirt and tabard are excluded as legitimately statless — measured,
not assumed: they resolve 0 of 209 and 0 of 87 across the corpus while every
other slot resolves the majority.

Across the gate's 41 characters: **median 100%, and 30 of 41 resolve every
stat-bearing slot.** So gear under-resolution is *eliminated* as the dominant
cause for most of them — they were simmed on their whole real gear set and
still missed by a median −92%.

**It cannot be improved from inside the corpus:** an unresolved item is
unresolved on *every* snapshot (0 of 592 unresolved item_ids resolve anywhere
else), because those ids are absent from the upstream item database — they are
levelling greens and vanilla items outside BisBeard's S10 scope. Recorded as
open question `crawl_gear_coverage_is_not_repairable` rather than papered over.

`missing_stat_budget_bound()` estimates what a partly-resolved character is
missing, by crediting each unresolved piece the **median** resolved stat budget
of its slot. 🛑 It is an estimate with a stated method, used **only** to
decompose a miss — never added to a character's stats, never fed to a sim run.

## 3. 🚨 Weapon damage is absent from every stat block

The one that mattered. `resolved_bisbeard.stats` never carries weapon damage
and `resolved_bisbeard.damage` is **NULL on all 1,413 weapon-slot entries**, so
`build_spec_for` was constructing every crawled character with `weapon=None` —
**the sim gave all 41 gate candidates no weapon at all**, zeroing every white
swing and every weapon-percent ability.

The numbers exist only in the rendered item description:
`63 - 107 Damage   Speed 2.60`.

⚠ **This is not the banned "read a magnitude from a description string" rule.**
That rule is about **DBC** descriptions, which are tooltip *templates* carrying
`$` variables and hand-rolled level scaling — the class of thing that renders
Hammer from the Heavens as "194 to 147". This is a third party's
already-rendered item text with literal integers, and **it ships its own check
digit**: the same string states the weapon's DPS, so `(min+max)/2/speed` must
reproduce it.

**The check is enforced, not assumed** — a parse that fails it returns `None`
rather than a number. Validated at **849 of 849** parsed weapons agreeing
within 3%. (At a 0.15 *absolute* band 110 look like mismatches, and every one
of them is the displayed speed being rounded to one decimal — which is why
speed is taken as `(min+max)/2/stated_dps`, the more precise of the two.) Hand
(1h/2h) comes from the numeric `INVTYPE` field, never from the prose.

Persisted as `snapshot_gear.weapon_json`; 361 rows populated.

## 4. The decomposed gate

`calibrate_crawled.py` now decomposes the miss into the three mechanisms that
each produce a one-directional negative delta. 🛑 It produces **a verdict per
mechanism, not a split that sums to the miss** — apportioning a multiplicative
shortfall across candidate causes would require knowing the answer, whereas
whether each cause is *capable* of explaining a miss that size is enough to
eliminate candidates.

| leg | before the weapon fix | after |
|---|---|---|
| gear resolution | ELIMINATED for 30 of 41 (median 100% coverage), who still missed by a median −92% | unchanged; those 30 now miss by a median −68% |
| buffs | median **+0.0%**, max +10.6% | median +0.0%, max +5.0% |
| magnitude coverage | DOMINANT for 36 of 41 — sim produces damage for a median **20%** of real damage | DOMINANT for 30 of 41 — median **37%** |

**Gate: 4 of 41 within ±20%, criterion ≥3 — PASS.**

### 🛑 Read the pass with its coverage

Only **one** of the four (Ari, −10.3%, 58% of its real damage modelled) is
within tolerance *while the sim also reproduces most of the kit*. The other
three — Chastie (5% modelled), Zaczao (6%), Xoller (13%) — agree on the total
while missing nearly everything the character pressed: the modelled slice
happens to sum to about the right number. **That is compensating error, and the
±20% aggregate criterion is structurally blind to it.**

The criterion was **not** changed after seeing the result. The qualified count
is reported alongside it and neither replaces the other — moving a gate's
definition once its number is known is how a gate stops meaning anything.
Owner decision recorded as open question
`crawled_gate_passes_by_compensating_error`.

### One reporting bug found and fixed en route

The log renders auto-attacks as **negative** spell ids (`-1`, plus school
variants `-22..-26`) while the sim keys its swing layer `auto_mh`/`auto_oh`, so
matching on id alone scored every character's white damage as unmodelled and
understated coverage by ~9 points. ⚠ Not every negative id is an ordinary
swing — extra-attack procs log identically (`Auto Attack [Hand of Justice]`)
and the sim does not model those. The discriminator is taken **from the row
itself**, not from the id's magnitude: a bracket tag equal to the row's own
`spell_school` is a school-flavoured swing; anything else names an item.

## 5. The measured demand list

The gate report now ends with the biggest unmodelled abilities across the
corpus, ranked by how much of their owners' real damage the sim produces
nothing for. **This is measured demand, not a guess at what matters**, and it
is the shortlist the next magnitude work should read. Top entries include
Devour Mind (287865), Arcing Light (954923), Icy Penance (271340), Frostbolt
(25304), Righteous Vengeance (61840) and Consecrated Holy Weapon (200818) —
200818 arriving on this list independently of the owner's own parse is
corroboration that `extract_scope_missing_log_observed_ids` is correctly
prioritised.

## 6. Doc drift caught

`BEFORE_3B.md` §3 and the 3b pre-flight session record both list the
`WoWCombatLog` naming convention and `ReloadUI()` availability as **still
blocked on the owner**. Both were **resolved 2026-08-04** and are written up in
`PHASE_3_builds_repo.md` Tasks 5 and 6 (filename `YYYY-MM-DD-HH.MM.SS
WoWCombatLog.txt`, verified against three real logs; `ReloadUI()` confirmed
working in game). They are not blockers for T5–T7 whenever that session runs.

## 7. Consolidation review — and the source the project had been missing

Owner asked mid-session to stop and consolidate rather than pay the cost later.
Classifying **every** unmodelled damage row across the gate cohort by *why* the
sim misses it:

| share of the cohort's real damage | root cause |
|---:|---|
| **42.9%** | spell absent from our DBC extract entirely |
| **41.1%** | we hold the magnitude but **no coefficient** |
| 9.1% | auto-attacks / extra-attack procs |
| 5.5% | data exists — a genuine resolver/APL gap |
| 1.3% | in extract, no decoded magnitude |

**Only 5.5% is a code problem.** The resolver and APL are essentially fine;
this is a data problem, and the second bucket is one the client *structurally
cannot fix* — Ascension keeps applied coefficients in tooltip text, not numeric
fields (`effect_bonus_coefficient_is_not_the_sp_ap_coefficient`).

🆕 **`db.ascension.gg` states them outright, and the project had used it by
hand exactly once** (session `1x`, Hammer from the Heavens) without ever
systematising it. Spot-checked against the worst offenders:

| spell | our data | the site |
|---|---|---|
| Icy Penance (271340) | flat 284, no coefficient | Value **284** · SP 29.0% · AP 7.8% |
| Devour Mind (287865) | nothing | 113/tick · SP 8.0% · AP 5.5% |
| Arcing Light (954923) | nothing | 140 +1.2/lvl · SP 12.0% · AP 7.8% |
| Firebolt (11763) | nothing | 83–93 +1.2/lvl · SP 74.5% · AP 48.4% |

It reaches **both** buckets — magnitudes for what the extract lacks,
coefficients for what it has. ⚠ **Consequence for the roadmap: the widened
`--with-dbc` run drops off the critical path.** It has been the top structural
ask since `2e` and needs the owner's client plus a built StormLib; the web
source reaches most of the same spells without him.

### Routes checked and rejected first (owner asked for outside-the-box)

- **`?spell=X&power`** — the site is Wowhead/Aowow-derived, so this returns a
  583-byte JS object instead of a 25 KB page. Carries the rendered tooltip
  but **no `Scaling #N` lines**. Cheaper and useless; not taken.
- **`sitemap.xml`** — 16 KB of guides and category listings, no per-spell URLs.
- **`robots.txt`** (checked 2026-08-06) — `Allow: /` for all agents, **no
  `Crawl-delay`**, disallowing only `?admin=`, `?account=`, `?compare=`,
  `?filter=`, `?search=`, `?go-to-comment=`, `*&filter=`. Spell pages are
  explicitly permitted; we are stricter than required regardless.

### The check digit, and the bug it caught

A scraped coefficient is accepted **only** where the page's stated base value
reproduces the flat we decoded independently from the client's numeric fields.
**14,100 spells** give us that check, so it is a standing validation surface,
not a spot check. A disagreement **refuses** the coefficients.

🚨 It earned its keep against our own code, not the site. The first version
aggregated `MIN/MAX` across effect slots, so Lightbound Cleave's effect 0
(flat **62**) and effect 1 (**65% weapon damage** — the `EFFECT_WEAPON_PCT`
trap, INDEX_GUIDE v13) merged into "62–65", *a range belonging to no effect*,
and falsely contradicted the page's correct `Value: 62`. Now compared **per
effect slot**. Generalises: **an aggregate across effect slots is not a
property of the spell** — it mixes units, and a flat and a weapon-percent are
different kinds of number.

### Free corroboration

The page gives Molten Earth `60 + 2.6/level, SP 0.11, AP 0.11`; the owner's
**live in-game tooltip** (primer §1 v7) reads `60 + (SP+AP)×0.12`. Two fully
independent sources landing on the same numbers is evidence the site reflects
*this server's* values rather than stock 3.3.5.

### Trigger links are a byproduct

Pages state `EffectTriggerSpell` relationships and the target id is taken from
the page's own `href` — **never** by matching link text to a name (primer §4).
Verified on Hour of Judgement → `282987` Hammer from the Heavens. **154 trigger
edges** found in the first 39% of the run.

### The scraper

`tools/scrapers/scrape_ascension_db.py` + `core/spells/db_ascension.py`
(parsing only — `core/` takes text, not URLs). **Scoped by measured demand,
never by enumeration**: the request list is spell ids that actually dealt
damage in the crawl corpus, ranked by damage. 285 ids cover 90% of all logged
damage (~11 min at 2s); 2,902 cover everything observed (~2 h, ~3 MB stored).
Records append-and-flush per response and `--resume` skips what is on disk, so
a network failure loses at most the request in flight.

**FINAL — the full run completed, 2,902 of 2,902 records:**

| verdict | count | share |
|---|---:|---:|
| agree | **1,925** | **66.3%** |
| unverifiable (no decoded flat our side) | 971 | 33.5% |
| **disagree** | **6** | **0.2%** |

**1,634 spells state a coefficient (56%)** and **329 trigger edges** were
found. 169 ids the site does not carry or that did not parse. Agreement rose
monotonically as the sample grew (59.5% → 63.8% → 66.3%) while disagreements
stayed flat — the source is consistent with our client-derived numbers at
scale, not just on the spot checks.

⚠ **`unverifiable` is not a failure and not a pass.** Those are largely the
bucket-A spells missing from our extract, which by definition have no check
digit on our side — that is precisely why they were worth fetching. They are
recorded at weaker confidence and must never be silently promoted.

### The 6 disagreements, diagnosed — and deliberately still refused

Four are **off-by-one against the `base_points + 1` decode**: Water Nova (page
4 / ours 5), Venom Belch (1 / 2), Beam of Hatred (35 / 36), and Judgement of
Arcane Wrath. One is an **inverted range** — Twin Fang renders "3 to 1", the
same broken-tooltip class as Hammer from the Heavens' "194 to 147" (primer
v21). One is a real mismatch: Favour of the Soulflayer, page 0 vs our 30.

🛑 **The tolerance was NOT widened to absorb them.** A ±1 band would make all
four vanish, and that is exactly the "redefine the check after seeing its
result" error the gate discipline forbids. The site agrees with our `+1` decode
in **1,925** cases, so these are anomalies, not a convention difference — six
refusals out of 2,902 is the check working, not the check being wrong.

## What did NOT happen

- **3b T5 (addon), T6 (log ingestion), T7 (session automation)** — deferred by
  the owner's scoping decision, not blocked.
- **PLAN_3B §4's accessible-ceiling object** — not built. It bounds the weight
  sweep, which cannot start until §6's gate question is settled.
- **PLAN_3B §6's weight emitter** — correctly not started: the spec says build
  it only after the sim passes the gate, and the pass is currently one
  qualified character.
