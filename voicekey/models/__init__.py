"""Model download and management."""

from voicekey.models.catalog import DEFAULT_MODEL_CATALOG, ModelCatalogEntry, get_model_entry
from voicekey.models.checksum import sha256_file, verify_sha256
from voicekey.models.downloader import (
    MirrorAttempt,
    ModelDownloadError,
    ModelDownloader,
    ModelDownloadResult,
)

__all__ = [
    "DEFAULT_MODEL_CATALOG",
    "MirrorAttempt",
    "ModelCatalogEntry",
    "ModelDownloadError",
    "ModelDownloadResult",
    "ModelDownloader",
    "get_model_entry",
    "sha256_file",
    "verify_sha256",
]
