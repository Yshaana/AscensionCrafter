#!/usr/bin/env python3
"""Resolve spell magnitudes from the client's NUMERIC DBC fields (session `1x`).

    py ingest/dbc/resolve_numeric_formulas.py

Runs off the committed extract — **no game client needed** — because
`load_extract.py` has already put `spell_dbc_raw` in the database.

## Why this exists

887 catalog entries are flagged `has_hidden_formula=1`: their export tooltip
interpolates a sub-spell id that the export itself does not contain, so the real
magnitude is invisible. The existing resolver (in `build_dbc_index.py`) runs a
regex over that sub-spell's **description text**, which finds a coefficient in 84
of them and nothing at all in 803.

Phase 0 measured that 98% of the 803 would resolve from numeric fields instead.
This is that extractor, and it lands **794 of the 887** (the remaining 93 carry no
numeric magnitude anywhere in their refs — debuff and immunity markers, which is
what Phase 0 predicted for its own 15). It reads `EffectBasePoints`, `EffectDieSides`,
`EffectRealPointsPerLevel` and `EffectPointsPerCombo` — 🛑 **never the description
string**, which is §2.2 tier 4's rule and the Titanic Mutilate trap in code.

## What it does NOT do, deliberately

* **It does not clear `has_hidden_formula`.** That flag means "the export's tooltip
  points at a sub-spell the export does not have", which stays true whether or not
  we resolved the number elsewhere. Clearing it is also exactly the shape of the
  idempotency bug Phase 0 found three times — a flag that scopes the next run's
  target set, mutated by this run.
* **It does not write SP/AP rows into `spell_scaling`.** `EffectBonusCoefficient`
  is not the SP/AP coefficient (7,647 of 9,211 non-zero values are the 1.0
  default; it agrees with a spell's own stated coefficient in 4 of 98 cases). It is
  stored under its real name, `bonus_multiplier`. See `core/spells/dbc_numeric.py`.
* **It does not re-key `spell_scaling` by rank**, though session `1x` established
  that it needs to be. Owner decision 2026-08-04: record and flag here, migrate in
  T4 (session `1b`), which rebuilds the table anyway.

It owns the deletion of its own output, so re-running is a replace.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from config import DATA_DERIVED, DB_PATH  # noqa: E402
from core.db.connection import connect, table_exists, transaction  # noqa: E402
from core.db.schema import create_phase1_schema  # noqa: E402
from core.spells import dbc_numeric as dn  # noqa: E402
from core.spells import rank_scaling as rs  # noqa: E402
from core.spells.text_extraction import SUBSPELL_REF_PAT  # noqa: E402

REALM = "Darkmoon"
SEASON = "S10"
SOURCE_TIER = "dbc_numeric_field"
REPORT_PATH = DATA_DERIVED / "numeric_extraction_report.md"

# Flat magnitudes already established INDEPENDENTLY of the DBC — from live tooltips
# and build docs — used to prove the base_points+1 convention still decodes
# correctly after a client patch. Same role as build_dbc_index.py's
# VALIDATION_SPELLS, for the numeric side rather than the text side.
VALIDATION = [
    (12329, 0, 40.0, "Improved Cleave R1 = +40% (build_paladin-hammerdin v9)"),
    (12950, 0, 80.0, "Improved Cleave R2 = +80%"),
    (20496, 0, 120.0, "Improved Cleave R3 = +120%"),
    (31884, 0, 20.0, "Avenging Wrath = +20% all damage (v10)"),
    (53385, 0, 110.0, "Divine Storm = 110% weapon damage (v10)"),
    (498, 1, -50.0, "Divine Protection = -50% damage taken (v10)"),
    (276082, 0, 15.0, "Fel Infused Weapon 2H bonus = +15% (INDEX_GUIDE v6)"),
    # 2c G4: the rank-sibling sub-spell chain. 25902 is reachable ONLY by parsing
    # Holy Shock R4's own DBC description — it is not a catalog id, not an export
    # hidden_ref, and not an EffectTriggerSpell target. If a future extraction
    # narrows the scope again, this is the check that fails instead of Holy Shock
    # silently reverting to zero damage.
    (25902, 0, 562.0, "Holy Shock R4 damage sub-spell (2c G4 rank-sibling chain)"),
    (25903, 0, 676.0, "Holy Shock R4 healing sub-spell (2c G4 rank-sibling chain)"),
]


def latest_patch_id(conn):
    row = conn.execute(
        "SELECT patch_id FROM patches WHERE realm = ? ORDER BY patch_date DESC LIMIT 1",
        (REALM,)).fetchone()
    return row[0] if row else None


def validate(conn):
    """Fail loudly if the flat-value convention stops reproducing known facts."""
    failures = []
    for spell_id, index, expected, label in VALIDATION:
        row = conn.execute("SELECT effect_json FROM spell_dbc_raw WHERE id = ?",
                           (spell_id,)).fetchone()
        if row is None:
            failures.append(f"{spell_id}: absent from spell_dbc_raw ({label})")
            continue
        decoded = dn.decode_effect(json.loads(row[0]), index)
        if decoded["flat_min"] != expected:
            failures.append(
                f"{spell_id} effect{index}: decoded {decoded['flat_min']}, "
                f"expected {expected} - {label}")
    return failures


def rank_sibling_targets(conn, level=60):
    """Level-appropriate rank siblings that are NOT catalog entries (session 2b).

    Why this is needed, and why its absence was invisible until the sim ran:
    the catalog stores Rank 1 for ~half of all multi-rank cards, so the resolver
    correctly redirects a query to the id a level-60 character actually casts —
    but this extractor only ever decoded CATALOG ids, so the redirect landed on a
    spell with no `spell_effect_values` rows at all. The resolver traded a WRONG
    magnitude for NO magnitude, and every affected ability silently simmed as 0.
    686 catalog cards were in that state, all of them present in `spell_dbc_raw`
    and therefore decodable the whole time.

    🛑 Ambiguous rank lines are SKIPPED, not tie-broken — `catalog_rank_gaps`
    returns every candidate precisely so nobody picks one by list order.
    """
    from core.spells.ranks import catalog_rank_gaps
    targets = {}
    skipped_ambiguous = []
    for gap in catalog_rank_gaps(conn, level=level):
        if gap["ambiguous"]:
            skipped_ambiguous.append(gap["catalog_spell_id"])
            continue
        cand = gap["candidates"][0]
        if not cand["in_catalog"]:
            targets[cand["spell_id"]] = gap["catalog_spell_id"]
    return targets, skipped_ambiguous


def sibling_hidden_refs(raw, sibling_id):
    """Sub-spell ids a rank sibling's OWN DBC description points at (session 2c, G4).

    A sibling inherits no `hidden_refs`, because that column is parsed from the
    export tooltip and a sibling is by definition absent from the export. When
    the sibling's own record is a DUMMY holding its magnitude in a sub-spell,
    that left the ability with no magnitude at all — Holy Shock R4 (20930) is the
    live case, and it simmed as 0 damage against 36 real casts.

    🛑 **This reads a POINTER, not a magnitude.** The project's rule is that a
    number must never come from a `description` string (the Titanic Mutilate
    trap, where the text said 115% and the numeric field said 70%). A `$25902s1`
    token is a spell id; the magnitude is still decoded from *that* spell's
    numeric fields. The export-tooltip `hidden_refs` path has always worked this
    way — this is the same mechanism on the DBC's copy of the same text, which is
    the only place the link is recorded for a spell the export never saw.
    """
    entry = raw.get(sibling_id)
    if entry is None:
        return []
    return sorted({int(m.group(1))
                   for m in SUBSPELL_REF_PAT.finditer(entry[2] or "")
                   if int(m.group(1)) != sibling_id})


def collect_rows(conn, patch_id, now, level=60):
    """One row per usable effect slot, for every catalog spell, its hidden refs,
    and the level-appropriate rank siblings catalog entries redirect to."""
    raw = {r[0]: (r[1], r[2], r[3]) for r in conn.execute(
        "SELECT id, effect_json, source_archive, description FROM spell_dbc_raw")}

    rows = []
    seen = set()
    stats = {"self": 0, "hidden_ref": 0, "rank_sibling": 0,
             "sibling_hidden_ref": 0, "catalog_covered": set(),
             "sibling_covered": set(), "sibling_ambiguous": [],
             "sibling_rescued": set(),
             "blocked_resolved": set(), "blocked_empty": set()}

    catalog = conn.execute("SELECT id, hidden_refs, has_hidden_formula FROM spells").fetchall()
    siblings, ambiguous = rank_sibling_targets(conn, level=level)
    stats["sibling_ambiguous"] = ambiguous
    # Siblings carry no `hidden_refs` from the export — see `sibling_hidden_refs`,
    # which recovers them from the sibling's OWN DBC description instead (2c G4).
    # Anything a sibling reaches by trigger is still picked up separately by the
    # bounded walk in core/spells/relationships.py.
    catalog = list(catalog) + [
        (sid, ",".join(str(r) for r in sibling_hidden_refs(raw, sid)) or None, 0)
        for sid in sorted(siblings)]

    for spell_id, hidden_refs, blocked in catalog:
        sources = [(spell_id, "self")]
        ref_ids = [int(x) for x in (hidden_refs or "").split(",") if x.strip()]
        sources += [(rid, "hidden_ref") for rid in ref_ids]

        found_any = False
        for source_id, via in sources:
            entry = raw.get(source_id)
            if entry is None:
                continue
            effect_json, archive = entry[0], entry[1]
            for decoded in dn.decode_effects(json.loads(effect_json)):
                key = (spell_id, source_id, decoded["effect_index"])
                if key in seen:
                    continue
                seen.add(key)
                if spell_id in siblings:
                    stats["sibling_hidden_ref" if via == "hidden_ref"
                          else "rank_sibling"] += 1
                    stats["sibling_rescued"].add((spell_id, via))
                else:
                    stats[via] += 1
                found_any = True
                rows.append((
                    spell_id, source_id, decoded["effect_index"], via,
                    decoded["effect_type"], decoded["effect_aura"],
                    decoded["base_points"], decoded["die_sides"],
                    decoded["flat_min"], decoded["flat_max"],
                    decoded["per_level"], decoded["per_combo"],
                    decoded["bonus_multiplier"], decoded["trigger_spell"],
                    decoded["misc_value"], decoded["misc_value_b"],
                    decoded["radius_index"], decoded["aura_period"],
                    decoded["chain_targets"],
                    SOURCE_TIER,
                    dn.evidence_ref(source_id, decoded["effect_index"], archive),
                    "confirmed", REALM, SEASON, patch_id, now,
                ))
        if found_any:
            (stats["sibling_covered"] if spell_id in siblings
             else stats["catalog_covered"]).add(spell_id)

        if blocked:
            # did the HIDDEN REF specifically yield a magnitude? that is the 803's
            # question - the spell's own effects resolving is not the same win
            ref_hit = any(
                any(d["flat_min"] is not None or d["per_level"] or d["per_combo"]
                    for d in dn.decode_effects(json.loads(raw[rid][0])))
                for rid in ref_ids if rid in raw)
            (stats["blocked_resolved"] if ref_hit else stats["blocked_empty"]).add(spell_id)

    # ------------------------------------------------------------------ 2e
    # Fourth source class: every REMAINING extracted spell, decoded under its own
    # id with NO attribution claim (`spell_id == source_spell_id`).
    #
    # 🚨 Why this exists. The three classes above are all reached FROM the
    # catalog — a card, its export hidden_refs, its rank sibling. Anything the
    # game reaches by a *different* route is extracted and then never read:
    #   * a seal's proc target      (20375 -> 20424 Seal of Command's damage)
    #   * a judgement's real spell  (20467, selected by the active seal)
    #   * an out-of-catalog version (270767/270768, Purification By Light's own)
    #   * a talent's damage spell   (16459 Sword Specialization, 913445 Blades of Light)
    #   * an imbue's hidden carrier (200819 Consecrated Holy Weapon Hidden)
    # `2e` measured 11,417 of 16,566 `spell_dbc_raw` rows in that state, holding
    # intact numeric fields the resolver simply never looked at. Combat logs name
    # spell ids directly, so the sim resolves exactly these ids — and got nothing.
    #
    # This is the same failure as `2b`'s "rank siblings had NO magnitudes, 686
    # cards silently simmed as 0" and `1x`'s "98% of blocked hidden-formula
    # spells resolve from numeric fields": the data was present and in scope the
    # whole time; the QUERY was narrow.
    #
    # 🛑 Attribution discipline is preserved, not relaxed. These rows say "spell
    # X has magnitude M", never "card C deals M". Card attribution stays with the
    # bounded trigger walk in core/spells/relationships.py (`via='trigger_hopN'`,
    # always `inferred`). A consumer that wants only card-owned damage filters
    # `via IN ('self','hidden_ref')` exactly as before.
    covered = {r[0] for r in rows}
    for source_id, entry in sorted(raw.items()):
        if source_id in covered:
            continue
        for decoded in dn.decode_effects(json.loads(entry[0])):
            key = (source_id, source_id, decoded["effect_index"])
            if key in seen:
                continue
            seen.add(key)
            stats["dbc_only"] = stats.get("dbc_only", 0) + 1
            stats.setdefault("dbc_only_covered", set()).add(source_id)
            rows.append((
                source_id, source_id, decoded["effect_index"], "dbc_only",
                decoded["effect_type"], decoded["effect_aura"],
                decoded["base_points"], decoded["die_sides"],
                decoded["flat_min"], decoded["flat_max"],
                decoded["per_level"], decoded["per_combo"],
                decoded["bonus_multiplier"], decoded["trigger_spell"],
                decoded["misc_value"], decoded["misc_value_b"],
                decoded["radius_index"], decoded["aura_period"],
                decoded["chain_targets"],
                SOURCE_TIER,
                dn.evidence_ref(source_id, decoded["effect_index"], entry[1]),
                "confirmed", REALM, SEASON, patch_id, now,
            ))

    # The G4 rescue set: siblings that have magnitudes ONLY because their own DBC
    # description was followed. Before this, each of these resolved to no events
    # at all, and the sim scored the ability as zero damage.
    by_sibling = {}
    for sid, via in stats["sibling_rescued"]:
        by_sibling.setdefault(sid, set()).add(via)
    stats["sibling_rescued"] = {sid for sid, vias in by_sibling.items()
                                if vias == {"hidden_ref"}}

    return rows, stats


def write_rows(conn, rows):
    # 🛑 Delete only the rows THIS script owns. `spell_effect_values` has a second
    # writer: core/spells/relationships.py adds the bounded trigger-attribution
    # rows (`via='trigger_hopN'`), and it correctly scopes its own delete the same
    # way. An unscoped `DELETE FROM spell_effect_values` here silently destroyed
    # them — and because the rebuild runs this step BEFORE relationships, the
    # chain hid it completely; it only appeared on a standalone re-run, which the
    # docstring explicitly invites ("re-running is a replace"). Cost: every
    # trigger-reached ability resolved to no events, Hammer from the Heavens —
    # the owner's top damage source — among them. Same family as the three
    # idempotency bugs Phase 0 found, inverted: not a script that fails to delete
    # its own output, but one that deletes output it does not own.
    # ⚠ `dbc_only` (session 2e) is a THIRD via this script owns — it must be in
    # this list or the rows leak across runs and the script stops being idempotent.
    conn.execute("DELETE FROM spell_effect_values "
                 "WHERE via IN ('self', 'hidden_ref', 'dbc_only')")
    conn.executemany(
        "INSERT INTO spell_effect_values VALUES (" + ",".join("?" * 26) + ")", rows)


def rank_report(conn):
    """Both halves of the rank-vs-coefficient question, at scale."""
    counts = {"numeric": {}, "text": {}, "ramps": 0, "lines": 0}
    for _line_id, _name, _members, verdict in rs.scan_rank_lines(conn):
        counts["lines"] += 1
        counts["numeric"][verdict["numeric"]] = counts["numeric"].get(verdict["numeric"], 0) + 1
        counts["text"][verdict["text"]] = counts["text"].get(verdict["text"], 0) + 1
        counts["ramps"] += bool(verdict["ramps_then_plateaus"])

    owned = rs.owned_spell_ids(conn)
    gaps = list(rs.catalog_coefficient_gaps(conn))
    differing = [g for g in gaps if g["verdict"] == "differs"]
    for g in differing:
        g["owned"] = g["catalog_spell_id"] in owned
    return counts, gaps, differing


def render_report(stats, counts, gaps, differing, validation_failures):
    verdicts = {}
    for g in gaps:
        verdicts[g["verdict"]] = verdicts.get(g["verdict"], 0) + 1

    lines = [
        "# Numeric-field extraction + rank-vs-coefficient — session `1x`",
        "",
        f"Generated {datetime.now(timezone.utc).isoformat(timespec='seconds')} "
        f"from the committed client extract. Regenerate with "
        "`py ingest/dbc/resolve_numeric_formulas.py`.",
        "",
        "## 1. Coverage",
        "",
        "| | count |",
        "|---|---|",
        f"| catalog spells with at least one decoded numeric effect | "
        f"{len(stats['catalog_covered'])} |",
        f"| effect rows decoded from the spell's own record | {stats['self']} |",
        f"| effect rows decoded from a hidden sub-spell | {stats['hidden_ref']} |",
        f"| **rank siblings** covered (the level-60 id a catalog entry redirects "
        f"to) | **{len(stats['sibling_covered'])}** |",
        f"| effect rows decoded from a rank sibling | {stats['rank_sibling']} |",
        f"| effect rows decoded from a rank sibling's **own sub-spell** (2c G4) | "
        f"{stats['sibling_hidden_ref']} |",
        f"| siblings that have a magnitude ONLY via that path | "
        f"**{len(stats['sibling_rescued'])}** |",
        f"| rank lines SKIPPED as ambiguous (never tie-broken) | "
        f"{len(stats['sibling_ambiguous'])} |",
        f"| `has_hidden_formula` spells whose hidden ref yielded a magnitude | "
        f"**{len(stats['blocked_resolved'])}** |",
        f"| `has_hidden_formula` spells still with no numeric magnitude | "
        f"{len(stats['blocked_empty'])} |",
        "",
        "⚠ `has_hidden_formula` is deliberately **not** cleared by this script — the "
        "flag records that the *export* cannot see the formula, which stays true.",
        "",
        "## 2. 🚨 `EffectBonusCoefficient` is not the SP/AP coefficient",
        "",
        "Stock 3.3.5's `EffectBonusMultiplier`, whose neutral value is 1.0: **7,647 of "
        "9,211** non-zero values are exactly 1.0, and the recurring non-default values "
        "are retail's cast-time formula (0.429 = 1.5/3.5, 0.714 = 2.5/3.5). Calibrated "
        "against 98 spells stating their own `$SP*x`/`$AP*x`, it agrees **4 times**.",
        "",
        "Phase 0's *\"311 blocked spells carry a non-zero `EffectBonusCoefficient` "
        "(SP/AP scaling)\"* counted right and read the field wrong: of the 343 blocked "
        "spells whose refs carry any coefficient, **270 carry only 1.0**. Stored as "
        "`bonus_multiplier`, never emitted as SP or AP.",
        "",
        "## 3. Do coefficients scale with rank? — **yes**",
        "",
        f"Scanned {counts['lines']} multi-rank lines with 2+ members in `spell_dbc_raw`.",
        "",
        "| evidence | constant | varies | no data |",
        "|---|---|---|---|",
        f"| numeric `EffectBonusCoefficient` (tier 4) | {counts['numeric'].get('constant', 0)} | "
        f"**{counts['numeric'].get('varies', 0)}** | {counts['numeric'].get('no_data', 0)} |",
        f"| tooltip `$SP*`/`$AP*` literals (tier 6) | {counts['text'].get('constant', 0)} | "
        f"**{counts['text'].get('varies', 0)}** | {counts['text'].get('no_data', 0)} |",
        "",
        f"{counts['ramps']} of the varying lines follow retail's **ramp-then-plateau** "
        "shape — the coefficient is penalised at low ranks and settles at higher ones. "
        "That is what makes this dangerous rather than academic: the catalog stores "
        "**Rank 1** for ~697 entries, which is exactly where the penalty is deepest.",
        "",
        "❌ **Retracts Phase 0's conclusion** that *\"reading a coefficient off the "
        "catalog's Rank-1 entry is probably safe\"* — derived from one line "
        "(Holy Supernova), which happens to be one of the constant ones.",
        "",
        "### Catalog entries whose stored coefficient is not the one they cast",
        "",
        "| verdict | count |",
        "|---|---|",
    ]
    for verdict, count in sorted(verdicts.items(), key=lambda kv: -kv[1]):
        lines.append(f"| `{verdict}` | {count} |")
    unresolved = verdicts.get("live_text_unresolved", 0) + \
        verdicts.get("catalog_text_unresolved", 0)
    lines += [
        "",
        f"**{len(differing)} entries differ** — meaning both ranks state a coefficient "
        "and the two disagree. That is the only verdict here that is evidence.",
        "",
        f"⚠ A further {unresolved} entries are `*_text_unresolved`: one rank states a "
        "coefficient and the other's text yields none. **These are not differences.** "
        "Three causes, all observed: a compound form the regex cannot read "
        "(`($SP+$AP)*0.36`, Bone Arrow); a formula that moved into a sub-spell "
        "(`$71791m1`, Deep Freeze); and a rank line that pulled in a different ability "
        "of the same name (Blood Drinker). Counting them would have reported 15 "
        "differences instead of 7.",
        "",
        "| card | catalog id | level-60 id | catalog SP/AP | level-60 SP/AP |",
        "|---|---|---|---|---|",
    ]

    def fmt(terms):
        if not terms:
            return "—"
        parts = [f"{k} {'/'.join(str(v) for v in vals)}"
                 for k, vals in terms.items() if vals]
        return ", ".join(parts) or "—"

    for g in sorted(differing, key=lambda g: g["name"]):
        lines.append(
            f"| {g['name']} | {g['catalog_spell_id']} | {g['live_spell_id']} | "
            f"{fmt(g['catalog_text'])} | {fmt(g['live_text'])} |")
    owned_n = sum(1 for g in differing if g["owned"])
    lines += [
        "",
        f"{owned_n} of the {len(differing)} are cards the owner holds — but he owns "
        "2,965 of 3,061 catalog cards, so that is the base rate, not a signal.",
    ]

    lines += [
        "",
        "**Schema consequence:** `spell_scaling` needs rank keying. The migration is "
        "T4's (session `1b`), which rebuilds the table anyway — owner decision "
        "2026-08-04 was record-and-flag here, not migrate.",
        "",
        "## 4. Validation",
        "",
    ]
    if validation_failures:
        lines.append("🚨 **FAILED** — the flat-value convention no longer reproduces "
                     "known facts:")
        lines += [f"* {f}" for f in validation_failures]
    else:
        lines.append(f"✅ {len(VALIDATION)} independently-established flat magnitudes "
                     "still decode correctly via `base_points + 1`.")
    return "\n".join(lines) + "\n"


def main():
    if not DB_PATH.exists():
        print(f"no database at {DB_PATH} - run py cli/rebuild.py first", file=sys.stderr)
        return 1

    conn = connect(DB_PATH)
    if not table_exists(conn, "spell_dbc_raw"):
        print("spell_dbc_raw missing - run ingest/dbc/load_extract.py first", file=sys.stderr)
        return 1

    create_phase1_schema(conn)

    failures = validate(conn)
    if failures:
        print("VALIDATION FAILED - numeric decoding regressed against known facts:",
              file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1
    print(f"validation OK: {len(VALIDATION)} known flat magnitudes decode correctly")

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    patch_id = latest_patch_id(conn)

    with transaction(conn):
        rows, stats = collect_rows(conn, patch_id, now)
        write_rows(conn, rows)

    print(f"spell_effect_values: {len(rows)} rows "
          f"({stats['self']} from the spell's own record, "
          f"{stats['hidden_ref']} from hidden sub-spells, "
          f"{stats['rank_sibling']} from rank siblings, "
          f"{stats.get('dbc_only', 0)} unattributed dbc_only)")
    print(f"  unattributed spells now carrying a magnitude (2e): "
          f"{len(stats.get('dbc_only_covered', ()))} — these are reached by "
          f"seal/judgement/enchant/talent routes, not from the catalog, and "
          f"combat logs name them directly")
    print(f"catalog spells with a decoded numeric effect: {len(stats['catalog_covered'])}")
    print(f"rank siblings covered (the id a level-60 character actually casts): "
          f"{len(stats['sibling_covered'])}"
          f"; {len(stats['sibling_ambiguous'])} ambiguous lines skipped, not tie-broken")
    print(f"  of which {len(stats['sibling_rescued'])} have a magnitude ONLY via "
          f"their own DBC sub-spell refs ({stats['sibling_hidden_ref']} rows) — "
          f"these resolved to zero damage before 2c's G4 fix")
    print(f"has_hidden_formula spells resolved from numeric fields: "
          f"{len(stats['blocked_resolved'])} "
          f"(still empty: {len(stats['blocked_empty'])})")

    counts, gaps, differing = rank_report(conn)
    print(f"\nrank scan: {counts['lines']} multi-rank lines")
    print(f"  numeric coefficient  constant {counts['numeric'].get('constant', 0)} / "
          f"varies {counts['numeric'].get('varies', 0)} / "
          f"no data {counts['numeric'].get('no_data', 0)}")
    print(f"  text coefficient     constant {counts['text'].get('constant', 0)} / "
          f"varies {counts['text'].get('varies', 0)} / "
          f"no data {counts['text'].get('no_data', 0)}")
    print(f"  catalog entries whose stored coefficient differs from the one cast: "
          f"{len(differing)} ({sum(1 for g in differing if g['owned'])} owned)")

    DATA_DERIVED.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(render_report(stats, counts, gaps, differing, failures),
                           encoding="utf-8")
    print(f"\nreport: {REPORT_PATH}")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
