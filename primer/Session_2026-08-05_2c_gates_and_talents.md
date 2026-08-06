# Session 2c — Calibration gates, talent modelling, Phase 2 close-out

> **`HISTORICAL`** — the record of a past session or a completed phase. Immutable. It **may contain claims that are false today**, and that is correct rather than a defect — it records what was believed at the time. **Never citable as current truth.** *(Classified `3f` F8c, 2026-08-07.)*

**Date:** 2026-08-05 · **Scope:** the `2c` addendum's gates G0–G4, then PHASE_2
T4b, T8, T9, T10, T11 · **Status:** ✅ complete — **Phase 2 is done**, with one
exit criterion deliberately moved to 3a.

The session's shape is worth stating up front, because it is not the shape that
was planned. The gates were meant to be quick checks before the real work of
talent modelling. **Four of the five overturned something `2b` believed**, three
of those turned out to be errors in *our own tooling* rather than in the game
data, and the largest single result of the session — the rotation conclusion
flipping back — came out of a gate rather than out of the sim work.

---

## 1. G4 — Holy Shock, and a scoping hole nobody had reached

`2b` left this as the first item for `2c`: Holy Shock's level-60 rank (20930) is
a bare `SPELL_EFFECT_DUMMY`, and a rank sibling inherits no `hidden_refs`,
because that column is parsed from the export and a sibling is by definition
absent from the export. So Holy Shock simmed as **0 damage against 36 real
casts averaging 1,380**.

The fix needed **two** halves, and only the first was anticipated:

1. **Serving.** `sibling_hidden_refs()` parses the sibling's own
   `spell_dbc_raw.description` for `$<id>` tokens, exactly as `build_index`
   parses export tooltips. R1 points at 25912/25914; **R4 points at
   25902/25903** — different sub-spells, which is why reusing the catalog
   entry's refs would not have worked.
2. **Scope — the half that was invisible.** Those ids had never been extracted
   from the client at all. `build_dbc_index.py` scoped `spell_dbc_raw` to
   catalog ids + **export** hidden_refs + neighbours + siblings, so a *sibling's
   own* refs were never in scope. This needed a `--with-dbc` re-extraction:
   **+797 ids**, 15,769 → 16,566 rows.

**Holy Shock R4 = 562–608 Holy damage** (+ 676–732 healing), now a permanent
`VALIDATION` anchor in `resolve_numeric_formulas.py` so a future re-scoping
fails loudly instead of silently reverting.

> 🛑 **This reads a POINTER out of a description string, never a magnitude.** The
> Titanic Mutilate rule bans trusting description *numbers*; a `$25902s1` token
> is a spell id, and the magnitude still comes from that spell's numeric fields.
> Worth stating because the code looks superficially like a rule violation.

**Scope of the residual, now measured:** 680 of 686 unambiguous siblings carry a
magnitude, and exactly **4** (Holy Shock, Wyvern Sting, Deep Freeze, Penance)
have one only through this path.

### 🚨 The consequence: build doc §11 is restored

`2b` reported `paladin_optimal` scoring **below** `paladin_observed` (602 vs
659) — inverting the build doc's central rotation conclusion — and correctly
refused to treat it as a result, because the optimal APL spends ~9 GCDs on an
ability the model scored at zero.

With Holy Shock resolving, **optimal 848 beats observed 823.** The `2b`
zero-damage guard was retargeted rather than deleted (it now runs against
Thorns, a genuinely unknown-magnitude damaging ability), and a second check
asserts the real comparison.

⚠ One trap found while retargeting: **Blades of Light looks like a zero-damage
ability and is not one.** Its own effect is zero but its trigger-reached
components resolve, so the ability-level guard correctly stays quiet. Testing
the guard against it would have produced a check that passes for the wrong
reason.

---

## 2. G3 — both calibration "outliers" were our own name matching

`2b` recorded two abilities that missed their school group and could not be
explained: **Consecration at 3.55×** and, separately, an Exorcism reading of
1.08× that looked like a genuine low outlier.

