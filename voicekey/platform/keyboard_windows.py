"""Windows keyboard backend with standard/admin capability states."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from voicekey.platform.keyboard_base import (
    KeyboardBackend,
    KeyboardBackendError,
    KeyboardCapabilityReport,
    KeyboardCapabilityState,
    KeyboardErrorCode,
)


class KeyboardInjector(Protocol):
    """Minimal injection surface used by this adapter."""

    def type_text(self, text: str, delay_ms: int) -> None: ...

    def press_key(self, key: str) -> None: ...

    def press_combo(self, keys: list[str]) -> None: ...


@dataclass(frozen=True)
class _NoOpInjector:
    """No-op injector used in unit scope to avoid OS side effects."""

    def type_text(self, text: str, delay_ms: int) -> None:
        del text, delay_ms

    def press_key(self, key: str) -> None:
        del key

    def press_combo(self, keys: list[str]) -> None:
        del keys


class WindowsKeyboardBackend(KeyboardBackend):
    """Windows keyboard adapter with deterministic capability self-check."""

    _PRIMARY_ADAPTER = "pynput_win32"
    _FALLBACK_ADAPTER = "sendinput_pywin32"

    def __init__(
        self,
        *,
        is_admin: bool = False,
        primary_available: bool = True,
        fallback_available: bool = True,
        primary_injector: KeyboardInjector | None = None,
        fallback_injector: KeyboardInjector | None = None,
    ) -> None:
        self._is_admin = is_admin
        self._primary_available = primary_available
        self._fallback_available = fallback_available
        self._primary_injector = primary_injector or _NoOpInjector()
        self._fallback_injector = fallback_injector or _NoOpInjector()

    def type_text(self, text: str, delay_ms: int = 0) -> None:
        if not text:
            raise KeyboardBackendError(KeyboardErrorCode.EMPTY_TEXT, "Cannot type empty text.")
        injector = self._resolve_injector()
        self._invoke(lambda: injector.type_text(text, delay_ms))

    def press_key(self, key: str) -> None:
        injector = self._resolve_injector()
        self._invoke(lambda: injector.press_key(key))

    def press_combo(self, keys: list[str]) -> None:
        if not keys:
            raise KeyboardBackendError(KeyboardErrorCode.INVALID_COMBO, "Key combo cannot be empty.")
        injector = self._resolve_injector()
        self._invoke(lambda: injector.press_combo(keys))

    def self_check(self) -> KeyboardCapabilityReport:
        available = self._available_adapters()
        codes: list[KeyboardErrorCode] = []
        warnings: list[str] = []
        remediation: list[str] = []

        if not self._is_admin:
            codes.append(KeyboardErrorCode.ADMIN_RECOMMENDED)
            warnings.append(
                "Running in standard user mode; admin mode is recommended for maximal compatibility."
            )
            remediation.append("Run VoiceKey as administrator if key injection fails in privileged apps.")

        active_adapter = self._select_active_adapter()
        if active_adapter is None:
            if not self._primary_available:
                codes.append(KeyboardErrorCode.PRIMARY_BACKEND_UNAVAILABLE)
            if not self._fallback_available:
                codes.append(KeyboardErrorCode.FALLBACK_BACKEND_UNAVAILABLE)
            if not self._is_admin:
                codes.append(KeyboardErrorCode.ADMIN_REQUIRED)

            return KeyboardCapabilityReport(
                backend="windows_keyboard",
                platform="windows",
                state=KeyboardCapabilityState.UNAVAILABLE,
                active_adapter=None,
                available_adapters=available,
                codes=tuple(dict.fromkeys(codes)),
                warnings=tuple(dict.fromkeys(warnings)),
                remediation=tuple(dict.fromkeys(remediation)),
            )

        if active_adapter == self._FALLBACK_ADAPTER:
            codes.append(KeyboardErrorCode.PRIMARY_BACKEND_UNAVAILABLE)
            warnings.append("Using pywin32 SendInput fallback path because pynput win32 path is unavailable.")

        state = KeyboardCapabilityState.READY if not codes else KeyboardCapabilityState.DEGRADED
        return KeyboardCapabilityReport(
            backend="windows_keyboard",
            platform="windows",
            state=state,
            active_adapter=active_adapter,
            available_adapters=available,
            codes=tuple(dict.fromkeys(codes)),
            warnings=tuple(dict.fromkeys(warnings)),
            remediation=tuple(dict.fromkeys(remediation)),
        )

    def _available_adapters(self) -> tuple[str, ...]:
        available: list[str] = []
        if self._primary_available:
            available.append(self._PRIMARY_ADAPTER)
        if self._fallback_available:
            available.append(self._FALLBACK_ADAPTER)
        return tuple(available)

    def _select_active_adapter(self) -> str | None:
        if self._primary_available:
            return self._PRIMARY_ADAPTER
        if self._fallback_available:
            return self._FALLBACK_ADAPTER
        return None

    def _resolve_injector(self) -> KeyboardInjector:
        report = self.self_check()
        if report.state is KeyboardCapabilityState.UNAVAILABLE:
            code = report.codes[0] if report.codes else KeyboardErrorCode.PRIMARY_BACKEND_UNAVAILABLE
            raise KeyboardBackendError(
                code,
                "Windows keyboard backend is unavailable. Run capability self-check for remediation.",
            )

        if report.active_adapter == self._PRIMARY_ADAPTER:
            return self._primary_injector
        if report.active_adapter == self._FALLBACK_ADAPTER:
            return self._fallback_injector
        raise KeyboardBackendError(
            KeyboardErrorCode.INJECTION_FAILED,
            "Windows keyboard backend has no active injector despite non-unavailable state.",
        )

    @staticmethod
    def _invoke(action: Callable[[], None]) -> None:
        try:
            action()
        except KeyboardBackendError:
            raise
        except Exception as exc:  # pragma: no cover - defensive conversion
            raise KeyboardBackendError(
                KeyboardErrorCode.INJECTION_FAILED,
                f"Windows keyboard injection failed: {exc}",
            ) from exc


__all__ = ["WindowsKeyboardBackend"]
