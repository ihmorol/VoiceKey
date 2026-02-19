"""Deterministic tray runtime controller and action contracts."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

from voicekey.app.state_machine import AppState


class TrayIndicatorState(StrEnum):
    """Tray icon indicator states from runtime lifecycle."""

    STANDBY = "standby"
    LISTENING = "listening"
    PAUSED = "paused"
    ERROR = "error"
    SHUTTING_DOWN = "shutting_down"


class TrayAction(StrEnum):
    """Supported tray menu actions."""

    START_OR_STOP = "start_or_stop"
    PAUSE_OR_RESUME = "pause_or_resume"
    OPEN_DASHBOARD = "open_dashboard"
    OPEN_SETTINGS = "open_settings"
    EXIT = "exit"


@dataclass(frozen=True)
class TrayMenuItem:
    """Single tray menu item contract."""

    action: TrayAction
    label: str
    enabled: bool = True


@dataclass(frozen=True)
class TrayActionHandlers:
    """Callback contracts for tray menu actions."""

    on_start: Callable[[], None] | None = None
    on_stop: Callable[[], None] | None = None
    on_pause: Callable[[], None] | None = None
    on_resume: Callable[[], None] | None = None
    on_open_dashboard: Callable[[], None] | None = None
    on_open_settings: Callable[[], None] | None = None
    on_exit: Callable[[], None] | None = None


_APP_STATE_TO_TRAY_STATE: dict[AppState, TrayIndicatorState] = {
    AppState.INITIALIZING: TrayIndicatorState.STANDBY,
    AppState.STANDBY: TrayIndicatorState.STANDBY,
    AppState.LISTENING: TrayIndicatorState.LISTENING,
    AppState.PROCESSING: TrayIndicatorState.LISTENING,
    AppState.PAUSED: TrayIndicatorState.PAUSED,
    AppState.SHUTTING_DOWN: TrayIndicatorState.SHUTTING_DOWN,
    AppState.ERROR: TrayIndicatorState.ERROR,
}


class TrayController:
    """Deterministic tray controller independent from pystray runtime."""

    def __init__(
        self,
        handlers: TrayActionHandlers,
        initial_runtime_state: AppState = AppState.INITIALIZING,
        runtime_active: bool = True,
    ) -> None:
        self._handlers = handlers
        self._runtime_state = initial_runtime_state
        self._runtime_active = runtime_active

    @property
    def runtime_state(self) -> AppState:
        """Current runtime state used by tray indicator/menu."""
        return self._runtime_state

    @property
    def runtime_active(self) -> bool:
        """Whether runtime is active for start/stop menu toggle."""
        return self._runtime_active

    @property
    def indicator_state(self) -> TrayIndicatorState:
        """Current tray indicator state mapped from runtime state."""
        return _APP_STATE_TO_TRAY_STATE[self._runtime_state]

    def set_runtime_state(self, state: AppState) -> None:
        """Update runtime state reflected by tray indicator/menu labels."""
        self._runtime_state = state

    def set_runtime_active(self, active: bool) -> None:
        """Update runtime active flag reflected by start/stop action."""
        self._runtime_active = active

    def menu_items(self) -> tuple[TrayMenuItem, ...]:
        """Return deterministic tray menu model for UI adapters."""
        start_stop_label = "Stop" if self._runtime_active else "Start"
        pause_resume_label = "Resume" if self._runtime_state is AppState.PAUSED else "Pause"
        return (
            TrayMenuItem(action=TrayAction.START_OR_STOP, label=start_stop_label),
            TrayMenuItem(action=TrayAction.PAUSE_OR_RESUME, label=pause_resume_label),
            TrayMenuItem(action=TrayAction.OPEN_DASHBOARD, label="Open Dashboard"),
            TrayMenuItem(action=TrayAction.OPEN_SETTINGS, label="Settings"),
            TrayMenuItem(action=TrayAction.EXIT, label="Exit"),
        )

    def trigger_action(self, action: TrayAction) -> None:
        """Dispatch a tray action to the configured handler contracts."""
        if action is TrayAction.START_OR_STOP:
            self._invoke_start_or_stop()
            return

        if action is TrayAction.PAUSE_OR_RESUME:
            self._invoke_pause_or_resume()
            return

        if action is TrayAction.OPEN_DASHBOARD:
            self._invoke(self._handlers.on_open_dashboard)
            return

        if action is TrayAction.OPEN_SETTINGS:
            self._invoke(self._handlers.on_open_settings)
            return

        if action is TrayAction.EXIT:
            self._invoke(self._handlers.on_exit)
            return

    def _invoke_start_or_stop(self) -> None:
        if self._runtime_active:
            self._invoke(self._handlers.on_stop)
            return
        self._invoke(self._handlers.on_start)

    def _invoke_pause_or_resume(self) -> None:
        if self._runtime_state is AppState.PAUSED:
            self._invoke(self._handlers.on_resume)
            return
        self._invoke(self._handlers.on_pause)

    @staticmethod
    def _invoke(handler: Callable[[], None] | None) -> None:
        if handler is None:
            return
        handler()


__all__ = [
    "TrayAction",
    "TrayActionHandlers",
    "TrayController",
    "TrayIndicatorState",
    "TrayMenuItem",
]
