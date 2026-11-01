"""A deliberately small World of Warcraft API mock.

The goal is not to emulate the game. The goal is to load the real add-on files
in the real .toc order and catch nil crashes, wrong return shapes, and missing
events before launching the client.

Everything is opt-in: if a mock is missing, the add-on should degrade, not
silently pretend it works.
"""

from __future__ import annotations

import lupa

COMMON_LUA = r'''
unpack = unpack or table.unpack

__FRAMES = {}
__ALL_FRAMES = {}
__PRINTED = {}
__NOW = 1000

function wipe(t)
  for k in pairs(t) do t[k] = nil end
  return t
end
tinsert = table.insert
tremove = table.remove

DEFAULT_CHAT_FRAME = {
  AddMessage = function(self, message)
    table.insert(__PRINTED, tostring(message))
  end,
}
SlashCmdList = {}

function GetTime() return __NOW end
function time() return 1700000000 end
function date() return "2026-01-01" end
function GetLocale() return __LOCALE or "enUS" end
function GetRealmName() return "TestRealm" end
function GetNormalizedRealmName() return "TestRealm" end
function UnitName() return "Tester" end
function UnitFactionGroup() return "Alliance" end
function GetBuildInfo() return "1.15.9", "11509", "Jan 1 2026", 11509 end

function CreateFrame(kind, name, parent, template)
  local f = {
    _kind = kind,
    _name = name,
    _parent = parent,
    _template = template,
    _events = {},
    _shown = true,
    _text = "",
    _children = {},
  }

  function f:RegisterEvent(event) self._events[event] = true end
  function f:UnregisterEvent(event) self._events[event] = nil end
  function f:IsEventRegistered(event) return self._events[event] == true end
  function f:SetScript(script, handler) self["_script_" .. script] = handler end
  function f:GetScript(script) return self["_script_" .. script] end
  function f:Show() self._shown = true end
  function f:Hide() self._shown = false end
  function f:IsShown() return self._shown end
  function f:SetShown(shown) self._shown = shown and true or false end
  function f:SetSize(width, height) self._w, self._h = width, height end
  function f:GetWidth() return self._w or 0 end
  function f:GetHeight() return self._h or 0 end
  function f:SetWidth(width) self._w = width end
  function f:SetHeight(height) self._h = height end
  function f:SetPoint(...) self._point = { ... } end
  function f:GetPoint() return unpack(self._point or {}) end
  function f:SetBackdrop() end
  function f:SetBackdropColor() end
  function f:SetBackdropBorderColor() end
  function f:SetMovable() end
  function f:SetClampedToScreen() end
  function f:EnableMouse() end
  function f:SetEnableMouse() end
  function f:RegisterForDrag() end
  function f:RegisterForClicks() end
  function f:SetFrameStrata() end
  function f:SetFrameLevel() end
  function f:SetAlpha() end
  function f:SetScale() end
  function f:GetScale() return 1 end
  function f:SetAllPoints() end
  function f:SetParent(value) self._parent = value end
  function f:GetParent() return self._parent end
  function f:SetText(value) self._text = tostring(value or "") end
  function f:GetText() return self._text end
  function f:SetFont() end
  function f:SetFontObject() end
  function f:SetJustifyH() end
  function f:SetJustifyV() end
  function f:SetShadowOffset() end
  function f:SetWordWrap() end
  function f:SetTextColor() end
  function f:SetTexture() end
  function f:SetColorTexture() end
  function f:SetVertexColor() end
  function f:SetTexCoord() end
  function f:SetDrawLayer() end
  function f:StartMoving() end
  function f:StopMovingOrSizing() end
  function f:CreateFontString(_, _, template)
    local child = CreateFrame("FontString", nil, self, template)
    table.insert(self._children, child)
    return child
  end
  function f:CreateTexture(_, _, template)
    local child = CreateFrame("Texture", nil, self, template)
    table.insert(self._children, child)
    return child
  end

  table.insert(__ALL_FRAMES, f)
  if name then
    _G[name] = f
    __FRAMES[name] = f
  end
  return f
end

UIParent = CreateFrame("Frame", "UIParent")
GameFontNormal = "GameFontNormal"
GameFontHighlight = "GameFontHighlight"
GameFontHighlightLarge = "GameFontHighlightLarge"
'''

