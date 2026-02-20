"""Privacy startup assertions for runtime guardrails.

This module provides startup verification that privacy defaults are correctly
configured per requirements/security.md and architecture.md section 12.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PrivacyAssertionResult:
    """Result of privacy startup assertions."""

    passed: bool
    telemetry_disabled: bool
    transcript_logging_disabled: bool
    redaction_enabled: bool
    warnings: tuple[str, ...]
    errors: tuple[str, ...]


def verify_privacy_defaults(config_data: dict[str, Any]) -> PrivacyAssertionResult:
    """Verify that privacy defaults are correctly configured.

    This should be called at startup to ensure:
    - Telemetry is disabled by default
    - Transcript logging is disabled by default
    - Debug text redaction is enabled by default

    Args:
        config_data: The loaded configuration dictionary.

    Returns:
        PrivacyAssertionResult with pass/fail status and any warnings/errors.
    """
    warnings: list[str] = []
    errors: list[str] = []

    privacy = config_data.get("privacy", {})

    # Check telemetry disabled
    telemetry_enabled = privacy.get("telemetry_enabled", False)
    if telemetry_enabled:
        warnings.append(
            "Telemetry is ENABLED. This requires explicit user opt-in. "
            "VoiceKey runs fully offline by default."
        )
    telemetry_disabled = not telemetry_enabled

    # Check transcript logging disabled
    transcript_logging = privacy.get("transcript_logging", False)
    if transcript_logging:
        warnings.append(
            "Transcript logging is ENABLED. Recognized speech will be persisted. "
            "Disable for privacy."
        )
    transcript_logging_disabled = not transcript_logging

    # Check debug redaction enabled
    redaction_enabled = privacy.get("redact_debug_text", True)
    if not redaction_enabled:
        warnings.append(
            "Debug text redaction is DISABLED. Transcripts may appear in logs. "
            "Enable for privacy."
        )

    passed = telemetry_disabled and transcript_logging_disabled and redaction_enabled

    if not passed:
        errors.append("Privacy defaults verification failed. See warnings for details.")

    return PrivacyAssertionResult(
        passed=passed,
        telemetry_disabled=telemetry_disabled,
        transcript_logging_disabled=transcript_logging_disabled,
        redaction_enabled=redaction_enabled,
        warnings=tuple(warnings),
        errors=tuple(errors),
    )


def assert_offline_runtime(config_data: dict[str, Any]) -> None:
    """Assert that the configuration supports offline runtime.

    This verifies that no features requiring network access are enabled.

    Args:
        config_data: The loaded configuration dictionary.

    Raises:
        RuntimeError: If configuration violates offline runtime requirements.
    """
    privacy = config_data.get("privacy", {})

    if privacy.get("telemetry_enabled", False):
        raise RuntimeError(
            "Offline runtime violation: telemetry_enabled is True. "
            "VoiceKey requires offline operation after model download."
        )


def log_privacy_startup_status(result: PrivacyAssertionResult) -> None:
    """Log the privacy startup assertion result.

    Args:
        result: The privacy assertion result to log.
    """
    if result.passed:
        logger.info("Privacy defaults verified: telemetry disabled, offline mode confirmed")
    else:
        logger.warning("Privacy defaults verification detected non-default settings")

    for warning in result.warnings:
        logger.warning("Privacy warning: %s", warning)

    for error in result.errors:
        logger.error("Privacy error: %s", error)


def verify_migration_telemetry_safety(
    old_config: dict[str, Any] | None,
    new_config: dict[str, Any],
) -> bool:
    """Verify that migration does not implicitly enable telemetry.

    This ensures that:
    - If telemetry was disabled in old config, it stays disabled
    - If old config doesn't exist, telemetry stays at default (disabled)
    - Telemetry cannot be enabled by migration logic

    Args:
        old_config: The pre-migration config (or None if new install).
        new_config: The post-migration config.

    Returns:
        True if telemetry safety is preserved, False otherwise.
    """
    new_telemetry = new_config.get("privacy", {}).get("telemetry_enabled", False)

    # New installs should have telemetry disabled
    if old_config is None:
        return not new_telemetry

    # Existing configs should preserve telemetry state
    old_telemetry = old_config.get("privacy", {}).get("telemetry_enabled", False)

    # Migration cannot enable telemetry if it was disabled
    if not old_telemetry and new_telemetry:
        logger.error(
            "Migration safety violation: telemetry was implicitly enabled during migration"
        )
        return False

    return True


__all__ = [
    "PrivacyAssertionResult",
    "assert_offline_runtime",
    "log_privacy_startup_status",
    "verify_migration_telemetry_safety",
    "verify_privacy_defaults",
]
