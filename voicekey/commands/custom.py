"""Custom command loader and validator for config-defined commands."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from voicekey.commands.registry import CommandDefinition, normalize_phrase

COMMAND_SUFFIX = "command"


class CustomActionType(StrEnum):
    """Supported custom command action types."""

    KEY_COMBO = "key_combo"
    TEXT = "text"


@dataclass(frozen=True)
class CustomCommandAction:
    """Validated action contract for a custom command definition."""

    command_id: str
    phrase: str
    action_type: CustomActionType
    keys: tuple[str, ...] | None = None
    text: str | None = None
    description: str | None = None

    def to_command_definition(self) -> CommandDefinition:
        return CommandDefinition(command_id=self.command_id, phrase=self.phrase)


def load_custom_command_actions(raw_commands: Mapping[str, Any] | None) -> tuple[CustomCommandAction, ...]:
    """Load and validate custom commands from configuration payload."""
    if raw_commands is None:
        return ()
    if not isinstance(raw_commands, Mapping):
        raise ValueError("custom_commands must be a mapping of command_id to command config")

    actions: list[CustomCommandAction] = []
    for raw_command_id, raw_item in raw_commands.items():
        command_id = _normalize_command_id(raw_command_id)
        if not isinstance(raw_item, Mapping):
            raise ValueError(f"custom command '{command_id}' must be a mapping")

        phrase = _normalize_custom_phrase(command_id, raw_item.get("phrase"))
        action_type = _normalize_action_type(command_id, raw_item.get("action"))
        description = _normalize_optional_string(raw_item.get("description"))

        if action_type is CustomActionType.KEY_COMBO:
            keys = _normalize_keys(command_id, raw_item.get("keys"))
            actions.append(
                CustomCommandAction(
                    command_id=command_id,
                    phrase=phrase,
                    action_type=action_type,
                    keys=keys,
                    description=description,
                )
            )
            continue

        text = _normalize_text(command_id, raw_item.get("text"))
        actions.append(
            CustomCommandAction(
                command_id=command_id,
                phrase=phrase,
                action_type=action_type,
                text=text,
                description=description,
            )
        )

    _ensure_unique_phrases(actions)
    return tuple(actions)


def _normalize_command_id(raw_command_id: object) -> str:
    if not isinstance(raw_command_id, str):
        raise ValueError("custom command id must be a string")
    normalized = normalize_phrase(raw_command_id).replace(" ", "_")
    if not normalized:
        raise ValueError("custom command id cannot be empty")
    return f"custom_{normalized}"


def _normalize_custom_phrase(command_id: str, raw_phrase: object) -> str:
    if not isinstance(raw_phrase, str):
        raise ValueError(f"custom command '{command_id}' requires string phrase")

    normalized_phrase = normalize_phrase(raw_phrase)
    if not normalized_phrase:
        raise ValueError(f"custom command '{command_id}' phrase cannot be empty")

    if normalized_phrase == COMMAND_SUFFIX:
        raise ValueError(f"custom command '{command_id}' phrase cannot be only '{COMMAND_SUFFIX}'")

    if normalized_phrase.endswith(f" {COMMAND_SUFFIX}"):
        normalized_phrase = normalized_phrase[: -len(COMMAND_SUFFIX)].strip()

    if not normalized_phrase:
        raise ValueError(f"custom command '{command_id}' phrase cannot be empty")

    return normalized_phrase


def _normalize_action_type(command_id: str, raw_action: object) -> CustomActionType:
    if not isinstance(raw_action, str):
        raise ValueError(f"custom command '{command_id}' requires string action")

    normalized = normalize_phrase(raw_action).replace(" ", "_")
    try:
        return CustomActionType(normalized)
    except ValueError as exc:
        raise ValueError(
            f"custom command '{command_id}' action must be 'key_combo' or 'text'"
        ) from exc


def _normalize_keys(command_id: str, raw_keys: object) -> tuple[str, ...]:
    if not isinstance(raw_keys, list) or not raw_keys:
        raise ValueError(f"custom command '{command_id}' key_combo action requires non-empty keys")

    keys: list[str] = []
    for item in raw_keys:
        if not isinstance(item, str):
            raise ValueError(f"custom command '{command_id}' keys must be strings")
        normalized = normalize_phrase(item)
        if not normalized:
            raise ValueError(f"custom command '{command_id}' keys cannot contain empty values")
        keys.append(normalized)
    return tuple(keys)


def _normalize_text(command_id: str, raw_text: object) -> str:
    if not isinstance(raw_text, str) or not raw_text.strip():
        raise ValueError(f"custom command '{command_id}' text action requires non-empty text")
    return raw_text


def _normalize_optional_string(raw_value: object) -> str | None:
    if raw_value is None:
        return None
    if not isinstance(raw_value, str):
        raise ValueError("custom command description must be a string")
    normalized = raw_value.strip()
    return normalized or None


def _ensure_unique_phrases(actions: list[CustomCommandAction]) -> None:
    seen: dict[str, str] = {}
    for action in actions:
        normalized_phrase = normalize_phrase(action.phrase)
        existing = seen.get(normalized_phrase)
        if existing is not None:
            raise ValueError(
                f"custom command phrase collision between '{existing}' and '{action.command_id}'"
            )
        seen[normalized_phrase] = action.command_id


__all__ = ["CustomActionType", "CustomCommandAction", "load_custom_command_actions"]
