"""
Tests for version and utility functions.
"""

import pytest
from clamav_gui.version import get_version, get_version_info


class TestVersion:
    """Test cases for version functionality."""

    def test_get_version(self):
        """Test get_version function."""
        version = get_version()
        assert isinstance(version, str)
        assert len(version) > 0
        # Version should follow semantic versioning format
        parts = version.split('.')
        assert len(parts) >= 2  # Should have at least major.minor

    def test_get_version_info(self):
        """Test get_version_info function."""
        version_info = get_version_info()
        assert isinstance(version_info, dict)
        assert 'version' in version_info
        assert 'major' in version_info
        assert 'minor' in version_info
        assert 'patch' in version_info

        # Check that the version string matches the parsed components
        version = version_info['version']
        assert version == f"{version_info['major']}.{version_info['minor']}.{version_info['patch']}"
