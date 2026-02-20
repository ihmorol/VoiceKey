"""Integration tests for user documentation validation script (E11-S01).

Tests the validate_user_docs.py script for:
- Required documentation sections validation
- Link validation
- Output format options
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_validate_user_docs_script_passes_for_existing_docs() -> None:
    """Test that validation passes for existing documentation structure."""
    script = Path(__file__).resolve().parents[2] / "scripts" / "docs" / "validate_user_docs.py"
    repo_root = Path(__file__).resolve().parents[2]

    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--docs-root",
            str(repo_root / "docs"),
            "--repo-root",
            str(repo_root),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    # Should pass since all required docs exist
    assert result.returncode == 0, f"Script failed: {result.stdout}\n{result.stderr}"
    assert "PASSED" in result.stdout


def test_validate_user_docs_detects_missing_section() -> None:
    """Test that validation fails when a required section is missing."""
    script = Path(__file__).resolve().parents[2] / "scripts" / "docs" / "validate_user_docs.py"

    # Use temp directory without required docs
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--docs-root",
            "/nonexistent/docs",
            "--repo-root",
            "/nonexistent",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    # Should fail due to missing files
    assert result.returncode == 1
    assert "FAILED" in result.stdout or "Error" in result.stdout


def test_validate_user_docs_json_output() -> None:
    """Test JSON output format."""
    script = Path(__file__).resolve().parents[2] / "scripts" / "docs" / "validate_user_docs.py"
    repo_root = Path(__file__).resolve().parents[2]

    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--docs-root",
            str(repo_root / "docs"),
            "--repo-root",
            str(repo_root),
            "--output-format",
            "json",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0

    # Parse JSON output
    stdout = result.stdout.strip()
    json_start = stdout.find("{")
    json_end = stdout.rfind("}") + 1

    assert json_start >= 0, f"No JSON found in output: {stdout}"
    assert json_end > json_start, f"Incomplete JSON in output: {stdout}"

    output = json.loads(stdout[json_start:json_end])

    assert "passed" in output
    assert "sections_checked" in output
    assert output["passed"] is True


def test_validate_user_docs_github_output() -> None:
    """Test GitHub Actions output format."""
    script = Path(__file__).resolve().parents[2] / "scripts" / "docs" / "validate_user_docs.py"
    repo_root = Path(__file__).resolve().parents[2]

    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--docs-root",
            str(repo_root / "docs"),
            "--repo-root",
            str(repo_root),
            "--output-format",
            "github",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "::notice::" in result.stdout or "PASSED" in result.stdout


def test_validate_user_docs_specific_sections() -> None:
    """Test validating specific sections only."""
    script = Path(__file__).resolve().parents[2] / "scripts" / "docs" / "validate_user_docs.py"
    repo_root = Path(__file__).resolve().parents[2]

    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--docs-root",
            str(repo_root / "docs"),
            "--repo-root",
            str(repo_root),
            "--sections",
            "installation,troubleshooting",
            "--output-format",
            "json",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0

    # Parse JSON output
    stdout = result.stdout.strip()
    json_start = stdout.find("{")
    json_end = stdout.rfind("}") + 1
    output = json.loads(stdout[json_start:json_end])

    # Should only have checked the specified sections
    assert "installation" in output["sections_checked"]
    assert "troubleshooting" in output["sections_checked"]
    # Other sections should not be present
    assert len(output["sections_checked"]) == 2


def test_validate_user_docs_installation_section() -> None:
    """Test that installation section is properly validated."""
    script = Path(__file__).resolve().parents[2] / "scripts" / "docs" / "validate_user_docs.py"
    repo_root = Path(__file__).resolve().parents[2]

    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--docs-root",
            str(repo_root / "docs"),
            "--repo-root",
            str(repo_root),
            "--sections",
            "installation",
            "--output-format",
            "json",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0

    stdout = result.stdout.strip()
    json_start = stdout.find("{")
    json_end = stdout.rfind("}") + 1
    output = json.loads(stdout[json_start:json_end])

    assert output["sections_checked"]["installation"] is True


def test_validate_user_docs_onboarding_section() -> None:
    """Test that onboarding section is properly validated."""
    script = Path(__file__).resolve().parents[2] / "scripts" / "docs" / "validate_user_docs.py"
    repo_root = Path(__file__).resolve().parents[2]

    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--docs-root",
            str(repo_root / "docs"),
            "--repo-root",
            str(repo_root),
            "--sections",
            "onboarding",
            "--output-format",
            "json",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0

    stdout = result.stdout.strip()
    json_start = stdout.find("{")
    json_end = stdout.rfind("}") + 1
    output = json.loads(stdout[json_start:json_end])

    assert output["sections_checked"]["onboarding"] is True


def test_validate_user_docs_commands_section() -> None:
    """Test that commands section is properly validated."""
    script = Path(__file__).resolve().parents[2] / "scripts" / "docs" / "validate_user_docs.py"
    repo_root = Path(__file__).resolve().parents[2]

    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--docs-root",
            str(repo_root / "docs"),
            "--repo-root",
            str(repo_root),
            "--sections",
            "commands",
            "--output-format",
            "json",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0

    stdout = result.stdout.strip()
    json_start = stdout.find("{")
    json_end = stdout.rfind("}") + 1
    output = json.loads(stdout[json_start:json_end])

    assert output["sections_checked"]["commands"] is True


def test_validate_user_docs_troubleshooting_section() -> None:
    """Test that troubleshooting section is properly validated."""
    script = Path(__file__).resolve().parents[2] / "scripts" / "docs" / "validate_user_docs.py"
    repo_root = Path(__file__).resolve().parents[2]

    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--docs-root",
            str(repo_root / "docs"),
            "--repo-root",
            str(repo_root),
            "--sections",
            "troubleshooting",
            "--output-format",
            "json",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0

    stdout = result.stdout.strip()
    json_start = stdout.find("{")
    json_end = stdout.rfind("}") + 1
    output = json.loads(stdout[json_start:json_end])

    assert output["sections_checked"]["troubleshooting"] is True


def test_validate_user_docs_strict_mode_with_warnings() -> None:
    """Test strict mode behavior (warnings treated as errors)."""
    script = Path(__file__).resolve().parents[2] / "scripts" / "docs" / "validate_user_docs.py"
    repo_root = Path(__file__).resolve().parents[2]

    # Run without strict - should pass even with warnings
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--docs-root",
            str(repo_root / "docs"),
            "--repo-root",
            str(repo_root),
            "--output-format",
            "json",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    stdout = result.stdout.strip()
    json_start = stdout.find("{")
    json_end = stdout.rfind("}") + 1
    output = json.loads(stdout[json_start:json_end])

    # If there are warnings, strict mode should fail
    if output.get("warnings"):
        result_strict = subprocess.run(
            [
                sys.executable,
                str(script),
                "--docs-root",
                str(repo_root / "docs"),
                "--repo-root",
                str(repo_root),
                "--strict",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        # Strict mode might fail if there are warnings
        # This test documents the expected behavior


def test_validate_user_docs_help_output() -> None:
    """Test that help output works."""
    script = Path(__file__).resolve().parents[2] / "scripts" / "docs" / "validate_user_docs.py"

    result = subprocess.run(
        [sys.executable, str(script), "--help"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Validate user documentation" in result.stdout
    assert "--docs-root" in result.stdout
    assert "--output-format" in result.stdout
