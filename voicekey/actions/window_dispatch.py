"""Window management action dispatcher."""

from __future__ import annotations

from voicekey.platform.window_base import WindowBackend

_WINDOW_COMMAND_TO_OPERATION: dict[str, str] = {
    "maximize_window": "maximize_active",
    "minimize_window": "minimize_active",
    "close_window": "close_active",
    "switch_window": "switch_next",
}


def dispatch_window_command(command_id: str, backend: WindowBackend) -> bool:
    """Dispatch command id to window backend operation when mapped."""

    operation_name = _WINDOW_COMMAND_TO_OPERATION.get(command_id)
    if operation_name is None:
        return False

    getattr(backend, operation_name)()
    return True


__all__ = ["dispatch_window_command"]
