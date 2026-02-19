"""Validate release artifact naming and compatibility policy constraints."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from voicekey.release.policy import validate_release_policy  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts-dir", required=True, type=Path)
    parser.add_argument("--release-version", required=True)
    parser.add_argument(
        "--checklist-path",
        type=Path,
        default=PROJECT_ROOT / "requirements" / "release-checklist.md",
    )
    parser.add_argument(
        "--distribution-path",
        type=Path,
        default=PROJECT_ROOT / "requirements" / "distribution.md",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    artifact_names = sorted(
        [path.name for path in args.artifacts_dir.iterdir() if path.is_file()],
    )
    checklist_text = args.checklist_path.read_text(encoding="utf-8")
    distribution_text = args.distribution_path.read_text(encoding="utf-8")

    report = validate_release_policy(
        artifact_names=artifact_names,
        release_version=args.release_version,
        checklist_text=checklist_text,
        distribution_text=distribution_text,
    )

    if report.ok:
        print("release_policy=ok")
        return 0

    for error in report.errors:
        print(f"release_policy_error={error}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
