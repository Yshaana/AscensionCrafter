# START HERE — Orientation for Claude Code

Read this file first, every session. It is deliberately short. It tells you what the project is, what
you're allowed to assume, and **which other files to read for the work in front of you.**

---

## What this is

**Project Ascension** is a classless WoW private server (3.3.5 client) where any character can slot
abilities and talents from any class. This repo is a theorycrafting toolkit for it: a spell/mechanics
database, a corpus of real player builds, a damage simulator, a component ("lego") library, and a
guide generator.

The project owner is not a coder. He plays the game, runs tests in-game, and validates or falsifies
your analysis with real parses. **He is the tier-1 evidence source.** When he corrects you, he's
usually right, and the correction should end up in the docs.

---

## Reading rules

| Always read | Read only when executing it | Never read speculatively |
|---|---|---|
| This file | The **one** phase doc `PROGRESS.md` names | Other phase docs |
| `primer/PROGRESS.md` — tells you what session is next | | |
| `primer/ARCHITECTURE.md` | | |
| `primer/RECON_FINDINGS.md` (once it exists) | | |

Phase docs reference each other by task number (e.g. "Phase 2 T7"). **Follow a cross-reference only
when you actually need that specific detail** — don't preload the whole file.

Also read, when relevant to the task: `primer/Ascension_Context_Primer.md` (game mechanics and
hard-won rules), `primer/INDEX_GUIDE.md` (existing schema and conventions), and the latest
`primer/Session_*.md`.

**GitHub is the source of truth.** Fetch fresh rather than trusting a summary. Memory and handoff
prose lag behind commits — this has produced a confidently wrong answer in this project before.

---

## Current state (as of 2026-08-04)

- Season 10, realm **Darkmoon**. A second realm, **Dawnrise**, exists and receives *different*
  balance changes — never apply a fact across realms without evidence.
