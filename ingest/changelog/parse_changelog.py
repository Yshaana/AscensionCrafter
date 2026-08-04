#!/usr/bin/env python3
"""Changelog parser (Phase 0 Task 3).

Reads the committed JSON captured by fetch_changelog.py and turns each entry into
a structured record: date, realm(s), live-status, category, change type, raw text,
and every ability name it can detect with a confidence tag by detection method.

Acquisition is NOT this script's job - fetch_changelog.py already did it. This is
pure parsing over `data/source/changelog/`, so it is offline and re-runnable.

Two things worth knowing before trusting the output:

  * ⚠ The corpus spans 2016->today across EVERY Ascension realm. Darkmoon (this
    project's realm) is a small, recent slice of it: `[Darkmoon]` appears on ~170
    of 35,238 entries. Most bracket tokens are historic realms (Elune, Area-52,
    Thrall, Alar), not abilities. Always filter by realm before drawing a
    conclusion, and treat an untagged entry as "realm unknown", not "all realms".

  * Ability-name detection is a *candidate generator*, not a resolver. A bracketed
    token is high confidence only once it matches a known card name; prose matches
    are weaker still. Nothing here should be written into seed_confirmed.py without
    a second source - the primer's standing rule that a diff report finds
    candidates rather than confirming novelty applies verbatim.
"""
import argparse
import collections
import json
import os
import re
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from config import (  # noqa: E402
    CHANGELOG_DIR, CRAWL_DIR, DBC_ASCENSION_EXTRACT_JSON as ASCENSION_EXTRACT,
    SPELL_EXPORT as CATALOG,
)

# Bracket tokens that are NOT ability names. Derived by frequency inspection of the
# real corpus (session 0a), not guessed: realms, status markers, and section labels.
REALM_TOKENS = {
    "darkmoon", "dawnrise", "elune", "area-52", "area 52", "area52", "thrall",
    "alar", "al'ar", "bleeding hollow", "classless - dawnrise", "classless - darkmoon",
    "high-risk", "league 2", "league", "tbc", "legacy", "seasonal", "wildcard",
    "bronzebeard", "coa", "conquest of azeroth",
}
STATUS_TOKENS = {
    "pending restart", "pending patch update", "pending update", "requires restart",
    "requires launcher update", "launcher", "hotfix", "live", "reverted",
}
SECTION_TOKENS = {
    "items", "general", "crafting", "new capstone", "new epic enchant", "quests",
    "professions", "pvp", "dungeons", "raids", "classes", "talents", "abilities",
    "mystic enchants", "bug fixes",
}
GOING_LIVE_RE = re.compile(r"^going live\b", re.I)
BRACKET_RE = re.compile(r"\[([^\]]{1,60})\]")

# Instance/zone names also appear in brackets and would otherwise swamp the
# new-card candidate list (Karazhan alone: 373 entries). Seeded from the phases
# the crawler actually captured, plus the legacy raids the older corpus is full
# of - the changelog reaches back to 2016 and most of it predates this realm.
LEGACY_ZONE_TOKENS = {
    "karazhan", "naxxramas", "archimonde", "serpentshrine", "the black temple",
    "the eye", "bwl", "the battle for mount hyjal", "magtheridon", "zul'aman",
    "lady vashj", "blackwing lair", "aqt", "magtheridon's lair", "sunwell plateau",
    "gruuls lair", "gruul's lair", "molten core", "onyxia", "temple of ahn'qiraj",
    "ruins of ahn'qiraj", "zul'gurub", "black temple", "hyjal", "ssc",
    "tempest keep", "vault of archavon", "ulduar", "trial of the crusader",
    "icecrown citadel", "obsidian sanctum", "eye of eternity",
}


def load_zone_tokens():
    """Zone names from captured /api/phases records, unioned with LEGACY_ZONE_TOKENS."""
    zones = set(LEGACY_ZONE_TOKENS)
    import gzip
    for path in CRAWL_DIR.glob("*/phases.jsonl.gz"):
        try:
            with gzip.open(path, "rt", encoding="utf-8") as f:
                for line in f:
                    for phase in json.loads(line)["payload"].get("phases") or []:
                        for loc in phase.get("locations") or []:
                            if loc.get("location"):
                                zones.add(loc["location"].strip().lower())
        except (OSError, KeyError, json.JSONDecodeError):
            continue
    return zones


ZONE_TOKENS = set()

# `label` / `category` are small integer enums in the API. Their meaning is NOT
# documented anywhere we can see, so they are carried through verbatim rather than
# translated into invented names.


def load_known_names():
    """Card/ability names to match against: the catalog, plus (if extracted) the
    client's own CharacterAdvancement card list, which is ~3.7x larger."""
    names = {}
    cat = json.loads(CATALOG.read_text(encoding="utf-8"))["spells"]
    for s in cat:
        names.setdefault(s["name"].strip().lower(), []).append(("catalog", s["id"]))
    if ASCENSION_EXTRACT.exists():
        payload = json.loads(ASCENSION_EXTRACT.read_text(encoding="utf-8"))
        ca = payload.get("dbc_character_advancement")
        if ca:
            i_name = ca["columns"].index("name")
            i_id = ca["columns"].index("ca_id")
            for row in ca["rows"]:
                nm = (row[i_name] or "").strip().lower()
                if nm:
                    names.setdefault(nm, []).append(("character_advancement", row[i_id]))
    return names


