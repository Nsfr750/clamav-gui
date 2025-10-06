"""
Main window for the ClamAV GUI application.

This module provides the core functionality for the ClamAV GUI application.
The UI components have been moved to clamav_gui.ui.UI.ClamAVMainWindow.
"""
import os
import subprocess
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from PySide6.QtCore import QObject, Signal, Slot, QThread, QProcess, QTimer
from PySide6.QtWidgets import QMainWindow, QMessageBox, QApplication, QVBoxLayout, QWidget, QTabWidget
from PySide6.QtGui import QIcon

from .ui.UI import ClamAVMainWindow as UI_ClamAVMainWindow
from .ui.settings import AppSettings
from .utils.virus_db import VirusDBUpdater
from .lang.lang_manager import SimpleLanguageManager

# Setup logger
logger = logging.getLogger(__name__)

class ClamAVGUI(UI_ClamAVMainWindow):
    """Main window for the ClamAV GUI application.
    
    This class extends UI_ClamAVMainWindow to provide the core functionality
    while the UI is defined in the parent class.
    """
    
    def __init__(self, lang_manager: Optional[SimpleLanguageManager] = None, parent: Optional[QMainWindow] = None):
        """Initialize the main window.
        
        Args:
            lang_manager: Instance of SimpleLanguageManager for translations
            parent: Parent widget
        """
        super().__init__(lang_manager=lang_manager, parent=parent)
        self.process = None
        self.scan_thread = None
        self.virus_db_updater = VirusDBUpdater()
        self.current_settings = {}
        
        # Initialize core components
        self.initialize_core_components()
        
        # Set up the main window
        self.setWindowTitle(self.tr("ClamAV GUI"))
        self.setMinimumSize(800, 600)
        
        # Set application icon
        self.setup_icon()
        
        # Initialize UI
        self.setup_ui()
        
        # Load settings
        self.load_settings()
        
        # Connect signals
        self.setup_connections()
    
    def setup_icon(self):
        """Set up the application icon."""
        try:
            icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'icon.ico')
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
            else:
                logger.warning(f"Icon not found at: {icon_path}")
        except Exception as e:
            logger.warning(f"Failed to load application icon: {e}")
    
    def initialize_core_components(self):
        """Initialize core components of the application."""
        self.settings = AppSettings()
        self.scan_in_progress = False
    
    def setup_ui(self):
        """Set up the user interface."""
        # Create central widget and main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # Create tab widget
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)
        
        # Initialize tabs (to be implemented in child classes)
        self.setup_tabs()
    
    def setup_tabs(self):
        """Set up the application tabs. To be overridden by child classes."""
        pass
    
    def load_settings(self):
        """Load application settings."""
        try:
            self.current_settings = self.settings.load_settings() or {}
            self.apply_settings()
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
    
    def apply_settings(self):
        """Apply application settings."""
        # Apply language if specified in settings
        if 'language' in self.current_settings and hasattr(self, 'lang_manager'):
            self.lang_manager.set_language(self.current_settings['language'])
    
    def setup_connections(self):
        """Set up signal connections."""
        if hasattr(self, 'lang_manager') and hasattr(self.lang_manager, 'language_changed'):
            self.lang_manager.language_changed.connect(self.retranslate_ui)
    
    def init_ui(self):
        """Initialize the user interface."""
        # Create and set up the menu bar
        self.setup_menu()
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Add tabs
        self.scan_tab = self.create_scan_tab()
        self.update_tab = self.create_update_tab()
        self.settings_tab = self.create_settings_tab()
        self.config_editor_tab = self.create_config_editor_tab()
        
        self.tabs.addTab(self.scan_tab, self.tr("Scan"))
        self.tabs.addTab(self.update_tab, self.tr("Update"))
        self.tabs.addTab(self.settings_tab, self.tr("Settings"))
        self.tabs.addTab(self.config_editor_tab, self.tr("Config Editor"))
        
        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage(self.tr("Ready"))
        
        # Set up update check timer (check once per day)
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.check_for_updates)
        self.update_timer.start(24 * 60 * 60 * 1000)  # 24 hours in milliseconds
    
    def setup_menu(self):
        """Set up the menu bar using ClamAVMenuBar."""
        # Create and set up the menu bar
        self.menu_bar = ClamAVMenuBar(self)
        self.setMenuBar(self.menu_bar)
        
        # Set the language manager for the menu bar
        if hasattr(self, 'lang_manager') and self.lang_manager is not None:
            self.menu_bar.set_language_manager(self.lang_manager)
        
        # Connect menu signals
        self.menu_bar.help_requested.connect(self.show_help)
        self.menu_bar.about_requested.connect(self.show_about)
        self.menu_bar.sponsor_requested.connect(self.show_sponsor)
        self.menu_bar.update_check_requested.connect(lambda: self.check_for_updates(force_check=True))
        
        # Set up the language menu
        self.setup_language_menu()
    
    def show_help(self):
        """Open the help dialog by executing help.py."""
        try:
            import subprocess
            import sys
            import os
            help_script = os.path.join(os.path.dirname(__file__), '..', 'script', 'help.py')
            if os.path.exists(help_script):
                subprocess.Popen([sys.executable, help_script])
            else:
                QMessageBox.warning(self, self.tr("Error"), 
                                 self.tr("Help file not found at: {}".format(help_script)))
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), 
                              self.tr("Failed to open help: {}".format(str(e))))
    
    def show_about(self):
        """Open the about dialog by executing about.py."""
        try:
            import subprocess
            import sys
            import os
            about_script = os.path.join(os.path.dirname(__file__), 'ui', 'about.py')
            if os.path.exists(about_script):
                subprocess.Popen([sys.executable, about_script])
            else:
                QMessageBox.warning(self, self.tr("Error"), 
                                 self.tr("About file not found at: {}".format(about_script)))
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), 
                              self.tr("Failed to open about: {}".format(str(e))))
    
    def show_sponsor(self):
        """Open the sponsor dialog by executing sponsor.py."""
        try:
            import subprocess
            import sys
            import os
            sponsor_script = os.path.join(os.path.dirname(__file__), 'ui', 'sponsor.py')
            if os.path.exists(sponsor_script):
                subprocess.Popen([sys.executable, sponsor_script])
            else:
                # Fallback to opening the sponsor URL if the script doesn't exist
                url = "https://github.com/sponsors/Nsfr750"
                QDesktopServices.openUrl(QUrl(url))
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), 
                              self.tr("Failed to open sponsor: {}".format(str(e))))
    
    def setup_language_menu(self):
        """Set up the language selection menu with available languages."""
        if not hasattr(self, 'lang_manager') or not self.lang_manager:
            logger.warning("Language manager not available")
            return
            
        # Make sure we have the menu bar and language menu
        if not hasattr(self, 'menu_bar') or not hasattr(self.menu_bar, 'language_menu'):
            logger.warning("Menu bar or language menu not available")
            return
            
        language_menu = self.menu_bar.language_menu
        
        # Clear existing actions safely
        try:
            # Clear any existing connections
            if hasattr(language_menu, 'aboutToShow'):
                try:
                    language_menu.aboutToShow.disconnect()
                except (TypeError, RuntimeError):
                    # No connections to disconnect or already disconnected
                    pass
            
            # Clear existing actions
            language_menu.clear()
            
            # Add language actions
            available_languages = self.lang_manager.get_available_languages()
            if not available_languages:
                logger.warning("No available languages found")
                return
                
            for lang_code, lang_name in available_languages.items():
                try:
                    # Get the display name for the language
                    display_name = lang_name
                    if hasattr(self.lang_manager, 'tr'):
                        display_name = self.lang_manager.tr(lang_name) or lang_name
                    
                    action = language_menu.addAction(display_name)
                    action.setCheckable(True)
                    action.setChecked(lang_code == self.lang_manager.get_language())
                    action.setData(lang_code)
                    
                    # Connect the action to change the language
                    action.triggered.connect(
                        lambda checked, code=lang_code: self.change_language(code)
                    )
                except Exception as e:
                    logger.error(f"Error adding language {lang_code}: {e}", exc_info=True)
                    continue
            
            # Add a separator
            language_menu.addSeparator()
            
            # Add a refresh action
            refresh_text = "Refresh"
            if hasattr(self.lang_manager, 'tr'):
                refresh_text = self.lang_manager.tr("menu.help.refresh") or refresh_text
                
            refresh_action = language_menu.addAction(refresh_text)
            refresh_action.triggered.connect(self.retranslate_ui)
            
            # Store a reference to the language menu
            self.language_menu = language_menu
            
        except Exception as e:
            logger.error(f"Error setting up language menu: {e}", exc_info=True)
            # Try to recover by creating a basic menu
            try:
                language_menu.clear()
                language_menu.addAction("Error loading languages").setEnabled(False)
            except:
                pass
    
    def change_language(self, lang_code=None):
        """Change the application language.
        
        Args:
            lang_code: The language code to change to (e.g., 'en_US', 'it_IT')
        """
        # If called from an action, get the language code from the action
        if lang_code is None and hasattr(self, 'sender'):
            action = self.sender()
            if action and hasattr(action, 'data'):
                lang_code = action.data()
        
        if not lang_code or not hasattr(self, 'lang_manager') or not self.lang_manager:
            logger.warning("Cannot change language: invalid language code or language manager not available")
            return
            
        try:
            # Update the language in the language manager
            if self.lang_manager.set_language(lang_code):
                self.current_lang = lang_code
                logger.info(f"Language changed to {lang_code}")
                
                # Save language preference
                if not hasattr(self, 'current_settings'):
                    self.current_settings = {}
                self.current_settings['language'] = lang_code
                self.settings.save_settings(self.current_settings)
                
                # Update the UI
                self.retranslate_ui(lang_code)
                
                # Show a message to the user
                if hasattr(self, 'status_bar'):
                    lang_name = self.lang_manager.available_languages.get(lang_code, lang_code)
                    self.status_bar.showMessage(
                        f"{self.tr('Language changed to')} {lang_name}",
                        3000  # Show for 3 seconds
                    )
            else:
                logger.warning(f"Failed to change language to {lang_code}")
        except Exception as e:
            logger.error(f"Error changing language to {lang_code}: {e}", exc_info=True)
    
    def is_menu_valid(self, menu):
        """Check if a menu is still valid (not deleted)."""
        try:
            # Try to access a property to see if the object is still valid
            return menu is not None and hasattr(menu, 'isWidgetType') and menu.isWidgetType()
        except RuntimeError:
            return False

    def retranslate_ui(self, language_code=None):
        """Retranslate the UI when the language changes.
        
        Args:
            language_code: The new language code (optional)
        """
        if not hasattr(self, 'lang_manager') or not self.lang_manager:
            logger.warning("Cannot retranslate UI: Language manager not available")
            return
            
        try:
            logger.debug(f"Retranslating UI to language: {language_code or self.lang_manager.get_language()}")
            
            # Update window title
            self.setWindowTitle(self.lang_manager.tr("window.title") or "ClamAV GUI")
            
            # Update menu bar safely
            if hasattr(self, 'menu_bar') and self.menu_bar and self.is_menu_valid(self.menu_bar):
                try:
                    # Update menu titles with safety checks
                    if hasattr(self.menu_bar, 'file_menu') and self.is_menu_valid(self.menu_bar.file_menu):
                        self.menu_bar.file_menu.setTitle(self.lang_manager.tr("menu.file") or "&File")
                    
                    if hasattr(self.menu_bar, 'tools_menu') and self.is_menu_valid(self.menu_bar.tools_menu):
                        self.menu_bar.tools_menu.setTitle(self.lang_manager.tr("menu.tools") or "&Tools")
                    
                    if hasattr(self.menu_bar, 'help_menu') and self.is_menu_valid(self.menu_bar.help_menu):
                        self.menu_bar.help_menu.setTitle(self.lang_manager.tr("menu.help") or "&Help")
                    
                    if hasattr(self.menu_bar, 'language_menu') and self.is_menu_valid(self.menu_bar.language_menu):
                        self.menu_bar.language_menu.setTitle(self.lang_manager.tr("menu.language") or "&Language")
                    
                    # Update all menu actions safely
                    for action in self.menu_bar.actions():
                        try:
                            if not hasattr(action, 'menu') or not action.menu():
                                if hasattr(action, 'text') and action.text():
                                    # Get the translation key by removing the '&' character
                                    key = action.text().replace('&', '')
                                    # Try to translate the key
                                    translation = self.lang_manager.tr(f"menu.{key.lower()}")
                                    if translation:
                                        action.setText(translation)
                        except RuntimeError:
                            logger.warning("Skipping invalid menu action")
                            continue
                except RuntimeError as e:
                    logger.error(f"Error updating menu bar: {e}")
            
            # Update tab names
            if hasattr(self, 'tabs') and self.tabs:
                try:
                    tab_keys = ["tab.scan", "tab.update", "tab.quarantine", "tab.settings"]
                    for i in range(min(self.tabs.count(), len(tab_keys))):
                        translated = self.lang_manager.tr(tab_keys[i])
                        if translated:
                            self.tabs.setTabText(i, translated)
                except RuntimeError as e:
                    logger.error(f"Error updating tabs: {e}")
            
            # Update status bar
            if hasattr(self, 'status_bar') and self.status_bar:
                try:
                    self.status_bar.showMessage(self.lang_manager.tr("status.ready") or "Ready")
                except RuntimeError as e:
                    logger.error(f"Error updating status bar: {e}")
            
            # Update the language menu items
            if hasattr(self, 'language_menu') and self.language_menu and self.is_menu_valid(self.language_menu):
                try:
                    for action in self.language_menu.actions():
                        if hasattr(action, 'data') and action.data():
                            lang_code = action.data()
                            lang_name = self.lang_manager.available_languages.get(lang_code, lang_code)
                            action.setText(lang_name)
                            action.setChecked(lang_code == self.lang_manager.get_language())
                except RuntimeError as e:
                    logger.error(f"Error updating language menu: {e}")
            
            # Force update the UI
            try:
                self.update()
                if QApplication.instance():
                    QApplication.instance().processEvents()
            except RuntimeError as e:
                logger.error(f"Error updating UI: {e}")
            
            logger.debug("UI retranslation completed")
                
        except Exception as e:
            logger.error(f"Error in retranslate_ui: {e}", exc_info=True)
    
    def check_for_updates(self, force_check=False):
        """Check for application updates."""
        from . import __version__
        check_for_updates(parent=self, current_version=__version__, force_check=force_check)
    
    # Add the rest of the existing methods from the original file
    # ... (create_scan_tab, create_update_tab, create_settings_tab, etc.)
    
    def create_scan_tab(self):
        """Create the scan tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Target selection
        target_group = QGroupBox(self.tr("Scan Target"))
        target_layout = QHBoxLayout()
        
        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText(self.tr("Select a file or directory to scan..."))
        target_layout.addWidget(self.target_input)
        
        browse_btn = QPushButton(self.tr("Browse..."))
        browse_btn.clicked.connect(self.browse_target)
        target_layout.addWidget(browse_btn)
        
        target_group.setLayout(target_layout)
        
        # Scan options
        options_group = QGroupBox(self.tr("Scan Options"))
        options_layout = QVBoxLayout()
        
        self.recursive_scan = QCheckBox(self.tr("Scan subdirectories"))
        self.recursive_scan.setChecked(True)
        options_layout.addWidget(self.recursive_scan)
        
        self.heuristic_scan = QCheckBox(self.tr("Enable heuristic scan"))
        self.heuristic_scan.setChecked(True)
        options_layout.addWidget(self.heuristic_scan)
        
        options_group.setLayout(options_layout)
        
        # Output
        output_group = QGroupBox(self.tr("Output"))
        output_layout = QVBoxLayout()
        
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        output_layout.addWidget(self.output)
        
        output_group.setLayout(output_layout)
        
        # Progress
        self.progress = QProgressBar()
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.scan_btn = QPushButton(self.tr("Start Scan"))
        self.scan_btn.clicked.connect(self.start_scan)
        button_layout.addWidget(self.scan_btn)
        
        self.stop_btn = QPushButton(self.tr("Stop"))
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_scan)
        button_layout.addWidget(self.stop_btn)
        
        # Add all to main layout
        layout.addWidget(target_group)
        layout.addWidget(options_group)
        layout.addWidget(output_group)
        layout.addWidget(self.progress)
        layout.addLayout(button_layout)
        
        return tab
    
    def create_update_tab(self):
        """Create the update tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Update options
        update_group = QGroupBox(self.tr("Virus Database Update"))
        update_layout = QVBoxLayout()
        
        self.update_output = QTextEdit()
        self.update_output.setReadOnly(True)
        update_layout.addWidget(self.update_output)
        
        update_btn = QPushButton(self.tr("Update Now"))
        update_btn.clicked.connect(self.update_database)
        update_layout.addWidget(update_btn)
        
        update_group.setLayout(update_layout)
        
        # Add to main layout
        layout.addWidget(update_group)
        layout.addStretch()
        
        return tab
    
    def create_settings_tab(self):
        """Create the settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # ClamAV Path settings
        path_group = QGroupBox(self.tr("ClamAV Paths"))
        path_layout = QFormLayout()
        
        self.clamd_path = QLineEdit()
        path_layout.addRow(self.tr("ClamD Path:"), self.clamd_path)
        
        self.freshclam_path = QLineEdit()
        path_layout.addRow(self.tr("FreshClam Path:"), self.freshclam_path)
        
        self.clamscan_path = QLineEdit()
        path_layout.addRow(self.tr("ClamScan Path:"), self.clamscan_path)
        
        path_group.setLayout(path_layout)
        
        # Save button
        save_btn = QPushButton(self.tr("Save Settings"))
        save_btn.clicked.connect(self.save_settings)
        
        # Add to main layout
        layout.addWidget(path_group)
        layout.addStretch()
        layout.addWidget(save_btn)
        
        return tab
    
    def create_config_editor_tab(self):
        """Create the config editor tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Config editor
        config_group = QGroupBox(self.tr("Configuration Editor"))
        config_layout = QVBoxLayout()
        
        self.config_editor = QPlainTextEdit()
        config_layout.addWidget(self.config_editor)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        load_btn = QPushButton(self.tr("Load Config"))
        load_btn.clicked.connect(self.load_config)
        btn_layout.addWidget(load_btn)
        
        save_btn = QPushButton(self.tr("Save Config"))
        save_btn.clicked.connect(self.save_config)
        btn_layout.addWidget(save_btn)
        
        config_layout.addLayout(btn_layout)
        config_group.setLayout(config_layout)
        
        # Add to main layout
        layout.addWidget(config_group)
        
        return tab
    
    # Add the rest of the original methods here
    def browse_target(self):
        """Open a file dialog to select a file or directory to scan."""
        target = QFileDialog.getExistingDirectory(self, self.tr("Select Directory"))
        if target:
            self.target_input.setText(target)
    
    def start_scan(self):
        """Start the ClamAV scan."""
        target = self.target_input.text()
        if not target:
            QMessageBox.warning(self, self.tr("Error"), self.tr("Please select a target to scan"))
            return
        
        # Get the path to clamscan from settings or use default
        clamscan_path = self.clamscan_path.text().strip()
        if not clamscan_path:
            clamscan_path = "clamscan"  # Default to system path if not set
            
        # Create a database directory in the user's AppData folder
        app_data = os.getenv('APPDATA')
        clamav_dir = os.path.join(app_data, 'ClamAV')
        db_dir = os.path.join(clamav_dir, 'database')
        
        try:
            os.makedirs(db_dir, exist_ok=True)
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), 
                               self.tr(f"Failed to create database directory: {e}"))
            return
            
        # Build the command with proper options
        cmd = [clamscan_path]
        
        # Add database directory
        cmd.extend(['--database', db_dir])
        
        # Add recursive flag if enabled
        if self.recursive_scan.isChecked():
            cmd.append("-r")
            
        # Add heuristic scan if enabled (use --heuristic-alerts for newer versions)
        if self.heuristic_scan.isChecked():
            cmd.append("--heuristic-alerts")
            
        # Add target and output options
        cmd.extend([target, "--verbose", "--stdout"])
        
        # Start the scan in a separate thread
        self.scan_thread = ScanThread(cmd)
        self.scan_thread.update_output.connect(self.update_scan_output)
        self.scan_thread.update_progress.connect(self.update_progress)
        self.scan_thread.finished.connect(self.scan_finished)
        
        # Update UI
        self.scan_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.output.clear()
        self.progress.setValue(0)
        
        # Start the thread
        self.scan_thread.start()
    
    def stop_scan(self):
        """Stop the current scan."""
        if self.scan_thread and self.scan_thread.isRunning():
            self.scan_thread.terminate()
            self.scan_thread.wait()
            self.scan_finished(1, 1)  # Signal error
    
    def update_scan_output(self, text):
        """Update the scan output with new text."""
        self.output.append(text)
    
    def scan_finished(self, exit_code, status):
        """Handle scan completion."""
        self.scan_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        if exit_code == 0:
            self.status_bar.showMessage(self.tr("Scan completed successfully - No threats found"))
            QMessageBox.information(self, self.tr("Scan Complete"), 
                                 self.tr("The scan completed successfully. No threats were found."))
        elif exit_code == 1:
            self.status_bar.showMessage(self.tr("Scan completed - Viruses found!"))
            QMessageBox.warning(self, self.tr("Threats Detected"), 
                             self.tr("The scan completed and found potential threats. Check the scan results for details."))
        else:
            self.status_bar.showMessage(self.tr("Scan failed with errors"))
            QMessageBox.critical(self, self.tr("Scan Failed"), 
                              self.tr("The scan failed to complete. Please check if ClamAV is properly installed and configured."))
    
    def update_database(self):
        """Update the ClamAV virus database."""
        # Disconnect any existing connections to avoid duplicates
        self.virus_db_updater.signals.disconnect_all()
            
        self.virus_db_updater.signals.output.connect(self.update_update_output)
        self.virus_db_updater.signals.finished.connect(self.update_finished)
        
        # Clear and update UI
        self.update_output.clear()
        
        # Get freshclam path from settings if available
        freshclam_path = None
        if hasattr(self, 'freshclam_path') and self.freshclam_path.text().strip():
            freshclam_path = self.freshclam_path.text().strip()
        
        # Start the update
        if not self.virus_db_updater.start_update(freshclam_path):
            QMessageBox.critical(self, self.tr("Error"), 
                               self.tr("Failed to start virus database update."))
    
    def update_progress(self, value):
        """Update the progress bar with the current value."""
        if hasattr(self, 'progress'):
            self.progress.setValue(value)
    
    def update_scan_output(self, text):
        """Update the scan output with new text."""
        if hasattr(self, 'output'):
            self.output.append(text)
            
            # Try to extract progress from the output
            if 'Scanned file:' in text:
                # This is a simple way to show progress is happening
                # The actual progress is handled by the update_progress signal
                if hasattr(self, 'progress'):
                    current = self.progress.value()
                    self.progress.setValue(min(99, current + 1))
    
    def update_finished(self, exit_code, status):
        """Handle update completion."""
        if exit_code == 0:
            self.status_bar.showMessage(self.tr("Database updated successfully"))
            if hasattr(self, 'progress'):
                self.progress.setValue(100)
            QMessageBox.information(self, self.tr("Success"),
                                 self.tr("Virus database updated successfully."))
        else:
            self.status_bar.showMessage(self.tr("Database update failed"))
            QMessageBox.warning(self, self.tr("Warning"), 
                             self.tr("Virus database update failed. Please check the logs for details."))
    
    def save_settings(self):
        """Save the application settings."""
        settings = {
            'clamd_path': self.clamd_path.text(),
            'freshclam_path': self.freshclam_path.text(),
            'clamscan_path': self.clamscan_path.text()
        }
        
        if self.settings.save_settings(settings):
            QMessageBox.information(self, self.tr("Success"), self.tr("Settings saved successfully"))
        else:
            QMessageBox.critical(self, self.tr("Error"), self.tr("Failed to save settings"))
    
    def load_config(self):
        """Load a configuration file."""
        file_name, _ = QFileDialog.getOpenFileName(self, self.tr("Open Config File"), "", "Config Files (*.conf);;All Files (*)")
        if file_name:
            try:
                with open(file_name, 'r') as f:
                    self.config_editor.setPlainText(f.read())
            except Exception as e:
                QMessageBox.critical(self, self.tr("Error"), self.tr(f"Failed to load config file: {str(e)}"))
    
    def save_config(self):
        """Save the current configuration to a file."""
        try:
            file_name, _ = QFileDialog.getSaveFileName(
                self, 
                self.tr("Save Config File"), 
                "", 
                "Config Files (*.conf);;All Files (*)"
            )
            if file_name:
                try:
                    with open(file_name, 'w', encoding='utf-8') as f:
                        f.write(self.config_editor.toPlainText())
                    QMessageBox.information(
                        self, 
                        self.tr("Success"), 
                        self.tr("Config file saved successfully")
                    )
                except PermissionError:
                    QMessageBox.critical(
                        self,
                        self.tr("Error"),
                        self.tr("Permission denied. Cannot write to the specified file.")
                    )
                except OSError as e:
                    QMessageBox.critical(
                        self,
                        self.tr("Error"),
                        self.tr(f"Failed to save config file: {str(e)}")
                    )
        except Exception as e:
            QMessageBox.critical(
                self,
                self.tr("Error"),
                self.tr(f"An unexpected error occurred: {str(e)}")
            )
    
    def apply_settings(self):
        """Apply the current settings to the UI."""
        if not self.current_settings:
            return
        
        self.clamd_path.setText(self.current_settings.get('clamd_path', ''))
        self.freshclam_path.setText(self.current_settings.get('freshclam_path', ''))
        self.clamscan_path.setText(self.current_settings.get('clamscan_path', ''))


class ScanThread(QThread):
    """Thread for running ClamAV scans."""
    update_output = Signal(str)
    update_progress = Signal(int)  # Signal for progress updates (0-100)
    finished = Signal(int, int)
    
    def __init__(self, command):
        super().__init__()
        self.command = command
        self.process = None
    
    def run(self):
        """Run the scan command."""
        try:
            self.process = QProcess()
            self.process.readyReadStandardOutput.connect(self.handle_output)
            self.process.readyReadStandardError.connect(self.handle_error)
            self.process.finished.connect(self.on_finished)
            
            # Start the process
            self.process.start(self.command[0], self.command[1:])
            
            # Track progress
            try:
                total_files = 0
                processed_files = 0
                
                while not self.process.waitForFinished(100):  # Check every 100ms
                    # Parse output to get progress
                    output = self.process.readAllStandardOutput().data().decode()
                    if output:
                        self.update_output.emit(output)
                        # Look for progress in the output
                        if 'Scanned file:' in output:
                            processed_files += 1
                            self.update_progress.emit(processed_files)
            except Exception as e:
                logger.error(f"Error in scan process: {e}")
                self.update_output.emit(f"ERROR: {str(e)}\n")
