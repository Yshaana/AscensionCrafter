# CHAT MONITORING PRIMER v8 — AscensionCrafter

> **`LIVE`** — the standing brief for the oversight chat. **Must be true today, and is
> citable as current truth.** Supersede at **v9** when `3m` closes. *(The streak is
> three: v5, v6 and v7 each held their stated expiry. ⚠ **v7 expired for one morning**
> — it said "supersede at v8 when `3l` closes", `3l` closed overnight, and the file sat
> `LIVE`-and-false until this rewrite. Half a day, in one of only 13 `LIVE` documents.
> **The repo file `primer/CHAT_MONITORING_PRIMER.md` is versionless and updated in
> place; the version lives in the title line only. Never commit a `_v8` sibling** — a
> versioned copy beside the live file is how v2–v4 each stayed marked `LIVE` after
> expiring.)*

**Paste this at the start of a fresh monitoring chat.** Supersedes v1–v7. Written
2026-08-08 (morning), at the end of the session that audited `3l` — the audit is
`AUDIT_3L_ADVERSARIAL.md`, ⚠ **written in the oversight chat and not yet committed to
`primer/`** — committing it, with this file, is the first document action owed
(`3m` pre-flight).

This chat's job is **oversight and verification** — Claude Code writes the code
locally. If this chat writes the code, nobody is left to audit it.

---

## First action, every time

Clone and read the tree. Do not work from prose, this file included.

```bash
git clone --depth 40 https://github.com/Yshaana/AscensionCrafter.git repo
```

Then `primer/PROGRESS.md`'s top block. **If a claim isn't in the tree, it isn't
confirmed.** The owner may connect the local repo via `device_list_dir` /
`device_stage_files` / `device_commit_files` — file read/write, **no shell**. Use it
for documents only; never write code through it.

---

## What this project is (one paragraph)

A theorycrafting toolkit for **Project Ascension** — a classless WoW private server
(3.3.5 client, realm **Darkmoon**, Season 10). Five layers: a provenance-enforced
spell/mechanics database, a crawled + live-captured builds repo, a ported-SimC damage
simulator, a "lego box" of build components, and a theorycrafter. Built in phases by
Claude Code locally; the owner plays the game and is the tier-1 evidence source.

---

## Where things stand, 2026-08-08 morning (post-`3l`, post-audit)

**Session map:** … → `3j`✅ (integrity) → `3k`✅ (flip + coverage) → `3l`✅ (Block C
landed + tuning by diagnosed mechanism) → **`3m` (correctness repairs from `AUDIT_3L`
§5 items 1–4 FIRST, then DELIVERY MODELLING)** → re-read Phase 3 exit honestly →
Phase 4.

**The gate:** `0 of 35 within ±20% · 0 qualified` at every `3l` commit; slice
**30.4% (n=24)** published, **but see the caveat below**; absent **58.8%**; producing
median **0.3116 (n=118)**; phantom 52.8%. 3 of the frozen 41 not admissible (Nodding
52 s window, Boomcat 0.24, Deyindra 0.22). Holdout: still carried from `3g`, `0 of 5`,
median slice 9.8% (n=4), **pre-E15**, not like-for-like — never compute a gap from the
pair. Phase 3 exit: **2 of 7 criteria met**.

🛑 **THE SLICE MOVE IS COMPOSITION, NOT ACCURACY, AND THIS IS THE HEADLINE CORRECTION
OF THE AUDIT.** `3l` published 26.3% (n=23) → 30.4% (n=24). Held to the same 22 members
across all three runs the number goes **30.635 → 30.425 — a change of −0.21 pp**. The
+4.12 pp is the population moving under the statistic. Worse, the *middle* leg
(26.3 → 33.5, n=23 → n=23) is the most composition-driven of the three and is the one
nobody flagged: **Onur left the band** (coverage 47.7→7.3, slice 6.03, the band's
lowest) and **Deyindra joined** (10.9→42.1, slice 105.43) — and Deyindra is NOT
ADMISSIBLE. The equal `n` is what made it look safe. `3l` derived this exact lesson
(P4b) and applied it to the downward leg only. **In fairness the fixes did work** — on
the 22 common members 16 moved toward 100%, mean 45.74 → 50.58; the statistic just
doesn't show it. Quote **both** numbers, always.

