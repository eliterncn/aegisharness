# 新增宿主接入规范

本文件是 AegisHarness 接入新 AI 编码产品的标准操作手册。目标是让"支持更多产品"成为一次
**配置级变更**，而不是修改工作流核心。可复制骨架见 [host-kit-template/](host-kit-template/)。

设计前提：[Host API 契约](../aegisharness/reference/host-api.md) · [支持矩阵](host-support-matrix.md)

---

## 0. 先判断：真的需要新 Host Kit 吗？

| 情况 | 做法 |
| --- | --- |
| 新产品兼容 Claude Code 或 Codex 的插件/命令/环境变量约定 | 复用现有 Host Kit，在支持矩阵补一条别名即可 |
| 新产品有独立的命令注册、Skill 发现、子代理或项目指令机制 | 新建 Host Kit |
| 新产品的差异无法用 Host API 1.1 的 `capabilities` 表达 | 先设计向后兼容的 Host API 新版本，再接入 |

**禁止**：复制 `hosts/codex/` 后改几个名字、在 `commands/` 或 `workflows/` 里加
`if <platform>` 分支、把宿主名写进 `metrics.py` / `version_update.py` / Registry 控制流。
出现这些情况说明抽象边界不对，应先修正 Host API。

## 1. 七步流程

1. **评估契约**：列出新产品的命令注册方式、Skill 发现、子代理、项目指令文件、插件清单格式、
   是否支持事件 hook 与项目 settings 合并。
2. **建目录**：`aegisharness/hosts/{host-id}/`，`host-id` 为 kebab-case、全局唯一，且与目录名一致。
3. **写 `host.json`**：按第 2 节声明能力；能力不足时如实写 `unsupported`，不要伪装。
4. **补齐 11 个必需资源**：见第 3 节。所有 `resource:` 引用的文件必须真实存在。
5. **做命令投影**：见第 4 节；九个命令一个都不能少。
6. **加原生分发清单与安装器**：`.{host}-plugin/plugin.json`、marketplace 入口或 npm bundle
   （见第 6 节），仓库根与插件根各一份，并在 `installer.md` 写清安装、重载、验证、更新与卸载。
7. **验证并更新文档**：见第 7 节；更新支持矩阵、README 与版本元数据，在目标客户端跑 E2E。

## 2. `host.json` 契约

顶层字段只允许 6 个：`host_id`、`host_api_version`（当前 `1.1`）、`aliases`、
`capabilities`、`adapters`、`support`。机器 schema 是
`hosts/host-manifest-v1.schema.json`，**Python Registry 是最终运行时门禁**。

```json
{
  "host_id": "new-host",
  "host_api_version": "1.1",
  "aliases": ["new-host-cli"],
  "support": {
    "level": "preview",
    "display_name": "New Host",
    "evidence": null,
    "limitations": ["尚未完成目标客户端 E2E"]
  },
  "capabilities": {
    "command_surface": "native",
    "plugin_install": "native",
    "telemetry": "unsupported",
    "plugin_update": "unsupported",
    "project_hooks": "unsupported"
  },
  "adapters": { "...": "..." }
}
```

### 能力等级

| 值 | 含义 |
| --- | --- |
| `native` | 宿主直接提供该行为 |
| `emulated` | Host Kit 提供有边界的等价实现 |
| `unsupported` | 只能使用公共契约明确允许的降级；没有安全降级时关闭失败 |

**未声明的能力视为 `unsupported`。** 能力启用时必须同时提供对应 adapter，
不能用说明文档伪装成可执行实现。

### 能力 → adapter 对照（Registry 强制校验）

| capability 非 `unsupported` 时 | 必需的 adapter | 类型 |
| --- | --- | --- |
| `command_surface` | `command_projection` | resource |
| `plugin_install` | `installer` | resource |
| `project_hooks` | `project_hooks` | resource |
| `subagents` | `subagent_protocol` | resource |
| `unit_test_workflow` | `ut` | resource |
| `workflow_transition` | `workflow_transition` | resource |
| `telemetry` | `telemetry` + `version` | python, python |
| `plugin_update` | `update` + `version` | python, python |

`detector` 是可选 python adapter，仅供自动识别与开发诊断，不强制。

