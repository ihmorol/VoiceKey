"""Pytest fixtures for performance tests.

This conftest isolates performance tests from hardware dependencies.
"""

from __future__ import annotations

import sys
import unittest.mock as mock

# Mock hardware-dependent modules before any imports
sys.modules["sounddevice"] = mock.MagicMock()

import pytest


@pytest.fixture(autouse=True)
def mock_hardware_dependencies():
    """Automatically mock hardware dependencies for all perf tests."""
    # This ensures sounddevice is mocked for all tests
    pass
