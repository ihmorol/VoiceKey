"""Linux hotkey backend adapter."""

from __future__ import annotations

from voicekey.platform.hotkey_base import InMemoryHotkeyBackend


class LinuxHotkeyBackend(InMemoryHotkeyBackend):
    """Linux hotkey adapter with deterministic unit-scope behavior."""


__all__ = ["LinuxHotkeyBackend"]
