# Architecture / 架构

> **EN TL;DR** — Four layers. Only the adapter layer knows which client you are
> on. Business code calls `ns.Env.*`. The UI renders; the data layer calculates;
> the entry layer wires. Every file has exactly one home.
>
> **中文摘要** — 四层：入口装配 / 适配层 / 数据层 / 表现层。只有适配层知道当前是
> 哪个客户端，业务代码只调用 `ns.Env.*`。UI 负责画，数据层负责算，入口层负责接线。
> 每个文件只有一个归属。

## English

### The four layers

| Layer | Allowed | Forbidden | Files in this demo |
| --- | --- | --- | --- |
| Entry wiring | namespace, slash commands, event wiring, load-time self-check | business math, building business widgets | `Core/Init.lua`, `UI/Main.lua` (loader block) |
| Adapter | the **only** place for raw dual-client APIs and `ns.MODERN_AH`; returns normalized data | business decisions (should I buy? is it worth it?) | `Core/Env.lua` |
| Data | pure calculations, saved-variable reads/writes, definitions | touching UI or raw client APIs | `Core/Probe.lua` |
| Presentation | widgets, rendering, forwarding clicks, formatting | holding buy/list primitives, writing business rules | `UI/Main.lua` |

### Three placement questions

1. Would this code change if we switched clients? **Yes → adapter.**
2. Is it calculating, deciding, or recording? **Yes → data.**
3. Is it drawing something or waiting for a click? **Yes → presentation.**
4. None of the above? The requirement is not decomposed enough. Split it first.

### Load order

`AHProbe.toc` order is dependency order. `Init` must run before `Env`; `Env`
before anything that calls it; `Probe` before the UI that reads it. A file that
is not in the toc is not loaded, and a value that is read too early is `nil`
forever.

When adding a file, update three places:

1. `AHProbe.toc` — between its dependencies and its dependents.
2. The test loader — it reads the toc, so no hand-written list is needed.
3. The expected file list in `tests/test_legacy.py`.

### Why not one big file

The demo is small on purpose, but the failure mode is the same at any size:
when two clients are mixed into business code, every change risks breaking the
other client. The adapter makes the difference explicit and testable.

## 中文

### 四层模型

| 层 | 允许 | 禁止 | 本示例中的文件 |
| --- | --- | --- | --- |
| 入口装配 | 命名空间、斜杠命令、事件装配、加载期自检 | 业务计算、建业务控件 | `Core/Init.lua`、`UI/Main.lua` 的 loader 段 |
| 适配层 | **唯一**允许原始双客户端 API 与 `ns.MODERN_AH` 的地方；对外只吐统一结构 | 业务决策（买不买、值不值） | `Core/Env.lua` |
| 数据层 | 纯计算、存档读写、口径定义 | 直接碰 UI、直接碰原始 API | `Core/Probe.lua` |
| 表现层 | 建控件、渲染、转发点击、格式化 | 持有买入/上架原语、写业务判定 | `UI/Main.lua` |

### 落层三问

1. 这段代码换到另一个客户端会不会变？**会 → 适配层。**
2. 它是在算、在判、在记吗？**是 → 数据层。**
3. 它是在画出来、在等玩家点吗？**是 → 表现层。**
4. 三句都答不上？说明需求拆得不够，先拆需求，再写代码。

### 加载顺序

`AHProbe.toc` 的顺序就是依赖顺序。`Init` 必须在 `Env` 之前，`Env` 必须在所有
调用它的文件之前，`Probe` 必须在读取它的 UI 之前。没进 toc 的文件不会被加载；
读得太早的值永远是 `nil`。

新增文件时同步三处：

1. `AHProbe.toc` —— 放在“它依赖的”之后、“依赖它的”之前。
2. 测试加载器 —— 它直接读 toc，不需要手写清单。
3. `tests/test_legacy.py` 里的期望文件清单。

### 为什么不做成一个大文件

示例很小，但失败模式与大型插件相同：两套客户端逻辑混进业务代码后，每次改动都可能
让另一侧回归。适配层把差异显式化，也让差异变得可测试。