**What `3l` did well, and it is most of the session:** Block C landed after two carries
(`cli/gear_tiers.py` refuses the live empty MC window by name, M55; the three
gate-feeding presets carry corpus-measured durations with the query, corpus sha and IQR
in the provenance string). Four real swing-layer mechanisms found and fixed — the corpus
stores weapons at **slot 15** (13 of 41 simmed weaponless), it **mixes two slot
conventions** (27 server / 14 API, found by a falsified prediction and fixed with a
per-snapshot detector; 41 of 41 now sim a main hand), `expected_swing` had **no attack
power term**, and the `mh<=0` early return killed Righteous Vengeance for weaponless
sims. The owner's guided `--with-dbc` run landed `SpellItemEnchantment.dbc` (18,035
rows) and decoded the Consecrated Weapon chain. The MC capture passed its ingest gate,
every figure exact from the bytes. **Five predictions falsified, all diagnosed, none
rescued.** Prereg parenthood exact on all three pairs. Harnesses green (77 arms).

**The five things the audit found wrong — `3m`'s first block:**

1. 🚨 **RV's rank is discarded.** `RIGHTEOUS_VENGEANCE_FRACTION = 0.30` flat, while the
   three card ids decode `EffectBasePoints` 9/19/29 → **10%/20%/30%**. A rank-1 holder
   is credited 3×. Direct hit on the standing rank rule.
2. 🚨 **RV's white-crit pool is unwarranted.** `3l` added white-swing crits to the pool;
   RV's own client text says *"**Direct** critical strikes with **spells and
   abilities**"*, and `core/builds/stats.py:234` asserts that wording **excludes**
   autos. Measured on the committed logs: widening the pool makes the prediction worse
   in **49 of 49** rows carrying white crit. Entered the gate with no warning line.
3. 🚨 **Aura 344 is flat ATTACK POWER, not the per-hit damage parameter.** Spell
   200809's own template: *"increasing Holy Spell power by `$200819s2` and your attack
   power by `$200819s3`"* — `s3` is effect 2 = aura 344. The per-hit speed-scaled term
   is effect **0**, rendered `$/77;m1 to $/25;M1`. `seed_confirmed.py:361` now
   contradicts `seed_confirmed.py:278` in the same file, and `3m`'s delivery block is
   scoped around a mechanic that does not exist. Rank 6 = **+73 raw AP per weapon**,
   unmodelled.
