# Addendum — mid-`3d`, folding into `3e`

**Written by:** the monitoring chat, 2026-08-06, after `3d` had already started.
Companion to `primer/SESSION_3D_PRIMER.md` and `primer/AUDIT_3C_ADVERSARIAL.md`.
**Nothing here changes `3d`'s scope or its §0 invariant.** Two items are owner-side
and land whenever convenient; the rest is `3e` input.

---

## 1. What changed while `3d` was running

**The stat-export addon gained five fields** (owner, 2026-08-06). The updated
`addons/AscensionCrafterExport/AscensionCrafterExport.lua` should be committed as-is:

> ✅ **DONE — it landed at commit `9486283`, version `2026-08-06c`.** `PROGRESS.md`
> carried an "⚠ OWNER ACTION OUTSTANDING" on this into `3e`; cleared in `3e` A6.

| New line | Why it exists |
|---|---|
| `ExportedAt: <local time>` | `2e` established a stat block from a different session is not a degraded input, it is **the whole error** for weapon-dominated abilities; `2d` found the read-too-early trap where a post-cast export was byte-identical to the pre-cast one. **Neither is checkable on an untimestamped block.** Now every export carries its own capture time |
| `PowerType` / `PowerMax` | Generic, so an energy/rage/runic character exports its own bar instead of nothing |
| `ManaMax` | On a 5-minute caster parse mana is usually the binding constraint, and `fast_sim` models no resources at all — so an OOM parse and a clean one are **indistinguishable downstream** unless the pool is recorded |
| `ManaRegen_raw` | ⚠ Deliberately **unconverted and labelled raw.** `GetManaRegen` returns per-second; the character sheet shows per-5. The value is printed exactly as the API returned it rather than rescaled, because guessing the unit and being wrong plants a silent 5× error in a block everything downstream trusts. **Whoever consumes this must establish the unit before using it** |
| `SpellHaste_raw_UNVERIFIED` / `MeleeHaste_raw_UNVERIFIED` | The existing `Rating_Haste*` lines are rating-derived and per primer v28 are **structurally unable to see buff or talent haste** — which is how an external Swift Retribution aura became a persistent "3% haste even naked" mystery. The gap between these and the rating lines is itself the measurement of everything non-gear. ⚠ **NAME CORRECTED, `3e` A6.** This row originally read `SpellHaste_total` / `MeleeHaste_total`; the shipped addon (`2026-08-06c`, commit `9486283`) calls them `*_raw_UNVERIFIED` and **explicitly does not trust them** — `GetMeleeHaste` read 1.06% against the rating line (`.lua:197-209`). Anything written against the old names silently misses the fields. Establish what the API is returning before consuming either, exactly as for `ManaRegen_raw` |

---

## 2. 🔺 This supersedes `SESSION_3D_PRIMER.md` §7 / F2

**F2 said: make the stat-block flags `required=True`. Do something better instead.**

⚠ **PREMISE CORRECTED, `3e` A6 — the first sentence below described a tree that no
longer exists.** `3d` shipped F2: `calibrate_vs_log.py:429-442` now exposes
`--ap --sp --weapon-min --weapon-max --weapon-speed`, all `required=True`, so **weapon
speed is no longer hardcoded at 3.57**. ⚠ **AND THAT WAS FALSIFIED THREE COMMITS
LATER BY `3e`'s OWN C1** (marked `3f` F8): the five flags are now OVERRIDES, not
required, and `--stat-block` parses the export directly. The correction A6 made was
itself out of date before the session ended — which is the argument for running
doc-drift work at the END of a session, not the start. The rest of the section stands untouched and is
still the right work — five hand-typed numbers is still a hand transcription of a
~40-line export, and the other ~35 fields are still discarded. Per the closing paragraph
of this section, that makes it **additive `3e` work, not a rework**.

Verified in the tree *at the time of writing*: `calibrate_vs_log.py:302-305` exposed
exactly four stat flags (`--ap --sp --weapon-min --weapon-max`), weapon speed was
hardcoded at `3.57` with no flag at all, and **no stat-block parser exists anywhere in
the repo** —
`grep -rl "SpellPower_\|MainHandDamage" --include=*.py` returns nothing but a docstring
mention in `core/sim/buffs.py`. So today a 40-line export is transcribed **by hand** into
four numbers, and the other ~36 fields are discarded.

That is the mechanism that produced the contamination in the first place. Making four
hand-typed flags mandatory does not fix a transcription channel — it just makes the
transcription compulsory.

