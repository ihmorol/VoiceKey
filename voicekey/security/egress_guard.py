"""Runtime egress guard for preventing unexpected outbound network calls.

This module implements privacy guardrails per architecture.md section 12 and
requirements/security.md section 2:
- No outbound network calls during normal runtime after model download/install
- Only model download hosts are allowed for network access
- Telemetry is disabled by default and cannot be enabled implicitly
"""

from __future__ import annotations

import socket
import urllib.parse
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Iterator
from urllib.request import Request

# Allowed hosts for model downloads (from voicekey/models/catalog.py)
ALLOWED_EGRESS_HOSTS: frozenset[str] = frozenset({
    "models.voicekey.dev",
    "mirror.voicekey.dev",
})


class EgressViolationError(RuntimeError):
    """Raised when an unexpected outbound network call is attempted."""


@dataclass(frozen=True)
class EgressAuditEntry:
    """Record of a network access attempt."""

    host: str
    port: int | None
    allowed: bool
    operation: str
    error: str | None = None


@dataclass
class EgressAuditor:
    """Auditor that records all network access attempts."""

    entries: list[EgressAuditEntry] = field(default_factory=list)

    def record(self, entry: EgressAuditEntry) -> None:
        """Record a network access attempt."""
        self.entries.append(entry)

    @property
    def violation_count(self) -> int:
        """Count of denied network access attempts."""
        return sum(1 for e in self.entries if not e.allowed)

    @property
    def allowed_count(self) -> int:
        """Count of allowed network access attempts."""
        return sum(1 for e in self.entries if e.allowed)

    @property
    def has_violations(self) -> bool:
        """Whether any violations occurred."""
        return self.violation_count > 0

    def get_violations(self) -> list[EgressAuditEntry]:
        """Get all violation entries."""
        return [e for e in self.entries if not e.allowed]

    def clear(self) -> None:
        """Clear all recorded entries."""
        self.entries.clear()


def get_allowed_hosts() -> frozenset[str]:
    """Return the set of hosts allowed for outbound network access."""
    return ALLOWED_EGRESS_HOSTS


def is_network_allowed(host: str) -> bool:
    """Check if network access to the given host is allowed.

    Args:
        host: The hostname to check (without port).

    Returns:
        True if the host is in the allowed list, False otherwise.
    """
    normalized = host.lower().strip()
    if not normalized:
        return False
    return normalized in ALLOWED_EGRESS_HOSTS


