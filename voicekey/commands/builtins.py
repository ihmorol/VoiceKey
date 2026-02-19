"""Built-in command catalog for parser and registry wiring."""

from __future__ import annotations

from collections.abc import Iterable

from voicekey.commands.registry import (
    CommandChannel,
    CommandDefinition,
    CommandRegistry,
    FeatureGate,
    normalize_phrase,
)

SPECIAL_PHRASE_COMMANDS: tuple[CommandDefinition, ...] = (
    CommandDefinition(
        command_id="pause_voice_key",
        phrase="pause voice key",
        channel=CommandChannel.SYSTEM,
    ),
    CommandDefinition(
        command_id="resume_voice_key",
        phrase="resume voice key",
        channel=CommandChannel.SYSTEM,
    ),
    CommandDefinition(
        command_id="voice_key_stop",
        phrase="voice key stop",
        channel=CommandChannel.SYSTEM,
    ),
)

CORE_COMMANDS: tuple[CommandDefinition, ...] = (
    CommandDefinition(command_id="new_line", phrase="new line", aliases=("enter",)),
    CommandDefinition(command_id="tab", phrase="tab"),
    CommandDefinition(command_id="space", phrase="space"),
    CommandDefinition(command_id="backspace", phrase="backspace"),
    CommandDefinition(command_id="delete", phrase="delete"),
    CommandDefinition(command_id="left", phrase="left"),
    CommandDefinition(command_id="right", phrase="right"),
    CommandDefinition(command_id="up", phrase="up"),
    CommandDefinition(command_id="down", phrase="down"),
    CommandDefinition(command_id="escape", phrase="escape"),
    CommandDefinition(command_id="control_c", phrase="control c"),
    CommandDefinition(command_id="control_v", phrase="control v"),
    CommandDefinition(command_id="control_x", phrase="control x"),
    CommandDefinition(command_id="control_z", phrase="control z"),
    CommandDefinition(command_id="control_a", phrase="control a"),
    CommandDefinition(command_id="control_l", phrase="control l"),
    CommandDefinition(command_id="scratch_that", phrase="scratch that"),
    CommandDefinition(command_id="capital_hello", phrase="capital hello"),
    CommandDefinition(command_id="all_caps_hello", phrase="all caps hello"),
)

WINDOW_PRODUCTIVITY_COMMANDS: tuple[CommandDefinition, ...] = (
    CommandDefinition(
        command_id="maximize_window",
        phrase="maximize window",
        feature_gate=FeatureGate.WINDOW_COMMANDS,
    ),
    CommandDefinition(
        command_id="minimize_window",
        phrase="minimize window",
        feature_gate=FeatureGate.WINDOW_COMMANDS,
    ),
    CommandDefinition(
        command_id="close_window",
        phrase="close window",
        feature_gate=FeatureGate.WINDOW_COMMANDS,
    ),
    CommandDefinition(
        command_id="switch_window",
        phrase="switch window",
        feature_gate=FeatureGate.WINDOW_COMMANDS,
    ),
    CommandDefinition(
        command_id="copy_that",
        phrase="copy that",
        feature_gate=FeatureGate.WINDOW_COMMANDS,
    ),
    CommandDefinition(
        command_id="paste_that",
        phrase="paste that",
        feature_gate=FeatureGate.WINDOW_COMMANDS,
    ),
    CommandDefinition(
        command_id="cut_that",
        phrase="cut that",
        feature_gate=FeatureGate.WINDOW_COMMANDS,
    ),
)

SPECIAL_PHRASES: tuple[str, ...] = tuple(
    normalize_phrase(command.phrase) for command in SPECIAL_PHRASE_COMMANDS
)


def builtin_commands() -> tuple[CommandDefinition, ...]:
    """Return deterministic built-in command set for parser contract."""
    return SPECIAL_PHRASE_COMMANDS + CORE_COMMANDS + WINDOW_PRODUCTIVITY_COMMANDS


def create_builtin_registry(
    enabled_features: Iterable[FeatureGate] | None = None,
    custom_commands: Iterable[CommandDefinition] | None = None,
) -> CommandRegistry:
    """Create registry with built-ins and optional feature gates enabled."""
    registry = CommandRegistry(commands=builtin_commands(), enabled_features=enabled_features)
    for command in custom_commands or ():
        registry.register(command)
    return registry
