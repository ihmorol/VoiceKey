"""Application-layer runtime coordination for wake-word mode."""

from __future__ import annotations

from dataclasses import dataclass

from voicekey.app.state_machine import (
    AppEvent,
    AppState,
    ListeningMode,
    TransitionResult,
    VoiceKeyStateMachine,
)
from voicekey.audio.wake import WakePhraseDetector, WakeWindowController
from voicekey.commands.parser import CommandParser, ParseKind


@dataclass(frozen=True)
class RuntimeUpdate:
    """Deterministic runtime update emitted by coordinator operations."""

    transition: TransitionResult | None = None
    wake_detected: bool = False
    routed_text: str | None = None


class RuntimeCoordinator:
    """Binds wake detection/window control to FSM transitions."""

    def __init__(
        self,
        state_machine: VoiceKeyStateMachine,
        wake_detector: WakePhraseDetector | None = None,
        wake_window: WakeWindowController | None = None,
        parser: CommandParser | None = None,
    ) -> None:
        self._state_machine = state_machine
        self._wake_detector = wake_detector or WakePhraseDetector()
        self._wake_window = wake_window or WakeWindowController()
        self._parser = parser or CommandParser()

    @property
    def state(self) -> AppState:
        """Current application state."""
        return self._state_machine.state

    @property
    def wake_window_timeout_seconds(self) -> float:
        """Configured wake window timeout."""
        return self._wake_window.timeout_seconds

    @property
    def is_wake_window_open(self) -> bool:
        """Whether wake listening window is currently open."""
        return self._wake_window.is_open()

    def on_transcript(self, transcript: str) -> RuntimeUpdate:
        """Handle transcript as wake detection input/activity signal."""
        if self.state is AppState.PAUSED:
            paused_update = self._handle_paused_system_phrase(transcript)
            if paused_update is not None:
                return paused_update

        if self._state_machine.mode is not ListeningMode.WAKE_WORD:
            return RuntimeUpdate()

        if self.state is AppState.STANDBY:
            match = self._wake_detector.detect(transcript)
            if not match.matched:
                return RuntimeUpdate()

            transition = self._state_machine.transition(AppEvent.WAKE_PHRASE_DETECTED)
            self._wake_window.open_window()
            return RuntimeUpdate(transition=transition, wake_detected=True)

        if self.state is AppState.LISTENING and self._wake_window.is_open():
            self._wake_window.on_activity()

        return RuntimeUpdate()

    def on_activity(self) -> RuntimeUpdate:
        """Handle generic activity hooks (for example VAD/speech activity)."""
        if self._state_machine.mode is not ListeningMode.WAKE_WORD:
            return RuntimeUpdate()

        if self.state is AppState.LISTENING and self._wake_window.is_open():
            self._wake_window.on_activity()

        return RuntimeUpdate()

    def poll(self) -> RuntimeUpdate:
        """Advance timeout logic and emit FSM transition updates."""
        if self._state_machine.mode is not ListeningMode.WAKE_WORD:
            return RuntimeUpdate()

        if self.state is not AppState.LISTENING:
            return RuntimeUpdate()
        if not self._wake_window.poll_timeout():
            return RuntimeUpdate()

        transition = self._state_machine.transition(AppEvent.WAKE_WINDOW_TIMEOUT)
        return RuntimeUpdate(transition=transition)

    def _handle_paused_system_phrase(self, transcript: str) -> RuntimeUpdate | None:
        parsed = self._parser.parse(transcript)
        if parsed.kind is not ParseKind.SYSTEM or parsed.command is None:
            return None

        if parsed.command.command_id == "resume_voice_key":
            transition = self._state_machine.transition(AppEvent.RESUME_REQUESTED)
            return RuntimeUpdate(transition=transition)

        if parsed.command.command_id == "voice_key_stop":
            transition = self._state_machine.transition(AppEvent.STOP_REQUESTED)
            return RuntimeUpdate(transition=transition)

        return None


__all__ = ["RuntimeCoordinator", "RuntimeUpdate"]
