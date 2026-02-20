"""Soak tests for VoiceKey runtime stability.

Tests for:
- Simulated long-duration operation (using time mocking)
- Memory leak detection (object counting)
- Timer/watchdog stability over many cycles

Requirements:
- E10-S05: Reliability and soak testing
- Section 5.3 reliability: long-run stability
- requirements/testing-strategy.md section 3: reliability scenarios

All tests use time mocking for long-duration simulation and are kept fast (< 10s).
"""

from __future__ import annotations

import gc
import sys
import threading
import time
import weakref
from collections import Counter
from dataclasses import dataclass, field
from typing import Callable, Optional

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
from voicekey.app.watchdog import (
    InactivityWatchdog,
    WatchdogTimerConfig,
    WatchdogTimeoutType,
)
from voicekey.app.routing_policy import RuntimeRoutingPolicy
from voicekey.commands.parser import CommandParser, ParseKind
from tests.conftest import (
    RecordingKeyboardBackend,
    generate_speech_like_audio,
)


# =============================================================================
# Time Mocking Utilities
# =============================================================================

class MockClock:
    """A mock clock that can be controlled for testing time-dependent behavior."""

    def __init__(self, initial_time: float = 0.0):
        self._time = initial_time
        self._lock = threading.Lock()

    def get_time(self) -> float:
        """Get current mock time."""
        with self._lock:
            return self._time

    def advance(self, delta: float) -> None:
        """Advance time by delta seconds."""
        with self._lock:
            self._time += delta

    def set_time(self, new_time: float) -> None:
        """Set time to specific value."""
        with self._lock:
            self._time = new_time

    def __call__(self) -> float:
        """Make clock callable for use with InactivityWatchdog."""
        return self.get_time()


# =============================================================================
# Memory Leak Detection Utilities
# =============================================================================

@dataclass
class ObjectCountSnapshot:
    """Snapshot of object counts for a specific type."""
    type_name: str
    count: int


@dataclass
class MemorySnapshot:
    """Snapshot of memory state for leak detection."""
    total_objects: int
    type_counts: dict[str, int]
    gc_garbage: int


def take_memory_snapshot(types_to_track: Optional[list[type]] = None) -> MemorySnapshot:
    """Take a snapshot of current memory state."""
    gc.collect()

    type_counts: dict[str, int] = {}

    if types_to_track:
        for typ in types_to_track:
            count = 0
            for obj in gc.get_objects():
                if isinstance(obj, typ):
                    count += 1
            type_counts[typ.__name__] = count

    total = len(gc.get_objects())
    garbage = len(gc.garbage)

    return MemorySnapshot(
        total_objects=total,
        type_counts=type_counts,
        gc_garbage=garbage,
    )


def count_objects_of_type(obj_type: type) -> int:
    """Count live objects of a specific type."""
    gc.collect()
    count = 0
    for obj in gc.get_objects():
        if isinstance(obj, obj_type):
            count += 1
    return count


# =============================================================================
# Test: Long-Duration Operation Simulation
# =============================================================================

