"""Unit tests for release integrity bundle helpers (E07-S04)."""

from __future__ import annotations

import hashlib
from pathlib import Path

from voicekey.release.integrity import (
    build_cyclonedx_sbom,
    build_provenance_manifest,
    build_sha256sums,
)


def test_build_sha256sums_sorts_and_formats_entries(tmp_path: Path) -> None:
    b_file = tmp_path / "b.bin"
    a_file = tmp_path / "a.bin"
    b_file.write_bytes(b"bbb")
    a_file.write_bytes(b"aaa")

    checksum_text = build_sha256sums([b_file, a_file])

    a_hash = hashlib.sha256(b"aaa").hexdigest()
    b_hash = hashlib.sha256(b"bbb").hexdigest()
    assert checksum_text.splitlines() == [
        f"{a_hash}  a.bin",
        f"{b_hash}  b.bin",
    ]


def test_build_sha256sums_excludes_integrity_sidecar_files(tmp_path: Path) -> None:
    payload = tmp_path / "voicekey-0.1.0-linux-x86_64.AppImage"
    sums = tmp_path / "SHA256SUMS"
    signature = tmp_path / "SHA256SUMS.sig"
    sbom = tmp_path / "sbom.cyclonedx.json"
    provenance = tmp_path / "provenance.json"

    payload.write_bytes(b"payload")
    sums.write_text("ignore", encoding="utf-8")
    signature.write_text("ignore", encoding="utf-8")
    sbom.write_text("ignore", encoding="utf-8")
    provenance.write_text("ignore", encoding="utf-8")

    checksum_text = build_sha256sums([payload, sums, signature, sbom, provenance])

    assert checksum_text.count("\n") == 0
    assert "voicekey-0.1.0-linux-x86_64.AppImage" in checksum_text


def test_build_cyclonedx_sbom_includes_required_top_level_fields(tmp_path: Path) -> None:
    artifact = tmp_path / "voicekey-0.1.0-linux-x86_64.AppImage"
    artifact.write_bytes(b"artifact")

    sbom = build_cyclonedx_sbom(
        artifact_paths=[artifact],
        release_version="0.1.0",
    )

    assert sbom["bomFormat"] == "CycloneDX"
    assert sbom["specVersion"] == "1.5"
    assert sbom["metadata"]["component"]["name"] == "voicekey"
    assert sbom["components"][0]["name"] == artifact.name


def test_build_provenance_manifest_includes_commit_and_toolchain(tmp_path: Path) -> None:
    artifact = tmp_path / "voicekey-0.1.0-py3-none-any.whl"
    artifact.write_bytes(b"wheel")

    provenance = build_provenance_manifest(
        artifact_paths=[artifact],
        commit_hash="abc123",
        build_timestamp_utc="2026-02-20T12:00:00Z",
        toolchain={"python": "3.12", "builder": "github-actions"},
    )

    assert provenance["commit_hash"] == "abc123"
    assert provenance["build_timestamp_utc"] == "2026-02-20T12:00:00Z"
    assert provenance["toolchain"]["python"] == "3.12"
    assert provenance["artifacts"][0]["name"] == artifact.name
