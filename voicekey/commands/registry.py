"""Command registry and lookup primitives."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum


def normalize_phrase(text: str) -> str:
    """Normalize phrase text deterministically for parser/registry matching."""
    return " ".join(text.strip().lower().split())


class CommandChannel(StrEnum):
    """Execution channel classification for parser results."""

    COMMAND = "command"
    SYSTEM = "system"


class FeatureGate(StrEnum):
    """Feature gates that can control command availability."""

    WINDOW_COMMANDS = "window_commands"
    TEXT_EXPANSION = "text_expansion"


@dataclass(frozen=True)
class CommandDefinition:
    """Registry entry for a parseable command phrase."""

    command_id: str
    phrase: str
    channel: CommandChannel = CommandChannel.COMMAND
    aliases: tuple[str, ...] = ()
    feature_gate: FeatureGate | None = None


class CommandRegistry:
    """Case-insensitive phrase/alias lookup for command parsing."""

    def __init__(
        self,
        commands: Iterable[CommandDefinition] | None = None,
        enabled_features: Iterable[FeatureGate] | None = None,
    ) -> None:
        self._phrase_map: dict[str, CommandDefinition] = {}
        self._enabled_features = set(enabled_features or ())

        if commands is not None:
            for command in commands:
                self.register(command)

    def register(self, command: CommandDefinition) -> None:
        """Register a command and all aliases with collision protection."""
        normalized_phrases = [normalize_phrase(command.phrase)]
        normalized_phrases.extend(normalize_phrase(alias) for alias in command.aliases)

        if any(not phrase for phrase in normalized_phrases):
            raise ValueError(f"command {command.command_id!r} has empty phrase/alias")

        collisions = [phrase for phrase in normalized_phrases if phrase in self._phrase_map]
        if collisions:
            raise ValueError(
                f"command phrase collision for {command.command_id!r}: {collisions!r}"
            )

        for phrase in normalized_phrases:
            self._phrase_map[phrase] = command

    def match(self, phrase: str) -> CommandDefinition | None:
        """Return command for phrase/alias when enabled by feature gates."""
        normalized = normalize_phrase(phrase)
        if not normalized:
            return None

        command = self._phrase_map.get(normalized)
        if command is None:
            return None

        if not self._is_enabled(command):
            return None

        return command

    def set_enabled_features(self, features: Iterable[FeatureGate]) -> None:
        """Replace active feature gates used for lookup availability."""
        self._enabled_features = set(features)

    def phrase_map(self) -> Mapping[str, CommandDefinition]:
        """Return read-only phrase mapping for diagnostics/tests."""
        return self._phrase_map

    def _is_enabled(self, command: CommandDefinition) -> bool:
        return command.feature_gate is None or command.feature_gate in self._enabled_features
