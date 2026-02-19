"""Configuration loading/saving with safe fallback and backup behavior."""

from __future__ import annotations

import os
import platform
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

import yaml

from voicekey.config.migration import ConfigMigrationError, MigrationRegistry, migrate_payload
from voicekey.config.schema import VoiceKeyConfig, default_config, serialize_config, validate_with_fallback


class ConfigError(RuntimeError):
    """Typed configuration subsystem error."""


@dataclass(frozen=True)
class ConfigLoadResult:
    """Result metadata emitted by config load operations."""

    config: VoiceKeyConfig
    path: Path
    created: bool
    warnings: tuple[str, ...] = ()
    backup_path: Path | None = None


def resolve_config_path(
    *,
    explicit_path: str | Path | None = None,
    env: Mapping[str, str] | None = None,
    platform_name: str | None = None,
    home_dir: Path | None = None,
) -> Path:
    """Resolve effective config path from CLI/env/platform defaults."""
    if explicit_path is not None:
        return Path(explicit_path).expanduser()

    env_map = env if env is not None else os.environ
    env_path = env_map.get("VOICEKEY_CONFIG")
    if env_path:
        return Path(env_path).expanduser()

    system_name = (platform_name or platform.system()).lower()
    home = home_dir or Path.home()
    if system_name.startswith("win"):
        appdata = env_map.get("APPDATA")
        base = Path(appdata) if appdata else home / "AppData" / "Roaming"
        return base / "voicekey" / "config.yaml"

    return home / ".config" / "voicekey" / "config.yaml"


def backup_config(path: Path) -> Path:
    """Create timestamped backup and return new path."""
    timestamp = datetime.now(tz=UTC).strftime("%Y%m%d%H%M%S")
    backup_path = path.with_suffix(f".yaml.bak.{timestamp}")
    backup_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    return backup_path


def save_config(config: VoiceKeyConfig, path: Path) -> None:
    """Persist validated config to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialize_config(config), encoding="utf-8")


def load_config(
    *,
    explicit_path: str | Path | None = None,
    env: Mapping[str, str] | None = None,
    platform_name: str | None = None,
    home_dir: Path | None = None,
    migration_registry: MigrationRegistry | None = None,
) -> ConfigLoadResult:
    """Load config from disk with schema fallback and backup safeguards."""
    config_path = resolve_config_path(
        explicit_path=explicit_path,
        env=env,
        platform_name=platform_name,
        home_dir=home_dir,
    )

    if not config_path.exists():
        config = default_config()
        save_config(config, config_path)
        return ConfigLoadResult(config=config, path=config_path, created=True)

    try:
        raw_text = config_path.read_text(encoding="utf-8")
    except OSError as exc:  # pragma: no cover - OS-level error path
        raise ConfigError(f"Failed to read config file '{config_path}': {exc}") from exc

    try:
        parsed: Any = yaml.safe_load(raw_text)
    except yaml.YAMLError as exc:
        backup_path = backup_config(config_path)
        config = default_config()
        save_config(config, config_path)
        warnings = (
            f"Failed to parse config YAML. Default config restored; backup preserved at '{backup_path}'.",
            "Migration note: invalid or unreadable config was replaced with safe defaults.",
        )
        return ConfigLoadResult(
            config=config,
            path=config_path,
            created=False,
            warnings=warnings,
            backup_path=backup_path,
        )

    if parsed is None:
        parsed = {}

    if not isinstance(parsed, dict):
        backup_path = backup_config(config_path)
        config = default_config()
        save_config(config, config_path)
        warnings = (
            "Config root must be a YAML mapping. Default config restored.",
            f"Migration note: original config preserved at '{backup_path}'.",
        )
        return ConfigLoadResult(
            config=config,
            path=config_path,
            created=False,
            warnings=warnings,
            backup_path=backup_path,
        )

    try:
        migration_result = migrate_payload(parsed, registry=migration_registry)
    except ConfigMigrationError as exc:
        backup_path = backup_config(config_path)
        config = default_config()
        save_config(config, config_path)
        warnings = (
            f"Config migration failed: {exc}. Default config restored.",
            f"Migration note: original config preserved at '{backup_path}'.",
        )
        return ConfigLoadResult(
            config=config,
            path=config_path,
            created=False,
            warnings=warnings,
            backup_path=backup_path,
        )

    config, validation_warnings = validate_with_fallback(migration_result.payload)
    requires_rewrite = migration_result.migrated or bool(validation_warnings)
    combined_warnings = migration_result.warnings + validation_warnings

    if not requires_rewrite:
        return ConfigLoadResult(
            config=config,
            path=config_path,
            created=False,
            warnings=combined_warnings,
        )

    backup_path = backup_config(config_path)
    save_config(config, config_path)
    warnings = combined_warnings + (
        f"Migration note: original config preserved at '{backup_path}'.",
    )
    return ConfigLoadResult(
        config=config,
        path=config_path,
        created=False,
        warnings=warnings,
        backup_path=backup_path,
    )


__all__ = [
    "ConfigError",
    "ConfigLoadResult",
    "backup_config",
    "load_config",
    "resolve_config_path",
    "save_config",
]
