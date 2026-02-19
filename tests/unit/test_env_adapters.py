"""Unit tests for startup environment override parsing (E06-S08)."""

from __future__ import annotations

from pathlib import Path

import pytest

from voicekey.config.manager import ConfigError, parse_startup_env_overrides


def test_parse_startup_env_overrides_accepts_valid_values(tmp_path: Path) -> None:
    model_dir = tmp_path / "models"
    env = {
        "VOICEKEY_CONFIG": str(tmp_path / "voicekey.yaml"),
        "VOICEKEY_MODEL_DIR": str(model_dir),
        "VOICEKEY_LOG_LEVEL": "DeBuG",
        "VOICEKEY_DISABLE_TRAY": "yes",
    }

    overrides = parse_startup_env_overrides(env)

    assert overrides.config_path == Path(env["VOICEKEY_CONFIG"])
    assert overrides.model_dir == model_dir
    assert overrides.log_level == "debug"
    assert overrides.disable_tray is True


def test_parse_startup_env_overrides_rejects_invalid_log_level() -> None:
    with pytest.raises(ConfigError) as exc_info:
        parse_startup_env_overrides({"VOICEKEY_LOG_LEVEL": "verbose"})

    assert "Invalid VOICEKEY_LOG_LEVEL" in str(exc_info.value)


def test_parse_startup_env_overrides_rejects_invalid_disable_tray_boolean() -> None:
    with pytest.raises(ConfigError) as exc_info:
        parse_startup_env_overrides({"VOICEKEY_DISABLE_TRAY": "maybe"})

    assert "Invalid VOICEKEY_DISABLE_TRAY" in str(exc_info.value)


def test_parse_startup_env_overrides_rejects_model_dir_when_path_is_file(tmp_path: Path) -> None:
    model_file = tmp_path / "model.bin"
    model_file.write_text("not_a_directory", encoding="utf-8")

    with pytest.raises(ConfigError) as exc_info:
        parse_startup_env_overrides({"VOICEKEY_MODEL_DIR": str(model_file)})

    assert "Invalid VOICEKEY_MODEL_DIR" in str(exc_info.value)
