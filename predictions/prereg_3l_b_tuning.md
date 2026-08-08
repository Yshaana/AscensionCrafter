# Pre-registration — `3l` Block B: ratio tuning of PRODUCING abilities, by diagnosed mechanism

> **`FINDING 2026-08-08`** — committed BEFORE any fix it predicts.
> `git log --format='%H %p %s'` proves parenthood. True as of its date, not
> maintained.

## Mode

Ratio tuning of producing abilities (`SESSION_3L_PRIMER` B1), owner decisions
at session start: **trigger-delivery modelling deferred whole to `3m`** (B5
default taken); no coverage block registered (D1 stays deferred by name).

**Baselines, both committed post-C2:**
- `predictions/per_ability_summary.json` @ commit `a97b849` (git_sha
  `25370b56`): producing **n=106, median 0.2727**, absent **59.9% / 287
  rows**, phantom **156 keys / 53.7%**, starved 12.9%.
- `predictions/gate_manifest_3e.json` @ commit `25370b5` (git_sha
  `f7b14afb`): **0 of 35 within ±20% · 0 qualified · slice 26.3% (n=23)**.

## Targets, from the committed per-key table, ranked by producing logged mass

| # | key | share | chars | ratio | diagnosed mechanism (B2, this session) |
|---:|---|---:|---:|---:|---|
| 1 | `auto` | 7.638% | 19 | 0.0426 | THREE defects, measured: **(a)** `WEAPON_SLOTS = {16: main_hand, 17: off_hand}` while the corpus stores weapons at **slot 15** (210 rows; 105 snapshots slot-15-only → simmed WEAPONLESS; **13 of 41 cohort members**) — slot 15 is 3.3.5's `EQUIPMENT_SLOT_MAINHAND`, the mapping used the API-style numbering; **(b)** double-2H characters swing slot 16 as their ONLY weapon (Blix sims Destiny 120-169 and drops The Light's Hope 206-311); **(c)** `expected_swing` has **no attack-power term** — `base = (min+max)/2` (swings mitigate the naked weapon roll; retail 3.3.5 adds `AP/14 × speed`). Measured on Ryno: sim 122/swing vs logged 1,382/hit |
| 2 | 61840 Righteous Vengeance | 3.035% | 7 | 0.0298 | **(d)** `_add_swing_sources` returns at `mh <= 0` BEFORE the RV section, so a weaponless-sim character derives no RV despite holding the card and having a positive crit pool — Deyindra and Shana both: `p_crit > 0` on 5-6 of their events (the `3k` §7 stats-gap hypothesis is **dead**), pool 2,216 / 5,144, card resolved `confirmed` — the weapon-slot bug reaches them through the early return; **(e)** the RV pool sums per-event crit damage of ABILITIES only — auto rows carry no events, so RV structurally excludes white-swing crits and inherits the rotation's under-production |
| 3 | 276445 Plague Swarm | 5.955% | 1 | 0.0068 | **REFUSED this session**: resolution is complete (flat 112 confirmed + AP 0.0585/SP 0.09 scraped-verified, rank 6 correct) — the 146× gap is a DELIVERY question (a "swarm" DoT; single-application model cannot contain it). Deferred to `3m` under the B5 owner decision, named |
| 4 | 954892 Elemental Blast | 1.697% | 2 | 0.1243 | **REFUSED this session**: resolution complete (flat 621-731 confirmed + AP 0.325/SP 0.5 scraped-verified, rank 3; PoI doubling verified present in `compute_stats`). The 8× gap's mechanism is NOT pinned (candidates: multi-school delivery, CD-modifier cards). Named, not guessed |

Below these: the producing tail (≤1.5% each) — untouched this session except
where fixes (a)-(e) reach them incidentally.

## The registered fixes (B3) — mechanisms, never fitted ratios

1. **F1 — weapon slot mapping**: `{15: "main_hand", 16: "off_hand"}`; slot 17
   (3.3.5 `RANGED`) is **dropped from melee-hand mapping** — a bow must not
   swing as an off-hand. Slots 10-14 stray weapon rows (8 corpus-wide) stay
   unmapped, named in a warning. Provenance: the corpus's own slot×hand
   distribution + the 3.3.5 equipment-slot enum.
2. **F2 — the AP term**: `expected_swing` gains `+ AP/14 × weapon_speed`
   (`retail_hypothesis`, warned as such — same tier as the off-hand 50%
   penalty already in the function; Ascension's engine is 3.3.5-based per
   primer §1). Nothing is fitted: AP is the character's computed stat, 14 and
   speed are the retail formula.
3. **F3 — decouple RV/seals from the weapon**: restructure
   `_add_swing_sources` so the seal note and the RV derivation run when
   `mh <= 0` (autos alone are skipped); RV pool gains the autos' expected crit
   damage (computable from the white table's own crit component); the seal
   warning's stale claim ("20424 has no record in spell_dbc_raw" — false
   since `3b`, found in `3l` pre-flight) is corrected to name the real
   blocker (per-proc delivery, deferred).

## Predictions

- **P1**: cohort members simmed with a main hand: **28 → 41 of 41** (counted
  by presence of an `auto_mh` per-ability key).
- **P2**: characters with a producing `auto` key: **19 → ≥ 25**; the `auto`
  producing **median ratio rises 0.0426 → 0.12–0.45**. The residual below 1.0
  is the school-variant / extra-attack negative-id mass the sim deliberately
  does not model this session (delivery class, deferred) — quoted next to the
  result.
- **P3**: RV sim rows exist for **all 11 cohort holders** (9 today per `3k`;
  Deyindra + Shana join), **zero non-holders**, and RV's producing character
  count reads **9** (the two holders who log no RV become phantom rows —
  predicted, not accidental: phantom keys **156 → 156–162**).
- **P4**: absent share **59.9% → 57.5–60.0%** (the fixes add sim keys, they
  do not add log keys; movement comes only from previously-absent negative-id
  pairings, which the committed table says are already paired).
- **P5**: the gate pair, quoted together per the standing rule: slice at ≥20%
  coverage **26.3% → 28–42%**; within ±20% **0 → 0–3**; qualified **0 → 0–2**.
  Every delta moves UP (the sim only gains damage); any character moving DOWN
  falsifies the mechanism model.
- **P6**: the producing median's direction is **NOT predicted** — two named
  forces oppose (the auto group's ratios rise; RV/low-ratio members join the
  denominator), and C2's diagnosis showed the median is epsilon-sensitive to
  ±0.02 membership moves. Its value is reported, not scored.

**NOT predicted:** per-character deltas; the holdout (stays unread); Plague
Swarm / Elemental Blast / Devour Mind / seal per-proc damage / imbue procs
(all named above or deferred under B5); medium/slow tier outputs.

**Falsifiers:** P1 exact; P2/P3/P4/P5 by their stated bands; any delta moving
away from zero. A falsified prediction is reported un-rescued and diagnosed
before any further tuning commit.
