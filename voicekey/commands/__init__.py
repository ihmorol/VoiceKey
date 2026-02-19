"""Command parsing and registry."""

from voicekey.commands.builtins import create_builtin_registry
from voicekey.commands.fuzzy import FuzzyMatchConfig, FuzzyMatcher
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
    "FuzzyMatchConfig",
    "FuzzyMatcher",
    "ParseKind",
    "ParseResult",
    "create_builtin_registry",
    "normalize_phrase",
]
