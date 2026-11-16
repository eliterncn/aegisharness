# MiniMax Code 安装与更新

需要 Python 3.10+、Git 与支持插件市场的 MiniMax Code。完整步骤见
[安装指南](../../../docs/installation.md)。将仓库根目录记为 `AEGISHARNESS_SOURCE`；
也可直接使用 `https://github.com/eliterncn/aegisharness.git`。

## 三条安装路径（按优先级）

MiniMax Code 有桌面端与 CLI 两种形态，插件能力由同一个插件目录承载，因此三条路径
装的是同一份东西，只是入口不同。

### A. 桌面端插件面板（推荐，入口在灰度）

打开 MiniMax Code → **Plugins** → **Add marketplace**，填 `eliterncn/aegisharness`，
装 `aegis`。该入口正在逐步放开，你的版本看不到时走 B 或 C。

### B. 本地插件目录（最稳，不依赖市场）

```bash
# 1) 让宿主告诉你它的本地插件目录
mcode plugin marketplace list

# 2) 把插件目录整体拷进去（注意是整个 aegisharness/，不是里面的子目录）
cp -R "$AEGISHARNESS_SOURCE/aegisharness" "<上一条命令显示的本地插件目录>/"

# 3) 在 MiniMax Code 里打开 /plugins，按 Ctrl+R 刷新，用 Space 启用
```

### C. Skill 直装（宿主原生发现，无需插件机制）

MiniMax Code 扫描 `项目/.minimax/skills/`、`项目/.claude/skills/`、`项目/.agents/skills/`，
以及全局 `~/.agents/skills/`（同时读 `~/.claude/skills/` 与 `~/.codex/skills/`）。

⚠️ **不要只拷 `hosts/minimax/skills/` 子目录**：那九个 `SKILL.md` 里写的是
「插件根为当前文件的 `../../../..`」，再往下要读 `commands/<cmd>.md` 与
`hosts/minimax/skill-entry.md`。只拷子目录会让插件根解析到 `~/.agents/`，
命令契约找不到文件。正确做法是把插件放在固定位置，再软链出来：

```bash
mkdir -p ~/.agents/skills
ln -sfn "$AEGISHARNESS_SOURCE/aegisharness/hosts/minimax/skills/init" ~/.agents/skills/aegis-init
# 其余八个同理：apply archive bug-fix config propose status update ut
```

### 关于 `mcode plugin add`

`mcode plugin add` 只从官方目录安装，**不接受 GitHub URL 或本地路径**。
装第三方插件只能走上面的 A / B / C。

## Host Context 绑定

`host_runtime_cli.py resolve` 优先读取 `AEGISHARNESS_PLATFORM`，其次使用各宿主的
detector 自动识别。若同一终端同时存在多个宿主的运行时标记（例如同时设置了
`CLAUDE_PLUGIN_ROOT` 与本宿主变量），稳定宿主会优先，可能误判。此时显式指定：

```bash
export AEGISHARNESS_PLATFORM=minimax
```

也可在命令中直接使用 `resolve --platform minimax`。禁止通过复制其他 Host Kit 的
入口、缓存或环境变量来绕过识别；未识别时 Registry 关闭失败。

## 验证

1. 新开会话，确认九个公开命令可见：`init`、`propose`、`apply`、`archive`、`bug-fix`、`ut`、`update`、`status`、`config`。
2. 运行 `python3 {plugin_root}/scripts/host_runtime_cli.py list`，输出必须包含 `minimax`。
3. 运行 `python3 {plugin_root}/scripts/host_runtime_cli.py resolve --platform minimax`，
   确认 `host_id` 与 `plugin_root` 指向本次安装，避免混入其他 checkout 或缓存版本。
4. 在业务仓库执行 `/aegis:init`，检查 `docs/harness/index.md`、`docs/knowledge/index.md`、
   `docs/knowledge/project-context.md` 与 `AGENTS.md` 是否非空。

## 更新与卸载

本宿主 `plugin_update` 声明为 `unsupported`，`/aegis:update` 不做跨版本自动升级。
请在宿主插件管理中刷新已配置的 marketplace 并重新安装，然后新开会话。
卸载通过宿主插件管理完成；插件卸载不会删除业务仓库中的
`docs/harness/`、`docs/knowledge/`、`docs/specs/` 或业务代码。
