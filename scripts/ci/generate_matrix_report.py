"""Generate a markdown report of CI matrix coverage.

This script creates a human-readable markdown report showing:
- All OS/Python combinations tested in CI
- Coverage status for each required combination
- Any documented waivers

The report is suitable for documentation or CI artifacts.

Usage:
    python scripts/ci/generate_matrix_report.py > matrix-coverage-report.md
    python scripts/ci/generate_matrix_report.py --output-file docs/matrix-coverage.md
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


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
        "--output-file",
        type=Path,
        default=None,
        help="Output file path for markdown report (default: stdout)",
    )
    parser.add_argument(
        "--title",
        default="CI Matrix Coverage Report",
        help="Title for the report",
    )
    return parser.parse_args()


def get_coverage_data(workflow_file: Path, waivers_file: Path | None) -> dict[str, Any]:
    """Run the coverage checker and get JSON output."""
    cmd = [
        sys.executable,
        str(Path(__file__).parent / "check_matrix_coverage.py"),
        "--workflow-file", str(workflow_file),
        "--output-format", "json",
    ]

    if waivers_file:
        cmd.extend(["--waivers-file", str(waivers_file)])

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode not in (0, 1, 2) or not result.stdout.strip():
        # Return empty data on error
        return {
            "status": "error",
            "required_combinations": [],
            "actual_combinations": [],
            "missing_combinations": [],
            "waived_combinations": [],
            "jobs_analyzed": [],
            "summary": {
                "total_required": 0,
                "total_covered": 0,
                "total_missing": 0,
                "total_waived": 0,
                "coverage_percent": 0.0,
            },
        }

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {
            "status": "error",
            "required_combinations": [],
            "actual_combinations": [],
            "missing_combinations": [],
            "waived_combinations": [],
            "jobs_analyzed": [],
            "summary": {},
        }


def format_markdown_report(data: dict[str, Any], title: str) -> str:
    """Format coverage data as markdown report."""
    lines = [
        f"# {title}",
        "",
        f"> Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
    ]

    # Summary section
    summary = data.get("summary", {})
    status = data.get("status", "unknown")
    status_emoji = {"pass": "✅", "fail": "❌", "error": "⚠️"}.get(status, "❓")

    lines.extend([
        "## Summary",
        "",
        f"- **Status**: {status_emoji} {status.upper()}",
        f"- **Coverage**: {summary.get('coverage_percent', 0)}%",
        f"- **Required combinations**: {summary.get('total_required', 0)}",
        f"- **Covered**: {summary.get('total_covered', 0)}",
        f"- **Missing**: {summary.get('total_missing', 0)}",
        f"- **Waived**: {summary.get('total_waived', 0)}",
        "",
    ])

    # Jobs analyzed
    jobs = data.get("jobs_analyzed", [])
    if jobs:
        lines.extend([
            "## Jobs Analyzed",
            "",
            "The following CI jobs use matrix strategy:",
            "",
        ])
        for job in jobs:
            lines.append(f"- `{job}`")
        lines.append("")

    # Required combinations table
    lines.extend([
        "## Required Matrix",
        "",
        "Per `requirements/testing-strategy.md` section 1, the following combinations are required:",
        "",
        "| OS | Python | Status |",
        "|----|--------|--------|",
    ])

    required = data.get("required_combinations", [])
    actual = data.get("actual_combinations", [])
    missing = data.get("missing_combinations", [])
    waived = data.get("waived_combinations", [])

    # Build lookup sets
    covered_keys = {f"{c['os']}:{c['python']}" for c in actual}
    missing_keys = {f"{c['os']}:{c['python']}" for c in missing}
    waived_lookup = {f"{c['os']}:{c['python']}": c for c in waived}

    for combo in required:
        key = f"{combo['os']}:{combo['python']}"
        if key in covered_keys:
            status_str = "✅ COVERED"
        elif key in waived_lookup:
            reason = waived_lookup[key].get("reason", "No reason provided")
            status_str = f"⚠️ WAIVED ({reason})"
        elif key in missing_keys:
            status_str = "❌ MISSING"
        else:
            status_str = "❓ UNKNOWN"

        lines.append(f"| {combo['os']} | {combo['python']} | {status_str} |")

    lines.append("")

    # Actual combinations
    if actual:
        lines.extend([
            "## Actual Combinations",
            "",
            "The following combinations are defined in the CI workflow:",
            "",
            "| OS | Python | Jobs |",
            "|----|--------|------|",
        ])

        for combo in actual:
            jobs_str = ", ".join(combo.get("jobs", [])) or "-"
            lines.append(f"| {combo['os']} | {combo['python']} | {jobs_str} |")

        lines.append("")

    # Missing combinations
    if missing:
        lines.extend([
            "## Missing Combinations",
            "",
            "The following required combinations are not covered and have no waivers:",
            "",
        ])
        for combo in missing:
            lines.append(f"- {combo['os']} + Python {combo['python']}")
        lines.append("")

    # Waivers
    if waived:
        lines.extend([
            "## Documented Waivers",
            "",
            "The following combinations are waived with documented reasons:",
            "",
            "| OS | Python | Reason |",
            "|----|--------|--------|",
        ])
        for combo in waived:
            lines.append(f"| {combo['os']} | {combo['python']} | {combo.get('reason', 'N/A')} |")
        lines.append("")

    # Platform notes
    lines.extend([
        "## Platform Notes",
        "",
        "- **Ubuntu 22.04/24.04**: Represents Linux LTS releases",
        "- **Windows 2022**: CI runner representing Windows 10/11 support targets",
        "- **Python 3.11/3.12**: Supported Python versions per project requirements",
        "",
    ])

    # Footer
    lines.extend([
        "---",
        "",
        "*This report was generated by `scripts/ci/generate_matrix_report.py`*",
        "",
    ])

    return "\n".join(lines)


def main() -> int:
    args = parse_args()

    # Get coverage data from checker script
    data = get_coverage_data(args.workflow_file, args.waivers_file)

    # Format as markdown
    report = format_markdown_report(data, args.title)

    # Output
    if args.output_file:
        args.output_file.parent.mkdir(parents=True, exist_ok=True)
        args.output_file.write_text(report, encoding="utf-8")
        print(f"matrix_report_generated={args.output_file}")
    else:
        print(report)

    return 0 if data.get("status") == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
