"""Release packaging helpers."""

from voicekey.release.windows_artifacts import (
    build_signtool_command,
    build_windows_artifact_name,
    create_portable_zip,
    normalize_version as normalize_windows_version,
    prepare_installer_artifact,
)
from voicekey.release.linux_artifacts import (
    build_appimage_smoke_command,
    build_linux_artifact_name,
    normalize_version as normalize_linux_version,
    prepare_appimage_artifact,
)

__all__ = [
    "build_appimage_smoke_command",
    "build_linux_artifact_name",
    "build_signtool_command",
    "build_windows_artifact_name",
    "create_portable_zip",
    "normalize_linux_version",
    "normalize_windows_version",
    "prepare_appimage_artifact",
    "prepare_installer_artifact",
]
