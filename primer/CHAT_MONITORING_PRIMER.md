# CHAT MONITORING PRIMER v7 — AscensionCrafter

> **`LIVE`** — the standing brief for the oversight chat. **Must be true today, and is
> citable as current truth.** Supersede at **v8** when `3l` closes. *(The streak is
> two: v5 and v6 both held their stated expiry — v6 declared v7 due at `3k` close and
> this is that rewrite, same day. **The repo file `primer/CHAT_MONITORING_PRIMER.md`
> is versionless and updated in place; the version lives in the title line only.
> Never commit a `_v7` sibling** — a versioned copy beside the live file is how v2–v4
> each stayed marked `LIVE` after expiring.)*

**Paste this at the start of a fresh monitoring chat.** Supersedes v1–v6. Written
2026-08-07 (late evening), at the end of the session that audited `3k` — the audit is
`AUDIT_3K_ADVERSARIAL.md`, ⚠ **written in the oversight chat and not yet committed to
`primer/`** — committing it, with this file, is the first document action owed
(`3l` pre-flight).

This chat's job is **oversight and verification** — Claude Code writes the code
locally. If this chat writes the code, nobody is left to audit it.

---

## First action, every time

Clone and read the tree. Do not work from prose, this file included.

```bash
git clone --depth 40 https://github.com/Yshaana/AscensionCrafter.git repo
```

Then `primer/PROGRESS.md`'s top block. **If a claim isn't in the tree, it isn't
confirmed.** The owner may connect the local repo via `device_list_dir` /
`device_stage_files` / `device_commit_files` — file read/write, **no shell**. Use it
for documents only; never write code through it.

---

## What this project is (one paragraph)

A theorycrafting toolkit for **Project Ascension** — a classless WoW private server
(3.3.5 client, realm **Darkmoon**, Season 10). Five layers: a provenance-enforced
spell/mechanics database, a crawled + live-captured builds repo, a ported-SimC damage
simulator, a "lego box" of build components, and a theorycrafter. Built in phases by
Claude Code locally; the owner plays the game and is the tier-1 evidence source.

---

## Where things stand, 2026-08-07 late evening (post-`3k`, post-audit, flip RESOLVED)

**Session map:** … → `3i`✅ (gate repair) → `3j`✅ (integrity) → `3k`✅ (flip +
coverage — **coverage is not accuracy, measured**) → **`3l` (Block C first, then
TUNING — work order drafted alongside this file, seeded from `AUDIT_3K` §5)** →
re-read Phase 3 exit honestly → Phase 4.

**The gate:** `0 of 35 within ±20% · 0 qualified · slice accuracy 26.3% at coverage
≥20% (n=23)`, 3 of the frozen 41 not admissible (Nodding 52s window, Boomcat 0.24,
Deyindra 0.22). Unchanged at every `3k` commit — a modelling session was *permitted*
to move it and did not, and the record says why. ⚠ **The denominator moved 36 → 35
by corpus growth** (the old reading came from a `builds.db` built before the day's
own crawl was ingested), not by admissibility. Holdout: carried from `3g`, `0 of 5`,
median slice 9.8% (n=4), **annotated pre-E15**, direction known (understates) — not
like-for-like with 26.3%, never compute a gap from the pair. Phase 3 exit: **2 of 7
criteria met** (per-criterion table now lives in `primer/PHASE_3_builds_repo.md`).

**The Molten Core flip is RESOLVED — additively.** MC opened **top-level** at
`2026-08-07T18:00:00Z` and Zul'Gurub stayed active: two active top-levels, a shape
no protocol covered. **Owner decision, now the model: transitions on this server are
ADDITIVE** — the current phase is the latest-STARTING active top-level, on both the
`core/` and crawler sides. The count-based refusal (`len(tops) != 1`) is retired —
it would have NULLed every label forever; the ambiguity protection **moved** to
same-`start_date` windows (M51 proves it live). `NEXT_PHASE_BOUNDARY` self-retired
as designed. **Zero corpus captures fall on the MC side** (latest 16:02:50Z), so the
MC window exists and is empty — which is C1's test case. Gear-tier reads are
unblocked in principle; in practice the production caller still doesn't exist.

**The `3k` result that shapes `3l`:** absent mass 62.9% → **59.9%** on one target
(Righteous Vengeance — a derivation that had **never once run**: `tiers.py` read
`ev.get("crit_damage")` since `2e` and nothing ever wrote the key; fixed WITH a
card-ownership gate, phantom share *fell* 58.4% → 53.8%) — and **slice accuracy did
not move at all** while the producing median *fell* 0.2727 → **0.2573** (RV came
back at ratios 0.004–0.005). **Coverage is not accuracy. Tuning is the load-bearing
problem, and most remaining absent mass is trigger-delivered damage the APL
structurally cannot contain** (not cards: Deep Wounds, Ignite, diseases, imbue
procs) — whether `3l` opens delivery modelling or defers it to `3m` is owner
decision 1.

**Key documents, reading order:**

