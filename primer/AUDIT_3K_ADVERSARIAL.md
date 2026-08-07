# AUDIT `3k` — ADVERSARIAL

> **`FINDING 2026-08-07`** — the audit of session `3k`, written from a fresh clone at
> `7729f01` (HEAD; no post-close commits exist). Method: clone, read the diff
> `b2ad6c1..7729f01`, run all three harnesses on the clean clone, and **independently
> re-run all four of the session's registered mutations from source** (M50, M51, M52,
> M53) rather than trusting the record's RED column. One check went further than any
> previous audit: the Righteous Vengeance card-id set was **re-derived from the
> committed client extract**, not just read from the constant. Claims not reproducible
> from the clone are marked as such.

**Verdict in one line:** `3k` survived its audit. Every number spot-checked reproduces
from the tree, the prereg→code commit-parent pairs are real, both falsified
predictions are reported un-rescued exactly as the discipline demands, and the
session's headline lesson — **coverage is not accuracy** — is the right thing to have
measured rather than assumed. The findings below are small; the loudest one is that
**Block C has now been carried twice**, which is a scheduling failure the tree
discloses honestly but cannot fix by disclosure.

**Closing gate as committed:** `0 of 35 within ±20% · 0 qualified · slice 26.31%
(n=23)`, 3 NOT ADMISSIBLE (Nodding 52s window, Boomcat 0.24, Deyindra 0.22).
Reproduced from `predictions/gate_manifest_3e.json` (status `LIVE`, clean tree,
`git_sha cf5ff3c` — regenerated at the close-out commit, the `3j` pattern), not
re-run: no `.db` is committed. Absent share **59.9%** (was 63.9% on the committed
baseline; 62.9% on the fresh-corpus baseline — see §3.2). Producing median **0.2573**
(n=107), phantom share **53.8%**.

---

## §1 — What `3k` earned (and what this audit re-ran itself)

* **M52 (delete the `per_event` `crit_damage` entry)** — re-run from source by this
  audit: **1 FAIL** (`[3k-B3] per_event dict keys include crit_damage=False`), suite
  exit 1; restored, exit 0. **Exact match** with the registered red.
