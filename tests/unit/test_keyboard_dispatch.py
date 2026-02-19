"""Unit tests for built-in keyboard command dispatch mapping."""

from __future__ import annotations

from dataclasses import dataclass, field

from voicekey.actions.keyboard_dispatch import dispatch_keyboard_command


@dataclass
class RecordingKeyboardBackend:
    keys: list[str] = field(default_factory=list)
    combos: list[tuple[str, ...]] = field(default_factory=list)
    texts: list[str] = field(default_factory=list)

    def press_key(self, key: str) -> None:
        self.keys.append(key)

    def press_combo(self, keys: list[str]) -> None:
        self.combos.append(tuple(keys))

    def type_text(self, text: str, delay_ms: int = 0) -> None:
        del delay_ms
        self.texts.append(text)


def test_dispatch_keyboard_command_routes_single_key_actions() -> None:
    backend = RecordingKeyboardBackend()

    handled = dispatch_keyboard_command("new_line", backend)

    assert handled is True
    assert backend.keys == ["enter"]
    assert backend.combos == []
    assert backend.texts == []


def test_dispatch_keyboard_command_routes_combo_actions() -> None:
    backend = RecordingKeyboardBackend()

    handled = dispatch_keyboard_command("control_c", backend)

    assert handled is True
    assert backend.keys == []
    assert backend.combos == [("ctrl", "c")]
    assert backend.texts == []


def test_dispatch_keyboard_command_routes_text_actions() -> None:
    backend = RecordingKeyboardBackend()

    handled = dispatch_keyboard_command("capital_hello", backend)

    assert handled is True
    assert backend.keys == []
    assert backend.combos == []
    assert backend.texts == ["Hello"]


def test_dispatch_keyboard_command_returns_false_for_unknown_command() -> None:
    backend = RecordingKeyboardBackend()

    handled = dispatch_keyboard_command("unknown_custom", backend)

    assert handled is False
    assert backend.keys == []
    assert backend.combos == []
    assert backend.texts == []
