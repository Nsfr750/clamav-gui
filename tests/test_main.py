"""
Tests for main application functionality.
"""

import pytest
import sys
import os

# Add the parent directory to the path so we can import clamav_gui
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clamav_gui import __main__


class TestMainApplication:
    """Test cases for main application functionality."""

    def test_main_module_import(self):
        """Test that the main module can be imported without errors."""
        # This should not raise any ImportError
        import clamav_gui
        assert hasattr(clamav_gui, '__version__')

    def test_main_entry_point_exists(self):
        """Test that the main entry point exists."""
        assert hasattr(__main__, 'main')
        assert callable(__main__.main)

    def test_version_string_format(self):
        """Test that version string is properly formatted."""
        import clamav_gui
        version = clamav_gui.__version__

        assert isinstance(version, str)
        assert len(version) > 0

        # Should be semantic version format
        parts = version.split('.')
        assert len(parts) >= 2

        # Major and minor should be integers
        assert parts[0].isdigit()
        assert parts[1].isdigit()

    def test_package_structure(self):
        """Test that the package has the expected structure."""
        import clamav_gui

        # Should have these main modules
        expected_modules = [
            'lang',
            'ui',
            'utils',
            'main_window',
            'version'
        ]

        for module in expected_modules:
            assert hasattr(clamav_gui, module), f"Missing expected module: {module}"
