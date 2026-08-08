"""`3o` Block B — RUN the capture addon against a stubbed WoW API and assert on
what it emits.

🚨 **WHY THIS EXISTS: THE ADDON IS THE ONE ARTIFACT IN THIS REPO THAT NOTHING
COULD TEST.** Every previous version was verified by the owner installing it,
playing, and pasting the result — so a Lua typo cost a dungeon, and a *silent*
emitter change cost a capture that looked fine until a parser refused it days
later. `2026-08-06c` shipped two real bugs found that way, one of which
("action bars resolved to Backstab and Terocone Motherlode") produced output
that read like data.

The client runs **Lua 5.1**, and `lupa` ships a real 5.1 runtime, so the addon
can be loaded and DRIVEN here: slash commands dispatched, combat events fired,
the session blob captured and handed to the same `parse_stat_block` the repo
uses on the owner's real captures.

🛑 **This is NOT part of `check_refusals.py`, deliberately.** It needs `lupa`,
and the owner's routine harness must not acquire a dependency he has to install
to get a green run. The parser-tolerance arm that *does* gate every run lives in
`check_refusals.py` and needs nothing but the repo. Run this one when the addon
changes:

    py -m pip install lupa
    py tools/audit/check_addon_lua.py

⚠ **What this CANNOT check** (stated, not implied): whether Ascension's client
actually exposes `LoggingCombat`, `UnitGUID` or any other API under the names
used here, and whether `PLAYER_REGEN_DISABLED` fires when this server thinks
combat begins. Those are live-client facts and only the owner's smoke test
settles them. This harness proves the addon RUNS and that what it emits is
shaped the way the repo parses — not that the client agrees.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import config                                              # noqa: E402
from core.builds.stat_block import parse_stat_block        # noqa: E402

config.ensure_utf8_stdout()

ADDON = (config.REPO / "addons" / "AscensionCrafterExport"
         / "AscensionCrafterExport.lua")

# A mock WoW client. Every value is a plausible constant rather than a real
# measurement — this harness asserts on SHAPE and PLUMBING, never on magnitudes,
# so no number here can leak into anything the project believes.
PRELUDE = r"""
_G = _G or {}
ACE_TEST = {printed = {}, shown = nil, logging = false, logging_calls = {}}

