"""Unit tests for command parser core contract (E02-S02)."""

from __future__ import annotations

from voicekey.commands.builtins import create_builtin_registry
from voicekey.commands.parser import CommandParser, ParseKind
from voicekey.commands.registry import FeatureGate


def test_phrase_ending_with_command_is_candidate() -> None:
    parser = CommandParser(registry=create_builtin_registry())

    result = parser.parse("new line command")

    assert result.kind is ParseKind.COMMAND
    assert result.command is not None
    assert result.command.command_id == "new_line"
    assert result.literal_text is None


def test_unknown_command_candidate_types_full_literal_including_suffix() -> None:
    parser = CommandParser(registry=create_builtin_registry())

    result = parser.parse("hello world command")

    assert result.kind is ParseKind.TEXT
    assert result.literal_text == "hello world command"
    assert result.command is None


def test_command_matching_is_case_insensitive_and_alias_aware() -> None:
    parser = CommandParser(registry=create_builtin_registry())

    result = parser.parse("EnTeR   CoMmAnD")

    assert result.kind is ParseKind.COMMAND
    assert result.command is not None
    assert result.command.command_id == "new_line"


def test_special_phrase_pause_has_precedence_without_command_suffix() -> None:
    parser = CommandParser(registry=create_builtin_registry())

    result = parser.parse("  PAUSE    voice   KEY ")

    assert result.kind is ParseKind.SYSTEM
    assert result.command is not None
    assert result.command.command_id == "pause_voice_key"


def test_special_phrase_resume_has_precedence_without_command_suffix() -> None:
    parser = CommandParser(registry=create_builtin_registry())

    result = parser.parse("resume voice key")

    assert result.kind is ParseKind.SYSTEM
    assert result.command is not None
    assert result.command.command_id == "resume_voice_key"


def test_special_phrase_stop_has_precedence_without_command_suffix() -> None:
    parser = CommandParser(registry=create_builtin_registry())

    result = parser.parse("voice key stop")

    assert result.kind is ParseKind.SYSTEM
    assert result.command is not None
    assert result.command.command_id == "voice_key_stop"


def test_non_command_phrase_is_typed_literal_text() -> None:
    parser = CommandParser(registry=create_builtin_registry())

    result = parser.parse("Hello   there")

    assert result.kind is ParseKind.TEXT
    assert result.literal_text == "hello there"
    assert result.command is None


def test_window_productivity_commands_are_disabled_by_default() -> None:
    parser = CommandParser(registry=create_builtin_registry())

    result = parser.parse("maximize window command")

    assert result.kind is ParseKind.TEXT
    assert result.literal_text == "maximize window command"
    assert result.command is None


def test_window_productivity_commands_can_be_enabled_explicitly() -> None:
    registry = create_builtin_registry(enabled_features={FeatureGate.WINDOW_COMMANDS})
    parser = CommandParser(registry=registry)

    result = parser.parse("maximize window command")

    assert result.kind is ParseKind.COMMAND
    assert result.command is not None
    assert result.command.command_id == "maximize_window"


def test_special_phrase_match_is_exact_not_prefix() -> None:
    parser = CommandParser(registry=create_builtin_registry())

    result = parser.parse("pause voice key command")

    assert result.kind is ParseKind.TEXT
    assert result.literal_text == "pause voice key command"
    assert result.command is None


def test_resume_special_phrase_match_is_exact_not_command_suffix_variant() -> None:
    parser = CommandParser(registry=create_builtin_registry())

    result = parser.parse("resume voice key command")

    assert result.kind is ParseKind.TEXT
    assert result.literal_text == "resume voice key command"
    assert result.command is None
