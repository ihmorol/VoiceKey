"""Unit tests for Linux/Windows autostart validation adapters (E04-S03-T03)."""

from __future__ import annotations

from pathlib import Path

from voicekey.platform.autostart_base import (
    AutostartValidationCode,
    AutostartValidationState,
    DirectoryProbe,
)
from voicekey.platform.autostart_linux import LinuxAutostartAdapter
from voicekey.platform.autostart_windows import WindowsAutostartAdapter


def test_linux_validate_reports_ok_when_desktop_and_systemd_paths_are_writable() -> None:
    desktop = Path("/tmp/voicekey/.config/autostart")
    systemd = Path("/tmp/voicekey/.config/systemd/user")
    probe_map = {
        str(desktop): DirectoryProbe(exists=True, is_directory=True, writable=True),
        str(systemd): DirectoryProbe(exists=True, is_directory=True, writable=True),
    }

    backend = LinuxAutostartAdapter(
        desktop_autostart_dir=desktop,
        systemd_user_dir=systemd,
        directory_probe=lambda path: probe_map[str(path)],
    )

    report = backend.validate()

    assert report.platform == "linux"
    assert report.state is AutostartValidationState.OK
    assert report.codes == ()
    assert report.warnings == ()
    assert report.remediation == ()


def test_linux_validate_reports_degraded_when_only_one_target_is_available() -> None:
    desktop = Path("/tmp/voicekey/.config/autostart")
    systemd = Path("/tmp/voicekey/.config/systemd/user")
    probe_map = {
        str(desktop): DirectoryProbe(exists=True, is_directory=True, writable=True),
        str(systemd): DirectoryProbe(exists=True, is_directory=True, writable=False),
    }

    backend = LinuxAutostartAdapter(
        desktop_autostart_dir=desktop,
        systemd_user_dir=systemd,
        directory_probe=lambda path: probe_map[str(path)],
    )

    report = backend.validate()

    assert report.state is AutostartValidationState.DEGRADED
    assert AutostartValidationCode.DIRECTORY_NOT_WRITABLE in report.codes
    assert any("systemd" in warning.lower() for warning in report.warnings)
    assert any("permission" in message.lower() for message in report.remediation)


def test_linux_validate_reports_unavailable_when_no_targets_are_available() -> None:
    desktop = Path("/tmp/voicekey/.config/autostart")
    systemd = Path("/tmp/voicekey/.config/systemd/user")
    probe_map = {
        str(desktop): DirectoryProbe(exists=False, is_directory=False, writable=False),
        str(systemd): DirectoryProbe(exists=True, is_directory=False, writable=False),
    }

    backend = LinuxAutostartAdapter(
        desktop_autostart_dir=desktop,
        systemd_user_dir=systemd,
        directory_probe=lambda path: probe_map[str(path)],
    )

    report = backend.validate()

    assert report.state is AutostartValidationState.UNAVAILABLE
    assert AutostartValidationCode.DIRECTORY_MISSING in report.codes
    assert AutostartValidationCode.DIRECTORY_INVALID in report.codes
    assert any("create" in message.lower() for message in report.remediation)


def test_windows_validate_reports_ok_when_startup_folder_and_registry_are_available() -> None:
    startup = Path("C:/Users/test/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup")
    probe_map = {
        str(startup): DirectoryProbe(exists=True, is_directory=True, writable=True),
    }

    backend = WindowsAutostartAdapter(
        startup_folder=startup,
        startup_folder_probe=lambda path: probe_map[str(path)],
        registry_run_key_accessible=True,
        registry_run_key_writable=True,
    )

    report = backend.validate()

    assert report.platform == "windows"
    assert report.state is AutostartValidationState.OK
    assert report.codes == ()


def test_windows_validate_reports_degraded_when_registry_is_inaccessible() -> None:
    startup = Path("C:/Users/test/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup")
    probe_map = {
        str(startup): DirectoryProbe(exists=True, is_directory=True, writable=True),
    }

    backend = WindowsAutostartAdapter(
        startup_folder=startup,
        startup_folder_probe=lambda path: probe_map[str(path)],
        registry_run_key_accessible=False,
        registry_run_key_writable=False,
    )

    report = backend.validate()

    assert report.state is AutostartValidationState.DEGRADED
    assert AutostartValidationCode.REGISTRY_KEY_INACCESSIBLE in report.codes
    assert any("registry" in warning.lower() for warning in report.warnings)
    assert any("hkcu" in message.lower() for message in report.remediation)


def test_windows_validate_reports_unavailable_when_both_targets_fail() -> None:
    startup = Path("C:/Users/test/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup")
    probe_map = {
        str(startup): DirectoryProbe(exists=False, is_directory=False, writable=False),
    }

    backend = WindowsAutostartAdapter(
        startup_folder=startup,
        startup_folder_probe=lambda path: probe_map[str(path)],
        registry_run_key_accessible=False,
        registry_run_key_writable=False,
    )

    report = backend.validate()

    assert report.state is AutostartValidationState.UNAVAILABLE
    assert AutostartValidationCode.STARTUP_FOLDER_MISSING in report.codes
    assert AutostartValidationCode.REGISTRY_KEY_INACCESSIBLE in report.codes


def test_validate_is_deterministic_for_same_adapter_state() -> None:
    desktop = Path("/tmp/voicekey/.config/autostart")
    systemd = Path("/tmp/voicekey/.config/systemd/user")
    probe_map = {
        str(desktop): DirectoryProbe(exists=True, is_directory=True, writable=True),
        str(systemd): DirectoryProbe(exists=True, is_directory=True, writable=False),
    }

    backend = LinuxAutostartAdapter(
        desktop_autostart_dir=desktop,
        systemd_user_dir=systemd,
        directory_probe=lambda path: probe_map[str(path)],
    )

    first = backend.validate()
    second = backend.validate()

    assert first == second
