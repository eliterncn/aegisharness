# 宿主支持矩阵

AegisHarness 通过 **Host Kit** 适配不同的 AI 编码产品。共享核心（`commands/`、`workflows/`、
`skills/`、`agents/`、`templates/`）定义业务结果，`hosts/{host-id}/` 只定义如何安装、发现和执行。
Registry 扫描 `hosts/*/host.json`，**不在核心代码里维护平台分支**。

支持范围：[English summary](#english-summary) · [新增宿主指南](add-new-host.md) · [Host API 契约](../aegisharness/reference/host-api.md)

## 当前支持的宿主

| Host ID | 产品 | 支持等级 | 命令表面 | 项目入口 | 原生分发清单 |
| --- | --- | --- | --- | --- | --- |
| `claude-code` | Claude Code | **stable** | `native-command`（`/aegis:*`） | `CLAUDE.md` | `.claude-plugin/marketplace.json` |
| `codex` | Codex | **stable** | `skill`（Skill 薄入口投影） | `AGENTS.md` | `.codex-plugin/plugin.json` |
| `minimax` | MiniMax Code (`mcode`) | preview | `skill` | `AGENTS.md` | `.minimax-plugin/plugin.json` |
| `workbuddy` | WorkBuddy / CodeBuddy | preview | `native-command` | `AGENTS.md` | `.codebuddy-plugin/plugin.json` |
| `qoder` | Qoder（IDE / CLI） | preview | `native-command` | `qoder.md` | `.qoder-plugin/plugin.json` |
| `deepseek-dsh` | DeepSeek Harness / dsh | preview | `skill`（`aegis-*` 触发别名） | `AGENTS.md` | `.dsh-plugin/plugin.json`（声明清单） |

别名：`claude` → `claude-code`；`mcode` / `minimax-code` → `minimax`；
`codebuddy` / `work-buddy` → `workbuddy`；`qoder-cli` / `qoder-ide` → `qoder`；
`dsh` / `deepseek-harness` / `deepseek` → `deepseek-dsh`。

## 能力对照

| 能力 | Codex | Claude Code | MiniMax Code | WorkBuddy | Qoder | DeepSeek Harness |
| --- | --- | --- | --- | --- | --- | --- |
| 命令入口 | emulated (Skill) | native | emulated (Skill) | native | native | emulated (Skill) |
| Skill 发现 | native | native | native | native | native | native |
| 子代理 | native | native | native | native | native | native（Standard preset） |
| 工作流跳转 / 单测 / 任务跟踪 | native / native / native | emulated / native / native | emulated | emulated | emulated | emulated |
| 会话启动 / 结束 / 事件 Hook | 部分 native | 部分 native | **unsupported** | **unsupported** | **unsupported** | **unsupported** |
| 项目级 hooks | `.codex/hooks.json` | `.claude/settings.json` | **unsupported** | **unsupported** | **unsupported** | **unsupported** |
| 遥测 | native | native | **unsupported** | **unsupported** | **unsupported** | **unsupported** |
| 插件安装 | native (marketplace) | native (marketplace) | native | native | native | skills + `AGENTS.md` |
| 插件自动更新 | native | native | **unsupported** | **unsupported** | **unsupported** | **unsupported** |

> **`unsupported` 的含义**：能力关闭失败，不伪造 adapter、不写宿主设置文件、不采集数据，
> 也不借用其他宿主的资源。核心 Propose → Apply → Archive 生命周期由公共命令显式记账，
> **与这些能力无关**，因此九个命令在全部六个宿主上都可正常使用。

## 支持等级

- **stable**：已完成目标客户端的安装、新会话发现、核心工作流与发布 E2E。
- **preview**：Host Kit 与分发清单完整、Registry 契约校验通过，但尚未在目标客户端完成端到端
  E2E。上线前请按该宿主 `installer.md` 的验证步骤实测，并把 `host.json` 的
  `support.level` 提升为 `stable`、补齐 `evidence/host-e2e/{host-id}/...json`。

## 各宿主的已知限制

| 宿主 | 限制 |
| --- | --- |
| MiniMax Code | 命令以 Skill 投影提供，需在对话中显式说明 `/aegis:<command>` 与 Skill 的对应关系；插件更新走宿主原生管理。 |
| WorkBuddy / CodeBuddy | 安装后需 `/reload-plugins` 并新开会话；插件更新走宿主原生管理。 |
| Qoder | Quest 模式生成的 Spec 不能替代 AegisHarness 的 Spec/Tasks 契约，两者并行时以本插件契约为准；插件更新走宿主原生管理。 |
| DeepSeek Harness / dsh | 处于 developer preview，profile / skills 目录约定可能随 RC 变化；没有插件市场，`dsh plugin ... add` 要求 npm 包，因此当前走 skills + `AGENTS.md` 安装；Skill 名 kebab-case，`/aegis:<cmd>` 以 `/aegis-<cmd>` 触发；`.dsh-plugin/plugin.json` 是声明清单，不是可安装的 Cordis 包。 |

四个 preview 宿主共同限制：无插件级 SessionStart/Stop hook、无项目级 settings 合并、无遥测、
无自动升级。质量检查通过 `docs/hooks/` 清单与公共命令中的检查点显式驱动。

## 查询与绑定当前宿主

```bash
cd aegisharness/scripts

python3 host_runtime_cli.py list                              # 列出全部已注册 Host Kit
python3 host_runtime_cli.py resolve --platform deepseek-dsh  # 解析指定宿主的 Host Context
python3 host_runtime_cli.py resolve                          # 自动识别
```

`resolve` 的优先级：显式 `--platform` → 环境变量 `AEGISHARNESS_PLATFORM` → 各 Host Kit 的
detector 自动识别。若同一终端存在多个宿主的运行时标记，stable 宿主优先（detector 分值 100
对 preview 的 70）。**混合环境请显式指定**，例如：

```bash
export AEGISHARNESS_PLATFORM=workbuddy
```

`deepseek-dsh` 的 detector 识别 `DSH_SESSION` / `DSH_PROFILE` / `DSH_PLUGIN_ROOT` / `DSH_HOME`
等标记。未识别到宿主时 Registry 关闭失败并返回 `unsupported_host`，不会回退到其他宿主。

## 安装速查

每个宿主的完整可复制安装脚本见 [README 快速开始](../README.md#1-install-the-plugin) 与
[安装指南](installation.md#install-by-host)。速查：

| 宿主 | 命令 |
| --- | --- |
| Codex | `codex plugin marketplace add "$AEGISHARNESS_SOURCE"` → `codex plugin add aegis@aegisharness-marketplace` |
| Claude Code | `claude plugin marketplace add "$AEGISHARNESS_SOURCE"` → `claude plugin install aegis@aegisharness-marketplace` |
| MiniMax Code | `mcode plugin marketplace add "$AEGISHARNESS_SOURCE"` → `mcode plugin install aegis@aegisharness-marketplace` |
| WorkBuddy / CodeBuddy | `codebuddy plugin marketplace add "$AEGISHARNESS_SOURCE"` → `codebuddy plugin install aegis@aegisharness-marketplace` → `/reload-plugins` |
| Qoder | `qodercli plugin marketplace add "$AEGISHARNESS_SOURCE"` → `qodercli plugin install aegis@aegisharness-marketplace` |
| DeepSeek Harness / dsh | `npm install -g @deepseek-ai/dsh` → 软链 `hosts/deepseek-dsh/skills/aegis-*` 到 `${DSH_HOME:-~/.dsh}/skills/` → `dsh --profile web --dump-config` → 重启新开会话 |

`$AEGISHARNESS_SOURCE` 为包含 `aegisharness/` 与 `aegisharness-platform/` 的仓库根目录；
公开仓库地址为 `https://github.com/elierncn/aegisharness.git`。各宿主细节见
`aegisharness/hosts/{host-id}/installer.md`。

---

## English summary

AegisHarness ships six manifest-driven Host Kits. Codex and Claude Code are **stable**;
MiniMax Code, WorkBuddy / CodeBuddy, Qoder and DeepSeek Harness (dsh) are **preview** with
full command support but `telemetry`, `plugin_update`, session hooks and project-level hooks
declared `unsupported`. Unsupported capabilities fail closed and never borrow another host's
resources. The nine `/aegis:*` commands and the Propose → Apply → Archive lifecycle are
host-independent. DSH is a developer preview without a plugin marketplace, so it installs
through native skill discovery plus `AGENTS.md`; its kebab-case Skill names trigger
`/aegis:<command>` as `/aegis-<command>`.
