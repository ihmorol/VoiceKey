"""Validate developer documentation alignment with project requirements.

This script validates that developer documentation files are present,
up-to-date, and aligned with the actual project workflow and requirements.

Requirements: E11-S02, FR-OSS05
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
class DocCheck:
    """Result of a documentation check."""

    name: str
    passed: bool
    message: str
    details: list[str] = field(default_factory=list)


@dataclass
class ValidationResult:
    """Aggregated validation result."""

    checks: list[DocCheck] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        return all(c.passed for c in self.checks)

    @property
    def failed_checks(self) -> list[DocCheck]:
        return [c for c in self.checks if not c.passed]

    def add_check(self, check: DocCheck) -> None:
        self.checks.append(check)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate all developer docs
  python validate_developer_docs.py

  # Output results as JSON
  python validate_developer_docs.py --output-format json

  # Check specific docs only
  python validate_developer_docs.py --docs CONTRIBUTING.md AGENTS.md
""",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=None,
        help="Project root directory (default: auto-detect)",
    )
    parser.add_argument(
        "--output-format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    parser.add_argument(
        "--docs",
        nargs="+",
        type=str,
        help="Specific docs to validate (default: all)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on warnings, not just errors",
    )
    return parser.parse_args()


def find_project_root() -> Path:
    """Find the project root by looking for key files."""
    current = Path(__file__).resolve()

    for parent in current.parents:
        if (parent / "software_requirements.md").exists():
            return parent

    # Fallback to script parent's parent
    return current.parents[2]


def check_file_exists(path: Path, description: str) -> DocCheck:
    """Check if a file exists."""
    if path.exists():
        return DocCheck(
            name=f"exists:{path.name}",
            passed=True,
            message=f"{description} exists",
        )
    return DocCheck(
        name=f"exists:{path.name}",
        passed=False,
        message=f"{description} not found: {path}",
    )


def check_required_sections(
    content: str,
    sections: list[str],
    filename: str,
) -> DocCheck:
    """Check if required sections are present in a document."""
    missing = []
    for section in sections:
        # Check for markdown headers with flexible matching
        patterns = [
            rf"^#+\s*{re.escape(section)}",  # Markdown header
            rf"^#+\s*\d+[\.\)]\s*{re.escape(section)}",  # Numbered header like "## 1. Section" or "## 1) Section"
            rf"^#+\s*{re.escape(section.lower())}",  # Lowercase header
            rf"\*\*{re.escape(section)}\*\*",  # Bold text
        ]

        found = any(re.search(p, content, re.MULTILINE | re.IGNORECASE) for p in patterns)
        if not found:
            missing.append(section)

    if missing:
        return DocCheck(
            name=f"sections:{filename}",
            passed=False,
            message=f"Missing sections in {filename}: {', '.join(missing)}",
            details=missing,
        )
    return DocCheck(
        name=f"sections:{filename}",
        passed=True,
        message=f"All required sections present in {filename}",
    )


def check_contributing_md(project_root: Path) -> list[DocCheck]:
    """Validate CONTRIBUTING.md."""
    checks = []
    path = project_root / "CONTRIBUTING.md"

    # Check file exists
    exists_check = check_file_exists(path, "CONTRIBUTING.md")
    checks.append(exists_check)

    if not path.exists():
        return checks

    content = path.read_text(encoding="utf-8")

    # Check required sections
    required_sections = [
        "Development Environment Setup",
        "Contribution Workflow",
        "DCO Sign-Off",
        "Testing",
        "Coding Standards",
    ]
    checks.append(check_required_sections(content, required_sections, "CONTRIBUTING.md"))

    # Check DCO sign-off requirement
    if "Signed-off-by" in content or "DCO" in content:
        checks.append(DocCheck(
            name="dco:CONTRIBUTING.md",
            passed=True,
            message="DCO sign-off requirement documented",
        ))
    else:
        checks.append(DocCheck(
            name="dco:CONTRIBUTING.md",
            passed=False,
            message="DCO sign-off requirement not documented",
        ))

    # Check test commands match actual workflow
    if "pytest" in content:
        checks.append(DocCheck(
            name="test_commands:CONTRIBUTING.md",
            passed=True,
            message="Test commands documented",
        ))
    else:
        checks.append(DocCheck(
            name="test_commands:CONTRIBUTING.md",
            passed=False,
            message="Test commands not documented",
        ))

    # Check Python version requirement
    if "Python 3.11" in content or "Python 3.12" in content:
        checks.append(DocCheck(
            name="python_version:CONTRIBUTING.md",
            passed=True,
            message="Python version requirement documented",
        ))
    else:
        checks.append(DocCheck(
            name="python_version:CONTRIBUTING.md",
            passed=False,
            message="Python version requirement not documented",
        ))

    return checks


