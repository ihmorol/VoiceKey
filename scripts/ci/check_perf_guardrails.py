"""Evaluate performance guardrails from metrics JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metrics-file", required=True, type=Path)
    parser.add_argument("--p50-threshold-ms", type=float, default=200.0)
    parser.add_argument("--p95-threshold-ms", type=float, default=350.0)
    parser.add_argument("--enforce", default="0")
    return parser.parse_args()


def _parse_enforce(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def main() -> int:
    args = parse_args()
    payload = json.loads(args.metrics_file.read_text(encoding="utf-8"))

    if "p50_ms" not in payload or "p95_ms" not in payload:
        print("perf_guardrail_error=metrics JSON must include p50_ms and p95_ms")
        return 2

    p50_ms = float(payload["p50_ms"])
    p95_ms = float(payload["p95_ms"])
    violations: list[str] = []

    if p50_ms > args.p50_threshold_ms:
        violations.append(f"p50_ms={p50_ms} exceeds threshold={args.p50_threshold_ms}")
    if p95_ms > args.p95_threshold_ms:
        violations.append(f"p95_ms={p95_ms} exceeds threshold={args.p95_threshold_ms}")

    if not violations:
        print("perf_guardrail=ok")
        return 0

    for violation in violations:
        print(f"perf_guardrail_violation={violation}")

    if _parse_enforce(args.enforce):
        return 1

    print("perf_guardrail=soft_fail")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