def iter_entries(directory):
    """Yield every changelog entry from the captured pages.

    Shape: {"data": {"YYYY/MM/DD": {"<category>": [entry, ...]}}}
    """
    for path in sorted(Path(directory).glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        data = payload.get("data")
        if not isinstance(data, dict):
            continue
        for group_key, by_cat in data.items():
            if not isinstance(by_cat, dict):
                continue
            for entries in by_cat.values():
                for entry in entries or []:
                    yield path.name, group_key, entry


def classify_token(tok):
    low = tok.strip().lower()
    if low in REALM_TOKENS:
        return "realm"
    if low in STATUS_TOKENS or GOING_LIVE_RE.match(low):
        return "status"
    if low in SECTION_TOKENS:
        return "section"
    if low in ZONE_TOKENS:
        return "zone"
    return "candidate_name"


def parse_entry(entry, known_names):
    desc = entry.get("description") or ""
    tokens = [t.strip() for t in BRACKET_RE.findall(desc)]
    realms, statuses, sections, zones, candidates = [], [], [], [], []
    for tok in tokens:
        kind = classify_token(tok)
        {"realm": realms, "status": statuses, "section": sections,
         "zone": zones, "candidate_name": candidates}[kind].append(tok)

    # bracketed candidate that matches a known card -> strongest signal available
    named = []
    for tok in candidates:
        hits = known_names.get(tok.strip().lower())
        if hits:
            named.append({"name": tok, "detection": "bracketed_and_known",
                          "confidence": "high", "refs": hits[:4]})
        else:
            named.append({"name": tok, "detection": "bracketed_unknown",
                          "confidence": "medium", "refs": []})

    # unbracketed prose mentions. Only names >=2 words are looked for: single-word
    # card names ("Focus", "Vengeance", "Bane") collide with ordinary English and
    # generate mostly noise.
    body = BRACKET_RE.sub(" ", desc).lower()
    seen = {n["name"].strip().lower() for n in named}
    for nm in known_names:
        if " " in nm and len(nm) >= 8 and nm not in seen and nm in body:
            named.append({"name": nm, "detection": "prose_match",
                          "confidence": "low", "refs": known_names[nm][:4]})
            seen.add(nm)

    return {
        "id": entry.get("id"),
        "date": entry.get("group_key"),
        "created_at": entry.get("created_at"),
        "updated_at": entry.get("updated_at"),
        "label": entry.get("label"),
        "category": entry.get("category"),
        "realm_type": entry.get("realm_type"),
        "realms": realms,
        "status": statuses,
        "sections": sections,
        "zones": zones,
        # not-yet-live if any status tag says so; absence of a tag means "no
        # statement", which is NOT the same as "confirmed live"
        "pending": bool(statuses),
        "description": desc,
        "abilities": named,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", default=str(CHANGELOG_DIR / "backfill"))
    ap.add_argument("--realm", help="only report entries tagged with this realm")
    ap.add_argument("--out", help="write parsed records as JSONL to this path")
    ap.add_argument("--since", help="only entries with group_key >= this YYYY/MM/DD")
    args = ap.parse_args()

    global ZONE_TOKENS
    ZONE_TOKENS = load_zone_tokens()
    known = load_known_names()
    print(f"zone tokens loaded: {len(ZONE_TOKENS)}")
    print(f"known card names loaded: {len(known)}")

    parsed = []
    for _src, _gk, entry in iter_entries(args.dir):
        rec = parse_entry(entry, known)
        if args.since and (rec["date"] or "") < args.since:
            continue
        if args.realm and args.realm.lower() not in {r.lower() for r in rec["realms"]}:
            continue
        parsed.append(rec)

    print(f"entries parsed: {len(parsed)}")
    if not parsed:
        return

    realm_c = collections.Counter()
    for r in parsed:
        if r["realms"]:
            realm_c.update(x.lower() for x in r["realms"])
        else:
            realm_c["(untagged)"] += 1
    print("\nrealm attribution:", realm_c.most_common(12))

    pend = sum(1 for r in parsed if r["pending"])
    print(f"entries carrying a not-yet-live status tag: {pend} "
          f"({pend / len(parsed) * 100:.1f}%)")

    det = collections.Counter(a["detection"] for r in parsed for a in r["abilities"])
    with_any = sum(1 for r in parsed if r["abilities"])
    with_known = sum(1 for r in parsed
                     if any(a["detection"] != "bracketed_unknown" for a in r["abilities"]))
    print(f"\nentries naming at least one ability candidate: {with_any} "
          f"({with_any / len(parsed) * 100:.1f}%)")
    print(f"  ...of which at least one resolves to a KNOWN card: {with_known} "
          f"({with_known / len(parsed) * 100:.1f}%)")
    print("  detections by method:", det.most_common())

    unknown = collections.Counter(a["name"] for r in parsed for a in r["abilities"]
                                  if a["detection"] == "bracketed_unknown")
    print(f"\nbracketed names NOT matching any known card: {len(unknown)} distinct "
          f"(these are the new-card-discovery candidates)")
    for nm, c in unknown.most_common(15):
        print(f"    {c:4d}  {nm}")

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            for r in parsed:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"\nwrote {len(parsed)} records to {args.out}")


if __name__ == "__main__":
    main()
