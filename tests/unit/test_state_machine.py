"""Unit tests for FSM transitions across listening modes."""

from __future__ import annotations

import pytest

from voicekey.app.state_machine import (
    AppEvent,
    AppState,
    InvalidTransitionError,
    ListeningMode,
    ModeHooks,
    VoiceKeyStateMachine,
)


@pytest.mark.parametrize(
    ("mode", "event"),
    [
        (ListeningMode.WAKE_WORD, AppEvent.WAKE_PHRASE_DETECTED),
        (ListeningMode.TOGGLE, AppEvent.TOGGLE_LISTENING_ON),
        (ListeningMode.CONTINUOUS, AppEvent.CONTINUOUS_START),
    ],
)
def test_mode_specific_standby_to_listening_transitions(mode: ListeningMode, event: AppEvent) -> None:
    machine = VoiceKeyStateMachine(mode=mode, initial_state=AppState.STANDBY)

    transition = machine.transition(event)

    assert transition.from_state is AppState.STANDBY
    assert transition.to_state is AppState.LISTENING
    assert machine.state is AppState.LISTENING


@pytest.mark.parametrize(
    ("mode", "event"),
    [
        (ListeningMode.WAKE_WORD, AppEvent.TOGGLE_LISTENING_ON),
        (ListeningMode.TOGGLE, AppEvent.WAKE_PHRASE_DETECTED),
        (ListeningMode.CONTINUOUS, AppEvent.WAKE_PHRASE_DETECTED),
    ],
)
def test_mode_specific_invalid_standby_transition_raises(mode: ListeningMode, event: AppEvent) -> None:
    machine = VoiceKeyStateMachine(mode=mode, initial_state=AppState.STANDBY)

    with pytest.raises(InvalidTransitionError):
        machine.transition(event)


@pytest.mark.parametrize(
    ("initial_state", "event", "expected_state"),
    [
        (AppState.INITIALIZING, AppEvent.INITIALIZATION_SUCCEEDED, AppState.STANDBY),
        (AppState.INITIALIZING, AppEvent.INITIALIZATION_FAILED, AppState.ERROR),
        (AppState.LISTENING, AppEvent.SPEECH_FRAME_RECEIVED, AppState.PROCESSING),
        (AppState.PROCESSING, AppEvent.PARTIAL_HANDLED, AppState.LISTENING),
        (AppState.PROCESSING, AppEvent.FINAL_HANDLED, AppState.LISTENING),
        (AppState.LISTENING, AppEvent.WAKE_WINDOW_TIMEOUT, AppState.STANDBY),
        (AppState.LISTENING, AppEvent.INACTIVITY_AUTO_PAUSE, AppState.PAUSED),
        (AppState.LISTENING, AppEvent.STOP_REQUESTED, AppState.SHUTTING_DOWN),
        (AppState.PROCESSING, AppEvent.STOP_REQUESTED, AppState.SHUTTING_DOWN),
        (AppState.STANDBY, AppEvent.PAUSE_REQUESTED, AppState.PAUSED),
        (AppState.PAUSED, AppEvent.RESUME_REQUESTED, AppState.STANDBY),
        (AppState.STANDBY, AppEvent.STOP_REQUESTED, AppState.SHUTTING_DOWN),
        (AppState.PAUSED, AppEvent.STOP_REQUESTED, AppState.SHUTTING_DOWN),
        (AppState.ERROR, AppEvent.STOP_REQUESTED, AppState.SHUTTING_DOWN),
    ],
)
def test_common_transitions(initial_state: AppState, event: AppEvent, expected_state: AppState) -> None:
    machine = VoiceKeyStateMachine(mode=ListeningMode.WAKE_WORD, initial_state=initial_state)

    transition = machine.transition(event)

    assert transition.from_state is initial_state
    assert transition.to_state is expected_state
    assert machine.state is expected_state


def test_shutdown_complete_sets_terminal_marker() -> None:
    machine = VoiceKeyStateMachine(mode=ListeningMode.WAKE_WORD, initial_state=AppState.SHUTTING_DOWN)

    transition = machine.transition(AppEvent.SHUTDOWN_COMPLETE)

    assert transition.from_state is AppState.SHUTTING_DOWN
    assert transition.to_state is None
    assert transition.terminal is True
    assert machine.state is AppState.SHUTTING_DOWN
    assert machine.terminated is True


def test_invalid_transition_error_has_context() -> None:
    machine = VoiceKeyStateMachine(mode=ListeningMode.WAKE_WORD, initial_state=AppState.PAUSED)

    with pytest.raises(InvalidTransitionError, match="PAUSED"):
        machine.transition(AppEvent.SPEECH_FRAME_RECEIVED)


def test_mode_hooks_called_on_mode_entry_and_shutdown_exit() -> None:
    class RecorderHooks(ModeHooks):
        def __init__(self) -> None:
            self.events: list[tuple[str, ListeningMode]] = []

        def on_mode_enter(self, mode: ListeningMode) -> None:
            self.events.append(("enter", mode))

        def on_mode_exit(self, mode: ListeningMode) -> None:
            self.events.append(("exit", mode))

    hooks = RecorderHooks()
    machine = VoiceKeyStateMachine(
        mode=ListeningMode.TOGGLE,
        initial_state=AppState.STANDBY,
        mode_hooks=hooks,
    )

    machine.transition(AppEvent.STOP_REQUESTED)
    machine.transition(AppEvent.SHUTDOWN_COMPLETE)

    assert hooks.events == [
        ("enter", ListeningMode.TOGGLE),
        ("exit", ListeningMode.TOGGLE),
    ]
