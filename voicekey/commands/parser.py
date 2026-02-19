"""Deterministic command parser contract."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from voicekey.commands.builtins import SPECIAL_PHRASES, create_builtin_registry
from voicekey.commands.registry import (
    CommandChannel,
    CommandDefinition,
    CommandRegistry,
    normalize_phrase,
)

COMMAND_SUFFIX = "command"


class ParseKind(StrEnum):
    """Parser output kind."""

    TEXT = "text"
    COMMAND = "command"
    SYSTEM = "system"


@dataclass(frozen=True)
class ParseResult:
    """Deterministic parser output schema for transcript routing."""

    kind: ParseKind
    normalized_transcript: str
    literal_text: str | None = None
    command: CommandDefinition | None = None


class CommandParser:
    """Parses transcript text into command/system/text outcomes."""

    def __init__(self, registry: CommandRegistry | None = None) -> None:
        self._registry = registry or create_builtin_registry()

    def parse(self, transcript: str) -> ParseResult:
        """Parse transcript using command suffix and special phrase precedence."""
        normalized = normalize_phrase(transcript)
        if not normalized:
            return ParseResult(kind=ParseKind.TEXT, normalized_transcript="", literal_text="")

        if normalized in SPECIAL_PHRASES:
            special_command = self._registry.match(normalized)
            if special_command is not None:
                return self._to_command_result(special_command, normalized)

        if self._ends_with_command_suffix(normalized):
            candidate = normalized[: -len(COMMAND_SUFFIX)].strip()
            matched = self._registry.match(candidate)
            if matched is not None and matched.channel is CommandChannel.COMMAND:
                return self._to_command_result(matched, normalized)

            return ParseResult(
                kind=ParseKind.TEXT,
                normalized_transcript=normalized,
                literal_text=normalized,
            )

        return ParseResult(
            kind=ParseKind.TEXT,
            normalized_transcript=normalized,
            literal_text=normalized,
        )

    @staticmethod
    def _ends_with_command_suffix(normalized_transcript: str) -> bool:
        return (
            normalized_transcript == COMMAND_SUFFIX
            or normalized_transcript.endswith(f" {COMMAND_SUFFIX}")
        )

    @staticmethod
    def _to_command_result(command: CommandDefinition, normalized_transcript: str) -> ParseResult:
        kind = ParseKind.SYSTEM if command.channel is CommandChannel.SYSTEM else ParseKind.COMMAND
        return ParseResult(
            kind=kind,
            normalized_transcript=normalized_transcript,
            command=command,
            literal_text=None,
        )
