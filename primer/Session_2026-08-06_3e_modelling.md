# Session `3e` — modelling, on a frozen cohort

**2026-08-06.** Work order: `primer/SESSION_3E_PRIMER.md`. Predecessor:
`primer/Session_2026-08-06_3d_hygiene_and_instrument.md`.

Seven commits, one per block or block-pair:
`68779e7` A · `735ef32` B1 · `1c07bab` B2 · `26ca87c` B3 · `c2de2a7` B4 ·
`897824f` B5+B6 · `5cad1e2` C1 · `d3829d5` C2+C5.

---

## The headline, and it is not the gate number

**The gate moved almost not at all, and the holdout moved less.**

| | pre-`3e` | post-`3e` |
|---|---:|---:|
| within ±20% (tuning set of 36) | 5 | **5** |
| qualified (≥50% coverage) | 2 | **2** |
| slice accuracy at ≥20% coverage | 64.3% | **64.3%** |
| **holdout, read once at close-out** | — | **0 of 5** |

`3e` closed **five** of the six registered engine defects, partly closed the
sixth, and found **two more** — and the pre-registered holdout barely twitched:

| holdout member | `3d` delta | `3e` delta | move | coverage |
|---|---:|---:|---:|---:|
| Qt (460) | −85.5% | −84.6% | **+0.9** | 27.9% |
| Ryno (461) | −67.8% | −67.8% | **+0.0** | 69.1% |
| Billyeye (462) | −45.7% | −45.2% | **+0.5** | 51.0% |
| Wynta (463) | −98.0% | −98.0% | **+0.0** | 1.3% |
| Iwannakissms (7661) | −87.4% | −79.4% | **+8.0** | 52.5% |

🛑 **This is recorded as the session's most informative result, not softened.**
The work order said in advance that a holdout which failed to move would be the
most useful outcome, and that is what happened. Three of the five carry
**27–69% coverage** and still miss by 45–85%, so for them this is **not** a
coverage story — it is an accuracy story, and it corroborates Block A2's
finding on characters that were never tuned against: **the sim under-produces
by roughly a third on the damage it does model.**

**What that means for `3f` onward:** the residual is not in the mechanisms `3e`
repaired. Six real defects were fixed and the answer did not move, which is
evidence about where the error *is not*. Per A2's algebra, closing ±20% needs
slice accuracy to climb from ~64% to ~100% **and** coverage from ~37% to ~80%;
neither lever alone can do it, and `3e` moved neither.

---

## Block A — make the gate readable (`68779e7`)

**A1 — the cohort is frozen, as committed data.** `candidates()` was
`ORDER BY character_id LIMIT N`, which `3d` proved is a sliding window keyed on
an arbitrary id: the gate read 5-of-41 → 4-of-38 with zero code changes when the
crawler grew the qualifying population 157 → 180. The population is now the id
set in **`predictions/cohort_frozen_3e.json`**, copied verbatim from the
committed `3d` manifest so it was fixed *before* the next result was seen.

A frozen member that stops qualifying is reported as **dropped, with its
reason** — never substituted, never silently omitted. Characters that qualify
but are not frozen in are counted (**116** today). The file read and the file
written are deliberately different: `gate_manifest.json` is the immutable record
`3e` froze from and is never written again; runs now write
`gate_manifest_3e.json`. **This run: 41 of 41 still qualify, 0 dropped.**

**A2 — the slice-accuracy reading was backwards.** `3d`'s *"cohort median 160% —
the slice is over-produced by 60%"* is a low-coverage artifact: the ratio has
coverage in its denominator and explodes as coverage → 0 (Mutaforma reports
**1,859,400%** at 0.2% coverage, and that value is in the committed manifest).
Above a real floor it is stable and points the other way — **64.3% at ≥20%,
63.4% at ≥30% and ≥50%**. The median is now reported only above a stated floor,
with the floor printed beside it, the band table under it, and the floor in the
manifest key name.

⚠ **The correction inverts the instruction the old reading gave.** At ~64%,
coverage work *alone* can never reach ±20%. Under 160% the conclusion was that
coverage work would overshoot and should be throttled.

**A3 — `within_tolerance` is `None`, not `False`, at zero coverage.** Three
cohort members (Huskeer, Jamppa, Xizek) have 0.0% coverage with a non-null
delta; the sim has no opinion about them and now says so, as slice accuracy
already did. **Owner decision 2026-08-06:** no floor above zero *this* run, so
the criterion's definition is unchanged and `3e`'s before/after pairs stay
comparable — **and a 20% coverage floor is stamped for the next gate**,
justified by slice-accuracy stability rather than by a wanted result, and
strictly harsher (it reads **2 of 36** on the run that stamped it).

**A4 — the holdout is split out of the headline.** All five ids were counted in
"n of 41", so any fix that lifted them moved the headline *and* spent the
holdout in the same number. The headline is now the 36-member tuning set; the
holdout is withheld from stdout, from the report and from the manifest unless
`--read-holdout` is passed.

