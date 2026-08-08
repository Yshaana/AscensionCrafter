# CHAT MONITORING PRIMER v10 — AscensionCrafter

> **`LIVE`** — the standing brief for the oversight chat. **Must be true today, and is
> citable as current truth.** Supersede at **v11** when `3o` closes. *(The streak: v5–v9
> each held their stated expiry. **The repo file `primer/CHAT_MONITORING_PRIMER.md` is
> versionless and updated in place; the version lives in the title line only. Never
> commit a `_v10` sibling** — a versioned copy beside the live file is how v2–v4 each
> stayed marked `LIVE` after expiring.)*

**Paste this at the start of a fresh monitoring chat.** Supersedes v1–v9. Written
2026-08-08 (evening), at the end of the session that audited `3n` — the audit is
`AUDIT_3N_ADVERSARIAL.md` (written to the project; ⚠ **commit it to `primer/` at `3o`
pre-flight**, census moves — along with this file's in-place update,
`SESSION_3O_PRIMER.md`, and `ADDON_SPEC_ace_session_capture.md`; the oversight chat has
already written all four into the local repo's working tree via the device bridge,
**uncommitted**).

This chat's job is **oversight and verification** — Claude Code writes the code
locally. If this chat writes the code, nobody is left to audit it.

---

## First action, every time

Clone and read the tree. Do not work from prose, this file included.

```bash
git clone --depth 80 https://github.com/Yshaana/AscensionCrafter.git repo
```

Then `primer/PROGRESS.md`'s top block. **If a claim isn't in the tree, it isn't
confirmed.** Rebuild the database so the full sim harness runs rather than refusing:
`python3 cli/rebuild.py` (21 steps, ~2 min, needs only committed source). The owner may
connect the local repo via `device_list_dir` / `device_stage_files` /
`device_commit_files` — file read/write, **no shell**. Use it for documents only; never
write code through it.

---

## What this project is (one paragraph)

A theorycrafting toolkit for **Project Ascension** — a classless WoW private server
(3.3.5 client, realm **Darkmoon**, Season 10). Five layers: a provenance-enforced
spell/mechanics database, a crawled + live-captured builds repo, a ported-SimC damage
simulator, a "lego box" of build components, and a theorycrafter. Built in phases by
Claude Code locally; the owner plays the game and is the tier-1 evidence source.

---

## Where things stand, 2026-08-08 evening (post-`3n`, post-audit)

