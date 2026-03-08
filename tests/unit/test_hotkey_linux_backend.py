"""Linux hotkey backend lifecycle tests."""

from __future__ import annotations

from typing import Any

import pytest

import voicekey.platform.hotkey_linux as hotkey_linux
from voicekey.platform.hotkey_linux import LinuxHotkeyBackend


class _FakeGlobalHotKeys:
    """Test double that records lifecycle events for listener instances."""

    instances: list["_FakeGlobalHotKeys"] = []

    def __init__(self, hotkey_map: dict[str, Any]) -> None:
        self.hotkey_map = hotkey_map
        self.start_calls = 0
        self.stop_calls = 0
        self.join_timeouts: list[float | None] = []
        _FakeGlobalHotKeys.instances.append(self)

    def start(self) -> None:
        self.start_calls += 1

    def stop(self) -> None:
        self.stop_calls += 1

    def join(self, timeout: float | None = None) -> None:
        self.join_timeouts.append(timeout)


@pytest.fixture
def linux_backend_with_fake_listener(monkeypatch: pytest.MonkeyPatch) -> LinuxHotkeyBackend:
    _FakeGlobalHotKeys.instances.clear()
    monkeypatch.setattr(hotkey_linux, "_pynput_available", True)
    monkeypatch.setattr(hotkey_linux, "_GlobalHotKeys", _FakeGlobalHotKeys)
    monkeypatch.setattr(hotkey_linux, "_Key", object())
    return LinuxHotkeyBackend()


def test_register_restart_stops_and_joins_previous_listener(
    linux_backend_with_fake_listener: LinuxHotkeyBackend,
) -> None:
    backend = linux_backend_with_fake_listener

    first = backend.register("ctrl+f12", lambda: None)
    second = backend.register("ctrl+f11", lambda: None)

    assert first.registered is True
    assert second.registered is True
    assert len(_FakeGlobalHotKeys.instances) == 2

    first_listener = _FakeGlobalHotKeys.instances[0]
    second_listener = _FakeGlobalHotKeys.instances[1]

    assert first_listener.stop_calls == 1
    assert first_listener.join_timeouts == [1.0]
    assert second_listener.start_calls == 1


def test_repeated_register_unregister_cycles_are_listener_stable(
    linux_backend_with_fake_listener: LinuxHotkeyBackend,
) -> None:
    backend = linux_backend_with_fake_listener

    for _ in range(5):
        result = backend.register("ctrl+f12", lambda: None)
        assert result.registered is True
        backend.unregister("ctrl+f12")

    assert backend.list_registered() == ()
    assert backend._hotkey_listener is None
    assert len(_FakeGlobalHotKeys.instances) == 5
    for listener in _FakeGlobalHotKeys.instances:
        assert listener.stop_calls == 1
        assert listener.join_timeouts == [1.0]


def test_os_restart_failure_keeps_in_memory_callbacks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _FlakyGlobalHotKeys:
        instances: list["_FlakyGlobalHotKeys"] = []

        def __init__(self, hotkey_map: dict[str, Any]) -> None:
            self.hotkey_map = hotkey_map
            self.stop_calls = 0
            self.join_timeouts: list[float | None] = []
            _FlakyGlobalHotKeys.instances.append(self)

        def start(self) -> None:
            if len(self.hotkey_map) > 1:
                raise RuntimeError("listener start failed")

        def stop(self) -> None:
            self.stop_calls += 1

        def join(self, timeout: float | None = None) -> None:
            self.join_timeouts.append(timeout)

    monkeypatch.setattr(hotkey_linux, "_pynput_available", True)
    monkeypatch.setattr(hotkey_linux, "_GlobalHotKeys", _FlakyGlobalHotKeys)
    monkeypatch.setattr(hotkey_linux, "_Key", object())

    backend = LinuxHotkeyBackend()
    triggered: list[str] = []
    first = backend.register("ctrl+f12", lambda: triggered.append("first"))
    second = backend.register("ctrl+f11", lambda: triggered.append("second"))

    assert first.registered is True
    assert second.registered is True
    assert backend.list_registered() == ("ctrl+f11", "ctrl+f12")
    assert backend.trigger("ctrl+f12") is True
    assert backend.trigger("ctrl+f11") is True
    assert triggered == ["first", "second"]
    assert set(backend._os_callbacks) == {"ctrl+f12"}
    assert len(_FlakyGlobalHotKeys.instances) == 3
