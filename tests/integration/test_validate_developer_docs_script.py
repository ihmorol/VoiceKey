"""Integration tests for developer docs validation script (E11-S02).

Requirements: E11-S02, FR-OSS05
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_validate_developer_docs_script_passes_with_valid_docs() -> None:
    """Test that validation passes with all required docs present."""
    script = Path(__file__).resolve().parents[2] / "scripts" / "docs" / "validate_developer_docs.py"
    result = subprocess.run(
        [sys.executable, str(script)],
        check=False,
        capture_output=True,
        text=True,
    )

    # Should pass since all docs exist in the project
    assert result.returncode == 0
    assert "PASSED" in result.stdout


def test_validate_developer_docs_script_json_output() -> None:
    """Test JSON output format."""
    script = Path(__file__).resolve().parents[2] / "scripts" / "docs" / "validate_developer_docs.py"
    result = subprocess.run(
        [sys.executable, str(script), "--output-format", "json"],
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
    assert "checks" in output
    assert output["passed"] is True
    assert output["total_checks"] > 0
    assert output["failed_checks"] == 0


def test_validate_developer_docs_script_specific_docs() -> None:
    """Test validation of specific docs only."""
    script = Path(__file__).resolve().parents[2] / "scripts" / "docs" / "validate_developer_docs.py"
    result = subprocess.run(
        [sys.executable, str(script), "--docs", "CONTRIBUTING.md", "--output-format", "json"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0

    stdout = result.stdout.strip()
    json_start = stdout.find("{")
    json_end = stdout.rfind("}") + 1
    output = json.loads(stdout[json_start:json_end])

    # Should only have checks for CONTRIBUTING.md
    check_names = [c["name"] for c in output["checks"]]
    assert any("CONTRIBUTING" in name for name in check_names)


def test_validate_developer_docs_script_detects_missing_doc(tmp_path: Path) -> None:
    """Test that validation detects missing documentation."""
    script = Path(__file__).resolve().parents[2] / "scripts" / "docs" / "validate_developer_docs.py"

    # Create a minimal project structure without CONTRIBUTING.md
    project_root = tmp_path / "test_project"
    project_root.mkdir()
    (project_root / "software_requirements.md").write_text("# Test", encoding="utf-8")
    (project_root / "requirements").mkdir()

    result = subprocess.run(
        [sys.executable, str(script), "--project-root", str(project_root), "--output-format", "json"],
        check=False,
        capture_output=True,
        text=True,
    )

    # Should fail due to missing docs
    assert result.returncode == 1

    stdout = result.stdout.strip()
    json_start = stdout.find("{")
    json_end = stdout.rfind("}") + 1
    output = json.loads(stdout[json_start:json_end])

    assert output["passed"] is False
    assert output["failed_checks"] > 0


def test_validate_developer_docs_script_checks_contributing_sections() -> None:
    """Test that CONTRIBUTING.md required sections are validated."""
    script = Path(__file__).resolve().parents[2] / "scripts" / "docs" / "validate_developer_docs.py"
    result = subprocess.run(
        [sys.executable, str(script), "--docs", "CONTRIBUTING.md", "--output-format", "json"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0

    stdout = result.stdout.strip()
    json_start = stdout.find("{")
    json_end = stdout.rfind("}") + 1
    output = json.loads(stdout[json_start:json_end])

    # Check that CONTRIBUTING.md sections were validated
    check_names = [c["name"] for c in output["checks"]]
    assert any("sections:CONTRIBUTING" in name for name in check_names)
    assert any("dco:CONTRIBUTING" in name for name in check_names)


def test_validate_developer_docs_script_checks_compatibility_matrix() -> None:
    """Test that compatibility matrix is validated."""
    script = Path(__file__).resolve().parents[2] / "scripts" / "docs" / "validate_developer_docs.py"
    result = subprocess.run(
        [sys.executable, str(script), "--docs", "docs/compatibility-matrix.md", "--output-format", "json"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0

    stdout = result.stdout.strip()
    json_start = stdout.find("{")
    json_end = stdout.rfind("}") + 1
    output = json.loads(stdout[json_start:json_end])

    # Check that compatibility matrix sections were validated
    check_names = [c["name"] for c in output["checks"]]
    assert any("compatibility-matrix" in name for name in check_names)


def test_validate_developer_docs_script_checks_agents_md() -> None:
    """Test that AGENTS.md is validated."""
    script = Path(__file__).resolve().parents[2] / "scripts" / "docs" / "validate_developer_docs.py"
    result = subprocess.run(
        [sys.executable, str(script), "--docs", "AGENTS.md", "--output-format", "json"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0

    stdout = result.stdout.strip()
    json_start = stdout.find("{")
    json_end = stdout.rfind("}") + 1
    output = json.loads(stdout[json_start:json_end])

    # Check that AGENTS.md sections were validated
    check_names = [c["name"] for c in output["checks"]]
    assert any("sections:AGENTS" in name for name in check_names)


def test_validate_developer_docs_script_checks_development_md() -> None:
    """Test that requirements/development.md is validated."""
    script = Path(__file__).resolve().parents[2] / "scripts" / "docs" / "validate_developer_docs.py"
    result = subprocess.run(
        [sys.executable, str(script), "--docs", "requirements/development.md", "--output-format", "json"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0

    stdout = result.stdout.strip()
    json_start = stdout.find("{")
    json_end = stdout.rfind("}") + 1
    output = json.loads(stdout[json_start:json_end])

    # Check that development.md sections were validated
    check_names = [c["name"] for c in output["checks"]]
    assert any("development.md" in name for name in check_names)


def test_validate_developer_docs_script_checks_devops_md() -> None:
    """Test that requirements/devops-cicd.md is validated."""
    script = Path(__file__).resolve().parents[2] / "scripts" / "docs" / "validate_developer_docs.py"
    result = subprocess.run(
        [sys.executable, str(script), "--docs", "requirements/devops-cicd.md", "--output-format", "json"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0

    stdout = result.stdout.strip()
    json_start = stdout.find("{")
    json_end = stdout.rfind("}") + 1
    output = json.loads(stdout[json_start:json_end])

    # Check that devops-cicd.md sections were validated
    check_names = [c["name"] for c in output["checks"]]
    assert any("devops-cicd.md" in name for name in check_names)


def test_validate_developer_docs_script_checks_docs_alignment() -> None:
    """Test that docs alignment with implementation is validated."""
    script = Path(__file__).resolve().parents[2] / "scripts" / "docs" / "validate_developer_docs.py"
    result = subprocess.run(
        [sys.executable, str(script), "--docs", "alignment", "--output-format", "json"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0

    stdout = result.stdout.strip()
    json_start = stdout.find("{")
    json_end = stdout.rfind("}") + 1
    output = json.loads(stdout[json_start:json_end])

    # Check that alignment was validated
    check_names = [c["name"] for c in output["checks"]]
    assert any("alignment" in name for name in check_names)


def test_validate_developer_docs_script_text_output_format() -> None:
    """Test text output format."""
    script = Path(__file__).resolve().parents[2] / "scripts" / "docs" / "validate_developer_docs.py"
    result = subprocess.run(
        [sys.executable, str(script), "--output-format", "text"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Developer Documentation Validation Report" in result.stdout
    assert "✅" in result.stdout  # Check marks for passed tests


def test_validate_developer_docs_script_invalid_project_root() -> None:
    """Test error handling for invalid project root."""
    script = Path(__file__).resolve().parents[2] / "scripts" / "docs" / "validate_developer_docs.py"
    result = subprocess.run(
        [sys.executable, str(script), "--project-root", "/nonexistent/path"],
        check=False,
        capture_output=True,
        text=True,
    )

    # Should fail due to invalid project root
    assert result.returncode == 2
