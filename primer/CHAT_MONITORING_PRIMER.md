# CHAT MONITORING PRIMER v2 — AscensionCrafter

> **`LIVE`** — v2, the current monitoring-chat primer. **Must be true today, and is citable as current truth.** If you find a claim here that the tree contradicts, that is a defect in this file. *(Classified `3f` F8c, 2026-08-07.)*

**Paste this at the start of a fresh monitoring chat.** Supersedes v1. Written
2026-08-06 evening, at the end of the session that audited `3c`, specified and
verified `3d`, and analysed the first non-paladin capture.

This chat's job is **oversight and verification** — Claude Code writes the code
locally. That split is not bureaucratic: everything useful this chat has produced came
from checking Code's output against the tree independently. **If this chat writes the
code, nobody is left to audit it.**

---

## First action, every time

Clone and read the tree. Do not work from prose, this file included.

```bash
git clone --depth 40 https://github.com/Yshaana/AscensionCrafter.git repo
```

The repo is ~130 MB and clones in under a minute. Working from a clone rather than
`curl`-ing individual files is what made this session's findings possible — several came
from `grep`-ing across the whole tree, which per-file fetching cannot do.

Then read `primer/PROGRESS.md`'s top block — it is the pointer to what just happened and
what is next. **If a claim isn't in the tree, it isn't confirmed.**

⚠ **The owner has also connected the local repo to the chat** (`C:\Users\Yshaana\Documents\GitHub\AscensionCrafter`), reachable via
`device_list_dir` / `device_stage_files` / `device_commit_files`. This gives file
read/write on his machine but **no shell** — you cannot run `cli/rebuild.py`, the purity
check, `check_sim_engine.py`, or the gate. Use it for docs and for reading the working
tree mid-session. **Do not use it to write code**: unrunnable code in a repo whose
discipline is "never manufacture confidence" is the exact failure mode `3d` found three
instances of.

---

## What this project is (one paragraph)

A theorycrafting toolkit for **Project Ascension** — a classless WoW private server
(3.3.5 client, realm **Darkmoon**, Season 10) where characters slot abilities and talents
from any class. Five layers: a provenance-enforced spell/mechanics database, a crawled +
live-captured builds repo, a ported-SimC damage simulator, a "lego box" of reusable build
components, and a theorycrafter that designs builds and emits guides. Built in phases by
Claude Code running locally; the owner plays the game and validates findings with real
parses. **The owner is the tier-1 evidence source.**

---

## Where things stand, 2026-08-06 evening

**Session map:** `3d` ✅ done → **`3e` modelling + gate re-run** → `3f` PHASE_3 T6 (log
ingestion) → T7 → re-read Phase 3 exit honestly → Phase 4.

**Phase 3 exit: NOT met.** Gate reads **5 of 41 within ±20%, 2 qualified** (needs 3 and
3). `PHASE_3` lists **seven** exit criteria; four are unmet, one unverifiable, two met.
`ContentProfile` presets (criterion 7) are **failed, not unverified** — 6 of 8 self-declare
`provenance="assumption: …"`.

**Key documents, in reading order for a new chat:**

| File | What |
|---|---|
| `primer/AUDIT_3C_ADVERSARIAL.md` | the adversarial audit — file:line findings, still the reference for what is broken |
| `primer/SESSION_3D_PRIMER.md` | `3d`'s work order; **§11 records Phase 4's hard blockers** so they are not rediscovered |
| `primer/Session_2026-08-06_3d_hygiene_and_instrument.md` | what `3d` actually did |
| `primer/ADDENDUM_3D_slice_accuracy_correction.md` | ⚠ **unlanded correction** — see below |
| `primer/ADDENDUM_3D_to_3E_mage_capture.md` | folds the Mage capture into `3e`; supersedes `SESSION_3D_PRIMER` §7/F2 and §5/D1 |
| `primer/FINDINGS_mage_capture_2026-08-06.md` | analysis of the first non-paladin capture |
| `data/source/captures/2026-08-06_elric_mage_frost/README.md` | its provenance record |
| `primer/ENGINE_BUGS.md` | the six defects `3d`'s fixtures found |

---

## The four open threads, in priority order

**1. 🚨 `casts` provenance, before C2 ships.** The Mage capture found that
`SPELL_CAST_SUCCESS` and `SPELL_CAST_START` are **disjoint by cast type** — instants log
the former, cast-time spells the latter, zero overlap. Frostbolt was cast 74 times with
zero `SUCCESS` events. So the site's `casts` column counts only instants, and `3c`'s
withdrawal of its own "`casts` under-reads the corpus" objection holds only for the
all-instant Hammerdin it was measured on.

**The cheapest first task for a new chat: check whether Boomcat is a cast-time caster.**
`3c` retracted its Boomcat conclusion on an APM ratio of 0.24 against Elric's known death
case at 0.38. If APM derives from `casts`, casters read as artificially low-APM — i.e.
look like death-deflated parses. That one lookup settles whether this is urgent or merely
interesting, and it is a `scouted_builds.db` / crawl query, not an in-game ask.

**2. ⚠ The slice-accuracy correction is written and not landed.**
`predictions/CALIBRATION_TOLERANCE.md:154` still says the modelled slice is
*"over-produced by about 60%"*, from a cohort median of 159.8%. **That median is a
low-coverage artifact** — slice accuracy has coverage in its denominator, and restricted
to characters with ≥20% coverage it is a stable **62.6%** across three thresholds. The sim
**under**-produces on what it models. The correction doc names three edits; the durable
one is making `calibrate_crawled.py` report the median only above a stated coverage floor.

