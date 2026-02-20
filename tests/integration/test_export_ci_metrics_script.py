"""Integration tests for CI metrics export script (E08-S04)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_export_ci_metrics_outputs_valid_json_to_stdout() -> None:
    script = Path(__file__).resolve().parents[2] / "scripts" / "ci" / "export_ci_metrics.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--workflow-name",
            "PR Validation",
            "--run-id",
            "12345",
            "--event",
            "pull_request",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["workflow_name"] == "PR Validation"
    assert output["run_id"] == "12345"
    assert output["event"] == "pull_request"
    assert "timestamp_utc" in output
    assert "duration_seconds" in output
    assert "job_results" in output
    assert "matrix_summary" in output
    assert "summary" in output


def test_export_ci_metrics_writes_to_file(tmp_path: Path) -> None:
    output_file = tmp_path / "metrics.json"
    
    script = Path(__file__).resolve().parents[2] / "scripts" / "ci" / "export_ci_metrics.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--output-file",
            str(output_file),
            "--workflow-name",
            "Release Pipeline",
            "--run-id",
            "67890",
            "--branch",
            "main",
            "--commit-sha",
            "abc123",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert output_file.exists()
    assert "ci_metrics_exported=" in result.stdout
    
    output = json.loads(output_file.read_text(encoding="utf-8"))
    assert output["workflow_name"] == "Release Pipeline"
    assert output["branch"] == "main"
    assert output["commit_sha"] == "abc123"


def test_export_ci_metrics_parses_job_results(tmp_path: Path) -> None:
    output_file = tmp_path / "metrics.json"
    job_results = json.dumps({
        "lint": {"result": "success", "duration_seconds": 30},
        "unit-tests": {"result": "success", "duration_seconds": 120},
        "integration-smoke": {"result": "failure", "duration_seconds": 45},
    })
    
    script = Path(__file__).resolve().parents[2] / "scripts" / "ci" / "export_ci_metrics.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--output-file",
            str(output_file),
            "--job-results",
            job_results,
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    output = json.loads(output_file.read_text(encoding="utf-8"))
    
    assert output["job_results"]["lint"]["result"] == "success"
    assert output["job_results"]["unit-tests"]["result"] == "success"
    assert output["job_results"]["integration-smoke"]["result"] == "failure"


def test_export_ci_metrics_calculates_summary_correctly(tmp_path: Path) -> None:
    output_file = tmp_path / "metrics.json"
    job_results = json.dumps({
        "lint": {"result": "success"},
        "unit-tests": {"result": "success"},
        "integration-smoke": {"result": "success"},
        "package-smoke": {"result": "success"},
        "some-smoke-test": {"result": "failure"},
    })
    
    script = Path(__file__).resolve().parents[2] / "scripts" / "ci" / "export_ci_metrics.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--output-file",
            str(output_file),
            "--job-results",
            job_results,
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    output = json.loads(output_file.read_text(encoding="utf-8"))
    
    assert output["summary"]["overall_result"] == "failure"
    # 3 smoke jobs: integration-smoke, package-smoke, some-smoke-test
    # 2 passed (integration-smoke, package-smoke), 1 failed (some-smoke-test)
    # Script rounds to 3 decimal places
    assert output["summary"]["smoke_pass_rate"] == round(2/3, 3)
    assert output["matrix_summary"]["total_jobs"] == 5
    assert output["matrix_summary"]["passed_jobs"] == 4
    assert output["matrix_summary"]["failed_jobs"] == 1


def test_export_ci_metrics_handles_empty_job_results(tmp_path: Path) -> None:
    output_file = tmp_path / "metrics.json"
    
    script = Path(__file__).resolve().parents[2] / "scripts" / "ci" / "export_ci_metrics.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--output-file",
            str(output_file),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    output = json.loads(output_file.read_text(encoding="utf-8"))
    
    assert output["job_results"] == {}
    assert output["summary"]["overall_result"] == "unknown"
    assert output["summary"]["smoke_pass_rate"] == 1.0


def test_export_ci_metrics_parses_matrix_os_and_python(tmp_path: Path) -> None:
    output_file = tmp_path / "metrics.json"
    
    script = Path(__file__).resolve().parents[2] / "scripts" / "ci" / "export_ci_metrics.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--output-file",
            str(output_file),
            "--matrix-os",
            "ubuntu-22.04,ubuntu-24.04,windows-2022",
            "--matrix-python",
            "3.11,3.12",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    output = json.loads(output_file.read_text(encoding="utf-8"))
    
    assert "ubuntu-22.04" in output["matrix_summary"]["os_list"]
    assert "ubuntu-24.04" in output["matrix_summary"]["os_list"]
    assert "windows-2022" in output["matrix_summary"]["os_list"]
    assert "3.11" in output["matrix_summary"]["python_versions"]
    assert "3.12" in output["matrix_summary"]["python_versions"]
