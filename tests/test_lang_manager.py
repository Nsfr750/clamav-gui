"""
Tests for the language manager functionality.
"""

import pytest
from clamav_gui.lang.lang_manager import SimpleLanguageManager


class TestSimpleLanguageManager:
    """Test cases for the SimpleLanguageManager class."""

    def test_initialization_default_language(self):
        """Test initialization with default language."""
        manager = SimpleLanguageManager()
        assert manager.current_lang == 'en_US'
        assert manager.default_lang == 'en_US'
        assert 'en_US' in manager.available_languages
        assert 'it_IT' in manager.available_languages

    def test_initialization_custom_language(self):
        """Test initialization with custom default language."""
        manager = SimpleLanguageManager(default_lang='it_IT')
        assert manager.current_lang == 'it_IT'
        assert manager.default_lang == 'it_IT'

    def test_language_fallback_on_invalid(self):
        """Test that invalid languages fall back to default."""
        manager = SimpleLanguageManager(default_lang='invalid_lang')
        # Should fall back to en_US when invalid language is specified
        assert manager.current_lang == 'en_US'

    def test_translation_functionality(self):
        """Test basic translation functionality."""
        manager = SimpleLanguageManager()

        # Test English translation
        result = manager.tr('scan.start', 'Start Scan')
        assert result == 'Start Scan'  # Should return the key itself if not found in translations

        # Test that available languages are loaded
        assert len(manager.available_languages) >= 2
        assert 'en_US' in manager.available_languages
        assert 'it_IT' in manager.available_languages

    def test_language_switching(self):
        """Test language switching functionality."""
        manager = SimpleLanguageManager()

        # Test switching to Italian
        success = manager.set_language('it_IT')
        assert success == True
        assert manager.current_lang == 'it_IT'

        # Test switching back to English
        success = manager.set_language('en_US')
        assert success == True
        assert manager.current_lang == 'en_US'

    def test_invalid_language_switching(self):
        """Test switching to invalid languages."""
        manager = SimpleLanguageManager()

        # Test switching to invalid language
        success = manager.set_language('invalid_lang')
        assert success == False
        assert manager.current_lang == 'en_US'  # Should remain unchanged

    def test_qaction_language_switching(self):
        """Test language switching with QAction objects."""
        manager = SimpleLanguageManager()

        # Create a mock QAction-like object
        class MockQAction:
            def data(self):
                return 'it_IT'

        mock_action = MockQAction()
        success = manager.set_language(mock_action)
        assert success == True
        assert manager.current_lang == 'it_IT'

    def test_available_languages_functionality(self):
        """Test that available languages are properly loaded."""
        manager = SimpleLanguageManager()

        languages = manager.get_available_languages()
        assert isinstance(languages, dict)
        assert len(languages) >= 2

        # Check that both English and Italian are available
        assert 'en_US' in languages
        assert 'it_IT' in languages

    def test_empty_translation_key(self):
        """Test translation with empty key."""
        manager = SimpleLanguageManager()

        result = manager.tr('', 'default')
        assert result == 'default'

        result = manager.tr(None, 'default')
        assert result == 'default'
