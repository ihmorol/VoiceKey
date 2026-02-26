"""Backend-agnostic ASR routing for local, hybrid, and cloud-primary modes."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Literal, Protocol

import numpy as np

from voicekey.audio.asr_faster_whisper import TranscriptEvent
from voicekey.audio.asr_openai_compatible import create_openai_compatible_asr_from_engine_config

ASRBackendName = Literal["faster-whisper", "openai-api-compatible"]
ASRExecutionBackend = Literal["local", "cloud"]


class ASRRouterError(Exception):
    """Base error for ASR router failures."""


class ASRConfigurationError(ASRRouterError):
    """Raised when ASR routing configuration is invalid for requested mode."""


class ASRTranscriptionError(ASRRouterError):
    """Raised when transcription fails in the selected backend path."""

    def __init__(self, backend: ASRExecutionBackend, message: str) -> None:
        self.backend = backend
        super().__init__(message)


class ASRRoutingMode(StrEnum):
    """Resolved runtime ASR routing mode."""

    LOCAL_ONLY = "local-only"
    HYBRID = "hybrid"
    CLOUD_PRIMARY = "cloud-primary"


class ASRBackend(Protocol):
    """Backend transcription contract expected by ASRRouter."""

    def transcribe(self, audio: np.ndarray) -> list[TranscriptEvent]:
        """Transcribe a chunk of audio samples."""


@dataclass(frozen=True)
class ASRRouterConfig:
    """Config values used to resolve ASR routing mode."""

    asr_backend: ASRBackendName = "faster-whisper"
    network_fallback_enabled: bool = False
    cloud_api_base: str | None = None
    cloud_api_key: str | None = None
    cloud_model: str = "gpt-4o-mini-transcribe"
    cloud_timeout_seconds: float = 30.0

    def __post_init__(self) -> None:
        if self.asr_backend not in ("faster-whisper", "openai-api-compatible"):
            raise ASRConfigurationError(f"Unsupported asr_backend: {self.asr_backend}")
        if self.cloud_timeout_seconds <= 0:
            raise ASRConfigurationError("cloud_timeout_seconds must be > 0")

    @property
    def cloud_configured(self) -> bool:
        """True when cloud mode has both endpoint and API key."""
        return bool((self.cloud_api_base or "").strip() and (self.cloud_api_key or "").strip())

    @classmethod
    def from_engine_config(
        cls,
        engine_config: Mapping[str, Any],
        environ: Mapping[str, str] | None = None,
    ) -> ASRRouterConfig:
        """Build router config from engine config and environment variables."""
        env = environ if environ is not None else os.environ
        timeout_raw = engine_config.get("cloud_timeout_seconds", 30)
        try:
            timeout_seconds = float(timeout_raw)
        except (TypeError, ValueError) as exc:
            raise ASRConfigurationError(
                f"Invalid cloud_timeout_seconds: {timeout_raw!r}"
            ) from exc

        api_base_value = engine_config.get("cloud_api_base")
        api_base = str(api_base_value).strip() if api_base_value is not None else None
        if api_base == "":
            api_base = None

        api_key = str(env.get("VOICEKEY_OPENAI_API_KEY", "")).strip() or None
        cloud_model = str(engine_config.get("cloud_model", "gpt-4o-mini-transcribe")).strip()

        return cls(
            asr_backend=str(engine_config.get("asr_backend", "faster-whisper")),
            network_fallback_enabled=bool(engine_config.get("network_fallback_enabled", False)),
            cloud_api_base=api_base,
            cloud_api_key=api_key,
            cloud_model=cloud_model,
            cloud_timeout_seconds=timeout_seconds,
        )


@dataclass(frozen=True)
class ASRRoutingDecision:
    """Resolved route metadata for runtime transcription."""

    mode: ASRRoutingMode
    cloud_configured: bool
    cloud_available: bool
    reason: str | None = None


@dataclass(frozen=True)
class ASRTranscriptionResult:
    """Structured ASR transcription outcome."""

    events: tuple[TranscriptEvent, ...]
    backend_used: ASRExecutionBackend
    mode: ASRRoutingMode
    fallback_used: bool = False
    fallback_reason: str | None = None


class ASRRouter:
    """Route transcription to local/cloud backends according to configuration."""

    def __init__(
        self,
        config: ASRRouterConfig,
        local_backend: ASRBackend,
        cloud_backend: ASRBackend | None = None,
    ) -> None:
        self._config = config
        self._local_backend = local_backend
        self._cloud_backend = cloud_backend

        decision = _resolve_routing_decision(config=config, cloud_backend=cloud_backend)
        if decision.mode is ASRRoutingMode.CLOUD_PRIMARY and not decision.cloud_available:
            raise ASRConfigurationError(
                "Cloud-primary mode requires configured cloud endpoint, API key, and cloud backend"
            )
        self._decision = decision

    @property
    def mode(self) -> ASRRoutingMode:
        """Current resolved routing mode."""
        return self._decision.mode

    @property
    def routing_decision(self) -> ASRRoutingDecision:
        """Resolved routing metadata."""
        return self._decision

    @property
    def is_model_loaded(self) -> bool:
        """Expose model-loaded compatibility for RuntimeCoordinator."""
        return bool(getattr(self._local_backend, "is_model_loaded", True))

    def load_model(self) -> None:
        """Load local model backend when available.

        Cloud-primary mode can proceed without local model load, so missing
        loader hooks on the backend are treated as no-op.
        """
        loader = getattr(self._local_backend, "load_model", None)
        if callable(loader):
            loader()

    def transcribe(self, audio: np.ndarray) -> ASRTranscriptionResult:
        """Transcribe audio through the active routing mode."""
        if self.mode is ASRRoutingMode.CLOUD_PRIMARY:
            return self._transcribe_cloud(audio)

        if self.mode is ASRRoutingMode.HYBRID:
            try:
                return self._transcribe_local(audio)
            except Exception as local_exc:
                try:
                    cloud_result = self._transcribe_cloud(audio)
                except Exception as cloud_exc:
                    raise ASRTranscriptionError(
                        "cloud",
                        (
                            "Hybrid transcription failed: local and cloud backends failed "
                            f"(local={local_exc}, cloud={cloud_exc})"
                        ),
                    ) from cloud_exc

                return ASRTranscriptionResult(
                    events=cloud_result.events,
                    backend_used="cloud",
                    mode=self.mode,
                    fallback_used=True,
                    fallback_reason=str(local_exc),
                )

        return self._transcribe_local(audio)

    def _transcribe_local(self, audio: np.ndarray) -> ASRTranscriptionResult:
        try:
            events = tuple(self._local_backend.transcribe(audio))
        except Exception as exc:
            raise ASRTranscriptionError("local", f"Local transcription failed: {exc}") from exc

        return ASRTranscriptionResult(
            events=events,
            backend_used="local",
            mode=self.mode,
        )

    def _transcribe_cloud(self, audio: np.ndarray) -> ASRTranscriptionResult:
        if self._cloud_backend is None:
            raise ASRTranscriptionError("cloud", "Cloud backend is not available")

        try:
            events = tuple(self._cloud_backend.transcribe(audio))
        except Exception as exc:
            raise ASRTranscriptionError("cloud", f"Cloud transcription failed: {exc}") from exc

        return ASRTranscriptionResult(
            events=events,
            backend_used="cloud",
            mode=self.mode,
        )


def create_asr_router_from_engine_config(
    engine_config: Mapping[str, Any],
    local_backend: ASRBackend,
    cloud_backend: ASRBackend | None = None,
    environ: Mapping[str, str] | None = None,
) -> ASRRouter:
    """Create ASRRouter from engine config, auto-creating cloud backend when possible."""
    resolved_engine_config = _resolve_engine_config(engine_config)
    config = ASRRouterConfig.from_engine_config(resolved_engine_config, environ=environ)

    resolved_cloud_backend = cloud_backend
    if resolved_cloud_backend is None:
        resolved_cloud_backend = create_openai_compatible_asr_from_engine_config(
            resolved_engine_config,
            environ=environ,
        )

    return ASRRouter(
        config=config,
        local_backend=local_backend,
        cloud_backend=resolved_cloud_backend,
    )


def create_asr_router_from_config(
    engine_config: Mapping[str, Any],
    *,
    sample_rate: int = 16000,
    environ: Mapping[str, str] | None = None,
) -> ASRRouter:
    """Compatibility factory used by runtime wiring.

    Builds local faster-whisper backend from engine config, then resolves
    optional cloud backend according to hybrid/cloud settings.
    """
    resolved_engine = _resolve_engine_config(engine_config)

    # Import lazily to avoid importing heavy runtime deps for non-ASR code paths.
    from voicekey.audio.asr_faster_whisper import ASREngine

    model_profile = str(resolved_engine.get("model_profile", "base"))
    compute_type_raw = resolved_engine.get("compute_type")
    compute_type = str(compute_type_raw) if compute_type_raw else None
    timeout_raw = resolved_engine.get("cloud_timeout_seconds", 30)
    try:
        timeout_seconds = float(timeout_raw)
    except (TypeError, ValueError):
        timeout_seconds = 30.0

    local_backend = ASREngine(
        model_size=model_profile,
        device="auto",
        compute_type=compute_type,
        sample_rate=sample_rate,
        transcription_timeout=timeout_seconds,
    )

    return create_asr_router_from_engine_config(
        engine_config=resolved_engine,
        local_backend=local_backend,
        environ=environ,
    )


def _resolve_routing_decision(
    *,
    config: ASRRouterConfig,
    cloud_backend: ASRBackend | None,
) -> ASRRoutingDecision:
    cloud_configured = config.cloud_configured
    cloud_available = cloud_configured and cloud_backend is not None

    if config.asr_backend == "openai-api-compatible":
        reason = None
        if not cloud_available:
            reason = "Cloud-primary requested but cloud backend is not configured"
        return ASRRoutingDecision(
            mode=ASRRoutingMode.CLOUD_PRIMARY,
            cloud_configured=cloud_configured,
            cloud_available=cloud_available,
            reason=reason,
        )

    if config.network_fallback_enabled and cloud_available:
        return ASRRoutingDecision(
            mode=ASRRoutingMode.HYBRID,
            cloud_configured=cloud_configured,
            cloud_available=cloud_available,
        )

    reason = None
    if config.network_fallback_enabled and not cloud_available:
        reason = "Hybrid fallback requested but cloud backend is not fully configured"

    return ASRRoutingDecision(
        mode=ASRRoutingMode.LOCAL_ONLY,
        cloud_configured=cloud_configured,
        cloud_available=cloud_available,
        reason=reason,
    )


def _resolve_engine_config(config: Mapping[str, Any]) -> Mapping[str, Any]:
    engine = config.get("engine")
    if isinstance(engine, Mapping):
        return engine
    return config


__all__ = [
    "ASRBackend",
    "ASRConfigurationError",
    "ASRRouter",
    "ASRRouterConfig",
    "ASRRouterError",
    "ASRRoutingDecision",
    "ASRRoutingMode",
    "ASRTranscriptionError",
    "ASRTranscriptionResult",
    "create_asr_router_from_config",
    "create_asr_router_from_engine_config",
]
