"""Integration tests for rollback guidance automation hook script (E08-S03)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_generate_rollback_guidance_writes_json_and_incident_log(tmp_path: Path) -> None:
    output_json = tmp_path / "rollback" / "guidance.json"
    incident_log = tmp_path / "rollback" / "incident.md"

    project_root = Path(__file__).resolve().parents[2]
    script = project_root / "scripts" / "release" / "generate_rollback_guidance.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--version",
            "1.2.3",
            "--reason",
            "post-publish smoke failed",
            "--incident-log",
            str(incident_log),
            "--output-json",
            str(output_json),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert output_json.exists()
    assert incident_log.exists()

    guidance = json.loads(output_json.read_text(encoding="utf-8"))
    assert guidance["version"] == "1.2.3"
    assert "twine yank" in guidance["actions"]["pypi_yank"]

    log_text = incident_log.read_text(encoding="utf-8")
    assert "Release Rollback Incident" in log_text
    assert "post-publish smoke failed" in log_text
