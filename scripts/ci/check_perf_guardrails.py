"""Evaluate performance guardrails from metrics JSON.

Compares current benchmarks against baseline and fails on regression.
Supports both absolute threshold checks and relative regression detection.

Requirements: E10-S03, FR-CI04 performance guardrail checks
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class GuardrailConfig:
    """Configuration for performance guardrails."""

    # Absolute thresholds (from software_requirements.md Section 5.1)
    p50_threshold_ms: float = 200.0
    p95_threshold_ms: float = 350.0

    # Relative regression thresholds
    max_regression_percent: float = 15.0  # Max % regression allowed

    # Individual component thresholds
    wake_detect_threshold_ms: float = 100.0
    asr_chunk_threshold_ms: float = 150.0
    command_parse_threshold_ms: float = 10.0

    # Resource budget thresholds (from Section 5.2)
    idle_cpu_threshold_percent: float = 5.0
    active_cpu_threshold_percent: float = 35.0
    memory_threshold_mb: float = 300.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check metrics against absolute thresholds
  python check_perf_guardrails.py --metrics-file metrics.json

  # Compare against baseline for regression detection
  python check_perf_guardrails.py --metrics-file metrics.json --baseline-file baseline.json

  # Enforce guardrails (fail on violation)
  python check_perf_guardrails.py --metrics-file metrics.json --enforce 1

  # Run benchmarks and check in one command
  python check_perf_guardrails.py --run-benchmarks --enforce 1
""",
    )
    parser.add_argument("--metrics-file", required=False, type=Path)
    parser.add_argument("--baseline-file", type=Path, help="Baseline metrics for regression detection")
    parser.add_argument("--p50-threshold-ms", type=float, default=200.0)
    parser.add_argument("--p95-threshold-ms", type=float, default=350.0)
    parser.add_argument("--max-regression-percent", type=float, default=15.0, help="Max % regression allowed")
    parser.add_argument("--enforce", default="0", help="Enforce guardrails (1/true/yes/on)")
    parser.add_argument("--run-benchmarks", action="store_true", help="Run benchmarks before checking")
    parser.add_argument("--benchmark-iterations", type=int, default=100, help="Benchmark iterations")
    parser.add_argument("--output-format", choices=["text", "json", "github"], default="text")
    return parser.parse_args()


