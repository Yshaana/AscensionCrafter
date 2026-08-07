# CHAT MONITORING PRIMER v4 — AscensionCrafter

> **`LIVE`** — the standing brief for the oversight chat. **Must be true today, and is
> citable as current truth.** Supersede at **v5** when `3i` closes. *(v3 expired the moment
> `3h` closed and was still `LIVE` when the `3h` audit found it — the same trap v2 fell into.
> **If you are reading this after `3i` has closed, it is stale: say so and rewrite it.**)*

**Paste this at the start of a fresh monitoring chat.** Supersedes v1, v2 and v3. Written
2026-08-07, at the end of the session that audited `3h` and drafted `3i`.

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
confirmed.** ⚠ And read the *rest* of `PROGRESS.md` too: the `3h` audit found its
`## Current position` section three sessions stale and still issuing live instructions.

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

## Where things stand, 2026-08-07 (post-`3h`)

**Session map:** `3d` ✅ → `3e` ✅ → `3f` ✅ → `3g` ✅ → `3h` ✅ → **`3i` (first gate-moving
commits since `3g`, work order written)** → E9/E11/E12 → re-read Phase 3 exit honestly →
Phase 4.

**The gate:** `1 of 36 within ±20% · 1 qualified · slice accuracy 20.5% at coverage ≥20%
(n=23)` — **unmoved across all ten `3h` commits**, because `3h` was an instrument session
and touched no file under `core/`. Holdout, read once at `3g` close-out: **0 of 5, −79% to
−98%**, median slice **9.8% (n=4)** — worse than the tuning set, so 20.5% is the optimistic
end.

**Phase 3 exit: NOT met.**

🚨 **`3h`'s result, in one line: the sim is not uniformly ~5× under.** It is **absent** for
most logged damage, **zero-producing** for a tenth, and **wrong in both directions** on the
rest — and the aggregates cancel. Slice accuracy was the last inferred headline; it is now a
measured distribution. Producing paired abilities: median ratio **0.253**, only **11%**
inside [0.8, 1.25]. ⚠ **All of those figures need re-stating in `3i`** — see the open
threads.

**Key documents, in reading order for a new chat:**

| File | What |
|---|---|
| `primer/PROGRESS.md` | live state — top block first, then check `## Current position` is not stale |
| `primer/AUDIT_3H_ADVERSARIAL.md` | the current audit; §4 is the serious findings, §10 is the list `3i` works from |
| `primer/SESSION_3I_PRIMER.md` | the work order in flight |
| `primer/ENGINE_BUGS.md` | the defect registry, `LIVE` — ⚠ its "enforced in both directions" claim has no parser behind it |
| `primer/Session_2026-08-07_3h_measurement.md` | what `3h` actually did |
| `predictions/CALIBRATION_TOLERANCE.md` | the stamped tolerances, the slice-accuracy record, and successor #3 (parse admissibility) |
| `predictions/gate_manifest_3e.json` | ⚠ named for `3e`, holds the **current** numbers |
| `primer/AUDIT_3G_ADVERSARIAL.md` | the previous audit; §7 is the list `3g` worked from |

---

## The open threads, in priority order

**1. 🚨 E15 — pet damage is stored TWICE and the fix is not in.** `ability_performance`'s
primary key includes `is_pet` (`corpus.py:156`) and pet rows carry the **owner's**
`character_id` (`:425-434`), so the owner copy and the pet copy coexist: 15,551
byte-identical groups. `corpus.py:594-614` then computes `dps = (total_damage + pet_damage)
/ dur` where `total_damage` already contains the pet damage — **every pet-owner's logged DPS
is inflated, and that is the gate's own comparison target.** Green path run and reverted in
`3h`: consumer dedupe alone moves the gate to `1 / 1 / 19.8%`. Fix at **ingest**, not just
the consumer. `3i` Block A.

**2. 🚨 `per_ability_accuracy.py`'s logged side does not agree with itself.** `:154` sums
duplicate rows into `total_logged`; `:204` collapses them with a dict assignment and no
`ORDER BY`. So the per-row shares in its own artifact **do not sum to 100%**, and for the
5,234 groups whose copies *differ*, **which one survives is nondeterministic**. Consequence:
`62.2% absent` has an **indeterminate sign and is plausibly understated**; the ratio
distribution is largely clean *except* the auto row. **Do not pick modelling targets from
the pre-repair distribution.** `3i` Block B.

**3. ⚠ The stamped admissibility rule is narrower than it reads.** Predicates 4 and 5 are
`print()` statements, not computations (`parse_admissibility.py:198-202`) — and **predicate
4's hardcoded "every capture predates the 2026-08-08 boundary" stops being true on the 8th.**
Every refusal path (out-of-regime, `<2` other scopes, NULL casts) lands on *admissible*, and
the regime test itself fails open four ways, so `resolved_entries` is computed and never
printed: *"regime valid, 0 cast-time entries"* is indistinguishable from *"nothing resolved"*.
"5 of 41" is a lower bound, not the rule's reach. `3i` Block C.

