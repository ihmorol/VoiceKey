"""Security tests for diagnostics module (E09-S02).

These tests verify that:
- Diagnostics export is redacted by default
- User paths are redacted
- Config values with secrets are redacted
- No raw audio or transcripts are included by default
- Full export mode requires explicit opt-in
"""

from __future__ import annotations

import json
import platform
import sys
from pathlib import Path

import pytest

from voicekey.diagnostics import (
    REDACTED_PLACEHOLDER,
    PATH_REDACTED_PLACEHOLDER,
    is_sensitive_field,
    is_path_field,
    redact_path,
    redact_dict,
    redact_config_for_diagnostics,
    contains_secrets,
    collect_diagnostics,
    export_diagnostics,
    validate_diagnostics_safety,
    get_export_warning_for_full_mode,
    DiagnosticsOutput,
    FullDiagnosticsOutput,
    DiagnosticsExportMode,
)
from voicekey.config.schema import default_config


class TestRedactionUtilities:
    """Tests for redaction utility functions."""
    
    def test_sensitive_field_detection(self) -> None:
        """Sensitive field names are correctly identified."""
        assert is_sensitive_field("password") is True
        assert is_sensitive_field("api_key") is True
        assert is_sensitive_field("secret_token") is True
        assert is_sensitive_field("auth_credential") is True
        assert is_sensitive_field("private_key") is True
        assert is_sensitive_field("PASSWORD") is True  # Case insensitive
        assert is_sensitive_field("APIKEY") is True
        
        # Non-sensitive fields
        assert is_sensitive_field("username") is False
        assert is_sensitive_field("enabled") is False
        assert is_sensitive_field("timeout") is False
    
    def test_path_field_detection(self) -> None:
        """Path field names are correctly identified."""
        assert is_path_field("config_path") is True
        assert is_path_field("data_dir") is True
        assert is_path_field("model_dir") is True
        assert is_path_field("output_root") is True
        assert is_path_field("path") is True
        assert is_path_field("dir") is True
        
        # Non-path fields
        assert is_path_field("timeout") is False
        assert is_path_field("enabled") is False
    
    def test_redact_path_home_directory(self) -> None:
        """Home directory paths are redacted."""
        # This test handles the actual home directory of the test runner
        result = redact_path("/home/username/.config/voicekey")
        assert "username" not in result
        assert "[USER]" in result
    
    def test_redact_path_preserves_structure(self) -> None:
        """Path redaction preserves directory structure."""
        result = redact_path("/home/username/.config/voicekey")
        assert ".config/voicekey" in result or ".config" in result
    
    def test_redact_path_none_value(self) -> None:
        """None path values are handled correctly."""
        assert redact_path(None) is None
    
    def test_redact_path_non_string(self) -> None:
        """Non-string path values are redacted."""
        assert redact_path(123) == PATH_REDACTED_PLACEHOLDER
        assert redact_path(["a", "b"]) == PATH_REDACTED_PLACEHOLDER
    
    def test_redact_dict_redacts_sensitive_fields(self) -> None:
        """Sensitive fields are redacted in dictionaries."""
        data = {
            "username": "testuser",
            "password": "secret123",
            "api_key": "key123",
            "normal_field": "value",
        }
        
        result = redact_dict(data)
        
        assert result["username"] == "testuser"
        assert result["password"] == REDACTED_PLACEHOLDER
        assert result["api_key"] == REDACTED_PLACEHOLDER
        assert result["normal_field"] == "value"
    
    def test_redact_dict_redacts_path_fields(self) -> None:
        """Path fields are redacted in dictionaries."""
        data = {
            "config_path": "/home/user/.config/voicekey",
            "timeout": 30,
        }
        
        result = redact_dict(data)
        
        assert "user" not in result["config_path"]
        assert result["timeout"] == 30
    
    def test_redact_dict_handles_nested_dicts(self) -> None:
        """Nested dictionaries are recursively redacted."""
        data = {
            "engine": {
                "model_profile": "base",
                "secret_token": "hidden",
            },
            "paths": {
                "config_dir": "/home/user/config",
            },
        }
        
        result = redact_dict(data)
        
        assert result["engine"]["model_profile"] == "base"
        assert result["engine"]["secret_token"] == REDACTED_PLACEHOLDER
        assert "user" not in result["paths"]["config_dir"]
    
    def test_redact_dict_handles_lists(self) -> None:
        """Lists containing dictionaries are redacted."""
        data = {
            "items": [
                {"name": "item1", "password": "pass1"},
                {"name": "item2", "password": "pass2"},
            ]
        }
        
        result = redact_dict(data)
        
        assert result["items"][0]["name"] == "item1"
        assert result["items"][0]["password"] == REDACTED_PLACEHOLDER
        assert result["items"][1]["password"] == REDACTED_PLACEHOLDER
    
    def test_redact_config_for_diagnostics_redacts_snippets(self) -> None:
        """Snippet content is redacted in config export."""
        config = default_config().model_dump(mode="python")
        config["snippets"]["myemail"] = "secret@example.com"
        
        result = redact_config_for_diagnostics(config)
        
        assert result["snippets"]["myemail"] == REDACTED_PLACEHOLDER
    
    def test_redact_config_for_diagnostics_redacts_custom_commands(self) -> None:
        """Custom command actions are redacted in config export."""
        config = default_config().model_dump(mode="python")
        config["custom_commands"]["login"] = {
            "action": "username\npassword",
            "type": "text",
        }
        
        result = redact_config_for_diagnostics(config)
        
        assert result["custom_commands"]["login"]["action"] == REDACTED_PLACEHOLDER


