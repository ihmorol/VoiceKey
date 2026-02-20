"""Unit tests for telemetry migration safety.

These tests verify that telemetry remains disabled by default and cannot be
enabled implicitly by upgrade/migration, as per:
- architecture.md section 12
- requirements/security.md section 2
- requirements/configuration.md privacy defaults
"""

from __future__ import annotations

from copy import deepcopy

import pytest

from voicekey.config.migration import (
    ConfigMigrationError,
    MigrationRegistry,
    MigrationResult,
    build_default_registry,
    migrate_payload,
)
from voicekey.config.schema import (
    CONFIG_VERSION,
    VoiceKeyConfig,
    default_config,
    validate_with_fallback,
)
from voicekey.security.privacy_assertions import (
    PrivacyAssertionResult,
    assert_offline_runtime,
    verify_migration_telemetry_safety,
    verify_privacy_defaults,
)


class TestTelemetryDefaultsInSchema:
    """Tests for telemetry default values in config schema."""

    def test_default_config_has_telemetry_disabled(self) -> None:
        """Default config should have telemetry disabled."""
        config = default_config()
        assert config.privacy.telemetry_enabled is False

    def test_default_config_has_transcript_logging_disabled(self) -> None:
        """Default config should have transcript logging disabled."""
        config = default_config()
        assert config.privacy.transcript_logging is False

    def test_default_config_has_redaction_enabled(self) -> None:
        """Default config should have debug text redaction enabled."""
        config = default_config()
        assert config.privacy.redact_debug_text is True

    def test_serialized_default_config_has_telemetry_false(self) -> None:
        """Serialized default config should show telemetry as false."""
        import yaml

        from voicekey.config.schema import serialize_config

        config = default_config()
        serialized = serialize_config(config)
        parsed = yaml.safe_load(serialized)

        assert parsed["privacy"]["telemetry_enabled"] is False


class TestPrivacyVerification:
    """Tests for privacy verification functions."""

    def test_verify_privacy_defaults_passes_default_config(self) -> None:
        """Default config should pass privacy verification."""
        config = default_config()
        result = verify_privacy_defaults(config.model_dump())

        assert result.passed
        assert result.telemetry_disabled
        assert result.transcript_logging_disabled
        assert result.redaction_enabled
        assert len(result.warnings) == 0
        assert len(result.errors) == 0

    def test_verify_privacy_defaults_fails_with_telemetry_enabled(self) -> None:
        """Config with telemetry enabled should fail verification."""
        config_data = default_config().model_dump()
        config_data["privacy"]["telemetry_enabled"] = True

        result = verify_privacy_defaults(config_data)

        assert not result.passed
        assert not result.telemetry_disabled
        assert len(result.warnings) >= 1
        assert any("telemetry" in w.lower() for w in result.warnings)

    def test_verify_privacy_defaults_warns_on_transcript_logging(self) -> None:
        """Config with transcript logging should produce warning."""
        config_data = default_config().model_dump()
        config_data["privacy"]["transcript_logging"] = True

        result = verify_privacy_defaults(config_data)

        assert not result.passed
        assert not result.transcript_logging_disabled
        assert any("transcript" in w.lower() for w in result.warnings)

    def test_verify_privacy_defaults_warns_on_redaction_disabled(self) -> None:
        """Config with redaction disabled should produce warning."""
        config_data = default_config().model_dump()
        config_data["privacy"]["redact_debug_text"] = False

        result = verify_privacy_defaults(config_data)

        assert not result.passed
        assert not result.redaction_enabled
        assert any("redact" in w.lower() for w in result.warnings)


class TestOfflineRuntimeAssertion:
    """Tests for offline runtime assertion."""

    def test_assert_offline_runtime_passes_default_config(self) -> None:
        """Default config should pass offline runtime assertion."""
        config_data = default_config().model_dump()
        # Should not raise
        assert_offline_runtime(config_data)

    def test_assert_offline_runtime_fails_with_telemetry(self) -> None:
        """Config with telemetry should fail offline runtime assertion."""
        config_data = default_config().model_dump()
        config_data["privacy"]["telemetry_enabled"] = True

        with pytest.raises(RuntimeError, match="telemetry"):
            assert_offline_runtime(config_data)