**Do this instead:**

```
py tools/audit/calibrate_vs_log.py --stat-block <path/to/stat_export_*.txt> <log>
```

* Parse the export file directly. Refuse to run without it (F2's refusal semantics are
  right and should be kept — Rule 2, unconfirmed is flagged, never defaulted).
* **Delete the four defaults.** Do not swap them for fresh numbers.
* Free wins that fall straight out: weapon speed stops being hardcoded; per-school SP and
  per-school crit become available instead of one blended `--sp`; `ExportedAt` lets the
  tool **warn when the block and the log are from different sessions**, which is the
  single error `2e` proved is worth more than all the others combined.
* Keep `--ap`/`--sp`/etc as explicit *overrides* if useful for what-if runs, but never as
  defaults.

If `3d` has already shipped F2 as written, this becomes an `3e` task rather than a rework
— it is additive, and the `required=True` behaviour is preserved either way.

**F2b still stands unchanged and is still the urgent half:** `PHASE_2_simulation.md:470`
states 1.718 and 0.769 as *"the targets a talent model must reproduce"*, and both were
computed from the wrong stat block. Re-derive them.

---

## 3. ✅ LANDED — a three-way controlled capture, non-paladin

> **Captured 2026-08-06 19:15–19:56.** Bundle:
> **`data/source/captures/2026-08-06_elric_mage_frost/`** (provenance table in its
> `README.md`). Analysis: **`primer/FINDINGS_mage_capture_2026-08-06.md`**.
>
> 🚨 **It overturned a `3c` conclusion on arrival.** `SPELL_CAST_SUCCESS` and
> `SPELL_CAST_START` are **disjoint by cast type** on this client — instants log the
> former, cast-time spells the latter, with zero overlap. So the site's `casts` column
> counts only instants, and `3c`'s withdrawal of its own "`casts` under-reads the corpus"
> objection holds for the all-instant Hammerdin it was measured on and **not** for casters.
> This lands directly on C2's APM-based admissibility filter. FINDINGS §1.

The owner captured a **Frost Mage, Path of Intelligence**, in three conditions:

| # | Condition | What it isolates |
|---|---|---|
| 1 | Unbuffed, 5-min dummy | Clean baseline, no group contamination |
| 2 | Buffed, 5-min dummy | **Buff layer for a caster** — same shape as `2e`'s ×1.45 core, on a completely different kit |
| 3 | Buffed, **real dungeon run** | **Content delta** — same character, same buffs, same block; the *only* variable is content |

Each with a stat block, a `WoWCombatLog.txt`, and the Ascension Logs parse.

### Why row 3 is the valuable one

Pair 2→3 is a controlled measurement of **exactly what `ContentProfile` is supposed to
model**, and `ContentProfile` is a **failed** Phase 3 exit criterion — `core/sim/content.py`
has 6 of 8 presets self-declaring `provenance="assumption: …"`, every target stat marked
`retail_hypothesis` (`:93-97`), and **all target counts invented**. No derivation tool
exists in `tools/` or `ingest/`.

This capture is the first data that can replace an assumption with a measurement: real
fight durations, real target counts, real cast uptime under movement, for dungeon content.

🛑 **Be precise about what it does and does not settle.** It derives **one** content
type from **one** run. It does not retire the other presets, and it is not a licence to
back-fill the remaining six by analogy. Derive dungeon, mark it derived, leave the rest
declared as assumptions until they have their own data. The whole reason criterion #7 is
failed rather than merely unverified is that invented values were carried as if they
weren't — do not repeat that with a wider blast radius.

### And it partly answers the objection I raised against C11

I noted that a training dummy is not a boss encounter, so criterion 1's *"per content
profile"* sub-clause could not be satisfied by dummy parses. Row 3 is real content, so it
addresses that for dungeons. ⚠ Still not a raid boss, and the gate cohort is not dungeon
content — so this makes the Mage a **valid second verified character for its own content
profile**, not a third of the raid-side exit.

---

## 4. 🔺 This changes `SESSION_3D_PRIMER.md` §5 / D1

D1 asked for two **synthetic** fixtures built from corpus card sets: a combo-point melee
and a DoT caster.

**Replace the synthetic caster with the Mage**, once the capture lands. A fixture with a
verified stat block, a paired buffed/unbuffed log and a real parse is worth more than a
plausible-looking synthetic one, because a synthetic fixture can only catch a *crash* —
it has no ground truth to be wrong against.

