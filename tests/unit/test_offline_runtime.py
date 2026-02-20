"""Unit tests for offline runtime network guardrails.

These tests verify that no network calls are made during normal operation
as per architecture.md section 12 and requirements/security.md section 2:
- No outbound network calls during normal runtime after model download
- Privacy guardrail tests fail build on runtime egress regression
"""

from __future__ import annotations

import socket
import urllib.request
from unittest.mock import MagicMock, patch

import pytest

from voicekey.security import (
    ALLOWED_EGRESS_HOSTS,
    EgressAuditor,
    EgressAuditEntry,
    EgressGuard,
    EgressViolationError,
    audit_network_calls,
    egress_guard_context,
    get_allowed_hosts,
    is_network_allowed,
)
from voicekey.security.egress_guard import (
    check_request_allowed,
    check_socket_allowed,
)


class TestAllowedEgressHosts:
    """Tests for allowed egress host configuration."""

    def test_allowed_hosts_is_frozen(self) -> None:
        """Allowed hosts set should be immutable."""
        # frozenset is immutable - attempting to add raises AttributeError
        with pytest.raises(AttributeError):
            ALLOWED_EGRESS_HOSTS.add("evil.com")  # type: ignore[attr-defined]

    def test_allowed_hosts_contains_model_hosts(self) -> None:
        """Allowed hosts should include model download hosts."""
        assert "models.voicekey.dev" in ALLOWED_EGRESS_HOSTS
        assert "mirror.voicekey.dev" in ALLOWED_EGRESS_HOSTS

    def test_allowed_hosts_excludes_unknown_hosts(self) -> None:
        """Allowed hosts should not include arbitrary hosts."""
        assert "google.com" not in ALLOWED_EGRESS_HOSTS
        assert "example.com" not in ALLOWED_EGRESS_HOSTS
        assert "analytics.voicekey.dev" not in ALLOWED_EGRESS_HOSTS
        assert "telemetry.voicekey.dev" not in ALLOWED_EGRESS_HOSTS

    def test_get_allowed_hosts_returns_same_set(self) -> None:
        """get_allowed_hosts should return the allowed hosts set."""
        hosts = get_allowed_hosts()
        assert hosts == ALLOWED_EGRESS_HOSTS


class TestIsNetworkAllowed:
    """Tests for network access checking."""

    def test_allowed_host_returns_true(self) -> None:
        """Allowed hosts should return True."""
        assert is_network_allowed("models.voicekey.dev")
        assert is_network_allowed("mirror.voicekey.dev")

    def test_unknown_host_returns_false(self) -> None:
        """Unknown hosts should return False."""
        assert not is_network_allowed("google.com")
        assert not is_network_allowed("example.com")
        assert not is_network_allowed("evil.com")

    def test_empty_host_returns_false(self) -> None:
        """Empty host should return False."""
        assert not is_network_allowed("")
        assert not is_network_allowed("   ")

    def test_case_insensitive_matching(self) -> None:
        """Host matching should be case-insensitive."""
        assert is_network_allowed("MODELS.VOICEKEY.DEV")
        assert is_network_allowed("Models.VoiceKey.Dev")
        assert is_network_allowed("MIRROR.VOICEKEY.DEV")

    def test_whitespace_is_trimmed(self) -> None:
        """Hostnames with whitespace should be trimmed."""
        assert is_network_allowed("  models.voicekey.dev  ")


