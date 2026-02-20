"""Validate CI matrix coverage against required OS/Python combinations.

This script parses the CI workflow YAML to extract matrix configuration and
validates that all required OS/Python combinations are present or have
documented waivers per requirements/testing-strategy.md section 1.

Required matrix:
- Ubuntu 22.04 + Python 3.11
- Ubuntu 22.04 + Python 3.12
- Ubuntu 24.04 + Python 3.11
- Ubuntu 24.04 + Python 3.12
- Windows 2022 (represents Windows 10/11) + Python 3.11
- Windows 2022 + Python 3.12

Exit codes:
- 0: All required combinations covered
- 1: Missing coverage (no waivers)
- 2: Missing coverage (with partial waivers)

Output JSON schema (stdout when --output-format=json):
{
    "status": "pass" | "fail",
    "required_combinations": [{os, python}],
    "actual_combinations": [{os, python, jobs: [str]}],
    "missing_combinations": [{os, python}],
    "waived_combinations": [{os, python, reason: str}],
    "jobs_analyzed": [str],
    "summary": {
        "total_required": int,
        "total_covered": int,
        "total_missing": int,
        "total_waived": int,
        "coverage_percent": float
    }
}
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Required combinations per testing-strategy.md section 1
REQUIRED_COMBINATIONS = [
    {"os": "ubuntu-22.04", "python": "3.11"},
    {"os": "ubuntu-22.04", "python": "3.12"},
    {"os": "ubuntu-24.04", "python": "3.11"},
    {"os": "ubuntu-24.04", "python": "3.12"},
    {"os": "windows-2022", "python": "3.11"},
    {"os": "windows-2022", "python": "3.12"},
]

# Documented waivers (if any) - maps combination key to reason
WAIVERS: dict[str, str] = {}


@dataclass
class MatrixCombination:
    """Represents an OS/Python combination."""
    os: str
    python: str
    jobs: list[str] = field(default_factory=list)

    @property
    def key(self) -> str:
        return f"{self.os}:{self.python}"


@dataclass
class CoverageResult:
    """Result of matrix coverage validation."""
    status: str
    required_combinations: list[dict[str, str]]
    actual_combinations: list[MatrixCombination]
    missing_combinations: list[dict[str, str]]
    waived_combinations: list[dict[str, str]]
    jobs_analyzed: list[str]

    @property
    def summary(self) -> dict[str, Any]:
        total_required = len(self.required_combinations)
        total_covered = total_required - len(self.missing_combinations)
        total_missing = len(self.missing_combinations)
        total_waived = len(self.waived_combinations)
        coverage_percent = (total_covered / total_required * 100) if total_required > 0 else 100.0

        return {
            "total_required": total_required,
            "total_covered": total_covered,
            "total_missing": total_missing,
            "total_waived": total_waived,
            "coverage_percent": round(coverage_percent, 1),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "required_combinations": self.required_combinations,
            "actual_combinations": [
                {"os": c.os, "python": c.python, "jobs": c.jobs}
                for c in self.actual_combinations
            ],
            "missing_combinations": self.missing_combinations,
            "waived_combinations": self.waived_combinations,
            "jobs_analyzed": self.jobs_analyzed,
            "summary": self.summary,
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workflow-file",
        type=Path,
        default=Path(".github/workflows/ci.yml"),
        help="Path to CI workflow YAML file (default: .github/workflows/ci.yml)",
    )
    parser.add_argument(
        "--waivers-file",
        type=Path,
        default=None,
        help="Optional JSON file with documented waivers",
    )
    parser.add_argument(
        "--output-format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail if any combination is missing (even with waivers)",
    )
    return parser.parse_args()


def load_waivers(waivers_file: Path | None) -> dict[str, str]:
    """Load waivers from JSON file if provided."""
    if not waivers_file or not waivers_file.exists():
        return {}

    try:
        data = json.loads(waivers_file.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return {}


def parse_yaml_matrix(yaml_content: str) -> dict[str, list[str]]:
    """Parse YAML content to extract matrix configuration.

    This is a simple parser that handles the common matrix patterns
    used in GitHub Actions workflows. It doesn't implement a full YAML
    parser but is sufficient for this use case.
    """
    matrices: dict[str, list[str]] = {}

    # Simple regex to find matrix.os and matrix.python-version inline lists
    # Handles formats like:
    #   os: [ubuntu-22.04, ubuntu-24.04, windows-2022]
    #   python-version: ["3.11", "3.12"]

    # Extract all os: [...] patterns
    os_pattern = re.compile(r"os:\s*\[([^\]]+)\]", re.MULTILINE)
    for match in os_pattern.finditer(yaml_content):
        os_values = [
            v.strip().strip('"').strip("'")
            for v in match.group(1).split(",")
            if v.strip()
        ]
        if "os" not in matrices:
            matrices["os"] = []
        for v in os_values:
            if v not in matrices["os"]:
                matrices["os"].append(v)

    # Extract all python-version: [...] patterns
    python_pattern = re.compile(r'python-version:\s*\[([^\]]+)\]', re.MULTILINE)
    for match in python_pattern.finditer(yaml_content):
        python_values = [
            v.strip().strip('"').strip("'")
            for v in match.group(1).split(",")
            if v.strip()
        ]
        if "python-version" not in matrices:
            matrices["python-version"] = []
        for v in python_values:
            if v not in matrices["python-version"]:
                matrices["python-version"].append(v)

    return matrices


def find_matrix_jobs(yaml_content: str) -> list[str]:
    """Find job names that use matrix strategy."""
    jobs = []

    # Find jobs that have matrix.os or matrix.python-version references
    # A job uses matrix if it has runs-on: ${{ matrix.os }} or similar
    lines = yaml_content.split("\n")

    current_job = None
    in_strategy = False
    has_matrix = False

    for i, line in enumerate(lines):
        # Check for job definition (2-space indent at start)
        job_match = re.match(r"^  ([a-z0-9_-]+):\s*$", line)
        if job_match:
            # If we were tracking a job with matrix, add it
            if current_job and has_matrix:
                if current_job not in jobs:
                    jobs.append(current_job)
            current_job = job_match.group(1)
            in_strategy = False
            has_matrix = False

        # Check for strategy block
        if current_job and re.match(r"^    strategy:", line):
            in_strategy = True

        # Check for matrix under strategy
        if in_strategy and re.match(r"^      matrix:", line):
            has_matrix = True

        # Reset strategy tracking when we hit a new section at same or lower indent
        if in_strategy and re.match(r"^    [a-z]+:", line) and not re.match(r"^    (strategy|fail-fast|matrix):", line):
            in_strategy = False

    # Don't forget the last job
    if current_job and has_matrix:
        if current_job not in jobs:
            jobs.append(current_job)

    return jobs


def extract_combinations_from_workflow(
    workflow_file: Path,
) -> tuple[list[MatrixCombination], list[str]]:
    """Extract all OS/Python combinations from a workflow file."""
    if not workflow_file.exists():
        return [], []

    yaml_content = workflow_file.read_text(encoding="utf-8")
    matrices = parse_yaml_matrix(yaml_content)
    jobs_with_matrix = find_matrix_jobs(yaml_content)

    os_list = matrices.get("os", [])
    python_list = matrices.get("python-version", [])

    combinations: list[MatrixCombination] = []

    for os_name in os_list:
        for python in python_list:
            combo = MatrixCombination(os=os_name, python=python, jobs=jobs_with_matrix)
            combinations.append(combo)

    return combinations, jobs_with_matrix


def validate_coverage(
    actual_combinations: list[MatrixCombination],
    waivers: dict[str, str],
    strict: bool = False,
) -> CoverageResult:
    """Validate that all required combinations are covered."""
    # Build set of actual combination keys
    actual_keys = {c.key: c for c in actual_combinations}

    # Check each required combination
    missing: list[dict[str, str]] = []
    waived: list[dict[str, str]] = []
    covered_actual: list[MatrixCombination] = []

    for req in REQUIRED_COMBINATIONS:
        key = f"{req['os']}:{req['python']}"

        if key in actual_keys:
            covered_actual.append(actual_keys[key])
        elif key in waivers:
            waived.append({**req, "reason": waivers[key]})
        else:
            missing.append(req)

    # Determine status
    if not missing and not waived:
        status = "pass"
    elif not missing and waived and not strict:
        status = "pass"  # All missing have waivers
    elif missing:
        status = "fail"
    else:
        status = "fail"  # Strict mode with waivers

    # Get unique job names
    jobs_analyzed = sorted(set(
        job for combo in covered_actual for job in combo.jobs
    ))

    return CoverageResult(
        status=status,
        required_combinations=REQUIRED_COMBINATIONS,
        actual_combinations=covered_actual,
        missing_combinations=missing,
        waived_combinations=waived,
        jobs_analyzed=jobs_analyzed,
    )


def format_text_report(result: CoverageResult) -> str:
    """Format coverage result as human-readable text."""
    lines = [
        "=" * 60,
        "CI Matrix Coverage Report",
        "=" * 60,
        "",
    ]

    # Summary
    summary = result.summary
    lines.append(f"Status: {result.status.upper()}")
    lines.append(f"Coverage: {summary['coverage_percent']}% ({summary['total_covered']}/{summary['total_required']})")
    lines.append(f"Jobs analyzed: {', '.join(result.jobs_analyzed) or 'none'}")
    lines.append("")

    # Required combinations
    lines.append("Required combinations:")
    for combo in result.required_combinations:
        key = f"{combo['os']}:{combo['python']}"
        covered = any(c.key == key for c in result.actual_combinations)
        waived = any(w["os"] == combo["os"] and w["python"] == combo["python"] for w in result.waived_combinations)
        missing = any(m["os"] == combo["os"] and m["python"] == combo["python"] for m in result.missing_combinations)

        if covered:
            status = "[COVERED]"
        elif waived:
            status = "[WAIVED]"
        elif missing:
            status = "[MISSING]"
        else:
            status = "[UNKNOWN]"

        lines.append(f"  {status} {combo['os']} + Python {combo['python']}")
    lines.append("")

    # Missing combinations
    if result.missing_combinations:
        lines.append("Missing combinations (no waivers):")
        for combo in result.missing_combinations:
            lines.append(f"  - {combo['os']} + Python {combo['python']}")
        lines.append("")

    # Waived combinations
    if result.waived_combinations:
        lines.append("Waived combinations:")
        for combo in result.waived_combinations:
            lines.append(f"  - {combo['os']} + Python {combo['python']}")
            lines.append(f"    Reason: {combo['reason']}")
        lines.append("")

    # Actual combinations found
    lines.append("Actual combinations in CI workflow:")
    for combo in result.actual_combinations:
        jobs_str = ", ".join(combo.jobs) if combo.jobs else "no jobs"
        lines.append(f"  - {combo.os} + Python {combo.python} (jobs: {jobs_str})")
    lines.append("")

    lines.append("=" * 60)
    return "\n".join(lines)


def main() -> int:
    args = parse_args()

    # Load waivers if provided
    waivers = load_waivers(args.waivers_file)

    # Extract combinations from workflow
    combinations, jobs = extract_combinations_from_workflow(args.workflow_file)

    # Validate coverage
    result = validate_coverage(combinations, waivers, strict=args.strict)

    # Output result
    if args.output_format == "json":
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_text_report(result))

    # Return appropriate exit code
    if result.status == "pass":
        return 0
    elif result.waived_combinations and not args.strict:
        return 2  # Missing but waived
    else:
        return 1  # Missing coverage


if __name__ == "__main__":
    raise SystemExit(main())
