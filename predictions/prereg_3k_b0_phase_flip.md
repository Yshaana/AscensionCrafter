# Pre-registration — `3k` Block 0: the Molten Core flip, and what re-deriving the corpus does to the gate

> **`FINDING 2026-08-07`** — committed BEFORE the run it predicts. Every
> measurement below is UNMADE at the time of writing; verify with `git log`
> that the commit carrying the results is a child of this one. True as of its
> date, not maintained.

## What happened, before any prediction

`/api/phases`, fetched live at **2026-08-07T19:20:51Z** with the crawler's own
headers (a bare `requests` call gets 403). Verbatim, `locations` arrays elided
and nothing else changed:

| id | name | `phase_number` | `progression_parent_phase_id` | `is_active` | `start_date` | `end_date` |
|---|---|---:|---|---|---|---|
| 1 | `Phase 0` | 0 | `null` | **false** | `2026-07-24T00:00:00.000Z` | `2026-07-31T18:00:00.000Z` |
| 2 | `Phase 1 - Zul'Gurub` | 1 | `null` | **true** | `2026-07-31T18:00:00.000Z` | `null` |
| 3 | `Phase 1.1` | 2 | `2` | true | `2026-08-03T18:00:00.000Z` | `null` |
| 4 | `Phase 2 - Molten Core / Onyxia` | 3 | `null` | **true** | `2026-08-07T18:00:00.000Z` | `null` |

Record 4 has `created_at: 2026-08-04T18:33:46.483Z` — it existed in the
server's database three days early — and the payload captured at
**15:49:07Z today did not contain it at all** (3 records, not 4). So the API
serves a phase record only once its `start_date` has passed.

