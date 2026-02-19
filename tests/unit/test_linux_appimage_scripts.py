"""Unit tests for Linux AppImage build/smoke scripts (E07-S03)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_build_and_smoke_scripts_create_and_launch_canonical_appimage(tmp_path: Path) -> None:
    unsigned = tmp_path / "unsigned.AppImage"
    unsigned.write_text(
        "#!/usr/bin/env sh\n"
        "if [ \"$1\" = \"--help\" ]; then\n"
        "  echo \"voicekey appimage\"\n"
        "  exit 0\n"
        "fi\n"
        "exit 0\n",
        encoding="utf-8",
    )
    unsigned.chmod(0o755)

    output_dir = tmp_path / "dist"
    project_root = Path(__file__).resolve().parents[2]

    build_script = project_root / "scripts" / "linux" / "build_appimage.py"
    smoke_script = project_root / "scripts" / "linux" / "smoke_launch_appimage.py"

    build_result = subprocess.run(
        [
            sys.executable,
            str(build_script),
            "--version",
            "1.2.3",
            "--unsigned-appimage-path",
            str(unsigned),
            "--output-dir",
            str(output_dir),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert build_result.returncode == 0
    artifact = output_dir / "voicekey-1.2.3-linux-x86_64.AppImage"
    assert artifact.exists()

    smoke_result = subprocess.run(
        [
            sys.executable,
            str(smoke_script),
            "--appimage-path",
            str(artifact),
            "--timeout-seconds",
            "5",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert smoke_result.returncode == 0
