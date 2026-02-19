"""Unit tests for portable runtime path resolution (E06-S07)."""

from __future__ import annotations

from pathlib import Path

from voicekey.config.manager import resolve_runtime_paths


def test_resolve_runtime_paths_uses_local_paths_in_portable_mode(tmp_path: Path) -> None:
    portable_root = tmp_path / "portable"

    paths = resolve_runtime_paths(portable_mode=True, portable_root=portable_root)

    assert paths.portable_mode is True
    assert paths.config_path == portable_root / "config" / "config.yaml"
    assert paths.data_dir == portable_root / "data"
    assert paths.model_dir == portable_root / "data" / "models"


def test_resolve_runtime_paths_honors_explicit_config_in_portable_mode(tmp_path: Path) -> None:
    portable_root = tmp_path / "portable"
    explicit_config = tmp_path / "portable-config.yaml"

    paths = resolve_runtime_paths(
        portable_mode=True,
        portable_root=portable_root,
        explicit_config_path=explicit_config,
    )

    assert paths.config_path == explicit_config
    assert paths.data_dir == portable_root / "data"


def test_resolve_runtime_paths_keeps_non_portable_defaults(tmp_path: Path) -> None:
    env = {"APPDATA": str(tmp_path / "appdata")}

    paths = resolve_runtime_paths(env=env, platform_name="windows", home_dir=tmp_path)

    assert paths.portable_mode is False
    assert paths.config_path == Path(env["APPDATA"]) / "voicekey" / "config.yaml"
    assert paths.data_dir == Path(env["APPDATA"]) / "voicekey"
    assert paths.model_dir == Path(env["APPDATA"]) / "voicekey" / "models"


def test_resolve_runtime_paths_uses_env_config_override_outside_portable_mode(tmp_path: Path) -> None:
    env_config = tmp_path / "custom" / "config.yaml"
    env = {"VOICEKEY_CONFIG": str(env_config)}

    paths = resolve_runtime_paths(env=env, platform_name="linux", home_dir=tmp_path)

    assert paths.portable_mode is False
    assert paths.config_path == env_config
    assert paths.data_dir == env_config.parent
    assert paths.model_dir == env_config.parent / "models"


def test_resolve_runtime_paths_honors_model_dir_override_in_portable_mode(tmp_path: Path) -> None:
    portable_root = tmp_path / "portable"
    custom_model_dir = tmp_path / "shared-models"

    paths = resolve_runtime_paths(
        portable_mode=True,
        portable_root=portable_root,
        model_dir_override=custom_model_dir,
    )

    assert paths.config_path == portable_root / "config" / "config.yaml"
    assert paths.model_dir == custom_model_dir
