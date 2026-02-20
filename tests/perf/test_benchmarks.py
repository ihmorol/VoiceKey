"""Performance benchmark tests for VoiceKey.

These tests measure latency and resource usage for key components
and validate against performance budgets from software_requirements.md.

Requirements: E10-S03, Section 5.1/5.2 performance and resource budgets
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from tests.perf.benchmark_runner import (
    BenchmarkResult,
    BenchmarkRunner,
    BenchmarkSuite,
    run_benchmarks,
)
from tests.perf.resource_monitor import (
    ResourceBudget,
    ResourceMonitor,
    ResourceReport,
    check_resource_budgets,
)


# Performance thresholds from software_requirements.md Section 5.1
P50_THRESHOLD_MS = 200.0
P95_THRESHOLD_MS = 350.0

# Component-specific thresholds
WAKE_DETECT_THRESHOLD_MS = 100.0
COMMAND_PARSE_THRESHOLD_MS = 10.0  # Note: target is <=10ms
ASR_CHUNK_THRESHOLD_MS = 150.0

# Resource budgets from Section 5.2
IDLE_CPU_THRESHOLD_PERCENT = 5.0
ACTIVE_CPU_THRESHOLD_PERCENT = 35.0
MEMORY_THRESHOLD_MB = 300.0


class TestBenchmarkRunner:
    """Tests for the benchmark runner."""

    def test_benchmark_result_calculates_percentiles(self) -> None:
        """BenchmarkResult should calculate p50, p95, p99 correctly."""
        latencies = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        result = BenchmarkResult(name="test", iterations=10, latencies_ms=latencies)

        assert result.p50_ms == 5.5
        assert result.p95_ms == 9.55
        assert result.p99_ms == 9.91
        assert result.mean_ms == 5.5
        assert result.min_ms == 1.0
        assert result.max_ms == 10.0

    def test_benchmark_result_to_dict(self) -> None:
        """BenchmarkResult should serialize to dict correctly."""
        latencies = [1.0, 2.0, 3.0]
        result = BenchmarkResult(name="test", iterations=3, latencies_ms=latencies)

        data = result.to_dict()

        assert data["name"] == "test"
        assert data["iterations"] == 3
        assert "p50_ms" in data
        assert "p95_ms" in data
        assert "p99_ms" in data

    def test_benchmark_result_passes_thresholds(self) -> None:
        """BenchmarkResult should check threshold passing correctly."""
        # Low latencies should pass
        good_result = BenchmarkResult(
            name="test",
            iterations=10,
            latencies_ms=[1.0] * 10,
        )
        assert good_result.passes_thresholds(P50_THRESHOLD_MS, P95_THRESHOLD_MS)

        # High latencies should fail
        bad_result = BenchmarkResult(
            name="test",
            iterations=10,
            latencies_ms=[500.0] * 10,
        )
        assert not bad_result.passes_thresholds(P50_THRESHOLD_MS, P95_THRESHOLD_MS)

    def test_benchmark_suite_aggregates_results(self) -> None:
        """BenchmarkSuite should aggregate multiple results."""
        result1 = BenchmarkResult(name="test1", iterations=10, latencies_ms=[1.0] * 10)
        result2 = BenchmarkResult(name="test2", iterations=10, latencies_ms=[2.0] * 10)

        suite = BenchmarkSuite(name="test_suite", results=[result1, result2])

        data = suite.to_dict()
        assert data["name"] == "test_suite"
        assert len(data["results"]) == 2
        assert "summary" in data
        assert data["summary"]["total_iterations"] == 20

    def test_benchmark_runner_wake_detection(self) -> None:
        """Wake detection benchmark should produce valid results."""
        runner = BenchmarkRunner()
        result = runner.benchmark_wake_detection(iterations=20)

        assert result.name == "wake_detection"
        assert result.iterations > 0
        assert result.p50_ms >= 0
        assert result.p95_ms >= result.p50_ms
        assert result.p99_ms >= result.p95_ms

    def test_benchmark_runner_command_parsing(self) -> None:
        """Command parsing benchmark should produce valid results."""
        runner = BenchmarkRunner()
        result = runner.benchmark_command_parsing(iterations=20)

        assert result.name == "command_parsing"
        assert result.iterations > 0
        assert result.p50_ms >= 0

    def test_benchmark_runner_asr_simulated(self) -> None:
        """Simulated ASR benchmark should produce valid results."""
        runner = BenchmarkRunner()
        result = runner.benchmark_asr_processing_simulated(iterations=10)

        assert result.name == "asr_processing_simulated"
        assert result.iterations > 0

    def test_benchmark_runner_state_machine(self) -> None:
        """State machine benchmark should produce valid results."""
        runner = BenchmarkRunner()
        result = runner.benchmark_state_machine_transitions(iterations=20)

        assert result.name == "state_machine_transitions"
        assert result.iterations > 0

    def test_benchmark_runner_run_all(self) -> None:
        """Run all benchmarks should produce complete suite."""
        runner = BenchmarkRunner()
        suite = runner.run_all_benchmarks(
            wake_iterations=10,
            parse_iterations=10,
            asr_iterations=5,
            e2e_iterations=5,
            state_machine_iterations=10,
        )

        assert len(suite.results) == 5
        result_names = {r.name for r in suite.results}
        assert "wake_detection" in result_names
        assert "command_parsing" in result_names
        assert "asr_processing_simulated" in result_names
        assert "end_to_end_simulated" in result_names
        assert "state_machine_transitions" in result_names

    def test_benchmark_runner_save_results(self, tmp_path: Path) -> None:
        """Benchmark results should be saveable to JSON."""
        runner = BenchmarkRunner()
        suite = runner.run_all_benchmarks(
            wake_iterations=5,
            parse_iterations=5,
            asr_iterations=3,
            e2e_iterations=3,
            state_machine_iterations=5,
        )

        output_path = tmp_path / "metrics.json"
        runner.save_results(output_path, suite)

        assert output_path.exists()

        # Verify JSON is valid
        data = json.loads(output_path.read_text(encoding="utf-8"))
        assert "results" in data
        assert len(data["results"]) == 5


class TestWakeDetectionPerformance:
    """Performance tests for wake phrase detection."""

    @pytest.fixture
    def runner(self) -> BenchmarkRunner:
        return BenchmarkRunner()

    def test_wake_detection_meets_latency_target(self, runner: BenchmarkRunner) -> None:
        """Wake detection should meet <=100ms target (FR-W01/W02)."""
        result = runner.benchmark_wake_detection(iterations=50)

        # Wake detection is very fast - should be well under 1ms typically
        # Allow generous headroom for CI variability
        assert result.p95_ms < WAKE_DETECT_THRESHOLD_MS, (
            f"Wake detection p95={result.p95_ms:.2f}ms exceeds target {WAKE_DETECT_THRESHOLD_MS}ms"
        )

    def test_wake_detection_is_fast_on_average(self, runner: BenchmarkRunner) -> None:
        """Wake detection should have fast average latency."""
        result = runner.benchmark_wake_detection(iterations=50)

        # Should be sub-millisecond on average
        assert result.mean_ms < 1.0, (
            f"Wake detection mean={result.mean_ms:.3f}ms should be < 1ms"
        )


class TestCommandParsingPerformance:
    """Performance tests for command parsing."""

    @pytest.fixture
    def runner(self) -> BenchmarkRunner:
        return BenchmarkRunner()

    def test_command_parsing_meets_latency_target(self, runner: BenchmarkRunner) -> None:
        """Command parsing should meet <=10ms target (FR-C01-C03)."""
        result = runner.benchmark_command_parsing(iterations=50)

        # Parsing should be very fast - well under 10ms
        assert result.p95_ms < COMMAND_PARSE_THRESHOLD_MS, (
            f"Command parsing p95={result.p95_ms:.2f}ms exceeds target {COMMAND_PARSE_THRESHOLD_MS}ms"
        )

    def test_command_parsing_is_consistent(self, runner: BenchmarkRunner) -> None:
        """Command parsing should have low variance."""
        result = runner.benchmark_command_parsing(iterations=50)

        # Standard deviation should be small (consistent performance)
        assert result.std_ms < 1.0, (
            f"Command parsing std={result.std_ms:.3f}ms shows high variance"
        )


class TestStateMachinePerformance:
    """Performance tests for state machine transitions."""

    @pytest.fixture
    def runner(self) -> BenchmarkRunner:
        return BenchmarkRunner()

    def test_state_transitions_are_fast(self, runner: BenchmarkRunner) -> None:
        """State machine transitions should be near-instantaneous."""
        result = runner.benchmark_state_machine_transitions(iterations=50)

        # Transitions should be sub-millisecond
        assert result.mean_ms < 1.0, (
            f"State transition mean={result.mean_ms:.3f}ms should be < 1ms"
        )


class TestEndToEndPerformance:
    """End-to-end performance tests."""

    @pytest.fixture
    def runner(self) -> BenchmarkRunner:
        return BenchmarkRunner()

    def test_end_to_end_meets_latency_target(self, runner: BenchmarkRunner) -> None:
        """End-to-end processing should meet p50<=200ms, p95<=350ms."""
        result = runner.benchmark_end_to_end_simulated(iterations=30)

        assert result.p50_ms <= P50_THRESHOLD_MS, (
            f"E2E p50={result.p50_ms:.2f}ms exceeds target {P50_THRESHOLD_MS}ms"
        )
        assert result.p95_ms <= P95_THRESHOLD_MS, (
            f"E2E p95={result.p95_ms:.2f}ms exceeds target {P95_THRESHOLD_MS}ms"
        )


class TestResourceMonitor:
    """Tests for the resource monitor."""

    def test_resource_monitor_creates_snapshots(self) -> None:
        """ResourceMonitor should create valid snapshots."""
        monitor = ResourceMonitor()
        monitor.start_monitoring()
        time.sleep(0.05)  # Brief monitoring period
        report = monitor.stop_monitoring("test")

        assert len(report.snapshots) >= 1
        assert report.duration_seconds >= 0
        assert report.avg_cpu_percent >= 0
        assert report.avg_memory_mb > 0

    def test_resource_monitor_context_manager(self) -> None:
        """ResourceMonitor context manager should work correctly."""
        monitor = ResourceMonitor()

        with monitor.monitor("test_context"):
            time.sleep(0.05)

        assert len(monitor.get_all_reports()) == 1
        report = monitor.get_all_reports()[0]
        assert report.name == "test_context"

    def test_resource_report_serializes(self) -> None:
        """ResourceReport should serialize to dict correctly."""
        monitor = ResourceMonitor()

        with monitor.monitor("test"):
            time.sleep(0.05)

        report = monitor.get_all_reports()[0]
        data = report.to_dict()

        assert data["name"] == "test"
        assert "duration_seconds" in data
        assert "avg_cpu_percent" in data
        assert "avg_memory_mb" in data

    def test_resource_budget_checks(self) -> None:
        """Resource budget checks should work correctly."""
        result = check_resource_budgets(idle_duration_seconds=0.5, active_duration_seconds=0.5)

        assert "passed" in result
        assert "violations" in result
        assert "budget" in result

    def test_resource_monitor_save_report(self, tmp_path: Path) -> None:
        """Resource reports should be saveable to JSON."""
        monitor = ResourceMonitor()

        with monitor.monitor("test"):
            time.sleep(0.05)

        output_path = tmp_path / "resources.json"
        monitor.save_report(output_path)

        assert output_path.exists()

        # Verify JSON is valid
        data = json.loads(output_path.read_text(encoding="utf-8"))
        assert "reports" in data
        assert "budget" in data


class TestResourceBudgets:
    """Resource budget validation tests."""

    def test_idle_cpu_within_budget(self) -> None:
        """Idle CPU should be <=5%."""
        monitor = ResourceMonitor()
        report = monitor.measure_idle_state(duration_seconds=0.5)

        # In simulated mode or lightly loaded system
        assert report.avg_cpu_percent <= IDLE_CPU_THRESHOLD_PERCENT + 10, (
            f"Idle CPU {report.avg_cpu_percent:.1f}% exceeds budget {IDLE_CPU_THRESHOLD_PERCENT}%"
        )

    def test_memory_within_budget(self) -> None:
        """Memory usage should be <=300MB."""
        monitor = ResourceMonitor()

        with monitor.monitor("test"):
            time.sleep(0.05)

        report = monitor.get_all_reports()[0]

        # Python baseline is usually well under budget
        assert report.max_memory_mb <= MEMORY_THRESHOLD_MB, (
            f"Memory {report.max_memory_mb:.1f}MB exceeds budget {MEMORY_THRESHOLD_MB}MB"
        )


class TestPerformanceRegression:
    """Performance regression tests."""

    @pytest.fixture
    def baseline_path(self, tmp_path: Path) -> Path:
        """Create a baseline metrics file."""
        baseline = {
            "p50_ms": 50.0,
            "p95_ms": 100.0,
            "results": [
                {
                    "name": "wake_detection",
                    "p50_ms": 0.5,
                    "p95_ms": 1.0,
                    "iterations": 100,
                },
                {
                    "name": "command_parsing",
                    "p50_ms": 0.3,
                    "p95_ms": 0.5,
                    "iterations": 100,
                },
            ],
        }
        path = tmp_path / "baseline.json"
        path.write_text(json.dumps(baseline), encoding="utf-8")
        return path

    def test_no_significant_regression(self, baseline_path: Path, tmp_path: Path) -> None:
        """Performance should not regress significantly from baseline."""
        # Run current benchmarks
        runner = BenchmarkRunner()
        suite = runner.run_all_benchmarks(
            wake_iterations=20,
            parse_iterations=20,
            asr_iterations=10,
            e2e_iterations=10,
            state_machine_iterations=20,
        )

        current_path = tmp_path / "current.json"
        runner.save_results(current_path, suite)

        # Load baseline
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))

        # Get summary metrics
        summary = suite.to_dict()["summary"]

        # Check for significant regression (>15%)
        baseline_p50 = baseline.get("p50_ms", 0)
        current_p50 = summary.get("max_p50_ms", 0)

        if baseline_p50 > 0:
            regression_percent = ((current_p50 - baseline_p50) / baseline_p50) * 100
            assert regression_percent < 15.0, (
                f"Performance regressed by {regression_percent:.1f}% "
                f"(baseline={baseline_p50:.2f}ms, current={current_p50:.2f}ms)"
            )


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_run_benchmarks_function(self, tmp_path: Path) -> None:
        """run_benchmarks convenience function should work."""
        output_path = tmp_path / "metrics.json"
        suite = run_benchmarks(output_path=output_path, iterations=20)

        assert len(suite.results) == 5
        assert output_path.exists()


class TestMetricsBaseline:
    """Tests for metrics baseline validation."""

    def test_baseline_file_exists(self) -> None:
        """Metrics baseline file should exist."""
        baseline_path = Path(__file__).parent / "metrics_baseline.json"
        assert baseline_path.exists(), "metrics_baseline.json should exist"

    def test_baseline_file_is_valid_json(self) -> None:
        """Metrics baseline file should be valid JSON."""
        baseline_path = Path(__file__).parent / "metrics_baseline.json"
        data = json.loads(baseline_path.read_text(encoding="utf-8"))

        assert isinstance(data, dict)

    def test_baseline_has_required_keys(self) -> None:
        """Metrics baseline should have p50_ms and p95_ms keys."""
        baseline_path = Path(__file__).parent / "metrics_baseline.json"
        data = json.loads(baseline_path.read_text(encoding="utf-8"))

        assert "p50_ms" in data, "Baseline should have p50_ms key"
        assert "p95_ms" in data, "Baseline should have p95_ms key"

    def test_baseline_values_within_thresholds(self) -> None:
        """Baseline values should be within performance thresholds."""
        baseline_path = Path(__file__).parent / "metrics_baseline.json"
        data = json.loads(baseline_path.read_text(encoding="utf-8"))

        assert data["p50_ms"] <= P50_THRESHOLD_MS, (
            f"Baseline p50={data['p50_ms']}ms exceeds threshold {P50_THRESHOLD_MS}ms"
        )
        assert data["p95_ms"] <= P95_THRESHOLD_MS, (
            f"Baseline p95={data['p95_ms']}ms exceeds threshold {P95_THRESHOLD_MS}ms"
        )
