"""Shared autostart validation contracts and diagnostics models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class AutostartValidationState(StrEnum):
    """Capability state returned by autostart adapter validation."""

    OK = "ok"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


class AutostartValidationCode(StrEnum):
    """Deterministic error/degradation codes surfaced by adapters."""

    DIRECTORY_MISSING = "directory_missing"
    DIRECTORY_INVALID = "directory_invalid"
    DIRECTORY_NOT_WRITABLE = "directory_not_writable"
    STARTUP_FOLDER_MISSING = "startup_folder_missing"
    STARTUP_FOLDER_INVALID = "startup_folder_invalid"
    STARTUP_FOLDER_NOT_WRITABLE = "startup_folder_not_writable"
    REGISTRY_KEY_INACCESSIBLE = "registry_key_inaccessible"
    REGISTRY_KEY_NOT_WRITABLE = "registry_key_not_writable"


@dataclass(frozen=True)
class DirectoryProbe:
    """Filesystem access result for a directory-like autostart target."""

    exists: bool
    is_directory: bool
    writable: bool

    @property
    def available(self) -> bool:
        """Whether target can be used for autostart writes now."""

        return self.exists and self.is_directory and self.writable


@dataclass(frozen=True)
class AutostartValidationReport:
    """Structured autostart capability diagnostics."""

    backend: str
    platform: str
    state: AutostartValidationState
    codes: tuple[AutostartValidationCode, ...]
    warnings: tuple[str, ...]
    remediation: tuple[str, ...]


__all__ = [
    "AutostartValidationCode",
    "AutostartValidationReport",
    "AutostartValidationState",
    "DirectoryProbe",
]
