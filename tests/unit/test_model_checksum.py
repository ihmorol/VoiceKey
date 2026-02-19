"""Unit tests for model checksum helpers."""

from __future__ import annotations

from voicekey.models.checksum import sha256_file, verify_sha256


def test_sha256_file_and_verify_sha256(tmp_path) -> None:
    payload = b"voicekey-model-bytes"
    model_file = tmp_path / "model.bin"
    model_file.write_bytes(payload)

    digest = sha256_file(model_file)

    assert len(digest) == 64
    assert verify_sha256(model_file, expected_sha256=digest)
    assert not verify_sha256(
        model_file,
        expected_sha256="0" * 64,
    )
