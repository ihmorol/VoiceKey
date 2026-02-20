"""Unit tests for audio capture module."""

from __future__ import annotations

import queue
import sys
import time
from unittest.mock import MagicMock, patch, PropertyMock

import numpy as np
import pytest

# Mock sounddevice before importing capture module
mock_sd = MagicMock()
mock_sd.query_devices = MagicMock(return_value={
    "name": "Test Microphone",
    "max_input_channels": 1,
    "default_input": 0,
    "sample_rate": 16000.0,
})
mock_sd.InputStream = MagicMock()
mock_sd.PortAudioError = Exception

# Pre-mock sounddevice to avoid PortAudio library requirement
sys.modules['sounddevice'] = mock_sd

from voicekey.audio.capture import (
    AudioCapture,
    AudioDeviceBusyError,
    AudioDeviceDisconnectedError,
    AudioDeviceNotFoundError,
    AudioFrame,
    get_default_device,
    get_invalid_frame_count,
    reset_invalid_frame_count,
    list_devices,
)


class TestAudioFrame:
    """Tests for AudioFrame dataclass."""

    def test_audio_frame_creation(self):
        """Test creating an AudioFrame."""
        audio_data = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        frame = AudioFrame(
            audio=audio_data,
            sample_rate=16000,
            timestamp=123.456,
        )

        assert np.array_equal(frame.audio, audio_data)
        assert frame.sample_rate == 16000
        assert frame.timestamp == 123.456
        assert frame.is_speech is None

    def test_audio_frame_with_vad(self):
        """Test creating an AudioFrame with VAD result."""
        audio_data = np.zeros(1600, dtype=np.float32)
        frame = AudioFrame(
            audio=audio_data,
            sample_rate=16000,
            timestamp=0.0,
            is_speech=True,
        )

        assert frame.is_speech is True


class TestDeviceListing:
    """Tests for device listing functions."""

    @patch("voicekey.audio.capture.sd.query_devices")
    def test_list_devices_single(self, mock_query):
        """Test listing devices with single device."""
        mock_query.return_value = {
            "name": "Test Microphone",
            "max_input_channels": 1,
            "default_input": 0,
            "sample_rate": 44100.0,
        }

        devices = list_devices()

        assert len(devices) == 1
        assert devices[0]["name"] == "Test Microphone"
        assert devices[0]["channels"] == 1

    @patch("voicekey.audio.capture.sd.query_devices")
    def test_list_devices_empty(self, mock_query):
        """Test listing devices when none available."""
        mock_query.side_effect = Exception("No devices")

        devices = list_devices()

        assert devices == []

    @patch("voicekey.audio.capture.sd.query_devices")
    def test_get_default_device(self, mock_query):
        """Test getting default device."""
        mock_query.return_value = {
            "name": "Default Mic",
            "max_input_channels": 2,
            "default_input": 0,
            "sample_rate": 48000.0,
        }

        device = get_default_device()

        assert device is not None
        assert device["name"] == "Default Mic"
        assert device["default"] is True


class TestAudioCapture:
    """Tests for AudioCapture class."""

    def test_initialization_default(self):
        """Test initialization with defaults."""
        capture = AudioCapture()

        assert capture._device_index is None
        assert capture._sample_rate == 16000
        assert capture._frames_per_chunk == 1600  # 16000 * 0.1
        assert capture._queue_size == 32
        assert not capture.is_running()

    def test_initialization_custom(self):
        """Test initialization with custom parameters."""
        capture = AudioCapture(
            device_index=2,
            sample_rate=22050,
            chunk_duration=0.05,
            queue_size=16,
        )

        assert capture._device_index == 2
        assert capture._sample_rate == 22050
        assert capture._frames_per_chunk == 1102  # 22050 * 0.05
        assert capture._queue_size == 16

    def test_get_audio_queue(self):
        """Test getting audio queue."""
        capture = AudioCapture()
        q = capture.get_audio_queue()

        assert isinstance(q, queue.Queue)
        assert q.maxsize == 32

    def test_context_manager(self):
        """Test context manager protocol."""
        with patch.object(AudioCapture, "start"):
            with patch.object(AudioCapture, "stop"):
                with AudioCapture() as capture:
                    assert capture is not None

    def test_double_start(self):
        """Test starting twice is idempotent."""
        capture = AudioCapture()

        with patch("voicekey.audio.capture.sd.InputStream") as mock_stream_class:
            mock_stream = MagicMock()
            mock_stream_class.return_value = mock_stream

            capture.start()
            assert capture.is_running()

            # Second start should be safe
            capture.start()
            assert capture.is_running()

            capture.stop()

    def test_double_stop(self):
        """Test stopping twice is safe."""
        capture = AudioCapture()

        with patch("voicekey.audio.capture.sd.InputStream") as mock_stream_class:
            mock_stream = MagicMock()
            mock_stream_class.return_value = mock_stream

            capture.start()
            capture.stop()
            assert not capture.is_running()

            # Second stop should be safe
            capture.stop()
            assert not capture.is_running()

    def test_stop_not_started(self):
        """Test stopping when not started is safe."""
        capture = AudioCapture()
        capture.stop()  # Should not raise
        assert not capture.is_running()


