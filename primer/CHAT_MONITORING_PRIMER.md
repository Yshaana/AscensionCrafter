# CHAT MONITORING PRIMER v5 — AscensionCrafter

> **`LIVE`** — the standing brief for the oversight chat. **Must be true today, and is
> citable as current truth.** Supersede at **v6** when `3j` closes. *(v4 expired the
> moment `3i` closed and — for the third consecutive version — was still marked `LIVE`
> when the next audit found it. **If you are reading this after `3j` has closed, it is
> stale: say so and rewrite it.** The fix `3j` C2 owes is committing THIS content into
> `primer/CHAT_MONITORING_PRIMER.md` — **the file is versionless and updated in
> place; the version lives in the title line only. Never commit a `_v5` sibling:** a
> versioned copy beside the live file is the exact mechanism by which v2–v4 each
> stayed marked `LIVE` after expiring.)*

**Paste this at the start of a fresh monitoring chat.** Supersedes v1–v4. Written
2026-08-08, at the end of the session that audited `3i` and drafted `3j`.

This chat's job is **oversight and verification** — Claude Code writes the code locally.
If this chat writes the code, nobody is left to audit it.

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

## Where things stand, 2026-08-08 (post-`3i`)

**Session map:** `3d`✅ → `3e`✅ → `3f`✅ → `3g`✅ → `3h`✅ (instruments) → `3i`✅ (gate
repair: E15 fixed, admissibility applied) → **`3j` (integrity, work order written)** →
`3k` (modelling/coverage) → re-read Phase 3 exit honestly → Phase 4.

**The gate:** `0 of 36 within ±20% · 0 qualified · slice accuracy 26.3% at coverage
≥20% (n=23)`. It moved twice in `3i`, each with a pre-registration: `1/1/20.5%` →
`1/1/26.3%` (E15 fixed at ingest — logged DPS was pet-inflated) → `0/0/26.3%`
(admissibility applied; the only passer, `Boomcat`, was a compensation pass on an
inadmissible parse). **Zero passers is the honest state, not a regression.**
Holdout: **not re-read since `3g`** — `0 of 5`, median slice 9.8% (n=4) — and 🚨 **it
is pre-E15**: computed against the inflated logged side, so it is not like-for-like
with the 26.3% tuning figure. Phase 3 exit (≥3 of 36): **NOT met.**

**The distribution that decides `3k`'s shape** (`predictions/per_ability_summary.json`,
committed, tool-produced, internally consistent — verified): **63.9%** of cohort
logged damage has **no sim key at all**; 24.8% producing; 11.3% keyed-but-starved
(GCD allocation, not refusals). Producing median ratio **0.273**, 58.4% of sim damage
lands on abilities the log never saw (phantom production). **Slice is arithmetically
capped near ~36% until absent keys exist** — `3k` is a coverage problem first, a
tuning problem second.

**Key documents, reading order:**

| File | What |
|---|---|
| `primer/PROGRESS.md` | live state — top block first |
| `primer/AUDIT_3I_ADVERSARIAL.md` | current audit; §10 is the list `3j` works from |
| `primer/SESSION_3J_PRIMER.md` | the work order in flight |
| `primer/Session_2026-08-07_3i_gate_repair.md` | what `3i` actually did |
| `predictions/gate_manifest_3e.json` | ⚠ named `3e` (frozen cohort slug), holds **current** numbers, ⚠ no status key yet |
| `predictions/per_ability_summary.json` | the repaired distribution — pick modelling targets from THIS |
| `predictions/CALIBRATION_TOLERANCE.md` | stamped tolerances — ⚠ band table stale until `3j` C3 regenerates it |
| `primer/ENGINE_BUGS.md` | defect registry — Checks rows parser-enforced; ⚠ mutation table is NOT (M32/M33 missing) |

---

## The open threads, in priority order

**1. 🚨 The phase flip fired last night (`2026-08-08T00:00:00Z`) and the admissibility
rule turns a payload outage into a cohort verdict.** `resolve_phase`'s FIRST branch
returns the payload-level `refuse_reason` for every timestamp (`phases.py:233-234`);
`admissibility_for` passes it through → all 41 members flagged "unresolved phase" →
gate publishes `0 of 36` on an infrastructure outage. The crawler writes the post-flip
payload **before** `assert_phase` raises, so the poison payload is on disk the first
morning. **Any gate number produced post-flip, pre-fix, is invalid.** `3j` Block 0.

**2. 🚨 The gate fails OPEN on stamp drift, then asserts the rule ran.**
`calibrate_crawled.py:830-837` sets `pa = None` and continues when
`assert_stamped_thresholds()` fails; `:1581` hardcodes
`parse_admissibility_rule_applied: True`. A drifted stamp ships a manifest claiming a
rule that did not run. `3j` A1.

**3. 🚨 The D5 comparator tightening is un-pre-registered and one-way.** The change
landed 7 seconds *before* its prereg, which covers only the wiring; its measured
effect (blind roster 5→3 of 41) was in the change's own commit message. Every arm can
only remove flags. Under `3h` P9's registered predicate: 0 failing removed, 1 passing
removed — the exact asymmetry `CLAUDE.md` calls a fitting device. Honestly disclosed,
wrongly sequenced. `3j` A2. The stamp↔code assertion (D6) checks three regex'd numbers
and is blind to the comparator definition — the thing D5 changed. `3j` A3.

