#!/usr/bin/env python3
"""Generate the two non-paladin sim fixtures from REAL crawled boards (3d D1).

    py tools/audit/build_nonpaladin_fixtures.py

Why this exists — the single biggest structural risk the `3c` adversarial audit
found. Every committed fixture, the whole `check_sim_engine.py` regression
harness, and `calibrate_vs_log.py`'s defaults are **one character**: Elric, a
Paladin/Hammerdin. Six real engine bugs sit in shared code paths that an
all-instant, single-filler, no-combo-point, no-pet melee build is
**structurally incapable of exposing**. Nothing in the repo would fail if a
Rogue or a Warlock produced nonsense.

The corpus is not paladin-skewed — 371 level-60 decoded boards split intellect
79 / strength 50 / spirit 48 / duality 40 / agility 38, with Hammerdin on 9 —
so real alternatives exist and there is no reason to invent one.

🛑 THE CARD SETS ARE REAL, AND SO ARE THE STATS, AND THE STATS ARE GEAR-ONLY.
`character_snapshots.gear_stats_json` carries an explicit `_gearOnly` key and
shows a level-60 character with Strength 31 — it is **not a character sheet**
(INDEX_GUIDE v16). That is written into each fixture's `provenance` rather than
papered over. These fixtures exist to exercise ENGINE CODE PATHS — does a
finisher ever fire, is a DoT re-cast every GCD, do multiple cast times order
sensibly — not to be calibration anchors. Nothing here should ever be read as a
DPS prediction for these characters.

Regenerating: `builds.db` is gitignored and its bulk needs tier-2 crawl data, so
this script cannot run on a clean clone. That is exactly why its OUTPUT is
committed JSON — the fixtures must be reproducible for anyone running the
harness, independent of whether they can rebuild the corpus.
"""
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import config  # noqa: E402
import season_config  # noqa: E402
from config import BUILDS_DB_PATH, DB_PATH  # noqa: E402

config.ensure_utf8_stdout()

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"

# Chosen on MECHANICS, not on name or class — the project has no classes.
# Each names the engine paths a Hammerdin cannot reach.
TARGETS = [
    {
        "snapshot_id": 462,
        "out": "build_crawled_cp_melee.json",
        "name": "crawled_cp_melee",
        "path": "Agility",
        "why": (
            "COMBO-POINT MELEE. Holds four abilities carrying a real per-combo "
            "term (Rupture, Crimson Tempest, Panache, Aether Rupture) plus "
            "energy builders (Razzashi Talon, Heroic Strike) and an "
            "EXECUTE-RANGE ability (Hammer of Wrath, usable only below a health "
            "threshold). Talent side carries the combo-point economy — Seal "
            "Fate, Ruthlessness, Relentless Strikes. Also holds two pet "
            "summons, so it reaches the no-pet-model gap as a side effect. "
            "Exercises: combo_points never incremented (tiers.py:197, "
            "apl.py:118), target_health_pct pinned at 100 so execute windows "
            "are dead code (tiers.py:198-199), and CP terms scored at 0 CP "
            "(ability_model.py:420-425)."
        ),
    },
    {
        "snapshot_id": 218,
        "out": "build_crawled_dot_caster.json",
        "name": "crawled_dot_caster",
        "path": "Intelligence",
        "why": (
            "DoT CASTER. Holds five periodic damage abilities of DIFFERENT "
            "durations (Corruption, Immolate, Living Bomb, Pyroblast, Fel "
            "Armor) and fillers at THREE different cast times — Scorch / "
            "Searing Pain / Fireball at 1.5s, Chaos Bolt / Hand of Gul'dan at "
            "2.0s, Pyroblast at 5.0s — on a mana bar, plus a pet (Summon Imp). "
            "Exercises: no DoT-uptime condition exists so apl_gen gives fillers "
            "'always' and a DoT is re-cast every GCD with its whole duration's "
            "damage re-scored (apl.py:19-32), fillers sorted by damage per CAST "
            "rather than per GCD/cast-time (apl_gen.py:62-63), the fast_sim "
            "first-filler-eats-the-budget bug (tiers.py:137-141), and the "
            "absent pet model against a corpus dps that INCLUDES pet damage "
            "(corpus.py:614)."
        ),
    },
]


def weapons_for(b, snapshot_id):
    out = {}
    rows = b.execute(
        "SELECT slot, item_name, weapon_json FROM snapshot_gear "
        "WHERE snapshot_id = ? AND weapon_json IS NOT NULL ORDER BY slot",
        (snapshot_id,)).fetchall()
    for i, (slot, item_name, wj) in enumerate(rows):
        w = json.loads(wj)
        key = "main_hand" if i == 0 else "off_hand"
        out[key] = {"min": w["min"], "max": w["max"], "speed": w["speed"],
                    "hand": w["hand"], "item_name": item_name}
    return out


