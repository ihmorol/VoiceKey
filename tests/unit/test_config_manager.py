"""Unit tests for config path resolution and persistence safeguards."""

from __future__ import annotations

import os
import stat
from pathlib import Path

import yaml

from voicekey.config.migration import MigrationRegistry
import pytest

from voicekey.config.manager import (
    ConfigError,
    backup_config,
    load_config,
    resolve_asr_runtime_policy,
    resolve_config_path,
    save_config,
)
from voicekey.config.schema import default_config


def test_resolve_config_path_uses_explicit_then_env_then_platform_defaults(tmp_path: Path) -> None:
    explicit = tmp_path / "explicit.yaml"
    env_path = tmp_path / "env.yaml"
    env = {"VOICEKEY_CONFIG": str(env_path), "APPDATA": str(tmp_path / "appdata")}
    platform_only_env = {"APPDATA": str(tmp_path / "appdata")}

    assert resolve_config_path(explicit_path=explicit, env=env) == explicit
    assert resolve_config_path(env=env) == env_path
    assert resolve_config_path(env={}, platform_name="linux", home_dir=tmp_path) == (
        tmp_path / ".config" / "voicekey" / "config.yaml"
    )
    assert resolve_config_path(env=platform_only_env, platform_name="windows", home_dir=tmp_path) == (
        Path(env["APPDATA"]) / "voicekey" / "config.yaml"
    )


def test_resolve_config_path_ignores_blank_env_override(tmp_path: Path) -> None:
    env = {"VOICEKEY_CONFIG": "   "}

    resolved = resolve_config_path(env=env, platform_name="linux", home_dir=tmp_path)

    assert resolved == tmp_path / ".config" / "voicekey" / "config.yaml"


def test_load_config_creates_default_file_when_missing(tmp_path: Path) -> None:
    config_path = tmp_path / "voicekey" / "config.yaml"

    result = load_config(explicit_path=config_path)

    assert result.created is True
    assert result.warnings == ()
    assert config_path.exists()
    assert result.config.version == 3


