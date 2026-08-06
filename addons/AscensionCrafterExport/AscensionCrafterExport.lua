--[[
AscensionCrafter Export addon
=============================================================
Standalone addon (not a WeakAura) - runs with normal addon API access,
outside WeakAuras' sandboxed custom-trigger pipeline. Built after the
WeakAuras "Custom Function" trigger route hit a hard wall: this server's
WeakAuras fork blocks `pcall` even inside a brand-new aura containing just
`true`, which means the block is coming from WeakAuras' own internal
trigger-execution wrapper, not anything pasted into it. A real addon file
isn't run through that pipeline, so this sidesteps the issue entirely.

Companion to inspects.nie.one - that already covers spec/talent/gear-ID
capture. This covers what it doesn't: full resolved per-slot item STATS,
live sheet numbers, resources, pet, and the board + rotation IN THE SAME
ARTIFACT, sharing one timestamp.

INSTALL:
  1. Copy this whole "AscensionCrafterExport" folder (both files) into
     your WoW install's Interface/AddOns/ folder, so the path looks like:
       .../Interface/AddOns/AscensionCrafterExport/AscensionCrafterExport.toc
       .../Interface/AddOns/AscensionCrafterExport/AscensionCrafterExport.lua
  2. Fully restart the WoW client (or at minimum /reload).
  3. At the character-select screen, confirm "AscensionCrafterExport" is
     checked in the AddOns list (bottom-left).
  4. In-game: type /acexport (or /ace) - or click the small draggable
     note-icon button that appears near screen-center on login.
  5. A copyable text window pops up. Ctrl+A, Ctrl+C, paste here.

CAVEATS:
  - Written against the standard WotLK 3.3.5 client Lua API, Ascension's
    client base per the primer. Every game-API call is pcall-wrapped so
    one broken/renamed API on this server skips that one line instead of
    breaking the whole export.
  - ⚠ A SKIPPED LINE IS SILENT. If an expected field is absent, that API
    does not exist here - the export will not say so. Diff a fresh export
    against the expected field list before relying on any single field.

CHANGELOG
  2026-08-06c - Two real bugs from the second live test.
    * 🚨 ACTION BARS WERE WRONG AND LOOKED PLAUSIBLE - the worst kind.
      `GetActionInfo` returns a SPELLBOOK INDEX, not a spell id, and the
      old code fed that index to `GetSpellInfo` as though it were an id.
      Low indices collided with low real spell ids, so a Frost Mage's bars
      resolved to "Backstab", "Terocone Motherlode" and "Normal bow shot
      (TEST)" - garbage that reads like data. Proof it was an index: the
      largest value seen was 156 and the spellbook held exactly 156
      entries. Now resolved through an index->id map built during the
      spellbook walk, and anything unresolvable is emitted as `idx<N>`
      so it can never again be mistaken for a spell id.
    * 🚨 `GetSpellInfo`'s 4th return is NOT cast time on this client.
      Measured: Arcane Intellect ranks 1-5 all reported "469ms" against a
      1500ms base (a 3.2x reduction no haste can produce), and Arcane
      Brilliance reported 1227ms - the two differ in the way MANA COST
      differs, not the way cast time does. That is the 4.x+ signature
      (name, rank, icon, cost, isFunnel, powerType, castTime, ...).
      🛑 Rather than guess a second position, the export now DUMPS ALL
      RETURNS BY POSITION for three probe spells chosen to identify the
      signature by contrast: one cast-time spell, one instant, one
      channel. Whichever position reads 0 for the instant is cast time.
    * 🆕 Cast-time probes deduped by name, keeping the highest rank, so
      the list surfaces max-rank damage spells instead of five ranks of
      Arcane Intellect.
    * 🆕 Pet spellbook walk (BOOKTYPE_PET) - pet abilities are the only
      route to modelling pet damage, and C5 has no ground truth at all.

  2026-08-06b - Spell-haste probes, `MeleeHaste_total` renamed
    `MeleeHaste_raw_UNVERIFIED` (it read 1.06% while `Rating_HasteMelee`
    read 3.77% on the same character - a total cannot be under its own
    rating component; weapon-speed ground truth implies ~5.71% and
    neither value reproduces it). Phantom off-hand fixed: `UnitDamage`
    returns the UNARMED baseline rather than nil, so a nonzero damage
    value alone never meant a weapon existed. Board capture added.

  2026-08-06a - ExportedAt, PowerType/PowerMax, ManaMax, ManaRegen_raw.
    ⚠ ManaRegen printed unconverted and labelled raw: the sheet shows
    per-5-seconds, this is the raw per-second API return. NOT rescaled,
    because guessing the unit and being wrong is worse than stating what
    was read.
]]--

