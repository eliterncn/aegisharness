# Installation and updates / 安装与更新

[English guide](user-guide.md) · [中文指南](user-guide.zh-CN.md)

## Requirements

Python 3.10+, Git and one of the supported hosts with a plugin marketplace or native skill discovery are required. DeepSeek Harness additionally needs Node.js 22.19+ (or 24+) and npm. See the [host support matrix](host-support-matrix.md). Make sure the host is signed in or has its model configuration set up and is working normally. The platform is optional.

The examples use Bash/Zsh. `elierncn/aegisharness` is the planned public repository; remote commands become usable after its publication. For testing before publication or modifying the plugin, use [developer installation](#developer-installation).

This edition uses only the AegisHarness identifiers: `aegis@aegisharness-marketplace`, `/aegis:*`, `.aegisharness/`, `aegisharness.workspace.yaml`, and `AEGISHARNESS_*` environment variables. It does not recognize or migrate identifiers, configuration or runtime data from previous branding. Initialize a fresh application copy when validating this edition.

## Install by host

Choose your host and run the matching block. Each block is a complete install script;
marketplace-based hosts need no manual source clone. Replace the repository URL with
`$AEGISHARNESS_SOURCE` for [developer installation](#developer-installation).

### Codex

```bash
codex plugin marketplace add https://github.com/elierncn/aegisharness.git
codex plugin add aegis@aegisharness-marketplace
```

### Claude Code

```bash
claude plugin marketplace add https://github.com/elierncn/aegisharness.git
claude plugin install aegis@aegisharness-marketplace
```

### MiniMax Code (preview)

```bash
mcode plugin marketplace add https://github.com/elierncn/aegisharness.git
mcode plugin install aegis@aegisharness-marketplace
```

Commands are Skill projections in `hosts/minimax/skills/`. MiniMax Code also discovers
`~/.agents/skills/`, `~/.claude/skills/` and `~/.codex/skills/`.

### WorkBuddy / CodeBuddy (preview)

```bash
codebuddy plugin marketplace add https://github.com/elierncn/aegisharness.git
codebuddy plugin install aegis@aegisharness-marketplace
# Inside the host conversation, run /reload-plugins and open a new session.
```

Then open a new session and confirm the nine `/aegis:*` commands are visible.

### Qoder (preview)

```bash
qodercli plugin marketplace add https://github.com/elierncn/aegisharness.git
qodercli plugin install aegis@aegisharness-marketplace
```

The desktop client can register the same repository through its plugin marketplace.
After installation, confirm the nine commands and the `qoder.md` project instructions loaded.

### DeepSeek Harness / dsh (preview)

Requirements: Node.js 22.19+ (or 24+), npm/npx, Python 3.10+, Git. DSH is a
**developer preview** — check `--dump-config` rather than assuming a directory layout.

DSH has no plugin marketplace: `dsh plugin --profile <name> add <package>` forwards to
pnpm and requires an npm package with `package.json`. Our `.dsh-plugin/plugin.json` is a
declarative projection manifest, not an installable Cordis plugin. This release therefore
installs via DSH's native skill discovery plus the project `AGENTS.md` instruction file.

```bash
# 1) CLI
npm install -g @deepseek-ai/dsh

# 2) Source checkout
export AEGISHARNESS_SOURCE="https://github.com/elierncn/aegisharness.git"
git clone "$AEGISHARNESS_SOURCE" "$HOME/aegisharness"

# 3) Mount the nine Skill entrypoints (bundle layout: <name>/SKILL.md)
DSH_SKILLS="${DSH_HOME:-$HOME/.dsh}/skills"
mkdir -p "$DSH_SKILLS"
for c in init propose apply archive bug-fix ut update status config; do
  ln -sfn "$HOME/aegisharness/aegisharness/hosts/deepseek-dsh/skills/aegis-$c" \
    "$DSH_SKILLS/aegis-$c"
done

# 4) Inspect the composed profile, then restart into a new session
npx @deepseek-ai/dsh --profile web --dump-config
npx @deepseek-ai/dsh web
```

Project-scoped alternative: link the same nine directories into `<repo>/.dsh/skills/`.
DSH reads `<repo>/AGENTS.md` (`instructionFileCandidates` defaults to
`['AGENTS.md','CLAUDE.md']`) and `${DSH_HOME:-~/.dsh}/AGENTS.md` globally.

Skill names are kebab-case, so `/aegis:init` is triggered as `/aegis-init` in DSH.
Both spellings enter the same shared `commands/init.md` contract. Full mapping,
the `dsh plugin ... add <npm-package>` path (available only after publishing an npm
package), update and uninstall steps: [dsh installer](../aegisharness/hosts/deepseek-dsh/installer.md).

The repository root contains `.claude-plugin/marketplace.json`, whose `./aegisharness`
source points to the plugin. Each host reads its own native manifest
(`.codex-plugin/`, `.minimax-plugin/`, `.codebuddy-plugin/`, `.qoder-plugin/`,
`.dsh-plugin/`); see the [host support matrix](host-support-matrix.md). The platform
is not installed by these commands. Preview hosts do not install hooks, telemetry or
automatic updates.

### Bind the Host Context

When several host markers are present in the same terminal, set the host explicitly:

```bash
export AEGISHARNESS_PLATFORM=deepseek-dsh   # or codex / claude-code / minimax / workbuddy / qoder
python3 aegisharness/scripts/host_runtime_cli.py resolve --platform deepseek-dsh
```

`resolve` priority: explicit `--platform` → `AEGISHARNESS_PLATFORM` → host detector.
Unknown hosts fail closed; they never fall back to another Host Kit.

Sources: [OpenAI plugin packaging](https://developers.openai.com/plugins/build/plugins#marketplace-metadata), [Claude Code marketplaces](https://code.claude.com/docs/en/plugin-marketplaces), [DSH CLI commands](https://deepseekdsh.com/guides/commands). Host commands and trust screens can vary with client version; use a version providing the listed commands.

## Developer installation

Use local source when developing the plugin or testing before publication. Download or clone the source, then run the following from the combined repository root containing both `aegisharness/` and `aegisharness-platform/`:

```bash
export AEGISHARNESS_SOURCE="$(pwd)"
```

Then pick your host — one complete block per host:

```bash
# Codex
codex plugin marketplace add "$AEGISHARNESS_SOURCE"
codex plugin add aegis@aegisharness-marketplace
```

```bash
# Claude Code
claude plugin marketplace add "$AEGISHARNESS_SOURCE"
claude plugin install aegis@aegisharness-marketplace
```

```bash
# MiniMax Code (preview)
mcode plugin marketplace add "$AEGISHARNESS_SOURCE"
mcode plugin install aegis@aegisharness-marketplace
```

```bash
# WorkBuddy / CodeBuddy (preview)
codebuddy plugin marketplace add "$AEGISHARNESS_SOURCE"
codebuddy plugin install aegis@aegisharness-marketplace
# then run /reload-plugins inside the host conversation
```

```bash
# Qoder (preview)
qodercli plugin marketplace add "$AEGISHARNESS_SOURCE"
qodercli plugin install aegis@aegisharness-marketplace
```

```bash
# DeepSeek Harness / dsh (preview) — no marketplace, mount Skills directly
DSH_SKILLS="${DSH_HOME:-$HOME/.dsh}/skills"
mkdir -p "$DSH_SKILLS"
for c in init propose apply archive bug-fix ut update status config; do
  ln -sfn "$AEGISHARNESS_SOURCE/aegisharness/hosts/deepseek-dsh/skills/aegis-$c" \
    "$DSH_SKILLS/aegis-$c"
done
npx @deepseek-ai/dsh --profile web --dump-config
```

A standalone plugin copy can still use the absolute path to `aegisharness/`; its nested marketplace points to `.`. Register only one source under `aegisharness-marketplace` at a time. When switching sources, remove the old marketplace using the host's plugin management first.

## Verify installation

Open a new host session in the application repository you want to develop. Confirm the nine public commands: `init`, `propose`, `apply`, `archive`, `bug-fix`, `ut`, `update`, `status`, `config`.

Review and trust the plugin's hooks through the host's native interface. Confirm SessionStart identifies the host and installed plugin path. Command visibility alone does not prove hooks executed. Then run `/aegis:init`; check generated project hooks and project documentation before creating a feature. Repeated init should preserve unrelated host settings. For single-repository Init, required project files include nonempty `docs/harness/index.md`, `docs/knowledge/index.md` and `docs/knowledge/project-context.md`; also check the other outputs required for the detected project type. A final completion message is not a substitute for those checks.

If an entrypoint reports `plugin_source_mismatch`, its executing copy differs from the source bound to the session. Check the active marketplace and installed plugin, keep the intended source selected, and start a new session. Use resources from that installation; do not mix another checkout or cached version into the workflow.

## Updates

Run `/aegis:update` in the host conversation. The plugin checks the configured marketplace, shows an available update and uses the host adapter after authorization.

- **Git source:** the host refreshes the configured repository; use the same marketplace for later versions.
- **Local source:** update the source copy yourself first, then check for updates. The plugin does not pull an arbitrary local checkout automatically. If the copy was cloned, review its working tree and update it using your normal Git workflow.
- Start a new host session after updating; review changed hooks when the host requests it.


## Uninstall

Use the host's plugin management to uninstall `aegis@aegisharness-marketplace`. Generated project knowledge, requirements and business code are retained. Review project hook settings separately if you no longer want the host to invoke AegisHarness in that application repository.

## 中文说明

需要 Python 3.10+、Git，以及支持插件市场的受支持宿主之一（见[宿主支持矩阵](host-support-matrix.md)）。先确保宿主已完成登录或模型配置，能够正常使用。平台不是安装插件的前置条件。

正式发布后使用上面的 GitHub 安装命令，无需先手动克隆源码。发布前测试或修改插件时，使用[开发者安装（本地源码）](#developer-installation)：先下载或克隆源码，再从**包含两个子项目的根目录**添加本地市场。根市场指向 `./aegisharness`，不会安装平台。独立插件副本仍可添加插件目录本身；同名市场只保留一个来源。

安装后新开会话，确认九个命令可见、插件 hooks 已审阅并实际执行，再在业务仓库运行 `/aegis:init` 并检查项目 hooks。单仓 Init 还需检查非空的 `docs/harness/index.md`、`docs/knowledge/index.md`、`docs/knowledge/project-context.md` 及对应项目类型要求的其他产物，不能只看“已完成”回复。若出现 `plugin_source_mismatch`，先核对市场来源与当前安装插件，选定正确来源并新开会话，避免混用其他 checkout 或缓存版本。更新使用 `/aegis:update`；本地来源需先自行更新源码，不能把版本识别成功当作已完成跨版本升级。

DeepSeek Harness (dsh) 是例外：它处于 developer preview，没有插件市场，`dsh plugin ... add`
要求目标是 npm 包。当前版本通过软链 `hosts/deepseek-dsh/skills/aegis-*` 到
`${DSH_HOME:-~/.dsh}/skills/`、并由 `/aegis-init` 生成项目 `AGENTS.md` 完成安装；
Skill 名 kebab-case，`/aegis:<cmd>` 以 `/aegis-<cmd>` 触发。安装前用
`dsh --profile web --dump-config` 核对实际目录，更新后重启 DSH 并新开会话。
完整脚本见[按宿主安装](#install-by-host)与 dsh installer。
