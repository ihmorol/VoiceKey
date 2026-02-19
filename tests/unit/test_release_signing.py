"""Unit tests for release signing helpers (E07-S04)."""

from __future__ import annotations

from pathlib import Path

from voicekey.release.signing import (
    build_gpg_detached_sign_command,
    build_verify_tag_signature_command,
)


def test_build_gpg_detached_sign_command_uses_expected_defaults(tmp_path: Path) -> None:
    checksums = tmp_path / "SHA256SUMS"
    signature = tmp_path / "SHA256SUMS.sig"

    command = build_gpg_detached_sign_command(
        input_file=checksums,
        output_signature_file=signature,
    )

    assert command == [
        "gpg",
        "--batch",
        "--yes",
        "--armor",
        "--detach-sign",
        "--output",
        str(signature),
        str(checksums),
    ]


def test_build_gpg_detached_sign_command_supports_key_id(tmp_path: Path) -> None:
    checksums = tmp_path / "SHA256SUMS"
    signature = tmp_path / "SHA256SUMS.sig"

    command = build_gpg_detached_sign_command(
        input_file=checksums,
        output_signature_file=signature,
        key_id="DEADBEEF",
    )

    assert "--local-user" in command
    assert "DEADBEEF" in command


def test_build_verify_tag_signature_command_is_deterministic() -> None:
    command = build_verify_tag_signature_command("v1.2.3")

    assert command == ["git", "tag", "-v", "v1.2.3"]
