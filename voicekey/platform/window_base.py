"""Window backend contracts, capability model, and typed errors."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum


class WindowCapabilityState(StrEnum):
    """Capability levels used by startup diagnostics and routing decisions."""

    READY = "ready"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


class WindowErrorCode(StrEnum):
    """Typed window backend error and degradation codes."""

    DISPLAY_SERVER_UNSUPPORTED = "display_server_unsupported"
    WAYLAND_BEST_EFFORT = "wayland_best_effort"
    PRIMARY_BACKEND_UNAVAILABLE = "primary_backend_unavailable"
    SWITCH_BACKEND_UNAVAILABLE = "switch_backend_unavailable"
    ADMIN_RECOMMENDED = "admin_recommended"
    ADMIN_REQUIRED = "admin_required"
    OPERATION_UNSUPPORTED = "operation_unsupported"
    ACTION_FAILED = "action_failed"


@dataclass(frozen=True)
class WindowCapabilityReport:
    """Deterministic structured capability report for window backends."""

    backend: str
    platform: str
    state: WindowCapabilityState
    active_adapter: str | None
    available_adapters: tuple[str, ...]
    supported_operations: tuple[str, ...]
    codes: tuple[WindowErrorCode, ...]
    warnings: tuple[str, ...]
    remediation: tuple[str, ...]


class WindowBackendError(RuntimeError):
    """Typed runtime error raised by window backend operations."""

    def __init__(self, code: WindowErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code


class WindowBackend(ABC):
    """Cross-platform window management contract."""

    @abstractmethod
    def maximize_active(self) -> None:
        """Maximize the currently focused window."""

    @abstractmethod
    def minimize_active(self) -> None:
        """Minimize the currently focused window."""

    @abstractmethod
    def close_active(self) -> None:
        """Close the currently focused window."""

    @abstractmethod
    def switch_next(self) -> None:
        """Switch focus to the next window."""

    @abstractmethod
    def self_check(self) -> WindowCapabilityReport:
        """Return deterministic capability diagnostics for this backend."""


__all__ = [
    "WindowBackend",
    "WindowBackendError",
    "WindowCapabilityReport",
    "WindowCapabilityState",
    "WindowErrorCode",
]
