"""Linux hotkey backend adapter with pynput integration."""

from __future__ import annotations

import threading
from typing import Any

from voicekey.platform.hotkey_base import (
    HotkeyCallback,
    HotkeyRegistrationResult,
    InMemoryHotkeyBackend,
    normalize_hotkey,
)

# Optional dependency - pynput for global hotkey registration
_pynput_available: bool = False
_GlobalHotKeys: Any = None
_Key: Any = None

try:
    from pynput.keyboard import GlobalHotKeys, Key

    _pynput_available = True
    _GlobalHotKeys = GlobalHotKeys
    _Key = Key
except ImportError:
    pass

_LISTENER_JOIN_TIMEOUT_SECONDS = 1.0


def _convert_hotkey_to_pynput(hotkey: str) -> str:
    """Convert normalized hotkey format to pynput format.

    Converts 'ctrl+shift+p' to '<ctrl>+<shift>+p'.
    """
    parts = hotkey.split("+")
    converted = []
    for part in parts:
        part = part.strip()
        # Map common modifiers to pynput format
        if part in ("ctrl", "alt", "shift", "meta", "super"):
            converted.append(f"<{part}>")
        elif part.startswith("f") and part[1:].isdigit():
            # Function keys: f1 -> <f1>
            converted.append(f"<{part}>")
        else:
            # Regular keys: a, b, c, etc.
            converted.append(part)
    return "+".join(converted)


class LinuxHotkeyBackend(InMemoryHotkeyBackend):
    """Linux hotkey adapter with OS-level registration via pynput.

    Falls back to in-memory behavior when pynput is unavailable or
    registration fails (e.g., missing X11, headless environment).
    """

    def __init__(
        self,
        *,
        blocked_hotkeys: set[str] | None = None,
        use_os_integration: bool = True,
    ) -> None:
        super().__init__(blocked_hotkeys=blocked_hotkeys)
        self._use_os_integration = use_os_integration
        self._os_callbacks: dict[str, HotkeyCallback] = {}
        self._hotkey_listener: Any = None
        self._listener_lock = threading.Lock()
        self._os_available: bool | None = None

    @classmethod
    def is_available(cls) -> bool:
        """Check if OS-level hotkey registration is available."""
        if not _pynput_available:
            return False
        # Additional runtime checks could be added here
        # (e.g., checking for X11 display)
        return True

    def register(self, hotkey: str, callback: HotkeyCallback) -> HotkeyRegistrationResult:
        """Register a hotkey with OS-level integration if available."""
        normalized = normalize_hotkey(hotkey)

        # Check if already registered or blocked
        if normalized in self._callbacks or normalized in self._blocked_hotkeys:
            return HotkeyRegistrationResult(
                hotkey=normalized,
                registered=False,
                alternatives=self._suggest_alternatives(normalized),
            )

        # Try OS-level registration if available
        if self._use_os_integration and self.is_available():
            return self._register_os(normalized, callback)

        # Fall back to in-memory registration
        self._callbacks[normalized] = callback
        return HotkeyRegistrationResult(hotkey=normalized, registered=True)

    def _register_os(self, normalized: str, callback: HotkeyCallback) -> HotkeyRegistrationResult:
        """Attempt OS-level hotkey registration via pynput."""
        assert _GlobalHotKeys is not None
        assert _Key is not None

        try:
            with self._listener_lock:
                # Store callback
                self._os_callbacks[normalized] = callback

                restarted = self._restart_listener_locked()
                if not restarted:
                    self._os_callbacks.pop(normalized, None)
                    self._restart_listener_locked()
                    raise RuntimeError("failed to start Linux hotkey listener")

                # Also store in in-memory for list_registered()
                self._callbacks[normalized] = callback

                self._os_available = True
                return HotkeyRegistrationResult(hotkey=normalized, registered=True)

        except Exception:
            # OS registration failed - fall back to in-memory
            self._os_available = False

            # Still register in-memory as fallback
            self._callbacks[normalized] = callback
            return HotkeyRegistrationResult(hotkey=normalized, registered=True)

    def unregister(self, hotkey: str) -> None:
        """Unregister a hotkey from both OS and in-memory."""
        normalized = normalize_hotkey(hotkey)

        # Remove from OS callbacks
        with self._listener_lock:
            if normalized in self._os_callbacks:
                del self._os_callbacks[normalized]
                if not self._restart_listener_locked():
                    self._os_available = False

        # Remove from in-memory
        super().unregister(normalized)

    def shutdown(self) -> None:
        """Stop the hotkey listener and clean up resources."""
        with self._listener_lock:
            self._stop_listener_locked()
            self._os_callbacks.clear()

    def _restart_listener_locked(self) -> bool:
        """Rebuild OS listener from current callback map under lock."""
        self._stop_listener_locked()
        if not self._os_callbacks:
            return True

        if not self.is_available():
            return False

        assert _GlobalHotKeys is not None
        hotkey_map = {_convert_hotkey_to_pynput(hk): cb for hk, cb in self._os_callbacks.items()}
        try:
            listener = _GlobalHotKeys(hotkey_map)
            listener.start()
        except Exception:
            self._hotkey_listener = None
            return False

        self._hotkey_listener = listener
        return True

    def _stop_listener_locked(self) -> None:
        """Stop and join current listener under lock to avoid thread leaks."""
        listener = self._hotkey_listener
        self._hotkey_listener = None
        if listener is None:
            return

        try:
            listener.stop()
        except Exception:
            pass

        join = getattr(listener, "join", None)
        if callable(join):
            try:
                join(timeout=_LISTENER_JOIN_TIMEOUT_SECONDS)
            except TypeError:
                try:
                    join()
                except Exception:
                    pass
            except Exception:
                pass


__all__ = ["LinuxHotkeyBackend"]
