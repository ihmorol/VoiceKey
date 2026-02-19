"""Release distribution policy validators."""

from __future__ import annotations

import re
from dataclasses import dataclass

from voicekey.release.linux_artifacts import build_linux_artifact_name
from voicekey.release.windows_artifacts import build_windows_artifact_name

_SEMVER_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)(?:[-+][0-9A-Za-z.-]+)?$")
_FORBIDDEN_ARCH_PATTERN = re.compile(r"(?:^|[_-])(arm64|aarch64|armv7|armv6|win32|i686)(?:[_\-.]|$)")


@dataclass(frozen=True, slots=True)
class ReleasePolicyReport:
    """Result object for distribution policy validation."""

    errors: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.errors


def validate_release_policy(
    *,
    artifact_names: list[str],
    release_version: str,
    checklist_text: str,
    distribution_text: str,
) -> ReleasePolicyReport:
    """Validate naming, architecture scope, and compatibility policy coverage."""
    errors: list[str] = []
    normalized = _normalize_version(release_version)
    errors.extend(validate_artifact_naming(artifact_names, release_version=normalized))
    errors.extend(validate_architecture_scope(artifact_names))
    errors.extend(
        validate_compatibility_policy_documents(
            checklist_text=checklist_text,
            distribution_text=distribution_text,
        )
    )
    return ReleasePolicyReport(errors=tuple(errors))


def validate_artifact_naming(artifact_names: list[str], *, release_version: str) -> list[str]:
    """Validate release artifact names against distribution naming policy."""
    errors: list[str] = []
    expected_linux = build_linux_artifact_name(release_version)
    expected_windows_installer = build_windows_artifact_name(
        release_version,
        artifact_kind="installer",
    )
    expected_windows_portable = build_windows_artifact_name(
        release_version,
        artifact_kind="portable",
    )

    required_exact = {
        expected_linux,
        expected_windows_installer,
        expected_windows_portable,
        f"voicekey-{release_version}.tar.gz",
    }

    names = set(artifact_names)
    missing = sorted(required_exact - names)
    for name in missing:
        errors.append(f"Missing required release artifact: {name}")

    wheel_names = [name for name in artifact_names if name.endswith(".whl")]
    if not wheel_names:
        errors.append("Missing required wheel artifact for PyPI channel.")
    for wheel_name in wheel_names:
        if not _is_valid_wheel_name(wheel_name, release_version=release_version):
            errors.append(f"Invalid wheel artifact name: {wheel_name}")

    for artifact_name in artifact_names:
        if artifact_name.endswith(".whl") or artifact_name.endswith(".tar.gz"):
            continue
        if artifact_name in required_exact:
            continue
        errors.append(f"Unexpected release artifact naming drift: {artifact_name}")

    return errors


def validate_architecture_scope(artifact_names: list[str]) -> list[str]:
    """Validate that all release artifacts stay within x64-only public scope."""
    errors: list[str] = []
    for artifact_name in artifact_names:
        lowered = artifact_name.lower()

        if _FORBIDDEN_ARCH_PATTERN.search(lowered) is not None:
            errors.append(f"Unsupported architecture artifact detected: {artifact_name}")
            continue

        if lowered.endswith(".appimage") and "linux-x86_64" not in lowered:
            errors.append(f"Linux artifact must target x86_64: {artifact_name}")
            continue

        if "-windows-" in lowered and "-windows-x64-" not in lowered:
            errors.append(f"Windows artifact must target x64: {artifact_name}")
            continue

        if lowered.endswith(".whl") and "none-any" not in lowered:
            if "win_amd64" not in lowered and "x86_64" not in lowered:
                errors.append(f"Platform wheel must target x64 architecture: {artifact_name}")

    return errors


def validate_compatibility_policy_documents(*, checklist_text: str, distribution_text: str) -> list[str]:
    """Validate compatibility and migration policy requirements in release docs."""
    errors: list[str] = []
    checklist_lower = checklist_text.lower()
    distribution_lower = distribution_text.lower()

    if "migration notes prepared" not in checklist_lower:
        errors.append("Release checklist must include migration notes verification.")
    if "update compatibility matrix" not in checklist_lower:
        errors.append("Release checklist must include compatibility matrix update step.")
    if "one previous major version migration path supported" not in distribution_lower:
        errors.append("Distribution policy must define one-previous-major migration support.")

    return errors


def _normalize_version(version: str) -> str:
    cleaned = version.strip()
    if not _SEMVER_RE.match(cleaned):
        raise ValueError(f"Invalid version '{version}'. Expected semver format like 1.2.3.")
    return cleaned[1:] if cleaned.startswith("v") else cleaned


def _is_valid_wheel_name(name: str, *, release_version: str) -> bool:
    escaped_version = re.escape(release_version)
    pattern = (
        rf"^voicekey-{escaped_version}-(?:"
        rf"py3-none-any"
        rf"|cp\d{{2,3}}-cp\d{{2,3}}-(?:win_amd64|manylinux[^-]*_x86_64|linux_x86_64)"
        rf")\.whl$"
    )
    return re.match(pattern, name) is not None


__all__ = [
    "ReleasePolicyReport",
    "validate_architecture_scope",
    "validate_artifact_naming",
    "validate_compatibility_policy_documents",
    "validate_release_policy",
]
