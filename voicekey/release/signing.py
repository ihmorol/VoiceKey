"""Release signing command helpers."""

from __future__ import annotations

from pathlib import Path


def build_gpg_detached_sign_command(
    *,
    input_file: Path,
    output_signature_file: Path,
    key_id: str | None = None,
) -> list[str]:
    """Build deterministic GPG detached-signature command."""
    command = [
        "gpg",
        "--batch",
        "--yes",
        "--armor",
        "--detach-sign",
        "--output",
        str(output_signature_file),
    ]
    if key_id is not None and key_id.strip():
        command.extend(["--local-user", key_id.strip()])
    command.append(str(input_file))
    return command


def build_verify_tag_signature_command(tag_name: str) -> list[str]:
    """Build deterministic git tag signature verification command."""
    return ["git", "tag", "-v", tag_name]


__all__ = [
    "build_gpg_detached_sign_command",
    "build_verify_tag_signature_command",
]
