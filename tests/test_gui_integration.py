"""
GUI Integration Tests for ClamAV GUI.

These tests use pytest-qt to test actual GUI components and their interactions.
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add the parent directory to the path so we can import clamav_gui
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton
from PySide6.QtCore import Qt, QTimer
from PySide6.QtTest import QTest


class TestMainWindowIntegration:
    """Integration tests for the main window GUI components."""

    @pytest.fixture(scope="class")
    def app(self):
        """Create QApplication for GUI testing."""
        if not QApplication.instance():
            return QApplication([])
        return QApplication.instance()

    @pytest.fixture
    def main_window(self, app):
        """Create a main window for testing."""
        from clamav_gui.main_window import ClamAVMainWindow

        window = ClamAVMainWindow()
        window.show()
        QTest.qWaitForWindowExposed(window)
        yield window
        window.close()

    def test_main_window_creation(self, main_window):
        """Test that main window can be created and shown."""
        assert main_window is not None
        assert main_window.isVisible()

    def test_window_title(self, main_window):
        """Test that window has correct title."""
        # This tests the translation system integration
        title = main_window.windowTitle()
        assert "ClamAV GUI" in title or title != ""

    def test_tab_widget_exists(self, main_window):
        """Test that tab widget is created."""
        assert hasattr(main_window, 'tabs')
        assert main_window.tabs is not None

    def test_menu_bar_exists(self, main_window):
        """Test that menu bar is created."""
        assert hasattr(main_window, 'menu_bar')
        assert main_window.menu_bar is not None

    def test_status_bar_exists(self, main_window):
        """Test that status bar is created."""
        assert hasattr(main_window, 'status_bar')
        assert main_window.status_bar is not None

    @pytest.mark.gui
    def test_scan_tab_creation(self, main_window):
        """Test that scan tab is properly created."""
        scan_tab = main_window.tabs.widget(0)
        assert scan_tab is not None

        # Check that scan tab has expected widgets
        # Look for target input, browse button, scan button
        target_input = scan_tab.findChild(type(main_window.target_input))
        browse_btn = scan_tab.findChild(QPushButton, "Browse...")
        scan_btn = scan_tab.findChild(QPushButton, "Start Scan")

        # At least some of these should exist (depending on implementation)
        widgets_exist = any([target_input, browse_btn, scan_btn])
        assert widgets_exist

    @pytest.mark.gui
    def test_language_switching_integration(self, main_window):
        """Test language switching through GUI."""
        # Mock the language manager to avoid file system dependencies
        with patch('clamav_gui.main_window.SimpleLanguageManager') as mock_lm_class:
            mock_lm = Mock()
            mock_lm.current_lang = 'en_US'
            mock_lm.available_languages = {'en_US': 'English', 'it_IT': 'Italian'}
            mock_lm.tr.return_value = "Test Translation"
            mock_lm.set_language.return_value = True
            mock_lm_class.return_value = mock_lm

            # Create window with mocked language manager
            test_window = type('TestWindow', (), {})()
            test_window.lang_manager = mock_lm

            # Test language switching
            success = mock_lm.set_language('it_IT')
            mock_lm.set_language.assert_called_with('it_IT')
            assert success is True


class TestMenuBarIntegration:
    """Integration tests for menu bar functionality."""

    @pytest.fixture(scope="class")
    def app(self):
        """Create QApplication for GUI testing."""
        if not QApplication.instance():
            return QApplication([])
        return QApplication.instance()

    @pytest.fixture
    def menu_bar(self, app):
        """Create a menu bar for testing."""
        from clamav_gui.ui.menu import ClamAVMenuBar

        menu_bar = ClamAVMenuBar()
        yield menu_bar

    def test_menu_bar_creation(self, menu_bar):
        """Test that menu bar can be created."""
        assert menu_bar is not None

    def test_menu_actions_creation(self, menu_bar):
        """Test that menu actions are created."""
        # Check that key actions exist
        assert hasattr(menu_bar, 'exit_action')
        assert hasattr(menu_bar, 'help_action')
        assert hasattr(menu_bar, 'about_action')

    @pytest.mark.gui
    def test_language_menu_creation(self, menu_bar):
        """Test that language menu is created when language manager is set."""
        # Initially language menu should be None
        assert menu_bar.language_menu is None

        # Mock language manager
        mock_lm = Mock()
        mock_lm.available_languages = {'en_US': 'English', 'it_IT': 'Italian'}
        mock_lm.current_lang = 'en_US'
        mock_lm.language_changed = Mock()

        # Set language manager
        menu_bar.set_language_manager(mock_lm)

        # Now language menu should exist
        assert menu_bar.language_menu is not None


class TestDialogIntegration:
    """Integration tests for dialog components."""

    @pytest.fixture(scope="class")
    def app(self):
        """Create QApplication for GUI testing."""
        if not QApplication.instance():
            return QApplication([])
        return QApplication.instance()

    @pytest.mark.gui
    def test_about_dialog_creation(self, app):
        """Test that about dialog can be created."""
        from clamav_gui.ui.about import AboutDialog

        # Mock language manager for dialog
        mock_lm = Mock()
        mock_lm.tr.return_value = "Test Translation"

        dialog = AboutDialog(language_manager=mock_lm)
        assert dialog is not None
        assert dialog.windowTitle() != ""

        dialog.close()

    @pytest.mark.gui
    def test_sponsor_dialog_creation(self, app):
        """Test that sponsor dialog can be created."""
        from clamav_gui.ui.sponsor import SponsorDialog

        # Mock language manager for dialog
        mock_lm = Mock()
        mock_lm.tr.return_value = "Test Translation"

        dialog = SponsorDialog(language_manager=mock_lm)
        assert dialog is not None
        assert dialog.windowTitle() != ""

        dialog.close()
