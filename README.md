# WoW Addon Harness · Classic

**人人都能做魔兽插件。 / Anyone can build WoW addons.**

A test-first development harness for World of Warcraft add-ons that must run on
both **Classic Era 1.15.x** (Interface `11509`, legacy Auction House) and a
**1.60.x modern Auction House client** (Interface `16001`).

One source tree. Two client flavors. No `if client then` branches in business code.

This is the dual-client tree: the legacy Auction House of Classic Era 1.15 and
the modern Auction House of the 1.60 client. It does not claim that Classic Era
uses the modern AH. The single-client Retail 12.x tree lives in the companion
repository.

> Building for **Retail 12.x** instead? That tree has a single modern client and
> lives in the companion repository, **wow-addon-harness-retail**.
>
> 如果你做的是**正式服 12.x**，请使用配套仓库 **wow-addon-harness-retail**。

[中文](#中文) · [English](#english)

---

## 中文

### 这是什么

这是一套“能被验证”的插件开发骨架，不是又一个空白模板。它把最容易出错的部分
收口成四条可执行的规则：

- **四层架构**：入口装配 / 适配层 / 数据层 / 表现层，每个文件只有一个归属。
- **双版本适配层**：只有 `Core/Env.lua` 允许出现两套客户端 API；业务代码只调用
  `ns.Env.*`，不再复制两套逻辑。
- **lupa 离线仿真**：不开游戏，按真实 `.toc` 顺序加载全部 Lua 文件，用最小 API
  mock 跑行为级测试，专抓 nil 崩溃、返回值形状错误和事件注册错误。
- **门禁 + 打包**：一条命令检查 toc、越层、版本、LF/BOM、敏感信息，并打出
  Legacy / Modern 两个安装包。

一句话分清：本仓是“老 AH + 现代 AH”的双客户端试验台。经典旧世 1.15 走老拍卖行，
1.60 客户端走现代拍卖行；正式服 12.x 的单客户端版本在 Retail 仓库。

### 为什么叫 Harness

Harness 是“试验台”。插件真正的风险不是语法错误，而是“看起来加载了，实际上没跑”：
事件注册错一侧、API 返回两个值却只接了一个、现代客户端根本没有 `AuctionFrame`。
这些问题在游戏里排查很慢，在试验台上几秒钟就能复现。

### 30 秒上手

```bash
python -m pip install lupa

# 跑行为级测试（Legacy + Modern 各一套）
python -m unittest discover -s tests -t . -v

# 跑仓库门禁
python tools/gate.py

# 打出两个安装包
python tools/package.py --flavor legacy --out dist
python tools/package.py --flavor modern --out dist
```

把 `dist/AHProbe-legacy/AHProbe` 或 `dist/AHProbe-modern/AHProbe` 放进对应客户端的
`Interface/AddOns/`，进游戏输入 `/ahprobe`。

### 目录

```text
addon/AHProbe/        最小示例插件（只读拍卖行浏览结果，不自动交易）
  Core/Init.lua       入口、环境探测、共享工具
  Core/Env.lua        唯一适配层（双版本 API 只允许出现在这里）
  Core/Probe.lua      数据层：发查询、读结果
  UI/Main.lua         表现层：建控件、转发点击
harness/              lupa 运行时、toc 加载器、WoW API mock
tests/                Legacy / Modern / 门禁 / 打包测试
tools/                gate.py（门禁）、package.py（分服打包）
docs/                 架构、API 映射、踩坑、工作流（中英双语）
AGENTS.md             给 AI Agent 的可执行规则（中英双语）
```

### 示例插件 AHProbe

只做一件事：拍卖行打开后点“扫描”，显示当前浏览结果的条数。它故意踩过三个真实坑：

1. Legacy `GetNumAuctionItems("list")` 返回**两个值**，只有第二个是总数。
2. Modern `C_AuctionHouse.GetBrowseResults()` **不接受索引**，直接返回整张表。
3. 现代客户端**没有** `AuctionFrame`，老客户端**没有** `C_AuctionHouse`。

它不自动购买、不自动上架、不模拟点击，只调用暴雪公开 API。你可以把它当最小起点，
替换成自己的功能。

### 四层架构

| 层 | 允许 | 禁止 |
| --- | --- | --- |
| 入口装配 | 命名空间、命令、事件装配、加载自检 | 业务计算、建业务控件 |
| 适配层 | 唯一允许原始双版本 API 与 `ns.MODERN_AH` 分支 | 业务决策（买不买、值不值） |
| 数据层 | 纯计算、存档读写、口径定义 | 直接碰 UI、直接碰原始 API |
| 表现层 | 建控件、渲染、转发点击、格式化 | 持有买入/上架原语、写业务判定 |

拿不准时问三句：换客户端会变吗？会 → 适配层。在算值不值/记不记？是 → 数据层。
在把它画出来/等玩家点？是 → 表现层。

详见 [`docs/architecture.md`](docs/architecture.md)。

### 双版本 API 映射

写任何涉及 API 的代码前，先查 [`docs/api-map.md`](docs/api-map.md)。表里每一条都对应
一次真实事故或真机实测，不是照抄通用文档。最重要的三条：

- 环境判据唯一入口：`ns.MODERN_AH`，业务层只问 `ns.Env.IsModern()`。
- 事件两侧互斥：在现代客户端注册老事件会直接中断初始化。
- 现代 API 不是“老 API 换了个名字”：返回结构、参数个数、宿主窗口都可能不同。

### 加一个新功能

1. 在 `docs/api-map.md` 找到要用的 API，确认两端的真实签名。
2. 判断落层：会随客户端变 → `Core/Env.lua` 加接口；纯计算 → `Core/*`；画界面 → `UI/*`。
3. 先改 `addon/AHProbe/`，再按需在 `tests/` 加一条行为测试。
4. 跑测试与门禁，确认两端都绿。
5. 打包两个 flavor，进游戏各验一次。

### 给第一次写插件的人

不需要先学完整个 WoW API。先让最小示例跑起来，再每次只改一个点：

- 改 UI 文案？只动 `UI/Main.lua`。
- 加一个查询条件？先看 `Core/Env.lua` 是否已有接口，再加测试。
- 换客户端报错？先跑 `tests/test_legacy.py` 和 `tests/test_modern.py`，看是哪一侧断了。

### 给 AI Agent

把 [`AGENTS.md`](AGENTS.md) 放在仓库根目录，Agent 会按同一套约束工作：先查 API 映射、
不越层、改完必跑测试与门禁、不把本机路径和账号信息写进仓库。

### 合规与免责声明

本项目只调用暴雪公开的客户端 API，示例不自动购买、不自动上架、不模拟点击。
使用前请阅读并遵守你所玩服务器与客户端的规则。本项目与 Blizzard Entertainment
无关联，不包含任何暴雪美术资源。

### License

MIT。见 [`LICENSE`](LICENSE)。

---

## English

### What this is

A development harness that can be **verified**, not another blank template. It
turns the error-prone parts of add-on development into four executable rules:

- **Four layers**: entry wiring / adapter / data / presentation. Every file has
  exactly one home.
- **Dual-client adapter**: only `Core/Env.lua` may contain the two client APIs.
  Business code calls `ns.Env.*` and never duplicates the same logic twice.
- **Offline simulation with lupa**: load every Lua file in real `.toc` order
  without launching the game. The minimal API mock catches nil crashes, wrong
  return shapes, and event-registration mistakes.
- **Gate + packaging**: one command checks the toc, layer leaks, version sync,
  LF/BOM, and sensitive strings, then builds Legacy and Modern packages.

### Why "harness"

A harness is a test bench. The real risk in add-on development is not a syntax
error; it is "it loaded, but it does not work": an event registered on the wrong
client, two return values treated as one, or `AuctionFrame` being assumed to
exist on a modern client. Those bugs are slow to debug in game and fast to
reproduce on a bench.

### Quick start

```bash
python -m pip install lupa

python -m unittest discover -s tests -t . -v
python tools/gate.py

python tools/package.py --flavor legacy --out dist
python tools/package.py --flavor modern --out dist
```

Copy `dist/AHProbe-legacy/AHProbe` or `dist/AHProbe-modern/AHProbe` into the
matching client's `Interface/AddOns/`, then type `/ahprobe` in game.

### The demo add-on

`AHProbe` does one thing: after the Auction House is open, click **Scan** and it
shows the number of current browse results. It deliberately demonstrates three
real pitfalls:

1. Legacy `GetNumAuctionItems("list")` returns **two values**; only the second
   one is the total.
2. Modern `C_AuctionHouse.GetBrowseResults()` takes **no index** and returns the
   whole table.
3. Modern clients have no `AuctionFrame`; legacy clients have no
   `C_AuctionHouse`.

It does not auto-buy, auto-list, or simulate clicks. It only calls public
Blizzard APIs. Use it as a minimal starting point and replace the behavior with
your own.

### Learn more

- [`docs/architecture.md`](docs/architecture.md) — four layers and placement rules
- [`docs/api-map.md`](docs/api-map.md) — verified Legacy / Modern API map
- [`docs/pitfalls.md`](docs/pitfalls.md) — the mistakes this harness exists to catch
- [`docs/workflow.md`](docs/workflow.md) — the day-to-day loop
- [`AGENTS.md`](AGENTS.md) — rules for AI coding agents

### Who this is for

First-time add-on authors, returning players, tool builders, and AI agents. You
do not need to learn the entire WoW API first. Get the demo running, then change
one small thing at a time.

### Compliance

This project only calls public Blizzard client APIs. The demo does not auto-buy,
auto-list, or simulate clicks. Follow the rules of the server and client you use.
This project is not affiliated with Blizzard Entertainment and contains no
Blizzard art assets.

### License

MIT. See [`LICENSE`](LICENSE).
