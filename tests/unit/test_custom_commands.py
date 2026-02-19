"""Unit tests for config-defined custom command loading and validation."""

from __future__ import annotations

import pytest

from voicekey.commands.custom import CustomActionType, load_custom_command_actions


def test_load_custom_commands_supports_key_combo_and_text_actions() -> None:
    actions = load_custom_command_actions(
        {
            "save_file": {
                "phrase": "save command",
                "action": "key_combo",
                "keys": ["ctrl", "s"],
                "description": "Save current file",
            },
            "signature": {
                "phrase": "signature command",
                "action": "text",
                "text": "Best regards,",
            },
        }
    )

    assert len(actions) == 2
    save_action = actions[0]
    signature_action = actions[1]

    assert save_action.command_id == "custom_save_file"
    assert save_action.phrase == "save"
    assert save_action.action_type is CustomActionType.KEY_COMBO
    assert save_action.keys == ("ctrl", "s")

    assert signature_action.command_id == "custom_signature"
    assert signature_action.phrase == "signature"
    assert signature_action.action_type is CustomActionType.TEXT
    assert signature_action.text == "Best regards,"


def test_custom_command_loader_rejects_unknown_action_type() -> None:
    with pytest.raises(ValueError):
        load_custom_command_actions(
            {
                "save_file": {
                    "phrase": "save command",
                    "action": "macro",
                }
            }
        )


def test_custom_command_loader_rejects_missing_key_combo_keys() -> None:
    with pytest.raises(ValueError):
        load_custom_command_actions(
            {
                "save_file": {
                    "phrase": "save command",
                    "action": "key_combo",
                }
            }
        )


def test_custom_command_loader_rejects_phrase_collisions() -> None:
    with pytest.raises(ValueError):
        load_custom_command_actions(
            {
                "first": {"phrase": "save command", "action": "text", "text": "a"},
                "second": {"phrase": "save command", "action": "text", "text": "b"},
            }
        )
