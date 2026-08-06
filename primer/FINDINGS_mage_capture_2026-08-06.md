# Findings — the Frost Mage capture, 2026-08-06

> **`FINDING 2026-08-06`** — point-in-time analysis, true as of its date and **not maintained since**. Not citable as current truth without re-checking against the tree. *(Classified `3f` F8c, 2026-08-07.)*

**Analysed by:** the monitoring chat, from the owner's three logs + two stat blocks.
**Capture bundle: `data/source/captures/2026-08-06_elric_mage_frost/`** — its `README.md`
carries the provenance table; this file carries the analysis.
Parsed with `tools/log_parser/combat_log_parser.py` using **named fields** (CLAUDE.md's
rule — no hand-indexed columns). Site reports
[110](https://darkmoon.ascensionlogs.gg/reports/110/encounters) /
[111](https://darkmoon.ascensionlogs.gg/reports/111/encounters) /
[112](https://darkmoon.ascensionlogs.gg/reports/112/encounters).

---

## 0. Capture quality: the cleanest controlled set this project has

| Check | Result |
|---|---|
| Zero-delta export (`2d`/`2e` read-too-early trap) | ✅ **Passed** — blocks differ: Int 321→352, SP 780→840, ManaMax 6097→6562 |
| Same dummy both runs (`2d`: dummy identity is a calibration variable, 10–18%) | ✅ **Verified from the logs** — `Azeroth Execute Training Dummy` is the sole damage target in both |
| Stat block ↔ log pairing | ✅ `ExportedAt 19:15:41` → log `19.16.56`; `19:21:39` → log `19.22.22`. **The timestamp field added this afternoon is what makes this checkable rather than assumed** |
| Windows | unbuffed **214.2s**, buffed **179.9s** — ⚠ not equal, see §2 |

⚠ Two caveats to record, neither fatal. The buffed export reads `PowerMax: 6562
(current 4466)` — taken at 68% mana, i.e. after combat had begun. And the target is an
**Execute** training dummy; `tiers.py:198-199` fixes `target_health_pct` at 100, so any
execute-scaling ability compares against a regime the sim cannot represent.

---

## 1. 🚨 `SPELL_CAST_SUCCESS` and `SPELL_CAST_START` are DISJOINT by cast type

Elric's own events, unbuffed log:

| Event | Count | Spells |
|---|---|---|
| `SPELL_CAST_SUCCESS` | 33 | Ice Lance 12, Ray of Frost 5, Frozen Orb 3, Summon Water Elemental 2, Absolute Zero 2, Cone of Cold 2, Icy Veins 2, Water Shield 2, Glacial Spike 1, Cold Snap 1, Innervate 1 |
| `SPELL_CAST_START` | 75 | **Frostbolt 74**, Hydricles 1 |

**Zero overlap.** Every instant logs `SUCCESS` and never `START`; every cast-time spell
logs `START` and never `SUCCESS`. Frostbolt was cast 74 times and produced **no
`SPELL_CAST_SUCCESS` event at all**, while landing 52 non-crit hits.

### What this breaks

`3c` established *"the site's `casts` IS `SPELL_CAST_SUCCESS` — 93% and 97.3%"*, and on
that basis **withdrew** its own objection that `casts` *"under-reads proc builds and
would bias the corpus"*, recording it as *"wrong at character level."*

That measurement was taken on a **Hammerdin — an all-instant kit**. It is correct there,
and it does not generalise. For a cast-time caster the site's `casts` column counts only
the instant portion of the rotation. Elric cast Frostbolt 74 times; `casts` records zero.

🛑 **The withdrawal needs partial un-retraction.** The objection was right for exactly the
population `3c` could not see.

### The consequence that matters most

`PLAN_3C`'s C2 (log admissibility) uses **APM ratios** to separate model error from
invalid parses — Boomcat 0.24 against Elric's known death case at 0.38. If APM derives
from a `casts` column that is blind to cast-time spells, **every caster in the cohort
reads as artificially low-APM — i.e. looks like a death-deflated parse.** That is a
false-positive generator sitting inside the filter built to detect invalid parses, and it
selects against exactly the archetype the cohort is thinnest on.

**Before C2 ships:** check whether the crawl's `casts` comes from the site column, and
whether any cohort character diagnosed via APM is a cast-time caster. Boomcat's
retraction rests on that number.

---

## 2. The buff layer, measured per hit — and why the DPS ratio is not the buff

**Per-hit non-crit averages, unbuffed → buffed:**

| Ability | n (U/B) | U avg | B avg | ratio |
|---|---|---|---|---|
| Frostbolt | 52/42 | 1347.2 | 1383.5 | **1.027** |
| Icicle | 43/48 | 1170.9 | 1174.9 | **1.003** |
| Ray of Frost | 16/15 | 2008.6 | 1887.9 | **0.940** |
| Waterbolt (pet) | 21/20 | 644.1 | 640.5 | **0.994** |
| Ice Lance | 8/10 | 436.4 | 544.8 | 1.248 |
| Frozen Orb | 17/19 | 201.1 | 215.2 | 1.070 |
| Frost Fever | 5/5 | 102.2 | 110.4 | 1.080 |

**The buff barely moves per-hit damage** — a tight ~×1.00 core on the well-sampled
abilities, against the paladin's ×1.45. That is consistent with what the stat blocks say
was actually applied: **Int +31, exactly reproducing `2e`'s measured Arcane Brilliance
grant**, and SP 780→840 (+7.7%). A +7.7% SP rise on abilities whose damage is part flat,
part coefficient lands at +2–3% per hit. It fits.

**But total DPS moved ×1.396** (1,454 → 2,030 including pet). That gap is **not the
buff.** Casts/min differ between the runs — Ice Lance 3.4 → 5.0, Frozen Orb 0.8 → 1.0,
plus Innervate and Cold Snap appearing only in the buffed run. The two runs are different
rotations.

> **Methodological finding: a paired-dummy capture measures a buff only if the rotation is
> held constant between the runs.** For an all-instant melee kit the rotation is close to
> automatic and this is free — which is why `2e` got a clean ×1.45. For a caster with
> cooldowns and a cast-time filler it is not free, and the DPS ratio silently absorbs
> every rotation difference.
>
> **The per-hit numbers are the durable quantity.** That is `2c`'s weapon-free-pair
> conclusion arrived at from a completely different direction: prefer the quantity that
> cancels what you did not control.

---

## 3. Cast time: the DBC base is not what is being cast

| Source | Frostbolt R11 |
|---|---|
| DBC base (`casting_time_index` 5 → `dbc_spellcasttimes`) | **2000 ms** |
| Client, `GetSpellInfo` position 7 | **1404 ms** |
| Log, back-to-back `SPELL_CAST_START` floor | **1273 ms** (p10 1306 ms; median 1554 ms) |

The client figure implies **×1.4245** — far beyond `Rating_HasteSpell`'s 2.90%, and
consistent with Path of Intelligence's 2H clause plus card effects. The log's floor sits
*below* the client figure, which is expected: Icy Veins was used (0.6/min), and the median
of 1554 ms carries human reaction latency between casts. The log corroborates the order of
magnitude; **the client's per-spell number is the better instrument.**

🛑 **Consequence: a sim reading Frostbolt's cast time from the DBC would model it ~42%
slow.** Combined with `apl_gen.py:62-63` sorting fillers by damage *per cast* rather than
per cast-time, this is the second independent reason the APL cannot order a caster's
rotation correctly today.

---

## 4. Pet contribution is small and cleanly separable

| Run | Player | Pet | Pet share |
|---|---|---|---|
| Unbuffed dummy | 296,031 | 15,453 | **5.0%** |
| Buffed dummy | 345,712 | 19,578 | **5.4%** |
| Dungeon | 940,460 | 14,385 | **1.5%** |

Separation was free from the log — the pet is its own `sourceName`. Waterbolt averages
644 per non-crit hit and is essentially buff-invariant (×0.994), consistent with a pet
that snapshots or scales off something the Arcane Intellect grant does not touch.

**This bounds C5 (pets, 440 points):** the unmodelled-pet gap on this build is ~5% on a
dummy and ~1.5% in a dungeon — real but not a dominant term. Worth knowing before the task
is scoped as though pets were a large share.

---

## 5. Smaller observations

* **175 `SPELL_CAST_FAILED` with no spell name** in the unbuffed run, against 75 starts.
  Consistent with the owner's own description of a rough rotation. Not a data problem, but
  it means GCD occupancy in this parse is genuinely low — useful, since it stresses the
  idle-budget path the paladin never reaches.
* **Dungeon is Scarlet Monastery** — High Inquisitor Whitemane, High Inquisitor Fairbanks,
  Scarlet Abbot. **288 ALC build records** decoded from that log: other players' builds,
  free corpus material.
* **`SPELL_PERIODIC_HEAL` is the second-largest event class** in both dummy runs
  (1,916 / 2,088) — Water Shield and/or Rejuvenating Water. Worth confirming nothing in
  the kit is trading damage for self-healing in a way the sim would not model.

---

## 6. Does the "bad build / bad rotation" matter?

**Not for what this capture is for, and in one respect it helps.**

The sim is scored against the rotation the character actually ran, so a sub-par rotation
is a valid test case as long as the *inputs* are right — and they are: same dummy,
same-session stat blocks, verified timestamps, no path switch, no zero-delta export. Input
fidelity is what `2e` proved is the whole error term, and this capture has none.

What a rough rotation changes is *which* engine paths get exercised, and it exercises more
of them: 175 failed casts and a sparse GCD occupancy push on the idle-budget and
filler-selection logic that a tight all-instant rotation never touches. Both of the
`fast_sim` defects the audit named — the first filler consuming the whole GCD budget, and
fillers ordered by damage-per-cast — are more visible here, not less.

**The one thing that would matter and does not apply:** if the rotation had been *tuned to
the sim's own recommendations*, the comparison would be circular. It was not.

---

## 7. What `3e` should do with this

1. **Check `casts` provenance before C2 ships** (§1). This is the finding with the largest
   blast radius — it may invalidate an APM-based retraction and it selects against casters.
2. **Use the per-hit table, not the DPS ratio**, for the caster buff layer (§2), and record
   in `core/sim/buffs.py` that this build's applied buff was Arcane Intellect alone.
3. **Feed the client's per-spell cast time into the APL** rather than the DBC base (§3);
   it is a precondition for fixing filler ordering, not a separate task.
4. **Scope C5 against the measured 1.5–5.4%** (§4).
5. **Use this as the caster fixture** per the earlier addendum — it now comes with
   ground truth on seven abilities.

🛑 And per the standing rule: if the Mage gets a `character_snapshots` row, it needs the
same `EXCLUDED_SNAPSHOT_SOURCES` exclusion Elric got in `3d`. The hazard is identical and
it is easier to forget the second time.
