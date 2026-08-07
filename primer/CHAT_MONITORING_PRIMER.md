# CHAT MONITORING PRIMER v3 — AscensionCrafter

> **`LIVE`** — the standing brief for the oversight chat. **Must be true today, and is
> citable as current truth.** Supersede at **v4** when `3h` closes. *(v2 was `LIVE` and
> three sessions stale when `3h` replaced it — the `3f` audit flagged it at two.)*

**Paste this at the start of a fresh monitoring chat.** Supersedes v1 and v2. Written
2026-08-07, at the end of the session that audited `3g` and drafted `3h`.

This chat's job is **oversight and verification** — Claude Code writes the code locally.
That split is not bureaucratic: everything useful this chat has produced came from checking
Code's output against the tree independently. **If this chat writes the code, nobody is left
to audit it.**

---

## First action, every time

Clone and read the tree. Do not work from prose, this file included.

```bash
git clone --depth 40 https://github.com/Yshaana/AscensionCrafter.git repo
```

~130 MB, under a minute. Working from a clone rather than `curl`-ing individual files is
what makes the findings possible — most come from `grep`-ing across the whole tree.

Then read `primer/PROGRESS.md`'s top block. **If a claim isn't in the tree, it isn't
confirmed.**

⚠ **The owner may connect the local repo** (`C:\Users\Yshaana\Documents\GitHub\AscensionCrafter`)
via `device_list_dir` / `device_stage_files` / `device_commit_files`. That is file read/write
on his machine with **no shell** — you cannot run `cli/rebuild.py`, the purity check,
`check_sim_engine.py`, or the gate. Use it for **documents**. **Do not write code with it**:
unrunnable code in a repo whose discipline is "never manufacture confidence" is the exact
failure mode `3d` found three instances of.

---

## What this project is (one paragraph)

A theorycrafting toolkit for **Project Ascension** — a classless WoW private server (3.3.5
client, realm **Darkmoon**, Season 10) where characters slot abilities and talents from any
class. Five layers: a provenance-enforced spell/mechanics database, a crawled +
live-captured builds repo, a ported-SimC damage simulator, a "lego box" of reusable build
components, and a theorycrafter that designs builds and emits guides. Built in phases by
Claude Code running locally; the owner plays the game and validates findings with real
parses. **The owner is the tier-1 evidence source.**

---

## Where things stand, 2026-08-07

**Session map:** `3d` ✅ → `3e` ✅ → `3f` ✅ → `3g` ✅ → **`3h` (instrument session, work
order written)** → then E9/E11/E12 → re-read Phase 3 exit honestly → Phase 4.

**The gate:** `1 of 36 within ±20% · 1 qualified · slice accuracy 20.5% at coverage ≥20%
(n=23)`. Holdout, read once at `3g` close-out: **0 of 5, −79% to −98%**, median slice
**9.8%** — worse than the tuning set, so 20.5% is the optimistic end.

🚨 **THE PROBLEM IS THE UNDER-PRODUCTION ITSELF.** `3g` fixed E13 (every white swing
**exactly 100×** over) and E14 (12,000 ticks per cast) and the gate got **five times
worse — on purpose, pre-registered, and that is the session working.** Slice accuracy did
not drift from 64.3% to 20.5%; **64.3% was never true.**

**Phase 3 exit: NOT met**, and further from met than before.

**Key documents, in reading order for a new chat:**

| File | What |
|---|---|
| `primer/PROGRESS.md` | live state — top block first, always |
| `primer/AUDIT_3G_ADVERSARIAL.md` | the current audit; §4 and §5 are the live findings |
| `primer/SESSION_3H_PRIMER.md` | the work order in flight |
| `primer/ENGINE_BUGS.md` | the defect registry, `LIVE`, enforced both ways by `check_sim_engine.py` |
| `primer/Session_2026-08-07_3g_explosions.md` | what `3g` actually did |
| `predictions/CALIBRATION_TOLERANCE.md` | the stamped tolerances and the slice-accuracy record |
| `predictions/gate_manifest_3e.json` | ⚠ named for `3e`, holds the **current** numbers |
| `primer/AUDIT_3F_ADVERSARIAL.md` | the previous audit; §7 is the list `3g` worked from |

---

## The open threads, in priority order

