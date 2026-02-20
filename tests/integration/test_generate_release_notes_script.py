"""Integration tests for release notes generation script (E08-S02)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_generate_release_notes_script_extracts_target_version_section(tmp_path: Path) -> None:
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text(
        "# Changelog\n\n"
        "## [1.2.3] - 2026-02-20\n\n"
        "### Added\n\n"
        "- Release feature\n\n"
        "## [1.2.2] - 2026-02-19\n\n"
        "### Fixed\n\n"
        "- Previous fix\n",
        encoding="utf-8",
    )

    output = tmp_path / "release-notes.md"
    script = Path(__file__).resolve().parents[2] / "scripts" / "release" / "generate_release_notes.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--changelog",
            str(changelog),
            "--version",
            "v1.2.3",
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    generated = output.read_text(encoding="utf-8")
    assert "### Added" in generated
    assert "Release feature" in generated
    assert "Previous fix" not in generated


def test_generate_release_notes_script_can_append_commit_metadata(tmp_path: Path) -> None:
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text(
        "# Changelog\n\n"
        "## [1.2.3] - 2026-02-20\n\n"
        "### Added\n\n"
        "- Release feature\n",
        encoding="utf-8",
    )

    output = tmp_path / "release-notes.md"
    script = Path(__file__).resolve().parents[2] / "scripts" / "release" / "generate_release_notes.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--changelog",
            str(changelog),
            "--version",
            "v1.2.3",
            "--include-commit-metadata",
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    generated = output.read_text(encoding="utf-8")
    assert "## Commit Metadata" in generated