**They are the same bug, and it is one this project has a hard rule against.**
`calibrate_vs_log.py` resolved abilities by NAME. In Elric's logs:

| logged name | logged spell id | what the tool resolved |
|---|---|---|
| Consecration | **270768** — out of catalog, `spell_level` 0, its own per-level scaling | 26573, the catalog card |
| Exorcism | **270767** — likewise | 879 |

Both are **Purification By Light's own summoned versions** — different abilities
that share a name, which is exactly what *"never relate two spell IDs by name"*
exists to prevent. The rule had simply never been applied to our own tools.

**Fixed structurally rather than by adding overrides:** the log states the spell
id on every damage line, so the tool now keys on `spellId` and nothing is
matched at all. `ID_ROUTING` retains only the two ids that are not directly
castable and must resolve through their owner.

**Result — the Holy group is tight with no outlier:**

| | before (name-matched) | after (id-keyed) |
|---|---|---|
| Holy group | n=6, range **1.08–2.62** "WIDE" | **n=3, range 1.97–2.15** |

The same fix surfaced three more mismatches that had been invisible: Seal of
Command logs as **20424** (not 20375), Righteous Vengeance as **61840**, and
Consecrated Holy Weapon as **200818** — confirming INDEX_GUIDE v3's refusal to
assume it was the catalog's `Consecrated Weapon` (200809). These now report
honestly as "not resolvable by the sim" instead of being silently mis-resolved.

---

## 3. G1 — the 1.31 ratio is confounded, and is demoted

`2b`'s headline calibration quantity was the Holy ÷ Holystrike ratio, on the
reasoning that buff state multiplies both schools and cancels. **It does. But a
ratio cancels factors applied to both sides, not an input error applied to one.**

Measured composition, now a first-class column in the tool:

| | weapon share of the base |
|---|---|
| Whirling Light, Dawnreaver | **100%** |
| Lightbound Cleave, Dawn Strike | **86–87%** |
| every Holy ability | **0%** |

The sim's weapon input came from the older King Gordok parse, not the same
session as any log, so an error in it moves the Holystrike denominator alone and
passes into the ratio at ~1:1. It could not be un-confounded from the existing
logs: white-swing maxima vary **1.52×** across the four sessions (869 / 676 /
603 / 571), equally consistent with a changed weapon and with changed physical
multipliers.

### What replaces it, and why it is strictly better

**Weapon-free pair ratios.** A same-school pair cancels weapon damage only at
the extremes — both sides with no weapon term, or both pure weapon-percent with
no flat. Anything in between does not cancel, because a flat does not scale with
weapon damage. Same school cancels the school's talent stack too, leaving the
ratio of the two **base formulas**: a prediction with no fitted input at all.

| Pair | Predicted | Observed | Worst delta |
|---|---|---|---|
| Hammer from the Heavens ÷ Hour of Judgement tick | **1.718** | 1.697 / 1.773 / 1.685 / 1.771 | **3.2%**, 4 logs |
| Dawnreaver ÷ Whirling Light | **0.769** | 0.768 / 0.720 / 0.757 | **6.4%**, 3 logs |

⚠ **Free way to un-confound the absolute numbers:** a character-sheet screenshot
(weapon damage, AP, SP) at the start of the next logged session.

---

## 4. G2 — the type-121 theory is wrong twice over

`2b` suspected Dawn Strike's low ratio came from effect type 121 (normalized
weapon) being double-counted alongside type 31, and warned it would affect every
ability carrying 121.

**Scope check — the anchors do not carry it.** Lightbound Cleave `[58,31]`,
Whirling Light `[31,64]`, Dawnreaver `[31]`, at both the catalog and level-60
ids. Only Dawn Strike carries 121, at all twelve of its ranks. So the
1.87/1.87/1.88 agreement is **three independent confirmations, and `2b`'s
base-formula validation stands** rather than being downgraded.

**Mechanism check — there is no double count to remove.** The resolver puts 121
in `DAMAGE_EFFECTS` and it falls through to the flat branch, contributing
basepoints as a flat 68. Had it been counted as a swing, the base would be
~1,100 rather than 476 and the ratio ~0.5.

