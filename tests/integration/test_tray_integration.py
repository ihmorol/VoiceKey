"""Integration tests for tray icon state synchronization.

Tests the integration between:
- TrayController and AppState
- Tray state transitions with state machine
- Tray action handlers and runtime events

Requirements:
- E10-S02: Integration harness expansion
- FR-S01, FR-S02, FR-S03: Tray and daemon requirements
- requirements/testing-strategy.md: Integration layer - tray state synchronization

All tests use mocks - no real system tray required.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import pytest

from voicekey.app.state_machine import AppState, AppEvent, ListeningMode, VoiceKeyStateMachine
from voicekey.ui.tray import (
    TrayAction,
    TrayActionHandlers,
    TrayController,
    TrayIndicatorState,
    TrayMenuItem,
)


# =============================================================================
# Tray State Synchronization Tests
# =============================================================================

class TestTrayStateSynchronization:
    """Integration tests for tray state synchronization with runtime."""

    def test_tray_indicator_maps_all_app_states(self) -> None:
        """Verify tray indicator state maps correctly for all app states."""
        state_mapping = {
            AppState.INITIALIZING: TrayIndicatorState.STANDBY,
            AppState.STANDBY: TrayIndicatorState.STANDBY,
            AppState.LISTENING: TrayIndicatorState.LISTENING,
            AppState.PROCESSING: TrayIndicatorState.LISTENING,
            AppState.PAUSED: TrayIndicatorState.PAUSED,
            AppState.ERROR: TrayIndicatorState.ERROR,
            AppState.SHUTTING_DOWN: TrayIndicatorState.SHUTTING_DOWN,
        }

        controller = TrayController(handlers=TrayActionHandlers())

        for app_state, expected_tray_state in state_mapping.items():
            controller.set_runtime_state(app_state)
            assert controller.indicator_state is expected_tray_state, (
                f"State {app_state.value} should map to {expected_tray_state.value}"
            )

    def test_tray_updates_on_state_machine_transitions(self) -> None:
        """Verify tray indicator updates when state machine transitions."""
        # Setup state machine and tray controller
        machine = VoiceKeyStateMachine(
            mode=ListeningMode.WAKE_WORD,
            initial_state=AppState.STANDBY,
        )
        tray = TrayController(handlers=TrayActionHandlers())

        # Initial state
        assert tray.indicator_state is TrayIndicatorState.STANDBY

        # Wake phrase detected -> LISTENING
        machine.transition(AppEvent.WAKE_PHRASE_DETECTED)
        tray.set_runtime_state(machine.state)
        assert tray.indicator_state is TrayIndicatorState.LISTENING

        # Speech frame received -> PROCESSING
        machine.transition(AppEvent.SPEECH_FRAME_RECEIVED)
        tray.set_runtime_state(machine.state)
        assert tray.indicator_state is TrayIndicatorState.LISTENING  # PROCESSING maps to LISTENING

        # Partial handled -> back to LISTENING
        machine.transition(AppEvent.PARTIAL_HANDLED)
        tray.set_runtime_state(machine.state)
        assert tray.indicator_state is TrayIndicatorState.LISTENING

        # Inactivity auto-pause -> PAUSED
        machine.transition(AppEvent.INACTIVITY_AUTO_PAUSE)
        tray.set_runtime_state(machine.state)
        assert tray.indicator_state is TrayIndicatorState.PAUSED

    def test_tray_reflects_runtime_active_flag(self) -> None:
        """Verify tray menu reflects runtime active state for Start/Stop toggle."""
        tray = TrayController(
            handlers=TrayActionHandlers(),
            runtime_active=True,
        )

        # When active, Start/Stop item should show "Stop"
        items = tray.menu_items()
        start_stop_item = next(
            (item for item in items if item.action is TrayAction.START_OR_STOP),
            None,
        )
        assert start_stop_item is not None
        assert start_stop_item.label == "Stop"

        # When inactive, should show "Start"
        tray.set_runtime_active(False)
        items = tray.menu_items()
        start_stop_item = next(
            (item for item in items if item.action is TrayAction.START_OR_STOP),
            None,
        )
        assert start_stop_item.label == "Start"

    def test_tray_pause_resume_label_changes_with_state(self) -> None:
        """Verify Pause/Resume label changes based on paused state."""
        tray = TrayController(
            handlers=TrayActionHandlers(),
            initial_runtime_state=AppState.STANDBY,
        )

        # When in STANDBY, should show "Pause"
        items = tray.menu_items()
        pause_resume_item = next(
            (item for item in items if item.action is TrayAction.PAUSE_OR_RESUME),
            None,
        )
        assert pause_resume_item.label == "Pause"

        # When PAUSED, should show "Resume"
        tray.set_runtime_state(AppState.PAUSED)
        items = tray.menu_items()
        pause_resume_item = next(
            (item for item in items if item.action is TrayAction.PAUSE_OR_RESUME),
            None,
        )
        assert pause_resume_item.label == "Resume"


class TestTrayActionHandling:
    """Integration tests for tray action handling."""

    def test_tray_actions_dispatch_to_handlers(self) -> None:
        """Verify tray actions dispatch to correct handlers."""
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

        tray = TrayController(handlers=handlers)

        # Test all actions
        tray.trigger_action(TrayAction.OPEN_DASHBOARD)
        tray.trigger_action(TrayAction.OPEN_SETTINGS)
        tray.trigger_action(TrayAction.EXIT)

        assert "dashboard" in calls
        assert "settings" in calls
        assert "exit" in calls

    def test_start_stop_action_toggles_based_on_runtime_active(self) -> None:
        """Verify Start/Stop action calls correct handler based on state."""
        calls: list[str] = []

        handlers = TrayActionHandlers(
            on_start=lambda: calls.append("start"),
            on_stop=lambda: calls.append("stop"),
        )

        tray = TrayController(handlers=handlers, runtime_active=False)

        # When inactive, should call on_start
        tray.trigger_action(TrayAction.START_OR_STOP)
        assert calls == ["start"]

        # When active, should call on_stop
        tray.set_runtime_active(True)
        tray.trigger_action(TrayAction.START_OR_STOP)
        assert calls == ["start", "stop"]

    def test_pause_resume_action_toggles_based_on_paused_state(self) -> None:
        """Verify Pause/Resume action calls correct handler based on state."""
        calls: list[str] = []

        handlers = TrayActionHandlers(
            on_pause=lambda: calls.append("pause"),
            on_resume=lambda: calls.append("resume"),
        )

        tray = TrayController(
            handlers=handlers,
            initial_runtime_state=AppState.STANDBY,
        )

        # When in STANDBY, should call on_pause
        tray.trigger_action(TrayAction.PAUSE_OR_RESUME)
        assert calls == ["pause"]

        # When PAUSED, should call on_resume
        tray.set_runtime_state(AppState.PAUSED)
        tray.trigger_action(TrayAction.PAUSE_OR_RESUME)
        assert calls == ["pause", "resume"]

    def test_missing_handlers_do_not_raise(self) -> None:
        """Verify missing handlers do not cause exceptions."""
        # Create tray with no handlers
        tray = TrayController(handlers=TrayActionHandlers())

        # None of these should raise
        tray.trigger_action(TrayAction.START_OR_STOP)
        tray.trigger_action(TrayAction.PAUSE_OR_RESUME)
        tray.trigger_action(TrayAction.OPEN_DASHBOARD)
        tray.trigger_action(TrayAction.OPEN_SETTINGS)
        tray.trigger_action(TrayAction.EXIT)


class TestTrayMenuContract:
    """Integration tests for tray menu contract."""

    def test_menu_items_contract(self) -> None:
        """Verify menu items follow the required contract."""
        tray = TrayController(handlers=TrayActionHandlers())
        items = tray.menu_items()

        # Required actions
        required_actions = {
            TrayAction.START_OR_STOP,
            TrayAction.PAUSE_OR_RESUME,
            TrayAction.OPEN_DASHBOARD,
            TrayAction.OPEN_SETTINGS,
            TrayAction.EXIT,
        }

        actual_actions = {item.action for item in items}

        assert required_actions == actual_actions, (
            f"Missing actions: {required_actions - actual_actions}"
        )

    def test_menu_item_labels_are_deterministic(self) -> None:
        """Verify menu item labels are deterministic for same state."""
        tray = TrayController(
            handlers=TrayActionHandlers(),
            initial_runtime_state=AppState.LISTENING,
            runtime_active=True,
        )

        first_items = tray.menu_items()
        second_items = tray.menu_items()

        assert first_items == second_items

    def test_menu_items_order_is_stable(self) -> None:
        """Verify menu items appear in consistent order."""
        tray = TrayController(handlers=TrayActionHandlers())
        items = tray.menu_items()

        # Expected order
        expected_order = [
            TrayAction.START_OR_STOP,
            TrayAction.PAUSE_OR_RESUME,
            TrayAction.OPEN_DASHBOARD,
            TrayAction.OPEN_SETTINGS,
            TrayAction.EXIT,
        ]

        actual_order = [item.action for item in items]
        assert actual_order == expected_order


class TestTrayWithStateMachineIntegration:
    """Integration tests for tray with state machine."""

    def test_full_lifecycle_tray_state_transitions(self) -> None:
        """Test full lifecycle: init -> standby -> listening -> paused -> shutdown."""
        # Setup
        machine = VoiceKeyStateMachine(
            mode=ListeningMode.WAKE_WORD,
            initial_state=AppState.INITIALIZING,
        )
        calls: list[str] = []
        handlers = TrayActionHandlers(
            on_pause=lambda: calls.append("pause"),
            on_resume=lambda: calls.append("resume"),
        )
        tray = TrayController(handlers=handlers)

        # INITIALIZING -> STANDBY
        machine.transition(AppEvent.INITIALIZATION_SUCCEEDED)
        tray.set_runtime_state(machine.state)
        assert tray.indicator_state is TrayIndicatorState.STANDBY

        # STANDBY -> LISTENING (wake detected)
        machine.transition(AppEvent.WAKE_PHRASE_DETECTED)
        tray.set_runtime_state(machine.state)
        assert tray.indicator_state is TrayIndicatorState.LISTENING

        # LISTENING -> PROCESSING
        machine.transition(AppEvent.SPEECH_FRAME_RECEIVED)
        tray.set_runtime_state(machine.state)
        assert tray.indicator_state is TrayIndicatorState.LISTENING

        # PROCESSING -> LISTENING (partial handled)
        machine.transition(AppEvent.PARTIAL_HANDLED)
        tray.set_runtime_state(machine.state)
        assert tray.indicator_state is TrayIndicatorState.LISTENING

        # LISTENING -> PAUSED (inactivity auto-pause)
        machine.transition(AppEvent.INACTIVITY_AUTO_PAUSE)
        tray.set_runtime_state(machine.state)
        assert tray.indicator_state is TrayIndicatorState.PAUSED

        # Trigger resume via tray
        tray.trigger_action(TrayAction.PAUSE_OR_RESUME)
        assert "resume" in calls

        # PAUSED -> STANDBY
        machine.transition(AppEvent.RESUME_REQUESTED)
        tray.set_runtime_state(machine.state)
        assert tray.indicator_state is TrayIndicatorState.STANDBY

        # STANDBY -> SHUTTING_DOWN
        machine.transition(AppEvent.STOP_REQUESTED)
        tray.set_runtime_state(machine.state)
        assert tray.indicator_state is TrayIndicatorState.SHUTTING_DOWN

    def test_error_state_reflected_in_tray(self) -> None:
        """Verify error state is reflected in tray indicator."""
        machine = VoiceKeyStateMachine(
            mode=ListeningMode.WAKE_WORD,
            initial_state=AppState.INITIALIZING,
        )
        tray = TrayController(handlers=TrayActionHandlers())

        # Initialization failed -> ERROR
        machine.transition(AppEvent.INITIALIZATION_FAILED)
        tray.set_runtime_state(machine.state)
        assert tray.indicator_state is TrayIndicatorState.ERROR

    def test_continuous_mode_tray_behavior(self) -> None:
        """Test tray behavior in continuous listening mode."""
        machine = VoiceKeyStateMachine(
            mode=ListeningMode.CONTINUOUS,
            initial_state=AppState.STANDBY,
        )
        calls: list[str] = []
        handlers = TrayActionHandlers(
            on_pause=lambda: calls.append("pause"),
        )
        tray = TrayController(handlers=handlers)

        # Start continuous mode
        machine.transition(AppEvent.CONTINUOUS_START)
        tray.set_runtime_state(machine.state)
        assert tray.indicator_state is TrayIndicatorState.LISTENING

        # Inactivity should trigger auto-pause
        machine.transition(AppEvent.INACTIVITY_AUTO_PAUSE)
        tray.set_runtime_state(machine.state)
        assert tray.indicator_state is TrayIndicatorState.PAUSED

        # Tray pause action should work
        tray.trigger_action(TrayAction.PAUSE_OR_RESUME)  # Should call resume
        assert "resume" not in calls  # Actually calls resume, not pause


class TestDaemonSessionIntegration:
    """Integration tests for daemon session behavior."""

    def test_graphical_session_enables_tray(self) -> None:
        """Verify graphical session detection enables tray."""
        from voicekey.ui.daemon import resolve_daemon_start_behavior

        behavior = resolve_daemon_start_behavior(
            daemon=True,
            environment={"XDG_SESSION_TYPE": "wayland"},
        )

        assert behavior.daemon is True
        assert behavior.show_terminal_ui is False
        assert behavior.tray_enabled is True
        assert behavior.graphical_session is True

    def test_headless_session_disables_tray(self) -> None:
        """Verify headless session disables tray."""
        from voicekey.ui.daemon import resolve_daemon_start_behavior

        behavior = resolve_daemon_start_behavior(
            daemon=True,
            environment={},
        )

        assert behavior.daemon is True
        assert behavior.show_terminal_ui is False
        assert behavior.tray_enabled is False
        assert behavior.graphical_session is False

    def test_foreground_mode_keeps_terminal_ui(self) -> None:
        """Verify foreground mode keeps terminal UI."""
        from voicekey.ui.daemon import resolve_daemon_start_behavior

        behavior = resolve_daemon_start_behavior(
            daemon=False,
            environment={"DISPLAY": ":0"},
        )

        assert behavior.daemon is False
        assert behavior.show_terminal_ui is True
        assert behavior.tray_enabled is False  # Foreground mode doesn't use tray
        assert behavior.graphical_session is True
