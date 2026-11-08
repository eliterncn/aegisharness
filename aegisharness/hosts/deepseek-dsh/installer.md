# DeepSeek Harness (dsh) 安装与更新

需要 Node.js 22.19+ 或 24+、npm/npx、Python 3.10+ 与 Git，以及 DeepSeek Harness
（CLI `dsh`，npm 包 `@deepseek-ai/dsh`）。完整步骤见
[安装指南](../../../docs/installation.md)。

> **developer preview**：DSH 的插件、profile 与 skills 目录约定可能随 RC 版本变化。
> 安装前用 `npx @deepseek-ai/dsh --profile web --dump-config` 核对当前 profile 实际生效的路径，
> 不要凭版本号猜测。本宿主支持等级为 `preview`，尚未完成官方 E2E。

## 方式 A：Skills + AGENTS.md（当前可用，推荐）

DSH 读取项目根 `AGENTS.md`（`instructionFileCandidates` 默认 `['AGENTS.md','CLAUDE.md']`），
并扫描 `<repo>/.dsh/skills/`、`${DSH_HOME:-~/.dsh}/skills/`、`~/.agents/skills/` 等目录下的
`<name>/SKILL.md`。本插件把九个公共命令投影为
`hosts/deepseek-dsh/skills/aegis-*/SKILL.md` 的 Skill 薄入口。

```bash
# 1) 安装 DSH CLI
npm install -g @deepseek-ai/dsh

# 2) 取得插件源码（发布前测试可把 URL 换成本地 checkout 路径）
export AEGISHARNESS_SOURCE="https://github.com/elierncn/aegisharness.git"
git clone "$AEGISHARNESS_SOURCE" "$HOME/aegisharness"

# 3) 把九个 Skill 薄入口挂到 DSH 的全局 skills 目录
DSH_SKILLS="${DSH_HOME:-$HOME/.dsh}/skills"
mkdir -p "$DSH_SKILLS"
for c in init propose apply archive bug-fix ut update status config; do
  ln -sfn "$HOME/aegisharness/aegisharness/hosts/deepseek-dsh/skills/aegis-$c" \
    "$DSH_SKILLS/aegis-$c"
done

# 4) 核对 profile 的实际配置，再启动并新开会话
npx @deepseek-ai/dsh --profile web --dump-config
npx @deepseek-ai/dsh web
```

只想对单个业务仓库生效时，把第 3 步的目标改成该仓库的 `.dsh/skills/`：

```bash
mkdir -p "<your-repo>/.dsh/skills"
for c in init propose apply archive bug-fix ut update status config; do
  ln -sfn "$HOME/aegisharness/aegisharness/hosts/deepseek-dsh/skills/aegis-$c" \
    "<your-repo>/.dsh/skills/aegis-$c"
done
```

在业务仓库新开会话后执行 `/aegis-init`（等价 `/aegis:init`）生成项目 `AGENTS.md`。
命令名映射见 `hosts/deepseek-dsh/skill-entry.md`。

## 方式 B：原生插件挂载（需先发布 npm 包）

`dsh plugin --profile <name> add <package>` 会把包操作转发给 pnpm，因此目标必须是含
`package.json` 的 npm 包。本仓库的 `.dsh-plugin/plugin.json` 是**声明清单**（描述投影、
skills 路径与安装方式），不是可直接安装的 Cordis 插件包；直接对它执行
`dsh plugin ... add link:<path>` 会失败。

待把本插件发布为带 `package.json` 的 npm 包后，可用（包名为占位，发布后替换）：

```bash
dsh plugin --profile web add "@elierncn/aegisharness-dsh"
dsh plugin --profile web remove aegisharness-dsh
```

安装完成后必须重启 `dsh web`。在此之前请使用方式 A。

## Host Context 绑定

`host_runtime_cli.py resolve` 优先读取 `AEGISHARNESS_PLATFORM`，其次使用各宿主的
detector 自动识别（本宿主识别 `DSH_SESSION` / `DSH_PROFILE` / `DSH_PLUGIN_ROOT` / `DSH_HOME`）。
若同一终端同时存在多个宿主的运行时标记，稳定宿主会优先，可能误判。此时显式指定：

```bash
export AEGISHARNESS_PLATFORM=deepseek-dsh
```

也可直接使用 `resolve --platform deepseek-dsh`。禁止通过复制其他 Host Kit 的入口、
缓存或环境变量来绕过识别；未识别时 Registry 关闭失败。

## 验证

1. 重启 DSH 并新开会话，确认九个 Skill 可见：`aegis-init`、`aegis-propose`、
   `aegis-apply`、`aegis-archive`、`aegis-bug-fix`、`aegis-ut`、`aegis-update`、
   `aegis-status`、`aegis-config`。
2. 运行 `python3 {plugin_root}/scripts/host_runtime_cli.py list`，输出必须包含 `deepseek-dsh`。
3. 运行 `python3 {plugin_root}/scripts/host_runtime_cli.py resolve --platform deepseek-dsh`，
   确认 `host_id` 与 `plugin_root` 指向本次安装，避免混入其他 checkout 或缓存版本。
4. 在业务仓库执行 `/aegis-init`，检查 `docs/harness/index.md`、`docs/knowledge/index.md`、
   `docs/knowledge/project-context.md` 与 `AGENTS.md` 是否非空。

## 更新与卸载

本宿主 `plugin_update` 声明为 `unsupported`，`/aegis:update` 不做跨版本自动升级。
更新源码后重新执行方式 A 的第 2–3 步（或重新 `git pull` 后刷新软链），重启 DSH 并新开会话。
卸载时删除 `$DSH_SKILLS/aegis-*` 软链；不会删除业务仓库中的
`docs/harness/`、`docs/knowledge/`、`docs/specs/` 或业务代码。