**4. ⚠ Two of `3h`'s own new check arms cannot go red.** `check_refusals.py:821` asserts a
sum that is true by construction (`keyed_zero = modelled - producing`); `:836` is green under
the exact defect it excludes. The `3g` G6 tautology family, one session later.

**5. ⚠ `gear_tier_stats(phase=…)` still has no production caller**, so `3f` exit condition 10
reads ✅ on a function nothing calls. In `PROGRESS.md`'s blocked table for **three** sessions.

**6. ⚠ `ContentProfile` presets are FAILED, not unverified** — 6 of 8 self-declare
`provenance="assumption: …"`. `PHASE_3` exit criterion 7, untouched since `3d` named it, now
the oldest unaddressed criterion by a wide margin.

---

## Corrections worth carrying — do not let these creep back

- ❌ **"E13 is ~78×"** — the bracket's value at one crit rate. It is a **unit** error:
  **exactly 100**, invariant across builds. **Fixed at `3g` G1.**
- ❌ **"slice accuracy is 64.3% / the sim under-produces by about a third"** — measured on a
  sim with a 100× auto-attack. **20.5%**, and the holdout says ~10%. **⚠ `PROGRESS.md:527-580`
  was still printing `5 of 36 / 64.3%` and "FIX E13 FIRST" as live instruction at `3h` close.**
- ❌ **"at ~62–64%, both levers have to roughly double"** — at 20.5% the coverage lever is
  arithmetically dead. `slice × coverage = 1.0` needs slice ~4.9× higher even at 100% coverage.
- ❌ **"the sim under-produces uniformly"** — `3h` C3 killed this. It is absent for most,
  zero for a tenth, and wrong in both directions on the rest; **17% of producing abilities are
  OVER 1.25×**. A single multiplier will not fix this model.
- ❌ **"the residual is not in the mechanisms" (`3e`)** — the **inference** is retracted, the
  measurement is not. Seeded as `retractions.residual_is_not_in_the_mechanisms`.
- ❌ **"E14 needs a refusal"** — the component's own duration is one join away. **Stopping
  the mixing** fixed eleven silently-wrong components as well as the loud one. **And `3h` B
  measured the aftermath: zero of the 90 keyed-but-zero entries are refusals — all 90 are
  GCD starvation (E6/E7).** The `3g` audit's §4 worry is measurably absent.
- ❌ **"the modelled slice is over-produced by ~60%"** (`3d`) — a low-coverage artifact,
  retracted, shipping bare in `predictions/gate_manifest.json` as `159.79`. That file is the
  **frozen `3d`** record and says so; the live numbers are in `gate_manifest_3e.json`.
- ❌ **"coverage means the sim produces damage for X%"** — it means the sim **has a key for**
  X%. `3h` B1 fixed the docstring and the per-character line; ⚠ `calibrate_crawled.py:692`
  and `tools/scrapers/scrape_ascension_db.py:12` still carry the old phrasing.
- ❌ **"`casts` is `SPELL_CAST_SUCCESS`, generally"** — true for all-instant kits, false for
  cast-time casters; the two event types are **disjoint by cast type**. **22 of the 41
  cohort boards are cast-time casters**, so any `casts`-derived metric needs a stated regime.
  *(This is why the APM ratio has one — and why it refuses on most of the cohort.)*

Still true and still load-bearing: the **eight rules**, `entry_id` ≠ `spells.id`, the
catalog's wrong-rank problem, class-from-`SkillLine`.

---

## How to review a session (the loop that works)

1. Clone fresh. Read `PROGRESS.md`, then the session's own handoff, then the work order it ran.
2. **Spot-check claims against committed files, not prose.** Every significant finding has
   come from reading code that contradicted a document.
3. **Run the greps the docs imply.** *"This guard is implemented"* is checkable in seconds.
4. **Check the `LIVE` documents against the code, in both directions.** `3g` and `3h` both
   shipped good code beside stale `LIVE` prose. **Document discipline has now been the weaker
   half for two consecutive sessions** — budget audit time accordingly.
5. 🆕 **Trace a headline number from the schema up, not from the summary down.** The `3h`
   audit's sharpest finding came from reading `CREATE TABLE`, then the ingest, then the query,
   then the four lines that consume the query — and finding the same rows counted one way in
   the denominator and another in the numerator. **Summaries are where errors hide; primary
   keys are where they are decided.**
6. Confirm 🛑 stop-points were asked, not guessed, and that pre-registrations are committed
   **before** the commit they predict. 🆕 Also check the prereg's *predicate*: `3h` reported
   "removes 3 failing characters" against a prereg that registered a different predicate
   (two of the three qualify; the third was removed by a rule not in the registration).
