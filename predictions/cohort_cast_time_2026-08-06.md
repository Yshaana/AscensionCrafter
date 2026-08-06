# Cohort cast-time profile — the 41 pinned gate characters

**Measured 2026-08-06 from committed artifacts at `91d8f92`.** Method and
interpretation: `primer/FINDINGS_3e_preflight_2026-08-06.md` §1–2.

Path: `entry_id` -> `dbc_character_advancement.ca_id` -> `spell_rank_1..5` ->
highest rank with `spell_level <= 60` -> `casting_time_index` ->
`dbc_spellcasttimes.base`. **Never `entry_id` -> `spells.id`.**

"Cast-time combat abilities" excludes summons, conjures, item-creates and
rebirths — a 10 s Summon Felguard is not a rotational cast.

| id | name | path | delta% | coverage% | slice% | cast-time combat abilities on board |
|---:|---|---|---:|---:|---:|---:|
| 460 | Qt | Intelligence |   -85.46 |   27.9 |     52.1 |   3 |
| 461 | Ryno | Strength |   -67.77 |   69.1 |     46.6 |   0 |
| 462 | Billyeye | Agility |   -45.70 |   51.0 |    106.5 |   2 |
| 463 | Wynta | Intelligence |   -98.05 |    1.3 |    150.0 |   4 |
| 464 | Ari | Strength |    -9.71 |   57.6 |    156.8 |   0 |
| 465 | Mcflurry | Intelligence |   -97.80 |   49.3 |      4.5 |   3 |
| 468 | Onur | Agility |   -75.40 |   47.6 |     51.7 |   3 |
| 1291 | Fana | Strength |   -21.11 |   47.9 |    164.7 |   0 |
| 1582 | Acality | Intelligence |   -90.45 |   36.6 |     26.1 |   8 |
| 2855 | Alicion | Strength |    68.07 |   28.3 |    593.9 |   2 |
| 7051 | Dads | Agility |   -86.47 |   27.5 |     49.2 |   1 |
| 7650 | Me | Strength |   -71.18 |   17.7 |    162.8 |   0 |
| 7661 | Iwannakissms | Healing |   -87.36 |   52.5 |     24.1 |   4 |
| 7674 | Blix | Strength |   -72.99 |   53.4 |     50.6 |   1 |
| 10456 | Nodding | Strength |   -63.57 |   58.2 |     62.6 |   0 |
| 10520 | Pedroporro | Healing |   -88.85 |    3.8 |    293.4 |   6 |
| 10547 | Robbery | Intelligence |   -39.05 |   37.4 |    163.0 |   5 |
| 11407 | Trace | Intelligence |   -72.96 |    9.9 |    273.1 |   3 |
| 11431 | Lootgoblin | Strength |   -85.65 |   46.2 |     31.1 |   0 |
| 11591 | Robottikyrpa | Strength |    20.98 |   48.9 |    247.4 |   1 |
| 16274 | Chastie | Intelligence |    13.11 |    4.6 |   2458.8 |   7 |
| 16501 | Boomcat | Agility |   625.28 |   82.2 |    882.3 |   0 |
| 17884 | Xyz | Agility |   -75.47 |   44.5 |     55.1 |   0 |
| 20419 | Huskeer | Intelligence |   -98.94 |    0.0 |        — |   2 |
| 20461 | Deyindra | Strength |   -79.49 |   10.2 |    201.1 |   2 |
| 20491 | Zaczao | Healing |    -2.84 |    5.6 |   1735.0 |   4 |
| 22640 | David | Intelligence |   -63.13 |    4.2 |    877.8 |   3 |
| 22833 | Meritania | Agility |   -83.41 |   37.7 |     44.0 |   1 |
| 24659 | Ikkura | Intelligence |   -76.19 |   57.8 |     41.2 |   5 |
| 24695 | Qtgamora | Intelligence |   -55.44 |   69.3 |     64.3 |   8 |
| 26116 | Prithika | Healing |   -77.33 |    3.0 |    755.8 |   4 |
| 32037 | Shana | Intelligence |   -78.82 |   56.2 |     37.7 |   4 |
| 32124 | Striker | Intelligence |   146.41 |   32.4 |    760.5 |   4 |
| 33407 | Candle | Healing |   129.40 |   31.5 |    728.2 |   5 |
| 33642 | Mutaforma | Healing |  3618.80 |    0.2 |1859400.2 |   5 |
| 33686 | Jamppa | Healing |   707.65 |    0.0 |        — |   6 |
| 33712 | Malo | Intelligence |   -18.12 |   62.4 |    131.2 |   6 |
| 33818 | Xizek | Healing |   -34.60 |    0.0 |        — |   3 |
| 38900 | Microplastic | Agility |   -56.47 |   22.3 |    195.2 |   0 |
| 39717 | Xoller | Strength |   -11.63 |   13.3 |    664.5 |   0 |
| 40568 | Frediib | Agility |   441.18 |   49.9 |   1084.5 |   1 |

cohort n=41, boards resolved 41/41, unresolved entries per board = 1 (Path of Agility/Intelligence 84865/84866, no spell_dbc_raw row)
>=3 cast-time combat abilities: 22 of 41
caster-ish (>=3): n=22 median delta -68.0% median coverage 29.7%
instant-ish (<3): n=19 median delta -63.6% median coverage 46.2%