local ADDON_NAME = ...

local SCHOOLS = {
  {id=2, tag="Holy"}, {id=3, tag="Fire"}, {id=4, tag="Nature"},
  {id=5, tag="Frost"}, {id=6, tag="Shadow"}, {id=7, tag="Arcane"},
}

local SLOTS = {
  {1,"Head"},{2,"Neck"},{3,"Shoulder"},{5,"Chest"},{6,"Waist"},
  {7,"Legs"},{8,"Feet"},{9,"Wrist"},{10,"Hands"},{11,"Ring1"},
  {12,"Ring2"},{13,"Trinket1"},{14,"Trinket2"},{15,"Back"},
  {16,"MainHand"},{17,"OffHand"},{18,"Ranged"},
}

-- Probe spells chosen to identify GetSpellInfo's return signature by
-- CONTRAST rather than by assumption. An instant must read 0 in whichever
-- position holds cast time; a channel and a normal cast must both be
-- nonzero. Any position that fails that pattern is not cast time.
local SIGNATURE_PROBES = {
  {id=25304,  note="Frostbolt R11 - normal cast, expect nonzero cast time"},
  {id=300909, note="Ice Lance R5 - INSTANT, expect ZERO cast time"},
  {id=10187,  note="Blizzard R6 - channel, expect nonzero"},
}

local MAX_ACTION_SLOTS  = 120
local MAX_SPELLBOOK     = 800
local MAX_PET_SPELLS    = 40
local HASTE_PROBE_LIMIT = 30
local PER_LINE          = 6

local function safe(fn, ...)
  if not fn then return nil end
  local ok, a,b,c,d,e,f,g,h = pcall(fn, ...)
  if ok then return a,b,c,d,e,f,g,h end
  return nil
end

-- pcall wrapper that preserves ALL returns, for signature probing
local function safePack(fn, ...)
  if not fn then return nil end
  local res = {pcall(fn, ...)}
  if res[1] then table.remove(res, 1); return res end
  return nil
end

local function idFromLink(link)
  if not link then return nil end
  local id = string.match(link, "spell:(%d+)")
  return id and tonumber(id) or nil
end

local function addWrapped(add, prefix, items, perLine)
  if #items == 0 then return end
  local chunk = {}
  for i = 1, #items do
    table.insert(chunk, items[i])
    if #chunk >= perLine or i == #items then
      add(prefix .. table.concat(chunk, ", "))
      chunk = {}
    end
  end
end

