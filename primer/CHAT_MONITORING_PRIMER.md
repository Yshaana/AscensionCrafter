# CHAT MONITORING PRIMER v9 — AscensionCrafter

> **`LIVE`** — the standing brief for the oversight chat. **Must be true today, and is
> citable as current truth.** Supersede at **v10** when `3n` closes. *(The streak: v5–v8
> each held their stated expiry, with v7's one-morning lapse on record. **The repo file
> `primer/CHAT_MONITORING_PRIMER.md` is versionless and updated in place; the version
> lives in the title line only. Never commit a `_v9` sibling** — a versioned copy beside
> the live file is how v2–v4 each stayed marked `LIVE` after expiring.)*

**Paste this at the start of a fresh monitoring chat.** Supersedes v1–v8. Written
2026-08-08 (afternoon), at the end of the session that audited `3m` — the audit is
`AUDIT_3M_ADVERSARIAL.md` (written to the project; ⚠ **commit it to `primer/` at `3n`
pre-flight**, census moves).

This chat's job is **oversight and verification** — Claude Code writes the code
locally. If this chat writes the code, nobody is left to audit it.

---

## First action, every time

Clone and read the tree. Do not work from prose, this file included.

```bash
git clone --depth 80 https://github.com/Yshaana/AscensionCrafter.git repo
```

Then `primer/PROGRESS.md`'s top block. **If a claim isn't in the tree, it isn't
confirmed.** 🆕 Rebuild the database so the full sim harness runs rather than refusing:
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

## Where things stand, 2026-08-08 afternoon (post-`3m`, post-audit)

