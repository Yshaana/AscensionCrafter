# Session `3l` — 2026-08-08 — Block C landed, tuning by diagnosed mechanism, the owner's extract run

> **`HISTORICAL`** — the record of session `3l`, written at its close. A past
> session; **may contain claims that are false today, and that is correct.**
> Work order it ran: `primer/SESSION_3L_PRIMER.md` (now `SUPERSEDED`). Audit it
> implemented: `primer/AUDIT_3K_ADVERSARIAL.md`. Overnight autonomous session;
> the owner was present for the stop-point questions at start and for the
> guided `--with-dbc` run, then handed the session off.

**One line:** both carried Block C deliverables landed; the tuning pass found
and fixed four swing-layer mechanisms (weapon slots, a second slot
*convention*, the missing AP term, RV's weapon coupling) under two preregs
with every falsification scored and diagnosed; the owner's guided extract run
landed `SpellItemEnchantment.dbc` (18,035 rows) and closed half the
Consecrated Weapon question by a numeric field; the MC capture passed its
ingest gate. **The gate: `0 of 35 · 0 qualified` at every commit; slice
26.3% (n=23) → 30.4% (n=24); absent 59.9% → 58.8%.**

---

## §0 — Commit by commit, with the gate at each

Owner pre-landed `e820c82` (MC capture, AUDIT_3K, v7 monitoring primer,
FINDINGS manifest, census) before the session opened — pre-flight 0–2 arrived
done, verified here.

| commit | what | gate `within ±20% / qualified / slice` |
|---|---|---|
| `f156b78` | pre-flight: season_config fossils | not re-read (docs) |
| `1fdf6f4` | D2 prep: SpellItemEnchantment extractor + M54 | cannot move |
| `f553297` | D2: the owner's guided `--with-dbc` run committed | cannot move |
| `d088833` | C1: gear_tiers production caller + M55 | cannot move |
| `bbed0e4` | B0: per-key table in the instrument + M56 | cannot move |
| `f7b14af` | B0: committed baseline; PROGRESS 3.5→**4.08** | `0 / 0 / 26.3 (n=23)` |
| `5b1dd3d` | pre-C2 gate baseline from the current tree | `0 / 0 / 26.3 (n=23)` |
| `567a807` | **C2 prereg** (parent of `18b0d40`) | — |
| `18b0d40` | C2: corpus-measured durations | pair follows |
| `25370b5` | C2 pair 1/2 — **P1 confirmed to the digit** | `0 / 0 / 26.3 (n=23)` |
| `a97b849` | C2 pair 2/2 — **P2 falsified**, diagnosed (epsilon) | instrument only |
| `a9dbd16` | **B1 prereg** (parent of `3efba04`) | — |
| `3efba04` | B3: slots 15/16 + AP/14×speed + RV decoupling | pair follows |
| `29fbc1b` | B3 pair 1/2 | `0 / 0 / 33.5 (n=23)` |
| `5bf7d98` | B3 pair 2/2 — **P1/P2-count/P4 falsified, one cause** | instrument |
| `4f1ba39` | **B3b prereg addendum** (parent of `778c892`) | — |
| `778c892` | B3b: per-snapshot convention detector | pair follows |
| `238b9cb` | B3b pair 1/2 — **P4b falsified** (composition) | `0 / 0 / 30.4 (n=24)` |
| `35cb55d` | B3b pair 2/2 — P2b/P3b/**P5b exact** confirmed | instrument |
| `e6e46f2` | D2: enchant chain in the epistemics seed | cannot move |
| `81dead0` | D3 registered / D4 re-deferred by name | cannot move |
| `49b5fde` | close: aura-345 verdict seeded | cannot move |

Prereg parenthood: `git log --format='%h %p %s'` shows `567a807`→`18b0d40`,
`a9dbd16`→`3efba04`, `4f1ba39`→`778c892` — prediction first, run second, all
three pairs. No gate-capable commit lacks one.

**Invariant, opening → closing:** tuning set 35 (unchanged); within ±20%
**0 → 0**; qualified **0 → 0**; slice **26.3% (n=23) → 30.4% (n=24)**; absent
**59.9% → 58.8%**; producing median 0.2573 (n=107) → 0.3116 (n=118); phantom
53.8% → 52.8%. Every move has a scored prediction or a diagnosed
falsification behind it (§2–§3).

## §1 — Owner decisions at session start (the five stop-points)

1. **B5 trigger-delivery modelling: DEFERRED whole to `3m`** (default taken).
2. **Block C confirmed first** — landed first, no third carry.
3. **`--with-dbc`: YES, guided** — the owner asked for step-by-step
   hand-holding with proof checked from this side; done that way (§4).
4. **E3 predicate 2 (deaths > 0): stays UNARMED by name.** No stamp change.
5. Holdout: unspent by default; see §8 (not spent — 0 passers).

## §2 — Block C, finally landed (was carried twice)

**C1** (`d088833`): `cli/gear_tiers.py` — the first production caller for
`gear_tier_stats`. The live Molten Core window (open since 18:00Z with zero
corpus snapshots) **refuses by name** — `phase window empty: 0 snapshots` —
with the excluded-by-reason breakdown (271 ZG + 8 Phase 0 measured on the
real corpus), exit 2; thin samples refuse distinctly; Phase 1 reports real
tiers (fresh 880 / mid 987 / bis 1255 budget over 271 snapshots). M55 run
red (2 FAIL), registered.

**C2** (`567a807`→`18b0d40`→pairs): the three gate-feeding presets carry
**corpus-measured durations** — raid 75.0→**78.1 s** (median, n=33
scope-joined), dungeon 60.0→**39.9 s** (n=566) — provenance states the query,
corpus sha and IQR; the five presets with no corpus measurement keep their
`assumption:` strings. **P1 confirmed to the digit** (gate unmoved —
`fast_sim` is linear in duration end to end, stated in the prereg before the
run). **P2 falsified and diagnosed**: the instrument moved (producing n
107→106, median +0.0154) because `_keyed_zero_reason`'s `casts <= 0.001` is
an **absolute epsilon** — budget-tail dust rows (≤0.078% of cohort logged)
scale across it when duration scales. Consequence recorded: the producing
median is membership-sensitive at ~±0.02; nothing was hung on moves that
size afterwards.

## §3 — Block B: four mechanisms, two preregs, five falsifications — all diagnosed

**B2 diagnosis.** The `3k` P2 thread's hypothesis (stats-resolution gap →
`p_crit = 0`) is **dead**: Deyindra and Shana carry `p_crit > 0` on 5–6 of
their events with positive crit pools (2,216 / 5,144) and the card resolved
`confirmed`. The real mechanisms, measured:

1. **`WEAPON_SLOTS = {16,17}` while the corpus stores weapons at slot 15** —
   105 snapshots (13 of 41 cohort members) simmed **weaponless**; every
   double-2H character swung its slot-16 weapon as the only one (Blix simmed
   Destiny 120-169 and dropped The Light's Hope 206-311).
2. **`expected_swing` had no attack-power term** — swings mitigated the naked
   weapon roll (Ryno: sim 122/swing vs 1,382 logged/hit).
3. **`_add_swing_sources` early-returned at `mh <= 0` before the RV
   section** — weaponless-sim characters derived no Righteous Vengeance
   despite holding the card; and the RV pool summed ability events only,
   structurally excluding every white-swing crit.
4. (Found by the B3 pair) **the corpus mixes TWO slot conventions**: 27
   members server-numbered (15/16), 14 API-style (16/17) — anchored by 2H
   weapons in slot 17, impossible for a ranged slot (Titan's Grip off-hands).

**B3** (`3efba04`, under `a9dbd16`): slots 15/16 + AP/14×speed
(retail_hypothesis, warned) + RV decoupling with white-crit pool. Pair:
slice 26.3→**33.5**, and **P1/P2-count/P4 falsified with one diagnosed
cause** — the fix flipped which convention half was served; the 14 API
members lost their weapons. Not rescued: registered as **B3b**
(`4f1ba39`→`778c892`), a per-snapshot detector (slot-15 weapon present →
server mapping; else API). Post-B3b: **41 of 41 members sim a main hand**
(P1b exact), auto-producing characters 19→**27** (P2b), absent **58.8%**
(P3b), **zero** of the 27 server-side members' rows moved (P5b exact).
**P4b falsified**: slice 33.5→**30.4 (n=24)** — no member fell; the restored
members *joined the readable population below the median*. The C2 epsilon
lesson, measured a second time at the slice level: **a median over a
population whose membership your fix changes is not a fixed target.**

**Named refusals, unchanged by tuning** (nothing fitted to its own target):
Plague Swarm 276445 (5.96%, resolution complete, 146× gap = delivery,
deferred with B5); Elemental Blast 954892 (mechanism unpinned, named); seal
per-proc damage, imbue procs, school-variant/extra-attack auto mass — all
the `3m` delivery block.

## §4 — D2: the owner's guided extract run, and what it decoded

The extractor gained `SpellItemEnchantment.dbc` **with a pure parse core and
three client-less harness arms** (M54 red 2 — the `3b` owner-gated-path
lesson applied in advance). The owner ran `run_dbc_extract.bat` step-by-step
(game closed → double-click → DONE box), and the log was verified from this
side before anything was built: 18,035 rows, stock field_count 38, rebuild
OK 22 steps, exit 0; the 7.8% odd-type slots are all `0xFFFFFFFF` unset
sentinels (measured, then excluded from the smoke line).

**The chain decoded** (`e6e46f2`, `49b5fde`): enchants 23387–23395 =
Consecrated Weapon ranks 1–9 → hidden equip-spells 200819–200827 with
Ascension-custom auras [DUMMY, 345, 344]. **Rank 6's aura-345 value decodes
85+1 = +86 — exactly the 2e-measured "+86 raw Holy SP per weapon"** — two
independent routes to the point, so aura 345 is the per-weapon school-SP
grant and the owner's enchant is rank 6. Seeded as a confirmed fact. Aura
344 (the per-hit, speed-scaled parameter: R1 19 … R9 132) stays underived —
`3m`'s delivery block, with the owner's per-hit distributions as test data.

🆕 **Pre-flight finding, tree over docs: the standing 20424 refusal reason
was stale when written.** Seal of Command's damage spell has been in
`spell_dbc_raw` since `3b`'s observed-ids extract and decodes (35%
weapon-percent, Holy; effect type 31). Its real blocker is per-proc
**delivery**, not extraction — corrected in PROGRESS, in the sim's own seal
warning text, and in the two-refusal arithmetic (the hand-typed "3.5 points"
was wrong; the regenerated figure is **4.08**, `f7b14af`).

## §5 — Block E: the MC capture through the analyze-capture protocol

- **Stability:** bytes identical to the `e820c82` commit across 6+ hours;
  mtimes corroborate the crash story. **Windows:** half 1 = 581,232 lines /
  2,417 s; half 2 = 600,740 lines / 3,901 s; crash gap **59.8 s**. Counts
  match the committed README exactly.
- **Parses:** `parse_log.py` on both halves — 1,177,726 combat events,
  5,348 ALC build records; the incomplete-frame warnings sit exactly at the
  crash boundary. Summaries are gitignored derived artifacts.
- **E0 PASSED for the resolvable slice:** every probed instant up to the
  payload horizon resolves to **`Phase 2 - Molten Core / Onyxia`** — all
  four kills (Magmadar 18:40:47Z, Lucifron 18:45:41Z, Gehennas 19:02:55Z,
  Garr 19:41:14Z), the Geddon attempt start, and Elric stat blocks #1–#2.
  ⚠ **The payload horizon is 19:45:34Z** (the newest committed `/api/phases`
  capture), so stat blocks #3–#6 and the last ~18 min of log 2 refuse with
  the correct named reason — retired automatically by the next crawler run.
- **E1 VERIFIED from the bytes:** GUID `0xF130002FE3000994` under fire at
  half 1's final line (19:57:30.470 local), ticking at half 2's first second
  (19:58:30.447), **one** `UNIT_DIED` at 20:02:55.246. One pull, never two
  encounters. Named limitation: `parse_log.py` produces whole-log summaries
  (no encounter segmentation), so it cannot mis-split — any future
  per-encounter ingest of this capture must stitch on the shared GUID.
- **E2 NOT RUN** (§8). **E3 unarmed** (owner decision). **E4:** reports
  116/117 pending tier-2 pickup — noted, not chased.

## §6 — Mutations registered and run this session

| id | site | red |
|---|---|---:|
| M54 | `parse_enchant_record` amounts_min read unsigned | 2 |
| M55 | `cli/gear_tiers.py run()` both REFUSED arms deleted | 2 |
| M56 | `per_key_table` per-group share denominator | 1 |

All three run red, reverted green, registered in `ENGINE_BUGS.md`'s table.
The `[3j-C3]` band-table assertion fired once mid-session (the B3 pair
commit lacked the re-render) and was satisfied by regeneration — the arm
did its job.

## §7 — Harnesses at close

Cited from the close-out runs on the final tree: `check_refusals.py`
**exit 0** (74 arms incl. 10 new `3l` arms), `check_sim_engine.py` **exit 0**
(registered XFAILs unchanged), `check_core_purity.py` **exit 0** (0
violations). Final gate manifest regenerated from a clean tree at the
close-out commit, per the established pattern.

## §8 — NOT done, explicitly

1. **E2 — `infer_coefficient` on the Elric stat blocks: prepared, not run.**
   E0/E1 verified, the blocks located and two of six phase-resolvable — but
   the dense Geddon trio (the natural pairing target) sits **beyond the
   19:45:34Z payload horizon**, and a fresh payload arrives with the next
   crawler logon anyway. First item of `3m`, with its own prereg, on a
   horizon that covers all six blocks. Nothing was derived from the capture
   beyond the gate verifications above.
2. **The holdout stays unspent** — recommendation recorded: at 0 passers on
   the tuning set there is nothing for it to validate; spending the one-shot
   read now would buy no decision.
3. **Elemental Blast's mechanism** — named refusal, unpinned (candidates:
   multi-school delivery, CD-modifier cards).
4. **Devour Mind (287865)** — deferred by name again; no coverage block was
   registered this session.
5. **The whole delivery family** (B5) — deferred to `3m` by owner decision:
   seal per-proc, imbue/Consecrated per-hit (aura 344), Plague Swarm,
   school-variant autos, Deep Wounds/Ignite/diseases.
6. **Slot-17-only and stray-slot weapon rows** (36 + 8 corpus-wide) — the
   detector maps neither; named in `compute_stats`' warning, not silently
   swung.

## §9 — What `3l` hands to `3m`

1. **Delivery modelling is the registered load-bearing problem** — the
   absent mass (58.8%) is dominated by trigger-delivered damage, and the
   producing tail's biggest gaps (Plague Swarm 146×, seals, imbues) are the
   same family. Aura 344's formula now has numeric per-rank values and the
   owner's own per-hit distributions to test against.
2. **The P4b lesson, twice measured:** medians over fix-shifted memberships
   (producing median, the slice itself) are not fixed targets — pre-register
   bands wide enough for composition, or predict per-member.
3. **E2 with a full horizon**: six stat blocks, the Geddon trio densest;
   `infer_coefficient`'s `refused:no_per_parse_stats` path is one prereg
   away from its first real input.
4. **The corpus slot-convention split** (27 server / 14 API in the cohort)
   is detected per snapshot at sim time; whether the crawler should
   normalise slots at ingest is `3m`'s call — a corpus-side fix would need
   its own migration discipline.
5. Gate at close: **0 of 35 · 0 qualified · slice 30.4% (n=24) · absent
   58.8%** — coverage and accuracy quoted together, per the standing rule.

---

## 🆕 APPENDED `3m` pre-flight, 2026-08-08 — one correction to §8 item 6

**The record above is unchanged; this is an append.** `AUDIT_3L` F10 checked §8's
sentence against the code and it is wrong in one half.

§8 item 6 reads: *"Slot-17-only and stray-slot weapon rows (36 + 8 corpus-wide) —
the detector maps neither; named in `compute_stats`' warning, not silently
swung."*

**What the detector actually does** (`calibrate_crawled.py:394-400`): slot-15
weapon present → `{15: main_hand, 16: off_hand}`, else → `{16: main_hand,
17: off_hand}`. A snapshot whose only weapon sits at slot **17** therefore takes
the API branch, and **slot 17 is mapped — to `off_hand` — with no warning**. The
36 slot-17-only rows are mapped, not skipped. Only the 8 stray-slot rows are
genuinely unmapped.

**Why "not silently swung" held anyway, and why that is not a defence.**
`swing_events` returns `(0, 0)` when there is no main hand, so nothing swung. That
is an accident of a different function's guard, not something the detector
enforces. Meanwhile the promoted row **does** reach `wielding()`, which reports
`'2h'` and switches on path clauses — Strength `physical_ability ×1.10`, Agility
`ability_crit_damage +0.20`, Duality `all_damage ×1.06`, Intelligence
`spell_haste +12`. And the stray-row check keys on the mapped slot **name**
(`g.slot not in ("main_hand", "off_hand")`), so a promoted slot-17 row escapes the
very check that was supposed to name it.

**Blast radius at the time of writing: none for the gate.** No member of the
frozen 41 is slot-17-only or {15,17}; the sentence was latent, not acting. `3m`
keys the stray check on the slot **index** rather than the mapped name (C6), so
the escape is closed rather than left to cohort luck.
