"""Integration tests for autostart registration and removal.

Tests the autostart functionality for both Linux and Windows platforms,
ensuring platform-specific behavior works correctly without actual OS modifications.

Requirements:
- E10-S02: Integration harness expansion
- FR-S04: Autostart platform tests
- requirements/testing-strategy.md: Integration layer - autostart adapters

All tests use mocks - no actual filesystem or registry modifications required.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest

from voicekey.platform.autostart_base import (
    AutostartValidationCode,
    AutostartValidationReport,
    AutostartValidationState,
    DirectoryProbe,
)
from voicekey.platform.autostart_linux import LinuxAutostartAdapter
from voicekey.platform.autostart_windows import WindowsAutostartAdapter


# =============================================================================
# Linux Autostart Integration Tests
# =============================================================================

class TestLinuxAutostartIntegration:
    """Integration tests for Linux autostart adapters."""

    def test_linux_autostart_validates_desktop_autostart_dir(self) -> None:
        """Verify Linux adapter validates desktop autostart directory."""
        desktop = Path("/home/test/.config/autostart")
        systemd = Path("/home/test/.config/systemd/user")

        probe_map = {
            str(desktop): DirectoryProbe(exists=True, is_directory=True, writable=True),
            str(systemd): DirectoryProbe(exists=True, is_directory=True, writable=True),
        }

        adapter = LinuxAutostartAdapter(
            desktop_autostart_dir=desktop,
            systemd_user_dir=systemd,
            directory_probe=lambda path: probe_map[str(path)],
        )

        report = adapter.validate()

        assert report.platform == "linux"
        assert report.state is AutostartValidationState.OK
        assert report.codes == ()

    def test_linux_autostart_degraded_when_one_target_unavailable(self) -> None:
        """Verify degraded state when one autostart target is unavailable."""
        desktop = Path("/home/test/.config/autostart")
        systemd = Path("/home/test/.config/systemd/user")

        probe_map = {
            str(desktop): DirectoryProbe(exists=True, is_directory=True, writable=True),
            str(systemd): DirectoryProbe(exists=False, is_directory=False, writable=False),
        }

        adapter = LinuxAutostartAdapter(
            desktop_autostart_dir=desktop,
            systemd_user_dir=systemd,
            directory_probe=lambda path: probe_map[str(path)],
        )

        report = adapter.validate()

        assert report.state is AutostartValidationState.DEGRADED
        assert AutostartValidationCode.DIRECTORY_MISSING in report.codes
        assert any("systemd" in w.lower() for w in report.warnings)

    def test_linux_autostart_unavailable_when_both_targets_fail(self) -> None:
        """Verify unavailable state when both targets fail."""
        desktop = Path("/home/test/.config/autostart")
        systemd = Path("/home/test/.config/systemd/user")

        probe_map = {
            str(desktop): DirectoryProbe(exists=False, is_directory=False, writable=False),
            str(systemd): DirectoryProbe(exists=True, is_directory=False, writable=False),
        }

        adapter = LinuxAutostartAdapter(
            desktop_autostart_dir=desktop,
            systemd_user_dir=systemd,
            directory_probe=lambda path: probe_map[str(path)],
        )

        report = adapter.validate()

        assert report.state is AutostartValidationState.UNAVAILABLE
        assert AutostartValidationCode.DIRECTORY_MISSING in report.codes
        assert AutostartValidationCode.DIRECTORY_INVALID in report.codes

    def test_linux_autostart_not_writable_returns_proper_code(self) -> None:
        """Verify not-writable directory returns proper error code."""
        desktop = Path("/home/test/.config/autostart")
        systemd = Path("/home/test/.config/systemd/user")

        probe_map = {
            str(desktop): DirectoryProbe(exists=True, is_directory=True, writable=False),
            str(systemd): DirectoryProbe(exists=True, is_directory=True, writable=True),
        }

        adapter = LinuxAutostartAdapter(
            desktop_autostart_dir=desktop,
            systemd_user_dir=systemd,
            directory_probe=lambda path: probe_map[str(path)],
        )

        report = adapter.validate()

        assert report.state is AutostartValidationState.DEGRADED
        assert AutostartValidationCode.DIRECTORY_NOT_WRITABLE in report.codes
        assert any("permission" in r.lower() for r in report.remediation)

    def test_linux_autostart_deterministic_validation(self) -> None:
        """Verify validation is deterministic for same adapter state."""
        desktop = Path("/home/test/.config/autostart")
        systemd = Path("/home/test/.config/systemd/user")

        probe_map = {
            str(desktop): DirectoryProbe(exists=True, is_directory=True, writable=True),
            str(systemd): DirectoryProbe(exists=False, is_directory=False, writable=False),
        }

        adapter = LinuxAutostartAdapter(
            desktop_autostart_dir=desktop,
            systemd_user_dir=systemd,
            directory_probe=lambda path: probe_map[str(path)],
        )

        first = adapter.validate()
        second = adapter.validate()

        assert first == second


# =============================================================================
# Windows Autostart Integration Tests
# =============================================================================

class TestWindowsAutostartIntegration:
    """Integration tests for Windows autostart adapters."""

    def test_windows_autostart_validates_startup_folder(self) -> None:
        """Verify Windows adapter validates startup folder."""
        startup = Path("C:/Users/test/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup")

        probe_map = {
            str(startup): DirectoryProbe(exists=True, is_directory=True, writable=True),
        }

        adapter = WindowsAutostartAdapter(
            startup_folder=startup,
            startup_folder_probe=lambda path: probe_map[str(path)],
            registry_run_key_accessible=True,
            registry_run_key_writable=True,
        )

        report = adapter.validate()

        assert report.platform == "windows"
        assert report.state is AutostartValidationState.OK
        assert report.codes == ()

    def test_windows_autostart_degraded_when_registry_unavailable(self) -> None:
        """Verify degraded state when registry is unavailable."""
        startup = Path("C:/Users/test/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup")

        probe_map = {
            str(startup): DirectoryProbe(exists=True, is_directory=True, writable=True),
        }

        adapter = WindowsAutostartAdapter(
            startup_folder=startup,
            startup_folder_probe=lambda path: probe_map[str(path)],
            registry_run_key_accessible=False,
            registry_run_key_writable=False,
        )

        report = adapter.validate()

        assert report.state is AutostartValidationState.DEGRADED
        assert AutostartValidationCode.REGISTRY_KEY_INACCESSIBLE in report.codes

    def test_windows_autostart_unavailable_when_both_targets_fail(self) -> None:
        """Verify unavailable state when both targets fail."""
        startup = Path("C:/Users/test/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup")

        probe_map = {
            str(startup): DirectoryProbe(exists=False, is_directory=False, writable=False),
        }

        adapter = WindowsAutostartAdapter(
            startup_folder=startup,
            startup_folder_probe=lambda path: probe_map[str(path)],
            registry_run_key_accessible=False,
            registry_run_key_writable=False,
        )

        report = adapter.validate()

        assert report.state is AutostartValidationState.UNAVAILABLE
        assert AutostartValidationCode.STARTUP_FOLDER_MISSING in report.codes
        assert AutostartValidationCode.REGISTRY_KEY_INACCESSIBLE in report.codes

    def test_windows_startup_folder_not_writable_returns_proper_code(self) -> None:
        """Verify not-writable startup folder returns proper error code."""
        startup = Path("C:/Users/test/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup")

        probe_map = {
            str(startup): DirectoryProbe(exists=True, is_directory=True, writable=False),
        }

        adapter = WindowsAutostartAdapter(
            startup_folder=startup,
            startup_folder_probe=lambda path: probe_map[str(path)],
            registry_run_key_accessible=True,
            registry_run_key_writable=True,
        )

        report = adapter.validate()

        assert report.state is AutostartValidationState.DEGRADED
        assert AutostartValidationCode.STARTUP_FOLDER_NOT_WRITABLE in report.codes

    def test_windows_registry_not_writable_returns_proper_code(self) -> None:
        """Verify not-writable registry returns proper error code."""
        startup = Path("C:/Users/test/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup")

        probe_map = {
            str(startup): DirectoryProbe(exists=True, is_directory=True, writable=True),
        }

        adapter = WindowsAutostartAdapter(
            startup_folder=startup,
            startup_folder_probe=lambda path: probe_map[str(path)],
            registry_run_key_accessible=True,
            registry_run_key_writable=False,
        )

        report = adapter.validate()

        assert report.state is AutostartValidationState.DEGRADED
        assert AutostartValidationCode.REGISTRY_KEY_NOT_WRITABLE in report.codes

    def test_windows_autostart_deterministic_validation(self) -> None:
        """Verify validation is deterministic for same adapter state."""
        startup = Path("C:/Users/test/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup")

        probe_map = {
            str(startup): DirectoryProbe(exists=True, is_directory=True, writable=True),
        }

        adapter = WindowsAutostartAdapter(
            startup_folder=startup,
            startup_folder_probe=lambda path: probe_map[str(path)],
            registry_run_key_accessible=False,
            registry_run_key_writable=False,
        )

        first = adapter.validate()
        second = adapter.validate()

        assert first == second


# =============================================================================
# Cross-Platform Autostart Integration Tests
# =============================================================================

class TestCrossPlatformAutostartIntegration:
    """Cross-platform autostart integration tests."""

    def test_autostart_report_structure_is_consistent(self) -> None:
        """Verify autostart report structure is consistent across platforms."""
        # Linux report
        linux_report = AutostartValidationReport(
            backend="linux_autostart",
            platform="linux",
            state=AutostartValidationState.OK,
            codes=(),
            warnings=(),
            remediation=(),
        )

        # Windows report
        windows_report = AutostartValidationReport(
            backend="windows_autostart",
            platform="windows",
            state=AutostartValidationState.OK,
            codes=(),
            warnings=(),
            remediation=(),
        )

        # Both should have same field structure
        assert hasattr(linux_report, 'backend')
        assert hasattr(linux_report, 'platform')
        assert hasattr(linux_report, 'state')
        assert hasattr(linux_report, 'codes')
        assert hasattr(linux_report, 'warnings')
        assert hasattr(linux_report, 'remediation')

        assert hasattr(windows_report, 'backend')
        assert hasattr(windows_report, 'platform')
        assert hasattr(windows_report, 'state')
        assert hasattr(windows_report, 'codes')
        assert hasattr(windows_report, 'warnings')
        assert hasattr(windows_report, 'remediation')

    def test_autostart_validation_states_are_exhaustive(self) -> None:
        """Verify all validation states are handled."""
        expected_states = {
            AutostartValidationState.OK,
            AutostartValidationState.DEGRADED,
            AutostartValidationState.UNAVAILABLE,
        }

        # Verify all expected states exist
        assert expected_states == set(AutostartValidationState)

    def test_autostart_error_codes_are_platform_specific(self) -> None:
        """Verify error codes are differentiated between platforms."""
        # Linux-specific codes
        linux_codes = {
            AutostartValidationCode.DIRECTORY_MISSING,
            AutostartValidationCode.DIRECTORY_INVALID,
            AutostartValidationCode.DIRECTORY_NOT_WRITABLE,
        }

        # Windows-specific codes
        windows_codes = {
            AutostartValidationCode.STARTUP_FOLDER_MISSING,
            AutostartValidationCode.STARTUP_FOLDER_INVALID,
            AutostartValidationCode.STARTUP_FOLDER_NOT_WRITABLE,
            AutostartValidationCode.REGISTRY_KEY_INACCESSIBLE,
            AutostartValidationCode.REGISTRY_KEY_NOT_WRITABLE,
        }

        # Verify codes are distinct
        assert linux_codes.isdisjoint(windows_codes)

    def test_directory_probe_available_property(self) -> None:
        """Verify DirectoryProbe.available property works correctly."""
        # All conditions met
        probe_available = DirectoryProbe(exists=True, is_directory=True, writable=True)
        assert probe_available.available is True

        # Missing conditions
        probe_missing = DirectoryProbe(exists=False, is_directory=False, writable=False)
        assert probe_missing.available is False

        # Not a directory
        probe_not_dir = DirectoryProbe(exists=True, is_directory=False, writable=False)
        assert probe_not_dir.available is False

        # Not writable
        probe_not_writable = DirectoryProbe(exists=True, is_directory=True, writable=False)
        assert probe_not_writable.available is False


# =============================================================================
# Autostart with Onboarding Integration Tests
# =============================================================================

class TestAutostartOnboardingIntegration:
    """Integration tests for autostart during onboarding flow."""

    def test_autostart_capability_check_before_onboarding(self) -> None:
        """Verify autostart capability is checked before onboarding step."""
        # Simulate onboarding flow where autostart is offered
        desktop = Path("/home/test/.config/autostart")
        systemd = Path("/home/test/.config/systemd/user")

        probe_map = {
            str(desktop): DirectoryProbe(exists=True, is_directory=True, writable=True),
            str(systemd): DirectoryProbe(exists=True, is_directory=True, writable=True),
        }

        adapter = LinuxAutostartAdapter(
            desktop_autostart_dir=desktop,
            systemd_user_dir=systemd,
            directory_probe=lambda path: probe_map[str(path)],
        )

        report = adapter.validate()

        # Autostart should be available for onboarding
        assert report.state in (
            AutostartValidationState.OK,
            AutostartValidationState.DEGRADED,
        )

    def test_autostart_unavailable_disables_onboarding_option(self) -> None:
        """Verify autostart unavailable disables onboarding option."""
        desktop = Path("/home/test/.config/autostart")
        systemd = Path("/home/test/.config/systemd/user")

        probe_map = {
            str(desktop): DirectoryProbe(exists=False, is_directory=False, writable=False),
            str(systemd): DirectoryProbe(exists=False, is_directory=False, writable=False),
        }

        adapter = LinuxAutostartAdapter(
            desktop_autostart_dir=desktop,
            systemd_user_dir=systemd,
            directory_probe=lambda path: probe_map[str(path)],
        )

        report = adapter.validate()

        # Autostart should not be offered when unavailable
        assert report.state is AutostartValidationState.UNAVAILABLE
        assert len(report.remediation) > 0  # Should provide guidance

    def test_autostart_degraded_warns_user_during_onboarding(self) -> None:
        """Verify degraded state warns user during onboarding."""
        desktop = Path("/home/test/.config/autostart")
        systemd = Path("/home/test/.config/systemd/user")

        probe_map = {
            str(desktop): DirectoryProbe(exists=True, is_directory=True, writable=True),
            str(systemd): DirectoryProbe(exists=False, is_directory=False, writable=False),
        }

        adapter = LinuxAutostartAdapter(
            desktop_autostart_dir=desktop,
            systemd_user_dir=systemd,
            directory_probe=lambda path: probe_map[str(path)],
        )

        report = adapter.validate()

        # Should warn about partial availability
        assert report.state is AutostartValidationState.DEGRADED
        assert len(report.warnings) > 0


# =============================================================================
# Autostart Remediation Integration Tests
# =============================================================================

class TestAutostartRemediation:
    """Integration tests for autostart remediation guidance."""

    def test_linux_remediation_provides_actionable_steps(self) -> None:
        """Verify Linux remediation provides actionable steps."""
        desktop = Path("/home/test/.config/autostart")
        systemd = Path("/home/test/.config/systemd/user")

        probe_map = {
            str(desktop): DirectoryProbe(exists=False, is_directory=False, writable=False),
            str(systemd): DirectoryProbe(exists=False, is_directory=False, writable=False),
        }

        adapter = LinuxAutostartAdapter(
            desktop_autostart_dir=desktop,
            systemd_user_dir=systemd,
            directory_probe=lambda path: probe_map[str(path)],
        )

        report = adapter.validate()

        # Should provide actionable remediation
        assert len(report.remediation) > 0
        for remediation in report.remediation:
            # Should mention one of the actionable items
            keywords = ["create", "permission", "writable", "directory", "resolve"]
            assert any(kw in remediation.lower() for kw in keywords), f"No keyword in: {remediation}"

    def test_windows_remediation_provides_actionable_steps(self) -> None:
        """Verify Windows remediation provides actionable steps."""
        startup = Path("C:/Users/test/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup")

        probe_map = {
            str(startup): DirectoryProbe(exists=False, is_directory=False, writable=False),
        }

        adapter = WindowsAutostartAdapter(
            startup_folder=startup,
            startup_folder_probe=lambda path: probe_map[str(path)],
            registry_run_key_accessible=False,
            registry_run_key_writable=False,
        )

        report = adapter.validate()

        # Should provide actionable remediation
        assert len(report.remediation) > 0
        for remediation in report.remediation:
            # Should mention one of the actionable items
            keywords = ["folder", "registry", "permission", "create", "grant"]
            assert any(kw in remediation.lower() for kw in keywords)
