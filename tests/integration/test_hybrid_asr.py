"""Integration tests for hybrid ASR runtime routing.

Covers live pipeline behavior where RuntimeCoordinator processes frames,
ASR local backend fails, and hybrid router falls back to cloud backend.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np

from voicekey.app.main import RuntimeCoordinator
from voicekey.app.state_machine import AppState, ListeningMode, VoiceKeyStateMachine
from voicekey.audio.asr_faster_whisper import TranscriptEvent, TranscriptionError
from voicekey.audio.asr_router import ASRRouter, ASRRouterConfig
from voicekey.audio.capture import AudioFrame
from tests.conftest import RecordingKeyboardBackend


@dataclass
class _FailingLocalBackend:
    calls: int = 0

    @property
    def is_model_loaded(self) -> bool:
        return True

    def load_model(self) -> None:
        return

    def transcribe(self, _audio: np.ndarray) -> list[TranscriptEvent]:
        self.calls += 1
        raise TranscriptionError("forced local failure")


@dataclass
class _CloudBackend:
    text: str
    calls: int = 0

    def transcribe(self, _audio: np.ndarray) -> list[TranscriptEvent]:
        self.calls += 1
        return [TranscriptEvent(text=self.text, is_final=True, confidence=0.95)]


@dataclass
class _GuardLocalBackend:
    calls: int = 0

    @property
    def is_model_loaded(self) -> bool:
        return True

    def load_model(self) -> None:
        return

    def transcribe(self, _audio: np.ndarray) -> list[TranscriptEvent]:
        self.calls += 1
        raise AssertionError("Local backend should not be called in cloud-primary mode")


def _feed_frames(coordinator: RuntimeCoordinator, count: int = 10) -> None:
    """Feed enough frames to trigger runtime transcription flush."""
    frame_audio = np.full(1600, 0.1, dtype=np.float32)
    for i in range(count):
        coordinator._process_frame(  # noqa: SLF001 - intentional integration path
            AudioFrame(
                audio=frame_audio,
                sample_rate=16000,
                timestamp=time.monotonic() + i * 0.01,
            )
        )


def test_runtime_pipeline_hybrid_falls_back_to_cloud_on_local_failure() -> None:
    keyboard = RecordingKeyboardBackend()
    local = _FailingLocalBackend()
    cloud = _CloudBackend(text="cloud fallback transcript")

    router = ASRRouter(
        config=ASRRouterConfig(
            asr_backend="faster-whisper",
            network_fallback_enabled=True,
            cloud_api_base="https://api.example.com/v1",
            cloud_api_key="test-key",
        ),
        local_backend=local,
        cloud_backend=cloud,
    )

    coordinator = RuntimeCoordinator(
        state_machine=VoiceKeyStateMachine(
            mode=ListeningMode.CONTINUOUS,
            initial_state=AppState.LISTENING,
        ),
        keyboard_backend=keyboard,
        asr_engine=router,
    )

    _feed_frames(coordinator)

    assert local.calls >= 1
    assert cloud.calls == 1
    assert keyboard.typed_texts == ["cloud fallback transcript "]


def test_runtime_pipeline_cloud_primary_uses_cloud_only() -> None:
    keyboard = RecordingKeyboardBackend()
    local = _GuardLocalBackend()
    cloud = _CloudBackend(text="cloud primary transcript")

    router = ASRRouter(
        config=ASRRouterConfig(
            asr_backend="openai-api-compatible",
            cloud_api_base="https://api.example.com/v1",
            cloud_api_key="test-key",
        ),
        local_backend=local,
        cloud_backend=cloud,
    )

    coordinator = RuntimeCoordinator(
        state_machine=VoiceKeyStateMachine(
            mode=ListeningMode.CONTINUOUS,
            initial_state=AppState.LISTENING,
        ),
        keyboard_backend=keyboard,
        asr_engine=router,
    )

    _feed_frames(coordinator)

    assert local.calls == 0
    assert cloud.calls == 1
    assert keyboard.typed_texts == ["cloud primary transcript "]