4. 🚨 **None of B3/B3b's four mechanisms carries a registered check.** `git log
   --name-only a97b849..642f531` touches no test file; `check_sim_engine.py` is
   untouched across the whole `3l` range. Reverting `WEAPON_SLOTS`, deleting the AP
   term or restoring `if mh <= 0: return` all leave the harness green. And the AP term
   made E13 **vacuous** — its fixture has no `attack_power`, so `getattr(..., 0.0)`
   runs the branch off; with realistic AP the check's own ceiling breaks.
5. ⚠ **C2's P1 is scored CONFIRMED and its falsifier says otherwise.** Six numbers
   moved on two characters (Frediib's producing-only slice **114.47 → 242.59**, and
   Frediib is a band member). The diagnosis (the `casts <= 0.001` absolute epsilon) is
   right; only the scoring is wrong — the same mechanism moved both artifacts and only
   the instrument was scored.

**Key documents, reading order:**

| File | What |
|---|---|
| `primer/PROGRESS.md` | live state — top block first; ⚠ its slice line needs the same-member pair appended |
| `AUDIT_3L_ADVERSARIAL.md` | current audit; §5 is `3m`'s list; ⚠ commit it to `primer/` |
| `primer/Session_2026-08-08_3l_tuning.md` | what `3l` did; §3 = the four mechanisms; §8 = honest not-done. ⚠ §7's "74 arms" is 77; ⚠ §5's "warnings sit exactly at the crash boundary" is false (1 of 11) |
| `predictions/gate_manifest_3e.json` | current numbers (`LIVE`, clean tree, `git_sha ab5ca92`, committed at `642f531`) |
| `predictions/per_ability_summary.json` | the distribution — ✅ **now carries the ranked per-key table** (`3l` B0 closed `AUDIT_3K` §3.2) |
| `predictions/prereg_3l_b_tuning.md` + `_addendum.md` | the tuning preregs — ⚠ note the **one-sided falsifier** ("every delta moves UP") |
| `predictions/CALIBRATION_TOLERANCE.md` | ⚠ `LIVE` **and stale in its derived prose** — the asserted band table was regenerated, the sentences around it were not (26.3%/3.8×/"one quarter"/the 3i A5 annotation) |
| `primer/ENGINE_BUGS.md` | defect registry — parser-enforced, M1..M56 contiguous |

---

## The open threads, in priority order

**0. 🚨 CORRECTNESS BEFORE COVERAGE.** `AUDIT_3L` §5 items 1–4 are three-line fixes plus
four mutations, and two of them change a gate number. **RV rank + RV pool retraction is
the first change of the arc that moves a number DOWN** — which is why the tuning
prereg's *"every delta moves UP; any character moving DOWN falsifies the mechanism
model"* clause must be rewritten before `3m` registers anything.

**1. DELIVERY MODELLING is `3m`'s registered core**, and `3l` sharpened it. Absent mass
58.8% is dominated by trigger-delivered damage. With the aura-344 correction the block
is: seal per-proc (20424 — 35% weapon, Holy, **delivery**-blocked not
extraction-blocked, corrected `3l`), imbue per-hit (effect **0**, divisors 77/25,
*stated by the client*), Plague Swarm 276445 (5.96%, resolution complete, **146× gap**),
school-variant/extra-attack autos, Deep Wounds/Ignite/diseases.

**2. E2 — `infer_coefficient` on the six Elric MC stat blocks**, `3l`'s named handoff.
Two of six were phase-resolvable at the 19:45:34Z payload horizon; the next crawler run
retires that. 🛑 **Before running it, fix the windowing**: Gehennas has **two GUIDs**
(a wipe at 19:52:51–19:54:56 and the kill pull), Garr has **four**, Geddon three. `3l`'s
"one pull, never two encounters" is true of the GUID it checked and **invites a 604 s
merged window** if read as an encounter-level claim. Window on GUID, pick the kill GUID
explicitly.

**3. Instrument hygiene, all one-liners:** `not_scoreable_below_coverage_floor` counts
3 NOT-ADMISSIBLE characters including the cohort's **highest-coverage** member (Boomcat,
82.2%) — the JSON contradicts the console the same function prints; four check arms are
satisfiable without the behaviour (`[3k-B3]` arm 4 is a pure source-text match — the
M52/M53 shape, again); `check_refusals.py` should print its own arm count; the stray
weapon-slot check keys on the mapped **name**, so a slot-17-only snapshot silently
becomes an off-hand.

**4. Small carried threads:** Devour Mind 287865 (6.63%, largest single absent key —
**third deferral**, register or explain); Elemental Blast 954892 (mechanism unpinned);
`WEAPON_SLOTS` now exists in three conventions across three tools; the AP term's
`retail_hypothesis` warning cannot reach the gate artifacts (`[:8]` truncation, no
warnings field in the manifest, no `ENGINE_BANDS` entry).

**5. Document actions owed at `3m` pre-flight:** `AUDIT_3L_ADVERSARIAL.md` → `primer/`
(born `FINDING`); THIS file committed in place as v8; census regenerated in each commit
that adds a `primer/` file; `CALIBRATION_TOLERANCE.md`'s derived prose regenerated.

**6. Standing:** the holdout stays unspent (0 passers — nothing to validate, correct
call); one owner-gated `--with-dbc` run remains the staleness clock; predicate 2
(deaths > 0) stays UNARMED by owner decision.

---

## Corrections worth carrying — do not let these creep back

- ❌ **"slice 26.3% → 30.4% is a 4-point accuracy gain"** — it is **−0.21 pp** held to
  the same 22 members. Quote the pair.
- ❌ **"equal n means the population didn't change"** — the 26.3 → 33.5 leg has n=23 on
  both sides and swapped its lowest member for a near-top one. **`n` is not a
  membership check.**
- ❌ **"aura 344 is the per-hit speed-scaled damage parameter"** — it is flat attack
  power (+73/weapon at rank 6). The per-hit term is effect 0.
- ❌ **"Righteous Vengeance is 30%"** — 10/20/30 by rank, and the code applies 30 to all
  three.
- ❌ **"RV pools white-swing crits"** — unwarranted; 49/49 worse against the committed
  logs.
- ❌ **"0 of 36"** — the denominator is **35** since `3k`.
- ❌ **"two active top-level phases = a transition in progress"** — transitions are
  ADDITIVE; the current phase is the latest-**starting** active top-level. Ambiguity now
  means same-`start_date` windows.
- ❌ **"coverage gains are progress toward the gate"** — `3k` P4, falsified by
  measurement; `3l` re-confirmed it (absent 59.9→58.8 with no real slice move).
- ❌ **"the absent-key targets can't be read from a committed artifact"** — ✅ **retired**,
  `3l` B0 landed the per-key table. The two-refusal mass is **4.08**, verified exact.
- Still true and load-bearing: the gate fails CLOSED; `entry_id` ≠ `spells.id`; the
  catalog's wrong-rank problem (**and it now applies to our own constants — see RV**);
  "coverage = has a key for, not produces damage for"; the holdout is pre-E15 and not
  comparable; a single multiplier cannot fix the sim; no coefficient fitted to the parse
  it must later check.

---

## How to review a session (the loop that works)

1. Clone fresh. `PROGRESS.md`, the session's handoff, the work order it ran.
2. **Spot-check claims against committed files, not prose.**
3. **Run the harnesses** (`check_refusals.py` — 77 arms post-`3l`; `check_sim_engine.py`
   exit 2 on a clone is a verdict, not a crash; `check_core_purity.py`).
4. **Check `LIVE` documents against code, both directions, and against post-close
   commits.** 🆕 And check a `LIVE` document's **own expiry condition** — v7 sat expired
   for a morning, and `CALIBRATION_TOLERANCE.md`'s asserted table was regenerated while
   every sentence deriving from it was not. **An assertion protects the block it covers
   and advertises safety over the paragraphs it doesn't.**
5. **Trace headline numbers from the schema up.** 🆕 **And recompute the headline
   statistic over a FIXED membership.** Reconstructing every published band median from
   the manifest's own `cohort` array takes ten minutes, validates the method before you
   use it, and is what turned `3l`'s +4.12 pp into −0.21 pp.
6. Confirm 🛑 stop-points were asked; **check prereg PARENTHOOD** (`git log --format='%H
   %p %s'`).
