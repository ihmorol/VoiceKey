"""Performance benchmark runner for VoiceKey.

Measures latency for:
- Wake detection
- ASR processing
- Command parsing

Reports p50, p95, p99 latencies for performance budget validation.

Requirements: E10-S03, Section 5.1 performance targets
"""

from __future__ import annotations

import json
import statistics
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import numpy as np


@dataclass
class BenchmarkResult:
    """Result of a single benchmark run."""

    name: str
    iterations: int
    latencies_ms: list[float]
    p50_ms: float = field(init=False)
    p95_ms: float = field(init=False)
    p99_ms: float = field(init=False)
    mean_ms: float = field(init=False)
    min_ms: float = field(init=False)
    max_ms: float = field(init=False)
    std_ms: float = field(init=False)

    def __post_init__(self) -> None:
        if not self.latencies_ms:
            raise ValueError(f"No latency measurements for benchmark {self.name}")

        sorted_latencies = sorted(self.latencies_ms)
        n = len(sorted_latencies)

        self.p50_ms = self._percentile(sorted_latencies, 50)
        self.p95_ms = self._percentile(sorted_latencies, 95)
        self.p99_ms = self._percentile(sorted_latencies, 99)
        self.mean_ms = statistics.mean(self.latencies_ms)
        self.min_ms = min(self.latencies_ms)
        self.max_ms = max(self.latencies_ms)
        self.std_ms = statistics.stdev(self.latencies_ms) if n > 1 else 0.0

    @staticmethod
    def _percentile(sorted_data: list[float], percentile: float) -> float:
        """Calculate percentile from sorted data."""
        n = len(sorted_data)
        if n == 1:
            return sorted_data[0]

        # Use linear interpolation
        k = (n - 1) * percentile / 100.0
        f = int(k)
        c = f + 1 if f + 1 < n else f
        return sorted_data[f] + (k - f) * (sorted_data[c] - sorted_data[f])

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "iterations": self.iterations,
            "p50_ms": round(self.p50_ms, 3),
            "p95_ms": round(self.p95_ms, 3),
            "p99_ms": round(self.p99_ms, 3),
            "mean_ms": round(self.mean_ms, 3),
            "min_ms": round(self.min_ms, 3),
            "max_ms": round(self.max_ms, 3),
            "std_ms": round(self.std_ms, 3),
        }

    def passes_thresholds(self, p50_threshold_ms: float, p95_threshold_ms: float) -> bool:
        """Check if benchmark passes performance thresholds."""
        return self.p50_ms <= p50_threshold_ms and self.p95_ms <= p95_threshold_ms


@dataclass
class BenchmarkSuite:
    """Collection of benchmark results."""

    name: str
    results: list[BenchmarkResult]
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "timestamp": self.timestamp,
            "results": [r.to_dict() for r in self.results],
            "summary": self._compute_summary(),
        }

    def _compute_summary(self) -> dict[str, Any]:
        """Compute aggregate summary across all benchmarks."""
        if not self.results:
            return {}

        # Find max p50 and p95 across all benchmarks
        max_p50 = max(r.p50_ms for r in self.results)
        max_p95 = max(r.p95_ms for r in self.results)

        # Weighted average by iterations
        total_iterations = sum(r.iterations for r in self.results)
        weighted_p50 = sum(r.p50_ms * r.iterations for r in self.results) / total_iterations
        weighted_p95 = sum(r.p95_ms * r.iterations for r in self.results) / total_iterations

        return {
            "max_p50_ms": round(max_p50, 3),
            "max_p95_ms": round(max_p95, 3),
            "weighted_p50_ms": round(weighted_p50, 3),
            "weighted_p95_ms": round(weighted_p95, 3),
            "total_iterations": total_iterations,
            "benchmark_count": len(self.results),
        }


