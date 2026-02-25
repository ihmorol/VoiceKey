"""Model download orchestration for CLI command."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from voicekey.models.downloader import ModelDownloader, ModelDownloadResult
from voicekey.models.catalog import ModelCatalogEntry, get_model_entry

if TYPE_CHECKING:
    from voicekey.audio.vad import SILERO_VAD_AVAILABLE

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ModelStatus:
    """Status of a model in the local cache."""

    name: str
    installed: bool
    path: Path | None = None
    checksum_valid: bool | None = None
    profile: str | None = None


@dataclass(frozen=True)
class DownloadResult:
    """Result of a model download operation."""

    name: str
    success: bool
    profile: str | None = None
    path: Path | None = None
    reused: bool = False
    error: str | None = None


class ModelDownloadManager:
    """Orchestrates model downloads for ASR and VAD models."""

    def __init__(self, model_dir: Path) -> None:
        """Initialize the download manager.

        Args:
            model_dir: Directory where models are stored.
        """
        self._model_dir = model_dir
        self._downloader = ModelDownloader()

    @property
    def model_dir(self) -> Path:
        """Return the model directory path."""
        return self._model_dir

    def get_asr_status(self, profile: str) -> ModelStatus:
        """Check the status of an ASR model.

        Args:
            profile: Model profile (tiny, base, small).

        Returns:
            ModelStatus with installation state.
        """
        try:
            entry = get_model_entry(profile)
        except ValueError:
            return ModelStatus(name=f"asr_{profile}", installed=False)

        model_path = self._model_dir / entry.filename
        if not model_path.exists():
            return ModelStatus(
                name=f"asr_{profile}",
                installed=False,
                path=model_path,
                profile=profile,
            )

        # Verify checksum
        from voicekey.models.checksum import verify_sha256

        is_valid = verify_sha256(model_path, expected_sha256=entry.sha256)
        return ModelStatus(
            name=f"asr_{profile}",
            installed=is_valid,
            path=model_path,
            checksum_valid=is_valid,
            profile=profile,
        )

    def get_vad_status(self) -> ModelStatus:
        """Check the status of the VAD model.

        Returns:
            ModelStatus with VAD installation state.
        """
        # Silero VAD auto-downloads from the package
        # We check if the silero-vad package can be loaded
        try:
            from silero_vad import load_silero_vad

            # Try to load the model (this triggers download if needed)
            load_silero_vad()
            return ModelStatus(name="vad", installed=True, profile="silero-vad")
        except ImportError:
            return ModelStatus(name="vad", installed=False, profile="silero-vad")
        except Exception as e:
            logger.warning(f"VAD model check failed: {e}")
            return ModelStatus(name="vad", installed=False, profile="silero-vad")

    def get_all_status(self) -> dict[str, ModelStatus]:
        """Get status of all known models.

        Returns:
            Dictionary mapping model names to their status.
        """
        status: dict[str, ModelStatus] = {}

        # Check ASR models
        for profile in ("tiny", "base", "small"):
            status[f"asr_{profile}"] = self.get_asr_status(profile)

        # Check VAD
        status["vad"] = self.get_vad_status()

        return status

    def download_asr(
        self,
        profile: str,
        force: bool = False,
        entry: ModelCatalogEntry | None = None,
    ) -> DownloadResult:
        """Download an ASR model.

        Args:
            profile: Model profile to download.
            force: Force re-download even if model exists.
            entry: Optional catalog entry (for testing).

        Returns:
            DownloadResult with operation outcome.
        """
        try:
            result: ModelDownloadResult = self._downloader.download_profile(
                profile=profile,
                model_dir=self._model_dir,
                force=force,
                entry=entry,
            )
            return DownloadResult(
                name=f"asr_{profile}",
                success=True,
                profile=profile,
                path=result.target_path,
                reused=result.reused_existing,
            )
        except Exception as e:
            logger.error(f"Failed to download ASR model {profile}: {e}")
            return DownloadResult(
                name=f"asr_{profile}",
                success=False,
                profile=profile,
                error=str(e),
            )

    def download_vad(self) -> DownloadResult:
        """Ensure VAD model is available.

        For Silero VAD, this just triggers a load check which will
        auto-download if needed.

        Returns:
            DownloadResult with operation outcome.
        """
        try:
            from silero import vad as silero_vad_loader

            # This triggers auto-download if needed
            silero_vad_loader()
            return DownloadResult(
                name="vad",
                success=True,
                profile="silero-vad",
            )
        except ImportError:
            return DownloadResult(
                name="vad",
                success=False,
                profile="silero-vad",
                error="silero-vad package not installed. Install with: pip install silero-vad",
            )
        except Exception as e:
            logger.error(f"Failed to ensure VAD model: {e}")
            return DownloadResult(
                name="vad",
                success=False,
                profile="silero-vad",
                error=str(e),
            )

    def download_all(self, force: bool = False) -> list[DownloadResult]:
        """Download all models.

        Args:
            force: Force re-download of existing models.

        Returns:
            List of DownloadResult for each model.
        """
        results: list[DownloadResult] = []

        # Download all ASR profiles
        for profile in ("tiny", "base", "small"):
            results.append(self.download_asr(profile, force=force))

        # Download VAD
        results.append(self.download_vad())

        return results


__all__ = [
    "DownloadResult",
    "ModelDownloadManager",
    "ModelStatus",
]
