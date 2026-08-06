# Session 2026-08-06 — 3b pre-flight (BEFORE_3B checklist)

Ran the owner's `BEFORE_3B.md` pre-flight: §2 green preconditions, §1 audit
remediations, §0.3 (the derived buff layer + calibration-gate re-run). This is
carryover and hygiene, **not 3b scope** — 3b proper has not started. §4
(patch-notes → DB freshness) was deliberately not touched: it is its own
workstream, owner-approved in principle only.

---

## §2 — green preconditions

- `py cli/rebuild.py` green, 20 steps. `check_core_purity` 0/46 (46 files —
  one new module this session). `check_sim_engine` all pass (now including 3
  new buff-layer checks, below).
- No `--with-dbc` has happened since 3a (last extract commit is 2c's), so the
  extract-staleness precondition does not apply. The audit's "no
  `_extracted_at` stamp" flags are the known pre-2e-T4 condition, not drift.
- Incidental: the scheduled daily crawler fired mid-session (07:46 local),
  committed the 2026-08-06 tier-1 capture, and swept the two backfilled
  `tier2_manifest.json` files into its commit — same content this session
  intended to commit, so it was left as-is.

## §1 — 3a audit remediations

1. **Reproducibility framing fixed everywhere** (§1.1a). `builds.db`'s
   headline figures (4,069 characters / 307,442 ability / 877,850 avoidance
   rows) were described as "rebuilt from committed NDJSON"; they are not — a
   clean rebuild from committed source yields **390 characters and 0
   ability/avoidance/performance rows**, because tier-2 is gitignored by
   design. Reworded in PROGRESS, the 3a session record (correction block, not
   a silent rewrite), INDEX_GUIDE (v17), and PHASE_3_builds_repo.
2. **Per-report reproducibility manifest built** (§1.1b) —
   `tools/scrapers/build_tier2_manifest.py`, called by every crawler run and
   run standalone to backfill 2026-08-04 and 2026-08-05. One committed
   `tier2_manifest.json` per crawl day folder: per report id × tier-2 stem,
   NDJSON record counts, payload row counts, and an order-independent payload
   sha256. **Verified against the corpus: avoidance payload rows sum to
   exactly `ability_avoidance`'s 877,850** (abilities+healing merge into
   `ability_performance` via upsert plus pet rows, so that count is post-merge
   by design). Row counts are the durable audit for a re-fetch; the checksum
   is exact only for the original capture.
3. **INDEX_GUIDE items counts corrected** (§1.2): v16 shipped pre-backfill
   1,680 / 1,313; actual is **2,384 / 1,792**. Bumped to v17 with a changelog
   rather than silently edited; the PROGRESS plan-changes row was annotated in
   place (historical record kept, post-backfill figures added).
4. **The 3a lag-0 self-retraction is now a table row** (§1.3):
   `strict_lag0_join_skews_toward_levellers` in `seed_epistemics.py`
   (32 retraction rows). It had been recorded in four places of prose but not
   in the table CLAUDE.md names as the source of truth for retractions.

## §0.3 — the derived buff layer, and what it measured

**Built:**

- `core/builds/group_buffs.py` — derives a crawled candidate's buff set from
  the boards of participants in the **same capture scope**. On a classless
  server the group's *cards* (never classes) determine available buffs; a buff
  applies only when a participant's linked snapshot holds the granting card,
  by `card_spell_id` (never name — names verified as a cross-check instrument
  only, zero collisions). Explicit lower bound: unlinked boards and unmeasured
  buffs contribute nothing. Card resolution recorded in the module docstring;
  the one assumption worth naming is **Arcane Brilliance ← the Arcane
  Intellect card (1459)** — no card named "Arcane Brilliance" exists in the
  catalog or CharacterAdvancement, so the measured group buff is attributed to
  the only candidate source, flagged per derivation.
- `compute_stats` now **applies** `raid_buffs` in component mode (previously a
  "not modelled" warning): flat stats sum first, **Kings ×1.10 multiplies
  last** (measured order), path AP and stat→crit conversions read buffed
  primaries, buff raw SP is added **after** Duality's gear-scoped amp and
  **doubled under PoI** ("items and effects"), imbue stacks per equipped
  weapon. Sheet mode refuses buffs with a double-count warning.
- 3 new `check_sim_engine` checks pin the arithmetic (Kings-last, PoI buff-SP
  doubling, sheet-mode refusal).
- `calibrate_crawled.py` derives buffs per candidate and sims each character
  **both unbuffed and buffed**, so the layer's contribution is visible per row
  and nothing about it can be fitted.

**Measured — and the 3a hypothesis is largely falsified:**

- Gate result: **still 0 of 41 within ±20%** (strict lag-0, 120-candidate
  completeness pool). 40 of 41 deltas negative, −35% to −99%.
- The derived layer engages (3–5 buffs per candidate, from real group boards)
  but moves crawled sim DPS by **+0% to +11%** (largest: Xyz +10.6%, an
  SP/AP-scaled kit). The stat-side buff arithmetic cannot explain a −90%
  median miss.
- **Why the owner's ×2.35 misled:** his unbuffed→buffed 1,555→3,650 includes
  the imbue's unmodelled damage proc (200818 — 25.1% of his buffed damage) and
  buffed SP flowing through coefficients his kit's spells actually carry. A
  crawled kit's damage is mostly flats-without-coefficients (2e's
  missing-coefficient mechanism — out-of-catalog spells have no tooltip to
  carry one — generalised to every class in the crawl), so buffed stats have
  little to multiply. The buff-state gap routes through **per-ability
  magnitude coverage**, not stat arithmetic.
- New open questions: `crawled_gate_residual_after_buff_layer` (revised
  candidate ranking for the residual) and
  `sim_magnitude_explosion_absolute_zero` (Mutaforma sims 89,340 DPS,
  +3,619%, off an attributed Absolute Zero periodic — the gate's one positive
  delta is a resolution error, not a strong build).
- 🛑 Nothing was fitted. The layer was built from measured buffs and derived
  membership; its measured insufficiency **is** the finding, and Phase 3's
  exit stays honestly blocked pending the residual mechanisms.

## Still blocked on the owner (unchanged, plus 3b's two questions)

| Item | Blocking |
|---|---|
| Tracker #200295 re-test + PBL × LC discriminator (in game) | Build doc §2/§11 revert |
| Consecrated Holy Weapon (200818) live tooltip | 25.1% of buffed damage, unmodelled — and now implicated in the gate residual |
| `WoWCombatLog` naming/location convention (BEFORE_3B §3) | 3b log normalisation |
| Is `ReloadUI()` restricted on this server? (BEFORE_3B §3) | 3b addon/session automation |
