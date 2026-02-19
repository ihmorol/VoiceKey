"""Unit tests for window command dispatch mapping (E04-S04)."""

from __future__ import annotations

from dataclasses import dataclass, field

from voicekey.actions.window_dispatch import dispatch_window_command


@dataclass
class RecordingWindowBackend:
    """Backend double that records invoked window operations."""

    calls: list[str] = field(default_factory=list)

    def maximize_active(self) -> None:
        self.calls.append("maximize")

    def minimize_active(self) -> None:
        self.calls.append("minimize")

    def close_active(self) -> None:
        self.calls.append("close")

    def switch_next(self) -> None:
        self.calls.append("switch")


def test_dispatch_returns_false_for_non_window_command_id() -> None:
    backend = RecordingWindowBackend()

    handled = dispatch_window_command("new_line", backend)

    assert handled is False
    assert backend.calls == []


def test_dispatch_invokes_expected_backend_operations() -> None:
    backend = RecordingWindowBackend()

    dispatch_window_command("maximize_window", backend)
    dispatch_window_command("minimize_window", backend)
    dispatch_window_command("close_window", backend)
    dispatch_window_command("switch_window", backend)

    assert backend.calls == ["maximize", "minimize", "close", "switch"]
