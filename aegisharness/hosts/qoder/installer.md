# Qoder 安装与更新

需要 Python 3.10+、Git 与支持插件市场的 Qoder。完整步骤见
[安装指南](../../../docs/installation.md)。将仓库根目录记为 `AEGISHARNESS_SOURCE`；
也可直接使用 `https://github.com/eliterncn/aegisharness.git`。

桌面端和 CLI 是两个独立入口，**加市场源只有 CLI 能做**：Qoder 桌面端的插件面板里
没有「添加市场源」，那里只有官方市场浏览与「导入本地插件」。按你手上的形态选一条。

## 方式 A：桌面端直接导入（最快，不需要命令行）

1. 打开 Qoder → **设置**（macOS `⌘,`）→ **插件**；
2. 在**自定义**区域点**导入**：国际版是「从本地文件夹导入」，Qoder CN 是「导入 ZIP」；
3. 选插件根目录——**含 `.qoder-plugin/plugin.json` 的那一层**：

   ```
   /绝对路径/aegisharness/aegisharness
   ```

   ⚠️ 不是仓库根。仓库根那层没有 `commands/`、`skills/`、`agents/`，导进去会是个空插件。

4. 生效范围选 **User 级**（对所有会话生效）或 **Project 级**；
5. 确认插件出现在「插件 → 用户级」且为启用状态，然后新开会话。

需要 ZIP 时，在插件根内打包（`dist/` 已在 `.gitignore` 里）：

```bash
cd "$AEGISHARNESS_SOURCE/aegisharness" && zip -rqX ../dist/aegis-qoder-plugin.zip . -x "*/__pycache__/*"
```

## 方式 B：CLI 加市场源（能跟随市场更新）

```bash
npm i -g @qoder-ai/qodercli
qoder plugins marketplace add eliterncn/aegisharness
qoder plugins install aegis@aegisharness-marketplace
qoder plugins list
```

- 可执行名是 `qoder`，文档与社区示例里也写作 `qodercli`；子命令组是 `plugins`（`plugin` 是别名）。
- `marketplace add` 接受 git URL（HTTPS / SSH）、`owner/repo` 简写、本地目录、或指向
  `marketplace.json` 的 URL。
- 不加市场源也可直接装本地目录，插件 ID 变成 `aegis@local`：

  ```bash
  qoder plugins install "$AEGISHARNESS_SOURCE/aegisharness" --scope project
  ```

- 开发期可先校验清单与组件发现：`qoder plugins validate "$AEGISHARNESS_SOURCE/aegisharness"`。

安装后新开会话，确认 `/aegis:*` 九个命令与 `qoder.md` 项目指令已加载。

## Host Context 绑定

`host_runtime_cli.py resolve` 优先读取 `AEGISHARNESS_PLATFORM`，其次使用各宿主的
detector 自动识别。若同一终端同时存在多个宿主的运行时标记（例如同时设置了
`CLAUDE_PLUGIN_ROOT` 与本宿主变量），稳定宿主会优先，可能误判。此时显式指定：

```bash
export AEGISHARNESS_PLATFORM=qoder
```

也可在命令中直接使用 `resolve --platform qoder`。禁止通过复制其他 Host Kit 的
入口、缓存或环境变量来绕过识别；未识别时 Registry 关闭失败。

## 验证

1. 新开会话，确认九个公开命令可见：`init`、`propose`、`apply`、`archive`、`bug-fix`、`ut`、`update`、`status`、`config`。
2. 运行 `python3 {plugin_root}/scripts/host_runtime_cli.py list`，输出必须包含 `qoder`。
3. 运行 `python3 {plugin_root}/scripts/host_runtime_cli.py resolve --platform qoder`，
   确认 `host_id` 与 `plugin_root` 指向本次安装，避免混入其他 checkout 或缓存版本。
4. 在业务仓库执行 `/aegis:init`，检查 `docs/harness/index.md`、`docs/knowledge/index.md`、
   `docs/knowledge/project-context.md` 与 `qoder.md` 是否非空。

## 更新与卸载

本宿主 `plugin_update` 声明为 `unsupported`，`/aegis:update` 不做跨版本自动升级。
升级路径按安装方式区分：走市场的用
`qoder plugins marketplace update aegisharness-marketplace` 再 `plugins install` 重装；
桌面端导入的重新导入一次覆盖即可（自定义插件同名可直接覆盖，市场来源不行）。改完新开会话。
卸载通过宿主插件管理完成；插件卸载不会删除业务仓库中的
`docs/harness/`、`docs/knowledge/`、`docs/specs/` 或业务代码。
