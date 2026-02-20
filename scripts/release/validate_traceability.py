"""Validate traceability matrix completeness for release readiness.

This script parses the TRACEABILITY_MATRIX.md file and validates that:
1. Every FR requirement has backlog story mapping
2. Every FR requirement has verification method documented
3. Non-ID requirements are also covered

Exit codes:
- 0: Complete coverage
- 1: Missing coverage (release blocked)

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
class RequirementCoverage:
    """Represents coverage status for a single requirement."""
    requirement_id: str
    backlog_stories: list[str] = field(default_factory=list)
    verification_method: str = ""
    is_covered: bool = False
    issues: list[str] = field(default_factory=list)


@dataclass
class ValidationResult:
    """Result of traceability validation."""
    passed: bool
    fr_requirements: list[RequirementCoverage]
    non_id_requirements: list[RequirementCoverage]
    missing_backlog: list[str]
    missing_verification: list[str]
    summary: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "summary": self.summary,
            "missing_backlog": self.missing_backlog,
            "missing_verification": self.missing_verification,
            "fr_requirements": [
                {
                    "id": r.requirement_id,
                    "backlog_stories": r.backlog_stories,
                    "verification": r.verification_method,
                    "covered": r.is_covered,
                    "issues": r.issues,
                }
                for r in self.fr_requirements
            ],
            "non_id_requirements": [
                {
                    "id": r.requirement_id,
                    "backlog_stories": r.backlog_stories,
                    "verification": r.verification_method,
                    "covered": r.is_covered,
                    "issues": r.issues,
                }
                for r in self.non_id_requirements
            ],
        }


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate traceability matrix
  python validate_traceability.py

  # Output in JSON format
  python validate_traceability.py --output-format json

  # Custom path to traceability matrix
  python validate_traceability.py --traceability-file custom/path/TRACEABILITY_MATRIX.md
""",
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
        "--strict",
        action="store_true",
        help="Fail on partial coverage (e.g., 'partial' status)",
    )
    return parser.parse_args()


def parse_markdown_table(content: str, section_header: str) -> list[dict[str, str]]:
    """Parse a markdown table from a specific section.

    Returns list of dicts with column headers as keys.
    """
    lines = content.split("\n")
    in_section = False
    in_table = False
    headers: list[str] = []
    rows: list[dict[str, str]] = []

    for i, line in enumerate(lines):
        # Check for section header
        if line.strip().startswith("## ") and section_header.lower() in line.lower():
            in_section = True
            continue

        # Check for next section (end of current section)
        if in_section and line.strip().startswith("## "):
            in_section = False
            in_table = False
            continue

        if not in_section:
            continue

        # Check for table row
        if "|" in line:
            cells = [c.strip() for c in line.split("|")]
            # Remove empty first/last cells from pipe parsing
            cells = [c for c in cells if c or cells.index(c) not in [0, len(cells) - 1]]

            # Skip separator row (contains only dashes)
            if all(set(c.replace(":", "").replace("-", "")) == set() or c == "" for c in cells):
                in_table = True
                continue

            # First table row with content is header
            if not headers:
                headers = [c.strip() for c in line.split("|") if c.strip()]
                in_table = True
                continue

            # Skip separator row (contains dashes)
            if "---" in line or all(c.replace("-", "").replace(":", "") == "" for c in cells):
                continue

            # Data row
            if headers and in_table:
                # Parse cells more carefully
                raw_cells = line.split("|")
                # Get rid of leading/trailing empty strings
                while raw_cells and raw_cells[0].strip() == "":
                    raw_cells.pop(0)
                while raw_cells and raw_cells[-1].strip() == "":
                    raw_cells.pop()

                if len(raw_cells) >= len(headers):
                    row = {}
                    for j, header in enumerate(headers):
                        row[header] = raw_cells[j].strip() if j < len(raw_cells) else ""
                    rows.append(row)

    return rows


def extract_requirement_id(text: str) -> str:
    """Extract requirement ID from text (e.g., FR-A01 from | FR-A01 | ...)."""
    # Match patterns like FR-A01, FR-W01, FR-CI01, etc.
    match = re.search(r"\b(FR-[A-Z]+\d+)\b", text)
    if match:
        return match.group(1)
    return text.strip()


def extract_backlog_stories(text: str) -> list[str]:
    """Extract backlog story IDs from text (e.g., E01-S01)."""
    # Match patterns like E01-S01, E12-S03, etc.
    matches = re.findall(r"\bE\d+-S\d+\b", text)
    return list(set(matches))


