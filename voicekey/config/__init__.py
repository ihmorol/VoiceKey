"""Configuration management exports."""

from voicekey.config.manager import (
    ConfigError,
    ConfigLoadResult,
    ReloadDecision,
    StartupEnvOverrides,
    backup_config,
    evaluate_reload_decision,
    load_config,
    parse_startup_env_overrides,
    resolve_config_path,
    save_config,
)
from voicekey.config.profiles import (
    ActiveAppIdentity,
    AppProfileResolver,
    ProfileResolutionResult,
    resolve_effective_profile,
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
    "ReloadDecision",
    "StartupEnvOverrides",
    "ActiveAppIdentity",
    "AppProfileResolver",
    "ProfileResolutionResult",
    "VoiceKeyConfig",
    "backup_config",
    "default_config",
    "evaluate_reload_decision",
    "load_config",
    "parse_startup_env_overrides",
    "resolve_effective_profile",
    "resolve_config_path",
    "save_config",
    "serialize_config",
    "validate_with_fallback",
]
