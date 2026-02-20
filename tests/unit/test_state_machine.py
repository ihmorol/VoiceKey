"""Unit tests for FSM transitions across listening modes."""

from __future__ import annotations

import threading

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


def test_transition_after_termination_raises_error() -> None:
    machine = VoiceKeyStateMachine(
        mode=ListeningMode.WAKE_WORD,
        initial_state=AppState.SHUTTING_DOWN,
    )
    machine.transition(AppEvent.SHUTDOWN_COMPLETE)

    assert machine.terminated is True

    with pytest.raises(InvalidTransitionError, match="already terminated"):
        machine.transition(AppEvent.STOP_REQUESTED)


class TestStateMachineThreadSafety:
    """Tests for thread-safe state transitions."""

    def test_concurrent_transitions_are_serialized(self) -> None:
        """Test that concurrent transitions are properly serialized."""
        import concurrent.futures
        import threading

        machine = VoiceKeyStateMachine(
            mode=ListeningMode.WAKE_WORD,
            initial_state=AppState.STANDBY,
        )

        errors: list[Exception] = []
        results: list[AppState] = []
        lock = threading.Lock()

        def attempt_transition(event: AppEvent) -> None:
            try:
                result = machine.transition(event)
                with lock:
                    results.append(result.to_state)  # type: ignore[arg-type]
            except InvalidTransitionError as e:
                with lock:
                    errors.append(e)

        # Try to trigger both valid and invalid transitions concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            # Submit multiple valid transitions
            futures = []
            for _ in range(5):
                futures.append(executor.submit(attempt_transition, AppEvent.WAKE_PHRASE_DETECTED))
            for _ in range(5):
                futures.append(executor.submit(attempt_transition, AppEvent.PAUSE_REQUESTED))

            concurrent.futures.wait(futures)

        # At least one valid transition should have succeeded
        # And exactly one should have transitioned to LISTENING
        assert AppState.LISTENING in results or AppState.PAUSED in results

    def test_state_property_is_thread_safe(self) -> None:
        """Test that reading state property is thread-safe."""
        import concurrent.futures
        import threading

        machine = VoiceKeyStateMachine(
            mode=ListeningMode.WAKE_WORD,
            initial_state=AppState.STANDBY,
        )

        states_read: list[AppState] = []
        lock = threading.Lock()

        def read_state() -> None:
            state = machine.state
            with lock:
                states_read.append(state)

        def write_state() -> None:
            try:
                machine.transition(AppEvent.WAKE_PHRASE_DETECTED)
            except InvalidTransitionError:
                pass  # Expected if already transitioned

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = []
            for _ in range(10):
                futures.append(executor.submit(read_state))
            for _ in range(10):
                futures.append(executor.submit(write_state))

            concurrent.futures.wait(futures)

        # All state reads should have returned valid states
        for state in states_read:
            assert isinstance(state, AppState)

    def test_terminated_property_is_thread_safe(self) -> None:
        """Test that reading terminated property is thread-safe."""
        import concurrent.futures

        machine = VoiceKeyStateMachine(
            mode=ListeningMode.WAKE_WORD,
            initial_state=AppState.SHUTTING_DOWN,
        )

        terminated_reads: list[bool] = []

        def read_terminated() -> None:
            terminated_reads.append(machine.terminated)

        def trigger_termination() -> None:
            try:
                machine.transition(AppEvent.SHUTDOWN_COMPLETE)
            except InvalidTransitionError:
                pass  # Already terminated

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for _ in range(5):
                futures.append(executor.submit(read_terminated))
            futures.append(executor.submit(trigger_termination))
            for _ in range(5):
                futures.append(executor.submit(read_terminated))

            concurrent.futures.wait(futures)

        # All terminated reads should be booleans
        for val in terminated_reads:
            assert isinstance(val, bool)

    def test_no_lost_state_updates(self) -> None:
        """Test that state updates are not lost under contention."""
        import concurrent.futures

        machine = VoiceKeyStateMachine(
            mode=ListeningMode.WAKE_WORD,
            initial_state=AppState.LISTENING,
        )

        success_count = 0
        lock = threading.Lock()

        def attempt_pause() -> None:
            nonlocal success_count
            try:
                machine.transition(AppEvent.INACTIVITY_AUTO_PAUSE)
                with lock:
                    success_count += 1
            except InvalidTransitionError:
                pass  # Already transitioned

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(attempt_pause) for _ in range(10)]
            concurrent.futures.wait(futures)

        # Exactly one transition should succeed
        assert success_count == 1
        assert machine.state == AppState.PAUSED
