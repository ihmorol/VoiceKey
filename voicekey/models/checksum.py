"""Checksum helpers for downloaded model artifacts."""

from __future__ import annotations

import hashlib
from pathlib import Path


def sha256_file(path: Path) -> str:
    """Return lowercase SHA-256 digest for the file at ``path``."""
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def verify_sha256(path: Path, *, expected_sha256: str) -> bool:
    """Check whether ``path`` matches the expected SHA-256 digest."""
    normalized = expected_sha256.strip().lower()
    return sha256_file(path) == normalized


__all__ = ["sha256_file", "verify_sha256"]