class BenchmarkRunner:
    """Runs performance benchmarks for VoiceKey components."""

    # Performance thresholds from software_requirements.md Section 5.1
    DEFAULT_P50_THRESHOLD_MS = 200.0
    DEFAULT_P95_THRESHOLD_MS = 350.0

    # Individual component targets
    WAKE_DETECT_TARGET_MS = 100.0
    ASR_CHUNK_TARGET_MS = 150.0
    COMMAND_PARSE_TARGET_MS = 10.0

    def __init__(
        self,
        p50_threshold_ms: float = DEFAULT_P50_THRESHOLD_MS,
        p95_threshold_ms: float = DEFAULT_P95_THRESHOLD_MS,
        warmup_iterations: int = 3,
    ) -> None:
        self.p50_threshold_ms = p50_threshold_ms
        self.p95_threshold_ms = p95_threshold_ms
        self.warmup_iterations = warmup_iterations
        self._results: list[BenchmarkResult] = []

    def benchmark_wake_detection(
        self,
        iterations: int = 100,
        transcripts: list[str] | None = None,
    ) -> BenchmarkResult:
        """Benchmark wake phrase detection latency.

        Args:
            iterations: Number of iterations to run
            transcripts: Test transcripts to use (uses defaults if None)

        Returns:
            BenchmarkResult with latency measurements
        """
        from voicekey.audio.wake import WakePhraseDetector

        detector = WakePhraseDetector()

        # Default test transcripts
        if transcripts is None:
            transcripts = [
                "voice key start listening",
                "hello world this is a test",
                "please voice key begin",
                "some random text without wake phrase",
                "VOICE KEY NOW",
                "testing voice key detection",
                "another phrase with no wake",
                "voice key hello there",
            ]

        latencies: list[float] = []

        # Warmup
        for _ in range(self.warmup_iterations):
            for transcript in transcripts:
                detector.detect(transcript)

        # Benchmark
        for _ in range(iterations):
            for transcript in transcripts:
                start = time.perf_counter_ns()
                detector.detect(transcript)
                end = time.perf_counter_ns()
                latencies.append((end - start) / 1_000_000)  # Convert to ms

        result = BenchmarkResult(
            name="wake_detection",
            iterations=len(latencies),
            latencies_ms=latencies,
        )
        self._results.append(result)
        return result

    def benchmark_command_parsing(
        self,
        iterations: int = 100,
        transcripts: list[str] | None = None,
    ) -> BenchmarkResult:
        """Benchmark command parsing latency.

        Args:
            iterations: Number of iterations to run
            transcripts: Test transcripts to use (uses defaults if None)

        Returns:
            BenchmarkResult with latency measurements
        """
        from voicekey.commands.parser import create_parser

        parser = create_parser()

        # Default test transcripts - mix of commands and text
        if transcripts is None:
            transcripts = [
                "new line command",
                "hello world command",  # unknown command
                "pause voice key",
                "resume voice key",
                "enter command",
                "tab command",
                "backspace command",
                "scratch that command",
                "this is regular text to type",
                "another sentence without commands",
                "control c command",
                "control v command",
                "left command",
                "right command",
            ]

        latencies: list[float] = []

        # Warmup
        for _ in range(self.warmup_iterations):
            for transcript in transcripts:
                parser.parse(transcript)

        # Benchmark
        for _ in range(iterations):
            for transcript in transcripts:
                start = time.perf_counter_ns()
                parser.parse(transcript)
                end = time.perf_counter_ns()
                latencies.append((end - start) / 1_000_000)  # Convert to ms

        result = BenchmarkResult(
            name="command_parsing",
            iterations=len(latencies),
            latencies_ms=latencies,
        )
        self._results.append(result)
        return result

    def benchmark_asr_processing_simulated(
        self,
        iterations: int = 50,
        audio_duration_seconds: float = 1.0,
        sample_rate: int = 16000,
    ) -> BenchmarkResult:
        """Benchmark simulated ASR processing path (without actual model).

        This measures the algorithmic overhead of audio processing pipeline
        components that can be tested without hardware or model loading:
        - Audio chunk handling
        - VAD-like operations
        - Event emission patterns

        Args:
            iterations: Number of iterations to run
            audio_duration_seconds: Duration of audio chunk to simulate
            sample_rate: Audio sample rate

        Returns:
            BenchmarkResult with latency measurements
        """
        # Generate synthetic audio data
        num_samples = int(audio_duration_seconds * sample_rate)

        latencies: list[float] = []

        # Simulate audio processing operations
        def simulate_asr_chunk(audio: np.ndarray) -> dict[str, Any]:
            """Simulate ASR chunk processing operations."""
            # Simulate VAD-like energy calculation
            energy = np.sqrt(np.mean(audio**2))

            # Simulate feature extraction
            # Simple RMS and zero-crossing rate calculation
            rms = np.sqrt(np.mean(audio**2))
            zero_crossings = np.sum(np.abs(np.diff(np.sign(audio)))) / (2 * len(audio))

            # Simulate chunking/buffering overhead
            chunks = np.array_split(audio, 10)

            # Return simulated result
            return {
                "energy": float(energy),
                "rms": float(rms),
                "zero_crossing_rate": float(zero_crossings),
                "chunk_count": len(chunks),
                "has_speech": energy > 0.01,
            }

        # Warmup
        for _ in range(self.warmup_iterations):
            audio = np.random.randn(num_samples).astype(np.float32) * 0.1
            simulate_asr_chunk(audio)

        # Benchmark
        for _ in range(iterations):
            # Generate fresh audio each iteration
            audio = np.random.randn(num_samples).astype(np.float32) * 0.1

            start = time.perf_counter_ns()
            result = simulate_asr_chunk(audio)
            end = time.perf_counter_ns()

            latencies.append((end - start) / 1_000_000)  # Convert to ms

        result = BenchmarkResult(
            name="asr_processing_simulated",
            iterations=len(latencies),
            latencies_ms=latencies,
        )
        self._results.append(result)
        return result

    def benchmark_end_to_end_simulated(
        self,
        iterations: int = 50,
    ) -> BenchmarkResult:
        """Benchmark simulated end-to-end processing path.

        This simulates the complete wake -> parse -> dispatch pipeline
        without actual audio I/O or keyboard injection.

        Args:
            iterations: Number of iterations to run

        Returns:
            BenchmarkResult with latency measurements
        """
        from voicekey.audio.wake import WakePhraseDetector
        from voicekey.commands.parser import create_parser

        detector = WakePhraseDetector()
        parser = create_parser()

        # Test scenarios
        scenarios = [
            "voice key hello world",
            "new line command",
            "pause voice key",
            "just some text to type",
            "enter command",
        ]

        latencies: list[float] = []

        # Warmup
        for _ in range(self.warmup_iterations):
            for scenario in scenarios:
                wake_result = detector.detect(scenario)
                parse_result = parser.parse(scenario)

        # Benchmark
        for _ in range(iterations):
            for scenario in scenarios:
                start = time.perf_counter_ns()

                # Wake detection
                wake_result = detector.detect(scenario)

                # Command parsing
                parse_result = parser.parse(scenario)

                end = time.perf_counter_ns()
                latencies.append((end - start) / 1_000_000)  # Convert to ms

        result = BenchmarkResult(
            name="end_to_end_simulated",
            iterations=len(latencies),
            latencies_ms=latencies,
        )
        self._results.append(result)
        return result

    def benchmark_state_machine_transitions(
        self,
        iterations: int = 100,
    ) -> BenchmarkResult:
        """Benchmark state machine transition latency.

        Args:
            iterations: Number of iterations to run

        Returns:
            BenchmarkResult with latency measurements
        """
        from voicekey.app.state_machine import (
            AppEvent,
            AppState,
            ListeningMode,
            VoiceKeyStateMachine,
        )

        # Transition sequence to benchmark (valid transitions for wake_word mode)
        events = [
            AppEvent.INITIALIZATION_SUCCEEDED,  # INITIALIZING -> STANDBY
            AppEvent.WAKE_PHRASE_DETECTED,  # STANDBY -> LISTENING
            AppEvent.SPEECH_FRAME_RECEIVED,  # LISTENING -> PROCESSING
            AppEvent.FINAL_HANDLED,  # PROCESSING -> LISTENING
            AppEvent.WAKE_WINDOW_TIMEOUT,  # LISTENING -> STANDBY
        ]

        latencies: list[float] = []

        # Warmup
        for _ in range(self.warmup_iterations):
            sm = VoiceKeyStateMachine(
                mode=ListeningMode.WAKE_WORD,
                initial_state=AppState.INITIALIZING,
            )
            for event in events:
                try:
                    sm.transition(event)
                except Exception:
                    pass  # Ignore transition errors in warmup

        # Benchmark
        for _ in range(iterations):
            sm = VoiceKeyStateMachine(
                mode=ListeningMode.WAKE_WORD,
                initial_state=AppState.INITIALIZING,
            )
            for event in events:
                start = time.perf_counter_ns()
                sm.transition(event)
                end = time.perf_counter_ns()
                latencies.append((end - start) / 1_000_000)  # Convert to ms

        result = BenchmarkResult(
            name="state_machine_transitions",
            iterations=len(latencies),
            latencies_ms=latencies,
        )
        self._results.append(result)
        return result

    def run_all_benchmarks(
        self,
        wake_iterations: int = 100,
        parse_iterations: int = 100,
        asr_iterations: int = 50,
        e2e_iterations: int = 50,
        state_machine_iterations: int = 100,
    ) -> BenchmarkSuite:
        """Run all standard benchmarks.

        Args:
            wake_iterations: Iterations for wake detection benchmark
            parse_iterations: Iterations for command parsing benchmark
            asr_iterations: Iterations for ASR processing benchmark
            e2e_iterations: Iterations for end-to-end benchmark
            state_machine_iterations: Iterations for state machine benchmark

        Returns:
            BenchmarkSuite with all results
        """
        self._results = []

        # Run individual benchmarks
        self.benchmark_wake_detection(iterations=wake_iterations)
        self.benchmark_command_parsing(iterations=parse_iterations)
        self.benchmark_asr_processing_simulated(iterations=asr_iterations)
        self.benchmark_end_to_end_simulated(iterations=e2e_iterations)
        self.benchmark_state_machine_transitions(iterations=state_machine_iterations)

        return BenchmarkSuite(name="voicekey_benchmarks", results=self._results)

    def save_results(self, output_path: Path, suite: BenchmarkSuite | None = None) -> None:
        """Save benchmark results to JSON file.

        Args:
            output_path: Path to save results
            suite: Suite to save (uses last run if None)
        """
        if suite is None:
            suite = BenchmarkSuite(name="voicekey_benchmarks", results=self._results)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(suite.to_dict(), indent=2), encoding="utf-8")

    def get_summary_metrics(self) -> dict[str, float]:
        """Get summary metrics for CI guardrail checks.

        Returns:
            Dictionary with p50_ms and p95_ms for CI comparison
        """
        if not self._results:
            return {"p50_ms": 0.0, "p95_ms": 0.0}

        suite = BenchmarkSuite(name="summary", results=self._results)
        summary = suite._compute_summary()

        return {
            "p50_ms": summary["max_p50_ms"],
            "p95_ms": summary["max_p95_ms"],
        }


def run_benchmarks(
    output_path: Path | None = None,
    iterations: int = 100,
) -> BenchmarkSuite:
    """Convenience function to run benchmarks and optionally save results.

    Args:
        output_path: Optional path to save results
        iterations: Number of iterations for each benchmark

    Returns:
        BenchmarkSuite with all results
    """
    runner = BenchmarkRunner()
    suite = runner.run_all_benchmarks(
        wake_iterations=iterations,
        parse_iterations=iterations,
        asr_iterations=max(50, iterations // 2),
        e2e_iterations=max(50, iterations // 2),
        state_machine_iterations=iterations,
    )

    if output_path:
        runner.save_results(output_path, suite)

    return suite
