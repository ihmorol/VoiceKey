"""Integration tests for post-publish release smoke script (E08-S03/E10-S04)."""

from __future__ import annotations

import subprocess
import sys
import zipfile
from pathlib import Path


def test_post_publish_smoke_script_supports_pypi_dry_run(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[2]
    script = project_root / "scripts" / "release" / "run_post_publish_smoke.py"

    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--channel",
            "pypi",
            "--version",
            "1.2.3",
            "--dry-run",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "smoke_command=" in result.stdout
    assert "voicekey==1.2.3" in result.stdout


def test_post_publish_smoke_script_validates_windows_portable_archive(tmp_path: Path) -> None:
    archive = tmp_path / "voicekey-1.2.3-windows-x64-portable.zip"
    with zipfile.ZipFile(archive, mode="w", compression=zipfile.ZIP_DEFLATED) as payload:
        payload.writestr("voicekey.exe", "binary")

    project_root = Path(__file__).resolve().parents[2]
    script = project_root / "scripts" / "release" / "run_post_publish_smoke.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--channel",
            "windows-portable",
            "--version",
            "1.2.3",
            "--artifact-path",
            str(archive),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "post_publish_smoke=ok channel=windows-portable" in result.stdout
