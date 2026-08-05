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

# ⚠ These three are kept EXACTLY as they were (case-sensitive, plain `$SP*N` form)
# because `core/spells/rank_scaling.py` imports them for rank-vs-rank text
# COMPARISON — extending them would silently shift the validated 1x rank-ramp
# verdicts. `extract_scaling()` below uses the wider 1c patterns instead.
SP_PAT = re.compile(r"\$SP\s*\*\s*([\d.]+)")
AP_PAT = re.compile(r"\$AP\s*\*\s*([\d.]+)")
RAP_PAT = re.compile(r"\$RAP\s*\*\s*([\d.]+)")
WEAPON_PAT = re.compile(r"\$(MWB|mwb|OWB|owb|mw|ow)\b|weapon damage|Normalized", re.I)
SUBSPELL_REF_PAT = re.compile(r"\$(\d{3,7})[a-zA-Z]{1,3}\d*")
PCT_PLACEHOLDER_PAT = re.compile(r"\$s\d+%?")  # unresolved $s1 / $s2 style magnitude

# --- 1c: the compound-form gap fix (was "KNOWN GAP" since primer v14) ------------
#
# Stat-token vocabulary, measured against the full 3,061-entry export (session 1c).
# Longest-first so `$SPFR` never half-matches as `$SP`; the `(?![A-Za-z])` guard in
# the patterns below stops `$SP` matching inside an unknown longer token.
#   SP + school-suffixed spell power (WotLK convention): SPH=Holy, SPFR=Frost,
#   SPFI=Fire, SPN=Nature, SPA=Arcane, SPS=Shadow. BH=bonus healing, SPI=spirit,
#   STA=stamina. $PL (player level) is deliberately ABSENT: level scaling belongs
#   to `spell_effect_values.per_level` (numeric, tier 4), and emitting a PL "stat
#   coefficient" from text would create a second, weaker home for the same fact.
STAT_TOKEN_ALT = "SPFR|SPFI|SPH|SPN|SPA|SPS|SPI|STA|RAP|BH|SP|AP"
_NUM = r"(?:\d+\.?\d*|\.\d+)"
# `$SP*0.2`, `$spfi*.31` — coefficient after the token (the classic form, now
# case-insensitive: `$sp*0.69` in Soul Fire was silently missed before 1c)
SINGLE_AFTER_PAT = re.compile(
    rf"\$({STAT_TOKEN_ALT})(?![A-Za-z])\s*\*\s*({_NUM})", re.I)
# `0.0066*$SPH` (Seal of Vengeance) — coefficient before the token. The lookbehind
# rejects `/100*$AP` (division context, Concussion Blow) and `$m2*$AP` (the `2`
# belongs to the `$m2` variable) — both real false positives found in the survey.
SINGLE_BEFORE_PAT = re.compile(
    rf"(?<![\w$./])({_NUM})\s*\*\s*\$({STAT_TOKEN_ALT})(?![A-Za-z])", re.I)
# `($AP+$SP)*1*1*0.02` / `0.0128*($AP+$SP)*1` / `($SP+$AP)*0.0475` — a
# parenthesised sum of BARE tokens with numeric factors before and/or after.
# Inner-coefficient forms like `($SP*0.05+$RAP*0.02)` deliberately do NOT match
# (the `+` must be immediately after a bare token) — SINGLE_AFTER already catches
# each inner term.
COMPOUND_PAT = re.compile(
    rf"(?:(?<![\w$./])({_NUM})\s*\*\s*)?"                       # optional prefix factor
    rf"\(\s*\$(?:{STAT_TOKEN_ALT})(?![A-Za-z])"                 # first token
    rf"(?:\s*\+\s*\$(?:{STAT_TOKEN_ALT})(?![A-Za-z]))+\s*\)"    # +token(s)
    rf"((?:\s*\*\s*{_NUM})*)", re.I)
_COMPOUND_TOKEN_PAT = re.compile(rf"\$({STAT_TOKEN_ALT})(?![A-Za-z])", re.I)
# Combo-point tier text substitutes the point count (an integer 1–5) into the
# factor chain: `($AP+$SP)*4*4*0.02` is tier 4 of a quadratic finisher whose
# per-unit coefficient is 0.02. Factors in this set are treated as CP counts,
# never as coefficients.
_CP_COUNTS = {1.0, 2.0, 3.0, 4.0, 5.0}

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
    for m in SINGLE_AFTER_PAT.finditer(tooltip):
        terms.add((m.group(1).upper(), float(m.group(2))))
    for m in SINGLE_BEFORE_PAT.finditer(tooltip):
        terms.add((m.group(2).upper(), float(m.group(1))))
    for m in COMPOUND_PAT.finditer(tooltip):
        tokens = {t.upper() for t in _COMPOUND_TOKEN_PAT.findall(m.group(0))}
        factors = [float(x) for x in ([m.group(1)] if m.group(1) else [])
                   + re.findall(_NUM, m.group(2) or "")]
        # per-unit coefficient = product of the non-CP-count factors; a chain of
        # only 1–5 integers is ambiguous (CP substitution vs a genuine small
        # integer coefficient) and is SKIPPED rather than guessed at
        coeff_factors = [f for f in factors if f not in _CP_COUNTS]
        if not coeff_factors:
            continue
        coeff = 1.0
        for f in coeff_factors:
            coeff *= f
        for tok in tokens:
            terms.add((tok, round(coeff, 10)))
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
