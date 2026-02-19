"""Unit tests for deterministic runtime routing policy."""

from __future__ import annotations

from voicekey.app.routing_policy import RuntimeRoutingPolicy
from voicekey.app.state_machine import AppState
from voicekey.commands.parser import CommandParser


def test_paused_state_blocks_dictation_text() -> None:
    parser = CommandParser()
    policy = RuntimeRoutingPolicy()

    decision = policy.evaluate(AppState.PAUSED, parser.parse("hello world"))

    assert decision.allowed is False


def test_paused_state_blocks_non_system_command() -> None:
    parser = CommandParser()
    policy = RuntimeRoutingPolicy()

    decision = policy.evaluate(AppState.PAUSED, parser.parse("new line command"))

    assert decision.allowed is False


def test_paused_state_allows_resume_phrase_by_default() -> None:
    parser = CommandParser()
    policy = RuntimeRoutingPolicy()

    decision = policy.evaluate(AppState.PAUSED, parser.parse("resume voice key"))

    assert decision.allowed is True


def test_paused_state_blocks_resume_phrase_when_channel_disabled() -> None:
    parser = CommandParser()
    policy = RuntimeRoutingPolicy(paused_resume_phrase_enabled=False)

    decision = policy.evaluate(AppState.PAUSED, parser.parse("resume voice key"))

    assert decision.allowed is False


def test_paused_state_always_allows_stop_phrase() -> None:
    parser = CommandParser()
    policy = RuntimeRoutingPolicy(paused_resume_phrase_enabled=False)

    decision = policy.evaluate(AppState.PAUSED, parser.parse("voice key stop"))

    assert decision.allowed is True