**Session map:** … → `3k`✅ (flip + coverage) → `3l`✅ (Block C + tuning) → `3m`✅
(deadline met + four repairs + first gate move DOWN) → **`3n` (APL clock fix, E2's
coefficients, delivery's opening — work order `primer/SESSION_3N_PRIMER.md`)** →
re-read Phase 3 exit honestly → Phase 4.

**The gate:** `0 of 35 within ±20% · 0 qualified` at every `3m` commit; slice
**30.426% → 30.040% (n=24)** — published **−0.385 pp** AND same-member **−0.385 pp**
over an unchanged membership, and **that equality is the evidence the move is accuracy,
not composition** (the manifest's `slice_delta_vs_previous_run` block now reports it
automatically). Absent **58.8%**; producing median **0.3234 (n=117)**; admissible-only
**27.4% (n=21)**. 3 of the frozen 41 not admissible (Nodding 52 s, Boomcat 0.24,
Deyindra 0.22). Holdout: carried, unspent, pre-E15, not like-for-like. Phase 3 exit:
**2 of 7 criteria met**.

**`3m` under audit — and it is the cleanest session of the arc:** every number checked
reproduced to the digit (gate recomputed from the manifests' own cohort arrays; all
Block D windows re-measured from the capture bytes with an independent parser; B5's
owner-facing arithmetic exact; five DBC constants re-derived). **Eight mutations
re-applied and re-run — all red, all reverted green**, including M60's isolating
property (the old source-text arm demonstrably prints `PASS (vacuous)` where the
repaired arm fails). Both falsifications (B P3/P5) reported, diagnosed to ONE mechanism
(the APL units mismatch), and the fix **correctly not** smuggled into the results
commit. The four `AUDIT_3L` soft arms are genuinely hardened. Prereg parenthood exact
on all three pairs. The Monday deadline was met before the patch.

**What the audit found — `3n`'s pre-flight block (AUDIT_3M §1):**

1. 🚨 **F1 — `seed_epistemics.py:181` still asserts the falsified aura-344 mechanic**
   ("the per-hit damage parameter") — the exact line `AUDIT_3L` F5 named. C3 corrected
   `seed_confirmed.py:361` only; the two seed files now disagree, and every rebuild
   loads the stale text into `open_questions`.
2. 🚨 **F2 — the `2b` seed `improved_cleave_modifies_all_effects_not_just_the_flat`
   still states ALL_EFFECTS as DECISIVE current truth** (~1,033/hit), contradicting the
   corrected seed in the same file. Annotate as pre-2026-08-10 **delivered** behaviour,
   don't delete — it is historically right. The Frostbound Cleave seed also still cites
   the retracted `(9+AP)*2.2`.
3. ⚠ **F3 — "13 of 15 predictions confirmed" is a hand tally no artifact reproduces.**
   Direct count over the scored prereg tables: **20 predictions — 17✓ / 2✗ / 1 split**
   (B 4✓·2✗·1 split, C 7/7, D 6/6). It reproduces only by dropping the five
   "gate-does-not-move" predictions AND counting the half-falsified P6 as confirmed —
   the flattering resolution, unstated. Same class: "58.83%" absent share has no
   committed emitter (the artifact says 58.8). Quote per-block counts from the tables.
4. ⚠ **F4 — ENGINE_BUGS registers M63 at a site that does not exist**
   (`core/sim/tiers.py`; `WEAPON_SLOTS` lives in `tools/audit/calibrate_crawled.py:207`).
   The mutation is real and red at the real site; the registry row sends a future
   session to a no-op green.

**The audit's tone note, worth carrying:** `3m` broke `3l`'s pattern where it mattered
(instruments, mutations, no rescues) — what it did not do is finish its own
corrections' **blast radius**. Each repair updated the primary site and left a sibling:
the second seed file, the seed twenty entries down, the registry row's path, the tally
in the close-out prose. *When a fact is corrected, grep for its siblings before the
commit.*

**Key documents, reading order:**

| File | What |
|---|---|
| `primer/PROGRESS.md` | live state — top block first; ⚠ its "13 of 15" and "58.83%" need the F3 correction |
| `AUDIT_3M_ADVERSARIAL.md` | current audit; §5 is `3n`'s list; ⚠ commit to `primer/` at pre-flight |
| `primer/SESSION_3N_PRIMER.md` | `3n`'s work order |
| `primer/Session_2026-08-08_3m_repair.md` | what `3m` did; §9 = the APL mechanism; §8 = honest not-done |
| `predictions/gate_manifest_3e.json` | current numbers (`LIVE`, clean tree, git `ce50207`, committed `44ea940`) — now carries `slice_delta_vs_previous_run` and `not_scoreable_by_reason` |
| `predictions/prereg_3m_{b,c,d}_*.md` | the three scored preregs — the ground truth for any tally |
| `predictions/CALIBRATION_TOLERANCE.md` | ✅ de-numbered: derived prose now points at a generated, asserted block (M57 guards it) |
| `primer/ENGINE_BUGS.md` | defect registry — M1..M69 contiguous, parser-enforced; ⚠ M63's site column is wrong (F4) |

---

## The open threads, in priority order

**0. Pre-flight doc/seed repairs** (F1–F4 above) — minutes of work, cannot move the
gate, and stop `3n` inheriting disproven facts.

**1. 🚨 THE APL CLOCK FIX** — the largest measured modelling error left. `apl_gen`
ranks fillers by damage per CAST across abilities on different clocks:
`is_next_swing = 1` abilities (Cleave family, Heroic Strike, Light Maul, Shadow
Slash) are swing-timer-limited, ordinary fillers GCD-limited. Blix's Lightbound
Cleave left the rotation entirely (−100% vs predicted −39.84%), costing 18% of his
sim; **15 of 41 members exposed**. ⚠ `3m`'s first diagnosis (per-cast vs
per-GCD-second) was WRONG — 0 disagreements cohort-wide, because `_gcd_for` is
per-character. Own prereg; direction NOT known in advance; mutation = restore
per-cast ranking.

**2. E2 — `infer_coefficient` on the six Elric MC stat blocks.** THIRD carry; lands
or gets a fresh owner stamp. The windowing is done and verified from the bytes
(`core/logs/encounters.py`: kill GUID explicit, no-kill and multi-kill REFUSE, wall
379.8 vs logged 320.1 on Gehennas). 🛑 Divide by **logged** seconds. Unblocks Phase 3
criteria 3-full and 4.

