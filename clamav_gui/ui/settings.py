"""
Settings management for the ClamAV GUI application.
"""
from PySide6.QtCore import QSettings
from pathlib import Path
import os
import json
import logging

logger = logging.getLogger(__name__)

class AppSettings:
    """Manages application settings and configuration."""

    def __init__(self):
        """Initialize the settings manager."""
        self.settings = QSettings("Tuxxle", "ClamAV-GUI")
        self.config_dir = Path(__file__).parent.parent.parent / 'config'
        self.config_file = self.config_dir / 'settings.json'
        self.default_paths = self._get_default_paths()

        # Ensure config directory exists
        self.config_dir.mkdir(exist_ok=True)

    def _get_default_paths(self):
        """Get default paths for ClamAV executables."""
        # Common paths for ClamAV on different platforms
        common_paths = {
            'clamd_path': '',
            'freshclam_path': '',
            'clamscan_path': ''
        }

        # Add platform-specific default paths
        if os.name == 'nt':  # Windows
            program_files = os.environ.get('ProgramFiles', 'C:\\Program Files')
            common_paths.update({
                'clamd_path': os.path.join(program_files, 'ClamAV', 'clamd.exe'),
                'freshclam_path': os.path.join(program_files, 'ClamAV', 'freshclam.exe'),
                'clamscan_path': os.path.join(program_files, 'ClamAV', 'clamscan.exe')
            })
        else:  # Linux/macOS
            common_paths.update({
                'clamd_path': '/usr/sbin/clamd',
                'freshclam_path': '/usr/bin/freshclam',
                'clamscan_path': '/usr/bin/clamscan'
            })

        return common_paths

    def load_settings(self):
        """
        Load application settings from both QSettings and JSON file.

        Returns:
            dict: Dictionary containing all settings
        """
        settings = {}

        # First load from JSON file if it exists
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    json_settings = json.load(f)
                    settings.update(json_settings)
                    logger.info(f"Loaded settings from {self.config_file}")
            except Exception as e:
                logger.warning(f"Failed to load settings from {self.config_file}: {e}")

        # Then load from QSettings (for backwards compatibility and system integration)
        for key, default in self.default_paths.items():
            if key not in settings:  # Don't override JSON settings
                settings[key] = self.settings.value(key, default)

        # Load window geometry and state from QSettings
        settings['geometry'] = self.settings.value('geometry')
        settings['window_state'] = self.settings.value('windowState')

        # Load other settings with defaults from QSettings if not in JSON
        qsettings_keys = {
            'auto_update': True,
            'scan_archives': True,
            'scan_heuristics': True,
            'scan_pua': False,
            'max_file_size': 100,  # MB
            'max_scan_time': 300,  # seconds
            'exclude_patterns': '*.log,*.tmp',
            'include_patterns': '*',
            'scanner_type': 'integrated'  # integrated, external, auto
        }

        for key, default in qsettings_keys.items():
            if key not in settings:
                settings[key] = self.settings.value(key, default, type=type(default) if default is not None else str)

        return settings

    def save_settings(self, settings):
        """
        Save application settings to both QSettings and JSON file.

        Args:
            settings (dict): Dictionary containing settings to save

        Returns:
            bool: True if settings were saved successfully, False otherwise
        """
        try:
            # Save to JSON file
            json_success = self._save_to_json(settings)

            # Save to QSettings (for backwards compatibility and system integration)
            qsettings_success = self._save_to_qsettings(settings)

            return json_success and qsettings_success

        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            return False

    def _save_to_json(self, settings):
        """Save settings to JSON file."""
        try:
            # Create a copy of settings for JSON (exclude Qt-specific objects)
            json_settings = {}

            # Include executable paths
            for key in ['clamd_path', 'freshclam_path', 'clamscan_path']:
                if key in settings:
                    json_settings[key] = settings[key]

            # Include scan settings
            scan_keys = ['scan_archives', 'scan_heuristics', 'scan_pua', 'max_file_size',
                        'max_scan_time', 'exclude_patterns', 'include_patterns']
            for key in scan_keys:
                if key in settings:
                    json_settings[key] = settings[key]

            # Include other settings
            other_keys = ['auto_update', 'language', 'theme', 'scanner_type']
            for key in other_keys:
                if key in settings:
                    json_settings[key] = settings[key]

            # Save to JSON file
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(json_settings, f, indent=2, ensure_ascii=False)

            logger.info(f"Settings saved to {self.config_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to save settings to JSON: {e}")
            return False

    def _save_to_qsettings(self, settings):
        """Save settings to QSettings."""
        try:
            # Save paths
            for key in ['clamd_path', 'freshclam_path', 'clamscan_path']:
                if key in settings:
                    self.settings.setValue(key, settings[key])

            # Save window state (keep in QSettings for Qt integration)
            if 'geometry' in settings:
                self.settings.setValue('geometry', settings['geometry'])
            if 'window_state' in settings:
                self.settings.setValue('windowState', settings['window_state'])

            # Save other settings
            if 'auto_update' in settings:
                self.settings.setValue('auto_update', settings['auto_update'])
            if 'scan_archives' in settings:
                self.settings.setValue('scan_archives', settings['scan_archives'])
            if 'scan_heuristics' in settings:
                self.settings.setValue('scan_heuristics', settings['scan_heuristics'])
            if 'scan_pua' in settings:
                self.settings.setValue('scan_pua', settings['scan_pua'])
            if 'max_file_size' in settings:
                self.settings.setValue('max_file_size', settings['max_file_size'])
            if 'max_scan_time' in settings:
                self.settings.setValue('max_scan_time', settings['max_scan_time'])
            if 'exclude_patterns' in settings:
                self.settings.setValue('exclude_patterns', settings['exclude_patterns'])
            if 'include_patterns' in settings:
                self.settings.setValue('include_patterns', settings['include_patterns'])
            if 'scanner_type' in settings:
                self.settings.setValue('scanner_type', settings['scanner_type'])

            # Sync settings
            self.settings.sync()
            return True

        except Exception as e:
            logger.error(f"Failed to save settings to QSettings: {e}")
            return False
    
    def reset_to_defaults(self):
        """Reset all settings to their default values."""
        self.settings.clear()
        self.settings.sync()
        return self.load_settings()
    
    def get_setting(self, key, default=None):
        """
        Get a specific setting value.
        
        Args:
            key (str): Setting key
            default: Default value if setting doesn't exist
            
        Returns:
            The setting value or default if not found
        """
        return self.settings.value(key, default)
    
    def set_setting(self, key, value):
        """
        Set a specific setting value.
        
        Args:
            key (str): Setting key
            value: Value to set
            
        Returns:
            bool: True if setting was saved successfully, False otherwise
        """
        try:
            self.settings.setValue(key, value)
            self.settings.sync()
            return True
        except Exception as e:
            logger.error(f"Failed to set setting '{key}': {e}")
            return False
