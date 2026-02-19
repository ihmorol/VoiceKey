"""Deterministic routing policy for transcript outputs by app state."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from voicekey.app.state_machine import AppState
from voicekey.commands.parser import ParseKind, ParseResult


class RoutingDecision(StrEnum):
    """Policy decision returned for a parsed transcript."""

    ALLOW = "allow"
    DROP = "drop"


@dataclass(frozen=True)
class RoutingPolicyResult:
    """Deterministic routing policy outcome."""

    decision: RoutingDecision
    reason: str

    @property
    def allowed(self) -> bool:
        """Whether parsed output can be routed/executed."""
        return self.decision is RoutingDecision.ALLOW


class RuntimeRoutingPolicy:
    """State-aware routing policy for dictation and command execution."""

    def __init__(self, paused_resume_phrase_enabled: bool = True) -> None:
        self._paused_resume_phrase_enabled = paused_resume_phrase_enabled

    def evaluate(self, state: AppState, parsed: ParseResult) -> RoutingPolicyResult:
        """Decide if parsed transcript can be routed in the current state."""
        if state is not AppState.PAUSED:
            return RoutingPolicyResult(
                decision=RoutingDecision.ALLOW,
                reason="non_paused_state",
            )

        if parsed.kind is not ParseKind.SYSTEM or parsed.command is None:
            return RoutingPolicyResult(
                decision=RoutingDecision.DROP,
                reason="paused_blocks_dictation_and_non_system_commands",
            )

        command_id = parsed.command.command_id
        if command_id == "voice_key_stop":
            return RoutingPolicyResult(
                decision=RoutingDecision.ALLOW,
                reason="paused_allows_stop_phrase",
            )

        if command_id == "resume_voice_key" and self._paused_resume_phrase_enabled:
            return RoutingPolicyResult(
                decision=RoutingDecision.ALLOW,
                reason="paused_allows_resume_phrase",
            )

        return RoutingPolicyResult(
            decision=RoutingDecision.DROP,
            reason="paused_blocks_non_control_system_phrase",
        )


__all__ = ["RoutingDecision", "RoutingPolicyResult", "RuntimeRoutingPolicy"]
