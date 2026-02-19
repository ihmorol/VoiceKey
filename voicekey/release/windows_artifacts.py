"""Windows artifact naming and packaging helpers."""

from __future__ import annotations

import re
import shutil
import zipfile
from pathlib import Path

_SEMVER_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)(?:[-+][0-9A-Za-z.-]+)?$")


def normalize_version(version: str) -> str:
    """Normalize version string and validate expected semver format."""
    cleaned = version.strip()
    if not _SEMVER_RE.match(cleaned):
        raise ValueError(f"Invalid version '{version}'. Expected semver format like 1.2.3.")
    return cleaned[1:] if cleaned.startswith("v") else cleaned


def build_windows_artifact_name(version: str, *, artifact_kind: str) -> str:
    """Build canonical Windows artifact file names from distribution spec."""
    normalized = normalize_version(version)
    if artifact_kind == "installer":
        suffix = "installer.exe"
    elif artifact_kind == "portable":
        suffix = "portable.zip"
    else:
        raise ValueError(
            f"Unsupported artifact_kind '{artifact_kind}'. Expected 'installer' or 'portable'."
        )
    return f"voicekey-{normalized}-windows-x64-{suffix}"


def prepare_installer_artifact(
    *,
    version: str,
    unsigned_installer_path: Path,
    output_dir: Path,
) -> Path:
    """Copy installer artifact into canonical release filename."""
    if not unsigned_installer_path.exists() or not unsigned_installer_path.is_file():
        raise FileNotFoundError(f"Unsigned installer file not found: {unsigned_installer_path}")

    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / build_windows_artifact_name(version, artifact_kind="installer")
    shutil.copy2(unsigned_installer_path, target)
    return target


def create_portable_zip(*, version: str, source_dir: Path, output_dir: Path) -> Path:
    """Create portable zip artifact using canonical release filename."""
    if not source_dir.exists() or not source_dir.is_dir():
        raise FileNotFoundError(f"Portable source directory not found: {source_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)
    archive_path = output_dir / build_windows_artifact_name(version, artifact_kind="portable")

    with zipfile.ZipFile(archive_path, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source_dir.rglob("*")):
            if path.is_file():
                archive.write(path, arcname=path.relative_to(source_dir))

    return archive_path


def build_signtool_command(
    *,
    signtool_path: Path,
    certificate_thumbprint: str,
    timestamp_url: str,
    target_path: Path,
) -> list[str]:
    """Build deterministic signtool invocation command for artifact signing."""
    return [
        str(signtool_path),
        "sign",
        "/sha1",
        certificate_thumbprint,
        "/fd",
        "SHA256",
        "/tr",
        timestamp_url,
        "/td",
        "SHA256",
        str(target_path),
    ]


__all__ = [
    "build_windows_artifact_name",
    "build_signtool_command",
    "create_portable_zip",
    "normalize_version",
    "prepare_installer_artifact",
]
