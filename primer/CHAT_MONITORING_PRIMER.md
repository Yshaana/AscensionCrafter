# CHAT MONITORING PRIMER v6 — AscensionCrafter

> **`LIVE`** — the standing brief for the oversight chat. **Must be true today, and is
> citable as current truth.** Supersede at **v7** when `3k` closes. *(v5 held to its own
> expiry for the first time in the file's history: its `3j` addendum declared v6 due at
> `3j` close, and this is that rewrite, same-day. Keep the streak. **The repo file
> `primer/CHAT_MONITORING_PRIMER.md` is versionless and updated in place; the version
> lives in the title line only. Never commit a `_v6` sibling** — a versioned copy beside
> the live file is the mechanism by which v2–v4 each stayed marked `LIVE` after
> expiring.)*

**Paste this at the start of a fresh monitoring chat.** Supersedes v1–v5. Written
2026-08-07 (evening), at the end of the session that audited `3j` — the audit is
`AUDIT_3J_ADVERSARIAL.md`, ⚠ **written in the oversight chat and not yet committed to
`primer/`**; committing it is the first document action owed.

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

## Where things stand, 2026-08-07 evening (post-`3j`, post-audit, boundary PASSED)

**Session map:** `3d`✅ → … → `3h`✅ (instruments) → `3i`✅ (gate repair) → `3j`✅
(integrity — machinery fixed, gate untouched) → **`3k` (modelling: coverage first —
work order not yet written; seed it from `AUDIT_3J` §5)** → re-read Phase 3 exit
honestly → Phase 4.

**The gate:** `0 of 36 within ±20% · 0 qualified · slice accuracy 26.3% at coverage
≥20% (n=23)`, 3 of 41 not admissible (Nodding, Boomcat, Deyindra). Unchanged at every
`3j` commit — that was the session's invariant, and it held. **Zero passers is the
honest state, not a regression.** Holdout: carried from `3g`, `0 of 5`, median slice
9.8% (n=4), **annotated pre-E15** (owner decision: annotate, don't spend a re-read) —
not like-for-like with the 26.3% figure, and the direction is known: 9.8% understates
it. Phase 3 exit criterion 1 (≥3 of 36 + the ≥50%-coverage rider): **NOT MET.**

**The machinery, post-`3j` — fail-closed, and independently verified:** a stamp↔code
drift raises instead of running without the rule; a refused `/api/phases` payload
makes the gate **refuse to publish** rather than flag 41 members and print `0 of 36`;
the corpus refuses to be read at the wrong `user_version`; the band table and census
are generated-and-asserted; ENGINE_BUGS' mutation table is parser-enforced (M1..M49,
contiguous). The `3j` audit re-ran three registered mutations from source (M37, M31,
M45) and got the claimed reds. **If you see a gate run refuse, that is the guard
working, not a breakage.**

**The distribution that decides `3k`'s shape** (`predictions/per_ability_summary.json`,
committed): **63.9%** of cohort logged damage has **no sim key at all**; 24.8%
producing (median ratio **0.273**); 11.3% keyed-but-starved. **Slice is arithmetically
capped near ~36% until absent keys exist** — `3k` is a coverage problem first, a
tuning problem second, and must pre-register which it is doing before touching `core/`.

**Key documents, reading order:**

| File | What |
|---|---|
| `primer/PROGRESS.md` | live state — top block first; ⚠ its boundary line is STALE (thread 2) |
| `AUDIT_3J_ADVERSARIAL.md` | current audit; §5 is the list `3k` works from; ⚠ commit it to `primer/` |
| `primer/Session_2026-08-07_3j_integrity.md` | what `3j` did; §6 is its honest not-done list |
| `predictions/gate_manifest_3e.json` | current numbers (status `LIVE`, clean tree, `3e` slug is the frozen cohort name) |
| `predictions/per_ability_summary.json` | the repaired distribution — pick `3k` targets from THIS |
| `predictions/CALIBRATION_TOLERANCE.md` | stamped tolerances + the `3j` A2 comparator amendment (appended, D7 style) |
| `primer/ENGINE_BUGS.md` | defect registry — both tables parser-enforced since `3j` |

---

## The open threads, in priority order

