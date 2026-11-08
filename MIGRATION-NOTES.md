# AegisHarness 改造说明

本仓库是公司标准研发工具 **AegisHarness**，由 Apache-2.0 上游项目派生并重构。
本文说明改了什么、如何验证、哪些能力有边界、发布前还需做什么。

---

## 1. 品牌与标识

全仓（代码、配置、命令、文档、目录名、文件名）统一改名，**产品侧已无上游品牌标识**：

| 上游 | 公司标准 |
| --- | --- |
| `HelixHarness` / `helixharness` / `HELIXHARNESS` | `AegisHarness` / `aegisharness` / `AEGISHARNESS` |
| 命令 `/helix:*`、插件 ID `helix@...` | `/aegis:*`、`aegis@aegisharness-marketplace` |
| `helixharness.workspace.yaml`、`~/.helixharness/` | `aegisharness.workspace.yaml`、`~/.aegisharness/` |
| 环境变量 `HELIXHARNESS_*` | `AEGISHARNESS_*` |
| `github.com/didi/helixharness` | `github.com/elierncn/aegisharness` |
| 目录 `helixharness/`、`helixharness-platform/` | `aegisharness/`、`aegisharness-platform/` |

品牌叙事重写为"Aegis = 守护之盾"，去掉上游的 DNA 双螺旋双关。
共 340 个文本文件被改写，所有目录/文件名同步重命名。

**合规例外**：各 `NOTICE` 中的上游版权行与 `ATTRIBUTION.md` 的来源链接按
Apache-2.0 §4(c)/4(d) 原样保留。这些是法律归属声明，不是产品标识。详见
[ATTRIBUTION.md](ATTRIBUTION.md)。

含上游品牌文字的 4 张平台截图与 1 张内嵌证据闭环图已处理：README 改为文字说明，
证据闭环图重绘为 `evolution-evidence-loop.svg`，原 PNG 覆盖为空白占位图（发布前可删除）。

## 2. 多宿主支持

原项目用清单驱动的 Host API 1.1，Registry 扫描 `hosts/*/host.json`，**核心代码没有平台分支**。
本次保留 Codex / Claude Code 两个 stable Kit，新增四个 preview Kit，共 6 个宿主：

| Host ID | 产品 | 等级 | 命令表面 | 分发清单 |
| --- | --- | --- | --- | --- |
| `claude-code` | Claude Code | stable | native-command | `.claude-plugin/marketplace.json` |
| `codex` | Codex | stable | skill | `.codex-plugin/plugin.json` |
| `minimax` | MiniMax Code | preview | skill | `.minimax-plugin/plugin.json` |
| `workbuddy` | WorkBuddy / CodeBuddy | preview | native-command | `.codebuddy-plugin/plugin.json` |
| `qoder` | Qoder | preview | native-command | `.qoder-plugin/plugin.json` |
| `deepseek-dsh` | DeepSeek Harness (dsh) | preview | skill | `.dsh-plugin/plugin.json`（声明清单） |

每个新 Host Kit 都包含完整的 `host.json` + 11 个必需资源适配器 + 命令投影 +
原生分发清单 + 安装器。Registry `list` 已校验通过。

新增的可扩展能力：

- `scripts/update_hosts/generic.py`：四个保守的宿主 detector（显式运行时标记才触发，
  preview 分值 70 低于 stable 的 100，避免混合环境误判）。
- `scripts/check_release.py`：不依赖临时目录的发布前一致性检查。
- `docs/host-support-matrix.md`：能力矩阵、别名、安装速查、Host Context 绑定。
- `docs/add-new-host.md`：新增宿主标准接入规范（7 步流程、契约字段、投影规则、验证清单）。
- `docs/host-kit-template/`：可复制的 Host Kit 骨架。

**共享核心零改动**：`commands/`、`workflows/`、`skills/`、`metrics.py`、`version_update.py`、
Registry 控制流都没有加 `if <platform>` 分支——新增宿主是纯配置级变更。

### preview 宿主的诚实边界

MiniMax Code / WorkBuddy / Qoder / DeepSeek Harness (dsh) 对 `telemetry`、`plugin_update`、`session_start`、
`session_events`、`session_end`、`project_hooks` 声明为 **`unsupported`**：
不注册插件级 hook、不写宿主设置文件、不采集遥测、不自动升级，也不借用其他宿主资源。
九个 `/aegis:*` 命令与 Propose → Apply → Archive 生命周期由公共命令显式记账，
**与这些能力无关，全部可用**。

插件升级在这些宿主上走宿主原生插件管理；混合环境用
`export AEGISHARNESS_PLATFORM=<host-id>` 显式绑定。

## 3. 验证结果

```bash
cd aegisharness/aegisharness/scripts
python3 check_release.py
python3 host_runtime_cli.py list
python3 host_runtime_cli.py resolve --platform deepseek-dsh
```

