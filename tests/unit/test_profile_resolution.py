"""Unit tests for per-app profile resolution and fallback merges (E06-S06)."""

from __future__ import annotations

from copy import deepcopy

from voicekey.config.profiles import ActiveAppIdentity, AppProfileResolver, resolve_effective_profile


def test_app_profile_resolver_matches_direct_profile_key() -> None:
    resolver = AppProfileResolver({"firefox": {"typing": {"char_delay_ms": 4}}})

    matched = resolver.resolve(ActiveAppIdentity(app_name="Firefox"))

    assert matched == "firefox"


def test_app_profile_resolver_matches_category_profile_from_identity_keywords() -> None:
    resolver = AppProfileResolver(
        {
            "browser": {"typing": {"char_delay_ms": 4}},
            "terminal": {"typing": {"char_delay_ms": 2}},
        }
    )

    matched = resolver.resolve(ActiveAppIdentity(app_name="Google Chrome"))

    assert matched == "browser"


def test_app_profile_resolver_returns_none_for_unknown_identity() -> None:
    resolver = AppProfileResolver({"browser": {"typing": {"char_delay_ms": 4}}})

    matched = resolver.resolve(ActiveAppIdentity(app_name="unknown app"))

    assert matched is None


def test_resolve_effective_profile_uses_fallback_when_no_app_specific_match() -> None:
    result = resolve_effective_profile(
        base_profile={"typing": {"char_delay_ms": 8}},
        fallback_profile={"typing": {"confidence_threshold": 0.4}},
        app_profiles={"browser": {"typing": {"char_delay_ms": 4}}},
        active_app=ActiveAppIdentity(app_name="unknown app"),
        enabled=True,
    )

    assert result.profile_key is None
    assert result.merged == {
        "typing": {
            "char_delay_ms": 8,
            "confidence_threshold": 0.4,
        }
    }


def test_resolve_effective_profile_applies_matching_override_merge() -> None:
    base_profile = {
        "typing": {
            "char_delay_ms": 8,
            "confidence_threshold": 0.5,
        },
        "features": {"text_expansion_enabled": False},
    }
    app_profiles = {
        "browser": {
            "typing": {"char_delay_ms": 3},
            "features": {"text_expansion_enabled": True},
        }
    }

    result = resolve_effective_profile(
        base_profile=base_profile,
        app_profiles=app_profiles,
        active_app=ActiveAppIdentity(app_name="Brave Browser"),
        enabled=True,
    )

    assert result.profile_key == "browser"
    assert result.merged == {
        "typing": {
            "char_delay_ms": 3,
            "confidence_threshold": 0.5,
        },
        "features": {"text_expansion_enabled": True},
    }


def test_resolve_effective_profile_does_not_mutate_inputs() -> None:
    base_profile = {"typing": {"char_delay_ms": 8}}
    app_profiles = {"editor": {"typing": {"char_delay_ms": 2}}}
    expected_base = deepcopy(base_profile)
    expected_profiles = deepcopy(app_profiles)

    resolve_effective_profile(
        base_profile=base_profile,
        app_profiles=app_profiles,
        active_app=ActiveAppIdentity(app_name="VSCode"),
        enabled=True,
    )

    assert base_profile == expected_base
    assert app_profiles == expected_profiles


def test_resolve_effective_profile_feature_gate_off_returns_base_only() -> None:
    result = resolve_effective_profile(
        base_profile={"typing": {"char_delay_ms": 8}},
        app_profiles={"browser": {"typing": {"char_delay_ms": 2}}},
        active_app=ActiveAppIdentity(app_name="Firefox"),
        enabled=False,
    )

    assert result.profile_key is None
    assert result.merged == {"typing": {"char_delay_ms": 8}}
