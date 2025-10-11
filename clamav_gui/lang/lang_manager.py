"""
Simple Language Manager for ClamAV GUI.
This provides a straightforward way to handle language switching.
"""

import logging
import os
from typing import Dict, Optional, Any
from PySide6.QtCore import QObject, Signal

logger = logging.getLogger(__name__)

class SimpleLanguageManager(QObject):
    """Simple language manager for the application."""

    # Signal emitted when the language is changed
    language_changed = Signal(str)

    def __init__(self, default_lang: str = 'en_US', parent: Optional[QObject] = None):
        """Initialize the language manager.

        Args:
            default_lang: Default language code (e.g., 'en_US', 'it_IT')
            parent: Optional parent QObject
        """
        super().__init__(parent)
        self.current_lang = default_lang
        self.default_lang = default_lang

        # Initialize translation storage
        self.translations = {}
        self.available_languages = {}

        # Load all available languages
        self._load_languages()

        # Validate that the language exists
        if self.current_lang not in self.translations:
            logger.warning(f"Language {self.current_lang} not found, using default 'en_US'")
            self.current_lang = 'en_US'

        logger.info(f"Language manager initialized with language: {self.current_lang}")

    def _load_languages(self):
        """Load translation files directly."""
        lang_dir = os.path.dirname(__file__)

        # Define available languages
        self.available_languages = {
            'en_US': 'English (United States)',
            'it_IT': 'Italiano (Italia)',
        }

        # Load translation files
        translation_files = {
            'en_US': 'en_US.py',
            'it_IT': 'it_IT.py',
        }

        for lang_code, filename in translation_files.items():
            file_path = os.path.join(lang_dir, filename)

            if os.path.exists(file_path):
                try:
                    # Import the translation file as a module
                    import importlib.util

                    spec = importlib.util.spec_from_file_location(f"lang_{lang_code}", file_path)
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)

                        # Extract translations and available languages
                        if hasattr(module, 'TRANSLATIONS'):
                            self.translations.update(module.TRANSLATIONS)

                        if hasattr(module, 'AVAILABLE_LANGUAGES'):
                            self.available_languages.update(module.AVAILABLE_LANGUAGES)

                        logger.info(f"Loaded language: {lang_code}")

                except Exception as e:
                    logger.error(f"Failed to load language {lang_code}: {e}")
            else:
                logger.warning(f"Translation file not found: {file_path}")

        logger.info(f"Loaded {len(self.translations)} languages: {list(self.translations.keys())}")

    def is_language_available(self, lang_code: str) -> bool:
        """Check if a language is available.

        Args:
            lang_code: Language code to check

        Returns:
            bool: True if the language is available, False otherwise
        """
        return lang_code in self.translations

    def set_language(self, lang_code) -> bool:
        """Set the current language.

        Args:
            lang_code: The language code to set (e.g., 'en_US', 'it_IT') or a QAction with language data

        Returns:
            bool: True if the language was changed successfully, False otherwise
        """
        # Handle case where lang_code is a QAction
        if hasattr(lang_code, 'data') and callable(lang_code.data):
            lang_code = lang_code.data()

        if not lang_code:
            logger.warning("No language code provided")
            return False

        # Convert to string in case it's not already
        lang_code = str(lang_code)

        # If the exact language is available, use it
        if lang_code in self.translations:
            if lang_code != self.current_lang:
                old_lang = self.current_lang
                self.current_lang = lang_code
                logger.info(f"Language changed from {old_lang} to {lang_code}")
                self.language_changed.emit(lang_code)
                return True
            return True  # Already set to this language

        # Try base language (e.g., 'en' from 'en_US')
        try:
            if '_' in lang_code:
                base_lang = lang_code.split('_')[0]
                if base_lang in self.translations and base_lang != lang_code:
                    if base_lang != self.current_lang:
                        old_lang = self.current_lang
                        self.current_lang = base_lang
                        logger.info(f"Language {lang_code} not found, using {base_lang} instead")
                        logger.info(f"Language changed from {old_lang} to {base_lang}")
                        self.language_changed.emit(base_lang)
                        return True
                    return True  # Already set to base language
        except Exception as e:
            logger.error(f"Error processing language code {lang_code}: {e}")
            return False

        logger.warning(f"Language {lang_code} not found in available languages")
        return False

    def get_language(self) -> str:
        """Get the current language code.

        Returns:
            str: The current language code
        """
        return self.current_lang

    def get_current_language(self) -> str:
        """Get the current language code (alias for get_language for backward compatibility).

        Returns:
            str: The current language code
        """
        return self.get_language()

    def get_available_languages(self) -> Dict[str, str]:
        """Get the available languages.

        Returns:
            Dict[str, str]: Dictionary of language codes to display names
        """
        return self.available_languages

    def tr(self, key: str, default: str = "") -> str:
        """Translate a string using the current language.

        Args:
            key: The translation key
            default: Default text if key is not found

        Returns:
            The translated string or the default if not found
        """
        if not key:
            return default

        # Get translations for current language
        translations = self.translations.get(self.current_lang, {})

        # Try to get the translation
        result = translations.get(key)

        # If not found and current language is en_US, try falling back to en_US (it's already the fallback)
        if result is None and self.current_lang == 'en_US':
            # Already using the most complete English translation
            pass

        # If still not found, use the default
        if result is None:
            result = default

        return result
