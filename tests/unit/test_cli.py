"""Unit tests for CLI command contract (E05-S01)."""

from __future__ import annotations

import json

from click.testing import CliRunner

from voicekey.ui.cli import cli
from voicekey.ui.exit_codes import ExitCode


def test_help_includes_required_commands() -> None:
    runner = CliRunner()

    result = runner.invoke(cli, ["--help"])

    assert result.exit_code == ExitCode.SUCCESS
    for command_name in [
        "setup",
        "start",
        "status",
        "devices",
        "commands",
        "config",
        "download",
        "calibrate",
        "diagnostics",
    ]:
        assert command_name in result.output


def test_required_commands_smoke(tmp_path) -> None:
    runner = CliRunner()

    setup_config = tmp_path / "voicekey-test-config.yaml"

    command_args = [
        ["setup", "--skip", "--config", str(setup_config)],
        ["start"],
        ["status"],
        ["devices"],
        ["commands"],
        ["config"],
        ["download"],
        ["calibrate"],
        ["diagnostics"],
    ]

    for args in command_args:
        result = runner.invoke(cli, args)
        assert result.exit_code == ExitCode.SUCCESS


def test_json_output_shape_is_deterministic() -> None:
    runner = CliRunner()

    result = runner.invoke(cli, ["--output", "json", "status"])

    assert result.exit_code == ExitCode.SUCCESS
    payload = json.loads(result.output)
    assert payload == {
        "ok": True,
        "command": "status",
        "result": {
            "runtime_state": "stub",
            "listening_mode": "stub",
            "model_status": "not_downloaded",
        },
    }


def test_unknown_command_returns_deterministic_usage_error_exit_code() -> None:
    runner = CliRunner()

    result = runner.invoke(cli, ["does-not-exist"])

    assert result.exit_code == ExitCode.USAGE_ERROR


def test_invalid_arguments_return_deterministic_usage_error_exit_code() -> None:
    runner = CliRunner()

    result = runner.invoke(cli, ["config", "--set", "missing_equals_sign"])

    assert result.exit_code == ExitCode.USAGE_ERROR


def test_setup_json_output_includes_required_onboarding_fields(tmp_path) -> None:
    runner = CliRunner()
    config_path = tmp_path / "voicekey" / "config.yaml"

    result = runner.invoke(
        cli,
        [
            "--output",
            "json",
            "setup",
            "--config",
            str(config_path),
            "--device-id",
            "3",
            "--wake-test-success",
            "--autostart",
        ],
    )

    assert result.exit_code == ExitCode.SUCCESS
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["command"] == "setup"
    assert payload["result"]["completed"] is True
    assert payload["result"]["persisted"] is True
    assert payload["result"]["selected_device_id"] == 3
    assert payload["result"]["skipped_steps"] == []
    assert "welcome_privacy" in payload["result"]["keyboard_interaction_map"]


def test_start_command_returns_command_error_for_invalid_env_override() -> None:
    runner = CliRunner()

    result = runner.invoke(cli, ["start"], env={"VOICEKEY_LOG_LEVEL": "verbose"})

    assert result.exit_code == ExitCode.COMMAND_ERROR


def test_start_command_supports_portable_mode_runtime_paths(tmp_path) -> None:
    runner = CliRunner()
    portable_root = tmp_path / "portable-root"

    result = runner.invoke(
        cli,
        [
            "--output",
            "json",
            "start",
            "--portable",
            "--portable-root",
            str(portable_root),
        ],
    )

    assert result.exit_code == ExitCode.SUCCESS
    payload = json.loads(result.output)
    runtime_paths = payload["result"]["runtime_paths"]
    assert runtime_paths["portable_mode"] is True
    assert runtime_paths["config_path"] == str(portable_root / "config" / "config.yaml")
    assert runtime_paths["data_dir"] == str(portable_root / "data")
    assert runtime_paths["model_dir"] == str(portable_root / "data" / "models")


def test_start_command_uses_env_config_override_for_runtime_paths(tmp_path) -> None:
    runner = CliRunner()
    env_config = tmp_path / "env" / "config.yaml"

    result = runner.invoke(
        cli,
        ["--output", "json", "start"],
        env={"VOICEKEY_CONFIG": str(env_config)},
    )

    assert result.exit_code == ExitCode.SUCCESS
    payload = json.loads(result.output)
    runtime_paths = payload["result"]["runtime_paths"]
    assert runtime_paths["portable_mode"] is False
    assert runtime_paths["config_path"] == str(env_config)
    assert runtime_paths["data_dir"] == str(env_config.parent)
