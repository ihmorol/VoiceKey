"""Unit tests for Linux artifact helpers (E07-S03)."""

from __future__ import annotations

from pathlib import Path

import pytest

from voicekey.release.linux_artifacts import (
    build_appimage_smoke_command,
    build_linux_artifact_name,
    normalize_version,
    prepare_appimage_artifact,
)


def test_normalize_version_accepts_semver_and_trims_v_prefix() -> None:
    assert normalize_version("1.2.3") == "1.2.3"
    assert normalize_version("v1.2.3") == "1.2.3"


def test_normalize_version_rejects_invalid_version() -> None:
    with pytest.raises(ValueError):
        normalize_version("1.2")


def test_build_linux_artifact_name_matches_required_convention() -> None:
    assert build_linux_artifact_name("1.2.3") == "voicekey-1.2.3-linux-x86_64.AppImage"


def test_prepare_appimage_artifact_copies_to_canonical_name(tmp_path: Path) -> None:
    unsigned = tmp_path / "voicekey-test.AppImage"
    unsigned.write_bytes(b"appimage")

    artifact = prepare_appimage_artifact(
        version="1.2.3",
        unsigned_appimage_path=unsigned,
        output_dir=tmp_path / "dist",
    )

    assert artifact.name == "voicekey-1.2.3-linux-x86_64.AppImage"
    assert artifact.read_bytes() == b"appimage"


def test_build_appimage_smoke_command_is_deterministic(tmp_path: Path) -> None:
    appimage = tmp_path / "voicekey-1.2.3-linux-x86_64.AppImage"

    command = build_appimage_smoke_command(appimage)

    assert command == [str(appimage), "--help"]
