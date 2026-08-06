"""Parsing for db.ascension.gg spell pages (Phase 3b).

## Why this source exists in the stack at all

Ascension keeps the coefficients its server actually applies in **tooltip
text**, not in the client's numeric fields — `EffectBonusCoefficient` is stock
`EffectBonusMultiplier` and matches a stated `$SP*x`/`$AP*x` in 4 of 98 cases
(`effect_bonus_coefficient_is_not_the_sp_ap_coefficient`). So for the ~41% of
crawled damage where we hold a magnitude but **no coefficient**, the client is
structurally unable to supply one. `db.ascension.gg` states them outright:

    <th>Scaling #1</th><td> +29.00% of spell power to direct component </td>

This module is the parser only. Fetching, politeness and checkpointing live in
`tools/scrapers/scrape_ascension_db.py` — `core/` takes text, not URLs.

## 🛑 The check digit, and why this is not "trust a third-party site"

A scraped coefficient is only accepted alongside a magnitude we can verify
**against our own client-derived numbers**. The page states its base value the
same way we decode it from `Spell.dbc`, so the two must agree — Icy Penance is
the worked case: our `spell_effect_values.flat_min` reads 284.0 and the page
reads `Value: 284`, derived completely independently. We hold decoded flats for
**14,100 spells**, so that is a large standing validation surface rather than a
spot check. `cross_check()` implements it; a page whose magnitude disagrees
with ours has its coefficients **refused**, not stored with a caveat.

This is the same discipline as the weapon-damage parse (`core/builds/gear.py`):
a rendered third-party string is admissible **when it carries a check digit and
the check is enforced**.

## What is deliberately NOT inferred

* **Nothing is related by name.** Trigger targets are taken from the `?spell=`
  href — an id the page itself states — never by matching a link's text
  against a spell name (primer §4, and the duplicate-name trap).
* **Rank is read, not assumed.** A coefficient scales with rank
  (`coefficients_do_scale_with_rank`), so the parsed rank travels with the
  coefficient and a consumer that needs level-60 must check it.
"""
import re

# <th>Scaling #1</th><td colspan="3"> +29.00% of spell power to direct component
_SCALING_RE = re.compile(
    r"<th>\s*Scaling\s*#(\d+)\s*</th>\s*<td[^>]*>\s*\+?([\d.]+)\s*%\s*of\s*"
    r"([a-z ]+?)\s*(?:to\s+(\w+)\s+component|per\s+(tick))?\s*(?:<br\s*/?>)?\s*</td>",
    re.I)

# "Value: 284" / "Value: 2 to 25, plus 2.4 per level" / "83 to 93, plus 1.2 per level"
_VALUE_RE = re.compile(
    r"Value:\s*(\d+)(?:\s*to\s*(\d+))?(?:\s*,\s*plus\s*([\d.]+)\s*per\s*level)?", re.I)

# Effect #N ... Trigger Spell: ... <a href="?spell=282987">Hammer from the Heavens</a>
_EFFECT_BLOCK_RE = re.compile(
    r"<th>\s*Effect\s*#(\d+)\s*</th>(.*?)(?=<th>\s*Effect\s*#\d+\s*</th>|</table>\s*</div>|\Z)",
    re.I | re.S)
_HREF_SPELL_RE = re.compile(r'href="\?spell=(\d+)"[^>]*>([^<]*)<', re.I)
_NAME_RE = re.compile(r"<h1[^>]*>([^<]+)</h1>", re.I)
_RANK_RE = re.compile(r"\bRank\s+(\d+)\b", re.I)

# "spell power" / "attack power" / "ranged attack power" -> spell_scaling.term_type
_TERM = {
    "spell power": "SP",
    "attack power": "AP",
    "ranged attack power": "RAP",
    "weapon damage": "WEAPON",
}


def _strip_tags(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)).strip()


