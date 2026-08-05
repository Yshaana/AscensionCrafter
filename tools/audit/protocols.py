#!/usr/bin/env python3
"""Phase 1 T8 — the test-protocol generator (session 1c).

The verification queue's real output isn't "these values are unverified" —
it's *what to actually do tonight at a target dummy*.

    py tools/audit/protocols.py                       # protocols for all open questions
    py tools/audit/protocols.py armor_pen_divisor_5_vs_4_2

Hard rules, encoded as code and not convention (primer §5):

* 🛑 **NEVER emit a card-destroying protocol.** Rerolling a card to measure it
  is refused outright — multi-rank cards can return lower and there is no
  respec. `generate_test_protocol` raises `CardDestructionRefused` rather than
  merely deprioritising.
* Method preference ladder: character-sheet breakdown tooltips → gear swaps →
  consumables → buff-state filtering → two-target comparisons → bar toggles.
* Minimum sample size is COMPUTED from the discriminating power needed; when
  candidate values are within ~3 points the correct output is
  "insufficient discriminator — find another test", not a number.
* Every protocol states target level (miss rates differ ~6% at +2 vs ~17% at
  +3 — unstated content produces uninterpretable data) and the expected
  outcome under EACH hypothesis.
"""
import argparse
import json
import math
import sqlite3
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from config import DB_PATH  # noqa: E402
import config  # noqa: E402

# Piped/redirected stdout defaults to cp1252 on Windows and this file
# prints non-ASCII; without this it dies with UnicodeEncodeError only when
# its output is captured. See config.ensure_utf8_stdout.
config.ensure_utf8_stdout()

METHOD_LADDER = [
    "character-sheet breakdown tooltip",
    "gear swap",
    "consumable",
    "buff-state filtering",
    "two-target comparison",
    "bar toggle",
]

FORBIDDEN_METHODS = ("reroll", "re-roll", "destroy", "consume the card")


class CardDestructionRefused(Exception):
    """Raised when a protocol would destroy a card. There is no respec."""


