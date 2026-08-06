# Findings — `3e` preflight audit

**Written by:** the monitoring chat, 2026-08-06 evening, against a fresh clone at
`91d8f92`. Everything below was measured from committed artifacts. Nothing here
is inherited from prose.

Three results: thread 1's cheapest task is **settled**, its blast radius is
**measured**, and the Mage capture's dungeon window is **de-confounded for
damage** — the last of these overturns a caveat I raised earlier the same
evening, on owner testimony that the log then corroborated.

---

## 1. Boomcat is not a cast-time caster. Thread 1 does not apply to it.

**Method.** Board resolved through the only legal path — `specialization.hero_build[*].entry_id`
→ `dbc_character_advancement.ca_id` → `spell_rank_1..5` → the highest rank whose
`spell_dbc_raw.spell_level ≤ 60` → `casting_time_index` → `dbc_spellcasttimes.base`.
Never `entry_id` → `spells.id`. Source: `data/source/crawl/*/characters.jsonl.gz`
+ `data/source/dbc/`, both committed.

**Result.** 56 board entries, 55 resolve to a spell with a cast-time index. Exactly
**one** carries a non-zero cast time:

| ca_id | name | spell | cast |
|---|---|---|---|
| 40274 | Conjure Refreshment | 42951 | 3000 ms |

Conjure Refreshment is a food conjure and deals no damage. The other 54 resolved
entries are all 0 ms: Path of Agility, a feral-cat / rogue / hunter physical kit
(Ravage, Maim, Prowl, Slice and Dice, Blade Flurry, Adrenaline Rush, Serpent
Strike, Feral Frenzy…). `primary_stat` reads `agility` independently.

**Therefore.** The mechanism thread 1 proposes — the site's `casts` column counts
only instants, so cast-time casters read as artificially low-APM and look like
death-deflated parses — **cannot** explain Boomcat's 0.24 APM ratio. `3c`'s
retraction of its Boomcat conclusion stands on its own merits, unaffected by the
Mage finding. Thread 1 is **not urgent on this case.**

⚠ **Also worth recording:** the APM ratio itself was a chat-side computation.
`grep -rn "apm" --include=*.py core/ tools/ ingest/` returns **nothing**. No code
in the repo computes APM, so there is no implementation to check the retraction
against — only the reasoning.

## 2. …but 22 of the 41 gate-cohort characters are cast-time casters.

Same method, run across the whole pinned cohort in `predictions/gate_manifest.json`.
All 41 boards resolve (one unresolved entry each, always `Path of Agility` 84865 /
`Path of Intelligence` 84866, which have no `spell_dbc_raw` row — worth a look on
its own, separately).

Counting only cast-time abilities that are **not** summons/conjures/rebirths:

| population | n | median delta | median coverage |
|---|---:|---:|---:|
| ≥3 cast-time combat abilities | **22** | −68.0% | **29.7%** |
| <3 | 19 | −63.6% | **46.2%** |

**Read this carefully.** The 16-point coverage gap is *not* evidence for the
`casts` artifact — `modelled_damage_pct` is computed from logged **damage**
(`calibrate_crawled.py:210-262`), not from casts, so the two are independent
measurements. What it does say is that **the sim covers casters materially worse
than it covers instant kits**, and that more than half the gate cohort sits in
that group.

**Consequence for C2.** Any admissibility filter keyed on APM or on `casts` would
be making a judgement about 22 of 41 cohort members using a column that is
structurally blind to their main abilities. Design it knowing that number; do not
design it on the Hammerdin.

The full per-character table is in `predictions/cohort_cast_time_2026-08-06.md`.

## 3. The Mage dungeon window is de-confounded for damage — corroborated, not assumed

I raised a caveat that Window C (Scarlet Monastery) had no stat block of its own,
leaving the 2→3 content-delta pair confounded by an unknown buff state. **The
owner states the stats were identical to the buffed case, with the caveat that
another player may have buffed him.** The log settles it.

**Method.** Parsed `SPELL_AURA_APPLIED` / `_REFRESH` with `dstName = Elric` and
aura type `BUFF` in both logs, split by whether the source is Elric. Then, to
catch anything already running before the log opened, took the set difference
`REMOVED − APPLIED`.

