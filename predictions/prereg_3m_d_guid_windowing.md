# Pre-registration — `3m` Block D: encounter windowing on GUID, kill selected explicitly

> **`FINDING 2026-08-08`** — committed BEFORE the tool it predicts. Verify with
> `git log --format='%H %p %s'` that the commit carrying the results is a child of
> this one. True as of its date, not maintained.

🛑 **SCOPE, stamped by the owner 2026-08-08: THE WINDOWING ONLY.**
`infer_coefficient` is **not run** this session and **no coefficient is seeded**. The
derivation is handed to `3n` with the windowing landed under it.

**The owner's stated reason, recorded because it is the better half of the decision:**
`3l`'s wrongest seeded fact — aura 344, corrected in this session's C3 — was written at
`49b5fde`, its *second-to-last commit*. **Seeding in a session's tail is this
project's known failure mode**, and E2 feeds Phase 3 exit criteria 3-full and 4. A
carry with the hard part done is worth more than a derivation done tired.

**This is E2's SECOND carry** (`3l` §8 item 1 handed it over already). Block C's
precedent applies: it is stamped as a carry, by name, rather than allowed to drift.

---

## The defect this closes

`3l` §5 states, of the Molten Core capture: *"GUID `0xF130002FE3000994` … one
`UNIT_DIED` at 20:02:55.246. **One pull, never two encounters.**"* That is **true of
the GUID it checked** and it **invites the mis-window it was written to prevent** — a
reader takes "one pull" as a property of the boss and windows on the boss's name.

Measured from the committed bytes this session, both log halves:

| boss | GUIDs | kill | note |
|---|---:|---|---|
| Lucifron | 1 | `…56000055` @ 19:45:41 | the easy case |
| Magmadar | **2** | `…CE0004B5` @ 19:40:47 | `…CE0000B2` is a wipe |
| Gehennas | **2** | `…E3000994` @ 20:02:55 | `…E3000058` is a wipe, 19:52:51–19:54:56 |
| Garr | **4** | `…19000FD7` @ 20:41:14 | three failed pulls first |
| Baron Geddon | **3** | **none** | no kill in this capture |

**The cost of getting it wrong, measured:** first-mention-of-the-name → `UNIT_DIED` on
Gehennas spans **603.6 s** against the kill GUID's **379.8 s** — it folds in a 125 s
wipe and ~100 s of downtime, deflating DPS by ~37% on the capture whose entire value is
per-parse calibration.

⚠ **And the correct window still is not clean**, which is the second thing a caller
must be told: the Gehennas kill spans the client crash (half 1 ends 19:57:30, half 2
resumes 19:58:30), so **~60 s of its 379.8 s wall-clock window has no log at all**.
A window is not the same as coverage of that window.

---

## Predictions

🆕 Falsifier is symmetric: a refusal where a kill exists falsifies just as hard as a
window where the tool should have refused.

**P1 — the tool returns exactly one window per boss WITH a kill, on the kill GUID:**
Lucifron `…56000055`, Magmadar `…CE0004B5`, Gehennas `…E3000994`, Garr `…19000FD7`.
*Direction: exactly these four, no others.*

**P2 — Gehennas' window is 379.8 s (±0.2 s), NOT 603.6 s.** *Direction: the shorter
one.* This is the whole point of the block; the naive figure is stated so the two can
never be confused.

**P3 — Baron Geddon REFUSES by name.** Three GUIDs, no `UNIT_DIED` on any: the tool
returns no window and says *why* (attempts present, no kill), rather than returning
the longest attempt or the last one. *Direction: refusal, not a best guess.*

**P4 — the crash gap is REPORTED, not silently absorbed.** Gehennas' window carries an
explicit note that ~60 s inside it has no log, and the logged duration is stated
separately from the wall-clock duration. *Direction: both numbers present.*

**P5 — a boss with more than one kill GUID would REFUSE**, not pick one. No such case
exists in this capture, so this is asserted on a synthetic fixture. *Direction:
refusal.* An ambiguous answer is recorded as ambiguous — the same rule rank resolution
already follows.

**P6 — the gate does not move.** *Direction: unchanged at `0 of 35 · 0 qualified ·
slice 30.040% (n=24)`.* This block adds a tool and touches no sim path.

### What is NOT predicted, and NOT done

* **No coefficient is derived, and none is seeded.** `infer_coefficient` is not run.
* **Nothing about whether the stat blocks resolve** — that is `3n`'s first act.
* **Anything about the holdout.**
