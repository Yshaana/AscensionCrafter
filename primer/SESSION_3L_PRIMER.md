# SESSION `3L` PRIMER — Block C first, then tuning. Pre-registered.

> **`LIVE`** — the work order for session `3l`, drafted 2026-08-07 (late evening) from
> `AUDIT_3K_ADVERSARIAL.md` (§5 is the source list; this file orders and scopes it).
> **Expiry: superseded by the `3l` session record when `3l` closes** — mark it
> `SUPERSEDED BY` that file, per the established pattern. *(Landing this file and the
> audit in `primer/` stales `CLAUDE.md`'s pasted census by two; refresh the paste in
> the same commit or `check_refusals.py` A4 fails at your own first commit.)*

**Audit implemented:** `AUDIT_3K_ADVERSARIAL.md` (⚠ delivered via the oversight chat,
not yet in `primer/` — committing it is pre-flight).
**Previous session record:** `primer/Session_2026-08-07_3k_coverage.md`.

---

## §0 — The rules (unchanged in substance, renumbered)

🛑 **`3l` is a MODELLING session: the gate is EXPECTED to move — by tuning this
time.** The permission is narrow:

1. **No commit that can move the gate lands without a pre-registration that is its
   commit-parent.** Prediction first, run second, `git log --format='%H %p %s'`
   proves parenthood. A falsified prediction is reported, not rescued. An unexpected
   move is a finding: stop, commit the pair with its cause, no retroactive prereg.
2. 🆕 **A quoted baseline must exist as a COMMITTED artifact** (`3k` audit §3.2 —
   the 62.9% baseline existed only as prose). Before any prereg: derive the corpus
   from the current tree, regenerate the instrument, **commit it**, and only then
   register predictions against it. Derive first, commit the before, then predict.
3. **Order of gate-capable work: C2 → tuning.** `ContentProfile` presets feed the
   sim side; if C2 lands mid-tuning nobody can attribute the movement. C2 gets its
   own prereg pair, committed and measured BEFORE the tuning prereg is written.
4. **No coefficient is fitted to the parse it must later check.** Tuning means
   finding the *mechanism* behind an under-production (missing coefficient, missing
   talent multiplier, missing buff state, wrong delivery) with provenance, never
   scaling a ratio to its own target. A gap you cannot close from provenanced data
   is a named refusal.
