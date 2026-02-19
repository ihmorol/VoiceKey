"""Integration tests for release distribution policy validator script (E07-S06)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_validate_distribution_policy_script_passes_on_valid_release_set(tmp_path: Path) -> None:
    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir()
    (artifacts_dir / "voicekey-1.2.3-py3-none-any.whl").write_bytes(b"wheel")
    (artifacts_dir / "voicekey-1.2.3.tar.gz").write_bytes(b"sdist")
    (artifacts_dir / "voicekey-1.2.3-windows-x64-installer.exe").write_bytes(b"installer")
    (artifacts_dir / "voicekey-1.2.3-windows-x64-portable.zip").write_bytes(b"portable")
    (artifacts_dir / "voicekey-1.2.3-linux-x86_64.AppImage").write_bytes(b"appimage")

    checklist = tmp_path / "release-checklist.md"
    checklist.write_text(
        "## Pre-release\n"
        "- [ ] migration notes prepared (if needed)\n"
        "\n"
        "## Post-release\n"
        "- [ ] update compatibility matrix\n",
        encoding="utf-8",
    )

    distribution = tmp_path / "distribution.md"
    distribution.write_text(
        "## 6. Backward Compatibility\n"
        "- one previous major version migration path supported\n",
        encoding="utf-8",
    )

    project_root = Path(__file__).resolve().parents[2]
    script = project_root / "scripts" / "release" / "validate_distribution_policy.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--artifacts-dir",
            str(artifacts_dir),
            "--release-version",
            "1.2.3",
            "--checklist-path",
            str(checklist),
            "--distribution-path",
            str(distribution),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "release_policy=ok" in result.stdout


def test_validate_distribution_policy_script_fails_on_unsupported_architecture(tmp_path: Path) -> None:
    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir()
    (artifacts_dir / "voicekey-1.2.3-py3-none-any.whl").write_bytes(b"wheel")
    (artifacts_dir / "voicekey-1.2.3.tar.gz").write_bytes(b"sdist")
    (artifacts_dir / "voicekey-1.2.3-windows-x64-installer.exe").write_bytes(b"installer")
    (artifacts_dir / "voicekey-1.2.3-windows-x64-portable.zip").write_bytes(b"portable")
    (artifacts_dir / "voicekey-1.2.3-linux-arm64.AppImage").write_bytes(b"appimage")

    checklist = tmp_path / "release-checklist.md"
    checklist.write_text(
        "- [ ] migration notes prepared (if needed)\n"
        "- [ ] update compatibility matrix\n",
        encoding="utf-8",
    )

    distribution = tmp_path / "distribution.md"
    distribution.write_text(
        "- one previous major version migration path supported\n",
        encoding="utf-8",
    )

    project_root = Path(__file__).resolve().parents[2]
    script = project_root / "scripts" / "release" / "validate_distribution_policy.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--artifacts-dir",
            str(artifacts_dir),
            "--release-version",
            "1.2.3",
            "--checklist-path",
            str(checklist),
            "--distribution-path",
            str(distribution),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "release_policy_error=" in result.stdout
