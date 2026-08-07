# Capture — Elric + raid, 2026-08-07 19:17–21:03 local, **MOLTEN CORE — first Phase 2 raid**

Tier-1, `source='user_provided'`. Supplied by the owner 2026-08-07 evening, hours after
the Phase 2 (Molten Core / Onyxia) flip at `18:00:00Z`, while session `3k` was in
flight. Inventoried and verified in the oversight chat the same evening.

**Full analysis: `primer/FINDINGS_MC_capture_2026-08-07.md`** (delivered alongside;
commit it if it is not yet in the tree). This file is the provenance record.

🛑 **Do not ingest until the two-actives phase fix (3k Block 0, option 1) is landed
and these captures verifiably resolve to Phase 2, not NULL.** Every event here is
post-boundary.

## Files

| File | What |
|---|---|
| `2026-08-07-19.17.12 WoWCombatLog.txt` | **Log half 1**, 19:17:13–19:57:30 local, 581,232 lines. Magmadar KILL, Lucifron KILL, Gehennas pull cut mid-fight by a client crash |
| `2026-08-07-19.58.24 WoWCombatLog.txt` | **Log half 2**, 19:58:30–21:03:30 local, 600,740 lines. Gehennas KILL (same pull, resumed), Garr KILL, Baron Geddon attempts (no kill in-log) |
| `Molten Core.txt` | **Mixed-content**, unlike prior captures: 6 × AscensionCrafterExport stat blocks for Elric (`ExportedAt` 19:46:28 / 20:16:37 / 20:53:52 / 20:54:11 / 20:57:05 / 21:04:29) **plus** 20 `inspects.nie.one` gear/talent links for 18 raid members (captured 19:21–19:35 local) |

Site reports: [116](https://darkmoon.ascensionlogs.gg/reports/116/encounters) ·
[117](https://darkmoon.ascensionlogs.gg/reports/117/encounters) — tier-2 fetch by
report id as usual.

## Provenance — VERIFIED from the artifacts, not asserted

| Condition | Status | How verified |
|---|---|---|
| **Post-boundary timing** | ✅ | Log timestamps are client local (BST, UTC+1): span 18:17–20:03 **UTC**, entirely ≥ the `18:00:00Z` boundary. The 19:17 local start is NOT pre-boundary |
| **The crash split is real and clean** | ✅ | File mtimes corroborate the log content: half 1 last-modified 18:57:30Z = its final line (the crash instant); half 2 last-modified 20:03:32Z = its final line. 60 s gap, no overlap, strictly ordered |
| **Gehennas is ONE pull across both files** | ✅ | Fight running at half 1's final line (19:57:30), still running at half 2's first (19:58:30), death 20:02:55. Stitch or treat as one encounter with a 60 s event gap — never two encounters, never dropped as incomplete |
| **Boss kills** | ✅ | `UNIT_DIED` in-log: Magmadar 19:40:47, Lucifron 19:45:41, Gehennas 20:02:55, Garr ~20:41. Baron Geddon: attempts 20:45–21:00, **no kill event in-log** |
| **Stat snapshots bracket the raid** | ✅ | All 6 `ExportedAt` stamps fall inside/adjacent to the log span; densest around the Geddon attempts (three within 4 min) — the natural first parse↔stats pairing target |
| **Same-evening inspects** | ✅ | Inspect-link timestamps 18:21–18:35Z sit inside the Magmadar window — snapshot-lag ≈ 0 for 18 raid members, several frozen-cohort |
| Roster | ✅ | ~24 players across both halves; player `UNIT_DIED` events present |

## ⚠ Caveats — recorded, not resolved

1. **Timezone:** filenames and every log line are **BST (UTC+1)**; the corpus is UTC.
   Shift before stamping — unshifted, every encounter lands an hour late and the
   capture's start would misread as pre-boundary.
2. **No year in 3.3.5 log timestamps** (`8/7 19:17:13.091`) — take the date from the
   filename, do not assume.
3. **Baron Geddon's outcome is not in these logs.** Any later kill is a different
   capture; do not backfill it from memory or from the site reports.
4. **`Molten Core.txt` is two datasets in one file** (stat blocks + inspect links).
   Prior captures kept these separate; a parser expecting a bare
   AscensionCrafterExport will trip on the URL lines. Split on the
   `=== Elric` block headers.
5. **These are the first per-parse stat snapshots the project has ever had** (the
   T5 unblock for `infer_coefficient`'s `refused:no_per_parse_stats` path). Using
   them for coefficient inference is **`3l`-scope with its own prereg** — not a
   drive-by during ingest.
6. **Arming admissibility predicate 2 (deaths > 0) from log-sourced deaths** is a
   stamp change → owner decision + prereg. The data now exists; the rule change is
   not thereby made.