| 检查 | 结果 |
| --- | --- |
| JSON 清单解析（全仓） | PASS |
| Python 源码编译（全仓） | PASS |
| Host Kit 契约（manifest / 11 资源 / 命令投影 / 项目配置 / hooks） | PASS（6 个宿主） |
| 分发清单 | PASS |
| 品牌残留（排除法律署名文件） | PASS |
| 文档链接 | PASS |
| `host_runtime_cli.py list` | `["claude-code","codex","deepseek-dsh","minimax","qoder","workbuddy"]` |
| `resolve --platform` 六个宿主 | 全部 `resolved` |
| detector 自动识别 + `AEGISHARNESS_PLATFORM` 显式覆盖 | PASS |

同时把 `test_public_workflow_router.py` 的宿主集合断言改成**动态校验**
（每个有清单的目录都必须被发现、每个宿主的投影覆盖九个命令），以后新增宿主不会再破坏测试。

> `run_tests.py` 完整套件在本环境跑了 364 个测试，其中 27 个 error 与 1 个耗时断言失败
> 来自执行环境的临时目录拦截（`sitecustomize.py` shim 报 `FileExistsError` /
> `No usable temporary directory`），与本次改动无关；另 1 个宿主集合断言已修复。
> 建议在 CI 或干净终端重跑全套：`python3 scripts/run_tests.py`。

## 4. 发布前待办

- [x] 把 `NOTICE`（4 份）里的 `<Your Company>` 换成公司法定名称 —— 已填为 `elierncn`，
      与上游 `Copyright 2026 DiDi Financial and HelixHarness contributors` 并列保留。
- [x] 把仓库地址占位换成实际地址 —— 已统一为 `github.com/elierncn/aegisharness`
      （README、安装文档、user-guide、`pyproject.toml`、`CONTRIBUTING.md`、`SECURITY.md`、
      各 `installer.md`，共 45 处）；dsh 的 npm 包名同步为 `@elierncn/aegisharness-dsh`。
- [x] 删除 [ATTRIBUTION.md](ATTRIBUTION.md) 列出的 5 个占位 PNG —— 已全部删除。
- [ ] 在四个 preview 宿主上完成安装 → 新会话发现九个命令 → `/aegis:init` →
      小需求 Propose→Apply→Archive → 归档证据 → 重载/卸载 的 E2E；
      通过后把 `host.json` 的 `support.level` 改为 `stable` 并补 E2E 证据路径。
- [ ] 在干净环境跑 `python3 scripts/run_tests.py` 确认全套通过。
- [ ] 按需补齐 preview 宿主的 telemetry / plugin_update Python 适配器
      （见 [新增宿主指南](docs/add-new-host.md) 第 2 节），或保持 `unsupported`。

## 5. 日常使用

命令、工作流、知识沉淀方式与原项目一致，只是命名空间换成 `/aegis:*`：

```text
/aegis:init
/aegis:propose task-filter ./requirements/task-filter.md --loop
/aegis:status task-filter
```

完整使用文档见 [docs/user-guide.zh-CN.md](docs/user-guide.zh-CN.md)，
宿主选择见 [docs/host-support-matrix.md](docs/host-support-matrix.md)。

## 6. 增量：新增 DeepSeek Harness (dsh) 宿主

在 5 宿主版本之上追加第六个 Host Kit，仍为纯配置级变更（共享核心零改动）：

- `hosts/deepseek-dsh/`：`host.json` + 11 个必需资源 + 命令投影（surface `skill`）+ 九个
  `skills/aegis-*/SKILL.md` 薄入口 + `installer.md`（含完整安装脚本）。
- `.dsh-plugin/plugin.json`（插件根与仓库根各一份）：声明清单。
- `scripts/update_hosts/generic.py` 增加 `detect_deepseek_dsh`（标记 `DSH_SESSION` /
  `DSH_PROFILE` / `DSH_PLUGIN_ROOT` / `DSH_HOME`）。
- README（中/英）与 `docs/installation.md` 的安装章节改为**每个宿主一段完整可复制安装脚本**。

### dsh 的诚实边界

DSH 处于 developer preview，没有插件市场：`dsh plugin --profile <name> add <package>` 转发给
pnpm，要求目标是含 `package.json` 的 npm 包。因此 `.dsh-plugin/plugin.json` 只是**声明清单**，
不是可安装的 Cordis 插件包。当前走 DSH 原生 skill 发现 + 项目 `AGENTS.md`：
把九个 `aegis-*` Skill 软链到 `${DSH_HOME:-~/.dsh}/skills/`，用 `/aegis-init` 生成项目入口。
Skill 名只接受 kebab-case，`/aegis:<cmd>` 在本宿主以 `/aegis-<cmd>` 触发，两者进入同一份
公共契约。待发布 npm 包后才可启用 `dsh plugin ... add` 路径。

`telemetry`、`plugin_update`、会话 hooks、`project_hooks` 仍为 `unsupported`；
`support.level` 保持 `preview`，未经官方 E2E。