**1. 🚨 Coverage counts abilities the sim produced ZERO damage for.**
`sim_spell_ids = set(res.per_ability.keys())` (`calibrate_crawled.py:745`), but
`core/sim/tiers.py:496` writes a `per_ability` entry **unconditionally** — including when
every event was REFUSED (`ability_model.py:918-924`) or nothing resolved (`:735-742`).
`modelled_damage_share`'s docstring says *"spells the sim produced any damage for"*; that is
**false**. Since `slice = (100 + delta) / coverage`, a keyed-but-zero ability pushes slice
accuracy down twice — and `3g`'s E14 fix **added** refusals into that bucket. **So `20.5%`
conflates magnitude error with zero production.** `3h` Block B.

**2. 🚨 Slice accuracy is inferred, not measured.** `(100 + delta) / coverage` is a ratio of
two aggregates. The direct per-ability comparison — `res.per_ability[sid]["damage"]` vs
`ability_performance.damage_total` — has never been run at cohort scale, and both sides are
already joined on spell id inside `modelled_damage_share`. **It is the last headline number
in the project on the wrong side of the equals sign.** `3h` Block C.

**3. 🛑 `Boomcat` (16501) is the ONLY passing row and is not yet trustworthy.** `3c`
retracted it on a suspected death-deflated parse (APM ratio 0.24 vs Elric's known death case
0.38); `3e` preflight ruled out the cast-time explanation. `dps = total_damage / SUM(encounter
duration)` (`corpus.py:614`) is **wall-clock, not active time**, so a death deflates the
denominator and *flatters* the delta against a sim that under-produces — `Ari`'s shape on the
log side. ⚠ `deaths` appears **exactly once** in the Python tree (`corpus.py:137`, the
`CREATE TABLE`): declared, never written, never read. And the APM ratio has no implementation
at all. `3h` Block D.

**4. ⚠ `gear_tier_stats(phase=…)` still has no production caller**, so `3f` exit condition 10
reads ✅ on a function nothing calls. Stated in `PROGRESS.md`'s blocked table for two
sessions running.

**5. ⚠ `ContentProfile` presets are FAILED, not unverified** — 6 of 8 self-declare
`provenance="assumption: …"`. `PHASE_3` exit criterion 7, untouched since `3d` named it, now
the oldest unaddressed criterion.

---

## Corrections worth carrying — do not let these creep back

- ❌ **"E13 is ~78× "** — the bracket's value at one crit rate. It is a **unit** error:
  **exactly 100**, invariant across builds.
- ❌ **"slice accuracy is 64.3% / the sim under-produces by about a third"** — measured on a
  sim with a 100× auto-attack. **20.5%**, and the holdout says ~10%.
- ❌ **"at ~62–64%, both levers have to roughly double"** — at 20.5% the coverage lever is
  arithmetically dead. `slice × coverage = 1.0` needs slice ~4.9× higher even at 100%
  coverage.
- ❌ **"the residual is not in the mechanisms" (`3e`)** — the **inference** is retracted, the
  measurement is not. `3e`'s six repairs really did leave the gate byte-identical; what
  cannot be concluded is *where the residual lives*, because the metric was dominated by a
  defect none of the six touched. Seeded as
  `retractions.residual_is_not_in_the_mechanisms`.
- ❌ **"E14 needs a refusal"** — the component's own duration is one join away. **Stopping
  the mixing** fixed eleven silently-wrong components as well as the loud one.
- ❌ **"the modelled slice is over-produced by ~60%"** (`3d`) — a low-coverage artifact.
  Still retracted, and now shipping bare in `predictions/gate_manifest.json` as
  `cohort_median_slice_accuracy_pct: 159.79`. That file is the **frozen `3d`** record; the
  live numbers are in `gate_manifest_3e.json`.
- ❌ **"`casts` is `SPELL_CAST_SUCCESS`, generally"** — true for all-instant kits, false for
  cast-time casters; the two event types are **disjoint by cast type**. **22 of the 41
  cohort boards are cast-time casters**, so any `casts`-derived metric needs a stated
  regime.

Still true and still load-bearing: the **eight rules**, `entry_id` ≠ `spells.id`, the
catalog's wrong-rank problem, class-from-`SkillLine`.

---

## How to review a session (the loop that works)

