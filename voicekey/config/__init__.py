"""Configuration management exports."""

from voicekey.config.manager import (
    ConfigError,
    ConfigLoadResult,
    backup_config,
    load_config,
    resolve_config_path,
    save_config,
)
from voicekey.config.schema import (
    CONFIG_VERSION,
    VoiceKeyConfig,
    default_config,
    serialize_config,
    validate_with_fallback,
)

__all__ = [
    "CONFIG_VERSION",
    "ConfigError",
    "ConfigLoadResult",
    "VoiceKeyConfig",
    "backup_config",
    "default_config",
    "load_config",
    "resolve_config_path",
    "save_config",
    "serialize_config",
    "validate_with_fallback",
]
