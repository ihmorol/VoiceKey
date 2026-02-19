"""Generate release integrity bundle files for built artifacts."""

from __future__ import annotations

import argparse
import json
import platform
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from voicekey.release.integrity import (  # noqa: E402
    build_cyclonedx_sbom,
    build_provenance_manifest,
    build_sha256sums,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--commit-hash", required=True)
    parser.add_argument("--build-timestamp-utc", required=True)
    parser.add_argument("--release-version", default="0.1.0")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    artifact_paths = sorted([p for p in args.artifacts_dir.iterdir() if p.is_file()], key=lambda p: p.name)

    args.output_dir.mkdir(parents=True, exist_ok=True)

    checksums_path = args.output_dir / "SHA256SUMS"
    checksums_path.write_text(build_sha256sums(artifact_paths) + "\n", encoding="utf-8")

    sbom_payload = build_cyclonedx_sbom(
        artifact_paths=artifact_paths,
        release_version=args.release_version,
    )
    (args.output_dir / "sbom.cyclonedx.json").write_text(
        json.dumps(sbom_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    provenance_payload = build_provenance_manifest(
        artifact_paths=artifact_paths,
        commit_hash=args.commit_hash,
        build_timestamp_utc=args.build_timestamp_utc,
        toolchain={
            "python": platform.python_version(),
            "platform": platform.platform(),
            "builder": "local-script",
        },
    )
    (args.output_dir / "provenance.json").write_text(
        json.dumps(provenance_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
