"""Pooled mechanics inference (Phase 3 Task 2) — the crawl corpus as instrument.

Everything here PROPOSES; nothing auto-seeds `spell_mechanics`. Findings land in
the `inference_findings` staging table with sample sizes and intervals, and a
human promotes them into the seed files.

Design constraints the data imposes (all Phase 0/2 findings, not choices):

* **Per-parse character stats do not exist** in the crawl, and armory stats are
  GEAR-ONLY — worse, hit and crit rating are unified *in gear*, so a regression
  against gear rating cannot separate the melee from the spell table at all.
  `infer_crit_table` therefore uses a WITHIN-CHARACTER ANCHOR comparison
  instead: for each character-scope, the target ability's crit% is compared to
  the same character's observed crit% on anchors whose table is doc-confirmed
  (melee anchor: Auto Attack; spell anchors: confirmed `crit_table='spell'`
  ids). Buff state, gear, and target-level suppression all cancel within the
  pair, which is the same property that made the primer's parse-sorting method
  work — here with measured anchors in place of the character sheet.
* **Avoidance rows carry no attacker id**, so hit-check inference pools per
  spell per enemy target. The per-target structure matters: a target that
  full-resists EVERY pulse while landing zero is an immunity, not a resist
  roll — collapsing both into one rate would manufacture a phantom mechanic.
* **Target level is not recorded.** Content type (raid vs dungeon) is the
  available proxy and every finding is partitioned by it; a pooled-across-
  content rate is refused, not averaged.
* **Patch partitioning**: callers pass `patch_touched_dates` (from ascension.db
  `patch_entry_spells`) and samples are split at those dates; this module never
  reads ascension.db itself.
"""
import json
import math
from datetime import datetime, timezone

STAGING_SCHEMA = """
CREATE TABLE IF NOT EXISTS inference_findings (
    finding_id INTEGER PRIMARY KEY AUTOINCREMENT,
    computed_at TEXT NOT NULL,
    question TEXT NOT NULL,          -- 'crit_table','rolls_hit_check','partial_resist','proc_rate'
    spell_id INTEGER,
    spell_name TEXT,
    content_type TEXT,               -- partition; never pooled across
    realm TEXT, season TEXT,
    verdict TEXT NOT NULL,           -- proposal, or 'insufficient_*' refusal
    ci_low REAL, ci_high REAL,       -- 95% interval where the question is a rate
    sample_size INTEGER,
    character_count INTEGER,
    detail_json TEXT,                -- everything a reviewer needs to judge it
    promoted INTEGER NOT NULL DEFAULT 0   -- human sets this; the sweep never does
);
"""

MIN_HITS_PER_CHAR = 30       # per-character floor for a crit% to mean anything
MIN_ANCHOR_SEPARATION = 3.0  # anchor gap (points) below which there is no discriminator
MIN_POOLED_HITS_CRIT = 800   # primer: crit questions need thousands pooled
MIN_POOLED_HITS_AVOID = 300


def init_staging(conn):
    conn.executescript(STAGING_SCHEMA)


def _wilson(k, n, z=1.96):
    """95% Wilson interval for a proportion — sane at 0 and small n."""
    if not n:
        return None, None
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def _now():
    return datetime.now(timezone.utc).isoformat()


