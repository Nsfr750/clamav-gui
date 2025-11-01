"""
Advanced main window base class for ClamAV GUI full mode functionality.
"""
import logging
import os
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QTabWidget, QStatusBar, QMessageBox
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QTextCursor

from clamav_gui.ui.menu import ClamAVMenuBar
from clamav_gui.ui.settings import AppSettings
from clamav_gui.lang.lang_manager import SimpleLanguageManager

logger = logging.getLogger(__name__)

class ClamAVMainWindow(QMainWindow):
    """Advanced main window base class with full mode functionality."""

    def __init__(self, lang_manager=None, parent=None):
        """Initialize the advanced main window.

        Args:
            lang_manager: Instance of SimpleLanguageManager for translations
            parent: Parent widget
        """
        super().__init__(parent)
        self.lang_manager = lang_manager or SimpleLanguageManager()

        # Initialize core components
        self.settings = AppSettings()
        self.current_settings = {}

        # Initialize managers (these will be overridden by subclasses)
        self.process = None
        self.scan_thread = None
        self.quarantine_manager = None

        # Menu components
        self.menu_bar = None
        self.file_menu = None
        self.tools_menu = None
        self.help_menu = None
        self.language_menu = None

        # UI components
        self.tabs = None
        self.status_bar = None
        self.update_timer = None

        # Setup window properties
        self.setWindowTitle(self.tr("ClamAV GUI"))
        self.resize(1000, 800)
        self.setWindowFlags(
            Qt.Window
            | Qt.WindowMinimizeButtonHint
            | Qt.WindowMaximizeButtonHint
            | Qt.WindowCloseButtonHint
        )

        # Set application icon
        self._setup_window_icon()

        # Initialize UI
        self.init_ui()

        # Connect language manager
        if hasattr(self.lang_manager, 'language_changed'):
            self.lang_manager.language_changed.connect(self.retranslate_ui)

    def _setup_window_icon(self):
        """Set up the application window icon."""
        try:
            # Try multiple possible icon locations
            possible_paths = [
                os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'icon.ico'),
                os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'icon.png'),
                'assets/icon.ico',
                'assets/icon.png'
            ]

            for icon_path in possible_paths:
                if os.path.exists(icon_path):
                    self.setWindowIcon(QIcon(icon_path))
                    logger.info(f"Successfully loaded application icon from: {icon_path}")
                    break
            else:
                logger.warning("No application icon found in any of the expected locations")
        except Exception as e:
            logger.warning(f"Failed to load application icon: {e}")

    def init_ui(self):
        """Initialize the user interface with advanced features."""
        # Create and set up the menu bar
        self.setup_menu()

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Create tab widget for multiple functionalities
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Create all tabs (these can be overridden by subclasses)
        self.create_tabs()

        # Status bar with advanced information
        self.status_bar = self.statusBar()
        self.status_bar.showMessage(self.tr("Ready"))

        # Set up periodic update checks
        self.setup_update_timer()

    def setup_menu(self):
        """Set up the advanced menu bar."""
        # Create and set up the menu bar
        self.menu_bar = ClamAVMenuBar(self)
        self.setMenuBar(self.menu_bar)

        # Set the language manager for the menu bar
        if self.lang_manager is not None:
            self.menu_bar.set_language_manager(self.lang_manager)

        # Connect common menu signals
        self.connect_menu_signals()

        # Set up the language menu
        self.setup_language_menu()

    def connect_menu_signals(self):
        """Connect menu bar signals to appropriate handlers."""
        if self.menu_bar:
            try:
                self.menu_bar.help_requested.connect(self.show_help)
                self.menu_bar.about_requested.connect(self.show_about)
                self.menu_bar.sponsor_requested.connect(self.show_sponsor)
                self.menu_bar.update_check_requested.connect(self.check_for_updates)
            except Exception as e:
                logger.warning(f"Failed to connect some menu signals: {e}")

    def setup_language_menu(self):
        """Set up the language selection menu."""
        if not self.lang_manager:
            return

        # Get the language menu from the menu bar
        if hasattr(self.menu_bar, 'language_menu'):
            self.language_menu = self.menu_bar.language_menu

            # Clear existing actions
            if self.language_menu:
                self.language_menu.clear()

                # Add available languages
                for lang_code, lang_name in self.lang_manager.available_languages.items():
                    if hasattr(self.lang_manager, 'is_language_available') and \
                       self.lang_manager.is_language_available(lang_code):
                        action = self.language_menu.addAction(lang_name, self.change_language)
                        action.setCheckable(True)
                        action.setData(lang_code)

                        # Check current language
                        if lang_code == self.lang_manager.current_lang:
                            action.setChecked(True)

    def setup_update_timer(self):
        """Set up timer for periodic update checks."""
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.check_for_updates)
        # Check for updates once per day (24 hours)
        self.update_timer.start(24 * 60 * 60 * 1000)

    def create_tabs(self):
        """Create all the tabs for the interface. Override in subclasses for custom tabs."""
        # Create all tabs using actual implementations
        self.scan_tab = self.create_scan_tab()
        self.email_scan_tab = self.create_email_scan_tab()
        self.virus_db_tab = self.create_virus_db_tab()
        self.update_tab = self.create_update_tab()
        self.settings_tab = self.create_settings_tab()
        self.quarantine_tab = self.create_quarantine_tab()
        self.config_editor_tab = self.create_config_editor_tab()

        # Create home tab using HomeTab class if available
        try:
            from clamav_gui.ui.home_tab import HomeTab
            self.home_tab = HomeTab(self)
        except ImportError:
            self.home_tab = self.create_home_tab()

        # Create advanced scanning tabs
        self.smart_scanning_tab = self.create_smart_scanning_tab()
        self.batch_analysis_tab = self.create_batch_analysis_tab()
        self.ml_detection_tab = self.create_ml_detection_tab()
        self.net_scan_tab = self.create_net_scan_tab()

        # Add tabs to the tab widget
        if self.tabs:
            self.tabs.addTab(self.home_tab, self.tr("Home"))
            self.tabs.addTab(self.scan_tab, self.tr("Scan"))
            self.tabs.addTab(self.email_scan_tab, self.tr("Email Scan"))
            self.tabs.addTab(self.virus_db_tab, self.tr("VirusDB"))
            self.tabs.addTab(self.update_tab, self.tr("Update"))
            self.tabs.addTab(self.settings_tab, self.tr("Settings"))
            self.tabs.addTab(self.smart_scanning_tab, self.tr("Smart Scanning"))
            self.tabs.addTab(self.batch_analysis_tab, self.tr("Batch Analysis"))
            self.tabs.addTab(self.ml_detection_tab, self.tr("ML Detection"))
            self.tabs.addTab(self.net_scan_tab, self.tr("Network Scan"))

    def create_home_tab(self):
        """Create the home tab. Override in subclasses for custom implementation."""
        from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.addWidget(QLabel(self.tr("Home tab not implemented in base class")))
        return tab

    def create_virus_db_tab(self):
        """Create the virus database update tab with full functionality."""
        from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                                     QLabel, QPushButton, QTextEdit, QProgressBar,
                                     QLineEdit, QFormLayout, QMessageBox)
        from PySide6.QtCore import Qt

        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Database Information Section
        info_group = QGroupBox(self.tr("Virus Database Information"))
        info_layout = QFormLayout()

        self.db_path_label = QLabel(self.get_database_path())
        self.db_path_label.setWordWrap(True)
        info_layout.addRow(self.tr("Database Path:"), self.db_path_label)

        self.db_version_label = QLabel(self.tr("Unknown"))
        info_layout.addRow(self.tr("Database Version:"), self.db_version_label)

        self.db_signatures_label = QLabel(self.tr("Unknown"))
        info_layout.addRow(self.tr("Signatures:"), self.db_signatures_label)

        self.db_last_update_label = QLabel(self.tr("Never"))
        info_layout.addRow(self.tr("Last Update:"), self.db_last_update_label)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # Update Controls Section
        controls_group = QGroupBox(self.tr("Update Controls"))
        controls_layout = QVBoxLayout()

        # FreshClam path setting
        path_layout = QHBoxLayout()
        self.freshclam_path_input = QLineEdit()
        self.freshclam_path_input.setPlaceholderText(self.tr("Path to freshclam executable (leave empty for system default)"))
        path_layout.addWidget(self.freshclam_path_input)

        browse_freshclam_btn = QPushButton(self.tr("Browse..."))
        browse_freshclam_btn.clicked.connect(self.browse_freshclam_path)
        path_layout.addWidget(browse_freshclam_btn)

        controls_layout.addLayout(path_layout)

        # Control buttons
        buttons_layout = QHBoxLayout()

        self.update_db_btn = QPushButton(self.tr("Update Virus Database"))
        self.update_db_btn.clicked.connect(self.update_virus_database)
        self.update_db_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px 20px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
            QPushButton:pressed {
                background-color: #1976D2;
            }
        """)
        buttons_layout.addWidget(self.update_db_btn)

        self.stop_update_btn = QPushButton(self.tr("Stop Update"))
        self.stop_update_btn.setEnabled(False)
        self.stop_update_btn.clicked.connect(self.stop_virus_database_update)
        self.stop_update_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 10px 20px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:pressed {
                background-color: #c62828;
            }
        """)
        buttons_layout.addWidget(self.stop_update_btn)

        self.refresh_info_btn = QPushButton(self.tr("Refresh Info"))
        self.refresh_info_btn.clicked.connect(self.refresh_database_info)
        buttons_layout.addWidget(self.refresh_info_btn)

        controls_layout.addLayout(buttons_layout)
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)

        # Progress and Output Section
        progress_group = QGroupBox(self.tr("Update Progress & Output"))
        progress_layout = QVBoxLayout()

        self.db_progress = QProgressBar()
        self.db_progress.setRange(0, 0)  # Animated progress bar
        progress_layout.addWidget(self.db_progress)

        self.db_output = QTextEdit()
        self.db_output.setReadOnly(True)
        self.db_output.setMaximumHeight(200)
        progress_layout.addWidget(self.db_output)

        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)

        # Initialize virus database updater
        try:
            from clamav_gui.utils.virus_db import VirusDBUpdater
            self.virus_db_updater = VirusDBUpdater()
            self.virus_db_updater.signals.output.connect(self.update_db_output)
            self.virus_db_updater.signals.finished.connect(self.db_update_finished)
        except ImportError as e:
            logger.warning(f"Could not import VirusDBUpdater: {e}")
            self.virus_db_updater = None

        # Load saved freshclam path if available
        self.load_freshclam_path()

        # Initial info refresh
        self.refresh_database_info()

        return tab

    def get_database_path(self):
        """Get the current virus database path."""
        try:
            if hasattr(self, 'virus_db_updater') and self.virus_db_updater:
                return self.virus_db_updater.get_database_dir()
        except Exception as e:
            logger.warning(f"Error getting database path: {e}")
        return self.tr("Unknown")

    def browse_freshclam_path(self):
        """Browse for freshclam executable path."""
        from PySide6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self, self.tr("Select FreshClam Executable"),
            "", "Executables (*.exe);;All Files (*)" if os.name == 'nt' else "All Files (*)"
        )
        if file_path:
            self.freshclam_path_input.setText(file_path)
            self.save_freshclam_path()

    def load_freshclam_path(self):
        """Load saved freshclam path from settings."""
        try:
            if hasattr(self, 'current_settings') and 'freshclam_path' in self.current_settings:
                self.freshclam_path_input.setText(self.current_settings['freshclam_path'])
        except Exception as e:
            logger.warning(f"Error loading freshclam path: {e}")

    def save_freshclam_path(self):
        """Save freshclam path to settings."""
        try:
            if not hasattr(self, 'current_settings'):
                self.current_settings = {}
            self.current_settings['freshclam_path'] = self.freshclam_path_input.text()
            if hasattr(self, 'settings'):
                self.settings.save_settings(self.current_settings)
        except Exception as e:
            logger.warning(f"Error saving freshclam path: {e}")

    def update_virus_database(self):
        """Start the virus database update process."""
        if not self.virus_db_updater:
            QMessageBox.critical(self, self.tr("Error"),
                               self.tr("Virus database updater not available"))
            return

        freshclam_path = self.freshclam_path_input.text().strip()
        if freshclam_path:
            self.save_freshclam_path()

        # Clear output
        self.db_output.clear()

        # Update UI
        self.update_db_btn.setEnabled(False)
        self.stop_update_btn.setEnabled(True)
        self.db_progress.setRange(0, 0)  # Show animated progress

        # Start update
        success = self.virus_db_updater.start_update(freshclam_path if freshclam_path else None)
        if not success:
            self.db_update_finished(1, 1)
            QMessageBox.critical(self, self.tr("Update Failed"),
                               self.tr("Failed to start virus database update"))

    def stop_virus_database_update(self):
        """Stop the virus database update process."""
        if self.virus_db_updater:
            self.virus_db_updater.stop_update()
            self.update_db_btn.setEnabled(True)
            self.stop_update_btn.setEnabled(False)
            self.db_progress.setRange(0, 100)
            self.db_progress.setValue(0)

    def update_db_output(self, text):
        """Update the database update output display."""
        self.db_output.append(text)
        # Scroll to bottom
        cursor = self.db_output.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.db_output.setTextCursor(cursor)

    def db_update_finished(self, exit_code, exit_status):
        """Handle database update completion."""
        # Update UI
        self.update_db_btn.setEnabled(True)
        self.stop_update_btn.setEnabled(False)
        self.db_progress.setRange(0, 100)
        self.db_progress.setValue(100 if exit_code == 0 else 0)

        # Refresh database info
        self.refresh_database_info()

        # Show result message
        if exit_code == 0:
            QMessageBox.information(self, self.tr("Update Successful"),
                                  self.tr("Virus database updated successfully!"))
        else:
            QMessageBox.warning(self, self.tr("Update Failed"),
                              self.tr("Virus database update failed. Check the output for details."))

    def refresh_database_info(self):
        """Refresh virus database information display."""
        try:
            if self.virus_db_updater:
                # Update database path
                self.db_path_label.setText(self.virus_db_updater.get_database_dir())

                # Get database info
                db_info = self.virus_db_updater.get_database_info()

                if 'error' in db_info and db_info['error']:
                    self.db_version_label.setText(self.tr("Error"))
                    self.db_signatures_label.setText(self.tr("Error"))
                    self.db_last_update_label.setText(f"Error: {db_info['error']}")
                else:
                    self.db_version_label.setText(db_info.get('version', self.tr('Unknown')))
                    self.db_signatures_label.setText(str(db_info.get('signatures', self.tr('Unknown'))))
                    self.db_last_update_label.setText(db_info.get('build_time', self.tr('Unknown')))

        except Exception as e:
            logger.error(f"Error refreshing database info: {e}")
            self.db_version_label.setText(self.tr("Error"))
            self.db_signatures_label.setText(self.tr("Error"))
            self.db_last_update_label.setText(f"Error: {str(e)}")

    def create_status_tab(self):
        """Create the status tab using the actual StatusTab implementation."""
        try:
            from clamav_gui.ui.status_tab import StatusTab
            return StatusTab(self)
        except ImportError:
            # Fallback to placeholder if StatusTab is not available
            from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
            tab = QWidget()
            layout = QVBoxLayout(tab)
            layout.addWidget(QLabel(self.tr("Status not implemented in base class")))
            return tab

    def create_scan_tab(self):
        """Create the scan tab using the actual ScanTab implementation."""
        try:
            from clamav_gui.ui.scan_tab import ScanTab
            return ScanTab(self)
        except ImportError:
            # Fallback to placeholder if ScanTab is not available
            from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
            tab = QWidget()
            layout = QVBoxLayout(tab)
            layout.addWidget(QLabel(self.tr("Scan functionality not implemented in base class")))
            return tab

    def create_email_scan_tab(self):
        """Create the email scan tab using the actual EmailScanTab implementation."""
        try:
            from clamav_gui.ui.email_scan_tab import EmailScanTab
            return EmailScanTab(self)
        except ImportError:
            # Fallback to placeholder if EmailScanTab is not available
            from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
            tab = QWidget()
            layout = QVBoxLayout(tab)
            layout.addWidget(QLabel(self.tr("Email scanning not implemented in base class")))
            return tab

    def create_smart_scanning_tab(self):
        """Create the smart scanning tab using the actual SmartScanningTab implementation."""
        try:
            from clamav_gui.ui.smart_scanning_tab import SmartScanningTab
            return SmartScanningTab(self)
        except ImportError:
            # Fallback to placeholder if SmartScanningTab is not available
            from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
            tab = QWidget()
            layout = QVBoxLayout(tab)
            layout.addWidget(QLabel(self.tr("Smart scanning not implemented in base class")))
            return tab

    def create_batch_analysis_tab(self):
        """Create the batch analysis tab using the actual BatchAnalysisTab implementation."""
        try:
            from clamav_gui.ui.batch_analysis_tab import BatchAnalysisTab
            return BatchAnalysisTab(self)
        except ImportError:
            # Fallback to placeholder if BatchAnalysisTab is not available
            from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
            tab = QWidget()
            layout = QVBoxLayout(tab)
            layout.addWidget(QLabel(self.tr("Batch analysis not implemented in base class")))
            return tab

    def create_ml_detection_tab(self):
        """Create the ML detection tab using the actual MLDetectionTab implementation."""
        try:
            from clamav_gui.ui.ml_detection_tab import MLDetectionTab
            return MLDetectionTab(self)
        except ImportError:
            # Fallback to placeholder if MLDetectionTab is not available
            from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
            tab = QWidget()
            layout = QVBoxLayout(tab)
            layout.addWidget(QLabel(self.tr("ML detection not implemented in base class")))
            return tab

    def create_net_scan_tab(self):
        """Create the network scan tab using the actual NetScanTab implementation."""
        try:
            from clamav_gui.ui.net_scan_tab import NetScanTab
            return NetScanTab(self)
        except ImportError:
            # Fallback to placeholder if NetScanTab is not available
            from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
            tab = QWidget()
            layout = QVBoxLayout(tab)
            layout.addWidget(QLabel(self.tr("Network scan not implemented in base class")))
            return tab

    def load_settings(self):
        """Load application settings."""
        try:
            self.current_settings = self.settings.load_settings() or {}
        except Exception as e:
            logger.warning(f"Failed to load settings: {e}")
            self.current_settings = {}

    def save_settings(self):
        """Save current settings."""
        try:
            self.settings.save_settings(self.current_settings)
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")

    def apply_settings(self):
        """Apply loaded settings to the interface."""
        # Override in subclasses to apply specific settings
        pass

    def change_language(self):
        """Change the application language."""
        try:
            action = self.sender()
            if action and self.lang_manager:
                lang_code = action.data()
                if lang_code and self.lang_manager.set_language(lang_code):
                    logger.info(f"Language changed to {lang_code}")
                    self.current_settings['language'] = lang_code
                    self.save_settings()
        except Exception as e:
            logger.error(f"Error changing language: {e}")

    def retranslate_ui(self, language_code=None):
        """Retranslate the UI when language changes."""
        try:
            # Update window title
            self.setWindowTitle(self.tr("ClamAV GUI"))

            # Update menu titles
            if self.file_menu:
                self.file_menu.setTitle(self.tr("&File"))
            if self.tools_menu:
                self.tools_menu.setTitle(self.tr("&Tools"))
            if self.help_menu:
                self.help_menu.setTitle(self.tr("&Help"))
            if self.language_menu:
                self.language_menu.setTitle(self.tr("&Language"))

            # Update tab names (advanced tabs)
            if self.tabs:
                # Update tab names if tabs exist
                tab_methods = [
                    ('home_tab', self.tr("Home")),
                    ('scan_tab', self.tr("Scan")),
                    ('email_scan_tab', self.tr("Email Scan")),
                    ('virus_db_tab', self.tr("VirusDB")),
                    ('update_tab', self.tr("Update")),
                    ('settings_tab', self.tr("Settings")),
                    ('smart_scanning_tab', self.tr("Smart Scanning")),
                    ('batch_analysis_tab', self.tr("Batch Analysis")),
                    ('ml_detection_tab', self.tr("ML Detection")),
                    ('net_scan_tab', self.tr("Network Scan")),
                ]

                for i, (attr_name, tab_name) in enumerate(tab_methods):
                    if i < self.tabs.count():
                        self.tabs.setTabText(i, tab_name)

            # Update status bar
            if self.status_bar:
                self.status_bar.showMessage(self.tr("Ready"))

        except Exception as e:
            logger.error(f"Error retranslating UI: {e}")

    def check_for_updates(self, force_check=False):
        """Check for application updates."""
        try:
            from clamav_gui.ui.updates_ui import check_for_updates
            from clamav_gui import __version__
            check_for_updates(parent=self, current_version=__version__, force_check=force_check)
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")

    def show_help(self):
        """Show help dialog or open help file."""
        try:
            import subprocess
            import sys
            help_script = os.path.join(os.path.dirname(__file__), '..', '..', 'script', 'help.py')
            if os.path.exists(help_script):
                subprocess.Popen([sys.executable, help_script])
            else:
                logger.warning(f"Help script not found at: {help_script}")
        except Exception as e:
            logger.error(f"Failed to open help: {e}")

    def show_about(self):
        """Show about dialog."""
        try:
            import subprocess
            import sys
            about_script = os.path.join(os.path.dirname(__file__), 'about.py')
            if os.path.exists(about_script):
                subprocess.Popen([sys.executable, about_script])
            else:
                logger.warning(f"About script not found at: {about_script}")
        except Exception as e:
            logger.error(f"Failed to open about dialog: {e}")

    def show_sponsor(self):
        """Show sponsor dialog or open sponsor URL."""
        try:
            import subprocess
            import sys
            from PySide6.QtCore import QUrl
            from PySide6.QtGui import QDesktopServices

            sponsor_script = os.path.join(os.path.dirname(__file__), 'sponsor.py')
            if os.path.exists(sponsor_script):
                subprocess.Popen([sys.executable, sponsor_script])
            else:
                # Fallback to opening sponsor URL
                url = "https://github.com/sponsors/Nsfr750"
                QDesktopServices.openUrl(QUrl(url))
        except Exception as e:
            logger.error(f"Failed to open sponsor dialog: {e}")

    def tr(self, key, default=None):
        """Translate text using the language manager."""
        if self.lang_manager and hasattr(self.lang_manager, 'translate'):
            return self.lang_manager.translate(key, default or key)
        return default or key

    def create_update_tab(self):
        """Create the application update tab with full functionality."""
        from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                                     QLabel, QPushButton, QTextEdit, QProgressBar,
                                     QMessageBox)
        from PySide6.QtCore import Qt

        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Update Information Section
        info_group = QGroupBox(self.tr("Application Update Information"))
        info_layout = QVBoxLayout()

        info_text = QLabel(self.tr("Check for updates to get the latest features and bug fixes."))
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)

        self.update_status_label = QLabel(self.tr("Ready to check for updates"))
        self.update_status_label.setStyleSheet("font-weight: bold; color: #2196F3;")
        info_layout.addWidget(self.update_status_label)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # Update Controls Section
        controls_group = QGroupBox(self.tr("Update Controls"))
        controls_layout = QVBoxLayout()

        # Control buttons
        buttons_layout = QHBoxLayout()

        self.check_updates_btn = QPushButton(self.tr("Check for Updates"))
        self.check_updates_btn.clicked.connect(self.check_for_app_updates)
        self.check_updates_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3e8e41;
            }
        """)
        buttons_layout.addWidget(self.check_updates_btn)

        self.open_download_btn = QPushButton(self.tr("Open Download Page"))
        self.open_download_btn.setEnabled(False)
        self.open_download_btn.clicked.connect(self.open_download_page)
        self.open_download_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px 20px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
            QPushButton:pressed {
                background-color: #1976D2;
            }
        """)
        buttons_layout.addWidget(self.open_download_btn)

        controls_layout.addLayout(buttons_layout)

        # Current version info
        version_layout = QHBoxLayout()
        version_layout.addWidget(QLabel(self.tr("Current Version:")))
        from clamav_gui import __version__
        self.current_version_label = QLabel(__version__)
        self.current_version_label.setStyleSheet("font-weight: bold;")
        version_layout.addWidget(self.current_version_label)
        version_layout.addStretch()

        controls_layout.addLayout(version_layout)

        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)

        # Update Output Section
        output_group = QGroupBox(self.tr("Update Check Results"))
        output_layout = QVBoxLayout()

        self.update_output = QTextEdit()
        self.update_output.setReadOnly(True)
        self.update_output.setMaximumHeight(200)
        self.update_output.setPlaceholderText(self.tr("Update check results will appear here..."))
        output_layout.addWidget(self.update_output)

        output_group.setLayout(output_layout)
        layout.addWidget(output_group)

        # Initialize update checker
        try:
            from clamav_gui.utils.updates import UpdateChecker
            from clamav_gui import __version__
            self.update_checker = UpdateChecker(__version__)
        except ImportError as e:
            logger.warning(f"Could not import UpdateChecker: {e}")
            self.update_checker = None

        return tab

    def check_for_app_updates(self):
        """Check for application updates."""
        if not self.update_checker:
            QMessageBox.critical(self, self.tr("Error"),
                               self.tr("Update checker not available"))
            return

        # Clear output
        self.update_output.clear()

        # Update UI
        self.check_updates_btn.setEnabled(False)
        self.check_updates_btn.setText(self.tr("Checking..."))
        self.update_status_label.setText(self.tr("Checking for updates..."))

        # Start update check in thread
        try:
            self.update_checker.start(force=True)
            self.update_checker.update_check_complete.connect(self.on_update_check_complete)
            self.update_checker.error_occurred.connect(self.on_update_check_error)
        except Exception as e:
            logger.error(f"Error starting update check: {e}")
            self.on_update_check_error(str(e))

    def on_update_check_complete(self, update_info, update_available):
        """Handle update check completion."""
        # Update UI
        self.check_updates_btn.setEnabled(True)
        self.check_updates_btn.setText(self.tr("Check for Updates"))

        if update_available and update_info:
            # Update available
            self.update_status_label.setText(self.tr(f"Update available: {update_info.get('version', 'Unknown')}"))
            self.update_status_label.setStyleSheet("font-weight: bold; color: #4CAF50;")
            self.open_download_btn.setEnabled(True)

            # Show update info in output
            self.update_output.append(self.tr(f"✅ Update available: Version {update_info.get('version', 'Unknown')}"))
            if update_info.get('changelog'):
                self.update_output.append(self.tr("📋 What's new:"))
                self.update_output.append(update_info.get('changelog', '')[:300] + "..." if len(update_info.get('changelog', '')) > 300 else update_info.get('changelog', ''))

            QMessageBox.information(self, self.tr("Update Available"),
                                  self.tr(f"Version {update_info.get('version', 'Unknown')} is available!\n\n"
                                        "Click 'Open Download Page' to get the latest version."))
        else:
            # No update available
            self.update_status_label.setText(self.tr("No updates available"))
            self.update_status_label.setStyleSheet("font-weight: bold; color: #666;")
            self.open_download_btn.setEnabled(False)

            self.update_output.append(self.tr("✅ No updates available. You are using the latest version."))

    def on_update_check_error(self, error_message):
        """Handle update check error."""
        # Update UI
        self.check_updates_btn.setEnabled(True)
        self.check_updates_btn.setText(self.tr("Check for Updates"))
        self.update_status_label.setText(self.tr("Update check failed"))
        self.update_status_label.setStyleSheet("font-weight: bold; color: #f44336;")

        # Show error in output
        self.update_output.append(self.tr(f"❌ Update check failed: {error_message}"))

        QMessageBox.warning(self, self.tr("Update Check Failed"),
                          self.tr(f"Could not check for updates:\n\n{error_message}"))

    def open_download_page(self):
        """Open the download page in browser."""
        try:
            import webbrowser
            from clamav_gui import __version__
            url = f"https://github.com/Nsfr750/clamav-gui/releases/tag/v{__version__}"
            webbrowser.open(url)
        except Exception as e:
            logger.error(f"Error opening download page: {e}")
            QMessageBox.critical(self, self.tr("Error"),
                               self.tr(f"Could not open download page:\n\n{str(e)}"))

    def create_settings_tab(self):
        """Create the settings tab using the actual SettingsTab implementation."""
        try:
            from clamav_gui.ui.settings_tab import SettingsTab
            tab = SettingsTab(self)
            return tab
        except ImportError as e:
            # Fallback to placeholder if SettingsTab is not available
            from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
            tab = QWidget()
            layout = QVBoxLayout(tab)
            layout.addWidget(QLabel(self.tr("Settings not implemented in base class")))
            return tab

    def create_config_editor_tab(self):
        """Create the config editor tab with file editing capabilities."""
        from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                                     QLabel, QPushButton, QTextEdit, QComboBox,
                                     QFileDialog, QMessageBox, QSplitter)
        from PySide6.QtCore import Qt

        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Configuration File Selection Section
        config_group = QGroupBox(self.tr("Configuration Files"))
        config_layout = QVBoxLayout()

        # Config file selector
        selector_layout = QHBoxLayout()

        self.config_selector = QComboBox()
        self.config_selector.addItem(self.tr("ClamAV Configuration (clamd.conf)"), "clamd.conf")
        self.config_selector.addItem(self.tr("FreshClam Configuration (freshclam.conf)"), "freshclam.conf")
        self.config_selector.addItem(self.tr("GUI Configuration (settings.json)"), "settings.json")
        self.config_selector.addItem(self.tr("Custom Configuration File"), "custom")
        selector_layout.addWidget(QLabel(self.tr("Select Config File:")))
        selector_layout.addWidget(self.config_selector, 1)

        config_layout.addLayout(selector_layout)

        # Config file path display and controls
        path_layout = QHBoxLayout()

        self.config_path_label = QLabel(self.tr("No file selected"))
        self.config_path_label.setStyleSheet("border: 1px solid #ccc; padding: 5px; background-color: #f5f5f5;")
        path_layout.addWidget(self.config_path_label, 1)

        browse_btn = QPushButton(self.tr("Browse..."))
        browse_btn.clicked.connect(self.browse_config_file)
        path_layout.addWidget(browse_btn)

        open_btn = QPushButton(self.tr("Open Config"))
        open_btn.clicked.connect(self.open_config_file)
        open_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
        """)
        path_layout.addWidget(open_btn)

        config_layout.addLayout(path_layout)
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # File Editor Section
        editor_group = QGroupBox(self.tr("File Editor"))
        editor_layout = QVBoxLayout()

        # Editor toolbar
        toolbar_layout = QHBoxLayout()

        self.save_btn = QPushButton(self.tr("Save Config"))
        self.save_btn.clicked.connect(self.save_config_file)
        self.save_btn.setEnabled(False)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        toolbar_layout.addWidget(self.save_btn)

        self.reload_btn = QPushButton(self.tr("Reload"))
        self.reload_btn.clicked.connect(self.reload_config_file)
        self.reload_btn.setEnabled(False)
        self.reload_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                border: none;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e68900;
            }
        """)
        toolbar_layout.addWidget(self.reload_btn)

        self.new_btn = QPushButton(self.tr("New Config"))
        self.new_btn.clicked.connect(self.new_config_file)
        self.new_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border: none;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
        """)
        toolbar_layout.addWidget(self.new_btn)

        toolbar_layout.addStretch()
        editor_layout.addLayout(toolbar_layout)

        # Text editor
        self.config_editor = QTextEdit()
        self.config_editor.setPlaceholderText(self.tr("Select a configuration file to edit..."))
        self.config_editor.textChanged.connect(self.on_config_text_changed)
        editor_layout.addWidget(self.config_editor)

        editor_group.setLayout(editor_layout)
        layout.addWidget(editor_group)

        # Status and info section
        info_group = QGroupBox(self.tr("Information"))
        info_layout = QVBoxLayout()

        self.status_label = QLabel(self.tr("Ready"))
        self.status_label.setStyleSheet("font-weight: bold; color: #2196F3;")
        info_layout.addWidget(self.status_label)

        self.file_info_label = QLabel("")
        self.file_info_label.setWordWrap(True)
        info_layout.addWidget(self.file_info_label)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # Connect config selector change
        self.config_selector.currentIndexChanged.connect(self.on_config_selection_changed)

        # Initialize
        self.current_config_file = None
        self.config_modified = False
        self.on_config_selection_changed()

        return tab

    def browse_config_file(self):
        """Browse for a configuration file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, self.tr("Select Configuration File"),
            "", "Configuration Files (*.conf *.json *.ini);;All Files (*)"
        )
        if file_path:
            self.config_path_label.setText(file_path)
            self.current_config_file = file_path
            self.load_config_file(file_path)

    def open_config_file(self):
        """Open the selected configuration file."""
        if not self.current_config_file:
            QMessageBox.warning(self, self.tr("No File Selected"),
                              self.tr("Please select a configuration file first."))
            return

        if not os.path.exists(self.current_config_file):
            QMessageBox.warning(self, self.tr("File Not Found"),
                              self.tr(f"Configuration file not found:\n{self.current_config_file}"))
            return

        self.load_config_file(self.current_config_file)

    def load_config_file(self, file_path):
        """Load a configuration file into the editor."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            self.config_editor.setPlainText(content)
            self.config_modified = False
            self.save_btn.setEnabled(False)
            self.reload_btn.setEnabled(True)

            # Update status
            file_size = os.path.getsize(file_path)
            self.file_info_label.setText(
                self.tr(f"Loaded: {file_path}\nSize: {file_size} bytes\nModified: {self.config_modified}")
            )

            self.status_label.setText(self.tr("File loaded successfully"))
            self.status_label.setStyleSheet("font-weight: bold; color: #4CAF50;")

        except Exception as e:
            error_msg = f"Error loading file: {str(e)}"
            logger.error(error_msg)
            QMessageBox.critical(self, self.tr("Load Error"), error_msg)
            self.status_label.setText(self.tr("Failed to load file"))
            self.status_label.setStyleSheet("font-weight: bold; color: #f44336;")

    def save_config_file(self):
        """Save the current configuration file."""
        if not self.current_config_file:
            QMessageBox.warning(self, self.tr("No File Selected"),
                              self.tr("Please select a configuration file first."))
            return

        try:
            # Create backup before saving
            backup_path = self.current_config_file + ".backup"
            if os.path.exists(self.current_config_file):
                import shutil
                shutil.copy2(self.current_config_file, backup_path)

            # Save file
            content = self.config_editor.toPlainText()
            with open(self.current_config_file, 'w', encoding='utf-8') as f:
                f.write(content)

            self.config_modified = False
            self.save_btn.setEnabled(False)

            # Update status
            file_size = os.path.getsize(self.current_config_file)
            self.file_info_label.setText(
                self.tr(f"Saved: {self.current_config_file}\nSize: {file_size} bytes\nModified: {self.config_modified}")
            )

            self.status_label.setText(self.tr("File saved successfully"))
            self.status_label.setStyleSheet("font-weight: bold; color: #4CAF50;")

            QMessageBox.information(self, self.tr("Save Successful"),
                                  self.tr(f"Configuration saved successfully!\n\nBackup created: {backup_path}"))

        except Exception as e:
            error_msg = f"Error saving file: {str(e)}"
            logger.error(error_msg)
            QMessageBox.critical(self, self.tr("Save Error"), error_msg)
            self.status_label.setText(self.tr("Failed to save file"))
            self.status_label.setStyleSheet("font-weight: bold; color: #f44336;")

    def reload_config_file(self):
        """Reload the current configuration file."""
        if not self.current_config_file:
            return

        reply = QMessageBox.question(
            self, self.tr("Reload File"),
            self.tr("Are you sure you want to reload the file?\n\nAny unsaved changes will be lost."),
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.load_config_file(self.current_config_file)

    def new_config_file(self):
        """Create a new configuration file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, self.tr("Create New Configuration File"),
            "", "Configuration Files (*.conf *.json *.ini);;All Files (*)"
        )

        if file_path:
            self.config_path_label.setText(file_path)
            self.current_config_file = file_path

            # Create empty file with basic template based on extension
            template = self.get_config_template(file_path)

            self.config_editor.setPlainText(template)
            self.config_modified = True
            self.save_btn.setEnabled(True)
            self.reload_btn.setEnabled(False)

            # Update status
            self.file_info_label.setText(
                self.tr(f"New file: {file_path}\nSize: {len(template)} characters\nModified: {self.config_modified}")
            )

            self.status_label.setText(self.tr("New file created - ready to edit"))
            self.status_label.setStyleSheet("font-weight: bold; color: #2196F3;")

    def get_config_template(self, file_path):
        """Get template content for new configuration files."""
        if file_path.lower().endswith('.conf'):
            return "# ClamAV Configuration File\n# Generated by ClamAV GUI\n\n# Example configuration\nLogFile /var/log/clamav/clamd.log\n"
        elif file_path.lower().endswith('.json'):
            return '{\n  "gui_settings": {\n    "language": "en_US",\n    "theme": "default"\n  }\n}'
        else:
            return "# Configuration file\n# Add your settings here...\n"

    def on_config_text_changed(self):
        """Handle text changes in the editor."""
        if hasattr(self, 'config_editor'):
            self.config_modified = True
            self.save_btn.setEnabled(True)

            if hasattr(self, 'file_info_label'):
                self.file_info_label.setText(
                    self.file_info_label.text().split('\n')[0] + f"\nModified: {self.config_modified}"
                )

            if hasattr(self, 'status_label'):
                self.status_label.setText(self.tr("File modified - save to apply changes"))
                self.status_label.setStyleSheet("font-weight: bold; color: #ff9800;")

    def on_config_selection_changed(self):
        """Handle configuration file selection change."""
        current_text = self.config_selector.currentText()
        current_data = self.config_selector.currentData()

        if current_data == "custom":
            # Custom file - don't auto-load
            self.config_path_label.setText(self.tr("Select a custom configuration file"))
            self.current_config_file = None
            self.config_editor.clear()
            self.save_btn.setEnabled(False)
            self.reload_btn.setEnabled(False)
            self.status_label.setText(self.tr("Select a custom configuration file to edit"))
        else:
            # Standard config files
            if current_data == "clamd.conf":
                config_path = self.get_clamav_config_path("clamd.conf")
            elif current_data == "freshclam.conf":
                config_path = self.get_clamav_config_path("freshclam.conf")
            elif current_data == "settings.json":
                config_path = self.get_gui_config_path()
            else:
                config_path = None

            if config_path and os.path.exists(config_path):
                self.config_path_label.setText(config_path)
                self.current_config_file = config_path
                self.load_config_file(config_path)
            else:
                self.config_path_label.setText(self.tr("Configuration file not found"))
                self.current_config_file = None
                self.config_editor.clear()
                self.save_btn.setEnabled(False)
                self.reload_btn.setEnabled(False)
                self.status_label.setText(self.tr("Configuration file not found"))

    def get_clamav_config_path(self, config_name):
        """Get the path to a ClamAV configuration file."""
        # Common locations for ClamAV config files
        common_paths = [
            f"/etc/clamav/{config_name}",
            f"/usr/local/etc/clamav/{config_name}",
            f"C:\\Program Files\\ClamAV\\{config_name}",
            f"C:\\Program Files (x86)\\ClamAV\\{config_name}",
        ]

        for path in common_paths:
            if os.path.exists(path):
                return path

        # Return default location even if it doesn't exist
        return common_paths[0]

    def get_gui_config_path(self):
        """Get the path to the GUI configuration file."""
        # GUI config is usually in the user's app data or the app directory
        app_data = os.getenv('APPDATA') if os.name == 'nt' else os.path.expanduser('~')
        config_dir = os.path.join(app_data, 'ClamAV-GUI')
        return os.path.join(config_dir, 'settings.json')