### adapter 引用格式

- `resource:hosts/{host-id}/runtime.md`：插件根目录内的相对路径，Registry 会校验文件存在并阻止路径穿越。
- `python:update_hosts.generic:detect_qoder`：模块 `:` 属性路径，由 Registry 按需 `importlib` 装载。

把 `telemetry` / `plugin_update` 声明为 `unsupported` 是**完全合法**的起点：不写 Python
适配器、不采集数据、不自动升级，等确认宿主 CLI 的真实接口后再补。
预览宿主可复用 `scripts/update_hosts/generic.py` 里的 detector 模式。

## 3. 11 个必需资源适配器

| adapter | 内容要求 |
| --- | --- |
| `distribution` | 该宿主的原生 marketplace / plugin 清单（文件本身） |
| `installer` | 安装、重载、验证、更新与卸载步骤；含 Host Context 绑定 |
| `command_projection` | 九个入口 → 唯一公共契约的映射 |
| `runtime` | 逻辑动作到宿主原生工具的映射表 |
| `subagent_protocol` | 派发、等待、终态、结果编码、资源回收与降级 |
| `workflow_transition` | 命令间跳转的物理方式（`inline` / `command`） |
| `project_config` | `entry_file`、两个模板路径、`settings_file` |
| `project_hooks` | settings 目标、owner、合并策略、去重键、payload |
| `ut` | 单测工作流物理入口 |
| `lifecycle` | 启动、阶段完成与失败生命周期 |
| `telemetry_protocol` | 遥测生命周期；可指向共享 `hosts/shared/telemetry.md` |

`project_config` 字段必须恰好是 `entry_file` / `entry_template` /
`workspace_entry_template` / `settings_file`。`settings_file: null` 表示 Init 不创建宿主设置文件，
**公共 Init 不得自行改用另一个宿主的路径**。

## 4. 命令投影规则

`command-projection.json` 必须 `projection_version: "1.0"`，`surface` 为
`native-command` 或 `skill`，且 `entrypoints` **恰好覆盖九个命令**：
`init`、`propose`、`apply`、`archive`、`bug-fix`、`ut`、`update`、`status`、`config`。

```json
{
  "projection_version": "1.0",
  "surface": "native-command",
  "entrypoints": {
    "init": ["commands/init.md", "commands/init.md"]
  }
}
```

每个值是 `[入口文件, 公共契约文件]`：

- 第二项必须严格是 `commands/{command}.md`，且该文件必须含
  `AegisHarness 公共命令唯一契约` 标记。
- 第一项必须真实存在。原生命令宿主可直接复用共享 `commands/*.md`；
  Skill 宿主需为每个命令写一个薄入口 `hosts/{id}/skills/{cmd}/SKILL.md`，
  正文明确"完整读取 `commands/{cmd}.md`"，不复制业务正文。
- `surface: "native-command"` 要求 `capabilities.command_surface == "native"`。

共享 `commands/*.md` 是**唯一业务契约**。Host Kit 只能改变物理执行方式，
不得改写流程顺序、产物、门禁或完成条件。

## 5. 项目 hooks 两种模式

**启用（json_append_dedup）**

```json
{
  "project_hooks_version": "1.0",
  "owner": "bootstrap",
  "settings_file": ".new-host/settings.json",
  "merge_strategy": "json_append_dedup",
  "dedupe_key": "hooks.PostToolUse[].matcher=Write|Edit",
  "payload": { "hooks": { "PostToolUse": [] } }
}
```

要求：`capabilities.project_hooks != "unsupported"`、`settings_file` 非 null、
与 `project_config.settings_file` **完全一致**、payload 为非空对象。

**不启用（unsupported）**

```json
{
  "project_hooks_version": "1.0",
  "owner": "bootstrap",
  "settings_file": null,
  "merge_strategy": "unsupported",
  "dedupe_key": null,
  "payload": null
}
```

要求：`capabilities.project_hooks == "unsupported"`、两个文件里的 `settings_file` 都是 null。
此时质量检查通过 `docs/hooks/` 清单与公共命令的检查点显式执行。

## 5b. 能力保持 `unsupported` 的判定标准

