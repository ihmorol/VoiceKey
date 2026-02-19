"""Wake phrase detection and wake-window timing controls.

Implements E02-S01 requirements:
- configurable wake phrase (default: "voice key")
- detector emits wake events only (no typing behavior)
- wake listening window timeout (default: 5s)
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass(frozen=True)
class WakeMatchResult:
    """Result of wake phrase matching."""

    matched: bool
    normalized_transcript: str


class WakePhraseDetector:
    """Detects wake phrase occurrences in transcript text.

    The detector only emits a wake match signal. It does not emit any typed
    text and does not execute commands directly.
    """

    def __init__(self, wake_phrase: str = "voice key") -> None:
        normalized = self._normalize(wake_phrase)
        if not normalized:
            raise ValueError("wake_phrase must not be empty")
        self._wake_phrase = normalized

    @property
    def wake_phrase(self) -> str:
        """Configured normalized wake phrase."""
        return self._wake_phrase

    def detect(self, transcript: str) -> WakeMatchResult:
        """Return wake match result for transcript text."""
        normalized = self._normalize(transcript)
        if not normalized:
            return WakeMatchResult(matched=False, normalized_transcript="")

        matched = self._wake_phrase in normalized
        return WakeMatchResult(matched=matched, normalized_transcript=normalized)

    @staticmethod
    def _normalize(text: str) -> str:
        return " ".join(text.strip().lower().split())


class WakeWindowController:
    """Controls wake listening window lifetime and timeout.

    The wake window can be opened on wake detection and expires after the
    configured timeout unless activity resets the timer.
    """

    def __init__(
        self,
        timeout_seconds: float = 5.0,
        time_provider: Callable[[], float] = time.monotonic,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be > 0")

        self._timeout_seconds = timeout_seconds
        self._time_provider = time_provider
        self._opened_at: Optional[float] = None
        self._last_activity_at: Optional[float] = None

    @property
    def timeout_seconds(self) -> float:
        """Configured wake window timeout in seconds."""
        return self._timeout_seconds

    def open_window(self) -> None:
        """Open listening window and start timeout countdown."""
        now = self._time_provider()
        self._opened_at = now
        self._last_activity_at = now

    def close_window(self) -> None:
        """Close listening window."""
        self._opened_at = None
        self._last_activity_at = None

    def on_activity(self) -> None:
        """Reset timeout due to transcript/VAD activity."""
        if self._opened_at is None:
            return
        self._last_activity_at = self._time_provider()

    def is_open(self) -> bool:
        """Check whether wake listening window is currently open."""
        if self._opened_at is None or self._last_activity_at is None:
            return False
        return not self._is_expired()

    def remaining_seconds(self) -> float:
        """Return remaining open-window duration in seconds."""
        if self._opened_at is None or self._last_activity_at is None:
            return 0.0
        elapsed = self._time_provider() - self._last_activity_at
        return max(0.0, self._timeout_seconds - elapsed)

    def poll_timeout(self) -> bool:
        """Close and report timeout expiry when window is expired."""
        if self._opened_at is None:
            return False
        if not self._is_expired():
            return False
        self.close_window()
        return True

    def _is_expired(self) -> bool:
        assert self._last_activity_at is not None
        return (self._time_provider() - self._last_activity_at) >= self._timeout_seconds
