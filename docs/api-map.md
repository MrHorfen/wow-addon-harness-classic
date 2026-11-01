# API Map / API 映射

> **Baseline / 基线** — Legacy = Classic Era 1.15.x (Interface `11509`).
> Modern = 1.60.x client (Interface `16001`). Always probe at runtime with
> `Env.Has()`; paper APIs lie.
>
> **原则** — 写任何涉及 API 的代码前，先在本表找到那一行。表里的“坑”都对应一次
> 真实事故或真机实测，不是从通用文档推断的。

## 1. Client / 客户端

| Capability | Legacy 1.15 | Modern 1.60 | Adapter | Pitfall |
| --- | --- | --- | --- | --- |
| Which client? | `QueryAuctionItems == nil` | `C_AuctionHouse ~= nil` | `ns.MODERN_AH` → `Env.IsModern()` | Never recreate this test in business code |
| AH host frame | `AuctionFrame` | `AuctionHouseFrame` | `ns.GetAHFrame()` | Modern clients have no `AuctionFrame` |
| AH open? | host `:IsShown()` | host `:IsShown()` | `ns.IsAuctionOpen()` | Never hard-code the host name |
| Capability probe | — | — | `Env.Has("C_AuctionHouse.X")` | The two modern clients are not identical |

## 2. Browse / 浏览查询

| Capability | Legacy 1.15 | Modern 1.60 | Adapter | Pitfall |
| --- | --- | --- | --- | --- |
| Send query | `QueryAuctionItems(name, minL, maxL, page, ...)` | `C_AuctionHouse.SendBrowseQuery(queryTable)` | `Env.QueryBrowse()` | Results arrive by event, not return value |
| Throttle | `CanSendAuctionQuery()` (2nd return = cooldown) | `C_AuctionHouse.IsThrottled()` | Check before sending | A long cooldown is normal on legacy |
| Result count | `GetNumAuctionItems("list")` → **two values** (page, total) | `#C_AuctionHouse.GetBrowseResults()` | `Env.GetBrowseCount()` | `tonumber()` on the call uses the first value |
| Result rows | `GetAuctionItemInfo("list", i)` → 17 values | `C_AuctionHouse.GetBrowseResults()` → whole table | Read via adapter | Modern takes **no index** |
| More results | — | `HasFullBrowseResults`, `CanRequestMoreBrowseResults`, `RequestMoreBrowseResults` | Adapter | Do not assume all pages arrived |

## 3. Events / 事件

| Capability | Legacy 1.15 | Modern 1.60 | Adapter |
| --- | --- | --- | --- |
| Browse results | `AUCTION_ITEM_LIST_UPDATE` | `AUCTION_HOUSE_BROWSE_RESULTS_UPDATED`, `_ADDED`, `_FAILURE` | `Env.RegisterAHEvents(frame, "browse")` |
| Item search | — | `ITEM_SEARCH_RESULTS_UPDATED` | `"item"` |
| Commodity purchase | — | `COMMODITY_PRICE_UPDATED`, `_UNAVAILABLE`, `COMMODITY_PURCHASE_SUCCEEDED`, `_FAILED` | `"commodity"` |
| AH open/close | `AUCTION_HOUSE_SHOW`, `AUCTION_HOUSE_CLOSED` | same | `"ah"` |

The two sides are **mutually exclusive**. Registering a legacy event on a modern
client throws `unknown event` and aborts initialization. Register only the side
you are on, and wrap each registration in `pcall`.

## 4. Items / 物品

| Capability | Legacy 1.15 | Modern 1.60 | Adapter | Pitfall |
| --- | --- | --- | --- | --- |
| Item info | `GetItemInfo(id)` | `C_Item.GetItemInfo(id)` | `ns.GetItemInfoSafe()` | Cold cache returns `nil`; that is normal |
| Item name | same | `C_Item.GetItemNameByID(id)` fallback | `Env.ItemName()` | Do not use a name as a filter |
| Max stack | return 8 | return 8 | `ns.ItemMaxStack()` | `> 1` = commodity, `== 1` = unique item |
| Class ID | return **12** | return **12** | `Env.ItemClassID()` | Return 11 is vendor price, not classID |
| Equip location | return 9 | return 9 | `Env.ItemEquipLoc()` | Empty string is valid for non-equipment |

## 5. Bags / 背包

| Capability | Legacy 1.15 | Modern 1.60 | Adapter |
| --- | --- | --- | --- |
| Slot count | `GetContainerNumSlots(bag)` | `C_Container.GetContainerNumSlots(bag)` | `Env.BagNumSlots()` |
| Item ID | `GetContainerItemID(bag, slot)` | `C_Container.GetContainerItemID(...)` | `Env.BagItemID()` |
| Item info | `GetContainerItemInfo(...)` → multiple returns | `C_Container.GetContainerItemInfo(...)` → info table | `Env.BagItemInfo()` |
| Item link | `GetContainerItemLink(...)` | `C_Container.GetContainerItemLink(...)` | `Env.BagItemInfo().link` |

`C_Container` must be fetched at **call time**, not captured at file load time.
The offline harness installs the API after the add-on loads; a top-of-file
capture becomes `nil` forever.

## 6. Trading actions (not used by the demo) / 交易动作（示例未使用）

The demo is read-only on purpose. If you add trading, these are the verified
shapes to start from; they still need real-client testing.

| Capability | Legacy 1.15 | Modern 1.60 | Adapter |
| --- | --- | --- | --- |
| Bid / buy item | `PlaceAuctionBid("list", index, price)` | `C_AuctionHouse.PlaceBid(auctionID, buyoutAmount)` | Buy layer |
| Buy commodity | same as above (buyout) | `StartCommoditiesPurchase(itemID, qty)` → `ConfirmCommoditiesPurchase(itemID, qty)` → `CancelCommoditiesPurchase()` | Buy layer |
| Post auction | `PostAuction(bid, buyout, duration, stack, count)` | `C_AuctionHouse.PostCommodity(...)` | Sell layer |
| Available posts | — | `C_AuctionHouse.GetAvailablePostCount` | Sell layer |
| Item key | — | `MakeItemKey(itemID, itemLevel, itemSuffix, battlePetSpeciesID)` | Modern only |

Two warnings:

- The first argument of `StartCommoditiesPurchase` is an **itemID number**, not
  an `itemKey` table.
- Purchase confirmation must run inside the client's real click stack. A
  self-drawn button that directly calls the purchase API can be silently
  discarded by the server. Use the native dialog/menu, and verify the result,
  not just the button state.

## 7. Return-shape cheat sheet / 返回值速查

```lua
-- Legacy: two values. Capture the second one.
local ok, pageCount, totalCount = pcall(GetNumAuctionItems, "list")

-- Modern: one table. Do not pass an index.
local ok, rows = pcall(C_AuctionHouse.GetBrowseResults)

-- Legacy container info: multiple returns; the 2nd value is the stack count.
-- Modern container info: a table with a stackCount field.
```

If a function's return shape changes between clients, that is an adapter
responsibility, not a business-layer `if`.
