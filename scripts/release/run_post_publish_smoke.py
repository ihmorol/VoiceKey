"""Run post-publish smoke checks for release channels."""

from __future__ import annotations

import argparse
import subprocess
import sys
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from voicekey.release.linux_artifacts import build_appimage_smoke_command  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--channel",
        required=True,
        choices=("pypi", "appimage", "windows-portable", "windows-installer"),
    )
    parser.add_argument("--version", required=True, help="Release version without leading 'v'.")
    parser.add_argument("--artifact-path", type=Path, default=None)
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    parser.add_argument("--python-executable", default=sys.executable)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def _run(command: list[str], *, timeout_seconds: float, dry_run: bool) -> None:
    print("smoke_command=" + " ".join(command))
    if dry_run:
        return
    subprocess.run(command, check=True, timeout=timeout_seconds)


def _smoke_pypi(*, version: str, python_executable: str, timeout_seconds: float, dry_run: bool) -> None:
    install_command = [python_executable, "-m", "pip", "install", "--no-cache-dir", f"voicekey=={version}"]
    help_command = ["voicekey", "--help"]
    _run(install_command, timeout_seconds=timeout_seconds, dry_run=dry_run)
    _run(help_command, timeout_seconds=timeout_seconds, dry_run=dry_run)


def _require_artifact(path: Path | None, *, channel: str) -> Path:
    if path is None:
        raise ValueError(f"--artifact-path is required for channel '{channel}'.")
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"Artifact not found for channel '{channel}': {path}")
    return path


def _smoke_appimage(*, artifact_path: Path | None, timeout_seconds: float, dry_run: bool) -> None:
    appimage = _require_artifact(artifact_path, channel="appimage")
    command = build_appimage_smoke_command(appimage)
    _run(command, timeout_seconds=timeout_seconds, dry_run=dry_run)


def _smoke_windows_portable(*, artifact_path: Path | None) -> None:
    archive_path = _require_artifact(artifact_path, channel="windows-portable")
    with zipfile.ZipFile(archive_path) as archive:
        members = [member.lower() for member in archive.namelist()]
    if not any(member.endswith("voicekey.exe") for member in members):
        raise RuntimeError(
            "windows-portable smoke failed: archive does not contain a voicekey.exe payload."
        )
    print(f"portable_archive_ok={archive_path}")


def _smoke_windows_installer(*, artifact_path: Path | None) -> None:
    installer_path = _require_artifact(artifact_path, channel="windows-installer")
    if installer_path.suffix.lower() != ".exe":
        raise RuntimeError("windows-installer smoke failed: artifact must be .exe")
    if installer_path.stat().st_size <= 0:
        raise RuntimeError("windows-installer smoke failed: installer artifact is empty")
    print(f"installer_artifact_ok={installer_path}")


def main() -> int:
    args = parse_args()

    if args.channel == "pypi":
        _smoke_pypi(
            version=args.version,
            python_executable=args.python_executable,
            timeout_seconds=args.timeout_seconds,
            dry_run=args.dry_run,
        )
    elif args.channel == "appimage":
        _smoke_appimage(
            artifact_path=args.artifact_path,
            timeout_seconds=args.timeout_seconds,
            dry_run=args.dry_run,
        )
    elif args.channel == "windows-portable":
        _smoke_windows_portable(artifact_path=args.artifact_path)
    elif args.channel == "windows-installer":
        _smoke_windows_installer(artifact_path=args.artifact_path)

    print(f"post_publish_smoke=ok channel={args.channel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
