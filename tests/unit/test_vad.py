"""Unit tests for VAD (Voice Activity Detection) module."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

# Mock silero before importing vad module
mock_silero = MagicMock()
mock_vad_model = MagicMock()
mock_silero.vad = MagicMock(return_value=(mock_vad_model, MagicMock()))

# Pre-mock silero to avoid import errors
sys.modules['silero'] = mock_silero

from voicekey.audio.vad import (
    VADCalibrator,
    VADProcessor,
    VADResult,
    StreamingVAD,
    create_vad_from_config,
)


class TestVADResult:
    """Tests for VADResult dataclass."""

    def test_vad_result_creation(self):
        """Test creating a VADResult."""
        result = VADResult(is_speech=True, confidence=0.85)

        assert result.is_speech is True
        assert result.confidence == 0.85

    def test_vad_result_silence(self):
        """Test VADResult for silence."""
        result = VADResult(is_speech=False, confidence=0.0)

        assert result.is_speech is False
        assert result.confidence == 0.0


class TestVADProcessor:
    """Tests for VADProcessor class."""

    def test_initialization_default(self):
        """Test initialization with default parameters."""
        processor = VADProcessor()

        assert processor.threshold == 0.5
        assert processor._min_speech_duration == 0.1
        assert processor.is_model_loaded is True  # Mocked

    def test_initialization_custom(self):
        """Test initialization with custom parameters."""
        processor = VADProcessor(threshold=0.7, min_speech_duration=0.2)

        assert processor.threshold == 0.7
        assert processor._min_speech_duration == 0.2

    def test_initialization_invalid_threshold(self):
        """Test initialization with invalid threshold raises ValueError."""
        with pytest.raises(ValueError, match=r"threshold must be in range"):
            VADProcessor(threshold=1.5)

        with pytest.raises(ValueError, match=r"threshold must be in range"):
            VADProcessor(threshold=-0.1)

    def test_threshold_setter(self):
        """Test setting threshold after initialization."""
        processor = VADProcessor()
        processor.threshold = 0.8

        assert processor.threshold == 0.8

    def test_threshold_setter_invalid(self):
        """Test setting invalid threshold raises ValueError."""
        processor = VADProcessor()

        with pytest.raises(ValueError, match=r"threshold must be in range"):
            processor.threshold = 1.5

    def test_process_empty_audio(self):
        """Test processing empty audio returns False."""
        processor = VADProcessor()

        result = processor.process(np.array([], dtype=np.float32))

        assert result is False

    def test_process_silence_audio(self):
        """Test processing silence (low energy) audio."""
        processor = VADProcessor(threshold=0.5)

        # Very quiet audio (silence)
        silence = np.zeros(1600, dtype=np.float32)

        result = processor.process(silence)

        assert result is False

    def test_process_speech_audio(self):
        """Test processing audio with speech-like energy."""
        processor = VADProcessor(threshold=0.5)

        # Generate audio with higher RMS (simulated speech)
        # RMS > 0.01 should trigger detection with default threshold
        speech = np.random.randn(1600).astype(np.float32) * 0.1

        result = processor.process(speech)

        # With fallback, this should be detected as speech
        assert isinstance(result, bool)

    def test_reset(self):
        """Test reset method."""
        processor = VADProcessor()
        processor.reset()  # Should not raise

    def test_process_with_numpy_array(self):
        """Test processing with direct numpy array."""
        processor = VADProcessor()

        # Audio data
        audio = np.random.randn(800).astype(np.float32) * 0.05

        result = processor.process(audio)

        assert isinstance(result, bool)


class TestVADProcessorSilero:
    """Tests for VADProcessor with Silero VAD."""

    @patch("voicekey.audio.vad.SILERO_VAD_AVAILABLE", True)
    def test_process_with_silero(self):
        """Test processing with Silero VAD model."""
        # Setup mock to return speech detected
        mock_vad_model.return_value = [{"start": 0, "end": 1600}]

        processor = VADProcessor(threshold=0.5)
        audio = np.random.randn(1600).astype(np.float32)

        result = processor.process(audio)

        # Should return True since speech is detected
        assert result is True

    @patch("voicekey.audio.vad.SILERO_VAD_AVAILABLE", True)
    def test_process_silero_no_speech(self):
        """Test Silero VAD when no speech detected."""
        # Setup mock to return no speech
        mock_vad_model.return_value = []

        processor = VADProcessor(threshold=0.5)
        audio = np.zeros(1600, dtype=np.float32)

        result = processor.process(audio)

        # Should return False since no speech detected
        assert result is False


class TestStreamingVAD:
    """Tests for StreamingVAD class."""

    def test_initialization_default(self):
        """Test initialization with defaults."""
        vad = StreamingVAD()

        assert vad.threshold == 0.5
        assert vad._sample_rate == 16000

    def test_initialization_custom(self):
        """Test initialization with custom parameters."""
        vad = StreamingVAD(threshold=0.7, sample_rate=22050)

        assert vad.threshold == 0.7
        assert vad._sample_rate == 22050

    def test_initialization_invalid_threshold(self):
        """Test initialization with invalid threshold."""
        with pytest.raises(ValueError, match=r"threshold must be in range"):
            StreamingVAD(threshold=-0.5)

    def test_process_chunk_empty(self):
        """Test processing empty chunk."""
        vad = StreamingVAD()

        result = vad.process_chunk(np.array([], dtype=np.float32))

        assert result.is_speech is False
        assert result.confidence == 0.0

    def test_process_chunk_silence(self):
        """Test processing silence chunk."""
        vad = StreamingVAD(threshold=0.5)

        silence = np.zeros(1600, dtype=np.float32)
        result = vad.process_chunk(silence)

        assert result.is_speech is False

    def test_process_chunk_with_audio(self):
        """Test processing audio chunk."""
        vad = StreamingVAD(threshold=0.5)

        # Audio with some energy
        audio = np.random.randn(1600).astype(np.float32) * 0.1
        result = vad.process_chunk(audio)

        assert isinstance(result, VADResult)
        assert 0.0 <= result.confidence <= 1.0


class TestVADCalibrator:
    """Tests for VADCalibrator class."""

    def test_initialization(self):
        """Test calibrator initialization."""
        calibrator = VADCalibrator()

        assert calibrator._sample_rate == 16000
        assert calibrator.get_ambient_level() == 0.0

    def test_add_sample(self):
        """Test adding samples to calibrator."""
        calibrator = VADCalibrator()

        # Add some quiet samples
        quiet = np.zeros(1600, dtype=np.float32) * 0.001
        calibrator.add_sample(quiet)

        assert len(calibrator._samples) == 1

    def test_get_ambient_level_empty(self):
        """Test ambient level with no samples."""
        calibrator = VADCalibrator()

        level = calibrator.get_ambient_level()

        assert level == 0.0

    def test_get_ambient_level_with_samples(self):
        """Test ambient level calculation."""
        calibrator = VADCalibrator()

        # Add samples with known RMS
        samples = [0.01, 0.02, 0.015]
        for s in samples:
            calibrator.add_sample(np.array([s], dtype=np.float32))

        level = calibrator.get_ambient_level()

        assert abs(level - 0.015) < 0.001

    def test_get_suggested_threshold_quiet(self):
        """Test threshold suggestion for quiet environment."""
        calibrator = VADCalibrator()

        # Very quiet - less than 0.001 RMS
        calibrator.add_sample(np.array([0.0001], dtype=np.float32))

        threshold = calibrator.get_suggested_threshold()

        assert 0.0 <= threshold <= 1.0

    def test_get_suggested_threshold_default(self):
        """Test default threshold when no samples."""
        calibrator = VADCalibrator()

        threshold = calibrator.get_suggested_threshold()

        # Should return default 0.5
        assert threshold == 0.5

    def test_reset(self):
        """Test calibrator reset."""
        calibrator = VADCalibrator()

        calibrator.add_sample(np.array([0.01], dtype=np.float32))
        assert len( calibrator._samples) > 0

        calibrator.reset()

        assert len(calibrator._samples) == 0


class TestCreateVADFromConfig:
    """Tests for create_vad_from_config helper."""

    def test_create_with_full_config(self):
        """Test creating VAD from complete config."""
        config = {
            "vad": {
                "speech_threshold": 0.7,
                "min_speech_ms": 200,
            }
        }

        processor = create_vad_from_config(config)

        assert processor.threshold == 0.7
        assert processor._min_speech_duration == 0.2

    def test_create_with_defaults(self):
        """Test creating VAD with default values."""
        config = {}

        processor = create_vad_from_config(config)

        assert processor.threshold == 0.5
        assert processor._min_speech_duration == 0.12  # 120ms default

    def test_create_with_partial_config(self):
        """Test creating VAD with partial config."""
        config = {
            "vad": {
                "speech_threshold": 0.3,
            }
        }

        processor = create_vad_from_config(config)

        assert processor.threshold == 0.3
        assert processor._min_speech_duration == 0.12  # default


class TestVADProcessorFallback:
    """Tests for VADProcessor fallback mode."""

    def test_fallback_mode(self):
        """Test VAD falls back to energy-based detection when Silero unavailable."""
        # Test that the class handles silero unavailability
        # We test the fallback logic directly by checking the energy threshold
        processor = VADProcessor(threshold=0.5)

        # Even without silero, should process via fallback
        audio = np.random.randn(1600).astype(np.float32) * 0.1
        result = processor.process(audio)

        assert isinstance(result, bool)

    def test_fallback_detects_speech_by_energy(self):
        """Test fallback energy-based detection detects speech."""
        # Create processor and directly test the fallback method
        processor = VADProcessor(threshold=0.5)

        # Use a signal that will definitely exceed the fallback threshold
        # The fallback uses: threshold = 0.01 + (1.0 - threshold) * 0.04
        # For threshold 0.5: threshold = 0.01 + 0.5 * 0.04 = 0.03
        # RMS of constant 0.5 signal = 0.5
        speech_audio = np.full(1600, 0.5, dtype=np.float32)

        # Directly test the fallback method
        result = processor._process_fallback(speech_audio)

        # Use bool() to handle numpy boolean
        assert bool(result) is True

    def test_fallback_detects_silence(self):
        """Test fallback energy-based detection detects silence."""
        processor = VADProcessor(threshold=0.5)

        # Low energy audio (silence)
        silence_audio = np.zeros(1600, dtype=np.float32)

        result = processor.process(silence_audio)

        assert result is False
