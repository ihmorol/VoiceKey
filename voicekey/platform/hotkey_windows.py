"""Windows hotkey backend adapter."""

from __future__ import annotations

from voicekey.platform.hotkey_base import InMemoryHotkeyBackend


class WindowsHotkeyBackend(InMemoryHotkeyBackend):
    """Windows hotkey adapter with deterministic unit-scope behavior."""


__all__ = ["WindowsHotkeyBackend"]
