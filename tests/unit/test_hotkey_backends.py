"""Unit tests for global hotkey backend abstraction and adapters (E04-S02)."""

from __future__ import annotations

from typing import Union

import pytest

from voicekey.platform.hotkey_base import InMemoryHotkeyBackend
from voicekey.platform.hotkey_linux import LinuxHotkeyBackend
from voicekey.platform.hotkey_windows import WindowsHotkeyBackend

# Type alias for the actual backend classes we test
HotkeyBackendClass = Union[type[LinuxHotkeyBackend], type[WindowsHotkeyBackend]]


@pytest.mark.parametrize("backend_cls", [LinuxHotkeyBackend, WindowsHotkeyBackend])
def test_hotkey_registration_lifecycle_is_dynamic(backend_cls: HotkeyBackendClass) -> None:
    backend = backend_cls()
    triggered: list[str] = []

    initial = backend.register("shift+ctrl+p", lambda: triggered.append("toggle"))
    assert initial.registered is True
    assert initial.hotkey == "ctrl+shift+p"
    assert backend.list_registered() == ("ctrl+shift+p",)

    assert backend.trigger("ctrl+shift+p") is True
    assert triggered == ["toggle"]

    backend.unregister("ctrl+shift+p")
    assert backend.list_registered() == ()
    assert backend.trigger("ctrl+shift+p") is False


@pytest.mark.parametrize("backend_cls", [LinuxHotkeyBackend, WindowsHotkeyBackend])
def test_hotkey_rebind_flow_supports_config_reload(backend_cls: HotkeyBackendClass) -> None:
    backend = backend_cls()

    first = backend.register("ctrl+shift+`", lambda: None)
    assert first.registered is True
    assert backend.list_registered() == ("ctrl+shift+`",)

    backend.unregister("ctrl+shift+`")
    second = backend.register("ctrl+shift+f12", lambda: None)

    assert second.registered is True
    assert backend.list_registered() == ("ctrl+shift+f12",)


@pytest.mark.parametrize("backend_cls", [LinuxHotkeyBackend, WindowsHotkeyBackend])
def test_conflicts_return_deterministic_alternative_suggestions(
    backend_cls: HotkeyBackendClass,
) -> None:
    backend = backend_cls(blocked_hotkeys={"ctrl+shift+`", "ctrl+shift+f12"})

    result = backend.register("shift+ctrl+`", lambda: None)

    assert result.registered is False
    assert result.hotkey == "ctrl+shift+`"
    assert result.alternatives == (
        "ctrl+shift+f11",
        "ctrl+shift+f10",
        "ctrl+shift+f9",
    )


@pytest.mark.parametrize("backend_cls", [LinuxHotkeyBackend, WindowsHotkeyBackend])
def test_existing_binding_conflict_returns_suggestions(
    backend_cls: HotkeyBackendClass,
) -> None:
    backend = backend_cls()
    backend.register("ctrl+shift+f12", lambda: None)

    result = backend.register("ctrl+shift+f12", lambda: None)

    assert result.registered is False
    assert result.alternatives[0] == "ctrl+shift+f11"


@pytest.mark.parametrize("backend_cls", [LinuxHotkeyBackend, WindowsHotkeyBackend])
def test_is_available_returns_bool(backend_cls: HotkeyBackendClass) -> None:
    """Test that is_available returns a boolean value."""
    result = backend_cls.is_available()
    assert isinstance(result, bool)


@pytest.mark.parametrize("backend_cls", [LinuxHotkeyBackend, WindowsHotkeyBackend])
def test_backend_works_with_os_integration_disabled(
    backend_cls: HotkeyBackendClass,
) -> None:
    """Test that backend works in pure in-memory mode."""
    backend = backend_cls(use_os_integration=False)
    triggered: list[str] = []

    result = backend.register("ctrl+f12", lambda: triggered.append("fired"))
    assert result.registered is True

    assert backend.trigger("ctrl+f12") is True
    assert triggered == ["fired"]


@pytest.mark.parametrize("backend_cls", [LinuxHotkeyBackend, WindowsHotkeyBackend])
def test_shutdown_clears_resources(backend_cls: HotkeyBackendClass) -> None:
    """Test that shutdown cleans up resources."""
    backend = backend_cls()
    backend.register("ctrl+f12", lambda: None)

    # Should not raise
    backend.shutdown()

    # Backend should still be usable after shutdown
    result = backend.register("ctrl+f11", lambda: None)
    assert result.registered is True
