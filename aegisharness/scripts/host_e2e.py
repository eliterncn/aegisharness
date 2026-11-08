#!/usr/bin/env python3
"""宿主级 E2E 验证：安装面、发现面、初始化产物与生命周期路由。

对指定宿主运行一组可自动化的端到端检查，并可把结果写成证据 JSON：
`evidence/host-e2e/<host_id>/<date>.json`，供 host.json 的 `support.evidence` 引用。

设计边界（不伪造结论）：
- 这里验证的是**宿主契约面**：清单/适配器解析、命令投影、Skill 发现布局、
  init 产物门禁、Propose→Apply→Archive 路由。这些都与具体模型无关。
- 需要真实产品会话的检查（模型在宿主 UI 里执行 `/aegis:*` 全链路）无法在此自动化。
  宿主 CLI 不可用时记为 `skip` 并在证据的 `not_verified` 中显式列出，绝不写成通过。
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

from host_runtime import HostContractError, HostManifest, HostRegistry
from host_runtime.command_projection import WORKFLOW_COMMANDS, load_command_projection
from host_runtime.project_config import load_project_config
from host_runtime.project_hooks import load_project_hooks
from project_hooks_cli import project_hooks
from source_binding import guard_source
import validate_init_outputs
import workflow_router

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PLUGIN_ROOT.parent
HOSTS_ROOT = PLUGIN_ROOT / "hosts"
EVIDENCE_ROOT = REPO_ROOT / "evidence" / "host-e2e"
EVIDENCE_SCHEMA_VERSION = "1.0"

# 宿主 CLI 的可执行文件名（用于可选的宿主侧版本核对）。
HOST_CLI_NAMES = {
    "codex": ("codex",),
    "claude-code": ("claude",),
    "minimax": ("mcode", "minimax"),
    "workbuddy": ("codebuddy", "mcode"),
    "qoder": ("qodercli", "qoder"),
    "deepseek-dsh": ("dsh",),
}

KEBAB = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class Check:
    """单个检查项的结果，status 只允许 pass / fail / skip。"""

    def __init__(self, name: str, status: str, detail: str, facts: dict[str, Any] | None = None) -> None:
        self.name = name
        self.status = status
        self.detail = detail
        self.facts = facts or {}

    def as_dict(self) -> dict[str, Any]:
        return {
            "check": self.name,
            "status": self.status,
            "detail": self.detail,
            "facts": self.facts,
        }


def _ok(name: str, detail: str, **facts: Any) -> Check:
    return Check(name, "pass", detail, facts)


def _fail(name: str, detail: str, **facts: Any) -> Check:
    return Check(name, "fail", detail, facts)


def _skip(name: str, detail: str, **facts: Any) -> Check:
    return Check(name, "skip", detail, facts)


def _run_check(name: str, fn: Callable[[], Check]) -> Check:
    """把检查内的异常收敛为该检查项的失败，不中断整轮。"""
    try:
        return fn()
    except (HostContractError, ValueError, OSError, KeyError) as exc:
        return _fail(name, f"{type(exc).__name__}: {exc}")


def _frontmatter(path: Path) -> dict[str, str]:
    """读取 SKILL.md 的简易 frontmatter（只取一级 key: value）。"""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    fields: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" in line and not line.startswith((" ", "\t", "-")):
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip().strip('"').strip("'")
    return fields


def _plugin_version() -> str:
    for candidate in (PLUGIN_ROOT / ".claude-plugin" / "plugin.json", PLUGIN_ROOT / "package.json"):
        if candidate.is_file():
            try:
                payload = json.loads(candidate.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            version = str(payload.get("version") or "").strip()
            if version:
                return version
    return "unknown"


def _write_scratch(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    return root


# --------------------------------------------------------------------------- 检查项


def check_registry(registry: HostRegistry, host_id: str) -> Check:
    manifest = registry.get(host_id)
    if manifest is None:
        return _fail("host.registry", f"Registry 未发现宿主 {host_id}")
    if manifest.host_id != host_id:
        return _fail("host.registry", f"别名解析到了 {manifest.host_id}，与请求的 {host_id} 不一致")
    aliases = sorted(manifest.aliases)
    for alias in aliases:
        if registry.get(alias) is not manifest:
            return _fail("host.registry", f"别名 {alias} 未指向同一清单")
    return _ok(
        "host.registry",
        f"清单已发现并通过校验（Host API {manifest.host_api_version}）",
        host_api_version=manifest.host_api_version,
        aliases=aliases,
        support_level=manifest.support_level,
        capabilities=dict(sorted(manifest.capabilities.items())),
    )


def check_adapters(manifest: HostManifest) -> Check:
    resources: list[str] = []
    python_adapters: list[str] = []
    for name in sorted(manifest.adapters):
        reference = manifest.require_adapter_reference(name)
        if reference.kind == "resource":
            path = manifest.resolve_resource_adapter(name)
            if not path.is_file():
                return _fail("host.adapters", f"资源适配器 {name} 指向的文件不存在: {path}")
            resources.append(name)
        elif reference.kind == "python":
            adapter = manifest.load_python_adapter(name)
            if not (callable(adapter) or hasattr(adapter, "__dict__")):
                return _fail("host.adapters", f"Python 适配器 {name} 不可调用")
            python_adapters.append(name)
    return _ok(
        "host.adapters",
        f"{len(resources)} 个资源适配器 + {len(python_adapters)} 个 Python 适配器全部解析成功",
        resources=resources,
        python_adapters=python_adapters,
    )


def check_context(manifest: HostManifest) -> Check:
    plugin_root = PLUGIN_ROOT.resolve()
    if manifest.root.parent.parent.resolve() != plugin_root:
        return _fail("host.context", "Host Kit 不在当前插件根内，存在多份 checkout 混用的风险")
    resolved: dict[str, str] = {}
    for name in sorted(manifest.adapters):
        reference = manifest.adapters[name]
        if reference.startswith("resource:"):
            resolved[name] = str(manifest.resolve_resource_adapter(name))
    outside = [f"{k}={v}" for k, v in resolved.items() if not Path(v).is_relative_to(plugin_root)]
    if outside:
        return _fail("host.context", "存在越出插件根的资源引用: " + ", ".join(outside))
    hooks = load_project_hooks(manifest)
    config = load_project_config(manifest)
    templates = {"entry_template": config.entry_template, "workspace_entry_template": config.workspace_entry_template}
    for label, relative in templates.items():
        candidates = [plugin_root / relative, manifest.root / relative]
        if not any(candidate.is_file() for candidate in candidates):
            return _fail("host.context", f"{label} 指向的模板不存在: {relative}")
    if not config.entry_file.strip():
        return _fail("host.context", "entry_file 为空，init 无法落地项目入口")
    return _ok(
        "host.context",
        f"插件根绑定正确；资源 {len(resolved)} 项全部位于插件根内",
        plugin_root=str(plugin_root),
        entry_file=config.entry_file,
        settings_file=config.settings_file,
        hooks_owner=hooks.owner,
        hooks_merge_strategy=hooks.merge_strategy,
    )


def check_projection(manifest: HostManifest) -> Check:
    projection = load_command_projection(manifest)
    if set(projection.entrypoints) != set(WORKFLOW_COMMANDS):
        return _fail("host.projection", "命令投影未完整覆盖九个公共命令")
    plugin_root = PLUGIN_ROOT.resolve()
    entries: dict[str, str] = {}
    for command in sorted(projection.entrypoints):
        entry, contract = projection.entrypoints[command]
        entry_path = (plugin_root / entry).resolve()
        contract_path = (plugin_root / contract).resolve()
        if not entry_path.is_file() or not contract_path.is_file():
            return _fail("host.projection", f"{command} 的入口或契约文件缺失")
        if not entry_path.is_relative_to(plugin_root) or not contract_path.is_relative_to(plugin_root):
            return _fail("host.projection", f"{command} 的入口或契约越出插件根")
        entries[command] = entry
    surface = projection.surface
    if surface == "native-command":
        commands_dir = PLUGIN_ROOT / "commands"
        canonical = sorted(p.name for p in commands_dir.glob("*.md"))
        expected = sorted(f"{command}.md" for command in WORKFLOW_COMMANDS)
        if canonical != expected:
            return _fail(
                "host.projection",
                f"commands/ 下的原生命令与公共契约不一致: {canonical} != {expected}",
            )
    return _ok(
        "host.projection",
        f"surface={surface}，九个命令入口与唯一公共契约全部命中",
        surface=surface,
        entries=entries,
    )


def check_discovery(manifest: HostManifest, scratch: Path) -> Check:
    """按宿主实际发现机制验证入口可被枚举，而不是只看文件存在。"""
    projection = load_command_projection(manifest)
    plugin_root = PLUGIN_ROOT.resolve()

    if projection.surface == "skill":
        skills_root = _write_scratch(scratch / "discovered-skills")
        discovered: dict[str, str] = {}
        for command in sorted(projection.entrypoints):
            entry, _ = projection.entrypoints[command]
            skill_file = plugin_root / entry
            if skill_file.name != "SKILL.md":
                return _fail("host.discovery", f"{command} 的入口不是 SKILL.md: {entry}")
            skill_dir = skill_file.parent
            target = skills_root / skill_dir.name
            if target.exists():
                return _fail("host.discovery", f"Skill 目录名重复: {skill_dir.name}")
            shutil.copytree(skill_dir, target)
            fields = _frontmatter(target / "SKILL.md")
            name = fields.get("name", "")
            if not name:
                return _fail("host.discovery", f"{skill_dir.name}/SKILL.md 缺少 frontmatter name")
            if not fields.get("description"):
                return _fail("host.discovery", f"{skill_dir.name}/SKILL.md 缺少 frontmatter description")
            if not KEBAB.match(name):
                return _fail("host.discovery", f"Skill 名不是 kebab-case: {name}")
            if name in discovered:
                return _fail("host.discovery", f"Skill 名重复: {name}")
            discovered[name] = entry
        if len(discovered) != len(WORKFLOW_COMMANDS):
            return _fail("host.discovery", f"可发现 Skill 数量为 {len(discovered)}，期望 {len(WORKFLOW_COMMANDS)}")
        return _ok(
            "host.discovery",
            f"复制到宿主 skills 目录后可枚举出 {len(discovered)} 个合法 Skill",
            surface="skill",
            skills_root=str(skills_root),
            discovered=sorted(discovered),
        )

    distribution = manifest.adapter_reference("distribution")
    if distribution is None or distribution.kind != "resource":
        return _fail("host.discovery", "native-command 宿主缺少 distribution 分发清单")
    manifest_path = manifest.resolve_resource_adapter("distribution")
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return _fail("host.discovery", f"分发清单不可解析: {exc}")
    commands = sorted((PLUGIN_ROOT / "commands").glob("*.md"))
    if len(commands) != len(WORKFLOW_COMMANDS):
        return _fail("host.discovery", f"commands/ 下有 {len(commands)} 个文件，期望 {len(WORKFLOW_COMMANDS)}")
    repo_manifest = REPO_ROOT / manifest_path.relative_to(PLUGIN_ROOT)
    return _ok(
        "host.discovery",
        f"分发清单可解析，{len(commands)} 个原生命令文件就位",
        surface="native-command",
        distribution=str(manifest_path.relative_to(REPO_ROOT)),
        distribution_root_copy=repo_manifest.is_file(),
        plugin_keys=sorted(payload)[:12],
    )


def check_init(manifest: HostManifest, scratch: Path) -> Check:
    config = load_project_config(manifest)
    root = _write_scratch(scratch / "init-project")
    (root / config.entry_file).parent.mkdir(parents=True, exist_ok=True)
    (root / config.entry_file).write_text(f"# {config.entry_file}\n\nInitialized by host_e2e.\n", encoding="utf-8")
    for directory in validate_init_outputs.SERVICE_COMMON_DIRS:
        (root / directory).mkdir(parents=True, exist_ok=True)
    for relative in validate_init_outputs.SERVICE_COMMON_FILES:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("Initialized.\n", encoding="utf-8")
    (root / "docs/knowledge/service-meta.yaml").write_text("service: demo\n", encoding="utf-8")

    # init 的 hooks 安装步骤：声明了 settings_file 的宿主必须真的能合并并自校验。
    hooks_result: dict[str, Any] | None = None
    if config.settings_file is not None:
        hooks_result = project_hooks(root, manifest.host_id, "merge")
        if hooks_result.get("status") not in {"merged"}:
            return _fail("project.init", f"project hooks 合并失败: {hooks_result}")
        check_result = project_hooks(root, manifest.host_id, "check")
        if check_result.get("status") != "pass":
            return _fail("project.init", f"合并后 project hooks 自校验未通过: {check_result}")

    report = validate_init_outputs.validate(root, "service", manifest.host_id, "disabled")
    if report["status"] != "pass":
        errors = "; ".join(f"{item['check']}:{item['detail']}" for item in report["errors"]) or "unknown"
        return _fail("project.init", f"init 产物门禁未通过: {errors}")
    failed_hooks = [item for item in report["checks"] if item["check"] == "project_hooks" and item["status"] != "pass"]
    if failed_hooks:
        return _fail("project.init", "project_hooks 检查未通过: " + failed_hooks[0]["detail"])
    return _ok(
        "project.init",
        f"init 产物门禁通过（entry={config.entry_file}，{len(report['checks'])} 项检查）",
        entry_file=config.entry_file,
        settings_file=config.settings_file,
        hooks_merged=bool(hooks_result and hooks_result.get("status") == "merged"),
        hooks_changed=bool(hooks_result and hooks_result.get("changed")),
        checks=len(report["checks"]),
        warnings=[item["detail"] for item in report["warnings"]],
    )


def _feature_repo(root: Path, status: str) -> Path:
    feature = root / "docs/specs/active/demo"
    feature.mkdir(parents=True, exist_ok=True)
    (feature / "spec.md").write_text(
        f"---\nfeature: demo\nexecution_scope: single\nstatus: {status}\n---\nDemo spec\n",
        encoding="utf-8",
    )
    (feature / "tasks.md").write_text("---\nfeature: demo\n---\nDemo tasks\n", encoding="utf-8")
    return root


def check_workflow(manifest: HostManifest, scratch: Path) -> Check:
    staged: dict[str, str] = {}
    for status, expected_stage in (("planning", "propose"), ("ready", "apply"), ("applying", "apply")):
        root = _feature_repo(_write_scratch(scratch / f"route-{status}"), status)
        code, result = workflow_router.route(root, command="propose", arguments="demo --loop")
        if code != 0:
            return _fail("workflow.route", f"status={status} 时路由返回 {code}: {result}")
        stage = result.get("stage")
        if stage != expected_stage:
            return _fail("workflow.route", f"status={status} 路由到 {stage}，期望 {expected_stage}")
        if result.get("execution_scope") != "single":
            return _fail("workflow.route", f"status={status} 执行范围判定错误: {result.get('execution_scope')}")
        staged[status] = stage

    guard_root = _write_scratch(scratch / "route-guard")
    blocked: dict[str, int] = {}
    for arguments in ("../escape request", "demo request --lite", "demo request --fusion"):
        code, _ = workflow_router.route(guard_root, command="propose", arguments=arguments)
        blocked[arguments] = code
    unsafe = {key: value for key, value in blocked.items() if value == 0}
    if unsafe:
        return _fail("workflow.route", f"不安全参数未被拦截: {sorted(unsafe)}")

    return _ok(
        "workflow.route",
        "Propose→Apply 路由按 spec 状态推进，不安全参数全部拦截",
        stages=staged,
        blocked=blocked,
    )


def check_bundle(manifest: HostManifest) -> Check:
    """宿主以原生 npm bundle 分发时，验证包清单、patch 层与插件模块自检。"""
    distribution = manifest.adapter_reference("distribution")
    if distribution is None or distribution.kind != "resource":
        return _skip("host.bundle", "该宿主不通过 npm bundle 分发")
    manifest_path = manifest.resolve_resource_adapter("distribution")
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return _skip("host.bundle", f"分发清单不是 npm 包清单: {exc}")
    bundle = (payload.get("dsh") or {}).get("bundle") if isinstance(payload, dict) else None
    if not isinstance(bundle, dict):
        return _skip("host.bundle", "该宿主不使用 dsh bundle 分发")

    package_root = manifest_path.parent
    patch_rel = str(bundle.get("patch") or "")
    if not patch_rel:
        return _fail("host.bundle", "bundle 未声明 patch 层")
    patch = package_root / patch_rel
    if not patch.is_file():
        return _fail("host.bundle", f"bundle patch 缺失: {patch_rel}")
    patch_text = patch.read_text(encoding="utf-8")
    package_name = str(payload.get("name") or "")
    if package_name not in patch_text:
        return _fail("host.bundle", f"patch 未挂载包自身: {package_name}")
    exports = {str(key).lstrip("./") for key in (payload.get("exports") or {})}
    if patch_rel.lstrip("./") not in exports:
        return _fail("host.bundle", f"patch 未导出: {patch_rel}")

    node = shutil.which("node")
    if node is None:
        return _skip(
            "host.bundle",
            f"bundle 清单与 patch 层有效（{package_name}），但未找到 node，跳过模块自检",
            package=package_name,
            version=payload.get("version"),
            patch=patch_rel,
        )
    smoke = package_root / "tests" / "dsh-plugin.test.mjs"
    if not smoke.is_file():
        return _fail("host.bundle", "缺少 tests/dsh-plugin.test.mjs 模块自检")
    completed = subprocess.run(
        [node, str(smoke)],
        cwd=str(package_root),
        capture_output=True,
        text=True,
        timeout=180,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip().splitlines()
        return _fail("host.bundle", "模块自检失败: " + (detail[-1] if detail else "unknown"))
    return _ok(
        "host.bundle",
        f"bundle 清单与 patch 层有效，模块自检注册九个 Skill（{package_name}@{payload.get('version')}）",
        package=package_name,
        version=payload.get("version"),
        patch=patch_rel,
        smoke=completed.stdout.strip()[-60:],
    )


def check_cli(manifest: HostManifest, cli_override: str | None) -> Check:
    candidates: list[str] = []
    if cli_override:
        candidates.append(cli_override)
    candidates.extend(HOST_CLI_NAMES.get(manifest.host_id, ()))
    for candidate in candidates:
        resolved = shutil.which(candidate) or (candidate if Path(candidate).is_file() else None)
        if not resolved:
            continue
        try:
            completed = subprocess.run(
                [resolved, "--version"],
                capture_output=True,
                text=True,
                timeout=90,
                env={**os.environ, "NO_COLOR": "1"},
            )
        except (OSError, subprocess.SubprocessError) as exc:
            return _skip("host.cli", f"宿主 CLI 无法执行: {type(exc).__name__}", cli=resolved)
        output = (completed.stdout or completed.stderr or "").strip().splitlines()
        version = output[0][:120] if output else ""
        if completed.returncode != 0:
            return _skip("host.cli", f"宿主 CLI 返回 {completed.returncode}，无法核对版本", cli=resolved)
        return _ok("host.cli", f"宿主 CLI 可用: {version}", cli=resolved, version=version)
    return _skip(
        "host.cli",
        "未找到该宿主的 CLI，无法做宿主侧版本核对（不影响契约面检查）",
        searched=candidates,
    )


# --------------------------------------------------------------------------- 证据


def _now() -> str:
    return _dt.datetime.now().astimezone().isoformat(timespec="seconds")


def run(host_id: str, scratch: Path, cli_override: str | None) -> dict[str, Any]:
    registry = HostRegistry.discover(HOSTS_ROOT)
    manifest = registry.get(host_id)
    if manifest is None:
        return {
            "schema_version": EVIDENCE_SCHEMA_VERSION,
            "host_id": host_id,
            "generated_at": _now(),
            "status": "fail",
            "checks": [_fail("host.registry", f"未知宿主: {host_id}，且不会回退").as_dict()],
            "summary": {"pass": 0, "fail": 1, "skip": 0},
            "verified": [],
            "not_verified": [],
        }

    scratch = scratch / manifest.host_id
    scratch.mkdir(parents=True, exist_ok=True)
    checks = [
        _run_check("host.registry", lambda: check_registry(registry, manifest.host_id)),
        _run_check("host.adapters", lambda: check_adapters(manifest)),
        _run_check("host.context", lambda: check_context(manifest)),
        _run_check("host.projection", lambda: check_projection(manifest)),
        _run_check("host.discovery", lambda: check_discovery(manifest, scratch)),
        _run_check("host.bundle", lambda: check_bundle(manifest)),
        _run_check("project.init", lambda: check_init(manifest, scratch)),
        _run_check("workflow.route", lambda: check_workflow(manifest, scratch)),
        _run_check("host.cli", lambda: check_cli(manifest, cli_override)),
    ]
    counts = {"pass": 0, "fail": 0, "skip": 0}
    for item in checks:
        counts[item.status] += 1
    status = "fail" if counts["fail"] else "pass"

    verified = [item.name for item in checks if item.status == "pass"]
    not_verified = [item.name for item in checks if item.status != "pass"]
    if any(item.name == "host.cli" and item.status == "skip" for item in checks):
        not_verified.append("host.session: 真实产品会话内的模型执行（需人工抽样）")

    return {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "host_id": manifest.host_id,
        "display_name": manifest.display_name,
        "support_level_at_run": manifest.support_level,
        "generated_at": _now(),
        "plugin": {"version": _plugin_version(), "root": str(PLUGIN_ROOT)},
        "environment": {
            "python": platform.python_version(),
            "platform": f"{platform.system()} {platform.release()}",
            "host_cli": next(
                (item.facts.get("version") for item in checks if item.name == "host.cli" and item.status == "pass"),
                None,
            ),
        },
        "status": status,
        "checks": [item.as_dict() for item in checks],
        "summary": counts,
        "verified": verified,
        "not_verified": not_verified,
    }


def write_evidence(report: dict[str, Any]) -> Path:
    host_id = report["host_id"]
    directory = EVIDENCE_ROOT / host_id
    directory.mkdir(parents=True, exist_ok=True)
    stamp = report["generated_at"][:10]
    path = directory / f"{stamp}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


LIMITATION_RETIRED = (
    "未经官方 E2E 验证，支持等级为 preview。",
)


def promote(host_id: str, evidence: Path) -> str:
    """在全部自动化检查通过后把宿主升为 stable 并引用证据。"""
    manifest_path = HOSTS_ROOT / host_id / "host.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    support = payload.setdefault("support", {})
    relative = evidence.relative_to(REPO_ROOT).as_posix()
    support["level"] = "stable"
    support["evidence"] = relative
    limitations = [item for item in support.get("limitations", []) if item not in LIMITATION_RETIRED]
    limitations.append(
        "已通过 host_e2e.py 宿主契约面 E2E（清单/适配器/投影/发现/init 门禁/生命周期路由），"
        "证据见 support.evidence；宿主 UI 内的模型执行仍需按发布节奏抽样复核。"
    )
    support["limitations"] = limitations
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return relative


def main(argv: list[str] | None = None) -> int:
    guard_source(PLUGIN_ROOT)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", help="宿主 ID 或别名；与 --all 二选一")
    parser.add_argument("--all", action="store_true", help="对 Registry 中所有宿主依次执行")
    parser.add_argument("--record", action="store_true", help="把结果写入 evidence/host-e2e/<host>/<date>.json")
    parser.add_argument("--promote", action="store_true", help="全部检查通过后把 host.json 升为 stable 并引用证据")
    parser.add_argument("--cli", help="显式指定宿主 CLI 可执行文件，用于版本核对")
    parser.add_argument("--scratch", help="临时目录（默认在系统临时目录下建立）")
    parser.add_argument("--json", action="store_true", help="输出完整 JSON 而不是摘要")
    args = parser.parse_args(argv)

    registry = HostRegistry.discover(HOSTS_ROOT)
    if args.all:
        host_ids = list(registry.supported_ids())
    elif args.host:
        manifest = registry.get(args.host)
        if manifest is None:
            print(json.dumps({"status": "fail", "reason": f"unknown_host:{args.host}"}, ensure_ascii=False))
            return 2
        host_ids = [manifest.host_id]
    else:
        parser.error("需要 --host 或 --all")

    reports: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="aegis-host-e2e-") as temporary:
        scratch = Path(args.scratch) if args.scratch else Path(temporary)
        for host_id in host_ids:
            report = run(host_id, scratch, args.cli)
            if args.record or args.promote:
                evidence = write_evidence(report)
                report["evidence"] = str(evidence.relative_to(REPO_ROOT))
                if args.promote:
                    if report["status"] == "pass" and report["summary"]["fail"] == 0:
                        report["promoted_to"] = promote(host_id, evidence)
                    else:
                        report["promoted_to"] = None
                        report["promote_blocked"] = "存在失败检查项，拒绝升级"
            reports.append(report)

    if args.json:
        print(json.dumps(reports if args.all else reports[0], ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"AegisHarness host E2E · plugin {_plugin_version()} · {_now()}")
        failed = 0
        for report in reports:
            counts = report["summary"]
            print(f"\n{report['host_id']:<14} {report['status'].upper():<5} "
                  f"pass={counts['pass']} fail={counts['fail']} skip={counts['skip']}")
            for item in report["checks"]:
                print(f"  [{item['status']:<4}] {item['check']:<16} {item['detail'][:96]}")
            if report.get("evidence"):
                print(f"  evidence: {report['evidence']}")
            if report.get("promoted_to"):
                print(f"  promoted: stable · evidence={report['promoted_to']}")
            if report.get("promote_blocked"):
                print(f"  promote blocked: {report['promote_blocked']}")
            failed += counts["fail"]
        print(f"\n{'PASSED' if failed == 0 else 'FAILED'} · {len(reports)} host(s)")
    return 0 if all(report["status"] == "pass" for report in reports) else 1


if __name__ == "__main__":
    raise SystemExit(main())
