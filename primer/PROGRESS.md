# PROGRESS

**Claude Code maintains this file. Update it at the end of every session, before writing the handoff.**

This is the pointer that lets a new session start with no memory of the last one. Keep it short —
detail belongs in `Session_*.md` handoffs, not here.

---

## Current position

### ▶ START WITH `0b`, NOT `0a`. This is deliberate — read why before doing anything else.

**`0b` (the crawler) is the first session, even though `0a` sorts first alphabetically.** The reason
is a hard external deadline, not preference:

- **Phase 2 launches 2026-08-08.** A phase transition permanently changes the gear distribution and
  the meta. Parse data from Phase 1 (Zul'Gurub) can only be collected *while Phase 1 is live* — it
  cannot be backfilled afterward. Every day the crawler isn't running before the 8th is data lost
  forever.
- `0a` is recon: fetching and reading. Valuable, but nothing breaks if it lands on the 10th.
- **So: `0b` first. Then `0a`.** They're independent and can even overlap, but if only one session
  happens before Aug 8, it must be `0b`.

Do not start `0a` first just because it appears above `0b` in the session-log table below. The table
is sorted by ID; **this pointer, not the table order, decides what's next.**

**Next session: `0b` — crawler + changelog fetcher (Phase 0 Task 6)**

Environment: **Windows**. Crawler is **manual-first** (no scheduler yet) — ship a double-clickable
launcher with a clear success/failure summary.

---

## Session log

| Session | Scope | Status | Handoff | Notes |
|---|---|---|---|---|
| **0b** | Crawler + changelog fetcher (T6) | ⬜ not started | — | 🚨 **DO FIRST — before Aug 8.** See Current Position |
| 0a | Recon T1–5, 7, 9 | ⬜ not started | — | After/alongside 0b. Fetching + reading, no deadline |
| 1a | Restructure, patches/realms/seasons, crosswalk | ⬜ | — | Gated on 0a Task 5 |
| 1b | `spell_mechanics` + relationship graph | ⬜ | — | |
| 1c | Facts, `spell_profile()`, auto-debugger, browsing, volatility | ⬜ | — | |
| 2a | Combat engine, content profiles, ability model, build spec | ⬜ | — | |
| 2b | Three sim tiers + uncertainty | ⬜ | — | |
| 2c | Weights, calibration, prediction ledger, cache, CLI | ⬜ | — | |
| 3a | Crawl normalisation, inference, search, gear | ⬜ | — | Gear scope gated on 0a Task 9 |
| 3b | Addon, logs, automation, crawler refinement | ⬜ | — | |
| 4 | Legos + Theorycrafter | ⬜ | — | Chunk as it goes |

Status values: ⬜ not started · 🟡 in progress · ✅ done · ⏸️ blocked

---

## Blocked on the user

Anything waiting on a 🛑 stop-point or a decision only the project owner can make. Clear entries as
they're answered.

| Item | Blocking | Asked on |
|---|---|---|
| `WoWCombatLog` file naming/location convention | 3b | — |
| Whether `ReloadUI()` is restricted on this server | 3b | — |

**Resolved:** crawler scheduling → **manual-first on Windows** (2026-08-04). No scheduler set up
initially; Windows Task Scheduler added later once the crawler is proven. `0b` is no longer blocked.

---

## Plan changes

When recon or implementation contradicts a phase doc, record it here **and** amend the doc itself.

| Date | What changed | Why |
|---|---|---|
| 2026-08-04 | Lego definition corrected: coupling-based, not "not a school" | A mostly-Frost cross-class cluster (Frost Mage ability + Frost Shaman feeder + Frost-damage talents) is a valid lego. Shared school is common evidence of coupling, not a disqualifier |
| 2026-08-04 | New `amplifies_school` relation type; graph is partly build-dependent | "Increases Frost damage" boosts unnamed abilities. Without a school-scoped edge that resolves against a build, school-amplifier legos are invisible to graph discovery. Enters at lower confidence per §5 |
| 2026-08-04 | ❌ **RETRACTED: "coefficients scale with rank"** and the `spell_scaling` re-key that depended on it | Derived by comparing `81193` to `270182` — two *different* abilities sharing the name "Holy Supernova" (radius 10 vs 15, cooldown 50 vs 40, instant vs 2s cast). Still plausible, now an open question |
| 2026-08-04 | ❌ **RETRACTED: "db.ascension.gg is a fifth ID space"** | `270182` resolves there normally. The db uses catalog-compatible IDs; `81193` is just another spell |
| 2026-08-04 | 🛑 **NEW HARD RULE: fingerprint before relating two IDs** | Same-name/different-ID was wrongly assumed to mean "related" **twice in one session** (`1111294` prefix, then `81193`). Compare radius/cooldown/cast/cost/effects first |
| 2026-08-04 | 🆕 In-game tooltips are **haste-adjusted** | Holy Supernova 2.00s base → 1.61s displayed ≈ 24% haste. A tooltip measures the character, not the spell — capture stats alongside every tooltip read |
| 2026-08-04 | ✅ **CONFIRMED: db.ascension.gg carries damage coefficients** on catalog-compatible IDs | `270182` → SP 24.15%, AP 15.70%, explicit Scaling fields, server-rendered. Best per-build source; rate-limited to ~2–3 automated requests |
| 2026-08-04 | ⚠ Contiguous rank rule downgraded to provisional | `270182`→`270187` is one pair; `270183`–`270186` unchecked. Must pass the fingerprint test |
| 2026-08-04 | ❌ **RETRACTED: "11 prefix / Wildcard variant" ID space.** No `wildcard_variant` crosswalk | Four in-game tooltips show plain IDs (1459, 10157, 136, 270187). `1111294` belongs to another realm, not Wildcard |
| 2026-08-04 | ✅ Catalog IDs = in-game IDs = db IDs, confirmed | 1459, 136, 270182 identical across all three. Task 4a class resolution stands |
| 2026-08-04 | 🚨 **Catalog stores Rank 1; owner plays max rank** | Arcane Intellect R1 = +2/+2, R5 = +31/+27 (~15×). Resolver must refuse rank fallback. `(spell_id, rank)` keying confirmed necessary |
| 2026-08-04 | 🆕 Fourth ID space: `CharacterAdvancement ID` (~40000) | Likely equals scouted `entry_id` (Shadow Bolt entry_id 40050 vs spellId 686). Would answer the v4 open question as "different spaces, never join" |
| 2026-08-04 | ⚠️ Ascension edits spells in place | Its Arcane Intellect grants spell power; retail's does not, same ID 1459. Class inherits from a WotLK ID; mechanics never do |
| 2026-08-04 | `db.ascension.gg` downgraded to "targeted manual lookups only" | robots.txt disallows automated access after ~2–3 requests |
| 2026-08-04 | New Phase 0 Task 4a — `SkillLineAbility.dbc` | 1,224/3,061 catalog entries (40%) are real WotLK IDs → deterministic class resolution, vs 392 (13%) today |
| 2026-08-04 | Server phase corrected to Phase 1 (Zul'Gurub); Phase 2 on 2026-08-08 | BisBeard's page metadata said "Phase 0" and was stale |

---

## Open questions raised during planning

Seed these into `open_questions` (Phase 1 Task 6) rather than losing them here.

| Question | Blocks | How to settle |
|---|---|---|
| Do damage coefficients scale with rank? | `spell_scaling` schema | Read one ability's in-game tooltip at two confirmed ranks of the **same** line; compare SP/AP terms |
| Is scouted `entry_id` the CharacterAdvancement ID? | Crosswalk, all "who runs X" queries | Collect ~10 CA IDs in-game, check against committed scouted JSON |
| Can the client dump a CA↔spellId mapping? | Crosswalk (if above confirms) | Addon API, debug command, or export |
| Which ID space do combat logs use? | Canonical ID choice project-wide | Inspect `ascensionlogs.gg` per-ability damage payloads |
| Is the contiguous rank rule real? | Rank resolution for Ascension originals | Fingerprint `270183`–`270186` against `270182` |
| Holy Supernova AP term: catalog `0.159` vs db `15.70%` | Coefficient accuracy | Live tooltip read |
| Fel Infused Weapon school: db says Fire, docs say Shadowflame | Ability classification | Live tooltip read |
