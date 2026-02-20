"""VoiceKey security and privacy guardrails."""

from voicekey.security.egress_guard import (
    ALLOWED_EGRESS_HOSTS,
    EgressAuditEntry,
    EgressAuditor,
    EgressGuard,
    EgressViolationError,
    audit_network_calls,
    egress_guard_context,
    get_allowed_hosts,
    is_network_allowed,
)
from voicekey.security.privacy_assertions import (
    PrivacyAssertionResult,
    assert_offline_runtime,
    log_privacy_startup_status,
    verify_migration_telemetry_safety,
    verify_privacy_defaults,
)

__all__ = [
    # Egress guard
    "ALLOWED_EGRESS_HOSTS",
    "EgressAuditEntry",
    "EgressAuditor",
    "EgressGuard",
    "EgressViolationError",
    "audit_network_calls",
    "egress_guard_context",
    "get_allowed_hosts",
    "is_network_allowed",
    # Privacy assertions
    "PrivacyAssertionResult",
    "assert_offline_runtime",
    "log_privacy_startup_status",
    "verify_migration_telemetry_safety",
    "verify_privacy_defaults",
]
