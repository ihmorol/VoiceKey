"""Unit tests for startup compatibility reporting (E04-S03 T01/T02)."""

from __future__ import annotations

from voicekey.platform.compatibility import (
    ComponentDiagnostic,
    DisplaySession,
    build_startup_compatibility_report,
    detect_display_session,
)
from voicekey.platform.keyboard_base import (
    KeyboardCapabilityReport,
    KeyboardCapabilityState,
    KeyboardErrorCode,
)


def test_detect_display_session_from_linux_env() -> None:
    assert detect_display_session(platform_name="linux", env={"XDG_SESSION_TYPE": "x11"}) is DisplaySession.X11
    assert (
        detect_display_session(platform_name="linux", env={"XDG_SESSION_TYPE": "wayland"})
        is DisplaySession.WAYLAND
    )


def test_detect_display_session_for_windows_platform() -> None:
    session = detect_display_session(platform_name="win32", env={})
    assert session is DisplaySession.WINDOWS


def test_detect_display_session_returns_unknown_without_signals() -> None:
    session = detect_display_session(platform_name="linux", env={})
    assert session is DisplaySession.UNKNOWN


def test_wayland_report_includes_explicit_best_effort_warning() -> None:
    keyboard = KeyboardCapabilityReport(
        backend="linux_keyboard",
        platform="linux",
        state=KeyboardCapabilityState.DEGRADED,
        active_adapter="x11_pynput",
        available_adapters=("x11_pynput",),
        codes=(KeyboardErrorCode.WAYLAND_BEST_EFFORT,),
        warnings=("Wayland keyboard injection is best-effort.",),
        remediation=("Use an X11 session for full keyboard compatibility.",),
    )
    hotkey = ComponentDiagnostic(
        component="hotkey",
        state=KeyboardCapabilityState.READY,
        summary="Hotkey backend ready.",
    )
    autostart = ComponentDiagnostic(
        component="autostart",
        state=KeyboardCapabilityState.READY,
        summary="Autostart adapter ready.",
    )

    report = build_startup_compatibility_report(
        keyboard=keyboard,
        hotkey=hotkey,
        autostart=autostart,
        platform_name="linux",
        env={"XDG_SESSION_TYPE": "wayland"},
    )

    assert report.session is DisplaySession.WAYLAND
    assert report.overall_state is KeyboardCapabilityState.DEGRADED
    assert any("best-effort" in warning.lower() for warning in report.warnings)
    assert any("reduced capability" in warning.lower() for warning in report.warnings)


def test_windows_report_propagates_admin_recommendation_from_keyboard_check() -> None:
    keyboard = KeyboardCapabilityReport(
        backend="windows_keyboard",
        platform="windows",
        state=KeyboardCapabilityState.DEGRADED,
        active_adapter="pynput_win32",
        available_adapters=("pynput_win32", "sendinput_pywin32"),
        codes=(KeyboardErrorCode.ADMIN_RECOMMENDED,),
        warnings=(
            "Running in standard user mode; admin mode is recommended for maximal compatibility.",
        ),
        remediation=("Run VoiceKey as administrator if key injection fails in privileged apps.",),
    )
    hotkey = ComponentDiagnostic(
        component="hotkey",
        state=KeyboardCapabilityState.READY,
        summary="Hotkey backend ready.",
    )
    autostart = ComponentDiagnostic(
        component="autostart",
        state=KeyboardCapabilityState.READY,
        summary="Autostart adapter ready.",
    )

    report = build_startup_compatibility_report(
        keyboard=keyboard,
        hotkey=hotkey,
        autostart=autostart,
        platform_name="win32",
        env={},
    )

    assert report.session is DisplaySession.WINDOWS
    assert report.overall_state is KeyboardCapabilityState.DEGRADED
    assert any("administrator" in item.lower() for item in report.remediation)
    assert any("admin mode" in item.lower() for item in report.warnings)


def test_overall_state_is_unavailable_if_any_component_is_unavailable() -> None:
    keyboard = KeyboardCapabilityReport(
        backend="linux_keyboard",
        platform="linux",
        state=KeyboardCapabilityState.READY,
        active_adapter="x11_pynput",
        available_adapters=("x11_pynput",),
        codes=(),
        warnings=(),
        remediation=(),
    )
    hotkey = ComponentDiagnostic(
        component="hotkey",
        state=KeyboardCapabilityState.UNAVAILABLE,
        summary="Hotkey backend unavailable.",
        warnings=("Global hotkeys are not available.",),
    )
    autostart = ComponentDiagnostic(
        component="autostart",
        state=KeyboardCapabilityState.READY,
        summary="Autostart adapter ready.",
    )

    report = build_startup_compatibility_report(
        keyboard=keyboard,
        hotkey=hotkey,
        autostart=autostart,
        platform_name="linux",
        env={"XDG_SESSION_TYPE": "x11"},
    )

    assert report.overall_state is KeyboardCapabilityState.UNAVAILABLE
    assert report.components[1].component == "hotkey"
    assert report.components[1].state is KeyboardCapabilityState.UNAVAILABLE
