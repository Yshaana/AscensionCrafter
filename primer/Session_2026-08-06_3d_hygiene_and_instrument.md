# Session `3d` — hygiene + instrument (2026-08-06)

**Work order:** `primer/SESSION_3D_PRIMER.md`. **Findings it rests on:**
`primer/AUDIT_3C_ADVERSARIAL.md`. **Scope fence:** no modelling changes; new
fixture failures are recorded, not fixed (those are `3e`).

**Six commits, one per block:** `342b493` A · `47bd374` B · `2d3db19` C ·
`788a771` D · `a77875e` E · `69f2192` F.

---

## §0 — the invariant, opening and closing

`py tools/audit/calibrate_crawled.py --limit 120 --max-lag-hours 0`

**Opening**, before any edit, at `main` = `edfcc61`:

```
[candidates] 120 distinct level-60 characters pass the completeness filter (max build staleness 0h)
[gate] 5 of 41 simmed characters within ±20%  (criterion: ≥3)  -> PASS
[gate] of those, 2 also have ≥50% of their real damage modelled (rider: ≥3) -> NOT MET
[exit] PHASE 3 EXIT: NOT MET — needs both.
```

**Closing**, at `69f2192`:

```
[candidates] 120 distinct level-60 characters pass the completeness filter (max build staleness 0h)
[gate] 5 of 41 simmed characters within ±20%  (criterion: ≥3)  -> PASS
[gate] of those, 2 also have ≥50% of their real damage modelled (rider: ≥3) -> NOT MET
[slice] cohort median slice accuracy 160%          <- new, F3, instrumentation only
[exit] PHASE 3 EXIT: NOT MET — needs both.
```

✅ **5 of 41, 2 qualified, both runs.** The only added line is F3's slice
accuracy, which no verdict reads.

---

## 🚨 The finding that matters most: THE GATE'S COHORT MOVES ON ITS OWN

This was not on the work order. It surfaced while testing E1 and it changes how
every gate number in this project should be read.

**Rebuilding `builds.db` moved the gate from 5 of 41 to 4 of 38 with ZERO code
changes.** Isolated by restoring the previous corpus: the gate read 5 of 41
again, so nothing in Blocks A–F touched it.

**Cause.** `calibrate_crawled.candidates()` is `ORDER BY character_id LIMIT 120`.
The scheduled daily crawler fired mid-session and the qualifying population grew
from **157 to 180** characters. The limit was written as a *cost cap*; what it
actually is, is a **sliding window keyed on an arbitrary id**. Four characters
left the cohort and four entered, for no reason but their id.

**Consequences.**

* Two gate results from different days are **not comparable even with identical
  code**.
* The "41" is an artifact of where a 120-cap landed on one particular day.
* Any holdout must be pinned **by id**, not by re-running a limit — which is why
  F5 is.

🛑 **NOT FIXED HERE.** Changing a gate's population is not a hygiene edit, and
`3d` ships no modelling change. It is `3e` work, recorded in
`CALIBRATION_TOLERANCE.md` and in `predictions/gate_manifest.json`, which now
records the cohort by character id on every run so the comparison is at least
checkable.

---

## What each block delivered

### A — crawler hardening *(own commit; the 2026-08-08 deadline)*

* **A1.** `season_config.py` is the one place realm/season/phase live. They were
  hardcoded in **five** files (the audit named four; `ingest_changelog.py:52` is
  the fifth) with nothing checking any of them. Values unchanged.
  `assert_realm()` checks the constant against the host; `assert_phase()` checks
  the live active **top-level** phase and raises, turning the Phase 2 flip into a
  refusal instead of a silently mis-stamped day. **The season is NOT checkable —
  no endpoint states one — and the module says so rather than pretending.**
* **A2.** The unattended auto-commit is scoped to the two paths the crawler
  writes. Verified: a dirty file under `data/source/captures` is staged by the
  old unscoped `git add data/source` and ignored by the new one.
* **A3.** Row-count canary against the previous day's manifest, checked **before**
  the commit. Scoped to `phases` and `leaderboards` deliberately — the other six
  writers legitimately hit zero (new-reports-driven, or content-hash deduped), and
  an alarm that cries wolf daily is worse than none. Rates are per-run, so a
  one-run day does not read as a collapse against a three-run day.
* **A4.** The changelog exit code is propagated and aborts the day.

### B — naming and doc truth

* **B1/B2.** `PLAN_3C` renumbered to `C1…C13` (87 replacements). All eight
  numbers collided with `PHASE_3`, with `PHASE_2` a third space, and the handoff
  collided **with itself** on three tokens 135 lines apart. `grep -n "\bT[0-9]"`
  on `PLAN_3C` returns nothing — including in prose that merely quotes the old
  names, which is why its naming header explains the collision without using them.
* **B3.** The exit-criteria record: **seven** criteria, **three** outstanding,
  and **#7 FAILED, not unverified**. Now a per-criterion table with file:line
  evidence; the "flag it as unverified" sentence is struck through and retracted
  rather than deleted.
