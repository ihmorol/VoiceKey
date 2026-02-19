"""Unit tests for release distribution policy validators (E07-S06)."""

from __future__ import annotations

from voicekey.release.policy import validate_release_policy


_CHECKLIST_TEXT = """
## Pre-release

- [ ] migration notes prepared (if needed)

## Post-release

- [ ] update compatibility matrix
"""

_DISTRIBUTION_TEXT = """
## 6. Backward Compatibility

- one previous major version migration path supported
"""


def test_validate_release_policy_accepts_required_x64_artifacts() -> None:
    report = validate_release_policy(
        artifact_names=[
            "voicekey-1.2.3-py3-none-any.whl",
            "voicekey-1.2.3.tar.gz",
            "voicekey-1.2.3-windows-x64-installer.exe",
            "voicekey-1.2.3-windows-x64-portable.zip",
            "voicekey-1.2.3-linux-x86_64.AppImage",
        ],
        release_version="1.2.3",
        checklist_text=_CHECKLIST_TEXT,
        distribution_text=_DISTRIBUTION_TEXT,
    )

    assert report.ok is True
    assert report.errors == ()


def test_validate_release_policy_rejects_architecture_drift() -> None:
    report = validate_release_policy(
        artifact_names=[
            "voicekey-1.2.3-py3-none-any.whl",
            "voicekey-1.2.3.tar.gz",
            "voicekey-1.2.3-windows-arm64-installer.exe",
            "voicekey-1.2.3-windows-x64-portable.zip",
            "voicekey-1.2.3-linux-x86_64.AppImage",
        ],
        release_version="1.2.3",
        checklist_text=_CHECKLIST_TEXT,
        distribution_text=_DISTRIBUTION_TEXT,
    )

    assert report.ok is False
    assert any("Unsupported architecture artifact detected" in error for error in report.errors)


def test_validate_release_policy_rejects_invalid_naming_and_missing_channels() -> None:
    report = validate_release_policy(
        artifact_names=[
            "voicekey-1.2.3-py3-none-any.whl",
            "voicekey-1.2.3.tar.gz",
            "voicekey-1.2.3-windows-x64-setup.exe",
            "voicekey-1.2.3-linux-x86_64.AppImage",
        ],
        release_version="1.2.3",
        checklist_text=_CHECKLIST_TEXT,
        distribution_text=_DISTRIBUTION_TEXT,
    )

    assert report.ok is False
    assert "Missing required release artifact: voicekey-1.2.3-windows-x64-installer.exe" in report.errors
    assert "Missing required release artifact: voicekey-1.2.3-windows-x64-portable.zip" in report.errors
    assert any("Unexpected release artifact naming drift" in error for error in report.errors)


def test_validate_release_policy_rejects_missing_compatibility_policy_markers() -> None:
    report = validate_release_policy(
        artifact_names=[
            "voicekey-1.2.3-py3-none-any.whl",
            "voicekey-1.2.3.tar.gz",
            "voicekey-1.2.3-windows-x64-installer.exe",
            "voicekey-1.2.3-windows-x64-portable.zip",
            "voicekey-1.2.3-linux-x86_64.AppImage",
        ],
        release_version="1.2.3",
        checklist_text="## Pre-release\n- [ ] version bumped\n",
        distribution_text="## 6. Backward Compatibility\n",
    )

    assert report.ok is False
    assert "Release checklist must include migration notes verification." in report.errors
    assert "Release checklist must include compatibility matrix update step." in report.errors
    assert "Distribution policy must define one-previous-major migration support." in report.errors
