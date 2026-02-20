"""Integration tests for CI performance guardrail script (E08-S01, E10-S03)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_perf_guardrail_script_passes_when_metrics_within_thresholds(tmp_path: Path) -> None:
    metrics_path = tmp_path / "metrics.json"
    metrics_path.write_text(json.dumps({"p50_ms": 180, "p95_ms": 320}), encoding="utf-8")

    script = Path(__file__).resolve().parents[2] / "scripts" / "ci" / "check_perf_guardrails.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--metrics-file",
            str(metrics_path),
            "--enforce",
            "1",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "perf_guardrail=ok" in result.stdout


def test_perf_guardrail_script_soft_fails_when_not_enforced(tmp_path: Path) -> None:
    metrics_path = tmp_path / "metrics.json"
    metrics_path.write_text(json.dumps({"p50_ms": 220, "p95_ms": 360}), encoding="utf-8")

    script = Path(__file__).resolve().parents[2] / "scripts" / "ci" / "check_perf_guardrails.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--metrics-file",
            str(metrics_path),
            "--enforce",
            "0",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "perf_guardrail=soft_fail" in result.stdout


def test_perf_guardrail_script_fails_when_enforced_and_thresholds_exceeded(tmp_path: Path) -> None:
    metrics_path = tmp_path / "metrics.json"
    metrics_path.write_text(json.dumps({"p50_ms": 240, "p95_ms": 410}), encoding="utf-8")

    script = Path(__file__).resolve().parents[2] / "scripts" / "ci" / "check_perf_guardrails.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--metrics-file",
            str(metrics_path),
            "--enforce",
            "true",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    # New format uses THRESHOLD VIOLATIONS instead of perf_guardrail_violation=
    assert "VIOLATION" in result.stdout.upper() or "exceeds" in result.stdout.lower()


def test_perf_guardrail_script_with_summary_format(tmp_path: Path) -> None:
    """Test that the script handles summary format correctly."""
    metrics_path = tmp_path / "metrics.json"
    metrics_path.write_text(
        json.dumps({
            "results": [
                {"name": "test1", "p50_ms": 50, "p95_ms": 100},
                {"name": "test2", "p50_ms": 75, "p95_ms": 150},
            ],
            "summary": {
                "max_p50_ms": 75,
                "max_p95_ms": 150,
            },
        }),
        encoding="utf-8",
    )

    script = Path(__file__).resolve().parents[2] / "scripts" / "ci" / "check_perf_guardrails.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--metrics-file",
            str(metrics_path),
            "--enforce",
            "1",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "perf_guardrail=ok" in result.stdout


def test_perf_guardrail_script_with_results_array(tmp_path: Path) -> None:
    """Test that the script computes metrics from results array."""
    metrics_path = tmp_path / "metrics.json"
    metrics_path.write_text(
        json.dumps({
            "results": [
                {"name": "test1", "p50_ms": 50, "p95_ms": 100},
                {"name": "test2", "p50_ms": 75, "p95_ms": 150},
            ],
        }),
        encoding="utf-8",
    )

    script = Path(__file__).resolve().parents[2] / "scripts" / "ci" / "check_perf_guardrails.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--metrics-file",
            str(metrics_path),
            "--enforce",
            "1",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "perf_guardrail=ok" in result.stdout


def test_perf_guardrail_script_with_baseline_comparison(tmp_path: Path) -> None:
    """Test that the script compares against baseline for regression."""
    # Create baseline
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(
        json.dumps({"p50_ms": 50, "p95_ms": 100}),
        encoding="utf-8",
    )

    # Create current metrics with regression
    metrics_path = tmp_path / "metrics.json"
    metrics_path.write_text(
        json.dumps({"p50_ms": 70, "p95_ms": 130}),  # 40% and 30% regression
        encoding="utf-8",
    )

    script = Path(__file__).resolve().parents[2] / "scripts" / "ci" / "check_perf_guardrails.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--metrics-file",
            str(metrics_path),
            "--baseline-file",
            str(baseline_path),
            "--max-regression-percent",
            "15.0",  # 15% max regression
            "--enforce",
            "1",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    # Should fail due to regression exceeding threshold
    assert result.returncode == 1
    assert "regressed" in result.stdout.lower()


def test_perf_guardrail_script_json_output(tmp_path: Path) -> None:
    """Test JSON output format."""
    metrics_path = tmp_path / "metrics.json"
    metrics_path.write_text(
        json.dumps({"p50_ms": 220, "p95_ms": 360}),
        encoding="utf-8",
    )

    script = Path(__file__).resolve().parents[2] / "scripts" / "ci" / "check_perf_guardrails.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--metrics-file",
            str(metrics_path),
            "--output-format",
            "json",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0

    # Parse JSON output - the JSON is multi-line, find the start and end
    stdout = result.stdout.strip()
    json_start = stdout.find("{")
    json_end = stdout.rfind("}") + 1

    assert json_start >= 0, f"No JSON found in output: {stdout}"
    assert json_end > json_start, f"Incomplete JSON in output: {stdout}"

    json_str = stdout[json_start:json_end]
    output = json.loads(json_str)

    assert "passed" in output
    assert "violations" in output
    assert output["passed"] is False  # Has violations


def test_perf_guardrail_script_component_thresholds(tmp_path: Path) -> None:
    """Test component-specific threshold checking."""
    metrics_path = tmp_path / "metrics.json"
    metrics_path.write_text(
        json.dumps({
            "results": [
                {"name": "wake_detection", "p50_ms": 150, "p95_ms": 200},  # Exceeds 100ms target
                {"name": "command_parsing", "p50_ms": 5, "p95_ms": 8},
            ],
        }),
        encoding="utf-8",
    )

    script = Path(__file__).resolve().parents[2] / "scripts" / "ci" / "check_perf_guardrails.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--metrics-file",
            str(metrics_path),
            "--output-format",
            "text",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    # Should report component threshold violation
    assert "wake_detection" in result.stdout or "component" in result.stdout.lower()


def test_perf_guardrail_script_resource_budget_check(tmp_path: Path) -> None:
    """Test resource budget checking."""
    metrics_path = tmp_path / "metrics.json"
    metrics_path.write_text(
        json.dumps({
            "p50_ms": 50,  # Required for metrics extraction
            "p95_ms": 100,  # Required for metrics extraction
            "reports": [
                {
                    "name": "idle_state",
                    "avg_cpu_percent": 8.0,  # Exceeds 5% budget
                    "max_memory_mb": 200,
                },
            ],
        }),
        encoding="utf-8",
    )

    script = Path(__file__).resolve().parents[2] / "scripts" / "ci" / "check_perf_guardrails.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--metrics-file",
            str(metrics_path),
            "--output-format",
            "text",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    # Should report resource violation
    assert "idle" in result.stdout.lower() or "cpu" in result.stdout.lower() or "resource" in result.stdout.lower()


def test_perf_guardrail_script_missing_metrics_file(tmp_path: Path) -> None:
    """Test error handling for missing metrics file."""
    nonexistent = tmp_path / "nonexistent.json"

    script = Path(__file__).resolve().parents[2] / "scripts" / "ci" / "check_perf_guardrails.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--metrics-file",
            str(nonexistent),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "error" in result.stdout.lower() or "not found" in result.stdout.lower()


def test_perf_guardrail_script_invalid_metrics_format(tmp_path: Path) -> None:
    """Test error handling for invalid metrics format."""
    metrics_path = tmp_path / "metrics.json"
    metrics_path.write_text(
        json.dumps({"invalid_key": 123}),  # Missing p50_ms and p95_ms
        encoding="utf-8",
    )

    script = Path(__file__).resolve().parents[2] / "scripts" / "ci" / "check_perf_guardrails.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--metrics-file",
            str(metrics_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
