#!/usr/bin/env python3
"""Phase 1 T6 (session 1c): open_questions + retractions backfill, and the
fact→spell link derivation.

Sources for the backfill: PROGRESS.md's open-questions and plan-changes tables,
the primer's assumption register and retraction history, and
build_paladin-hammerdin.md §9/§12. Nothing here is new research — every row
traces to a statement already made in a committed doc.

Discipline (same as seed_confirmed.py): this file is APPEND-ONLY SOURCE OF
TRUTH for open_questions and retractions. Resolving a question = editing its
row here (status, resolved_by_fact_topic) in the session that resolved it —
never UPDATE the db directly, the next rebuild would silently revert it.

fact_spell_links is different: it is DERIVED (core/spells/epistemics.py) from
confirmed_facts text each rebuild, so it has no hand-curated rows here.
"""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from config import DB_PATH  # noqa: E402
import config  # noqa: E402

# Piped/redirected stdout defaults to cp1252 on Windows and this file
# prints non-ASCII; without this it dies with UnicodeEncodeError only when
# its output is captured. See config.ensure_utf8_stdout.
config.ensure_utf8_stdout()
from core.db.schema import create_phase1_schema  # noqa: E402
from core.spells.epistemics import (  # noqa: E402
    find_answered_questions, link_facts_to_spells,
)

conn = sqlite3.connect(str(DB_PATH))
create_phase1_schema(conn)   # idempotent; makes standalone runs safe
cur = conn.cursor()

