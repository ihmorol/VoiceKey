"""Linux artifact naming and packaging helpers."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

_SEMVER_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)(?:[-+][0-9A-Za-z.-]+)?$")


def normalize_version(version: str) -> str:
    """Normalize version string and validate expected semver format."""
    cleaned = version.strip()
    if not _SEMVER_RE.match(cleaned):
        raise ValueError(f"Invalid version '{version}'. Expected semver format like 1.2.3.")
    return cleaned[1:] if cleaned.startswith("v") else cleaned


def build_linux_artifact_name(version: str) -> str:
    """Build canonical Linux AppImage artifact name from distribution spec."""
    normalized = normalize_version(version)
    return f"voicekey-{normalized}-linux-x86_64.AppImage"


def prepare_appimage_artifact(
    *,
    version: str,
    unsigned_appimage_path: Path,
    output_dir: Path,
) -> Path:
    """Copy AppImage artifact into canonical release filename."""
    if not unsigned_appimage_path.exists() or not unsigned_appimage_path.is_file():
        raise FileNotFoundError(f"Unsigned AppImage file not found: {unsigned_appimage_path}")

    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / build_linux_artifact_name(version)
    shutil.copy2(unsigned_appimage_path, target)
    target.chmod(0o755)
    return target


def build_appimage_smoke_command(appimage_path: Path) -> list[str]:
    """Build deterministic launch smoke command for AppImage artifact."""
    return [str(appimage_path), "--help"]


__all__ = [
    "build_appimage_smoke_command",
    "build_linux_artifact_name",
    "normalize_version",
    "prepare_appimage_artifact",
]
