--[[
  AHProbe / Core/Init.lua

  Entry point. Detects the client flavor once and exposes the few helpers that
  every layer shares. Only this file and Core/Env.lua may touch raw client APIs.

  Detected flavors:
    legacy  Classic Era 1.15.x, old AuctionFrame API
    modern  1.60.x client, C_AuctionHouse API
]]

local ADDON_NAME, ns = ...

ns.VERSION = "0.1.0"
ns.DISPLAY = "AH Probe"

-- Single source of truth for "which client am I on?".
-- Never recreate this test in business code: call ns.Env.IsModern().
ns.MODERN_AH = (type(_G.QueryAuctionItems) ~= "function"
  and type(_G.C_AuctionHouse) == "table") and true or false
ns.FLAVOR = ns.MODERN_AH and "modern" or "legacy"

-- Debug handle for the offline harness. Harmless in game.
_G.AHProbeNS = ns

-- Minimal localization. Add another table if you need more languages.
ns.L = {
  enUS = {
    TITLE = "AH Probe",
    MODE = "Mode",
    AUCTIONS = "Auctions",
    SCAN = "Scan",
    OPEN_AH = "Open the auction house first.",
    QUERY_SENT = "Browse query sent (%s).",
    QUERY_FAILED = "Query failed: %s",
    LEGACY = "Legacy",
    MODERN = "Modern",
  },
  zhCN = {
    TITLE = "拍卖行探针",
    MODE = "模式",
    AUCTIONS = "拍卖行条目",
    SCAN = "扫描",
    OPEN_AH = "请先打开拍卖行。",
    QUERY_SENT = "已发出浏览查询（%s）。",
    QUERY_FAILED = "查询失败：%s",
    LEGACY = "经典",
    MODERN = "现代",
  },
}

function ns.Lang(key)
  local locale = (type(_G.GetLocale) == "function" and _G.GetLocale()) or "enUS"
  local pack = (locale == "zhCN" or locale == "zhTW") and ns.L.zhCN or ns.L.enUS
  return pack[key] or ns.L.enUS[key] or key
end

function ns.Print(message)
  if _G.DEFAULT_CHAT_FRAME and _G.DEFAULT_CHAT_FRAME.AddMessage then
    _G.DEFAULT_CHAT_FRAME:AddMessage(
      "|cff00ff96" .. ns.DISPLAY .. "|r " .. tostring(message)
    )
  end
end

-- Old and new clients use different Auction House host frames.
-- Hard-coding AuctionFrame makes the add-on unusable on modern clients.
function ns.GetAHFrame()
  if ns.MODERN_AH then
    return _G.AuctionHouseFrame
  end
  return _G.AuctionFrame
end

function ns.IsAuctionOpen()
  local frame = ns.GetAHFrame()
  if not frame or type(frame.IsShown) ~= "function" then
    return false
  end
  local ok, shown = pcall(frame.IsShown, frame)
  return (ok and shown) and true or false
end

-- Returns name, link, raw[1..12].
-- raw[8] = maxStack, raw[11] = vendor price, raw[12] = classID.
-- These indexes are easy to get wrong; do not guess them.
function ns.GetItemInfoSafe(item)
  local fn = (_G.C_Item and _G.C_Item.GetItemInfo) or _G.GetItemInfo
  if type(fn) ~= "function" then
    return nil
  end

  local ok, name, link, quality, ilvl, reqLevel, class, subclass,
        maxStack, equipLoc, icon, vendorPrice, classID = pcall(fn, item)
  if not ok or name == nil then
    return nil
  end

  local raw = {
    name, link, quality, ilvl, reqLevel, class, subclass,
    maxStack, equipLoc, icon, vendorPrice, classID,
  }
  return name, link, raw
end

-- maxStack > 1 means "commodity"; == 1 means "unique item" (gear, pets, etc.).
function ns.ItemMaxStack(item)
  local _, _, raw = ns.GetItemInfoSafe(item)
  return tonumber(raw and raw[8]) or 1
end
