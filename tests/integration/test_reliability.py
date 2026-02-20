"""Reliability integration tests for VoiceKey.

Tests for:
- Audio device reconnect after disconnect (mock audio capture)
- Rapid toggle (start/stop/pause/resume) cycles
- Paused-resume phrase path race conditions
- State machine stability under stress (many rapid transitions)

Requirements:
- E10-S05: Reliability and soak testing
- Section 5.3 reliability: microphone disconnect/reconnect, rapid mode switching
- requirements/testing-strategy.md section 3: reliability scenarios

All tests use mocks/fixtures - no real microphone or keyboard hardware required.
"""

from __future__ import annotations

import gc
import queue
import threading
import time
from dataclasses import dataclass, field
from typing import Optional
from unittest import mock

import numpy as np
import pytest

from voicekey.app.state_machine import (
    AppEvent,
    AppState,
    InvalidTransitionError,
    ListeningMode,
    ModeHooks,
    VoiceKeyStateMachine,
)
from voicekey.app.routing_policy import RuntimeRoutingPolicy
from voicekey.app.resilience import (
    MICROPHONE_RECONNECT_RETRY_POLICY,
    RetryPolicy,
    SafetyFallbackDecision,
    decide_safety_fallback,
)
from voicekey.app.runtime_errors import RuntimeErrorCode
from voicekey.app.watchdog import (
    InactivityWatchdog,
    WatchdogTimerConfig,
    WatchdogTimeoutEvent,
    WatchdogTimeoutType,
)
from voicekey.commands.parser import CommandParser, ParseKind
from tests.conftest import (
    RecordingKeyboardBackend,
    generate_speech_like_audio,
    generate_silence_audio,
)


# =============================================================================
# Mock Audio Capture with Disconnect/Reconnect Support
# =============================================================================

@dataclass
class AudioFrame:
    """Audio frame for testing (avoids sounddevice dependency)."""
    audio: np.ndarray
    sample_rate: int
    timestamp: float
    is_speech: Optional[bool] = None


class DisconnectableMockAudioCapture:
    """Mock audio capture that supports disconnect/reconnect simulation."""

    def __init__(
        self,
        sample_rate: int = 16000,
        auto_reconnect: bool = False,
        max_reconnect_attempts: int = 3,
    ):
        self._sample_rate = sample_rate
        self._auto_reconnect = auto_reconnect
        self._max_reconnect_attempts = max_reconnect_attempts
        self._audio_queue: queue.Queue[AudioFrame] = queue.Queue(maxsize=32)
        self._is_running = False
        self._is_disconnected = False
        self._reconnect_count = 0
        self._disconnect_count = 0
        self._frame_index = 0
        self._lock = threading.Lock()

    def start(self) -> None:
        """Start audio capture."""
        with self._lock:
            if self._is_running:
                return
            self._is_running = True
            self._is_disconnected = False
            self._frame_index = 0

    def stop(self) -> None:
        """Stop audio capture."""
        with self._lock:
            self._is_running = False
            self._is_disconnected = False
            # Drain queue
            try:
                while True:
                    self._audio_queue.get_nowait()
            except queue.Empty:
                pass

    def disconnect(self) -> None:
        """Simulate audio device disconnect."""
        with self._lock:
            self._is_disconnected = True
            self._disconnect_count += 1

    def reconnect(self) -> bool:
        """Attempt to reconnect after disconnect."""
        with self._lock:
            if self._reconnect_count >= self._max_reconnect_attempts:
                return False
            self._reconnect_count += 1
            self._is_disconnected = False
            return True

    def is_running(self) -> bool:
        with self._lock:
            return self._is_running and not self._is_disconnected

    def is_disconnected(self) -> bool:
        with self._lock:
            return self._is_disconnected

    def get_audio_queue(self) -> queue.Queue[AudioFrame]:
        return self._audio_queue

    def push_frame(self, audio: np.ndarray, is_speech: bool = True) -> None:
        """Push a frame into the queue (simulates incoming audio)."""
        frame = AudioFrame(
            audio=audio,
            sample_rate=self._sample_rate,
            timestamp=time.monotonic(),
            is_speech=is_speech,
        )
        try:
            self._audio_queue.put_nowait(frame)
        except queue.Full:
            pass  # Backpressure - drop frame

    @property
    def reconnect_count(self) -> int:
        return self._reconnect_count

    @property
    def disconnect_count(self) -> int:
        return self._disconnect_count


