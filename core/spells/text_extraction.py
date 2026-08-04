"""Tooltip text signal extraction — schools, mechanic tags, scaling terms, hidden refs.

Lifted verbatim (behaviour-preserving) out of `index/build_index.py` in the Phase 1 T1
restructure so the sim and the ingesters share one implementation.

⚠ Everything here is a **text-presence signal**, not a verified game mechanic. A
`heal` tag means the word appears in the tooltip. A missing school means the tooltip
never wrote it down — not that the ability has no school. Treat output as candidates
for a tier-1/tier-4 check, never as fact (§2.2).

⚠ It reads the *export catalog's* tooltip, which for ~697 multi-rank entries is the
wrong rank's text (Phase 0). Coefficients extracted here appear to survive that
(identical at R1 and R6 on the one line measured); flat magnitudes do not.
"""
import re

PURE_SCHOOLS = ["Frost", "Fire", "Shadow", "Arcane", "Nature", "Holy", "Physical"]
HYBRID_SCHOOLS = ["Holystrike", "Holyfire", "Shadowflame", "Firestrike", "Froststrike",
                  "Shadowstrike", "Spellstrike", "Stormstrike"]
OTHER_SCHOOL_WORDS = ["Fel", "Chaos"]
ALL_SCHOOLS = PURE_SCHOOLS + HYBRID_SCHOOLS + OTHER_SCHOOL_WORDS

SP_PAT = re.compile(r"\$SP\s*\*\s*([\d.]+)")
AP_PAT = re.compile(r"\$AP\s*\*\s*([\d.]+)")
RAP_PAT = re.compile(r"\$RAP\s*\*\s*([\d.]+)")
WEAPON_PAT = re.compile(r"\$(MWB|mwb|OWB|owb|mw|ow)\b|weapon damage|Normalized", re.I)
SUBSPELL_REF_PAT = re.compile(r"\$(\d{3,7})[a-zA-Z]{1,3}\d*")
PCT_PLACEHOLDER_PAT = re.compile(r"\$s\d+%?")  # unresolved $s1 / $s2 style magnitude

# KNOWN GAP (primer v14, still open): school-suffixed variants like `$SPFR*0.0096`
# (Winds of Winter's Frost-SP term) and compound forms like `($AP+$SP)*n*n` (Holy
# Finish) are NOT matched by the patterns above. Both are hand-seeded downstream.
# Fixing the extractor is Phase 1 T4's job, not this module's.

MECHANIC_RULES = {
    "heal": re.compile(r"\bheal(s|ing|ed)?\b|restore(s)? .*health", re.I),
    "proc": re.compile(r"chance to|% chance|when you|on your next|has a \$", re.I),
    "dot_hot": re.compile(r"over \d|over \$|each \$?\d*\s*sec|per sec", re.I),
    "aoe": re.compile(r"nearby enem|all enem|area|\byards?\b|target area", re.I),
    "cc": re.compile(r"\bstun(s|ned)?\b|\broot(s|ed)?\b|\bsilence(s|d)?\b|\bfear(s|ed)?\b|"
                     r"\bsleep\b|polymorph|disorient|incapacitat|snare|\bslow(s|ed)?\b", re.I),
    "execute": re.compile(r"below \d+%|at or below|health remaining", re.I),
    "cooldown_effect": re.compile(r"cooldown", re.I),
    "buff_debuff": re.compile(r"increases|decreases|reduces|grants|gains", re.I),
    "resource_mana": re.compile(r"\bmana\b", re.I),
    "resource_rage": re.compile(r"\brage\b", re.I),
    "resource_energy": re.compile(r"\benergy\b", re.I),
    "resource_runic": re.compile(r"runic power", re.I),
    "resource_holypower": re.compile(r"holy power", re.I),
    "resource_combopoints": re.compile(r"combo point", re.I),
    "resource_focus": re.compile(r"\bfocus\b", re.I),
    "exclusivity_bucket": re.compile(r"does not stack with", re.I),
}


def extract_schools(tooltip: str) -> list:
    """Damage schools *named in the tooltip text*, sorted. Presence signal only."""
    found = set()
    for school in ALL_SCHOOLS:
        if re.search(r"\b" + re.escape(school) + r"\b", tooltip):
            found.add(school)
    return sorted(found)


def extract_scaling(tooltip: str, spell_id: int, valid_ids):
    """Return `(terms, hidden_refs, has_unresolved_pct)`.

    `terms` is a list of `(term_type, coefficient)`; WEAPON carries None.
    `hidden_refs` are sub-spell IDs the tooltip interpolates that are absent from
    `valid_ids` — i.e. the real formula lives somewhere this export cannot see.
    """
    # dedupe identical (type, coeff) pairs — per-combo-point / per-rank tables repeat
    # the same unit coefficient once per point/rank in the raw text
    terms = set()
    for m in SP_PAT.finditer(tooltip):
        terms.add(("SP", float(m.group(1))))
    for m in AP_PAT.finditer(tooltip):
        terms.add(("AP", float(m.group(1))))
    for m in RAP_PAT.finditer(tooltip):
        terms.add(("RAP", float(m.group(1))))
    if WEAPON_PAT.search(tooltip):
        terms.add(("WEAPON", None))

    hidden_refs = set()
    for m in SUBSPELL_REF_PAT.finditer(tooltip):
        rid = int(m.group(1))
        if rid != spell_id and rid not in valid_ids:
            hidden_refs.add(rid)

    return sorted(terms, key=lambda t: (t[0], t[1] is None, t[1] or 0)), \
        sorted(hidden_refs), bool(PCT_PLACEHOLDER_PAT.search(tooltip))


def extract_mechanics(tooltip: str) -> list:
    """Mechanic signal tags present in the tooltip text, sorted."""
    return sorted(tag for tag, pat in MECHANIC_RULES.items() if pat.search(tooltip))