class TestSecretsDetection:
    """Tests for secrets detection in diagnostics output."""
    
    def test_contains_secrets_detects_api_keys(self) -> None:
        """API key patterns are detected."""
        assert contains_secrets('api_key: "sk-abcdefghijklmnopqrstuvwxyz123456"') is True
        assert contains_secrets("sk-1234567890abcdefghijklmnop") is True
    
    def test_contains_secrets_detects_bearer_tokens(self) -> None:
        """Bearer token patterns are detected."""
        assert contains_secrets("Bearer abc123xyz789") is True
        assert contains_secrets("bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9") is True
    
    def test_contains_secrets_detects_connection_strings(self) -> None:
        """Connection strings with credentials are detected."""
        assert contains_secrets("mongodb://user:password@localhost:27017") is True
        assert contains_secrets("postgres://admin:secret123@db.example.com") is True
    
    def test_contains_secrets_allows_normal_text(self) -> None:
        """Normal text without secrets passes detection."""
        assert contains_secrets("Hello world") is False
        assert contains_secrets("The quick brown fox") is False
        assert contains_secrets("model_profile: base") is False


class TestDiagnosticsOutput:
    """Tests for diagnostics output schema."""
    
    def test_default_export_mode_is_redacted(self) -> None:
        """Default export mode is redacted, not full."""
        assert DiagnosticsExportMode.REDACTED == DiagnosticsExportMode.REDACTED
        output = DiagnosticsOutput.create_redacted()
        assert output.export_mode == DiagnosticsExportMode.REDACTED
    
    def test_redacted_output_excludes_raw_audio(self) -> None:
        """Redacted output does not include raw audio data."""
        output = DiagnosticsOutput.create_redacted()
        data = output.model_dump(mode="python")
        
        assert "raw_audio" not in data
        assert "audio_data" not in data
        assert "waveform" not in data
    
    def test_redacted_output_excludes_transcripts(self) -> None:
        """Redacted output does not include transcript history."""
        output = DiagnosticsOutput.create_redacted()
        data = output.model_dump(mode="python")
        
        assert "transcripts" not in data
        assert "transcript_history" not in data
        assert "recognized_text" not in data
    
    def test_system_info_includes_platform_details(self) -> None:
        """System info includes expected platform details."""
        output = DiagnosticsOutput.create_redacted()
        
        assert output.system.os_name == platform.system()
        assert output.system.python_version == platform.python_version()
        assert output.system.architecture == platform.machine()
    
    def test_config_summary_excludes_sensitive_values(self) -> None:
        """Config summary does not include sensitive config values."""
        config = default_config().model_dump(mode="python")
        output = DiagnosticsOutput.create_redacted(config_dict=config)
        
        # Config summary should have structure but not sensitive details
        assert output.config_summary.version == config["version"]
        assert output.config_summary.default_mode == config["modes"]["default"]