class TestAudioCaptureErrors:
    """Tests for AudioCapture error handling."""

    @patch("voicekey.audio.capture.AudioCapture._validate_device")
    def test_device_not_found(self, mock_validate):
        """Test AudioDeviceNotFoundError on start."""
        # Skip validation in init, mock error on start
        mock_validate.return_value = None

        with patch("voicekey.audio.capture.sd.query_devices") as mock_query:
            mock_query.side_effect = Exception("Invalid device")

            capture = AudioCapture(device_index=999)

            with pytest.raises(AudioDeviceNotFoundError):
                capture.start()

    @patch("voicekey.audio.capture.AudioCapture._validate_device")
    def test_device_busy(self, mock_validate):
        """Test AudioDeviceBusyError on start."""
        # Skip validation in init, mock error on start
        mock_validate.return_value = None

        with patch("voicekey.audio.capture.sd.query_devices") as mock_query:
            mock_query.side_effect = Exception("Device busy")

            capture = AudioCapture(device_index=0)

            with pytest.raises(AudioDeviceBusyError):
                capture.start()

    def test_device_disconnected(self):
        """Test AudioDeviceDisconnectedError."""
        with patch("voicekey.audio.capture.sd.query_devices") as mock_query, \
             patch("voicekey.audio.capture.sd.InputStream") as mock_stream_class:
            mock_query.return_value = {
                "name": "Test",
                "max_input_channels": 1,
                "default_input": 0,
                "sample_rate": 16000,
            }

            mock_stream = MagicMock()
            mock_stream.start.side_effect = Exception("Disconnected")
            mock_stream_class.return_value = mock_stream

            capture = AudioCapture()

            with pytest.raises(AudioDeviceDisconnectedError):
                capture.start()


class TestAudioCaptureCallback:
    """Tests for audio callback functionality."""

    def test_audio_callback(self):
        """Test audio callback puts frames in queue."""
        capture = AudioCapture()

        # Mock the stream
        mock_stream = MagicMock()
        capture._stream = mock_stream
        capture._is_running = True

        # Create sample audio data
        audio_data = np.random.randn(1600).astype(np.float32) * 0.1

        # Create mock callback info
        mock_time_info = MagicMock()
        mock_time_info.input_buffer_adc_time = 123.456

        # Call the callback
        capture._audio_callback(audio_data.reshape(-1, 1), 1600, mock_time_info)

        # Verify frame was put in queue
        assert not capture._audio_queue.empty()
        frame = capture._audio_queue.get_nowait()
        assert isinstance(frame, AudioFrame)
        assert frame.sample_rate == 16000
        assert frame.timestamp == 123.456

    def test_audio_callback_backpressure(self):
        """Test audio callback handles full queue (backpressure)."""
        capture = AudioCapture()

        # Fill the queue
        for _ in range(capture._queue_size):
            capture._audio_queue.put(AudioFrame(
                audio=np.zeros(1600, dtype=np.float32),
                sample_rate=16000,
                timestamp=0.0,
            ))

        # Try to add another frame
        audio_data = np.random.randn(1600).astype(np.float32) * 0.1
        mock_time_info = MagicMock()
        mock_time_info.input_buffer_adc_time = 1.0

        # Should not raise, just drop the frame
        capture._audio_callback(audio_data.reshape(-1, 1), 1600, mock_time_info)

        # Queue should still be full
        assert capture._audio_queue.full()


class TestErrorMessages:
    """Tests for error message content."""

    def test_device_not_found_with_index(self):
        """Test AudioDeviceNotFoundError includes device index."""
        with patch("voicekey.audio.capture.list_devices"):
            error = AudioDeviceNotFoundError(device_index=5)
            assert "5" in str(error)

    def test_device_not_found_without_index(self):
        """Test AudioDeviceNotFoundError without device index."""
        with patch("voicekey.audio.capture.list_devices"):
            error = AudioDeviceNotFoundError()
            assert "microphone" in str(error).lower()

    def test_device_busy_error(self):
        """Test AudioDeviceBusyError message."""
        error = AudioDeviceBusyError(device_index=2)
        assert "2" in str(error)
        assert "busy" in str(error).lower()

    def test_device_disconnected_error(self):
        """Test AudioDeviceDisconnectedError message."""
        error = AudioDeviceDisconnectedError()
        assert "disconnected" in str(error).lower()