- **Server is on Phase 1 (Zul'Gurub). Phase 2 launches 2026-08-08.**
  ⚠ The logs API's `phase_number` field does **not** match this label — its `phase_number=2` record is
  named "Phase 1.1" and is a child of Phase 1. Read `name` + `progression_parent_phase_id`, never
  `phase_number` alone.
- ✅ **The crawler (Phase 0 Task 6) is built and running** as of 2026-08-04 — `run_crawler.bat`,
  double-clicked once a day. 🚨 **One deadline item remains: run `py tools\scrapers\baseline_phase1.py`
  before Aug 8.** Reports persist across a phase flip, so historical parses are safe; the
  *leaderboard standings and armory snapshots* are what cannot be recovered afterward.
- The project owner runs **Windows**. Scripts meant to run on his machine (the crawler, the addon
  ingest, session hooks) target Windows — no cron, no bash-only assumptions. The crawler is
  **manual-first**: launched by hand until proven, scheduled later.
- **The server patches daily.** Facts decay. Everything is stamped with patch, realm, and season.

---

## The eight rules that matter most

Violating any of these quietly poisons everything downstream. They're expanded in
`ARCHITECTURE.md` §2 — this is the version to keep in your head.

1. **No value without provenance.** Source tier, evidence pointer, patch/realm/season, confidence —
   all `NOT NULL`. A number with no source cannot be inserted.
2. **Never fabricate precision.** If a formula or magnitude is unconfirmed, say so loudly. Never
   silently default a NULL field to a plausible number.
3. **Conflicts are surfaced, never auto-resolved.** Two sources disagreeing → record both, flag
   `conflict`, queue for human verification. Auto-picking a winner is how confidently wrong data gets
   created.
4. **Never read a DBC `description` string for a magnitude.** Numeric fields only. A stale
   description string once cost this project a session (Titanic Mutilate: text said 115%, the field
   said 70%).
5. **Never string-match to identify a spell, and never relate two IDs by name.** Join through the ID
   crosswalk, and **fingerprint on mechanics** (radius, cooldown, cast type, cost, effect structure)
   before treating two IDs as the same ability, a variant, or two ranks. Two spells named "Holy
   Supernova" (`270182`, `81193`) are unrelated. String matching produced a real undetected bug;
   name-based ID relation produced two retracted conclusions in a single session.
6. **Stop and ask rather than guess.** 🛑 marks explicit stop-points. Guessed assumptions have burned
   this project repeatedly — a wrong spell ID, a stale coefficient, a JS-required belief that turned
   out false.
7. **Retract explicitly, with the reason recorded.** Being wrong is fine and expected. Being quietly
   wrong is not.
8. **Pure logic layer.** `core/` has no `print()`, no `argparse`, no hardcoded paths, and takes a
   connection as a parameter. This is what lets a web app reuse everything later.

---

## Session protocol

**The standing prompt is always the same:**

> Read `primer/START_HERE_FOR_CODE.md`, then continue from `primer/PROGRESS.md`.

`PROGRESS.md` holds the pointer to what's next. You maintain it — the project owner should never have
to remember which session number is up.

1. Fetch the repo's current state. Read this file, then `PROGRESS.md`.
2. Read `ARCHITECTURE.md` and **only** the phase doc for the session `PROGRESS.md` names.
3. State what you're about to do and confirm before writing code.
4. Build it. Stop at any 🛑 and ask — log the question in `PROGRESS.md`'s blocked table.
5. **Before ending the session:**
   - Update `PROGRESS.md`: mark this session's status, set the next session, record any plan changes
   - Amend the phase doc if reality differed from it, noting what changed and why
   - Add any new facts to the seed scripts
   - **Log any game bug or tooltip-vs-log discrepancy found along the way in `bugs/`** — the owner
     submits these to Ascension when he has time, so they must outlive the transcript. File it
     `needs verification` and name the missing check unless the evidence already stands alone
   - Write `primer/Session_<date>_<topic>.md`

**Drift between these docs and reality is the most expensive failure mode in this project.** A doc
that says something untrue is worse than a doc that says nothing.

If the owner wants to jump ahead or redo something, he'll say so — otherwise `PROGRESS.md` decides.

---

## Session breakdown

Phases 0 and 1 are too large for single sessions. The chunking below is what `PROGRESS.md` tracks;
adjust it there if reality disagrees.

| Session | Scope |
|---|---|
| **0b** | Task 6 — crawler + changelog fetcher (manual-first, Windows). ✅ **DONE 2026-08-04** |
| **0a** | Recon Tasks 1–5, 7, 9. Fetching and reading, almost no code. Produces `RECON_FINDINGS.md`. ✅ **DONE 2026-08-04** |
| **1a** | Repo restructure (T1) + patch/realm/season tracking (T2) + crosswalk (T3). ✅ **DONE 2026-08-04** |
| **1x** | Numeric-field DBC extractor (788/803 blocked spells) + settle rank-vs-coefficient. ▶ **next** |
| **1b** | `spell_mechanics` (T4) + relationship graph (T5) — the schema core |
| **1c** | Facts/questions (T6), `spell_profile()` (T7), auto-debugger + test protocols (T8), browsing (T9), volatility (T10) |
| **2a** | Combat engine (T1) + content profiles (T2) + ability model (T3) + build spec (T4) |
| **2b** | Three sim tiers (T5) + uncertainty (T6) |
| **2c** | Weights/paths/curves (T7) + calibration (T8) + prediction ledger (T9) + cache/report/CLI (T10–12) |
| **3a** | Crawl normalisation (T1) + inference (T2) + search (T3) + gear (T4) |
| **3b** | Addon (T5) + logs (T6) + automation (T7) + crawler refinement (T8) |
| **4** | Legos and Theorycrafter, chunked as it goes |

0b came first because the crawler was on a hard deadline; it's done. Everything after Phase 0 is
sequential. **Letters do not imply order** — `0b` ran before `0a`, and `1x` was inserted between
`1a` and `1b` after Phase 0 found a task the original chunking didn't anticipate. `PROGRESS.md`
decides what's next, not the alphabet.

---

## What "done" looks like for a session

Not "code written." A session is done when the code runs, the docs match what was actually built, the
next session could be started by someone with no memory of this one, and anything you were unsure
about is written down as an open question rather than resolved by assumption.
