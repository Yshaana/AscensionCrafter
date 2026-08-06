# Session record — 2026-08-06 `3c`: the paired upload

The owner uploaded four of his own logs to ascensionlogs.gg, giving — for the
first time — **the same combat measured twice**: locally at ground truth and
through the site's API. Everything below is measured, not inferred.

| report | log | content | what it is for |
|---|---|---|---|
| [104](https://darkmoon.ascensionlogs.gg/reports/104/encounters) | `2026-08-04-20.37.12` | Scarlet Monastery | deaths + casts, Path of Intelligence |
| [105](https://darkmoon.ascensionlogs.gg/reports/105/encounters) | `2026-08-04-20.07.21` | Uldaman, 7 bosses | casts control (⚠ Duality — not calibration-grade) |
| [106](https://darkmoon.ascensionlogs.gg/reports/106/encounters) | `2026-08-05-22.42.20` | dummy, **unbuffed** | the clean baseline |
| [107](https://darkmoon.ascensionlogs.gg/reports/107/encounters) | `2026-08-05-23.10.44` | dummy, **buffed** | the buff A/B |

---

## 1. ✅ `ability_performance` is EXACT, not approximate

The single most important result, and it validates the table the whole
calibration gate reads.

| report | site total | log total | abilities disagreeing |
|---|---:|---:|---:|
| 106 (unbuffed) | **443,505** | **443,505** | **0** of 20 |
| 107 (buffed) | **1,102,221** | **1,102,221** | **0** |

Every ability matches to the digit, twice, against an independently parsed local
log. 443,505 also reproduces the capture README's own stated ground truth.

⚠ **DPS differs ~1–2% purely by WINDOW, never by data.** Site 1,540 over its
288.032s against the README's 1,555 over 285.2s; site 3,586 over 307.349s
against 3,650 over 302s. Both are right. **Compare damage totals, not DPS,
unless the window is stated.**

## 2. ✅ The site's `casts` IS `SPELL_CAST_SUCCESS`

| report | site casts | log casts | agreement |
|---|---:|---:|---:|
| 104, Whitemane | 54 | 58 | 93% |
| 105, 7 bosses | 257 | 250 | **97.3%** |

Per-ability exact on Dawn Strike, Dawnreaver, Holy Finish, Judgement of Wisdom,
Light's Hammer, Lightbound Cleave, Whirling Light. **Crawl casts/sec is a
faithful character-level APM measure.** The earlier "it under-reads proc builds
and would bias the corpus" objection was wrong at this level and is **withdrawn**
— the `casts = 0` rows are proc/trigger-delivered damage, which genuinely are
not casts and do not corrupt the total.

## 3. 🛑 `deaths` is UNOBTAINABLE — and the failure mode it hides is real

Searched the entire API payload for a report we control: **no death-like key and
no presence/active-time key exists.** `encounter_performance.deaths` (0 of
19,649) can never be filled from this source. A permanently-NULL column that
looks fillable is its own trap and should be documented as unavailable.

**Ground truth for what that hides**, from report 104: Elric died **6.1s into the
34.0s Fairbanks encounter** and was dead for **82%** of it (alignment verified to
99ms; log local = UTC+1). The site reports **481 DPS against 3,473 on Mograine —
7.2× deflation — with `deaths` NULL and `validation_status: 'valid'`.** A parse
in that state enters the gate looking like a sim **over-prediction**, which is
exactly the Boomcat / Jamppa / Frediib signature.

**But APM cannot be the filter.** It catches this case (14.1 vs 37–43, ratio
0.38), yet as a within-character rule across the cohort it flags 13 of 41 —
including **Malo, one of only two qualified characters** — while missing
Mutaforma (0.99), Jamppa (0.90), Candle (1.05) and Striker (0.55).

> **Four admissibility candidates now tested and rejected: wipes, raw DPS,
> absolute APM, within-character APM. Nothing is filtered.** The corpus contains
> an unknown number of death-deflated parses we cannot identify — a stated gate
> limitation, not something to paper over. Remaining route: infer a death from a
> killing blow in `damage_taken_rows`.

## 4. 🆕 The buff layer, MEASURED per ability (106 vs 107)

Same character, same gear, same dummy, same path. **Per hit**, so cast-count
differences between the windows cannot inflate it:

| ability | unbuffed/hit | buffed/hit | ×/hit |
|---|---:|---:|---:|
| Righteous Vengeance | 228 | 725 | **3.18** |
| Holy Finish | 1,758 | 3,735 | 2.12 |
| Judgement of Command | 1,014 | 2,089 | 2.06 |
| Whirling Light (OH) | 423 | 853 | 2.02 |
| Auto Attack | 389 | 645 | 1.66 |
| Lightbound Cleave | 689 | 1,068 | 1.55 |
| Seal of Command | 450 | 675 | 1.50 |
| Dawn Strike | 582 | 860 | 1.48 |
| Hammer from the Heavens | 474 | 699 | 1.47 |
| Dawnreaver | 489 | 716 | 1.47 |
| Consecration | 163 | 235 | 1.44 |
| Exorcism | 730 | 1,030 | 1.41 |
| Holy Shock | 1,857 | 2,574 | 1.39 |
| Sword Specialization | 624 | 866 | 1.39 |
| Judgement of the Three Hammers | 679 | 860 | 1.27 |
| Righteous Smite | 267 | 329 | 1.23 |
| Arcing Light | 183 | 207 | 1.13 |

**Totals: ×2.49 damage, ×2.33 DPS. Excluding the imbue: ×1.86.**

### What this says

* **The core stat-driven effect is a tight ~×1.45 per hit** — ten abilities sit
  in 1.39–1.55. That is the buff layer doing what a stat buff should.
* 🚨 **Righteous Vengeance ×3.18 is the conversion mechanic compounding**, exactly
  as `PLAN_3C` T6 predicts: buffed crits are both bigger and more frequent, and RV
  converts crit damage. It is the strongest argument yet for implementing
  conversion mechanics rather than treating RV as an ordinary ability.
* 🚨 **Consecrated Holy Weapon is 0 unbuffed → 276,301 buffed = 25.1% of buffed
  damage**, independently reproducing the documented 25.1% to one decimal. The
  sim has **no magnitude for 200818** (enchant-delivered, in the unextracted
  `SpellItemEnchantment.dbc`), so a quarter of the owner's buffed damage remains
  unmodellable. The live tooltip stays the one genuine owner-only ask.
* ⚠ Part of the ×1.45 is the **imbue's stat grant** (+86 raw Holy SP per weapon,
  stacking under Titan's Grip), not only the external buffs — the buffed window
  had the imbue on. Do not attribute the whole ratio to group buffs.

## 5. ⚠ A labelling artifact worth knowing about

The site classified both dummy sessions as a single **"Dynamic Training Dummy"**
encounter with 174/284 participants and `is_boss_encounter = False`, because the
logs are public-area captures and it picks the most-hit target across everyone
present. **Elric never touched that dummy** (883 of 887 events on the Azeroth
Execute Training Dummy). His own rows are complete and correct regardless.

**Consequence:** the cleanest calibration target in the corpus will **not**
auto-qualify as a gate candidate under the non-trash/boss filter. Handle that
deliberately — do not loosen the filter to admit it.

## 6. Method notes

* 🛑 **Aggregate site rows by name before comparing.** A first pass keyed a dict
  on `spell_name` and silently overwrote duplicates (28 Elric rows, several
  sharing a name), producing four bogus `-100%` entries. The site splits some
  abilities across rows.
* 🛑 **The combat log carries no YEAR** — `strptime` defaults to 1900, so
  comparing log timestamps against the site's 2026 ISO times matches nothing.
  Normalise the year before any window filtering.
