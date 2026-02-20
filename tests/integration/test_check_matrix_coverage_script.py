"""Integration tests for CI matrix coverage script (E10-S06)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def get_script_path() -> Path:
    """Get path to check_matrix_coverage.py script."""
    return Path(__file__).resolve().parents[2] / "scripts" / "ci" / "check_matrix_coverage.py"


def get_report_script_path() -> Path:
    """Get path to generate_matrix_report.py script."""
    return Path(__file__).resolve().parents[2] / "scripts" / "ci" / "generate_matrix_report.py"


def get_workflow_path() -> Path:
    """Get path to CI workflow file."""
    return Path(__file__).resolve().parents[2] / ".github" / "workflows" / "ci.yml"


class TestCheckMatrixCoverageScript:
    """Tests for check_matrix_coverage.py script."""

    def test_script_exists_and_is_executable(self) -> None:
        """Script file exists."""
        script = get_script_path()
        assert script.exists(), f"Script not found: {script}"

    def test_script_runs_successfully_with_default_workflow(self) -> None:
        """Script runs and finds coverage for actual CI workflow."""
        script = get_script_path()
        workflow = get_workflow_path()

        result = subprocess.run(
            [sys.executable, str(script), "--workflow-file", str(workflow)],
            check=False,
            capture_output=True,
            text=True,
        )

        # Should pass since CI workflow has full matrix coverage
        assert result.returncode == 0, f"Script failed: {result.stderr}"

    def test_script_outputs_valid_json(self) -> None:
        """Script outputs valid JSON when requested."""
        script = get_script_path()
        workflow = get_workflow_path()

        result = subprocess.run(
            [sys.executable, str(script), "--workflow-file", str(workflow), "--output-format", "json"],
            check=False,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        output = json.loads(result.stdout)

        # Verify required fields
        assert "status" in output
        assert "required_combinations" in output
        assert "actual_combinations" in output
        assert "missing_combinations" in output
        assert "waived_combinations" in output
        assert "jobs_analyzed" in output
        assert "summary" in output

    def test_script_detects_all_required_combinations(self) -> None:
        """Script detects all 6 required OS/Python combinations."""
        script = get_script_path()
        workflow = get_workflow_path()

        result = subprocess.run(
            [sys.executable, str(script), "--workflow-file", str(workflow), "--output-format", "json"],
            check=False,
            capture_output=True,
            text=True,
        )

        output = json.loads(result.stdout)
        required = output["required_combinations"]

        assert len(required) == 6

        # Verify specific combinations
        required_keys = {f"{r['os']}:{r['python']}" for r in required}
        expected_keys = {
            "ubuntu-22.04:3.11",
            "ubuntu-22.04:3.12",
            "ubuntu-24.04:3.11",
            "ubuntu-24.04:3.12",
            "windows-2022:3.11",
            "windows-2022:3.12",
        }
        assert required_keys == expected_keys

    def test_script_detects_full_coverage(self) -> None:
        """Script reports 100% coverage for actual CI workflow."""
        script = get_script_path()
        workflow = get_workflow_path()

        result = subprocess.run(
            [sys.executable, str(script), "--workflow-file", str(workflow), "--output-format", "json"],
            check=False,
            capture_output=True,
            text=True,
        )

        output = json.loads(result.stdout)

        assert output["status"] == "pass"
        assert output["summary"]["coverage_percent"] == 100.0
        assert output["summary"]["total_missing"] == 0
        assert len(output["missing_combinations"]) == 0

    def test_script_detects_jobs_with_matrix(self) -> None:
        """Script identifies which jobs use matrix strategy."""
        script = get_script_path()
        workflow = get_workflow_path()

        result = subprocess.run(
            [sys.executable, str(script), "--workflow-file", str(workflow), "--output-format", "json"],
            check=False,
            capture_output=True,
            text=True,
        )

        output = json.loads(result.stdout)
        jobs = output["jobs_analyzed"]

        # Should find unit-tests and integration-smoke jobs
        assert "unit-tests" in jobs
        assert "integration-smoke" in jobs

    def test_script_text_output_is_readable(self) -> None:
        """Script produces human-readable text output."""
        script = get_script_path()
        workflow = get_workflow_path()

        result = subprocess.run(
            [sys.executable, str(script), "--workflow-file", str(workflow), "--output-format", "text"],
            check=False,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        output = result.stdout

        # Check for key sections
        assert "CI Matrix Coverage Report" in output
        assert "Status:" in output
        assert "Coverage:" in output
        assert "Required combinations:" in output

    def test_script_fails_on_missing_workflow_file(self) -> None:
        """Script fails gracefully when workflow file doesn't exist."""
        script = get_script_path()

        result = subprocess.run(
            [sys.executable, str(script), "--workflow-file", "/nonexistent/workflow.yml"],
            check=False,
            capture_output=True,
            text=True,
        )

        # Should fail (no coverage possible)
        assert result.returncode != 0

    def test_script_handles_missing_coverage_in_minimal_workflow(self, tmp_path: Path) -> None:
        """Script detects missing coverage in minimal workflow."""
        script = get_script_path()

        # Create minimal workflow with only Ubuntu 24.04 + Python 3.12
        minimal_workflow = tmp_path / "ci.yml"
        minimal_workflow.write_text("""
name: Minimal CI
on: push
jobs:
  test:
    runs-on: ubuntu-24.04
    steps:
      - run: echo test
""")
        # No matrix - should fail

        result = subprocess.run(
            [sys.executable, str(script), "--workflow-file", str(minimal_workflow), "--output-format", "json"],
            check=False,
            capture_output=True,
            text=True,
        )

        output = json.loads(result.stdout)

        # Should have missing combinations
        assert output["status"] == "fail"
        assert output["summary"]["total_missing"] > 0

    def test_script_detects_partial_matrix_coverage(self, tmp_path: Path) -> None:
        """Script detects partial coverage when some combinations missing."""
        script = get_script_path()

        # Create workflow with partial matrix (no Windows)
        partial_workflow = tmp_path / "ci.yml"
        partial_workflow.write_text(r"""
name: Partial CI
on: push
jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-22.04, ubuntu-24.04]
        python-version: ["3.11", "3.12"]
    steps:
      - run: echo test
""")

        result = subprocess.run(
            [sys.executable, str(script), "--workflow-file", str(partial_workflow), "--output-format", "json"],
            check=False,
            capture_output=True,
            text=True,
        )

        output = json.loads(result.stdout)

        # Should be missing Windows combinations
        assert output["status"] == "fail"
        assert output["summary"]["coverage_percent"] < 100.0

        # Check that Windows is specifically missing
        missing_os = {m["os"] for m in output["missing_combinations"]}
        assert "windows-2022" in missing_os


