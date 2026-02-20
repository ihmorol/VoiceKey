"""Application-layer runtime coordination for wake-word mode."""

from __future__ import annotations

import logging
import queue
import threading
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

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
from voicekey.platform.keyboard_base import KeyboardBackend

logger = logging.getLogger(__name__)

# Audio components - will be imported conditionally
AudioCapture = None
AudioFrame = None
VADProcessor = None
_streaming_vad = None

# Try to import audio components - may fail if PortAudio is missing
_audio_import_error = None
try:
    from voicekey.audio.capture import AudioCapture, AudioFrame
except Exception as e:
    _audio_import_error = e
    logger.debug(f"Audio capture not available: {e}")

try:
    from voicekey.audio.vad import VADProcessor
except Exception as e:
    logger.debug(f"VAD processor not available: {e}")


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
        # Audio components
        audio_capture=None,  # Type: AudioCapture | None
        vad_processor=None,  # Type: VADProcessor | None
        asr_engine=None,
        keyboard_backend: KeyboardBackend | None = None,
        # Configuration
        device_index: int | None = None,
        sample_rate: int = 16000,
        vad_threshold: float = 0.5,
    ) -> None:
        self._state_machine = state_machine
        self._wake_detector = wake_detector or WakePhraseDetector()
        self._wake_window = wake_window or WakeWindowController()
        self._parser = parser or create_parser()
        self._routing_policy = routing_policy or RuntimeRoutingPolicy()
        self._action_router = action_router
        self._text_output = text_output
        self._confidence_filter = confidence_filter or ConfidenceFilter(log_dropped=False)

        # Audio components
        self._audio_capture = audio_capture
        self._vad_processor = vad_processor
        self._asr_engine = asr_engine
        self._keyboard_backend = keyboard_backend

        # Audio configuration
        self._device_index = device_index
        self._sample_rate = sample_rate
        self._vad_threshold = vad_threshold

        # Runtime state
        self._lock = threading.Lock()
        self._is_running = False
        self._processing_thread: threading.Thread | None = None
        self._stop_event = threading.Event()

        # Audio buffers for ASR
        self._audio_buffer: list = []
        self._buffer_lock = threading.Lock()
        self._speech_active = False
        self._min_speech_frames = 3  # Require 3 consecutive VAD detections

        # Text output callback for runtime
        self._runtime_text_output: Callable[[str], None] | None = None

    @property
    def is_running(self) -> bool:
        """Whether the runtime coordinator is currently running."""
        with self._lock:
            return self._is_running

    def start(self) -> None:
        """Start the audio pipeline and begin voice recognition."""
        with self._lock:
            if self._is_running:
                logger.warning("RuntimeCoordinator already running")
                return

            logger.info("Starting RuntimeCoordinator")

            # Initialize audio capture if not provided
            if self._audio_capture is None:
                if AudioCapture is None:
                    raise RuntimeError("Audio capture not available (sounddevice/PortAudio missing)")
                self._audio_capture = AudioCapture(
                    device_index=self._device_index,
                    sample_rate=self._sample_rate,
                )

            # Initialize VAD processor if not provided
            if self._vad_processor is None:
                if VADProcessor is None:
                    raise RuntimeError("VAD processor not available")
                self._vad_processor = VADProcessor(threshold=self._vad_threshold)

            # Initialize ASR engine if not provided and available
            if self._asr_engine is None:
                try:
                    from voicekey.audio.asr_faster_whisper import ASREngine

                    self._asr_engine = ASREngine(
                        model_size="base",
                        device="auto",
                        sample_rate=self._sample_rate,
                    )
                except ImportError:
                    logger.warning("ASR engine not available, speech recognition disabled")

            # Initialize keyboard backend and action router if not provided
            if self._action_router is None and self._keyboard_backend is not None:
                self._action_router = ActionRouter(keyboard_backend=self._keyboard_backend)

            # Mark as running
            self._is_running = True
            self._stop_event.clear()

            # Start audio capture
            self._audio_capture.start()

            # Start processing thread
            self._processing_thread = threading.Thread(
                target=self._audio_processing_loop,
                daemon=True,
            )
            self._processing_thread.start()

            # Transition state machine to STANDBY
            try:
                self._state_machine.transition(AppEvent.INITIALIZATION_SUCCEEDED)
            except Exception as e:
                logger.warning(f"Could not transition to STANDBY: {e}")

            logger.info("RuntimeCoordinator started successfully")

    def stop(self) -> None:
        """Stop the audio pipeline and shutdown gracefully."""
        with self._lock:
            if not self._is_running:
                logger.warning("RuntimeCoordinator not running")
                return

            logger.info("Stopping RuntimeCoordinator")

            # Signal stop event
            self._stop_event.set()

            # Stop audio capture
            if self._audio_capture is not None:
                self._audio_capture.stop()

            # Wait for processing thread to finish
            if self._processing_thread is not None:
                self._processing_thread.join(timeout=2.0)
                self._processing_thread = None

            # Transition to shutting down
            try:
                self._state_machine.transition(AppEvent.STOP_REQUESTED)
            except Exception:
                pass  # State machine might already be in terminal state

            self._is_running = False
            logger.info("RuntimeCoordinator stopped")

    def set_text_output(self, callback: Callable[[str], None] | None) -> None:
        """Set the text output callback for dictation."""
        self._runtime_text_output = callback

    def _audio_processing_loop(self) -> None:
        """Main audio processing loop running in a separate thread."""
        consecutive_speech_frames = 0

        while not self._stop_event.is_set():
            try:
                # Get audio frame from queue with timeout
                if self._audio_capture is None:
                    break

                audio_queue = self._audio_capture.get_audio_queue()
                try:
                    frame: AudioFrame = audio_queue.get(timeout=0.1)
                except queue.Empty:
                    # Check for timeout in listening state
                    if self._state_machine.state == AppState.LISTENING:
                        self._check_timeout()
                    continue

                # Process VAD
                is_speech = self._vad_processor.process(frame.audio)

                # Update frame with VAD result
                frame.is_speech = is_speech

                if is_speech:
                    consecutive_speech_frames += 1

                    # Add to audio buffer for ASR
                    with self._buffer_lock:
                        self._audio_buffer.append(frame.audio)
                        self._speech_active = True

                    # Notify coordinator of activity
                    self.on_activity()
                else:
                    if self._speech_active:
                        # Speech ended, process accumulated audio
                        consecutive_speech_frames = 0
                        self._process_speech_end()

                    consecutive_speech_frames = 0
                    with self._buffer_lock:
                        self._speech_active = False

                # Process audio through coordinator
                self._process_frame(frame)

            except Exception as e:
                logger.error(f"Error in audio processing loop: {e}")
                time.sleep(0.1)  # Brief sleep to avoid busy loop on errors

    def _process_frame(self, frame: AudioFrame) -> None:
        """Process a single audio frame through the coordinator."""
        # Check for timeout
        if self._state_machine.state == AppState.LISTENING:
            self._check_timeout()

        # Get current state and handle accordingly
        state = self._state_machine.state

        if state == AppState.STANDBY:
            # In standby, we could potentially do wake word detection
            # but typically this is done on transcribed text
            pass

    def _process_speech_end(self) -> None:
        """Process accumulated audio when speech ends."""
        with self._buffer_lock:
            if not self._audio_buffer:
                return

            # Concatenate all audio frames
            import numpy as np

            audio_data = np.concatenate(self._audio_buffer)
            self._audio_buffer.clear()

        if len(audio_data) == 0:
            return

        # Transcribe audio if ASR is available
        if self._asr_engine is None:
            logger.debug("No ASR engine available for transcription")
            return

        try:
            # Ensure model is loaded
            if not self._asr_engine.is_model_loaded:
                self._asr_engine.load_model()

            # Transcribe the audio
            events = self._asr_engine.transcribe(audio_data)

            # Process each transcript event
            for event in events:
                self._handle_transcript_event(event)

        except Exception as e:
            logger.error(f"Transcription error: {e}")

    def _handle_transcript_event(self, event: TranscriptEvent) -> None:
        """Handle a transcript event from ASR."""
        # Apply confidence filter
        filtered = self._confidence_filter.filter(event)
        if filtered is None:
            return

        transcript = filtered.text
        if not transcript:
            return

        # Process through coordinator's transcript handler
        update = self.on_transcript(transcript, vad_active=True)

        # Handle wake detected
        if update.wake_detected:
            logger.info(f"Wake phrase detected, transitioned to {self._state_machine.state}")

        # Handle routed text (dictation)
        if update.routed_text:
            logger.debug(f"Routing text: {update.routed_text}")
            if self._text_output is not None:
                self._text_output(update.routed_text)
            if self._runtime_text_output is not None:
                self._runtime_text_output(update.routed_text)

        # Handle executed commands
        if update.executed_command_id:
            logger.info(f"Executed command: {update.executed_command_id}")

    def _check_timeout(self) -> None:
        """Check for wake window timeout."""
        update = self.poll()
        if update.transition is not None:
            logger.info(f"Wake window timed out, transitioning to {update.transition.to_state}")

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