def parse_spell_page(html, spell_id):
    """A db.ascension.gg `?spell=<id>` page -> a structured record.

    Returns a dict always; `parsed_ok` says whether anything usable was found,
    so a miss is recorded rather than silently dropped (a spell the site does
    not carry is itself information).
    """
    if not html:
        return {"spell_id": spell_id, "parsed_ok": False,
                "reason": "empty response"}

    name_m = _NAME_RE.search(html)
    rank_m = _RANK_RE.search(html)

    scaling = []
    for idx, pct, stat, component, per_tick in _SCALING_RE.findall(html):
        term = _TERM.get(stat.strip().lower())
        if term is None:
            # an unrecognised scaling stat is REPORTED, never coerced into the
            # known vocabulary — a stat we cannot name is a finding
            scaling.append({"index": int(idx), "term_type": None,
                            "raw_stat": stat.strip(),
                            "coefficient": float(pct) / 100.0,
                            "component": component or ("periodic" if per_tick else None)})
            continue
        scaling.append({
            "index": int(idx), "term_type": term,
            "coefficient": float(pct) / 100.0,
            "component": (component or ("periodic" if per_tick else "direct")).lower(),
        })

    value = None
    v = _VALUE_RE.search(html)
    if v:
        value = {"min": int(v.group(1)),
                 "max": int(v.group(2)) if v.group(2) else int(v.group(1)),
                 "per_level": float(v.group(3)) if v.group(3) else None}

    # Trigger links: the id comes from the page's own href, never from the
    # link TEXT — relating two spells by name is the standing error (primer §4)
    effects = []
    for eff_idx, block in _EFFECT_BLOCK_RE.findall(html):
        text = _strip_tags(block)
        triggers = [{"spell_id": int(sid), "name_on_page": nm.strip()}
                    for sid, nm in _HREF_SPELL_RE.findall(block)]
        is_trigger = bool(re.search(r"Trigger\s+Spell", block, re.I))
        effects.append({
            "effect_index": int(eff_idx),
            "is_trigger_spell": is_trigger,
            "triggers": triggers if is_trigger else [],
            "linked_spells": [t["spell_id"] for t in triggers],
            "text": text[:400],
        })

    return {
        "spell_id": spell_id,
        "parsed_ok": bool(scaling or value or effects),
        "name_on_page": name_m.group(1).strip() if name_m else None,
        "rank_on_page": int(rank_m.group(1)) if rank_m else None,
        "value": value,
        "scaling": scaling,
        "effects": effects,
        "trigger_edges": sorted({t["spell_id"] for e in effects
                                 if e["is_trigger_spell"] for t in e["triggers"]}),
    }


def decoded_flats_by_spell(conn):
    """`{spell_id: [(flat_min, flat_max), ...]}` — the check digit, per slot.

    🛑 Keyed and grouped **exactly** as `tools/scrapers/scrape_ascension_db.py`
    did when it wrote the committed verdicts. The ingest recomputes verdicts
    against a *fresher extract*, which is the point; it must not also change the
    *method*, or the recomputed tally stops being comparable with the committed
    one and the check has effectively been redefined after seeing its result.

    ⚠ Note for a future session, deliberately NOT acted on here: this keys on
    `spell_id`, so a card's list also carries flats decoded from its
    `hidden_ref`/`trigger_hop` sub-spells. Since `cross_check` accepts a match
    against ANY slot, that is marginally *permissive* — keying on
    `source_spell_id` (the record actually decoded) would be stricter. Changing
    it is a real question, but it is a change to the check, so it belongs in a
    session that re-runs and re-reports the whole tally, not in an ingest.
    """
    out = {}
    for sid, lo, hi in conn.execute(
            "SELECT spell_id, flat_min, flat_max FROM spell_effect_values "
            "WHERE flat_min IS NOT NULL"):
        out.setdefault(sid, []).append((lo, hi))
    return out


def cross_check(record, our_effect_values, *, tolerance=0.02):
    """🛑 The gate on trusting a scraped coefficient.

    The page's stated base value must reproduce the magnitude we decoded
    independently from the client's numeric DBC fields. Agreement means the two
    sources are describing the same spell at the same rank, which is what makes
    the coefficient on that page usable; disagreement means they are not, and
    the coefficient is REFUSED rather than stored with a caveat.

    `our_effect_values` is a list of `(flat_min, flat_max)` **per effect
    slot**, NOT an aggregate. ⚠ Aggregating across slots is wrong and was
    caught doing exactly this: Lightbound Cleave decodes effect 0 = 62 (a flat)
    and effect 1 = 65 (a **weapon percent**, not damage — the
    `EFFECT_WEAPON_PCT` trap), so `MIN/MAX` across slots produced "62-65", a
    range belonging to no effect, and reported a false disagreement against the
    page's correct `Value: 62`. The page states one effect's value, so the
    check asks whether it matches **any** slot we decoded.

    Returns (verdict, detail) where verdict is one of:
      'agree'        -> coefficients from this page may be used
      'disagree'     -> do NOT use; likely a different rank or a different spell
      'unverifiable' -> we hold no decoded flat, so there is no check digit.
                        Coefficients are still recorded but must be stored at a
                        weaker confidence and never silently promoted.
    """
    v = (record or {}).get("value")
    if not v:
        return "unverifiable", "page states no base value"
    slots = [(float(lo), float(hi if hi is not None else lo))
             for lo, hi in (our_effect_values or []) if lo is not None]
    if not slots:
        return "unverifiable", "no decoded flat on our side to check against"
    theirs_lo, theirs_hi = float(v["min"]), float(v["max"])

    def close(a, b):
        if a == 0 and b == 0:
            return True
        return abs(a - b) <= tolerance * max(abs(a), abs(b), 1.0)

    for ours_lo, ours_hi in slots:
        if close(ours_lo, theirs_lo) and close(ours_hi, theirs_hi):
            return "agree", (f"{theirs_lo:g}-{theirs_hi:g} matches decoded "
                             f"{ours_lo:g}-{ours_hi:g}")
    shown = ", ".join(f"{lo:g}-{hi:g}" for lo, hi in slots[:4])
    return "disagree", (f"page {theirs_lo:g}-{theirs_hi:g} matches no decoded "
                        f"effect slot ({shown}) — different rank or different spell")