**3. The gate cohort moves on its own — `3e`'s first job.** `candidates()` is
`ORDER BY character_id LIMIT 120` over a population that grew 157→180 mid-session, so
rebuilding `builds.db` moved the gate 5-of-41 → 4-of-38 with **zero code changes**. `3d`
correctly declined to fix it (changing a gate's population is not a hygiene edit) and
pinned the 41 ids in `predictions/gate_manifest.json` so comparisons are at least
checkable. 🛑 **Whatever replaces the sliding window must be chosen before the next gate
result is seen** — a cohort definition picked after observing which characters it admits is
the same failure as moving a gate after seeing its number.

**4. One fixture still missing.** `3d` added a DoT-caster and a combo-point-melee fixture
from crawled boards; the Mage capture now supersedes the synthetic caster with a real one
carrying ground truth on seven abilities. **The combo-point melee fixture has no ground
truth** and no owner capture behind it. Combo points are never incremented anywhere in the
engine, so finishers can never fire — that defect is currently held by a synthetic fixture
alone.

---

## What changed since v1 — corrections worth carrying

Retractions and corrections from this session. **Do not let these creep back.**

- ❌ **"The site's `casts` is `SPELL_CAST_SUCCESS`, generally"** — true for all-instant
  kits, false for cast-time casters (thread 1).
- ❌ **"The modelled slice is over-produced by ~60%"** — low-coverage artifact (thread 2).
- ❌ **"`PHASE_3` has six exit criteria, two outstanding"** — seven, four unmet.
- ❌ **"`ContentProfile` presets are unverified"** — they are **failed**; the file says so
  itself.
- ❌ **"`ingest/logs/` does not exist, therefore T6 does not exist"** — strawman path; T6
  exists as verified manual tools, unsystematised. Promoted to `3f`.
- ❌ **"T5 (capture addon) should be reinstated"** — demoted. ALC + `decode_alc.py` already
  decode every player build in a log.
- ❌ **My own F2, "make the stat-block flags `required=True`"** — superseded. There is no
  stat-block parser in the repo, so four hand-typed flags are the transcription channel
  that caused the contamination. `--stat-block <file>` is the fix.

Still true from v1 and still load-bearing: the **eight rules**, `entry_id` ≠ `spells.id`,
the catalog's wrong-rank problem, class-from-`SkillLine`, and the retracted-claims list.
⚠ `3d` fixed three rule violations that were being *reported as satisfied* — that failure
mode (a guard documented but not implemented) is the one worth checking hardest.

---

## Things I am least sure about — check these rather than inherit them

State these as uncertain to the next session; each is a real gap in what I verified.

1. **The 62.6% slice figure is one gate run.** It is stable across three coverage bands,
   which is reassuring, but it has not been reproduced on a second cohort.
2. **The Frostbolt cast-time gap is not fully explained.** DBC base 2000 ms, client
   1404 ms, log back-to-back floor 1273 ms. I attributed the log floor being *under* the
   client figure to Icy Veins being active — **plausible, unverified**.
3. **The Mage buff decomposition is incomplete.** Per-hit damage moved ~×1.00 while DPS
   moved ×1.396; I attributed the gap to rotation differences (casts/min do differ) but did
   not decompose it fully. Someone should.
4. **I never verified the gate numbers themselves.** `data/derived/` is gitignored and no
   `.db` is committed, so 5-of-41, the 37% coverage and the conflict counts are
   reproducible only on the owner's machine. `gate_manifest.json` now pins the cohort,
   which helps, but the underlying corpus is still unauditable from the repo alone.
5. **Whether `3d`'s six engine defects are the *only* ones the fixtures can expose.** They
   were found in one pass. The fixtures are permanent; nobody has run them adversarially.

---

## How to review a session (the loop that works)

1. Clone fresh. Read `PROGRESS.md`, then the session's own handoff.
2. **Spot-check claims against committed files, not prose.** Every significant finding this
   session came from reading code that contradicted a document.
3. **Run the greps the docs imply.** "This guard is implemented" is checkable in seconds;
   three of `3d`'s Block C items were guards that existed only in prose.
4. Check the eight rules and the retracted-claims list for regressions.
5. Confirm 🛑 stop-points were asked, not guessed.
6. **Ask of every check and metric: does it have a regime where it returns a number it
   cannot support?** This session found four fail-open or fail-misleading instruments —
   `check_alignment()` passing vacuously off-Hammerdin, the extract wrapper's "game is
   closed" check, two of Code's own `3d` checks, and slice accuracy at 1% coverage. It is
   the most productive single question to ask here.

**Tone:** this project's value comes from falsifiable checking, not cheerleading. If
something looks off, say so plainly, with the file:line. If it is genuinely good, a short
confirmation is enough.

---

## Standing owner actions (not session tasks)

- **Daily:** the crawler runs automatically at logon (Task Scheduler). `3d` hardened it —
  row-count canary, scoped auto-commit, changelog exit code, live phase assertion.
- **Occasional, overnight, manual:** `catchup_crawler.bat` — deliberately not scheduled.
- **Per client patch:** `run_dbc_extract.bat` (double-click). ⚠ Its last **successful** run
  is the staleness clock, not its last commit.
- **The stat-export addon is at `v2026-08-06c`** — timestamps, resources, board, action
  bars, pet, and a `GetSpellInfo` signature probe. Verified byte-identical to the repo copy.

## 🚨 Time-critical

**The server flips to Phase 2 on 2026-08-08.** `3d` centralised the season/realm constants
and made the crawl hard-fail on a stale phase, so this should now announce itself rather
than silently mis-stamp — **but nobody has seen it fire.** Check on the 8th that the flip
was detected and that `gear_tier_stats`' `phase_label` stops being NULL.
