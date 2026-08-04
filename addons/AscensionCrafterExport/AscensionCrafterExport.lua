--[[
AscensionCrafter Export addon
=============================================================
Standalone addon (not a WeakAura) - runs with normal addon API access,
outside WeakAuras' sandboxed custom-trigger pipeline. Built after the
WeakAuras "Custom Function" trigger route hit a hard wall: this server's
WeakAuras fork blocks `pcall` even inside a brand-new aura containing just
`true`, which means the block is coming from WeakAuras' own internal
trigger-execution wrapper, not anything pasted into it - i.e. Custom
Function triggers may not be usable at all here, independent of code
content. A real addon file isn't run through that pipeline, so this
should sidestep the issue entirely.

Companion to inspects.nie.one, not a replacement - that already covers
spec/talent/gear-ID capture well. This covers what it doesn't: full
resolved per-slot item STATS, and live sheet numbers (primary stats,
AP/RAP, per-school Spell Power, crit/hit/haste/expertise/armor pen).

INSTALL:
  1. Copy this whole "AscensionCrafterExport" folder (both files) into
     your WoW install's Interface/AddOns/ folder, so the path looks like:
       .../Interface/AddOns/AscensionCrafterExport/AscensionCrafterExport.toc
       .../Interface/AddOns/AscensionCrafterExport/AscensionCrafterExport.lua
  2. Fully restart the WoW client (or at minimum reload UI with /reload -
     a fresh restart is safer for a first-time addon install).
  3. At the character-select screen, confirm "AscensionCrafterExport" is
     checked in the AddOns list (bottom-left).
  4. In-game: type /acexport (or /ace) - or click the small draggable
     note-icon button that appears near screen-center on login.
  5. A copyable text window pops up. Ctrl+A, Ctrl+C, paste here.

CAVEATS:
  - Written against the standard WotLK 3.3.5 client Lua API, Ascension's
    client base per the primer. Every game-API call is pcall-wrapped
    (pcall is a normal, always-available Lua function for real addons -
    the earlier WeakAuras block was specific to WeakAuras' sandboxed
    custom-code editor, not a general server-wide restriction) so one
    broken/renamed API on this server skips that one line instead of
    breaking the whole export.
  - Still untested in a live client (no WoW client available here). If
    the addon fails to load, doesn't appear in the AddOns list, or the
    slash command errors, paste the exact error text (enable Lua errors
    via /console scriptErrors 1 if you don't see one) or a screenshot
    back and it'll get fixed.
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

local function safe(fn, ...)
  if not fn then return nil end
  local ok, a,b,c,d,e,f,g,h = pcall(fn, ...)
  if ok then return a,b,c,d,e,f,g,h end
  return nil
end

local function gatherText()
  local lines = {}
  local function add(s) table.insert(lines, s) end

  add("=== " .. (UnitName("player") or "?") .. " - " .. (GetRealmName() or "?") .. " ===")
  add("Level: " .. tostring(UnitLevel("player")))

  local statNames = {"Strength","Agility","Stamina","Intellect","Spirit"}
  for i=1,5 do
    local base, total = safe(UnitStat, "player", i)
    if base then add(statNames[i]..": "..(total or base)) end
  end

  local apBase, apPos, apNeg = safe(UnitAttackPower, "player")
  if apBase then add("AttackPower: "..(apBase+(apPos or 0)+(apNeg or 0))) end
  local rapBase, rapPos, rapNeg = safe(UnitRangedAttackPower, "player")
  if rapBase then add("RangedAttackPower: "..(rapBase+(rapPos or 0)+(rapNeg or 0))) end

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
  if offLo and offLo > 0 then add(("OffHandDamage: %.1f-%.1f (speed %.2f)"):format(offLo, offHi, oSpeed or 0)) end

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
