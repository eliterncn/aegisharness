# WorkBuddy / CodeBuddy 入口装载

本宿主不注册 SessionStart hook，公共命令由用户显式触发。每个入口在执行前：

1. 执行 `reference/runtime-preflight.md`，确认 Python 3.10+ 与 Git 可用。
2. 完整读取当前命令在 `commands/` 下的唯一公共契约文件。
3. 读取 `reference/workflow-projection-protocol.md`、`reference/host-runtime-protocol.md`、
   `reference/tool-semantics.md`，以及当前 Host Context 中的
   `resources.runtime`、`resources.subagent_protocol`、`resources.project_config`、
   `resources.project_hooks`、`resources.telemetry_protocol`。
4. 按 `reference/loading-protocol.md` 通过 `docs/harness/index.md` 与
   `docs/knowledge/index.md` 按需加载上下文，不跳过索引凭路径猜测。

Host Context 通过 `python3 scripts/host_runtime_cli.py resolve --platform workbuddy` 获取；
新会话内若已解析且插件根未变化则沿用，不重复注入。