# --------------------------------------------------------------------------
# open_questions — (slug, question, blocks, status, resolved_by_fact_topic,
#                   affected_spell_ids, opened_at)
# variance_contribution stays NULL until Phase 2's sensitivity analysis exists;
# T8 falls back to a dependent-count until then.
# --------------------------------------------------------------------------
QUESTIONS = [
    ('coefficient_source_precedence_177_conflicts',
     'The scrape-over-tooltip precedence in _COEFF_SOURCE_RANK is a judgement call now load-bearing on 177 (spell, term, component) triples where export_tooltip and db_ascension_gg_scraped state DIFFERENT coefficients - Mongoose Bite AP 0.20 vs 0.45, Holy Wrath SP 0.15 vs 0.07 - out of 323 same-triple pairs overall. The precedence itself is APPROVED and is NOT what this question asks: preferring the scrape is well-argued (it states the APPLIED value, it carries an enforced check digit against our independently decoded flat, and the catalog stores the wrong rank for ~half of multi-rank cards). What was missing is that the choice was INVISIBLE. Until 3d the losing value never entered spell_mechanics.conflicts_json - it was NULL for all 177 - and cli/mechanics.py printed a "rows with a source conflict" count that omitted every one of them, so the operator was shown a number that was wrong by ~177 while the tooltip-vs-scrape disagreement looked like it did not exist. 3d C3 routes them into conflicts_json under keys of the form coefficient:<term>:<component>@<source_spell_id> and reports FIELD conflicts and COEFFICIENT conflicts as separate counts. Deliberately NOT done: setting confidence=conflict on those rows, which would claim the mechanics are undecided when an approved precedence has decided them, and would fire ability_model conflict warnings on 177 behaving-as-intended spells. WHAT CLOSES THIS: a human review pass over the 177 now that they are queryable, spot-checking a sample against live tooltips, and either ratifying the precedence or naming the classes of spell where it should invert. 🛑 Do not close it by fitting - a coefficient chosen because it makes a calibration fit better is a fitted parameter wearing a source string.',
     'Nothing today - the sim uses the precedence winner. Blocks any claim that coefficient provenance has been REVIEWED rather than merely recorded.',
     'open', None, None, '2026-08-06'),
    ('armor_pen_divisor_5_vs_4_2',
     'Is armor penetration 5 or 4.2 rating per 1% at level 60? The site calculator says 5, the client gtCombatRatings says 4.2; every other level-60 divisor agrees exactly across both sources. Settle with a level-60 in-game armor-pen reading.',
     'Physical-build stat weights only', 'open', None, None, '2026-08-04'),
    ('max_report_id',
     'What is the current maximum ascensionlogs report ID? No list endpoint exists; it emerges from a full crawler run. Sizes the historical backfill.',
     'Backfill sizing', 'open', None, None, '2026-08-04'),
    ('capped_level_scaling_engine_formula',
     'Does the engine apply max_level the way min(level, max_level) assumes? 1,653 spells carry a real cap, 196 of the 354 level-scaled catalog spells among them. Hammer from the Heavens could not test it (max_level=0). Settle opportunistically: check one CAPPED level-scaled spell\'s in-game tooltip against the computed value.',
     'Level-scaled flats on the 196 capped spells', 'open', None, None, '2026-08-04'),
    ('talent_amplifier_review_queue',
     '243 talent_amplifiers rows are flagged needs-manual-review and contribute no graph edges. Owner decision 2026-08-05: pre-classify with evidence into a review file; NOTHING enters spell_relationships until the owner approves a batch.',
     'Amplifier coverage of the relationship graph', 'in_progress', None, None, '2026-08-05'),
    ('current_pool_vs_bisbeard_97_gap',
     'What explains the 97-card gap between in_current_pool=1 (3,129) and BisBeard\'s S10 count (3,226)? Intersect BisBeard\'s entryId list against in_current_pool=1 and inspect the difference.',
     'Exactness of the card-pool scope', 'open', None, None, '2026-08-04'),
    ('class_origin_five_conflicts',
     'Which of the 5 recorded class_origin conflicts is right? Proc test or live tooltip per spell. Note Fel Infused Weapon\'s previous value ("Duality") was a Path, not a class — a data-entry error, already corrected to conflict status.',
     'class_origin correctness for 5 spells', 'open', 'fel_infused_weapon_class_three_way', '276076', '2026-08-04'),
    ('bisbeard_item_json_host',
     'Where is BisBeard\'s item JSON actually served from? Read the base-URL construction in its itemDatabaseSync chunk, or ask the author.',
     'Phase 3 T4 gear data source', 'open', None, None, '2026-08-04'),
    ('item_dbc_layout_stability',
     'Are Item.dbc / ItemStat.dbc layouts stable enough to extract (1,513,931 records, layout unverified)? Extract a handful of known items and compare against in-game tooltips.',
     'A gear database with no third-party dependency', 'open', None, None, '2026-08-04'),
    ('ca_raw_int_slots_meaning',
     'What do CharacterAdvancement slots 14/15/17/21/25/29-41 mean? Correlate raw_ints_json against known card properties — no re-extraction needed.',
     'Acquisition / prerequisite modelling (Phase 4)', 'open', None, None, '2026-08-04'),
    ('fel_infused_weapon_per_level_3x',
     'Fel Infused Weapon per-level term: db.ascension.gg renders 4.5/level, client DBC says 1.5 — exactly 3x. db was byte-faithful on Holy Supernova, so suspect a rank/variant (276069 vs 276076) or stale snapshot. Settle with an in-game tooltip read at level 60 (tier 1, beats both).',
     'The card\'s flat damage component', 'open', 'dbc_real_points_per_level_is_a_rate_not_a_flat_add', '276069,276075,276076', '2026-08-04'),
    ('elric_active_path_and_duality_ap_anomaly',
     'Two residuals after the Duality amp was "confirmed real" (1.895x, controlled empty-spec test): (1) is Elric\'s CURRENT board actually on Path of Duality, and (2) the anomaly — Attack Power at 0.548x the Path of Strength value under Duality, contradicting "AP = highest of Str or Agi". RESOLVED 2026-08-05 (session 2d), and BOTH halves turned out to be the same external cause. (1) The owner confirmed Path of Duality on his current board, then captured all three paths with a RELOG between each: PoS Str 155 / AP 348 / SP 250, PoI Int 259 / AP 141 / SP 638, PoD Int 199 / AP 307 / SP 271. (2) THE 0.548x IS NOT A CONVERSION RATE - it is an OFF-phase reading of a cycling bug. Path of Duality (129243) is reported broken by multiple independent players: its AP bonus switches ON and OFF roughly every 10-15 seconds, indefinitely, while standing still (one player watched 832 <-> 1128, a delta equal to their Strength). Elric\'s 174 <-> 307 is the same oscillation: 160 x 1.10 Deadliness = 176 with the Strength bonus off, (160+121) x 1.10 = 309 with it on, and 174/307 = 0.567 against the 0.548 originally recorded. When the bonus IS applying, the tooltip\'s "AP = highest of Str or Agi at 100%" is exactly what the server does. The SP half resolved the same way: Duality grants a flat ~+19 SP (independently reported by another player as "a difference of 19 Spellpower") and NO amplifier - see retraction duality_sp_amp_1895_confirmed. NEW STANDING ADVISORY, not a residual of this question: Duality parses are unusable for absolute calibration until a fix lands, and the owner has moved to Path of Intelligence. Tracked in bugs/bug_path-of-duality-broken.md with changelog keywords for fix detection.',
     'SP weight (1.00 vs ~1.77) and AP posture in build_paladin-hammerdin §10', 'resolved', 'path_of_duality_is_broken_ignore_its_parses', '129243', '2026-08-04'),
    ('titans_grip_tax_on_holystrike',
     'Does the Titan\'s Grip -10% physical tax apply to Holystrike\'s weapon-damage half?',
     'Titan\'s Grip A/B verdict; Holystrike ability valuations', 'open', None, None, '2026-08-02'),
    ('brutal_crusader_effect',
     'What does "Brutal Crusader" on Light\'s Hope actually do? If it is a Crusader-family Str proc it changes Str\'s weight.',
     'Chase-weapon choice (Light\'s Hope vs alternatives)', 'open', None, None, '2026-08-02'),
    ('mental_quickness_exclusivity',
     'Does Mental Quickness pool with Holy Focus\'s capstone or Answered Prayers, or does it share an exclusivity bucket with either?',
     'Whether Mental Quickness 4/5 is a live slot', 'open', None, None, '2026-08-02'),
    ('dark_justicar_consume_vs_hold',
     'Dark Justicar consume-vs-hold once acquired: Judgement eats 10 SoV stacks for burst but drops Inevitable Vengeance\'s stacking debuff to zero. Which nets more?',
     'Rotation priority once Dark Justicar lands', 'open', None, None, '2026-08-02'),
    ('lightbound_cleave_post_patch_procs',
     'Re-verify Lightbound Cleave\'s proc behavior post-2026-08-03 patch ("fixed... proc effects triggered by abilities not on the GCD, including Cleave... restores intended proc behaviour"). The confirmed "0 Hammerdin procs" verdict predates this fix; check what LC does and does not feed now (Hammerdin, JotTH, PBL). RESOLVED 2026-08-05 (session 2d) by an isolation test: 204 seconds pressing ONLY Lightbound Cleave over autos on one dummy, then a 72-second normal-rotation control window in the same log. From 53 isolated LC hits and 70 white swings: ZERO Hammerdin procs (the pre-patch verdict survives - at Dawnreaver\'s measured 13-17% rate, 53 casts predicts about 7, so a true zero is under 0.1% likely); ZERO Purification By Light events, while the control window produced 14 Consecrations and 2 Exorcisms proving the engine was alive - NEW, and notable because LC is 65% weapon damage and PBL\'s intake reads "weapon-damage spells and abilities", so the intake is narrower than its wording; and all 7 Seal of Command riders landed at exactly 0.00 s from a white swing and ~3 s from any LC hit, i.e. autos only. Judgement of the Three Hammers got NO verdict - it is a pressed ability and was never cast in either window. NET: Lightbound Cleave feeds none of this build\'s engines, which is also what makes it portable (see the Cleave Kit).',
     'LC\'s engine interactions; §2 class-tag table currency', 'resolved', 'lightbound_cleave_feeds_no_engine_post_patch', '907300', '2026-08-03'),
    ('hammerdin_trigger_set_excludes_trigger_delivered_damage',
     'Hammerdin (282983) states 20% on damaging Paladin abilities, but MEASURED on 2026-08-05 it procs from Dawnreaver (15-17 / 119 casts) and Hammer of Wrath (~16%) while Holy Shock gave 1 proc in 78 casts and Judgement 0 in 51 - combined 1 where ~26 is predicted (p < 1e-9). Submitted as tracker 200295. THE OPEN QUESTION IS THE MECHANISM AND ITS SCOPE: the failing abilities are exactly those that deliver damage through a SECOND spell (Holy Shock 20930 is a dummy whose damage is sub-spell 25902; a Judgement press damages via the seal, logged as 20467), so the proc check may be blind to trigger-delivered damage. IF THAT GENERALISES IT AFFECTS EVERY "damaging X abilities" ENGINE ON THE SERVER, which would be a major modelling fact rather than one card\'s bug. Settle by isolation-testing a second engine with a trigger-delivered feeder: Judgement of the Three Hammers (wide intake, "any direct damage") and Purification By Light are both available on this character, and PBL already showed a narrower-than-worded intake in the same session. Also re-check on any patch that touches Hammerdin - see the watch list in bugs/README.md.',
     'Every proc-engine intake model; build_paladin-hammerdin §2 class-tag table and §11 rotation priority', 'open', 'hammerdin_does_not_proc_from_holy_shock_or_judgement', '282983,20930,20467,903158,24239', '2026-08-05'),
    ('siphon_health_and_swift_retribution_sources_unknown',
     'Two effects appear on Elric that no slotted card explains. (1) SIPHON HEALTH (18652) deals ~44-48 per tick, 40-60 ticks per 10-minute window, in every 2026-08-05 log - it is not in the 55-id board export. (2) SWIFT RETRIBUTION appears on his buff bar as spell 853484 ("increases spell haste by X%") with no identified source; it is NOT the catalog talent 53648, which is not slotted. Both are small, but an unattributed damage source and an unattributed haste buff both corrupt calibration if left unmodelled, and the haste one changes GCD and swing timing. Settle by hovering each in game (source is usually named in the tooltip footer) or by checking whether either is granted by an equipped item or a set bonus.',
     'Completeness of the modelled passive layer; small calibration residuals', 'open', 'elric_board_and_passive_layer_confirmed_from_addon_and_log', '18652,853484', '2026-08-05'),
    ('duality_bug_fix_watch',
     'STANDING WATCH, not a research question: Path of Duality (129243) is broken in ~6 reported ways (AP bonus cycling on/off every 10-15 s, SP grant reduced to a flat 19, weapon-type passives dead, AP added after modifiers, Twin Flurry main-hand only, bonus Str/Agi not applying). The owner has stopped playing it and the project treats its parses as unusable for absolute calibration. RESOLVE THIS QUESTION WHEN A FIX SHIPS, then: re-capture the three-path trio with relogs, re-open the Duality parameters in core/builds/stats.py (SP amp, AP factor, the disabled weapon clauses), revisit primer section 3\'s Duality block, and re-evaluate whether Duality is recommendable. Detection: scan the daily changelog capture for Duality / attack power / spell power / path. See bugs/bug_path-of-duality-broken.md.',
     'Whether Path of Duality can be modelled, calibrated against, or recommended', 'open', 'path_of_duality_is_broken_ignore_its_parses', '129243', '2026-08-05'),
    ('improved_cleave_lc_share_remeasure',
     'Lightbound Cleave\'s total-damage share needs re-measuring once Improved Cleave is acquired — the corrected (9+AP)x2.2 bonus-term formula (v9) predicts a large gain but has not been checked against a fresh parse.',
     'Chase-list ranking of Improved Cleave (§7 2b)', 'open', None, '907300', '2026-08-03'),
    ('nurturing_instinct_healing_clause',
     'Is Nurturing Instinct\'s Agility-scaled healing clause touching anything in the kit at all (Holy Shock / Holy Finish healing components)? Assumed dead/marginal on tooltip reading alone; not proc-tested.',
     'Whether it stays reroll-first on the §7 list', 'open', None, None, '2026-08-03'),
    ('reroll_upgrade_chance_slot_scope',
     'Does the elevated upgrade-roll chance for held partial-rank talents apply to rerolls of ANY slot, or only the slot currently holding the card?',
     'Reroll strategy for partial-rank upgrade fishing', 'open', None, None, '2026-08-02'),
    ('necrosis_school_changes_across_ranks',
     'Necrosis genuinely changes damage school across its own ranks (0 -> 32 Shadow -> 1 Physical) and is in the current pool. Nothing in the docs explains a rank-variant school. Recorded as a conflict, unresolved.',
     'The assumption that a card\'s school is rank-invariant', 'open', None, None, '2026-08-04'),
    ('winds_of_winter_crit_source',
     'Winds of Winter\'s observed 91.7-100% crit rate is not fully explained by the one confirmed crit source (Killing Machine, 9 procs vs 11-12 crits). Pending a trinket-proc check the player would have to do themselves.',
     'Nothing of ours — external build reference only', 'open', None, '274121', '2026-08-03'),
    ('reloadui_in_combat',
     'Is ReloadUI() callable IN COMBAT? Not needed for the intended out-of-combat capture flow; recorded for completeness.',
     'Nothing currently', 'open', None, None, '2026-08-04'),
    ('rank_line_ambiguities_25',
     '25 rank lines are genuinely ambiguous — several spells tie for the top rank available at 60 (all-Rank-1 lines like Desolation; other-realm 11-prefix pulls like Arcane Focus). The crosswalk returns the candidate list and no answer; spell_mechanics carries no sibling for them.',
     'Level-60 magnitudes for those 25 lines', 'open', None, None, '2026-08-04'),
    ('trigger_attributed_coefficients_not_in_spell_scaling',
     'Hammer from the Heavens\' confirmed +9.1% SP / +9.1% AP (three-source, session 1x) existed only in doc prose — spell_scaling had no rows for 282987, so the resolver served the flat 122-145 without the stat terms (~45% understatement at AP 584/SP 533). DECISION (owner, 2026-08-05, same day): coefficients live on the trigger TARGET — seed_hand_coefficients.py now owns tier-3 db_ascension_gg rows keyed to 282987, never duplicated onto the cards. RESOLVED (session 2b, 2026-08-05): core/spells/mechanics.py::_formula_terms now pulls spell_scaling per component source_spell_id, not per card. The walk is INHERITED rather than re-done — component sources come from the rows spell_effect_values already holds, so 1b\'s bounds (depth <= 2, cycle-safe, single-path, out-of-catalog only) apply unchanged; hidden_ref sources are deliberately not followed because their coefficients already land on the card id as dbc_hidden_formula and following them too would double-count. Attributed terms carry via/source_spell_id/evidence chain and stay confidence=inferred, never a calibration anchor. Verified end-to-end: Hammerdin (282983) now resolves to 223.6-246.6 per hit at AP 584/SP 533, matching build doc §12\'s confirmed 224-247, against flat-only 122-145 before. Required a second fix: ability_model._components deduped coefficients by term name alone, which would have silently dropped one of Hour of Judgement\'s own SP 0.05 and HftH\'s attributed SP 0.091 — now keyed on (source_spell_id, term).',
     'Sim accuracy for trigger-reached abilities (HftH first among them)', 'resolved', 'trigger_reached_coefficients_served_per_component_source', '282983,282984,282987', '2026-08-05'),
    ('consecration_and_dawn_strike_calibration_outliers',
     'Two abilities missed their school group in 2b\'s calibration - Consecration at 3.55x against a Holy group near 1.76x, and Dawn Strike at 1.11x against Holystrike peers near 1.40x. CONSECRATION IS RESOLVED (2c, gate G3), and the cause was in our own tooling rather than in the game or the data: calibrate_vs_log.py matched abilities by NAME, and the Consecration in Elric\'s log is spell 270768 - an out-of-catalog spell summoned by Purification By Light, spell_level 0, no rank line, its own per-level scaling - while the tool resolved the catalog\'s 26573. Different abilities that share a name, which is precisely what this project\'s "never relate two spell IDs by name" hard rule exists to prevent; it had simply never been applied to our own tools. EXORCISM had the same defect and the same cause (logged 270767, not the catalog\'s 879) and was producing a 1.08x that looked like a genuine low outlier. FIXED STRUCTURALLY: the tool now keys every ability on the log\'s own spellId field, so nothing is matched at all - the log states the id on every damage line. With that fix the Holy group is TIGHT at n=3, 1.97-2.15 (Hammer from the Heavens 2.14, Hour of Judgement 2.15, Holy Supernova 1.97) with no outlier, and Consecration and Exorcism correctly report as "not resolvable by the sim" instead of being silently mis-resolved. Same fix also revealed Seal of Command logs as 20424 (not 20375) and Consecrated Holy Weapon as 200818 (not the catalog\'s 200809 - confirming INDEX_GUIDE v3\'s refusal to assume those two were identical). DAWN STRIKE REMAINS OPEN - see dawn_strike_sim_base_is_systematically_too_high, which G2 re-specified.',
     'Accuracy of the Phase 2c talent multiplier fit', 'resolved', 'calibration_outliers_were_name_matching_the_wrong_spell', '26573,270767,270768,879,907894', '2026-08-05'),
    ('dawn_strike_sim_base_is_systematically_too_high',
     'Dawn Strike misses its Holystrike group in every log, always low - 1.43 / 1.17 / 1.11 / 1.13 against peers at 1.87 / 1.50 / 1.40 / 1.42 (pooled 1.22 against 1.55-1.59). A bias that reproduces in every sample is neither noise nor buff state. 2b proposed a cause: effect type 121 (normalized weapon) being double-counted alongside type 31 (weapon-percent), which would affect every ability carrying 121. GATE G2 TESTED THAT AND IT IS WRONG ON BOTH HALVES. First, the scope check: Lightbound Cleave is effects [58,31], Whirling Light [31,64] and Dawnreaver [31] - NONE of the three anchors carries type 121, at the catalog rank or at the level-60 rank. So their 1.87/1.87/1.88 agreement is three independent confirmations, not one shared bias, and 2b\'s base-formula validation STANDS rather than being downgraded. Dawn Strike is the only type-121 carrier in the sample, exactly the branch that leaves the anchors intact. Second, the mechanism check: the resolver does not treat 121 as a weapon swing at all - core/spells/mechanics.py puts it in DAMAGE_EFFECTS and it falls through to the flat branch, so Dawn Strike\'s 121 slot contributes its basepoints as a FLAT 68, not a swing. There is no double count to remove; if there were, the base would be roughly 1,100 rather than 476 and the ratio would be near 0.5. WHAT IS ACTUALLY TRUE: at the level-60 rank Dawn Strike (907901) resolves to 68 + WEAPON*0.65 and Lightbound Cleave (907304) to 62 + WEAPON*0.65 - near-identical modelled formulas, sim bases 476 and 470 - yet the game pays Dawn Strike 528 where it pays Lightbound Cleave 661 in the same log. So the question is no longer "why is our base too high" but "which multiplier does Lightbound Cleave receive that Dawn Strike does not", which makes this a TALENT question and T4b\'s to answer, not a data-extraction one. Note the class tags do not obviously explain it: Dawn Strike borrows Sinister Strike (Rogue) while Lightbound Cleave and Whirling Light borrow Cleave and Whirlwind (Warrior) - but Dawnreaver borrows Crusader Strike (Paladin) and tracks the Warrior pair, so it is not a simple class gate. Two candidates worth checking first: a talent whose EffectSpellClassMask covers the Warrior and Paladin abilities but not the Rogue one, and whether Dawn Strike is normalized-weapon in the ENGINE (normalized 2H speed 3.3 against Elric\'s actual 3.57 would cost it 7.6%, which is a third of the gap and not all of it). ALSO NOTE: 161 catalog cards carry type 121 and 158 of those pair it with type 31, so whatever the resolution is, it generalises widely - 80 of them are in the current pool.',
     'Dawn Strike\'s modelled damage, and the 158 catalog cards sharing its [121,...,31] effect shape', 'open', None, '907894,907901,907300,907304', '2026-08-05'),
    ('holy_holystrike_ratio_weapon_input_confound',
     'Session 2b\'s headline calibration quantity was the Holy divided by Holystrike ratio, 1.31, on the reasoning that whatever buff state multiplies both schools cancels in a ratio, leaving talent structure - and 2b named it "the number a correct talent model must reproduce". GATE G1 FINDS IT CONFOUNDED, and the ratio is DEMOTED: do not fit against it. A ratio cancels factors applied to BOTH sides; it does not cancel an input error applied to ONE. The two sides are not symmetric - measured composition is Whirling Light and Dawnreaver 100% weapon damage, Lightbound Cleave 87%, Dawn Strike 86%, against 0% for every Holy ability. The sim\'s weapon input came from the older King Gordok parse rather than from the same session as any log, so an error in it moves the Holystrike denominator alone and passes into the ratio at very nearly 1:1 (a 10% weapon error moves 1.31 by about 9%). It could not be un-confounded from the existing logs: white-swing maxima vary 1.52x across these four sessions (869 / 676 / 603 / 571) and that is equally consistent with a changed weapon and with changed physical multipliers, which cannot be separated without a character-sheet weapon read stamped to the same session as a parse. REPLACEMENT, and it is strictly better because it needs no weapon input at all: WEAPON-FREE PAIR RATIOS, now a first-class report in calibrate_vs_log.py. A same-school pair cancels weapon damage only at the extremes - both sides carrying no weapon term, or both being pure weapon-percent with no flat - and same-school means the school\'s whole talent stack cancels too, leaving the ratio of the two BASE FORMULAS, which is a claim about our data that a parse can check directly. Two such pairs exist in this kit and both REPRODUCE: Hammer from the Heavens over Hour of Judgement\'s own tick, predicted 1.718, observed 1.697/1.773/1.685/1.771 across four logs, worst delta 3.2%; and Dawnreaver over Whirling Light, predicted 0.769, observed 0.768/0.720/0.757 across three, worst delta 6.4%. These are what T4b should reproduce. TO UN-CONFOUND THE ABSOLUTE NUMBERS LATER, and it is free: capture a character-sheet screenshot (weapon damage, AP, SP) at the start of the next logged session, so one parse has a same-moment stat block.',
     'Any talent multiplier fitted in T4b/T8; 2b\'s 1.31 must not be used as a target', 'resolved', 'cross_school_ratio_demoted_use_weapon_free_pairs', '907300,907304,907780,903158,282984,282987', '2026-08-05'),
    ('effect_type_121_double_count_scope',
     'Asked by gate G2: if the three Holystrike anchors (Lightbound Cleave, Whirling Light, Dawnreaver) also carry effect type 121, then their 1.87/1.87/1.88 agreement is three instances of one shared bias rather than three independent confirmations, and 2b\'s base-formula validation would have to be downgraded to "consistent, not independently confirmed". MEASURED AND ANSWERED: they do not. Lightbound Cleave is [58,31], Whirling Light [31,64], Dawnreaver [31], at both the catalog id and the level-60 rank id. Dawn Strike is [121,80,31] at every one of its twelve ranks and is the only type-121 carrier in the calibration sample. THE ANCHORS STAND and 2b\'s validation claim needs no qualification. Catalog-wide scope for whenever the 121 semantics are settled: 161 cards carry it, 158 of them alongside type 31, and 80 are in the current pool. The mechanism half of 2b\'s suspicion was also wrong - the resolver never treats 121 as a swing, it falls through to the flat branch - see dawn_strike_sim_base_is_systematically_too_high for what that leaves open.',
     'Whether 2b\'s Holystrike base-formula validation holds', 'resolved', 'holystrike_anchors_do_not_carry_type_121', '907300,907780,903158,907894', '2026-08-05'),
    ('rank_siblings_inherit_no_hidden_refs',
     'Session 2b taught the numeric extractor to decode rank siblings (the level-60 id a catalog entry redirects to), closing a hole where 686 cards resolved to ZERO damage because the resolver correctly redirected to an id that had no spell_effect_values rows. The RESIDUAL gap: a sibling inherits no hidden_refs, because that column is parsed from the EXPORT tooltip and a sibling is by definition absent from the export. So a sibling whose own record is a DUMMY effect loses its sub-spell chain entirely. Holy Shock was the live case - catalog Rank 1 (20473) resolves through hidden refs 25912/25914, but the Rank 4 a level-60 character casts (20930) is a bare DUMMY (Effect [3,0,0], all base points zero) with no EffectTriggerSpell for the bounded walk to follow, so it simmed as 0 damage against 36 real casts averaging 1,380. RESOLVED (session 2c, 2026-08-05) in two halves. SERVING: resolve_numeric_formulas.py::sibling_hidden_refs parses the SIBLING\'s own spell_dbc_raw.description for $<id> tokens, exactly as build_index parses export tooltips. SCOPE: the sibling\'s refs were never extracted from the client either, because build_dbc_index scoped spell_dbc_raw to catalog ids + EXPORT hidden_refs + neighbours + siblings - so a --with-dbc re-extraction was needed, adding 797 rank-sibling sub-spell ids (15,769 -> 16,566 rows). Holy Shock R4 now decodes to 562-608 Holy damage (25902) and 676-732 healing (25903) and is a permanent VALIDATION anchor in resolve_numeric_formulas.py. Scope of the residual, now measured: 680 of the 686 unambiguous siblings carry a magnitude, and exactly 4 (Holy Shock 20930, Wyvern Sting 24133, Deep Freeze 44666, Penance 302003) have one ONLY through this path. 🛑 IMPORTANT read: this reads a POINTER out of a description string, never a magnitude - the number still comes from the referenced spell\'s numeric fields, so the Titanic Mutilate rule is intact. CONSEQUENCE: the optimal-vs-observed APL comparison is UNBLOCKED and inverts back - optimal 679 vs observed 659, restoring build_paladin-hammerdin §11\'s central conclusion, which the data gap had been contradicting.',
     'Damage of any ability whose level-60 rank resolves through sub-spells; Holy Shock is in the owner\'s rotation', 'resolved', 'rank_sibling_subspell_chain_recovered_from_dbc_description', '20473,20930', '2026-08-05'),
    ('holy_shock_bonus_coefficient_0429',
     'Holy Shock R4\'s damage sub-spell (25902) carries EffectBonusCoefficient = 0.429 and its healing sub-spell (25903) carries 0.807. The project rule (session 1x, catalog-wide) is that this field is stock 3.3.5 EffectBonusMultiplier - neutral value 1.0, and 0.429 = 1.5/3.5 is named there as one of the RECURRING non-defaults that are retail\'s cast-time formula rather than a stated coefficient. So the rule says do not read it as SP. But Holy Shock is a STOCK WotLK spell, not an Ascension custom card, and 0.429 is exactly retail Holy Shock\'s real spell coefficient - so for stock spells the field may be carrying the applied value after all, which is a different question from the one 1x answered (1x calibrated against 98 spells that STATE their own $SP*x, i.e. custom cards). THE DISCRIMINATOR WAS RUN (2c, all four logs with Holy Shock hits, against each log\'s own two Holy anchors HftH and the HoJ tick, so buff state is held fixed within each row). Sim base 585 with no SP term vs 814 with SP 0.429 at SP 533: log 20.51 3.15 vs 2.26 against anchors 2.46/2.49; log 21.18 2.51 vs 1.81 against 2.02/1.96; log 20.07 2.36 vs 1.70 against 1.74/1.78; log 20.37 2.51 vs 1.80 against 1.93/1.87. VERDICT: "no SP term" is falsified - it puts Holy Shock 26-34% ABOVE its own group in every log, the same reproduces-everywhere signature that condemned Dawn Strike. SP 0.429 puts it 3-9% BELOW the group in every log. So Holy Shock certainly has an SP coefficient and 0.429 is close, but consistently slightly too large - the residual is systematic, not noise, so either the coefficient is a little lower or Holy Shock collects slightly fewer talent multipliers than HftH and the HoJ tick do. 🛑 STILL NOT SEEDED, deliberately: entering 0.429 into spell_scaling would give it tier provenance the evidence does not support (the evidence supports "there is an SP term near 0.429", not "the term is 0.429"), and it would then be fitted against. Owner decision needed. MEANWHILE Holy Shock is EXCLUDED from the Holy-group constant, same treatment as Consecration - see consecration_and_dawn_strike_calibration_outliers. If the field is eventually trusted, the finding is narrower than the field: "for spells the client inherited from stock WotLK, EffectBonusCoefficient carries the applied coefficient", which needs its own catalog-wide check before generalising - and note it cannot be checked the way 1x checked it, since 1x calibrated against spells that state their own $SP*x, which stock spells do not. 🟡 OWNER DECISION 2026-08-06 (session 3a): seed the MEASURED ~0.40 (2d, n=40 unbuffed non-crits against HftH in the same log) as PROVISIONAL, not the client\'s 0.429 and not nothing. It lives on the damage sub-spell 25902 with source = "ascension_measured_provisional" in seed_hand_coefficients.py, deliberately under its own source string so it is filterable and visibly weaker than a stated coefficient. THIS QUESTION STAYS LIVE at in_progress: 0.40 is back-solved from the owner\'s parses, so it must never be used as a fit target against those same parses (2e\'s rule for the deliberately-unseeded Holy residual applies unchanged). WHAT CLOSES IT: a live in-game tooltip that states Holy Shock\'s coefficient, or any independent stating source. Until then the sim stops understating Holy Shock without anyone being able to mistake 0.40 for a measurement of the game rather than of a parse.',
     'Holy Shock damage (3.0% of the owner\'s parse) and, if it generalises, every stock-WotLK spell in the catalog', 'in_progress', None, '20473,20930,25902,25903', '2026-08-05'),
    ('periodic_trigger_delivery_pulse_count',
     'Session 2b established that trigger-reached damage can be delivered by a SPELL_AURA_PERIODIC_TRIGGER_SPELL slot, firing once per period for the aura\'s duration (Hour of Judgement: 500 ms over 10 s = 20 Hammer from the Heavens pulses per cast, alongside 5 ticks of its own 81). The RATIO is validated against real parses with no fitting - pooled 16,491 HftH hits / 4,332 HoJ hits = 3.81 against a predicted 4.00. What is NOT settled is the ABSOLUTE pulse count, because the ratio is invariant to duration: a 5 s duration would give 10 and 2.5 pulses and the identical 4.00 ratio. The absolute count rides entirely on dbc_spellduration index 1 = 10,000 ms, which is a tier-4 client read that no parse has yet confirmed. This matters because the pulse count multiplies the component\'s whole per-cast contribution - it is the single largest lever on the modelled damage of the owner\'s top ability. Settle by counting Hammer from the Heavens hits within one Hour of Judgement window in a SINGLE-TARGET parse (tools/log_parser/parse_log.py), where hits per cast equals the pulse count directly with no target-count confound. 34 cards use periodic-trigger delivery, so this generalises. Related guard: periods as low as 0.01 s appear in the data, which over a 10 s duration would imply 1,000 pulses; the ability model refuses any count above 100 rather than applying or clamping it, and those spells are unmodelled until someone checks what their period field means.',
     'Per-cast damage of all 34 cards with periodic-trigger delivery, Hour of Judgement first', 'open', None, '282984,282986,282987', '2026-08-05'),
    ('melee_crit_suppression_vs_higher_level',
     'Does Ascension apply melee crit suppression vs higher-level targets, and at what rate? The owner\'s own parse hints it exists (sheet melee crit 21.76% vs autos parsed at 16.2% — but n=37 swings, far too small per the sample-size rule). The sim\'s combat engine WARNS instead of modelling it (no fabricated retail constant). Settle with a large white-swing parse vs known-level targets. 🆕 2e EVIDENCE, first real constraint and it points AGAINST suppression: pooled white swings across the two PoI windows vs the level-63 dummy give 66 crits / 261 swings = 25.29% against a sheet-weighted expectation of 26.06% — difference −0.77 points at 1σ = 2.69, consistent with ZERO suppression. Not conclusive (a 3-point effect fits inside the error bar), so the question stays open and the engine keeps warning; a 1,000+ swing sample would discriminate. Two smaller 2e oddities logged alongside: the melee auto CRIT MULTIPLIER measured 2.318 (above the 2.0 physical base), and Sword Specialization crits 31.6% against a 24.92% melee sheet — both unexplained.',
     'White-swing crit output in core/sim/combat_engine.py', 'open', None, None, '2026-08-05'),
    ('hidden_formula_outlier_coefficients',
     'Some dbc_hidden_formula spell_scaling rows carry implausible values — e.g. 277595 (Fury of the Eagle) RAP 6.0 / SP 6.0, where the sub-spell text\'s "*6" looks like a damage-over-time total multiplier swallowed as a coefficient. The widened 1c extractor delegates build_dbc_index to the shared implementation, but the committed extract\'s cached rows date from the narrow one. Audit outliers; re-extract at next --with-dbc.',
     'Trust in the 84-spell dbc_hidden_formula coefficient set', 'open', None, '277595', '2026-08-05'),
    # --- resolved entries kept so the queue reads as history, not amnesia ---
    ('hammer_from_the_heavens_coefficients',
     'What are Hammer from the Heavens\' coefficients (hidden sub-spell 282987, 22.1% of damage)? THE largest stat-weight unknown since v5.',
     'Paladin stat weights', 'resolved', 'hammer_from_the_heavens_formula_resolved', '282987', '2026-08-02'),
    ('do_coefficients_scale_with_rank',
     'Do damage coefficients scale with rank?',
     'spell_scaling schema (rank keying)', 'resolved', 'coefficients_do_scale_with_rank', None, '2026-08-03'),
    ('entry_id_vs_spells_id',
     'Is scouted entry_id the same ID space as spells.id?',
     'Every "who runs ability X" query', 'resolved', 'ca_table_has_playable_pool_flag', None, '2026-08-03'),
    ('sourcesbystat_itemisation',
     'Does stats_summary.sourcesByStat itemise per-source stat contributions (talents/path included)?',
     'Path of Duality verification route', 'resolved', 'crawl_stats_summary_is_gear_only_not_the_character_sheet', None, '2026-08-03'),

    # ------------------------------------------------------------- session 2e
    ('holy_residual_two_mechanisms',
     'The Holy calibration residual is TWO clusters with different causes, not one multiplier (2e PoI Window A, same-session stats). CLUSTER 1, out-of-catalog spells with NO route to a coefficient: Righteous Smite 273123 at 2.27x and PBL\'s Consecration 270768 at 2.20x — Ascension keeps applied coefficients in tooltip text and these have no catalog tooltip, so their SP terms are MISSING, not zero. Back-solved gap sizes (~0.37 SP for Righteous Smite, ~0.16 SP for Consecration) are stated as gap sizes and DELIBERATELY NOT SEEDED — fitting a coefficient to the parse it must later check is what T8 forbids. Settle with live tooltips or a two-SP-level A/B. CLUSTER 2, coefficient-bearing spells: HftH 282987 at 1.45x and HoJ 282984 at 1.41x — after the x1.155 talent layer a real ~1.24x remains unexplained. The residual also GREW with buffs (HftH predicted B/A 1.311 vs observed 1.429), so something multiplicative scales with buff state on top of the constant gap. DO NOT collapse the clusters into one Holy amplifier.',
     'The D4 cross-school ranking gate (PHASE_2 §8.1b); Holy ability valuations', 'open', 'holystrike_residual_was_the_weapon_input', '273123,270768,282987,282984', '2026-08-05'),
    ('extract_scope_missing_log_observed_ids',
     'Five ids carry real damage in the owner\'s own logs and have NO record in spell_dbc_raw, so no extraction route reaches them — together ~38% of buffed damage: 200818 Consecrated Holy Weapon (25.1% of the buffed window — THE largest modelling gap), 20424 Seal of Command\'s damage spell (6.5%), 954923 Arcing Light (3.7%), 907790 Whirling Light off-hand, 18652 Siphon Health. The next --with-dbc run should widen the extract scope, cheapest robust rule: SEED THE SCOPE FROM SPELL IDS OBSERVED IN THE OWNER\'S COMBAT LOGS (small, concrete, covers what matters by construction), plus EffectTriggerSpell targets of catalog spells (reaches 20424), plus SpellItemEnchantment.dbc — Consecrated Weapon applies enchant 23387 and that DBC is not extracted at all; it is the only route to 200818.',
     'Absolute calibration completeness; Consecrated Holy Weapon\'s magnitude', 'resolved', 'db_ascension_gg_states_the_applied_coefficients', '200818,20424,954923,907790,18652', '2026-08-05'),
    ('consecrated_holy_weapon_is_enchant_delivered',
     'The 2026-08-06 --with-dbc run put all five previously-missing ids in the extract, but 200818 decodes to a flat of 1 - and db.ascension.gg independently states "Value: 1" for the same spell. Two sources derived by completely separate routes agreeing on a nominal 1 is not a magnitude: it is proof the damage IS NOT IN THIS SPELLS OWN RECORD. Consecrated Weapon applies enchant 23387 and SpellItemEnchantment.dbc is still not extracted, so that remains the only DBC route to it. CONSEQUENCE: the widened extract was expected to retire the live-tooltip ask for 200818 and did the OPPOSITE - it is still the single largest unmodelled damage source in the owners own build (25.1% of his buffed damage) and a live in-game tooltip is still the only way to get it. GENERAL LESSON worth more than the case: before assuming a wider extract will reach a value, check whether that value lives in that DBC at all - widening scope cannot recover something stored in a different table. '
     '3L UPDATE (2026-08-08, owner-gated --with-dbc run with SpellItemEnchantment.dbc in scope, 18,035 rows): the enchant route now EXISTS and half the question is CLOSED BY A NUMERIC FIELD. Enchants 23387-23395 are "Consecrated Weapon 1".."9" -> equip-spells 200819-200827 "Consecrated Holy Weapon Hidden", each carrying Ascension-CUSTOM auras [4 DUMMY, 345, 344] (stock 3.3.5 aura ids end ~316) with rank-rising BasePoints. ANCHOR, exact: rank 6 aura-345 decodes 85+1 = +86 - the 2e-measured "+86 RAW Holy SP per weapon", recovered independently, so aura 345 IS the per-weapon school-SP sheet grant, per rank, provenanced. CORRECTED 3m C3, edited here 3n pre-flight (AUDIT_3M F1 - this file was the sibling site AUDIT_3L F5 named and 3m did not reach): AURA 344 IS NOT THE PER-HIT DAMAGE PARAMETER. It is a flat ATTACK POWER grant, +73 per weapon at rank 6, and spell 200809\'s own tooltip template says so; the ladder R1 19 .. R6 73 .. R9 132 is an AP ladder. The per-hit damage term is EFFECT 0, with divisors 77/25 STATED by the client rather than underived. WHAT REMAINS OPEN IS THE DELIVERY HALF, AND IT IS REAL: effect 0 gives the parameter but the per-hit damage is enchant-delivered through 200818, whose own record decodes to a nominal 1 (see consecrated_holy_weapon_is_enchant_delivered), so what still needs testing is whether effect 0 with those divisors reproduces the owner 200818 per-hit distributions (2e + MC captures) at his known rank-6 enchant and weapon speeds - and separately, the +73 AP grant is seeded but NOT YET MODELLED in the sim (3m NOT-done item 6). Do not re-inherit the per-hit reading of aura 344. Delivery modelling for crawled characters (enchant_id per snapshot_gear row names each character rank) is the 3m trigger-delivery block, owner decision 2026-08-08.',
     'The owners own build modelling (25.1% of buffed damage); absolute calibration',
     'open', None, '200818,200819,200824', '2026-08-06'),
    ('str_to_ap_1_21_under_buffs',
     'Buffed states show ~1.21 Attack Power per point of Strength where the exact unbuffed formula gives 1.10 (AP = (Str-20+gearAP) x 1.10, verified to the point). Two independent buffed steps agree (totem: 68 Str -> 82 AP = 1.206; Kings: ~12 -> ~15 after subtracting imbue AP), and Agility is ruled out (elixir test: dAgi 15 -> dAP 0). Either a buff grants AP beyond its Strength (Strength of Earth Totem is the candidate) or a second x1.10 multiplier appears only under buffs. Settle with one export after adding the totem ALONE to the unbuffed state.',
     'The buff model\'s AP arithmetic; melee stat weights under raid buffs', 'open', 'attack_power_formula_str_minus_20_plus_gear_times_deadliness', None, '2026-08-05'),
    ('sp_no_talent_capture_contradiction_59',
     'The two no-talent spell-power captures contradict each other by EXACTLY 59 in both directions: naked/no-talents reads SP 118 at gear 0 (implying flat 118), geared/no-talents reads SP 288 at gear 229 (implying flat 59; 229+118=347 was expected). Too clean to be rounding; recorded as a conflict per §2.3, NOT fitted. The working talented-state model (SP = 2.0 x (gear + 59 + effects + 0.12 x Int)) fits every talented capture to ≤1.6, so whatever differs lives in the stripped states. Settle by asking: was the Path still Intelligence in BOTH captures, and did removing "all abilities" also remove an SP-granting self-aura (Brilliance Aura is self-cast in the Window A log)?',
     'The PoI spell-power model\'s flat term (118 vs 59, under-determined)', 'open', None, None, '2026-08-05'),
    ('seal_proc_mechanic_rate_vs_ppm',
     'Is Seal of Command\'s rider a flat per-event chance (~0.25 per melee event, measured twice) or a PPM mechanic? Both fit two windows at ONE weapon speed — they are only separated by a capture at a materially different weapon speed or haste level. Until then core/sim/swings.py serves the measured rate with a warning.',
     'Seal damage modelling in the swing layer', 'open', 'seal_of_command_procs_from_melee_events_not_autos_only', '20424', '2026-08-05'),
    ('sword_specialization_modelled_too_high',
     'Sword Specialization (16459) is the one ability the sim models TOO HIGH: 0.60x (modelled ~782, logged 469.2 non-crit). Its decoded effect is type 31 weapon damage plus a flat 120, but it is an EXTRA-ATTACK proc — a free swing — and 469 is what an unglanced white swing looks like (same-log swing average 305.4 INCLUDES 33% glancing; an extra attack may not glance). Hypothesis: the flat 120 does not apply, or belongs to a different rank. Also crits 31.6% vs the 24.92% melee sheet, unexplained. Recorded, not patched.',
     'Physical-side calibration; the extra-attack model', 'open', None, '16459', '2026-08-05'),
    ('melee_haste_displays_1_30x_ranged_spell',
     'Melee haste displays exactly 1.30x the ranged/spell value at identical rating (3.77% vs 2.90% at 29 rating) in every geared 2e export, with AND without talents, and 0.00% naked. A permanent x1.30 melee-haste display multiplier that talents do not supply. Unexplained; affects swing-timer arithmetic if real rather than cosmetic. Settle by timing actual white swings against the displayed speed.',
     'Swing-timer inputs in core/sim/swings.py', 'open', None, None, '2026-08-05'),

    # -------------------------------------------------- 3b pre-flight (2026-08-06)
    ('crawled_gate_residual_after_buff_layer',
     'What dominates the crawled calibration residual now that the measured buff layer is DERIVED and applied? The 3a ranked-cause #1 ("buffs are modelled for the owner only", expected order x2.35) is largely FALSIFIED as the dominant stat-side mechanism: deriving each candidate\'s buff set from group boards and applying the full measured arithmetic (Kings x1.10 last, +31 Int/+27 raw SP, +62 Str/Agi, +14 AP, imbue per weapon) moves crawled sim DPS by only +0% to +11%, against misses of -35% to -99% (still 0 of 41 within tolerance). The owner\'s own x2.35 unbuffed->buffed gap must therefore route mostly through mechanisms the sim lacks per ability, not through stat arithmetic: his buffed parse is 25.1% Consecrated Holy Weapon damage (200818, no magnitude) and buffed SP feeds coefficients that out-of-catalog spells cannot carry (2e\'s missing-coefficient mechanism, which generalises to EVERY class\'s kit in the crawl). Candidate ranking for the residual: per-kit magnitude/coefficient coverage; unmodelled proc/trigger/imbue damage; APL realism for unknown kits; CP finishers scored at 0 CP; hybrid mitigation unsplit.',
     'Phase 3 exit (the >=3-characters calibration gate)', 'resolved',
     'crawled_gate_miss_was_missing_weapon_damage', None, '2026-08-06'),

    # -------------------------------------------------------------- session 3b
    ('crawled_gate_passes_by_compensating_error',
     'The crawled gate now reads 4 of 41 within +/-20% (criterion >=3, PASS) — but only ONE of those four (Ari, -10.3%) also has >=50% of its real damage modelled. The other three land inside tolerance while the sim reproduces 5-13% of what they actually pressed (Chastie 5%, Zaczao 6%, Xoller 13%): the modelled slice happens to total about the right number. That is compensating error, and the +/-20% aggregate criterion is structurally blind to it. QUESTION: should the Phase 3 exit criterion carry a magnitude-coverage floor, and at what level? 🛑 The criterion was NOT changed after seeing the result — the qualified count is reported alongside it and neither replaces the other, because redefining a gate once its number is known is how a gate stops meaning anything. Owner decision needed.',
     'Whether Phase 3 exit is genuinely met; whether the sim earns the right to emit stat weights (PLAN_3B §6)',
     'resolved', 'crawled_gate_miss_was_missing_weapon_damage', None, '2026-08-06'),
    ('crawled_gate_exit_carries_a_coverage_rider',
     'RESOLUTION of crawled_gate_passes_by_compensating_error (2026-08-06). The +/-20% pass definition is UNCHANGED. What was added is a Phase 3 EXIT rider: Phase 3 exits only when >=3 characters are within +/-20% AND >=3 of those also have >=50% of their real damage modelled. 🛑 Stamped in predictions/CALIBRATION_TOLERANCE.md and wired into calibrate_crawled.py BEFORE the scraped-coefficient ingest was re-run through the gate, precisely so the rule predates the number it judges — it is a STRICTER bar than what passed at the time (4 pass / 1 qualified), so it cannot have been chosen to flatter a result. 50% is a floor on interpretability, not a fitted target: below half the kit modelled, the unmodelled remainder is large enough to absorb an arbitrary error in the modelled part, which is the compensating-error case itself. First run under the rider: 5 of 41 within tolerance, 2 qualified -> EXIT NOT MET.',
     'Phase 3 exit; whether the sim earns the right to emit stat weights (PLAN_3B §6)',
     'resolved', 'crawled_gate_passes_by_compensating_error', None, '2026-08-06'),
    ('unmodelled_damage_is_unreachable_ids_not_missing_numbers',
     'MEASURED 2026-08-06, immediately after the db.ascension.gg coefficient ingest, and it redirects the magnitude work. The ingest added 3,446 stated coefficients across 1,617 spells and moved the gate from 4 of 41 to 5 of 41 (qualified 1 -> 2) — but median magnitude coverage did NOT move at all, staying at 37%. Cause, measured rather than assumed over the 88 demand-ranked unmodelled abilities the gate names: 83 of 88 ALREADY HAVE A MAGNITUDE and 51 now have a coefficient (50 of them from this ingest). The numbers are not the bottleneck. ALL 88 are OUT OF CATALOG — not one is a card the sim could press — and 57 of 88 have no card AND no incoming trigger edge, so no route the sim walks reaches them at all. Worked case: the log reports Devour Mind damage under 287865, while the sim presses catalog card 285133 and its bounded walk reaches sibling 287860; 287860 and 287865 hold IDENTICAL decoded magnitudes and identical scraped coefficients (SP 0.08 / AP 0.055), but only 287860 has a trigger edge, so the gate scores 287865 as unmodelled. CONSEQUENCE: coverage is an ATTRIBUTION/REACHABILITY problem, not a data-acquisition one, and it was never going to be fixed by a coefficient source — the primer expectation that the ingest is "where the median 37% should move" was mis-specified. This generalises 2e\'s dbc_only finding (extracted-but-never-read because the resolver only walked catalog routes) from magnitudes to the whole routing layer. 🛑 Do NOT close this by matching ids on name or by numeric proximity (287860 vs 287865 is exactly the shape rule 5 forbids); the join has to be mechanical.',
     'Magnitude coverage; the Phase 3 exit rider; what the next magnitude session should actually work on',
     'open', None, '285133,287860,287865,20467,25902', '2026-08-06'),
    ('crawl_gear_coverage_is_not_repairable',
     'Gear-stat resolution coverage across the gate is a median 100% (30 of 41 characters resolve every stat-bearing slot), so gear under-resolution is ELIMINATED as the dominant cause of the crawled miss for most characters. The 592 unresolved item_ids are unresolved on EVERY snapshot — 0 of them resolve anywhere else in the corpus — because they are absent from the upstream item database (levelling greens and vanilla items outside BisBeard S10 scope). QUESTION: is enriching those from db.ascension.gg item pages (PHASE_3 T4 Path B) worth it, given the characters that need it are mostly the low-coverage minority? Currently reported, not repaired.',
     'Gate candidate quality for the 11 characters below 100% coverage', 'open', None, None, '2026-08-06'),
    ('sim_models_no_pets_10pct_of_damage',
     'The sim models NO pets, and pet abilities are 10% of the crawled gate cohorts real damage — Firebolt (Wild Imp) 413112, Lightning Bolt (Pet) 892102 and Bite 17261 all rank in the top 20 unmodelled. Scored as zero today, which does not merely understate pet-carrying builds, it BIASES THE CORPUS against them: such a character can never pass the calibration gate honestly, so the gate quietly selects for petless kits. OWNER DECISION 2026-08-06: model them. ability_performance carries is_pet so the damage is already separable, and pet abilities resolve like any other spell once the coefficient source lands. Open until implemented; the question is the APL/uptime model for a pet, not the magnitudes.',
     'Gate honesty for pet-carrying builds; corpus bias in the calibration cohort',
     'open', None, '413112,892102,17261', '2026-08-06'),
    ('sim_cannot_express_damage_conversion_mechanics',
     'Righteous Vengeance (61840) appears unmodelled for 9 of the 41 gate characters, and it is NOT a coefficient problem — we have held the mechanic as a confirmed fact since v5 of the build doc (30% of a critical strikes damage as an 8s Holy DoT, pools on refresh, cannot crit). db.ascension.gg confirms there is no stat coefficient to find: the page states a nominal "Value: 1" with no Scaling lines, because the magnitude is a CONVERSION of other damage rather than a function of a stat. The sim has no way to express "X% of another events damage, redelivered as a periodic". Likely a small family, not a one-off — Ignite (12654, 5 characters) and Deep Wounds (12721, 7 characters) are the same shape, and both are also top-20 unmodelled. NO DATA IS NEEDED to fix this; it is pure sim work and should not be waiting behind the scrape.',
     'Magnitude coverage for conversion-damage abilities; the crawled gate',
     'open', None, '61840,12654,12721', '2026-08-06'),
    ('sim_magnitude_explosion_absolute_zero',
     'Mutaforma (Healing path, Bloodlord Mandokir) sims at 89,340 DPS against a logged 2,402 (+3,619%) — the only positive delta in the crawled gate, driven by Absolute Zero (285148) whose periodic component is ATTRIBUTED from trigger target 285149 at confidence=inferred. One attributed magnitude producing ~30x a real parse is a resolution error (wrong rank, wrong per-level scaling, or a periodic tick misread as per-tick-per-target), not a strong build. Locate the bad row and decide whether the bounded trigger walk needs a sanity cap or the magnitude decode is wrong. || RESOLVED 2026-08-07 (3g G2), and the 3e guess was RIGHT about the family and wrong about the layer. It was NOT a magnitude error and NOT a trigger-walk error: the attributed magnitude is fine and the bounded walk behaved correctly. The defect was in occurrences_per_cast, which computed a periodic component tick count as round(dur / tick) where dur came from the CARD (285148, 12.0s) and tick from the COMPONENT (285149, 0.001s) - 12,000 ticks for one cast. A duration and a period from two different spells describe no single aura. Fixed by reading each reached component OWN duration (spell_dbc_raw.duration_index -> dbc_spellduration, the join core/spells/mechanics.py already performed for the card and had never performed for a component); 285149 states 0.001s duration and 0.001s tick, i.e. ONE application. Mutaforma moved +3,618.8% -> -88.3% on that change alone. THE SANITY CAP 3e ASKED ABOUT ALREADY EXISTED - the periodic-trigger-DELIVERY branch has enforced PULSE_COUNT_SANITY_LIMIT since 2b and it had simply never been applied to its sibling branch; it is applied now, as a second guard. SCOPE, and it is the part worth carrying: this was never a one-spell defect. Measured across the frozen cohort (1,055 distinct spell ids), 12 periodic events are built from two different spells timing and the two durations DISAGREE IN ELEVEN OF THEM. Absolute Zero is only where the disagreement is four orders of magnitude instead of one tick, which is why it was the one anybody noticed.',
     'Crawled-gate credibility; trigger-attribution trust', 'resolved',
     'sim_magnitude_explosion_absolute_zero', '285148', '2026-08-06'),

    # -------------------------------------------------------------- session 3e
    ('combo_point_generation_absent_from_extract',
     'MEASURED 2026-08-06 (3e B4). SPELL_EFFECT_ADD_COMBO_POINTS is effect type 40 and spell_effect_values holds ZERO rows of it, so nothing in our data says WHICH abilities generate combo points or how many. 3e fixed the rest of the combo-point economy — is_finisher now reads per_combo (not just cp_scaling, which is set only on tooltip-parsed coefficient terms and was None even there, so 0 of 4 real per-combo abilities on the cp_melee board were classified as finishers); finishers got their own APL tier above the fillers, because a gated entry sitting among the fillers never won a priority scan; and expected_hit/expected_cast now take combo_points read from the APLs own gate. What CANNOT be derived is the generation rate, so CP_PER_BUILDER_CAST = 1.0 is a named retail_hypothesis carrying a warning in every sim that relies on it, exactly like BASE_GCD. RESOLUTION ROUTE: a wider --with-dbc extract that exports effect type 40, or measurement from combat logs (a builder cast is followed by a CP change the client shows).',
     'Combo-point build accuracy in both sim tiers; any finisher cadence',
     'open', None, '11275,954886,277038,904965', '2026-08-06'),
    ('execute_gating_absent_from_extract',
     'MEASURED 2026-08-06 (3e B5). In 3.3.5 an execute window is TargetAuraState = AURA_STATE_HEALTHLESS_20_PERCENT, and spell_dbc_raw carries NO aura-state column at all (it exports attributes / attributes_ex and nothing of that family). So the sim cannot tell which abilities require a low-health target. 3e fixed the MECHANISM either side of that gap: target_health_pct now decays linearly 100->0 across the fight instead of being pinned at 100.0 forever, a target_health_pct_below condition works in medium_sim, and fast_sim — which has no clock — takes the same gate as a share of cast count (under linear decay an ability gated at "below X%" is available for exactly the last X/100 of the fight). CONSEQUENCE WHILE OPEN: an execute-gated ability with no hand-authored condition is modelled as ALWAYS AVAILABLE and is over-credited — Hammer of Wrath casts 9x at full target health on the cp_melee fixture. Both tiers now emit EXECUTE_GATING_UNAVAILABLE by name rather than leaving it silent. RESOLUTION ROUTE: export TargetAuraState in the next --with-dbc run.',
     'Over-crediting of execute abilities in every tier; apl_gen cannot emit a health gate',
     'open', None, '24239', '2026-08-06'),
    ('pet_damage_not_derivable',
     'MEASURED 2026-08-06 (3e B6), and this is the one 3e data gap NO owner-gated extract can close. Summons themselves ARE derivable: SPELL_EFFECT_SUMMON is effect type 28, spell_effect_values holds 395 rows across 389 spells, each carrying the summoned creature id in misc_value — core/sim/pets.py detects them and both tiers now name each pet with the measured size of the omission. But a pets DAMAGE is not: creature stats (attack power, damage range, attack speed, the pets own spells) live in the servers creature_template, NOT in any client DBC. There is no creature table in ascension.db and no --with-dbc widening would produce one, because the client does not ship it. The owner decision of 2026-08-06 was "model pets" at the mechanical minimum (summon -> pet actor scaled from owner stats); that scope is therefore NOT BUILDABLE from our sources, which is the finding. MEASURED SCALE: 5.0% unbuffed / 5.4% buffed / 1.5% dungeon on the owners Frost Mage capture (Lesser Water Elemental), ~10% across the gate cohort, and the corpus DPS INCLUDES pet damage so pet-carrying builds miss low against it. ⚠ CORRECTED 3j B4: this row previously read "corpus.py computes dps = (total_damage + pet_damage)/duration". That expression was fixed in 3i B3 (it counted pet damage TWICE — ENGINE_BUGS E15); the current one is dps = total_damage/duration. The FINDING is unchanged, because the endpoint merges pets into rows[] and total_damage sums those owner rows — pet damage sits in the denominator exactly once instead of twice. Mechanism corrected, conclusion re-derived and unaffected. RESOLUTION ROUTE: LOGS, not DBC — ability_performance already carries is_pet and a combat log names pet damage directly, so a pet damage profile can be MEASURED per pet. That is PHASE_3 T6 (session 3f). 🛑 Do not substitute a fabricated pet damage figure in the meantime: it would be fabrication inside the number the calibration gate reads.',
     'Gate honesty for pet-carrying builds; supersedes the implementation half of sim_models_no_pets_10pct_of_damage',
     'open', None, '31687,413112,892102,17261', '2026-08-06'),
    ('mixed_direct_and_periodic_ability_has_no_correct_cast_rate',
     'FOUND 2026-08-06 (3e B3, ENGINE_BUGS E7). An ability with BOTH a direct hit and a periodic rider — Fireball, Immolate, Living Bomb, and on the melee side Aether Rupture — has no correct single cast rate, because expected_cast returns ONE mean for the whole activation. Bound it by the DoTs duration and the direct component starves (a Fire mage casting Fireball once every 4 seconds); leave it unbounded and every cast re-scores the riders entire duration, over-counting the periodic component by roughly duration/gcd. NO FIELD RESOLVES IT: what a refresh does to a partially-elapsed DoT is a server behaviour nobody has measured on Ascension. Unbounded is what runs, because the direct component dominates on these spells, and the residual is NAMED per ability in warnings rather than buried. ⚠ LOAD-BEARING FOR THE GATE: Chastie passes at +9.1% partly on this over-count, at 4.6% coverage. THE REAL FIX is per-EVENT cast allocation — score the direct component at the cast rate and the periodic component at its own refresh rate — which is a change to the ability model, not to the APL. Discovered because a first pass treated "has a periodic component" as "is a DoT"; the fixture caught it (Fireball 10 casts in 68s) where reasoning did not.',
     'Damage accuracy for every hybrid direct+DoT ability; one current gate pass',
     'open', None, '133,25309,44523,904965', '2026-08-06'),
    ('sim_never_reads_is_channeled',
     'FOUND 2026-08-06 (3e C2, ENGINE_BUGS E8), verified rather than inherited. is_channeled is resolved into the DB (core/spells/mechanics.py:275, column at core/db/schema.py:340) and grep -rn is_channeled core/sim/ returns NOTHING — so the sim charges a channel ONE GCD while crediting EVERY tick, over-crediting it by roughly channel_duration/gcd. The owners Frost Mage capture settles exactly where this bites, per window: Blizzard casts 0 in Window A (unbuffed dummy), 0 in Window B (buffed dummy), and 4 in Window C (Scarlet Monastery) [CORRECTED 3i A5: this row shipped 305, a raw grep LINE COUNT wrong by ~76x and not even all Elrics - re-measured 3f F8 through combat_log_parser.py named fields as SPELL_CAST_SUCCESS 4, delivering 9.4 pct of the window; see ENGINE_BUGS.md E8]. So every A->B comparison in that capture is SAFE from it, and anything derived from Window C is NOT — which is a second reason the dungeon ContentProfile (3e C4, spilled to 3f) needs care beyond its segmentation problem. ⚠ Channels are also indistinguishable from instants in the client API: GetSpellInfo position 7 reads 0 for Blizzard exactly as it does for Ice Lance, and attributes_ex & 0x44 in the DBC is the only route — which is why the mechanics layer resolves it at all. The data is present; the sim simply never asks for it.',
     'Any build with a channel; the dungeon ContentProfile derivation',
     'open', None, '10187', '2026-08-06'),
    ('engine_fixes_did_not_move_the_holdout',
     'MEASURED 2026-08-06 at 3e close-out, reading the pre-registered holdout ONCE as designed. 3e closed five of six registered engine defects (E6, E4, E1, E2 fixed; E5 fixed for pure DoTs; E3 named) and the gate did not move at all: 5 of 36 within +/-20% before and after, 2 qualified before and after, slice accuracy 64.3% before and after. The holdout (460, 461, 462, 463, 7661) reads 0 of 5, having moved only +0.0 to +8.0 points and still missing by -45% to -98%. THREE OF THE FIVE CARRY 27-69% COVERAGE, so for them this is not a coverage story but an accuracy one — corroborating 3e A2s finding (the sim under-produces by ~37% on what it DOES model) on characters never tuned against. QUESTION: where is the residual? It is demonstrably NOT in the rotation mechanisms 3e repaired. Per A2s algebra, reaching +/-20% needs slice accuracy ~64% -> ~100% AND coverage ~37% -> ~80%; neither lever alone suffices and 3e moved neither. 🛑 Do not close this by fitting a constant — same rule as 2cs demoted 1.31 and 2es deliberately unseeded Holy residual.',
     'Phase 3 exit; what the next modelling session should actually target',
     'open', None, None, '2026-08-06'),

    # ------------------------------------------------------------- session 3f
    # 🛑 A DESIGN DECISION THAT CHANGES WHAT A TEST MEASURES BELONGS IN THE
    # SEEDS, not only in a plan document. /close-session: "Prose is not a
    # seed." Recorded as a QUESTION rather than a retraction because the plan
    # has not run yet — this row is the pre-registration of how it will be
    # scored, and it must exist BEFORE v2 runs or the rescope is unfalsifiable.
    # -------------------------------------------------- 3l close (2026-08-08)
    # D3, the THIRD carry, converted from a floating to-do into a registered
    # bounded unknown per SESSION_3L_PRIMER — the substance was measured in 3h
    # D2 and located in 3i; what it never had was a durable question row.
    ('owner_lt_pet_groups_scope_drift',
     'BOUNDED UNKNOWN, registered 3l after being carried three sessions: 1,208 (scope, character, spell) groups in ability_performance carry owner-row damage STRICTLY BELOW the pet restatement (ratios 5-1800x; e.g. Firebolt (Wild Imp) 4,067 pet casts vs 143 owner-merged), which contradicts the discriminated endpoint semantics (rows[] is owner-MERGED, so owner >= pet everywhere). Measured cohort impact: ZERO of them occur in any boss_single scope, so 0 of 41 gate members are touched; they concentrate in trash_bundle and aggregated boss_group scopes. Candidate mechanisms: partial capture windows, or scope drift between the payloads two blocks on aggregated scopes. NAMED UNBLOCK: re-fetch the affected trash_bundle/boss_group payloads (crawl_ascensionlogs.py --recrawl-report) and diff the two blocks per scope; unprovable from the committed corpus alone. Their excess (69.7M) is already excluded from canonical totals under the rows[]-canonical rule (ENGINE_BUGS E15 block).',
     'Nothing in the gate; canonical-total honesty for trash/boss_group scopes',
     'open', None, None, '2026-08-08'),
    # D4 — re-deferred BY NAME, with its standing engine entry pointed at.
    ('keyed_but_starved_gcd_allocation_share',
     'RE-DEFERRED BY NAME at 3l close (was 12.9% of cohort logged damage at the 3k close; 10.6% after 3l B3/B3b): sim keys exist and resolve but fast_sim allocates them zero casts — the GCD-allocation family ENGINE_BUGS E7 registers (one spam button absorbs the budget; mixed direct+periodic fillers starve). Not a coverage gap and not a coefficient gap: the fix is allocation modelling, adjacent to 3m trigger-delivery work (both are "the sim does not press the buttons the player pressed"). The share is printed by per_ability_accuracy.py as starved:zero-casts — regenerate, never quote this rows figure as current.',
     'The starved slice of the per-ability instrument; APL realism',
     'open', None, None, '2026-08-08'),
    ('plan_v2_blind_rederivation_scoring_rescoped',
     'OWNER DECISION 2026-08-06, taken before v2 ran and seeded in 3f (F8). PLAN_V2_BLIND_REDERIVATION as originally written IS NOT BLIND: Step 3 lists the DATABASES among v2s permitted inputs, and the databases ARE the answer key. The retractions table names v1s graded claims verbatim and by slug — sword_specialization_zero_output, duality_sp_amp_not_applying, improved_cleave_is_low_value_because_the_flat_is_small, art_of_war_dead_slot — which are exactly the claims cited as v1s known-wrong ones. A v2 session with DB access learns, before deriving anything, that Sword Specialization is not zero-output. THE RESCOPE: (1) the HEADLINE is scored on v1s still-OPEN claims only, which have no answer key anywhere in the tree and are scored against the 2026-08-06 Hammerdin proc-retest capture (tier-1 evidence, not a seeded verdict); (2) the RETRACTED claims are demoted to a labelled sanity check, run and reported AFTER the headline and reported AS LEAKED — "v2 avoided these; it could also have looked them up"; (3) Step 4s flagship outcome, "v2 reproduces a retracted v1 claim -> the single most valuable outcome the test can produce", is RETIRED — it was never available, because the leak had already suppressed it, and counting its absence as success is assumption-laundering: "v2 read the answer" scored as "v2 measured the answer". REJECTED, with reasons recorded so they are not re-litigated: DB blinding by exclusion list is an honour system unless a filtered view is actually built, and this project does not need another guard that is documented rather than implemented; a pre-v1 rebuild would be a real blind but hands v2 LESS knowledge than the current toolkit, so a v2 miss could not be separated from "v2 had less to work with". KEPT UNCHANGED: scoring v2s SILENCE where v1 was confident as an improvement — v1 asserted things it could not support, and refusing to answer is a gain, or the test rewards overconfidence.',
     'PLAN_V2 cannot run until this row and the amended plan are both committed',
     'open', None, None, '2026-08-06'),
]

