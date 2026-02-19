"""Deterministic terminal dashboard rendering and refresh control."""

from __future__ import annotations

from dataclasses import dataclass
from time import monotonic
from typing import Callable

from voicekey.app.state_machine import AppState


@dataclass(frozen=True)
class DashboardSnapshot:
    """Single dashboard frame payload bound to runtime state."""

    state: AppState
    latency_ms: float | None
    last_action: str


class DashboardRenderer:
    """Pure renderer that converts dashboard snapshots into terminal text."""

    _INDICATOR_BY_STATE: dict[AppState, str] = {
        AppState.INITIALIZING: "INITIALIZING - starting services",
        AppState.STANDBY: "STANDBY - waiting for wake phrase",
        AppState.LISTENING: "LISTENING - microphone active",
        AppState.PROCESSING: "PROCESSING - handling speech",
        AppState.PAUSED: "PAUSED - dictation disabled",
        AppState.SHUTTING_DOWN: "SHUTTING_DOWN - stopping services",
        AppState.ERROR: "ERROR - attention required",
    }

    def render(self, snapshot: DashboardSnapshot) -> str:
        """Render a deterministic dashboard frame from a runtime snapshot."""
        latency_text = "n/a" if snapshot.latency_ms is None else f"{snapshot.latency_ms:.1f} ms"
        indicator = self._INDICATOR_BY_STATE[snapshot.state]
        lines = [
            "VoiceKey Dashboard",
            f"State: {snapshot.state.value}",
            f"Indicator: {indicator}",
            f"Latency: {latency_text}",
            f"Last action: {snapshot.last_action}",
        ]
        return "\n".join(lines)


class DashboardController:
    """Throttles dashboard refreshes using latest-snapshot non-blocking updates."""

    def __init__(
        self,
        *,
        renderer: DashboardRenderer | None = None,
        refresh_interval_seconds: float = 0.2,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        if refresh_interval_seconds < 0:
            raise ValueError("refresh_interval_seconds must be >= 0")

        self._renderer = renderer or DashboardRenderer()
        self._refresh_interval_seconds = refresh_interval_seconds
        self._clock = clock
        self._pending_snapshot: DashboardSnapshot | None = None
        self._last_render_at: float | None = None

    def update(self, snapshot: DashboardSnapshot) -> None:
        """Queue the latest runtime snapshot without blocking caller progress."""
        self._pending_snapshot = snapshot

    def poll_render(self) -> str | None:
        """Render pending snapshot if throttle window allows, otherwise return None."""
        if self._pending_snapshot is None:
            return None

        now = self._clock()
        if self._last_render_at is not None:
            elapsed = now - self._last_render_at
            if elapsed < self._refresh_interval_seconds:
                return None

        snapshot = self._pending_snapshot
        self._pending_snapshot = None
        self._last_render_at = now
        return self._renderer.render(snapshot)


__all__ = ["DashboardController", "DashboardRenderer", "DashboardSnapshot"]
