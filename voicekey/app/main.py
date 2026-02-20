"""Application-layer runtime coordination for wake-word mode."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from voicekey.actions.router import ActionRouter
from voicekey.app.routing_policy import RuntimeRoutingPolicy
from voicekey.app.state_machine import (
    AppEvent,
    AppState,
    ListeningMode,
    TransitionResult,
    VoiceKeyStateMachine,
)
from voicekey.audio.asr_faster_whisper import TranscriptEvent
from voicekey.audio.threshold import ConfidenceFilter
from voicekey.audio.wake import WakePhraseDetector, WakeWindowController
from voicekey.commands.parser import CommandParser, ParseKind, create_parser


@dataclass(frozen=True)
class RuntimeUpdate:
    """Deterministic runtime update emitted by coordinator operations."""

    transition: TransitionResult | None = None
    wake_detected: bool = False
    routed_text: str | None = None
    executed_command_id: str | None = None


class RuntimeCoordinator:
    """Binds wake detection/window control to FSM transitions."""

    def __init__(
        self,
        state_machine: VoiceKeyStateMachine,
        wake_detector: WakePhraseDetector | None = None,
        wake_window: WakeWindowController | None = None,
        parser: CommandParser | None = None,
        routing_policy: RuntimeRoutingPolicy | None = None,
        action_router: ActionRouter | None = None,
        text_output: Callable[[str], None] | None = None,
        confidence_filter: ConfidenceFilter | None = None,
    ) -> None:
        self._state_machine = state_machine
        self._wake_detector = wake_detector or WakePhraseDetector()
        self._wake_window = wake_window or WakeWindowController()
        self._parser = parser or create_parser()
        self._routing_policy = routing_policy or RuntimeRoutingPolicy()
        self._action_router = action_router
        self._text_output = text_output
        self._confidence_filter = confidence_filter or ConfidenceFilter(log_dropped=False)

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

    def on_transcript(self, transcript: str, *, vad_active: bool = True) -> RuntimeUpdate:
        """Handle transcript as wake detection input/activity signal."""
        if self.state is AppState.PAUSED:
            return self._handle_paused_transcript(transcript)

        if self._state_machine.mode is not ListeningMode.WAKE_WORD:
            return RuntimeUpdate()

        if self.state is AppState.STANDBY:
            if not vad_active:
                return RuntimeUpdate()
            match = self._wake_detector.detect(transcript)
            if not match.matched:
                return RuntimeUpdate()

            transition = self._state_machine.transition(AppEvent.WAKE_PHRASE_DETECTED)
            self._wake_window.open_window()
            return RuntimeUpdate(transition=transition, wake_detected=True)

        if self.state is AppState.LISTENING and self._wake_window.is_open():
            self._wake_window.on_activity()
            return self._handle_listening_transcript(transcript)

        return RuntimeUpdate()

    def on_transcript_event(self, transcript: TranscriptEvent, *, vad_active: bool = True) -> RuntimeUpdate:
        """Handle ASR transcript event with confidence-threshold filtering."""
        filtered = self._confidence_filter.filter(transcript)
        if filtered is None:
            return RuntimeUpdate()
        return self.on_transcript(filtered.text, vad_active=vad_active)

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

    def _handle_paused_transcript(self, transcript: str) -> RuntimeUpdate:
        parsed = self._parser.parse(transcript)
        policy = self._routing_policy.evaluate(self.state, parsed)
        if not policy.allowed:
            return RuntimeUpdate()

        if parsed.kind is not ParseKind.SYSTEM or parsed.command is None:
            return RuntimeUpdate()

        if parsed.command.command_id == "resume_voice_key":
            transition = self._state_machine.transition(AppEvent.RESUME_REQUESTED)
            return RuntimeUpdate(transition=transition)

        if parsed.command.command_id == "voice_key_stop":
            transition = self._state_machine.transition(AppEvent.STOP_REQUESTED)
            return RuntimeUpdate(transition=transition)

        return RuntimeUpdate()

    def _handle_listening_transcript(self, transcript: str) -> RuntimeUpdate:
        parsed = self._parser.parse(transcript)
        policy = self._routing_policy.evaluate(self.state, parsed)
        if not policy.allowed:
            return RuntimeUpdate()

        if parsed.kind is ParseKind.TEXT:
            literal = parsed.literal_text or ""
            if not literal:
                return RuntimeUpdate()
            if self._text_output is not None:
                self._text_output(literal)
            return RuntimeUpdate(routed_text=literal)

        if parsed.command is None:
            return RuntimeUpdate()

        command_id = parsed.command.command_id
        if command_id == "pause_voice_key":
            transition = self._state_machine.transition(AppEvent.INACTIVITY_AUTO_PAUSE)
            return RuntimeUpdate(transition=transition, executed_command_id=command_id)

        if command_id == "voice_key_stop":
            transition = self._state_machine.transition(AppEvent.STOP_REQUESTED)
            return RuntimeUpdate(transition=transition, executed_command_id=command_id)

        if self._action_router is None:
            return RuntimeUpdate(executed_command_id=command_id)

        route_result = self._action_router.dispatch(command_id)
        if not route_result.handled:
            return RuntimeUpdate()

        return RuntimeUpdate(executed_command_id=command_id)


__all__ = ["RuntimeCoordinator", "RuntimeUpdate"]