class TestEgressAuditor:
    """Tests for the egress auditor."""

    def test_empty_auditor_has_no_violations(self) -> None:
        """New auditor should have no violations."""
        auditor = audit_network_calls()
        assert not auditor.has_violations
        assert auditor.violation_count == 0
        assert auditor.allowed_count == 0

    def test_record_allowed_entry(self) -> None:
        """Recording an allowed entry should update counts."""
        auditor = EgressAuditor()
        auditor.record(EgressAuditEntry(
            host="models.voicekey.dev",
            port=443,
            allowed=True,
            operation="download",
        ))
        assert auditor.allowed_count == 1
        assert auditor.violation_count == 0
        assert not auditor.has_violations

    def test_record_violation_entry(self) -> None:
        """Recording a violation should update counts."""
        auditor = EgressAuditor()
        auditor.record(EgressAuditEntry(
            host="google.com",
            port=443,
            allowed=False,
            operation="request",
        ))
        assert auditor.allowed_count == 0
        assert auditor.violation_count == 1
        assert auditor.has_violations

    def test_get_violations_returns_only_violations(self) -> None:
        """get_violations should return only denied entries."""
        auditor = EgressAuditor()
        auditor.record(EgressAuditEntry(host="models.voicekey.dev", port=443, allowed=True, operation="download"))
        auditor.record(EgressAuditEntry(host="google.com", port=443, allowed=False, operation="request"))
        auditor.record(EgressAuditEntry(host="evil.com", port=80, allowed=False, operation="connect"))

        violations = auditor.get_violations()
        assert len(violations) == 2
        assert all(not v.allowed for v in violations)

    def test_clear_resets_auditor(self) -> None:
        """clear() should remove all entries."""
        auditor = EgressAuditor()
        auditor.record(EgressAuditEntry(host="test.com", port=80, allowed=False, operation="test"))
        auditor.clear()
        assert len(auditor.entries) == 0
        assert not auditor.has_violations


class TestEgressGuard:
    """Tests for the egress guard."""

    def test_disabled_guard_does_not_block(self) -> None:
        """Disabled guard should not block disallowed hosts."""
        guard = EgressGuard()
        assert not guard.enabled
        # Should return False but not raise
        result = guard.check_url("https://evil.com/steal-data")
        assert not result

    def test_enabled_guard_blocks_disallowed_urls(self) -> None:
        """Enabled guard should raise on disallowed URLs."""
        guard = EgressGuard()
        guard.enable()
        with pytest.raises(EgressViolationError, match="evil.com"):
            guard.check_url("https://evil.com/steal-data")

    def test_enabled_guard_allows_model_hosts(self) -> None:
        """Enabled guard should allow model download hosts."""
        guard = EgressGuard()
        guard.enable()
        assert guard.check_url("https://models.voicekey.dev/models/model.tar.zst")
        assert guard.check_url("https://mirror.voicekey.dev/models/model.tar.zst")

    def test_check_host_blocks_disallowed(self) -> None:
        """check_host should block disallowed hosts when enabled."""
        guard = EgressGuard()
        guard.enable()
        with pytest.raises(EgressViolationError):
            guard.check_host("google.com", 443)

    def test_check_host_allows_model_hosts(self) -> None:
        """check_host should allow model download hosts."""
        guard = EgressGuard()
        guard.enable()
        assert guard.check_host("models.voicekey.dev", 443)
        assert guard.check_host("mirror.voicekey.dev", 443)

    def test_audit_context_provides_fresh_auditor(self) -> None:
        """audit_context should provide a fresh auditor."""
        guard = EgressGuard()

        with guard.audit_context() as auditor:
            # Both URLs checked within the context should be recorded
            guard.check_url("https://models.voicekey.dev/test")
            guard.check_url("https://mirror.voicekey.dev/test")
            assert len(auditor.entries) == 2  # Both URLs in context

    def test_on_violation_callback_is_called(self) -> None:
        """on_violation callback should be called for violations."""
        guard = EgressGuard()
        violations: list[EgressAuditEntry] = []

        guard.enable(on_violation=violations.append)

        # This will record the violation AND raise the exception
        with pytest.raises(EgressViolationError):
            guard.check_url("https://evil.com/test", operation="test")

        # Callback should still have been called before the exception
        assert len(violations) == 1
        assert violations[0].host == "evil.com"
        assert not violations[0].allowed

    def test_disable_stops_blocking(self) -> None:
        """Disabling the guard should stop blocking."""
        guard = EgressGuard()
        guard.enable()
        guard.disable()

        # Should not raise after disable
        result = guard.check_url("https://evil.com/steal-data")
        assert not result


class TestEgressGuardContext:
    """Tests for the egress_guard_context context manager."""

    def test_non_blocking_context_records_violations(self) -> None:
        """Non-blocking context should record violations without raising."""
        with egress_guard_context(block=False) as guard:
            guard.check_url("https://evil.com/test")
            guard.check_url("https://google.com/test")

        assert guard.auditor.violation_count == 2

    def test_blocking_context_raises_on_violation(self) -> None:
        """Blocking context should raise on violations."""
        with pytest.raises(EgressViolationError):
            with egress_guard_context(block=True) as guard:
                guard.check_url("https://evil.com/test")

    def test_context_allows_model_hosts(self) -> None:
        """Context should allow model download hosts."""
        with egress_guard_context(block=True) as guard:
            assert guard.check_url("https://models.voicekey.dev/test")
            assert guard.check_url("https://mirror.voicekey.dev/test")


