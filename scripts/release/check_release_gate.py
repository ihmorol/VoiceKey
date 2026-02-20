"""Check release gate conditions for release readiness.

This script validates that all P0 stories are complete and the traceability
matrix is complete before allowing a release.

Exit codes:
- 0: Release is ready (all gates pass)
- 1: Release is blocked (one or more gates fail)

Requirements: E11-S03 - Traceability maintenance and release blocking enforcement
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class StoryStatus:
    """Status of a single backlog story."""
    story_id: str
    status: str  # "complete", "pending", "unknown"
    epic: str
    priority: str  # "P0", "P1", "P2"


@dataclass
class GateResult:
    """Result of a single gate check."""
    name: str
    passed: bool
    message: str
    details: list[str] = field(default_factory=list)


@dataclass
class ReleaseGateResult:
    """Result of all release gate checks."""
    passed: bool
    gates: list[GateResult]
    blocking_issues: list[str]
    summary: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "summary": self.summary,
            "blocking_issues": self.blocking_issues,
            "gates": [
                {
                    "name": g.name,
                    "passed": g.passed,
                    "message": g.message,
                    "details": g.details,
                }
                for g in self.gates
            ],
        }


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check release gates
  python check_release_gate.py

  # Output in JSON format
  python check_release_gate.py --output-format json

  # Check specific gates only
  python check_release_gate.py --gates p0_stories,traceability
""",
    )
    parser.add_argument(
        "--backlog-file",
        type=Path,
        default=Path("backlog/BACKLOG_MASTER.md"),
        help="Path to backlog master file (default: backlog/BACKLOG_MASTER.md)",
    )
    parser.add_argument(
        "--traceability-file",
        type=Path,
        default=Path("backlog/TRACEABILITY_MATRIX.md"),
        help="Path to traceability matrix file (default: backlog/TRACEABILITY_MATRIX.md)",
    )
    parser.add_argument(
        "--output-format",
        choices=["text", "json", "github"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--gates",
        type=str,
        default="",
        help="Comma-separated gates to check (default: all)",
    )
    return parser.parse_args()


def parse_execution_status(content: str) -> dict[str, str]:
    """Parse execution status section from BACKLOG_MASTER.md.

    Returns dict mapping story_id -> status.
    """
    statuses: dict[str, str] = {}

    # Find execution status section
    lines = content.split("\n")
    in_execution_status = False

    for line in lines:
        if "## Execution Status" in line or "### Execution Status" in line:
            in_execution_status = True
            continue

        if in_execution_status:
            # End at next section
            if line.startswith("## ") and "Execution Status" not in line:
                break

            # Parse status lines like "- E00-S01: complete (details)"
            match = re.match(r"-\s+(E\d+-S\d+):\s+(complete|pending|in_progress|blocked)", line, re.IGNORECASE)
            if match:
                story_id = match.group(1)
                status = match.group(2).lower()
                statuses[story_id] = status

    return statuses


def parse_story_priorities(content: str) -> dict[str, tuple[str, str]]:
    """Parse story priorities from backlog.

    Returns dict mapping story_id -> (epic_id, priority).
    """
    priorities: dict[str, tuple[str, str]] = {}

    # Find epic sections and their priorities
    lines = content.split("\n")
    current_epic = ""
    current_priority = ""

    for line in lines:
        # Epic header like "## Epic E00 - Name (P0)"
        epic_match = re.match(r"##\s+Epic\s+(E\d+).*?\((P\d+)\)", line)
        if epic_match:
            current_epic = epic_match.group(1)
            current_priority = epic_match.group(2)
            continue

        # Story header like "### Story E00-S01 - Name"
        story_match = re.match(r"###\s+Story\s+(E\d+-S\d+)", line)
        if story_match and current_epic:
            story_id = story_match.group(1)
            priorities[story_id] = (current_epic, current_priority)

    return priorities


def check_p0_stories_complete(backlog_file: Path) -> GateResult:
    """Check that all P0 stories are marked as complete.

    Returns GateResult with pass/fail status.
    """
    if not backlog_file.exists():
        return GateResult(
            name="P0 Stories Complete",
            passed=False,
            message=f"Backlog file not found: {backlog_file}",
            details=[],
        )

    content = backlog_file.read_text(encoding="utf-8")

    # Parse execution status
    statuses = parse_execution_status(content)
    priorities = parse_story_priorities(content)

    # Find all P0 stories
    p0_stories = {
        story_id: (epic, priority)
        for story_id, (epic, priority) in priorities.items()
        if priority == "P0"
    }

    # Check which are complete
    incomplete: list[str] = []
    complete: list[str] = []

    for story_id in sorted(p0_stories.keys()):
        status = statuses.get(story_id, "unknown")
        if status == "complete":
            complete.append(story_id)
        else:
            incomplete.append(f"{story_id} ({status})")

    total = len(p0_stories)
    completed = len(complete)

    if not p0_stories:
        return GateResult(
            name="P0 Stories Complete",
            passed=False,
            message="No P0 stories found in backlog",
            details=["Check backlog format - expected P0 stories"],
        )

    if incomplete:
        return GateResult(
            name="P0 Stories Complete",
            passed=False,
            message=f"{len(incomplete)} P0 stories incomplete ({completed}/{total} complete)",
            details=incomplete,
        )

    return GateResult(
        name="P0 Stories Complete",
        passed=True,
        message=f"All {total} P0 stories complete",
        details=complete,
    )


def check_traceability_complete(traceability_file: Path) -> GateResult:
    """Check that traceability matrix is complete.

    Returns GateResult with pass/fail status.
    """
    if not traceability_file.exists():
        return GateResult(
            name="Traceability Complete",
            passed=False,
            message=f"Traceability matrix not found: {traceability_file}",
            details=[],
        )

    content = traceability_file.read_text(encoding="utf-8")

    # Check for required sections
    required_sections = [
        "Canonical FR Coverage",
        "Non-ID Requirement Coverage",
        "Coverage Gate Rule",
    ]

    missing_sections = []
    for section in required_sections:
        if section.lower() not in content.lower():
            missing_sections.append(section)

    if missing_sections:
        return GateResult(
            name="Traceability Complete",
            passed=False,
            message=f"Missing required sections: {', '.join(missing_sections)}",
            details=missing_sections,
        )

    # Count FR requirements with backlog mapping
    # Parse table rows looking for FR-* patterns
    fr_pattern = re.compile(r"\|\s*(FR-[A-Z]+\d+)\s*\|([^|]+)\|([^|]+)\|")
    matches = fr_pattern.findall(content)

    total_fr = len(matches)
    with_backlog = 0
    with_verification = 0
    partial_coverage = []

    for req_id, backlog_col, verification_col in matches:
        backlog_stories = re.findall(r"E\d+-S\d+", backlog_col)
        if backlog_stories:
            with_backlog += 1
        else:
            partial_coverage.append(f"{req_id}: no backlog mapping")

        # Check for meaningful verification
        verification_lower = verification_col.lower().strip()
        if verification_lower and verification_lower not in ["pending", "tbd", "-", "n/a"]:
            if "partial" not in verification_lower:
                with_verification += 1
            else:
                partial_coverage.append(f"{req_id}: partial verification")

    if total_fr == 0:
        return GateResult(
            name="Traceability Complete",
            passed=False,
            message="No FR requirements found in traceability matrix",
            details=["Check traceability matrix format"],
        )

    coverage_percent = (with_backlog / total_fr * 100) if total_fr > 0 else 0

    if partial_coverage:
        return GateResult(
            name="Traceability Complete",
            passed=False,
            message=f"Traceability incomplete: {len(partial_coverage)} requirements need attention",
            details=partial_coverage,
        )

    return GateResult(
        name="Traceability Complete",
        passed=True,
        message=f"Traceability complete: {total_fr} FR requirements covered ({coverage_percent:.0f}%)",
        details=[f"{with_backlog} with backlog mapping", f"{with_verification} with verification"],
    )


def check_no_critical_defects(backlog_file: Path) -> GateResult:
    """Check for blocking notes in execution status.

    This is a placeholder check - in a real system this would integrate
    with issue tracking.

    Returns GateResult with pass/fail status.
    """
    if not backlog_file.exists():
        return GateResult(
            name="No Critical Defects",
            passed=False,
            message="Cannot check for defects - backlog file not found",
            details=[],
        )

    content = backlog_file.read_text(encoding="utf-8")

    # Look for blocking keywords in execution status
    blocking_keywords = ["blocked", "critical failure", "release blocker"]
    status_section = ""

    lines = content.split("\n")
    in_status = False
    for line in lines:
        if "Execution Status" in line:
            in_status = True
        elif in_status and line.startswith("## "):
            break
        elif in_status:
            status_section += line + "\n"

    found_blockers = []
    for keyword in blocking_keywords:
        if keyword.lower() in status_section.lower():
            # Find the line with the keyword
            for line in status_section.split("\n"):
                if keyword.lower() in line.lower():
                    found_blockers.append(line.strip())

    if found_blockers:
        return GateResult(
            name="No Critical Defects",
            passed=False,
            message=f"Found {len(found_blockers)} blocking issues",
            details=found_blockers,
        )

    return GateResult(
        name="No Critical Defects",
        passed=True,
        message="No critical defects or blockers found",
        details=[],
    )


def run_all_gates(
    backlog_file: Path,
    traceability_file: Path,
    gates_to_run: list[str] | None = None,
) -> ReleaseGateResult:
    """Run all release gate checks.

    Args:
        backlog_file: Path to BACKLOG_MASTER.md
        traceability_file: Path to TRACEABILITY_MATRIX.md
        gates_to_run: Optional list of specific gates to run

    Returns:
        ReleaseGateResult with all findings
    """
    all_gates = {
        "p0_stories": lambda: check_p0_stories_complete(backlog_file),
        "traceability": lambda: check_traceability_complete(traceability_file),
        "defects": lambda: check_no_critical_defects(backlog_file),
    }

    gates: list[GateResult] = []
    blocking_issues: list[str] = []

    gates_to_execute = gates_to_run if gates_to_run else list(all_gates.keys())

    for gate_name in gates_to_execute:
        if gate_name in all_gates:
            result = all_gates[gate_name]()
            gates.append(result)

            if not result.passed:
                blocking_issues.append(f"{gate_name}: {result.message}")

    # Summary
    total_gates = len(gates)
    passed_gates = sum(1 for g in gates if g.passed)

    return ReleaseGateResult(
        passed=len(blocking_issues) == 0,
        gates=gates,
        blocking_issues=blocking_issues,
        summary={
            "total_gates": total_gates,
            "passed_gates": passed_gates,
            "failed_gates": total_gates - passed_gates,
            "release_ready": len(blocking_issues) == 0,
        },
    )


def format_text_report(result: ReleaseGateResult) -> str:
    """Format release gate result as human-readable text."""
    lines = [
        "=" * 70,
        "Release Gate Check Report",
        "=" * 70,
        "",
    ]

    # Overall status
    status = "READY" if result.passed else "BLOCKED"
    lines.append(f"Release Status: {status}")
    lines.append("")

    # Summary
    summary = result.summary
    lines.append(f"Gates Passed: {summary['passed_gates']}/{summary['total_gates']}")
    lines.append("")

    # Individual gates
    lines.append("Gate Results:")
    for gate in result.gates:
        mark = "[PASS]" if gate.passed else "[FAIL]"
        lines.append(f"  {mark} {gate.name}: {gate.message}")
        for detail in gate.details[:5]:  # Limit details
            lines.append(f"       - {detail}")
        if len(gate.details) > 5:
            lines.append(f"       ... and {len(gate.details) - 5} more")
    lines.append("")

    # Blocking issues
    if result.blocking_issues:
        lines.append("Blocking Issues:")
        for issue in result.blocking_issues:
            lines.append(f"  - {issue}")
        lines.append("")

    lines.append("=" * 70)

    if result.passed:
        lines.append("Release is READY - all gates passed")
    else:
        lines.append("Release is BLOCKED - fix blocking issues before release")

    lines.append("=" * 70)

    return "\n".join(lines)


def format_github_report(result: ReleaseGateResult) -> str:
    """Format release gate result for GitHub Actions."""
    lines = []

    if result.passed:
        lines.append("::notice::Release gate check passed - release is ready")
        for gate in result.gates:
            lines.append(f"::notice::{gate.name}: {gate.message}")
    else:
        lines.append("::error::Release gate check failed - release is blocked")
        for issue in result.blocking_issues:
            lines.append(f"::error::{issue}")

    return "\n".join(lines)


def main() -> int:
    """Main entry point."""
    args = parse_args()

    # Determine which gates to run
    gates_to_run = None
    if args.gates:
        gates_to_run = [g.strip() for g in args.gates.split(",")]

    # Run all gates
    result = run_all_gates(args.backlog_file, args.traceability_file, gates_to_run)

    # Output result
    if args.output_format == "json":
        print(json.dumps(result.to_dict(), indent=2))
    elif args.output_format == "github":
        print(format_github_report(result))
    else:
        print(format_text_report(result))

    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
