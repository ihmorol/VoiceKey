"""Unit tests for release changelog parser helpers."""

from __future__ import annotations

import pytest

from voicekey.release.changelog import extract_release_notes


_CHANGELOG_SAMPLE = """
# Changelog

## [Unreleased]

- Draft notes

## [1.2.3] - 2026-02-20

### Added

- Feature A

## [1.2.2] - 2026-02-19

### Fixed

- Bug B
"""


def test_extract_release_notes_returns_target_section_body() -> None:
    notes = extract_release_notes(_CHANGELOG_SAMPLE, version="1.2.3")

    assert "### Added" in notes
    assert "Feature A" in notes
    assert "1.2.2" not in notes


def test_extract_release_notes_accepts_v_prefix() -> None:
    notes = extract_release_notes(_CHANGELOG_SAMPLE, version="v1.2.2")

    assert "### Fixed" in notes
    assert "Bug B" in notes


def test_extract_release_notes_raises_for_missing_version() -> None:
    with pytest.raises(ValueError, match="No changelog section"):
        extract_release_notes(_CHANGELOG_SAMPLE, version="9.9.9")


def test_extract_release_notes_raises_for_empty_section() -> None:
    changelog = "# Changelog\n\n## [1.0.0]\n\n## [0.9.0]\n\n- note\n"
    with pytest.raises(ValueError, match="is empty"):
        extract_release_notes(changelog, version="1.0.0")
