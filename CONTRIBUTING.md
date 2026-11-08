# Contributing / 参与贡献

Bug reports, documentation improvements, tests and focused pull requests are welcome.

## Discuss and propose

Use [GitHub Issues](https://github.com/elierncn/aegisharness/issues) for reproducible bugs and feature proposals. You do not need to deploy aegisharness-platform to report an issue. Security issues follow [SECURITY.md](SECURITY.md).

Before a substantial behavior change, describe the problem, acceptance criteria and compatibility impact in an Issue. Work on a branch in your fork and open a PR against the repository's default branch. Keep each PR focused and include the verification commands and results. Maintainers review before merging; no CLA or DCO bot is configured in this source tree.

## Development environment

Use Python 3.10+ and Git. Follow the component's `AGENTS.md`.

```bash
# Repository root
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e './aegisharness-platform[server,dev]'

# Plugin behavior and host contracts
(cd aegisharness && python scripts/run_tests.py)

# Platform behavior and module boundaries
(cd aegisharness-platform && python -m pytest)
(cd aegisharness-platform && python -m ruff check web_ui eval bench evolution tests)
```

Tests must use synthetic data and mock paid model calls, external workers and network dependencies. Live agent acceptance requires your own model configuration and a disposable application repository. Do not put runtime output or credentials in a PR.

## Source boundaries

- `aegisharness/commands/`: nine public entrypoints: seven development commands plus `status` and `config`.
- `aegisharness/workflows/single/` and `workflows/workspace/`: workflow bodies.
- `aegisharness/skills/`, `agents/`, `hosts/`, `scripts/`: reusable methods, delegated roles, host adapters, deterministic runtime and tests.
- `aegisharness-platform/web_ui/`: composition and UI; `eval/`, `bench/`, `evolution/` remain independent modules.
- Root `.claude-plugin/marketplace.json`: combined-repository distribution, with source `./aegisharness`.

Keep generated host projections aligned when changing plugin commands or skills. Plugin tests belong in `aegisharness/scripts/tests/`. For platform UI changes, validate the real Demo page as well as relevant Web tests.

Plugin development references: [Host API](aegisharness/reference/host-api.md), [scan protocol](aegisharness/reference/scan-agent-protocol.md), [script exit codes](aegisharness/reference/script-exit-codes.md), [working directory rules](aegisharness/reference/skill-runtime-working-directory.md), [frontend loading](aegisharness/reference/frontend-loading.md), and [loading protocol](aegisharness/reference/loading-protocol.md).

To rebuild the platform stylesheet, use Node.js and run from `aegisharness-platform/`:

```bash
npx --yes tailwindcss@3.4.17 -c tailwind.config.js -i web_ui/assets/tailwind.css -o web_ui/static/css/tailwind.css --minify
```

## Releasing the npm bundle

The dsh plugin ships as `@elierncn/aegisharness-dsh`, published by
[`.github/workflows/publish-npm.yml`](.github/workflows/publish-npm.yml). Bump `version` in
`aegisharness/package.json`, commit, then push a matching tag:

```bash
git tag v1.0.0 && git push origin v1.0.0
```

The workflow prefers OIDC trusted publishing (no secret; configure a trusted publisher on the
package's npm settings page) and falls back to the repository secret `NPM_TOKEN` while the
package does not exist on npm yet — such a token must have "Bypass two-factor authentication"
enabled, or CI fails with `EOTP`. It runs the bundle self-check and `scripts/check_release.py`
before publishing, refuses to continue when the tag and `package.json` disagree, and verifies
the version is resolvable from the registry afterwards.

## PR checklist

- Explain the user-visible problem and resulting behavior.
- List relevant tests; distinguish local tests, Mock execution and real model verification.
- Update both language entry pages and the relevant guide when behavior changes.
- Keep unrelated files and generated runtime evidence out of the diff.
- Preserve third-party licenses and notices.

Unless explicitly stated otherwise, contributions intentionally submitted for inclusion are provided under [Apache-2.0](LICENSE). Follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## 中文说明

欢迎通过 GitHub Issue 提交问题、通过 PR 改进代码和文档；无需先部署平台。较大行为变更先说明问题、验收标准和兼容性影响。PR 面向仓库默认分支，保持单一目的，列出实际执行的验证命令和结果，并由维护者评审。

使用 Python 3.10+，按上面的命令准备环境并运行相关组件测试。工作流正文放在 `workflows/`，不要复制回 `commands/`；平台三个后端保持模块边界。示例与测试使用合成数据，不提交凭据、私有对话或运行产物。贡献按 Apache-2.0 提交，并遵守社区行为准则。

发布 dsh bundle 时，先改 `aegisharness/package.json` 的 `version` 并提交，再推同名 `v*` tag，由 `.github/workflows/publish-npm.yml` 发布。工作流优先走 OIDC 可信发布（无需 Secret，需在 npm 包设置页配好 Trusted Publisher）；包还没上 npm 时退回用仓库 Secret `NPM_TOKEN`，该 token 必须勾选「Bypass two-factor authentication」，否则 CI 会报 `EOTP`。
