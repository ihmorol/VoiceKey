"""Unit tests for command parser core contract (E02-S02)."""

from __future__ import annotations

from voicekey.commands.builtins import create_builtin_registry
from voicekey.commands.parser import CommandParser, ParseKind, create_parser
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


def test_create_parser_disables_window_commands_by_default() -> None:
    parser = create_parser()

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


def test_create_parser_routes_window_commands_when_enabled() -> None:
    parser = create_parser(window_commands_enabled=True)

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


def test_text_expansion_snippets_are_disabled_by_default() -> None:
    parser = create_parser(snippets={"ty": "thank you"})

    result = parser.parse("ty")

    assert result.kind is ParseKind.TEXT
    assert result.literal_text == "ty"
    assert result.command is None


def test_text_expansion_snippets_can_be_enabled_explicitly() -> None:
    parser = create_parser(text_expansion_enabled=True, snippets={"ty": "thank you"})

    result = parser.parse("ty")

    assert result.kind is ParseKind.TEXT
    assert result.literal_text == "thank you"
    assert result.command is None


def test_unknown_command_literal_fallback_is_preserved_when_text_expansion_enabled() -> None:
    parser = create_parser(text_expansion_enabled=True, snippets={"ty": "thank you"})

    result = parser.parse("hello world command")

    assert result.kind is ParseKind.TEXT
    assert result.literal_text == "hello world command"
    assert result.command is None


class TestUnicodeNormalization:
    """Tests for Unicode normalization in phrase matching."""

    def test_normalize_phrase_handles_composed_unicode(self) -> None:
        """Test that normalize_phrase handles composed unicode characters."""
        from voicekey.commands.registry import normalize_phrase

        # é as a single composed character (NFC)
        composed = "café"
        # é as decomposed (NFD): e + combining acute accent
        decomposed = "cafe\u0301"

        assert normalize_phrase(composed) == normalize_phrase(decomposed)
        assert normalize_phrase(composed) == "café"

    def test_normalize_phrase_handles_various_accented_characters(self) -> None:
        """Test normalization of various accented characters."""
        from voicekey.commands.registry import normalize_phrase

        # German umlauts
        assert normalize_phrase("über") == normalize_phrase("u\u0308ber")
        # Spanish ñ
        assert normalize_phrase("señor") == normalize_phrase("sen\u0303or")
        # French é (e with acute accent)
        assert normalize_phrase("café") == normalize_phrase("cafe\u0301")

    def test_parser_matches_commands_with_decomposed_unicode(self) -> None:
        """Test that parser matches commands regardless of unicode composition."""
        from voicekey.commands.registry import CommandDefinition, CommandRegistry, normalize_phrase

        # Register a command with composed unicode
        registry = CommandRegistry()
        registry.register(
            CommandDefinition(
                command_id="test_cafe",
                phrase="café",
            )
        )

        # Match with decomposed unicode should work
        decomposed_query = "cafe\u0301"
        result = registry.match(decomposed_query)
        assert result is not None
        assert result.command_id == "test_cafe"

    def test_parser_matches_builtins_with_unicode_input(self) -> None:
        """Test that parser handles unicode in user input."""
        parser = CommandParser(registry=create_builtin_registry())

        # Unicode whitespace should be normalized
        result = parser.parse("new\u00a0line command")  # non-breaking space

        # Should match the command despite unicode whitespace
        assert result.kind is ParseKind.COMMAND
        assert result.command is not None
        assert result.command.command_id == "new_line"

    def test_normalize_phrase_preserves_case_insensitivity(self) -> None:
        """Test that normalization still applies case insensitivity."""
        from voicekey.commands.registry import normalize_phrase

        assert normalize_phrase("CAFÉ") == normalize_phrase("café")
        assert normalize_phrase("CAFÉ") == "café"

    def test_normalize_phrase_handles_emoji(self) -> None:
        """Test that emoji are handled without errors."""
        from voicekey.commands.registry import normalize_phrase

        # Emoji should pass through (they're already in NFC form typically)
        result = normalize_phrase("hello 👋 world")
        assert "👋" in result
        assert result == "hello 👋 world"

    def test_special_phrase_with_unicode_normalization(self) -> None:
        """Test special phrases work with unicode input."""
        parser = CommandParser(registry=create_builtin_registry())

        # Test with decomposed unicode characters
        result = parser.parse("pause voice key")

        assert result.kind is ParseKind.SYSTEM
        assert result.command is not None
        assert result.command.command_id == "pause_voice_key"
