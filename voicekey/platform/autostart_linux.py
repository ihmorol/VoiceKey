"""Linux autostart validation adapter for desktop/systemd-user targets."""

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


class LinuxAutostartAdapter:
    """Validate Linux autostart prerequisites with deterministic diagnostics."""

    def __init__(
        self,
        *,
        desktop_autostart_dir: Path | None = None,
        systemd_user_dir: Path | None = None,
        directory_probe: DirectoryProbeFn | None = None,
    ) -> None:
        home_dir = Path.home()
        self._desktop_autostart_dir = desktop_autostart_dir or home_dir / ".config" / "autostart"
        self._systemd_user_dir = systemd_user_dir or home_dir / ".config" / "systemd" / "user"
        self._directory_probe = directory_probe or _default_directory_probe

    def validate(self) -> AutostartValidationReport:
        """Return structured autostart capability diagnostics."""

        warnings: list[str] = []
        remediation: list[str] = []
        codes: list[AutostartValidationCode] = []

        desktop_available = self._validate_target(
            target_name="Desktop autostart",
            path=self._desktop_autostart_dir,
            missing_code=AutostartValidationCode.DIRECTORY_MISSING,
            invalid_code=AutostartValidationCode.DIRECTORY_INVALID,
            not_writable_code=AutostartValidationCode.DIRECTORY_NOT_WRITABLE,
            warnings=warnings,
            remediation=remediation,
            codes=codes,
        )
        systemd_available = self._validate_target(
            target_name="Systemd user unit",
            path=self._systemd_user_dir,
            missing_code=AutostartValidationCode.DIRECTORY_MISSING,
            invalid_code=AutostartValidationCode.DIRECTORY_INVALID,
            not_writable_code=AutostartValidationCode.DIRECTORY_NOT_WRITABLE,
            warnings=warnings,
            remediation=remediation,
            codes=codes,
        )

        available_count = int(desktop_available) + int(systemd_available)
        if available_count == 2:
            state = AutostartValidationState.OK
        elif available_count == 1:
            state = AutostartValidationState.DEGRADED
            warnings.append(
                "Only one Linux autostart target is available; setup is partially degraded."
            )
            remediation.append(
                "Fix the unavailable Linux autostart target to avoid setup drift across desktop environments."
            )
        else:
            state = AutostartValidationState.UNAVAILABLE
            remediation.append(
                "No Linux autostart target is currently writable. Resolve one target before enabling autostart."
            )

        return AutostartValidationReport(
            backend="linux_autostart",
            platform="linux",
            state=state,
            codes=tuple(dict.fromkeys(codes)),
            warnings=tuple(dict.fromkeys(warnings)),
            remediation=tuple(dict.fromkeys(remediation)),
        )

    def _validate_target(
        self,
        *,
        target_name: str,
        path: Path,
        missing_code: AutostartValidationCode,
        invalid_code: AutostartValidationCode,
        not_writable_code: AutostartValidationCode,
        warnings: list[str],
        remediation: list[str],
        codes: list[AutostartValidationCode],
    ) -> bool:
        probe = self._directory_probe(path)
        if not probe.exists:
            codes.append(missing_code)
            warnings.append(f"{target_name} path does not exist: {path}")
            remediation.append(
                f"Create directory '{path}' and ensure user write permission for Linux autostart setup."
            )
            return False

        if not probe.is_directory:
            codes.append(invalid_code)
            warnings.append(f"{target_name} path is not a directory: {path}")
            remediation.append(
                f"Replace '{path}' with a directory and grant user write permission."
            )
            return False

        if not probe.writable:
            codes.append(not_writable_code)
            warnings.append(f"{target_name} path is not writable: {path}")
            remediation.append(
                f"Fix ownership or permissions so '{path}' is writable by the current user."
            )
            return False

        return True


def _default_directory_probe(path: Path) -> DirectoryProbe:
    exists = path.exists()
    is_directory = exists and path.is_dir()
    writable = is_directory and os.access(path, os.W_OK)
    return DirectoryProbe(exists=exists, is_directory=is_directory, writable=writable)


__all__ = ["LinuxAutostartAdapter"]
