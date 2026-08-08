# AUDIT `3l` — ADVERSARIAL

> **`FINDING 2026-08-08`** — the oversight chat's audit of session `3l`, written the
> morning after its close against a fresh clone at `642f531`. True as of its date, not
> maintained. **Expires when `3m` closes**; its §5 is `3m`'s list. Born with this status
> line, per the `3f` F8c rule.

**Method.** Fresh `git clone --depth 40`, nothing read from the local working tree.
All three harnesses run on the clone. All three `3l` mutations (M54/M55/M56) re-applied
and re-run, then reverted (tree verified clean). Every headline number re-derived from
the committed manifests at the sha the docs cite. Two hard-rule-adjacent constants
re-derived from `data/source/dbc/dbc-extract.json` directly. The MC capture re-measured
from the bytes.

**Verdict in one line.** `3l` is the most productive modelling session the project has
had — four real mechanisms found, five predictions falsified and reported, Block C
finally landed, and every commit under a prereg that is genuinely its parent. It is also
the session whose **headline number does not survive its own lesson**, whose four
headline fixes carry **no registered check at all**, and which **seeded a mechanic the
same extract falsifies**. The honesty is intact; the instrumentation is not.

---

## §0 — What reproduced exactly

Stated first, because it is most of the session, and because a finding list read without
it is a distortion.