def _record(conn, question, spell_id, spell_name, content_type, verdict, *,
            ci=(None, None), n=None, chars=None, detail=None,
            realm=None, season=None):
    conn.execute(
        """INSERT INTO inference_findings
             (computed_at, question, spell_id, spell_name, content_type, realm, season,
              verdict, ci_low, ci_high, sample_size, character_count, detail_json)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (_now(), question, spell_id, spell_name, content_type, realm, season,
         verdict, ci[0], ci[1], n, chars,
         json.dumps(detail, default=str) if detail is not None else None))


# ---------------------------------------------------------------------------
# crit table
# ---------------------------------------------------------------------------

def infer_crit_table(conn, spell_id, spell_anchor_ids, *, melee_anchor_name="Auto Attack",
                     content_type=None, patch_touched_dates=(), record=True):
    """Within-character anchor comparison. Returns the finding dict.

    `spell_anchor_ids`: iterable of spell ids with doc-confirmed
    `crit_table='spell'` — supplied by the caller from ascension.db.
    """
    anchor_set = set(spell_anchor_ids)
    rows = conn.execute("""
        SELECT ap.scope_id, ap.character_id, ap.spell_id, ap.spell_name,
               ap.hits, ap.crits, e.content_type, cs.captured_at, cs.realm, cs.season
        FROM ability_performance ap
        JOIN capture_scopes cs ON cs.scope_id = ap.scope_id
        LEFT JOIN encounters e ON e.encounter_id = cs.encounter_id
        WHERE ap.is_pet = 0 AND ap.hits >= ? AND
              (ap.spell_id = ? OR ap.spell_name = ? OR ap.spell_id IN
                 (SELECT value FROM json_each(?)))
    """, (MIN_HITS_PER_CHAR, spell_id, melee_anchor_name,
          json.dumps(sorted(anchor_set)))).fetchall()

    spell_name = None
    per_char = {}       # (scope, char) -> {'target':(h,c), 'melee':(h,c), 'spell':(h,c)}
    realm = season = None
    for (scope, char, sid, name, hits, crits, ct, captured_at, r, s) in rows:
        if content_type is not None and ct is not None and ct != content_type:
            continue
        if any(captured_at and d and captured_at[:10] >= d for d in patch_touched_dates):
            bucket_suffix = "post_patch"
        else:
            bucket_suffix = "pre_patch" if patch_touched_dates else ""
        key = (scope, char, bucket_suffix)
        slot = per_char.setdefault(key, {})
        realm, season = realm or r, season or s
        if sid == spell_id:
            spell_name = spell_name or name
            slot["target"] = (hits, crits)
        elif name == melee_anchor_name:
            slot["melee"] = (hits, crits)
        elif sid in anchor_set:
            h, c = slot.get("spell", (0, 0))
            slot["spell"] = (h + hits, c + crits)

    votes = {"melee": 0, "spell": 0, "none": 0}
    usable, pooled_hits, no_discriminator = [], 0, 0
    for key, slot in per_char.items():
        if "target" not in slot or "melee" not in slot or "spell" not in slot:
            continue
        th, tc = slot["target"]
        mh, mc = slot["melee"]
        sh, sc = slot["spell"]
        if min(mh, sh) < MIN_HITS_PER_CHAR:
            continue
        m_rate, s_rate = 100 * mc / mh, 100 * sc / sh
        t_rate = 100 * tc / th
        # the third bucket first: a ~0% crit rate while BOTH anchors crit
        # normally is a cannot-crit periodic, not a melee-table ability
        if t_rate < 1.0 and min(m_rate, s_rate) >= 5.0:
            vote = "none"
        elif abs(m_rate - s_rate) < MIN_ANCHOR_SEPARATION:
            no_discriminator += 1
            continue
        else:
            vote = "melee" if abs(t_rate - m_rate) < abs(t_rate - s_rate) else "spell"
        votes[vote] += 1
        pooled_hits += th
        usable.append({"key": key[:2], "target_pct": round(t_rate, 1),
                       "melee_anchor_pct": round(m_rate, 1),
                       "spell_anchor_pct": round(s_rate, 1), "hits": th, "vote": vote})

    n_chars = len({u["key"][1] for u in usable})
    total_votes = sum(votes.values())
    if pooled_hits < MIN_POOLED_HITS_CRIT or total_votes < 3 or n_chars < 3:
        verdict = "insufficient_sample"
    elif no_discriminator and total_votes < no_discriminator:
        verdict = "insufficient_discriminator"
    else:
        winner = max(votes, key=votes.get)
        agreement = votes[winner] / total_votes
        verdict = f"propose:{winner}" if agreement >= 0.8 else "conflicting_votes"

    finding = {
        "question": "crit_table", "spell_id": spell_id, "spell_name": spell_name,
        "verdict": verdict, "votes": votes, "pooled_target_hits": pooled_hits,
        "character_scopes_usable": total_votes,
        "character_scopes_no_discriminator": no_discriminator,
        "samples": usable[:40],
        "method": "within-character anchor comparison (per-parse stats do not exist)",
    }
    if record:
        _record(conn, "crit_table", spell_id, spell_name, content_type,
                verdict, n=pooled_hits, chars=n_chars, detail=finding,
                realm=realm, season=season)
    return finding


# ---------------------------------------------------------------------------
# hit check / avoidance
# ---------------------------------------------------------------------------

def infer_hit_check(conn, spell_id, *, content_type=None, record=True):
    """Pooled avoidance, with the immunity/roll split made explicit.

    Verdict `propose:rolls_hit_check=0` needs zero miss+dodge+parry over a
    large pooled sample. Targets that full-resist everything while landing
    nothing are reported as `immune_like_targets`, not folded into a rate.
    """
    rows = conn.execute("""
        SELECT av.target_character_id, av.spell_name,
               SUM(av.hit_count), SUM(av.miss_count), SUM(av.dodge_count),
               SUM(av.parry_count), SUM(av.resist_count), SUM(av.resist_full_count),
               SUM(av.immune_count), MIN(e.content_type)
        FROM ability_avoidance av
        JOIN capture_scopes cs ON cs.scope_id = av.scope_id
        LEFT JOIN encounters e ON e.encounter_id = cs.encounter_id
        WHERE av.spell_id = ?
        GROUP BY av.target_character_id
    """, (spell_id,)).fetchall()

    name = None
    hits = miss = dodge = parry = partial = full = immune = 0
    immune_like = []
    for (tid, sname, h, m, d, p, rp, rf, im, ct) in rows:
        if content_type is not None and ct is not None and ct != content_type:
            continue
        name = name or sname
        h, m, d, p, rp, rf, im = [x or 0 for x in (h, m, d, p, rp, rf, im)]
        if h == 0 and (rf > 0 or im > 0):
            immune_like.append({"target": tid, "full_resists": rf, "immunes": im})
            continue
        hits += h
        miss += m
        dodge += d
        parry += p
        partial += rp
        full += rf
        immune += im

    avoidable = miss + dodge + parry
    attempts = hits + avoidable + full
    ci = _wilson(avoidable, attempts) if attempts else (None, None)
    if attempts < MIN_POOLED_HITS_AVOID:
        verdict = "insufficient_sample"
    elif avoidable == 0 and full == 0:
        verdict = "propose:rolls_hit_check=0,can_be_full_resisted=0"
    elif avoidable == 0:
        verdict = "propose:rolls_hit_check=0"
    else:
        verdict = "avoidable"

    finding = {
        "question": "rolls_hit_check", "spell_id": spell_id, "spell_name": name,
        "verdict": verdict, "attempts": attempts, "hits": hits,
        "miss": miss, "dodge": dodge, "parry": parry,
        "partial_resists": partial, "full_resists": full, "immunes": immune,
        "avoided_ci_95": [ci[0], ci[1]],
        "immune_like_targets": immune_like[:20],
        "immune_like_target_count": len(immune_like),
        "caveat": "target level not recorded; partitioned by content_type only",
    }
    if record:
        _record(conn, "rolls_hit_check", spell_id, name, content_type, verdict,
                ci=ci, n=attempts, detail=finding)
    return finding


def infer_partial_resist(conn, spell_id, *, content_type=None, record=True):
    """Partial-resist incidence per landed hit (school chip, §1 refinement)."""
    rows = conn.execute("""
        SELECT SUM(av.hit_count), SUM(av.resist_count), MIN(av.spell_name)
        FROM ability_avoidance av
        JOIN capture_scopes cs ON cs.scope_id = av.scope_id
        LEFT JOIN encounters e ON e.encounter_id = cs.encounter_id
        WHERE av.spell_id = ? AND (? IS NULL OR e.content_type = ? OR e.content_type IS NULL)
    """, (spell_id, content_type, content_type)).fetchone()
    hits, partial, name = (rows[0] or 0), (rows[1] or 0), rows[2]
    ci = _wilson(partial, hits) if hits else (None, None)
    verdict = ("insufficient_sample" if hits < MIN_POOLED_HITS_AVOID
               else ("propose:partial_resist=yes" if partial else "propose:partial_resist=none_observed"))
    finding = {"question": "partial_resist", "spell_id": spell_id, "spell_name": name,
               "verdict": verdict, "hits": hits, "partial_resists": partial,
               "rate_ci_95": [ci[0], ci[1]]}
    if record:
        _record(conn, "partial_resist", spell_id, name, content_type, verdict,
                ci=ci, n=hits, detail=finding)
    return finding


# ---------------------------------------------------------------------------
# proc rate
# ---------------------------------------------------------------------------

def infer_proc_rate(conn, proc_spell_id, trigger_spell_ids, *, per="casts",
                    content_type=None, record=True):
    """Observed proc hits per trigger event, per character-scope, pooled.

    An OBSERVATIONAL rate: triggers and procs are counted in the same scope,
    so rotation mix varies by character. Good for order-of-magnitude and for
    detecting proc-blind feeders (a trigger with procs ≈ 0 across many
    characters while others produce them), not for a clean PPM.
    """
    trig = json.dumps(sorted(set(trigger_spell_ids)))
    rows = conn.execute(f"""
        SELECT ap.scope_id, ap.character_id,
               SUM(CASE WHEN ap.spell_id = ? THEN ap.hits ELSE 0 END) AS proc_hits,
               SUM(CASE WHEN ap.spell_id IN (SELECT value FROM json_each(?))
                        THEN ap.{'casts' if per == 'casts' else 'hits'} ELSE 0 END) AS trig_n,
               MIN(ap.spell_name)
        FROM ability_performance ap
        WHERE ap.is_pet = 0 AND (ap.spell_id = ? OR ap.spell_id IN
              (SELECT value FROM json_each(?)))
        GROUP BY ap.scope_id, ap.character_id
    """, (proc_spell_id, trig, proc_spell_id, trig)).fetchall()

    samples = [(ph, tn) for (_s, _c, ph, tn, _n) in rows if tn and tn > 0]
    total_procs = sum(p for p, _ in samples)
    total_trigs = sum(t for _, t in samples)
    rates = sorted(p / t for p, t in samples)
    if len(samples) < 5 or total_trigs < 100:
        verdict = "insufficient_sample"
    else:
        verdict = f"observed_rate:{total_procs / total_trigs:.3f}_per_{per}"
    finding = {
        "question": "proc_rate", "proc_spell_id": proc_spell_id,
        "trigger_spell_ids": sorted(set(trigger_spell_ids)), "per": per,
        "verdict": verdict, "total_procs": total_procs, "total_triggers": total_trigs,
        "character_scopes": len(samples),
        "rate_median": rates[len(rates) // 2] if rates else None,
        "rate_p10_p90": [rates[int(len(rates) * .1)], rates[int(len(rates) * .9)]]
        if len(rates) >= 10 else None,
        "caveat": "observational (same-scope counting); rotation mix varies by character",
    }
    if record:
        _record(conn, "proc_rate", proc_spell_id, None, content_type, verdict,
                n=total_trigs, chars=len(samples), detail=finding)
    return finding


def infer_coefficient(conn, spell_id, term, *, record=True):
    """Coefficient regression across characters — currently an HONEST REFUSAL.

    The regression the phase doc describes needs each character's stats AT THE
    PARSE. Phase 0 established those do not exist in the crawl; the armory
    snapshot's stats are gear-only AND lag the parse by `snapshot_lag_hours`,
    and path grants (PoI's ×2.0 SP doubling, Duality's broken cycling) move
    the true stat by more than the effect being fitted. Running the regression
    anyway would produce a confident number whose error is dominated by an
    unrecorded input — the exact failure §2 exists to prevent.

    The function exists so the refusal is recorded per spell (visible in the
    review queue) instead of the capability silently missing. It unlocks when
    per-parse stats exist — Phase 3 T5's self-snapshot for the owner, or a
    future API change for everyone else.
    """
    name = conn.execute(
        "SELECT spell_name FROM ability_performance WHERE spell_id = ? LIMIT 1",
        (spell_id,)).fetchone()
    verdict = "refused:no_per_parse_stats"
    finding = {
        "question": "coefficient", "spell_id": spell_id,
        "spell_name": name[0] if name else None, "term": term, "verdict": verdict,
        "unblocks_when": "per-parse character stats exist (Phase 3 T5 self-snapshot)",
    }
    if record:
        _record(conn, "coefficient", spell_id, finding["spell_name"], None,
                verdict, detail=finding)
    return finding


# ---------------------------------------------------------------------------
# sweeps
# ---------------------------------------------------------------------------

def top_played_spells(conn, limit=50):
    """Most-pooled damage abilities: the sweep targets."""
    return conn.execute("""
        SELECT ap.spell_id, MIN(ap.spell_name), SUM(ap.hits) AS pooled_hits,
               COUNT(DISTINCT ap.character_id) AS characters
        FROM ability_performance ap
        WHERE ap.is_pet = 0 AND ap.spell_id IS NOT NULL AND ap.spell_id > 0
          AND ap.damage_total IS NOT NULL
        GROUP BY ap.spell_id
        ORDER BY pooled_hits DESC LIMIT ?
    """, (limit,)).fetchall()


def run_sweep(conn, spell_anchor_ids, *, limit=50, patch_touched=lambda sid: ()):
    """Crit-table + hit-check + partial-resist proposals for the top-played
    abilities. `patch_touched(spell_id)` -> iterable of patch dates that
    touched it (caller derives from ascension.db)."""
    conn.execute("DELETE FROM inference_findings WHERE promoted = 0")
    results = []
    for spell_id, name, pooled, chars in top_played_spells(conn, limit):
        f1 = infer_crit_table(conn, spell_id, spell_anchor_ids,
                              patch_touched_dates=tuple(patch_touched(spell_id)))
        f2 = infer_hit_check(conn, spell_id)
        f3 = infer_partial_resist(conn, spell_id)
        results.append({"spell_id": spell_id, "spell_name": name,
                        "pooled_hits": pooled, "characters": chars,
                        "crit_table": f1["verdict"], "hit_check": f2["verdict"],
                        "partial_resist": f3["verdict"]})
    return results
