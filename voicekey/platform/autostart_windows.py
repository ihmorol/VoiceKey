"""Windows autostart validation adapter for startup-folder/registry targets."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable

from voicekey.platform.autostart_base import (
    AutostartValidationCode,
    AutostartValidationReport,
    AutostartValidationState,
    DirectoryProbe,
)

DirectoryProbeFn = Callable[[Path], DirectoryProbe]


class WindowsAutostartAdapter:
    """Validate Windows autostart prerequisites with deterministic diagnostics."""

    # Registry key path for Windows Run (autostart)
    # Using normal string with escaped backslashes (not raw string with double backslashes)
    _RUN_KEY = "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run"

    def __init__(
        self,
        *,
        startup_folder: Path | None = None,
        startup_folder_probe: DirectoryProbeFn | None = None,
        registry_run_key_accessible: bool = True,
        registry_run_key_writable: bool = True,
    ) -> None:
        self._startup_folder = startup_folder or _default_startup_folder()
        self._startup_folder_probe = startup_folder_probe or _default_directory_probe
        self._registry_run_key_accessible = registry_run_key_accessible
        self._registry_run_key_writable = registry_run_key_writable

    def validate(self) -> AutostartValidationReport:
        """Return structured autostart capability diagnostics."""

        warnings: list[str] = []
        remediation: list[str] = []
        codes: list[AutostartValidationCode] = []

        startup_available = self._validate_startup_folder(warnings, remediation, codes)
        registry_available = self._validate_registry(warnings, remediation, codes)

        available_count = int(startup_available) + int(registry_available)
        if available_count == 2:
            state = AutostartValidationState.OK
        elif available_count == 1:
            state = AutostartValidationState.DEGRADED
            warnings.append(
                "Only one Windows autostart target is available; setup is partially degraded."
            )
            remediation.append(
                "Restore both startup-folder and registry access for robust Windows autostart behavior."
            )
        else:
            state = AutostartValidationState.UNAVAILABLE
            remediation.append(
                "Neither startup folder nor HKCU Run key is writable. Resolve one target before enabling autostart."
            )

        return AutostartValidationReport(
            backend="windows_autostart",
            platform="windows",
            state=state,
            codes=tuple(dict.fromkeys(codes)),
            warnings=tuple(dict.fromkeys(warnings)),
            remediation=tuple(dict.fromkeys(remediation)),
        )

    def _validate_startup_folder(
        self,
        warnings: list[str],
        remediation: list[str],
        codes: list[AutostartValidationCode],
    ) -> bool:
        probe = self._startup_folder_probe(self._startup_folder)
        if not probe.exists:
            codes.append(AutostartValidationCode.STARTUP_FOLDER_MISSING)
            warnings.append(f"Startup folder path does not exist: {self._startup_folder}")
            remediation.append(
                f"Create startup folder '{self._startup_folder}' and ensure it is writable by the user."
            )
            return False

        if not probe.is_directory:
            codes.append(AutostartValidationCode.STARTUP_FOLDER_INVALID)
            warnings.append(f"Startup folder path is not a directory: {self._startup_folder}")
            remediation.append(
                f"Replace '{self._startup_folder}' with a directory writable by the user."
            )
            return False

        if not probe.writable:
            codes.append(AutostartValidationCode.STARTUP_FOLDER_NOT_WRITABLE)
            warnings.append(f"Startup folder is not writable: {self._startup_folder}")
            remediation.append(
                f"Grant write permissions for '{self._startup_folder}' or use a writable user profile."
            )
            return False

        return True

    def _validate_registry(
        self,
        warnings: list[str],
        remediation: list[str],
        codes: list[AutostartValidationCode],
    ) -> bool:
        if not self._registry_run_key_accessible:
            codes.append(AutostartValidationCode.REGISTRY_KEY_INACCESSIBLE)
            warnings.append(f"Registry run key is inaccessible: {self._RUN_KEY}")
            remediation.append(
                f"Verify user registry access to {self._RUN_KEY} and retry with a standard desktop user profile."
            )
            return False

        if not self._registry_run_key_writable:
            codes.append(AutostartValidationCode.REGISTRY_KEY_NOT_WRITABLE)
            warnings.append(f"Registry run key is read-only: {self._RUN_KEY}")
            remediation.append(
                f"Grant write access to {self._RUN_KEY} or use startup-folder autostart as fallback."
            )
            return False

        return True


def _default_startup_folder() -> Path:
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    return Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"


def _default_directory_probe(path: Path) -> DirectoryProbe:
    exists = path.exists()
    is_directory = exists and path.is_dir()
    writable = is_directory and os.access(path, os.W_OK)
    return DirectoryProbe(exists=exists, is_directory=is_directory, writable=writable)


__all__ = ["WindowsAutostartAdapter"]
