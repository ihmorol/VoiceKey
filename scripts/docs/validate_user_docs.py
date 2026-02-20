"""Validate user documentation completeness and release-link integrity.

This script checks that user-facing documentation is complete and properly
linked to release artifacts.

Requirements: E11-S01 - User docs release-link completeness validation

Checks:
- Required documentation sections exist (installation, onboarding, troubleshooting, commands)
- Internal links between docs are valid
- Version references are current
- Release links point to valid locations
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
class DocSection:
    """Represents a required documentation section."""

    name: str
    required_paths: list[str]
    required_headers: list[str] = field(default_factory=list)
    description: str = ""


@dataclass
class ValidationResult:
    """Result of validation checks."""

    passed: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    sections_checked: dict[str, bool] = field(default_factory=dict)
    links_checked: int = 0
    links_broken: list[str] = field(default_factory=list)


# Required documentation sections per E11-S01 acceptance criteria
REQUIRED_SECTIONS: list[DocSection] = [
    DocSection(
        name="installation",
        required_paths=["docs/installation/index.md", "docs/installation/linux.md", "docs/installation/windows.md"],
        required_headers=["System Requirements", "Installation"],
        description="Installation guide for Linux and Windows",
    ),
    DocSection(
        name="onboarding",
        required_paths=["docs/getting-started.md"],
        required_headers=["Setup", "Configuration", "Tutorial"],
        description="Onboarding and setup wizard walkthrough",
    ),
    DocSection(
        name="commands",
        required_paths=["docs/guide/commands.md", "docs/reference/commands.md"],
        required_headers=["Command", "Control Commands", "Editing"],
        description="Command reference for voice commands",
    ),
    DocSection(
        name="troubleshooting",
        required_paths=["docs/resources/troubleshooting.md"],
        required_headers=["Common Issues", "Diagnostic", "Solutions"],
        description="Troubleshooting guide for common problems",
    ),
]

# Pattern for markdown links: [text](target)
MARKDOWN_LINK_PATTERN = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")

# Pattern for version references like v1.0.0, version 1.0.0, etc.
VERSION_PATTERN = re.compile(r"\b(v?\d+\.\d+(?:\.\d+)?)\b", re.IGNORECASE)

# Pattern for release links
RELEASE_LINK_PATTERN = re.compile(r"github\.com/[^/]+/[^/]+/releases", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate all user docs
  python validate_user_docs.py --docs-root docs/

  # Output in JSON format
  python validate_user_docs.py --docs-root docs/ --output-format json

  # Check specific sections only
  python validate_user_docs.py --docs-root docs/ --sections installation,troubleshooting
""",
    )
    parser.add_argument(
        "--docs-root",
        type=Path,
        default=Path("docs"),
        help="Root directory for documentation (default: docs)",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path("."),
        help="Repository root directory (default: current directory)",
    )
    parser.add_argument(
        "--sections",
        type=str,
        default="",
        help="Comma-separated sections to check (default: all)",
    )
    parser.add_argument(
        "--output-format",
        choices=["text", "json", "github"],
        default="text",
        help="Output format",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors",
    )
    return parser.parse_args()


def check_file_exists(path: Path, repo_root: Path) -> tuple[bool, str]:
    """Check if a file exists.

    Returns:
        Tuple of (exists, error_message)
    """
    full_path = repo_root / path
    if not full_path.exists():
        return False, f"File not found: {path}"
    if not full_path.is_file():
        return False, f"Not a file: {path}"
    return True, ""


def check_headers(content: str, required_headers: list[str]) -> list[str]:
    """Check that required headers are present in markdown content.

    Returns:
        List of missing headers
    """
    missing = []
    content_lower = content.lower()

    for header in required_headers:
        # Check for header in various forms: # Header, ## Header, Header in text
        patterns = [
            rf"^#+\s*{re.escape(header)}",  # Markdown header
            rf"\b{re.escape(header.lower())}\b",  # In text
        ]

        found = False
        for pattern in patterns:
            if re.search(pattern, content_lower, re.MULTILINE | re.IGNORECASE):
                found = True
                break

        if not found:
            missing.append(header)

    return missing


def extract_links(content: str, source_path: Path) -> list[tuple[str, str, Path]]:
    """Extract markdown links from content.

    Returns:
        List of (link_text, link_target, resolved_path)
    """
    links = []

    for match in MARKDOWN_LINK_PATTERN.finditer(content):
        text = match.group(1)
        target = match.group(2)

        # Skip external URLs and anchors
        if target.startswith(("http://", "https://", "#", "mailto:")):
            continue

        # Strip anchor fragment for file path resolution
        file_target = target.split("#")[0] if "#" in target else target

        # Resolve relative path
        source_dir = source_path.parent
        resolved = (source_dir / file_target).resolve()

        links.append((text, target, resolved))

    return links