**Window B (buffed dummy, 19.22.22):** 11 distinct buffs, **all self-applied**.
No buffs pre-existing the log.

**Window C (Scarlet Monastery, 19.45.40):** 37 distinct buffs. Externals:

| buff | source | affects Elric's spell damage? |
|---|---|---|
| Inspiration | Neruune | no — armour |
| Grace | Neruune | no — healing taken |
| Halo | Neruune | no |
| Prayer of Mending | Neruune | no — healing |
| Devotion Aura | Artichoke | no — armour |
| Blessing of Wisdom | Heypal | no — mana regen (sustain, not per-hit) |
| Horn of Winter | Influx | no — AP/Str/Agi, irrelevant to a Frost Mage |
| **Arcane Intellect** | Baconbish | **already present in Window B** (self-cast) |

Pre-existing at log open, from `REMOVED − APPLIED`: **Arcane Brilliance** (the
group version of Arcane Intellect — same grant, does not stack, so no net change
against Window B) and **Commanding Shout** (stamina/health only).

**Therefore: no buff present in Window C and absent in Window B raises Elric's
spell damage.** The owner's statement is corroborated by the artifact. The 2→3
pair is a clean content delta on the damage side.

🛑 **The real blocker on the dungeon `ContentProfile` is not buffs — it is caveat 4
of the capture README: Window C is unsegmented.** Boss and trash pulls are mixed,
and target count and fight duration are exactly what a `ContentProfile` encodes.
Segment C into `boss_single` / `trash_bundle` scopes *before* deriving anything
from it, or the derived profile is an average of two different fight shapes.

**Method note worth generalising:** buff state on the player is recoverable from
the combat log itself, not only from a stat block. The stat block remains the only
source for *ratings*; but "was I buffed by someone in this window" is a `grep`.
Add this to the capture protocol as a check, and the "another player may have
buffed me" caveat stops being unresolvable.

---

## 4. Two smaller things the tree contradicts

**`PROGRESS.md`'s "⚠ OWNER ACTION OUTSTANDING" is stale.** The addon landed at
`9486283`; `addons/AscensionCrafterExport/AscensionCrafterExport.lua` is at
`2026-08-06c`. **But `ADDENDUM_3D_to_3E_mage_capture.md` §1's field table is now
wrong too:** `MeleeHaste_total` / `SpellHaste_total` were renamed
`MeleeHaste_raw_UNVERIFIED` / `SpellHaste_raw_UNVERIFIED` in `b`
(`GetMeleeHaste` read 1.06% against the rating line and is explicitly not
trusted — `.lua:197-209`). Anything written against the addendum's names will
miss the fields.

**`within_tolerance` has no coverage floor.** `calibrate_crawled.py:494` is
`abs(delta) <= AGGREGATE_TOLERANCE_PCT`, nothing else. From the committed
manifest, three of the five characters carrying the ≥3 criterion sit at **4.6%,
5.6% and 13.3%** coverage, and three cohort members have **0.0% coverage with a
non-null delta** (Huskeer −98.9%, Xizek −34.6%, Jamppa +707.7%) — for those, the
sim produced DPS that maps to none of what the character actually logged. The
rider (`QUALIFIED_COVERAGE_PCT = 50`) catches this at the headline; the
**criterion** does not, and the criterion is what `PHASE_3` exit reads.

This is the shape `CHAT_MONITORING_PRIMER` §"how to review" item 6 asks for: a
metric with a regime where it returns a number it cannot support. Slice accuracy
is correctly `None` at zero coverage (`:535-537`); `within_tolerance` is not.

**And the holdout is registered but not wired.** `HOLDOUT_IDS` appears only in
`ingest/export/seed_predictions.py:196`; `grep -n holdout tools/audit/calibrate_crawled.py`
returns nothing. The five are still counted in "n of 41", so any fix that lifts
them moves the headline and spends the holdout in the same number. Splitting the
report — tuning set vs holdout — costs a few lines and keeps them independent.