class TestMigrationTelemetrySafety:
    """Tests for migration telemetry safety verification."""

    def test_migration_safety_new_install(self) -> None:
        """New installation should have telemetry disabled."""
        new_config = default_config().model_dump()
        assert verify_migration_telemetry_safety(None, new_config)

    def test_migration_safety_preserves_disabled_state(self) -> None:
        """Migration should preserve disabled telemetry state."""
        old_config = {"privacy": {"telemetry_enabled": False}}
        new_config = {"privacy": {"telemetry_enabled": False}}

        assert verify_migration_telemetry_safety(old_config, new_config)

    def test_migration_safety_preserves_enabled_state(self) -> None:
        """Migration should preserve explicitly enabled telemetry state."""
        old_config = {"privacy": {"telemetry_enabled": True}}
        new_config = {"privacy": {"telemetry_enabled": True}}

        assert verify_migration_telemetry_safety(old_config, new_config)

    def test_migration_safety_detects_implicit_enable(self) -> None:
        """Migration safety should detect implicitly enabled telemetry."""
        old_config = {"privacy": {"telemetry_enabled": False}}
        new_config = {"privacy": {"telemetry_enabled": True}}  # Implicitly enabled!

        assert not verify_migration_telemetry_safety(old_config, new_config)

    def test_migration_safety_handles_missing_privacy_section(self) -> None:
        """Migration safety should handle missing privacy section."""
        old_config: dict = {}
        new_config = {"privacy": {"telemetry_enabled": False}}

        assert verify_migration_telemetry_safety(old_config, new_config)

    def test_migration_safety_detects_implicit_enable_from_missing(self) -> None:
        """Migration should not enable telemetry if it wasn't explicitly set."""
        old_config: dict = {}  # No privacy section, implies disabled
        new_config = {"privacy": {"telemetry_enabled": True}}  # But now enabled

        assert not verify_migration_telemetry_safety(old_config, new_config)


class TestConfigMigrationPreservesTelemetry:
    """Tests that config migration preserves telemetry disabled state."""

    def test_v1_to_current_preserves_telemetry_disabled(self) -> None:
        """Migration from v1 should preserve telemetry disabled."""
        v1_config = {
            "version": 1,
            "privacy": {"telemetry_enabled": False},
        }

        result = migrate_payload(v1_config)
        assert result.payload["privacy"]["telemetry_enabled"] is False

    def test_v2_to_current_preserves_telemetry_disabled(self) -> None:
        """Migration from v2 should preserve telemetry disabled."""
        v2_config = {
            "version": 2,
            "privacy": {"telemetry_enabled": False},
        }

        result = migrate_payload(v2_config)
        assert result.payload["privacy"]["telemetry_enabled"] is False

    def test_migration_does_not_enable_telemetry(self) -> None:
        """Migration should never enable telemetry implicitly."""
        # Config without privacy section
        v1_config = {"version": 1}

        result = migrate_payload(v1_config)

        # After migration, telemetry should still be disabled
        # (either preserved from old config or set to default False)
        privacy = result.payload.get("privacy", {})
        telemetry = privacy.get("telemetry_enabled", False)

        assert telemetry is False, "Migration should not enable telemetry"

    def test_migration_to_current_version_has_telemetry_disabled(self) -> None:
        """Migrated config should have telemetry disabled."""
        registry = build_default_registry()

        # Start with minimal v1 config
        v1_config = {"version": 1}
        result = registry.migrate(v1_config)

        # Validate the migrated config
        validated, _ = validate_with_fallback(result.payload)
        assert validated.privacy.telemetry_enabled is False

    def test_migration_with_explicit_telemetry_disabled_stays_disabled(self) -> None:
        """Explicitly disabled telemetry should stay disabled after migration."""
        v1_config = {
            "version": 1,
            "privacy": {
                "telemetry_enabled": False,
                "transcript_logging": False,
                "redact_debug_text": True,
            },
        }

        result = migrate_payload(v1_config)

        assert result.payload["privacy"]["telemetry_enabled"] is False
        assert result.payload["privacy"]["transcript_logging"] is False
        assert result.payload["privacy"]["redact_debug_text"] is True


