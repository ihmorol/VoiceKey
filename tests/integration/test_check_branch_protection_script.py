"""Integration tests for branch protection check script (E08-S04)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_check_branch_protection_fails_without_codowners_file(tmp_path: Path) -> None:
    script = Path(__file__).resolve().parents[2] / "scripts" / "ci" / "check_branch_protection.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--check-codowners-file",
            str(tmp_path / "CODEOWNERS"),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "CODEOWNERS file not found" in result.stdout
    assert "branch_protection_check=failed" in result.stdout


def test_check_branch_protection_passes_with_valid_codowners(tmp_path: Path) -> None:
    codowners_file = tmp_path / ".github" / "CODEOWNERS"
    codowners_file.parent.mkdir(parents=True)
    codowners_file.write_text(
        "/.github/workflows/release.yml    @emon-morol\n"
        "/.github/workflows/ci.yml         @emon-morol\n",
        encoding="utf-8",
    )
    
    script = Path(__file__).resolve().parents[2] / "scripts" / "ci" / "check_branch_protection.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--check-codowners-file",
            str(codowners_file),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Has workflow rules: True" in result.stdout
    assert "branch_protection_check=passed" in result.stdout


def test_check_branch_protection_fails_with_codowners_missing_workflow_rules(tmp_path: Path) -> None:
    codowners_file = tmp_path / ".github" / "CODEOWNERS"
    codowners_file.parent.mkdir(parents=True)
    codowners_file.write_text(
        "/src/    @emon-morol\n",
        encoding="utf-8",
    )
    
    script = Path(__file__).resolve().parents[2] / "scripts" / "ci" / "check_branch_protection.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--check-codowners-file",
            str(codowners_file),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "CODEOWNERS file missing workflow review rules" in result.stdout


def test_check_branch_protection_outputs_json_format(tmp_path: Path) -> None:
    codowners_file = tmp_path / ".github" / "CODEOWNERS"
    codowners_file.parent.mkdir(parents=True)
    codowners_file.write_text(
        "/.github/workflows/release.yml    @emon-morol\n",
        encoding="utf-8",
    )
    
    script = Path(__file__).resolve().parents[2] / "scripts" / "ci" / "check_branch_protection.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--format",
            "json",
            "--check-codowners-file",
            str(codowners_file),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    output = json.loads(result.stdout)
    
    assert output["status"] == "pass"
    assert output["codowners_check"]["exists"] is True
    assert output["codowners_check"]["has_workflow_rules"] is True
    assert "required_status_checks" in output
    assert "lint" in output["required_status_checks"]


def test_check_branch_protection_validates_branch_protection_from_api(tmp_path: Path) -> None:
    codowners_file = tmp_path / ".github" / "CODEOWNERS"
    codowners_file.parent.mkdir(parents=True)
    codowners_file.write_text(
        "/.github/workflows/release.yml    @emon-morol\n"
        "/.github/workflows/ci.yml         @emon-morol\n",
        encoding="utf-8",
    )
    
    api_response = tmp_path / "branch_protection.json"
    api_response.write_text(
        json.dumps({
            "enforce_admins": True,
            "required_status_checks": {
                "contexts": [
                    "lint",
                    "vulnerability-scan",
                    "secret-scan",
                    "license-scan",
                    "unit-tests",
                    "integration-smoke",
                    "package-smoke",
                    "performance-guardrail",
                ],
            },
            "required_pull_request_reviews": {
                "required_approving_review_count": 1,
                "require_code_owner_reviews": True,
                "dismiss_stale_reviews": True,
            },
        }),
        encoding="utf-8",
    )
    
    script = Path(__file__).resolve().parents[2] / "scripts" / "ci" / "check_branch_protection.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--format",
            "json",
            "--check-codowners-file",
            str(codowners_file),
            "--github-api-response",
            str(api_response),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    output = json.loads(result.stdout)
    
    assert output["branch_protection_check"]["api_available"] is True
    assert output["branch_protection_check"]["enforce_admins"] is True
    assert "lint" in output["branch_protection_check"]["required_status_checks"]
    assert output["branch_protection_check"]["required_pull_request_reviews"]["require_code_owner_reviews"] is True


def test_check_branch_protection_detects_missing_status_checks(tmp_path: Path) -> None:
    codowners_file = tmp_path / ".github" / "CODEOWNERS"
    codowners_file.parent.mkdir(parents=True)
    codowners_file.write_text(
        "/.github/workflows/release.yml    @emon-morol\n"
        "/.github/workflows/ci.yml         @emon-morol\n",
        encoding="utf-8",
    )
    
    api_response = tmp_path / "branch_protection.json"
    api_response.write_text(
        json.dumps({
            "enforce_admins": True,
            "required_status_checks": {
                "contexts": ["lint"],  # Missing many required checks
            },
            "required_pull_request_reviews": {
                "required_approving_review_count": 1,
                "require_code_owner_reviews": True,
                "dismiss_stale_reviews": True,
            },
        }),
        encoding="utf-8",
    )
    
    script = Path(__file__).resolve().parents[2] / "scripts" / "ci" / "check_branch_protection.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--format",
            "json",
            "--check-codowners-file",
            str(codowners_file),
            "--github-api-response",
            str(api_response),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    output = json.loads(result.stdout)
    
    assert output["status"] == "fail"
    assert any("Missing required status checks" in issue for issue in output["issues"])


def test_check_branch_protection_detects_missing_codeowners_review(tmp_path: Path) -> None:
    codowners_file = tmp_path / ".github" / "CODEOWNERS"
    codowners_file.parent.mkdir(parents=True)
    codowners_file.write_text(
        "/.github/workflows/release.yml    @emon-morol\n"
        "/.github/workflows/ci.yml         @emon-morol\n",
        encoding="utf-8",
    )
    
    api_response = tmp_path / "branch_protection.json"
    api_response.write_text(
        json.dumps({
            "enforce_admins": True,
            "required_status_checks": {
                "contexts": [
                    "lint",
                    "vulnerability-scan",
                    "secret-scan",
                    "license-scan",
                    "unit-tests",
                    "integration-smoke",
                    "package-smoke",
                    "performance-guardrail",
                ],
            },
            "required_pull_request_reviews": {
                "required_approving_review_count": 1,
                "require_code_owner_reviews": False,  # Should be True
                "dismiss_stale_reviews": True,
            },
        }),
        encoding="utf-8",
    )
    
    script = Path(__file__).resolve().parents[2] / "scripts" / "ci" / "check_branch_protection.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--format",
            "json",
            "--check-codowners-file",
            str(codowners_file),
            "--github-api-response",
            str(api_response),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    output = json.loads(result.stdout)
    
    assert output["status"] == "fail"
    assert any("CODEOWNERS review should be required" in issue for issue in output["issues"])
