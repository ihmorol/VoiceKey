"""Diagnostics output schema for secure export (E09-S02).

This module defines the structure for VoiceKey diagnostics output,
ensuring privacy-by-default with explicit opt-in for full exports.
"""

from __future__ import annotations

import platform
import sys
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class DiagnosticsExportMode(str, Enum):
    """Export mode for diagnostics."""
    
    REDACTED = "redacted"  # Default: redacted, privacy-safe
    FULL = "full"  # Opt-in: includes potentially sensitive data


class SystemInfo(BaseModel):
    """System information for diagnostics."""
    
    model_config = ConfigDict(extra="forbid")
    
    os_name: str = Field(description="Operating system name")
    os_version: str = Field(description="Operating system version")
    python_version: str = Field(description="Python version")
    python_implementation: str = Field(description="Python implementation (CPython, PyPy, etc.)")
    architecture: str = Field(description="System architecture (x86_64, ARM64, etc.)")
    platform_detail: str = Field(description="Detailed platform string")


class RuntimeStatus(BaseModel):
    """Runtime status summary for diagnostics."""
    
    model_config = ConfigDict(extra="forbid")
    
    state: str = Field(description="Current runtime state")
    listening_mode: str | None = Field(default=None, description="Current listening mode")
    model_status: str = Field(default="unknown", description="ASR model status")
    uptime_seconds: float | None = Field(default=None, description="Runtime uptime")
    

class ConfigSummary(BaseModel):
    """Redacted configuration summary for diagnostics."""
    
    model_config = ConfigDict(extra="forbid")
    
    version: int = Field(description="Config schema version")
    engine_profile: str = Field(description="ASR engine and model profile")
    default_mode: str = Field(description="Default listening mode")
    wake_word_enabled: bool = Field(description="Whether wake word is enabled")
    features_enabled: dict[str, bool] = Field(
        default_factory=dict,
        description="Feature flags status",
    )
    privacy_settings: dict[str, bool] = Field(
        default_factory=dict,
        description="Privacy-related settings",
    )


class DiagnosticsOutput(BaseModel):
    """Secure diagnostics output schema.
    
    By default, all diagnostics exports are redacted to protect
    user privacy and sensitive configuration values.
    """
    
    model_config = ConfigDict(extra="forbid")
    
    export_mode: DiagnosticsExportMode = Field(
        default=DiagnosticsExportMode.REDACTED,
        description="Export mode (redacted by default)",
    )
    export_timestamp: str = Field(
        description="ISO 8601 timestamp of export",
    )
    voicekey_version: str = Field(
        default="unknown",
        description="VoiceKey version",
    )
    system: SystemInfo = Field(description="System information")
    config_summary: ConfigSummary = Field(description="Redacted config summary")
    runtime_status: RuntimeStatus = Field(
        default_factory=lambda: RuntimeStatus(state="not_running"),
        description="Runtime status summary",
    )
    paths: dict[str, str] = Field(
        default_factory=dict,
        description="Redacted runtime paths",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Any warnings or issues detected",
    )
    
    # Explicitly excluded by default:
    # - raw audio data (never included)
    # - transcript history (never included)
    # - full config with potential secrets (only in FULL mode)
    
    @classmethod
    def create_redacted(
        cls,
        *,
        voicekey_version: str = "unknown",
        config_dict: dict[str, Any] | None = None,
        runtime_state: str = "not_running",
        runtime_mode: str | None = None,
        model_status: str = "unknown",
        paths: dict[str, str] | None = None,
        warnings: list[str] | None = None,
    ) -> "DiagnosticsOutput":
        """Create a redacted diagnostics output.
        
        This is the default and safe way to create diagnostics.
        """
        from voicekey.diagnostics.redaction import (
            redact_config_for_diagnostics,
            redact_path,
        )
        
        system = SystemInfo(
            os_name=platform.system(),
            os_version=platform.version(),
            python_version=platform.python_version(),
            python_implementation=platform.python_implementation(),
            architecture=platform.machine(),
            platform_detail=platform.platform(),
        )
        
        # Build redacted config summary
        if config_dict:
            redacted_config = redact_config_for_diagnostics(config_dict)
            config_summary = ConfigSummary(
                version=redacted_config.get("version", 1),
                engine_profile=f"{redacted_config.get('engine', {}).get('asr_backend', 'unknown')}/{redacted_config.get('engine', {}).get('model_profile', 'unknown')}",
                default_mode=redacted_config.get("modes", {}).get("default", "wake_word"),
                wake_word_enabled=redacted_config.get("wake_word", {}).get("enabled", True),
                features_enabled={
                    "text_expansion": redacted_config.get("features", {}).get("text_expansion_enabled", False),
                    "per_app_profiles": redacted_config.get("features", {}).get("per_app_profiles_enabled", False),
                    "window_commands": redacted_config.get("features", {}).get("window_commands_enabled", False),
                },
                privacy_settings={
                    "telemetry_enabled": redacted_config.get("privacy", {}).get("telemetry_enabled", False),
                    "transcript_logging": redacted_config.get("privacy", {}).get("transcript_logging", False),
                    "redact_debug_text": redacted_config.get("privacy", {}).get("redact_debug_text", True),
                },
            )
        else:
            config_summary = ConfigSummary(
                version=1,
                engine_profile="unknown",
                default_mode="wake_word",
                wake_word_enabled=True,
                features_enabled={},
                privacy_settings={},
            )
        
        # Redact paths
        redacted_paths = {}
        if paths:
            for key, value in paths.items():
                redacted_paths[key] = redact_path(value) or "[NONE]"
        
        return cls(
            export_mode=DiagnosticsExportMode.REDACTED,
            export_timestamp=datetime.now(timezone.utc).isoformat(),
            voicekey_version=voicekey_version,
            system=system,
            config_summary=config_summary,
            runtime_status=RuntimeStatus(
                state=runtime_state,
                listening_mode=runtime_mode,
                model_status=model_status,
            ),
            paths=redacted_paths,
            warnings=warnings or [],
        )


