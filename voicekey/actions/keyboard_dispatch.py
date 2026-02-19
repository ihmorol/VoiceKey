"""Keyboard action dispatcher for built-in command ids."""

from __future__ import annotations

from voicekey.platform.keyboard_base import KeyboardBackend

_KEY_COMMANDS: dict[str, str] = {
    "new_line": "enter",
    "tab": "tab",
    "space": "space",
    "backspace": "backspace",
    "delete": "delete",
    "left": "left",
    "right": "right",
    "up": "up",
    "down": "down",
    "escape": "escape",
}

_COMBO_COMMANDS: dict[str, tuple[str, ...]] = {
    "control_c": ("ctrl", "c"),
    "control_v": ("ctrl", "v"),
    "control_x": ("ctrl", "x"),
    "control_z": ("ctrl", "z"),
    "control_a": ("ctrl", "a"),
    "control_l": ("ctrl", "l"),
    "copy_that": ("ctrl", "c"),
    "paste_that": ("ctrl", "v"),
    "cut_that": ("ctrl", "x"),
}

_TEXT_COMMANDS: dict[str, str] = {
    "capital_hello": "Hello",
    "all_caps_hello": "HELLO",
}


def dispatch_keyboard_command(command_id: str, backend: KeyboardBackend) -> bool:
    """Dispatch built-in command id to keyboard backend operation."""
    key_name = _KEY_COMMANDS.get(command_id)
    if key_name is not None:
        backend.press_key(key_name)
        return True

    combo = _COMBO_COMMANDS.get(command_id)
    if combo is not None:
        backend.press_combo(list(combo))
        return True

    text = _TEXT_COMMANDS.get(command_id)
    if text is not None:
        backend.type_text(text)
        return True

    return False


__all__ = ["dispatch_keyboard_command"]
