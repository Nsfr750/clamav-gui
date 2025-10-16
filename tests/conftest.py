"""
Pytest configuration and fixtures for ClamAV GUI tests.
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch

# Add the parent directory to the path so we can import clamav_gui
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def sample_language_manager():
    """Create a language manager for testing."""
    from clamav_gui.lang.lang_manager import SimpleLanguageManager
    return SimpleLanguageManager()


@pytest.fixture
def sample_clamav_validator():
    """Create a ClamAV validator for testing."""
    from clamav_gui.utils.clamav_validator import ClamAVValidator
    return ClamAVValidator()


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for testing."""
    return tmp_path


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication for GUI testing."""
    from PySide6.QtWidgets import QApplication

    if not QApplication.instance():
        app = QApplication([])
        yield app
        app.quit()
    else:
        yield QApplication.instance()


@pytest.fixture
def mock_clamav_process():
    """Mock ClamAV subprocess calls for testing."""
    with patch('subprocess.run') as mock_run:
        # Default mock for successful ClamAV operations
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = 'Mock ClamAV output'
        mock_process.stderr = ''
        mock_process.communicate.return_value = ('Mock ClamAV output', '')
        mock_run.return_value = mock_process
        yield mock_run


@pytest.fixture
def mock_clamav_not_installed():
    """Mock scenario where ClamAV is not installed."""
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = FileNotFoundError("clamscan not found")
        yield mock_run


@pytest.fixture
def mock_clamav_version_check():
    """Mock ClamAV version check response."""
    with patch('subprocess.run') as mock_run:
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = 'ClamAV 1.0.0/26985/Mon Jan 1 00:00:00 2025'
        mock_process.stderr = ''
        mock_run.return_value = mock_process
        yield mock_run


@pytest.fixture
def mock_scan_process():
    """Mock scan process for testing."""
    with patch('subprocess.run') as mock_run:
        # Mock a scan that finds some threats
        mock_process = Mock()
        mock_process.returncode = 1  # 1 indicates threats found
        mock_process.stdout = '''Scanning /test/file.txt
/test/file.txt: Test.Virus FOUND
/test/file.txt: Test.Trojan FOUND

----------- SCAN SUMMARY -----------
Infected files: 2
Time: 0.001 sec (0 m 0 s)
'''
        mock_process.stderr = ''
        mock_run.return_value = mock_process
        yield mock_run


@pytest.fixture
def performance_benchmark():
    """Create a benchmark fixture for performance testing."""
    return {}


@pytest.fixture
def gui_test_window(qapp):
    """Create a test window for GUI testing."""
    from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel

    class TestWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Test Window")
            self.setGeometry(100, 100, 400, 300)

            central_widget = QWidget()
            self.setCentralWidget(central_widget)

            layout = QVBoxLayout(central_widget)
            layout.addWidget(QLabel("Test GUI Component"))

    window = TestWindow()
    window.show()
    yield window
    window.close()
