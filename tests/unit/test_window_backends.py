"""Unit tests for window backend contract and adapters (E04-S04)."""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from voicekey.platform.window_base import (
    WindowBackend,
    WindowBackendError,
    WindowCapabilityState,
    WindowErrorCode,
)
from voicekey.platform.window_linux import LinuxWindowBackend
from voicekey.platform.window_windows import WindowsWindowBackend


@dataclass
class RecordingWindowOperator:
    """Operator double that records operation invocations."""

    calls: list[str] = field(default_factory=list)

    def maximize_active(self) -> None:
        self.calls.append("maximize")

    def minimize_active(self) -> None:
        self.calls.append("minimize")

    def close_active(self) -> None:
        self.calls.append("close")

    def switch_next(self) -> None:
        self.calls.append("switch")


def test_linux_and_windows_backends_share_window_contract() -> None:
    linux = LinuxWindowBackend(session_type="x11", wmctrl_available=True, xdotool_available=True)
    windows = WindowsWindowBackend(is_admin=True, primary_available=True)

    assert isinstance(linux, WindowBackend)
    assert isinstance(windows, WindowBackend)


def test_linux_x11_reports_ready_when_all_operations_available() -> None:
    backend = LinuxWindowBackend(session_type="x11", wmctrl_available=True, xdotool_available=True)

    report = backend.self_check()

    assert report.state is WindowCapabilityState.READY
    assert report.supported_operations == ("maximize_active", "minimize_active", "close_active", "switch_next")
    assert report.codes == ()


def test_linux_wayland_reports_degraded_best_effort_state() -> None:
    backend = LinuxWindowBackend(session_type="wayland", wmctrl_available=True, xdotool_available=True)

    report = backend.self_check()

    assert report.state is WindowCapabilityState.DEGRADED
    assert WindowErrorCode.WAYLAND_BEST_EFFORT in report.codes


def test_linux_missing_tools_reports_unavailable_with_remediation() -> None:
    backend = LinuxWindowBackend(session_type="x11", wmctrl_available=False, xdotool_available=False)

    report = backend.self_check()

    assert report.state is WindowCapabilityState.UNAVAILABLE
    assert WindowErrorCode.PRIMARY_BACKEND_UNAVAILABLE in report.codes
    assert any("Install wmctrl/xdotool" in item for item in report.remediation)


def test_windows_standard_user_reports_degraded_admin_recommended_state() -> None:
    backend = WindowsWindowBackend(is_admin=False, primary_available=True)

    report = backend.self_check()

    assert report.state is WindowCapabilityState.DEGRADED
    assert WindowErrorCode.ADMIN_RECOMMENDED in report.codes


def test_window_operations_route_to_operator_without_os_side_effects() -> None:
    operator = RecordingWindowOperator()
    backend = LinuxWindowBackend(
        session_type="x11",
        wmctrl_available=True,
        xdotool_available=True,
        primary_operator=operator,
    )

    backend.maximize_active()
    backend.minimize_active()
    backend.close_active()
    backend.switch_next()

    assert operator.calls == ["maximize", "minimize", "close", "switch"]


def test_switch_next_raises_typed_error_when_unsupported() -> None:
    backend = LinuxWindowBackend(session_type="x11", wmctrl_available=True, xdotool_available=False)

    with pytest.raises(WindowBackendError) as exc_info:
        backend.switch_next()

    assert exc_info.value.code is WindowErrorCode.OPERATION_UNSUPPORTED
