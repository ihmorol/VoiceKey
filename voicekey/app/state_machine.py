"""State machine for VoiceKey application lifecycle."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from enum import Enum


class AppState(str, Enum):
    """Runtime lifecycle states."""

    INITIALIZING = "INITIALIZING"
    STANDBY = "STANDBY"
    LISTENING = "LISTENING"
    PROCESSING = "PROCESSING"
    PAUSED = "PAUSED"
    SHUTTING_DOWN = "SHUTTING_DOWN"
    ERROR = "ERROR"


class ListeningMode(str, Enum):
    """Supported listening modes."""

    WAKE_WORD = "wake_word"
    TOGGLE = "toggle"
    CONTINUOUS = "continuous"


class AppEvent(str, Enum):
    """Events that can drive state transitions."""

    INITIALIZATION_SUCCEEDED = "initialization_succeeded"
    INITIALIZATION_FAILED = "initialization_failed"

    WAKE_PHRASE_DETECTED = "wake_phrase_detected"
    TOGGLE_LISTENING_ON = "toggle_listening_on"
    CONTINUOUS_START = "continuous_start"

    SPEECH_FRAME_RECEIVED = "speech_frame_received"
    PARTIAL_HANDLED = "partial_handled"
    FINAL_HANDLED = "final_handled"

    WAKE_WINDOW_TIMEOUT = "wake_window_timeout"
    INACTIVITY_AUTO_PAUSE = "inactivity_auto_pause"

    PAUSE_REQUESTED = "pause_requested"
    RESUME_REQUESTED = "resume_requested"
    STOP_REQUESTED = "stop_requested"

    SHUTDOWN_COMPLETE = "shutdown_complete"


class InvalidTransitionError(ValueError):
    """Raised when a state/event pair is not allowed."""


class ModeHooks:
    """Minimal lifecycle hooks for mode-scoped setup and teardown."""

    def on_mode_enter(self, mode: ListeningMode) -> None:
        """Called when the state machine starts in a listening mode."""

    def on_mode_exit(self, mode: ListeningMode) -> None:
        """Called once when transitioning to shutdown."""


class _NoOpModeHooks(ModeHooks):
    def on_mode_enter(self, mode: ListeningMode) -> None:
        return

    def on_mode_exit(self, mode: ListeningMode) -> None:
        return


@dataclass(frozen=True)
class TransitionResult:
    """A single state transition outcome."""

    from_state: AppState
    to_state: AppState | None
    event: AppEvent
    terminal: bool


_TERMINAL = object()

_COMMON_TRANSITIONS: dict[tuple[AppState, AppEvent], AppState | object] = {
    (AppState.INITIALIZING, AppEvent.INITIALIZATION_SUCCEEDED): AppState.STANDBY,
    (AppState.INITIALIZING, AppEvent.INITIALIZATION_FAILED): AppState.ERROR,
    (AppState.LISTENING, AppEvent.SPEECH_FRAME_RECEIVED): AppState.PROCESSING,
    (AppState.PROCESSING, AppEvent.PARTIAL_HANDLED): AppState.LISTENING,
    (AppState.PROCESSING, AppEvent.FINAL_HANDLED): AppState.LISTENING,
    (AppState.LISTENING, AppEvent.WAKE_WINDOW_TIMEOUT): AppState.STANDBY,
    (AppState.LISTENING, AppEvent.INACTIVITY_AUTO_PAUSE): AppState.PAUSED,
    (AppState.LISTENING, AppEvent.STOP_REQUESTED): AppState.SHUTTING_DOWN,
    (AppState.PROCESSING, AppEvent.STOP_REQUESTED): AppState.SHUTTING_DOWN,
    (AppState.STANDBY, AppEvent.PAUSE_REQUESTED): AppState.PAUSED,
    (AppState.PAUSED, AppEvent.RESUME_REQUESTED): AppState.STANDBY,
    (AppState.STANDBY, AppEvent.STOP_REQUESTED): AppState.SHUTTING_DOWN,
    (AppState.PAUSED, AppEvent.STOP_REQUESTED): AppState.SHUTTING_DOWN,
    (AppState.ERROR, AppEvent.STOP_REQUESTED): AppState.SHUTTING_DOWN,
    (AppState.SHUTTING_DOWN, AppEvent.SHUTDOWN_COMPLETE): _TERMINAL,
}

_MODE_TRANSITIONS: dict[ListeningMode, dict[tuple[AppState, AppEvent], AppState]] = {
    ListeningMode.WAKE_WORD: {
        (AppState.STANDBY, AppEvent.WAKE_PHRASE_DETECTED): AppState.LISTENING,
    },
    ListeningMode.TOGGLE: {
        (AppState.STANDBY, AppEvent.TOGGLE_LISTENING_ON): AppState.LISTENING,
    },
    ListeningMode.CONTINUOUS: {
        (AppState.STANDBY, AppEvent.CONTINUOUS_START): AppState.LISTENING,
    },
}


class VoiceKeyStateMachine:
    """Deterministic FSM for runtime lifecycle and listening modes.

    Thread-safe implementation using a lock to protect state transitions.
    """

    def __init__(
        self,
        mode: ListeningMode = ListeningMode.WAKE_WORD,
        initial_state: AppState = AppState.INITIALIZING,
        mode_hooks: ModeHooks | None = None,
    ) -> None:
        self._mode = mode
        self._state = initial_state
        self._terminated = False
        self._mode_exited = False
        self._mode_hooks = mode_hooks or _NoOpModeHooks()
        self._mode_hooks.on_mode_enter(mode)
        self._lock = threading.Lock()

    @property
    def mode(self) -> ListeningMode:
        """Configured listening mode."""
        return self._mode

    @property
    def state(self) -> AppState:
        """Current FSM state (thread-safe read)."""
        with self._lock:
            return self._state

    @property
    def terminated(self) -> bool:
        """Whether the machine has reached terminal shutdown marker (thread-safe read)."""
        with self._lock:
            return self._terminated

    def transition(self, event: AppEvent) -> TransitionResult:
        """Apply an event and return transition details.

        Thread-safe: uses a lock to protect state transitions.

        Raises:
            InvalidTransitionError: If the current state/event is not allowed.
        """
        with self._lock:
            if self._terminated:
                raise InvalidTransitionError("state machine is already terminated")

            key = (self._state, event)
            target = _MODE_TRANSITIONS[self._mode].get(key)
            if target is None:
                target = _COMMON_TRANSITIONS.get(key)
            if target is None:
                raise InvalidTransitionError(
                    f"invalid transition: mode={self._mode.value} state={self._state.value} event={event.value}"
                )

            from_state = self._state
            if target is _TERMINAL:
                self._terminated = True
                return TransitionResult(
                    from_state=from_state,
                    to_state=None,
                    event=event,
                    terminal=True,
                )

            to_state = target
            self._state = to_state
            if to_state is AppState.SHUTTING_DOWN and not self._mode_exited:
                self._mode_hooks.on_mode_exit(self._mode)
                self._mode_exited = True

            return TransitionResult(
                from_state=from_state,
                to_state=to_state,
                event=event,
                terminal=False,
            )


__all__ = [
    "AppEvent",
    "AppState",
    "InvalidTransitionError",
    "ListeningMode",
    "ModeHooks",
    "TransitionResult",
    "VoiceKeyStateMachine",
]
