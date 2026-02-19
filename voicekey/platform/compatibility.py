"""Startup compatibility diagnostics for session, keyboard, hotkey, and autostart."""

from __future__ import annotations

import os
import sys
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum

from voicekey.platform.keyboard_base import (
    KeyboardCapabilityReport,
    KeyboardCapabilityState,
    KeyboardErrorCode,
)


class DisplaySession(StrEnum):
    """Supported display-session classifications used by startup diagnostics."""

    X11 = "x11"
    WAYLAND = "wayland"
    WINDOWS = "windows"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ComponentDiagnostic:
    """Generic deterministic diagnostic result for a startup component."""

    component: str
    state: KeyboardCapabilityState
    summary: str
    codes: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    remediation: tuple[str, ...] = ()


@dataclass(frozen=True)
class StartupCompatibilityReport:
    """Aggregated startup compatibility report for CLI and diagnostics views."""

    platform: str
    session: DisplaySession
    overall_state: KeyboardCapabilityState
    components: tuple[ComponentDiagnostic, ...]
    warnings: tuple[str, ...]
    remediation: tuple[str, ...]


def detect_display_session(
    *, platform_name: str | None = None, env: Mapping[str, str] | None = None
) -> DisplaySession:
    """Return deterministic display-session classification."""

    resolved_platform = (platform_name or sys.platform).strip().lower()
    if resolved_platform.startswith("win"):
        return DisplaySession.WINDOWS

    source_env = env if env is not None else os.environ
    xdg_session = source_env.get("XDG_SESSION_TYPE", "").strip().lower()
    if xdg_session == DisplaySession.X11.value:
        return DisplaySession.X11
    if xdg_session == DisplaySession.WAYLAND.value:
        return DisplaySession.WAYLAND

    if source_env.get("WAYLAND_DISPLAY"):
        return DisplaySession.WAYLAND
    if source_env.get("DISPLAY"):
        return DisplaySession.X11
    return DisplaySession.UNKNOWN


def build_startup_compatibility_report(
    *,
    keyboard: KeyboardCapabilityReport,
    hotkey: ComponentDiagnostic,
    autostart: ComponentDiagnostic,
    platform_name: str | None = None,
    env: Mapping[str, str] | None = None,
) -> StartupCompatibilityReport:
    """Build startup compatibility report for keyboard/hotkey/autostart checks."""

    session = detect_display_session(platform_name=platform_name, env=env)
    platform_label = _resolve_platform_label(platform_name, keyboard.platform)
    keyboard_component = _keyboard_to_component(keyboard)
    components = (keyboard_component, hotkey, autostart)

    warnings: list[str] = []
    remediation: list[str] = []
    for component in components:
        warnings.extend(component.warnings)
        remediation.extend(component.remediation)

    if session is DisplaySession.WAYLAND:
        warnings.append(
            "Wayland session detected: support is best-effort with reduced capability for "
            "keyboard and hotkey operations."
        )
        remediation.append("Use an X11 session for full compatibility.")

    if platform_label == "windows":
        code_values = set(keyboard_component.codes)
        if KeyboardErrorCode.ADMIN_RECOMMENDED.value in code_values:
            remediation.append(
                "Admin mode is recommended for maximal compatibility with privileged apps."
            )
        if KeyboardErrorCode.ADMIN_REQUIRED.value in code_values:
            remediation.append("Run VoiceKey as administrator to restore keyboard compatibility.")

    return StartupCompatibilityReport(
        platform=platform_label,
        session=session,
        overall_state=_worst_state(component.state for component in components),
        components=components,
        warnings=_dedupe_keep_order(warnings),
        remediation=_dedupe_keep_order(remediation),
    )


def _resolve_platform_label(platform_name: str | None, keyboard_platform: str) -> str:
    platform_hint = (platform_name or "").strip().lower()
    if platform_hint.startswith("win"):
        return "windows"
    if platform_hint.startswith("linux"):
        return "linux"
    normalized_keyboard = keyboard_platform.strip().lower()
    if normalized_keyboard in {"linux", "windows"}:
        return normalized_keyboard
    return "unknown"


def _keyboard_to_component(report: KeyboardCapabilityReport) -> ComponentDiagnostic:
    active_text = report.active_adapter or "none"
    state_text = report.state.value
    summary = f"Keyboard backend {state_text}; active adapter: {active_text}."
    return ComponentDiagnostic(
        component="keyboard",
        state=report.state,
        summary=summary,
        codes=tuple(code.value for code in report.codes),
        warnings=report.warnings,
        remediation=report.remediation,
    )


def _worst_state(states: Iterable[KeyboardCapabilityState]) -> KeyboardCapabilityState:
    severity = {
        KeyboardCapabilityState.READY: 0,
        KeyboardCapabilityState.DEGRADED: 1,
        KeyboardCapabilityState.UNAVAILABLE: 2,
    }
    resolved_states = tuple(states)
    return max(resolved_states, key=lambda state: severity[state])


def _dedupe_keep_order(values: list[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


__all__ = [
    "ComponentDiagnostic",
    "DisplaySession",
    "StartupCompatibilityReport",
    "build_startup_compatibility_report",
    "detect_display_session",
]