* **B4.** `ARCHITECTURE` §4 re-synced against `find . -type d` — eight
  load-bearing directories were undocumented. Also records that §2.4 is inverted
  in practice.
* **B5.** `api/` is a docstring with zero functions, imported by nothing, while
  **5 of 7** CLIs import `core/` directly. Three docs claimed otherwise; all three
  now say the boundary is aspirational. Chose amending over adding a token
  function — routing a CLI through a new layer is a behaviour change.
* **B6.** 21 steps, not 20.

### C — the three rule violations

* **C1.** `spell_scaling` had **no provenance columns at all**, and
  `source TEXT DEFAULT 'export_tooltip'` was nullable *with a default*, so an
  omitting writer **fabricated** tier-6 provenance. Five NOT NULL columns added
  and backfilled by stating each of six writers' real evidence — 4,815 rows, 0
  missing. `verified_at_patch` stays nullable, mirroring the precedent the audit
  itself cites as compliant.
  ⚠ Two `source_tier` calls worth knowing: the DBC coefficient routes are
  `dbc_description_text`, **not** the tier-4 `dbc_numeric_field` — they are regex
  extractions from description strings, and labelling them tier 4 would borrow a
  numeric field's authority for a tooltip template.
* **C2.** An unranked `source` did not fail — it ranked *below* `export_tooltip`,
  and two unranked sources **tie**, both survive, and are summed. That is the
  Mongoose Bite double-count, reachable again. Now a build-time hard failure.
  Same-source duplicates are recorded as conflicts instead of silently destroyed.
* **C3.** The operator-facing conflict count was wrong. It printed **30**; the
  true figure is **170**, of which **142** are coefficient conflicts (266 distinct
  triples) that never reached `conflicts_json` at all. Both kinds now counted and
  named. Deliberately does **not** mark those rows `confidence='conflict'` — an
  owner-approved precedence has decided them, and claiming otherwise would be
  false and would fire warnings on 142 correct spells. Precedence untouched.
* **C4.** The Holy Shock circularity guard was **documented and never
  implemented**. Now implemented **by source**, not by spell id — hardcoding
  25902 goes stale the moment a second back-solved value is seeded. Fires on all
  13 logs. It also surfaces the independent alternative (scraped SP 0.2145 vs the
  back-solved 0.40) but does **not** substitute it — see the owner question below.

### D — two non-paladin fixtures ⭐

Built from **real crawled boards**, chosen on mechanics: `build_crawled_cp_melee`
(snapshot 462) and `build_crawled_dot_caster` (snapshot 218). Their stats are
**gear-only** and each fixture's provenance says so — they exercise code paths,
and their absolute output means nothing.

**Six defects found, none fixed**, written up in `primer/ENGINE_BUGS.md`:

| | defect |
|---|---|
| E1 | `combo_points` incremented nowhere — **and worse**: `apl_gen` classified none of the board's four per-combo abilities as finishers, so zero entries are CP-gated and the predicted bug is currently *masked* |
| E2 | `target_health_pct` pinned at 100. The sim cast an execute-gated ability **9×** as if always available, over-crediting it, with no warning |
| E3 | no pet model, while `corpus.py:614` includes pet damage in the dps being calibrated against |
| E4 | the APL grammar has no target-debuff/DoT-uptime condition at all |
| E5 | 🚨 **not predicted by anyone** — 6 of 7 DoTs on a DoT-caster board are cast **zero** times; a cooldown-less DoT is filed behind every cooldown ability and the GCD budget never reaches it |
| E6 | `fast_sim`'s first filler eats the whole GCD budget — listed, not registered, because the current check does not bite. It is the tier the gate runs on |

**Two of my own checks passed vacuously mid-block** (a broken `is_periodic`
comparison, and treating "a finisher cast" as evidence the CP economy works) and
were rewritten. Finding fail-open checks *inside the block written to fix
fail-open checks* is the whole argument for the fixtures.

The `EXPECTED_FAILURES` registry is enforced **both ways** so it cannot rot:
registered+failing is XFAIL and green; registered+**passing** is a hard failure
telling you to close the entry; unregistered+failing is a regression; a registry
entry naming a check that no longer runs also fails. All four unit-tested.

### E — reproducibility

* **E1.** `build_builds_db.py` added to `rebuild.py` but **opt-in** via
  `--with-corpus`. A deliberate deviation, for the finding above: an
  unconditional step would mean every routine rebuild silently redefines the
  gate's population.
* **E2.** `predictions/gate_manifest.json`, committed, emitted per run. Counts,
  ids and hashes only. Records the cohort **by character id** with each member's
  delta, coverage and slice accuracy, plus the cohort-instability warning in the
  file itself.
* **E3.** A killed rebuild now leaves a database that **refuses to be read**
  rather than one that lies. Verified in all four states. Two ordering details
  that are easy to get wrong: the marker is written *after* step 1 (which unlinks
  the db), and the rebuild signals itself with an env var rather than making
  fifteen call sites pass a flag.

### F — the instrument

