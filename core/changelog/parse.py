"""Changelog entry parsing and classification (Phase 1 Task 2).

The realm patches **daily**, so the changelog is how a fact learns it has decayed.
Pure logic: this module takes entry dicts and known-name maps and returns records.
Acquisition lives in `tools/scrapers/fetch_changelog.py`, ingestion in
`ingest/changelog/`.

Three things this has to get right, each learned the hard way in Phase 0:

  1. **Realm.** Darkmoon and Dawnrise receive different balance changes. An untagged
     entry is `realm unknown`, **never** `all realms` — 78% of the historical corpus
     is untagged and mostly about realms that no longer exist.
  2. **Status.** 84.9% of current-era entries carry `[Pending Restart]` or
     `[Going Live …]`. Treating one as live invalidates facts prematurely; ignoring
     it misses the change when it lands.
  3. **Direction.** Feeds volatility scoring (Task 10). Classified conservatively —
     an entry that both increases and reduces something is `neutral`, not a guess.

⚠ Name detection is a **candidate generator, not a resolver.** A bracketed token is
high confidence only once it matches a known card; prose matches are weaker still.
Nothing here should become a confirmed fact without a second source.
"""
import re

# Bracket tokens that are NOT ability names, derived by frequency inspection of the
# real corpus (session 0a) rather than guessed: realms, status markers, section labels.
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

# Instance/zone names also appear in brackets and would otherwise swamp the new-card
# candidate list (Karazhan alone: 373 entries). The caller unions this with the zone
# names the crawler actually captured.
LEGACY_ZONE_TOKENS = {
    "karazhan", "naxxramas", "archimonde", "serpentshrine", "the black temple",
    "the eye", "bwl", "the battle for mount hyjal", "magtheridon", "zul'aman",
    "lady vashj", "blackwing lair", "aqt", "magtheridon's lair", "sunwell plateau",
    "gruuls lair", "gruul's lair", "molten core", "onyxia", "temple of ahn'qiraj",
    "ruins of ahn'qiraj", "zul'gurub", "black temple", "hyjal", "ssc",
    "tempest keep", "vault of archavon", "ulduar", "trial of the crusader",
    "icecrown citadel", "obsidian sanctum", "eye of eternity",
}

# The machine-detectable new-card announcement, 52 matches since 2026-07-01 and
# every one of them ALREADY in the client's CharacterAdvancement.dbc. So this is a
# *change-history* signal, not the earliest existence signal (Phase 0 Task 3).
# The live wording varies more than it looks: "A new Talent/Mystic Enchant is now
# available!", "A new Conquest of Azeroth Talent/Mystic Enchant...", "A new Legendary
# Talent and Talent Card...". A pattern that pinned the noun directly before "is now
# available" matched none of them and then classified every new card as a `nerf`,
# since their body text is usually "X and Y reduce Z's cooldown". Match the frame,
# not the noun.
NEW_CARD_RE = re.compile(r"\ba\s+new\s+[^.!?]{0,80}?\bis\s+now\s+available\b", re.I)

# 🔑 The most useful fact about this corpus's grammar: **a reduction applied to a
# cooldown, cost, cast time or damage taken is a BUFF**, whichever direction word
# sits next to it. All six of these are buffs, and a naive reading calls them nerfs:
#
#     "Windfury Weapon's internal cooldown has been reduced by 33%"
#     "reduces Vampiric Blood's cooldown by 2 seconds, up from 1 second"
#     "Glacial Light's cooldown reduction has been increased to 7s, up from 4s"
#     "reduces Soul Fire's cast time and global cooldown by 50%, up from 40%"
#     "now reduces damage taken by 12% for 6 seconds, up from 2%"
#     "now cost 10 rage, down from 30"
#
# An earlier version tried to *invert* the comparative for these and got 10 of 13
# nerfs wrong — "reduces X's cooldown ... up from" inverts twice. Recognising the
# beneficial-reduction frame itself is what actually holds.
_BENEFICIAL_REDUCTION_RE = re.compile(
    r"\breduc(?:e|es|ed|ing|tion)\b[^.]{0,70}"
    r"\b(?:cooldown|cost|cast time|damage taken|threat|recharge)\b"
    r"|\b(?:cooldown|cost|cast time|damage taken|threat|recharge)\b[^.]{0,70}"
    r"\breduc(?:e|es|ed|ing|tion)\b", re.I)

# The other inverting quantities: paying less, or unlocking earlier, is a buff.
_CHEAPER_RE = re.compile(
    r"\b(?:costs?|requires? level|consumes?|stacks? of)\b[^.]{0,70}\bdown from\b", re.I)

# The plain comparative idiom, used only after the frames above have had their say.
_UP_FROM_RE = re.compile(r"\bup from\b", re.I)
_DOWN_FROM_RE = re.compile(r"\bdown from\b", re.I)

_BUFF_RE = re.compile(r"\bincreas(e|es|ed|ing)\b|\bbuff(ed)?\b|\bimprov(e|ed|es)\b|"
                      r"\bnow\s+also\b|\bhigher\b|\braised\b", re.I)
# `lower` as a bare adjective is ordinary English ("at lower levels") and was
# producing false nerfs; only the past participle is a change verb.
_NERF_RE = re.compile(r"\breduc(e|ed|es)\b|\bdecreas(e|ed|es)\b|\blowered\b|"
                      r"\bnerf(ed)?\b|\bno longer\b|\bremoved\b|\bcapped\b", re.I)