**So the question changes shape.** At the level-60 rank Dawn Strike resolves to
`68 + WEAPON*0.65` and Lightbound Cleave to `62 + WEAPON*0.65` — near-identical
formulas, bases 476 and 470 — yet the game pays Dawn Strike 528 where it pays
Lightbound Cleave 661. It is no longer *"why is our base too high"* but *"which
multiplier does Lightbound Cleave get that Dawn Strike does not"*, which makes
it T4b's question. Note the class tags do not settle it on their own: Dawn
Strike is Rogue-family, Lightbound Cleave and Whirling Light Warrior — but
Dawnreaver is Paladin-family and tracks the Warrior pair.

Catalog scope for whenever 121's semantics are settled: **161 cards carry it,
158 alongside type 31, 80 in the current pool.**

---

## 5. T4b — talent modelling

Built on **auras 107/108 + `EffectMiscValue` (SpellModOp) + `EffectSpellClassMask`
from numeric fields**, as `2b` specified after the Improved Cleave case.

⚠ **`EffectSpellClassMask` had to be added to the extract.** It was already
parsed by `build_dbc_index.py` and simply never written into `effect_json` —
the same shape as v9's hardcoded-column-list gap, and it hid the one field that
says *which* spells an amplifier reaches. No earlier session could have built
this.

**Card rank is a ROLL, not a level gate**, so `dbc_spell_rank`'s level rule is
the wrong lookup; the mapping is `dbc_character_advancement.spell_rank_<n>`.
Getting this wrong reads Rank 1 for a 5/5 card.

### The Improved Cleave case, closed from numeric fields alone

| ability | family | class mask | Improved Cleave 3/3 reaches it? |
|---|---|---|---|
| **Lightbound Cleave** | 4 | `[4194304,0,0]` | ✅ **×2.20** |
| Cleave, Fel Cleave | 4 | `[4194304,0,0]` | ✅ |
| Whirling Light | 4 | `[0,4,0]` | ❌ |
| Dawnreaver | 10 | `[0,32768,0]` | ❌ |
| Dawn Strike | 8 | `[8388610,0,0]` | ❌ |

Its mask is **byte-identical** to Lightbound Cleave's. v9's ranking and v12's
re-derivation were both right; this is the first time the card's reach has been
*proved* rather than argued, and it needed no tooltip.

### 🚨 Two of the "Holy multiplier stack" do not multiply damage

`Holy Power` and `Holy Specialization` are **aura 71 — +5% crit CHANCE with Holy
each**, not damage multipliers. The build doc describes the pair as part of a
stacked Holy multiplier chain; they are crit talents. `Holy Focus` is likewise
crit *damage* (+34%), not damage.

**The whole modelled damage layer is ×1.155** — Answered Prayers +10% all
schools, Twin Disciplines +5% Holy — against a logged ~2.1×.

### Unknown auras are named, never assumed inert

6 talents use auras outside stock 3.3.5 (231, 333, 122, 136) and 4 are
`SPELL_AURA_DUMMY` — a server-side script no numeric field states. Both sets are
listed by name in `warnings`. A talent silently contributing 1.0× is
indistinguishable from one read correctly and doing nothing, and that is a state
this project has been burned by often enough to refuse.

Sheet mode and talents are kept from double-counting explicitly: `stats_override`
means the sheet values are FINAL and already contain every talent's crit/AP/SP
contribution, so in that mode **only the damage multipliers apply**.

---

## 6. A bug this session introduced, and how it surfaced

Re-running `ingest/dbc/resolve_numeric_formulas.py` standalone — which its own
docstring invites, *"it owns the deletion of its own output, so re-running is a
replace"* — **deleted every trigger-attributed row** and zeroed Hammer from the
Heavens, the owner's top damage source.

`spell_effect_values` has two writers. `relationships.py` correctly scopes its
delete to `via LIKE 'trigger_hop%'`; this script ran an unscoped `DELETE FROM`.
The rebuild order hid it completely (numeric runs *before* relationships), so it
was only reachable via the standalone re-run.