**Session map:** … → `3l`✅ → `3m`✅ (deadline met + first gate move DOWN) → `3n`✅
(APL clock fix in two legs + E2's blocker replaced + two vacuous drafts caught) →
**`3o` (delivery modelling, the one-button capture addon, `3n`'s last-mile repairs —
work order `primer/SESSION_3O_PRIMER.md`)** → re-read Phase 3 exit honestly → Phase 4.

**The gate:** `0 of 35 within ±20% · 0 qualified` at every `3n` commit; slice
**30.040% → 30.150% (n=24)** — published **+0.11 pp** = same-member **+0.11 pp**,
membership unchanged. Producing median at close **0.2571 (n=123)**; ⚠ **endpoint
discipline (AUDIT_3N F3):** the equal pair **−0.0562 / −0.0562** spans **leg 1 → leg 2**
(0.3133 → 0.2571, 4 auto rows dropped, same-member verified over the 123); the
baseline→close move (0.3234 → 0.2571) is **−0.0663** and its first segment (leg 1,
0.3234 → 0.3133) is **composition by design** — 11 starved rows entered below the
median, the purest P4b instance yet ("fixing the clock made an existing error
countable"). Absent **59.0%**. Admissible-only **27.62% (n=21)** — recomputed by the
audit from the final manifest; **no committed emitter until `3o` pre-flight** (the
closing table's 27.4 was stale). 3 of the frozen 41 not admissible (Nodding 52 s,
Boomcat 0.24, Deyindra 0.22). Holdout: carried, unspent, pre-E15, not like-for-like.
Phase 3 exit: **2 of 7 criteria met**, unchanged.

**`3n` under audit — the strongest modelling session of the arc:** every committed
number reproduced to the digit (slice and producing recomputed from the artifacts' own
arrays; all of P1/P2/P7/P9 verified per-member; P8's falsification on Meritania real,
diagnosed, not rescued). Both mutations (M70/M71) red/green as registered. All 11
next-swing ids re-derived (`Attributes & 0x4`), with the sibling field agreeing:
`start_recovery_time = 0` on all 11 — the client itself says they cost no GCD. The
2026-08-08 capture reproduced from the bytes with an independent parser to the last
digit (LBC n=143, non-crit 523.8, ×1.141 vs base 459.05; imbue 3-step +80 AP / +172
Holy SP / +86 BH per weapon, linear, school-scoped). The E2 pairing tool's verdicts
reproduce (Gehennas sole admissible of 4; Garr refused on a five-stat bracket
disagreement). Prereg parenthood held; two vacuous check drafts were caught by running
the mutation — the label lesson (*"a string describing what the code MEANT is not
evidence of what it DID"*) is the best new rule since the mutation table.

**What the audit found — `3o`'s repair list (AUDIT_3N §1):**

1. 🚨 **F1 — the retired "+88 AP per imbue" still EXECUTES in the gate pipeline**:
   `core/sim/buffs.py:81` `attack_power=88.0`, reached via `group_buffs.derive_buffs`
   → `calibrate_crawled.py:1042` for any cohort member holding card 200809. The
   retirement commit said "and its blast radius" and updated both seeds — prose
   siblings are found reliably now; **code constants are the siblings still slipping
   through.** Gate-capable → `3o` Block C with its own prereg, NOT pre-flight.
2. 🚨 **F2 — `improved_cleave_lc_share_remeasure` (seed_epistemics) still cites the
   doubly-retracted `(9+AP)×2.2` as "the corrected formula"**, in an OPEN question, in
   a file the pre-flight edited 75 lines down.
3. ⚠ **F3 — the producing-median headline mispairs its endpoints** (see the gate
   paragraph above).
4. ⚠ **F4 — admissible-only 27.4 stale (true 27.62) and no tool emits it.**
5. ⚠ **F5 — Block B's sharing rules are mutation-blind**: the audit deleted the
   shared-budget decrement and made leg 2 reduce the off-hand — **both stayed green**,
   because every fixture holds exactly one next-swing ability. Robottikyrpa (3),
   Meritania/Deyindra/Nodding (2 each) sim through unprotected code.
6. ⚠ **F6 — "starved allocations 105 → 94" has no committed emitter** (committed
   counts: 37→27 keyed-at-zero, 28→22 per-key starved).
7. ⚠ **F7 — `pair_parses_to_stats.py` hardcodes the crash gap at whole seconds**:
   emits Gehennas logged 319.8 where the bytes give ~320.0 (`3m` published 320.1).
   The denominator instrument for every future coefficient, biased in the
   DPS-inflating direction. Fix: derive gaps from the logs' own ms stamps.

**The audit's tone note, worth carrying:** the recurring seam has narrowed to the
**last mile of blast radius, specifically its non-prose sites**. The mechanical rule
that catches it: *when a fact is corrected, grep the tree for the VALUE — `88`,
`(9+AP)`, `1.21` — not for the sentence.* And the close-out's prose drifted looser
than the artifacts under it (F3/F4/F6) — the instruments are honest; quote them at
their own endpoints and let them own every number.

**Key documents, reading order:**

| File | What |
|---|---|
| `primer/PROGRESS.md` | live state — top block first; ⚠ carries F3's mispaired pair and F4's stale 27.4 until `3o` pre-flight |
| `AUDIT_3N_ADVERSARIAL.md` | current audit; §5 is `3o`'s list; ⚠ commit to `primer/` at pre-flight |
| `primer/SESSION_3O_PRIMER.md` | `3o`'s work order |
| `primer/ADDON_SPEC_ace_session_capture.md` | the one-button capture spec (owner decisions stamped: auto-toggle logging; start+end snapshots only; build early in `3o`) |
| `primer/Session_2026-08-08_3n_clocks.md` | what `3n` did; §5 = the label lesson; §8 = honest not-done |
| `predictions/gate_manifest_3e.json` | current numbers (`LIVE`, clean tree, generated at `1fba7f5`, committed `6f1fc7c`) |
| `predictions/prereg_3n_b_apl_clocks.md` | the scored two-leg prereg — ground truth for any `3n` tally (9 predictions: 8✓ 1✗) |
| `predictions/CALIBRATION_TOLERANCE.md` | both generated blocks verified byte-equal to `render_band_table.py` output |
| `primer/ENGINE_BUGS.md` | defect registry — M1..M71 contiguous, parser-enforced; M72+ are `3o`'s |

---

## The open threads, in priority order

**0. Pre-flight doc/seed repairs** (F2, F3, F4, F6, the Devour Mind sentence — F1 is
NOT pre-flight, it is gate-capable) — minutes of work, stops `3o` inheriting
disproven facts. Cycle docs land here too; census moves.

**1. 🚨 DELIVERY MODELLING** — the load-bearing problem, absent **59.0%**. Open with
the client-stated formulas: imbue per-hit (effect 0, divisors 77/25, rank via
`snapshot_gear.enchant_id`) plus the **+73 AP per weapon** grant (Block C's corrected
constant is the prerequisite); then seal per-proc 20424 (~0.25/melee event, autos AND
abilities). **Devour Mind 287865: registered, step (1) answered — no trigger edge
reaches it; find the pressing card.** The 88-vs-80 delta and the weapon-damage sheet
anomaly stay named findings, never fitted.

**2. The one-button capture** (`/ace start` … `/ace stop`) — the E2 unblock: every
pull self-brackets with stat snapshots at combat start/end, logging auto-toggled,
one paste at session end. Spec is final; `3o` Block B; owner smoke-tests on a dummy.

**3. Fixture protection for the clock fix** (F5) — one dual-wield fixture with two
next-swing abilities, M73/M74. Cheap; protects `3n`'s headline before Block E builds
on it.

**4. The three unscored measurements** — the ×1.141 LBC residual (compute the talent
layer for the exact 2026-08-08 board), the 88-vs-80 imbue delta (ask the owner what
changed between boards), the +15.4×speed sheet anomaly (recorded, underived).

**5. The Monday split (E1)** — fix ships 2026-08-10. Owner holds IC **0/3**: his
captures cannot be contaminated; his post-Monday control capture should show **no
change**. The split bites only card-holding cohort members' post-Monday parses —
E1 (date-aware impairment) must land before any such parse is compared to anything
pre-fix, and that first parse doubles as the fix-shipped detector. The daily crawler
pulls post-Monday parses on its own schedule either way.

**6. Standing:** holdout unspent; predicate 2 UNARMED; `--with-dbc` staleness clock
`2026-08-08T00:48:58`; `verify_scraped_coefficients`' third slot convention, named by
arm.

---

## Corrections worth carrying — do not let these creep back

- ❌ **"+88 AP per imbue" / "the ×1.21 residual"** — retired. The 2026-08-08 three-step
  capture reads **+80 per weapon, linear** = raw 73 × **1.096** (one Deadliness-shaped
  multiplier). The SP half (+86 raw / +172 doubled) reproduces EXACTLY across both
  captures; only the AP half moved, and the 88-vs-80 delta is the successor question.
  ⚠ **`core/sim/buffs.py:81` still executes 88.0 until `3o` Block C lands.**
- ❌ **"the producing move is accuracy, endpoint-free"** — the equal −0.0562 pair is
  **leg 1 → leg 2 only**; baseline→close is −0.0663 with a composition first segment
  (deliberate, P4b). Quote deltas at the endpoints they span.
- ❌ **"admissible-only slice 27.4"** — stale at `3n` close; the final manifest gives
  **27.62 (n=21)**, and no tool emits the statistic yet.
- ❌ **"105 → 94 starved allocations"** — no committed derivation exists; the
  committed counts are 37→27 (keyed-at-zero) and 28→22 (per-key starved).
- ⚠ **"Gehennas logged 319.8 s"** — the pairing tool's hand-typed whole-second gap;
  the bytes give ~320.0 (`3m` published 320.1). Fixed when F7 lands; quote the
  regenerated value after.
- ❌ **"aura 344 is the per-hit damage parameter"** — flat attack power (+73/weapon at
  rank 6); per-hit is effect 0, divisors 77/25, stated by the client.
- ❌ **"Improved Cleave multiplies the whole ability"** — pre-2026-08-10 delivered
  behaviour only, declared a bug; the model is INTENDED (bonus-term-only, 74.4/hit at
  3/3 on the owner's weapon). ❌ **"LC's bonus is 9 + AP"** — flat 62, no AP term.
- ❌ **"the owner is affected by Monday's fix"** — he holds IC **0/3**; the patch
  changes his damage by exactly zero and the fix detector must come from card-holding
  cohort members' parses.
- ❌ **"13 of 15 predictions"** (3m) — 20: 17✓/2✗/1 split; per-block from the scored
  tables. `3n` was **9: 8✓/1✗** the same way.
- ❌ **"one pull, never two encounters"** — window on GUID (Garr 4 GUIDs, naive
  name-windows inflate 5.6×).
- Still true and load-bearing: the gate fails CLOSED; `entry_id` ≠ `spells.id`; the
  catalog's wrong-rank problem; "coverage = has a key for, not produces damage for";
  the holdout is pre-E15 and not comparable; no coefficient fitted to the parse it
  must later check; cite the `[arms]` line, never a remembered number (87 clean at
  `3n` close — but always re-run).

---

## How to review a session (the loop that works)

1. Clone fresh; rebuild the db. `PROGRESS.md`, the session's record, its work order.
2. **Spot-check claims against committed files, not prose.**
3. **Run the harnesses** (`check_refusals.py` — cite its `[arms]` line, clean tree;
   `check_sim_engine.py`; `check_core_purity.py`).
4. **Check `LIVE` documents both directions, and against their own expiry conditions.**
5. **Recompute every headline over FIXED membership from the artifacts' own arrays** —
   verify the instrument against your own recompute, and 🆕 **check every quoted delta
   spans the same two runs as the medians beside it** (`3n` F3 — the instrument was
   honest, the prose re-paired its numbers).
6. Confirm 🛑 stop-points were asked; **check prereg PARENTHOOD**
   (`git log --format='%H %p %s'`). A two-leg prereg: state the ancestry shape up
   front, don't call ancestry "parenthood".
7. **Re-run the session's registered mutations** — red, reverted green, tree clean.
8. **Mutate what the session did NOT register** — and 🆕 **probe fixture blind spots
   deliberately**: a rule about N-of-a-kind interactions (sharing, ordering,
   exclusivity) is untestable on fixtures holding one of the kind; count instances
   before trusting an arm (`3n` F5 — two green mutants on the headline mechanism).
9. **Re-derive hard-rule-adjacent constants from the committed extract — and read the
   sibling fields in the same rows** (the `start_recovery_time = 0` corroboration came
   free).
10. **Re-measure capture-derived claims from the bytes** with an independent parser —
    including stat exports, not just combat logs. Check hand-typed constants in tools
    against the bytes they claim to state (`3n` F7).
11. **Trace every correction's blast radius by VALUE**: grep the tree for the retired
    magnitude itself (`88`, `1.21`, `9+AP`) across code, seeds, docs. Prose siblings
    get found; **code constants are the ones that slip** (`3n` F1).
12. **Recount every hand-typed tally against a committed derivation** — including
    "unchanged" claims for statistics that moved (`3n` F4) and counts no artifact
    produces (`3n` F6).
13. **A named mutation that does NOT go red is a result** — and a falsified prediction
    diagnosed to its true cause is worth more than a confirmed one.

**Tone:** falsifiable checking, not cheerleading. `3n` earned the fattest §0 table of
the arc — say so first, then hold `3o` to the sharpened rule: *grep for the value, not
the sentence, and let the tools own every number the close-out speaks.*

---

## Standing owner actions (not session tasks)

- **Daily:** crawler at logon (Task Scheduler). **Read the changelog by hand every
  session** — `bugfix_watch_sweep` only sees our own submitted bugs.
- **Monday 2026-08-10:** the Improved Cleave fix ships. Your damage: unchanged (IC
  0/3). Your optional control capture should show no change. The detector is a
  post-Monday parse of Blix/Lootgoblin/Robottikyrpa/Nodding — E1 lands before any
  comparison.
- **Until the addon lands:** stat export immediately before AND after each pull (two
  stat levels = a slope). **After `3o` Block B:** `/ace start` on zone-in, `/ace stop`
  at the end, paste the one blob; `/ace snap` after re-imbuing between pulls. Dummy
  smoke test first.
- **Occasional, overnight, manual:** `catchup_crawler.bat`.
- **Per client patch:** `run_dbc_extract.bat`. Last successful run is the clock —
  `2026-08-08T00:48:58`.

## Reproducibility limit (standing)

Tier-2 captures gitignored; no `.db` committed. Corpus figures (the 12-of-35 exposure
census, Blix's per-cast means, leg 1's "11 added rows at 0.2061" — the baseline
artifact predates the per-row instrument) are unverifiable from a clone — verify
function behaviour with fixtures, manifest-internal arithmetic, commit parenthood,
and mutation re-runs instead. **The committed DBC extract and the capture bytes
remain the strongest ground the oversight chat has** — every `3n` capture figure and
every DBC constant reproduced from them exactly; prefer them over manifest arithmetic
when a claim can be reached either way.
