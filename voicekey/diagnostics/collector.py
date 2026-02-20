"""Diagnostics collection and export functions (E09-S02).

This module provides functions to collect and export VoiceKey diagnostics
in a secure, privacy-preserving manner.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from voicekey.config.manager import load_config
from voicekey.diagnostics.redaction import redact_path, contains_secrets
from voicekey.diagnostics.schema import (
    DiagnosticsOutput,
    DiagnosticsExportMode,
    FullDiagnosticsOutput,
    FULL_EXPORT_WARNING,
)


def collect_diagnostics(
    *,
    include_full_config: bool = False,
    runtime_state: str = "not_running",
    runtime_mode: str | None = None,
    model_status: str = "unknown",
    additional_paths: dict[str, str] | None = None,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    """Collect diagnostics for VoiceKey.
    
    By default, returns a redacted, privacy-safe diagnostics export.
    
    Args:
        include_full_config: If True, include full config (WARNING: may contain sensitive data)
        runtime_state: Current runtime state
        runtime_mode: Current listening mode
        model_status: ASR model status
        additional_paths: Additional paths to include
        warnings: Any warnings to include
    
    Returns:
        Diagnostics dictionary suitable for export
    """
    # Try to get version
    try:
        from voicekey import __version__
        version = __version__
    except ImportError:
        version = "unknown"
    
    # Try to load config
    config_dict: dict[str, Any] = {}
    config_warnings: list[str] = []
    
    try:
        load_result = load_config()
        config_dict = load_result.config.model_dump(mode="python")
        config_warnings = list(load_result.warnings)
    except Exception as e:
        config_warnings.append(f"Could not load config: {e}")
    
    # Build paths dict
    paths: dict[str, str] = {}
    if additional_paths:
        paths.update(additional_paths)
    
    # Try to resolve runtime paths
    try:
        from voicekey.config.manager import resolve_runtime_paths
        runtime_paths = resolve_runtime_paths()
        paths["config_path"] = str(runtime_paths.config_path)
        paths["data_dir"] = str(runtime_paths.data_dir)
        paths["model_dir"] = str(runtime_paths.model_dir)
    except Exception:
        pass
    
    all_warnings = (warnings or []) + config_warnings
    
    if include_full_config:
        # WARNING: Full export mode
        output = FullDiagnosticsOutput.create_full(
            voicekey_version=version,
            config_dict=config_dict,
            runtime_state=runtime_state,
            runtime_mode=runtime_mode,
            model_status=model_status,
            paths=paths,
            warnings=all_warnings,
        )
        return output.model_dump(mode="python")
    else:
        # Default: redacted export
        output = DiagnosticsOutput.create_redacted(
            voicekey_version=version,
            config_dict=config_dict,
            runtime_state=runtime_state,
            runtime_mode=runtime_mode,
            model_status=model_status,
            paths=paths,
            warnings=all_warnings,
        )
        return output.model_dump(mode="python")


def export_diagnostics(
    export_path: Path | str,
    *,
    include_full_config: bool = False,
    runtime_state: str = "not_running",
    runtime_mode: str | None = None,
    model_status: str = "unknown",
    additional_paths: dict[str, str] | None = None,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    """Export diagnostics to a file.
    
    By default, exports redacted, privacy-safe diagnostics.
    
    Args:
        export_path: Path to write diagnostics file
        include_full_config: If True, include full config (WARNING: may contain sensitive data)
        runtime_state: Current runtime state
        runtime_mode: Current listening mode
        model_status: ASR model status
        additional_paths: Additional paths to include
        warnings: Any warnings to include
    
    Returns:
        The diagnostics dictionary that was exported
    """
    diagnostics = collect_diagnostics(
        include_full_config=include_full_config,
        runtime_state=runtime_state,
        runtime_mode=runtime_mode,
        model_status=model_status,
        additional_paths=additional_paths,
        warnings=warnings,
    )
    
    path = Path(export_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(diagnostics, f, indent=2, sort_keys=False)
    
    return diagnostics


def validate_diagnostics_safety(diagnostics: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate that diagnostics output is safe (no secrets leaked).
    
    This is a safety check to ensure no sensitive data was accidentally
    included in the diagnostics output.
    
    Args:
        diagnostics: Diagnostics dictionary to validate
    
    Returns:
        Tuple of (is_safe, list_of_issues)
    """
    issues: list[str] = []
    
    def check_dict(data: dict[str, Any], path: str = "") -> None:
        for key, value in data.items():
            current_path = f"{path}.{key}" if path else key
            
            if isinstance(value, dict):
                check_dict(value, current_path)
            elif isinstance(value, str):
                if contains_secrets(value):
                    issues.append(f"Potential secret found at {current_path}")
    
    check_dict(diagnostics)
    
    return len(issues) == 0, issues


def get_export_warning_for_full_mode() -> str:
    """Get the warning message for full export mode."""
    return FULL_EXPORT_WARNING.strip()


__all__ = [
    "collect_diagnostics",
    "export_diagnostics",
    "validate_diagnostics_safety",
    "get_export_warning_for_full_mode",
]
