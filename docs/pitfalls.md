# Pitfalls / 踩坑清单

> **EN TL;DR** — Most add-on bugs are not syntax errors. They are wrong return
> shapes, wrong event sides, wrong host frames, and mocks that are nicer than
> the real client. This page lists the mistakes the harness is designed to
> catch.
>
> **中文摘要** — 插件 bug 大多不是语法错误，而是返回值形状、事件侧、宿主窗口，
> 以及“比真机更宽松”的夹具。下面这些坑，试验台就是为它们准备的。

## English

1. **`GetNumAuctionItems("list")` returns two values.** The first is the page
   count, the second is the total. Capturing only the first silently reports the
   wrong number.

2. **`C_AuctionHouse.GetBrowseResults()` takes no index.** It returns the whole
   table. `GetBrowseResults(i)` is a paper API that does not exist on the real
   client.

3. **Modern clients have no `AuctionFrame`.** The host is `AuctionHouseFrame`.
   Hard-coding the legacy name makes the add-on claim the AH is closed even when
   it is open.

4. **Event sides are mutually exclusive.** Registering `AUCTION_ITEM_LIST_UPDATE`
   on a modern client throws `unknown event` and aborts initialization. The
   add-on looks "loaded but dead".

5. **`C_Container` must be fetched at call time.** Capturing it at file load
   time is `nil` in the offline harness and can be `nil` during early load in
   game. Fetch inside the function.

6. **Container info has two shapes.** Legacy returns multiple values; modern
   returns an info table with `stackCount`. Normalize in the adapter.

7. **Item info indexes are easy to swap.** Return 11 is the vendor price,
   return 12 is `classID`. Getting this wrong misclassifies items.

8. **`maxStack > 1` is the commodity test.** Do not use `isCommodity`; an
   aggregated gear row can be misclassified as a commodity.

9. **A commodity purchase starts with an itemID, not an itemKey.** Passing a
   table where a number is expected is a common paper-API mistake.

10. **Purchase confirmation must be in the real click stack.** A self-drawn
    button that directly calls the purchase API can be silently dropped. Use the
    native dialog/menu and verify the result.

11. **"The button changed color" is not "the purchase succeeded".** Confirm from
    the server response or the ledger, not from local UI state.

12. **A mock that is nicer than the client hides bugs.** If the mock adds a
    method the real client does not have, the test can pass while the game
    fails. Only mock methods you have verified.

13. **lupa runs Lua 5.5; the game runs Lua 5.1.** Add the shim
    `unpack = unpack or table.unpack` before loading anything.

14. **Load the full `.toc`, not a hand-written file list.** A file missing from
    the test list is a file whose bugs are invisible.

15. **A cold item cache returns `nil`.** That is normal. Do not use a name as a
    hard filter; use item IDs where possible.

## 中文

1. **`GetNumAuctionItems("list")` 返回两个值。** 第一个是页数，第二个才是总数。
   只接第一个，数量会静默报错。

2. **`C_AuctionHouse.GetBrowseResults()` 不接受索引。** 它直接返回整张表。
   `GetBrowseResults(i)` 是纸面 API，真机不存在。

3. **现代客户端没有 `AuctionFrame`。** 宿主是 `AuctionHouseFrame`。写死老名字，
   拍卖行明明开着也会被判成“没开”。

4. **事件两侧互斥。** 在现代客户端注册 `AUCTION_ITEM_LIST_UPDATE` 会报
   `unknown event` 并中断初始化，表现是“插件加载了但整个不能用”。

5. **`C_Container` 必须在函数体内取。** 文件顶部捕获，在离线夹具里永远是 `nil`；
   游戏里过早加载也可能拿不到。调用时再取。

6. **背包信息有两种形状。** 老版返回多值，新版返回带 `stackCount` 的表。
   在适配层归一化，别让业务层自己分辨。

7. **物品信息的下标很容易错。** 第 11 项是卖店价，第 12 项才是 `classID`。
   取错会把物品分错类。

8. **`maxStack > 1` 才是商品判据。** 不要用 `isCommodity`；聚合后的装备行会被
   误判成商品。

9. **商品购买的第一个参数是 itemID，不是 itemKey。** 该传数字的地方传表，
   是典型的“照抄纸面文档”错误。

10. **购买确认必须在真实点击栈内。** 自绘按钮直接调购买 API，可能被服务器静默
    丢弃。用原生对话框/菜单，并校验结果。

11. **“按钮变色了”不等于“买到了”。** 以服务端回执或账本为准，不以本地 UI 状态为准。

12. **比真机更宽松的夹具会藏 bug。** 夹具里多一个真机没有的方法，测试会绿、游戏会炸。
    只 mock 你核实过的方法。

13. **lupa 跑 Lua 5.5，游戏跑 Lua 5.1。** 加载任何东西之前先垫
    `unpack = unpack or table.unpack`。

14. **按完整 `.toc` 加载，不要手写文件清单。** 测试清单里漏掉的文件，它的 bug
    就是隐形的。

15. **物品缓存冷启动返回 `nil` 是正常的。** 不要拿名字当硬过滤条件；能用 itemID
    就用 itemID。
