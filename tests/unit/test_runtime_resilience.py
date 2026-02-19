"""Unit tests for runtime resilience policies (E03-S04)."""

from __future__ import annotations

import pytest

from voicekey.app.resilience import RetryPolicy, decide_safety_fallback
from voicekey.app.runtime_errors import RuntimeErrorCategory, RuntimeErrorCode, runtime_error_info
from voicekey.app.state_machine import AppEvent, AppState


@pytest.mark.parametrize(
    ("code", "category", "hint"),
    [
        (RuntimeErrorCode.NO_MICROPHONE, RuntimeErrorCategory.AUDIO, "voicekey devices"),
        (RuntimeErrorCode.HOTKEY_CONFLICT, RuntimeErrorCategory.CONFIG, "alternative"),
        (
            RuntimeErrorCode.MODEL_CHECKSUM_FAILED,
            RuntimeErrorCategory.RECOGNITION,
            "voicekey download",
        ),
        (RuntimeErrorCode.KEYBOARD_BLOCKED, RuntimeErrorCategory.INJECTION, "permissions"),
    ],
)
def test_required_error_scenarios_include_actionable_remediation(
    code: RuntimeErrorCode,
    category: RuntimeErrorCategory,
    hint: str,
) -> None:
    info = runtime_error_info(code)

    assert info.code is code
    assert info.category is category
    assert hint in info.remediation.lower()
    assert info.actionable_message().strip()


def test_retry_policy_is_bounded_and_deterministic() -> None:
    policy = RetryPolicy(max_attempts=3, backoff_seconds=(1.0, 2.0, 4.0))

    assert policy.next_delay_after_failure(1) == 1.0
    assert policy.next_delay_after_failure(2) == 2.0
    assert policy.next_delay_after_failure(3) == 4.0
    assert policy.next_delay_after_failure(4) is None


def test_retry_policy_reuses_last_backoff_value_when_attempts_exceed_schedule() -> None:
    policy = RetryPolicy(max_attempts=5, backoff_seconds=(0.5, 1.0))

    assert policy.next_delay_after_failure(1) == 0.5
    assert policy.next_delay_after_failure(2) == 1.0
    assert policy.next_delay_after_failure(3) == 1.0
    assert policy.next_delay_after_failure(4) == 1.0
    assert policy.next_delay_after_failure(5) == 1.0
    assert policy.next_delay_after_failure(6) is None


def test_retry_policy_validates_configuration() -> None:
    with pytest.raises(ValueError, match="max_attempts"):
        RetryPolicy(max_attempts=0, backoff_seconds=(1.0,))

    with pytest.raises(ValueError, match="backoff_seconds"):
        RetryPolicy(max_attempts=1, backoff_seconds=())


@pytest.mark.parametrize(
    ("code", "state", "expected_event"),
    [
        (RuntimeErrorCode.NO_MICROPHONE, AppState.LISTENING, AppEvent.INACTIVITY_AUTO_PAUSE),
        (RuntimeErrorCode.MODEL_CHECKSUM_FAILED, AppState.STANDBY, AppEvent.PAUSE_REQUESTED),
        (RuntimeErrorCode.KEYBOARD_BLOCKED, AppState.PROCESSING, None),
    ],
)
def test_safety_fallback_forces_pause_when_safety_is_not_guaranteed(
    code: RuntimeErrorCode,
    state: AppState,
    expected_event: AppEvent | None,
) -> None:
    decision = decide_safety_fallback(code=code, state=state)

    assert decision.force_pause is True
    assert decision.pause_event is expected_event


def test_hotkey_conflict_does_not_force_pause_by_default() -> None:
    decision = decide_safety_fallback(
        code=RuntimeErrorCode.HOTKEY_CONFLICT,
        state=AppState.LISTENING,
    )

    assert decision.force_pause is False
    assert decision.pause_event is None


def test_microphone_disconnect_only_forces_pause_after_retry_budget_exhausted() -> None:
    retrying = decide_safety_fallback(
        code=RuntimeErrorCode.MICROPHONE_DISCONNECTED,
        state=AppState.LISTENING,
        retries_exhausted=False,
    )
    exhausted = decide_safety_fallback(
        code=RuntimeErrorCode.MICROPHONE_DISCONNECTED,
        state=AppState.LISTENING,
        retries_exhausted=True,
    )

    assert retrying.force_pause is False
    assert retrying.pause_event is None
    assert exhausted.force_pause is True
    assert exhausted.pause_event is AppEvent.INACTIVITY_AUTO_PAUSE