1. Clone fresh. Read `PROGRESS.md`, then the session's own handoff, then the work order it ran.
2. **Spot-check claims against committed files, not prose.** Every significant finding has
   come from reading code that contradicted a document.
3. **Run the greps the docs imply.** *"This guard is implemented"* is checkable in seconds.
4. 🆕 **Check the `LIVE` documents against the code, in both directions.** `3g`'s engine work
   was flawless and three `LIVE` documents still described the pre-`3g` world — including
   `ENGINE_BUGS.md`, which carried both fixed defects as unfixed while the session record
   claimed the correction had landed there. **Code discipline and document discipline are
   now failing separately, and the documents are the weaker half.**
5. Confirm 🛑 stop-points were asked, not guessed, and that pre-registrations are committed
   **before** the commit they predict.
6. **Ask of every check and metric: does it have a regime where it returns a number it cannot
   support?** This is still the most productive single question here. It has found
   fail-open checks (`3d`), permanently-red checks (`3g` G5 — worse, because a permanent
   alarm gets silenced rather than satisfied), tautological arms (`3g` G6), and now a
   coverage denominator that counts refusals as coverage.
7. 🆕 **Ask also: is this number measured, or derived from two other numbers?** Everything
   this project has retracted was derived.

**Tone:** this project's value comes from falsifiable checking, not cheerleading. If
something looks off, say so plainly, with the file:line. If it is genuinely good, a short
confirmation is enough — and `3g` earned several.

---

## Standing owner actions (not session tasks)

- **Daily:** the crawler runs automatically at logon (Task Scheduler) — row-count canary,
  scoped auto-commit, changelog exit code, live phase assertion.
- **Occasional, overnight, manual:** `catchup_crawler.bat` — deliberately not scheduled.
- **Per client patch:** `run_dbc_extract.bat`. ⚠ Its last **successful** run is the staleness
  clock, not its last commit.
- **The stat-export addon** — verified byte-identical to the repo copy at `v2026-08-06c`.

## 🚨 Time-critical

**`season_config.NEXT_PHASE_BOUNDARY` is `2026-08-08T00:00:00Z`.** Checked live at
`2026-08-07T00:35Z` (`3g` G0): **the flip had NOT happened** — `/api/phases` still returns
Phase 1 - Zul'Gurub active with Phase 1.1 as a **child**.

`3g` built three defences, widest first: `phase_guard()` asserts the payload's active
top-level phase equals `EXPECTED_PHASE_NAME`; a **declared boundary** catches a Phase 2
shipped as a child (which `phase_windows` drops and `assert_phase` ignores); and
`horizon is None` now fails **closed**.

🛑 **Nobody has seen any of it fire.** On the 8th, check that the boundary armed, that
`phase_label` goes **NULL** rather than mis-stamping, and — if the flip really happened —
that `EXPECTED_PHASE_NAME` was bumped and the corpus re-derived **before** any gear tier was
read. Leaderboards and armory are the only data a flip destroys; reports persist, so the
report backfill has no deadline.

---

## Things to check rather than inherit

Each is a real gap in what has been verified.

1. **Every gate number is read from a committed manifest, not reproduced.** `data/derived/`
   is gitignored and no `.db` is committed, so `1 of 36`, `20.5%` and the holdout's five
   members are checkable only on the owner's machine. Both manifests also report
   `git_working_tree_dirty: true`, so the sha does not identify the code that produced them.
   **This is the limiting factor on what a monitoring chat can verify**, and it has been
   unchanged for four sessions.
2. **Thread 1's magnitude is still unmeasured.** How many keyed-but-zero abilities exist in
   the cohort could be three or a third of it, and which one changes the whole `3h` payoff.
3. **F9's frost-mage number and the cohort median disagree.** −66.9% (33.1% of measured) with
   **no coverage term**, against a cohort slice of 20.5%. Two measurements of the same
   quantity, 1.6× apart, and nobody has reconciled them.
4. **`Boomcat` is one row.** With `1 of 36` passing, it *is* the gate. A single high-coverage
   passer is exactly the shape E13 taught this project to distrust — `Ari` was also a
   qualified pass.
5. **Whether `3d`'s engine fixtures can expose more than the defects already found.** They
   are permanent; nobody has run them adversarially.
