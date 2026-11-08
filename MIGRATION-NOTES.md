# AegisHarness 改造说明

本仓库是公司标准研发工具 **AegisHarness**，由 Apache-2.0 上游项目派生并重构。
本文说明改了什么、如何验证、哪些能力有边界、发布前还需做什么。

---

## 1. 品牌与标识

全仓（代码、配置、命令、文档、目录名、文件名）统一改名，**产品侧已无上游品牌标识**：

| 上游 | 公司标准 |
| --- | --- |
| `HelixHarness` / `helixharness` / `HELIXHARNESS` | `AegisHarness` / `aegisharness` / `AEGISHARNESS` |
| 命令 `/helix:*`、插件 ID `helix@...` | `/aegis:*`、`aegis@aegisharness-marketplace` |
| `helixharness.workspace.yaml`、`~/.helixharness/` | `aegisharness.workspace.yaml`、`~/.aegisharness/` |
| 环境变量 `HELIXHARNESS_*` | `AEGISHARNESS_*` |
| `github.com/didi/helixharness` | `github.com/elierncn/aegisharness` |
| 目录 `helixharness/`、`helixharness-platform/` | `aegisharness/`、`aegisharness-platform/` |

品牌叙事重写为"Aegis = 守护之盾"，去掉上游的 DNA 双螺旋双关。
共 340 个文本文件被改写，所有目录/文件名同步重命名。

**合规例外**：各 `NOTICE` 中的上游版权行与 `ATTRIBUTION.md` 的来源链接按
Apache-2.0 §4(c)/4(d) 原样保留。这些是法律归属声明，不是产品标识。详见
[ATTRIBUTION.md](ATTRIBUTION.md)。

含上游品牌文字的 4 张平台截图与 1 张内嵌证据闭环图已处理：README 改为文字说明，
证据闭环图重绘为 `evolution-evidence-loop.svg`，原 PNG 覆盖为空白占位图（发布前可删除）。

## 2. 多宿主支持

原项目用清单驱动的 Host API 1.1，Registry 扫描 `hosts/*/host.json`，**核心代码没有平台分支**。
本次保留 Codex / Claude Code 两个 stable Kit，新增四个 preview Kit，共 6 个宿主：

| Host ID | 产品 | 等级 | 命令表面 | 分发清单 |
| --- | --- | --- | --- | --- |
| `claude-code` | Claude Code | stable | native-command | `.claude-plugin/marketplace.json` |
| `codex` | Codex | stable | skill | `.codex-plugin/plugin.json` |
| `minimax` | MiniMax Code | preview | skill | `.minimax-plugin/plugin.json` |
| `workbuddy` | WorkBuddy / CodeBuddy | preview | native-command | `.codebuddy-plugin/plugin.json` |
| `qoder` | Qoder | preview | native-command | `.qoder-plugin/plugin.json` |
| `deepseek-dsh` | DeepSeek Harness (dsh) | preview | skill | `package.json` + `cordis.patch.yml`（原生 npm bundle） |

每个新 Host Kit 都包含完整的 `host.json` + 11 个必需资源适配器 + 命令投影 +
原生分发清单 + 安装器。Registry `list` 已校验通过。

新增的可扩展能力：

- `scripts/update_hosts/generic.py`：四个保守的宿主 detector（显式运行时标记才触发，
  preview 分值 70 低于 stable 的 100，避免混合环境误判）。
- `scripts/check_release.py`：不依赖临时目录的发布前一致性检查。
- `scripts/host_e2e.py`：宿主级端到端校验器，八项检查 + 证据记录 + 升级辅助。
- `docs/host-support-matrix.md`：能力矩阵、别名、安装速查、Host Context 绑定。
- `docs/add-new-host.md`：新增宿主标准接入规范（7 步流程、契约字段、投影规则、
  `unsupported` 判定标准、dsh npm bundle 契约、验证清单）。
- `docs/host-kit-template/`：可复制的 Host Kit 骨架。

**共享核心零改动**：`commands/`、`workflows/`、`skills/`、`metrics.py`、`version_update.py`、
Registry 控制流都没有加 `if <platform>` 分支——新增宿主是纯配置级变更。

### preview 宿主的诚实边界

MiniMax Code / WorkBuddy / Qoder / DeepSeek Harness (dsh) 对 `telemetry`、`plugin_update`、`session_start`、
`session_events`、`session_end`、`project_hooks` 声明为 **`unsupported`**：
不注册插件级 hook、不写宿主设置文件、不采集遥测、不自动升级，也不借用其他宿主资源。
九个 `/aegis:*` 命令与 Propose → Apply → Archive 生命周期由公共命令显式记账，
**与这些能力无关，全部可用**。

