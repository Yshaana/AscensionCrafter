--[[
SUPERSEDED (2026-08-04): the "Custom Function" WeakAuras trigger route hit
a hard wall — this server's WeakAuras fork throws "Forbidden function or
table: pcall" even on a brand-new aura containing nothing but the literal
code `true`, meaning the block comes from WeakAuras' own internal trigger
execution wrapper, not from anything pasted into the box. Custom Function
triggers may not be usable at all on this server. Use
index/AscensionCrafterExport/ instead — a real standalone addon (.toc +
.lua) that runs outside WeakAuras' sandbox entirely. Left here for
reference only; do not paste this into WeakAuras again.
=============================================================

AscensionCrafter Gear/Stat Exporter — WeakAura custom code (v2)
=============================================================
Companion to inspects.nie.one, not a replacement. inspects.nie.one already
captures spec/talent/gear IDs well. This aura captures what that export
does NOT give us: full resolved per-slot item STATS, and your live stat
sheet numbers (primary stats, AP/RAP, per-school Spell Power, crit/hit/
haste/expertise/armor pen). Paste the output back into chat as plain text.

v2 rewrite: your WeakAuras editor has ONE "Custom" code box under Trigger
Combination -> Required for Activation -> Custom Function (screenshot
confirmed, 2026-08-04) — no separate Load/Actions/Init tabs. That box gets
compiled as `loadstring("return " .. your_code)`, which is why v1's
multi-statement paste errored ("unexpected symbol near 'local'"): the box
needs ONE valid Lua expression, not a statement list.

Fix: everything below IS one expression — an immediately-invoked function
`(function() ... end)()` — so `return (function() ... end)()` is valid.
It also doesn't rely on a WeakAuras icon/region at all: it builds its OWN
draggable button the first time it runs, guarded so repeat trigger checks
don't recreate it. The button is what you click; the WeakAuras aura itself
can stay invisible/ignored — it's only here as the vehicle to run this code.

SETUP:
  1. Create any aura, set its trigger type to "Custom Function" (per your
     screenshot).
  2. Paste the ENTIRE block below (everything from "(function()" through
     the final "end)()") into the black "Custom" text box.
  3. Click Accept.
  4. A small draggable icon button appears on screen (default: center-ish).
     Drag it wherever you want (e.g. next to your character panel).
  5. Click the button any time -> a copyable text window pops up. Ctrl+A,
     Ctrl+C, paste here.

CAVEATS:
  - Written against the standard WotLK 3.3.5 client Lua API (UnitStat,
    GetSpellBonusDamage, GetCombatRating, GetItemStats, etc.), Ascension's
    client base per the primer.
  - v3: this WeakAuras fork's sandbox blocks `pcall` ("Forbidden function
    or table: pcall") - removed. The `safe()` helper now only guards
    against an API not EXISTING on this server (still calls the game
    function directly, unprotected, if it does exist) - it can no longer
    catch a function that exists but errors on given arguments. If a
    specific line errors, paste the error text and that one call gets a
    manual guard instead.
  - Still untested in a live client (no WoW client available here). If
    the Accept button itself rejects this with a syntax error, or nothing
    appears after Accept, or the popup is blank/wrong, paste the exact
    error text (or a screenshot) back and it'll get fixed.
  - GetItemStats() key names (ITEM_MOD_CRIT_RATING_SHORT, etc.) are left
    mostly raw rather than translated — still readable, safer than
    guessing a mapping that might be wrong.
]]--

(function()
  if _G.ACF_ExportInit then return true end
  _G.ACF_ExportInit = true

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
    -- pcall is blocked by this WeakAuras fork's sandbox ("Forbidden function
    -- or table: pcall"), so this only guards against the function not
    -- existing on this server, not against it existing and erroring.
    if not fn then return nil end
    return fn(...)
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

  -- copyable popup window (created once)
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

  AscensionCrafterExportFrame = f

  -- self-made draggable button (does NOT depend on the WeakAuras icon/region)
  local btn = CreateFrame("Button", "ACF_ExportButton", UIParent)
  btn:SetSize(32, 32)
  btn:SetPoint("CENTER", UIParent, "CENTER", 200, 0)
  btn:SetNormalTexture("Interface\\Icons\\INV_Misc_Note_01")
  btn:SetHighlightTexture("Interface\\Buttons\\ButtonHilight-Square")
  btn:EnableMouse(true)
  btn:SetMovable(true)
  btn:RegisterForDrag("LeftButton")
  btn:SetScript("OnDragStart", btn.StartMoving)
  btn:SetScript("OnDragStop", btn.StopMovingOrSizing)
  btn:SetScript("OnClick", function()
    local text = gatherText()
    f.editBox:SetText(text)
    f.editBox:HighlightText()
    f.editBox:SetFocus()
    f:Show()
  end)

  return true
end)()
