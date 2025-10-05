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
    language_changed = pyqtSignal(str)

    def __init__(self, default_lang: str = 'en', parent: Optional[QObject] = None):
        """Initialize the language manager.

        Args:
            default_lang: Default language code (e.g., 'en', 'it')
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
            logger.warning(f"Language {self.current_lang} not found, using default 'en'")
            self.current_lang = 'en'

        logger.info(f"Language manager initialized with language: {self.current_lang}")
    
    def _load_languages(self):
        """Load all available language files from the script/lang directory."""
        lang_dir = os.path.dirname(__file__)
        
        # Check if we're running in a Nuitka-compiled environment
        is_nuitka = '__compiled__' in globals()
        
        if not os.path.exists(lang_dir):
            logger.error(f"Language directory not found: {lang_dir}")
            return
        
        # Load each language file
        for filename in os.listdir(lang_dir):
            if filename.endswith('.py') and filename != '__init__.py':
                lang_code = filename[:-3]  # Remove .py extension
                lang_file_path = os.path.join(lang_dir, filename)
                
                try:
                    # Read the language file content
                    if is_nuitka:
                        # In Nuitka-compiled environment, try to read from data files
                        try:
                            import sys
                            # Try to find the file in the Nuitka data directory
                            for path in sys.path:
                                potential_path = os.path.join(path, 'script', 'lang', filename)
                                if os.path.exists(potential_path):
                                    lang_file_path = potential_path
                                    break
                        except:
                            pass
                    
                    with open(lang_file_path, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                    
                    # Create a namespace to execute the file content
                    namespace = {}
                    
                    # Execute the file content in the namespace
                    exec(file_content, namespace)
                    
                    # Get translations and available languages from the namespace
                    if 'TRANSLATIONS' in namespace:
                        self.translations.update(namespace['TRANSLATIONS'])
                    
                    if 'AVAILABLE_LANGUAGES' in namespace:
                        self.available_languages.update(namespace['AVAILABLE_LANGUAGES'])
                    
                    logger.info(f"Loaded language: {lang_code}")
                    
                except Exception as e:
                    logger.error(f"Failed to load language {lang_code}: {e}")
        
        logger.info(f"Loaded {len(self.translations)} languages: {list(self.translations.keys())}")

    def set_language(self, lang_code: str) -> bool:
        """Set the current language.

        Args:
            lang_code: The language code to set (e.g., 'en', 'it')

        Returns:
            bool: True if the language was changed successfully, False otherwise
        """
        if lang_code not in self.translations:
            logger.warning(f"Language {lang_code} not found")
            return False

        if lang_code != self.current_lang:
            old_lang = self.current_lang
            self.current_lang = lang_code
            logger.info(f"Language changed from {old_lang} to {lang_code}")

            # Emit the signal
            self.language_changed.emit(lang_code)
            return True

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
            Dict[str, str]: Dictionary of language codes to language names
        """
        return self.available_languages.copy()

    def tr(self, key: str, default: str = None) -> str:
        """Translate a key to the current language.

        Args:
            key: The translation key
            default: Default text if key not found (optional)

        Returns:
            str: The translated text or default/key if not found
        """
        # Try to get the translation for the current language
        if self.current_lang in self.translations:
            translation = self.translations[self.current_lang]
            if key in translation:
                return translation[key]

        # If not found, try the default language
        if self.default_lang in self.translations:
            translation = self.translations[self.default_lang]
            if key in translation:
                return translation[key]

        # If still not found, try English as fallback
        if 'en' in self.translations and self.default_lang != 'en':
            translation = self.translations['en']
            if key in translation:
                return translation[key]

        # If not found anywhere, return default or key
        if default is not None:
            return default

        logger.warning(f"Translation key not found: {key}")
        return key