**A6 — five documents that had stopped matching the tree**, including the item
the owner added to the block: `.claude/README.md` declared the >5 MB commit hook
**UNVERIFIED**; the owner ran its test on **2026-08-06** and it returned exit
`2` as specified. Recorded as verified, with the date — and with what the test
does *not* establish (that the harness is wired to call the hook, and that exit
2 aborts the commit).

⚠ **Unprompted, and the same class as everything else in A6:**
`check_sim_engine.py` never got `2c`'s `ensure_utf8_stdout()` fix, so the
regression harness crashed on a `UnicodeEncodeError` the moment its output was
piped — i.e. exactly when a session tries to read it.

---

## Block B — the six engine defects

| | defect | outcome |
|---|---|---|
| **E6** | first filler consumes the whole GCD budget | ✅ **fixed** (B1) |
| **E4** | APL grammar cannot express DoT uptime | ✅ **fixed** (B2) |
| **E5** | 6 of 7 DoTs never enter the rotation | 🟡 **pure DoTs fixed** (B3) |
| **E1** | `combo_points` never incremented, `is_finisher` never fires | ✅ **fixed** (B4) |
| **E2** | execute windows are dead code and silent | ✅ **fixed** (B5) |
| **E3** | no pet model | 🟡 **named, not modelled** (B6) |
| **E7** | mixed direct+periodic ability has no correct cast rate | 🆕 **found** |
| **E8** | the sim never reads `is_channeled` | 🆕 **found** |

**B1 / E6.** The cited line (`gcd_budget = 0.0`) was *redundant*, not wrong —
arithmetically identical to `gcd_budget - casts * occupancy` for an unbounded
filler. What was actually missing is a bound on a filler's **useful** cast rate:
`expected_cast` scores a periodic event as `duration / tick` ticks **for one
cast**, so a DoT treated as an unbounded filler is re-applied every GCD and
re-scores its whole duration each time. One allocation rule now covers every
on-GCD ability. **Gate: 5 → 4.** Only 7 of 36 characters moved and **every one
moved down** — Chastie's `+13.1%` pass became `−27.9%`, i.e. it was passing *on
the over-count*, at 4.6% coverage. **A criterion count fell because the model got
more truthful.**

**B3 / E5 — and the fixture caught an error reasoning did not.** With DoTs
entering the rotation, the predicted re-cast bug appeared on schedule (Fireball
10 casts, Living Bomb 6, Pyroblast 7 in one 68 s fight) — and the cause was **my
own discriminator**. I had treated *"has a periodic component"* as *"is a DoT"*.
**Fireball is a direct nuke with a 4 s rider**, and bounding it to one cast per
4 s models a Fire mage casting Fireball ten times a minute. The test is now
`_is_pure_periodic`, read from `events()`.

That correction exposed **E7**: a mixed direct+periodic ability has **no correct
single cast rate**. Bound by duration, the direct component starves; unbounded,
the rider is re-scored every cast. No field resolves it — what a refresh does to
a partially-elapsed DoT is unmeasured on this server. Unbounded runs and the
residual is **named per ability** in `warnings`.

**B4 / E1 — three steps, each necessary.** `is_finisher` read `cp_scaling`
alone while every real per-combo term carries **`per_combo`** (0 → 4 gated
entries). Detection alone was not enough: the finisher still cast zero times
because it sat among the *fillers* and a higher-damage filler carrying `always`
won every scan — finishers now have their own tier above the fillers. Then the
economy: `expected_hit`/`expected_cast` take `combo_points`, **read from the
APL's own gate** so the gate and the damage cannot disagree.

**Three data gaps, each named rather than papered over:**

* `SPELL_EFFECT_ADD_COMBO_POINTS` (effect 40) has **zero rows** — which
  abilities generate combo points is not derivable. `CP_PER_BUILDER_CAST = 1.0`
  is a `retail_hypothesis`, assumed once, under a name, with a warning.
* `TargetAuraState` is **absent from the extract** — which abilities are
  execute-gated is not derivable. Target health now *decays* so the window is
  reachable, and both tiers say what they cannot know.
* **Creature stats are in no client DBC at all.** They live in the server's
  `creature_template`, so **no `--with-dbc` widening reaches them.** This is the
  one `3e` gap an owner-gated extract cannot close; the route is logs
  (`ability_performance.is_pet`), i.e. PHASE_3 T6 / `3f`.

🔬 **A rule-5 finding fell out of B6:** the harness had been identifying pets by
**string-matching "summon" in the ability name** — the thing rule 5 forbids,
inside the harness that polices the rest of the engine. Against the mechanical
detector the two disagree **in both directions**: the name match returns
`Summon Felguard / Summon Void Zone / Summon Voidwalker`; the effect query
returns `Summon Void Zone` and **`Roll the Bones`**, plus two "Summon …" titles
carrying no summon effect at all.

---

## Block C — the Mage

