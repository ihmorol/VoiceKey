"""Generate release notes from CHANGELOG metadata for a target version."""

from __future__ import annotations

import argparse
import subprocess
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
    parser.add_argument("--include-commit-metadata", action="store_true")
    return parser.parse_args()


def _build_commit_metadata(version: str) -> str:
    normalized = version.lstrip("v")
    target_tag = f"v{normalized}"

    try:
        tag_list = subprocess.check_output(
            ["git", "tag", "--sort=-creatordate"],
            text=True,
            cwd=PROJECT_ROOT,
        ).splitlines()
    except subprocess.CalledProcessError:
        return "- commit metadata unavailable (failed to query tags)"

    previous_tag = next((tag for tag in tag_list if tag != target_tag), None)
    revision_range = f"{previous_tag}..{target_tag}" if previous_tag is not None else target_tag

    try:
        commits = subprocess.check_output(
            ["git", "log", "--pretty=format:- %h %s (%an)", revision_range],
            text=True,
            cwd=PROJECT_ROOT,
        ).strip()
    except subprocess.CalledProcessError:
        return "- commit metadata unavailable (failed to query commit range)"

    return commits if commits else "- no commits found for release range"


def main() -> int:
    args = parse_args()
    changelog_text = args.changelog.read_text(encoding="utf-8")
    notes = extract_release_notes(changelog_text, version=args.version)

    if args.include_commit_metadata:
        notes = (
            notes.strip()
            + "\n\n## Commit Metadata\n\n"
            + _build_commit_metadata(args.version)
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(notes.strip() + "\n", encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