LEGACY_LUA = r'''
function GetBuildInfo() return "1.15.9", "11509", "Jan 1 2026", 11509 end

__QUERIES = {}
__LEGACY_ROWS = {
  { name = "Item A", count = 1, buyout = 100, itemID = 101 },
  { name = "Item B", count = 1, buyout = 200, itemID = 102 },
  { name = "Item C", count = 20, buyout = 300, itemID = 103 },
}
__ITEMS = {
  [101] = { name = "Item A", classID = 2, maxStack = 1, equipLoc = "INVTYPE_WEAPON" },
  [102] = { name = "Item B", classID = 4, maxStack = 1, equipLoc = "INVTYPE_CHEST" },
  [103] = { name = "Item C", classID = 7, maxStack = 20, equipLoc = "" },
}

function QueryAuctionItems(name, minLevel, maxLevel, page)
  table.insert(__QUERIES, {
    name = tostring(name or ""),
    minLevel = tonumber(minLevel) or 0,
    maxLevel = tonumber(maxLevel) or 0,
    page = tonumber(page) or 0,
  })
  return true
end

function CanSendAuctionQuery() return true, 0 end

-- Deliberately returns TWO values. Tests must prove the add-on reads the
-- second one, not the first.
function GetNumAuctionItems(kind)
  if kind == "list" then return 1, #__LEGACY_ROWS end
  return 0, 0
end

-- Deliberately returns 17 values, with itemID in position 17.
function GetAuctionItemInfo(kind, index)
  local row = __LEGACY_ROWS[index]
  if not row then return nil end
  return row.name,
    "Interface\\Icons\\INV_Misc_QuestionMark",
    row.count, 2, false, 60, 60,
    row.buyout, 0, row.buyout, 0,
    nil, nil, 0, 0, 0, row.itemID
end

function GetItemInfo(item)
  local id = tonumber(item)
  if not id and type(item) == "string" then
    id = tonumber(item:match("item:(%d+)"))
  end
  local row = id and __ITEMS[id]
  if not row then return nil end
  local link = "|cffffffff|Hitem:" .. id .. "::::::::|h[" .. row.name .. "]|h|r"
  return row.name, link, 2, 60, 1, "Weapon", "Sword",
    row.maxStack, row.equipLoc, "Interface\\Icons\\INV_Misc_QuestionMark",
    10, row.classID
end

NUM_BAG_SLOTS = 4
NUM_REAGENTBAG_SLOTS = 0

function GetContainerNumSlots(bag)
  if tonumber(bag) == 0 then return 2 end
  return 0
end

function GetContainerItemID(bag, slot)
  if tonumber(bag) == 0 and tonumber(slot) == 1 then return 103 end
  return nil
end

function GetContainerItemLink(bag, slot)
  if tonumber(bag) == 0 and tonumber(slot) == 1 then
    return "|cffffffff|Hitem:103::::::::|h[Item C]|h|r"
  end
  return nil
end

-- Deliberately returns multiple values. The 2nd value is the stack count.
function GetContainerItemInfo(bag, slot)
  if tonumber(bag) == 0 and tonumber(slot) == 1 then
    return "Interface\\Icons\\INV_Misc_QuestionMark", 5, false, 2, false, false,
      "|cffffffff|Hitem:103::::::::|h[Item C]|h|r", false, false, 103
  end
  return nil
end

AuctionFrame = CreateFrame("Frame", "AuctionFrame")
AuctionFrame:Show()
'''

