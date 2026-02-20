"""Export CI observability metrics from GitHub Actions context.

This script collects CI metrics including duration, job results, and matrix
summary for observability tracking per requirements/devops-cicd.md section 6.

Output JSON schema:
{
    "workflow_name": str,
    "run_id": str,
    "run_number": str,
    "event": str,
    "branch": str,
    "commit_sha": str,
    "timestamp_utc": str,
    "duration_seconds": float,
    "job_results": {job_name: {"result": str, "duration_seconds": float}},
    "matrix_summary": {
        "os_list": [str],
        "python_versions": [str],
        "total_jobs": int,
        "passed_jobs": int,
        "failed_jobs": int,
        "skipped_jobs": int
    },
    "summary": {
        "overall_result": str,
        "smoke_pass_rate": float
    }
}
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-file",
        type=Path,
        default=None,
        help="Output file path for metrics JSON (default: stdout)",
    )
    parser.add_argument(
        "--workflow-name",
        default=os.environ.get("GITHUB_WORKFLOW", "unknown"),
        help="Workflow name from GITHUB_WORKFLOW env",
    )
    parser.add_argument(
        "--run-id",
        default=os.environ.get("GITHUB_RUN_ID", "unknown"),
        help="Run ID from GITHUB_RUN_ID env",
    )
    parser.add_argument(
        "--run-number",
        default=os.environ.get("GITHUB_RUN_NUMBER", "unknown"),
        help="Run number from GITHUB_RUN_NUMBER env",
    )
    parser.add_argument(
        "--event",
        default=os.environ.get("GITHUB_EVENT_NAME", "unknown"),
        help="Event name from GITHUB_EVENT_NAME env",
    )
    parser.add_argument(
        "--branch",
        default=os.environ.get("GITHUB_REF_NAME", "unknown"),
        help="Branch name from GITHUB_REF_NAME env",
    )
    parser.add_argument(
        "--commit-sha",
        default=os.environ.get("GITHUB_SHA", "unknown"),
        help="Commit SHA from GITHUB_SHA env",
    )
    parser.add_argument(
        "--job-results",
        default=os.environ.get("CI_JOB_RESULTS", ""),
        help="JSON-encoded job results from CI context",
    )
    parser.add_argument(
        "--duration-seconds",
        type=float,
        default=0.0,
        help="Total workflow duration in seconds",
    )
    parser.add_argument(
        "--matrix-os",
        default=os.environ.get("CI_MATRIX_OS", ""),
        help="Comma-separated OS list",
    )
    parser.add_argument(
        "--matrix-python",
        default=os.environ.get("CI_MATRIX_PYTHON", ""),
        help="Comma-separated Python version list",
    )
    return parser.parse_args()


def _parse_job_results(job_results_json: str) -> dict[str, dict[str, Any]]:
    """Parse job results from JSON string."""
    if not job_results_json:
        return {}
    try:
        results = json.loads(job_results_json)
        if isinstance(results, dict):
            return results
    except json.JSONDecodeError:
        pass
    return {}


def _parse_csv_list(value: str) -> list[str]:
    """Parse comma-separated values into list."""
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]


def _calculate_summary(job_results: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Calculate summary statistics from job results."""
    total = len(job_results)
    passed = sum(1 for j in job_results.values() if j.get("result") == "success")
    failed = sum(1 for j in job_results.values() if j.get("result") == "failure")
    skipped = sum(1 for j in job_results.values() if j.get("result") == "skipped")

    overall = "success" if failed == 0 and passed > 0 else "failure" if failed > 0 else "unknown"
    
    # Calculate smoke pass rate (jobs containing 'smoke' in name)
    smoke_jobs = {k: v for k, v in job_results.items() if "smoke" in k.lower()}
    smoke_total = len(smoke_jobs)
    smoke_passed = sum(1 for j in smoke_jobs.values() if j.get("result") == "success")
    smoke_pass_rate = smoke_passed / smoke_total if smoke_total > 0 else 1.0

    return {
        "overall_result": overall,
        "smoke_pass_rate": round(smoke_pass_rate, 3),
        "total_jobs": total,
        "passed_jobs": passed,
        "failed_jobs": failed,
        "skipped_jobs": skipped,
    }


def main() -> int:
    args = parse_args()
    
    job_results = _parse_job_results(args.job_results)
    summary = _calculate_summary(job_results)
    
    metrics: dict[str, Any] = {
        "workflow_name": args.workflow_name,
        "run_id": args.run_id,
        "run_number": args.run_number,
        "event": args.event,
        "branch": args.branch,
        "commit_sha": args.commit_sha,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": args.duration_seconds,
        "job_results": job_results,
        "matrix_summary": {
            "os_list": _parse_csv_list(args.matrix_os),
            "python_versions": _parse_csv_list(args.matrix_python),
            **summary,
        },
        "summary": {
            "overall_result": summary["overall_result"],
            "smoke_pass_rate": summary["smoke_pass_rate"],
        },
    }
    
    output_json = json.dumps(metrics, indent=2, sort_keys=True)
    
    if args.output_file:
        args.output_file.parent.mkdir(parents=True, exist_ok=True)
        args.output_file.write_text(output_json, encoding="utf-8")
        print(f"ci_metrics_exported={args.output_file}")
    else:
        print(output_json)
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