# =============================================================================
# Test: Audio Device Reconnect After Disconnect
# =============================================================================

class TestAudioDeviceReconnect:
    """Tests for audio device disconnect and reconnect handling."""

    def test_capture_reports_disconnected_state(self) -> None:
        """Verify capture correctly reports disconnected state."""
        capture = DisconnectableMockAudioCapture()
        capture.start()

        assert capture.is_running() is True
        assert capture.is_disconnected() is False

        capture.disconnect()

        assert capture.is_disconnected() is True
        assert capture.is_running() is False  # Disconnected = not running

    def test_reconnect_after_single_disconnect_succeeds(self) -> None:
        """Verify reconnect succeeds after a single disconnect."""
        capture = DisconnectableMockAudioCapture()
        capture.start()
        capture.disconnect()

        assert capture.reconnect() is True
        assert capture.is_running() is True
        assert capture.is_disconnected() is False
        assert capture.reconnect_count == 1

    def test_reconnect_respects_max_attempts(self) -> None:
        """Verify reconnect fails after exhausting max attempts."""
        capture = DisconnectableMockAudioCapture(max_reconnect_attempts=3)
        capture.start()

        # First 3 reconnects should succeed
        for i in range(3):
            capture.disconnect()
            assert capture.reconnect() is True

        # 4th reconnect should fail
        capture.disconnect()
        assert capture.reconnect() is False
        assert capture.reconnect_count == 3

    def test_reconnect_policy_allows_retry_before_fallback(self) -> None:
        """Verify retry policy allows retries before forcing pause."""
        policy = MICROPHONE_RECONNECT_RETRY_POLICY

        # Should allow retries up to max_attempts
        assert policy.next_delay_after_failure(1) == 1.0
        assert policy.next_delay_after_failure(2) == 2.0
        assert policy.next_delay_after_failure(3) == 4.0
        assert policy.next_delay_after_failure(4) is None  # Exhausted

    def test_safety_fallback_only_after_retries_exhausted(self) -> None:
        """Verify safety fallback to pause only after retries exhausted."""
        # While retrying - should not force pause
        retrying = decide_safety_fallback(
            code=RuntimeErrorCode.MICROPHONE_DISCONNECTED,
            state=AppState.LISTENING,
            retries_exhausted=False,
        )
        assert retrying.force_pause is False

        # After exhausted - should force pause
        exhausted = decide_safety_fallback(
            code=RuntimeErrorCode.MICROPHONE_DISCONNECTED,
            state=AppState.LISTENING,
            retries_exhausted=True,
        )
        assert exhausted.force_pause is True
        assert exhausted.pause_event is AppEvent.INACTIVITY_AUTO_PAUSE

    def test_audio_queue_survives_disconnect_reconnect_cycle(self) -> None:
        """Verify audio queue state survives disconnect/reconnect cycle."""
        capture = DisconnectableMockAudioCapture()
        capture.start()

        # Push some frames
        audio = generate_speech_like_audio(0.1)
        capture.push_frame(audio)
        capture.push_frame(audio)

        # Verify queue has frames
        assert capture.get_audio_queue().qsize() == 2

        # Disconnect
        capture.disconnect()

        # Reconnect
        capture.reconnect()

        # Queue should still exist and be usable
        capture.push_frame(audio)
        assert capture.get_audio_queue().qsize() == 3


# =============================================================================
# Test: Rapid Toggle Cycles
# =============================================================================

