# DeepSeek Harness (dsh) 入口装载

本宿主不注册 SessionStart hook，公共命令由用户显式触发。每个入口在执行前：

1. 执行 `reference/runtime-preflight.md`，确认 Python 3.10+ 与 Git 可用；
   DSH 本体另需 Node.js 22.19+ 或 24+。
2. 完整读取当前命令在 `commands/` 下的唯一公共契约文件。
3. 读取 `reference/workflow-projection-protocol.md`、`reference/host-runtime-protocol.md`、
   `reference/tool-semantics.md`，以及当前 Host Context 中的
   `resources.runtime`、`resources.subagent_protocol`、`resources.project_config`、
   `resources.project_hooks`、`resources.telemetry_protocol`。
4. 按 `reference/loading-protocol.md` 通过 `docs/harness/index.md` 与
   `docs/knowledge/index.md` 按需加载上下文，不跳过索引凭路径猜测。

## DSH 的命令名映射

DSH 的 Skill 名使用 kebab-case，公共命令的冒号命名空间不能直接注册。投影目录为
`hosts/deepseek-dsh/skills/aegis-*/SKILL.md`，触发名与公共命令一一对应：

| 公共命令 | DSH Skill |
| --- | --- |
| `/aegis:init` | `/aegis-init` |
| `/aegis:propose` | `/aegis-propose` |
| `/aegis:apply` | `/aegis-apply` |
| `/aegis:archive` | `/aegis-archive` |
| `/aegis:bug-fix` | `/aegis-bug-fix` |
| `/aegis:ut` | `/aegis-ut` |
| `/aegis:update` | `/aegis-update` |
| `/aegis:status` | `/aegis-status` |
| `/aegis:config` | `/aegis-config` |

两种写法都进入同一份公共契约；不得因为名称不同而改变产物、门禁或完成条件。

## Skills 与指令文件的发现路径

- 项目指令：`<repo>/AGENTS.md`（`instructionFileCandidates` 默认 `['AGENTS.md','CLAUDE.md']`）；
  全局指令为 `${DSH_HOME:-~/.dsh}/AGENTS.md`。
- Skills（优先级由高到低）：`<repo>/.dsh/skills/`、`<repo>/.agents/skills/`、
  `${DSH_HOME:-~/.dsh}/skills/`、`~/.agents/skills/`。
- 用 `dsh --profile web --dump-config` 核对当前 profile 实际生效的路径；DSH 处于
  developer preview，目录约定可能随 RC 版本变化，不要凭版本猜测。

Host Context 通过 `python3 scripts/host_runtime_cli.py resolve --platform deepseek-dsh` 获取；
新会话内若已解析且插件根未变化则沿用，不重复注入。
