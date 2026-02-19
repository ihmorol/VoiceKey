"""Unit tests for Windows distribution artifact helpers (E07-S02)."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from voicekey.release.windows_artifacts import (
    build_signtool_command,
    build_windows_artifact_name,
    create_portable_zip,
    normalize_version,
    prepare_installer_artifact,
)


def test_normalize_version_accepts_semver_and_trims_v_prefix() -> None:
    assert normalize_version("1.2.3") == "1.2.3"
    assert normalize_version("v1.2.3") == "1.2.3"


def test_normalize_version_rejects_invalid_version() -> None:
    with pytest.raises(ValueError):
        normalize_version("1.2")


def test_build_windows_artifact_name_matches_required_convention() -> None:
    assert build_windows_artifact_name("1.2.3", artifact_kind="installer") == (
        "voicekey-1.2.3-windows-x64-installer.exe"
    )
    assert build_windows_artifact_name("1.2.3", artifact_kind="portable") == (
        "voicekey-1.2.3-windows-x64-portable.zip"
    )


def test_prepare_installer_artifact_copies_unsigned_installer(tmp_path: Path) -> None:
    unsigned = tmp_path / "unsigned-installer.exe"
    unsigned.write_bytes(b"binary-installer")
    output_dir = tmp_path / "dist"

    final_path = prepare_installer_artifact(
        version="1.2.3",
        unsigned_installer_path=unsigned,
        output_dir=output_dir,
    )

    assert final_path.name == "voicekey-1.2.3-windows-x64-installer.exe"
    assert final_path.read_bytes() == b"binary-installer"


def test_create_portable_zip_builds_named_archive_with_all_files(tmp_path: Path) -> None:
    source_dir = tmp_path / "portable-root"
    nested = source_dir / "bin"
    nested.mkdir(parents=True)
    (source_dir / "voicekey.exe").write_bytes(b"exe")
    (nested / "config.yaml").write_text("version: 3\n", encoding="utf-8")
    output_dir = tmp_path / "dist"

    archive = create_portable_zip(version="1.2.3", source_dir=source_dir, output_dir=output_dir)

    assert archive.name == "voicekey-1.2.3-windows-x64-portable.zip"
    with zipfile.ZipFile(archive, "r") as zipped:
        names = sorted(zipped.namelist())
    assert names == ["bin/config.yaml", "voicekey.exe"]


def test_build_signtool_command_uses_expected_parameters(tmp_path: Path) -> None:
    target = tmp_path / "voicekey-1.2.3-windows-x64-installer.exe"

    command = build_signtool_command(
        signtool_path=Path("C:/SDK/signtool.exe"),
        certificate_thumbprint="ABC123",
        timestamp_url="http://timestamp.digicert.com",
        target_path=target,
    )

    assert command == [
        "C:/SDK/signtool.exe",
        "sign",
        "/sha1",
        "ABC123",
        "/fd",
        "SHA256",
        "/tr",
        "http://timestamp.digicert.com",
        "/td",
        "SHA256",
        str(target),
    ]