**This is none of the work order's shapes A, B or C.** Molten Core landed
**top-level** (shape A's diagnostic), but Zul'Gurub **stayed active** — so
there are now **two active top-level phases**, which is the work order's
STOP-POINT 0 (*"two active top-levels → ask before touching the corpus"*).

**Owner decision, 2026-08-07 (recorded before any code was changed):**
*"transitions are additive on this server: raids get added, none removed, so
expect actives to accumulate each phase; don't treat `count == 2` as special."*
`is_active` means *this content is live*, not *this is the current phase*.

## Registered facts, measured before the change

* **Zero corpus captures at or after the boundary.** The latest
  `captured_at` anywhere in `data/source/crawl/*/characters.jsonl.gz` is
  **`2026-08-07T16:02:50.721183+00:00`**, 1h57m before `18:00:00Z`.
  601 character records scanned.
* **The gate, run immediately before the change** (dirty tree, so no manifest
  was written — stdout only): **`0 of 36 within ±20% · 0 qualified · slice
  26.3% (n=23)`**, 3 NOT ADMISSIBLE (Nodding, Boomcat, Deyindra). Identical to
  `predictions/gate_manifest_3e.json` at `ed00608`.

## The change this document precedes

1. `season_config.EXPECTED_PHASE_NAME` → `"Phase 2 - Molten Core / Onyxia"`,
   and the stale *"Phase 2 is scheduled for 2026-08-08"* comment replaced.
2. `current_top_level()` / `current_top_level_phase()` — the active top-level
   phase with the **latest `start_date`** — replaces the `len(tops) != 1`
   refusal arm in both `core.builds.phases.phase_guard()` and
   `season_config.assert_phase()`.
3. The ambiguity protection **moves** to `_overlapping_windows()`: two
   top-level phases claiming the **same** `start_date` still refuse every
   label. Registered mutations **M50** (restore the count arm) and **M51**
   (delete the overlap arm).
4. A fresh `/api/phases` capture appended to
   `data/source/crawl/2026-08-07/phases.jsonl.gz` (2 records now: 15:49Z with
   3 phases, 19:45Z with 4), because `latest_phase_context()` reads the newest
   **committed** payload and the 15:49Z one no longer describes this server.
5. `py ingest/logs_gg/build_builds_db.py` — the corpus re-derivation.

## The prediction

**P1 — the gate reads exactly `0 of 36 within ±20% · 0 qualified · slice 26.3%
(n=23)` after re-derivation**, unchanged in all three numbers, with the same 3
NOT ADMISSIBLE names (Nodding, Boomcat, Deyindra).

*Reason:* the only corpus input the change touches is `phase_label`; no gate
predicate reads it; and no capture falls on the new side of the boundary
anyway.

*Falsified by:* any of the three numbers moving, or the NOT ADMISSIBLE roster
changing. Either way it is **reported, not rescued** — a gate move here would
mean `phase_label` is load-bearing somewhere nobody has looked, which is a
finding worth more than the prediction.

**P1 is unmeasured at the time this document is committed.** The gate has not
been re-run since the change; the last reading is the pre-change one recorded
above.

## Measured while drafting — NOT pre-registered, and not to be read as confirmed predictions

🛑 These three were checked **before** this document was committed, so they are
**observations, not predictions**, and saying otherwise would be exactly the
`3i` failure this file exists to avoid. They are recorded here because they are
the evidence the change is safe, and because a reader is owed the distinction.
None of them can move the gate — all three are pure functions over the existing
`builds.db` snapshots.

| observation | measured |
|---|---|
| The corpus phase census is **byte-identical before and after**: `{Phase 0: 183, Phase 1 - Zul'Gurub: 253}`. Zero snapshots land in the Molten Core window. | ✅ |
| `phase_guard` against the fresh 19:45Z payload returns `refuse_reason = None`, and the declared `NEXT_PHASE_BOUNDARY` **self-retires** (`boundary is None`) because a top-level window now starts at exactly `2026-08-07T18:00:00Z`. | ✅ |
| Against the **stale** 15:49Z payload the same code refuses everything — `PHASE FLIP`, census `{(unresolved): 436}` — which is precisely why step 4 (the fresh capture) is part of this change and not optional. | ✅ |

## What is NOT predicted

* **Per-ability ratios, coverage, and any slice number other than the headline
  above.** Block 0 is a labelling fix; it touches no modelling. Block B's
  coverage work has its **own** pre-registration and its own commit pair.
* **What `gear_tier_stats(phase=…)` returns for Molten Core.** With zero
  post-boundary snapshots, the answer is an empty phase. Block C1's caller is
  scheduled to **refuse with a named reason** rather than report an empty tier
  as a measurement.
* **Whether Zul'Gurub ever goes `is_active: false`.** It may; the model above
  does not depend on it either way, which is the point of reading `start_date`
  instead of the flag.

---

## OUTCOME — appended 2026-08-07 after the run (P1 FALSIFIED AS WRITTEN)

**P1 named `0 of 36`. Both sides read `0 of 35`. The prediction is falsified
as written, and the fault is in the baseline, not in the change.**

The "before" reading P1 quoted was taken against a `builds.db` built at
**14:34 local**, and the daily crawl commit `c23b822` landed at **17:03
local**. So the baseline corpus was missing already-committed source: it held
**436** snapshots where a fresh derivation from the same tree holds **472**.
`0 of 36` was a number from a stale database, and P1 inherited it.

**The pair was re-measured properly**, by checking `season_config.py`,
`core/builds/phases.py` and `data/source/crawl/2026-08-07/phases.jsonl.gz`
back out at `b2ad6c1`, re-deriving, and re-running the gate — so both sides
see the same source tree and differ only in the Block 0 change:

| | tuning set | qualified | slice @≥20% | NOT ADMISSIBLE |
|---|---:|---:|---:|---|
| **before** (`b2ad6c1` code, 472-snapshot corpus) | 0 of 35 | 0 | 26.3% (n=23) | Nodding, Boomcat, Deyindra |
| **after** (`9d29028` code, same corpus) | 0 of 35 | 0 | 26.3% (n=23) | Nodding, Boomcat, Deyindra |

**The Block 0 change moved the gate by exactly nothing** — which is what P1
meant, on numbers P1 got wrong. The 36 → 35 is entirely corpus growth from
`c23b822`; two members changed status inside it (Huskeer left the
zero-modelled bucket and now scores at −93.7% on 33% coverage, and one member
left the simmed set), and **none of it is attributable to phase labelling**:
the admissibility roster is identical, `assert_publishable` did not raise, and
no gate predicate reads `phase_label`.

⚠ **The lesson is the one already in `MEMORY.md` as "the gate cohort slides
with the corpus", arriving from the other direction.** That entry warns against
comparing two gate results across a corpus rebuild. Here the *baseline itself*
was pre-rebuild — a stale `builds.db` is a sliding window with no
`ORDER BY` to blame. **A gate reading is only a baseline if the corpus under it
was derived from the tree you are about to change.** Derive first, then read
the before.

Bands moved with the corpus, not with the change: `≥30%` 17.5% → 19.2%,
`≥50%` (n=9) 15.6% → (n=8) 14.0%. `predictions/CALIBRATION_TOLERANCE.md`'s
table regenerated with `render_band_table.py`, not retyped.
