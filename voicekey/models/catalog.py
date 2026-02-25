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
        sha256="",
        mirrors=(
            "https://huggingface.co/guillaumekln/faster-whisper-tiny/resolve/main/model.bin",
        ),
    ),
    "base": ModelCatalogEntry(
        profile="base",
        filename="faster-whisper-base-int8.tar.zst",
        sha256="",
        mirrors=(
            "https://huggingface.co/guillaumekln/faster-whisper-base/resolve/main/model.bin",
        ),
    ),
    "small": ModelCatalogEntry(
        profile="small",
        filename="faster-whisper-small-int8.tar.zst",
        sha256="",
        mirrors=(
            "https://huggingface.co/guillaumekln/faster-whisper-small/resolve/main/model.bin",
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