def _parse_enforce(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def load_metrics(metrics_path: Path) -> dict[str, Any]:
    """Load metrics from JSON file."""
    if not metrics_path.exists():
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")
    return json.loads(metrics_path.read_text(encoding="utf-8"))


def extract_summary_metrics(payload: dict[str, Any]) -> dict[str, float]:
    """Extract p50/p95 summary metrics from payload.

    Supports multiple formats:
    - Direct p50_ms/p95_ms keys
    - Nested in 'summary' object
    - Computed from 'results' array
    """
    # Direct keys
    if "p50_ms" in payload and "p95_ms" in payload:
        return {"p50_ms": payload["p50_ms"], "p95_ms": payload["p95_ms"]}

    # Summary object
    if "summary" in payload:
        summary = payload["summary"]
        if "max_p50_ms" in summary and "max_p95_ms" in summary:
            return {"p50_ms": summary["max_p50_ms"], "p95_ms": summary["max_p95_ms"]}
        if "weighted_p50_ms" in summary and "weighted_p95_ms" in summary:
            return {"p50_ms": summary["weighted_p50_ms"], "p95_ms": summary["weighted_p95_ms"]}

    # Compute from results array
    if "results" in payload:
        results = payload["results"]
        if isinstance(results, list) and results:
            max_p50 = max(r.get("p50_ms", 0) for r in results if isinstance(r, dict))
            max_p95 = max(r.get("p95_ms", 0) for r in results if isinstance(r, dict))
            return {"p50_ms": max_p50, "p95_ms": max_p95}

    return {}


def check_absolute_thresholds(
    metrics: dict[str, float],
    config: GuardrailConfig,
) -> list[str]:
    """Check metrics against absolute thresholds."""
    violations = []

    p50_ms = metrics.get("p50_ms", 0)
    p95_ms = metrics.get("p95_ms", 0)

    if p50_ms > config.p50_threshold_ms:
        violations.append(
            f"p50_ms={p50_ms:.2f}ms exceeds threshold={config.p50_threshold_ms:.2f}ms "
            f"(+{p50_ms - config.p50_threshold_ms:.2f}ms / "
            f"+{(p50_ms / config.p50_threshold_ms - 1) * 100:.1f}%)"
        )

    if p95_ms > config.p95_threshold_ms:
        violations.append(
            f"p95_ms={p95_ms:.2f}ms exceeds threshold={config.p95_threshold_ms:.2f}ms "
            f"(+{p95_ms - config.p95_threshold_ms:.2f}ms / "
            f"+{(p95_ms / config.p95_threshold_ms - 1) * 100:.1f}%)"
        )

    return violations


def check_regression(
    current: dict[str, float],
    baseline: dict[str, float],
    config: GuardrailConfig,
) -> list[str]:
    """Check for performance regression against baseline."""
    regressions = []

    for metric in ["p50_ms", "p95_ms"]:
        current_val = current.get(metric, 0)
        baseline_val = baseline.get(metric, 0)

        if baseline_val <= 0:
            continue

        regression_percent = ((current_val - baseline_val) / baseline_val) * 100

        if regression_percent > config.max_regression_percent:
            regressions.append(
                f"{metric}={current_val:.2f}ms regressed from baseline={baseline_val:.2f}ms "
                f"(+{regression_percent:.1f}% > max {config.max_regression_percent}%)"
            )

    return regressions


def check_component_thresholds(
    payload: dict[str, Any],
    config: GuardrailConfig,
) -> list[str]:
    """Check individual component thresholds."""
    violations = []

    results = payload.get("results", [])
    if not isinstance(results, list):
        return violations

    component_thresholds = {
        "wake_detection": config.wake_detect_threshold_ms,
        "command_parsing": config.command_parse_threshold_ms,
        "asr_processing_simulated": config.asr_chunk_threshold_ms,
        "end_to_end_simulated": config.p50_threshold_ms,
    }

    for result in results:
        if not isinstance(result, dict):
            continue

        name = result.get("name", "")
        p50_ms = result.get("p50_ms", 0)
        p95_ms = result.get("p95_ms", 0)

        threshold = component_thresholds.get(name)
        if threshold is not None:
            if p50_ms > threshold:
                violations.append(
                    f"{name}: p50_ms={p50_ms:.2f}ms exceeds component threshold={threshold:.2f}ms"
                )
            if p95_ms > threshold * 1.5:  # Allow 50% headroom for p95
                violations.append(
                    f"{name}: p95_ms={p95_ms:.2f}ms exceeds component threshold*1.5={threshold * 1.5:.2f}ms"
                )

    return violations


def check_resource_budgets(
    payload: dict[str, Any],
    config: GuardrailConfig,
) -> list[str]:
    """Check resource budget thresholds."""
    violations = []

    # Check for resource reports
    reports = payload.get("reports", [])
    if not isinstance(reports, list):
        return violations

    for report in reports:
        if not isinstance(report, dict):
            continue

        name = report.get("name", "")
        avg_cpu = report.get("avg_cpu_percent", 0)
        max_memory = report.get("max_memory_mb", 0)

        if "idle" in name.lower():
            if avg_cpu > config.idle_cpu_threshold_percent:
                violations.append(
                    f"{name}: avg_cpu={avg_cpu:.1f}% exceeds idle budget {config.idle_cpu_threshold_percent}%"
                )

        if "active" in name.lower():
            if avg_cpu > config.active_cpu_threshold_percent:
                violations.append(
                    f"{name}: avg_cpu={avg_cpu:.1f}% exceeds active budget {config.active_cpu_threshold_percent}%"
                )

        if max_memory > config.memory_threshold_mb:
            violations.append(
                f"{name}: max_memory={max_memory:.1f}MB exceeds budget {config.memory_threshold_mb}MB"
            )

    return violations


def run_benchmarks(iterations: int, output_path: Path | None = None) -> dict[str, Any]:
    """Run benchmarks and optionally save results."""
    # Import here to avoid circular dependencies
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tests.perf.benchmark_runner import run_benchmarks as _run_benchmarks

    suite = _run_benchmarks(output_path=output_path, iterations=iterations)
    return suite.to_dict()


def format_output(
    violations: list[str],
    regressions: list[str],
    resource_violations: list[str],
    component_violations: list[str],
    format_type: str,
) -> str:
    """Format output based on requested format."""
    all_issues = violations + regressions + resource_violations + component_violations

    if format_type == "json":
        import json

        return json.dumps(
            {
                "passed": len(all_issues) == 0,
                "violations": violations,
                "regressions": regressions,
                "resource_violations": resource_violations,
                "component_violations": component_violations,
            },
            indent=2,
        )

    if format_type == "github":
        lines = []
        if all_issues:
            lines.append("::error::Performance guardrails failed")
            for issue in all_issues:
                lines.append(f"::error::{issue}")
        else:
            lines.append("::notice::Performance guardrails passed")
        return "\n".join(lines)

    # Default text format
    lines = []
    if violations:
        lines.append("THRESHOLD VIOLATIONS:")
        for v in violations:
            lines.append(f"  - {v}")

    if regressions:
        lines.append("PERFORMANCE REGRESSIONS:")
        for r in regressions:
            lines.append(f"  - {r}")

    if resource_violations:
        lines.append("RESOURCE BUDGET VIOLATIONS:")
        for r in resource_violations:
            lines.append(f"  - {r}")

    if component_violations:
        lines.append("COMPONENT THRESHOLD VIOLATIONS:")
        for c in component_violations:
            lines.append(f"  - {c}")

    return "\n".join(lines)


def main() -> int:
    args = parse_args()

    # Run benchmarks if requested
    if args.run_benchmarks:
        if args.metrics_file is None:
            args.metrics_file = Path("tests/perf/current_metrics.json")
        run_benchmarks(args.benchmark_iterations, args.metrics_file)

    if args.metrics_file is None:
        print("perf_guardrail_error=--metrics-file is required (unless --run-benchmarks is used)")
        return 2

    # Load current metrics
    try:
        payload = load_metrics(args.metrics_file)
    except FileNotFoundError as e:
        print(f"perf_guardrail_error={e}")
        return 2

    config = GuardrailConfig(
        p50_threshold_ms=args.p50_threshold_ms,
        p95_threshold_ms=args.p95_threshold_ms,
        max_regression_percent=args.max_regression_percent,
    )

    # Extract summary metrics
    metrics = extract_summary_metrics(payload)

    if not metrics:
        print("perf_guardrail_error=metrics JSON must include p50_ms and p95_ms (directly or in summary)")
        return 2

    # Run all checks
    violations = check_absolute_thresholds(metrics, config)

    regressions = []
    if args.baseline_file:
        try:
            baseline_payload = load_metrics(args.baseline_file)
            baseline_metrics = extract_summary_metrics(baseline_payload)
            if baseline_metrics:
                regressions = check_regression(metrics, baseline_metrics, config)
        except FileNotFoundError:
            print(f"perf_guardrail_warning=baseline file not found: {args.baseline_file}")

    resource_violations = check_resource_budgets(payload, config)
    component_violations = check_component_thresholds(payload, config)

    # Format and print output
    all_issues = violations + regressions + resource_violations + component_violations

    output = format_output(
        violations,
        regressions,
        resource_violations,
        component_violations,
        args.output_format,
    )

    if output:
        print(output)

    if not all_issues:
        print("perf_guardrail=ok")
        return 0

    if _parse_enforce(args.enforce):
        print("perf_guardrail=failed")
        return 1

    print("perf_guardrail=soft_fail")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
