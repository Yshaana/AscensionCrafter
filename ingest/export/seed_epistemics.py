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
     'Two residuals after the Duality amp was confirmed real (1.895x, controlled empty-spec test): (1) is Elric\'s CURRENT board actually on Path of Duality, and (2) the new anomaly — Attack Power dropped to 0.548x the Path of Strength value under Duality, contradicting "AP = highest of Str or Agi". Bug or undocumented conversion rate?',
     'SP weight (1.00 vs ~1.77) and AP posture in build_paladin-hammerdin §10', 'open', 'duality_sp_amp_confirmed_reverses_retraction', None, '2026-08-04'),
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
     'Re-verify Lightbound Cleave\'s proc behavior post-2026-08-03 patch ("fixed... proc effects triggered by abilities not on the GCD, including Cleave... restores intended proc behaviour"). The confirmed "0 Hammerdin procs" verdict predates this fix; check what LC does and does not feed now (Hammerdin, JotTH, PBL).',
     'LC\'s engine interactions; §2 class-tag table currency', 'open', None, '907300', '2026-08-03'),
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
    ('rank_siblings_inherit_no_hidden_refs',
     'Session 2b taught the numeric extractor to decode rank siblings (the level-60 id a catalog entry redirects to), closing a hole where 686 cards resolved to ZERO damage because the resolver correctly redirected to an id that had no spell_effect_values rows. 676 siblings now decode. The RESIDUAL gap: a sibling inherits no hidden_refs, because that column is parsed from the EXPORT tooltip and a sibling is by definition absent from the export. So a sibling whose own record is a DUMMY effect loses its sub-spell chain entirely. Holy Shock is the live example - the catalog Rank 1 (20473) resolves its damage through hidden refs 25912 (191-216 damage) and 25914 (301-327 heal), but the Rank 4 a level-60 character casts (20930) has Effect = [3,0,0], a bare DUMMY with all base points zero, and no EffectTriggerSpell for the bounded walk to follow. Holy Shock therefore sims as 0 damage - which is honest ("0 because nothing is KNOWN") but wrong about the game. Fix direction: parse the SIBLING\'s own client description text for $<id> references the way build_index parses export tooltips, rather than reusing the catalog entry\'s refs, since rank siblings can point at different sub-spells. Scope this before implementing: count how many of the 676 siblings have a dummy-only or empty own record.',
     'Damage of any ability whose level-60 rank resolves through sub-spells; Holy Shock is in the owner\'s rotation', 'open', None, '20473,20930', '2026-08-05'),
    ('periodic_trigger_delivery_pulse_count',
     'Session 2b established that trigger-reached damage can be delivered by a SPELL_AURA_PERIODIC_TRIGGER_SPELL slot, firing once per period for the aura\'s duration (Hour of Judgement: 500 ms over 10 s = 20 Hammer from the Heavens pulses per cast, alongside 5 ticks of its own 81). The RATIO is validated against real parses with no fitting - pooled 16,491 HftH hits / 4,332 HoJ hits = 3.81 against a predicted 4.00. What is NOT settled is the ABSOLUTE pulse count, because the ratio is invariant to duration: a 5 s duration would give 10 and 2.5 pulses and the identical 4.00 ratio. The absolute count rides entirely on dbc_spellduration index 1 = 10,000 ms, which is a tier-4 client read that no parse has yet confirmed. This matters because the pulse count multiplies the component\'s whole per-cast contribution - it is the single largest lever on the modelled damage of the owner\'s top ability. Settle by counting Hammer from the Heavens hits within one Hour of Judgement window in a SINGLE-TARGET parse (tools/log_parser/parse_log.py), where hits per cast equals the pulse count directly with no target-count confound. 34 cards use periodic-trigger delivery, so this generalises. Related guard: periods as low as 0.01 s appear in the data, which over a 10 s duration would imply 1,000 pulses; the ability model refuses any count above 100 rather than applying or clamping it, and those spells are unmodelled until someone checks what their period field means.',
     'Per-cast damage of all 34 cards with periodic-trigger delivery, Hour of Judgement first', 'open', None, '282984,282986,282987', '2026-08-05'),
    ('melee_crit_suppression_vs_higher_level',
     'Does Ascension apply melee crit suppression vs higher-level targets, and at what rate? The owner\'s own parse hints it exists (sheet melee crit 21.76% vs autos parsed at 16.2% — but n=37 swings, far too small per the sample-size rule). The sim\'s combat engine WARNS instead of modelling it (no fabricated retail constant). Settle with a large white-swing parse vs known-level targets.',
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
]

# --------------------------------------------------------------------------
# retractions — (slug, claim, why_believed, what_falsified_it,
#                superseding_fact_topic, retracted_at)
# From PROGRESS.md's plan-changes table and the primer/build-doc retraction
# histories. §2.6: a fresh session must not be able to re-derive a dead claim.
# --------------------------------------------------------------------------
RETRACTIONS = [
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
    ('titanic_mutilate_115_pct',
     'Titanic Mutilate deals 115% weapon damage (from the DBC description string).',
     'The description text stated it plainly.',
     'The numeric field says 70% — the text was stale. THE proof case for the never-read-a-magnitude-from-a-description hard rule.',
     None, '2026-08-04'),
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
