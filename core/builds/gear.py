"""Gear data for the sim (Phase 3 Task 4).

🛑 **No `optimize_gearset()`.** Phase 0 Task 9 confirmed BisBeard owns items,
phase tagging and BiS selection, and takes stat weights as a first-class input
(`weightString`). Building a competing optimizer is weeks of work for a worse
result. What this module owns is the half nobody else can produce: the stat
blocks the sim's gear-tier scaling curve needs, and the export that hands our
derived weights to BisBeard.

## Where the item data comes from — and why it is NOT the client's DBCs

Owner decision 2026-08-06 was "client DBC first, it needs nobody's permission."
That route was probed and it **does not carry item stat values**:

* `Item.dbc` (563,308 records, 8 fields) is stock 3.3.5 display data —
  class/subclass/display id/inventory type/sheath. No stats. Expected: in
  3.3.5 item stats live server-side in `item_template`, not in the client.
* `ItemStat.dbc` (1,513,931 records, 39 fields) is a **custom Ascension table
  and it is not a stat block.** Tested against 1,198 items whose real stats
  the crawl already resolves: reading fields 3–22 as `(ITEM_MOD type, value)`
  pairs reproduces the true block exactly **6 times out of 567 overlaps**, and
  no single field equals a real stat value above chance (best 9.2%). Its
  decodable content is display/gating-shaped — f37 is a 1–70 required level,
  f36 an 8000/12000 delay-like constant, f23–f26 floats. Layout otherwise
  unresolved and recorded as an open question rather than guessed at.

So the items table is assembled from `snapshot_gear` — Path B's own fallback,
and the one the recon called "an item database assembled as a byproduct."
Provenance is honest: these stat blocks are **BisBeard's resolution**, carried
through the ascensionlogs armory capture, tier `crawl_resolved_bisbeard`. That
makes cross-validating our weights against BisBeard a check on the *weights*,
not an independent check on the *items* — worth stating before anyone reads
agreement as confirmation.

## 🚨 This server's gear is dynamic — and the difficulty axis lives in the ID

Item stats are rolled at drop as a function of tier (raid difficulty
Normal/Heroic/Mythic/Ascended, or M+ keystone level), so **two items with the
same NAME can carry completely different stats**. Measured in this corpus:
**476 of 1,157** resolved item names span several item_ids at different tiers.
`Golem Shard Leggings` is the clean case — `13074` "Mythic 10" (Str 45,
armor 703), `1563074` "Heroic" (Str 30, armor 606), `1663074` "Mythic"
(Str 38, armor 633).

**But each variant carries its own item_id**, and that makes `item_id ->
(tier, stats)` a *function*: across 3,919 stat-bearing rows, **0 item_ids
carry more than one distinct stat block, and 0 span more than one tier.**

Two consequences, and they point in opposite directions — keep both:

1. 🛑 **Never map item NAME -> stats.** It is many-valued and will silently
   pick a variant the character never wore. This is the duplicate-name trap
   (primer §2) reappearing in item space, and the crawl's own
   `match_type='name_fallback'` rows are exactly it — carried through as
   `snapshot_gear.stats_match_type` rather than dropped, so they can be
   flagged or excluded.
2. ✅ **Keying on item_id is lossless**, so the deduped `items` table is safe
   as a stat source and the per-character `snapshot_gear` read agrees with it
   by construction. Reading instances is still the right discipline (it is
   what carries slot, enchant and gems), but the dedup is not the hazard —
   the name is.

⚠ **Not established:** whether the numeric relationship between a base id and
its variants (`13074` -> `1563074` / `1663074`) is a decodable scheme. The
prefixes are inconsistent across the corpus, and relating two ids by a pattern
is the same error class as relating two spells by name. Variants are grouped
by NAME + tier as an observation, never derived arithmetically.
"""
import json
import re
from collections import defaultdict

