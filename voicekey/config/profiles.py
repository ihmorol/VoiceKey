"""Per-application profile resolution and override merge helpers."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ActiveAppIdentity:
    """Normalized active application identity descriptor."""

    app_name: str


@dataclass(frozen=True)
class ProfileResolutionResult:
    """Resolved profile metadata and merged override payload."""

    profile_key: str | None
    merged: dict[str, Any]


def resolve_effective_profile(
    *,
    base_profile: Mapping[str, Any],
    app_profiles: Mapping[str, Mapping[str, Any]] | None,
    active_app: ActiveAppIdentity | None,
    fallback_profile: Mapping[str, Any] | None = None,
    enabled: bool = False,
) -> ProfileResolutionResult:
    """Resolve and merge per-app profile override with deterministic fallback."""
    merged_base = _deep_merge(base_profile, fallback_profile or {})
    if not enabled or not app_profiles:
        return ProfileResolutionResult(profile_key=None, merged=merged_base)

    resolver = AppProfileResolver(app_profiles)
    profile_key = resolver.resolve(active_app)
    if profile_key is None:
        return ProfileResolutionResult(profile_key=None, merged=merged_base)

    return ProfileResolutionResult(
        profile_key=profile_key,
        merged=_deep_merge(merged_base, app_profiles[profile_key]),
    )


class AppProfileResolver:
    """Resolve active app identity to a profile key."""

    _EDITOR_KEYWORDS: tuple[str, ...] = (
        "code",
        "vscode",
        "pycharm",
        "idea",
        "sublime",
        "vim",
        "emacs",
    )
    _TERMINAL_KEYWORDS: tuple[str, ...] = (
        "terminal",
        "kitty",
        "alacritty",
        "wezterm",
        "xterm",
        "powershell",
        "cmd",
    )
    _BROWSER_KEYWORDS: tuple[str, ...] = (
        "chrome",
        "chromium",
        "firefox",
        "edge",
        "brave",
        "opera",
    )

    def __init__(self, app_profiles: Mapping[str, Mapping[str, Any]]) -> None:
        self._app_profiles = dict(app_profiles)
        self._normalized_lookup = {
            _normalize_key(profile_key): profile_key for profile_key in self._app_profiles
        }

    def resolve(self, active_app: ActiveAppIdentity | None) -> str | None:
        if active_app is None:
            return None

        normalized_name = _normalize_key(active_app.app_name)
        if not normalized_name:
            return None

        direct = self._normalized_lookup.get(normalized_name)
        if direct is not None:
            return direct

        category = _detect_category(normalized_name)
        if category is None:
            return None

        return self._normalized_lookup.get(category)


def _detect_category(normalized_name: str) -> str | None:
    if any(keyword in normalized_name for keyword in AppProfileResolver._EDITOR_KEYWORDS):
        return "editor"
    if any(keyword in normalized_name for keyword in AppProfileResolver._TERMINAL_KEYWORDS):
        return "terminal"
    if any(keyword in normalized_name for keyword in AppProfileResolver._BROWSER_KEYWORDS):
        return "browser"
    return None


def _normalize_key(value: str) -> str:
    return " ".join(value.strip().lower().split())


def _deep_merge(base: Mapping[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for key, value in base.items():
        if isinstance(value, Mapping):
            merged[key] = _deep_merge(value, {})
        else:
            merged[key] = value

    for key, value in override.items():
        existing = merged.get(key)
        if isinstance(existing, Mapping) and isinstance(value, Mapping):
            merged[key] = _deep_merge(existing, value)
        elif isinstance(value, Mapping):
            merged[key] = _deep_merge({}, value)
        else:
            merged[key] = value

    return merged


__all__ = [
    "ActiveAppIdentity",
    "AppProfileResolver",
    "ProfileResolutionResult",
    "resolve_effective_profile",
]