* **M53 (stub `holds_rv = True`)** — re-run: **1 FAIL**, and the failure text proves
  the AST half of the session's own §4 lesson is real: `holds_rv derived from
  NOTHING, constant assignments=['True'], branches gated on it=3`. The check reads
  derivation structure, not the name — a stub cannot satisfy it. **Exact match.**
* **M51 (delete the `_overlapping_windows` arm)** — re-run: **1 FAIL** (`(no
  refusal)` where same-`start_date` payloads must refuse). **Exact match.** The
  ambiguity protection demonstrably *moved* rather than vanished.
* **M50 (restore `len(tops) != 1` in `phase_guard` AND `assert_phase`)** — re-run:
  **red, 4 FAILs** against the registered **3**. The variance is
  insertion-point-dependent: with the count arm restored *ahead of* the overlap arm,
  the same-`start_date` fixture also trips it (wrong refusal reason → 4th FAIL);
  restored after, 3. Not a defect — the check catches the restoration either way —
  but ENGINE_BUGS' M50 row could name the insertion point for exact
  reproducibility.
* **Harnesses on the clean clone:** `check_refusals.py` **67 PASS, 0 FAIL, exit 0**
  (up from 59 — the eight new `3k-B0`/`3k-B3` arms all run on a clone);
  `check_sim_engine.py` exit **2** (verdict-bearing refusal on the missing db, per
  `3j` A6); `check_core_purity.py` **50 files, 0 violations**. All three match the
  close-out commit's claims.
* **Prereg parenthood verified with `git log --format='%h %p %s'`:** `e803275` is
  the direct parent of `9d29028` (39 s), `c69a46f` the direct parent of `dc8281b`
  (5 m 53 s). Prediction first, run second, both pairs. No gate-capable commit lacks
  one.
* **🆕 The RV card-id set re-derived from the crosswalk, independently.** The
  constant `RIGHTEOUS_VENGEANCE_CARD_SPELL_IDS = {53380, 53381, 53382}` was located
  by a name-LIKE query over `snapshot_cards` (its own comment says so). This audit
  re-derived it from `dbc_character_advancement` in the committed extract: the
  Righteous Vengeance card line is **exactly** `53380/53381/53382`, `max_rank 3` —
  and the duplicate-name trap is live here: an other-realm sibling line
  (`1153380–82`, 11-prefix space) exists and is correctly excluded. The constant is
  right, and it is now confirmed by the route the hard rules prescribe, not only by
  the route that found it.
* **Both falsifications are reported, not rescued.** B0's P1 (`0 of 36` vs `0 of 35`
  both sides) is diagnosed to a *stale baseline database*, with the honest
  re-measure done by checking the three changed files back out and re-deriving —
  and the resulting rule ("a gate reading is only a baseline if the corpus under it
  was derived from the tree you are about to change") is the session's second-best
  finding. P2 (7 of 9, not ≥8) and P4 (slice unchanged at 26.3%) stand as falsified
  in the record, the prereg, and PROGRESS. **P4's falsification is the finding of
  the session** — coverage bought 3 points of absent mass and zero accuracy, the
  producing median *fell* (0.2727 → 0.2573), and every document that could have
  quoted coverage as progress instead warns against it.
* **The document half held again.** PROGRESS.md's top block is current (boundary
  retired, 36→35 explained, holdout caveat carried); `PHASE_3_builds_repo.md`'s
  criterion-1 fossil is corrected **by appending** with the full 7-criterion audited
  table added (2 of 7 met — verified: no `gear_tier_stats` caller exists anywhere in
  `cli/`/`tools/`/`api/` (grep), `ContentProfile` still carries 6 of 8
  `assumption:` strings); D2's annotation on the frozen `gate_manifest.json` is
  **annotation-only** — this audit JSON-compared the file before and after and the
  frozen numbers are byte-identical apart from the status note; the census
  (68 files — 13/39/6/10) is generated-and-asserted; the v6 monitoring primer is in
  place with **no versioned sibling**; the appended `phases.jsonl.gz` capture
  verifies (2 records: 15:49Z with 3 phases, 19:45Z with 4, MC top-level).

The gate read `0 of 35 / 0 / 26.3%` at every gate-capable commit, the one
denominator change is explained by corpus growth and disclosed in bold, and the
session opened no scope it had not registered. Second session running in which the
sharpest available criticism is procedural, not substantive.

---

## §2 — The phase machinery after Block 0 (state, verified)

* `EXPECTED_PHASE_NAME = "Phase 2 - Molten Core / Onyxia"`; the flip is modelled
  **additively** (owner decision stamped in three places: prereg, docstrings,
  PROGRESS). Current phase = latest-starting active top-level, implemented twice by
  design (`core/builds/phases.py` + `season_config.py` — `core/` may not import the
  config; the purity check enforces it).
* `NEXT_PHASE_BOUNDARY` **self-retired** exactly as its docstring promised — the
  19:45Z payload carries a top-level window starting at the boundary. Verified by
  the harness arm (`declared boundary self-retired=True`).
* **Zero corpus captures fall on the MC side** (latest 16:02:50Z). The Molten Core
  window exists and is empty — which converts C1's "refuse with a named reason"
  from a hypothetical into a testable case.
* The standing "no gear tier reads" freeze is **lifted in principle** — labelling is
  resolved — but remains *practically* moot: the production caller C1 still does
  not exist, so nothing can read a gear tier anyway.
* ⚠ Next boundary, the count grows to three actives. The additive model handles it;
  the thing to watch is a future **same-`start_date`** pair (still refuses, M51
  proves the arm is live) and a future **child-phase** boundary, where
  `NEXT_PHASE_BOUNDARY` must be re-armed by hand — that protocol now has precedent
  but still no committed code path. Acceptable: the guard's docstring documents the
  re-arm obligation.

---

## §3 — Findings against the session (small; none moves a number)

1. **🛑 Block C has now been carried TWICE, against a work order that said "not
   carried again."** The record's §6 is honest about it and the reasoning (budget
   spent on Block 0's emergency + one coverage target) is defensible — Block 0 was
   genuinely unplanned and genuinely first. But this is the third session in which
   an owner-scheduled deliverable was scheduled and the fourth in which it did not
   land. **`3l` must open with Block C or the owner must formally re-scope it.**
   C2 in particular is load-bearing (presets feed the sim side of the very gate the
   tuning session will be judged on) and needs its own prereg pair — doing it
   *after* tuning would contaminate the tuning attribution.
2. **⚠ The B1 prereg's baseline is quoted from an uncommitted regeneration.** At
   the prereg commit (`57e844f`) the committed `per_ability_summary.json` still
   read **63.9% absent / 36 characters / 646 rows** (git_sha `9311a04`, stale
   corpus); the prereg's stated baseline — **62.9% / 35 / 652** — comes from a
   fresh-corpus regeneration that was never committed as an artifact. The
   provenance line ("as regenerated this session at `git_sha 57e844fb`") is
   accurate, but a reader running `git show 57e844f:predictions/per_ability_summary.json`
   gets different numbers, and the before-side of the coverage pair exists only as
   quoted prose. Same gap one level down: the committed summary carries only
   aggregate counts (`absent: {rows: 287, share: 59.9}`) — **no per-key table** —
   so B2's instruction to "pick targets from the committed artifact" was not
   literally executable; the target table (Devour Mind 6.63%, RV 3.32%…) is pasted
   tool output with no committed source. Two fixes for `3l`, both cheap: commit the
   before-summary as its own artifact in the prereg commit, and widen
   `per_ability_summary.json` to carry the ranked absent-key rows (it is exactly
   the table every target-pick reads).
3. **⚠ `season_config.py`'s module docstring still narrates the old world:**
   "Phase 2 flips on 2026-08-08" (line ~12) and "makes the 2026-08-08 flip
   self-announcing" (line ~29), in a file whose constants were correctly updated
   below. Historical-rationale prose, but the file is code every capture loads.
   One-line fix, `3l` pre-flight.
4. **⚠ The session record §5 cites the final manifest at `git_sha 9683e87`;** the
   tree's final manifest is `git_sha cf5ff3c` (regenerated once more at `7729f01`,
   the established close-out pattern). The record is `HISTORICAL` and was true when
   written; noted so the next reader doesn't burn time on the mismatch.
5. **M50's registered red count (3) is insertion-point-dependent** (this audit
   measured 4 with the arm restored ahead of the overlap check). Substance holds;
   a five-word note in the M50 row would make it exactly reproducible.
6. **The monitoring primer's expiry has fired:** v6 says "supersede at v7 when `3k`
   closes" and `3k` has closed. v7 is due from the oversight chat (this one),
   commit-in-place at `3l` pre-flight together with this audit — the same handoff
   pattern as v6 + AUDIT_3J. Keep the streak at two.

---

## §4 — Reproducibility limit (standing, restated)

Tier-2 captures gitignored; no `.db` committed. Corpus figures (472 snapshots, the
9-character RV roster, the 0.004–0.005 ratios, Deyindra/Shana's zero crit damage)
are unverifiable from the clone. What IS verifiable — and was verified — is
function behaviour under the harness fixtures, manifest-internal arithmetic, the
band table, commit ordering and parenthood, all four mutation reverts, the frozen
manifest's immutability, and the card-id set against the committed client extract.

---

## §5 — The list `3l` works from

In priority order. Item 1 is a gate on the session being scheduled at all.

1. **Block C FIRST, before any tuning commit — or a stamped owner re-scope.**
   * **C1 — `gear_tier_stats(phase=…)` production caller.** It now has a real
     refusal case to prove itself on: the Molten Core window with zero snapshots
     must refuse with a named reason, not report an empty tier as a measurement.
   * **C2 — `ContentProfile` presets → corpus-measured durations**, its own prereg
     pair, committed BEFORE the tuning prereg. It can move the gate; if it lands
     mid-tuning, nobody can say which change did what.
2. **TUNING is the registered load-bearing problem.** Producing median 0.2573,
   n=107, and `3k` measured that coverage does not move the slice. Pre-register
   the mode, the target set (from a committed artifact — see §3.2), and what a
   pass looks like. The structural half — trigger-delivered damage the APL cannot
   contain (Deep Wounds, Ignite, the diseases, the imbue procs; the RV case was
   merely the one already wired) — is a *delivery-modelling* problem, not a
   coefficient problem; decide explicitly whether `3l` opens it or defers it,
   and register the choice either way.
3. **One owner-gated `--with-dbc` run scoped to include `SpellItemEnchantment.dbc`**
   unblocks both named refusals (Consecrated Holy Weapon 200818, 2.61%/6 chars;
   Seal of Command 20424, 1.47%/4) — ~4 points of absent mass for one double-click.
   Ask for it at session start so it can run while the session works.
4. **The P2 thread, small and sharp:** Deyindra and Shana hold the card, log the
   DoT, and their rotations report zero crit damage. First question is the record's
   own: do their resolved abilities carry `p_crit > 0`? (If not, this is a stats
   resolution gap, which is tuning-adjacent and cheap to answer.)
5. **Devour Mind (287865, 6.63%, 2 characters)** — the largest single absent key,
   deferred by name. It is `3l`'s first coverage target *if* a coverage block is
   registered; otherwise it stays named, not silently dropped.
6. **Housekeeping, one commit:** the `season_config.py` docstring fossils (§3.3);
   the B5 bucket (keyed-but-starved 12.9%, GCD allocation) registered or
   re-deferred by name; D1 (1,208 owner<pet groups, 0 of 41 cohort impact) —
   explain or register as a bounded unknown, third carry.
7. **The holdout stays unspent** until a tuned slice exists to validate. When read:
   once, post-E15, like-for-like, per the standing annotation.
8. **Pre-flight:** commit this audit to `primer/` (born `FINDING`), the v7
   monitoring primer in place (no sibling), the `3l` work order born `LIVE` with
   its expiry stated, census refresh in the same commit.

**Tone check, per the standing method:** `3k` was handed an unplanned live incident
(the flip landing in a shape no protocol covered) and processed it with a
pre-registration committed before the fix, an owner decision recorded before the
code, and a falsified prediction diagnosed to its true cause within the hour. The
coverage block then falsified its own optimism and said so in bold. That is the
method working under pressure. The criticism that remains — Block C, the
uncommitted baseline — is about budget and artifact hygiene, not about honesty.
Hold `3l` to the same standard, starting with the deliverable it now owes twice.