def stats_for(gear_stats_json):
    """Gear-only stats, mapped to the `stats_override` vocabulary.

    ⚠ Uses the crawl's own `derived` block where it exists, because that is
    BisBeard's resolution of the same gear and applying our own conversions on
    top would double-count. Anything the block does not state is OMITTED, never
    defaulted to a plausible number.
    """
    gs = json.loads(gear_stats_json)
    raw, der = gs.get("raw", {}), gs.get("derived", {})
    out = {}
    for key, src, field in (
        ("attack_power", der, "attackPower"),
        ("spell_power", raw, "spellPower"),
        ("melee_crit_pct", der, "critPercentMelee"),
        ("spell_crit_pct", der, "critPercentSpell"),
        ("melee_hit_pct", der, "hitPercent"),
        ("spell_hit_pct", der, "hitPercent"),
        ("expertise_points", der, "expertise"),
        ("armor_pen_pct", der, "armorPenPercent"),
        ("melee_haste_pct", der, "hastePercent"),
        ("spell_haste_pct", der, "hastePercent"),
        ("strength", raw, "strength"),
        ("agility", raw, "agility"),
        ("intellect", raw, "intellect"),
        ("stamina", raw, "stamina"),
        ("spirit", raw, "spirit"),
    ):
        v = src.get(field)
        if v is not None:
            out[key] = float(v)
    return out


def build_one(b, spec):
    snap = spec["snapshot_id"]
    row = b.execute(
        "SELECT ch.name, s.path, s.captured_at, s.patch_date, s.realm, s.season,"
        " s.gear_stats_json, s.capture_report_id, s.captured_for_boss "
        "FROM character_snapshots s JOIN characters ch "
        "ON ch.character_id = s.character_id WHERE s.snapshot_id = ?",
        (snap,)).fetchone()
    if row is None:
        raise SystemExit(f"snapshot {snap} not in builds.db — cannot regenerate. "
                         f"The COMMITTED fixture is the artifact; this script "
                         f"needs a corpus with tier-2 data.")
    (who, crawl_path, captured_at, patch_date, realm, season,
     gear_json, report_id, boss) = row

    cards = {"abilities": [], "talents": []}
    for tree, spell_id, name, rank in b.execute(
            "SELECT tree, spell_id, name, rank FROM snapshot_cards "
            "WHERE snapshot_id = ? AND spell_id IS NOT NULL ORDER BY tree, name",
            (snap,)):
        cards[tree].append({"spell_id": spell_id, "rank": rank or 1,
                            "name": name})

    unresolved = b.execute(
        "SELECT COUNT(*) FROM snapshot_cards WHERE snapshot_id = ? "
        "AND spell_id IS NULL", (snap,)).fetchone()[0]

    fixture = {
        "name": spec["name"],
        "provenance": (
            f"REAL crawled board — character {who!r}, snapshot {snap}, captured "
            f"{captured_at} (patch {patch_date}, report {report_id}"
            f"{', boss ' + boss if boss else ''}), crawl path {crawl_path!r}. "
            f"Generated by tools/audit/build_nonpaladin_fixtures.py (3d D1). "
            f"WHY THIS BOARD: {spec['why']} "
            f"🛑 STATS ARE GEAR-ONLY. They come from "
            f"character_snapshots.gear_stats_json, which carries an explicit "
            f"_gearOnly key — no path grant, no talent, no buff, no base "
            f"stats. That is why the primary stats look far too low for level "
            f"60. THIS FIXTURE IS NOT A DPS PREDICTION AND ITS ABSOLUTE OUTPUT "
            f"MEANS NOTHING; it exists to exercise engine code paths a "
            f"single-paladin harness cannot reach. Weapon damage IS real — "
            f"parsed from the item description and self-checked against that "
            f"description's own stated DPS."
        ),
        "character_level": 60,
        "role": "dps",
        "path": spec["path"],
        "realm": season_config.REALM,
        "season": season_config.SEASON,
        "source": "crawled",
        "crawl_snapshot_id": snap,
        "stats_override": stats_for(gear_json),
        "weapons": weapons_for(b, snap),
        "abilities": cards["abilities"],
        "talents": cards["talents"],
        "unresolved": ([
            f"{unresolved} card(s) on this board did not resolve to a spell id "
            f"at corpus-build time and are OMITTED rather than guessed at "
            f"(snapshot_cards.spell_id IS NULL)."
        ] if unresolved else []),
    }
    return fixture


def main():
    if not BUILDS_DB_PATH.exists():
        print(f"no builds.db at {BUILDS_DB_PATH} — run "
              f"ingest/logs_gg/build_builds_db.py first. The committed "
              f"fixtures remain valid without it.", file=sys.stderr)
        return 1
    b = sqlite3.connect(BUILDS_DB_PATH)
    FIXTURES.mkdir(exist_ok=True)
    for spec in TARGETS:
        fx = build_one(b, spec)
        out = FIXTURES / spec["out"]
        out.write_text(json.dumps(fx, indent=2, ensure_ascii=False) + "\n",
                       encoding="utf-8")
        print(f"{out.name}: {len(fx['abilities'])} abilities, "
              f"{len(fx['talents'])} talents, "
              f"{len(fx['weapons'])} weapon(s), "
              f"{len(fx['stats_override'])} gear-only stats"
              + ("  ⚠ " + fx["unresolved"][0] if fx["unresolved"] else ""))
    b.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
