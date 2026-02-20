"""Configuration loading/saving with safe fallback and backup behavior."""

from __future__ import annotations

import os
import platform
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from voicekey.config.migration import ConfigMigrationError, MigrationRegistry, migrate_payload
from voicekey.config.schema import (
    VoiceKeyConfig,
    default_config,
    serialize_config,
    validate_with_fallback,
)


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


@dataclass(frozen=True)
class StartupEnvOverrides:
    """Validated startup environment overrides."""

    config_path: Path | None = None
    model_dir: Path | None = None
    log_level: str | None = None
    disable_tray: bool | None = None


@dataclass(frozen=True)
class ReloadDecision:
    """Deterministic config hot-reload decision output."""

    safe_to_apply: tuple[str, ...]
    restart_required: tuple[str, ...]

    @property
    def restart_needed(self) -> bool:
        return bool(self.restart_required)


@dataclass(frozen=True)
class RuntimePaths:
    """Resolved runtime paths for config/data/model storage."""

    config_path: Path
    data_dir: Path
    model_dir: Path
    portable_mode: bool = False


_SAFE_RELOAD_KEYS: tuple[str, ...] = (
    "typing.confidence_threshold",
    "wake_word.sensitivity",
    "vad.speech_threshold",
    "wake_word.wake_window_timeout_seconds",
    "modes.inactivity_auto_pause_seconds",
    "ui.audio_feedback",
)

_SAFE_RELOAD_PREFIXES: tuple[str, ...] = ("hotkeys.",)

_RESTART_REQUIRED_KEYS: tuple[str, ...] = (
    "engine.model_profile",
    "engine.asr_backend",
)

_VALID_LOG_LEVELS: tuple[str, ...] = ("debug", "info", "warning", "error", "critical")


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
    if env_path is not None and env_path.strip():
        return Path(env_path.strip()).expanduser()

    system_name = (platform_name or platform.system()).lower()
    home = home_dir or Path.home()
    if system_name.startswith("win"):
        appdata = env_map.get("APPDATA")
        base = Path(appdata) if appdata else home / "AppData" / "Roaming"
        return base / "voicekey" / "config.yaml"

    return home / ".config" / "voicekey" / "config.yaml"


def resolve_runtime_paths(
    *,
    explicit_config_path: str | Path | None = None,
    model_dir_override: str | Path | None = None,
    env: Mapping[str, str] | None = None,
    platform_name: str | None = None,
    home_dir: Path | None = None,
    portable_mode: bool = False,
    portable_root: str | Path | None = None,
) -> RuntimePaths:
    """Resolve deterministic runtime paths for standard and portable modes."""
    if portable_mode:
        root = Path(portable_root).expanduser() if portable_root is not None else Path.cwd()
        config_path = (
            Path(explicit_config_path).expanduser()
            if explicit_config_path is not None
            else root / "config" / "config.yaml"
        )
        data_dir = root / "data"
        model_dir = (
            Path(model_dir_override).expanduser()
            if model_dir_override is not None
            else data_dir / "models"
        )
        return RuntimePaths(
            config_path=config_path,
            data_dir=data_dir,
            model_dir=model_dir,
            portable_mode=True,
        )

    config_path = resolve_config_path(
        explicit_path=explicit_config_path,
        env=env,
        platform_name=platform_name,
        home_dir=home_dir,
    )
    data_dir = config_path.parent
    model_dir = (
        Path(model_dir_override).expanduser() if model_dir_override is not None else data_dir / "models"
    )
    return RuntimePaths(
        config_path=config_path,
        data_dir=data_dir,
        model_dir=model_dir,
        portable_mode=False,
    )


def _set_secure_file_permissions(path: Path) -> None:
    """Set restrictive permissions on a file (owner read/write only).

    On POSIX systems, sets mode to 0o600. On Windows, this is a no-op
    as the OS handles file permissions differently via ACLs.
    """
    if os.name == "posix":
        os.chmod(path, 0o600)