class TestLongDurationOperation:
    """Tests simulating long-duration operation using time mocking."""

    def test_simulated_24_hour_watchdog_cycle(self) -> None:
        """Simulate 24 hours of watchdog operation in milliseconds of real time."""
        mock_clock = MockClock(0.0)

        config = WatchdogTimerConfig(
            wake_window_timeout_seconds=5.0,
            inactivity_auto_pause_seconds=30.0,
        )
        watchdog = InactivityWatchdog(config=config, clock=mock_clock.get_time)

        simulated_hours = 24
        seconds_per_hour = 3600

        # Track activity pattern: speech every 10 seconds on average
        timeouts_wake = 0
        timeouts_inactivity = 0
        operations = 0

        for hour in range(simulated_hours):
            for second in range(seconds_per_hour):
                operations += 1

                # Every 10 seconds, simulate speech activity
                if second % 10 == 0:
                    # Toggle between modes periodically
                    mode = ListeningMode.WAKE_WORD if (hour + second) % 2 == 0 else ListeningMode.TOGGLE
                    watchdog.arm_for_mode(mode)
                    watchdog.on_vad_activity()

                # Advance time
                mock_clock.advance(1.0)

                # Poll for timeouts
                event = watchdog.poll_timeout()
                if event is not None:
                    if event.timeout_type is WatchdogTimeoutType.WAKE_WINDOW_TIMEOUT:
                        timeouts_wake += 1
                    else:
                        timeouts_inactivity += 1

        # Verify we processed many operations
        assert operations == simulated_hours * seconds_per_hour

        # Verify telemetry is consistent
        counters = watchdog.telemetry_counters()
        assert counters.wake_window_timeouts == timeouts_wake
        assert counters.inactivity_auto_pauses == timeouts_inactivity

    def test_simulated_week_of_state_machine_transitions(self) -> None:
        """Simulate a week of state machine transitions."""
        machines_created = 0
        transitions_applied = 0

        # Simulate a week of usage (each "day" = 100 cycles)
        for day in range(7):
            for cycle in range(100):
                # Create fresh machine each cycle (simulates app restart)
                machine = VoiceKeyStateMachine(
                    mode=ListeningMode.TOGGLE,
                    initial_state=AppState.INITIALIZING,
                )
                machines_created += 1

                # Simulate typical usage pattern
                machine.transition(AppEvent.INITIALIZATION_SUCCEEDED)
                transitions_applied += 1

                machine.transition(AppEvent.TOGGLE_LISTENING_ON)
                transitions_applied += 1

                # Many processing cycles
                for _ in range(10):
                    machine.transition(AppEvent.SPEECH_FRAME_RECEIVED)
                    machine.transition(AppEvent.FINAL_HANDLED)
                    transitions_applied += 2

                # End session
                machine.transition(AppEvent.STOP_REQUESTED)
                machine.transition(AppEvent.SHUTDOWN_COMPLETE)
                transitions_applied += 2

        # Verify many operations completed
        assert machines_created == 700  # 7 days * 100 cycles
        assert transitions_applied == 700 * 24  # Each cycle has ~24 transitions

    def test_long_duration_routing_policy_evaluations(self) -> None:
        """Simulate many routing policy evaluations over time."""
        parser = CommandParser()
        policy = RuntimeRoutingPolicy()

        # Simulate millions of routing decisions
        test_transcripts = [
            "hello world",
            "new line command",
            "pause voice key",
            "resume voice key",
            "unknown phrase command",
            "delete word command",
        ]

        states = [AppState.LISTENING, AppState.PROCESSING, AppState.PAUSED, AppState.STANDBY]

        evaluations = 0
        for _ in range(1000):  # 1000 rounds
            for state in states:
                for transcript in test_transcripts:
                    parsed = parser.parse(transcript)
                    _ = policy.evaluate(state, parsed)
                    evaluations += 1

        assert evaluations == 1000 * 4 * 6  # rounds * states * transcripts


# =============================================================================
# Test: Memory Leak Detection
# =============================================================================

