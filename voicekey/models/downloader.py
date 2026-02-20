"""Model downloader with checksum verification and mirror fallback."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from voicekey.models.catalog import ModelCatalogEntry, get_model_entry
from voicekey.models.checksum import verify_sha256


@dataclass(frozen=True, slots=True)
class MirrorAttempt:
    """Result details for one mirror URL attempt."""

    url: str
    success: bool
    error: str | None = None


@dataclass(frozen=True, slots=True)
class ModelDownloadResult:
    """Successful model download outcome payload."""

    profile: str
    target_path: Path
    used_mirror: str
    checksum_verified: bool
    reused_existing: bool
    attempts: tuple[MirrorAttempt, ...]


class ModelDownloadError(RuntimeError):
    """Raised when all mirrors fail or checksum verification fails."""


class ModelDownloader:
    """Download model artifacts with deterministic checksum checks."""

    def __init__(self, *, timeout_seconds: float = 30.0, chunk_size: int = 1024 * 64) -> None:
        self._timeout_seconds = timeout_seconds
        self._chunk_size = chunk_size

    def download_profile(
        self,
        *,
        profile: str,
        model_dir: Path,
        force: bool = False,
        entry: ModelCatalogEntry | None = None,
    ) -> ModelDownloadResult:
        """Download ``profile`` into ``model_dir`` using mirror fallback behavior."""
        catalog_entry = entry or get_model_entry(profile)
        target_path = model_dir / catalog_entry.filename
        model_dir.mkdir(parents=True, exist_ok=True)

        attempts: list[MirrorAttempt] = []
        if target_path.exists() and not force:
            if verify_sha256(target_path, expected_sha256=catalog_entry.sha256):
                reused = MirrorAttempt(url="local_cache", success=True)
                attempts.append(reused)
                return ModelDownloadResult(
                    profile=catalog_entry.profile,
                    target_path=target_path,
                    used_mirror="local_cache",
                    checksum_verified=True,
                    reused_existing=True,
                    attempts=tuple(attempts),
                )
            target_path.unlink()

        for mirror_url in catalog_entry.mirrors:
            temp_path = target_path.with_suffix(target_path.suffix + ".download")
            try:
                self._download_url_to_file(mirror_url, temp_path)
                if not verify_sha256(temp_path, expected_sha256=catalog_entry.sha256):
                    temp_path.unlink(missing_ok=True)
                    attempts.append(
                        MirrorAttempt(
                            url=mirror_url,
                            success=False,
                            error="checksum_mismatch",
                        )
                    )
                    continue

                temp_path.replace(target_path)
                attempts.append(MirrorAttempt(url=mirror_url, success=True))
                return ModelDownloadResult(
                    profile=catalog_entry.profile,
                    target_path=target_path,
                    used_mirror=mirror_url,
                    checksum_verified=True,
                    reused_existing=False,
                    attempts=tuple(attempts),
                )
            except (OSError, URLError) as exc:
                temp_path.unlink(missing_ok=True)
                attempts.append(MirrorAttempt(url=mirror_url, success=False, error=str(exc)))

        raise ModelDownloadError(
            f"Failed to download model profile '{catalog_entry.profile}' from all mirrors."
        )

    def _download_url_to_file(self, url: str, target_path: Path) -> None:
        # Security: Only allow HTTPS for remote downloads. file:// URLs are allowed
        # for local files which don't pose a MITM risk.
        url_lower = url.lower()
        if url_lower.startswith("http://"):
            raise ModelDownloadError(
                f"Security: model downloads require HTTPS. Rejected insecure URL: {url}"
            )
        request = Request(url, headers={"User-Agent": "voicekey-model-downloader/1"})
        with urlopen(request, timeout=self._timeout_seconds) as response:
            with target_path.open("wb") as handle:
                while True:
                    chunk = response.read(self._chunk_size)
                    if not chunk:
                        break
                    handle.write(chunk)


__all__ = [
    "MirrorAttempt",
    "ModelDownloadError",
    "ModelDownloadResult",
    "ModelDownloader",
]