def check_backlog_coverage(stories: list[str]) -> tuple[bool, list[str]]:
    """Check if backlog stories are documented.

    Returns (is_covered, issues).
    """
    issues = []

    if not stories:
        return False, ["No backlog story mapping"]

    # Check for pending/unknown status
    return True, []


def check_verification_coverage(verification_text: str) -> tuple[bool, list[str]]:
    """Check if verification method is documented.

    Returns (is_covered, issues).
    """
    issues = []

    if not verification_text or verification_text.lower() in ["pending", "tbd", "n/a", "-"]:
        return False, ["No verification method documented"]

    # Check for partial coverage indicator
    if "partial" in verification_text.lower():
        return False, ["Partial coverage - verification incomplete"]

    # Check for meaningful verification content
    test_indicators = [
        "test", "tests", "verified", "validation", "audit", "check",
        "integration", "unit", "e2e", "smoke", "coverage", "passing",
    ]

    has_verification = any(ind in verification_text.lower() for ind in test_indicators)

    if not has_verification and len(verification_text.strip()) < 10:
        return False, ["Verification method unclear or too brief"]

    return True, []


def validate_requirement_row(row: dict[str, str], is_fr: bool = True) -> RequirementCoverage:
    """Validate a single requirement row.

    Args:
        row: Parsed table row with column headers as keys
        is_fr: Whether this is an FR-* requirement (vs non-ID)

    Returns:
        RequirementCoverage with validation status
    """
    # Determine column names (handle variations)
    req_col = None
    backlog_col = None
    verification_col = None

    for key in row.keys():
        key_lower = key.lower()
        if "requirement" in key_lower or "source" in key_lower:
            req_col = key
        elif "backlog" in key_lower or "story" in key_lower or "coverage" in key_lower:
            backlog_col = key
        elif "verif" in key_lower or "method" in key_lower:
            verification_col = key

    if not req_col or not backlog_col:
        # Return empty coverage for malformed rows
        return RequirementCoverage(
            requirement_id="UNKNOWN",
            is_covered=False,
            issues=["Malformed table row - missing columns"],
        )

    req_id = extract_requirement_id(row.get(req_col, ""))
    backlog_text = row.get(backlog_col, "")
    verification_text = row.get(verification_col, "") if verification_col else ""

    backlog_stories = extract_backlog_stories(backlog_text)

    # Check coverage
    backlog_covered, backlog_issues = check_backlog_coverage(backlog_stories)
    verification_covered, verification_issues = check_verification_coverage(verification_text)

    all_issues = backlog_issues + verification_issues
    is_covered = backlog_covered and verification_covered

    return RequirementCoverage(
        requirement_id=req_id,
        backlog_stories=backlog_stories,
        verification_method=verification_text,
        is_covered=is_covered,
        issues=all_issues,
    )


def validate_traceability_matrix(traceability_file: Path, strict: bool = False) -> ValidationResult:
    """Validate the traceability matrix file.

    Args:
        traceability_file: Path to TRACEABILITY_MATRIX.md
        strict: Whether to fail on partial coverage

    Returns:
        ValidationResult with all findings
    """
    if not traceability_file.exists():
        return ValidationResult(
            passed=False,
            fr_requirements=[],
            non_id_requirements=[],
            missing_backlog=[],
            missing_verification=[],
            summary={
                "error": f"Traceability matrix file not found: {traceability_file}",
                "total_fr_requirements": 0,
                "total_non_id_requirements": 0,
                "total_covered": 0,
                "total_missing_backlog": 0,
                "total_missing_verification": 0,
                "coverage_percent": 0.0,
            },
        )

    content = traceability_file.read_text(encoding="utf-8")

    # Parse FR requirements table (Section A)
    fr_rows = parse_markdown_table(content, "Canonical FR Coverage")
    fr_requirements = [validate_requirement_row(row, is_fr=True) for row in fr_rows]

    # Parse non-ID requirements table (Section B)
    non_id_rows = parse_markdown_table(content, "Non-ID Requirement Coverage")
    non_id_requirements = [validate_requirement_row(row, is_fr=False) for row in non_id_rows]

    # Collect missing items
    missing_backlog: list[str] = []
    missing_verification: list[str] = []

    for req in fr_requirements:
        if not req.backlog_stories:
            missing_backlog.append(req.requirement_id)
        if not req.is_covered:
            for issue in req.issues:
                if "verification" in issue.lower() or "partial" in issue.lower():
                    if req.requirement_id not in missing_verification:
                        missing_verification.append(req.requirement_id)

    for req in non_id_requirements:
        if not req.backlog_stories:
            # Use truncated description as ID for non-ID requirements
            missing_backlog.append(req.requirement_id[:50] + "..." if len(req.requirement_id) > 50 else req.requirement_id)

    # Calculate summary
    total_fr = len(fr_requirements)
    total_non_id = len(non_id_requirements)
    total_requirements = total_fr + total_non_id
    total_covered = sum(1 for r in fr_requirements if r.is_covered) + sum(1 for r in non_id_requirements if r.is_covered)

    coverage_percent = (total_covered / total_requirements * 100) if total_requirements > 0 else 0.0

    # Determine pass/fail
    # In strict mode, fail if any coverage is missing
    # In non-strict mode, only fail if critical coverage (backlog mapping) is missing
    passed = len(missing_backlog) == 0 and len(missing_verification) == 0

    if strict:
        passed = coverage_percent == 100.0

    return ValidationResult(
        passed=passed,
        fr_requirements=fr_requirements,
        non_id_requirements=non_id_requirements,
        missing_backlog=missing_backlog,
        missing_verification=missing_verification,
        summary={
            "total_fr_requirements": total_fr,
            "total_non_id_requirements": total_non_id,
            "total_requirements": total_requirements,
            "total_covered": total_covered,
            "total_missing_backlog": len(missing_backlog),
            "total_missing_verification": len(missing_verification),
            "coverage_percent": round(coverage_percent, 1),
        },
    )


