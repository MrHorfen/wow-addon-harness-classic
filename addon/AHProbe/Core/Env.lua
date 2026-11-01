--[[
  AHProbe / Core/Env.lua

  The only business-facing adapter. It translates two very different clients
  into one small set of functions:

    Env.IsModern()       legacy or modern?
    Env.QueryBrowse()    send a browse query
    Env.GetBrowseCount() read the result count safely
    Env.RegisterAHEvents register only the events this client actually has

  Rules:
    1. Raw dual-client APIs and ns.MODERN_AH belong here (and in Init).
    2. No business decisions in this file: no "should I buy this?", no pricing.
    3. Every external API call is wrapped in pcall. A missing API is normal.
]]

local ADDON_NAME, ns = ...

local Env = {}
ns.Env = Env

-- Event names are mutually exclusive between the two clients.
-- Registering a legacy event on a modern client is not a no-op: it aborts
-- initialization with "unknown event" and the add-on appears broken.
local AH_EVENTS = {
  browse = {
    legacy = { "AUCTION_ITEM_LIST_UPDATE" },
    modern = {
      "AUCTION_HOUSE_BROWSE_RESULTS_UPDATED",
      "AUCTION_HOUSE_BROWSE_RESULTS_ADDED",
      "AUCTION_HOUSE_BROWSE_FAILURE",
    },
  },
  ah = {
    legacy = { "AUCTION_HOUSE_SHOW", "AUCTION_HOUSE_CLOSED" },
    modern = { "AUCTION_HOUSE_SHOW", "AUCTION_HOUSE_CLOSED" },
  },
}

local function IsModern()
  return (ns.MODERN_AH and true) or false
end

local function Call1(fn, ...)
  if type(fn) ~= "function" then
    return nil
  end
  local ok, value = pcall(fn, ...)
  if ok then
    return value
  end
  return nil
end

-- C_Container must be fetched at call time. Capturing it at file load time
-- makes the offline harness see nil forever.
local function CC()
  return (type(_G.C_Container) == "table") and _G.C_Container or nil
end

-- Prefer the modern namespace, fall back to the legacy global.
local function Pick(modernName, legacyName)
  local cc = CC()
  if cc and type(cc[modernName]) == "function" then
    return cc[modernName]
  end
  if type(_G[legacyName]) == "function" then
    return _G[legacyName]
  end
  return nil
end

function Env.IsModern()
  return IsModern()
end

function Env.Flavor()
  return IsModern() and "modern" or "legacy"
end

-- Runtime capability probe. Supports dotted paths:
--   Env.Has("C_AuctionHouse.SendBrowseQuery")
function Env.Has(path)
  if type(path) ~= "string" or path == "" then
    return false
  end
  local node = _G
  for part in path:gmatch("[^%.]+") do
    if type(node) ~= "table" then
      return false
    end
    node = node[part]
    if node == nil then
      return false
    end
  end
  return true
end

-- ---------------------------------------------------------------------------
-- Bags / 背包
-- ---------------------------------------------------------------------------

function Env.BagCount()
  local count = (type(_G.NUM_BAG_SLOTS) == "number") and _G.NUM_BAG_SLOTS or 4
  if type(_G.NUM_REAGENTBAG_SLOTS) == "number" then
    count = count + _G.NUM_REAGENTBAG_SLOTS
  end
  if count < 5 then
    count = 5
  end
  return count
end

function Env.BagNumSlots(bag)
  bag = tonumber(bag)
  if not bag then
    return 0
  end
  return tonumber(Call1(Pick("GetContainerNumSlots", "GetContainerNumSlots"), bag)) or 0
end

function Env.BagItemID(bag, slot)
  bag, slot = tonumber(bag), tonumber(slot)
  if not bag or not slot then
    return nil
  end
  local id = tonumber(Call1(Pick("GetContainerItemID", "GetContainerItemID"), bag, slot))
  if id then
    return id
  end
  local link = Call1(Pick("GetContainerItemLink", "GetContainerItemLink"), bag, slot)
  if type(link) == "string" then
    return tonumber(link:match("item:(%d+)"))
  end
  return nil
end

-- Normalise both return shapes to { itemID, stackCount, link }.
-- Legacy: multiple returns, the 2nd value is the stack count.
-- Modern: an info table with a stackCount field.
function Env.BagItemInfo(bag, slot)
  bag, slot = tonumber(bag), tonumber(slot)
  if not bag or not slot then
    return nil
  end

  local cc = CC()
  if cc and type(cc.GetContainerItemInfo) == "function" then
    local ok, info = pcall(cc.GetContainerItemInfo, bag, slot)
    if ok and type(info) == "table" then
      local id = tonumber(info.itemID) or Env.BagItemID(bag, slot)
      if id then
        return {
          itemID = id,
          stackCount = tonumber(info.stackCount) or 1,
          link = info.itemLink or info.link,
        }
      end
    end
  end

  if type(_G.GetContainerItemInfo) == "function" then
    local ok, _texture, count, _locked, _quality, _readable, _lootable,
          link, _filtered, _noValue, itemID = pcall(_G.GetContainerItemInfo, bag, slot)
    if ok then
      local id = tonumber(itemID) or Env.BagItemID(bag, slot)
      if id then
        return {
          itemID = id,
          stackCount = tonumber(count) or 1,
          link = (type(link) == "string") and link or nil,
        }
      end
    end
  end

  return nil
