"""
Tests for ClamAV validator utility functions.
"""

import pytest
import sys
import os

# Add the parent directory to the path so we can import clamav_gui
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clamav_gui.utils.clamav_validator import ClamAVValidator


class TestClamAVValidator:
    """Test cases for ClamAVValidator class."""

    def test_validator_initialization(self):
        """Test that the validator can be initialized."""
        validator = ClamAVValidator()
        assert validator is not None

    def test_find_clamscan_method_exists(self):
        """Test that find_clamscan method exists."""
        validator = ClamAVValidator()
        assert hasattr(validator, 'find_clamscan')
        assert callable(validator.find_clamscan)

    def test_check_clamav_installation_method_exists(self):
        """Test that check_clamav_installation method exists."""
        validator = ClamAVValidator()
        assert hasattr(validator, 'check_clamav_installation')
        assert callable(validator.check_clamav_installation)

    def test_get_installation_guidance_method_exists(self):
        """Test that get_installation_guidance method exists."""
        validator = ClamAVValidator()
        assert hasattr(validator, 'get_installation_guidance')
        assert callable(validator.get_installation_guidance)

    def test_find_clamscan_returns_string(self):
        """Test that find_clamscan returns a string or None."""
        validator = ClamAVValidator()
        result = validator.find_clamscan()
        assert result is None or isinstance(result, str)

    def test_check_clamav_installation_returns_tuple(self):
        """Test that check_clamav_installation returns a tuple."""
        validator = ClamAVValidator()
        result = validator.check_clamav_installation()
        assert isinstance(result, tuple)
        assert len(result) == 3  # (is_installed, status_msg, version_info)

    def test_get_installation_guidance_returns_string(self):
        """Test that get_installation_guidance returns a string."""
        validator = ClamAVValidator()
        result = validator.get_installation_guidance()
        assert isinstance(result, str)
        assert len(result) > 0