_FIX_RE = re.compile(r"\bfixed\b|\bbug\b|\bcorrected\b|\bshould now\b|"
                     r"\bintended behaviou?r\b|\btypo\b", re.I)


def classify_token(token, zone_tokens=()):
    low = token.strip().lower()
    if low in REALM_TOKENS:
        return "realm"
    if low in STATUS_TOKENS or GOING_LIVE_RE.match(low):
        return "status"
    if low in SECTION_TOKENS:
        return "section"
    if low in zone_tokens:
        return "zone"
    return "candidate_name"


def classify_status(status_tokens):
    """`'live'` | `'pending_restart'` | `'announced_future'`.

    Absence of a status tag means **no statement was made**, which is not the same
    as "confirmed live" — but `live` is the only sensible default for an entry that
    was published with no caveat, so it is what we store, and `status_note` keeps
    the verbatim tag so the distinction survives.
    """
    lowered = [t.strip().lower() for t in status_tokens]
    for tok in lowered:
        if GOING_LIVE_RE.match(tok):
            return "announced_future"
    for tok in lowered:
        if "pending" in tok or "requires" in tok:
            return "pending_restart"
    return "live"


def classify_direction(text, *, is_new_card=False):
    """`'buff'` | `'nerf'` | `'fix'` | `'new_card'` | `'neutral'`.

    Conservative on purpose (Task 2: "classify conservatively — flag the rest as
    neutral rather than guessing"). An entry containing both increase and reduce
    language is genuinely ambiguous at this granularity and is left `neutral`;
    Task 10's volatility score would rather see fewer, right classifications.

    `fix` wins over buff/nerf: "fixed a bug where X dealt too much damage" is a
    correction, and lumping it in with deliberate nerfs would distort nerf-risk.
    """
    if is_new_card or NEW_CARD_RE.search(text or ""):
        return "new_card"
    body = text or ""
    if _FIX_RE.search(body):
        return "fix"

    # the beneficial-reduction frames, before anything reads a direction word
    if _BENEFICIAL_REDUCTION_RE.search(body) or _CHEAPER_RE.search(body):
        return "buff"

    up_from, down_from = bool(_UP_FROM_RE.search(body)), bool(_DOWN_FROM_RE.search(body))
    if up_from != down_from:
        return "buff" if up_from else "nerf"

    up, down = bool(_BUFF_RE.search(body)), bool(_NERF_RE.search(body))
    if up and not down:
        return "buff"
    if down and not up:
        return "nerf"
    return "neutral"


def parse_entry(entry, known_names, zone_tokens=()):
    """Turn one raw changelog entry into a structured record.

    `known_names` maps a lowercased card name to a list of `(source, id)` pairs —
    supplied by the caller from the catalog and `CharacterAdvancement.dbc`.
    """
    desc = entry.get("description") or ""
    realms, statuses, sections, zones, candidates = [], [], [], [], []
    for tok in (t.strip() for t in BRACKET_RE.findall(desc)):
        kind = classify_token(tok, zone_tokens)
        {"realm": realms, "status": statuses, "section": sections,
         "zone": zones, "candidate_name": candidates}[kind].append(tok)

    named = []
    for tok in candidates:
        hits = known_names.get(tok.strip().lower())
        named.append({
            "name": tok,
            "detection": "bracketed_and_known" if hits else "bracketed_unknown",
            "confidence": "high" if hits else "medium",
            "refs": hits[:4] if hits else [],
        })

    # Unbracketed prose mentions. Only names of >=2 words are looked for: single-word
    # card names ("Focus", "Vengeance", "Bane") collide with ordinary English.
    body = BRACKET_RE.sub(" ", desc).lower()
    seen = {n["name"].strip().lower() for n in named}
    for nm, refs in known_names.items():
        if " " in nm and len(nm) >= 8 and nm not in seen and nm in body:
            named.append({"name": nm, "detection": "prose_match",
                          "confidence": "low", "refs": refs[:4]})
            seen.add(nm)

    is_new_card = bool(NEW_CARD_RE.search(desc))
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
        "status_class": classify_status(statuses),
        "sections": sections,
        "zones": zones,
        # not-yet-live if any status tag says so; absence of a tag is "no statement"
        "pending": bool(statuses),
        "change_type": "New" if is_new_card else "Change",
        "change_direction": classify_direction(desc, is_new_card=is_new_card),
        "description": desc,
        "abilities": named,
    }


def detect_new_cards(records, known_names):
    """Bracketed names in a `New` entry that resolve against nothing we know.

    These would be the leading edge of the game's content — **except** Phase 0
    measured 52/52 announced cards already present in `CharacterAdvancement.dbc`
    and only 2/52 in `spell-export.json`. So a hit here almost always means *the
    catalog export is stale*, not *the game has something nobody has seen*. Check
    the DBC before treating one as a discovery.
    """
    out = []
    for rec in records:
        if rec.get("change_type") != "New":
            continue
        for ability in rec["abilities"]:
            if ability["detection"] == "bracketed_unknown":
                out.append({"name": ability["name"], "entry_id": rec["id"],
                            "date": rec["date"], "realms": rec["realms"],
                            "description": rec["description"],
                            "in_known_names": ability["name"].strip().lower() in known_names})
    return out