def check_agents_md(project_root: Path) -> list[DocCheck]:
    """Validate AGENTS.md."""
    checks = []
    path = project_root / "AGENTS.md"

    # Check file exists
    exists_check = check_file_exists(path, "AGENTS.md")
    checks.append(exists_check)

    if not path.exists():
        return checks

    content = path.read_text(encoding="utf-8")

    # Check required sections (matching actual document structure)
    required_sections = [
        "Repository State",
        "Source of Truth",
        "Environment Setup",
        "Build / Lint / Test Commands",
        "Python Style Guidelines",
    ]
    checks.append(check_required_sections(content, required_sections, "AGENTS.md"))

    # Check test commands
    test_patterns = ["pytest", "tests/unit", "tests/integration"]
    found = sum(1 for p in test_patterns if p in content)
    if found >= 2:
        checks.append(DocCheck(
            name="test_commands:AGENTS.md",
            passed=True,
            message="Test commands documented in AGENTS.md",
        ))
    else:
        checks.append(DocCheck(
            name="test_commands:AGENTS.md",
            passed=False,
            message="Test commands missing or incomplete in AGENTS.md",
        ))

    # Check reference to requirements
    if "software_requirements.md" in content:
        checks.append(DocCheck(
            name="requirements_ref:AGENTS.md",
            passed=True,
            message="Requirements document referenced",
        ))
    else:
        checks.append(DocCheck(
            name="requirements_ref:AGENTS.md",
            passed=False,
            message="Requirements document not referenced",
        ))

    return checks


def check_requirements_development(project_root: Path) -> list[DocCheck]:
    """Validate requirements/development.md."""
    checks = []
    path = project_root / "requirements" / "development.md"

    # Check file exists
    exists_check = check_file_exists(path, "requirements/development.md")
    checks.append(exists_check)

    if not path.exists():
        return checks

    content = path.read_text(encoding="utf-8")

    # Check required sections (matching actual document structure)
    required_sections = [
        "Local Setup",
        "Project Standards",
        "Required Test Commands",
        "Performance Regression Policy",
    ]
    checks.append(check_required_sections(content, required_sections, "requirements/development.md"))

    # Check for perf guardrails reference
    if "perf" in content.lower() and "guardrail" in content.lower():
        checks.append(DocCheck(
            name="perf_guardrails:development.md",
            passed=True,
            message="Performance guardrails documented",
        ))
    else:
        checks.append(DocCheck(
            name="perf_guardrails:development.md",
            passed=False,
            message="Performance guardrails not documented",
        ))

    return checks


def check_requirements_devops(project_root: Path) -> list[DocCheck]:
    """Validate requirements/devops-cicd.md."""
    checks = []
    path = project_root / "requirements" / "devops-cicd.md"

    # Check file exists
    exists_check = check_file_exists(path, "requirements/devops-cicd.md")
    checks.append(exists_check)

    if not path.exists():
        return checks

    content = path.read_text(encoding="utf-8")

    # Check required sections (matching actual document structure)
    required_sections = [
        "CI/CD Principles",
        "PR Pipeline Requirements",
        "Release Pipeline Requirements",
        "Security Controls",
    ]
    checks.append(check_required_sections(content, required_sections, "requirements/devops-cicd.md"))

    # Check for OIDC/trusted publishing reference
    if "OIDC" in content or "trusted publishing" in content.lower():
        checks.append(DocCheck(
            name="trusted_publishing:devops-cicd.md",
            passed=True,
            message="OIDC trusted publishing documented",
        ))
    else:
        checks.append(DocCheck(
            name="trusted_publishing:devops-cicd.md",
            passed=False,
            message="OIDC trusted publishing not documented",
        ))

    return checks


def check_compatibility_matrix(project_root: Path) -> list[DocCheck]:
    """Validate docs/compatibility-matrix.md."""
    checks = []
    path = project_root / "docs" / "compatibility-matrix.md"

    # Check file exists
    exists_check = check_file_exists(path, "docs/compatibility-matrix.md")
    checks.append(exists_check)

    if not path.exists():
        return checks

    content = path.read_text(encoding="utf-8")

    # Check required sections (matching actual document structure)
    required_sections = [
        "Supported Operating Systems",
        "Supported Python Versions",
        "Linux Platform Notes",
        "Known Limitations",
    ]
    checks.append(check_required_sections(content, required_sections, "compatibility-matrix.md"))

    # Check supported OS versions (flexible matching for table format)
    # Look for Ubuntu versions and Windows separately since they may be in different columns
    ubuntu_versions = ["22.04", "24.04"]
    windows_found = "Windows" in content and ("| 10 |" in content or "| 11 |" in content)
    
    found_ubuntu = sum(1 for v in ubuntu_versions if v in content)
    
    if found_ubuntu >= 2 and windows_found:
        checks.append(DocCheck(
            name="os_versions:compatibility-matrix.md",
            passed=True,
            message="Supported OS versions documented",
        ))
    else:
        checks.append(DocCheck(
            name="os_versions:compatibility-matrix.md",
            passed=False,
            message="Supported OS versions incomplete",
        ))

    # Check Python versions
    if "3.11" in content and "3.12" in content:
        checks.append(DocCheck(
            name="python_versions:compatibility-matrix.md",
            passed=True,
            message="Supported Python versions documented",
        ))
    else:
        checks.append(DocCheck(
            name="python_versions:compatibility-matrix.md",
            passed=False,
            message="Supported Python versions incomplete",
        ))

    # Check Wayland/X11 documentation
    if "Wayland" in content and "X11" in content:
        checks.append(DocCheck(
            name="display_servers:compatibility-matrix.md",
            passed=True,
            message="Display server compatibility documented",
        ))
    else:
        checks.append(DocCheck(
            name="display_servers:compatibility-matrix.md",
            passed=False,
            message="Display server compatibility not documented",
        ))

    return checks


