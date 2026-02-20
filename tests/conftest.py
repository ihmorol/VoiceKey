"""Shared pytest fixtures for VoiceKey tests.

This module provides deterministic fixtures for:
- Mock audio capture (fixture audio instead of real microphone)
- Mock keyboard backend (recording injector for verification)
- Mock ASR engine (deterministic transcript generation)
- Mock VAD processor (configurable speech/silence detection)

Note: This module avoids importing sounddevice-dependent modules to ensure
tests can run without PortAudio installed.
"""

from __future__ import annotations

import queue
import sys
import time
from dataclasses import dataclass, field
from typing import Callable, Optional
from unittest.mock import MagicMock

import numpy as np
import pytest

# Mock sounddevice before importing any voicekey modules that depend on it
# This allows tests to run without PortAudio installed
if 'sounddevice' not in sys.modules:
    sys.modules['sounddevice'] = MagicMock()

from voicekey.app.state_machine import AppState, ModeHooks, VoiceKeyStateMachine
from voicekey.audio.asr_faster_whisper import TranscriptEvent
from voicekey.audio.vad import VADResult
from voicekey.commands.parser import CommandParser
from voicekey.commands.registry import CommandRegistry
from voicekey.actions.router import ActionRouter
from voicekey.platform.keyboard_base import KeyboardBackend, KeyboardCapabilityReport, KeyboardCapabilityState
from voicekey.ui.tray import TrayActionHandlers, TrayController


# =============================================================================
# Local AudioFrame Definition (avoids sounddevice dependency)
# =============================================================================

@dataclass
class AudioFrame:
    """Single audio frame for testing (avoids sounddevice dependency).

    Attributes:
        audio: Raw PCM samples as numpy array (float32, range [-1, 1])
        sample_rate: Sample rate in Hz (default 16000)
        timestamp: Monotonic timestamp when frame was captured
        is_speech: VAD result - True if speech detected, False if silence,
                   None if VAD not applied
    """

    audio: np.ndarray
    sample_rate: int
    timestamp: float
    is_speech: Optional[bool] = None


# =============================================================================
# Mock Keyboard Backend
# =============================================================================

@dataclass
class RecordingKeyboardBackend(KeyboardBackend):
    """Test keyboard backend that records calls without OS side effects."""

    typed_texts: list[str] = field(default_factory=list)
    pressed_keys: list[str] = field(default_factory=list)
    pressed_combos: list[list[str]] = field(default_factory=list)
    capability_state: KeyboardCapabilityState = KeyboardCapabilityState.READY

    def type_text(self, text: str, delay_ms: int = 0) -> None:
        if not text:
            return
        self.typed_texts.append(text)

    def press_key(self, key: str) -> None:
        self.pressed_keys.append(key)

    def press_combo(self, keys: list[str]) -> None:
        if keys:
            self.pressed_combos.append(keys)

    def self_check(self) -> KeyboardCapabilityReport:
        return KeyboardCapabilityReport(
            backend="recording_test_backend",
            platform="test",
            state=self.capability_state,
            active_adapter="recording",
            available_adapters=("recording",),
            codes=(),
            warnings=(),
            remediation=(),
        )

    def reset(self) -> None:
        """Clear all recorded calls."""
        self.typed_texts.clear()
        self.pressed_keys.clear()
        self.pressed_combos.clear()


# =============================================================================
# Mock Audio Components
# =============================================================================

class MockAudioCapture:
    """Mock audio capture that yields fixture audio frames."""

    def __init__(
        self,
        frames: list[np.ndarray] | None = None,
        sample_rate: int = 16000,
        is_speech_sequence: list[bool] | None = None,
    ):
        self._frames = frames or []
        self._sample_rate = sample_rate
        self._is_speech_sequence = is_speech_sequence or []
        self._frame_index = 0
        self._is_running = False
        self._audio_queue: queue.Queue[AudioFrame] = queue.Queue(maxsize=32)

    def load_frames(self, frames: list[np.ndarray], is_speech_sequence: list[bool] | None = None) -> None:
        """Load fixture frames for playback."""
        self._frames = frames
        self._is_speech_sequence = is_speech_sequence or [True] * len(frames)
        self._frame_index = 0

    def start(self) -> None:
        self._is_running = True
        self._frame_index = 0
        # Push frames into queue
        for i, frame in enumerate(self._frames):
            is_speech = self._is_speech_sequence[i] if i < len(self._is_speech_sequence) else True
            audio_frame = AudioFrame(
                audio=frame,
                sample_rate=self._sample_rate,
                timestamp=time.monotonic() + i * 0.1,
                is_speech=is_speech,
            )
            self._audio_queue.put_nowait(audio_frame)

    def stop(self) -> None:
        self._is_running = False
        # Drain queue
        try:
            while True:
                self._audio_queue.get_nowait()
        except queue.Empty:
            pass

    def is_running(self) -> bool:
        return self._is_running

    def get_audio_queue(self) -> queue.Queue[AudioFrame]:
        return self._audio_queue


class MockVADProcessor:
    """Mock VAD that returns predetermined speech/silence results."""

    def __init__(self, results: list[VADResult] | None = None):
        self._results = results or []
        self._result_index = 0

    def set_results(self, results: list[VADResult]) -> None:
        self._results = results
        self._result_index = 0

    def process(self, audio: np.ndarray) -> bool:
        if self._result_index < len(self._results):
            result = self._results[self._result_index]
            self._result_index += 1
            return result.is_speech
        return True  # Default to speech

    def reset(self) -> None:
        self._result_index = 0