def proportion_sample_size(p1, p2, alpha=0.05, power=0.8):
    """Two-proportion test n per arm. Returns None when the gap is inside the
    ~3-point insufficient-discriminator zone (primer §5)."""
    if abs(p1 - p2) < 0.03:
        return None
    z_a, z_b = 1.96, 0.84
    pbar = (p1 + p2) / 2
    n = ((z_a * math.sqrt(2 * pbar * (1 - pbar))
          + z_b * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2) / (p1 - p2) ** 2
    return math.ceil(n)


def _check(protocol):
    """Every protocol passes through here — the refusal is structural.

    The scan covers the ACTIONABLE fields (method/setup/record) only: a
    question may legitimately be *about* reroll mechanics (observed during
    fishing the player does anyway) without the protocol instructing one."""
    blob = json.dumps({k: protocol.get(k) for k in ("method", "setup", "record")}).lower()
    for term in FORBIDDEN_METHODS:
        if term in blob:
            raise CardDestructionRefused(
                f"protocol for {protocol.get('question_slug')} instructs '{term}' — "
                "card-destroying tests are refused, not deprioritised")
    for field in ("method", "setup", "record", "hypotheses", "target_level"):
        assert field in protocol, f"protocol missing {field}"
    hyps = protocol["hypotheses"]
    assert len(hyps) >= 2, "a test with one hypothesis is not a test"
    outcomes = {json.dumps(h["expected_outcome"], sort_keys=True) for h in hyps}
    assert len(outcomes) == len(hyps), \
        "hypotheses with identical expected outcomes cannot be distinguished"
    return protocol


# --------------------------------------------------------------------------
# Hand-written protocols for the top open questions (exit criterion: a runnable
# test for at least the top 5). Keyed by open_questions.slug.
# --------------------------------------------------------------------------
HAND_PROTOCOLS = {
    "armor_pen_divisor_5_vs_4_2": {
        "ability": None,
        "method": "character-sheet breakdown tooltip",
        "target_level": "n/a — sheet read, no target",
        "setup": "At level 60, equip any gear with armor penetration rating. "
                 "Hover the Armor Penetration line on the character sheet and "
                 "read the displayed percentage next to the rating.",
        "record": ["armor pen rating", "displayed %"],
        "min_sample_size": 1,
        "hypotheses": [
            {"name": "site is right (5.0)", "expected_outcome": "pct = rating / 5.0"},
            {"name": "client gt table is right (4.2)", "expected_outcome": "pct = rating / 4.2"},
        ],
        "note": "At e.g. 42 rating the readings differ 8.4% vs 10.0% — one sheet "
                "read discriminates. Zero cost.",
    },
    "fel_infused_weapon_per_level_3x": {
        "ability": "Fel Infused Weapon (276076 / sub-spell 276075)",
        "method": "character-sheet breakdown tooltip",
        "target_level": "n/a — tooltip read at level 60",
        "setup": "Read Fel Infused Weapon's tooltip in-game at level 60 with "
                 "known AP and SP (screenshot the sheet in the same session). "
                 "The flat component resolves fully in the live tooltip.",
        "record": ["tooltip flat range", "AP", "SP"],
        "min_sample_size": 1,
        "hypotheses": [
            {"name": "client DBC right (1.5/level)",
             "expected_outcome": "flat ≈ 4 + (60-spell_level)*1.5 after removing AP*0.05+SP*0.05"},
            {"name": "db.ascension.gg right (4.5/level)",
             "expected_outcome": "flat ≈ 4 + (60-spell_level)*4.5 after removing AP*0.05+SP*0.05"},
        ],
        "note": "3x apart at level 60 — trivially discriminated by one read. "
                "Tier 1, beats both conflicting sources.",
    },
    "elric_active_path_and_duality_ap_anomaly": {
        "ability": None,
        "method": "character-sheet breakdown tooltip",
        "target_level": "n/a — sheet read",
        "setup": "On Elric's CURRENT (talent-loaded) board: (1) confirm the "
                 "active Path on the character panel; (2) hover melee crit and "
                 "spell crit breakdowns — under Duality the melee table lists "
                 "an Intellect line and the spell table an Agility line; "
                 "(3) note AP with Str/Agi visible for the anomaly check.",
        "record": ["active path", "melee crit source list", "spell crit source list",
                   "AP", "Str", "Agi"],
        "min_sample_size": 1,
        "hypotheses": [
            {"name": "Duality active",
             "expected_outcome": "Int appears in melee crit sources AND Agi in spell crit sources"},
            {"name": "another path active",
             "expected_outcome": "base-game conversions only (Agi->melee, Int->spell)"},
        ],
        "note": "The amp itself is already confirmed (1.895x, empty-spec A/B). "
                "This settles only the CURRENT board's selection. The AP-at-"
                "0.548x anomaly needs the same sheet's AP vs highest(Str,Agi).",
    },
    "lightbound_cleave_post_patch_procs": {
        "ability": "Lightbound Cleave (907300)",
        "method": "two-target comparison",
        "target_level": "target dummy (equal level) — proc counting, not avoidance",
        "setup": "On a dummy, queue ONLY Lightbound Cleave off-GCD over autos "
                 "for ~5 minutes; count Hammerdin stack gains, JotTH procs, and "
                 "PBL procs in the log. Then repeat pressing ONLY Judgement + "
                 "Holy Shock for the same duration as the positive control.",
        "record": ["LC casts", "Hammerdin procs during LC-only window",
                   "JotTH procs", "PBL procs", "control-window procs"],
        "min_sample_size": 100,
        "hypotheses": [
            {"name": "verdict unchanged (Warrior-tagged, 0 Hammerdin procs)",
             "expected_outcome": "0 Hammerdin procs from ~100 LC casts; control window procs normally"},
            {"name": "patch changed LC's proc eligibility",
             "expected_outcome": "nonzero Hammerdin procs from LC casts"},
        ],
        "note": "~100 casts suffices: a 0%-vs-anything question needs presence, "
                "not a rate estimate. The 2026-08-03 patch specifically touched "
                "off-GCD On-Next-Hit proc eligibility.",
    },
    "capped_level_scaling_engine_formula": {
        "ability": "any CAPPED level-scaled spell (spell_effect_values: per_level "
                   "> 0 AND max_level > 0) owned by the character",
        "method": "character-sheet breakdown tooltip",
        "target_level": "n/a — tooltip read at level 60",
        "setup": "Pick one capped level-scaled spell from the query "
                 "SELECT spell_id FROM spell_effect_values v JOIN spell_dbc_raw d "
                 "ON d.id=v.source_spell_id WHERE v.per_level>0 AND d.max_level>0 "
                 "— read its in-game tooltip and compare the flat against "
                 "flat + (min(60, max_level) - spell_level) * per_level.",
        "record": ["spell id", "tooltip flat", "computed flat with cap",
                   "computed flat without cap"],
        "min_sample_size": 1,
        "hypotheses": [
            {"name": "engine caps as min(level, max_level)",
             "expected_outcome": "tooltip matches the capped computation"},
            {"name": "cap applies differently (or not at all)",
             "expected_outcome": "tooltip matches the uncapped computation or neither"},
        ],
        "note": "Pick a spell where cap and no-cap differ by >10% or the read "
                "cannot discriminate (insufficient-discriminator rule).",
    },
    "titans_grip_tax_on_holystrike": {
        "ability": "Lightbound Cleave (907300) or Dawn Strike",
        "method": "two-target comparison",
        "target_level": "target dummy (equal level); state dummy armor if known",
        "setup": "Parse ~100 Lightbound Cleave non-crit hits under Titan's Grip, "
                 "then ~100 with a single 2H equipped (same weapon MH). Compare "
                 "mean non-crit damage after normalising for the weapon change "
                 "via Dawnreaver's (pure-physical) shift in the same windows.",
        "record": ["LC non-crit mean x2", "Dawnreaver non-crit mean x2",
                   "weapon/AP/SP at both readings"],
        "min_sample_size": 100,
        "hypotheses": [
            {"name": "tax applies to Holystrike weapon half",
             "expected_outcome": "LC shifts by the same factor as Dawnreaver (~-10% under TG)"},
            {"name": "tax skips the magic-school half",
             "expected_outcome": "LC shifts LESS than Dawnreaver by the magic component's share"},
        ],
        "note": "Multiplier-scale question: ~100 hits per arm (primer §5). "
                "Requires owning a spare 2H — the board itself is untouched.",
    },
    "reroll_upgrade_chance_slot_scope": {
        "ability": None,
        "method": "buff-state filtering",   # observational: log outcomes of fishing already happening
        "target_level": "n/a — economy observation, no combat",
        "setup": "OBSERVATIONAL ONLY — during upgrade fishing the player "
                 "already does, log every roll outcome twice: rolls landing in "
                 "the slot holding the partial-rank card vs rolls landing in "
                 "other slots. Never touch a slot for the sake of this test.",
        "record": ["slot rolled", "held partial present in that slot y/n",
                   "did the roll upgrade a held partial", "card rolled"],
        "min_sample_size": 200,
        "hypotheses": [
            {"name": "elevated chance is holding-slot-only",
             "expected_outcome": "upgrade rate higher only when the roll lands in the holding slot"},
            {"name": "elevated chance applies to any slot",
             "expected_outcome": "upgrade rate elevated regardless of which slot the roll lands in"},
        ],
        "note": "Passive logging of normal play — zero cards at risk. 200 rolls "
                "is a floor; the rate gap size determines the real n.",
    },
}


def generic_protocol(slug, question, blocks):
    """Fallback for questions without a hand-written protocol: classify by
    keywords and emit the closest template, honestly labelled as generic."""
    q = question.lower()
    if "crit" in q or "proc rate" in q or "chance" in q:
        n = proportion_sample_size(0.15, 0.20)
        kind, n = "proportion (crit/proc rate)", n or 2000
    elif any(w in q for w in ("coefficient", "magnitude", "formula", "flat", "%")):
        kind, n = "multiplier/magnitude", 100
    else:
        kind, n = "structural/lookup", 1
    return {
        "question_slug": slug, "generic": True,
        "ability": None, "method": METHOD_LADDER[0] if n == 1 else METHOD_LADDER[4],
        "target_level": "STATE THE CONTENT LEVEL — +2 dungeon ~6% miss vs +3 raid ~17%",
        "setup": f"[generic {kind} template — refine by hand] {question[:200]}",
        "record": ["depends on the refined design"],
        "min_sample_size": n,
        "hypotheses": [
            {"name": "H1 (as documented)", "expected_outcome": "matches the documented value"},
            {"name": "H2 (alternative)", "expected_outcome": "matches the competing value"},
        ],
        "note": f"blocks: {blocks or 'unknown'}",
    }


def generate_test_protocol(conn, slug):
    row = conn.execute(
        "SELECT question, blocks, status FROM open_questions WHERE slug = ?",
        (slug,)).fetchone()
    if row is None:
        return None
    question, blocks, status = row
    proto = dict(HAND_PROTOCOLS.get(slug) or generic_protocol(slug, question, blocks))
    proto.update({"question_slug": slug, "question": question, "status": status})
    if proto.get("min_sample_size") is None:
        proto["method"] = "INSUFFICIENT DISCRIMINATOR"
        proto["note"] = ("candidate values within ~3 points — find another test "
                         "(primer §5); do not collect a sample that cannot decide")
    return _check(proto)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("slug", nargs="?", help="one open_questions slug (default: all open)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    conn = sqlite3.connect(str(DB_PATH))

    slugs = ([args.slug] if args.slug else
             [r[0] for r in conn.execute(
                 "SELECT slug FROM open_questions WHERE status IN "
                 "('open','in_progress') ORDER BY id")])
    protos = []
    for s in slugs:
        p = generate_test_protocol(conn, s)
        if p:
            protos.append(p)

    if args.json:
        print(json.dumps(protos, indent=2))
        return 0
    for p in protos:
        tag = " [GENERIC — refine by hand]" if p.get("generic") else ""
        print(f"— {p['question_slug']}{tag}")
        print(f"  method: {p['method']} | n ≥ {p['min_sample_size']} | target: {p['target_level']}")
        print(f"  setup: {p['setup'][:150]}")
        for h in p["hypotheses"]:
            print(f"    if {h['name']}: {h['expected_outcome'][:110]}")
    hand = sum(1 for p in protos if not p.get("generic"))
    print(f"\n{len(protos)} protocol(s), {hand} hand-written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
