# WorkBuddy / CodeBuddy 安装与更新

需要 Python 3.10+、Git 与支持插件市场的 WorkBuddy / CodeBuddy。完整步骤见
[安装指南](../../../docs/installation.md)。将仓库根目录记为 `AEGISHARNESS_SOURCE`；
也可直接使用 `https://github.com/elierncn/aegisharness.git`。

```bash
# 本地源码安装（WorkBuddy / CodeBuddy）
codebuddy plugin marketplace add "$AEGISHARNESS_SOURCE"
codebuddy plugin install aegis@aegisharness-marketplace
```

安装后运行 `/reload-plugins` 并新开会话，确认 `/aegis:*` 九个命令可见。

## Host Context 绑定

`host_runtime_cli.py resolve` 优先读取 `AEGISHARNESS_PLATFORM`，其次使用各宿主的
detector 自动识别。若同一终端同时存在多个宿主的运行时标记（例如同时设置了
`CLAUDE_PLUGIN_ROOT` 与本宿主变量），稳定宿主会优先，可能误判。此时显式指定：

```bash
export AEGISHARNESS_PLATFORM=workbuddy
```

也可在命令中直接使用 `resolve --platform workbuddy`。禁止通过复制其他 Host Kit 的
入口、缓存或环境变量来绕过识别；未识别时 Registry 关闭失败。

## 验证

1. 新开会话，确认九个公开命令可见：`init`、`propose`、`apply`、`archive`、`bug-fix`、`ut`、`update`、`status`、`config`。
2. 运行 `python3 {plugin_root}/scripts/host_runtime_cli.py list`，输出必须包含 `workbuddy`。
3. 运行 `python3 {plugin_root}/scripts/host_runtime_cli.py resolve --platform workbuddy`，
   确认 `host_id` 与 `plugin_root` 指向本次安装，避免混入其他 checkout 或缓存版本。
4. 在业务仓库执行 `/aegis:init`，检查 `docs/harness/index.md`、`docs/knowledge/index.md`、
   `docs/knowledge/project-context.md` 与 `AGENTS.md` 是否非空。

## 更新与卸载

本宿主 `plugin_update` 声明为 `unsupported`，`/aegis:update` 不做跨版本自动升级。
请在宿主插件管理中刷新已配置的 marketplace 并重新安装，然后新开会话。
卸载通过宿主插件管理完成；插件卸载不会删除业务仓库中的
`docs/harness/`、`docs/knowledge/`、`docs/specs/` 或业务代码。
