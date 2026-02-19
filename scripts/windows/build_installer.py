"""Build Windows installer artifact with optional code signing."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from voicekey.release.windows_artifacts import build_signtool_command, prepare_installer_artifact


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True, help="Release version (for example 1.2.3).")
    parser.add_argument(
        "--unsigned-installer-path",
        required=True,
        type=Path,
        help="Path to unsigned installer .exe produced by installer toolchain.",
    )
    parser.add_argument(
        "--output-dir",
        default="dist",
        type=Path,
        help="Directory where canonical installer artifact is written.",
    )
    parser.add_argument(
        "--signtool-path",
        default=None,
        type=Path,
        help="Optional path to signtool.exe for Authenticode signing.",
    )
    parser.add_argument(
        "--certificate-thumbprint",
        default=os.getenv("VOICEKEY_SIGN_CERT_SHA1"),
        help="Certificate thumbprint used by signtool (or VOICEKEY_SIGN_CERT_SHA1).",
    )
    parser.add_argument(
        "--timestamp-url",
        default=os.getenv("VOICEKEY_SIGN_TIMESTAMP_URL", "http://timestamp.digicert.com"),
        help="RFC3161 timestamp URL for signing.",
    )
    return parser.parse_args()


def sign_file(*, signtool_path: Path, thumbprint: str, timestamp_url: str, target: Path) -> None:
    command = build_signtool_command(
        signtool_path=signtool_path,
        certificate_thumbprint=thumbprint,
        timestamp_url=timestamp_url,
        target_path=target,
    )
    subprocess.run(command, check=True)


def main() -> int:
    args = parse_args()
    artifact = prepare_installer_artifact(
        version=args.version,
        unsigned_installer_path=args.unsigned_installer_path,
        output_dir=args.output_dir,
    )

    if args.signtool_path is not None:
        if not args.certificate_thumbprint:
            raise ValueError(
                "Code signing requested but no certificate thumbprint provided. "
                "Use --certificate-thumbprint or VOICEKEY_SIGN_CERT_SHA1."
            )
        sign_file(
            signtool_path=args.signtool_path,
            thumbprint=args.certificate_thumbprint,
            timestamp_url=args.timestamp_url,
            target=artifact,
        )

    print(artifact)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