插件升级在这些宿主上走宿主原生插件管理；混合环境用
`export AEGISHARNESS_PLATFORM=<host-id>` 显式绑定。

## 3. 验证结果

```bash
cd aegisharness/aegisharness/scripts
python3 check_release.py
python3 host_runtime_cli.py list
python3 host_runtime_cli.py resolve --platform deepseek-dsh
python3 host_e2e.py --all
```

| 检查 | 结果 |
| --- | --- |
| JSON 清单解析（全仓） | PASS |
| Python 源码编译（全仓） | PASS |
| Host Kit 契约（manifest / 11 资源 / 命令投影 / 项目配置 / hooks） | PASS（6 个宿主） |
| 分发清单 | PASS |
| 原生插件 bundle（`dsh.bundle.patch` / `exports` / `files` 覆盖） | PASS（`@eliterncn/aegisharness-dsh@1.0.0`） |
| 宿主 E2E 证据（`support.evidence` 一致性） | PASS（两个 stable 宿主） |
| CI 发布工作流（工作流引用了 bundle 名与 `NPM_TOKEN`、`publishConfig.access=public`） | PASS（`publish-npm.yml`） |
| 品牌残留（排除法律署名文件） | PASS |
| 文档链接 | PASS |
| `host_runtime_cli.py list` | `["claude-code","codex","deepseek-dsh","minimax","qoder","workbuddy"]` |
| `resolve --platform` 六个宿主 | 全部 `resolved` |
| `host_e2e.py --all` | `PASSED · 6 host(s)`，每宿主 7 pass / 0 fail / 2 skip |
| detector 自动识别 + `AEGISHARNESS_PLATFORM` 显式覆盖 | PASS |

同时把 `test_public_workflow_router.py` 的宿主集合断言改成**动态校验**
（每个有清单的目录都必须被发现、每个宿主的投影覆盖九个命令），以后新增宿主不会再破坏测试。

> `run_tests.py` 完整套件在干净终端跑 **366 项全绿**（约 110 秒）：
> `env -u PYTHONPATH -u NODE_OPTIONS python3 scripts/run_tests.py`。
> 宿主 shim 会拦截 Python 的 `tempfile`、`ps` 与 Node 侧的 `mkdirSync`/`unlink`，
> 这两条环境变量就是唯一的绕过方式；CI 中不需要它们。

## 4. 待办与完成状态

- [x] 把 `NOTICE`（4 份）里的 `<Your Company>` 换成公司法定名称 —— 已填为 `elierncn`，
      与上游 `Copyright 2026 DiDi Financial and HelixHarness contributors` 并列保留。
- [x] 把仓库地址占位换成实际地址 —— 已统一为 `github.com/elierncn/aegisharness`。
- [x] 删除 [ATTRIBUTION.md](ATTRIBUTION.md) 列出的 5 个占位 PNG。
- [x] 宿主 E2E 自动化 —— 新增 `scripts/host_e2e.py`，八项检查覆盖清单解析、适配器、
      插件根绑定、命令投影、发现布局、npm bundle 自检、init 产物门禁与生命周期路由；
      六个宿主全部通过，`--record` 可把结果写成 `evidence/host-e2e/<host>/<date>.json`
      并供 `host.json` 的 `support.evidence` 引用。
- [x] 干净环境跑完整测试 —— `env -u PYTHONPATH -u NODE_OPTIONS python3 scripts/run_tests.py`：
      366 项全绿。
- [x] preview 宿主的 telemetry / plugin_update 适配器 —— **决定保持 `unsupported`**：
      这些宿主没有可订阅的会话事件与插件升级回调，伪造采集会绕开
      `telemetry_consent.py` 的同意记录。判定标准见
      [新增宿主指南](docs/add-new-host.md)。
- [ ] 真实产品会话内的模型执行抽样（minimax / workbuddy / qoder / deepseek-dsh）：
      需在装了对应产品并完成登录的机器上跑一遍 `/aegis:init` → `propose` → `apply` → `archive`，
      然后 `python3 scripts/host_e2e.py --host <id> --record --promote` 升为 `stable`。
