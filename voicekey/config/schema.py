"""Typed VoiceKey configuration schema and validation helpers."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

CONFIG_VERSION = 3


class EngineConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asr_backend: Literal["faster-whisper"] = "faster-whisper"
    model_profile: Literal["tiny", "base", "small"] = "base"
    compute_type: Literal["int8", "int16", "float16"] = "int8"
    language: str = "en"


class AudioConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sample_rate_hz: Literal[8000, 16000, 32000, 44100, 48000] = 16000
    channels: Literal[1] = 1
    chunk_ms: int = Field(default=160, ge=80, le=300)
    device_id: int | None = None


class VADConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    speech_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    min_speech_ms: int = Field(default=120, ge=50, le=2000)


class WakeWordConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    phrase: str = "voice key"
    sensitivity: float = Field(default=0.55, ge=0.0, le=1.0)
    wake_window_timeout_seconds: int = Field(default=5, ge=1, le=30)


class ModesConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    default: Literal["wake_word", "toggle", "continuous"] = "wake_word"
    inactivity_auto_pause_seconds: int = Field(default=30, ge=5, le=300)
    allow_continuous_mode: bool = True
    paused_resume_phrase_enabled: bool = True


class HotkeysConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    toggle_listening: str = "ctrl+shift+`"
    pause: str = "ctrl+shift+p"
    stop: str = "ctrl+shift+e"


class TypingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    char_delay_ms: int = Field(default=8, ge=0, le=50)
    undo_buffer_segments: int = Field(default=30, ge=1, le=200)
    confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0)


class UIConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tray_enabled: bool = True
    start_minimized_to_tray: bool = True
    terminal_dashboard: bool = True
    audio_feedback: bool = True
    show_latency: bool = True


class SystemConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    autostart_enabled: bool = False
    single_instance: bool = True
    daemon_mode_default: bool = True


class FeaturesConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text_expansion_enabled: bool = False
    per_app_profiles_enabled: bool = False
    window_commands_enabled: bool = False


class PrivacyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    telemetry_enabled: bool = False
    transcript_logging: bool = False
    redact_debug_text: bool = True
    persist_audio: bool = False


class VoiceKeyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int = CONFIG_VERSION
    engine: EngineConfig = Field(default_factory=EngineConfig)
    audio: AudioConfig = Field(default_factory=AudioConfig)
    vad: VADConfig = Field(default_factory=VADConfig)
    wake_word: WakeWordConfig = Field(default_factory=WakeWordConfig)
    modes: ModesConfig = Field(default_factory=ModesConfig)
    hotkeys: HotkeysConfig = Field(default_factory=HotkeysConfig)
    typing: TypingConfig = Field(default_factory=TypingConfig)
    ui: UIConfig = Field(default_factory=UIConfig)
    system: SystemConfig = Field(default_factory=SystemConfig)
    features: FeaturesConfig = Field(default_factory=FeaturesConfig)
    privacy: PrivacyConfig = Field(default_factory=PrivacyConfig)
    app_profiles: dict[str, dict[str, Any]] = Field(default_factory=dict)
    custom_commands: dict[str, dict[str, Any]] = Field(default_factory=dict)
    snippets: dict[str, str] = Field(
        default_factory=lambda: {
            "ty": "thank you",
            "brb": "be right back",
        }
    )


def default_config() -> VoiceKeyConfig:
    """Create default validated configuration instance."""
    return VoiceKeyConfig()


def serialize_config(config: VoiceKeyConfig) -> str:
    """Serialize configuration to stable YAML text."""
    return yaml.safe_dump(config.model_dump(mode="python"), sort_keys=False)


def validate_with_fallback(raw_data: dict[str, Any] | None) -> tuple[VoiceKeyConfig, tuple[str, ...]]:
    """Validate raw config data and replace invalid fields with safe defaults."""
    merged = default_config().model_dump(mode="python")
    if raw_data:
        _merge_dicts(merged, raw_data)

    defaults = default_config().model_dump(mode="python")
    warnings: list[str] = []

    while True:
        try:
            validated = VoiceKeyConfig.model_validate(merged)
            return validated, tuple(warnings)
        except ValidationError as exc:
            changed = False
            for error in exc.errors():
                loc = tuple(str(part) for part in error["loc"])
                field_path = ".".join(loc)
                has_default, default_value = _try_get_nested(defaults, loc)
                if has_default:
                    _set_nested(merged, loc, deepcopy(default_value))
                    warnings.append(
                        f"Invalid value at '{field_path}' replaced with default: {error['msg']}"
                    )
                    changed = True
                    continue

                if _delete_nested(merged, loc):
                    warnings.append(
                        f"Unsupported key '{field_path}' removed during validation: {error['msg']}"
                    )
                    changed = True

            if not changed:
                raise


def _merge_dicts(base: dict[str, Any], override: dict[str, Any]) -> None:
    for key, value in override.items():
        if isinstance(base.get(key), dict) and isinstance(value, dict):
            _merge_dicts(base[key], value)
        else:
            base[key] = value


def _try_get_nested(data: dict[str, Any], path: tuple[str, ...]) -> tuple[bool, Any]:
    current: Any = data
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return False, None
        current = current[key]
    return True, current


def _set_nested(data: dict[str, Any], path: tuple[str, ...], value: Any) -> None:
    current = data
    for key in path[:-1]:
        next_item = current.get(key)
        if not isinstance(next_item, dict):
            next_item = {}
            current[key] = next_item
        current = next_item
    current[path[-1]] = value


def _delete_nested(data: dict[str, Any], path: tuple[str, ...]) -> bool:
    if not path:
        return False

    current = data
    for key in path[:-1]:
        next_item = current.get(key)
        if not isinstance(next_item, dict):
            return False
        current = next_item

    return current.pop(path[-1], None) is not None


__all__ = [
    "CONFIG_VERSION",
    "VoiceKeyConfig",
    "default_config",
    "serialize_config",
    "validate_with_fallback",
]