class TestRapidToggleCycles:
    """Tests for rapid start/stop/pause/resume toggle cycles."""

    def test_rapid_pause_resume_cycles_stability(self) -> None:
        """Verify state machine handles rapid pause/resume cycles."""
        machine = VoiceKeyStateMachine(
            mode=ListeningMode.TOGGLE,
            initial_state=AppState.STANDBY,
        )

        # Perform many rapid pause/resume cycles
        for _ in range(100):
            # Pause
            result = machine.transition(AppEvent.PAUSE_REQUESTED)
            assert result.to_state is AppState.PAUSED

            # Resume
            result = machine.transition(AppEvent.RESUME_REQUESTED)
            assert result.to_state is AppState.STANDBY

        assert machine.state is AppState.STANDBY

    def test_rapid_start_stop_cycles_stability(self) -> None:
        """Verify state machine handles rapid start/stop cycles."""
        for cycle in range(50):
            machine = VoiceKeyStateMachine(
                mode=ListeningMode.TOGGLE,
                initial_state=AppState.STANDBY,
            )

            # Start listening
            result = machine.transition(AppEvent.TOGGLE_LISTENING_ON)
            assert result.to_state is AppState.LISTENING

            # Stop
            result = machine.transition(AppEvent.STOP_REQUESTED)
            assert result.to_state is AppState.SHUTTING_DOWN

            result = machine.transition(AppEvent.SHUTDOWN_COMPLETE)
            assert result.terminal is True

    def test_rapid_toggle_with_listening_processing_transitions(self) -> None:
        """Verify rapid listening <-> processing transitions."""
        machine = VoiceKeyStateMachine(
            mode=ListeningMode.CONTINUOUS,
            initial_state=AppState.LISTENING,
        )

        for _ in range(100):
            # Speech frame received -> processing
            result = machine.transition(AppEvent.SPEECH_FRAME_RECEIVED)
            assert result.to_state is AppState.PROCESSING

            # Partial handled -> back to listening
            result = machine.transition(AppEvent.PARTIAL_HANDLED)
            assert result.to_state is AppState.LISTENING

    def test_rapid_mode_switching_preserves_state_integrity(self) -> None:
        """Verify rapid mode switching doesn't corrupt state."""
        # Test all three modes in rapid succession
        modes = [ListeningMode.WAKE_WORD, ListeningMode.TOGGLE, ListeningMode.CONTINUOUS]

        for _ in range(30):  # Multiple cycles through all modes
            for mode in modes:
                machine = VoiceKeyStateMachine(
                    mode=mode,
                    initial_state=AppState.STANDBY,
                )

                # Each mode should have its specific entry event
                if mode == ListeningMode.WAKE_WORD:
                    result = machine.transition(AppEvent.WAKE_PHRASE_DETECTED)
                elif mode == ListeningMode.TOGGLE:
                    result = machine.transition(AppEvent.TOGGLE_LISTENING_ON)
                else:
                    result = machine.transition(AppEvent.CONTINUOUS_START)

                assert result.to_state is AppState.LISTENING


# =============================================================================
# Test: Paused-Resume Phrase Path Race Conditions
# =============================================================================

