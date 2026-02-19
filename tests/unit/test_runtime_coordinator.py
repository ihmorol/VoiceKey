"""Unit tests for app-layer wake/FSM runtime coordination (E02-S01)."""

from __future__ import annotations

from voicekey.app.main import RuntimeCoordinator
from voicekey.app.state_machine import AppState, ListeningMode, VoiceKeyStateMachine
from voicekey.audio.wake import WakeWindowController


class FakeClock:
    """Deterministic monotonic clock for timeout tests."""

    def __init__(self) -> None:
        self._now = 100.0

    def now(self) -> float:
        return self._now

    def tick(self, seconds: float) -> None:
        self._now += seconds


def test_wake_phrase_transitions_standby_to_listening_and_opens_window() -> None:
    coordinator = RuntimeCoordinator(
        state_machine=VoiceKeyStateMachine(
            mode=ListeningMode.WAKE_WORD,
            initial_state=AppState.STANDBY,
        ),
    )

    update = coordinator.on_transcript("VOICE   key")

    assert update.wake_detected is True
    assert update.transition is not None
    assert update.transition.from_state is AppState.STANDBY
    assert update.transition.to_state is AppState.LISTENING
    assert update.routed_text is None
    assert coordinator.state is AppState.LISTENING
    assert coordinator.is_wake_window_open is True


def test_non_wake_transcript_in_standby_does_not_transition_or_open_window() -> None:
    coordinator = RuntimeCoordinator(
        state_machine=VoiceKeyStateMachine(
            mode=ListeningMode.WAKE_WORD,
            initial_state=AppState.STANDBY,
        ),
    )

    update = coordinator.on_transcript("hello there")

    assert update.wake_detected is False
    assert update.transition is None
    assert update.routed_text is None
    assert coordinator.state is AppState.STANDBY
    assert coordinator.is_wake_window_open is False


def test_wake_window_timeout_transitions_listening_to_standby() -> None:
    clock = FakeClock()
    coordinator = RuntimeCoordinator(
        state_machine=VoiceKeyStateMachine(
            mode=ListeningMode.WAKE_WORD,
            initial_state=AppState.STANDBY,
        ),
        wake_window=WakeWindowController(timeout_seconds=5.0, time_provider=clock.now),
    )

    coordinator.on_transcript("voice key")
    clock.tick(5.01)
    update = coordinator.poll()

    assert update.transition is not None
    assert update.transition.from_state is AppState.LISTENING
    assert update.transition.to_state is AppState.STANDBY
    assert coordinator.state is AppState.STANDBY
    assert coordinator.is_wake_window_open is False


def test_activity_hooks_reset_wake_timeout() -> None:
    clock = FakeClock()
    coordinator = RuntimeCoordinator(
        state_machine=VoiceKeyStateMachine(
            mode=ListeningMode.WAKE_WORD,
            initial_state=AppState.STANDBY,
        ),
        wake_window=WakeWindowController(timeout_seconds=5.0, time_provider=clock.now),
    )

    coordinator.on_transcript("voice key")
    clock.tick(4.0)
    coordinator.on_activity()
    clock.tick(4.0)
    no_timeout = coordinator.poll()

    assert no_timeout.transition is None
    assert coordinator.state is AppState.LISTENING

    clock.tick(1.1)
    timeout_update = coordinator.poll()
    assert timeout_update.transition is not None
    assert timeout_update.transition.to_state is AppState.STANDBY


def test_transcript_activity_resets_wake_timeout() -> None:
    clock = FakeClock()
    coordinator = RuntimeCoordinator(
        state_machine=VoiceKeyStateMachine(
            mode=ListeningMode.WAKE_WORD,
            initial_state=AppState.STANDBY,
        ),
        wake_window=WakeWindowController(timeout_seconds=5.0, time_provider=clock.now),
    )

    coordinator.on_transcript("voice key")
    clock.tick(4.0)
    update = coordinator.on_transcript("dictation payload")
    clock.tick(4.0)
    no_timeout = coordinator.poll()

    assert update.transition is None
    assert no_timeout.transition is None
    assert coordinator.state is AppState.LISTENING

    clock.tick(1.1)
    timeout_update = coordinator.poll()
    assert timeout_update.transition is not None
    assert timeout_update.transition.to_state is AppState.STANDBY


def test_default_wake_window_timeout_is_five_seconds() -> None:
    coordinator = RuntimeCoordinator(
        state_machine=VoiceKeyStateMachine(
            mode=ListeningMode.WAKE_WORD,
            initial_state=AppState.STANDBY,
        ),
    )

    assert coordinator.wake_window_timeout_seconds == 5.0


def test_paused_resume_phrase_transitions_to_standby() -> None:
    coordinator = RuntimeCoordinator(
        state_machine=VoiceKeyStateMachine(
            mode=ListeningMode.WAKE_WORD,
            initial_state=AppState.PAUSED,
        ),
    )

    update = coordinator.on_transcript("resume voice key")

    assert update.transition is not None
    assert update.transition.from_state is AppState.PAUSED
    assert update.transition.to_state is AppState.STANDBY
    assert coordinator.state is AppState.STANDBY


def test_paused_stop_phrase_transitions_to_shutting_down() -> None:
    coordinator = RuntimeCoordinator(
        state_machine=VoiceKeyStateMachine(
            mode=ListeningMode.WAKE_WORD,
            initial_state=AppState.PAUSED,
        ),
    )

    update = coordinator.on_transcript("voice key stop")

    assert update.transition is not None
    assert update.transition.from_state is AppState.PAUSED
    assert update.transition.to_state is AppState.SHUTTING_DOWN
    assert coordinator.state is AppState.SHUTTING_DOWN
