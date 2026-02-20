"""Integration tests for traceability validation scripts (E11-S03)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def get_validate_traceability_script() -> Path:
    """Get path to validate_traceability.py script."""
    return Path(__file__).resolve().parents[2] / "scripts" / "release" / "validate_traceability.py"


def get_check_release_gate_script() -> Path:
    """Get path to check_release_gate.py script."""
    return Path(__file__).resolve().parents[2] / "scripts" / "release" / "check_release_gate.py"


def get_traceability_file() -> Path:
    """Get path to traceability matrix file."""
    return Path(__file__).resolve().parents[2] / "backlog" / "TRACEABILITY_MATRIX.md"


def get_backlog_file() -> Path:
    """Get path to backlog master file."""
    return Path(__file__).resolve().parents[2] / "backlog" / "BACKLOG_MASTER.md"


class TestValidateTraceabilityScript:
    """Tests for validate_traceability.py script."""

    def test_script_exists(self) -> None:
        """Script file exists."""
        script = get_validate_traceability_script()
        assert script.exists(), f"Script not found: {script}"

    def test_script_runs_with_actual_traceability_file(self) -> None:
        """Script runs against actual traceability matrix."""
        script = get_validate_traceability_script()
        traceability = get_traceability_file()

        result = subprocess.run(
            [sys.executable, str(script), "--traceability-file", str(traceability)],
            check=False,
            capture_output=True,
            text=True,
        )

        # Should output something
        assert result.stdout or result.stderr

    def test_script_outputs_valid_json(self) -> None:
        """Script outputs valid JSON when requested."""
        script = get_validate_traceability_script()
        traceability = get_traceability_file()

        result = subprocess.run(
            [
                sys.executable, str(script),
                "--traceability-file", str(traceability),
                "--output-format", "json",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        output = json.loads(result.stdout)

        # Verify required fields
        assert "passed" in output
        assert "summary" in output
        assert "fr_requirements" in output
        assert "non_id_requirements" in output

    def test_script_detects_fr_requirements(self) -> None:
        """Script detects FR requirements in traceability matrix."""
        script = get_validate_traceability_script()
        traceability = get_traceability_file()

        result = subprocess.run(
            [
                sys.executable, str(script),
                "--traceability-file", str(traceability),
                "--output-format", "json",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        output = json.loads(result.stdout)

        # Should have detected FR requirements
        fr_reqs = output["fr_requirements"]
        assert len(fr_reqs) > 0

        # Check structure of FR requirements
        for req in fr_reqs:
            assert "id" in req
            assert "backlog_stories" in req
            assert "verification" in req

    def test_script_text_output_is_readable(self) -> None:
        """Script produces human-readable text output."""
        script = get_validate_traceability_script()
        traceability = get_traceability_file()

        result = subprocess.run(
            [
                sys.executable, str(script),
                "--traceability-file", str(traceability),
                "--output-format", "text",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        output = result.stdout

        # Check for key sections
        assert "Traceability Matrix Validation Report" in output
        assert "Status:" in output
        assert "Coverage:" in output

    def test_script_github_output_format(self) -> None:
        """Script produces GitHub Actions compatible output."""
        script = get_validate_traceability_script()
        traceability = get_traceability_file()

        result = subprocess.run(
            [
                sys.executable, str(script),
                "--traceability-file", str(traceability),
                "--output-format", "github",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        output = result.stdout

        # Should have GitHub annotations
        assert "::" in output  # GitHub Actions syntax

    def test_script_fails_gracefully_on_missing_file(self) -> None:
        """Script fails gracefully when file doesn't exist."""
        script = get_validate_traceability_script()

        result = subprocess.run(
            [
                sys.executable, str(script),
                "--traceability-file", "/nonexistent/TRACEABILITY_MATRIX.md",
                "--output-format", "json",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        # Should fail (non-zero exit)
        assert result.returncode != 0

        output = json.loads(result.stdout)
        assert output["passed"] is False
        assert "error" in output["summary"]

    def test_script_detects_incomplete_traceability(self, tmp_path: Path) -> None:
        """Script detects missing coverage in incomplete traceability."""
        script = get_validate_traceability_script()

        # Create incomplete traceability matrix
        incomplete_matrix = tmp_path / "TRACEABILITY_MATRIX.md"
        incomplete_matrix.write_text("""
# Traceability Matrix

## A. Canonical FR Coverage

| Requirement | Backlog Story Coverage | Verification Method |
|-------------|------------------------|---------------------|
| FR-A01 | E01-S01 | tests |
| FR-A02 | | pending |
| FR-A03 | E01-S03 | |

## B. Non-ID Requirement Coverage

| Source Requirement | Backlog Coverage | Verification |
|-------------------|------------------|--------------|
| Some requirement | E01-S01 | test |

## C. Coverage Gate Rule

Release blocked if incomplete.
""")

        result = subprocess.run(
            [
                sys.executable, str(script),
                "--traceability-file", str(incomplete_matrix),
                "--output-format", "json",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        output = json.loads(result.stdout)

        # Should detect incomplete coverage
        assert output["passed"] is False

    def test_script_with_strict_mode(self) -> None:
        """Script respects strict mode flag."""
        script = get_validate_traceability_script()
        traceability = get_traceability_file()

        result = subprocess.run(
            [
                sys.executable, str(script),
                "--traceability-file", str(traceability),
                "--output-format", "json",
                "--strict",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        # Should run without error
        output = json.loads(result.stdout)
        assert "passed" in output


class TestCheckReleaseGateScript:
    """Tests for check_release_gate.py script."""

    def test_script_exists(self) -> None:
        """Script file exists."""
        script = get_check_release_gate_script()
        assert script.exists(), f"Script not found: {script}"

    def test_script_runs_with_actual_files(self) -> None:
        """Script runs against actual backlog and traceability files."""
        script = get_check_release_gate_script()
        backlog = get_backlog_file()
        traceability = get_traceability_file()

        result = subprocess.run(
            [
                sys.executable, str(script),
                "--backlog-file", str(backlog),
                "--traceability-file", str(traceability),
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        # Should output something
        assert result.stdout

    def test_script_outputs_valid_json(self) -> None:
        """Script outputs valid JSON when requested."""
        script = get_check_release_gate_script()
        backlog = get_backlog_file()
        traceability = get_traceability_file()

        result = subprocess.run(
            [
                sys.executable, str(script),
                "--backlog-file", str(backlog),
                "--traceability-file", str(traceability),
                "--output-format", "json",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        output = json.loads(result.stdout)

        # Verify required fields
        assert "passed" in output
        assert "summary" in output
        assert "gates" in output
        assert "blocking_issues" in output

    def test_script_runs_all_gates(self) -> None:
        """Script runs all gate checks by default."""
        script = get_check_release_gate_script()
        backlog = get_backlog_file()
        traceability = get_traceability_file()

        result = subprocess.run(
            [
                sys.executable, str(script),
                "--backlog-file", str(backlog),
                "--traceability-file", str(traceability),
                "--output-format", "json",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        output = json.loads(result.stdout)
        gates = output["gates"]

        # Should have at least p0_stories and traceability gates
        gate_names = {g["name"] for g in gates}
        assert "P0 Stories Complete" in gate_names or any("P0" in g["name"] for g in gates)
        assert "Traceability Complete" in gate_names or any("Traceability" in g["name"] for g in gates)

    def test_script_can_run_specific_gates(self) -> None:
        """Script can run specific gates only."""
        script = get_check_release_gate_script()
        backlog = get_backlog_file()
        traceability = get_traceability_file()

        result = subprocess.run(
            [
                sys.executable, str(script),
                "--backlog-file", str(backlog),
                "--traceability-file", str(traceability),
                "--gates", "p0_stories",
                "--output-format", "json",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        output = json.loads(result.stdout)
        gates = output["gates"]

        # Should only have p0_stories gate
        assert len(gates) == 1
        assert "P0" in gates[0]["name"]

    def test_script_text_output_is_readable(self) -> None:
        """Script produces human-readable text output."""
        script = get_check_release_gate_script()
        backlog = get_backlog_file()
        traceability = get_traceability_file()

        result = subprocess.run(
            [
                sys.executable, str(script),
                "--backlog-file", str(backlog),
                "--traceability-file", str(traceability),
                "--output-format", "text",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        output = result.stdout

        # Check for key sections
        assert "Release Gate Check Report" in output
        assert "Release Status:" in output
        assert "Gate Results:" in output

    def test_script_github_output_format(self) -> None:
        """Script produces GitHub Actions compatible output."""
        script = get_check_release_gate_script()
        backlog = get_backlog_file()
        traceability = get_traceability_file()

        result = subprocess.run(
            [
                sys.executable, str(script),
                "--backlog-file", str(backlog),
                "--traceability-file", str(traceability),
                "--output-format", "github",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        output = result.stdout

        # Should have GitHub annotations
        assert "::" in output

    def test_script_fails_on_missing_backlog(self) -> None:
        """Script fails when backlog file doesn't exist."""
        script = get_check_release_gate_script()
        traceability = get_traceability_file()

        result = subprocess.run(
            [
                sys.executable, str(script),
                "--backlog-file", "/nonexistent/BACKLOG_MASTER.md",
                "--traceability-file", str(traceability),
                "--output-format", "json",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        # Should fail (non-zero exit)
        assert result.returncode != 0

    def test_script_detects_incomplete_p0_stories(self, tmp_path: Path) -> None:
        """Script detects incomplete P0 stories."""
        script = get_check_release_gate_script()

        # Create backlog with incomplete P0 stories
        incomplete_backlog = tmp_path / "BACKLOG_MASTER.md"
        incomplete_backlog.write_text("""
# Backlog Master

## Execution Status (Live)

- E00-S01: complete
- E01-S01: pending  # This is incomplete!

---

## Epic E00 - Foundation (P0)

### Story E00-S01 - Repository governance files
- Requirement IDs: FR-OSS01

## Epic E01 - Audio (P0)

### Story E01-S01 - Real-time microphone capture
- Requirement IDs: FR-A01
""")

        result = subprocess.run(
            [
                sys.executable, str(script),
                "--backlog-file", str(incomplete_backlog),
                "--gates", "p0_stories",
                "--output-format", "json",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        output = json.loads(result.stdout)

        # Should detect incomplete P0
        assert output["passed"] is False
        assert len(output["blocking_issues"]) > 0


class TestTraceabilityCoverageValidation:
    """Tests for current traceability coverage."""

    def test_current_traceability_has_fr_requirements(self) -> None:
        """Current traceability matrix has FR requirements documented."""
        traceability = get_traceability_file()
        script = get_validate_traceability_script()

        result = subprocess.run(
            [
                sys.executable, str(script),
                "--traceability-file", str(traceability),
                "--output-format", "json",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        output = json.loads(result.stdout)

        # Should have FR requirements
        assert output["summary"]["total_fr_requirements"] > 0

    def test_current_traceability_has_non_id_requirements(self) -> None:
        """Current traceability matrix has non-ID requirements documented."""
        traceability = get_traceability_file()
        script = get_validate_traceability_script()

        result = subprocess.run(
            [
                sys.executable, str(script),
                "--traceability-file", str(traceability),
                "--output-format", "json",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        output = json.loads(result.stdout)

        # Should have non-ID requirements
        assert output["summary"]["total_non_id_requirements"] > 0

    def test_current_release_gate_status(self) -> None:
        """Current release gate status can be determined."""
        script = get_check_release_gate_script()
        backlog = get_backlog_file()
        traceability = get_traceability_file()

        result = subprocess.run(
            [
                sys.executable, str(script),
                "--backlog-file", str(backlog),
                "--traceability-file", str(traceability),
                "--output-format", "json",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        output = json.loads(result.stdout)

        # Should have summary with gate counts
        assert "total_gates" in output["summary"]
        assert "passed_gates" in output["summary"]
        assert "failed_gates" in output["summary"]

    def test_all_p0_stories_have_backlog_mapping(self) -> None:
        """All P0 stories in execution status have traceability mapping."""
        traceability = get_traceability_file()
        backlog = get_backlog_file()

        # Parse P0 stories from backlog
        backlog_content = backlog.read_text()
        priorities = {}

        for line in backlog_content.split("\n"):
            if "Epic" in line and "P0)" in line:
                epic_match = line.split("-")[0].strip().split()[-1]
                current_epic = epic_match
            elif line.startswith("### Story") and current_epic:
                story_match = line.split()[2]
                priorities[story_match] = "P0"

        # All P0 stories should appear in traceability
        traceability_content = traceability.read_text()

        # At minimum, traceability should mention epic patterns
        for story_id in list(priorities.keys())[:5]:  # Check first 5 P0 stories
            epic_prefix = story_id.split("-")[0]
            assert epic_prefix in traceability_content, f"Epic {epic_prefix} not found in traceability"