`unsupported` 是**契约承诺**，不是"暂时没做"的占位。它会让 `project_hooks` 走清单兜底路径、
让 `subagent_protocol` 退化为提示词约定。下面四项**同时满足**才允许标 `unsupported`：

| # | 判定条件 | 检查方式 |
| --- | --- | --- |
| 1 | 宿主确实没有对应的事件 / 扩展点 | 官方文档或 `--help` / schema 中不存在，且**不是**你尚未调研 |
| 2 | 没有明确的第三方声明载体 | 无插件清单字段、无配置文件可写、无 API 可调用 |
| 3 | 无法通过受支持的回调间接实现 | 不得靠"让模型自己记得做"来伪造能力 |
| 4 | 无模型凭据的 CI 中也能验证"确实做不到" | `scripts/host_e2e.py` 对应检查项走 `skip` / `unsupported` 分支通过，而非超时失败 |

常见误判：

- 只能写 `AGENTS.md` 之类自由文本 → **不能**承载 hooks（没有结构化去重键），判 `unsupported` 正确；
  但若宿主支持 `settings.json` 里的 `hooks` 数组，就必须判 `supported`。
- 宿主有子代理但只能在 UI 里手动点 → `subagent_protocol` 判 `partial`（有载体、无程序化入口），
  不要直接降到 `unsupported`。

六个宿主的 `project_hooks` 分布可作对照：`claude-code` / `codex` / `qoder` / `workbuddy` 为
`supported`（有结构化 settings 载体）；`minimax`（无 hooks 扩展点）与 `deepseek-dsh`
（Cordis 事件尚未暴露跨进程的 hook 声明面）为 `unsupported`，二者的质量检查统一由
`docs/hooks/` 清单 + 公共命令检查点承担。

## 6. 原生分发清单

放在插件根 `aegisharness/.{host}-plugin/`，并在仓库根放一份带
`"source": "./aegisharness"` 的入口。常见格式：

| 宿主 | 清单 | 关键字段 |
| --- | --- | --- |
| Codex | `.codex-plugin/plugin.json` | `skills`, `hooks`, `interface` |
| Claude Code | `.claude-plugin/marketplace.json` | `plugins[].source` |
| MiniMax Code | `.minimax-plugin/plugin.json` | `apps`, `mcpServers`, `skills`（三个数组都要有，可为空） |
| WorkBuddy / CodeBuddy | `.codebuddy-plugin/plugin.json` | `commands`, `skills`, `agents`, `hooks` |
| Qoder | `.qoder-plugin/plugin.json` | `skills`, `rules`, `agents`, `commands`, `hooks`, `mcpServers` |
| DeepSeek Harness / dsh | `package.json`（`dsh.bundle.patch` → `cordis.patch.yml`） | Cordis 插件模块：`name` / `inject` / `apply`，通过 `ctx.skills.register` 注册 Skill |

注册了 hook 能力的宿主，manifest **必须显式声明** `hosts/{host-id}/hooks.json`；
声明 `session_start` / `session_end` 为 `unsupported` 的宿主不得提供 hooks.json。
禁止发布根目录默认 `hooks/hooks.json`，以免客户端装载到另一个宿主的入口。

### dsh 原生 npm bundle 契约

dsh 不走 json 清单，而是一个**可发布的 npm 包**。三份文件构成契约：

```json
{
  "name": "@elierncn/aegisharness-dsh",
  "type": "module",
  "main": "lib/index.js",
  "exports": {
    ".": "./lib/index.js",
    "./cordis.patch.yml": "./cordis.patch.yml",
    "./package.json": "./package.json"
  },
  "files": ["lib", "cordis.patch.yml", "commands", "hosts"],
  "dsh": { "bundle": { "patch": "./cordis.patch.yml" } },
  "peerDependencies": { "@deepseek-ai/cordis": "~4.1.0" }
}
```

```yaml
# cordis.patch.yml —— insert 自己，不要写死宿主侧路径
- insert:
    - id: aegisharness
      name: '@elierncn/aegisharness-dsh'
```

