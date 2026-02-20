"""Privacy-by-default regression tests for E09-S01.

This module ensures that data minimization controls are enforced by default,
preventing accidental logging or persistence of sensitive user data.

Requirements: Section 5.4 privacy, requirements/security.md section 2
Story: E09-S01 - Data minimization controls
"""

from voicekey.audio.threshold import ConfidenceFilter
from voicekey.config.schema import PrivacyConfig, VoiceKeyConfig


class TestPrivacyDefaults:
    """Test suite for privacy-by-default enforcement."""

    def test_privacy_config_default_values(self) -> None:
        """Verify PrivacyConfig has privacy-protective defaults."""
        config = PrivacyConfig()

        assert config.telemetry_enabled is False, "Telemetry must be off by default"
        assert config.transcript_logging is False, "Transcript logging must be off by default"
        assert config.redact_debug_text is True, "Debug text redaction must be on by default"
        assert config.persist_audio is False, "Audio persistence must be off by default"

    def test_main_config_has_privacy_defaults(self) -> None:
        """Verify VoiceKeyConfig includes privacy-protective defaults."""
        config = VoiceKeyConfig()

        assert config.privacy.telemetry_enabled is False
        assert config.privacy.transcript_logging is False
        assert config.privacy.redact_debug_text is True
        assert config.privacy.persist_audio is False

    def test_confidence_filter_default_does_not_log_transcripts(self) -> None:
        """Verify ConfidenceFilter defaults to NOT logging transcript text."""
        filter_obj = ConfidenceFilter()
        assert filter_obj._log_dropped is False, (
            "ConfidenceFilter must default to log_dropped=False for privacy"
        )

    def test_config_serialization_includes_privacy_settings(self) -> None:
        """Verify serialized config includes privacy settings."""
        from voicekey.config.schema import serialize_config

        config = VoiceKeyConfig()
        yaml_str = serialize_config(config)

        # Verify privacy section is present
        assert "privacy:" in yaml_str
        assert "telemetry_enabled: false" in yaml_str
        assert "transcript_logging: false" in yaml_str
        assert "redact_debug_text: true" in yaml_str
        assert "persist_audio: false" in yaml_str

    def test_config_validation_preserves_privacy_defaults(self) -> None:
        """Verify config validation doesn't override privacy defaults."""
        from voicekey.config.schema import validate_with_fallback

        # Empty config should use safe defaults
        validated, warnings = validate_with_fallback({})

        assert validated.privacy.telemetry_enabled is False
        assert validated.privacy.transcript_logging is False
        assert validated.privacy.redact_debug_text is True
        assert validated.privacy.persist_audio is False
        assert len(warnings) == 0, "Empty config should not generate warnings"
