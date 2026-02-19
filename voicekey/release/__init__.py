"""Release packaging helpers."""

from voicekey.release.windows_artifacts import (
    build_signtool_command,
    build_windows_artifact_name,
    create_portable_zip,
    normalize_version as normalize_windows_version,
    prepare_installer_artifact,
)
from voicekey.release.linux_artifacts import (
    build_appimage_smoke_command,
    build_linux_artifact_name,
    normalize_version as normalize_linux_version,
    prepare_appimage_artifact,
)
from voicekey.release.integrity import (
    build_cyclonedx_sbom,
    build_provenance_manifest,
    build_sha256sums,
)
from voicekey.release.signing import (
    build_gpg_detached_sign_command,
    build_verify_tag_signature_command,
)
from voicekey.release.policy import (
    ReleasePolicyReport,
    validate_architecture_scope,
    validate_artifact_naming,
    validate_compatibility_policy_documents,
    validate_release_policy,
)
from voicekey.release.changelog import extract_release_notes

__all__ = [
    "build_appimage_smoke_command",
    "build_cyclonedx_sbom",
    "build_gpg_detached_sign_command",
    "build_linux_artifact_name",
    "build_provenance_manifest",
    "build_signtool_command",
    "build_sha256sums",
    "build_verify_tag_signature_command",
    "build_windows_artifact_name",
    "create_portable_zip",
    "normalize_linux_version",
    "normalize_windows_version",
    "prepare_appimage_artifact",
    "prepare_installer_artifact",
    "ReleasePolicyReport",
    "extract_release_notes",
    "validate_architecture_scope",
    "validate_artifact_naming",
    "validate_compatibility_policy_documents",
    "validate_release_policy",
]
