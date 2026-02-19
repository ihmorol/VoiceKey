"""Unit tests for onboarding wizard flow and persistence (E06-S03)."""

from __future__ import annotations

import yaml

from voicekey.ui.onboarding import (
    DEFAULT_TOGGLE_HOTKEY,
    MAX_ONBOARDING_SECONDS,
    OnboardingStateMachine,
    OnboardingStep,
    run_onboarding,
)


class FakeClock:
    def __init__(self, *values: float) -> None:
        self._values = list(values)
        self._index = 0

    def __call__(self) -> float:
        value = self._values[self._index]
        if self._index < len(self._values) - 1:
            self._index += 1
        return value


def test_onboarding_state_machine_steps_are_in_required_order() -> None:
    flow = OnboardingStateMachine()

    observed: list[OnboardingStep] = []
    while flow.current_step is not None:
        observed.append(flow.current_step)
        flow.complete_current_step()

    assert tuple(observed) == (
        OnboardingStep.WELCOME,
        OnboardingStep.MICROPHONE,
        OnboardingStep.WAKE_TEST,
        OnboardingStep.HOTKEY,
        OnboardingStep.AUTOSTART,
        OnboardingStep.TUTORIAL,
    )


def test_onboarding_success_persists_selected_values(tmp_path) -> None:
    config_path = tmp_path / "voicekey" / "config.yaml"
    clock = FakeClock(0.0, 120.0)

    result = run_onboarding(
        config_path=config_path,
        selected_device_id=7,
        wake_phrase_verified=True,
        toggle_hotkey="ctrl+alt+k",
        autostart_enabled=True,
        clock=clock,
    )

    assert result.completed is True
    assert result.persisted is True
    assert result.errors == ()
    assert result.within_target is True
    assert result.duration_seconds == 120.0

    persisted = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert persisted["audio"]["device_id"] == 7
    assert persisted["hotkeys"]["toggle_listening"] == "ctrl+alt+k"
    assert persisted["system"]["autostart_enabled"] is True


def test_onboarding_skip_writes_safe_defaults(tmp_path) -> None:
    config_path = tmp_path / "voicekey" / "config.yaml"

    result = run_onboarding(config_path=config_path, skip=True)

    assert result.completed is False
    assert result.skipped is True
    assert result.persisted is True
    assert result.toggle_hotkey == DEFAULT_TOGGLE_HOTKEY

    persisted = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert persisted["system"]["autostart_enabled"] is False
    assert persisted["features"]["window_commands_enabled"] is False
    assert persisted["features"]["text_expansion_enabled"] is False
    assert persisted["privacy"]["telemetry_enabled"] is False
    assert persisted["privacy"]["transcript_logging"] is False


def test_onboarding_reports_failure_when_required_checks_fail(tmp_path) -> None:
    config_path = tmp_path / "voicekey" / "config.yaml"
    clock = FakeClock(0.0, MAX_ONBOARDING_SECONDS + 20.0)

    result = run_onboarding(
        config_path=config_path,
        selected_device_id=None,
        wake_phrase_verified=False,
        clock=clock,
    )

    assert result.completed is False
    assert result.persisted is False
    assert result.within_target is False
    assert "microphone selection failed: no valid device" in result.errors
    assert "wake phrase test failed: phrase not detected" in result.errors
