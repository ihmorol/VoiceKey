"""CLI exit code contract for deterministic command behavior."""

from __future__ import annotations

from enum import IntEnum


class ExitCode(IntEnum):
    """Stable process exit codes used by VoiceKey CLI."""

    SUCCESS = 0
    COMMAND_ERROR = 1
    USAGE_ERROR = 2
    NOT_IMPLEMENTED = 3
    RUNTIME_ERROR = 10
