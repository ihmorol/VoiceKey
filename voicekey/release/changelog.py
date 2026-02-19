"""Helpers for extracting versioned release notes from changelog metadata."""

from __future__ import annotations

import re

_SECTION_RE = re.compile(r"^##\s+\[(?P<version>[^\]]+)\](?:\s+-\s+.*)?$", re.MULTILINE)


def extract_release_notes(changelog_text: str, *, version: str) -> str:
    """Return changelog section body for ``version`` or raise ``ValueError``."""
    sections = list(_SECTION_RE.finditer(changelog_text))
    target_index = None
    normalized_version = version.strip().lstrip("v")

    for index, match in enumerate(sections):
        if match.group("version").strip().lstrip("v") == normalized_version:
            target_index = index
            break

    if target_index is None:
        raise ValueError(f"No changelog section found for version '{version}'.")

    start_match = sections[target_index]
    section_start = start_match.end()
    section_end = sections[target_index + 1].start() if target_index + 1 < len(sections) else len(changelog_text)
    section_text = changelog_text[section_start:section_end].strip()

    if not section_text:
        raise ValueError(f"Changelog section for version '{version}' is empty.")

    return section_text


__all__ = ["extract_release_notes"]