def check_docs_alignment(project_root: Path) -> list[DocCheck]:
    """Check that docs are aligned with actual implementation."""
    checks = []

    # Check test commands in CONTRIBUTING.md match actual test structure
    contributing_path = project_root / "CONTRIBUTING.md"
    if contributing_path.exists():
        content = contributing_path.read_text(encoding="utf-8")

        # Verify test directories exist
        test_dirs = ["tests/unit", "tests/integration"]
        for test_dir in test_dirs:
            test_path = project_root / test_dir
            if test_path.exists() and test_dir in content:
                checks.append(DocCheck(
                    name=f"alignment:{test_dir}",
                    passed=True,
                    message=f"Documented test directory {test_dir} exists",
                ))
            elif test_dir in content and not test_path.exists():
                checks.append(DocCheck(
                    name=f"alignment:{test_dir}",
                    passed=False,
                    message=f"Documented test directory {test_dir} does not exist",
                ))

    # Check perf guardrails script exists if documented
    perf_script = project_root / "scripts" / "ci" / "check_perf_guardrails.py"
    contributing_content = contributing_path.read_text(encoding="utf-8") if contributing_path.exists() else ""

    if "check_perf_guardrails" in contributing_content:
        if perf_script.exists():
            checks.append(DocCheck(
                name="alignment:perf_script",
                passed=True,
                message="Documented perf guardrails script exists",
            ))
        else:
            checks.append(DocCheck(
                name="alignment:perf_script",
                passed=False,
                message="Documented perf guardrails script not found",
            ))

    return checks


def validate_docs(
    project_root: Path,
    specific_docs: list[str] | None = None,
) -> ValidationResult:
    """Run all documentation validation checks."""
    result = ValidationResult()

    # Define all check functions
    all_checks = {
        "CONTRIBUTING.md": lambda: check_contributing_md(project_root),
        "AGENTS.md": lambda: check_agents_md(project_root),
        "requirements/development.md": lambda: check_requirements_development(project_root),
        "requirements/devops-cicd.md": lambda: check_requirements_devops(project_root),
        "docs/compatibility-matrix.md": lambda: check_compatibility_matrix(project_root),
        "alignment": lambda: check_docs_alignment(project_root),
    }

    # Filter to specific docs if provided
    checks_to_run = all_checks
    if specific_docs:
        checks_to_run = {k: v for k, v in all_checks.items() if k in specific_docs}

    # Run checks
    for name, check_func in checks_to_run.items():
        try:
            for check in check_func():
                result.add_check(check)
        except Exception as e:
            result.add_check(DocCheck(
                name=f"error:{name}",
                passed=False,
                message=f"Error checking {name}: {e}",
            ))

    return result


def format_output(result: ValidationResult, format_type: str) -> str:
    """Format validation result for output."""
    if format_type == "json":
        return json.dumps({
            "passed": result.all_passed,
            "total_checks": len(result.checks),
            "passed_checks": sum(1 for c in result.checks if c.passed),
            "failed_checks": len(result.failed_checks),
            "checks": [
                {
                    "name": c.name,
                    "passed": c.passed,
                    "message": c.message,
                    "details": c.details,
                }
                for c in result.checks
            ],
        }, indent=2)

    # Text format
    lines = []
    lines.append("=" * 60)
    lines.append("Developer Documentation Validation Report")
    lines.append("=" * 60)

    for check in result.checks:
        status = "✅" if check.passed else "❌"
        lines.append(f"{status} {check.name}: {check.message}")
        for detail in check.details:
            lines.append(f"    - {detail}")

    lines.append("")
    lines.append("-" * 60)
    if result.all_passed:
        lines.append("Result: ALL CHECKS PASSED")
    else:
        lines.append(f"Result: {len(result.failed_checks)} CHECK(S) FAILED")
        for check in result.failed_checks:
            lines.append(f"  - {check.name}: {check.message}")

    return "\n".join(lines)


def main() -> int:
    args = parse_args()

    # Determine project root
    project_root = args.project_root or find_project_root()

    if not (project_root / "software_requirements.md").exists():
        print(f"Error: Project root not found or invalid: {project_root}", file=sys.stderr)
        return 2

    # Run validation
    result = validate_docs(project_root, args.docs)

    # Output results
    output = format_output(result, args.output_format)
    print(output)

    # Return code
    if not result.all_passed:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
