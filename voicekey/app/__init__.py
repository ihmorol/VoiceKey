"""VoiceKey application core."""

from voicekey.app.state_machine import (
    AppEvent,
    AppState,
    InvalidTransitionError,
    ListeningMode,
    ModeHooks,
    TransitionResult,
    VoiceKeyStateMachine,
)
from voicekey.app.main import RuntimeCoordinator, RuntimeUpdate
from voicekey.app.watchdog import (
    InactivityWatchdog,
    WatchdogTelemetryCounters,
    WatchdogTimerConfig,
    WatchdogTimeoutEvent,
    WatchdogTimeoutType,
)

__all__ = [
    "AppEvent",
    "AppState",
    "InvalidTransitionError",
    "ListeningMode",
    "ModeHooks",
    "TransitionResult",
    "VoiceKeyStateMachine",
    "RuntimeCoordinator",
    "RuntimeUpdate",
    "InactivityWatchdog",
    "WatchdogTelemetryCounters",
    "WatchdogTimerConfig",
    "WatchdogTimeoutEvent",
    "WatchdogTimeoutType",
]
