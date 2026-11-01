# Workflow / 工作流

> **EN TL;DR** — Read the API map, change one layer, add a behavior test, run
> both client suites, run the gate, package both flavors, verify in game.
>
> **中文摘要** — 先查 API 映射，一次只改一层，补一条行为测试，跑两端测试与门禁，
> 打两个包，再进游戏验证。

## English

### Setup

```bash
python -m pip install lupa
```

Python 3.11+ is recommended. The harness uses `lupa` to embed Lua 5.5.

### The loop

```bash
# 1. Behavior tests: legacy and modern
python -m unittest discover -s tests -t . -v

# 2. Repository gate
python tools/gate.py

# 3. Build installable folders
python tools/package.py --flavor legacy --out dist
python tools/package.py --flavor modern --out dist
```

### Continuous integration

`docs/ci.yml` contains a ready-to-use GitHub Actions workflow. Copy it to
`.github/workflows/ci.yml` and push with a token that has the `workflow` scope.

### Adding a feature

1. Find the API in `docs/api-map.md`. If it is not there, verify it on the real
   client before writing code.
2. Decide the layer with the three questions in `docs/architecture.md`.
3. If the API differs by client, add one normalized function to `Core/Env.lua`
   first. Do not add an `if` to the business layer.
4. Change the data layer, then the UI. Keep UI free of purchase/list primitives.
5. Add a behavior test: call the function, fire the event, read the result.
6. Run both suites, the gate, and both packages.

### Adding a file

- Add it to `AHProbe.toc` in dependency order.
- Add it to the expected list in `tests/test_legacy.py`.
- The package script follows the toc automatically.

### Adding a client

This repository is intentionally two-flavor. If you need a third flavor:

1. Add a new `ns.FLAVOR` branch in `Core/Init.lua`.
2. Add the new API/event set to `Core/Env.lua`.
3. Add a new `WowRuntime` mode and a test file.
4. Add a package flavor in `tools/package.py`.

If the third flavor starts to make `Env.lua` unreadable, split it into
`Env/<flavor>.lua` behind the same public interface. Do not leak the branch into
business code.

### Release checklist

- [ ] Both test suites pass.
- [ ] Gate passes.
- [ ] Both packages build.
- [ ] The package loads in the matching client.
- [ ] `/ahprobe` opens the panel and `Scan` updates the count.
- [ ] No new absolute paths, account names, tokens, logs, or SavedVariables.

## 中文

### 环境

```bash
python -m pip install lupa
```

建议 Python 3.11+。Harness 用 `lupa` 内嵌 Lua 5.5。

### 日常闭环

```bash
# 1. 行为测试：Legacy + Modern
python -m unittest discover -s tests -t . -v

# 2. 仓库门禁
python tools/gate.py

# 3. 打安装包
python tools/package.py --flavor legacy --out dist
python tools/package.py --flavor modern --out dist
```

### 持续集成

`docs/ci.yml` 是一份可直接使用的 GitHub Actions 工作流。复制到
`.github/workflows/ci.yml`，用带 `workflow` 权限的 token 推送即可启用。

### 加一个功能

1. 在 `docs/api-map.md` 找到 API；表里没有，就先去真机核实，再写代码。
2. 用 `docs/architecture.md` 的三问判断落层。
3. 如果 API 分客户端，先在 `Core/Env.lua` 加一个归一化函数，不要往业务层加 `if`。
4. 先改数据层，再改 UI；UI 不持有买入/上架原语。
5. 补一条行为测试：调用函数、触发事件、读回结果。
6. 跑两套测试、门禁、两个打包。

### 新增文件

- 按依赖顺序加入 `AHProbe.toc`。
- 同步 `tests/test_legacy.py` 的期望清单。
- 打包脚本自动跟随 toc，不需要另改。

### 新增客户端

本仓刻意只做两个 flavor。如果确实要加第三个：

1. 在 `Core/Init.lua` 增加 `ns.FLAVOR` 分支。
2. 在 `Core/Env.lua` 增加对应的 API/事件集合。
3. 增加一个 `WowRuntime` 模式和一份测试。
4. 在 `tools/package.py` 增加打包 flavor。

如果第三个 flavor 让 `Env.lua` 难以阅读，就按同一套公开接口拆成
`Env/<flavor>.lua`。分支不许漏进业务层。

### 发布前检查

- [ ] 两套测试通过。
- [ ] 门禁通过。
- [ ] 两个包都能打出来。
- [ ] 包能在对应客户端加载。
- [ ] `/ahprobe` 能打开面板，`Scan` 能更新数量。
- [ ] 没有新增绝对路径、账号名、token、日志或存档。