end

function Env.ForEachBagSlot(fn)
  if fn == nil then
    return 0
  end
  local visited = 0
  for bag = 0, Env.BagCount() do
    local slots = Env.BagNumSlots(bag)
    for slot = 1, slots do
      local info = Env.BagItemInfo(bag, slot)
      if info then
        visited = visited + 1
        fn(bag, slot, info.itemID, info.stackCount, info.link)
      end
    end
  end
  return visited
end

-- ---------------------------------------------------------------------------
-- Items / 物品
-- ---------------------------------------------------------------------------

function Env.ItemInfo(item)
  return ns.GetItemInfoSafe(item)
end

function Env.ItemID(item)
  local id = tonumber(item)
  if id then
    return id
  end
  if type(item) == "string" then
    return tonumber(item:match("item:(%d+)"))
  end
  return nil
end

function Env.ItemName(item)
  local name = ns.GetItemInfoSafe(item)
  return name
end

function Env.ItemMaxStack(item)
  return ns.ItemMaxStack(item)
end

function Env.ItemClassID(item)
  local _, _, raw = ns.GetItemInfoSafe(item)
  return tonumber(raw and raw[12])
end

function Env.ItemEquipLoc(item)
  local _, _, raw = ns.GetItemInfoSafe(item)
  local value = raw and raw[9]
  return (type(value) == "string") and value or nil
end

-- ---------------------------------------------------------------------------
-- Auction House / 拍卖行
-- ---------------------------------------------------------------------------

function Env.AHFrame()
  return ns.GetAHFrame()
end

function Env.IsAuctionOpen()
  return ns.IsAuctionOpen()
end

-- Send a browse query. The two clients return nothing useful here; the result
-- arrives through an event. Always check the boolean before waiting for it.
function Env.QueryBrowse()
  if IsModern() then
    local ah = _G.C_AuctionHouse
    if type(ah) ~= "table" or type(ah.SendBrowseQuery) ~= "function" then
      return false, "C_AuctionHouse.SendBrowseQuery is missing"
    end
    local ok, err = pcall(ah.SendBrowseQuery, {})
    if not ok then
      return false, tostring(err)
    end
    return true
  end

  if type(_G.QueryAuctionItems) ~= "function" then
    return false, "QueryAuctionItems is missing"
  end
  local ok, err = pcall(_G.QueryAuctionItems, "", 0, 0, 0)
  if not ok then
    return false, tostring(err)
  end
  return true
end

-- Read the number of rows in the current browse result.
--
-- Legacy pitfall: GetNumAuctionItems("list") returns TWO values
-- (page count, total count). Capturing only the first is correct.
-- Modern pitfall: GetBrowseResults() takes no index and returns the whole table.
function Env.GetBrowseCount()
  if IsModern() then
    local ah = _G.C_AuctionHouse
    if type(ah) ~= "table" or type(ah.GetBrowseResults) ~= "function" then
      return 0
    end
    local ok, rows = pcall(ah.GetBrowseResults)
    if ok and type(rows) == "table" then
      return #rows
    end
    return 0
  end

  if type(_G.GetNumAuctionItems) ~= "function" then
    return 0
  end
  local ok, _pageCount, totalCount = pcall(_G.GetNumAuctionItems, "list")
  if ok then
    return tonumber(totalCount) or 0
  end
  return 0
end

-- Register only the events that exist on this client.
-- Returns the number of successful registrations; 0 means "not available".
function Env.RegisterAHEvents(frame, set)
  if type(frame) ~= "table" or type(frame.RegisterEvent) ~= "function" then
    return 0
  end
  local definition = AH_EVENTS[set]
  if not definition then
    return 0
  end

  local list = IsModern() and definition.modern or definition.legacy
  local count = 0
  for i = 1, #list do
    if pcall(frame.RegisterEvent, frame, list[i]) then
      count = count + 1
    end
  end
  return count
end

-- Create a hidden event frame. Missing individual events are skipped, never
-- allowed to abort the whole initialization.
function Env.NewEventFrame(events)
  local frame = _G.CreateFrame("Frame")
  if type(events) == "table" then
    for i = 1, #events do
      pcall(frame.RegisterEvent, frame, events[i])
    end
  end
  return frame
end
