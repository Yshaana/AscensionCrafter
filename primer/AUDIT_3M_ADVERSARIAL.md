# AUDIT `3m` — ADVERSARIAL

> **`FINDING 2026-08-08`** — the oversight chat's audit of session `3m`, written the same
> day against a fresh clone at `c821841`. True as of its date, not maintained. **Expires
> when `3n` closes**; its §5 is `3n`'s list. Born with this status line, per the `3f` F8c
> rule. ⚠ Commit this file to `primer/` at `3n` pre-flight (census moves).

**Method.** Fresh `git clone --depth 80`, nothing read from any local working tree. All
three harnesses run on the clone; `ascension.db` rebuilt from committed source
(`cli/rebuild.py`, 21 steps, exit 0) so `check_sim_engine.py` ran its full arm set rather
than refusing. **Eight registered mutations re-applied, re-run and reverted** (M60, M61,
M63, M64, M67, M68, plus the audit's own named mutations for the repaired `[3l-B0]` and
`[3l-D2]` arms), tree verified clean after each. Every headline number re-derived from the
committed manifests at the sha the docs cite; the gate's same-member claim recomputed
independently from each manifest's own `cohort` array. Five hard-rule-adjacent constants
re-derived from `data/source/dbc/dbc-extract.json` directly. The MC capture's encounter
windows re-measured from the bytes with an independent parser.

**Verdict in one line.** `3m` is the cleanest session of this arc under audit: **every
number checked reproduces to the digit, every mutation is real and goes red, the deadline
was met before the patch, both falsifications were reported and diagnosed to one mechanism,
and the same-member instrument landed and told the truth on its first outing.** Its
defects are all at the seams: **two sibling seeds still assert facts this session's own
repairs falsified** — including the exact line `AUDIT_3L` F5 named — and the headline
"13 of 15" tally is a hand count no committed artifact reproduces.

---

## §0 — What reproduced exactly

Stated first, because it is nearly the whole session.

| claim | measured | verdict |
|---|---|---|
| prereg parenthood, all three pairs | `196838c`→`9267660`, `dee3ebd`→`fd11099`, `263e6db`→`766b269` | ✅ exact |
| `check_refusals.py` clean tree | exit 0, **87 arms / 87 passed** | ✅ |
| the 87-clean / 91-dirty arm-count mechanism | every dirty-tree mutation run in this audit printed **91 arms**; the clean baseline 87 | ✅ reproduced from this audit's own logs |
| `check_core_purity.py` | exit 0, 52 files, 0 violations | ✅ |
| `check_sim_engine.py` | refuses by name without the db; **exit 0 with the rebuilt db** | ✅ |
| census `[A4]` | `75 files — 13 LIVE / 41 HISTORICAL / 8 SUPERSEDED / 13 FINDING`, asserted by the harness | ✅ |
| A4 baseline → C pair gate move | recomputed from the manifests' own cohort arrays: **30.425 → 30.040 (n=24), published −0.385 pp, same-member −0.385 pp, membership unchanged** (B pair: unchanged to the digit) | ✅ exact — the headline equality is real |
| `slice_delta_vs_previous_run` (A1) | implementation intersects on `character_id`, uses each run's own committed values, refuses with no previous manifest; matches independent recomputation | ✅ sound |
| `not_scoreable_by_reason` split (A2) | manifest carries `zero_coverage` 1 / `below_coverage_floor` 10 / `not_admissible` 3, by name | ✅ |
| absent share / producing median | `per_ability_summary.json`: absent **58.8%**, producing **0.3234 (n=117)** | ✅ (⚠ "58.83" — F3) |
| Block D windows, from the bytes | Gehennas 2 GUIDs, name-window **603.6 s** vs kill GUID **379.8 s**; Garr **4 GUIDs**, **2,138.6 vs 382.6 s (5.6×)**; Geddon 3 GUIDs no kill; Magmadar wipe-then-kill; crash gap **59.8 s**; logged **320.1** vs wall **379.8** | ✅ every figure exact, independent parser |
| B5 arithmetic, owner's build | `0.65×645.8+62 = 481.8`; weapon **87.13%**; card at 3/3 **578.1 → 74.4 (−87.1%)**; LC **−47.5%** | ✅ exact |
| Improved Cleave rank decode | `EffectBasePoints` 39/79/119 → +40/80/120%, aura 108 op 8, all three rank ids in `BONUS_TERM_ONLY_TALENT_IDS` | ✅ re-derived from the extract |
| Lightbound Cleave decode | BP `[61, 64]` → flat **62** + **65%** weapon | ✅ — the `9+AP` retraction is right |
| RV rank ladder | 9/19/29 → 10/20/30%, mapped by card id in `swings.py:93`; unknown-ownership path warns UPPER BOUND | ✅ |
| aura 345 / 344 at rank 6 | BP 85→**+86** (Holy SP), BP 72→**+73** (AP) — C3's magnitudes | ✅ re-derived |
| CALIBRATION_TOLERANCE derived figures | `<!-- GENERATED -->` block **equals** `render_band_table.py` output byte-for-byte; surviving 26.3/30.4 mentions are all historical narration; the derived prose is de-numbered | ✅ — third staling should be the last |
| canary carry-over fix (pre-flight) | the "audit's proposed fix does not work" claim verified against the committed captures' own numbers: yield ~3%→1% is population collapse (198 of 200 MC queries legitimately empty), invisible to every structural denominator; carry-over test is the correct shape | ✅ — the audit's own §5 proposal is superseded, correctly |