**C1 (`5cad1e2`) — `--stat-block`.** No stat-block parser existed anywhere in
the repo; `3d`'s `required=True` made the hand transcription *compulsory* rather
than correct. `core/builds/stat_block.py` parses the export directly, verified
against both generations. `--ap`/`--sp`/`--weapon-*` are demoted to explicit
**overrides**, printed loudly on disagreement, with the refusal now covering
both paths.

The half that matters most is `ExportedAt`: `session_mismatch()` compares the
block against the log's start time (read from the **filename**, because the
lines inside carry `8/6 19:16:56` with no year). Verified in all three states —
same session silent, 33.3 h apart flagged, no timestamp says it **cannot**
check.

**C2 — the Frost Mage fixture**, built *by the parser* from a verified
same-session block, joining rather than replacing the two `3d` fixtures. It
broke something immediately (1 of 4 fillers casts — E7's third fixture) and
surfaced **E8**, with the capture settling exactly where the channel gap bites:
Blizzard casts **0 / 0 / 305** across Windows A / B / C. So every A→B comparison
is safe from it and **anything derived from Window C is not.**

**C5 — the pair ratios, re-derived through the parser.** The block parses to
AP 141 / SP 638 / weapon 543.6–646.3 @ 3.57 s — **exactly** what `3d` hand-typed,
so that transcription is now verified mechanically rather than trusted.
HftH ÷ HoJ tick predicted **1.704**, observed 1.750 and 1.707. Dawnreaver ÷
Whirling Light could not be re-run (no log pairs it with a timestamped block)
and is **provably stat-invariant** — both sides are pure weapon-percent, so the
ratio is `k₁/k₂`.

### 🛑 C3 and C4 did NOT land — spilled to `3f`, whole, not half

* **C3** (caster buff layer per ability) — the measurements exist in the capture
  README (Frostbolt ×1.027 … Frost Fever ×1.080) but landing them as a
  *derived* finding needs `calibrate_vs_log` to run on a Mage log, and it
  **refuses**: its field-alignment anchors are five Paladin abilities. That
  refusal is **fail-closed and correct** — it declines to report an unverified
  alignment — but it blocks every non-paladin log. That is `PLAN_3G`'s territory.
* **C4** (dungeon `ContentProfile`) — blocked on segmenting Window C into
  `boss_single` / `trash_bundle`, which the work order already called the hard
  part, and now additionally on **E8**: 305 channel casts sit in that window.

---

## PHASE_3's seven exit criteria, re-read honestly

| # | criterion | status |
|---|---|---|
| 1 | sim reproduces ≥3 real characters within tolerance | **MET as written** (5 of 36) — but 2 qualified against a ≥3 rider, so **EXIT NOT MET**. Unmoved by `3e`. |
| 2 | every crawled record resolves via the crosswalk; zero string matching | **Improved, not met.** `3e` removed one string match — in the *harness*, on pets. That it existed there at all is the finding. |
| 3 | inference proposes crit-table verdicts for the top ~50 abilities | **Unmoved.** Nothing in `3e` touched it. |
| 4 | ≥1 default uncertainty range replaced by a measured CI | **FAILED, mechanism still absent.** No code sets `inference.promoted=1`; `uncertainty.py`'s `POLICY` has no `measured` band. Unmoved. |
| 5 | `find_builds()` answers multi-ability queries | **Unmoved.** |
| 6 | every parse and snapshot patch/realm/season stamped | **MET**, unchanged. |
| 7 | `ContentProfile` presets derived from real encounter data | **Still FAILED.** C4 did not land, so 6 of 8 presets still carry `provenance="assumption: …"`. No back-filling by analogy was done, deliberately. |

**Four unmet, one improved-not-met, two met.** `3e` moved criterion 2 slightly
and nothing else. That is consistent with the holdout result: the session fixed
mechanisms, and Phase 3's exit is gated on magnitudes and coverage.

---

## For the owner

1. **The holdout did not move.** Six engine defects fixed, 0 of 5 holdout
   characters inside ±20%, three of them with 27–69% coverage. The residual is
   somewhere `3e` did not look.
2. **A 20% coverage floor on `within_tolerance` is stamped for the next gate**
   (your decision, taken before this run's result). It reads **2 of 36** today,
   i.e. the criterion will fail when it takes effect. That is the intended
   direction, but it should not be a surprise when it happens.
3. **Your chosen pet scope was not buildable** and the reason is structural:
   creature stats are not in any client DBC, so no extract you can run reaches
   them. Pets need log-derived profiles (`3f`).
4. **A `git add -A` briefly swept your Hammerdin proc-retest capture into one of
   my commits.** Split back out at `c7d2892` under an accurate message; nothing
   was lost. Tracker **#200295 is verified fixed** in that bundle — 0.8% → 17.2%
   combined proc rate — which unblocks the build doc §2/§11 revert.
5. **`primer/PLAN_3G_self_verifying_gates.md`** gained a third live example this
   session: `calibrate_vs_log`'s Paladin-only anchors block every non-paladin
   log. Its ordering against `3f` is still your open question.
