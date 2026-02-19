"""Unit tests for deterministic terminal dashboard (E05-S02)."""

from __future__ import annotations

from voicekey.app.state_machine import AppState
from voicekey.ui.dashboard import DashboardController, DashboardRenderer, DashboardSnapshot


class FakeClock:
    """Deterministic monotonic clock for refresh throttling tests."""

    def __init__(self) -> None:
        self._now = 10.0

    def now(self) -> float:
        return self._now

    def tick(self, seconds: float) -> None:
        self._now += seconds


def test_dashboard_renders_state_latency_and_last_action() -> None:
    renderer = DashboardRenderer()

    frame = renderer.render(
        DashboardSnapshot(
            state=AppState.STANDBY,
            latency_ms=118.37,
            last_action="wake phrase timeout",
        )
    )

    assert "State: STANDBY" in frame
    assert "Latency: 118.4 ms" in frame
    assert "Last action: wake phrase timeout" in frame


def test_listening_indicator_is_always_clear() -> None:
    renderer = DashboardRenderer()

    frame = renderer.render(
        DashboardSnapshot(
            state=AppState.LISTENING,
            latency_ms=82.0,
            last_action="wake phrase detected",
        )
    )

    assert "Indicator: LISTENING - microphone active" in frame


def test_paused_indicator_is_always_clear() -> None:
    renderer = DashboardRenderer()

    frame = renderer.render(
        DashboardSnapshot(
            state=AppState.PAUSED,
            latency_ms=None,
            last_action="pause voice key",
        )
    )

    assert "Indicator: PAUSED - dictation disabled" in frame


def test_controller_throttles_refresh_and_keeps_latest_pending_snapshot() -> None:
    clock = FakeClock()
    controller = DashboardController(refresh_interval_seconds=0.5, clock=clock.now)

    controller.update(DashboardSnapshot(AppState.STANDBY, 120.0, "startup complete"))
    first = controller.poll_render()

    assert first is not None
    assert "Last action: startup complete" in first

    controller.update(DashboardSnapshot(AppState.LISTENING, 85.0, "wake phrase detected"))
    assert controller.poll_render() is None

    controller.update(DashboardSnapshot(AppState.PAUSED, 90.0, "pause voice key"))
    clock.tick(0.5)
    second = controller.poll_render()

    assert second is not None
    assert "Last action: pause voice key" in second
    assert "wake phrase detected" not in second
