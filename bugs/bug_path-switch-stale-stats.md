# Path switching leaves stat grants stale until relog

**Status: ❌ withdrawn 2026-08-05 — TWICE, and the second correction is the real
one.** Kept per house style; both wrong diagnoses are instructive.

1. First diagnosis: *"stale until relog"* — wrong.
2. Second diagnosis, from the owner watching the sheet settle: *"~5–10 s delay
   after a path switch"* — **also wrong, or rather a narrow view of the truth.**
3. **Actual cause, found the same evening in the community bug database:
   Path of Duality's AP bonus CYCLES ON AND OFF every ~10–15 seconds,
   indefinitely.** Another player watched AP oscillate 832 ↔ 1128 while standing
   still. Our 174 ↔ 307 is the same oscillation (160×1.10 = 176 with the Str
   bonus off; (160+121)×1.10 = 309 with it on). See
   **[bug_path-of-duality-broken.md](bug_path-of-duality-broken.md)** — already
   reported by others, so nothing to submit from here.

**Method lesson worth keeping:** a settle *delay* and an indefinite *oscillation*
look identical through a single before/after pair. Distinguishing them needs
repeated sampling over minutes, which neither of our first two diagnoses did.

**⚠ The rule that survives withdrawal: after switching paths, WAIT ~15 seconds
before reading or exporting anything.** Any stat measurement taken within the
settle window is contaminated — this retroactively explains every anomalous
path reading in the project's history (the 0.548× AP anomaly, the 2026-08-04
"Duality SP amp" attribution, and today's three mid-settle exports), and none
of tonight's post-relog conclusions are affected (a relog always outlasts the
delay). Not submitted: a ~10 s settle with no combat consequence beyond that
window isn't worth a report unless it's shown to affect combat math mid-window.

---
*Original write-up below, kept for the record:*

**Found:** 2026-08-05, session `2d`, by the owner (Elric, Darkmoon, S10 Wildcard).

## The observation (undeniable)

Character switched **Path of Intelligence → Path of Duality**, then captured stats
via addon (reads the client's own stat API, not a rendered tooltip):

| | before relog | after quit + relog | change |
|---|---|---|---|
| AttackPower | **174** | **307** | +133, gear/board/path identical |
| MainHandDamage | 380.6–483.3 | 415.4–518.1 | +34.8 ≈ ΔAP/14 × 3.57 ✓ |
| OffHandDamage | 347.9–429.3 | 381.7–463.1 | +33.8 ≈ ΔAP/14 × 3.47 ✓ |
| every other stat | — | — | unchanged |

Nothing but quitting and logging back in changed. The post-relog value matches
Duality's stated formula: (base 160 + Str 121) × 1.10 Deadliness = **309** ≈ 307.
The pre-relog value is the previous path's state surviving the switch.

## Diagnosis (offered separately, may be wrong)

The path switch applies some grants immediately but does not recompute
stat-conversion grants (here: Duality's `AP = highest of Str or Agi`); a full
login recomputes everything. If so, **any measurement or play session right
after a path switch runs on a mix of the old and new paths' stats.**

## Why it matters beyond cosmetics

Weapon damage on the sheet moved with the stale AP, so this is at minimum a
character-sheet-wide staleness, not one bad tooltip. Whether server-side combat
used 174 or 307 pre-relog is the open half (below).

## Steps to reproduce

1. On a path with a stat-conversion grant active, note AttackPower.
2. Switch to a different path with a different AP rule. Note AttackPower — it
   does not (fully) update.
3. Log out and back in. AttackPower now matches the new path's formula.

## What's still needed before submitting

- **Does combat use the stale value or the correct one?** Cheapest check: ~20
  white swings on a dummy immediately after a path switch (no relog), then ~20
  after relog, same gear. If mean swing damage moves ~+9% (34/415), combat was
  using the stale AP → real gameplay bug. If not, display/API staleness only —
  still reportable, lower priority.

## Second demonstration (same day, three-path capture)

A three-path capture series produced a quantified example of *partial*
application. A capture taken on **Path of Strength** — a path with no Spell
Power clause at all — read **SP 500**, which decomposes as **2.0× (item SP 229 +
Lunar Guidance 21.6)** to within rounding (ratio 1.995): **Path of
Intelligence's item-and-effect doubling was still active on a Path of Strength
board.** In the same capture, the flat grants had updated correctly (Str 155 =
base 121 + the +34 PoS flat curve, exactly; AP 348 matching PoS's formula).

So the split is: **flat stat grants and AP rules re-apply on switch; multiplier/
conversion auras from the previous path persist until relog.** The owner
confirmed no relog preceded that capture; after relogging on the same path, the
same board read **SP 250 = items 229 + Lunar Guidance 21.6** — the correct
clean value, exactly half the contaminated reading.

## Notes for us (not for the report)

- **This bug retroactively contaminates every rapid path-toggle measurement**,
  including the 2026-08-04 empty-spec PoS↔PoD test in
  `wip_winds-of-winter-frostblade.md` §4 (`duality_sp_amp_confirmed_reverses_retraction`)
  and the 0.548× `duality_attack_power_anomaly` (174/307 = 0.567 — same bug,
  measured twice). Any future path measurement: **switch → relog → then read.**
- Owner's standing workaround: always relog after switching paths.