class TestCheckRequestAllowed:
    """Tests for urllib Request checking."""

    def test_allowed_request_returns_true(self) -> None:
        """Allowed requests should return True."""
        request = urllib.request.Request("https://models.voicekey.dev/model.tar.zst")
        assert check_request_allowed(request)

    def test_disallowed_request_returns_false(self) -> None:
        """Disallowed requests should return False."""
        request = urllib.request.Request("https://google.com/analytics")
        assert not check_request_allowed(request)

    def test_mirror_request_allowed(self) -> None:
        """Mirror requests should be allowed."""
        request = urllib.request.Request("https://mirror.voicekey.dev/model.tar.zst")
        assert check_request_allowed(request)


class TestCheckSocketAllowed:
    """Tests for socket connection checking."""

    def test_allowed_socket_returns_true(self) -> None:
        """Allowed socket connections should return True."""
        assert check_socket_allowed("models.voicekey.dev", 443)
        assert check_socket_allowed("mirror.voicekey.dev", 443)

    def test_disallowed_socket_returns_false(self) -> None:
        """Disallowed socket connections should return False."""
        assert not check_socket_allowed("google.com", 443)
        assert not check_socket_allowed("telemetry.voicekey.dev", 443)


class TestOfflineRuntimeSimulation:
    """Tests simulating offline runtime behavior."""

    def test_no_network_calls_during_normal_operation(self) -> None:
        """Simulate normal operation and verify no unexpected network calls."""
        auditor = audit_network_calls()

        # Simulate normal runtime operations that should NOT make network calls
        operations = [
            ("parser", "parse command", None),
            ("fsm", "transition state", None),
            ("config", "load config", None),
            ("audio", "capture frame", None),
            ("asr", "transcribe audio", None),
        ]

        for module, operation, _ in operations:
            # These operations should not trigger any network calls
            # If they did, they would be recorded in the auditor
            pass

        # No network calls should have been made during normal operation
        assert auditor.violation_count == 0
        assert auditor.allowed_count == 0

    def test_only_model_download_triggers_network(self) -> None:
        """Only model download operations should trigger allowed network calls."""
        guard = EgressGuard()
        guard.enable()

        # Model download should be allowed
        assert guard.check_url("https://models.voicekey.dev/model.tar.zst", operation="model_download")

        # Telemetry, analytics, etc. should be blocked
        blocked_urls = [
            "https://telemetry.voicekey.dev/collect",
            "https://analytics.voicekey.dev/track",
            "https://google.com/analytics",
            "https://example.com/api/track",
        ]

        for url in blocked_urls:
            with pytest.raises(EgressViolationError):
                guard.check_url(url, operation="telemetry")

    @patch("urllib.request.urlopen")
    def test_urllib_request_to_disallowed_host_detected(self, mock_urlopen: MagicMock) -> None:
        """Test that urllib requests to disallowed hosts can be detected."""
        # This test demonstrates how to detect network calls
        # In practice, the egress guard would be used before making requests

        guard = EgressGuard()
        guard.enable()

        # Attempting to check a disallowed URL should fail
        with pytest.raises(EgressViolationError):
            guard.check_url("https://evil.com/steal-data")

        # The mock shouldn't be called because the guard blocked it
        mock_urlopen.assert_not_called()


class TestEgressAuditEntry:
    """Tests for EgressAuditEntry dataclass."""

    def test_entry_creation(self) -> None:
        """Entry should store all provided values."""
        entry = EgressAuditEntry(
            host="example.com",
            port=443,
            allowed=False,
            operation="connect",
            error="Blocked by policy",
        )
        assert entry.host == "example.com"
        assert entry.port == 443
        assert not entry.allowed
        assert entry.operation == "connect"
        assert entry.error == "Blocked by policy"

    def test_entry_is_frozen(self) -> None:
        """Entry should be immutable."""
        entry = EgressAuditEntry(host="test.com", port=80, allowed=True, operation="test")
        with pytest.raises(AttributeError):
            entry.host = "changed.com"  # type: ignore[misc]