def format_text_report(result: ValidationResult) -> str:
    """Format validation result as human-readable text."""
    lines = [
        "=" * 70,
        "Traceability Matrix Validation Report",
        "=" * 70,
        "",
    ]

    # Summary
    status = "PASS" if result.passed else "FAIL"
    lines.append(f"Status: {status}")
    summary = result.summary
    lines.append(f"Coverage: {summary['coverage_percent']}% ({summary['total_covered']}/{summary['total_requirements']})")
    lines.append(f"FR Requirements: {summary['total_fr_requirements']}")
    lines.append(f"Non-ID Requirements: {summary['total_non_id_requirements']}")
    lines.append("")

    # Missing backlog mappings
    if result.missing_backlog:
        lines.append("Requirements Missing Backlog Mapping:")
        for req_id in result.missing_backlog:
            lines.append(f"  - {req_id}")
        lines.append("")

    # Missing verification
    if result.missing_verification:
        lines.append("Requirements Missing/Incomplete Verification:")
        for req_id in result.missing_verification:
            lines.append(f"  - {req_id}")
        lines.append("")

    # Detailed FR requirements
    lines.append("FR Requirements Coverage:")
    for req in result.fr_requirements:
        mark = "[OK]" if req.is_covered else "[MISSING]"
        stories = ", ".join(req.backlog_stories) if req.backlog_stories else "NONE"
        lines.append(f"  {mark} {req.requirement_id}: {stories}")
    lines.append("")

    # Non-ID requirements summary
    if result.non_id_requirements:
        covered = sum(1 for r in result.non_id_requirements if r.is_covered)
        lines.append(f"Non-ID Requirements: {covered}/{len(result.non_id_requirements)} covered")
        for req in result.non_id_requirements:
            if not req.is_covered:
                lines.append(f"  [MISSING] {req.requirement_id[:60]}...")
        lines.append("")

    lines.append("=" * 70)
    return "\n".join(lines)


def format_github_report(result: ValidationResult) -> str:
    """Format validation result for GitHub Actions."""
    lines = []

    if result.passed:
        lines.append("::notice::Traceability matrix validation passed")
        lines.append(f"::notice::Coverage: {result.summary['coverage_percent']}%")
    else:
        lines.append("::error::Traceability matrix validation failed")
        lines.append(f"::error::Coverage: {result.summary['coverage_percent']}%")

        for req_id in result.missing_backlog:
            lines.append(f"::error::Missing backlog mapping: {req_id}")

        for req_id in result.missing_verification:
            lines.append(f"::warning::Missing/incomplete verification: {req_id}")

    return "\n".join(lines)


def main() -> int:
    """Main entry point."""
    args = parse_args()

    result = validate_traceability_matrix(args.traceability_file, args.strict)

    if args.output_format == "json":
        print(json.dumps(result.to_dict(), indent=2))
    elif args.output_format == "github":
        print(format_github_report(result))
    else:
        print(format_text_report(result))

    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