class TestAudioDataValidation:
    """Tests for audio data validation (NaN/inf detection)."""

    def setup_method(self):
        """Reset invalid frame counter before each test."""
        reset_invalid_frame_count()

    def test_audio_callback_skips_nan_values(self):
        """Test that audio callback skips frames with NaN values."""
        capture = AudioCapture()
        capture._stream = MagicMock()
        capture._is_running = True

        # Create audio data with NaN
        audio_data = np.array([0.1, np.nan, 0.3], dtype=np.float32)
        mock_time_info = MagicMock()
        mock_time_info.input_buffer_adc_time = 1.0

        # Call callback
        capture._audio_callback(audio_data.reshape(-1, 1), 3, mock_time_info)

        # Frame should be skipped, queue should be empty
        assert capture._audio_queue.empty()
        assert get_invalid_frame_count() == 1

    def test_audio_callback_skips_inf_values(self):
        """Test that audio callback skips frames with inf values."""
        capture = AudioCapture()
        capture._stream = MagicMock()
        capture._is_running = True

        # Create audio data with inf
        audio_data = np.array([0.1, np.inf, 0.3], dtype=np.float32)
        mock_time_info = MagicMock()
        mock_time_info.input_buffer_adc_time = 1.0

        # Call callback
        capture._audio_callback(audio_data.reshape(-1, 1), 3, mock_time_info)

        # Frame should be skipped, queue should be empty
        assert capture._audio_queue.empty()
        assert get_invalid_frame_count() == 1

    def test_audio_callback_skips_negative_inf_values(self):
        """Test that audio callback skips frames with -inf values."""
        capture = AudioCapture()
        capture._stream = MagicMock()
        capture._is_running = True

        # Create audio data with -inf
        audio_data = np.array([0.1, -np.inf, 0.3], dtype=np.float32)
        mock_time_info = MagicMock()
        mock_time_info.input_buffer_adc_time = 1.0

        # Call callback
        capture._audio_callback(audio_data.reshape(-1, 1), 3, mock_time_info)

        # Frame should be skipped, queue should be empty
        assert capture._audio_queue.empty()
        assert get_invalid_frame_count() == 1

    def test_audio_callback_accepts_valid_audio(self):
        """Test that audio callback accepts valid finite audio."""
        reset_invalid_frame_count()
        capture = AudioCapture()
        capture._stream = MagicMock()
        capture._is_running = True

        # Create valid audio data
        audio_data = np.random.randn(1600).astype(np.float32) * 0.1
        mock_time_info = MagicMock()
        mock_time_info.input_buffer_adc_time = 123.456

        # Call callback
        capture._audio_callback(audio_data.reshape(-1, 1), 1600, mock_time_info)

        # Frame should be in queue
        assert not capture._audio_queue.empty()
        assert get_invalid_frame_count() == 0

    def test_invalid_frame_count_increments(self):
        """Test that invalid frame counter increments correctly."""
        reset_invalid_frame_count()
        capture = AudioCapture()
        capture._stream = MagicMock()
        capture._is_running = True

        # Create audio with NaN
        nan_audio = np.full(100, np.nan, dtype=np.float32).reshape(-1, 1)
        mock_time_info = MagicMock()
        mock_time_info.input_buffer_adc_time = 1.0

        # Call callback multiple times
        for _ in range(3):
            capture._audio_callback(nan_audio, 100, mock_time_info)

        assert get_invalid_frame_count() == 3

    def test_reset_invalid_frame_count(self):
        """Test resetting the invalid frame counter."""
        reset_invalid_frame_count()
        capture = AudioCapture()
        capture._stream = MagicMock()
        capture._is_running = True

        # Create invalid audio
        nan_audio = np.full(100, np.nan, dtype=np.float32).reshape(-1, 1)
        mock_time_info = MagicMock()
        mock_time_info.input_buffer_adc_time = 1.0

        capture._audio_callback(nan_audio, 100, mock_time_info)
        assert get_invalid_frame_count() == 1

        # Reset counter
        reset_invalid_frame_count()
        assert get_invalid_frame_count() == 0
