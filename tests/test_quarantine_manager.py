"""
Tests for Quarantine Manager functionality.
"""

import pytest
import sys
import os
import tempfile
import json

# Add the parent directory to the path so we can import clamav_gui
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clamav_gui.utils.quarantine_manager import QuarantineManager


class TestQuarantineManager:
    """Test cases for QuarantineManager class."""

    def test_manager_initialization(self):
        """Test that the quarantine manager can be initialized."""
        manager = QuarantineManager()
        assert manager is not None

    def test_quarantine_directory_creation(self, temp_dir):
        """Test that quarantine directory is created properly."""
        manager = QuarantineManager(str(temp_dir))

        # Check that quarantine directory exists
        quarantine_dir = os.path.join(temp_dir, 'quarantine')
        assert os.path.exists(quarantine_dir)
        assert os.path.isdir(quarantine_dir)

    def test_get_quarantine_stats_structure(self):
        """Test that get_quarantine_stats returns proper structure."""
        manager = QuarantineManager()

        stats = manager.get_quarantine_stats()
        assert isinstance(stats, dict)

        # Should have these keys
        expected_keys = ['total_quarantined', 'total_size_mb', 'threat_types', 'newest_file', 'oldest_file']
        for key in expected_keys:
            assert key in stats

    def test_list_quarantined_files_empty(self):
        """Test listing quarantined files in empty directory."""
        manager = QuarantineManager()

        files = manager.list_quarantined_files()
        assert isinstance(files, list)
        assert len(files) == 0

    def test_quarantine_file_metadata_structure(self, temp_dir):
        """Test quarantine file metadata structure."""
        manager = QuarantineManager(str(temp_dir))

        # Create a test metadata file
        metadata = {
            'original_filename': 'test.txt',
            'threat_name': 'Test.Virus',
            'file_size': 1024,
            'quarantine_date': '2025-01-01T00:00:00',
            'sha256': 'abc123'
        }

        metadata_file = os.path.join(temp_dir, 'quarantine', 'test.txt.json')
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f)

        # Test that the file is detected and parsed correctly
        files = manager.list_quarantined_files()
        assert len(files) == 1
        assert files[0]['original_filename'] == 'test.txt'
        assert files[0]['threat_name'] == 'Test.Virus'

    def test_export_quarantine_list(self, temp_dir):
        """Test exporting quarantine list to file."""
        manager = QuarantineManager(str(temp_dir))

        # Create test data
        metadata = {
            'original_filename': 'test.txt',
            'threat_name': 'Test.Virus',
            'file_size': 1024
        }

        metadata_file = os.path.join(temp_dir, 'quarantine', 'test.txt.json')
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f)

        # Test export
        export_file = os.path.join(temp_dir, 'export.json')
        success = manager.export_quarantine_list(export_file)

        assert success == True
        assert os.path.exists(export_file)

        # Verify exported content
        with open(export_file, 'r') as f:
            exported_data = json.load(f)

        assert isinstance(exported_data, list)
        assert len(exported_data) == 1
        assert exported_data[0]['original_filename'] == 'test.txt'
