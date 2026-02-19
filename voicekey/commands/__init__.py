"""Command parsing and registry."""

from voicekey.commands.builtins import create_builtin_registry
from voicekey.commands.custom import CustomActionType, CustomCommandAction, load_custom_command_actions
from voicekey.commands.fuzzy import FuzzyMatchConfig, FuzzyMatcher
from voicekey.commands.snippets import SnippetExpander
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
    "CustomActionType",
    "CustomCommandAction",
    "FeatureGate",
    "FuzzyMatchConfig",
    "FuzzyMatcher",
    "ParseKind",
    "ParseResult",
    "SnippetExpander",
    "create_builtin_registry",
    "load_custom_command_actions",
    "normalize_phrase",
]
