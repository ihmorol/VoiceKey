"""Shutdown-safe dispatch queue draining with timeout guard."""

from __future__ import annotations

from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from threading import Lock
from time import monotonic
from typing import Generic, TypeVar

T = TypeVar("T")


class DispatchQueueClosedError(RuntimeError):
    """Raised when enqueue is attempted after shutdown has started."""


class DispatchQueue(Generic[T]):
    """Thread-safe FIFO queue that can be closed during shutdown."""

    def __init__(self) -> None:
        self._items: deque[T] = deque()
        self._lock = Lock()
        self._closed = False

    @property
    def pending_count(self) -> int:
        with self._lock:
            return len(self._items)

    def enqueue(self, item: T) -> None:
        with self._lock:
            if self._closed:
                raise DispatchQueueClosedError(
                    "dispatch queue is closed for shutdown; new items are rejected"
                )
            self._items.append(item)

    def close(self) -> None:
        with self._lock:
            self._closed = True

    def pop_next(self) -> T | None:
        with self._lock:
            if not self._items:
                return None
            return self._items.popleft()

    def discard_pending(self) -> int:
        with self._lock:
            discarded_count = len(self._items)
            self._items.clear()
            return discarded_count


@dataclass(frozen=True)
class ShutdownDrainResult:
    """Outcome of shutdown drain policy execution."""

    drained_count: int
    discarded_count: int
    timed_out: bool
    dispatch_error: str | None = None


class ShutdownQueueDrainer(Generic[T]):
    """Drain queue during shutdown, then safely discard leftover items."""

    def __init__(
        self,
        *,
        queue: DispatchQueue[T],
        timeout_seconds: float,
        monotonic: Callable[[], float] = monotonic,
    ) -> None:
        if timeout_seconds < 0:
            raise ValueError("timeout_seconds must be non-negative")
        self._queue = queue
        self._timeout_seconds = timeout_seconds
        self._monotonic = monotonic

    def shutdown(self, dispatcher: Callable[[T], None]) -> ShutdownDrainResult:
        """Close queue, drain within timeout, then safely discard pending work."""

        self._queue.close()
        deadline = self._monotonic() + self._timeout_seconds
        drained_count = 0
        timed_out = False
        dispatch_error: str | None = None

        while True:
            if self._monotonic() >= deadline:
                timed_out = self._queue.pending_count > 0
                break

            item = self._queue.pop_next()
            if item is None:
                break

            try:
                dispatcher(item)
            except Exception as exc:  # pragma: no cover - explicit fail-safe
                dispatch_error = str(exc)
                break

            drained_count += 1

        discarded_count = self._queue.discard_pending()
        return ShutdownDrainResult(
            drained_count=drained_count,
            discarded_count=discarded_count,
            timed_out=timed_out,
            dispatch_error=dispatch_error,
        )


__all__ = [
    "DispatchQueue",
    "DispatchQueueClosedError",
    "ShutdownDrainResult",
    "ShutdownQueueDrainer",
]
