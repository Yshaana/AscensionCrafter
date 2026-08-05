# Session `2d` — Residuals, buff model, scorecard spec (slots BEFORE `3a`)

**Origin:** chat review session 2026-08-05 (post-`2c` audit + halfway confidence analysis).
**Status:** planned · **Blocks:** `3a` must not start until 2d's T1–T5 are done or explicitly
deferred with a recorded reason.

STARTING POINT — read these first, in order:
1. `primer/PROGRESS.md` — current position and the `2c` inheritance block.
2. `primer/Session_2026-08-05_2c_gates_and_talents.md` — the school residual, the demoted 1.31,
   the weapon-free pair ratios (1.718 / 0.769) that are now the calibration targets.
3. `primer/NEXT_CAPTURE.md` — the owner's capture bundle. **T1 consumes it.**
4. `predictions/CALIBRATION_TOLERANCE.md` — the recorded gates. All three thresholds, not one.
5. This file, in full. Dependency-ordered; later tasks assume earlier ones.

## Why this session exists

The halfway confidence analysis found the plan's two load-bearing gaps are not on the plan as
named tasks: **(a) the school-grouped calibration residual (~1.86 Holy / ~1.37 Holystrike) has no
owner** — it blocks cross-school ranking, which is the core act of classless theorycrafting — and
**(b) there is no buff model anywhere in the stack**, despite buff state moving calibration 1.41×
between the owner's own sessions and content profiles carrying a decorative
`raid_buffs_available` flag. Both were on track to be "resolved by accident inside 3a," which is
the exact pattern that produced the Tdoctor and 1.31 lessons. This session names them.

It also lands a batch of decisions made in the same review (scorecard, volatility rework,
terminology, generation constraints) so `3a` and the eventual Phase 4 doc inherit them as
settled rather than re-deriving them.

---

## Decisions ledger (owner, 2026-08-05) — record these, do not relitigate

| # | Decision |
|---|---|
| D1 | **Enjoyment modelling: CUT.** Playability is preference, not merit. No "fun" score anywhere. Complexity survives only as a neutral difficulty *descriptor* (T6), never in the merit tally |
| D2 | **"Above average" is operationalized as the Build Scorecard** (T6): 10 axes × 10 = 100, performance axes percentile-anchored against the crawl population |
| D3 | **Build generation: exclusivity-bucket conflicts are ALLOWED, warned, and scored as the game scores them** — only the highest bucket member applies in the math. The **slot budget (30 abilities / 25 talents) stays a HARD constraint** — game rule, not preference. The analysis path (modelling someone else's board) keeps warn-only behavior |
| D4 | **Calibration gate before generation:** Phase 4 emits NO cross-school ranking until the school residual is explained — either modelled (buff/Path/enchant) or per-school calibration lands within `CALIBRATION_TOLERANCE.md`'s recorded thresholds. Write this into PHASE_2 §8 and carry it into the Phase 4 doc when written |
| D5 | **Guide staleness: DEFERRED to the display/share phase**, with this carried forward: every guide carries its patch stamp, and the existing verified-at-patch sweep can flag "a spell this guide references was patched since publication" — display only needs to surface that as a warning banner. Nothing to build now |
| D6 | **Terminology: "lego" → "kit".** Two-tier vocabulary: a **chassis** (large shared base of build variants — existing usage, unchanged) is composed of **kits** (measured, coupling-based card clusters, possibly cross-class). Rename footprint in T7 |
| D7 | **Volatility becomes recency-weighted** (T8): exponential decay, half-life 90 days, direction multipliers. Parameters are stated priors, tunable — flagged as such in code and docs |

---

## Task 0 — 🔴 FIRST ACTION: present the owner ONE consolidated in-game task list

Before any code, compile and present the complete list of in-game actions this session (and 3a)
needs from the owner — **compiled fresh from the current docs at session start, not copied from
this file**, because open items move. One list, priority-ordered, so the owner can do a single
efficient in-game pass instead of being asked piecemeal across sessions. Sources to sweep:

1. **`NEXT_CAPTURE.md`, all of it** — the stat block + two logs (item 1–2), **and the tooltip
   groups A–D** (unresolved damage sources incl. Righteous Vengeance 61840 / Consecrated Holy
   Weapon 200818 / Arcing Light 954923; the two question-settling tooltips — Holy Shock R4 and
   Lightbound Cleave R5; the six unknown-aura + four server-script talents; Brutal Crusader and
   Dawn Strike R8). The restart-state note travels with it.
2. **Standing in-game items from PROGRESS' open-questions table:** the armor-pen divisor
   (5 vs 4.2 — one character-sheet hover), Fel Infused Weapon's per-level term (db 4.5 vs DBC
   1.5 — one tooltip), and one *capped* level-scaled spell's tooltip vs the computed value
   (confirms the engine applies `min(level, max_level)`).