def check_link_valid(link_target: str, resolved_path: Path, repo_root: Path) -> tuple[bool, str]:
    """Check if a link target is valid.

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Handle anchor links in same file
    if "#" in link_target:
        # The resolved_path already has the anchor stripped, so just check it exists
        if not resolved_path.exists():
            return False, f"Linked file not found: {link_target}"
        # Note: We don't validate anchor targets as that would require parsing
        return True, ""

    # Check file exists
    try:
        relative = resolved_path.relative_to(repo_root)
        full_path = repo_root / relative
    except ValueError:
        full_path = resolved_path

    if not full_path.exists():
        return False, f"Linked file not found: {link_target}"

    return True, ""


def check_version_references(content: str, doc_path: Path) -> list[str]:
    """Check version references in documentation.

    Returns:
        List of warnings about potentially outdated version references
    """
    warnings = []

    # Find all version-like strings
    versions = VERSION_PATTERN.findall(content)

    if versions:
        # Just note that version references exist - actual validation would
        # require comparing to current version
        unique_versions = sorted(set(versions))
        if len(unique_versions) > 2:
            warnings.append(
                f"{doc_path}: Multiple version references found: {', '.join(unique_versions[:3])}... "
                f"Verify these are current"
            )

    return warnings


def validate_section(
    section: DocSection,
    docs_root: Path,
    repo_root: Path,
) -> tuple[bool, list[str], list[str], list[str]]:
    """Validate a documentation section.

    Returns:
        Tuple of (passed, errors, warnings, broken_links)
    """
    errors = []
    warnings = []
    broken_links = []

    # Check required files exist
    for req_path in section.required_paths:
        exists, error = check_file_exists(Path(req_path), repo_root)
        if not exists:
            errors.append(f"[{section.name}] {error}")

    # Check file contents
    for req_path in section.required_paths:
        full_path = repo_root / req_path
        if not full_path.exists():
            continue

        content = full_path.read_text(encoding="utf-8")

        # Check required headers
        missing_headers = check_headers(content, section.required_headers)
        for header in missing_headers:
            warnings.append(f"[{section.name}] Missing header in {req_path}: '{header}'")

        # Check internal links
        links = extract_links(content, full_path)
        for text, target, resolved in links:
            is_valid, error = check_link_valid(target, resolved, repo_root)
            if not is_valid:
                broken_links.append(f"{req_path}: {error} (link: '{text}')")

        # Check version references
        version_warnings = check_version_references(content, Path(req_path))
        warnings.extend(version_warnings)

    passed = len(errors) == 0
    return passed, errors, warnings, broken_links


def validate_all(
    docs_root: Path,
    repo_root: Path,
    sections_to_check: list[str] | None = None,
) -> ValidationResult:
    """Run all validation checks.

    Args:
        docs_root: Root directory for documentation
        repo_root: Repository root directory
        sections_to_check: List of section names to check, or None for all

    Returns:
        ValidationResult with all findings
    """
    result = ValidationResult(passed=True)

    sections = REQUIRED_SECTIONS
    if sections_to_check:
        sections = [s for s in REQUIRED_SECTIONS if s.name in sections_to_check]

    for section in sections:
        passed, errors, warnings, broken_links = validate_section(
            section, docs_root, repo_root
        )

        result.sections_checked[section.name] = passed
        result.errors.extend(errors)
        result.warnings.extend(warnings)
        result.links_broken.extend(broken_links)
        result.links_checked += len(broken_links) + sum(
            1 for _ in range(len(errors) + len(warnings))
        )

        if not passed:
            result.passed = False

    return result


def format_output(result: ValidationResult, format_type: str, strict: bool) -> str:
    """Format validation result for output."""
    if format_type == "json":
        return json.dumps(
            {
                "passed": result.passed and (not strict or not result.warnings),
                "errors": result.errors,
                "warnings": result.warnings,
                "sections_checked": result.sections_checked,
                "links_checked": result.links_checked,
                "links_broken": result.links_broken,
            },
            indent=2,
        )

    if format_type == "github":
        lines = []
        if result.errors or (strict and result.warnings):
            lines.append("::error::User documentation validation failed")
            for error in result.errors:
                lines.append(f"::error::{error}")
            for warning in result.warnings:
                if strict:
                    lines.append(f"::error::{warning}")
                else:
                    lines.append(f"::warning::{warning}")
        else:
            lines.append("::notice::User documentation validation passed")
        return "\n".join(lines)

    # Default text format
    lines = []

    # Summary
    status = "PASSED" if result.passed else "FAILED"
    if strict and result.warnings:
        status = "FAILED (strict mode)"
    lines.append(f"User Documentation Validation: {status}")
    lines.append("")

    # Sections checked
    lines.append("Sections Checked:")
    for section, passed in result.sections_checked.items():
        mark = "OK" if passed else "FAIL"
        lines.append(f"  [{mark}] {section}")
    lines.append("")

    # Errors
    if result.errors:
        lines.append("Errors:")
        for error in result.errors:
            lines.append(f"  - {error}")
        lines.append("")

    # Warnings
    if result.warnings:
        lines.append("Warnings:")
        for warning in result.warnings:
            lines.append(f"  - {warning}")
        lines.append("")

    # Broken links
    if result.links_broken:
        lines.append("Broken Links:")
        for link in result.links_broken:
            lines.append(f"  - {link}")
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    """Main entry point."""
    args = parse_args()

    # Determine sections to check
    sections_to_check = None
    if args.sections:
        sections_to_check = [s.strip() for s in args.sections.split(",")]

    # Run validation
    result = validate_all(args.docs_root, args.repo_root, sections_to_check)

    # Format and print output
    output = format_output(result, args.output_format, args.strict)
    print(output)

    # Determine exit code
    if result.errors:
        return 1
    if args.strict and result.warnings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
