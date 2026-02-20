"""Secure diagnostics module for VoiceKey (E09-S02).

This module provides privacy-by-default diagnostics collection and export
functionality. All exports are redacted by default to protect user privacy.

Security Requirements (from requirements/security.md sections 4.1 and 6):
- Diagnostics export is redacted by default
- User paths are redacted
- Config values with secrets are redacted
- No raw audio or transcripts are included by default
- Opt-in for full export with explicit warning

Usage:
    from voicekey.diagnostics import collect_diagnostics, export_diagnostics
    
    # Default: redacted, privacy-safe export
    diagnostics = collect_diagnostics()
    
    # Export to file
    export_diagnostics("/path/to/diagnostics.json")
    
    # Full export (WARNING: may contain sensitive data)
    diagnostics = collect_diagnostics(include_full_config=True)
"""

from __future__ import annotations

from voicekey.diagnostics.collector import (
    collect_diagnostics,
    export_diagnostics,
    validate_diagnostics_safety,
    get_export_warning_for_full_mode,
)
from voicekey.diagnostics.redaction import (
    REDACTED_PLACEHOLDER,
    PATH_REDACTED_PLACEHOLDER,
    is_sensitive_field,
    is_path_field,
    redact_path,
    redact_dict,
    redact_config_for_diagnostics,
    contains_secrets,
)
from voicekey.diagnostics.schema import (
    DiagnosticsExportMode,
    SystemInfo,
    RuntimeStatus,
    ConfigSummary,
    DiagnosticsOutput,
    FullDiagnosticsOutput,
    FULL_EXPORT_WARNING,
)


__all__ = [
    # Collector functions
    "collect_diagnostics",
    "export_diagnostics",
    "validate_diagnostics_safety",
    "get_export_warning_for_full_mode",
    # Redaction utilities
    "REDACTED_PLACEHOLDER",
    "PATH_REDACTED_PLACEHOLDER",
    "is_sensitive_field",
    "is_path_field",
    "redact_path",
    "redact_dict",
    "redact_config_for_diagnostics",
    "contains_secrets",
    # Schema types
    "DiagnosticsExportMode",
    "SystemInfo",
    "RuntimeStatus",
    "ConfigSummary",
    "DiagnosticsOutput",
    "FullDiagnosticsOutput",
    "FULL_EXPORT_WARNING",
]
