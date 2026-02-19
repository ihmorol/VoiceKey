"""Hotkey backend contract and deterministic conflict handling."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol

HotkeyCallback = Callable[[], None]

_MODIFIER_ORDER: tuple[str, ...] = ("ctrl", "alt", "shift", "meta", "super")
_MODIFIER_ALIASES: dict[str, str] = {
    "control": "ctrl",
    "ctl": "ctrl",
    "option": "alt",
    "win": "meta",
    "command": "meta",
    "cmd": "meta",
}
_FALLBACK_KEYS: tuple[str, ...] = ("f12", "f11", "f10", "f9", "f8")


@dataclass(frozen=True)
class HotkeyRegistrationResult:
    """Result for a single hotkey registration attempt."""

    hotkey: str
    registered: bool
    alternatives: tuple[str, ...] = ()


class HotkeyBackend(Protocol):
    """Contract for global hotkey registration adapters."""

    def register(self, hotkey: str, callback: HotkeyCallback) -> HotkeyRegistrationResult:
        """Register a hotkey callback, returning conflict alternatives if needed."""

    def unregister(self, hotkey: str) -> None:
        """Unregister a previously registered hotkey."""

    def list_registered(self) -> tuple[str, ...]:
        """Return currently registered hotkeys in deterministic order."""


class InMemoryHotkeyBackend:
    """Deterministic hotkey backend used for unit-scope adapters/tests."""

    def __init__(self, *, blocked_hotkeys: set[str] | None = None) -> None:
        normalized_blocked = blocked_hotkeys or set()
        self._blocked_hotkeys = {normalize_hotkey(hotkey) for hotkey in normalized_blocked}
        self._callbacks: dict[str, HotkeyCallback] = {}

    def register(self, hotkey: str, callback: HotkeyCallback) -> HotkeyRegistrationResult:
        normalized = normalize_hotkey(hotkey)
        if normalized in self._callbacks or normalized in self._blocked_hotkeys:
            return HotkeyRegistrationResult(
                hotkey=normalized,
                registered=False,
                alternatives=self._suggest_alternatives(normalized),
            )

        self._callbacks[normalized] = callback
        return HotkeyRegistrationResult(hotkey=normalized, registered=True)

    def unregister(self, hotkey: str) -> None:
        normalized = normalize_hotkey(hotkey)
        self._callbacks.pop(normalized, None)

    def list_registered(self) -> tuple[str, ...]:
        return tuple(sorted(self._callbacks))

    def _suggest_alternatives(self, requested: str) -> tuple[str, ...]:
        unavailable = self._blocked_hotkeys | set(self._callbacks)
        requested_modifiers = _extract_modifiers(requested)
        candidate_sequences: list[tuple[str, ...]] = []

        if requested_modifiers:
            candidate_sequences.append(requested_modifiers)
        candidate_sequences.extend(
            [
                ("ctrl", "shift"),
                ("ctrl", "alt"),
                ("alt", "shift"),
            ]
        )

        seen: set[str] = set()
        suggestions: list[str] = []
        for modifiers in candidate_sequences:
            for key in _FALLBACK_KEYS:
                candidate = normalize_hotkey("+".join((*modifiers, key)))
                if candidate == requested or candidate in unavailable or candidate in seen:
                    continue
                seen.add(candidate)
                suggestions.append(candidate)
                if len(suggestions) == 3:
                    return tuple(suggestions)
        return tuple(suggestions)

    def trigger(self, hotkey: str) -> bool:
        """Invoke callback for a registered hotkey; returns False if missing."""

        normalized = normalize_hotkey(hotkey)
        callback = self._callbacks.get(normalized)
        if callback is None:
            return False
        callback()
        return True


def normalize_hotkey(hotkey: str) -> str:
    """Return canonical lowercase hotkey representation."""

    tokens = [_normalize_token(token) for token in hotkey.split("+")]
    if not tokens or any(token == "" for token in tokens):
        raise ValueError(f"invalid hotkey: {hotkey!r}")

    modifiers: list[str] = []
    keys: list[str] = []
    for token in tokens:
        if token in _MODIFIER_ORDER:
            if token not in modifiers:
                modifiers.append(token)
            continue
        if token not in keys:
            keys.append(token)

    modifiers.sort(key=_modifier_rank)
    keys.sort()
    return "+".join((*modifiers, *keys))


def _normalize_token(token: str) -> str:
    normalized = token.strip().lower()
    return _MODIFIER_ALIASES.get(normalized, normalized)


def _modifier_rank(token: str) -> int:
    return _MODIFIER_ORDER.index(token)


def _extract_modifiers(hotkey: str) -> tuple[str, ...]:
    tokens = hotkey.split("+")
    return tuple(token for token in tokens if token in _MODIFIER_ORDER)


__all__ = [
    "HotkeyBackend",
    "HotkeyCallback",
    "HotkeyRegistrationResult",
    "InMemoryHotkeyBackend",
    "normalize_hotkey",
]
