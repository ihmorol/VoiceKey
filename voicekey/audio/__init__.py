"""Audio processing components."""

from voicekey.audio.asr_faster_whisper import (
    ASREngine,
    ModelLoadError,
    TranscriptionError,
    TranscriptionTimeoutError,
    TranscriptEvent,
    create_asr_from_config,
    get_all_model_info,
    get_available_models,
    get_model_size_info,
)
from voicekey.audio.asr_openai_compatible import (
    CloudASRConfigurationError,
    CloudASRTranscriptionError,
    OpenAICompatibleASRBackend,
    OpenAICompatibleASRConfig,
    OpenAICompatibleASRError,
    build_openai_compatible_config_from_engine,
    create_openai_compatible_asr_from_engine_config,
)
from voicekey.audio.asr_router import (
    ASRBackend,
    ASRConfigurationError,
    ASRRouter,
    ASRRouterConfig,
    ASRRouterError,
    ASRRoutingDecision,
    ASRRoutingMode,
    ASRTranscriptionError,
    ASRTranscriptionResult,
    create_asr_router_from_engine_config,
)
from voicekey.audio.capture import (
    AudioCapture,
    AudioDeviceBusyError,
    AudioDeviceDisconnectedError,
    AudioDeviceInfo,
    AudioDeviceNotFoundError,
    AudioFrame,
    get_default_device,
    get_invalid_frame_count,
    list_devices,
    reset_invalid_frame_count,
)
from voicekey.audio.threshold import ConfidenceFilter
from voicekey.audio.vad import (
    StreamingVAD,
    VADCalibrator,
    VADProcessor,
    VADResult,
    create_vad_from_config,
)
from voicekey.audio.wake import WakePhraseDetector, WakeWindowController

__all__ = [
    # ASR (local)
    "ASREngine",
    "TranscriptEvent",
    "ModelLoadError",
    "TranscriptionError",
    "TranscriptionTimeoutError",
    "get_available_models",
    "get_model_size_info",
    "get_all_model_info",
    "create_asr_from_config",
    # ASR (cloud)
    "OpenAICompatibleASRError",
    "CloudASRConfigurationError",
    "CloudASRTranscriptionError",
    "OpenAICompatibleASRConfig",
    "OpenAICompatibleASRBackend",
    "build_openai_compatible_config_from_engine",
    "create_openai_compatible_asr_from_engine_config",
    # ASR Router
    "ASRBackend",
    "ASRRouterError",
    "ASRConfigurationError",
    "ASRTranscriptionError",
    "ASRRoutingMode",
    "ASRRouterConfig",
    "ASRRoutingDecision",
    "ASRTranscriptionResult",
    "ASRRouter",
    "create_asr_router_from_engine_config",
    # Audio capture
    "AudioCapture",
    "AudioDeviceInfo",
    "AudioDeviceBusyError",
    "AudioDeviceDisconnectedError",
    "AudioDeviceNotFoundError",
    "AudioFrame",
    "get_default_device",
    "list_devices",
    "get_invalid_frame_count",
    "reset_invalid_frame_count",
    # Threshold
    "ConfidenceFilter",
    # VAD
    "VADProcessor",
    "VADResult",
    "StreamingVAD",
    "VADCalibrator",
    "create_vad_from_config",
    # Wake
    "WakePhraseDetector",
    "WakeWindowController",
]
