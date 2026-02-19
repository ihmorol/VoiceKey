"""Linux window backend with deterministic capability self-check."""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from voicekey.platform.compatibility import detect_display_session
from voicekey.platform.window_base import (
    WindowBackend,
    WindowBackendError,
    WindowCapabilityReport,
    WindowCapabilityState,
    WindowErrorCode,
)


class WindowOperator(Protocol):
    """Minimal operation surface used by this adapter."""

    def maximize_active(self) -> None: ...

    def minimize_active(self) -> None: ...

    def close_active(self) -> None: ...

    def switch_next(self) -> None: ...


@dataclass(frozen=True)
class _NoOpWindowOperator:
    """No-op operator used in unit scope to avoid OS side effects."""

    def maximize_active(self) -> None:
        return None

    def minimize_active(self) -> None:
        return None

    def close_active(self) -> None:
        return None

    def switch_next(self) -> None:
        return None


class LinuxWindowBackend(WindowBackend):
    """Linux window adapter with wmctrl/xdotool availability modeling."""

    _PRIMARY_ADAPTER = "wmctrl_xdotool"
    _ALL_OPERATIONS = (
        "maximize_active",
        "minimize_active",
        "close_active",
        "switch_next",
    )

    def __init__(
        self,
        *,
        session_type: str | None = None,
        wmctrl_available: bool = True,
        xdotool_available: bool = True,
        primary_operator: WindowOperator | None = None,
    ) -> None:
        self._session_type = self._detect_session_type(session_type)
        self._wmctrl_available = wmctrl_available
        self._xdotool_available = xdotool_available
        self._primary_operator = primary_operator or _NoOpWindowOperator()

    def maximize_active(self) -> None:
        self._require_supported("maximize_active")
        self._invoke(self._primary_operator.maximize_active)

    def minimize_active(self) -> None:
        self._require_supported("minimize_active")
        self._invoke(self._primary_operator.minimize_active)

    def close_active(self) -> None:
        self._require_supported("close_active")
        self._invoke(self._primary_operator.close_active)

    def switch_next(self) -> None:
        self._require_supported("switch_next")
        self._invoke(self._primary_operator.switch_next)

    def self_check(self) -> WindowCapabilityReport:
        codes: list[WindowErrorCode] = []
        warnings: list[str] = []
        remediation: list[str] = []
        supported = self._supported_operations()

        if self._session_type not in {"x11", "wayland"}:
            codes.append(WindowErrorCode.DISPLAY_SERVER_UNSUPPORTED)
            warnings.append(
                f"Linux session type '{self._session_type}' is not a supported window-control target."
            )
            remediation.append("Use an X11 session for full window command compatibility.")

        if self._session_type == "wayland":
            codes.append(WindowErrorCode.WAYLAND_BEST_EFFORT)
            warnings.append("Wayland window control is best-effort and may fail in some applications.")
            remediation.append("Use an X11 session for full window command compatibility.")

        if not self._wmctrl_available and not self._xdotool_available:
            codes.append(WindowErrorCode.PRIMARY_BACKEND_UNAVAILABLE)
            remediation.append("Install wmctrl/xdotool or choose an environment with window-control tools.")

        if self._wmctrl_available and not self._xdotool_available:
            codes.append(WindowErrorCode.SWITCH_BACKEND_UNAVAILABLE)
            warnings.append("switch window command is unavailable because xdotool is missing.")
            remediation.append("Install xdotool to enable switch window command.")

        if not self._wmctrl_available and self._xdotool_available:
            codes.append(WindowErrorCode.PRIMARY_BACKEND_UNAVAILABLE)
            warnings.append("maximize/minimize/close window commands are unavailable because wmctrl is missing.")
            remediation.append("Install wmctrl to enable maximize/minimize/close window commands.")

        if not supported or self._session_type not in {"x11", "wayland"}:
            state = WindowCapabilityState.UNAVAILABLE
            active_adapter = None
        elif len(supported) < len(self._ALL_OPERATIONS) or codes:
            state = WindowCapabilityState.DEGRADED
            active_adapter = self._PRIMARY_ADAPTER
        else:
            state = WindowCapabilityState.READY
            active_adapter = self._PRIMARY_ADAPTER

        available_adapters = (self._PRIMARY_ADAPTER,) if supported else ()
        return WindowCapabilityReport(
            backend="linux_window",
            platform="linux",
            state=state,
            active_adapter=active_adapter,
            available_adapters=available_adapters,
            supported_operations=supported,
            codes=tuple(dict.fromkeys(codes)),
            warnings=tuple(dict.fromkeys(warnings)),
            remediation=tuple(dict.fromkeys(remediation)),
        )

    @staticmethod
    def _detect_session_type(session_type: str | None) -> str:
        if session_type is not None:
            return session_type.strip().lower() or "unknown"
        env_value = os.environ.get("XDG_SESSION_TYPE")
        if env_value is not None:
            return env_value.strip().lower() or "unknown"
        return detect_display_session(platform_name="linux", env=os.environ).value

    def _supported_operations(self) -> tuple[str, ...]:
        supported: list[str] = []
        if self._wmctrl_available:
            supported.extend(("maximize_active", "minimize_active", "close_active"))
        if self._xdotool_available:
            supported.append("switch_next")
        return tuple(supported)

    def _require_supported(self, operation: str) -> None:
        report = self.self_check()
        if report.state is WindowCapabilityState.UNAVAILABLE:
            code = report.codes[0] if report.codes else WindowErrorCode.PRIMARY_BACKEND_UNAVAILABLE
            raise WindowBackendError(
                code,
                "Linux window backend is unavailable. Run capability self-check for remediation.",
            )
        if operation not in report.supported_operations:
            raise WindowBackendError(
                WindowErrorCode.OPERATION_UNSUPPORTED,
                f"Linux window backend does not support operation: {operation}.",
            )

    @staticmethod
    def _invoke(action: Callable[[], None]) -> None:
        try:
            action()
        except WindowBackendError:
            raise
        except Exception as exc:  # pragma: no cover - defensive conversion
            raise WindowBackendError(
                WindowErrorCode.ACTION_FAILED,
                f"Linux window action failed: {exc}",
            ) from exc


__all__ = ["LinuxWindowBackend"]