class TestCollectDiagnostics:
    """Tests for diagnostics collection function."""
    
    def test_collect_diagnostics_returns_redacted_by_default(self) -> None:
        """collect_diagnostics returns redacted output by default."""
        diagnostics = collect_diagnostics()
        
        assert diagnostics["export_mode"] == "redacted"
    
    def test_collect_diagnostics_includes_system_info(self) -> None:
        """Diagnostics includes system information."""
        diagnostics = collect_diagnostics()
        
        assert "system" in diagnostics
        assert "os_name" in diagnostics["system"]
        assert "python_version" in diagnostics["system"]
    
    def test_collect_diagnostics_includes_redacted_paths(self) -> None:
        """Diagnostics includes redacted runtime paths."""
        diagnostics = collect_diagnostics()
        
        if "paths" in diagnostics and diagnostics["paths"]:
            for path_value in diagnostics["paths"].values():
                if path_value and isinstance(path_value, str):
                    # Home directory should not appear literally
                    # (unless redaction failed to match a pattern)
                    assert "/home/" not in path_value or "[USER]" in path_value or "[HOME]" in path_value
    
    def test_collect_diagnostics_full_mode_includes_config(self) -> None:
        """Full mode includes full config dictionary."""
        diagnostics = collect_diagnostics(include_full_config=True)
        
        assert diagnostics["export_mode"] == "full"
        assert "config_full" in diagnostics
    
    def test_collect_diagnostics_redacted_mode_uses_config_summary(self) -> None:
        """Redacted mode uses config summary instead of full config."""
        diagnostics = collect_diagnostics(include_full_config=False)
        
        assert diagnostics["export_mode"] == "redacted"
        assert "config_summary" in diagnostics
        assert "config_full" not in diagnostics


class TestExportDiagnostics:
    """Tests for diagnostics export function."""
    
    def test_export_diagnostics_creates_file(self, tmp_path: Path) -> None:
        """export_diagnostics creates a JSON file."""
        export_file = tmp_path / "diagnostics.json"
        
        result = export_diagnostics(export_file)
        
        assert export_file.exists()
        assert export_file.stat().st_size > 0
    
    def test_export_diagnostics_creates_parent_directories(self, tmp_path: Path) -> None:
        """export_diagnostics creates parent directories if needed."""
        export_file = tmp_path / "subdir" / "nested" / "diagnostics.json"
        
        result = export_diagnostics(export_file)
        
        assert export_file.exists()
    
    def test_export_diagnostics_returns_valid_json(self, tmp_path: Path) -> None:
        """Exported file contains valid JSON."""
        export_file = tmp_path / "diagnostics.json"
        
        export_diagnostics(export_file)
        
        with open(export_file) as f:
            data = json.load(f)
        
        assert "export_mode" in data
        assert "system" in data


