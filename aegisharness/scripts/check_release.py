#!/usr/bin/env python3
"""Release consistency checks that do not depend on temp directories.

Validates JSON manifests, Python syntax, Host Kit contracts, command
projections, distribution manifests, native plugin bundles, host E2E evidence,
CI publish workflows, branding residue and documentation links.
Run from anywhere:

    python3 scripts/check_release.py

Exit status is 0 only when every check passes.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from host_runtime import HostContractError, HostRegistry
from host_runtime.command_projection import load_command_projection
from host_runtime.project_config import load_project_config
from host_runtime.project_hooks import load_project_hooks

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PLUGIN_ROOT.parent
HOSTS_ROOT = PLUGIN_ROOT / "hosts"

EXPECTED_COMMANDS = frozenset(
    {"init", "propose", "apply", "archive", "bug-fix", "ut", "update", "status", "config"}
)
REQUIRED_RESOURCE_ADAPTERS = frozenset(
    {
        "distribution", "installer", "command_projection", "runtime",
        "subagent_protocol", "workflow_transition", "project_config",
        "project_hooks", "ut", "lifecycle", "telemetry_protocol",
    }
)
# Files where the upstream name is preserved deliberately (Apache-2.0 4(c)/4(d)).
ATTRIBUTION_FILES = frozenset(
    {
        "NOTICE", "ATTRIBUTION.md", "MIGRATION-NOTES.md",
        "THIRD_PARTY_NOTICES.md", "LICENSE",
    }
)
BRAND_RESIDUE = re.compile(r"HelixHarness|helixharness|HELIXHARNESS|/helix:|helix@")
SKIP_SUFFIXES = frozenset(
    {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".gz", ".zip", ".pyc", ".woff", ".woff2", ".ttf"}
)
# VCS metadata, dependency trees and build output are not reviewed source.
# Git commit messages legitimately carry upstream attribution, so .git must be
# excluded or the branding check would flag its own history.
SKIP_DIRS = frozenset(
    {
        ".git", ".hg", ".svn", "node_modules", ".venv", "venv",
        "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache",
        "dist", "build", ".cache",
    }
)


def repo_files(pattern: str = "*"):
    """Yield repository files, skipping VCS and build/dependency trees."""
    for path in sorted(REPO_ROOT.rglob(pattern)):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(REPO_ROOT).parts[:-1]):
            continue
        yield path


def check(label: str, errors: list[str], fn) -> None:
    try:
        fn()
        print(f"  OK   {label}")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"{label}: {exc}")
        print(f"  FAIL {label}: {exc}")


def json_files() -> None:
    bad = []
    for path in repo_files("*.json"):
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, UnicodeDecodeError) as exc:
            bad.append(f"{path.relative_to(REPO_ROOT)}: {exc}")
    if bad:
        raise ValueError("; ".join(bad[:5]))


def python_syntax() -> None:
    bad = []
    for path in repo_files("*.py"):
        try:
            compile(path.read_text(encoding="utf-8"), str(path), "exec")
        except (SyntaxError, UnicodeDecodeError) as exc:
            bad.append(f"{path.relative_to(REPO_ROOT)}: {exc}")
    if bad:
        raise ValueError("; ".join(bad[:5]))


def host_kits() -> None:
    registry = HostRegistry.discover(HOSTS_ROOT)
    ids = set(registry.supported_ids())
    declared = {p.parent.name for p in HOSTS_ROOT.glob("*/host.json")}
    if ids != declared:
        raise ValueError(f"discovered {sorted(ids)} != declared {sorted(declared)}")
    for required in ("codex", "claude-code"):
        if required not in ids:
            raise ValueError(f"stable host missing: {required}")
    for manifest in registry.manifests():
        missing = sorted(REQUIRED_RESOURCE_ADAPTERS - set(manifest.adapters))
        if missing:
            raise ValueError(f"{manifest.host_id} missing adapters: {missing}")
        for name, raw in manifest.adapters.items():
            if raw.startswith("resource:"):
                manifest.resolve_resource_adapter(name)
            elif raw.startswith("python:"):
                manifest.load_python_adapter(name)
        projection = load_command_projection(manifest)
        if set(projection.entrypoints) != EXPECTED_COMMANDS:
            raise ValueError(f"{manifest.host_id} projection covers wrong commands")
        load_project_config(manifest)
        load_project_hooks(manifest)
    print(f"       hosts: {', '.join(sorted(ids))}")


def distribution_manifests() -> None:
    registry = HostRegistry.discover(HOSTS_ROOT)
    for manifest in registry.manifests():
        path = manifest.resolve_resource_adapter("distribution")
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or not payload.get("name"):
            raise ValueError(f"{manifest.host_id} distribution manifest has no name")
        # A repository-root entry point is optional: some hosts (e.g. Codex)
        # are only distributed from the plugin root. If present, it must parse.
        repo_entry = REPO_ROOT / path.relative_to(PLUGIN_ROOT)
        if repo_entry.is_file():
            entry_payload = json.loads(repo_entry.read_text(encoding="utf-8"))
            if not isinstance(entry_payload, dict) or not entry_payload.get("name"):
                raise ValueError(f"{manifest.host_id} repository-root manifest has no name")


def native_bundle_packages() -> list[tuple[str, Path, dict]]:
    """Resolve every package that some host installs as a native bundle."""
    registry = HostRegistry.discover(HOSTS_ROOT)
    packages: list[tuple[str, Path, dict]] = []
    for manifest in registry.manifests():
        path = manifest.resolve_resource_adapter("distribution")
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            continue
        if not isinstance((payload.get("dsh") or {}).get("bundle"), dict):
            continue
        packages.append((manifest.host_id, path.parent, payload))
    return packages


def native_bundles() -> None:
    """Validate packages that a host installs as a native plugin bundle."""
    found = []
    for host_id, package_root, payload in native_bundle_packages():
        bundle = payload["dsh"]["bundle"]
        patch_rel = bundle.get("patch")
        if not isinstance(patch_rel, str) or not patch_rel:
            raise ValueError(f"{host_id} bundle patch is not declared")
        patch = package_root / patch_rel
        if not patch.is_file():
            raise ValueError(f"{host_id} bundle patch missing: {patch_rel}")
        patch_text = patch.read_text(encoding="utf-8")
        if payload.get("name") not in patch_text:
            raise ValueError(f"{host_id} bundle patch does not mount {payload.get('name')}")
        exports = payload.get("exports") or {}
        if patch_rel.lstrip("./") not in {str(key).lstrip("./") for key in exports}:
            raise ValueError(f"{host_id} bundle patch is not exported: {patch_rel}")
        main = payload.get("main")
        if not isinstance(main, str) or not (package_root / main).is_file():
            raise ValueError(f"{host_id} bundle main module missing: {main}")
        files = [str(item).lstrip("./") for item in payload.get("files") or []]
        for required in (patch_rel.lstrip("./"), main.lstrip("./")):
            # A directory entry such as "lib" covers everything beneath it.
            if not any(required == entry or required.startswith(entry.rstrip("/") + "/") for entry in files):
                raise ValueError(f"{host_id} bundle omits {required} from files")
        found.append(f"{payload['name']}@{payload.get('version')}")
    if found:
        print(f"       bundles: {', '.join(found)}")


def host_evidence() -> None:
    """A declared E2E evidence path must exist and still describe this host."""
    registry = HostRegistry.discover(HOSTS_ROOT)
    declared = []
    for manifest in registry.manifests():
        if manifest.evidence is None:
            continue
        path = REPO_ROOT / manifest.evidence
        if not path.is_file():
            raise ValueError(f"{manifest.host_id} evidence missing: {manifest.evidence}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("host_id") != manifest.host_id:
            raise ValueError(f"{manifest.host_id} evidence names a different host")
        if payload.get("status") != "pass":
            raise ValueError(f"{manifest.host_id} evidence status is {payload.get('status')!r}")
        declared.append(manifest.host_id)
    if declared:
        print(f"       evidence: {', '.join(sorted(declared))}")


def ci_workflows() -> None:
    """The CI publish workflow must still describe the bundles it releases."""
    workflow_root = REPO_ROOT / ".github" / "workflows"
    if not workflow_root.is_dir():
        raise ValueError(".github/workflows is missing; npm release has no automation")
    workflows = sorted(path for path in workflow_root.iterdir() if path.suffix in {".yml", ".yaml"})
    if not workflows:
        raise ValueError(".github/workflows holds no workflow file")
    texts = {path.name: path.read_text(encoding="utf-8") for path in workflows}
    published = []
    for _host_id, _package_root, payload in native_bundle_packages():
        name = payload["name"]
        if not any(name in text for text in texts.values()):
            raise ValueError(f"no workflow publishes {name}; the npm bundle would never ship")
        if (payload.get("publishConfig") or {}).get("access") != "public":
            raise ValueError(f"{name} does not set publishConfig.access=public")
        if not any("NPM_TOKEN" in text for text in texts.values()):
            raise ValueError("workflows never read NPM_TOKEN")
        if not any("id-token: write" in text for text in texts.values()):
            raise ValueError("no workflow grants id-token: write; OIDC publishing would fail")
        if any(re.search(r"^\s*registry-url\s*:", text, re.MULTILINE) for text in texts.values()):
            raise ValueError("a workflow sets setup-node registry-url, which blocks OIDC publishing")
        published.append(name)
    if published:
        print(f"       workflows: {', '.join(sorted(texts))} -> {', '.join(published)}")


def branding_residue() -> None:
    hits = []
    for path in repo_files():
        if path.suffix.lower() in SKIP_SUFFIXES:
            continue
        if path.name in ATTRIBUTION_FILES or path.name == "check_release.py":
            # This script necessarily contains the patterns it scans for.
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if BRAND_RESIDUE.search(text):
            hits.append(str(path.relative_to(REPO_ROOT)))
        if BRAND_RESIDUE.search(str(path)):
            hits.append(f"path:{path.relative_to(REPO_ROOT)}")
    if hits:
        raise ValueError("residue in " + ", ".join(hits[:8]))


def documentation_links() -> None:
    required = [
        "README.md", "README.zh-CN.md", "ATTRIBUTION.md", "MIGRATION-NOTES.md",
        "NOTICE", "LICENSE",
        "docs/installation.md", "docs/user-guide.md", "docs/user-guide.zh-CN.md",
        "docs/host-support-matrix.md", "docs/add-new-host.md",
        "docs/host-kit-template/README.md",
    ]
    missing = [rel for rel in required if not (REPO_ROOT / rel).is_file()]
    if missing:
        raise ValueError("missing docs: " + ", ".join(missing))
    for name in ("README.md", "README.zh-CN.md"):
        text = (REPO_ROOT / name).read_text(encoding="utf-8")
        for target in re.findall(r"\]\(([^)#]+\.md)(?:#[^)]*)?\)", text):
            if target.startswith(("http://", "https://")):
                continue
            if not (REPO_ROOT / target).is_file():
                raise ValueError(f"{name} broken link: {target}")


def main() -> int:
    print("AegisHarness release consistency check")
    errors: list[str] = []
    check("JSON manifests parse", errors, json_files)
    check("Python sources compile", errors, python_syntax)
    check("Host Kit contracts", errors, host_kits)
    check("distribution manifests", errors, distribution_manifests)
    check("native plugin bundles", errors, native_bundles)
    check("host E2E evidence", errors, host_evidence)
    check("CI publish workflows", errors, ci_workflows)
    check("branding residue (excluding attribution files)", errors, branding_residue)
    check("documentation links", errors, documentation_links)
    print()
    if errors:
        print(f"FAILED: {len(errors)} check(s)")
        return 1
    print("PASSED: all checks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