class TestGenerateMatrixReportScript:
    """Tests for generate_matrix_report.py script."""

    def test_script_exists_and_is_executable(self) -> None:
        """Script file exists."""
        script = get_report_script_path()
        assert script.exists(), f"Script not found: {script}"

    def test_script_generates_markdown_report(self) -> None:
        """Script generates valid markdown report."""
        script = get_report_script_path()
        workflow = get_workflow_path()

        result = subprocess.run(
            [sys.executable, str(script), "--workflow-file", str(workflow)],
            check=False,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        output = result.stdout

        # Check for markdown structure
        assert "# CI Matrix Coverage Report" in output
        assert "## Summary" in output
        assert "## Required Matrix" in output

    def test_script_includes_coverage_percentage(self) -> None:
        """Report includes coverage percentage."""
        script = get_report_script_path()
        workflow = get_workflow_path()

        result = subprocess.run(
            [sys.executable, str(script), "--workflow-file", str(workflow)],
            check=False,
            capture_output=True,
            text=True,
        )

        output = result.stdout

        # Should show 100% coverage for actual workflow
        assert "100.0%" in output
        assert "PASS" in output.upper() or "✅" in output

    def test_script_writes_to_file(self, tmp_path: Path) -> None:
        """Script can write report to file."""
        script = get_report_script_path()
        workflow = get_workflow_path()
        output_file = tmp_path / "matrix-coverage.md"

        result = subprocess.run(
            [
                sys.executable, str(script),
                "--workflow-file", str(workflow),
                "--output-file", str(output_file),
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert output_file.exists()
        assert "matrix_report_generated=" in result.stdout

        content = output_file.read_text()
        assert "# CI Matrix Coverage Report" in content

    def test_report_includes_required_combinations_table(self) -> None:
        """Report includes table of required combinations."""
        script = get_report_script_path()
        workflow = get_workflow_path()

        result = subprocess.run(
            [sys.executable, str(script), "--workflow-file", str(workflow)],
            check=False,
            capture_output=True,
            text=True,
        )

        output = result.stdout

        # Check for required combinations in table
        assert "ubuntu-22.04" in output
        assert "ubuntu-24.04" in output
        assert "windows-2022" in output
        assert "3.11" in output
        assert "3.12" in output

    def test_report_includes_jobs_analyzed(self) -> None:
        """Report lists jobs that use matrix strategy."""
        script = get_report_script_path()
        workflow = get_workflow_path()

        result = subprocess.run(
            [sys.executable, str(script), "--workflow-file", str(workflow)],
            check=False,
            capture_output=True,
            text=True,
        )

        output = result.stdout

        assert "## Jobs Analyzed" in output
        assert "unit-tests" in output
        assert "integration-smoke" in output

    def test_report_custom_title(self) -> None:
        """Report can use custom title."""
        script = get_report_script_path()
        workflow = get_workflow_path()

        result = subprocess.run(
            [
                sys.executable, str(script),
                "--workflow-file", str(workflow),
                "--title", "Custom Matrix Report",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        assert "# Custom Matrix Report" in result.stdout

    def test_report_includes_platform_notes(self) -> None:
        """Report includes platform clarification notes."""
        script = get_report_script_path()
        workflow = get_workflow_path()

        result = subprocess.run(
            [sys.executable, str(script), "--workflow-file", str(workflow)],
            check=False,
            capture_output=True,
            text=True,
        )

        output = result.stdout

        assert "## Platform Notes" in output
        assert "Windows 10/11" in output


class TestWaiversHandling:
    """Tests for waiver handling."""

    def test_script_loads_waivers_from_file(self, tmp_path: Path) -> None:
        """Script loads waivers from JSON file."""
        script = get_script_path()

        # Create workflow with partial coverage
        partial_workflow = tmp_path / "ci.yml"
        partial_workflow.write_text(r"""
name: Partial CI
on: push
jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-22.04]
        python-version: ["3.11"]
    steps:
      - run: echo test
""")

        # Create waivers file
        waivers_file = tmp_path / "waivers.json"
        waivers_file.write_text(json.dumps({
            "ubuntu-24.04:3.11": "Temporary infrastructure issue",
        }))

        result = subprocess.run(
            [
                sys.executable, str(script),
                "--workflow-file", str(partial_workflow),
                "--waivers-file", str(waivers_file),
                "--output-format", "json",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        output = json.loads(result.stdout)

        # Should have waived combination
        waived_keys = {f"{w['os']}:{w['python']}" for w in output["waived_combinations"]}
        assert "ubuntu-24.04:3.11" in waived_keys

    def test_strict_mode_fails_with_waivers(self, tmp_path: Path) -> None:
        """Strict mode fails even with waivers."""
        script = get_script_path()

        # Create minimal workflow (missing most combinations)
        minimal_workflow = tmp_path / "ci.yml"
        minimal_workflow.write_text("""
name: Minimal CI
on: push
jobs:
  test:
    runs-on: ubuntu-24.04
    steps:
      - run: echo test
""")

        # Create waivers file
        waivers_file = tmp_path / "waivers.json"
        waivers_file.write_text(json.dumps({
            "ubuntu-22.04:3.11": "Waived",
            "ubuntu-22.04:3.12": "Waived",
            "windows-2022:3.11": "Waived",
            "windows-2022:3.12": "Waived",
            "ubuntu-24.04:3.11": "Waived",
            "ubuntu-24.04:3.12": "Waived",
        }))

        result = subprocess.run(
            [
                sys.executable, str(script),
                "--workflow-file", str(minimal_workflow),
                "--waivers-file", str(waivers_file),
                "--strict",
                "--output-format", "json",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        output = json.loads(result.stdout)

        # Should fail in strict mode even with all waived
        assert output["status"] == "fail"
