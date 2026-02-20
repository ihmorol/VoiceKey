"""Redaction utilities for secure diagnostics export (E09-S02).

This module provides redaction functions to sanitize sensitive data
before including it in diagnostics exports.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any


# Fields that contain sensitive information and should be redacted
SENSITIVE_FIELD_PATTERNS = [
    re.compile(r"password", re.IGNORECASE),
    re.compile(r"secret", re.IGNORECASE),
    re.compile(r"token", re.IGNORECASE),
    re.compile(r"api_?key", re.IGNORECASE),
    re.compile(r"credential", re.IGNORECASE),
    re.compile(r"auth", re.IGNORECASE),
    re.compile(r"private", re.IGNORECASE),
]

# Path-like fields that should be redacted to show only structure
PATH_FIELD_PATTERNS = [
    re.compile(r"_path$", re.IGNORECASE),
    re.compile(r"_dir$", re.IGNORECASE),
    re.compile(r"^path$", re.IGNORECASE),
    re.compile(r"^dir$", re.IGNORECASE),
    re.compile(r"_root$", re.IGNORECASE),
]

REDACTED_PLACEHOLDER = "[REDACTED]"
PATH_REDACTED_PLACEHOLDER = "[PATH_REDACTED]"


def is_sensitive_field(field_name: str) -> bool:
    """Check if a field name indicates sensitive data."""
    return any(pattern.search(field_name) for pattern in SENSITIVE_FIELD_PATTERNS)


def is_path_field(field_name: str) -> bool:
    """Check if a field name indicates a file system path."""
    return any(pattern.search(field_name) for pattern in PATH_FIELD_PATTERNS)


def redact_path(path_value: str | None) -> str | None:
    """Redact a path to show only structure, not user directories.
    
    Examples:
        /home/username/.config/voicekey -> [HOME]/.config/voicekey
        C:\\Users\\john\\AppData -> [HOME]\\AppData
        /tmp/voicekey-test -> [TMP]/voicekey-test
    """
    if path_value is None:
        return None
    
    if not isinstance(path_value, str):
        return PATH_REDACTED_PLACEHOLDER
    
    result = path_value
    
    # Redact home directory
    home = os.path.expanduser("~")
    if home and home != "/" and result.startswith(home):
        result = result.replace(home, "[HOME]", 1)
    
    # Redact common user paths on Windows
    if os.name == "nt":
        # Match C:\Users\username pattern
        result = re.sub(
            r"^([A-Za-z]:\\)Users\\[^\\]+",
            r"\1Users\\[USER]",
            result,
        )
    
    # Redact /home/username on Linux
    result = re.sub(
        r"^/home/[^/]+",
        "/home/[USER]",
        result,
    )
    
    # Redact /Users/username on macOS
    result = re.sub(
        r"^/Users/[^/]+",
        "/Users/[USER]",
        result,
    )
    
    # Redact temp directories that might contain username
    tmp_dir = "/tmp"
    if result.startswith(tmp_dir):
        # Keep /tmp but redact any username-like segments after
        pass  # /tmp is generally safe to show
    
    return result


def redact_sensitive_value(value: Any) -> str:
    """Redact a sensitive value."""
    return REDACTED_PLACEHOLDER


def redact_dict(
    data: dict[str, Any],
    *,
    redact_paths: bool = True,
    redact_secrets: bool = True,
) -> dict[str, Any]:
    """Recursively redact sensitive fields in a dictionary.
    
    Args:
        data: Dictionary to redact
        redact_paths: Whether to redact user paths
        redact_secrets: Whether to redact secret/sensitive values
    
    Returns:
        Redacted copy of the dictionary
    """
    result: dict[str, Any] = {}
    
    for key, value in data.items():
        if redact_secrets and is_sensitive_field(key):
            result[key] = REDACTED_PLACEHOLDER
        elif redact_paths and is_path_field(key) and isinstance(value, str):
            result[key] = redact_path(value)
        elif isinstance(value, dict):
            result[key] = redact_dict(
                value,
                redact_paths=redact_paths,
                redact_secrets=redact_secrets,
            )
        elif isinstance(value, list):
            result[key] = [
                redact_dict(item, redact_paths=redact_paths, redact_secrets=redact_secrets)
                if isinstance(item, dict)
                else item
                for item in value
            ]
        else:
            result[key] = value
    
    return result


def redact_config_for_diagnostics(config_dict: dict[str, Any]) -> dict[str, Any]:
    """Redact configuration for safe diagnostics export.
    
    This function specifically handles VoiceKey configuration,
    ensuring sensitive fields are redacted while preserving
    useful debugging information.
    """
    redacted = redact_dict(config_dict, redact_paths=True, redact_secrets=True)
    
    # Additional specific redactions for VoiceKey config
    # Note: VoiceKey's default config doesn't have secret fields,
    # but custom commands or app profiles might contain sensitive data
    
    # Redact any custom command values that might be sensitive
    if "custom_commands" in redacted and isinstance(redacted["custom_commands"], dict):
        redacted["custom_commands"] = {
            name: {"action": "[REDACTED]", "type": cmd.get("type", "unknown")}
            for name, cmd in redacted["custom_commands"].items()
            if isinstance(cmd, dict)
        }
    
    # Redact snippet content that might contain sensitive text
    if "snippets" in redacted and isinstance(redacted["snippets"], dict):
        redacted["snippets"] = {
            key: "[REDACTED]" for key in redacted["snippets"]
        }
    
    return redacted


def contains_secrets(text: str) -> bool:
    """Check if text might contain secret-like patterns.
    
    This is a heuristic check for common secret patterns.
    """
    secret_patterns = [
        # API keys (common formats)
        r"sk-[a-zA-Z0-9]{20,}",
        r"api[_-]?key['\"]?\s*[:=]\s*['\"][a-zA-Z0-9]{16,}['\"]",
        # Tokens
        r"bearer\s+[a-zA-Z0-9._-]+",
        r"token['\"]?\s*[:=]\s*['\"][a-zA-Z0-9]{16,}['\"]",
        # Passwords in connection strings
        r"password['\"]?\s*[:=]\s*['\"][^'\"]+['\"]",
        r"://[^:]+:[^@]+@",  # user:pass@host
    ]
    
    for pattern in secret_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    return False


__all__ = [
    "REDACTED_PLACEHOLDER",
    "PATH_REDACTED_PLACEHOLDER",
    "is_sensitive_field",
    "is_path_field",
    "redact_path",
    "redact_sensitive_value",
    "redact_dict",
    "redact_config_for_diagnostics",
    "contains_secrets",
]
