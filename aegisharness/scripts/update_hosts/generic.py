"""Conservative host detectors for manifest-driven preview Host Kits.

A detector only fires when the host runtime sets an explicit marker. Preview
hosts score below the two stable kits so a shared environment never silently
resolves to a preview host. When two hosts tie, the Registry fails closed.
"""

from __future__ import annotations

from typing import Any, Mapping

PREVIEW_SCORE = 70

_MARKERS: dict[str, tuple[str, ...]] = {
    "minimax": (
        "MINIMAX_CODE",
        "MCODE_SESSION_ID",
        "MINIMAX_PLUGIN_ROOT",
        "MCODE_PLUGIN_ROOT",
    ),
    "workbuddy": (
        "WORKBUDDY_SESSION",
        "WORKBUDDY_PLUGIN_ROOT",
        "CODEBUDDY_PLUGIN_ROOT",
        "CODEBUDDY_PROJECT_DIR",
    ),
    "qoder": (
        "QODER_SESSION",
        "QODER_PLUGIN_ROOT",
        "QODER_CLI",
        "QODER_PROJECT_DIR",
    ),
    "deepseek-dsh": (
        "DSH_SESSION",
        "DSH_PROFILE",
        "DSH_PLUGIN_ROOT",
        "DSH_HOME",
        "DEEPSEEK_HARNESS_SESSION",
    ),
}


def _detect(host_id: str, environment: Mapping[str, Any]) -> int | None:
    markers = _MARKERS[host_id]
    if any(str(environment.get(name) or "").strip() for name in markers):
        return PREVIEW_SCORE
    return None


def detect_minimax(environment: Mapping[str, Any]) -> int | None:
    """Recognise MiniMax Code runtimes."""

    return _detect("minimax", environment)


def detect_workbuddy(environment: Mapping[str, Any]) -> int | None:
    """Recognise WorkBuddy / CodeBuddy runtimes."""

    return _detect("workbuddy", environment)


def detect_qoder(environment: Mapping[str, Any]) -> int | None:
    """Recognise Qoder IDE / CLI runtimes."""

    return _detect("qoder", environment)


def detect_deepseek_dsh(environment: Mapping[str, Any]) -> int | None:
    """Recognise DeepSeek Harness (dsh) runtimes."""

    return _detect("deepseek-dsh", environment)


__all__ = [
    "PREVIEW_SCORE",
    "detect_deepseek_dsh",
    "detect_minimax",
    "detect_qoder",
    "detect_workbuddy",
]
