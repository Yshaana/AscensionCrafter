---
name: close-session
description: Land the phase plan's remaining deliverables, sync the docs, commit and push. Use at the end of any phase/work-order session, or when the owner asks whether the session is ready to close.
---

# Close the session

This encodes `primer/START_HERE_FOR_CODE.md`'s session protocol so it is invoked
rather than remembered. **A session is not done when the code is written** — it is done
when the code runs, the docs match what was actually built, and the next session could
be started by someone with no memory of this one.

## 1. Deliverables first — report before you fix

Re-read the phase doc `PROGRESS.md` names and list **every concrete artifact** it
required: each code file, seed row, doc section and commit.

Print a table of **DONE vs NOT LANDED** before doing anything else. Do not quietly
land the missing ones and present a clean list — the owner needs to see what nearly
slipped, because that is the signal about how the session was spent.

Then land what is missing. If something cannot be landed, it becomes a row in
`PROGRESS.md`'s plan-changes table with the reason, not a silent omission.

## 2. Sync the seeds — same session, not "next time"

- A verdict changed, a retraction, a new resolution, an updated stat weight →
  `ingest/export/seed_confirmed.py`
- A question resolved or a claim retracted → `ingest/export/seed_epistemics.py`
- A new external engine written up in `builds/shared/` → `ingest/export/seed_synergies.py`
- A game bug or tooltip-vs-log discrepancy found along the way → a row in
  `bugs/README.md`. ⚠ **Engine defects in OUR code do NOT go there** — that folder is
  the Ascension submission queue. They go in `primer/ENGINE_BUGS.md`.

**Prose is not a seed.** A verdict that exists only in a markdown file is invisible to
the next rebuild, and doc-vs-tree drift is this project's most expensive failure mode.

## 3. Write the handoff

- `primer/Session_<date>_<topic>.md` — what was actually done, including what failed.
- `PROGRESS.md` — mark this session's status, set the next session, record plan changes.
- Amend the phase doc where reality differed from it, saying what changed and why.
- 🛑 **Record every 🛑 you stopped at and what the owner decided.** A guessed answer to
  a stop-point is worse than an unanswered one.

## 4. Commit safely

```
git status --short
```

- Check for any staged file over 5 MB. Never commit a `.db` or a raw DBC dump.
  (`.claude/hooks/block_large_staged_files.ps1` should catch this — but verify it has
  actually been tested before relying on it; see `.claude/README.md`.)
- Write the commit message **now**, describing what this session did. Do not reuse a
  message staged during an earlier attempt.
- One commit per block where the session had blocks — a single squashed commit makes a
  later bisect useless, and this project has already needed one.
- Push, then show `git log --oneline -5`.

## 5. State the invariant

If the session had a numeric invariant (a gate reading, a row count, a cohort size),
**report it opening and closing.** If it moved, stop and say so with the cause — never
fix it forward and never report the closing value alone.
