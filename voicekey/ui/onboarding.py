"""First-run onboarding wizard flow and persistence helpers."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from time import monotonic
from typing import Callable

from voicekey.config.manager import load_config, save_config
from voicekey.config.schema import default_config

MAX_ONBOARDING_SECONDS = 300.0
DEFAULT_TOGGLE_HOTKEY = "ctrl+shift+`"
TUTORIAL_SCRIPT: tuple[str, ...] = (
    "say voice key",
    "say hello world",
    "say new line command",
    "say pause voice key",
    "say resume voice key",
)

KEYBOARD_INTERACTION_MAP: dict[str, tuple[str, ...]] = {
    "welcome_privacy": ("enter", "tab", "shift+tab"),
    "microphone_selection": ("up", "down", "enter", "tab", "shift+tab"),
    "wake_phrase_test": ("enter", "tab", "shift+tab"),
    "hotkey_confirmation": ("enter", "tab", "shift+tab"),
    "autostart_preference": ("left", "right", "enter", "tab", "shift+tab"),
    "quick_tutorial": ("enter", "tab", "shift+tab"),
}


class OnboardingStep(StrEnum):
    """Canonical onboarding step identifiers in required order."""

    WELCOME = "welcome_privacy"
    MICROPHONE = "microphone_selection"
    WAKE_TEST = "wake_phrase_test"
    HOTKEY = "hotkey_confirmation"
    AUTOSTART = "autostart_preference"
    TUTORIAL = "quick_tutorial"


@dataclass
class OnboardingStateMachine:
    """Deterministic step progression for onboarding flow orchestration."""

    _steps: tuple[OnboardingStep, ...] = (
        OnboardingStep.WELCOME,
        OnboardingStep.MICROPHONE,
        OnboardingStep.WAKE_TEST,
        OnboardingStep.HOTKEY,
        OnboardingStep.AUTOSTART,
        OnboardingStep.TUTORIAL,
    )
    _index: int = 0

    @property
    def current_step(self) -> OnboardingStep | None:
        if self._index >= len(self._steps):
            return None
        return self._steps[self._index]

    @property
    def completed_steps(self) -> tuple[OnboardingStep, ...]:
        return self._steps[: self._index]

    def complete_current_step(self) -> None:
        if self.current_step is None:
            raise ValueError("onboarding already completed")
        self._index += 1


@dataclass(frozen=True)
class OnboardingResult:
    """Structured onboarding execution result."""

    completed: bool
    skipped: bool
    config_path: Path
    persisted: bool
    selected_device_id: int | None
    wake_phrase_verified: bool
    toggle_hotkey: str
    autostart_enabled: bool
    completed_steps: tuple[str, ...]
    skipped_steps: tuple[str, ...]
    tutorial_script: tuple[str, ...]
    keyboard_interaction_map: dict[str, tuple[str, ...]]
    errors: tuple[str, ...] = ()
    duration_seconds: float = 0.0
    within_target: bool = True


def run_onboarding(
    *,
    config_path: str | Path | None = None,
    skip: bool = False,
    selected_device_id: int | None = None,
    wake_phrase_verified: bool = True,
    toggle_hotkey: str = DEFAULT_TOGGLE_HOTKEY,
    autostart_enabled: bool = False,
    clock: Callable[[], float] = monotonic,
) -> OnboardingResult:
    """Execute deterministic onboarding flow and persist selected settings."""
    started_at = clock()

    if skip:
        config = default_config()
        loaded = load_config(explicit_path=config_path)
        save_config(config, loaded.path)
        duration = _duration_seconds(started_at, clock)
        return OnboardingResult(
            completed=False,
            skipped=True,
            config_path=loaded.path,
            persisted=True,
            selected_device_id=config.audio.device_id,
            wake_phrase_verified=False,
            toggle_hotkey=config.hotkeys.toggle_listening,
            autostart_enabled=config.system.autostart_enabled,
            completed_steps=(),
            skipped_steps=tuple(step.value for step in flow_steps()),
            tutorial_script=TUTORIAL_SCRIPT,
            keyboard_interaction_map=KEYBOARD_INTERACTION_MAP,
            duration_seconds=duration,
            within_target=duration <= MAX_ONBOARDING_SECONDS,
        )

    flow = OnboardingStateMachine()
    errors: list[str] = []

    flow.complete_current_step()  # welcome/privacy acknowledged

    if selected_device_id is None:
        errors.append("microphone selection failed: no valid device")
    else:
        flow.complete_current_step()

    if wake_phrase_verified:
        if selected_device_id is not None:
            flow.complete_current_step()
    else:
        errors.append("wake phrase test failed: phrase not detected")

    hotkey_value = toggle_hotkey.strip() or DEFAULT_TOGGLE_HOTKEY
    if not errors:
        flow.complete_current_step()  # hotkey
        flow.complete_current_step()  # autostart
        flow.complete_current_step()  # tutorial

    loaded = load_config(explicit_path=config_path)
    config = loaded.config
    persisted = False

    if not errors:
        config.audio.device_id = selected_device_id
        config.hotkeys.toggle_listening = hotkey_value
        config.system.autostart_enabled = autostart_enabled
        save_config(config, loaded.path)
        persisted = True

    duration = _duration_seconds(started_at, clock)
    return OnboardingResult(
        completed=not errors,
        skipped=False,
        config_path=loaded.path,
        persisted=persisted,
        selected_device_id=selected_device_id,
        wake_phrase_verified=wake_phrase_verified,
        toggle_hotkey=hotkey_value,
        autostart_enabled=autostart_enabled,
        completed_steps=tuple(step.value for step in flow.completed_steps),
        skipped_steps=(),
        tutorial_script=TUTORIAL_SCRIPT,
        keyboard_interaction_map=KEYBOARD_INTERACTION_MAP,
        errors=tuple(errors),
        duration_seconds=duration,
        within_target=duration <= MAX_ONBOARDING_SECONDS,
    )


def _duration_seconds(started_at: float, clock: Callable[[], float]) -> float:
    return max(0.0, clock() - started_at)


def flow_steps() -> tuple[OnboardingStep, ...]:
    """Return canonical onboarding step order."""
    return (
        OnboardingStep.WELCOME,
        OnboardingStep.MICROPHONE,
        OnboardingStep.WAKE_TEST,
        OnboardingStep.HOTKEY,
        OnboardingStep.AUTOSTART,
        OnboardingStep.TUTORIAL,
    )


__all__ = [
    "DEFAULT_TOGGLE_HOTKEY",
    "KEYBOARD_INTERACTION_MAP",
    "MAX_ONBOARDING_SECONDS",
    "OnboardingResult",
    "OnboardingStateMachine",
    "OnboardingStep",
    "TUTORIAL_SCRIPT",
    "flow_steps",
    "run_onboarding",
]
