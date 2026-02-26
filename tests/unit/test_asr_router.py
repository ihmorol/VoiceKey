"""Unit tests for hybrid ASR routing and OpenAI-compatible ASR backend."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import pytest

from voicekey.audio.asr_faster_whisper import TranscriptEvent, TranscriptionError
from voicekey.audio.asr_openai_compatible import (
    OpenAICompatibleASRBackend,
    OpenAICompatibleASRConfig,
)
from voicekey.audio.asr_router import (
    ASRConfigurationError,
    ASRRouter,
    ASRRouterConfig,
    ASRRoutingMode,
    create_asr_router_from_engine_config,
)


@dataclass
class _FakeBackend:
    events: Sequence[TranscriptEvent] | None = None
    error: Exception | None = None
    calls: int = 0

    def transcribe(self, _audio: np.ndarray) -> list[TranscriptEvent]:
        self.calls += 1
        if self.error is not None:
            raise self.error
        return list(self.events or [])


def _event(text: str) -> TranscriptEvent:
    return TranscriptEvent(text=text, is_final=True, confidence=0.9)


def test_local_only_mode_uses_local_backend_and_never_calls_cloud() -> None:
    local = _FakeBackend(events=[_event("local")])
    cloud = _FakeBackend(events=[_event("cloud")])

    router = ASRRouter(
        config=ASRRouterConfig(
            asr_backend="faster-whisper",
            network_fallback_enabled=False,
        ),
        local_backend=local,
        cloud_backend=cloud,
    )

    result = router.transcribe(np.ones(8, dtype=np.float32))

    assert router.mode is ASRRoutingMode.LOCAL_ONLY
    assert result.backend_used == "local"
    assert local.calls == 1
    assert cloud.calls == 0


def test_hybrid_requested_without_cloud_config_stays_local_only() -> None:
    local = _FakeBackend(events=[_event("local")])
    cloud = _FakeBackend(events=[_event("cloud")])

    router = ASRRouter(
        config=ASRRouterConfig(
            asr_backend="faster-whisper",
            network_fallback_enabled=True,
            cloud_api_base=None,
            cloud_api_key=None,
        ),
        local_backend=local,
        cloud_backend=cloud,
    )

    result = router.transcribe(np.ones(8, dtype=np.float32))

    assert router.mode is ASRRoutingMode.LOCAL_ONLY
    assert result.backend_used == "local"
    assert cloud.calls == 0


def test_hybrid_mode_falls_back_to_cloud_when_local_fails() -> None:
    local = _FakeBackend(error=TranscriptionError("local failed"))
    cloud = _FakeBackend(events=[_event("cloud")])

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

    result = router.transcribe(np.ones(8, dtype=np.float32))

    assert router.mode is ASRRoutingMode.HYBRID
    assert result.backend_used == "cloud"
    assert result.fallback_used is True
    assert local.calls == 1
    assert cloud.calls == 1


def test_cloud_primary_requires_cloud_configuration() -> None:
    local = _FakeBackend(events=[_event("local")])

    with pytest.raises(ASRConfigurationError):
        ASRRouter(
            config=ASRRouterConfig(asr_backend="openai-api-compatible"),
            local_backend=local,
            cloud_backend=None,
        )


def test_cloud_primary_routes_only_to_cloud_backend() -> None:
    local = _FakeBackend(events=[_event("local")])
    cloud = _FakeBackend(events=[_event("cloud")])

    router = ASRRouter(
        config=ASRRouterConfig(
            asr_backend="openai-api-compatible",
            cloud_api_base="https://api.example.com/v1",
            cloud_api_key="test-key",
        ),
        local_backend=local,
        cloud_backend=cloud,
    )

    result = router.transcribe(np.ones(8, dtype=np.float32))

    assert router.mode is ASRRoutingMode.CLOUD_PRIMARY
    assert result.backend_used == "cloud"
    assert local.calls == 0
    assert cloud.calls == 1


def test_router_factory_reads_cloud_key_from_environment() -> None:
    local = _FakeBackend(events=[_event("local")])
    cloud = _FakeBackend(events=[_event("cloud")])

    router = create_asr_router_from_engine_config(
        engine_config={
            "asr_backend": "faster-whisper",
            "network_fallback_enabled": True,
            "cloud_api_base": "https://api.example.com/v1",
            "cloud_model": "gpt-4o-mini-transcribe",
            "cloud_timeout_seconds": 30,
        },
        local_backend=local,
        cloud_backend=cloud,
        environ={"VOICEKEY_OPENAI_API_KEY": "test-key"},
    )

    assert router.mode is ASRRoutingMode.HYBRID


def test_openai_backend_empty_audio_short_circuits_without_transport_call() -> None:
    calls: list[dict[str, object]] = []

    def transport(**kwargs: object) -> dict[str, object]:
        calls.append(kwargs)
        return {"text": "should not be used"}

    backend = OpenAICompatibleASRBackend(
        OpenAICompatibleASRConfig(
            api_base="https://api.example.com/v1",
            api_key="test-key",
            model="gpt-4o-mini-transcribe",
        ),
        transport=transport,
    )

    result = backend.transcribe(np.array([], dtype=np.float32))

    assert result == []
    assert calls == []
