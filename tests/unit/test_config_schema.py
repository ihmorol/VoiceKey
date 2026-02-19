"""Unit tests for configuration schema validation and fallback behavior."""

from __future__ import annotations

from voicekey.config.schema import CONFIG_VERSION, default_config, validate_with_fallback


def test_default_config_matches_expected_baseline() -> None:
    config = default_config()

    assert config.version == CONFIG_VERSION
    assert config.engine.model_profile == "base"
    assert config.audio.sample_rate_hz == 16000
    assert config.wake_word.phrase == "voice key"
    assert config.modes.inactivity_auto_pause_seconds == 30
    assert config.features.window_commands_enabled is False
    assert config.features.text_expansion_enabled is False


def test_validate_with_fallback_replaces_invalid_values_and_keeps_valid_values() -> None:
    config, warnings = validate_with_fallback(
        {
            "audio": {"sample_rate_hz": 12345},
            "typing": {"confidence_threshold": 1.2},
            "modes": {"inactivity_auto_pause_seconds": 20},
        }
    )

    assert config.audio.sample_rate_hz == 16000
    assert config.typing.confidence_threshold == 0.5
    assert config.modes.inactivity_auto_pause_seconds == 20
    assert any("audio.sample_rate_hz" in warning for warning in warnings)
    assert any("typing.confidence_threshold" in warning for warning in warnings)


def test_validate_with_fallback_removes_unknown_keys() -> None:
    config, warnings = validate_with_fallback(
        {
            "engine": {"model_profile": "tiny", "unknown_option": True},
            "unknown_top_level": {"foo": "bar"},
        }
    )

    assert config.engine.model_profile == "tiny"
    assert any("engine.unknown_option" in warning for warning in warnings)
    assert any("unknown_top_level" in warning for warning in warnings)