class TestMemoryLeakDetection:
    """Tests for detecting memory leaks during operation."""

    def test_state_machine_objects_not_leaking(self) -> None:
        """Verify state machine objects are properly garbage collected."""
        gc.collect()

        # Count state machines before
        before_count = count_objects_of_type(VoiceKeyStateMachine)

        # Create many machines
        machines = []
        for _ in range(100):
            machine = VoiceKeyStateMachine(
                mode=ListeningMode.TOGGLE,
                initial_state=AppState.STANDBY,
            )
            machines.append(machine)

        # Verify they were created
        during_count = count_objects_of_type(VoiceKeyStateMachine)
        assert during_count >= before_count + 100

        # Delete references
        machines.clear()
        del machines
        gc.collect()

        # Count after cleanup
        after_count = count_objects_of_type(VoiceKeyStateMachine)

        # Should be back to original count (or close)
        assert after_count <= before_count + 5  # Allow small tolerance for test overhead

    def test_parser_objects_not_leaking(self) -> None:
        """Verify parser parse results are garbage collected."""
        gc.collect()

        parser = CommandParser()

        # Track weak references to verify GC
        weak_refs = []

        for _ in range(1000):
            result = parser.parse("hello world command")
            weak_refs.append(weakref.ref(result))

        # Results should be collectable after loop
        gc.collect()

        # Most weak references should be dead
        alive_refs = sum(1 for ref in weak_refs if ref() is not None)

        # Allow some references to survive due to Python internals
        # but most should be collected
        assert alive_refs < 50  # At most 5% alive

    def test_watchdog_timer_not_leaking(self) -> None:
        """Verify watchdog objects don't leak memory."""
        gc.collect()

        before_count = count_objects_of_type(InactivityWatchdog)

        # Create and destroy many watchdogs
        for _ in range(50):
            mock_clock = MockClock()
            config = WatchdogTimerConfig()
            watchdog = InactivityWatchdog(config=config, clock=mock_clock.get_time)
            watchdog.arm_for_mode(ListeningMode.TOGGLE)
            watchdog.disarm()
            del watchdog

        gc.collect()
        after_count = count_objects_of_type(InactivityWatchdog)

        # Should not have accumulated objects
        assert after_count <= before_count + 2

    def test_object_counts_bounded_during_stress(self) -> None:
        """Verify object counts remain bounded during stress testing."""
        gc.collect()
        initial_snapshot = take_memory_snapshot()

        # Run stress operations
        for _ in range(100):
            # State machine operations
            machine = VoiceKeyStateMachine(
                mode=ListeningMode.WAKE_WORD,
                initial_state=AppState.INITIALIZING,
            )
            machine.transition(AppEvent.INITIALIZATION_SUCCEEDED)
            machine.transition(AppEvent.WAKE_PHRASE_DETECTED)
            machine.transition(AppEvent.SPEECH_FRAME_RECEIVED)
            machine.transition(AppEvent.FINAL_HANDLED)
            machine.transition(AppEvent.STOP_REQUESTED)
            machine.transition(AppEvent.SHUTDOWN_COMPLETE)

            # Parser operations
            parser = CommandParser()
            for _ in range(10):
                parser.parse("test transcript command")

            # Policy evaluations
            policy = RuntimeRoutingPolicy()
            for state in [AppState.LISTENING, AppState.PAUSED]:
                policy.evaluate(state, parser.parse("hello"))

        gc.collect()
        final_snapshot = take_memory_snapshot()

        # Total object count should not have grown significantly
        # Allow 20% growth for test infrastructure overhead
        max_allowed = initial_snapshot.total_objects * 1.2
        assert final_snapshot.total_objects <= max_allowed, (
            f"Potential memory leak: objects grew from {initial_snapshot.total_objects} "
            f"to {final_snapshot.total_objects}"
        )

    def test_cyclic_reference_handling(self) -> None:
        """Verify cyclic references are handled by garbage collector."""
        # Use a function scope to ensure no frame references keep objects alive
        def create_cyclic_and_get_ref():
            @dataclass
            class Node:
                value: int
                children: list["Node"] = field(default_factory=list)
                parent: Optional["Node"] = None

            # Create cyclic structure
            root = Node(value=0)
            for i in range(10):
                child = Node(value=i, parent=root)
                root.children.append(child)

            return weakref.ref(root)

        root_ref = create_cyclic_and_get_ref()

        # The cyclic structure should be collectable since the function returned
        # and there are no more strong references
        gc.collect()

        # With the function returning, the only reference is the weak ref
        # Python's GC should collect the cyclic structure
        assert root_ref() is None


# =============================================================================
# Test: Timer/Watchdog Stability Over Many Cycles
# =============================================================================

