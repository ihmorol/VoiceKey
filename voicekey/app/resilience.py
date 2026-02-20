"""Retry and safety fallback helpers for runtime resilience."""

from __future__ import annotations

from dataclasses import dataclass

from voicekey.app.runtime_errors import RuntimeErrorCode, runtime_error_info
from voicekey.app.state_machine import AppEvent, AppState


@dataclass(frozen=True)
class RetryPolicy:
    """Deterministic bounded retry policy with fixed backoff schedule."""

    max_attempts: int
    backoff_seconds: tuple[float, ...]

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        if not self.backoff_seconds:
            raise ValueError("backoff_seconds must include at least one value")
        if any(value <= 0.0 for value in self.backoff_seconds):
            raise ValueError("backoff_seconds values must be > 0")

    def next_delay_after_failure(self, failure_count: int) -> float | None:
        """Return next retry delay after N consecutive failures.

        Args:
            failure_count: Number of consecutive failures observed so far (1-based).

        Returns:
            Delay in seconds for the next retry, or None if retry budget is exhausted.
        """
        if failure_count < 1:
            raise ValueError("failure_count must be >= 1")
        if failure_count > self.max_attempts:
            return None

        backoff_index = min(failure_count - 1, len(self.backoff_seconds) - 1)
        return self.backoff_seconds[backoff_index]


MICROPHONE_RECONNECT_RETRY_POLICY = RetryPolicy(
    max_attempts=3,
    backoff_seconds=(1.0, 2.0, 4.0),
)


@dataclass(frozen=True)
class SafetyFallbackDecision:
    """Decision for whether runtime error handling should force paused mode."""

    force_pause: bool
    pause_event: AppEvent | None
    reason: str


def decide_safety_fallback(
    code: RuntimeErrorCode,
    state: AppState,
    retries_exhausted: bool = False,
) -> SafetyFallbackDecision:
    """Decide when to force PAUSED if runtime safety guarantees are degraded."""
    if code is RuntimeErrorCode.MICROPHONE_DISCONNECTED and not retries_exhausted:
        return SafetyFallbackDecision(
            force_pause=False,
            pause_event=None,
            reason="recoverable_audio_error_retrying",
        )

    info = runtime_error_info(code)
    should_pause = info.safety_critical or (
        code is RuntimeErrorCode.MICROPHONE_DISCONNECTED and retries_exhausted
    )
    if not should_pause:
        return SafetyFallbackDecision(
            force_pause=False,
            pause_event=None,
            reason="no_forced_pause_required",
        )

    return SafetyFallbackDecision(
        force_pause=True,
        pause_event=_pause_event_for_state(state),
        reason="safety_not_guaranteed_force_pause",
    )


def _pause_event_for_state(state: AppState) -> AppEvent | None:
    if state == AppState.STANDBY:
        return AppEvent.PAUSE_REQUESTED
    if state == AppState.LISTENING:
        return AppEvent.INACTIVITY_AUTO_PAUSE
    return None


__all__ = [
    "MICROPHONE_RECONNECT_RETRY_POLICY",
    "RetryPolicy",
    "SafetyFallbackDecision",
    "decide_safety_fallback",
]