# Warning message for full export mode
FULL_EXPORT_WARNING = """
WARNING: Full diagnostics export may contain sensitive information including:
- User file paths
- Configuration values that may include secrets
- Custom commands with sensitive content

This export should only be shared with trusted parties or for
debugging purposes where privacy is not a concern.

Consider using the default redacted export instead.
"""


class FullDiagnosticsOutput(BaseModel):
    """Full diagnostics output with sensitive data.
    
    WARNING: This mode includes potentially sensitive information.
    Use only when explicitly needed and with user consent.
    """
    
    model_config = ConfigDict(extra="forbid")
    
    export_mode: Literal[DiagnosticsExportMode.FULL] = DiagnosticsExportMode.FULL
    export_timestamp: str
    voicekey_version: str = "unknown"
    system: SystemInfo
    config_full: dict[str, Any] = Field(
        description="Full configuration (may contain sensitive data)",
    )
    runtime_status: RuntimeStatus
    paths: dict[str, str] = Field(
        description="Full runtime paths (may contain user directories)",
    )
    warnings: list[str] = Field(default_factory=list)
    _security_warning: str = FULL_EXPORT_WARNING
    
    @classmethod
    def create_full(
        cls,
        *,
        voicekey_version: str = "unknown",
        config_dict: dict[str, Any],
        runtime_state: str = "not_running",
        runtime_mode: str | None = None,
        model_status: str = "unknown",
        paths: dict[str, str] | None = None,
        warnings: list[str] | None = None,
    ) -> "FullDiagnosticsOutput":
        """Create a full diagnostics output with sensitive data.
        
        WARNING: This should only be used with explicit user consent.
        """
        system = SystemInfo(
            os_name=platform.system(),
            os_version=platform.version(),
            python_version=platform.python_version(),
            python_implementation=platform.python_implementation(),
            architecture=platform.machine(),
            platform_detail=platform.platform(),
        )
        
        config_summary = ConfigSummary(
            version=config_dict.get("version", 1),
            engine_profile=f"{config_dict.get('engine', {}).get('asr_backend', 'unknown')}/{config_dict.get('engine', {}).get('model_profile', 'unknown')}",
            default_mode=config_dict.get("modes", {}).get("default", "wake_word"),
            wake_word_enabled=config_dict.get("wake_word", {}).get("enabled", True),
            features_enabled={
                "text_expansion": config_dict.get("features", {}).get("text_expansion_enabled", False),
                "per_app_profiles": config_dict.get("features", {}).get("per_app_profiles_enabled", False),
                "window_commands": config_dict.get("features", {}).get("window_commands_enabled", False),
            },
            privacy_settings={
                "telemetry_enabled": config_dict.get("privacy", {}).get("telemetry_enabled", False),
                "transcript_logging": config_dict.get("privacy", {}).get("transcript_logging", False),
                "redact_debug_text": config_dict.get("privacy", {}).get("redact_debug_text", True),
            },
        )
        
        return cls(
            export_timestamp=datetime.now(timezone.utc).isoformat(),
            voicekey_version=voicekey_version,
            system=system,
            config_full=config_dict,
            runtime_status=RuntimeStatus(
                state=runtime_state,
                listening_mode=runtime_mode,
                model_status=model_status,
            ),
            paths=paths or {},
            warnings=warnings or [],
        )


__all__ = [
    "DiagnosticsExportMode",
    "SystemInfo",
    "RuntimeStatus",
    "ConfigSummary",
    "DiagnosticsOutput",
    "FullDiagnosticsOutput",
    "FULL_EXPORT_WARNING",
]