| File | What |
|---|---|
| `primer/PROGRESS.md` | live state — top block first; ⚠ its "3.5 points" refusal figure is suspect (prereg sums 4.1; `3l` regenerates it) |
| `AUDIT_3K_ADVERSARIAL.md` | current audit; §5 is `3l`'s list; ⚠ commit it to `primer/` |
| `primer/Session_2026-08-07_3k_coverage.md` | what `3k` did; §3 = coverage-vs-accuracy; §6 = honest not-done |
| `predictions/gate_manifest_3e.json` | current numbers (`LIVE`, clean tree, `git_sha cf5ff3c`; ⚠ the record's §5 cites `9683e87` — one regen earlier, close-out pattern) |
| `predictions/per_ability_summary.json` | the distribution — ⚠ aggregates only, NO per-key rows (audit §3.2; `3l` B0 widens it) |
| `predictions/prereg_3k_b_coverage.md` | the model prereg — and the uncommitted-baseline caveat lives here |
| `primer/ENGINE_BUGS.md` | defect registry — parser-enforced, M1..M53 contiguous |

---

## The open threads, in priority order

**0. 🚨 THE MC CAPTURE EXISTS ONLY ON THE OWNER'S DISK — one commit owed.**
`data/source/captures/2026-08-07_elric_mc_first_raid/` (two WoWCombatLog halves,
89.4/91.4 MB, split by a client crash; `Molten Core.txt` — 6 Elric stat-export
blocks + 20 inspect links for 18 raid members; README in the house provenance
format) plus `primer/FINDINGS_MC_capture_2026-08-07.md` — untracked, invisible to
any clone, and it is **the project's first per-parse stats ever** (the T5 unblock
for `infer_coefficient`'s `refused:no_per_parse_stats`, which gates Phase 3
criteria 3-full and 4). Until committed, a disk failure loses it. The >5 MB rule is
waived for this commit by owner decision (four committed capture precedents); the
new `primer/` file stales the census — same commit. 🛑 **Ingest gates:** nothing
derives a number from it until records verifiably resolve to Phase 2 (not NULL, not
ZG — all content is post-boundary, 18:17–20:03 UTC); the Gehennas kill is **one
pull split across the two halves** (~60 s crash gap), never two encounters, never
dropped. Using the stats is `3l`-scope with its own prereg; **arming admissibility
predicate 2 (deaths > 0) from log-sourced deaths is a stamp change needing an owner
decision**, not a drive-by. Site reports 116/117 pending tier-2 crawl pickup.

**1. 🛑 BLOCK C HAS BEEN CARRIED TWICE.** The `gear_tier_stats(phase=…)` production
caller (now with a real refusal case: the empty MC window) and corpus-measured
`ContentProfile` presets. `3l` opens with them or the owner stamps a re-scope —
no third silent carry. **C2 must land before the tuning prereg** (it feeds the sim
side; mid-tuning it kills attribution).

**2. TUNING is `3l`'s registered core.** Producing median 0.2573 (n=107).
Discipline: committed baseline first (B0), diagnose mechanism before fitting,
nothing fitted to its own target. Warm-up thread: Deyindra and Shana hold the RV
card, log the DoT, report **zero crit damage** — do their resolved abilities carry
`p_crit > 0`? Scope decision owed: delivery modelling in or out (default: out).

**3. One owner-gated `--with-dbc` run** scoped to include `SpellItemEnchantment.dbc`
unblocks both named refusals — Consecrated Holy Weapon (200818, 2.61%/6 chars) and
Seal of Command (20424, 1.47%/4). Ask at session start; it runs in parallel.

**4. Small carried threads:** the 1,208 owner<pet groups (**third carry** — explain
or register, not a fourth); keyed-but-starved 12.9% (GCD allocation, register or
re-defer by name); Devour Mind (287865, 6.63%, 2 chars — largest single absent key,
`3l`/`3m` coverage target); the `season_config.py` docstring fossils
("2026-08-08"); the 3.5-vs-4.1 figure (regenerate, correct, cite the run).

**5. Document actions owed at `3l` pre-flight:** the MC capture commit (thread 0,
its own commit); `AUDIT_3K_ADVERSARIAL.md` → `primer/` (born `FINDING`); THIS file
committed in place as v7; census regenerated in each commit that adds a `primer/`
file.

**6. Owner decisions given to `3k` mid-run — all three verified STAMPED, not just
implemented** (checked by the `3k` audit): (a) additive transitions / latest-
starting active top-level — stamped in `prereg_3k_b0_phase_flip.md` (verbatim
quote, recorded before code), `season_config.py`, `core/builds/phases.py`,
PROGRESS, the session record §1; (b) tuning deferred whole to `3l` — stamped in
`prereg_3k_b_coverage.md` + record §6; (c) D2 dirty-tree thread closed by
annotating the FROZEN status note — stamped in `gate_manifest.json`'s
`_status_note`, annotation-only (JSON-compared). Nothing to chase.

---

## Corrections worth carrying — do not let these creep back

- ❌ **"0 of 36"** — the denominator is **35** since `3k` (corpus growth, not
  admissibility). Any doc citing 36 is stale.
