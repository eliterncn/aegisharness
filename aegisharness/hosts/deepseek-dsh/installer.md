# DeepSeek Harness (dsh) 安装与更新

需要 Node.js 22.19+ 或 24+、npm/npx、Python 3.10+ 与 Git，以及 DeepSeek Harness
（CLI `dsh`，npm 包 `@deepseek-ai/dsh`）。完整步骤见
[安装指南](../../../docs/installation.md)。

> **developer preview**：DSH 的插件、profile 与 bundle 约定可能随 RC 版本变化。
> 安装前用 `dsh --version` 与 `dsh --profile <name> --dump-config` 核对当前 profile
> 实际生效的内容，不要凭版本号猜测。本宿主支持等级为 `preview`。

## 方式 A：原生插件（推荐）

本仓库的插件根就是 npm 包 `@eliterncn/aegisharness-dsh` 的包根：`package.json` 用
`dsh.bundle.patch` 声明 `cordis.patch.yml`，该 patch 只插入一个条目，由
`lib/index.js` 通过 `ctx.skills.register()` 把九个公共命令注册成运行时 Skill。
因此安装就是 `dsh` 自己的插件管理，不需要往 `$DSH_HOME/skills/` 拷文件。

```bash
# 1) 安装 DSH CLI（已装可跳过）
npm install -g @deepseek-ai/dsh

# 2) 用 dsh 自己的插件管理安装，并自动写入 profile 的 bundles
dsh plugin --profile web add @eliterncn/aegisharness-dsh

# 3) 确认 profile 已包含本插件的 bundle 层与组合条目
dsh --profile web --dump-config | grep -A1 aegisharness

# 4) 重启 dsh web，新开会话后确认九个 /aegis-* Skill 可见
dsh web
```

`dsh plugin add` 会把包解析到 `$DSH_HOME/profiles/<name>/node_modules/` 并把包名追加进
profile `package.json` 的 `dsh.profile.bundles`，因此不需要手改清单。卸载同样一条命令：

```bash
dsh plugin --profile web remove @eliterncn/aegisharness-dsh
```

包尚未发布到 npm 时，用本地路径做同样的原生安装（开发者模式）：

```bash
git clone https://github.com/eliterncn/aegisharness.git "$HOME/aegisharness"
dsh plugin --profile web add "file:$HOME/aegisharness/aegisharness"
```

> 包内 `hosts/`、`commands/`、`reference/`、`templates/`、`workflows/`、`skills/`、
> `scripts/` 都是运行时资源：Skill 正文按绝对路径引用它们，缺失即视为打包错误。
> 可在包根用 `node tests/dsh-plugin.test.mjs` 做离线自检（不启动 dsh、不联网）。

## 方式 B：skills 目录（无 npm 访问权限时）

DSH 也会扫描 `<repo>/.dsh/skills/`、`${DSH_HOME:-~/.dsh}/skills/`、`~/.agents/skills/`
下的 `<name>/SKILL.md`，并读取项目根 `AGENTS.md`。把九个薄入口挂到这些目录即可：

```bash
export AEGISHARNESS_SOURCE="https://github.com/eliterncn/aegisharness.git"
git clone "$AEGISHARNESS_SOURCE" "$HOME/aegisharness"

DSH_SKILLS="${DSH_HOME:-$HOME/.dsh}/skills"
mkdir -p "$DSH_SKILLS"
for c in init propose apply archive bug-fix ut update status config; do
  ln -sfn "$HOME/aegisharness/aegisharness/hosts/deepseek-dsh/skills/aegis-$c" \
    "$DSH_SKILLS/aegis-$c"
done
```

只想对单个业务仓库生效时，把目标改成该仓库的 `.dsh/skills/`。两种方式的命令名一致：
`/aegis-init` 等价 `/aegis:init`，映射见 `hosts/deepseek-dsh/skill-entry.md`。

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

1. `dsh --profile web --dump-config` 输出中出现 `id: aegisharness` 与
   `name: '@eliterncn/aegisharness-dsh'`。
2. 重启 DSH 并新开会话，确认九个 Skill 可见：`aegis-init`、`aegis-propose`、
   `aegis-apply`、`aegis-archive`、`aegis-bug-fix`、`aegis-ut`、`aegis-update`、
   `aegis-status`、`aegis-config`。
3. 运行 `python3 {plugin_root}/scripts/host_runtime_cli.py list`，输出必须包含 `deepseek-dsh`。
4. 运行 `python3 {plugin_root}/scripts/host_runtime_cli.py resolve --platform deepseek-dsh`，
   确认 `host_id` 与 `plugin_root` 指向本次安装，避免混入其他 checkout 或缓存版本。
5. 在业务仓库执行 `/aegis-init`，检查 `docs/harness/index.md`、`docs/knowledge/index.md`、
   `docs/knowledge/project-context.md` 与 `AGENTS.md` 是否非空。

## 更新与卸载

本宿主 `plugin_update` 声明为 `unsupported`，`/aegis:update` 不做跨版本自动升级；
升级走宿主自己的包管理：

```bash
dsh plugin --profile web add @eliterncn/aegisharness-dsh@latest
dsh plugin --profile web remove @eliterncn/aegisharness-dsh   # 卸载
```

方式 B 卸载时删除 `$DSH_SKILLS/aegis-*` 软链。两种方式都不会删除业务仓库中的
`docs/harness/`、`docs/knowledge/`、`docs/specs/` 或业务代码。
