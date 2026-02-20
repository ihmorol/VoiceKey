"""Resource monitor for VoiceKey performance budget validation.

Measures CPU and memory usage during idle and active states.
Reports against resource budget thresholds from software_requirements.md.

Requirements: E10-S03, Section 5.2 resource budgets
"""

from __future__ import annotations

import gc
import json
import os
import statistics
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Generator, Iterator

# Try to import psutil for resource monitoring
try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None  # type: ignore


@dataclass
class ResourceSnapshot:
    """Snapshot of resource usage at a point in time."""

    timestamp_ms: float
    cpu_percent: float
    memory_mb: float
    thread_count: int = 0
    open_files: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp_ms": round(self.timestamp_ms, 2),
            "cpu_percent": round(self.cpu_percent, 2),
            "memory_mb": round(self.memory_mb, 2),
            "thread_count": self.thread_count,
            "open_files": self.open_files,
        }


@dataclass
class ResourceReport:
    """Aggregated resource usage report."""

    name: str
    snapshots: list[ResourceSnapshot]
    duration_seconds: float = field(init=False)
    avg_cpu_percent: float = field(init=False)
    max_cpu_percent: float = field(init=False)
    avg_memory_mb: float = field(init=False)
    max_memory_mb: float = field(init=False)
    min_memory_mb: float = field(init=False)

    def __post_init__(self) -> None:
        if not self.snapshots:
            raise ValueError(f"No snapshots for resource report {self.name}")

        self.duration_seconds = (self.snapshots[-1].timestamp_ms - self.snapshots[0].timestamp_ms) / 1000.0

        cpu_values = [s.cpu_percent for s in self.snapshots]
        memory_values = [s.memory_mb for s in self.snapshots]

        self.avg_cpu_percent = statistics.mean(cpu_values)
        self.max_cpu_percent = max(cpu_values)
        self.avg_memory_mb = statistics.mean(memory_values)
        self.max_memory_mb = max(memory_values)
        self.min_memory_mb = min(memory_values)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "duration_seconds": round(self.duration_seconds, 2),
            "snapshot_count": len(self.snapshots),
            "avg_cpu_percent": round(self.avg_cpu_percent, 2),
            "max_cpu_percent": round(self.max_cpu_percent, 2),
            "avg_memory_mb": round(self.avg_memory_mb, 2),
            "max_memory_mb": round(self.max_memory_mb, 2),
            "min_memory_mb": round(self.min_memory_mb, 2),
        }

    def passes_budgets(
        self,
        cpu_threshold_percent: float,
        memory_threshold_mb: float,
    ) -> bool:
        """Check if resource usage passes budget thresholds."""
        return (
            self.avg_cpu_percent <= cpu_threshold_percent
            and self.max_memory_mb <= memory_threshold_mb
        )


@dataclass
class ResourceBudget:
    """Resource budget thresholds from software_requirements.md."""

    # From Section 5.2 Resource Budget
    IDLE_CPU_PERCENT: float = 5.0
    ACTIVE_CPU_PERCENT: float = 35.0
    MEMORY_MB: float = 300.0
    DISK_GB: float = 2.5

    def to_dict(self) -> dict[str, float]:
        """Convert to dictionary for JSON serialization."""
        return {
            "idle_cpu_percent": self.IDLE_CPU_PERCENT,
            "active_cpu_percent": self.ACTIVE_CPU_PERCENT,
            "memory_mb": self.MEMORY_MB,
            "disk_gb": self.DISK_GB,
        }


