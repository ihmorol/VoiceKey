"""Unit tests for optional fuzzy command parsing (E02-S03)."""

from __future__ import annotations

import pytest

from voicekey.commands.builtins import create_builtin_registry
from voicekey.commands.parser import CommandParser, FuzzyMatchConfig, ParseKind


def test_fuzzy_disabled_by_default_typo_stays_literal() -> None:
    parser = CommandParser(registry=create_builtin_registry())

    result = parser.parse("new lnie command")

    assert result.kind is ParseKind.TEXT
    assert result.command is None
    assert result.literal_text == "new lnie command"


def test_fuzzy_enabled_typo_resolves_when_score_meets_threshold() -> None:
    parser = CommandParser(
        registry=create_builtin_registry(),
        fuzzy=FuzzyMatchConfig(enabled=True, threshold=0.8),
    )

    result = parser.parse("new lnie command")

    assert result.kind is ParseKind.COMMAND
    assert result.command is not None
    assert result.command.command_id == "new_line"


def test_fuzzy_enabled_low_similarity_phrase_does_not_match() -> None:
    parser = CommandParser(
        registry=create_builtin_registry(),
        fuzzy=FuzzyMatchConfig(enabled=True, threshold=0.8),
    )

    result = parser.parse("zebra helicopter command")

    assert result.kind is ParseKind.TEXT
    assert result.command is None
    assert result.literal_text == "zebra helicopter command"


@pytest.mark.parametrize("threshold", (-0.1, 1.1))
def test_fuzzy_threshold_must_be_within_zero_to_one(threshold: float) -> None:
    with pytest.raises(ValueError):
        FuzzyMatchConfig(enabled=True, threshold=threshold)
