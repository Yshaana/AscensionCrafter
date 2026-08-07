# FINDINGS — Molten Core capture, 2026-08-07 (first Phase 2 tier-1 evidence)

> **`FINDING 2026-08-07`** — inventory and ingest notes for the owner's Molten Core
> raid capture, delivered as `Molten COre.7z` to the oversight chat and inventoried
> there. True as of its date, not maintained. The archive itself is tier-1 owner
> capture: **it is not committed to the repo**; this document is its manifest.

**One line:** two combat logs (1.18M events, split by a client crash), **6 mid-raid
stat-export snapshots of Elric** — the first per-parse stats the project has ever
had — and **20 gear/talent inspects of 18 raid members**, all captured
**post-flip**, in the server's first hours of Molten Core.

---

## §1 — Contents

| File | Size | What |
|---|---|---|
| `2026-08-07-19.17.12 WoWCombatLog.txt` | 89.4 MB, 581,232 lines | log half 1, 19:17:13–19:57:30 client local |
| `2026-08-07-19.58.24 WoWCombatLog.txt` | 91.4 MB, 600,740 lines | log half 2, 19:58:30–21:03:30 client local |
| `Molten Core.txt` | 143 KB | 6 Elric stat-export blocks + 20 `inspects.nie.one` links |

⚠ **All timestamps in the logs and export blocks are client local time (BST,
UTC+1).** Log span in UTC: **18:17–20:03Z** — every event is at or after the
`2026-08-07T18:00:00Z` boundary. The whole capture is **Phase 2 material** and is
stampable only after Block 0's two-actives fix lands; until then it would resolve
phase-NULL. Ingest AFTER the fix, or the parses are flagged inadmissible.

The same raid is on ascensionlogs as **reports 116 and 117**
(`darkmoon.ascensionlogs.gg/reports/116|117/encounters`) — the tier-2 crawler will
pick them up by id at the next logon run (last crawl knew ids through 114).

## §2 — Encounters in the logs

| Boss | Activity window (local) | Outcome |
|---|---|---|
| Magmadar | 19:27:45 – 19:40:47 | **KILL** (log 1) |
| Lucifron | 19:41:28 – 19:45:41 | **KILL** (log 1) |
| Gehennas | 19:52:51 – 19:57:30 ‖ 19:58:30 – 20:02:55 | **KILL — pull SPLIT by the crash** |
| Garr | 20:05:36 – 20:41:14 (window incl. trash) | **KILL** (log 2) |
| Baron Geddon | 20:45:02 – 21:00:36 | attempts, **no kill in-log** |

🛑 **The Gehennas parse straddles the two files** — log 1 ends mid-fight at
19:57:30 (the crash), log 2 opens 60 s later with the fight still running. The
ingest must either stitch the two files (they are strictly ordered, no overlap) or
treat Gehennas as one encounter with a 60 s event gap — **not** as two encounters,
and not dropped for being "incomplete" in either half. Trash between bosses is in
the windows above; the ingest's own encounter segmentation decides pull boundaries.

Roster: ~24 players across both halves. Player deaths are in the logs
(`UNIT_DIED` on player GUIDs) — the per-player death data the API never exposed
(admissibility predicate 2 has been inert for want of exactly this).

## §3 — The Elric snapshots: T5 per-parse stats exist now

Six full stat-export blocks (addon `v2026-08-06c` format), ExportedAt (client
local): **19:46:28** (just after the Lucifron kill), **20:16:37** (Garr window),
**20:53:52 / 20:54:11 / 20:57:05** (during Geddon attempts), **21:04:29** (after
the log ends). Each block: full ratings **split by melee/ranged/spell** (hit, crit,
haste, expertise, ArmorPen), spell power per school, final crit percentages per
school, weapon damage/speed, mana regen raw, `GetSpellInfo` probes, full spellbook.

**This is the data `infer_coefficient` refuses without**
(`refused:no_per_parse_stats`, Phase 3 criteria 3-full and 4). It is one character,
six instants — not per-parse coverage of the cohort — but it is the first time a
parse and a same-minute stat snapshot exist for the same character, and the
melee-vs-spell crit split it carries is exactly what the crit-table anchor
comparison needs. Scope note for whoever ingests it: snapshots bracket the Geddon
attempts most densely (three within 4 minutes), so that fight is the natural first
pairing target.

## §4 — The inspects: gear/talents for 18 raid members

20 `inspects.nie.one` links captured **18:21–18:35 UTC** (during the Magmadar
window), 18 unique characters — Frinto and Amfe twice each: Robottikyrpa, Imothep,
Frinto ×2, Shaka, Mizmo, Amfe ×2, Sakikotogawa, Blasted, Rakken, Luminira, Bal,
Redcoats, Melikepoopy, Missandae, Serathuli, Petslaver, Gothbaddie, Mapoot.
Several are frozen-cohort members. The links encode gear + talents in the URL
fragment (hex name/realm + item payload) — decodable offline, no fetch needed for
the parts already inventoried; full item-payload decoding is an ingest task, not
done here.

## §5 — What this capture unblocks (map, not a work order)

1. **`3k` Block C2 (ContentProfile measured durations):** real MC boss durations —
   note the tier-2 route (reports 116/117) gives per-encounter durations for the
   whole corpus too; this capture corroborates from the log side.
2. **T5 per-parse stats (§3):** unblocks the `infer_coefficient` refusal path for
   Elric's parses — criteria 3-full/4 machinery gets its first real input. Not in
   `3k`'s registered scope; a candidate for `3l`, named here so it is scheduled
   rather than discovered.
3. **Cohort gear freshness (§4):** 18 same-day inspect snapshots, several of
   cohort members, taken *inside* a raid — snapshot-lag zero for once.
4. **Death data (§2):** admissibility predicate 2 ("deaths > 0") has been inert
   because no source carried deaths. The owner's own logs do. Arming it for
   log-sourced parses is a stamp change → owner decision + prereg, not a drive-by.

## §6 — Cautions, so this capture is not mis-ingested

- **Timezone:** filenames and log lines are BST; the corpus is UTC. Shift before
  stamping, or every encounter lands an hour late — and the 19:17 local start
  would wrongly read as pre-boundary when it is 18:17Z, post-boundary.
- **Order of operations:** ingest only after the two-actives fix stamps Phase 2
  correctly; verify the capture resolves to Phase 2, not NULL, before trusting any
  derived number.
- **The split (§2):** Gehennas is one pull in two files.
- **No year in log timestamps** (3.3.5 format `8/7 19:17:13.091`) — the filename
  carries the date; the ingest must take it from there, not assume.