| claim | measured | verdict |
|---|---|---|
| prereg parenthood, all three pairs | `567a807`→`18b0d40`, `a9dbd16`→`3efba04`, `4f1ba39`→`778c892` | ✅ exact |
| `check_refusals.py` | exit 0 | ✅ (⚠ **77** arms, not the record's 74 — F11) |
| `check_core_purity.py` | exit 0, 50 files, 0 violations | ✅ |
| `check_sim_engine.py` | exit 0, refuses without the db — a verdict, not a crash | ✅ |
| census assertion `[A4]` | pasted line **equals** generated: 72 files, 13/40/7/12 | ✅ |
| M54 / M55 / M56 red counts | **2 / 2 / 1** — matches registry and record exactly | ✅ |
| the two-refusal mass = **4.08** | `f7b14af:per_ability_summary.json` → 200818 = 2.608% / 6 chars, 20424 = 1.475% / 4 chars, sum **4.083** | ✅ to the digit |
| C2 durations + provenance | `content.py:118,123` — raid 78.1 s n=33 IQR 49.3–112.1, dungeon 39.9 s n=566 IQR 26.0–59.9, query + corpus sha in the string; the five unmeasured presets keep `assumption:` | ✅ |
| median-over-mean pre-registered | yes, with means (88.5 / 49.0) and the right-skew reason, before the run | ✅ |
| gate manifest internal arithmetic | 41 = 41+0; 41 = 40+1; 35+5 = 40; holdout ids disjoint | ✅ |
| MC capture, every figure in §5 | 581,232 / 600,740 lines · 2417.379 s / 3900.606 s · gap 59.764 s · 1,177,726 events · 5,348 ALC records · horizon `19:45:34.695Z` | ✅ exact, reproduced without the parser |
| enchant chain 23387–95 → 200819–27 | present, type 3 EQUIP_SPELL, aura triple `[4,345,344]`; rank 6 aura-345 = 85+1 = **86** | ✅ exact |
| the aura-345 **conclusion** | independently corroborated: `Molten Core.txt` `SpellPower_Holy 1084 − SpellPower_Fire 740 = 344 = 2 × 86 × 2.0` (PoI) | ✅ |

The falsification discipline held under pressure: P1/P2-count/P4/P4b/C2-P2 were reported
falsified, diagnosed to mechanisms, and **not rescued**. That is the property that makes
the rest of this document worth writing.

---

## §1 — The severe findings

### F1 🚨 The headline slice move is composition, not accuracy — and the session derived that exact lesson one leg earlier. CONFIRMED

`3l` publishes **26.3% (n=23) → 30.4% (n=24)**, and P4b states the standard that reads
it: *"a median over a population whose membership your fix changes is not a fixed
target."* Applied to the whole session, from the committed manifests:

| membership held fixed at | pre-C2 `5b1dd3d` | post-B3 `29fbc1b` | post-B3b `238b9cb` | end-to-end |
|---|---:|---:|---:|---:|
| intersection of all three bands (n=22) | 30.635 | 30.425 | 30.425 | **−0.21 pp** |
| the pre-C2 band (n=23) | 26.310 | 32.440 | 27.400 | +1.09 pp |
| **as published** | 26.308 | 33.453 | 30.426 | **+4.12 pp** |

*(Reproduced independently: recomputing every published band median and `n` from each
manifest's own `cohort` array matches to 4 dp, which validates the method before the
comparison is read.)*

**The n=23 → n=23 leg is the worst of the three, and it is the one nobody tested.**
Band membership between `5b1dd3d` and `29fbc1b`: **Onur leaves** (coverage 47.7% → 7.3%,
slice 6.03 — the band's lowest) and **Deyindra joins** (coverage 10.9% → 42.1%, slice
105.43). Drop the bottom, add near the top: that is the entire +7.15 pp. The constant
`n` is what made it look safe. And **Deyindra is NOT ADMISSIBLE** (APM ratio 0.22) — the
33.5% peak was produced by a parse the project's own stamped rule refuses to score.

**In fairness, the fixes did work.** On the 22 common members, 16 moved toward 100% and 6
away; the mean went 45.74 → 50.58. The defect is that the published statistic does not
register the improvement it is being credited with — and that no same-member number is
computed anywhere. `paired_medians_same_members_at_headline_floor` reads like the control
for this and is not one: it pairs headline vs producing-only **within one run**
(`calibrate_crawled.py:1806`, a `3i` C5 selection-bias control).

**Where it is quoted bare:** `PROGRESS.md` top block and closing table; the record's §0
one-liner, the "Invariant, opening → closing" line, and §3. The P4b caveat is present and
prominent — but never at the point where the move is quoted, and never against the
upward leg.

### F2 🚨 The four headline fixes carry no registered check. CONFIRMED

`git log --name-only a97b849..642f531` touches **no test file**. `check_sim_engine.py` is
untouched across the **entire** `3l` range. `ENGINE_BUGS.md` gained M54/M55/M56 — all
three from D2, C1 and B0, i.e. all three *before* Block B opened.

Consequence, measured: reverting `WEAPON_SLOTS` to `{16,17}`, deleting the AP term, or
restoring `if mh <= 0: return` each leaves the harness **green**. The session's most
consequential behaviour change is the only part of it with no alarm on it.

Worse, F2's AP term **made an existing registered invariant vacuous**.
`check_sim_engine.py:1045-1060` (E13) is the only `expected_swing` test, and its `_CS`
fixture defines no `attack_power` — so `getattr(char_state, "attack_power", 0.0)`
(`swings.py:157`) runs the branch **off**. Run with AP added to that same fixture, E13's
ceiling breaks at AP ≈ 3,342 (1H 100-200 @2.6) and ≈ 4,828 (2H 200-400 @3.6) — and its
failure text calls a mean above that *"arithmetically impossible and can only be a unit
error"*, which after F2 it is not. The first fixture with a realistic AP reports a unit
bug that does not exist.

### F3 🚨 Righteous Vengeance's rank is discarded — 30% applied to all three ranks. CONFIRMED

Re-derived from `data/source/dbc/dbc-extract.json`, the ten-minute check rule #10 asks for:

```
53380  EffectBasePoints [9,  -1, 0]  -> +1 =  10%
53381  EffectBasePoints [19, -1, 0]  -> +1 =  20%
53382  EffectBasePoints [29, -1, 0]  -> +1 =  30%
```

`core/sim/swings.py:79` is `RIGHTEOUS_VENGEANCE_FRACTION = 0.30`, a single constant, and
`tiers.py:894` is a **membership** test over the three ids that throws away the rank the
id itself encodes. `snapshot_cards.rank` is never read.

A cohort member holding RV 1/3 is credited **3×** its real DoT. This is a direct hit on
CLAUDE.md's *"Check the rank before trusting a magnitude"* — the rule the project has
paid for twice. `3l` F3 widened this derivation's reach (removing the `mh<=0` return) and
its pool without touching the rank. Exposure is unmeasurable from a clone; the 7 RV
holders in the committed scouted captures are all 3/3, so it may be small — **but nothing
checks it**.

### F4 🚨 RV's white-crit pool is an assumption, the repo's own captures point the other way, and it enters the gate silently. CONFIRMED

F3 added white-swing crit damage to RV's pool (`tiers.py:883`, `crit_damage =
auto_crit_damage` — "the write-only field's first reader"). Its warrant:

- RV's own client description (53380–82) reads *"**Direct** critical strikes with
  **spells and abilities**…"*.
- The repo's rule for that exact wording is asserted three files away —
  `core/builds/stats.py:234`: *"primer §3; 'abilities' wording excludes auto-attacks
  (ascension_confirmed)"*.
- Nothing in `primer/`, `seed_confirmed.py` or `seed_epistemics.py` states RV's intake.

Measured against **the committed logs** (all 5 capture folders, 68 player-rows logging
61840, via `combat_log_parser.py`'s named fields, periodic crits excluded per "Direct"):

| pool definition | median implied fraction | RMSE @ 0.30 |
|---|---:|---:|
| ability-direct crit only (pre-`3l`) | 0.174 | 137,528 |
| **+ white-swing crit (`3l` F3)** | 0.136 | **153,239** |

The fraction is rank-invariant, so F3's confound cancels. **Of the 49 rows carrying any
white crit, widening the pool makes the prediction worse in 49/49.** Two-regressor OLS
through the origin gives the white-crit coefficient **−1.25**, not +0.30.

The RV warning (`tiers.py:916-920`) states the derivation, the pooling and "Cannot crit"
— it **never** says the pool now includes white crits, or that the intake is unverified.
No `open_questions` slug, no `ENGINE_BUGS` row. And it compounds F1/F2: bigger autos →
bigger `auto_crit_damage` → bigger RV, on exactly the members the session just gave
weapons to.

⚠ **The prereg's falsifier is one-sided by construction**: *"Every delta moves UP (the sim
only gains damage); any character moving DOWN falsifies the mechanism model"*
(`prereg_3l_b_tuning.md:70-71`). A mechanism that *reduced* output could not have been
registered under that clause. That is not fitting — but it is a shape worth naming
before `3m` writes its prereg.

### F5 🚨 Aura 344 is flat ATTACK POWER, and the seeded fact says otherwise — contradicting a fact seeded in the same file. CONFIRMED

`seed_confirmed.py:361` and `seed_epistemics.py:181` both state aura 344 is *"the per-hit,
speed-scaled damage parameter"* and defer it to `3m` as the delivery block. Three
independent lines say it is attack power. The first is decisive, and it is a
**structural pointer-follow, not a magnitude read from prose** — which the 2026-08-06
sharpening of the hard rule explicitly admits:

```
spell 200809 "Consecrated Weapon" description:
  "...increasing Holy Spell power by $200819s2 and your attack power by $200819s3
   Each auto attack and melee ability causes $/77;200819m1 to $/25;200819M1
   additional Holy damage, based on the speed of the weapon."
```

`$s2` = effect index 1 = **aura 345** = Holy SP ✅ (what `3l` concluded).
`$s3` = effect index 2 = **aura 344** = **attack power**.
`$m1`/`$M1` = effect index **0** — the DUMMY aura, base 410…6627, `RealPointsPerLevel`
19.0 — **is** the per-hit speed-scaled term, divided by 77 and 25.

This string is already quoted verbatim inside `seed_confirmed.py:278`
(`consecrated_weapon_imbue_grants_holy_sp_and_ap`, seeded `2d`). **Two confirmed facts in
one file now disagree.** Corroborating: aura 344 has 42 effects in the same extract,
`EffectMiscValue = 0` on all 42, and the 33 non-Consecrated ones are without exception
attack-power modifiers (Demoralizing Shout/Roar R1–R8, Curse of Weakness R1–R9,
Vindication, …).

**Consequences.** Rank 6 grants **+73 raw AP per weapon** (~+146 dual-wield), currently
unmodelled, unseeded, and absent from the buff layer. `3m`'s delivery block is scoped
around a mechanic that does not exist. And the check this opens *fails to agree*: `2e`
measured "+88 AP per imbue (post-Deadliness)" against a raw 73, implying ~×1.21 —
an asymmetry against aura 345's exact 86-vs-86 that is itself a result worth having.

### F6 🚨 `rank_for_level()` executably disagrees with the fact `3l` seeded, and nothing records the conflict. CONFIRMED

The nine hidden spells are in `dbc_spell_rank` as `line_id 1890`. Against the committed
extract:

```
rank_for_level(conn, 200824, level=60)  ->  rank 5, spell_id 200823, spell_level 56
```

i.e. **+40 Holy SP**, not the seeded +86 — because rank 6's `SpellLevel` is 64. For an
**enchant** line the correct gate is the `SpellItemEnchantment.min_level` ladder
(rank 6 = 55, rank 7 = 63), not `SpellLevel`. The measurement settles which gate is
right; nothing in `3l`'s commits or either seed records that the two disagree, so the
next caller reaching this line through the canonical resolver gets 40 and no warning.

---

## §2 — Method findings (the ones that change how `3m` should work)

### F7 C2's P1 is scored CONFIRMED and its own falsifier says otherwise. CONFIRMED

`prereg_3l_c2.md:47` — *"P1 — the gate does not move. Not approximately: to the digit.
`gate_manifest_3e.json` regenerated after the change **equals** the committed pre-C2
baseline"*. `:73` — *"**Falsifier:** any digit of P1 or P2 changing. If the gate moves at
all, the linearity claim above is wrong…"*

Diffed field-by-field, `generated_at`/`git_sha` stripped, `5b1dd3d` vs `25370b5`:

```
David   (22640)  modelled_and_producing_pct   3.2 -> 7.9
David   (22640)  keyed_but_zero_pct           4.7 -> 0.0
David   (22640)  slice_accuracy_producing_pct 415.54 -> 168.32
Frediib (40568)  modelled_and_producing_pct  46.2 -> 21.8
Frediib (40568)  keyed_but_zero_pct           0.0 -> 24.4
Frediib (40568)  slice_accuracy_producing_pct 114.47 -> 242.59
```

Frediib is a ≥20% band member and its producing-only slice **more than doubled** from a
change predicted to be a mathematical no-op. The enumerated headline items (0/35, 0
qualified, 26.3 n=23, admissibility flags, band table) all held — so the substance is
fine and the diagnosis (`_keyed_zero_reason`'s absolute `casts <= 0.001` epsilon) is
correct. What is wrong is the **scoring**: the same mechanism moved both artifacts and
only the instrument was scored. "Unchanged to the digit" is asserted in three places
(`a97b849`'s message, record §0/§2, `PROGRESS.md`) while six digits changed.

### F8 `not_scoreable_below_coverage_floor` counts 3 characters that are not below the floor. CONFIRMED

`calibrate_crawled.py:1752` tests `within_tolerance is None and has coverage`. At
`642f531` the 13 = **10 genuinely below-floor + 3 NOT ADMISSIBLE** — Boomcat at **82.2%
coverage, the cohort's highest**, Nodding 61.8%, Deyindra 42.1%. A reader reconciling
35 − 1 − 13 = 21 "scoreable" against a band of n=24 finds a 3-character gap.

This is the exact defect the key's own `3g` G4/G8 comment says the split was made to fix
— *"its NAME would have been a lie"* — recurring because `3i` D added a third reason for
`None` and the survivor key absorbed it. The **console** line at `:1094` explicitly
excludes them and calls the alternative *"actively MISLEADING"*; the shipped JSON
contradicts the console the same function prints.

Related: the headline slice median filters on **coverage only**, so it includes 3 NOT
ADMISSIBLE parses. Admissible-only: **26.31 (n=21) → 30.43 (n=20) → 27.40 (n=21)**.
Nothing states this.

### F9 Four check arms are satisfiable without the behaviour. CONFIRMED, all four run

| arm | site | mutation that leaves it GREEN | severity |
|---|---|---|---|
| `[3k-B3]` arm 4 | `check_refusals.py:976-980` | deleted the `holds_rv is None` warning branch (`tiers.py:903-907`), left the phrase in a `# TODO(3m):` comment → **exit 0, PASS**, defect fully present | 🚨 vacuous — pure `inspect.getsource` substring match, the exact M52/M53 failure mode `3k` fixed in arms 1 and 3 of the same function |
| `[3l-B0]` arm 2 | `check_refusals.py:1040` | `statistics.median` → `statistics.mean` in `per_key_table` → **PASS**. The only producing group has two ratios (0.30, 0.10) so median == mean | ⚠ fixture cannot express the claim it asserts |
| `[3l-D2]` arm 1 | `check_refusals.py:1191` | the identical signed-read regression on the sibling line (`build_dbc_index.py:897`, `slots_i[8:11]`→`slots[8:11]`) → **all three D2 arms PASS**. `amounts_max` fixture values are all non-negative | ⚠ covers one of the two fields it claims |
| `[3l-C1]` arm 2 | `check_refusals.py:1120-1124` | passes under its own registered M55 (predicate has no `rc` or `REFUSED` term; the report path prints the same substrings) | ⚠ dependent arm, not vacuous — a narrower mutation does turn it red |

Fixes are one line each: call the function and assert on the returned `warnings` list; add
a third producing row; make one `amounts_max` value negative; add `rc == 2 and "REFUSED"
in text`.

### F10 The B3b detector silently maps slot 17 to a melee off-hand, and the session record states the opposite. CONFIRMED

Predicate (`calibrate_crawled.py:394-400`): slot-15 weapon present → `{15:MH, 16:OH}`,
else `{16:MH, 17:OH}`. It is **deterministic and blind** — a pure function of
`snapshot_gear`, referencing no delta — so it passes the gate-exclusion standard. Cases
(a) 16-only and (b) 15+17 behave correctly. Case **(c) weapon at 17 only** → API branch →
17 becomes `off_hand`, **no warning**, and `wielding()` flips to `'2h'`, which turns on
path clauses: Strength `physical_ability ×1.10`, Agility `ability_crit_damage +0.20`,
Duality `all_damage ×1.06`, Intelligence `spell_haste +12`. The stray check keys on the
slot **name** (`g.slot not in ("main_hand","off_hand")`), so a promoted slot-17 row
escapes it.

`Session_2026-08-08_3l_tuning.md:227-229` says: *"Slot-17-only and stray-slot weapon rows
(36 + 8 corpus-wide) — the detector maps neither; named in `compute_stats`' warning, not
silently swung."* For the 36 slot-17-only rows **the detector does map them and no
warning names them**. ("Not swung" holds only because `swing_events` returns 0,0 with no
main hand — accidental, not enforced.) Latent for the current gate: the cohort's 41
contain no slot-17-only or {15,17} member. It is the sentence `3m` inherits.

### F11 Two documentation numbers have no owner, in the file the standing rule was written for. CONFIRMED

- The record's §7 states `check_refusals.py` **74 arms**; measured **77**. The harness
  does not print its own arm count, so per *"a magnitude never appears in a markdown file
  except as generated output"* this number has no owner. One-line fix: print
  `len(PASSED) + len(FAILURES)`.
- **`predictions/CALIBRATION_TOLERANCE.md` is `LIVE` and its derived prose is stale.**
  `3l`'s only edit to it is the 5-row band table (asserted by `[3j-C3]`); everything
  derived from that table was not regenerated: `:246` *"At **26.3%** the coverage lever is
  arithmetically dead"* (now 30.4%), `:249` *"a **3.8×** rise"* (now 3.29×), `:204`
  *"roughly **ONE QUARTER**"*, and the `3i` A5 annotation's *"37.6% (n=19) beside the
  headline 26.3% (n=23)"* against a manifest that now reads producing-only 36.65 (n=22),
  paired 30.43 / 39.94 — an annotation whose own claim is that its figures were "re-read
  from the manifest, not retyped". **The file documents this same staleness twice
  already.** This is the third occurrence. The assertion covers the table block only; the
  paragraphs around it are unprotected.

### F12 `3l`'s two false-precision / untested-condition reports. CONFIRMED

- **"the incomplete-frame warnings sit exactly at the crash boundary"** (§5) — false.
  11 warnings; half-1's nearest is **9 min 08 s** before the crash, half-2's are spread
  over 50 minutes, and the last ALC chunk is 3½ min before EOF, so it is not truncation
  either. **1 of 11** is near a boundary; the loss mechanism is scattered chunk drop and
  is unexplained. This is the `3b` *"never report a condition you failed to test"* shape.
- **Raid duration 78.1 s** — n=33 with IQR 49.3–112.1 gives SE(median) ≈ **10.2 s**. The
  change it makes (75.0 → 78.1, +4.1%) is ~0.3 SE — statistically indistinguishable from
  the assumption it supersedes — yet quoted to 0.1 s with no interval. (Dungeon, SE ≈
  1.3 s and −33.5%, is a real correction. Both are immaterial to *this* gate by C2's
  correct linearity argument; they are load-bearing for `medium_sim`/`slow_sim`, where
  DPS(median duration) ≠ median(DPS) — unaddressed.)

### F13 E1's headline invites the mis-window it was written to prevent. CONFIRMED

Every E1 fact is true. But **Gehennas has two GUIDs**, both creature entry `0x2FE3`:

| GUID | window (local) | events | UNIT_DIED |
|---|---|---:|---|
| `…000058` | 19:52:51.639 → 19:54:56.401 | 9,547 | none — **wipe** |
| `…000994` | 19:56:35.398 → 19:57:30.470 + 19:58:30.447 → 20:02:55.246 | 28,938 | one |

Two pulls, 100 s apart, both in half 1. Same pattern: Magmadar 2 GUIDs, **Garr 4**, Baron
Geddon 3 (no kill). A future ingest reading *"One pull, never two encounters"* and
windowing first-mention → UNIT_DIED spans **604 s**, folding in a 100 s wipe and 160 s of
downtime — deflating DPS on the capture whose whole value is per-parse calibration. The
follow-on sentence ("stitch on the shared GUID") is safe; the headline is not.

### F14 The aura-345 identification is a zero-residual fit, and three stronger constraints sat unused. CONFIRMED

One datum (+86) fixes two unknowns at once — which aura is the SP grant, and which rank
the owner holds. 18 candidates (2 auras × 9 ranks), exactly one equals 86, so it is
uniquely determined with **zero degrees of freedom left over** — hence no residual and no
test. *"Two fully independent routes agreeing to the point"* overstates it: they agree on
the number, and the whole agreement is spent setting the parameters. The **conclusion is
right** (§0), and the match is sharply discriminating (neighbours 40 and 141); the
criticism is about what was claimed, and about three constraints already in hand:

1. **Rank is forced without the measurement.** `Molten Core.txt:2` = `Level: 60`; the
   enchant `min_level` ladder is 15/23/31/39/47/55/63/71/79 → rank 6 is the highest
   available at 60. With rank fixed independently, +86 becomes a real 1-of-2 test between
   aura 345 (86) and aura 344 (73) — and would have caught F5.
2. **The school is a numeric field.** `EffectMiscValue[1] = 2` = `SCHOOL_MASK_HOLY`.
   Second case in the same table: Frostbrand Weapon (Passive) 965990–95 carry aura 345 at
   `misc = 16` = Frost; the 63 generic grants carry `misc = 127` = all schools. The seed
   claims "closed by a numeric field" and never cites it.
3. **Aura 345's meaning has check digits.** Eight spells state their magnitude in their
   own name and decode exactly: `Increase Spell Dam 19/21/32/91/178/180/210/309` → base
   18/20/31/90/177/179/209/308, all `+1`.

Root cause: *"Ascension-CUSTOM auras (stock 3.3.5 ids end ~316)"* is a **false warrant** —
aura 345 appears on 78 effects in this extract (Arcane Intellect R1–R7, Flametongue
Weapon R1–R10, Totem of Wrath, Fel Armor R1–R4, …), aura 344 on 33 stock spells. The
enum is partially re-indexed, not custom; "custom" was read as "opaque", which is what
made a one-number coincidence look like the only route.

---

## §3 — Smaller, carried

- **The AP term's `retail_hypothesis` label cannot reach the gate's artifacts.** Emission
  is correctly coupled (`swings.py:158-164` — term-applied ⟺ warning-emitted), but the
  pipe is `sorted({...})[:8]` (`calibrate_crawled.py:1036`) and the string ranks **56 of
  88** distinct warning literals in `core/`; `gate_manifest_3e.json` has **no warnings
  field at all**; and `core/sim/uncertainty.py:89 ENGINE_BANDS` — the registry of exactly
  this class of input — gained no entry, though the AP term moves white damage far more
  than glancing or partial resist, which are in it.
- **The retail weapon formula was applied to white swings only.** `AP/14 × speed` is part
  of weapon damage for `WEAPON_PERCENT` effects too in 3.3.5, and `ability_model.py:479`
  still takes the naked roll. The magnitude is not fitted — but the **scope of
  application** coincides exactly with the prereg's #1 target by logged mass (`auto`,
  7.638%, ratio 0.0426), while the structurally identical term elsewhere was left alone.