class TestMigrationRegistryTelemetrySafety:
    """Tests for migration registry telemetry safety guarantees."""

    def test_custom_migration_cannot_enable_telemetry(self) -> None:
        """Custom migration handlers should not be able to enable telemetry."""
        registry = MigrationRegistry(target_version=CONFIG_VERSION + 1)

        # Register all existing migrations
        registry.register(1, lambda p: {**p, "version": 2})
        registry.register(2, lambda p: {**p, "version": 3})

        # Try to register a malicious migration that enables telemetry
        def malicious_migration(payload: dict) -> dict:
            result = deepcopy(payload)
            if "privacy" not in result:
                result["privacy"] = {}
            result["privacy"]["telemetry_enabled"] = True  # Malicious!
            result["version"] = CONFIG_VERSION + 1
            return result

        registry.register(3, malicious_migration)

        v1_config = {"version": 1, "privacy": {"telemetry_enabled": False}}
        result = registry.migrate(v1_config)

        # Verify migration safety catches this
        assert not verify_migration_telemetry_safety(
            v1_config,
            result.payload
        )


class TestTelemetryExplicitOptIn:
    """Tests for telemetry explicit opt-in requirements."""

    def test_telemetry_requires_explicit_enable(self) -> None:
        """Telemetry should require explicit user action to enable."""
        # User explicitly enables telemetry
        config_data = default_config().model_dump()
        config_data["privacy"]["telemetry_enabled"] = True

        # This should be detected as user opt-in
        result = verify_privacy_defaults(config_data)
        assert not result.telemetry_disabled
        assert any("opt-in" in w.lower() or "explicit" in w.lower() for w in result.warnings)

    def test_telemetry_cannot_be_enabled_by_validation_fallback(self) -> None:
        """Validation fallback should not enable telemetry."""
        # Config with invalid telemetry value
        raw_data = {
            "privacy": {
                "telemetry_enabled": "invalid",  # Invalid type
            }
        }

        # Validation should fallback to default (disabled)
        validated, warnings = validate_with_fallback(raw_data)

        assert validated.privacy.telemetry_enabled is False
        assert any("privacy" in w.lower() or "telemetry" in w.lower() for w in warnings)

    def test_missing_privacy_section_defaults_to_disabled(self) -> None:
        """Missing privacy section should default to telemetry disabled."""
        raw_data: dict = {}

        validated, _ = validate_with_fallback(raw_data)

        assert validated.privacy.telemetry_enabled is False


class TestPrivacyConfigImmutabilityDuringMigration:
    """Tests that privacy config is not accidentally modified during migration."""

    def test_migration_preserves_all_privacy_settings(self) -> None:
        """Migration should preserve all privacy settings exactly."""
        original_privacy = {
            "telemetry_enabled": False,
            "transcript_logging": False,
            "redact_debug_text": True,
        }

        v1_config = {
            "version": 1,
            "privacy": original_privacy.copy(),
        }

        result = migrate_payload(v1_config)

        # Privacy settings should be preserved
        assert result.payload["privacy"] == original_privacy

    def test_migration_does_not_add_new_privacy_keys(self) -> None:
        """Migration should not add unexpected keys to privacy section."""
        v1_config = {
            "version": 1,
            "privacy": {
                "telemetry_enabled": False,
                "transcript_logging": False,
                "redact_debug_text": True,
            },
        }

        result = migrate_payload(v1_config)

        # Privacy should only have the expected keys
        expected_keys = {"telemetry_enabled", "transcript_logging", "redact_debug_text"}
        assert set(result.payload["privacy"].keys()) == expected_keys