**3. Delivery modelling** — the load-bearing problem, absent **58.8%**. Open with the
client-stated formulas: imbue per-hit (effect 0, divisors 77/25, rank via
`snapshot_gear.enchant_id`) plus the **+73 AP per weapon** grant (seeded `3m` C3,
unmodelled; ×1.21 residual named, not fitted); then seal per-proc 20424. Behind
those: Plague Swarm 276445 (146×), school-variant autos, Deep Wounds/Ignite/diseases.
**Devour Mind 287865 is at its FOURTH deferral — register or model, no bare carry.**

**4. The Monday split, date-aware (E1).** From **2026-08-10** the server fixes
Improved Cleave; the frozen cohort stays pre-fix (owner decision). No post-Monday
capture of a hybrid-Cleave character is comparable to anything pre-fix until the
date-aware impairment lands. The first post-fix capture doubles as the free detector
that the fix shipped as stated.

**5. Standing:** holdout unspent; predicate 2 UNARMED; one owner-gated `--with-dbc`
run remains the staleness clock (last successful `2026-08-08T00:48:58`);
`verify_scraped_coefficients.py`'s third slot convention is named by a check arm,
deliberately not aligned.

---

## Corrections worth carrying — do not let these creep back

- ❌ **"aura 344 is the per-hit speed-scaled damage parameter"** — it is flat attack
  power (+73/weapon at rank 6); the per-hit term is effect 0, divisors 77/25,
  *stated by the client*. ⚠ `seed_epistemics.py:181` still says otherwise until `3n`
  pre-flight lands.
- ❌ **"Improved Cleave multiplies the whole ability"** — true only of pre-2026-08-10
  delivered behaviour, declared a bug by the server. The model is INTENDED
  (bonus-term-only, scoped by card id, NOT generalised to op 8). The card adds
  **74.4/hit at 3/3** on the owner's weapon, not 578.1.
- ❌ **"Lightbound Cleave's bonus is 9 + AP"** — the 9 was Rank 1 and the AP term was
  `EffectBonusCoefficient = 1.0` read as a coefficient; its neutral value IS 1.0.
  The decode is a **flat 62**, no AP term.
- ❌ **"13 of 15 predictions confirmed"** — 20 predictions, 17✓/2✗/1 split by direct
  count; quote per-block from the scored tables.
- ❌ **"3m ranked fillers per-GCD-second wrongly"** — that diagnosis was falsified
  (0 disagreements). The defect is the CLOCK mismatch: per-cast ranking across
  swing-timer vs GCD abilities.
- ❌ **"one pull, never two encounters"** — Gehennas 2 GUIDs, Magmadar 2, **Garr 4**,
  Geddon 3 (no kill). Window on GUID; naive name-windows inflate Garr **5.6×**
  (2,138.6 s vs 382.6 s).
- ⚠ **"the audit said normalise the canary by active phases"** — superseded by
  measurement: population collapse (MC returned rows for 2 of 200 queries) is
  invisible to every structural denominator. The carry-over test is the standing fix.
- ❌ **"slice 26.3% → 30.4% was a 4-point accuracy gain"** — composition; same-member
  it was −0.21 pp. The `3m` move (−0.385 = −0.385) is what a real accuracy move looks
  like. Quote the pair, always.
- Still true and load-bearing: the gate fails CLOSED; `entry_id` ≠ `spells.id`; the
  catalog's wrong-rank problem (and RV's own constants were its latest victim);
  "coverage = has a key for, not produces damage for"; the holdout is pre-E15 and not
  comparable; no coefficient fitted to the parse it must later check; the arm count
  is **dirty-tree-dependent — cite the clean-tree figure** (87 at `3m` close, but
  always cite the `[arms]` line, never a remembered number).

---

## How to review a session (the loop that works)

1. Clone fresh; rebuild the db so the sim harness runs. `PROGRESS.md`, the session's
   record, the work order it ran.