Revised fixture set:

| Slot | Source | Status |
|---|---|---|
| Melee physical, paladin | `build_elric_paladin.json` | exists |
| **Caster, cast-time + mana** | **Frost Mage, verified** | incoming |
| Combo-point melee | synthetic, from corpus | still needed — no ground truth available |
| DoT caster | synthetic, from corpus | still needed; Frost is burst, not DoT |

A Frost Mage exercises cast-time filler ordering, mana as a binding constraint, and
channels — three of the engine gaps a Hammerdin structurally cannot reach. It does **not**
exercise combo points or DoT uptime, so D1's other half is unchanged.

---

## 5. Capture protocol notes for the owner

Small things, each of which has already cost this project a measurement once.

🛑 **Use the SAME training dummy for runs 1 and 2, and record which one.** `2d`'s finding:
two sessions an hour apart with an identical unbuffed character differed **10–18% on every
ability** because one dummy scales to player level and the other is a fixed 63. A different
dummy between the unbuffed and buffed runs would contaminate the entire buff factor — the
one quantity the pair exists to measure.

**Take the stat export INSIDE the dungeon, with the group's buffs actually up** — not
before queueing. Group buffs arrive from other players, and an external aura that nobody
recorded is exactly how Swift Retribution became an unexplained 3% haste. Ideally one at
the start and one at the end; `ExportedAt` now makes the pair checkable. ALC captures every
player build in the log, so group composition is recovered automatically via
`decode_alc.py` — but the *buffs on you* are only in the stat block.

**Note any death, and roughly when.** `deaths` is proven unobtainable from the site API,
and a death-deflated parse is indistinguishable from a model error per candidate — that is
the entire Boomcat retraction. A one-line note converts an unusable parse into a usable one.

**Note whether you went OOM, and roughly when.** `fast_sim` models no resources at all.

**Note whether any channel was in the rotation** (Blizzard, Evocation, Arcane Missiles).
`is_channeled` is resolved in the DB at `spells/mechanics.py:232` and the sim **never reads
it** — a channel costs one GCD and delivers all its ticks. Any channel will read wrong.
That is a bug worth exposing, but only if we know it was there.

**Note whether the build uses Shatter or any freeze-dependent crit.** Dummies are usually
CC-immune, so a freeze-dependent crit profile will under-represent real damage for a reason
that is not a model error. "No freeze effects in this build" is just as useful an answer.

**Mark which dungeon pulls were bosses.** `capture_scopes` distinguishes `boss_single` from
`trash_bundle`, and trash is multi-target while bosses mostly are not — mixing them makes
the target-count derivation meaningless.

---

## 6. What `3e` should do with it

In dependency order, after `3d`'s exit criteria hold:

1. **Land the `--stat-block` parser** (§2). Everything below is read through it, and it
   removes the transcription channel before any new numbers are derived.
2. **Add the Mage fixture** and run `check_sim_engine.py`. Expect failures; record them.
   Per D3's discipline these are `bugs/` entries first, fixes second.
3. **Measure the caster buff layer** from pair 1→2, the same way `2e` measured ×1.45 per
   ability. 🛑 Per-ability, not a blended constant — `2e`'s Righteous Vengeance at ×3.18
   against a ×1.45 core is what proved a single number is wrong.
4. **Derive the dungeon `ContentProfile`** from pair 2→3, and stamp its provenance as
   derived with the evidence ref. Leave the other six presets declared as assumptions.
5. **Then** the modelling work already scheduled for `3e` — RV un-broken and talent-gated,
   the `fast_sim` filler bug, C10→C9 with a second Holy character.

Two standing rules from the primer still apply and matter more now, not less: every
coverage task reports slice accuracy **before and after**, and the ≥5-character holdout is
named **before** the work, not after.

---

## 7. One thing to watch

The Mage is about to become the second character the model is tuned against, and the first
one that is not a paladin. That is the point. **But it is still the owner's own character,
captured under conditions the owner controls** — which is what makes it a good instrument
and also what makes it a poor sample.

The Phase 3 exit wants ≥3 distinct characters and the crawl cohort is where they have to
come from. Two verified owner characters make the *model* honest; they cannot make the
*gate* pass. Keep the exclusion in `candidates()` (§7 F1) applying to the Mage as well as
to Elric — the same silent-cohort-inflation hazard exists, and it will be easier to forget
the second time.