@dataclass
class EgressGuard:
    """Runtime egress guard that can block/audit unexpected outbound connections.

    The guard tracks allowed network hosts (only model download hosts) and can
    be enabled to block or audit unexpected outbound connections.

    Usage:
        guard = EgressGuard()

        # Check before network operation
        if guard.is_allowed("models.voicekey.dev"):
            # proceed with download

        # Use context manager for auditing
        with guard.audit_context() as auditor:
            # perform operations
            pass
        if auditor.has_violations:
            # handle violations
            pass
    """

    _enabled: bool = False
    _auditor: EgressAuditor = field(default_factory=EgressAuditor)
    _on_violation: Callable[[EgressAuditEntry], None] | None = None

    @property
    def enabled(self) -> bool:
        """Whether the egress guard is actively blocking."""
        return self._enabled

    def enable(self, *, on_violation: Callable[[EgressAuditEntry], None] | None = None) -> None:
        """Enable the egress guard.

        Args:
            on_violation: Optional callback for handling violations.
                          If not provided, violations are only recorded.
        """
        self._enabled = True
        self._on_violation = on_violation

    def disable(self) -> None:
        """Disable the egress guard."""
        self._enabled = False
        self._on_violation = None

    def is_allowed(self, host: str) -> bool:
        """Check if network access to the given host is allowed."""
        return is_network_allowed(host)

    def check_url(self, url: str, *, operation: str = "request") -> bool:
        """Check if a URL is allowed for network access.

        Args:
            url: The URL to check.
            operation: Description of the operation being performed.

        Returns:
            True if the URL is allowed, False otherwise.

        Raises:
            EgressViolationError: If the guard is enabled and the URL is not allowed.
        """
        try:
            parsed = urllib.parse.urlparse(url)
            host = parsed.hostname or ""
        except Exception:
            host = ""

        allowed = self.is_allowed(host)
        entry = EgressAuditEntry(
            host=host,
            port=parsed.port if hasattr(parsed, "port") else None,
            allowed=allowed,
            operation=operation,
        )
        self._auditor.record(entry)

        if not allowed:
            if self._on_violation is not None:
                self._on_violation(entry)
            if self._enabled:
                raise EgressViolationError(
                    f"Network egress to '{host}' is not allowed. "
                    f"Allowed hosts: {', '.join(sorted(ALLOWED_EGRESS_HOSTS))}"
                )

        return allowed

    def check_host(self, host: str, port: int | None = None, *, operation: str = "connect") -> bool:
        """Check if connecting to a host:port is allowed.

        Args:
            host: The hostname to check.
            port: Optional port number.
            operation: Description of the operation.

        Returns:
            True if the connection is allowed, False otherwise.

        Raises:
            EgressViolationError: If the guard is enabled and the host is not allowed.
        """
        allowed = self.is_allowed(host)
        entry = EgressAuditEntry(
            host=host,
            port=port,
            allowed=allowed,
            operation=operation,
        )
        self._auditor.record(entry)

        if not allowed:
            if self._on_violation is not None:
                self._on_violation(entry)
            if self._enabled:
                raise EgressViolationError(
                    f"Network egress to '{host}:{port or '*'}' is not allowed. "
                    f"Allowed hosts: {', '.join(sorted(ALLOWED_EGRESS_HOSTS))}"
                )

        return allowed

    @contextmanager
    def audit_context(self) -> Iterator[EgressAuditor]:
        """Context manager that collects network access audit entries.

        Yields:
            An EgressAuditor that records entries during the context.
        """
        # Use a fresh auditor for this context
        context_auditor = EgressAuditor()
        previous_auditor = self._auditor
        self._auditor = context_auditor
        try:
            yield context_auditor
        finally:
            self._auditor = previous_auditor

    @property
    def auditor(self) -> EgressAuditor:
        """Get the current auditor."""
        return self._auditor

    def clear_audit(self) -> None:
        """Clear all audit entries."""
        self._auditor.clear()


@contextmanager
def egress_guard_context(*, block: bool = False) -> Iterator[EgressGuard]:
    """Context manager for egress guard operations.

    Args:
        block: If True, violations will raise EgressViolationError.
               If False, violations are only recorded.

    Yields:
        An EgressGuard instance.
    """
    guard = EgressGuard()
    if block:
        guard.enable()
    try:
        yield guard
    finally:
        guard.disable()


def audit_network_calls() -> EgressAuditor:
    """Create a fresh auditor for recording network calls.

    Returns:
        A new EgressAuditor instance.
    """
    return EgressAuditor()


def check_request_allowed(request: Request) -> bool:
    """Check if a urllib Request is allowed.

    Args:
        request: The urllib Request to check.

    Returns:
        True if the request is allowed, False otherwise.
    """
    try:
        host = request.host
    except AttributeError:
        # Fallback: parse full URL
        try:
            parsed = urllib.parse.urlparse(request.full_url)
            host = parsed.hostname or ""
        except Exception:
            return False

    return is_network_allowed(host)


def check_socket_allowed(host: str, port: int) -> bool:
    """Check if a socket connection is allowed.

    Args:
        host: The hostname.
        port: The port number.

    Returns:
        True if the connection is allowed, False otherwise.
    """
    return is_network_allowed(host)


__all__ = [
    "ALLOWED_EGRESS_HOSTS",
    "EgressAuditEntry",
    "EgressAuditor",
    "EgressGuard",
    "EgressViolationError",
    "audit_network_calls",
    "check_request_allowed",
    "check_socket_allowed",
    "egress_guard_context",
    "get_allowed_hosts",
    "is_network_allowed",
]
