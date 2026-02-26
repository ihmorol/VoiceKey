"""Unit tests for model catalog helpers."""

from __future__ import annotations

import re

import pytest

from voicekey.models.catalog import DEFAULT_MODEL_CATALOG, get_model_entry


def test_get_model_entry_returns_known_profile() -> None:
    entry = get_model_entry("BASE")

    assert entry.profile == "base"
    assert entry.filename
    assert entry.mirrors


def test_get_model_entry_raises_for_unknown_profile() -> None:
    with pytest.raises(ValueError, match="Unsupported model profile"):
        get_model_entry("xl")


def test_default_catalog_contains_required_profiles() -> None:
    assert set(DEFAULT_MODEL_CATALOG) == {"tiny", "base", "small"}


def test_default_catalog_entries_have_valid_sha256_values() -> None:
    sha256_pattern = re.compile(r"^[0-9a-f]{64}$")

    for profile, entry in DEFAULT_MODEL_CATALOG.items():
        assert sha256_pattern.fullmatch(entry.sha256), (
            f"Catalog entry '{profile}' has invalid sha256 value: {entry.sha256!r}"
        )