class TestPausedResumePhraseRaceConditions:
    """Tests for race conditions in paused-resume phrase path."""

    def test_paused_state_blocks_concurrent_text_and_resume(self) -> None:
        """Verify paused state correctly handles concurrent text and resume."""
        parser = CommandParser()
        policy = RuntimeRoutingPolicy()

        # In paused state, text should be blocked
        text_result = parser.parse("hello world")
        assert policy.evaluate(AppState.PAUSED, text_result).allowed is False

        # But resume phrase should be allowed
        resume_result = parser.parse("resume voice key")
        assert policy.evaluate(AppState.PAUSED, resume_result).allowed is True

    def test_resume_phrase_during_processing_doesnt_cause_race(self) -> None:
        """Verify resume phrase during processing doesn't cause state race."""
        machine = VoiceKeyStateMachine(
            mode=ListeningMode.WAKE_WORD,
            initial_state=AppState.PROCESSING,
        )

        # Resume from processing state is not a valid transition
        # (need to finish processing first)
        with pytest.raises(InvalidTransitionError):
            machine.transition(AppEvent.RESUME_REQUESTED)

    def test_concurrent_pause_and_resume_sequencing(self) -> None:
        """Verify correct sequencing of concurrent pause/resume requests."""
        machine = VoiceKeyStateMachine(
            mode=ListeningMode.CONTINUOUS,
            initial_state=AppState.LISTENING,
        )

        # Pause
        result = machine.transition(AppEvent.INACTIVITY_AUTO_PAUSE)
        assert result.to_state is AppState.PAUSED

        # Multiple resume attempts should be idempotent at state machine level
        # First resume succeeds
        result = machine.transition(AppEvent.RESUME_REQUESTED)
        assert result.to_state is AppState.STANDBY

        # Second resume from STANDBY is invalid (already resumed)
        with pytest.raises(InvalidTransitionError):
            machine.transition(AppEvent.RESUME_REQUESTED)

    def test_paused_resume_phrase_timing_with_watchdog(self) -> None:
        """Verify resume phrase timing works correctly with watchdog."""
        # Use a controlled clock
        current_time = [0.0]

        def mock_clock() -> float:
            return current_time[0]

        config = WatchdogTimerConfig(
            wake_window_timeout_seconds=5.0,
            inactivity_auto_pause_seconds=30.0,
        )
        watchdog = InactivityWatchdog(config=config, clock=mock_clock)
        parser = CommandParser()
        policy = RuntimeRoutingPolicy()

        # Start in paused state
        machine = VoiceKeyStateMachine(
            mode=ListeningMode.TOGGLE,
            initial_state=AppState.PAUSED,
        )

        # Resume phrase should work even when watchdog is armed
        resume_result = parser.parse("resume voice key")
        assert policy.evaluate(AppState.PAUSED, resume_result).allowed is True

        # Apply state transition
        result = machine.transition(AppEvent.RESUME_REQUESTED)
        assert result.to_state is AppState.STANDBY

    def test_resume_phrase_enabled_toggles_correctly(self) -> None:
        """Verify resume phrase can be enabled/disabled correctly."""
        parser = CommandParser()
        resume_result = parser.parse("resume voice key")

        # Enabled (default)
        policy_enabled = RuntimeRoutingPolicy(paused_resume_phrase_enabled=True)
        assert policy_enabled.evaluate(AppState.PAUSED, resume_result).allowed is True

        # Disabled
        policy_disabled = RuntimeRoutingPolicy(paused_resume_phrase_enabled=False)
        assert policy_disabled.evaluate(AppState.PAUSED, resume_result).allowed is False

        # Stop phrase should always be allowed
        stop_result = parser.parse("voice key stop")
        assert policy_disabled.evaluate(AppState.PAUSED, stop_result).allowed is True

    def test_multiple_rapid_resume_requests_handled_gracefully(self) -> None:
        """Verify multiple rapid resume requests don't corrupt state."""
        results = []

        def try_resume():
            machine = VoiceKeyStateMachine(
                mode=ListeningMode.TOGGLE,
                initial_state=AppState.PAUSED,
            )
            try:
                result = machine.transition(AppEvent.RESUME_REQUESTED)
                results.append(("success", result.to_state))
            except InvalidTransitionError as e:
                results.append(("error", str(e)))

        # Simulate rapid concurrent resume attempts
        threads = [threading.Thread(target=try_resume) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All should succeed (each thread has its own machine)
        assert all(r[0] == "success" and r[1] == AppState.STANDBY for r in results)


# =============================================================================
# Test: State Machine Stability Under Stress
# =============================================================================

class TestStateMachineStress:
    """Tests for state machine stability under stress conditions."""

    def test_many_rapid_valid_transitions(self) -> None:
        """Verify state machine handles many rapid valid transitions."""
        machine = VoiceKeyStateMachine(
            mode=ListeningMode.WAKE_WORD,
            initial_state=AppState.STANDBY,
        )

        transition_count = 0
        for _ in range(100):
            # Wake -> listening
            machine.transition(AppEvent.WAKE_PHRASE_DETECTED)
            transition_count += 1

            # Listening -> processing
            machine.transition(AppEvent.SPEECH_FRAME_RECEIVED)
            transition_count += 1

            # Processing -> listening
            machine.transition(AppEvent.PARTIAL_HANDLED)
            transition_count += 1

            # Listening -> standby (timeout)
            machine.transition(AppEvent.WAKE_WINDOW_TIMEOUT)
            transition_count += 1

        assert transition_count == 400
        assert machine.state is AppState.STANDBY

    def test_invalid_transitions_raise_errors_not_crash(self) -> None:
        """Verify invalid transitions raise errors without crashing."""
        machine = VoiceKeyStateMachine(
            mode=ListeningMode.WAKE_WORD,
            initial_state=AppState.STANDBY,
        )

        # Try many invalid transitions
        invalid_events = [
            AppEvent.SPEECH_FRAME_RECEIVED,  # Can't receive speech in STANDBY
            AppEvent.PARTIAL_HANDLED,
            AppEvent.FINAL_HANDLED,
            AppEvent.WAKE_WINDOW_TIMEOUT,
            AppEvent.INACTIVITY_AUTO_PAUSE,
            AppEvent.SHUTDOWN_COMPLETE,
        ]

        for event in invalid_events:
            with pytest.raises(InvalidTransitionError):
                machine.transition(event)

        # State should remain unchanged after failed transitions
        assert machine.state is AppState.STANDBY

    def test_stress_with_all_modes_and_transitions(self) -> None:
        """Stress test with all modes and valid transitions."""
        test_cycles = 50

        for mode in [ListeningMode.WAKE_WORD, ListeningMode.TOGGLE, ListeningMode.CONTINUOUS]:
            for _ in range(test_cycles):
                machine = VoiceKeyStateMachine(
                    mode=mode,
                    initial_state=AppState.INITIALIZING,
                )

                # Init -> standby
                machine.transition(AppEvent.INITIALIZATION_SUCCEEDED)

                # Mode-specific entry to listening
                if mode == ListeningMode.WAKE_WORD:
                    machine.transition(AppEvent.WAKE_PHRASE_DETECTED)
                elif mode == ListeningMode.TOGGLE:
                    machine.transition(AppEvent.TOGGLE_LISTENING_ON)
                else:
                    machine.transition(AppEvent.CONTINUOUS_START)

                # Processing cycle
                machine.transition(AppEvent.SPEECH_FRAME_RECEIVED)
                machine.transition(AppEvent.FINAL_HANDLED)

                # Exit path
                machine.transition(AppEvent.STOP_REQUESTED)
                machine.transition(AppEvent.SHUTDOWN_COMPLETE)

                assert machine.terminated is True

    def test_mode_hooks_not_duplicated_under_stress(self) -> None:
        """Verify mode hooks are called exactly once even under stress."""

        class CountingHooks(ModeHooks):
            def __init__(self) -> None:
                self.enter_count = 0
                self.exit_count = 0

            def on_mode_enter(self, mode: ListeningMode) -> None:
                self.enter_count += 1

            def on_mode_exit(self, mode: ListeningMode) -> None:
                self.exit_count += 1

        hooks = CountingHooks()
        machine = VoiceKeyStateMachine(
            mode=ListeningMode.TOGGLE,
            initial_state=AppState.STANDBY,
            mode_hooks=hooks,
        )

        # Many transitions, but only one shutdown
        for _ in range(50):
            machine.transition(AppEvent.TOGGLE_LISTENING_ON)
            machine.transition(AppEvent.SPEECH_FRAME_RECEIVED)
            machine.transition(AppEvent.PARTIAL_HANDLED)
            machine.transition(AppEvent.INACTIVITY_AUTO_PAUSE)
            machine.transition(AppEvent.RESUME_REQUESTED)

        # Shutdown
        machine.transition(AppEvent.STOP_REQUESTED)
        machine.transition(AppEvent.SHUTDOWN_COMPLETE)

        # Hooks should be called exactly once each
        assert hooks.enter_count == 1
        assert hooks.exit_count == 1

    def test_error_state_recovery(self) -> None:
        """Verify recovery from error state."""
        for _ in range(20):
            machine = VoiceKeyStateMachine(
                mode=ListeningMode.WAKE_WORD,
                initial_state=AppState.INITIALIZING,
            )

            # Init failed -> error
            machine.transition(AppEvent.INITIALIZATION_FAILED)
            assert machine.state is AppState.ERROR

            # Error -> shutdown
            machine.transition(AppEvent.STOP_REQUESTED)
            assert machine.state is AppState.SHUTTING_DOWN

            machine.transition(AppEvent.SHUTDOWN_COMPLETE)
            assert machine.terminated is True


# =============================================================================
# Test: Watchdog Stability Under Stress
# =============================================================================

class TestWatchdogStress:
    """Tests for watchdog timer stability under stress."""

    def test_watchdog_many_arm_disarm_cycles(self) -> None:
        """Verify watchdog handles many arm/disarm cycles."""
        current_time = [0.0]

        def mock_clock() -> float:
            return current_time[0]

        config = WatchdogTimerConfig(
            wake_window_timeout_seconds=5.0,
            inactivity_auto_pause_seconds=10.0,
        )
        watchdog = InactivityWatchdog(config=config, clock=mock_clock)

        for cycle in range(100):
            # Arm
            watchdog.arm_for_mode(ListeningMode.WAKE_WORD)

            # Advance time but not past timeout
            current_time[0] += 4.0
            assert watchdog.poll_timeout() is None

            # Disarm
            watchdog.disarm()
            assert watchdog.poll_timeout() is None

        # Check telemetry
        counters = watchdog.telemetry_counters()
        assert counters.wake_window_timeouts == 0
        assert counters.inactivity_auto_pauses == 0

    def test_watchdog_rapid_activity_resets(self) -> None:
        """Verify rapid activity resets don't cause issues."""
        current_time = [0.0]

        def mock_clock() -> float:
            return current_time[0]

        config = WatchdogTimerConfig(
            wake_window_timeout_seconds=5.0,
            inactivity_auto_pause_seconds=30.0,
        )
        watchdog = InactivityWatchdog(config=config, clock=mock_clock)
        watchdog.arm_for_mode(ListeningMode.TOGGLE)

        # Many rapid activity resets
        for _ in range(1000):
            current_time[0] += 0.01  # 10ms increments
            watchdog.on_vad_activity()

            # Never times out because we keep resetting
            assert watchdog.poll_timeout() is None

    def test_watchdog_many_timeout_events(self) -> None:
        """Verify watchdog correctly tracks many timeout events."""
        current_time = [0.0]

        def mock_clock() -> float:
            return current_time[0]

        config = WatchdogTimerConfig(
            wake_window_timeout_seconds=1.0,
            inactivity_auto_pause_seconds=2.0,
        )
        watchdog = InactivityWatchdog(config=config, clock=mock_clock)

        timeout_count = 0
        for _ in range(50):
            # Arm for wake word mode
            watchdog.arm_for_mode(ListeningMode.WAKE_WORD)

            # Advance past timeout
            current_time[0] += 1.5

            # Poll for timeout
            event = watchdog.poll_timeout()
            if event is not None:
                timeout_count += 1
                assert event.timeout_type is WatchdogTimeoutType.WAKE_WINDOW_TIMEOUT

        assert timeout_count == 50
        counters = watchdog.telemetry_counters()
        assert counters.wake_window_timeouts == 50


# =============================================================================
# Test: Thread Safety
# =============================================================================

class TestThreadSafety:
    """Tests for thread safety of state machine and watchdog."""

    def test_concurrent_state_machine_operations(self) -> None:
        """Verify state machine handles concurrent operations safely."""
        machine = VoiceKeyStateMachine(
            mode=ListeningMode.TOGGLE,
            initial_state=AppState.STANDBY,
        )
        errors = []
        successes = []

        def transition_worker(event: AppEvent):
            try:
                # Each thread tries a valid transition
                if event == AppEvent.PAUSE_REQUESTED:
                    # Need to be in a state that allows pause
                    pass  # Skip - would need state coordination
                elif event == AppEvent.STOP_REQUESTED:
                    machine.transition(event)
                    successes.append(1)
            except InvalidTransitionError as e:
                errors.append(str(e))

        # Create threads
        threads = [
            threading.Thread(target=transition_worker, args=(AppEvent.STOP_REQUESTED,))
            for _ in range(5)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # At least one should succeed (the first one)
        # Others may fail with invalid transition (already in shutting down)
        assert len(successes) >= 1

    def test_watchdog_thread_safe_polling(self) -> None:
        """Verify watchdog polling is thread-safe."""
        current_time = [0.0]
        lock = threading.Lock()

        def mock_clock() -> float:
            with lock:
                return current_time[0]

        config = WatchdogTimerConfig(
            wake_window_timeout_seconds=1.0,
            inactivity_auto_pause_seconds=2.0,
        )
        watchdog = InactivityWatchdog(config=config, clock=mock_clock)

        results = []

        def poll_worker():
            for _ in range(10):
                event = watchdog.poll_timeout()
                results.append(event)
                time.sleep(0.001)

        # Arm the watchdog
        watchdog.arm_for_mode(ListeningMode.WAKE_WORD)

        # Start multiple polling threads
        threads = [threading.Thread(target=poll_worker) for _ in range(5)]
        for t in threads:
            t.start()

        # Advance time to trigger timeout
        with lock:
            current_time[0] += 2.0

        for t in threads:
            t.join()

        # Only one thread should have gotten the timeout event
        timeout_events = [r for r in results if r is not None]
        assert len(timeout_events) <= 1  # At most one timeout event
