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
        
        # Map of language codes to their display names
        self.available_languages = {
            'en': 'English',
            'en_US': 'English (United States)',
            'it': 'Italiano',
            'it_IT': 'Italiano (Italia)',
        }
        
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

    def is_language_available(self, lang_code: str) -> bool:
        """Check if a language is available.
        
        Args:
            lang_code: Language code to check
            
        Returns:
            bool: True if the language is available, False otherwise
        """
        return lang_code in self.translations
        
    def set_language(self, lang_code: str) -> bool:
        """Set the current language.

        Args:
            lang_code: The language code to set (e.g., 'en', 'it')

        Returns:
            bool: True if the language was changed successfully, False otherwise
        """
        if not lang_code:
            logger.warning("No language code provided")
            return False
            
        # If the exact language is available, use it
        if lang_code in self.translations:
            if lang_code != self.current_lang:
                old_lang = self.current_lang
                self.current_lang = lang_code
                logger.info(f"Language changed from {old_lang} to {lang_code}")
                self.language_changed.emit(lang_code)
                return True
            return True  # Already set to this language
            
        # Try language code without region (e.g., 'en' from 'en_US')
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
        
        # If not found and current language is en_US, try falling back to en
        if result is None and self.current_lang == 'en_US':
            en_translations = self.translations.get('en', {})
            result = en_translations.get(key)
        
        # If still not found, try English as fallback
        if result is None and 'en' in self.translations and self.current_lang != 'en':
            en_translations = self.translations['en']
            result = en_translations.get(key)
        
        # If still not found, use the default
        if result is None:
            result = default
            
        return result