class MockASREngine:
    """Mock ASR engine that yields predetermined transcripts."""

    def __init__(self, transcripts: list[TranscriptEvent] | None = None):
        self._transcripts = transcripts or []
        self._transcript_index = 0

    def set_transcripts(self, transcripts: list[TranscriptEvent]) -> None:
        self._transcripts = transcripts
        self._transcript_index = 0

    def transcribe(self, audio: np.ndarray) -> list[TranscriptEvent]:
        if self._transcript_index < len(self._transcripts):
            events = [self._transcripts[self._transcript_index]]
            self._transcript_index += 1
            return events
        return []

    def load_model(self) -> None:
        pass

    def unload_model(self) -> None:
        pass

    @property
    def is_model_loaded(self) -> bool:
        return True


# =============================================================================
# Audio Fixtures
# =============================================================================

def generate_speech_like_audio(duration_seconds: float = 0.5, sample_rate: int = 16000) -> np.ndarray:
    """Generate synthetic speech-like audio for testing.

    Creates a combination of frequencies that simulates speech patterns.
    """
    samples = int(duration_seconds * sample_rate)
    t = np.linspace(0, duration_seconds, samples, dtype=np.float32)

    # Generate speech-like frequencies (fundamental + harmonics)
    fundamental = 150  # Hz - typical speech fundamental
    audio = np.zeros(samples, dtype=np.float32)

    for harmonic in range(1, 6):
        amplitude = 0.3 / harmonic
        audio += amplitude * np.sin(2 * np.pi * fundamental * harmonic * t)

    # Add some noise and modulation
    audio += 0.05 * np.random.randn(samples).astype(np.float32)
    audio *= 0.5 * (1 + 0.3 * np.sin(2 * np.pi * 3 * t))  # Amplitude modulation

    # Normalize to typical speech levels
    audio = audio / (np.max(np.abs(audio)) + 1e-8) * 0.5

    return audio


def generate_silence_audio(duration_seconds: float = 0.5, sample_rate: int = 16000) -> np.ndarray:
    """Generate silence audio (very low amplitude noise)."""
    samples = int(duration_seconds * sample_rate)
    # Very low amplitude noise representing silence/background
    return np.random.randn(samples).astype(np.float32) * 0.001


# =============================================================================
# Pytest Fixtures
# =============================================================================

@pytest.fixture
def recording_keyboard_backend() -> RecordingKeyboardBackend:
    """Provide a fresh recording keyboard backend for each test."""
    return RecordingKeyboardBackend()


@pytest.fixture
def mock_audio_capture() -> MockAudioCapture:
    """Provide a mock audio capture instance."""
    return MockAudioCapture()


@pytest.fixture
def mock_vad_processor() -> MockVADProcessor:
    """Provide a mock VAD processor instance."""
    return MockVADProcessor()


@pytest.fixture
def mock_asr_engine() -> MockASREngine:
    """Provide a mock ASR engine instance."""
    return MockASREngine()


@pytest.fixture
def speech_audio_frames() -> list[np.ndarray]:
    """Provide a sequence of speech-like audio frames for testing."""
    chunk_duration = 0.1  # 100ms chunks
    return [generate_speech_like_audio(chunk_duration) for _ in range(5)]


@pytest.fixture
def silence_audio_frames() -> list[np.ndarray]:
    """Provide a sequence of silence audio frames for testing."""
    chunk_duration = 0.1  # 100ms chunks
    return [generate_silence_audio(chunk_duration) for _ in range(5)]


@pytest.fixture
def mixed_audio_frames() -> tuple[list[np.ndarray], list[bool]]:
    """Provide mixed speech/silence frames with VAD labels."""
    chunk_duration = 0.1
    frames = [
        generate_silence_audio(chunk_duration),  # silence
        generate_speech_like_audio(chunk_duration),  # speech
        generate_speech_like_audio(chunk_duration),  # speech
        generate_silence_audio(chunk_duration),  # silence
        generate_speech_like_audio(chunk_duration),  # speech
    ]
    is_speech_sequence = [False, True, True, False, True]
    return frames, is_speech_sequence


@pytest.fixture
def command_parser() -> CommandParser:
    """Provide a default command parser for testing."""
    return CommandParser()


@pytest.fixture
def action_router(recording_keyboard_backend: RecordingKeyboardBackend) -> ActionRouter:
    """Provide an action router with a recording keyboard backend."""
    return ActionRouter(keyboard_backend=recording_keyboard_backend)


@pytest.fixture
def state_machine() -> VoiceKeyStateMachine:
    """Provide a fresh state machine in INITIALIZING state."""
    return VoiceKeyStateMachine()


@pytest.fixture
def tray_controller() -> TrayController:
    """Provide a tray controller for testing."""
    return TrayController(handlers=TrayActionHandlers())


# =============================================================================
# Helper Functions
# =============================================================================

def create_transcript_event(text: str, is_final: bool = True, confidence: float = 0.9) -> TranscriptEvent:
    """Create a transcript event for testing."""
    return TranscriptEvent(
        text=text,
        is_final=is_final,
        confidence=confidence,
        language="en",
        timestamp_start=0.0,
        timestamp_end=1.0,
    )
