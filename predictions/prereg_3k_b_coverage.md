# Pre-registration — `3k` Block B: the modelling MODE is coverage, and the first target is a key that was never wired

> **`FINDING 2026-08-07`** — committed BEFORE any `core/` edit and before the
> run it predicts. Every number under "Predictions" is UNMADE at the time of
> writing; `git log --format='%H %ci %s'` proves the order. True as of its
> date, not maintained.

## Mode: COVERAGE (not ratio tuning)

Registered per the work order's §0 rule 2, from
`predictions/per_ability_summary.json` as regenerated this session at
`git_sha 57e844fb`, clean tree, 35 characters / 652 ability rows:

| key state | share of cohort logged damage |
|---|---:|
| **absent** (no sim key at all) | **62.9%** |
| producing | 24.2% |
| starved:zero-casts | 12.9% |

Ratio tuning (producing median **0.2727**) is **out of scope for `3k`** —
owner decision 2026-08-07, restating the work order default: coverage results
decide `3l`'s shape, and one session doing both under one prereg muddies
attribution.

## The target distribution, from the committed artifact

Absent keys ranked by their share of **cohort** logged damage (total logged
`18,209,256`; absent mass `11,461,892`). Top 12, with the number of cohort
characters affected:

| # | spell_id | name | % of cohort logged | chars |
|---:|---:|---|---:|---:|
| 1 | 287865 | Devour Mind | 6.63% | 2 |
| 2 | **61840** | **Righteous Vengeance** | **3.32%** | **9** |
| 3 | 277181 | Burning Ground | 2.72% | 2 |
| 4 | 200818 | Consecrated Holy Weapon | 2.61% | 6 |
| 5 | 12721 | Deep Wounds | 2.07% | 8 |
| 6 | 10444 | Flametongue Attack | 2.04% | 2 |
| 7 | 280212 | Judgement of The Three Hammers | 1.50% | 3 |
| 8 | 20424 | Seal of Command | 1.47% | 4 |
| 9 | 272624 | Molten Earth | 1.37% | 1 |
| 10 | 907921 | Mystic Shot | 1.31% | 1 |
| 11 | 276075 | Fel Infused Attack | 1.31% | 3 |
| 12 | 288848 | Ebon Corruption | 1.31% | 1 |

🛑 **The registered shape of this distribution, which is itself a finding:
there is no big win.** The largest single absent key is 6.6% of cohort logged
damage and is held by **two** characters; the top 30 keys together cover only
**69.3%** of the absent mass, and 14 of those 30 affect exactly one character.
**Absent mass is not concentrated, it is shattered.** A session that expected
to halve 62.9% by keying a handful of abilities would be planning against a
distribution that does not exist.

🆕 **And the mass is dominated by TRIGGER-DELIVERED damage, which the APL
structurally cannot contain.** `generate_apl()` iterates `build_spec.abilities`
— the character's *cards*. Righteous Vengeance, Deep Wounds, Ignite, Frost
Fever, Blood Plague, Flametongue/Windfury/Fel Infused Attack, Seal of Command
and the pet firebolts are none of them cards; they are damage the engine
delivers off something else. That is why they are absent, and it is a
different problem from a missing coefficient.

## The one target `3k` builds, and why it is first

**#2, Righteous Vengeance (61840)** — the broadest single absent key
(**9 characters**, vs 2 for the largest by mass), and the only one in the top
12 that needs **no new game data at all**.

**It is already implemented and it has never once run.** `core/sim/tiers.py`
derives it as 30% of the rotation's own crit damage:

```python
for ev in rec.get("events") or ():
    if ev.get("crit_damage"):
        crit_damage += ev["crit_damage"] * rec["casts"]
```

**Nothing in the tree ever writes a `crit_damage` key.**
`ExpectedCastResult.per_event` dicts carry `event_key, kind, school,
source_spell_id, via, attributed, occurrences, mean_each, mean_total, p_land,
p_crit` — and no `crit_damage`. So the sum is always `0.0`, the
`if crit_damage > 0` branch never fires, and every character takes the
`"Righteous Vengeance NOT modelled"` path. Measured: **0 sim rows for 61840
across the whole cohort**, and the derivation's warning appears **0 times** in
`data/derived/calibration_crawled.md`.

