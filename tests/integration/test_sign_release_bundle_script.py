"""Integration tests for release checksum signing script (E07-S04)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_sign_release_bundle_uses_configured_signer_and_writes_signature(tmp_path: Path) -> None:
    checksums = tmp_path / "SHA256SUMS"
    checksums.write_text("abc  file\n", encoding="utf-8")
    signature = tmp_path / "SHA256SUMS.sig"

    fake_gpg = tmp_path / "fake-gpg"
    fake_gpg.write_text(
        "#!/usr/bin/env sh\n"
        "OUT=''\n"
        "while [ $# -gt 0 ]; do\n"
        "  if [ \"$1\" = \"--output\" ]; then\n"
        "    shift\n"
        "    OUT=\"$1\"\n"
        "  fi\n"
        "  shift\n"
        "done\n"
        "printf 'signed' > \"$OUT\"\n",
        encoding="utf-8",
    )
    fake_gpg.chmod(0o755)

    project_root = Path(__file__).resolve().parents[2]
    script = project_root / "scripts" / "release" / "sign_release_bundle.py"

    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--checksums-file",
            str(checksums),
            "--signature-file",
            str(signature),
            "--gpg-path",
            str(fake_gpg),
            "--key-id",
            "DEADBEEF",
        ],
        check=False,
        capture_output=True,
        text=True,
        env=os.environ.copy(),
    )

    assert result.returncode == 0
    assert signature.exists()
    assert signature.read_text(encoding="utf-8") == "signed"
