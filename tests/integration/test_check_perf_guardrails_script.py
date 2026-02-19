"""Integration tests for CI performance guardrail script (E08-S01)."""

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
    assert "perf_guardrail_violation=" in result.stdout