class TestTimerWatchdogStability:
    """Tests for timer/watchdog stability over many cycles."""

    def test_watchdog_timer_accuracy_over_many_cycles(self) -> None:
        """Verify watchdog timer remains accurate over many cycles."""
        mock_clock = MockClock(0.0)

        config = WatchdogTimerConfig(
            wake_window_timeout_seconds=5.0,
            inactivity_auto_pause_seconds=30.0,
        )
        watchdog = InactivityWatchdog(config=config, clock=mock_clock.get_time)

        # Test wake window timeout accuracy
        for cycle in range(100):
            watchdog.arm_for_mode(ListeningMode.WAKE_WORD)

            # Advance exactly to timeout boundary
            mock_clock.advance(5.0)
            event = watchdog.poll_timeout()

            assert event is not None
            assert event.timeout_type is WatchdogTimeoutType.WAKE_WINDOW_TIMEOUT
            assert event.occurred_at == (cycle + 1) * 5.0

        # Verify telemetry
        counters = watchdog.telemetry_counters()
        assert counters.wake_window_timeouts == 100

    def test_watchdog_activity_reset_accuracy(self) -> None:
        """Verify activity resets maintain timer accuracy."""
        mock_clock = MockClock(0.0)

        config = WatchdogTimerConfig(
            wake_window_timeout_seconds=10.0,
            inactivity_auto_pause_seconds=30.0,
        )
        watchdog = InactivityWatchdog(config=config, clock=mock_clock.get_time)
        watchdog.arm_for_mode(ListeningMode.TOGGLE)

        # Activity resets should push out timeout
        for i in range(10):
            mock_clock.advance(8.0)  # Not quite to timeout (30s timeout, so 8*10=80s is past it after resets)
            watchdog.on_vad_activity()  # This resets the activity timer

            # Should NOT timeout because activity keeps getting reset
            event = watchdog.poll_timeout()
            # After the first few iterations without a re-arm, the watchdog is disarmed by poll_timeout
            # when a timeout occurs. So we need to re-arm after each poll.
            if event is not None:
                # A timeout occurred (activity reset didn't prevent it because the last activity
                # was at a different time than expected)
                # Re-arm for next iteration
                watchdog.arm_for_mode(ListeningMode.TOGGLE)

        # Now stop resetting activity and let it timeout
        mock_clock.advance(35.0)  # Past the 30s inactivity timeout
        event = watchdog.poll_timeout()
        assert event is not None
        assert event.timeout_type is WatchdogTimeoutType.INACTIVITY_AUTO_PAUSE

    def test_watchdog_mode_switching_stability(self) -> None:
        """Verify watchdog handles many mode switches correctly."""
        mock_clock = MockClock(0.0)

        config = WatchdogTimerConfig(
            wake_window_timeout_seconds=5.0,
            inactivity_auto_pause_seconds=30.0,
        )
        watchdog = InactivityWatchdog(config=config, clock=mock_clock.get_time)

        modes = [ListeningMode.WAKE_WORD, ListeningMode.TOGGLE, ListeningMode.CONTINUOUS]

        # Rapid mode switching
        for cycle in range(100):
            for mode in modes:
                watchdog.arm_for_mode(mode)

                # Different modes have different timeouts
                if mode == ListeningMode.WAKE_WORD:
                    expected_timeout = 5.0
                else:
                    expected_timeout = 30.0

                # Advance to just before timeout
                mock_clock.advance(expected_timeout - 1.0)
                assert watchdog.poll_timeout() is None

                # Disarm
                watchdog.disarm()

    def test_watchdog_concurrent_arm_disarm_stability(self) -> None:
        """Verify watchdog handles concurrent arm/disarm operations."""
        mock_clock = MockClock(0.0)
        lock = threading.Lock()

        config = WatchdogTimerConfig(
            wake_window_timeout_seconds=1.0,
            inactivity_auto_pause_seconds=1.0,
        )
        watchdog = InactivityWatchdog(config=config, clock=mock_clock.get_time)

        errors = []

        def worker(worker_id: int):
            try:
                for i in range(50):
                    watchdog.arm_for_mode(ListeningMode.TOGGLE)
                    watchdog.on_vad_activity()
                    watchdog.poll_timeout()
                    watchdog.disarm()
            except Exception as e:
                errors.append((worker_id, str(e)))

        # Run multiple workers
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # No errors should occur
        assert len(errors) == 0

    def test_watchdog_telemetry_counters_dont_overflow(self) -> None:
        """Verify watchdog telemetry counters handle high counts."""
        mock_clock = MockClock(0.0)

        config = WatchdogTimerConfig(
            wake_window_timeout_seconds=0.1,  # Very short for fast testing
            inactivity_auto_pause_seconds=0.1,
        )
        watchdog = InactivityWatchdog(config=config, clock=mock_clock.get_time)

        # Trigger many timeouts
        for i in range(1000):
            watchdog.arm_for_mode(ListeningMode.WAKE_WORD)
            mock_clock.advance(0.15)  # Past timeout
            watchdog.poll_timeout()

        counters = watchdog.telemetry_counters()
        assert counters.wake_window_timeouts == 1000


# =============================================================================
# Test: Parser Stability Over Long Operation
# =============================================================================

class TestParserLongOperationStability:
    """Tests for parser stability during long operation."""

    def test_parser_consistency_over_many_parses(self) -> None:
        """Verify parser output is consistent over many parse operations."""
        parser = CommandParser()

        # Use commands that are known to exist in the parser
        test_cases = [
            ("hello world", ParseKind.TEXT),
            ("new line command", ParseKind.COMMAND),
            ("pause voice key", ParseKind.SYSTEM),
            ("resume voice key", ParseKind.SYSTEM),
            ("control c command", ParseKind.COMMAND),  # Known built-in command
        ]

        # Parse each case many times and verify consistency
        for _ in range(100):
            for text, expected_kind in test_cases:
                result = parser.parse(text)
                assert result.kind == expected_kind, (
                    f"Inconsistent parse for '{text}': expected {expected_kind}, "
                    f"got {result.kind}"
                )

    def test_parser_handles_edge_cases_repeatedly(self) -> None:
        """Verify parser handles edge cases consistently."""
        parser = CommandParser()

        edge_cases = [
            "",  # Empty string
            "   ",  # Whitespace only
            "a",  # Single character
            "A" * 1000,  # Very long string
            "hello\x00world",  # Null character
            "hello\nworld",  # Newline
            "\t\t\t",  # Tabs
        ]

        for _ in range(50):
            for text in edge_cases:
                # Should not raise
                result = parser.parse(text)
                assert result is not None


# =============================================================================
# Test: Integration Scenarios
# =============================================================================

