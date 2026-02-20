"""Single-instance runtime guard with cross-platform lock backends."""

from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path
from typing import BinaryIO, Protocol


class DuplicateInstanceStartupError(RuntimeError):
    """Raised when another process already owns the runtime lock."""


class InstanceLockBackend(Protocol):
    """Backend contract for single-instance lock adapters."""

    def acquire(self, lock_id: str) -> bool:
        """Try to acquire lock ownership for lock_id."""

    def release(self, lock_id: str) -> None:
        """Release lock ownership for lock_id."""


class DeterministicLockBackend:
    """Process-local deterministic lock backend used for tests/fallback."""

    def __init__(self) -> None:
        self._owned: set[str] = set()

    def acquire(self, lock_id: str) -> bool:
        if lock_id in self._owned:
            return False
        self._owned.add(lock_id)
        return True

    def release(self, lock_id: str) -> None:
        self._owned.discard(lock_id)


class PosixFileLockBackend:
    """POSIX `flock`-based adapter for single-instance locking."""

    def __init__(self, base_lock_path: Path) -> None:
        self._base_lock_path = base_lock_path
        self._handles: dict[str, int] = {}

    def acquire(self, lock_id: str) -> bool:
        if lock_id in self._handles:
            return True

        import fcntl

        lock_path = _lock_path_for(self._base_lock_path, lock_id)
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)

        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            os.close(fd)
            return False

        os.ftruncate(fd, 0)
        os.write(fd, f"{os.getpid()}\n".encode("ascii"))
        os.fsync(fd)
        self._handles[lock_id] = fd
        return True

    def release(self, lock_id: str) -> None:
        fd = self._handles.pop(lock_id, None)
        if fd is None:
            return

        import fcntl

        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


class WindowsFileLockBackend:
    """Windows file-region lock adapter for single-instance safety."""

    def __init__(self, base_lock_path: Path) -> None:
        self._base_lock_path = base_lock_path
        self._handles: dict[str, BinaryIO] = {}

    def acquire(self, lock_id: str) -> bool:
        if lock_id in self._handles:
            return True

        import msvcrt

        lock_path = _lock_path_for(self._base_lock_path, lock_id)
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        handle = lock_path.open("a+b")
        handle.seek(0)
        if handle.read(1) == b"":
            handle.seek(0)
            handle.write(b"0")
            handle.flush()

        handle.seek(0)
        try:
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            handle.close()
            return False

        handle.seek(0)
        handle.truncate()
        handle.write(f"{os.getpid()}\n".encode("ascii"))
        handle.flush()
        self._handles[lock_id] = handle
        return True

    def release(self, lock_id: str) -> None:
        handle = self._handles.pop(lock_id, None)
        if handle is None:
            return

        import msvcrt

        try:
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        finally:
            handle.close()


def default_lock_backend(base_lock_path: Path, *, platform: str | None = None) -> InstanceLockBackend:
    """Return backend adapter for the current platform.

    Unknown platforms use deterministic fallback so tests remain stable.
    """

    platform_name = os.name if platform is None else platform
    if platform_name == "nt":
        return WindowsFileLockBackend(base_lock_path)
    if platform_name == "posix":
        return PosixFileLockBackend(base_lock_path)
    return DeterministicLockBackend()


class SingleInstanceGuard:
    """Runtime process guard that enforces a single active instance."""

    def __init__(
        self,
        *,
        lock_id: str = "voicekey",
        backend: InstanceLockBackend | None = None,
        base_lock_path: Path | None = None,
    ) -> None:
        self._lock_id = lock_id
        if base_lock_path is not None:
            self._base_lock_path = base_lock_path
        else:
            # Use a secure subdirectory within the temp directory
            secure_dir = _secure_lock_directory(Path(tempfile.gettempdir()))
            self._base_lock_path = secure_dir / "voicekey.runtime.lock"
        self._backend = backend or default_lock_backend(self._base_lock_path)
        self._acquired = False

    def acquire(self) -> None:
        """Acquire process lock, raising actionable error on duplicate start."""

        if self._acquired:
            return

        acquired = self._backend.acquire(self._lock_id)
        if not acquired:
            lock_path = _lock_path_for(self._base_lock_path, self._lock_id)
            raise DuplicateInstanceStartupError(
                "VoiceKey is already running and owns the runtime lock at "
                f"'{lock_path}'. Close the existing VoiceKey process, then retry startup."
            )
        self._acquired = True

    def release(self) -> None:
        """Release process lock if currently acquired by this guard."""

        if not self._acquired:
            return
        self._backend.release(self._lock_id)
        self._acquired = False

    def __enter__(self) -> SingleInstanceGuard:
        self.acquire()
        return self

    def __exit__(self, _exc_type: object, _exc: object, _tb: object) -> None:
        self.release()


def _secure_lock_directory(base_dir: Path) -> Path:
    """Create a secure lock directory with restricted permissions.

    Creates a 'voicekey-locks' subdirectory with mode 0o700 (owner-only access)
    to prevent symlink attacks and unauthorized access in world-writable temp dirs.
    """
    lock_dir = base_dir / "voicekey-locks"
    lock_dir.mkdir(parents=True, exist_ok=True)
    # Set restrictive permissions on the lock directory
    os.chmod(lock_dir, 0o700)
    return lock_dir


def _lock_path_for(base_lock_path: Path, lock_id: str) -> Path:
    normalized_lock_id = _normalize_lock_id(lock_id)
    suffix = base_lock_path.suffix
    stem = base_lock_path.name[: -len(suffix)] if suffix else base_lock_path.name
    lock_filename = f"{stem}.{normalized_lock_id}{suffix}" if normalized_lock_id else base_lock_path.name
    return base_lock_path.with_name(lock_filename)


def _normalize_lock_id(lock_id: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]", "_", lock_id)


__all__ = [
    "DeterministicLockBackend",
    "DuplicateInstanceStartupError",
    "InstanceLockBackend",
    "PosixFileLockBackend",
    "SingleInstanceGuard",
    "WindowsFileLockBackend",
    "default_lock_backend",
]
