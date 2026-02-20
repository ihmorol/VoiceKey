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


# Optional dependency - pystray for system tray icon
_pystray_available: bool = False
_Icon: Callable | None = None
_Menu: Callable | None = None
_Item: Callable | None = None

try:
    from pystray import Icon, Menu, MenuItem

    _pystray_available = True
except ImportError:
    pass


class TrayIconBackend:
    """System tray icon backend using pystray.

    Provides actual OS-level tray icon integration. Falls back gracefully
    when pystray is unavailable or in headless environments.
    """

    def __init__(
        self,
        controller: TrayController,
        app_name: str = "VoiceKey",
        icon_path: str | None = None,
    ) -> None:
        self._controller = controller
        self._app_name = app_name
        self._icon_path = icon_path
        self._icon: Icon | None = None
        self._running = False

    @classmethod
    def is_available(cls) -> bool:
        """Check if system tray integration is available."""
        if not _pystray_available:
            return False
        # Additional runtime checks could be added here
        # (e.g., checking for DISPLAY on Linux)
        return True

    def _create_icon(self) -> Icon | None:
        """Create a pystray Icon instance with menu items."""
        if not self.is_available():
            return None

        assert _Icon is not None
        assert _Menu is not None
        assert _Item is not None

        def on_start_stop() -> None:
            self._controller.trigger_action(TrayAction.START_OR_STOP)

        def on_pause_resume() -> None:
            self._controller.trigger_action(TrayAction.PAUSE_OR_RESUME)

        def on_open_dashboard() -> None:
            self._controller.trigger_action(TrayAction.OPEN_DASHBOARD)

        def on_open_settings() -> None:
            self._controller.trigger_action(TrayAction.OPEN_SETTINGS)

        def on_exit() -> None:
            self._controller.trigger_action(TrayAction.EXIT)
            self.stop()

        # Create menu items
        menu = _Menu(
            _Item(
                lambda: self._get_start_stop_label(),
                on_start_stop,
                default=True,
            ),
            _Item(
                lambda: self._get_pause_resume_label(),
                on_pause_resume,
            ),
            _Menu.SEPARATOR,
            _Item("Open Dashboard", on_open_dashboard),
            _Item("Settings", on_open_settings),
            _Menu.SEPARATOR,
            _Item("Exit", on_exit),
        )

        # Create icon with default image
        icon_image = self._create_icon_image()
        icon = _Icon(self._app_name, icon_image, self._app_name, menu)
        return icon

    def _create_icon_image(self):
        """Create an icon image for the tray."""
        if not _pystray_available:
            return None

        try:
            from PIL import Image, ImageDraw

            # Create a simple colored circle as default icon
            width = 64
            height = 64
            color = self._get_indicator_color()
            image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            draw.ellipse([4, 4, width - 4, height - 4], fill=color)
            return image
        except ImportError:
            # PIL not available - pystray will use default
            return None

    def _get_indicator_color(self) -> tuple[int, int, int, int]:
        """Get the color for the current indicator state."""
        state = self._controller.indicator_state
        colors = {
            TrayIndicatorState.STANDBY: (128, 128, 128, 255),  # Gray
            TrayIndicatorState.LISTENING: (0, 200, 0, 255),  # Green
            TrayIndicatorState.PAUSED: (255, 165, 0, 255),  # Orange
            TrayIndicatorState.ERROR: (255, 0, 0, 255),  # Red
            TrayIndicatorState.SHUTTING_DOWN: (64, 64, 64, 255),  # Dark gray
        }
        return colors.get(state, (128, 128, 128, 255))

    def _get_start_stop_label(self) -> str:
        """Get the current Start/Stop label."""
        items = self._controller.menu_items()
        for item in items:
            if item.action == TrayAction.START_OR_STOP:
                return item.label
        return "Stop"

    def _get_pause_resume_label(self) -> str:
        """Get the current Pause/Resume label."""
        items = self._controller.menu_items()
        for item in items:
            if item.action == TrayAction.PAUSE_OR_RESUME:
                return item.label
        return "Pause"

    def start(self) -> bool:
        """Start the tray icon in a background thread.

        Returns:
            True if tray icon started successfully, False otherwise.
        """
        if not self.is_available():
            return False

        if self._running:
            return True

        self._icon = self._create_icon()
        if self._icon is None:
            return False

        try:
            # Run icon in a separate thread
            import threading

            thread = threading.Thread(target=self._icon.run, daemon=True)
            thread.start()
            self._running = True
            return True
        except Exception:
            self._icon = None
            return False

    def stop(self) -> None:
        """Stop the tray icon."""
        if self._icon is not None:
            try:
                self._icon.stop()
            except Exception:
                pass
            self._icon = None
        self._running = False

    def update_icon(self) -> None:
        """Update the tray icon image to reflect current state."""
        if self._icon is not None:
            try:
                new_image = self._create_icon_image()
                if new_image is not None:
                    self._icon.icon = new_image
                self._icon.update_menu()
            except Exception:
                pass

    @property
    def running(self) -> bool:
        """Check if the tray icon is running."""
        return self._running


__all__ = [
    "TrayAction",
    "TrayActionHandlers",
    "TrayController",
    "TrayIconBackend",
    "TrayIndicatorState",
    "TrayMenuItem",
]
