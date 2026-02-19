"""Create detached signature for release checksum bundle."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from voicekey.release.signing import (  # noqa: E402
    build_gpg_detached_sign_command,
    build_verify_tag_signature_command,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checksums-file", required=True, type=Path)
    parser.add_argument("--signature-file", required=True, type=Path)
    parser.add_argument("--gpg-path", default="gpg")
    parser.add_argument("--key-id", default=None)
    parser.add_argument("--verify-tag", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.verify_tag is not None:
        verify_command = build_verify_tag_signature_command(args.verify_tag)
        subprocess.run(verify_command, check=True)

    command = build_gpg_detached_sign_command(
        input_file=args.checksums_file,
        output_signature_file=args.signature_file,
        key_id=args.key_id,
    )
    command[0] = args.gpg_path
    subprocess.run(command, check=True)
    print(args.signature_file)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