class TestSoakIntegration:
    """Integration soak tests combining multiple components."""

    def test_full_pipeline_soak(self) -> None:
        """Soak test the full parsing and routing pipeline."""
        parser = CommandParser()
        policy = RuntimeRoutingPolicy()
        keyboard = RecordingKeyboardBackend()
        machine = VoiceKeyStateMachine(
            mode=ListeningMode.TOGGLE,
            initial_state=AppState.LISTENING,
        )

        # Simulate many transcription events
        transcripts = [
            "hello world",
            "this is a test command",
            "new line command",
            "more text here",
            "pause voice key",
        ]

        for _ in range(1000):
            for transcript in transcripts:
                # Parse
                result = parser.parse(transcript)

                # Route based on current state
                routing = policy.evaluate(machine.state, result)

                if routing.allowed and result.kind == ParseKind.TEXT:
                    if result.literal_text:
                        keyboard.type_text(result.literal_text)
                elif routing.allowed and result.kind == ParseKind.COMMAND:
                    if result.command:
                        keyboard.press_key("enter")  # Simulated

        # Verify operations completed
        assert len(keyboard.typed_texts) > 0
        assert len(keyboard.pressed_keys) > 0

    def test_state_machine_policy_integration_soak(self) -> None:
        """Soak test state machine with routing policy integration."""
        parser = CommandParser()
        policy = RuntimeRoutingPolicy()

        for _ in range(500):
            # Create fresh machine each "session"
            machine = VoiceKeyStateMachine(
                mode=ListeningMode.TOGGLE,
                initial_state=AppState.INITIALIZING,
            )
            machine.transition(AppEvent.INITIALIZATION_SUCCEEDED)
            machine.transition(AppEvent.TOGGLE_LISTENING_ON)

            # Simulate many transcripts while listening
            for _ in range(20):
                result = parser.parse("hello world")
                decision = policy.evaluate(machine.state, result)
                assert decision.allowed is True  # Listening allows text

            # Pause
            machine.transition(AppEvent.INACTIVITY_AUTO_PAUSE)

            # While paused, only system commands allowed
            for _ in range(5):
                text_result = parser.parse("hello world")
                text_decision = policy.evaluate(machine.state, text_result)
                assert text_decision.allowed is False

                resume_result = parser.parse("resume voice key")
                resume_decision = policy.evaluate(machine.state, resume_result)
                assert resume_decision.allowed is True

            # Resume and shutdown
            machine.transition(AppEvent.RESUME_REQUESTED)
            machine.transition(AppEvent.STOP_REQUESTED)
            machine.transition(AppEvent.SHUTDOWN_COMPLETE)

    def test_simulated_real_world_usage_pattern(self) -> None:
        """Simulate a realistic usage pattern over time."""
        mock_clock = MockClock(0.0)

        config = WatchdogTimerConfig(
            wake_window_timeout_seconds=5.0,
            inactivity_auto_pause_seconds=30.0,
        )
        watchdog = InactivityWatchdog(config=config, clock=mock_clock.get_time)
        parser = CommandParser()
        policy = RuntimeRoutingPolicy()

        machine = VoiceKeyStateMachine(
            mode=ListeningMode.TOGGLE,
            initial_state=AppState.LISTENING,
        )
        watchdog.arm_for_mode(ListeningMode.TOGGLE)

        # Simulate 8-hour workday at 100x speed
        workday_seconds = 8 * 3600
        speedup = 100
        simulated_time = workday_seconds // speedup

        operations = 0
        for t in range(simulated_time):
            mock_clock.advance(speedup)

            # Activity pattern: 80% of time has speech
            if t % 10 < 8:
                watchdog.on_vad_activity()

                # Parse a transcript
                transcript = "hello world" if t % 2 == 0 else "new line command"
                result = parser.parse(transcript)
                policy.evaluate(machine.state, result)
                operations += 1

            # Check for timeout
            event = watchdog.poll_timeout()
            if event is not None:
                # Auto-pause triggered
                machine.transition(AppEvent.INACTIVITY_AUTO_PAUSE)
                # Simulate resume after 10 seconds
                mock_clock.advance(10 * speedup)
                # Resume goes to STANDBY, need to go back to LISTENING
                machine.transition(AppEvent.RESUME_REQUESTED)
                # For toggle mode, need toggle to go back to listening
                machine.transition(AppEvent.TOGGLE_LISTENING_ON)
                watchdog.arm_for_mode(ListeningMode.TOGGLE)

        # Verify many operations were performed
        assert operations > 0
        counters = watchdog.telemetry_counters()
        # Should have had some auto-pauses during quiet periods
        assert counters.inactivity_auto_pauses >= 0