function print(...)
  local parts = {}
  for i = 1, select('#', ...) do parts[#parts+1] = tostring((select(i, ...))) end
  ACE_TEST.printed[#ACE_TEST.printed+1] = table.concat(parts, ' ')
end

-- Frames: accept any method, remember the ones the addon's behaviour depends on.
local frameMT = {}
frameMT.__index = function(t, k)
  local fn = rawget(t, '_real_'..k)
  if fn then return fn end
  return function(...) return nil end          -- every other method is a no-op
end

local function newFrame()
  local f = {events = {}, _handlers = {}}
  f._real_SetScript = function(self, ev, fn) self._handlers[ev] = fn end
  f._real_GetScript = function(self, ev) return self._handlers[ev] end
  f._real_RegisterEvent = function(self, ev) self.events[ev] = true end
  f._real_UnregisterAllEvents = function(self) self.events = {} end
  f._real_SetText = function(self, txt) self.text = txt; ACE_TEST.shown = txt end
  f._real_CreateFontString = function() return newFrame() end
  return setmetatable(f, frameMT)
end

ACE_TEST.frames = {}
function CreateFrame(kind, name, parent, template)
  local f = newFrame()
  ACE_TEST.frames[#ACE_TEST.frames+1] = f
  if name then _G[name] = f end
  return f
end

UIParent = newFrame()
ChatFontNormal = newFrame()
SlashCmdList = {}

-- Combat logging: the API the addon must VERIFY rather than assume.
function LoggingCombat(want)
  if want == nil then return ACE_TEST.logging end
  ACE_TEST.logging_calls[#ACE_TEST.logging_calls+1] = want and 'on' or 'off'
  ACE_TEST.logging = want and true or false
  return ACE_TEST.logging
end

-- Character sheet
function UnitName(u) if u == 'target' then return ACE_TEST.target_name end
                     if u == 'pet' then return nil end
                     return 'Elric' end
function GetRealmName() return 'Darkmoon - Season 10 Wildcard' end
function UnitLevel() return 60 end
function UnitGUID(u) if u == 'target' then return ACE_TEST.target_guid end return '0xPLAYER' end
function UnitStat(u, i) local v = {121, 84, 130, 359, 90} return v[i], v[i] end
function UnitAttackPower() return ACE_TEST.ap or 141, 0, 0 end
function UnitRangedAttackPower() return 60, 0, 0 end
function UnitPowerType() return 0, 'MANA' end
function UnitPowerMax() return 4200 end
function UnitPower() return 4200 end
function GetManaRegen() return 12.5, 3.1 end
function GetSpellBonusDamage(school) return 600 + school end
function GetSpellBonusHealing() return 243 end
function GetCritChance() return 21.76 end
function GetRangedCritChance() return 11.2 end
function GetSpellCritChance(school) return 18.9 + school end
function GetMeleeHaste() return 1.06 end
function UnitSpellHaste() return 3.0 end
function GetHaste() return 3.0 end
function GetRangedHaste() return 0 end
function GetCombatRating(id) return 36 end
function GetCombatRatingBonus(id) return 3.6 end
function UnitArmor() return 1000, 1200 end
function UnitDamage() return 227.7, 253.7, 180.2, 200.4 end
function UnitAttackSpeed() return 1.66, 1.90 end
function UnitExists(u) return false end
function UnitCreatureFamily() return nil end
function UnitHealthMax() return 3000 end
function GetSpellInfo(id) return 'Probe', 'Rank 1', 'icon', 100, false, 0, 1500 end
function GetNumSpellTabs() return 1 end
function GetSpellTabInfo(t) return 'General', '', 0, 2 end
function GetSpellLink(i) return '|cff71d5ff|Hspell:'..(1000+i)..'|h[Spell]|h|r' end
function GetSpellName(i) return 'Spell'..i, 'Rank 1' end
function GetNumTalentTabs() return 0 end
function GetNumTalents() return 0 end
function GetTalentInfo() return nil end
function GetActionInfo(slot) if slot == 1 then return 'spell', 1, 'spell' end return nil end
function GetMacroInfo() return nil end
function GetItemInfo(link) return 'An Item' end
function GetItemStats(link) return {ITEM_MOD_STRENGTH_SHORT = 45} end

-- Weapons. The MAIN HAND carries enchant 23392 = Consecrated Weapon 6, which is
-- the imbue rank the repo must be able to read back off a parse.
function GetInventoryItemLink(unit, slot)
  if slot == 16 then
    return '|cffa335ee|Hitem:200001:23392:0:0:0:0:0:0:60:0|h[The Light\'s Hope]|h|r'
  elseif slot == 17 then
    return '|cffa335ee|Hitem:200002:23392:0:0:0:0:0:0:60:0|h[Dawnreaver]|h|r'
  elseif slot == 1 then
    return '|cffa335ee|Hitem:200003:0:0:0:0:0:0:0:60:0|h[A Helm]|h|r'
  end
  return nil
end

-- A monotonic clock, so ExportedAt stamps differ between snapshots the way real
-- ones do. A harness where every stamp is identical cannot see an ordering bug.
ACE_TEST.clock = 0
local _rawdate = os and os.date
function date(fmt)
  ACE_TEST.clock = ACE_TEST.clock + 37
  local t = ACE_TEST.clock
  return string.format('2026-08-08 %02d:%02d:%02d', 13 + math.floor(t/3600),
                       math.floor(t/60) % 60, t % 60)
end
"""

DRIVER = r"""
local function slash(arg) SlashCmdList['ASCENSIONCRAFTEREXPORT'](arg) end
local function fire(ev)
  for _, f in ipairs(ACE_TEST.frames) do
    local h = f._handlers and f._handlers['OnEvent']
    if h and f.events and f.events[ev] then h(f, ev) end
  end
end

-- login path first, exactly as the client does it
fire('ADDON_LOADED')
fire('PLAYER_LOGIN')

slash('start')
ACE_TEST.target_name = 'Training Dummy'
ACE_TEST.target_guid = '0xF130002FE3000994'
fire('PLAYER_REGEN_DISABLED')
ACE_TEST.ap = 221                     -- the imbue goes up mid-fight
fire('PLAYER_REGEN_ENABLED')
slash('snap')
ACE_TEST.target_name = nil            -- no target for the second pull
ACE_TEST.target_guid = nil
fire('PLAYER_REGEN_DISABLED')
fire('PLAYER_REGEN_ENABLED')
slash('status')
slash('stop')
return ACE_TEST.shown, table.concat(ACE_TEST.logging_calls, ','),
       table.concat(ACE_TEST.printed, '\n'), tostring(ACE_TEST.logging)
"""


def run_addon():
    try:
        from lupa import lua51
    except ImportError:                                       # noqa: BLE001
        return None, ("lupa is not installed — this harness CANNOT RUN. "
                      "`py -m pip install lupa`. Reporting that it did not "
                      "run, rather than a pass it did not earn.")
    L = lua51.LuaRuntime(unpack_returned_tuples=True)
    L.execute(PRELUDE)
    src = ADDON.read_text(encoding="utf-8")
    compiled = L.eval("function(s, n) return loadstring(s, n) end")(src, "@addon")
    if compiled is None:
        return None, "the addon does not COMPILE under Lua 5.1"
    # The addon reads `local ADDON_NAME = ...` from its vararg, as the client
    # passes it. Calling with the name reproduces that exactly.
    compiled("AscensionCrafterExport")
    blob, calls, printed, final = L.execute(DRIVER)
    return {"blob": blob, "logging_calls": calls, "printed": printed,
            "logging_final": final}, None


def split_blocks(text):
    """Split on the stat-block header, the same way the pairing tool does."""
    import re
    header = re.compile(r"^\s*===\s+.+\s+-\s+.+\s+-\s+.+\s+===\s*$")
    blocks, cur = [], None
    for ln in text.splitlines(keepends=True):
        if header.match(ln):
            if cur:
                blocks.append("".join(cur))
            cur = [ln]
        elif cur is not None:
            cur.append(ln)
    if cur:
        blocks.append("".join(cur))
    return blocks


def main():
    rc = 0
    checks = []

    def check(ok, label, detail=""):
        nonlocal rc
        checks.append((ok, label, detail))
        if not ok:
            rc = 1

    result, err = run_addon()
    if result is None:
        print(f"🛑 [3o-B] CANNOT RUN — {err}")
        return 1
    blob = result["blob"]

    blocks = split_blocks(blob)
    reasons = []
    for b in blocks:
        for ln in b.splitlines():
            if ln.startswith("SnapshotReason:"):
                reasons.append(ln.split(":", 1)[1].strip())

    # The spec's own acceptance arithmetic: combats x 2 + start + stop + manuals.
    expected = 2 * 2 + 1 + 1 + 1
    check(len(blocks) == expected,
          f"snapshot count = combats x2 + start + stop + manuals = {expected}",
          f"got {len(blocks)}: {reasons}")
    check(reasons == ["session_start", "combat_start", "combat_end", "manual",
                      "combat_start", "combat_end", "session_stop"],
          "snapshots appear in the order the events fired",
          f"got {reasons}")

    # Every block must parse, and must carry the stats — this is the property
    # that lets pair_parses_to_stats.py ingest a session blob unchanged.
    parsed, failed = [], []
    for b in blocks:
        try:
            parsed.append(parse_stat_block(b))
        except Exception as e:                                # noqa: BLE001
            failed.append(f"{type(e).__name__}: {e}")
    check(not failed, "every snapshot parses with core.builds.stat_block",
          "; ".join(failed))
    check(all(p.get("character") == "Elric" for p in parsed),
          "every snapshot identifies its character",
          str([p.get("character") for p in parsed]))
    check(all(p.get("attack_power") is not None for p in parsed),
          "every snapshot carries attack_power")

    # 🚨 THE MAGNITUDE ARM, not a label arm (`3n`'s lesson). A stat that MOVED
    # between two snapshots must read differently in the two blocks — this is
    # the entire point of bracketing, and a session that emitted one cached
    # block per snapshot would pass every count above while failing this.
    aps = [p.get("attack_power") for p in parsed]
    check(len(set(aps)) > 1,
          "a stat that changed mid-session reads DIFFERENTLY across snapshots",
          f"attack_power per snapshot: {aps}")

    # Timestamps must advance: a blob of identical stamps cannot be windowed.
    stamps = [p.get("exported_at") for p in parsed]
    check(all(s is not None for s in stamps) and
          stamps == sorted(s for s in stamps if s is not None),
          "ExportedAt stamps are present and monotonic",
          str([str(s) for s in stamps]))

    # Target + weapon lines: the two fields that only the session path emits.
    combat_starts = [b for b in blocks if "SnapshotReason: combat_start" in b]
    check(any("Target: Training Dummy / 0xF130002FE3000994" in b
              for b in combat_starts),
          "combat_start carries the target's NAME and GUID when one exists")
    check(any("Target: none" in b for b in combat_starts),
          "…and says `none` when there is no target, rather than guessing")
    check(all("WeaponMH: item:200001:23392:" in b for b in combat_starts),
          "weapon itemStrings carry the enchant id (= the imbue RANK per parse)")

    # The full export happens exactly once, at session_start — the size
    # discipline the spec asks for (a 5-boss dungeon has to paste in one go).
    gear_blocks = [b for b in blocks if "--- Gear ---" in b]
    check(len(gear_blocks) == 1 and "SnapshotReason: session_start" in gear_blocks[0],
          "the full gear/board dump appears ONCE, in the session_start snapshot",
          f"{len(gear_blocks)} block(s) carry gear")

    # 🛑 Logging: turned ON at start, OFF at stop, and VERIFIED both times.
    #
    # ⚠ The first draft of this arm read `("...verified ON" in blob) or True`,
    # which is green under every possible mutation — the exact vacuity `3f`
    # found four of and `3n` found two more of, written here by the session
    # that quotes those lessons. It is kept in the comment rather than deleted
    # because the shape is the point: an arm ending `or True` is not a weak
    # check, it is not a check. The replacement asserts the CALLS the addon
    # made and the state it left behind, both observed in the mock client.
    check(result["logging_calls"] == "on,off",
          "logging is enabled at /ace start and disabled at /ace stop, in order",
          f"LoggingCombat calls: {result['logging_calls']!r}")
    check(result["logging_final"] == "false",
          "the client is left with logging OFF after /ace stop",
          f"final state {result['logging_final']!r}")
    check("combat logging verified ON" in result["printed"]
          and "combat logging verified OFF" in result["printed"],
          "both states are reported from a READ-BACK, never assumed",
          f"printed: {result['printed'][-200:]!r}")

    for ok, label, detail in checks:
        print(f"{'PASS ' if ok else '🛑 FAIL'} [3o-B] {label}"
              + (f"  ({detail})" if detail and not ok else ""))
    print(f"\n[addon] {sum(1 for c in checks if c[0])}/{len(checks)} checks "
          f"passed against a stubbed Lua 5.1 client; "
          f"{len(blocks)} snapshots, {len(blob)} chars of blob")
    return rc


if __name__ == "__main__":
    sys.exit(main())