# --------------------------------------------------------------------------
# retractions — (slug, claim, why_believed, what_falsified_it,
#                superseding_fact_topic, retracted_at)
# From PROGRESS.md's plan-changes table and the primer/build-doc retraction
# histories. §2.6: a fresh session must not be able to re-derive a dead claim.
# --------------------------------------------------------------------------
RETRACTIONS = [
    ('residual_is_not_in_the_mechanisms',
     "3e repaired six engine mechanisms and the calibration gate did not move (5 of 36 within +/-20%, 2 qualified, slice accuracy 64.3% at coverage >=20%), and concluded that the residual therefore does not live in the mechanisms - that it is per-ability magnitude coverage rather than modelling error.",
     'The reasoning was sound given the instrument. Six independent mechanism repairs producing a byte-identical gate is genuinely strong evidence that the mechanisms were not the binding constraint, and 3e said so carefully rather than overclaiming.',
     "Session 3g, G1. The gate that did not move was measured on a total containing E13, a percent-vs-fraction unit error making every white swing EXACTLY 100x over. Measured with the auto_share_of_sim_pct instrument added in 3g: the auto-attack supplied 89-96% of TOTAL SIM DAMAGE for fourteen of the 36 scored characters and 41-95% for ALL FIVE passers. Fixing that one unit moved the gate from 5 of 36 to 1 of 36, qualified 2 to 1, and slice accuracy 64.3% to 20.5% at the same n=23 and with coverage BYTE-IDENTICAL for all 36. So the six mechanism repairs were being measured against a number in which a 100x positive error was cancelling a large negative one - the compensating-error hazard the qualified rider was invented to catch, one level deeper, inside a qualified pass (Ari: -9.7% with the auto at 89.3% of its sim damage). WHAT IS RETRACTED IS THE INFERENCE, NOT THE MEASUREMENT: 3e's six repairs really did leave the gate unmoved, and that fact is unchanged. What cannot be concluded from it is anything about where the residual lives, because the metric it was read from was dominated by a defect none of the six touched. 12 of the 36 characters carry no auto damage at all and their deltas are unchanged to the decimal, which is what makes the attribution exact rather than inferred. The residual question is re-opened, and is now being asked of honest numbers for the first time: post-E13 the cohort is one-sidedly negative and slice accuracy says the sim under-produces on what it models by a factor of ~5, not ~1.5.",
     'sim_under_produces_by_five_fold_after_e13', '2026-08-07'),
    ('improved_cleave_amplifies_an_ap_scaling_bonus_term',
     'Lightbound Cleave\'s "bonus damage" term is 9 + AP x 1.0, so Improved Cleave 3/3 (+120%) takes it from 593 to 1,305 at AP 584 - worth about +11% total DPS, which moved Improved Cleave from LAST on the chase list to #2b (build_paladin-hammerdin.md v9, section 7 and section 10a).',
     'Session 1b-era reading of the raw DBC for 907300: Effect[0] = flat 9 with EffectBonusCoefficient = 1.0, read as "a full 1:1 AP-scaling term, unusually strong for a per-hit coefficient in this project\'s data so far". The oddity was noticed and interpreted as a finding rather than as a red flag.',
     'Session 2b, TWO independent errors compounding, each one already covered by an existing hard rule. FIRST, the wrong rank: 907300 is Rank 1 at SpellLevel 16, and a level-60 character casts Rank 5 (907304, SpellLevel 56) where the same effect slot reads 62, not 9. SECOND, and decisive, EffectBonusCoefficient = 1.0 is NOT an AP coefficient - it is stock EffectBonusMultiplier, whose neutral default is exactly 1.0 (7,647 of 9,211 non-zero values), which session 1x had ALREADY retracted as effect_bonus_coefficient_read_as_sp_ap. There is no AP term: Lightbound Cleave Rank 5 is 65% weapon damage plus a flat 62 Holystrike, and the tooltip states no $AP coefficient. Improved Cleave 3/3 therefore adds 120% of 62 = 74, taking the flat from 62 to 136 - not +712. That is roughly a 9.6x overestimate of the card\'s value. NOTE ON THE CORROBORATION: v9 reported the formula as independently corroborated against a scouted character\'s Voidbound Cleave damage, but that check applied the same formula to the same premises, so it never tested them. CAVEAT, stated honestly: "no AP scaling" here means NO COEFFICIENT IS STATED ANYWHERE - not that a coefficient is proven absent. Ascension keeps applied coefficients in tooltip text and this tooltip has none, and spell_scaling carries no rows for 907304. If a live tooltip at Rank 5 shows an $AP term, this retraction is itself wrong and should be revisited.',
     'improved_cleave_modifies_all_effects_not_just_the_flat', '2026-08-05'),
    ('improved_cleave_is_low_value_because_the_flat_is_small',
     'Because Lightbound Cleave\'s amplified "bonus damage" term is a flat 62 rather than 9 + AP, Improved Cleave 3/3 is worth only +74 per hit and belongs back at the BOTTOM of the chase list where v8 had it.',
     'Written in session 2b, an hour after correctly retracting v9\'s "9 + AP x 1.0" formula. Having shown the MECHANISM was wrong, I carried the demolition straight through to the CONCLUSION without re-deriving it - and read Improved Cleave\'s tooltip ("increases the bonus damage done by your Cleave ability") as authoritative about which effects it touches.',
     'The owner flagged it immediately as contradicting direct in-game experience of the card on other players, and the numeric field settles it against me: Improved Cleave is EffectAura 108 = SPELL_AURA_ADD_PCT_MODIFIER with EffectMiscValue 8 = SPELLMOD_ALL_EFFECTS. It multiplies EVERY effect of the spells in its class mask, so +120 percent applies to the 65 percent weapon-damage component as well as the flat: Lightbound Cleave goes from about 470 to about 1,033 per hit at Elric weapon damage, on an ability that is over half his pressed damage. TWO LESSONS. First, a retracted mechanism does not retract the conclusion it was used to support - the conclusion has to be re-derived, and v9 was right about the card for a reason it never stated. Second, this project\'s own rule about not reading magnitudes from tooltip prose extends to SCOPE: "the bonus damage done by your Cleave ability" names one term, and the modifier op says all of them.',
     'improved_cleave_modifies_all_effects_not_just_the_flat', '2026-08-05'),
    ('rank1_coefficient_probably_safe',
     'Reading an SP/AP coefficient off the catalog\'s Rank-1 entry is probably safe; only flats change with rank.',
     'Measured on ONE rank line (Holy Supernova): EffectBonusCoefficient identical at R1 and R6.',
     'Session 1x measured all 1,580 multi-rank lines: numeric coefficient varies on 169, tooltip literals on 34, in retail\'s ramp-then-plateau shape — and the catalog stores Rank 1, the deepest point of the ramp. Seven entries measurably wrong (Sun Down SP 0.4->1.3 = 3.25x).',
     'coefficients_do_scale_with_rank', '2026-08-04'),
    ('effect_bonus_coefficient_read_as_sp_ap',
     '311 blocked hidden-formula spells carry a non-zero EffectBonusCoefficient (SP/AP scaling) — the largest single data win available.',
     'A non-zero numeric field adjacent to spells with hidden formulas read naturally as the scaling coefficient.',
     '7,647 of 9,211 non-zero values are exactly 1.0; the recurring non-defaults are retail\'s cast-time formula; calibrated against 98 spells stating their own $SP*x/$AP*x it agrees 4 times. It is stock EffectBonusMultiplier. Building on it would have fabricated SP coefficients across 311 spells with tier-4 provenance attached.',
     'effect_bonus_coefficient_is_not_the_sp_ap_coefficient', '2026-08-04'),
    ('hfth_tooltip_double_applies_scaling',
     'Hammer from the Heavens\' tooltip double-applies level scaling.',
     'The displayed 194 minimum exceeded the computed base + one application.',
     'A double application would render 242/195 — ABOVE the observed minimum, impossible since the stat term cannot be negative. The real mechanism: the max term hand-rolls the wrong per-level rate (1 vs 2.4).',
     'hammer_from_the_heavens_tooltip_max_term_uses_wrong_per_level_rate', '2026-08-04'),
    ('hfth_level_cap_40',
     'Hammer from the Heavens\' level scaling caps at 40, giving a flat of 74-97.',
     'A 48-point gap between computed and displayed values fit a cap hypothesis.',
     'A --with-dbc re-extraction returned MaxLevel = 0 (uncapped) for 282987. The 48-point gap is fully explained by the stat term A = 72.',
     'hammer_from_the_heavens_formula_resolved', '2026-08-04'),
    ('pooled_crawl_rules_out_hfth_flat',
     'Pooled crawl damage (17,972 hits, 12 characters) ruled out the 122-145 flat for Hammer from the Heavens.',
     'Implied non-crit averages sat below the hypothesised flat.',
     'The crawl records NO character level, and the ability scales 2.4/level — a level-40 character deals 74-97 for the same spell. With Holy partial resistance on top, pooled figures discriminate nothing about a level-scaled magnitude.',
     'hammer_from_the_heavens_formula_resolved', '2026-08-04'),
    ('contiguous_rank_id_rule',
     'An unresolved spell ID is likely a rank sibling at +/-1-3 of a known card\'s ID.',
     '5/5 unmatched IDs resolved this way in one session — which happened to sample only contiguous lines.',
     '4,791 rank lines are non-contiguous vs 1,908 contiguous (Winds of Winter R1 274121 -> R2 274129). The rule that holds: highest rank with SpellLevel <= level.',
     'rank_resolution_is_level_gated_not_contiguous', '2026-08-04'),
    ('spell_274132_absent_from_client',
     'Spell 274132 is absent from the client.',
     'It was missing from spell_dbc_raw.',
     'The absence was an artifact of catalog+/-3 scoping, which excluded non-contiguous rank siblings. It is Winds of Winter Rank 5. Scoping widened +7,639 ids.',
     None, '2026-08-04'),
    ('hidden_formula_resolver_not_incremental',
     'The hidden-formula resolver runs against the full has_hidden_formula=1 list every invocation (not incremental).',
     'Reported in INDEX_GUIDE v3 from a same-count re-run.',
     'It was incremental AND destructive: it cleared the flag on resolution, so a second run found nothing to re-derive after deleting its own rows — spell_scaling\'s dbc_hidden_formula rows went 113 -> 0 across two consecutive runs. Fixed and verified idempotent.',
     None, '2026-08-04'),
    ('coefficients_scale_with_rank_from_name_match',
     'Coefficients scale with rank (early planning claim), with spell_scaling re-keying to follow.',
     'Compared 81193 to 270182 — two spells sharing the name "Holy Supernova".',
     'They are DIFFERENT ABILITIES (radius 10 vs 15, cooldown 50 vs 40, instant vs 2s cast). The conclusion later turned out true by proper measurement (session 1x), but this evidence was invalid — the retraction was of the reasoning, and it produced the fingerprint-before-relating hard rule.',
     'coefficients_do_scale_with_rank', '2026-08-04'),
    ('db_ascension_fifth_id_space',
     'db.ascension.gg uses a fifth spell-ID space.',
     '81193 did not resolve as expected during the same name-confusion incident.',
     '270182 resolves there normally; the db uses catalog-compatible IDs and 81193 is just another spell.',
     None, '2026-08-04'),
    ('wildcard_11_prefix_variant_space',
     'IDs with an 11-prefix (e.g. 1111294) are a Wildcard-mode variant ID space needing a crosswalk.',
     'Same-name spells appeared at 11-prefixed IDs.',
     'Four in-game tooltips show plain IDs (1459, 10157, 136, 270187). The 11-prefix space belongs to ANOTHER REALM, not Wildcard — later independently confirmed by the in_current_pool flag work.',
     'ca_table_has_playable_pool_flag', '2026-08-04'),
    ('int_to_melee_crit_38_confirmed',
     'Int -> melee crit at ~38 Int per 1% is CONFIRMED under Path of Duality.',
     'A single +11 Int gear swing produced +0.29% melee crit.',
     'That is ~4 crit rating at the known conversion — inside contamination range from a second stat on the test item. The live sheet showed no Intellect line in the melee crit table at all. Lesson: prefer crit-source breakdown tooltips over small differential measurements.',
     None, '2026-08-02'),
    ('sword_specialization_zero_output',
     'Sword Specialization produces ZERO output on this board.',
     'An early parse read that missed both clauses\' contributions.',
     'The King Gordok parse: the hit clause was carrying melee hit to cap on a polearm, and the extra-attack clause logged 6.8K / 3.1% / 10 procs. Both clauses work.',
     None, '2026-08-02'),
    ('art_of_war_dead_slot',
     'The Art of War is a dead slot for this kit.',
     'Cut on a tooltip clause that looked conditional.',
     'Its first line is an always-on damage increase to Judgement, Crusader Strike (-> Dawnreaver), Execution Sentence and Divine Storm. Cut on the wrong clause; back on the chase list.',
     None, '2026-08-02'),
    ('consecration_not_worth_slot',
     'Consecration is not worth a slot.',
     'Early low-gear parse share.',
     'Measured 2.2-7.6% of damage at 30-79% uptime across four parses. Earns its slot.',
     None, '2026-08-02'),
    ('enhanced_weapon_mastery_protect',
     'Enhanced Weapon Mastery is a protect-list card (top-tier all-damage multiplier).',
     'Export tooltip shows only the damage line.',
     'The live tooltip adds an exclusivity clause: does not stack with Answered Prayers / Unending Fury / Blessed Weapons, highest only — Answered Prayers 5/5 is already slotted, making EWM a dead slot on THIS board. (Codified as a server rule in the 2026-08-03 patch.)',
     'exclusivity_bucket_alldamage', '2026-08-02'),
    ('avenging_wrath_goak_substitutes',
     'Avenging Wrath and Guardian of Ancient Kings are substitutes — take the first.',
     'Both read as "big cooldown damage buff".',
     'They are independent cooldowns on separate systems (flat all-damage buff vs Holy-specific reset-and-buff). Even mutually buff-exclusive, sequential use on two cooldowns beats picking one. Both belong on the chase list.',
     None, '2026-08-02'),
    ('no_lucky_cards_cannot_roll',
     'Cards without the LUCKY family flag cannot appear in random rolls.',
     'The flag read like a roll-eligibility gate.',
     'Divine Steed (no-LUCKY) has been rolled multiple times. Working roll model is rarity x affinity only; the flag is likely a previous-season remnant.',
     'lucky_flag_falsified', '2026-08-02'),
    ('duality_sp_amp_not_applying',
     'Path of Duality\'s SP amp and cross-crit conversions are absent from the live sheet (v4/v5 downgrade of the earlier x1.75 claim).',
     'Bonus Damage 400 vs Bonus Healing 379 (5.5% gap) plus crit-source tables summing exactly with base-game conversions only.',
     'A controlled test on the SAME character — identical gear, EMPTY talent spec, Strength vs Duality back-to-back via the export addon — showed SP 229 -> 434, a clean 1.895x amp, plus real Int->melee-crit and Agi->spell-crit channels. The v4 reading was contaminated by Lunar Guidance and the talent-loaded board. (New anomaly found in the same test: AP at 0.548x under Duality, still open.)',
     'duality_sp_amp_confirmed_reverses_retraction', '2026-08-04'),
    ('aura_tick_vs_instant_pulse_crit_theory',
     'Ground effects that crit (Molten Earth) are repeating instant pulses, structurally distinct from aura-tick DoTs which cannot crit.',
     'It reconciled Molten Earth\'s 40.7% crit with the periodic-no-crit rule.',
     'Molten Earth\'s live tooltip is a textbook aura-tick DoT — structurally identical to Righteous Vengeance (0% crit) — and it still crits. No structural predictor; crit-capability is a per-spell server-side flag. Verify per ability from a parse.',
     'periodic_no_crit', '2026-08-02'),
    ('molten_earth_inherits_lava_lash_talents',
     'Molten Earth benefits from Lava Lash damage talents (Elemental Fusion, Lava Flows) since Lava Lash spawns it.',
     'Trigger proximity read as modifier inheritance.',
     'Live tooltip: "uses Fire Nova modifiers". Retracted the same session it was recommended. Trigger source != modifier source (class-tag rule proof case #2).',
     None, '2026-08-02'),
    ('sourcesbystat_settles_duality',
     'stats_summary.sourcesByStat can settle the Path of Duality question with zero in-game work.',
     'The field name suggested per-source itemisation including path grants.',
     'It itemises ITEM sources only (gear/enchant/set) — the whole stats_summary block is gear-only (_gearOnly key; a level-60 character shows Strength 13). No path or talent contribution exists in the data.',
     'crawl_stats_summary_is_gear_only_not_the_character_sheet', '2026-08-04'),
    ('fifteen_rank_coefficient_differences',
     '15 catalog entries carry rank-different coefficients (near-published figure).',
     'Eight entries had a coefficient at one rank and none at the other, counted as differences.',
     'All eight are artifacts: a compound form the regex could not read (Bone Arrow), a formula moved into a sub-spell (Deep Freeze), and a rank line polluted by a different same-name ability (Blood Drinker). The honest figure is 7.',
     'coefficients_do_scale_with_rank', '2026-08-04'),
    ('duality_sp_amp_1895_confirmed',
     'Path of Duality applies a 1.895x Spell Power amplifier, measured in a controlled empty-spec Path-of-Strength-vs-Duality test (SP 229 -> 434) — which itself reversed the earlier v4 "no amp" retraction.',
     'It was a clean-looking controlled test on one character with identical gear and an empty spec, exactly the design the primer recommends.',
     'The toggle was not clean, and could not have been. A relog-separated three-path capture on 2026-08-05 measured Duality at SP 271 vs Path of Strength 250 on identical gear — a flat +19 and NO amplifier — while Path of INTELLIGENCE measured 638, i.e. a real x2.0 doubling that belongs to PoI\'s tooltip, not Duality\'s. A Path-of-Strength capture taken without relogging read SP 500 = 1.995 x (items + Lunar Guidance), proving PoI\'s doubling persists across a switch. An independent player separately reports Duality\'s SP grant as a bugged "difference of 19 Spellpower". So the 1.895x reading could have been a stale PoI doubling, an ON phase of Duality\'s cycling bug, or a working-then-broken Duality — and nothing distinguishes them after the fact. v4\'s original "no amp on the live sheet" observation was right.',
     'duality_sp_amp_1895_retracted_as_a_duality_property', '2026-08-05'),
    ('duality_attack_power_anomaly_is_a_rate',
     'Path of Duality converts Strength to Attack Power at 0.548x rather than the tooltip\'s 100%, an undocumented reduced conversion rate.',
     'Two separate measurements agreed closely (0.548 on 2026-08-04, 0.567 on 2026-08-05), which looked like a stable rate rather than noise.',
     'Both were OFF-phase readings of a cycling bug. Duality\'s AP bonus switches on and off roughly every 10-15 seconds indefinitely — another player watched it oscillate 832 <-> 1128 (delta = their Strength) while standing still. Elric\'s two states are 174 (bonus off: 160 x 1.10 = 176) and 307 (bonus on: (160+121) x 1.10 = 309). When it applies, the tooltip\'s 100% is exactly right. Two agreeing measurements of an oscillating quantity are two samples of the same phase, not a confirmed rate.',
     'path_of_duality_is_broken_ignore_its_parses', '2026-08-05'),
    ('judgement_and_holy_shock_feed_hammerdin',
     'Judgement and Holy Shock feed the Hammerdin proc engine, so pressing them on cooldown compresses Hour of Judgement\'s cooldown — the basis of build_paladin-hammerdin §11\'s central rotation priority.',
     'Both are native Paladin abilities and Hammerdin\'s tooltip reads "damaging Paladin abilities", so they were the obvious feeders; §2\'s class-tag table listed them as "Yes — underused".',
     'Measured 2026-08-05 over a dedicated 10-minute dummy test: Holy Shock 1 proc in 78 casts, Judgement 0 in 51, against ~26 expected at the stated 20% (p < 1e-9) — while Dawnreaver procced 15-17 times in 119 casts and Hammer of Wrath at ~16%. Submitted as bug tracker 200295. Dawnreaver is the real engine driver. Note the abilities that fail are exactly those whose damage is delivered by a triggered sub-spell.',
     'hammerdin_does_not_proc_from_holy_shock_or_judgement', '2026-08-05'),
    ('crit_and_hit_rating_are_unified_stats',
     'Hit Rating and Crit Rating are UNIFIED on this server — the sheet shows melee and spell values that move together, so you cannot buy the spell half without the melee half (build_paladin-hammerdin §10\'s stat-weight framing).',
     'Every sheet reading available at the time showed melee and spell crit rating equal (e.g. 57/57 hit), which is what gear-only itemisation produces.',
     'They are unified in GEAR, not in the engine. The 2026-08-05 path trio shows melee crit rating 238 vs spell crit rating 187 on the same gear under Path of Duality, against 179/179 under Strength and Intelligence — Duality\'s Int->melee-crit and Agi->spell-crit conversions grant RATING (~3.4 stat per rating point) and split them. Any effect that grants one table\'s rating specifically breaks the unification, so the weights must be per-table.',
     'path_grants_measured_at_level_60_trio', '2026-08-05'),
    ('titanic_mutilate_115_pct',
     'Titanic Mutilate deals 115% weapon damage (from the DBC description string).',
     'The description text stated it plainly.',
     'The numeric field says 70% — the text was stale. THE proof case for the never-read-a-magnitude-from-a-description hard rule.',
     None, '2026-08-04'),

    # ------------------------------------------------------------- session 2e
    ('seal_of_command_riders_fire_on_autos_only',
     'Seal of Command riders fire on AUTOS ONLY, never on the queued Cleave — all 7 procs in the 2d isolation window landed at exactly 0.00 s from a white swing (session 2d, primer v27, the Cleave Kit costing).',
     'Generalised from the Lightbound-Cleave-only isolation window — a window whose ONLY melee ability was the one ability measured to feed nothing. The sample proved "LC does not proc the seal" and was read as "only autos proc the seal".',
     'The 2e full-rotation windows: 84 seal procs / 367 melee events unbuffed and 106 / 397 buffed, with only ~30% of procs within 50 ms of a white swing and ~51-64% within 50 ms of a MELEE ABILITY. The seal procs from both autos and abilities at ~0.25 per event. WHAT SURVIVES: Lightbound Cleave specifically still does not proc it, so the Cleave Kit\'s "converted swings drop auto-keyed riders" cost stands for LC. Method lesson: an isolation window isolates its subject — it cannot ground a claim about everything OUTSIDE the isolation.',
     'seal_of_command_procs_from_melee_events_not_autos_only', '2026-08-05'),

    # ------------------------------------------------------------- session 3a
    ('strict_lag0_join_skews_toward_levellers',
     'The strict lag-0 build-to-parse join yields only ONE level-60 crawled character, because exact-join captures structurally skew toward levelling players — so the calibration gate must loosen its staleness threshold (to 336h) to get a usable n at all.',
     'Measured against a MID-BACKFILL corpus, where the strict filter really did return one level-60 character. A plausible mechanism was available (armory captures fire on levelling milestones), so the starvation was written up as a structural property of the data rather than as a sample-size artifact.',
     'The uncapped backfill completed during the same session and the SAME strict filter returned 41 level-60 characters. It was small-sample, not structure. Generalised (now in calibrate_crawled.py\'s own docstring): a filter that starves on a partial corpus is not evidence that the filter is too strict — re-run on more data before loosening a constraint. The gate now runs at its strictest setting (--max-lag-hours 0) with no staleness caveat, so the correction strengthened the result. Retracted the same session it was made (3a, 2026-08-06); recorded here because the claim had already justified a methodological decision (the 336h loosening), which is exactly the kind of decision a fresh session could re-derive from the prose alone.',
     None, '2026-08-06'),

    # ------------------------------------------------------------- session 3e
    # 🛑 Seeded in 3f (F8), not 3e. `3e` published this reversal in THREE prose
    # documents and added ZERO retraction rows — `git diff` over the session
    # adds 6 QUESTIONS and 0 retractions. /close-session's own rule: "Prose is
    # not a seed." It is load-bearing beyond bookkeeping: PLAN_3G designates
    # RETRACTIONS as the ready-made regression set for 3g, so a retraction that
    # exists only in prose is a regression test that will never be written.
    ('cohort_slice_accuracy_160pct_means_the_sim_overproduces',
     'The cohort median slice accuracy is 160%, so the sim OVER-produces the damage slice it models by about 60% — and coverage work must therefore be throttled, because raising coverage on an already-over-producing slice would overshoot.',
     'Computed in 3d as a single median over the whole cohort and reported without a coverage floor. The number is arithmetically correct for the population it was taken over, and nothing in the output signalled that the population was inadmissible - the manifest shipped the bare figure with no n and no caveat beside it.',
     'Session 3e A2. slice_accuracy = (100 + delta) / coverage has COVERAGE IN ITS DENOMINATOR, so it explodes as coverage -> 0 and must never be aggregated across a cohort spanning 0.2% to 82% coverage. Mutaforma reports 1,859,400% at 0.2% coverage, in the committed 3d manifest. Restricted to coverage >= 20% the median is 64.3%, and it is STABLE there - 63.4% at >=30% and again at >=50%. THE SIGN IS THE OPPOSITE OF WHAT WAS PUBLISHED: the sim UNDER-produces on what it models, by about a third. CONSEQUENCE, and it inverts the instruction the claim was used to justify: at ~64% slice accuracy, coverage work ALONE can never reach +/-20%, because delta = 0 requires slice x coverage = 1.0 and at 0.64 that demands coverage above 100%. Both levers must roughly double. The old reading said coverage work would overshoot and should be throttled. GENERAL LESSON: a ratio whose denominator is itself a measured fraction has no meaningful cohort-wide average - report it per band above a stated floor, with n, or not at all.',
     None, '2026-08-06'),
]