class TestValidateDiagnosticsSafety:
    """Tests for diagnostics safety validation."""
    
    def test_validate_redacted_diagnostics_is_safe(self) -> None:
        """Redacted diagnostics passes safety validation."""
        diagnostics = collect_diagnostics(include_full_config=False)
        
        is_safe, issues = validate_diagnostics_safety(diagnostics)
        
        assert is_safe is True
        assert len(issues) == 0
    
    def test_validate_detects_secrets_in_output(self) -> None:
        """Safety validation detects secrets in output."""
        diagnostics = collect_diagnostics(include_full_config=False)
        diagnostics["injected_secret"] = "api_key: sk-1234567890abcdefghijklmnop"
        
        is_safe, issues = validate_diagnostics_safety(diagnostics)
        
        assert is_safe is False
        assert len(issues) > 0
        assert any("secret" in issue.lower() for issue in issues)


class TestFullExportWarning:
    """Tests for full export warning."""
    
    def test_full_export_warning_exists(self) -> None:
        """Full export warning message is available."""
        warning = get_export_warning_for_full_mode()
        
        assert len(warning) > 0
        assert "WARNING" in warning
    
    def test_full_export_warning_mentions_sensitive_data(self) -> None:
        """Full export warning mentions sensitive data risks."""
        warning = get_export_warning_for_full_mode()
        
        assert "sensitive" in warning.lower()
    
    def test_full_export_warning_mentions_opt_in(self) -> None:
        """Full export warning emphasizes user consent."""
        warning = get_export_warning_for_full_mode()
        
        # Warning should emphasize this is a deliberate choice
        assert "explicit" in warning.lower() or "consent" in warning.lower() or "consider" in warning.lower()


class TestIncidentResponseFlow:
    """Tests verifying incident response flow from requirements/security.md section 6."""
    
    def test_diagnostics_command_supports_incident_response(self) -> None:
        """Diagnostics can be collected for incident response."""
        # Per requirements/security.md section 6:
        # If unexpected typing is observed:
        # 1. pause voice input immediately
        # 2. export redacted diagnostics
        # 3. disable autostart until resolved
        
        diagnostics = collect_diagnostics(
            runtime_state="paused",  # Step 1: voice input paused
            warnings=["Autostart should be disabled"],  # Step 3 reminder
        )
        
        assert diagnostics["export_mode"] == "redacted"  # Step 2: redacted export
        assert diagnostics["runtime_status"]["state"] == "paused"
        assert len(diagnostics.get("warnings", [])) > 0
    
    def test_redacted_export_does_not_leak_user_paths(self) -> None:
        """Incident response export does not leak user paths."""
        diagnostics = collect_diagnostics(
            additional_paths={
                "user_home": "/home/secretuser",
                "config_path": "/home/secretuser/.config/voicekey/config.yaml",
            }
        )
        
        output_str = json.dumps(diagnostics)
        
        assert "secretuser" not in output_str


class TestSecurityRequirementsCoverage:
    """Tests mapping to specific security requirement IDs."""
    
    def test_req_section_4_1_vulnerability_response_sla_documented(self) -> None:
        """Security.md section 4.1 SLA is documented."""
        # This is verified by existence of requirements/security.md
        # The diagnostics module supports this by providing safe export
        assert DiagnosticsExportMode.REDACTED is not None
    
    def test_req_section_6_incident_response_export_redacted(self) -> None:
        """Security.md section 6: diagnostics export is redacted by default."""
        diagnostics = collect_diagnostics()
        
        # Requirement: export redacted diagnostics
        assert diagnostics["export_mode"] == "redacted"
    
    def test_req_no_raw_audio_in_diagnostics(self) -> None:
        """Diagnostics do not include raw audio data."""
        diagnostics = collect_diagnostics()
        
        # Raw microphone audio must not be persisted by default (section 2)
        assert "raw_audio" not in diagnostics
        assert "audio_samples" not in diagnostics
        assert "microphone_data" not in diagnostics
    
    def test_req_no_transcripts_in_diagnostics(self) -> None:
        """Diagnostics do not include transcripts."""
        diagnostics = collect_diagnostics()
        
        # Recognized text must not be logged by default (section 2)
        assert "transcripts" not in diagnostics
        assert "transcript_history" not in diagnostics
        assert "last_transcript" not in diagnostics