- **The measurement motivating F2 mixes units.** *"Ryno: sim 122/swing vs 1,382
  logged/hit"* — `expected_swing().mean` is per **attempt** (misses contribute zero, ~33%
  glance at 75%); 1,382 is per **hit**. The ~11× gap is inflated by ~`1/landed_fraction`.
  Nothing was fitted to it, so this is a reporting defect — but it is the number the
  mechanism's necessity rests on.
- **`WEAPON_SLOTS` now exists in three conventions**: `calibrate_crawled.py:207` (with the
  detector), `verify_scraped_coefficients.py:77` (still pre-B3 `{16,17}`, no detector),
  `build_nonpaladin_fixtures.py:95-100` (positional — incidentally the most robust).
- **The producing median 0.2573 (n=107) → 0.3116 (n=118)** carries P4b's caveat verbatim
  (+10.3% membership) and is quoted bare in `PROGRESS.md` and record §0. The prereg's
  ±0.02 epsilon bound was measured on a **1-row** change and is implicitly carried onto an
  11-row one. Part of the move is real: on the 62 keys producing in **both** committed
  `per_key_table`s the median of per-key medians goes 0.3790 → 0.4031.
- **`primer/CHAT_MONITORING_PRIMER.md` is `LIVE` and expired.** Its own header says
  *"Supersede at v8 when `3l` closes"*; `3l` closed and the file is untouched since
  `e820c82`. It still describes Block C as carried, AUDIT_3K as uncommitted, and the gate
  as 26.3%. This is the oversight chat's action, not Code's — **v8 is written with this
  audit** — but it means one of the 13 `LIVE` documents was false all morning.

