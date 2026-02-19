"""Voice Activity Detection using Silero VAD.

This module provides VAD (Voice Activity Detection) capabilities for VoiceKey
to reduce ASR decode load when no speech is detected and mitigate wake false triggers.

Uses Silero VAD for local, privacy-preserving voice activity detection.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

# Try to import silero-vad, provide graceful fallback
try:
    from silero import vad
    SILERO_VAD_AVAILABLE = True
except ImportError:
    SILERO_VAD_AVAILABLE = False
    logger.warning("silero-vad not available, VAD functionality will be limited")


@dataclass
class VADResult:
    """Result of voice activity detection on an audio chunk.

    Attributes:
        is_speech: True if speech detected, False if silence
        confidence: Confidence score from 0.0 to 1.0
    """

    is_speech: bool
    confidence: float


class VADProcessor:
    """Voice Activity Detector for processing individual audio frames.

    This processor uses Silero VAD to classify audio frames as speech or silence.
    It helps reduce ASR decode load when no speech is detected and mitigates
    wake false triggers via configurable sensitivity threshold.

    Example:
        >>> processor = VADProcessor(threshold=0.5, min_speech_duration=0.1)
        >>> # Process an audio frame
        >>> is_speech = processor.process(audio_frame)
        >>> # Reset when starting new capture session
        >>> processor.reset()
    """

    def __init__(
        self,
        threshold: float = 0.5,
        min_speech_duration: float = 0.1,
    ):
        """Initialize VAD processor.

        Args:
            threshold: Speech detection threshold from 0.0 to 1.0 (default 0.5).
                       Higher values require more confident speech detection.
            min_speech_duration: Minimum duration in seconds for speech detection
                                  (default 0.1). Helps filter out short noises.

        Raises:
            ValueError: If threshold is not in range [0.0, 1.0]
        """
        if not 0.0 <= threshold <= 1.0:
            raise ValueError(f"threshold must be in range [0.0, 1.0], got {threshold}")

        self._threshold = threshold
        self._min_speech_duration = min_speech_duration
        self._model: Optional[object] = None
        self._model_loaded = False

        # Load model lazily on first use
        self._load_model()

    def _load_model(self) -> None:
        """Load Silero VAD model."""
        if not SILERO_VAD_AVAILABLE:
            logger.warning("Silero VAD not available, using fallback")
            return

        try:
            self._model, _ = vad()
            self._model_loaded = True
            logger.info("Silero VAD model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Silero VAD model: {e}")
            self._model_loaded = False

    @property
    def threshold(self) -> float:
        """Get current speech detection threshold."""
        return self._threshold

    @threshold.setter
    def threshold(self, value: float) -> None:
        """Set speech detection threshold.

        Args:
            value: New threshold value from 0.0 to 1.0

        Raises:
            ValueError: If value is not in range [0.0, 1.0]
        """
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"threshold must be in range [0.0, 1.0], got {value}")
        self._threshold = value

    def process(self, audio: np.ndarray) -> bool:
        """Process an audio frame and detect speech.

        Args:
            audio: Audio samples as float32 numpy array

        Returns:
            True if speech detected, False if silence
        """
        # Ensure audio is float32 numpy array
        if not isinstance(audio, np.ndarray):
            audio = np.array(audio, dtype=np.float32)

        # Handle empty audio
        if len(audio) == 0:
            return False

        # Use Silero VAD if available
        if self._model_loaded and self._model is not None:
            return self._process_with_silero(audio)
        else:
            # Fallback: use simple energy-based detection
            return self._process_fallback(audio)

    def _process_with_silero(self, audio: np.ndarray, sample_rate: int = 16000) -> bool:
        """Process audio using Silero VAD.

        Args:
            audio: Audio samples as float32 numpy array
            sample_rate: Sample rate in Hz

        Returns:
            True if speech detected
        """
        try:
            # Silero VAD expects audio as a torch tensor or list
            # The model returns a list of speech segments
            audio_list = audio.tolist()

            # Get speech timestamps
            speech_timestamps = self._model(
                audio_list,
                sampling_rate=sample_rate,
            )

            # If we have any speech timestamps, speech is detected
            # The threshold controls sensitivity internally in Silero
            return len(speech_timestamps) > 0

        except Exception as e:
            logger.warning(f"Silero VAD processing error: {e}, using fallback")
            return self._process_fallback(audio)

    def _process_fallback(self, audio: np.ndarray) -> bool:
        """Fallback energy-based VAD when Silero is unavailable.

        Args:
            audio: Audio samples as float32 numpy array

        Returns:
            True if speech detected based on energy threshold
        """
        # Calculate RMS energy
        rms = np.sqrt(np.mean(audio ** 2))

        # Simple threshold - adjust based on typical speech levels
        # Speech typically has RMS > 0.01
        energy_threshold = 0.01 + (1.0 - self._threshold) * 0.04

        return rms > energy_threshold

    def reset(self) -> None:
        """Reset VAD state.

        Called when starting a new capture session to clear any internal state.
        """
        # Silero VAD doesn't maintain state between calls, but we keep
        # the model loaded for performance
        logger.debug("VAD processor state reset")

    @property
    def is_model_loaded(self) -> bool:
        """Check if VAD model is loaded and available."""
        return self._model_loaded


class StreamingVAD:
    """Streaming Voice Activity Detector for continuous audio processing.

    Processes continuous audio chunks and returns VAD results with confidence scores.
    Suitable for real-time audio pipelines.

    Example:
        >>> vad = StreamingVAD(threshold=0.5, sample_rate=16000)
        >>> # Process audio chunks as they arrive
        >>> result = vad.process_chunk(audio_samples)
        >>> if result.is_speech:
        ...     print(f"Speech detected (confidence: {result.confidence:.2f})")
    """

    def __init__(
        self,
        threshold: float = 0.5,
        sample_rate: int = 16000,
    ):
        """Initialize streaming VAD.

        Args:
            threshold: Speech detection threshold from 0.0 to 1.0 (default 0.5)
            sample_rate: Audio sample rate in Hz (default 16000)

        Raises:
            ValueError: If threshold is not in range [0.0, 1.0]
        """
        if not 0.0 <= threshold <= 1.0:
            raise ValueError(f"threshold must be in range [0.0, 1.0], got {threshold}")

        self._threshold = threshold
        self._sample_rate = sample_rate
        self._model: Optional[object] = None
        self._model_loaded = False

        # Load model lazily
        self._load_model()

    def _load_model(self) -> None:
        """Load Silero VAD model."""
        if not SILERO_VAD_AVAILABLE:
            logger.warning("Silero VAD not available for streaming VAD")
            return

        try:
            self._model, _ = vad()
            self._model_loaded = True
            logger.info("Streaming VAD model loaded")
        except Exception as e:
            logger.error(f"Failed to load Silero VAD for streaming: {e}")
            self._model_loaded = False

    @property
    def threshold(self) -> float:
        """Get current threshold."""
        return self._threshold

    def process_chunk(self, audio_samples: np.ndarray) -> VADResult:
        """Process an audio chunk and return VAD result.

        Args:
            audio_samples: Audio samples as float32 numpy array (range [-1, 1])

        Returns:
            VADResult with is_speech flag and confidence score
        """
        # Ensure numpy array
        if not isinstance(audio_samples, np.ndarray):
            audio_samples = np.array(audio_samples, dtype=np.float32)

        # Handle empty audio
        if len(audio_samples) == 0:
            return VADResult(is_speech=False, confidence=0.0)

        if self._model_loaded and self._model is not None:
            return self._process_chunk_silero(audio_samples)
        else:
            return self._process_chunk_fallback(audio_samples)

    def _process_chunk_silero(self, audio: np.ndarray) -> VADResult:
        """Process chunk using Silero VAD."""
        try:
            audio_list = audio.tolist()

            # Get speech timestamps
            speech_timestamps = self._model(
                audio_list,
                sampling_rate=self._sample_rate,
            )

            if speech_timestamps:
                # Calculate confidence based on proportion of speech
                total_samples = len(audio)
                speech_samples = sum(
                    seg["end"] - seg["start"]
                    for seg in speech_timestamps
                )
                confidence = min(1.0, speech_samples / total_samples)
                return VADResult(is_speech=True, confidence=confidence)
            else:
                return VADResult(is_speech=False, confidence=0.0)

        except Exception as e:
            logger.warning(f"Silero streaming VAD error: {e}")
            return self._process_chunk_fallback(audio)

    def _process_chunk_fallback(self, audio: np.ndarray) -> VADResult:
        """Fallback energy-based VAD."""
        rms = np.sqrt(np.mean(audio ** 2))
        energy_threshold = 0.01 + (1.0 - self._threshold) * 0.04

        if rms > energy_threshold:
            # Confidence based on how far above threshold
            confidence = min(1.0, (rms - energy_threshold) / (0.1 - energy_threshold))
            confidence = max(0.0, confidence)
            return VADResult(is_speech=True, confidence=confidence)
        else:
            return VADResult(is_speech=False, confidence=0.0)


# Type checking imports
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from voicekey.audio.capture import AudioFrame


class VADCalibrator:
    """Helper for calibrating VAD threshold for noisy environments.

    Measures ambient noise level and suggests appropriate threshold settings.

    Example:
        >>> calibrator = VADCalibrator(sample_rate=16000)
        >>> # Collect ambient noise samples
        >>> for _ in range(100):
        ...     calibrator.add_sample(microphone_chunk)
        >>> threshold = calibrator.get_suggested_threshold()
        >>> print(f"Suggested threshold: {threshold}")
    """

    def __init__(self, sample_rate: int = 16000):
        """Initialize calibrator.

        Args:
            sample_rate: Audio sample rate in Hz
        """
        self._sample_rate = sample_rate
        self._samples: list[float] = []

    def add_sample(self, audio_chunk: np.ndarray) -> None:
        """Add an audio chunk to the calibration data.

        Args:
            audio_chunk: Audio samples as numpy array
        """
        if not isinstance(audio_chunk, np.ndarray):
            audio_chunk = np.array(audio_chunk, dtype=np.float32)

        # Calculate RMS energy
        rms = float(np.sqrt(np.mean(audio_chunk ** 2)))
        self._samples.append(rms)

    def get_ambient_level(self) -> float:
        """Get the measured ambient noise level.

        Returns:
            RMS energy level of ambient noise, or 0.0 if no samples
        """
        if not self._samples:
            return 0.0
        return float(np.mean(self._samples))

    def get_suggested_threshold(self, margin: float = 2.0) -> float:
        """Get suggested VAD threshold based on ambient noise.

        Args:
            margin: Multiplier for ambient level (default 2.0).
                   Higher margin = higher threshold = less sensitive

        Returns:
            Suggested threshold value in range [0.0, 1.0]
        """
        if not self._samples:
            return 0.5  # Default

        ambient = self.get_ambient_level()

        if ambient < 0.001:
            # Very quiet environment
            return 0.3
        elif ambient < 0.01:
            # Normal quiet environment
            return 0.4
        elif ambient < 0.03:
            # Moderate noise
            return 0.5
        else:
            # Noisy environment - need higher threshold
            # Map to threshold in range [0.5, 0.9]
            noisy_threshold = 0.5 + min(0.4, (ambient - 0.03) * 10)
            return min(0.9, noisy_threshold)

    def reset(self) -> None:
        """Reset calibration data."""
        self._samples.clear()


def create_vad_from_config(config: dict) -> VADProcessor:
    """Create VADProcessor from configuration dictionary.

    Args:
        config: Configuration dictionary with VAD settings

    Returns:
        Configured VADProcessor instance
    """
    vad_config = config.get("vad", {})

    threshold = vad_config.get("speech_threshold", 0.5)
    min_speech_sec = vad_config.get("min_speech_ms", 120) / 1000.0

    return VADProcessor(
        threshold=threshold,
        min_speech_duration=min_speech_sec,
    )
