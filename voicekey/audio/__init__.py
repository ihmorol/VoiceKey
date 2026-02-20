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
    # ASR
    "ASREngine",
    "TranscriptEvent",
    "ModelLoadError",
    "TranscriptionError",
    "TranscriptionTimeoutError",
    "get_available_models",
    "get_model_size_info",
    "get_all_model_info",
    "create_asr_from_config",
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