**Mutations re-run by this audit — all red, all reverted green:**

| id | result |
|---|---|
| M60 | ✅ red 1 — and the **isolating** property is real: with the branch deleted and the phrase left in a comment, the repaired arm fails while the old source-text arm would have passed |
| M61 | ✅ red 2 (`[3m-B]` both arms) |
| M63 | ✅ red, exit 1 — ⚠ but see F4: the registry names the wrong file |
| M64 | ✅ red 1, asserted as arithmetic (400 vs 100) |
| M67 | ✅ red 2 |
| M68 | ✅ red 1 — re-implemented as a plausible longest-attempt fallback per the registry's own note, not a crash |
| `[3l-B0]` median→mean | ✅ red — the fixture's third producing row landed |
| `[3l-D2]` sibling signed-read | ✅ red — the negative `amounts_max` fixture value landed |

The four `AUDIT_3L` F9 soft arms are genuinely hardened; the remaining
`inspect.getsource` uses in the harness are AST-structural, not comment-satisfiable.
The falsification discipline held: P3/P5 were reported falsified, diagnosed to one
mechanism (the APL units mismatch), and the fix was **deliberately not** smuggled into
the results commit.

---

## §1 — The findings

### F1 🚨 `seed_epistemics.py:181` still asserts the falsified aura-344 mechanic — the exact line `AUDIT_3L` F5 named. CONFIRMED

C3 corrected `seed_confirmed.py:361` (aura 344 = flat attack power, per-hit term =
effect 0, divisors 77/25 — verified exact in §0). But `AUDIT_3L` F5 named **two** sites,
and the second is untouched: `seed_epistemics.py:181` still reads

> *"STILL OPEN: aura 344 (R1 19 .. R6 73 .. R9 132) is **the per-hit damage parameter**
> and its formula ('based on the speed of the weapon') is underived…"*