local function gatherText()
  local lines = {}
  local function add(s) table.insert(lines, s) end

  add("=== " .. (UnitName("player") or "?") .. " - " .. (GetRealmName() or "?") .. " ===")
  add("Level: " .. tostring(UnitLevel("player")))

  local stamp = safe(date, "%Y-%m-%d %H:%M:%S")
  if stamp then add("ExportedAt: "..stamp.." (client local time)") end

  local statNames = {"Strength","Agility","Stamina","Intellect","Spirit"}
  for i=1,5 do
    local base, total = safe(UnitStat, "player", i)
    if base then add(statNames[i]..": "..(total or base)) end
  end

  local apBase, apPos, apNeg = safe(UnitAttackPower, "player")
  if apBase then add("AttackPower: "..(apBase+(apPos or 0)+(apNeg or 0))) end
  local rapBase, rapPos, rapNeg = safe(UnitRangedAttackPower, "player")
  if rapBase then add("RangedAttackPower: "..(rapBase+(rapPos or 0)+(rapNeg or 0))) end

  -- --- Resources ---------------------------------------------------------
  local powerType, powerToken = safe(UnitPowerType, "player")
  if powerToken then add("PowerType: "..tostring(powerToken)) end
  if powerType then
    local pMax = safe(UnitPowerMax, "player", powerType)
    local pCur = safe(UnitPower, "player", powerType)
    if pMax then add("PowerMax: "..pMax..(pCur and (" (current "..pCur..")") or "")) end
  end
  local manaMax = safe(UnitPowerMax, "player", 0)
  if manaMax and manaMax > 0 then add("ManaMax: "..manaMax) end
  local mBase, mCasting = safe(GetManaRegen)
  if mBase then
    add(("ManaRegen_raw: %.4f not-casting / %.4f casting (RAW API return, unconverted)")
        :format(mBase, mCasting or 0))
  end

  for _, s in ipairs(SCHOOLS) do
    local v = safe(GetSpellBonusDamage, s.id)
    if v then add("SpellPower_"..s.tag..": "..v) end
  end
  local heal = safe(GetSpellBonusHealing)
  if heal then add("BonusHealing: "..heal) end

  local meleeCrit = safe(GetCritChance)
  if meleeCrit then add(("MeleeCrit: %.2f%%"):format(meleeCrit)) end
  local rangedCrit = safe(GetRangedCritChance)
  if rangedCrit then add(("RangedCrit: %.2f%%"):format(rangedCrit)) end
  for _, s in ipairs(SCHOOLS) do
    local v = safe(GetSpellCritChance, s.id)
    if v then add(("SpellCrit_%s: %.2f%%"):format(s.tag, v)) end
  end

  -- --- Haste, raw and unverified -----------------------------------------
  -- 🛑 Nothing in this block is trusted. GetMeleeHaste disagreed with both
  -- the rating line and the actual swing timer on 2026-08-06. The cast-time
  -- route below is the reliable one: the repo holds each spell's BASE cast
  -- time, so client/base carries its own check digit.
  local mh = safe(GetMeleeHaste)
  if mh then add(("MeleeHaste_raw_UNVERIFIED: %.2f%% (GetMeleeHaste)"):format(mh)) end
  local ush = safe(UnitSpellHaste, "player")
  if ush then add(("SpellHaste_raw_UNVERIFIED: %.2f%% (UnitSpellHaste)"):format(ush)) end
  local gh = safe(GetHaste)
  if gh then add(("Haste_raw_UNVERIFIED: %.2f%% (GetHaste)"):format(gh)) end
  local rh = safe(GetRangedHaste)
  if rh then add(("RangedHaste_raw_UNVERIFIED: %.2f%% (GetRangedHaste)"):format(rh)) end

  local ratings = {
    {id=(CR_HIT_MELEE or 6), tag="HitMelee"},
    {id=(CR_HIT_RANGED or 7), tag="HitRanged"},
    {id=(CR_HIT_SPELL or 8), tag="HitSpell"},
    {id=(CR_CRIT_MELEE or 9), tag="CritMelee"},
    {id=(CR_CRIT_RANGED or 10), tag="CritRanged"},
    {id=(CR_CRIT_SPELL or 11), tag="CritSpell"},
    {id=(CR_HASTE_MELEE or 18), tag="HasteMelee"},
    {id=(CR_HASTE_RANGED or 19), tag="HasteRanged"},
    {id=(CR_HASTE_SPELL or 20), tag="HasteSpell"},
    {id=(CR_EXPERTISE or 24), tag="Expertise"},
    {id=(CR_ARMOR_PENETRATION or 25), tag="ArmorPen"},
  }
  for _, r in ipairs(ratings) do
    local rating = safe(GetCombatRating, r.id)
    local bonus = safe(GetCombatRatingBonus, r.id)
    if rating then add(("Rating_%s: %d (%.2f%%)"):format(r.tag, rating, bonus or 0)) end
  end

  local aBase, aEff = safe(UnitArmor, "player")
  if aEff then add("Armor: "..aEff) end

  local lo, hi, offLo, offHi = safe(UnitDamage, "player")
  local mSpeed, oSpeed = safe(UnitAttackSpeed, "player")
  if lo then add(("MainHandDamage: %.1f-%.1f (speed %.2f)"):format(lo, hi, mSpeed or 0)) end
  -- ⚠ UnitDamage returns the UNARMED baseline, not nil, with no off-hand.
  -- A real off-hand always has a nonzero swing speed.
  if offLo and offLo > 0 and oSpeed and oSpeed > 0 then
    add(("OffHandDamage: %.1f-%.1f (speed %.2f)"):format(offLo, offHi, oSpeed))
  else
    add("OffHandDamage: none (no off-hand equipped)")
  end

  -- --- GetSpellInfo signature probe --------------------------------------
  -- Every return position, verbatim, for three spells whose expected shape
  -- differs. Identify cast time as the position reading 0 on the instant and
  -- nonzero on the other two. Do NOT assume position 4 - it is mana cost on
  -- this client (measured 2026-08-06).
  add("--- GetSpellInfo signature probe (raw returns by POSITION) ---")
  for _, p in ipairs(SIGNATURE_PROBES) do
    local res = safePack(GetSpellInfo, p.id)
    if res and res[1] then
      local parts = {}
      for i = 1, 9 do
        parts[#parts+1] = i.."="..tostring(res[i])
      end
      add(("  [%d] %s"):format(p.id, p.note))
      add("     "..table.concat(parts, " | "))
    else
      add(("  [%d] %s -> NOT KNOWN by this character"):format(p.id, p.note))
    end
  end

  -- --- Board: spellbook ---------------------------------------------------
  -- Everything the character KNOWS. On a classless server this is the closest
  -- thing to the slotted card board a standard API exposes. The index->id map
  -- built here is also what makes the action-bar section correct.
  local bookIds, bookByIndex, probeByName = {}, {}, {}
  local numTabs = safe(GetNumSpellTabs) or 0
  local walked = 0
  for t = 1, numTabs do
    local tabName, _, offset, numSpells = safe(GetSpellTabInfo, t)
    if offset and numSpells then
      for i = offset + 1, offset + numSpells do
        walked = walked + 1
        if walked > MAX_SPELLBOOK then break end
        local link = safe(GetSpellLink, i, "spell")
        local sid  = idFromLink(link)
        local nm, rk = safe(GetSpellName, i, "spell")
        if sid then
          local label = tostring(sid)
          if nm then
            label = label .. ":" .. nm .. ((rk and rk ~= "") and ("("..rk..")") or "")
          end
          table.insert(bookIds, label)
          bookByIndex[i] = label
          -- Cast-time probe, deduped by NAME keeping the LAST seen, which is
          -- the highest rank - otherwise the list fills with five ranks of a
          -- buff and never reaches the damage spells.
          if nm then probeByName[nm] = sid end
        else
          bookByIndex[i] = "idx"..i
        end
      end
    end
  end
  if #bookIds > 0 then
    add("--- Spellbook ("..#bookIds.." known) ---")
    addWrapped(add, "  ", bookIds, PER_LINE)
  end

  -- --- Cast-time probes ---------------------------------------------------
  -- Emitted with ALL positions again, because until the signature probe above
  -- is read, we do not know which field to quote.
  local probeList = {}
  for nm, sid in pairs(probeByName) do
    if #probeList < HASTE_PROBE_LIMIT then
      local res = safePack(GetSpellInfo, sid)
      if res then
        -- keep only spells where SOME position looks like a timing value
        local p4, p7 = res[4], res[7]
        if (type(p4)=="number" and p4 > 0) or (type(p7)=="number" and p7 > 0) then
          table.insert(probeList, ("%d:%s[4=%s,7=%s]")
            :format(sid, nm, tostring(p4), tostring(p7)))
        end
      end
    end
  end
  if #probeList > 0 then
    add("--- Cast/cost probes, max rank per name (positions 4 and 7) ---")
    addWrapped(add, "  ", probeList, 3)
  end

  -- --- Board: talent API, if this server exposes one ----------------------
  local talentLines = {}
  local numTalentTabs = safe(GetNumTalentTabs) or 0
  for tt = 1, numTalentTabs do
    local numTalents = safe(GetNumTalents, tt) or 0
    for ti = 1, numTalents do
      local tname, _, _, _, rank, maxRank = safe(GetTalentInfo, tt, ti)
      if tname and rank and rank > 0 then
        table.insert(talentLines, ("%s %d/%s"):format(tname, rank, tostring(maxRank or "?")))
      end
    end
  end
  if #talentLines > 0 then
    add("--- Talents (standard API) ---")
    addWrapped(add, "  ", talentLines, 4)
  else
    add("--- Talents (standard API): none returned (expected on a classless server) ---")
  end

  -- --- Rotation: action bars ---------------------------------------------
  -- 🚨 GetActionInfo's second return is a SPELLBOOK INDEX, not a spell id.
  -- Feeding it to GetSpellInfo produces confident nonsense (a Frost Mage's
  -- bars resolved to "Backstab" and "Normal bow shot (TEST)"). Resolve it
  -- through the index map built above; anything unresolved is emitted as
  -- idx<N> so it can never be misread as an id.
  local barIds = {}
  for slot = 1, MAX_ACTION_SLOTS do
    local aType, aId, aSubType = safe(GetActionInfo, slot)
    if aType == "spell" and aId then
      local label = bookByIndex[aId]
      if not label then
        local link = safe(GetSpellLink, aId, aSubType or "spell")
        local rid  = idFromLink(link)
        local nm   = safe(GetSpellName, aId, aSubType or "spell")
        label = rid and (rid..":"..(nm or "?")) or ("idx"..tostring(aId).."(UNRESOLVED)")
      end
      table.insert(barIds, label.."@"..slot)
    elseif aType == "item" and aId then
      table.insert(barIds, ("item%d@%d"):format(aId, slot))
    elseif aType == "macro" and aId then
      local mname = safe(GetMacroInfo, aId)
      table.insert(barIds, ("macro%d:%s@%d"):format(aId, tostring(mname or "?"), slot))
    end
  end
  if #barIds > 0 then
    add("--- Action bars ("..#barIds.." bound; resolved via spellbook index) ---")
    addWrapped(add, "  ", barIds, PER_LINE)
  end

  -- --- Pet ----------------------------------------------------------------
  -- No pet model exists in core/sim, while the corpus counts pet damage into
  -- DPS. Recording the pet is what separates "unmodelled pet" from "the model
  -- is wrong" when a parse comes up short.
  if safe(UnitExists, "pet") then
    local pname = safe(UnitName, "pet") or "?"
    local pfam  = safe(UnitCreatureFamily, "pet")
    local plvl  = safe(UnitLevel, "pet")
    add(("Pet: %s (family %s, level %s)"):format(pname, tostring(pfam or "?"), tostring(plvl or "?")))
    local pAtkBase, pAtkPos, pAtkNeg = safe(UnitAttackPower, "pet")
    if pAtkBase then add("Pet_AttackPower: "..(pAtkBase+(pAtkPos or 0)+(pAtkNeg or 0))) end
    local pLo, pHi = safe(UnitDamage, "pet")
    local pSpeed = safe(UnitAttackSpeed, "pet")
    if pLo then add(("Pet_Damage: %.1f-%.1f (speed %.2f)"):format(pLo, pHi or pLo, pSpeed or 0)) end
    local pHealth = safe(UnitHealthMax, "pet")
    if pHealth then add("Pet_HealthMax: "..pHealth) end
    local pMana = safe(UnitPowerMax, "pet", 0)
    if pMana and pMana > 0 then add("Pet_ManaMax: "..pMana) end

    -- pet spellbook: the only route to modelling what the pet actually does
    local petSpells = {}
    for i = 1, MAX_PET_SPELLS do
      local nm, rk = safe(GetSpellName, i, "pet")
      if not nm then break end
      local link = safe(GetSpellLink, i, "pet")
      local sid  = idFromLink(link)
      table.insert(petSpells, (sid and (sid..":") or "idx"..i..":")..nm
        ..((rk and rk ~= "") and ("("..rk..")") or ""))
    end
    if #petSpells > 0 then
      add("--- Pet spellbook ("..#petSpells..") ---")
      addWrapped(add, "  ", petSpells, 4)
    end
  else
    add("Pet: none")
  end

  add("--- Gear ---")
  for _, slotdef in ipairs(SLOTS) do
    local slotId, slotName = slotdef[1], slotdef[2]
    local link = GetInventoryItemLink("player", slotId)
    if link then
      local itemName = safe(GetItemInfo, link)
      local statTable = safe(GetItemStats, link) or {}
      local statParts = {}
      for statKey, statVal in pairs(statTable) do
        table.insert(statParts, tostring(statKey)..":"..tostring(statVal))
      end
      table.sort(statParts)
      add(("[%s] %s | %s"):format(slotName, itemName or link, table.concat(statParts, ", ")))
    end
  end

  return table.concat(lines, "\n")
end

-- copyable popup window (created lazily, once)
local exportFrame
local function ensureExportFrame()
  if exportFrame then return exportFrame end

  local f = CreateFrame("Frame", "AscensionCrafterExportFrame", UIParent)
  f:SetSize(520, 420)
  f:SetPoint("CENTER")
  f:SetFrameStrata("DIALOG")
  if f.SetBackdrop then
    f:SetBackdrop({
      bgFile = "Interface/DialogFrame/UI-DialogBox-Background",
      edgeFile = "Interface/DialogFrame/UI-DialogBox-Border",
      tile = true, tileSize = 32, edgeSize = 32,
      insets = {left=11, right=12, top=12, bottom=11},
    })
  end
  f:EnableMouse(true)
  f:SetMovable(true)
  f:RegisterForDrag("LeftButton")
  f:SetScript("OnDragStart", f.StartMoving)
  f:SetScript("OnDragStop", f.StopMovingOrSizing)
  f:Hide()

  local scroll = CreateFrame("ScrollFrame", "AscensionCrafterExportScroll", f, "UIPanelScrollFrameTemplate")
  scroll:SetPoint("TOPLEFT", 20, -30)
  scroll:SetPoint("BOTTOMRIGHT", -32, 40)

  local edit = CreateFrame("EditBox", nil, scroll)
  edit:SetMultiLine(true)
  edit:SetFontObject(ChatFontNormal)
  edit:SetWidth(460)
  edit:SetAutoFocus(false)
  edit:SetScript("OnEscapePressed", function(self) f:Hide() end)
  scroll:SetScrollChild(edit)
  f.editBox = edit

  local close = CreateFrame("Button", nil, f, "UIPanelCloseButton")
  close:SetPoint("TOPRIGHT", -4, -4)
  close:SetScript("OnClick", function() f:Hide() end)

  local title = f:CreateFontString(nil, "OVERLAY", "GameFontNormal")
  title:SetPoint("TOP", 0, -12)
  title:SetText("AscensionCrafter Export - Ctrl+A, Ctrl+C, paste to Claude")

  exportFrame = f
  return f
end

local function showExport()
  local f = ensureExportFrame()
  local text = gatherText()
  f.editBox:SetText(text)
  f.editBox:HighlightText()
  f.editBox:SetFocus()
  f:Show()
end

-- slash command
SLASH_ASCENSIONCRAFTEREXPORT1 = "/acexport"
SLASH_ASCENSIONCRAFTEREXPORT2 = "/ace"
SlashCmdList["ASCENSIONCRAFTEREXPORT"] = function()
  showExport()
end

-- draggable button, created once on login
local eventFrame = CreateFrame("Frame")
eventFrame:RegisterEvent("PLAYER_LOGIN")
eventFrame:SetScript("OnEvent", function()
  if _G.ACF_ExportButton then return end
  local btn = CreateFrame("Button", "ACF_ExportButton", UIParent)
  btn:SetSize(100, 100)
  btn:SetPoint("CENTER", UIParent, "CENTER", 200, 0)
  btn:SetNormalTexture("Interface\\Icons\\INV_Misc_Note_01")
  btn:SetHighlightTexture("Interface\\Buttons\\ButtonHilight-Square")
  btn:EnableMouse(true)
  btn:SetMovable(true)
  btn:RegisterForDrag("LeftButton")
  btn:SetScript("OnDragStart", btn.StartMoving)
  btn:SetScript("OnDragStop", btn.StopMovingOrSizing)
  btn:SetScript("OnClick", showExport)

  local label = btn:CreateFontString(nil, "OVERLAY", "GameFontNormalLarge")
  label:SetPoint("TOP", btn, "BOTTOM", 0, -2)
  label:SetText("Export")
  print("|cff33ff99AscensionCrafterExport|r loaded. Type /acexport or /ace, or click the draggable note icon.")
end)