def test_load_config_replaces_invalid_yaml_and_preserves_backup(tmp_path: Path) -> None:
    config_path = tmp_path / "voicekey" / "config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text("version: [", encoding="utf-8")

    result = load_config(explicit_path=config_path)

    assert result.created is False
    assert result.backup_path is not None
    assert result.backup_path.exists()
    assert any("Migration note" in warning for warning in result.warnings)
    persisted = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert persisted["version"] == 3


def test_load_config_sanitizes_invalid_values_and_writes_clean_file(tmp_path: Path) -> None:
    config_path = tmp_path / "voicekey" / "config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        yaml.safe_dump(
            {
                "version": 3,
                "typing": {"confidence_threshold": 2.0},
                "modes": {"inactivity_auto_pause_seconds": 15},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    result = load_config(explicit_path=config_path)

    assert result.created is False
    assert result.backup_path is not None
    assert result.config.typing.confidence_threshold == 0.5
    assert result.config.modes.inactivity_auto_pause_seconds == 15
    assert any("typing.confidence_threshold" in warning for warning in result.warnings)


def test_load_config_migrates_legacy_version_and_rewrites_file(tmp_path: Path) -> None:
    config_path = tmp_path / "voicekey" / "config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "modes": {"inactivity_auto_pause_seconds": 20},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    result = load_config(explicit_path=config_path)

    assert result.created is False
    assert result.backup_path is not None
    assert result.config.version == 3
    assert result.config.modes.inactivity_auto_pause_seconds == 20
    assert any("Applied config migration 1->2." in warning for warning in result.warnings)
    persisted = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert persisted["version"] == 3


def test_load_config_migration_failure_restores_defaults_and_preserves_backup(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "voicekey" / "config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(yaml.safe_dump({"version": 1}, sort_keys=False), encoding="utf-8")

    failing_registry = MigrationRegistry(target_version=3)

    def fail_v1_to_v2(payload: dict[str, object]) -> dict[str, object]:
        raise RuntimeError("boom")

    failing_registry.register(1, fail_v1_to_v2)

    result = load_config(explicit_path=config_path, migration_registry=failing_registry)

    assert result.created is False
    assert result.backup_path is not None
    assert result.config.version == 3
    assert any("Config migration failed:" in warning for warning in result.warnings)
    persisted = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert persisted["version"] == 3


def test_load_config_rejects_unsupported_future_version_with_safe_defaults(tmp_path: Path) -> None:
    config_path = tmp_path / "voicekey" / "config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(yaml.safe_dump({"version": 99}, sort_keys=False), encoding="utf-8")

    result = load_config(explicit_path=config_path)

    assert result.created is False
    assert result.backup_path is not None
    assert result.config.version == 3
    assert any("Config migration failed:" in warning for warning in result.warnings)


def test_save_config_sets_restricted_file_permissions(tmp_path: Path) -> None:
    """Security: Config files must have restrictive permissions (0o600)."""
    from voicekey.config.schema import default_config

    config_path = tmp_path / "secure" / "config.yaml"
    config = default_config()

    save_config(config, config_path)

    assert config_path.exists()

    # On POSIX systems, verify permissions are restricted
    if os.name == "posix":
        mode = config_path.stat().st_mode
        permissions = stat.S_IMODE(mode)
        assert permissions == 0o600, f"Expected 0o600, got {oct(permissions)}"


def test_backup_config_sets_restricted_file_permissions(tmp_path: Path) -> None:
    """Security: Backup files must have restrictive permissions (0o600)."""
    config_path = tmp_path / "original.yaml"
    config_path.write_text("version: 3\n", encoding="utf-8")

    backup_path = backup_config(config_path)

    assert backup_path.exists()

    # On POSIX systems, verify permissions are restricted
    if os.name == "posix":
        mode = backup_path.stat().st_mode
        permissions = stat.S_IMODE(mode)
        assert permissions == 0o600, f"Expected 0o600, got {oct(permissions)}"


def test_load_config_creates_file_with_restricted_permissions(tmp_path: Path) -> None:
    """Security: Newly created config files must have restrictive permissions."""
    config_path = tmp_path / "newconfig" / "config.yaml"

    result = load_config(explicit_path=config_path)

    assert result.created is True
    assert config_path.exists()

    # On POSIX systems, verify permissions are restricted
    if os.name == "posix":
        mode = config_path.stat().st_mode
        permissions = stat.S_IMODE(mode)
        assert permissions == 0o600, f"Expected 0o600, got {oct(permissions)}"


def test_resolve_asr_runtime_policy_defaults_to_local_only_without_cloud_requirements() -> None:
    config = default_config()

    policy = resolve_asr_runtime_policy(config, env={})

    assert policy.mode == "local-only"
    assert policy.requires_cloud_credentials is False


def test_resolve_asr_runtime_policy_downgrades_hybrid_mode_without_api_key() -> None:
    config = default_config()
    config.engine.network_fallback_enabled = True
    config.engine.cloud_api_base = "https://api.openai.com/v1"

    policy = resolve_asr_runtime_policy(config, env={})

    assert policy.mode == "local-only"
    assert policy.requires_cloud_credentials is False
    assert policy.warning is not None
    assert "VOICEKEY_OPENAI_API_KEY" in policy.warning
    assert "engine.network_fallback_enabled=true" in policy.warning


def test_resolve_asr_runtime_policy_rejects_cloud_primary_without_api_base() -> None:
    config = default_config()
    config.engine.asr_backend = "openai-api-compatible"

    with pytest.raises(ConfigError) as exc_info:
        resolve_asr_runtime_policy(config, env={"VOICEKEY_OPENAI_API_KEY": "sk-test"})

    message = str(exc_info.value)
    assert "engine.cloud_api_base" in message
    assert "voicekey config --set engine.cloud_api_base=https://api.openai.com/v1" in message
