"""Windows window backend with deterministic capability self-check."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

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


class WindowsWindowBackend(WindowBackend):
    """Windows window adapter with standard/admin capability states."""

    _PRIMARY_ADAPTER = "pywin32_user32"
    _ALL_OPERATIONS = (
        "maximize_active",
        "minimize_active",
        "close_active",
        "switch_next",
    )

    def __init__(
        self,
        *,
        is_admin: bool = False,
        primary_available: bool = True,
        switch_available: bool = True,
        primary_operator: WindowOperator | None = None,
    ) -> None:
        self._is_admin = is_admin
        self._primary_available = primary_available
        self._switch_available = switch_available
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

        if not self._is_admin:
            codes.append(WindowErrorCode.ADMIN_RECOMMENDED)
            warnings.append(
                "Running in standard user mode; admin mode is recommended for maximal compatibility."
            )
            remediation.append("Run VoiceKey as administrator if window commands fail in privileged apps.")

        if not self._primary_available:
            codes.append(WindowErrorCode.PRIMARY_BACKEND_UNAVAILABLE)
            remediation.append("Install/enable pywin32 window APIs to use window commands.")

        if self._primary_available and not self._switch_available:
            codes.append(WindowErrorCode.SWITCH_BACKEND_UNAVAILABLE)
            warnings.append("switch window command is unavailable on this runtime path.")
            remediation.append("Enable switch-window adapter support for this environment.")

        if not supported:
            if not self._is_admin:
                codes.append(WindowErrorCode.ADMIN_REQUIRED)
            state = WindowCapabilityState.UNAVAILABLE
            active_adapter = None
        elif len(supported) < len(self._ALL_OPERATIONS) or codes:
            state = WindowCapabilityState.DEGRADED
            active_adapter = self._PRIMARY_ADAPTER
        else:
            state = WindowCapabilityState.READY
            active_adapter = self._PRIMARY_ADAPTER

        available_adapters = (self._PRIMARY_ADAPTER,) if self._primary_available else ()
        return WindowCapabilityReport(
            backend="windows_window",
            platform="windows",
            state=state,
            active_adapter=active_adapter,
            available_adapters=available_adapters,
            supported_operations=supported,
            codes=tuple(dict.fromkeys(codes)),
            warnings=tuple(dict.fromkeys(warnings)),
            remediation=tuple(dict.fromkeys(remediation)),
        )

    def _supported_operations(self) -> tuple[str, ...]:
        if not self._primary_available:
            return ()

        supported = ["maximize_active", "minimize_active", "close_active"]
        if self._switch_available:
            supported.append("switch_next")
        return tuple(supported)

    def _require_supported(self, operation: str) -> None:
        report = self.self_check()
        if report.state is WindowCapabilityState.UNAVAILABLE:
            code = report.codes[0] if report.codes else WindowErrorCode.PRIMARY_BACKEND_UNAVAILABLE
            raise WindowBackendError(
                code,
                "Windows window backend is unavailable. Run capability self-check for remediation.",
            )
        if operation not in report.supported_operations:
            raise WindowBackendError(
                WindowErrorCode.OPERATION_UNSUPPORTED,
                f"Windows window backend does not support operation: {operation}.",
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
                f"Windows window action failed: {exc}",
            ) from exc


__all__ = ["WindowsWindowBackend"]
