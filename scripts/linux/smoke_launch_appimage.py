"""Run launch smoke command for Linux AppImage artifact."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from voicekey.release.linux_artifacts import build_appimage_smoke_command


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--appimage-path",
        required=True,
        type=Path,
        help="Path to canonical AppImage artifact to smoke test.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=20.0,
        help="Launch command timeout in seconds.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.appimage_path.exists() or not args.appimage_path.is_file():
        raise FileNotFoundError(f"AppImage artifact not found: {args.appimage_path}")

    command = build_appimage_smoke_command(args.appimage_path)
    subprocess.run(command, check=True, timeout=args.timeout_seconds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
