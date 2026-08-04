/**
 * scout_ascensionlogs.js
 * -----------------------
 * Run this in the browser console (or have Claude execute it via
 * claude-in-chrome:javascript_tool) while on ANY page under
 * https://darkmoon.ascensionlogs.gg/ — it calls same-origin API routes,
 * so no auth/CORS issues.
 *
 * Usage in DevTools console:
 *   const data = await scoutCharacter('David');
 *   downloadJSON(data, 'David');   // triggers a file download
 *
 * Usage via Claude's javascript_tool: call scoutCharacter(name) and
 * JSON.stringify() the result directly — no download needed, Claude
 * reads the return value straight out of the tool result.
 *
 * What it collects:
 *   - character identity (id, class/spec label, race, guild)
 *   - full resolved gear (item id/name/quality/enchant/gems/stats/drop source)
 *   - full resolved build: every ability + talent card, entry_id, rank,
 *     max_ranks, and PER-RANK tooltip text (richer than a static export —
 *     multi-rank cards show the tooltip at every rank, not just current)
 *   - live character stat sheet (primary/offensive/defensive/resist)
 *   - path (primary_stat) history split
 *   - ranking summary across every phase/zone the character has logged
 *   - capture history (report_id per past capture — for later fight-level
 *     digging once the per-ability damage-breakdown endpoint is found)
 *
 * Known gaps (v1):
 *   - Fight-level per-ability damage tables are NOT pulled yet — found
 *     GET /api/reports/{id} (metadata only), but not yet the sub-route for
 *     the actual damage-done table. Next step: click into a report in the
 *     UI and capture the network call.
 *   - entry_id (this site's card-catalog id) has NOT been confirmed to
 *     equal spells.id in our own ascension_index.db. Verify before joining
 *     scouted_build_entries.entry_id against your own spells table.
 */

async function fetchJSON(url) {
  const res = await fetch(url);
  if (!res.ok) return { __error: true, status: res.status, url };
  return res.json();
}