**4. 🚨 E15 is fixed only for fresh ingests, and its check cannot fail.** No migration,
no `user_version`; legacy DBs still double-count through three `is_pet`-blind
consumers; the committed check exercises a hand-built fixture, not the corpus; a
NULL-`spell_id` row bypasses PK dedupe in both tables (reachable — 5 report ids
re-ingest). `3j` B1–B3.

**5. ⚠ E3's repair has no check (full revert leaves the suite green) and dropped rows
it must name** (zero-producing auto keys with no logged auto row vanish from the
named zero list). E2 is still green under the `3h`-registered mutation. `3j` A4–A5.

**6. ⚠ Four+ sessions old, needs a decision not a carry:** `gear_tier_stats(phase=…)`
has no production caller (Phase 3 exit 10 reads ✅ on a function nothing calls);
`ContentProfile` presets are 6/8 `provenance="assumption:…"` (criterion 7, open since
`3d`).

---

## Corrections worth carrying — do not let these creep back

- ❌ **"1 of 36 / 1 qualified / 20.5%"** — pre-`3i`. Current: **0 / 0 / 26.3%**.
- ❌ **"E15 is not fixed"** — fixed at ingest+dps in `3i` B (`corpus.py`), verified by
  execution. What remains is migration + a check that can fail (thread 4).
- ❌ **"62.2% absent, indeterminate sign / producing median 0.253"** — pre-repair
  figures. Measured post-repair: **63.9% / 0.273**. The move is **Block B's corpus
  fix**, not Block C's dedupe — the dedupe is dormant by construction post-B.
- ❌ **"5 of 41 flagged"** — the stamped figure. Post-tightening: **3 of 41**
  (Nodding, Boomcat, Deyindra) — and under the narrow P9 predicate, 0.
- ❌ **"the admissibility rule is stamped but NOT applied"** — applied `3i` D
  (`0fbffd5`). ⚠ `CLAUDE.md:199` still says otherwise until `3j` C1 lands.
- ❌ **"the sim is ~5× under, uniformly"** — killed `3h`. Absent for most, zero for a
  tenth, both directions on the rest; a single multiplier cannot fix it.
- ❌ **"the holdout (0 of 5, 9.8%) is comparable to the 26.3% tuning slice"** — it is
  **pre-E15**; the corpus under it was corrected afterwards. Annotate or re-read
  (`3j` C6) before citing the pair together.
- ❌ **"E13 is ~78×"** — exactly 100, unit error, fixed `3g`. — ❌ **"64.3% slice"** —
  measured on the 100× auto sim, dead since `3g`.
- Still true and load-bearing: the eight rules, `entry_id` ≠ `spells.id`, the
  catalog's wrong-rank problem, class-from-`SkillLine`, "coverage = has a key for,
  not produces damage for".

---

## How to review a session (the loop that works)

1. Clone fresh. `PROGRESS.md`, the session's handoff, the work order it ran.
2. **Spot-check claims against committed files, not prose.**
3. **Run the greps the docs imply**; run the harness (`check_refusals.py` runs clean
   on a clone; `check_sim_engine.py` needs the local db — but see `3j` A6).
4. **Check `LIVE` documents against code, both directions.** Document discipline has
   now been the weaker half for **three** consecutive sessions.
5. **Trace headline numbers from the schema up.** Primary keys are where errors are
   decided; summaries are where they hide.
6. Confirm 🛑 stop-points were asked; **check prereg commit ORDER against the change
   commit** — `3i`'s sharpest finding was a prereg landing 7 seconds *after* the
   change it "predicts", with the effect already in the change's commit message.
   `git log --format='%H %ci %s'` takes seconds.
7. **Ask of every check: does it have a regime where it returns a number it cannot
   support?** Still the most productive question. New sub-question from `3i`: **can
   the check's fixture even express the defect?** (E2's correct answer *was* the
   maximal-producing answer; E1's fixture had no auto rows.)
8. **Ask: measured or derived? committed or gitignored?** And new from `3i`: **does
   the mutation claimed as "registered" exist in the registry?** (M32/M33 don't.)
9. 🆕 **Run the claimed repairs' reverts.** The one-line test that found `3i`'s worst
   check finding: revert the fix (`if False:`), run the suite, count failures. Zero
   failures = no check.

**Tone:** falsifiable checking, not cheerleading. `3i` earned real credit — E15 at the
right layer, a falsified prereg reported without rescue, the committed distribution
artifact — and its audit says so in §1 before anything else. Do the same.

---

## Standing owner actions (not session tasks)

- **Daily:** crawler at logon (Task Scheduler) — ⚠ **post-flip it will be dying at
  `assert_phase` until `3j` Block 0 runs; the poison phases payload is still written.**
- **Occasional, overnight, manual:** `catchup_crawler.bat`.
- **Per client patch:** `run_dbc_extract.bat` — last *successful* run is the clock.
- **Stat-export addon** — byte-identical at `v2026-08-06c`.

## Reproducibility limit (standing)

Tier-2 captures gitignored; no `.db` committed. Corpus figures (15,551 / 22,427 /
530.5M / n=23…) are unverifiable from the clone — verify function behaviour with
synthetic fixtures and manifest-internal arithmetic instead. The committed
`per_ability_summary.json` and clean-tree `git_sha` manifests are real progress;
neither makes the *inputs* checkable.
