"""Generate rollback and yank guidance artifact for failed release smoke checks."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True, help="Release version without leading 'v'.")
    parser.add_argument("--reason", required=True, help="Short rollback trigger reason.")
    parser.add_argument("--incident-log", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    tag = f"v{args.version}"
    guidance = {
        "version": args.version,
        "tag": tag,
        "reason": args.reason,
        "generated_at_utc": datetime.now(tz=UTC).isoformat(),
        "actions": {
            "pypi_yank": f"twine yank voicekey -r pypi {args.version}",
            "github_mark_superseded": (
                f"gh release edit {tag} --latest=false --notes 'Superseded due to post-publish regression'"
            ),
            "hotfix_timeline_note": (
                "gh release create <next-tag> --notes 'Hotfix timeline: publish within SLA window'"
            ),
        },
    }

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(guidance, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    log_lines = [
        "# Release Rollback Incident",
        "",
        f"- Version: `{args.version}`",
        f"- Tag: `{tag}`",
        f"- Trigger: {args.reason}",
        f"- Generated: {guidance['generated_at_utc']}",
        "",
        "## Required Actions",
        "",
        f"1. `{guidance['actions']['pypi_yank']}`",
        f"2. `{guidance['actions']['github_mark_superseded']}`",
        f"3. `{guidance['actions']['hotfix_timeline_note']}`",
    ]
    args.incident_log.parent.mkdir(parents=True, exist_ok=True)
    args.incident_log.write_text("\n".join(log_lines) + "\n", encoding="utf-8")

    print(args.output_json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