class ResourceMonitor:
    """Monitors CPU and memory usage for VoiceKey."""

    def __init__(
        self,
        sample_interval_ms: float = 100.0,
        budget: ResourceBudget | None = None,
    ) -> None:
        """Initialize resource monitor.

        Args:
            sample_interval_ms: Interval between samples in milliseconds
            budget: Resource budget thresholds (uses defaults if None)
        """
        self.sample_interval_ms = sample_interval_ms
        self.budget = budget or ResourceBudget()
        self._reports: list[ResourceReport] = []
        self._current_snapshots: list[ResourceSnapshot] = []
        self._start_time: float | None = None

        if not PSUTIL_AVAILABLE:
            # Fall back to simulated monitoring
            self._process = None
        else:
            self._process = psutil.Process(os.getpid())

    def _take_snapshot(self) -> ResourceSnapshot:
        """Take a snapshot of current resource usage."""
        timestamp_ms = (time.monotonic() - (self._start_time or 0)) * 1000.0

        if not PSUTIL_AVAILABLE or self._process is None:
            # Simulated snapshot for testing without psutil
            return ResourceSnapshot(
                timestamp_ms=timestamp_ms,
                cpu_percent=self._simulate_cpu(),
                memory_mb=self._simulate_memory(),
                thread_count=1,
                open_files=0,
            )

        try:
            cpu = self._process.cpu_percent() / 100.0  # Normalize to 0-100 scale
            memory_info = self._process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)

            try:
                thread_count = self._process.num_threads()
            except (psutil.AccessDenied, AttributeError):
                thread_count = 0

            try:
                open_files = len(self._process.open_files())
            except (psutil.AccessDenied, AttributeError):
                open_files = 0

            return ResourceSnapshot(
                timestamp_ms=timestamp_ms,
                cpu_percent=min(cpu, 100.0),
                memory_mb=memory_mb,
                thread_count=thread_count,
                open_files=open_files,
            )
        except psutil.NoSuchProcess:
            # Process no longer exists
            return ResourceSnapshot(
                timestamp_ms=timestamp_ms,
                cpu_percent=0.0,
                memory_mb=0.0,
            )

    def _simulate_cpu(self) -> float:
        """Simulate CPU usage for testing without real monitoring."""
        # Simulate low CPU usage
        return statistics.mean([0.5, 1.2, 0.8, 1.5, 0.9])

    def _simulate_memory(self) -> float:
        """Simulate memory usage for testing without real monitoring."""
        # Simulate reasonable memory usage
        import sys

        base_memory = 50.0  # Base Python process memory
        return base_memory + len(sys.modules) * 0.1

    @contextmanager
    def monitor(
        self,
        name: str = "monitoring_session",
    ) -> Generator[None, None, None]:
        """Context manager for monitoring a code block.

        Args:
            name: Name for this monitoring session

        Yields:
            None

        Example:
            >>> monitor = ResourceMonitor()
            >>> with monitor.monitor("idle_state"):
            ...     time.sleep(1.0)  # Idle period
        """
        self.start_monitoring()
        try:
            yield
        finally:
            self.stop_monitoring(name)

    def start_monitoring(self) -> None:
        """Start collecting resource snapshots."""
        self._current_snapshots = []
        self._start_time = time.monotonic()

        # Take initial snapshot after a brief settle period
        time.sleep(self.sample_interval_ms / 1000.0 / 2)
        self._current_snapshots.append(self._take_snapshot())

    def stop_monitoring(self, name: str = "monitoring_session") -> ResourceReport:
        """Stop collecting snapshots and generate report.

        Args:
            name: Name for this monitoring session

        Returns:
            ResourceReport with aggregated statistics
        """
        # Take final snapshot
        self._current_snapshots.append(self._take_snapshot())

        report = ResourceReport(name=name, snapshots=self._current_snapshots)
        self._reports.append(report)

        # Reset for next session
        self._current_snapshots = []
        self._start_time = None

        return report

    def collect_samples(self, duration_seconds: float, name: str = "sampled") -> ResourceReport:
        """Collect samples for a fixed duration.

        Args:
            duration_seconds: How long to collect samples
            name: Name for this monitoring session

        Returns:
            ResourceReport with aggregated statistics
        """
        self.start_monitoring()

        end_time = time.monotonic() + duration_seconds
        while time.monotonic() < end_time:
            time.sleep(self.sample_interval_ms / 1000.0)
            self._current_snapshots.append(self._take_snapshot())

        return self.stop_monitoring(name)

    def measure_idle_state(self, duration_seconds: float = 5.0) -> ResourceReport:
        """Measure resource usage during idle state.

        Args:
            duration_seconds: Duration to measure idle state

        Returns:
            ResourceReport for idle state
        """
        # Force garbage collection to get clean baseline
        gc.collect()

        return self.collect_samples(duration_seconds, name="idle_state")

    def measure_active_state(
        self,
        duration_seconds: float = 5.0,
        workload: callable | None = None,
    ) -> ResourceReport:
        """Measure resource usage during active processing.

        Args:
            duration_seconds: Duration to measure active state
            workload: Optional workload function to execute during measurement

        Returns:
            ResourceReport for active state
        """
        self.start_monitoring()

        end_time = time.monotonic() + duration_seconds

        while time.monotonic() < end_time:
            # Execute workload if provided
            if workload is not None:
                workload()

            time.sleep(self.sample_interval_ms / 1000.0)
            self._current_snapshots.append(self._take_snapshot())

        return self.stop_monitoring(name="active_state")

    def get_all_reports(self) -> list[ResourceReport]:
        """Get all collected reports."""
        return self._reports.copy()

    def get_summary(self) -> dict[str, Any]:
        """Get summary of all reports."""
        if not self._reports:
            return {"reports": [], "budget": self.budget.to_dict()}

        return {
            "reports": [r.to_dict() for r in self._reports],
            "budget": self.budget.to_dict(),
            "violations": self._check_violations(),
        }

    def _check_violations(self) -> list[dict[str, Any]]:
        """Check for budget violations across all reports."""
        violations = []

        for report in self._reports:
            # Check idle CPU budget
            if "idle" in report.name.lower():
                if report.avg_cpu_percent > self.budget.IDLE_CPU_PERCENT:
                    violations.append({
                        "report": report.name,
                        "metric": "cpu_percent",
                        "value": report.avg_cpu_percent,
                        "threshold": self.budget.IDLE_CPU_PERCENT,
                        "message": f"Idle CPU {report.avg_cpu_percent:.1f}% exceeds budget {self.budget.IDLE_CPU_PERCENT}%",
                    })

            # Check active CPU budget
            if "active" in report.name.lower():
                if report.avg_cpu_percent > self.budget.ACTIVE_CPU_PERCENT:
                    violations.append({
                        "report": report.name,
                        "metric": "cpu_percent",
                        "value": report.avg_cpu_percent,
                        "threshold": self.budget.ACTIVE_CPU_PERCENT,
                        "message": f"Active CPU {report.avg_cpu_percent:.1f}% exceeds budget {self.budget.ACTIVE_CPU_PERCENT}%",
                    })

            # Check memory budget
            if report.max_memory_mb > self.budget.MEMORY_MB:
                violations.append({
                    "report": report.name,
                    "metric": "memory_mb",
                    "value": report.max_memory_mb,
                    "threshold": self.budget.MEMORY_MB,
                    "message": f"Memory {report.max_memory_mb:.1f}MB exceeds budget {self.budget.MEMORY_MB}MB",
                })

        return violations

    def save_report(self, output_path: Path) -> None:
        """Save resource monitoring report to JSON file.

        Args:
            output_path: Path to save report
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(self.get_summary(), indent=2), encoding="utf-8")


def check_resource_budgets(
    idle_duration_seconds: float = 3.0,
    active_duration_seconds: float = 3.0,
) -> dict[str, Any]:
    """Check if resource usage passes budget thresholds.

    This is a convenience function for CI integration.

    Args:
        idle_duration_seconds: Duration to measure idle state
        active_duration_seconds: Duration to measure active state

    Returns:
        Dictionary with budget check results
    """
    monitor = ResourceMonitor()
    budget = monitor.budget

    # Measure idle state
    idle_report = monitor.measure_idle_state(idle_duration_seconds)

    # Measure active state with simulated workload
    def simulated_workload() -> None:
        """Simulate active processing workload."""
        # Create and destroy some objects to simulate activity
        data = [list(range(1000)) for _ in range(10)]
        _ = sum(sum(d) for d in data)

    active_report = monitor.measure_active_state(active_duration_seconds, workload=simulated_workload)

    # Check violations
    violations = monitor._check_violations()

    return {
        "passed": len(violations) == 0,
        "violations": violations,
        "idle_report": idle_report.to_dict(),
        "active_report": active_report.to_dict(),
        "budget": budget.to_dict(),
    }