- [ ] 发布 npm 包。两条路径任选：
      ① 本机 `cd aegisharness && npm publish --access public --otp=<验证码>`
      （账号开了 2FA，交互发布必须带一次性验证码）；
      ② 推 `v*` tag，由 `.github/workflows/publish-npm.yml` 自动发布：首版用仓库 Secret
      `NPM_TOKEN`（需勾 `Bypass 2FA`），发成功后配 Trusted Publisher 切到 OIDC 并删掉 Secret。
      **当前状态**：本机 `~/.npmrc` 里的 40 字符 legacy token 已被 npm 全面下线（`whoami` 401）；
      新账号 `elitern` 的 granular token 权限正常但**未勾 `Bypass 2FA`**，`npm publish` 报 `EOTP`。

## 5. 日常使用

命令、工作流、知识沉淀方式与原项目一致，只是命名空间换成 `/aegis:*`：

```text
/aegis:init
/aegis:propose task-filter ./requirements/task-filter.md --loop
/aegis:status task-filter
```

完整使用文档见 [docs/user-guide.zh-CN.md](docs/user-guide.zh-CN.md)，
宿主选择见 [docs/host-support-matrix.md](docs/host-support-matrix.md)。

## 6. 增量：新增 DeepSeek Harness (dsh) 宿主

在 5 宿主版本之上追加第六个 Host Kit，仍为纯配置级变更（共享核心零改动）：

- `hosts/deepseek-dsh/`：`host.json` + 11 个必需资源 + 命令投影（surface `skill`）+ 九个
  `skills/aegis-*/SKILL.md` 薄入口 + `installer.md`（含完整安装脚本）。
- ~~`.dsh-plugin/plugin.json`~~：已在第 7 节改为原生 npm bundle 后删除。
- `scripts/update_hosts/generic.py` 增加 `detect_deepseek_dsh`（标记 `DSH_SESSION` /
  `DSH_PROFILE` / `DSH_PLUGIN_ROOT` / `DSH_HOME`）。
- README（中/英）与 `docs/installation.md` 的安装章节改为**每个宿主一段完整可复制安装脚本**。

### dsh 的诚实边界

DSH 处于 developer preview，没有插件市场：`dsh plugin --profile <name> add <package>` 转发给
pnpm，要求目标是含 `package.json` 的 npm 包。因此 dsh 改为原生 npm 插件（见第 7 节），
不再使用声明清单。Skill 名只接受 kebab-case，`/aegis:<cmd>` 在本宿主以 `/aegis-<cmd>` 触发，
两者进入同一份公共契约。

`telemetry`、`plugin_update`、会话 hooks、`project_hooks` 仍为 `unsupported`；
`support.level` 保持 `preview`，未经官方 E2E。

## 7. 增量：dsh 改为原生 npm 插件

上一版把 dsh 当作「声明清单 + skills 软链」，现在改成宿主原生插件：

| 文件 | 作用 |
| --- | --- |
| `aegisharness/package.json` | 包名 `@eliterncn/aegisharness-dsh`；`dsh.bundle.patch` → `./cordis.patch.yml`；`exports` 同时导出模块与 patch |
| `aegisharness/cordis.patch.yml` | `insert` 一个条目：`id: aegisharness`、`name: '@eliterncn/aegisharness-dsh'` |
| `aegisharness/lib/index.js` | Cordis 插件（`name` / `inject: ['skills']` / `apply`）：读取 `hosts/deepseek-dsh/skills/aegis-*/SKILL.md`，把正文里的插件根改写成安装后绝对路径，再 `ctx.skills.register()` 注册九个运行时 Skill（`source: bundled`、`resourceBase` 指向包根） |
| `aegisharness/tests/dsh-plugin.test.mjs` | 离线自检：无 dsh、无网络，断言九个 Skill、kebab-case、绝对路径与 patch 一致性 |
| `aegisharness/scripts/tests/test_dsh_plugin_module.py` | 把上面这份自检接进统一测试入口 |
| `hosts/deepseek-dsh/host.json` | `distribution` 改为 `resource:package.json`，`.dsh-plugin/` 两份声明清单删除 |

README（中/英）、`docs/installation.md`、`docs/host-support-matrix.md`、
`docs/add-new-host.md` 与 `installer.md` 全部改为一条安装命令：
`dsh plugin --profile <name> add @eliterncn/aegisharness-dsh`。

### 本地实测（dsh 0.2.2-rc.1）

