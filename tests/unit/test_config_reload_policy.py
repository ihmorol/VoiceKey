"""Unit tests for config hot-reload classification policy (E06-S08)."""

from __future__ import annotations

from voicekey.config.manager import evaluate_reload_decision


def test_reload_decision_classifies_safe_keys_without_restart() -> None:
    decision = evaluate_reload_decision(
        [
            "typing.confidence_threshold",
            "modes.inactivity_auto_pause_seconds",
            "hotkeys.pause",
            "ui.audio_feedback",
        ]
    )

    assert decision.safe_to_apply == (
        "hotkeys.pause",
        "modes.inactivity_auto_pause_seconds",
        "typing.confidence_threshold",
        "ui.audio_feedback",
    )
    assert decision.restart_required == ()
    assert decision.restart_needed is False


def test_reload_decision_marks_engine_model_and_backend_as_restart_required() -> None:
    decision = evaluate_reload_decision(["engine.model_profile", "engine.asr_backend"])

    assert decision.safe_to_apply == ()
    assert decision.restart_required == ("engine.asr_backend", "engine.model_profile")
    assert decision.restart_needed is True


def test_reload_decision_marks_unknown_keys_as_restart_required_for_safety() -> None:
    decision = evaluate_reload_decision(["custom.unknown_key"])

    assert decision.safe_to_apply == ()
    assert decision.restart_required == ("custom.unknown_key",)
    assert decision.restart_needed is True


def test_reload_decision_supports_mixed_change_set_with_restart_signal() -> None:
    decision = evaluate_reload_decision(
        [
            "hotkeys.stop",
            "engine.model_profile",
            "typing.confidence_threshold",
        ]
    )

    assert decision.safe_to_apply == ("hotkeys.stop", "typing.confidence_threshold")
    assert decision.restart_required == ("engine.model_profile",)
    assert decision.restart_needed is True
