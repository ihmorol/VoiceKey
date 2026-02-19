"""Coverage tests for built-in command catalog phrases and aliases."""

from __future__ import annotations

import pytest

from voicekey.commands.builtins import SPECIAL_PHRASES, builtin_commands, create_builtin_registry
from voicekey.commands.parser import COMMAND_SUFFIX, CommandParser, ParseKind
from voicekey.commands.registry import CommandChannel, FeatureGate, normalize_phrase


def _command_phrases(*, feature_gate: FeatureGate | None) -> tuple[tuple[str, str], ...]:
    phrases: list[tuple[str, str]] = []
    for command in builtin_commands():
        if command.channel is not CommandChannel.COMMAND:
            continue
        if command.feature_gate is not feature_gate:
            continue
        for phrase in (command.phrase, *command.aliases):
            phrases.append((phrase, command.command_id))
    return tuple(phrases)


UNGATED_COMMAND_PHRASES = _command_phrases(feature_gate=None)
WINDOW_GATED_COMMAND_PHRASES = _command_phrases(feature_gate=FeatureGate.WINDOW_COMMANDS)
SYSTEM_PHRASES = tuple(
    (command.phrase, command.command_id)
    for command in builtin_commands()
    if command.channel is CommandChannel.SYSTEM
)


@pytest.mark.parametrize(("phrase", "command_id"), UNGATED_COMMAND_PHRASES)
def test_every_ungated_builtin_phrase_and_alias_parses_as_command(
    phrase: str, command_id: str
) -> None:
    parser = CommandParser(registry=create_builtin_registry())

    transcript = f"{phrase} {COMMAND_SUFFIX}"
    result = parser.parse(transcript)

    assert result.kind is ParseKind.COMMAND
    assert result.command is not None
    assert result.command.command_id == command_id
    assert result.literal_text is None


@pytest.mark.parametrize(("phrase", "command_id"), SYSTEM_PHRASES)
def test_every_system_phrase_parses_without_command_suffix(phrase: str, command_id: str) -> None:
    parser = CommandParser(registry=create_builtin_registry())

    result = parser.parse(phrase)

    assert result.kind is ParseKind.SYSTEM
    assert result.command is not None
    assert result.command.command_id == command_id


@pytest.mark.parametrize(("phrase", "_command_id"), WINDOW_GATED_COMMAND_PHRASES)
def test_window_productivity_phrases_are_unavailable_by_default(
    phrase: str, _command_id: str
) -> None:
    parser = CommandParser(registry=create_builtin_registry())

    transcript = f"{phrase} {COMMAND_SUFFIX}"
    result = parser.parse(transcript)

    assert result.kind is ParseKind.TEXT
    assert result.command is None
    assert result.literal_text == normalize_phrase(transcript)


@pytest.mark.parametrize(("phrase", "command_id"), WINDOW_GATED_COMMAND_PHRASES)
def test_window_productivity_phrases_are_available_when_feature_enabled(
    phrase: str, command_id: str
) -> None:
    registry = create_builtin_registry(enabled_features={FeatureGate.WINDOW_COMMANDS})
    parser = CommandParser(registry=registry)

    result = parser.parse(f"{phrase} {COMMAND_SUFFIX}")

    assert result.kind is ParseKind.COMMAND
    assert result.command is not None
    assert result.command.command_id == command_id


def test_parser_special_phrase_list_is_derived_from_builtin_catalog() -> None:
    expected_special_phrases = tuple(normalize_phrase(phrase) for phrase, _ in SYSTEM_PHRASES)

    assert SPECIAL_PHRASES == expected_special_phrases
