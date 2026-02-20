"""Action router for command execution across keyboard/window/custom actions."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from voicekey.actions.keyboard_dispatch import dispatch_keyboard_command
from voicekey.actions.window_dispatch import dispatch_window_command
from voicekey.commands.custom import CustomActionType, CustomCommandAction
from voicekey.platform.keyboard_base import KeyboardBackend
from voicekey.platform.window_base import WindowBackend


@dataclass(frozen=True)
class ActionRouteResult:
    """Deterministic action-routing execution result."""

    handled: bool
    route: str | None = None


class ActionRouter:
    """Route parsed command ids to backend operations."""

    def __init__(
        self,
        *,
        keyboard_backend: KeyboardBackend,
        window_backend: WindowBackend | None = None,
        custom_actions: Mapping[str, CustomCommandAction] | None = None,
    ) -> None:
        self._keyboard_backend = keyboard_backend
        self._window_backend = window_backend
        self._custom_actions = dict(custom_actions or {})

    def dispatch(self, command_id: str) -> ActionRouteResult:
        """Dispatch command id to first matching execution route."""
        if self._window_backend is not None and dispatch_window_command(command_id, self._window_backend):
            return ActionRouteResult(handled=True, route="window")

        if dispatch_keyboard_command(command_id, self._keyboard_backend):
            return ActionRouteResult(handled=True, route="keyboard")

        custom_action = self._custom_actions.get(command_id)
        if custom_action is None:
            return ActionRouteResult(handled=False, route=None)

        if custom_action.action_type is CustomActionType.KEY_COMBO:
            if custom_action.keys is None:
                raise ValueError(
                    f"Custom action '{command_id}' has action_type KEY_COMBO but keys is None"
                )
            self._keyboard_backend.press_combo(list(custom_action.keys))
            return ActionRouteResult(handled=True, route="custom_key_combo")

        if custom_action.text is None:
            raise ValueError(
                f"Custom action '{command_id}' has action_type TEXT but text is None"
            )
        self._keyboard_backend.type_text(custom_action.text)
        return ActionRouteResult(handled=True, route="custom_text")


__all__ = ["ActionRouteResult", "ActionRouter"]
