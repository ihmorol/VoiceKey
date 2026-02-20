"""Model download and management."""

from voicekey.models.catalog import DEFAULT_MODEL_CATALOG, ModelCatalogEntry, get_model_entry
from voicekey.models.checksum import sha256_file, verify_sha256
from voicekey.models.download_manager import (
    DownloadResult,
    ModelDownloadManager,
    ModelStatus,
)
from voicekey.models.downloader import (
    MirrorAttempt,
    ModelDownloadError,
    ModelDownloader,
    ModelDownloadResult,
)

__all__ = [
    "DEFAULT_MODEL_CATALOG",
    "DownloadResult",
    "MirrorAttempt",
    "ModelCatalogEntry",
    "ModelDownloadError",
    "ModelDownloadManager",
    "ModelDownloadResult",
    "ModelDownloader",
    "ModelStatus",
    "get_model_entry",
    "sha256_file",
    "verify_sha256",
]