- ❌ **"two active top-level phases = a transition in progress"** — FALSIFIED by the
  server's own modelling. Transitions are ADDITIVE (owner decision); the current
  phase is the latest-starting active top-level. Ambiguity now means
  same-`start_date` windows, which still refuse.
- ❌ **"the boundary is armed / no gear tier reads"** — `NEXT_PHASE_BOUNDARY`
  self-retired on the 19:45Z payload. The freeze is lifted; the caller (C1) still
  doesn't exist. A future CHILD-phase boundary still needs the constant re-armed by
  hand — that protocol has precedent now, not code.
- ❌ **"coverage gains are progress toward the gate"** — `3k` P4, falsified by
  measurement. Absent 62.9→59.9 moved the slice **zero** and the producing median
  *down*. Quote the pair together, always.
- ❌ **"the absent-key targets can be read from the committed summary"** — they
  cannot (aggregates only, no per-key rows) until `3l` B0 lands. The `3k` target
  table is pasted tool output whose source artifact was never committed.
- ❌ **"Phase 3 exit criterion 1: MET as written (4 of 41)"** — corrected in the
  phase doc itself, by appending. Current: **0 of 35, NOT met**; 2 of 7 overall.
- Still true and load-bearing: the gate fails CLOSED (a refusal is the guard
  working); the eight rules; `entry_id` ≠ `spells.id`; the catalog's wrong-rank
  problem; "coverage = has a key for, not produces damage for"; the holdout is
  pre-E15 and not comparable; a single multiplier cannot fix the sim (killed `3h`);
  no coefficient fitted to the parse it must later check.

---

## How to review a session (the loop that works)

1. Clone fresh. `PROGRESS.md`, the session's handoff, the work order it ran.
2. **Spot-check claims against committed files, not prose.**
3. **Run the greps the docs imply; run the harnesses** (`check_refusals.py` — 67
   PASS post-`3k`; `check_sim_engine.py` exit 2 on a clone is a verdict, not a
   crash; `check_core_purity.py`).
4. **Check `LIVE` documents against code, both directions, and against post-close
   commits** — `git log` past the close-out before trusting any `LIVE` doc.
5. **Trace headline numbers from the schema up.** Primary keys are where errors are
   decided; summaries are where they hide.
6. Confirm 🛑 stop-points were asked; **check prereg PARENTHOOD, not just order**
   (`git log --format='%H %p %s'` — the prereg must be the commit-parent).
7. **Ask of every check: does it have a regime where it returns a number it cannot
   support?** And: can the fixture even express the defect?
8. **Ask: measured or derived? committed or gitignored?** 🆕 And: **does a quoted
   baseline exist as a committed artifact?** `git show <sha>:<path>` the artifact a
   prereg cites — `3k`'s baseline existed only as prose (audit §3.2).
9. **Re-run the claimed reverts yourself — all of them if the count is small.** The
   `3k` audit re-ran M50–M53 and matched three exactly; the fourth (M50) was red
   with a count that depends on the insertion point — reproduce the substance, note
   the variance. Zero failures under a revert = no check.
10. 🆕 **Re-derive a hard-rule-adjacent constant from the committed extract when
    cheap.** The RV card-id set was found by name-LIKE and verified by this audit
    against `dbc_character_advancement` (exact match, 11-prefix trap live and
    dodged). Ten minutes, and it converts "probably right" into "derived twice".
11. **A named mutation that does NOT go red is a result, not an embarrassment** —
    and a falsified prediction diagnosed to its true cause (`3k` P1: stale baseline)
    is worth more than a confirmed one.

**Tone:** falsifiable checking, not cheerleading. `3k` handled a live incident with
prereg-before-fix and falsified two of its own five predictions in bold — say so
first, then hold the next session to the standard. The criticism that remains
(Block C, artifact hygiene) is about budget, not honesty.

---

## Standing owner actions (not session tasks)

- **Daily:** crawler at logon (Task Scheduler) — post-flip it should run CLEAN with
  the bumped `EXPECTED_PHASE_NAME`. ⚠ If it dies at `assert_phase` ("PHASE FLIP
  DETECTED") again, that is a NEW boundary — save the message verbatim for the
  session record. A silent label-refusal pile-up would now mean same-`start_date`
  windows — also report.
- **Occasional, overnight, manual:** `catchup_crawler.bat`.
- **Per client patch — and NOW SPECIFICALLY ASKED:** `run_dbc_extract.bat` with
  `SpellItemEnchantment.dbc` added to scope (unblocks 200818 + 20424). Last
  *successful* run is the clock.
- **Stat-export addon** — byte-identical at `v2026-08-06c` (its T5 per-parse stats
  still gate Phase 3 criteria 3-full and 4).

## Reproducibility limit (standing)

Tier-2 captures gitignored; no `.db` committed. Corpus figures (472 snapshots, the
RV roster, per-character ratios) are unverifiable from a clone — verify function
behaviour with fixtures, manifest-internal arithmetic, commit parenthood, and
source-edit mutation re-runs instead. The committed manifests and (post-`3l` B0)
the widened per-key summary are the honest perimeter; none of it makes the *inputs*
checkable.