**1. 🚨 MOLTEN CORE IS LIVE and the third shape has no protocol.** Two post-close
owner commits (`139170b`, `efc9baa`, hand-edited 2026-08-07 ~16:50 BST) moved
`NEXT_PHASE_BOUNDARY` to **`2026-08-07T18:00:00Z`** (19:00 BST MC unlock) — that time
has passed. The last crawl (`c23b822`, captured 15:49–16:03Z) is safely
**pre**-boundary: ZG active, no MC record in the payload, corpus clean. What happens
next is the diagnostic:
* **Top-level flip** → next crawler run dies loudly at `assert_phase` ("PHASE FLIP
  DETECTED") — the tripwire working. Then: bump `EXPECTED_PHASE_NAME` (+`SEASON` if
  rolled), re-derive the corpus, verify post-boundary stamping.
* **Payload lag** → `phase_guard` NULLs captures ≥18:00Z; post-`3j` the gate
  **refuses** rather than publishing on them.
* **🚨 Child phase** (the server's own precedent — `Phase 1.1` shipped as a child,
  invisible to `assert_phase` by design) → **no alarm fires and the boundary guard
  can never self-retire** (its disarm condition requires a *top-level* phase ≥ the
  boundary). Every capture from 18:00Z onward stays phase-NULL → inadmissible,
  indefinitely, with no loud failure anywhere. There is no committed protocol for
  manually retiring a child-phase boundary or for labelling post-MC captures.
  **Owner decision + small code path needed — `3k` Block 0.**
Until resolved: **no gear tier reads.** Leaderboards/armory are the only data a flip
destroys; reports persist.

**2. ⚠ Three `LIVE` documents are stale on the boundary and the exit.**
`PROGRESS.md`'s top block still says the boundary "arms `2026-08-08T00:00:00Z`" —
staled by the owner's hand-edits within two hours of being written.
`season_config.py`'s comment still says "Phase 2 is scheduled for 2026-08-08".
`primer/PHASE_3_builds_repo.md`'s exit criterion 1 still carries "⚠ Status
2026-08-06: MET as written (4 of 41)" — **three gate-repairs stale**; current truth
is 0 of 36, NOT met. One document pass, `3k`.

**3. `3k` is a MODELLING session — coverage first, pre-registered.** Expect to
*build* a pass, not defend one. Two named deliverables, owner-scheduled 2026-08-07,
not to be carried again: the `gear_tier_stats(phase=…)` production caller (Phase 3
exit-list item, currently 🟡), and `ContentProfile` presets replaced with
**corpus-measured** durations (criterion 7 — load-bearing: presets feed the sim side).

**4. Phase 3 exit distance — 2 of 7 criteria met** (re-derived from the tree,
2026-08-07): ✅ `find_builds()` (met since `3a`, unmoved); ✅ stamping (met, columns
nullable by design); 🟡 crit-table verdicts (74 proposals / 70 refusals — mechanism
works, output DB gitignored so unverifiable from a clone; `infer_coefficient` refuses
pending T5 per-parse stats); ❌ the calibration gate (0 of 36 — the pacing item);
❌ zero string matching (live `spell_name = ?` match in `inference.py:109`,
`name_fallback` rows in gear); ❌ measured CI (no mechanism at all — downstream of
T5); ❌ ContentProfile provenance (6 of 8 `assumption:…`, scheduled `3k`).

**5. Small carried threads:** the 1,208 owner<pet groups (located, not explained,
0 of 41 cohort members affected); the frozen `gate_manifest.json`'s missing
dirty-tree reason (owner call: annotate the FROZEN status note, or close the thread
as a record); `CHAT_MONITORING_PRIMER.md` — commit THIS content in place as v6.

---

## Corrections worth carrying — do not let these creep back

- ❌ **"the boundary arms `2026-08-08T00:00:00Z`"** — moved by owner hand-edit to
  **`2026-08-07T18:00:00Z`** and now PASSED. Any doc citing the old date is stale.
- ❌ **"the gate fails OPEN on stamp drift"** / **"a payload outage becomes a cohort
  verdict"** — both closed in `3j`, both verified by independent mutation re-runs.
  Current truth: the gate fails CLOSED; a refusal is the guard working.
- ❌ **"E15 is fixed only for fresh ingests"** — `user_version` + migrate-or-refuse
  landed `3j` B1; the session's own v0 corpus was caught by its own check.
