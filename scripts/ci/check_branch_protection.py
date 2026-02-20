"""Check branch protection configuration requirements.

This script validates that required branch protection settings are documented
and provides informational output about expected configuration. The actual
branch protection is enforced by GitHub repository settings.

This is an informational/validation check per requirements/devops-cicd.md section 4.

Expected branch protection rules for 'main':
- Required status checks enabled
- No direct push to protected branches
- At least one reviewed approval
- Signed tags for releases
- Required CODEOWNERS review for release pipeline changes
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


# Required status checks that should be enabled for the main branch
REQUIRED_STATUS_CHECKS = [
    "lint",
    "vulnerability-scan",
    "secret-scan",
    "license-scan",
    "unit-tests",
    "integration-smoke",
    "package-smoke",
    "performance-guardrail",
]

# Required review settings
REQUIRED_REVIEW_SETTINGS = {
    "required_approving_review_count": 1,
    "require_code_owner_reviews": True,
    "dismiss_stale_reviews": True,
}

# Protected branch patterns
PROTECTED_BRANCHES = ["main"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--check-codowners-file",
        type=Path,
        default=Path(".github/CODEOWNERS"),
        help="Path to CODEOWNERS file to validate",
    )
    parser.add_argument(
        "--github-api-response",
        type=Path,
        default=None,
        help="Optional path to GitHub API response JSON for branch protection",
    )
    return parser.parse_args()


def check_codowners_file(path: Path) -> dict[str, Any]:
    """Validate CODEOWNERS file exists and contains required patterns."""
    result = {
        "exists": path.exists(),
        "has_workflow_rules": False,
        "required_patterns": [],
    }
    
    if not path.exists():
        return result
    
    content = path.read_text(encoding="utf-8")
    
    # Check for workflow patterns
    workflow_patterns = [
        "/.github/workflows/release.yml",
        "/.github/workflows/ci.yml",
    ]
    
    for pattern in workflow_patterns:
        if pattern in content:
            result["required_patterns"].append(pattern)
    
    result["has_workflow_rules"] = len(result["required_patterns"]) > 0
    
    return result


def check_branch_protection_from_api(api_response: dict[str, Any] | None) -> dict[str, Any]:
    """Validate branch protection settings from GitHub API response."""
    result = {
        "api_available": api_response is not None,
        "required_status_checks": [],
        "enforce_admins": False,
        "required_pull_request_reviews": {},
        "restrictions": None,
    }
    
    if api_response is None:
        return result
    
    # Extract required status checks
    checks = api_response.get("required_status_checks", {})
    result["required_status_checks"] = checks.get("contexts", [])
    result["enforce_admins"] = api_response.get("enforce_admins", False)
    
    # Extract PR review requirements
    reviews = api_response.get("required_pull_request_reviews", {})
    result["required_pull_request_reviews"] = {
        "required_approving_review_count": reviews.get("required_approving_review_count", 0),
        "require_code_owner_reviews": reviews.get("require_code_owner_reviews", False),
        "dismiss_stale_reviews": reviews.get("dismiss_stale_reviews", False),
    }
    
    return result


def validate_configuration(
    codowners_result: dict[str, Any],
    protection_result: dict[str, Any],
) -> list[str]:
    """Validate configuration and return list of issues."""
    issues = []
    
    # Check CODEOWNERS file
    if not codowners_result["exists"]:
        issues.append("CODEOWNERS file not found at .github/CODEOWNERS")
    elif not codowners_result["has_workflow_rules"]:
        issues.append("CODEOWNERS file missing workflow review rules")
    
    # If API response available, validate branch protection
    if protection_result["api_available"]:
        # Check required status checks
        enabled_checks = set(protection_result["required_status_checks"])
        missing_checks = set(REQUIRED_STATUS_CHECKS) - enabled_checks
        if missing_checks:
            issues.append(f"Missing required status checks: {', '.join(missing_checks)}")
        
        # Check review requirements
        reviews = protection_result["required_pull_request_reviews"]
        if reviews.get("required_approving_review_count", 0) < REQUIRED_REVIEW_SETTINGS["required_approving_review_count"]:
            issues.append(f"Required approving review count should be at least {REQUIRED_REVIEW_SETTINGS['required_approving_review_count']}")
        if not reviews.get("require_code_owner_reviews", False):
            issues.append("CODEOWNERS review should be required")
        if not reviews.get("dismiss_stale_reviews", False):
            issues.append("Stale reviews should be dismissed on new commits")
    
    return issues


def main() -> int:
    args = parse_args()
    
    # Check CODEOWNERS file
    codowners_result = check_codowners_file(args.check_codowners_file)
    
    # Check branch protection from API if provided
    api_response = None
    if args.github_api_response and args.github_api_response.exists():
        api_response = json.loads(args.github_api_response.read_text(encoding="utf-8"))
    
    protection_result = check_branch_protection_from_api(api_response)
    
    # Validate configuration
    issues = validate_configuration(codowners_result, protection_result)
    
    # Output results
    if args.format == "json":
        output = {
            "codowners_check": codowners_result,
            "branch_protection_check": protection_result,
            "required_status_checks": REQUIRED_STATUS_CHECKS,
            "required_review_settings": REQUIRED_REVIEW_SETTINGS,
            "protected_branches": PROTECTED_BRANCHES,
            "issues": issues,
            "status": "pass" if not issues else "fail",
        }
        print(json.dumps(output, indent=2, sort_keys=True))
        return 1 if issues else 0
    
    print("=== Branch Protection Configuration Check ===\n")
    
    print("CODEOWNERS File:")
    print(f"  Exists: {codowners_result['exists']}")
    print(f"  Has workflow rules: {codowners_result['has_workflow_rules']}")
    if codowners_result['required_patterns']:
        print(f"  Patterns: {', '.join(codowners_result['required_patterns'])}")
    print()
    
    print("Branch Protection (from API):")
    print(f"  API available: {protection_result['api_available']}")
    if protection_result['api_available']:
        print(f"  Enforce admins: {protection_result['enforce_admins']}")
        print(f"  Required status checks: {', '.join(protection_result['required_status_checks']) or 'none'}")
        reviews = protection_result['required_pull_request_reviews']
        print(f"  Required approvals: {reviews.get('required_approving_review_count', 0)}")
        print(f"  CODEOWNERS review required: {reviews.get('require_code_owner_reviews', False)}")
        print(f"  Dismiss stale reviews: {reviews.get('dismiss_stale_reviews', False)}")
    print()
    
    print("Required Status Checks:")
    for check in REQUIRED_STATUS_CHECKS:
        print(f"  - {check}")
    print()
    
    if issues:
        print("Issues Found:")
        for issue in issues:
            print(f"  - {issue}")
        print()
        print("branch_protection_check=failed")
        return 1
    else:
        print("branch_protection_check=passed")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