ITEMS_SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    item_id INTEGER PRIMARY KEY,
    name TEXT, quality INTEGER, slot INTEGER, item_level INTEGER,
    stats_json TEXT, sockets_json TEXT,
    drop_source TEXT, source_category TEXT, tier TEXT,
    phase_label TEXT,               -- server phase this becomes available, when known
    provenance TEXT NOT NULL,       -- 'crawl_resolved_bisbeard' | 'client_dbc' | 'manual'
    first_seen_at TEXT, seen_count INTEGER
);
CREATE INDEX IF NOT EXISTS idx_items_slot ON items(slot);
"""

# crawl stat key -> the sim's CharState vocabulary (core/sim/weights.py STAT_SETTERS)
STAT_KEY_MAP = {
    "strength": "strength", "agility": "agility", "intellect": "intellect",
    "stamina": "stamina", "spirit": "spirit",
    "spellPower": "spell_power", "attackPower": "attack_power",
    "feralAttackPower": "feral_attack_power",
    "critRating": "crit_rating", "hitRating": "hit_rating",
    "hasteRating": "haste_rating", "expertise": "expertise_rating",
    "armorPenetration": "armor_pen_rating", "resilienceRating": "resilience_rating",
    "mp5": "mp5", "hp5": "hp5", "armor": "armor",
    "defense": "defense_rating", "dodge": "dodge_rating", "parry": "parry_rating",
    "block": "block_rating", "blockValue": "block_value",
    "shieldBlockValue": "block_value",
    "healingPower": "healing_power", "spellPenetration": "spell_penetration",
    "shadowSpellPower": "shadow_spell_power",
    "fireResist": "fire_resist", "frostResist": "frost_resist",
    "shadowResist": "shadow_resist", "natureResist": "nature_resist",
    "arcaneResist": "arcane_resist",
}


def init_items_schema(conn):
    conn.executescript(ITEMS_SCHEMA)


def build_items_from_gear(conn):
    """Dedupe `snapshot_gear` by item_id into `items`. Owns its own deletion."""
    init_items_schema(conn)
    conn.execute("DELETE FROM items WHERE provenance = 'crawl_resolved_bisbeard'")
    rows = conn.execute("""
        SELECT sg.item_id, MIN(sg.item_name), MIN(sg.quality), MIN(sg.slot),
               MIN(sg.item_level), MIN(sg.stats_json), MIN(sg.gems_json),
               MIN(sg.drop_source), MIN(sg.source_category), MIN(sg.tier),
               MIN(cs.captured_at), COUNT(DISTINCT sg.snapshot_id)
        FROM snapshot_gear sg
        JOIN character_snapshots cs ON cs.snapshot_id = sg.snapshot_id
        WHERE sg.item_id IS NOT NULL
        GROUP BY sg.item_id
    """).fetchall()
    conn.executemany(
        """INSERT OR REPLACE INTO items
             (item_id, name, quality, slot, item_level, stats_json, sockets_json,
              drop_source, source_category, tier, phase_label, provenance,
              first_seen_at, seen_count)
           VALUES (?,?,?,?,?,?,?,?,?,?,?, 'crawl_resolved_bisbeard', ?,?)""",
        [(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9],
          None, r[10], r[11]) for r in rows])
    return {"items": len(rows),
            "with_stats": sum(1 for r in rows if r[5]),
            "provenance": "crawl_resolved_bisbeard"}


def normalise_stats(stats_json):
    """Crawl stat block -> the sim's vocabulary. Unknown keys are RETURNED in
    `unmapped`, never dropped silently — a stat we cannot name is a finding."""
    if not stats_json:
        return {}, []
    raw = json.loads(stats_json) if isinstance(stats_json, str) else stats_json
    out, unmapped = {}, []
    for k, v in raw.items():
        key = STAT_KEY_MAP.get(k)
        if key is None:
            unmapped.append(k)
            continue
        out[key] = out.get(key, 0) + v
    return out, unmapped


# 3.3.5 INVTYPE constants. Numeric, so the one-hand/two-hand question never
# goes through the description's prose.
_INVTYPE_TWO_HAND = 17
_INVTYPE_WEAPON = {13, 17, 21, 22}          # 1h, 2h, main-hand, off-hand
_DAMAGE_RE = re.compile(r"(\d+)\s*-\s*(\d+)\s+Damage\s+Speed\s+([\d.]+)")
_DPS_RE = re.compile(r"\(([\d.]+)\s+damage per second\)")


def parse_weapon_damage(description, inventory_type):
    """Weapon min/max/speed, read from the crawl's rendered item description.

    🛑 **Weapon damage is in NO stat block.** `resolved_bisbeard.stats` never
    carries it and `resolved_bisbeard.damage` is null on all 1,413 weapon-slot
    entries in the corpus — so a crawled character built from stat blocks alone
    is simmed **with no weapon at all**, zeroing every white swing and every
    weapon-percent ability. The numbers exist only in the rendered description
    (`63 - 107 Damage   Speed 2.60`).

    ⚠ This is NOT the banned "read a magnitude from a description string" rule
    (CLAUDE.md). That rule is about **DBC** descriptions, which are tooltip
    TEMPLATES carrying `$` variables and hand-rolled level scaling — the class
    of thing that renders Hammer from the Heavens as "194 to 147". This is a
    third party's already-rendered item text with literal integers, and it
    ships its own check digit: the same string states the weapon's DPS, so
    `(min+max)/2/speed` must reproduce it.

    **That check is enforced, not assumed** — a parse that fails it returns
    None rather than a number. Validated across the whole corpus: 849 of 849
    parsed weapons agree within 3% (the residual is the displayed speed being
    rounded to one decimal; at a 0.15 absolute band 110 look like mismatches
    and every one of them is display rounding).

    Speed is taken from the STATED DPS rather than the displayed speed, since
    `(min+max)/2/dps` is the more precise of the two — the displayed 1.4 could
    be anything from 1.35 to 1.44.
    """
    if not description or inventory_type not in _INVTYPE_WEAPON:
        return None
    m = _DAMAGE_RE.search(description)
    if not m:
        return None                      # shields, holdables, relics, tomes
    lo, hi, shown_speed = int(m.group(1)), int(m.group(2)), float(m.group(3))
    if hi < lo or shown_speed <= 0:
        return None
    d = _DPS_RE.search(description)
    if not d:
        return None                      # no check digit -> no number
    stated_dps = float(d.group(1))
    if stated_dps <= 0:
        return None
    if abs((lo + hi) / 2 / shown_speed - stated_dps) / stated_dps > 0.03:
        return None                      # self-inconsistent: refuse, don't guess
    return {
        "min": lo, "max": hi,
        "speed": round((lo + hi) / 2 / stated_dps, 3),
        "hand": "2h" if inventory_type == _INVTYPE_TWO_HAND else "1h",
        "dps": stated_dps,
        "displayed_speed": shown_speed,
        "source": "crawl_item_description (self-checked against stated DPS)",
    }


# Slots that legitimately carry no stats, so a NULL stat block there is not a
# resolution miss. Measured, not assumed: across the whole corpus these two
# slots resolve 0 of 209 (shirt) and 0 of 87 (tabard) stat blocks, while every
# other slot resolves the majority of its rows.
COSMETIC_SLOTS = {4, 19}


def gear_coverage(conn, snapshot_id):
    """How much of a snapshot's stat-bearing gear actually resolved to stats.

    A character with unresolved pieces is simmed at **too-low stats**, which
    produces the same one-directional negative delta as a missing buff or a
    missing ability magnitude — so a calibration miss cannot be attributed
    until this number is known per character. That is the whole reason this
    exists (PLAN_3B §3.4).

    Coverage is *reportable but not fixable from within the corpus*: an
    unresolved item is unresolved everywhere (measured — 0 of 592 unresolved
    item_ids resolve on any other snapshot), because those ids are simply
    absent from the upstream item database. There is no backfill to do here,
    only an honest number to carry.
    """
    rows = conn.execute(
        "SELECT slot, item_id, item_name, stats_json, stats_match_type "
        "FROM snapshot_gear WHERE snapshot_id = ?", (snapshot_id,)).fetchall()
    stat_bearing = [r for r in rows if r[0] not in COSMETIC_SLOTS]
    resolved = [r for r in stat_bearing if r[3]]
    missing = [{"slot": r[0], "item_id": r[1], "name": r[2]}
               for r in stat_bearing if not r[3]]
    name_matched = [{"slot": r[0], "item_id": r[1], "name": r[2]}
                    for r in resolved if r[4] == "name_fallback"]
    return {
        "slots_present": len(rows),
        "stat_bearing_slots": len(stat_bearing),
        "resolved": len(resolved),
        "coverage_pct": (100.0 * len(resolved) / len(stat_bearing)
                         if stat_bearing else None),
        "missing": missing,
        "cosmetic_slots_skipped": len(rows) - len(stat_bearing),
        # a stat block matched on NAME may belong to a different difficulty
        # variant of the same item — see this module's header
        "name_matched": name_matched,
    }


def missing_stat_budget_bound(conn, snapshot_id, *, coverage=None,
                              slot_medians=None):
    """An ESTIMATED upper-ish bound on the stat budget a snapshot is missing.

    🛑 This is an estimate with a stated method, for **decomposing a
    calibration miss only**. It is never added to a character's stats and
    never enters a sim run — doing that would be fitting the gate.

    Method: each unresolved piece is credited the MEDIAN stat budget of the
    resolved pieces in the same slot across the corpus. Median (not mean, not
    max) because the unresolved ids are dominated by levelling greens, so a
    max would inflate the bound and a mean is skewed by the Ascended tail.
    The returned `basis` names the method so the number is never read as
    measured.
    """
    cov = coverage or gear_coverage(conn, snapshot_id)
    if not cov["missing"]:
        return {"missing_pieces": 0, "estimated_missing_budget": 0.0,
                "resolved_budget": _snapshot_budget(conn, snapshot_id),
                "basis": "no unresolved pieces"}
    medians = slot_medians if slot_medians is not None else slot_budget_medians(conn)
    est = sum(medians.get(m["slot"], 0.0) for m in cov["missing"])
    resolved_budget = _snapshot_budget(conn, snapshot_id)
    total = resolved_budget + est
    return {
        "missing_pieces": len(cov["missing"]),
        "resolved_budget": round(resolved_budget, 1),
        "estimated_missing_budget": round(est, 1),
        "estimated_budget_shortfall_pct": (round(100.0 * est / total, 1)
                                           if total else None),
        "slots_without_a_corpus_median": sorted(
            {m["slot"] for m in cov["missing"] if m["slot"] not in medians}),
        "basis": "estimated: per-slot MEDIAN resolved stat budget across the "
                 "corpus, credited to each unresolved piece. Not measured, "
                 "not applied to any sim run.",
    }


# stats excluded from a "budget": they do not convert into throughput, so
# including them would let a tank's plate outrank a caster's whole set.
_NON_THROUGHPUT = {"armor", "hp5", "fire_resist", "frost_resist",
                   "shadow_resist", "nature_resist", "arcane_resist"}


def _block_budget(stats):
    return sum(v for k, v in stats.items() if k not in _NON_THROUGHPUT)


def _snapshot_budget(conn, snapshot_id):
    total = 0.0
    for (stats_json,) in conn.execute(
            "SELECT stats_json FROM snapshot_gear "
            "WHERE snapshot_id = ? AND stats_json IS NOT NULL", (snapshot_id,)):
        mapped, _unmapped = normalise_stats(stats_json)
        total += _block_budget(mapped)
    return total


def slot_budget_medians(conn):
    """Median resolved stat budget per slot, corpus-wide. Full scan — compute
    once and pass it into `missing_stat_budget_bound` when looping."""
    by_slot = defaultdict(list)
    for slot, stats_json in conn.execute(
            "SELECT slot, stats_json FROM snapshot_gear "
            "WHERE stats_json IS NOT NULL"):
        mapped, _unmapped = normalise_stats(stats_json)
        by_slot[slot].append(_block_budget(mapped))
    out = {}
    for slot, budgets in by_slot.items():
        budgets.sort()
        out[slot] = budgets[len(budgets) // 2]
    return out


def gear_tier_stats(conn, *, path=None, role=None, tiers=(("fresh", 0.25),
                                                          ("mid", 0.50),
                                                          ("bis", 0.90))):
    """Fresh / mid / BiS stat blocks, MEASURED from what characters wear.

    Not a hand-invented curve: characters are ranked by the **total stat budget
    their gear actually carries**, and each tier is the stat block of the
    character at that percentile. That keeps the three tiers internally
    consistent (a real person wore all of it) instead of summing per-slot
    bests, which produces a set nobody has.

    ⚠ Ranking deliberately does NOT use `item_level`: it is NULL on most
    crawled rows, so an ilvl ranking sorts by *how much metadata resolved*
    rather than by gear quality — the fresh and mid tiers came back with EMPTY
    stat blocks, which is what caught it.

    ⚠ Phase parameterisation: the corpus is currently all Phase 1, so
    `phase_label` is NULL everywhere and this function does not filter on it.
    S10 Phase 2 starts 2026-08-08; once snapshots straddle the flip, tiers MUST
    be computed per phase or a Phase-1 BiS will be reported as current.
    """
    sql = """
        SELECT cs.snapshot_id, cs.character_id, cs.path,
               COUNT(sg.item_id) AS pieces
        FROM character_snapshots cs
        JOIN snapshot_gear sg ON sg.snapshot_id = cs.snapshot_id
        WHERE sg.stats_json IS NOT NULL
    """
    params = []
    if path:
        sql += " AND lower(cs.path) = lower(?)"
        params.append(path)
    if role:
        sql += " AND lower(COALESCE(cs.spec_role,'')) LIKE lower(?)"
        params.append(f"%{role}%")
    sql += " GROUP BY cs.snapshot_id HAVING pieces >= 12"

    all_unmapped = set()
    scored = []
    for snapshot_id, character_id, snap_path, pieces in conn.execute(sql, params):
        block = defaultdict(float)
        for (stats_json,) in conn.execute(
                "SELECT stats_json FROM snapshot_gear WHERE snapshot_id = ?",
                (snapshot_id,)):
            mapped, unmapped = normalise_stats(stats_json)
            all_unmapped.update(unmapped)
            for k, v in mapped.items():
                block[k] += v
        # budget = the stats a build actually converts into throughput; armor,
        # resistances and health regen are excluded so a tank's plate does not
        # outrank a caster's whole set.
        budget = sum(v for k, v in block.items()
                     if k not in {"armor", "hp5", "fire_resist", "frost_resist",
                                  "shadow_resist", "nature_resist", "arcane_resist"})
        scored.append((budget, snapshot_id, character_id, snap_path, pieces, block))
    scored.sort(key=lambda r: r[0])

    if len(scored) < 8:
        return {"verdict": "insufficient_sample", "population": len(scored),
                "tiers": {}}

    out = {}
    for label, pct in tiers:
        budget, snapshot_id, character_id, snap_path, pieces, block = \
            scored[min(len(scored) - 1, int(len(scored) * pct))]
        out[label] = {
            "percentile": pct, "snapshot_id": snapshot_id,
            "character_id": character_id, "path": snap_path,
            "gear_stat_budget": round(budget, 1), "pieces": pieces,
            "stats": {k: round(v, 1) for k, v in sorted(block.items())},
        }
    return {"verdict": "ok", "population": len(scored), "tiers": out,
            "unmapped_stat_keys": sorted(all_unmapped),
            "provenance": "crawl_resolved_bisbeard",
            "caveat": "single-phase corpus; re-derive per phase after 2026-08-08"}


def export_stat_weights(weights, *, target="bisbeard", normalise_to=None):
    """Emit derived weights in an external optimizer's input format.

    BisBeard's chunk exposes `weightString`, `configStatWeights`,
    `normalizedWeights` — the encoding itself is NOT documented anywhere we can
    read, and Phase 0 stopped short of probing for it. So this emits the two
    forms that are unambiguous: a `key=value` string and JSON. If the real
    `weightString` grammar is ever learned, add it as another target rather
    than guessing at it now.
    """
    if normalise_to and normalise_to in weights and weights[normalise_to]:
        base = weights[normalise_to]
        weights = {k: v / base for k, v in weights.items()}
    ordered = sorted(weights.items(), key=lambda kv: -abs(kv[1]))
    if target == "json":
        return json.dumps({k: round(v, 4) for k, v in ordered}, indent=1)
    if target == "bisbeard":
        return ",".join(f"{k}={v:.4f}" for k, v in ordered if v)
    raise ValueError(f"unknown target {target!r} — add it rather than guessing "
                     f"at an undocumented encoding")


def rank_items(conn, slot, stat_weights, *, limit=20, min_seen=1):
    """Items in a slot scored by our own weights. A REPORT, not an optimizer —
    it exists to cross-validate weights against `item_usage()` (Task 3): if the
    weight-ranked list disagrees with what every top performer wears, the
    weights or the item data are wrong, and that is a finding either way.

    ⚠ **Weapon damage is not in `stats_json`**, so for weapon slots this score
    omits the single largest term (the build doc weights it 2.6). A weapon
    ranking from this function is a stat-stick ranking and must not be read as
    a weapon ranking — which is exactly why it disagrees with `item_usage` on
    slot 16."""
    out = []
    for item_id, name, stats_json, ilvl, seen, tier in conn.execute(
            "SELECT item_id, name, stats_json, item_level, seen_count, tier "
            "FROM items WHERE slot = ? AND stats_json IS NOT NULL AND seen_count >= ?",
            (slot, min_seen)):
        stats, _unmapped = normalise_stats(stats_json)
        score = sum(stat_weights.get(k, 0.0) * v for k, v in stats.items())
        out.append({"item_id": item_id, "name": name, "item_level": ilvl,
                    "tier": tier, "wearers": seen, "score": round(score, 1),
                    "stats": stats})
    out.sort(key=lambda r: r["score"], reverse=True)
    return out[:limit]