- ❌ **"E3's repair has no check"** — M37's full revert now produces 3 named FAILs
  (re-run independently in the `3j` audit).
- ❌ **"AUDIT_3I §4: no arm of the change can add a flag"** — **falsified**, `3j` A2
  P3: filters can add a flag via a raised median (0.76 → 0.42). True of the `<2`
  escape hatch, false of the median.
- ❌ **"Phase 3 exit criterion 1: MET as written (4 of 41)"** — pre-`3g` figure still
  sitting in a `LIVE` phase doc. Current: **0 of 36, NOT met.**
- ❌ **"1 of 36 / 1 qualified / 20.5%"** — pre-`3i`. Current: **0 / 0 / 26.3%**.
- ❌ **"the sim is ~5× under, uniformly"** — killed `3h`. Absent for most, zero for a
  tenth, both directions on the rest; a single multiplier cannot fix it.
- ❌ **"the holdout (0 of 5, 9.8%) is comparable to the 26.3% tuning slice"** — it is
  pre-E15, annotated as such in the manifest, direction known (understates).
- Still true and load-bearing: the eight rules, `entry_id` ≠ `spells.id`, the
  catalog's wrong-rank problem, class-from-`SkillLine`, "coverage = has a key for,
  not produces damage for", and "a refusal is data, not an error".

---

## How to review a session (the loop that works)

1. Clone fresh. `PROGRESS.md`, the session's handoff, the work order it ran.
2. **Spot-check claims against committed files, not prose.**
3. **Run the greps the docs imply**; run the harness (`check_refusals.py` runs clean
   on a clone — 59 PASS post-`3j`; `check_sim_engine.py` needs the local db but its
   doc-sync arms and exit code now work on a clone).
4. **Check `LIVE` documents against code, both directions** — and now also against
   **post-close commits**: `3j`'s top block was staled within two hours by owner
   hand-edits. `git log` past the close-out commit before trusting any `LIVE` doc.
5. **Trace headline numbers from the schema up.** Primary keys are where errors are
   decided; summaries are where they hide.
6. Confirm 🛑 stop-points were asked; **check prereg commit ORDER against the change
   commit** (`git log --format='%H %ci %s'`). `3j`'s A2 shows what an honest prereg
   looks like: it names what it CANNOT register.
7. **Ask of every check: does it have a regime where it returns a number it cannot
   support?** And: can the check's fixture even express the defect?
8. **Ask: measured or derived? committed or gitignored?** And: does every mutation
   claimed as "registered" exist in the parser-enforced table?
9. **Re-run the claimed reverts yourself — do not trust the RED column.** The `3j`
   audit re-ran M37, M31, M45 from source and matched the record exactly; that match
   is what "survived its audit" means. Zero failures under a revert = no check.
10. 🆕 **A named mutation that does NOT go red is a result, not an embarrassment** —
    `3j` kept one in the record (the A1 literal-restore staying green because the
    assertion re-derives the fact). Expect and reward that honesty.

**Tone:** falsifiable checking, not cheerleading. `3j` earned real credit — the audit's
sharpest finding was about the environment, not the session, for the first time since
`3f` — and `AUDIT_3J` §1 says so before anything else. Do the same.

---

## Standing owner actions (not session tasks)

- **Daily:** crawler at logon (Task Scheduler) — ⚠ **post-MC it may die loudly at
  `assert_phase` ("PHASE FLIP DETECTED"). That is the tripwire, not a bug. Save the
  message verbatim for the session record. If it does NOT die, that is ALSO
  information — the child-phase shape (thread 1). Either way, report which.**
- **Occasional, overnight, manual:** `catchup_crawler.bat`.
- **Per client patch:** `run_dbc_extract.bat` — last *successful* run is the clock.
- **Stat-export addon** — byte-identical at `v2026-08-06c`. (Its T5 per-parse stats
  gate Phase 3 criteria 3-full and 4 — see thread 4.)

## Reproducibility limit (standing)

Tier-2 captures gitignored; no `.db` committed. Corpus figures (291,320 rows /
2.82B damage / n=23…) are unverifiable from the clone — verify function behaviour
with synthetic fixtures, manifest-internal arithmetic, and source-edit mutation
re-runs instead. The committed `per_ability_summary.json` and clean-tree `git_sha`
manifests are real progress; neither makes the *inputs* checkable.
