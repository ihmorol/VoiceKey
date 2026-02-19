"""Keyboard backend contracts, capability model, and typed errors."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum


class KeyboardCapabilityState(StrEnum):
    """Capability levels used by startup diagnostics and health checks."""

    READY = "ready"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


class KeyboardErrorCode(StrEnum):
    """Typed keyboard backend error and degradation codes."""

    EMPTY_TEXT = "empty_text"
    INVALID_COMBO = "invalid_combo"
    DISPLAY_SERVER_UNSUPPORTED = "display_server_unsupported"
    WAYLAND_BEST_EFFORT = "wayland_best_effort"
    PRIMARY_BACKEND_UNAVAILABLE = "primary_backend_unavailable"
    FALLBACK_BACKEND_UNAVAILABLE = "fallback_backend_unavailable"
    INPUT_PERMISSION_REQUIRED = "input_permission_required"
    ADMIN_RECOMMENDED = "admin_recommended"
    ADMIN_REQUIRED = "admin_required"
    INJECTION_FAILED = "injection_failed"


@dataclass(frozen=True)
class KeyboardCapabilityReport:
    """Deterministic structured capability report for keyboard backends."""

    backend: str
    platform: str
    state: KeyboardCapabilityState
    active_adapter: str | None
    available_adapters: tuple[str, ...]
    codes: tuple[KeyboardErrorCode, ...]
    warnings: tuple[str, ...]
    remediation: tuple[str, ...]


class KeyboardBackendError(RuntimeError):
    """Typed runtime error raised by keyboard backend operations."""

    def __init__(self, code: KeyboardErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code


class KeyboardBackend(ABC):
    """Cross-platform keyboard injection contract."""

    @abstractmethod
    def type_text(self, text: str, delay_ms: int = 0) -> None:
        """Type literal text into the active focused target."""

    @abstractmethod
    def press_key(self, key: str) -> None:
        """Press a single key in the active focused target."""

    @abstractmethod
    def press_combo(self, keys: list[str]) -> None:
        """Press a multi-key combination in the active focused target."""

    @abstractmethod
    def self_check(self) -> KeyboardCapabilityReport:
        """Return deterministic capability diagnostics for this backend."""


__all__ = [
    "KeyboardBackend",
    "KeyboardBackendError",
    "KeyboardCapabilityReport",
    "KeyboardCapabilityState",
    "KeyboardErrorCode",
]
