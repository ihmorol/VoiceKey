"""Unit tests for inactivity watchdog timer behavior."""

from __future__ import annotations

import pytest

from voicekey.app.state_machine import ListeningMode
from voicekey.app.watchdog import (
    InactivityWatchdog,
    WatchdogTelemetryCounters,
    WatchdogTimerConfig,
    WatchdogTimeoutType,
)


class FakeClock:
    """Deterministic monotonic clock for watchdog tests."""

    def __init__(self) -> None:
        self._now = 100.0

    def now(self) -> float:
        return self._now

    def tick(self, seconds: float) -> None:
        self._now += seconds


def test_watchdog_uses_required_default_timeouts() -> None:
    watchdog = InactivityWatchdog()

    assert watchdog.config.wake_window_timeout_seconds == 5.0
    assert watchdog.config.inactivity_auto_pause_seconds == 30.0


def test_watchdog_rejects_non_positive_timeouts() -> None:
    with pytest.raises(ValueError, match="wake_window_timeout_seconds"):
        InactivityWatchdog(config=WatchdogTimerConfig(wake_window_timeout_seconds=0))

    with pytest.raises(ValueError, match="inactivity_auto_pause_seconds"):
        InactivityWatchdog(config=WatchdogTimerConfig(inactivity_auto_pause_seconds=0))


def test_wake_mode_emits_wake_window_timeout() -> None:
    clock = FakeClock()
    watchdog = InactivityWatchdog(clock=clock.now)
    watchdog.arm_for_mode(ListeningMode.WAKE_WORD)

    clock.tick(5.01)
    event = watchdog.poll_timeout()

    assert event is not None
    assert event.timeout_type is WatchdogTimeoutType.WAKE_WINDOW_TIMEOUT
    assert watchdog.poll_timeout() is None


def test_toggle_mode_emits_inactivity_auto_pause() -> None:
    clock = FakeClock()
    watchdog = InactivityWatchdog(clock=clock.now)
    watchdog.arm_for_mode(ListeningMode.TOGGLE)

    clock.tick(30.01)
    event = watchdog.poll_timeout()

    assert event is not None
    assert event.timeout_type is WatchdogTimeoutType.INACTIVITY_AUTO_PAUSE


def test_continuous_mode_emits_inactivity_auto_pause() -> None:
    clock = FakeClock()
    watchdog = InactivityWatchdog(clock=clock.now)
    watchdog.arm_for_mode(ListeningMode.CONTINUOUS)

    clock.tick(30.01)
    event = watchdog.poll_timeout()

    assert event is not None
    assert event.timeout_type is WatchdogTimeoutType.INACTIVITY_AUTO_PAUSE


def test_vad_activity_resets_timeout() -> None:
    clock = FakeClock()
    watchdog = InactivityWatchdog(clock=clock.now)
    watchdog.arm_for_mode(ListeningMode.TOGGLE)

    clock.tick(20.0)
    watchdog.on_vad_activity()
    clock.tick(15.0)

    assert watchdog.poll_timeout() is None

    clock.tick(15.1)
    event = watchdog.poll_timeout()
    assert event is not None
    assert event.timeout_type is WatchdogTimeoutType.INACTIVITY_AUTO_PAUSE


def test_transcript_activity_resets_timeout() -> None:
    clock = FakeClock()
    watchdog = InactivityWatchdog(clock=clock.now)
    watchdog.arm_for_mode(ListeningMode.WAKE_WORD)

    clock.tick(4.0)
    watchdog.on_transcript_activity()
    clock.tick(4.0)

    assert watchdog.poll_timeout() is None

    clock.tick(1.1)
    event = watchdog.poll_timeout()
    assert event is not None
    assert event.timeout_type is WatchdogTimeoutType.WAKE_WINDOW_TIMEOUT


def test_poll_timeout_returns_none_when_disarmed() -> None:
    clock = FakeClock()
    watchdog = InactivityWatchdog(clock=clock.now)

    clock.tick(100.0)

    assert watchdog.poll_timeout() is None


def test_timeout_telemetry_counters_increment() -> None:
    clock = FakeClock()
    watchdog = InactivityWatchdog(clock=clock.now)

    watchdog.arm_for_mode(ListeningMode.WAKE_WORD)
    clock.tick(5.1)
    wake_event = watchdog.poll_timeout()

    watchdog.arm_for_mode(ListeningMode.CONTINUOUS)
    clock.tick(30.1)
    inactivity_event = watchdog.poll_timeout()

    counters = watchdog.telemetry_counters()

    assert wake_event is not None
    assert inactivity_event is not None
    assert counters == WatchdogTelemetryCounters(
        wake_window_timeouts=1,
        inactivity_auto_pauses=1,
    )
