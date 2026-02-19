"""Unit tests for config path resolution and persistence safeguards."""

from __future__ import annotations

from pathlib import Path

import yaml

from voicekey.config.migration import MigrationRegistry
from voicekey.config.manager import load_config, resolve_config_path


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
