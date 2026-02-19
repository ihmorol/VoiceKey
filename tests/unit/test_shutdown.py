"""Unit tests for shutdown queue-drain policy safety."""

from __future__ import annotations

import pytest

from voicekey.app.shutdown import DispatchQueue, DispatchQueueClosedError, ShutdownQueueDrainer


class FakeClock:
    """Deterministic clock for timeout behavior."""

    def __init__(self) -> None:
        self._now = 0.0

    def now(self) -> float:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now += seconds


def test_shutdown_drains_queue_within_timeout() -> None:
    queue = DispatchQueue[str]()
    queue.enqueue("hello")
    queue.enqueue("world")
    dispatched: list[str] = []

    drainer = ShutdownQueueDrainer(queue=queue, timeout_seconds=1.0)
    result = drainer.shutdown(dispatched.append)

    assert result.drained_count == 2
    assert result.discarded_count == 0
    assert result.timed_out is False
    assert dispatched == ["hello", "world"]
    assert queue.pending_count == 0


def test_shutdown_timeout_discards_remaining_without_partial_dispatch() -> None:
    clock = FakeClock()
    queue = DispatchQueue[str]()
    queue.enqueue("a")
    queue.enqueue("b")
    queue.enqueue("c")
    dispatched: list[str] = []

    def slow_dispatch(item: str) -> None:
        dispatched.append(item)
        clock.advance(0.2)

    drainer = ShutdownQueueDrainer(
        queue=queue,
        timeout_seconds=0.35,
        monotonic=clock.now,
    )
    result = drainer.shutdown(slow_dispatch)

    assert result.drained_count == 2
    assert result.discarded_count == 1
    assert result.timed_out is True
    assert dispatched == ["a", "b"]
    assert queue.pending_count == 0


def test_shutdown_rejects_new_enqueue_race_after_close() -> None:
    queue = DispatchQueue[str]()
    queue.enqueue("initial")

    def dispatch_and_race(_item: str) -> None:
        with pytest.raises(DispatchQueueClosedError):
            queue.enqueue("late item")

    drainer = ShutdownQueueDrainer(queue=queue, timeout_seconds=1.0)
    result = drainer.shutdown(dispatch_and_race)

    assert result.drained_count == 1
    assert result.discarded_count == 0
    assert result.timed_out is False
    assert queue.pending_count == 0