The quantity is recoverable from fields the event already has, with no new
data: `mean = p_land · base · scale · (1 + p_crit(mult−1))`, so the damage
dealt *by crits* is `mean · p_crit·mult / (1 + p_crit(mult−1))`.

🚨 **The fix has a second half, and shipping the first half alone would be
actively wrong.** `_add_swing_sources` adds Righteous Vengeance to **any**
character with crit damage. It has been harmless only because the value was
always zero. Populate `crit_damage` on its own and all 35 cohort characters
gain a Righteous Vengeance row — **phantom production on the 26 who do not
hold the card**, which the work order names as being as bad as a missing key.
So the change is: **populate the key AND gate the derivation on card
ownership** (the talent card resolves to spell ids `53380` / `53381` /
`53382`). All 9 characters that log it hold it.

## Named refusals — targets NOT built, with the reason

Refusal over fabrication. Each is a real gap and none is a guess:

| spell_id | name | % / chars | refusal |
|---:|---|---|---|
| 200818 | Consecrated Holy Weapon | 2.61% / 6 | **Enchant-delivered; the damage is not in its own record.** Primer v31 §2: the client decodes a flat of `1` and db.ascension.gg independently states `Value: 1` — two independent sources agreeing on a nominal 1 *prove* the magnitude lives elsewhere. `SpellItemEnchantment.dbc` is unextracted, and no widening of the current scope reaches it. Unblocked by: an owner-gated `--with-dbc` run whose scope includes that DBC. |
| 20424 | Seal of Command | 1.47% / 4 | **No record in `spell_dbc_raw`** — reached by no extraction route. Already named in the sim's own seal note, which states the damage is MISSING rather than zero. Same unblock. |
| 287865 | Devour Mind | 6.63% / 2 | Not refused on data grounds — **deferred**. It is 2 characters, and `3k` is spending its coverage budget on breadth (9 characters) over mass. Named here so it is not silently dropped; it is `3l`'s largest single target. |

## Predictions

Measured after the change by re-running `per_ability_accuracy.py` and
`calibrate_crawled.py` against the same corpus. **None is measured at the time
this document is committed.** A falsified prediction is reported, not rescued.

| # | prediction | falsified by |
|---:|---|---|
| **P1** | The **absent** share of cohort logged damage falls from **62.9%** to between **59.0% and 60.0%** — Righteous Vengeance's 3.32% leaves the absent bucket for the 9 characters that log it, and nothing else moves. | landing outside that band |
| **P2** | Righteous Vengeance carries a **non-zero sim damage row for at least 8 of the 9** characters that log it (0 today), and for **zero characters that do not hold the card**. | fewer than 8, or any non-holder gains a row |
| **P3** | **Phantom production does not rise.** Its share of cohort sim damage stays at or below its current **58.4%**±1pp. This is the prediction the ownership gate exists to make true; without that gate it would rise. | phantom share above 59.4% |
| **P4** | **Slice accuracy at the ≥20% coverage floor RISES** from **26.3%**, to somewhere in **27%–34%**. The sim under-produces (median ratio 0.27), so restoring a real damage source raises the modelled/logged ratio. | landing outside that band, in either direction |
| **P5** | The gate's headline stays **0 of 35 within ±20%, 0 qualified**. RV is single-digit percentages of damage against a median delta of **−87%**; it cannot close that, and predicting otherwise would be wishful. | any character entering ±20% |

## What is NOT predicted

* **Any per-ability ratio.** That is tuning, and it is `3l`'s.
* **The direction of the `starved:zero-casts` bucket (12.9%).** RV has no
  casts by construction (`"casts": 0`), so it touches the GCD budget not at
  all — but the bucket is measured, not reasoned about, and B5 was not
  registered.
* **The holdout.** Unspent this session (standing decision 3).
