"""Unit tests for parser integration with custom command definitions."""

from __future__ import annotations

import pytest

from voicekey.commands.parser import ParseKind, create_parser


def test_create_parser_with_custom_commands_parses_custom_key_combo_phrase() -> None:
    parser = create_parser(
        custom_commands={
            "save_file": {
                "phrase": "save command",
                "action": "key_combo",
                "keys": ["ctrl", "s"],
            }
        }
    )

    result = parser.parse("save command")

    assert result.kind is ParseKind.COMMAND
    assert result.command is not None
    assert result.command.command_id == "custom_save_file"


def test_create_parser_with_custom_commands_preserves_unknown_literal_fallback() -> None:
    parser = create_parser(
        custom_commands={
            "save_file": {
                "phrase": "save command",
                "action": "key_combo",
                "keys": ["ctrl", "s"],
            }
        }
    )

    result = parser.parse("unmapped command")

    assert result.kind is ParseKind.TEXT
    assert result.command is None
    assert result.literal_text == "unmapped command"


def test_create_parser_rejects_custom_phrase_collision_with_builtins() -> None:
    with pytest.raises(ValueError):
        create_parser(
            custom_commands={
                "duplicate": {
                    "phrase": "new line command",
                    "action": "text",
                    "text": "x",
                }
            }
        )
