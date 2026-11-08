#!/usr/bin/env python3
"""Release consistency checks that do not depend on temp directories.

Validates JSON manifests, Python syntax, Host Kit contracts, command
projections, distribution manifests, branding residue and documentation links.
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


def check(label: str, errors: list[str], fn) -> None:
    try:
        fn()
        print(f"  OK   {label}")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"{label}: {exc}")
        print(f"  FAIL {label}: {exc}")


def json_files() -> None:
    bad = []
    for path in sorted(REPO_ROOT.rglob("*.json")):
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, UnicodeDecodeError) as exc:
            bad.append(f"{path.relative_to(REPO_ROOT)}: {exc}")
    if bad:
        raise ValueError("; ".join(bad[:5]))


def python_syntax() -> None:
    bad = []
    for path in sorted(REPO_ROOT.rglob("*.py")):
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


def branding_residue() -> None:
    hits = []
    for path in sorted(REPO_ROOT.rglob("*")):
        if not path.is_file() or path.suffix.lower() in SKIP_SUFFIXES:
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
