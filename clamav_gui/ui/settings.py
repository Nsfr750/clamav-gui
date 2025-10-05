"""
Settings management for the ClamAV GUI application.
"""
from PySide6.QtCore import QSettings
from pathlib import Path
import os
import logging

logger = logging.getLogger(__name__)

class AppSettings:
    """Manages application settings and configuration."""
    
    def __init__(self):
        """Initialize the settings manager."""
        self.settings = QSettings("Tuxxle", "ClamAV-GUI")
        self.default_paths = self._get_default_paths()
    
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
        Load application settings.
        
        Returns:
            dict: Dictionary containing all settings
        """
        settings = {}
        
        # Load paths with defaults
        for key, default in self.default_paths.items():
            settings[key] = self.settings.value(key, default)
        
        # Load window geometry and state
        settings['geometry'] = self.settings.value('geometry')
        settings['window_state'] = self.settings.value('windowState')
        
        # Load other settings with defaults
        settings['auto_update'] = self.settings.value('auto_update', True, type=bool)
        settings['scan_archives'] = self.settings.value('scan_archives', True, type=bool)
        settings['scan_heuristics'] = self.settings.value('scan_heuristics', True, type=bool)
        settings['scan_pua'] = self.settings.value('scan_pua', False, type=bool)
        
        return settings
    
    def save_settings(self, settings):
        """
        Save application settings.
        
        Args:
            settings (dict): Dictionary containing settings to save
            
        Returns:
            bool: True if settings were saved successfully, False otherwise
        """
        try:
            # Save paths
            for key in ['clamd_path', 'freshclam_path', 'clamscan_path']:
                if key in settings:
                    self.settings.setValue(key, settings[key])
            
            # Save window state
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
            
            # Sync settings - on Windows, sync() doesn't return a value
            self.settings.sync()
            return True
            
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
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