7. **Ask of every check: does it have a regime where it returns a number it cannot
   support?** And: can the fixture even express the defect? 🆕 **Then ask the inverse:
   which of this session's changes has NO check at all?** `git log --name-only <range>`
   and look for a test file. `3l`'s four headline mechanisms touched none.
8. **Ask: measured or derived? committed or gitignored? does a quoted baseline exist as
   a committed artifact?**
9. **Re-run the claimed reverts yourself — all of them if the count is small.** `3l`'s
   M54/M55/M56 reproduced 2/2/1 exactly. 🆕 **Then mutate the checks the session did
   NOT register** — that is where the four soft arms were found.
10. **Re-derive a hard-rule-adjacent constant from the committed extract when cheap.**
    🆕 Highest-yield check of this audit: `EffectBasePoints` for the three RV card ids
    (nine lines of Python) exposed a 3× error, and reading spell 200809's own `$sN`
    pointers exposed a mis-seeded aura. **When a session seeds a fact from one extract,
    read the sibling fields in the same rows** — the disconfirming evidence is usually
    two columns over.
11. **A named mutation that does NOT go red is a result, not an embarrassment** — and a
    falsified prediction diagnosed to its true cause is worth more than a confirmed one.

**Tone:** falsifiable checking, not cheerleading. `3l` falsified five of its own
predictions, rescued none, and put its sharpest lesson at the top of `PROGRESS.md` — say
so first. The pattern to hold it to is narrower than "be careful": **it reasoned
excellently about the numbers it was watching and left the numbers it was not watching
unguarded.** In every finding above, the missing half was already in hand.

---

## Standing owner actions (not session tasks)

- **Daily:** crawler at logon (Task Scheduler). ⚠ If it dies at `assert_phase` ("PHASE
  FLIP DETECTED"), that is a NEW boundary — save the message verbatim. A silent
  label-refusal pile-up would now mean same-`start_date` windows — also report.
  🆕 The next run also retires the `19:45:34Z` payload horizon that blocks four of the
  six MC stat blocks, which is E2's precondition.
- **Occasional, overnight, manual:** `catchup_crawler.bat`.
- **Per client patch:** `run_dbc_extract.bat`. Last *successful* run is the clock —
  currently `2026-08-08T00:48:58`, with `SpellItemEnchantment.dbc` in scope.
- **Stat-export addon** — byte-identical at `v2026-08-06c` (its T5 per-parse stats still
  gate Phase 3 criteria 3-full and 4; the MC capture is their first real input).

## Reproducibility limit (standing)

Tier-2 captures gitignored; no `.db` committed. Corpus figures (472 snapshots, the RV
roster, per-character ratios, the 27/14 convention split) are unverifiable from a clone —
verify function behaviour with fixtures, manifest-internal arithmetic, commit parenthood,
and source-edit mutation re-runs instead. 🆕 **The committed DBC extract and the
committed capture bytes are the strongest ground the oversight chat has, and `3l`'s two
worst findings both came from there** — prefer them over manifest arithmetic when a
claim can be reached either way.
