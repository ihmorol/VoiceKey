"""Audio capture module for VoiceKey.

Real-time microphone capture using sounddevice with low-latency callback streaming,
bounded queue with backpressure strategy, and robust device error handling.
"""

from __future__ import annotations

import logging
import queue
import threading
import time
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import sounddevice as sd

logger = logging.getLogger(__name__)

# Queue configuration
DEFAULT_QUEUE_SIZE = 32  # Bounded queue max size
DEFAULT_CHUNK_DURATION = 0.1  # 100ms chunks for low latency

# Metrics counters for audio validation
_invalid_frame_count = 0


class AudioDeviceNotFoundError(Exception):
    """Raised when no microphone device is found or specified device doesn't exist."""

    def __init__(self, device_index: Optional[int] = None, message: Optional[str] = None):
        self.device_index = device_index
        if message is None:
            if device_index is not None:
                message = f"No audio device found at index {device_index}"
            else:
                message = "No microphone device found"
        super().__init__(message)
        self._list_available_devices()

    def _list_available_devices(self) -> None:
        """Log available devices for debugging."""
        try:
            devices = list_devices()
            logger.error("Available audio input devices: %s", devices)
        except Exception as e:
            logger.error("Could not list devices: %s", e)


class AudioDeviceBusyError(Exception):
    """Raised when the audio device is already in use."""

    def __init__(self, device_index: Optional[int] = None, message: Optional[str] = None):
        self.device_index = device_index
        if message is None:
            if device_index is not None:
                message = (
                    f"Audio device {device_index} is busy. "
                    "It may be in use by another application."
                )
            else:
                message = (
                    "Audio device is busy. "
                    "It may be in use by another application."
                )
        super().__init__(message)


class AudioDeviceDisconnectedError(Exception):
    """Raised when the audio device is disconnected during operation."""

    def __init__(self, message: Optional[str] = None):
        if message is None:
            message = "Audio device was disconnected"
        super().__init__(message)