```js
// lib/index.js —— Cordis 插件入口
export const name = 'aegisharness'
export const inject = ['skills']
export function apply(ctx) {
  for (const skill of collectSkills()) {
    ctx.skills.register({
      name: skill.name,               // 必须 kebab-case
      description: skill.description, // 不可为空，否则 dsh 拒绝加载
      content: skill.content,
      source: 'bundled',
      provider: name,
      resourceBase: { kind: 'directory', path: PACKAGE_ROOT },
      invocation: { modelInvocable: true, userInvocable: true },
    })
  }
}
```

三条硬性约束：

1. `dsh.bundle.patch` 指向的 patch 必须 `insert` **本包自身**，`id` 与 `name` 都要写；
2. `main` 与 patch 必须被 `files` 覆盖（目录条目如 `"lib"` 合法），否则发布后加载失败；
3. Skill 正文里的相对路径要在安装时改写成**绝对路径**，因为 dsh 从 profile 的
   `node_modules/` 里读文件，相对路径会解析到错误的位置。

`scripts/check_release.py` 的 `native plugin bundles` 检查会自动校验第 1、2 条；
`tests/dsh-plugin.test.mjs`（`node` 直跑，无需 dsh 与网络）校验 Skill 命名、绝对路径与契约文件存在。

## 7. 验证清单

```bash
cd aegisharness/aegisharness/scripts

# 1) Registry 能发现新宿主（不会因非法 manifest 关闭失败）
python3 host_runtime_cli.py list

# 2) 每个资源都能解析、命令投影与项目 hooks 契约都合法
python3 host_runtime_cli.py resolve --platform new-host

# 3) 显式覆盖与 detector 自动识别
AEGISHARNESS_PLATFORM=new-host python3 host_runtime_cli.py resolve
python3 run_tests.py

# 4) 宿主级 E2E（八项检查，可在无模型凭据的 CI 跑）
python3 host_e2e.py --host new-host
```

`list` 会把 `hosts/*/host.json` 全部载入，任一 manifest 非法会整体失败——
这是刻意设计的关闭失败行为。

随后在目标客户端完成 E2E：安装 → 新会话发现九个 `/aegis:*` 命令 → `/aegis:init` 生成
非空 `docs/harness/index.md`、`docs/knowledge/index.md`、`docs/knowledge/project-context.md` →
跑一个小需求的 Propose → Apply → Archive → 检查 `docs/specs/completed/` 的 Spec/Tasks/验证证据 →
重载/更新/卸载。通过后执行：

```bash
python3 host_e2e.py --host new-host --record --promote   # 写证据并把 support.level 升为 stable
```

## 8. 常见错误

| 现象 | 原因 |
| --- | --- |
| `宿主清单包含未知字段` | `host.json` 多了顶层字段，或 `support` 里字段不全 |
| `缺少必需资源适配器` | 11 个 resource adapter 有遗漏 |
| `命令投影未完整覆盖公共 workflow` | `entrypoints` 少了或多于九个命令 |
| `公共命令契约缺少唯一契约标记` | 改过 `commands/*.md` 时删掉了契约标记 |
| `项目 hooks 与 project_config 不一致` | 两个文件里的 `settings_file` 不同 |
| `宿主 adapter 不是 Python 引用` | `telemetry` / `plugin_update` 声明启用却指向 resource |
| `宿主识别冲突` | 两个 detector 返回同分；让 preview 宿主低于 stable，或显式指定 `AEGISHARNESS_PLATFORM` |
| `plugin_source_mismatch` | 执行副本与会话绑定的插件源不同；核对 marketplace 后新开会话 |
| `bundle omits lib/index.js from files` | `package.json` 的 `files` 没覆盖 `main` 或 patch |
| dsh 里看不到 `/aegis:*` | patch 未 `insert` 自身，或 profile 的 `dsh.profile.bundles` 未追加 |

## 9. 不要做的事

- 不要在 `commands/`、`workflows/`、共享 `skills/`、`metrics.py`、`version_update.py`
  或 Registry 控制流里加平台分支。
- 不要用"文档说明"冒充可执行 adapter；能力不足就写 `unsupported`。
- 不要让未知宿主回退到 Claude Code 或借用 Codex 资源。
- 不要伪造 E2E 证据；`support.level` 与 `evidence` 必须对应真实测试。
