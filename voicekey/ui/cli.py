"""Command-line interface for VoiceKey."""

from __future__ import annotations

import json
import os
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import click
import yaml

from voicekey.config.manager import (
    backup_config,
    ConfigError,
    load_config,
    parse_startup_env_overrides,
    resolve_runtime_paths,
    save_config,
)
from voicekey.config.schema import default_config, validate_with_fallback
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


def _split_key_value(raw_set_value: str) -> tuple[str, str]:
    if "=" not in raw_set_value:
        raise click.UsageError("--set expects KEY=VALUE format.")
    key, value = raw_set_value.split("=", 1)
    key = key.strip()
    if not key:
        raise click.UsageError("--set expects non-empty key in KEY=VALUE format.")
    return key, value


def _get_nested_value(data: dict[str, Any], dotted_key: str) -> tuple[bool, Any]:
    current: Any = data
    for part in dotted_key.split("."):
        if not isinstance(current, dict) or part not in current:
            return False, None
        current = current[part]
    return True, current


def _set_nested_value(data: dict[str, Any], dotted_key: str, value: Any) -> None:
    parts = dotted_key.split(".")
    current = data
    for part in parts[:-1]:
        next_item = current.get(part)
        if not isinstance(next_item, dict):
            raise click.ClickException(
                f"Unsupported config key '{dotted_key}'. Use a valid dotted key path."
            )
        current = next_item

    final_key = parts[-1]
    if final_key not in current:
        raise click.ClickException(
            f"Unsupported config key '{dotted_key}'. Use a valid dotted key path."
        )
    current[final_key] = value


def _config_payload_for_show(config_data: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": config_data.get("version"),
        "engine.model_profile": config_data.get("engine", {}).get("model_profile"),
        "wake_word.phrase": config_data.get("wake_word", {}).get("phrase"),
        "wake_word.sensitivity": config_data.get("wake_word", {}).get("sensitivity"),
        "modes.inactivity_auto_pause_seconds": config_data.get("modes", {}).get(
            "inactivity_auto_pause_seconds"
        ),
        "typing.confidence_threshold": config_data.get("typing", {}).get("confidence_threshold"),
        "system.autostart_enabled": config_data.get("system", {}).get("autostart_enabled"),
        "privacy.telemetry_enabled": config_data.get("privacy", {}).get("telemetry_enabled"),
    }


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
@click.option("--export", "export_path", type=click.Path(), default=None, help="Export diagnostics to file.")
@click.option(
    "--full",
    "full_export",
    is_flag=True,
    default=False,
    help="WARNING: Include full config (may contain sensitive data). Use with caution.",
)
@click.pass_context
def diagnostics_command(ctx: click.Context, export_path: str | None, full_export: bool) -> None:
    """Collect and export VoiceKey diagnostics.
    
    By default, exports are REDACTED for privacy. Use --full only if you
    understand the security implications and consent to including potentially
    sensitive data.
    
    If unexpected typing is observed, follow the incident response procedure:
    1. Pause voice input immediately
    2. Export redacted diagnostics (this command without --full)
    3. Disable autostart until resolved
    """
    from pathlib import Path
    
    from voicekey.diagnostics import (
        collect_diagnostics,
        export_diagnostics,
        get_export_warning_for_full_mode,
        validate_diagnostics_safety,
    )
    
    if full_export:
        click.echo(get_export_warning_for_full_mode(), err=True)
        if not click.confirm("Continue with full export?", default=False):
            raise click.ClickException("Full export cancelled.")
    
    if export_path:
        diagnostics = export_diagnostics(
            export_path=Path(export_path),
            include_full_config=full_export,
        )
        result = {
            "exported": True,
            "export_path": export_path,
            "export_mode": "full" if full_export else "redacted",
            "safety_check": "passed" if validate_diagnostics_safety(diagnostics)[0] else "warning",
        }
    else:
        diagnostics = collect_diagnostics(include_full_config=full_export)
        result = {
            "exported": False,
            "export_mode": "full" if full_export else "redacted",
            "diagnostics": diagnostics,
            "safety_check": "passed" if validate_diagnostics_safety(diagnostics)[0] else "warning",
        }
    
    _emit_output(ctx, command="diagnostics", result=result)


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
    """Config command for get/set/reset/edit operations."""
    operation = _validate_single_config_operation(get_key, set_value, reset_flag, edit_flag)
    try:
        load_result = load_config()
    except ConfigError as exc:
        raise click.ClickException(str(exc)) from exc

    config_data = load_result.config.model_dump(mode="python")
    config_path = load_result.path
    load_warnings = list(load_result.warnings)

    if operation == "get":
        assert get_key is not None
        found, value = _get_nested_value(config_data, get_key)
        _emit_output(
            ctx,
            command="config",
            result={
                "operation": "get",
                "key": get_key,
                "value": value,
                "found": found,
                "path": str(config_path),
                "source": "file",
                "warnings": load_warnings,
            },
        )
        return

    if operation == "set":
        assert set_value is not None
        key, value_raw = _split_key_value(set_value)
        value = yaml.safe_load(value_raw)
        updated_data = load_result.config.model_dump(mode="python")
        _set_nested_value(updated_data, key, value)
        validated, validation_warnings = validate_with_fallback(updated_data)
        save_config(validated, config_path)

        found, persisted_value = _get_nested_value(validated.model_dump(mode="python"), key)
        _emit_output(
            ctx,
            command="config",
            result={
                "operation": "set",
                "key": key,
                "value": persisted_value if found else None,
                "persisted": True,
                "path": str(config_path),
                "warnings": load_warnings + list(validation_warnings),
            },
        )
        return

    if operation == "reset":
        backup_path = backup_config(config_path) if config_path.exists() else None
        defaults = default_config()
        save_config(defaults, config_path)
        _emit_output(
            ctx,
            command="config",
            result={
                "operation": "reset",
                "persisted": True,
                "path": str(config_path),
                "backup_path": str(backup_path) if backup_path is not None else None,
                "warnings": load_warnings,
            },
        )
        return

    if operation == "edit":
        editor = os.getenv("VISUAL") or os.getenv("EDITOR")
        click.edit(filename=str(config_path), editor=editor, require_save=False)
        _emit_output(
            ctx,
            command="config",
            result={
                "operation": "edit",
                "editor_spawned": True,
                "path": str(config_path),
                "editor": editor or "system_default",
                "warnings": load_warnings,
            },
        )
        return

    _emit_output(
        ctx,
        command="config",
        result={
            "operation": "show",
            "path": str(config_path),
            "values": _config_payload_for_show(config_data),
            "warnings": load_warnings,
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
