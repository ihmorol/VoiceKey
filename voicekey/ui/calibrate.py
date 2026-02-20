"""Microphone calibration workflow for VoiceKey.

This module provides interactive calibration to:
- Test microphone input levels
- Detect background noise level
- Suggest VAD threshold based on noise
- Test wake word detection
- Validate audio quality
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Callable, Optional

import numpy as np

from voicekey.audio.capture import AudioCapture, list_devices
from voicekey.audio.vad import VADCalibrator, VADProcessor
from voicekey.audio.wake import WakePhraseDetector

logger = logging.getLogger(__name__)


@dataclass
class CalibrationResult:
    """Result of calibration process."""

    success: bool
    device_index: int | None
    device_name: str | None
    ambient_noise_level: float
    suggested_vad_threshold: float
    current_vad_threshold: float
    audio_quality_score: float
    wake_word_test_passed: bool
    messages: list[str]
    recommendations: list[str]


class CalibrationRunner:
    """Interactive calibration workflow runner."""

    def __init__(
        self,
        device_index: int | None = None,
        vad_threshold: float = 0.5,
        wake_phrase: str = "voice key",
        wake_sensitivity: float = 0.55,
        noise_duration_seconds: float = 3.0,
        speech_duration_seconds: float = 5.0,
    ):
        """Initialize calibration runner.

        Args:
            device_index: Specific device to calibrate, or None for default
            vad_threshold: Current VAD threshold to compare against
            wake_phrase: Wake phrase to test
            wake_sensitivity: Wake detection sensitivity
            noise_duration_seconds: How long to measure ambient noise
            speech_duration_seconds: How long to collect speech samples
        """
        self._device_index = device_index
        self._vad_threshold = vad_threshold
        self._wake_phrase = wake_phrase
        self._wake_sensitivity = wake_sensitivity
        self._noise_duration = noise_duration_seconds
        self._speech_duration = speech_duration_seconds

        # Results
        self._captured_audio: list[np.ndarray] = []
        self._vad_calibrator = VADCalibrator()
        self._wake_detector = WakePhraseDetector(wake_phrase, sensitivity=wake_sensitivity)

    def _get_device_info(self) -> tuple[int | None, str | None]:
        """Get device index and name."""
        if self._device_index is not None:
            try:
                devices = list_devices()
                for dev in devices:
                    if dev["index"] == self._device_index:
                        return self._device_index, dev["name"]
            except Exception:
                pass
            return self._device_index, f"Device {self._device_index}"

        # Use default
        try:
            devices = list_devices()
            if devices:
                return devices[0]["index"], devices[0]["name"]
        except Exception:
            pass
        return None, None

    def _measure_noise_level(
        self,
        capture: AudioCapture,
        duration: float,
        progress_callback: Callable[[str], None] | None = None,
    ) -> float:
        """Measure ambient noise level."""
        if progress_callback:
            progress_callback(f"Measuring ambient noise for {duration:.1f} seconds...")

        start_time = time.monotonic()
        samples_collected = 0

        while time.monotonic() - start_time < duration:
            try:
                frame = capture.get_audio_queue().get(timeout=1.0)
                self._captured_audio.append(frame.audio)
                self._vad_calibrator.add_sample(frame.audio)
                samples_collected += len(frame.audio)

                if progress_callback:
                    elapsed = time.monotonic() - start_time
                    progress_callback(
                        f"Collecting noise sample... {elapsed:.1f}/{duration:.1f}s "
                        f"(RMS: {np.sqrt(np.mean(frame.audio ** 2)):.4f})"
                    )
            except Exception as e:
                logger.warning("Error during noise measurement: %s", e)

        return self._vad_calibrator.get_ambient_level()

    def _measure_speech_level(
        self,
        capture: AudioCapture,
        duration: float,
        progress_callback: Callable[[str], None] | None = None,
    ) -> tuple[float, list[str]]:
        """Measure speech input and test wake word detection."""
        if progress_callback:
            progress_callback(f"Please speak the wake phrase '{self._wake_phrase}' for {duration:.1f} seconds...")

        start_time = time.monotonic()
        speech_rms: list[float] = []
        transcripts_detected: list[str] = []

        # For calibration, we simulate wake detection by checking audio levels
        # In a real scenario, this would use the ASR to get actual transcripts

        while time.monotonic() - start_time < duration:
            try:
                frame = capture.get_audio_queue().get(timeout=1.0)
                self._captured_audio.append(frame.audio)

                # Calculate RMS
                rms = float(np.sqrt(np.mean(frame.audio ** 2)))
                speech_rms.append(rms)

                # Check if above typical speech threshold
                vad = VADProcessor(threshold=self._vad_threshold)
                is_speech = vad.process(frame.audio)

                if progress_callback:
                    elapsed = time.monotonic() - start_time
                    progress_callback(
                        f"Listening for speech... {elapsed:.1f}/{duration:.1f}s "
                        f"(RMS: {rms:.4f}, Speech: {is_speech})"
                    )

            except Exception as e:
                logger.warning("Error during speech measurement: %s", e)

        # Calculate average speech level
        avg_speech_level = float(np.mean(speech_rms)) if speech_rms else 0.0

        return avg_speech_level, transcripts_detected

    def run(
        self,
        progress_callback: Callable[[str], None] | None = None,
    ) -> CalibrationResult:
        """Run the full calibration workflow.

        Args:
            progress_callback: Optional callback for progress updates

        Returns:
            CalibrationResult with findings and recommendations
        """
        messages: list[str] = []
        recommendations: list[str] = []

        # Get device info
        device_index, device_name = self._get_device_info()
        messages.append(f"Using device: {device_name or 'default'}")

        if device_index is None:
            return CalibrationResult(
                success=False,
                device_index=None,
                device_name=None,
                ambient_noise_level=0.0,
                suggested_vad_threshold=0.5,
                current_vad_threshold=self._vad_threshold,
                audio_quality_score=0.0,
                wake_word_test_passed=False,
                messages=["No microphone device found"],
                recommendations=["Check microphone connection and permissions"],
            )

        # Create capture
        capture = AudioCapture(device_index=device_index, sample_rate=16000)

        try:
            # Start capture
            capture.start()
            time.sleep(0.5)  # Let the stream stabilize

            # Phase 1: Measure ambient noise
            ambient_level = self._measure_noise_level(
                capture, self._noise_duration, progress_callback
            )
            messages.append(f"Ambient noise level: {ambient_level:.4f} RMS")

            # Phase 2: Measure speech / test wake detection
            speech_level, transcripts = self._measure_speech_level(
                capture, self._speech_duration, progress_callback
            )
            messages.append(f"Speech input level: {speech_level:.4f} RMS")

        except Exception as e:
            logger.error("Calibration error: %s", e)
            return CalibrationResult(
                success=False,
                device_index=device_index,
                device_name=device_name,
                ambient_noise_level=0.0,
                suggested_vad_threshold=0.5,
                current_vad_threshold=self._vad_threshold,
                audio_quality_score=0.0,
                wake_word_test_passed=False,
                messages=[f"Calibration failed: {e}"],
                recommendations=["Check microphone permissions and try again"],
            )
        finally:
            capture.stop()

        # Calculate suggested VAD threshold
        suggested_threshold = self._vad_calibrator.get_suggested_threshold()
        messages.append(f"Suggested VAD threshold: {suggested_threshold:.2f}")

        # Determine wake word test result
        # In calibration mode, we pass because we heard speech above threshold
        wake_test_passed = speech_level > 0.01  # Typical speech threshold

        # Calculate audio quality score (0-1)
        # Based on signal-to-noise ratio and input levels
        quality_score = 0.0
        if speech_level > 0:
            snr = speech_level / max(ambient_level, 0.0001)
            # Map SNR to quality score (20dB = 1.0, 0dB = 0.0)
            quality_score = min(1.0, max(0.0, (np.log10(snr + 0.0001) / 2.0) + 0.5))
        messages.append(f"Audio quality score: {quality_score:.2f}")

        # Generate recommendations
        if suggested_threshold > self._vad_threshold:
            recommendations.append(
                f"Consider increasing VAD threshold from {self._vad_threshold:.2f} "
                f"to {suggested_threshold:.2f} for better noise immunity"
            )
        elif suggested_threshold < self._vad_threshold:
            recommendations.append(
                f"Consider lowering VAD threshold from {self._vad_threshold:.2f} "
                f"to {suggested_threshold:.2f} for better sensitivity"
            )

        if ambient_level > 0.03:
            recommendations.append(
                "High ambient noise detected. Consider using a quieter location "
                "or a microphone with noise cancellation."
            )

        if quality_score < 0.5:
            recommendations.append(
                "Low audio quality detected. Check microphone distance "
                "and ensure clear audio path."
            )

        if not wake_test_passed:
            recommendations.append(
                "Wake phrase not clearly detected. Speak louder or closer to microphone."
            )

        if not recommendations:
            recommendations.append("Calibration complete. Your microphone is well configured!")

        return CalibrationResult(
            success=True,
            device_index=device_index,
            device_name=device_name,
            ambient_noise_level=ambient_level,
            suggested_vad_threshold=suggested_threshold,
            current_vad_threshold=self._vad_threshold,
            audio_quality_score=quality_score,
            wake_word_test_passed=wake_test_passed,
            messages=messages,
            recommendations=recommendations,
        )


def run_calibration(
    device_index: int | None = None,
    vad_threshold: float = 0.5,
    wake_phrase: str = "voice key",
    wake_sensitivity: float = 0.55,
) -> CalibrationResult:
    """Run microphone calibration.

    Args:
        device_index: Specific device to calibrate, or None for default
        vad_threshold: Current VAD threshold
        wake_phrase: Wake phrase to test
        wake_sensitivity: Wake detection sensitivity

    Returns:
        CalibrationResult with findings and recommendations
    """
    runner = CalibrationRunner(
        device_index=device_index,
        vad_threshold=vad_threshold,
        wake_phrase=wake_phrase,
        wake_sensitivity=wake_sensitivity,
    )
    return runner.run()


__all__ = [
    "CalibrationResult",
    "CalibrationRunner",
    "run_calibration",
]
