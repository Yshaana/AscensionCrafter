# SPEC — `/ace` session capture mode (dungeon/raid one-button bracketing)

> **`FINDING 2026-08-08`** — owner-requested design, drafted by the oversight chat the
> evening after `AUDIT_3N`. **Implement in `3o`** (owner decision 2026-08-08: fold into
> `3o`, built early so it's usable in the next dungeon). Supersede when the addon lands
> and its first live capture is committed. This file is a spec, not code — the oversight
> chat does not write the code.

## What the owner asked for, verbatim in spirit

One button at dungeon start, one at the end, no copy-pasting between fights. The addon
detects combat start/stop itself, snapshots with timestamps, and at the end produces ONE
blob to paste. Owner decisions taken 2026-08-08: **auto-toggle combat logging** with the
session; **combat start + end snapshots only** (no mid-combat sampling); **build in `3o`**.

## Why this is the E2 unblock, not a convenience

`3n` Block C proved the blocker: one admissible window is one (stat, damage) point and a
coefficient is a slope. The fix is *a stat block immediately before and after each pull*
(`per_parse_coefficient_needs_two_stat_levels`). `PLAYER_REGEN_DISABLED` /
`PLAYER_REGEN_ENABLED` fire at exactly those two instants. This addon makes the capture
protocol automatic instead of a per-pull owner chore — every pull in every dungeon
becomes a candidate admissible window with its brackets already taken.

## Design constraints (all inherited, none new)

1. **Extend `addons/AscensionCrafterExport` (v2026-08-06c), do not fork.** It already
   has: pcall-wrapped API calls, the copyable EditBox window, the spellbook index→id
   map, and — critically — the stat-block emitter whose `ExportedAt` format
   `tools/analysis/pair_parses_to_stats.py` parses. **The per-snapshot block must reuse
   that emitter** so the parser works unchanged. New lines (see below) are additive;
   verify the parser tolerates unknown lines before the session ends.
2. **3.3.5 client Lua** (WotLK API), every call pcall-wrapped, and the standing rule: **a
   guard that cannot run must say so** — if `LoggingCombat` errors or is absent, print a
   loud "COULD NOT VERIFY LOGGING" line, never a silent OK.
3. **Timestamps in client local time** (`date("%Y-%m-%d %H:%M:%S")`) — the same clock
   the combat log stamps, which is the property the pairing depends on.

## Behaviour

**`/ace start`** (alias `/ace dungeon`)
- If a session is already active: say so, do nothing.
- Read `LoggingCombat()` current state; if already ON, warn (a stale log from a previous
  session is about to be appended to); then `LoggingCombat(true)` and confirm in chat
  with the timestamp. If the call cannot be verified, say so loudly.
- Take snapshot #1, reason `session_start`, as a **full export** (the existing
  `/acexport` content: board, gear, bars — the slow-changing stuff, once per session).
- Register for `PLAYER_REGEN_DISABLED` / `PLAYER_REGEN_ENABLED`.

**On `PLAYER_REGEN_DISABLED`** (combat begins)
- Stat-only snapshot, reason `combat_start`, sequence number, plus:
  - `Target: <name> / <UnitGUID("target")>` if a target exists at that instant (it may
    not — record `Target: none`, never guess),
  - `WeaponMH:` / `WeaponOH:` — the two `GetInventoryItemLink` itemStrings, one line
    each. The enchant id inside the itemString is the **imbue rank per parse**, which
    delivery modelling needs and no stat number carries.

**On `PLAYER_REGEN_ENABLED`** (combat ends)
- Stat-only snapshot, reason `combat_end`, same extras.

**`/ace snap`** — manual stat-only snapshot any time (reason `manual`), for the cases
the events can't see (e.g. re-imbuing between pulls).

**`/ace stop`**
- Final stat-only snapshot, reason `session_stop`; `LoggingCombat(false)` with the same
  verify-or-say-so discipline; unregister events.
- Open the existing copyable window with the whole session as one blob:
  a `SESSION` header (start/stop stamps, snapshot count, combat count, logging on/off
  confirmations), then every snapshot in order, each as a standard `ExportedAt` block
  with its `SnapshotReason:` / `Seq:` / `Target:` / weapon lines.

**Persistence:** append the session buffer into the addon's SavedVariables on every
snapshot, so any `/reload` (e.g. after a wipe) persists everything so far, and offer
`/ace resume` on login if an unclosed session is found. **Stated limit, not hidden:** a
hard client crash loses whatever wasn't persisted by a reload — the combat log file
survives crashes, the Lua buffer does not. The 3m MC capture (client crash mid-raid)
is the precedent; the pairing tool already knows how to handle a gap.

**Size discipline:** per-combat snapshots are STAT BLOCKS ONLY (~40 lines each), never
the full gear/bars dump — a 5-boss dungeon with trash should paste comfortably. Full
export once at `session_start` only.

## Snapshot noise is handled by the comparator, on purpose

A `combat_start` snapshot fires the instant combat begins — pull-triggered procs and
auras may already be on the sheet (the `2e` read-too-early family). This design does
NOT try to outsmart that: `pair_parses_to_stats.py` **refuses** any window whose
brackets disagree, so a noisy snapshot produces a refusal, never a silently wrong
coefficient. More brackets = more candidate windows; the test keeps its teeth.

## Tool-side work in the same `3o` block

1. **Generalise `pair_parses_to_stats.py`** — it is currently hardcoded to the
   2026-08-07 MC capture (fixed path, `EXPECTED_BLOCKS = 6`, hand-typed
   `CRASH_GAP_LOCAL` at whole seconds — `AUDIT_3N` F7). It should take a capture folder,
   read however many blocks the files hold, and **derive capture gaps from the log
   files' own first/last event stamps with milliseconds**, which fixes F7 in the same
   change. `SnapshotReason`/`Target` lines give it window-pairing hints for free.
2. **Parser tolerance check + arm**: one registered check that a block containing the
   new lines still parses to the same stat dict (mutation: a parser that chokes on an
   unknown line).

## Acceptance (live smoke test, owner + oversight)

1. Owner: `/ace start` on a training dummy, one short combat, `/ace snap`, `/ace stop`,
   paste the blob into chat/project.
2. Oversight verifies: snapshot count = combats×2 + start + stop + manuals; every
   `ExportedAt` stamp inside the session window; `Target:` carries the dummy's GUID;
   weapon itemStrings carry the enchant id; `WoWCombatLog.txt` grew during the session
   and stopped growing after `/ace stop`; the generalised pairing tool ingests the blob
   and brackets the dummy combat.
3. First real dungeon capture lands under `data/source/captures/` with a README stating
   window, line count, and snapshot census — the standing capture rule, unchanged.

## Explicitly out of scope (named, not silent)

- Mid-combat periodic sampling (owner decision: not now; if a Duality-style oscillation
  question returns, add an optional `/ace watch` rather than changing the default).
- Any parsing/derivation inside the addon — it captures, the repo derives.
- Auto-upload of any kind; the blob is paste-by-hand by design (the tier-1 evidence
  path stays owner-mediated).
