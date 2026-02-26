"""OpenAI-compatible ASR backend adapter.

This adapter intentionally keeps cloud routing explicit and opt-in. It performs no
network work unless initialized with a valid cloud API base and API key.
"""

from __future__ import annotations

import base64
import json
import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

import numpy as np

from voicekey.audio.asr_faster_whisper import TranscriptEvent

CloudTransport = Callable[..., Mapping[str, Any]]


class OpenAICompatibleASRError(Exception):
    """Base error for OpenAI-compatible ASR adapter failures."""


class CloudASRConfigurationError(OpenAICompatibleASRError):
    """Raised when cloud ASR configuration is incomplete or invalid."""


class CloudASRTranscriptionError(OpenAICompatibleASRError):
    """Raised when cloud ASR transcription request/response fails."""


@dataclass(frozen=True)
class OpenAICompatibleASRConfig:
    """Configuration for OpenAI-compatible cloud ASR."""

    api_base: str
    api_key: str
    model: str = "gpt-4o-mini-transcribe"
    timeout_seconds: float = 30.0
    sample_rate_hz: int = 16000
    endpoint_path: str = "/audio/transcriptions"

    def __post_init__(self) -> None:
        if not self.api_base or not self.api_base.strip():
            raise CloudASRConfigurationError("cloud_api_base must be configured")
        if not self.api_base.startswith("https://"):
            raise CloudASRConfigurationError("cloud_api_base must start with https://")
        if not self.api_key or not self.api_key.strip():
            raise CloudASRConfigurationError("VOICEKEY_OPENAI_API_KEY must be configured")
        if not self.model or not self.model.strip():
            raise CloudASRConfigurationError("cloud_model must not be empty")
        if self.timeout_seconds <= 0:
            raise CloudASRConfigurationError("cloud_timeout_seconds must be > 0")
        if self.sample_rate_hz <= 0:
            raise CloudASRConfigurationError("sample_rate_hz must be > 0")

    @property
    def transcription_url(self) -> str:
        """Full transcription endpoint URL."""
        normalized = self.api_base.rstrip("/") + "/"
        return urljoin(normalized, self.endpoint_path.lstrip("/"))


class OpenAICompatibleASRBackend:
    """OpenAI-compatible ASR backend implementation."""

    def __init__(
        self,
        config: OpenAICompatibleASRConfig,
        transport: CloudTransport | None = None,
    ) -> None:
        self._config = config
        self._transport = transport or _default_transport

    @property
    def config(self) -> OpenAICompatibleASRConfig:
        """Adapter configuration."""
        return self._config

    def transcribe(self, audio: np.ndarray) -> list[TranscriptEvent]:
        """Transcribe audio via OpenAI-compatible endpoint."""
        if audio.size == 0:
            return []

        normalized_audio = np.asarray(audio, dtype=np.float32)
        payload = {
            "model": self._config.model,
            "encoding": "pcm_f32le",
            "sample_rate_hz": self._config.sample_rate_hz,
            "audio_base64": base64.b64encode(normalized_audio.tobytes()).decode("ascii"),
        }
        headers = {
            "Authorization": f"Bearer {self._config.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            response = self._transport(
                url=self._config.transcription_url,
                headers=headers,
                payload=payload,
                timeout_seconds=self._config.timeout_seconds,
            )
        except (HTTPError, URLError) as exc:
            raise CloudASRTranscriptionError(f"Cloud transcription request failed: {exc}") from exc
        except Exception as exc:  # pragma: no cover - defensive wrapper
            raise CloudASRTranscriptionError(f"Cloud transcription transport failed: {exc}") from exc

        text = str(response.get("text", "")).strip()
        if not text:
            raise CloudASRTranscriptionError("Cloud transcription response missing non-empty 'text'")

        language_value = response.get("language")
        language = str(language_value) if language_value is not None else None

        return [
            TranscriptEvent(
                text=text,
                is_final=True,
                confidence=1.0,
                language=language,
            )
        ]


def build_openai_compatible_config_from_engine(
    engine_config: Mapping[str, Any],
    environ: Mapping[str, str] | None = None,
) -> OpenAICompatibleASRConfig | None:
    """Build cloud ASR config from engine config and environment.

    Returns None when required cloud settings are incomplete.
    """
    resolved_engine_config = _resolve_engine_config(engine_config)
    env = environ if environ is not None else os.environ
    api_base_value = resolved_engine_config.get("cloud_api_base")
    api_base = str(api_base_value).strip() if api_base_value is not None else ""
    api_key = str(env.get("VOICEKEY_OPENAI_API_KEY", "")).strip()

    if not api_base or not api_key:
        return None

    model = str(resolved_engine_config.get("cloud_model", "gpt-4o-mini-transcribe")).strip()
    timeout_raw = resolved_engine_config.get("cloud_timeout_seconds", 30)
    try:
        timeout_seconds = float(timeout_raw)
    except (TypeError, ValueError) as exc:
        raise CloudASRConfigurationError(
            f"Invalid cloud_timeout_seconds: {timeout_raw!r}"
        ) from exc

    return OpenAICompatibleASRConfig(
        api_base=api_base,
        api_key=api_key,
        model=model,
        timeout_seconds=timeout_seconds,
    )


def create_openai_compatible_asr_from_engine_config(
    engine_config: Mapping[str, Any],
    environ: Mapping[str, str] | None = None,
    transport: CloudTransport | None = None,
) -> OpenAICompatibleASRBackend | None:
    """Create cloud ASR backend from engine config when fully configured."""
    config = build_openai_compatible_config_from_engine(engine_config, environ=environ)
    if config is None:
        return None
    return OpenAICompatibleASRBackend(config=config, transport=transport)


def _resolve_engine_config(config: Mapping[str, Any]) -> Mapping[str, Any]:
    engine = config.get("engine")
    if isinstance(engine, Mapping):
        return engine
    return config


def _default_transport(
    *,
    url: str,
    headers: Mapping[str, str],
    payload: Mapping[str, Any],
    timeout_seconds: float,
) -> Mapping[str, Any]:
    request = Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        headers=dict(headers),
        method="POST",
    )

    with urlopen(request, timeout=timeout_seconds) as response:
        body = response.read().decode("utf-8")

    decoded = json.loads(body)
    if not isinstance(decoded, dict):
        raise CloudASRTranscriptionError("Cloud transcription response must be a JSON object")

    return decoded


__all__ = [
    "CloudASRConfigurationError",
    "CloudASRTranscriptionError",
    "OpenAICompatibleASRError",
    "OpenAICompatibleASRConfig",
    "OpenAICompatibleASRBackend",
    "build_openai_compatible_config_from_engine",
    "create_openai_compatible_asr_from_engine_config",
]
