"""Build Linux AppImage artifact into canonical release filename."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from voicekey.release.linux_artifacts import prepare_appimage_artifact


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True, help="Release version (for example 1.2.3).")
    parser.add_argument(
        "--unsigned-appimage-path",
        required=True,
        type=Path,
        help="Path to unsigned AppImage produced by builder toolchain.",
    )
    parser.add_argument(
        "--output-dir",
        default="dist",
        type=Path,
        help="Directory where canonical AppImage artifact is written.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    artifact = prepare_appimage_artifact(
        version=args.version,
        unsigned_appimage_path=args.unsigned_appimage_path,
        output_dir=args.output_dir,
    )
    print(artifact)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