---

## §4 — The one thing that did not get audited

`data/derived/` is gitignored, so **none of the corpus-side inputs are checkable from a
clone**: the 472 snapshots, the per-character coverage figures, the RV roster, the 27/14
convention split, the "13 of 41 simmed weaponless" count. Everything in §1 F1/F7/F8 was
derived from the committed **manifests**, which is manifest-internal arithmetic, not input
verification. F3/F4/F5/F6/F13 were derived from committed **source data** (the DBC
extract, the capture bytes) and are stronger. The reproducibility limit is unchanged and
correctly stated in the primer; it is the reason `3m` should keep widening what the
committed instruments carry.

---

## §5 — `3m`'s list, in priority order

The ranking rule: things that make a number **wrong** first, then things that make a
number **unprotected**, then the delivery work `3l` handed over.

1. 🚨 **Rescore RV by rank** (F3). Read `snapshot_cards.rank`, or map card id → fraction
   `{53380: 0.10, 53381: 0.20, 53382: 0.30}` — it is three lines, and it is a standing
   hard rule. Register a mutation (flatten the map to 0.30) with a named green path.
2. 🚨 **Retract the RV white-crit pool, or defend it with a prereg** (F4). The default
   should be retraction: it is unwarranted by the client's own wording, it is
   contradicted 49/49 by the committed logs, and it entered the gate silently. If `3m`
   keeps it, it needs an `open_questions` slug and a `warnings` line saying so. Note the
   gate consequence — this is the first change of the session that moves a number
   **down**, which is exactly why the prereg's one-sided falsifier should be rewritten.