2. **Spot-check claims against committed files, not prose.**
3. **Run the harnesses** (`check_refusals.py` — cite its own `[arms]` line, clean
   tree; `check_sim_engine.py`; `check_core_purity.py`).
4. **Check `LIVE` documents both directions, against post-close commits, and against
   their own expiry conditions.** Where an asserted block changed, check the prose
   around it was regenerated — or better, de-numbered.
5. **Trace headline numbers from the artifact up, and recompute the headline
   statistic over FIXED membership** from each manifest's own `cohort` array. The
   instrument reports it now — verify the instrument against your own recompute.
6. Confirm 🛑 stop-points were asked; **check prereg PARENTHOOD**
   (`git log --format='%H %p %s'`).
7. **Re-run the session's registered mutations yourself** — red, then reverted green,
   tree clean after. 🆕 **If a registered site doesn't exist, that is a finding (F4):
   find the real site and run it there** — a no-op green is worse than no mutation.
8. **Mutate what the session did NOT register**, and probe new arms for vacuity
   (comment-satisfiable? fixture-blind? AST-structural arms are the acceptable form).
9. **Re-derive hard-rule-adjacent constants from the committed extract** — and read
   the sibling fields in the same rows.
10. **Re-measure capture-derived claims from the bytes** with an independent parser.
11. 🆕 **Trace every correction's blast radius**: grep the tree for the corrected
    fact's siblings — both seed files, related seeds, registry rows, prose. `3m`'s
    two 🚨 findings were both unfinished blast radius, and `AUDIT_3L` F5 had already
    named one of the sites.
12. 🆕 **Recount every hand-typed tally** in the record and PROGRESS against the
    scored tables. A count that needs an unstated counting rule is a finding.
13. **A named mutation that does NOT go red is a result, not an embarrassment** — and
    a falsified prediction diagnosed to its true cause is worth more than a confirmed
    one.

**Tone:** falsifiable checking, not cheerleading. `3m` earned its §0 table — say so
first, and hold the next session to the blast-radius rule, which is narrower and
cheaper than "be careful": *the missing half was already named in a document the
session had open.*

---

## Standing owner actions (not session tasks)

- **Daily:** crawler at logon (Task Scheduler). ✅ **The canary is satisfiable again**
  (`3m` pre-flight, carry-over test) — auto-commits should resume; hand-commits are no
  longer needed. If it fails now, the failure text names carried-over boards — that is
  a real signal, investigate rather than override. 🆕 **Read the changelog by hand
  every session** — `bugfix_watch_sweep` only sees our own submitted bugs; the
  Improved Cleave patch (a fix to a model we were *right* about) was invisible to it.
- **Monday 2026-08-10:** the Improved Cleave fix ships. First post-fix capture is the
  free detector — but E1 (date-aware impairment) must land before that capture is
  compared to anything.
- **Improved Cleave is resettable at Gabril Mewell** — the toolkit's verdict: at 3/3
  it adds 74.4/hit on The Light's Hope (was 578.1); no longer a top-tier slot.
- **Occasional, overnight, manual:** `catchup_crawler.bat`.
- **Per client patch:** `run_dbc_extract.bat`. Last *successful* run is the clock —
  `2026-08-08T00:48:58`, `SpellItemEnchantment.dbc` in scope.
- **Stat-export addon** — byte-identical at `v2026-08-06c`; its per-parse stats feed
  E2 this session.

## Reproducibility limit (standing)

Tier-2 captures gitignored; no `.db` committed. Corpus figures (C2's 1,416/1,852 and
0.2004; the APL's 15-of-41; the RV holder census) are unverifiable from a clone —
verify function behaviour with fixtures, manifest-internal arithmetic, commit
parenthood, and mutation re-runs instead. **The committed DBC extract and the capture
bytes remain the strongest ground the oversight chat has** — every `3m` D-block figure
reproduced from the bytes exactly; prefer them over manifest arithmetic when a claim
can be reached either way.
