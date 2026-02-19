"""Unit tests for single-instance runtime locking safety."""

from __future__ import annotations

from pathlib import Path

import pytest

from voicekey.app.single_instance import (
    DeterministicLockBackend,
    DuplicateInstanceStartupError,
    SingleInstanceGuard,
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