7. **Ask of every check and metric: does it have a regime where it returns a number it cannot
   support?** Still the most productive single question here. It has found fail-open checks
   (`3d`), permanently-red checks (`3g` G5), tautological arms (`3g` G6 — and again at `3h`
   B4), a coverage denominator counting refusals as coverage (`3g`), and fail-open
   admissibility predicates (`3h`).
8. **Ask also: is this number measured, or derived from two other numbers?** Everything this
   project has retracted was derived. 🆕 **And: is it committed?** `3h`'s headline result
   lives only in gitignored `data/derived/`, so it is the one number a monitoring chat cannot
   check — the reverse of the provenance progress the same session made on the manifest.

**Tone:** this project's value comes from falsifiable checking, not cheerleading. If
something looks off, say so plainly, with the file:line. If it is genuinely good, a short
confirmation is enough — and `3h` earned several: the structural holdout exclusion, the
rate-normalised ratio, the fail-closed dirty-tree refusal, and reporting P4 false.

---

## Standing owner actions (not session tasks)

- **Daily:** the crawler runs automatically at logon (Task Scheduler) — row-count canary,
  scoped auto-commit, changelog exit code, live phase assertion.
- **Occasional, overnight, manual:** `catchup_crawler.bat` — deliberately not scheduled.
- **Per client patch:** `run_dbc_extract.bat`. ⚠ Its last **successful** run is the staleness
  clock, not its last commit.
- **The stat-export addon** — verified byte-identical to the repo copy at `v2026-08-06c`.

## 🚨 Time-critical

**`season_config.NEXT_PHASE_BOUNDARY` is `2026-08-08T00:00:00Z` — it arms tonight.** At the
last live check (`3g` G0, `2026-08-07T00:35Z`) the flip had **not** happened: `/api/phases`
still returned Phase 1 - Zul'Gurub active with Phase 1.1 as a **child**.

`3g` built three defences, widest first: `phase_guard()` asserts the payload's active
top-level phase equals `EXPECTED_PHASE_NAME`; a **declared boundary** catches a Phase 2
shipped as a child (which `phase_windows` drops and `assert_phase` ignores); and
`horizon is None` now fails **closed**.

🛑 **Nobody has seen any of it fire.** On the 8th, check that the boundary armed, that
`phase_label` goes **NULL** rather than mis-stamping, and — if the flip really happened —
that `EXPECTED_PHASE_NAME` was bumped and the corpus re-derived **before** any gear tier was
read. Leaderboards and armory are the only data a flip destroys; reports persist, so the
report backfill has no deadline.

🆕 **And from the 8th, `parse_admissibility.py:198-199` prints a claim that is no longer
true** — predicate 4's hardcoded *"every corpus capture predates the boundary, so this
removes nobody today"*. It is a string, not a test.

---

## Things to check rather than inherit

Each is a real gap in what has been verified.

1. **Every gate number is read from a committed manifest, not reproduced.** `data/derived/`
   is gitignored and no `.db` is committed, so `1 of 36`, `20.5%` and the holdout's five
   members are checkable only on the owner's machine. **✅ Improved at `3h` A7:** the
   manifest now **refuses to write from a dirty tree**, so `e06a8c3` onward the `git_sha`
   identifies the code. ⚠ But `--allow-dirty` records a bool nothing reads, and
   `gate_manifest.json` still ships `git_working_tree_dirty: true` unflagged.
2. 🆕 **`3h`'s headline distribution is in no committed artifact at all** —
   `per_ability_accuracy.py` writes only to `data/derived/`. **This is now the limiting
   factor**, having replaced item 1 as the thing a monitoring chat most wants and cannot get.
3. **F9's frost-mage number and the cohort median.** −66.9% (33.1% of measured) against
   producing-only 30.7% — `3h` P5 called this reconciled at 2.4 points. ⚠ The two medians are
   over **different populations** (n=20 vs n=23, selected on different denominators), so the
   reconciliation is not yet a paired comparison.
4. **`Boomcat` is one row, and `3h` explained rather than rescued it.** APM ratio **0.27**
   (implemented, confirming `3c`'s hand-computed 0.24), and its +0.8% pass is per-ability
   **compensation** — top logged ability starved to 0 against two at 2–3.5× over. `Ari`'s
   shape on the passing side. Applying the stamped rule takes `within ±20%` from **1 to 0**.
5. **Whether `3d`'s engine fixtures can expose more than the defects already found.** They
   are permanent; nobody has run them adversarially. Unchanged for five sessions.
6. 🆕 **`ENGINE_BUGS.md` claims it is "enforced in both directions" and nothing parses it.**
   `resolve_generality()` enforces check *names* against `EXPECTED_FAILURES`, not the
   document. It has already drifted twice. Either build the parser or downgrade the claim.
