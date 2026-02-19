"""Unit tests for action router command dispatch behavior."""

from __future__ import annotations

from dataclasses import dataclass, field

from voicekey.actions.router import ActionRouter
from voicekey.commands.custom import CustomActionType, CustomCommandAction


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


@dataclass
class RecordingWindowBackend:
    calls: list[str] = field(default_factory=list)

    def maximize_active(self) -> None:
        self.calls.append("maximize")

    def minimize_active(self) -> None:
        self.calls.append("minimize")

    def close_active(self) -> None:
        self.calls.append("close")

    def switch_next(self) -> None:
        self.calls.append("switch")


def test_router_dispatches_window_commands_before_keyboard_commands() -> None:
    keyboard = RecordingKeyboardBackend()
    window = RecordingWindowBackend()
    router = ActionRouter(keyboard_backend=keyboard, window_backend=window)

    result = router.dispatch("maximize_window")

    assert result.handled is True
    assert result.route == "window"
    assert window.calls == ["maximize"]
    assert keyboard.keys == []


def test_router_dispatches_built_in_keyboard_commands() -> None:
    keyboard = RecordingKeyboardBackend()
    router = ActionRouter(keyboard_backend=keyboard)

    result = router.dispatch("control_v")

    assert result.handled is True
    assert result.route == "keyboard"
    assert keyboard.combos == [("ctrl", "v")]


def test_router_dispatches_custom_key_combo_action() -> None:
    keyboard = RecordingKeyboardBackend()
    router = ActionRouter(
        keyboard_backend=keyboard,
        custom_actions={
            "custom_save_file": CustomCommandAction(
                command_id="custom_save_file",
                phrase="save",
                action_type=CustomActionType.KEY_COMBO,
                keys=("ctrl", "s"),
            )
        },
    )

    result = router.dispatch("custom_save_file")

    assert result.handled is True
    assert result.route == "custom_key_combo"
    assert keyboard.combos == [("ctrl", "s")]


def test_router_dispatches_custom_text_action() -> None:
    keyboard = RecordingKeyboardBackend()
    router = ActionRouter(
        keyboard_backend=keyboard,
        custom_actions={
            "custom_signature": CustomCommandAction(
                command_id="custom_signature",
                phrase="signature",
                action_type=CustomActionType.TEXT,
                text="Best regards,",
            )
        },
    )

    result = router.dispatch("custom_signature")

    assert result.handled is True
    assert result.route == "custom_text"
    assert keyboard.texts == ["Best regards,"]


def test_router_returns_unhandled_for_unknown_command() -> None:
    keyboard = RecordingKeyboardBackend()
    router = ActionRouter(keyboard_backend=keyboard)

    result = router.dispatch("unknown_command")

    assert result.handled is False
    assert result.route is None