3. 🚨 **Correct the aura-344 seed** (F5) and register the AP grant. Aura 344 = flat attack
   power, +73/weapon at rank 6; the per-hit speed-scaled term is effect **0**, rendered
   `$/77;m1 to $/25;M1`, and is *stated by the client*, not underived. Then re-check `2e`'s
   "+88 AP per imbue" against the raw 73 — the ~×1.21 residual is a finding, and it is
   the shape of a Deadliness-style multiplier.
4. 🚨 **Register a check for each of B3/B3b's four mechanisms** (F2), and repair E13's
   fixture so it exercises the AP branch. Four mutations: `WEAPON_SLOTS` → `{16,17}`;
   delete the AP term; restore `if mh <= 0: return`; force the detector to one branch.
   Name the green path for each and **run it**.
5. 🚨 **Publish a same-member slice number** (F1) — add a `slice_delta_same_members`
   block to the manifest keyed to the previous run's band, and quote the pair
   (published, same-member) everywhere the move is cited. Then correct the `3l` headline
   in `PROGRESS.md` by appending: published +4.12 pp, same-member **−0.21 pp**.
6. ⚠ **Rename `not_scoreable_below_coverage_floor`, or split it** (F8) — the JSON
   contradicts the console the same function prints. And publish the admissible-only
   slice beside the headline.
