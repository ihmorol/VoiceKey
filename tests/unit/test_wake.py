"""Unit tests for wake phrase detection and wake window controls."""

from __future__ import annotations

from voicekey.audio.wake import WakePhraseDetector, WakeWindowController


class FakeClock:
    """Deterministic monotonic clock for timeout tests."""

    def __init__(self) -> None:
        self._now = 100.0

    def now(self) -> float:
        return self._now

    def tick(self, seconds: float) -> None:
        self._now += seconds


def test_wake_detector_defaults_to_voice_key() -> None:
    detector = WakePhraseDetector()
    assert detector.wake_phrase == "voice key"


def test_wake_detector_is_case_insensitive() -> None:
    detector = WakePhraseDetector()
    result = detector.detect("Please VOICE    KEY start listening")
    assert result.matched is True
    assert result.normalized_transcript == "please voice key start listening"


def test_wake_detector_supports_configured_phrase() -> None:
    detector = WakePhraseDetector("hello keyboard")
    assert detector.detect("hello keyboard now").matched is True
    assert detector.detect("voice key now").matched is False


def test_wake_detector_empty_phrase_rejected() -> None:
    try:
        WakePhraseDetector("   ")
        assert False, "expected ValueError"
    except ValueError:
        assert True


def test_wake_window_default_timeout_is_five_seconds() -> None:
    controller = WakeWindowController()
    assert controller.timeout_seconds == 5.0


def test_wake_window_expires_after_timeout() -> None:
    clock = FakeClock()
    controller = WakeWindowController(timeout_seconds=5.0, time_provider=clock.now)
    controller.open_window()

    assert controller.is_open() is True
    clock.tick(5.01)

    assert controller.poll_timeout() is True
    assert controller.is_open() is False


def test_wake_window_activity_resets_timeout() -> None:
    clock = FakeClock()
    controller = WakeWindowController(timeout_seconds=5.0, time_provider=clock.now)
    controller.open_window()

    clock.tick(4.0)
    controller.on_activity()
    clock.tick(4.0)

    assert controller.is_open() is True
    assert controller.poll_timeout() is False

    clock.tick(1.1)
    assert controller.poll_timeout() is True


def test_wake_window_invalid_timeout_rejected() -> None:
    try:
        WakeWindowController(timeout_seconds=0)
        assert False, "expected ValueError"
    except ValueError:
        assert True
