"""Static model catalog for runtime model downloads."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ModelCatalogEntry:
    """Download metadata for a single model profile artifact."""

    profile: str
    filename: str
    sha256: str
    mirrors: tuple[str, ...]


DEFAULT_MODEL_CATALOG: dict[str, ModelCatalogEntry] = {
    "tiny": ModelCatalogEntry(
        profile="tiny",
        filename="faster-whisper-tiny-int8.tar.zst",
        sha256="1111111111111111111111111111111111111111111111111111111111111111",
        mirrors=(
            "https://models.voicekey.dev/faster-whisper/tiny/faster-whisper-tiny-int8.tar.zst",
            "https://mirror.voicekey.dev/faster-whisper/tiny/faster-whisper-tiny-int8.tar.zst",
        ),
    ),
    "base": ModelCatalogEntry(
        profile="base",
        filename="faster-whisper-base-int8.tar.zst",
        sha256="2222222222222222222222222222222222222222222222222222222222222222",
        mirrors=(
            "https://models.voicekey.dev/faster-whisper/base/faster-whisper-base-int8.tar.zst",
            "https://mirror.voicekey.dev/faster-whisper/base/faster-whisper-base-int8.tar.zst",
        ),
    ),
    "small": ModelCatalogEntry(
        profile="small",
        filename="faster-whisper-small-int8.tar.zst",
        sha256="3333333333333333333333333333333333333333333333333333333333333333",
        mirrors=(
            "https://models.voicekey.dev/faster-whisper/small/faster-whisper-small-int8.tar.zst",
            "https://mirror.voicekey.dev/faster-whisper/small/faster-whisper-small-int8.tar.zst",
        ),
    ),
}


def get_model_entry(profile: str) -> ModelCatalogEntry:
    """Return catalog entry for ``profile`` or raise ``ValueError``."""
    normalized = profile.strip().lower()
    try:
        return DEFAULT_MODEL_CATALOG[normalized]
    except KeyError as exc:
        supported = ", ".join(sorted(DEFAULT_MODEL_CATALOG))
        raise ValueError(
            f"Unsupported model profile '{profile}'. Expected one of: {supported}."
        ) from exc


__all__ = ["DEFAULT_MODEL_CATALOG", "ModelCatalogEntry", "get_model_entry"]