async function scoutCharacter(name) {
  const result = {
    scouted_at: new Date().toISOString(),
    name,
  };

  // 1. Resolve name -> character id + latest capture pointer
  const byName = await fetchJSON(`/api/armory/by-name/${encodeURIComponent(name)}`);
  if (!byName.success || !byName.has_armory) {
    result.error = 'No armory data for this character (not inspected/logged, or name mismatch).';
    return result;
  }
  const charId = byName.character.id;
  result.character = byName.character;

  // 2. Full resolved capture: gear + build + stats
  const capture = await fetchJSON(`/api/armory/character/${charId}`);
  const ci = capture.ci_resolved || {};
  result.captured_at = capture.capture?.captured_at;
  result.captured_for_boss = capture.capture?.captured_for_boss;

  // -- gear, flattened and trimmed to what matters for theorycrafting
  result.gear = Object.entries(ci.gear || {}).map(([slot, item]) => ({
    slot: item.slot ?? Number(slot),
    item_id: item.item_id,
    name: item.resolved_item?.name,
    quality: item.resolved_item?.quality,
    icon: item.resolved_item?.icon,
    enchant_id: item.enchant || null,
    enchant_name: item.resolved_enchant?.name || null,
    gems: item.gems,
    stats: item.resolved_bisbeard?.stats || null,
    damage: item.resolved_bisbeard?.damage || null,
    source: item.resolved_bisbeard?.source || null,
    source_category: item.resolved_bisbeard?.source_category || null,
    tier: item.resolved_item?.mythic_tier || null,
  }));

  // -- mystic enchants (separate custom-enchant system, kept raw)
  result.mystic_enchants = ci.mystic_enchants || null;

  // -- full build: abilities + talents, WITH per-rank tooltip text
  const trees = ci.specialization?.talents?.trees || {};
  result.build = {};
  for (const [treeSlug, tree] of Object.entries(trees)) {
    result.build[treeSlug] = (tree.talents || []).map(t => ({
      entry_id: t.entry_id,
      name: t.name,
      icon: t.icon,
      rank: t.rank,
      max_ranks: t.max_ranks,
      per_rank_text: t.per_rank_text, // array, index 0 = rank 1 tooltip, etc.
    }));
  }

  // -- live stat sheet + path
  result.primary_stat = ci.primary_stat || null;
  result.player = ci.player || null;
  result.guild = ci.guild || null;

  // 3. Path/primary-stat history (own endpoint, distinct from capture snapshot)
  result.primary_stat_history = await fetchJSON(
    `/api/characters/${encodeURIComponent(name)}/primary-stat`
  );

  // 4. Ranking summary — walk every phase, then every zone in that phase
  const phasesResp = await fetchJSON('/api/phases');
  const phases = phasesResp.phases || phasesResp || [];
  result.rankings = [];
  for (const phase of phases) {
    const phaseNum = phase.phase_number ?? phase.number ?? phase.id;
    if (phaseNum === undefined) continue;
    const zoneSummaries = await fetchJSON(
      `/api/characters/${encodeURIComponent(name)}/zone-summaries?phase=${phaseNum}&difficulty=ascended&bracket=all&metric=avg_dps`
    );
    for (const tile of zoneSummaries.tiles || []) {
      // Skip zones with nothing logged — cuts a LOT of empty-zone noise
      // (every phase lists every zone, most with bosses_killed: 0).
      if (!tile.bosses_killed) continue;
      const bossRows = await fetchJSON(
        `/api/characters/${encodeURIComponent(name)}/boss-rows?phase=${phaseNum}&difficulty=ascended&bracket=all&metric=avg_dps&location=${encodeURIComponent(tile.location)}`
      );
      result.rankings.push({
        phase: phaseNum,
        zone: tile.location,
        zone_summary: tile,
        // Only keep bosses actually killed — drops the zero-kill filler rows
        boss_rows: (bossRows.rows || []).filter(r => r.kills > 0),
      });
    }
  }

  // 5. Capture history (for later fight-level digging — report_id per kill)
  const captures = await fetchJSON(`/api/armory/character/${charId}/captures?limit=100`);
  result.capture_history = (captures.captures || []).map(c => ({
    capture_id: c.capture_id,
    captured_at: c.captured_at,
    boss_name: c.encounter?.boss_name,
    report_id: c.encounter?.report_id,
    location: c.encounter?.location,
    success: c.encounter?.success,
  }));

  return result;
}

function downloadJSON(obj, filenameBase) {
  const blob = new Blob([JSON.stringify(obj, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `scout_${filenameBase}_${Date.now()}.json`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

/**
 * findTopCharacters(zone, phase, limit)
 * --------------------------------------
 * Auto-discovers outliers instead of hunting character names by hand.
 * Hits the site's own leaderboard endpoint (found via the Rankings ->
 * Damage Rankings page network trace) — ranked by total All-Star points
 * across all bosses in the zone, role='dps'.
 *
 * Example:
 *   const top = await findTopCharacters("Zul'Gurub", 1, 10);
 *   const builds = await scoutMany(top.map(c => c.name));
 */
async function findTopCharacters(zone, phase, limit = 10) {
  const url = `/api/encounters/rankings/overall?location=${encodeURIComponent(zone)}&difficulty=ascended&phase=${phase}&metric=avg_dps&page=1&limit=${limit}&role=dps&cohort=global`;
  const r = await fetchJSON(url);
  const rankings = r.rankings || {};
  const zoneData = rankings[zone] || {};
  return zoneData.ascended || zoneData.normal || Object.values(zoneData)[0] || [];
}

// Batch helper — scout a whole list of names in one go (sequential, polite)
async function scoutMany(names) {
  const out = {};
  for (const n of names) {
    out[n] = await scoutCharacter(n);
  }
  return out;
}

// Expose on window so DevTools console access works without re-pasting
if (typeof window !== 'undefined') {
  window.scoutCharacter = scoutCharacter;
  window.scoutMany = scoutMany;
  window.findTopCharacters = findTopCharacters;
  window.downloadJSON = downloadJSON;
}
