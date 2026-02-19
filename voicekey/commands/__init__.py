"""Command parsing and registry."""

from voicekey.commands.builtins import create_builtin_registry
from voicekey.commands.parser import CommandParser, ParseKind, ParseResult
from voicekey.commands.registry import (
    CommandChannel,
    CommandDefinition,
    CommandRegistry,
    FeatureGate,
    normalize_phrase,
)

__all__ = [
    "CommandChannel",
    "CommandDefinition",
    "CommandParser",
    "CommandRegistry",
    "FeatureGate",
    "ParseKind",
    "ParseResult",
    "create_builtin_registry",
    "normalize_phrase",
]