```bash
npm pack                 # @eliterncn/aegisharness-dsh-1.0.0.tgz，705 KB / 341 文件
dsh plugin --profile web add file:.../eliterncn-aegisharness-dsh-1.0.0.tgz
dsh --profile web --dump-config | grep -A1 aegisharness
dsh plugin --profile web remove @eliterncn/aegisharness-dsh
```

- 安装后 profile `package.json` 的 `dsh.profile.bundles` **自动**追加 `@eliterncn/aegisharness-dsh`，
  不需要手改清单；
- 组合树出现 `- id: aegisharness` / `name: '@eliterncn/aegisharness-dsh'`；
- 卸载命令可干净回退（包与 bundles 条目一起移除）；
- `--dump-config-schema` 在本插件存在与不存在时报同样的 4 条 web-profile 既有错误，
  说明这些错误与本插件无关。

### 发布与后续

`npm publish` 需要有效的 npm 凭据。当前机器上的 `~/.npmrc` 只有一个 40 字符的 legacy token，
用它对 `registry.npmjs.org` 调 `GET /-/whoami` 返回 **401**，因此本仓库无法自动发布。
包名 `@eliterncn/aegisharness-dsh` 在公共 registry 上仍为 **404（未被占用）**，可用。

手动发布（一次性）：

```bash
cd aegisharness/aegisharness
npm login              # 或 npm config set //registry.npmjs.org/:_authToken=<新 token>
npm whoami             # 必须打印出你的用户名
npm publish --access public
```

`--access public` 对 scoped 包是必需的，否则默认按私有包发布（需要付费槽位）。

### 用 GitHub Actions 发布（推荐，本机不必登录 npm）

`.github/workflows/publish-npm.yml` 把上面那串命令搬到了 CI，**两种鉴权自动切换**：

- **OIDC 可信发布（首选，不需要任何 Secret）**：npm 通过 OIDC 校验「这次发布确实来自
  本仓库的这个 workflow」，签发短期凭据。需要 npm CLI ≥ 11.5.1、GitHub 托管 runner、
  public 仓库，以及在 npm 包设置页配好的 Trusted Publisher。
- **`NPM_TOKEN`（首版引导用）**：包还不存在于 npm 上时无法配置 Trusted Publisher，
  这时用 granular token 发首版。**必须勾选 `Bypass two-factor authentication`**，
  否则 CI 里会报 `EOTP`（CI 没法输入动态验证码）。

其他要点：

- **触发**：推 `v*` tag（如 `v1.0.0`），或在 Actions 页手动 Run 并填 `version`；
- **发布前门禁**：`node tests/dsh-plugin.test.mjs` + `python3 scripts/check_release.py`，
  任一失败即中止；tag 与 `aegisharness/package.json` 的 `version` 不一致也直接失败；
- **provenance**：`npm publish --provenance`，npm 页面会链回本次 commit；
- **发布后自检**：轮询 `npm view @eliterncn/aegisharness-dsh@<version>` 直到 registry 可解析，
  避免「发布了但装不上」；
- **不要给 `setup-node` 加 `registry-url`**：它会写一个 `_authToken` 为空的 `.npmrc`，
  空凭据会挡住 OIDC 发布。`check_release.py` 的 CI 检查会拦这种写法。

从 token 切到 OIDC 的顺序（首版发布成功后）：

1. 打开 `https://www.npmjs.com/package/@eliterncn/aegisharness-dsh` → Settings →
   Trusted Publisher → Add → **GitHub Actions**；
2. 填 `elierncn` / `aegisharness` / `publish-npm.yml`（只填文件名，带 `.yml`）；
3. **Allowed actions 里必须勾上 `npm publish`**——新建配置默认只允许 stage publish，
   不勾就只会把版本暂存，不会真正发布；
4. 回仓库删掉 `NPM_TOKEN` Secret，之后打 tag 走纯 OIDC。

发一版：

```bash
# 先改 aegisharness/package.json 的 version，提交后打同名 tag
git tag v1.0.0 && git push origin v1.0.0
```

发布后安装命令对外可用：

```bash
dsh plugin --profile web add @eliterncn/aegisharness-dsh
```

在此之前用本地路径走同一条原生路径：
`dsh plugin --profile web add "file:/abs/path/to/aegisharness/aegisharness"`。

`support.level` 仍为 `preview`：插件挂载与 Skill 注册已实测，但 `dsh web` 内的真实模型会话
（需要模型凭据）尚未跑过。补齐后一条命令即可升级：
`python3 scripts/host_e2e.py --host deepseek-dsh --record --promote`。