* **F1.** `EXCLUDED_SNAPSHOT_SOURCES`, applied **in the SQL before the LIMIT** —
  a filtered row that was still SELECTed would consume a window slot and displace
  a real character. `tools/audit/check_gate_exclusion.py` proves it by cloning a
  real cohort member (so only the source can reject it) at `character_id 1` (so a
  post-hoc filter would displace someone), and checks the converse: without the
  filter the same character *does* enter.
  ⚠ **Elric's snapshot itself is not created** — it needs a log→`builds.db`
  writer, which is PHASE_3 T6 and belongs to `3f`. The guard, which carries the
  risk, ships today so `3f` can add the snapshot safely.
* **F2.** `calibrate_vs_log` refuses without a stat block. Defaults **deleted,
  not corrected**. `--weapon-speed` added (was hardcoded); `--haste`,
  `--spell-crit`, `--ranged-ap` accepted as **named gaps**.
* **F2b.** The audit was right to flag the contaminated targets and **wrong about
  the size**: HftH÷HoJ `1.718 → 1.704` (−0.83%), Dawnreaver÷Whirling Light
  `0.769 → 0.769` (0.00%). Both stand. The stat block is now stated inline with
  the reproducing command. General lesson: a weapon-free pair chosen so a wrong
  *weapon* input cancels turns out to be nearly immune to a wrong *AP/SP* input
  too.
* **F3.** Slice accuracy, per character and cohort median (**160%**).
* **F4.** A dated successor criterion, recorded before the work it judges, taking
  effect at the **next** gate. The 50% rider is untouched. **80% is a diagnostic
  landmark, not a bar**, and the entry says why in four ways.
* **F5.** A five-character holdout, chosen by a mechanical **outcome-blind** rule
  (lowest `character_id` per Path, plus the next-lowest overall), pinned by id,
  registered through the ledger whose refusal to overwrite a slug *is* the
  pre-registration. Neither `3d` fixture character is in the cohort.

---

## Exit criteria — all seven

| # | criterion | status |
|---|---|---|
| 1 | gate reads exactly 5 of 41, 2 qualified | ✅ identical to the opening run |
| 2 | rebuild green at 21 steps; purity 0/47; sim engine passes for the paladin fixture, new fixtures' failures recorded | ✅ 21 steps, 0/47, all checks pass with 6 XFAILs registered |
| 3 | a wrong `SEASON` hard-fails the crawl; a simulated schema break fails and does not stamp the day | ✅ both demonstrated |
| 4 | `grep -n "\bT[0-9]" primer/PLAN_3C_clean_exit.md` returns nothing | ✅ |
| 5 | every `spell_scaling` source ranked (enforced); provenance NOT NULL; conflict count includes coefficients; Holy Shock exclusion implemented | ✅ 6 sources validated, 4,815/4,815 rows, 30+142, exclusion fires on 13 logs |
| 6 | `calibrate_vs_log` refuses without a stat block and refuses to report alignment with no anchor | ✅ both |
| 7 | provably excluded from `candidates()`, cohort 41, by test | ✅ `check_gate_exclusion.py`, 4 checks — ⚠ the *snapshot* is `3f` |

---

## 🛑 For the owner — three things, none blocking

1. **The gate cohort slides (see above).** The fix is to pin it by id. It is
   `3e` work and I did not touch it.
2. **Holy Shock: report vs substitute.** The primer's C4 says *"then the scraped
   0.214 stands in calibration"*, which reads as *swap the tool onto the
   independent value*. I implemented the exclusion the seed file literally
   documents (Holy Shock cannot vote in the Holy group) and **report** the
   independent 0.2145 beside it, because substituting changes a calibration
   number and `3d` ships none. If you want the substitution, it is a small `3e`
   change with both numbers already visible in the output.
3. **`bugs/` vs engine bugs — convention conflict.** The primer's D3 says to file
   the six engine defects in `bugs/`. `bugs/README.md` says the opposite in as
   many words: *"These are **game** bugs, not this repo's bugs."* I honoured the
   repo — engine defects are in `primer/ENGINE_BUGS.md`, so the queue you submit
   to Ascension from stays clean. If you prefer `bugs/`, it is a `git mv`.

## Incidents

* **The scheduled crawler fired mid-session** (17:23–17:35 UTC) and committed
  `9cdab2e` using the *old* code — the unscoped `git add data/source`. It swept
  nothing extra only because my working files sat outside `data/source`. That is
  the A2 risk, observed live, an hour before A2 shipped.
* **I deleted 22 tracked capture files** while cleaning up the A2 test
  (`rm -rf data/source/captures` instead of the one test file) and restored them
  with `git checkout`. `git diff HEAD` is empty and nothing was committed in the
  broken state. No data lost.

## Next: `3e`

Modelling. Read `primer/ENGINE_BUGS.md` first — it is the concrete work list, and
E5/E1's masking relationship means several of them must be fixed together.
Righteous Vengeance must be un-broken **and talent-gated**, with the cohort-wide
delta measured before acceptance. Every coverage task reports slice accuracy
before and after. The holdout (`holdout_3e_crawled_gate_validation_set`) is read
once, at the end.