`git log 851fc64..HEAD` touches `seed_confirmed.py` twice and `seed_epistemics.py`
**never**. Consequences: the two seed files now disagree about the same aura — the `3l`
F5 shape ("two confirmed facts in one file disagree") promoted to file scope; every
rebuild loads the stale text into `open_questions`; and a `3n` session reading the open
question as scoped will re-inherit the mechanic C3 just killed. The repair is one
sentence, and the standing rule ("when a verdict changes, edit the seed **in the same
session**") already covers it.

### F2 🚨 `improved_cleave_modifies_all_effects_not_just_the_flat` still states the bug-declared delivery as DECISIVE truth, in the same file as the corrected seed. CONFIRMED

`seed_confirmed.py` (~line 205) still carries the `2b` verdict, unannotated:

> *"DECISIVE… its +40 percent per rank applies to EVERY EFFECT… roughly 1,033 per hit —
> an increase of about 563 per hit… The card is excellent because it multiplies a large
> weapon-damage component."*

Twenty-odd seeds below it, `improved_cleave_true_magnitude` (updated this session) says
the opposite: bonus-term-only by owner decision, the whole-ability ×2.20 declared a bug,
card contribution **74.4** per hit. Two confirmed facts in one file disagree — in the
Block whose whole purpose was reconciling this seed with this code. Same repair class:
annotate the `2b` seed as describing the **pre-2026-08-10 delivered** behaviour (it is
historically correct — M61's note even says so) rather than current truth.

Related, smaller: `frostbound_cleave_identified_for_winds_of_winter_stack` still carries
`weapon_dmg*0.65 + (9+AP)*2.2` and predicted hits (973/700/606) derived from the
**retracted** `9+AP` magnitude. It is labelled PREDICTED, but its formula cites a seed
that no longer says that.

### F3 ⚠ The headline tally "13 of 15 predictions confirmed" has no owner and no committed derivation. CONFIRMED

Counted directly from the three preregs' own scored tables: **B 7 + C 7 + D 6 = 20
predictions; 17 confirmed, 2 falsified, 1 split** (B's P6: tail exact, magnitudes
falsified). "13 of 15" reproduces only under one unstated counting — drop the five
"gate does not move" predictions *and* score the half-falsified P6 as confirmed — which
resolves an ambiguity in the flattering direction. This is the arm-count lesson (`AUDIT_3L`
F11) recurring **inside the very close-out that fixed the arm count**: a magnitude in a
document with no tool emitting it. Same class, same fix: have the close-out quote
per-block counts from the prereg tables ("B 4✓/2✗/1 split · C 7/7 · D 6/6"), which is
reproducible by reading, or print the tally from a tool.

Also in this class: the record and `PROGRESS.md` quote absent share **58.83%** while the
committed artifact (`per_ability_summary.json`) emits **58.8** — the extra digit exists
in no committed output.

### F4 ⚠ ENGINE_BUGS registers M63 at a site that does not exist. CONFIRMED

The M63 row reads `core/sim/tiers.py :: WEAPON_SLOTS = {16…, 17…}`. `WEAPON_SLOTS` lives
in `tools/audit/calibrate_crawled.py:207`; `tiers.py` has no such constant (measured: the
registered edit applied to `tiers.py` is a no-op and the harness stays green). Applied to
the real site, the mutation is red as claimed — the defect is registry accuracy, not
check vacuity. One-line fix; worth doing because the registry is the document a future
session uses to re-run reverts, and a no-op green is exactly the false comfort the
mutation table exists to prevent.

---

## §2 — Smaller, carried

- **`primer/CHAT_MONITORING_PRIMER.md` (v8) expired at `3m`'s close by its own
  condition** ("supersede at v9 when `3m` closes"). This is the oversight chat's action,
  not Code's — v9 accompanies this audit — but for the record: one of the 13 `LIVE`
  documents is past its stated expiry until v9 lands in the tree.
- **`verify_scraped_coefficients.py` still carries the pre-`3l` `{16,17}` map** — the
  third slot convention. Named by a registered check arm rather than silently aligned,
  and it feeds no gate artifact; a deliberate, stamped NOT-done. Fine, carried.
- **The APL units mismatch is measured, not fixed** — correct per the no-rescue rule
  (changing it inside the falsified prereg's results commit would have been rescuing).
  It is `3n`'s largest item; the code confirms the mechanism (`apl_gen` ranks fillers by
  `-s["mean"]`, damage per **cast**, while `is_next_swing` abilities cast on the swing
  clock).
- **B P2's same-member delta printed +0.001 pp on a predicted 0.000** — rounding at the
  2-dp cohort serialisation, visible in this audit's own recompute (30.4250 vs 30.4263).
  Harmless today; worth one decimal more in the manifest's stored per-row values if the
  instrument is ever read at that precision.

## §3 — What this audit could not check (standing reproducibility limit)

`data/derived/` is gitignored, so corpus-side figures are unverifiable from a clone:
C2's cohort-wide re-measure (worse in **1,416 of 1,852**, implied fraction **0.2004**),
the APL exposure count (**15 of 41** members, 11 next-swing ids of 530), and the RV
holder census (12 holders, exactly 2 at rank 2). Everything checked here came from
committed manifests, committed source data (DBC extract, capture bytes) and function
behaviour under fixtures — the strong ground. The limit is unchanged and correctly
stated in the primer.

---

## §5 — `3n`'s list, in priority order

0. **Pre-flight, before anything gate-capable — fix the two stale seeds** (F1, F2):
   one sentence in `seed_epistemics.py:181`; a dated annotation on the `2b`
   ALL_EFFECTS seed (+ the Frostbound formula citation). Census + rebuild. Also correct
   ENGINE_BUGS M63's site (F4) and the "13 of 15" / "58.83" prose (F3).
1. 🚨 **The APL units mismatch** — the largest measured modelling error left
   (18% of Blix's sim; 15 of 41 members exposed). Own prereg; rank fillers by damage
   per unit of the clock that limits them (GCD abilities per GCD-second, next-swing per
   swing); predict per-member direction; register the mutation (rank by per-cast again).
   Expect the producing median and slice to move; quote the published + same-member pair.
2. 🚨 **E2 — run `infer_coefficient` inside the landed GUID windows** (third carry,
   stamped). The windowing refuses ambiguity and reports wall vs logged; the six Elric
   stat blocks are phase-resolvable. This unblocks Phase 3 criteria 3-full and 4.
3. **Delivery modelling** — still the load-bearing problem at **58.8% absent**,
   dominated by trigger-delivered damage: seal per-proc (20424), imbue per-hit
   (effect 0, divisors 77/25, *stated*), Plague Swarm 276445 (146× gap), school-variant
   autos, Deep Wounds/Ignite/diseases. With C3 landed, model the **+73 AP per weapon**
   grant while in there (seeded, not yet modelled) and name the ×1.21 residual's test.
4. **Devour Mind 287865** — largest single absent key (6.63%), now at its **fourth**
   deferral. Register it or explain it; a third "carried, unchanged" line is what the
   deferral rule exists to prevent.
5. **The Monday split, date-aware** — the B prereg named (and deferred) applying the
   Improved Cleave impairment only to pre-2026-08-10 parses. Any capture taken from
   Monday onward needs it before it can join any comparison with the frozen cohort.
6. **Carried, unchanged:** holdout unspent (0 passers, correct); predicate 2 UNARMED by
   owner decision; one `--with-dbc` run remains the staleness clock;
   `verify_scraped_coefficients`' third convention (named by arm).

---

## §6 — Tone note for the next session

`3l`'s pattern was "excellent about the numbers it was watching, unguarded about the
numbers it was not." `3m` broke that pattern where it mattered — the instrument now
watches the composition question automatically, the mutations now exist and are sharp
enough to isolate (M60 is the best mutation in the registry), and a falsified prediction
was diagnosed without being rescued. What `3m` did not do is **finish its own
corrections' blast radius**: each repair updated the primary site and left a sibling —
the second seed file, the `2b` seed twenty lines down, the registry row's path, the
tally in the close-out prose. The next session's cheapest discipline is the one C3's own
seed text states: *when you correct a fact, grep for its siblings before you commit.*
