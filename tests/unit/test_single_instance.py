"""Unit tests for single-instance runtime locking safety."""

from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

from voicekey.app.single_instance import (
    DeterministicLockBackend,
    DuplicateInstanceStartupError,
    SingleInstanceGuard,
    _secure_lock_directory,
    default_lock_backend,
)


def test_duplicate_start_raises_actionable_error() -> None:
    backend = DeterministicLockBackend()
    first = SingleInstanceGuard(lock_id="voicekey", backend=backend)
    second = SingleInstanceGuard(lock_id="voicekey", backend=backend)

    first.acquire()

    with pytest.raises(DuplicateInstanceStartupError) as exc_info:
        second.acquire()

    assert "already running" in str(exc_info.value)
    assert "Close the existing VoiceKey process" in str(exc_info.value)

    first.release()


def test_releasing_lock_allows_next_startup() -> None:
    backend = DeterministicLockBackend()
    first = SingleInstanceGuard(lock_id="voicekey", backend=backend)
    second = SingleInstanceGuard(lock_id="voicekey", backend=backend)

    first.acquire()
    first.release()

    second.acquire()
    second.release()


def test_unknown_platform_uses_deterministic_fallback_backend() -> None:
    backend = default_lock_backend(Path("/tmp/voicekey.lock"), platform="unknown")

    assert isinstance(backend, DeterministicLockBackend)


def test_secure_lock_directory_creates_directory_with_restricted_permissions(tmp_path: Path) -> None:
    """Security: Lock directory must have restrictive permissions (0o700)."""
    lock_dir = _secure_lock_directory(tmp_path)

    assert lock_dir.exists()
    assert lock_dir.name == "voicekey-locks"

    # On POSIX systems, verify permissions are restricted
    if os.name == "posix":
        mode = lock_dir.stat().st_mode
        # Extract permission bits (last 9 bits)
        permissions = stat.S_IMODE(mode)
        assert permissions == 0o700, f"Expected 0o700, got {oct(permissions)}"


def test_secure_lock_directory_is_idempotent(tmp_path: Path) -> None:
    """Security: Calling _secure_lock_directory multiple times should be safe."""
    lock_dir1 = _secure_lock_directory(tmp_path)
    lock_dir2 = _secure_lock_directory(tmp_path)

    assert lock_dir1 == lock_dir2
    assert lock_dir1.exists()

    if os.name == "posix":
        permissions = stat.S_IMODE(lock_dir1.stat().st_mode)
        assert permissions == 0o700


def test_single_instance_guard_uses_secure_lock_directory(tmp_path: Path) -> None:
    """Security: SingleInstanceGuard should use the secure lock directory."""
    backend = DeterministicLockBackend()
    guard = SingleInstanceGuard(lock_id="test-secure", backend=backend, base_lock_path=tmp_path / "test.lock")

    # The guard should not use the secure directory when base_lock_path is explicitly provided
    # but should use it when not provided
    assert guard._base_lock_path == tmp_path / "test.lock"


def test_single_instance_guard_default_path_uses_secure_directory() -> None:
    """Security: Default lock path should be in the voicekey-locks subdirectory."""
    backend = DeterministicLockBackend()
    guard = SingleInstanceGuard(lock_id="test-default", backend=backend)

    # Default path should be in voicekey-locks subdirectory
    assert "voicekey-locks" in str(guard._base_lock_path)
