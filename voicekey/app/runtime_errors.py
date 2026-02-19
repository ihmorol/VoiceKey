"""Structured runtime error taxonomy for resilience and remediation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class RuntimeErrorCategory(StrEnum):
    """Top-level runtime error categories from architecture recovery design."""

    AUDIO = "audio"
    RECOGNITION = "recognition"
    INJECTION = "injection"
    CONFIG = "config"


class RuntimeErrorCode(StrEnum):
    """Typed runtime error codes for edge scenarios and recovery logic."""

    NO_MICROPHONE = "no_microphone"
    MICROPHONE_DISCONNECTED = "microphone_disconnected"
    HOTKEY_CONFLICT = "hotkey_conflict"
    MODEL_CHECKSUM_FAILED = "model_checksum_failed"
    KEYBOARD_BLOCKED = "keyboard_blocked"


@dataclass(frozen=True)
class RuntimeErrorInfo:
    """User-facing runtime error metadata and remediation guidance."""

    code: RuntimeErrorCode
    category: RuntimeErrorCategory
    title: str
    remediation: str
    retryable: bool
    safety_critical: bool

    def actionable_message(self, detail: str | None = None) -> str:
        """Render a deterministic actionable message for CLI/tray surfaces."""
        message = self.title if detail is None else f"{self.title}: {detail}"
        return f"{message} Remediation: {self.remediation}"


_RUNTIME_ERROR_MAP: dict[RuntimeErrorCode, RuntimeErrorInfo] = {
    RuntimeErrorCode.NO_MICROPHONE: RuntimeErrorInfo(
        code=RuntimeErrorCode.NO_MICROPHONE,
        category=RuntimeErrorCategory.AUDIO,
        title="No microphone device is available",
        remediation="Connect a microphone, then run `voicekey devices` to select a valid input device.",
        retryable=False,
        safety_critical=True,
    ),
    RuntimeErrorCode.MICROPHONE_DISCONNECTED: RuntimeErrorInfo(
        code=RuntimeErrorCode.MICROPHONE_DISCONNECTED,
        category=RuntimeErrorCategory.AUDIO,
        title="Microphone was removed during runtime",
        remediation="Reconnect the device and retry capture. VoiceKey retries with bounded backoff and pauses if recovery fails.",
        retryable=True,
        safety_critical=False,
    ),
    RuntimeErrorCode.HOTKEY_CONFLICT: RuntimeErrorInfo(
        code=RuntimeErrorCode.HOTKEY_CONFLICT,
        category=RuntimeErrorCategory.CONFIG,
        title="Configured global hotkey conflicts with another application",
        remediation="Choose an alternative hotkey in settings and retry registration.",
        retryable=False,
        safety_critical=False,
    ),
    RuntimeErrorCode.MODEL_CHECKSUM_FAILED: RuntimeErrorInfo(
        code=RuntimeErrorCode.MODEL_CHECKSUM_FAILED,
        category=RuntimeErrorCategory.RECOGNITION,
        title="Model checksum verification failed",
        remediation="Delete the corrupted model cache and run `voicekey download` to force a clean re-download.",
        retryable=False,
        safety_critical=True,
    ),
    RuntimeErrorCode.KEYBOARD_BLOCKED: RuntimeErrorInfo(
        code=RuntimeErrorCode.KEYBOARD_BLOCKED,
        category=RuntimeErrorCategory.INJECTION,
        title="Keyboard injection is blocked by the operating system",
        remediation="Grant required input permissions or accessibility permissions, then restart VoiceKey.",
        retryable=False,
        safety_critical=True,
    ),
}


def runtime_error_info(code: RuntimeErrorCode) -> RuntimeErrorInfo:
    """Return runtime error metadata for a typed runtime error code."""
    return _RUNTIME_ERROR_MAP[code]


__all__ = [
    "RuntimeErrorCategory",
    "RuntimeErrorCode",
    "RuntimeErrorInfo",
    "runtime_error_info",
]
