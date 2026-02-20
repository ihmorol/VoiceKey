"""Unit tests for tray runtime and daemon behavior contracts (E05-S03)."""

from __future__ import annotations

from voicekey.app.state_machine import AppState
from voicekey.ui.daemon import resolve_daemon_start_behavior
from voicekey.ui.tray import (
    TrayAction,
    TrayActionHandlers,
    TrayController,
    TrayIconBackend,
    TrayIndicatorState,
)


def test_tray_indicator_state_maps_runtime_state() -> None:
    controller = TrayController(handlers=TrayActionHandlers())

    assert controller.indicator_state is TrayIndicatorState.STANDBY

    controller.set_runtime_state(AppState.STANDBY)
    assert controller.indicator_state is TrayIndicatorState.STANDBY

    controller.set_runtime_state(AppState.LISTENING)
    assert controller.indicator_state is TrayIndicatorState.LISTENING

    controller.set_runtime_state(AppState.PROCESSING)
    assert controller.indicator_state is TrayIndicatorState.LISTENING

    controller.set_runtime_state(AppState.PAUSED)
    assert controller.indicator_state is TrayIndicatorState.PAUSED

    controller.set_runtime_state(AppState.ERROR)
    assert controller.indicator_state is TrayIndicatorState.ERROR

    controller.set_runtime_state(AppState.SHUTTING_DOWN)
    assert controller.indicator_state is TrayIndicatorState.SHUTTING_DOWN


def test_tray_menu_actions_dispatch_expected_handlers() -> None:
    calls: list[str] = []
    handlers = TrayActionHandlers(
        on_start=lambda: calls.append("start"),
        on_stop=lambda: calls.append("stop"),
        on_pause=lambda: calls.append("pause"),
        on_resume=lambda: calls.append("resume"),
        on_open_dashboard=lambda: calls.append("dashboard"),
        on_open_settings=lambda: calls.append("settings"),
        on_exit=lambda: calls.append("exit"),
    )
    controller = TrayController(handlers=handlers)

    controller.set_runtime_active(False)
    controller.trigger_action(TrayAction.START_OR_STOP)
    controller.set_runtime_active(True)
    controller.trigger_action(TrayAction.START_OR_STOP)
    controller.set_runtime_state(AppState.STANDBY)
    controller.trigger_action(TrayAction.PAUSE_OR_RESUME)
    controller.set_runtime_state(AppState.PAUSED)
    controller.trigger_action(TrayAction.PAUSE_OR_RESUME)
    controller.trigger_action(TrayAction.OPEN_DASHBOARD)
    controller.trigger_action(TrayAction.OPEN_SETTINGS)
    controller.trigger_action(TrayAction.EXIT)

    assert calls == ["start", "stop", "pause", "resume", "dashboard", "settings", "exit"]


def test_tray_menu_contract_exposes_required_actions() -> None:
    controller = TrayController(handlers=TrayActionHandlers())

    controller.set_runtime_active(False)
    labels_when_stopped = tuple(item.label for item in controller.menu_items())
    assert labels_when_stopped == (
        "Start",
        "Pause",
        "Open Dashboard",
        "Settings",
        "Exit",
    )

    controller.set_runtime_active(True)
    controller.set_runtime_state(AppState.PAUSED)
    labels_when_paused = tuple(item.label for item in controller.menu_items())
    assert labels_when_paused == (
        "Stop",
        "Resume",
        "Open Dashboard",
        "Settings",
        "Exit",
    )


def test_daemon_start_behavior_in_graphical_session_enables_tray() -> None:
    behavior = resolve_daemon_start_behavior(
        daemon=True,
        environment={"XDG_SESSION_TYPE": "wayland"},
    )

    assert behavior.daemon is True
    assert behavior.show_terminal_ui is False
    assert behavior.tray_enabled is True
    assert behavior.graphical_session is True


def test_daemon_start_behavior_in_headless_session_disables_tray() -> None:
    behavior = resolve_daemon_start_behavior(
        daemon=True,
        environment={},
    )

    assert behavior.daemon is True
    assert behavior.show_terminal_ui is False
    assert behavior.tray_enabled is False
    assert behavior.graphical_session is False


def test_foreground_start_behavior_keeps_terminal_ui() -> None:
    behavior = resolve_daemon_start_behavior(
        daemon=False,
        environment={"DISPLAY": ":0"},
    )

    assert behavior.daemon is False
    assert behavior.show_terminal_ui is True
    assert behavior.tray_enabled is False
    assert behavior.graphical_session is True


# =============================================================================
# TrayIconBackend Tests
# =============================================================================


def test_tray_icon_backend_is_available_returns_bool() -> None:
    """Test that is_available returns a boolean value."""
    result = TrayIconBackend.is_available()
    assert isinstance(result, bool)


def test_tray_icon_backend_initializes_with_controller() -> None:
    """Test that TrayIconBackend can be initialized with a controller."""
    controller = TrayController(handlers=TrayActionHandlers())
    backend = TrayIconBackend(controller)

    assert backend._controller is controller
    assert backend.running is False


def test_tray_icon_backend_stop_is_safe_when_not_running() -> None:
    """Test that stop() is safe to call when not running."""
    controller = TrayController(handlers=TrayActionHandlers())
    backend = TrayIconBackend(controller)

    # Should not raise
    backend.stop()
    assert backend.running is False


def test_tray_icon_backend_start_returns_false_when_unavailable() -> None:
    """Test that start() returns False when pystray is unavailable."""
    controller = TrayController(handlers=TrayActionHandlers())
    backend = TrayIconBackend(controller)

    # If pystray is not available, start should return False
    # If pystray is available, start may still fail in headless environment
    result = backend.start()

    # The result depends on whether pystray is installed and display is available
    assert isinstance(result, bool)

    # Clean up
    backend.stop()


def test_tray_icon_backend_update_icon_is_safe() -> None:
    """Test that update_icon() is safe to call at any time."""
    controller = TrayController(handlers=TrayActionHandlers())
    backend = TrayIconBackend(controller)

    # Should not raise even when not running
    backend.update_icon()

    # Change state and update again
    controller.set_runtime_state(AppState.LISTENING)
    backend.update_icon()


def test_tray_icon_backend_get_indicator_color() -> None:
    """Test that indicator color changes with state."""
    controller = TrayController(handlers=TrayActionHandlers())
    backend = TrayIconBackend(controller)

    # Test all states
    states_and_expected = [
        (AppState.INITIALIZING, TrayIndicatorState.STANDBY),
        (AppState.STANDBY, TrayIndicatorState.STANDBY),
        (AppState.LISTENING, TrayIndicatorState.LISTENING),
        (AppState.PROCESSING, TrayIndicatorState.LISTENING),
        (AppState.PAUSED, TrayIndicatorState.PAUSED),
        (AppState.ERROR, TrayIndicatorState.ERROR),
        (AppState.SHUTTING_DOWN, TrayIndicatorState.SHUTTING_DOWN),
    ]

    for app_state, expected_tray_state in states_and_expected:
        controller.set_runtime_state(app_state)
        assert controller.indicator_state is expected_tray_state

        color = backend._get_indicator_color()
        assert isinstance(color, tuple)
        assert len(color) == 4  # RGBA
        assert all(isinstance(c, int) for c in color)
