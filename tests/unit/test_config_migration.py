"""Unit tests for config migration registry behavior (E06-S02)."""

from __future__ import annotations

import pytest

from voicekey.config.migration import (
    ConfigMigrationError,
    MigrationRegistry,
    build_default_registry,
    migrate_payload,
)


def test_default_registry_migrates_v1_payload_to_current_version() -> None:
    legacy_payload = {
        "version": 1,
        "engine": {"model_profile": "base"},
    }

    result = migrate_payload(legacy_payload)

    assert result.from_version == 1
    assert result.to_version == 3
    assert result.migrated is True
    assert result.payload["version"] == 3
    assert result.warnings == (
        "Applied config migration 1->2.",
        "Applied config migration 2->3.",
    )


def test_migration_is_idempotent_for_current_version_payload() -> None:
    current_payload = {"version": 3, "typing": {"char_delay_ms": 8}}

    first = migrate_payload(current_payload)
    second = migrate_payload(first.payload)

    assert first.migrated is False
    assert second.migrated is False
    assert second.payload == first.payload
    assert second.warnings == ()


def test_missing_version_assumes_legacy_v1_and_migrates() -> None:
    result = migrate_payload({"typing": {"confidence_threshold": 0.5}})

    assert result.from_version == 1
    assert result.payload["version"] == 3
    assert result.warnings[0] == "Missing config version; assuming version 1 for migration."


def test_registry_rejects_duplicate_source_version_registration() -> None:
    registry = MigrationRegistry(target_version=3)
    registry.register(1, lambda payload: {**payload, "version": 2})

    with pytest.raises(ValueError):
        registry.register(1, lambda payload: {**payload, "version": 2})


def test_migration_rejects_newer_config_version_than_supported() -> None:
    registry = build_default_registry()

    with pytest.raises(ConfigMigrationError):
        registry.migrate({"version": 99})


def test_migration_raises_when_step_missing_for_source_version() -> None:
    registry = MigrationRegistry(target_version=3)
    registry.register(2, lambda payload: {**payload, "version": 3})

    with pytest.raises(ConfigMigrationError):
        registry.migrate({"version": 1})


def test_registry_rejects_target_version_less_than_one() -> None:
    with pytest.raises(ValueError, match="target_version must be >= 1"):
        MigrationRegistry(target_version=0)


def test_registry_rejects_from_version_less_than_one() -> None:
    registry = MigrationRegistry(target_version=3)

    with pytest.raises(ValueError, match="from_version must be >= 1"):
        registry.register(0, lambda payload: {**payload, "version": 2})


def test_registry_rejects_from_version_at_or_above_target() -> None:
    registry = MigrationRegistry(target_version=3)

    with pytest.raises(ValueError, match="from_version must be below target_version"):
        registry.register(3, lambda payload: {**payload, "version": 4})

    with pytest.raises(ValueError, match="from_version must be below target_version"):
        registry.register(4, lambda payload: {**payload, "version": 5})


def test_migration_raises_when_handler_returns_non_dict() -> None:
    registry = MigrationRegistry(target_version=2)
    registry.register(1, lambda payload: "not a dict")  # type: ignore[arg-type]

    with pytest.raises(ConfigMigrationError, match="must return a mapping payload"):
        registry.migrate({"version": 1})


def test_migration_raises_when_handler_does_not_set_integer_version() -> None:
    registry = MigrationRegistry(target_version=2)
    registry.register(1, lambda payload: {**payload, "version": "not-an-int"})

    with pytest.raises(ConfigMigrationError, match="did not set integer version"):
        registry.migrate({"version": 1})


def test_migration_raises_when_handler_does_not_advance_version() -> None:
    registry = MigrationRegistry(target_version=3)
    registry.register(1, lambda payload: {**payload, "version": 1})  # Doesn't advance

    with pytest.raises(ConfigMigrationError, match="did not advance config version"):
        registry.migrate({"version": 1})


def test_migration_raises_when_handler_advances_past_target() -> None:
    registry = MigrationRegistry(target_version=2)
    registry.register(1, lambda payload: {**payload, "version": 5})  # Skips past target

    with pytest.raises(ConfigMigrationError, match="advanced past supported target version"):
        registry.migrate({"version": 1})


def test_migration_raises_for_non_integer_version_in_payload() -> None:
    registry = build_default_registry()

    with pytest.raises(ConfigMigrationError, match="config version must be an integer"):
        registry.migrate({"version": "1"})  # String instead of int


def test_migration_raises_for_boolean_version_in_payload() -> None:
    registry = build_default_registry()

    with pytest.raises(ConfigMigrationError, match="config version must be an integer"):
        registry.migrate({"version": True})  # Boolean (subclass of int but rejected)


def test_migration_raises_for_negative_source_version() -> None:
    registry = build_default_registry()

    with pytest.raises(ConfigMigrationError, match="config version must be >= 1"):
        registry.migrate({"version": -1})
