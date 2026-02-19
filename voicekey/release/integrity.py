"""Release integrity bundle helpers."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


_INTEGRITY_SIDECAR_NAMES: tuple[str, ...] = (
    "SHA256SUMS",
    "SHA256SUMS.sig",
    "sbom.cyclonedx.json",
    "provenance.json",
)


def build_sha256sums(artifact_paths: list[Path]) -> str:
    """Build deterministic SHA256SUMS file content from artifact paths."""
    included = [
        path for path in artifact_paths if path.name not in _INTEGRITY_SIDECAR_NAMES and path.is_file()
    ]
    lines = [f"{_sha256_for_file(path)}  {path.name}" for path in sorted(included, key=lambda p: p.name)]
    return "\n".join(lines)


def build_cyclonedx_sbom(*, artifact_paths: list[Path], release_version: str) -> dict[str, Any]:
    """Build minimal CycloneDX JSON structure for release artifact set."""
    timestamp = datetime.now(tz=UTC).isoformat().replace("+00:00", "Z")
    components = []
    for path in sorted(artifact_paths, key=lambda p: p.name):
        if not path.is_file():
            continue
        components.append(
            {
                "type": "file",
                "name": path.name,
                "hashes": [
                    {
                        "alg": "SHA-256",
                        "content": _sha256_for_file(path),
                    }
                ],
            }
        )

    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "version": 1,
        "metadata": {
            "timestamp": timestamp,
            "component": {
                "type": "application",
                "name": "voicekey",
                "version": release_version,
            },
        },
        "components": components,
    }


def build_provenance_manifest(
    *,
    artifact_paths: list[Path],
    commit_hash: str,
    build_timestamp_utc: str,
    toolchain: dict[str, str],
) -> dict[str, Any]:
    """Build deterministic provenance metadata for release artifact set."""
    artifacts = []
    for path in sorted(artifact_paths, key=lambda p: p.name):
        if not path.is_file():
            continue
        artifacts.append(
            {
                "name": path.name,
                "sha256": _sha256_for_file(path),
            }
        )

    return {
        "commit_hash": commit_hash,
        "build_timestamp_utc": build_timestamp_utc,
        "toolchain": dict(sorted(toolchain.items())),
        "artifacts": artifacts,
    }


def _sha256_for_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


__all__ = [
    "build_cyclonedx_sbom",
    "build_provenance_manifest",
    "build_sha256sums",
]