def backup_config(path: Path) -> Path:
    """Create timestamped backup and return new path."""
    timestamp = datetime.now(tz=UTC).strftime("%Y%m%d%H%M%S")
    backup_path = path.with_suffix(f".yaml.bak.{timestamp}")
    backup_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    _set_secure_file_permissions(backup_path)
    return backup_path


def save_config(config: VoiceKeyConfig, path: Path) -> None:
    """Persist validated config to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialize_config(config), encoding="utf-8")
    _set_secure_file_permissions(path)


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
    except yaml.YAMLError:
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


def parse_startup_env_overrides(env: Mapping[str, str] | None = None) -> StartupEnvOverrides:
    """Parse supported startup env vars with actionable validation errors."""
    env_map = env if env is not None else os.environ

    config_path_value = _clean_optional_env_value(env_map.get("VOICEKEY_CONFIG"))
    model_dir_value = _clean_optional_env_value(env_map.get("VOICEKEY_MODEL_DIR"))
    log_level_value = _clean_optional_env_value(env_map.get("VOICEKEY_LOG_LEVEL"))
    disable_tray_value = _clean_optional_env_value(env_map.get("VOICEKEY_DISABLE_TRAY"))

    config_path = Path(config_path_value).expanduser() if config_path_value is not None else None
    model_dir = None
    if model_dir_value is not None:
        model_dir = Path(model_dir_value).expanduser()
        if model_dir.exists() and not model_dir.is_dir():
            raise ConfigError(
                "Invalid VOICEKEY_MODEL_DIR: expected a directory path; "
                f"got non-directory '{model_dir}'."
            )

    log_level = None
    if log_level_value is not None:
        normalized = log_level_value.lower()
        if normalized not in _VALID_LOG_LEVELS:
            allowed = ", ".join(_VALID_LOG_LEVELS)
            raise ConfigError(
                "Invalid VOICEKEY_LOG_LEVEL: "
                f"'{log_level_value}'. Allowed values: {allowed}."
            )
        log_level = normalized

    disable_tray = None
    if disable_tray_value is not None:
        disable_tray = _parse_bool_env_value(
            variable_name="VOICEKEY_DISABLE_TRAY",
            raw_value=disable_tray_value,
        )

    return StartupEnvOverrides(
        config_path=config_path,
        model_dir=model_dir,
        log_level=log_level,
        disable_tray=disable_tray,
    )


def evaluate_reload_decision(changed_keys: Iterable[str]) -> ReloadDecision:
    """Classify changed config keys into hot-reload-safe vs restart-required buckets."""
    safe_to_apply: set[str] = set()
    restart_required: set[str] = set()

    for raw_key in changed_keys:
        key = raw_key.strip()
        if not key:
            continue

        if _is_safe_reload_key(key):
            safe_to_apply.add(key)
            continue

        if key in _RESTART_REQUIRED_KEYS:
            restart_required.add(key)
            continue

        restart_required.add(key)

    return ReloadDecision(
        safe_to_apply=tuple(sorted(safe_to_apply)),
        restart_required=tuple(sorted(restart_required)),
    )


def _is_safe_reload_key(key: str) -> bool:
    if key in _SAFE_RELOAD_KEYS:
        return True
    return any(key.startswith(prefix) for prefix in _SAFE_RELOAD_PREFIXES)


def _clean_optional_env_value(raw_value: str | None) -> str | None:
    if raw_value is None:
        return None
    cleaned = raw_value.strip()
    return cleaned or None


def _parse_bool_env_value(*, variable_name: str, raw_value: str) -> bool:
    lowered = raw_value.lower()
    if lowered in {"1", "true", "yes", "on"}:
        return True
    if lowered in {"0", "false", "no", "off"}:
        return False
    raise ConfigError(
        f"Invalid {variable_name}: '{raw_value}'. Allowed boolean values: "
        "1/0, true/false, yes/no, on/off."
    )


__all__ = [
    "ConfigError",
    "ConfigLoadResult",
    "ReloadDecision",
    "RuntimePaths",
    "StartupEnvOverrides",
    "backup_config",
    "evaluate_reload_decision",
    "load_config",
    "parse_startup_env_overrides",
    "resolve_config_path",
    "resolve_runtime_paths",
    "save_config",
]
