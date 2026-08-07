# AUDIT `3h` — ADVERSARIAL

> **`FINDING 2026-08-07`** — an adversarial audit of session `3h`, true as of its date and
> **not maintained since**. Not citable as current truth without re-checking against the
> tree. Reclassify **`SUPERSEDED BY primer/Session_<date>_3i_*.md`** when `3i` closes.
> *(Born with a status line and an expiry condition, per `3f` F8c — and classified
> `FINDING` to match `AUDIT_3C` / `AUDIT_3E` / `AUDIT_3G`, not `LIVE`: an audit is a
> point-in-time analysis, and this one's own §4.2 was corrected within the hour.)*
>
> Written 2026-08-07 in the oversight chat, from a fresh `--depth 40` clone at `eaa7604`.

Session audited: `3h` (`357521d..eaa7604`, ten commits).
Record: `primer/Session_2026-08-07_3h_measurement.md`. Work order: `primer/SESSION_3H_PRIMER.md`
(`SUPERSEDED`). Previous audit: `primer/AUDIT_3G_ADVERSARIAL.md`.

---

## §1 — Verdict

**The engine discipline held and the instrument work is the best in the project so far.
The document discipline failed again, in the same way `3g` failed, and this time it failed
inside `PROGRESS.md` itself.**

`3h` did what an instrument session is supposed to do: it replaced the last inferred
headline with a measurement, it kept the gate byte-identical across all ten commits, it
pre-registered both measurements before running them, and it reported a false prediction
as false. The per-ability distribution is a real result and E15 is a genuinely important
find.

Three things stop this being a clean pass:

1. 🚨 **`primer/PROGRESS.md:527-580` — the `LIVE` file's own "Current position" section
   still says `3e` IS DONE and still carries `🔴 FIRST ACTIONS NEXT SESSION (3g)`
   telling the reader to fix E13 and E14 as the highest-consequence items in the repo.**
   Both were fixed two sessions ago, by this project, with closure boxes. This is exactly
   the failure class `AUDIT_3G` §4 named — and it is now in the first file every session
   reads.
2. 🚨 **Block C's logged side counts E15's duplicate rows in its denominator and drops them
   from its numerator** — the shares in its own artifact do not sum to 100%, and which copy
   of a differing pair survives is **nondeterministic**. The next-session lever list is
   picked off numbers that inherit this.
3. 🚨 **The committed manifest now ships producing-only numbers derived through that same
   defect**, with no reference to E15 anywhere in `predictions/` — while the session
   itself measured the effect (slice 20.5% → 19.8% on the consumer dedupe alone).

Findings §4–§8, ranked. Remediation list for `3i` at §10.

---

## §2 — Method, and what this audit could not check

Fresh clone, `grep` across the tree, three parallel adversarial passes (admissibility rule
+ Boomcat prereg; `LIVE`-doc vs code in both directions; the new checks' regimes). Every
mutation cited as *run* was run on a scratch copy; `/tmp/repo` was read-only.

⚠ **The limiting factor named in the monitoring primer is unchanged for a fifth session,
and `3h` made one half of it worse.** `data/derived/` is gitignored and no `.db` is
committed, so:

| number | checkable from the tree? |
|---|---|
| gate `1 / 1 / 20.5% (n=23)`, holdout deltas | ✅ pinned in `predictions/gate_manifest_3e.json` |
| producing-only `30.7% (n=20)`, keyed-but-zero median/max | ✅ now pinned in the manifest (`3h` B3) |
| **median ratio `0.253`, `11%` in band, `25%` at zero, `62.2%` absent, `90` zero-keys** | ❌ **in no committed artifact** — `per_ability_accuracy.py:70-71` writes only to `data/derived/` |
| APM `0.27`, `n_others=8`, "5 of 41" | ❌ the tool writes nothing (`parse_admissibility.py:280-281`) and stamps nothing |
| E15's `15,551 / 20,785` | ❌ prose only |

**The session's headline result is its least verifiable one.** The gate numbers got a
provenance upgrade this session; the numbers that replaced them as the interesting ones
got none. See §10 item 6.

---

## §3 — What `3h` got right (short, because it earned it)

* ✅ **The invariant is real.** `git diff --stat 357521d..HEAD` touches **no file under
  `core/`**. The gate reading `1 / 1 / 20.5%` at all ten commits is consistent with the
  tree, not merely asserted.
* ✅ **The holdout exclusion is structural, not a flag.** `per_ability_accuracy.py:261`
  filters `cc.HOLDOUT_IDS` out of the candidate list before any sim runs, and `--char`
  cannot reintroduce them. This is the strongest form that guard has taken.
* ✅ **Both pre-registrations precede their measurements at commit level.**
  `1dd464e` → `acb8ec8`; `cd54716` → `7fc5bc0`. `parse_admissibility.py` exists in no
  commit before its prereg.
* ✅ **The comparison is rate-normalised and says so.** `ratio = (sim_damage/sim_fight_s) /
  (logged_damage/encounter_s)` (`per_ability_accuracy.py:23-27`). Comparing two totals over
  different windows was the obvious trap and it was not walked into.
* ✅ **The dirty-tree refusal fails CLOSED**, including when git itself fails
  (`calibrate_crawled.py:1415`, `if dirty is not False`). `e06a8c3` is the first manifest in
  this project whose `git_sha` identifies the code that produced it. Real progress on a
  four-session-old complaint.
* ✅ **The A3 consistency assertion runs before the write** (`:1699` vs `:1711`) and is red
  under its registered mutation. An inconsistent manifest is refused, not shipped.
* ✅ **E15 is wired, not decorated.** Registry entry ↔ `EXPECTED_FAILURES` match;
  `resolve_generality()` catches stale entries in both directions; the green path was run
  and reverted **with its gate pair recorded**.
* ✅ **B2's taxonomy departure was correct and was declared.** Folding `zero-casts-allocated`
  into "refused" would have misattributed the entire zero mass to E14 — the opposite of what
  Block B existed to find out.
* ✅ **P4 was reported ❌ FALSE as stated**, and the scan's incidental find became the
  session's biggest result. That is pre-registration paying for itself; say so.
* ✅ **The absent set is emitted at all** (`per_ability_accuracy.py:228-233`). *"Excluding
  these is how coverage came to mean two things"* is the right diagnosis, written at the
  right place.

---

## §4 — 🚨 The three serious findings

### 4.1 `PROGRESS.md` carries live instructions to fix two already-fixed defects

`primer/PROGRESS.md:527` — `## Current position` reads **"✅ `3e` IS DONE"** while the top
block of the same file says `3h` is done. Under it, `:535` — `### 🔴 FIRST ACTIONS NEXT
SESSION (3g)` — is **not** wrapped in the `<details><summary>Superseded` element that the
`3f` block (`:582`) and `3e` block (`:606`) both carry. It reads as current truth and says:

| line | claim | reality |
|---|---|---|
| `:531`, `:537` | "Gate: **5 of 36, 2 qualified, slice 64.3%**" | retracted; `1 / 1 / 20.5%` |
| `:542-543` | "🚨 **FIX E13 FIRST** … every white swing is ~78× over" | fixed `7af0195` (`3g` G1); factor is **exactly 100** |
| `:557` | "**Then E14**" | fixed `6c62309` (`3g` G2) |

The archiving convention broke at exactly one step — `3g` closed without wrapping its
predecessor — and `3h`'s Block A, which existed to sweep stale documents, did not catch it.
`PROGRESS.md`'s own header says *"if you find a claim here that the tree contradicts, that
is a defect in this file."* Three of them.

🛑 **This is the highest-severity item in the audit** not because it is subtle but because
it is the first thing a fresh session reads after the top block, and it points at work
already done.

### 4.2 Block C's logged side sums the duplicate in its denominator and drops it from its numerator

**Traced from the schema up. Every link below is checkable from the tree with no database.**

1. `core/builds/corpus.py:425-434` writes each pet row with **`character_id = the owner's id`**
   and `is_pet = 1`.
2. `core/builds/corpus.py:156` — `PRIMARY KEY (scope_id, character_id, spell_id, spell_name,
   is_pet)`. **`is_pet` is part of the key**, so the owner copy and the pet copy coexist as two
   rows. E15 is real at the schema level, not just as a count.
3. `per_ability_accuracy.py:149-153` queries that table with **no `DISTINCT`, no `GROUP BY`,
   no `ORDER BY`** and gets both.
4. It then treats them **four different ways inside one function**:

| line | code | effect on a duplicated ability |
|---|---|---|
| `:154` | `total_logged = sum(r[2] for r in logged)` | **both copies counted** |
| `:204` | `logged_by_sid[r[0]] = r` | dict — **last row wins, the other copy silently dropped** |
| `:200` | `auto_logged += r[2]` | **both copies accumulated** |
| `:202` | `other_negative.append(r)` | **both copies kept as separate rows** |

🛑 **The denominator counts the duplicate and the per-ability numerator does not.** For any
character with a duplicated ability, the `coverage_share_of_logged` values in the tool's own
artifact **do not sum to 100%**, and nothing in the tool notices.

⚠ **Correcting my own first reading**, because the direction is not what "double-counted"
suggests:

| figure | mechanism | direction |
|---|---|---|
| every `coverage_share_of_logged` | collapsed numerator over summed denominator | **deflated** |
| **62.2% absent** | numerator mixes *collapsed* positive-id rows with *doubled* negative-id rows; denominator sums everything | **sign not determinable from the tree.** If the duplicated mass is mostly positive-id unmatched pet spells — which is exactly what `ENGINE_BUGS.md:923-931` concludes — the duplicate leaves the numerator and stays in the denominator, so **62.2% is understated and the absent problem is bigger than reported** |
| **median ratio 0.253 · 11% in band · 25% at zero** | positive-id ratios are computed against a **single** copy, so the doubling does **not** halve them | **largely uncontaminated.** Two exceptions: the auto row (one per character; `auto_logged` accumulates — precisely the halved pet-class autos `ENGINE_BUGS.md:929-931` observed on Malo/Ikkura/Onur), and any ability where the arbitrary surviving copy is the wrong one |
| **gate slice 20.5% and producing-only 30.7%** | `modelled_damage_share:457-497` sums every row on **both** sides, no collapse anywhere | **fully double-counted — and measured.** The dedupe run moved slice 20.5 → 19.8 |

🆕 **The collapse is a defect in its own right, independent of E15's magnitude.**
`logged_by_sid[r[0]] = r` with no `ORDER BY` means **which copy survives is nondeterministic**.
E15 records **5,234** owner+pet groups whose values *differ* (owner < pet in 1,208). For those,
`per_ability_accuracy.py` keeps whichever row SQLite happened to return last. **Two runs of the
same tool against the same database can produce different per-ability ratios**, and the tool
reports neither the drop nor the ambiguity.

Only one line anywhere acknowledges any of this, and it is scoped to a single row: the session
record's P4 entry calls *"the ~0.1 auto E15-contaminated"* (`Session_…_3h_measurement.md:80`).
`PROGRESS.md:14-18` quotes all four distribution figures bare, and `PROGRESS.md:57` hands the
next session **"the 62.2% absent-key majority"** as a modelling lever.

🛑 **So the recommendation is stronger than "re-run after the E15 fix", not weaker:
`per_ability_accuracy.py`'s logged side needs repairing before the numbers mean anything,
and the repair is the honest place to learn the absent share's true magnitude.** See §10
items 2–3.

### 4.3 The committed manifest ships producing-only numbers derived through the same defect

`predictions/gate_manifest_3e.json` was regenerated at `eaa7604`, **after** E15 was
registered at `acb8ec8`. It now carries
`median_slice_accuracy_pct_producing_only_at_coverage_ge_20: 30.749`, `producing_only_n: 20`,
`keyed_but_zero_pct_median/_max`, and a `slice_accuracy_producing_pct` on every character
row. Both the numerator (`100 + delta`, whose `logged_dps` E15 inflates — `corpus.py:594-614`)
and the denominator (`modelled_damage_share`, which sums both copies) run through the defect.

`grep -rn E15 predictions/` returns **nothing**. The session measured the magnitude of the
bite on the sibling number (20.5% → 19.8%) and did not attach it to the new keys.

⚠ The manifest gained a provenance guard this session and simultaneously gained numbers
whose provenance caveat is missing. Those pull in opposite directions.

---

## §5 — ⚠ The stamped admissibility rule: what it does not do

The rule was stamped honestly — the falsifiability check ran before the stamp, the blind
computation is real, and `Boomcat` being flagged is the right outcome. The implementation is
narrower than the stamp reads.

### 5.1 Predicate 4 is a `print()` that becomes false tonight

`parse_admissibility.py:219-225` builds `flags` from **three** inputs: `apm_ratio`, `deaths`,
`dur`. Predicates 4 and 5 never reach the verdict — they are strings:

```
:198-199  "predicate 4: capture resolves to no phase — every corpus capture predates
           the 2026-08-08 boundary, so this removes nobody today"
:200-202  "predicate 5: snapshot lag > 0h — … removes nobody by construction"
```

🚨 **`season_config.NEXT_PHASE_BOUNDARY` is `2026-08-08T00:00:00Z` — tonight.** From
tomorrow that hardcoded sentence keeps printing while ceasing to be true, and nothing tests
the condition it asserts. `CLAUDE.md`'s own rule: *a guard that cannot run must say so —
never report a condition you failed to test.* The seam exists and is three lines:
`core.builds.phases.resolve_phase(captured_at, …)`, already used at `core/builds/gear.py:121-125`.
`lag` is even collected into the table (`:229`) and never tested.

Predicate 5 is genuinely inert-by-construction and the stamp says so — fine, but it should
assert rather than assume.

### 5.2 Every refusal path lands on "admissible"

The rule's verdict is meant to be NOT ADMISSIBLE (`None`), never `False`. A **refused ratio**
is silently a pass. `ar["ratio"] is None` produces no flag (`:220`) for:

* out-of-regime kits — **22 of the 41 cohort boards are cast-time casters**, so predicate 1 is
  structurally incapable of removing any of them;
* `< 2` other scopes (`:168-171`) — an escape hatch **not present in the stamped text**;
* `SUM(casts)` NULL (`:138-139`); no scope duration (`:131-132`).

And the regime test itself fails open four ways (`:68-103`): unresolved cards are excluded by
the query (`:76-78`), a card with no `spell_dbc_raw` row `continue`s without incrementing
`n_resolved` (`:84-85`), a NULL/0 `casting_time_index` is treated as instant (`:88-89`), and a
missing `dbc_spellcasttimes` row likewise (`:93-94`). A board that resolves to **nothing**
reports `cast_time_entries = 0` → `in_regime = True` → a number.

`resolved_entries` **is** computed (`:102`) and stored (`:231`) — and **never printed**
(`:239-246`). So the stamped evidence line *"regime valid (0 cast-time entries, n_others=8)"*
cannot be distinguished from *"nothing resolved"* by anyone reading the output.

⚠ Consequence: **"5 of 41" is a lower bound produced by predicates that are inert or
fail-open for most of the cohort**, not a measurement of how much of the corpus is
inadmissible. It does not invalidate the stamp — a rule that under-removes is the safe
direction — but the blind-effect figure should not be quoted as the rule's reach.

### 5.3 Two smaller ones on the same rule

* **P9's reported outcome crosses its own predicate boundary.** `prereg_3h_boomcat.md:55-58`
  registers the bar against *"the death-deflation predicate (an APM ratio ≤ 0.5 within the
  valid regime, or deaths > 0)"*. The record reports *"removes 3 (Nodding, Robottikyrpa,
  Frediib)"* — but the stamp's own pasted output shows **Nodding was removed by the 52 s
  window predicate**. On the pre-registered predicate the count is **2**. The bar (≥1) is met
  and the stop-rule was not triggered; the headline number is not the registered quantity.
* **`MIN_PARSE_SECONDS = 60` first appears in the same commit as the run** (`:61`), unlike
  `APM_RATIO_BOUND = 0.5`, which is genuinely pre-registered. A threshold that arrives with
  its result is the shape this project distrusts everywhere else.
* **The stamped rule has no registered check.** No `EXPECTED_FAILURES` entry, no assertion
  that the module constants equal the stamped thresholds, no red mutation. `3h` A3 built
  exactly that analogue for the manifest and did not build it here, so stamp/code drift is
  undetectable.

---

## §6 — ⚠ The new checks: two arms that cannot go red

The project's most productive question, asked of `3h`'s own additions.

### 6.1 The "split sums to the headline" arm is tautological

`calibrate_crawled.py:496` — `keyed_zero = modelled - producing`. The sum therefore equals
`modelled` identically, to within two roundings, against a 0.2 tolerance.
`check_refusals.py:821` asserts that sum. **It cannot go red by any change to the split
logic.** The docstring at `:778` claims its registered mutation (`is_producing` → `return
True`) turns *"the producing==0 case and the sum case both red"*. Run: **1 of 4 cases went
red**; the sum case printed `60.0 + 0.0 vs 60.0` and PASSED.

### 6.2 The "SAME key flips to producing" case is green under the defect it excludes

`check_refusals.py:836` asserts `producing == 60.0, keyed_but_zero == 0.0`. Under
`is_producing → True` — the split reading key *membership* rather than *production*, i.e.
precisely the bug Block B exists to prevent — the output is identically `60.0 / 0.0`. PASS.

This is the `3g` G6 family (tautological arms) recurring one session later, in the checks
written to guard `3g`'s own lesson. Cases 1 and 2 of B4 are sound; cases 3 and 4 are
decoration.

### 6.3 The named zero list cannot account for its own aggregate

`calibrate_crawled.py:505-518`: `logged_by_sid` is keyed by **integer** `spell_id`, but
`per_ability` also carries the **string** keys `auto_mh` / `auto_oh`, which reach the
keyed-zero *mass* through the negative-id auto path (`:490`). So a zero-producing auto
contributes to `keyed_but_zero_pct` and reports `logged_share_pct: 0.0`, then sorts **last**
(`:517`). Reproduced on a fixture:

```
modelled 100.0  producing 30.0  keyed_but_zero 70.0
zero_list [{'spell_id': 'auto_mh', ..., 'logged_share_pct': 0.0, ...}]
```

The renderer (`:1258-1266`) prints **70% keyed-but-zero** and then names 0.0% of it. The
same dict also collapses E15's duplicate owner+pet rows, so a duplicated spell's named share
understates its own contribution.

### 6.4 Smaller regime holes

* `check_refusals.py:750` — the new `predictions/` census **fails open on an empty or missing
  directory**. Verified: renaming `predictions/` yields `0 files — 0 LIVE / 0 HISTORICAL …`
  and **PASS**. `primer/`'s equivalent is protected indirectly by the `CLAUDE.md` paste
  comparison; `predictions/` has no anchor. One `len(files) > 0` assertion closes it.
* `check_refusals.py:701` — `_status_census` classifies on any **backticked status word** in
  the first 1200 chars, not on a status *line*. A doc containing "see the \`LIVE\` gate
  numbers" counts as `LIVE`. The comment at `:687-691` claims the delimiter prevents this; it
  prevents the bare word only.
* `calibrate_crawled.py:1429` — `--allow-dirty` records a boolean **nothing reads**. No check
  asserts `git_working_tree_dirty == false` on a committed manifest, the flag never appears in
  stdout or the markdown report, and `predictions/gate_manifest.json` still ships
  `git_working_tree_dirty: true` with no flag key at all. `AUDIT_3G` §remediation asked for the
  **reason** to be recorded; a bool is not a reason.
* `check_refusals.py:395-427` — A7's refusal case runs only when the harness's own tree is
  dirty, i.e. never in the clean state the rule enforces. It is *printed* rather than silently
  skipped, so the convention is respected; note it as a check that mostly does not run.

---

## §7 — ⚠ Measurement gaps in the instrument itself

### 7.1 `30.7% (n=20)` and `20.5% (n=23)` are medians over different populations

`calibrate_crawled.py:988-995` selects on `modelled_and_producing_pct ≥ 20`; `:906-917`
selects on `modelled_damage_pct ≥ 20`. The **three** characters that fall out are, by
construction, the ones whose keyed-but-zero mass pushed them under the floor — the worst
cases. So the producing-only median is **upward-biased by selection**, and the headline pair
"30.7 beside 20.5" overstates how much of the gap the split explains.

⚠ P5's reconciliation with F9's frost-mage 33.1% (*"2.4 points"*) inherits that bias.

The honest statement is one line: the **paired** median over the same 20 characters, both
metrics. Compute both and print them together.

### 7.2 Phantom sim production is measured and never reported

`per_ability_accuracy.py:207-212` emits every sim key with `logged_damage = 0.0` when the log
has no matching row. `:287` — `paired = [r for r in all_rows if r["logged_damage"] > 0]` —
drops them, and **no statistic in the tool covers them**.

Sim damage landing on abilities the character never used inflates the aggregate delta while
earning **zero** coverage credit. That is a mechanism which makes the aggregate look better
than the per-ability truth — the exact class of thing Block C was built to expose — and it is
the one cell of the 2×2 the tool does not report. The rows are already in the JSON artifact;
it is a `Counter` and a share-of-sim-damage line.

### 7.3 The two ✅ preregistered shape predictions are weaker than they read

`prereg_3h_per_ability.md:23-24` derives P1's `[0.20, 0.45]` band from *"producing-only slice
30.7%, which is an aggregate of exactly these numbers"*; `:43-44` derives P2's `>55%` absent
from *"coverage median ~37% implies ~63% absent"*. Both are honest about their inputs — the
prereg says so in its own header — but a prediction arithmetically implied by a number already
in hand is a consistency check, not a test. P1's willing-to-be-wrong arm (`<15% in
[0.8, 1.25]`) and all of P3/P4 are real tests. Grade accordingly.

---

## §8 — ⚠ `LIVE` documents still contradicting the tree

Beyond §4.1, as of `eaa7604`:

| file:line | says | tree says |
|---|---|---|
| `predictions/gate_manifest_3e.json:19` | `successor_floor_justification`: *"slice accuracy is stable at **~62.6%** across the >=20/>=30/>=50 bands"* | the same file's bands: **20.45 / 16.86 / 16.86**. Hardcoded at `calibrate_crawled.py:1451`; `:1160` of that file says ~62% was E13's inflated autos |
| `calibrate_crawled.py:1504` | `slice_accuracy_band_note`: *"the >=0 band reads ~164%"* | the artifact's `>=0` band: **40.25** |
| `primer/ENGINE_BUGS.md:3` | *"ENFORCED in both directions by `check_sim_engine.py`"* | **nothing in the tree parses `ENGINE_BUGS.md`.** `resolve_generality()` (`check_sim_engine.py:248-283`) enforces `EXPECTED_FAILURES` ↔ `GENERALITY_RESULTS` **names** only. A check that cannot go red for the failure it advertises |
| `check_sim_engine.py:193` | registers *"[frost_mage] every well-sampled ability's modelled per-cast mean…"* | the string appears in **no** document; its registry value names no E-number. Direction (b) already broken |
| `check_sim_engine.py:131` | frost-mage DPS assertion, still registered | owned only by `ENGINE_BUGS.md:747` (E13, ✅ FIXED) and `:846` (E14, ✅ FIXED). Orphaned by the correct closures |
| `primer/CHAT_MONITORING_PRIMER.md:4` | *"Supersede at **v4** when `3h` closes"* | `3h` closed at `eaa7604`. Still `LIVE` at v3, body frames Blocks B/C/D as **unrun** |
| `primer/PLAN_3G_self_verifying_gates.md:32-34` | *"`within_tolerance` … has **no coverage floor**"* | applied at `3g` G4 (`389c735`); `calibrate_crawled.py:864-866` |
| `predictions/CALIBRATION_TOLERANCE.md:197-198, 203` | *"until that split is measured…"*, *"a `3h` Block C question"* | both measured in `3h`; sections never gained the producing-only companion |
| `predictions/CALIBRATION_TOLERANCE.md:238` | *"stable at ~63% … 144% at ≥10%, 165% at ≥0%"* | pre-E13; contradicts the corrected band table 55 lines above. Stamped text may not be rewritten to fit a result — it needs the same *"measured on E13-inflated autos"* annotation `calibrate_crawled.py:1160` got |
| `ingest/export/seed_epistemics.py:252` | *"Blizzard casts … **305** in Window C"* | `ENGINE_BUGS.md:559-566` corrects to **4** and calls 305 *"a raw grep LINE COUNT, wrong by ~76×"*. Untouched since an E14 commit; breaches `CLAUDE.md`'s same-session seed rule |
| `calibrate_crawled.py:692` | cohort summary: *"the sim **produces damage for** a median of…"* | the exact phrase B1 retired everywhere else in the file (`:427-430`, `:1250-1258`). Renders into `data/derived/calibration_crawled.md` every run |
| `tools/scrapers/scrape_ascension_db.py:12` | *"produces damage for a median 37%…"* | stale phrasing **and** a pre-E13 figure, in a live tool |
| `primer/PROGRESS.md:73` | holdout *"0 of 5 … median slice **9.8%**"* | source (`Session_…_3g_explosions.md:433`) says **9.8% (n=4)**. Two cohort sizes in one row |
| `primer/ENGINE_BUGS.md:17` | *"Every entry here is a FAILING CHECK"* | `:534` (E8) and `:670-698` (eight more) self-disclose that they are not. Honest, but the invariant as written is false and should carry its exemption |
| `primer/ENGINE_BUGS.md:495, 534` | cites `check_sim_engine.py:78-102` and *"line-15 invariant"* | keys are at `:81, :86, :103`; the invariant is at `:17` |

✅ **Confirmed clean:** status-line census (0 unclassified in `primer/` **and** `predictions/`,
the latter new this session); E13/E14 closure boxes and the `~78 → exactly 100` correction;
`gate_manifest.json` correctly self-labelled `FROZEN 3d RECORD` with `159.79` formally
retracted; every surviving `64.3` / `159.8` / `~78` outside §4.1 sits in a `HISTORICAL` doc or
an explicit retraction list.

---

## §9 — 🚨 Time-critical, tonight

`season_config.NEXT_PHASE_BOUNDARY = 2026-08-08T00:00:00Z`. `3g`'s three defences have still
never fired. On the 8th, before any gear tier is read:

1. `phase_guard()` asserted the payload's active top-level phase equals `EXPECTED_PHASE_NAME`.
2. `phase_label` went **NULL** rather than mis-stamping, and the declared boundary caught a
   Phase 2 shipped as a *child*.
3. `horizon is None` failed **closed**.
4. If the flip happened: `EXPECTED_PHASE_NAME` bumped and the corpus re-derived **before**
   any gear tier read. Leaderboards and armory are the only data a flip destroys; reports
   persist, so the report backfill has no deadline.
5. 🆕 **`parse_admissibility.py:198-199` starts lying tomorrow** (§5.1) — predicate 4's
   hardcoded "predates the boundary" sentence. Fix or gate it in the same session that
   applies the rule.

---

## §10 — The list `3i` works from

Ordered. Items 1–3 are the pre-conditions for the modelling work `3h` handed forward; doing
modelling first aims it at contaminated targets.

| # | item | why now | size |
|---:|---|---|---|
| **1** | **Unwrap-and-archive `PROGRESS.md:527-580`.** Wrap the `3e`/`3g` block in `<details><summary>Superseded`, matching `:582` and `:606`. Add a `check_refusals.py` arm: no un-collapsed `FIRST ACTIONS NEXT SESSION` block may name a session earlier than the top block's | §4.1 — a `LIVE` file instructing work already done, two sessions running | tiny |
| **2** | **Fix E15 at ingest + `encounter_performance.dps`, one commit, its own pair** (consumer-dedupe-only pair known: 20.5 → 19.8). Check leaves `EXPECTED_FAILURES`. Also look at the **1,208 owner < pet groups** E15 says are unexplained | the gate's own `logged_dps` is wrong for every pet owner | medium |
| **3** | 🆕 **Repair `per_ability_accuracy.py`'s logged side, then re-run it.** Make the numerator and denominator agree (one policy for a duplicated `(spell_id, spell_name)` pair, applied at both `:154` and `:200-204`), assert the per-row shares sum to 100 ± ε, and add an `ORDER BY` or an explicit refusal so no row is dropped nondeterministically. Then re-state `0.253 / 11% / 25% / 62.2%` — and expect the absent share to **move up**, not down (§4.2) | the absent-key majority is `3h`'s handed-forward lever and its magnitude is currently indeterminate | small |
| **4** | **Apply the stamped admissibility rule**, one commit, its own pair, `1 → 0` expected with `Boomcat` NOT ADMISSIBLE. In the same commit: implement predicate 4 via `resolve_phase` (§5.1), print `resolved_entries` and the comparator median beside every ratio (§5.2), turn the `< 2 other scopes` escape hatch into a stated refusal, and add the stamp↔constants assertion (§5.3) | the rule goes live the day predicate 4's hardcoded sentence stops being true | small–medium |
| **5** | **Then modelling, from the re-run distribution.** Current visible levers, to be re-confirmed post-fix: Elemental Blast (0.02–0.19 on three characters at 56–69% of their logged damage), the starved-allocation mass (E6/E7, 10.9%), the absent-key majority. E9/E11/E12 keep their run green paths | first gate-moving modelling since `3g` | large |
| **6** | **Commit a small per-ability summary artifact** — the distribution's summary stats and per-character coverage split, not 651 rows — so the next audit can check the session's headline result from the tree (§2) | the headline result is currently the least verifiable number in the project | tiny |
| **7** | **Repair the two tautological check arms** (`check_refusals.py:821, 836`) and the auto-key hole in the named zero list (`calibrate_crawled.py:505-518`); add `len(files) > 0` to the `predictions/` census; tighten `_status_census` to match a status *line* | §6 — `3g` G6's lesson, one session later | small |
| **8** | **Document sweep, both directions:** the §8 table. Priority: `gate_manifest_3e.json:19`'s `~62.6%`, `ENGINE_BUGS.md:3`'s unenforceable "both directions" claim (either build the parser or downgrade the claim), the orphaned `check_sim_engine.py:131` / unregistered `:193`, `CHAT_MONITORING_PRIMER` → v4, and `seed_epistemics.py:252`'s retracted 305 | document discipline is now the weaker half for the **second** consecutive session | small |
| **9** | **Report the phantom-production cell** (§7.2) and the **paired** producing-vs-has-a-key median over the same members (§7.1) | two known blind spots in the project's newest instrument | tiny |

---

## §11 — Two questions to carry into `3i`

1. 🆕 **"Does this document have an owner who runs?"** `3g` and `3h` both shipped flawless
   code beside stale `LIVE` prose, and both times the stale prose was in a file no check
   reads. `ENGINE_BUGS.md`'s "enforced in both directions" is the clearest case: the claim is
   an aspiration with no parser behind it. **Either a document is machine-checked or its
   `LIVE` badge is a promise a human has to keep — and this project has now missed that
   promise twice in a row.**
2. **Still the best one, unchanged:** *does this check or metric have a regime where it
   returns a number it cannot support?* It found the fail-open admissibility predicates
   (§5.2), the tautological split arms (§6.1-6.2), the fail-open `predictions/` census
   (§6.4), and the auto-key hole in the zero list (§6.3) — in a session whose whole purpose
   was to stop doing that.
