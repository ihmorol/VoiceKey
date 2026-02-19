"""Unit tests for model downloader mirror and checksum behavior."""

from __future__ import annotations

import hashlib

import pytest

from voicekey.models.catalog import ModelCatalogEntry
from voicekey.models.downloader import ModelDownloadError, ModelDownloader


def _sha256_for_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def test_download_profile_uses_existing_cache_when_checksum_matches(tmp_path) -> None:
    model_dir = tmp_path / "models"
    model_dir.mkdir(parents=True)
    payload = b"cached-model"
    model_path = model_dir / "model.bin"
    model_path.write_bytes(payload)

    entry = ModelCatalogEntry(
        profile="base",
        filename="model.bin",
        sha256=_sha256_for_bytes(payload),
        mirrors=("https://example.invalid/unused",),
    )

    downloader = ModelDownloader()
    result = downloader.download_profile(profile="base", model_dir=model_dir, entry=entry)

    assert result.reused_existing is True
    assert result.used_mirror == "local_cache"
    assert result.target_path == model_path


def test_download_profile_falls_back_to_second_mirror(tmp_path) -> None:
    payload = b"downloaded-model"
    source = tmp_path / "source-model.bin"
    source.write_bytes(payload)
    first_url = (tmp_path / "missing.bin").as_uri()
    second_url = source.as_uri()

    entry = ModelCatalogEntry(
        profile="tiny",
        filename="tiny.bin",
        sha256=_sha256_for_bytes(payload),
        mirrors=(first_url, second_url),
    )

    downloader = ModelDownloader()
    model_dir = tmp_path / "models"
    result = downloader.download_profile(profile="tiny", model_dir=model_dir, entry=entry)

    assert result.reused_existing is False
    assert result.used_mirror == second_url
    assert result.target_path.read_bytes() == payload
    assert len(result.attempts) == 2
    assert result.attempts[0].success is False
    assert result.attempts[1].success is True


def test_download_profile_retries_after_checksum_mismatch(tmp_path) -> None:
    bad_source = tmp_path / "bad.bin"
    bad_source.write_bytes(b"corrupt")
    good_payload = b"valid"
    good_source = tmp_path / "good.bin"
    good_source.write_bytes(good_payload)

    entry = ModelCatalogEntry(
        profile="small",
        filename="small.bin",
        sha256=_sha256_for_bytes(good_payload),
        mirrors=(bad_source.as_uri(), good_source.as_uri()),
    )

    downloader = ModelDownloader()
    result = downloader.download_profile(profile="small", model_dir=tmp_path / "models", entry=entry)

    assert result.target_path.read_bytes() == good_payload
    assert result.attempts[0].error == "checksum_mismatch"
    assert result.attempts[1].success is True


def test_download_profile_raises_when_all_mirrors_fail(tmp_path) -> None:
    entry = ModelCatalogEntry(
        profile="base",
        filename="base.bin",
        sha256="f" * 64,
        mirrors=((tmp_path / "missing-1.bin").as_uri(), (tmp_path / "missing-2.bin").as_uri()),
    )

    downloader = ModelDownloader()

    with pytest.raises(ModelDownloadError):
        downloader.download_profile(profile="base", model_dir=tmp_path / "models", entry=entry)
