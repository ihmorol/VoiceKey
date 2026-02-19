"""Integration smoke coverage for portable CLI startup contract (E06-S07)."""

from __future__ import annotations

import json

from click.testing import CliRunner

from voicekey.ui.cli import cli
from voicekey.ui.exit_codes import ExitCode


def test_portable_start_smoke_returns_local_runtime_paths(tmp_path) -> None:
    runner = CliRunner()
    portable_root = tmp_path / "portable"

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
    assert payload["command"] == "start"
    assert payload["result"]["runtime_paths"]["portable_mode"] is True
    assert payload["result"]["runtime_paths"]["config_path"] == str(
        portable_root / "config" / "config.yaml"
    )