@dataclass
class AudioFrame:
    """Single audio frame from microphone capture.

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


@dataclass
class AudioDeviceInfo:
    """Information about an audio input device."""

    index: int
    name: str
    channels: int
    sample_rate: float
    default: bool = False


def list_devices() -> list[dict]:
    """List all available audio input devices.

    Returns:
        List of dictionaries containing device information:
        - index: Device index
        - name: Human-readable device name
        - channels: Number of input channels
        - sample_rate: Supported sample rates
        - default: Whether this is the system default
    """
    try:
        devices = sd.query_devices(kind="input")
        # Handle single device or multiple devices
        if isinstance(devices, dict):
            return [_format_device_info(devices, 0, is_default=True)]
        else:
            result = []
            for i, dev in enumerate(devices):
                result.append(_format_device_info(dev, i, is_default=(i == 0)))
            return result
    except Exception as e:
        logger.error("Failed to query audio devices: %s", e)
        return []


def _format_device_info(device: dict, index: int, is_default: bool = False) -> dict:
    """Format device info into standardized dictionary."""
    return {
        "index": index,
        "name": device.get("name", f"Device {index}"),
        "channels": device.get("max_input_channels", 0),
        "sample_rates": device.get("sample_rate", 16000),
        "default": is_default,
    }


def get_default_device() -> Optional[dict]:
    """Get the system default audio input device.

    Returns:
        Dictionary with device information or None if no default found
    """
    try:
        default_info = sd.query_devices(kind="input")
        if default_info is None:
            return None
        return _format_device_info(default_info, default_info.get("default_input"), is_default=True)
    except Exception as e:
        logger.warning("Could not get default device: %s", e)
        return None


class AudioCapture:
    """Real-time audio capture from microphone.

    Captures mono microphone audio at configurable sample rate using
    low-latency callback streaming with bounded queue and backpressure.

    Example:
        >>> capture = AudioCapture(sample_rate=16000)
        >>> capture.start()
        >>> frame = capture.get_audio_queue().get()
        >>> print(f"Got {len(frame.audio)} samples")
        >>> capture.stop()
    """

    def __init__(
        self,
        device_index: Optional[int] = None,
        sample_rate: int = 16000,
        chunk_duration: float = DEFAULT_CHUNK_DURATION,
        queue_size: int = DEFAULT_QUEUE_SIZE,
    ):
        """Initialize audio capture.

        Args:
            device_index: Specific device index to use, or None for default
            sample_rate: Target sample rate in Hz (default 16000)
            chunk_duration: Duration of each audio chunk in seconds (default 0.1)
            queue_size: Maximum size of audio queue (default 32)
        """
        self._device_index = device_index
        self._sample_rate = sample_rate
        self._chunk_duration = chunk_duration
        self._queue_size = queue_size

        # Calculate frames per chunk
        self._frames_per_chunk = int(sample_rate * chunk_duration)

        # Thread-safe state
        self._lock = threading.Lock()
        self._is_running = False

        # Audio queue with backpressure
        self._audio_queue: queue.Queue[AudioFrame] = queue.Queue(maxsize=queue_size)

        # Stream handle
        self._stream: Optional[sd.InputStream] = None

        # Device info cache
        self._device_info: Optional[dict] = None

        # Validate device early if specified
        if device_index is not None:
            self._validate_device(device_index)

    def _validate_device(self, device_index: int) -> None:
        """Validate that the device exists and is usable.

        Raises:
            AudioDeviceNotFoundError: Device doesn't exist
            AudioDeviceBusyError: Device is busy
        """
        try:
            devices = sd.query_devices(device_index)
            if devices is None:
                raise AudioDeviceNotFoundError(device_index)
            if devices.get("max_input_channels", 0) < 1:
                raise AudioDeviceNotFoundError(device_index, "Device has no input channels")
        except sd.PortAudioError as e:
            if "Invalid device" in str(e):
                raise AudioDeviceNotFoundError(device_index) from e
            raise AudioDeviceBusyError(device_index, str(e)) from e

    def start(self) -> None:
        """Start audio capture streaming.

        Raises:
            AudioDeviceNotFoundError: No microphone found
            AudioDeviceBusyError: Device is in use
            AudioDeviceDisconnectedError: Device removed during operation
        """
        with self._lock:
            if self._is_running:
                logger.warning("AudioCapture already running")
                return

            try:
                # Determine device to use
                device = self._device_index
                if device is None:
                    default = get_default_device()
                    if default:
                        device = default["index"]
                    else:
                        raise AudioDeviceNotFoundError()

                # Get device info
                device_info = sd.query_devices(device)
                self._device_info = _format_device_info(device_info, device, is_default=True)

                # Create input stream with callback
                self._stream = sd.InputStream(
                    device=device,
                    channels=1,  # Mono
                    samplerate=self._sample_rate,
                    blocksize=self._frames_per_chunk,
                    dtype=np.float32,
                    callback=self._audio_callback,
                )

                assert self._stream is not None
                self._stream.start()
                self._is_running = True
                logger.info(
                    "AudioCapture started: device=%s, sample_rate=%d, "
                    "chunk_size=%d",
                    self._device_info.get("name"),
                    self._sample_rate,
                    self._frames_per_chunk,
                )

            except sd.PortAudioError as e:
                error_msg = str(e).lower()
                if "invalid device" in error_msg or "device not found" in error_msg:
                    raise AudioDeviceNotFoundError(self._device_index) from e
                elif "device busy" in error_msg or "resource busy" in error_msg:
                    raise AudioDeviceBusyError(self._device_index) from e
                elif "disconnected" in error_msg or "unexpectedly" in error_msg:
                    raise AudioDeviceDisconnectedError(str(e)) from e
                else:
                    raise
            except Exception as e:
                logger.error("Failed to start audio capture: %s", e)
                raise

    def stop(self) -> None:
        """Stop audio capture streaming.

        This method is safe to call multiple times.
        """
        with self._lock:
            if not self._is_running:
                return

            logger.info("Stopping AudioCapture")

            if self._stream is not None:
                try:
                    self._stream.stop()
                    self._stream.close()
                except Exception as e:
                    logger.warning("Error stopping stream: %s", e)
                finally:
                    self._stream = None

            self._is_running = False
            self._device_info = None

            # Drain the queue
            try:
                while True:
                    self._audio_queue.get_nowait()
            except queue.Empty:
                pass

    def is_running(self) -> bool:
        """Check if audio capture is currently running.

        Returns:
            True if streaming, False otherwise
        """
        with self._lock:
            return self._is_running

    def get_audio_queue(self) -> queue.Queue[AudioFrame]:
        """Get the audio frame queue.

        The queue has a maximum size to provide backpressure.
        If the queue is full, new frames will be dropped.

        Returns:
            Queue containing AudioFrame objects
        """
        return self._audio_queue

    @property
    def device_info(self) -> Optional[dict]:
        """Get current device information.

        Returns:
            Device info dict or None if not running
        """
        return self._device_info

    def _audio_callback(
        self,
        indata: np.ndarray,
        frames: int,
        time_info: sd.CallbackInfo,
    ) -> None:
        """Audio input callback from sounddevice.

        This is called from a separate thread by sounddevice.

        Args:
            indata: Input audio data (shape: [frames, channels])
            frames: Number of frames in this chunk
            time_info: Timing information from PortAudio
        """
        global _invalid_frame_count

        # Extract mono channel
        audio_data = indata[:, 0].copy()

        # Validate audio data for NaN/inf values
        if not np.all(np.isfinite(audio_data)):
            _invalid_frame_count += 1
            logger.warning(
                "Invalid audio frame detected (NaN/inf values), frame skipped. "
                "Total invalid frames: %d",
                _invalid_frame_count,
            )
            return

        # Create audio frame
        frame = AudioFrame(
            audio=audio_data,
            sample_rate=self._sample_rate,
            timestamp=time_info.input_buffer_adc_time,
        )

        # Put frame in queue with non-blocking to provide backpressure
        # If queue is full, frame is dropped (backpressure strategy)
        try:
            self._audio_queue.put_nowait(frame)
        except queue.Full:
            logger.warning(
                "Audio queue full, dropping frame (backpressure triggered)"
            )

    def __enter__(self) -> "AudioCapture":
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.stop()

    def __del__(self) -> None:
        """Destructor to ensure stream is closed."""
        try:
            self.stop()
        except Exception:
            pass


def get_invalid_frame_count() -> int:
    """Get the total count of invalid audio frames detected (NaN/inf values).

    This is a global counter across all AudioCapture instances.

    Returns:
        Number of invalid frames detected since module load or last reset.
    """
    return _invalid_frame_count


def reset_invalid_frame_count() -> None:
    """Reset the invalid frame counter to zero.

    Useful for testing or periodic monitoring.
    """
    global _invalid_frame_count
    _invalid_frame_count = 0