# --------------------------------------------------------------------------
# Idempotency: this script OWNS open_questions and retractions.
# --------------------------------------------------------------------------
cur.execute('DELETE FROM open_questions')
cur.execute('DELETE FROM retractions')

cur.executemany('''INSERT INTO open_questions
    (slug, question, blocks, status, resolved_by_fact_topic, affected_spell_ids, opened_at)
    VALUES (?,?,?,?,?,?,?)''', QUESTIONS)
cur.executemany('''INSERT INTO retractions
    (slug, claim, why_believed, what_falsified_it, superseding_fact_topic, retracted_at)
    VALUES (?,?,?,?,?,?)''', RETRACTIONS)

link_counts = link_facts_to_spells(conn)
conn.commit()

n_open = cur.execute("SELECT COUNT(*) FROM open_questions WHERE status='open'").fetchone()[0]
print(f"open_questions: {len(QUESTIONS)} rows ({n_open} open) | retractions: {len(RETRACTIONS)} rows")
print(f"fact_spell_links: {link_counts['total']} rows "
      f"(id_regex {link_counts['id_regex']}, id_plus_name {link_counts['id_plus_name']}, "
      f"name_exact/needs_review {link_counts['name_exact']})")

# The check that justifies all of this: "you already answered this."
hits = find_answered_questions(conn)
if hits:
    print(f"\n⚠ answered-question candidates ({len(hits)}) — open questions overlapping a confirmed fact:")
    for h in hits[:10]:
        print(f"  {h['question_slug']} <-> {h['fact_topic']} (score {h['score']})")
else:
    print("answered-question sweep: no overlap candidates")
conn.close()