**Same family as the three idempotency bugs Phase 0 found, inverted:** not a
script that fails to delete its own output, but one that deletes output it does
not own. Now scoped to `via IN ('self','hidden_ref')`, and the standalone re-run
is verified to leave the 727 trigger rows intact.

---

## 7. T8 — calibration, with the tolerance recorded first

`predictions/CALIBRATION_TOLERANCE.md`, stamped **before any 2c calibration
run**, because a tolerance chosen after seeing the deltas gates nothing.
Aggregate DPS **±20%**, per-ability **±25%** on the non-crit average — set from
the measured noise floor, not from ambition.

**Reported result: 1 of 7 abilities within tolerance.**

| ability | logged / modelled |
|---|---|
| Hour of Judgement | 1.87× |
| Hammer from the Heavens | 1.86× |
| Holy Supernova | 1.71× |
| Whirling Light | 1.38× |
| Lightbound Cleave | 1.37× |
| Dawnreaver | 1.34× |
| Dawn Strike | **1.06× ✅** |

The misses group by **school**, which is what an unmodelled school amplifier
*or* an unmodelled buff looks like — and buff state is known to move 1.41×
between these same sessions. 🛑 Not closed by fitting a constant.

**§8.2, resolved explicitly rather than at the exit gate:** the "≥3 real
characters" criterion **moves to Phase 3a**, because simulating a crawled
character needs gear and gear is Phase 3 T4's `items` table. `2c` calibrates one
character across five logs and four sessions instead — which tests the model
against session variation, something three single parses would not.

---

## 8. T9–T11

* **T9 prediction ledger** — `predictions` + `prediction_outcomes`,
  `core/sim/predictions.py`, seeded by `ingest/export/seed_predictions.py` (new
  rebuild step). `record_prediction` **refuses to overwrite an existing slug**:
  a changed prediction is a new row. The `2b` file is migrated with its
  **original** stamps (`sim_version=2b`, the 19-step rebuild, 602/674) — never
  re-derived, which would turn a post-hoc number into an apparently
  pre-registered one. `2c`'s own prediction (848) is logged before any parse
  that could test it. `reconcile()` reports **one-sided** per-ability bias only,
  because a large mean with mixed signs is variance, not bias.
* **T10 cache** — `core/sim/cache.py`. `data_version()` hashes **every** table
  the sim reads, not just `spell_mechanics`: this session alone changed
  `spell_effect_values`, `spell_dbc_raw` and the talent path, and a narrower key
  would have served `2b`'s answers for `2c`'s model, silently.
* **T11 diff/report** — `core/sim/diff.py` returns a **verdict before a winner**
  and refuses to rank two builds whose delta sits inside the combined
  uncertainty; `core/sim/report.py` is a pure formatter (dict / terminal / HTML)
  that renders warnings rather than summarising them away.

---

## 9. What the next session inherits

* 🛑 **Do not quote 1.31.** It is confounded (G1). The targets are the
  weapon-free pair ratios, 1.718 and 0.769.
* 🛑 **The ~1.86 Holy / ~1.37 Holystrike residual is NOT "more talents".** It is
  school-grouped, and buff state alone moves 1.41× between the owner's sessions.
  Model buffs, or fit per-log with buff state known.
* **The single cheapest thing available:** a character-sheet screenshot at the
  start of the next logged session. It un-confounds the absolute calibration
  *and* settles `elric_active_path_and_duality_ap_anomaly`.
* **Open and now better specified:** `dawn_strike_sim_base_is_systematically_too_high`
  (reframed as a talent question), `holy_shock_bonus_coefficient_0429` (the
  discriminator was run — "no SP term" is falsified, 0.429 is close but
  consistently ~5% too large; owner decision needed before seeding),
  `periodic_trigger_delivery_pulse_count` (unchanged).
* **Unmodelled auras 231, 333, 122, 136** are the concrete next win for talent
  coverage — 6 of the owner's own slotted talents sit behind them.