3. **Anything `audit_gaps.py`'s latest report flags as settleable only in-game** (conflicts,
   `class_origin` disputes with a proc-test protocol, etc.).
4. Anything T1–T3 of this file will predictably need that isn't covered above.

Present it grouped by *where in-game the owner will be* (character sheet reads / city tooltip
reads / dungeon runs) — that's the shape that makes one pass efficient. ⚠ Per the standing
haste-adjustment rule: **every tooltip read needs the stat state noted alongside it** — a
tooltip measures the character, not the spell; the same-session stat export covers this if the
reads happen in that session.

🛑 Do not start T2+ implementation before this list has been delivered — the whole point is
that the owner can go play while the session codes, and hand results back before it ends.

## Task 1 — 🔴 consume the capture bundle (owner-dependent)

`NEXT_CAPTURE.md` already instructs asking for this first thing; T0's list supersets it. When
the bundle arrives:

1. **Record restart state.** The 73-entry `[Pending Restart]` balance pass may or may not be live.
   The owner was asked to note it; if the note is missing, 🛑 ask before using the logs — a
   mid-bundle restart reintroduces exactly the mismatch the bundle exists to remove.
2. Ingest the stat export (same-session weapon damage, AP/SP, crit/hit/haste, Str/Agi/Int,
   **active Path**, full board with ranks) as tier-1, `source='user_provided'`.
3. **Re-run absolute calibration with same-session inputs.** This is the first calibration in the
   project's history with no stale-input confound. Report against **all three** recorded gates
   (aggregate ±20%, per-ability share ±15%, per-ability non-crit ±25%) — `2c` reported only one.
4. **Settle `elric_active_path_and_duality_ap_anomaly`** from the stated Path.
5. **Test the residual's shape:** if per-ability logged/modelled is again school-grouped near
   ~1.86 / ~1.37 with same-session stats, the missing factor is **structural** (Path grant,
   school amplifier, enchant) — not session buff state. That was `2c`'s pre-registered
   falsifiable prediction; reconcile it in the ledger either way.

🛑 If the bundle isn't available this session, T1 blocks and is recorded in "Blocked on the
user"; T2–T9 proceed regardless (none depend on it).

## Task 2 — buff/aura state model (the named task, finally)

A first-class `core/sim/buffs.py`, same discipline as `talents.py`:

- **Model the states that plausibly explain the residual and the 1.41× session swing:** active
  Path grants (Duality's SP amplification — read magnitudes from the capture, never assume),
  Avenging Wrath / Vengeance-style uptime windows, raid buffs, consumables, and **gear enchants
  with damage/school effects** (Brutal Crusader's magnitude is a standing open item — if it's a
  school amplifier, enchants are a modeling domain, not a footnote).
- `char_state` gains a `buff_state`; `raid_buffs_available` in content profiles stops being
  decorative — each profile maps to a concrete buff set with per-buff provenance.
- **Every unconfirmed magnitude is a named warning, not a default.** A buff modelled at an
  assumed value is the fabricated-precision trap wearing a new hat.
- Uptime-windowed buffs (Avenging Wrath) belong in the medium/slow tiers' timelines; static
  multipliers can apply in fast. Both tiers read one shared buff definition — the 2b "one
  formula model, two rigor levels" rule applies here identically.
- Exit test: with the T1 capture's known buff state, the per-log absolute multiplier spread
  should shrink from 1.41× toward the pair-ratio noise floor (~3–6%). Report the before/after —
  a partial shrink is a finding, not a failure.

## Task 3 — close the 2b sim gaps (melee-side bias)

These four were named in `2b`, not closed in `2c`, and they bias rankings **against melee-lean
builds specifically** — a systematic error, worse than a uniform one:

1. **Seals per swing, not per cast.** Requires a swing timer (weapon speed ÷ haste) in the
   medium/slow tiers; seals ride landed swings through the attack table the combat engine
   already has. Validate against logged Seal of Command — it logs as **20424** (id-keyed,
   per `2c` G3; never name-matched).
2. **Auto-attacks modelled.** Small (~4.2% per the build doc) but structural — the swing timer
   from (1) makes this nearly free.
3. **Righteous Vengeance's 30% crit-damage DoT** (logs as **61840**). Build doc measures it at
   6.4–9.0% of damage. Aura-tick rule applies: 0% crit on the DoT itself.
4. **Judgement resolves to no current-pool card.** Investigate how Elric actually casts it —
   likely a baseline non-card ability, which the build spec currently can't represent. If so,
   add baseline-ability support to `BuildSpec`; 🛑 if the logs are ambiguous about which
   Judgement id fires, ask rather than pick.

## Task 4 — extract-staleness sweep in `audit_gaps.py`

New sweep: **latest client-DBC extract date vs latest Darkmoon patch date.** A client patch can
silently stale the entire numeric layer, and nothing currently notices — `data_version()` hashes
*our* tables, which stay byte-identical while the server changes underneath them. Flag when a
patch postdates the extract; the fix is always "owner re-runs `--with-dbc`," so the flag should
say exactly that. The pending 73-entry balance pass makes this immediately real.

Also: seed `predictions.patch_id` on the three existing rows (column exists, all NULL) and make
it required-with-a-warning for future rows — a prediction that can't say which balance state it
was made under loses its meaning at the first restart.

## Task 5 — doc hygiene (audit findings, all small)

1. **The orphaned exit criterion:** PHASE_2's exit-criteria list still reads "reproduces ≥3 real
   characters" unamended, and PHASE_3 never carries the inherited gate as a task. Amend the
   PHASE_2 list to reference §8.2's move; add the ≥3-character calibration gate to
   PHASE_3 as an explicit task with the gear dependency stated.
2. **"Blocked on the user" table** in PROGRESS currently says *nothing open*. It should list the
   capture bundle (until T1 consumes it) and `holy_shock_bonus_coefficient_0429` (owner decision
   needed before seeding).
3. **The 1.31 marker:** `predictions/pred_2026-08-05_elric_paladin.md` still states 1.31 as "the
   number a correct talent model must reproduce." Append-only discipline: do not edit the
   original text — append a dated ⚠ note pointing at `2c` G1 (confounded; superseded by the
   weapon-free pair ratios 1.718 / 0.769).
4. **Check count:** `check_sim_engine.py` has 40 `check(` call sites (two names duplicated);
   PROGRESS/handoff say 38. Fix the count where quoted, and de-duplicate the two names so the
   count is honest going forward.
5. **Refresh `CHAT_MONITORING_PRIMER`** (if repo-committed; otherwise emit an updated copy for
   the owner to re-upload): current through `2c`+`2d`, next session `3a`, model guidance updated.

## Task 6 — `SCORECARD.md` spec (design doc, no implementation yet)

Write `primer/SCORECARD.md`. Implementation lands with Phase 4; the spec lands now so 3a knows
what population data it must produce. Content:

**Ten axes × 10 = 100.** Performance axes are **percentile-anchored** against
`character_scenario_dps` (5/10 = population median by construction — "above average" becomes
measurable, not vibes). Every axis names its data source; any axis with unconfirmed inputs
shows a confidence marker, never a fabricated number.

| # | Axis | Source |
|---|---|---|
| 1 | Single-Target | sim `patchwork` percentile vs crawl distribution |
| 2 | Cleave | sim `cleave` percentile |
| 3 | AoE | sim `aoe` percentile |
| 4 | Burst | medium-sim timeline windowing (best 10s / mean 10s) |
| 5 | Consistency | inverse RNG dependence — combat-RNG band width, proc-chain damage share |
| 6 | Survivability | kit analysis: mitigation, self-heals, sustain (healing terms already extracted) |
| 7 | Support | buffs/debuffs/utility brought — relationship graph + aura categories |
| 8 | Accessibility | acquisition model: chase-card count, essence cost, RNG roll depth (Phase 4) |
| 9 | Gear Scaling | DPS slope per gear tier (§2.10 curves + 3a `items`) |
| 10 | Volatility | recency-weighted patch risk (T8), damage-share-weighted over the board |

**Complexity is OFF the tally** — computed 1–10 internally (APL button count, conditionals,
procs/timers tracked, GCD pressure), displayed only as a neutral difficulty badge:
1–2 Very Easy · 3–4 Easy · 5–6 Moderate · 7–8 Hard · 9–10 Very Hard.
Guide header form: **`74/100 · Difficulty: Hard`**.

**Confounds to state in the spec** (they gate axes 1–3 and shrink as 3a lands): crawl records no
character level; target count is inferred; buff state unnormalized; gear unbracketed. Launch
those axes marked low-confidence; tighten as each confound resolves.

## Task 7 — terminology rename (D6)

`lego` → `kit`, everywhere forward-looking: ARCHITECTURE.md layer 4 ("Lego Box" → "Kit
Library"), planned `core/legos/` → `core/kits/` (not yet created — a doc edit), the
"lego definition corrected" plan-changes row gets a dated terminology note (do not rewrite
history — annotate), Scorecard axis 8 wording, and this file's own vocabulary. Definition
unchanged: a kit is a **coupling-based cluster** of cards measured to work together, possibly
cross-class; a **chassis** is the large shared base multiple build variants sit on.

## Task 8 — volatility rework (D7)

Amend `core/spells/volatility.py`:

```
weight(touch) = direction_mult × 0.5^(age_days / half_life)
score         = Σ weights over the realm-scoped touch history, banded
```

- `half_life = 90` days (stated prior — 60–120 all defensible; record the choice, make it a
  parameter).
- `direction_mult`: nerf **1.5** · rework **1.25** · buff **0.75** · neutral/unknown **1.0**.
  Stated priors, not derived — flag in the docstring and INDEX_GUIDE; revisit when history is
  deep enough to test whether nerfs cluster.
- Rationale worth encoding in the docstring: 2 nerfs at ~45 days ≈ 2.1 weighted; 6 changes at
  4 years ≈ 0 — recency ordering the flat rate got backwards.
- The `data_thin` honesty block **stays** until `data_window_days` exceeds ~2 half-lives, then
  notes itself moot: decay makes the thin-window problem self-healing (anything older than
  ~9 months is <6% weight regardless of whether it was captured).
- Keep it report-only, Darkmoon-strict, per the 1c owner decisions — this changes the *formula*,
  not the scope.

## Task 9 — write D3 and D4 into the standing docs

- D4 (calibration gate) → PHASE_2 §8, plus a forward note wherever the Phase 4 doc stub lands.
- D3 (generation constraints) → recorded in INDEX_GUIDE or the future Phase 4 doc: buckets
  allow + warn + highest-member-only scoring; slot budget hard. **Prerequisite noted:** the
  talent model must implement highest-member-only bucket scoring before generation exists —
  today it warns and over-values. If cheap, implement it in `talents.py` this session (the
  bucket data is step 9 of the rebuild); at minimum, run the bucket check against **Elric's own
  ~24 slotted cards** — Answered Prayers' +10% is most of the modelled ×1.155 and sits in a
  documented bucket, so this either confirms or shrinks the only talent number the sim has.

## Task 10 — full documentation sync (LAST, not optional)

Every doc that states something 2d changed gets updated **in the same session**, before the
handoff is written — drift between docs and reality is the project's named most-expensive
failure mode. Checklist, each item confirmed or marked n/a in the handoff:

| Doc | What 2d changes in it |
|---|---|
| `PROGRESS.md` | Current position (2d done, 3a next + what 3a now inherits); Blocked-on-user table reflecting T0's list state (delivered / partially answered / outstanding items named); session-log row; plan-changes rows for every retraction/correction 2d produced |
| `INDEX_GUIDE.md` | Version bump + changelog: buff model tables/conventions, volatility formula change, any schema touched by T3/T4, `predictions.patch_id` convention, kit/chassis terminology |
| `primer/Ascension_Context_Primer.md` | Any §-level rule or verdict 2d changed (bucket scoring, calibration status, residual verdict from T1) |
| `PHASE_2_simulation.md` | Exit-criteria list amended (§8.2 move referenced); D4 calibration gate written into §8 |
| `PHASE_3_builds_repo.md` | Inherited ≥3-character gate added as an explicit task with the gear dependency; anything T0's list resolves that 3a was going to ask for again |
| `NEXT_CAPTURE.md` | Items consumed marked ✅ with a pointer to where the result landed; outstanding items carried into T0's list state rather than left ambiguous |
| `predictions/` | T1's calibration reconciled in the ledger; the 1.31 ⚠ append (T5.3); `patch_id` seeded |
| `SCORECARD.md` | Created (T6) |
| `ARCHITECTURE.md` | Kit Library rename (T7) |
| `CHAT_MONITORING_PRIMER` | Refreshed through 2d: snapshot currency line, phase table, confirmed-facts additions, retraction list, model guidance, next session = 3a. If not repo-committed, emit the updated copy to an obvious path and tell the owner to re-upload it to the chat Project |
| Build doc (`build_paladin-hammerdin.md`) | Only if T1/T2 change a conclusion it states (e.g. the "Holy multiplier chain" framing `2c` already flagged, the §10 split, Path verdict) — version-bump per its own convention |
| Session handoff (`Session_*_2d_*.md`) | Written last, after all of the above, per standing convention |

Rule of thumb: if a future session could read a doc and act on a pre-2d claim without any
marker that 2d changed it, T10 is not done.

---

## Execution order

T0 (compile + deliver the in-game list; owner goes to play) → T1 (owner-dependent; proceed if
blocked) → T3 (swing timer unblocks seals + autos; independent of T1) → T2 (buff model;
consumes T1's Path/buff state if available, otherwise builds the frame with warnings) → re-run
calibration with T2+T3 in place, report all three gates → T4 → T5 → T6–T9 in any order
(mechanical, no dependencies) → T10 last, always.

## Model guidance

T1–T3 + the calibration re-run are judgment-critical (Opus-tier). T4–T9 are well-specified and
mechanical (Sonnet-tier). If splitting, split there.

## Exit criteria

- The consolidated in-game task list (T0) was delivered to the owner at session start, and its
  end-of-session state (answered / outstanding per item) is recorded in PROGRESS.
- Capture bundle consumed (or formally blocked-on-user), calibration reported against **all
  three** recorded tolerances, residual's structural-vs-buff question answered or explicitly
  narrowed.
- Buff model exists; `raid_buffs_available` maps to concrete modelled buff sets; unconfirmed
  magnitudes warn.
- Seals ride swings; auto-attacks modelled; RV DoT modelled; Judgement representable.
- Extract-staleness sweep live; `predictions.patch_id` populated.
- `SCORECARD.md` written; volatility decay-weighted; kit/chassis terminology landed; D3/D4 in
  the standing docs; all five doc-hygiene items closed.
- **T10's doc-sync checklist fully walked** — every listed doc updated or marked n/a in the
  handoff, handoff written last.
- Zero silent defaults introduced — every new modelled quantity carries provenance or a warning.

## Explicitly out of scope

Scorecard *implementation* (Phase 4). Gear (3a). Guide display/staleness UX (deferred, D5).
Population percentile computation (needs 3a's confound fixes — the spec only *defines* it).
