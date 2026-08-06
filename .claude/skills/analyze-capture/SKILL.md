---
name: analyze-capture
description: Safely ingest and analyse a combat log or stat export before deriving any number from it. Use whenever a WoWCombatLog.txt or an AscensionCrafterExport stat block is about to be parsed, including files already sitting in data/source/captures/.
---

# Analyse a capture

Every step here exists because skipping it has already cost this project a
measurement. Run them in order and **print each result** — a check whose output nobody
saw is a check that did not happen.

## 1. Is the file finished?

**A log the game is still writing to is not a capture.** Confirm size and mtime are
unchanged across a short interval before reading a byte. A 2026-08-05 session analysed
a truncated 46-second window and had to redo the work.

🛑 **If you cannot check, say so and stop.** `3b` found the owner-facing wrapper's
"is the game closed?" check printing *"OK - game is closed"* after erroring — Git for
Windows' Unix `find` had shadowed the Windows one on PATH. **A guard that silently
passes when it breaks is worse than no guard, because it manufactures confidence.**

## 2. Report the window before reading anything from it

Line count · first timestamp · last timestamp · **window duration in seconds**.

⚠ Flag any conclusion drawn from under ~60 s of data as **provisional**, in the output.

## 3. Use the parser, never hand-indexed columns

```
py tools/log_parser/parse_log.py <file>
```

Needs `combat_log_parser.py`, `decode_alc.py` and `d1_dict.bin` alongside it. Its event
parsing is verified against real Ascension logs. **Use its named fields.** The `2e`
session's one parsing error was a throwaway script hand-counting columns and reading
`glancing` where it wanted `critical`.

If you must parse directly anyway, **print the header row and echo your column-index
mapping before extracting** — and assert on names, never on positions.

## 4. Establish what the capture cannot tell you

Before any number leaves this step, state which of these apply:

- **Stat block pairing.** Does an `AscensionCrafterExport` accompany it, and does its
  `ExportedAt` fall inside this log's window? A stat block from a different session is
  not a degraded input — for weapon-dominated abilities it is *the whole error*.
  ⚠ A zero-delta pair (buffed block byte-identical to unbuffed) is the read-too-early
  trap, not a clean measurement.
- **Dummy identity.** Two sessions an hour apart with an identical unbuffed character
  differed **10–18% on every ability** because one dummy scales to player level and the
  other is a fixed 63. Read the target's name out of the log, not out of memory.
- **Buff state.** Buffs on the player are recoverable from the log itself —
  `SPELL_AURA_APPLIED`/`_REFRESH` with `dstName` = the character, plus the
  `REMOVED − APPLIED` difference for auras already running when the log opened. Do this
  rather than assuming; it is how the 2026-08-06 Mage dungeon window was de-confounded.
- **Death, OOM, channels, freeze-dependent crit.** Each makes a parse read wrong for a
  reason that is not a model error. `deaths` is proven unobtainable from the site API.
- **Segmentation.** Boss and trash mixed in one window makes any per-encounter or
  target-count number meaningless. Split before deriving.

## 5. Ratios over absolutes, and check the ratio actually cancels

A damage multiplier measured against a parse **is not a constant** — it moves with buff
state. Never pool logs to fit one. Prefer a ratio between two things measured in the
same log.

🛑 **But a ratio cancels shared factors, not a one-sided input error.** Holy ÷ Holystrike
does not cancel a stale weapon input, because one side is 86–100% weapon damage and the
other is 0%. Before trusting any ratio, check that **both sides depend on the same
inputs**.

## 6. Write it down where it survives

Findings go in `primer/FINDINGS_*.md` or a session record; the capture gets a
provenance `README.md` in its own folder under `data/source/captures/`, with a table of
what was **verified from the artifacts** versus what was asserted. Verdicts that change
a project belief also go in the seeds — see `/close-session`.