MODERN_LUA = r'''
function GetBuildInfo() return "1.60.1", "16001", "Jan 1 2026", 16001 end

__QUERIES = {}
__MODERN_ROWS = {
  { itemKey = { itemID = 201, itemLevel = 0, itemSuffix = 0, battlePetSpeciesID = 0 },
    quantity = 1, buyoutAmount = 100, auctionID = 5001 },
  { itemKey = { itemID = 202, itemLevel = 0, itemSuffix = 0, battlePetSpeciesID = 0 },
    quantity = 2, buyoutAmount = 250, auctionID = 5002 },
  { itemKey = { itemID = 203, itemLevel = 0, itemSuffix = 0, battlePetSpeciesID = 0 },
    quantity = 1, buyoutAmount = 400, auctionID = 5003 },
}
__ITEMS = {
  [201] = { name = "Modern Item A", classID = 2, maxStack = 1, equipLoc = "INVTYPE_WEAPON" },
  [202] = { name = "Modern Item B", classID = 4, maxStack = 1, equipLoc = "INVTYPE_CHEST" },
  [203] = { name = "Modern Item C", classID = 7, maxStack = 20, equipLoc = "" },
}

C_AuctionHouse = {}

function C_AuctionHouse.SendBrowseQuery(query)
  table.insert(__QUERIES, query or {})
end

-- Takes no index. Returns the whole table.
function C_AuctionHouse.GetBrowseResults() return __MODERN_ROWS end
function C_AuctionHouse.HasFullBrowseResults() return true end
function C_AuctionHouse.RequestMoreBrowseResults() end
function C_AuctionHouse.IsThrottled() return false end

function C_AuctionHouse.MakeItemKey(itemID, itemLevel, itemSuffix, battlePetSpeciesID)
  return {
    itemID = itemID,
    itemLevel = itemLevel or 0,
    itemSuffix = itemSuffix or 0,
    battlePetSpeciesID = battlePetSpeciesID or 0,
  }
end

function C_AuctionHouse.GetItemKeyInfo(key)
  if type(key) ~= "table" then return nil end
  return key.itemID, key.itemLevel, key.itemSuffix, key.battlePetSpeciesID
end

function C_AuctionHouse.SendSearchQuery() end
function C_AuctionHouse.GetNumItemSearchResults() return 0 end
function C_AuctionHouse.GetItemSearchResultInfo() return nil end
function C_AuctionHouse.CalculateCommodityDeposit() return 0 end
function C_AuctionHouse.CalculateItemDeposit() return 0 end

C_Item = {}
function C_Item.GetItemInfo(item)
  local id = tonumber(item)
  if not id and type(item) == "string" then
    id = tonumber(item:match("item:(%d+)"))
  end
  local row = id and __ITEMS[id]
  if not row then return nil end
  local link = "|cffffffff|Hitem:" .. id .. "::::::::|h[" .. row.name .. "]|h|r"
  return row.name, link, 2, 60, 1, "Weapon", "Sword",
    row.maxStack, row.equipLoc, "Interface\\Icons\\INV_Misc_QuestionMark",
    10, row.classID
end

C_Container = {}
NUM_BAG_SLOTS = 4
NUM_REAGENTBAG_SLOTS = 0

function C_Container.GetContainerNumSlots(bag)
  if tonumber(bag) == 0 then return 2 end
  return 0
end

function C_Container.GetContainerItemID(bag, slot)
  if tonumber(bag) == 0 and tonumber(slot) == 1 then return 203 end
  return nil
end

function C_Container.GetContainerItemLink(bag, slot)
  if tonumber(bag) == 0 and tonumber(slot) == 1 then
    return "|cffffffff|Hitem:203::::::::|h[Modern Item C]|h|r"
  end
  return nil
end

-- Deliberately returns an info table. The field is stackCount.
function C_Container.GetContainerItemInfo(bag, slot)
  if tonumber(bag) == 0 and tonumber(slot) == 1 then
    return {
      itemID = 203,
      stackCount = 5,
      itemLink = "|cffffffff|Hitem:203::::::::|h[Modern Item C]|h|r",
    }
  end
  return nil
end

AuctionHouseFrame = CreateFrame("Frame", "AuctionHouseFrame")
AuctionHouseFrame:Show()
'''


class WowRuntime:
    """One isolated Lua VM with a minimal WoW API surface."""

    def __init__(self, mode: str = "legacy", locale: str = "enUS"):
        if mode not in ("legacy", "modern"):
            raise ValueError(f"mode must be 'legacy' or 'modern', got {mode!r}")

        self.mode = mode
        self.L = lupa.LuaRuntime(unpack_returned_tuples=True)
        self.L.globals()["__LOCALE"] = locale
        self.L.execute(COMMON_LUA)
        self.L.execute(LEGACY_LUA if mode == "legacy" else MODERN_LUA)

    def fire(self, event: str, *args) -> int:
        """Dispatch an event to every frame that registered it.

        Returns the number of handlers called. A zero is meaningful: it proves
        the add-on did not register that event on this client.
        """
        frames = self.L.globals()["__ALL_FRAMES"]
        fired = 0
        for index in range(1, len(frames) + 1):
            frame = frames[index]
            events = frame["_events"]
            if events is not None and events[event]:
                handler = frame["_script_OnEvent"]
                if handler is not None:
                    handler(frame, event, *args)
                    fired += 1
        return fired

    def queries(self) -> list[dict]:
        """Return recorded browse queries as plain Python dicts."""
        rows = self.L.globals()["__QUERIES"]
        result = []
        for index in range(1, len(rows) + 1):
            result.append({key: value for key, value in rows[index].items()})
        return result

    def printed(self) -> list[str]:
        """Return chat lines printed by the add-on."""
        rows = self.L.globals()["__PRINTED"]
        return [str(rows[index]) for index in range(1, len(rows) + 1)]
