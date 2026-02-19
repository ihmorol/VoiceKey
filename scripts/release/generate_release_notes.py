"""Generate release notes from CHANGELOG metadata for a target version."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from voicekey.release.changelog import extract_release_notes  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--changelog", type=Path, default=PROJECT_ROOT / "CHANGELOG.md")
    parser.add_argument("--version", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    changelog_text = args.changelog.read_text(encoding="utf-8")
    notes = extract_release_notes(changelog_text, version=args.version)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(notes.strip() + "\n", encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
