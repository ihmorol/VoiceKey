"""Command-line interface for VoiceKey."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import click

from voicekey.config.manager import (
    ConfigError,
    parse_startup_env_overrides,
    resolve_runtime_paths,
)
from voicekey.ui.exit_codes import ExitCode
from voicekey.ui.onboarding import run_onboarding

REQUIRED_COMMANDS: tuple[str, ...] = (
    "setup",
    "start",
    "status",
    "devices",
    "commands",
    "config",
    "download",
    "calibrate",
    "diagnostics",
)

DEFAULT_CONFIG_VALUES: dict[str, str] = {
    "modes.default": "wake_word",
    "system.autostart_enabled": "false",
    "wake_word.sensitivity": "0.55",
    "vad.speech_threshold": "0.5",
}


def _emit_output(ctx: click.Context, command: str, result: dict[str, Any]) -> None:
    output_mode = ctx.obj["output"]
    payload = {
        "ok": True,
        "command": command,
        "result": result,
    }
    if output_mode == "json":
        click.echo(json.dumps(payload, sort_keys=True))
        return

    click.echo(f"{command}: ok")
    for key in sorted(result):
        value = result[key]
        if isinstance(value, (dict, list)):
            rendered_value = json.dumps(value, sort_keys=True)
        else:
            rendered_value = str(value)
        click.echo(f"{key}={rendered_value}")


def _validate_single_config_operation(
    get_key: str | None,
    set_value: str | None,
    reset_flag: bool,
    edit_flag: bool,
) -> str:
    selected = {
        "get": bool(get_key),
        "set": bool(set_value),
        "reset": reset_flag,
        "edit": edit_flag,
    }
    enabled = [name for name, is_enabled in selected.items() if is_enabled]
    if len(enabled) > 1:
        raise click.UsageError("Use only one config operation: --get, --set, --reset, or --edit.")
    return enabled[0] if enabled else "show"


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "--output",
    type=click.Choice(["text", "json"], case_sensitive=False),
    default="text",
    show_default=True,
    help="Output mode for command responses.",
)
@click.pass_context
def cli(ctx: click.Context, output: str) -> None:
    """VoiceKey command-line interface."""
    ctx.ensure_object(dict)
    ctx.obj["output"] = output.lower()


@cli.command("start")
@click.option("--daemon", is_flag=True, help="Start without terminal dashboard.")
@click.option("--config", "config_path", type=click.Path(), default=None)
@click.option("--portable", is_flag=True, help="Use local portable config/data paths.")
@click.option(
    "--portable-root",
    type=click.Path(file_okay=False),
    default=None,
    help="Root directory used by portable mode.",
)
@click.pass_context
def start_command(
    ctx: click.Context,
    daemon: bool,
    config_path: str | None,
    portable: bool,
    portable_root: str | None,
) -> None:
    """Start VoiceKey runtime contract (stub)."""
    try:
        startup_overrides = parse_startup_env_overrides()
    except ConfigError as exc:
        raise click.ClickException(str(exc)) from exc

    effective_config_path = config_path or startup_overrides.config_path
    runtime_paths = resolve_runtime_paths(
        explicit_config_path=effective_config_path,
        model_dir_override=startup_overrides.model_dir,
        portable_mode=portable,
        portable_root=Path(portable_root).expanduser() if portable_root is not None else None,
    )

    _emit_output(
        ctx,
        command="start",
        result={
            "accepted": True,
            "daemon": daemon,
            "config_path": config_path,
            "runtime_paths": {
                "config_path": str(runtime_paths.config_path),
                "data_dir": str(runtime_paths.data_dir),
                "model_dir": str(runtime_paths.model_dir),
                "portable_mode": runtime_paths.portable_mode,
            },
            "env_overrides": {
                "config_path": str(startup_overrides.config_path)
                if startup_overrides.config_path is not None
                else None,
                "model_dir": str(startup_overrides.model_dir)
                if startup_overrides.model_dir is not None
                else None,
                "log_level": startup_overrides.log_level,
                "disable_tray": startup_overrides.disable_tray,
            },
            "runtime": "not_implemented",
        },
    )


@cli.command("setup")
@click.option("--config", "config_path", type=click.Path(), default=None)
@click.option("--skip", is_flag=True, help="Skip onboarding and write safe defaults.")
@click.option("--device-id", type=int, default=None, help="Selected microphone device id.")
@click.option(
    "--wake-test-success/--wake-test-fail",
    "wake_test_success",
    default=True,
    help="Result of wake phrase verification step.",
)
@click.option("--hotkey", default="ctrl+shift+`", show_default=True)
@click.option("--autostart/--no-autostart", "autostart_enabled", default=False, show_default=True)
@click.pass_context
def setup_command(
    ctx: click.Context,
    config_path: str | None,
    skip: bool,
    device_id: int | None,
    wake_test_success: bool,
    hotkey: str,
    autostart_enabled: bool,
) -> None:
    """Run onboarding setup flow and persist selected values."""
    result = run_onboarding(
        config_path=config_path,
        skip=skip,
        selected_device_id=device_id,
        wake_phrase_verified=wake_test_success,
        toggle_hotkey=hotkey,
        autostart_enabled=autostart_enabled,
    )
    _emit_output(
        ctx,
        command="setup",
        result={
            "completed": result.completed,
            "skipped": result.skipped,
            "persisted": result.persisted,
            "config_path": str(result.config_path),
            "selected_device_id": result.selected_device_id,
            "wake_phrase_verified": result.wake_phrase_verified,
            "toggle_hotkey": result.toggle_hotkey,
            "autostart_enabled": result.autostart_enabled,
            "completed_steps": list(result.completed_steps),
            "skipped_steps": list(result.skipped_steps),
            "tutorial_script": list(result.tutorial_script),
            "keyboard_interaction_map": {
                key: list(value) for key, value in result.keyboard_interaction_map.items()
            },
            "duration_seconds": result.duration_seconds,
            "within_target": result.within_target,
            "errors": list(result.errors),
        },
    )


@cli.command("status")
@click.pass_context
def status_command(ctx: click.Context) -> None:
    """Show runtime status contract (stub)."""
    _emit_output(
        ctx,
        command="status",
        result={
            "runtime_state": "stub",
            "listening_mode": "stub",
            "model_status": "not_downloaded",
        },
    )


@cli.command("devices")
@click.pass_context
def devices_command(ctx: click.Context) -> None:
    """List microphone devices contract (stub)."""
    _emit_output(
        ctx,
        command="devices",
        result={
            "devices": [],
            "selected_device_id": None,
            "probe": "not_implemented",
        },
    )


@cli.command("commands")
@click.pass_context
def commands_command(ctx: click.Context) -> None:
    """List supported CLI commands for contract verification."""
    _emit_output(
        ctx,
        command="commands",
        result={
            "supported": list(REQUIRED_COMMANDS),
        },
    )


@cli.command("download")
@click.option("--force", is_flag=True, help="Force model redownload.")
@click.pass_context
def download_command(ctx: click.Context, force: bool) -> None:
    """Run model download contract (stub)."""
    _emit_output(
        ctx,
        command="download",
        result={
            "requested": True,
            "force": force,
            "status": "not_implemented",
        },
    )


@cli.command("calibrate")
@click.pass_context
def calibrate_command(ctx: click.Context) -> None:
    """Run calibration contract (stub)."""
    _emit_output(
        ctx,
        command="calibrate",
        result={
            "requested": True,
            "status": "not_implemented",
        },
    )


@cli.command("diagnostics")
@click.option("--export", "export_path", type=click.Path(), default=None)
@click.pass_context
def diagnostics_command(ctx: click.Context, export_path: str | None) -> None:
    """Run diagnostics contract (stub)."""
    _emit_output(
        ctx,
        command="diagnostics",
        result={
            "requested": True,
            "export_path": export_path,
            "status": "not_implemented",
        },
    )


@cli.command("config")
@click.option("--get", "get_key", type=str, default=None)
@click.option("--set", "set_value", type=str, default=None)
@click.option("--reset", "reset_flag", is_flag=True)
@click.option("--edit", "edit_flag", is_flag=True)
@click.pass_context
def config_command(
    ctx: click.Context,
    get_key: str | None,
    set_value: str | None,
    reset_flag: bool,
    edit_flag: bool,
) -> None:
    """Config command contract for get/set/reset/edit operations."""
    operation = _validate_single_config_operation(get_key, set_value, reset_flag, edit_flag)

    if operation == "get":
        assert get_key is not None
        _emit_output(
            ctx,
            command="config",
            result={
                "operation": "get",
                "key": get_key,
                "value": DEFAULT_CONFIG_VALUES.get(get_key),
                "found": get_key in DEFAULT_CONFIG_VALUES,
                "source": "deterministic_stub",
            },
        )
        return

    if operation == "set":
        assert set_value is not None
        if "=" not in set_value:
            raise click.UsageError("--set expects KEY=VALUE format.")
        key, value = set_value.split("=", 1)
        if not key:
            raise click.UsageError("--set expects non-empty key in KEY=VALUE format.")
        _emit_output(
            ctx,
            command="config",
            result={
                "operation": "set",
                "key": key,
                "value": value,
                "persisted": False,
                "status": "contract_only",
            },
        )
        return

    if operation == "reset":
        _emit_output(
            ctx,
            command="config",
            result={
                "operation": "reset",
                "persisted": False,
                "status": "contract_only",
            },
        )
        return

    if operation == "edit":
        _emit_output(
            ctx,
            command="config",
            result={
                "operation": "edit",
                "editor_spawned": False,
                "status": "contract_only",
            },
        )
        return

    _emit_output(
        ctx,
        command="config",
        result={
            "operation": "show",
            "status": "contract_only",
            "path": "not_implemented",
        },
    )


def run(argv: Sequence[str] | None = None) -> int:
    """Execute CLI and return deterministic process exit code."""
    args = list(argv) if argv is not None else None
    try:
        cli.main(args=args, prog_name="voicekey", standalone_mode=False)
        return int(ExitCode.SUCCESS)
    except click.UsageError as exc:
        exc.show()
        return int(ExitCode.USAGE_ERROR)
    except click.ClickException as exc:
        exc.show()
        return int(ExitCode.COMMAND_ERROR)
    except click.Abort:
        click.echo("Aborted.", err=True)
        return int(ExitCode.RUNTIME_ERROR)
    except click.exceptions.Exit as exc:
        return int(exc.exit_code)


def main() -> None:
    """Script entrypoint used by packaging metadata."""
    raise SystemExit(run())