5. **Mutation discipline continues:** every commit that changes a check ships the
   RED mutation, run, cited, registered in `ENGINE_BUGS.md`'s parser-enforced table.
   **M54+ are yours.** State the insertion point when a mutation restores deleted
   code (`3k` audit §3.5: M50's red count was insertion-point-dependent).
6. **Never quote coverage as progress toward the gate** (`3k` P4, measured). Report
   absent share and slice accuracy together, always.
7. **The holdout stays unspent** unless the owner explicitly spends it. If tuning
   moves the ≥20% slice materially, ASK at session end — reading it is one-shot,
   post-E15, like-for-like, and it is the owner's bullet to fire.

---

## Pre-flight

**0 — THE MC CAPTURE COMMIT (first, its own commit — this data exists only on the
owner's disk; a fresh clone does not have it).** Commit
`data/source/captures/2026-08-07_elric_mc_first_raid/` — two WoWCombatLog halves
(89.4 / 91.4 MB, split by a client crash), `Molten Core.txt` (6 Elric stat-export
blocks + 20 inspect links for 18 raid members), and its README (house provenance
format, verified by the oversight chat) — **together with**
`primer/FINDINGS_MC_capture_2026-08-07.md` (born `FINDING`, status line present;
`3k`'s pre-flight landed the other three docs but not this one). Two tripwires,
both intentional: the logs exceed the 5 MB staged-file rule — **sanctioned
exception, owner decision, per the four committed capture precedents in
`data/source/captures/`; say so in the commit message** — and the new `primer/`
file stales `CLAUDE.md`'s census paste: regenerate it in the same commit or the
suite fails.

Then, one commit:

1. Commit `AUDIT_3K_ADVERSARIAL.md` into `primer/` (born `FINDING`, dated
   2026-08-07). The owner has the file from the oversight chat.
2. Overwrite `primer/CHAT_MONITORING_PRIMER.md` **in place** with the v7 content
   (owner has it; versionless file, version in the title line — **never a `_v7`
   sibling**).
3. `season_config.py` docstring fossils: "Phase 2 flips on 2026-08-08" (~line 12)
   and "the 2026-08-08 flip" (~line 29) — the constants below them are current, the
   prose is not.
4. ⚠ **Regenerate, don't retype, the two-refusal mass figure.** `PROGRESS.md` and
   the `3k` close-out say the two named refusals are "**3.5** points of absent mass
   over 10 characters"; the session's own prereg table says **2.61 + 1.47 = 4.1**.
   The committed summary carries no per-key rows, so the tree cannot adjudicate —
   emit the number from the tool (see B0) and correct whichever document is wrong,
   citing the run.
5. This file's status line; census refresh in the same commit (+2 `primer/` files).

---

## Block C — the two owner-scheduled deliverables. FIRST. Third carry is not an option.

Carried in `3j`, carried again in `3k`. If the owner wants them dropped instead,
that is a stamped decision, not a fourth silent carry.

**C1 — `gear_tier_stats(phase=…)` production caller** (CLI or report path). It now
has a real refusal case: the Molten Core window exists with **zero snapshots** — the
caller must refuse it with a named reason ("phase window empty: 0 snapshots"), never
report an empty tier as a measurement. Ships with its RED mutation (M54 candidate:
stub the refusal to return an empty dict). Cannot move the gate.

**C2 — `ContentProfile` presets → corpus-measured durations** for the content types
the gate's scopes use. The corpus holds thousands of real encounter durations; this
is measurement. Provenance strings become `measured: <query>`. 🛑 **Own prereg pair
(§0 rule 3), committed and its gate pair measured BEFORE the tuning prereg exists.**
Predict the direction and rough size of the gate effect, or state explicitly that
none is predicted and why.

---

## Block B — tuning (the registered core)

**B0 — widen the instrument, then commit the baseline.** `per_ability_summary.json`
currently commits only aggregates (`absent: {rows: 287, share: 59.9}`). Add the
ranked per-key table (spell_id, name, state, share of cohort logged, character
count, producing ratio where producing) — it is exactly what every target-pick and
every audit reads. Then: rebuild `builds.db` from the current tree, regenerate,
**commit** — this is the baseline every later pair cites (§0 rule 2). Instrument
change ships with a RED mutation.

**B1 — pre-register the tuning pass.** Mode = ratio tuning of PRODUCING abilities
(median 0.2573, n=107). The prereg names: the target abilities (from B0's committed
artifact, by spell_id, ranked by producing logged-damage mass), the suspected
mechanism per target (diagnosis first — see B2), falsifiable pass numbers (e.g.
"producing median into X–Y; slice at ≥20% into A–B%; within-±20% count expected
0 → N"), and what is NOT predicted.

**B2 — diagnose before fitting, and the P2 thread is the warm-up.** Deyindra and
Shana hold the RV card, log the DoT, and report zero crit damage — first question
(the record's own): do their resolved abilities carry `p_crit > 0`? If not, that is
a stats-resolution gap that may explain more than RV. Decompose each target's
under-production into: missing coefficient (site/client route exists?), missing
talent/buff multiplier, wrong rank, wrong delivery model, starved APL. Per-mechanism
verdicts, the `3b` decomposition style — no split that merely sums to the miss.

**B3 — fix what has provenance; refuse what doesn't.** Every magnitude cited to
`spell_effect_values` / `spell_scaling` / stamped measured facts. Named refusals for
the rest.

**B4 — pairs.** Instrument + gate manifest from a clean tree after each gate-capable
commit; every pair cites its prereg; falsifications reported.

**B5 — scope boundary, owner decision 1 (ask, don't guess):** trigger-delivery
modelling (Deep Wounds, Ignite, the diseases, imbue procs — the structural bulk of
absent mass; the record calls it "the shape of `3l`'s work" in §3 while §7.1
registers tuning). In `3l`, or `3m`'s own session? Default written into this order:
**tuning of producing abilities only; delivery modelling deferred whole** — same
attribution logic as `3k`'s coverage/tuning split. If the owner pulls it in, it gets
its own prereg, separate from B1's.

---

## Block D — coverage odds and ends (only if registered; else named in the handoff)

**D1 — Devour Mind (287865, 6.63%, 2 chars)** — the largest single absent key,
deferred by name from `3k`. Only under a registered coverage add-on with its own
prereg.
**D2 — the `--with-dbc` unblock:** if the owner has run `run_dbc_extract.bat` with
`SpellItemEnchantment.dbc` in scope (ask at session START so it can run in
parallel), build Consecrated Holy Weapon (200818) and Seal of Command (20424) from
the fresh extract — provenance-enforced, own prereg if the gate can move.
**D3 — the 1,208 owner<pet groups (THIRD carry):** explain, or register as a bounded
unknown with measured cohort impact (0 of 41) and a named unblock. Pick one; this
does not carry a fourth time.
**D4 — keyed-but-starved (12.9%, GCD allocation):** register or re-defer by name.

---

## Block E — the MC capture: the first per-parse stats the project has ever had

**E0 — the ingest gate.** 🛑 **Nothing derives a number from this capture until its
records verifiably resolve to `Phase 2 - Molten Core / Onyxia` — not NULL, not
Zul'Gurub.** Everything in it is post-boundary (logs are BST on disk; 18:17–20:03
UTC). The committed 19:45Z payload should label ≥18:00Z as Phase 2 (the harness arm
proves 18:30Z does) — verify it on the real ingest and refuse otherwise. Read the
capture README **and** `FINDINGS_MC_capture_2026-08-07.md` before parsing; the
caveats live there.

**E1 — the Gehennas kill is ONE pull split across the two log halves** (~60 s crash
gap). Never two encounters, never dropped as incomplete. If the parser cannot
represent a cross-file encounter, that is a named limitation to fix or refuse —
not a reason to split or drop the pull.

**E2 — T5 unblock, own prereg.** The 6 Elric stat-export blocks are the first
per-parse stats ever captured — the unblock for `infer_coefficient`'s
`refused:no_per_parse_stats` (`core/builds/inference.py:350`), which gates Phase 3
criteria 3-full and 4. Using them is `3l`-scope **with its own pre-registration**
(what the stats feed, which refusals may convert to verdicts, falsifiable
expectations) — separate from B1's.

**E3 — 🛑 admissibility predicate 2 (deaths > 0) from log-sourced deaths is a STAMP
CHANGE, not a drive-by.** Owner decision required; D7-style append to
`predictions/CALIBRATION_TOLERANCE.md`; pre-registered with its measured cohort
effect before any gate re-read; applies identically to tuning set and holdout
(`3h` D4 rules in full).

**E4 —** site reports 116/117 are pending tier-2 crawl pickup — note it, don't
chase it.

---

## Standing decisions needed from the owner (ask, don't guess)

1. **B5 scope:** delivery modelling in `3l` or deferred? (Default: deferred.)
2. **Block C:** confirm C1+C2 first — or stamp a re-scope/drop. No third carry.
3. **Holdout:** unspent by default; if the tuned slice moves materially, the
   end-of-session ask is the owner's call.
4. **`--with-dbc` run** (his machine, double-click, ~minutes): yes/no this session.
5. **E3 — predicate 2 arming** from log-sourced deaths: a stamp change; decide
   before it is coded, or leave it unarmed by name.

---

## Close-out (its own commit, per the established pattern)

Session record `primer/Session_<date>_3l_tuning.md` (born `HISTORICAL`) with the §0
commit-by-commit gate table and prereg parent pairs; `PROGRESS.md` top block
replaced, `3k` block collapsed; this file `SUPERSEDED BY` the record; final gate
manifest from a clean tree; `check_refusals.py` / `check_sim_engine.py` /
`check_core_purity.py` exit codes cited; the honest NOT-done list; and the
**coverage + accuracy pair quoted together** wherever either appears.

## What `3l` hands to `3m`

A gate whose producing abilities are diagnosed (fixed or refused with mechanism
named), measured content profiles under the sim side, the production caller alive,
and — if deferred — trigger-delivery modelling as `3m`'s single registered concern,
with the P4 lesson stapled to it: delivery coverage will not move the slice either
until the delivered amounts are right.
