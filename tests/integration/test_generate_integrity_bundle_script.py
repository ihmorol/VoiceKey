"""Integration tests for release integrity bundle generation script (E07-S04)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_generate_integrity_bundle_outputs_required_files(tmp_path: Path) -> None:
    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir()
    (artifacts_dir / "voicekey-0.1.0-py3-none-any.whl").write_bytes(b"wheel")
    (artifacts_dir / "voicekey-0.1.0-linux-x86_64.AppImage").write_bytes(b"appimage")

    output_dir = tmp_path / "integrity"
    project_root = Path(__file__).resolve().parents[2]
    script = project_root / "scripts" / "release" / "generate_integrity_bundle.py"

    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--artifacts-dir",
            str(artifacts_dir),
            "--output-dir",
            str(output_dir),
            "--commit-hash",
            "abc123",
            "--build-timestamp-utc",
            "2026-02-20T12:00:00Z",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0

    checksums = output_dir / "SHA256SUMS"
    sbom = output_dir / "sbom.cyclonedx.json"
    provenance = output_dir / "provenance.json"

    assert checksums.exists()
    assert sbom.exists()
    assert provenance.exists()
    assert "voicekey-0.1.0-linux-x86_64.AppImage" in checksums.read_text(encoding="utf-8")

    sbom_payload = json.loads(sbom.read_text(encoding="utf-8"))
    provenance_payload = json.loads(provenance.read_text(encoding="utf-8"))

    assert sbom_payload["bomFormat"] == "CycloneDX"
    assert provenance_payload["commit_hash"] == "abc123"