7. ⚠ **Fix the four soft arms** (F9), one line each. `[3k-B3]` arm 4 is the urgent one —
   it is a pure source-text match on a function whose warning branch can be deleted.
8. ⚠ **Correct the record's slot-17 sentence and add the warning** (F10) — key the stray
   check on the slot **index**, not the mapped name, so a slot-17-only snapshot cannot
   become an off-hand.
9. ⚠ **Rescore C2's P1 as falsified-and-diagnosed** (F7). The substance is fine; the
   scoreboard is what the discipline is for. And regenerate `CALIBRATION_TOLERANCE.md`'s
   derived prose (F11) — extend `[3j-C3]` past the table block, or move the derived
   sentences into generated output.
10. **E2 with a full horizon** — the handoff item. ⚠ Before running it, resolve F13:
    window on **GUID**, and pick the kill GUID explicitly, or Gehennas ingests as 604 s.
11. **Delivery modelling** (B5) — with F5 applied, the block is: seal per-proc (20424,
    35% weapon, Holy, delivery-blocked not extraction-blocked), imbue per-hit (effect 0,
    divisors 77/25 — *stated*), Plague Swarm 276445 (146× gap), school-variant autos,
    Deep Wounds/Ignite/diseases.
12. **Carried, unchanged:** Devour Mind 287865 (6.63%, largest single absent key — third
    deferral); Elemental Blast 954892 mechanism; the holdout stays unspent (0 passers,
    correct call); one `--with-dbc` run remains the staleness clock.

---

## §6 — Tone note for the next session

`3l` falsified five of its own predictions, diagnosed every one, rescued none, and put the
sharpest lesson of the session (P4b) at the top of `PROGRESS.md` in bold. That is the
behaviour this project is built to produce, and it is why the findings above were
findable at all — every one of them was reached through an artifact `3l` itself committed.

The pattern worth naming is narrower than "be more careful": **`3l` reasoned excellently
about the numbers it was watching and left the numbers it was not watching unguarded.**
P4b was derived and then applied to one leg. The epsilon was diagnosed and scored to one
artifact. The rank rule was honoured for the card-id space and skipped for the card's own
magnitude. The `+86` was verified and the `+73` beside it was asserted. In each case the
missing half was in hand.

The cheapest structural fix is the one CLAUDE.md already states and `3l` skipped for its
headline work: **no mechanism lands without a registered mutation.** Four checks would
have caught F2, F3, F4 and F10 before the close-out.
