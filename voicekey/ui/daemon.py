"""Daemon start behavior resolution by session type."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class DaemonStartBehavior:
    """Resolved startup behavior for daemon and foreground modes."""

    daemon: bool
    show_terminal_ui: bool
    tray_enabled: bool
    graphical_session: bool


def has_graphical_session(environment: Mapping[str, str]) -> bool:
    """Return whether environment indicates an interactive graphical session."""
    session_type = environment.get("XDG_SESSION_TYPE", "").strip().lower()
    if session_type in {"x11", "wayland"}:
        return True

    display = environment.get("DISPLAY", "").strip()
    if display:
        return True

    wayland_display = environment.get("WAYLAND_DISPLAY", "").strip()
    return bool(wayland_display)


def resolve_daemon_start_behavior(
    daemon: bool,
    environment: Mapping[str, str] | None = None,
) -> DaemonStartBehavior:
    """Resolve startup behavior for daemon mode and tray activation."""
    env = environment or {}
    graphical = has_graphical_session(env)
    if daemon:
        return DaemonStartBehavior(
            daemon=True,
            show_terminal_ui=False,
            tray_enabled=graphical,
            graphical_session=graphical,
        )

    return DaemonStartBehavior(
        daemon=False,
        show_terminal_ui=True,
        tray_enabled=False,
        graphical_session=graphical,
    )


__all__ = [
    "DaemonStartBehavior",
    "has_graphical_session",
    "resolve_daemon_start_behavior",
]
